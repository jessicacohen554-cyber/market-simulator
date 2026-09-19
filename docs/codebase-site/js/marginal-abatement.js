/**
 * marginal-abatement.js — renderer for marginal-abatement.html.
 *
 * MOCK STATE: reads window.MAC_SYNTHETIC (data/marginal-abatement-synthetic.js).
 * When real data lands this module keeps its shape and swaps `loadCells()` for a
 * fetch of the committed per-grid-year sidecars listed in
 * frontend/data/mac/manifest.js — nothing else here changes, because the page
 * already treats "this grid-year has no data" as a first-class render path.
 *
 * Charts are hand-rolled SVG (no CDN dependency, deterministic, and themed by
 * the CSS custom properties declared on .mac-scope — which this design system
 * redeclares under .section-dark rather than behind a global toggle).
 *
 * Every color used here cleared dataviz/scripts/validate_palette.js first; the
 * results are recorded in the page's <style> header.
 */
(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // Roster. Order = config/iso_configs.py::_ISO_BUILDERS registration order, so
  // the page's roster is the model's roster. A grid is NEVER dropped from this
  // list for lack of data — a short list would read as "these are the grids".
  // ---------------------------------------------------------------------------
  var ISOS = ['ERCOT', 'CAISO', 'MISO', 'PJM', 'NYISO', 'NEISO', 'SPP', 'NWPP', 'SOCO'];
  var YEARS = [2023, 2024, 2025];
  var TECHS = [['wind', 'New wind'], ['solar', 'New solar']];
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  // Which grids the mock pretends have landed, per preview state. The DEFAULT is
  // `partial` because that is what the page will actually look like for a while:
  // results arrive one lane at a time. `empty` and `full` are there so the
  // pending path and the full-data layout are both reviewable without editing a URL.
  var SYNTH_STATES = {
    empty: [],
    partial: ['ERCOT', 'MISO', 'CAISO'],
    full: ISOS.slice()
  };

  // The keeper bundle each grid's number will come from — named in the pending
  // card so a reader can see exactly which artifact is blocking.
  var KEEPER_BUNDLE = {
    ERCOT: 'ercot265_receipts_fallback', CAISO: 'caiso275_B_gascoupling_span',
    MISO: 'miso260_seam_ladder', PJM: 'pjm_d4_4_A', NYISO: 'nyiso239_bench_span',
    NEISO: 'neiso110_dualfuel_derate_scope', SPP: 'spp42_span_a',
    NWPP: 'nwpp41_span_A', SOCO: 'soco53_measured_ct_hr'
  };

  var DATA = window.MAC_SYNTHETIC || { cells: {}, lcoe: {}, shape: {} };

  var state = { year: 2024, tech: 'wind', iso: 'ERCOT', synth: 'partial', shape: false };
  var tables = { rank: false, dur: false, wf: false };

  // ---------------------------------------------------------------------------
  // data access
  // ---------------------------------------------------------------------------
  function readySet() { return SYNTH_STATES[state.synth] || []; }
  function isReady(iso) { return readySet().indexOf(iso) >= 0; }

  /** The cell for a grid-year, or null when that grid-year has not landed. */
  function cell(iso, year) {
    if (!isReady(iso)) return null;
    return DATA.cells[iso + '-' + year] || null;
  }
  function scalars(iso, year, tech) {
    var c = cell(iso, year);
    return c && c.scalars ? c.scalars[tech] : null;
  }

  // ---------------------------------------------------------------------------
  // formatting
  // ---------------------------------------------------------------------------
  function fmtT(v) { return (v < 0 ? '−' : '') + '$' + Math.abs(v).toFixed(1); }
  function fmtMWh(v) { return (v < 0 ? '−' : '') + '$' + Math.abs(v).toFixed(2); }
  function fmtRate(v) { return v.toFixed(3); }
  function fmtPct(v) { return (v * 100).toFixed(1) + '%'; }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function techLabel(t) { return t === 'wind' ? 'new wind' : 'new solar'; }

  var PENDING_SVG =
    '<svg viewBox="0 0 12 12" aria-hidden="true">' +
    '<circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M6 3.2v3.2l2 1.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>';
  function pendingChip() {
    // Status color NEVER travels alone — icon + the word, every time.
    return '<span class="pending-chip">' + PENDING_SVG + 'pending</span>';
  }

  // ---------------------------------------------------------------------------
  // tooltip (one shared node; the hover layer dataviz asks for by default)
  // ---------------------------------------------------------------------------
  var tip = document.createElement('div');
  tip.className = 'bc-tooltip';
  tip.setAttribute('role', 'presentation');
  tip.style.display = 'none';
  document.body.appendChild(tip);

  function bindTip(node, html) {
    node.addEventListener('mousemove', function (e) {
      tip.innerHTML = html;
      tip.style.display = 'block';
      var w = tip.offsetWidth, h = tip.offsetHeight;
      var x = Math.min(e.clientX + 14, window.innerWidth - w - 10);
      var y = Math.max(e.clientY - h - 12, 8);
      tip.style.left = x + 'px';
      tip.style.top = y + 'px';
    });
    node.addEventListener('mouseleave', function () { tip.style.display = 'none'; });
  }

  // ---------------------------------------------------------------------------
  // tiny SVG helpers
  // ---------------------------------------------------------------------------
  var NS = 'http://www.w3.org/2000/svg';
  function svgEl(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] !== null && attrs[k] !== undefined) e.setAttribute(k, attrs[k]);
    return e;
  }
  function svgRoot(w, h, label) {
    var s = svgEl('svg', {
      width: w, height: h, viewBox: '0 0 ' + w + ' ' + h,
      role: 'img', 'aria-label': label
    });
    return s;
  }
  function txt(parent, x, y, s, cls, anchor) {
    var t = svgEl('text', { x: x, y: y, class: cls || '', 'text-anchor': anchor || 'start' });
    t.textContent = s;
    parent.appendChild(t);
    return t;
  }
  function title(node, s) {
    var t = svgEl('title', {});
    t.textContent = s;
    node.appendChild(t);
  }
  /** Nice axis ticks spanning [lo, hi]. */
  function ticks(lo, hi, want) {
    var span = hi - lo;
    if (!(span > 0)) return [lo];
    var raw = span / (want || 5);
    var mag = Math.pow(10, Math.floor(Math.log10(raw)));
    var step = [1, 2, 2.5, 5, 10].map(function (m) { return m * mag; })
      .filter(function (s) { return s >= raw; })[0] || 10 * mag;
    var out = [], v = Math.ceil(lo / step) * step;
    for (; v <= hi + 1e-9; v += step) out.push(Math.abs(v) < 1e-9 ? 0 : v);
    return out;
  }
  /** Hide a legend whose chart drew nothing — a legend over an empty panel
   *  invites the reader to look for marks that do not exist. */
  function legend(id, show) {
    var el = document.getElementById(id);
    if (el) el.hidden = !show;
  }
  function width(id, fallback) {
    var el = document.getElementById(id);
    var w = el ? el.clientWidth : 0;
    return Math.max(w || fallback || 640, 300);
  }

  // ===========================================================================
  // HERO
  // ===========================================================================
  function renderHero() {
    var ready = readySet();
    var rows = ready.map(function (iso) {
      var s = scalars(iso, state.year, state.tech);
      return s ? { iso: iso, post: s.mac_post_ira, pre: s.mac_pre_ira } : null;
    }).filter(Boolean).sort(function (a, b) { return a.post - b.post; });

    var find = document.getElementById('heroFinding');
    var sub = document.getElementById('heroSub');
    var sel = document.getElementById('heroSelection');

    if (!rows.length) {
      find.innerHTML = 'No grid has been measured yet — so this page has ' +
        '<em>nothing to report</em>, and says so rather than showing a zero.';
      sub.innerHTML = 'The marginal emission rate is emitted by every solve from commit ' +
        '<code>fba0ecd7</code> onward, but every designated keeper predates it. The first grid ' +
        'to light up will be whichever lane next completes a control replay; each one appears on ' +
        'its own, and nothing is inferred for the others.';
    } else {
      var lo = rows[0], hi = rows[rows.length - 1];
      var one = rows.length === 1;
      find.innerHTML = one
        ? ('Abating with ' + techLabel(state.tech) + ' costs <em>' + fmtT(lo.post) +
           '/tCO<sub>2</sub></em> in ' + lo.iso + ' post-IRA — and <em>' + fmtT(lo.pre) +
           '</em> without the credit.')
        : ('Abating with ' + techLabel(state.tech) + ' is cheapest in <em>' + lo.iso +
           '</em> at ' + fmtT(lo.post) + '/tCO<sub>2</sub> and dearest in <em>' + hi.iso +
           '</em> at ' + fmtT(hi.post) + ' — a ' +
           (hi.post > 0 && lo.post > 0 ? (hi.post / lo.post).toFixed(1) + '× spread' :
            'spread of ' + fmtT(hi.post - lo.post)) + ' across grids that buy the same turbines.');
      var ratio = (rows.reduce(function (a, r) { return a + r.pre; }, 0) /
                   Math.max(rows.reduce(function (a, r) { return a + r.post; }, 0), 1e-9));
      sub.innerHTML = 'Strip the IRA credit and every one of those numbers rises — on this ' +
        'selection by about <b>' + ratio.toFixed(1) + '×</b>. Post-IRA and pre-IRA are shown ' +
        'together everywhere on this page, because quoting one as the other is the easiest way to ' +
        'publish a wrong number. The denominator is the LP’s <b>emissions dual</b>, weighted by ' +
        'the technology’s own hourly output — not a fleet or fossil average.';
    }
    sel.innerHTML = 'Showing <b>' + techLabel(state.tech) + '</b> in <b>' + state.year +
      '</b>. These are model-SELECTION numbers: since rule 22’s <code>[R-HOLDOUT]</code> ' +
      'removal there is no certified out-of-sample year in this program, so nothing here is ' +
      'evidence of forecast skill.';

    var n = ready.length;
    document.getElementById('progFill').style.width = (100 * n / ISOS.length).toFixed(1) + '%';
    document.getElementById('progLabel').innerHTML =
      '<b>' + n + ' of ' + ISOS.length + '</b> modeled grids measured' +
      (n < ISOS.length ? ' · ' + (ISOS.length - n) + ' awaiting a control replay' : '');
  }

  // ===========================================================================
  // KPI TILES
  // ===========================================================================
  function renderTiles() {
    var host = document.getElementById('tiles');
    host.innerHTML = ISOS.map(function (iso) {
      var s = scalars(iso, state.year, state.tech);
      if (!s) {
        return '<div class="mac-tile is-pending">' +
          '<div class="mac-tile__iso">' + iso + pendingChip() + '</div>' +
          '<div class="mac-tile__pendingmsg">Not measured. Its keeper predates the emissions dual.</div>' +
          '</div>';
      }
      var c = cell(iso, state.year);
      var ov = c.system.capture_price_overlay_usd_per_mwh;
      return '<div class="mac-tile">' +
        '<div class="mac-tile__iso">' + iso + '</div>' +
        '<div class="mac-tile__val">' + fmtT(s.mac_post_ira) +
          '<span class="unit">/tCO₂ post-IRA</span></div>' +
        '<div class="mac-tile__pre">' + fmtT(s.mac_pre_ira) + ' pre-IRA</div>' +
        '<div class="mac-tile__foot">rate ' + fmtRate(s.mer_tech) + ' tCO₂/MWh · ' +
          'capture ' + fmtMWh(s.capture_price) + '/MWh' +
          (ov > 0 ? ' (incl. ' + fmtMWh(ov) + ' overlay)' : '') + '</div>' +
        '</div>';
    }).join('');
  }

  // ===========================================================================
  // CHART 1 — MAC ranking, dumbbell (1 hue, 2 shades; "before → after per item")
  // ===========================================================================
  function renderRank() {
    var host = document.getElementById('rankChart');
    host.innerHTML = '';
    document.getElementById('rankTitle').textContent =
      'Marginal abatement cost by grid — ' + techLabel(state.tech) + ', ' + state.year;

    var ready = [], pend = [];
    ISOS.forEach(function (iso) {
      var s = scalars(iso, state.year, state.tech);
      if (s) ready.push({ iso: iso, post: s.mac_post_ira, pre: s.mac_pre_ira, s: s });
      else pend.push({ iso: iso });
    });
    ready.sort(function (a, b) { return a.post - b.post; });
    pend.sort(function (a, b) { return a.iso < b.iso ? -1 : 1; });
    var rows = ready.concat(pend);   // pending always listed, always last, never a mark

    var W = width('rankChart', 860);
    var padL = 112, padR = 66, padT = 26, padB = 34;
    var rowH = 30, H = padT + rows.length * rowH + padB;

    // Domain always includes 0 so a negative MAC reads as "below zero", not as a
    // short bar. A negative is a real result (capture above cost), not an error.
    var vals = ready.reduce(function (a, r) { return a.concat([r.post, r.pre]); }, [0]);
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var pad = (hi - lo) * 0.08 || 1;
    lo -= pad; hi += pad;
    var x = function (v) { return padL + (v - lo) / (hi - lo) * (W - padL - padR); };

    var svg = svgRoot(W, H,
      'Marginal abatement cost by grid for ' + techLabel(state.tech) + ' in ' + state.year +
      '. Post-IRA and pre-IRA dollars per tonne, ' + ready.length + ' grids measured, ' +
      pend.length + ' pending.');

    // No measured grid ⇒ NO dollar axis. A $-scale drawn across nine empty rows
    // invites the reader to place the missing values somewhere near zero, which
    // is the one reading this page must never permit.
    if (ready.length) {
      ticks(lo, hi, 6).forEach(function (t) {
        svg.appendChild(svgEl('line', {
          x1: x(t), x2: x(t), y1: padT - 8, y2: H - padB + 2,
          class: t === 0 ? 'zero-line' : 'grid-line'
        }));
        txt(svg, x(t), padT - 13, '$' + t, 'ax-label', 'middle');
      });
      txt(svg, 2, H - 8, W < 560 ? '$ per tonne CO₂ — lower is cheaper'
                                 : '$ per tonne CO₂  —  lower is cheaper to abate', 'ax-title');
    } else {
      txt(svg, 2, H - 8,
        'No scale is drawn — no grid has been measured for ' + state.year + '.', 'ax-title');
    }
    legend('rankLegend', ready.length > 0);

    rows.forEach(function (r, i) {
      var cy = padT + i * rowH + rowH / 2;
      txt(svg, 2, cy + 4, r.iso, 'row-label', 'start');

      if (!r.s) {
        // PENDING: the row exists, the marks do not. No zero, no dash, no bar.
        var g = svgEl('g', { class: 'pend-row' });
        g.appendChild(svgEl('line', {
          x1: padL, x2: W - padR, y1: cy, y2: cy,
          stroke: 'var(--mac-pending)', 'stroke-width': 1,
          'stroke-dasharray': '3 5', opacity: 0.45
        }));
        var pl = txt(g, W - padR + 8, cy + 4, 'pending', 'ax-label');
        pl.setAttribute('fill', 'var(--mac-pending)');
        pl.setAttribute('font-weight', '700');
        title(g, r.iso + ' — not measured yet. No value is shown because none exists.');
        svg.appendChild(g);
        return;
      }

      var g2 = svgEl('g', {});
      g2.appendChild(svgEl('line', {           // the connector IS the credit
        x1: x(r.post), x2: x(r.pre), y1: cy, y2: cy,
        stroke: 'var(--mac-accent-2)', 'stroke-width': 2.5, 'stroke-linecap': 'round', opacity: 0.55
      }));
      // 2px surface ring on overlapping marks (marks-and-anatomy)
      g2.appendChild(svgEl('circle', {
        cx: x(r.pre), cy: cy, r: 6, fill: 'var(--mac-surface)',
        stroke: 'var(--mac-accent-2)', 'stroke-width': 2.5
      }));
      g2.appendChild(svgEl('circle', {
        cx: x(r.post), cy: cy, r: 6, fill: 'var(--mac-accent)',
        stroke: 'var(--mac-surface)', 'stroke-width': 2
      }));
      // Direct labels on both ends — the relief channel for the pre-IRA mark's
      // sub-3:1 fill, and what keeps a 2-shade ramp readable under CVD.
      // The post-IRA value lives in the LEFT GUTTER, not beside its dot: a dot
      // near the domain minimum sits only a few px into the plot, and a label
      // hung off it collides with the row name at phone width. Gutter placement
      // is collision-free at every width and needs no per-row special-casing.
      var pa = txt(g2, padL - 12, cy + 4, fmtT(r.post), 'val-label', 'end');
      pa.setAttribute('fill', 'var(--mac-ink)');
      // pre-IRA is always the larger number (a credit only lowers cost), so its
      // label always goes to the right of its dot, clamped inside the canvas.
      var pb = txt(g2, Math.min(x(r.pre) + 11, W - 4), cy + 4, fmtT(r.pre), 'ax-label', 'start');
      pb.setAttribute('font-weight', '600');

      bindTip(g2,
        '<b>' + r.iso + ' · ' + techLabel(state.tech) + ' · ' + state.year + '</b><br>' +
        'post-IRA <b>' + fmtT(r.post) + '</b> / tCO₂<br>' +
        'pre-IRA <b>' + fmtT(r.pre) + '</b> / tCO₂<br>' +
        'cost ' + fmtMWh(r.s.cost_per_delivered_mwh_post_ira) + '/MWh − capture ' +
        fmtMWh(r.s.capture_price) + '/MWh<br>' +
        '÷ rate ' + fmtRate(r.s.mer_tech) + ' tCO₂/MWh');
      title(g2, r.iso + ': ' + fmtT(r.post) + ' post-IRA, ' + fmtT(r.pre) + ' pre-IRA per tonne.');
      svg.appendChild(g2);
    });

    host.appendChild(svg);

    // table view (always available — the WARN relief for the lighter mark)
    var tb = '<table class="mac-table"><caption class="mac-fig__sub" style="text-align:left">' +
      'Same data, ' + techLabel(state.tech) + ', ' + state.year +
      '.</caption><thead><tr><th scope="col">Grid</th><th scope="col">post-IRA $/t</th>' +
      '<th scope="col">pre-IRA $/t</th><th scope="col">cost $/MWh</th>' +
      '<th scope="col">capture $/MWh</th><th scope="col">rate tCO₂/MWh</th></tr></thead><tbody>' +
      rows.map(function (r) {
        if (!r.s) return '<tr><td>' + r.iso + '</td><td class="pend" colspan="5">pending — not measured</td></tr>';
        return '<tr><td>' + r.iso + '</td><td>' + fmtT(r.post) + '</td><td>' + fmtT(r.pre) +
          '</td><td>' + fmtMWh(r.s.cost_per_delivered_mwh_post_ira) + '</td><td>' +
          fmtMWh(r.s.capture_price) + '</td><td>' + fmtRate(r.s.mer_tech) + '</td></tr>';
      }).join('') + '</tbody></table>';
    document.getElementById('rankTable').innerHTML = tb;
  }

  // ===========================================================================
  // CHART 2 — MER duration curve (emphasis: focus in hue, rest in gray)
  // ===========================================================================
  function renderDuration() {
    var host = document.getElementById('durChart');
    host.innerHTML = '';
    document.getElementById('durFocusName').textContent = state.iso;

    var series = readySet().map(function (iso) {
      var c = cell(iso, state.year);
      return c ? { iso: iso, d: c.mer_duration, zero: c.system.zero_mer_hour_share } : null;
    }).filter(Boolean);

    if (!series.length) {
      host.innerHTML = '<p class="mac-fig__sub" style="margin:8px 0 0">' +
        'No grid has landed for ' + state.year + ' yet, so there is no curve to draw.</p>';
      document.getElementById('durTable').innerHTML = '';
      legend('durLegend', false);
      return;
    }

    var W = width('durChart', 520), H = 300;
    var padL = 46, padR = 14, padT = 14, padB = 40;
    var hi = 0;
    series.forEach(function (s) { s.d.forEach(function (v) { if (v > hi) hi = v; }); });
    hi = hi * 1.06 || 1;
    var n = series[0].d.length;
    var x = function (i) { return padL + i / (n - 1) * (W - padL - padR); };
    var y = function (v) { return H - padB - v / hi * (H - padT - padB); };

    var svg = svgRoot(W, H,
      'Marginal emission rate duration curve for ' + state.year + ', ' + state.iso +
      ' emphasised against ' + (series.length - 1) + ' other measured grids.');

    ticks(0, hi, 5).forEach(function (t) {
      svg.appendChild(svgEl('line', { x1: padL, x2: W - padR, y1: y(t), y2: y(t), class: 'grid-line' }));
      txt(svg, padL - 7, y(t) + 4, t.toFixed(2), 'ax-label', 'end');
    });
    [0, 25, 50, 75, 100].forEach(function (p) {
      txt(svg, x((p / 100) * (n - 1)), H - padB + 15, p + '%', 'ax-label', 'middle');
    });
    txt(svg, 2, H - 8, 'hours ranked, highest rate first', 'ax-title');
    txt(svg, 12, padT + 6, 'tCO₂/MWh', 'ax-title');

    legend('durLegend', true);
    var focus = null;
    function path(s) {
      return s.d.map(function (v, i) { return (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1); }).join('');
    }
    // Context first, emphasis last — one series is the point, the rest are context.
    series.forEach(function (s) {
      if (s.iso === state.iso) { focus = s; return; }
      var p = svgEl('path', {
        d: path(s), fill: 'none', stroke: 'var(--mac-context)',
        'stroke-width': 1.25, opacity: 0.5
      });
      title(p, s.iso + ' (context)');
      svg.appendChild(p);
    });

    if (focus) {
      // The zero-rate tail, shaded: caveat 2 made visible.
      var z0 = x((1 - focus.zero) * (n - 1));
      if (focus.zero > 0.005) {
        svg.appendChild(svgEl('rect', {
          x: z0, y: padT, width: Math.max(W - padR - z0, 0), height: H - padT - padB,
          fill: 'var(--mac-warm)', opacity: 0.16
        }));
        svg.appendChild(svgEl('line', {
          x1: z0, x2: z0, y1: padT, y2: H - padB,
          stroke: 'var(--mac-warm)', 'stroke-width': 1.5, 'stroke-dasharray': '4 3'
        }));
        var zl = txt(svg, Math.min(z0 + 6, W - padR - 4), padT + 13,
                     fmtPct(focus.zero) + ' at rate 0', 'ax-label',
                     z0 > W - padR - 92 ? 'end' : 'start');
        zl.setAttribute('fill', 'var(--mac-warm)');
        zl.setAttribute('font-weight', '700');
      }
      var fp = svgEl('path', {
        d: path(focus), fill: 'none', stroke: 'var(--mac-accent)',
        'stroke-width': 2.5, 'stroke-linejoin': 'round'
      });
      title(fp, state.iso + ' (focus)');
      svg.appendChild(fp);
      var fl = txt(svg, x(4), y(focus.d[0]) - 9, state.iso, 'val-label');
      fl.setAttribute('fill', 'var(--mac-accent)');
    } else {
      txt(svg, W / 2, padT + 22, state.iso + ' — pending, no curve', 'val-label', 'middle')
        .setAttribute('fill', 'var(--mac-pending)');
    }
    host.appendChild(svg);

    var f = focus;
    document.getElementById('durTable').innerHTML = f
      ? ('<table class="mac-table"><thead><tr><th scope="col">Percentile of hours</th>' +
         '<th scope="col">' + state.iso + ' rate tCO₂/MWh</th></tr></thead><tbody>' +
         [0, 10, 25, 50, 75, 90, 95, 99].map(function (p) {
           return '<tr><td>' + p + 'th</td><td>' +
             fmtRate(f.d[Math.min(Math.round(p / 100 * (n - 1)), n - 1)]) + '</td></tr>';
         }).join('') +
         '<tr><td>share at exactly 0</td><td>' + fmtPct(f.zero) + '</td></tr></tbody></table>')
      : '<p class="mac-fig__sub">' + state.iso + ' is pending — no rows.</p>';
  }

  // ===========================================================================
  // Zero-share meters (a single ratio against a limit → meter, not a chart)
  // ===========================================================================
  function renderMeters() {
    var host = document.getElementById('meterList');
    var max = 0.40;
    host.innerHTML = ISOS.map(function (iso) {
      var c = cell(iso, state.year);
      if (!c) {
        return '<div class="meter-row"><div class="meter-row__iso">' + iso + '</div>' +
          '<div class="meter-row__track"></div>' +
          '<div class="meter-row__val pend">pending</div></div>';
      }
      var z = c.system.zero_mer_hour_share, imp = c.system.import_marginal_hour_share;
      var pct = Math.min(z / max, 1) * 100;
      return '<div class="meter-row" title="' + esc(iso + ': ' + fmtPct(z) +
        ' of hours read exactly 0 tCO2/MWh, of which ' + fmtPct(imp) +
        ' are import-marginal. The MAC shown is a floor by that much.') + '">' +
        '<div class="meter-row__iso">' + iso + '</div>' +
        '<div class="meter-row__track"><div class="meter-row__fill' + (z > 0.20 ? ' hi' : '') +
          '" style="width:' + pct.toFixed(1) + '%"></div></div>' +
        '<div class="meter-row__val">' + fmtPct(z) +
          '<span style="opacity:.62"> · imp ' + fmtPct(imp) + '</span></div>' +
        '</div>';
    }).join('');
  }

  // ===========================================================================
  // CHART 3 — month × hour-of-day MER heatmap (sequential, one hue)
  // ===========================================================================
  function renderHeat() {
    var host = document.getElementById('heatChart');
    host.innerHTML = '';
    var legend = document.getElementById('heatLegend');
    document.getElementById('heatTitle').textContent =
      'Marginal emission rate — month × hour of day · ' + state.iso + ' ' + state.year;

    var c = cell(state.iso, state.year);
    if (!c) {
      host.innerHTML = '<p class="mac-fig__sub" style="margin:8px 0 0">' + state.iso +
        ' is <b>pending</b> for ' + state.year +
        ' — no grid is drawn, because no rate has been measured. Pick another grid, or wait ' +
        'for this lane’s control replay.</p>';
      legend.innerHTML = '';
      return;
    }
    var grid = c.mer_month_hour;
    var shape = (DATA.shape || {})[state.tech] || null;

    var W = width('heatChart', 900);
    var padL = 46, padR = 12, padT = 20, padB = 34;
    var cw = (W - padL - padR) / 24, ch = 21, H = padT + 12 * ch + padB;

    var hi = 0;
    grid.forEach(function (r) { r.forEach(function (v) { if (v > hi) hi = v; }); });
    var STEPS = ['--mac-s1', '--mac-s2', '--mac-s3', '--mac-s4', '--mac-s5'];
    function bin(v) { return Math.min(Math.floor(v / hi * STEPS.length), STEPS.length - 1); }

    var svg = svgRoot(W, H,
      'Marginal emission rate by month and hour of day for ' + state.iso + ' ' + state.year +
      ', tonnes CO2 per megawatt hour.');

    for (var h = 0; h < 24; h += 3) {
      txt(svg, padL + (h + 0.5) * cw, padT - 6, String(h), 'ax-label', 'middle');
    }
    grid.forEach(function (row, m) {
      txt(svg, padL - 7, padT + m * ch + ch / 2 + 4, MONTHS[m], 'ax-label', 'end');
      row.forEach(function (v, hh) {
        var dim = state.shape && shape ? shape[m][hh] : 1;
        var r = svgEl('rect', {
          x: padL + hh * cw + 1, y: padT + m * ch + 1,           // 2px surface gap between fills
          width: Math.max(cw - 2, 1), height: ch - 2, rx: 2,
          fill: 'var(' + STEPS[bin(v)] + ')',
          opacity: state.shape && shape ? (0.13 + 0.87 * Math.min(dim / 0.55, 1)) : 1
        });
        title(r, MONTHS[m] + ', hour ' + hh + ': ' + fmtRate(v) + ' tCO₂/MWh' +
          (shape ? ' · ' + techLabel(state.tech) + ' output ' +
                   (shape[m][hh] * 100).toFixed(0) + '% of its peak' : ''));
        bindTip(r, '<b>' + MONTHS[m] + ' · hour ' + hh + '</b><br>rate <b>' + fmtRate(v) +
          '</b> tCO₂/MWh' + (shape ? '<br>' + techLabel(state.tech) + ' output ' +
          (shape[m][hh] * 100).toFixed(0) + '% of peak' : ''));
        svg.appendChild(r);
      });
    });
    txt(svg, 2, H - 8, 'hour of day (local)', 'ax-title');
    host.appendChild(svg);

    legend.innerHTML = STEPS.map(function (s, i) {
      var a = (hi * i / STEPS.length), b = (hi * (i + 1) / STEPS.length);
      return '<span><i class="sq" style="background:var(' + s + ')"></i>' +
        a.toFixed(2) + '–' + b.toFixed(2) + '</span>';
    }).join('') + '<span style="opacity:.8">tCO₂/MWh' +
      (state.shape ? ' · dimmed = hours ' + techLabel(state.tech) + ' barely generates in' : '') +
      '</span>';
  }

  // ===========================================================================
  // CHART 4 — cost stack, $/MWh only (the unit never changes mid-chart)
  // ===========================================================================
  function renderWaterfall() {
    var host = document.getElementById('wfChart');
    host.innerHTML = '';
    document.getElementById('wfTitle').textContent =
      'How the number is built — ' + state.iso + ', ' + techLabel(state.tech) + ', ' + state.year;

    var s = scalars(state.iso, state.year, state.tech);
    if (!s) {
      host.innerHTML = '<p class="mac-fig__sub" style="margin:8px 0 0">' + state.iso +
        ' is <b>pending</b> for ' + state.year + ' — there is no stack to build.</p>';
      document.getElementById('wfTable').innerHTML = '';
      legend('wfLegend', false);
      return;
    }

    legend('wfLegend', true);
    var credit = s.lcoe_post_ira - s.lcoe_pre_ira;                 // negative
    var cfAdj = s.cost_per_delivered_mwh_post_ira - s.lcoe_post_ira;   // either sign
    var net = s.cost_per_delivered_mwh_post_ira - s.capture_price;
    var steps = [
      { k: 'LCOE, national base CF', v: s.lcoe_pre_ira, type: 'start' },
      { k: 'IRA credit (' + (state.tech === 'wind' ? '§45 PTC' : '§48 ITC') + ')', v: credit, type: 'delta' },
      { k: 'LCOE after credit', v: s.lcoe_post_ira, type: 'sub' },
      { k: 'CF adjustment (' + s.cf_base.toFixed(2) + ' → ' + s.cf_expected.toFixed(3) + ')', v: cfAdj, type: 'delta' },
      { k: 'Cost per delivered MWh', v: s.cost_per_delivered_mwh_post_ira, type: 'sub' },
      { k: 'less capture price', v: -s.capture_price, type: 'delta' },
      { k: 'Net cost gap', v: net, type: 'total' }
    ];

    var W = width('wfChart', 880);
    var padL = 200, padR = 96, padT = 16, padB = 46;
    var rowH = 34, H = padT + steps.length * rowH + padB;

    var run = 0, lo = 0, hi = 0;
    steps.forEach(function (st) {
      if (st.type === 'delta') { st.from = run; run += st.v; st.to = run; }
      else { st.from = 0; st.to = st.v; run = st.v; }
      lo = Math.min(lo, st.from, st.to); hi = Math.max(hi, st.from, st.to);
    });
    var padv = (hi - lo) * 0.06 || 1;
    lo -= padv; hi += padv;
    var x = function (v) { return padL + (v - lo) / (hi - lo) * (W - padL - padR); };

    var svg = svgRoot(W, H, 'Cost stack in dollars per megawatt hour for ' + state.iso +
      ', ' + techLabel(state.tech) + ', ' + state.year + '.');
    ticks(lo, hi, 5).forEach(function (t) {
      svg.appendChild(svgEl('line', {
        x1: x(t), x2: x(t), y1: padT - 6, y2: H - padB + 2,
        class: t === 0 ? 'zero-line' : 'grid-line'
      }));
      txt(svg, x(t), padT - 11, '$' + t, 'ax-label', 'middle');
    });
    txt(svg, 2, H - 26, '$ per MWh — one unit throughout', 'ax-title');

    steps.forEach(function (st, i) {
      var cy = padT + i * rowH + rowH / 2;
      txt(svg, padL - 12, cy + 4, st.k, 'row-label', 'end');
      var x0 = Math.min(x(st.from), x(st.to)), x1 = Math.max(x(st.from), x(st.to));
      var fill = st.type === 'delta'
        ? (st.v >= 0 ? 'var(--mac-warm)' : 'var(--mac-cool)')
        : 'var(--mac-total)';
      var r = svgEl('rect', {
        x: x0, y: cy - 9, width: Math.max(x1 - x0, 2.5), height: 18, rx: 4, fill: fill
      });
      title(r, st.k + ': ' + fmtMWh(st.type === 'delta' ? st.v : st.to) + ' per MWh');
      bindTip(r, '<b>' + esc(st.k) + '</b><br>' +
        (st.type === 'delta' ? (st.v >= 0 ? 'adds ' : 'subtracts ') + fmtMWh(Math.abs(st.v))
                             : 'running total ' + fmtMWh(st.to)) + ' /MWh');
      svg.appendChild(r);
      var lbl = txt(svg, x1 + 8, cy + 4,
        (st.type === 'delta' ? (st.v >= 0 ? '+' : '−') + fmtMWh(Math.abs(st.v)).replace('$', '$')
                             : fmtMWh(st.to)), 'val-label');
      lbl.setAttribute('fill', 'var(--mac-ink)');
    });

    // The one division, stated rather than drawn — this is where the unit changes.
    var div = svgEl('text', { x: padL, y: H - 6, class: 'val-label' });
    div.textContent = '÷ ' + fmtRate(s.mer_tech) + ' tCO₂/MWh  =  ' +
      fmtT(s.mac_post_ira) + ' per tonne  (pre-IRA ' + fmtT(s.mac_pre_ira) + ')';
    div.setAttribute('fill', 'var(--mac-accent)');
    svg.appendChild(div);
    host.appendChild(svg);

    document.getElementById('wfTable').innerHTML =
      '<table class="mac-table"><thead><tr><th scope="col">Step</th>' +
      '<th scope="col">$/MWh</th><th scope="col">Running</th></tr></thead><tbody>' +
      steps.map(function (st) {
        return '<tr><td>' + esc(st.k) + '</td><td>' +
          (st.type === 'delta' ? fmtMWh(st.v) : '—') + '</td><td>' + fmtMWh(st.to) + '</td></tr>';
      }).join('') +
      '<tr><td><b>÷ marginal emission rate</b></td><td>' + fmtRate(s.mer_tech) +
      ' tCO₂/MWh</td><td><b>' + fmtT(s.mac_post_ira) + '/t</b></td></tr></tbody></table>';
  }

  // ===========================================================================
  // PENDING detail cards
  // ===========================================================================
  function renderPending() {
    var host = document.getElementById('pendingGrid');
    var head = document.getElementById('pendingHead');
    var pend = ISOS.filter(function (iso) { return !cell(iso, state.year); });
    head.textContent = pend.length
      ? 'Grids still pending — ' + pend.length + ' of ' + ISOS.length + ' for ' + state.year
      : 'Every grid has landed for ' + state.year;
    if (!pend.length) {
      host.innerHTML = '<p class="mac-sub" style="margin:0">All ' + ISOS.length +
        ' modeled grids carry a measured marginal emission rate for ' + state.year + '.</p>';
      return;
    }
    host.innerHTML = pend.map(function (iso) {
      return '<div class="pending-card"><h4>' + iso + pendingChip() + '</h4>' +
        '<p>Its designated keeper predates <code>fba0ecd7</code>, the commit that first emitted the ' +
        'emissions dual, so the column simply is not in the file:</p>' +
        '<p><code>results/calibration/' + KEEPER_BUNDLE[iso] + '/hourly/system_' + state.year +
        '.parquet</code> — <b>no <code>marginal_emission_rate</code> column</b></p>' +
        '<p style="margin-bottom:0">Unblocked by that lane’s next control replay. Nothing is ' +
        'estimated, carried over from another grid, or shown as zero in the meantime.</p></div>';
    }).join('');
  }

  // ===========================================================================
  // controls, hash, wiring
  // ===========================================================================
  function seg(hostId, items, current, onPick) {
    var host = document.getElementById(hostId);
    host.innerHTML = items.map(function (it) {
      var v = it[0], l = it[1];
      return '<button type="button" data-v="' + v + '"' +
        (String(v) === String(current) ? ' class="active" aria-pressed="true"' : ' aria-pressed="false"') +
        '>' + l + '</button>';
    }).join('');
    Array.prototype.forEach.call(host.querySelectorAll('button'), function (b) {
      b.addEventListener('click', function () { onPick(b.getAttribute('data-v')); });
    });
  }

  function renderIsoSelect() {
    var sel = document.getElementById('isoSel');
    sel.innerHTML = ISOS.map(function (iso) {
      var ok = !!cell(iso, state.year);
      return '<option value="' + iso + '"' + (iso === state.iso ? ' selected' : '') + '>' +
        iso + (ok ? '' : '  — pending') + '</option>';
    }).join('');
    var dot = document.getElementById('isoDot');
    var ok = !!cell(state.iso, state.year);
    dot.style.background = ok ? 'var(--mac-accent)' : 'var(--mac-pending)';
    dot.style.boxShadow = 'none';
  }

  function writeHash() {
    location.replace('#iso=' + state.iso + '&year=' + state.year +
      '&tech=' + state.tech + '&state=' + state.synth);
  }
  function readHash() {
    var p = {};
    location.hash.replace(/^#/, '').split('&').forEach(function (kv) {
      var i = kv.indexOf('=');
      if (i > 0) p[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1));
    });
    if (ISOS.indexOf(p.iso) >= 0) state.iso = p.iso;
    if (YEARS.indexOf(parseInt(p.year, 10)) >= 0) state.year = parseInt(p.year, 10);
    if (p.tech === 'wind' || p.tech === 'solar') state.tech = p.tech;
    if (SYNTH_STATES[p.state]) state.synth = p.state;
  }

  function renderAll() {
    seg('yearSel', YEARS.map(function (y) { return [y, y]; }), state.year, function (v) {
      state.year = parseInt(v, 10); writeHash(); renderAll();
    });
    seg('techSel', TECHS, state.tech, function (v) { state.tech = v; writeHash(); renderAll(); });
    renderIsoSelect();
    renderHero();
    renderTiles();
    renderRank();
    renderDuration();
    renderMeters();
    renderHeat();
    renderWaterfall();
    renderPending();
    Object.keys(tables).forEach(function (k) {
      var el = document.getElementById(k + 'Table');
      if (el) el.hidden = !tables[k];
    });
    var st = document.getElementById('shapeToggle');
    st.setAttribute('aria-pressed', state.shape ? 'true' : 'false');
    st.textContent = state.shape
      ? 'Overlay on — showing ' + techLabel(state.tech) + '’s hours'
      : 'Overlay the technology’s hours';
  }

  function init() {
    readHash();

    document.getElementById('isoSel').addEventListener('change', function (e) {
      state.iso = e.target.value; writeHash(); renderAll();
    });
    document.getElementById('shapeToggle').addEventListener('click', function () {
      state.shape = !state.shape; renderHeat();
      var st = document.getElementById('shapeToggle');
      st.setAttribute('aria-pressed', state.shape ? 'true' : 'false');
      st.textContent = state.shape
        ? 'Overlay on — showing ' + techLabel(state.tech) + '’s hours'
        : 'Overlay the technology’s hours';
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-table]'), function (b) {
      b.addEventListener('click', function () {
        var k = b.getAttribute('data-table');
        tables[k] = !tables[k];
        document.getElementById(k + 'Table').hidden = !tables[k];
        b.setAttribute('aria-expanded', tables[k] ? 'true' : 'false');
        b.textContent = tables[k] ? 'Hide table' : 'Table';
      });
    });
    Array.prototype.forEach.call(document.querySelectorAll('.synth-banner__states button'), function (b) {
      b.addEventListener('click', function () {
        state.synth = b.getAttribute('data-state');
        Array.prototype.forEach.call(document.querySelectorAll('.synth-banner__states button'), function (o) {
          o.setAttribute('aria-pressed', o === b ? 'true' : 'false');
        });
        writeHash(); renderAll();
      });
      b.setAttribute('aria-pressed', b.getAttribute('data-state') === state.synth ? 'true' : 'false');
    });

    var rid = null;
    window.addEventListener('resize', function () {
      if (rid) cancelAnimationFrame(rid);
      rid = requestAnimationFrame(function () {
        renderRank(); renderDuration(); renderHeat(); renderWaterfall();
      });
    });

    renderAll();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
