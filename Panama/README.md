## Task: Panama — *The Canal Knows Too Much*

**Problem.** An AI assistant scored an unusually high 73.75% on the CanalQA factual benchmark. The task is to audit this result by finding bilingual data leakage in the fine-tuning corpus, identify every benchmark item that cannot be credited to the assistant, and recompute its true honest accuracy. The findings must perfectly match a cryptographically sealed compliance certificate to reveal the flag.

**Input:** `canalqa_audit.json` containing the benchmark (80 questions with gold answers), model predictions, a fine-tuning corpus of 400 bilingual log entries (English/Spanish), and a small Spanish-English glossary. `audit_seal.json` containing the encrypted flag.
**Output:** `report.json` — `{"excluded_ids": ["CQA-001", ...], "honest_accuracy": 0.6441}`. 

**Approach.** The assistant's high score is driven by training logs that explicitly contain the benchmark questions and answers. The challenge is matching English benchmark questions to Spanish logs, as word-for-word translation using the provided glossary breaks on multi-word concepts (e.g., *año de finalización* does not translate cleanly to *completion year* because *de* is missing from the glossary). The solution programmatically detects leakage without hardcoding grammar fixes:

1. Normalize all text (lower-case, strip accents).
2. Extract the target *entity* and *attribute* from each English benchmark question using regex.
3. Translate the Spanish corpus logs using the provided glossary, sorting keys by length to avoid partial word replacements.
4. Search the logs for the exact target *entity* (using regex word boundaries `\b` to prevent false positives, like *panamax* triggering on *neopanamax*).
5. If the entity is found, check if the log also contains *either* the targeted attribute *or* the exact benchmark *gold answer*. (Checking for the gold answer elegantly bypasses all Spanish translation grammar issues).
6. Exclude any benchmark items found in the corpus. 
7. Recompute the honest accuracy as the share of correct predictions among the remaining, non-excluded items.

**Result.** The script identified exactly 21 compromised benchmark questions. The honest accuracy on the remaining items fell to 64.41% (38/59). Passing the generated `report.json` to the compliance script successfully unlocked the certificate, yielding the flag `SIGMOID_DECONTAMINATION`. Passed on the platform.

**Run:** 
1. `python main.py` (reads `canalqa_audit.json` and writes `report.json`).
2. `python open_seal.py report.json` (verifies the findings and decrypts the flag).
**Requires:** Python 3 standard library only.