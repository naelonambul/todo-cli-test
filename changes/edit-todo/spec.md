# Specification

## Summary

`todo_cli` is a local, single-user command-line todo manager, run as `python3 -m todo_cli`. It provides five commands: `add`, `list`, `complete`, `delete` and `edit`. Todos are stored in a JSON file, by default `~/.todo-cli-test/todos.json`. The environment variable `TODO_CLI_FILE` overrides that location. Identifiers are stable positive integers that are never reused. The tool uses only the Python standard library.

## Requirements

### Functional

- **FR1 Add.** `add TEXT...` creates an incomplete todo with the given text and the next unused identifier, saves it, and reports the new identifier.
- **FR2 List.** `list` prints every todo, incomplete and completed, in ascending identifier order. Each line shows the completion marker, the identifier and the text. A final summary line gives the total number of todos and how many are complete. With no todos, it prints a message saying so.
- **FR3 Complete.** `complete ID` marks the todo with that identifier complete and saves it. Completing an already-complete todo succeeds and changes nothing.
- **FR4 Delete.** `delete ID` removes the todo with that identifier and saves the result. The identifier is never assigned again.
- **FR5 Persistence.** Todos persist between invocations in the data file (see "Interfaces, data, and dependencies").
- **FR6 Stable identifiers.** Identifiers are positive integers assigned in increasing order starting at 1. Deleting a todo never changes another todo's identifier. A deleted identifier is never reused, including the highest one.
- **FR7 Data-location override.** If the environment variable `TODO_CLI_FILE` is set to a non-empty value, that path is used as the data file instead of the default. `~` is expanded, and a relative path is resolved against the current working directory.
- **FR8 Errors.** Invalid input and unusable data produce a clear message on standard error and a non-zero exit status, and leave the data file unchanged (see "User experience and behavior").
- **FR9 Edit.** `edit ID TEXT...` replaces the text of the todo with that identifier and saves it. Only the text changes: the todo keeps its identifier, its completion state and its position in the data file, and `next_id` is unchanged.

### Non-functional

- **NFR1 Dependencies.** Runtime and tests use the Python standard library only. The target is Python 3.13, the version CI uses.
- **NFR2 Platforms.** macOS and Linux. No network access.
- **NFR3 Data safety.** A failed or interrupted write never leaves a partially written data file. Writes go to a temporary file in the same directory, followed by an atomic `os.replace`.
- **NFR4 Simplicity.** A small package with no configuration file, plugin system, or state beyond the data file.
- **NFR5 Testability.** Every behaviour in this spec can be tested without touching the user's real data. Most behaviour is tested with `TODO_CLI_FILE` pointing into a temporary directory. The default data location is tested with `TODO_CLI_FILE` unset and `HOME` set to a temporary directory.

## User experience and behavior

Invocation: `python3 -m todo_cli <command> [arguments]`, run from the repository root or with the package on `PYTHONPATH`. Command-line parsing uses `argparse`, and `-h`/`--help` is available for the program and for each command.

| Command | Arguments | Standard output on success | Exit |
|---|---|---|---|
| `add` | one or more words of text | `Added 3: buy milk` | 0 |
| `list` | none | one line per todo followed by a summary line, or `No todos.` | 0 |
| `complete` | `ID` | `Completed 3: buy milk`, or `Todo 3 is already complete.` | 0 |
| `delete` | `ID` | `Deleted 3: buy milk` | 0 |
| `edit` | `ID`, then one or more words of text | `Edited 3: buy oat milk` | 0 |

**Text.** The words given to `add` or `edit` are joined with single spaces, then leading and trailing whitespace is removed. The result must not be empty. It must not contain line breaks or other control characters, so each todo stays on one output line.

**List format.** One line per todo: `[ ] 1 buy milk` for an incomplete todo, `[x] 2 call the bank` for a completed one. The marker, identifier and text are separated by single spaces, and identifiers are not padded.

**List summary.** When at least one todo exists, `list` ends with one summary line after the todo lines: `<N> todos, <M> complete`, where `<N>` is the number of todos and `<M>` the number of completed todos. It uses `todo` instead of `todos` when `<N>` is 1. Examples: `1 todo, 0 complete`, `2 todos, 1 complete`, `3 todos, 3 complete`. There is no blank line before it. An empty store prints only `No todos.`, with no summary line.

**Identifiers on the command line.** `ID` must be a positive decimal integer. Anything else, such as `0`, `-1`, `abc` or `1.5`, is a usage error.

**Edit.** `edit` validates its text by the same rules as `add`, before it reads the data file, so invalid text is reported even when the identifier is unknown or the data file is unreadable. It then replaces the target todo's text with the validated text and prints `Edited <id>: <text>`. Editing a completed todo keeps it completed. Giving a todo the text it already has still succeeds and prints the same message.

**Errors.** Every error message goes to standard error, prefixed `todo_cli: error: `. On error, nothing is written to standard output and the data file is not modified.

| Condition | Exit | Example message |
|---|---|---|
| Unknown command, missing or extra argument, or malformed `ID` | 2 | argparse usage message |
| Empty text, or text with control characters | 1 | `todo_cli: error: todo text must not be empty` |
| No todo with the given `ID` | 1 | `todo_cli: error: no todo with id 7` |
| Data file unreadable, not valid JSON, or not matching the schema | 1 | `todo_cli: error: cannot read data file <path>: <reason>` |
| Data file or its directory cannot be written | 1 | `todo_cli: error: cannot write data file <path>: <reason>` |

**Missing data file.** A missing file counts as an empty store: `list` prints `No todos.` and creates nothing. The first command that changes data creates the file and any missing parent directories.

## Architecture and design

A Python package `todo_cli/` at the repository root, so `python3 -m todo_cli` runs from a checkout with no install step:

- `todo_cli/__main__.py`: entry point. Calls the CLI and exits with its status.
- `todo_cli/cli.py`: `argparse` definitions, command dispatch, output formatting, and mapping errors to exit statuses. It exposes `main(argv=None) -> int` so tests can call it in-process.
- `todo_cli/store.py`: works out the data-file path (default or `TODO_CLI_FILE`), loads and validates the JSON, assigns identifiers, and saves atomically. It does no terminal input or output.

Each command is one load, change and save cycle. The next identifier to assign is stored in the file, so it survives the deletion of the highest-numbered todo.

Tests live in `tests/` as standard-library `unittest` modules. Every case runs in an isolated filesystem and environment built from a temporary directory: `HOME` always points into it, and `TODO_CLI_FILE` normally points to a data file inside it. Default-location tests unset `TODO_CLI_FILE` instead, so the default path resolves inside the temporary `HOME`. In-process and subprocess invocations both receive this isolated environment. At least one test runs `python3 -m todo_cli` as a subprocess to cover the real entry point and exit statuses.

## Interfaces, data, and dependencies

**Data file.** UTF-8 JSON:

```json
{
  "version": 1,
  "next_id": 4,
  "todos": [
    {"id": 1, "text": "buy milk", "done": false},
    {"id": 3, "text": "call the bank", "done": true}
  ]
}
```

- `version` must be `1`. Any other value is a read error.
- `next_id` is an integer greater than every `id` present, and at least 1.
- `todos` is a list of objects with a unique positive integer `id`, a non-empty string `text` and a boolean `done`.
- The file is rewritten in full on every change, with 2-space indentation and a trailing newline.
- A file that violates any of these rules is reported as a read error and never overwritten.

**Environment.** `TODO_CLI_FILE` sets the data-file path (FR7). If it is unset or empty, the default `~/.todo-cli-test/todos.json` is used. `HOME` is used for `~` expansion as usual.

**Dependencies.** Python 3.13 standard library only (`argparse`, `json`, `os`, `pathlib`, `sys`, `tempfile`, `unittest`, `subprocess`).

## Security, privacy, and policy constraints

- All data stays on the local machine. The tool makes no network calls and collects no telemetry.
- The data file is plain text. It is not encrypted, and its permissions come from the user's umask. Users should not store secrets in todos.
- Todo text is data only: it is never executed or interpreted as a format string or shell command.

## Risks and concerns

- **Concurrent invocations.** Two commands run at the same moment could both read the file and lose one update (last write wins). This is accepted for a single-user tool. The atomic write still prevents a corrupted file.
- **Tests touching real data.** A test that runs with the real environment could modify the user's real `~/.todo-cli-test/todos.json`. Mitigation: every test goes through a shared helper that always provides an isolated temporary environment. It sets `HOME` to a temporary directory for every case, whether or not `TODO_CLI_FILE` is set, and passes that environment to subprocesses. This means even the default path resolves inside the temporary directory, so the user's real default path cannot be reached.
- **Hand-edited files.** A user who edits the JSON by hand may make it invalid. The tool reports the error and does not overwrite the file.

## Acceptance criteria

1. `add` with text in a fresh store prints `Added 1: <text>` and exits 0. A following `list` shows `[ ] 1 <text>`.
2. Todos added in one invocation are listed by a later, separate invocation.
3. `complete 1` prints `Completed 1: <text>`, and `list` then shows `[x] 1 <text>`. Running `complete 1` again prints `Todo 1 is already complete.` and exits 0.
4. After adding todos 1–3 and deleting 3, the next `add` receives identifier 4. Deleting 2 leaves 1 and 4 unchanged.
5. `list` shows incomplete and completed todos together, in ascending identifier order, followed by the summary line. For example, one incomplete and one completed todo end with `2 todos, 1 complete`, and a single todo ends with `1 todo, 0 complete`. An empty store prints only `No todos.`
6. `add` or `edit` with empty or whitespace-only text, or text containing a control character, exits 1 with an error on standard error and leaves the data file byte-for-byte unchanged.
7. `complete`, `delete` or `edit` with an unknown identifier exits 1 with `no todo with id <n>` and leaves the data file unchanged.
8. A malformed `ID` (`0`, `-1`, `abc`) exits 2.
9. A data file that is not valid JSON or does not match the schema makes every command exit 1 with a read error, and the file is left unchanged.
10. With `TODO_CLI_FILE` set, all reads and writes go to that path. With it unset, the default `~/.todo-cli-test/todos.json` is used (tested with `HOME` pointing at a temporary directory).
11. `list` on a missing data file prints `No todos.` and does not create the file. `add` creates the file and its parent directories.
12. `edit 1 new text` prints `Edited 1: new text` and exits 0. A following, separate `list` shows the new text for identifier 1, the other todos unchanged, and the same summary line. The todo's identifier, completion state and position in the data file, and the file's `next_id`, are unchanged. Editing a completed todo keeps `[x]`.
13. The automated `unittest` suite covers criteria 1–12 using only the standard library.

## Open questions

None. The data-location override is resolved as `TODO_CLI_FILE` (FR7).
