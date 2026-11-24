"""Anumaan terminal - the design system's CSS (Graphite / Paper, from Tattva, shared with Pragyam and Arthagati).

theme.css is the shared stylesheet, unchanged apart from its header: the dark token block, every component rule
reading var(--token). Paper is a second, smaller :root injected after it. terminal.css adds the terminal's own
layout: the toolbar, the chart frame, the rail and the bottom panel.
"""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

HERE = Path(__file__).parent
VERSION = "1.2.1"
PRODUCT = "Anumaan"

LIGHT_TOKENS = """
:root {
    /* Counterpart to the dark block's declaration — see the note there. This
       is what keeps Paper light on a device whose system theme is dark; the
       two together mean the OS preference is never consulted in either
       direction. */
    color-scheme: light;

    /* Paper — the reporting/print theme. Not "dark inverted": a near-white
       ground reflects far more light than a graphite one, so the semantic
       hues are DEEPENED rather than reused (a #2CA36B that clears 5.9:1 on
       graphite manages 2.6:1 on white and would be illegible). Every value
       below clears WCAG AA on both --surface-1 and --surface-2. */
    --bg:            #F4F6F8;
    --surface-1:     #FFFFFF;
    --surface-2:     #EEF1F5;
    --surface-3:     #E2E7EE;

    --ink:           #141920;   /* 17.7:1 on white */
    --ink-secondary: #3D4756;   /*  9.4:1 */
    --ink-tertiary:  #5E6979;   /*  5.6:1 */
    --ink-quaternary:#6B7482;   /*  4.6:1 */
    --spike: rgba(90, 100, 114, 0.45);

    --accent:        #2B5FD9;   /* 5.6:1 */
    --long:          #0F7A54;   /* 5.3:1 */
    --short:         #C0392F;   /* 5.4:1 */
    --caution:       #96660F;   /* 5.0:1 */
    --system:        #15708C;   /* 5.6:1 */
    --neutral:       #5A6472;   /* 6.0:1 */

    --accent-fill:   rgba(43, 95, 217, 0.07);
    --long-fill:     rgba(15, 122, 84, 0.08);
    --short-fill:    rgba(192, 57, 47, 0.07);
    --caution-fill:  rgba(150, 102, 15, 0.08);
    --system-fill:   rgba(21, 112, 140, 0.07);
    --accent-edge:   rgba(43, 95, 217, 0.32);
    --long-edge:     rgba(15, 122, 84, 0.32);
    --short-edge:    rgba(192, 57, 47, 0.30);
    --caution-edge:  rgba(150, 102, 15, 0.30);
    --system-edge:   rgba(21, 112, 140, 0.28);

    --line:          rgba(15, 23, 42, 0.10);
    --line-strong:   rgba(15, 23, 42, 0.18);
    --line-faint:    rgba(15, 23, 42, 0.05);

    --violet:        #6A4BC0;   /* 6.2:1 */
    --violet-fill:   rgba(106, 75, 192, 0.07);
    --violet-edge:   rgba(106, 75, 192, 0.30);

    --shadow-sm:     0 1px 2px rgba(15, 23, 42, 0.06);
    --shadow-pop:    0 10px 24px rgba(15, 23, 42, 0.12);
}
/* Two rules cannot be expressed as a token swap. On paper the primary
   button's hover needs a DARKER accent (the dark theme's is lighter), and
   the sidebar rail reads better as the tinted surface with the content
   area white — the reverse of the dark theme's arrangement. */
[data-testid="stBaseButton-primary"]:hover { background: #244EB4 !important; border-color: #244EB4 !important; }
[data-testid="stSidebar"] { background: var(--surface-2); }

/* ── Reclaiming Streamlit's own natives ──────────────────────────────────
   THIS is why Paper mode looked half-broken. `.streamlit/config.toml` pins
   Streamlit to `base = "dark"` with `textColor = #E6EAF1`, and that is a
   STATIC config — it cannot follow a runtime theme switch. So on Paper the
   token swap repaints every surface white while Streamlit keeps colouring
   its own internals near-white: the navigation labels, button faces, input
   text and placeholders all went white-on-white. "Some fonts or elements
   show up, some do not" is precisely a light ground wearing a dark-theme
   text colour.

   Anything the app styles through its own classes was already fine — which
   is why the effect looked arbitrary rather than total. The rules below
   claim the remainder. They live in LIGHT_TOKENS (not theme.css) because on
   the dark theme Streamlit's defaults are already correct and overriding
   them there would be noise. */
[data-testid="stSidebarNavLink"],
[data-testid="stSidebarNavLink"] span,
[data-testid="stSidebarNavLink"] p { color: var(--ink-tertiary) !important; }
[data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebarNavLink"]:hover span { color: var(--ink) !important; }
[data-testid="stSidebarNavLink"][aria-current="page"],
[data-testid="stSidebarNavLink"][aria-current="page"] span { color: var(--ink) !important; }
[data-testid="stNavSectionHeader"] { color: var(--ink-quaternary) !important; }

/* Buttons: Streamlit's dark-base face is a dark pill, which on paper reads
   as an inverted, "pressed" control sitting on a white rail. */
[data-testid^="stBaseButton"]:not([data-testid^="stBaseButton-primary"]) {
    background: var(--surface-1) !important;
    color: var(--ink-secondary) !important;
    border-color: var(--line-strong) !important;
}
[data-testid^="stBaseButton"]:not([data-testid^="stBaseButton-primary"]):hover {
    background: var(--surface-2) !important; color: var(--ink) !important;
}
[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important; color: #FFFFFF !important;
}

/* Inputs, their text, and — the easiest one to miss — their placeholders.
   The select's own FACE needs claiming too: BaseWeb paints it from
   Streamlit's dark base, so on Paper the dropdown stayed a dark well with
   dark text while the rail around it went white. */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div { color: var(--ink) !important; }
input::placeholder, textarea::placeholder { color: var(--ink-quaternary) !important; opacity: 1; }
.stSelectbox [data-baseweb="select"] > div,
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: var(--surface-1) !important;
    border-color: var(--line-strong) !important;
}
.stSelectbox [data-baseweb="select"] svg { color: var(--ink-quaternary) !important; }
/* The open menu is a portal at the document root — it inherits nothing from
   the app, so it needs the light surface named explicitly. Selectors match
   the RENDERED markup: the popover shell and a bare `ul` (the listbox role
   lives on the option, not the list). */
[data-baseweb="popover"] > div,
[data-baseweb="popover"] ul,
[data-baseweb="popover"] [data-baseweb="menu"] {
    background: var(--surface-1) !important;
    color: var(--ink) !important;
    border-color: var(--line-strong) !important;
}
[data-baseweb="popover"] [role="option"] { color: var(--ink-secondary) !important; }
[data-baseweb="popover"] [role="option"]:hover { background: var(--surface-2) !important; }
[data-baseweb="popover"] [role="option"][aria-selected="true"] { color: var(--ink) !important; }
/* Tooltips are portalled to the document root like the menus, and Streamlit
   paints them from its static dark base — a black slab with white text on a
   white page. The inner div carries the background, so both are named. */
[data-baseweb="tooltip"], [data-baseweb="tooltip"] > div,
[role="tooltip"], [role="tooltip"] > div {
    background: var(--surface-3) !important;
    color: var(--ink) !important;
    border-color: var(--line-strong) !important;
}

/* Segmented controls and body copy. */
[data-testid="stButtonGroup"] button { color: var(--ink-tertiary) !important; }
[data-testid="stButtonGroup"] button[data-testid$="Active"] { color: var(--ink) !important; }
[data-testid="stMain"], [data-testid="stSidebar"] { color: var(--ink); }
.stMarkdown, .stMarkdown p, .stMarkdown li { color: var(--ink-secondary); }
"""


def inject_css(theme: str = "dark") -> None:
    css = (HERE / "theme.css").read_text(encoding="utf-8") + "\n" + (HERE / "terminal.css").read_text(encoding="utf-8")
    if theme == "light":
        css += LIGHT_TOKENS
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ── The progress card ─────────────────────────────────────────────────────────
# The family's one loading surface, in place of Streamlit's spinner: a card with the phase, the step, what it is
# working on and a bar that only moves forward. A chart is built in four phases; the percentage picks the phase.
RUN_PHASES = (
    (1, 0, 29, "Symbol & Bars"),
    (2, 30, 59, "Anumaan Engine"),
    (3, 60, 84, "Volume Profile"),
    (4, 85, 100, "Watchlist"),
)


def _phase_of(pct: int) -> "tuple[int, int, str]":
    """Which phase a percentage falls in, as ``(n, total, name)``."""
    for n, lo, hi, name in RUN_PHASES:
        if lo <= pct <= hi:
            return n, len(RUN_PHASES), name
    return len(RUN_PHASES), len(RUN_PHASES), RUN_PHASES[-1][3]


def progress_bar(slot, pct: int, label: str, sub: str = "") -> None:
    """Render the progress card into an ``st.empty()`` slot (the family's markup; theme.css styles it)."""
    state = " complete" if pct >= 100 else ""
    n, total, phase = _phase_of(pct)
    slot.markdown(
        f'<div class="progress-card{state}">'
        f'<div class="progress-phase">Phase {n} of {total}'
        f'<span class="pp-name">{html.escape(phase)}</span></div>'
        f'<div class="progress-label">'
        f'<span class="pulse-dot"></span>{html.escape(label)}'
        f'<span class="progress-pct">{int(pct)}%</span>'
        f'</div>'
        + (f'<div class="progress-sub">{html.escape(sub)}</div>' if sub else "")
        + f'<div class="progress-track"><i style="width:{int(pct)}%"></i></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
