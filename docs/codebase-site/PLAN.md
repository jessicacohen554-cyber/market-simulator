# Codebase Explorer Site — Build Plan

> **Status:** Draft for review. No code yet — this is the blueprint.
>
> **Goal:** A polished, static HTML site (GitHub Pages) that lets a reader
> explore the market-sim electricity-market dispatch model in depth, moving
> from high-level mental model down to LP formulation, data pipeline, capacity
> evolution, policy layers, and calibration — at their own pace. Visualization-
> heavy, code-grounded, intuition-first.

---

## 1. Audience & Learning Goals

### Primary audience

Technical readers who want to understand *how the model works* — analysts
evaluating results, developers extending the code, reviewers assessing
methodology, or curious engineers who want to see inside an LP-based market
simulator. They are comfortable with charts, tables, and light math but are
not assumed to know linear programming or electricity market design.

### What a reader should leave with

1. **Mental model**: electricity demand must be met every hour; generators bid
   costs into a merit order; an LP clears supply against demand; the shadow
   price on the balance constraint *is* the market price.
2. **Data intuition**: where the numbers come from (EIA, CAMPD, eGRID), how
   raw data becomes the FleetArrays the LP consumes, and what the CAMPD
   per-plant binning / tranche offer curves actually look like.
3. **LP literacy**: the flat variable layout, the sparse constraint matrix,
   the objective function components, and how duals become zonal prices —
   without needing to read the code.
4. **Solve-sequence understanding**: why three LP solves (P0→P1→P2), what
   each adds, how startup costs enter pricing, and what the optional
   commitment screen does.
5. **Capacity-evolution logic**: the 6-step annual loop (retire → add →
   retrofit → build → backstop), how prior-year prices drive next-year
   investment, and Wright's-Law learning.
6. **Policy & scarcity awareness**: IRA credits, RPS constraints, carbon
   pricing, ORDC/RCPF scarcity curves, reserve co-optimization — how each
   enters the LP or post-solve overlay.
7. **Network/ISO awareness**: the 7-ISO topology, zonal structure, transmission
   as pipe-and-bubble, and how congestion manifests as price separation.
8. **Calibration understanding**: forecast vs. backcast, what the backcast
   validates, the diagnostic checks, and what makes a run a "keeper."

### Narrative arc (concept unlock order)

```
① Mental Model (the 8,760-hour problem, supply meets demand)
     ↓
② Data Pipeline (raw sources → clean arrays → FleetArrays)
     ↓
③ Fleet & Offer Curves (CAMPD binning, tranches, coal sigmoid, merit order)
     ↓
④ The LP Core (variable layout, constraints, objective, matrix structure)
     ↓
⑤ Solving & Pricing (P0→P1→P2 sequence, duals→LMP, commitment screen)
     ↓
⑥ The Network (7-ISO topologies, transmission, congestion, seams)
     ↓
⑦ Capacity Evolution (6-step loop, retirements, new entry, CCS, storage)
     ↓
⑧ Policy & Scarcity (IRA, RPS, carbon, ORDC/RCPF, reserve co-opt)
     ↓
⑨ Results & Calibration (outputs, backcast validation, diagnostics, dashboard)
     ↓
⑩ Configuration Reference (ScenarioConfig, constants, paths — searchable)
```

Each concept builds on the previous one. The site structure mirrors this arc
but allows random access — a reader can jump to any page from the sidebar.

---

## 2. Information Architecture

### Navigation model

- **Persistent left sidebar** (collapsible on mobile) with the 10 spine pages,
  grouped into three sections:
  - *Foundations* (①–③): Mental Model, Data Pipeline, Fleet & Offer Curves
  - *The Engine* (④–⑥): LP Core, Solving & Pricing, The Network
  - *Evolution & Policy* (⑦–⑨): Capacity Evolution, Policy & Scarcity, Calibration
  - *Reference* (⑩): Config Reference
- **In-page anchor navigation**: a floating right-rail mini-TOC on wide screens
  (auto-generated from `<h2>`/`<h3>` headings) for within-page orientation.
- **Cross-links**: inline links between pages where concepts connect (e.g.,
  "duals→LMP" on the LP page links to the Pricing section of page ⑤).
- **No full-text search in v1** — scope guardrail. The sidebar + anchor nav +
  cross-links are sufficient for 10 pages. Search is a Phase 2+ enhancement
  if needed.

### Sitemap / page inventory

| # | Page | Slug | Content source | Key visuals |
|---|------|------|---------------|-------------|
| 0 | **Landing / Overview** | `index.html` | New (synthesis) | Hero with animated system diagram; quick-nav cards to all pages |
| 1 | **Mental Model** | `mental-model.html` | `01-architecture.md` (high-level) | Animated supply-meets-demand diagram; 24-hour demand trace with stacking gen |
| 2 | **Data Pipeline** | `data-pipeline.html` | `04-data-layer.md` | Data-flow diagram (raw→clean→FleetArrays); source-file inventory table |
| 3 | **Fleet & Offer Curves** | `fleet-offer-curves.html` | `04-data-layer.md` (fleet/binning), `docs/binning-methodology.md` | Interactive merit-order stack; tranche offer-curve builder; coal sigmoid |
| 4 | **The LP Core** | `lp-core.html` | `02-lp-dispatch.md` | Variable-layout block diagram; constraint-matrix sparsity pattern; objective waterfall; energy-balance Sankey |
| 5 | **Solving & Pricing** | `solving-pricing.html` | `02-lp-dispatch.md` (duals), `03-capacity-and-commitment.md` (P0→P1→P2) | P0→P1→P2 sequence diagram; price-duration curve; LMP heatmap; commitment decision tree |
| 6 | **The Network** | `network.html` | `03-capacity-and-commitment.md` (transmission), `iso_configs.py` | Interactive 7-ISO topology map; zone-link force graph; congestion price-split example |
| 7 | **Capacity Evolution** | `capacity-evolution.html` | `03-capacity-and-commitment.md` (capacity) | 6-step animated flowchart; stacked-area capacity & generation over years; retirement waterfall; Wright's-Law learning curve |
| 8 | **Policy & Scarcity** | `policy-scarcity.html` | `05-policy.md` | IRA credit timeline; RPS constraint diagram; carbon-price map; ORDC/RCPF interactive curves |
| 9 | **Results & Calibration** | `results-calibration.html` | `06-results-and-calibration.md` | Calibration diagnostic scorecard; forecast-vs-backcast toggle comparison; result-flow diagram |
| 10 | **Config Reference** | `config-reference.html` | `08-config-reference.md` | Searchable/filterable parameter table; tier badge system; collapsible sections |

**Deep-dive panels** (expandable within pages, not separate pages):
- LP Core → "Expand: Full constraint equations" (KaTeX-rendered math)
- Fleet → "Expand: CAMPD bin assignment algorithm" (step-by-step)
- Network → "Expand: ISO detail" (per-ISO zone/link tables)
- Policy → "Expand: Reserve co-optimization formulation"

---

## 3. Visualization Inventory

| # | Model Concept | Visual Type | Technique | Interactive? | Data Source | Intuition Delivered |
|---|--------------|-------------|-----------|-------------|-------------|-------------------|
| V1 | **System overview** | Animated flow diagram | D3 (custom SVG) | Hover highlights | Schematic | How demand, fleet, LP, prices, and capacity loop connect |
| V2 | **Supply meets demand** | Stacked-area 24h dispatch | D3 area chart | Time scrubber | Illustrative JSON (faithful to real proportions) | Renewables fill first, thermal stacks by cost, price = marginal unit |
| V3 | **Data pipeline flow** | Sankey / directed-graph | D3 (custom SVG) | Hover for details | Schematic | Raw sources → loaders → FleetArrays → LP |
| V4 | **Merit-order stack** | Horizontal stacked bars | D3 bar chart | Hover for unit details; fuel filter | Illustrative JSON (based on real ERCOT fleet composition) | Cheapest generators dispatch first; price set at the margin |
| V5 | **Tranche offer curve** | Stepped line chart | D3 line + area | Toggle fuel type; slider for gas price | Illustrative JSON (per `docs/binning-methodology.md` multipliers) | Each plant's rising cost curve from must-run through peaking |
| V6 | **Coal take-or-pay sigmoid** | Interactive curve | D3 line chart | Gas-price slider moves the sigmoid | Illustrative (sigmoid formula from `fleet.py`) | How gas price determines coal fuel-cost fraction |
| V7 | **LP variable layout** | Colored block diagram | SVG (static, hand-built) | Hover for variable names/counts | Schematic (from VariableLayout) | The flat column vector: P\|W\|S\|Chg\|Dis\|SOC\|Flow\|Slack\|Dump |
| V8 | **Constraint-matrix sparsity** | Block-structure heatmap | D3 (canvas for performance) | Zoom; hover shows constraint type | Schematic (block structure from `build_constraints`) | Sparse, block-diagonal structure; Kronecker tiling across hours |
| V9 | **Objective-function waterfall** | Waterfall chart | D3 bar chart | Hover for component values | Illustrative JSON | How MC = fuel + VOM + carbon + NOx − credits assembles |
| V10 | **Energy-balance Sankey** | Sankey diagram | D3-sankey plugin | Zone selector; hour slider | Illustrative JSON (one zone, representative hour) | Inflows (gen + imports + discharge) = demand + exports + charge |
| V11 | **Duals → LMP** | Annotated constraint diagram | SVG + KaTeX | Static with callouts | Schematic | The dual on the energy-balance row IS the zonal price |
| V12 | **P0→P1→P2 sequence** | Stepped process diagram | D3/SVG animated | Step-through animation | Schematic | Base cost → startup markup → commitment screen |
| V13 | **Price-duration curve** | Sorted line chart | D3 line chart | ISO overlay toggle | Illustrative JSON | 8,760 hours sorted by price; scarcity tail visible |
| V14 | **7-ISO topology map** | Network graph | D3 force layout | Click ISO to expand zones/links | From `iso_configs.py` (zone names, link TTCs) | Zonal structure, transfer limits, import nodes |
| V15 | **Congestion example** | Dual-zone price split | D3 line pair | Hour scrubber | Illustrative JSON | When flow hits TTC, prices diverge between zones |
| V16 | **6-step capacity evolution** | Animated flowchart | D3/SVG with step transitions | Play/step buttons | Schematic (from `evolve_fleet` steps) | Known retire → economic retire → add → CCS → new entry → backstop |
| V17 | **Stacked-area capacity/gen** | Multi-year area chart | D3 stacked area | Fuel toggle; hover year detail | Illustrative JSON (25-year trajectory) | Fleet composition shift over forecast horizon |
| V18 | **Wright's-Law learning** | Log-log scatter + curve | D3 scatter plot | Tech selector | Illustrative (NREL ATB learning rates) | How cumulative deployment drives cost down |
| V19 | **Storage SOC trace** | Multi-line time series | D3 line chart | Duration toggle (4h/8h) | Illustrative JSON (48-hour window) | Charge low-price → discharge high-price; SOC cycles |
| V20 | **Storage value stack** | Stacked bar | D3 bar chart | Static | Illustrative JSON | Arbitrage + capacity value + AS revenue |
| V21 | **IRA credit timeline** | Gantt / timeline bars | SVG (static) | Hover for credit values | From `scenarios.py` IRA fields | Which credits apply when, phase-out cliffs |
| V22 | **ORDC scarcity curve** | Interactive demand curve | D3 line chart | Reserve-level slider | Illustrative (ORDC formula from `policy/`) | LOLP-based penalty rises as reserves fall |
| V23 | **RPS constraint diagram** | Annotated LP row | SVG + KaTeX | Static | Schematic | Annual clean-energy floor; dual = REC price |
| V24 | **Forecast vs backcast toggle** | Side-by-side comparison | CSS + D3 | Toggle switch | Schematic | What changes between modes (data sources, overlays) |
| V25 | **Calibration diagnostic scorecard** | Traffic-light table | HTML/CSS table | Static example | Illustrative (based on real check structure) | PASS/WARN/FAIL per metric per fuel |
| V26 | **Result data flow** | Flow diagram | SVG (static) | None | Schematic | LP solve → DispatchResult → Parquet → aggregation → dashboard |

**Total: 26 visualizations.** ~15 interactive (D3), ~11 static (SVG/CSS).

---

## 4. Data Strategy

### Approach: illustrative JSON with faithful proportions

Most charts use **committed illustrative JSON data** that is faithful to real
model proportions but not raw solver output. This avoids:
- Committing large result files
- Stale data if the model evolves
- Misrepresentation of specific scenarios as "the" answer

### Data file inventory

```
docs/codebase-site/data/
  fleet-merit-order.json      # ~50 generators, realistic ERCOT-like stack
  offer-curve-tranches.json   # Per-fuel tranche multipliers + example plants
  energy-balance-sankey.json  # One zone, one representative hour
  dispatch-24h.json           # 24-hour stacked dispatch (summer peak day)
  price-duration.json         # 8760 sorted prices (illustrative)
  capacity-trajectory.json    # 25-year capacity evolution by fuel
  generation-trajectory.json  # 25-year generation evolution by fuel
  storage-soc-48h.json        # 48-hour SOC trace for 4h and 8h battery
  storage-value-stack.json    # Revenue decomposition for storage entry screen
  iso-topologies.json         # Extracted from iso_configs.py (zones, links, TTCs)
  ordc-curve.json             # ORDC penalty curve data points
  congestion-example.json     # Two-zone price series with binding flow
  learning-curves.json        # Wright's-Law cost trajectories by tech
  mc-waterfall.json           # Marginal cost component breakdown
  calibration-scorecard.json  # Example diagnostic check results
```

### Extraction approach

- **`iso-topologies.json`**: extracted directly from `config/iso_configs.py`
  by a one-time script (`scripts/extract_iso_topologies.py`) that imports the
  ISO registry and serializes zone names, coordinates, links, and TTCs. This
  is the only file derived from live code — it should be regenerated if ISO
  configs change.
- **All other JSON**: hand-curated to be representative. Values sourced from
  docs/codebase documentation (generation mixes, typical prices, capacity
  ranges) and scaled to be internally consistent. Each file includes a
  `_meta` field documenting its provenance.
- **Schematic/structural diagrams** (V1, V3, V7, V8, V11, V12, V16, V23,
  V24, V26): no data files — these are SVG/HTML structures built from the
  code's architecture, not from numeric data.

### What we explicitly do NOT include

- Raw solver output or Parquet files
- Actual backcast results (those live on the backcast dashboard)
- Anything that could be mistaken for a forecast or official result

---

## 5. Tech Stack & Build Approach

### Core stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Markup** | Vanilla HTML | No build step, Pages-deployable, matches repo convention |
| **Styling** | Vanilla CSS (custom properties) | Matches both existing design systems; no preprocessor needed |
| **Charts** | D3.js v7 (CDN) | Already used by learning-hub; full control over interactive viz |
| **Diagrams** | Hand-built SVG | Better control than Mermaid for the specific block/flow diagrams needed |
| **Math** | KaTeX (CDN) | Lightweight, fast, static rendering — no MathJax bloat |
| **Layout** | CSS Grid + Flexbox | Native, no framework overhead |
| **Fonts** | Plus Jakarta Sans + DM Sans (Google Fonts) | Matches learning-hub; more polished than the dashboard's system fonts |
| **Icons** | Inline SVG | No icon library dependency |

### Why not a framework?

- The site is ~11 HTML files with shared CSS/JS — a framework adds build
  complexity for no gain.
- No client-side routing needed — each page is a standalone document.
- Shared components (nav, footer, theme toggle) are small enough to inline
  or include via a tiny JS module that injects them.

### Library loading

All external libraries loaded via CDN with `integrity` hashes and
`crossorigin="anonymous"`:
- `d3.v7.min.js` (~290 KB)
- `katex.min.js` + `katex.min.css` (~120 KB)
- `d3-sankey.min.js` (~15 KB, for V10 only — loaded on that page)

Total external payload: ~425 KB (cached after first page load).

### Performance budget

- First Contentful Paint: < 1.5s on 3G
- Total page weight (HTML + CSS + inline JS + data JSON): < 500 KB per page
  (excluding cached CDN libraries)
- All images as inline SVG (no image requests)
- Data JSON files are small (< 50 KB each) and loaded on demand

### Dark/light mode

- CSS `prefers-color-scheme` media query for auto-detection
- Manual toggle button in the nav (persisted to `localStorage`)
- All colors defined as CSS custom properties with light/dark variants
- D3 charts read CSS custom properties for colors (no hardcoded hex in JS)

### Accessibility

- Semantic HTML (`<nav>`, `<main>`, `<article>`, `<section>`, `<figure>`)
- ARIA labels on interactive elements
- Keyboard navigation for all interactive charts (arrow keys for sliders,
  Enter/Space for toggles)
- Color contrast: WCAG AA minimum (4.5:1 text, 3:1 large text/UI)
- SVG charts include `<title>` and `<desc>` elements
- Reduced-motion: `prefers-reduced-motion` disables animations

### Responsiveness

- Desktop-first (matches repo convention), with breakpoints at:
  - 1200px: sidebar collapses to hamburger
  - 900px: two-column layouts stack
  - 600px: mobile typography scale
- Charts resize via `ResizeObserver` (D3 redraws on container resize)
- Touch targets ≥ 44px on mobile

---

## 6. Design System

### Decision: extend the learning-hub aesthetic

The codebase site adopts the **learning-hub** design language (Plus Jakarta
Sans + DM Sans, navy/cyan palette, card-based layout) rather than the
dashboard's system-font/blue-accent style. Rationale:
- The learning hub is the closest existing analog (educational, visualization-
  heavy)
- Its typography is more polished and distinctive
- Its color tokens are already designed for data visualization
- The codebase site is a natural sibling of the learning hub, not the
  dashboard

### Extended token set

```css
:root {
  /* --- Typography --- */
  --font-heading: 'Plus Jakarta Sans', 'DM Sans', sans-serif;
  --font-body:    'DM Sans', 'Plus Jakarta Sans', sans-serif;
  --font-mono:    'JetBrains Mono', 'SF Mono', 'Consolas', monospace;

  --fs-xs:   0.75rem;    /* 12px — captions, badges */
  --fs-sm:   0.875rem;   /* 14px — secondary text */
  --fs-base: 1rem;       /* 16px — body */
  --fs-lg:   1.125rem;   /* 18px — lead text */
  --fs-xl:   1.5rem;     /* 24px — h3 */
  --fs-2xl:  2rem;       /* 32px — h2 */
  --fs-3xl:  2.75rem;    /* 44px — h1 */

  /* --- Surfaces (light mode) --- */
  --bg:          #F8F9FC;
  --bg-surface:  #FFFFFF;
  --bg-inset:    #F1F3F7;
  --bg-nav:      #1A2744;
  --bg-code:     #1E293B;

  /* --- Text --- */
  --text:        #1E293B;
  --text-muted:  #566370;
  --text-faint:  #94A3B8;
  --text-inverse:#FFFFFF;

  /* --- Borders --- */
  --border:      #D4D8E0;
  --border-soft: #E5E7EB;
  --border-strong:#B0B8C4;

  /* --- Accent (cyan, from learning hub) --- */
  --accent:        #38BDF8;
  --accent-deep:   #0E7490;
  --accent-soft:   rgba(56, 189, 248, 0.12);
  --accent-border: rgba(56, 189, 248, 0.45);

  /* --- Semantic --- */
  --positive: #16A34A;
  --negative: #DC2626;
  --warning:  #D97706;
  --info:     #0284C7;

  /* --- Fuel palette (canonical, from frontend/css/style.css) --- */
  --fuel-gas-cc:   #4A90D9;
  --fuel-gas-ct:   #7BB3E0;
  --fuel-coal:     #8B4513;
  --fuel-nuclear:  #9B59B6;
  --fuel-wind:     #2ECC71;
  --fuel-solar:    #F1C40F;
  --fuel-storage:  #E67E22;
  --fuel-hydro:    #1ABC9C;
  --fuel-oil:      #92400E;
  --fuel-ccs:      #26A69A;
  --fuel-hydrogen: #10B981;
  --fuel-geo:      #D97706;
  --fuel-offshore: #009688;

  /* --- ISO palette (canonical, from docs/DESIGN_SYSTEM.md) --- */
  --iso-ercot:  #22C55E;
  --iso-caiso:  #F59E0B;
  --iso-pjm:    #0EA5E9;
  --iso-nyiso:  #E91E63;
  --iso-neiso:  #9C27B0;
  --iso-miso:   #F97316;
  --iso-spp:    #14B8A6;

  /* --- Spacing --- */
  --sp-xs:  4px;
  --sp-sm:  8px;
  --sp-md:  16px;
  --sp-lg:  24px;
  --sp-xl:  36px;
  --sp-2xl: 56px;
  --sp-3xl: 80px;

  /* --- Radius & elevation --- */
  --radius-sm:  6px;
  --radius-md:  10px;
  --radius-lg:  16px;
  --shadow-sm:  0 1px 3px rgba(0, 0, 0, 0.06);
  --shadow-md:  0 4px 16px rgba(0, 0, 0, 0.08);
  --shadow-lg:  0 8px 28px rgba(0, 0, 0, 0.12);
  --shadow-glow:0 0 20px rgba(56, 189, 248, 0.15);

  /* --- Layout --- */
  --content-max:  1280px;
  --sidebar-w:    260px;
  --nav-height:   56px;
}
```

### Dark-mode overrides

```css
[data-theme="dark"] {
  --bg:          #0F172A;
  --bg-surface:  #1E293B;
  --bg-inset:    #162032;
  --bg-code:     #0D1420;
  --text:        #E2E8F0;
  --text-muted:  #94A3B8;
  --text-faint:  #64748B;
  --border:      #334155;
  --border-soft: #1E293B;
  --border-strong:#475569;
}
```

### Component library

| Component | Description | Used on |
|-----------|-------------|---------|
| **`.sidebar`** | Persistent left nav with section groups, active-page highlight | All pages |
| **`.page-hero`** | Dark navy header with eyebrow, title, lead paragraph | All pages |
| **`.card`** | White surface with border, radius, shadow; accent top-border variant | Landing, several pages |
| **`.fig`** | Figure wrapper: chart container + caption + optional expand toggle | All viz pages |
| **`.fig-controls`** | Toolbar above a chart: toggles, sliders, selectors | Interactive viz |
| **`.callout`** | Highlighted aside (info, warning, key-insight variants) | All pages |
| **`.equation`** | KaTeX-rendered block equation with optional label | LP Core, Policy |
| **`.code-block`** | Syntax-highlighted code snippet (dark bg, mono font) | Data Pipeline, Config |
| **`.data-table`** | Styled table with header, striped rows, numeric alignment | Config Ref, several |
| **`.badge`** | Small pill label (tier badges, fuel-type tags, ISO tags) | Config Ref, Fleet |
| **`.tabs`** | Tab group for switching between views in the same container | Network (per-ISO), Policy |
| **`.tooltip`** | Hover/focus tooltip for chart elements | All interactive viz |
| **`.breadcrumb`** | Previous/next page links at bottom | All pages |
| **`.toc-rail`** | Right-rail floating mini-TOC (auto from headings) | All pages (wide screens) |
| **`.theme-toggle`** | Dark/light switch in nav | All pages |

### Motion guidelines

- Page transitions: none (multi-page, not SPA)
- Chart enter animations: fade-in + slight upward slide (300ms ease-out)
- Interactive state transitions: 200ms ease
- Step-through animations (P0→P1→P2, capacity evolution): 600ms per step
- `prefers-reduced-motion`: all durations → 0

---

## 7. File & Directory Layout

```
docs/codebase-site/
├── index.html                    # Landing / overview (page 0)
├── mental-model.html             # Page 1
├── data-pipeline.html            # Page 2
├── fleet-offer-curves.html       # Page 3
├── lp-core.html                  # Page 4
├── solving-pricing.html          # Page 5
├── network.html                  # Page 6
├── capacity-evolution.html       # Page 7
├── policy-scarcity.html          # Page 8
├── results-calibration.html      # Page 9
├── config-reference.html         # Page 10
├── css/
│   └── site.css                  # Full design system + component styles
├── js/
│   ├── shared.js                 # Nav injection, theme toggle, TOC builder
│   ├── chart-utils.js            # D3 helpers (responsive resize, tooltips,
│   │                             #   color scale from CSS vars, axis formatting)
│   ├── viz-merit-order.js        # V4 merit-order chart
│   ├── viz-offer-curve.js        # V5 tranche offer curve
│   ├── viz-coal-sigmoid.js       # V6 coal take-or-pay sigmoid
│   ├── viz-dispatch-24h.js       # V2 stacked 24h dispatch
│   ├── viz-sparsity.js           # V8 constraint matrix sparsity
│   ├── viz-waterfall.js          # V9 MC waterfall
│   ├── viz-sankey.js             # V10 energy-balance Sankey
│   ├── viz-p012-sequence.js      # V12 P0→P1→P2 animated sequence
│   ├── viz-price-duration.js     # V13 price-duration curve
│   ├── viz-iso-topology.js       # V14 ISO network graph
│   ├── viz-congestion.js         # V15 congestion price-split
│   ├── viz-capacity-flow.js      # V16 6-step capacity evolution
│   ├── viz-stacked-area.js       # V17 multi-year stacked area
│   ├── viz-learning.js           # V18 Wright's-Law curve
│   ├── viz-storage-soc.js        # V19 storage SOC trace
│   ├── viz-storage-value.js      # V20 storage value stack
│   ├── viz-ordc.js               # V22 ORDC scarcity curve
│   └── viz-config-table.js       # V25 config reference filter/search
├── data/
│   ├── fleet-merit-order.json
│   ├── offer-curve-tranches.json
│   ├── energy-balance-sankey.json
│   ├── dispatch-24h.json
│   ├── price-duration.json
│   ├── capacity-trajectory.json
│   ├── generation-trajectory.json
│   ├── storage-soc-48h.json
│   ├── storage-value-stack.json
│   ├── iso-topologies.json
│   ├── ordc-curve.json
│   ├── congestion-example.json
│   ├── learning-curves.json
│   ├── mc-waterfall.json
│   └── calibration-scorecard.json
├── img/                          # Only if needed for static SVG exports
│   └── .gitkeep
├── PLAN.md                       # This file
└── PROMPT-PACK.md                # Build prompts for follow-on sessions
```

### Shared files created in Phase 0 (collision-prevention)

These files MUST exist before any Phase 1 parallel prompt runs:
- `css/site.css` — full design system
- `js/shared.js` — nav, theme toggle, TOC
- `js/chart-utils.js` — D3 helpers
- `index.html` — landing page (the "golden" quality-bar example)
- All `data/*.json` files — so parallel pages can reference them

---

## 8. Risks, Open Questions & Non-Goals

### Risks

| Risk | Mitigation |
|------|-----------|
| Illustrative data drifts from model reality | Each JSON file has `_meta.source` citing the code/doc it represents; QA phase verifies |
| D3 charts are complex to build correctly | `chart-utils.js` provides shared patterns; golden page sets the bar |
| 26 visualizations is ambitious | Prioritize: V2, V4, V5, V7, V10, V12, V14, V16, V17 are must-haves; others can be static SVG fallbacks |
| Dark mode doubles CSS/chart work | CSS custom properties + D3 reading from CSS vars handles most; test both in QA |
| CDN availability | Fallback: vendored copies in `js/vendor/` if CDN is unreliable |

### Open questions (for approval)

1. **Separate site vs. integrated into learning-hub?** Plan assumes separate
   (`docs/codebase-site/`) because this is a reference explorer, not a
   scrollytelling narrative. The learning hub is concept-first; this is
   code-first. They can cross-link. Confirm?
2. **JetBrains Mono for code?** It requires a Google Fonts load (~50 KB).
   Alternative: use `font-mono` from system stack (Consolas/SF Mono). The
   plan uses JetBrains Mono for the polished look, falling back to system
   mono.
3. **Landing page on root index or nested?** Plan puts the site landing at
   `docs/codebase-site/index.html`. The root `index.html` would need a new
   card linking to it (simple addition). Confirm?

### Non-goals (scope guardrails)

- **No live solver integration.** Charts use static illustrative data, not
  live model runs.
- **No user input / scenario builder.** This is a documentation site, not a
  simulation tool.
- **No full-text search in v1.** Sidebar + TOC + cross-links are sufficient.
- **No server-side rendering or build step.** Pure static files.
- **No CMS or markdown-to-HTML pipeline.** Content is authored directly in
  HTML with the component library.
- **No duplication of the backcast dashboard.** Calibration page explains the
  process and links to the dashboard; it does not replicate it.
- **No video or audio.** Animations are CSS/D3 only.
- **No mobile-first design.** Desktop-first, responsive down to mobile.
  Charts are readable but not fully interactive on small screens.

---

## 9. Prompt Pack — Build Prompts for Follow-On Sessions

See **[PROMPT-PACK.md](PROMPT-PACK.md)** (sibling file).
