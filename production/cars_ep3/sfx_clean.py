"""Clean sound palette (rule, 27 Nov 2026): no noise-based sounds.
Every effect is built from smooth sine tones with soft fades, so nothing hisses or crackles over the voice.
The function names are the same as in audio.py / audio2.py, so they drop in as replacements."""
import numpy as np

SR = 48000


def _fade(y, a=0.01, r=0.08):
    n = len(y)
    ai, ri = max(1, int(a * SR)), max(1, int(r * SR))
    env = np.ones(n)
    env[:ai] = np.sin(np.linspace(0, np.pi / 2, ai)) ** 2
    env[-ri:] *= np.cos(np.linspace(0, np.pi / 2, ri)) ** 2
    return y * env


def _tone(freqs, d):
    t = np.arange(int(d * SR)) / SR
    f = np.interp(t, np.linspace(0, d, len(freqs)), freqs)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def whoosh(d=0.45):
    """Soft 'swish': a low, gliding tone with a bell-shaped swell (no noise)."""
    t = np.linspace(0, 1, int(d * SR))
    y = 0.6 * _tone([180, 420, 260], d) + 0.3 * _tone([360, 840, 520], d)
    return _fade(y * np.sin(np.pi * t) ** 2, 0.02, 0.1) * 0.5


def pop(f0=900):
    """Gentle 'blip': short sine with a quick downward glide."""
    d = 0.11
    f0 = min(f0, 900) * 0.8
    y = _tone([f0, f0 * 0.7], d)
    t = np.arange(len(y)) / SR
    return _fade(y * np.exp(-t * 28), 0.004, 0.04) * 0.55


def thud():
    """Clean low 'boom' for stamps: pure sine drop, no click."""
    d = 0.35
    y = _tone([140, 55], d)
    t = np.arange(len(y)) / SR
    return _fade(y * np.exp(-t * 9), 0.004, 0.1) * 0.8


def ding():
    d = 1.0
    t = np.arange(int(d * SR)) / SR
    y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, a, k in [(880, .5, 4), (1320, .2, 6), (1760, .08, 8)])
    return _fade(y, 0.005, 0.2) * 0.45


def rev(d=1.0, f0=70, f1=330):
    """Smooth engine rise: a few sine harmonics, no sawtooth buzz."""
    t = np.linspace(0, 1, int(d * SR))
    f = f0 + (f1 - f0) * t ** 0.7
    ph = np.cumsum(f) / SR
    y = np.sin(2 * np.pi * ph) + 0.35 * np.sin(4 * np.pi * ph) + 0.15 * np.sin(6 * np.pi * ph)
    return _fade(y, 0.05, 0.25) * 0.35


def screech(d=0.6):
    """Replaced by a soft rising swish (tyre squeal was pure noise)."""
    return whoosh(d) * 0.8


def zap(d=0.4):
    """Charging 'shimmer': two soft rising sines instead of buzzing noise."""
    y = 0.5 * _tone([600, 1200], d) + 0.3 * _tone([900, 1800], d)
    t = np.linspace(0, 1, len(y))
    return _fade(y * (1 - t), 0.01, 0.1) * 0.25


def music(dur):
    """Warm bass-led bed: soft pad + sine bass + gentle sine kick. No hi-hats, no noise snare."""
    bpm = 92
    beat = 60 / bpm
    n = int(dur * SR)
    out = np.zeros(n)
    chords = [[261.6, 329.6, 392.0], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7]]
    bar = beat * 4
    for b in range(int(dur / bar) + 1):
        ch = chords[b % 4]
        s0 = int(b * bar * SR)
        s1 = min(n, int((b + 1) * bar * SR))
        if s0 >= n:
            break
        tt = np.arange(s1 - s0) / SR
        pad = sum(np.sin(2 * np.pi * f * tt) for f in ch) / len(ch)
        out[s0:s1] += pad * (1 - np.exp(-tt * 4)) * np.exp(-tt * 0.25) * 0.28
        for k in (0, 2):
            a = int((b * bar + k * beat) * SR)
            m = min(n - a, int(beat * 1.6 * SR))
            if m > 0:
                tb = np.arange(m) / SR
                out[a:a + m] += np.sin(2 * np.pi * ch[0] / 2 * tb) * np.exp(-tb * 1.8) * 0.5
    for k in range(0, int(dur / beat) + 1, 2):
        a = int(k * beat * SR)
        if a >= n:
            break
        m = min(n - a, int(0.3 * SR))
        tb = np.arange(m) / SR
        out[a:a + m] += np.sin(2 * np.pi * np.cumsum(50 + 60 * np.exp(-tb * 25)) / SR) * np.exp(-tb * 10) * 0.6
    return out
