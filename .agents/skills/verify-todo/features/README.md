# todo_cli feature map

Each file covers one command. They share these preconditions and rules.

## Shared preconditions

- A fresh run from the verify skill's Launch, with Doctor passing. A new run has no data file, which counts as an empty store.
- State is built only with the product's own commands. For example, three `add` steps create ids 1, 2 and 3.
- Commands run from the repository root as `python3 -m todo_cli ...`, through `drive.py step`.

## Proof and skip rules

- **Pass.** A path passes only when all three of these match the feature file: exit status, exact stdout and stderr (or the stated pattern for argparse usage errors), and the data-file effect (`data_changed` and the resulting JSON).
- **Errors.** An error path must also show empty stdout and `data_changed: false`.
- **Skips.** A path you cannot drive is named in `summary.md` with its reason. It is never reported as passed.
- **Mismatches.** When the output differs from a feature file, decide which one is wrong by checking the root `spec.md`:
  - the map is wrong: this is doc drift, so fix the map;
  - the product is wrong: this is a product gap, so report it.

## Data file shape

The data file is UTF-8 JSON with 2-space indentation and a trailing newline:

```json
{"version": 1, "next_id": N, "todos": [{"id": 1, "text": "...", "done": false}]}
```

`todos` keeps its order, and `next_id` never goes down.

## Full-sweep order

Use this order for a broad regression run: add, list, complete, edit, delete. Each file builds its own state in a fresh run.

## Index

- [add.md](add.md): create a todo.
- [list.md](list.md): show all todos and the summary line.
- [complete.md](complete.md): mark a todo complete.
- [edit.md](edit.md): replace a todo's text.
- [delete.md](delete.md): remove a todo; its id is never reused.
