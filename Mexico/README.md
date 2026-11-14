## Task: Mexico — *Ruta de las Identidades*

**Problem.** Three regional registration tables (`a`, `b`, `c`) were merged and the
same reader can appear in several of them with different spelling. Find every pair
of records that refers to the same person. Scoring is all-or-nothing: the set of
pairs must match the reference exactly.

**Input:** `test-input.csv` with columns `source_table, record_id, first_name, last_name, address`.
**Output:** `test-output.json` — `{"matches": [["a0001", "c0002"], ...]}`; if three
records are the same person, all three pairs are listed.

**Approach.** Exploring the training data showed that names are noisy (typos,
initials, swapped first/last name, missing accents), while the *address* is the
same in every true pair — only its *writing* changes. So the solution links
records by a canonical address key:

1. Lower-case, strip accents and punctuation.
2. Expand the abbreviations seen in the data (`Int.` → `interior`, `Av.` → `avenida`,
   `Priv.` → `privada`, `Ret.` → `retorno`, `C.jón` → `callejon`, `Blvd.` → `boulevard`, …).
3. Sort the address tokens, so the house number can stand before or after the street name.
4. Records with the same key from *different* tables form a group; all pairs inside
   a group are output (so a 3-record group gives 3 pairs).
5. Fallback: if two records from the same table share an address, a pair is accepted
   only if the names are also similar (order-insensitive `SequenceMatcher` ratio ≥ 0.6).

**Result.** On the training data this reproduces `train-output.json` exactly
(12 038 / 12 038 pairs, no extras). Passed on the platform.

**Run:** `python main.py` (looks for `test-input.csv`, falls back to `train-input.csv`;
optional arguments: `python main.py <input.csv> <output.json>`).
**Requires:** Python 3 standard library only.
