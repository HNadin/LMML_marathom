## Task: Morocco — *The Dispatch Desk of Fez*

**Problem.** Every request goes to exactly one of two language models: the cheap
apprentice (Qwen2.5-0.5B, 1 dirham) or the expensive master guide (Qwen2.5-7B,
25 dirham). The choice is made from the request text alone, before either guide
sees it. On the 500 hidden requests the routing log must reach quality ≥ 0.80
and cost ≤ 10,000 dirham at the same time.

**Input:** `test-input.csv` with columns `request_id, prompt`.
**Output:** `routing_log.csv` — one row per request, `model` is `cheap` or `expensive`:

    request_id,model
    test_0001,cheap
    test_0002,expensive

**Approach.** The training data showed that the requests come from a handful of
templates, and that the two guides fail in very different places on each one.
The router matches the template and applies a rule:

1. Price lookup, plain → `cheap` (apprentice is almost always right).
   With "whatever X's stall sells" → `expensive` (indirection breaks the apprentice).
2. Crates, "how many in total" → `cheap` when the product is small or the factors
   are moderate, otherwise `expensive`. With sales and apprentices (multi-step) → `expensive`.
3. Shortest walk: parse the edges, run Dijkstra, compare with the direct edge.
   If a detour is shorter → `cheap` (both guides were wrong on every such case, so
   the master adds nothing). If the direct route is shortest → `expensive`.
4. Stall closing time, toll totals, takings → `expensive` (apprentice is nearly always wrong).
5. Stall fee: "keeps the least" → `cheap` (master is barely better);
   "keeps the most" → `expensive`.
6. Anything unrecognised, unparsable, or raising an error → `expensive`
   (costs money, never accuracy).

**Result.** On the 400 training requests: quality 0.8375 (gate ≥ 0.80) and cost
7,168 (gate ≤ 8,000, i.e. 20 dirham per request). 282 of the 400 requests go to the
master guide; the other 118 go to the apprentice. The hidden set has a slightly
different mix, so the margins are about 3.75 quality points and about 10% on cost.

**Run:** `python main.py` (reads `test-input.csv` from the working folder and writes
`routing_log.csv` there). To check locally, copy `train-input.csv` to `test-input.csv` first.
**Requires:** Python 3 standard library only.
