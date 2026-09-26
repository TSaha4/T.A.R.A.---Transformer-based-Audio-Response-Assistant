"""TARA Intent Classifier and Dialogue Inference Pipeline.

Transformer-based Audio & Response Assistant
Pipeline:
Voice → Web Speech (Browser) → Text → Transformer Intent Classifier → Intent & Confidence → Local Response Generation → Spoken Response → Web SpeechSynthesis
"""

from __future__ import annotations

import json
import logging
import pickle
import random
import re
import uuid
from functools import lru_cache
from pathlib import Path

import keras
import numpy as np
import tensorflow as tf
from keras import layers
# from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.utils import pad_sequences

from config import CONFIDENCE_THRESHOLD, MAX_SEQUENCE_LENGTH
from knowledge_base import answer_general_query

logger = logging.getLogger("tara.predict")

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "model"
RESPONSES_PATH = ROOT / "data" / "tara_responses.json"


# =====================================================================
# Custom Keras Layers for Transformer Architecture
# =====================================================================

@keras.saving.register_keras_serializable(name="TokenAndPositionEmbedding")
class TokenAndPositionEmbedding(layers.Layer):
    def __init__(self, maxlen: int = 24, vocab_size: int = 4000, embed_dim: int = 64, **kwargs):
        super().__init__(**kwargs)
        self.maxlen = maxlen
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.token_emb = layers.Embedding(input_dim=vocab_size, output_dim=embed_dim)
        self.pos_emb = layers.Embedding(input_dim=maxlen, output_dim=embed_dim)

    def call(self, x):
        maxlen = tf.shape(x)[-1]
        positions = tf.range(start=0, limit=maxlen, delta=1)
        positions = self.pos_emb(positions)
        x = self.token_emb(x)
        return x + positions

    def get_config(self):
        config = super().get_config()
        config.update({
            "maxlen": self.maxlen,
            "vocab_size": self.vocab_size,
            "embed_dim": self.embed_dim,
        })
        return config


@keras.saving.register_keras_serializable(name="TransformerBlock")
class TransformerBlock(layers.Layer):
    def __init__(self, embed_dim: int = 64, num_heads: int = 4, ff_dim: int = 128, rate: float = 0.15, **kwargs):
        super().__init__(**kwargs)
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.rate = rate
        self.att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = keras.Sequential(
            [
                layers.Dense(ff_dim, activation="relu"),
                layers.Dense(embed_dim),
            ]
        )
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs, training=False):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim": self.embed_dim,
            "num_heads": self.num_heads,
            "ff_dim": self.ff_dim,
            "rate": self.rate,
        })
        return config


# =====================================================================
# Text Cleaning & Normalization
# =====================================================================

def clean_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"\b(hey\s+)?tara\b", "tara", text)
    text = re.sub(r"[^a-z0-9'\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =====================================================================
# Artifact Caching
# =====================================================================

@lru_cache(maxsize=1)
def _artifacts():
    model_path = MODEL_DIR / "tara_transformer.keras"
    if not model_path.exists():
        model_path = MODEL_DIR / "intent_lstm.keras"

    custom_objs = {
        "TokenAndPositionEmbedding": TokenAndPositionEmbedding,
        "TransformerBlock": TransformerBlock,
    }
    model = keras.models.load_model(model_path, custom_objects=custom_objs)

    with (MODEL_DIR / "tokenizer.pkl").open("rb") as fh:
        tokenizer = pickle.load(fh)

    label2id_path = MODEL_DIR / "label2id.json"
    if label2id_path.exists():
        l2id = json.loads(label2id_path.read_text(encoding="utf-8"))
        id2label = {int(v): str(k) for k, v in l2id.items()}
    else:
        labels_json = json.loads((MODEL_DIR / "labels.json").read_text(encoding="utf-8"))
        id2label = {i: str(c) for i, c in enumerate(labels_json["classes"])}

    responses = {}
    if RESPONSES_PATH.exists():
        responses = json.loads(RESPONSES_PATH.read_text(encoding="utf-8"))
    else:
        # Fallback to intents.json if available
        intents_path = ROOT / "data" / "intents.json"
        if intents_path.exists():
            data = json.loads(intents_path.read_text(encoding="utf-8"))
            responses = {item["tag"]: item["responses"] for item in data["intents"]}

    return model, tokenizer, id2label, responses


def model_ready() -> bool:
    try:
        _artifacts()
        return True
    except Exception as exc:
        logger.error(f"Error checking model readiness: {exc}")
        return False


def _extract_weather_location(query: str) -> str | None:
    """Extract location if explicitly mentioned in query, e.g. 'in Pune', 'for London'."""
    match = re.search(r"\b(?:in|for|at|around|of)\s+([a-zA-Z\s]+?)(?:\?|\.|\s*$|\s+(?:today|tomorrow|right now|currently|this week))", query, re.IGNORECASE)
    if match:
        loc = match.group(1).strip()
        # Filter out common stop words / temporal words
        if loc.lower() not in {"the", "a", "an", "today", "tomorrow", "tonight", "this week", "this morning", "now", "here", "my area", "the city"}:
            return loc.title()
    return None


def _generate_honest_response(intent: str, text: str, cleaned: str, responses: dict, last_topic: str | None = None) -> str:
    """Generate an honest, natural local response respecting TARA's actual capabilities."""
    if intent == "WEATHER":
        loc = _extract_weather_location(text)
        if loc:
            return (
                f"I'm not connected to a live weather feed, so I can't confirm current conditions or forecasts for {loc}. "
                f"Please check a live weather app or search online for the latest update."
            )
        return (
            "I don't have access to live weather data or sensor feeds, so I can't report current weather conditions. "
            "A dedicated weather app or quick web search will have the latest forecast."
        )

    if intent == "TASK":
        # Check sub-action: removal/deletion, list retrieval, or task addition
        if any(w in cleaned for w in ["remove", "delete", "clear", "cancel", "drop", "cross off", "mark done"]):
            return (
                "I understand that you're asking to remove a task, but I don't have a persistent task list to modify. "
                "You can manage and delete tasks in your device's to-do app."
            )
        if any(w in cleaned for w in ["what is my list", "whats my list", "what's my list", "show my list", "view my list", "get my list", "my list"]):
            return (
                "I don't have a persistent task list connected right now, so I can't retrieve or view your current list. "
                "I recommend using a notes or to-do app on your device."
            )
        return (
            "I understand this as a task request, but persistent task storage is not currently enabled. "
            "I'd recommend using a dedicated app like Google Tasks or Todoist to track it."
        )

    if intent == "REMINDER":
        return (
            "I understand you want to set a reminder, but I don't have persistent scheduling or alarm storage enabled. "
            "Please use your phone or computer's calendar or alarm app so you don't miss it."
        )

    pool = responses.get(intent, [])
    if pool:
        return random.choice(pool)
    return answer_general_query(text, last_topic=last_topic)


# =====================================================================
# Prediction & Dialogue Manager
# =====================================================================

def predict_intent(text: str, threshold: float | None = None, session_id: str | None = None) -> dict:
    threshold = CONFIDENCE_THRESHOLD if threshold is None else threshold

    from sentiment import analyze_sentiment
    sentiment = analyze_sentiment(text)

    cleaned = clean_text(text)
    if not cleaned:
        fallback = "Hey! I am ready to help. Try the microphone or type a question."
        return {
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "response": fallback,
            "below_threshold": True,
            "sentiment": sentiment,
        }

    # Fetch last conversation context if available
    last_topic = None
    if session_id:
        try:
            from db.repository import get_repository
            repo = get_repository()
            last_topic = repo.get_last_topic(session_id)
        except Exception:
            pass

    # Check for obvious open-ended follow-up phrases that need context resolution
    is_follow_up = any(m in cleaned for m in ["its types", "their types", "what are the types", "what about it", "tell me more"])

    model, tokenizer, id2label, responses = _artifacts()
    seq = tokenizer.texts_to_sequences([cleaned])
    padded = pad_sequences(seq, maxlen=MAX_SEQUENCE_LENGTH, padding="post", truncating="post")

    probs = model.predict(padded, verbose=0)[0]
    idx = int(np.argmax(probs))
    confidence = float(probs[idx])
    predicted_intent = id2label.get(idx, "UNKNOWN")

    # Determine response strategy:
    # 1. Low confidence / UNKNOWN / general knowledge concepts / follow-up -> Built-in Knowledge Base
    # 2. Predicted intents (TASK, REMINDER, WEATHER, GREETING, etc.) -> Honest local response generator
    needs_knowledge_base = (
        predicted_intent == "UNKNOWN"
        or confidence < threshold
        or is_follow_up
        or predicted_intent in ("GENERAL_QUERY", "KNOWLEDGE")
        or any(k in cleaned for k in ["backpropagation", "machine learning", "what is ml", "neural network", "why are neural", "what is a transformer", "black hole", "why is the sky"])
    )

    if needs_knowledge_base:
        spoken_response = answer_general_query(text, last_topic=last_topic)
        final_intent = "GENERAL_QUERY" if predicted_intent == "UNKNOWN" else predicted_intent
        below = confidence < threshold
    else:
        spoken_response = _generate_honest_response(predicted_intent, text, cleaned, responses, last_topic=last_topic)
        final_intent = predicted_intent
        below = False

    # Persist to repository layer
    if session_id:
        try:
            from db.repository import get_repository, ChatMessageRecord
            repo = get_repository()
            # Infer current topic for contextual follow-ups
            topic_to_save = None
            if any(k in cleaned for k in ["machine learning", "deep learning", "neural network", "backpropagation"]):
                for k in ["machine learning", "deep learning", "neural network", "backpropagation"]:
                    if k in cleaned:
                        topic_to_save = k
                        break

            repo.save_message(ChatMessageRecord(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role="user",
                content=text,
                intent=final_intent,
                confidence=round(confidence, 4),
                sentiment=sentiment["label"],
            ))
            repo.save_message(ChatMessageRecord(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role="assistant",
                content=spoken_response,
                intent=final_intent,
                confidence=round(confidence, 4),
            ))
            if topic_to_save:
                # Store in session state
                if hasattr(repo, "_sessions"):
                    repo._sessions.setdefault(session_id, {})["last_topic"] = topic_to_save
        except Exception as exc:
            logger.debug(f"Persistence skipped: {exc}")

    return {
        "intent": final_intent,
        "raw_intent": predicted_intent,
        "confidence": round(confidence, 4),
        "response": spoken_response,
        "below_threshold": below,
        "sentiment": sentiment,
    }
