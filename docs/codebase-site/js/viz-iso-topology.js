/**
 * viz-iso-topology.js — V14: Interactive region topology network graph
 *
 * Renders a D3 force-directed graph for each ISO showing zones (circles)
 * and transmission links (lines). Tab bar switches between ISOs.
 *
 * Data: data/iso-topologies.json
 * Mount: #viz-iso-topology
 */

import { addTooltip, cssColor } from './chart-utils.js';

const DATA_URL = 'data/iso-topologies.json';
const MOUNT_ID = 'viz-iso-topology';

/* Registration order of config/iso_configs._ISO_BUILDERS, which carries NINE
   regions at this writing (2026-09-14). SOCO registered the same day as NWPP
   but has no block in iso-topologies.json yet — buildTabBar skips any key the
   data file does not carry, so listing it here early would be harmless; it is
   left to the SOCO desk's own lane rather than pre-empted. */
const ISO_ORDER = ['ERCOT', 'CAISO', 'PJM', 'MISO', 'NYISO', 'NEISO', 'SPP', 'NWPP'];

/* ISO accent colors (matches CSS --iso-* vars) */
const ISO_COLORS = {
  ERCOT: '#22C55E',
  CAISO: '#F59E0B',
  PJM:   '#0EA5E9',
  MISO:  '#F97316',
  NYISO: '#E91E63',
  NEISO: '#9C27B0',
  SPP:   '#14B8A6',
  NWPP:  '#65A30D',
};

/* Import-node zone names (styled differently) */
const IMPORT_NODES = new Set(['WECC_import', 'HQ_import', 'Panhandle']);

/**
 * Geographic seed positions (x/y, 0-1 range) for cleaner initial layouts.
 * Force simulation will settle from these.
 */
const GEO_HINTS = {
  ERCOT: {
    West:          [0.12, 0.42],
    Panhandle:     [0.22, 0.08],
    North:         [0.42, 0.28],
    Northeast:     [0.72, 0.18],
    Houston:       [0.62, 0.72],
    South_Central: [0.30, 0.68],
    South:         [0.42, 0.90],
  },
  CAISO: {
    NP15:         [0.45, 0.12],
    ZP26:         [0.45, 0.50],
    /* SP15 was split into the three LCT local areas (caiso-172); placed
       north-to-south down the SP26 footprint. SP15_rest is the gateway the
       Path 26 and Path 46 (West of the River) imports land on. */
    SP15_rest:    [0.42, 0.70],
    LA_BASIN:     [0.60, 0.86],
    SDGE:         [0.70, 0.98],
    WECC_import:  [0.10, 0.46],
  },
  PJM: {
    PJM_ComEd:      [0.08, 0.20],
    PJM_AEP_Ohio:   [0.28, 0.42],
    PJM_ATSI:       [0.36, 0.20],
    PJM_West_APS:   [0.48, 0.62],
    PJM_Central_PA: [0.58, 0.22],
    PJM_Dominion:   [0.68, 0.70],
    PJM_EMAAC:      [0.78, 0.32],
    PJM_SWMAAC:     [0.72, 0.58],
  },
  /* Six LRZ-union zones; the former 3-zone North/Central/South build was a
     copperplate and is gone. Placed on the real state geography named in
     iso_configs._miso_config: West = MN/ND/SD/MT, Plains = IA/MO,
     Illinois = IL, Indiana = IN/KY, East = WI/MI, South = AR/LA/MS/E-TX
     (electrically separate, reached only over the RDT contract path). */
  MISO: {
    'MISO-West':     [0.16, 0.10],
    'MISO-East':     [0.74, 0.18],
    'MISO-Plains':   [0.22, 0.42],
    'MISO-Illinois': [0.46, 0.42],
    'MISO-Indiana':  [0.70, 0.52],
    'MISO-South':    [0.40, 0.88],
  },
  NYISO: {
    Upstate_West:   [0.08, 0.32],
    Capital_Hudson: [0.38, 0.32],
    Lower_Hudson:   [0.58, 0.52],
    NYC:            [0.72, 0.62],
    Long_Island:    [0.90, 0.55],
  },
  NEISO: {
    Connecticut:  [0.62, 0.88],
    Boston:       [0.78, 0.58],
    Central:      [0.46, 0.44],
    North:        [0.28, 0.12],
    HQ_import:    [0.08, 0.08],
  },
  /* Five zones over ~17 balancing authorities — NWPP is a POOL, not an ISO, so
     each zone is a BA group rather than a control area. Placed on the real
     geography named in iso_configs._nwpp_config: NW = BPAT/PSEI/SCL/TPWR plus
     the mid-Columbia PUDs, OR = PGE/PACW down the Willamette, INLAND =
     IPCO/AVA/NWMT/WAUW, EAST = PACE (UT/WY/SE Idaho), SNV = NEVP (all of
     Nevada, but load-weighted to the south). */
  NWPP: {
    'NWPP-NW':     [0.16, 0.14],
    'NWPP-OR':     [0.12, 0.46],
    'NWPP-INLAND': [0.46, 0.34],
    'NWPP-EAST':   [0.82, 0.44],
    'NWPP-SNV':    [0.54, 0.90],
  },
};

/* Clean display names */
function shortName(raw) {
  return raw
    .replace(/^PJM_/, '')
    .replace(/^MISO-/, '')
    .replace(/_import$/, ' (import)')
    .replace(/_/g, ' ');
}

async function init() {
  const container = document.getElementById(MOUNT_ID);
  if (!container) return;

  let data;
  try {
    const resp = await fetch('data/iso-topologies.json');
    data = await resp.json();
  } catch (e) {
    container.innerHTML = '<p style="color:#94A3B8;padding:2rem;text-align:center">Could not load topology data.</p>';
    return;
  }

  buildTabBar(container, data);
  renderISO('ERCOT', data['ERCOT'], container);
}

/* ---------------------------------------------------------------------------
   Tab bar
   --------------------------------------------------------------------------- */
function buildTabBar(container, data) {
  const tabBar = container.querySelector('.iso-tab-bar');
  if (!tabBar) return;

  ISO_ORDER.forEach((iso, i) => {
    if (!data[iso]) return;
    const btn = document.createElement('button');
    btn.className = 'tabs__tab' + (i === 0 ? ' active' : '');
    btn.dataset.iso = iso;
    btn.textContent = iso;
    btn.setAttribute('aria-selected', i === 0 ? 'true' : 'false');
    btn.style.setProperty('--iso-accent', ISO_COLORS[iso]);
    if (i === 0) {
      btn.style.color = ISO_COLORS[iso];
      btn.style.borderBottomColor = ISO_COLORS[iso];
    }

    btn.addEventListener('click', () => {
      tabBar.querySelectorAll('.tabs__tab').forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
        t.style.color = '';
        t.style.borderBottomColor = '';
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      btn.style.color = ISO_COLORS[iso];
      btn.style.borderBottomColor = ISO_COLORS[iso];
      renderISO(iso, data[iso], container);
    });

    tabBar.appendChild(btn);
  });
}

/* ---------------------------------------------------------------------------
   ISO topology renderer
   --------------------------------------------------------------------------- */
function renderISO(isoName, isoData, container) {
  const svgContainer = container.querySelector('.iso-graph-area');
  if (!svgContainer) return;

  svgContainer.innerHTML = '';

  const color = ISO_COLORS[isoName] || '#0EA5E9';
  const zones = isoData.zones || [];
  const links = isoData.links || [];
  const hints = GEO_HINTS[isoName] || {};

  const W = svgContainer.clientWidth || 720;
  const H = Math.min(420, Math.max(300, W * 0.48));
  const PAD = 60;

  /* Build node/link objects */
  const nodes = zones.map(z => {
    const hint = hints[z.name];
    return {
      id: z.name,
      label: shortName(z.name),
      loadShare: z.load_share,
      isImport: IMPORT_NODES.has(z.name),
      x: hint ? PAD + hint[0] * (W - 2 * PAD) : W / 2,
      y: hint ? PAD + hint[1] * (H - 2 * PAD) : H / 2,
    };
  });

  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  const simLinks = links.map(l => ({
    source: l.from,
    target: l.to,
    ttc: l.ttc_mw,
    bidirectional: l.bidirectional,
    label: `${(l.ttc_mw / 1000).toFixed(1)} GW`,
  }));

  /* Radius scale: load carriers get 20–48px radius; import nodes fixed small */
  const maxShare = Math.max(...zones.map(z => z.load_share));
  function nodeRadius(d) {
    if (d.isImport) return 14;
    if (d.loadShare === 0) return 14;
    return 18 + (d.loadShare / maxShare) * 28;
  }

  /* Stroke width for links: TTC 1 GW → 1.5px, 12 GW → 7px */
  function linkWidth(d) {
    return 1.5 + (d.ttc / 12000) * 5.5;
  }

  const svg = d3.select(svgContainer)
    .append('svg')
    .attr('width', W)
    .attr('height', H)
    .attr('viewBox', `0 0 ${W} ${H}`)
    .style('display', 'block');

  /* Defs: import node dash pattern + arrowheads */
  const defs = svg.append('defs');
  defs.append('marker')
    .attr('id', `arrow-${isoName}`)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('refX', 5)
    .attr('refY', 3)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,0 L0,6 L6,3 Z')
    .attr('fill', color)
    .attr('opacity', 0.5);

  /* D3 force simulation */
  const linkForce = d3.forceLink(simLinks)
    .id(d => d.id)
    .distance(d => {
      /* Longer distance for high-TTC links */
      return 80 + (d.ttc / 12000) * 60;
    })
    .strength(0.6);

  const sim = d3.forceSimulation(nodes)
    .force('link', linkForce)
    .force('charge', d3.forceManyBody().strength(-320))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collide', d3.forceCollide(d => nodeRadius(d) + 10))
    .force('x', d3.forceX(d => {
      const hint = hints[d.id];
      return hint ? PAD + hint[0] * (W - 2 * PAD) : W / 2;
    }).strength(0.25))
    .force('y', d3.forceY(d => {
      const hint = hints[d.id];
      return hint ? PAD + hint[1] * (H - 2 * PAD) : H / 2;
    }).strength(0.25));

  /* Link group (below nodes) */
  const linkGroup = svg.append('g').attr('class', 'links');

  const linkSel = linkGroup.selectAll('line')
    .data(simLinks)
    .join('line')
    .attr('stroke', color)
    .attr('stroke-opacity', 0.45)
    .attr('stroke-width', d => linkWidth(d))
    .attr('stroke-dasharray', d => d.bidirectional ? null : '6 3');

  /* Link TTC labels */
  const linkLabelSel = svg.append('g').attr('class', 'link-labels')
    .selectAll('text')
    .data(simLinks)
    .join('text')
    .attr('font-size', '9px')
    .attr('font-family', 'DM Sans, sans-serif')
    .attr('fill', color)
    .attr('opacity', 0.70)
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .text(d => d.label);

  /* Node group */
  const nodeGroup = svg.append('g').attr('class', 'nodes');

  const nodeSel = nodeGroup.selectAll('g')
    .data(nodes)
    .join('g')
    .attr('class', 'node')
    .style('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on('end', (event, d) => {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null; d.fy = null;
      })
    );

  /* Zone circle */
  nodeSel.append('circle')
    .attr('r', d => nodeRadius(d))
    .attr('fill', d => d.isImport ? 'transparent' : color)
    .attr('fill-opacity', d => d.isImport ? 0 : 0.18)
    .attr('stroke', color)
    .attr('stroke-width', d => d.isImport ? 1.5 : 2)
    .attr('stroke-dasharray', d => d.isImport ? '4 3' : null)
    .attr('stroke-opacity', 0.75);

  /* Zone label */
  nodeSel.append('text')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .attr('font-size', d => nodeRadius(d) < 20 ? '9px' : '10px')
    .attr('font-weight', '600')
    .attr('font-family', 'DM Sans, sans-serif')
    .attr('fill', color)
    .attr('fill-opacity', 0.90)
    .text(d => {
      const lbl = d.label;
      /* Truncate long labels */
      return lbl.length > 12 ? lbl.slice(0, 10) + '…' : lbl;
    });

  /* Tooltip */
  const tip = addTooltip('tooltip');

  nodeSel
    .on('mouseenter', (event, d) => {
      const connectedLinks = simLinks.filter(l =>
        l.source.id === d.id || l.target.id === d.id
      );
      const ttcSum = connectedLinks.reduce((s, l) => s + l.ttc, 0);

      let html = `<div class="tooltip__title">${d.id}</div>`;
      if (d.loadShare > 0) {
        html += `<div class="tooltip__row"><span class="tooltip__key">Load share</span><span class="tooltip__val">${(d.loadShare * 100).toFixed(1)}%</span></div>`;
      }
      if (d.isImport) {
        html += `<div class="tooltip__row"><span class="tooltip__key">Type</span><span class="tooltip__val">Import node</span></div>`;
      }
      html += `<div class="tooltip__row"><span class="tooltip__key">Links</span><span class="tooltip__val">${connectedLinks.length}</span></div>`;
      if (connectedLinks.length > 0) {
        html += `<div class="tooltip__row"><span class="tooltip__key">Total TTC</span><span class="tooltip__val">${(ttcSum / 1000).toFixed(1)} GW</span></div>`;
      }
      tip.show(html, event);
    })
    .on('mouseleave', () => tip.hide());

  linkSel
    .on('mouseenter', (event, d) => {
      const fromId = typeof d.source === 'object' ? d.source.id : d.source;
      const toId   = typeof d.target === 'object' ? d.target.id : d.target;
      let html = `<div class="tooltip__title">${fromId} → ${toId}</div>`;
      html += `<div class="tooltip__row"><span class="tooltip__key">TTC</span><span class="tooltip__val">${(d.ttc / 1000).toFixed(1)} GW</span></div>`;
      html += `<div class="tooltip__row"><span class="tooltip__key">Direction</span><span class="tooltip__val">${d.bidirectional ? 'Bidirectional' : 'One-way'}</span></div>`;
      tip.show(html, event);
    })
    .on('mouseleave', () => tip.hide());

  /* Simulation tick */
  sim.on('tick', () => {
    /* Clamp nodes to SVG bounds */
    nodes.forEach(d => {
      const r = nodeRadius(d);
      d.x = Math.max(r + PAD * 0.4, Math.min(W - r - PAD * 0.4, d.x));
      d.y = Math.max(r + PAD * 0.4, Math.min(H - r - PAD * 0.4, d.y));
    });

    linkSel
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    linkLabelSel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2);

    nodeSel.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  /* Stop sim after it settles (save CPU) */
  setTimeout(() => sim.stop(), 6000);

  /* Update ISO stat bar */
  updateStatBar(container, isoName, isoData);
}

function updateStatBar(container, isoName, isoData) {
  const statBar = container.querySelector('.iso-stat-bar');
  if (!statBar) return;

  const loadZones = (isoData.zones || []).filter(z => z.load_share > 0);
  const totalTTC = (isoData.links || []).reduce((s, l) => s + l.ttc_mw, 0);
  const hasInterface = isoData.interface_limits && isoData.interface_limits.length > 0;

  statBar.innerHTML = `
    <span><strong>${loadZones.length}</strong> load zones</span>
    <span><strong>${isoData.n_links}</strong> links</span>
    <span><strong>${(totalTTC / 1000).toFixed(0)} GW</strong> total TTC</span>
    ${hasInterface ? `<span><strong>${isoData.interface_limits.length}</strong> interface limit${isoData.interface_limits.length > 1 ? 's' : ''}</span>` : ''}
  `;
}

/* Boot */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
