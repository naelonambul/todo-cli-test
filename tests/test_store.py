"""Unit tests for persistent storage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

from tests.support import IsolatedTestCase
from todo_cli import store


class StoreTests(IsolatedTestCase):
    def test_resolves_override_expanding_home_and_relative_paths(self) -> None:
        os.environ["TODO_CLI_FILE"] = "~/custom/todos.json"
        self.assertEqual(store.data_path(), Path(os.environ["HOME"]) / "custom/todos.json")
        os.environ["TODO_CLI_FILE"] = "relative/todos.json"
        self.assertEqual(store.data_path(), Path.cwd() / "relative/todos.json")

    def test_missing_file_is_empty_without_creating_it(self) -> None:
        self.assertEqual(store.load(), {"version": 1, "next_id": 1, "todos": []})
        self.assertFalse(self.data_file.exists())

    def test_empty_override_falls_back_to_default(self) -> None:
        with patch.dict(os.environ, {"TODO_CLI_FILE": ""}):
            expected = Path(os.environ["HOME"]) / ".todo-cli-test" / "todos.json"
            self.assertEqual(store.data_path(), expected)
            self.assertEqual(store.load()["todos"], [])
            self.assertFalse(expected.exists())

    def test_load_validates_schema(self) -> None:
        invalid_documents = [
            ("[]", "top-level"),
            ('{"version": 2, "next_id": 1, "todos": []}', "version"),
            ('{"version": 1, "next_id": true, "todos": []}', "next_id"),
            ('{"version": 1, "next_id": 1, "todos": {}}', "todos"),
            ('{"version": 1, "next_id": 2, "todos": [{"id": 1, "text": "x", "done": 0}]}', "done"),
            ('{"version": 1, "next_id": 1, "todos": [{"id": 1, "text": "x", "done": false}]}', "next_id"),
            ('{"version": 1, "next_id": 3, "todos": [{"id": 1, "text": "", "done": false}]}', "text"),
            ('{"version": 1, "next_id": 3, "todos": [{"id": 1, "text": "x", "done": false}, {"id": 1, "text": "y", "done": true}]}', "duplicate"),
        ]
        for document, expected_reason in invalid_documents:
            with self.subTest(document=document):
                self.data_file.parent.mkdir(parents=True, exist_ok=True)
                self.data_file.write_text(document, encoding="utf-8")
                with self.assertRaisesRegex(store.StoreReadError, expected_reason):
                    store.load()

    def test_invalid_json_is_read_error(self) -> None:
        self.data_file.parent.mkdir(parents=True)
        self.data_file.write_text("{", encoding="utf-8")
        with self.assertRaises(store.StoreReadError):
            store.load()

    def test_add_does_not_reuse_deleted_highest_id(self) -> None:
        data = {"version": 1, "next_id": 4, "todos": [{"id": 1, "text": "one", "done": False}, {"id": 3, "text": "three", "done": False}]}
        updated = store.add(data, "four")
        self.assertEqual(updated["todos"][-1]["id"], 4)
        self.assertEqual(updated["next_id"], 5)

    def test_save_writes_indented_json_and_trailing_newline(self) -> None:
        store.save({"version": 1, "next_id": 2, "todos": [{"id": 1, "text": "one", "done": False}]})
        content = self.data_file.read_text(encoding="utf-8")
        self.assertTrue(content.endswith("\n"))
        self.assertIn("\n  \"version\": 1,", content)
        self.assertEqual(json.loads(content)["next_id"], 2)

    def test_replace_failure_keeps_previous_data_and_cleans_temporary_file(self) -> None:
        original = {"version": 1, "next_id": 2, "todos": [{"id": 1, "text": "old", "done": False}]}
        store.save(original)
        previous_bytes = self.data_file.read_bytes()
        with patch("todo_cli.store.os.replace", side_effect=OSError("simulated failure")):
            with self.assertRaisesRegex(store.StoreWriteError, "cannot write data file"):
                store.save({"version": 1, "next_id": 3, "todos": []})
        self.assertEqual(self.data_file.read_bytes(), previous_bytes)
        self.assertEqual(list(self.data_file.parent.iterdir()), [self.data_file])


class DefaultLocationStoreTests(IsolatedTestCase):
    use_default_location = True

    def test_default_path_with_override_unset(self) -> None:
        self.assertNotIn("TODO_CLI_FILE", os.environ)
        expected = Path(os.environ["HOME"]) / ".todo-cli-test" / "todos.json"
        self.assertEqual(store.data_path(), expected)
        self.assertEqual(store.load()["todos"], [])
        self.assertFalse(expected.exists())
