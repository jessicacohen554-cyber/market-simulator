/**
 * viz-learning.js — V18 log-log learning curve chart (Wright's Law)
 * Used on: capacity-evolution.html
 *
 * X-axis: cumulative GW deployed (log). Y-axis: capex $/kW (log).
 * Lines for solar, wind, li_ion_4hr, offshore_wind, li_ion_8hr.
 */

import {
  responsiveChart,
  addTooltip,
  makeAxis,
  styleAxis,
  styleAxisDark,
  margin,
  formatYear,
} from './chart-utils.js';

document.addEventListener('DOMContentLoaded', initLearning);

const TECH_COLORS = {
  solar_utility: '#F59E0B',
  wind_onshore: '#22C55E',
  wind_offshore: '#009688',
  li_ion_4hr: '#E67E22',
  li_ion_8hr: '#D97706',
};

const TECH_LABELS = {
  solar_utility: 'Solar PV',
  wind_onshore: 'Onshore Wind',
  wind_offshore: 'Offshore Wind',
  li_ion_4hr: 'Li-Ion 4hr',
  li_ion_8hr: 'Li-Ion 8hr',
};

async function initLearning() {
  const container = document.getElementById('learning-curves-container');
  if (!container) return;

  let data;
  try {
    const res = await fetch('data/learning-curves.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.error('Failed to load learning-curves data:', err);
    container.innerHTML = '<div style="padding:2rem;text-align:center;color:#666;">Unable to load data.</div>';
    return;
  }

  const tooltip = addTooltip('learning-tooltip');
  const techs = data.technologies;

  function draw(width, height) {
    d3.select(container).selectAll('svg').remove();

    const isDark = container.closest('.section-dark') !== null;
    const m = margin({ top: 20, right: 24, bottom: 48, left: 58 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    const allPoints = techs.flatMap(t => t.data);

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('role', 'img')
      .attr('aria-label', 'Wright\'s Law learning curves on log-log axes');

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    // Log scales
    const xScale = d3.scaleLog()
      .domain([
        d3.min(allPoints, d => d.cum_capacity_gw) * 0.8,
        d3.max(allPoints, d => d.cum_capacity_gw) * 1.2,
      ])
      .range([0, w]);

    const yScale = d3.scaleLog()
      .domain([
        d3.min(allPoints, d => d.capex_per_kw) * 0.8,
        d3.max(allPoints, d => d.capex_per_kw) * 1.2,
      ])
      .range([h, 0]);

    // Grid
    g.append('g')
      .attr('class', 'grid-y')
      .call(d3.axisLeft(yScale).tickSize(-w).tickFormat('').ticks(6))
      .selectAll('line')
      .attr('stroke', isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid-y .domain').remove();

    g.append('g')
      .attr('class', 'grid-x')
      .attr('transform', `translate(0,${h})`)
      .call(d3.axisBottom(xScale).tickSize(-h).tickFormat('').ticks(5))
      .selectAll('line')
      .attr('stroke', isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid-x .domain').remove();

    // Line generator
    const line = d3.line()
      .x(d => xScale(d.cum_capacity_gw))
      .y(d => yScale(d.capex_per_kw))
      .curve(d3.curveMonotoneX);

    // Draw each technology
    techs.forEach(tech => {
      const color = TECH_COLORS[tech.tech] || '#94A3B8';
      const pts = tech.data;

      // Line
      g.append('path')
        .datum(pts)
        .attr('d', line)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2.5)
        .attr('stroke-linecap', 'round');

      // Data points
      g.selectAll(`.dot-${tech.tech}`)
        .data(pts)
        .join('circle')
        .attr('class', `dot-${tech.tech}`)
        .attr('cx', d => xScale(d.cum_capacity_gw))
        .attr('cy', d => yScale(d.capex_per_kw))
        .attr('r', 4)
        .attr('fill', color)
        .attr('stroke', isDark ? '#0f172a' : '#fff')
        .attr('stroke-width', 1.5)
        .style('cursor', 'pointer')
        .on('mouseenter', (event, d) => {
          const label = TECH_LABELS[tech.tech] || tech.name;
          tooltip.show(
            `<strong>${label}</strong><br>` +
            `Year: ${d.year}<br>` +
            `Deployed: ${d.cum_capacity_gw.toLocaleString()} GW<br>` +
            `CAPEX: $${d.capex_per_kw.toLocaleString()}/kW<br>` +
            `<span style="opacity:0.7">Learning rate: ${tech.learning_rate_pct}% per doubling</span>`,
            event
          );
          d3.select(event.target).attr('r', 6);
        })
        .on('mouseleave', (event) => {
          tooltip.hide();
          d3.select(event.target).attr('r', 4);
        });

      // End label
      const lastPt = pts[pts.length - 1];
      g.append('text')
        .attr('x', xScale(lastPt.cum_capacity_gw) + 6)
        .attr('y', yScale(lastPt.capex_per_kw) + 4)
        .attr('font-size', '10px')
        .attr('font-weight', '600')
        .attr('fill', color)
        .attr('font-family', "'DM Sans', sans-serif")
        .text(TECH_LABELS[tech.tech] || tech.tech);
    });

    // Axes
    const xAxis = d3.axisBottom(xScale)
      .ticks(width < 500 ? 3 : 6, '.0s')
      .tickFormat(d => {
        if (d >= 1000) return `${d / 1000}k`;
        return d;
      });
    const xG = g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(xAxis);
    isDark ? styleAxisDark(xG) : styleAxis(xG);

    // X label
    g.append('text')
      .attr('x', w / 2)
      .attr('y', h + 38)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', isDark ? 'rgba(241,245,249,0.55)' : '#566370')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('Cumulative global deployment (GW, log scale)');

    const yAxis = d3.axisLeft(yScale)
      .ticks(5, '$.0s')
      .tickFormat(d => `$${d}`);
    const yG = g.append('g').call(yAxis);
    isDark ? styleAxisDark(yG) : styleAxis(yG);

    // Y label
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -m.left + 14)
      .attr('x', -h / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', isDark ? 'rgba(241,245,249,0.55)' : '#566370')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('Capital cost ($/kW, log scale)');
  }

  responsiveChart(container, (w, h) => draw(w, h));
}

export { initLearning };
