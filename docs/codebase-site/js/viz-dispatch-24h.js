/**
 * viz-dispatch-24h.js — Interactive 24-hour stacked-area dispatch chart
 * D3 visualization showing hourly generation by fuel type, demand line, and LMP.
 * Supports fuel filtering, time scrubber, and hover tooltips.
 */

import { responsiveChart, fuelColorScale, addTooltip, formatMW, formatPrice, makeAxis, styleAxis, margin } from './chart-utils.js';

// Load and initialize when the container is ready
document.addEventListener('DOMContentLoaded', initChart);

async function initChart() {
  const container = document.getElementById('dispatch-24h-container');
  if (!container) return;

  try {
    const response = await fetch('data/dispatch-24h.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    // Initialize chart
    const chart = new Dispatch24hChart(container, data);
    chart.render();

    // Wire up controls
    setupControls(chart, container);
  } catch (error) {
    console.error('Failed to load dispatch-24h data:', error);
    container.innerHTML = `<div style="padding: 2rem; text-align: center; color: #666;">Unable to load visualization data.</div>`;
  }
}

/**
 * Main chart class
 */
class Dispatch24hChart {
  constructor(container, data) {
    this.container = container;
    this.data = data;
    this.hours = data.hours || [];
    this.activeFuels = new Set(['coal', 'gas', 'gas_cc', 'gas_ct', 'wind', 'solar', 'nuclear', 'hydro', 'storage_net', 'imports']);
    this.tooltip = addTooltip('dispatch-tooltip');
    this.colorScale = fuelColorScale();
    this.currentHour = 0;

    // Prepare stacked data
    this.prepareData();
  }

  prepareData() {
    // Get all fuel columns from the first hour
    if (this.hours.length === 0) return;

    const allFuels = Object.keys(this.hours[0]).filter(k =>
      !['hour', 'demand_mw', 'price_per_mwh', 'storage_net', 'imports'].includes(k)
    );

    this.fuels = allFuels.filter(f => this.activeFuels.has(f));

    // Stack data: cumulative generation for stacking
    this.stackedData = this.hours.map((hour, idx) => {
      const row = { hour: hour.hour, demand_mw: hour.demand_mw, price_per_mwh: hour.price_per_mwh };
      let cumulative = 0;
      this.fuels.forEach(fuel => {
        const val = hour[fuel] || 0;
        row[`${fuel}_0`] = cumulative;
        row[`${fuel}_1`] = cumulative + val;
        cumulative += val;
      });
      return row;
    });
  }

  render() {
    this.observer = responsiveChart(this.container, (width, height) => {
      this.draw(width, height);
    });
  }

  draw(width, height) {
    const m = margin({ top: 16, right: 60, bottom: 40, left: 60 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    // Clear previous
    d3.select(this.container).selectAll('svg').remove();

    // Create SVG
    const svg = d3.select(this.container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    // Create group for margins
    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    // Scales
    const xScale = d3.scaleLinear()
      .domain([0, 23])
      .range([0, w]);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(this.stackedData, d => d.demand_mw) * 1.15])
      .range([h, 0]);

    const priceScale = d3.scaleLinear()
      .domain([0, d3.max(this.hours, d => d.price_per_mwh) * 1.2])
      .range([h, 0]);

    // Area generator for stacked areas
    const area = d3.area()
      .x(d => xScale(d.hour))
      .y0(d => yScale(d[`${this.currentFuel}_0`]))
      .y1(d => yScale(d[`${this.currentFuel}_1`]));

    // Create defs for patterns (optional gradients)
    const defs = svg.append('defs');

    // Draw stacked areas for each fuel
    this.fuels.forEach(fuel => {
      if (!this.activeFuels.has(fuel)) return;

      const color = this.colorScale(fuel);
      g.append('path')
        .attr('class', `fuel-area fuel-${fuel}`)
        .attr('d', d3.area()
          .x(d => xScale(d.hour))
          .y0(d => yScale(d[`${fuel}_0`]))
          .y1(d => yScale(d[`${fuel}_1`]))(this.stackedData))
        .attr('fill', color)
        .attr('fill-opacity', 0.7)
        .attr('stroke', 'none')
        .on('mouseenter', () => {
          // Highlight this fuel
          g.selectAll('.fuel-area').attr('fill-opacity', 0.3);
          g.select(`.fuel-${fuel}`).attr('fill-opacity', 0.9);
        })
        .on('mouseleave', () => {
          g.selectAll('.fuel-area').attr('fill-opacity', 0.7);
        });
    });

    // Demand line (dashed)
    const demandLine = d3.line()
      .x(d => xScale(d.hour))
      .y(d => yScale(d.demand_mw));

    g.append('path')
      .attr('class', 'demand-line')
      .attr('d', demandLine(this.hours))
      .attr('fill', 'none')
      .attr('stroke', '#1e293b')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,4')
      .attr('stroke-linecap', 'round');

    // Price line (secondary y-axis)
    const priceLine = d3.line()
      .x(d => xScale(d.hour))
      .y(d => priceScale(d.price_per_mwh));

    g.append('path')
      .attr('class', 'price-line')
      .attr('d', priceLine(this.hours))
      .attr('fill', 'none')
      .attr('stroke', '#E91E63')
      .attr('stroke-width', 2.5)
      .attr('stroke-linecap', 'round');

    // X-axis
    const xAxis = makeAxis('x', xScale, { ticks: 6, tickFormat: h => `${h % 12 || 12}${h < 12 ? 'AM' : 'PM'}` });
    g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(xAxis);
    styleAxis(g.select('[transform="translate(0,' + h + ')"]'));

    // Y-axis (left, generation)
    const yAxis = makeAxis('y', yScale, { ticks: 5, tickFormat: v => `${Math.round(v / 1000)}GW` });
    g.append('g')
      .call(yAxis);
    styleAxis(g.select('g:nth-of-type(3)'));

    // Y-axis label (left)
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - m.left)
      .attr('x', 0 - (h / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '0.9rem')
      .style('font-weight', '600')
      .style('fill', '#566370')
      .text('Generation (GW)');

    // Y-axis (right, price)
    const yAxisRight = makeAxis('y', priceScale, { ticks: 5, tickFormat: v => `$${Math.round(v)}` });
    g.append('g')
      .attr('transform', `translate(${w}, 0)`)
      .call(yAxisRight);
    const rightAxis = g.select(`g[transform="translate(${w}, 0)"]`);
    rightAxis.selectAll('.tick line').remove();
    rightAxis.selectAll('text').attr('fill', '#E91E63').style('font-size', '0.85rem');

    // Y-axis label (right)
    g.append('text')
      .attr('transform', 'rotate(90)')
      .attr('y', w + m.right - 12)
      .attr('x', h / 2)
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '0.9rem')
      .style('font-weight', '600')
      .style('fill', '#E91E63')
      .text('LMP ($/MWh)');

    // Grid lines
    g.append('g')
      .attr('class', 'd3-grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-w)
        .tickFormat('')
      )
      .selectAll('line')
      .attr('stroke', '#e5e7eb')
      .attr('stroke-dasharray', '3,3')
      .attr('opacity', 0.5);

    // Hover overlay
    const hoverGroup = g.append('g').attr('class', 'hover-group').style('pointer-events', 'none');
    const hoverLine = hoverGroup.append('line')
      .attr('stroke', '#0ea5e9')
      .attr('stroke-width', 2)
      .attr('opacity', 0);

    const hoverCircles = {};
    this.fuels.forEach(fuel => {
      hoverCircles[fuel] = hoverGroup.append('circle')
        .attr('fill', this.colorScale(fuel))
        .attr('r', 4)
        .attr('opacity', 0);
    });

    // Interactive overlay for hover
    const overlay = g.append('rect')
      .attr('width', w)
      .attr('height', h)
      .attr('fill', 'none')
      .attr('pointer-events', 'all');

    overlay
      .on('mousemove', (event) => {
        const [mx] = d3.pointer(event, overlay.node());
        const hour = Math.round(xScale.invert(mx));
        if (hour < 0 || hour > 23) return;

        const hourData = this.hours[hour];
        const stackedHour = this.stackedData[hour];

        // Show hover line
        hoverLine
          .attr('x1', xScale(hour))
          .attr('x2', xScale(hour))
          .attr('y1', 0)
          .attr('y2', h)
          .attr('opacity', 1);

        // Update hover circles and show tooltip
        let tooltipHTML = `<strong>Hour ${hour}:00</strong><br>`;
        let totalGen = 0;
        this.fuels.forEach(fuel => {
          if (this.activeFuels.has(fuel)) {
            const val = hourData[fuel] || 0;
            totalGen += Math.max(0, val);
            hoverCircles[fuel]
              .attr('cx', xScale(hour))
              .attr('cy', yScale(stackedHour[`${fuel}_1`]))
              .attr('opacity', val > 0 ? 0.8 : 0);

            if (val > 0 || fuel === 'storage_net' || fuel === 'imports') {
              const label = fuel
                .replace('_', '-')
                .replace(/^\w/, c => c.toUpperCase());
              tooltipHTML += `${label}: ${formatMW(val)}<br>`;
            }
          }
        });

        tooltipHTML += `<strong>Demand: ${formatMW(hourData.demand_mw)}</strong><br>`;
        tooltipHTML += `<strong>Price: ${formatPrice(hourData.price_per_mwh)}</strong>`;

        this.tooltip.show(tooltipHTML, event);
      })
      .on('mouseleave', () => {
        hoverLine.attr('opacity', 0);
        Object.values(hoverCircles).forEach(circle => circle.attr('opacity', 0));
        this.tooltip.hide();
      });

    // Legend
    this.renderLegend(svg, width, height);
  }

  renderLegend(svg, width, height) {
    const legendX = width - 220;
    const legendY = 20;

    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${legendX},${legendY})`);

    // Legend background
    legend.append('rect')
      .attr('width', 200)
      .attr('height', this.fuels.length * 28 + 10)
      .attr('fill', 'white')
      .attr('fill-opacity', 0.95)
      .attr('stroke', '#d4d8e0')
      .attr('rx', 6);

    // Title
    legend.append('text')
      .attr('x', 8)
      .attr('y', 20)
      .style('font-size', '0.85rem')
      .style('font-weight', '700')
      .style('fill', '#1a2744')
      .text('Fuel Type');

    // Legend items
    this.fuels.forEach((fuel, idx) => {
      const y = 35 + idx * 24;
      const item = legend.append('g')
        .attr('class', `legend-item legend-item-${fuel}`)
        .attr('transform', `translate(0,${y})`)
        .style('cursor', 'pointer');

      // Swatch
      item.append('rect')
        .attr('x', 8)
        .attr('y', 0)
        .attr('width', 12)
        .attr('height', 12)
        .attr('fill', this.colorScale(fuel))
        .attr('rx', 2);

      // Label
      item.append('text')
        .attr('x', 28)
        .attr('y', 10)
        .style('font-size', '0.9rem')
        .style('fill', '#1e293b')
        .text(fuel.replace('_', ' ').replace(/^\w/, c => c.toUpperCase()));

      // Click to toggle
      item.on('click', () => {
        this.toggleFuel(fuel);
      });
    });
  }

  toggleFuel(fuel) {
    if (this.activeFuels.has(fuel)) {
      this.activeFuels.delete(fuel);
    } else {
      this.activeFuels.add(fuel);
    }
    this.prepareData();
    // Trigger redraw via ResizeObserver pattern (or manual redraw)
    const w = this.container.clientWidth;
    const h = this.container.clientHeight || Math.round(w * 0.5);
    this.draw(w, h);
  }
}

/**
 * Wire up the fuel toggle buttons and hour slider
 */
function setupControls(chart, container) {
  const fuelToggle = document.getElementById('fuelToggle');
  const hourSlider = document.getElementById('hourSlider');
  const hourLabel = document.getElementById('hourLabel');

  if (fuelToggle) {
    fuelToggle.querySelectorAll('.btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const fuel = btn.dataset.fuel;
        if (fuel === '*') {
          // Toggle all fuels
          const allBtns = Array.from(fuelToggle.querySelectorAll('.btn[data-fuel!="*"]'));
          const allActive = allBtns.every(b => b.classList.contains('active'));
          allBtns.forEach(b => {
            const f = b.dataset.fuel;
            if (allActive) {
              chart.activeFuels.delete(f);
              b.classList.remove('active');
            } else {
              chart.activeFuels.add(f);
              b.classList.add('active');
            }
          });
          btn.classList.toggle('active', !allActive);
          chart.prepareData();
          const w = container.clientWidth;
          const h = container.clientHeight || Math.round(w * 0.5);
          chart.draw(w, h);
        } else {
          chart.toggleFuel(fuel);
          btn.classList.toggle('active');
        }
      });
    });
  }

  if (hourSlider) {
    const hours = ['Midnight', '1 AM', '2 AM', '3 AM', '4 AM', '5 AM', '6 AM', '7 AM', '8 AM', '9 AM', '10 AM', '11 AM',
      'Noon', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM', '10 PM', '11 PM'];
    hourSlider.addEventListener('input', (e) => {
      const hour = parseInt(e.target.value, 10);
      if (hourLabel) hourLabel.textContent = hours[hour];
      chart.currentHour = hour;
    });
  }
}

export { Dispatch24hChart };
