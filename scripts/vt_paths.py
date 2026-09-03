#!/usr/bin/env python3
"""skill 根目录、.env 与输出目录的统一解析。

优先级:命令行 --output-dir > 环境变量 / .env 里的 VT_OUTPUT_DIR > $VT_HOME/outputs
"""
import os

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(SKILL_DIR, ".env")
OUTPUT_DIR_ENV = "VT_OUTPUT_DIR"


def load_dotenv(path=ENV_FILE):
    """把 .env 里的 KEY=VALUE 写进环境变量;已存在的环境变量优先。"""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            os.environ.setdefault(k, v)


def resolve_output_dir(cli_value=None):
    """返回绝对路径;支持 ~ 与 $VAR。"""
    raw = cli_value or os.environ.get(OUTPUT_DIR_ENV) or ""
    raw = raw.strip()
    if not raw:
        return os.path.join(SKILL_DIR, "outputs")
    return os.path.abspath(os.path.expanduser(os.path.expandvars(raw)))
