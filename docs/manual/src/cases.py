"""Real-data case plates for the manual: research/case_extract.py's output, drawn.

Each plate is the last 300 daily bars of one market to the data's end: the
close, the rolling 126-bar value area and POC, the acceptance trail coloured as
Pragati colours it with Accepted momentum on (hue the side, intensity the size,
neutral when flat), probe onsets (gold x), flips (rings), and the traded weight
of the tested sizing underneath. Nothing here is synthetic.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
COST = {"index": 5, "etf": 5, "fx": 3, "commodity": 8, "us_stock": 10, "nse_stock": 15, "crypto": 20}
NAMES = {"NIFTY_50": "NIFTY 50", "RELIANCE": "RELIANCE", "GOLD": "Gold (USD)", "USDINR": "USD/INR", "BTCUSDT": "BTC/USDT", "BANKBEES": "BANKBEES"}


def load(sym):
    return json.load(open(os.path.join(HERE, "cases", sym + ".json")))


def campaigns(j):
    """Every campaign of the traded weight inside the window: a maximal run of one sign (0 = flat)."""
    w, o, dates, cls = j["window"]["w"], j["window"]["open"], j["window"]["date"], j["class"]
    cost = COST.get(cls, 10) / 1e4
    sg = [0 if (x is None or abs(x) < 1e-12) else (1 if x > 0 else -1) for x in w]
    n, out, t = len(w), [], 0
    while t < n:
        k = t
        while k + 1 < n and sg[k + 1] == sg[t]:
            k += 1
        if sg[t] != 0:
            eq = 1.0
            for i in range(t, k + 1):
                if i + 2 >= n:
                    break
                prev = w[i - 1] if i > 0 and w[i - 1] is not None else 0.0
                eq *= 1 + w[i] * (o[i + 2] / o[i + 1] - 1.0) - cost * abs(w[i] - prev)
            done = k + 2 < n
            out.append({"start": dates[t], "end": dates[k], "bars": k - t + 1, "side": sg[t], "w_max": max(abs(w[i]) for i in range(t, k + 1)),
                        "ret": eq - 1.0, "move": (o[min(k + 2, n - 1)] / o[t + 1] - 1.0) if t + 1 < n else 0.0, "open": not done})
        t = k + 1
    return out


def fmt_px(v, ref):
    if v is None:
        return "—"
    if ref >= 1000:
        return f"{v:,.0f}"
    if ref >= 100:
        return f"{v:,.1f}"
    return f"{v:,.2f}"


def plate(sym, letters=()):
    """letters: [(date, 'A'), ...] to label bars the narrative refers to."""
    j = load(sym)
    win = j["window"]
    n = len(win["close"])
    W, H = 900, 372
    L, R, T, B = 16, 820, 18, 270
    hi = max(v for v in win["high"] + [x for x in win["vah"] if x is not None] + [x for x in win["lvl"] if x is not None])
    lo = min(v for v in win["low"] + [x for x in win["val"] if x is not None] + [x for x in win["lvl"] if x is not None])
    pad = (hi - lo) * 0.04
    hi, lo = hi + pad, lo - pad
    y = lambda v: B - (v - lo) / (hi - lo) * (B - T)
    bw = (R - L) / n
    X = lambda i: L + i * bw + bw / 2
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{NAMES[sym]}, the last {n} daily bars, with the acceptance trail and Accepted momentum">']
    out.append(f'<rect x="{L}" y="{T - 6}" width="{R - L}" height="{B - T + 12}" class="f-surface s-line" stroke-width="1"/>')
    # month gridlines and labels
    prev = None
    for i, d in enumerate(win["date"]):
        m = d[:7]
        if m != prev and prev is not None:
            out.append(f'<line x1="{L + i * bw:.1f}" x2="{L + i * bw:.1f}" y1="{T - 6}" y2="{B + 6}" class="s-line" stroke-width="0.6"/>')
            if int(d[5:7]) in (1, 4, 7, 10):
                lab = d[:4] if d[5:7] == "01" else ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(d[5:7])]
                out.append(f'<text x="{L + i * bw + 3:.1f}" y="{B + 18}" class="t-tiny f-muted">{lab}{" " + d[:4] if lab != d[:4] else ""}</text>')
        prev = m
    # price axis
    for k in range(5):
        v = lo + (hi - lo) * (k + 0.5) / 5
        out.append(f'<line x1="{R}" x2="{R + 4}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="s-muted" stroke-width="0.8"/>')
        out.append(f'<text x="{R + 7}" y="{y(v) + 4:.1f}" class="t-tiny f-muted">{fmt_px(v, hi)}</text>')
    # value ribbon (rolling 126-bar value area) and POC
    seg, segs = [], []
    for i in range(n):
        if win["val"][i] is None:
            if seg:
                segs.append(seg)
            seg = []
        else:
            seg.append(i)
    if seg:
        segs.append(seg)
    for sg in segs:
        top = " ".join(f"{L + i * bw:.1f},{y(win['vah'][i]):.1f} {L + (i + 1) * bw:.1f},{y(win['vah'][i]):.1f}" for i in sg)
        bot = " ".join(f"{L + (i + 1) * bw:.1f},{y(win['val'][i]):.1f} {L + i * bw:.1f},{y(win['val'][i]):.1f}" for i in reversed(sg))
        out.append(f'<polygon points="{top} {bot}" class="f-slate" opacity="0.16"/>')
        out.append(f'<polyline points="{" ".join(f"{X(i):.1f},{y(win["poc"][i]):.1f}" for i in sg)}" fill="none" class="s-slate" stroke-width="1" stroke-dasharray="2 3"/>')
    # high-low bars and the close
    for i in range(n):
        out.append(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{y(win["high"][i]):.1f}" y2="{y(win["low"][i]):.1f}" class="s-muted" stroke-width="0.7" opacity="0.55"/>')
    out.append(f'<polyline points="{" ".join(f"{X(i):.1f},{y(c):.1f}" for i, c in enumerate(win["close"]))}" fill="none" class="s-ink" stroke-width="1.3"/>')
    # the trail: hue its side, intensity the AM size, neutral when flat
    for i in range(n):
        if win["dir"][i] == 0 or win["lvl"][i] is None:
            continue
        a = win["am"][i]
        if a is None or abs(a) < 1e-12:
            cls, op = "s-neut", 0.9
        else:
            cls = "s-bull" if win["dir"][i] > 0 else "s-bear"
            op = 1.0 if abs(a) >= 0.5 else 0.75 if abs(a) >= 0.25 else 0.5
        x1, x2 = L + i * bw, L + (i + 1) * bw
        out.append(f'<line x1="{x1:.1f}" x2="{x2 + 0.3:.1f}" y1="{y(win["lvl"][i]):.1f}" y2="{y(win["lvl"][i]):.1f}" class="{cls}" stroke-width="2.6" opacity="{op}"/>')
        if i + 1 < n and win["lvl"][i + 1] is not None and win["lvl"][i + 1] != win["lvl"][i] and win["dir"][i + 1] != 0:
            out.append(f'<line x1="{x2:.1f}" x2="{x2:.1f}" y1="{y(win["lvl"][i]):.1f}" y2="{y(win["lvl"][i + 1]):.1f}" class="{cls}" stroke-width="1.4" opacity="{op}"/>')
    # probe onsets and flips
    for i in range(n):
        if win["onset"][i]:
            cx, cy = X(i), y(win["close"][i])
            out.append(f'<path d="M{cx - 4:.1f},{cy - 4:.1f}L{cx + 4:.1f},{cy + 4:.1f}M{cx - 4:.1f},{cy + 4:.1f}L{cx + 4:.1f},{cy - 4:.1f}" class="s-gold" stroke="var(--gold)" stroke-width="2"/>')
        if win["flip"][i]:
            out.append(f'<circle cx="{X(i):.1f}" cy="{y(win["close"][i]):.1f}" r="6" fill="none" stroke="var(--ink)" stroke-width="1.6"/>')
    # letters
    idx = {d: i for i, d in enumerate(win["date"])}
    for d, lab in letters:
        if d not in idx:
            continue
        i = idx[d]
        cy = min(y(win["high"][i]), y(win["lvl"][i]) if win["lvl"][i] else 1e9) - 14
        cy = max(cy, T + 10)
        out.append(f'<circle cx="{X(i):.1f}" cy="{cy:.1f}" r="8.5" class="f-ink"/><text x="{X(i):.1f}" y="{cy + 4:.1f}" text-anchor="middle" class="t-callout">{lab}</text>')
    # traded weight strip
    S0, S1 = B + 30, B + 92
    mid = (S0 + S1) / 2
    wm = max(0.25, max(abs(x) for x in win["w"] if x is not None))
    out.append(f'<line x1="{L}" x2="{R}" y1="{mid:.1f}" y2="{mid:.1f}" class="s-line" stroke-width="1"/>')
    for i in range(n):
        x = win["w"][i]
        if x is None or abs(x) < 1e-9:
            continue
        hgt = abs(x) / wm * (S1 - S0) / 2
        out.append(f'<rect x="{L + i * bw:.1f}" y="{mid - hgt if x > 0 else mid:.1f}" width="{bw + 0.2:.1f}" height="{hgt:.1f}" class="{"f-bull" if x > 0 else "f-bear"}" opacity="0.85"/>')
    out.append(f'<text x="{R + 7}" y="{S0 + 8:.1f}" class="t-tiny f-muted">+{wm:.2f}</text><text x="{R + 7}" y="{S1:.1f}" class="t-tiny f-muted">−{wm:.2f}</text>')
    out.append("</svg>")
    return "\n".join(out)
