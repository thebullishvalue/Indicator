"""The script's inputs, read from pramana.pine itself - labels, defaults, options, limits, groups and tooltips - so the
settings dialog says exactly what the script's settings say."""
from __future__ import annotations

import re
from pathlib import Path

PINE = Path(__file__).resolve().parents[2] / "pramana.pine"

FIELD = {
    "inpPane": "pane", "inpTapes": "tapes", "inpCone": "cone", "inpLand": "land", "inpMid": "mid", "inpMidMk": "mid_marks",
    "inpTrail": "trail", "inpTbl": "table", "inpPos": "table_pos", "inpMark": "marks", "inpTheme": "theme", "inpH": "H",
    "inpCover": "cover", "inpStop": "stop", "inpRisk": "risk", "inpMode": "mode", "inpCap": "cap", "inpEta": "eta", "inpReg": "reg",
    "inpTrF": "trend_f", "inpFloor": "floor", "inpStep": "step", "inpCost": "cost", "inpTau": "tau", "inpVpMaster": "vp",
    "inpVpIntrabar": "vp_intrabar", "inpVpUseVol": "vp_use_vol", "inpVpBinMode": "vp_bin_mode", "inpVpBinsPerAtr": "vp_bins_per_atr",
    "inpVpBinTicks": "vp_bin_ticks", "inpVpVaPct": "vp_va_pct", "inpVpHistg": "vp_histogram", "inpVpStyle": "vp_style",
    "inpVpWidth": "vp_width", "inpVpNodes": "vp_nodes", "inpVpVa": "vp_va", "inpVpPoc": "vp_poc", "inpVpTrail": "vp_trail",
    "inpVpPrev": "vp_prev", "inpVpNaked": "vp_naked", "inpVpNakedMax": "vp_naked_max", "inpVpNakedAge": "vp_naked_age",
    "inpVpVwap": "vp_vwap", "inpVpIb": "vp_ib", "inpVpIbBars": "vp_ib_bars",
}

_DECL = re.compile(r'^(bool|int|float|string)\s+(inp\w+)\s*=\s*input\.(bool|int|float|string)\((.*)\)\s*$')
_GROUP = re.compile(r'^var string (G_\w+)\s*=\s*"([^"]*)"')


def _str(s: str, key: str):
    m = re.search(key + r'\s*=\s*"((?:[^"\\]|\\.)*)"', s)
    return m.group(1).encode().decode("unicode_escape").encode("latin-1").decode("utf-8") if m else None


def _num(s: str, key: str):
    m = re.search(key + r'\s*=\s*(-?[\d.]+)', s)
    return float(m.group(1)) if m else None


def load() -> list[dict]:
    """[{field, kind, label, default, options, minval, maxval, step, tooltip, group}] in the script's order."""
    groups, out = {}, []
    for line in PINE.read_text(encoding="utf-8").splitlines():
        g = _GROUP.match(line.strip())
        if g:
            groups[g.group(1)] = g.group(2)
            continue
        m = _DECL.match(line.strip())
        if not m or m.group(2) not in FIELD:
            continue
        kind, args = m.group(3), m.group(4)
        first = re.match(r'\s*("(?:[^"\\]|\\.)*"|[^,]+)\s*,\s*"((?:[^"\\]|\\.)*)"', args)
        default_raw, label = first.group(1).strip(), first.group(2)
        default = (default_raw == "true") if kind == "bool" else default_raw.strip('"') if kind == "string" else float(default_raw)
        opts = re.search(r'options\s*=\s*\[([^\]]*)\]', args)
        grp = re.search(r'group\s*=\s*(G_\w+)', args)
        out.append(dict(field=FIELD[m.group(2)], kind=kind, label=label.strip(), indent=len(label) - len(label.lstrip()),
                        default=int(default) if kind == "int" else default,
                        options=[o.strip().strip('"') for o in opts.group(1).split(",")] if opts else None,
                        minval=_num(args, "minval"), maxval=_num(args, "maxval"), step=_num(args, "step"),
                        tooltip=_str(args, "tooltip"), group=groups.get(grp.group(1), "") if grp else ""))
    return out
