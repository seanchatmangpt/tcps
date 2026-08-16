import json
from pathlib import Path

from tcps.cli import main


def test_init_and_run(tmp_path: Path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    capsys.readouterr()
    work = tmp_path / "work.json"
    work.write_text(
        json.dumps(
            {
                "schema": "tcps.work.v1",
                "subject": "cli-fixture",
                "purpose": "write one file",
                "observations": [{"kind": "request", "value": "write"}],
                "actions": [{"op": "write_text", "path": "artifact.txt", "content": "andon\n"}],
            }
        )
    )
    receipts = tmp_path / ".tcps/receipts.ndjson"
    plan = tmp_path / ".tcps/last-plan.json"
    assert (
        main(
            [
                "run",
                str(work),
                "--authority",
                str(tmp_path / ".tcps/authority.json"),
                "--root",
                str(tmp_path),
                "--receipts",
                str(receipts),
                "--plan-out",
                str(plan),
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "ALIVE"
    assert (tmp_path / "artifact.txt").read_text() == "andon\n"
    assert main(["replay", "--receipts", str(receipts), "--root", str(tmp_path)]) == 0
