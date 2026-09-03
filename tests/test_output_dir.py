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

WORK = os.path.join(ROOT, "outputs")

PRE_MD = """# 测试标题

> 来源: 本地文件 | 时长 00:08 | 转录: FunASR 2026-09-03 | 整理: 机器预整理

## 目录

1. 第一章 [00:00]

## 1. 第一章 [00:00 - 00:08]

这是正文。

---

## 附：识别修正对照表（整理时改动）

**已修正（确信度高）**：
- （待 LLM 增量补全）
"""


class DirPriorityTest(unittest.TestCase):
    def test_work_dir_is_fixed_under_skill(self):
        with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "/tmp/elsewhere"}):
            self.assertEqual(vt_paths.work_dir(), WORK)

    def test_final_dir_defaults_to_work_dir(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(vt_paths.OUTPUT_DIR_ENV, None)
            self.assertEqual(vt_paths.final_dir(), WORK)

    def test_env_sets_final_dir_and_expands_home(self):
        with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "~/逐字稿"}):
            self.assertEqual(vt_paths.final_dir(), os.path.expanduser("~/逐字稿"))

    def test_cli_overrides_env(self):
        with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "/tmp/from-env"}):
            self.assertEqual(vt_paths.final_dir("/tmp/from-cli"), "/tmp/from-cli")

    def test_dotenv_feeds_env_without_clobbering(self):
        with tempfile.TemporaryDirectory() as d:
            env_file = os.path.join(d, ".env")
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# comment\nVT_OUTPUT_DIR=\"/tmp/from-dotenv\"\n")
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop(vt_paths.OUTPUT_DIR_ENV, None)
                vt_paths.load_dotenv(env_file)
                self.assertEqual(vt_paths.final_dir(), "/tmp/from-dotenv")
            with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "/tmp/already-set"}):
                vt_paths.load_dotenv(env_file)
                self.assertEqual(vt_paths.final_dir(), "/tmp/already-set")


class ScriptsFollowSplitTest(unittest.TestCase):
    def test_process_files_stay_in_work_dir_and_final_follows_env(self):
        with mock.patch.dict(os.environ, {vt_paths.OUTPUT_DIR_ENV: "/tmp/final-out"}):
            transcript = importlib.reload(importlib.import_module("transcript"))
            make_optimized = importlib.reload(importlib.import_module("make_optimized"))
            self.assertEqual(transcript.DEFAULT_OUTPUT_DIR, WORK)
            self.assertEqual(transcript.CACHE_INDEX, os.path.join(WORK, ".cache", "index.json"))
            self.assertEqual(make_optimized.DEFAULT_OUT, "/tmp/final-out")

    def test_make_optimized_writes_md_to_final_and_html_to_work(self):
        make_optimized = importlib.import_module("make_optimized")
        content = make_optimized.parse_optimized_md(PRE_MD)
        with tempfile.TemporaryDirectory() as final, tempfile.TemporaryDirectory() as work:
            md_path, html_path, _ = make_optimized.write_outputs(content, final, "t_整理优化版", html_dir=work)
            self.assertEqual(os.path.dirname(md_path), final)
            self.assertEqual(os.path.dirname(html_path), work)
            self.assertTrue(os.path.exists(md_path) and os.path.exists(html_path))
            self.assertEqual(sorted(os.listdir(final)), ["t_整理优化版.md"])


if __name__ == "__main__":
    unittest.main()
