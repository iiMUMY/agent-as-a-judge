from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_as_a_judge.languages import ALL_LANGUAGES, FRAMEWORKS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync canonical instance JSONs from one pack/framework to all matching targets."
    )
    parser.add_argument("--benchmark_root", default="benchmark_tests")
    parser.add_argument("--source_pack", default="gpt-4o")
    parser.add_argument("--source_language", default="English")
    parser.add_argument("--source_framework", default="MetaGPT")
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["English"],
        help="Target languages to sync.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    benchmark_root = REPO_ROOT / args.benchmark_root
    source_instances_dir = (
        benchmark_root
        / args.source_pack
        / args.source_language
        / args.source_framework
        / "devai"
        / "instances"
    )
    if not source_instances_dir.exists():
        raise FileNotFoundError(f"Source instances directory not found: {source_instances_dir}")

    pack_dirs = sorted(
        child for child in benchmark_root.iterdir() if child.is_dir() and (child / "English").exists()
    )
    for language in args.languages:
        if language not in ALL_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        for pack_dir in pack_dirs:
            for framework in FRAMEWORKS:
                if (
                    pack_dir.name == args.source_pack
                    and language == args.source_language
                    and framework == args.source_framework
                ):
                    continue
                target_instances_dir = (
                    pack_dir / language / framework / "devai" / "instances"
                )
                if not target_instances_dir.exists():
                    raise FileNotFoundError(f"Target instances directory not found: {target_instances_dir}")
                shutil.rmtree(target_instances_dir)
                shutil.copytree(source_instances_dir, target_instances_dir)
                print(f"Synced {language} -> {pack_dir.name}/{framework}")


if __name__ == "__main__":
    main()
