/**
 * viz-forecast-bands.js — PB-4 fan-chart renderer for forecast-bands.html.
 *
 * Draws up to five independently-toggleable layers over a single (year, metric)
 * axis pair (dataviz skill: one axis, never dual-scale):
 *   - scenario_envelope : dashed min/max area across the 13 named matrix cases
 *   - parametric fan     : P10-P90 shaded band from the PB-2 sampler
 *   - published fan      : P10-P90 shaded band from PB-2 + PB-3 (parametric_plus_structural)
 *   - P50 path            : the median of the most-authoritative layer present
 *   - case trajectories   : the 13 named cases as thin uniform-color reference
 *     lines (not a 13-way categorical palette -- see the dataviz-skill note in
 *     the module below: >8-12 categorical hues has no CVD-safe assignment, so
 *     identity here comes from the hover tooltip, not color).
 *
 * Every layer this module can draw is gated on the payload actually carrying
 * that data -- a control for an absent layer is never rendered (the chart
 * must never imply data the metadata cannot defend).
 */

import {
  responsiveChart,
  addTooltip,
  makeAxis,
  styleAxis,
  margin,
} from './chart-utils.js';
import { inflateGz } from './bc-data.js';

const LAYER_META = {
  scenario_envelope: { label: 'Scenario envelope (min/max)', swatch: 'area dashed', color: 'var(--text-muted)' },
  parametric: { label: 'Parametric P10–P90', swatch: 'area', color: 'var(--hydro)' },
  parametric_plus_structural: { label: 'Published P10–P90 (+ structural)', swatch: 'area', color: 'var(--nuclear)' },
  p50: { label: 'P50 path', swatch: 'solid', color: 'var(--navy)' },
  cases: { label: '13 named-case trajectories', swatch: 'solid muted', color: 'var(--text-muted)' },
};

const BEST_LAYER_ORDER = ['parametric_plus_structural', 'parametric'];

function loadScript(url) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = url;
    s.onload = resolve;
    s.onerror = () => reject(new Error(`Failed to load ${url}`));
    document.head.appendChild(s);
  });
}

// Unlike the backcast pages, nothing stages a docs/codebase-site/data/forecast/
// copy at preview or deploy time -- the deploy workflow's `cp -r frontend
// _site/` already lands frontend/data/forecast/ under _site/frontend, so this
// mirrors bc-data.js's self-healing probe (primary path first, fall back to
// the repo-relative frontend/ path) rather than requiring a new copy step.
let DATA_ROOT = 'data/forecast';
const DATA_ROOT_FALLBACK = '../../frontend/data/forecast';
let _rootProbed = false;

async function _probeDataRoot() {
  if (_rootProbed) return;
  const resp = await fetch(`${DATA_ROOT}/manifest.json`).catch(() => null);
  if (!resp || !resp.ok) DATA_ROOT = DATA_ROOT_FALLBACK;
  _rootProbed = true;
}

/** Load frontend/data/forecast/manifest.json (self-healing path, see above). */
async function loadManifest() {
  await _probeDataRoot();
  const resp = await fetch(`${DATA_ROOT}/manifest.json`);
  if (!resp.ok) throw new Error(`manifest.json HTTP ${resp.status}`);
  return resp.json();
}

/** Lazy-load + inflate one ensemble's payload by id. */
async function loadEnsemble(id) {
  await _probeDataRoot();
  window.FB = window.FB || {};
  window.FB.bandsGz = window.FB.bandsGz || {};
  if (!window.FB.bandsGz[id]) {
    await loadScript(`${DATA_ROOT}/${id}.js`);
  }
  const gz = window.FB.bandsGz[id];
  if (!gz) throw new Error(`ensemble ${id} not found after loading script`);
  return inflateGz(gz);
}

/** Return the most-authoritative probability layer present, or null. */
function bestLayer(layersPresent) {
  for (const l of BEST_LAYER_ORDER) if (layersPresent.includes(l)) return l;
  return null;
}

/** True when no probability layer (parametric or +structural) is present. */
function isDeterministicOnly(layersPresent) {
  return !layersPresent.some(l => l === 'parametric' || l === 'parametric_plus_structural');
}

/** Build {year: {p10,p50,p90,n,bootstrap_lo,bootstrap_hi}} for one layer+metric. */
function seriesFor(payload, layer, metric) {
  const byYear = (payload.bands[layer] || {})[metric];
  if (!byYear) return null;
  const out = {};
  for (const [year, byQ] of Object.entries(byYear)) {
    out[year] = {
      p10: byQ['0.1']?.value,
      p50: byQ['0.5']?.value,
      p90: byQ['0.9']?.value,
      n: byQ['0.5']?.n ?? byQ['0.1']?.n,
      bootstrap_lo: byQ['0.5']?.bootstrap_lo,
      bootstrap_hi: byQ['0.5']?.bootstrap_hi,
    };
  }
  return out;
}

/** Escape text for safe interpolation into banner HTML. */
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/** Render the label banners (synthetic / dispatch-conditional / deterministic-only). */
function renderBanners(container, payload) {
  const banners = [];
  if (payload.synthetic) {
    banners.push(
      `<div class="fb-banner fb-synthetic"><span class="fb-banner-icon">&#9888;</span>` +
      `<div><strong>SYNTHETIC FIXTURE</strong> &mdash; every number on this page is fabricated ` +
      `for display-shape only. This is not a real forecast run and must never be quoted as one.</div></div>`
    );
  }
  if (payload.dispatch_conditional) {
    banners.push(
      `<div class="fb-banner fb-caveat"><span class="fb-banner-icon">&#9432;</span>` +
      `<div><strong>Dispatch-conditional band</strong> &mdash; excludes fleet-path structural error. ` +
      `The horizon-widening term &lambda;(h) is unmeasured until the PP-0.3 capacity hindcast lands ` +
      `(plan &sect;3.4).</div></div>`
    );
  }
  if (isDeterministicOnly(payload.layers_present)) {
    banners.push(
      `<div class="fb-banner fb-deterministic"><span class="fb-banner-icon">&#9678;</span>` +
      `<div><strong>Deterministic scenario range</strong> &mdash; this payload carries no sampled ` +
      `probability draws, only the named-case scenario matrix. The envelope shown is NOT a ` +
      `probability band.</div></div>`
    );
  }
  // Run-declared HONEST-LIMITATIONS (PB-5 / plan §3.4, §7): rendered verbatim,
  // never softened. Each is a {id, title, detail} the ensemble_meta.json
  // declares; empty for the synthetic fixture. The dispatch-conditional /
  // lambda(h) caveat above already covers limitation (a); these add the axes
  // (datacenter, AEO anchor, small-n, etc.) the standard banners do not.
  (payload.honest_limitations || []).forEach(lim => {
    banners.push(
      `<div class="fb-banner fb-caveat"><span class="fb-banner-icon">&#9432;</span>` +
      `<div><strong>${escapeHtml(lim.title || 'Limitation')}</strong> &mdash; ` +
      `${escapeHtml(lim.detail || '')}</div></div>`
    );
  });
  container.innerHTML = banners.join('');
}

/** Render the layer-toggle chips, gated on data actually present in the payload. */
function renderToggles(container, payload, state, onChange) {
  const chips = [];
  const has = {
    scenario_envelope: !!payload.matrix,
    parametric: payload.layers_present.includes('parametric'),
    parametric_plus_structural: payload.layers_present.includes('parametric_plus_structural'),
    p50: bestLayer(payload.layers_present) !== null,
    cases: !!payload.matrix,
  };

  for (const key of ['scenario_envelope', 'parametric', 'parametric_plus_structural', 'p50', 'cases']) {
    if (!has[key]) continue; // never render a control for absent data
    const meta = LAYER_META[key];
    const on = state.layers[key];
    const swatchCls = meta.swatch.includes('area')
      ? `fb-swatch fb-area${meta.swatch.includes('dashed') ? ' dashed' : ''}`
      : `fb-swatch ${meta.swatch.includes('dashed') ? 'dashed' : 'solid'}`;
    chips.push(`
      <label class="fb-layer-chip ${on ? 'on' : ''}" data-layer="${key}">
        <input type="checkbox" ${on ? 'checked' : ''} data-layer-input="${key}">
        <span class="${swatchCls}" style="border-color:${meta.color};background:${meta.swatch.includes('area') ? meta.color : 'transparent'}"></span>
        ${meta.label}
      </label>
    `);
  }
  container.innerHTML = chips.join('');
  container.querySelectorAll('input[data-layer-input]').forEach(input => {
    input.addEventListener('change', () => {
      const key = input.dataset.layerInput;
      state.layers[key] = input.checked;
      input.closest('.fb-layer-chip').classList.toggle('on', input.checked);
      onChange();
    });
  });
}

/** Render the P10/P50/P90-by-year (or min/max) HTML table view. */
function renderTable(container, payload, metric) {
  const layer = bestLayer(payload.layers_present);
  if (layer) {
    const series = seriesFor(payload, layer, metric);
    const years = Object.keys(series).sort((a, b) => +a - +b);
    let html = '<div class="bc-table-wrap"><table><thead><tr><th>Year</th><th>P10</th><th>P50</th><th>P90</th></tr></thead><tbody>';
    for (const y of years) {
      const r = series[y];
      const fmt = v => (v == null ? '—' : v.toFixed(2));
      html += `<tr><td>${y}</td><td class="num">${fmt(r.p10)}</td><td class="num">${fmt(r.p50)}</td><td class="num">${fmt(r.p90)}</td></tr>`;
    }
    html += '</tbody></table></div>';
    container.innerHTML = html;
    return;
  }
  const envelope = payload.matrix?.envelope;
  if (!envelope) {
    container.innerHTML = '<p class="bc-mute">No data for this metric.</p>';
    return;
  }
  const years = Object.keys(envelope).sort((a, b) => +a - +b);
  let html = '<div class="bc-table-wrap"><table><thead><tr><th>Year</th><th>Min</th><th>Min case</th><th>Max</th><th>Max case</th></tr></thead><tbody>';
  for (const y of years) {
    const r = envelope[y];
    html += `<tr><td>${y}</td><td class="num">${r.min.toFixed(2)}</td><td>${r.min_case}</td><td class="num">${r.max.toFixed(2)}</td><td>${r.max_case}</td></tr>`;
  }
  html += '</tbody></table></div>';
  container.innerHTML = html;
}

/**
 * Initialize the fan chart in `container` for the given payload/metric, wired
 * to the toggle chips in `toggleContainer`. Returns a redraw() you can call
 * after external state changes (e.g. metric switch).
 */
function initChart(container, toggleContainer, payload, initialMetric) {
  const state = {
    metric: initialMetric,
    layers: {
      scenario_envelope: true,
      parametric: true,
      parametric_plus_structural: true,
      p50: true,
      cases: false, // reference lines default off to avoid clutter
    },
  };

  const tooltip = addTooltip('fb-tooltip');

  function draw(width, height) {
    const m = margin({ top: 20, right: 24, bottom: 40, left: 60 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;
    // Container is hidden (e.g. the Table view toggled the chart panel to
    // display:none) -- the ResizeObserver still fires on that 0x0 collapse,
    // so skip drawing rather than feed a negative size to an SVG <rect>.
    if (w <= 0 || h <= 0) return;
    d3.select(container).selectAll('svg').remove();

    const layer = bestLayer(payload.layers_present);
    const series = layer ? seriesFor(payload, layer, state.metric) : null;
    const parametricSeries = payload.layers_present.includes('parametric')
      ? seriesFor(payload, 'parametric', state.metric)
      : null;
    const structuralSeries = payload.layers_present.includes('parametric_plus_structural')
      ? seriesFor(payload, 'parametric_plus_structural', state.metric)
      : null;
    const envelope = payload.matrix?.envelope;
    const trajectories = payload.matrix?.trajectories;

    const allYears = new Set();
    if (series) Object.keys(series).forEach(y => allYears.add(+y));
    if (envelope) Object.keys(envelope).forEach(y => allYears.add(+y));
    const years = Array.from(allYears).sort((a, b) => a - b);

    if (!years.length) {
      container.innerHTML = '<p class="bc-mute" style="padding:2rem;text-align:center;">No data to display for this metric.</p>';
      return;
    }

    const svg = d3.select(container).append('svg')
      .attr('width', width).attr('height', height)
      .attr('class', 'chart')
      .attr('role', 'img')
      .attr('aria-label', `Forecast band fan chart for ${state.metric}, ${years[0]}–${years[years.length - 1]}`);
    const g = svg.append('g').attr('transform', `translate(${m.left},${m.top})`);

    const xScale = d3.scaleLinear().domain(d3.extent(years)).range([0, w]);

    let yMin = Infinity, yMax = -Infinity;
    const consider = v => { if (v != null) { yMin = Math.min(yMin, v); yMax = Math.max(yMax, v); } };
    if (state.layers.scenario_envelope && envelope) {
      Object.values(envelope).forEach(r => { consider(r.min); consider(r.max); });
    }
    if (state.layers.parametric && parametricSeries) {
      Object.values(parametricSeries).forEach(r => { consider(r.p10); consider(r.p90); });
    }
    if (state.layers.parametric_plus_structural && structuralSeries) {
      Object.values(structuralSeries).forEach(r => { consider(r.p10); consider(r.p90); });
    }
    if (state.layers.cases && trajectories) {
      Object.values(trajectories).forEach(byYear => Object.values(byYear).forEach(consider));
    }
    if (!isFinite(yMin)) { yMin = 0; yMax = 1; }
    const pad = (yMax - yMin) * 0.08 || 1;
    const yScale = d3.scaleLinear().domain([Math.max(0, yMin - pad), yMax + pad]).range([h, 0]);

    g.append('g').attr('class', 'grid')
      .call(d3.axisLeft(yScale).tickSize(-w).tickFormat('').ticks(6))
      .selectAll('line').attr('stroke', 'rgba(0,0,0,0.06)').attr('stroke-dasharray', '3,3');
    g.select('.grid .domain').remove();

    const cssColor = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

    // Layer 1: scenario envelope (dashed area + boundary lines)
    if (state.layers.scenario_envelope && envelope) {
      const envYears = Object.keys(envelope).map(Number).sort((a, b) => a - b);
      const area = d3.area()
        .x(y => xScale(y))
        .y0(y => yScale(envelope[y].min))
        .y1(y => yScale(envelope[y].max))
        .curve(d3.curveMonotoneX);
      g.append('path').datum(envYears).attr('d', area)
        .attr('fill', cssColor('--text-muted')).attr('fill-opacity', 0.08);
      const lineMin = d3.line().x(y => xScale(y)).y(y => yScale(envelope[y].min)).curve(d3.curveMonotoneX);
      const lineMax = d3.line().x(y => xScale(y)).y(y => yScale(envelope[y].max)).curve(d3.curveMonotoneX);
      [lineMin, lineMax].forEach(lineFn => {
        g.append('path').datum(envYears).attr('d', lineFn)
          .attr('fill', 'none').attr('stroke', cssColor('--text-muted'))
          .attr('stroke-width', 1.5).attr('stroke-dasharray', '5,3');
      });
    }

    // Layer 5 (drawn early, under the fans): 13 named-case reference lines
    if (state.layers.cases && trajectories) {
      for (const [caseName, byYear] of Object.entries(trajectories)) {
        const caseYears = Object.keys(byYear).map(Number).sort((a, b) => a - b);
        const lineFn = d3.line().x(y => xScale(y)).y(y => yScale(byYear[y])).curve(d3.curveMonotoneX);
        g.append('path').datum(caseYears).attr('d', lineFn)
          .attr('class', 'fb-case-line')
          .on('mouseenter', function () { d3.select(this).classed('fb-hover', true); })
          .on('mouseleave', function () { d3.select(this).classed('fb-hover', false); })
          .on('mousemove', event => {
            tooltip.show(`<strong>${caseName}</strong>`, event);
          })
          .on('mouseleave.tip', () => tooltip.hide());
      }
    }

    // Layer 2: parametric fan
    if (state.layers.parametric && parametricSeries) {
      const pYears = Object.keys(parametricSeries).map(Number).sort((a, b) => a - b);
      const area = d3.area()
        .x(y => xScale(y))
        .y0(y => yScale(parametricSeries[y].p10))
        .y1(y => yScale(parametricSeries[y].p90))
        .curve(d3.curveMonotoneX);
      g.append('path').datum(pYears).attr('d', area)
        .attr('fill', cssColor('--hydro')).attr('fill-opacity', 0.18);
    }

    // Layer 3: published (+structural) fan -- drawn on top, more authoritative
    if (state.layers.parametric_plus_structural && structuralSeries) {
      const sYears = Object.keys(structuralSeries).map(Number).sort((a, b) => a - b);
      const area = d3.area()
        .x(y => xScale(y))
        .y0(y => yScale(structuralSeries[y].p10))
        .y1(y => yScale(structuralSeries[y].p90))
        .curve(d3.curveMonotoneX);
      g.append('path').datum(sYears).attr('d', area)
        .attr('fill', cssColor('--nuclear')).attr('fill-opacity', 0.22)
        .attr('stroke', cssColor('--nuclear')).attr('stroke-width', 1).attr('stroke-opacity', 0.5);
    }

    // Layer 4: P50 path (from the best available probability layer)
    if (state.layers.p50 && series) {
      const p50Years = Object.keys(series).map(Number).sort((a, b) => a - b);
      const lineFn = d3.line().x(y => xScale(y)).y(y => yScale(series[y].p50)).curve(d3.curveMonotoneX);
      g.append('path').datum(p50Years).attr('d', lineFn)
        .attr('fill', 'none').attr('stroke', cssColor('--navy')).attr('stroke-width', 2);
    }

    // Axes
    const xAxis = makeAxis('x', xScale, { ticks: width < 500 ? 5 : 10, tickFormat: d3.format('d') });
    const xG = g.append('g').attr('transform', `translate(0,${h})`).call(xAxis);
    styleAxis(xG);
    const yAxis = makeAxis('y', yScale, { ticks: 6, tickFormat: d3.format(',.0f') });
    const yG = g.append('g').call(yAxis);
    styleAxis(yG);

    // Hover crosshair aggregating year-keyed series
    const bisect = d3.bisector(d => d).left;
    const hoverLine = g.append('line')
      .attr('stroke', 'rgba(0,0,0,0.2)').attr('stroke-width', 1).attr('stroke-dasharray', '4,3')
      .attr('y1', 0).attr('y2', h).style('display', 'none');
    const overlay = g.append('rect').attr('width', w).attr('height', h)
      .attr('fill', 'none').attr('pointer-events', 'all');

    overlay.on('mousemove', event => {
      const [mx] = d3.pointer(event, overlay.node());
      const yearVal = xScale.invert(mx);
      const idx = bisect(years, yearVal);
      const year = years[Math.min(Math.max(idx, 0), years.length - 1)];
      hoverLine.attr('x1', xScale(year)).attr('x2', xScale(year)).style('display', null);

      let html = `<strong>${year}</strong><br>`;
      if (state.layers.scenario_envelope && envelope?.[year]) {
        html += `Envelope: ${envelope[year].min.toFixed(1)}–${envelope[year].max.toFixed(1)}<br>`;
      }
      if (state.layers.parametric && parametricSeries?.[year]) {
        const r = parametricSeries[year];
        html += `Parametric P10/P50/P90: ${r.p10.toFixed(1)} / ${r.p50.toFixed(1)} / ${r.p90.toFixed(1)}<br>`;
      }
      if (state.layers.parametric_plus_structural && structuralSeries?.[year]) {
        const r = structuralSeries[year];
        html += `Published P10/P50/P90: ${r.p10.toFixed(1)} / ${r.p50.toFixed(1)} / ${r.p90.toFixed(1)}<br>`;
      }
      tooltip.show(html, event);
    }).on('mouseleave', () => { hoverLine.style('display', 'none'); tooltip.hide(); });
  }

  renderToggles(toggleContainer, payload, state, () => {
    const w = container.clientWidth;
    const h = container.clientHeight || Math.round(w * 0.5);
    draw(w, h);
  });

  const resize = responsiveChart(container, (w, h) => draw(w, h));
  return {
    setMetric(metric) {
      state.metric = metric;
      const w = container.clientWidth;
      const h = container.clientHeight || Math.round(w * 0.5);
      draw(w, h);
    },
    destroy() { resize.disconnect(); },
  };
}

export { loadManifest, loadEnsemble, initChart, renderBanners, renderTable, bestLayer, isDeterministicOnly };
