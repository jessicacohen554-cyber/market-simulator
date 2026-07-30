# FINDING — pjm-141: **the overnight marginal TRANCHE is already correct, and the defect is that no offer in the model varies by hour at all.** The chartered W6 census answers `FINDING-pjm139` §W4's open question: the marginal rung at h01–h04 is `econ` — **78.7 / 78.4 / 77.5 %** of the marginal set — and the evening-peak control is **statistically identical** (77.3 / 79.5 / 80.7 %). There is no part-load artifact, no floor rung at the margin, and the model's overnight thermal requirement matches PJM's own CAMPD actual to **+0.9 / −2.0 / +2.5 %**. What the census exposes instead is larger than the overnight cell: measured directly on the keeper's own offers, **every one of the 2,034–2,044 thermal LP rows posts the SAME offer in every hour of a calendar day — within-day σ = $0.000000, h01–h04 offer = h16–h18 offer to $0.0000, all three years.** So the model's entire intra-day price amplitude must come from merit-order traversal, and that traversal delivers only **31 / 33 / 32 %** of the measured overnight→evening-peak swing, with sign-symmetric error: **too DEAR overnight (+$6.82 / +$5.78 / +$3.40)** and **too CHEAP at peak (−$7.62 / −$11.37 / −$22.19)**. The overnight bottom-of-distribution miss and pjm-139's winter morning ramp (26 / 21 / 18 % of the h04→h07 rise) are **one defect measured at two points**, and the annual level being right is a cancellation, not a correct level.

**No LP was solved.** Every measurement runs on the committed keeper
`pjm140_rampenv_B` — its `meta.json` replayed through
`replay_keeper.build_kwargs` → `run_year(fleet_only=True)` for the offer arrays
(no LP constructed), its committed `hourly/` sidecars for prices and class MW,
the committed bench payload `frontend/data/backcast/bench/PJM/<year>.json.gz`
for the CAMPD actual, `data/raw/eia-930-hourly/PJM hourly.parquet` for measured
interchange, and the `data/raw/pjm-zonal-lmp/` DA component intake for measured
MEC. Probes: `scripts/probes/_pjm141_overnight_tranche.py` (new, W6-T) and the
committed `scripts/probes/_pjm139_winter_ramp.py --with-fleet` (W6, **run for the
first time** — pjm-139 could not run it and pjm-140 did not need it). Machine
output: `results/probes/pjm141_overnight_tranche.json`,
`results/probes/pjm141_w6.json`.

**Nothing is registered on the dashboard and no keeper changes.** No arm was
solved, so there is no bundle to register — the same disposition as pjm-138 and
pjm-139 (rule 15 governs *completed runs*; there is none). The keeper stays
`2026-07-30-pjm-140-rampenv`, **CALIBRATED**, every criterion passing; no gate
moves because nothing was solved. `audit_keepers.py --check` shows PJM `[✓] all
checks passed` (the single suite failure is the pre-existing stale
`status/NEISO.js` on main — NEISO's lane, untouched here).

**No lever is chartered, and §5 explains why that is the honest outcome rather
than an unfinished one:** the mechanism the diagnosis points at is
hour-varying offer conduct, and every in-model route to it is already
adjudicated `R` or owner-closed.

---

## §0 — the verdict in one table

| # | question | result | verdict |
|---|---|---|---|
| **T1** | which TRANCHE sets the overnight price? (**the chartered deliverable**) | **`econ`** — 78.7 / 78.4 / 77.5 % of the marginal set at h01–h04, at **100.0 %** detection in all three years. Dominant pair `CC_REGULAR:econ` **40.2 / 38.5 / 35.4 %**. `committed` is only 14.4 / 15.3 / 14.9 %, `peak` 2.9 / 2.5 / 3.3 %, `sync` 0.6 / 0.3 / 1.0 % | **ANSWERED** |
| **T1-control** | is that mix distinctive to overnight? | **No.** The evening-peak control is the same: `econ` **77.3 / 79.5 / 80.7 %**, `committed` 15.2 / 13.2 / 13.0 % | **the tranche is NOT the defect** |
| **T4** | is the model standing higher on its stack because it needs more thermal? | **No.** Overnight thermal model/measured = **1.0092 / 0.9799 / 1.0253**; CC, the dominant class, within **±1.4 %** | **requirement is correct** |
| **T2** | does the model lack a cheap enough offer, as §W4 concluded? | **Not as stated.** Its cheapest thermal offer is **$4.50** (coal `mustrun`, fuel sunk) — *below* PJM's overnight p05 target in all three years. What it lacks is **depth**: only **6.65 / 4.43 / 6.40 GW** of 95.9 / 94.4 / 96.5 GW available offers below the target (**6.9 / 4.7 / 6.6 %** of the stack) against 46.2 / 47.8 / 53.0 GW of thermal to serve | **§W4 reading CORRECTED** |
| **T6** | does ANY tranche's offer vary within the day? | **NO — exactly zero.** Within-day offer σ = **$0.000000** across all 2,034 / 2,041 / 2,044 thermal rows; capacity-weighted offer at h01–h04 equals h16–h18 to **$0.0000** | **the structural finding** |
| **D-BIN** | can the armed conduct surface supply diurnal slope? | **No.** `[0.8, 0.9, 0.97]` net-load percentile bins put **99.0 / 97.2 / 94.4 %** of h01–h04 *and* **61.3 / 61.1 / 63.7 %** of h16–h18 in the **same bin 0**. Overnight net load 75.3 / 77.7 / 81.4 GW vs peak 94.4 / 98.0 / 98.9 GW — a ~20 GW swing inside one conduct level | **resolution defect** |
| **D-AMP** | how much of the diurnal amplitude does the model produce? | **31 / 33 / 32 %**, with sign-symmetric error: overnight **+$6.82 / +$5.78 / +$3.40**, peak **−$7.62 / −$11.37 / −$22.19** | **one defect, two windows** |
| **D-SEAM** | is the overnight seam position the owner? | **REFUTED.** Model overnight net import −4.33 / −3.61 / −3.76 GW vs measured −5.16 / −4.71 / −2.47 GW: accurate to ~1 GW, and the error's sign **flips** across years (+0.83 / +1.09 / **−1.29**), wrong-signed for the defect in 2023–24 | **lead closed** |
| **charter** | | the successor mechanism is hour-varying offer conduct; `measured_offer_surface` PJM = **R** under both conditioning definitions (pjm-123/126/127/**132 "Lane 2 ENDS"**), and re-binning it against this residual is barred by rule 23 | **no lever chartered** |

---

## §1 — T1: the chartered census, and the tranche is not the defect

`scripts/probes/_pjm141_overnight_tranche.py` rebuilds the keeper's own fleet
per year with **no LP** (`fleet_only=True`), then applies the pjm-138 §4.1 /
pjm-122 marginal-set test — a unit is marginal when its own hourly offer equals
its own zone's dual to within `EPS = 1.0` — reported as pjm-122's count share.
The tranche family is the `unit_id` suffix `bins_to_fleet` writes
(`mustrun` / `sync` / `committed[NN]` / `econ|econcNN` / `peak[N]`).

### §1.1 — the answer

**Marginal count share at h01–h04, by tranche family (%):**

| tranche | 2023 | 2024 | 2025 |
|---|---|---|---|
| **`econ`** | **78.7** | **78.4** | **77.5** |
| `committed` | 14.4 | 15.3 | 14.9 |
| `_unbinned` (DA virtuals) | 3.4 | 3.4 | 3.2 |
| `peak` | 2.9 | 2.5 | 3.3 |
| `sync` | 0.6 | 0.3 | 1.0 |
| `mustrun` | — | — | — |
| detection rate | **100.0 %** | **100.0 %** | **100.0 %** |

**And the evening-peak control, which is what makes the reading safe:**

| tranche | 2023 | 2024 | 2025 |
|---|---|---|---|
| `econ` | 77.3 | 79.5 | 80.7 |
| `committed` | 15.2 | 13.2 | 13.0 |
| `peak` | 4.1 | 4.5 | 3.5 |

The two windows are **statistically indistinguishable**. The model's overnight
price is set by the same rung family that sets its evening-peak price: ordinary
economic loading. `mustrun` never appears — as expected, it is the cheapest rung
in the fleet and sits below everything, so it is in merit but never marginal.
**There is no floor rung, no part-load artifact and no pinning mechanism at the
overnight margin.** The handoff's anticipated branch — "the overnight marginal
tranche is already correct" — is the one that fires.

Dominant pair: **`CC_REGULAR:econ` 40.2 / 38.5 / 35.4 %**, 420 LP rows,
27.5 GW, capacity-weighted offer **$28.76 / $27.14 / $36.24**, p05 **$16.83 /
$16.58 / $20.35**.

### §1.2 — the fleet the census ran on, disclosed with its match rate

2024 (2023/2025 differ only in pmax): **2,822** LP generators, **2,742**
internal, **2,041** internal thermal. Tranche rows: `mustrun` 32, `sync` 20,
`committed` 281, `econ` 1,462, `peak` 246, `_unbinned` 701 (renewables,
nuclear, hydro, imports, DA virtuals). Thermal capacity by tranche:

| | mustrun | sync | committed | econ | peak | **total** |
|---|---|---|---|---|---|---|
| GW | 9.27 | 1.12 | 47.28 | 71.29 | 8.74 | **137.71** |

That total is **137,713 MW — byte-for-byte pjm-140 §1.2's "total ramp-eligible
thermal"**, reached from a different direction (tranche families vs ramp
groups). The census's thermal denominator is therefore cross-validated against
the keeper's own committed artifact, and it is printed rather than assumed
(the pjm-140 §7 lesson: never let the denominator go silent).

Coal enters as the single `plant_group = COAL`, not the `klass` split
`COAL_BIT`/`COAL_PRB`/`COAL_WC` — the pjm-140 §7 trap. The census keys on
`plant_group` throughout, so no coal is dropped.

### §1.3 — a correction to §W4's class picture: marginal ≠ energy

§W4 reported the overnight stack as `CC_REGULAR` 66–69 % + `COAL_BIT` 23–26 %.
Those are **energy** shares. The **marginal** shares are materially different:

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| `CC_REGULAR` | 44.5 | 42.3 | 40.0 |
| **`CT_PEAKER`** | **17.4** | **20.7** | **27.0** |
| `COAL` | 21.0 | 19.9 | 15.3 |
| `CC_CHP` | 5.4 | 4.1 | 6.8 |
| `CT_CHP` | 5.3 | 6.4 | 4.4 |
| `VIRTUAL_INC` | 3.4 | 3.4 | 3.2 |
| `ST_GAS` | 1.8 | — | 1.9 |

**`CT_PEAKER` is the second-largest marginal owner overnight and rising
steeply** — 17.4 → 27.0 % — while carrying only **0.60–0.98 GW** of overnight
output. It is invisible in the energy view and it is *one fifth to one quarter*
of who sets the price. A successor reasoning about the overnight clearing point
from §W4's energy shares alone will mis-attribute it. (§W4's `ST_GAS` closure is
**unaffected and confirmed**: 1.8 / — / 1.9 % of the marginal set, consistent
with its 0.9–1.9 % energy share. It is not the owner on either measure.)

The committed instrument's own W6 census, run here for the first time,
reproduces these class shares **exactly** (2023: 44.5 / 21.0 / 17.4 / 5.4 / 5.3
/ 3.4), so the tranche dimension is added on an independently verified base.

## §2 — T4: the overnight requirement is right, so the model is not simply deeper in its stack

The most economical alternative explanation — the model burns more thermal
overnight than PJM did, so it stands higher on its own merit order — is
**refuted**. Model vs the committed bench payload's CAMPD actual (217 plants
decoded), mean GW over h01–h04:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC model / measured | 33.32 / 33.48 | 35.33 / 35.32 | 35.97 / 35.49 |
| CT model / measured | 0.98 / 0.58 | 0.60 / 0.63 | 0.97 / 0.78 |
| ST model / measured | 11.87 / 11.68 | 11.83 / 12.78 | 16.10 / 15.45 |
| **thermal total** | **46.16 / 45.74** | **47.76 / 48.74** | **53.03 / 51.72** |
| **model ÷ measured** | **1.0092** | **0.9799** | **1.0253** |

Within **±2.6 %** all three years, and CC — 74 % of the overnight thermal fleet
— within **±1.4 %**. The volume side of the overnight cell is correct.

## §3 — T2: what §W4 got right, and the one clause that needs correcting

§W4 concluded *"the model has no offer cheap enough to reach PJM's overnight
floor."* The stack says otherwise, and the distinction matters for what a
successor charters.

Capacity-weighted offer quantiles over the **available** thermal stack at
h01–h04, against PJM's own measured overnight p05:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| PJM measured overnight p05 (target) | **$13.32** | **$11.44** | **$17.02** |
| thermal available, mean | 95.9 GW | 94.4 GW | 96.5 GW |
| offer p00 | **$4.50** | **$4.50** | **$4.50** |
| offer p05 | $4.71 | $12.41 | $14.58 |
| offer p10 | $15.71 | $15.09 | $18.84 |
| offer p25 | $20.02 | $18.72 | $24.10 |
| offer p50 | $28.24 | $25.46 | $33.17 |
| **GW available below the target** | **6.65** | **4.43** | **6.40** |
| — as a share of the stack | 6.9 % | 4.7 % | 6.6 % |
| GW below the model's own dual | 45.17 | 48.29 | 52.94 |
| thermal that must actually run | 46.16 | 47.76 | 53.03 |

The model's cheapest thermal offer is **$4.50** — the coal `mustrun` tranche,
bid at VOM + carbon + NOx with the fuel cost sunk — and that is **below** the
target in all three years. So the correct statement is not that the model lacks
a cheap offer; it is that it lacks **depth** at one: 4.7–6.9 % of its stack
prices below PJM's overnight p05 while it must serve 46–53 GW of thermal, so
the clearing point is pushed onto the `econ` rungs at $26.48–36.18.

Two things follow. First, the model's bottom-of-stack depth is **not obviously
wrong**: ERCOT-136 §3 measured the real share of capacity offered at or below
$4.50 at **5.8–8.4 %**, and PJM's model share here is **4.7–6.9 %** — the same
order. Second, the `CC_REGULAR:econ` rung that actually clears sits only
**+$3.51 / +$5.14 / +$3.33** above the target at its own p05, so the miss is a
few dollars on the marginal rung's level, not a missing tier.

## §4 — T6 and D-BIN: the structural finding — nothing in the model's offer varies by hour

This is the measurement that reframes the session, and it was made directly
rather than inferred.

### §4.1 — T6: within-day offer σ is exactly zero

For every thermal LP row, the standard deviation of its **own** offer across the
24 hours of each calendar day, averaged over unit-days with live capacity, and
the same rows' capacity-weighted offer in the two windows:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| dominant rung (`CC_REGULAR:econ`, 420 rows) — within-day σ | **$0.000000** | **$0.000000** | **$0.000000** |
| all internal thermal (2,034 / 2,041 / 2,044 rows) — within-day σ | **$0.000000** | **$0.000000** | **$0.000000** |
| all-thermal cap-wtd offer, h01–h04 | $35.909 | $32.902 | $41.776 |
| all-thermal cap-wtd offer, h16–h18 | $35.909 | $32.902 | $41.776 |
| **diurnal offer delta** | **$0.0000** | **$0.0000** | **$0.0000** |

**Every thermal tranche in the PJM keeper posts an identical offer in every hour
of a calendar day.** This is measured on the **P0 base cost** (`mc_base`, the
assembled objective with all pricing overlays applied), and the two elements the
P1 bid adds cannot change it:

* `tranche_startup_amortization` — `compute_monthly_markup` amortizes each
  tranche's start cost over its **calendar-month** average run length, so it is
  constant within a month and therefore within a day;
* the mid-curve conduct surface (`pjm_offer_midcurve_segments`, P1-only) — the
  **only** hour-varying element in the whole offer path, and §4.2 measures that
  it is silent where the defect lives.

So the model's intra-day price variation can come from **exactly one place**:
which rung of a fixed merit order clears. pjm-139 §2 already showed the
delivered-gas day factor is flat within a day (σ ≤ 4.4e-16); T6 shows that is
true of the *entire* offer, not just its fuel leg.

### §4.2 — D-BIN: the one hour-varying mechanism cannot resolve the diurnal cycle

The keeper runs `pjm_offer_surface_netload_pcts = [0.8, 0.9, 0.97]` — four
net-load **tightness** bins of 7,008 / 876 / 613 / 263 hours. Where the two
windows actually fall:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| bin thresholds (GW) | 94.7 / 104.0 / 118.6 | 99.1 / 109.4 / 124.0 | 103.5 / 112.9 / 127.2 |
| **h01–h04 in bin 0** | **99.0 %** | **97.2 %** | **94.4 %** |
| h01–h04 mean net load | 75.3 GW | 77.7 GW | 81.4 GW |
| **h16–h18 in bin 0** | **61.3 %** | **61.1 %** | **63.7 %** |
| h16–h18 mean net load | 94.4 GW | 98.0 GW | 98.9 GW |
| h16–h18 in bins 1/2/3 | 14.7 / 13.5 / 10.5 | 13.7 / 15.6 / 9.6 | 13.9 / 13.1 / 9.3 |

Bin 0 spans the bottom **80 %** of net load — everything below 94.7–103.5 GW.
It therefore contains **94–99 %** of the overnight window *and* **61–64 %** of
the evening peak, and it assigns them **the same conduct level by
construction**. A ~20 GW net-load swing (75→94, 78→98, 81→99 GW) sits inside one
bin.

**The mechanism is a scarcity-reach device for the tightest fifth of hours, not
a merit-slope mechanism, and it contributes zero slope across the diurnal band
where the defect lives.** This is the same class of objection pjm-139 §2 raised
against `gas_daily_shape` — a mechanism whose resolution cannot reach the defect
— stated on the **tightness** axis instead of the time axis.

Consistency note, not a decomposition: **36–39 %** of peak hours *do* land in
bins 1–3 and receive an uplift, and the model reproduces **31–33 %** of the
amplitude. The two numbers are compatible; this session does not claim the first
causes the second.

## §5 — D-AMP: one defect, two windows — and why no lever is chartered

### §5.1 — the amplitude, which is the result that outgrew the charter

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model dual, h01–h04 → h16–h18 | 27.70 → 34.28 = **+6.58** | 26.48 → 35.09 = **+8.61** | 36.18 → 48.21 = **+12.04** |
| measured MEC, same windows | 20.88 → 41.90 = **+21.02** | 20.70 → 46.46 = **+25.76** | 32.77 → 70.41 = **+37.64** |
| **model reproduces** | **31 %** | **33 %** | **32 %** |
| overnight error | **+6.82** | **+5.78** | **+3.40** |
| peak error | **−7.62** | **−11.37** | **−22.19** |

Three things this settles:

1. **The overnight miss and the winter morning ramp are the same defect.**
   pjm-139 §W5 measured the model reproducing **26 / 21 / 18 %** of the DJF
   h04→h07 rise; this measures **31 / 33 / 32 %** of the overnight→peak rise.
   Same mechanism-free traversal, same fraction, different window. Queue item 12
   and the overnight cell are one item, not two.
2. **The error is sign-symmetric, so the annual level is a cancellation.** The
   keeper's annual price level is right (+$0.47 / +$2.62 / +$8.48; −$2.36 /
   −$0.08 / +$2.76 after the pjm-138 reserve credit) — but that is a large
   positive overnight error netting against a large negative peak error, not a
   correct level. **Any successor lever must be judged on the amplitude, never on
   the mean**, and a lever that cheapens overnight without steepening the stack
   will break a level that currently passes for the wrong reason.
3. **The peak half is already owner-closed and the overnight half is not.** The
   peak under-pricing is substantially the reserve/opportunity-cost lane
   pjm-138 measured (PJM's synchronized reserve priced above zero in 84.2 / 96.7
   / 47.6 % of hours against the model's 0 / 2 / 28 of 8,760) and the owner closed
   on 2026-07-11 as the LP-vs-MIP boundary. Overnight, PJM's reserve price is
   small and the model's is zero, so **that credit does not touch the overnight
   half** (pjm-138 §7 lead 2, confirmed). The overnight +$3.40–6.82 stands on its
   own.

### §5.2 — the seam lead, measured and refuted

The census showed the model **net-exporting** 3.6–4.3 GW overnight, which would
push it up its own stack. PJM does the same in reality, and the model's error is
small and inconsistently signed — EIA-930 `Total interchange`, UTC-keyed then
shifted to the model's EST clock (the pjm-138 §5 hour-key rule):

| net import, GW | 2023 | 2024 | 2025 |
|---|---|---|---|
| h01–h04 model / measured | −4.33 / −5.16 | −3.61 / −4.71 | −3.76 / −2.47 |
| **delta** | **+0.83** | **+1.09** | **−1.29** |
| h16–h18 delta | +1.84 | +1.39 | −0.12 |
| all-hours delta | +1.15 | +1.07 | −1.01 |

Accurate to ~1 GW, and the sign **flips** in 2025. In 2023–24 the model exports
*less* than PJM did, which would make it **cheaper**, not dearer — wrong-signed
for the defect. **`import_hub_pricing` is not the overnight owner.** The cell
stays `U` (the mechanism prices import *bands*; this refutes the seam-*volume*
premise, not the mechanism), with the measurement recorded against it.

### §5.3 — and why the charter stops here

The diagnosis names its own mechanism: **hour-varying offer conduct on the
marginal rung**. Every in-model route to it is already adjudicated, and rule 28
forbids re-testing an adjudicated cell without new evidence:

* **`measured_offer_surface` PJM = `R`.** pjm-123 refuted the three-leg
  composite at the no-LP pre-check; pjm-126/127 settled the season half;
  **pjm-132 solved and refuted it at the price level** (C3a moves
  **−0.011 $/MWh** against a −4.54 gap; dispersion *narrows* in 2023/2024) and
  recorded *"Lane 2 ENDS — the measured-offer-surface family has now been tried
  as a dispersion lever under BOTH conditioning definitions."*
* **Re-binning the surface's edges is barred independently.** §4.2's finding is
  new evidence about *why* the current parameterisation is inert on this defect,
  but the remedy it suggests — finer or lower tightness bins — is a
  **re-derivation against a residual** with no change in the source data, which
  rule 23 `[R-FROZEN-DERIVE]` forbids outright. There is no admissible version
  of "re-bin it so it binds."
* **The reserve/scarcity route is owner-closed** (pjm-138 §6) and in any case
  does not reach overnight.
* **`ramp_envelopes` is spent** (pjm-140 §6): near-inert on price, and its
  PREREG §5 forbids any re-parameterisation.
* **`gas_daily_shape` and any daily gas series** — including queue item 10's
  TETCO-M3 `winter_citygate_daily` — are barred against a *diurnal* defect in
  any ISO (pjm-139 §6). §4.1 **strengthens** that bound rather than weakening
  it: the offer's within-day σ is zero on *every* leg, so no daily series can
  produce intra-day variation. **Item 10 is therefore not the successor for this
  defect either**, though it remains defensible as a rule-14 accuracy correction
  to the winter *level* on its own separate story.

So PJM's diurnal amplitude deficit is now a **DIAGNOSED, UNCLOSED structural
limitation with no admissible in-model lever** — the state NYISO's C3c lane
reached at nyiso-96/97. That is a legitimate terminal state under rule 1
`[R-STRUCT]`: the alternative is an adder tuned to the residual, which rule 13
forbids and which would make the fit better and the model worse. **It fails no
gate** — the keeper is CALIBRATED on every criterion — so nothing here is a
regression.

## §6 — DO-NOT-REDO (binding on successors)

- **Do not re-run the overnight marginal-tranche census.** It is answered on the
  keeper's own offers at 100.0 % detection, cross-validated against the
  committed W6 class census and against pjm-140's own 137,713 MW thermal
  denominator: the marginal rung at h01–h04 is **`econ` 78.7 / 78.4 / 77.5 %**,
  and the evening-peak control is identical. **The tranche is not the defect.**
- **Do not read the overnight miss as a missing cheap tier.** §3: the model's
  cheapest thermal offer is **$4.50**, *below* PJM's overnight p05 in all three
  years, and its 4.7–6.9 % share of stack below that target is the same order as
  ERCOT-136's measured 5.8–8.4 %. The miss is a few dollars on the level of the
  rung that clears (`CC_REGULAR:econ`, p05 **+$3.51 / +$5.14 / +$3.33** above
  target), not an absent tranche. §W4's "no offer cheap enough" clause is
  corrected here.
- **Do not size the overnight defect from §W4's energy shares.** §1.3: marginal
  shares are `CC_REGULAR` 44.5 / 42.3 / 40.0 %, **`CT_PEAKER` 17.4 / 20.7 /
  27.0 %**, `COAL` 21.0 / 19.9 / 15.3 %. `CT_PEAKER` is a fifth to a quarter of
  who sets the overnight price on **0.6–1.0 GW** of output, and is invisible in
  the energy view.
- **Do not treat the overnight cell and the winter morning ramp as two
  defects.** §5.1: 31 / 33 / 32 % of the overnight→peak amplitude against
  pjm-139's 26 / 21 / 18 % of the DJF h04→h07 rise. One flat-stack defect, two
  windows.
- **Do not judge any successor lever on the annual mean.** §5.1: the level
  passes by cancellation (+$6.82 / +$5.78 / +$3.40 overnight against −$7.62 /
  −$11.37 / −$22.19 at peak). Judge on the amplitude, and pre-register the
  annual-level effect.
- **Do not charter another offer-surface conditioning variant for PJM, and do
  not re-derive its bin edges against this residual.** §5.3: cell is `R` under
  both conditioning definitions (pjm-132 "Lane 2 ENDS"), and re-binning with
  unchanged source data is a rule-23 violation regardless of the cell's verdict.
- **Do not charter `winter_citygate_daily` — or any daily series — against this
  defect.** §4.1 strengthens pjm-139's bound: the within-day offer σ is
  **$0.000000** on every leg of the offer, so no calendar-day series can move an
  intra-day differential. Item 10 survives only on the winter-**level** story.
- **Do not charter `import_hub_pricing` on the overnight cell.** §5.2: the seam
  volume is accurate to ~1 GW with a sign that flips across years, and is
  wrong-signed for the defect in 2023–24.
- Carried forward unchanged and still binding **in full**: `FINDING-pjm140` §6
  (including the `ramp_envelopes` closure, the MAX-vs-p99 pre-check bound and the
  swap requirement), `FINDING-pjm139` §6, `FINDING-pjm138` §6,
  `FINDING-pjm137` §5, `FINDING-pjm136` §5, `FINDING-pjm135` §7,
  `FINDING-pjm134` §5/§8.

## §7 — the record this session changed, and the duties discharged

Rule 28 duty (b) — a session that tests or measures a mechanism updates its cell
in the same session, rejections included. No verdict moves, because no mechanism
was armed and no run solved:

- `docs/codebase-site/data/mechanism-matrix.js` — the `measured_offer_surface`
  PJM note is **extended, not replaced**, with the D-BIN bin-occupancy
  measurement (why the armed parameterisation is silent overnight) and the
  rule-23 bar on re-binning. `import_hub_pricing` PJM keeps `U` with the
  refuted overnight seam premise recorded. Header re-stamped for pjm-141.
  ERCOT's and CAISO's cells are untouched (rule 25).
- `docs/mechanism-testing-matrix.md` §5.3 — item **12 CLOSED**: its named
  instrument (the `--with-fleet` W6 census) is run and its question answered.
  Replaced with the pjm-141 diagnosis, its empty lever queue, and the
  successor lead below. Item **10's scope tightened** — barred from this defect
  by §4.1, surviving on the winter-level story alone. Item **8** (`ST_GAS`)
  confirmed closed on a second, independent measure (marginal share 1.8 / — /
  1.9 %).
- No dashboard registration: **no run was solved.** No keeper edit: **promotion
  is owner-only.**

## §8 — handover: leads stated, NOT built here

1. **The one structurally-grounded successor that is NOT adjudicated: a PJM
   overnight gas commitment bridge.** The keeper carries no commitment bridge
   (`commitment_enabled` and `pjm_commitment_posture` False), so its overnight
   commitment is purely economic, while the three P1-native bridges are
   ISO-exclusive to CAISO/ERCOT/NYISO. Arming a PJM form would floor merchant
   slow-start gas at min-load overnight, shifting marginal ownership from the
   `econ` rung (p05 $16.58–20.35) toward the cheaper `committed` rung (p05
   $14.50) — the right direction. **But its premise needs a real pre-check
   first, and T4 partially refutes it already:** the model's overnight thermal
   volume is *already* correct to ±2.6 % and CC to ±1.4 %, so a bridge must
   shift MW *between tranches of the same plants* without adding volume, and T3
   shows the LP already loads `committed` preferentially (28.79 of 36.24 GW in
   merit, 79 %, vs `econ` 15.08 of 48.72, 31 %). It needs a new
   `ScenarioConfig` field, a matrix row in the same PR (rule 28 duty c), owner
   sign-off, and a PREREG committed before any arm.
2. **The amplitude is the right target statistic from here**, not the overnight
   level in isolation — and it must be scored at both ends, because the peak end
   is the owner-closed reserve lane and only the overnight end is open.
3. **An owner-lane item:** `keepers/PJM.json` root cause (15) names the W6
   census as "the next instrument". It is now **run and answered**, so (15)
   should be restated to the pjm-141 diagnosis — the flat-stack amplitude defect
   and its empty lever queue. This session does not edit the keeper shard.
4. Carried from pjm-137, still open and still blocked: a `PJM_Dominion`
   NoVA/Loudoun split needs a measured sub-zonal load basis.

## §9 — reproduction

```
PYTHONPATH=. .venv/bin/python scripts/probes/_pjm141_overnight_tranche.py \
    --bundle results/calibration/pjm140_rampenv_B \
    --out results/probes/pjm141_overnight_tranche.json
PYTHONPATH=. .venv/bin/python scripts/probes/_pjm139_winter_ramp.py \
    --bundle results/calibration/pjm140_rampenv_B --with-fleet \
    --out results/probes/pjm141_w6.json
```

One fleet reconstruction per year, ~7 min and ~4 GB each, **no LP** — so no swap
is required for either probe (unlike a keeper re-solve, which needs it per
pjm-140 §2). `results/probes/` is gitignored; the numbers above are the record
and the probe scripts are committed.

`data/raw/pjm-zonal-lmp/`'s 36 DA parquets are **gitignored** — only the
`SHA256SUMS.txt` manifest is committed — so they must be re-fetched
(`--feeds da_hrl_lmps`). All 36 came back **byte-identical to the committed
manifest** (sha256 + size, 36/36), a clean reproducibility check on PJM's own
feed. The fetch rewrites `SHA256SUMS.txt` with only its own feed's entries, so
`git checkout -- data/raw/pjm-zonal-lmp/SHA256SUMS.txt` was run afterwards and
both feeds' 36+36 entries are intact.
