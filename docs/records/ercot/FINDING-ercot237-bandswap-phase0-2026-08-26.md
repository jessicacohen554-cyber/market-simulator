# FINDING — ercot-237 (2026-08-26): the keeper's band-structure residual is NOT a pairwise swap — the [500,1000) band is a CRUSHED TRANSITION (2 of 43 actual mid-deep hours land in-band; the surface passes through it from both sides), plus a 14-hour family of entirely-missed off-core events; and the registered "≥$1,000 tail EXACT (59 vs 59)" is WRONG (the actual is 61, and hour-level identity is only 36/59)

**Session ercot-237, 2026-08-26, branch
`claude/ercot-236-merge-owner-queue-k97n01`. ZERO-SOLVE — every number below
is read from the committed keeper sidecar
(`results/calibration/ercot236_k33_clip/hourly/system_2023.parquet`) and the
committed actuals (`data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`),
constructions byte-identical to the ercot-236 point scorer.** Precommit
`docs/PRECOMMIT-ercot237-bandswap-phase0-2026-08-26.md` pushed + blob-verified
before any measurement; **Amendment 1** (recorded and pushed mid-round, before
any characterization) corrects the V-0 actual-side expectation — see §1.
Probe: `scripts/probes/ercot237_bandswap_phase0.py` →
`results/calibration/ercot237_bandswap_phase0.json` (committed).
Keeper `2026-08-25-236-swcap-clip-k33` (CALIBRATED, zero caveats) is
UNTOUCHED; no lever is proposed or armed this round (any lever is a new
precommitted, owner-visible round per the handoff); no matrix cell changes
(nothing tested).

## 0. Verdict in four lines

1. The reported residual is **not** hours swapping between adjacent bands:
   the joint matrix shows the model's `[500,1000)` band nearly disjoint
   from reality's — **only 2 of the 43 actual mid-deep hours are modeled
   in-band**; 28 are modeled below $500 and **13 are modeled ≥ $1,000**.
   The k=33 surface transitions August afternoons from `[200,500)` to
   ≥ $1,000 too steeply to populate the band between.
2. A separate **14-hour family of entirely-missed events** (model < $200,
   actual $537–2,014) spans Mar/May/Jul/Aug/Sep/Oct/Nov — real short-lived
   scarcity events the dispatch does not see at all, mostly OUTSIDE the
   August core.
3. The `[200,500)` over-fill is the already-known G-SPUR population wearing
   a second label: 39 of its 46 spurious members (actual < $200) are
   G-SPUR banded hours (39/68 = 57 % of the spur set).
4. **The registered "≥ $1,000 tail EXACT (59 vs 59)" is factually wrong
   twice over**: the actual count is **61** (Amendment 1; tail-sum proof
   77+43+61 = 181 = `actual_tail.json` rt_gt), and count-identity is not
   hour-identity — only **36 of the model's 59** deep hours are actually
   deep. No scored criterion moves (C3a/C3b/C3c never touched these
   constants); the prose correction is an owner-visible queue item.

## 1. V-0 identity gate — FIRED on the actual side, resolved by Amendment 1

First run hard-stopped: recomputed actual bands 77/43/**61** vs the
registered 77/43/59. Model side reproduced exactly (103/18/59 — zero
drift). Diagnosis (Amendment 1, recorded before proceeding): the actual
band constants were **hardcoded** in `ercot235_offer2023_sweep.py` and
copied into `ercot236_h4097_repair.py` — the actual side was never
computed from data in either probe. 61 is correct under every edge
convention (≥, >, ≥ 1000.005); the two hours separating the counts are
borderline members h5343 ($1,007.94) and h5563 ($1,001.54); and
77+43+61 = 181 = the committed rt_gt tail count, where the registered
decomposition sums to 179 ≠ 181. **Corrected residual statement:
[200,500) 103 vs 77 · [500,1000) 18 vs 43 · ≥1000 59 vs 61.**
Surfaces carrying the wrong "EXACT (59 vs 59)" prose (all report-only;
correction NOT made this round — promotion-record surfaces are the
owner's): `docs/calibration-log/ercot.md` (ercot-235/236 entries),
`frontend/data/backcast/keepers/ERCOT.json`,
`frontend/data/backcast/registry/2026-08-25-236-swcap-clip-k33.json`,
`frontend/data/backcast/status/ERCOT.js`,
`docs/mechanism-testing-matrix.md` §5.1,
`docs/codebase-site/data/mechanism-matrix/ERCOT.js`, plus the hardcoded
constants in the two probe scripts.

## 2. The joint band matrix (model × actual, 8760 h)

| model \ actual | <200 | [200,500) | [500,1000) | ≥1000 | Σ |
|---|---|---|---|---|---|
| <200 | 8526 | 40 | 13 | 1 | 8580 |
| [200,500) | **46** | 24 | 15 | **18** | 103 |
| [500,1000) | 4 | 6 | **2** | 6 | 18 |
| ≥1000 | 3 | 7 | **13** | 36 | 59 |
| Σ | 8579 | 77 | 43 | 61 | 8760 |

Diagonal above $200: 24 + 2 + 36 = 62 of 180/181 banded hours — the
count-level C3b/C3c agreement rides on off-diagonal cancellation, which is
exactly what this Phase-0 was chartered to expose.

## 3. WHERE the 43 actual-[500,1000) hours go (the under-fill, three legs)

* **Leg U1 — missed events entirely (13 h, model < $200):** actual
  $537–843 vs model $35–167. By month 10 of 13 are OUTSIDE August:
  Mar h2058, May h2971, Jul h4623/h4626, Aug h5369/h5484/h5777,
  Sep h5943/h5945/h6399, Oct h7001/h7145, Nov h7480 — all hod 12–19.
  With the `lt_200|ge_1000` corner hour h4578 (Jul, hod 18, actual
  $2,014 vs model $175) this is a **14-hour missed-event family**: real
  shoulder-season / off-core scarcity events (single-hour to two-hour
  spikes) the dispatch does not reproduce at any level.
* **Leg U2 — August shoulder under-shoot (15 h, model [200,500)):**
  13 of 15 in August, hod 13–19; model $230–425 vs actual $521–988 —
  the event-day shoulders where the surface sits one band low.
* **Leg U3 — August overshoot THROUGH the band (13 h, model ≥ $1,000):**
  all Aug/Sep, hod 13–19; model $1,174–2,725 vs actual $570–946 —
  the same event complex, overshot past the band. Only h5394/h5395
  (Aug, hod 18–19) land in-band.
* The clip is NOT implicated: 1 hour at λ ≥ $4,999 in the whole year,
  0 overlap with this population.

## 4. The [200,500) over-fill (103 vs 77) — mostly the spur population

Of the 103 model-banded hours, 46 have actual < $200 (Aug 34, Sep 9,
Jul 2, Jun 1; hod 12–21). **39 of those 46 are G-SPUR banded hours**
(the ercot-225 card's population; 39/68 = 57 % of the spur set, 85 % of
this cell): the over-fill is dominantly the known blunt-instrument level
lift, not a new object. The remaining 18 hours of the cell's imbalance
are the U2 shoulders (15, §3) plus `200_500|ge_1000` misses (18 h —
counted below); net +26 vs actual arises from these overlapping flows,
not one population.

## 5. The deep tail: count-EXACT is not hour-exact

Model ≥ $1,000 (59 h): 36 correctly deep, 13 are actual-[500,1000)
(leg U3), 7 actual-[200,500), 3 actual < $200 (h5684, h5729, h5731 —
h5684/h5731 are members of the ercot-225 card's corrected 2023 G-SPUR
baseline identity list; band-top-blind under the current gate, visible
under its Option A). Actual ≥ $1,000 (61 h): 36 hit, 18 modeled
[200,500) (Aug-14/Jul-2/Jun-1/Sep-1, afternoons — e.g. h5175–h5178
consecutive at model $211–335 vs actual $1,246–2,100), 6 modeled
[500,1000), 1 modeled < $200 (h4578). **Within August the surface
redistributes scarcity across the wrong afternoons** — deep where
reality was mid ($1,400 vs $300 on h5726–h5731) and mid where reality
was deep (h5175–h5178) — netting the monthly mean to within $1 and the
deep count to 59 vs 61 while hour-level identity is 36/59.

## 6. Precommit priors, graded

* **P1 CONFIRMED** — 28/43 (65 %) of the actual mid-deep hours are
  modeled below $500. Honest addendum the prior under-called: the
  overshoot leg is substantial (13/43 ≥ $1,000), so the correct object
  is *bimodality around the band* (2/43 in-band), not a one-sided level
  gap.
* **P2 CONFIRMED** — 39/68 = 57 % of the spur set appears in the
  over-fill's spurious cell (≥ half, as declared); 85 % of that cell is
  spur.
* **P3 PARTIAL** — month leg CONFIRMED (Aug+Sep 36/43 = 84 %, Jun–Sep
  38/43 = 88 %); the hod leg REFUTED AS STATED: the under-fill peaks at
  hod 13–18 (afternoon-through-evening, mode hod 17), not the declared
  HE 17–21 — 20/43 in 17–21 vs 22/43 in 12–16.

## 7. Named candidate objects (NOT chartered — owner-visible queue)

1. **The missed-event family (14 h, §3 U1 + h4578):** off-core real
   scarcity events (10+ outside August) the dispatch misses at any
   price level. Structurally distinct from the level/steepness story —
   likely an availability/outage/net-load-ramp representation question,
   not an offer-curve one. Bounded and enumerable.
2. **The August steepness object (U2+U3+§5):** the k=33 uniform peak
   lift places the right MASS of scarcity in August but transitions too
   steeply through [500,1000) and on partially wrong afternoons. Any
   repair is offer-SURFACE-shape work (rule 1: structure first — a real
   mechanism, not a band-targeted fitted reshuffle; and the spur cost
   already binds the same lift).
3. **The prose correction (59 → 61, §1):** owner sign-off to correct the
   keeper's promotion-record surfaces (list in §1) in one pass; the
   determination and every scored criterion are untouched.

**Disposition:** characterization complete, zero solves, nothing armed,
keeper untouched. Results JSON + this FINDING + the calibration-log entry
are the deliverable; the queue above goes to the owner alongside the two
standing items (the ercot-225 G-SPUR gate card, the `complete`-marker
question).
