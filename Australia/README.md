# The Drunken Mario Adventures

**Flag:** `SIGMOID_TANH`

## Finding

Marathon Lab evolves Mario agents live. A fully trained agent runs the level, collects some of its **20 coins** and deliberately skips the rest. Read left to right along the level, collected = `1` and skipped = `0` give 20 bits. Each group of 5 bits is a letter (A=1 … Z=26):

| Coins | Bits | Number | Letter |
|---|---|---|---|
| 1–5 | `10100` | 20 | T |
| 6–10 | `00001` | 1 | A |
| 11–15 | `01110` | 14 | N |
| 16–20 | `01000` | 8 | H |

`TANH` is the answer, so the flag is `SIGMOID_TANH`. Per-coin data is in `mario_coins_table.xlsx`.

## Method

Input: a screen recording of generation 535 in `BEST ONLY` mode, which ends at the flagpole.

1. Detect coins by colour
2. A coin that vanishes next to Mario was collected. A coin that leaves through the left edge, or is still on screen when the run ends, was skipped.
3. Sort by world x, then map to bits, 5-bit groups and letters.


