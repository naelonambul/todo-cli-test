# Deterministic Scripts

Repository-controlled, deterministic behavior. Standard-library Python and Git only, so the control plane runs on any stack.

- `repo.py`: the control plane.
  - `status` computes change state and enforces lifecycle, approval, identity, write-scope, and agent-surface gates.
  - `verify` runs the checks registered in `../checks.json`.
- `tests/`: `unittest` fixtures for `repo.py`. Every hard guard has a failing negative case and a passing positive control. Run `python3 -m unittest discover -s scripts/tests -t .` from the repository root.
- `hooks/`: optional, agent-neutral guardrails that agent-specific hook configuration may call.

Do not add placeholder scripts that pretend to validate a stack that does not exist. When a product needs a multi-command check, add a stable wrapper here and register it in `checks.json`.
