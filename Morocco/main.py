"""Dispatch Desk router: reads test-input.csv, writes routing_log.csv.

Standard library only. Each request is routed from its text alone, using what
the training data showed about where each guide succeeds or fails per
request type.
"""
import csv
import heapq
import re

CHEAP, EXP = "cheap", "expensive"


def walk_is_indirect(p):
    """True when the shortest walk is a detour (both guides fail on those)."""
    edges = re.findall(r"([A-Za-z]+)-([A-Za-z]+) (\d+) minutes", p)
    q = re.search(r"from ([A-Za-z]+) to ([A-Za-z]+)", p)
    if not edges or not q:
        return None
    src, dst = q.group(1), q.group(2)
    g = {}
    direct = None
    for a, b, w in edges:
        w = int(w)
        g.setdefault(a, []).append((b, w))
        g.setdefault(b, []).append((a, w))
        if {a, b} == {src, dst}:
            direct = w
    dist = {src: 0}
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, 1e9):
            continue
        for v, w in g.get(u, []):
            if d + w < dist.get(v, 1e9):
                dist[v] = d + w
                heapq.heappush(heap, (d + w, v))
    if dst not in dist or direct is None:
        return None
    return dist[dst] < direct


def route(p):
    if "shortest walk" in p:
        ind = walk_is_indirect(p)
        if ind is True:
            return CHEAP          # detour answers: both guides get them wrong
        return EXP
    if "board lists" in p:
        return EXP if "whatever" in p else CHEAP
    if "loads" in p and "crates" in p:
        if "sells" in p:
            return EXP            # multi-step arithmetic: apprentice fails
        m = re.search(r"loads (\d+) crates .*? with (\d+)", p)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a * b <= 54:
                return CHEAP
            if a >= 9 and b >= 9 and a * b <= 170 and not (a == 9 and b == 12):
                return CHEAP
            if b >= 10 and a * b <= 170:
                return CHEAP
            if a * b <= 134 and a <= 14:
                return CHEAP
        return EXP
    if "stall fee" in p and "keeps the least" in p:
        return CHEAP
    return EXP


def main():
    with open("test-input.csv", "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    with open("routing_log.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["request_id", "model"])
        for r in rows:
            try:
                m = route(r["prompt"])
            except Exception:
                m = EXP
            w.writerow([r["request_id"], m])


if __name__ == "__main__":
    main()
