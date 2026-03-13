import hashlib
import argparse
from pathlib import Path


LANGUAGES = ["English", "Arabic", "Turkish", "Chinese", "Hindi"]
FRAMEWORKS = ["MetaGPT", "GPT-Pilot", "OpenHands"]


def digest_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(paths):
        h.update(path.name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_pack", default="gpt-4o")
    parser.add_argument("--target_pack", default="gpt-5.4")
    args = parser.parse_args()

    root = Path("benchmark_tests")
    source_pack = args.source_pack
    target_pack = args.target_pack

    all_ok = True
    for language in LANGUAGES:
        for framework in FRAMEWORKS:
            source_base = root / source_pack / language / framework
            target_base = root / target_pack / language / framework

            source_instances = sorted((source_base / "devai" / "instances").glob("*.json"))
            target_instances = sorted((target_base / "devai" / "instances").glob("*.json"))

            source_workspaces = [p for p in (source_base / "workspaces" / framework).rglob("*") if p.is_file()]
            target_workspaces = [p for p in (target_base / "workspaces" / framework).rglob("*") if p.is_file()]

            source_trajectories = sorted((source_base / "trajectories" / framework).glob("*.json"))
            target_trajectories = sorted((target_base / "trajectories" / framework).glob("*.json"))

            parity_ok = (
                len(source_instances) == len(target_instances) == 55
                and len(source_workspaces) == len(target_workspaces)
                and len(source_trajectories) == len(target_trajectories)
            )
            all_ok = all_ok and parity_ok
            print(
                f"{language}/{framework}: instances {len(target_instances)} vs {len(source_instances)} | "
                f"workspace_files {len(target_workspaces)} vs {len(source_workspaces)} | "
                f"trajectories {len(target_trajectories)} vs {len(source_trajectories)} | parity={parity_ok}"
            )

    rep_source = sorted((root / source_pack / "English" / "MetaGPT" / "devai" / "instances").glob("*.json"))
    rep_target = sorted((root / target_pack / "English" / "MetaGPT" / "devai" / "instances").glob("*.json"))
    print(
        "instances_hash_equal(English/MetaGPT)=",
        digest_files(rep_source) == digest_files(rep_target),
    )
    print("overall_parity=", all_ok)


if __name__ == "__main__":
    main()
