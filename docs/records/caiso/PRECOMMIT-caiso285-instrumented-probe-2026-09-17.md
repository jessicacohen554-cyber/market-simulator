# PRECOMMIT caiso-285 — the INSTRUMENTED PROBE of the CAISO RA bridge's candidacy, with its verdicts fixed before any number exists

**Lane:** CAISO calibration · **Date:** 2026-09-17 · **Keeper:** `2026-09-12-caiso-275-gascoupling`
(bundle `results/calibration/caiso275_B_gascoupling_span`, solve sha
`b8ddf8bc6ae539fb3a6c55824b4c5ead24521abe`) · **LP spent by this session (the parent): ZERO**
(rule 32 `[R-SHARD]` (a)). Nothing armed, no `ScenarioConfig` field, no derive re-run, **no
mechanism cell moved** (rule 28 `[R-MECH-MATRIX]` duty (b) is not owed — this probe tests no
mechanism; it instruments one that is already in the keeper).

This document is written and **PUSHED BEFORE THE SHARD IS LAUNCHED**. Every threshold, bucket
definition, hour set and verdict word below is fixed here. Nothing in §4–§6 may be edited once a
probe number exists; a change goes in a dated ADDENDUM that says what moved and why.

---

## 1. The object, inherited — not re-derived

`FINDING-caiso284-belly-commitment-phase0-2026-09-16.md` settled it. In the 2024 belly (lowest
decile of model net load, 876 h) CAISO `CC_REGULAR` runs **100 % out of its `committed` band and
exactly 0.0 MW out of all twelve econ/peak bands**, and that band delivers **670.471 MW** against
its own year-max of ~4,063 MW — roughly one fifth of the CA CC fleet's own minimum-load block
(0.26 × 12.7 GW ≈ 3.3 GW). Actual belly gas is 7.2 GW (caiso-275 §1). **No offer-level lever can
move belly gas**; the object is bridge **COVERAGE** — which units become candidates.

Reproduced here at zero LP from the keeper's own committed sidecars, to the milli-MW:
`committed` = 670.471, every `econc0*` and `peak*` = 0.000. The belly hour set is frozen in
`results/calibration/_caiso285_belly_2024.json` (876 hours, `sha256[:16] = c5948fb0d43620a1`,
construction recorded in the file).

## 2. What the keeper actually arms — including one gate caiso-284 did not name

Read from the keeper's own `run_config_2024.json`:

| field | keeper value | bearing |
|---|---|---|
| `caiso_ra_mustoffer` | `True` | the bridge is on |
| `caiso_ra_startup_bridge` | `True` | ≥min-down economic bridges enabled |
| `caiso_ra_bridge_decommit` | `True` | DA-horizon cap + surplus decommit screen on |
| **`caiso_ra_bridge_startup_aware`** | **`True`** | **the RUN SCREEN is on** |
| `caiso_ra_startup_trajectory` | `True` | lead-hour ramp-in floors before every KEPT run |
| `caiso_ra_bridge_curtailment_release` | `False` | `release_hours is None` — the release limb cannot fire |
| `caiso_ra_mustoffer_quantity_gate` | `False` | the published-RA MW cap is NOT applied |
| `caiso_ra_min_load_frac` | `0.26` | measured, rule 23-frozen (§4 do-not-redo) |

Two of these change the suspect list the handoff inherited:

* **`caiso_ra_mustoffer_quantity_gate` is OFF**, so the published gas-RA MW cap is *not* what caps
  coverage. Ruled out here, with no probe needed.
* **`caiso_ra_bridge_startup_aware` is ON**, and the handoff's three suspects do not include it.
  In `model/commitment.py:1062-1109` the screen keeps only runs whose own P0 margin per MW of
  capacity (`Σ_t (LMP − MC) × dispatch / pmax`) repays one startup, then **rebinds `runs` to
  `kept_runs`**. A unit whose runs are all dropped falls out at `if not runs: continue` and
  receives **no floor of any kind** — not the unconditional sub-min-down physical bridge, not the
  startup-trajectory lead. It is the only gate in the mechanism that can zero a unit outright, and
  it sits **upstream of all three named suspects**. It is carried below as **S4**.

## 3. Drift: what the probe is replaying against

`replay_keeper.py` is byte-faithful by construction (it rebuilds the kwargs from `meta.json`), but
HEAD is 5 days and 96 files past the keeper's solve sha. Two facts, both measured at zero LP:

* **Registry-value drift for CAISO is ZERO.** The capx-D79 solve-surface fingerprint projected onto
  CAISO at `origin/main` is `cba92d202f32f9fd` over 204 rows with `moved = {NUCLEAR_MONTHLY_CF_BY_YEAR:
  9f120808f18b3f19, STATE_CARBON_PRICE_BY_ISO: c970824c3c583991}` — **identical, name for name and
  hash for hash, to the block the keeper's `run_config_2024.json` recorded.** `SOLVE_EPOCHS` is
  empty. None of the seven registry modules a CAISO solve reads has moved.
* **Code drift is NOT zero and is not audited here.**
  `git diff b8ddf8bc..origin/main -- src/market_sim scripts/run_calibration*.py scripts/lib
  data/raw/_validation-source data/raw/reference` is 96 files, +14,739/−1,445. Much of it is
  plainly another lane's (NWPP/SOCO scaffolding, PJM capacity-evolution arms, MISO interchange,
  forecast-only capacity steps a `mode="backcast"` run never enters), but files a CAISO backcast
  does touch also moved (`data/zone_assignment.py`, `data/hydro.py`, `data/renewables.py`,
  `data/fleet/campd_bins.py`, `data/offer_curves.py`, `pipeline/backcast_config.py`,
  `model/lp/*`).

**This probe does not spend a hunk-by-hunk G-DRIFT audit, and states why rather than skipping it
quietly.** Rule 29 `[R-SCREEN]` (b) requires G-DRIFT to validate G-CTRL **form 4** — differencing an
ARM against the keeper's committed numbers. **This probe runs no arm.** It re-solves the keeper's
own recipe, so the drift question is answered *directly and empirically* by whether the re-solve
reproduces the keeper's own 2024 price — a strictly stronger test than classifying hunks, and one
the probe performs for free. It is pre-registered as gate **G1** in §5.

## 4. Do-not-redo, inherited and enforced (rule 28 `[R-MECH-MATRIX]` (a))

Not re-opened by this session, and not re-measured:

1. `caiso_ra_min_load_frac` = 0.26 — MEASURED (CAMPD/CEMS P5 of net CF over online hours,
   cap-weighted 0.259 over 23 plants / 12.7 GW), rule 23 `[R-FROZEN-DERIVE]` refuses re-derivation
   without new source data. The NYISO 0.523 / ERCOT 0.574 gap is a **statistic** difference.
2. The export family — `caiso_p1_export_sink_seam` **R**, `caiso_corridor_export_path` **R**,
   `caiso_node_export_constraint` **G**.
3. RTM-basis CC offer surface — FLAT on an exact instrument (caiso-283 §3).
4. Re-pointing C3a at the DA benchmark — withdrawn (caiso-281 §5.1).
5. The flat ×0.92 fossil multiplier — owner-blocked (rules 1 c / 14).
6. Scarcity/ORDC overlay (caiso-270); tranche granularity; import quantity (caiso-280).

## 5. The probe, and its two HARD STOPS

**ONE shard** (rule 32 `[R-SHARD]` (a): the parent never solves), **ONE year**, ONE command:

```
.venv/bin/python scripts/replay_keeper.py results/calibration/caiso275_B_gascoupling_span \
  --years 2024 --out-dir results/calibration/caiso285_instr_2024 \
  --persist-p0-commitment --note "caiso-285 instrumented replay: P0 pattern + SOC"
```

A **one-year** shard is correct here and is not the rule 32(b) fan-out ban: that ban protects a run
that must be REASSEMBLED for registration. **This bundle will never be registered** — registering a
2024-only replay of a 2023–2025 keeper would violate rule 16 `[R-ALLYEARS]` outright. It is a
diagnostic. It nevertheless **pushes its whole bundle**, `dispatch/2024_P1.parquet` and `floors/`
included (rule 34 `[R-SHARD-PROMOTABLE]` (a): `.gitignore` negation + a **plain** `git add`, never
`git add -f`), because the cost of stranding bytes on an ephemeral container is a full re-solve and
the cost of pushing them is ~100 MB that the `caiso275_B_gascoupling_*` bundles already precede.

Both persisted flags are **WRITE-ONLY**: `p0_commitment_bits` is packed at
`run_calibration.py:6860`, *after* `energy_solve` has returned, and `persist_p0_commitment` is in
`run_calibration_full._REUSE_IGNORED` precisely because two runs differing only in it have
byte-identical solves. `soc_mwh`/`energy_cap_mwh` persist `DispatchResult.storage_soc`, a variable
the LP already solved. Neither is a `ScenarioConfig` field.

### G1 — THE REPRODUCTION GATE (pre-registered, hard)

The shard reports its 2024 **load-weighted model price**, computed from its own
`hourly/system_2024.parquet` as `Σ(price × demand) / Σ demand` over all zones and all 8,760 hours.

* **G1 PASS** — it reproduces the keeper's committed value to **< 0.01 $/MWh**. The probe's
  artifacts are then the keeper's own, and §6 reads as a statement about the keeper.
* **G1 FAIL** — it does not. **That is the finding**, reported as such: HEAD has drifted off the
  keeper on the CAISO backcast path, which is material for every CAISO lane and for the keeper's
  reproducibility. §6 still runs — the artifacts remain a faithful reading of *this recipe at
  HEAD* — but **every conclusion is stated as "at HEAD", never attributed to the keeper**, and the
  drift is routed to its own root-cause card rather than absorbed.

Pre-registering both branches is deliberate: a probe whose only reported outcome is "it matched" is
not a test.

### G2 — THE ALIGNMENT GATE (pre-registered, hard)

`hourly/p0_commitment_2024.parquet.unit_id` must be row-for-row identical to
`floors/2024_P1.npz["unit_ids"]`, and `p0_commitment_pattern`'s threshold (`0.05 × pmax`,
`run_calibration.py:365`) must equal the detector's `run_threshold_frac` default (0.05,
`model/commitment.py:697`) — so `find_runs` on the unpacked bits reproduces the detector's `runs`
**exactly, before its screen**. Both are verified in the parent before any bucket is counted. A
mismatch STOPS the analysis; it is not worked around.

## 6. THE DECISION RULE — fixed here, before any number

### 6.1 The eligible population **E**

Rows `g` of the 2024 fleet that reach the detector's per-unit body at all:
`not plant_group.endswith("_CHP")` **and** `fuel_type ∈ {gas_cc, gas_ct}` **and**
`_ra_bridge_unit_params(gen, heat_rate) is not None` (a class commitment table exists, and the row
is not a binned incremental tranche carrying `startup_per_mw = 0`). `E_cc` is its `CC_REGULAR`
subset; CT is reported separately and never pooled with CC.

`E_econ ⊂ E` additionally satisfies the detector's economic-eligibility test:
`startup_per_mw > 0` **and** `min_down ≥ RA_BRIDGE_ECON_MIN_DOWN_HOURS` (4.0).

`target_mw(g) = min(0.26 × plant_pmax(g), pmax(g))` — the detector's own floor target, computed
with the detector's own `plant_pmax` grouping (bin-id prefix `unit_id.rpartition("_")[0]`).

### 6.2 The exhaustive partition

For every belly hour `h` in the frozen 876 and every `g ∈ E`, exactly one bucket, evaluated in this
order:

| bucket | condition | meaning |
|---|---|---|
| `P_UNAVAIL` | `availability[g,h] == 0` | an outage — **excluded from the deficit**; not a coverage failure |
| `P_ON` | P0 bit set at `h` | the unit is already running; no bridge is needed |
| `P_FLOOR` | `floors[2024_P1].mechanism[g,h] == 7` (`MECH_RA_MUSTOFFER`) and `min_gen[g,h] > 0` | the bridge HELD it |
| `S4` | off, inside a gap `< min_down`, unfloored | a physical restart bar is bridged **unconditionally**, so unfloored here has exactly one route: **`startup_aware` dropped the anchoring runs** (`release_hours is None`, §2) |
| `S1` | off, inside a gap `≥ min_down`, `g ∉ E_econ` | the **4 h min-down eligibility** gate |
| `S2` | off, inside a gap `> 24 h`, `g ∈ E_econ` | the **`DA_COMMITMENT_HORIZON_HOURS`** cap |
| `S3_5` | off, inside a gap in `[min_down, 24]`, `g ∈ E_econ`, unfloored | the **restart inequality** (`mc_gap`) **or** the surplus **decommit** screen — jointly, and reported jointly |
| `S0` | off, and **not inside any gap** (before the first run, after the last, or the unit has no P0 run at all) | **no anchor**: the fleet is not running adjacent to the belly, so there is nothing for a bridge to bridge |

Each bucket is summed as `Σ_{h ∈ belly} Σ_g target_mw(g)`, then divided by 876 to read as **mean
belly MW**. The partition is exhaustive by construction, so the buckets sum to
`Σ_g target_mw(g)` and nothing is unattributed.

```
DEFICIT  =  S0 + S1 + S2 + S3_5 + S4          (mean belly MW)
share(X) =  X / DEFICIT
```

### 6.3 Verdicts

Applied to **S1, S2, S3_5, S4 and S0 alike** — S0 is a candidate answer, not a residual:

* **IMPLICATED** — `share ≥ 0.40`.
* **CONTRIBUTORY** — `0.05 ≤ share < 0.40`. Named on the record; **not** promoted to a lever.
* **EXONERATED** — `share < 0.05`.

Two pre-registered readings of the whole:

* **If `share(S0) ≥ 0.40`** the conclusion is that **the object is UPSTREAM of the bridge**: the CC
  fleet is not running adjacent to the belly in P0 at all, so no commitment-gate parameter can
  reach it, and the successor is a dispatch question (why the base-cost LP does not start CC
  around the belly), not a bridge question. This is a legitimate and, on the phase-0 evidence,
  likely outcome — **naming it in advance is the point**, so that finding it cannot later be
  presented as a disappointment or quietly converted into a search for something else.
* **If no bucket reaches 0.40 and `S1 + S2 + S3_5 + S4 < 0.60 × DEFICIT`**, no lever is identified
  and **no span is launched.** The session reports the partition and stops.

### 6.4 Falsifiable identity checks (reported pass or fail, never asserted)

1. `P_FLOOR` (mean belly MW) **≤ 670.471** — a floor cannot exceed the band's delivered energy.
2. `P_FLOOR ∩ P_ON = ∅` — `floor_online_hours` is off for CAISO, so no RA floor may land on a
   P0-online hour. Any overlap is reported at full size and the partition re-stated.
3. Every `g` with `P_FLOOR > 0` has `≥ 1` P0 run — the run screen's own by-construction claim
   (`runs` is rebound to `kept_runs` and every floor leg reads it), made falsifiable rather than
   assumed.

### 6.5 The storage-energy premise — a separate, independently pre-registered test

`_apply_economic_bridges` excludes storage-charge headroom from `absorb` on an explicit **energy**
premise: *"the fleet already fills by the belly in P1."* caiso-284 falsified the **power** half
(1,477 / 1,945 / 2,391 MW of unused charge power) and could not test the energy half at all —
committed sidecars carried no SOC, and a reconstruction from the tech-aggregate failed its own
physical check (420–4,121 % of implied capacity) and **is not quoted**.

From the probe's `hourly/storage_2024.parquet` (`pass == "P1"`), define per belly hour
`H(h) = Σ_tech (energy_cap_mwh − soc_mwh)` and `C = Σ_tech energy_cap_mwh`:

* **UPHELD** — `median_{h ∈ belly} H(h) / C < 0.05`.
* **FALSIFIED** — `median_{h ∈ belly} H(h) / C ≥ 0.20`.
* **INDETERMINATE** — between. Reported as such; no lever either way.

Reported alongside, because it is the quantity that decides whether the power matters:
`median H(h) ÷ 1,945 MW` — the hours of charging the unused belly charge POWER could actually
sustain. Under **0.5 h** the power is unusable whatever the headroom ratio says, and that is stated
as the operative fact.

**A FALSIFIED verdict does not by itself arm anything.** It converts "counting storage headroom in
`absorb`" from an untested premise into a testable mechanism — which would then need its own
PRECOMMIT, its own screen, and the four-year span rule 34 `[R-SHARD-PROMOTABLE]` (c) prices at
2022–2025.

## 7. What a positive result costs, stated before it is wanted

CAISO's registered year set is **2022, 2023, 2024, 2025** (rule 34 (c), rule 35 `[R-PROMOTE]` (c):
a promotion must cover the union). So any mechanism this probe identifies is priced at **four
year-shards**, each pushing its bundle, after its own PRECOMMIT. Nothing in §6 authorizes that
span; §6.3's "no lever ⇒ no span" is binding.

## 8. Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e))

The shard pushes its full bundle to its own branch and the RESULT will record the **full 40-char
SHA** of that commit plus the `git checkout <sha> -- <path>` line (rule 33 `[R-SHARD-ARCHIVE]` (d)),
never a branch name. The parent verifies `git ls-tree -r <sha> -- results/calibration/caiso285_instr_2024`
returns more than zero files **before** archiving the shard (rule 34 (d)), and archives only after
fetch + checkout + verify (rule 33 (a)).

## 9. Rules this session is operating under

Rule 1 `[R-STRUCT]` (no mechanism selected because a residual moved — §6 fixes the verdicts before
the numbers), rule 12 `[R-PARALLEL]`, rule 15 `[R-DASHBOARD]` (**this probe is not registered**:
a 2024-only replay of a 2023–2025 keeper is not a registrable run under rule 16 `[R-ALLYEARS]`),
rule 23 `[R-FROZEN-DERIVE]` (§4.1), rule 28 `[R-MECH-MATRIX]` (§4; duty (b) not owed), rule 31
`[R-RETAIN]` (nothing deleted until the owner rules; the promotion question is asked in the final
report), rules 32–34 (§5, §8), rule 35 `[R-PROMOTE]` (§7).
