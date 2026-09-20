/**
 * marginal-abatement.js — renderer for marginal-abatement.html.
 *
 * Reads window.MAC_DATA — the generated index over the committed per-grid-year
 * sidecars in frontend/data/mac/. A grid with no sidecar for the selected year
 * renders as `pending`; a grid whose sidecar says a technology is not present
 * (no wind fleet at all, say) renders that reason instead of a number. Neither
 * is ever shown as a zero.
 *
 * Charts are hand-rolled SVG — no CDN dependency, and themed entirely by the
 * CSS custom properties on .mac-scope, which the page redeclares under
 * .section-dark (this design system has no global dark toggle).
 *
 * Reader-facing text in here carries NO repo, commit or file references: the
 * page has to stand on its own for someone who has never seen this codebase.
 */
(function () {
  'use strict';

  var ISOS = ['ERCOT', 'CAISO', 'MISO', 'PJM', 'NYISO', 'NEISO', 'SPP', 'NWPP', 'SOCO'];
  var YEARS = [2023, 2024, 2025];
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  var DATA = window.MAC_DATA || { cells: {}, isos: [], years: [] };

  // imports: 'counted' charges imported power the average rate of the grid it
  // came from; 'zero' leaves it at zero. 'counted' is the default — it is the
  // more accurate of the two.
  var state = { year: 2024, tech: 'wind', iso: null, shape: false, imports: 'counted' };
  var tables = { range: false, dur: false, wf: false };

  // ---------------------------------------------------------------------------
  // data access
  // ---------------------------------------------------------------------------
  /** Grids with a sidecar for the selected year, in roster order. */
  function readySet() {
    return ISOS.filter(function (iso) { return !!DATA.cells[iso + '-' + state.year]; });
  }
  function cell(iso, year) { return DATA.cells[iso + '-' + year] || null; }
  /** Scalars for a grid-year-technology, or null when there is no number.
   *  Null covers two different things the UI must not conflate: the grid is
   *  pending, or the grid genuinely has no fleet of that technology. Callers
   *  that need to tell them apart use unavailableReason(). */
  function scalars(iso, year, tech) {
    var c = cell(iso, year);
    var s = c && c.scalars ? c.scalars[tech] : null;
    return s && !s.unavailable ? s : null;
  }
  /** Why a technology has no number on a grid that HAS landed, else null. */
  function unavailableReason(iso, year, tech) {
    var c = cell(iso, year);
    var s = c && c.scalars ? c.scalars[tech] : null;
    return s && s.unavailable ? s.unavailable : null;
  }
  var withImports = function () { return state.imports === 'counted'; };
  /** Headline cost per tonne, under the current import treatment. */
  function mac(s, which) {
    return s['mac_' + which + '_ira' + (withImports() ? '_with_imports' : '')];
  }
  /** CO2 avoided per MWh, under the current import treatment. */
  function rate(s) { return withImports() ? s.mer_tech_with_imports : s.mer_tech; }

  // ---------------------------------------------------------------------------
  // formatting
  // ---------------------------------------------------------------------------
  function fmtT(v) { return (v < 0 ? '−' : '') + '$' + Math.abs(v).toFixed(0); }
  function fmtT1(v) { return (v < 0 ? '−' : '') + '$' + Math.abs(v).toFixed(1); }
  function fmtMWh(v) { return (v < 0 ? '−' : '') + '$' + Math.abs(v).toFixed(2); }
  function fmtRate(v) { return v.toFixed(3); }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function techLabel(t) { return t === 'wind' ? 'wind' : 'solar'; }

  var CLOCK =
    '<svg viewBox="0 0 12 12" aria-hidden="true">' +
    '<circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M6 3.2v3.2l2 1.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>';

  // ---------------------------------------------------------------------------
  // tooltip
  // ---------------------------------------------------------------------------
  var tip = document.createElement('div');
  tip.className = 'bc-tooltip';
  tip.style.display = 'none';
  document.body.appendChild(tip);
  function bindTip(node, html) {
    node.addEventListener('mousemove', function (e) {
      tip.innerHTML = html; tip.style.display = 'block';
      tip.style.left = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 10) + 'px';
      tip.style.top = Math.max(e.clientY - tip.offsetHeight - 12, 8) + 'px';
    });
    node.addEventListener('mouseleave', function () { tip.style.display = 'none'; });
  }

  // ---------------------------------------------------------------------------
  // SVG helpers
  // ---------------------------------------------------------------------------
  var NS = 'http://www.w3.org/2000/svg';
  function svgEl(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] !== null && attrs[k] !== undefined) e.setAttribute(k, attrs[k]);
    return e;
  }
  function svgRoot(w, h, label) {
    return svgEl('svg', { width: w, height: h, viewBox: '0 0 ' + w + ' ' + h, role: 'img', 'aria-label': label });
  }
  function txt(parent, x, y, s, cls, anchor) {
    var t = svgEl('text', { x: x, y: y, class: cls || '', 'text-anchor': anchor || 'start' });
    t.textContent = s; parent.appendChild(t); return t;
  }
  function title(node, s) { var t = svgEl('title', {}); t.textContent = s; node.appendChild(t); }
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
  function legend(id, show) { var el = document.getElementById(id); if (el) el.hidden = !show; }
  function width(id, fallback) {
    var el = document.getElementById(id);
    return Math.max((el ? el.clientWidth : 0) || fallback || 640, 300);
  }

  // ===========================================================================
  // HERO
  // ===========================================================================
  function renderCoverage() {
    var el = document.getElementById('coverage');
    if (!el) return;
    var n = readySet().length, tot = ISOS.length;
    el.innerHTML = n === tot
      ? 'All ' + tot + ' modelled grids, ' + state.year + '.'
      : '<b>' + n + ' of ' + tot + ' modelled grids</b> have been measured for ' +
        state.year + '. The rest are marked pending — nothing is estimated for them.';
  }

  function renderHero() {
    var rows = [];
    readySet().forEach(function (iso) {
      ['wind', 'solar'].forEach(function (t) {
        var s = scalars(iso, state.year, t);
        if (s) rows.push({ iso: iso, tech: t, v: mac(s, 'post') });
      });
    });
    rows.sort(function (a, b) { return a.v - b.v; });

    var find = document.getElementById('heroFinding');
    var sub = document.getElementById('heroSub');
    var n = readySet().length;

    if (!rows.length) {
      find.innerHTML = 'No grid has been measured yet, so there is <em>nothing to report</em> here.';
      sub.innerHTML = 'Results appear one grid at a time. Until a grid has been measured it is ' +
        'marked pending — never filled in from a neighbour, and never shown as zero.';
      return;
    }
    var lo = rows[0], hi = rows[rows.length - 1];
    find.innerHTML = rows.length === 1
      ? ('Cutting a tonne of CO<sub>2</sub> with new ' + techLabel(lo.tech) + ' in ' + lo.iso +
         ' costs <em>' + fmtT(lo.v) + '</em>.')
      : ('The cheapest way to cut a tonne of CO<sub>2</sub> is new ' + techLabel(lo.tech) + ' in <em>' +
         lo.iso + '</em> at ' + fmtT(lo.v) + '. The most expensive is new ' + techLabel(hi.tech) + ' in <em>' +
         hi.iso + '</em> at ' + fmtT(hi.v) + '.');
    sub.innerHTML = 'Same turbines, same panels — the gap is entirely about what the power sells ' +
      'for on each grid, how much of it the local weather delivers, and how dirty the electricity ' +
      'it pushes off the system is. ' +
      (n < ISOS.length ? '<b>' + n + ' of ' + ISOS.length + ' grids measured so far.</b>' : '') +
      ' Without the tax credits every number roughly triples.';
  }

  // ===========================================================================
  // CHART 1 — wind + solar range bars, every grid
  // ===========================================================================
  function renderRange() {
    var host = document.getElementById('rangeChart');
    host.innerHTML = '';
    document.getElementById('rangeTitle').innerHTML =
      'Cost to cut a tonne of CO<sub>2</sub> — ' + state.year;

    var rows = ISOS.map(function (iso) {
      var w = scalars(iso, state.year, 'wind'), s = scalars(iso, state.year, 'solar');
      var any = w || s;
      return { iso: iso, wind: w, solar: s, ready: !!any,
               sort: any ? Math.min.apply(null, [w, s].filter(Boolean)
                      .map(function (x) { return mac(x, 'post'); })) : Infinity };
    });
    rows.sort(function (a, b) {
      if (a.sort !== b.sort) return a.sort - b.sort;
      return a.iso < b.iso ? -1 : 1;
    });
    var ready = rows.filter(function (r) { return r.ready; });

    var W = width('rangeChart', 880);
    // The tech word needs its own column beside the grid name; below ~620px
    // there isn't room, and colour + legend + the value label carry it alone
    // (two series — the series-count ladder allows it).
    var showTech = W >= 620;
    var padL = showTech ? 122 : 76, padR = 58, padT = 26, padB = 32;
    // A measured grid needs room for two bars; a pending one needs a single
    // line. Giving them the same slot padded the chart with empty space when
    // most grids are pending — which is most of the time, early on.
    var groupH = 46, pendH = 26, barH = 13;
    var yTop = [], acc = padT;
    rows.forEach(function (r) { yTop.push(acc); acc += r.ready ? groupH : pendH; });
    var H = acc + padB;

    var vals = [0];
    ready.forEach(function (r) {
      ['wind', 'solar'].forEach(function (t) {
        if (r[t]) vals.push(mac(r[t], 'post'), mac(r[t], 'pre'));
      });
    });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var padv = (hi - lo) * 0.06 || 1;
    lo -= padv; hi += padv;
    var x = function (v) { return padL + (v - lo) / (hi - lo) * (W - padL - padR); };

    var svg = svgRoot(W, H, 'Cost to cut a tonne of CO2 with new wind and new solar on each grid in ' +
      state.year + '. ' + ready.length + ' of ' + rows.length + ' grids measured.');

    // No measured grid ⇒ no dollar scale. A $-axis over empty rows invites the
    // reader to place the missing values near zero.
    if (ready.length) {
      ticks(lo, hi, 6).forEach(function (t) {
        svg.appendChild(svgEl('line', {
          x1: x(t), x2: x(t), y1: padT - 8, y2: H - padB + 2,
          class: t === 0 ? 'zero-line' : 'grid-line'
        }));
        txt(svg, x(t), padT - 13, '$' + t, 'ax-label', 'middle');
      });
      txt(svg, 2, H - 8, 'dollars per tonne of CO₂ avoided — further left is cheaper', 'ax-title');
    } else {
      txt(svg, 2, H - 8, 'No scale shown — no grid has been measured for ' + state.year + '.', 'ax-title');
    }
    legend('rangeLegend', ready.length > 0);

    rows.forEach(function (r, i) {
      var y0 = yTop[i], gh = r.ready ? groupH : pendH;
      txt(svg, 2, y0 + gh / 2 + 4, r.iso, 'row-label', 'start');

      if (!r.ready) {
        var g = svgEl('g', {});
        g.appendChild(svgEl('line', {
          x1: padL, x2: W - padR, y1: y0 + pendH / 2, y2: y0 + pendH / 2,
          stroke: 'var(--mac-pending)', 'stroke-width': 1, 'stroke-dasharray': '3 5', opacity: 0.45
        }));
        var pl = txt(g, W - padR + 8, y0 + pendH / 2 + 4, 'pending', 'ax-label');
        pl.setAttribute('fill', 'var(--mac-pending)');
        pl.setAttribute('font-weight', '700');
        title(g, r.iso + ' — pending.');
        svg.appendChild(g);
        return;
      }

      [['wind', 0], ['solar', 1]].forEach(function (pair) {
        var t = pair[0];
        var s = r[t];
        if (!s) {
          // Measured grid, no fleet of this technology — say so, don't draw a
          // bar. The note goes INSIDE the plot area: it is too long for the
          // label gutter and would run back over the grid's name.
          var cyN = y0 + 12 + pair[1] * (barH + 6) + barH / 2 + 4;
          if (showTech) {
            var tn = txt(svg, padL - 10, cyN, t, 'ax-label', 'end');
            tn.setAttribute('fill', t === 'wind' ? 'var(--mac-wind)' : 'var(--mac-solar)');
            tn.setAttribute('font-weight', '700');
            tn.setAttribute('opacity', '0.55');
          }
          var nl = txt(svg, padL + 6, cyN, 'none on this grid', 'ax-label', 'start');
          nl.setAttribute('opacity', '0.7');
          return;
        }
        var cy = y0 + 12 + pair[1] * (barH + 6) + barH / 2;
        var col = t === 'wind' ? 'var(--mac-wind)' : 'var(--mac-solar)';
        var a = mac(s, 'post'), b = mac(s, 'pre');
        var g2 = svgEl('g', {});
        g2.appendChild(svgEl('rect', {
          x: Math.min(x(a), x(b)), y: cy - barH / 2,
          width: Math.max(Math.abs(x(b) - x(a)), 3), height: barH, rx: 4,
          fill: col, opacity: 0.42
        }));
        // filled end = with credits; open end = without. Shape, not just color,
        // so the pair reads without relying on hue.
        g2.appendChild(svgEl('circle', {
          cx: x(a), cy: cy, r: 5.5, fill: col, stroke: 'var(--mac-surface)', 'stroke-width': 2
        }));
        g2.appendChild(svgEl('circle', {
          cx: x(b), cy: cy, r: 5.5, fill: 'var(--mac-surface)', stroke: col, 'stroke-width': 2.5
        }));
        var l = txt(g2, Math.min(x(b) + 10, W - 4), cy + 4, fmtT(a) + ' → ' + fmtT(b), 'ax-label');
        l.setAttribute('font-weight', '600');
        if (showTech) {
          var tl = txt(g2, padL - 10, cy + 4, t, 'ax-label', 'end');
          tl.setAttribute('fill', col);
          tl.setAttribute('font-weight', '700');
        }
        bindTip(g2, '<b>' + r.iso + ' · new ' + techLabel(t) + ' · ' + state.year + '</b><br>' +
          'with credits <b>' + fmtT1(a) + '</b> per tonne<br>' +
          'without credits <b>' + fmtT1(b) + '</b> per tonne<br>' +
          'avoids ' + fmtRate(rate(s)) + ' tonnes per MWh');
        title(g2, r.iso + ' ' + techLabel(t) + ': ' + fmtT1(a) + ' per tonne with credits, ' +
          fmtT1(b) + ' without.');
        svg.appendChild(g2);
      });
    });
    host.appendChild(svg);

    // A grid can be measured and still have no fleet of one technology.
    function cellPair(x) {
      return x
        ? '<td>' + fmtT1(mac(x, 'post')) + '</td><td>' + fmtT1(mac(x, 'pre')) + '</td>'
        : '<td colspan="2" style="text-align:center;opacity:.7">none on this grid</td>';
    }
    document.getElementById('rangeTable').innerHTML =
      '<table class="mac-table"><thead><tr><th scope="col">Grid</th>' +
      '<th scope="col">Wind, with credits</th><th scope="col">Wind, without</th>' +
      '<th scope="col">Solar, with credits</th><th scope="col">Solar, without</th></tr></thead><tbody>' +
      rows.map(function (r) {
        if (!r.ready) return '<tr><td>' + r.iso + '</td><td class="pend" colspan="4">pending</td></tr>';
        return '<tr><td>' + r.iso + '</td>' +
          cellPair(r.wind) + cellPair(r.solar) + '</tr>';
      }).join('') +
      '</tbody></table><p class="mac-fig__sub" style="margin:8px 0 0">Dollars per tonne of CO₂, ' +
      state.year + '.</p>';
  }

  // ===========================================================================
  // Selected grid — headline cards
  // ===========================================================================
  function renderCards() {
    var host = document.getElementById('cards');
    var c = cell(state.iso, state.year);
    if (!c) {
      host.innerHTML = '<div class="mac-card" style="grid-column:1/-1;border-left-color:var(--mac-pending)">' +
        '<div class="mac-card__t">' + state.iso + ' · ' + state.year + '</div>' +
        '<div class="mac-card__pend"><span class="pending-chip">' + CLOCK + 'pending</span>' +
        ' &nbsp;This grid has not been measured yet.</div></div>';
      return;
    }
    host.innerHTML = ['wind', 'solar'].map(function (t) {
      var why = unavailableReason(state.iso, state.year, t);
      if (why) {
        return '<div class="mac-card' + (t === 'solar' ? ' solar' : '') + '">' +
          '<div class="mac-card__t">New ' + techLabel(t) + '</div>' +
          '<div class="mac-card__pend">No figure: ' + esc(why) + '.</div></div>';
      }
      var s = c.scalars[t];
      var net = s.cost_per_delivered_mwh_post_ira - s.capture_price;
      return '<div class="mac-card' + (t === 'solar' ? ' solar' : '') + '">' +
        '<div class="mac-card__t">New ' + techLabel(t) + '</div>' +
        '<div class="mac-card__v">' + fmtT1(mac(s, 'post')) + '<span class="unit">per tonne of CO₂</span></div>' +
        '<div class="mac-card__alt">' + fmtT1(mac(s, 'pre')) + ' without the tax credits</div>' +
        '<div class="mac-card__rows">' +
        'Costs <b>' + fmtMWh(s.cost_per_delivered_mwh_post_ira) + '</b> to deliver a MWh here<br>' +
        'Earns <b>' + fmtMWh(s.capture_price) + '</b> when it sells that MWh<br>' +
        'Avoids <b>' + fmtRate(rate(s)) + '</b> tonnes of CO₂ per MWh<br>' +
        '<span style="opacity:.8">' + fmtMWh(net) + ' extra ÷ ' + fmtRate(rate(s)) +
        ' tonnes = ' + fmtT1(mac(s, 'post')) + '</span>' +
        '</div></div>';
    }).join('');
  }

  // ===========================================================================
  // CHART 2 — month × hour heatmap
  // ===========================================================================
  function renderHeat() {
    var host = document.getElementById('heatChart');
    host.innerHTML = '';
    var legendEl = document.getElementById('heatLegend');
    document.getElementById('heatTitle').textContent =
      'When is ' + state.iso + ' dirtiest? · ' + state.year;

    var c = cell(state.iso, state.year);
    if (!c) {
      host.innerHTML = '<p class="mac-fig__sub" style="margin:8px 0 0">' + state.iso + ' is pending.</p>';
      legendEl.innerHTML = '';
      return;
    }
    var grid = c.mer_month_hour;
    // The per-technology hourly shape is not in the committed sidecar (it would
    // roughly double its size for a presentational overlay), so the overlay
    // button only appears when a shape is available.
    var shape = (DATA.shape || {})[state.tech] || null;

    var W = width('heatChart', 560);
    var padL = 38, padR = 8, padT = 18, padB = 30;
    var cw = (W - padL - padR) / 24, ch = 19, H = padT + 12 * ch + padB;

    var hi = 0;
    grid.forEach(function (r) { r.forEach(function (v) { if (v > hi) hi = v; }); });
    var STEPS = ['--mac-s1', '--mac-s2', '--mac-s3', '--mac-s4', '--mac-s5'];
    function bin(v) { return Math.min(Math.floor(v / hi * STEPS.length), STEPS.length - 1); }

    var svg = svgRoot(W, H, 'CO2 caused by one extra megawatt-hour of demand in ' + state.iso +
      ' ' + state.year + ', by month and hour of day.');
    for (var h = 0; h < 24; h += 4) txt(svg, padL + (h + 0.5) * cw, padT - 5, String(h), 'ax-label', 'middle');
    grid.forEach(function (row, m) {
      txt(svg, padL - 6, padT + m * ch + ch / 2 + 4, MONTHS[m], 'ax-label', 'end');
      row.forEach(function (v, hh) {
        var dim = state.shape && shape ? shape[m][hh] : 1;
        var r = svgEl('rect', {
          x: padL + hh * cw + 1, y: padT + m * ch + 1,
          width: Math.max(cw - 2, 1), height: ch - 2, rx: 2,
          fill: 'var(' + STEPS[bin(v)] + ')',
          opacity: state.shape && shape ? (0.12 + 0.88 * Math.min(dim / 0.55, 1)) : 1
        });
        title(r, MONTHS[m] + ', hour ' + hh + ': ' + fmtRate(v) + ' tonnes per MWh');
        bindTip(r, '<b>' + MONTHS[m] + ' · hour ' + hh + '</b><br>' + fmtRate(v) + ' tonnes of CO₂ ' +
          'per extra MWh' + (shape ? '<br>' + techLabel(state.tech) + ' output: ' +
          (shape[m][hh] * 100).toFixed(0) + '% of its peak' : ''));
        svg.appendChild(r);
      });
    });
    txt(svg, 2, H - 8, 'hour of day', 'ax-title');
    host.appendChild(svg);

    legendEl.innerHTML = STEPS.map(function (s, i) {
      return '<span><i style="background:var(' + s + ')"></i>' +
        (hi * i / STEPS.length).toFixed(2) + '–' + (hi * (i + 1) / STEPS.length).toFixed(2) + '</span>';
    }).join('') + '<span style="opacity:.85">tonnes of CO₂ per extra MWh' +
      (state.shape ? ' · faded = hours ' + techLabel(state.tech) + ' barely generates' : '') + '</span>';
  }

  // ===========================================================================
  // CHART 3 — duration curve, one grid
  // ===========================================================================
  function renderDuration() {
    var host = document.getElementById('durChart');
    host.innerHTML = '';
    var c = cell(state.iso, state.year);
    if (!c) {
      host.innerHTML = '<p class="mac-fig__sub" style="margin:8px 0 0">' + state.iso + ' is pending.</p>';
      document.getElementById('durTable').innerHTML = '';
      legend('durLegend', false);
      return;
    }
    legend('durLegend', true);

    // The raw curve ends in a flat run of exact zeros: hours whose marginal
    // resource emits nothing *on this grid*. Some of those are genuinely clean
    // (nuclear, hydro, wind); the rest are imports, where the emissions simply
    // happen across the border. When imports are being counted, lift that share
    // of the tail onto the source region's rate and re-sort, so the chart shows
    // the same quantity the headline does.
    var d = c.mer_duration.slice(), n = d.length;
    if (withImports() && c.system.import_marginal_hour_share > 0) {
      var nLift = Math.round(c.system.import_marginal_hour_share * n);
      var ef = c.system.import_emission_rate;
      for (var i = n - 1, done = 0; i >= 0 && done < nLift; i--) {
        if (d[i] === 0) { d[i] = ef; done++; }
      }
      d.sort(function (a, b) { return b - a; });
    }
    var avg = d.reduce(function (a, v) { return a + v; }, 0) / n;

    var W = width('durChart', 560), H = 268;
    var padL = 42, padR = 12, padT = 14, padB = 38;
    // ROBUST SCALE. At a degenerate optimum the underlying derivative is
    // genuinely two-sided and the solver can report an extreme value — measured
    // across these grids, a handful of hours a year, once as far as -7.7 against
    // a physical range of roughly 0 to 1.4. They move the yearly averages by
    // less than 0.005, so they are NOT removed from the data; but on a linear
    // axis one of them flattens the whole curve, so the SCALE is set from the
    // 1st/99th percentile and outliers are drawn clamped to the edge and
    // counted underneath. Nothing is hidden: the count is on the page.
    var sorted = d.slice().sort(function (a, b) { return a - b; });
    var q = function (f) { return sorted[Math.min(n - 1, Math.max(0, Math.round(f * (n - 1))))]; };
    var hi = Math.max(q(0.99) * 1.10, 0.1);
    var lo = Math.min(q(0.01), 0);
    var nOut = d.filter(function (v) { return v > hi || v < lo; }).length;
    var clamp = function (v) { return Math.min(hi, Math.max(lo, v)); };
    var x = function (i) { return padL + i / (n - 1) * (W - padL - padR); };
    var y = function (v) { return H - padB - (clamp(v) - lo) / (hi - lo) * (H - padT - padB); };

    var svg = svgRoot(W, H, 'Every hour of ' + state.year + ' in ' + state.iso +
      ', sorted from the dirtiest to the cleanest.');
    ticks(lo, hi, 5).forEach(function (t) {
      svg.appendChild(svgEl('line', { x1: padL, x2: W - padR, y1: y(t), y2: y(t), class: 'grid-line' }));
      txt(svg, padL - 7, y(t) + 4, t.toFixed(2), 'ax-label', 'end');
    });
    [0, 25, 50, 75, 100].forEach(function (p) {
      txt(svg, x((p / 100) * (n - 1)), H - padB + 15, p + '%', 'ax-label', 'middle');
    });
    txt(svg, 2, H - 8, 'hours of the year, dirtiest first', 'ax-title');
    txt(svg, 8, padT + 4, 'tonnes CO₂ / MWh', 'ax-title');

    var area = svgEl('path', {
      d: d.map(function (v, i) { return (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1); }).join('') +
         'L' + x(n - 1).toFixed(1) + ' ' + y(lo) + 'L' + x(0).toFixed(1) + ' ' + y(lo) + 'Z',
      fill: 'var(--mac-accent)', opacity: 0.14
    });
    svg.appendChild(area);
    svg.appendChild(svgEl('path', {
      d: d.map(function (v, i) { return (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1); }).join(''),
      fill: 'none', stroke: 'var(--mac-accent)', 'stroke-width': 2.5, 'stroke-linejoin': 'round'
    }));
    // The average, drawn so "it is not an average" is a thing you can see.
    svg.appendChild(svgEl('line', {
      x1: padL, x2: W - padR, y1: y(avg), y2: y(avg),
      stroke: 'var(--mac-warm)', 'stroke-width': 1.5, 'stroke-dasharray': '5 4'
    }));
    var al = txt(svg, W - padR - 2, y(avg) - 6, 'average ' + fmtRate(avg), 'ax-label', 'end');
    al.setAttribute('fill', 'var(--mac-warm)');
    al.setAttribute('font-weight', '700');
    host.appendChild(svg);

    document.getElementById('durLegend').innerHTML =
      '<span><i style="background:var(--mac-accent)"></i> ' + state.iso + ', every hour sorted</span>' +
      '<span><i style="background:var(--mac-warm)"></i> the yearly average</span>' +
      (nOut ? '<span style="opacity:.8">' + nOut + ' hour' + (nOut > 1 ? 's' : '') +
              ' fall outside this scale (see the last note below)</span>' : '');

    document.getElementById('durTable').innerHTML =
      '<table class="mac-table"><thead><tr><th scope="col">Hours of the year</th>' +
      '<th scope="col">Tonnes CO₂ per MWh</th></tr></thead><tbody>' +
      [['dirtiest hour', 0], ['dirtiest 10%', 10], ['dirtiest 25%', 25], ['middle', 50],
       ['cleanest 25%', 75], ['cleanest 10%', 90]].map(function (p) {
        return '<tr><td>' + p[0] + '</td><td>' +
          fmtRate(d[Math.min(Math.round(p[1] / 100 * (n - 1)), n - 1)]) + '</td></tr>';
      }).join('') +
      '<tr><td><b>yearly average</b></td><td><b>' + fmtRate(avg) + '</b></td></tr></tbody></table>';
  }

  // ===========================================================================
  // CHART 4 — cost stack, $/MWh only
  // ===========================================================================
  function renderWaterfall() {
    var host = document.getElementById('wfChart');
    host.innerHTML = '';
    document.getElementById('wfTitle').textContent =
      'Where the cost comes from — ' + state.iso + ', new ' + techLabel(state.tech) + ', ' + state.year;

    var s = scalars(state.iso, state.year, state.tech);
    if (!s) {
      // Grid-level pending and "this grid has no fleet of this technology" are
      // different facts, and this chart is the one place they collide: SOCO is
      // fully measured and still has no wind to cost.
      var why = unavailableReason(state.iso, state.year, state.tech);
      host.innerHTML = '<p class="mac-fig__sub" style="margin:8px 0 0">' +
        (why ? 'No cost to break down: ' + esc(why) + '.' : state.iso + ' is pending.') + '</p>';
      document.getElementById('wfTable').innerHTML = '';
      legend('wfLegend', false);
      return;
    }
    legend('wfLegend', true);

    var credit = s.lcoe_post_ira - s.lcoe_pre_ira;
    var net = s.cost_per_delivered_mwh_post_ira - s.capture_price;
    // Local resource quality is NOT a step in this waterfall — it is already
    // inside every dollar figure here, because it sets the megawatt-hours the
    // build cost is divided by rather than adding or removing a cost. The
    // sub-heading and the caveats say so; a bar would misrepresent it as an
    // adjustment applied on top.
    var steps = [
      { k: 'Cost to build and run it', v: s.lcoe_pre_ira, type: 'start' },
      { k: 'Less the tax credit', v: credit, type: 'delta' },
      { k: 'Cost per MWh delivered here', v: s.lcoe_post_ira, type: 'sub' },
      { k: 'Less what the power sells for', v: -s.capture_price, type: 'delta' },
      { k: 'Extra cost of the clean MWh', v: net, type: 'total' }
    ];

    var W = width('wfChart', 880);
    var padL = Math.min(230, Math.max(150, W * 0.26)), padR = 92, padT = 16, padB = 48;
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

    var svg = svgRoot(W, H, 'How the cost per megawatt-hour is built up for new ' +
      techLabel(state.tech) + ' in ' + state.iso + ', ' + state.year + '.');
    ticks(lo, hi, 5).forEach(function (t) {
      svg.appendChild(svgEl('line', {
        x1: x(t), x2: x(t), y1: padT - 6, y2: H - padB + 2,
        class: t === 0 ? 'zero-line' : 'grid-line'
      }));
      txt(svg, x(t), padT - 11, '$' + t, 'ax-label', 'middle');
    });
    txt(svg, 2, H - 28, 'dollars per megawatt-hour', 'ax-title');

    steps.forEach(function (st, i) {
      var cy = padT + i * rowH + rowH / 2;
      txt(svg, padL - 12, cy + 4, st.k, 'row-label', 'end').setAttribute('font-size', '12px');
      var x0 = Math.min(x(st.from), x(st.to)), x1 = Math.max(x(st.from), x(st.to));
      var fill = st.type === 'delta'
        ? (st.v >= 0 ? 'var(--mac-warm)' : 'var(--mac-cool)')
        : 'var(--mac-total)';
      var r = svgEl('rect', { x: x0, y: cy - 9, width: Math.max(x1 - x0, 2.5), height: 18, rx: 4, fill: fill });
      title(r, st.k + ': ' + fmtMWh(st.type === 'delta' ? st.v : st.to) + ' per MWh');
      bindTip(r, '<b>' + esc(st.k) + '</b><br>' +
        (st.type === 'delta' ? (st.v >= 0 ? 'adds ' : 'takes off ') + fmtMWh(Math.abs(st.v))
                             : 'running total ' + fmtMWh(st.to)) + ' per MWh');
      svg.appendChild(r);
      txt(svg, x1 + 8, cy + 4,
        st.type === 'delta' ? (st.v >= 0 ? '+' : '−') + fmtMWh(Math.abs(st.v)) : fmtMWh(st.to),
        'val-label').setAttribute('fill', 'var(--mac-ink)');
    });

    var div = svgEl('text', { x: 2, y: H - 8, class: 'val-label' });
    div.textContent = fmtMWh(net) + ' ÷ ' + fmtRate(rate(s)) + ' tonnes per MWh = ' +
      fmtT1(mac(s, 'post')) + ' per tonne';
    div.setAttribute('fill', 'var(--mac-accent)');
    svg.appendChild(div);
    host.appendChild(svg);

    document.getElementById('wfTable').innerHTML =
      '<table class="mac-table"><thead><tr><th scope="col">Step</th><th scope="col">$/MWh</th>' +
      '<th scope="col">Running total</th></tr></thead><tbody>' +
      steps.map(function (st) {
        return '<tr><td>' + esc(st.k) + '</td><td>' +
          (st.type === 'delta' ? fmtMWh(st.v) : '—') + '</td><td>' + fmtMWh(st.to) + '</td></tr>';
      }).join('') +
      '<tr><td><b>÷ CO₂ avoided per MWh</b></td><td>' + fmtRate(rate(s)) +
      '</td><td><b>' + fmtT1(mac(s, 'post')) + ' per tonne</b></td></tr></tbody></table>';
  }

  // ===========================================================================
  // controls
  // ===========================================================================
  function seg(hostId, items, current, onPick) {
    var host = document.getElementById(hostId);
    host.innerHTML = items.map(function (it) {
      return '<button type="button" data-v="' + it[0] + '"' +
        (String(it[0]) === String(current) ? ' class="active" aria-pressed="true"' : ' aria-pressed="false"') +
        '>' + it[1] + '</button>';
    }).join('');
    Array.prototype.forEach.call(host.querySelectorAll('button'), function (b) {
      b.addEventListener('click', function () { onPick(b.getAttribute('data-v')); });
    });
  }

  function renderPicker() {
    var host = document.getElementById('isoPicker');
    host.innerHTML = ISOS.map(function (iso) {
      var ok = !!cell(iso, state.year);
      return '<button type="button" class="iso-btn' + (ok ? '' : ' is-pending') + '" data-iso="' + iso + '"' +
        ' aria-pressed="' + (iso === state.iso ? 'true' : 'false') + '">' +
        (ok ? '' : '<span class="dot" aria-hidden="true"></span>') + iso +
        (ok ? '' : ' <span style="font-weight:500;opacity:.85">pending</span>') + '</button>';
    }).join('');
    Array.prototype.forEach.call(host.querySelectorAll('.iso-btn'), function (b) {
      b.addEventListener('click', function () {
        state.iso = b.getAttribute('data-iso'); writeHash(); renderAll();
      });
    });
  }

  function writeHash() {
    location.replace('#grid=' + state.iso + '&year=' + state.year + '&tech=' + state.tech +
      '&imports=' + state.imports);
  }
  function readHash() {
    var p = {};
    location.hash.replace(/^#/, '').split('&').forEach(function (kv) {
      var i = kv.indexOf('=');
      if (i > 0) p[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1));
    });
    if (ISOS.indexOf(p.grid) >= 0) state.iso = p.grid;
    if (YEARS.indexOf(parseInt(p.year, 10)) >= 0) state.year = parseInt(p.year, 10);
    if (p.tech === 'wind' || p.tech === 'solar') state.tech = p.tech;
    if (p.imports === 'counted' || p.imports === 'zero') state.imports = p.imports;

  }

  function syncShapeToggle() {
    var st = document.getElementById('shapeToggle');
    var c = cell(state.iso, state.year);
    st.hidden = !((DATA.shape || {})[state.tech]) || !c;
    if (st.hidden) { state.shape = false; return; }
    st.setAttribute('aria-pressed', state.shape ? 'true' : 'false');
    st.textContent = state.shape ? 'Showing ' + techLabel(state.tech) + "'s hours"
                                 : "Show " + techLabel(state.tech) + "'s hours";
  }

  function renderAll() {
    seg('yearSel', YEARS.map(function (y) { return [y, y]; }), state.year, function (v) {
      state.year = parseInt(v, 10); writeHash(); renderAll();
    });
    seg('impSel', [['counted', 'Counted'], ['zero', 'Ignored']], state.imports, function (v) {
      state.imports = v; writeHash(); renderAll();
    });
    seg('techSel', [['wind', 'Wind'], ['solar', 'Solar']], state.tech, function (v) {
      state.tech = v; writeHash(); renderAll();
    });
    renderPicker();
    renderCoverage();
    renderHero();
    renderRange();
    renderCards();
    renderHeat();
    renderDuration();
    renderWaterfall();
    renderIntro();
    Object.keys(tables).forEach(function (k) {
      var el = document.getElementById(k + 'Table');
      if (el) el.hidden = !tables[k];
    });
    syncShapeToggle();
  }

  /** One plain sentence about the selected grid, including its import treatment. */
  function renderIntro() {
    var el = document.getElementById('gridIntro');
    var c = cell(state.iso, state.year);
    var base = 'Pick a grid to see what drives its number: when its emissions actually sit on the ' +
      'margin, and how the cost is built up.';
    if (!c) { el.innerHTML = base; return; }
    var imp = c.system.import_marginal_hour_share, src = c.system.import_source;
    var pct = (imp * 100).toFixed(0);
    el.innerHTML = base + ' ' + (imp >= 0.02
      ? ('In ' + state.iso + ', about <b>' + pct + '% of hours</b> are met at the margin by power ' +
         'brought in from ' + esc(src) + '. ' + (withImports()
           ? 'Those hours are currently charged that region\'s average emission rate of <b>' +
             fmtRate(c.system.import_emission_rate) + '</b> tonnes per MWh.'
           : 'Those hours are currently counted as <b>zero emissions</b>, which flatters the ' +
             'numbers below — switch “Imported power” to <i>Counted</i> above.'))
      : (state.iso + ' imports very little, so the import setting barely moves its numbers.'));
    // Most grids are charged for how much power wind and solar ACTUALLY produce
    // there. A grid with too few recently-built projects to measure that falls
    // back to a nationwide average, and a reader comparing it to the others has
    // to be told — the number is otherwise presented as if it were local.
    var nat = nationalCfTechs(c);
    if (nat.length) {
      el.innerHTML += ' <b>One caution specific to ' + state.iso + ':</b> every other grid is ' +
        'charged for how much power ' +
        (nat.length > 1 ? 'wind and solar actually produce' : techLabel(nat[0]) + ' actually produces') +
        ' there, but ' + state.iso + ' has too few recently-built projects to measure that, so ' +
        (nat.length > 1 ? 'they are' : 'it is') + ' charged a nationwide average instead. ' +
        'Its cost is less tied to its own weather than the others are.';
    }
  }

  /** Techs on this grid-year whose capacity factor fell back to the national figure. */
  function nationalCfTechs(c) {
    return ['wind', 'solar'].filter(function (t) {
      var s = c.scalars[t];
      return s && !s.unavailable && s.cf_source && s.cf_source.indexOf('national') === 0;
    });
  }

  function init() {
    readHash();
    // Default focus: the first grid that actually has data, so the per-grid
    // section is never pointed at a pending grid on load.
    if (!state.iso) state.iso = readySet()[0] || ISOS[0];

    document.getElementById('shapeToggle').addEventListener('click', function () {
      state.shape = !state.shape; renderHeat(); syncShapeToggle();
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
    var rid = null;
    window.addEventListener('resize', function () {
      if (rid) cancelAnimationFrame(rid);
      rid = requestAnimationFrame(function () {
        renderRange(); renderHeat(); renderDuration(); renderWaterfall();
      });
    });

    renderAll();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
