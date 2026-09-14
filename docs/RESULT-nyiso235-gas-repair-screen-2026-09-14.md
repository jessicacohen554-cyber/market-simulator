# RESULT — nyiso-235: the rule-29 screen of the repaired NYISO delivered-gas series

**Session** nyiso-235 · **Date** 2026-09-14 · **Keeper under test** `2026-09-13-nyiso-232-st-gas`
(bundle `results/calibration/nyiso232_deleak_span`), **UNCHANGED by this session**.
**Pre-registration:** `docs/PRECOMMIT-nyiso234-gas-repair-screen-2026-09-14.md` +
`docs/PRECOMMIT-nyiso235-gas-repair-screen-ADDENDUM-2026-09-14.md`, both pushed before any solve.

> ## THE SCREEN CLEARS. G-1 · G-2 · G-3 · G-4 · G-5 all PASS.
> Rule 29 `[R-SCREEN]` (2): the full span is authorized and was spent as ONE shard, ONE
> `--years 2022 2023 2024 2025` invocation, ONE bundle.
>
> **A screen may kill an arm; it may never promote one. It did not promote this one.**
> Every criterion below is REPORTED, and none of them is a gate — in either direction.

---

## 1. WHAT WAS SOLVED, AND HOW IT DIFFERS FROM THE CONTROL

The arm is the keeper's frozen recipe replayed byte-faithfully (`scripts/replay_keeper.py`) with the
**nyiso-234b repaired delivered-gas series as the only difference**. No `ScenarioConfig` field was
set, no flag armed, no offer-curve multiplier touched, no DOF-ledger entry added.

The arm's `run_config.json` differs from the keeper's in exactly **two** fields, and **both are
accounted for as propagation, not as choices**:

| field | keeper → arm | what it is |
|---|---|---|
| `committed_band_measured_basis` | `None` → `False` | the PJM Route-A field **materializing at its default**. `None` (absent when the keeper solved) and `False` are the same posture: off. Its frozen cache-key drop value is `"False"`, so the keeper's key does not move. |
| `gas_offer_margin_anchor_by_zone` | +0.213359 in **all five zones** | **derived at solve time from the gas series itself.** Verified: the anchor delta **equals the signed annual-mean change in delivered gas to 1e-15** (8.443127 → 8.656486 $/MMBtu). Not a config change — the keeper's own code recomputing a derived quantity from repaired data. |

**Control = the keeper's committed bundle** (rule 29(b) form 4). No control solve was spent.

## 2. G-DRIFT — RE-RUN AT THIS SESSION'S HEAD, AND IT NEEDED TO BE

The parent PRECOMMIT §5 recorded "zero LIVE hunks", measured at nyiso-234's head. **This session's
head is a week later and the diff is not the same one**: `0ef1fac3 → dd33fc27` moves **37
solve-path files, +2,144 / −58 lines** (NWPP region onboarding, PJM Route-A, CAISO intake). The
verdict survives, but on measurement rather than on the diff being small. Full classification:
ADDENDUM §1. The three shared-code risks were checked empirically, not read:

* `ba_codes("NYISO") == ("NYIS",)` → `.isin` selects exactly the rows `==` did (NYISO's hydro fleet
  is the largest consumer of the four refactored `hydro.py` call sites);
* the new NERC admission predicate is `{"NWPP": "WECC"}` — a single key, NYISO absent;
* the new `_egrid_boundary_hr_repairs()` entry, plant **7350, is PGE/Oregon** — not among NYISO's
  1,088 plants.

Confirmed by the repo's own machinery: **`moved_rows("NYISO") = 0`**, and the keeper's recorded
`solve_surface.fingerprint = bd2b4657f9b5df7e` (210 rows) **reproduces byte-identically at HEAD**.
(ERCOT and CAISO *do* carry moved rows — `NUCLEAR_MONTHLY_CF_BY_YEAR`, `STATE_CARBON_PRICE_BY_ISO`.
Reported under rule 25 `[R-ISO-SCOPE]`; not this lane's to touch.)

## 3. THE GATES

| gate | result | evidence |
|---|---|---|
| **G-1 FOOTPRINT CONFINEMENT** | **PASS** (decided pre-solve) | The gate is written over *the delivered gas array in $/MMBtu*. That array moves 1,464 h across a contiguous 61-day run, **2022-11-01 … 2022-12-31 — and 0 hours outside it.** The repaired inputs touch exactly those two months: 10 daily dates (11-17/18/21/22, 12-22/23/27/28/29/30) and the two basis rows 2022-11 `0.7490→1.3122`, 2022-12 `3.5705→5.5376`. The 61-day span is wider than the Elliott days because the daily construction is **mean-preserving against the monthly anchor** — the reading was fixed in the ADDENDUM before any LP ran. |
| **G-2 DIRECTION** | **PASS** | Dec 22–23 load-weighted price **69.20 → 169.86 $/MWh (+100.67)**. |
| **G-3 ORDER OF MAGNITUDE** | **PASS** | +100.67 $/MWh against the band **pre-registered before the arm solved** (207.38 CC_REGULAR … 410.36 CT_PEAKER). Max single zone-hour rise **+193.17**, also inside. The LP is repricing, not amplifying. |
| **G-4 NO STRUCTURAL BREAK** | **PASS** | slack **0.000000**, dump **0.000000**, zero hours of either — exactly as the control. This was the gate most likely to fire (gas at $32–36/MMBtu could have pushed the LP into shedding load); it did not. |
| **G-5 IDENTITY** | **PASS on the review the gate's own text requires** | §4. |

**Rule 25 re-verified on the shared basis file:** of 940 rows, **30 moved and every one is NYISO**
(0 added, 0 removed, no other ISO's row touched).

## 4. G-5 — OIL +76.7 %, AND WHY THAT IS A PASS RATHER THAN A STOP

G-5's STOP condition is, verbatim, *"a plant class's annual energy moves by > 10 % **with no Δmc to
explain it**"*. Oil moved **0.632 → 1.117 TWh (+76.7 %)**, so the conditional half is owed. The
automated scorer deliberately reports this as `REVIEW — check it has a Δmc explanation` rather than
deciding it, because the Δmc half cannot be mechanized.

**It has one, and it is the canonical one:** the repaired gas crosses the measured dual-fuel
oil-parity price, so dual-fuel units switch to oil. Tested in a form that could have failed:

| test | result |
|---|---|
| Oil rise inside the touched months | **99.74 %** |
| Oil rise inside the **72 hours** where repaired delivered gas > $24.85/MMBtu oil parity | **99.71 %** — and the **control had 0 such hours** |
| Energy substitution | oil **+0.4848** TWh vs gas family **−0.4825** TWh — one-for-one to 0.5 % |
| Directional consistency | oil rises in **72 of 72** above-parity hours, falls in **0** |
| Oil move in touched months but *below* parity | **+0.0001 TWh** |

Had the oil risen outside the touched months, failed to track the parity crossing, or not conserved
energy against the gas classes, this would have been a STOP. It did none of those.

**This is not a new mechanism.** The keeper already carries `dual_fuel_oil_daily_parity` and
`dual_fuel_oil_reattribution` armed; the repair simply pushed delivered gas above parity for the
first time. The ADDENDUM §4 named this possibility **in advance**, before the arm solved.

**Corroboration, reported not relied on:** NYISO actually burned **1.844 TWh** of oil in 2022
(`classFull`). The control burned 0.632 (−1.212 vs actual); the arm burns 1.117 (−0.727). The
switch moves the model **toward** its measured value.

## 5. EVERY CRITERION, AT FULL MAGNITUDE — AND NONE OF THEM IS A GATE

The PRECOMMIT §4 pre-registered the expectation that **C3a would get WORSE**, and that a worse C3a
would not be grounds to revert. **It got better.** The symmetric discipline binds: *a better C3a is
not grounds to promote.* These numbers decided nothing here.

| criterion (2022) | control | arm | move |
|---|---:|---:|---|
| **C3a** RT load-weighted price vs actual $81.12 | 71.710 (**−11.60 %**) | 72.595 (**−10.51 %**) | +1.09 pp closer |
| **C3b** 12-month load-weighted NRMSE | **0.2175** | **0.1990** | −0.0185 (better) |
| **C1** CC_REGULAR vs actual 31.586 TWh | 37.080 (**+5.494**) | 36.764 (**+5.178**) | −0.316 TWh |
| **C1** gas family vs actual 59.520 TWh | 64.676 (+5.155) | 64.193 (**+4.673**) | −0.482 TWh |
| **C1** oil vs actual 1.844 TWh | 0.632 (−1.212) | 1.117 (**−0.727**) | +0.485 TWh |
| CT_PEAKER vs actual 2.687 | 2.572 (−0.115) | 2.449 (−0.238) | −0.123 TWh (**away**) |
| ST_GAS vs actual 7.699 | 7.309 (−0.390) | 7.326 (−0.372) | +0.017 TWh |

Method calibrated against the record: this basis reproduces the keeper's C3a-2022 of **−11.60 %**
and C3b of **0.2175** (log: 0.218) exactly.

**C8 / D-4 is unchanged and pre-existing.** Both bundles read `"passed": false`, and the failing set
is **identical** — the same 5 unit-conduct rows, same floors, same plants (2480, 8006 on
`reliability_floor × ST_GAS`; 52056, 54574, 8906 on `nyiso_gas_commitment_bridge`). **Zero arm-only
failures, zero control-only.** The screen shard's own summary line reported "legitimacy FAIL on D-4"
— that is the keeper's standing state, not a finding about the arm.

## 6. THE OPEN FINDING THIS SCREEN SURFACED — HANDED FORWARD, NOT ACTED ON

**A Nov–Dec data repair moves prices in all twelve months, and the channel is the annual-mean gas
offer anchor.**

`gas_offer_margin_anchor_by_zone` is anchored to the **annual mean** delivered gas (§1). Repairing
61 days therefore shifts the anchor by +0.2134 $/MMBtu, which shifts gas offers — and prices — in
every hour of the year, **including the ~7,300 hours where the delivered gas array itself did not
move at all**. Measured:

* Jan–Oct signed mean price delta **+0.21762 $/MWh**; **ratio to the anchor delta = 1.020**.
* Near-uniform month to month (+0.167 … +0.307), i.e. a level shift, not an event.
* **17.3 %** of Jan–Oct zone-hours are *exactly* unchanged — the hours where gas is not marginal,
  which is precisely what a gas-offer level shift predicts.
* By contrast the touched months carry the real action: Nov mean +2.84, Dec mean +5.01, Dec max
  **+193.17**, Dec min **−44.61**.

**This does not fail G-1**, which is written over the delivered gas array in $/MMBtu, and that array
is exactly confined. It is also **not introduced by this repair** — it is a standing property of the
keeper's anchor construction that the repair made visible.

It is recorded here as an **open structural question for the NYISO lane** — whether an offer anchor
with annual reach is the right construction when the underlying driver is seasonal — and this
session **deliberately did nothing about it**. Changing it to contain the footprint would be a
compensating tune of exactly the kind the pre-registration exists to forbid.

*(My scorer's inline note attributing out-of-window movement to "storage-SOC / hydro-budget
coupling" is superseded by this measurement and is wrong: storage throughput moves +1.4 % and hydro
+0.004 %, far too little to carry a +0.218 $/MWh mean shift.)*

## 7. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

| bundle | where | promotion cost from this state |
|---|---|---|
| screen, 2022 | commit **`750e4a72421e4548a5d82b71ccf13e6254cc3b87`**, branch `claude/nyiso-235-screen-2022` — **17 files incl. `dispatch/2022_P1.parquet` and root `system.parquet`** | zero re-solve; `git checkout 750e4a72421e4548a5d82b71ccf13e6254cc3b87 -- results/calibration/nyiso235_gasrepair_2022` |
| full span, 2022–2025 | *(filled in when the span shard lands)* | |

## 8. FLAG FOR THE OWNER — NEISO, AND IT IS WORSE THAN THE HANDOFF SAID

Rule 25 `[R-ISO-SCOPE]`: **NEISO's lane to measure and fix, not NYISO's.** Measured read-only here
only to make the flag concrete:

* `data/raw/gas-prices/algonquin_citygate_daily.csv` carries **the identical Elliott hole** — last
  print **2022-12-21 $6.51**, next **2023-01-04**, a 14-day gap straight through the storm.
* **And the series is not daily at all.** Its own `source` column reads `wednesday` /
  `last_wednesday`: it is a **weekly** series behind a `_daily.csv` filename, with **37 gaps longer
  than 7 days** across 2018–2025.

If NEISO's delivered-gas construction is mean-preserving against a monthly anchor the way NYISO's
is, both defects propagate the same way this session's did.

## 9. WHAT WAS NOT DONE

* **Object B (the gas-monotone tilt) has not been re-measured** since the repair. It should be, and
  the span bundle is what it should be measured on.
* No mechanism cell moves in `docs/codebase-site/data/mechanism-matrix/NYISO.js`: **no
  `ScenarioConfig` field was added or changed**, so there is no mechanism cell to update under rule
  28 `[R-MECH-MATRIX]` (b). The keeper/gates stamp is refreshed instead.
* `temp_dependent_derate` was **not** re-opened (rule 28(a), `G`, owner-confirmed 2026-09-14), and
  no `"."` neighbour was quietly substituted for it.
