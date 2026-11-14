Task: The Gángan Never Lies

**Problem.** `challenge.wav` (16-bit PCM, mono, ~10 s, 22050 Hz) is labelled "test tone — ignore" and sounds like flat, buzzing noise. Find what the old sound engineer hid inside and submit it as the flag in the format `SIGMOID_<WORD>`. Scoring is all-or-nothing.

**Input:** `challenge.wav`. **Output:** the flag string.

**Approach.** The file is noise-like and nothing is stored in the bytes, so the message is hidden in the time-frequency plane, i.e. drawn into the spectrogram:

1. Check the header and run `strings` — nothing useful.
2. Check the sample LSBs — they decode to random bytes, so there is no LSB payload.
3. Take an FFT — the energy is concentrated in a band around 3–3.5 kHz, which hints at a drawn image.
4. Plot the spectrogram (`NFFT` 256–1024, grayscale colormap) — dark letters in that band read `TALKINGDRUM`.
5. Wrap the word in the required format.

**Run:** `python solve.py challenge.wav` writes `spectrogram.png`; open it and read the text near 3–3.5 kHz. Requires: Python 3, numpy, matplotlib.

If the text is hard to read, try other `NFFT` values (256, 512) or the `gray` colormap. In Audacity: switch the track view to Spectrogram and raise the upper frequency limit.
