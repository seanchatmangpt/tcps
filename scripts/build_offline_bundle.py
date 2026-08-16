#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_TOP = {".git", ".pytest_cache", "dist", "__pycache__"}


def include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if relative.parts and relative.parts[0] in EXCLUDED_TOP:
        return False
    return not any(part == "__pycache__" for part in relative.parts)


def tar_bytes() -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(ROOT.rglob("*"), key=lambda p: str(p.relative_to(ROOT))):
            if not include(path):
                continue
            relative = Path("tcps-1979.1.1") / path.relative_to(ROOT)
            info = archive.gettarinfo(str(path), arcname=str(relative))
            info.uid = 0
            info.gid = 0
            info.uname = "root"
            info.gname = "root"
            info.mtime = 0
            info.pax_headers = {}
            if path.is_file():
                with path.open("rb") as handle:
                    archive.addfile(info, handle)
            else:
                archive.addfile(info)
    return buffer.getvalue()


def gzip_bytes(payload: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0, compresslevel=9) as handle:
        handle.write(payload)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-determinism", action="store_true")
    parser.add_argument("--output", default="dist/tcps-1979.1.1.tar.gz")
    args = parser.parse_args()

    first = gzip_bytes(tar_bytes())
    if args.check_determinism:
        second = gzip_bytes(tar_bytes())
        if first != second:
            print(json.dumps({"state": "BUILD_BROKEN", "code": "BUNDLE_NONDETERMINISTIC"}))
            return 1

    from sys import path as sys_path
    sys_path.insert(0, str(ROOT / "src"))
    from tcps.blake3_ref import hexdigest

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(first)
    digest = hexdigest(first)
    output.with_suffix(output.suffix + ".blake3").write_text(digest + "  " + output.name + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": "tcps.offline-bundle.v1",
                "state": "ALIVE",
                "path": str(output.relative_to(ROOT)),
                "bytes": len(first),
                "blake3": digest,
                "deterministic": bool(args.check_determinism),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
