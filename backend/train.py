"""
Train an LSTM intent classifier on backend/data/intents.json.

Architecture: Text → Tokenizer → Padding → Embedding → LSTM → Dropout → Dense → Softmax
Saves model, tokenizer, labels, and real metrics under backend/model/.
"""

from __future__ import annotations

import json
import pickle
import random
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras import Sequential
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import Dense, Dropout, Embedding, Input, LSTM
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.utils import to_categorical

from config import (
    DROPOUT_RATE,
    EMBEDDING_DIM,
    LSTM_UNITS,
    MAX_SEQUENCE_LENGTH,
    RANDOM_SEED,
    VOCAB_SIZE,
)

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "intents.json"
MODEL_DIR = ROOT / "model"


def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9'\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def augment(text: str) -> list[str]:
    variants = {text, text + " please", "please " + text}
    if text.startswith("what "):
        variants.add("whats " + text[5:])
    if " the " in text:
        variants.add(text.replace(" the ", " "))
    return [clean_text(v) for v in variants if clean_text(v)]


def load_xy() -> tuple[list[str], list[str]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    texts: list[str] = []
    labels: list[str] = []
    for intent in payload["intents"]:
        tag = intent["tag"]
        for pattern in intent["patterns"]:
            texts.append(clean_text(pattern))
            labels.append(tag)
    return texts, labels


def encode_xy(tokenizer: Tokenizer, texts: list[str], tags: list[str], encoder: LabelEncoder, num_classes: int):
    x = pad_sequences(
        tokenizer.texts_to_sequences(texts),
        maxlen=MAX_SEQUENCE_LENGTH,
        padding="post",
        truncating="post",
    )
    y = to_categorical(encoder.transform(tags), num_classes=num_classes)
    return x, y


def build_model(num_classes: int) -> tf.keras.Model:
    model = Sequential(
        [
            Input(shape=(MAX_SEQUENCE_LENGTH,), name="tokens"),
            Embedding(
                input_dim=VOCAB_SIZE,
                output_dim=EMBEDDING_DIM,
                mask_zero=True,
                name="embedding",
            ),
            LSTM(LSTM_UNITS, name="lstm"),
            Dropout(DROPOUT_RATE, name="dropout"),
            Dense(64, activation="relu", name="dense_hidden"),
            Dense(num_classes, activation="softmax", name="softmax"),
        ]
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.002),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main() -> None:
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    tf.random.set_seed(RANDOM_SEED)

    texts, labels = load_xy()
    encoder = LabelEncoder()
    y_int_all = encoder.fit_transform(labels)
    num_classes = len(encoder.classes_)

    x_train_raw, x_val_raw, y_train_raw, y_val_raw = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=y_int_all,
    )

    x_train_text, y_train_tags = [], []
    for text, tag in zip(x_train_raw, y_train_raw):
        for variant in augment(text):
            x_train_text.append(variant)
            y_train_tags.append(tag)

    holdout_tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
    holdout_tokenizer.fit_on_texts(x_train_text)
    x_train, y_train = encode_xy(holdout_tokenizer, x_train_text, y_train_tags, encoder, num_classes)
    x_val, y_val = encode_xy(holdout_tokenizer, x_val_raw, y_val_raw, encoder, num_classes)

    eval_model = build_model(num_classes)
    callbacks = [
        EarlyStopping(monitor="val_accuracy", patience=8, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, verbose=1),
    ]
    history = eval_model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=40,
        batch_size=16,
        verbose=2,
        callbacks=callbacks,
    )
    train_loss, train_acc = eval_model.evaluate(x_train, y_train, verbose=0)
    val_loss, val_acc = eval_model.evaluate(x_val, y_val, verbose=0)

    # Deployed weights: fit on all seed patterns + light augmentation.
    all_text, all_tags = [], []
    for text, tag in zip(texts, labels):
        for variant in augment(text):
            all_text.append(variant)
            all_tags.append(tag)
    tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
    tokenizer.fit_on_texts(all_text)
    x_all, y_all = encode_xy(tokenizer, all_text, all_tags, encoder, num_classes)
    x_fit, x_es, y_fit, y_es = train_test_split(
        x_all, y_all, test_size=0.1, random_state=RANDOM_SEED
    )
    deploy_model = build_model(num_classes)
    deploy_hist = deploy_model.fit(
        x_fit,
        y_fit,
        validation_data=(x_es, y_es),
        epochs=25,
        batch_size=16,
        verbose=2,
        callbacks=[
            EarlyStopping(monitor="val_accuracy", patience=5, restore_best_weights=True, verbose=1),
        ],
    )
    deploy_train_loss, deploy_train_acc = deploy_model.evaluate(x_all, y_all, verbose=0)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "intent_lstm.keras"
    deploy_model.save(model_path)
    with (MODEL_DIR / "tokenizer.pkl").open("wb") as fh:
        pickle.dump(tokenizer, fh)
    labels_payload = {
        "classes": encoder.classes_.tolist(),
        "tag_to_index": {tag: int(i) for i, tag in enumerate(encoder.classes_)},
    }
    (MODEL_DIR / "labels.json").write_text(json.dumps(labels_payload, indent=2), encoding="utf-8")

    hist = history.history
    metrics = {
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed_patterns": len(texts),
        "holdout": {
            "samples_train_augmented": int(len(x_train)),
            "samples_val_original": int(len(x_val)),
            "epochs_ran": len(hist.get("loss", [])),
            "train_accuracy": float(train_acc),
            "train_loss": float(train_loss),
            "val_accuracy": float(val_acc),
            "val_loss": float(val_loss),
            "note": "20% of original patterns held out before augmentation. This is the generalization estimate.",
            "history": {
                "accuracy": [float(x) for x in hist.get("accuracy", [])],
                "val_accuracy": [float(x) for x in hist.get("val_accuracy", [])],
                "loss": [float(x) for x in hist.get("loss", [])],
                "val_loss": [float(x) for x in hist.get("val_loss", [])],
            },
        },
        "deployed_model": {
            "samples": int(len(x_all)),
            "epochs_ran": len(deploy_hist.history.get("loss", [])),
            "train_accuracy_all_augmented": float(deploy_train_acc),
            "train_loss_all_augmented": float(deploy_train_loss),
            "note": "Weights shipped in intent_lstm.keras are refit on all seed patterns plus light augmentation.",
        },
        "num_classes": int(num_classes),
        "classes": encoder.classes_.tolist(),
        "architecture": "Embedding → LSTM → Dropout → Dense(ReLU) → Dense(Softmax)",
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "vocab_size": VOCAB_SIZE,
        "embedding_dim": EMBEDDING_DIM,
        "lstm_units": LSTM_UNITS,
        "notes": "All figures come from this training script. Do not replace with estimates.",
    }
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    deploy_model.summary()
    print("\n=== Hold-out evaluation (real) ===")
    print(f"Train accuracy: {train_acc:.4f}  loss: {train_loss:.4f}")
    print(f"Val accuracy:   {val_acc:.4f}  loss: {val_loss:.4f}")
    print("=== Deployed model (all seed patterns) ===")
    print(f"Augmented-set accuracy: {deploy_train_acc:.4f}  loss: {deploy_train_loss:.4f}")
    print(f"Saved: {model_path}")


if __name__ == "__main__":
    main()
