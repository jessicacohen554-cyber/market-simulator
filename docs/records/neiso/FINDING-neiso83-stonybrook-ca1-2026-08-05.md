# FINDING — neiso-83: NEISO 6081 Stony Brook `CA1` was burning a fuel it does not have

**Session:** neiso-83 · **Date:** 2026-08-05 · **ISO:** NEISO (rule 25 `[R-ISO-SCOPE]`)
**Prereg:** `results/calibration/PREREG-neiso83-stonybrook-ca1-2026-08-05.md`, pushed
BEFORE either arm solved
**Keeper replayed:** `2026-08-04-neiso81-chpheatrate` · **New keeper:**
`2026-08-05-neiso-83-ca1-reclass` · **Control:** `2026-08-05-neiso-83-control-zerodelta`

## 0. Headline

**CONFIRMED misclassified. Fixed with zero fitted parameters. PROMOTED on the
pre-registered V3 branch — and the result is CORRECT AND NUMERICALLY SMALL, which is the
clean outcome, not a caveat (rule 1 `[R-STRUCT]`).**

| | |
|---|---|
| Verdict | **V3 — `K`, PROMOTE**, reached mechanically by `scripts/probes/_neiso83_ca1reclass_ab.py` against the pre-registered ladder |
| Construction properties | **P1–P6 all PASS** |
| Stop triggers | **N1–N4 none fired** |
| Determination | **CALIBRATED-WITH-CAVEATS in BOTH arms**, criterion for criterion identical to the superseded keeper — 0 FAILs, 1 ledgered C3c caveat, C1 all 12/12 · free 8/8 |
| Largest class move | **CC_REGULAR +0.0108 TWh in 2025 = 0.018 % of the class** |
| Years | 2023 2024 2025, ONE invocation per arm (rule 16 `[R-ALLYEARS]`) |
| Runs registered | **both** (rule 15 `[R-DASHBOARD]`), control and arm alike |

**The control came back BYTE-IDENTICAL to the committed keeper** — max |class-hour delta|
**0.000000 MW in all three years** — so unlike neiso-81 there is no same-HEAD drift to
decompose and **every arm-B number is the mechanism**.

---

## 1. Q1 — is `CA1` actually misclassified in the LP? **YES — and two pieces of the inherited framing are WRONG**

Read from the fleet built at the **keeper's own** `ScenarioConfig`, never the loader
defaults (the miso-116 trap):

| unit | fuel | plant_group | pmax MW | heat rate | VOM | CO2 t/MWh | EFORd |
|---|---|---|---|---|---|---|---|
| `6081_CA1` | **oil** | *(none)* | **96.0** | 10.60617891 | 4.50 | 1.00 | 0.10 |
| `6081_CT1/2/3` | gas_cc | CC_REGULAR | 69.7 ea | 10.60617891 | 2.00 | 0.43 | 0.05 |
| `6081_1`, `6081_2` | oil | *(none)* | 65.0 ea | 10.60617891 | 4.50 | 1.00 | 0.10 |
| `6081_EDSI` | oil | *(none)* | 0.6 | 10.60617891 | 4.50 | 1.00 | 0.10 |

**Corrections to the inherited description, stated so they are not repeated:**

1. **The empty `plant_group` is NOT an anomaly.** Every oil unit in NEISO carries one —
   **135 units / 5,181.5 MW, all empty** — because the EIA-860 loader assigns a group only
   to coal and gas. Nothing was ever inferable from it.
2. **The 96.0 vs 105.0 MW "mismatch" is a basis difference, not a discrepancy.** 96.0 is
   EIA-860 **net summer**, 105.0 is nameplate, and the fleet's `pmax` rule is
   net-summer-else-nameplate.

What **is** real: a 96.0 MW steam turbine priced off the distillate curve at $4.50 VOM and
1.0 t-CO2/MWh, disjoint in class, fuel, VOM, emission rate and forced-outage rate from the
three combustion turbines it shares a shaft-block — and a heat rate — with.

**Why `cc_steam_part_capacity` could never have reached it: population, not gating.** The
national predicate is exactly **four** rows and splits two-and-two:

| plant | gen | ES1 | `_map_fuel_type` | population |
|---|---|---|---|---|
| 55088 Dearborn (MI) | ST1 | BFG | `None` | **DROPPED** → the repair |
| 54912 Martinez (CA) | STG1 | OG | `None` | **DROPPED** → the repair |
| 1004 Edwardsport (IN) | ST | SGC | `coal` | **CARRIED** → re-class |
| 6081 Stony Brook (MA) | CA1 | DFO | `oil` | **CARRIED** → re-class |

The repair only ever RESTORES a dropped row, so a carried row is outside its population
entirely — which is precisely what neiso-80 measured as a byte-identical armed fleet. Its
`fuel_type is None` gate is load-bearing (miso-125 §6: it is what keeps Edwardsport's real
555 MW IGCC machine in `COAL`), so re-classing got its **own** flag and its **own** ISO
registry rather than widening the repair's. **`cc_steam_part_capacity` was NOT re-armed and
its `I` was NOT re-stamped** (rule 28a).

## 2. Q2 — the physically correct representation

**Chosen: (a) fold `CA1` into its own block** — re-class to `gas_cc` / `CC_REGULAR` at the
incumbent eGRID plant heat rate. Capacity unchanged (24,209.58 MW both arms); class, fuel,
VOM, CO2 rate, NOx rate and EFORd move; **`pmax` and `heat_rate` do not**.

**The LP must not burn distillate in it.** Plant 6081 meters **five** CEMS units in every
train year — 001/002/003 "Combined cycle" on Pipeline Natural Gas, 004/005 "Combustion
turbine" on Diesel Oil — and **no unit for `CA1` in any year**. That is physically correct,
not a data gap: a HRSG steam turbine has no stack because it has no combustion path. Every
MMBtu the block burns is already metered at the combustion turbines.

**It is not double-counting the block's fuel.** The incumbent heat rate is the eGRID
**plant-average**, whose `PLNGENAN` denominator already counts the steam part's own
generation — it is a **block** rate. A per-MWh block rate applied uniformly to every block
MW reproduces the block's total fuel burn *by construction*. What the model did before is
the inconsistent case: it charged that block-denominated rate to 209.1 MW of a 305.1 MW
block and priced the missing 96 MW off the distillate curve.

**(b) "carry `CA1` as a zero-fuel-cost unit" was rejected on physics, not fit.** It is
self-consistent only if the CT siblings simultaneously move to a **CT-denominated** rate
(metered ≈ 12.6 MMBtu/MWh gross); left on the block rate they already carry it would charge
`10.606 × CT-MWh` instead of `10.606 × block-MWh` and **under**-count the block's fuel. It
is also two changes, not one, and would make `CA1` the only CC steam part in the model
priced differently from every other — every `NG`-coded `CA` row in all six ISOs is already
`gas_cc` at its plant's rate.

## 3. Q3 — the measured identification, and there is no parameter in it

**Zero fitted parameters.** The capacity is EIA-860's published net-summer figure; the heat
rate is the incumbent one; the flag selects a class and every downstream attribute follows
from existing per-fuel constants. Nothing below enters the LP — it establishes that the
machine is **real and live**.

**The decisive test — fuel inheritance.** If the steam part had a fuel of its own, its
EIA-923 fuel split would be independent of its siblings'. It is not:

| year | CA DFO share | CT DFO share | \|gap\| |
|---|---|---|---|
| 2018 | 0.4556 | 0.4684 | 0.0128 |
| 2019 | 0.0043 | 0.0206 | 0.0163 |
| 2020 | 0.0096 | 0.0080 | 0.0016 |
| 2021 | 0.0289 | 0.0319 | 0.0030 |
| 2022 | 0.3655 | 0.3872 | 0.0217 |

The `CA` row tracks whatever the block burned, across a **0.004 → 0.468** swing in the
block's own oil share. **EIA-860's `DFO` on that row is a duct / legacy label, not a
primary energy input.**

**Direct steam share (2018–2022):** 0.2753 / 0.2886 / 0.2853 / 0.2911 / 0.2841 — **mean
0.2849, sd 0.0060**, a textbook 3×1 fraction and consistent with `CA1`'s 96.0 / 305.1 =
0.315 capacity share.

**The 2023–2025 zeros are a reporting-convention change, and that is a PROOF, not an
inference.** The `CA` rows fall to 2,165 / 0 / 0 MWh while the `CT` rows' EIA-923 **net**
generation *exceeds* the CAMPD `CT` **gross** — 1.343 (2024) and 1.338 (2025). Net above
gross is impossible for a CT-only row. **The two routes agree:** applying the 0.2849 direct
share to those ratios implies a CT net/gross of **0.9601 / 0.9572**, an ordinary
auxiliary-load figure. Two independent instruments, one number.

## 4. Q4 — does it change anything? **Yes, correctly, and by very little**

Per-class energy, arm B minus the same-HEAD control (TWh):

| year | oil | CC_REGULAR | CT_PEAKER | total gen frac |
|---|---|---|---|---|
| 2023 | **−0.00231** | +0.00220 | +0.00068 | +9.4e-7 |
| 2024 | **−0.00034** | +0.00062 | −0.00131 | −1.0e-5 |
| 2025 | **−0.00139** | **+0.01078** | −0.01105 | −2.3e-5 |

Load-weighted λ: **+0.0005 / −0.0192 / −0.0701 $/MWh** (+0.001 % / −0.04 % / −0.10 % of
level). C3c tail: **0 hours > $300 in both arms, all three years — bit-unchanged.** Summed
per-class C1 |error| delta: **+0.0044 / −0.0004 / −0.0010 TWh** — marginally worse in 2023,
marginally better in 2024 and 2025, all of it two orders of magnitude inside the
±1.955–2.103 TWh C1 band.

**Why the realized effect is ~1/100th of the available headroom — measured, not asserted.**
6081's heat rate of **10.6062 MMBtu/MWh sits above 97.5 % of NEISO's CC_REGULAR capacity**
(cap-weighted p50 7.340, p90 8.616; only 312.1 MW of the class is dearer). The re-classed
96 MW is deep out of merit and clears only in the tightest hours — which is also why 2025's
CC_REGULAR gain is absorbed almost exactly by CT_PEAKER (+0.0108 against −0.0111).

**2023 could not move through this plant at all, and did not.** The block is derated to
zero in all 8,760 hours in BOTH arms, so 2023's CC_REGULAR change is system re-dispatch
displacing the 96 MW that left `oil` — pre-registered, and borne out.

---

## 5. Disclosed against interest

**(a) The charter's own magnitude expectation was corrected BEFORE the solve, not after.**
The lane was chartered expecting "< 0.15 % of CC_REGULAR". Phase 0 measured the block's
effective available capacity moving **0.0 → 0.0 / 61.7 → 156.4 / 40.5 → 134.2 MW** — more
HEADROOM than that implies — and the prereg said so in advance so this finding could not be
read as retrofitting the expectation. The realized **dispatch** effect then landed an order
of magnitude **under** the charter's bound, for the merit-order reason in §4. Both halves
are on the record.

**(b) The outage-denominator leg is part of this mechanism and DOMINATES the headroom.**
The CAMPD unit-outage overlay derates `(plant_code, plant_group)` by
`removed_mw / plant_capacity_mw` and reads that denominator off the same fleet, so it moves
with the flag (209.1 → 305.1 MW at 6081). It is **not a second mechanism** — it is the same
mechanism's own input, and leaving it un-forwarded would remove the wrong ABSOLUTE MW: a
152 MW 2024 outage against the un-armed denominator removes 72.7 % of an armed 305.1 MW bin
= **221.8 MW, 46 % more than went out**. Decomposed: capacity leg **+0.0 / +28.3 / +18.6
MW** against denominator leg **+0.0 / +66.4 / +75.2 MW**.

**Rule 23 `[R-FROZEN-DERIVE]` is NOT engaged.** The outage deriver's own inputs at 6081
(`group_by_code`, `groups_by_code`, `steam_np_by_code`) are **identical** under both arms,
so the committed extract would re-derive byte-for-byte. Nothing was regenerated.

**(c) NEW OPEN ROOT-CAUSE ISSUE — named, sized, and deliberately NOT fixed (rules 19 / 21 /
25).** `campd-unit-outages-NEISO.csv` carries plant 6081's **DIESEL peakers** — CAMPD units
004/005 = EIA-860 generators `1` and `2` — with `plant_group = CC_REGULAR`. They land there
because `oil` carries no `plant_group` at all, so the outage overlay **cannot represent an
oil unit's outage** and the deriver routes it to the plant's only modelled group. In 2024
and 2025 those two units are the **only** source of 6081 outage rows while the CC block's
own units 001/002/003 have **none** — so the model derates a fully-available CC block to
**29.5 % / 19.4 %**. Pre-existing, ISO-agnostic, and a fleet-taxonomy change with six-ISO
blast radius. The armed denominator moves the block **toward** physical truth (~100 %
available), not away from it, which is why rule 14 `[R-ACCURATE]` says take the consistent
basis and open the root cause rather than bury it in an inconsistent one.

**(d) The benchmark side is NOT symmetrically corrected, and the residue is measured.** The
EIA-923 benchmark buckets Page-1 rows through the same `classify_plant` registry, but at
**national** scope with no ISO gate — so re-classing there would reach MISO's Edwardsport
(rule 25). The un-corrected residue is the 6081 `CA`/`DFO` row: **2,165 MWh in 2023 and
ZERO in 2024 and 2025** — 0.0022 TWh against a ±1.955 TWh C1 band, **0.11 % of it**.
`cc_steam_part_capacity`'s own MISO keeper does not touch the benchmark side either.

**(e) Firing was proven at the ENERGY grain, not the loader grain.** The miso-126 wiring
gap: a byte-identical arm would have scored **INVALID** (the flag never reached the LP), not
"inert". P4's bar was |Δ oil energy| > 0.001 TWh in at least one year; 2023 (−0.00231) and
2025 (−0.00139) clear it.

**(f) 2025 EIA-923 re-checked and still NOT landed.** `audit_eia923_completeness.py --year
2025 --no-write` reproduces NEISO's committed block **byte-identically** — CC_CHP and
CC_REGULAR `incomplete`, every class `gate: false`. The 2025 C1 CC rows stay SKIPPED and
**nothing was estimated around it**. The committed file was not rewritten, so the
cross-lane MISO/SPP perturbation neiso-82 flagged never arose.

---

## 6. Governance

| item | status |
|---|---|
| **Rule 1 `[R-STRUCT]`** | Promoted on structure. A correct-and-inert result is a clean PASS; the size of the residual move is reported, never required. |
| **Rule 13 `[R-MEASURED]`** | Prime mover, unit code, vintage and net-summer capacity are published EIA-860 INPUTS that regenerate for any forward year. No residual consulted, in either direction. |
| **Rule 15 `[R-DASHBOARD]`** | **Both** runs registered in-session — `2026-08-05-neiso-83-control-zerodelta` and `2026-08-05-neiso-83-ca1-reclass`. |
| **Rule 16 `[R-ALLYEARS]`** | 2023 + 2024 + 2025, one bundle per arm, one invocation each. |
| **Rule 19 `[R-ONE-MECH]`** | One mechanism. The outage denominator is its own input; the deriver's oil-peaker routing is filed as an open root cause, not stacked on. |
| **Rule 20 `[R-DOF]`** | DOF ledger **13 → 14** entries, `n_residual` **UNCHANGED at 5**. Zero free parameters added. |
| **Rule 22 `[R-HOLDOUT]`** | `--year` strictly {2023, 2024, 2025}. No holdout of either tier solved, scored or touched; the spend freeze was never approached. EIA-923 2018–2022 was read as **source data for a physical-share measurement**, which is not a solve, a score or a registration. `calibration-complete.json` re-keyed **with** a determination re-verification (D-5(b)); the result is NOT worse, so no owner escalation. `locked_test_scored_on` deliberately NOT re-keyed. |
| **Rule 23 `[R-FROZEN-DERIVE]`** | Not engaged, proven rather than assumed. |
| **Rule 24 `[R-REGISTRY]`** | The arming is a `ScenarioConfig` field visible in `run_config.json`. No env var, no hardcoded per-plant dict. |
| **Rule 25 `[R-ISO-SCOPE]`** | NEISO-only, gated on `CC_STEAM_PART_RECLASS_ISOS`. Proven by RUNNING the armed loader per ISO: ERCOT (1,450), CAISO (782), PJM (1,922), MISO (1,975), NYISO (460) fleets **byte-identical**; Edwardsport stays `COAL`. |
| **Rule 27 `[R-PUSH]`** | Opus. Every push touching a file ≥ 300 lines blob-verified immediately after. |
| **Rule 28 `[R-MECH-MATRIX]`** | New field's row landed in the same PR as the field (28c); cell stamped `U` → `K` in this session (28b); `cc_steam_part_capacity` `I` untouched, no closed lever re-opened (28a). NEISO keeper header re-stamped and the stale `2026-08-03-neiso-caiso156-meter-screen` drift repaired in the same edit. |

## 7. Files

| file | change |
|---|---|
| `src/market_sim/config/plant_taxonomy.py` | `CC_STEAM_PART_RECLASS_ISOS = {NEISO}` |
| `src/market_sim/config/scenarios.py` | `cc_steam_part_reclass: bool = False` + hash-exempt + default map |
| `src/market_sim/data/fleet/eia860.py` | the re-class branch in the row loop; flag threaded through all four loader entry points |
| `src/market_sim/data/fleet/assembly.py`, `scripts/run_calibration.py` | flag forwarded at every `load_fleet_from_csv` call site |
| `src/market_sim/data/outages.py`, `src/market_sim/data/fleet/arrays.py` | the derate denominator follows the same fleet |
| `tests/unit/data/test_cc_steam_part_reclass.py` | 18 tests: fuel-map premise, row loop, ISO scope, the real NEISO fleet, cross-ISO invariance |
| `scripts/probes/_neiso83_stonybrook_ca1_phase0.py` + `.json` | Phase-0 evidence (no LP) |
| `scripts/probes/_neiso83_ca1reclass_ab.py` + `.json` | the A/B scorer and its record |
| `scripts/gen_neiso83_attestation.py` | both arms' attestations + DOF ledger |
| `results/calibration/neiso83_control_A/`, `neiso83_ca1reclass_B/` | the two bundles (slim + `hourly/` sidecars) |
| `frontend/data/backcast/keepers/NEISO.json`, `status/NEISO.js`, `calibration-complete.json` | the promotion |
| `docs/codebase-site/data/mechanism-matrix.js`, `docs/mechanism-testing-matrix.md` | the new row, the `K` stamp, the §5.6 block, the keeper header |

`manifest.js` / `benchmark.js` untouched — the Pages deploy is their single writer.
