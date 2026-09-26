"""Evaluate TARA Transformer Intent Classifier on the official tara_test.jsonl split."""

import json
import pickle
import sys
from pathlib import Path

import keras
import numpy as np
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from tensorflow.keras.preprocessing.sequence import pad_sequences

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from predict import TokenAndPositionEmbedding, TransformerBlock


def main():
    test_path = ROOT.parent / "data" / "tara_dataset" / "tara_test.jsonl"
    model_path = ROOT / "model" / "tara_transformer.keras"
    tok_path = ROOT / "model" / "tokenizer.pkl"
    label2id_path = ROOT / "model" / "label2id.json"

    print(f"Loading test split from {test_path}...")
    utterances = []
    y_true_labels = []

    with open(test_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            utterances.append(row["utterance"])
            y_true_labels.append(row["intent"])

    print(f"Total test utterances: {len(utterances)}")

    l2id = json.loads(label2id_path.read_text(encoding="utf-8"))
    id2l = {v: k for k, v in l2id.items()}
    y_true = [l2id[label] for label in y_true_labels]

    with open(tok_path, "rb") as fh:
        tokenizer = pickle.load(fh)

    model = keras.models.load_model(
        model_path,
        custom_objects={
            "TokenAndPositionEmbedding": TokenAndPositionEmbedding,
            "TransformerBlock": TransformerBlock,
        },
    )

    seqs = pad_sequences(tokenizer.texts_to_sequences(utterances), maxlen=24, padding="post", truncating="post")
    probs = model.predict(seqs, verbose=0)
    y_pred = [int(np.argmax(p)) for p in probs]

    accuracy = float(np.mean(np.array(y_pred) == np.array(y_true)))
    macro_p = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_r = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    report = classification_report(
        y_true,
        y_pred,
        target_names=[id2l[i] for i in range(len(l2id))],
        digits=4,
        zero_division=0,
    )

    print("\n" + "=" * 60)
    print("OFFICIAL TEST EVALUATION RESULTS ON tara_test.jsonl")
    print("=" * 60)
    print(f"Accuracy:         {accuracy * 100:.2f}% ({accuracy:.4f})")
    print(f"Macro Precision:  {macro_p * 100:.2f}% ({macro_p:.4f})")
    print(f"Macro Recall:     {macro_r * 100:.2f}% ({macro_r:.4f})")
    print(f"Macro F1-Score:   {macro_f1 * 100:.2f}% ({macro_f1:.4f})")
    print(f"Weighted F1:      {weighted_f1 * 100:.2f}% ({weighted_f1:.4f})")
    print("\nDetailed Per-Class Report:\n")
    print(report)

    # Save to metrics file
    out_metrics = {
        "model": "TARA Transformer (Multi-Head Self-Attention Encoder)",
        "dataset": "data/tara_dataset (19 intents, 12,557 utterances total)",
        "test_split_file": "tara_test.jsonl",
        "test_samples": len(utterances),
        "test_accuracy": round(accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "num_classes": len(l2id),
        "classes": sorted(list(l2id.keys())),
    }

    metrics_file = ROOT / "model" / "evaluation_metrics.json"
    metrics_file.write_text(json.dumps(out_metrics, indent=2), encoding="utf-8")
    print(f"Updated {metrics_file}")


if __name__ == "__main__":
    main()
