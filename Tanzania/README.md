# Please, You Are So Delusional! — Repaired Retrieval Pipeline

Repair of the starter retrieval pipeline for the *Safari ya Sayansi* (Tanzania) task.
For each of the 72 questions the pipeline returns the single best source document,
and `flag_utils.py` turns those document IDs into the flag.

## Files

| File | Purpose |
|---|---|
| `retrieval_pipeline.py` | Repaired pipeline (the only file changed) |
| `flag_utils.py` | Supplied flag helper (unchanged) |
| `corpus.jsonl`, `questions.json` | Task data (unchanged) |
| `requirements.txt` | Pinned dependencies, Python 3.11 |
| `retrieved_ids.json` | Pipeline output: `[{"question_id": ..., "document_id": ...}, ...]` |

## How to run

```bash
python -m pip install -r requirements.txt
python retrieval_pipeline.py
```

Optional arguments: `--corpus`, `--questions`, `--output`
(defaults: `corpus.jsonl`, `questions.json`, `retrieved_ids.json`).
The program saves the results and prints the flag.

## About the data

- 744 documents: 600 generic operations bulletins (`TZ-G-*`) and 144 exhibit notices.
- 24 exhibits × 3 cities (Dar es Salaam, Arusha, Mwanza). Each exhibit/city pair has two
  near-identical notices:
  - `CURRENT ACCESS NOTICE: <exhibit>, <city>` (ID ends in `A`) holds the collection point and time.
  - `ARCHIVED BACKGROUND: <exhibit>, <city>` (ID ends in `B`) is a decoy: it describes the exhibit but says it does not replace the current notice.
- Every question asks for the current access notice of one exhibit in one city, giving both the
  formal exhibit name and a descriptive alias.

## What was wrong in the starter, and the fixes

1. **Two different embedding models.** Documents used `all-MiniLM-L6-v2`, queries used
   `e5-small-v2`. Their vector spaces are unrelated, so similarities were meaningless.
   *Fix:* one model, `intfloat/e5-small-v2`, for both sides.
2. **Missing e5 prefix.** e5 expects `query: ` and `passage: ` prefixes; only the query had one.
   *Fix:* documents are now encoded with `passage: `.
3. **180-character chunks.** The title (exhibit + city), the "Access details" paragraph and the
   filler text were split into separate fragments, so the best fragment was often not from the
   right notice.
   *Fix:* each document is embedded whole (all are far below the 512-token limit).
4. **Archived look-alikes.** The decoy notices share almost all wording with the real ones, and
   nothing in the starter used the question's request for the *current* notice.
   *Fix:* before ranking, candidates are narrowed using the question text:
   - "current access notice" → keep only `CURRENT ACCESS NOTICE` titles,
   - city named in the question → keep that city,
   - formal exhibit name found in the question → keep that exhibit.

   Each narrowing step is skipped if it would leave no candidates, so unusual questions fall back
   to plain dense retrieval. Cities and exhibit names are read from the corpus titles, not hard-coded.
   The highest cosine similarity among the remaining candidates is the answer.

## Validation

- With a TF-IDF stand-in encoder, the pipeline matched an independently computed ground truth
  (formal exhibit name + city → current notice) on all 72 questions, with an identical flag.
- Narrowing leaves exactly one candidate for every question, so the dense scores only break ties
  that do not occur here.
- The same stand-in without narrowing got 4/72 on whole documents and 0/72 on the starter's
  180-character chunks.

## How the flag is built (`flag_utils.py`)

For each question in `questions.json` order, take the `verification_code` character of the
retrieved document, concatenate the 72 characters, SHA-256 the string, and format the first
20 uppercase hex digits as `SIGMOID_<...>`.
