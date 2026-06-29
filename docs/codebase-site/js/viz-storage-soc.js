/**
 * viz-storage-soc.js — V19 48-hour SOC trace with price overlay
 * Used on: capacity-evolution.html
 *
 * Dual-axis chart: SOC (MWh) for 4h and 8h batteries + LMP ($/MWh) overlay.
 * Shows charge/discharge cycling behavior over two summer peak days.
 */

import {
  responsiveChart,
  addTooltip,
  makeAxis,
  styleAxis,
  styleAxisDark,
  margin,
  formatPrice,
} from './chart-utils.js';

document.addEventListener('DOMContentLoaded', initStorageSoc);

async function initStorageSoc() {
  const container = document.getElementById('storage-soc-container');
  if (!container) return;

  let data;
  try {
    const res = await fetch('data/storage-soc-48h.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.error('Failed to load storage-soc data:', err);
    container.innerHTML = '<div style="padding:2rem;text-align:center;color:#666;">Unable to load data.</div>';
    return;
  }

  const tooltip = addTooltip('storage-soc-tooltip');
  const trace = data.hourly_trace;

  function draw(width, height) {
    d3.select(container).selectAll('svg').remove();

    const isDark = container.closest('.section-dark') !== null;
    const m = margin({ top: 16, right: 56, bottom: 44, left: 56 });
    const w = width - m.left - m.right;
    const h = height - m.top - m.bottom;

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('role', 'img')
      .attr('aria-label', '48-hour battery SOC trace with LMP overlay');

    const g = svg.append('g')
      .attr('transform', `translate(${m.left},${m.top})`);

    // Scales
    const xScale = d3.scaleLinear()
      .domain([1, 48])
      .range([0, w]);

    const socMax = d3.max(trace, d => Math.max(d.soc_4h_mwh, d.soc_8h_mwh)) * 1.1;
    const socScale = d3.scaleLinear()
      .domain([0, socMax])
      .range([h, 0]);

    const priceMax = d3.max(trace, d => d.lmp_per_mwh) * 1.1;
    const priceScale = d3.scaleLinear()
      .domain([0, priceMax])
      .range([h, 0]);

    // Grid
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(socScale).tickSize(-w).tickFormat('').ticks(5))
      .selectAll('line')
      .attr('stroke', isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)')
      .attr('stroke-dasharray', '3,3');
    g.select('.grid .domain').remove();

    // Day separator
    g.append('line')
      .attr('x1', xScale(24.5)).attr('x2', xScale(24.5))
      .attr('y1', 0).attr('y2', h)
      .attr('stroke', isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.10)')
      .attr('stroke-dasharray', '6,4');

    g.append('text')
      .attr('x', xScale(12)).attr('y', -4)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', isDark ? 'rgba(241,245,249,0.4)' : 'rgba(0,0,0,0.35)')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('Day 1 — Jul 15');

    g.append('text')
      .attr('x', xScale(36)).attr('y', -4)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', isDark ? 'rgba(241,245,249,0.4)' : 'rgba(0,0,0,0.35)')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('Day 2 — Jul 16');

    // Price area (background)
    const priceArea = d3.area()
      .x(d => xScale(d.hour))
      .y0(h)
      .y1(d => priceScale(d.lmp_per_mwh))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(trace)
      .attr('d', priceArea)
      .attr('fill', '#E91E63')
      .attr('fill-opacity', 0.06);

    // Price line
    const priceLine = d3.line()
      .x(d => xScale(d.hour))
      .y(d => priceScale(d.lmp_per_mwh))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(trace)
      .attr('d', priceLine)
      .attr('fill', 'none')
      .attr('stroke', '#E91E63')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.5)
      .attr('stroke-dasharray', '5,3');

    // SOC lines
    const socLine4h = d3.line()
      .x(d => xScale(d.hour))
      .y(d => socScale(d.soc_4h_mwh))
      .curve(d3.curveMonotoneX);

    const socLine8h = d3.line()
      .x(d => xScale(d.hour))
      .y(d => socScale(d.soc_8h_mwh))
      .curve(d3.curveMonotoneX);

    // 4h SOC area fill
    const soc4hArea = d3.area()
      .x(d => xScale(d.hour))
      .y0(h)
      .y1(d => socScale(d.soc_4h_mwh))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(trace)
      .attr('d', soc4hArea)
      .attr('fill', '#E67E22')
      .attr('fill-opacity', 0.08);

    g.append('path')
      .datum(trace)
      .attr('d', socLine4h)
      .attr('fill', 'none')
      .attr('stroke', '#E67E22')
      .attr('stroke-width', 2.5)
      .attr('stroke-linecap', 'round');

    g.append('path')
      .datum(trace)
      .attr('d', socLine8h)
      .attr('fill', 'none')
      .attr('stroke', '#0EA5E9')
      .attr('stroke-width', 2.5)
      .attr('stroke-linecap', 'round');

    // Axes
    const xAxis = makeAxis('x', xScale, {
      ticks: width < 500 ? 6 : 12,
      tickFormat: d => {
        const hr = ((d - 1) % 24);
        if (hr === 0) return '12AM';
        if (hr === 6) return '6AM';
        if (hr === 12) return '12PM';
        if (hr === 18) return '6PM';
        return '';
      },
    });
    const xG = g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(xAxis);
    isDark ? styleAxisDark(xG) : styleAxis(xG);

    // SOC y-axis (left)
    const yAxis = makeAxis('y', socScale, {
      ticks: 5,
      tickFormat: v => `${Math.round(v)} MWh`,
    });
    const yG = g.append('g').call(yAxis);
    isDark ? styleAxisDark(yG) : styleAxis(yG);

    // Price y-axis (right)
    const priceAxisFn = d3.axisRight(priceScale)
      .ticks(5)
      .tickFormat(v => `$${Math.round(v)}`);
    const priceG = g.append('g')
      .attr('transform', `translate(${w},0)`)
      .call(priceAxisFn);
    priceG.select('.domain').remove();
    priceG.selectAll('.tick line').remove();
    priceG.selectAll('text')
      .attr('fill', '#E91E63')
      .attr('font-size', '10px')
      .attr('font-family', "'DM Sans', sans-serif");

    // Axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -m.left + 14)
      .attr('x', -h / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', isDark ? 'rgba(241,245,249,0.5)' : '#566370')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('State of Charge (MWh)');

    g.append('text')
      .attr('transform', 'rotate(90)')
      .attr('y', -(w + m.right - 14))
      .attr('x', h / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', '#E91E63')
      .attr('font-family', "'DM Sans', sans-serif")
      .text('LMP ($/MWh)');

    // Hover
    const hoverLine = g.append('line')
      .attr('y1', 0).attr('y2', h)
      .attr('stroke', isDark ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.15)')
      .attr('stroke-width', 1)
      .style('display', 'none');

    const overlay = g.append('rect')
      .attr('width', w).attr('height', h)
      .attr('fill', 'none').attr('pointer-events', 'all');

    overlay
      .on('mousemove', (event) => {
        const [mx] = d3.pointer(event, overlay.node());
        const hr = Math.round(xScale.invert(mx));
        const d = trace.find(t => t.hour === hr);
        if (!d) return;

        hoverLine.attr('x1', xScale(hr)).attr('x2', xScale(hr)).style('display', null);

        const chg4 = d.charge_4h_mw > 0 ? `⚡ Charging ${d.charge_4h_mw} MW` : '';
        const dis4 = d.discharge_4h_mw > 0 ? `🔋 Discharging ${d.discharge_4h_mw} MW` : '';
        const chg8 = d.charge_8h_mw > 0 ? `⚡ Charging ${d.charge_8h_mw} MW` : '';
        const dis8 = d.discharge_8h_mw > 0 ? `🔋 Discharging ${d.discharge_8h_mw} MW` : '';

        tooltip.show(
          `<strong>${d.datetime}</strong><br>` +
          `<span style="color:#E91E63;">LMP: $${d.lmp_per_mwh}/MWh</span><br><br>` +
          `<span style="color:#E67E22;">■</span> 4h Battery: ${d.soc_4h_mwh} MWh` +
          (chg4 ? `<br>&nbsp;&nbsp;${chg4}` : '') +
          (dis4 ? `<br>&nbsp;&nbsp;${dis4}` : '') +
          `<br><span style="color:#0EA5E9;">■</span> 8h Battery: ${d.soc_8h_mwh} MWh` +
          (chg8 ? `<br>&nbsp;&nbsp;${chg8}` : '') +
          (dis8 ? `<br>&nbsp;&nbsp;${dis8}` : ''),
          event
        );
      })
      .on('mouseleave', () => {
        hoverLine.style('display', 'none');
        tooltip.hide();
      });
  }

  responsiveChart(container, (w, h) => draw(w, h));
}

export { initStorageSoc };
