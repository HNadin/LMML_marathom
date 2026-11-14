import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations

ABBR = {
    "int": "interior", "av": "avenida", "priv": "privada", "cor": "corredor",
    "blvd": "boulevard", "ret": "retorno", "and": "andador", "peat": "peatonal",
    "cjon": "callejon", "c": "calle",
}


def strip_accents(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


def addr_key(address):
    """Order-independent canonical key: the same address can be written with
    the street number before or after the street name, with abbreviations,
    accents or odd spacing."""
    s = strip_accents(address or "").replace(".", "")
    s = re.sub(r"[^a-z0-9\- ]", " ", s)
    return " ".join(sorted(ABBR.get(t, t) for t in s.split()))


def name_tokens(first, last):
    toks = strip_accents(f"{first} {last}")
    return re.sub(r"[^a-z ]", " ", toks).split()


def name_sim(a, b):
    """Fuzzy, order-insensitive name similarity (used only as a fallback)."""
    ta, tb = sorted(name_tokens(*a)), sorted(name_tokens(*b))
    return SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()


def main(inp, out):
    with open(inp, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    groups = defaultdict(list)
    for r in rows:
        groups[addr_key(r["address"])].append(r)

    matches = []
    for recs in groups.values():
        if len(recs) < 2:
            continue
        tables = [r["source_table"] for r in recs]
        ambiguous = len(set(tables)) < len(tables)
        for a, b in combinations(recs, 2):
            if a["source_table"] == b["source_table"]:
                continue
            if ambiguous and name_sim((a["first_name"], a["last_name"]),
                                      (b["first_name"], b["last_name"])) < 0.6:
                continue
            matches.append([a["record_id"], b["record_id"]])

    with open(out, "w", encoding="utf-8") as f:
        json.dump({"matches": matches}, f, ensure_ascii=False)


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "train-input.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "output.json"
    main(inp, out)
