"""Verification test suite for TARA Transformer Intent & Fallback Engine."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from predict import predict_intent


def run_tests():
    print("=" * 60)
    print("RUNNING TARA END-TO-END INFERENCE TESTS")
    print("=" * 60)

    test_cases = [
        # (Query, Session_ID, Expected Behavior)
        ("hello", None, "Greeting"),
        ("hi", None, "Greeting"),
        ("hey tara", None, "Greeting with name"),
        ("good morning", None, "Morning Greeting"),
        ("who are you", None, "Identity / ABOUT_TARA"),
        ("what can you do", None, "Capabilities / HELP"),
        ("tell me a joke", None, "Humor / JOKE"),
        ("remind me to submit the assignment at 6 pm", None, "REMINDER"),
        ("What is machine learning?", "sess-ai-context", "General AI Concept"),
        ("What are its types?", "sess-ai-context", "Contextual Follow-up"),
        ("Explain backpropagation.", None, "Deep Learning Concept"),
        ("Why are neural networks useful?", None, "General Educational"),
        ("quantum banana pizza on pluto", None, "Out-of-domain Fallback"),
    ]

    for query, session_id, label in test_cases:
        out = predict_intent(query, session_id=session_id)
        print(f"[{label}]")
        print(f"  Input:    {query}")
        print(f"  Intent:   {out['intent']} (raw: {out['raw_intent']}, conf: {out['confidence']})")
        print(f"  Response: {out['response']}")
        print("-" * 60)


if __name__ == "__main__":
    run_tests()
