"""
Optional helper: prints how to obtain Svarah. Does not download audio by default
(the release is large and licensed by AI4Bharat).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent

INFO = """
Svarah (AI4Bharat) — Indian English ASR evaluation set
GitHub: https://github.com/AI4Bharat/Svarah
Paper:  https://arxiv.org/abs/2305.15760

This project's live STT uses the browser Web Speech API (lang=en-IN).
Svarah is used here for documentation and human evaluation of Indian-accented English,
not as training data for Web Speech API or the intent LSTM.

After you download official clips, put them in:
  dataset/svarah/audio/
Then speak / play evaluation_phrases.json while watching the on-screen transcript.
"""


def main() -> None:
    print(INFO)
    print(f"Folder: {ROOT}")
    print(f"Phrases file exists: {(ROOT / 'evaluation_phrases.json').exists()}")


if __name__ == "__main__":
    main()
