/**
 * viz-ordc.js — Interactive ORDC (Operating Reserve Demand Curve) Visualization
 *
 * Renders an ORDC demand curve with interactive reserve-level slider.
 * X-axis: reserve (MW). Y-axis: penalty ($/MWh).
 * Slider moves a marker along the curve; tooltip shows LOLP and penalty.
 *
 * Requires D3 v7 and chart-utils.js
 */

import { responsiveChart, cssColor } from './chart-utils.js';

export function initOrdcChart(containerId, dataUrl) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.warn(`initOrdcChart: container #${containerId} not found`);
    return;
  }

  fetch(dataUrl)
    .then(r => r.json())
    .then(data => renderOrdcChart(container, data))
    .catch(e => {
      console.error('Error loading ORDC data:', e);
      container.innerHTML = '<p style="color: var(--text-muted); padding: 20px;">Could not load ORDC curve data.</p>';
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initOrdcChart('ordc-chart-container', 'data/ordc-curve.json');
  });
} else {
  initOrdcChart('ordc-chart-container', 'data/ordc-curve.json');
}

function renderOrdcChart(container, data) {
  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Extract parameters and data points from the JSON
  const { parameters, data_points, iso } = data;
  const targetReserve = parameters.target_reserve_mw;
  const voll = parameters.voll_per_mwh;

  // Sort by reserve (descending)
  const points = [...data_points].sort((a, b) => b.reserve_mw - a.reserve_mw);

  // Responsive chart setup
  responsiveChart(container, (width, height) => {
    container.innerHTML = ''; // clear on resize

    // Margins and dimensions
    const margin = { top: 32, right: 40, bottom: 48, left: 60 };
    const chartW = width - margin.left - margin.right;
    const chartH = Math.max(300, height - margin.top - margin.bottom);

    // Scales
    const maxReserve = Math.max(...points.map(p => p.reserve_mw)) * 1.1;
    const maxPenalty = voll * 1.05;

    const xScale = d3.scaleLinear()
      .domain([0, maxReserve])
      .range([0, chartW]);

    const yScale = d3.scaleLinear()
      .domain([0, maxPenalty])
      .range([chartH, 0]);

    // SVG
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('role', 'img')
      .attr('aria-label', `ORDC curve for ${iso || 'ERCOT'}: reserve level vs penalty price`);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Axes
    const xAxis = d3.axisBottom(xScale)
      .tickSize(-chartH)
      .tickFormat(d => d >= 1000 ? `${(d / 1000).toFixed(1)}k` : d);

    const yAxis = d3.axisLeft(yScale)
      .tickSize(-chartW)
      .tickFormat(d => `$${d.toFixed(0)}`);

    g.append('g')
      .attr('class', 'axis axis-x')
      .attr('transform', `translate(0,${chartH})`)
      .call(xAxis)
      .style('font-size', '11px')
      .style('color', 'var(--text-muted)');

    g.append('g')
      .attr('class', 'axis axis-y')
      .call(yAxis)
      .style('font-size', '11px')
      .style('color', 'var(--text-muted)');

    // Axis labels
    g.append('text')
      .attr('x', chartW / 2)
      .attr('y', chartH + 36)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', '600')
      .style('color', 'var(--text-secondary)')
      .text('Online Reserves (MW)');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -chartH / 2)
      .attr('y', -44)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('font-weight', '600')
      .style('color', 'var(--text-secondary)')
      .text('Penalty ($/MWh)');

    // Target reserve line (vertical dashed)
    g.append('line')
      .attr('x1', xScale(targetReserve))
      .attr('x2', xScale(targetReserve))
      .attr('y1', 0)
      .attr('y2', chartH)
      .attr('stroke', 'rgba(107, 114, 128, 0.3)')
      .attr('stroke-dasharray', '4,4')
      .attr('stroke-width', 1);

    g.append('text')
      .attr('x', xScale(targetReserve))
      .attr('y', -8)
      .attr('text-anchor', 'middle')
      .style('font-size', '10px')
      .style('color', 'var(--text-muted)')
      .style('font-weight', '500')
      .text(`Target: ${(targetReserve / 1000).toFixed(1)}k MW`);

    // VOLL line (horizontal dashed)
    g.append('line')
      .attr('x1', 0)
      .attr('x2', chartW)
      .attr('y1', yScale(voll))
      .attr('y2', yScale(voll))
      .attr('stroke', 'rgba(220, 38, 38, 0.2)')
      .attr('stroke-dasharray', '4,4')
      .attr('stroke-width', 1);

    g.append('text')
      .attr('x', -8)
      .attr('y', yScale(voll) - 4)
      .attr('text-anchor', 'end')
      .style('font-size', '10px')
      .style('color', 'var(--text-muted)')
      .style('font-weight', '500')
      .text(`VOLL: $${voll}`);

    // Line generator
    const line = d3.line()
      .x(d => xScale(d.reserve_mw))
      .y(d => yScale(d.penalty_per_mwh));

    // Curve
    g.append('path')
      .datum(points)
      .attr('fill', 'none')
      .attr('stroke', 'var(--warning)')
      .attr('stroke-width', 2.5)
      .attr('d', line);

    // Data points (small circles)
    g.selectAll('.ordc-dot')
      .data(points)
      .join('circle')
      .attr('class', 'ordc-dot')
      .attr('cx', d => xScale(d.reserve_mw))
      .attr('cy', d => yScale(d.penalty_per_mwh))
      .attr('r', 2.5)
      .attr('fill', 'var(--warning)')
      .attr('opacity', 0.7);

    // Interactive slider for reserve level
    const sliderContainer = d3.select(container).insert('div', ':first-child')
      .style('padding', `${margin.top / 2}px ${margin.left}px 0`)
      .style('display', 'flex')
      .style('align-items', 'center')
      .style('gap', '12px')
      .style('font-size', '12px')
      .style('color', 'var(--text-secondary)');

    sliderContainer.append('label')
      .style('font-weight', '600')
      .text('Reserve level:');

    const slider = sliderContainer.append('input')
      .attr('type', 'range')
      .attr('min', 0)
      .attr('max', maxReserve)
      .attr('value', targetReserve)
      .attr('step', 100)
      .style('flex', '1')
      .style('max-width', '300px')
      .style('cursor', 'pointer');

    const valueLabel = sliderContainer.append('div')
      .style('min-width', '140px')
      .style('font-weight', '600')
      .style('color', 'var(--warning)')
      .text(`${Math.round(targetReserve).toLocaleString()} MW`);

    // Tooltip for marker
    const tooltip = d3.select(container).append('div')
      .style('position', 'absolute')
      .style('background', 'rgba(10, 18, 38, 0.96)')
      .style('border', '1px solid rgba(255, 255, 255, 0.14)')
      .style('border-radius', '8px')
      .style('padding', '12px 16px')
      .style('pointer-events', 'none')
      .style('z-index', '9999')
      .style('opacity', '0')
      .style('transition', 'opacity 140ms ease')
      .style('max-width', '220px')
      .style('font-size', '12px')
      .style('color', 'rgba(255, 255, 255, 0.85)');

    // Marker circle on curve
    const marker = g.append('circle')
      .attr('class', 'ordc-marker')
      .attr('r', 5.5)
      .attr('fill', 'var(--warning)')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('opacity', 0);

    function interpolateOrdc(reserveMw) {
      // Find two adjacent points and interpolate linearly
      let below = points[0], above = points[points.length - 1];
      for (let i = 0; i < points.length - 1; i++) {
        if (points[i].reserve_mw >= reserveMw && points[i + 1].reserve_mw <= reserveMw) {
          above = points[i];
          below = points[i + 1];
          break;
        }
      }

      const pct = (reserveMw - below.reserve_mw) / (above.reserve_mw - below.reserve_mw);
      const pctClamped = Math.max(0, Math.min(1, pct));

      const penaltyMwh = below.penalty_per_mwh + (above.penalty_per_mwh - below.penalty_per_mwh) * pctClamped;
      const lolp = below.lolp + (above.lolp - below.lolp) * pctClamped;

      return { penaltyMwh, lolp };
    }

    function updateMarker(reserveMw) {
      const { penaltyMwh, lolp } = interpolateOrdc(reserveMw);

      // Update marker position
      marker
        .attr('cx', xScale(reserveMw))
        .attr('cy', yScale(penaltyMwh))
        .style('opacity', 1);

      // Update value label
      valueLabel.text(`${Math.round(reserveMw).toLocaleString()} MW`);

      // Update tooltip
      const tooltipHtml = `
        <div style="font-weight: 700; margin-bottom: 6px; font-size: 11px; color: #fff;">
          Reserve Level
        </div>
        <div style="font-size: 11px; line-height: 1.5;">
          <div><strong>Reserves:</strong> ${(reserveMw / 1000).toFixed(2)} GW</div>
          <div><strong>Penalty:</strong> $${penaltyMwh.toFixed(0)}/MWh</div>
          <div><strong>LOLP:</strong> ${(lolp * 100).toFixed(2)}%</div>
        </div>
      `;
      tooltip.html(tooltipHtml);

      // Position tooltip near marker (if it fits)
      const tooltipNode = tooltip.node();
      const markerX = margin.left + xScale(reserveMw);
      const markerY = margin.top + yScale(penaltyMwh);

      let tooltipX = markerX + 12;
      let tooltipY = markerY - tooltipNode.offsetHeight / 2;

      if (tooltipX + tooltipNode.offsetWidth > window.innerWidth - 16) {
        tooltipX = markerX - tooltipNode.offsetWidth - 12;
      }
      if (tooltipY < 8) tooltipY = 8;
      if (tooltipY + tooltipNode.offsetHeight > window.innerHeight - 8) {
        tooltipY = window.innerHeight - tooltipNode.offsetHeight - 8;
      }

      tooltip
        .style('left', `${tooltipX}px`)
        .style('top', `${tooltipY}px`)
        .style('opacity', 1);
    }

    slider.on('input', function () {
      updateMarker(+this.value);
    });

    slider.on('mouseenter', function () {
      tooltip.style('opacity', 1);
    });

    slider.on('mouseleave', function () {
      tooltip.style('opacity', 0);
    });

    // Initial marker position
    if (!REDUCED_MOTION) {
      marker.style('opacity', 0);
      setTimeout(() => {
        updateMarker(targetReserve);
      }, 100);
    } else {
      updateMarker(targetReserve);
    }

    // Keyboard support for slider
    slider.on('keydown', function (e) {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
        this.value = Math.max(0, +this.value - 100);
        slider.dispatch('input');
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
        this.value = Math.min(maxReserve, +this.value + 100);
        slider.dispatch('input');
      }
    });
  });
}