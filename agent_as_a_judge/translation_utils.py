from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from litellm import completion


def extract_json_block(text: str) -> Any:
    text = (text or "").strip()
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


def llm_text_completion(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    retries: int = 5,
) -> str:
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
                base_url=os.getenv("OPENAI_BASE_URL"),
            )
            content = response.choices[0].message.content or ""
            if not isinstance(content, str):
                content = str(content)
            return content
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(min(2 * attempt, 8))
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_error}")


def translate_payload(
    payload: dict[str, Any],
    *,
    model: str,
    language: str,
    retries: int = 5,
) -> dict[str, Any]:
    system_prompt = (
        "You are a meticulous multilingual software benchmark translator. "
        "Produce fluent, natural, and technically faithful translations."
    )
    user_prompt = (
        f"Target language: {language}\n"
        "Translate the JSON fields below.\n"
        "Rules:\n"
        "1) Translate all natural-language content fully into the target language.\n"
        "2) Preserve all technical meaning exactly.\n"
        "3) Keep all code identifiers, library names, file paths, filenames, numbers, model names, and any text inside backticks unchanged.\n"
        "4) Do not add, remove, reorder, merge, or split items.\n"
        "5) Keep the exact same keys: query, requirements, preferences.\n"
        "6) requirements and preferences must keep the exact same list lengths.\n"
        "7) Return ONLY valid JSON. No prose. No markdown.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    content = llm_text_completion(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        retries=retries,
    )
    translated = extract_json_block(content)
    if not isinstance(translated, dict):
        raise ValueError("Translated output is not an object")
    return translated
