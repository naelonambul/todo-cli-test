# Edit

Replaces one todo's text. Its id, completion state, position in the file, and the store's `next_id` are all unchanged.

## Sub-features

- edit-open: edit an incomplete todo.
- edit-done: edit a completed todo; it stays `[x]`.
- edit-same-text: giving a todo its current text succeeds with the same message.
- edit-list: a later `list` shows the new text and the unchanged summary line.
- edit-unknown: an unknown id is an error; the data is unchanged.
- edit-malformed: a malformed id, or missing text, is a usage error.
- edit-invalid-text: empty or control-character text is refused, and is checked before the id or the data file.
- edit-persist: separate invocations see the edited text.

## How to get to it (user POV)

`python3 -m todo_cli edit ID TEXT...`

## Driving it

Setup, in a fresh run: `add buy milk`, `add call the bank`, `add walk dog`, then `complete 2`. That gives `next_id` 4, with todo 2 done.

| Step | Command after `--` | Expected |
|---|---|---|
| edit-open | `python3 -m todo_cli edit 1 buy oat milk` | exit 0; stdout `Edited 1: buy oat milk\n`; stderr empty; in `data_after`, todo 1's text is `buy oat milk`, `done` is false, it is still first in `todos`, the other todos are unchanged, and `next_id` is 4 |
| edit-done | `python3 -m todo_cli edit 2 call the bank today` | exit 0; stdout `Edited 2: call the bank today\n`; todo 2 has `"done": true` and is still second |
| edit-same-text | `python3 -m todo_cli edit 3 walk dog` | exit 0; stdout `Edited 3: walk dog\n` |
| edit-list | `python3 -m todo_cli list` | exit 0; stdout `[ ] 1 buy oat milk\n[x] 2 call the bank today\n[ ] 3 walk dog\n3 todos, 1 complete\n`; data unchanged |
| edit-unknown | `python3 -m todo_cli edit 7 new text` | exit 1; stdout empty; stderr `todo_cli: error: no todo with id 7\n`; data unchanged |
| edit-malformed-zero | `python3 -m todo_cli edit 0 new text` | exit 2; stdout empty; stderr starts `usage: todo_cli edit` and contains `ID must be a positive decimal integer`; data unchanged |
| edit-malformed-word | `python3 -m todo_cli edit abc new text` | exit 2; same as above |
| edit-missing-text | `python3 -m todo_cli edit 1` | exit 2; stderr starts `usage: todo_cli edit` and contains `the following arguments are required: text`; data unchanged |
| edit-empty | `python3 -m todo_cli edit 1 "   "` | exit 1; stderr `todo_cli: error: todo text must not be empty\n`; data unchanged |
| edit-control | `python3 -m todo_cli edit 1 $'bad\ttext'` | exit 1; stderr `todo_cli: error: todo text must be a single line without control characters\n`; data unchanged |
| edit-invalid-before-id | `python3 -m todo_cli edit 7 "   "` | exit 1; stderr `todo_cli: error: todo text must not be empty\n` (text is checked before the id); data unchanged |
| edit-persist | `python3 -m todo_cli list` | exit 0; the same stdout as edit-list |

## Gotchas

- Text is validated before the data file is read. Invalid text with an unknown id reports the text error, not `no todo with id`.
- `edit-same-text` rewrites the file with identical bytes, so its `data_changed` is `false`. That is expected.
- Byte-identical data on error means `data_changed: false`. Check the recorded state, not only the message.
- "Position" means the todo's index in the `todos` array of `data_after.text`, not the `list` order. `list` always sorts by id.
