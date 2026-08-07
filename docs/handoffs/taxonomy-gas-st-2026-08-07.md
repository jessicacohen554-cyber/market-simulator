# TAXONOMY — the `gas_st` branch in `data.fleet._map_fuel_type` (D-25)

**Session 2026-08-07, branch `claude/fuel-taxonomy-gas-st-n0jir2` (base `origin/main`
c710d17e).** Owner decision **D-25** (SIGNED sitting Addendum Y.4, 2026-08-06; evidence
FFR-7A §4.1, FFR-7C §1.1 note, SCORE-GATE handoff §1). Executed under the Addendum-D
paired-control + HOLD-PROMOTION discipline; rule 14 `[R-ACCURATE]` accurate-data
correction, potentially keeper-moving.

**TL;DR.** Natural-gas steam turbines (EIA-860 prime mover `ST`, energy source `NG`) now
map to the dedicated `gas_st` fuel — the fuel the CAMPD bin path always carried
(`BIN_GROUP_TO_FUEL`) — instead of folding into `gas_ct`. The FFR-7A §4.1 scoring seam is
closed: the scoring target can now contain `gas_st`, so a model `gas_st` retirement is
creditable against an actual. 326 units / 44.9 GW re-label across the six ISOs;
**CAISO, PJM and ERCOT solve inputs are byte-identical**; the solve-affecting residue is
14 synthesized-bin heat rates (MISO 11 / NEISO 2 / NYISO 1 — the rows with no unit-level
eGRID rate, whose `HEAT_RATE_BINS` fallback moves from the gas_ct vintage bins to the
gas_st bin). Paired controls: §4.

---

## 1. Blast radius (measured BEFORE any edit)

Method: the real loader path (`load_fleet_from_csv`) per ISO at `origin/main` c710d17e; a
"physically gas steam" row is one whose `plant_group` resolved to `ST_GAS`/`ST_CHP`, which
`classify_plant` keys on prime mover `ST` + fuel `NG` — the same physical predicate as the
fix. Per-unit table: `docs/handoffs/taxonomy-gas-st/blast-radius-units.csv`.

| ISO | gas_ct-class units | gas_ct MW | steam units | steam MW | % of class MW | ST_GAS / ST_CHP |
|---|--:|--:|--:|--:|--:|---|
| ERCOT | 868 | 20,402 | 42 | 10,136 | 49.7 % | 36 / 6 |
| CAISO | 424 | 12,437 | 6 | 2,859 | 23.0 % | 6 / 0 |
| PJM | 595 | 35,896 | 85 | 9,493 | 26.4 % | 28 / 57 |
| MISO | 749 | 37,838 | 137 | 12,923 | 34.2 % | 38 / 99 |
| NYISO | 172 | 12,432 | 36 | 9,373 | 75.4 % | 27 / 9 |
| NEISO | 127 | 1,632 | 20 | 160 | 9.8 % | 1 / 19 |
| **total** | | | **326** | **44,944** | | |

**CAMPD unitType cross-check** (`blast-radius-campd-xcheck.csv`): 188/326 units
(43.6/44.9 GW) sit at CAMPD-covered facilities; 179 of them (43.4 GW, > 99.5 % of covered
MW) at facilities carrying a CAMPD steam-boiler unitType (`Tangentially-fired`,
wall-fired, `Stoker` — the type FFR-7C cites for Braunig). The 9 outliers (177 MW: New
Ulm, ExxonMobil Beaumont TG*, two small PJM CHP) are facilities where CAMPD covers only
the turbine siblings — facility-grain limitation, not a classification disagreement; the
EIA-860 row's own prime mover `ST` governs (rule 23 identification).

**Why the class structure was already right and only the FUEL was wrong:** the loader's
`plant_group` comes from `classify_plant` (prime-mover-based, has had `ST_GAS`/`ST_CHP`
all along), and non-ERCOT bin synthesis (`fleet_to_bins`) bins every `ST_GAS`/`ST_CHP`
row with bin fuel `BIN_GROUP_TO_FUEL["ST_GAS"] = "gas_st"`. So **binned steam units
already dispatched as gas_st**; the wrong `gas_ct` label lived on the loader record,
where it set the heat-rate fallback / efficiency bin / VOM / EFORd / CO2-NOx of the raw
record, the scoring-target fuel, and every raw-unit path.

### 1.1 The ERCOT CAMPD-bin path — verified, not assumed

The bin side is unaffected by construction: ERCOT's dispatch thermal fleet comes from the
curated `custom-bin-assignments.csv` via `load_campd_bins`, fuel from `BIN_GROUP_TO_FUEL`
(already `gas_st`). **But the raw side is fuel-filtered, and would NOT have been
unaffected without a matching edit:** `build_base_fleet`'s ERCOT branch keeps every raw
EIA-860 unit whose `fuel_type` is NOT in the exclude set (`_AGGREGATABLE_FUELS` on the
forecast path; a `{gas_cc, gas_ct, coal, biomass}` literal in `run_calibration.py` on the
backcast path). ERCOT's 42 steam rows were excluded via their old `gas_ct` label; as
`gas_st` they would have re-entered as ~10.1 GW of raw duplicates of the curated bins.
Both exclude sets therefore gain `gas_st` in the same commit. Verified post-fix: the
forecast path retains only 4 raw units (all nuclear), the backcast path retains the same
295 rows as before, and no `ST_GAS`/`ST_CHP` row is retained on either — **ERCOT is
byte-identical by construction, with the exclusion-set edit as a load-bearing part of
that construction.**

## 2. The fix (commit `deda7e92`)

1. **`_map_fuel_type`** (`src/market_sim/data/fleet/eia860.py`): inside the `NG` branch,
   after the combined-cycle check — `if "steam turbine" in tech or mover == "ST": return
   "gas_st"`. Prime-mover-based, cited to the EIA-860 Schedule 3 "Prime Mover" field
   (rule 23); the tech-string leg mirrors the CC branch for rows carrying only the
   Technology description. CC steam parts (`CA`, in `_CC_PRIME_MOVERS`) still resolve
   `gas_cc` first, so the miso-126/neiso-83 repair populations are untouched.
2. **`_rows_to_generators`**: `gas_st` joins the `classify_plant` group-branch tuple
   (`("gas_cc", "gas_cc_ccs", "gas_ct", "gas_st")`) so gas-steam rows keep resolving to
   `ST_GAS`/`ST_CHP` and keep being binned. (Without this, all 326 rows would have fallen
   out of the bin synthesis — group `""` — the largest trap in the change.)
3. **`constants.py`**: `HEAT_RATE_BINS["gas_st"] = {"default": 10.3}` (EIA Table 8.2,
   natural-gas steam generators ≈ 10,300 Btu/kWh) and `CO2_RATES["gas_st"] = {"default":
   0.59}` (= 10.3 × the existing 0.057 tCO2/MMBtu back-solve convention,
   `FUEL_CO2_FACTOR_PER_MMBTU["gas_st"]`). `NOX_RATES`/`VOM`/`EFORD`/commitment/startup
   params/`retirement_*_gas_st`/fuel-price map already carried `gas_st` — the fuel was
   downstream-complete everywhere except these two vintage-bin tables.
   `_efficiency_bin` needs no edit (unknown fuels fall to `"default"`).
4. **`_AGGREGATABLE_FUELS`** (`legacy_bins.py`) and the **`run_calibration.py` ERCOT
   backcast exclude literal** gain `gas_st` (§1.1).

No `ScenarioConfig` field, no mechanism, no gate: the solve-affecting residue is the
heat-rate fallback correction itself, which is exactly the accurate-data delta being
adjudicated by the paired controls — gating it off would be keeping the wrong number
behind a flag. (Rule 28: no matrix row due — CI's `mechanism-matrix-guard` checks
`ScenarioConfig` additions, and there are none.)

**Fleet invariance, measured (same-head paired dump, control vs arm, all six ISOs):**
7,020 loader rows: 326 change `fuel_type` `gas_ct→gas_st` and nothing else changes
`plant_group`/`zone`/`pmax`/`pmin` anywhere; `heat_rate` changes on exactly 24 rows (the
fallback rows: MISO 15 / 695 MW, NYISO 6 / 120 MW, NEISO 3 / 9 MW). Synthesized bin
frames: 1,245 rows, identical membership/capacity/tranche-%/fuel; `hr_weighted` changes
on **14 bins**: MISO 11 (Burlington 170 MW, R S Nelson 425 MW ST_CHP, New Ulm, PPG,
+7 sub-10 MW CHP), NEISO 2 (Indian Orchard 3.2 MW, VA Central Heating 6.1 MW), NYISO 1
(RED-Rochester 119.6 MW ST_CHP). CAISO and PJM: zero — every one of their steam rows
carries a unit-level eGRID rate. Tests: `test_fleet` 125, `test_fleet_construction`,
steam-part suites, facade regression, `test_build_capacity_actuals` 28 — all pass.

## 3. Scoring-target + re-emit deltas (commits `cddc9bee`, `1a1f9aed`)

`build_capacity_actuals.py` rerun for all five target ISOs. Row counts and every non-fuel
column unchanged; fuel labels move on: **ERCOT 4** (V H Braunig 1/2, Decker Creek 2,
Garland GEN7), **PJM 14**, **MISO 30**, **NEISO 6**, **NYISO 0** (stamp only).

`ffr7c_exit_decode.py` re-emitted to its registered path (the probe reads `target_fuel`
live from the target CSV — a mechanical re-derivation from the changed committed input).
The two-bar seam collapses: Braunig 1/2 and Decker now carry `gas_st` with the **35.0
gas_st bar**; every margin and every `economically_consistent_*` verdict is unchanged
(FFR-7C pre-adjudicated both bars — bar-invariant). Only derived fields move:
`bar_target_taxonomy` 21.0→35.0, `loss_year_target_lag` onto the gas_st 1-yr lag.

`score_gate_d24_rescore_ffr5d.py` re-emitted (committed-artifact, no solve, the arms'
registered bundles untouched; JSON:
`docs/handoffs/taxonomy-gas-st/score-gate-rescore-2026-08-07.json`):

* **Every band verdict and the D-24 recall identical**: shipped recall n/a (0 of 2
  reachable), unified recall n/a; thermal-GW band FAIL both arms; false-retire PASS
  shipped / FAIL unified — all unchanged.
* **The seam closes at the number**: target `gas_st` `actual_gw` **0.000 → 0.888**
  (`gas_ct` 0.990 → 0.102), so the unified arm's 10.943 GW `gas_st` wave now grades
  against a real actual — `err_frac` 11.32 instead of an uncreditable −1/∞ split. It
  still FAILs, exactly as FFR-7A §4 said it should (the D-21(a) forward-price defect is
  untouched by re-labelling the target).
* **Unreachable-exits diagnostic: same five rows, same reasons, same gating.** What
  changes is the print: the three steam rows carry `gas_st`, and Braunig's margin note
  reads "vs bar 35.0" — nothing about reachability moved, because reachability never
  depended on the label (Braunig: `post_vintage_instrument`; Decker:
  `not_in_fleet_basis`; both bar-invariant).

## 4. Paired controls (Addendum D) — HOLD-PROMOTION posture

Affected-by-solve-input ISOs: **MISO, NYISO, NEISO** (§2). Per the charter, the top two
by impact (MISO ~692 MW of bin capacity re-rated; NYISO 119.6 MW) were run as same-head
control-vs-arm pairs on the ISO's keeper recipe, 2023–2025, one `replay_keeper`
invocation per arm (years sequential within each; ≤2 invocations concurrent; PJM and
MISO never co-run — PJM needed no solve at all).

Harness (committed, reusable for the NEISO tail):

```
# control tree = origin/main src+scripts via git archive, data/ symlinked:
mkdir -p /home/user/market-simulator-control
git archive origin/main src scripts pyproject.toml uv.lock CLAUDE.md \
  | tar -x -C /home/user/market-simulator-control
cd /home/user/market-simulator-control && for d in data results frontend docs tests; do
  ln -s /home/user/market-simulator/$d $d; done

# per ISO (bundle = the keeper's committed bundle):
<venv-python> <tree>/scripts/replay_keeper.py \
  /home/user/market-simulator/results/calibration/<bundle> \
  --out-dir <scratch>/<iso>_tax_<arm> --note "gas_st taxonomy paired <arm>"
```

RESULTS_PLACEHOLDER_PAIRED_CONTROLS

**NEISO is handed off, not run** (charter: run the top two, hand off the rest): its
entire delta is two CHP bins totalling 9.3 MW (Indian Orchard 3.2 MW 11.5→10.3,
VA Central Heating 6.1 MW 9.98→10.3) in an ISO whose keeper bundle is
`results/calibration/neiso83_ca1reclass_B` (keeper `2026-08-05-neiso-83-ca1-reclass`,
years 2023–2025); the harness above applies verbatim with that bundle. Memory note for
the runner: on a ~15 GB box never co-run two large-ISO solves — this session phased the
pairs as (MISO control ∥ NYISO control) then (MISO arm ∥ NYISO arm).

## 5. What was NOT separated / not done

1. **The `gas_st` heat-rate/CO2 constants ride the same commit as the branch** — they are
   the branch's own fallback table, not a separable mechanism; splitting them would have
   left a `gas_st` row with a 0.0 fallback heat rate in between.
2. **The exclusion-set edits ride the same commit** (§1.1) — separable only at the cost
   of an intermediate state that double-counts 10 GW in ERCOT.
3. **FFR-7C's decode JSON was regenerated in place at its registered path** rather than
   forked to a new dated file: `EXIT_DECODE_EVIDENCE` pins that path, the probe is the
   file's single writer, and the .md handoffs remain the historical record of the
   pre-collapse two-bar adjudication.
4. **NOT done:** no keeper promotion, no dashboard registration (no run here is a keeper
   or probe candidate — the paired controls are adjudication evidence, reported here),
   no re-derivation of FFR-6A, no CAISO/PJM/ERCOT solves (byte-identical inputs
   demonstrated instead), no mechanism-matrix cell (no mechanism tested), no
   `ScenarioConfig` change, no touching of `retirement_execution_lag_*` or bars.
5. **The FFR-5D arms' committed bundles and hindcast sidecars are untouched** — the
   re-score table lives here (same convention as FFR-7A §3 / SCORE-GATE §11).
6. **`build_throughput` / `build_exit_throughput` entry-ladder seeds**: consume
   `_map_fuel_type` but derive from CODs in a trailing window — no gas-steam unit has a
   window-recent COD in any ISO, so the seeds are unchanged; noted, not re-derived.

## 6. Rule compliance

* **Rule 12**: solve concurrency ≤2, years sequential inside each invocation; PJM/MISO
  never co-ran (PJM not solved).
* **Rule 13/14**: the reclass is a physical-classification correction on a published
  EIA-860 field, applied consistently across all years; nothing pinned to an outcome.
* **Rule 22**: 2023–2025 solves only; no out-of-training year touched; freeze respected.
* **Rule 23**: `_map_fuel_type` cites the EIA-860 field; the decode/targets re-derived
  because their source taxonomy changed, not because a residual moved.
* **Rule 27**: all pushes as exact on-disk bytes over `git push`; blob hashes of every
  ≥300-line touched file verified against the remote after each push (eia860.py,
  constants.py, run_calibration.py, legacy_bins.py — all MATCH).
* **Rule 28**: no new `ScenarioConfig` field; no matrix duty (checked against
  `check_mechanism_matrix.py` semantics).
