## Task: Senegal — *The Teranga FM Token Diet*

**Problem.** Teranga FM's helpline answers 20 fixed questions through an LLM gateway
that bills prompt and completion tokens alike. For each question we choose a `tier`
(cheap or large), a `style` (verbose or terse), whether to attach a `fewshot` block, and
whether to attach the question's `context` snippet. Every answer must contain all
required facts (no partial credit) and the total over all 20 answers must be ≤ 1200
tokens. The intern's config (everything large / verbose / few-shot) passes quality but
costs 3626 tokens.

**Input:** `dataset/fact_bank.json` (20 questions, required facts, context snippets).
**Output:** `routing_config.json` — one entry per question id; `main.py` turns it into `answers.json`:

    {"q01": {"tier": "cheap", "style": "terse", "fewshot": false, "context": false},
     "q04": {"tier": "large", "style": "terse", "fewshot": false, "context": false}}

**Approach.** Each question passes or fails on its own and tokens simply add up, so the
best total is the sum of each question's cheapest passing option. `optimize_routing.py`
tries all 16 combinations of tier × style × few-shot × context per question and keeps the
cheapest one that passes the quality check:

1. Style → `terse` everywhere (verbose intro, outro and instruction add tokens, no facts).
2. `fewshot` → `false` everywhere (pure prompt overhead).
3. No `large_only` fact slot → `cheap`, no context
   (q01, q03, q09, q11, q14, q15, q16, q19).
4. `large_only` slots and a short snippet → `cheap` + `context`; the snippet costs less
   than the large preamble (q02, q10, q13, q17, q18, q20).
5. `large_only` slots and a long snippet → `large`, no context; the snippet would cost
   more than the large preamble (q04, q05, q06, q07, q08, q12).
6. Ties → cheap, no few-shot, no context.

