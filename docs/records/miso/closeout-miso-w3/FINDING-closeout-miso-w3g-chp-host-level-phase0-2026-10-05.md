# FINDING — closeout-MISO-w3g phase 0 (ZERO LP): the CHP host-online leg cannot be armed on MISO as chartered; its static effect would trip the kill bar

**Desk GO (2026-10-05 07:48Z):** "a host min-run/online leg inside `chp_steam_following`", with:
- multi-year CEMS-derived parameters (rule 13);
- no second floor (rule 19);
- binding only in the host's window (rule 17);
- bars: ≤ 1 failing record, CHP online share ≥ 0.75, C8 holds, C3a/C3b within band, unserved ≤ B;
- kill: any PASS→FAIL, or any per-hour pin.

**Outcome.** Phase 0 stops before a PRECOMMIT and no shard is launched. There are two independent blockers, both measured at zero LP.

Probe: `scripts/probes/_closeout_miso_w3g_chp_host_level_phase0.py` → `results/phase0/miso/_closeout_miso_w3g_chp_host_level_phase0.json`. HEAD derive (scratch, evidence only): `results/phase0/miso/_closeout_miso_w3g_thermal_tranches_MISO_head_2019_2025.csv`.

## 1. The leg already exists: a registered level swap, not a new mechanism

The object the desk described is MECH_CHP_STEAM's level swap `chp_steam_floor_p25`, scoped by `chp_steam_floor_conduct_scope`. This is the SPP-100 configuration, promoted in SPP (cell K).
- **Level:** pooled multi-year CEMS on-frequency × p50 loading-when-online.
- **Scope:** applies only to metered hosts whose on-frequency exceeds `CHP_STEAM_ALLHOURS_MIN_ON_FRAC` = 0.5, which is D-4's own conduct test applied ex ante.

It satisfies all three guardrails by construction:
- one floor, a level-source swap (rule 19);
- no per-hour pin (rule 13);
- scoped away from cyclers (rule 17).

No new field is needed. MISO has never tested either field: `chp_steam_floor_conduct_scope` is U in MISO.js, and `chp_steam_floor_p25` has no MISO evidence.

## 2. Blocker A: the MISO artifact cannot carry the column without an owner-blocked re-derivation (rule 23)

**The column is missing.** The swap reads `steam_level_cf`. MISO's keeper reads `thermal_tranches-fuelsplit-stcov-splitremap-MISO.csv`, whose CHP rows are copied verbatim from the base `thermal_tranches_MISO.csv` (`write_unit_fuel_split_companions` protects `_CHP_GROUPS`). That base predates WP-3 and has no `steam_level_cf`.

**The fleet guard refuses to arm.** A fleet-only build of the arm-B leg with the swap armed is refused by `assert_thermal_tranche_coverage`:

> chp_steam_floor_p25 reads 'steam_level_cf/p25_allhr_cf' for CC_CHP: COLUMN ABSENT (14 status='ok' rows would be silently skipped) … Remedy: this ISO's own pre-registered keeper-grade re-derivation under rule 23 [R-FROZEN-DERIVE] — never a silent skip, never another ISO's artifact.

**The base does not reproduce at HEAD.** The base artifact is provenance-orphaned:
- miso-95 found it `PROVENANCE-BLOCKED`, with no recorded derive invocation;
- FINDING-xiso5 §1 lists the MISO tranche re-baseline as "chartered, not landed — a subset of miso-95's owner-blocked re-baseline".

A HEAD derive (2019–25 pooled) against the committed CHP rows:

| committed column | rows that reproduce |
|---|---|
| `status`, `nameplate_mw`, `chp_sector` | 104/110 |
| `committed_pct` | 101/110 |
| `median_cf` | 95/110 |
| **`chp_pmin_cf`** (the incumbent floor) | **28/110** |

Six CHP rows exist at HEAD only.

**Consequence.** Adding `steam_level_cf` means one of two things:
- re-deriving MISO's CHP floors, which moves the incumbent `chp_pmin_cf` on 82 rows — the owner-blocked re-baseline;
- splicing a HEAD-vintage column into an orphan-vintage file — the vintage mix the guard exists to refuse.

Neither is this lane's to take. The lane does not work around the guard.

## 3. Blocker B: the static effect trips the desk's kill bar (PASS→FAIL)

As if the swap were armed at the HEAD level with the scope applied, added forced energy against arm B's own dispatch (TWh; an upper bound before LP re-dispatch):

| year | CC_CHP metered | CC_CHP 923-only | CT_CHP | ST_CHP | B CC_CHP C1 | static CC_CHP C1 |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 10.39 | 0.56 | 0.27 | 0.05 | −4.62 | ≈ +6.3 |
| 2020 | 9.34 | 0.48 | 0.28 | 0.08 | −1.98 | ≈ +7.8 |
| 2021 | 12.00 | 0.85 | 0.30 | 0.06 | −4.43 | ≈ +8.4 **FAIL** |
| 2022 | 11.41 | 0.76 | 0.31 | 0.03 | −6.12 | ≈ +6.1 |
| 2023 | 9.25 | 0.33 | 0.15 | 0.10 | −0.31 | ≈ +9.3 **FAIL** |
| 2024 | 7.46 | 0.28 | 0.14 | 0.07 | +2.25 | ≈ +10.0 **FAIL** |
| 2025 | 9.86 | 0.40 | 0.17 | 0.07 | (not gated) | — |

The band is ±8 TWh. CC_CHP goes PASS→FAIL in 2021, 2023 and 2024, which is the kill. The metered lens carries 90–95 % of the add, so a metered-only form does not escape it.

**The over-force is a basis defect, not only a level.** Metered levels are percentages of the artifact's CAMPD nameplate. The floor applies them to the model's own grid capacity. In 2023:
- **Midland 10745:** level 64.7 % on a 1,750 MW grid cap (artifact nameplate 1,479 MW). Floored energy is 11.66 TWh against the plant's whole-year CAMPD net of 7.89 TWh, i.e. 1.48× its meter.
- **Dearborn 55088:** 5.00 vs 3.65 TWh.
- **Clipped plants:** four metered rows carry levels above 100 % (Dearborn 121, 55075 132, 55419 143, CT_CHP 1391/50625 ≈ 147), so their floor clips to the full grid capacity in every available hour.

That is a floor above the plant's own measured output, the rule-17 conduct D-4 convicts. On MISO, the swap would not be the SPP-100 object (a host floored at a fraction of its meter).

## 4. What would make it admissible (recorded, not proposed for this lane)

1. **Owner unblocks the MISO tranche re-baseline (miso-95).** A pre-registered, keeper-grade re-derivation of the MISO CHP rows at HEAD would emit `steam_level_cf`/`chp_pmin_on_cf` alongside re-derived `chp_pmin_cf`. That re-derivation moves the incumbent floor on 82 rows and is its own lane, with its own control.
2. **Fix the basis before any arm.** The level must be expressed on the capacity the floor multiplies (the model's grid capacity, or the artifact nameplate carried through), so a metered host is never floored above its own meter. This is a shared-code question for MECH_CHP_STEAM (CAISO and SPP also arm the swap), not a MISO lever.
3. **Then re-run this probe's static bound.** Without (2), the kill fires ex ante.

## 5. Matrix

MISO.js:
- `chp_steam_floor_conduct_scope`: stays U;
- `chp_steam_following`: stays K.

Evidence notes cite this FINDING. No cell verdict moves, because nothing was solved. ST_GAS 2019 stays a ledgered, routed miss (`scuc_load_pocket_commitment` G).
