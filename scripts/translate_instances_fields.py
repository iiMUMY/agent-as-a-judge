import argparse
import json
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion


def _extract_json_block(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def _translate_payload(payload: dict, model: str, language: str, retries: int = 5) -> dict:
    system_prompt = (
        "You are a precise software benchmark translator. "
        "Translate text to the target language while preserving technical meaning."
    )
    user_prompt = (
        f"Target language: {language}\n"
        "Translate the JSON fields below.\n"
        "Rules:\n"
        "1) Translate all natural language text completely to the target language.\n"
        "2) Keep technical tokens, library names, code identifiers, file paths, and numbers unchanged when appropriate.\n"
        "3) Preserve punctuation and intent.\n"
        "4) Return ONLY valid JSON with exactly these keys: query, requirements, preferences.\n"
        "5) requirements and preferences must keep the exact same list lengths.\n"
        "6) Do not add explanations or markdown.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            content = response.choices[0].message.content or ""
            translated = _extract_json_block(content)
            if not isinstance(translated, dict):
                raise ValueError("Translated output is not an object")
            return translated
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(min(2 * attempt, 8))
    raise RuntimeError(f"Translation failed after {retries} attempts: {last_error}")


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

        translated = _translate_payload(payload, model=args.model, language=args.language)

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
