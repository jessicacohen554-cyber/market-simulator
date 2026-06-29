/**
 * viz-merit-order.js — Merit order supply stack chart for Fleet & Offer Curves page.
 *
 * Renders an interactive supply stack (merit order) bar chart using D3 v7.
 * Each generator is a horizontal rect sorted by marginal cost (cheapest left).
 * A vertical dashed demand line at 55 GW separates dispatching from idle capacity.
 * Fuel filter buttons control opacity; the chart is drawn once via responsiveChart
 * and filter state is applied by updating bar opacity only (no full redraw on filter).
 *
 * Data source: data/fleet-merit-order.json (relative to HTML page, not this file).
 * Imports: chart-utils.js (relative to this file's directory).
 */

import {
  responsiveChart,
  fuelColorScale,
  addTooltip,
  formatMW,
  formatPrice,
  styleAxis,
  margin,
} from './chart-utils.js';

// Demand line position in MW
const DEMAND_MW = 55000;

// Minimum display height for zero-MC generators (wind, solar, storage, hydro at $0)
const ZERO_MC_DISPLAY = 1.5;

// Fuel groups: map fuel_type values to canonical group keys used in filter buttons
const FUEL_GROUP = {
  nuclear:      'nuclear',
  coal_prb:     'coal',
  coal_lignite: 'coal',
  coal_bit:     'coal',
  gas_cc:       'gas_cc',
  gas_ct:       'gas_ct',
  wind:         'wind',
  solar:        'solar',
  hydro:        'hydro',
  storage:      'storage',
};

// Map fuel_type to the fuelColorScale canonical key
const FUEL_COLOR_KEY = {
  nuclear:      'nuclear',
  coal_prb:     'fossil-coal',
  coal_lignite: 'fossil-coal',
  coal_bit:     'fossil-coal',
  gas_cc:       'fossil-gas',
  gas_ct:       'fossil-gas',
  wind:         'wind',
  solar:        'solar',
  hydro:        'hydro',
  storage:      'storage',
};

// Human-readable fuel labels for tooltip
const FUEL_LABEL = {
  nuclear:      'Nuclear',
  coal_prb:     'Coal PRB',
  coal_lignite: 'Coal Lignite',
  coal_bit:     'Coal Bituminous',
  gas_cc:       'Gas CC',
  gas_ct:       'Gas CT',
  wind:         'Wind',
  solar:        'Solar',
  hydro:        'Hydro',
  storage:      'Storage',
};

document.addEventListener('DOMContentLoaded', initMeritOrder);

/**
 * Initialize the merit order chart: fetch data, set up chart, wire filter buttons.
 */
async function initMeritOrder() {
  const container = document.getElementById('merit-order-container');
  if (!container) return;

  let data;
  try {
    const res = await fetch('data/fleet-merit-order.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.error('viz-merit-order: failed to load data', err);
    container.innerHTML = `<div style="padding:2rem;text-align:center;color:#888;">
      Unable to load merit order data.</div>`;
    return;
  }

  const generators = prepareGenerators(data.generators || []);

  // Active fuel groups — all active at start
  const activeFuels = new Set(['all', 'nuclear', 'coal', 'gas_cc', 'gas_ct', 'wind', 'solar', 'hydro', 'storage']);

  const colorScale = fuelColorScale();
  const tooltip = addTooltip('merit-tooltip');

  // Chart state: SVG bar selection cached after draw
  let barSelection = null;

  /**
   * Draw the full merit order chart into the container.
   * Called once on init and on resize by responsiveChart.
   * @param {number} width - container pixel width
   * @param {number} height - container pixel height
   */
  function draw(width, height) {
    const m = margin({ top: 24, right: 24, bottom: 48, left: 56 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    d3.select(container).selectAll('svg').remove();

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('aria-label', 'Merit order supply stack chart');

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    // Total capacity for x-domain
    const totalMW = d3.sum(generators, d => d.pmax_mw);
    const xMax = Math.max(totalMW, DEMAND_MW * 1.05);

    const xScale = d3.scaleLinear()
      .domain([0, xMax])
      .range([0, w]);

    const yMax = d3.max(generators, d => d.mc_display) * 1.12;
    const yScale = d3.scaleLinear()
      .domain([0, Math.max(yMax, 50)])
      .range([h, 0]);

    // Y-axis gridlines
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .ticks(5)
        .tickSize(-w)
        .tickFormat(''))
      .selectAll('line')
      .attr('stroke', 'rgba(255,255,255,0.07)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid .domain').remove();

    // Generator bars
    barSelection = g.selectAll('.gen-bar')
      .data(generators)
      .join('rect')
        .attr('class', d => `gen-bar gen-fuel-${FUEL_GROUP[d.fuel_type] || 'other'}`)
        .attr('x', d => xScale(d.cumStart))
        .attr('y', d => yScale(d.mc_display))
        .attr('width', d => Math.max(1, xScale(d.cumEnd) - xScale(d.cumStart)))
        .attr('height', d => h - yScale(d.mc_display))
        .attr('fill', d => colorScale(FUEL_COLOR_KEY[d.fuel_type] || 'fossil-gas'))
        .attr('fill-opacity', 0.85)
        .attr('stroke', 'rgba(255,255,255,0.08)')
        .attr('stroke-width', 0.5)
        .style('cursor', 'pointer')
        .on('mouseenter', (event, d) => {
          const html = `
            <div class="tooltip__title">${d.name}</div>
            <div class="tooltip__row">
              <span class="tooltip__key">Fuel</span>
              <span class="tooltip__val">${FUEL_LABEL[d.fuel_type] || d.fuel_type}</span>
            </div>
            <div class="tooltip__row">
              <span class="tooltip__key">Zone</span>
              <span class="tooltip__val">${d.zone}</span>
            </div>
            <div class="tooltip__row">
              <span class="tooltip__key">Capacity</span>
              <span class="tooltip__val">${formatMW(d.pmax_mw)}</span>
            </div>
            <div class="tooltip__row">
              <span class="tooltip__key">MC</span>
              <span class="tooltip__val">${d.mc_total === 0 ? '$0/MWh' : '$' + d.mc_total.toFixed(1) + '/MWh'}</span>
            </div>
            <div class="tooltip__row">
              <span class="tooltip__key">Tranche</span>
              <span class="tooltip__val">${d.tranche}</span>
            </div>`;
          tooltip.show(html, event);
        })
        .on('mouseleave', () => tooltip.hide());

    // Demand line at 55 GW
    const demandX = xScale(DEMAND_MW);
    g.append('line')
      .attr('class', 'demand-line')
      .attr('x1', demandX)
      .attr('x2', demandX)
      .attr('y1', -8)
      .attr('y2', h)
      .attr('stroke', '#F59E0B')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '7,4');

    // Demand line label
    g.append('text')
      .attr('x', demandX + 6)
      .attr('y', 12)
      .attr('font-size', '11px')
      .attr('font-weight', '700')
      .attr('fill', '#F59E0B')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('55 GW demand');

    // Region labels: "DISPATCHING" and "IDLE"
    if (demandX > 60) {
      g.append('text')
        .attr('x', demandX / 2)
        .attr('y', h + 36)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', 'rgba(255,255,255,0.35)')
        .attr('font-family', "'DM Sans', sans-serif")
        .attr('letter-spacing', '0.08em')
        .text('◀ DISPATCHING');
    }

    if (w - demandX > 60) {
      g.append('text')
        .attr('x', demandX + (w - demandX) / 2)
        .attr('y', h + 36)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', 'rgba(255,255,255,0.25)')
        .attr('font-family', "'DM Sans', sans-serif")
        .attr('letter-spacing', '0.08em')
        .text('IDLE ▶');
    }

    // X-axis
    const xAxis = d3.axisBottom(xScale)
      .ticks(6)
      .tickFormat(d => (d / 1000).toFixed(0) + ' GW');

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

    // Y-axis
    const yAxis = d3.axisLeft(yScale)
      .ticks(6)
      .tickFormat(d => `$${d}`);

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
      .text('Marginal Cost ($/MWh)');

    // Apply current filter state
    applyFilter();
  }

  /**
   * Apply the current activeFuels filter by adjusting bar opacity.
   * Does NOT redraw the chart — only mutates opacity attributes.
   */
  function applyFilter() {
    if (!barSelection) return;
    const showAll = activeFuels.has('all');
    barSelection.attr('fill-opacity', d => {
      const group = FUEL_GROUP[d.fuel_type] || 'other';
      return (showAll || activeFuels.has(group)) ? 0.85 : 0.08;
    });
  }

  // Wire up fuel filter buttons
  const filterButtons = document.querySelectorAll('.fuel-filter-btn');
  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const fuel = btn.dataset.fuel;

      if (fuel === 'all') {
        const allActive = filterButtons.length > 1 &&
          Array.from(filterButtons).filter(b => b.dataset.fuel !== 'all').every(b => b.classList.contains('active'));

        if (allActive) {
          filterButtons.forEach(b => {
            if (b.dataset.fuel !== 'all') b.classList.remove('active');
          });
          activeFuels.clear();
          activeFuels.add('all');
          btn.classList.add('active');
        } else {
          filterButtons.forEach(b => b.classList.add('active'));
          activeFuels.clear();
          activeFuels.add('all');
          ['nuclear','coal','gas_cc','gas_ct','wind','solar','hydro','storage'].forEach(f => activeFuels.add(f));
        }
      } else {
        activeFuels.delete('all');
        document.querySelector('.fuel-filter-btn[data-fuel="all"]')?.classList.remove('active');

        if (activeFuels.has(fuel)) {
          activeFuels.delete(fuel);
          btn.classList.remove('active');
        } else {
          activeFuels.add(fuel);
          btn.classList.add('active');
        }

        const allFuels = ['nuclear','coal','gas_cc','gas_ct','wind','solar','hydro','storage'];
        if (allFuels.every(f => activeFuels.has(f))) {
          activeFuels.add('all');
          document.querySelector('.fuel-filter-btn[data-fuel="all"]')?.classList.add('active');
        }
      }

      applyFilter();
    });
  });

  // Mount responsive chart — draws once and on resize, does NOT redraw on filter
  responsiveChart('#merit-order-container', (w, h) => draw(w, h));
}

/**
 * Sort generators by mc_total ascending, compute cumulative MW positions,
 * and set display MC for zero-cost generators.
 *
 * @param {Array} generators - raw generator array from JSON
 * @returns {Array} enriched generator array with cumStart, cumEnd, mc_display
 */
function prepareGenerators(generators) {
  const sorted = [...generators].sort((a, b) => a.mc_total - b.mc_total);
  let cumulative = 0;
  return sorted.map(g => {
    const cumStart = cumulative;
    cumulative += g.pmax_mw;
    return {
      ...g,
      cumStart,
      cumEnd: cumulative,
      // Zero-MC generators get a small display height so they're visible
      mc_display: g.mc_total === 0 ? ZERO_MC_DISPLAY : g.mc_total,
    };
  });
}
