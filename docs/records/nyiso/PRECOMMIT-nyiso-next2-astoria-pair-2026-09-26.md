# PRECOMMIT — NYISO-NEXT-2: the Astoria stack-duplicate boiler pair in the outage extract — 2026-09-26

**Session:** NYISO-NEXT-2 (orchestrator; no LP in this container, rule 32 (a)).
**Keeper (control, rule 29 (b) form 4):** `2026-09-26-nyisonext-floor-layup-span`
(`results/calibration/nyisonext_span`, 2022–2025) + stamped `2026-09-26-nyisonext-floor-layup-2021`
(`results/calibration/nyisonext_2021`). Keeper basis `5a977fecc5770ae77aade7a585791675b85ea544`.
**This document is pinned before any solve; the pin is the commit that carries it.**

## 0. Headline, fixed before any solve

- **Lever (c) of the lane brief**, the only candidate with a measured, zero-parameter
  identification (§2). **ZERO `scenario_config` changes.** The arm is the keeper recipe solved on
  the merit-guarded hour-grain unit-outage extract pair RE-DERIVED under its committed invocation
  after a deriver repair — the nyiso-192 form (rule 23: the re-derivation cites a derive-code defect,
  never a residual).
- **The defect.** `scripts/data/derive_campd_unit_outages.py`'s detector loop never folded CAMPD's
  stack-duplicate twins (`campd.CAMPD_STACK_DUPLICATE_UNITS`: Astoria 8906 `32SH` → `31RH`,
  `52SH` → `51RH`; identified at nyiso-141 on three channels). Every other consumer folds them —
  the emissions curation, the parasitic factors, and since nyiso-192 the merit-order panel. In the
  outage extract each twin was
  1. detected on the generator's full gross load and booked at the generator's full observed peak
     (~380 MW each), so Astoria's plant basis read **1,689–1,705 MW against a physical 924–936**;
  2. and the duplicate, absent from the merit panel that already folds it onto its primary, failed
     OPEN to **"outage"** on every stop its primary's own merit test classified as **lay-up**:
     `32SH`/`52SH` 66/53 windows, **all** outage; `31RH`/`51RH` 62/44 lay-up + 4/9 outage, the
     identical windows. 137–262 mixed days per pair per year.
- **The repair:** drop the duplicate rows before detection (they carry nothing but a copy of the
  primary's `grossLoad`; detection reads only `grossLoad`/`opTime`). Unit-tested.
- **Predicted direction: NYC ST_GAS moves UP, away from EIA-923.** This lever does **not** address
  the lane's headline merit-order object; it is a correctness repair of the availability basis that
  object sits on (the brief's item (4), nyiso-177 G2's over-booking). Stated now so it cannot be
  re-read afterwards.

## 1. Phase 0 (zero LP), committed evidence

Probes: `scripts/probes/nyisonext2_astoria_pair_phase0.py` →
`results/calibration/_nyisonext2_astoria_pair_phase0.json`; the floor-in-meter-zero census →
`results/calibration/_nyisonext2_astoria_floor_meterzero.json`. Fleet-only rebuilds through
`replay_keeper.run_year_kwargs`, committed pair (CONTROL) vs repaired pair (ARM).

### 1.1 Reproducibility and the extract footprint

- Re-deriving under the committed invocation at HEAD **before** the repair reproduces both committed
  files **byte-identically** (sha256 `ee778a87…` / `c4cd6ace…`).
- After the repair: `-perunitmerithour-` 3,734 → **3,615** rows (the 119 `32SH`/`52SH` windows
  removed); the lay-up companion keeps its 1,213 rows. **Every non-8906 row is byte-identical in
  both files.** New sha256: extract `986d1d43…`, lay-up `fe01645d…`.
- Out of scope, stated: the day-grain `-perunitmerit-` extract does **not** reproduce at HEAD even
  pre-repair (drift in other plants), and the keeper does not read it for outages; it and the
  `thermal_tranches-perunitmerit-` artifact derived from it are left as committed.

### 1.2 G-FOOTPRINT (fleet arrays, every year 2021–2025)

`pmax`, `pmin`, `heat_rate`, `zone_idx`, `vom`, `mc_base` identical; `availability` and `min_gen`
differ **only on Astoria 8906 rows**. Astoria's CT row (13.6–15.7 MW) is unchanged.

### 1.3 Astoria ST_GAS (918.8–923.2 MW)

| year | avail mean CTL → ARM | avail TWh CTL → ARM | rel.-floor TWh CTL → ARM | floor in meter-zero h (ARM) | keeper model TWh | EIA-923 | binding h (keeper) | **binding bound** |
|---|---|---|---|---|---|---|---|---|
| 2021 | 0.377 → 0.799 | 3.04 → 6.43 | 0.047 → 0.252 | 0.004 | 1.71 | 0.66 | 0 | **0.000** |
| 2022 | 0.441 → 0.813 | 3.57 → 6.57 | 0.102 → 0.302 | 0.003 | 2.12 | 0.83 | 10 | **0.003** |
| 2023 | 0.325 → 0.735 | 2.63 → 5.94 | 0.112 → 0.285 | 0.009 | 1.72 | 0.73 | 1,260 | **0.423** |
| 2024 | 0.431 → 0.800 | 3.49 → 6.47 | 0.158 → 0.323 | 0.010 | 1.71 | 0.87 | 209 | **0.116** |
| 2025 | 0.394 → 0.678 | 3.18 → 5.48 | 0.276 → 0.439 | 0.002 | 1.98 | 1.36 | 1,318 | **0.535** |

- **Binding bound** = added available energy in hours the keeper's registered Astoria dispatch sat
  at its availability cap (one uint8 quantum). Astoria is **economically**, not
  availability-limited in most hours, so the doubled envelope reaches dispatch only there.
- The NYC ST_GAS reliability-floor limb gains exactly Astoria's increment (pro-rata basis):
  0.52 → 0.73 / 0.66 → 0.86 / 0.72 → 0.89 / 0.84 → 1.01 / 1.12 → 1.29 TWh. It lands in hours
  Astoria's own CAMPD meter was running (≤ 0.010 TWh in meter-zero hours).

## 2. Why (c) and not (a), (b), (d)

- **(a) delivered-fuel basis beyond Rate D(2): refused, no measured source.** The Con Ed VAC is
  individual-customer and unpublished; the three NYC steam plants are LDC-served and file no EIA-923
  receipts cost (nyiso-192); the state N3045NY3 series pools pipeline-connected upstate plants
  (rule 14 misalignment); the daily LDC index was refused on NYC steam at nyiso-192. Oil is not the
  carrier either: EIA-923 oil share of heat input at Ravenswood is 0.4–4.2 %, Astoria 0.1–10 %.
- **(b) measured offer conduct from P-27: refused, not identifiable.** P-27 carries no zone, fuel,
  class or unit identity (its README limit 1); a per-class NYC steam offer cannot be keyed to it,
  and `measured_offer_surface` is `G` (nyiso-244) with no new evidence.
- **(d) CC_REGULAR tranches / band multipliers: refused.** The one measured grounding available
  (committed 0.90 → phys 0.964) makes CC dearer and, on the model's own merit order, hands the
  energy to NYC steam at Z6 gas — the wrong object. Restoring `econ_high` 1.21 is a DO-NOT-REDO
  (nyiso-230). A rule-1 carve-out value has no ex-ante basis here that is not a residual.

## 3. G-DRIFT (rule 29 (b)), keeper basis `5a977fec` → lane base `91497567`

`git diff 5a977fec 91497567 -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
touches 25 files. **Every hunk is INERT for NYISO** — each is another ISO's branch (CAISO intertie
gap-fill and supply-consistent demand, PJM zonal gas basis, ERCOT hour-grain / event cap, MISO/NEISO
coal yard budget, SPP outage_detect BA map), a default-off field absent from the keeper recipe (11
new fields, all dropped from the cache key at their default), or provenance accounting
(`key_provenance`, `forecast_parity_registry`, `bundle_io`, `resolved_inputs`). The one shared
path, `campd_bins._APPLIED_MEASURED_FLAGS`, admits only `eia923_identity` rows, which no NYISO
artifact carries. No NYISO-named raw file changed. **Form 4 stands; no control solve.**

## 4. Pre-registered expectations (fixed now)

- **Direction:** Astoria ST_GAS ↑ every year; NYC ST_GAS ↑ (away from EIA-923); the energy comes
  off Ravenswood / Arthur Kill / CC_REGULAR / imports at the NYC margin. NYC price ↓ slightly.
- **Magnitude:** Astoria **+0.2 to +0.8 TWh** per year — the floor increment (+0.17–0.21) plus at
  most the binding bound (0.00 / 0.00 / 0.42 / 0.12 / 0.54), plus whatever economic re-dispatch the
  lower NYC price allows. NYC ST_GAS net **+0.1 to +0.7 TWh**.
- **C1-2023 ST_GAS** (+2.14 TWh, PASS) may worsen; whether it crosses its band is **not a criterion**.
- **C8 ST_GAS forced share** rises slightly (floor numerator +0.16–0.21 TWh).
- **D-4:** no new `reliability_floor` FAIL row at 8906 (the added floor sits where the plant ran).
- **Structural metric that must move:** Astoria's booked-outage share falls by 0.28–0.42 of the
  plant in every year.

## 5. The recipe: five shards, one per year (rule 36), pinned to this document's commit SHA

```
uv run python scripts/replay_keeper.py results/calibration/<BUNDLE> --years <Y> \
  --out-dir results/calibration/nyisonext2_<Y> 2>&1 | tee results/calibration/nyisonext2_<Y>/solve.log
```

`<BUNDLE>` = `nyisonext_2021` for Y = 2021, `nyisonext_span` for 2022–2025. **No `--set`**: the
recipe rides in the bundle's `meta.json`; the one change is the committed extract at the pin.

## 6. Leg acceptance (`scripts/probes/nyisonext2_compose_span.py --pin <this SHA>`)

- **S0 pin:** `git.basis_sha` = the pin, not dirty.
- **S1 config:** the keeper's flags exactly (incl. `nyiso_ldc_generator_delivered_gas`,
  `nyiso_dynamic_reserve_requirements`, `reliability_floor_layup_window_mask` true); offer-curve block
  equal to the keeper's.
- **S2 inputs:** `campd_unit_outages` sha256 = **`986d1d43…`** (the repaired extract);
  `thermal_tranches` = the keeper's `a3bbd6ef…`.
- **S5 footprint:** the solve log carries the keeper's LDC line (42 rows, 6 plants) and
  `reliability_floor_layup_window_mask ARMED`.

## 7. Reporting and promotion (fixed now)

- **Report per year, at full magnitude**, differenced against the keeper's committed bundles: C1–C8;
  ST_GAS and CC_REGULAR TWh vs EIA-923 by zone and plant; D-4 rows; price bias / MAE vs RT.
- **Promotion rule.** The arm repairs a measured double-count and a fail-open misclassification and
  moves nothing else, so it is **structurally more faithful by construction** (rules 14, 23). It is
  promoted unless:
  1. a leg fails acceptance; or
  2. a protective criterion (C6 / C8) newly fails without passing C8's provenance + shape
     escalation (rule 21); or
  3. a **new** `reliability_floor` D-4 FAIL row appears at 8906 (falsifies §1.3's placement).

  C1 at NYC steam, C3a/b, MAE and the determination moving are **reported, not a bar**; never
  promoted on MAE alone.
- **If promoted (rule 35):** enumerate the year set ({2021–2025}); register 2022–2025 composed as the
  keeper and 2021 stamped to it; `audit_keepers`; prune the outgoing keeper with `--keep` for the new
  2021 run and `--force-uncite`; re-key gate (a); `check_promotion_completeness`. No new field, so no
  parity-registry declaration.
- **If not promoted:** the committed extract is restored to `ee778a87…` on `main` together with a
  default-off gate for the deriver repair, so the keeper keeps reproducing.
- **Rule 28 (b):** the NYISO `campd_outage_merit_order_guard` cell carries this evidence.
