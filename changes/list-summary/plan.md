# Implementation Plan

## Summary

Implement the approved `list` summary line (`changes/list-summary/spec.md`, "List summary"). When at least one todo exists, `list` prints one final line, `<N> todos, <M> complete`, using `todo` when N is 1. An empty store still prints only `No todos.`.

This is a `behavior` change against the frozen `product-init` baseline:

- the root `intent.md` is unchanged;
- at closure, the root `spec.md` is replaced by the approved packet copy.

## Files and components that change

Final `write_scope` in `change.json`:

```json
["spec.md", "todo_cli/cli.py", "tests/test_cli.py"]
```

| Path | Change |
|---|---|
| `todo_cli/cli.py` | In the `list` branch, after printing the todo lines, print the summary line. No other command changes. |
| `tests/test_cli.py` | Update the four existing exact `list` assertions to expect the summary line. Add one focused test for the summary format. |
| `spec.md` (root) | At closure, replaced whole by the packet copy. |
| `changes/list-summary/**` | The packet: `change.json`, `spec.md`, `plan.md`, and `closure.json` at closure. |

Out of scope:

- `todo_cli/store.py`;
- other test modules;
- `README.md`: its one-line description, "`list` shows all todos", stays accurate;
- `checks.json`: the existing `product-tests` check already routes `todo_cli/**` and `tests/**`;
- the root `intent.md`, `.github/**`, `scripts/**`, and any other path.

## Order of work

1. **Plan approval (owner).** The owner approves the exact `plan.md` digest printed by `status`. The agent records the claim and confirms `stage=implementation readiness=ready`. Nothing outside `changes/list-summary/` changes before this.
2. **Packet commit.** Commit the packet (`change.json` with the spec and plan claims, `spec.md`, `plan.md`) on `change/list-summary` as the App (`agent-git`).
3. **Implementation.** In `todo_cli/cli.py`, after the todo lines, compute `total = len(todos)` and `done = sum(1 for t in todos if t["done"])`. Print `f"{total} {'todo' if total == 1 else 'todos'}, {done} complete"`. The empty-store branch is unchanged.
4. **Tests** in `tests/test_cli.py`:
   - Update the existing exact `list` outputs at the four current assertions (add/list persistence, the mixed idempotent-complete listing, delete/ID stability, and the default-location listing), so each also expects the correct summary line.
   - Add `test_list_summary_line`, covering:
     - a single incomplete todo: `1 todo, 0 complete`;
     - two todos with one complete: `2 todos, 1 complete`;
     - all complete: `3 todos, 3 complete`;
     - a summary that follows the last todo line with no blank line;
     - an empty store that still prints exactly `No todos.\n`.
5. **Local verification.**
   - Run `python3 -m unittest discover -s tests -t . -v`.
   - Run `python3 scripts/repo.py verify --change list-summary`: `control-plane` and `product-tests` must pass.
   - Run `python3 scripts/repo.py verify --full`.
   - None may report `failed`, `blocked` or `not-run`.
6. **Self-review.** Review the diff against `REVIEW.md` and the approved spec. Confirm only in-scope paths changed and no `.evidence/` or cache files are included.
7. **Baseline update and verification.**
   - Replace the root `spec.md` with a byte copy of `changes/list-summary/spec.md`. Confirm the root digest equals the approved `6560fb2e…5253` and that the root `intent.md` is unchanged.
   - Re-run `verify --change list-summary` and `verify --full`, and keep their evidence paths.
8. **Candidate closure.** Add `changes/list-summary/closure.json` with only the fields `repo.py` accepts:
   - `schema`: `1`;
   - `baseline`: exactly `{"spec.md": <resulting root digest>}`. The packet carries only `spec.md`, so the closure lists only that artifact;
   - `packet_sha256`: computed with `repo.py`'s `packet_digest(worktree_packet(...))`;
   - `evidence`: only the step 7 local verify evidence paths.

   Confirm `status --change list-summary` reports `stage=closed freshness=current approval=unverified readiness=ready closure=candidate` and `status: ok`.
9. **Commit, push and pull request.**
   - Commit the implementation, baseline update and `closure.json` as the App.
   - Push with `agent-git`.
   - Open a PR with `agent-gh`. The body starts with `Change-ID: list-summary` and follows the PR template.
10. **CI on the closure-containing head.** `summary` must be success. The agent records the run URL, head SHA and result in a PR comment, not in `closure.json`.
11. **Changes before merge.** If CI or review requires further commits after the closure exists, each fix commit, in that same commit:
    - re-runs both local verifications;
    - replaces the closure `evidence` with the new local evidence paths;
    - recomputes `packet_sha256` if a packet file changed, and `baseline` if the root `spec.md` changed;
    - confirms `closure=candidate`.

    CI results go in the PR only, so there is never a closure-only commit made just to cite a CI run.
12. **Human review and merge (owner).**
    - The owner reviews and approves as `naelonambul`. The ruleset requires an approval from someone other than the pusher and dismisses stale approvals.
    - The owner squash-merges.
    - The agent does not approve, merge, or enable auto-merge.
13. **Post-merge confirmation.**
    - The `push` run on `main` succeeds.
    - `repo.py status` on `main` reports `list-summary` as `stage=closed freshness=frozen closure=frozen`, anchored at the squash commit.
    - `product-init` remains frozen at `2b60efb`.

## Tests and proof

| Spec item | Proof |
|---|---|
| FR2 and "List summary": the line is present, its format, and singular/plural | `test_list_summary_line`, plus the four updated exact-output assertions |
| No blank line before the summary | exact full-stdout equality in all list tests |
| Empty store prints only `No todos.` | the existing `test_empty_store_and_missing_file_list`, unchanged |
| Acceptance criterion 5 (mixed listing, ordering, summary) | the updated mixed idempotent-complete listing test |
| No regression in other behaviour | the full existing suite, via `product-tests` |

All new and updated tests use the existing `IsolatedTestCase` helper, so the temporary-`HOME` isolation is unchanged.

## Risks and mitigations

- **Anyone parsing `list` output line by line** now sees one extra line. This is accepted by the approved spec, and there are no known consumers.
- **Baseline staleness.** If another change updates the root `intent.md` or `spec.md` before this merges, `status` reports this change as `stale`. Mitigation: refresh the baseline and get a fresh approval.
- **Closure invalidated by late edits.** Handled by step 11.

## Rollback or recovery

- **Before merge:** close the PR. Nothing reaches `main`.
- **After merge:** revert in a new change packet. The frozen `list-summary` packet is never edited.

## Open questions

None.
