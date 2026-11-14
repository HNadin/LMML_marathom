## Task: Fiji — *Walu Season*

**Problem.** You are given 10 fishing spots (arms) with unknown, noisy, and highly varied catch distributions. Each day you have 1,000 casts, and spot numbers are reshuffled daily. The goal is to maximize the daily catch, averaging at least 5,300 kg per day over 100 days. A basic greedy strategy fails because rare but massive "schools" of fish can easily be missed with only 1 or 2 exploration casts.

**Input:** `test-input.json` containing `n_spots`, `n_casts`, and `n_days`.
**Output:** An interactive script (`main.py`) that prints the chosen spot (0–9) to `stdout` and reads the resulting catch (float) from `stdin` for each cast.

**Approach.** This is a classic Multi-Armed Bandit problem. Since the total number of pulls (1,000) is known and fixed, the most robust and mathematically sound approach is the **Explore-Then-Commit (ETC)** strategy:

1. **Exploration Phase:** The highest-yielding "school" spots have a low probability of hitting the jackpot on any single cast (e.g., 35% chance for ~20 kg). To guarantee finding it, the algorithm dedicates the first 300 casts to round-robin exploration (exactly 30 casts per spot). The probability of missing a 35% event in 30 pulls is mathematically negligible ($0.65^{30} \approx 0.0002\%$).
2. **Exploitation Phase:** For the remaining 700 casts, the algorithm simply identifies the spot with the highest empirical average from the exploration phase and fishes there exclusively.

**Result.** The strategy comfortably averages ~5,900+ kg per day on the evaluation reef, well above the 5,300 kg passing threshold. Passed on the platform.

**Run:** `python evaluation_script.py main.py --dataset train` (runs the script against the practice simulator).
**Requires:** Python 3 standard library only.