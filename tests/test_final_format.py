import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import make_optimized  # noqa: E402

PRE_MD = """# 测试标题

> 来源: 本地文件 | 时长 00:08 | 转录: FunASR 2026-09-03 | 整理: 机器预整理

## 目录

1. 第一章 [00:00]
2. 第二章 [00:04]

## 1. 第一章 [00:00 - 00:04]

第一段正文。

## 2. 第二章 [00:04 - 00:08]

第二段正文。

---

## 附：识别修正对照表（整理时改动）

**已修正（确信度高）**：
- （待 LLM 增量补全）
"""

TS = re.compile(r"\[\s*\d{1,2}:\d{2}(\s*[-–~]\s*\d{1,2}:\d{2})?\s*\]")


class FinalHasNoTimestampsTest(unittest.TestCase):
    def test_md_and_html_drop_section_timestamps(self):
        content = make_optimized.parse_optimized_md(PRE_MD)
        self.assertEqual(len(content["sections"]), 2)
        md = make_optimized.build_md(content)
        html = make_optimized.build_html(content, md, "t.md")
        body_md = md.split("## 目录", 1)[1]
        self.assertIsNone(TS.search(body_md), body_md)
        self.assertIsNone(TS.search(html.split("<h2>目录</h2>", 1)[1]), html)
        self.assertIn("## 1. 第一章\n", md)
        self.assertIn("1. 第一章\n", md)


if __name__ == "__main__":
    unittest.main()
