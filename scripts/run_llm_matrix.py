import argparse
import os
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv


LANGUAGES = ["English", "Arabic", "Turkish", "Chinese", "Hindi"]
FRAMEWORKS = ["MetaGPT", "GPT-Pilot", "OpenHands"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        required=True,
        help="Model used by run_aaaj (e.g., openrouter/openai/gpt-5.4).",
    )
    parser.add_argument(
        "--benchmark_root",
        default="benchmark_tests",
        help="Root directory containing model benchmark packs.",
    )
    parser.add_argument(
        "--source_pack",
        default="gpt-4o",
        help="Existing benchmark pack to clone from.",
    )
    parser.add_argument(
        "--target_pack",
        required=True,
        help="Target benchmark pack name (e.g., gpt-5.4).",
    )
    parser.add_argument(
        "--setting",
        default="gray_box",
        choices=["gray_box", "black_box"],
        help="Judge setting to use.",
    )
    parser.add_argument(
        "--planning",
        default="efficient (no planning)",
        choices=["planning", "comprehensive (no planning)", "efficient (no planning)"],
        help="Judging workflow mode.",
    )
    parser.add_argument(
        "--skip_copy",
        action="store_true",
        help="Skip cloning target pack from source pack.",
    )
    return parser.parse_args()


def run_cmd(command: list[str], env: dict[str, str]):
    print(f"\n>>> Running: {' '.join(command)}")
    completed = subprocess.run(command, env=env, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(command)}")


def main():
    load_dotenv()
    args = parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    benchmark_root = repo_root / args.benchmark_root
    source_pack_dir = benchmark_root / args.source_pack
    target_pack_dir = benchmark_root / args.target_pack

    if not source_pack_dir.exists():
        raise FileNotFoundError(f"Source benchmark pack not found: {source_pack_dir}")

    if not args.skip_copy:
        if target_pack_dir.exists():
            print(f"Removing existing target pack: {target_pack_dir}")
            shutil.rmtree(target_pack_dir)
        print(f"Cloning benchmark pack: {source_pack_dir} -> {target_pack_dir}")
        shutil.copytree(source_pack_dir, target_pack_dir)
    else:
        if not target_pack_dir.exists():
            raise FileNotFoundError(f"Target pack not found and --skip_copy provided: {target_pack_dir}")

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["PYTHONIOENCODING"] = "utf-8"

    for language in LANGUAGES:
        for framework in FRAMEWORKS:
            benchmark_dir = target_pack_dir / language / framework
            judgment_dir = benchmark_dir / "judgment"
            if judgment_dir.exists():
                print(f"Clearing old judgments: {judgment_dir}")
                shutil.rmtree(judgment_dir)

            cmd = [
                "poetry",
                "run",
                "python",
                "scripts/run_aaaj.py",
                "--developer_agent",
                framework,
                "--setting",
                args.setting,
                "--planning",
                args.planning,
                "--language",
                language,
                "--benchmark_dir",
                str(benchmark_dir),
                "--llm_model",
                args.model,
            ]
            run_cmd(cmd, env=env)

    print("\nAll matrix runs completed successfully.")


if __name__ == "__main__":
    main()
