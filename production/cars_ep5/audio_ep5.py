"""Ep2 sound design (same palette as ep1 v2) keyed to the AMG timeline."""
import os, wave, subprocess
import numpy as np
import compose as C
import compose_ep5 as A
from compose2 import SEGS
from audio import SR, whoosh, pop, thud, ding, music
from audio2 import rev, screech, zap

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    A.build()
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'voiceover.mp3'), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    voice = np.frombuffer(raw, np.float32).astype(np.float64)
    dur = C.END + 0.3; n = int(dur * SR)
    v = np.zeros(n); v[:min(n, len(voice))] = voice[:n]
    sfx = np.zeros(n)

    def add(snd, t, g=1.0):
        a = int(t * SR)
        if 0 <= a < n:
            m = min(n - a, len(snd)); sfx[a:a + m] += snd[:m] * g
    ph = A.ph
    for s in SEGS:
        if s['enter'] == 'left':
            add(whoosh(0.5), s['t_in'] - 0.05, 0.45)
        add(whoosh(0.4), s['t_out'] - 0.02, 0.35)
        for ts_, _ in s.get('swaps', []):
            add(thud(), ts_, 0.5); add(rev(0.6, 70, 280), ts_, 0.45)
    add(whoosh(0.5), 0.0, 0.6)
    add(whoosh(0.35), ph('model') + 0.1, 0.4)
    for i in range(14):
        add(pop(800 + 45 * i), ph('model') + 0.25 + i * 0.03, 0.16)
    for i in range(5):
        add(pop(700 + 100 * i), ph('letters') + i * 0.12, 0.22)
    for p in ['lineup', 'the A Class', 'while the B', 'taller', 'move up', 'the E Class', 'and the S Class', 'put GL', 'the GLA', 'GLB', 'GLC',
              'GLE', 'GLS', 'the GLA is', 'top of', 'closer to', 'the G Class', 'G Wagon', 'CL', 'coupe', 'four-door', 'replaces',
              'convertibles', 'the SL', 'roadster', 'entry-level', 'flagship saloon', 'an SUV', 'a coupe', 'a sports']:
        add(pop(760 + (hash(p) % 5) * 90), ph(p), 0.3)
    for i in range(5):
        add(pop(800 + 90 * i), ph('size order') - 0.2 + i * 0.2, 0.25)
    add(ding(), ph('flagship') + 0.4, 0.35); add(ding(), ph('closer to') + 0.4, 0.3)
    add(thud(), ph('C and'), 0.5); add(thud(), ph('C and') + 0.25, 0.5)
    add(screech(), ph('while the AMG') - 0.1, 0.55); add(rev(1.0), ph('performance') - 0.1, 0.6)
    add(rev(0.9, 50, 200), ph('the G Class'), 0.45)
    add(ding(), ph('and if you'), 0.4)
    # ---- house sound rule (Nov 2026): continuous bass-heavy bed ~12 dB under the voice, light ducking,
    #      sound effects soft and short so the voice always leads
    mus = music(dur)
    k = int(SR * 0.004)
    low = np.convolve(mus, np.ones(k) / k, 'same')          # crude low-pass for extra bass weight
    mus = mus + 1.2 * low
    frame = SR // 50
    m_env = np.array([np.sqrt(np.mean(v[i:i + frame] ** 2)) for i in range(0, n, frame)])
    voiced = 20 * np.log10(m_env + 1e-6) > -38
    vad = np.convolve(voiced.astype(float), np.ones(10) / 10, 'same')
    duck = np.repeat(1 - 0.25 * vad, frame)[:n]
    vv = v / (np.abs(v).max() + 1e-9) * 0.9
    v_rms = np.sqrt(np.mean(vv[np.repeat(voiced, frame)[:n]] ** 2))
    m_rms = np.sqrt(np.mean(mus ** 2)) + 1e-9
    mus = mus / m_rms * v_rms * 10 ** (-12 / 20) * duck
    s_peak = np.abs(sfx).max() + 1e-9
    sfx = sfx / s_peak * 0.12   # original effects, volume lowered (user, 27 Nov 2026)
    mix = vv + sfx + mus
    mix = mix / max(1.0, np.abs(mix).max() / 0.98)
    st = np.stack([mix + mus * 0.15, mix - mus * 0.15], 1)
    with wave.open(os.path.join(HERE, 'build', 'mix.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    print('mix written')


if __name__ == '__main__':
    main()
