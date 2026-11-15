# The Abidjan Transit Ledger: recovering a dual-task routing model

Solution for the CTF task *The Abidjan Transit Ledger* (`task_cote_divoire`).
The deliverable is a single file, `main.py`.

## Problem

A small text classifier routes plain-language clerk requests to one of ten query-template labels:

| Task | Labels |
|------|--------|
| Old (transactional SQL) | `OLD_JOIN_CUSTOMER_ORDERS`, `OLD_GROUPBY_REVENUE_BY_CATEGORY`, `OLD_CRUD_INSERT_ORDER`, `OLD_CRUD_UPDATE_INVENTORY`, `OLD_CRUD_DELETE_ACCOUNT` |
| New (spatial / window) | `NEW_SPATIAL_NEAREST_WAREHOUSE`, `NEW_SPATIAL_WITHIN_RADIUS`, `NEW_WINDOW_LAG_DELIVERY_DELAY`, `NEW_WINDOW_LEAD_NEXT_SHIPMENT`, `NEW_WINDOW_PARTITION_RANK_FLEET` |

Fine-tuning on the new task alone caused catastrophic forgetting:

| Checkpoint | Old accuracy | New accuracy |
|------------|:-----------:|:-----------:|
| `original_model.joblib` | 1.00 | 0.00 |
| `finetuned_model.joblib` | 0.00 | 1.00 |

Goal: one model with **old ≥ 0.85 and new ≥ 0.85** on the hidden test set.

## Approach

Instead of patching the fine-tuned checkpoint, `main.py` retrains a compact classifier from scratch at run time on all labelled data available:

- `dataset/old_task_sample.json` (40 old-task rows, the replay data),
- `dataset/train-input.json` + `dataset/train-output.json` (250 rows covering both tasks).

After deduplication this gives 252 training rows, balanced across the ten labels.

Model: scikit-learn `Pipeline`

1. `FeatureUnion` of two TF-IDF vectorizers
   - word n-grams (1–2),
   - character n-grams (`char_wb`, 2–5), which makes it robust to rephrasings and misspellings;
2. `LogisticRegression(C=20, max_iter=2000)`.

Because the training set contains both tasks together, there is no forgetting to manage. The model sees every label in every fit. Training takes a few seconds on CPU, far below the 120 s cap.

The shipped `vectorizer.joblib` and the two checkpoints are not used. The new pipeline carries its own vectorizer. Only the I/O helpers from `model_utils.py` are imported.

## Local evaluation

5-fold stratified cross-validation on the 252 labelled rows, scored with `model_utils.accuracy_by_task`:

| Fold | Old | New |
|:----:|:---:|:---:|
| 1 | 1.000 | 1.000 |
| 2 | 0.964 | 0.957 |
| 3 | 1.000 | 0.909 |
| 4 | 1.000 | 1.000 |
| 5 | 1.000 | 1.000 |

Mean: old ≈ 0.99, new ≈ 0.97, both well above the 0.85 gates.

## How to run

The harness runs it from a working directory containing `model_utils.py`, `checkpoints/`, `dataset/` and the hidden `test-input.json`:

```bash
python main.py
```

Optional flags (same as `main_template.py`):

| Flag | Default | Meaning |
|------|---------|---------|
| `--input` | `test-input.json` | input file (filename only) |
| `--output` | `predictions.json` | output file (filename only) |
| `--model` | `checkpoints/recovered_model.joblib` | where the recovered model is saved |

Steps performed:

1. Load the training data and fit the pipeline.
2. Save the pipeline to `checkpoints/recovered_model.joblib` (optional; failure to save does not stop the run).
3. Read `test-input.json` (`{"id", "text"}` records).
4. Write `predictions.json`: one `{"id", "label"}` object per row.
