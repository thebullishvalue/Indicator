"""Property test of the CVG state engine (docs/audit-readout-v9.8.md, C1): a literal port of
pragati.pine's grid engine run on 200,000 random bars, checked against the rules its tooltips
state.

    python -I research/audit/grid_props.py
"""
import math, random
Z1, Z2, TH = 30.0, 60.0, 40.0      # inner zone, outer zone, θ - any positive values with Z1 < Z2
def unit(r, c):
    return (3.0 if c == 0 else 1.5 if c == 1 else 0.75) if r == 1 else (1.5 if c == 0 else 1.0 if c == 1 else 0.75) if r == 0 else (4.0 if c == 0 else 1.5 if c == 1 else 0.25)
def at(rp, cp):
    r, c = max(-1.0, min(1.0, rp)), max(-1.0, min(1.0, cp))
    r0, c0 = (-1 if r < 0 else 0), (-1 if c < 0 else 0)
    wr, wc = r - r0, c - c0
    lo = (1 - wc) * unit(r0, c0 + 1) + wc * unit(r0, c0 + 2)
    hi = (1 - wc) * unit(r0 + 1, c0 + 1) + wc * unit(r0 + 1, c0 + 2)
    return (1 - wr) * lo + wr * hi
def ink(x, knee, solid):
    a = abs(x)
    return 0.65 + 0.35 * max(0.0, min(1.0, (a - knee) / max(solid - knee, 1e-9))) if a >= knee else 0.12 + 0.33 * max(0.0, min(1.0, a / max(knee, 1e-9)))
def side(prev, m, knee):
    if m is None: return 0.0
    if knee is None or knee <= 0: return math.copysign(1.0, m) if m != 0 else 0.0
    return 1.0 if m >= knee else -1.0 if m <= -knee else prev if prev != 0 else (math.copysign(1.0, m) if m != 0 else 0.0)
sgn = lambda x: (x > 0) - (x < 0)
rng = random.Random(7)
row, sc, sv = None, 0.0, 0.0
fails, n = {}, 0
def check(k, ok):
    if not ok: fails[k] = fails.get(k, 0) + 1
for t in range(200000):
    read = rng.random() > 0.02
    mC, mV = rng.uniform(-100, 100), rng.uniform(-100, 100)
    gate = None if rng.random() < 0.05 else rng.choice([-1.0, 0.0, 1.0])
    push = None if gate is None else rng.uniform(-1, 1)
    tgt = 1 if mC >= Z1 else -1 if mC <= -Z1 else 0
    col = 0 if mV <= -TH else 2 if mV >= TH else 1
    prev = row
    if not read:
        row, sc, sv = None, 0.0, 0.0
    else:
        if row is None or gate is None: row = tgt
        elif tgt > row and gate > 0: row = tgt
        elif tgt < row and gate < 0: row = tgt
        sc = side(sc, rng.uniform(-50, 50) if rng.random() > 0.1 else None, 10.0)
        sv = side(sv, rng.uniform(-50, 50) if rng.random() > 0.1 else None, 10.0)
    if not read: continue
    n += 1
    held = row != tgt
    cph = 0 if (row == 0 or sc == 0.0) else (1 if sc == row else -1)
    vph = 0 if (col == 1 or sv == 0.0) else (1 if sv == (1.0 if col == 0 else -1.0) else -1)
    if held:
        hs = 1.0 if row > tgt else -1.0
        hh = 0.0 if push is None else max(0.0, min(1.0, push * hs))
        nb = row + (1 if tgt > row else -1)
        pr = row * (0.5 + 0.5 * hh) + nb * (0.5 - 0.5 * hh)
    elif row != 0:
        pr = row * ink(mC, Z1, Z2)
    else:
        pr = (1.0 if mC > 0 else -1.0) * (ink(mC, Z1, Z2) - 0.12)
    pc = (col - 1) * ink(mV, TH, 70.0) if col != 1 else (1.0 if mV > 0 else -1.0) * (ink(mV, TH, 70.0) - 0.12)
    if row != 0 and cph == -1: pr *= 0.5
    if col != 1 and vph == -1: pc *= 0.5
    u = at(pr, pc)
    # the properties the tooltips and comments state
    check("P1 units within the map's range [0.25, 4]", 0.25 - 1e-9 <= u <= 4.0 + 1e-9)
    check("P2 position inside the map", abs(pr) <= 1 + 1e-9 and abs(pc) <= 1 + 1e-9)
    if prev is not None and gate is not None and row != prev:
        check("P3 a row moves only on a push its way", sgn(row - prev) == sgn(gate))
    if prev is not None and gate is not None and row != prev:
        check("P4 a row that moves lands on its tape", row == tgt)
    if not held and row != 0 and cph != -1:
        check("P5 an unheld confirmed row sits past its knee ink (>= 0.65)", abs(pr) >= 0.65 - 1e-9 and sgn(pr) == row)
    if not held and row == 0:
        check("P6 the FAINT row stays inside +-0.33", abs(pr) <= 0.33 + 1e-9)
    if held and push is not None:
        check("P7 a held name sits between the held row and half-way", min(row, (row + nb) / 2) - 1e-9 <= pr / (0.5 if (row != 0 and cph == -1) else 1.0) <= max(row, (row + nb) / 2) + 1e-9)
for r in (-1, 0, 1):
    for c in (0, 1, 2):
        check("P8 the map's corners are the nine cells", abs(at(r, c - 1) - unit(r, c)) < 1e-12)
print(f"{n} readable bars checked")
for k in sorted({"P1 units within the map's range [0.25, 4]", "P2 position inside the map", "P3 a row moves only on a push its way", "P4 a row that moves lands on its tape", "P5 an unheld confirmed row sits past its knee ink (>= 0.65)", "P6 the FAINT row stays inside +-0.33", "P7 a held name sits between the held row and half-way", "P8 the map's corners are the nine cells"}):
    print(("FAIL " + str(fails[k]) if k in fails else "pass") + "  " + k)
