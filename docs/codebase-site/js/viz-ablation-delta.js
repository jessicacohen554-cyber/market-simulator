/**
 * viz-ablation-delta.js — keeper vs zero-forcing ablation-twin per-class delta
 * Used on: results-calibration.html (§Ablation Twins & the DOF Ledger)
 *
 * Diverging horizontal bars of delta_twh = keeper - ablation for each class:
 *   delta > 0  the energy the class's merchant floors BUY (forcing color)
 *   delta < 0  the flexible margin (gas-CC) ABSORBING the reallocated energy
 *   delta ~ 0  structural must-run kept in the twin (no floor effect)
 *
 * Reads data/ablation-delta.json (illustrative). Matches the site viz idiom:
 * ES module, responsiveChart wrapper, dark-section aware, chart-utils tooltip.
 */

import {
  responsiveChart,
  addTooltip,
  makeAxis,
  styleAxis,
  styleAxisDark,
  margin,
} from './chart-utils.js';

document.addEventListener('DOMContentLoaded', initAblationDelta);

// Nicer display labels for the D-2 class ids.
const CLASS_LABELS = {
  NUCLEAR: 'Nuclear',
  GAS_CC: 'Gas-CC',
  COAL: 'Coal',
  ST_GAS: 'Steam gas',
  CT_PEAKER: 'CT peaker',
  OIL_GT: 'Oil GT',
};

// Semantic diverging palette around a meaningful zero.
const COLOR_BUYS    = '#E67E22'; // delta > 0 — floors buy this class's energy
const COLOR_ABSORBS = '#0EA5E9'; // delta < 0 — flexible margin absorbs it
const COLOR_STRUCT  = '#94A3B8'; // |delta| ~ 0 — structural must-run, no floor
const STRUCT_EPS = 0.5;          // TWh: below this a delta reads as structural

function classLabel(cls) {
  return CLASS_LABELS[cls] || cls;
}

function fmtTwh(v) {
  const sign = v > 0 ? '+' : (v < 0 ? '−' : '');
  return `${sign}${Math.abs(v).toFixed(1)} TWh`;
}

function barColor(delta) {
  if (Math.abs(delta) < STRUCT_EPS) return COLOR_STRUCT;
  return delta > 0 ? COLOR_BUYS : COLOR_ABSORBS;
}

async function initAblationDelta() {
  const container = document.getElementById('ablation-delta-container');
  if (!container) return;

  let data;
  try {
    const res = await fetch('data/ablation-delta.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.error('Failed to load ablation-delta data:', err);
    container.innerHTML = '<div style="padding:2rem;text-align:center;color:#666;">Unable to load data.</div>';
    return;
  }

  const tooltip = addTooltip('ablation-delta-tooltip');
  // Largest |delta| first so the visual reads top-to-bottom by magnitude.
  const classes = data.classes.slice().sort((a, b) => Math.abs(b.delta_twh) - Math.abs(a.delta_twh));

  function draw(width, height) {
    d3.select(container).selectAll('svg').remove();

    const isDark = container.closest('.section-dark') !== null;
    const m = margin({ top: 16, right: 72, bottom: 44, left: 92 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('role', 'img')
      .attr('aria-label', 'Per-class energy delta between the keeper and its zero-forcing ablation twin');

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    // Scales — x diverges around zero.
    const maxAbs = d3.max(classes, d => Math.abs(d.delta_twh)) || 1;
    const xScale = d3.scaleLinear()
      .domain([-maxAbs * 1.15, maxAbs * 1.15])
      .range([0, w]);

    const yScale = d3.scaleBand()
      .domain(classes.map(d => d.class))
      .range([0, h])
      .padding(0.32);

    // Vertical grid
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisBottom(xScale).tickSize(h).tickFormat('').ticks(6))
      .attr('transform', 'translate(0,0)')
      .selectAll('line')
      .attr('stroke', isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.05)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid .domain').remove();

    const x0 = xScale(0);

    // Bars
    g.selectAll('.abl-bar')
      .data(classes)
      .join('rect')
      .attr('class', 'abl-bar')
      .attr('x', d => Math.min(x0, xScale(d.delta_twh)))
      .attr('y', d => yScale(d.class))
      .attr('width', d => Math.abs(xScale(d.delta_twh) - x0))
      .attr('height', yScale.bandwidth())
      .attr('rx', 3)
      .attr('fill', d => barColor(d.delta_twh))
      .attr('fill-opacity', 0.85)
      .style('cursor', 'pointer')
      .on('mouseenter', (event, d) => {
        const dir = Math.abs(d.delta_twh) < STRUCT_EPS
          ? 'structural must-run (kept in the twin)'
          : (d.delta_twh > 0 ? 'energy the floors buy' : 'absorbed by the flexible margin');
        tooltip.show(
          `<strong>${classLabel(d.class)}</strong><br><br>` +
          `Keeper: ${d.keeper_twh.toFixed(1)} TWh<br>` +
          `Twin (floors off): ${d.ablation_twh.toFixed(1)} TWh<br>` +
          `<strong>Delta: ${fmtTwh(d.delta_twh)}</strong> &mdash; ${dir}` +
          (d.note ? `<br><br><span style="opacity:0.75">${d.note}</span>` : ''),
          event
        );
      })
      .on('mouseleave', () => tooltip.hide());

    // Value labels at the outer end of each bar
    g.selectAll('.abl-val')
      .data(classes)
      .join('text')
      .attr('class', 'abl-val')
      .attr('x', d => d.delta_twh >= 0 ? xScale(d.delta_twh) + 6 : xScale(d.delta_twh) - 6)
      .attr('y', d => yScale(d.class) + yScale.bandwidth() / 2 + 4)
      .attr('text-anchor', d => d.delta_twh >= 0 ? 'start' : 'end')
      .attr('font-size', '11px')
      .attr('font-weight', '700')
      .attr('font-family', "'DM Sans', sans-serif")
      .attr('fill', d => barColor(d.delta_twh))
      .text(d => fmtTwh(d.delta_twh));

    // Zero line (emphasized)
    g.append('line')
      .attr('x1', x0)
      .attr('x2', x0)
      .attr('y1', 0)
      .attr('y2', h)
      .attr('stroke', isDark ? 'rgba(255,255,255,0.5)' : 'rgba(10,18,38,0.45)')
      .attr('stroke-width', 1.5);

    // Class labels (left, as y ticks)
    const yAxis = d3.axisLeft(yScale).tickSize(0).tickFormat(classLabel);
    const yG = g.append('g').call(yAxis);
    isDark ? styleAxisDark(yG) : styleAxis(yG);
    yG.select('.domain').remove();
    yG.selectAll('text').attr('font-size', '12px').attr('font-weight', '600');

    // X axis
    const xAxis = makeAxis('x', xScale, {
      ticks: width < 480 ? 4 : 7,
      tickFormat: v => (v > 0 ? `+${v}` : `${v}`),
    });
    const xG = g.append('g').attr('transform', `translate(0,${h})`).call(xAxis);
    isDark ? styleAxisDark(xG) : styleAxis(xG);

    // X label
    g.append('text')
      .attr('x', w / 2)
      .attr('y', h + 38)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', isDark ? 'rgba(241,245,249,0.55)' : '#566370')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('keeper − twin energy (TWh)  —  ← absorbed by flexible margin  ·  bought by floors →');
  }

  responsiveChart(container, (w, h) => draw(w, h));
}

export { initAblationDelta };
