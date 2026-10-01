# FINDING — caiso-250: the ranked-first object is **NOT a new object**. In the caiso-249 `STORAGE` cell a **storage charge column is the marginal buyer**, and **44 / 60 / 57 %** of the cell's 2023 / 2024 / 2025 gap lies **inside caiso-168's already-adjudicated belly-surplus mask** — with the remainder the SAME state in hours that cut excluded, concentrated in a single hour-of-day (**Pacific 07–08 carries 9–24 % of the WHOLE C3a gap**). The instrument-class census that closed the belly is **mask-independent**, so widening the hours opens no new channel. **HYDRO IS REFUTED** as the carrier — it is interior in **93–96 % of ALL hours**, so the census leg is near-vacuous, and its within-zone-month λ IQR is **$11–15**, not a water value. **ZERO SOLVES. 7 of 10 predictions hold, 3 FALSIFIED — and one of the 7 held VACUOUSLY.**

**Session caiso-250, 2026-09-05.** Branch
`claude/caiso-250-backcast-calibration-7tci3e` off `main` `182aa74a`. Keeper
**`2026-09-05-caiso-246-b1-spot`** (`caiso246_b1_spot_coverage`, `git_sha`
`900402b`) **UNCHANGED**, NOT-YET, C3a +3.9 / +12.3 / +11.4 %. Pre-registration:
`PRECOMMIT-caiso250-lambda-carrier-2026-09-05.md`, pushed to `origin` before
the estimator was written and before any cell of the object was computed.
**Nothing armed — no `ScenarioConfig` field, no flag, no derive, no LP, no run
registered, no promotion.** Rule 22 `[R-HOLDOUT]`: 2023–2025 only, hard-filtered
and fail-closed; CAISO holds no `complete` and no `final` marker; the holdout
freeze is ACTIVE.

---

## §1 — THE RESULT

caiso-249 handed forward, ranked first: *"what sets λ when no thermal unit is
marginal?"* — **43.4 % (2024) / 55.0 % (2025)** of the C3a gap in a residual
cell with no identified price-setter. The answer is that the cell is **mostly
an object this lane closed thirteen months of sessions ago**, plus the same
mechanism in hours its cut did not reach.

### §1.1 — Where the cell actually sits

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| whole-year C3a gap ($/MWh) | 1.3071 | 3.7812 | 3.1507 |
| `STORAGE` cell gap | **0.8368** | **1.6395** | **1.7340** |
| … of which **INSIDE caiso-168's belly-surplus mask** | **0.3683** | **0.9861** | **0.9888** |
| … as a share of the CELL | **44.0 %** | **60.2 %** | **57.0 %** |
| … as a share of the WHOLE YEAR's gap | **28.2 %** | **26.1 %** | **31.4 %** |
| … OUTSIDE that mask | 0.4684 | 0.6534 | 0.7452 |
| … as a share of the whole year's gap | 35.8 % | 17.3 % | 23.6 % |

The mask is caiso-168's own, carried **verbatim and never re-chosen here**:
Pacific `[09,16)` and measured CA day-ahead hub ≤ $20/MWh (1,116 / 1,604 /
1,623 hours). caiso-168 §1–§2 established, on the reduced-cost argument and
with a month × measured-hub-decile matched control, that in those hours **a
storage charge column is the marginal buyer and its bid is the zone's dual**.
That verdict is carried, **not re-measured** (its DO-NOT-REDO item 2).

Adding the `DOM_GAS` cell's own overlap (0.2097 / 0.4657 / 0.1392), those
1,116 / 1,604 / 1,623 belly-surplus hours — **12.7 / 18.3 / 18.5 % of the
year** — carry **at least 44.2 / 38.4 / 35.8 %** of the whole year's C3a gap.

### §1.2 — The part OUTSIDE the mask is the SAME state, in ONE hour of the day

Post-registration characterisation (§4.4), not a labelling rule. The
outside-mask remainder of the cell has a sharply peaked diurnal profile, and
the peak is **not** the evening:

| hour (Pacific) | 06 | **07** | **08** | 09 | 17 | 18 | 19 |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2023 gap $/MWh | −0.031 | **+0.115** | **+0.194** | +0.086 | −0.043 | −0.114 | −0.112 |
| 2024 | +0.046 | **+0.101** | **+0.240** | +0.005 | −0.035 | −0.034 | +0.010 |
| 2025 | +0.036 | **+0.138** | **+0.212** | +0.041 | −0.030 | +0.007 | +0.011 |

**Hours 07–08 alone carry +0.309 / +0.341 / +0.349 $/MWh — 23.6 / 9.0 / 11.1 %
of the WHOLE year's C3a gap**, and 65.9 / 52.1 / 46.9 % of the outside-mask
cell. The evening ramp (17–19) is **negative or negligible** in every year.

And the storage state there is the same one caiso-168 identified. Load-weighted
gap of the outside-mask cell by column state (states OVERLAP — a hour can have
both techs interior — so the rows do not sum):

| state | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| li_ion **charge** interior | **+0.658** | **+0.428** | **+0.450** |
| pumped-storage **charge** interior | **+0.579** | **+0.413** | **+0.382** |
| li_ion **discharge** interior | −0.273 | +0.035 | +0.093 |
| pumped-storage **discharge** interior | +0.014 | −0.000 | +0.178 |
| **no storage column interior at all** | −0.091 | +0.009 | +0.002 |
| (cell total, outside mask) | 0.468 | 0.653 | 0.745 |

The **charge**-side columns carry it, exactly as inside the belly; the
discharge side does not; and the hours where **no** storage column is interior
carry essentially **nothing** (−0.091 / +0.009 / +0.002 $/MWh — under 1 % of
the year's gap in 2024/2025). **caiso-168's object is larger than caiso-168's
mask.** The belly cut (a *measured*-hub surplus test in `[09,16)`) simply does
not reach the Pacific 07–08 morning charging hours or the shoulder hours where
the measured hub sat above $20.

### §1.3 — Why widening the hours opens no new channel

caiso-168 §5's instrument census — the class that could reach a
charge-side-marginal battery is the **already-armed `caiso_storage_shape_anchor`**,
re-picking whose p95 percentile against a residual is barred three ways (rule 23
`[R-FROZEN-DERIVE]`, rule 13 `[R-MEASURED]` outcome-pinning, rule 19
`[R-ONE-MECH]` stacking), and the pumped-storage limb's capability envelope is
**not derivable from public data** (the owner-ledgered C3a-2025 wall,
caiso-141/145) — is a census over **instrument classes, not over hours**. It
therefore transfers to the morning-ramp hours unchanged. Widening the object's
time window does not create an admissible lever that the belly did not have.

### §1.4 — HYDRO IS REFUTED, and my own registered prediction "held" vacuously

PRECOMMIT §0.1 named the one candidate no price-match instrument in this lane
can see: `_build_hydro_rows` puts a **monthly energy-budget row per (hydro unit,
month)** in this LP (`hydro_dispatch_envelope` / `hydro_budget_nameplate_aware`
/ `hydro_min_flow_floor` all ARMED), so a marginal hydro unit prices
`λ_z = mc_g + w_{g,m}` with the water value `w` **absent from `mc`**. It is
refuted on two independent measurements:

1. **The census leg is near-vacuous.** ISO hydro is strictly inside its hourly
   envelope in **8,400 / 8,119 / 8,150 of 8,760 hours — 95.9 / 92.7 / 93.0 % of
   the entire year.** P-4 ("hydro interior in ≥ 60 % of the cell") therefore
   held at 90.8 / 84.2 / 91.5 % **for a reason that carries no information**.
   Reported as a vacuous hold, not a result.
2. **There is no common water value.** In `STORAGE ∧ hydro-interior` zone-hours
   the within-(zone, month) λ IQR is **$14.84 / $12.13 / $11.40** (weighted
   median over 60 zone-months each year; weighted p75 $19.25 / $13.72 / $13.56)
   against a registered ≤ $3.00. A monthly budget dual is ONE number per
   unit-month; λ moving by $11–15 inside a zone-month is not it. **P-7
   FALSIFIED by 4–5×.**

### §1.5 — caiso-249's wedge sentence is QUALIFIED — my own, and it was over-read

caiso-249 published *"the nearest AVAILABLE own-zone thermal offer sits ABOVE λ
in 64.7 / 65.7 / 69.8 % of the load-weight … λ sits JUST UNDER the thermal
stack"*. Measured on BOTH sides here:

| `STORAGE` zone-hours, $/MWh | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| median distance to nearest offer **ABOVE** λ | 1.390 | 1.002 | 1.227 |
| median distance to nearest offer **BELOW** λ | 1.293 | 0.657 | 1.423 |
| ratio below ÷ above | **0.93** | **0.66** | **1.16** |
| the same, `DOM_GAS` zone-hours (above / below) | 0.183 / 0.177 | 0.156 / 0.167 | 0.156 / 0.171 |

λ sits **roughly equidistant** from the rung above and the rung below — **P-9
HOLDS**. Every available unit at its lower bound satisfies `mc ≥ λ` at ANY
optimum, so a positive nearest-offer wedge is **mechanical** and carries no
information about the carrier. What the two-sided reading DOES say is different
and useful: the offer stack near λ is **6–8× sparser** in `STORAGE` hours
($1.0–1.4 to the nearest rung either way) than in `DOM_GAS` hours ($0.16–0.18)
— λ sits in a **gap in the thermal stack**, which is what a non-thermal column
setting the price looks like.

---

## §2 — GATES

| gate | 2023 | 2024 | 2025 |
|---|---|---|---|
| **G-REPRO** (labels reproduce the committed caiso-249 artifact) | **PASS, max diff 0.000000** | **PASS 0.000000** | **PASS 0.000000** |
| **G-FLEET′** (the caiso-249 §6 item 3 repair, registered in advance) | **PASS** | **PASS** | **PASS** |
| **G-CONSERVE** (cells sum to gap = caiso-248's) | PASS 1.3071 | PASS 3.7812 | PASS 3.1507 |
| **G-BENCH** | PASS | PASS | PASS |
| **G-CAP** (armed caps dominate the dispatch) | PASS | PASS | PASS |
| **G-HOLDOUT** | PASS | PASS | PASS |

**G-REPRO matched to machine zero on every regime, every year** — the
reproduction of caiso-249's labelling is exact, so this session's cells are
that session's cells.

**G-FLEET′ closes caiso-249 queue item 3.** caiso-249's G-FLEET keyed its
phantom test on caiso-248's SHAPE heuristic and consequently FAILED 2023 on a
documented false positive. Re-keyed on the solver's authoritative
`run_calibration_full._INJECTED_MUSTRUN_CLASSES = ("biomass", "OTHER")` — a
class counts as injected only if it is in that tuple **and** shape-detected —
the gate passes all three years, and the artifact records exactly what the
repair drops: 2023 `oil` (`false_positives_dropped_by_the_repair: ['oil']`,
`families_the_caiso249_gate_would_have_flagged: ['fuel:oil']`), nothing in
2024/2025. **caiso-249's published record stands as published, with its FAIL**
— the repair lives in this session's probe, which registered it in advance; a
committed evidence artifact is not rewritten to convert its own gate failure.

**G-CAP** is stronger than caiso-168's inversion: the armed bounds are
reconstructed by calling the shipped builders (`caiso_storage_shape_caps`,
`caiso_ps_charge_caps`) on the rebuilt fleet, so they are the LP's own. Maximum
dispatch-over-cap across all three years and both techs: **0.0006 MW**.

---

## §3 — PREDICTIONS, SCORED AGAINST INTEREST

| # | registered | measured | verdict |
|---|---|---|---|
| P-1 | G-REPRO within 0.001 | 0.000000 all years | **HOLDS** |
| P-2 | G-FLEET′ passes ALL THREE years incl. 2023 | passes; drops `oil` exactly as diagnosed | **HOLDS** |
| P-3 | a storage column interior in ≥ 70 % of cell weight | **86.3 / 89.9 / 93.3 %** | **HOLDS** |
| P-4 | hydro interior in ≥ 60 % of cell weight | 90.8 / 84.2 / 91.5 % | **HOLDS — VACUOUSLY** (§1.4: hydro is interior in 93–96 % of ALL hours) |
| P-5 | BOTH interior in ≥ 40 % of the cell, so the census CANNOT name a winner | **82.2 / 81.6 / 89.0 %** | **HOLDS** — the stop rule fires |
| P-6 | ≥ 25 % of cell weight on λ repeating ≥ 5× in its (zone, month) **AND** < 10 % in `DOM_GAS` | STORAGE **45.4 / 54.8 / 61.2 %** ✓; DOM_GAS **17.6 / 27.6 / 30.5 %** ✗ | **FALSIFIED** (§4.2) |
| P-7 | λ IQR ≤ $3.00 in hydro-interior STORAGE hours | **$14.84 / $12.13 / $11.40** | **FALSIFIED by 4–5×** — hydro refuted |
| P-8 | ≥ 35 % of the 2025 cell GAP inside caiso-168's mask | **57.0 %** (2024 60.2 %, 2023 44.0 %) | **HOLDS, and larger than registered** |
| P-9 | nearest offer below within 3× of above | ratio **0.93 / 0.66 / 1.16** | **HOLDS** — my own caiso-249 sentence is qualified |
| P-10 | no single named carrier > 60 % of the cell's gap | `BOTH` = **132.8 / 92.3 / 102.1 %** | **FALSIFIED** — the census collapses entirely onto the joint cell |

**7 hold, 3 falsified**, and P-4's hold is vacuous, so the honest count of
*informative* holds is 6.

---

## §4 — DISCLOSURES AGAINST INTEREST

### §4.1 — The ranked-first object was mostly closed before this session opened, and the lane ranked it first anyway

caiso-249 §6 item 1 was written as a new object and the handoff ranked it first
at 43–55 % of the gap. It is, on this measurement, **44–60 % literally
caiso-168's belly-surplus object** and the remainder is the same charge-side
state in hours caiso-168's cut excluded. caiso-168 is cited five times in the
CAISO lane's own DO-NOT-REDO chains; **the overlap was never measured** because
the two sessions defined their masks differently (a model-λ residual cell
versus a measured-hub surplus window) and nobody crossed them. That is a
process failure in the lane's queue-ranking, not a discovery.

### §4.2 — The dual-signature instrument does NOT discriminate, and I registered it as if it would

P-6's premise was that exactly-repeating λ within a (zone, month) is the
fingerprint of an inter-temporal dual. The `STORAGE`/`DOM_GAS` contrast is real
and large (45.4/54.8/61.2 % against 17.6/27.6/30.5 % at ≥ 5 repeats; 33.5/37.2/
45.6 % against 8.3/15.2/17.7 % at ≥ 10) — but `DOM_GAS`'s own share is **2–3×
my registered ceiling**, and the reason is obvious in hindsight: this keeper
prices gas on **daily** citygate spot prints, so a marginal thermal unit's `mc`
is constant across the hours of a day and `λ = mc` repeats exactly too. The
signature is **not specific to inter-temporal duals** and the prediction is
FALSIFIED as written. The contrast is reported as a ratio, never as an
identification.

### §4.3 — Everything here is ISO-AGGREGATE, and the census over-identifies

`storage_<year>.parquet` carries no zone (caiso-168 §7) and `class_hourly`
carries no zone, so both the storage and the hydro interiority tests are
**fleet-level necessary conditions**: a fleet strictly inside its aggregate
bound does not prove any single unit is interior (a mix of at-cap and zero
units reproduces it), and with `caiso_zonal_loss_surface` armed the CA zones
carry different duals. **No causal claim is made.** caiso-168's belly verdict
has a month × measured-hub-decile matched control behind it; this session has
**none**, and the state/dual endogeneity caiso-168 §2 stated is unaddressed
here. Stage 6 is a **state census**, not a counterfactual.

### §4.4 — Stage 6 is a DESCRIPTION of a registered cell, not a new labelling rule

PRECOMMIT §3's stop rule forbids reaching for another labelling rule after the
census collapses. The hour-of-day profile and the column-state split in §1.2
relabel nothing, change no cell, and are excluded from every scored prediction
— the caiso-247/249 group-characterisation convention.

### §4.5 — The scarcity overlay was NOT measured, deliberately

`caiso_scarcity_pricing = True` and the adder is folded into the persisted
price (`runner.py`: `result.prices = result.prices + caiso_adder`), so the
committed `system_<year>.parquet` `price` is `λ_LP + A(t)`. **caiso-229 already
bounded `A(t)` at $0.017 / $0.006 / $0.003 per MWh** on CAISO's own constants
against caiso-131 §4's committed minimum-headroom hour. It is **cited, never
re-derived** (PRECOMMIT §0.2), and it is 12–100× smaller than the distances
measured in §1.5, so it is not the carrier. Recorded because a reader of the
price-match instruments in this lane should know the committed price is not
literally the raw dual — and that the difference is bounded and inert.

### §4.6 — Two of the handoff's four constraint falsifiers were decided by the RECIPE, before measurement

The handoff named "reserve co-optimisation, ramp, the RA must-offer floor, or
the ORDC scarcity adder" as the carrier if λ does not track a storage or hydro
dual. Read off the keeper's `run_config.json` in PRECOMMIT §0.1, before
measuring: **`ramp_limits = False`** (no ramp rows exist) and
**`caiso_reserve_coopt = energy_reserve_coopt = False`** (reserves are not in
the energy balance), so neither can be a carrier in this LP at all. The RA
must-offer floor is a **bound**, not a row: a unit at a min-gen floor has
`mc ≥ λ` and explains why the thermal stack sits above λ — it never sets the
price. The ORDC adder is §4.5. The falsifier list was, in this recipe, already
half-empty.

### §4.7 — What did NOT change

`gap_hourly` and every caiso-249 cell (G-REPRO exact), the HUB acquittal, the
CC-hot / CT-cold split, the weight-basis disclosure (caiso-247 §4.5, still NOT
offered as a reduction of C3a), the DOM_GAS/STORAGE tolerance sensitivity
(caiso-249 P-9: **no DOM_GAS share is quotable**, and this session quotes none),
and the demotion of the import seam and the two fitted firm prices as C3a
objects.

---

## §5 — WHAT THIS DOES NOT DO

It arms nothing, changes no keeper, registers no run, proposes no mechanism and
touches no other ISO's shard. It does **not** re-open caiso-168's belly verdict,
caiso-169's refusal of `storage_daily_cycling`, the PS wall, or the armed
`caiso_storage_shape_anchor`'s percentile. It does **not** adjudicate the
DOM_GAS/STORAGE boundary — that stays unquotable. It makes **no causal claim**
about the outside-mask hours (§4.3).

---

## §6 — THE QUEUE, RE-RANKED

1. **DE-RANKED: caiso-249 item 1 is substantially CLOSED.** 44–60 % of the
   `STORAGE` cell is caiso-168's adjudicated object and the remainder is the
   same charge-side state; §1.3's instrument-class census is mask-independent,
   so there is no new admissible lever behind it. It should not be funded again
   as a C3a lever.
2. **NEW, and concrete: the Pacific 07–08 morning-ramp slab.** +0.309 / +0.341 /
   +0.349 $/MWh — **9–24 % of the whole C3a gap in two hours of the day**,
   outside caiso-168's mask, charge-side-marginal. What it needs first is
   **caiso-168's matched control re-run on that mask** (a month × measured-hub-
   decile pairing of interior against at-cap hours), because this session has
   none. If the control transfers, the object is the same one and it is closed
   with it; if it does not, that is a genuinely new question about the morning
   ramp.
3. **The missing artifact that would end the ISO-aggregate caveat:** a
   **per-zone** storage sidecar (`storage_<year>.parquet` carries only `tech`)
   and a per-zone (or per-klass-per-zone) generation column. `_storage_frame`
   (`scripts/run_calibration_full.py` L1589) already has the units in hand and
   groups them by `tech` only; the class frame likewise. Adding a `zone` key at
   persist time would make every future zonal complementarity test EXACT rather
   than necessary-only, and would end the caveat in §4.3 for every ISO. Filed as
   an all-ISO instrument ask, not a CAISO lever, and NOT sized here.
4. **The CC-hot / CT-cold split** (caiso-247 §4.7, caiso-249 P-8) — unchanged,
   still live, still needs a functional-form charter. **Now the highest-ranked
   genuinely-open C3a object.**
5. **The DOM_GAS/STORAGE boundary stays unquotable** (caiso-249 P-9, 32 points
   of tolerance sensitivity).
6. **Demoted and unchanged:** the import seam (5.1 / 7.8 % of the gap) and the
   two fitted firm prices — structural objects under rule 1, not C3a levers.
7. **Owner asks carried:** the C3a weight basis (caiso-247 §4.5); the EIA-NA
   back-fill question for other ISOs' lanes; the transport adder on a
   spot-indexed marginal offer (caiso-244 ask E).

---

## §7 — DO-NOT-REDO ADDS

1. **Never re-fund "what sets λ in the caiso-249 STORAGE cell" as a new
   object.** 44 / 60 / 57 % of it is caiso-168's belly-surplus object measured
   directly, and the remainder is the same charge-side-marginal state outside
   that cut. caiso-168 §8 items 1–5 govern the whole cell, not just the belly.
2. **caiso-168's §5 instrument census is MASK-INDEPENDENT.** It censuses
   instrument CLASSES, not hours, so extending the object's time window does
   not open a charge-side channel. Never propose a new charge-side cap, floor,
   adder or hurdle for the morning-ramp hours either.
3. **HYDRO NEVER SETS THE CAISO PRICE IN A WAY THIS LANE CAN USE.** It is
   strictly interior in **93–96 % of ALL hours**, so "hydro is interior" is
   near-vacuous as a test, and its within-zone-month λ IQR is $11–15, not a
   water value. Never propose the hydro monthly-budget dual as the carrier of
   the C3a residual, and never quote a hydro-interiority share as evidence.
4. **Exact-repeat λ multiplicity does NOT discriminate an inter-temporal dual
   from a thermal one** on this keeper: daily citygate spot pricing makes a
   marginal thermal unit's `mc` constant within a day, so `DOM_GAS` hours repeat
   too (17.6 / 27.6 / 30.5 % at ≥ 5). Quote the STORAGE:DOM_GAS ratio if
   anything, never the level as an identification.
5. **Never read caiso-249's positive nearest-offer wedge as evidence of a
   carrier.** `mc ≥ λ` holds for every available unit at its lower bound at ANY
   optimum; the two-sided medians are near-symmetric (ratio 0.93 / 0.66 / 1.16).
   What the wedge measures is **stack sparsity** — 6–8× sparser near λ in
   `STORAGE` hours than in `DOM_GAS` hours.
6. **The committed `system_<year>.parquet` `price` is `λ_LP + A(t)`,** the
   post-solve CAISO scarcity adder — bounded by caiso-229 at
   $0.017/$0.006/$0.003 per MWh. Cite the bound; never re-derive it, and never
   assume the sidecar price is the raw dual without it.
7. **`ramp_limits` and the reserve co-opt are OFF on the CAISO keeper** — a
   ramp dual or a reserve dual cannot carry any CAISO residual. Check the
   recipe before naming a constraint as a candidate carrier.
8. caiso-249 §7, caiso-248 §8, caiso-247 §8, caiso-246 §8, caiso-245 §7,
   caiso-244 §7, caiso-243 §10, caiso-242 §9, caiso-241 §10, caiso-240 §7,
   caiso-239 §8, caiso-230 §9, caiso-169, caiso-168 §8 stand in full.

---

## §8 — DELIVERABLES

`PRECOMMIT-caiso250-lambda-carrier-2026-09-05.md` (pushed first);
`scripts/probes/_caiso250_lambda_carrier_anatomy.py` +
`results/calibration/_caiso250_lambda_carrier_anatomy.json`; this finding; the
`docs/calibration-log/caiso.md` entry; an **evidence-only** append on the CAISO
matrix shard. **No cell verdict moves; no mechanism was tested; no run
registered; keeper unchanged.**

**Next number: caiso-251.**
