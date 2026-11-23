"""anumaan.pine's palette and transparency ladder. Pine's color.new(c, t) is the colour at (100 - t)% opacity."""
from __future__ import annotations

A_SOLID, A_FIRM, A_QUIET, A_FAINT, A_WARM = 0, 40, 65, 80, 90

_DARK = dict(
    UP="#3FB980", DN="#E4776A", UPD="#2A8660", DND="#B4554B", NEUT="#8A97A0", CONE="#B4BEC6", GOLD="#D9B44A",
    TEXT="#C9D1D6", PANEL=("#0D1215", 8),
    POC="#FFB020", VA="#5B8FD6", VWAP="#F06BA8", NODE="#6E7C88", HVN="#8F7BD8", LVN="#C6BBEA", VIOLET="#A87ABF",
)
_LIGHT = dict(
    UP="#08724A", DN="#A8443A", UPD="#5C9E86", DND="#BC7A72", NEUT="#69757E", CONE="#414B53", GOLD="#8A6A0E",
    TEXT="#2B3338", PANEL=("#FFFFFF", 6),
    POC="#B26A00", VA="#2C5C99", VWAP="#A32468", NODE="#8A949B", HVN="#5E4B9E", LVN="#8F7DBB", VIOLET="#6A3F84",
)


def palette(dark: bool) -> dict:
    return dict(_DARK if dark else _LIGHT)


def rgba(hex_: str, transp: float = 0.0) -> str:
    """color.new(hex, transp) as a CSS rgba string."""
    h = hex_.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    a = max(0.0, min(1.0, 1.0 - transp / 100.0))
    return f"rgba({r},{g},{b},{a:.3f})"


def from_gradient(x: float, lo: float, hi: float, c1: tuple[str, float], c2: tuple[str, float]) -> str:
    """color.from_gradient(x, lo, hi, color.new(h1, t1), color.new(h2, t2)): linear in RGB and in opacity, clamped."""
    f = 0.0 if hi == lo else max(0.0, min(1.0, (x - lo) / (hi - lo)))
    (h1, t1), (h2, t2) = c1, c2
    a1, a2 = _rgb(h1), _rgb(h2)
    r, g, b = (round(a1[i] + (a2[i] - a1[i]) * f) for i in range(3))
    op = (1 - t1 / 100.0) + ((1 - t2 / 100.0) - (1 - t1 / 100.0)) * f
    return f"rgba({r},{g},{b},{max(0.0, min(1.0, op)):.3f})"


def _rgb(hex_: str) -> tuple[int, int, int]:
    h = hex_.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
