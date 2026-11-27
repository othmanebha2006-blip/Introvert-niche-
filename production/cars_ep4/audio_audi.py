"""Ep2 sound design (same palette as ep1 v2) keyed to the AMG timeline."""
import os, wave, subprocess
import numpy as np
import compose as C
import compose_audi as A
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
    add(whoosh(0.5), 0.0, 0.6); add(rev(0.7), 0.05, 0.5)
    add(whoosh(0.35), ph('explained') - 0.05, 0.4); add(whoosh(0.35), ph('Audi uses') - 0.15, 0.4)
    for i in range(12):
        add(pop(800 + 50 * i), ph('explained') + 0.1 + i * 0.035, 0.16)
    for p in ['two main', 'separate', 'lower-bodied', 'A3', 'SUVs', 'compact Q3', 'larger Q7', 'Q8', 'where the car', 'higher', 'bigger',
              'expensive', 'badges', 'TFSI', 'TDI', 'e-tron', 'e-hybrid', 'plug-in hybrid', 'body style', 'estate', 'sloping', 'saloon',
              'sporty model', 'RennSport', 'German', 'racing', 'styling package', 'sportier details', 'all-wheel-drive', 'old power',
              'size', 'high-performance', 'sharper', 'extra performance', 'all-wheel drive']:
        add(pop(760 + (hash(p) % 5) * 90), ph(p), 0.3)
    for i in range(4):
        add(pop(900 + 120 * i), ph('higher') + i * 0.45, 0.25)
        add(pop(600 + 150 * i), ph("Audi's") - 0.05 + i * 0.15, 0.3)
    add(thud(), ph('the engine') - 0.05, 0.8); add(thud(), ph('different'), 0.8); add(thud(), ph('because') + 0.2, 0.6)
    add(pop(500), ph('fully') - 0.1, 0.5); add(zap(), ph('fully') - 0.08, 0.6)
    add(screech(), ph('and RS comes') - 0.1, 0.55); add(rev(1.0), ph('racing') - 0.1, 0.6)
    add(rev(0.9, 60, 300), ph("then there's the"), 0.5)
    add(rev(1.0), ph('extra performance') - 0.1, 0.7)
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
