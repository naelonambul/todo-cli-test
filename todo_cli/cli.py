"""Command-line interface for todo_cli."""

from __future__ import annotations

import argparse
import sys
import unicodedata
from collections.abc import Sequence

from todo_cli import store


def positive_id(value: str) -> int:
    """Parse a positive decimal integer for argparse."""
    if not value or not value.isascii() or not value.isdecimal():
        raise argparse.ArgumentTypeError("ID must be a positive decimal integer")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("ID must be a positive decimal integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("ID must be a positive decimal integer")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo_cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("text", nargs="+")
    subparsers.add_parser("list")
    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("id", type=positive_id)
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", type=positive_id)
    return parser


def _validate_text(words: Sequence[str]) -> str:
    text = " ".join(words).strip()
    if not text:
        raise ValueError("todo text must not be empty")
    if any(unicodedata.category(character) in {"Cc", "Zl", "Zp"} for character in text):
        raise ValueError("todo text must be a single line without control characters")
    if text.splitlines() != [text]:
        raise ValueError("todo text must be a single line without control characters")
    return text


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the process exit status."""
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "add":
            text = _validate_text(args.text)
            data = store.load()
            updated = store.add(data, text)
            new_todo = updated["todos"][-1]
            store.save(updated)
            print(f"Added {new_todo['id']}: {new_todo['text']}")
        elif args.command == "list":
            data = store.load()
            todos = sorted(data["todos"], key=lambda todo: todo["id"])
            if not todos:
                print("No todos.")
            else:
                for todo in todos:
                    marker = "x" if todo["done"] else " "
                    print(f"[{marker}] {todo['id']} {todo['text']}")
        elif args.command == "complete":
            data = store.load()
            original = next((item for item in data["todos"] if item["id"] == args.id), None)
            if original is None:
                raise ValueError(f"no todo with id {args.id}")
            if original["done"]:
                print(f"Todo {args.id} is already complete.")
                return 0
            updated, todo = store.complete(data, args.id)
            store.save(updated)
            print(f"Completed {todo['id']}: {todo['text']}")
        elif args.command == "delete":
            data = store.load()
            try:
                updated, todo = store.delete(data, args.id)
            except KeyError as exc:
                raise ValueError(f"no todo with id {args.id}") from exc
            store.save(updated)
            print(f"Deleted {todo['id']}: {todo['text']}")
    except ValueError as exc:
        print(f"todo_cli: error: {exc}", file=sys.stderr)
        return 1
    except store.StoreReadError as exc:
        print(f"todo_cli: error: {exc}", file=sys.stderr)
        return 1
    except store.StoreWriteError as exc:
        print(f"todo_cli: error: {exc}", file=sys.stderr)
        return 1
    return 0
