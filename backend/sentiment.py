"""Lightweight lexicon-based sentiment analysis (not emotion detection)."""

from __future__ import annotations

POSITIVE_WORDS = {
    "good", "great", "awesome", "excellent", "amazing", "love", "loved", "happy",
    "thanks", "thank", "helpful", "wonderful", "fantastic", "nice", "cool",
    "perfect", "glad", "appreciate", "brilliant", "super", "best", "enjoy",
    "pleased", "wow", "yes", "yeah", "yay", "excited", "hopeful",
}

NEGATIVE_WORDS = {
    "bad", "worse", "worst", "hate", "hated", "angry", "upset", "sad", "terrible",
    "awful", "stupid", "useless", "broken", "fail", "failed", "problem", "issue",
    "confused", "lost", "worried", "annoying", "frustrated", "disappoint",
    "disappointed", "horrible", "stress", "stressed", "no", "not", "never",
    "cant", "cannot", "don't", "dont", "difficult", "hard", "helpless", "struggling",
}

NEGATION = {"not", "never", "no", "dont", "don't", "cannot", "cant"}


def analyze_sentiment(text: str) -> dict:
    tokens = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in (text or "")).split()
    pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)

    # Simple negation flip: "not good" should not stay strongly positive
    for i, t in enumerate(tokens[:-1]):
        if t in NEGATION and tokens[i + 1] in POSITIVE_WORDS:
            pos -= 1
            neg += 1

    score = pos - neg
    if score > 0:
        label = "Positive"
    elif score < 0:
        label = "Negative"
    else:
        label = "Neutral"

    magnitude = abs(score)
    confidence = min(0.95, 0.5 + 0.12 * magnitude)
    return {"label": label, "score": score, "confidence": round(confidence, 3)}


def adapt_response(base: str, sentiment_label: str) -> str:
    if sentiment_label == "Positive":
        prefixes = (
            "Glad to hear! ",
            "Happy to help! ",
            "",
        )
        prefix = prefixes[abs(hash(base)) % len(prefixes)]
        return prefix + base
    if sentiment_label == "Negative":
        return "I understand this can be challenging. " + base
    return base
