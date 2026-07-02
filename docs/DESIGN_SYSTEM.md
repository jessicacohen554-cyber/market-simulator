# Canonical Color Palettes

> **Status (2026-06-19).** This file used to document a `dashboard/` component
> library — a Chart.js-based design system (`dashboard/styles/shared.css` +
> `dashboard/js/{nav,shared-header,canvas-banners,chart-colors,scroll-observer,shared-footer}.js`).
> That library was never linked from any page and was never staged by the Pages
> deploy, so it shipped nowhere; it has been removed (see `docs/frontend-audit.md`).
> The cross-references it carried to `PIPELINE.md` / `SPEC.md` / `CLAUDE.md` were
> stale too — none of those files exist.
>
> The **live** design system is `frontend/css/style.css` (Plotly/d3), used by the
> landing page, the `frontend/` results dashboard and `model-updates.html`;
> the codebase-site backcast pages use `docs/codebase-site/css/shared.css`.
> The learning hub has its own (`learning-hub/shared/scrollytell.css`).
>
> **This file is retained as the canonical hex record only.** The deployed
> backcast dashboard pages (`docs/codebase-site/backcast-runs.html` /
> `calibration-status.html`, via `--iso-*` vars in `docs/codebase-site/css/shared.css`)
> color-code the ISO toggle and header badge from the **ISO palette** below and
> cite this file as their source — so the ISO table is load-bearing. The resource
> and semantic palettes are the sole written record of the colors that lived in
> the deleted `chart-colors.js`. Note that `frontend/css/style.css` defines its
> **own**, different resource hexes (e.g. `--solar #F1C40F`, `--wind #2ECC71`,
> `--nuclear #9B59B6`); the resource palette here is the Chart.js library's, not
> the live one.

## ISO palette — live (used by the codebase-site backcast pages)

| ISO | CSS Variable | Hex |
|-----|-------------|-----|
| CAISO | `--iso-caiso` | `#F59E0B` |
| ERCOT | `--iso-ercot` | `#22C55E` |
| PJM | `--iso-pjm` | `#0EA5E9` |
| NYISO | `--iso-nyiso` | `#E91E63` |
| NEISO | `--iso-neiso` | `#9C27B0` |
| MISO | `--iso-miso` | `#F97316` |

Transparent variants are the same hex at 12% opacity (`--iso-caiso-t`, …).

## Resource palette — reference (from the retired `chart-colors.js`)

| Resource | Hex |
|----------|-----|
| Solar | `#F59E0B` |
| Wind (Onshore) | `#22C55E` |
| Offshore Wind | `#009688` |
| Hydro | `#0EA5E9` |
| Nuclear | `#6366F1` |
| CCS-CCGT | `#26A69A` (per `chart-colors.js`) / `#64748B` (older doc table) |
| Clean Firm | `#6366F1` |
| Battery 4hr | `#06B6D4` |
| Battery 8hr | `#0891B2` |
| LDES | `#E91E63` |
| Green H₂ | `#10B981` |
| Geothermal | `#D97706` |
| Storage | `#EF4444` |
| Gap | `#D1D5DB` |
| Fossil Gas | `#6B7280` |
| Fossil Coal | `#374151` |
| Fossil Oil | `#92400E` |
| Solar+Batt 4hr | `#E6890B` |
| Solar+Batt 8hr | `#CC7A0A` |
| Wind+Batt 4hr | `#1AA34E` |
| Wind+Batt 8hr | `#158F42` |

Transparent fills were the same hex at 55% opacity; light backgrounds at 8%.

## Semantic palette — reference (from the retired `chart-colors.js`)

| Role | Hex |
|------|-----|
| Positive | `#16A34A` |
| Negative | `#DC2626` |
| Warning | `#D97706` |
| Info | `#0284C7` |
| Accent | `#38bdf8` |
| Muted | `#6B7280` |
