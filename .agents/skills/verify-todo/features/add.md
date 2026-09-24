# Add

Creates an incomplete todo with the next unused id, and saves it.

## Sub-features

- add-first: the first todo in an empty store gets id 1, and the data file and its missing directory are created.
- add-next: later todos get `next_id`.
- add-normalise: the words are joined with single spaces and trimmed.
- add-invalid-text: empty or whitespace-only text, or text with a control character, is refused.

## How to get to it (user POV)

`python3 -m todo_cli add TEXT...`

## Driving it

| Step | Command after `--` | Expected |
|---|---|---|
| add-first | `python3 -m todo_cli add buy milk` | exit 0; stdout `Added 1: buy milk\n`; `data_before.dir_exists` and `data_before.exists` are false, `data_after.exists` is true, with `next_id` 2 and `{"id": 1, "text": "buy milk", "done": false}` |
| add-next | `python3 -m todo_cli add call the bank` | exit 0; stdout `Added 2: call the bank\n`; `next_id` 3 |
| add-normalise | `python3 -m todo_cli add "  spaced   " out` | exit 0; stdout `Added 3: spaced    out\n` (the words are joined with one space, then the ends are trimmed; spaces inside a word are kept) |
| add-empty | `python3 -m todo_cli add "   "` | exit 1; stderr `todo_cli: error: todo text must not be empty\n`; data unchanged |
| add-control | `python3 -m todo_cli add $'bad\ttext'` | exit 1; stderr `todo_cli: error: todo text must be a single line without control characters\n`; data unchanged |

## Gotchas

- Joining happens before trimming, so spaces inside one quoted argument are kept.
- A deleted id is never reused, even the highest one (see delete.md).
