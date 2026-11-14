import json, re, unicodedata

d = json.load(open("canalqa_audit.json", encoding="utf-8"))
G = d["glossary_es_en"]
correct = {p["id"]: p["correct"] for p in d["model_predictions"]}

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))

pats = [r"^state the (.+?) of (.+?)\.?$",
        r"^what is the (.+?) of (.+?)\?$",
        r"^tell me the (.+?) of (.+?)\.?$",
        r"^which value is recorded as the (.+?) of (.+?)\?$",
        r"^according to the canal registry, what is the (.+?) of (.+?)\?$"]
def parse(q):
    for p in pats:
        m = re.match(p, q.strip(), re.I)
        if m: return norm(m.group(1)), norm(m.group(2))

qa = [c["text"] for c in d["corpus"]
      if c["text"].startswith(("Canal operations log", "Registro del canal"))]

def translate_and_normalize(t):
    t = norm(t)
    for es, en in sorted(G.items(), key=lambda item: len(item[0]), reverse=True):
        t = t.replace(norm(es), en)

    # Нормализуем испанские десятичные дроби
    t = re.sub(r'(\d+),(\d+)', r'\1.\2', t)
    return t

leaked = []
for b in d["benchmark"]:
    attr, ent = parse(b["question"])
    gold = norm(b["gold"])

    # Регулярки с границами слов (\b), чтобы "panamax" не находил "neopanamax"
    ent_pattern = r'\b' + re.escape(ent) + r'\b'
    attr_pattern = r'\b' + re.escape(attr) + r'\b'
    gold_pattern = r'\b' + re.escape(gold) + r'\b'

    for t in qa:
        nt = norm(t)
        tt = translate_and_normalize(t)

        if re.search(ent_pattern, nt):
            if (re.search(attr_pattern, nt) or
                    re.search(attr_pattern, tt) or
                    re.search(gold_pattern, nt) or
                    re.search(gold_pattern, tt)):
                leaked.append(b["id"])
                break

excluded = set(leaked)
remaining = [i for i in correct if i not in excluded]

honest = sum(correct[i] for i in remaining) / len(remaining)

report_data = {
    "excluded_ids": leaked,
    "honest_accuracy": honest
}

with open("report.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=1, ensure_ascii=False)
