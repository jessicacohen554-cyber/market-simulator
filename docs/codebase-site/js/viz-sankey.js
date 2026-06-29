/**
 * viz-sankey.js — V10 Energy Balance Sankey Diagram
 * D3 + d3-sankey visualization of one zone's hourly energy balance.
 * Data from data/energy-balance-sankey.json.
 */
(function () {
  'use strict';

  /* Observatory color map for node types */
  const NODE_COLORS = {
    nuclear:     '#6366F1',
    coal:        '#374151',
    gas_cc:      '#6B7280',
    gas_ct:      '#9CA3AF',
    wind:        '#22C55E',
    solar:       '#F59E0B',
    hydro:       '#0EA5E9',
    storage_dis: '#E67E22',
    imports:     '#14B8A6',
    demand:      '#1A2744',
    exports:     '#2DD4BF',
    storage_chg: '#D97706',
    dump:        '#DC2626',
  };

  const FONT = "'DM Sans', sans-serif";
  const FONT_HEADING = "'Plus Jakarta Sans', sans-serif";

  /* ── Public API ────────────────────────────────────────────────────────── */
  window.VizSankey = { init };

  function init(containerId, dataPath) {
    const container = document.getElementById(containerId);
    if (!container) return;

    /* Load data, then render */
    fetch(dataPath || 'data/energy-balance-sankey.json')
      .then(r => r.json())
      .then(data => {
        render(container, data);
        if ('ResizeObserver' in window) {
          let raf;
          const ro = new ResizeObserver(() => {
            cancelAnimationFrame(raf);
            raf = requestAnimationFrame(() => render(container, data));
          });
          ro.observe(container);
        }
      })
      .catch(err => {
        container.innerHTML = '<p style="color:#94A3B8;padding:24px;text-align:center;">Could not load Sankey data.</p>';
        console.warn('VizSankey:', err);
      });
  }

  /* ── Tooltip ────────────────────────────────────────────────────────────── */
  function getTooltip() {
    let el = document.getElementById('sankey-tt');
    if (!el) {
      el = document.createElement('div');
      el.id = 'sankey-tt';
      el.style.cssText = [
        'position:fixed;pointer-events:none;z-index:9999;',
        'background:rgba(10,18,38,.96);color:#fff;',
        'border:1px solid rgba(255,255,255,.14);border-radius:10px;',
        'padding:10px 14px;font-size:.75rem;line-height:1.55;',
        'box-shadow:0 8px 24px rgba(0,0,0,.45);max-width:240px;',
        'opacity:0;transition:opacity 140ms ease;',
      ].join('');
      document.body.appendChild(el);
    }
    return el;
  }

  function showTip(tt, html, event) {
    tt.innerHTML = html;
    tt.style.opacity = '1';
    moveTip(tt, event);
  }
  function moveTip(tt, event) {
    const m = 14, tw = tt.offsetWidth, th = tt.offsetHeight;
    const vw = window.innerWidth, vh = window.innerHeight;
    let left = event.clientX + m, top = event.clientY + m;
    if (left + tw > vw - 8) left = event.clientX - tw - m;
    if (top  + th > vh - 8) top  = event.clientY - th - m;
    tt.style.left = Math.max(8, left) + 'px';
    tt.style.top  = Math.max(8, top)  + 'px';
  }
  function hideTip(tt) { tt.style.opacity = '0'; }

  /* ── Render ─────────────────────────────────────────────────────────────── */
  function render(container, data) {
    container.innerHTML = '';

    const W     = container.clientWidth  || 720;
    const H     = Math.min(520, Math.max(360, W * 0.55));
    const pad   = { top: 24, right: 20, bottom: 24, left: 20 };
    const inner = { w: W - pad.left - pad.right, h: H - pad.top - pad.bottom };

    /* ── Prepare nodes & links for d3-sankey ─────────────────────────────── */
    /* Filter out zero-value links to avoid empty flows */
    const rawLinks = data.links.filter(lk => lk.value > 0);

    /* Build node index by id */
    const nodeById = {};
    data.nodes.forEach((n, i) => { nodeById[n.id] = i; });

    /* Some links in the JSON may reference nodes not in nodes array; guard. */
    const validLinks = rawLinks.filter(lk =>
      nodeById[lk.source] !== undefined && nodeById[lk.target] !== undefined
    );

    if (validLinks.length === 0) {
      container.innerHTML = '<p style="color:#94A3B8;padding:24px;text-align:center;">No valid Sankey links.</p>';
      return;
    }

    const nodesForSankey = data.nodes.map(n => ({ ...n }));
    const linksForSankey = validLinks.map(lk => ({
      source: nodeById[lk.source],
      target: nodeById[lk.target],
      value:  lk.value,
      _src:   lk.source,
      _tgt:   lk.target,
    }));

    /* Remove nodes not referenced by any link */
    const activeNodeIds = new Set();
    linksForSankey.forEach(lk => {
      activeNodeIds.add(lk.source);
      activeNodeIds.add(lk.target);
    });
    const activeNodes = nodesForSankey.filter((_, i) => activeNodeIds.has(i));

    /* Remap indices after filtering */
    const remapOld = {};
    nodesForSankey.forEach((n, oldIdx) => {
      const newIdx = activeNodes.findIndex(an => an.id === n.id);
      if (newIdx >= 0) remapOld[oldIdx] = newIdx;
    });

    const finalLinks = linksForSankey
      .filter(lk => remapOld[lk.source] !== undefined && remapOld[lk.target] !== undefined)
      .map(lk => ({ ...lk, source: remapOld[lk.source], target: remapOld[lk.target] }));

    /* Run d3-sankey layout */
    if (typeof d3 === 'undefined' || typeof d3.sankey === 'undefined') {
      container.innerHTML = '<p style="color:#94A3B8;padding:24px;text-align:center;">d3-sankey plugin not loaded.</p>';
      return;
    }

    const sankeyLayout = d3.sankey()
      .nodeWidth(18)
      .nodePadding(12)
      .extent([[pad.left, pad.top], [W - pad.right, H - pad.bottom]]);

    let graph;
    try {
      graph = sankeyLayout({
        nodes: activeNodes.map(n => ({ ...n })),
        links: finalLinks.map(lk => ({ ...lk })),
      });
    } catch (e) {
      container.innerHTML = '<p style="color:#94A3B8;padding:24px;text-align:center;">Sankey layout error.</p>';
      console.warn('VizSankey layout error:', e);
      return;
    }

    /* ── SVG ────────────────────────────────────────────────────────────── */
    const svg = d3.select(container)
      .append('svg')
      .attr('viewBox', `0 0 ${W} ${H}`)
      .attr('width', '100%')
      .attr('height', H)
      .style('display', 'block')
      .attr('aria-label', `Energy balance Sankey for ${data.zone} zone, hour ${data.hour}`);

    /* White background */
    svg.append('rect').attr('width', W).attr('height', H).attr('fill', '#fff');

    const tt = getTooltip();
    const linkG = svg.append('g').attr('class', 'sankey-links');
    const nodeG = svg.append('g').attr('class', 'sankey-nodes');

    /* ── Links ───────────────────────────────────────────────────────────── */
    linkG.selectAll('path')
      .data(graph.links)
      .join('path')
      .attr('d', d3.sankeyLinkHorizontal())
      .attr('stroke-width', d => Math.max(1, d.width))
      .attr('stroke', d => {
        const srcId = d.source.id;
        return d3.color(NODE_COLORS[srcId] || '#94A3B8').copy({ opacity: 0 }) + '';  // transparent stroke
      })
      .attr('fill', 'none')
      .attr('stroke', d => {
        const c = d3.color(NODE_COLORS[d.source.id] || '#94A3B8');
        return c ? c.formatHex() : '#94A3B8';
      })
      .attr('opacity', 0.35)
      .on('mouseover', function (event, d) {
        d3.select(this).attr('opacity', 0.65);
        const mw = d.value.toLocaleString();
        showTip(tt, `
          <div style="font-family:${FONT_HEADING};font-weight:700;font-size:.8rem;margin-bottom:5px;">
            ${d.source.label} → ${d.target.label}
          </div>
          <div><span style="opacity:.6;">Flow:</span> <strong>${mw} MW</strong></div>
          <div style="opacity:.6;margin-top:3px;">${((d.value / data.demand_mw) * 100).toFixed(1)}% of total load</div>
        `, event);
      })
      .on('mousemove', e => moveTip(tt, e))
      .on('mouseleave', function () {
        d3.select(this).attr('opacity', 0.35);
        hideTip(tt);
      });

    /* ── Nodes ───────────────────────────────────────────────────────────── */
    const node = nodeG.selectAll('g')
      .data(graph.nodes)
      .join('g')
      .attr('class', 'sankey-node')
      .style('cursor', 'default');

    node.append('rect')
      .attr('x', d => d.x0)
      .attr('y', d => d.y0)
      .attr('height', d => Math.max(1, d.y1 - d.y0))
      .attr('width', d => d.x1 - d.x0)
      .attr('fill', d => NODE_COLORS[d.id] || '#94A3B8')
      .attr('rx', 2)
      .on('mouseover', function (event, d) {
        d3.select(this).attr('opacity', 0.85);
        const inflow  = graph.links.filter(l => l.target === d).reduce((s, l) => s + l.value, 0);
        const outflow = graph.links.filter(l => l.source === d).reduce((s, l) => s + l.value, 0);
        const val = Math.max(inflow, outflow);
        showTip(tt, `
          <div style="font-family:${FONT_HEADING};font-weight:700;font-size:.8rem;margin-bottom:5px;color:${NODE_COLORS[d.id] || '#fff'};">${d.label}</div>
          <div><span style="opacity:.6;">Value:</span> <strong>${val.toLocaleString()} MW</strong></div>
          <div><span style="opacity:.6;">Share:</span> ${((val / data.demand_mw) * 100).toFixed(1)}% of load</div>
        `, event);
      })
      .on('mousemove', e => moveTip(tt, e))
      .on('mouseleave', function () {
        d3.select(this).attr('opacity', 1);
        hideTip(tt);
      });

    /* Node labels */
    node.append('text')
      .attr('x', d => d.x0 < W / 2 ? d.x1 + 6 : d.x0 - 6)
      .attr('y', d => (d.y0 + d.y1) / 2)
      .attr('text-anchor', d => d.x0 < W / 2 ? 'start' : 'end')
      .attr('dominant-baseline', 'middle')
      .attr('font-family', FONT)
      .attr('font-size', Math.max(9, Math.min(12, W / 70)))
      .attr('fill', '#1E293B')
      .attr('font-weight', d => d.id === 'demand' ? '700' : '400')
      .text(d => {
        const inflow  = graph.links.filter(l => l.target === d).reduce((s, l) => s + l.value, 0);
        const outflow = graph.links.filter(l => l.source === d).reduce((s, l) => s + l.value, 0);
        const val = Math.max(inflow, outflow);
        if (val >= 1000) return `${d.label} ${(val / 1000).toFixed(1)} GW`;
        return `${d.label} ${Math.round(val)} MW`;
      });

    /* Zone / hour annotation */
    svg.append('text')
      .attr('x', W - pad.right)
      .attr('y', H - 8)
      .attr('text-anchor', 'end')
      .attr('font-family', FONT)
      .attr('font-size', 10)
      .attr('fill', '#94A3B8')
      .text(`${data.zone} zone · Hour ${data.hour}:00 · ${data.season ?? ''} · LMP: $${(data.summary?.lmp_per_mwh ?? 0).toFixed(1)}/MWh`);
  }
})();
