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

## 8. What the mock actually built, and what the build changed

Committed in this session:

| File | Lines | What it is |
|---|---:|---|
| `docs/codebase-site/marginal-abatement.html` | ~530 | the page — markup, page-local tokens, caveats, method |
| `docs/codebase-site/js/marginal-abatement.js` | ~690 | the renderer: hand-rolled SVG, no CDN dependency |
| `docs/codebase-site/data/marginal-abatement-synthetic.js` | 117 KB | **the synthetic fixture — delete with the banner when real data lands** |
| `docs/codebase-site/js/nav.js` | +1 | one nav entry under **Backcast** |

**What is real in the fixture, and only this:** the LCOEs, computed from the shipped
`NEW_ENTRY_COSTS` constants through the real `compute_lcoe` formula — wind $50.71 pre / $35.15
post, solar $62.66 pre / $46.69 post. Every capture price, marginal emission rate, expected CF,
installed MW, duration curve and month × hour grid is **invented**. The MACs are then computed
from those invented inputs with the real formula, so a reviewer can check any tile against its own
waterfall — verified: **0 arithmetic mismatches across all 27 grid-years × 2 technologies.**
Resulting spread: post-IRA −$10 to $64/t, pre-IRA $24 to $124/t. The one negative
(NEISO wind 2023) is kept deliberately: it is a real result shape — capture price above cost, so
abatement paid for itself — and it stress-tests a zero-crossing axis.

**Palette, validated not eyeballed** (`dataviz/scripts/validate_palette.js`):

- sequential light `#6FB9E0 #3E9ACB #1B82B4 #0E5E88 #08405E` — **ALL PASS** (ordinal)
- sequential dark `#BDE6F8 #82CAEB #4AA6D4 #2E7B9C #31586F` — **ALL PASS** (ordinal)
- The site's own `--wind` / `--solar` tokens were **rejected as a pair**: ΔE 5.7 under protanopia,
  below the 6–8 floor. They are not needed — technology is a *toggle*, not a series, and region
  identity is **nominal categorical**, so every region takes the same slot-1 hue and
  position/length carries the value. That is why a nine-region chart needs no nine-hue palette.

**Defects the render pass caught and fixed** (the validator checks color, not layout — each of
these was found by opening the page, not by reading the code):

1. `.mac-fig svg { width:100% }` captured the pending chip's own 12 px icon and inflated it to the
   figure width — a full-panel clock. Fixed with an explicit chip override.
2. The banner's `<code>` inherited the site's light-surface style (`#0369A1` on `#7C2D12`):
   **invisible**. The banner now supplies its own.
3. `.ax-title { text-transform: uppercase }` rendered the unit as `TCO₂/MWH`.
4. The dumbbell's post-IRA label collided with the row name at phone width whenever a grid sat near
   the domain minimum. Moved to the **left gutter** — collision-free at every width, no per-row
   special-casing.
5. In the empty state the ranking chart still drew a dollar axis across nine empty rows, and three
   legends sat over empty panels. Both suppressed: **a $-scale over no data invites the reader to
   place the missing values near zero, which is the one reading this page must never permit.**

**Accessibility.** Audited by walking every text node in the live browser and compositing each
against its effective background (including SVG fills and the `.section-dark` gradient, which
computes as transparent), in all three data states. One finding on this page: the pending status
color `#B45309` measured **4.49:1** on the pending card's own tinted surface — one hundredth under
AA — stepped to `#9A4708` (5.73:1 there, 6.40:1 on white). **The page is now clean.**

One finding is **pre-existing and NOT this page's**: `.top-nav__mobile-section-label` in
`shared.css:395` is `rgba(255,255,255,0.35)` on navy = **3.2:1**, failing AA for its 10.9 px bold
text. It affects the mobile menu of **all 23 codebase-site pages**. Medium severity, one line, but
it is shared CSS outside this task's scope — **named, left, and routed to whoever next touches the
nav.**

**Both themes are exercised in production, not behind a switch.** This design system has no global
dark toggle, only the section-level rhythm, so the page is laid out with the MER evidence band
(duration curve, zero-share meters, heatmap) in `.section-dark` and the rest in `.section-light`.
Tokens are declared on `.mac-scope` and redeclared under `.section-dark`; the heatmap ramp flips
its anchor so *more* reads *lighter* on the dark surface.

**Verified behaviour:** nav entry present and `aria-current="page"`; hash round-trips
(`#iso=CAISO&year=2025&tech=solar&state=full` survives reload); no console errors in any state (the
only browser complaint is the Google Fonts fetch failing offline); no horizontal scroll at 390 px;
and the invariants — in the empty state **0** dollar ticks, **0** marks, 9 named pending rows,
**0** digits inside any pending tile, **0** meter fills for a pending grid.

**The mock ships three preview states** as buttons in the banner — `0 ready`, `3 ready`, `9 ready`
— so the pending path is reviewable without editing a URL. The default is **3 of 9**, because that
is what the page will actually look like while lanes land one at a time.
