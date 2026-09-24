# List

Prints every todo in ascending id order, followed by a summary line.

## Sub-features

- list-empty: an empty or missing store prints `No todos.` and creates nothing.
- list-mixed: `[ ]` marks incomplete todos and `[x]` complete ones, followed by `<N> todos, <M> complete`.
- list-singular: a single todo gives `1 todo, 0 complete`.

## How to get to it (user POV)

`python3 -m todo_cli list`

## Driving it

| Step | Command after `--` | Expected |
|---|---|---|
| list-empty (fresh run) | `python3 -m todo_cli list` | exit 0; stdout `No todos.\n`; `data_after.dir_exists` and `data_after.exists` false (nothing created) |
| setup | `add buy milk`, then `add call the bank`, then `complete 2` | as in add.md and complete.md |
| list-mixed | `python3 -m todo_cli list` | exit 0; stdout `[ ] 1 buy milk\n[x] 2 call the bank\n2 todos, 1 complete\n`; data unchanged |
| setup | `delete 2` | as in delete.md |
| list-singular | `python3 -m todo_cli list` | exit 0; stdout `[ ] 1 buy milk\n1 todo, 0 complete\n` |

## Gotchas

- There is no blank line before the summary, and ids are not padded.
- `list` must leave the data file byte-identical (`data_changed: false`).
