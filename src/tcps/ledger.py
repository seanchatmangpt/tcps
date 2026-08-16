from __future__ import annotations

import json
import os
import socket
from pathlib import Path
from typing import Any

from .model import Refusal, TCPSRefused
from .receipt import verify_chain, verify_pre_receipt


def _fsync_dir(path: Path) -> None:
    """Persist directory-entry changes on filesystems that support fsync."""
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
    if not path.exists():
        return []
    result: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            result.append(json.loads(line))
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
    return result


def load_pending(path: Path) -> dict[str, Any] | None:
    pending = pending_path(path)
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
    verify_pre_receipt(item)
    return item


class Ledger:
    """Single-writer durable receipt ledger with crash-recovery state."""

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
                        "allow the active writer to finish or recover a stale lock",
                    )
                )

            payload = json.dumps(
                {"pid": os.getpid(), "host": host},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8") + b"\n"
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
                    "new actuation cannot begin while a prior actuation is unresolved",
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
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    pre_receipt,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, pending)
        _fsync_dir(pending.parent)

    def finalize(self, receipt: dict[str, Any]) -> None:
        """Fsync the final receipt before clearing the prepared state."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    receipt,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        pending = pending_path(self.path)
        if pending.exists():
            pending.unlink()
            _fsync_dir(pending.parent)

    def abort_pending(self) -> None:
        pending = pending_path(self.path)
        if pending.exists():
            pending.unlink()
            _fsync_dir(pending.parent)
