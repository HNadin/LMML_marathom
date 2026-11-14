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
