# Delete

Removes a todo. Its id is never assigned again.

## Sub-features

- delete-one: the todo is removed, and the other todos keep their ids.
- delete-highest-not-reused: after the highest id is deleted, the next `add` still gets `next_id`.
- delete-unknown: an unknown id is an error.
- delete-malformed: a malformed id is a usage error.

## How to get to it (user POV)

`python3 -m todo_cli delete ID`

## Driving it

Setup: `add a`, `add b`, `add c`, which give ids 1–3 and `next_id` 4.

| Step | Command after `--` | Expected |
|---|---|---|
| delete-highest | `python3 -m todo_cli delete 3` | exit 0; stdout `Deleted 3: c\n`; `next_id` still 4 |
| add-after-delete | `python3 -m todo_cli add d` | exit 0; stdout `Added 4: d\n` |
| delete-middle | `python3 -m todo_cli delete 2` | exit 0; stdout `Deleted 2: b\n`; the remaining ids are 1 and 4, in that order |
| delete-unknown | `python3 -m todo_cli delete 2` | exit 1; stderr `todo_cli: error: no todo with id 2\n`; data unchanged |
| delete-malformed | `python3 -m todo_cli delete abc` | exit 2; stderr starts `usage: todo_cli delete`; data unchanged |

## Gotchas

- Check `next_id` in `data_after.text`. The printed output alone does not prove an id is not reused.
