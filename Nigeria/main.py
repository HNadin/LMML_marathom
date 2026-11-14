import wave, numpy as np
import matplotlib.pyplot as plt

w = wave.open("challenge.wav")
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)

plt.figure(figsize=(16, 5))
plt.specgram(x, NFFT=1024, Fs=22050, noverlap=768, cmap="gray_r")
plt.savefig("spec.png", dpi=100)
