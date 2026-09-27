# PRECOMMIT — PJM-NEXT-4 card 1: the 2019 mid-curve table from PJM's own 2019 offers

Session PJM-NEXT-4, 2026-09-26. Keeper `2026-09-26-pjm-next-3-unitfuel` (bundle `results/calibration/pjmnext3_c2_span`,
2019–2025, solved at `54849585`). Written and pushed **before any solve**. The arm changes one data artifact and no
code on the solve path: no flag, zero free parameters, no `offer_curve_by_group` multiplier touched.

## 1. The handoff premise was stale for 2020–2022 (zero LP)

The handoff (from `FINDING-pjm-next-3-phase0-cards-1-3-4` card 3) said 2019–2022 read the POOLED mid-curve ladder.
At HEAD that is true **only for 2019**. The committed surface `pjm_offer_midcurve_condbinned.json` has carried
year-own 2020–2022 tables since pjm-h9c (2026-09-16, 72 month-files, 2020–2025). The loader
(`offer_surfaces.py:1231`) reads `years[str(year)]` and falls back to `pooled` only for a missing year.

So the COAL_BIT 2020–2022 over-run (+10.5 / +20.7 / +8.1 TWh) **already runs on year-own measured tables**. A
year-own table is not its cause. The 2021 coal econ rung at $32.9 vs CC econ $37.0 is what PJM's own 2021 offers
say. The remaining increment is 2019.

## 2. The arm: the 2019 table

- **Fetch:** `fetch_pjm_energy_offers.py --years 2019`, 12 month-files, 10.66 M rows (gitignored).
- **Publisher gap, carried as published:** 2019-11-08 through 2019-12-05 serves ~1,081 units/hour vs ~1,220. The
  API's own row count confirms it (2019-11-12: 25,944 rows vs 29,256 on 2019-11-07). Not a fetch fault.
- **Derive:** `derive_pjm_offer_midcurve.py --years 2019 --merge-into-existing`. This is a new flag. It derives the
  2019 ladders alone (2019's own unit-physics segmentation, same rules) and inserts them. It carries every
  existing entry verbatim and refuses a year already present.
- **Rule 23 proof (2020–2025 byte-identical):** canonical sha of every (segment, year) ladder for 2020–2025 and all
  three `pooled` ladders: identical, 21/21. `_provenance` is identical apart from the added `merged_year_derives`
  block. The summary CSV's first 72 rows are byte-identical and 12 rows are appended. Forward years read `pooled`,
  so the forecast is untouched by construction.
- **Why merge, not a full re-derive:** a 2019–2025 re-derive re-segments units on the widened union and re-pools
  the forward ladder. That would move tables whose source data did not change, which rule 23 forbids.
- Surface sha256 `f5426f75…` → **`936db1ba4c62f815a739b1e935ef4d9aa5bc97bb1952bf6e3837c4370c3cfc4a`**.

## 3. Zero-LP prediction (fleet-only 2019 rebuild, keeper recipe, own vs pooled)

2019 ladder, own − pooled (implied-HR mult): LONG_RUN mid/upper shares **−0.6 to −1.25** (bin 0); CC_LIKE lower
shares **+0.4**, top shares −2 to −4. Built with the model's own builder:

| class econ | GW | mc_base | bid, pooled (keeper) | bid, 2019-own | floor binds |
|---|---|---|---|---|---|
| COAL_BIT | 13.4 | 21.80 | 26.68 | **25.05** | 74 → 63 % |
| CC_REGULAR | 18.0 | 27.12 | 27.20 | 27.14 | 6 → 5 % |
| ST_GAS / CT_PEAKER | — | — | unchanged | unchanged | ~0 |

These are cap-weighted $/MWh, before startup amortization. `pjm_da_virtual_bids` is off: it is demand-side and inert
for offers.

**Predictions, stated before the solve:**
- **2019, AGAINST INTEREST:** COAL_BIT **rises** by +0.5 to +2.5 TWh. The +13.98 FAIL widens. CC_REGULAR 2019 falls by
  about the same amount. The measured 2019 coal offers sit lower relative to gas than the pooled blend of
  2020–2025.
- 2019 C3a (+10.6 % out of span): no change to −2 pts, because a cheaper coal rung lowers trough prices slightly.
  C3b: no direction predicted.
- **2020–2025:** inert by construction. The surface entries they read are byte-identical, and no code moved. Replays
  should reproduce the keeper's class energy. Any movement is a replay-reproducibility finding (rule 36(f)), not this
  arm, and is reported at full magnitude.
- No training-span (2023–2025) criterion flips. PJM stays NOT-YET on C1 CC_REGULAR 2024.

Why this solve is still owed although it is predicted to worsen a number: rule 14 `[R-ACCURATE]`. The pooled ladder
is an estimate for 2019. The publisher's own 2019 offers are the measured input. A worse fit means something else
is miscalibrated (§1 already shows the pre-2023 coal over-run persists on year-own tables). Rule 1: the residual
does not select the input.

## 4. G-DRIFT (rule 29(b)): form 4 holds, no control solves

I classified `git diff 54849585 HEAD` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`data/raw/_validation-source` and `data/raw/reference` hunk by hunk. **All 29 hunks are INERT for the PJM backcast:**

- New fields default False and absent from the keeper recipe:
  - `unit_outage_netload_mask_repair` (no PJM netloadmask file exists either);
  - `admit_standby_units` (the `eia860_operable_statuses()` refactor still returns `{"OP"}`);
  - `caiso_intertie_gap_fill_measured_dam`;
  - `cc_eia923_identity_emission_basis`.
- The coal-budget gate refactor: `coal_fuel_inventory*` are False in the recipe.
- `unit_outage_active_units(hour_grain=...)`: inside the ERCOT branch.
- CAISO interchange code and its data files: CAISO only.
- `key_provenance.py`, `forecast_parity_registry.py` and `bundle_io.py`: audit and provenance tooling.
- `outage_detect.py`: an SPP key in the offline deriver.

`replay_keeper.py` and `run_calibration_full.py` have no diff.

Extended to `origin/main` after the rebase (`3be69b8f` → main, 27 commits). Both new hunks are INERT:
- `miso_winter_gas_daily_delivered`: default False, and `apply_…` returns unless the flag is set and `iso == "MISO"`.
- `heat_rate_years.union_fleet(klass=None)`: an offline derive helper, byte-identical without the new argument.

The keeper's committed bundle is the control.

## 5. Execution (rules 32/34/36)

- **Shards:** one per year 2019–2025, pinned to the full SHA of the commit carrying this doc. Each runs
  `replay_keeper.py results/calibration/pjmnext3_c2_span --years <y> --out-dir results/calibration/pjmnext4_c1_<y>`,
  with no `--set`: the arm is the data file.
- **Hard stops:**
  - `git rev-parse HEAD` equals the pinned SHA.
  - The surface sha256 is `936db1ba…`.
  - The leg's `scenario_config` shows `pjm_offer_midcurve_conditional` true with segments `["LONG_RUN","CC_LIKE"]`,
    and `unit_outage_unit_fuel_routing` true.
- **Push:** the full bundle, including `dispatch/<y>_P1.parquet`, goes to `claude/pjmnext4-c1-<y>` via a
  `.gitignore` negation and a plain `git add`.
- **Parent:** composes the span (copy of `_pjmnext3_compose_span.py`), rebuilds the benchmark, scores against the
  keeper on the same benchmark, and attests (DOF ledger carried, zero entries added,
  `authorized_price_tuning.used = false`).
- **Close-out:** register `--no-prune`, update the PJM matrix shard, and ask the promotion question.

## 6. Card 2 (CC_REGULAR 2024, MD/VA gas basis): DATA-BLOCKED, no solve

There is no admissible daily east-PJM hub commodity series:
- The repo carries HH daily, the N3045 state delivered averages and four NGI-via-EIA daily points: Transco Z6 **NY**,
  Algonquin, Chicago and Cal Comp. None is Transco Z5/Z6-non-NY, Tetco M3, Eastern Gas South or Cove Point.
- Transco Z6 NY is New York City delivery. Using it for NJ/MD/VA would be a boundary misalignment under rule 14, and
  it carries the NGI licensing flag (`docs/data-licensing.md` §5).
- EIA's free ICE natgas workbooks stop at `ice_natgas-2017final.xlsx`. The wholesale page, checked 2026-09-26, lists
  electric workbooks only from 2018 onward.
- A daily series needs a licensed hub index (Platts/NGI/ICE). That is the owner's call. AP South (`I`) and Dominion
  sub-zonal congestion (pjm-137) were not re-opened.
