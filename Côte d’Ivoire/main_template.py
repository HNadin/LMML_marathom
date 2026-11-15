"""Abidjan Transit Ledger - recover a single model that handles both tasks.

Approach: the fine-tuned checkpoint has overwritten the old-task decision
boundaries, so instead of patching it we retrain a compact text classifier
on everything labelled we have (old-task replay sample + the public
both-task set). Training takes a couple of seconds on CPU.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

import model_utils as mu


def load_training_data() -> tuple[list[str], list[str]]:
    texts, labels, seen = [], [], set()

    def add(text: str, label: str) -> None:
        key = (text.strip().lower(), label)
        if key not in seen:
            seen.add(key)
            texts.append(text)
            labels.append(label)

    for r in mu.load_records(Path("dataset/old_task_sample.json")):
        add(r["text"], r["label"])

    train_in = {r["id"]: r["text"] for r in mu.load_records(Path("dataset/train-input.json"))}
    train_out = {r["id"]: r["label"] for r in mu.load_records(Path("dataset/train-output.json"))}
    for rid, text in train_in.items():
        if rid in train_out:
            add(text, train_out[rid])
    return texts, labels


def build_pipeline() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, lowercase=True)),
    ])
    clf = LogisticRegression(C=20.0, max_iter=2000)
    return Pipeline([("features", features), ("clf", clf)])


def recover_model() -> Pipeline:
    texts, labels = load_training_data()
    model = build_pipeline()
    model.fit(texts, labels)
    return model


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="test-input.json", help="filename only, no path")
    parser.add_argument("--output", default="predictions.json", help="filename only, no path")
    parser.add_argument(
        "--model",
        default=str(mu.RECOVERED_MODEL_PATH),
        help="where the recovered checkpoint is saved (defaults to checkpoints/recovered_model.joblib)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"input file not found: {input_path}", file=sys.stderr)
        return 2

    model = recover_model()
    try:
        mu.save_model(model, Path(args.model))
    except Exception as exc:  # saving is optional
        print(f"could not save checkpoint: {exc}", file=sys.stderr)

    records = mu.load_records(input_path)
    ids = [r["id"] for r in records]
    texts = [r["text"] for r in records]

    labels = [str(x) for x in model.predict(texts)]
    predictions = [{"id": rid, "label": label} for rid, label in zip(ids, labels)]
    mu.save_records(predictions, Path(args.output))
    print(f"wrote {len(predictions)} predictions to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
