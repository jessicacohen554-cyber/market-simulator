/**
 * viz-storage-value.js — V20 storage value-stack bar chart
 * Used on: capacity-evolution.html
 *
 * Grouped bars per storage tech: stacked revenue components (arbitrage +
 * capacity value + AS) vs LCOE line. Shows economic screening logic.
 */

import {
  responsiveChart,
  addTooltip,
  makeAxis,
  styleAxis,
  styleAxisDark,
  margin,
} from './chart-utils.js';

document.addEventListener('DOMContentLoaded', initStorageValue);

const COMPONENT_COLORS = {
  arbitrage: '#0EA5E9',
  capacity_value: '#6366F1',
  as_revenue: '#22C55E',
};

const COMPONENT_LABELS = {
  arbitrage: 'Arbitrage',
  capacity_value: 'Capacity Value',
  as_revenue: 'Ancillary Services',
};

const TECH_LABELS = {
  li_ion_4hr: 'Li-Ion 4hr',
  li_ion_8hr: 'Li-Ion 8hr',
  flow_battery: 'Flow Battery',
  pumped_hydro: 'Pumped Hydro',
};

async function initStorageValue() {
  const container = document.getElementById('storage-value-container');
  if (!container) return;

  let data;
  try {
    const res = await fetch('data/storage-value-stack.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.error('Failed to load storage-value-stack data:', err);
    container.innerHTML = '<div style="padding:2rem;text-align:center;color:#666;">Unable to load data.</div>';
    return;
  }

  const tooltip = addTooltip('storage-value-tooltip');
  const techs = data.technologies;

  function draw(width, height) {
    d3.select(container).selectAll('svg').remove();

    const isDark = container.closest('.section-dark') !== null;
    const m = margin({ top: 20, right: 24, bottom: 60, left: 56 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('role', 'img')
      .attr('aria-label', 'Storage technology value stack vs LCOE');

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    // Scales
    const xScale = d3.scaleBand()
      .domain(techs.map(t => t.tech))
      .range([0, w])
      .padding(0.35);

    const components = ['arbitrage_per_kw_yr', 'capacity_value_per_kw_yr', 'as_revenue_per_kw_yr'];
    const componentKeys = ['arbitrage', 'capacity_value', 'as_revenue'];

    const maxVal = Math.max(
      d3.max(techs, t => t.revenue_components.total_value_per_kw_yr),
      d3.max(techs, t => t.lcoe_per_kwh),
    ) * 1.15;

    const yScale = d3.scaleLinear()
      .domain([0, maxVal])
      .range([h, 0]);

    // Grid
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).tickSize(-w).tickFormat('').ticks(6))
      .selectAll('line')
      .attr('stroke', isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid .domain').remove();

    // Stacked bars
    techs.forEach(tech => {
      const x = xScale(tech.tech);
      const bw = xScale.bandwidth();
      const rev = tech.revenue_components;
      let cumY = 0;

      const stackData = [
        { key: 'arbitrage', value: rev.arbitrage_per_kw_yr },
        { key: 'capacity_value', value: rev.capacity_value_per_kw_yr },
        { key: 'as_revenue', value: rev.as_revenue_per_kw_yr },
      ];

      stackData.forEach(comp => {
        const barH = yScale(0) - yScale(comp.value);
        g.append('rect')
          .attr('x', x)
          .attr('y', yScale(cumY + comp.value))
          .attr('width', bw)
          .attr('height', barH)
          .attr('fill', COMPONENT_COLORS[comp.key])
          .attr('fill-opacity', 0.8)
          .attr('rx', comp.key === 'as_revenue' ? 4 : 0)
          .style('cursor', 'pointer')
          .on('mouseenter', (event) => {
            const label = TECH_LABELS[tech.tech] || tech.tech;
            const margin = tech.margin_per_kw_yr;
            const marginColor = margin >= 0 ? '#22C55E' : '#EF4444';
            tooltip.show(
              `<strong>${label}</strong> (${tech.duration}h)<br><br>` +
              `<span style="color:${COMPONENT_COLORS.arbitrage}">■</span> Arbitrage: $${rev.arbitrage_per_kw_yr}/kW/yr<br>` +
              `<span style="color:${COMPONENT_COLORS.capacity_value}">■</span> Capacity: $${rev.capacity_value_per_kw_yr}/kW/yr<br>` +
              `<span style="color:${COMPONENT_COLORS.as_revenue}">■</span> AS Rev: $${rev.as_revenue_per_kw_yr}/kW/yr<br>` +
              `<strong>Total: $${rev.total_value_per_kw_yr}/kW/yr</strong><br><br>` +
              `LCOE: $${tech.lcoe_per_kwh}/kW/yr<br>` +
              `<span style="color:${marginColor}">Margin: $${margin}/kW/yr (${tech.margin_pct.toFixed(1)}%)</span>`,
              event
            );
          })
          .on('mouseleave', () => tooltip.hide());

        cumY += comp.value;
      });

      // LCOE marker
      const lcoeY = yScale(tech.lcoe_per_kwh);
      g.append('line')
        .attr('x1', x - 6)
        .attr('x2', x + bw + 6)
        .attr('y1', lcoeY)
        .attr('y2', lcoeY)
        .attr('stroke', '#EF4444')
        .attr('stroke-width', 2.5)
        .attr('stroke-linecap', 'round');

      // LCOE label
      g.append('text')
        .attr('x', x + bw + 8)
        .attr('y', lcoeY + 4)
        .attr('font-size', '9px')
        .attr('font-weight', '600')
        .attr('fill', '#EF4444')
        .attr('font-family', "'DM Sans', sans-serif")
        .text(`$${tech.lcoe_per_kwh}`);

      // Margin indicator
      const margin = tech.margin_per_kw_yr;
      const marginColor = margin >= 0 ? '#22C55E' : '#EF4444';
      g.append('text')
        .attr('x', x + bw / 2)
        .attr('y', yScale(cumY) - 8)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '700')
        .attr('fill', marginColor)
        .attr('font-family', "'DM Sans', sans-serif")
        .text(margin >= 0 ? `+$${margin}` : `-$${Math.abs(margin)}`);
    });

    // Axes
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d => TECH_LABELS[d] || d);
    const xG = g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(xAxis);
    isDark ? styleAxisDark(xG) : styleAxis(xG);
    xG.selectAll('text')
      .attr('transform', width < 500 ? 'rotate(-25)' : 'rotate(0)')
      .style('text-anchor', width < 500 ? 'end' : 'middle');

    const yAxis = makeAxis('y', yScale, {
      ticks: 6,
      tickFormat: v => `$${Math.round(v)}`,
    });
    const yG = g.append('g').call(yAxis);
    isDark ? styleAxisDark(yG) : styleAxis(yG);

    // Y label
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -m.left + 14)
      .attr('x', -h / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', isDark ? 'rgba(241,245,249,0.5)' : '#566370')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('$/kW/yr');

    // Legend
    const legendY = h + 34;
    const legendItems = [
      ...componentKeys.map(k => ({ label: COMPONENT_LABELS[k], color: COMPONENT_COLORS[k], type: 'rect' })),
      { label: 'LCOE', color: '#EF4444', type: 'line' },
    ];

    const legendG = g.append('g').attr('transform', `translate(0,${legendY})`);
    let lx = 0;
    legendItems.forEach(item => {
      const ig = legendG.append('g').attr('transform', `translate(${lx},0)`);
      if (item.type === 'rect') {
        ig.append('rect').attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', item.color);
      } else {
        ig.append('line').attr('x1', 0).attr('x2', 14).attr('y1', 5).attr('y2', 5)
          .attr('stroke', item.color).attr('stroke-width', 2.5);
      }
      ig.append('text')
        .attr('x', 16).attr('y', 9)
        .attr('font-size', '10px')
        .attr('fill', isDark ? 'rgba(241,245,249,0.55)' : '#566370')
        .attr('font-family', "'DM Sans', sans-serif")
        .text(item.label);
      lx += item.label.length * 6.5 + 28;
    });
  }

  responsiveChart(container, (w, h) => draw(w, h));
}

export { initStorageValue };
