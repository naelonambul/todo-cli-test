# Implementation Plan

## Summary

Implement the approved `edit` command (`changes/edit-todo/spec.md`, FR9, "Edit", and acceptance criterion 12). `edit ID TEXT...` replaces one todo's text and keeps its identifier, completion state, position in the data file and the store's `next_id`. Text uses the `add` rules and is validated before the data file is read.

This is a `behavior` change against the frozen `list-summary` baseline:

- the root `intent.md` is unchanged;
- at closure, the root `spec.md` is replaced by the approved packet copy.

The change is also a weak-worker execution pilot. It follows the `change-execution` method of Template v2: a coordinator writes a protected oracle test and a closed worker brief, and one fresh economy-tier worker implements. The worker's model is chosen by the coordinator when it spawns the worker and is recorded in the pull request. No model or harness configuration is added to the repository.

## Files and components that change

Final `write_scope` in `change.json`:

```json
["spec.md", "todo_cli/cli.py", "todo_cli/store.py", "tests/test_cli.py", "tests/test_store.py", "tests/test_edit_acceptance.py"]
```

| Path | Written by | Change |
|---|---|---|
| `tests/test_edit_acceptance.py` | coordinator, before the worker starts | New protected oracle: product acceptance tests for `edit` through the real `python3 -m todo_cli` entry point, with literal expected values. |
| `todo_cli/store.py` | worker | Add `edit(data, todo_id, text)`, shaped like `complete`: return a changed copy of the store and the edited todo, or raise `KeyError(todo_id)`. It changes only that todo's `text`. |
| `todo_cli/cli.py` | worker | Add the `edit` subparser (`id` with `type=positive_id`, `text` with `nargs="+"`) and its dispatch branch: validate text with `_validate_text`, then load, then `store.edit`, then `store.save`, then print `Edited <id>: <text>`. Map `KeyError` to `ValueError(f"no todo with id {args.id}")`, as `delete` does. |
| `tests/test_store.py` | worker | Unit test for `store.edit`: text replaced, other fields and other todos unchanged, input not mutated, unknown id raises `KeyError`. |
| `tests/test_cli.py` | worker | Extend the existing per-command tables to include `edit`: the corrupt-file test (`("edit", "1", "new")`), the unknown-id test and the malformed-id test. |
| `spec.md` (root) | coordinator, at closure | Replaced whole by the packet copy. |
| `changes/edit-todo/**` | coordinator | The packet: `change.json`, `spec.md`, `plan.md`, and `closure.json` at closure. |

Out of scope:

- `README.md`. Its command line (line 7) stays accurate but does not mention `edit`; a follow-up change may update it.
- `checks.json`: the existing `product-tests` check already routes `todo_cli/**` and `tests/**`, and discovers `tests/test_edit_acceptance.py`.
- `todo_cli/__main__.py`, `tests/support.py`, the root `intent.md`, `.github/**`, `scripts/**`, `.agents/**`, and any other path.
- Any data schema or `version` change, and any new dependency.

## Order of work

1. **Spec and plan approval (owner).** The owner approves the exact `spec.md` and `plan.md` digests printed by `status`. The coordinator records the spec claim, then the plan claim, and confirms `stage=implementation readiness=ready`. Nothing outside `changes/edit-todo/` changes before this.
2. **Packet commit.** Commit the packet (`change.json` with both claims, `spec.md`, `plan.md`) on `change/edit-todo` as the App (`agent-git`).
3. **Oracle (coordinator).** Write `tests/test_edit_acceptance.py` (see "Protected oracle"). Commit it as the App before the worker starts. Proof: `python3 -m unittest tests.test_edit_acceptance -v` fails only because `edit` does not exist yet (argparse exit 2 instead of the expected results). Record its SHA-256.
4. **Worker brief (coordinator).** Fill the `change-execution` worker brief from this plan, with no placeholder left:
   - GOAL: implement `edit` as specified;
   - FILES: exactly `todo_cli/store.py`, `todo_cli/cli.py`, `tests/test_store.py`, `tests/test_cli.py`;
   - PROTECTED: exactly `tests/test_edit_acceptance.py`;
   - READ: `todo_cli/cli.py`, `todo_cli/store.py`, `tests/support.py`, `tests/test_cli.py`, `tests/test_store.py`, `tests/test_edit_acceptance.py`, and the spec lines for FR9, "Text", "Edit" and the error table, quoted verbatim;
   - ACCEPTANCE: the literal outputs from the spec (`Edited <id>: <text>`, `todo_cli: error: no todo with id <id>`, the two existing text-validation messages, exit statuses 0/1/2, byte-identical data file on every error);
   - VERIFY: `python3 -m unittest tests.test_edit_acceptance -v` → exit 0; `python3 -m unittest discover -s tests -t . -v` → exit 0;
   - FORBIDDEN and STOP as in the template, with no network and no dependency installation.

   The brief is kept outside the repository and summarised in the pull request.
5. **Worker (economy tier).** Spawn one fresh, non-interactive worker with only the brief and repository access, stdin closed, a workspace-write sandbox and no network. It does not commit.
6. **Mechanical acceptance (coordinator).** Regardless of the worker's reported status:
   - every path in `git status --porcelain` is inside FILES;
   - `git diff --exit-code -- tests/test_edit_acceptance.py` passes and its SHA-256 equals the step 3 value;
   - re-run both VERIFY commands;
   - `python3 scripts/repo.py status --change edit-todo` and `python3 scripts/repo.py verify --change edit-todo` report no `failed`, `blocked` or `not-run` check;
   - read the diff, including the worker's own tests, against the spec and `REVIEW.md`.
7. **Retry or escalate.** If step 6 fails, spawn a fresh worker with the same brief plus only the concrete failure evidence. At most two failed retries. After that, record an economy-worker failure and implement at a higher tier (a stronger worker or the coordinator). Never weaken the oracle, ACCEPTANCE or scope to obtain a pass. A retry, a diff clearly larger than this plan implies, or an ambiguity triggers one read-only reviewer using the `change-execution` review brief.
8. **Commit accepted work.** The coordinator commits the accepted implementation as the App. Workers never commit.
9. **Baseline update and verification.**
   - Replace the root `spec.md` with a byte copy of `changes/edit-todo/spec.md`. Confirm the root digest equals the approved spec digest and that the root `intent.md` is unchanged.
   - Run `python3 scripts/repo.py verify --change edit-todo` and `python3 scripts/repo.py verify --full`, and keep their evidence paths.
10. **Candidate closure.** Add `changes/edit-todo/closure.json` with only:
    - `schema`: `1`;
    - `baseline`: exactly `{"spec.md": <resulting root digest>}`;
    - `packet_sha256`: computed with `repo.py`'s `packet_digest(worktree_packet(...))`;
    - `evidence`: only the step 9 local verify evidence paths.

    Confirm `status --change edit-todo` reports `stage=closed freshness=current approval=unverified readiness=ready closure=candidate` and `status: ok`.
11. **Commit, push and pull request.** Commit the baseline update and `closure.json` as the App, push with `agent-git`, and open a PR with `agent-gh`. The body starts with `Change-ID: edit-todo`. Its Verification section records the route, the worker's tier and model, each attempt with the worker-reported status and the coordinator's acceptance result, and the commands the coordinator re-ran.
12. **CI on the closure-containing head.** `summary` must be success. Record the run URL, head SHA and result in a PR comment, not in `closure.json`.
13. **Changes before merge.** If CI or review requires further commits after the closure exists, each fix commit re-runs both local verifications, replaces the closure `evidence`, recomputes `packet_sha256` and `baseline` if needed, and confirms `closure=candidate`, all in that same commit.
14. **Human review and merge (owner).** The owner reviews, approves and squash-merges. The agent does not approve, merge, or enable auto-merge.
15. **Post-merge confirmation.** The `push` run on `main` succeeds, and `repo.py status` on `main` reports `edit-todo` as `stage=closed freshness=frozen closure=frozen`, anchored at the squash commit.

## Protected oracle

`tests/test_edit_acceptance.py` uses the shared `IsolatedTestCase` and runs the real entry point as a subprocess. Every expected value is a literal. It covers:

| Case | Expected |
|---|---|
| Edit an incomplete todo among two | `Edited 1: buy oat milk\n`, exit 0, empty stderr; stored todos are exactly `[{"id": 1, "text": "buy oat milk", "done": false}, {"id": 2, "text": "call the bank", "done": false}]`, `next_id` 3 |
| Words are normalized like `add` | `edit 1 "  spaced" "words  "` prints `Edited 1: spaced words` |
| Edit a completed todo | `done` stays `true`; `list` prints `[x] 1 renamed\n[ ] 2 second\n2 todos, 1 complete\n` |
| Stable id, `next_id` and position | from a hand-written valid file whose todos are in the order id 3, id 1 with `next_id` 5, editing 1 keeps that order, both ids and `next_id` 5; a later `add` gets id 5 |
| Persistence | each step is a separate process; a later `list` shows the edited text |
| Same text | editing a todo to its current text succeeds with the same message |
| Unknown id | `edit 7 new text`: exit 1, empty stdout, stderr exactly `todo_cli: error: no todo with id 7\n`, file byte-identical; on a missing file, the same error and no file is created |
| Malformed id | `0`, `-1`, `abc`, `1.5`: exit 2, empty stdout, `usage:` in stderr, file byte-identical; `edit 1` with no text also exits 2 |
| Invalid text | empty, whitespace-only, and representative control characters (`\n`, `\t`, `\x1c`, `\x85`, ` `): exit 1, empty stdout, the exact existing message, file byte-identical |
| Text validated first | invalid text with an unknown id, and with a corrupt data file, reports the text error |
| Corrupt data file | `{`: exit 1, empty stdout, `todo_cli: error: cannot read data file` in stderr, file byte-identical |

The oracle is a product acceptance artifact. It tests only observable CLI behaviour and the data file, never the worker's internal names.

## Tests and proof

| Spec item | Proof |
|---|---|
| FR9, "Edit", acceptance criterion 12 | `tests/test_edit_acceptance.py` |
| "Text" rules for `edit`, criterion 6 | oracle invalid-text and normalization cases |
| Criterion 7 for `edit` | oracle unknown-id case, and the extended unknown-id test in `tests/test_cli.py` |
| Criterion 8 and 9 for `edit` | oracle malformed-id and corrupt-file cases, and the extended tables in `tests/test_cli.py` |
| NFR3 atomic write | `edit` saves only through the existing `store.save` (diff review) |
| No regression | the full existing suite, via `product-tests` |

## Risks and mitigations

- **Weak worker drifts outside scope or edits the oracle.** Mitigated by FILES/PROTECTED in the brief and the mechanical checks in step 6. A violation fails the attempt.
- **Worker's own tests assert nothing useful.** Acceptance rests on the protected oracle and a coordinator diff review, not on the worker's tests.
- **Mutation of the loaded store.** `store.edit` must return a copy, as `complete` does. Checked by the worker's store test and diff review.
- **Baseline staleness.** If another change updates the root `intent.md` or `spec.md` before this merges, `status` reports this change as `stale`. Mitigation: refresh and re-approve.
- **Closure invalidated by late edits.** Handled by step 13.

## Rollback or recovery

- **Before merge:** close the PR. Nothing reaches `main`.
- **After merge:** revert in a new change packet. The frozen `edit-todo` packet is never edited.

## Open questions

None.
