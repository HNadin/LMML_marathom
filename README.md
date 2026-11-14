# LMML 2.0 — Solutions

Solutions for the LMML 2.0 machine-learning marathon (Sigmoid, 14–15 Nov 2026).
Each task lives in its own folder and is solved by a single `main.py` that reads
the platform's input file from the current working directory and writes the
output file next to it.

```
.
├── Mexico/           # Ruta de las Identidades  (NLP, Easy)
│   └── main.py
├── United States/    # The Great American Token Mystery  (NLP, Easy)
│   └── main.py
└── README.md
```

---

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

---

## Task: United States — *The Great American Token Mystery*

**Problem.** A tokenizer configuration was lost. Given a calibration pair
(`text` + the exact `token_ids` it produced) and an encoded challenge payload,
identify the tokenizer and decode the challenge message.

**Input:** `test-input.json` with `calibration.text`, `calibration.token_ids`,
`challenge.token_ids`.
**Output:** `test-output.json` — `{"tokenizer_id": "...", "decoded_message": "..."}`.

**Approach.**

1. Load every available candidate tokenizer: all tiktoken encodings first
   (`cl100k_base`, `o200k_base`, `p50k_base`, `r50k_base`, `p50k_edit`, `gpt2`, …),
   then, if `transformers` is installed, a few common Hugging Face tokenizers.
2. Encode `calibration.text` with each candidate and compare with
   `calibration.token_ids`. The first candidate that reproduces the IDs *exactly*
   is the missing tokenizer.
3. Decode `challenge.token_ids` with that tokenizer and write the result.

Useful hint: the very first calibration ID is `2`, which is `#` in `cl100k_base`,
and the text begins with `#`. Encoding the calibration text with `cl100k_base`
gives all 105 IDs exactly; the GPT-2/r50k/p50k encodings and `o200k_base` do not.

**Result.** Tokenizer: `cl100k_base`. The decoded message contains the flag.

**Run:** `python main.py` (reads `test-input.json` from the current directory;
optional arguments: `python main.py <input.json> <output.json>`; for local practice
run it on `train-input.json`, which should report `p50k_base`).
**Requires:** `pip install tiktoken` (it downloads the vocabulary files on first use,
so internet access is needed once). `transformers` is optional.

---

## Notes

- All scripts are deterministic and do not use any external data beyond the
  provided input files (and, for the tokenizer task, the public tiktoken vocabularies).
- Each script was first verified on the training sample (where one was provided)
  before being submitted.
