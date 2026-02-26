import argparse
import json
import re
from pathlib import Path

BACKTICK_PATTERN = re.compile(r"`([^`]+)`")
PURE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_.\-/\\]+/?$")
EMBEDDED_PATH_PATTERN = re.compile(r"[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)+[\\/]?")


def extract_path_candidates(token: str) -> list[str]:
    token = token.strip().strip("\"'")
    if not token:
        return []
    if PURE_PATH_PATTERN.fullmatch(token):
        return [token]
    return EMBEDDED_PATH_PATTERN.findall(token)


def normalize_relative_path(token: str) -> tuple[str, bool] | None:
    raw = token.strip().strip("\"'")
    is_dir = raw.endswith("/") or raw.endswith("\\")
    raw = raw.replace("\\", "/").lstrip("/")
    if raw.startswith("./"):
        raw = raw[2:]
    if not raw:
        return None
    rel = Path(raw)
    if rel.is_absolute():
        return None
    if any(part in {"..", ""} for part in rel.parts):
        return None
    return str(rel).replace("\\", "/"), is_dir


def looks_like_file_path(candidate: str) -> bool:
    cleaned = candidate.strip().strip("\"'")
    if "/" in cleaned or "\\" in cleaned:
        return True
    suffix = Path(cleaned).suffix.lower()
    allowed = {
        ".py",
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".yaml",
        ".yml",
        ".png",
        ".gif",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".webp",
        ".pt",
        ".pth",
        ".npy",
        ".npz",
        ".pkl",
        ".h5",
    }
    return suffix in allowed


def is_logic_required(criteria: str) -> bool:
    text = criteria.lower()
    logic_cues = [
        "algorithm",
        "implemented",
        "defined",
        "imported",
        "training",
        "evaluate",
        "predict",
        "classif",
        "detect",
        "segment",
        "generate",
        "summar",
        "record",
        "visualize",
        "plot",
        "using",
    ]
    return any(cue in text for cue in logic_cues)


def build_spec(instances_dir: Path) -> dict:
    task_specs: dict[str, dict] = {}
    for instance_file in sorted(instances_dir.glob("*.json")):
        data = json.loads(instance_file.read_text(encoding="utf-8"))
        task_name = instance_file.stem
        task_spec = {
            "instance_file": str(instance_file).replace("\\", "/"),
            "query": data.get("query", ""),
            "language": data.get("language", "English"),
            "paths": [],
            "python_files": {},
            "artifact_files": [],
            "criteria": [],
        }
        seen_paths = set()
        seen_artifacts = set()
        for requirement in data.get("requirements", []):
            criteria = requirement.get("criteria", "")
            req_entry = {
                "requirement_id": requirement.get("requirement_id"),
                "criteria": criteria,
                "category": requirement.get("category", ""),
                "logic_required": is_logic_required(criteria),
                "paths": [],
            }

            for backtick in BACKTICK_PATTERN.findall(criteria):
                for candidate in extract_path_candidates(backtick):
                    if not looks_like_file_path(candidate):
                        continue
                    normalized = normalize_relative_path(candidate)
                    if not normalized:
                        continue
                    rel_path, is_dir = normalized
                    req_entry["paths"].append({"path": rel_path, "is_dir": is_dir})
                    path_key = (rel_path, is_dir)
                    if path_key not in seen_paths:
                        task_spec["paths"].append({"path": rel_path, "is_dir": is_dir})
                        seen_paths.add(path_key)

                    if not is_dir:
                        if rel_path.endswith(".py"):
                            file_criteria = task_spec["python_files"].setdefault(
                                rel_path, []
                            )
                            file_criteria.append(criteria)
                        else:
                            if rel_path not in seen_artifacts:
                                task_spec["artifact_files"].append(rel_path)
                                seen_artifacts.add(rel_path)

            task_spec["criteria"].append(req_entry)

        task_specs[task_name] = task_spec
    return task_specs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build per-task requirement spec.")
    parser.add_argument(
        "--instances_dir",
        default="benchmark_tests/English/OpenHands/devai/instances",
        help="Directory containing instance JSON files.",
    )
    parser.add_argument(
        "--output",
        default="benchmark_tests/English/requirement_spec.json",
        help="Path to write generated requirement spec JSON.",
    )
    args = parser.parse_args()

    instances_dir = Path(args.instances_dir)
    if not instances_dir.exists():
        raise FileNotFoundError(f"Instances directory not found: {instances_dir}")

    spec = build_spec(instances_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(f"Wrote spec for {len(spec)} tasks to {output_path}")


if __name__ == "__main__":
    main()
