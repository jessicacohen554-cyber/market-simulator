# DIAGNOSIS — ERCOT-134: ERCOT coal is CAPACITY-PINNED, not price-set — ~45 % of its online plant-hours sit AT a legacy statistical availability ceiling that ERCOT's own COP declaration contradicts, so no merit-order work on ERCOT coal has ever been validated against anything

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot134-coal-pin ·
**Keeper** `2026-07-28-ercot129-conditional-coal-min` (bundle
`results/calibration/ercot129_conditional`) — **unchanged by this document** ·
**Method** Phase 1 — no LP, no solve. Every number below is re-verified this
session from the committed tree: the keeper's committed dashboard payload, the
keeper's own fleet-array availability captured at the exact point the LP
consumes it (`ercot130_capoff_phase1.capture_availability`, regenerated on
current HEAD), CAMPD unit-level operation, the 60-Day DAM accepted COP, and
the committed `hourly/` sidecars of the registered `ercot116` / `ercot122`
probe bundles. Default `ScenarioConfig().cache_key()` verified
`603c2498bf71d21d` at session start.
**Reproduction:** `scripts/probes/ercot134_coal_availability_pin.py`
(committed with this document — §8). The ERCOT-130 §4 table this synthesis
leans on was previously **not reproducible from the repo**; now it is.

**This is the synthesis document for the coal availability-pin lane.** It
consolidates what ERCOT-130 §4/§6 discovered, ERCOT-132 leg B independently
corroborated, and ERCOT-116 measured — into one statement with one
consequence, and pre-commits the ERCOT-116 re-solve A/B
(`PRECOMMIT-ercot134-coal-avail-regate-2026-07-28.md`) that sizes it on the
current keeper.

---

## 1. Coal is the ONLY thermal class still on the legacy statistical availability model

`ercot_thermal_dam_availability=True` arms the measured COP-declared
availability overlay for the ERCOT thermal fleet, but the sub-flag
`ercot_thermal_dam_availability_coal=False` carves coal out — verified in the
keeper's `run_config.json` and in the code: `src/market_sim/data/fleet/
arrays.py:1292` and `:1312` drop every `COAL*` class from the measured class
dicts unless the sub-flag is armed, and the plant grain only forms
`mapped_plants` for classes already in the measured dict, so a coal plant in
the crosswalk is unreachable while the gate is off. Any keeper-recipe solve
log shows the plant-grain redistribution firing for `CC_REGULAR` /
`CT_PEAKER` / `ST_GAS` and **no coal line** (ERCOT-130 §0 verified this in
the live log).

This was never a decision that coal's estimate is good. ERCOT-110 added the
coal rows to the deriver's artifacts and gated them off so a re-derive could
not move a keeper; ERCOT-116 armed the gate, measured the consequence, and
was rejected on level (§6 below); nobody implemented a coal deflation —
**coal was excluded from the fix, not fixed.**

## 2. The legacy estimate sits BELOW ERCOT's own declaration — and below actual p95 output

2025, mean over online hours, model available capacity / COP declared HSL
(probe output; COP `live_mw` is the fleet's own filed availability, an ERCOT
HSL, NET):

| plant | model avail / COP declared | model mean avail (MW) | actual p95 (MW) |
|---|---|---|---|
| W A Parish | **0.774** | 1,611 | 2,334 |
| Martin Lake | **0.861** | 1,228 | 1,527 |
| Limestone | **0.884** | 1,051 | 1,496 |
| Major Oak | **0.903** | 259 | 316 |
| Oak Grove | **0.936** | 1,405 | 1,663 |
| J K Spruce | **0.994** | 852 | 1,161 |

The model's mean available capacity is below the plant's **actual p95 net
output** at all six — the estimate does not merely disagree with the filing,
it is contradicted by what the plant measurably delivered. Fleet-wide, actual
output exceeds the model's *entire available capacity* for the plant in
22,633 / 24,627 / 30,697 plant-hours (2023/2024/2025) — per plant,
1,200–6,800 hours a year (Major Oak 2025: 6,842; W A Parish 2025: 4,448 —
reproducing ERCOT-130 §4's published table to ~1 % on current HEAD). In such
an hour no offer curve, at any price, can reproduce reality.

## 3. Coal is capacity-pinned, not price-set

Share of the model's online coal plant-hours dispatched AT the availability
ceiling (half-quantization-step tolerance per ERCOT-130 §1):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| fleet pin share | 31.9 % | 33.0 % | **45.2 %** (33,338 / 73,737) |
| Oak Grove | 79.5 % | 73.8 % | **89.4 %** |
| Major Oak | 70.1 % | 67.0 % | **84.1 %** |

In a pinned hour the binding constraint is the availability bound; the offer
price is irrelevant. Between the pin (§3) and the impossible hours (§2), the
availability estimate — not the offer curve — is what sets roughly half of
ERCOT coal's dispatch.

## 4. Therefore merit order has never been tested on ERCOT coal

While the pin holds, no coal offer-curve lever can be validated: the LP is
not choosing coal on price in the pinned hours, and in the impossible hours
it *cannot* reach reality whatever the price. ERCOT-132 leg B is the
independent proof from the other side (re-verified from the committed
`ercot122_offerlevel` sidecars): moving **6.4 GW** of coal offer LEVEL onto
the measured fleet-representative value changed coal energy by at most
**0.184 TWh** on a ~60 TWh class (−0.184 / +0.034 / +0.150 by year) — and
regressed G1 19/21 → 18/21. A price lever cannot move a
quantity-constrained block. The defect ERCOT-122/132 named as REACH is, at
plant grain, this pin.

## 5. The annual total looks fine for the wrong reason

Keeper coal (P1 `class_hourly` sidecars) vs actual (committed EIA-923 bench):

| year | keeper | actual | err |
|---|---|---|---|
| 2023 | 60.791 | 60.420 | +0.371 |
| 2024 | 58.414 | 57.617 | +0.797 |
| 2025 | 61.047 | 62.214 | −1.167 |

Too little available capacity run too hard — ~45 % of it flat against an
understated ceiling — landing on the right annual number. That is rule 1
`[R-STRUCT]`'s exact pattern: the right number through a mechanism that is
not real. The C1 pass is not evidence the coal representation is correct; it
is evidence the availability error and the merit-order bias currently cancel.

## 6. The carve-out is load-bearing for the fit

ERCOT-116 armed the measured coal availability
(`2026-07-26-ercot116-coal-avail-probe`, on the then-keeper ercot115) and
coal over-ran actual by **+5.7 / +8.9 / +11.0 TWh** (66.108 / 66.521 /
73.163 vs 60.420 / 57.617 / 62.214; +6.8 / +9.2 / +12.9 vs its
contemporaneous keeper) — which got it rejected on level (G3: C3a degrades
5.6–7.6 pp). That over-run is **not the cost of measured data** — it is the
coal-vs-gas merit bias becoming visible once coal is un-pinned. The
statistical estimate's too-tight envelope was silently absorbing a real
mid-merit ranking bias (the ERCOT-116 finding's own §4.2: corr(dCoal, dGas)
= −0.93 to −0.97, the surplus coal is exactly the missing gas). This is rule
14 `[R-ACCURATE]` nearly verbatim: *if swapping a hand estimate for real
data makes the backcast worse, something else is miscalibrated and the
estimate was silently compensating for it. Do not bury the error back inside
an inaccurate input.*

## 7. ERCOT-130 §4 is sound — audited, not an artifact

Two candidate artifacts were tested and both ruled out
(`ercot134_coal_availability_pin.py --audit`):

* **(a) dual-fuel contamination.** W A Parish is the ONLY dual-fuel plant in
  the set (2025 gross: 14.72 TWh coal + 2.04 TWh pipeline gas under one
  CAMPD facilityId). The model splits it: plant 3470 COAL (`H_COAL1`) /
  synthetic 34702 ST_GAS (`H_STGAS1`); `campd_coal_gross` filters
  `primaryFuelInfo` on Coal|Lignite and `SITE_TO_PLANT` maps only
  `WAP_WAP_G5..G8`. Had §4 scored the whole facility (raw gross basis),
  Parish would read **6,213** impossible hours, not 4,448.
* **(b) gross-vs-net.** §4 correctly applied the COAL_PLANTS-scoped
  gross→net anchor (0.8972 / 0.9051 / 0.9069 by year). Unconverted, Oak
  Grove 2025 would read **6,325** impossible hours, not 3,613.
* **The anchor trap, recorded for successors:** the anchor MUST be computed
  over the ERCOT `COAL_PLANTS` set only. Over all Texas coal facilities in
  the CAMPD extract it is **0.8037**, which deflates every actual by a
  further ~11 % and makes §4 look ~50 % inflated — this produced a wrong
  intermediate answer in the ERCOT-132 session before being caught. The
  probe hard-asserts the anchor stays in [0.85, 0.95].

Small deltas vs the published §4 table (Oak Grove 3,488 → 3,613, Major Oak
6,727 → 6,842, fleet ~+1 %) are the current-HEAD availability — the merged
Sandy Creek repair (ERCOT-132 D2/D3) restored Sandy Creek's 2025
availability (now 0.137 mean fraction, 376 impossible hours, vs dark all
year / 1,300 running hours before), which also slightly moves the shared
class-level statistical inputs. This is exactly why Phase 2 mandates a fresh
BASE (§9).

---

## 8. THE CONSEQUENCE — stated plainly

**No merit-order work on ERCOT coal — offer levels, marginal-HR bounds,
passthrough sigmoids, the min-config floor — has been validated against
anything**, because ~half of coal's dispatch is set by an availability
estimate rather than by price. Every coal offer-curve verdict on the books
(the ercot115 marginal-HR floor's effect size, ercot122/132's level
refutation, the sigmoid parameters' apparent adequacy) was scored on a fleet
whose dispatch quantity was largely fixed before the offer curve was
consulted. The verdicts that REJECTED price levers remain sound — they
showed a price lever cannot move a pinned block, which is precisely this
diagnosis. But nothing affirmative about the coal offer surface is known,
and nothing can be until the pin is lifted.

**Reproduction:** `scripts/probes/ercot134_coal_availability_pin.py` —
default mode scores the keeper payload against the captured fleet-array
availability, the COP declaration and CAMPD actuals (regenerating the
gitignored `_ercot130_avail_cache` if absent, ~2 min/year, no LP);
`--bundle DIR` scores a solved bundle's `hourly/unit_hourly_<year>.parquet`
directly (used by Phase 2); `--audit` reproduces §7.

## 9. Phase 2 — the ERCOT-116 re-solve A/B this document pre-commits

ERCOT-116's numbers are stale twice over: solved against the ercot115 keeper
(two promotions ago — ercot128/129 added the coal min-config floor), and
before the Sandy Creek availability repair. Phase 2 re-runs the A/B on the
current keeper recipe at current HEAD — BASE (recipe unchanged) vs ARM
(single delta `ercot_thermal_dam_availability_coal=true`) — to **size the
un-pinning and expose the merit bias**, NOT to produce a keeper. Gates,
predictions and the decision rule are pre-registered in
`docs/PRECOMMIT-ercot134-coal-avail-regate-2026-07-28.md`, pushed before any
solve. The expected outcome is that the ARM FAILS on level (C1/C3a) — that
is the measurement, not the verdict.

## 10. The successor this lane sets up (chartered, NOT started)

If the ARM un-pins coal (ceiling-pin share falls toward the measured
~20 %) and the over-run appears, the named successor is the **coal-vs-gas
MERIT-ORDER lane on the un-pinned fleet** — the first time ERCOT coal merit
can actually be calibrated. Its charter, from the evidence already on file:

* **Target:** the mid-merit ranking bias ERCOT-116 §4.2 located — coal
  priced too cheap relative to gas in the $15–25 bands where both are
  marginal (arm B's gap vs the measured envelope was +9–29 pp exactly
  there), with the displaced quantity landing 1:1 in gas
  (corr(dCoal, dGas) −0.93 to −0.97).
* **Instruments, in evidence order:** the F923 delivered-coal-price
  receipts question (ERCOT-112 §6 — the model's full-passthrough coal SRMC
  tops near $28/MWh vs the real fleet's ~$21 top submitted DAM coal offer);
  the take-or-pay/committed share and the PRB/lignite sigmoid floors (0.76 /
  0.675) — the low/mid tranches, NOT the level (rejected, ercot132 leg B)
  and NOT the pooled `econ_high` 2.856 (frozen, ercot122 §5.2).
* **Gate:** the ERCOT-116 metrics (matched-band excess + spread + C3a) with
  the measured envelope ARMED — the compensator must not be re-tuned around
  the estimate (rule 14). Exit criterion per the ERCOT-116 finding: the
  measured envelope re-armed and passing.
* **Do not start it in this lane.** It requires an owner ruling on
  ERCOT-116 adoption first (§11).

## 11. Owner decisions — surfaced, NOT decided here

1. **ERCOT-116 adoption.** This lane MEASURES it on the current keeper; it
   does not adopt it. The owner has not ruled; there is no promotion path
   from this lane without that ruling.
2. **San Miguel (6183) registration.** EIA-860 registered min load is
   genuinely 0.639 of capacity and the real plant runs below its own filed
   LSL — a registration-data question, not a mechanism defect; not "fixable"
   by lowering a measured value (rule 21). Owner leaning: document, no code
   change. (Noted: San Miguel is also the fleet's pin EXCEPTION — pin share
   2–7 %, model/declared ≈ 0.97–1.03 — consistent with its problem being
   registration, not availability.)
3. **Sandy Creek / `BIN_FORCED_DERATE_BY_YEAR` — RESOLVED 2026-07-28**
   (ERCOT-132 D2/D3, merged): `SC_COAL3 {2025: 0.0}` deleted (self-refuting;
   the measured overlay already carries the event), `N_COAL4 {2025: 0.67}`
   retained (Martin Lake unit 1 destroyed before the vintage starts never
   produces the transition the outage derive detects). Tests pin both.
   Consequence: ercot129 is no longer byte-reproducible from the committed
   tree (the ercot97→ercot98 precedent) — hence Phase 2's mandatory fresh
   BASE.

## 12. Scope, closed items honoured

No LP was built for this document; no year was solved; no `ScenarioConfig`
field, cache-key surface or solve path was touched; no keeper file was
touched; holdout years (2022 / 2019 / ≤2021 / H1-2026) untouched (rule 22).
Every CLOSED lane stays closed: coal offer LEVEL (ercot132 leg B), the
pooled `econ_high` 2.856 (ercot122 §5.2), coal ramp trajectory bounds
(ercot127 §1 / ercot132 leg A), the coal availability ENVELOPE layer
(ercot126 §§2–3), the min-config upper bound / cap-off (ercot130 §§3–4 —
reopen ONLY per its §7 item 5 reopening condition, which Phase 2 may finally
adjudicate), the plant-grain fractional min-load floor (ercot127 §3),
unit-grain commitment STATE (ercot128 §§1–2), the availability-SCALED
min-config floor (ercot128 §§P3–P4), age/temp coal derates (ercot121 §1a),
the EP-rebasis C3c lane (ercot119), `ercot_zonal_gas_basis` ablations, and
the West/Panhandle topology split. ERCOT-120 remains a separate
un-renumbered lane.
