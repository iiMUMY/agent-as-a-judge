import argparse
import json
from pathlib import Path

from dotenv import load_dotenv
from agent_as_a_judge.translation_utils import translate_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate benchmark instance text fields.")
    parser.add_argument("--instances_dir", required=True, help="Path to instances directory")
    parser.add_argument("--language", required=True, help="Target language name")
    parser.add_argument("--model", default="gpt-4o-2024-08-06", help="LLM model name")
    args = parser.parse_args()

    load_dotenv(".env")

    instances_dir = Path(args.instances_dir)
    files = sorted(instances_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files found in {instances_dir}")

    for i, instance_file in enumerate(files, 1):
        data = json.loads(instance_file.read_text(encoding="utf-8"))
        requirements = data.get("requirements", [])
        preferences = data.get("preferences", [])
        payload = {
            "query": data.get("query", ""),
            "requirements": [r.get("criteria", "") for r in requirements],
            "preferences": [p.get("criteria", "") for p in preferences],
        }

        translated = translate_payload(payload, model=args.model, language=args.language)

        if "query" not in translated or "requirements" not in translated or "preferences" not in translated:
            raise ValueError(f"Missing required keys in translation for {instance_file.name}")
        if len(translated["requirements"]) != len(requirements):
            raise ValueError(f"Requirements length mismatch for {instance_file.name}")
        if len(translated["preferences"]) != len(preferences):
            raise ValueError(f"Preferences length mismatch for {instance_file.name}")

        data["query"] = translated["query"]
        for idx, req in enumerate(requirements):
            req["criteria"] = translated["requirements"][idx]
        for idx, pref in enumerate(preferences):
            pref["criteria"] = translated["preferences"][idx]
        data["language"] = args.language

        instance_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{i}/{len(files)}] Translated {instance_file.name}")

    print(f"Completed translation of {len(files)} files to {args.language}.")


if __name__ == "__main__":
    main()
