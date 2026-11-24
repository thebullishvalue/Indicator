/* Anumaan on Lightweight Charts. Reads window.ANUMAAN = {p, tokens, title, height}.
   Pane 0: candles, volume, the script's overlays and its drawings. Pane 1: the Anumaan pane.
   Drawings are primitives positioned in bar indices (logical) and prices, as the Pine script positions them. */
(function () {
  const { p, tokens: K, title, height } = window.ANUMAAN;
  // unpack the compact payload: per-bar series are {v, c} aligned with p.times, colours indices into p.colours
  const U = (o) => p.times.map((t, i) => (o.v[i] === null || o.v[i] === undefined) ? { time: t } :
    (o.c ? { time: t, value: o.v[i], color: p.colours[o.c[i]] } : { time: t, value: o.v[i] }));
  p.bars = p.times.map((t, i) => ({ time: t, open: p.o[i], high: p.h[i], low: p.l[i], close: p.c[i] }));
  ['cols', 'bandU', 'bandD', 'tT', 'tL', 'tR', 'tM', 'proofF', 'proofH', 'landU', 'landD', 'stopLh', 'stopSh', 'midl', 'vwap', 'vols']
    .forEach(k => { p[k] = U(p[k]); });
  Object.keys(p.trails).forEach(k => { p.trails[k] = U(p.trails[k]); });
  const LW = LightweightCharts;
  const el = document.getElementById('chart');
  el.style.height = '100vh';                // the frame's height is set by the page, per screen size
  const dec = p.decimals;
  const fmtPx = (x) => (x === null || x === undefined || Number.isNaN(x)) ? '—' :
    Number(x).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }).replace('-', '\u2212');   // the family's minus
  const fmtVol = (v) => v >= 1e9 ? (v / 1e9).toFixed(2) + 'B' : v >= 1e6 ? (v / 1e6).toFixed(2) + 'M' : v >= 1e3 ? (v / 1e3).toFixed(2) + 'K' : v.toFixed(0);

  const chart = LW.createChart(el, {
    autoSize: true,
    layout: {
      background: { type: 'solid', color: K.bg }, textColor: K.axis, fontFamily: K.font, fontSize: 11,
      attributionLogo: false,          // the licence's link to tradingview.com is in the page footer
      panes: { separatorColor: K.separator, separatorHoverColor: K.separatorHover, enableResize: true },
    },
    grid: { vertLines: { color: K.grid }, horzLines: { color: K.grid } },
    crosshair: { mode: LW.CrosshairMode.Normal,
      vertLine: { color: K.crosshair, style: LW.LineStyle.LargeDashed, labelBackgroundColor: K.crosshairLabel },
      horzLine: { color: K.crosshair, style: LW.LineStyle.LargeDashed, labelBackgroundColor: K.crosshairLabel } },
    rightPriceScale: { borderColor: K.border, scaleMargins: { top: 0.08, bottom: 0.06 } },
    timeScale: { borderColor: K.border, timeVisible: p.intraday, secondsVisible: false, rightOffset: 6, barSpacing: 7, minBarSpacing: 0.5 },
    localization: { priceFormatter: fmtPx },
  });

  // ── pane 0 ─────────────────────────────────────────────────────────────
  const candles = chart.addSeries(LW.CandlestickSeries, {
    upColor: K.candleUp, downColor: K.candleDown, borderVisible: false, wickUpColor: K.candleUp, wickDownColor: K.candleDown,
    priceFormat: { type: 'price', precision: dec, minMove: p.mintick }, priceLineStyle: LW.LineStyle.Dotted,
  }, 0);
  candles.setData(p.bars.concat(p.future.map(t => ({ time: t }))));

  let vol = null;
  if (p.showVolume) {
    vol = chart.addSeries(LW.HistogramSeries, { priceScaleId: 'vol', priceFormat: { type: 'volume' }, lastValueVisible: false, priceLineVisible: false }, 0);
    vol.setData(p.vols);
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 }, visible: false });
  }

  const quiet = { lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false };
  const addLine = (data, color, opts = {}) => {
    const sr = chart.addSeries(LW.LineSeries, Object.assign({ color, lineWidth: 1 }, quiet, opts), opts.pane || 0);
    sr.setData(data);
    return sr;
  };
  addLine(p.landU, p.landColor);
  addLine(p.landD, p.landColor);
  addLine(p.stopLh, p.stopLhColor, { lineType: LW.LineType.WithSteps });
  addLine(p.stopSh, p.stopShColor, { lineType: LW.LineType.WithSteps });
  addLine(p.midl, p.midColor);
  if (p.trails.vah) { addLine(p.trails.vah, p.trailVA); addLine(p.trails.val, p.trailVA); addLine(p.trails.poc, p.trailPOC); }
  addLine(p.vwap, p.vwapColor);
  if (p.markers.length) LW.createSeriesMarkers(candles, p.markers);

  // ── drawings: the profile, its levels and tags, the cone and the stops ──
  class Drawing {
    constructor(spec, z) { this.spec = spec; this.z = z; }
    attached({ chart: c, series, requestUpdate }) { this.c = c; this.s = series; this.req = requestUpdate; }
    detached() {}
    updateAllViews() {}
    autoscaleInfo() {
      const cn = this.spec.cone;
      if (this.z === 'top' && cn && cn.on) return { priceRange: { minValue: cn.botY, maxValue: cn.topY } };
      return null;
    }
    paneViews() {
      const self = this;
      return [{ zOrder: () => self.z, renderer: () => ({ draw: (target) => target.useMediaCoordinateSpace(({ context: ctx }) => self.draw(ctx)) }) }];
    }
    X(i) { return this.c.timeScale().logicalToCoordinate(i); }
    Y(v) { return this.s.priceToCoordinate(v); }
    seg(x1, y1, x2, y2, color, width, style) {
      const a = this.X(x1), b = this.X(x2), ya = this.Y(y1), yb = this.Y(y2);
      if (a === null || b === null || ya === null || yb === null) return;
      const ctx = this.ctx;
      ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = width || 1;
      ctx.setLineDash(style === 'dotted' ? [1, 2] : style === 'dashed' ? [4, 3] : []);
      ctx.beginPath(); ctx.moveTo(a, ya); ctx.lineTo(b, yb); ctx.stroke(); ctx.restore();
    }
    label(x, y, text, color, bg, style) {
      const px = this.X(x), py = this.Y(y);
      if (px === null || py === null) return;
      const ctx = this.ctx;
      ctx.save(); ctx.font = `10px ${K.monoFont}`;
      const linesT = String(text).split('\n');
      const w = Math.max(...linesT.map(t => ctx.measureText(t).width)) + 8, lh = 12, hgt = lh * linesT.length + 3;
      let bx = px, by = py - hgt / 2;
      if (style === 'left') { bx = px + 5; }
      if (style === 'lower_right') { bx = px - w; by = py - hgt - 2; }
      if (style === 'upper_right') { bx = px - w; by = py + 2; }
      if (style === 'plain') { bx = px + 2; }
      if (bg) {
        ctx.fillStyle = bg;
        ctx.beginPath();
        if (style === 'left') { ctx.moveTo(px, py); ctx.lineTo(bx, py - 4); ctx.lineTo(bx, py + 4); ctx.closePath(); ctx.fill(); }
        ctx.beginPath(); ctx.roundRect ? ctx.roundRect(bx, by, w, hgt, 2) : ctx.rect(bx, by, w, hgt); ctx.fill();
      }
      ctx.fillStyle = color; ctx.textBaseline = 'top';
      linesT.forEach((t, k) => ctx.fillText(t, bx + 4, by + 2 + k * lh));
      ctx.restore();
    }
    box(b) {
      const x1 = this.X(b.x1), x2 = this.X(b.x2), y1 = this.Y(b.y1), y2 = this.Y(b.y2);
      if (x1 === null || x2 === null || y1 === null || y2 === null) return;
      const ctx = this.ctx;
      const L = Math.min(x1, x2), T = Math.min(y1, y2), W = Math.abs(x2 - x1), Hh = Math.max(1, Math.abs(y2 - y1));
      if (b.fill) { ctx.fillStyle = b.fill; ctx.fillRect(L, T, W, Hh); }
      if (b.border) { ctx.strokeStyle = b.border; ctx.lineWidth = 1; ctx.strokeRect(L + 0.5, T + 0.5, W - 1, Hh - 1); }
    }
    draw(ctx) {
      this.ctx = ctx;
      const sp = this.spec;
      if (this.z === 'bottom') {                       // the value-area band sits beneath the candles
        (sp.profile.boxes || []).filter(b => b.kind === 'va').forEach(b => this.box(b));
        return;
      }
      if (this.z === 'normal') {                       // the cone's lines render beneath the profile's rows
        const cn = sp.cone;
        if (cn && cn.on) {
          cn.segs.forEach(s => this.seg(s[0], s[1], s[2], s[3], cn.color, 1, 'solid'));
          this.seg(cn.x0, cn.stopL, cn.x1, cn.stopL, cn.stopLc, 1, 'dashed');
          this.seg(cn.x0, cn.stopS, cn.x1, cn.stopS, cn.stopSc, 1, 'dashed');
        }
        (sp.profile.lines || []).forEach(l => this.seg(l.x1, l.y, l.x2, l.y, l.color, l.width, l.style));
        return;
      }
      (sp.profile.boxes || []).filter(b => b.kind !== 'va').forEach(b => this.box(b));
      (sp.profile.tags || []).forEach(t => this.label(t.x, t.y, t.text, t.color, t.bg, 'left'));
      const cn = sp.cone;
      if (cn && cn.on) {
        this.label(cn.tagX, cn.topY, cn.topTxt, cn.tagC, null, 'lower_right');
        this.label(cn.tagX, cn.botY, cn.botTxt, cn.tagC, null, 'upper_right');
      }
    }
  }
  ['bottom', 'normal', 'top'].forEach(z => candles.attachPrimitive(new Drawing({ profile: p.profile, cone: p.cone }, z)));

  // ── pane 1: Anumaan ───────────────────────────────────────────────────
  const P1 = 1;
  let pane1Series;
  if (p.pane === 'Surprise') {
    if (p.tapes) {
      [['tT', 'tT'], ['tL', 'tL'], ['tR', 'tR'], ['tM', 'tM']].forEach(([k]) => {
        const sr = chart.addSeries(LW.HistogramSeries, Object.assign({ base: p.tapeBase[k] }, quiet, { priceFormat: { type: 'price', precision: 2, minMove: 0.01 } }), P1);
        sr.setData(p[k]);
      });
    }
    pane1Series = chart.addSeries(LW.HistogramSeries, Object.assign({ base: 0 }, quiet, { priceFormat: { type: 'price', precision: 2, minMove: 0.01 } }), P1);
    pane1Series.setData(p.cols);
    addLine(p.bandU, p.bandColor, { pane: P1 });
    addLine(p.bandD, p.bandColor, { pane: P1 });
    pane1Series.createPriceLine({ price: 0, color: p.zeroColor, lineWidth: 1, lineStyle: LW.LineStyle.Dotted, axisLabelVisible: false, title: '' });
    class TapeTags {
      constructor(tags) { this.tags = tags; }
      attached({ chart: c, series }) { this.c = c; this.s = series; }
      updateAllViews() {}
      paneViews() {
        const self = this;
        return [{ zOrder: () => 'top', renderer: () => ({ draw: (t) => t.useMediaCoordinateSpace(({ context: ctx }) => {
          self.tags.forEach(g => {
            const x = self.c.timeScale().logicalToCoordinate(g.x), y = self.s.priceToCoordinate(g.y);
            if (x === null || y === null) return;
            ctx.save(); ctx.font = `10px ${K.monoFont}`; ctx.fillStyle = g.color; ctx.textBaseline = 'middle';
            const ls = g.text.split('\n'); ls.forEach((s, k) => ctx.fillText(s, x + 4, y + (k - (ls.length - 1) / 2) * 12)); ctx.restore();
          });
        }) }) }];
      }
    }
    pane1Series.attachPrimitive(new TapeTags(p.tapeTags));
  } else {
    pane1Series = addLine(p.proofF, p.proofFColor, { pane: P1, lineWidth: 2 });
    addLine(p.proofH, p.proofHColor, { pane: P1 });
  }
  const panes = chart.panes();
  const sizePanes = () => { const ps = chart.panes(); if (ps[1]) ps[1].setHeight(Math.round(window.innerHeight * 0.34)); };
  sizePanes();
  // keep every scale's end labels inside its pane: the Anumaan pane's ±6 labels sat on the pane's edges and were cut
  if (p.pane === 'Surprise') {
    const fixed = () => ({ priceRange: { minValue: -6.6, maxValue: 6.9 } });   // +0.3 at the top: the legend's strip
    chart.panes()[1].getSeries().forEach(sr => sr.applyOptions({ autoscaleInfoProvider: fixed }));
    pane1Series.priceScale().applyOptions({ scaleMargins: { top: 0.02, bottom: 0.02 } });
  } else {
    pane1Series.priceScale().applyOptions({ scaleMargins: { top: 0.12, bottom: 0.06 } });
  }

  // ── watermark ──────────────────────────────────────────────────────────
  try {
    LW.createTextWatermark(panes[0], { horzAlign: 'center', vertAlign: 'center',
      lines: [{ text: title.watermark, color: K.watermark, fontSize: 64, fontStyle: '600' }] });
  } catch (e) { /* older builds */ }

  // ── legends (status lines) ─────────────────────────────────────────────
  const mk = (cls, parent) => { const d = document.createElement('div'); d.className = cls; parent.appendChild(d); return d; };
  const wrapEl = document.getElementById('wrap');
  const leg0 = mk('legend', wrapEl);
  const row1 = mk('lrow', leg0), row2 = mk('lrow', leg0);
  const leg1 = mk('legend pane', wrapEl);
  const lastBar = p.bars[p.bars.length - 1];
  const prevClose = (i) => (i > 0 ? p.bars[i - 1].close : p.bars[i].open);
  const byTime = new Map(p.bars.map((b, i) => [b.time, i]));
  function paintLegend(i) {
    if (i === undefined || i === null || i < 0) i = p.bars.length - 1;
    const b = p.bars[i];
    if (!b) return;
    const ch = b.close - prevClose(i), pc = ch / prevClose(i) * 100;
    const col = b.close >= b.open ? K.candleUp : K.candleDown;
    const v = (k, x) => `<span class="q q${k}"><span class="k">${k}</span><span class="v" style="color:${col}">${fmtPx(x)}</span></span>`;
    row1.innerHTML = `<span class="sym">${title.name}</span><span class="dot">·</span><span class="tf">${title.tf}</span>` +
      `<span class="dot">·</span><span class="ex">${title.exchange}</span>` +
      `<span class="ohlc">${v('O', b.open)}${v('H', b.high)}${v('L', b.low)}${v('C', b.close)}` +
      `<span class="v" style="color:${col}">${ch >= 0 ? '+' : ''}${fmtPx(ch)} (${pc >= 0 ? '+' : ''}${pc.toFixed(2).replace('-', '\u2212')}%)</span></span>`;
    row2.innerHTML = p.showVolume ? `<span class="ind">Vol</span><span class="v" style="color:${col}">${fmtVol(p.vols[i].value)}</span>` : '';
    const c = p.cols[i];
    const val = p.pane === 'Surprise' ? (c && c.value !== undefined ? c.value : null) : null;
    const raw = p.pane === 'Surprise' ? p.uRaw[i] : val;
    leg1.innerHTML = `<span class="ind">Anumaan</span>` + (p.pane === 'Surprise'
      ? `<span class="v" style="color:${(c && c.color) || K.axis}">${raw === null || raw === undefined ? '∅' : Number(raw).toFixed(2).replace('-', '\u2212')}</span>`
      : `<span class="v">${p.proofF[i].value !== undefined ? p.proofF[i].value.toFixed(1).replace('-', '\u2212') : '∅'}</span>` +
        `<span class="v muted">${p.proofH[i].value !== undefined ? p.proofH[i].value.toFixed(1).replace('-', '\u2212') : '∅'}</span>`);
  }
  function placePaneLegend() {
    const ps = chart.panes();
    if (ps[1]) { const top = ps[0].getHeight() + 1 + 8; leg1.style.top = top + 'px'; }
  }
  chart.subscribeCrosshairMove((param) => {
    const i = param && param.time !== undefined ? byTime.get(param.time) : undefined;
    paintLegend(i);
  });
  // The status lines stop at the plot's edge. The price scale's width is measured, not guessed from the screen: on a
  // phone the quote (close and change) wraps under the symbol as one block instead of running across the axis labels,
  // and a right-hand table clears the scale whatever its labels' width.
  function fitLegend() {
    let psw = 0;
    try { psw = chart.priceScale('right').width(); } catch (e) { /* older builds */ }
    if (!psw) return;
    wrapEl.style.setProperty('--psw', psw + 'px');
    const room = Math.max(140, el.clientWidth - psw - leg0.offsetLeft - 8);
    leg0.style.maxWidth = room + 'px'; leg1.style.maxWidth = room + 'px';
  }
  paintLegend();
  placePaneLegend();
  requestAnimationFrame(fitLegend);
  chart.timeScale().subscribeVisibleLogicalRangeChange(fitLegend);     // a zoom can widen the scale's labels
  new ResizeObserver(() => { sizePanes(); placePaneLegend(); fitLegend(); }).observe(el);

  // ── the table (off by default) ─────────────────────────────────────────
  if (p.tableOn && p.table.length) {
    const tb = mk('ptable ' + p.tablePos.toLowerCase().replace(' ', '-'), wrapEl);
    tb.innerHTML = p.table.map(r => `<div class="tr" title="${r.tip.replace(/"/g, '&quot;')}"><span class="tk">${r.key}</span>` +
      `<span class="tv" style="color:${r.color}">${r.value}</span></div>`).join('');
  }

  // first view: the last ~150 bars and the profile beside them
  const n = p.bars.length;
  const home = () => {
    const w = el.clientWidth || window.innerWidth;
    const narrow = w < 640;
    const shown = narrow ? Math.max(28, Math.round(w / 10)) : Math.max(40, Math.min(220, Math.round(w / 7.5)));  // ~7.5px a bar
    const right = narrow ? 74 : 58;            // room for the profile and its tags; a phone's bars are narrower than a tag
    chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, n - shown), to: n + right });
  };
  home();
  window.addEventListener('dblclick', home);

  // "/" jumps to the symbol search from anywhere, as in a terminal; Escape leaves it. The handler lives on the page, and
  // each render of the chart replaces the last one's, so there is only ever one.
  try {
    const P = window.parent;
    const onKey = (ev) => {
      const t = ev.target, typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
      if (ev.key === '/' && !typing && !ev.metaKey && !ev.ctrlKey) {
        const box = P.document.querySelector('.st-key-toolbar input');
        if (box) { ev.preventDefault(); box.focus(); box.select(); }
      } else if (ev.key === 'Escape' && typing && t.closest && t.closest('.st-key-toolbar')) { t.blur(); }
    };
    if (P.__anumaanKeys) P.document.removeEventListener('keydown', P.__anumaanKeys);
    P.__anumaanKeys = onKey;
    P.document.addEventListener('keydown', onKey);
    window.addEventListener('keydown', onKey);
  } catch (e) { /* a page that is not ours: no shortcut */ }
})();
