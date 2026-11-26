"""Ep2 sound design (same palette as ep1 v2) keyed to the AMG timeline."""
import os, wave, subprocess
import numpy as np
import compose as C
import compose_amg as A
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
    add(whoosh(0.5), 0.0, 0.6); add(rev(0.7), 0.05, 0.5)
    add(whoosh(0.35), ph('AMG', 1) + 0.1, 0.4); add(whoosh(0.35), ph('AMG stands') - 0.1, 0.4)
    for i in range(8):
        add(pop(800 + 60 * i), ph('AMG', 1) + 0.25 + i * 0.04, 0.18)
    for p in ['Aufrecht', 'Melcher', 'Großaspach', 'founders', 'the town', 'born', 'performance division', 'full AMG', 'own engine', 'suspension',
              'performance upgrades', 'sporty trim', 'bigger wheels', 'aggressive bumpers', 'performance level', '35 is', '43 sits', '53 brings',
              'and 63 is', 'a V8', 'plug-in hybrid', 'V8 models', 'AMG GT', 'sharper', 'all-wheel-drive', 'sports car', 'G-Class',
              'performance SUV', 'top-tier', 'extra-powerful', 'all-wheel drive']:
        add(pop(760 + (hash(p) % 5) * 90), ph(p), 0.3)
    add(pop(1100), ph('plug-in hybrid', 3), 0.3)
    for p in ['GLC 63', '63 S E', 'S E PERFORMANCE']:
        add(pop(1200), ph(p) + 0.2, 0.25)
    add(thud(), ph('no extra'), 0.8); add(thud(), ph('engine size') - 0.2, 0.8)
    add(ding(), ph('top of the range') + 0.4, 0.35)
    add(pop(500), ph('high-performance plug-in') + 0.15, 0.5); add(zap(), ph('high-performance plug-in') + 0.17, 0.6)
    add(screech(), ph("then there's 55") - 0.1, 0.55)
    add(rev(1.0), ph('V8 models') - 0.1, 0.7); add(rev(0.8, 60, 260), ph('sharper'), 0.5)
    add(rev(0.8, 50, 200), ph('performance division') - 0.1, 0.4)
    for i in range(4):
        add(pop(600 + 150 * i), ph('all-wheel-drive') + i * 0.15, 0.3)
    add(ding(), ph('and if you'), 0.4)
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
    with wave.open(os.path.join(HERE, 'build', 'mix.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    print('mix written')


if __name__ == '__main__':
    main()
