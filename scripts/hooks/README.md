# Hook Implementations

Put fast, deterministic, agent-neutral guardrails here when the repository needs them. Agent-specific hook configuration should call these scripts rather than duplicate their policy.

Good candidates include:

- protected-path checks;
- secret or credential checks;
- narrowly scoped formatting or lint checks;
- prevention of unsafe repository mutations;
- refusing agent edits to the `approvals` of a `changes/<id>/change.json`.

The last one adds friction and an audit trail, but it is **not authentication**. An agent that can edit the hook, its configuration, or the repository can bypass it. `repo.py` therefore never upgrades an approval to `verified` because such a hook exists.

Long-running suites belong in `repo.py verify` and CI, not in per-edit hooks. Routine human approval prompts do not belong in hooks either.
