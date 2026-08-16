set shell := ["bash", "-euo", "pipefail", "-c"]

verify:
    python3 scripts/release_verifier.py

test:
    PYTHONPATH=src python3 -m pytest -q

identity-zero:
    python3 scripts/verify_reconstitution.py

bundle:
    python3 scripts/build_offline_bundle.py --check-determinism

project:
    ggen sync run
