# FINDING — nyiso-108: the NYISO hydro input repair is armed and PROMOTED, and it exposed a real 2023 over-pricing that phantom hydro was masking

**Session:** nyiso-108. **Frozen HEAD:** `e1a4bc6` (solve path byte-identical to the
pre-rebase HEAD `69cd53d`; the 6 intervening main commits touched only CAISO
artifacts and forecast docs). **Outgoing keeper:** `2026-07-31-nyiso105-chp-heat-rates`.
**NEW KEEPER:** `2026-07-31-nyiso108-hydro-input-repair`
(bundle `results/calibration/nyiso108_hydrorepair_B`).
**Pre-registration:** `results/calibration/PREREG-nyiso108-hydro-input-repair-2026-07-31.md`,
committed **and pushed** (PR #3235) before either arm solved.
**Solves: 2** — one same-HEAD zero-delta control, one single-delta arm, three years each.

---

## §0 — Headline

Scope Item A is executed. NYISO was the **only material-hydro ISO whose keeper ran
on an unrepaired truncated EIA-923 vintage**; it no longer is. The repair is a
rule 14 `[R-ACCURATE]` input correction with **zero free parameters**, and it
does what nyiso-107 predicted to four decimals.

It also did something nyiso-107 could not predict: **removing ~1.55 TWh of
phantom zero-MC 2023 hydro exposed a pre-existing NYISO 2023 fossil
over-pricing**, which crosses C3a's ±10 % band at **+10.2 %** (control +8.6 %).
NYISO's determination therefore regresses **CALIBRATED-WITH-CAVEATS → NOT-YET**.

**Promotion is an EXPLICIT OWNER OVERRIDE of this session's own prereg §6**,
which pre-committed that a new FAIL means no promotion. The owner's standing
instruction — *"If structural integrity improves but gates regress that may still
be a keeper"* — was given with the numbers in hand. It is recorded as an
override, not as the pre-registration's verdict, so the record stays honest.

---

## §1 — Every pre-registered construction gate PASSES

| gate | result |
|---|---|
| **K1** flag fidelity | **PASS** — arm `hydro_backfill_year=2024` / `hydro_eia930_monthly=true`; control `None` / `false` |
| **K2** control integrity | **PASS on the STRICT BYTE basis** — control − committed keeper = **exactly 0.0 MW** on every class in all three years |
| **K3** liveness | **PASS** — hydro moves **−1.5505 / −1.0904 / +3.0107 TWh**, live in every year on both the MW and TWh bases |
| **K4** single delta | **PASS** — the recorded configs differ in exactly the two hydro keys |
| **K5** year span | **PASS** — both bundles `[2023, 2024, 2025]`; the holdout spend freeze is ACTIVE and untouched |
| **K6** pin sensitivity | reported — free classes move (CC_REGULAR, ST_GAS, CT_PEAKER, oil), so the verdict does not rest on D-10 pinned classes |

**K2 on the byte basis is the load-bearing one.** Unlike caiso-146 and neiso-69,
NYISO shows **no same-HEAD drift at all**, so the A/B is unconfounded and every
delta below is the mechanism, not the base.

---

## §2 — The construction choice, adjudicated BEFORE the solve

Option (i), backfill + EIA-930 level pin (the CAISO/NEISO posture), on three
independent grounds — all measured pre-solve
(`scripts/probes/_nyiso108_hydro_construction_audit.py`).

**Level.** Adjudicated against NYISO MIS **P-63 Real-Time Fuel Mix**, the one
series that is **neither the model input nor the scorer benchmark**:

| construction | 2023 | 2024 | 2025 |
|---|---|---|---|
| bare (outgoing keeper) | +4.48 % | +3.33 % | **−13.20 %** |
| backfill-only (PJM/MISO posture) | +4.49 % | +3.33 % | **+7.20 %** |
| **pinned (chosen)** | **−1.29 %** | **−0.88 %** | **−0.78 %** |

**Shape — this is what killed backfill-only, independently of level.** Against
P-63, carrying the prior year's water forward *degrades* the 2025 seasonal shape
**below the unrepaired keeper** and puts the annual peak in the wrong month:

| construction | 2023 r | 2024 r | **2025 r** | 2025 peak month (P-63 = **5**) |
|---|---|---|---|---|
| bare | 0.9931 | 0.9938 | 0.9251 | 5 |
| backfill-only | 0.9930 | 0.9938 | **0.8265** | **3 — wrong** |
| **pinned** | 0.9882 | 0.9915 | **0.9943** | 5 |

The PJM/MISO refusal of the pin **does not transfer**: it exists for a
pumped-storage fold NYISO does not have (`NG: WAT`/923-`HY` = 0.9448 / 0.9606,
*below* 923 HY; NYIS PS netgen net **negative**, so pumping is netted **in**, not
folded in gross — re-confirmed independently at nyiso-107 and asserted at probe
runtime).

**Physical attainability.** Plant-months whose budget exceeds the plant's own
`nameplate × hours` — energy the LP cannot deliver and must silently clip — fall
**34 / 34 / 33 → 14 / 20 / 10**.

Option (iii) (put input *and* benchmark on one basis) requires changing the
**benchmark** side — the cross-ISO scope the owner DEFERRED at nyiso-107 (matrix
§5.5 item 11b). Adjudicated as out of lane, not forgotten.

---

## §3 — What the solve did

**Fleet.** 2025 LP hydro **3 plants / 21.0482 TWh → 147 plants / 24.0589 TWh**.

**Dispatch, and the 1:1 fossil displacement** (energy balance, as physics
requires — hydro is zero-MC and energy-limited):

| year | hydro Δ | fossil Δ | largest movers |
|---|---|---|---|
| 2023 | −1.5505 | **+1.5669** | CC_REGULAR +0.886, CC_CHP +0.406, ST_GAS +0.231 |
| 2024 | −1.0904 | **+1.1086** | CC_REGULAR +0.586, CC_CHP +0.375, ST_GAS +0.109 |
| 2025 | +3.0107 | **−3.2302** | CC_REGULAR −1.346, ST_GAS −0.946, CC_CHP −0.577, CT_PEAKER −0.188 |

**Prices.** Mean λ +0.518 / +0.373 / **−2.118** $/MWh — up where hydro was
removed, down where it was restored. Slack and dump are **0.0 in both arms, all
years**: no unserved energy, no curtailment gaming.

**What does NOT move.** C1 stays **14/14 all-class, 10/10 free-class** in *both*
arms. C2 / C3b / C4 / C6 / C7 / C8 all PASS in both. **C3c is BIT-IDENTICAL** —
model 3 / 0 / 7 h vs actual 10 / 12 / 42 h above $300 in both arms.

---

## §4 — The regression: a DISCOVERED defect, not a created one

**C3a mean LMP 2023: +8.6 % (control) → +10.2 % (arm)**, against a ±10.0 % band
(`PRICE_MEAN_TOL`). A **0.2 pp** breach. 2024 improves (−1.4 → −0.4 % vs DA);
2025 moves further under.

This is exactly the pattern rule 14 `[R-ACCURATE]` names in its own text — *"if
swapping a hand estimate for real data makes the backcast worse, that is a signal
that something else in the model is miscalibrated and the estimate was silently
compensating for it."* The evidence that it is compensation, not causation:

* EIA-923 raw 2023 (**28.0312 TWh**) sits **+3.11 % ABOVE** NYISO's own P-63
  telemetry (27.1845); the armed level sits **−1.29 % below** it. Both
  market-boundary instruments (P-63, EIA-930) agree with each other within
  1.3 %; the plant-boundary 923 is the outlier.
* So the outgoing keeper was carrying **~1.55 TWh of phantom zero-MC 2023
  hydro**, and zero-MC energy suppresses the clearing price by construction.
* Removing it does not create a 2023 over-pricing — it **stops hiding one**.

**Reverting the measured input to restore the PASS is precisely what rule 14
forbids.** The input stays; the root cause becomes the named successor.

**Cross-ISO precedent, same mechanism family, same signature:** PJM at pjm-143 —
*"C3a 2023 now +2.99 % (was +2.05: the phantom energy was suppressing a real
over-pricing)"* — and PJM was likewise promoted on rule-1 structural fidelity.
NYISO's differs only in that its 2023 baseline already sat near the band edge, so
the same physics crosses a threshold instead of staying inside one.

### §4.1 A residual that is EXPLAINED and deliberately NOT corrected

The pinned level sits a consistent **−1.29 / −0.88 / −0.78 %** below P-63. NYIS
files no `NG: PS` column and its EIA-923 PS netgen is net **negative**
(−0.372 / −0.410 / −0.490 TWh), so pumping load is **netted into** `NG: WAT`.
Predicted understatement from that netting: **−1.33 / −1.49 / −2.38 %** —
matching the 2023 residual to **0.05 pt**. Disclosed, **not corrected**: a
reconciliation factor here would be a fitted adjustment (rules 5 `[R-NO-MAGIC]` /
21 `[R-REGISTRY]`). It does **not** re-open the PS-fold question, whose
MISO/PJM refusal is for gross discharge *added* — the opposite sign.

---

## §5 — The frontier: the C3c declaration STANDS; its PREMISE does not

The nyiso-104b frontier is scoped to the **C3c scarcity-tail lever queue**, and
this session moved **no C3c evidence whatsoever** — the tail is bit-identical
across arm and control. The exhausted-queue finding, its re-open condition
(Capital_Hudson → Zone-F/Zone-G topology split, owner charter required), and the
C3c ledger entry all carry forward **unchanged**, and **no new caveat slot is
spent**.

What lapses is the **premise** the declaration rested on. nyiso-104b granted
CALIBRATED-WITH-CAVEATS because *"C3c was the SOLE blocker and every other
criterion already PASSED."* That is no longer true: NYISO now has a **second,
non-C3c, tractable** blocker with a named successor lane. **NYISO is no longer at
a frontier in the sense of "options exhausted" — it is back in active calibration
with a concrete open item.** The keeper shard's `frontier` block records this
amendment verbatim.

Holdout unaffected: NYISO keeps `complete` (validation tier), stays **absent**
from `final`, and the ACTIVE spend freeze independently blocks every
out-of-training solve.

---

## §6 — DOF ledger

**+1 entry, +0 residual-identified** (25 → 26 entries, 6 → 6 residual). Both
switches are pre-existing registered measured-data flags **already armed on four
of the six keepers**; the level is read from EIA-930 and the backfill year is the
prior complete EIA-923 vintage. Nothing is chosen; nothing is fitted.

Rule 13 `[R-MEASURED]`: a monthly inflow budget is a physical availability limit
(the outage-window family) with a **named forward analogue already in the code** —
`forecast_monthly_hydro`'s climatology scaled by the `hydro_year` wet/dry lever —
and `build_hydro_fleet` rejects `eia930_monthly` and `forecast_budget` together.
It is already a declared `backcast_only` MechanismSpec (`hydro_eia930_monthly`,
L6) in `legitimacy_diagnostics.py`.

**The hydro VOLUME statistic is declared plumbing and is never banked.** Pinning
to the same EIA-930 series the 2025 benchmark uses drives 2025 hydro to −0.19 %
by construction. That is not a new concession: `calibration_verdict.py` already
lists hydro as a D-10 pinned class (*"L6 hydro (monthly budgets)"*) and C1 scores
only the gas/coal families, so **hydro volume is not a gated C1 row at all**. The
scored movement is fossil displacement, which is free.

---

## §7 — Named successor and what is NOT claimed

**nyiso-109: the NYISO 2023 fossil over-pricing, now visible at +10.2 %.** An
offer-stack / fuel-basis root cause — **not** the hydro input, which is now
correct and must not be re-tuned to bury the miss.

Not claimed: no C3c improvement (bit-identical), no skill claim on the hydro
volume number (plumbing), no forecast-lane result, no out-of-training year
touched. Two measurement bugs in this session's own *reported* (non-gating)
diagnostics are recorded rather than quietly dropped: the A/B scorer's
`hydro_lp_units` counts rows rather than distinct units, and its `_tail_hours`
returns 0 for the control whose committed C3c is 3/0/7 h, so it does not
reproduce the scorer's tail basis — the authoritative C3c above comes from
`calibration_verdict.py`, not from that helper.

**Environment note for successors:** a fresh container needs `uv sync`,
`curate_capacity_deliverability.py`, **and a full `scripts/regenerate_clean.py`**
(48 datatypes, ~35 min) — the two commands in the standing prompt are not
sufficient; `fleet`, `reference`, `emissions`, `outages`, `renewables`,
`fuel-prices` and the NYISO-specific tables are all required by the solve.

**Test baseline measured at this HEAD** (`tests/{curation,scoring,unit}`, after a
full `regenerate_clean`): **13 failed / 4346 passed / 14 skipped** in 14m29s. This
session changed **no `src/` code** — only `scripts/probes/`,
`scripts/gen_nyiso108_attestation.py`, docs, `frontend/data/backcast/` and
`results/calibration/` — so none of the 13 are attributable to it. Composition:
`test_measured_chp_heat_rates.py` 7 (the standing deriver cluster),
`test_consume_lmp.py` 1 (NEW at this HEAD), `test_ff_readiness_battery.py` 1,
`test_outages.py` 1, and three cache-key byte-stability tests
(`test_cc_committed_offer_margin.py`, `test_ramp_envelope_basis.py`,
`test_forecast_xyear_warmstart_flag.py`). This is **down from the 20** quoted into
nyiso-108: the `test_export.py` cluster (4) and four of the five
`ff_readiness_battery` failures were fixed on main during this session. Re-measure
rather than inherit — the set moves several PRs per session.
