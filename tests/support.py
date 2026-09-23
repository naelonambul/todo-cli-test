"""Shared filesystem and environment isolation for every test."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from todo_cli.store import data_path

REPO_ROOT = Path(__file__).resolve().parents[1]


class IsolatedTestCase(unittest.TestCase):
    """Give each test a temporary HOME and data file."""

    use_default_location = False

    def setUp(self) -> None:
        super().setUp()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.temp_path = Path(self.temporary_directory.name).resolve()
        self.data_file = self.temp_path / "nested" / "todos.json"
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.temp_path / "home")
        Path(self.env["HOME"]).mkdir()
        if self.use_default_location:
            self.env.pop("TODO_CLI_FILE", None)
        else:
            self.env["TODO_CLI_FILE"] = str(self.data_file)
        self._environment_patch = patch.dict(os.environ, self.env, clear=True)
        self._environment_patch.start()
        self.addCleanup(self._environment_patch.stop)
        resolved = data_path().resolve()
        self.assertTrue(
            resolved == self.temp_path or self.temp_path in resolved.parents,
            f"resolved data path escaped test temp dir: {resolved}",
        )

    def subprocess(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        """Run the actual package entry point with this test's environment."""
        return subprocess.run(
            [sys.executable, "-m", "todo_cli", *arguments],
            cwd=REPO_ROOT,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )
