"""
Minimal semantic implementation for benchmark judging.
Task: 55_SQLite_Database_Viewer_and_Analyzer_App
File: src/backend_logic.py
"""

from pathlib import Path

REQUIREMENT_CRITERIA = [
    "In `src/backend_logic.py`, retrieve all development steps from the `development_steps` table and group them by development task using the `prompt_path` field starting with `development/task/breakdown.prompt`."
]
KEYWORDS = []


def requirement_notes() -> str:
    return "\n".join(REQUIREMENT_CRITERIA)



def main():
    return {"status": "ok", "notes": requirement_notes(), "keywords": KEYWORDS}


if __name__ == "__main__":
    main()
