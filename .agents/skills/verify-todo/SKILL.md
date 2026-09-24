---
name: verify-todo
description: Drive the real todo_cli command line the way a user does, in an isolated run directory, and capture evidence of each command's output, exit status and data-file effect. Use when proving user-visible todo_cli behaviour (add, list, complete, edit, delete), after changing todo_cli, or when asked to verify a feature end to end.
---

# Verify todo_cli

Drive `python3 -m todo_cli` from the repository root, as a user does. Every run uses its own run directory under `.evidence/verify-todo/`, which is gitignored. It never touches the user's real `~/.todo-cli-test/todos.json`.

This produces local evidence only. The registered checks in `checks.json` (`python3 scripts/repo.py verify`) remain the only automatic gate.

`drive.py` (in this directory, executable) runs each command with the run's isolated environment and records what happened. It asserts nothing. The expected results are in `features/`. Read `features/README.md`, then only the feature files you need.

Run every command below from the repository root.

**Every verification drives the product itself, in a new run that you launch.** Earlier runs under `.evidence/verify-todo/` belong to someone else, and may come from a different build. Never report them as your result, and never copy steps from them. Your result is only the run you launched, with its Doctor, steps, summary and cleanup.

## Launch

No build or install step: the package runs from the checkout.

```bash
RUN=$(python3 .agents/skills/verify-todo/drive.py launch)
```

This creates `$RUN/home/` (used as `HOME`), `$RUN/data/` and `$RUN/steps/`. `TODO_CLI_FILE` is `$RUN/data/store/todos.json`. Its directory `store/` is deliberately not created, so the product's own directory creation can be observed. The run starts with no data file, which counts as an empty store. The command is short-lived, so there is nothing to start or wait for.

## Doctor

```bash
python3 .agents/skills/verify-todo/drive.py doctor "$RUN"
```

This is read-only. It writes `$RUN/doctor.json` and prints `doctor: ok` only when all of these hold:

- `python3` is Python 3;
- `python3 -m todo_cli --help` lists exactly `add`, `list`, `complete`, `edit` and `delete`;
- the data path the product resolves is `$RUN/data/store/todos.json`;
- the directory is a git checkout. It records `HEAD` and `git status --porcelain`, so you know which build you drove.

Doctor uses the same `python3` on `PATH` that the steps use. If Doctor fails, stop and report its problems. `step` refuses to run until Doctor passes, and refuses again if `HEAD` has changed since Doctor ran. Run Doctor again after any drive that failed or surprised you.

## Drive

Each drive is one real command:

```bash
python3 .agents/skills/verify-todo/drive.py step "$RUN" <step-name> -- python3 -m todo_cli <command> [arguments]
```

Examples:

```bash
python3 .agents/skills/verify-todo/drive.py step "$RUN" add-milk -- python3 -m todo_cli add buy milk
python3 .agents/skills/verify-todo/drive.py step "$RUN" edit-1 -- python3 -m todo_cli edit 1 buy oat milk
python3 .agents/skills/verify-todo/drive.py step "$RUN" list -- python3 -m todo_cli list
```

- Step names are lowercase letters, digits and hyphens.
- To pass a control character, use bash ANSI-C quoting, for example `$'bad\ttext'` for a tab.
- Set up state only through the product's own commands (`add`, `complete`, `delete`), never by writing `todos.json` by hand. The one exception is a feature file that says a corrupt file is its precondition.
- For each step, `drive.py` prints the exit status, whether the data file changed, stdout and stderr. Compare them with the feature file right away.

## Evidence

`drive.py` writes `$RUN/steps/NN-<step-name>.json` for each step. Each record holds:

- `argv`, `exit`, `stdout` and `stderr`;
- `data_before` and `data_after`, each with `dir_exists` (whether `data/store/` exists), `exists`, `sha256`, the exact bytes (`bytes_b64`) and `text`;
- `data_changed`.

Judge side effects from `data_before` and `data_after`, not only from the printed output. "Data file unchanged" means `data_changed` is `false`, with equal `sha256`. That shows the bytes are identical. It cannot show whether the product rewrote identical bytes.

When you finish driving, write `$RUN/summary.md` with:

- the Doctor result, and the `HEAD` you drove;
- one line per step: `PASS` or `FAIL`, the step file, and for a failure, the expected result against the actual one;
- every path the feature file lists that you did not drive, and why.

## Cleanup

```bash
python3 .agents/skills/verify-todo/drive.py cleanup "$RUN"
```

This removes only `$RUN/home/` and `$RUN/data/`. It keeps `doctor.json`, `steps/` and `summary.md`. Nothing is left running, because every command has already exited. Never delete `$RUN` itself or any other run. Report the path of `$RUN` so others can inspect the evidence.
