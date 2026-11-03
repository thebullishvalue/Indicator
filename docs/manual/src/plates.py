"""SVG plates for the Pragati manual. Example drawings built from synthetic series, labelled as such."""
import math


def ema(x, n):
    a, out, v = 2 / (n + 1), [], None
    for xi in x:
        v = xi if v is None else v + a * (xi - v)
        out.append(v)
    return out


def plate_pane():
    W, H, L, R = 900, 430, 30, 700
    N = 64
    trace = []
    for i in range(N):
        t = i / (N - 1)
        v = 18 + 40 * math.sin(2 * math.pi * (t * 1.05 + 0.05)) - 48 * math.exp(-((t - 0.62) / 0.11) ** 2) + 6 * math.sin(i * 0.9)
        trace.append(max(-92, min(92, v)))
    sig = ema(trace, 9)
    hist = [a - b for a, b in zip(trace, sig)]
    y = lambda v: 215 - v * 1.75
    bw = (R - L) / N
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Annotated example of Pragati\'s pane">']
    out.append(f'<rect x="{L}" y="20" width="{R - L}" height="390" class="f-surface s-line" stroke-width="1"/>')
    # capitulation tint (grid state) bars 37-45, deeper after the turn at 42
    out.append(f'<rect x="{L + 37 * bw:.1f}" y="20" width="{5 * bw:.1f}" height="390" class="f-bull" opacity="0.07"/>')
    out.append(f'<rect x="{L + 42 * bw:.1f}" y="20" width="{4 * bw:.1f}" height="390" class="f-bull" opacity="0.14"/>')
    # rails
    for v, dash, lab in ((60, "6 4", "+60"), (43, "2 3", "+θ"), (-43, "2 3", "−θ"), (-60, "6 4", "−60")):
        out.append(f'<line x1="{L}" x2="{R}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="s-muted" stroke-dasharray="{dash}" stroke-width="1"/>')
        out.append(f'<text x="{L - 4}" y="{y(v) + 4:.1f}" text-anchor="end" class="t-small f-muted">{lab}</text>')
    out.append(f'<line x1="{L}" x2="{R}" y1="{y(0)}" y2="{y(0)}" class="s-muted" stroke-width="1"/>')
    out.append(f'<text x="{L - 4}" y="{y(0) + 4}" text-anchor="end" class="t-small f-muted">0</text>')
    # tapes: conviction +82 (with momentum band +89), value -82 (momentum -89)
    mc = ema([v * 1.1 for v in trace], 5)
    mv = ema([(-v) * 0.8 for v in trace], 12)
    for i in range(N):
        x = L + i * bw
        c = mc[i]; vv = mv[i]
        cc = "f-bull" if c > 0 else "f-bear"
        op = 0.95 if abs(c) >= 30 else 0.35
        out.append(f'<rect x="{x:.1f}" y="{y(84):.1f}" width="{bw - 0.6:.1f}" height="6" class="{cc}" opacity="{op}"/>')
        mom = mc[i] - (mc[i - 4] if i >= 4 else mc[0])
        out.append(f'<rect x="{x:.1f}" y="{y(91):.1f}" width="{bw - 0.6:.1f}" height="3" class="{"f-bull" if mom > 0 else "f-bear"}" opacity="0.55"/>')
        vc = "f-bull" if vv > 0 else "f-bear"
        op = 0.95 if abs(vv) >= 30 else 0.35
        out.append(f'<rect x="{x:.1f}" y="{y(-80):.1f}" width="{bw - 0.6:.1f}" height="6" class="{vc}" opacity="{op}"/>')
        vm = mv[i] - (mv[i - 4] if i >= 4 else mv[0])
        out.append(f'<rect x="{x:.1f}" y="{y(-88):.1f}" width="{bw - 0.6:.1f}" height="3" class="{"f-bull" if vm > 0 else "f-bear"}" opacity="0.55"/>')
    # histogram columns with tiers
    for i in range(1, N):
        h = hist[i] * 2.0
        x = L + i * bw + 1
        grow = abs(hist[i]) > abs(hist[i - 1])
        with_ = (trace[i] - trace[i - 1]) * (1 if hist[i] >= 0 else -1) > 0.4
        op = (0.95 if abs(h) > 9 else 0.7) if grow else (0.5 if with_ else 0.22)
        cls = "f-bull" if h >= 0 else "f-bear"
        if 14 <= i <= 16:
            cls = "f-gold"
        top = min(y(0), y(h))
        out.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw - 2.4:.1f}" height="{abs(y(h) - y(0)):.1f}" class="{cls}" opacity="{op}"/>')
    # trace
    pts = " ".join(f"{L + i * bw + bw / 2:.1f},{y(v):.1f}" for i, v in enumerate(trace))
    out.append(f'<polyline points="{pts}" fill="none" class="s-ink" stroke-width="2.2"/>')
    # markers on the rails
    out.append(f'<text x="{L + 42 * bw + bw / 2:.1f}" y="{y(-60) + 18:.1f}" text-anchor="middle" class="t-mark f-bull">▲</text>')
    out.append(f'<text x="{L + 19 * bw + bw / 2:.1f}" y="{y(60) - 8:.1f}" text-anchor="middle" class="t-mark f-bear">▼</text>')
    # right-edge labels
    out.append(f'<text x="{R + 8}" y="{y(84) + 6:.1f}" class="t-small f-bull">CONVICTION +41</text>')
    out.append(f'<text x="{R + 8}" y="{y(-80) + 6:.1f}" class="t-small f-bear">VALUE cheap −36</text>')
    out.append(f'<text x="{R + 8}" y="{y(43) + 4:.1f}" class="t-small f-muted">TRACE · θ</text>')
    # callouts
    calls = [(1, L + 8 * bw, y(42) - 10, "trace"), (2, L + 27 * bw, y(-16), "hist"), (3, R - 4, y(60) - 4, "rail"),
             (4, L + 3 * bw, y(84) - 8, "ctape"), (5, L + 3 * bw, y(-80) + 22, "vtape"), (6, L + 42 * bw + bw / 2, y(-60) + 34, "up"),
             (7, L + 19 * bw + bw / 2, y(60) - 26, "dn"), (8, L + 39 * bw, 36, "tint"), (9, L + 15 * bw + bw / 2, y(0) + 16, "gold")]
    for n, cx, cy, _ in calls:
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="10" class="f-accent"/><text x="{cx:.1f}" y="{cy + 4:.1f}" text-anchor="middle" class="t-callout">{n}</text>')
    out.append(f'<text x="{L}" y="{H - 2}" class="t-tiny f-muted">Example drawing from a synthetic series, not real data. Histogram drawn at the default display gain of 2.</text>')
    out.append('</svg>')
    return "\n".join(out)


def plate_chart():
    W, H = 900, 470
    import random
    rng = random.Random(4)
    N = 52
    p, rows = 100.0, []
    for i in range(N):
        drift = 0.55 if i < 22 else (-0.7 if i < 31 else 0.6)
        o = p
        c = o + drift + rng.gauss(0, 1.1)
        hi = max(o, c) + abs(rng.gauss(0, 0.7))
        lo = min(o, c) - abs(rng.gauss(0, 0.7))
        rows.append((o, hi, lo, c))
        p = c
    pmin = min(r[2] for r in rows) - 4
    pmax = max(r[1] for r in rows) + 4
    L, R, T, B = 40, 600, 24, 330
    y = lambda v: B - (v - pmin) / (pmax - pmin) * (B - T)
    bw = (R - L) / N
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Annotated example of Pragati on the price chart">']
    out.append(f'<rect x="{L}" y="{T - 10}" width="{770 - L}" height="{B - T + 20}" class="f-surface s-line" stroke-width="1"/>')
    # value ribbon (slate band) and its dotted POC: rolling around price
    mids = ema([r[3] for r in rows], 8)
    band_hi = [m + 3.0 for m in mids]; band_lo = [m - 3.2 for m in mids]
    pts = [f"{L + i * bw + bw / 2:.1f},{y(v):.1f}" for i, v in enumerate(band_hi)] + [f"{L + i * bw + bw / 2:.1f},{y(v):.1f}" for i, v in reversed(list(enumerate(band_lo)))]
    out.append(f'<polygon points="{" ".join(pts)}" class="f-slate" opacity="0.16"/>')
    out.append(f'<polyline points="{" ".join(f"{L + i * bw + bw / 2:.1f},{y(m):.1f}" for i, m in enumerate(mids))}" fill="none" class="s-slate" stroke-dasharray="2 3" stroke-width="1.2"/>')
    # naked POC from an earlier session
    yn = y(rows[8][3] + 6)
    out.append(f'<line x1="{L + 8 * bw:.1f}" x2="{R:.1f}" y1="{yn:.1f}" y2="{yn:.1f}" class="s-poc" stroke-dasharray="1 3" stroke-width="1.2"/>')
    # session POC / VA box from session start (bar 30)
    s0 = 30
    vah, val, poc = rows[s0][3] + 4.5, rows[s0][3] - 3.0, rows[s0][3] + 0.8
    out.append(f'<rect x="{L + s0 * bw:.1f}" y="{y(vah):.1f}" width="{R - (L + s0 * bw):.1f}" height="{y(val) - y(vah):.1f}" class="f-va" opacity="0.08"/>')
    for v, cls, w in ((vah, "s-va", 1), (val, "s-va", 1), (poc, "s-poc", 2)):
        out.append(f'<line x1="{L + s0 * bw:.1f}" x2="{700}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="{cls}" stroke-width="{w}"/>')
    # VWAP curve from session start
    vw, acc_pv, acc_v = [], 0.0, 0.0
    for i in range(s0, N):
        o, hi, lo, c = rows[i]
        acc_pv += (hi + lo + c) / 3; acc_v += 1
        vw.append(acc_pv / acc_v)
    out.append(f'<polyline points="{" ".join(f"{L + (s0 + k) * bw + bw / 2:.1f},{y(v):.1f}" for k, v in enumerate(vw))}" fill="none" class="s-vwap" stroke-width="1.4"/>')
    # accepted momentum trail: stepped; long (green) then flat (neutral) then long again
    lvl, segs = None, []
    for i in range(N):
        lo_i = min(r[2] for r in rows[max(0, i - 8):i + 1])
        if i < 6:
            continue
        if lvl is None or (i % 5 == 0 and lo_i > lvl and i < 22) or (i > 34 and i % 5 == 0 and lo_i > lvl):
            lvl = lo_i - 0.4
        state = "long" if (i < 24 or i > 37) else "flat"
        segs.append((i, lvl, state))
    for (i, v, st), nxt in zip(segs, segs[1:] + [None]):
        x1 = L + i * bw; x2 = L + (i + 1) * bw
        cls = "s-bull" if st == "long" else "s-neut"
        op = "1" if (st == "long" and (i < 18 or i > 42)) else ("0.55" if st == "long" else "0.9")
        out.append(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="{cls}" stroke-width="3" opacity="{op}"/>')
        if nxt and abs(nxt[1] - v) > 1e-9:
            out.append(f'<line x1="{x2:.1f}" x2="{x2:.1f}" y1="{y(v):.1f}" y2="{y(nxt[1]):.1f}" class="{cls}" stroke-width="3" opacity="{op}"/>')
    # candles
    for i, (o, hi, lo, c) in enumerate(rows):
        x = L + i * bw + bw / 2
        cls = "bull" if c >= o else "bear"
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(hi):.1f}" y2="{y(lo):.1f}" class="s-{cls}" stroke-width="1"/>')
        out.append(f'<rect x="{x - bw * 0.32:.1f}" y="{y(max(o, c)):.1f}" width="{bw * 0.64:.1f}" height="{max(1.2, abs(y(o) - y(c))):.1f}" class="f-{cls}"/>')
    # a probe onset (gold x)
    pi_ = 27
    out.append(f'<text x="{L + pi_ * bw + bw / 2:.1f}" y="{y(rows[pi_][3]) + 5:.1f}" text-anchor="middle" class="t-mark f-gold">×</text>')
    # volume profile at the right edge
    px0 = 612
    prof = [3, 5, 8, 12, 17, 22, 26, 23, 18, 12, 8, 5, 3]
    step = (vah - val + 9) / len(prof)
    base = val - 4.5
    for k, wv in enumerate(prof):
        v0 = base + k * step
        inva = val <= v0 + step / 2 <= vah
        is_poc = wv == max(prof)
        cls = "f-poc" if is_poc else ("f-va" if inva else "f-node")
        op = "0.75" if is_poc else ("0.52" if inva else "0.32")
        out.append(f'<rect x="{px0}" y="{y(v0 + step * 0.9):.1f}" width="{wv * 2.6:.1f}" height="{abs(y(v0 + step * 0.9) - y(v0)):.1f}" class="{cls}" opacity="{op}"/>')
    # tags
    for v, lab, cls in ((poc, "POC", "f-poc"), (vah, "VAH", "f-va"), (val, "VAL", "f-va"), (vw[-1], "VWAP", "f-vwap")):
        out.append(f'<rect x="704" y="{y(v) - 8:.1f}" width="60" height="16" rx="2" class="{cls}" opacity="0.16"/><text x="708" y="{y(v) + 4:.1f}" class="t-small {cls}">{lab}</text>')
    # readout table, bottom left
    tx, ty = 40, 352
    cols = ["", "STATE", "WHY", "PUSH", "CHART", "SPAN"]
    cw = [64, 130, 196, 54, 104, 50]
    rowsT = [("OI", "Long build-up", "new longs · book 62 pct", "+1.4σ", "", "3d", "f-bull"),
             ("CVG", "Buy 2.71", "buyers running · turning up", "↑", "same", "6d", "f-bull"),
             ("AUCTION", "Migrating ↑", "trail ↑ · in value", "↑", "LONG 0.62", "41d", "f-bull")]
    out.append(f'<rect x="{tx}" y="{ty}" width="{sum(cw)}" height="{22 * 4}" class="f-surface s-line" stroke-width="1"/>')
    xx = tx
    for c, w in zip(cols, cw):
        out.append(f'<text x="{xx + 6}" y="{ty + 15}" class="t-tiny f-muted">{c}</text>'); xx += w
    for r, row in enumerate(rowsT):
        xx = tx
        for k, (val_, w) in enumerate(zip(row[:6], cw)):
            cls = row[6] if k in (1, 4) and val_ else ("f-muted" if k in (0, 2, 5) else "f-ink")
            out.append(f'<text x="{xx + 6}" y="{ty + 15 + 22 * (r + 1)}" class="t-small {cls}">{val_}</text>'); xx += w
    calls = [(1, L + 12 * bw, y(segs[6][1]) + 18), (2, L + 30 * bw, y(segs[24][1]) + 18), (3, L + 4 * bw, y(band_hi[4]) - 12),
             (4, L + pi_ * bw + bw / 2, y(rows[pi_][3]) - 16), (5, px0 + 72, y(poc) - 12), (6, 776, y(vah) - 2), (7, L + 44 * bw, y(vw[-6]) + 16),
             (8, L + 12 * bw, yn - 12), (9, tx + sum(cw) + 14, ty + 40)]
    for n, cx, cy in calls:
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="10" class="f-accent"/><text x="{cx:.1f}" y="{cy + 4:.1f}" text-anchor="middle" class="t-callout">{n}</text>')
    out.append(f'<text x="{40}" y="{H - 2}" class="t-tiny f-muted">Example drawing from a synthetic series, not real data. The readout is the default bottom-left table.</text>')
    out.append('</svg>')
    return "\n".join(out)


def plate_am():
    W, H = 900, 300
    import random
    rng = random.Random(9)
    N = 70
    p, px = 100.0, []
    for i in range(N):
        d = 0.5 if i < 28 else (-0.65 if i < 50 else 0.15)
        p += d + rng.gauss(0, 0.8)
        px.append(p)
    L, R, T, B = 40, 860, 20, 210
    lo, hi = min(px) - 6, max(px) + 6
    y = lambda v: B - (v - lo) / (hi - lo) * (B - T)
    bw = (R - L) / N
    # momentum boundary: a slow weighted average of past closes
    cstar = []
    for i in range(N):
        lags = [px[max(0, i - h)] for h in (5, 12, 24, 40)]
        w = [1 / math.sqrt(h) for h in (5, 12, 24, 40)]
        cstar.append(sum(a * b for a, b in zip(lags, w)) / sum(w))
    # acceptance trail: stepped, long until 36, short after 44, flips with a lag
    trail, side = [], []
    lvl, s = px[0] - 4, 1
    for i in range(N):
        if s == 1 and px[i] < lvl - 0.5 and i > 34:
            s, lvl = -1, max(px[i - 6:i + 1]) + 2
        elif s == 1 and i % 6 == 0 and px[i] - 4 > lvl:
            lvl = px[i] - 4
        elif s == -1 and i % 6 == 0 and px[i] + 4 < lvl:
            lvl = px[i] + 4
        trail.append(lvl); side.append(s)
    pos = []
    for i in range(N):
        mom = 1 if px[i] > cstar[i] else -1
        pos.append(side[i] if mom == side[i] else 0)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="How Accepted momentum decides long, flat or short">']
    for i in range(N):
        cls = "f-bull" if pos[i] > 0 else ("f-bear" if pos[i] < 0 else "f-neut")
        op = "0.13" if pos[i] else "0.10"
        out.append(f'<rect x="{L + i * bw:.1f}" y="{T}" width="{bw + 0.2:.1f}" height="{B - T}" class="{cls}" opacity="{op}"/>')
    out.append(f'<polyline points="{" ".join(f"{L + i * bw + bw / 2:.1f},{y(v):.1f}" for i, v in enumerate(cstar))}" fill="none" class="s-va" stroke-dasharray="6 4" stroke-width="1.8"/>')
    d = []
    for i in range(N):
        x1, x2 = L + i * bw, L + (i + 1) * bw
        d.append(f"M{x1:.1f},{y(trail[i]):.1f}H{x2:.1f}")
        if i + 1 < N:
            d.append(f"M{x2:.1f},{y(trail[i]):.1f}V{y(trail[i + 1]):.1f}")
    out.append(f'<path d="{"".join(d)}" fill="none" class="s-ink" stroke-width="2.4"/>')
    out.append(f'<polyline points="{" ".join(f"{L + i * bw + bw / 2:.1f},{y(v):.1f}" for i, v in enumerate(px))}" fill="none" class="s-poc" stroke-width="1.6"/>')
    # position strip
    for i in range(N):
        cls = "f-bull" if pos[i] > 0 else ("f-bear" if pos[i] < 0 else "f-neut")
        out.append(f'<rect x="{L + i * bw:.1f}" y="{B + 18}" width="{bw:.1f}" height="16" class="{cls}" opacity="{"0.9" if pos[i] else "0.45"}"/>')
    out.append(f'<text x="{L}" y="{B + 52}" class="t-small f-muted">Position: green LONG · grey FLAT (the two disagree) · red SHORT</text>')
    out.append(f'<line x1="{L}" x2="{L + 26}" y1="{B + 70}" y2="{B + 70}" class="s-ink" stroke-width="2.4"/><text x="{L + 32}" y="{B + 74}" class="t-small f-ink">trail (six-month): the SIDE</text>')
    out.append(f'<line x1="{L + 300}" x2="{L + 326}" y1="{B + 70}" y2="{B + 70}" class="s-va" stroke-dasharray="6 4" stroke-width="1.8"/><text x="{L + 332}" y="{B + 74}" class="t-small f-ink">momentum boundary: where S turns</text>')
    out.append(f'<line x1="{L + 640}" x2="{L + 666}" y1="{B + 70}" y2="{B + 70}" class="s-poc" stroke-width="1.6"/><text x="{L + 672}" y="{B + 74}" class="t-small f-ink">price</text>')
    out.append(f'<text x="{L}" y="{H - 2}" class="t-tiny f-muted">Schematic, synthetic series. The chart draws the trail only; S and its turning price are in the readout.</text>')
    out.append('</svg>')
    return "\n".join(out)
