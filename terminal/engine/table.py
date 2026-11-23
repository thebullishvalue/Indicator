"""Section 9 of anumaan.pine - the table - and the tapes' words, with the script's own text and number formats.

Pine formats numbers with DecimalFormat-style patterns: "#" (no decimals), "#.0" (one, no leading zero),
"0.00", "+0.00;-0.00". `fmt()` follows them for the patterns the script uses.
"""
from __future__ import annotations

import math

NAN = float("nan")


def _na(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def fmt(x: float, pattern: str) -> str:
    if _na(x):
        return "—"
    if ";" in pattern:
        pos, neg = pattern.split(";")
        return fmt(x, pos) if x >= 0 else "-" + fmt(-x, neg.lstrip("-"))
    sign = ""
    if pattern.startswith("+"):
        pattern = pattern[1:]
        sign = "+"
    dec = len(pattern.split(".")[1]) if "." in pattern else 0
    s = f"{abs(x):.{dec}f}"
    if pattern.startswith("#.") and s.startswith("0."):
        s = s[1:]
    if s in ("", "-0"):
        s = "0"
    return ("-" if x < 0 and float(s) != 0 else sign) + s


def f_pct(x, pattern):
    return "—" if _na(x) else fmt(100.0 * x, pattern) + "%"


def f_px(x, decimals):
    return "—" if _na(x) else f"{x:.{decimals}f}"


def st_name(s: int) -> str:
    a = "trend down" if s < 3 else "trend flat" if s < 6 else "trend up"
    b = "closed below the band" if s % 3 == 0 else "closed above the band" if s % 3 == 2 else "inside the band"
    return f"{a} · {b}"


def words(e: dict, t: int) -> dict:
    """The tapes' words on bar t (the script builds them on the last bar)."""
    s = e["series"]
    T, trRaw, ladOk, ladUp, ladDn = s["T"][t], s["trRaw"][t], s["ladOk"][t], int(s["ladUp"][t]), int(s["ladDn"][t])
    regOk, regRaw, rMom, rmS = s["regOk"][t], s["regRaw"][t], s["rMom"][t], s["rmS"][t]
    trTxt = "warming" if _na(T) else ("up " if trRaw == 2 else "down " if trRaw == 0 else "flat ") + fmt(T, "+0.0;-0.0") + "σ"
    if not ladOk:
        ladTxt = ladShort = "warming"
    elif ladUp == 0 and ladDn == 0:
        ladTxt, ladShort = "all four rungs inside", "inside"
    else:
        ladTxt = ((f"{ladUp} of 4 above" if ladUp > 0 else "") + (" · " if ladUp > 0 and ladDn > 0 else "")
                  + (f"{ladDn} of 4 below" if ladDn > 0 else ""))
        ladShort = ((f"{ladUp} above" if ladUp > 0 else "") + (" " if ladUp > 0 and ladDn > 0 else "")
                    + (f"{ladDn} below" if ladDn > 0 else ""))
    regTxt = "warming" if not regOk else "calm" if regRaw == 0 else "stressed" if regRaw == 2 else "normal"
    trWord = "warming" if _na(T) else "up" if trRaw == 2 else "down" if trRaw == 0 else "flat"
    rmWord = "warming" if _na(rMom) else "rising" if rmS == 2 else "falling" if rmS == 0 else "steady"
    return dict(trTxt=trTxt, ladTxt=ladTxt, ladShort=ladShort, regTxt=regTxt, trWord=trWord, rmWord=rmWord)


def rows(e: dict, close: float, decimals: int) -> list[dict]:
    """The table's eight rows on the last bar: [{key, value, tone, tip}]. tone names the script's colour."""
    s, L, inp = e["series"], e["last"], e["inputs"]
    t = e["n"] - 1
    W = words(e, t)
    H = inp.H
    hTxt = f"{H} bars"
    sig = s["sig"][t]
    if _na(sig):
        return [dict(key="ANUMAAN", value=f"warming {t + 1}/{252 + H}", tone="NEUT",
                     tip="The risk forecast needs a year of bars before its first reading.")]
    stopL, stopS, upper, lower = s["stopL"][t], s["stopS"][t], s["upper"][t], s["lower"][t]
    dL = 1.0 - stopL / close
    dS = stopS / close - 1.0
    nF, nMU, nMD, nMS, nMR = L["nF"], L["nMU"], L["nMD"], L["nMS"], L["nMR"]
    cov = 1.0 - (nMU + nMD) / nF if nF > 0 else NAN
    ladOk, ladDn = s["ladOk"][t], int(s["ladDn"][t])
    regRaw, rmS, rMom = s["regRaw"][t], s["rmS"][t], s["rMom"][t]
    E, dial, dialR, dialT = s["E"][t], s["dial"][t], s["dialR"][t], s["dialT"][t]
    st = int(s["st"][t])
    lZ, lNe, lMu, gM = s["lZ"][t], s["lNe"][t], s["lMu"][t], L["gM"]
    proven = 1 if (not _na(lZ) and lZ >= 2) else -1 if (not _na(lZ) and lZ <= -2) else 0
    sH = s["sH"][t]
    bpy = L["bpy"]
    out = [
        dict(key=f"CONE {fmt(inp.cover, '#')}%", value=f"{f_px(lower, decimals)} – {f_px(upper, decimals)}", tone="CONE",
             tip=f"Where the close should be {hTxt} from now, this share of the time."),
        dict(key="LONG STOP", value=f"{f_px(stopL, decimals)} · size {f_pct(inp.risk / 100.0 / dL, '#')}",
             tone="GOLD" if (ladOk and ladDn >= 3) else "DN",
             tip=(f"Touched within {hTxt} {fmt(inp.stop, '#')}% of the time. Size: the position, as a share of equity, that loses "
                  f"{inp.risk}% of equity there. Gold: three or four ladder rungs are below their bands - there it is touched about a quarter of the time.")),
        dict(key="SHORT STOP", value=f"{f_px(stopS, decimals)} · size {f_pct(inp.risk / 100.0 / dS, '#')}", tone="UP",
             tip=f"Touched within {hTxt} {fmt(inp.stop, '#')}% of the time, and the position size that goes with it."),
        dict(key="EXPOSURE", value=f_pct(E, "#"), tone="TEXT",
             tip=(f"The share of a full position to carry: {f_pct(dial, '#')} = risk {f_pct(dialR, '#')}"
                  + ("" if inp.mode == "Risk only" else f" × trend {f_pct(dialT, '#')}")
                  + ", changed in steps. Daily and weekly charts only: on hourly bars it lost to buy and hold.")),
        dict(key="RECORD", value=(f"cone {f_pct(cov, '#')} · stops {fmt(100.0 * nMS / nF if nF > 0 else NAN, '#')}/"
                                  f"{f_pct(nMR / nF if nF > 0 else NAN, '#')}"),
             tone="GOLD" if (not _na(cov) and abs(cov - inp.cover / 100.0) > 0.03) else "TEXT",
             tip=(f"This chart's own record over {nF} forecasts: how often the cone held (target {fmt(inp.cover, '#')}%; last 250: "
                  f"{f_pct(s['covRecent'][t], '#')}) and how often the long / short stop was touched (target {fmt(inp.stop, '#')}%). "
                  "Gold when the cone is more than 3 points off.")),
        dict(key="RISK", value=f"±{f_pct(sH, '#.0')} · {W['regTxt']}" + ("" if (rmS == 1 or _na(rMom)) else f" · {W['rmWord']}"),
             tone="GOLD" if (regRaw == 2 or rmS == 2) else "TEXT",
             tip=(f"One standard move over {hTxt} ({f_pct(sig * math.sqrt(bpy) if not _na(bpy) else NAN, '#')} a year); where risk "
                  f"stands in its last 500 bars; and whether it rose or fell more than 10% over {hTxt}. A rise usually fades.")),
        dict(key="TREND", value=f"{W['trWord']} · ladder {W['ladShort']}",
             tone="UP" if s["trRaw"][t] == 2 and not _na(s["T"][t]) else "DN" if s["trRaw"][t] == 0 and not _na(s["T"][t]) else "NEUT",
             tip=(f"Trend {W['trTxt']}. Ladder: {W['ladTxt']} ({L['h0']}, {H}, {L['h2']}, {L['h3']} bars). "
                  + ("" if st < 0 else f"State: {st_name(st)} - " + (
                      "too few on this chart to judge." if _na(lZ) else
                      f"seen {fmt(lNe, '#')} times, next {hTxt} {fmt(lMu, '+0.00;-0.00')}σ against {fmt(gM, '+0.00;-0.00')}σ usual: "
                      + ("proven positive." if proven == 1 else "proven negative." if proven == -1 else "unproven."))))),
        dict(key="SHARPE", value=f"{fmt(L['shF'], '0.00')} · B&H {fmt(L['shH'], '0.00')}", tone="TEXT",
             tip=(f"Following exposure against buy and hold (B&H) on this chart, one bar late, net of costs. Worst drawdown "
                  f"{f_pct(L['ddF'], '#')} against {f_pct(L['ddH'], '#')}."
                  + (f" Midline rule (long above, flat below): Sharpe {fmt(L['shM'], '0.00')}; {L['mRuns']} runs, "
                     f"{f_pct(L['mWon'] / L['mRuns'] if L['mRuns'] > 0 else NAN, '#')} won, "
                     f"{f_pct(L['mLong'] / L['mRuns'] if L['mRuns'] > 0 else NAN, '#')} lasted 20+ bars." if inp.mid else ""))),
    ]
    return out
