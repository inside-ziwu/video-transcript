import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import vt_paths  # noqa: E402


class OutputDirPriorityTest(unittest.TestCase):
    def test_default_is_skill_outputs(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(vt_paths.OUTPUT_DIR_ENV, None)
            self.assertEqual(vt_paths.resolve_output_dir(), os.path.join(ROOT, "outputs"))

    def test_env_overrides_default_and_expands_home(self):
        with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "~/逐字稿"}):
            self.assertEqual(vt_paths.resolve_output_dir(), os.path.expanduser("~/逐字稿"))

    def test_cli_overrides_env(self):
        with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "/tmp/from-env"}):
            self.assertEqual(vt_paths.resolve_output_dir("/tmp/from-cli"), "/tmp/from-cli")

    def test_dotenv_feeds_env_without_clobbering(self):
        with tempfile.TemporaryDirectory() as d:
            env_file = os.path.join(d, ".env")
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# comment\nVT_OUTPUT_DIR=\"/tmp/from-dotenv\"\n")
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop(vt_paths.OUTPUT_DIR_ENV, None)
                vt_paths.load_dotenv(env_file)
                self.assertEqual(vt_paths.resolve_output_dir(), "/tmp/from-dotenv")
            with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "/tmp/already-set"}):
                vt_paths.load_dotenv(env_file)
                self.assertEqual(vt_paths.resolve_output_dir(), "/tmp/already-set")

    def test_transcript_and_make_optimized_follow_env(self):
        with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "/tmp/shared-out"}):
            transcript = importlib.reload(importlib.import_module("transcript"))
            make_optimized = importlib.reload(importlib.import_module("make_optimized"))
            self.assertEqual(transcript.DEFAULT_OUTPUT_DIR, "/tmp/shared-out")
            self.assertEqual(transcript.CACHE_INDEX, "/tmp/shared-out/.cache/index.json")
            self.assertEqual(make_optimized.DEFAULT_OUT, "/tmp/shared-out")


if __name__ == "__main__":
    unittest.main()
