# Implementation Plan

## Summary

Implement the approved `todo_cli` product (`changes/product-init/intent.md`, `changes/product-init/spec.md`) as a standard-library Python package at the repository root, with a standard-library `unittest` suite. Register that suite as a `core` check in `checks.json`, so the existing `verify-core` CI job runs it without any workflow change. Then close the change:

- replace the root `intent.md` and `spec.md` with the approved packet copies;
- add a candidate `closure.json`;
- open a pull request as the `naelonambul-agent` App with `Change-ID: product-init`;
- the owner reviews and squash-merges it, and the closure becomes frozen on `main`.

The approved intent and spec are authoritative throughout. This plan adds no behaviour beyond them.

## Files and components that change

Final `write_scope` in `change.json`:

```json
["intent.md", "spec.md", "checks.json", "todo_cli/**", "tests/**", "README.md"]
```

| Path | Change |
|---|---|
| `todo_cli/__init__.py` | New. Package marker with a one-line docstring. |
| `todo_cli/__main__.py` | New. `raise SystemExit(main())` using `todo_cli.cli.main`. |
| `todo_cli/cli.py` | New. `argparse` parser and commands, output formatting, error-to-exit-status mapping, and `main(argv=None) -> int`. |
| `todo_cli/store.py` | New. Resolves the data path, loads and validates the JSON, assigns identifiers, and saves atomically. No terminal output. |
| `tests/__init__.py` | New, empty. Lets `unittest discover -t .` import `tests.*`. |
| `tests/support.py` | New. The shared isolation helper (see "Tests and proof"). |
| `tests/test_store.py` | New. Unit tests for path resolution, load and validation, identifier assignment, and atomic save. |
| `tests/test_cli.py` | New. In-process tests of `main()` and subprocess tests of `python3 -m todo_cli`, covering spec acceptance criteria 1–11. |
| `checks.json` | Add the `product-tests` check (below). The existing `control-plane` check is unchanged. |
| `README.md` | Add a short "Todo CLI" usage section at the top: invocation, the four commands, the default data path, `TODO_CLI_FILE`, and how to run the tests. The template sections below it are unchanged. |
| `intent.md`, `spec.md` (root) | At closure, replaced whole by the packet copies. This removes the `sdlc:baseline-unestablished` marker. |
| `changes/product-init/**` | The packet itself: `change.json` (approval claims), `plan.md`, and `closure.json` at closure. |

Explicitly out of scope: `.github/**` (including `.github/workflows/**`), `scripts/**`, `.agents/**`, `.claude/**`, `AGENTS.md`, `REVIEW.md`, `docs/**`, and any `pyproject.toml` or packaging file.

### `checks.json` addition

```json
{
  "id": "product-tests",
  "group": "core",
  "argv": ["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
  "cwd": ".",
  "timeout_seconds": 300,
  "paths": ["todo_cli/**", "tests/**", "checks.json"],
  "requires": ["python3"]
}
```

Using group `core` puts the check in the existing `verify-core` CI job, so no workflow edit is needed. On pushes to `main`, `verify --full` runs it regardless of routing.

## Order of work

Each step keeps `repo.py status --change product-init` at `status: ok`.

1. **Plan approval (owner).** The owner approves the exact `plan.md` digest printed by `status`. The agent records the claim in `change.json` and confirms `stage=implementation readiness=ready`. Nothing outside `changes/product-init/` changes before this.
2. **Packet commit.** Commit the packet (`change.json` with three approval claims, `intent.md`, `spec.md`, `plan.md`) on branch `change/product-init`. The commit is authored as the App (`agent-git`, bot name `naelonambul-agent[bot]`).
3. **Store.** Implement `todo_cli/store.py`:
   - **Path resolution:** use `TODO_CLI_FILE` when it is non-empty, otherwise `~/.todo-cli-test/todos.json`. Expand `~` and make the path absolute. The path is resolved at call time, never at import time, so tests can change the environment.
   - **Load:** a missing file is an empty store with `next_id` 1. Otherwise parse UTF-8 JSON and validate the spec schema (`version == 1`; `next_id` an integer at least 1 and greater than every `id`; unique positive-integer `id`; non-empty string `text`; boolean `done`). Any failure raises a read error that names the path and the reason.
   - **Save:** create parent directories, write JSON with 2-space indentation and a trailing newline to a `tempfile.NamedTemporaryFile` in the same directory, flush and `fsync`, then `os.replace`. Remove the temporary file on failure. Any `OSError` becomes a write error.
   - **Operations** (`add`, `complete`, `delete`): pure functions on the loaded data. `add` uses `next_id` and then increments it, so deleting the highest identifier never frees it.
4. **CLI.** Implement `todo_cli/cli.py` and `__main__.py`:
   - subcommands `add TEXT...`, `list`, `complete ID`, `delete ID`;
   - `ID` parsed by an `argparse` type that accepts only positive decimal integers (usage errors exit 2);
   - text joined with single spaces and stripped; empty text, or text containing any character that can break a terminal line, is exit 1. The rejected set is Unicode categories `Cc` (C0/C1 controls, including `\n`, `\r`, `\v`, `\f`, `\x1c`–`\x1e` and U+0085), `Zl` (U+2028 line separator) and `Zp` (U+2029 paragraph separator). This covers every boundary recognised by `str.splitlines()`, and accepted text always satisfies `text.splitlines() == [text]`;
   - output exactly as specified;
   - errors to stderr as `todo_cli: error: <message>` with exit 1, and nothing on stdout;
   - validation, lookup and loading all happen before any save, so errors never write.
5. **Tests.** Add `tests/support.py`, `tests/test_store.py` and `tests/test_cli.py` (see "Tests and proof").
6. **Check registration and docs.** Add `product-tests` to `checks.json` and the usage section to `README.md`.
7. **Local verification.**
   - Run `python3 -m unittest discover -s tests -t . -v` and `python3 scripts/repo.py verify --change product-init`. Both must report no `failed`, `blocked` or `not-run` check.
   - Run `python3 scripts/repo.py verify --full` to cover the post-merge configuration.
   - Run a short manual session against a temporary `TODO_CLI_FILE` and record the transcript in the PR description.
8. **Self-review.** Review the diff against `REVIEW.md` and the approved intent and spec. Confirm there is no generated metadata, no credentials, no `.evidence/`, and no path outside `write_scope`.
9. **Baseline update and local verification.**
    - Replace the root `intent.md` and `spec.md` with byte copies of the packet files. Confirm `status` still reports `status: ok`, and that the root digests equal the approved digests (`5acae8a6…0dbd`, `a3096645…5b5b`).
    - Re-run `python3 scripts/repo.py verify --change product-init` and `python3 scripts/repo.py verify --full` on this tree. Both must report no `failed`, `blocked` or `not-run` check.
    - Keep their existing `.evidence/<timestamp>/evidence.json` paths.
10. **Candidate closure.** Add `changes/product-init/closure.json`, using only the schema fields `repo.py` accepts (`schema`, `baseline`, `packet_sha256`, `evidence`):
    - `schema`: `1`;
    - `baseline`: the resulting root digests of exactly `intent.md` and `spec.md`;
    - `packet_sha256`: computed with `scripts/repo.py`'s own `packet_digest(worktree_packet(...))`, not by hand;
    - `evidence`: only evidence that already exists when the closure is written, namely the local `verify` evidence paths from step 9. It contains no PR or CI reference: `repo.py` requires only a non-empty list of non-empty strings.

    Confirm `python3 scripts/repo.py status --change product-init` reports `status: ok` with `stage=closed freshness=current approval=unverified readiness=ready closure=candidate`. `repo.py` sets `stage=closed` as soon as `closure.json` exists. `closure=candidate` means the closure is not yet anchored on `main`.
11. **Commit, push and pull request.**
    - Commit the completed change, including `closure.json`, on `change/product-init` as the App.
    - Push with `agent-git`.
    - Open a PR against `main` with `agent-gh`. The body follows `.github/pull_request_template.md` and starts with `Change-ID: product-init`; it covers the local verification results and evidence paths, "Plan deviation: none" (or the details), and remaining risks.
    - The PR is authored by `app/naelonambul-agent`.
12. **CI on the closure-containing head.**
    - The `repository` workflow must end with `summary` = success on this head: `control-plane-tests`, `status` (which validates the candidate closure), and `verify-core` including `product-tests`.
    - The agent records the run URL, head SHA and result in the PR (a comment or the description's Verification section) for review. It does not go into `closure.json`.
    - On failure, the agent fixes within scope and follows step 13's rules for later commits.

13. **Changes before merge.** If CI or review requires further commits after the closure exists, each fix commit keeps the closure current in the same commit:
    - re-run `python3 scripts/repo.py verify --change product-init` and `verify --full` on the fixed tree;
    - replace `closure.json`'s `evidence` with the new local evidence paths, so the closure cites verification of the tree it closes;
    - recompute `packet_sha256` if a packet file changed, and `baseline` if a root `intent.md` or `spec.md` changed (neither is expected);
    - confirm `status --change product-init` still reports `closure=candidate`.

    `packet_sha256` excludes `closure.json`, so updating `evidence` never changes the digest. Only local evidence, which exists before the commit, is cited. The CI result for each new head is reported in the PR, never in the closure, so no closure-only commit is made to cite a CI run and no cycle arises. The final head must again pass `summary`.
14. **Human review and merge (owner).**
    - The owner reviews the final head against `REVIEW.md` and approves it as `naelonambul`. The App cannot approve its own PR, and the ruleset requires the most recent push to be approved by someone other than the pusher.
    - Because stale approvals are dismissed, any later push needs a fresh approval.
    - The owner squash-merges, the only method the ruleset allows.
    - The agent does not merge, and does not enable auto-merge unless asked.
15. **Post-merge confirmation.**
    - The `push` run on `main` (`verify --full`) must succeed.
    - `python3 scripts/repo.py status` on the updated `main` must report `product-init` as `stage=closed freshness=frozen closure=frozen`, with the squash commit (the first first-parent commit on `main` containing `closure.json`) as the closure anchor.
    - Deleting the remote `change/product-init` branch is left to the owner, or done by the agent only on request.

## Tests and proof

**Isolation helper (`tests/support.py`).** Every test case goes through a base class or context manager that:

- creates a `tempfile.TemporaryDirectory`;
- sets `HOME` to a directory inside it for every case;
- sets `TODO_CLI_FILE` to a file inside it by default, or removes `TODO_CLI_FILE` for default-location tests;
- applies these via `unittest.mock.patch.dict(os.environ, ...)` for in-process calls, and passes the same environment dict explicitly to every `subprocess.run`;
- before each test body, asserts that the resolved data path lies inside the temporary directory, and fails the test otherwise.

With `HOME` always temporary, the real `~/.todo-cli-test/todos.json` cannot be resolved by any test.

**Coverage map** (spec acceptance criteria → tests):

| AC | Proof |
|---|---|
| 1, 2 | `add` then `list`, both in-process and as separate subprocess invocations |
| 3 | `complete` output and marker; repeat `complete` is exit 0 with the "already complete" message |
| 4 | add 1–3, delete 3, add gets 4; delete 2 leaves 1 and 4 unchanged |
| 5 | mixed complete and incomplete listing in ascending order; empty store prints `No todos.` |
| 6 | empty and whitespace-only text, and text containing each of `\n`, `\r`, `\t`, `\v`, `\f`, `\x1c`, U+0085, U+2028 and U+2029: exit 1, stderr message, data file bytes unchanged. Accepted text is checked to satisfy `text.splitlines() == [text]` |
| 7 | unknown ID for `complete` and `delete`: exit 1, message, file unchanged |
| 8 | `0`, `-1`, `abc`, `1.5`: exit 2 (subprocess) |
| 9 | invalid JSON and each schema violation: every command exits 1 with a read error, and the file is unchanged |
| 10 | `TODO_CLI_FILE` routes reads and writes to its path; with it unset and a temporary `HOME`, data lands at `$HOME/.todo-cli-test/todos.json` |
| 11 | `list` on a missing file creates nothing; `add` creates the file and its parent directories |
| NFR3 | a simulated failure during save (patched `os.replace`) leaves the previous file intact and no temporary file behind |

**Repository verification.**

- `python3 scripts/repo.py verify --change product-init` passes, with evidence under `.evidence/`.
- `verify --full` passes.
- CI `summary` succeeds on the closure-containing final PR head (required for merge, recorded in the PR).

## Risks and mitigations

- **Tests reaching real user data.** The shared helper makes a temporary `HOME` unconditional and asserts the resolved path. A reviewer checks that no test bypasses the helper.
- **Host protection (established).** The `main-protection` ruleset (id 23880463) is active on `main` with no bypass actors. It requires:
  - a pull request with 1 approving review, dismissing stale approvals, with the last push approved by someone other than the pusher;
  - the `summary` check (strict);
  - squash merge only.

  It blocks force pushes and deletion. Owner-confirmed, and verified read-only on 2026-09-23. The agent relies on it as the merge gate and never pushes to `main`. The App has no administration permission and cannot change it.
- **Closure invalidated or evidence stale after late edits.** Any edit to a packet file after step 10 changes `packet_sha256`, and `status` then reports the closure as invalid. Any code fix makes the cited local evidence describe an older tree. Mitigation: finish implementation before the closure. After any later commit, follow step 13, which refreshes the evidence in the same commit, and re-run `status`.
- **Scope creep.** Anything beyond the approved intent and spec, including `pyproject.toml`, a console command, or workflow changes, is out of scope and needs a revised, re-approved plan.
- **Platform differences.** `os.replace` is atomic on the same filesystem on macOS and Linux. The temporary file is created in the target directory to guarantee that.

## Rollback or recovery

- **Before merge:** close the PR, or reset the local branch. Nothing reaches `main`.
- **After merge:** revert the squash commit in a new change (a new packet). A frozen packet is never edited, and follow-up work is recorded as a new change.
- **User data:** the tool never deletes the data file. A corrupt file is reported, not overwritten.

## Open questions

None.
