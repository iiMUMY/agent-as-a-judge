from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--developer_agent", required=True)
    parser.add_argument("--benchmark_dir", required=True)
    parser.add_argument("--llm_model", required=True)
    parser.add_argument("--language", default="English")
    parser.add_argument("--setting", default="gray_box")
    parser.add_argument("--planning", default="efficient (no planning)")
    parser.add_argument("--clear_judgment", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    benchmark_dir = Path(args.benchmark_dir)
    judgment_dir = (
        benchmark_dir
        / "judgment"
        / args.developer_agent
        / "agent_as_a_judge"
        / args.setting
    )
    if args.clear_judgment and judgment_dir.exists():
        shutil.rmtree(judgment_dir)

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [
        sys.executable,
        "scripts/run_aaaj.py",
        "--developer_agent",
        args.developer_agent,
        "--setting",
        args.setting,
        "--planning",
        args.planning,
        "--language",
        args.language,
        "--benchmark_dir",
        str(benchmark_dir),
        "--llm_model",
        args.llm_model,
    ]
    raise SystemExit(subprocess.run(cmd, env=env, check=False).returncode)


if __name__ == "__main__":
    main()
