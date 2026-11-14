"""LMML Tokenizer Challenge.

1. Find the tokenizer whose encoding of calibration.text equals calibration.token_ids.
2. Decode challenge.token_ids with it.
Reads test-input.json (or the path in argv[1]) and writes test-output.json
into the same directory (or the path in argv[2]).
"""
import json
import os
import sys


def candidates():
    """Yield (tokenizer_id, encode_fn, decode_fn) for every tokenizer we can load."""
    # --- tiktoken family -------------------------------------------------
    try:
        import tiktoken
        names = list(tiktoken.list_encoding_names())
    except Exception:
        tiktoken, names = None, []
    # prefer the common ones first
    order = ["cl100k_base", "o200k_base", "p50k_base", "r50k_base", "p50k_edit", "gpt2"]
    names = [n for n in order if n in names] + [n for n in names if n not in order]
    for name in names:
        try:
            enc = tiktoken.get_encoding(name)
        except Exception:
            continue
        yield (name,
               lambda t, e=enc: e.encode(t, allowed_special="all"),
               lambda ids, e=enc: e.decode(ids))

    # --- Hugging Face tokenizers (only if installed and reachable) -------
    try:
        from transformers import AutoTokenizer
    except Exception:
        AutoTokenizer = None
    if AutoTokenizer is not None:
        for name in ["gpt2", "roberta-base", "bert-base-uncased", "bert-base-multilingual-cased",
                     "xlm-roberta-base", "t5-small", "facebook/opt-125m", "EleutherAI/gpt-neox-20b",
                     "meta-llama/Llama-2-7b-hf", "mistralai/Mistral-7B-v0.1"]:
            try:
                tok = AutoTokenizer.from_pretrained(name)
            except Exception:
                continue
            yield (name,
                   lambda t, k=tok: k.encode(t),
                   lambda ids, k=tok: k.decode(ids, skip_special_tokens=False))


def main(inp, out):
    with open(inp, encoding="utf-8") as f:
        data = json.load(f)
    text = data["calibration"]["text"]
    want = data["calibration"]["token_ids"]
    challenge = data["challenge"]["token_ids"]

    found = None
    for name, encode, decode in candidates():
        try:
            if list(encode(text)) == list(want):
                found = (name, decode)
                break
        except Exception:
            continue

    if found is None:
        raise SystemExit("no tokenizer reproduces the calibration token ids")

    name, decode = found
    result = {"tokenizer_id": name, "decoded_message": decode(challenge)}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "test-input.json"
    if len(sys.argv) > 2:
        out = sys.argv[2]
    else:
        base = os.path.basename(inp)
        name = base.replace("-input.json", "-output.json") if base.endswith("-input.json") else "test-output.json"
        out = os.path.join(os.path.dirname(os.path.abspath(inp)), name)
    main(inp, out)
