# Complete

Marks a todo complete. Completing it again succeeds and changes nothing.

## Sub-features

- complete-open: an incomplete todo becomes `done: true`.
- complete-again: an already complete todo reports so, and the file is unchanged.
- complete-unknown: an unknown id is an error.
- complete-malformed: a malformed id is a usage error.

## How to get to it (user POV)

`python3 -m todo_cli complete ID`

## Driving it

Setup: `add buy milk`.

| Step | Command after `--` | Expected |
|---|---|---|
| complete-open | `python3 -m todo_cli complete 1` | exit 0; stdout `Completed 1: buy milk\n`; todo 1 has `"done": true` |
| complete-again | `python3 -m todo_cli complete 1` | exit 0; stdout `Todo 1 is already complete.\n`; data unchanged |
| complete-unknown | `python3 -m todo_cli complete 7` | exit 1; stderr `todo_cli: error: no todo with id 7\n`; data unchanged |
| complete-malformed | `python3 -m todo_cli complete 0` | exit 2; stderr starts `usage: todo_cli complete` and contains `ID must be a positive decimal integer`; data unchanged |

## Gotchas

- `complete-again` must leave the file byte-identical (`data_changed: false`). Check the recorded state, not only the message.
