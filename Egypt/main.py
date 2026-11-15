"""Always Valid, No Excuses: OCR 'key: value | key: value' cards -> strict JSON lines.

Design
------
* The final output is ALWAYS produced by a strict rule-based converter
  (parse_record). The task rules are fully deterministic, so a 1.7B model
  must never be the thing that decides whether a card is valid.
* The local Qwen3-1.7B oracle (grammar-constrained to emit JSON, temperature 0)
  converts the same cleaned fields, and its answer is cross-checked against the
  rule-based result. If it ever disagrees, the rule-based result wins.
  The oracle only runs inside a time budget so the 60 s limit is never at risk.
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "test-input.txt")
OUT_PATH = os.path.join(HERE, "test-output.txt")
MODEL_PATH = os.path.join(HERE, "models", "Qwen3-1.7B-Q8_0.gguf")

USE_ORACLE = True
ORACLE_BUDGET_S = 35.0  # stop consulting the model after this many seconds in total

KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
INT_RE = re.compile(r"-?[0-9]+")


def extract_fields(line):
    """Return [(key, trimmed_value_string), ...]; scan noise is dropped."""
    fields = []
    for seg in line.split("|"):
        if ":" not in seg:
            continue  # page numbers, chapters, footers, [torn], ###, ...
        key, value = seg.split(":", 1)  # only the FIRST colon separates
        key = key.strip()
        if not KEY_RE.fullmatch(key):
            continue  # not a simple word key -> noise
        fields.append((key, value.strip()))
    return fields


def convert_value(v):
    if v == "":
        return None
    if v == "true":
        return True
    if v == "false":
        return False
    if INT_RE.fullmatch(v):
        return int(v)
    return v


def parse_record(line):
    obj = {}
    for k, v in extract_fields(line):
        obj[k] = convert_value(v)  # duplicate key: last one wins
    return obj


def dump(obj):
    # ensure_ascii=True keeps every output strictly on one physical line
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":"))


def canon(obj):
    # json.dumps distinguishes true from 1, which Python's == does not
    return json.dumps(obj, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


SYSTEM = (
    "You turn cleaned record fields into ONE line of strictly valid JSON. "
    "Keep every field, in order, and add nothing. Typing rules: "
    "empty value -> null; exactly true/false -> JSON boolean; "
    "a whole number such as 40, 0 or -3 -> JSON number; "
    "anything else -> JSON string with \" and \\ escaped. "
    "Never turn a string into a number or the other way round."
)


def load_oracle():
    if not USE_ORACLE or not os.path.exists(MODEL_PATH):
        return None, None
    try:
        from llama_cpp import Llama, LlamaGrammar

        llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=-1,
            n_ctx=2048,
            verbose=False,
        )
        grammar = LlamaGrammar.from_json_schema('{"type":"object"}')
        return llm, grammar
    except Exception as e:  # never let the oracle break the deliverable
        print(f"[oracle disabled] {e!r}", file=sys.stderr)
        return None, None


def ask_oracle(llm, grammar, fields):
    listing = "\n".join(f"{k}: {v}" for k, v in fields) or "(no fields)"
    res = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": listing + "\n/no_think"},
        ],
        grammar=grammar,
        temperature=0.0,
        max_tokens=512,
    )
    return res["choices"][0]["message"]["content"].strip()


def main():
    t0 = time.time()
    with open(IN_PATH, "r", encoding="utf-8-sig", newline="") as f:
        text = f.read()
    lines = text.split("\n")  # not splitlines(): keep line N <-> line N exactly
    if lines and lines[-1] == "":
        lines.pop()
    lines = [ln.rstrip("\r") for ln in lines]

    llm, grammar = load_oracle()
    checked = agreed = 0
    out_lines = []

    for ln in lines:
        expected = parse_record(ln)
        if llm is not None and (time.time() - t0) < ORACLE_BUDGET_S and expected:
            try:
                got = json.loads(ask_oracle(llm, grammar, extract_fields(ln)))
                checked += 1
                agreed += canon(got) == canon(expected)
            except Exception:
                checked += 1
        out_lines.append(dump(expected))  # rule-based result is what we ship

    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out_lines) + ("\n" if out_lines else ""))

    print(
        f"{len(out_lines)} records written in {time.time() - t0:.1f}s; "
        f"oracle agreed on {agreed}/{checked} cross-checked",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
