# Codebase Explorer Site — Prompt Pack

> Copy-paste prompts for follow-on build sessions. Each prompt is self-contained.
> Phases are sequential (must finish before the next starts); prompts within a
> phase are parallel unless marked SEQUENTIAL.

---

## Phase 0 — Scaffold, Design System & Golden Page

> **Dependency:** None (first phase).
> **Must complete before:** all Phase 1 prompts.
> **Goal:** Create the shared infrastructure and one finished page that sets the
> quality bar for everything that follows.

### Prompt 0A — Design System + Shared Infrastructure + Landing Page

```
CONTEXT
You are building a static HTML documentation site for an LP-based electricity
market dispatch simulator. The site lives at docs/codebase-site/ in the
market-simulator repo. Read docs/codebase-site/PLAN.md for the full plan.

The design system is the **Observatory** system from the hourly-cfe-optimizer
repo (dashboard/styles/shared.css + article.css). Fetch the upstream files for
reference — the key tokens, components, and patterns are documented in
PLAN.md §6, but the full CSS is the source of truth for the port.

UPSTREAM REFERENCE (read before building)
- https://raw.githubusercontent.com/jessicacohen554-cyber/hourly-cfe-optimizer/master/dashboard/styles/shared.css
- https://raw.githubusercontent.com/jessicacohen554-cyber/hourly-cfe-optimizer/master/dashboard/styles/article.css
- https://raw.githubusercontent.com/jessicacohen554-cyber/hourly-cfe-optimizer/master/dashboard/js/nav.js
- https://raw.githubusercontent.com/jessicacohen554-cyber/hourly-cfe-optimizer/master/dashboard/js/shared-header.js

TASK
Build the shared infrastructure and the landing page (index.html) — the
"golden" page that sets the quality bar for all subsequent pages.

DELIVERABLES (exact files)
1. docs/codebase-site/css/shared.css
   - Port of the Observatory design system. Include:
     - All :root tokens from PLAN.md §6 (surfaces, text, fonts, fuel palette,
       ISO palette, layout, radius, elevation).
     - Section-rhythm classes: .section-light, .section-dark (navy gradient bg,
       white text, glassmorphic cards), .section-transition-light-to-dark,
       .section-transition-dark-to-light, .energy-divider (3px gradient bar).
     - Components: .top-nav (sticky, hamburger < 768px), .header (with SVG
       waveform overlay placeholder), .hero-overview, .content-section,
       .content-section-narrow, .card (with hover lift), .chart-panel,
       .glass-chart-panel (frosted glass), .stat-card, .insight-box
       (.info/.warn/.danger/.success), .insight-glass, .emphasis-callout,
       .section-header + .section-number, .narrative-card, .scroll-section,
       .data-table, .badge, .stat-badge, .toggle-btn-group, .iso-selector +
       .iso-btn, .chart-legend (with swatch types), .headline-card,
       .headline-row, .page-footer + .bottom-banner (4-color gradient bar).
     - .story-section (fade-in on scroll, works with GSAP ScrollTrigger).
     - Responsive breakpoints at 900px, 768px, 600px, 480px.
     - @import Plus Jakarta Sans + DM Sans (Google Fonts).
   - NO global dark-mode toggle or [data-theme] overrides — use the
     section-level .section-light / .section-dark rhythm instead.

2. docs/codebase-site/css/site.css
   - Site-specific additions not in Observatory:
     - .fig (figure wrapper: chart container + caption + expand toggle)
     - .fig-controls (toolbar above chart: toggles, sliders, selectors)
     - .equation (KaTeX block with optional label)
     - .code-block (dark bg, mono font)
     - .tabs (tab group for view switching)
     - .tooltip (chart hover/focus tooltip)
     - .breadcrumb (prev/next page links)
     - .toc-rail (right-rail floating mini-TOC)
     - KaTeX overrides so equations match the site typography.
     - Print styles (hide nav, full-width content).

3. docs/codebase-site/js/nav.js
   - Inject a sticky top nav bar into <nav id="topNav"> placeholder on every
     page. Structure (match CFE optimizer pattern):
     - Logo/home link: "Codebase Explorer" → index.html
     - Dropdown group: "Foundations" → Mental Model, Data Pipeline,
       Fleet & Offer Curves
     - Dropdown group: "The Engine" → LP Core, Solving & Pricing, The Network
     - Dropdown group: "Evolution & Policy" → Capacity Evolution,
       Policy & Scarcity, Results & Calibration
     - Single link: "Reference" → Config Reference
     - Hamburger toggle on mobile (< 768px)
   - Active page detection: highlight the current page link by matching
     filename from window.location.pathname.

4. docs/codebase-site/js/shared-header.js
   - Inject SVG waveform overlay into .header elements (same pattern as CFE
     optimizer). Read data-header-variant attribute for variant selection.
   - Lazy-load pattern for below-fold headers.

5. docs/codebase-site/js/shared.js
   - Auto-build floating right-rail mini-TOC from <h2> and <h3> elements
     inside <main>. Highlight the currently-visible heading via
     IntersectionObserver.
   - Initialize GSAP ScrollTrigger for .story-section and .narrative-card
     entrance animations (fade-in + translateY).
   - Register prefers-reduced-motion: disable all GSAP animations.

6. docs/codebase-site/js/chart-utils.js
   - D3 v7 helper module (imported as ES module by viz scripts).
   - responsiveChart(containerSelector, drawFn): handles ResizeObserver,
     calls drawFn(width, height) on resize, debounced.
   - cssColor(varName): reads a CSS custom property value from :root.
   - fuelColorScale(): returns a D3 ordinal scale mapping fuel names to
     Observatory --solar/--wind/--hydro/--nuclear/--fossil-gas/--fossil-coal
     CSS vars.
   - isoColorScale(): same for --iso-* vars.
   - addTooltip(svg, className): creates a tooltip <div> positioned on
     mousemove, with show(html, event)/hide() methods.
   - formatMW(value), formatPrice(value), formatPct(value): locale-aware
     number formatters for chart labels.

7. docs/codebase-site/index.html
   The landing page. Requirements:
   - <nav id="topNav"></nav> placeholder (filled by nav.js).
   - .header section with SVG waveform overlay (filled by shared-header.js):
     - Eyebrow: "Codebase Explorer"
     - Title: "Inside the Market Simulator"
     - Subtitle: one paragraph explaining what the site is.
   - .section-light with a .headline-row of 3–4 .stat-cards showing key
     model facts (7 ISOs, 8,760 hours, ~200k LP variables, 2026–2050 horizon).
   - .energy-divider
   - .section-light with a grid of 10 .cards (one per page), each with:
     - A small icon (inline SVG).
     - The page title and a one-sentence description.
     - A link to the page.
     - Cards grouped visually into the 3+1 sections with .section-header
       labels (Foundations, Engine, Evolution & Policy, Reference).
   - .section-dark with the "system overview" animated diagram (V1): a
     simplified flow showing Demand → Fleet → LP → Prices → Capacity
     Evolution → next year, built with D3 SVG. Nodes are rounded rectangles;
     arrows animate on load via GSAP. Hover tooltips per node. Use
     .glass-chart-panel for the diagram container.
   - .section-transition-dark-to-light
   - .page-footer with .bottom-banner (4-color gradient bar).
     Text: "Built from the docs/codebase reference. Code is the source of
     truth." Link back to the repo root.

QUALITY BAR
- The landing page must look polished enough to serve as a portfolio piece.
  Typography, spacing, color, and animation quality set the standard for
  every subsequent page — the Observatory design system sets a high visual bar.
- Section rhythm (light/dark) must feel intentional and varied.
- Lighthouse accessibility score ≥ 90.
- All external libraries loaded via CDN with integrity hashes:
  D3 v7, GSAP + ScrollTrigger. KaTeX only on pages that need it.
- The landing page should showcase: .top-nav, .header, .stat-card, .card,
  .section-light, .section-dark, .glass-chart-panel, .energy-divider,
  .page-footer, .bottom-banner, .toc-rail, .breadcrumb.
- Responsive: test at 1400px, 1000px, 700px, 400px widths.

ACCEPTANCE CRITERIA
- [ ] All seven files exist and are syntactically valid.
- [ ] index.html loads in a browser with no console errors.
- [ ] Top nav renders with dropdown groups and all 10 pages listed.
- [ ] SVG waveform header renders in the .header section.
- [ ] Mini-TOC auto-generates from headings.
- [ ] System overview diagram animates on load (GSAP).
- [ ] Section rhythm: light → dark → light transitions are smooth.
- [ ] Cards link to the correct (not-yet-built) page slugs.
- [ ] Responsive at all four breakpoints (no horizontal scroll, no overlap).
- [ ] prefers-reduced-motion disables all animations.
```

### Prompt 0B — Illustrative Data Files (PARALLEL with 0A)

```
CONTEXT
You are preparing illustrative JSON data files for a static documentation site
about an LP-based electricity market dispatch simulator. The site lives at
docs/codebase-site/. Read docs/codebase-site/PLAN.md §4 (Data Strategy) for
the full spec.

The data must be ILLUSTRATIVE but FAITHFUL — representative of real model
proportions, not raw solver output. Every file must include a "_meta" field
documenting its provenance.

SOURCE MATERIAL (read these for realistic values)
- docs/codebase/04-data-layer.md — fleet composition, fuel types, capacities
- docs/codebase/02-lp-dispatch.md — LP structure, variable counts
- docs/codebase/03-capacity-and-commitment.md — capacity evolution, storage
- docs/binning-methodology.md — tranche multipliers, offer curve shapes
- docs/codebase/08-config-reference.md — parameter values, constants
- src/market_sim/config/iso_configs.py — 7-ISO zone/link/TTC data
- src/market_sim/config/constants.py — numeric constants

TASK
Create all 15 JSON data files listed in PLAN.md §4 / §7:

DELIVERABLES (exact files, all under docs/codebase-site/data/)

1. fleet-merit-order.json
   ~50 generators for an ERCOT-like system. Each generator:
   { name, fuel_type, zone, pmax_mw, heat_rate, vom, mc_total, tranche }.
   Sorted by mc_total ascending (merit order). Include a realistic mix:
   ~2 nuclear (baseload, low MC), ~8 coal plants (with PRB/lignite/bit
   tranches), ~15 gas-CC (mid MC), ~10 gas-CT (high MC), ~5 wind farms
   (zero MC), ~5 solar farms (zero MC), ~3 hydro, ~2 storage.
   Total capacity ~85 GW (ERCOT-scale).

2. offer-curve-tranches.json
   Per-fuel-type tranche definitions: { fuel_type, tranches: [
     { name, hr_multiplier, pct_of_capacity, mc_adder }
   ]}. Cover: coal_prb, coal_lignite, coal_bit, gas_cc, gas_ct.
   Values from docs/binning-methodology.md (committed 0.92×, econ 1.0×,
   peaking 2.0–2.5×, etc.). Include the coal sigmoid parameters.

3. energy-balance-sankey.json
   One zone, one summer-peak hour. Flows:
   { nodes: [...], links: [{ source, target, value }] }.
   Inflows: gas_cc, gas_ct, wind, solar, nuclear, coal, imports, storage_dis.
   Outflows: demand, exports, storage_chg, curtailment (dump).
   Values in MW, summing to balance (inflow = outflow).

4. dispatch-24h.json
   24-hour stacked dispatch for a summer peak day. Array of 24 objects:
   { hour, demand_mw, nuclear, coal, gas_cc, gas_ct, wind, solar, hydro,
     storage_net, imports, price_per_mwh }.
   Shape: nuclear flat ~5GW, coal flat ~10GW, solar bell curve peaking ~20GW
   at hour 13, wind higher at night, gas filling residual, price tracking
   marginal gas cost with evening peak ~$80/MWh.

5. price-duration.json
   8760 prices sorted descending. Array of { rank, price }.
   Shape: ~50 hours above $200 (scarcity), bulk 4000–7000 hours at $25–45,
   ~1000 hours below $15 (renewable surplus). Realistic ERCOT-like.

6. capacity-trajectory.json
   25-year (2026–2050) capacity by fuel. Array of { year, nuclear, coal,
   gas_cc, gas_ct, wind, solar, storage, hydro, hydrogen, ccs, offshore_wind,
   geothermal }. All in GW.
   Story: coal retires from 18→2 GW, gas_cc stable ~30 GW, wind grows 25→65,
   solar grows 20→80, storage grows 5→35, nuclear flat ~5, hydrogen/CCS/
   offshore enter after 2030.

7. generation-trajectory.json
   Same years, generation in TWh. Tracks capacity trajectory but with
   capacity factors applied. Total ~400–500 TWh/yr growing with demand.

8. storage-soc-48h.json
   48-hour SOC trace for two batteries: 4h (100 MW/400 MWh) and 8h
   (50 MW/400 MWh). Array of { hour, soc_4h_mwh, soc_8h_mwh, charge_4h_mw,
   discharge_4h_mw, charge_8h_mw, discharge_8h_mw, price }.
   Show: charge overnight (low price), discharge evening peak (high price),
   4h cycles daily, 8h cycles less frequently.

9. storage-value-stack.json
   Revenue decomposition per storage tech: { tech, arbitrage_per_kw_yr,
   capacity_value_per_kw_yr, as_revenue_per_kw_yr, total_per_kw_yr,
   lcoe_per_kw_yr, margin }. Cover: li_ion_4hr, li_ion_8hr, flow_battery,
   pumped_hydro.

10. iso-topologies.json
    Extract directly from iso_configs.py. Structure:
    { iso_name: { zones: [{ name, load_share }],
      links: [{ from, to, ttc_mw, bidirectional }],
      interface_limits: [{ name, links, cap_mw }],
      voll } }.
    Cover all 7 ISOs. This is the ONE file derived from live code.

11. ordc-curve.json
    ORDC penalty curve. Array of { reserve_mw, penalty_per_mwh }.
    Shape: exponential rise as reserves fall below ~3000 MW, hitting VOLL
    ($5000) at 0 MW reserve. ~50 data points.

12. congestion-example.json
    Two-zone price series for 48 hours with a binding transmission constraint.
    { hours: [{ hour, zone_a_price, zone_b_price, flow_mw, ttc_mw }] }.
    Show: prices equal when flow < TTC, zone_b higher when flow hits TTC
    (import-constrained zone).

13. learning-curves.json
    Wright's-Law cost trajectories. { tech, data: [{ year, cum_gw,
    capex_per_kw }] }. Cover: solar, wind, li_ion_4hr, li_ion_8hr, offshore_wind.
    Capex declining per NREL ATB learning rates.

14. mc-waterfall.json
    Marginal cost breakdown for one gas-CC generator at one hour.
    { components: [{ name, value, color_var }] }.
    Components: fuel (heat_rate × gas_price), VOM, carbon, NOx, SO2, minus
    EAC credit. Values in $/MWh. Total ~$35–40.

15. calibration-scorecard.json
    Example diagnostic results. { iso, year, checks: [
      { metric, category, actual, modeled, pct_error, status }
    ] }. Categories: generation (per fuel TWh), prices (mean, P10, P50, P90),
    capacity_factors. Mix of PASS/WARN/FAIL for illustration.

ACCEPTANCE CRITERIA
- [ ] All 15 files exist and are valid JSON.
- [ ] Every file has a "_meta" field with "source" and "description".
- [ ] No file exceeds 100 KB.
- [ ] iso-topologies.json matches the actual iso_configs.py data (read it).
- [ ] Numeric values are internally consistent (generation ≤ capacity × 8760,
      dispatch sums to demand, prices track marginal cost, etc.).
- [ ] No raw solver output or actual backcast results — all illustrative.
```

---

## Phase 1 — Spine Pages (PARALLEL)

> **Dependency:** Phase 0 must be complete (css/site.css, js/shared.js,
> js/chart-utils.js, index.html, and all data/*.json files must exist).
> **All prompts in Phase 1 run in PARALLEL** — they write to separate HTML
> and JS files with no shared-file conflicts.

### Prompt 1A — Mental Model (page 1)

```
CONTEXT
You are building page 1 of a static documentation site for an LP-based
electricity market dispatch simulator. The site lives at docs/codebase-site/.
Read docs/codebase-site/PLAN.md for the full architecture, design system, and
visualization inventory.

REQUIRED READING (before writing any code)
- docs/codebase-site/css/shared.css + css/site.css — use these classes, don't invent new ones
- docs/codebase-site/index.html — match this quality bar exactly
- docs/codebase/01-architecture.md — the content source for this page

TASK
Build the "Mental Model" page — the reader's first conceptual entry point.

DELIVERABLES
1. docs/codebase-site/mental-model.html
2. docs/codebase-site/js/viz-dispatch-24h.js

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "Foundations", title "The 8,760-Hour Problem", subtitle about
  how electricity demand must be met every hour.
- Section 1: "Supply Meets Demand" — explain the core problem. Text: demand
  varies by hour, generators have different costs, cheapest run first, price
  is set by the most expensive unit needed.
- Visualization V2 (dispatch-24h): Interactive stacked-area chart showing 24
  hours of a summer peak day. Data: data/dispatch-24h.json. Features:
  - Stacked areas colored by fuel (use fuelColorScale from chart-utils.js)
  - Demand line overlay (dashed black/white depending on theme)
  - Price line on secondary y-axis
  - Hover: show hour, dispatch by fuel, price in tooltip
  - Legend with fuel toggles (click to show/hide a fuel)
  - Time scrubber slider below the chart
- Section 2: "The Merit Order" — brief intro to why generators stack by cost.
  Link forward to page 3 (Fleet & Offer Curves) for the deep dive.
- Section 3: "From Dispatch to Prices" — explain that the LP's shadow price
  (dual variable) on the energy-balance constraint IS the market price.
  Link forward to page 4 (LP Core) and page 5 (Solving & Pricing).
- Section 4: "The Year Loop" — one paragraph explaining that this dispatch
  repeats for every year 2026–2050, with fleet changes between years.
  Link forward to page 7 (Capacity Evolution).
- .insight-box (info): "This is a dispatch model, not a unit commitment model.
  The LP finds the cheapest way to meet demand — no binary on/off decisions."
- Breadcrumb: ← Overview | Data Pipeline →

ACCEPTANCE CRITERIA
- [ ] Page loads with no console errors.
- [ ] Uses only classes from site.css (no custom styles beyond minor layout).
- [ ] Top nav highlights "Mental Model" as active.
- [ ] V2 chart renders correctly with data from dispatch-24h.json.
- [ ] Chart works in both .section-light and .section-dark contexts.
- [ ] Chart is responsive (readable at 900px and 600px).
- [ ] All cross-links point to correct page slugs.
- [ ] Mini-TOC generates from section headings.
```

### Prompt 1B — Data Pipeline (page 2)

```
CONTEXT
You are building page 2 of a static documentation site for an LP-based
electricity market dispatch simulator. The site lives at docs/codebase-site/.
Read PLAN.md for the full plan. Match the quality of index.html exactly.

REQUIRED READING
- docs/codebase-site/css/site.css, js/shared.js, js/chart-utils.js
- docs/codebase-site/index.html (quality bar)
- docs/codebase/04-data-layer.md (content source)

TASK
Build the "Data Pipeline" page — explaining how raw data becomes LP input.

DELIVERABLES
1. docs/codebase-site/data-pipeline.html

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "Foundations", title "The Data Pipeline", subtitle about
  turning raw EIA/CAMPD/eGRID data into the arrays the LP consumes.
- Section 1: "Raw Sources" — table of data sources:
  | Source | What It Provides | Files |
  EIA-860 (plant characteristics), EIA-930 (hourly demand/gen/interchange),
  EIA-923 (monthly fuel costs/generation), CAMPD (unit-level CEMS emissions/
  generation), eGRID (emission rates, geography), gas prices (Henry Hub + basis).
  Use .data-table component.
- Section 2: "The Pipeline" — V3 data-flow diagram (static SVG, hand-built
  in the HTML). Show: raw sources → loader modules → intermediate objects
  (Generator, FleetArrays) → LP builder. Each stage is a rounded box; arrows
  show flow. Color-code by layer (data=blue, model=purple, config=green).
  No D3 needed — pure SVG with CSS animations for arrow flow.
- Section 3: "FleetArrays — The LP's Input" — explain the struct-of-arrays
  pattern: pmax, pmin, heat_rate, vom, emission_rate, zone_idx, etc. as
  parallel numpy arrays. Show a schematic table of what FleetArrays contains.
  Use a .code-block showing the field list.
- Section 4: "Marginal Cost Assembly" — V9 waterfall chart showing how MC
  is assembled: fuel cost + VOM + carbon + NOx − EAC. Interactive hover.
  Data: data/mc-waterfall.json. Build in a small inline <script> or a
  dedicated viz-waterfall.js file.
- .insight-box (info): "The LP builder only touches arrays and scalars.
  The conversion from rich Pydantic objects to flat arrays is the architectural
  seam — all complexity is resolved before the LP sees it."
- Breadcrumb: ← Mental Model | Fleet & Offer Curves →

ACCEPTANCE CRITERIA
- [ ] Page loads with no console errors; matches index.html quality.
- [ ] Data-flow SVG diagram renders with animated arrows.
- [ ] Waterfall chart renders from mc-waterfall.json with hover tooltips.
- [ ] Source table is properly styled with .data-table.
- [ ] .section-dark sections render with glassmorphic cards and white text.
- [ ] Responsive at all breakpoints.
```

### Prompt 1C — Fleet & Offer Curves (page 3)

```
CONTEXT
You are building page 3 of a static documentation site for an LP-based
electricity market dispatch simulator at docs/codebase-site/. Read PLAN.md.
Match index.html quality.

REQUIRED READING
- css/shared.css, css/site.css, js/nav.js, js/shared.js, js/chart-utils.js
- docs/codebase/04-data-layer.md (fleet section)
- docs/binning-methodology.md (tranche structure, offer curves)

TASK
Build the "Fleet & Offer Curves" page — the CAMPD binning system, tranche
offer curves, and merit-order visualization.

DELIVERABLES
1. docs/codebase-site/fleet-offer-curves.html
2. docs/codebase-site/js/viz-merit-order.js (V4)
3. docs/codebase-site/js/viz-offer-curve.js (V5)
4. docs/codebase-site/js/viz-coal-sigmoid.js (V6)

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "Foundations", title "Fleet & Offer Curves", subtitle about
  how each plant becomes an LP generator with a rising cost curve.
- Section 1: "CAMPD Per-Plant Binning" — explain that each plant splits into
  tranches: must-run, committed, economic (N slices), peaking. Table showing
  tranche structure per fuel type. Use data from offer-curve-tranches.json.
- Section 2: "The Merit Order" — V4 interactive merit-order stack.
  Horizontal stacked bars, one per generator, sorted by MC (cheapest at
  bottom). Width = capacity (MW), color = fuel type.
  Data: fleet-merit-order.json.
  Features: hover shows generator details; fuel-type filter buttons above
  chart; demand line overlay (vertical dashed line at e.g. 55 GW).
  Intuition: "everything to the left of the demand line dispatches."
- Section 3: "Tranche Offer Curves" — V5 stepped line chart showing one
  plant's rising cost curve from must-run through peaking.
  Interactive: dropdown to select fuel type (coal_prb, gas_cc, gas_ct);
  the chart redraws with that fuel's tranche multipliers.
  Data: offer-curve-tranches.json.
- Section 4: "Coal Take-or-Pay & PRB Sigmoid" — V6 interactive sigmoid.
  X-axis: gas price ($/MMBtu, range 2–8). Y-axis: coal fuel_frac (0–1).
  The sigmoid shows how the fraction of coal fuel cost passed through
  depends on gas price competition. Slider to adjust gas price; the curve
  and a marker move in real time.
  Explain: mine-mouth lignite = full cost always; PRB = sigmoid passthrough;
  bituminous = full spot.
- .insight-box: "One plant = one LP generator. Despite the legacy name 'binning',
  there are no aggregated bins — each plant dispatches on its own heat rate."
- Breadcrumb: ← Data Pipeline | The LP Core →

ACCEPTANCE CRITERIA
- [ ] Three interactive D3 charts render correctly.
- [ ] Merit-order chart responds to fuel filter toggles.
- [ ] Offer-curve chart redraws on fuel-type selection.
- [ ] Coal sigmoid moves smoothly with slider interaction.
- [ ] All charts support dark mode and responsive resize.
- [ ] Cross-links to adjacent pages work.
```

### Prompt 1D — The LP Core (page 4)

```
CONTEXT
You are building page 4 of a static documentation site for an LP-based
electricity market dispatch simulator at docs/codebase-site/. Read PLAN.md.
Match index.html quality.

REQUIRED READING
- css/shared.css, css/site.css, js/nav.js, js/shared.js, js/chart-utils.js
- docs/codebase/02-lp-dispatch.md (content source — the LP formulation)
- src/market_sim/model/dispatch.py (variable layout, constraints)

TASK
Build the "LP Core" page — the variable layout, constraint matrix, objective
function, and energy-balance Sankey. This is the mathematical heart of the
site.

DELIVERABLES
1. docs/codebase-site/lp-core.html
2. docs/codebase-site/js/viz-sparsity.js (V8)
3. docs/codebase-site/js/viz-sankey.js (V10)

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "The Engine", title "The LP Core", subtitle about the
  linear program that clears 8,760 hours of electricity demand.
- Section 1: "Decision Variables" — V7 variable-layout block diagram.
  Build as a static SVG: a long horizontal bar divided into colored blocks
  labeled P[g,t] | W[z,t] | S[z,t] | Chg[s,t] | Dis[s,t] | SOC[s,t] |
  Flow[l,t] | Slack[z,t] | Dump[z,t]. Each block's width proportional to
  its dimension count. Hover shows: variable name, typical count, bounds.
  Below the bar: a formula showing total columns = T × (n_gen + 4×n_zones
  + 3×n_storage + n_links). Use KaTeX for the formula.
  Table below listing each variable with description, dimensions, bounds.
- Section 2: "Objective Function" — KaTeX-rendered objective:
  min Σ mc[g,t]×P[g,t] + ε×(Chg+Dis) + VOLL×Slack + dump_cost×Dump
  Expandable detail panel breaking down mc[g,t] = heat_rate × fuel_price +
  VOM + emission_rate × carbon_price + ...
  V9 waterfall (same as data-pipeline page, or link to it).
- Section 3: "Constraints" — structured list of constraint families:
  energy balance, generator bounds, renewable bounds, storage SOC, transmission.
  Each with its KaTeX equation and a brief explanation.
  Expandable panels for optional constraints: RPS, hydro monthly, interface
  limits, reserve co-optimization.
- Section 4: "The Constraint Matrix" — V8 sparsity pattern.
  Interactive D3 canvas visualization showing the block-diagonal structure.
  Rows = constraints (energy balance, storage SOC, bounds). Columns =
  variables. Color-code blocks by constraint type. Show the Kronecker
  tiling pattern (one per-hour block repeated T times).
  Controls: zoom, hover shows block type and dimensions.
  Data: schematic (no JSON file — computed from variable/constraint counts).
- Section 5: "Energy Balance — The Core Constraint" — V10 Sankey diagram.
  D3-sankey showing one zone, one hour: inflows (thermal, wind, solar,
  discharge, imports) → demand node → outflows (charge, exports, dump).
  Data: energy-balance-sankey.json.
  Zone selector dropdown, hour slider (illustrative).
- Section 6: "Duals → Prices" — V11 annotated diagram (static SVG) showing
  the energy-balance constraint row with an arrow pointing to its dual
  variable, labeled "= Zonal LMP ($/MWh)". KaTeX equation for the dual
  interpretation. Brief explanation: "The shadow price on each zone's energy
  balance constraint is the locational marginal price."
- Breadcrumb: ← Fleet & Offer Curves | Solving & Pricing →

ACCEPTANCE CRITERIA
- [ ] KaTeX renders all equations correctly (load KaTeX CDN on this page).
- [ ] Variable-layout SVG is clear and readable, with hover tooltips.
- [ ] Sparsity pattern renders in D3 canvas with zoom and hover.
- [ ] Sankey diagram renders with d3-sankey plugin.
- [ ] All expandable panels work (click to toggle).
- [ ] KaTeX equations render correctly in both .section-light and .section-dark.
- [ ] Page is responsive; complex charts stack vertically on mobile.
```

### Prompt 1E — Solving & Pricing (page 5)

```
CONTEXT
You are building page 5 of a static documentation site for an LP-based
electricity market dispatch simulator at docs/codebase-site/. Read PLAN.md.
Match index.html quality.

REQUIRED READING
- css/shared.css, css/site.css, js/nav.js, js/shared.js, js/chart-utils.js
- docs/codebase/03-capacity-and-commitment.md (P0→P1→P2 section)
- docs/codebase/02-lp-dispatch.md (duals, pricing)

TASK
Build the "Solving & Pricing" page — the P0→P1→P2 solve sequence, how
startup costs enter pricing, the commitment screen, and price outputs.

DELIVERABLES
1. docs/codebase-site/solving-pricing.html
2. docs/codebase-site/js/viz-p012-sequence.js (V12)
3. docs/codebase-site/js/viz-price-duration.js (V13)

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "The Engine", title "Solving & Pricing", subtitle about the
  three-solve sequence and how prices emerge from LP duals.
- Section 1: "Why Three Solves?" — brief motivation: base cost discovers
  run lengths, bid cost adds startup recovery, commitment screens unprofitable
  units.
- Section 2: "P0 → P1 → P2" — V12 animated step-through diagram.
  Three stages shown as connected panels. Click "Next" to advance:
  - P0 panel: "Base MC dispatch" — shows fleet dispatched at fuel cost only.
    Arrow to P1 labeled "extract run lengths."
  - P1 panel: "Bid MC dispatch" — same LP re-costed with startup markup.
    Arrow to P2 labeled "screen commitments."
  - P2 panel: "Commitment screen" — decision tree: Is the unit's run
    profitable at P1 prices? Does it meet min-run/min-down? If yes, commit;
    if no, decommit. Coal pinned to P1 dispatch.
  Animated transitions (slide left, fade in). Step indicator dots below.
- Section 3: "How Startup Costs Enter Prices" — explain the monthly markup
  calculation: startup_cost / avg_run_length. Diagram showing a CC unit's
  P0 run pattern → measured run length → markup applied in P1.
- Section 4: "Price Outputs" — V13 price-duration curve.
  Data: price-duration.json. Sorted descending. X-axis: hours (0–8760).
  Y-axis: price ($/MWh). Log-scale toggle for y-axis.
  Annotations: label the scarcity tail (>$200), the baseload plateau
  ($25–45), and the renewable-surplus trough (<$15).
  Interactive: hover shows rank and price; optional ISO overlay toggle
  (if multiple ISOs in data, else single line).
- Section 5: "Warm-Start & Performance" — brief note on how P1 warm-starts
  from P0's basis for ~5× speedup. Link to docs for details.
- Breadcrumb: ← The LP Core | The Network →

ACCEPTANCE CRITERIA
- [ ] P0→P1→P2 diagram animates correctly with step-through controls.
- [ ] Price-duration curve renders with hover, annotations, and log toggle.
- [ ] Step indicator dots track current animation state.
- [ ] Section rhythm (light/dark) renders correctly. Responsive at all breakpoints.
- [ ] Cross-links to LP Core and Network pages work.
```

### Prompt 1F — The Network (page 6)

```
CONTEXT
You are building page 6 of a static documentation site for an LP-based
electricity market dispatch simulator at docs/codebase-site/. Read PLAN.md.
Match index.html quality.

REQUIRED READING
- css/shared.css, css/site.css, js/nav.js, js/shared.js, js/chart-utils.js
- docs/codebase/03-capacity-and-commitment.md (transmission section)
- src/market_sim/config/iso_configs.py (zone/link definitions)
- data/iso-topologies.json (created in Phase 0B)

TASK
Build the "Network" page — 7-ISO topology visualization, transmission
modeling, and congestion pricing.

DELIVERABLES
1. docs/codebase-site/network.html
2. docs/codebase-site/js/viz-iso-topology.js (V14)
3. docs/codebase-site/js/viz-congestion.js (V15)

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "The Engine", title "The Network", subtitle about the
  pipe-and-bubble model connecting zones within and between ISOs.
- Section 1: "Pipe and Bubble" — explain the transmission model: zones are
  copper-plate bubbles, links are pipes with TTC limits. Incidence matrix
  representation. Brief, conceptual.
- Section 2: "7-ISO Topologies" — V14 interactive ISO network graph.
  Data: iso-topologies.json.
  Features:
  - Tab bar with 7 ISO names (colored by --iso-* palette). Click to switch.
  - For each ISO: D3 force-directed graph showing zones as circles (sized by
    load_share) and links as lines (thickness ∝ TTC). Labels on zones and
    links (TTC in GW). Import nodes (WECC, HQ) styled differently (dashed
    border).
  - Hover on zone: show name, load share, connected links.
  - Hover on link: show from→to, TTC, bidirectional status.
  - Optional: geographic layout hints (approximate x,y positions) for ISOs
    where it makes the topology clearer (ERCOT, PJM, NYISO).
- Section 3: "Interface Limits" — explain aggregate interface limits (e.g.,
  CAISO simultaneous import cap 8.3 GW < sum of individual path TTCs).
  Table of interface limits per ISO from iso-topologies.json.
- Section 4: "Congestion & Price Separation" — V15 congestion example.
  Data: congestion-example.json. Two-line chart showing zone_a and zone_b
  prices over 48 hours, with a shaded band when flow = TTC (binding).
  Annotation: "When the link binds, prices diverge."
  Hour scrubber showing flow vs TTC below the price chart.
- Section 5: "Priced Seams" — explain import/export synthetic generators
  for inter-ISO seams (CAISO WECC tranches, NEISO HQ import). Diagram
  showing tranche ladder structure.
- Breadcrumb: ← Solving & Pricing | Capacity Evolution →

ACCEPTANCE CRITERIA
- [ ] ISO topology graph renders for all 7 ISOs with tab switching.
- [ ] Zone and link hover tooltips work correctly.
- [ ] Congestion chart shows price divergence when flow binds.
- [ ] All 7 ISOs' data matches iso-topologies.json.
- [ ] Section rhythm and responsive design work.
```

### Prompt 1G — Capacity Evolution (page 7)

```
CONTEXT
You are building page 7 of a static documentation site for an LP-based
electricity market dispatch simulator at docs/codebase-site/. Read PLAN.md.
Match index.html quality.

REQUIRED READING
- css/shared.css, css/site.css, js/nav.js, js/shared.js, js/chart-utils.js
- docs/codebase/03-capacity-and-commitment.md (capacity evolution section)

TASK
Build the "Capacity Evolution" page — the 6-step annual loop, multi-year
trajectories, and Wright's-Law learning.

DELIVERABLES
1. docs/codebase-site/capacity-evolution.html
2. docs/codebase-site/js/viz-capacity-flow.js (V16)
3. docs/codebase-site/js/viz-stacked-area.js (V17)
4. docs/codebase-site/js/viz-learning.js (V18)

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "Evolution & Policy", title "Capacity Evolution", subtitle
  about how the fleet changes year over year.
- Section 1: "The Six Steps" — V16 animated flowchart.
  Six connected boxes: Known Retirements → Economic Retirements → Known
  Additions → CCS Retrofits → Economic New Entry → Reserve-Margin Backstop.
  Play/step buttons to advance through steps one at a time.
  Each step, when active, shows a brief explanation panel beside it.
  Step details:
  1. Known retirements: drop units past retirement date
  2. Economic retirements: revenue < FOM for N consecutive years
  3. Known additions: EIA-860 pipeline (construction-committed)
  4. CCS retrofits: payback < remaining life on gas-CCs
  5. Economic new entry: LCOE vs expected revenue, per-tech queue caps
  6. Reserve-margin backstop: force-build CT if below planning margin
- Section 2: "Capacity Over Time" — V17 stacked-area chart.
  Data: capacity-trajectory.json. X-axis: 2026–2050. Y-axis: GW.
  Stacked by fuel type (use fuelColorScale). Hover shows year breakdown.
  Toggle between capacity (GW) and generation (TWh) using
  generation-trajectory.json.
- Section 3: "Economic Retirement Logic" — explain the going-forward test:
  inframarginal energy margin + attribute revenue + capacity payment vs FOM.
  Table of per-fuel thresholds (coal 1yr, gas_ct 2yr, gas_cc 3yr) and FOM
  multipliers.
- Section 4: "Wright's-Law Learning" — V18 log-log chart.
  Data: learning-curves.json. X-axis: cumulative GW deployed (log). Y-axis:
  capex $/kW (log). Lines for solar, wind, li_ion_4hr, offshore_wind.
  Hover shows year, deployment, cost.
- Section 5: "Storage New Entry" — V20 value-stack bar chart.
  Data: storage-value-stack.json. Stacked bars per tech: arbitrage +
  capacity value + AS revenue vs LCOE.
  Brief explanation of the value-stack screening logic.
  V19 storage SOC trace: data/storage-soc-48h.json. 48-hour line chart
  showing SOC for 4h and 8h batteries with price overlay.
  Build viz-storage-soc.js and viz-storage-value.js.
- Breadcrumb: ← The Network | Policy & Scarcity →

EXTRA DELIVERABLES (storage viz)
5. docs/codebase-site/js/viz-storage-soc.js (V19)
6. docs/codebase-site/js/viz-storage-value.js (V20)

ACCEPTANCE CRITERIA
- [ ] 6-step flowchart animates correctly with play/step controls.
- [ ] Stacked-area chart renders with fuel toggle and capacity/generation switch.
- [ ] Learning-curves chart renders on log-log axes.
- [ ] Storage SOC trace and value-stack charts render correctly.
- [ ] All charts support dark mode and responsive resize.
```

### Prompt 1H — Policy & Scarcity (page 8)

```
CONTEXT
You are building page 8 of a static documentation site for an LP-based
electricity market dispatch simulator at docs/codebase-site/. Read PLAN.md.
Match index.html quality.

REQUIRED READING
- css/shared.css, css/site.css, js/nav.js, js/shared.js, js/chart-utils.js
- docs/codebase/05-policy.md (content source)

TASK
Build the "Policy & Scarcity" page — IRA credits, RPS, carbon pricing,
ORDC/RCPF scarcity curves, and reserve co-optimization.

DELIVERABLES
1. docs/codebase-site/policy-scarcity.html
2. docs/codebase-site/js/viz-ordc.js (V22)

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "Evolution & Policy", title "Policy & Scarcity", subtitle
  about how policy layers and scarcity pricing shape the market.
- Section 1: "IRA Tax Credits" — V21 timeline/Gantt chart (static SVG).
  Horizontal bars showing each credit's duration:
  - §45 PTC Wind: 2022–2027 ($26/MWh)
  - §48 ITC Solar/Storage: 2022–2027 (30%)
  - §45Q CCUS: 2022–2032 ($85/tCO2)
  - §45V Hydrogen: 2022–2027 ($3/kg)
  - §45E Geothermal: 2028–2033 (phased)
  Show phase-out cliffs. Explain how each enters dispatch MC or LCOE.
- Section 2: "RPS Constraint" — V23 annotated LP diagram (static SVG).
  Show the annual inequality: Σ(wind + solar + nuclear) ≥ target × demand.
  KaTeX equation. Explain: dual = REC/RPS shadow price.
  Table of state RPS targets (CA SB100, NY CLCPA, MA CES) with year ramps.
- Section 3: "Carbon Pricing" — explain resolution priority: flat override →
  state program (CA cap-and-trade, RGGI) → trajectory (RFF low/mid/high).
  Small map or table showing which ISOs have state carbon pricing.
- Section 4: "ORDC Scarcity Pricing" — V22 interactive ORDC curve.
  Data: ordc-curve.json. X-axis: reserve (MW). Y-axis: penalty ($/MWh).
  Interactive: slider for reserve level; marker moves along curve; tooltip
  shows LOLP and penalty. Explain: ERCOT's ORDC prices scarcity as reserves
  fall, lifting energy prices endogenously.
  Brief comparison: NYISO RCPF (nested locational) and PJM stepped ORDC.
- Section 5: "Reserve Co-Optimization" — explain the optional LP extension:
  reserve variables, shared-headroom constraints, reserve-balance rows.
  Expandable panel with KaTeX formulation.
  Diagram showing ERCOT multi-product nesting (RegUp ⊂ RRS ⊂ ECRS ⊂ NonSpin).
- Section 6: "Environmental Attribute Credits" — brief explanation of
  exogenous EAC prices per technology (nuclear, CCS, geothermal, offshore).
  How they enter dispatch MC as negative adders.
- Breadcrumb: ← Capacity Evolution | Results & Calibration →

ACCEPTANCE CRITERIA
- [ ] IRA timeline renders as clear, readable SVG.
- [ ] ORDC curve is interactive with slider and tooltip.
- [ ] KaTeX equations render for RPS and reserve co-opt formulations.
- [ ] All expandable panels work.
- [ ] Section rhythm works for all elements.
- [ ] Responsive at all breakpoints.
```

### Prompt 1I — Results & Calibration (page 9)

```
CONTEXT
You are building page 9 of a static documentation site for an LP-based
electricity market dispatch simulator at docs/codebase-site/. Read PLAN.md.
Match index.html quality.

REQUIRED READING
- css/shared.css, css/site.css, js/nav.js, js/shared.js, js/chart-utils.js
- docs/codebase/06-results-and-calibration.md (content source)

TASK
Build the "Results & Calibration" page — output structure, backcast
validation, forecast-vs-backcast distinction, and the calibration dashboard.

DELIVERABLES
1. docs/codebase-site/results-calibration.html

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "Evolution & Policy", title "Results & Calibration", subtitle
  about how the model's outputs are structured and validated.
- Section 1: "Result Structure" — V26 flow diagram (static SVG).
  LP solve → DispatchResult → Parquet cache → annual aggregation → JSON
  export → dashboard. Each stage as a rounded box.
- Section 2: "What Gets Cached" — explain the Parquet-per-scenario-year
  pattern: one file per year, deterministic cache key, check-before-run.
  Code block showing the cache directory structure.
- Section 3: "Forecast vs. Backcast" — V24 toggle comparison.
  Two-column layout with a toggle switch. Left: "Forecast" column listing
  what forecast mode uses (statistical outages, parametric fuel prices,
  renewable buildout). Right: "Backcast" column listing what backcast mode
  uses (CAMPD outage windows, EIA-923 fuel prices, measured CFs, historic
  weather year). The toggle highlights one column at a time.
  .insight-box.warn: "Measured data is allowed as a reproducible physical
  input, never as the answer — no pinning the backcast to actuals."
- Section 4: "Calibration Diagnostics" — V25 scorecard table.
  Data: calibration-scorecard.json. Traffic-light table with PASS (green),
  WARN (yellow), FAIL (red) badges per metric.
  Explain the four ordered checks: generation mix, price-duration curve,
  average price, capacity factors.
- Section 5: "The Dashboard" — explain that every completed run goes on the
  backcast results dashboard. Link to backcast-runs.html (run explorer) and
  calibration-status.html (all-ISO keeper summary). Screenshot or
  diagram of the dashboard layout (optional — can be a simple description).
  Explain keeper vs. probe distinction.
- Breadcrumb: ← Policy & Scarcity | Config Reference →

ACCEPTANCE CRITERIA
- [ ] Result-flow SVG diagram renders clearly.
- [ ] Forecast/backcast toggle comparison works.
- [ ] Calibration scorecard renders with colored badges.
- [ ] Warning callout uses the .insight-box.warn component.
- [ ] Section rhythm (light/dark) renders correctly. Responsive at all breakpoints.
```

### Prompt 1J — Config Reference (page 10)

```
CONTEXT
You are building page 10 of a static documentation site for an LP-based
electricity market dispatch simulator at docs/codebase-site/. Read PLAN.md.
Match index.html quality.

REQUIRED READING
- css/shared.css, css/site.css, js/nav.js, js/shared.js, js/chart-utils.js
- docs/codebase/08-config-reference.md (content source)

TASK
Build the "Config Reference" page — a searchable, filterable reference for
ScenarioConfig fields, constants, and ISO configurations.

DELIVERABLES
1. docs/codebase-site/config-reference.html
2. docs/codebase-site/js/viz-config-table.js

PAGE STRUCTURE
- .header with SVG waveform (via shared-header.js): eyebrow "Reference", title "Configuration Reference", subtitle
  about the full parameter inventory.
- Section 1: "ScenarioConfig Fields" — large filterable table.
  Columns: Field Name | Type | Default | Tier | Description.
  Tier badges: Tier 0 (structural, blue), Tier 1 (scenario, green),
  Tier 2 (expert, orange), Tier 3 (calibration, red).
  Features (viz-config-table.js):
  - Text search box filtering across all columns.
  - Tier filter buttons (toggle tiers on/off).
  - Category collapse (group fields by purpose: Pricing, Demand, Fleet,
    Storage, Retirement, Policy, Scarcity, Transmission).
  - Click a row to expand and show the full description + citation.
  Data: inline in the HTML as a <script type="application/json"> block
  (not a separate JSON file — it's structural content, not illustrative
  data). Parse from docs/codebase/08-config-reference.md.
- Section 2: "ISO Configurations" — collapsible per-ISO sections.
  For each ISO: zone table (name, load_share), link table (from, to, TTC),
  interface limits, VOLL. Use .data-table with .badge for ISO colors.
- Section 3: "Constants Catalogue" — grouped by category with collapsible
  sections: Heat Rates, Commitment, Emissions, VOM, Availability, Gas,
  Coal, Carbon, Storage, Market Design, RPS, Queue Caps, New-Entry Costs.
  Each group: brief description + key constants in a table.
- Section 4: "Path Resolution" — explain how paths.py centralizes all
  file paths. Code block showing the key path constants.
- Breadcrumb: ← Results & Calibration | Overview →

ACCEPTANCE CRITERIA
- [ ] Config table renders with all ScenarioConfig fields.
- [ ] Search filters the table in real-time (debounced 200ms).
- [ ] Tier filter buttons toggle visibility correctly.
- [ ] Category sections collapse/expand.
- [ ] Per-ISO sections show correct zone/link data.
- [ ] Section rhythm works. Responsive (table scrolls horizontally on mobile).
```

---

## Phase 2 — Integration & Polish (SEQUENTIAL)

> **Dependency:** All Phase 1 prompts must be complete.
> **Goal:** Wire everything together, cross-link, final responsive/accessibility
> pass.

### Prompt 2A — Integration, Cross-Linking & Polish

```
CONTEXT
You are doing the integration pass on a 10-page static documentation site at
docs/codebase-site/. All pages and visualizations were built in Phase 1 by
independent sessions. Read PLAN.md for the full architecture.

TASK
1. Cross-link audit: verify every inline cross-reference between pages
   points to the correct slug and anchor. Add missing cross-links where
   concepts connect (e.g., "duals→LMP" on page 4 → page 5 Pricing section;
   "merit order" on page 1 → page 3; "FleetArrays" on page 2 → page 3).

2. Navigation consistency: verify the top nav on every page renders all
   dropdown groups with all 10 pages in the correct order and highlights
   the current page. Verify breadcrumbs (prev/next) are correct on every
   page.

3. Responsive audit: test every page at 1400px, 1000px, 700px, 400px.
   Fix any:
   - Horizontal scroll
   - Overlapping elements
   - Unreadable text or charts
   - Broken chart layouts (D3 charts should resize)

4. Section rhythm audit: verify .section-dark sections on every page. Fix:
   - Unreadable text in dark sections (contrast < 4.5:1)
   - Charts with hardcoded colors that don't work on navy backgrounds
   - SVG diagrams missing glassmorphic treatment in dark sections
   - KaTeX equations not adapting in dark sections

5. Accessibility pass:
   - Every interactive element has a focus indicator
   - All images/SVGs have alt text or aria-label
   - Tab order is logical on every page
   - No autoplay animations (respect prefers-reduced-motion)
   - ARIA roles on navigation, tabs, expandable panels

6. Performance check:
   - No page loads more than 500 KB of JS/CSS/JSON (excluding cached CDN)
   - D3 charts use requestAnimationFrame for animations
   - Data files loaded on demand (not all at once)

7. Link the site from the repo: add a card to the root index.html linking
   to docs/codebase-site/index.html with title "Codebase Explorer" and
   subtitle "Explore how the model works — visualized."

DELIVERABLES
- Modified HTML/CSS/JS files as needed (no new files).
- Modified root index.html (one new card).

ACCEPTANCE CRITERIA
- [ ] All cross-links resolve (no 404s between pages).
- [ ] Top nav consistent across all 11 HTML files.
- [ ] No horizontal scroll at any breakpoint on any page.
- [ ] Section rhythm (light/dark) correct on all pages.
- [ ] All interactive elements keyboard-accessible.
- [ ] Root index.html has the new card.
```

---

## Phase 3 — QA (SEQUENTIAL)

> **Dependency:** Phase 2 must be complete.
> **Goal:** Verify every visualization against the code/docs it claims to
> represent. Fix any drift.

### Prompt 3A — Accuracy Audit & Final Review

```
CONTEXT
You are doing the final QA pass on a 10-page static documentation site at
docs/codebase-site/ that documents an LP-based electricity market dispatch
simulator. The site must be ACCURATE — every diagram, equation, table, and
statement must match what the code actually does. Code is the source of truth.

TASK
Audit every page against its source material. For each page:

1. Read the page HTML and identify every factual claim, equation, diagram
   label, and data structure description.

2. Read the corresponding source code and docs/codebase documentation.

3. Flag any discrepancy: wrong variable name, incorrect equation term,
   missing constraint, wrong parameter value, outdated description,
   misleading simplification.

4. Fix each discrepancy directly in the HTML.

SOURCE MAPPING
| Page | Verify against |
|------|---------------|
| mental-model.html | docs/codebase/01-architecture.md, runner.py |
| data-pipeline.html | docs/codebase/04-data-layer.md, data/fleet.py, data/fuel.py |
| fleet-offer-curves.html | docs/binning-methodology.md, data/fleet.py |
| lp-core.html | docs/codebase/02-lp-dispatch.md, model/dispatch.py |
| solving-pricing.html | docs/codebase/03-capacity-and-commitment.md, model/commitment.py |
| network.html | model/transmission.py, config/iso_configs.py |
| capacity-evolution.html | docs/codebase/03-capacity-and-commitment.md, model/capacity.py |
| policy-scarcity.html | docs/codebase/05-policy.md, policy/*.py |
| results-calibration.html | docs/codebase/06-results-and-calibration.md, results/*.py |
| config-reference.html | docs/codebase/08-config-reference.md, config/scenarios.py |

ALSO CHECK
- iso-topologies.json matches current iso_configs.py (run the extraction
  or diff manually).
- Illustrative data files are internally consistent (generation ≤ capacity,
  prices track marginal cost, etc.).
- No broken CDN links.
- All file references in the site (links to source files) use correct paths.

DELIVERABLES
- Modified HTML files with corrections.
- A summary table of all discrepancies found and fixed, written to
  docs/codebase-site/QA-REPORT.md.

ACCEPTANCE CRITERIA
- [ ] Every equation matches the code (not just the methodology spec).
- [ ] Every variable name, constraint name, and parameter name is correct.
- [ ] iso-topologies.json matches live iso_configs.py.
- [ ] No factual claim contradicts the source code.
- [ ] QA-REPORT.md documents all findings.
```

---

## Execution Order Summary

```
Phase 0A  ──────────┐
                     ├── (both complete) ──→ Phase 1 fan-out
Phase 0B  ──────────┘
                                              ↓
Phase 1A (Mental Model)      ─┐
Phase 1B (Data Pipeline)      │
Phase 1C (Fleet & Offers)     │
Phase 1D (LP Core)            ├── ALL PARALLEL
Phase 1E (Solving & Pricing)  │
Phase 1F (Network)            │
Phase 1G (Capacity Evolution) │
Phase 1H (Policy & Scarcity)  │
Phase 1I (Results & Calib)    │
Phase 1J (Config Reference)  ─┘
                                              ↓
Phase 2A (Integration & Polish) ── SEQUENTIAL
                                              ↓
Phase 3A (QA Accuracy Audit)    ── SEQUENTIAL
```

**Total prompts:** 14 (2 scaffold + 10 pages + 1 integration + 1 QA)
**Maximum parallelism:** 10 (Phase 1)
**Critical path:** 0A → any Phase 1 page → 2A → 3A (4 sequential steps)
