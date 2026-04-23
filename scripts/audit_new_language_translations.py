from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

# Repo root (parent of scripts/)
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_as_a_judge.languages import NEW_LANGUAGES
from agent_as_a_judge.module.prompt.prompt_ask import get_ask_prompt
from agent_as_a_judge.module.prompt.prompt_judge import get_judge_prompt
from agent_as_a_judge.module.prompt.prompt_locate import get_prompt_locate
from agent_as_a_judge.module.prompt.prompt_planning import get_planning_prompt
from agent_as_a_judge.module.prompt.prompt_retrieve import get_text_retrieve_prompt
from agent_as_a_judge.module.prompt.system_prompt_ask import get_ask_system_prompt
from agent_as_a_judge.module.prompt.system_prompt_judge import get_judge_system_prompt
from agent_as_a_judge.module.prompt.system_prompt_locate import get_system_prompt_locate
from agent_as_a_judge.module.prompt.system_prompt_planning import get_planning_system_prompt
from agent_as_a_judge.module.prompt.system_prompt_retrieve import get_retrieve_system_prompt
from agent_as_a_judge.translation_utils import extract_json_block, llm_text_completion

BACKTICK_RE = re.compile(r"`[^`]+`")
ANGLE_RE = re.compile(r"<[^>]+>")
ACTION_RE = re.compile(r"\[[A-Za-z][^\]]+\]")
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit translation quality for newly added benchmark languages."
    )
    parser.add_argument("--benchmark_root", default="benchmark_tests")
    parser.add_argument("--source_pack", default="gpt-4o")
    parser.add_argument(
        "--languages",
        nargs="+",
        default=list(NEW_LANGUAGES),
    )
    parser.add_argument(
        "--model",
        default="openrouter/openai/gpt-5.4",
        help="LLM used for review.",
    )
    parser.add_argument(
        "--output_json",
        default="analysis/new_language_translation_audit.json",
    )
    parser.add_argument(
        "--output_md",
        default="analysis/new_language_translation_audit.md",
    )
    return parser.parse_args()


def _protected_tokens(text: str) -> dict[str, list[str]]:
    return {
        "backticks": BACKTICK_RE.findall(text),
        "angles": ANGLE_RE.findall(text),
        "actions": ACTION_RE.findall(text),
    }


def _compare_prompt_tokens(source: str, target: str) -> list[str]:
    issues: list[str] = []
    source_tokens = _protected_tokens(source)
    target_tokens = _protected_tokens(target)
    for key in ("backticks", "angles", "actions"):
        if source_tokens[key] != target_tokens[key]:
            issues.append(f"Protected token mismatch in {key}")
    return issues


def _compare_instance_tokens(source: str, target: str) -> list[str]:
    issues: list[str] = []
    source_backticks = BACKTICK_RE.findall(source)
    target_backticks = BACKTICK_RE.findall(target)
    if Counter(source_backticks) != Counter(target_backticks):
        issues.append("Protected token mismatch in backticks")
    return issues


def _review_pair(
    *,
    item_type: str,
    item_name: str,
    language: str,
    source_payload: dict,
    target_payload: dict,
    model: str,
) -> dict:
    system_prompt = (
        "You are a rigorous translation quality auditor for multilingual software benchmarks. "
        "Assess whether the target translation is faithful, fluent, and preserves all technical tokens."
    )
    user_prompt = (
        f"Target language: {language}\n"
        f"Item type: {item_type}\n"
        f"Item name: {item_name}\n"
        "Review the translation quality.\n"
        "Rules:\n"
        "1) Check semantic faithfulness to the English source.\n"
        "2) Check fluency and naturalness in the target language.\n"
        "3) Check preservation of technical tokens, code identifiers, file paths, filenames, action tags, and judgment tags.\n"
        "4) Return ONLY valid JSON with keys faithful, accuracy_score, fluency_score, issues.\n"
        "5) accuracy_score and fluency_score must be integers from 1 to 5.\n"
        "6) issues must be a short list of concrete problems, or [] if none.\n\n"
        f"English source:\n{json.dumps(source_payload, ensure_ascii=False)}\n\n"
        f"Target translation:\n{json.dumps(target_payload, ensure_ascii=False)}"
    )
    response = llm_text_completion(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    parsed = extract_json_block(response)
    if not isinstance(parsed, dict):
        raise ValueError("Audit response is not a JSON object")
    return {
        "faithful": bool(parsed.get("faithful", False)),
        "accuracy_score": int(parsed.get("accuracy_score", 0) or 0),
        "fluency_score": int(parsed.get("fluency_score", 0) or 0),
        "issues": list(parsed.get("issues", []) or []),
    }


def _prompt_rows() -> list[tuple[str, Callable[[str], str], dict]]:
    return [
        (
            "prompt_ask",
            lambda language: get_ask_prompt(
                question="__QUESTION__",
                evidence="__EVIDENCE__",
                language=language,
            ),
            {},
        ),
        (
            "system_prompt_ask",
            get_ask_system_prompt,
            {},
        ),
        (
            "prompt_locate",
            lambda language: get_prompt_locate(
                criteria="__CRITERIA__",
                workspace_info="__WORKSPACE__",
                language=language,
            ),
            {},
        ),
        (
            "system_prompt_locate",
            get_system_prompt_locate,
            {},
        ),
        (
            "prompt_judge",
            lambda language: get_judge_prompt(
                criteria="__CRITERIA__",
                evidence="__EVIDENCE__",
                language=language,
            ),
            {},
        ),
        (
            "system_prompt_judge",
            get_judge_system_prompt,
            {},
        ),
        (
            "prompt_retrieve",
            lambda language: get_text_retrieve_prompt(
                criteria="__CRITERIA__",
                long_context="__LONG_CONTEXT__",
                language=language,
            ),
            {},
        ),
        (
            "system_prompt_retrieve",
            get_retrieve_system_prompt,
            {},
        ),
        (
            "prompt_planning",
            lambda language: get_planning_prompt(
                criteria="__CRITERIA__",
                language=language,
            ),
            {},
        ),
        (
            "system_prompt_planning",
            get_planning_system_prompt,
            {},
        ),
    ]


def _audit_prompts(language: str, model: str) -> list[dict]:
    results: list[dict] = []
    for name, getter, _meta in _prompt_rows():
        source_text = getter("English")
        target_text = getter(language)
        heuristic_issues = _compare_prompt_tokens(source_text, target_text)
        llm_review = _review_pair(
            item_type="prompt",
            item_name=name,
            language=language,
            source_payload={"text": source_text},
            target_payload={"text": target_text},
            model=model,
        )
        results.append(
            {
                "item_type": "prompt",
                "item_name": name,
                "heuristic_issues": heuristic_issues,
                "llm_review": llm_review,
                "passed": not heuristic_issues
                and llm_review["faithful"]
                and llm_review["accuracy_score"] >= 4
                and llm_review["fluency_score"] >= 4,
            }
        )
    return results


def _audit_instances(source_instances_dir: Path, target_instances_dir: Path, language: str, model: str) -> list[dict]:
    results: list[dict] = []
    for source_file in sorted(source_instances_dir.glob("*.json")):
        target_file = target_instances_dir / source_file.name
        source_data = json.loads(source_file.read_text(encoding="utf-8"))
        target_data = json.loads(target_file.read_text(encoding="utf-8"))

        heuristic_issues: list[str] = []
        heuristic_issues.extend(
            _compare_instance_tokens(source_data.get("query", ""), target_data.get("query", ""))
        )

        source_requirements = source_data.get("requirements", [])
        target_requirements = target_data.get("requirements", [])
        source_preferences = source_data.get("preferences", [])
        target_preferences = target_data.get("preferences", [])

        if len(source_requirements) != len(target_requirements):
            heuristic_issues.append("Requirement count mismatch")
        if len(source_preferences) != len(target_preferences):
            heuristic_issues.append("Preference count mismatch")

        for source_req, target_req in zip(source_requirements, target_requirements):
            heuristic_issues.extend(
                _compare_instance_tokens(
                    source_req.get("criteria", ""),
                    target_req.get("criteria", ""),
                )
            )
        for source_pref, target_pref in zip(source_preferences, target_preferences):
            heuristic_issues.extend(
                _compare_instance_tokens(
                    source_pref.get("criteria", ""),
                    target_pref.get("criteria", ""),
                )
            )

        source_payload = {
            "query": source_data.get("query", ""),
            "requirements": [requirement.get("criteria", "") for requirement in source_requirements],
            "preferences": [preference.get("criteria", "") for preference in source_preferences],
        }
        target_payload = {
            "query": target_data.get("query", ""),
            "requirements": [requirement.get("criteria", "") for requirement in target_requirements],
            "preferences": [preference.get("criteria", "") for preference in target_preferences],
        }
        llm_review = _review_pair(
            item_type="instance",
            item_name=source_file.name,
            language=language,
            source_payload=source_payload,
            target_payload=target_payload,
            model=model,
        )

        results.append(
            {
                "item_type": "instance",
                "item_name": source_file.name,
                "heuristic_issues": heuristic_issues,
                "llm_review": llm_review,
                "passed": not heuristic_issues
                and llm_review["faithful"]
                and llm_review["accuracy_score"] >= 4
                and llm_review["fluency_score"] >= 4,
            }
        )
    return results


def _build_markdown(report: dict) -> str:
    lines = ["# New Language Translation Audit", ""]
    for language, section in report["languages"].items():
        prompt_results = [item for item in section["results"] if item["item_type"] == "prompt"]
        instance_results = [item for item in section["results"] if item["item_type"] == "instance"]
        failed = [item for item in section["results"] if not item["passed"]]
        lines.append(f"## {language}")
        lines.append(
            f"- Passed: {section['passed_count']}/{section['total_count']} "
            f"(prompts {sum(item['passed'] for item in prompt_results)}/{len(prompt_results)}, "
            f"instances {sum(item['passed'] for item in instance_results)}/{len(instance_results)})"
        )
        if failed:
            lines.append("- Review-needed items:")
            for item in failed[:10]:
                issues = item["heuristic_issues"] + item["llm_review"]["issues"]
                issue_text = "; ".join(issues) if issues else "needs manual review"
                lines.append(f"  - `{item['item_name']}`: {issue_text}")
        else:
            lines.append("- No audit issues found.")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    load_dotenv(".env")
    args = parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    benchmark_root = repo_root / args.benchmark_root
    source_pack_dir = benchmark_root / args.source_pack
    english_instances_dir = source_pack_dir / "English" / "MetaGPT" / "devai" / "instances"

    report = {"languages": {}}
    for language in args.languages:
        print(f"Auditing {language}...")
        translated_instances_dir = source_pack_dir / language / "MetaGPT" / "devai" / "instances"
        prompt_results = _audit_prompts(language, args.model)
        instance_results = _audit_instances(
            source_instances_dir=english_instances_dir,
            target_instances_dir=translated_instances_dir,
            language=language,
            model=args.model,
        )
        results = prompt_results + instance_results
        report["languages"][language] = {
            "results": results,
            "passed_count": sum(item["passed"] for item in results),
            "total_count": len(results),
        }

    output_json = repo_root / args.output_json
    output_md = repo_root / args.output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(_build_markdown(report), encoding="utf-8")
    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")


if __name__ == "__main__":
    main()
