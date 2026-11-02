"""The OI block of pragati.pine ported literally, v9.7 (CURRENT) and v9.8 (FIXED),
run on scripted scenarios. Prints what the readout's STATE / BUILD cells would say."""
import math
BASE, ROLL, ROLL_ABS, STRU, ACT, DEAD = 50, 3.0, 0.20, 0.50, 0.20, 0.50
def run(oi, px, fixed):
    seen, sq, out, moved = False, [], [], []
    for t in range(len(oi)):
        v, p = oi[t], (oi[t - 1] if t else None)
        if v is not None and v > 0: seen = True
        moved.append(1.0 if (t and v is not None and p is not None and v != p) else 0.0)
        act = sum(moved[-BASE:]) / BASE if t >= BASE - 1 else 0.0
        live = seen and v is not None and v > 0 and act >= ACT
        pair = v is not None and v > 0 and p is not None and p > 0
        lg = math.log(v / p) if pair else 0.0
        share = abs(v - p) / p if pair else 0.0
        rms = math.sqrt(sum(sq) / len(sq)) if len(sq) >= 10 else None
        has = (live and rms is not None) if fixed else live
        z = lg / rms if (rms or 0) > 1e-12 and (has or not fixed) else 0.0
        roll = (live if fixed else has) and pair and (share > STRU or (abs(z) > ROLL and share > ROLL_ABS))
        if (live if fixed else has) and pair and not roll:
            sq.append(lg * lg); sq[:] = sq[-BASE:]
        dpx = px[t] - px[t - 1] if t else 0.0
        if not has:
            st = ("Warming" if fixed and live else "Stale feed" if seen else "No OI")
        elif roll: st = "Expiry / roll"
        elif z > DEAD and dpx > 0: st = "Long build-up"
        elif z > DEAD and dpx < 0: st = "Short build-up"
        elif z < -DEAD and dpx > 0: st = "Short covering"
        elif z < -DEAD and dpx < 0: st = "Long unwinding"
        else: st = "Price flat" if (fixed and abs(z) > DEAD) else "Balanced"
        out.append((st, f"{z:+.1f}σ" if has else ""))
    return out
# Scenario 1 · a feed that goes live: 60 bars of steady 1-3% daily changes, price rising
oi, px = [], []
v, p = 1e6, 100.0
for t in range(80):
    v *= 1.0 + (0.02 if t % 3 else 0.01); p *= 1.004
    oi.append(v); px.append(p)
cur, fix = run(oi, px, False), run(oi, px, True)
print("Scenario 1 - OI growing 1-2% a day with price up (a long build-up throughout):")
for t in (49, 50, 52, 55, 58, 59, 60, 62, 70):
    print(f"   bar {t:2d}  current: {cur[t][0]:<15} {cur[t][1]:>6}   fixed: {fix[t][0]:<15} {fix[t][1]:>6}")
# Scenario 2 · price unchanged, book jumps 15%
oi2, px2 = oi[:] + [oi[-1] * 1.15], px[:] + [px[-1]]
c2, f2 = run(oi2, px2, False)[-1], run(oi2, px2, True)[-1]
print(f"Scenario 2 - book +15% on a bar whose close did not move: current {c2}, fixed {f2}")
