"""Protected acceptance tests for the edit command (change edit-todo).

These tests are the product oracle for `edit`. They exercise only the real
entry point and the data file, with literal expected values.
"""

from __future__ import annotations

import json

from tests.support import IsolatedTestCase

EMPTY_TEXT = "todo_cli: error: todo text must not be empty\n"
CONTROL_TEXT = "todo_cli: error: todo text must be a single line without control characters\n"


class EditAcceptanceTests(IsolatedTestCase):
    def stored(self) -> dict:
        return json.loads(self.data_file.read_text(encoding="utf-8"))

    def write_raw(self, content: bytes) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_bytes(content)

    def test_edit_incomplete_todo(self) -> None:
        self.subprocess("add", "buy", "milk")
        self.subprocess("add", "call", "the", "bank")
        result = self.subprocess("edit", "1", "buy", "oat", "milk")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "Edited 1: buy oat milk\n", ""))
        self.assertEqual(
            self.stored(),
            {
                "version": 1,
                "next_id": 3,
                "todos": [
                    {"id": 1, "text": "buy oat milk", "done": False},
                    {"id": 2, "text": "call the bank", "done": False},
                ],
            },
        )
        listing = self.subprocess("list")
        self.assertEqual(
            (listing.returncode, listing.stdout, listing.stderr),
            (0, "[ ] 1 buy oat milk\n[ ] 2 call the bank\n2 todos, 0 complete\n", ""),
        )

    def test_edit_normalizes_words_like_add(self) -> None:
        self.subprocess("add", "original")
        result = self.subprocess("edit", "1", "  spaced", "words  ")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "Edited 1: spaced words\n", ""))
        self.assertEqual(self.stored()["todos"], [{"id": 1, "text": "spaced words", "done": False}])

    def test_edit_completed_todo_keeps_it_complete(self) -> None:
        self.subprocess("add", "first")
        self.subprocess("add", "second")
        self.subprocess("complete", "1")
        result = self.subprocess("edit", "1", "renamed")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "Edited 1: renamed\n", ""))
        self.assertEqual(
            self.stored()["todos"],
            [{"id": 1, "text": "renamed", "done": True}, {"id": 2, "text": "second", "done": False}],
        )
        listing = self.subprocess("list")
        self.assertEqual(listing.stdout, "[x] 1 renamed\n[ ] 2 second\n2 todos, 1 complete\n")

    def test_edit_keeps_ids_position_and_next_id(self) -> None:
        self.write_raw(
            b'{"version": 1, "next_id": 5, "todos": ['
            b'{"id": 3, "text": "three", "done": true}, '
            b'{"id": 1, "text": "one", "done": false}]}\n'
        )
        result = self.subprocess("edit", "1", "uno")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "Edited 1: uno\n", ""))
        self.assertEqual(
            self.stored(),
            {
                "version": 1,
                "next_id": 5,
                "todos": [
                    {"id": 3, "text": "three", "done": True},
                    {"id": 1, "text": "uno", "done": False},
                ],
            },
        )
        self.assertEqual(self.subprocess("add", "five").stdout, "Added 5: five\n")
        self.assertEqual(
            self.subprocess("list").stdout,
            "[ ] 1 uno\n[x] 3 three\n[ ] 5 five\n3 todos, 1 complete\n",
        )

    def test_edit_persists_across_invocations(self) -> None:
        self.subprocess("add", "draft")
        self.subprocess("edit", "1", "final")
        self.subprocess("edit", "1", "final", "v2")
        listing = self.subprocess("list")
        self.assertEqual(
            (listing.returncode, listing.stdout, listing.stderr),
            (0, "[ ] 1 final v2\n1 todo, 0 complete\n", ""),
        )

    def test_edit_to_same_text_succeeds(self) -> None:
        self.subprocess("add", "same")
        result = self.subprocess("edit", "1", "same")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "Edited 1: same\n", ""))
        self.assertEqual(self.stored()["todos"], [{"id": 1, "text": "same", "done": False}])

    def test_unknown_id_leaves_data_unchanged(self) -> None:
        self.subprocess("add", "existing")
        original = self.data_file.read_bytes()
        result = self.subprocess("edit", "7", "new", "text")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", "todo_cli: error: no todo with id 7\n"))
        self.assertEqual(self.data_file.read_bytes(), original)

    def test_unknown_id_on_missing_file_creates_nothing(self) -> None:
        result = self.subprocess("edit", "1", "new")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", "todo_cli: error: no todo with id 1\n"))
        self.assertFalse(self.data_file.exists())

    def test_malformed_id_is_usage_error(self) -> None:
        self.subprocess("add", "existing")
        original = self.data_file.read_bytes()
        for value in ("0", "-1", "abc", "1.5"):
            with self.subTest(value=value):
                result = self.subprocess("edit", value, "new")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("usage:", result.stderr)
                self.assertEqual(self.data_file.read_bytes(), original)

    def test_missing_text_is_usage_error(self) -> None:
        self.subprocess("add", "existing")
        original = self.data_file.read_bytes()
        result = self.subprocess("edit", "1")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("usage:", result.stderr)
        self.assertEqual(self.data_file.read_bytes(), original)

    def test_invalid_text_leaves_data_unchanged(self) -> None:
        cases = [
            (("",), EMPTY_TEXT),
            (("   ",), EMPTY_TEXT),
            (("  ", " "), EMPTY_TEXT),
            (("before\nafter",), CONTROL_TEXT),
            (("before\tafter",), CONTROL_TEXT),
            (("before\x1cafter",), CONTROL_TEXT),
            (("before\x85after",), CONTROL_TEXT),
            (("before after",), CONTROL_TEXT),
        ]
        self.subprocess("add", "existing")
        original = self.data_file.read_bytes()
        for words, message in cases:
            with self.subTest(words=words):
                result = self.subprocess("edit", "1", *words)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", message))
                self.assertEqual(self.data_file.read_bytes(), original)

    def test_text_is_validated_before_the_data_file_is_read(self) -> None:
        self.subprocess("add", "existing")
        original = self.data_file.read_bytes()
        result = self.subprocess("edit", "7", "   ")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", EMPTY_TEXT))
        self.assertEqual(self.data_file.read_bytes(), original)

        corrupt = b"{"
        self.write_raw(corrupt)
        result = self.subprocess("edit", "1", "before\nafter")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, "", CONTROL_TEXT))
        self.assertEqual(self.data_file.read_bytes(), corrupt)

    def test_corrupt_data_file_is_read_error(self) -> None:
        corrupt = b"{"
        self.write_raw(corrupt)
        result = self.subprocess("edit", "1", "new")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("todo_cli: error: cannot read data file "))
        self.assertEqual(self.data_file.read_bytes(), corrupt)
