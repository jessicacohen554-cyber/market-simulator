/**
 * viz-offer-curve.js — Tranche offer curve stepped line chart for Fleet & Offer Curves page.
 *
 * Shows a single representative plant's offer curve as a step function from minimum-load
 * committed tranche through economic ramp steps to peaking/duct-firing. The user selects
 * a fuel type via the #offer-fuel-select dropdown; the chart redraws with computed tranches.
 *
 * All marginal costs are computed inline from reference heat rates and a fixed gas price of
 * $3.50/MMBtu. Each tranche's MW range and cost is displayed as a step path with colored
 * background regions and inline labels.
 *
 * Data source: data/offer-curve-tranches.json (relative to HTML page, not this JS file).
 * Imports: chart-utils.js (relative to this file's directory).
 */

import {
  responsiveChart,
  addTooltip,
  formatMW,
  margin,
} from './chart-utils.js';

// Reference constants
const GAS_PRICE = 3.50;      // $/MMBtu — reference gas price shown in UI
const PLANT_CAPACITY = 1000; // MW — representative plant size

// Coal fuel cost per MMBtu (delivered PRB coal, approximate)
const COAL_PRB_PRICE = 1.50; // $/MMBtu

// Tranche region fill colors (very light, for background tinting)
const TRANCHE_COLORS = {
  committed:   'rgba(14,165,233,0.08)',
  economic:    'rgba(34,197,94,0.06)',
  peaking:     'rgba(245,158,11,0.10)',
  must_run:    'rgba(99,102,241,0.08)',
};

// Tranche label colors
const TRANCHE_LABEL_COLORS = {
  committed:   '#0369A1',
  economic:    '#15803D',
  peaking:     '#B45309',
  must_run:    '#4338CA',
};

/**
 * Compute the step-function tranche points for a given fuel.
 * Returns an array of segment objects: { label, mwStart, mwEnd, mc, colorKey }
 *
 * @param {string} fuel - 'gas_cc' | 'gas_ct' | 'coal_prb'
 * @returns {Array<{label:string, mwStart:number, mwEnd:number, mc:number, colorKey:string}>}
 */
function computeTranches(fuel) {
  const C = PLANT_CAPACITY;
  const g = GAS_PRICE;

  if (fuel === 'gas_cc') {
    const HR = 6.5;
    const VOM = 2.0;

    const committedMW = C * 0.48;
    const committedMC = HR * 0.92 * g + VOM;

    const econMW = C * 0.35;
    const stepsN = 6;
    const stepMW = econMW / stepsN;
    const hrLow = 1.06;
    const hrHigh = 1.35;

    const econSteps = Array.from({ length: stepsN }, (_, i) => {
      const frac = stepsN === 1 ? 0 : i / (stepsN - 1);
      const hrMult = hrLow + frac * (hrHigh - hrLow);
      const mc = HR * hrMult * g + VOM;
      const mwStart = committedMW + i * stepMW;
      const mwEnd = mwStart + stepMW;
      return { label: `Econ Ramp ${i + 1}`, mwStart, mwEnd, mc, colorKey: 'economic' };
    });

    const peakMW = C * 0.17;
    const peakMC = HR * 2.25 * g + VOM;
    const peakStart = committedMW + econMW;

    return [
      { label: 'Committed\n(Min Load)', mwStart: 0, mwEnd: committedMW, mc: committedMC, colorKey: 'committed' },
      ...econSteps,
      { label: 'Peaking\n(Duct Fire)', mwStart: peakStart, mwEnd: peakStart + peakMW, mc: peakMC, colorKey: 'peaking' },
    ];
  }

  if (fuel === 'gas_ct') {
    const HR = 10.5;
    const VOM = 3.5;

    const committedMW = C * 0.35;
    const committedMC = HR * 0.95 * g + VOM;

    const econMW = C * 0.40;
    const stepsN = 4;
    const stepMW = econMW / stepsN;
    const hrLow = 1.02;
    const hrHigh = 1.25;

    const econSteps = Array.from({ length: stepsN }, (_, i) => {
      const frac = stepsN === 1 ? 0 : i / (stepsN - 1);
      const hrMult = hrLow + frac * (hrHigh - hrLow);
      const mc = HR * hrMult * g + VOM;
      const mwStart = committedMW + i * stepMW;
      const mwEnd = mwStart + stepMW;
      return { label: `Econ Ramp ${i + 1}`, mwStart, mwEnd, mc, colorKey: 'economic' };
    });

    const peakMW = C * 0.25;
    const peakMC = HR * 1.45 * g + VOM;
    const peakStart = committedMW + econMW;

    return [
      { label: 'Committed', mwStart: 0, mwEnd: committedMW, mc: committedMC, colorKey: 'committed' },
      ...econSteps,
      { label: 'Peaking', mwStart: peakStart, mwEnd: peakStart + peakMW, mc: peakMC, colorKey: 'peaking' },
    ];
  }

  if (fuel === 'coal_prb') {
    const HR = 10.0;
    const VOM = 4.5;
    const coalFuel = HR * COAL_PRB_PRICE;

    const mustMW = C * 0.30;
    const mustMC = VOM;

    const committedMW = C * 0.25;
    const committedMC = VOM + 0.35 * coalFuel;

    const econMW = C * 0.45;
    const econMC = VOM + coalFuel;

    return [
      { label: 'Must-Run\n(Take-or-Pay)', mwStart: 0, mwEnd: mustMW, mc: mustMC, colorKey: 'must_run' },
      { label: 'Committed\n(35% passthru)', mwStart: mustMW, mwEnd: mustMW + committedMW, mc: committedMC, colorKey: 'committed' },
      { label: 'Economic\n(Full cost)', mwStart: mustMW + committedMW, mwEnd: C, mc: econMC, colorKey: 'economic' },
    ];
  }

  return [];
}

/**
 * Build the SVG step path from a tranches array.
 * Returns D attribute string for a horizontal step function.
 *
 * @param {Array} tranches
 * @param {Function} xScale
 * @param {Function} yScale
 * @returns {string} SVG path d attribute
 */
function buildStepPath(tranches, xScale, yScale) {
  if (!tranches.length) return '';
  let d = '';
  tranches.forEach((t, i) => {
    const x0 = xScale(t.mwStart);
    const x1 = xScale(t.mwEnd);
    const y  = yScale(t.mc);

    if (i === 0) {
      d += `M ${x0} ${y}`;
    } else {
      d += ` V ${y}`;
    }
    d += ` H ${x1}`;
  });
  return d;
}

document.addEventListener('DOMContentLoaded', initOfferCurve);

/**
 * Initialize the offer curve chart: set up chart, wire dropdown.
 */
async function initOfferCurve() {
  const container = document.getElementById('offer-curve-container');
  if (!container) return;

  let activeFuel = 'gas_cc';

  const tooltip = addTooltip('offer-tooltip');

  /**
   * Draw the offer curve chart for the given fuel.
   * @param {number} width
   * @param {number} height
   */
  function draw(width, height) {
    const tranches = computeTranches(activeFuel);
    if (!tranches.length) return;

    const m = margin({ top: 28, right: 28, bottom: 52, left: 64 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    d3.select(container).selectAll('svg').remove();

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('aria-label', 'Tranche offer curve chart');

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    const xScale = d3.scaleLinear()
      .domain([0, PLANT_CAPACITY])
      .range([0, w]);

    const mcValues = tranches.map(t => t.mc);
    const yMax = d3.max(mcValues) * 1.18;
    const yMin = Math.max(0, d3.min(mcValues) * 0.85);

    const yScale = d3.scaleLinear()
      .domain([yMin, yMax])
      .range([h, 0]);

    // Gridlines
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).ticks(5).tickSize(-w).tickFormat(''))
      .selectAll('line')
      .attr('stroke', 'rgba(0,0,0,0.06)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid .domain').remove();

    // Tranche background regions
    tranches.forEach(t => {
      const x0 = xScale(t.mwStart);
      const x1 = xScale(t.mwEnd);
      const regionW = x1 - x0;

      g.append('rect')
        .attr('x', x0)
        .attr('y', 0)
        .attr('width', Math.max(0, regionW))
        .attr('height', h)
        .attr('fill', TRANCHE_COLORS[t.colorKey] || 'rgba(0,0,0,0.03)');
    });

    // Vertical separator lines between tranches
    const boundaries = new Set();
    tranches.forEach(t => { boundaries.add(t.mwStart); boundaries.add(t.mwEnd); });
    boundaries.delete(0);
    boundaries.delete(PLANT_CAPACITY);
    boundaries.forEach(mw => {
      g.append('line')
        .attr('x1', xScale(mw))
        .attr('x2', xScale(mw))
        .attr('y1', 0)
        .attr('y2', h)
        .attr('stroke', 'rgba(0,0,0,0.12)')
        .attr('stroke-dasharray', '4,3')
        .attr('stroke-width', 1);
    });

    // Step path (the offer curve line)
    const pathD = buildStepPath(tranches, xScale, yScale);
    g.append('path')
      .attr('d', pathD)
      .attr('fill', 'none')
      .attr('stroke', '#1A2744')
      .attr('stroke-width', 2.5)
      .attr('stroke-linecap', 'round')
      .attr('stroke-linejoin', 'round');

    // Dots at step transitions
    tranches.forEach((t, i) => {
      g.append('circle')
        .attr('cx', xScale(t.mwStart))
        .attr('cy', yScale(t.mc))
        .attr('r', 4)
        .attr('fill', '#1A2744')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5);

      if (i === tranches.length - 1) {
        g.append('circle')
          .attr('cx', xScale(t.mwEnd))
          .attr('cy', yScale(t.mc))
          .attr('r', 4)
          .attr('fill', '#1A2744')
          .attr('stroke', '#fff')
          .attr('stroke-width', 1.5);
      }
    });

    // Tranche region labels
    tranches.forEach(t => {
      const midX = xScale((t.mwStart + t.mwEnd) / 2);
      const regionW = xScale(t.mwEnd) - xScale(t.mwStart);

      if (regionW < 36) return;

      const labelColor = TRANCHE_LABEL_COLORS[t.colorKey] || '#566370';
      const lines = t.label.split('\n');

      const labelG = g.append('g')
        .attr('transform', `translate(${midX}, 14)`);

      lines.forEach((line, li) => {
        labelG.append('text')
          .attr('x', 0)
          .attr('y', li * 13)
          .attr('text-anchor', 'middle')
          .attr('font-size', regionW > 80 ? '10px' : '9px')
          .attr('font-weight', '700')
          .attr('font-family', "'DM Sans', sans-serif")
          .attr('fill', labelColor)
          .text(line);
      });
    });

    // MC value labels at each step level
    tranches.forEach((t, i) => {
      if (i > 0 && Math.abs(t.mc - tranches[i - 1].mc) < 1.5) return;
      const x1 = xScale(t.mwEnd);
      if (x1 > w - 8) return;

      g.append('text')
        .attr('x', x1 - 4)
        .attr('y', yScale(t.mc) - 6)
        .attr('text-anchor', 'end')
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('font-family', "'JetBrains Mono', monospace")
        .attr('fill', '#1A2744')
        .text(`$${t.mc.toFixed(1)}`);
    });

    // Hover overlay for tooltips
    const hoverG = g.append('g').style('pointer-events', 'all');
    tranches.forEach(t => {
      const x0 = xScale(t.mwStart);
      const x1 = xScale(t.mwEnd);
      hoverG.append('rect')
        .attr('x', x0)
        .attr('y', 0)
        .attr('width', Math.max(1, x1 - x0))
        .attr('height', h)
        .attr('fill', 'transparent')
        .on('mouseenter', (event) => {
          const html = `
            <div class="tooltip__title">${t.label.replace('\n', ' ')}</div>
            <div class="tooltip__row">
              <span class="tooltip__key">MW range</span>
              <span class="tooltip__val">${t.mwStart}–${t.mwEnd} MW</span>
            </div>
            <div class="tooltip__row">
              <span class="tooltip__key">Marginal cost</span>
              <span class="tooltip__val">$${t.mc.toFixed(2)}/MWh</span>
            </div>
            <div class="tooltip__row">
              <span class="tooltip__key">% of plant</span>
              <span class="tooltip__val">${Math.round((t.mwEnd - t.mwStart) / PLANT_CAPACITY * 100)}%</span>
            </div>`;
          tooltip.show(html, event);
        })
        .on('mouseleave', () => tooltip.hide());
    });

    // X-axis
    const xAxis = d3.axisBottom(xScale)
      .ticks(5)
      .tickFormat(d => `${d} MW`);

    const xAxisG = g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(xAxis);

    xAxisG.select('.domain').remove();
    xAxisG.selectAll('.tick line')
      .attr('stroke', 'rgba(0,0,0,0.12)')
      .attr('stroke-dasharray', '3,3');
    xAxisG.selectAll('.tick text')
      .attr('fill', '#566370')
      .attr('font-size', '11px')
      .attr('font-family', "'DM Sans', sans-serif");

    // X-axis label
    g.append('text')
      .attr('x', w / 2)
      .attr('y', h + 42)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', '#566370')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('Plant Capacity (MW)');

    // Y-axis
    const yAxis = d3.axisLeft(yScale)
      .ticks(5)
      .tickFormat(d => `$${d.toFixed(0)}`);

    const yAxisG = g.append('g').call(yAxis);
    yAxisG.select('.domain').remove();
    yAxisG.selectAll('.tick line')
      .attr('stroke', 'rgba(0,0,0,0.12)')
      .attr('stroke-dasharray', '3,3');
    yAxisG.selectAll('.tick text')
      .attr('fill', '#566370')
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
      .attr('fill', '#566370')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('Offer Price ($/MWh)');
  }

  // Mount responsive chart
  const observer = responsiveChart('#offer-curve-container', (w, h) => draw(w, h));

  // Wire dropdown
  const select = document.getElementById('offer-fuel-select');
  if (select) {
    select.addEventListener('change', () => {
      activeFuel = select.value;
      const w = container.clientWidth;
      const h = container.clientHeight || Math.round(w * 0.5);
      draw(w, h);
    });
  }
}
