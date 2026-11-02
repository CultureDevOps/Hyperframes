#!/usr/bin/env python3
"""Original deterministic 10-second soundtrack synchronized to the intro storyboard.

Only generated oscillators/noise: no copyrighted or external audio. No network.
"""
import math
import random
import struct
import sys
import wave

RATE = 22050
SECONDS = 10
SAMPLES = RATE * SECONDS
audio = [0.0] * SAMPLES
rng = random.Random(17)

def tone(start, duration, frequency, volume=0.2, kind="sine", sweep=0.0):
    first = int(round(start * RATE))
    count = min(int(duration * RATE), SAMPLES - first)
    for j in range(max(0, count)):
        t = j / RATE
        phase = 2 * math.pi * (frequency * t + sweep * t * t / (2 * duration))
        sample = math.sin(phase)
        if kind == "square":
            sample = math.tanh(sample * 3.5)
        elif kind == "noise":
            sample = rng.uniform(-1, 1)
        envelope = max(0, min(1, t / 0.022, (duration - t) / 0.08))
        audio[first + j] += volume * sample * envelope

# 0.3–2.4 s: comic confidence, quiet pulses and enough room to read the hook.
for k in range(10):
    start = 0.35 + k * 0.50
    tone(start, 0.15, 92 + k * 9, 0.09 + k * 0.007, "square")
    tone(start, 0.06, 500 + k * 35, 0.035)

# 2.6–5.1 s: escalating test/deploy glitches.
for t in (2.60, 3.35, 4.10, 4.75):
    tone(t, 0.24, 920, 0.18, "square", -390)
    tone(t + 0.05, 0.11, 170, 0.11, "noise")

# 5.5–6.95 s: fast alternating siren; leave an intentional silence before impact.
for k in range(8):
    tone(5.35 + k * 0.20, 0.16, 570 if k % 2 == 0 else 780, 0.24, "square")

# 7.18 s: comic smash and short triumphant sting; aligned with white flash/payoff.
tone(7.18, 0.63, 80, 0.53, "noise")
tone(7.18, 0.82, 72, 0.57, "sine", -40)
for i, note in enumerate((392, 494, 587, 784)):
    tone(7.36 + i * 0.22, 0.32, note, 0.19, "square")

# 8.9–10 s: falling rollback trombone, decaying cleanly at the end.
for i, note in enumerate((330, 294, 247, 165)):
    tone(8.77 + i * 0.26, 0.29, note, 0.19, "square", -30)

peak = max(1.0, max(abs(v) for v in audio))
target = sys.argv[1] if len(sys.argv) > 1 else "soundtrack.wav"
with wave.open(target, "wb") as output:
    output.setnchannels(1)
    output.setsampwidth(2)
    output.setframerate(RATE)
    for offset in range(0, SAMPLES, 4096):
        values = []
        for index in range(offset, min(SAMPLES, offset + 4096)):
            fade = min(1.0, (SAMPLES - index - 1) / (RATE * 0.14))
            sample = max(-1.0, min(1.0, audio[index] / peak * 0.84 * fade))
            values.append(struct.pack("<h", round(sample * 32767)))
        output.writeframes(b"".join(values))
