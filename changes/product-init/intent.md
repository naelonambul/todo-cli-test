# Intent

## Problem

Keeping track of small personal tasks from the terminal usually means either a scratch text file with no structure, or a full-featured task manager that brings accounts, sync, network services and more concepts than the job needs. A single user working locally needs something in between: a tiny command-line tool that records short todos, shows them, marks them done and removes them, keeping the data in a plain local file that stays with the user.

## Proposed outcome

A local, single-user command-line todo manager written in Python, run as `python3 -m todo_cli`. A user can:

- add a todo with a short text description;
- list todos, seeing each one's identifier, text and a visible completion marker;
- mark a todo complete by its identifier;
- delete a todo by its identifier.

Todos persist between runs in a local JSON file.

Product decisions for the initial version:

- **Invocation:** `python3 -m todo_cli`. No installed `todo` command yet.
- **Default data location:** `~/.todo-cli-test/todos.json`.
- **Storage format:** JSON.
- **Identifiers:** stable positive integers. An identifier is never reused, even after its todo is deleted.
- **Listing:** `list` shows both incomplete and completed todos, each with a visible completion marker. There are no filtering options.

## Affected users and systems

- **The user**: a single person running the CLI on their own machine.
- **The local filesystem**, where the todo data file lives.

## Constraints

- Python 3, standard library only at runtime. No third-party runtime dependencies.
- Tests use the Python standard-library `unittest`.
- Runs locally on macOS and Linux. No network access, server, database service, or account.
- Keep the application deliberately small. Choose the simplest design that fits.

## Out of scope

- Multiple users, sync, sharing, or any network or cloud storage.
- Due dates, priorities, tags, projects, search, filtering, sorting options, or editing a todo's text.
- An installed console command, packaging for distribution (PyPI, Homebrew), or installers.
- A GUI, TUI or web interface.
- Encryption or access control for the data file.

## Success criteria

- A user can add, list, complete and delete todos with `python3 -m todo_cli`, and todos survive between invocations.
- `list` shows every todo, incomplete and completed, with its identifier, text and completion marker.
- Identifiers stay stable: deleting a todo never changes another todo's identifier, and a deleted identifier is never assigned again.
- Invalid input, such as an unknown identifier or empty todo text, produces a clear error message and a non-zero exit status, and leaves the stored data unchanged.
- Automated `unittest` tests cover each of the four operations and the main error paths.

## Open questions

1. How a user or a test points the CLI at a data file other than the default (for example an environment variable or a flag), so tests never touch the real `~/.todo-cli-test/todos.json`. Left to the spec.
