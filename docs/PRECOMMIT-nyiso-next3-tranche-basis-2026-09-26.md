# PRECOMMIT — NYISO-NEXT-3: the committed tranche share on the solve's own availability basis — 2026-09-26

**Session:** NYISO-NEXT-3 (orchestrator; no LP in this container, rule 32 (a)).
**Keeper (control, rule 29 (b) form 4):** `2026-09-26-nyisonext2-astoria-pair-span`
(`results/calibration/nyisonext2_span`, 2022–2025) + stamped `2026-09-26-nyisonext2-astoria-pair-2021`
(`results/calibration/nyisonext2_2021`). Keeper basis `9fe82bde8aa2090c55c1440a307a8a99cf6861f8`.
**This document is pinned before any solve; the pin is the commit that carries it.**

## 0. Headline, fixed before any solve

- **Lever: item (5) of the brief, which turned out to be solve-inert on its own, plus the defect that
  made it inert.** ZERO `scenario_config` changes, ZERO new fields, ZERO free parameters.
- **What (5) alone does: nothing.** Re-deriving `thermal_tranches-perunitmerit-NYISO.csv` on the
  repaired extract moves 8 ST_GAS rows, but a fleet-only rebuild is **byte-identical in every array
  in every year 2021–2025** (§1.3 `arm`). No keeper consumer reads the columns that move.
- **Why: the bin builder never read that artifact's committed share.** `campd_bins.fleet_to_bins`
  called `thermal_tranche_overrides(iso, coal_online_pmin, per_unit)` without `merit_guard`. So under
  `campd_outage_merit_order_guard` every bin's `committed_pct` came from the **unguarded `-perunit-`
  artifact**, while `online_frac`, peaking, p25 and the reserve pool mlf read `-perunitmerit-`.
  - That is two availability bases in one LP: the state nyiso-177 built `campd_attribution_selectors`
    to prevent ("ONE field over BOTH artifacts").
  - The `-perunit-` artifact still carries the Astoria double count (committed 11.3 %,
    median_cf 90.6 %).
  - The repair is one argument (`_mg`). Only NYISO arms the guard, so **no other ISO or keeper can
    move**. SOCO arms `per_unit` alone, where `_mg` is False and nothing changes.
- **The arm = that repair + the tranche artifact on the current outage basis** (one object: the
  committed share on the solve's own availability basis, rule 19).
  - Astoria committed **11.3 % → 9.0 %** (CAMPD P5 when on).
  - Ravenswood ST **20.4 → 8.5 %**, Arthur Kill **30.0 → 11.0 %**.
- **Predicted direction: NYC steam UP slightly, away from EIA-923.** The committed band is offered at
  1.05 × and econ at 1.00 ×, so the MW the repair moves from committed to econ get ~3 % cheaper.
  This lever does **not** address the NYC steam merit-order object. It is a correctness repair.
  Stated now so it cannot be re-read afterwards.

## 1. Phase 0 (zero LP)

Probe: `scripts/probes/nyisonext3_tranche_basis_phase0.py` →
`results/calibration/_nyisonext3_tranche_basis_phase0.json`. Fleet-only rebuilds through
`replay_keeper.run_year_kwargs`:
- CONTROL = committed artifacts;
- `arm` = re-derived artifacts;
- `arm_sel` = re-derived artifacts + the selector repair (patched in-process). A rebuild with the real
  code change reproduces `arm_sel` exactly (14 plant-classes, 0 mismatches, 2023).

### 1.1 The day-grain extract (why it did not reproduce)

- HEAD **before** the NEXT-2 repair (the deriver at `9fe82bde^`) = committed extract + **17 rows**,
  and **zero rows removed**:
  - Cayuga 2535 ×5 and Somerset 6082 ×10 (the two NYISO coal retirees);
  - Nassau 52056 ×2 (CC).
- **Every one of the 17 is a 2019–2020 window.** They sit outside every solved year (2021–2025) and
  outside the 2023–2025 tranche window, so they are inert. They are **not absorbed**.
- HEAD **after** the repair differs from HEAD before it **only at Astoria 8906** (181 → 62 rows).
- **Committed as a splice:** the committed file with its 8906 rows replaced by the repaired
  deriver's. The splice plus the 17 drift rows equals the whole-file HEAD re-derivation as a
  multiset (asserted).
  - `-perunitmerit-` sha256 `6612f806…`, 3,598 rows;
  - lay-up companion `c143d5c0…`.
- The solve does not read this file (it reads the hour-grain pair, unchanged at `986d1d43…`). Its
  only consumer is the tranche deriver.

### 1.2 The tranche artifact (why it did not reproduce)

- **Last written by nyiso-187 (`e19dfee0`, 2026-09-04)**, against the nyiso-187 extract. After that,
  nyiso-192 (2026-09-05; 106 Astoria windows out, 155 steam windows at 15 other plants in) and
  NYISO-NEXT-2 re-derived the extract, but **not this artifact**.
- **HEAD's deriver on the nyiso-187 extract reproduces the committed rows exactly (0 differing
  values).** The whole drift is therefore those two extract re-derivations. Nothing is unexplained.
- On the current extract, **8 ST_GAS rows move** (`online_hours`, `committed_pct`, `p25_cf`,
  `median_cf`) and no other row does:

| plant | committed_pct | p25_cf | median_cf |
|---|---|---|---|
| Astoria 8906 | 17.8 → **9.0** | 50.9 → 9.1 | 57.6 → **15.4** |
| Ravenswood 2500 | 6.5 → 8.5 | 18.6 → 21.0 | 28.8 → 29.6 |
| Northport 2516 | 15.3 → 24.7 | 29.1 → 32.3 | 43.9 → 49.1 |
| Arthur Kill 2490 | 11.0 → 11.0 | 11.2 → 28.3 | 29.1 → 30.0 |
| Bowline 2625 | 20.1 → 21.0 | 51.8 → 58.9 | 92.8 → 94.9 |
| Danskammer 2480 / Port Jefferson 2517 / Roseton 8006 | ≤ 0.2 pp | | |

- **Measured check for Astoria:** CAMPD shows it on for 4,967–6,650 h/yr at a median of **83–136 MW
  (9–15 % of 923 MW)**. The re-derived committed 9.0 % and median 15.4 % match that; 17.8 / 57.6 did
  not.
- Written in the committed column set: HEAD also emits `chp_pmin_on_cf`, which is not part of this
  repair. sha256 `38cc256b…`.
- The derivation on the spliced extract is byte-identical to the derivation on the whole-file HEAD
  extract, so the 17 drift rows are proven inert for this artifact too.

### 1.3 G-FOOTPRINT (fleet arrays, every year)

- **`arm`: identical in every array, every year.** It is solve-inert alone.
- **`arm_sel`: only `pmax` and `min_gen` move.**
  - `heat_rate`, `availability`, `mc_base`, `vom`, `zone_idx` and `pmin` are identical.
  - Per plant-class, total `pmax` is unchanged; MW move between the committed and econ tranche rows.
  - Floor TWh per plant is identical to 4 d.p.; the floor is only reallocated across rows.
- 14 plant-classes move:
  - ST_GAS 8906, 2500, 2490, 2516, 2511, 2480, 2517 (8006 in 2025, floor only);
  - CC_REGULAR 50978, 55375, 57664;
  - CC_CHP 52168, 54914.

### 1.4 Both bounds (TWh; `arm_sel`, keeper's own hourly zonal price)

- **Binding-hour bound = 0.000 in every year for every plant.** Available energy per plant-class is
  unchanged, so no availability cap moves.
- **Economic-reach estimate** = Σₜ Σ_rows cap·1(offer < keeper zonal price), arm minus control. It is
  a first-order figure at a fixed price, not a strict bound.

| year | NYC ST_GAS | LI ST_GAS | Cap/Hud ST_GAS | CC_CHP (NYC) | CC_REGULAR | NYC steam MW committed → econ |
|---|---|---|---|---|---|---|
| 2021 | +0.168 | +0.005 | +0.002 | −0.161 | −0.002 | 386 |
| 2022 | +0.069 | +0.004 | +0.003 | −0.105 | −0.003 | 387 |
| 2023 | +0.234 | +0.003 | +0.001 | −0.047 | −0.003 | 391 |
| 2024 | +0.087 | +0.004 | +0.003 | −0.147 | −0.005 | 390 |
| 2025 | +0.076 | +0.004 | +0.003 | −0.201 | −0.001 | 389 |

- In 2023 Ravenswood carries the largest share (+0.149), then Arthur Kill (+0.067) and Astoria (+0.018).
- NYC CC_CHP 54914's committed tranche shrinks 215 → 135 MW.

## 2. Why this lever and not (ii), (iii) or a band multiplier

- **(ii) NYC steam tranche shares from the plants' own conduct: answered by §1.2, and it cannot reach
  the object.**
  - `committed_pct` IS measured (status `ok`); it was read off the wrong artifact, which this arm
    repairs.
  - `econ_low_share` 0.5 is a structural class share. Rule 1 (a) protects it from tuning, and it is
    price-inert here (`econ_low` = `econ_high` = 1.0).
  - Every Astoria / Ravenswood band except peak offers at ~$32–36 against a NYC mean of ~$34. The
    committed/econ split moves the offer by ~3 %, so **no tranche share can take NYC steam out of
    merit.**
  - The object is that the real plants run at minimum load in hours the model runs them at full
    econ output. That is a conduct/commitment object (Con Ed VAC unpublished; `scuc_load_pocket_commitment`
    `G`), not a tranche object.
- **(iii) the 8906 2024 bridge D-4 row:** 0.005 TWh in 54 h. The bridge floors the P0 run pattern at
  the measured ST `min_load_frac` 0.239. The row is a consequence of the over-dispatch, not a
  construction defect in the bridge, and it is not addressed here.
- **Band multipliers:** no ex-ante value exists that is not the residual (rule 1 (c)); not used.

## 3. G-DRIFT (rule 29 (b)), keeper basis `9fe82bde` → lane base `55b89a3f` (origin/main)

`git diff 9fe82bde 55b89a3f -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
touches 19 files. **Every hunk is INERT for NYISO:**

- **Default-off fields absent from the keeper recipe:**
  - `admit_standby_units` (`{"OP"}` unchanged while off; `_fleet_cache_dir_key` identical);
  - `unit_outage_netload_mask_repair` (SPP-85; NYISO has no `-netloadmask-` companion);
  - `miso_winter_gas_daily_delivered` (MISO branch).
- **Other ISOs' branches:**
  - the ERCOT hour-grain `unit_outage_active_units`;
  - the SPP `_ISO_TO_BA` key;
  - the CAISO supply-consistent demand files.
- **Derive-time only:** `heat_rate_years.union_fleet(klass)`, which the CT heat-rate deriver uses and
  the solve does not.
- **Provenance accounting:** `bundle_io` captures `-netloadmask-` paths only if the file exists.
- **Commits between `9149be2c` and `55b89a3f`:** none touch these paths.

Form 4 stands. **No control solve.**

## 4. Pre-registered expectations (fixed now)

- **Direction:**
  - NYC ST_GAS ↑ (away from EIA-923), led by Ravenswood and Arthur Kill;
  - NYC CC_CHP ↓;
  - NYC price ↓ very slightly or unchanged.
- **Magnitude:**
  - NYC ST_GAS **+0.05 to +0.30 TWh/yr**;
  - CC_CHP **−0.05 to −0.25 TWh/yr**;
  - every C1 class moves < 0.4 TWh;
  - C3a moves < 1 pp.
- **Floors:** the NYC ST_GAS reliability-floor TWh is unchanged (§1.3). C8 moves only through the
  dispatch denominator.
- **D-4:** no new `reliability_floor` FAIL row.
- **The determination may not change.** C3a 2022 / 2025 stay outside ±10 % unless the price moves
  more than predicted.

## 5. The recipe: five shards, one per year (rule 36), pinned to this document's commit SHA

```
uv run python scripts/replay_keeper.py results/calibration/<BUNDLE> --years <Y> \
  --out-dir results/calibration/nyisonext3_<Y> 2>&1 | tee results/calibration/nyisonext3_<Y>/solve.log
```

- `<BUNDLE>` = `nyisonext2_2021` for Y = 2021 and `nyisonext2_span` for 2022–2025.
- **No `--set`.** The recipe rides in the bundle's `meta.json`; the change is the code and the
  artifact at the pin.

## 6. Leg acceptance (`scripts/probes/nyisonext3_compose_span.py --pin <this SHA>`)

- **S0 pin:** `git.basis_sha` = the pin, not dirty.
- **S1 config:** the keeper's flags exactly; offer-curve block equal to the keeper's.
- **S2 inputs:**
  - `thermal_tranches` sha256 = **`38cc256b…`** (re-derived);
  - `campd_unit_outages` = the keeper's `986d1d43…`.
- **S5 footprint:** the keeper's LDC line and `reliability_floor_layup_window_mask ARMED`.

## 7. Reporting and promotion (fixed now)

- **Report per year, at full magnitude,** against the keeper's committed bundles:
  - C1–C8;
  - ST_GAS and CC_REGULAR TWh vs EIA-923 by zone and plant;
  - D-4 rows;
  - price bias / MAE vs RT.
- **Promotion rule.** The arm removes a two-basis mix inside one LP and puts a stale artifact on the
  basis its own extract has carried since nyiso-192. It fits nothing and moves nothing else, so it is
  **structurally more faithful by construction** (rules 14, 19, 23). It is promoted unless:
  1. a leg fails acceptance; or
  2. a protective criterion (C6 / C8) newly fails without passing C8's provenance + shape
     escalation (rule 21); or
  3. a **new** `reliability_floor` D-4 FAIL row appears.

  C1, C3a/b, MAE and the determination moving are **reported, not a bar**. Never promoted on MAE alone.
- **If promoted (rule 35):**
  1. enumerate the year set ({2021–2025});
  2. register 2022–2025 composed as the keeper and 2021 stamped to it;
  3. run `audit_keepers`;
  4. prune the outgoing keeper with `--keep` and `--force-uncite`;
  5. re-key gate (a);
  6. run `check_promotion_completeness`.

  No new field, so no parity-registry declaration.
- **If not promoted:** the selector repair goes behind a default-off gate and the committed tranche
  artifact is restored to `a3bbd6ef…`, so the keeper keeps reproducing.
- **Rule 28 (b):** the NYISO `campd_outage_merit_order_guard` cell carries this evidence.
