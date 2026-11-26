"""Sound design: synthesized SFX on the visual beats + a quiet lo-fi bed ducked under the voice.
Writes build/mix.wav (48 kHz stereo); final loudness is set to -14 LUFS in the mux step."""
import os, subprocess, json
import numpy as np
import compose as C

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(1)


def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)


def whoosh(d=0.45):
    n = int(d * SR)
    x = rng.normal(0, 1, n)
    # sweep a one-pole low-pass up then down
    t = np.linspace(0, 1, n)
    cut = 0.02 + 0.25 * np.sin(np.pi * t) ** 2
    y = np.zeros(n); s = 0
    for i in range(n):
        s += cut[i] * (x[i] - s); y[i] = s
    return y * np.sin(np.pi * t) ** 1.5 * 0.9


def pop(f0=900):
    n = int(0.09 * SR); t = np.arange(n) / SR
    f = f0 * np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.03) * 0.7


def click():
    n = int(0.03 * SR)
    return rng.normal(0, 1, n) * env(n, 0.0005, 0.006) * 0.5


def thud():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 120 * np.exp(-t * 10) + 45
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.12)
    return (body + rng.normal(0, 1, n) * env(n, 0.001, 0.02) * 0.6) * 0.9


def ding():
    n = int(1.2 * SR); t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy) for f, a, dcy in [(1318, .5, 3), (2637, .25, 5), (3951, .12, 7), (1975, .2, 4)])
    return y * np.minimum(1, t / 0.003) * 0.6


def music(dur):
    bpm = 92; beat = 60 / bpm
    n = int(dur * SR); out = np.zeros(n)
    t = np.arange(n) / SR
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 329.6]]
    bar = beat * 4
    for b in range(int(dur / bar) + 1):
        ch = chords[b % 4]
        s0 = int(b * bar * SR); s1 = min(n, int((b + 1) * bar * SR))
        if s0 >= n: break
        tt = (np.arange(s1 - s0)) / SR
        pad = sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt) for f in ch) / len(ch)
        pad *= (1 - np.exp(-tt * 6)) * np.exp(-tt * 0.35)
        out[s0:s1] += pad * 0.35
        # bass
        bf = ch[0] / 2
        for k in (0, 2.5):
            a = int((b * bar + k * beat) * SR)
            m = min(n - a, int(beat * 1.2 * SR))
            if m > 0:
                tb = np.arange(m) / SR
                out[a:a + m] += np.sin(2 * np.pi * bf * tb) * np.exp(-tb * 3) * 0.45
    for k in range(int(dur / beat) + 1):
        a = int(k * beat * SR)
        if a >= n: break
        if k % 2 == 0:  # kick
            m = min(n - a, int(0.25 * SR)); tb = np.arange(m) / SR
            out[a:a + m] += np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-tb * 30)) / SR) * np.exp(-tb * 14) * 0.8
        else:  # snare-ish
            m = min(n - a, int(0.18 * SR))
            out[a:a + m] += rng.normal(0, 1, m) * np.exp(-np.arange(m) / SR * 25) * 0.18
        for h in (0, 0.5):  # hats
            a2 = int((k + h) * beat * SR)
            m = min(n - a2, int(0.04 * SR))
            if m > 0:
                hs = rng.normal(0, 1, m); hs = np.diff(np.concatenate([[0], hs]))
                out[a2:a2 + m] += hs * np.exp(-np.arange(m) / SR * 120) * 0.08
    return out


def main():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'voiceover.mp3'), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
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
    W1 = whoosh()
    car_entries = ['IS and ES', 'the IS is', 'while the ES', 'LS is the', 'UX is', 'NX is', 'RX is', 'GX is', 'and LX is',
                   'so an RX', "then there's F", 'while the LC', 'And the LFA', 'So an NX', 'LS and']
    for p in car_entries:
        add(W1, at(p) - 0.15, 0.55)
    add(W1, at('ES') - 0.1, 0.4)
    add(whoosh(0.35), at('RC F') - 0.3, 0.8)
    for i in range(5):
        add(whoosh(0.3), at('SUV', 1) - 0.3 + i * 0.07, 0.25)
    pops = ['explained', 'two letters', 'kind of car', 'saloons', 'smaller', 'sportier', 'comfortable', 'executive', 'X', 'the end',
            'urban', 'nimble', 'radiant', 'larger', 'rugged', 'off-roader', '350', '500', 'roughly', 'engine size', 'powertrain', 'performance',
            'an h means', 'h plus', 'and e means', '500h', 'hybrid SUV', 'look', 'high-performance', 'Fuji', 'Speedway', 'Japan',
            'L', 'luxury-focused', 'grand', 'coupe', 'long journeys', 'legendary', 'supercar', 'nimble crossover', 'package']
    for i, p in enumerate(pops):
        try:
            add(pop(700 + 140 * (i % 4)), at(p), 0.35)
        except KeyError:
            print('no word', p)
    add(pop(1100), at('plug-in hybrid', 2), 0.35)
    add(thud(), at('not a'), 0.8); add(thud(), at('different'), 0.7)
    add(ding(), at('flagship'), 0.35); add(ding(), at('flagship', 2), 0.35); add(ding(), at('V10'), 0.3)
    add(ding(), at('and if you'), 0.4)
    for k in range(int(dur * 2)):
        pass
    mus = music(dur)
    # duck music under the voice
    frame = SR // 50
    m_env = np.array([np.sqrt(np.mean(v[i:i + frame] ** 2)) for i in range(0, n, frame)])
    vad = (20 * np.log10(m_env + 1e-6) > -38).astype(float)
    k = np.ones(10) / 10
    vad = np.convolve(vad, k, 'same')
    duck = np.repeat(1 - 0.55 * vad, frame)[:n]
    mus = mus / (np.abs(mus).max() + 1e-9) * 0.12 * duck
    sfx = sfx / max(1, np.abs(sfx).max()) * 0.5
    vv = v / (np.abs(v).max() + 1e-9) * 0.9
    mix = vv + sfx + mus
    mix = mix / max(1.0, np.abs(mix).max() / 0.98)
    st = np.stack([mix, mix], 1)
    # slight stereo width on music
    st[:, 0] += mus * 0.15; st[:, 1] -= mus * 0.15
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    import wave
    with wave.open(os.path.join(HERE, 'build', 'mix.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print('mix written', dur)


if __name__ == '__main__':
    main()
