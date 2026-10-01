# FINDING — capx D29: the trajectory summary now carries an energy mix and a real storage column (additive; zero solves)

**Session:** D29 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d29-trajectory-grain`, the reporting-grain fix D25 §6.1 routed.
**Date:** 2026-09-01 · **HEAD at launch:** `3c1f9642` (branch cut fresh off `origin/main`).
**Zero solves.** No committed bundle was regenerated, no scorer was re-run, no verdict,
disposition, board or keeper surface was touched.

**Headline.** `run_full_horizon.extract_trajectory` gains an **energy block**
(`generation_by_fuel_mwh`, `total_gen_mwh`, `storage_discharge_mwh`, `storage_charge_mwh`) and
a **real storage power column** (`storage_power_mw`, read from the evolution ledger's own
fleet-state field). The change is **strictly additive**: every pre-existing key keeps its name,
type and meaning, pinned by a test. The defective `storage_mw` is **kept bug-compatible** —
three committed consumers read it, two of them by comparing two summaries key-by-key (§3). The
FC-5 corridor's 252 AEO generation anchors become dispositionable **for future runs**; the 34
committed summaries stay on the old grain until their bundle next re-solves (§5), which is what
the charter specified.

**One thing found that the charter did not anticipate, and it matters more than the fix:** the
ledger field the new column reads is the **whole** storage fleet — batteries **and pumped
storage** — while AEO's "Diurnal Storage" anchor is batteries only. Quoting the new column
against that anchor raw would manufacture a false convergence (PJM 2030: −13.6 % "IN CORRIDOR"
against a real battery divergence of −92 %). The trap is documented at the definition, pinned
by a test, and §6 routes the one-field producer split that removes it. **D25's storage rows
were right**; this is a warning about the new column, not a correction to them (§4).

---

## 1. What changed, exactly

`scripts/run_full_horizon.py` — `extract_trajectory` (+ one new module helper
`_storage_throughput_mwh`). New keys per trajectory row:

| key | type | source | meaning |
|---|---|---|---|
| `generation_by_fuel_mwh` | `dict[str, float]` | `C._fuel_gen_mwh(yd)` | annual **dispatched** energy by fuel — thermal summed on the fleet context's `fuel_types`, wind/solar from their own dispatch arrays (post-curtailment, which is what a generation anchor reports) |
| `total_gen_mwh` | `float \| None` | `sum(gen.values())` | the denominator an energy-**share** anchor needs; `None` when the year carries no fleet context |
| `storage_discharge_mwh` | `float \| None` | `result.storage_discharge.sum()` | `None` = no storage arrays at all ("not measured"), never 0.0 |
| `storage_charge_mwh` | `float \| None` | `result.storage_charge.sum()` | same |
| `storage_power_mw` | `float \| None` | **ledger** `storage_power_mw` | the storage fleet's nameplate power after that year's entry screen; `None` on legacy ledgers |

Storage is deliberately **not** folded into `generation_by_fuel_mwh`: discharge is round-tripped
energy already counted at charge, so summing it into the fuel mix would double-count. It is
reported as its own throughput pair.

`src/market_sim/results/evolution_ledger.py` — docstring only: the schema block never listed
`storage_power_mw` / `storage_firm_mw` / `wind_cap_mw` / `solar_cap_mw` /
`renewable_credit_applied`, all of which `runner.run_scenario_iso` has been writing. Now listed,
with a paragraph stating that `storage_power_mw` is the **only** durable record of the storage
fleet state and why (`FleetContext` carries `storage_energy_cap_mwh` but no power column, and
LP storage resources are not on the generator axis).

`tests/scoring/test_full_horizon_instruments.py` — a new `TrajectoryReportingGrainTest` over a
synthetic `Run` (a real `FleetContext` + a real `DispatchResult`, no LP), seven cases: the energy
block closes on its own total; storage is not folded into the fuel mix; `storage_power_mw` is
**nonzero** against a fleet with storage and equals the ledger value; `storage_mw` stays 0.0
beside it; an absent ledger key reads `None`, never 0.0; no storage arrays read `None`; and every
legacy key survives with its type. **19 passed** in that module.

## 2. Why the storage column is read from the ledger and not reconstructed

`runner.run_scenario_iso` writes `storage_power_mw = sum(u.power_cap_mw for u in storage_units)`
into every `evolution_<year>.json` — the fleet state **after** that year's new-entry screen. It
is the quantity `storage_mw` was always meant to carry. The alternative (base fleet from the
registry + the cumulative `storage_additions` ledger) is a reconstruction *over* the model's
state rather than the state itself, and it is only as good as its assumption that nothing else
moves the fleet. Reading the ledger costs nothing and cannot drift.

Coverage measured over every on-disk ledger: **232 carry `storage_power_mw`, 83 do not** (older
hindcast bundles predating the field). Those 83 read `None` — "not measured" — following the
ledger's own stated contract for `confirmed_derates` / `firm_clean_accredited_mw`. Rendering
them as 0.0 would assert a fleet that was never recorded.

## 3. The `storage_mw` consumer enumeration, and what was done about it

The charter's rule: repair in place **iff** nothing committed reads it. Three committed consumers
do, so it is **kept bug-compatible**, the new column added beside it, and the defect documented
at the definition.

| # | call site | how it reads it | why an in-place repair would hurt |
|---|---|---|---|
| 1 | `scripts/collate_full_horizon.py:263` | `r.get('storage_mw', 0) / 1000` → the "storage GW" column of the collated findings table | Cosmetically the repair helps, but the table mixes bundles of different vintages in one grid; a repaired new-vintage row beside 0.0 old-vintage rows reads as a storage build-out that never happened. |
| 2 | `scripts/probes/_d9_relative_deltas.py:28` (`SCALARS`) | max **relative** delta per quantity between a cold and a warm summary | Compares **two summaries key-by-key**. A repaired value against an old committed summary reports a phantom multi-GW delta. |
| 3 | `scripts/probes/_d9_forecast_warmstart_ab.py:74` (`_CAPACITY_KEYS`) | the warm-vs-cold **guardrail**: these keys must not move | Same cross-vintage hazard, and here it does not merely mislead — it **fails the guardrail**, i.e. the repair would defeat the very check it feeds. |

Two near-misses checked and excluded: `scripts/probes/_miso150_universe.py` uses `"storage_mw"`
as an unrelated local dict key (an hourly storage-power array), and
`retirements._storage_portfolio_elcc_dilution(existing_storage_mw=…)` is a parameter name, not a
trajectory read. Neither touches the summary.

**Honest note on the cost of bug-compatibility.** Consumer 3's guardrail over `storage_mw` is
today a **dead check** — the key is 0.0 in both arms of every A/B, so it can never detect a
storage difference. Keeping it bug-compatible keeps it dead. The right repair is for that probe
to add `storage_power_mw` to `_CAPACITY_KEYS` **once every arm it compares is post-D29**;
doing it now would break cross-vintage comparisons, so it is routed (§6), not done here.

**The magnitude of the defect, measured on the committed corpus.** All **34** committed
`full_horizon_summary.json` files (230 trajectory rows) read `storage_mw = 0.0` in **every year**
— including ten CAISO bundles. Against the same bundles' own committed ledgers:

| bundle (the five FC-5-dispositioned + one CAISO) | ISO | summary `storage_mw` | ledger `storage_power_mw` (2026) |
|---|---|---|---|
| `ff-t3-neiso-golden/bau` (the golden) | NEISO | 0.0 | 2,635.0 |
| `ff-t1f-s6-pjm/ledger` | PJM | 0.0 | 5,546.1 |
| `ff-t1f-s123/verify` | MISO | 0.0 | 3,216.8 |
| `ff-t1f-extcap/nyiso` | NYISO | 0.0 | 1,470.0 |
| `ff-t1f-s4b-ara/neiso` | NEISO | 0.0 | 2,635.0 |
| `ffr4e/caiso-control` | CAISO | 0.0 | 17,527.6 |

## 4. The classification trap the fix uncovered (and why D25 is NOT corrected)

`runner.run_scenario_iso` puts **pumped storage into `storage_units` on both legs** — the
measured leg logs "MW incl. pumped storage", the default leg prepends `load_eia860_pumped_storage`
— so the ledger's `storage_power_mw`, and therefore the new column, is **batteries + PS**.
AEO2025's "Diurnal Storage" row, the FC-5 corridor's storage anchor, is **batteries only** (AEO
books PS separately).

Quoting the new column against that anchor raw would score **PJM 2030 at 5,546.1 MW vs AEO
6.42 GW = −13.6 %, "IN CORRIDOR"** — against a battery-only divergence of **−92 %**. That is a
mapping artifact of exactly the class D25 §2 spent its care avoiding, and it would have flipped a
row's verdict in the model's favour.

**This vindicates D25's basis rather than correcting it.** D25 quoted
`STORAGE_BASE_FLEET_MW[iso]["mid"] + builds_storage_mw` — the battery fleet — which is the
AEO-comparable quantity. The residual against the ledger total is the PS fleet, and it lands
where PS actually is: PJM 5,046.1 / NEISO 1,865.0 / MISO 2,416.8 / NYISO 1,220.0 MW (derived as
ledger total − registry mid; **not** valid for the measured-base-fleet ISOs, whose battery seed
is not the registry scalar, which is why CAISO is excluded from that arithmetic). No D25 storage
row is wrong and none was touched.

Mitigation shipped: the trap is written out at the column's definition with the reconciliation a
consumer must perform, and the test pins the column as **equal to the ledger figure** rather than
merely nonzero, so a future change that silently netted PS here would fail rather than quietly
alter every consumer's basis.

## 5. Which committed bundles remain on the old grain

**All 34.** Every tracked `full_horizon_summary.json` (230 trajectory rows across six ISOs) was
written before D29 and carries none of the new keys. They are **not** regenerated — that needs a
re-solve, which this lane is chartered not to do. Concretely, this means:

- The **252 AEO generation anchors stay undispositionable against today's committed bundles**;
  they become dispositionable against the first bundle solved at or after this commit. The D25
  §6.1 basis caveat is therefore *resolved at the producer* and *still standing on the artifacts*
  until a re-solve lands. That is the intended state, not a shortfall.
- The five FC-5-dispositioned bundles (`neiso-t3`, `pjm-t1f`, `miso-t1f`, `nyiso-t1f`,
  `neiso-t1f`) keep their current FC-5 CAVEAT scores unchanged; nothing in
  `results/ff-corridor/` was read for a verdict or written.
- Every reader must treat an absent new key as backward-compatible, never malformed — the same
  contract the evolution ledger states for `confirmed_derates` / `firm_clean_accredited_mw`.
- **D27 (MISO T1-H, in flight):** if its solve starts after this commit lands its bundle carries
  the new grain; if not, it does not. Either is fine and no coordination was attempted, per the
  charter's collision clause. Nothing on any MISO board surface was touched.

## 6. Routed to the director (none actioned here)

1. **The battery/PS split is the last mile of this fix.** `storage_power_mw` is a fleet total, so
   every corridor use of it needs the §4 reconciliation. `runner.run_scenario_iso` already holds
   the `storage_units` list and `model.storage._battery_mask` already distinguishes the two, so
   emitting `storage_power_battery_mw` / `storage_power_ps_mw` into the ledger is a one-field
   producer addition — but it is in `runner.py`, outside this lane's stated scope, and like every
   producer field it needs a re-solve to populate. A lane already touching `runner.py` should
   carry it.
2. **`_d9_forecast_warmstart_ab.py` should add `storage_power_mw` to `_CAPACITY_KEYS`** once every
   arm it compares is post-D29. Its storage guardrail is dead until then (§3).
3. **The generation anchors need a bundle to land against.** The 252 rows are now producible but
   no committed bundle carries them. The first re-solve of any of the five FC-5 bundles unlocks
   its share; D25 §6.2's ERCOT/CAISO committed-summary gap is the same lane's work.
4. **`total_cap_mw` / `thermal_mw` / `vre_mw` are generator-axis roll-ups and structurally exclude
   storage.** Unchanged by D29 (folding storage into a total whose meaning readers depend on is
   not additive), and now stated in a comment beside them. D25's disposition tables already
   reconcile this by hand ("+ storage base fleet" in their `model_basis` strings); a future
   corridor builder should keep doing so rather than expecting the roll-ups to include it.

## 7. Charter compliance

- **Additive only** — pinned by `test_the_addition_is_additive_every_legacy_key_survives`.
- **Zero solves** — no LP was run; no bundle, verdict, disposition, board or keeper file was read
  for a score or written. The only files changed are the three named in §1.
- **No mechanism, no `ScenarioConfig` field** — rule 28 duties do not fire (no matrix row, no
  cell). No `.github/workflows/` addition (the GitHub-Actions ban).
- **Rule 27** — `scripts/run_full_horizon.py` is a ≥300-line core run script: edited locally with
  targeted string replacements (never a regenerated full-file rewrite), pushed as the exact
  on-disk bytes, and blob-verified after the push (line count + SHA-256 against local).
- **Tests** — `tests/scoring/test_full_horizon_instruments.py` 19 passed;
  `tests/unit/results/test_evolution_ledger.py` + `tests/regression/test_forecast_invariants.py`
  62 passed; `tests/scoring/` full sweep 1226 passed / 3 failed, and those **three failures
  reproduce byte-identically on clean `origin/main`** (`test_forecast_parity::
  test_all_six_keepers_resolve`, `test_ff_readiness_battery::
  test_marker_state_reflects_committed_markers`, `test_crossover_harness::
  test_forward_year_demand_not_from_realized_loader`) — verified by stashing the diff and
  re-running. Pre-existing, unrelated, untouched. `ruff check` + `ruff format --check` clean on
  all three changed files.

---

*Produced 2026-09-01 (D29, Opus, zero solves). Committed deliverables: the extended
`extract_trajectory` + `_storage_throughput_mwh`; the evolution-ledger schema docstring; the
`TrajectoryReportingGrainTest` suite; this finding.*
