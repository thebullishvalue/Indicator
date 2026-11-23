"""Pramana terminal components: the design system's command bar, panel chrome, chips and metric cards (the markup
Tattva, Pragyam and Arthagati share, so theme.css styles them unchanged), plus the terminal's own blocks."""
from __future__ import annotations

import html as H
from contextlib import contextmanager

import streamlit as st


def chip(label: str, tone: str = "neutral") -> str:
    return f'<span class="chip chip-{H.escape(tone)}">{H.escape(label)}</span>'


def command_bar(*, name: str, description: str, price: float | None, change_pct: float | None, decimals: int,
                meta: list[tuple[str, str]], status: tuple[str, str] | None = None) -> None:
    """Identity, then value, then trust - the design system's reading order."""
    quote = ""
    if price is not None:
        chg = change_pct or 0.0
        cls = "up" if chg > 0.005 else "down" if chg < -0.005 else "flat"
        arrow = "▲" if cls == "up" else "▼" if cls == "down" else "▬"
        quote = (f'<div class="cb-quote"><span class="px">{price:,.{decimals}f}</span>'
                 f'<span class="chg {cls}">{arrow} {abs(chg):.2f}%</span></div>')
    meta_html = "".join(f'<div class="cb-meta"><span class="k">{H.escape(k)}</span><span class="v">{H.escape(v)}</span></div>'
                        for k, v in meta if v)
    st.markdown(
        f'<div class="command-bar"><div class="cb-left">'
        f'<div class="cb-brand"><span class="mark">PRA<span class="accent-ink">MANA</span></span><span class="sub">प्रमाण · terminal</span></div>'
        f'<div class="cb-instrument"><span class="eyebrow">{H.escape(description)}</span><span class="sym">{H.escape(name)}</span></div>'
        f'{quote}</div><div class="cb-right">{meta_html}{chip(*status) if status else ""}</div></div>',
        unsafe_allow_html=True,
    )


def panel_header(title: str = "", *, context: str = "", meta: str = "", chip_: tuple[str, str] | None = None) -> None:
    if not (title or context or meta or chip_):
        return
    left = (f'<span class="ph-title">{H.escape(title)}</span>' if title else "") + (
        f'<span class="ph-context">{H.escape(context)}</span>' if context else "")
    right = (f"<span>{H.escape(meta)}</span>" if meta else "") + (chip(*chip_) if chip_ else "")
    st.markdown(f'<div class="panel-hdr"><div class="ph-left">{left}</div><div class="ph-right">{right}</div></div>',
                unsafe_allow_html=True)


@contextmanager
def panel(key: str, title: str = "", *, context: str = "", meta: str = "", chip_: tuple[str, str] | None = None, footer: str = ""):
    with st.container(key=f"panel-{key}"):
        panel_header(title, context=context, meta=meta, chip_=chip_)
        yield
        if footer:
            st.markdown(f'<div class="panel-foot">{footer}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, subtext: str = "", tone: str = "neutral", tooltip: str = "") -> None:
    tip = (f'<div class="metric-tooltip" data-tooltip="{H.escape(tooltip)}"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
           f'stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>'
           f'<line x1="12" y1="17" x2="12.01" y2="17"/></svg><span class="metric-tooltip-text">{H.escape(tooltip)}</span></div>') if tooltip else ""
    sub = f'<div class="sub-metric">{H.escape(subtext)}</div>' if subtext else ""
    st.markdown(f'<div class="metric-card {H.escape(tone)}"><span class="label">{H.escape(label)}</span><h2>{H.escape(value)}</h2>{sub}{tip}</div>',
                unsafe_allow_html=True)


def kpi_strip(items: list[dict], key: str, max_cols: int = 6) -> None:
    with st.container(key=key):
        for i in range(0, len(items), max_cols):
            row = items[i:i + max_cols]
            for c, it in zip(st.columns(len(row), gap="small"), row):
                with c:
                    metric_card(it["label"], it["value"], it.get("subtext", ""), it.get("tone", "neutral"), it.get("tooltip", ""))


def readout(rows: list[dict]) -> None:
    """The script's table, as a rail block: key on the left, value in the script's colour, tooltip on hover."""
    body = "".join(f'<div class="ro-row" title="{H.escape(r["tip"])}"><span class="ro-k">{H.escape(r["key"])}</span>'
                   f'<span class="ro-v" style="color:{r["color"]}">{H.escape(r["value"])}</span></div>' for r in rows)
    st.markdown(f'<div class="readout">{body}</div>', unsafe_allow_html=True)


def kv_list(rows: list[tuple[str, str]], cls: str = "kv") -> None:
    body = "".join(f'<div class="kv-row"><span class="kv-k">{H.escape(k)}</span><span class="kv-v">{v}</span></div>' for k, v in rows)
    st.markdown(f'<div class="{cls}">{body}</div>', unsafe_allow_html=True)


def note(text: str) -> None:
    st.markdown(f'<div class="t-note">{text}</div>', unsafe_allow_html=True)


# ── the watchlist: a two-way component in plain JavaScript (ui/static/watchlist) ──────────────────────────────────
import streamlit.components.v1 as _components  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_WATCH = _components.declare_component("pramana_watchlist", path=str(_Path(__file__).parent / "static" / "watchlist"))


def watchlist(rows: list[dict], tokens: dict, key: str = "watchlist"):
    """rows: [{sym, desc, last, chg, pct, dec, active}]. Returns {symbol, nonce} for the row last clicked, or None."""
    return _WATCH(rows=rows, tokens=tokens, key=key, default=None)


def table(df, *, fmt: dict | None = None, tone: dict | None = None, mark: int | None = None, align_left: tuple = ()) -> None:
    """A themed HTML table - the design system's tables are HTML so Paper restyles them (st.dataframe's grid cannot).

    fmt: {column: callable(value) -> str}. tone: {column: callable(value) -> css colour or None}. mark: row to highlight."""
    fmt, tone = fmt or {}, tone or {}
    cols = list(df.columns)
    head = "".join(f'<th class="{"l" if c in align_left else ""}">{H.escape(str(c))}</th>' for c in cols)
    body = []
    for i, row in enumerate(df.itertuples(index=False)):
        cells = []
        for c, v in zip(cols, row):
            txt = fmt[c](v) if c in fmt else ("—" if v is None or (isinstance(v, float) and v != v) else str(v))
            col = tone[c](v) if c in tone else None
            style = f' style="color:{col}"' if col else ""
            cells.append(f'<td class="{"l" if c in align_left else ""}"{style}>{H.escape(txt)}</td>')
        body.append(f'<tr class="{"mark" if mark == i else ""}">{"".join(cells)}</tr>')
    st.markdown(f'<div class="t-table"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>',
                unsafe_allow_html=True)
