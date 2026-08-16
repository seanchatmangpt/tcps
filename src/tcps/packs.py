from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from .authority import load_authority
from .canonical import digest_object, load_json
from .engine import actuate, construct, observe, select_and_authorize
from .model import Refusal, TCPSRefused

PACK_KINDS = {"workflow", "integration", "preset", "extension", "bundle", "standard-work"}
PACK_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")

CORE_PACK: dict[str, Any] = {
    "schema": "tcps.pack.v1",
    "pack_id": "core-1979",
    "version": "1979.1.1",
    "kind": "standard-work",
    "requires": [],
    "files": {
        "prompts/eve.en.md": """# EVE — Human Threshold\n\nConvert human purpose into bounded observation. Preserve requested outcome, observed facts, unknown facts, constraints, acceptance conditions, and authority boundaries. Do not invent missing observation, choose implementation, or infer permission from intent. UNKNOWN is not ADMITTED. Output only the smallest lawful demand required downstream.\n""",
        "prompts/wizard.zh.md": """# WIZARD — 制造\n\n你的职责是制造，不是执行。仅从已接纳的观察、生产法、图式和下游看板需求构造可逆候选。保留合法的可能空间，记录来源，把未知保持为未知，把不支持保持为 UNSUPPORTED。生成不是接纳，构造不是选择，选择不是执行。不得授予自己执行权限。\n""",
        "prompts/telco.ja.md": """# TELCO — 経路・選択・権限\n\n意味を再解釈せず、承認済み要求に対して能力の所在、所有者、経路、境界、利用可能性、権限を区別する。UNKNOWN を AVAILABLE とみなさない。接続可能であることを実行許可とみなさない。経路は実行ではない。下流が再解釈せずに利用できる正確な計画だけを出力する。\n""",
        "prompts/robot.ko.md": """# ROBOT — 실행\n\n역할은 해석이 아니라 정확한 실행이다. 승인된 계획, 정확한 권한, 루트, 사전 영수증 없이는 실행하지 않는다. 경로를 임의로 바꾸지 않고 새로운 capability를 탐색하지 않는다. 관측된 결과만 기록하고 결과를 성공으로 추정하지 않는다. 모든 외부 변화는 검증된 최종 영수증으로 닫는다.\n""",
        "standard/production.md": """# TCPS 1979 Standard Work\n\nObserve → Admit → Model → Select → Authorize → Prepare → Actuate → Verify → Receipt → Reobserve.\n\nDownstream is the customer. Selection is not execution. Execution without durable evidence is not production.\n""",
    },
}


def _refuse(code: str, object_id: str, observed: Any, expected: Any, repair: str) -> None:
    raise TCPSRefused(
        Refusal(
            code,
            object_id,
            "pack admission preserves deterministic bounded production",
            observed,
            expected,
            repair,
        )
    )


def _pack_body(pack: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in pack.items() if key != "pack_digest"}


def validate_pack(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        _refuse("PACK_SHAPE_INVALID", "pack", type(value).__name__, "object", "supply a pack object")
    required = {"schema", "pack_id", "version", "kind", "requires", "files"}
    allowed = required | {"pack_digest"}
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - allowed)
    if missing or unknown:
        _refuse("PACK_SHAPE_INVALID", str(value.get("pack_id", "pack")), {"missing": missing, "unknown": unknown}, sorted(required), "repair the manifest shape")
    if value["schema"] != "tcps.pack.v1":
        _refuse("PACK_SCHEMA_UNSUPPORTED", str(value.get("pack_id", "pack")), value["schema"], "tcps.pack.v1", "migrate the pack manifest")
    pack_id = value["pack_id"]
    if not isinstance(pack_id, str) or PACK_ID.fullmatch(pack_id) is None:
        _refuse("PACK_ID_INVALID", str(pack_id), pack_id, "lowercase safe pack id", "use [a-z0-9._-] only")
    if not isinstance(value["version"], str) or not value["version"]:
        _refuse("PACK_VERSION_INVALID", pack_id, value["version"], "non-empty version", "supply an exact version")
    if value["kind"] not in PACK_KINDS:
        _refuse("PACK_KIND_UNSUPPORTED", pack_id, value["kind"], sorted(PACK_KINDS), "choose an admitted pack kind")
    if not isinstance(value["requires"], list) or not all(isinstance(item, str) and PACK_ID.fullmatch(item) for item in value["requires"]):
        _refuse("PACK_REQUIRES_INVALID", pack_id, value["requires"], "array of safe pack ids", "normalize dependency identities")
    files = value["files"]
    if not isinstance(files, dict) or not files:
        _refuse("PACK_FILES_INVALID", pack_id, files, "non-empty object<relative-path,text>", "supply pack files")
    for raw, content in files.items():
        if not isinstance(raw, str) or not isinstance(content, str):
            _refuse("PACK_FILE_INVALID", pack_id, {"path": raw, "content_type": type(content).__name__}, "relative path -> text", "normalize pack files")
        path = PurePosixPath(raw)
        if path.is_absolute() or not raw or any(part in {"", ".", ".."} for part in path.parts):
            _refuse("PACK_PATH_INVALID", pack_id, raw, "bounded relative path", "remove absolute or traversal components")
    computed = digest_object(_pack_body(value))
    if value.get("pack_digest") not in {None, computed}:
        _refuse("PACK_DIGEST_MISMATCH", pack_id, value.get("pack_digest"), computed, "restore the admitted manifest")
    return {**_pack_body(value), "pack_digest": computed}


def builtin_pack(name: str) -> dict[str, Any]:
    if name != "core-1979":
        _refuse("PACK_NOT_FOUND", name, name, ["core-1979"], "choose an available built-in pack or supply a manifest")
    return validate_pack(CORE_PACK)


def load_pack(source: str) -> dict[str, Any]:
    if source.startswith("builtin:"):
        return builtin_pack(source.split(":", 1)[1])
    return validate_pack(load_json(source))


def _mkdir_actions(paths: set[PurePosixPath]) -> list[dict[str, Any]]:
    ordered = sorted(paths, key=lambda item: (len(item.parts), str(item)))
    return [{"op": "mkdir", "path": str(path)} for path in ordered]


def pack_work_order(pack: dict[str, Any]) -> dict[str, Any]:
    admitted = validate_pack(pack)
    base = PurePosixPath(".tcps") / "packs" / admitted["pack_id"]
    directories: set[PurePosixPath] = {PurePosixPath(".tcps") / "packs", base}
    for raw in admitted["files"]:
        parent = (base / PurePosixPath(raw)).parent
        while str(parent) not in {".", ".tcps"}:
            directories.add(parent)
            parent = parent.parent
    files = dict(admitted["files"])
    files["manifest.json"] = json.dumps(admitted, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    actions = _mkdir_actions(directories)
    for raw, content in sorted(files.items()):
        actions.append({"op": "write_text", "path": str(base / PurePosixPath(raw)), "content": content})
    return {
        "schema": "tcps.work.v1",
        "subject": f"pack:{admitted['pack_id']}@{admitted['version']}",
        "purpose": "install an admitted TCPS production pack",
        "observations": [
            {"kind": "pack", "value": admitted["pack_digest"]},
            {"kind": "downstream-demand", "value": admitted["kind"]},
        ],
        "actions": actions,
    }


def install_pack(source: str, *, root: Path, authority_path: Path, receipt_path: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    pack = load_pack(source)
    for dependency in pack["requires"]:
        if not (root / ".tcps" / "packs" / dependency / "manifest.json").is_file():
            _refuse("PACK_DEPENDENCY_MISSING", pack["pack_id"], dependency, "installed dependency", "install dependencies before this pack")
    work = pack_work_order(pack)
    policy = load_authority(authority_path)
    graph = construct(observe(work))
    plan = select_and_authorize(graph, policy, root)
    receipts = actuate(plan, policy, root, receipt_path)
    return {
        "schema": "tcps.pack-install.v1",
        "pack_id": pack["pack_id"],
        "pack_digest": pack["pack_digest"],
        "receipt_count": len(receipts),
        "receipt_head": receipts[-1]["receipt_id"] if receipts else None,
        "state": "ALIVE",
    }


def installed_packs(root: Path) -> dict[str, Any]:
    base = Path(root).resolve() / ".tcps" / "packs"
    packs: list[dict[str, Any]] = []
    if base.is_dir():
        for manifest in sorted(base.glob("*/manifest.json")):
            try:
                pack = validate_pack(load_json(manifest))
                packs.append({"pack_id": pack["pack_id"], "version": pack["version"], "kind": pack["kind"], "pack_digest": pack["pack_digest"], "state": "ALIVE"})
            except (TCPSRefused, OSError):
                packs.append({"pack_id": manifest.parent.name, "state": "BUILD_BROKEN"})
    return {"schema": "tcps.pack-list.v1", "packs": packs, "count": len(packs), "state": "ALIVE" if all(item["state"] == "ALIVE" for item in packs) else "BUILD_BROKEN"}
