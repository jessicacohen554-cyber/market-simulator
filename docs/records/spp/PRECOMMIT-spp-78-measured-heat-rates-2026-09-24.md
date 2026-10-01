# PRECOMMIT — SPP-78: arm SPP's measured CAMPD heat rates (existing fields), all seven years

**Pushed before any artifact is derived or any new number is read.** Base (pinned) `06d7de402b0b28f05361a3434a7d04e10fcb9fe8`.
Keeper `2026-09-22-hydro-5-spp-floor` (`hydro5_spp_floor_span`, 2023–2025, CALIBRATED, one ledgered C3c).
Rung `2026-09-22-hydro-5-spp-rung` (`hydro5_spp_floor_rung`, 2019–2022, NOT-YET), stamped to the keeper.
Predecessor: `RESULT-spp-76-crossover-heat-rates-2026-09-24.md` §2–§5 (the only prior numbers this doc uses).

## 0. Why this lane exists

**Rule 14 `[R-ACCURATE]`, not a gate.** SPP-76 measured the model's eGRID heat rates against CAMPD:
CC_REGULAR −2.9 %, ST_GAS −2.8 %, COAL −1.7 % (capacity-weighted, net, 2023–25; the 2019–22 window
agrees to ≤ 1.1 pp), with the largest per-plant errors on eGRID **blended-plant rows** (GRDA 165: CC
8.02 vs 6.67, coal 8.02 vs 12.35; Hawthorn 2079: CC 11.79 vs 8.38). Measured data is available, so it
is preferred. This lane is **not** the crossover repair (SPP-76 closed that: ΔCOAL_PRB ≤ 0.1 TWh in
2021/22). It may regress gates and still be promotable (rule 1).

## 1. The input (fixed now)

- **Fields** (confirmed in `ScenarioConfig`, all default `False`, all existing — no new field, no
  rule-28(c) PR): `measured_cc_heat_rates`, `measured_st_heat_rates`, `measured_coal_heat_rates`.
  Armed **together**, all three, in every year.
- **Artifacts**: `scripts/data/derive_campd_{cc,gas_st,coal}_heat_rates.py --iso SPP`, **run
  unmodified at their own default construction** — `--years 2023 2024 2025` pooled, operating-hour
  window (`opTime ≥ 0.99`), the CC boundary guard and each derive's physical band kept, output to the
  loader's own path `data/raw/_processed-legacy/campd_{cc,st,coal}_heat_rates_SPP.csv` (+ `_units`).
  Only `flag == "ok"` rows apply (loader behaviour).
- **Why the default window and not per-year or 2019–22, decided now:** the field reads **one**
  per-ISO artifact for every year; the derive's default is the construction every other ISO armed
  (SOCO / NWPP); choosing a window per result is forbidden (rule 1(c) spirit, rule 23). SPP-76 already
  showed the 2019–22 window agrees to ≤ 1.1 pp, so the choice is not load-bearing. **Stated cost:** a
  plant that retired before 2023 has no 2023–25 CAMPD hours and stays on eGRID in 2019–22 — reported
  as covered MW per year, not repaired.
- **Rule 13 forward test:** a machine's operating heat rate is a physical characteristic. For a
  forecast year Y the same derive runs over the trailing three CAMPD vintages available at the run's
  information cutoff and responds to retrofits / retirements / new units. It is a multi-year
  history input, **not** a same-year overlay, and nothing is fitted (rule 21: zero free parameters —
  every number is Σ heatInput / Σ grossLoad over the plant's own hours).
- **Rule 25:** SPP-only artifact; a strict no-op for every other ISO (loader returns `{}` without it).

## 2. Rule 19 enumeration — what else sets these rows' heat rates

Order in `eia860._rows_to_generators` (read at base):
1. eGRID plant rate (`PLHTRT`) — **the value replaced**.
2. `_apply_egrid_boundary_hr_repairs` (unconditional; Riverside-class double counts) — precedes, unaffected.
3. `_apply_simple_cycle_hr_floor` (SPP-49, GT/IC only) — cannot reach CC_REGULAR / ST_GAS / COAL rows.
4. `egrid_family_heat_rates` — **OFF** in keeper and rung (`run_config_*.json`). Not armed here.
5. `egrid_identity_heat_rates`, `egrid_steam_collapse_heat_rates`, `measured_chp_heat_rates` — OFF; CHP
   is excluded by class from all three fields.
6. **Measured fields (this lane)** — class-scoped per row: CC_REGULAR ← cc, ST_GAS ← st, COAL ← coal.
   Each **replaces** the row's base HR; nothing stacks.
7. Downstream, unchanged and multiplicative on the base: tranche physics (`cc_committed_hr_mult` 1.23,
   `cc_econ_hr_mult` 0.96, `cc_peak_hr_penalty` 1.15, `gas_st_*` 1.32 / 0.97, coal tranches) — measured
   physics (`phys_*`), not touched — and the **`offer_curve_by_group` band multiplier 0.93** (rule 1
   authorized channel). **The 0.93 is held exactly as declared.** It was set ex ante on eGRID heat
   rates; re-tuning it after arming would be the per-criterion selection rule 1(c) forbids. If the
   level moves, it moves, and is reported.
- Blended-plant handling: there is no separate SPP blended-plant repair to reconcile; the class-scoped
  measured fields are what separates GRDA 165 / Hawthorn 2079's coal and CC rows.
- Rule 21: `build_dof_ledger.py --iso SPP --check <composite>` run on the arm composite; the three
  fields add **zero** free parameters (measured inputs, identification = CAMPD).

## 3. Controls — why this lane solves them (rule 29(b) exception, stated before solving)

Rule 29(b) defaults to the keeper bundle as control. Here the brief requires per-year control solves,
and rule 36(f) supplies the reason: the keeper and rung were solved with cross-year warm start ON, so
their committed numbers carry an unmeasured basis artifact that an isolated per-year arm does not.
Differencing arm vs. an isolated per-year control at the **same SHA** removes it. Control deltas vs.
the committed keeper/rung are reported as the rule-36 drift, not attributed to the arm.

## 4. Solve plan (rules 32 / 34 / 36)

Seven shards, one per year 2019–2025, all at ONE pinned 40-char SHA (the commit carrying the three SPP
artifacts). Each shard runs, sequentially, from its own bundle's recipe (rung for 2019–22, keeper for
2023–25):
- control: `replay_keeper.py <bundle> --years <y> --out-dir results/calibration/spp78_ctl_<y>`
- arm: same + `--set measured_cc_heat_rates=true --set measured_st_heat_rates=true --set measured_coal_heat_rates=true`, out-dir `spp78_hr_<y>`

Hard stops: `git rev-parse HEAD` = pinned SHA; gas price 2019 2.57 / 2020 2.03 / 2021 3.72 / 2022 6.45 /
2023 2.54 / 2024 2.19 / 2025 3.52; control recipe == bundle recipe; arm differs from control by
**exactly** the three fields False → True; artifacts' sha256 match the pinned commit. Full bundles
(incl. `dispatch/<y>_P1.parquet`) pushed via `.gitignore` negation + plain `git add`.

## 5. Pre-registered predictions (from SPP-76's merit proxy; re-run at the pinned SHA before shards)

| # | prediction |
|---|---|
| P1 | Derived SPP artifacts reproduce SPP-76 §2 class means to ±0.3 pp (CC −2.9, ST −2.8, coal −1.7 %). |
| P2 | Zero-LP proxy ΔCOAL_PRB (arm − model) within ±0.3 TWh of SPP-76 §3 every year (+1.00 / +0.61 / −0.09 / −0.06 / +0.38 / +0.21 / +0.53). |
| P3 | Solved Δ (arm − control) COAL_PRB: same sign as proxy in 2019/2020/2023/2025, \|Δ\| ≤ 1.5 TWh every year. |
| P4 | **C1 COAL_PRB 2022 stays out of band** (+9.60 → ≥ +8.5 TWh vs ±8.00). |
| P5 | Solved Δ CC_REGULAR ≥ −0.5 TWh in every year (CC gets cheaper; does not lose energy). |
| P6 | **C3a 2020 falls** (arm − control < 0), by 0.5–4 pp; demand-weighted mean price falls in ≥ 6 of 7 years. |
| P7 | C4 gas 2022 NRMSE moves < 0.02 (stays failing near 0.32). |
| P8 | C3b 2020/21/22 move < 0.02 each. |
| P9 | D-4 / C8 clean: no new forced share, no new off-window binding (the fields touch no floor). |
| P10 | Keeper span (2023–25) determination unchanged or one gate moves; any regression reported at full magnitude. |

## 6. Promotion rule (fixed now)

**Recommend PROMOTE** iff all hold: (a) all three fields arm cleanly — the arm differs from the control
by exactly the three flags, every covered row's base HR equals its artifact value (zero-LP fleet
check), no `flag != ok` plant applied; (b) C8 / D-4 clean and no new forced share (rule 20); (c)
`audit_keepers --iso SPP` 0 failures after re-stamp; (d) DOF ledger `--check` passes with zero new free
parameters. **Gate outcomes are not a criterion in either direction** (rule 1): a regression (e.g. C3a
2023–25 moving low, a C1 row crossing its band) is reported with its owning object and does not block
the recommendation; an improvement does not earn it. A span that reads NOT-YET where the keeper read
CALIBRATED is reported as such and put to the owner — the lane recommends, the owner rules (rule 31).

## 7. Failing rung rows and their owning objects (carried from SPP-76 §6, re-scored after)

C1 COAL_PRB 2022 +9.60 (crossover fuel-price elasticity / DA commitment physics, SPP-77) · C4 gas 2022
0.321 (same + Jan-2022 F923 outlier, routed) · C3b 2020/21/22 (price body/shape, SPP-74; gas low side,
SPP-75) · C3a 2020 +15.5 % (price level; this lane moves it the right way, P6).

## 8. Standing duties

Matrix cells `measured_{cc,coal,st}_heat_rates` in `mechanism-matrix/SPP.js` updated whatever the
outcome (rule 28); nothing deleted (rule 31); shards archived after bytes are verified (rule 33); if
promoted, rule 35 order: year union {2019..2025} recorded here → register → promote → re-stamp rung →
`audit_keepers` E1/E13 → prune → re-key `calibration-complete.json` → keeper auditor.
