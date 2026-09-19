# PLAN — Marginal Abatement Cost page (plan + mock)

*Session: `claude/marginal-abatement-cost-page-ljctty`, 2026-09-19. Plan-first; the deliverable
in this session is this plan plus a **synthetic mock**. Nothing is registered, no run is solved,
`frontend/data/backcast/**` is untouched.*

## Context

The LP now emits `DispatchResult.marginal_emission_rate` (commit `fba0ecd7`) — the
**emissions dual** `r_B' B^-1`: the same triangular solve as the zonal price with the
per-generator CO2 rate vector swapped in for the cost vector. It is *not* the emission
rate of the unit whose `mc` equals the price; at a tranched, reserve-co-optimized vertex
that unit is not even well defined. `scripts/run_calibration_full.py:1555` persists it
per zone-hour into `hourly/system_<year>.parquet`.

That unlocks a number the program could not previously state: **what it costs, per tonne
of CO2, to abate with new wind and new solar on each modeled grid.** Nothing on the site
carries it today. This adds one new page — `docs/codebase-site/marginal-abatement.html` —
as a sibling of `backcast-runs.html` / `calibration-status.html` / `mechanism-matrix.html`,
in the same navigation and the same Observatory design system.

**Verified blocking fact, and it shapes the whole design.** No committed sidecar carries
the column yet:

```
for f in results/calibration/*/hourly/system_*.parquet; do strings "$f" | grep -c marginal_emission_rate; done
→ 0 for all 58 bundles          (`price`, `demand`, `zone` etc. all found by the same probe, so the probe works)
```

Every keeper predates `fba0ecd7`; `PRECOMMIT-soco-53c-2026-09-19.md` §3 records SOCO-53c as
the first lane to solve past it. So on the day this page ships **all nine regions are
PENDING**, and they light up one at a time as each lane's control replay lands. The PENDING
state is not an edge case — it is the page's normal condition for the next while, and it is
designed first.

This session is **plan + mock only**: synthetic data, labelled synthetic, nothing registered,
`frontend/data/backcast/**` untouched.

---

## 1. The underlying number

```
MAC ($/tCO2) = (cost per delivered MWh − energy capture price) / MER_tech

cost per delivered MWh = compute_lcoe(tech, year, config) × cf_base / cf_expected
energy capture price   = Σ(price × tech_shape) / Σ(tech_shape)
MER_tech               = Σ(MER   × tech_shape) / Σ(tech_shape)   ← results.emissions.weighted_marginal_rate
```

Reported **twice**, post-IRA and pre-IRA. They differ by ~3× and conflating them is the
single easiest way to publish a wrong number, so the page never shows one without the other
— the hero tile carries both, and the ranking chart is a dumbbell whose *connector length
is the credit*.

- **post-IRA** — `compute_lcoe` as shipped (`model/capacity_evolution/new_entry.py:525`).
- **pre-IRA** — strip both credits at their correct layers, exactly as `compute_lcoe` applies
  them: wind adds back `wind_ptc_levelized_per_mwh(config)` **$/MWh** (levelized
  `CRF(life)/CRF(window)`, not full-life); solar re-annualizes from `capex_wright_per_kw`
  instead of `capex_after_credit_per_kw` — i.e. undo `capex *= 1 − ira_itc_solar` *before*
  the CRF, never as a $/MWh subtraction.

Sanity check at shipped constants (wind 1676.6 $/kW, FOM 33.7, life 30, `base_cf` 0.38;
solar 1562.2 / 22.3 / 30 / 0.27): wind LCOE ≈ $50.7 pre / ≈ $35.2 post; solar ≈ $62.7 pre /
≈ $46.7 post. Against plausible capture prices and MERs that lands post-IRA MAC in the
~$1–50/t band and pre-IRA ~$29–125/t — the magnitudes the mock is seeded at.

### Two decisions this plan pins, both stated on the page

**(a) Which price the capture calculation uses → the settled `price` column, overlays
included.** `price` carries the ERCOT RTORDPA / DAM-AS / ORDC post-solve adders;
`marginal_emission_rate` is written RAW against the LP's own energy dual, deliberately
(`run_calibration_full.py:1555`: an overlay leaves dispatch untouched, so it cannot move a
CO2 response). A project is *paid* the settled price, so the numerator uses it. The mismatch
is then disclosed **numerically, not asserted**: the overlay columns (`rtordpa_overlay`,
`ordc_adder`, `dam_as_overlay`) are persisted in the same sidecar, so the builder writes
`capture_price_overlay_usd_per_mwh` and the page shows it. Verified scope: the overlay branch
is guarded by `ercot_*` flags only (`run_calibration_full.py:1382–1397`), and the ERCOT keeper
config has `ercot_rtordpa_overlay: true` + `ercot_ordc_cap_dual_adder: true`, so the delta is
non-zero for ERCOT and **exactly 0.0 for all eight other regions**.

**(b) The zonal collapse → load-weighted, v1.** MER and `price` are per zone-hour;
`class_hourly_<year>.parquet` is ISO-wide `(year, pass, klass, hour, mw)` with no zone
column, and I confirmed no committed sidecar carries per-zone VRE (`network_<year>.parquet`
is link flows only). So:

```
MER_iso(t)   = Σ_z MER(z,t)·demand(z,t) / Σ_z demand(z,t)
price_iso(t) = Σ_z price(z,t)·demand(z,t) / Σ_z demand(z,t)
```
then weight both by the ISO-wide `wind` / `solar` shape. Load-weighting is the neutral,
well-defined collapse and matches the existing `weighted_marginal_rate(mer, demand)`
convention. **The bias, named on the page:** VRE is concentrated in particular zones (ERCOT
West/Panhandle, CAISO SP15, MISO North/West); in a congested hour that zone's MER differs
from the load centre's and this collapse cannot see it. The direction is not signable a
priori. **Routed, not absorbed:** the LP already has per-zone `wind_dispatched` /
`solar_dispatched`; a `hourly/vre_zone_<year>.parquet` sidecar closes it exactly. That is a
v2 item on the solve path, not this page's.

**One input is not in any sidecar: installed wind/solar MW,** needed for `cf_expected`. The
builder resolves it from `data/renewables.py::_eia860_monthly_capacity` at the keeper's
`run_config_<year>.json` vintage — a fleet read, still zero LP — and writes the MW **and its
provenance string** into the sidecar so the page can show them. `cf_expected` is then the
*delivered* CF (`mean(tech_shape)/installed_MW`), which puts curtailment inside the cost per
delivered MWh; the page says so, since it qualifies caveat 4. **If capacity cannot be
resolved, the ISO-year is PENDING — never estimated.**

---

## 2. Data contract — which files are committed, which are generated

Mirrors the backcast/forecast split exactly (sidecars committed, index generated at deploy).

| Path | State | Written by |
|---|---|---|
| `frontend/data/mac/<ISO>-<year>.json` | **COMMITTED** | `scripts/build_mac_sidecar.py` (pandas; run in the ISO's own lane) |
| `frontend/data/mac/manifest.js` | **GENERATED** (gitignored) | `scripts/build_mac_sidecar.py --reindex` (stdlib only; deploy is its single writer) |
| `docs/codebase-site/marginal-abatement.html` | committed | this session |

The page reads `../../frontend/data/mac/` — which resolves correctly both under
`_site/docs/codebase-site/` on Pages and from the repo for a local `file://` preview, so **no
copier script and no second data root is needed**.

**Sidecar shape**, per ISO-year (a few KB; the two arrays are the whole size):

```jsonc
{
  "iso": "ERCOT", "year": 2024, "status": "ready",
  "source_run": "2026-09-09-ercot265-receipts-fallback",
  "bundle": "results/calibration/ercot265_receipts_fallback",
  "git_sha": "…", "built_at": "…", "pass": "P1",
  "scalars": {
    "wind":  { "mac_post_ira": 11.8, "mac_pre_ira": 44.2,
               "lcoe_post_ira": 35.2, "lcoe_pre_ira": 50.7,
               "cost_per_delivered_mwh_post_ira": 33.4, "cost_per_delivered_mwh_pre_ira": 48.2,
               "capture_price": 28.1, "mer_tech": 0.452,
               "cf_base": 0.38, "cf_expected": 0.401,
               "installed_mw": 38210.0, "installed_mw_provenance": "EIA-860 monthly, 2024 vintage" },
    "solar": { … }
  },
  "system": { "mer_load_weighted": 0.481, "mer_mean": 0.469,
              "zero_mer_hour_share": 0.061, "import_marginal_hour_share": 0.004,
              "capture_price_overlay_usd_per_mwh": 3.42,
              "load_weighted_price": 31.7 },
  "mer_duration": [ /* 200 evenly-spaced percentiles, tCO2/MWh */ ],
  "mer_month_hour": [ /* 12 × 24, tCO2/MWh, load-weighted */ ],
  "shape_month_hour": { "wind": [12×24 normalised], "solar": [12×24 normalised] },
  "approximations": ["load-weighted zonal collapse", "ISO-wide VRE shape", …]
}
```

`build_mac_sidecar.py` is **zero-LP**: it reads `hourly/system_<year>.parquet` (filtered to
`pass == "P1"`) + `hourly/class_hourly_<year>.parquet` from the designated keeper bundle, plus
`run_config_<year>.json` to rebuild the `ScenarioConfig` for `compute_lcoe`. **It refuses,
loudly, when `marginal_emission_rate` is absent from the parquet** — that refusal is what
keeps an ISO honestly PENDING instead of silently zero.

---

## 3. Page structure

One `content-section`, page-local `<style>`, classic `<script>` at the bottom — the
`mechanism-matrix.html` archetype (the closest sibling: a committed-data page that is a pure
renderer). Adds one `nav.js` entry under **Backcast** → *Marginal Abatement*.

1. **SYNTHETIC banner** — full-bleed, high-contrast, sticky under the nav, unmissable. Present
   only in the mock; removed by the commit that first wires real data.
2. **Hero banner** — reads as a *finding*, not a legend: one sentence naming the cheapest and
   dearest grid to abate on at the selected year/tech, then a KPI row of per-region stat tiles
   (post-IRA $/t large, pre-IRA beneath, MER as the sub-label). With zero regions ready it says
   so plainly and names what lands first. A `n of 9 grids measured` progress strip sits beside it.
3. **Controls** — `seg-ctrl` for year (2023 / 2024 / 2025) and tech (wind / solar / both), and an
   ISO focus selector. Hash state `#iso=ERCOT&year=2024&tech=wind`, matching the sibling pages.
4. **Charts** — §4.
5. **Caveats** — a visible panel above the charts, not footnotes. §5.
6. **Method** — the formula, the price decision (a), the zonal collapse (b), and the file list.

### The PENDING state, designed deliberately

- The ISO roster is **always all nine** (`_ISO_BUILDERS`: ERCOT, CAISO, MISO, PJM, NYISO,
  NEISO, SPP, NWPP, SOCO). A region is never dropped for lack of data — a short chart would
  read as "these are the grids."
- A pending region renders as a dashed-border card carrying: the word **PENDING**, the reason
  (*its keeper predates the emissions dual*), the **exact blocking artifact path**
  (`results/calibration/<bundle>/hourly/system_<year>.parquet → no marginal_emission_rate column`),
  and what unblocks it (*that lane's next control replay*).
- In the ranking chart pending regions are **named rows with no marks** and a right-aligned
  `pending` chip. Never a zero, never a dash that could read as zero, never an interpolation,
  never a bar of unknown length.
- Partial years are per-cell: a region ready in 2024 but not 2023 shows ready 2024 and pending
  2023, never a carried-forward value.
- **Rule 25 `[R-ISO-SCOPE]`:** no region's number ever fills another's cell. A pending cell
  stays pending; there is no fallback, no regional average, no "typical" value anywhere in the
  render path.

---

## 4. Chart inventory — each justified, one modified, one dropped

Loading the `dataviz` skill first is done; `scripts/validate_palette.js` runs here (node
present) and gates the categorical palette before any color ships. Light and dark both work
via the site's `.section-light` / `.section-dark` rhythm (this system has **no global dark
toggle** — dark is a section class, so every chart is drawn twice under test, not flipped).

| # | Chart | Form (dataviz heuristic) | Why it earns its place |
|---|---|---|---|
| 1 | **MAC ranking across regions**, selected year + tech | **Dumbbell** — "before → after per item", one hue two shades | The hero's evidence. Post-IRA and pre-IRA are two values per region, and the *connector length is the IRA credit* — the 3× conflation becomes impossible to make by looking at it. A grouped bar would let a reader read one number and walk away. |
| 2 | **MER duration curve**, per region | **Emphasis** — selected region accent, others in de-emphasis gray | The only view where "it is not an average" is visible, and the only place caveat 2 is *shown* rather than claimed: the flat zero tail at the right is the zero-carbon-and-import share, shaded and labelled. Emphasis rather than 9 categorical lines — past the 7–8 token ceiling a 9th hue is indistinguishable under CVD. |
| 3 | **Month × hour-of-day MER heatmap**, one region-year | **Heatmap**, sequential one hue | This is the *mechanism* by which wind's and solar's MACs differ inside one market. Without it the two numbers look like two assumptions. A shape-weight overlay toggle (wind / solar) shows which cells each technology actually earns. |
| 4 | **Cost-stack waterfall — MODIFIED to $/MWh only** | **Waterfall**, then a separate division callout | As briefed it crossed units mid-chart ($/MWh → $/tonne), which is a two-scale chart wearing a bridge costume. Rebuilt as: national LCOE → CF adjustment → −PTC/ITC → −capture price = **net cost gap $/MWh**, single axis, single unit; then one large callout dividing by MER to reach $/tonne. Earns its place as the audit trail that makes the headline checkable. |
| — | Capture-price vs MER scatter | **DROPPED** | All-pairs forms cap at three series; #1 and #3 already carry it. |
| + | **Zero-share meter**, per region | **Meter** — "a single ratio against a limit" | Added. Caveat 2 asks the reader to size the import/zero-carbon understatement themselves — a meter is the form for that, and it discharges the caveat visibly instead of in prose. Large in CAISO and NEISO. |
| + | **Per-region stat tiles** in the hero | **KPI row**, not a one-bar chart | The form table's own answer for a handful of headline numbers. |

Every chart: legend present for ≥2 series, ≤4 also direct-labelled, hover tooltip by default,
a table view behind a toggle, text in ink tokens never series color, recessive grid.

---

## 5. Caveats the page carries visibly

A bordered panel above the charts, plus the two that have a *chart* (2 → the duration curve's
shaded tail and the meter; 3 → the heatmap's national-capex note).

1. **The dual is one-sided at a degenerate vertex and HiGHS reports the DOWN derivative.**
   Correct for abatement — a new VRE MWh removes net load — but it is *not* the cost of serving
   one more MWh. (Pinned both ways by `tests/unit/model/test_marginal_emission_rate.py`.)
2. **Zero-carbon and IMPORT columns carry rate 0 by design** (G-E3, `import_nodes.py:100–104`),
   so an import-marginal hour reads 0 and understates true system consequence. The per-region
   zero-share meter is on the page so a reader can size it.
3. **New-build capex and base CF are NATIONAL** — `cf_base` 0.38 wind / 0.27 solar in every
   region. Regional differences come through capture price and expected CF, **not** through
   resource-quality-differentiated capex.
4. **LCOE excludes integration, interconnection and transmission.** Curtailment enters *only*
   through `cf_expected` being the incumbent fleet's delivered CF — a proxy for a new project's,
   not a project-specific curtailment estimate.
5. **Since rule 22's `[R-HOLDOUT]` removal there is no certified out-of-sample year anywhere in
   this program.** These are model-SELECTION numbers. The page states this in the hero, not only
   in the caveat panel, and nothing on it implies forecast skill.
6. **v1 approximations** — load-weighted zonal collapse against an ISO-wide VRE shape; settled
   price (overlays in) against a raw MER, with the overlay $/MWh shown.

---

## 6. Files

**This session (plan + mock):**
- `docs/codebase-site/marginal-abatement.html` — new, the mock, synthetic data inline + banner.
- `docs/codebase-site/js/nav.js` — one line under **Backcast**. (269 lines, under rule 27's
  300-line bar; edited locally regardless.)
- `docs/handoffs/PLAN-marginal-abatement-page-2026-09-19.md` — this plan, committed.

**The follow-up that wires real data (NOT this session):**
- `scripts/build_mac_sidecar.py` — new; `--iso/--year` (pandas, writes the committed sidecar)
  and `--reindex` (stdlib, writes `manifest.js`).
- `frontend/data/mac/<ISO>-<year>.json` — committed, one per region-year as lanes land.
- `.gitignore` — `frontend/data/mac/manifest.js`, beside the existing forecast block.
- `.github/workflows/deploy-pages.yml` — **one line** in the existing "Assemble" step
  (`python3 scripts/build_mac_sidecar.py --reindex --site-dir _site`) and `frontend/data/mac/**`
  is already covered by the `frontend/**` path filter. **No new workflow** (private repo, billed
  minutes).

Not touched: `backcast-runs.html`, `calibration-status.html`, `frontend/data/backcast/**`,
`src/market_sim/**`, any bundle.

---

## 7. Verification

1. `node <dataviz>/scripts/validate_palette.js "<hexes>" --mode light` and `--mode dark` — must
   PASS the lightness band, chroma floor, adjacent-pair CVD ΔE, the normal-vision floor and
   contrast. Fixed before any color ships.
2. Open the mock in a browser; screenshot light and dark; eyeball for label collisions, overflow
   and geometry (the validator checks color, not layout).
3. **Drive the PENDING path explicitly** — flip the synthetic fixture to `0 of 9 ready`,
   `1 of 9`, and `mixed years`, and confirm: no zero renders, no chart silently shortens, the
   hero still reads as a sentence, and every pending cell names its blocking artifact.
4. Run the **`accessibility-audit`** skill against the page and fix everything it reports.
5. Confirm the nav entry is active-highlighted on this page and that the three sibling pages
   render unchanged (`git diff --stat` shows only the one nav line outside the new file).
6. Hash round-trip: `#iso=CAISO&year=2025&tech=solar` restores state on reload.
7. Commit plan + mock to `claude/marginal-abatement-cost-page-ljctty` and push. No PR, no
   dashboard registration, no `frontend/data/backcast/**` write.

---

## 8. REVISION — owner review, same day

The first mock was rejected as too long, too jargony, and too dependent on knowing this repo.
Four instructions, and what each changed.

**(1) "I don't need to see every ISO summarized together the whole way thru."** The page is now
two parts. The top is **one chart** — wind and solar together, every grid, for the selected year.
Below it, **everything is one grid at a time**, behind a row of grid buttons. The per-grid KPI tile
grid, the nine-line duration curve, the nine-row zero-share meter list and the pending-card grid
are all gone; each collapsed into its single-grid form or was cut. Page height fell **5,517 → 3,522 px**
(−36%) in the default state, and the empty state fell to 2,568.

**(2) "Simpler explanation — some of this isn't digestible."** Named as the example:
*"Zero-rate hour share — size caveat 2 yourself."* That panel is **deleted**, not reworded. So is
every cross-reference of the "caveat 2" kind. Headings are now questions a reader actually has —
*When is the grid dirtiest? · How much does it vary? · Where the cost comes from* — and the four
caveats are written without a single rule number, gap id, file path or commit. The method section
is three sentences and one line of arithmetic.

**(3) "Imports should be given an emission rate."** Done, as a real toggle rather than a footnote.
Imported power is charged the **average emission rate of the grid it came from**, applied after the
fact, and **this is the default**. The `Ignored` setting reproduces the old treatment for
comparison. It moves what it should: **CAISO wind $56 → $44**, NWPP wind $42 → $40, while ERCOT and
SPP — which import almost nothing — do not move at all. The duration curve honours the toggle too:
the flat run of exact zeros is the tail where the marginal resource emits nothing *on this grid*,
and counting imports lifts that share of it onto the source region's rate and re-sorts, so the
chart shows the same quantity the headline does. Leaving a visible zero cliff under a headline that
counts imports would have been a lie. **The heatmap stays raw** and now says so in words — it is
emissions *at power plants on this grid* — because the fixture has no hour-level import split and
distributing the lift across 288 cells would be invented precision.

**(4) "Get rid of the self-referential bullshit."** Every reader-facing mention of a commit hash, a
bundle path, a parquet column, a lane, a control replay, a rubric rule or a criterion id is gone. A
grid with no data now says **`pending`** and nothing else. The renderer carries a standing comment
saying the page must read standalone. What survives is one line in the synthetic banner naming the
placeholder data file — which is about *this mock*, not the model, and leaves with it.

**What did not change:** the pending discipline (full roster always, never a zero, never an
interpolation, no dollar axis when nothing is measured), the with/without-credits pairing shown
everywhere, the committed-sidecar / generated-index data contract in §2, and the zonal-collapse
decision in §1(b).

### Files, after the revision

| File | Lines | What it is |
|---|---:|---|
| `docs/codebase-site/marginal-abatement.html` | ~470 | the page |
| `docs/codebase-site/js/marginal-abatement.js` | ~640 | the renderer |
| `docs/codebase-site/data/marginal-abatement-synthetic.js` | 124 KB | **synthetic — delete with the banner** |
| `docs/codebase-site/js/nav.js` | +1 | one nav entry |

The sidecar in §2 gains three fields for the import correction: `import_emission_rate`,
`import_source` (a plain-English phrase the page prints), and a per-technology
`import_marginal_share`, from which `mer_tech_with_imports` and the `*_with_imports` costs are
derived. Arithmetic re-verified: **0 mismatches** over 27 grid-years × 2 technologies, on both the
raw and the import-corrected path.

### Verification after the revision

Palette re-validated for the new wind/solar pair, which now share one chart and so are a genuine
categorical pair: **`#2A78D6` / `#EB6834` light and `#4589D6` / `#D4753E` dark, ALL CHECKS PASS**.
(The site's own `--wind` / `--solar` tokens were re-confirmed unusable as a pair: ΔE 5.7 under
protanopia, below the floor.) Contrast re-audited over every text node in all three data states:
**clean on this page**. One latent trap was fixed while there — the selected grid button's ink was
pinned to a dark navy that works on the dark section's light accent but would have been 2.2:1 if
the picker ever moved to a light section; it now flips with the accent. No console errors, no
horizontal scroll at 390 px, and the pending invariants still hold in the empty state: **0** bars,
**0** dollar ticks, 9 named rows.

The pre-existing `shared.css:395` mobile-nav finding (3.2:1, all 23 pages) is still **named and
left** — it is not this page's.
