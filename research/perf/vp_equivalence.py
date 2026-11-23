"""Old vs new pragyam.pine profile code, ported line for line: per-row search and a value-area walk on every
bar (old) against one search per span with a neighbour hint and the walk only where it is read (new).
Random sessions, intrabars, gaps and volumes; every bar in turn is taken as the last bar."""
import math, random, bisect

def locate(keys, k):
    i = bisect.bisect_left(keys, k)
    return i, (i < len(keys) and keys[i] == k)

def walk(S, sTot, sKey, poc0, vah0, val0, pct=0.70):
    keys, vols, binw = S["keys"], S["vols"], S["bin"]
    sPoc, sVah, sVal = poc0, vah0, val0
    n = len(keys)
    if n > 0 and sKey is not None and binw is not None:
        pi, pf = locate(keys, sKey)
        if pf:
            target = sTot * pct; lo = hi = pi; acc = vols[pi]; g = 0
            while acc < target and (lo > 0 or hi < n - 1) and g < n + 2:
                g += 1
                vd = vols[lo - 1] if lo > 0 else -1.0
                vu = vols[hi + 1] if hi < n - 1 else -1.0
                if vu >= vd: hi += 1; acc += vu
                else: lo -= 1; acc += vd
            sPoc = (sKey + 0.5) * binw; sVah = (keys[hi] + 1.0) * binw; sVal = keys[lo] * binw
    return sPoc, sVah, sVal

def add_old(S, k, v, b, s):
    keys = S["keys"]; pos, f = locate(keys, k); nv = v
    if f:
        nv = S["vols"][pos] + v; S["vols"][pos] = nv; S["buys"][pos] += b; S["sells"][pos] += s
    else:
        keys.insert(pos, k); S["vols"].insert(pos, v); S["buys"].insert(pos, b); S["sells"].insert(pos, s)
    return nv

def find(keys, k, hint):
    if hint is not None:
        for i in (hint, hint - 1, hint + 1):
            if 0 <= i < len(keys) and keys[i] == k:
                return i, True
    return locate(keys, k)

def span_new(S, kl, nb, v, b, s, tot, pv, pk, hint):
    keys = S["keys"]; pos0, _ = find(keys, kl, hint); pos = pos0
    for k in range(kl, kl + nb):
        nv = v
        if pos < len(keys) and keys[pos] == k:
            nv = S["vols"][pos] + v; S["vols"][pos] = nv; S["buys"][pos] += b; S["sells"][pos] += s
        else:
            keys.insert(pos, k); S["vols"].insert(pos, v); S["buys"].insert(pos, b); S["sells"].insert(pos, s)
        tot += v
        if nv > pv: pv, pk = nv, k
        pos += 1
    return tot, pv, pk, pos0

def fresh():
    return dict(keys=[], vols=[], buys=[], sells=[], bin=None, tot=0.0, pk=None, pv=0.0, poc=None, vah=None, val=None,
                ppoc=None, pvah=None, pval=None)

def run(bars, last, new_code, trail=False):
    S = fresh()
    for t, (newsess, binw, ib) in enumerate(bars[: last + 1]):
        islast = t == last
        if newsess:
            if new_code and not trail:
                S["poc"], S["vah"], S["val"] = walk(S, S["tot"], S["pk"], S["poc"], S["vah"], S["val"])
            S["ppoc"], S["pvah"], S["pval"] = S["poc"], S["vah"], S["val"]
            S.update(keys=[], vols=[], buys=[], sells=[], tot=0.0, pk=None, pv=0.0, bin=binw)
        hint = None
        for (lo, hi, v, b, s) in ib:
            kl = math.floor(lo / S["bin"]); kh = math.floor(hi / S["bin"]); nb = max(1, min(kh - kl + 1, 200))
            if new_code:
                S["tot"], S["pv"], S["pk"], hint = span_new(S, kl, nb, v / nb, b / nb, s / nb, S["tot"], S["pv"], S["pk"], hint)
            else:
                for k in range(kl, kl + nb):
                    tot = add_old(S, k, v / nb, b / nb, s / nb); S["tot"] += v / nb
                    if tot > S["pv"]: S["pv"], S["pk"] = tot, k
        if not new_code or trail or islast:
            S["poc"], S["vah"], S["val"] = walk(S, S["tot"], S["pk"], S["poc"], S["vah"], S["val"])
    return {k: v for k, v in S.items()}

random.seed(7)
checked = 0
for trial in range(300):
    bars = []; px = 100.0
    for t in range(random.randint(20, 90)):
        newsess = t == 0 or random.random() < 0.15
        binw = random.choice([0.05, 0.1, 0.25, 0.5])
        ib = []
        for j in range(random.choice([0, 1, 1, 3, 12])):
            px *= math.exp(random.gauss(0, 0.004)) if random.random() > 0.03 else math.exp(random.gauss(0, 0.05))
            w = abs(random.gauss(0, 0.3)); v = random.choice([0.0, random.random() * 100, float(random.randint(1, 5))])
            sh = random.random()
            ib.append((px - w, px + w, v, v * sh, v * (1 - sh)))
        if not ib:
            ib = [(px - 1, px + 1, 10.0, 5.0, 5.0)]
        bars.append((newsess, binw, ib))
    for last in range(len(bars)):
        for trail in (False, True):
            a, b = run(bars, last, False), run(bars, last, True, trail)
            assert a == b, (trial, last, trail, {k: (a[k], b[k]) for k in a if a[k] != b[k]})
            checked += 1
print("identical on", checked, "last-bar states")
