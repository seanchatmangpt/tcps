from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .authority import load_authority
from .canonical import load_json, write_json
from .engine import actuate, construct, observe, recover, select_and_authorize
from .generated_contract import SYSTEM_NAME, VERSION
from .model import TCPSRefused
from .replay import replay


def _emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tcps", description=SYSTEM_NAME)
    parser.add_argument("--version", action="version", version=f"tcps {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="initialize a bounded TCPS workspace")
    init.add_argument("path", nargs="?", default=".")

    eve = sub.add_parser("eve", help="observe and normalize a work order")
    eve.add_argument("work")
    eve.add_argument("--out")

    wizard = sub.add_parser("wizard", help="construct the reversible candidate graph")
    wizard.add_argument("observation")
    wizard.add_argument("--out")

    telco = sub.add_parser("telco", help="select and authorize candidates under policy")
    telco.add_argument("graph")
    telco.add_argument("--authority", default=".tcps/authority.json")
    telco.add_argument("--root", default=".")
    telco.add_argument("--out")

    robot = sub.add_parser("robot", help="execute an authorized plan and issue receipts")
    robot.add_argument("plan")
    robot.add_argument("--authority", default=".tcps/authority.json")
    robot.add_argument("--root", default=".")
    robot.add_argument("--receipts", default=".tcps/receipts.ndjson")

    run = sub.add_parser("run", help="execute the complete deterministic production cycle")
    run.add_argument("work")
    run.add_argument("--authority", default=".tcps/authority.json")
    run.add_argument("--root", default=".")
    run.add_argument("--receipts", default=".tcps/receipts.ndjson")
    run.add_argument("--plan-out", default=".tcps/last-plan.json")

    replay_parser = sub.add_parser("replay", help="verify receipt chain and current consequences")
    replay_parser.add_argument("--receipts", default=".tcps/receipts.ndjson")
    replay_parser.add_argument("--root", default=".")

    recover_parser = sub.add_parser("recover", help="close or abort an interrupted actuation")
    recover_parser.add_argument("--receipts", default=".tcps/receipts.ndjson")
    recover_parser.add_argument("--root", default=".")

    return parser


def _write_or_emit(value: Any, output: str | None) -> None:
    if output:
        write_json(output, value)
    else:
        _emit(value)


def _init(path: Path) -> dict[str, Any]:
    path = path.resolve()
    tcps_dir = path / ".tcps"
    tcps_dir.mkdir(parents=True, exist_ok=True)
    authority_path = tcps_dir / "authority.json"
    if not authority_path.exists():
        write_json(
            authority_path,
            {
                "schema": "tcps.authority.v1",
                "authority_id": "local-default",
                "allowed_roots": [str(path)],
                "allowed_operations": ["mkdir", "write_text"],
                "max_actions": 64,
                "allow_irreversible": False,
            },
        )
    receipts = tcps_dir / "receipts.ndjson"
    receipts.touch(exist_ok=True)
    return {"state": "PARTIAL_ALIVE", "workspace": str(path), "authority": str(authority_path)}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            _emit(_init(Path(args.path)))
            return 0
        if args.command == "eve":
            value = observe(load_json(args.work))
            _write_or_emit(value, args.out)
            return 0
        if args.command == "wizard":
            value = construct(load_json(args.observation))
            _write_or_emit(value, args.out)
            return 0
        if args.command == "telco":
            value = select_and_authorize(
                load_json(args.graph), load_authority(args.authority), Path(args.root)
            )
            _write_or_emit(value, args.out)
            return 0
        if args.command == "robot":
            receipts = actuate(
                load_json(args.plan),
                load_authority(args.authority),
                Path(args.root),
                Path(args.receipts),
            )
            _emit({"state": "ALIVE", "receipts": receipts})
            return 0
        if args.command == "run":
            work = load_json(args.work)
            policy = load_authority(args.authority)
            observation = observe(work)
            graph = construct(observation)
            plan = select_and_authorize(graph, policy, Path(args.root))
            write_json(args.plan_out, plan)
            receipts = actuate(plan, policy, Path(args.root), Path(args.receipts))
            _emit(
                {
                    "state": "ALIVE",
                    "subject": plan["subject"],
                    "plan_digest": plan["plan_digest"],
                    "receipt_count": len(receipts),
                    "receipt_head": receipts[-1]["receipt_id"] if receipts else None,
                }
            )
            return 0
        if args.command == "replay":
            result = replay(Path(args.receipts), Path(args.root))
            _emit(result)
            return 0 if result["state"] == "ALIVE" else 3
        if args.command == "recover":
            result = recover(Path(args.receipts), Path(args.root))
            _emit(result)
            return 0 if result["state"] in {"ALIVE", "PARTIAL_ALIVE"} else 3
        raise AssertionError("unreachable")
    except TCPSRefused as exc:
        _emit(exc.refusal.as_dict())
        return 2
    except FileNotFoundError as exc:
        _emit(
            {
                "state": "BLOCKED",
                "code": "INPUT_NOT_FOUND",
                "path": str(exc.filename),
                "repair": "provide the declared input without changing authority",
            }
        )
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
