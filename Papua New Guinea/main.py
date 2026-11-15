"""Submission template for task_papua_new_guinea (Bihainim Angkol).

Reads test-input.csv (row,col,hold,steps_left) from the current directory and
writes test-output.csv (row,col,hold,steps_left,action) next to it, with one
action for every state.

As shipped, the canoe never leaves the beach, so it lands no fish. Replace
choose_action with your agent. main.py runs alone, next to test-input.csv only:
it cannot import lagoon.py or read the logbook, so your policy has to be inside
this file. lagoon.export_main(policy) writes a complete main.py from any
{state: action} dict or function.
"""

import csv

ACTIONS = ("NORTH", "SOUTH", "EAST", "WEST", "FISH", "WAIT")


def choose_action(row, col, hold, steps_left):
    """Your agent: the action to take in this state."""
    return "WAIT"


def main():
    with open("test-input.csv", newline="") as src, open("test-output.csv", "w", newline="") as dst:
        out = csv.writer(dst)
        out.writerow(["row", "col", "hold", "steps_left", "action"])
        for rec in csv.DictReader(src):
            state = (int(rec["row"]), int(rec["col"]), int(rec["hold"]), int(rec["steps_left"]))
            action = choose_action(*state)
            if action not in ACTIONS:
                raise ValueError(f"unknown action {action!r} for state {state}")
            out.writerow([*state, action])


if __name__ == "__main__":
    main()
