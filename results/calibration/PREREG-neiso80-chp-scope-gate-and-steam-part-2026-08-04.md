# PREREG — neiso-80: the miso-122 dark-fuel scope gate at NEISO, and the Stony Brook `CA` presence question

**Session:** neiso-80 · **ISO:** NEISO · **Date:** 2026-08-04
**Branch:** `claude/neiso-backcast-calibration-nx93bt`
**Designated keeper (unchanged unless a promotion is earned):**
`2026-08-03-neiso-caiso156-meter-screen`
**Holdout (rule 22 `[R-HOLDOUT]`):** training years **2023 / 2024 / 2025 only**,
one bundle (rule 16 `[R-ALLYEARS]`). NEISO's locked test is **SPENT and never
re-grantable**; nothing out-of-training is touched, and the active holdout spend
freeze is not consulted for permission because nothing here asks for any.

**This document is pushed BEFORE any arm is built and before any adjudicating
statistic is computed.** Everything below the line "measured before this
document was written" is a *construction* fact read out of committed artifacts
(what the keeper arms, what the derive script contains, what columns an on-disk
CSV has). No magnitude, no share, no presence verdict and no A/B number has been
computed at the time of writing.

---

## 0. Two items, in order, and the stop rule between them

The cross-ISO queue hands NEISO two named, un-adjudicated items. They are
independent and are pre-registered together because item 1 has a **pre-declared
route to inertness** (§1.2) and the session prompt authorises item 2 as its
successor in the same lane.

* **Item 1 — the miso-122 hybrid-cogen dark-fuel scope gate, unapplied at
  NEISO.** `data/raw/_processed-legacy/chp_power_only_heat_rates_NEISO.csv`
  carries **19 columns** and no `dark_fuel_share` at all; MISO's and NYISO's
  carry 22. Plant **1595 Kendall Green Energy, 206.0 MW `CC_CHP`** is the one
  NEISO plant the gate reaches.
* **Item 2 — NEISO 6081 Stony Brook `CA1`, 96.0 MW `DFO`.** The
  `cc_steam_part_capacity` repair promoted to MISO keeper at miso-126; NEISO's
  cell is `U` and the plant's presence is `UNDETERMINED` even on miso-126's own
  basis-consistent test.

**Stop rule between them:** item 2's Phase 0 (presence, §2) runs regardless —
it is a no-LP measurement on committed EIA-860 and fleet artifacts. **An LP arm
is built for at most ONE of the two items**, and only if that item's properties
all hold and its magnitude survives §3.

**CAISO 54912 Martinez `STG1` is not this session's.** It is handed off to the
CAISO lane and **no CAISO cell is stamped here** (rule 25 `[R-ISO-SCOPE]`).

---

## 1. Item 1 — the dark-fuel scope gate at NEISO

### 1.1 The defect, at grain

`scripts/data/derive_chp_power_only_heat_rates.py` **already implements** scope
gate 3 (miso-122, 2026-08-03) and its own module docstring already names the
NEISO number:

> Measured 2023 across the five artifact ISOs: MISO 55088 Dearborn 16.6 %
> (515 MW), NYISO 2493 East River 37.5 % (306 MW, `below_credited`), **NEISO
> 1595 Kendall 1.2 % (206 MW)**; PJM and CAISO carry none above 0.1 %.

miso-122 re-derived **only MISO's** artifact and handed NEISO's off with a
number (rule 25). nyiso-120 re-derived **only NYISO's** and re-stated the same
hand-off verbatim. NEISO's artifact was therefore last written **before gate 3
existed** — `git log` puts it at PR #3410, the same commit as PJM's and CAISO's,
and its `source` string carries neither the `* (1 - dark_fuel_share)` term nor
gate 3's `below_credited` exclusion clause.

**The re-derive is a rule 23 `[R-FROZEN-DERIVE]` re-derivation on the permitted
ground and on no other:** *"it re-derives ONLY when EPA publishes a new eGRID
vintage OR when a **scope gate's logic** changes on measured grounds, and the
re-derivation commit must cite that change — never a residual."* The commit
cites the miso-122 gate-3 addition. **No residual is consulted, in either
direction.**

### 1.2 The load-bearing assumptions, as numbered properties with falsifiers

*Per miso-125 §7 item 4 and miso-126 §2.1: each property carries its own
falsifier, and **if a falsifier fires the arm stops there**, whatever the
magnitudes say.*

**P1 — CONSUMPTION.** An artifact change can only reach the LP through a flag
that reads it. `data/fleet/eia860.py:1686` applies the artifact **only** under
`measured_chp_heat_rates`; `campd_bins.measured_chp_heat_rates(iso)` is its sole
loader and has no other caller in `src/`.

*Measured before this document was written:* the designated keeper bundle
`results/calibration/neiso_c156_meter_screen_B/run_config.json` records
`measured_chp_heat_rates = **false**`.

*Pre-declared consequence:* **the item-1 artifact re-derive is score-inert on
the designated NEISO keeper by construction, not by measurement.** No solve can
show otherwise and none is owed to establish it.

*Falsifier (which would re-open an LP arm):* a second, ungated consumer of
`chp_power_only_heat_rates_NEISO.csv` exists anywhere on the backcast path, or
the keeper's `run_config.json` records `true`. Either would mean the artifact is
live on the keeper and the re-derive needs an A/B.

**P2 — STRICT NO-OP OFF THE PHENOMENON.** Gate 3 has no threshold: a plant with
no dark units gets `dark_share = 0.0` and a byte-identical rate.

*Test:* on the re-derived NEISO artifact, **every row except 1595 keeps its
`heat_rate`, `flag`, `thermal_share`, `heat_rate_credited`, `basis_heat_rate`
and `model_heat_rate` bit-identical to the committed artifact.** Only 1595's
`heat_rate` may move, and only downward.

*Falsifier:* any second row moves, or any `flag` flips anywhere. That would mean
the re-derive carries a change the citation does not cover — the commit would no
longer be a gate-3 re-derivation and the artifact does not ship.

**P3 — THE PUBLISHED MAGNITUDE REPRODUCES.** miso-122 measured Kendall's 2023
dark share at **1.2 %**; the session prompt carries the three-year series
**1.21 / 0.96 / 1.48 %** and a corrected 2023 rate **9.5584 → 9.4423 (−1.2 %)**.

*Test:* re-deriving at `--vintage 2023` reproduces `dark_fuel_share ≈ 0.0121`
and `heat_rate ≈ 9.4423` for `(1595, CC_CHP)`, to 4 dp.

*Falsifier:* a materially different number means either the committed derive has
drifted or the hand-off number was wrong. **Either way the discrepancy is
reported as measured and the number of record is corrected, never re-narrated**
(miso-126 §6/§8-5).

**P4 — RECONCILIATION GATE HOLDS.** Gate 3 applies the share only where
`cems_vs_egrid_total` is inside (0.9, 1.1), so the CEMS unit split may be
attributed to eGRID's plant total.

*Test:* 1595's committed `cems_vs_egrid_total` is **1.0**; it must stay in band
on the re-derive.

*Falsifier:* out of band ⇒ the row flags `dark_unreconciled` and is **excluded
rather than corrected**. The artifact still ships (the exclusion *is* gate 3's
answer) but the magnitude of record becomes zero.

**P5 — NO CROSS-ISO WRITE.** Rule 25 `[R-ISO-SCOPE]`: only
`chp_power_only_heat_rates_NEISO.csv` is written.

*Falsifier:* any other ISO's artifact changes on disk ⇒ stop, revert, and do not
commit. PJM's and CAISO's remain ungated and are **handed off with their
measured numbers**, exactly as miso-122 and nyiso-120 handed NEISO's off.

### 1.3 What item 1 can and cannot reach — declared ex ante

`measured_chp_heat_rates` **NEISO is `O`, not `K`**, and neiso-70 recorded
exactly why: the mechanism is **live** (max |Δ| 204.6 MW, every pre-registered
gate passing, C3c bit-identical) but **overshoots the class it reprices** —
`CC_CHP` crosses from over- to under-generating in every year (2023 |error|
0.224 → 0.369 TWh) on a **+27.96 %** dearer cap-weighted offer at the LP seam.

The dark gate moves Kendall's rate by **−1.21 %** of itself. Kendall is 206.0 of
the 429.7 MW the artifact reprices.

*Pre-declared honest ceiling, stated before measurement:* **the dark gate cannot
flip the `O` cell.** Its cap-weighted effect on the repriced population is of
order half a percent against the +27.96 % that produced the overshoot — roughly
one part in fifty of the object that blocks promotion. **Item 1 is a
correctness repair, not a route to `K`,** and it will not be reported as one
whatever the arithmetic returns. Any claim that it improves NEISO's fit would be
a rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]` inversion.

*What item 1 therefore ships, and the only thing it ships:* a corrected NEISO
artifact whose scope gates match the other four ISOs', a stamped statement of
its inertness-by-construction on the designated keeper (P1), and the measured
magnitude for the successor lane that will one day adjudicate the `O` cell.

---

## 2. Item 2 — NEISO 6081 Stony Brook `CA1`, presence first

### 2.1 The question, and the one that is NOT being asked

miso-126 §8-2 hands this off with presence **`UNDETERMINED`** even on the
basis-consistent test: fleet **435.7** MW against EIA-860 **446.6** including
`CA` / **350.6** excluding it. Vintage-coherent (all 1981). *"That lane must
resolve presence first."*

**Presence is the entire Phase-0 question.** Whether NEISO should enter
`plant_taxonomy.CC_STEAM_PART_REPAIR_ISOS` is downstream of it and is not
assumed here.

### 2.2 Properties, with falsifiers

**Q1 — BASIS.** The comparison is made on the **fleet's own `pmax` rule**:
summer capacity where present, else nameplate, coalesced per row (miso-126 §3's
census-method correction). Both bases are reported; the coalesced one decides.

*Falsifier:* if the two bases disagree about the verdict, the verdict is
**`UNDETERMINED` and the item stops** — a presence claim that depends on which
capacity column you pick is not a presence claim.

**Q2 — TOTALS, NEVER SIBLINGS.** Presence is decided against the plant's
**EIA-860 operable plant TOTAL**, never against block siblings (miso-125 §6, the
DO-NOT-MISREAD).

*Test, pre-declared with its bands:*
* **`MISSING`** ⇔ fleet total ≈ EIA-860 total **excluding** `CA` (±1 MW) **and**
  the total **including** `CA` exceeds it by > 1 MW.
* **`REPRESENTED`** ⇔ fleet total ≈ EIA-860 total **including** `CA` (±1 MW).
* **`UNDETERMINED`** ⇔ neither. **This is a real outcome, not a failure to
  measure**, and it closes the item with no arm.

*Falsifier:* `REPRESENTED` ⇒ the capacity is already in the LP, adding it would
be a double count, and the item closes.

**Q3 — PREDICATE MATCH.** 6081 `CA1` must satisfy
`fleet/eia860.py::cc_steam_part_generators` verbatim: prime mover `CA`, own
Energy Source 1 ≠ `NG`, non-empty Unit Code, ≥ 1 sibling at the same plant
sharing that Unit Code with prime mover `CT` and Energy Source 1 `NG`, and the
steam part **not older** than the oldest such sibling.

*Falsifier:* any clause fails ⇒ the row is out of the repair's population and
the item closes on the predicate, whatever the presence verdict says.

**Q4 — THE FUEL MAP ACTUALLY DROPS IT.** The repair only ever *restores* a row
the fuel map drops; it never reclassifies a represented one (miso-126's 1004
Edwardsport false positive).

*Test:* `fleet/eia860._map_fuel_type` returns `None` for the `CA1` row's
technology/energy-source pair, and no `6081` row of ≈ 96 MW appears in NEISO's
loaded fleet.

*Falsifier:* the row resolves under some other class ⇒ `REPRESENTED` by another
name; item closes.

**Q5 — THE MISO-126 FIVE PROPERTIES ARE RE-RUN ON NEISO'S OWN DATA.** Rule 25:
MISO's `K` transfers nothing. Before NEISO may be added to
`CC_STEAM_PART_REPAIR_ISOS`, miso-126's **P1 absence, P2 one-meter-one-rate
(including the implied-CF falsifier), P3 design-share coherence, P4 artifact
stability, P5 no-other-ISO-moves** are re-measured on NEISO's data.

*Falsifier:* any one fires ⇒ NEISO does not enter the ISO set and the cell is
stamped with the property that killed it, **not** left silent.

**Q6 — DFO IS NOT AUTOMATICALLY A DUCT FUEL.** `CA1` reports `DFO`. miso-126's
whole premise is that a `CA` row's Energy Source 1 names the block's
**supplementary/duct** fuel. At a plant that is genuinely oil-capable this may
instead be the block's real fuel.

*Test:* the `CT` siblings' own Energy Source 1 / 2 and the plant's CAMPD fuel
mix.

*Falsifier:* if `DFO` is a primary energy input for the block rather than a duct
fuel, the restored row's block-heat-rate representation is wrong and the item
closes `R` on Q6.

---

## 3. Kill criteria for an LP arm, pre-declared and in order

An arm is built **only** if an item clears every property above. If one does:

**K0 — CONTROL INTEGRITY.** Arm A is a **same-HEAD zero-delta control**
(`scripts/replay_keeper.py` on `2026-08-03-neiso-caiso156-meter-screen`, `--years
2023 2024 2025` in ONE invocation). Every delta in this session is quoted
against arm A and **never** against the committed keeper (miso-124: price
response is not stable across keepers).
*Kill:* arm A's own recipe differs from the keeper's in any solve-affecting
field ⇒ stop.

**K1 — ARMING VISIBLE.** Arm B's `run_config.json` records the flag `true` and
arm A's records it `false` (rule 26 `[R-REGISTRY]`).

**K2 — FIRING PROVEN AT TWO GRAINS (miso-126 §4, the rule that caught the
wiring gap).** A pre-arm `load_fleet_from_csv` check **and** a post-arm per-class
**ENERGY** delta. **A null is not trusted until both fire.** A fleet-loader
firing check alone is not sufficient proof.
*Kill:* loader fires, LP shows zero class-energy delta ⇒ **that is a wiring bug,
not an inert mechanism** — the nyiso-89 / miso-126 class. Stop, find the seam,
and run `tests/unit/data/test_cc_steam_part_capacity.py::TestBackcastFleetSourcing`
(extended if this lever enters by a different seam).

**K3 — ENERGY CONSERVATION ON THE FULL IDENTITY.** miso-126 §6: the
`class_hourly` sidecar is **not** the whole balance. Score
`Δclass + Δdischarge − Δcharge + Δslack − Δdump − Δdemand == 0` over
`hourly/class_hourly_<y>.parquet`, `hourly/storage_<y>.parquet` and
`hourly/system_<y>.parquet`, tolerance 0.5 GWh, with `Δdemand` exactly 0.
*Kill:* residual outside tolerance ⇒ **a boundary defect in the statistic before
it is a result** — complete the statistic, never widen the band.

**K4 — NO CRITERION REGRESSES INTO A FAIL.** `calibration_verdict.py --run-id`
on committed artifacts. A worse fit from a more accurate input is **kept** and
routed to root cause (rule 14 `[R-ACCURATE]`); a *new FAIL* stops the promotion.

**K5 — RULE 16.** One bundle, `--years 2023 2024 2025` in a single invocation.
A per-year chain writes `meta.json` with only the last year and silently breaks
this — it is forbidden.

**K6 — LOYO.** Any mechanism-change-driven verdict flip is scored
leave-one-year-out within 2023–2025 before any promotion.

---

## 4. The six DO-NOT-MISREAD guards, applied ex ante

1. **miso-119** — a max |Δ| is an **upper bound only**. No magnitude in this
   session is predicted from one.
2. **miso-121** — **binding is not marginality**. Nothing here is sized from a
   count of binding hours.
3. **miso-122** — `max_abs_class_hour_mw` is **not** a mechanism magnitude. Every
   magnitude reported is a per-class **ENERGY** delta.
4. **miso-124** — price response is **not stable across keepers**. Every delta is
   quoted against the same-HEAD zero-delta control arm A (K0), never against the
   committed predecessor.
5. **miso-125** — a wrong-sign magnitude is a **denominator defect**.
   Presence (Q2) is tested against the plant's **EIA-860 TOTALS**, never against
   block siblings.
6. **miso-126** — (a) a **fleet-loader firing check is not sufficient proof**;
   firing is proven at two grains (K2). (b) A magnitude that violates a
   **conservation law** is a boundary defect in the statistic before it is a
   result (K3).

---

## 5. What is settled and is NOT re-opened (rule 28a DO-NOT-REDO)

* `da_virtual_bids` NEISO is **`R`** (neiso-76, both limbs, no solve). Not
  re-tested.
* `pumped_storage_cycling_depth` NEISO is **`G`** (neiso-74). No storage-side PS
  lever until the diurnal amplitude defect closes.
* `chp_steam_floor_p25` for NEISO `CC_CHP` is **DO-NOT-REDO** (neiso-71): NEISO's
  merchant `CC_CHP` genuinely carries no host-steam obligation, and the
  Kendall-based floor would be a fitted parameter (rules 21/24). **This session
  builds no floor.**
* Kendall's **capacity basis** is `ADJUDICATED-ARTIFACT` (neiso-73): the EIA-860
  206.0 MW summer basis is correct and CAMPD unit-4 `grossLoad` is not gross
  electrical MW. **Not re-opened.** Item 1 changes a *heat rate*, not a capacity.
* `cc_steam_part_capacity` **MISO** is `K` and its population is a closed
  national census of four rows. Not re-tested.
* NEISO's C3c is a ledgered caveat with a **declared frontier**. Neither item
  targets it and neither will be reported as touching it.

---

## 6. Rule duties this session discharges

| Rule | Duty |
|---|---|
| 13 `[R-MEASURED]` | Both items are published EIA-860 / eGRID / CAMPD **inputs** that regenerate for a forward year. Neither is a measured outcome fed back. |
| 14 `[R-ACCURATE]` | A worse fit from a more accurate input is a discovered root cause, never grounds to revert. Stated in both directions before measurement. |
| 15 `[R-DASHBOARD]` | Every completed run is registered in-session. **If a phase produces no LP run, this document's successor states that explicitly** rather than leaving it implied. |
| 16 `[R-ALLYEARS]` | 2023 2024 2025, one bundle, one invocation. |
| 22 `[R-HOLDOUT]` | Training years only. NEISO's locked test is SPENT and never re-grantable. |
| 23 `[R-FROZEN-DERIVE]` | The re-derive cites the **miso-122 gate-3 scope change**, on measured grounds. No residual is consulted. |
| 25 `[R-ISO-SCOPE]` | NEISO derives its own parameters from NEISO's own data. MISO's `K` transfers nothing; `cc_steam_part_capacity` NEISO enters as `U`. No CAISO/PJM/other cell is stamped. |
| 26 `[R-REGISTRY]` | Any arming is visible in `run_config.json`. |
| 27 `[R-PUSH]` | Exact on-disk bytes; blob-verify line count + hash after any push touching a ≥300-line file (`derive_chp_power_only_heat_rates.py` is 742 lines). |
| 28b | The tested cells are stamped **in this session**, inert and rejected verdicts included. |
| 28c | Any new solve-affecting `ScenarioConfig` field gets its matrix row in the same PR. |

---

*Pre-registered by neiso-80, 2026-08-04, before any arm and before any
adjudicating statistic.*
