"""The plan as a ticket, after VAAYDO (thebullishvalue/Vaaydo), which takes its stops and ranges from this script.

VAAYDO turns Anumaan's risk into an order: a side, an entry at the next open, a trailing stop, a size and a range. Its
rules, as its ledger keeps them (vaaydo/ledger.py, forecast.py):

    entry   the OPEN of the session after the decision; the reference before it is the last close
    stop    trailing on closes: k x best close since entry, k = 1 + 1.5 x (the script's 20%-touch stop / close - 1),
            fixed at the decision; the best starts at the fill. Decided on a close, filled at the next open.
    paths   filtered historical simulation: each bar's gap and close-to-close return over the risk forecast that
            prevailed when it happened (its shape: fat tails, skew, gap days, without its old level), bootstrapped in
            blocks of 5 and rescaled to today's forecast. Centred: no directional view. The script finds risk
            forecastable and direction not, and VAAYDO's tests agree, so the paths carry no drift.

R is the risk taken: the distance from the fill to the first stop. Results are in R, after costs (the script's cost,
on each side). The same rule is replayed from every past bar of the chart, so the simulation's claims sit beside this
chart's own record, the way the script audits its cone and stops.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

STOP_MULT = 1.5
BLOCK = 5
N_PATHS = 4000


def k_factor(close: float, stop: float, mult: float = STOP_MULT) -> float:
    """The trailing multiple: below 1 for a long, above 1 for a short."""
    return 1.0 + mult * (stop / close - 1.0)


def shocks(o: np.ndarray, c: np.ndarray, sig: np.ndarray) -> np.ndarray:
    """(m, 2) standardised (close-to-close, gap) pairs: bar t over the risk forecast made at t-1. Centred on no drift and
    scaled to unit variance, so the paths take today's forecast as their level."""
    with np.errstate(divide="ignore", invalid="ignore"):
        s = sig[:-1]
        r = np.log(c[1:] / c[:-1]) / s
        g = np.log(o[1:] / c[:-1]) / s
    ok = np.isfinite(r) & np.isfinite(g)
    z = np.clip(np.column_stack([r[ok], g[ok]]), -10, 10)
    if len(z) < 60:
        return np.empty((0, 2))
    z[:, 0] -= z[:, 0].mean()
    sd = z[:, 0].std()
    return z / sd if sd > 0 else np.empty((0, 2))


def _rule(O: np.ndarray, C: np.ndarray, side: int, k: np.ndarray, cost: float) -> tuple[np.ndarray, np.ndarray]:
    """The trailing stop on price windows. O, C: (n, h+1) opens and closes of the bars after the decision (bar 0 is the
    fill). k: (n,) multiples. Returns R by bar (n, h), locked once stopped, and the bar (1-based) whose close stopped it
    (0 if never)."""
    n, w = C.shape
    h = w - 1
    E = O[:, 0]
    Cm = C[:, :h]
    if side > 0:
        best = np.maximum.accumulate(np.maximum(Cm, E[:, None]), axis=1)
        hit = Cm <= best * k[:, None]
    else:
        best = np.minimum.accumulate(np.minimum(Cm, E[:, None]), axis=1)
        hit = Cm >= best * k[:, None]
    first = np.where(hit.any(axis=1), hit.argmax(axis=1), h)            # 0-based bar of the stopping close, h if none
    risk = E * np.abs(1.0 - k)
    rows = np.arange(n)
    fill = O[rows, np.minimum(first + 1, h)]                             # the next open after the stopping close
    r_mtm = side * (Cm - E[:, None]) / risk[:, None] - cost / np.abs(1.0 - k)[:, None]
    r_exit = side * (fill - E) / risk - cost / np.abs(1.0 - k)
    bars = np.arange(h)[None, :]
    R = np.where(bars >= first[:, None], r_exit[:, None], r_mtm)
    return R, np.where(first < h, first + 1, 0)


@dataclass
class Outcome:
    R: np.ndarray            # (n, h) R by bar
    stopped_at: np.ndarray   # (n,) bar whose close stopped it, 0 if never
    n: int

    def at(self, h: int) -> dict:
        r = self.R[:, h - 1]
        s = (self.stopped_at > 0) & (self.stopped_at <= h)
        return dict(stopped=float(s.mean()), median=float(np.median(r)), mean=float(r.mean()), p10=float(np.quantile(r, 0.10)),
                    p90=float(np.quantile(r, 0.90)), ge1=float((r >= 1).mean()), ge2=float((r >= 2).mean()))

    def band(self, qs=(0.10, 0.25, 0.50, 0.75, 0.90)) -> np.ndarray:
        return np.quantile(self.R, qs, axis=0)

    def stopped_by_bar(self) -> np.ndarray:
        h = self.R.shape[1]
        return np.array([((self.stopped_at > 0) & (self.stopped_at <= j)).mean() for j in range(1, h + 1)])


def simulate(z: np.ndarray, side: int, k: float, sig_now: float, h: int, cost: float, n: int = N_PATHS,
             block: int = BLOCK, seed: int = 7) -> Outcome | None:
    """The ticket on n bootstrapped paths of h bars after the fill, at today's risk."""
    if len(z) < 60 or not (sig_now > 0) or not math.isfinite(k):
        return None
    rng = np.random.default_rng(seed)
    w = h + 1
    nb = int(math.ceil(w / block))
    starts = rng.integers(0, len(z) - block, size=(n, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n, nb * block)[:, :w]
    r, g = z[idx, 0] * sig_now, z[idx, 1] * sig_now
    logC = np.cumsum(r, axis=1)                                           # closes of bars 0..h; the decision's close is 0
    logO = np.concatenate([np.zeros((n, 1)), logC[:, :-1]], axis=1) + g
    R, at = _rule(np.exp(logO), np.exp(logC), side, np.full(n, k), cost)
    return Outcome(R, at, n)


def replay(o: np.ndarray, c: np.ndarray, stop: np.ndarray, side: int, h: int, cost: float) -> Outcome | None:
    """The same ticket opened after every past bar of the chart that had a stop, held h bars or to its stop."""
    n = len(c)
    i = np.arange(n - h - 1)
    i = i[np.isfinite(stop[i]) & (stop[i] > 0)]
    if len(i) < 30:
        return None
    k = k_factor(c[i], stop[i])
    win = i[:, None] + 1 + np.arange(h + 1)[None, :]
    R, at = _rule(o[win], c[win], side, k, cost)
    return Outcome(R, at, len(i))
