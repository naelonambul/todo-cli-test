# Implementation Plan

## Summary

Add `verify-todo`, a project-local verification skill with a feature map. It lets any agent drive the real `todo_cli` command line the way a user does, capture evidence and clean up, without reading the source. The skill follows the Template v2 `verification-map` method (frozen at template commit `b25ff090b87ce1e962002277bc0a26ee820d866e`). The method is used as a reference; the `verification-map` skill itself is not copied into this repository.

The skill is **proven end to end** before the change closes:

1. launch;
2. doctor;
3. drive the `edit` feature on every reachable path;
4. capture evidence;
5. clean up;
6. confirm the evidence still exists.

The coordinator runs this proof first. Then a fresh agent runs it again with only the skill as instruction.

This is a `repository` change. It inherits no product baseline, and changes no product code, tests, `checks.json`, CI or root artifact. Registered checks remain the only automatic gate. The skill produces local evidence only.

## Files and components that change

Final `write_scope`:

```json
[".agents/skills/verify-todo/", ".claude/skills/verify-todo"]
```

| Path | Change |
|---|---|
| `.agents/skills/verify-todo/SKILL.md` | The skill: frontmatter plus Launch, Doctor, Drive, Evidence and Cleanup sections. |
| `.agents/skills/verify-todo/drive.py` | An executable helper using only the Python standard library (details below). |
| `.agents/skills/verify-todo/features/README.md` | Shared preconditions, proof and skip rules, sweep order, and an index. |
| `.agents/skills/verify-todo/features/{add,list,complete,delete,edit}.md` | One file per command, in the frozen feature-file shape: Sub-features, How to get to it, Driving it, Gotchas. |
| `.claude/skills/verify-todo` | A relative symlink to `../../.agents/skills/verify-todo`. |

Out of scope: `todo_cli/**`, `tests/**`, `scripts/**`, `checks.json`, `.github/**`, `.gitignore`, root `intent.md`/`spec.md`, other skills, and every frozen packet.

## Skill design

- **Surface.** The CLI `python3 -m todo_cli <command>` from the repository root. It is short-lived and has no build step.
- **Isolation.** Every run gets its own directory, `<run>` = `.evidence/verify-todo/<UTC timestamp>-<pid>/`. It holds:
  - `home/`, used as `HOME`;
  - `data/todos.json`, set as `TODO_CLI_FILE`;
  - `steps/`, the evidence.

  `.evidence/` is already gitignored. The skill never uses the default data path `~/.todo-cli-test/todos.json` and never uses the user's real `HOME`.
- **Launch.** No build. Launch creates `<run>` and sets `HOME` and `TODO_CLI_FILE` for this run only.
- **Doctor.** Read-only. It records:
  - `python3 --version` is 3.x;
  - `python3 -m todo_cli --help` exits 0 and lists `add`, `list`, `complete`, `edit` and `delete`;
  - the resolved data path is inside `<run>`;
  - `git rev-parse HEAD` and `git status --porcelain`, which identify the build being driven.

  If any check fails, the skill stops.
- **Drive.** Exact commands from this repository, for example `python3 -m todo_cli edit 1 buy oat milk`. Each step goes through `drive.py`.
- **`drive.py`.** `drive.py step <run> <name> -- <argv...>` runs one command with the run's environment and writes `steps/<n>-<name>.json`, containing:
  - `argv`, exit code, stdout and stderr;
  - the data file's bytes (base64) and sha256, before and after.

  `drive.py doctor <run>` and `drive.py cleanup <run>` implement those sections. The helper holds no product logic and asserts no expected values; the expected values live in the feature files.
- **Evidence.**
  - Each feature file states the expected exit code, exact output and data-file effect for each path.
  - The agent compares the step records against those expectations and writes `<run>/summary.md`, one pass or fail line per step.
  - Side effects are judged from the recorded data-file bytes, not only from printed output.
- **Cleanup.** Remove only `<run>/home/` and `<run>/data/`. `steps/`, `doctor.json` and `summary.md` are kept. Nothing is left running, because the CLI is short-lived.

### Edit feature paths (the proof)

The expected values come from root `spec.md` (FR9 and the error table):

- edit an incomplete todo;
- edit a completed todo, which stays done;
- `list` after the edit shows the new text and the existing summary line;
- an unknown id gives exit 1 and the exact error, and the data file is byte-identical;
- a malformed id (`0`, `abc`) gives exit 2, and the data file is byte-identical;
- empty text and control-character text give exit 1 and the exact errors, and the data file is byte-identical;
- the `id` and `next_id` are unchanged;
- persistence across separate invocations.

## Order of work

1. **Plan approval (owner).** The owner approves the exact `plan.md` digest. The coordinator records the claim, confirms `readiness=ready`, and commits the packet as the App.
2. **Write the skill**, the helper, the feature map and the adapter symlink. The feature files are checked against the current `todo_cli/cli.py`, `todo_cli/store.py` and `spec.md`.
3. **Coordinator proof.** Follow the skill literally: launch, doctor, drive every `edit` path above, write the summary, clean up. Then show that:
   - `steps/`, `doctor.json` and `summary.md` still exist;
   - `home/` and `data/` are gone;
   - `git status --porcelain` shows no tracked-file change from the run;
   - `~/.todo-cli-test/` was not created or touched.

   Any step that fails because the skill is wrong or unclear is fixed in the skill and proved again. A product defect is reported, and kept out of this change.
4. **Independent proof.** Spawn one fresh economy-tier agent in a separate harness. Its only instruction is "verify the `edit` feature using `.agents/skills/verify-todo`, then report where the evidence is".

   The coordinator accepts the result mechanically, not from the agent's report:
   - the evidence files exist and match the feature file's expected values;
   - cleanup ran;
   - no tracked file changed.

   The agent may write only under `.evidence/`. If it fails because of the skill, the skill is fixed, and steps 3 and 4 are repeated at most twice.
5. **Verification.**
   - `python3 scripts/repo.py verify --change verify-todo` and `verify --full` report no `failed`, `blocked` or `not-run`;
   - `status --change verify-todo` shows `status: ok`, including the adapter symlink check.
6. **Review.** Selective review is not triggered: the change adds no product code, public interface or registered check. If the independent proof needed a skill fix, one read-only reviewer is run on the final skill.
7. **Candidate closure, PR and CI**, as in the lifecycle:
   - `closure.json` with `baseline: {}` and local evidence. The evidence cites both proof runs' `summary.md` paths and their sha256.
   - A PR starting `Change-ID: verify-todo`.
   - CI `summary` passing on the closure-containing head, recorded in a PR comment.
8. **Human review and merge (owner).** The agent does not approve or merge.
9. **Post-merge.** The `main` push run passes, and `verify-todo` is `frozen`.

## Tests and proof

| Claim | Proof |
|---|---|
| The skill drives the real product with isolated data | the coordinator proof: the doctor records the data path inside `<run>`, and no tracked-file or default data-path change |
| The feature map is accurate for `edit` | every `edit` path's recorded exit, output and data bytes match `edit.md`, which matches `spec.md` |
| Cleanup keeps the evidence | after cleanup, the evidence files exist and the run's `home/` and `data/` are gone |
| Usable without context | the independent agent run, accepted mechanically |
| Adapter present | `status` symlink check |
| No regression | `verify --full` (`control-plane`, `product-tests`) |

The `add`, `list`, `complete` and `delete` feature files are source-checked but not live-driven in this change. The summary says so. A later maintenance pass drives them.

## Risks and mitigations

- **Evidence mistaken for a gate.** The skill states that registered checks are the only automatic gate.
- **Driving the user's real data.** The launch is refused unless the resolved data path is inside `<run>`.
- **Helper hides logic.** `drive.py` only runs commands and records the results; the expectations are in the feature files.

## Rollback or recovery

Revert the squash commit. The product is not affected.

## Open questions

None.
