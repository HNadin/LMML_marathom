import json, re, unicodedata

d = json.load(open("canalqa_audit.json", encoding="utf-8"))
G = d["glossary_es_en"]
correct = {p["id"]: p["correct"] for p in d["model_predictions"]}

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))

# 1. вопрос -> (атрибут, объект)
pats = [r"^state the (.+?) of (.+?)\.?$",
        r"^what is the (.+?) of (.+?)\?$",
        r"^tell me the (.+?) of (.+?)\.?$",
        r"^which value is recorded as the (.+?) of (.+?)\?$",
        r"^according to the canal registry, what is the (.+?) of (.+?)\?$"]
def parse(q):
    for p in pats:
        m = re.match(p, q.strip(), re.I)
        if m: return norm(m.group(1)), norm(m.group(2))

# 2. только записи с вопросом-ответом
qa = [c["text"] for c in d["corpus"]
      if c["text"].startswith(("Canal operations log", "Registro del canal"))]

# 3. утечка: в записи есть и объект, и атрибут (для испанских - после перевода)
def translate(t):
    t = norm(t)
    for es, en in G.items():
        t = t.replace(norm(es), en)
    return t

leaked = []
for b in d["benchmark"]:
    attr, ent = parse(b["question"])
    for t in qa:
        nt, tt = norm(t), translate(t)
        if ent in nt and (attr in nt or attr in tt):
            leaked.append(b["id"]); break
print(len(leaked), leaked)

excluded = set(leaked)
remaining = [i for i in correct if i not in excluded]

honest = sum(correct[i] for i in remaining) / len(remaining)

report_data = {
    "excluded_ids": leaked,
    "honest_accuracy": honest
}

with open("report.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=1, ensure_ascii=False)
