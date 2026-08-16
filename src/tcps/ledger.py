from __future__ import annotations

import json
import os
import socket
from pathlib import Path
from typing import Any

from .model import Refusal, TCPSRefused
from .receipt import verify_chain, verify_pre_receipt


def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _lock_path(path: Path) -> Path:
    return path.with_name(path.name + ".lock")


def pending_path(path: Path) -> Path:
    return path.with_name(path.name + ".pending.json")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def load_receipts(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    result: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TCPSRefused(
                Refusal(
                    "RECEIPT_LOG_INVALID_JSON",
                    f"{path}:{line_number}",
                    "receipt log is canonical JSON Lines",
                    str(exc),
                    "valid JSON object",
                    "restore the original line from durable evidence",
                )
            ) from exc
        if not isinstance(item, dict):
            raise TCPSRefused(
                Refusal(
                    "RECEIPT_LOG_INVALID_SHAPE",
                    f"{path}:{line_number}",
                    "each receipt log line is an object",
                    type(item).__name__,
                    "object",
                    "restore the original receipt",
                )
            )
        result.append(item)
    return result


def load_pending(path: Path) -> dict[str, Any] | None:
    pending = pending_path(Path(path))
    if not pending.exists():
        return None
    try:
        item = json.loads(pending.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TCPSRefused(
            Refusal(
                "PRE_RECEIPT_INVALID_JSON",
                str(pending),
                "pending record is canonical JSON",
                str(exc),
                "valid JSON object",
                "restore the original pending record",
            )
        ) from exc
    if not isinstance(item, dict):
        raise TCPSRefused(
            Refusal(
                "PRE_RECEIPT_INVALID_SHAPE",
                str(pending),
                "pending record is an object",
                type(item).__name__,
                "object",
                "restore the original pending record",
            )
        )
    verify_pre_receipt(item)
    return item


class Ledger:
    """Single-writer durable receipt ledger with explicit recovery state."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._fd: int | None = None

    def __enter__(self) -> "Ledger":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._acquire()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._release()

    def _acquire(self) -> None:
        lock = _lock_path(self.path)
        host = socket.gethostname()
        for _ in range(2):
            try:
                fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                stale = False
                try:
                    data = json.loads(lock.read_text(encoding="utf-8"))
                    stale = data.get("host") == host and not _pid_alive(int(data.get("pid", -1)))
                except Exception:
                    stale = False
                if stale:
                    lock.unlink(missing_ok=True)
                    _fsync_dir(lock.parent)
                    continue
                raise TCPSRefused(
                    Refusal(
                        "LEDGER_LOCKED",
                        str(self.path),
                        "one writer owns the receipt ledger at a time",
                        str(lock),
                        "unlocked ledger",
                        "allow the active writer to finish or recover a stale local lock",
                    )
                )
            payload = json.dumps({"pid": os.getpid(), "host": host}, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
            os.write(fd, payload)
            os.fsync(fd)
            _fsync_dir(lock.parent)
            self._fd = fd
            return
        raise TCPSRefused(
            Refusal(
                "LEDGER_LOCKED",
                str(self.path),
                "one writer owns the receipt ledger at a time",
                str(lock),
                "unlocked ledger",
                "inspect the lock owner before retrying",
            )
        )

    def _release(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        lock = _lock_path(self.path)
        if lock.exists():
            lock.unlink()
            _fsync_dir(lock.parent)

    def receipts(self) -> list[dict[str, Any]]:
        items = load_receipts(self.path)
        verify_chain(items)
        return items

    def head_and_count(self) -> tuple[str | None, int]:
        items = self.receipts()
        return verify_chain(items), len(items)

    def pending(self) -> dict[str, Any] | None:
        return load_pending(self.path)

    def require_clean(self) -> None:
        pending = self.pending()
        if pending is not None:
            raise TCPSRefused(
                Refusal(
                    "RECOVERY_REQUIRED",
                    pending["pre_receipt_id"],
                    "new actuation cannot begin while prior DO is unresolved",
                    pending["pre_receipt_id"],
                    None,
                    "run tcps recover before starting new work",
                )
            )

    def prepare(self, pre_receipt: dict[str, Any]) -> None:
        """Atomically persist and fsync intent before consequential mutation."""
        verify_pre_receipt(pre_receipt)
        pending = pending_path(self.path)
        if pending.exists():
            self.require_clean()
        temporary = pending.with_name(pending.name + f".{os.getpid()}.tmp")
        encoded = json.dumps(pre_receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, pending)
        _fsync_dir(pending.parent)

    def repair_incomplete_tail(self) -> bool:
        """Truncate only a crash-incomplete final line while a pre-receipt exists."""
        if self.pending() is None or not self.path.exists():
            return False
        payload = self.path.read_bytes()
        if not payload or payload.endswith(b"\n"):
            return False
        boundary = payload.rfind(b"\n") + 1
        prefix = payload[:boundary]
        if prefix:
            parsed = [json.loads(line) for line in prefix.decode("utf-8").splitlines() if line]
            verify_chain(parsed)
        with self.path.open("r+b") as handle:
            handle.truncate(boundary)
            handle.flush()
            os.fsync(handle.fileno())
        return True

    def finalize(self, receipt: dict[str, Any]) -> None:
        """Validate and fsync the final receipt before clearing prepared state."""
        pending = self.pending()
        if pending is None:
            raise TCPSRefused(
                Refusal(
                    "FINALIZE_WITHOUT_PRE_RECEIPT",
                    str(receipt.get("receipt_id")),
                    "every final receipt closes a durable pre-receipt",
                    None,
                    "pending pre-receipt",
                    "prepare the exact intent before DO",
                )
            )
        if receipt.get("pre_receipt") != pending["pre_receipt_id"]:
            raise TCPSRefused(
                Refusal(
                    "FINAL_RECEIPT_PRE_MISMATCH",
                    str(receipt.get("receipt_id")),
                    "final receipt closes exactly the prepared actuation",
                    receipt.get("pre_receipt"),
                    pending["pre_receipt_id"],
                    "finalize only the prepared actuation",
                )
            )
        existing = self.receipts()
        verify_chain(existing + [receipt])
        encoded = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            offset = 0
            while offset < len(encoded):
                written = os.write(fd, encoded[offset:])
                if written <= 0:
                    raise OSError("short ledger write")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)
        pending_path(self.path).unlink()
        _fsync_dir(self.path.parent)

    def abort_pending(self) -> None:
        pending = pending_path(self.path)
        if pending.exists():
            pending.unlink()
            _fsync_dir(pending.parent)
