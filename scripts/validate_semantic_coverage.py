import argparse
import json
import re
from pathlib import Path

QUOTED_PATTERN = re.compile(r"\"([^\"]+)\"")


def extract_signature_tokens(criteria: str) -> list[str]:
    tokens = [q.strip() for q in QUOTED_PATTERN.findall(criteria) if q.strip()]
    lower = criteria.lower()
    for token in [
        "q-learning",
        "gridworld",
        "resnet-18",
        "tqdm",
        "torchvision.transforms",
        "lstm",
        "bert",
        "yolo",
        "xgboost",
        "kmeans",
        "ppo",
        "dqn",
        "gcn",
        "unet",
    ]:
        if token in lower:
            tokens.append(token)
    return sorted(set(tokens))


def validate_workspace(spec: dict, workspace_root: Path) -> dict:
    stats = {
        "tasks": 0,
        "missing_paths": 0,
        "python_files_checked": 0,
        "python_signature_misses": 0,
    }
    failures = []

    for task_name, task_spec in spec.items():
        stats["tasks"] += 1
        task_root = workspace_root / task_name
        for path_entry in task_spec.get("paths", []):
            target = task_root / path_entry["path"]
            if not target.exists():
                stats["missing_paths"] += 1
                failures.append(
                    {
                        "task": task_name,
                        "type": "missing_path",
                        "path": str(target).replace("\\", "/"),
                    }
                )

        for py_path, criteria_list in task_spec.get("python_files", {}).items():
            target = task_root / py_path
            if not target.exists():
                continue
            stats["python_files_checked"] += 1
            content = target.read_text(encoding="utf-8", errors="ignore").lower()
            tokens = []
            for criteria in criteria_list:
                tokens.extend(extract_signature_tokens(criteria))
            tokens = sorted(set([t.lower() for t in tokens]))
            if tokens and not any(token in content for token in tokens):
                stats["python_signature_misses"] += 1
                failures.append(
                    {
                        "task": task_name,
                        "type": "python_signature_miss",
                        "file": str(target).replace("\\", "/"),
                        "tokens": tokens,
                    }
                )
    return {"stats": stats, "failures": failures}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate semantic coverage.")
    parser.add_argument(
        "--spec",
        default="benchmark_tests/English/requirement_spec.json",
        help="Requirement spec file.",
    )
    parser.add_argument(
        "--workspace_root",
        default="benchmark_tests/English/OpenHands/workspaces/OpenHands",
        help="Workspace root to validate.",
    )
    parser.add_argument(
        "--output",
        default="benchmark_tests/English/semantic_validation_openhands.json",
        help="Validation report output path.",
    )
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    report = validate_workspace(spec=spec, workspace_root=Path(args.workspace_root))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    stats = report["stats"]
    print(
        "Validation completed: "
        f"tasks={stats['tasks']}, "
        f"missing_paths={stats['missing_paths']}, "
        f"python_files_checked={stats['python_files_checked']}, "
        f"python_signature_misses={stats['python_signature_misses']}"
    )
    print(f"Report: {out_path}")


if __name__ == "__main__":
    main()
