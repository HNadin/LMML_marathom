"""Per question, brute-force every (tier, style, fewshot, context) combo, keep the cheapest one that passes quality."""
import itertools, json
import model_utils as mu

fb = mu.load_fact_bank()
config = {}
for qid, q in fb.items():
    best = None
    for tier, style, fs, ctx in itertools.product(mu.TIERS, mu.STYLES, (False, True), (False, True)):
        call = mu.build_call(q, tier, style, fs, ctx)
        if not mu.question_passes(q["slots"], call["answer"]):
            continue
        key = (call["tokens"], tier == "large", fs, ctx)
        if best is None or key < best[0]:
            best = (key, dict(tier=tier, style=style, fewshot=fs, context=ctx))
    config[qid] = best[1]
mu.save_json(config, mu.Path("routing_config.json"))
r = mu.run_config(config, fb)
print("total tokens:", r["total_tokens"], "quality:", r["quality_gate"], "budget:", r["budget_gate"])
