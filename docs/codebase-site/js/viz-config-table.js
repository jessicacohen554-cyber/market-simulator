/**
 * viz-config-table.js — Config Reference table search & filter
 *
 * Provides:
 * - Real-time search across field name, type, default, and description
 * - Tier filter buttons to toggle visibility by Tier 0-3
 * - Expandable rows to show full descriptions
 * - Debounced search (200ms)
 */

(function () {
  'use strict';

  const DEBOUNCE_MS = 200;

  let configData = null;
  let activeSearch = '';
  let activeTiers = new Set([0, 1, 2, 3]);
  let searchTimeout = null;
  let expandedRows = new Set();

  /**
   * Load and parse the inline JSON config data.
   */
  function loadConfigData() {
    const script = document.querySelector('#configData');
    if (!script) {
      console.error('Config data script not found');
      return [];
    }
    try {
      return JSON.parse(script.textContent).fields;
    } catch (e) {
      console.error('Failed to parse config data:', e);
      return [];
    }
  }

  /**
   * Build tier badge HTML.
   */
  function tierBadge(tier) {
    const labels = ['Structural', 'Scenario', 'Expert', 'Calibration'];
    const label = labels[tier] || `Tier ${tier}`;
    return `<span class="tier-badge tier-${tier}">${label}</span>`;
  }

  /**
   * Check if a field matches the current search and tier filters.
   */
  function matches(field) {
    // Check tier filter
    if (!activeTiers.has(field.tier)) {
      return false;
    }

    // Check search term
    if (!activeSearch) {
      return true;
    }

    const term = activeSearch.toLowerCase();
    const searchable = [
      field.name,
      field.type,
      field.default,
      field.description,
    ].join(' ').toLowerCase();

    return searchable.includes(term);
  }

  /**
   * Render the config table with current filters applied.
   */
  function renderTable() {
    const tbody = document.querySelector('#configTableBody');
    const noResults = document.querySelector('#noResults');
    if (!tbody) return;

    const filtered = configData.filter(matches);
    tbody.innerHTML = '';

    if (filtered.length === 0) {
      noResults.style.display = 'block';
      return;
    }

    noResults.style.display = 'none';

    filtered.forEach((field, idx) => {
      const mainRow = document.createElement('tr');
      const isExpanded = expandedRows.has(`${field.tier}-${field.name}`);

      mainRow.className = 'expandable-row';
      if (isExpanded) {
        mainRow.classList.add('expanded');
      }
      mainRow.dataset.fieldName = field.name;
      mainRow.dataset.tier = field.tier;

      mainRow.innerHTML = `
        <td class="field-name">${field.name}</td>
        <td><code style="font-family: var(--font-mono); font-size: 0.8rem;">${field.type}</code></td>
        <td><code style="font-family: var(--font-mono); font-size: 0.8rem;">${field.default}</code></td>
        <td>${tierBadge(field.tier)}</td>
        <td style="color: var(--text-muted); font-size: 0.85rem;">${truncateText(field.description, 80)}</td>
      `;

      mainRow.addEventListener('click', () => toggleRowExpand(mainRow, field));
      tbody.appendChild(mainRow);

      // Detail row (hidden by default)
      if (isExpanded) {
        const detailRow = document.createElement('tr');
        detailRow.className = 'detail-row show';
        detailRow.innerHTML = `
          <td colspan="5">
            <div class="detail-content">
              <h4>${field.name}</h4>
              <p>${field.description}</p>
            </div>
          </td>
        `;
        tbody.appendChild(detailRow);
      }
    });
  }

  /**
   * Truncate text to a maximum length with ellipsis.
   */
  function truncateText(text, maxLen) {
    if (text.length > maxLen) {
      return text.substring(0, maxLen) + '…';
    }
    return text;
  }

  /**
   * Toggle row expansion and detail visibility.
   */
  function toggleRowExpand(row, field) {
    const key = `${field.tier}-${field.name}`;
    const detailRow = row.nextElementSibling;

    if (expandedRows.has(key)) {
      expandedRows.delete(key);
      row.classList.remove('expanded');
      if (detailRow && detailRow.classList.contains('detail-row')) {
        detailRow.classList.remove('show');
      }
    } else {
      expandedRows.add(key);
      row.classList.add('expanded');
      if (detailRow && detailRow.classList.contains('detail-row')) {
        detailRow.classList.add('show');
      } else {
        // If detail row doesn't exist, insert it
        const tbody = row.parentElement;
        const detailRow = document.createElement('tr');
        detailRow.className = 'detail-row show';
        detailRow.innerHTML = `
          <td colspan="5">
            <div class="detail-content">
              <h4>${field.name}</h4>
              <p>${field.description}</p>
            </div>
          </td>
        `;
        row.insertAdjacentElement('afterend', detailRow);
      }
    }
  }

  /**
   * Update search term (debounced).
   */
  function updateSearch(term) {
    activeSearch = term;
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      expandedRows.clear();
      renderTable();
    }, DEBOUNCE_MS);
  }

  /**
   * Toggle a tier filter button.
   */
  function toggleTier(tier) {
    if (activeTiers.has(tier)) {
      activeTiers.delete(tier);
    } else {
      activeTiers.add(tier);
    }
    expandedRows.clear();
    renderTable();
  }

  /**
   * Initialize the config table on page load.
   */
  function init() {
    configData = loadConfigData();
    if (!configData || configData.length === 0) {
      console.error('No config data loaded');
      return;
    }

    // Search input
    const searchInput = document.querySelector('#configSearch');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        updateSearch(e.target.value);
      });
    }

    // Tier filter buttons
    document.querySelectorAll('.tier-btn').forEach((btn) => {
      const tier = parseInt(btn.dataset.tier, 10);
      btn.addEventListener('click', () => {
        toggleTier(tier);
        btn.classList.toggle('active');
      });
    });

    // Initial render
    renderTable();
  }

  // Run on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
