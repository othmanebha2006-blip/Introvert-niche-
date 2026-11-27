"""Exact word timing by forced alignment (pocketsphinx, bundled English model). Writes words.json."""
import json, re, wave, sys
from pocketsphinx import Decoder

REP = {'A4': 'a four', 'Q5': 'q five', 'S3': 's three', 'RS3': 'r s three', 'SUV': 's u v', 'SUVs': 's u vs', 'what\'s': "what's", 'petrol-powered': 'petrol powered', 'e': 'e',
       'A3': 'a three', 'A6': 'a six', 'Q3': 'q three', 'Q7': 'q seven', 'Q8': 'q eight', 'TFSI': 't f s i', 'TDI': 't d i',
       'e-tron': 'e tron', 'e-hybrid': 'e hybrid', 'RS': 'r s', 'S5': 's five', 'A5': 'a five', '40': 'forty', '45': 'forty five',
       'lower-bodied': 'lower bodied', 'plug-in': 'plug in', 'all-wheel-drive': 'all wheel drive', 'all-wheel': 'all wheel',
       'high-performance': 'high performance', "doesn't": "doesn't", "that's": "that's", "there's": "there's", "it's": "it's",
       "Audi's": 'audis', "car's": 'cars', 'RennSport': 'renn sport', 'Sportback': 'sport back', '5': 'five', '6': 'six'}


def main(wav, script, out):
    words = open(script).read().split()
    spoken, owner = [], []
    for i, w in enumerate(words):
        c = w.strip('.,')
        s = REP.get(c, c).lower()
        s = re.sub(r"[^a-z' ]", '', s)
        for t in s.split():
            spoken.append(t); owner.append(i)
    dec = Decoder(lm=None)
    for t in set(spoken):
        if dec.lookup_word(t) is None:
            print('not in dict:', t)
    with wave.open(wav) as f:
        assert f.getframerate() == 16000
        data = f.readframes(f.getnframes())
    dec.set_align_text(' '.join(spoken))
    dec.start_utt(); dec.process_raw(data, full_utt=True); dec.end_utt()
    segs = [s for s in dec.seg() if s.word not in ('<s>', '</s>', '<sil>', '[NOISE]') and not s.word.startswith('+')]
    print('aligned tokens', len(segs), 'expected', len(spoken))
    fr = 0.01
    tok_times = [(s.start_frame * fr, (s.end_frame + 1) * fr) for s in segs]
    res = []
    for i, w in enumerate(words):
        idx = [k for k, o in enumerate(owner) if o == i]
        res.append(dict(w=w, s=round(tok_times[idx[0]][0], 2), e=round(tok_times[idx[-1]][1], 2)))
    json.dump(dict(words=res, speech=[res[0]['s'], res[-1]['e']]), open(out, 'w'), indent=0)


if __name__ == '__main__':
    main(*sys.argv[1:4])
