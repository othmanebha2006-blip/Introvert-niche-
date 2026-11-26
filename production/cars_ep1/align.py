"""Rough word timing for a known script: syllable-weighted spread over voiced audio,
with phrase breaks (commas/periods) snapped to detected pauses."""
import re, json, sys, subprocess
import numpy as np

SPELL = {'IS':2,'ES':2,'LS':2,'UX':2,'NX':2,'RX':2,'GX':2,'LX':2,'LC':2,'SUV':3,'SUVs':3,
         'RC':2,'F':1,'X':1,'L':1,'h':1,'e':1,'350':3,'500':3,'500h':4,'450h+':5,
         '5-litre':3,'V10':2,'LFA':3,'Lexus':2,"Lexus's":3}

def syl(w):
    c = w.strip('.,')
    if c in SPELL: return SPELL[c]
    c = c.lower()
    v = re.findall(r'[aeiouy]+', c)
    n = len(v) - (1 if c.endswith('e') and len(v) > 1 and not c.endswith('le') else 0)
    return max(1, n)

def main(audio, script, out):
    raw = subprocess.run(['ffmpeg','-v','error','-i',audio,'-ac','1','-ar','16000','-f','s16le','-'],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = 160
    n = len(a) // hop
    db = 20*np.log10(np.sqrt((a[:n*hop].reshape(n, hop)**2).mean(1)) + 1e-6)
    voiced = db > -38
    # speech start/end
    idx = np.where(voiced)[0]; t0, t1 = idx[0]/100, idx[-1]/100
    # pauses
    pauses = []
    i = 0
    while i < n:
        if not voiced[i]:
            j = i
            while j < n and not voiced[j]: j += 1
            if j - i >= 5 and i/100 > t0 and j/100 < t1: pauses.append(((i+j)/200, (j-i)/100, i/100, j/100))
            i = j
        else: i += 1
    words = open(script).read().split()
    sy = np.array([syl(w) for w in words], float)
    cum = np.concatenate([[0], np.cumsum(sy)]) / sy.sum()
    # map syllable fraction -> time via cumulative voiced time
    vc = np.cumsum(voiced) / voiced.sum()
    def frac2t(f): return np.searchsorted(vc, f) / 100
    est = [frac2t(c) for c in cum]
    # DP: assign each phrase end to a pause so speaking rate stays even
    ends = [k for k, w in enumerate(words) if w[-1] in ',.' and k < len(words)-1]
    psyl = []; prev = -1
    for k in ends + [len(words)-1]:
        psyl.append(sy[prev+1:k+1].sum()); prev = k
    cv = np.concatenate([[0], np.cumsum(voiced)]) / 100
    def vdur(a, b): return max(cv[int(b*100)] - cv[int(a*100)], 0.05)
    rate = sy.sum() / vdur(t0, t1)
    Q = [(None, None, t0, t0)] + pauses
    INF = 1e18
    P = len(ends)
    cost = np.full((P+1, len(Q)), INF); back = np.zeros((P+1, len(Q)), int)
    cost[0][0] = 0
    for p in range(1, P+1):
        for q in range(1, len(Q)):
            best = INF; bq = 0
            for r in range(q):
                if cost[p-1][r] >= INF: continue
                c = cost[p-1][r] + np.log(psyl[p-1] / vdur(Q[r][3], Q[q][2]) / rate)**2 - 0.3*min(Q[q][1], .4)
                if c < best: best, bq = c, r
            cost[p][q] = best; back[p][q] = bq
    # last phrase to t1
    tot = [cost[P][q] + np.log(psyl[P] / vdur(Q[q][3], t1) / rate)**2 for q in range(len(Q))]
    q = int(np.argmin(tot)); bounds = {}
    for p in range(P, 0, -1):
        bounds[ends[p-1]] = Q[q]; q = back[p][q]
    # build segments between anchors and spread by syllables over voiced frames inside
    anchors = [(-1, t0)]
    for k in sorted(bounds): anchors.append((k, bounds[k]))
    res = []
    start_t = t0
    prev_k = -1
    for k, p in anchors[1:] + [(len(words)-1, (t1, 0, t1, t1))]:
        seg = list(range(prev_k+1, k+1))
        s, e = start_t, p[2]
        fr = np.arange(int(s*100), max(int(e*100), int(s*100)+1))
        vv = voiced[fr] if len(fr) else np.array([True])
        vcs = np.cumsum(vv) / max(vv.sum(), 1)
        ss = sy[seg]; cc = np.concatenate([[0], np.cumsum(ss)]) / ss.sum()
        for j, wi in enumerate(seg):
            ws = s + np.searchsorted(vcs, cc[j]+1e-9) / 100 if j else s
            we = s + np.searchsorted(vcs, cc[j+1]-1e-9) / 100
            res.append(dict(w=words[wi], s=round(float(ws), 2), e=round(float(max(we, ws+0.05)), 2)))
        start_t = p[3]; prev_k = k
    json.dump(dict(words=res, pauses=pauses, speech=[t0, t1]), open(out, 'w'), indent=0)
    print(len(words), 'words', len(bounds), 'phrase breaks snapped of', sum(w[-1] in ',.' for w in words), 'speech', t0, t1)

if __name__ == '__main__':
    main(*sys.argv[1:4])
