/**
 * iso-configs-table.js — ISO Configuration renderer
 *
 * Loads iso-topologies.json and renders:
 * - Collapsible per-ISO sections
 * - Zone table (name, load share %)
 * - Transfer link table (from, to, TTC)
 * - Interface limits if present
 * - VOLL
 */

(function () {
  'use strict';

  const ISO_COLORS = {
    ERCOT: '#22C55E',
    CAISO: '#F59E0B',
    PJM: '#0EA5E9',
    MISO: '#F97316',
    NYISO: '#E91E63',
    NEISO: '#9C27B0',
    SPP: '#14B8A6',
    NWPP: '#65A30D',
    SOCO: '#6366F1',
  };

  const ISO_DESCRIPTIONS = {
    ERCOT: 'Seven zones with major congestion interfaces (WESTEX, PNHNDL, NE_LOB); calibrated reference.',
    CAISO: 'Five load zones north to south (NP15, ZP26, SP15_rest, LA_BASIN, SDGE) plus the WECC import node.',
    PJM: 'Eight LDA zones capturing west-to-east price gradients and eastern load pockets.',
    MISO: 'Six LRZ-union zones with per-zone CIL/CEL limits and the asymmetric RDT path to MISO-South.',
    NYISO: 'Five zones with downstate import constraints (Progressive eastern islanding).',
    NEISO: 'Four load zones plus the HQ import node for the Quebec interconnection.',
    SPP: 'Two zones along the North–South seam; the N↔S TTC is 3,400 MW — the rule-14 reconciled corridor limit derived from SPP’s own published flowgate limits (FINDING-spp-53).',
    NWPP: 'Five zones over ~17 balancing authorities — a POOL, not an ISO. NW (BPAT + Puget-Sound/mid-Columbia), OR (PGE + PacifiCorp West), INLAND (IPCO/AVA/NWMT/WAUW), EAST (PacifiCorp East) and SNV (NV Energy). Six WECC path limits are Tier-1/Tier-2 cited; the NW↔OR link is a Tier-3 documented-absence placeholder that cannot bind.',
    SOCO: 'Three geographic zones over a SINGLE balancing authority — Southern Company Services – Trans, not an ISO: cost-based pooled dispatch under the Intercompany Interchange Contract, with no day-ahead market, no LMP and no capacity auction. AL (Alabama plus six SERC Florida-panhandle plants), GA (Georgia) and MS (Mississippi, which reaches the system through Alabama). Both links are Tier-3 documented-absence placeholders that cannot bind — the Operating Companies publish no internal interface rating, so each TTC is the smaller side’s EIA-860 winter capability and the real value is lever SOCO-54. The load shares are an EIA-860 fleet-MW fallback, not load shares (lane SOCO-32 replaces them). VOLL is $61,900/MWh, an LBNL/DOE ICE-Calculator-2 customer-mix derivation, not the $2,000 the other non-ERCOT regions carry.',
  };

  /**
   * Fetch and parse iso-topologies.json.
   */
  async function loadIsoData() {
    try {
      const response = await fetch('data/iso-topologies.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (e) {
      console.error('Failed to load ISO topologies:', e);
      return null;
    }
  }

  /**
   * Format a percentage from 0–1.
   */
  function formatPct(val) {
    return (val * 100).toFixed(1);
  }

  /**
   * Build a zone table for an ISO.
   */
  function renderZoneTable(zones) {
    const totalShare = zones.reduce((sum, z) => sum + z.load_share, 0);
    let html = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Zone Name</th>
            <th style="text-align: right;">Load Share</th>
          </tr>
        </thead>
        <tbody>
    `;

    zones.forEach((zone) => {
      html += `
        <tr>
          <td>${zone.name}</td>
          <td style="text-align: right;">${formatPct(zone.load_share)}%</td>
        </tr>
      `;
    });

    html += `
        </tbody>
      </table>
    `;

    return html;
  }

  /**
   * Build a transfer links table for an ISO.
   */
  function renderLinksTable(links) {
    if (links.length === 0) {
      return '<p style="color: var(--text-muted); font-size: 0.9rem;">No transfer links defined.</p>';
    }

    let html = `
      <table class="data-table">
        <thead>
          <tr>
            <th>From Zone</th>
            <th>To Zone</th>
            <th style="text-align: right;">TTC (MW)</th>
            <th>Direction</th>
          </tr>
        </thead>
        <tbody>
    `;

    links.forEach((link) => {
      const direction = link.bidirectional ? 'Bidirectional' : 'One-way';
      html += `
        <tr>
          <td>${link.from}</td>
          <td>${link.to}</td>
          <td style="text-align: right;"><strong>${link.ttc_mw.toLocaleString()}</strong></td>
          <td><span class="badge" style="background: ${link.bidirectional ? '#10B981' : '#F59E0B'}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600;">${direction}</span></td>
        </tr>
      `;
    });

    html += `
        </tbody>
      </table>
    `;

    return html;
  }

  /**
   * Build interface limits table if present.
   */
  function renderInterfaceLimits(limits) {
    if (!limits || limits.length === 0) {
      return '';
    }

    let html = '<h4>Aggregate Interface Limits</h4>';
    html += `
      <table class="data-table">
        <thead>
          <tr>
            <th>Interface Name</th>
            <th>Linked Paths</th>
            <th style="text-align: right;">Aggregate Cap (MW)</th>
          </tr>
        </thead>
        <tbody>
    `;

    limits.forEach((limit) => {
      const paths = limit.links.map((pair) => `${pair[0]} → ${pair[1]}`).join('; ');
      html += `
        <tr>
          <td><strong>${limit.name}</strong></td>
          <td>${paths}</td>
          <td style="text-align: right;"><strong>${limit.cap_mw.toLocaleString()}</strong></td>
        </tr>
      `;
    });

    html += `
        </tbody>
      </table>
    `;

    return html;
  }

  /**
   * Render a single ISO section.
   */
  function renderIsoSection(isoName, isoData) {
    const color = ISO_COLORS[isoName] || '#6B7280';
    const description = ISO_DESCRIPTIONS[isoName] || '';

    const html = `
      <div class="iso-section">
        <div class="iso-header" data-iso="${isoName}">
          <span class="iso-badge" style="background: ${color};">${isoName}</span>
          <div>
            <strong>${isoName}</strong>
            <p style="margin: 0; font-size: 0.85rem; color: var(--text-muted);">${description}</p>
          </div>
        </div>

        <div class="iso-content" data-iso="${isoName}">
          <div>
            <h4>Zones (${isoData.n_zones})</h4>
            ${renderZoneTable(isoData.zones)}
          </div>

          <div>
            <h4>Transfer Links (${isoData.n_links})</h4>
            ${renderLinksTable(isoData.links)}
          </div>

          ${renderInterfaceLimits(isoData.interface_limits)}

          <div>
            <h4>Economic Parameters</h4>
            <table class="data-table" style="width: auto;">
              <tbody>
                <tr>
                  <td><strong>VOLL ($/MWh)</strong></td>
                  <td style="text-align: right;"><strong>${isoData.voll.toLocaleString()}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;

    return html;
  }

  /**
   * Initialize ISO sections.
   */
  async function init() {
    const container = document.querySelector('#isoConfigs');
    if (!container) return;

    const data = await loadIsoData();
    if (!data) {
      container.innerHTML = '<p style="color: var(--negative);">Failed to load ISO topology data.</p>';
      return;
    }

    let html = '';
    // Registration order of config/iso_configs._ISO_BUILDERS, which carries NINE
    // regions at 2026-09-16, all nine serialized in iso-topologies.json since
    // lane SOCO-34. Only the keys the data file actually carries render, so this
    // list stays fail-safe if a region is registered before it is serialized.
    const isoOrder = ['ERCOT', 'CAISO', 'PJM', 'MISO', 'NYISO', 'NEISO', 'SPP', 'NWPP', 'SOCO'];
    isoOrder.forEach((iso) => {
      if (data[iso]) {
        html += renderIsoSection(iso, data[iso]);
      }
    });

    container.innerHTML = html;

    // Add toggle handlers
    document.querySelectorAll('.iso-header').forEach((header) => {
      header.addEventListener('click', () => {
        const isoName = header.dataset.iso;
        const content = document.querySelector(`.iso-content[data-iso="${isoName}"]`);
        if (content) {
          header.classList.toggle('expanded');
          content.classList.toggle('show');
        }
      });
    });
  }

  // Run on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
