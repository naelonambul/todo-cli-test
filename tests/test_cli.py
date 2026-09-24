"""CLI behavior and acceptance tests."""

from __future__ import annotations

import json
import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from tests.support import IsolatedTestCase
from todo_cli import store
from todo_cli.cli import main


class CliTests(IsolatedTestCase):
    def run_main(self, *arguments: str) -> tuple[int, str, str]:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(list(arguments))
        return status, stdout.getvalue(), stderr.getvalue()

    def test_add_list_and_subprocess_persistence(self) -> None:
        status, output, error = self.run_main("add", "buy", "milk")
        self.assertEqual((status, output, error), (0, "Added 1: buy milk\n", ""))
        result = self.subprocess("list")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "[ ] 1 buy milk\n1 todo, 0 complete\n", ""))

    def test_complete_is_idempotent_and_list_shows_mixed_items_sorted(self) -> None:
        self.subprocess("add", "second")
        self.subprocess("add", "first")
        completed = self.subprocess("complete", "1")
        self.assertEqual(completed.stdout, "Completed 1: second\n")
        repeated = self.subprocess("complete", "1")
        self.assertEqual((repeated.returncode, repeated.stdout), (0, "Todo 1 is already complete.\n"))
        listing = self.subprocess("list")
        self.assertEqual(listing.stdout, "[x] 1 second\n[ ] 2 first\n2 todos, 1 complete\n")

    def test_delete_keeps_ids_and_next_id_advances(self) -> None:
        for name in ("one", "two", "three"):
            self.subprocess("add", name)
        self.assertEqual(self.subprocess("delete", "3").stdout, "Deleted 3: three\n")
        self.assertEqual(self.subprocess("add", "four").stdout, "Added 4: four\n")
        self.subprocess("delete", "2")
        self.assertEqual(self.subprocess("list").stdout, "[ ] 1 one\n[ ] 4 four\n2 todos, 0 complete\n")

    def test_list_summary_line(self) -> None:
        self.subprocess("add", "one")
        self.assertEqual(self.subprocess("list").stdout, "[ ] 1 one\n1 todo, 0 complete\n")
        self.subprocess("add", "two")
        self.subprocess("complete", "2")
        self.assertEqual(self.subprocess("list").stdout, "[ ] 1 one\n[x] 2 two\n2 todos, 1 complete\n")
        self.subprocess("add", "three")
        for todo_id in ("1", "3"):
            self.subprocess("complete", todo_id)
        self.assertEqual(
            self.subprocess("list").stdout,
            "[x] 1 one\n[x] 2 two\n[x] 3 three\n3 todos, 3 complete\n",
        )
        for todo_id in ("1", "2", "3"):
            self.subprocess("delete", todo_id)
        self.assertEqual(self.subprocess("list").stdout, "No todos.\n")

    def test_empty_store_and_missing_file_list(self) -> None:
        result = self.subprocess("list")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "No todos.\n", ""))
        self.assertFalse(self.data_file.exists())

    def test_empty_and_control_text_are_errors_without_file_changes(self) -> None:
        invalid_inputs = [("",), ("   ",), *[(f"before{char}after",) for char in "\n\r\t\v\f\x1c\x1d\x1e\x85\u2028\u2029"]]
        for words in invalid_inputs:
            with self.subTest(words=words):
                original = b'{"sentinel": true}\n'
                self.data_file.parent.mkdir(parents=True, exist_ok=True)
                self.data_file.write_bytes(original)
                status, output, error = self.run_main("add", *words)
                self.assertEqual(status, 1)
                self.assertEqual(output, "")
                message = (
                    "todo_cli: error: todo text must not be empty\n"
                    if not " ".join(words).strip()
                    else "todo_cli: error: todo text must be a single line without control characters\n"
                )
                self.assertEqual(error, message)
                self.assertEqual(self.data_file.read_bytes(), original)

    def test_unknown_ids_leave_data_unchanged(self) -> None:
        self.subprocess("add", "existing")
        original = self.data_file.read_bytes()
        for operation in ("complete", "delete", "edit"):
            arguments = (operation, "7", "new") if operation == "edit" else (operation, "7")
            result = self.subprocess(*arguments)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "todo_cli: error: no todo with id 7\n")
            self.assertEqual(self.data_file.read_bytes(), original)

    def test_malformed_ids_are_usage_errors(self) -> None:
        for operation in ("complete", "delete", "edit"):
            for value in ("0", "-1", "abc", "1.5"):
                with self.subTest(operation=operation, value=value):
                    arguments = (operation, value, "new") if operation == "edit" else (operation, value)
                    result = self.subprocess(*arguments)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("usage:", result.stderr)

    def test_each_command_reports_corrupt_file_without_modifying_it(self) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        invalid_data = [
            "{",
            '{"version":2,"next_id":1,"todos":[]}',
            '{"version":1,"next_id":0,"todos":[]}',
            '{"version":1,"next_id":true,"todos":[]}',
            '{"version":1,"next_id":1,"todos":{}}',
            '{"version":1,"next_id":2,"todos":[{"id":0,"text":"x","done":false}]}',
            '{"version":1,"next_id":2,"todos":[{"id":1,"text":"x","done":0}]}',
            '{"version":1,"next_id":1,"todos":[{"id":1,"text":"x","done":false}]}',
            '{"version":1,"next_id":3,"todos":[{"id":1,"text":"","done":false}]}',
            '{"version":1,"next_id":3,"todos":[{"id":1,"text":"x","done":false},{"id":1,"text":"y","done":true}]}',
        ]
        for bad_data in invalid_data:
            for command in (("list",), ("add", "new"), ("complete", "1"), ("delete", "1"), ("edit", "1", "new")):
                with self.subTest(bad_data=bad_data, command=command):
                    self.data_file.write_text(bad_data, encoding="utf-8")
                    original = self.data_file.read_bytes()
                    result = self.subprocess(*command)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("todo_cli: error: cannot read data file", result.stderr)
                    self.assertEqual(self.data_file.read_bytes(), original)

    def test_override_location(self) -> None:
        self.subprocess("add", "override")
        self.assertTrue(self.data_file.exists())
        self.assertEqual(json.loads(self.data_file.read_text())["todos"][0]["text"], "override")

    def test_add_creates_parent_directories_and_accepts_single_line_text(self) -> None:
        result = self.subprocess("add", "  spaced", "text  ")
        self.assertEqual((result.returncode, result.stdout), (0, "Added 1: spaced text\n"))
        stored = json.loads(self.data_file.read_text(encoding="utf-8"))
        text = stored["todos"][0]["text"]
        self.assertEqual(text.splitlines(), [text])


class DefaultLocationCliTests(IsolatedTestCase):
    use_default_location = True

    def test_default_path_without_override(self) -> None:
        self.assertNotIn("TODO_CLI_FILE", os.environ)
        default_file = Path(os.environ["HOME"]) / ".todo-cli-test" / "todos.json"
        self.assertEqual(store.data_path(), default_file)
        self.assertEqual(store.data_path().resolve(), default_file.resolve())
        self.assertEqual(store.load()["todos"], [])
        self.assertFalse(default_file.exists())

        added = self.subprocess("add", "default", "todo")
        self.assertEqual((added.returncode, added.stdout, added.stderr), (0, "Added 1: default todo\n", ""))
        listed = self.subprocess("list")
        self.assertEqual((listed.returncode, listed.stdout, listed.stderr), (0, "[ ] 1 default todo\n1 todo, 0 complete\n", ""))
        self.assertTrue(default_file.exists())
