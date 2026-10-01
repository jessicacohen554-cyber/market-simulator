# FINDING — codebase-site factual repair, pass 2 (WS5 Job 1, pre-G3)

**Session:** `claude/site-facts-2-repair-43gm3p`, 2026-08-22.
**Charter:** WS5 Job 1 (site factual repair), continuing
`docs/FINDING-site-facts-repair-2026-08-19.md`. **Not SITE-A** — no restructure, no §7.6
signed-disposition work.
**Owner-reported defects:** three, listed below. **Owner ruling on scope, binding:** site content
only. P2 stays in the codebase behind `--enable-legacy-p2`; nothing under `src/` was touched.

Companion to the 2026-08-19 pass. That pass fixed twelve staleness defects and three
governance-grade ones and *deferred* two P2-presentation items to SITE-A (its §4 items 5 and 6).
**The owner has since pulled both back into this lane**, which is what defect 1 below is.

---

## 0. Headline

Three reported defects, all repaired. Two things the reported scope did not include and that a
sweep surfaced:

1. **The 25-year forecast claim was wrong in its *mechanism*, not just its number.** The site
   attributed the forecast's runtime to cross-year warm-starting. Owner decision **D-10**
   (2026-08-04) **disarmed cross-year warm-start on the forecast path** — every shipped forecast
   runner passes `forecast_xyear_warmstart=False`. Forecast years solve **cold** at HEAD. A
   measured full-horizon wallclock does exist for three ISOs and is now quoted instead of derived.
2. **Three pages rendered their table headers at 1.01–2.41:1 contrast** — black on navy, effectively
   invisible, across 81 table headers. Pre-existing, one root cause, fixed. Details in §4.

---

## 1. DEFECT 1 — P2 presented as a live third pass

`solving-pricing.html` was the last page still built around P0→P1→P2. Repaired to two passes; P2
remains **mentioned in prose as an archived legacy artifact** and appears in no step, diagram or
aria-label.

| Was | Is | Source |
|---|---|---|
| header subtitle `:300` "**Three** LP solves per year" | "Two" | `wallclock-baseline-2026-07.md:16` — *"Solves per year: exactly 2 (P0 base-cost + P1 bid-cost)"*; CLAUDE.md "Dispatch & Commitment" |
| section 2 heading + HTML comment "P0 → P1 → P2" | "P0 → P1" | same |
| figure `aria-label` / figcaption "P0→P1→P2 solve sequence" | "P0→P1 solve sequence — the only two passes" | same |
| intro "Step through **each** pass … Click **any** panel" | "**both** passes … **either** panel" | now literally two |
| **"P2 adequacy backstop"** glass panel, describing `apply_commitment_with_coal_pin()` as live engine behaviour | replaced with the mechanism that actually carries commitment structure at HEAD | `pipeline/solve.py` (P0→P1 seam); detector `model/commitment.py::caiso_ra_mustoffer_min_gen:703` |

**Kept verbatim, as instructed:** the archived-P2 table row and the "P2 is archived — not a
calibration option" callout (`:374-:384`). Both were already accurate.

### 1.1 The animation JS did key off a three-panel array

`js/viz-p012-sequence.js` — the owner's suspicion was correct. What moved:

- `STEPS` 3 → 2 entries; eyebrows `Pass N of 3` → `of 2`.
- P1's `arrowLabel: 'screen commitments →'` — an arrow pointing at P2 — dropped.
- Region `aria-label` "P0 to P1 to P2 solve sequence" → "P0 to P1".
- The seed step label was **hardcoded** `Step 1 of 3` while every subsequent update already derived
  from `STEPS.length`. Now derived, so it cannot drift again.
- `buildP2SVG` (79 lines) removed as dead code.
- **Next/Prev bounds and the dot tablist needed no change** — they were already
  `STEPS.length`-derived.

**Exercised in Chromium, not just loaded:** 2 panels; `Step 1 of 2` → Next → `Step 2 of 2`; Prev
disabled at index 0; Next disabled at the end; Prev returns to step 1. `node --check` clean.

### 1.2 `config-reference.html`

`commitment_enabled` (`:812`) and `commitment_irr_hurdle` (`:973`) described live P2 config with no
archived note. Both now **lead** with the archived status and the `--enable-legacy-p2` hard-error.

**Deliberately plain text, not markup.** `js/viz-config-table.js:107` truncates `field.description`
to 80 characters for the collapsed row, which would sever an HTML tag mid-attribute; the note leads
so it survives that truncation.

**Swept the whole page as instructed:** these are the only two `commitment_*` rows.
`ercot_as_aware_commitment` does not appear on the page at all.

**Not touched** (already correct, per the owner): `calibration-rubric.html:338`, `index.html:494`,
`mental-model.html:198`.

---

## 2. DEFECT 2 — solve-time and memory claims

Authoritative records used throughout, and now cited **on the pages themselves** so the figures are
traceable without this doc:

- `docs/handoffs/wallclock-baseline-2026-07.md` — the plain-recipe per-year tables, the P-4 solver
  experiments, the H2/H3/H3b warm-start and full-horizon A/Bs, and the **2026-08-17 PERF-B at-HEAD
  keeper-replay anchor**.
- `docs/handoffs/perf-recheck-2026-08.md` §2 — at-HEAD phase re-measures.
- `results/calibration/FINDING-miso169-15gb-memory-fit-2026-08-19.md` — MISO LP dimensions and peak RSS.

**A caveat that governs every wall figure and is now stated on both pages:** cross-run solve walls
on this host class vary up to **±35 %** (the PERF-B record measures the same ERCOT-2025 P0 at 574.5 s
and 363.6 s in back-to-back byte-identical arms). Phase *structure* is the reliable signal; a single
wall reading is not.

### 2.1 `lp-core.html`

| Line | Was | Is | Why |
|---|---|---|---|
| `:612` | "Typical: **30–60 seconds per year** on a modern CPU" | total-per-year, phases named, host named: **3–6 min** plain recipe (ERCOT 183–323 s, MISO 293–339 s); **4–18 min** at-HEAD keeper recipes (NEISO 278–362 s, NYISO 229–459 s, ERCOT 846–1093 s); solves are 74–83 % of it | Wrong by 3–11×, **and ambiguous** between total-per-year and solve-only — both readings were wrong, so the fix states which it is |
| `:596` | "~**1.8M** columns … well under 1 % dense" | **13.2 M** columns (plant-level ERCOT); **25.4 M × 492,516 rows, 50.3 M nnz** (plant-level MISO); **~0.0004 %** dense | 1.8 M traces to a stale `dispatch.py` comment the 2026-07 baseline explicitly corrected ("the plan's '~1.8 M' was stale"). "Under 1 %" was *true* but understated by three orders of magnitude |
| `:627` | cross-year warm start "converges in **seconds instead of minutes**" | the measured gains **and** the disarm — see §2.2 | False as a number and misleading as a mechanism |
| `:631` | "the 25-year forecast solves in **under an hour** — warm-starting buys enormous speed gains" | measured cold full-horizon runs + three caveats — see §2.2 | The causal half was false |
| `:600` | Algorithm: "Dual simplex (fast warm-starts from prior year's basis)" | records the measured IPM+crossover rejection (>300 s cap unconverged vs dual simplex's 136 s) | The parenthetical asserted a property that is path-dependent (§2.2) |

**Two further unsourceable claims found in the same section, not in the owner's list, and
REMOVED rather than restated** — per the instruction that an unsourceable claim gets removed or
hedged, never left standing:

- solver-info "P1 … **Converges in <5 iterations**"
- prose "only **1–5 simplex iterations** are needed to re-optimize after the cost change"

P1 costs 22–51 s on the plain recipe and 322–447 s on the ERCOT keeper replays; P0 alone runs
~190,000 dual-simplex iterations. **No measured P1 iteration count exists anywhere in the record**,
so no number replaces these — the text now gives the measured *walls* instead.

### 2.2 The 25-year forecast figure — derived, then superseded by a measurement

The owner's instruction was to derive a defensible range rather than invent one, and to show the
arithmetic. **A derivation turned out to be the wrong instrument**, because direct measurements
exist. Both are recorded here so the reasoning is auditable.

**The derivation the owner sketched** (25 × the fastest measured *backcast* year, 183.1 s ≈ 76 min)
**does not apply**, because forecast years are materially cheaper than backcast years: the measured
ERCOT forecast years run **95.9–171.3 s** each against 183–323 s for a backcast year, and peak RSS
is 3.76 GB against ~5.9 GB. Forecast mode carries no benchmark-scoring frames and a different fleet
path. Extrapolating backcast per-year walls onto the forecast horizon would have overstated it.

**What is measured** (`wallclock-baseline-2026-07.md` §H3 / §H3b — 2026–2050, 8,760 h, every
`ScenarioConfig` field at default except mode/iso/horizon):

| ISO | cold (the shipped posture) | warm | status |
|---|---|---|---|
| ERCOT | **3,066.3 s = 51.1 min** | 1,506.3 s | complete |
| NEISO | **2,473.3 s = 41.2 min** | 1,350.6 s | complete |
| NYISO | **2,083.8 s = 34.7 min** | 1,110.5 s | complete |
| CAISO | stopped at **22 of 25 years** | 7,346.6 s = **122.4 min** | **no verdict** — must not be quoted as one |
| PJM, MISO | — | — | **never run at full horizon** |

**Why the cold column is the live one.** Owner decision **D-10** (2026-08-04, sitting Addendum K.3)
disarmed cross-year warm-start on the forecast path:
`scripts/lib/forecast_posture.py::shipped_forecast_xyear_warmstart` returns
`FORECAST_BUNDLE_XYEAR_WARMSTART = False` (`scenarios.py:1594`) and is the **one reader** all three
shipped forecast runners pass through (`run_full_horizon.py:357`, `run_capacity_hindcast.py:677`,
`ff_readiness_battery.py:180`), because FFR-3M measured that a killed-and-resumed forecast does not
reproduce from its own cache. The ~2.3× is an accepted cost.

So "under an hour" happens to be **true for the three measured ISOs**, but the site was right by
accident and wrong in its reason. The page now states the measured cold figures, names the mechanism
correctly, and carries the three caveats a reader planning against the number needs: CAISO carries
no verdict and its *warm* arm alone was 122 min; PJM and MISO are unmeasured and MISO is the heaviest
ISO in the model; and all of it predates the 2026-08 performance work.

**Backcast cross-year warm-start is a separate mechanism and stays on**, so the page distinguishes
them explicitly: 5.6× on ERCOT's year-1 P0 from a persisted basis (211.5 → 38.0 s), 3.8× MISO,
~2.3× on adjacent warm years.

### 2.3 `solving-pricing.html` §5

| Was | Is |
|---|---|
| `:743` "P0 solves the full **~1.8M-column** LP … (**~8–15 min**) … P1 re-optimises **in minutes**" | 13.2 M / 25.4 M columns; P0 **133–219 s**; P1 **23–51 s** |
| stat card "**~5×** warm-start speedup" | **1–7×**, labelled as the measured P1-vs-P0 wall ratio and recipe-dependent |
| "P1 typically reaches optimality in **a handful of dual-simplex pivots**" | removed; P0 alone is ~190,000 iterations |
| "each year's LP uses **several GB of RAM**" | **5.7–5.9 GB** ERCOT / **12.4 GB** MISO, with rule 12's ~2-concurrent cap given its actual reason |

The "~5×" was not merely imprecise — it does not hold at HEAD. Measured P1-vs-P0 wall ratios: 5.0–7.0×
(ERCOT plain), 4.3–4.9× (MISO plain), but 1.1–1.3× (ERCOT keeper replay), ~1.0× (NYISO), 2.4–3.3×
(NEISO). The page now gives the range and says it depends on the recipe. **No causal explanation for
the narrowing is asserted** — a plausible one exists (the bridges inject `min_gen` floors at the
seam, so P1's LP differs from P0's by more than its cost vector) but it is not measured, so it is
not claimed.

### 2.4 `data-pipeline.html:759`

"still fits in a **few GB of RAM**" → measured 5.7–5.9 GB (ERCOT) and **12.4 GB** (MISO, down from
13.95 GB after the 2026-08-19 marshalling fix) against a 15 GB host, with rule 12's cap explained.
The same sentence's "solves in minutes" is **true and kept**, now quantified.

### 2.5 The sweep — everything else checked

Swept all 17 narrative pages for timing, memory and throughput claims. Everything else resolved to
CSS `transition` durations, storage-duration hours (4-hour battery), or scarcity-hour counts. **One
claim was checked and left standing:** `results-calibration.html:600`, "the Parquet file is
~100–200 MB per ISO-year". No dispatch parquet exists on disk in this checkout to measure, but it is
consistent with the one available anchor — CLAUDE.md's "`caiso119_base_A` alone is ~120 MB of
parquet/npz". Recorded rather than silently accepted; a session with a live bundle should confirm it.

---

## 3. DEFECT 3 — the ISO-specific corpora

`data-pipeline.html` named only the federal sources. New **"The ISO-Specific Corpora"** section, an
`h3` inside §3 so it takes a TOC-rail entry without renumbering the page's five sections.

### 3.1 Establishing use from code first (the load-bearing part)

Every corpus was traced to its consumers before being described, because under rule 13
`[R-MEASURED]` the difference between a dispatch input and a parameter-identification input is the
difference between admissible and inadmissible. Four tags, defined on the page:

| Tag | Meaning |
|---|---|
| `SOLVE` | read at solve time by `src/market_sim/` |
| `DERIVED → SOLVE` | the bulk corpus is **not** read at solve time; a small committed artifact derived from it is |
| `IDENTIFY` | grounds a parameter; never enters a solve |
| `SCORE` | grades the model's output; never an input |

What checking changed, versus what a plausible-sounding description would have said:

- **The five offer corpora are `IDENTIFY`, not dispatch inputs.** `ercot/SCED-CT`,
  `caiso-public-bids`, `pjm-energy-offers`, `miso-energy-offers` are read only by
  `scripts/data/derive_*` / `curate_*` and probes — nothing under `src/`.
- **`pjm-da-virtuals` is the single offer corpus that IS a live LP input** and is tagged `SOLVE`:
  `src/market_sim/data/virtual_bids.py:122` resolves `paths.PJM_DA_VIRTUALS_DIR` and errors if it is
  empty when `pjm_da_virtual_bids` is on.
- **`pjm-zonal-lmp` and `lmp-components` are `DERIVED → SOLVE`.** The bulk corpora are not read by a
  solve; the committed `PJM_loss_surface.csv` / `MISO_loss_surface.csv` derived from them are, via
  `src/market_sim/data/loss_surface.py`. Describing the raw corpora as dispatch inputs would have
  been the exact error the owner warned about.
- **`lmp-data` is `SCORE`**, and the page says why: pinning the backcast to observed prices is what
  rule 13 forbids.
- **`miso-energy-offers` carries its own limit on the page** — identity is masked with no fuel or
  technology attribute, and the offer-side coal/CC/CT class bridge was built and **refuted** at
  miso-138, so no class crosswalk is asserted from it.
- **All five AS feeds are `SOLVE`** — `data/reserve_requirements.py` and
  `data/caiso_as_requirements.py`, not merely reference material as the directory names suggest.
- **`data/raw/ERCOT/` and `data/raw/MISO/` are publications, not data** (Potomac IMM State of the
  Market volumes), opened by no code; **`data/raw/PJM/` is an orphan** with zero consumers whose live
  equivalents sit under near-identically-named directories. Said plainly on the page so the names are
  not mistaken for live corpora.

Nineteen rows across four themed tables: offer conduct · network and congestion · availability and
emergencies · reserves, capacity and zonal load.

### 3.2 Retention, stated honestly

The page must not imply the payloads sit in the repo. It now says, in a callout:

- For most of these corpora only `README.md` and `SHA256SUMS.txt` are tracked; the payload is
  gitignored.
- The **2026-08-16 history rewrite stripped the previously-tracked payloads out of history**, so
  checking out an older commit will not bring them back.
- **The recovery route is re-fetch**, and each README carries the verified source-URL table and fetch
  command.
- **No `git restore --source=<pin>` command appears anywhere on the site.** Those pins are dead
  (`docs/FINDING-history-rewrite-2026-08-16.md`).
- Named as **unrecoverable from this repository**: the CAISO OASIS group-zip dailies, and pre-slim
  SCED columns past ERCOT MIS retention.
- The two non-size reasons for gitignoring are given: the PJM DataMiner2 non-member redistribution
  restriction, and CAPTCHA-gated ISO-NE workbooks that no committed script can refresh.
- What **is** tracked: the small derived artifacts each solve actually reads.

---

## 4. Accessibility — three Critical bugs found, all pre-existing, all fixed

Ran the `accessibility-audit` skill over every edited page. The new content was clean; the audit
surfaced a **pre-existing Critical defect** that my new tables would have inherited.

**Root cause, one line, three pages.** `shared.css:982` styles `.data-table th` as
`background: var(--navy); color: rgba(255,255,255,0.90)` — navy header, white text. Three pages
carry a page-local `.data-table th` rule that overrides the **colour** with a light-theme token but
**not the background**, so the header renders near-black on navy:

| Page | Local colour | Measured | Headers affected |
|---|---|---|---|
| `config-reference.html` | `var(--text-secondary)` | **1.01:1** | 50 |
| `data-pipeline.html` | `var(--text-primary)` | **1.42:1** | 26 |
| `fleet-offer-curves.html` | `var(--text-muted)` | **2.41:1** | 5 |
| `network.html` *(control)* | none | 12.24:1 PASS | 5 |

`network.html`, which has no local override, is the control and shows the design intent. Fix: drop
the conflicting `color` declaration on all three, leaving a comment saying why.

**A second layer on `data-pipeline` only.** Its page-local `.data-table thead
{ background: var(--bg-card) }` put an opaque white layer beneath the dark-section `th` tint
(`rgba(255,255,255,0.10)`, which is meant to composite over navy). With the colour fixed that
rendered **white-on-white**. The opaque thead background is dropped too.

**After:** 9.19–12.24:1 on every table header of all four pages, verified in Chromium.

`fleet-offer-curves.html` is outside the reported page set. It shares the single-line root cause and
was measurably Critical, so it was fixed here rather than left; noted because it widens the diff
beyond the named pages.

### 4.1 New elements, measured on their true painted background

Measured in Chromium with alpha compositing **and** gradient awareness — `.section-dark` paints via
`linear-gradient`, so `getComputedStyle().backgroundColor` returns transparent and a naive walker
reports a false failure. (It did, twice, before the measurement was corrected; both were measurement
artifacts, not page defects, and the corrected numbers are below.)

| Element | Ratio | |
|---|---|---|
| `.use-tag.solve` `#166534` on its tint | 5.85 | PASS |
| `.use-tag.derived` `#6B21A8` | 7.06 | PASS |
| `.use-tag.identify` `#92400E` | 5.81 | PASS |
| `.use-tag.score` `#1E40AF` | 7.09 | PASS |
| corpus table cell | 13.90 | PASS |
| corpus table header (post-fix) | 12.24 | PASS |
| retention callout body / title | 13.06 / 6.32 | PASS |
| `#iso-corpora` h3 | 19.95 | PASS |
| dark-section glass panel body / title / code | 7.96 / 14.81 / 8.88 | PASS |

Scanned all edited pages for light-theme tokens used inside a `.section-dark`: three hits on
`data-pipeline`, all **pre-existing and all correct** — the element paints its own opaque
`var(--bg-card)` background, so the dark-token trap does not apply.

### 4.2 Wide tables are clipped, not scrollable — site-wide

`html` and `body` both carry `overflow-x: hidden` (`shared.css:137,147`), so a table wider than the
viewport is **clipped and unreachable**, not scrollable. At 375 px the document reports zero overflow
while `main.scrollWidth` is 562 px — the right-hand column is simply gone.

The four new corpus tables are wrapped in `.corpus-table-scroll` (`overflow-x: auto`), so no column
is lost. **The same clipping affects the site's other `.data-table` instances** and is recorded in §5
for SITE-A rather than re-architected in this lane.

---

## 5. Deferred, and things I could not source

1. **Wide-table clipping site-wide (§4.2).** Only the four new corpus tables were given a scroll
   container. Every other `.data-table` on the site is still clipped at narrow widths. A general fix
   belongs with SITE-A because it touches shared CSS and every page's table layout.
2. **`results-calibration.html:600`'s "~100–200 MB per ISO-year"** (§2.5) — consistent with the one
   available anchor but not directly measured in this checkout. Left standing; flagged.
3. **No measured P1 simplex-iteration count exists** (§2.1). Two claims that asserted one were
   removed rather than replaced. If a future perf session captures it, the solver-info row can say so.
4. **PJM and MISO have no full-horizon forecast measurement** (§2.2). The site now says so explicitly
   rather than implying the three measured ISOs generalise. Producing them is a perf-lane call.
5. **CAISO's full-horizon cold arm carries no verdict** (stopped at 22/25). Not quoted as one
   anywhere.
6. Everything the 2026-08-19 pass deferred in its §4 that the owner did not pull into this lane —
   the orphaned `forecast-validation.html` nav entry, the `scarcity-deep-dive` ercot215 re-run, the
   ablation-twin section's existence, the v3.4 rubric re-read, and the `holdout-freeze.json` intake
   clause — **remains deferred and untouched**.

---

## 6. Verification

**Nothing data-driven was touched.** No edit went near `backcast-runs.html`,
`calibration-status.html`, `forecast-runs.html`, `forecast-status.html`, `mechanism-matrix.html`,
their generated manifests, the forecast namespace, or any mechanism-matrix shard. No new
`.github/workflows`. No change under `src/`, `scripts/run_*`, `scripts/score_*`, `CLAUDE.md` or the
spec.

**Rendering.** All six edited files: HTML well-formedness checked (zero unclosed tags, zero
mismatches); `viz-p012-sequence.js` passes `node --check`. Every edited page loaded in Chromium off a
local server with **zero page errors**. The only console errors on any page are the sandbox blocking
`cdnjs.cloudflare.com` and `fonts.googleapis.com`, which is environmental and identical to the
2026-08-19 pass's record.

**Interactive elements exercised, not just rendered.** The P0→P1 stepper: 2 panels, `Step 1 of 2` →
Next → `Step 2 of 2`, Prev disabled at index 0, Next disabled at the end, Prev returns to step 1.
The corpus tables: 4 tables / 19 rows present, `#iso-corpora` in the TOC rail, no document-level
horizontal overflow at 375 / 768 / 1280 px.

**Rule 27 `[R-PUSH]`.** All six files are ≥300 lines. Every push was byte-verified — the pushed blob
fetched back and its line count and SHA-256 compared to the local file — before the next commit. All
matched. No file was regenerated from model output; every edit was a targeted local `Edit`, and the
one bulk removal (dead `buildP2SVG`) was a line-range deletion with asserted boundaries.

**Commits** (three, each pushed and verified before the next):

| Commit | Files |
|---|---|
| `3e9a47a` | `solving-pricing.html`, `js/viz-p012-sequence.js`, `config-reference.html` |
| `59e52fc` | `lp-core.html`, `data-pipeline.html` |
| `599320a` | `data-pipeline.html`, `config-reference.html`, `fleet-offer-curves.html` |
