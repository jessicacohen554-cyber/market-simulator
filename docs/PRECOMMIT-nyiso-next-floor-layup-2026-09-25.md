# PRECOMMIT — NYISO-NEXT: the NYC persistent-base floor at unit grain, and the lay-up window mask — 2026-09-25

**Session:** NYISO-NEXT (ORCHESTRATOR, rule 32 `[R-SHARD]` (a): this container runs no LP).
**Keeper (control, rule 29 (b) form 4):** `2026-09-25-nyiso-stgas-ldc-leg`, bundle
`results/calibration/nyisostg_span` (2022–2025, basis `54ac9e1a509c0cad01aadcb9d7583535fd27d883`),
plus the stamped 2021 run `2026-09-25-nyiso-stgas-ldc-2021` (`results/calibration/nyisostg_2021`,
same basis). Determination **CALIBRATED**, C3c the single ledgered caveat.
**Lane branch cut from:** `origin/main` = `d5d5e0e8665e30367b329a3407eef7658eacf32f`.

---

## 0. Headline, fixed before any solve

1. **The object is (b), the pro-rata fill base.** The NYC persistent-base limb floors each unit at
   `floor_pct × pmax × availability[t]`. The CAMPD merit-order guard **deliberately returns measured
   economic lay-up windows to availability**. So the floor forces a unit on inside the very windows
   the model's own outage pipeline classified as laid up — a rule 17 `[R-FLOOR-WINDOW]` violation
   by definition.
2. **Why Ravenswood's floor jumps in 2021 and 2023.** The guard books Ravenswood's 2021/2023 stops as
   **lay-up** (mean lay-up share 0.76 / 0.66 of the bin) and its 2022/2024/2025 stops mostly as
   **outage**. Its availability, and with it the floor, reads 0.68 / 0.64 in the two lay-up years
   against 0.13 / 0.23 / 0.12 otherwise.
3. **One lever, structural, zero free parameters:** `reliability_floor_layup_window_mask` (new,
   default off, backcast-only). On a **pro-rata** limb, each unit's floor basis becomes
   `pmax × max(0, availability − layup_share(t))`, read from the lay-up half of the **same**
   detection the availability overlay reads its outage half from. `availability` and `floor_pct`
   are untouched; cheapest-first limbs are not masked.
4. **Not (a) and not (c).** The window is right: nyiso-203 measured all three NYC plants running a
   24 h base, and this lane does not re-open it. The coefficient is not the instrument: it already
   reads **0.1663** on `main` and in the keeper. (The lane brief's "main still reads 0.175" is stale:
   nyiso-226/227 landed 0.1663 on 2026-09-11, and the keeper's basis SHA carries it.) A masked-basis
   coefficient is **not identifiable** (§1.4).
5. **All five years are solved, one shard each (rule 36), on the same config.** No offer-curve band
   moves, no multiplier is tuned, and no gate is a stop condition. Regressions are reported at full
   magnitude and routed, never recovered by tuning (rule 1 (c)).

## 1. Phase 0 (zero LP), committed evidence

Probe `scripts/probes/nyiso_next_floor_layup_phase0.py` → `results/calibration/_nyiso_next_floor_layup_phase0.json`.
It makes two fleet-only rebuilds per year through `replay_keeper.run_year_kwargs`: the keeper
recipe (CONTROL), and the same recipe with the mask on (ARM). It reads the reliability-floor
`min_gen` rows (`min_gen_mechanism == reliability_floor`) at LP-row grain and sums them per plant.

- **Meter:** each plant's class-resolved CAMPD series (the bench part). "Meter ~zero" means below
  0.5 % of the class's own nameplate.
- **Binding hours:** on the keeper's registered dispatch (payload), model MW within one 1 % quantum
  of the floor.

### 1.1 The NYC limb at unit grain (TWh; CONTROL → ARM)

| year | Ravenswood 2500 | Astoria 8906 | Arthur Kill 2490 | **NYC limb** | **in meter-~zero h** |
|---|---|---|---|---|---|
| 2021 | 1.718 → 0.142 | 0.505 → 0.047 | 0.346 → 0.333 | **2.569 → 0.522** | **1.238 → 0.017** |
| 2022 | 0.327 → 0.191 | 0.593 → 0.102 | 0.438 → 0.362 | **1.358 → 0.655** | **0.248 → 0.031** |
| 2023 | 1.619 → 0.298 | 0.437 → 0.112 | 0.871 → 0.308 | **2.927 → 0.718** | **0.795 → 0.014** |
| 2024 | 0.573 → 0.237 | 0.580 → 0.158 | 0.503 → 0.446 | **1.656 → 0.841** | **0.299 → 0.017** |
| 2025 | 0.291 → 0.291 | 0.529 → 0.276 | 0.576 → 0.555 | **1.396 → 1.122** | **0.058 → 0.041** |

**Floor vs the guard-returned availability.** `floor / (pmax × availability)` = 0.1663 exactly, in
every year and at every plant, by construction. Mean availability and mean lay-up share by year
(2021–2025):

- **Ravenswood:** availability 0.68 / 0.13 / 0.64 / 0.23 / 0.12; lay-up 0.76 / 0.08 / 0.66 / 0.20 / —.
- **Astoria:** availability 0.38 / 0.44 / 0.32 / 0.43 / 0.39; lay-up 0.69 / 0.64 / 0.60 / 0.62 / 0.39.

**Measured output (CAMPD class series, TWh):**
- **Ravenswood:** 0.51 / 0.55 / 0.85 / 0.68 / 1.07.
- **Astoria:** 0.72 / 0.89 / 0.77 / 0.92 / 1.35.

In 2021 Ravenswood's floor alone (1.72) is **3.4×** its measured output, and 68 % of that floor
(1.17 TWh) sits in hours its own meter reads ~zero.

**Binding (keeper dispatch) hours / of which meter ~zero:**

| plant | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Ravenswood | 6,545 / 4,936 | 2,635 / 1,798 | 3,750 / 1,788 | 4,002 / 2,311 | 892 / 77 |
| Astoria | 3,513 / 1,449 | 2,754 / 677 | 2,408 / 1,205 | 4,270 / 1,571 | 2,557 / 578 |

### 1.2 Long Island (the other pro-rata limb) — the footprint outside NYC

- **Northport 2516, 2023:** 1.173 → 1.115 TWh (lay-up share 0.016).
- **Barrett 2511, 2025:** 0.594 → 0.525 TWh (0.081).
- Every other LI plant-year: unchanged. Port Jefferson 2517 is already excluded (nyiso-140).
- **Cheapest-first limbs:** Capital_Hudson ST_GAS is unchanged by construction.

### 1.3 G-FOOTPRINT (zero LP)

In every year, CONTROL and ARM are **byte-identical** on `pmax`, `pmin`, `heat_rate`,
`availability`, `zone_idx`, `vom` and `mc_base`.

- `min_gen` differs on 12 rows (16 in 2023). Every one is a pro-rata reliability-floor row of NYC or
  LI ST_GAS.
- The ARM **never raises** a floor.
- Changed plants: {2490, 2500, 8906} in 2021, 2022 and 2024; + 2516 in 2023; {2490, 2511, 8906} in
  2025.

### 1.4 The coefficient disclosure (reported, not armed)

The limb's own statistic (cool-day p25 of NYC steam CAMPD gross ÷ floor basis, hourly, pooled over
the identification span 2023–2025) on the model's own arrays:

| basis | p25 |
|---|---|
| unmasked | 0.228 |
| masked | **1.049** |

On the masked basis the statistic is **greater than 1**, and the basis is zero in 3,246 of 26,280
hours: the NYC steam availability already carries nyiso-177's pre-existing outage over-booking
(G3, open). A basis-matched masked coefficient is therefore **not identifiable**. `floor_pct` stays
at its frozen 0.1663, which is also the precedent miso-173 and ercot-256 set for their masks
("LEVEL untouched").

### 1.5 A measured overlap, reported

Astoria's paired boilers (31RH/32SH, 51RH/52SH) carry **identical** stop windows. The guard books
one boiler's copy as outage and the other's as lay-up, so outage + lay-up exceeds 1 in 7,692 hours
of 2023 (max 1.83).

The mask clips the basis at zero, so a stopped turbine is simply unforced. The mask is not wrong
here, but the split classification of one turbine stop is a **pre-existing extract defect**, and a
likely contributor to nyiso-177's open over-booking. It is routed, not absorbed. Ravenswood
partitions cleanly (sum ≤ 1.05).

## 2. The mechanism (`reliability_floor_layup_window_mask`, default off)

- `scenarios.py` field, registered in `_CACHE_KEY_OPTIONAL_FIELDS` / `_DEFAULTS` (drop `"False"`) and
  `_BACKCAST_ONLY_OVERLAY_FIELDS` in the same commit.
- Consumer `scripts/run_calibration.py::_reliability_floor_layup_shares`. It returns `None` unless
  the field is set **and** `mode == "backcast"` **and** `outage_source == "historic"`.
- Engine `model/interchange/core.py::inject_reliability_floor(layup_removed=...)`, pro-rata branch
  only, keyed `(plant_code, artifact_class(plant_group))` exactly as the outage overlay keys
  availability.
- **Resolver extension** (the one nyiso-177 §7.5 named): `outages.unit_layup_csv_for_iso` and
  `unit_layup_removed_fractions` take the overlay's own selector flags (`per_unit_crosswalk`,
  `merit_order_guard`, `hour_grain` → `campd-unit-outages-layup-perunitmerithour-NYISO.csv`). They
  route by the same `per_unit_crosswalk`, and default False, so `mustrun_layup_window_mask` and
  `netload_drag_layup_window_mask` read exactly what they always read.
- **Rules:**
  - 21: zero free parameters.
  - 13: backcast-only; same-year lay-up windows have no forward analogue, exactly like the outage
    windows the same detector writes.
  - 19: no new floor, no membership change, no stacking.
  - 18: population by measured conduct, never a class or plant list.
- **Unit tests:** `tests/unit/model/test_reliability_floor.py::TestReliabilityFloorLayupWindowMask`
  and `TestLayupCompanionResolver`.

## 3. G-DRIFT (rule 29 (b)), keeper basis `54ac9e1a` → lane base `d5d5e0e8`

`git diff 54ac9e1a d5d5e0e8 -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib scripts/replay_keeper.py data/raw/_validation-source data/raw/reference data/raw/NYISO-AS data/raw/_processed-legacy data/raw/eia-860 data/raw/campd-unit-outages*NYISO* data/raw/gas-prices`
touches 7 files. **Every hunk is INERT:** each is NWPP-NEXT-3's `nwpp_demand_plant_basis` (default
off, gated `iso == "NWPP"`, absent from the NYISO recipe).

| file | hunk |
|---|---|
| `scenarios.py` | the field + its two cache-key registrations + a `TIER_TAGS` entry |
| `eia930/demand.py`, `runner.py`, `run_calibration{,_full}.py` | threading the flag into `load_demand`, whose one changed branch is `iso == "NWPP" and (...)` |
| `eia930/envelopes.py` | NWPP-only helpers and an import |
| `data/raw/reference/nwpp_plant_basis_energy.csv` | an NWPP artifact |

**Form 4 stands.** The keeper's committed 2022–2025 bundle and its stamped 2021 bundle are the
controls; no control solve is spent.

**This lane's own diff:** the field is default off, and its consumer returns `None` before any read
when off (byte-inert, unit-tested). `check_cache_key_registration` is OK (882 fields / 337
registered). The lay-up resolver's new arguments default to the old file and routing.

## 4. Pre-registered expectations (fixed now, so they cannot be written to fit)

- **Direction:**
  - NYC ST_GAS ↓ in every year, largest in 2021 and 2023, smallest in 2025.
  - LI ST_GAS ↓ slightly in 2023 (Northport) and 2025 (Barrett).
  - The displaced energy moves to CC / imports / other steam. NYC price rises slightly in hours
    where the floor was setting it down.
- **Magnitude.** The removed floor is −2.05 / −0.70 / −2.21 / −0.82 / −0.27 TWh (2021–2025). Of
  that, the part inside the keeper's own **binding** hours (probe column
  `removed_floor_twh_in_binding_h`) is **NYC 1.36 / 0.28 / 1.12 / 0.40 / 0.10 TWh** and LI 0 /
  0 / 0.05 / 0 / 0.06 TWh. The rest was floor under economic dispatch and cannot move it.
  - **Prediction:** NYC ST_GAS −0.1 to −1.4 TWh per year, with the binding bound as the
    first-order ceiling. The LP re-dispatches part of it economically, and a lower NYC ST
    commitment can raise the price that re-dispatches it.
  - **2023:** Ravenswood −0.63, Arthur Kill −0.39, Astoria −0.10 at most.
  - **2021:** Ravenswood −1.18 at most.
  - Whether C1 moves toward or away from its band is **not predicted and not a criterion**. NYC
    steam is over EIA-923 in every year, so NYC moves toward it; LI is under, so LI moves away.
- **C8 ST_GAS forced share falls** in every year: the numerator loses floor energy. Watch for the
  gas bridge (`nyiso_gas_commitment_bridge`) picking up forcing on newly decommitted steam.
- **D-4:** the `reliability_floor × ST_GAS` unit-conduct FAIL rows at **8906 (2023, 0.105 TWh)** and
  **2500 (2021, 0.312 TWh)** lose most of their floored energy. Whether each row clears is reported;
  it is not a criterion. No **new** reliability-floor D-4 FAIL row appears (the mask only removes
  floor).
- **C3a** moves up slightly (less must-take steam energy).

## 5. The recipe: five shards, one per year (rule 36), pinned to this document's commit SHA

```
uv run python scripts/replay_keeper.py results/calibration/<BUNDLE> --years <Y> \
  --set reliability_floor_layup_window_mask=true \
  --out-dir results/calibration/nyisonext_<Y> 2>&1 | tee results/calibration/nyisonext_<Y>/solve.log
```

- `<BUNDLE>` = `nyisostg_2021` for Y = 2021, `nyisostg_span` for 2022–2025.
- The keeper recipe (F1 flags, the LDC leg, dynamic reserves, `hydro_ror_split`) rides in the
  bundle's `meta.json`. The ONE added field is the mask.

## 6. Leg acceptance (the parent refuses a leg that fails any check)

`scripts/probes/nyisonext_compose_span.py --pin <this SHA>`:

- **S0 pin:** `git.basis_sha` = the pin, and `dirty` = false.
- **S1 config:** the keeper flags + `nyiso_ldc_generator_delivered_gas`,
  `nyiso_dynamic_reserve_requirements` and **`reliability_floor_layup_window_mask`** true; the
  offer-curve block equals the keeper's.
- **S2 inputs:** `campd_unit_outages` `ee778a87…` and `thermal_tranches` `a3bbd6ef…` sha256 equal
  the keeper's.
- **S5 footprint:** the solve log carries both the keeper's LDC line (42 rows, 6 plants) and
  `reliability_floor_layup_window_mask ARMED`.

## 7. Reporting and promotion (fixed now)

- **Report, per year, at full magnitude**, each differenced against the keeper's committed bundle:
  - C1–C8;
  - ST_GAS TWh vs EIA-923, by zone and by plant;
  - the D-4 rows;
  - price bias / MAE vs RT.
- **Promotion rule.** The arm removes forcing the model's own outage pipeline classified as laid
  up, and moves nothing else, so it is **structurally more faithful by construction**. It is
  promoted unless:
  1. a leg fails acceptance; or
  2. a protective criterion (C6 / C8) newly fails without passing C8's provenance + shape
     escalation (rule 21); or
  3. the arm creates a **new** `reliability_floor` D-4 unit-conduct FAIL row, which would falsify
     the construction.

  A regression elsewhere (C1 at LI, C3a/b, price MAE, the determination) is **reported, not a bar**
  (owner guidance: a structurally more faithful run may be a keeper even if some gates regress). It
  is never promoted on MAE alone.
- **If promoted (rule 35):**
  1. enumerate the year set first ({2021, 2022, 2023, 2024, 2025});
  2. register 2022–2025 composed as the keeper;
  3. register 2021 stamped to it (`--holdout-year 2021`);
  4. run `audit_keepers`;
  5. prune the outgoing keeper, `--keep` the new stamped 2021 run, `--force-uncite`;
  6. run `check_promotion_completeness`.
- **Rule 28 (b):** the NYISO cell `reliability_floor_layup_window_mask` moves O → K / R with this
  evidence.
