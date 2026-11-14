"""Walu Season: starter main.py (the greedy baseline).

This file already speaks the evaluator's protocol. The part to change is the
Strategy class. As shipped it is pure greedy: try every spot once, then keep
going back to whichever spot has the best average so far. It runs end to end
and it does NOT reach the threshold.

Check it locally on the practice reef:

    python evaluation_script.py main.py --dataset train

Rules of the protocol (see task_description.md):
  * read test-input.json from the current directory (bare filename),
  * for every cast print one spot number on stdout, then read one line from
    stdin with the catch in kg,
  * start a fresh Strategy every day (spot numbers are reshuffled daily),
  * anything else you want to print goes to stderr.
"""

import json
import sys


class Strategy:
    def __init__(self, n_spots, n_casts):
        self.n_spots = n_spots
        self.n_casts = n_casts
        self.casts = [0] * n_spots      # how many times each spot was fished
        self.total = [0.0] * n_spots    # kg caught at each spot
        self.current_cast = 0

        # Explore each spot 30 times (300 total exploration casts).
        # This is robust enough to hit the high-yield school spot multiple times,
        # ensuring its empirical average cleanly beats the steady spots.
        self.explore_limit = min(30, max(1, n_casts // (3 * n_spots)))

    def choose(self):
        # 1. Exploration phase: round-robin across all spots
        if self.current_cast < self.n_spots * self.explore_limit:
            spot = self.current_cast % self.n_spots

        # 2. Exploitation phase: exclusively play the highest average spot
        else:
            averages = [self.total[s] / max(1, self.casts[s]) for s in range(self.n_spots)]
            spot = max(range(self.n_spots), key=lambda s: averages[s])

        self.current_cast += 1
        return spot

    def update(self, spot, catch):
        self.casts[spot] += 1
        self.total[spot] += catch


def main():
    with open("test-input.json") as f:
        rules = json.load(f)

    for _day in range(rules["n_days"]):
        agent = Strategy(rules["n_spots"], rules["n_casts"])
        for _cast in range(rules["n_casts"]):
            spot = agent.choose()
            print(spot, flush=True)
            catch = float(sys.stdin.readline())
            agent.update(spot, catch)


if __name__ == "__main__":
    main()
