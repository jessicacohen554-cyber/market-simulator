# PRECOMMIT — R-CAISO-5: CC outage-derate basis (X) ± Pastoria CO2 (E); 2019–21 intertie source (2026-09-26)

Written before any shard. The parent spends zero LP (rule 32(a)). Keeper: `2026-09-26-caiso-r4-intertie-dam`
(bundle `rcaiso4_D_span`, pin `9a1980bc`), CALIBRATED, thin margin C4 2025 gas NRMSE 0.299 (≤ 0.30).

## 1. Phase 0 — what carries the C4 midday gap (zero LP, committed artifacts)

Sources: the keeper payload (`runs/2026-09-26-caiso-r4-intertie-dam.js`, per-plant hourly model MW and the
EIA-930 hourly comparisons) and the CEMS bench (`bench/CAISO/<Y>.json.gz`). Hour index = the payload clock.

**Plant view, 2025, h8–h16 (MW, model − CEMS, summed over 85 gas plants):**

- model off while CEMS on: **−1,116**; both on, model loaded lower: **−521**; model on while CEMS off: **+735**.
- When on at midday, model CCs sit at 0.27–0.43 of nameplate against CEMS 0.49–0.68 (Delta, Gateway, Colusa,
  Pastoria, Metcalf).
- So both commitment and loading are low at midday. That is the symptom. §1.2 is the cause.

**System view — what displaces midday gas (model − EIA-930, hod means, MW):**

| | h8–16 2022 | 2023 | 2024 | 2025 | h18–23 2025 |
|---|--:|--:|--:|--:|--:|
| net imports | +1,557 | +2,035 | +1,974 | **+1,834** | **−659** |
| solar | +598 | +583 | +479 | **+747** | +48 |
| hydro | −101 | −81 | −56 | −114 | +17 |

- The import over-delivery at midday appears in **every month of every year** (monthly h8–16 means +600 to
  +2,900 MW). Annual imports are +3.2 / +5.1 / +7.2 / +4.1 TWh over 930 in 2022–25.
- The solar excess is concentrated Feb–May (+0.7 to +1.8 GW), i.e. curtailment the zonal model does not take.
  caiso-216 measured 78–92 % of reported curtailment as LOCAL (sub-zonal), a declared model-class limit.
- **Evening overshoot is not storage timing.** 2025 storage net discharge over h18–23: model 3,910 MW, actual
  3,909 MW. Within the window, discharge is ~1 h late (h17–18 under, h21–22 over), which nets to zero.
  The evening gas excess (+865 MW) matches the evening import shortfall (−659 MW).

**Verdict on the shape:** the C4 residual is the import diurnal shape, net of a firm block already shaped by
measured data (caiso-73). No measured-input defect was found in it. The export route is adjudicated R/G
(`caiso_p1_export_sink_seam`, `caiso_corridor_export_path`, `caiso_node_export_constraint`). caiso-284 already
records the midday bridge-coverage object. **No lever is taken on the import shape.**

## 2. The measured-input defect found: phantom capacity in full-plant CC outages

- **Moss Landing (260) 2025:** CEMS shows the whole plant dark on **89 days**, including Jan 17–Feb 11 (the
  battery-fire window) and Dec 13–31. The outage extract (`campd-unit-outages-CAISO.csv`) has **all four CEMS
  units (1A/2A/3A/4A) out** in both windows.
- The keeper still keeps **207 MW available** in those windows and dispatches it: 154 / 192 MW mean.
- **Cause.** The keeper's CC derate (`unit_outage_lp_capacity_basis`, K since caiso-184) divides the extract's
  unit MW by the fleet's raised nameplate denominator:
  - numerator: 262 + 262 + 350 + 267 = **1,141 MW**, `observed_peak` / `eia_digits` capacity sources;
  - denominator: **1,398 MW**;
  - so four-of-four units out removes 81.6 %, and the bottom tranche stays up.
- caiso-184 verified the two bases agree **only for EIA-sourced rows**. Moss Landing's rows are not EIA-sourced.
- **The registered repair already exists:** `unit_outage_extract_basis_share` (nyiso-196, same defect at Cricket
  Valley). It takes the removed share on the extract's own basis, so all units out means 100 % out. It is
  **mutually exclusive** with `unit_outage_lp_capacity_basis`, and the code raises if both are set, so the arm
  REPLACES the incumbent construction (rule 19). Its CAISO cell is **U**, and the census below is the one that
  cell names.

**Census (zero LP; `fleet_only` rebuild, keeper recipe at HEAD; X = extract basis, K = keeper).** The rebuild
checks Moss Landing directly: under X its capacity is **0 MW** in both all-units-out windows; under K it is
**207 MW**.

| year | CC bins moved | avail-capacity Δ (TWh-cap) | removed / added | keeper CC_REGULAR energy above the X cap (TWh, static) |
|---|--:|--:|---|--:|
| 2022 | 20 | −0.620 | −0.990 / +0.370 | ~0.37 |
| 2023 | 20 | −0.538 | −0.929 / +0.391 | ~0.35 |
| 2024 | 18 | −1.303 | −1.534 / +0.231 | ~0.43 |
| 2025 | 20 | −2.589 | −2.933 / +0.344 | ~0.96 |

- The largest removals are Moss Landing, Desert Star, Otay Mesa, Blythe and Sunrise. In 2025 the model
  over-dispatches Moss Landing by +1.49 TWh and Otay Mesa by +0.80.
- Mountainview, Glenarm and King City gain availability, because their extract basis exceeds the LP denominator.
  That is the same construction and is not selected.
- `min_gen` moves by |Δ| 0.04–0.10 TWh.
- The static "energy above cap" excludes CC_CHP: the payload adds the CHP host back to Los Medanos, which shows as
  0.4–0.5 TWh there.

## 3. G-DRIFT (rule 29(b)), zero LP

The keeper's `fleet_only` rebuild was run at pin `9a1980bc` (sparse worktree, shared `data/`) and at HEAD
`c87cdc04`, 2022–2025. **All 27 LP-visible arrays are byte-identical in every year** (fleet arrays, `mc_base`,
wind/solar CF and cap and mc, storage, demand).

The post-`fleet_only` hunks in `scripts/run_calibration.py` are the coal-budget refactor (`resolve_coal_budget_arms`,
neiso-117). They are INERT for CAISO: MISO/NEISO-gated, and the keeper arms no coal budget. The `runner.py` hunk
is `set_eia860_standby_admission`, which is INERT: `admit_standby_units` defaults off and is absent from the recipe.
**Form 4 is valid; the keeper bundle is the control.**

## 4. Arms and shards (rules 32, 34, 36)

- **Recipe:** `scripts/replay_keeper.py results/calibration/rcaiso4_D_span --years <Y>`.
- **X:** `--set unit_outage_extract_basis_share=true --set unit_outage_lp_capacity_basis=false`.
- **XE:** X plus `--set cc_eia923_identity_emission_basis=true`.

| shard | years | out-dir |
|---|---|---|
| r-caiso-5-X-{Y} | 2022, 2023, 2024, 2025 | `results/calibration/rcaiso5_X_{Y}` |
| r-caiso-5-XE-{Y} | 2023, 2024, 2025 | `results/calibration/rcaiso5_XE_{Y}` |

- **XE span** = X-2022 + XE-2023..2025. E is inert in 2022 (no v2 rows; R-CAISO-4 G-IDENT), and the XE-2022
  fleet equals X-2022 (verified: identical availability and `min_gen`).
- **Attribution:** X = X − keeper per year; E = XE − X for 2023–25.
- **2019–2021 deliberately deferred (rule 34(c) names it).** They are reported-only folded years, dominated by the
  import fallback (§6). If the owner rules to promote, three X (or XE) legs are launched then, at about 20 min
  each in parallel. The outgoing folded run is not pruned until they exist (rule 35(c)).

## 5. Stated before the solve

**Direction, not a gate.**

- X lowers CC_REGULAR in all years, most in 2025, where Moss Landing and Otay Mesa are over-dispatched.
  Replacement comes from other CCs and imports.
- **The C4 direction is not predicted.** Removed phantom is roughly flat across the day, while the C4 error is
  diurnal (§1). C4 2025 can move either way.
- XE behaves as in R-CAISO-4: Pastoria up, High Desert and other SP15 CC down.

**Stop gates (they can kill an arm; none promotes one):**

- **G-IDENT.** Each leg's `run_config.json` differs from the keeper's only in the declared flags.
- **G-LIVE.** Moss Landing's model output is 0 in Jan 18–Feb 10 2025 and Dec 14–30 2025 (X and XE, 2025 leg).
- **G-FOOT.** Leg annual CC_REGULAR TWh falls relative to the keeper in 2025.

**Not a keeper if:**

- a load-bearing criterion (C1/C2/C3a/C3b) flips PASS → FAIL;
- C6 or C8 fails;
- a second ledgered caveat appears;
- the determination is NOT-YET. A NOT-YET promotion withdraws the complete marker, so that is the owner's trade
  and never taken in-session.

Offer-curve multipliers are unchanged, the DOF ledger stays 9/6, and there is no `authorized_price_tuning` block.
The flag is not resized or selected against any result.

## 6. Object 2 — 2019–21 intertie prices: the STOP stands (zero LP)

- **OASIS, re-probed 2026-09-26.**
  - SingleZip PRC_LMP DAM (MALIN_5_N101, PALOVRDE_ASR-APND, TH_SP15), PRC_INTVL_LMP RTM and GroupZip
    DAM_LMP_GRP all return "No data" for 2019-06-01 and 2020-06-01. GroupZip 2020-11-15 also returns "No data".
  - GroupZip 2021-09-01 is served. SingleZip retention starts at about 2023-06.
- **EIA/ICE daily on-peak indices (2019–21 download).**
  - They carry Mid-C, Palo Verde, SP15 and NP15 on-peak only (no COB, no off-peak), which covers **55.9 % of
    hours**, below the loader's 75 % bound.
  - Overlap against the committed node series (2022, lag 0): r 0.82 MALIN / 0.83 PALOVRDE.
  - The ICE/node level ratio is 1.02–1.52 annually and 0.55–2.97 monthly, and it drifts.
  - An hourly construction would need a hub basis plus an off-peak/intra-day shape, and both would be fitted to
    the node series. **Inadmissible** under rules 13/14; ICE is a diagnostic at most.
- **EIA-930** carries no prices. **FERC EQR** is bilateral transactions, not an index; not pursued.
- **Firm-base block:** `IMPORT_TRANCHES_BY_YEAR["CAISO"]` has 2022–2025 only. 2019–21 silently fall back to the
  static ladder (1,566 / 1,805 MW, i.e. the 2025 values), the same defect caiso-262 fixed for 2022. The repair is
  zero-parameter (DMM annual report `Imports` RA row × MIC north share), but the 2019–21 DMM rows are not intaken.
  Routed as a successor data intake; it cannot close a 14–25 TWh shortfall alone.
- **`caiso_per_year_import_caps`:** `capacity-deliverability/caiso/caiso.csv` has LA Basin / SD-IV requirement
  rows for 2019–22 but no area `peak_load` rows. The caps are a no-op for 2019–22 and the links keep the static
  TTC.

## 7. Routed, report only

- **`benchmark_semantics.gas_foldin_deflation`** (PR #6735): see the RESULT; no flip in this session.
- **Stale comments** about the Jan–Feb 2023 hours being absent from the RT benchmark (`envelopes.py`,
  `calibration_verdict.py`): see the RESULT.
