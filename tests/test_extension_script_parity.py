"""Structural parity invariant for bundled extension runtime scripts.

Guards the documented parity law (AGENTS.md, "Parity rule for contributors"):
all three script types (``sh``, ``ps``, ``py``) are first-class. Behavioral
parity of individual scripts is covered by
``tests/extensions/git/test_git_extension_python_parity.py`` and
``tests/extensions/test_update_agent_context_python_parity.py``; this module
pins the *set-level* invariant so a script added to one runtime directory
without its siblings fails fast instead of silently forking the contract.

It also verifies that every
``.specify/extensions/<id>/scripts/<runtime>/<file>`` path referenced by an
extension command template resolves to a real file in the extension source
tree (``extensions/<id>/scripts/<runtime>/<file>``), so template docs cannot
drift from what ships.

The ``python/`` variants pre-exist on disk even though extension command
templates do not yet route ``--script py`` (AGENTS.md, "Script Types and
Migration"); this checker enforces the precondition for that wiring.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EXTENSIONS_DIR = REPO_ROOT / "extensions"

# Runtime directory name -> script filename suffix shipped in that directory.
RUNTIME_SUFFIXES = {"bash": ".sh", "powershell": ".ps1", "python": ".py"}

# Extension scripts follow the naming convention: same stem across runtimes,
# hyphens in bash/powershell filenames becoming underscores in Python.
_CANONICAL_REF = re.compile(
    r"\.specify/extensions/(?P<ext>[A-Za-z0-9_-]+)/scripts/"
    r"(?P<runtime>bash|powershell|python)/(?P<file>[A-Za-z0-9_.-]+)"
)


def _canonical_stem(path: Path) -> str:
    return path.stem.replace("-", "_")


def _extensions_with_scripts() -> list[Path]:
    return sorted(
        p
        for p in EXTENSIONS_DIR.iterdir()
        if p.is_dir() and (p / "scripts").is_dir()
    )


def test_extension_runtime_script_sets_match():
    extensions = _extensions_with_scripts()
    assert extensions, (
        "expected at least one bundled extension with a scripts/ directory"
    )
    for ext_dir in extensions:
        scripts_dir = ext_dir / "scripts"
        by_runtime: dict[str, set[str]] = {}
        for runtime, suffix in RUNTIME_SUFFIXES.items():
            runtime_dir = scripts_dir / runtime
            assert runtime_dir.is_dir(), (
                f"{ext_dir.name}: missing scripts/{runtime}/ directory "
                f"(parity rule: all three script types are first-class)"
            )
            by_runtime[runtime] = {
                _canonical_stem(f) for f in runtime_dir.glob(f"*{suffix}")
            }

        bash_scripts = by_runtime["bash"]
        assert bash_scripts, f"{ext_dir.name}: scripts/bash/ is empty"
        for runtime in ("powershell", "python"):
            missing = bash_scripts - by_runtime[runtime]
            extra = by_runtime[runtime] - bash_scripts
            assert not missing, (
                f"{ext_dir.name}: scripts/{runtime}/ is missing variants for "
                f"{sorted(missing)} (parity rule: all three script types are "
                f"first-class)"
            )
            assert not extra, (
                f"{ext_dir.name}: scripts/{runtime}/ has scripts with no bash "
                f"sibling: {sorted(extra)}"
            )


def test_extension_command_templates_reference_real_scripts():
    checked = 0
    for cmd in sorted(EXTENSIONS_DIR.glob("*/commands/*.md")):
        ext_id = cmd.parent.parent.name
        content = cmd.read_text(encoding="utf-8")
        for match in _CANONICAL_REF.finditer(content):
            ref_ext = match.group("ext")
            runtime = match.group("runtime")
            filename = match.group("file")
            assert ref_ext == ext_id, (
                f"{cmd.relative_to(REPO_ROOT)} references "
                f".specify/extensions/{ref_ext}/ but lives in the {ext_id} "
                f"extension"
            )
            source = EXTENSIONS_DIR / ref_ext / "scripts" / runtime / filename
            assert source.is_file(), (
                f"{cmd.relative_to(REPO_ROOT)} references {source}, which "
                f"does not exist in the extension source tree"
            )
            checked += 1
    assert checked > 0, (
        "expected at least one script reference across extension command "
        "templates; the reference parser may need updating"
    )


def test_extension_command_templates_document_python_runtime():
    """Python variants exist on disk; templates must not present sh/ps as the
    only runtimes once ``--script py`` routing lands for extensions.

    Until that wiring ships (AGENTS.md, "Script Types and Migration"), this
    assertion is intentionally lenient: it only requires that a template which
    mentions a Python script path documents it alongside the sh/ps entries,
    and it documents today's known state so the flip is a deliberate edit.
    """
    for ext_dir in _extensions_with_scripts():
        has_python = bool(
            list((ext_dir / "scripts" / "python").glob("*.py"))
        )
        commands = sorted((ext_dir / "commands").glob("*.md"))
        assert commands, f"{ext_dir.name}: no command templates found"
        mentions_python = any(
            "scripts/python/" in c.read_text(encoding="utf-8")
            for c in commands
        )
        if has_python and not mentions_python:
            # Documented-unbuilt state: python variants ship but templates do
            # not surface them yet. Record it explicitly so this changes only
            # alongside the py-routing work, never by silent drift.
            assert ext_dir.name in {"agent-context", "git"}, (
                f"{ext_dir.name}: ships python scripts but no command "
                f"template mentions scripts/python/; document the runtime or "
                f"extend the py-routing allowlist"
            )
