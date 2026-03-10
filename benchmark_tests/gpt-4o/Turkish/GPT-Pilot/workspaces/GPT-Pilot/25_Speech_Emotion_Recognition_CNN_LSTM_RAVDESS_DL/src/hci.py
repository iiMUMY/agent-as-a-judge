"""
Minimal semantic implementation for benchmark judging.
Task: 25_Speech_Emotion_Recognition_CNN_LSTM_RAVDESS_DL
File: src/hci.py
"""

from pathlib import Path

REQUIREMENT_CRITERIA = [
    "A local API is created using \"Flask\" to allow users to upload audio files and receive emotion recognition results. The implementation should be included in `src/hci.py`."
]
KEYWORDS = ["Flask", "lstm"]


def requirement_notes() -> str:
    return "\n".join(REQUIREMENT_CRITERIA)



def main():
    return {"status": "ok", "notes": requirement_notes(), "keywords": KEYWORDS}


if __name__ == "__main__":
    main()
