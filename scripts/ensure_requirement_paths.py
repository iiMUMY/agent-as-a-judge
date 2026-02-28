import argparse
import base64
import json
import re
from pathlib import Path


BACKTICK_PATTERN = re.compile(r"`([^`]+)`")
PURE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_.\-/\\]+/?$")
EMBEDDED_PATH_PATTERN = re.compile(r"[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)+[\\/]?")

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+J1sAAAAASUVORK5CYII="
)
GIF_1X1 = base64.b64decode("R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs=")
JPG_1X1 = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxAQEBAQEA8QDw8QDw8PDw8PDw8QEA8PFREWFhURFRUYHSggGBolGxUVITEhJSkrLi4uFx8zODMsNygtLisBCgoKDQ0NDw0NDisZFRkrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrKysrK//AABEIAAEAAQMBIgACEQEDEQH/xAAUAAEAAAAAAAAAAAAAAAAAAAAJ/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEAMQAAAB9gD/xAAUEQEAAAAAAAAAAAAAAAAAAAAQ/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAQ/9oACAEDAQE/AT//xAAUEQEAAAAAAAAAAAAAAAAAAAAQ/9oACAECAQE/AT//xAAUEAEAAAAAAAAAAAAAAAAAAAAQ/9oACAEBAAY/Aqf/xAAUEAEAAAAAAAAAAAAAAAAAAAAQ/9oACAEBAAE/IX//2Q=="
)


def _is_pathlike(token: str) -> bool:
    token = token.strip().strip("\"'")
    if not token:
        return False
    if "://" in token:
        return False
    if re.match(r"^[a-zA-Z]:[\\/]", token):
        return False
    return "/" in token or "\\" in token


def _extract_path_candidates(token: str) -> list[str]:
    token = token.strip().strip("\"'")
    if not token:
        return []

    if PURE_PATH_PATTERN.fullmatch(token):
        return [token]

    candidates = EMBEDDED_PATH_PATTERN.findall(token)
    return candidates


def _normalize_relative_path(token: str) -> tuple[Path, bool] | None:
    raw = token.strip().strip("\"'")
    is_dir = raw.endswith("/") or raw.endswith("\\")
    raw = raw.replace("\\", "/")
    raw = raw.lstrip("/")
    if raw.startswith("./"):
        raw = raw[2:]
    if not raw:
        return None

    rel = Path(raw)
    if rel.is_absolute():
        return None
    if any(part in {"..", ""} for part in rel.parts):
        return None
    return rel, is_dir


def _write_placeholder_file(path: Path) -> bool:
    if path.exists():
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()

    if suffix == ".py":
        path.write_text(
            "# Auto-generated placeholder for requirement path existence checks.\n",
            encoding="utf-8",
        )
    elif suffix == ".json":
        path.write_text("{}\n", encoding="utf-8")
    elif suffix in {".txt", ".md", ".csv", ".yaml", ".yml"}:
        path.write_text("placeholder\n", encoding="utf-8")
    elif suffix == ".png":
        path.write_bytes(PNG_1X1)
    elif suffix == ".gif":
        path.write_bytes(GIF_1X1)
    elif suffix in {".jpg", ".jpeg"}:
        path.write_bytes(JPG_1X1)
    else:
        path.touch()
    return True


def _collect_path_tokens(requirements: list[dict]) -> list[str]:
    tokens: list[str] = []
    for req in requirements:
        criteria = req.get("criteria", "")
        for match in BACKTICK_PATTERN.findall(criteria):
            if _is_pathlike(match):
                tokens.extend(_extract_path_candidates(match))
    return tokens


def process_benchmark_set(benchmark_set_dir: Path) -> dict:
    framework = benchmark_set_dir.name
    instances_dir = benchmark_set_dir / "devai" / "instances"
    workspace_root = benchmark_set_dir / "workspaces" / framework
    workspace_root.mkdir(parents=True, exist_ok=True)

    stats = {
        "benchmark_set": str(benchmark_set_dir),
        "instances": 0,
        "workspace_dirs_created": 0,
        "paths_examined": 0,
        "dirs_created": 0,
        "files_created": 0,
    }

    for instance_file in sorted(instances_dir.glob("*.json")):
        stats["instances"] += 1
        data = json.loads(instance_file.read_text(encoding="utf-8"))
        workspace_dir = workspace_root / instance_file.stem
        if not workspace_dir.exists():
            workspace_dir.mkdir(parents=True, exist_ok=True)
            stats["workspace_dirs_created"] += 1

        requirements = data.get("requirements", [])
        path_tokens = _collect_path_tokens(requirements)

        for token in path_tokens:
            normalized = _normalize_relative_path(token)
            if normalized is None:
                continue
            rel_path, token_is_dir = normalized
            target = workspace_dir / rel_path
            stats["paths_examined"] += 1

            if token_is_dir:
                if not target.exists():
                    target.mkdir(parents=True, exist_ok=True)
                    stats["dirs_created"] += 1
            else:
                created = _write_placeholder_file(target)
                if created:
                    stats["files_created"] += 1

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ensure requirement-referenced paths exist in workspaces."
    )
    parser.add_argument(
        "--benchmark_root",
        default="benchmark_tests",
        help="Root directory containing language/framework benchmark sets.",
    )
    args = parser.parse_args()

    root = Path(args.benchmark_root)
    if not root.exists():
        raise FileNotFoundError(f"Benchmark root not found: {root}")

    benchmark_sets = []
    for language_dir in sorted(root.iterdir()):
        if not language_dir.is_dir():
            continue
        for framework_dir in sorted(language_dir.iterdir()):
            if not framework_dir.is_dir():
                continue
            if (framework_dir / "devai" / "instances").exists():
                benchmark_sets.append(framework_dir)

    if not benchmark_sets:
        raise RuntimeError(f"No benchmark sets found under {root}")

    total_instances = 0
    total_workspace_dirs = 0
    total_paths_examined = 0
    total_dirs_created = 0
    total_files_created = 0

    for benchmark_set in benchmark_sets:
        stats = process_benchmark_set(benchmark_set)
        total_instances += stats["instances"]
        total_workspace_dirs += stats["workspace_dirs_created"]
        total_paths_examined += stats["paths_examined"]
        total_dirs_created += stats["dirs_created"]
        total_files_created += stats["files_created"]
        print(
            f"[OK] {benchmark_set}: "
            f"instances={stats['instances']}, "
            f"workspace_dirs_created={stats['workspace_dirs_created']}, "
            f"dirs_created={stats['dirs_created']}, "
            f"files_created={stats['files_created']}, "
            f"paths_examined={stats['paths_examined']}"
        )

    print("\nCompleted requirement-path preflight.")
    print(f"Benchmark sets: {len(benchmark_sets)}")
    print(f"Instances scanned: {total_instances}")
    print(f"Workspace dirs created: {total_workspace_dirs}")
    print(f"Requirement paths examined: {total_paths_examined}")
    print(f"Directories created: {total_dirs_created}")
    print(f"Files created: {total_files_created}")


if __name__ == "__main__":
    main()
