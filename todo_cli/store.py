"""Persistent JSON storage for todo items."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class StoreReadError(Exception):
    """The data file cannot be read or does not match the schema."""


class StoreWriteError(Exception):
    """The data file cannot be written safely."""


def data_path() -> Path:
    """Resolve the configured data file path at call time."""
    configured = os.environ.get("TODO_CLI_FILE", "")
    raw_path = configured if configured else "~/.todo-cli-test/todos.json"
    return Path(raw_path).expanduser().absolute()


def _invalid(reason: str) -> StoreReadError:
    return StoreReadError(reason)


def _validate(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise _invalid("top-level value must be an object")
    if type(data.get("version")) is not int or data["version"] != 1:
        raise _invalid("version must be 1")
    next_id = data.get("next_id")
    if type(next_id) is not int or next_id < 1:
        raise _invalid("next_id must be an integer greater than or equal to 1")
    todos = data.get("todos")
    if not isinstance(todos, list):
        raise _invalid("todos must be a list")
    ids: set[int] = set()
    for index, todo in enumerate(todos):
        if not isinstance(todo, dict):
            raise _invalid(f"todos[{index}] must be an object")
        todo_id = todo.get("id")
        if type(todo_id) is not int or todo_id < 1:
            raise _invalid(f"todos[{index}].id must be a positive integer")
        if todo_id in ids:
            raise _invalid(f"duplicate todo id {todo_id}")
        ids.add(todo_id)
        text = todo.get("text")
        if not isinstance(text, str) or not text:
            raise _invalid(f"todos[{index}].text must be a non-empty string")
        if type(todo.get("done")) is not bool:
            raise _invalid(f"todos[{index}].done must be a boolean")
    if ids and next_id <= max(ids):
        raise _invalid("next_id must be greater than every todo id")
    return {"version": 1, "next_id": next_id, "todos": todos}


def load() -> dict[str, Any]:
    """Load the store, treating a missing file as an empty store."""
    path = data_path()
    try:
        with path.open("r", encoding="utf-8") as stream:
            raw = json.load(stream)
        return _validate(raw)
    except FileNotFoundError:
        return {"version": 1, "next_id": 1, "todos": []}
    except (OSError, UnicodeError, json.JSONDecodeError, StoreReadError) as exc:
        raise StoreReadError(f"cannot read data file {path}: {exc}") from exc


def save(data: dict[str, Any]) -> None:
    """Atomically replace the store file with validated JSON."""
    path = data_path()
    temporary_path: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.",
            suffix=".tmp", delete=False,
        ) as stream:
            temporary_path = stream.name
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        raise StoreWriteError(f"cannot write data file {path}: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
            except OSError:
                pass


def add(data: dict[str, Any], text: str) -> dict[str, Any]:
    """Return a changed store containing a new todo."""
    updated = {**data, "todos": list(data["todos"])}
    todo_id = data["next_id"]
    updated["todos"].append({"id": todo_id, "text": text, "done": False})
    updated["next_id"] = todo_id + 1
    return updated


def complete(data: dict[str, Any], todo_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the store with the requested todo completed and the todo itself."""
    updated = {**data, "todos": [dict(todo) for todo in data["todos"]]}
    for todo in updated["todos"]:
        if todo["id"] == todo_id:
            todo["done"] = True
            return updated, todo
    raise KeyError(todo_id)


def delete(data: dict[str, Any], todo_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the store without the requested todo and the removed todo."""
    for todo in data["todos"]:
        if todo["id"] == todo_id:
            updated = {**data, "todos": [item for item in data["todos"] if item["id"] != todo_id]}
            return updated, todo
    raise KeyError(todo_id)
