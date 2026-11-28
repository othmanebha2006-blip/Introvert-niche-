"""v2 sound design: whoosh on every car entry/exit (from the compose2 timeline), revs, burnout,
plug-in click + zap, stamps, crown dings, keycap pops; lo-fi bed ducked under the voice."""
import os, wave
import numpy as np
import compose as C
import compose2 as V
from audio import SR, whoosh, pop, thud, ding, music, env, rng

HERE = os.path.dirname(os.path.abspath(__file__))


def rev(d=1.0, f0=70, f1=330):
    n = int(d * SR); t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (t / d) ** 0.7
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    y = np.zeros(n); s = 0
    for i in range(n):
        s += 0.12 * (saw[i] - s); y[i] = s
    y += 0.3 * np.sin(2 * np.pi * ph * 0.5)
    return y * np.minimum(1, t / 0.05) * np.exp(-np.maximum(0, t - d * 0.8) * 8) * 0.9


def screech(d=0.7):
    n = int(d * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * (1800 + 200 * np.sin(t * 40)) * t) * 0.25 + rng.normal(0, 1, n) * 0.35
    return y * np.minimum(1, t / 0.02) * np.exp(-t * 2.5) * 0.7


def zap(d=0.5):
    n = int(d * SR); t = np.arange(n) / SR
    y = np.sign(np.sin(2 * np.pi * (900 + 600 * np.sin(t * 60)) * t)) * rng.uniform(0.3, 1, n)
    return y * np.exp(-t * 6) * 0.25


def main():
    V.build()
    import subprocess
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'voiceover.mp3'), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    voice = np.frombuffer(raw, np.float32).astype(np.float64)
    dur = C.END + 0.3
    n = int(dur * SR)
    v = np.zeros(n); v[:min(n, len(voice))] = voice[:n]
    sfx = np.zeros(n)

    def add(snd, t, g=1.0):
        a = int(t * SR)
        if a < 0 or a >= n: return
        m = min(n - a, len(snd)); sfx[a:a + m] += snd[:m] * g

    at = C.at
    W1, W2 = whoosh(0.5), whoosh(0.4)
    for s in V.SEGS:
        if s['enter'] == 'left':
            add(W1, s['t_in'] - 0.05, 0.45)
        add(W2, s['t_out'] - 0.02, 0.35)
    add(W1, 0.0, 0.6)                       # logo fly-in
    add(whoosh(0.35), at('model') - 0.05, 0.4)  # zoom out to range
    add(whoosh(0.35), at('Lexus names'), 0.4)
    for i in range(10):
        add(pop(800 + 60 * i), at('model') + 0.1 + i * 0.035, 0.18)
    # beat pops (keycaps / meaning cards)
    for p in ['two letters', 'tell you', 'kind of car', 'saloons', 'smaller', 'sportier', 'comfortable', 'executive', 'luxury',
              'X', 'the end', 'urban', 'nimble', 'radiant', 'larger', 'rugged', 'off-roader', 'number', '350', 'roughly', 'engine size',
              'powertrain', 'performance', 'an h means', 'h plus', 'and e means', 'fully', 'hybrid SUV', 'look', 'feel', 'high-performance',
              'Fuji', 'Japan', 'L', 'luxury-focused', 'grand', 'coupe', 'legendary', 'supercar', 'nimble crossover', 'package']:
        try:
            add(pop(760 + (hash(p) % 5) * 90), at(p), 0.3)
        except KeyError:
            print('no word', p)
    add(pop(1100), at('plug-in hybrid', 2), 0.3)
    # number roll clicks
    for i in range(7):
        add(pop(1400), at('500', 1) + i * 0.07, 0.15)
    add(thud(), at('X', 1), 0.7)
    add(thud(), at('not a') + 0.1, 0.85)
    add(thud(), at('different'), 0.7)
    for w, k in [('flagship', 1), ('flagship', 2)]:
        add(ding(), at(w, k) + 0.4, 0.35)
    add(pop(500), at('plug-in') + 0.2, 0.5); add(zap(), at('plug-in') + 0.22, 0.6)
    add(screech(), at('RC F') - 0.5, 0.6)
    add(screech(0.6), at('And the LFA') - 0.1, 0.45)
    add(rev(1.0), at('V10') - 0.1, 0.7)
    add(rev(0.8, 60, 260), at('high-performance'), 0.45)
    add(ding(), at('and if you'), 0.4)

    mus = music(dur)
    frame = SR // 50
    m_env = np.array([np.sqrt(np.mean(v[i:i + frame] ** 2)) for i in range(0, n, frame)])
    vad = np.convolve((20 * np.log10(m_env + 1e-6) > -38).astype(float), np.ones(10) / 10, 'same')
    duck = np.repeat(1 - 0.55 * vad, frame)[:n]
    mus = mus / (np.abs(mus).max() + 1e-9) * 0.12 * duck
    sfx = sfx / max(1, np.abs(sfx).max()) * 0.55
    mix = v / (np.abs(v).max() + 1e-9) * 0.9 + sfx + mus
    mix = mix / max(1.0, np.abs(mix).max() / 0.98)
    st = np.stack([mix + mus * 0.15, mix - mus * 0.15], 1)
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(os.path.join(HERE, 'build', 'mix2.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print('mix2 written')


if __name__ == '__main__':
    main()
