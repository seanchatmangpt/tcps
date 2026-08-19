from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .authority import load_authority
from .canonical import load_json, write_json
from .dfcm import bottleneck as dfcm_bottleneck
from .dfcm import flow_metrics as dfcm_flow_metrics
from .dfcm import kaizen_from_bottleneck as dfcm_kaizen
from .dfcm import plan as dfcm_plan
from .dfcm import verify_plan as verify_dfcm_plan
from .engine import actuate, construct, observe, recover, select_and_authorize
from .generated_contract import SYSTEM_NAME, VERSION
from .model import TCPSRefused
from .packs import builtin_pack, install_pack, installed_packs, load_pack
from .plant import andon, kanban, kaizen, metrics, standard_work, standing, wip
from .replay import replay


def _emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _add_cycle_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("work")
    parser.add_argument("--authority", default=".tcps/authority.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--receipts", default=".tcps/receipts.ndjson")
    parser.add_argument("--plan-out", default=".tcps/last-plan.json")


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
    _add_cycle_args(run)
    make = sub.add_parser("make", help="pull one customer demand through the full production line")
    _add_cycle_args(make)

    replay_parser = sub.add_parser("replay", help="verify receipt chain and current consequences")
    replay_parser.add_argument("--receipts", default=".tcps/receipts.ndjson")
    replay_parser.add_argument("--root", default=".")

    recover_parser = sub.add_parser("recover", help="close or abort an interrupted actuation")
    recover_parser.add_argument("--receipts", default=".tcps/receipts.ndjson")
    recover_parser.add_argument("--root", default=".")

    sub.add_parser("standard", help="emit canonical machine-readable standard work")

    kanban_parser = sub.add_parser("kanban", help="manufacture a downstream demand token")
    kanban_parser.add_argument("subject")
    kanban_parser.add_argument("purpose")
    kanban_parser.add_argument("--quantity", type=int, default=1)
    kanban_parser.add_argument("--due-tick", type=int)

    for name, help_text in (
        ("wip", "observe semantic actuation WIP"),
        ("andon", "observe the production-line signal"),
        ("metrics", "derive production metrics from receipts"),
        ("standing", "derive current standing from replay"),
    ):
        item = sub.add_parser(name, help=help_text)
        item.add_argument("--receipts", default=".tcps/receipts.ndjson")
        if name != "wip":
            item.add_argument("--root", default=".")

    kaizen_parser = sub.add_parser("kaizen", help="construct a non-actuating improvement candidate")
    kaizen_parser.add_argument("reason")
    kaizen_parser.add_argument("proposal")

    dfcm = sub.add_parser("dfcm", help="govern the reversible production frontier")
    dfcm_sub = dfcm.add_subparsers(dest="dfcm_command", required=True)

    dfcm_plan_parser = dfcm_sub.add_parser("plan", help="manufacture a deterministic Pareto/heijunka pull plan")
    dfcm_plan_parser.add_argument("queue")
    dfcm_plan_parser.add_argument("--downstream-wip", type=int, default=0)
    dfcm_plan_parser.add_argument("--downstream-limit", type=int, default=1)
    dfcm_plan_parser.add_argument("--andon-active", action="store_true")
    dfcm_plan_parser.add_argument("--out")

    dfcm_verify_parser = dfcm_sub.add_parser("verify", help="replay and verify a DfCM planning receipt")
    dfcm_verify_parser.add_argument("plan")

    dfcm_flow_parser = dfcm_sub.add_parser("flow", help="derive takt, Little's Law, and flow-efficiency evidence")
    dfcm_flow_parser.add_argument("--available-ticks", required=True, type=float)
    dfcm_flow_parser.add_argument("--demand", required=True, type=float)
    dfcm_flow_parser.add_argument("--throughput", required=True, type=float)
    dfcm_flow_parser.add_argument("--wip", required=True, type=float)
    dfcm_flow_parser.add_argument("--observed-cycle", type=float)
    dfcm_flow_parser.add_argument("--touch", type=float)
    dfcm_flow_parser.add_argument("--lead", type=float)

    dfcm_bottleneck_parser = dfcm_sub.add_parser("bottleneck", help="observe the deterministic production constraint")
    dfcm_bottleneck_parser.add_argument("stages")
    dfcm_bottleneck_parser.add_argument("--out")

    dfcm_kaizen_parser = dfcm_sub.add_parser("kaizen", help="manufacture a non-actuating Kaizen candidate from a bottleneck")
    dfcm_kaizen_parser.add_argument("bottleneck")

    pack = sub.add_parser("pack", help="manage receipted production packs")
    pack_sub = pack.add_subparsers(dest="pack_command", required=True)
    pack_sub.add_parser("builtins", help="list built-in production packs")
    pack_list = pack_sub.add_parser("list", help="list installed production packs")
    pack_list.add_argument("--root", default=".")
    pack_validate = pack_sub.add_parser("validate", help="validate a built-in or local pack manifest")
    pack_validate.add_argument("source")
    pack_install = pack_sub.add_parser("install", help="install a pack through the full receipt boundary")
    pack_install.add_argument("source", nargs="?", default="builtin:core-1979")
    pack_install.add_argument("--root", default=".")
    pack_install.add_argument("--authority", default=".tcps/authority.json")
    pack_install.add_argument("--receipts", default=".tcps/receipts.ndjson")

    return parser


def _write_or_emit(value: Any, output: str | None) -> None:
    if output:
        write_json(output, value)
    else:
        _emit(value)


def _dfcm_queue(path: str) -> list[dict[str, Any]]:
    value = load_json(path)
    if not isinstance(value, dict) or value.get("schema") != "tcps.dfcm-queue.v1" or not isinstance(value.get("candidates"), list):
        raise ValueError("DfCM queue must be tcps.dfcm-queue.v1 with a candidates array")
    if set(value) != {"schema", "candidates"}:
        raise ValueError("DfCM queue contains undeclared fields")
    return value["candidates"]


def _dfcm_stages(path: str) -> list[dict[str, Any]]:
    value = load_json(path)
    if not isinstance(value, dict) or value.get("schema") != "tcps.dfcm-stages.v1" or not isinstance(value.get("stages"), list):
        raise ValueError("DfCM stages must be tcps.dfcm-stages.v1 with a stages array")
    if set(value) != {"schema", "stages"}:
        raise ValueError("DfCM stage observation contains undeclared fields")
    return value["stages"]


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
    return {
        "state": "PARTIAL_ALIVE",
        "workspace": str(path),
        "authority": str(authority_path),
        "next_pull": "tcps pack install builtin:core-1979",
    }


def _run_cycle(args: argparse.Namespace) -> dict[str, Any]:
    work = load_json(args.work)
    policy = load_authority(args.authority)
    observation = observe(work)
    graph = construct(observation)
    plan = select_and_authorize(graph, policy, Path(args.root))
    write_json(args.plan_out, plan)
    receipts = actuate(plan, policy, Path(args.root), Path(args.receipts))
    return {
        "state": "ALIVE",
        "subject": plan["subject"],
        "plan_digest": plan["plan_digest"],
        "receipt_count": len(receipts),
        "receipt_head": receipts[-1]["receipt_id"] if receipts else None,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            _emit(_init(Path(args.path)))
            return 0
        if args.command == "eve":
            _write_or_emit(observe(load_json(args.work)), args.out)
            return 0
        if args.command == "wizard":
            _write_or_emit(construct(load_json(args.observation)), args.out)
            return 0
        if args.command == "telco":
            value = select_and_authorize(load_json(args.graph), load_authority(args.authority), Path(args.root))
            _write_or_emit(value, args.out)
            return 0
        if args.command == "robot":
            receipts = actuate(load_json(args.plan), load_authority(args.authority), Path(args.root), Path(args.receipts))
            _emit({"state": "ALIVE", "receipts": receipts})
            return 0
        if args.command in {"run", "make"}:
            _emit(_run_cycle(args))
            return 0
        if args.command == "replay":
            result = replay(Path(args.receipts), Path(args.root))
            _emit(result)
            return 0 if result["state"] == "ALIVE" else 3
        if args.command == "recover":
            result = recover(Path(args.receipts), Path(args.root))
            _emit(result)
            return 0 if result["state"] in {"ALIVE", "PARTIAL_ALIVE"} else 3
        if args.command == "standard":
            _emit(standard_work())
            return 0
        if args.command == "kanban":
            _emit(kanban(args.subject, args.purpose, quantity=args.quantity, due_tick=args.due_tick))
            return 0
        if args.command == "wip":
            _emit(wip(Path(args.receipts)))
            return 0
        if args.command == "andon":
            result = andon(Path(args.receipts), Path(args.root))
            _emit(result)
            return 0 if result["state"] in {"ALIVE", "PARTIAL_ALIVE"} else 3
        if args.command == "metrics":
            result = metrics(Path(args.receipts), Path(args.root))
            _emit(result)
            return 0 if result["state"] in {"ALIVE", "PARTIAL_ALIVE"} else 3
        if args.command == "standing":
            result = standing(Path(args.receipts), Path(args.root))
            _emit(result)
            return 0 if result["state"] in {"ALIVE", "PARTIAL_ALIVE"} else 3
        if args.command == "kaizen":
            _emit(kaizen(args.reason, args.proposal))
            return 0
        if args.command == "dfcm":
            if args.dfcm_command == "plan":
                result = dfcm_plan(
                    _dfcm_queue(args.queue),
                    downstream_wip=args.downstream_wip,
                    downstream_limit=args.downstream_limit,
                    andon_active=args.andon_active,
                )
                _write_or_emit(result, args.out)
                return 0 if result["state"] == "PARTIAL_ALIVE" else 3
            if args.dfcm_command == "verify":
                result = verify_dfcm_plan(load_json(args.plan))
                _emit(result)
                return 0 if result["state"] == "ALIVE" else 3
            if args.dfcm_command == "flow":
                result = dfcm_flow_metrics(
                    args.available_ticks,
                    args.demand,
                    args.throughput,
                    args.wip,
                    observed_cycle_ticks=args.observed_cycle,
                    touch_ticks=args.touch,
                    lead_ticks=args.lead,
                )
                _emit(result)
                return 0
            if args.dfcm_command == "bottleneck":
                result = dfcm_bottleneck(_dfcm_stages(args.stages))
                _write_or_emit(result, args.out)
                return 0
            if args.dfcm_command == "kaizen":
                _emit(dfcm_kaizen(load_json(args.bottleneck)))
                return 0
        if args.command == "pack":
            if args.pack_command == "builtins":
                core = builtin_pack("core-1979")
                _emit({"schema": "tcps.pack-builtins.v1", "packs": [{"pack_id": core["pack_id"], "version": core["version"], "kind": core["kind"], "pack_digest": core["pack_digest"]}], "state": "ALIVE"})
                return 0
            if args.pack_command == "list":
                result = installed_packs(Path(args.root))
                _emit(result)
                return 0 if result["state"] == "ALIVE" else 3
            if args.pack_command == "validate":
                pack_value = load_pack(args.source)
                _emit({"schema": "tcps.pack-validation.v1", "pack_id": pack_value["pack_id"], "pack_digest": pack_value["pack_digest"], "state": "ALIVE"})
                return 0
            if args.pack_command == "install":
                result = install_pack(args.source, root=Path(args.root), authority_path=Path(args.authority), receipt_path=Path(args.receipts))
                _emit(result)
                return 0
        raise AssertionError("unreachable")
    except TCPSRefused as exc:
        _emit(exc.refusal.as_dict())
        return 2
    except ValueError as exc:
        _emit({"state": "REFUSED:CONTROL_INPUT_INVALID", "code": "CONTROL_INPUT_INVALID", "observed": str(exc), "repair": "supply a value admitted by the control-plane schema"})
        return 2
    except FileNotFoundError as exc:
        _emit({"state": "BLOCKED", "code": "INPUT_NOT_FOUND", "path": str(exc.filename), "repair": "provide the declared input without changing authority"})
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
