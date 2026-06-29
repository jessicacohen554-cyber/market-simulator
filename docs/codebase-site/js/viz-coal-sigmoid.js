/**
 * viz-coal-sigmoid.js — Interactive coal fuel-cost passthrough sigmoid chart.
 *
 * Displays three logistic sigmoid curves showing the fraction of coal fuel cost
 * included in the offer price as a function of the Henry Hub gas price.
 * The user moves a slider to set the current gas price; a vertical marker updates
 * and dots show each coal type's current passthrough fraction.
 *
 * No data file required — all values computed mathematically.
 *
 * Formula: fuel_frac = 1 / (1 + exp(-k * (gas_price - midpoint)))
 *
 * Coal types:
 *   PRB (coal_prb):         midpoint=3.5, k=0.8
 *   Lignite (coal_lignite): midpoint=3.2, k=0.85
 *   Bituminous (coal_bit):  midpoint=3.4, k=0.8
 *
 * Imports: chart-utils.js (relative to this file's directory).
 */

import {
  responsiveChart,
  margin,
} from './chart-utils.js';

// Coal sigmoid parameter definitions
const COAL_TYPES = [
  {
    key:        'coal_prb',
    label:      'PRB (sub-bituminous)',
    midpoint:   3.5,
    k:          0.8,
    color:      '#374151',
    strokeDash: null,
  },
  {
    key:        'coal_lignite',
    label:      'Lignite (mine-mouth)',
    midpoint:   3.2,
    k:          0.85,
    color:      '#92400E',
    strokeDash: '6,4',
  },
  {
    key:        'coal_bit',
    label:      'Bituminous (spot)',
    midpoint:   3.4,
    k:          0.8,
    color:      '#6B7280',
    strokeDash: '3,3',
  },
];

// Gas price range for x-axis
const GAS_MIN = 2.0;
const GAS_MAX = 8.0;
const N_POINTS = 200;

/**
 * Logistic sigmoid: fuel fraction at a given gas price.
 * @param {number} gasPrice
 * @param {number} midpoint
 * @param {number} k - steepness
 * @returns {number} 0-1 fraction
 */
function sigmoid(gasPrice, midpoint, k) {
  return 1 / (1 + Math.exp(-k * (gasPrice - midpoint)));
}

/**
 * Generate x,y point array for a sigmoid curve.
 * @param {number} midpoint
 * @param {number} k
 * @returns {Array<{x:number, y:number}>}
 */
function sigmoidCurve(midpoint, k) {
  return Array.from({ length: N_POINTS }, (_, i) => {
    const x = GAS_MIN + (i / (N_POINTS - 1)) * (GAS_MAX - GAS_MIN);
    return { x, y: sigmoid(x, midpoint, k) };
  });
}

document.addEventListener('DOMContentLoaded', initCoalSigmoid);

/**
 * Initialize the coal sigmoid chart, wire up the gas price slider.
 */
function initCoalSigmoid() {
  const container = document.getElementById('coal-sigmoid-container');
  if (!container) return;

  const slider = document.getElementById('gas-price-slider');
  const display = document.getElementById('gas-price-display');

  let currentGasPrice = slider ? parseFloat(slider.value) : 3.5;

  // Precompute curves
  const curves = COAL_TYPES.map(ct => ({
    ...ct,
    points: sigmoidCurve(ct.midpoint, ct.k),
  }));

  // Shared mutable references into SVG for updating without full redraw
  let markerLine = null;
  let dotGroups = [];
  let yScale = null;
  let xScale = null;

  /**
   * Update just the gas-price marker and dots — called on every slider input.
   * @param {number} gasPrice
   */
  function updateMarker(gasPrice) {
    if (!markerLine || !xScale || !yScale) return;
    const mx = xScale(gasPrice);

    markerLine
      .attr('x1', mx)
      .attr('x2', mx);

    dotGroups.forEach((dg, i) => {
      const ct = curves[i];
      const frac = sigmoid(gasPrice, ct.midpoint, ct.k);
      dg.dot
        .attr('cx', mx)
        .attr('cy', yScale(frac));
      dg.label
        .attr('x', mx + 8)
        .attr('y', yScale(frac) + 4)
        .text(`${(frac * 100).toFixed(0)}%`);
    });
  }

  /**
   * Full chart draw — called on init and resize.
   * @param {number} width
   * @param {number} height
   */
  function draw(width, height) {
    const m = margin({ top: 32, right: 80, bottom: 52, left: 64 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    d3.select(container).selectAll('svg').remove();
    markerLine = null;
    dotGroups = [];

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('aria-label', 'Coal sigmoid fuel passthrough chart');

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    xScale = d3.scaleLinear()
      .domain([GAS_MIN, GAS_MAX])
      .range([0, w]);

    yScale = d3.scaleLinear()
      .domain([0, 1.05])
      .range([h, 0]);

    // Gridlines
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).ticks(5).tickSize(-w).tickFormat(''))
      .selectAll('line')
      .attr('stroke', 'rgba(255,255,255,0.07)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid .domain').remove();

    // 100% reference line
    g.append('line')
      .attr('x1', 0)
      .attr('x2', w)
      .attr('y1', yScale(1.0))
      .attr('y2', yScale(1.0))
      .attr('stroke', 'rgba(255,255,255,0.20)')
      .attr('stroke-dasharray', '8,4')
      .attr('stroke-width', 1);

    g.append('text')
      .attr('x', w + 4)
      .attr('y', yScale(1.0) + 4)
      .attr('font-size', '10px')
      .attr('fill', 'rgba(255,255,255,0.40)')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('100%');

    // Annotation text
    g.append('text')
      .attr('x', xScale(3.0))
      .attr('y', yScale(0.15))
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'rgba(255,255,255,0.30)')
      .attr('font-family', "'DM Sans', sans-serif")
      .attr('font-style', 'italic')
      .text('coal competitive ↑');

    g.append('text')
      .attr('x', xScale(6.0))
      .attr('y', yScale(0.93))
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'rgba(255,255,255,0.30)')
      .attr('font-family', "'DM Sans', sans-serif")
      .attr('font-style', 'italic')
      .text('gas expensive →');

    // D3 line generator
    const lineGen = d3.line()
      .x(d => xScale(d.x))
      .y(d => yScale(d.y))
      .curve(d3.curveCatmullRom.alpha(0.5));

    // Draw each sigmoid curve
    curves.forEach(ct => {
      g.append('path')
        .datum(ct.points)
        .attr('fill', 'none')
        .attr('d', lineGen)
        .attr('stroke', ct.color)
        .attr('stroke-width', 2.5)
        .attr('stroke-dasharray', ct.strokeDash || null)
        .attr('stroke-linecap', 'round');

      // End label at right edge
      const lastFrac = sigmoid(GAS_MAX, ct.midpoint, ct.k);
      g.append('text')
        .attr('x', w + 4)
        .attr('y', yScale(lastFrac) + 4)
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', ct.color)
        .attr('font-family', "'DM Sans', sans-serif")
        .text(ct.label.split(' ')[0]);
    });

    // Gas price marker line
    const mx = xScale(currentGasPrice);
    markerLine = g.append('line')
      .attr('x1', mx)
      .attr('x2', mx)
      .attr('y1', -8)
      .attr('y2', h)
      .attr('stroke', '#F59E0B')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,3');

    // Marker top label
    g.append('text')
      .attr('id', 'sigmoid-gas-marker-label')
      .attr('x', mx)
      .attr('y', -12)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', '700')
      .attr('fill', '#F59E0B')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('gas price');

    // Dots at intersection of current gas price and each sigmoid
    dotGroups = curves.map(ct => {
      const frac = sigmoid(currentGasPrice, ct.midpoint, ct.k);
      const dot = g.append('circle')
        .attr('cx', mx)
        .attr('cy', yScale(frac))
        .attr('r', 5.5)
        .attr('fill', ct.color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);

      const label = g.append('text')
        .attr('x', mx + 8)
        .attr('y', yScale(frac) + 4)
        .attr('font-size', '10px')
        .attr('font-weight', '700')
        .attr('fill', ct.color)
        .attr('font-family', "'JetBrains Mono', monospace")
        .text(`${(frac * 100).toFixed(0)}%`);

      return { dot, label };
    });

    // Legend
    const legendX = 16;
    const legendY = h - curves.length * 20 - 8;

    const legend = g.append('g').attr('transform', `translate(${legendX},${legendY})`);

    legend.append('rect')
      .attr('x', -8)
      .attr('y', -14)
      .attr('width', 210)
      .attr('height', curves.length * 22 + 14)
      .attr('fill', 'rgba(0,0,0,0.30)')
      .attr('rx', 6);

    curves.forEach((ct, i) => {
      const gy = i * 22;

      legend.append('line')
        .attr('x1', 0)
        .attr('x2', 22)
        .attr('y1', gy + 5)
        .attr('y2', gy + 5)
        .attr('stroke', ct.color)
        .attr('stroke-width', 2.5)
        .attr('stroke-dasharray', ct.strokeDash || null);

      legend.append('text')
        .attr('x', 28)
        .attr('y', gy + 9)
        .attr('font-size', '11px')
        .attr('fill', 'rgba(255,255,255,0.75)')
        .attr('font-family', "'DM Sans', sans-serif")
        .text(ct.label);
    });

    // X-axis
    const xAxis = d3.axisBottom(xScale)
      .ticks(6)
      .tickFormat(d => `$${d.toFixed(1)}`);

    const xAxisG = g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(xAxis);

    xAxisG.select('.domain').remove();
    xAxisG.selectAll('.tick line')
      .attr('stroke', 'rgba(255,255,255,0.12)')
      .attr('stroke-dasharray', '3,3');
    xAxisG.selectAll('.tick text')
      .attr('fill', 'rgba(255,255,255,0.55)')
      .attr('font-size', '11px')
      .attr('font-family', "'DM Sans', sans-serif");

    // X-axis label
    g.append('text')
      .attr('x', w / 2)
      .attr('y', h + 42)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', 'rgba(255,255,255,0.45)')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('Gas Price ($/MMBtu)');

    // Y-axis
    const yAxis = d3.axisLeft(yScale)
      .ticks(5)
      .tickFormat(d => `${Math.round(d * 100)}%`);

    const yAxisG = g.append('g').call(yAxis);
    yAxisG.select('.domain').remove();
    yAxisG.selectAll('.tick line')
      .attr('stroke', 'rgba(255,255,255,0.12)')
      .attr('stroke-dasharray', '3,3');
    yAxisG.selectAll('.tick text')
      .attr('fill', 'rgba(255,255,255,0.55)')
      .attr('font-size', '11px')
      .attr('font-family', "'DM Sans', sans-serif");

    // Y-axis label
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -m.left + 14)
      .attr('x', -h / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', 'rgba(255,255,255,0.45)')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('Coal Fuel Cost Fraction');
  }

  // Mount responsive chart
  responsiveChart('#coal-sigmoid-container', (w, h) => draw(w, h));

  // Wire slider
  if (slider) {
    if (display) display.textContent = parseFloat(slider.value).toFixed(2);

    slider.addEventListener('input', () => {
      currentGasPrice = parseFloat(slider.value);
      if (display) display.textContent = currentGasPrice.toFixed(2);
      updateMarker(currentGasPrice);
    });
  }
}
