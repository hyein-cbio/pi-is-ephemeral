"""Offline checks for Modal source uploads, commands, and failure propagation."""

import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

import modal_ci as ci


class ModalCITests(unittest.TestCase):
    def setUp(self):
        output = patch("builtins.print")
        output.start()
        self.addCleanup(output.stop)

    def test_dispatches_to_modal(self):
        with patch.object(ci, "compatibility") as function:
            ci.run_tests()
        function.remote.assert_called_once_with()

    def test_remote_failure_propagates(self):
        with patch.object(ci, "compatibility") as function:
            function.remote.side_effect = RuntimeError("remote failed")
            with self.assertRaisesRegex(RuntimeError, "remote failed"):
                ci.run_tests()

    def test_latest_install_version_reporting_and_full_suite(self):
        with patch.object(ci.subprocess, "run") as run:
            with patch.dict(os.environ, {"PI_OFFLINE": "0"}):
                ci.compatibility.local()
        self.assertEqual([call.args[0] for call in run.call_args_list], [
            ["python", "-m", "unittest", "discover", "-s", "ci", "-p", "test_*.py"],
            ["npm", "install", "--no-save", "--package-lock=false", "--ignore-scripts",
             "@earendil-works/pi-coding-agent@latest"],
            ["node", "--version"],
            ["npm", "ls", "@earendil-works/pi-coding-agent", "--depth=0"],
            ["node_modules/.bin/pi", "--version"],
            ["npm", "test"],
            ["npm", "run", "test:integration"],
        ])
        for call in run.call_args_list:
            self.assertTrue(call.kwargs["check"])
            self.assertEqual(call.kwargs["cwd"], "/workspace")
            self.assertEqual(call.kwargs["env"]["PI_OFFLINE"], "1")

    def test_command_failure_stops_checks_and_propagates(self):
        for index in range(7):
            with self.subTest(index=index), patch.object(
                ci.subprocess, "run",
                side_effect=[None] * index + [subprocess.CalledProcessError(1, "check")],
            ) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    ci.compatibility.local()
                self.assertEqual(run.call_count, index + 1)

    def test_source_upload_allowlist_and_latest_lts(self):
        image = MagicMock()
        for method in ("env", "workdir", "add_local_file", "add_local_dir"):
            getattr(image, method).return_value = image
        with patch.object(ci.modal, "is_local", return_value=True):
            with patch.object(ci.modal.Image, "from_registry", return_value=image) as registry:
                self.assertIs(ci.make_image(), image)
        registry.assert_called_once_with("node:lts-bookworm-slim", add_python="3.11")
        self.assertEqual(image.env.call_args.args[0]["PI_OFFLINE"], "1")
        self.assertEqual([call.args for call in image.add_local_file.call_args_list], [
            (ci.ROOT / path, f"/workspace/{path}")
            for path in ("package.json", "ci/modal_ci.py", "ci/test_modal_ci.py")
        ])
        self.assertEqual([call.args for call in image.add_local_dir.call_args_list], [
            (ci.ROOT / path, f"/workspace/{path}") for path in ("extensions", "test")
        ])

    def test_remote_import_skips_local_uploads(self):
        image = MagicMock()
        image.env.return_value = image
        image.workdir.return_value = image
        with patch.object(ci.modal, "is_local", return_value=False):
            with patch.object(ci.modal.Image, "from_registry", return_value=image):
                self.assertIs(ci.make_image(), image)
        image.add_local_file.assert_not_called()
        image.add_local_dir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
