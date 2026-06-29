/**
 * viz-stacked-area.js — V17 stacked-area chart for capacity/generation trajectories
 * Used on: capacity-evolution.html
 *
 * X-axis: 2026–2050. Y-axis: GW (capacity) or TWh (generation).
 * Stacked by fuel type using fuelColorScale. Toggle between capacity and generation.
 */

import {
  responsiveChart,
  fuelColorScale,
  addTooltip,
  formatMW,
  makeAxis,
  styleAxis,
  styleAxisDark,
  margin,
} from './chart-utils.js';

document.addEventListener('DOMContentLoaded', initStackedArea);

const CAPACITY_FUELS = [
  'nuclear', 'coal', 'gas_cc', 'gas_ct', 'hydro',
  'wind', 'offshore_wind', 'solar',
  'storage', 'ccs', 'hydrogen', 'geothermal',
];

const GENERATION_FUELS = [
  'nuclear', 'coal', 'gas_cc', 'gas_ct', 'hydro',
  'wind', 'offshore_net', 'solar',
  'ccs_net', 'hydrogen_net', 'geothermal',
];

const FUEL_LABELS = {
  nuclear: 'Nuclear', coal: 'Coal', gas_cc: 'Gas CC', gas_ct: 'Gas CT',
  hydro: 'Hydro', wind: 'Wind', offshore_wind: 'Offshore Wind',
  solar: 'Solar', storage: 'Storage', ccs: 'CCS', hydrogen: 'Hydrogen',
  geothermal: 'Geothermal', offshore_net: 'Offshore Wind',
  ccs_net: 'CCS', hydrogen_net: 'Hydrogen', storage_net: 'Storage (net)',
};

const COLOR_MAP = {
  nuclear: 'nuclear', coal: 'coal', gas_cc: 'gas', gas_ct: 'gas',
  hydro: 'hydro', wind: 'wind', offshore_wind: 'offshore',
  solar: 'solar', storage: 'storage', ccs: 'ccs', hydrogen: 'hydrogen',
  geothermal: 'geothermal', offshore_net: 'offshore',
  ccs_net: 'ccs', hydrogen_net: 'hydrogen', storage_net: 'storage',
};

async function initStackedArea() {
  const container = document.getElementById('stacked-area-container');
  if (!container) return;

  let capacityData, generationData;
  try {
    const [capRes, genRes] = await Promise.all([
      fetch('data/capacity-trajectory.json'),
      fetch('data/generation-trajectory.json'),
    ]);
    if (!capRes.ok || !genRes.ok) throw new Error('HTTP error');
    capacityData = await capRes.json();
    generationData = await genRes.json();
  } catch (err) {
    console.error('Failed to load trajectory data:', err);
    container.innerHTML = '<div style="padding:2rem;text-align:center;color:#666;">Unable to load data.</div>';
    return;
  }

  let mode = 'capacity';
  const colorScale = fuelColorScale();
  const tooltip = addTooltip('stacked-area-tooltip');

  function getData() {
    return mode === 'capacity' ? capacityData.years : generationData.years;
  }

  function getFuels() {
    return mode === 'capacity' ? CAPACITY_FUELS : GENERATION_FUELS;
  }

  function draw(width, height) {
    d3.select(container).selectAll('svg').remove();

    const isDark = container.closest('.section-dark') !== null;
    const m = margin({ top: 20, right: 24, bottom: 44, left: 56 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;
    const data = getData();
    const fuels = getFuels();

    // Build stack data
    const stackData = data.map(yr => {
      const row = { year: yr.year };
      fuels.forEach(f => {
        row[f] = Math.max(0, yr[f] || 0);
      });
      return row;
    });

    const stack = d3.stack()
      .keys(fuels)
      .order(d3.stackOrderNone)
      .offset(d3.stackOffsetNone);

    const series = stack(stackData);

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('role', 'img')
      .attr('aria-label', `${mode === 'capacity' ? 'Capacity (GW)' : 'Generation (TWh)'} trajectory 2026-2050`);

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    // Scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(data, d => d.year))
      .range([0, w]);

    const yMax = d3.max(series, s => d3.max(s, d => d[1])) * 1.05;
    const yScale = d3.scaleLinear()
      .domain([0, yMax])
      .range([h, 0]);

    // Grid lines
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).tickSize(-w).tickFormat('').ticks(6))
      .selectAll('line')
      .attr('stroke', isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid .domain').remove();

    // Area generator
    const area = d3.area()
      .x(d => xScale(d.data.year))
      .y0(d => yScale(d[0]))
      .y1(d => yScale(d[1]))
      .curve(d3.curveMonotoneX);

    // Draw areas
    g.selectAll('.fuel-area')
      .data(series)
      .join('path')
      .attr('class', d => `fuel-area fuel-area-${d.key}`)
      .attr('d', area)
      .attr('fill', d => colorScale(COLOR_MAP[d.key] || d.key))
      .attr('fill-opacity', 0.8)
      .attr('stroke', d => colorScale(COLOR_MAP[d.key] || d.key))
      .attr('stroke-width', 0.5)
      .attr('stroke-opacity', 0.3);

    // Axes
    const xAxis = makeAxis('x', xScale, {
      ticks: width < 500 ? 4 : 8,
      tickFormat: d3.format('d'),
    });
    const xG = g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(xAxis);
    isDark ? styleAxisDark(xG) : styleAxis(xG);

    const unit = mode === 'capacity' ? 'GW' : 'TWh';
    const yAxis = makeAxis('y', yScale, {
      ticks: 6,
      tickFormat: v => `${Math.round(v)} ${unit}`,
    });
    const yG = g.append('g').call(yAxis);
    isDark ? styleAxisDark(yG) : styleAxis(yG);

    // Hover overlay
    const bisect = d3.bisector(d => d.year).left;
    const hoverLine = g.append('line')
      .attr('stroke', isDark ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.15)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3')
      .attr('y1', 0).attr('y2', h)
      .style('display', 'none');

    const overlay = g.append('rect')
      .attr('width', w).attr('height', h)
      .attr('fill', 'none').attr('pointer-events', 'all');

    overlay
      .on('mousemove', (event) => {
        const [mx] = d3.pointer(event, overlay.node());
        const yearVal = xScale.invert(mx);
        const idx = bisect(data, yearVal);
        const d = data[Math.min(idx, data.length - 1)];
        if (!d) return;

        hoverLine
          .attr('x1', xScale(d.year))
          .attr('x2', xScale(d.year))
          .style('display', null);

        let html = `<strong>${d.year}</strong><br>`;
        const activeFuels = fuels.filter(f => (d[f] || 0) > 0);
        activeFuels.reverse().forEach(f => {
          const val = d[f] || 0;
          const label = FUEL_LABELS[f] || f;
          const color = colorScale(COLOR_MAP[f] || f);
          html += `<span style="color:${color};">■</span> ${label}: <strong>${val.toFixed(1)} ${unit}</strong><br>`;
        });

        if (mode === 'generation' && d.demand) {
          html += `<span style="color:#E91E63;">━</span> Demand: <strong>${d.demand.toFixed(0)} TWh</strong>`;
        } else if (mode === 'capacity' && d.total_mw) {
          html += `Total: <strong>${d.total_mw.toFixed(1)} GW</strong>`;
        }

        tooltip.show(html, event);
      })
      .on('mouseleave', () => {
        hoverLine.style('display', 'none');
        tooltip.hide();
      });

    // Legend
    const activeFuels = fuels.filter(f =>
      data.some(yr => (yr[f] || 0) > 0)
    );
    const legendG = svg.append('g')
      .attr('transform', `translate(${m.left + 8},${m.top})`);

    activeFuels.forEach((f, i) => {
      const col = Math.floor(i / 4);
      const row = i % 4;
      const item = legendG.append('g')
        .attr('transform', `translate(${col * 120},${row * 18})`);

      item.append('rect')
        .attr('width', 10).attr('height', 10).attr('rx', 2)
        .attr('fill', colorScale(COLOR_MAP[f] || f));

      item.append('text')
        .attr('x', 14).attr('y', 9)
        .attr('font-size', '10px')
        .attr('fill', isDark ? 'rgba(241,245,249,0.65)' : '#566370')
        .attr('font-family', "'DM Sans', sans-serif")
        .text(FUEL_LABELS[f] || f);
    });
  }

  // Mode toggle
  const toggleBtns = document.querySelectorAll('#trajectory-mode .btn');
  toggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      toggleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      mode = btn.dataset.mode;
      const w = container.clientWidth;
      const h = container.clientHeight || Math.round(w * 0.5);
      draw(w, h);
    });
  });

  responsiveChart(container, (w, h) => draw(w, h));
}

export { initStackedArea };
