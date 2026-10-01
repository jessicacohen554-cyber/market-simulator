# FINDING miso-213 — THE RULE-19 ZONAL-BASIS LAYERING ON 923-PRICED CELLS: the print path prices 100 % of MISO gas capacity-hours, so the mean-zero basis was fully redundant in a MISO backcast; repaired as one default-off field, single-delta A/B against the keeper itself, EVERY KILL SILENT, all six object gates moving South→North → **PROMOTED, keeper → `2026-09-05-miso-213-layering`**; determination unchanged in class (NOT-YET on C3a-2025 alone, −12.38 → −11.75 %) (2026-09-05)

**Keeper → `2026-09-05-miso-213-layering`** (bundle `results/calibration/miso213_layering_B`,
solved at `cf55ab5`), superseding `2026-09-04-miso-210-clock`. PREREG
`PREREG-miso213-zonal-basis-layering-2026-09-05.md` pushed BLIND at `a1a4a48`; scorer
`scripts/probes/_miso213_ab_gates.py` committed with the arm code before the solve. Phase 0:
`scripts/probes/_miso213_basis_layering_phase0.py` + `_miso213_arm_liveness.py` →
`results/calibration/_miso213_basis_layering.json`. A/B: `_miso213_ab_gates.json`. Attestation:
`scripts/gen_miso213_attestation.py`. Rule 22: 2023–2025 only. Rule 12: three years sequential
in one invocation (thread cap 4, 8 GB swap, the miso-169 recipe; 1 h 05 min wall).

---

## 0. Verdict in one paragraph

Every MISO gas cell's delivered price was set twice for the same reason. The EIA-923 print
path (`gas_plant_monthly_fuel_pricing`, a harness default for every non-ERCOT ISO) prices a
gas cell from the plant's own monthly receipt or, when that month is unreported, from the
class-aware state/zone pool of other plants' receipts; `miso_zonal_gas_basis` then adds the
zone's N3045 state delivered-to-electric-power basis minus the capacity-weighted mean — and
the N3045 series is the state aggregate of those same receipts. Phase 0 measured the print
path pricing **100.0 % of MISO gas capacity-hours in 2023, 2024 and 2025** (own print ~74 %,
pool ~26 %), so the basis contributed a second regional premium on every cell and nothing
else. The repair is one default-off `ScenarioConfig` field that makes the MISO applier skip
the cells the print path wrote; on this keeper that removes the increment from every gas
cell, and in forecast mode (where the print path is off by construction) it changes
nothing. Scored blind against the keeper itself: S-0/S-1/S-2 and K-1..K-6 all silent. The
values moved an order of magnitude more than the prereg predicted — CT_PEAKER −3.3/−2.3/
−3.6 TWh as the Midwest peaker fleet lost the increment's discount and now bids its own
delivered cost, ST_GAS +1.3/+0.7/+0.9 toward actual, coal backfilling, ST_GAS forced share
down in every year — and every one of the six pre-registered object gates moved the way the
prereg said: in the 2025 real South→North binding shoulder hours the South turns from a
0.05 GW net importer into a 0.73 GW exporter (measured 2.9), corridor flow doubles to
710 MW, South gas 15.56 → 16.33 GW against 18.9 measured, Midwest gas −1.05 GW. C3a moves
+0.79/+0.56/+0.64 pp (2023 away from zero, 2024/2025 toward it) and is never the
justification. Promoted on the prereg's own rule and under the owner's standing bar; the
determination class is unchanged, NOT-YET on C3a-2025 alone with C3c ledgered.

## 1. Phase 0 — measured against the PREREG

### L-1 Population (P-1 RIGHT, and stronger than predicted)

Capacity-hour share of MISO gas cells by how the print path priced them, Jun–Jul, pmax-weighted (all-hours in the JSON):

| year | own print | nearby pool | trajectory | South own | South pool | South trajectory |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 75.0 % | 25.0 % | 0.0 % | 75.4 % | 24.6 % | 0.0 % |
| 2024 | 73.8 % | 26.2 % | 0.0 % | 73.9 % | 26.1 % | 0.0 % |
| 2025 | 74.0 % | 26.0 % | 0.0 % | 75.1 % | 24.9 % | 0.0 % |

Every zone, every class: no trajectory cell survives the class-aware state/zone pools (`min_state_plants=2`). The all-hours 2023 inference showed 0.09 % "trajectory" cells; L-5 (post-code, production mask) found those 8,184 cells were print-derived too, hidden from the `F_nobasis ≠ F_noplant` inference by the dual-fuel oil-parity cap. **The production mask covers 100.0 % of gas cells in all three years.** P-1 predicted ≥ 90 % (0.7), South own ≥ 60 % (0.6), trajectory ≤ 10 % (0.7): all RIGHT, at the ceiling.

Zone spread after the capacity-weighted mean (the increment each print-derived cell received, $/MMBtu):

| year | West/Plains | Illinois/Indiana/East | South | mean removed |
|---|---:|---:|---:|---:|
| 2023 | +0.307 | −0.260 | +0.143 | 0.152 |
| 2024 | +0.087 | −0.150 | +0.118 | 0.270 |
| 2025 | −0.642 | −0.039 | +0.287 | 0.057 |

### L-2 Per-plant (923 print − HH daily spot), real S→N binding shoulder hours, capacity-weighted

| year (hours) | South own p10 / p50 / p90 (mean) | South pool p50 | Midwest own p10 / p50 / p90 (mean) | Midwest pool p50 |
|---|---|---:|---|---:|
| 2023 (65) | −0.09 / +0.17 / +0.63 (+0.25) | +0.22 | −0.06 / +0.60 / +3.24 (+1.70) | +0.88 |
| 2024 (190) | −0.20 / +0.22 / +0.56 (+0.55) | +0.35 | −0.17 / +0.38 / +1.54 (+1.12) | +0.46 |
| 2025 (177) | −0.15 / +0.25 / +0.90 (+0.33) | +0.25 | −0.42 / +0.17 / +1.77 (+0.86) | +0.19 |

P-2 South p50 +0.3 to +0.6, p90 ≥ 1.0: WRONG (lower — p50 +0.17/+0.22/+0.25, p90 0.63/0.56/0.90). Midwest p50 +0.5 to +0.9: RIGHT in 2023 only; 2024/2025 lower. The Midwest capacity-weighted MEAN (+1.70/+1.12/+0.86) sits far above its median: the premium is concentrated in a few large-print plants (p90 3.2/1.5/1.8), the concentration miso-212 §5 asked about — the South's is not (p90 ≤ 0.9).

### L-3 Static reach (P-3 South RIGHT; Midwest larger than predicted)

Instrument: `mc_base` (no P1 startup adder — the keeper's unit_hourly sidecars are gitignored and absent), implied heat rate, fixed keeper prices. GW of gas made economic at the fixed zone price, real S→N binding hours:

| year | pop (h) | South base econ / idle≤$20 | arm Δ | all-cell Δ (miso-212 b analogue) | ratio | $/MWh removed (HR) | Midwest Δ (own zone price) |
|---|---|---|---:|---:|---:|---|---:|
| 2025 | shoulder (177) | 15.64 / 3.52 | **+0.842** | +0.842 | 1.00 | 2.59 (9.02) | **−1.595** (West −0.86, Plains −0.55, East −0.11) |
| 2025 | tail (10) | 18.25 / 1.64 | +0.429 | +0.429 | 1.00 | 2.60 (9.06) | −0.458 |
| 2024 | shoulder (190) | 15.66 / 3.64 | +0.448 | +0.448 | 1.00 | 1.06 (8.99) | −0.645 (East −0.46, Indiana −0.24, West +0.12) |
| 2024 | tail (5) | 15.02 / 3.80 | +0.479 | +0.479 | 1.00 | 1.06 (9.01) | −0.570 |
| 2023 | shoulder (65) | 16.35 / 3.95 | +0.580 | +0.580 | 1.00 | 1.29 (9.00) | −1.519 (East −1.06, Indiana −0.68, West +0.26) |
| 2023 | tail (10) | 16.28 / 3.97 | +0.742 | +0.742 | 1.00 | 1.28 (8.98) | −1.863 |

South 2025 shoulder by class: ST_GAS +0.45, CT_PEAKER +0.26, CC_REGULAR +0.07, CC_CHP +0.04; by band: econ +0.59, committed +0.19, peak +0.06. P-3 South 0.6–0.9 GW (0.65): RIGHT (0.84; miso-212's P1-bid figure 0.78). Midwest 0.3–1.0 GW made uneconomic (0.5): WRONG — 1.6 GW in 2025, carried by West/Plains where the removed increment is −0.64 (+$5.8/MWh at 9 HR); 2024 inside (0.65). Ratio arm/all = 1.00 everywhere: **the arm IS the all-cell removal on this keeper.**

### L-4 Genealogy (P-4 RIGHT)

`gas_plant_monthly_fuel_pricing` is not a CLI flag: `pipeline/backcast_config.py` sets it `(iso != "ERCOT")` — a harness default for every non-ERCOT ISO. The gate-2 recipe (`docs/multi-iso/miso-zonal-gate2.md`, keeper `2026-07-02-miso-38-zonal-reserves`) names `--miso-zonal-gas-basis` explicitly and states every other flag is a default, so the print path was ON the day the basis was armed; the layering has been in every MISO keeper since. The basis rows are `N3045<ST>3 / 1.036 − HH` monthly means (`fetch_eia_delivered_gas.py`) — the state aggregate of the same EIA-923 receipts the prints apply per plant: GROSS of the prints, never identified net of them. Record correction: `zonal_gas_basis`'s MISO.js line opened "miso-119 (keeper lineage …)"; miso-119 adjudicated `gas_offer_margin_zonal_anchor` (I). Fixed in this session's shard edit.

### L-5 Arm liveness (post-code, zero-solve, on the keeper's own chain)

With the flag on, every cell the production print path wrote has an arm price equal to `F_nobasis` (share 1.000, max |Δ| 0.0), and there are no unmasked gas cells to keep the increment; capacity-weighted |increment| removed 0.218 / 0.126 / 0.240 $/MMBtu (2023 / 2024 / 2025). **On this keeper the arm is behaviourally `miso_zonal_gas_basis=False` in backcast mode** — the honest headline the PREREG §5 stated in advance. The mechanism is not deleted: a trajectory cell (a partially reporting fleet, or every cell in forecast mode) still receives the increment.

### Decision rule

Neither PREREG §4 kill holds — the print path excludes nothing (L-1), the basis is gross of the prints (L-4). The arm was built and solved.

## 2. The arm (rule 19, one field, zero free parameters)

`apply_plant_monthly_fuel_prices` now returns the `(n_gen, T)` boolean mask of the cells it
wrote (own print or pool; all-False when it is a no-op). Both fuel chains —
`resolve_fuel_prices(apply_monthly=True)` and `run_calibration.run_year` — hand it to
`apply_miso_zonal_gas_basis`, which under `ScenarioConfig.miso_zonal_gas_basis_skip_923_priced`
(default False, `_CACHE_KEY_OPTIONAL_FIELDS`, TIER_TAGS 3) passes it as `skip_cells` to the
shared mean-zero core. Masked cells are left byte-untouched (no floor either); unmasked cells
receive exactly the spread they receive with the flag off, because the capacity-weighted mean
is still taken over ALL gas rows. Flag off ⇒ byte-identical to HEAD; the pinned default
cache key is unchanged. Seven unit tests (`tests/unit/data/test_miso213_basis_skip_923.py`)
pin the mask, the skip, the flag-off no-op and the seam. The solve log reads "100.0 % of gas
cells skipped as print-derived" in every year.

## 3. The A/B — arm `miso213_layering_B` vs the keeper bundle itself

| gate | result |
|---|---|
| **S-0** control integrity | INHERITED — the control is the committed keeper bundle (miso-210 S-0: 9 sidecars, `max_abs_diff` 0.0), not re-solved |
| **S-1** single delta | **PASS, restated** (§6): zero diffs over the 784 fields present in both records; five fields new on main since the keeper solved sit at their defaults; `miso_zonal_gas_basis_skip_923_priced` absent → True; `a9b67b53` vs `cf55ab5` |
| **S-2** liveness | PASS — L-5: every production-masked cell equals `F_nobasis`, no unmasked gas cell exists |
| **K-1** C1 band ±8.00 | **PASS** — no band exit; largest class-year move **CT_PEAKER-2025 −3.62 TWh**; ST_GAS-2024 −7.486 → −6.803, CC_REGULAR-2024 +6.940 → +7.419, ST_GAS-2025 −6.686 → −5.748 |
| **K-2** C3b | PASS — 0.081 / 0.111 / 0.182 → 0.080 / 0.109 / 0.177 |
| **K-3** D-4 | PASS — 57 → 56 rows, zero new failures, one CLEARED: (2023, unit-conduct, reliability_floor × ST_GAS, 1122), the cell the miso-201 kill had fired on |
| **K-4** D-1 | PASS — ST_GAS profile_r 0.941/0.956/0.977 → 0.951/0.957/0.982; cv_ratio 1.76/1.25/1.49 → 1.71/1.14/1.53 |
| **K-5** status flips | PASS — status map IDENTICAL once the arm is attested (§6) |
| **K-6** DOF | PASS — 41 entries / 2 residual on both legs; no new entry |

**C1, arm − control (TWh, 2023 / 2024 / 2025), reported at full magnitude:**

| class | Δ 2023 | Δ 2024 | Δ 2025 | arm face vs actual 2025 |
|---|---:|---:|---:|---|
| CT_PEAKER | **−3.33** | **−2.32** | **−3.62** | 16.10 vs 19.29 (control 19.71) |
| ST_GAS | **+1.34** | +0.68 | +0.94 | 9.82 vs 15.57 (control 8.88) |
| CC_REGULAR | +0.63 | +0.48 | −0.25 | 135.54 vs 137.96 |
| CC_CHP | −1.17 | −0.56 | +0.36 | 19.67 vs 17.75 |
| COAL_PRB | +0.85 | +0.54 | +0.70 | 141.65 vs 145.86 |
| COAL_BIT | +0.35 | 0.00 | +0.59 | 58.73 vs 60.18 |
| gas classes | −2.43 | −1.69 | −2.61 | |

The PREREG P-5 said gas classes < 0.3 TWh/yr, ST_GAS +0.1..+0.5, CC_REGULAR −0.1..−0.5: WRONG
on magnitude everywhere. The mechanism is plain in hindsight: the Illinois/Indiana/East
zones (16.7 + 7.1 + 3.9 GW of gas) had been receiving a −0.26 / −0.15 / −0.04 $/MMBtu
discount and West/Plains +0.31 / +0.09 / −0.64; removing them re-prices the Midwest CT fleet
at its own receipts and the LP swaps 2–4 TWh of peaker energy for South steam and coal.
CT_PEAKER moves AWAY from actual in 2023 and 2025 — rule 14: the plant's own delivered cost
is the accurate input, and the class's own conduct is the discovered question (§7).

**C8** ST_GAS forced share 0.155 / 0.153 / 0.271 → **0.138 / 0.138 / 0.212** — less forcing in
every year, with the ST_GAS D-1 profile unchanged.

**C3a, at full magnitude, never the justification:**

| year | control | arm | Δ pp | PREREG band | inside |
|---|---:|---:|---:|---|---|
| 2023 | +0.122 | **+0.913** | **+0.79** | [−0.5, −0.05] | NO — sign wrong, AWAY from zero |
| 2024 | −4.396 | **−3.839** | **+0.56** | [−0.5, −0.05] | NO — sign wrong |
| 2025 | −12.385 | **−11.747** | **+0.64** | [+0.2, +1.5] | yes |

The prereg's 2023/2024 sign rested on the West/Plains increment being positive those years
(removing it lowers West gas); it was, and West gas did fall — but the Illinois/Indiana/East
discount (−0.26 / −0.15) is on 27.7 GW of gas against West/Plains' 10.6 GW, and removing a
discount from the larger fleet raised the load-weighted price. The prereg weighed the
increments, not the capacity under them. C3c 3 / 7 / 1 → 3 / 7 / 0 tail hours (ledgered).

## 4. The object — six gates, all in the pre-registered direction

2025 real S→N RDT-binding SHOULDER hours (177 h; control from the committed miso-211 record,
arm from its fresh `network_` / `unit_hourly_` sidecars through the miso-211 readers):

| gate | control | arm | PREREG band | measured | verdict |
|---|---:|---:|---|---:|---|
| O-1 South boundary net (into-South, GW) | +0.05 | **−0.73** | −0.1 .. −0.6 | −2.86 | direction right, OVERSHOOT |
| O-2 S→N corridor flow (MW) | 357 | **710** | 450 .. 1000 | at the 2,500 limit half the hours | inside |
| O-3 S→N free-tier binding share | 2.8 % | **6.8 %** | 4 .. 12 % | ~50 % | inside |
| O-4 Indiana − South spread ($/MWh) | −0.16 | **+0.16** | +0.3 .. +3 | +58.3 | direction right, SHORT |
| O-5 South gas (GW) | 15.56 | **16.33** | 15.9 .. 16.4 | 18.90 | inside |
| O-6 Midwest gas Δ (GW) | — | **−1.05** | −0.2 .. −0.8 | — | direction right, OVERSHOOT |

Other populations: 2025 tail (10 h) net −0.25 → −0.72, flow 556 → 945, South gas 17.68 →
18.13; 2024 shoulder (190 h) net −0.38 → −0.72, flow 424 → 555, share 6.3 → 9.5 %, South gas
15.83 → 16.15, Midwest −0.49; 2023 shoulder (65 h) net −1.10 → −1.59, flow 846 → 1,193, share
12.3 → 24.6 %, South gas 16.90 → 17.40, Midwest −0.83. The static L-3 reach (0.84 GW South,
−1.6 GW Midwest) was a ceiling at fixed prices; the LP delivered 0.77 GW of South gas and
−1.05 GW of Midwest gas — the response is most of the ceiling. What it does not deliver is
PRICE separation: the Indiana−South spread opens $0.3 against a measured $58, because the
corridor's free tier binds in 6.8 % of the hours, not half of them. The South under-export
(miso-211's D-3 object) closes 0.78 of its 2.9 GW; the rest is still generation-side.

## 5. My prior, scored against interest

P-1 RIGHT (at the ceiling, stronger than predicted). P-2 WRONG: the South print premium is
smaller than predicted and the Midwest's is concentrated in a few large-print plants. P-3
South RIGHT (0.84 vs 0.6–0.9); Midwest WRONG-high (1.6 vs 0.3–1.0). P-4 RIGHT. P-5 WRONG by an
order of magnitude on every class move and WRONG on the C3a sign in 2023 and 2024 (right in
2025). P-6 RIGHT (every K silent; K-6 41 → 41). Object gates: 3 inside, 2 overshoot, 1 short —
all six in the predicted direction.

## 6. Instrument corrections, disclosed

1. **Phase-0 print-cell inference.** `F_nobasis ≠ F_noplant` is blind where the dual-fuel
   oil-parity cap equalises the two toggles; it called 8,184 2023 cells (0.06 %) trajectory
   cells that the production mask shows were prints in a negative-spread zone capped at oil.
   L-5 was re-based on the production mask (`apply_plant_monthly_fuel_prices` replayed on the
   pre-overlay array) before the solve; the scorer's S-2 reads that block. Effect on the
   result: the population is 100.0 %, not 99.9 %, in 2023.
2. **S-1 restated after the first scoring pass.** The miso-210 form (set-union diff of the
   two `scenario_config` blocks) read VOID on `adequacy_accounting_ratio_dated_net`,
   `caiso_citygate_spot_coverage`, `ccs_retrofit_capex_co2_scaling`,
   `nyiso_requirement_forecast_peak`, `nyiso_requirement_vintage_factors` — fields main added
   after the keeper solved on 2026-09-04, absent from its record and at their dataclass
   defaults in the arm. Restated: zero diffs over fields present in both records, every new
   field at default except the tested one. No kill threshold or object band moved.
3. **K-5 / C3c on the first pass.** Before `gen_miso213_attestation.py` ran, the arm read
   governance UNATTESTED and C3c CAVEAT → FAIL (the ledger lives in the attestation) — the
   miso-200 vacuous trap in its inverse form; both clear with the attestation in place.
4. **L-3 instrument.** Static reach on `mc_base` (no P1 startup adder), because the keeper's
   `unit_hourly` sidecars are gitignored; the miso-212 all-cell number was recomputed on the
   same instrument so the ratio (1.00) is exact even though the level (0.84 vs miso-212's
   0.78 on the P1 bid) is not.

## 7. What this licenses, and what it hands on

* **Licensed and PROMOTED:** `miso_zonal_gas_basis_skip_923_priced` (K, MISO). The
  `zonal_gas_basis` cell stays K on its forward story and code path, with its backcast effect
  now zero on this recipe — stated in the cell. Rule 25: the PJM and CAISO mean-zero siblings
  share the core and the print path, so the same layering exists there in kind; each enters
  its own lane as U.
* **Named for miso-214 (queue head): the Midwest CT_PEAKER fleet at its own delivered
  cost.** CT_PEAKER is now the largest C1 mover on the board, 3.2 TWh under actual in 2025
  (SKIPPED — preliminary 923 vintage) and 5.1 TWh under in 2023 (PASS, inside ±8). Its fuel is
  now the accurate input; what is left is the class's own offer/commitment conduct (the
  miso-134/179/180 family adjudicated LEVEL/SPREAD on the whole fleet, not the peaker class
  at its post-repair cost). Phase 0 first: which peakers ran in the market (CAMPD) and did
  not run in the arm, and at what implied margin.
* **Still open, not this lane's lever:** the South price separation (O-4: +$0.16 vs +$58)
  — dispatch and flow moved, price did not, because the free tier binds 6.8 % of the hours;
  the miso-211 D-3 object stands. The average-vs-marginal delivered-cost convention (miso-212
  §8) is untouched and OWNER-COURT.
* **Not chartered:** re-tuning anything to the C3a moves; re-opening `gas_hub_basis_overlay`
  (R), the offer level/spread family (R/I), `miso_rdt_measured_limit` (R).

## 8. Reported against interest

1. The arm is, on this keeper, a basis-off backcast. The prereg said so in advance and the
   repair is right at any magnitude, but a reader should not mistake it for added structure:
   it removes a double-counted input.
2. C3a-2023 moved AWAY from zero (+0.12 → +0.91) and CT_PEAKER moved AWAY from actual in
   two of three years. Both are reported, neither is argued; rule 14 keeps the accurate
   input.
3. The PREREG's magnitude predictions were wrong by an order of magnitude because they
   weighed the increments and not the capacity under them; the scorer's kills are
   band-based, so no kill depended on those predictions.
4. The object gates overshoot on the dispatch/flow side and fall short on price; "all six
   in the pre-registered direction" is true and is the weaker of the two possible claims.

## 9. Governance

Rule 15: registered `2026-09-05-miso-213-layering` (payload over `git push`; retention
pruned `2026-08-30-miso-191-control`), `legitimacy_diagnostics.json` and
`calibration_attestation.json` in the bundle; `network_<year>.parquet` committed with
`git add -f` (the lane interrogates the corridor); `unit_hourly` (79 MB/yr) not committed.
Rule 28(b)/(c): base row + six cells for the new field; `zonal_gas_basis` evidence appended
and its genealogy corrected; keeper/gates stamps; §5.4 header re-keyed + queue stamp.
Rule 25: MISO's verdict only. Rule 22: 2023–2025. Rule 23: no derive script touched. Rule
24: the flag is a `ScenarioConfig` field recorded in `run_config.json`. Rule 27: every
≥300-line file edited locally and blob-verified after each push. Rule 13: the prints and
the basis are both measured inputs; the arm changes which cells receive an existing one.
`keepers/MISO.json` → `2026-09-05-miso-213-layering`, `build_status.py --iso MISO`,
`audit_keepers.py --iso MISO` PASS 0/0.

Next shorthand: **miso-214**.
