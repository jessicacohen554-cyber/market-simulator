# FINDING — D5 crossover CO2 derivation: the three-ISO CO2 miss is dominated by a scoring-taxonomy drop, not by dispatch volumes and not by the emission-rate derivation

**Lane:** capacity-expansion D5 (director refresh #14, `docs/handoffs/capx-director-ledger-2026-08.md` §0k) ·
**Session:** capx-d5-crossover-co2 · **Date:** 2026-08-30 · **Zero-solve:** yes — every number below
is computed from committed artifacts; nothing was solved, tuned, re-scored, or registered, and no
board surface was edited.

---

## 0. Headline

The T1-X crossover CO2 misses in ERCOT (−49/−43/−51 %), PJM (−45/−42/−57 %) and MISO
(−63/−60/−77 %) are **dominated by a measurement defect in the crossover scorer, not by the
forecast leg's dispatch or its emission-rate derivation**. The crossover fleet carries its entire
coal fleet under the generic model class `COAL` (`config/plant_taxonomy.py` canonical class), while
the bench's per-class CO2 intensities are keyed by coal rank (`COAL_PRB` / `COAL_LIGNITE` /
`COAL_BIT` / `COAL_WC`). `scripts/score_crossover.py::model_co2_mt_fullplant` iterates over the
**bench's** intensity keys only, so the model's entire coal generation — 32–86 TWh (ERCOT), 86–164
TWh (PJM), 168–273 TWh (MISO) per year — contributes **zero** to the scored model CO2. At ~1.0
tCO2/MWh, that single dropped term is:

- **MISO: 97–117 % of the entire miss** (its fuel volumes are nearly perfect — the pattern the
  charter flagged);
- **PJM: 75–98 % of the miss**;
- **ERCOT: 46–103 % of the miss** (the rest is real volume error, see §3);
- **NYISO (control): exactly zero** — it has no coal, every model class lands on a bench intensity
  key, and its small +10/+10/+4 % miss is honest gas-volume error. The discriminant the charter
  hypothesized (a material coal fleet) is confirmed, but the shared mechanism is the **scoring
  drop**, not fuel-volume error and not the rate derivation.

Two corollaries, both established from the same committed artifacts:

1. **The forecast emission-rate derivation chain is NOT implicated.** Comparing the model's own
   physical CO2 (dispatch × own rates, committed as `co2.model`) against a bench-intensity
   reconstruction of the *identical* mix (coal mapped), the model's own rates agree with the
   same-year bench intensities within **±5 % in every ISO-year** (§2, "own-rate" column). The
   multi-year-CAMPD-conditioned forward rates (`docs/handoffs/emissions-co2-rate-plan-2026-07.md`)
   are doing their job.
2. **As constructed, FC-4's co2 metric cannot measure rate error at all** — it applies bench
   (actual) intensities to the model mix on both sides, so the scored miss is *by construction*
   volume/mix + class-mapping. The pre-registered volume-vs-rate split therefore resolves
   degenerately on the scored basis (rate ≡ 0); the rate leg is measured separately in §2 via the
   physical-vs-bench-rate comparison.

This is a **derivation/scoring defect (fixable), not an honest input gap**: it is the third
instance of an already-known model-vs-bench class-grain seam, of which the other two instances were
found and patched (`_family_volume` in the same scorer; `PLANT_GROUP_MEMBERS` in
`calibration_verdict.py`, rubric v2.8) while the CO2 leg was left on the broken grain. §5 gives the
repair lane and the pre-declared post-repair expectations.

---

## 1. Measured object, artifact identity, and pre-declared directions

### 1.1 Live verdicts ↔ committed artifacts

Numbers were read from the LIVE verdict records in `frontend/data/forecast/ff-verdicts.json`
(keys `ercot-t1x`, `pjm-2023-2027-crossover-ffr3a3-t1x`, `miso-2023-2027-crossover-ffr3a4-t1x`,
`nyiso-t1x`), then decomposed on the committed crossover score artifacts:

| verdict key | committed artifact decomposed here | agreement |
|---|---|---|
| `ercot-t1x` (FFR-3A-2) | `results/hindcast/ercot-2023-2027-crossover-ffr2a/ERCOT/499ee0856d28e343/crossover_score.json` | co2 2023/24 exact (49.18/42.74); 2025 51.2 vs verdict 50.6 |
| `pjm-…-ffr3a3-t1x` | `results/hindcast/pjm-2023-2027-crossover-ffr2a/PJM/ba25b72007084b1e/crossover_score.json` | co2 2023 exact (45.12); 2024/25 42.2/57.3 vs verdict 40.4/54.2 |
| `miso-…-ffr3a4-t1x` | `results/hindcast/miso-2023-2027-crossover-ffr2a/MISO/9277cfc6773d187c/crossover_score.json` | co2 2023 exact (63.33); 2024/25 59.9/77.1 vs verdict 58.9/75.5 |
| `nyiso-t1x` (capx-D10) | `results/hindcast/nyiso-2023-2027-crossover-capxd10/NYISO/7323dc2ddabc95c7/crossover_score.json` | **exact identity** — the verdict's `cache_epoch` is this bundle's cache key |

The ERCOT/PJM/MISO live verdicts were re-measured on later re-solves (sessions FFR-3A-2/-3A-3/-3A-4)
whose full score JSONs are **not** committed (only `results/ffr3a3/scorecard/scorecard.json` and
`results/ffr3a4/RESULT-miso-t1x-2026-08-04.md` survive; the scorecard's `crossover_score` paths
point at uncommitted `results/ffr3a3/t1x/...` trees). The committed `ffr2a` bundles agree with the
live verdicts within ≤ 2.9 pp on every co2/coal/gas row, with identical signs and identical
structure, and MISO's RESULT doc records its co2 values (63.33/58.87/75.46) reproducing at +0.0000
against the ffr3a2 comparator — the defect found here is representation-level (class taxonomy) and
invariant across those re-solves. Decomposition is therefore on the committed record, as a
zero-solve lane must be.

### 1.2 Input vintages — verified, not inferred

- **NYISO (control):** the bundle commits `run_config.json`. Verified directly:
  `mode="forecast"`, `eia860_vintage_year=2023`, `outage_source="statistical"` (no backcast
  overlay), `use_plant_emission_rates=True` + `use_plant_emission_rates_v2=True` (the forward
  emission-rate derivation armed), `plant_level_fleet=False`, `use_campd_bins=True`.
- **ERCOT / PJM / MISO:** the committed bundles carry **no `run_config.json`** — that is exactly
  the FC-7 `run_config` FAIL row on each live verdict, and this lane cannot manufacture one.
  The committed config record is each bundle's `meta.json`: `kind="crossover"`,
  `vintage_year=2023`, `start/end 2023–2027`, `crossover_forward_year=2026`,
  `gas_price_path="hindcast_realized"`, `crossover_forward_gas_path="mid"`. The legs were produced
  by `scripts/run_capacity_hindcast.py --crossover --vintage 2023` (EIA-860 2023-vintage
  initialisation; harness header, lines 14–38) and scored by `scripts/score_crossover.py`.

### 1.3 Pre-declared directions (recorded before any decomposition arithmetic ran)

Recorded verbatim to the session scratchpad before any intensity arithmetic, on the basis of the
verdict rows and the per-family volume rows alone:

- **ERCOT:** expect VOLUME-dominated in 2023–24 (coal −35/−44 %, gas −20/−10 %); expect 2025
  (coal **+38 %** yet CO2 −51 %) to be inexplicable by volume alone → a second (rate/basis) term.
- **PJM:** expect MIXED — coal −13/−25 % with gas ≈ 0 cannot mechanically reach −45/−54 % at
  plausible intensities → a material non-volume term every year.
- **MISO:** expect RATE/BASIS-dominated — coal volumes within ±5 %, gas −9.5/−15 %, CO2 −63/−77 %.
- **NYISO (control):** expect both terms small; expect whatever term the three share to be ABSENT.
- Mechanistic suspicion, also pre-declared: `model_co2_mt_fullplant` iterates bench intensity keys,
  and the family rows list `model_only_classes=["COAL"]` — if the shared term is a taxonomy drop it
  is a derivation defect, not an input gap; control prediction: NYISO has no dropped fossil class.

Adjudication against these in §4.

---

## 2. The decomposition

### 2.1 Method — exact, on the scored basis

The FC-4 co2 metric (`scripts/calibration_verdict.py::score_co2`, reused by
`score_crossover.py:555–581`) compares:

```
S  =  Σ_c (gmModel[c] + btmClass[c]) × intensity[c]      (model, full-plant basis)
E  =  bench co2.egrid                                    (actual, same basis)
scored signed error = (S − E) / E
```

where `intensity`/`btmClass`/`egrid` come from the committed bench
(`frontend/data/backcast/bench/<ISO>/<year>.json.gz`, `bench.co2`) and `gmModel` is rebuilt from
the crossover DispatchResult with classes taken **verbatim** from `plant_group`
(`score_crossover.py::build_gmmodel`, lines 188–217). Because the summation runs over the
**bench's** intensity keys, any model class absent from that dict contributes zero.

The scored miss then decomposes **exactly** (no model re-run; per-class model TWh from the
committed `fuelmix.forecast_per_class`, per-class actual TWh from the bench `classFull`, family
totals from the committed `family_volume` rows):

```
S − E =  T_gas   Σ over gas classes of intensity × (model − actual) TWh
      +  T_coal  ī_coal × (model_coal_family − actual_coal_family)     [volume at actual rates]
      +  DROP    − ī_coal × model_coal_family                          [the unmapped-COAL drop]
      +  resid   (unlisted-class net + coverage; ≤ 1.8 Mt wherever per-class rows exist)
```

with `ī_coal` = the bench's actual-coal-CO2-weighted mean coal intensity (ERCOT ≈ 1.047, PJM ≈
1.012, MISO ≈ 1.001 t/MWh; per-ISO rank spread ERCOT 1.03–1.06, PJM 0.98–1.29, MISO 0.97–1.14 —
the reallocation of the model's unsplit COAL across ranks is the only approximation in the DROP
term and its weighted value is bracketed by that tight-to-moderate range). The identity
`T_coal + DROP = −Σ_ranks intensity × actual` holds algebraically, so the split is exact given
`ī_coal`. 2023/2024 rows close to the scored miss at < 0.01 Mt. 2025 rows (marked ~) use family
totals because C1 emits no per-class gas rows for the preliminary-vintage year; their residual
absorbs within-family mix.

**Rate term.** On the scored basis the rate term is identically zero (bench intensities on both
sides). The rate leg is instead measured as: model **physical** CO2 (`co2.model` in the score file
— dispatch × the model's own rates, grid basis) minus the bench-rate reconstruction of the *same
mix* (S + ī_coal·model_coal − BTM add-back CO2). This isolates "model's own rates vs measured
same-year intensities at identical volumes".

### 2.2 Result table (Mt CO2; negative = model under actual; % of bench eGRID actual)

| ISO | year | scored miss | = T_gas | + T_coal(vol) | + **DROP** | + resid | DROP share | if COAL mapped | own-rate vs bench |
|---|---|---|---|---|---|---|---|---|---|
| ERCOT | 2023 | −84.5 (−49.2 %) | −19.8 | −22.2 | **−41.1** | −1.4 | 49 % | **−25.3 %** | −4.4 % |
| ERCOT | 2024 | −73.6 (−42.7 %) | −12.0 | −26.5 | **−33.6** | −1.4 | 46 % | **−23.2 %** | −4.8 % |
| ERCOT | 2025 | −87.0 (−51.2 %) | −17.9~ | +24.6 | **−89.2** | −4.5 | 103 % | **+1.3 %** | −2.7 % |
| PJM | 2023 | −119.2 (−45.1 %) | −4.8 | −14.8 | **−99.1** | −0.5 | 83 % | **−7.6 %** | +1.3 % |
| PJM | 2024 | −115.3 (−42.2 %) | +0.9 | −29.2 | **−86.6** | −0.4 | 75 % | **−10.5 %** | +1.6 % |
| PJM | 2025 | −167.7 (−57.3 %) | −25.5~ | +27.0 | **−163.9** | −5.3 | 98 % | **−1.3 %** | +1.3 % |
| MISO | 2023 | −184.7 (−63.3 %) | +2.9 | +1.8 | **−188.1** | −1.4 | 102 % | **+1.2 %** | −2.1 % |
| MISO | 2024 | −171.0 (−59.9 %) | +5.1 | −8.6 | **−165.7** | −1.8 | 97 % | **−1.9 %** | −1.9 % |
| MISO | 2025 | −230.5 (−77.1 %) | −27.1~ | +60.0 | **−270.5** | +7.1 | 117 % | **+13.4 %** | −2.9 % |
| NYISO | 2023 | +2.7 (+10.1 %) | +3.4 | 0 | **0** | −0.7 | 0 | +10.1 % | +1.5 % |
| NYISO | 2024 | +3.0 (+10.3 %) | +3.6 | 0 | **0** | −0.6 | 0 | +10.3 % | +1.0 % |
| NYISO | 2025 | +1.1 (+3.9 %) | +1.7~ | 0 | **0** | −0.6 | 0 | +3.9 % | +2.9 % |

"If COAL mapped" = the scored error had the model's COAL family been valued at `ī_coal`
(= scored miss − DROP, as % of actual): **the counterfactual FC-4 co2 row after the scorer
repair**, computable today with zero solves. "Own-rate vs bench" = the §2.1 rate leg, grid basis,
as % of the bench-rate reconstruction.

Reproduction: every input above is in the four `crossover_score.json` files (§1.1) and the twelve
bench files `frontend/data/backcast/bench/{ERCOT,PJM,MISO,NYISO}/{2023,2024,2025}.json.gz` —
`S = egrid × (1 + forecast_signed)` from `dispatch_skill.metrics.co2`, per-class model TWh from
`dispatch_skill.metrics.fuelmix.<year>.forecast_per_class`, family totals from
`dispatch_skill.family_volume.<fam>.<year>.forecast_detail`, physical CO2 from `co2.model`,
intensities/BTM/classFull/egrid from `bench.co2` / `bench.classFull`.

### 2.3 Cross-checks

- **Closure:** 2023/24 rows close to the committed scored miss at < 0.01 Mt (exact identity).
- **Physical corroboration (PJM):** `S_known + ī_coal × model_coal − BTM_co2` = 239.8 Mt vs the
  independently committed physical CO2 = 242.8 Mt (2023) — two constructions, two code paths,
  1.3 % apart. Same agreement in 2024/25 and in MISO/NYISO; ERCOT agrees within 5 %.
- **Actual-side basis:** the FC-4 actual is `bench.co2.egrid`, and the bench's own
  `Σ (classFull + btm) × intensity` reproduces it to ≈ 0.0 Mt in every gated ISO-year — the
  actual side is internally consistent. (The separate `co2` block in the same score file —
  `model` 106.0 vs `actual` 191.4 Mt for ERCOT 2023 — is the **capacity-track** number scored by
  `score_capacity_hindcast.py`, whose "actual" is a CAMPD **state-sum** for ERCOT/PJM
  (`actual_co2_by_year`: whole-TX ≈ +11 % vs ERCOT eGRID; PJM's 13-state sum ≈ +54 % vs PJM
  eGRID). That footprint overcount does not enter the FC-4 dispatch metric decomposed here, but
  any future reader comparing the two co2 blocks in one score file should know they are on
  different actual bases — worth a note in the successor PR, not a term in this miss.)

---

## 3. Trace of the dominant term — the full derivation chain

1. **The model class.** `COAL` is the canonical *generic* coal class in
   `src/market_sim/config/plant_taxonomy.py::PLANT_CLASSES` (first row). The crossover fleet
   carries it as `plant_group` on every coal unit: ERCOT's CAMPD bin rows are labelled `COAL` in
   `data/raw/reference/custom-bin-assignments.csv` (cf. `campd_bins.py:1172` matching
   `plant_group == "COAL"`), and the non-ERCOT per-plant EIA-860 fleets derive class from
   `fuel_type == "coal"`. The rank split (`COAL` → `COAL_PRB`/`COAL_BIT`/`COAL_LIGNITE`/`COAL_WC`,
   via `coal_supply_class` on the plant code) is applied **only in the calibration report chain**
   — `scripts/run_calibration_full.py::_coal_supply_class` / `_model_class_for_unit` ("Coal is
   returned as the bare `COAL` here; the caller splits it into the supply class") — which is why
   every keeper backcast payload scores cleanly on split classes while the crossover leg does not.
2. **The scorer.** `scripts/score_crossover.py::build_gmmodel` (lines 188–217) rebuilds `gmModel`
   from the crossover DispatchResult taking `plant_group` **verbatim** — no rank split. Its
   `_FUEL_TO_CLASS` fallback map (lines 94–109) is the discriminant's sharp edge: the gas
   fallbacks land on real bench keys (`gas_cc→CC_REGULAR`, `gas_ct→CT_PEAKER`, `gas_st→ST_GAS`),
   but coal's fallback is `"COAL"` — the one fossil key no bench intensity dict contains (verified
   in all 12 bench files: ERCOT keys PRB/LIGNITE, PJM BIT/PRB/WC, MISO BIT/LIGNITE/PRB, NYISO none).
3. **The drop.** `model_co2_mt_fullplant` (lines 266–286) computes
   `Σ_{c ∈ bench intensity} (gm[c] + btm[c]) × intensity[c]` — iterating the bench's keys, so
   `gm["COAL"]` is simply never read.
4. **The seam was already known — twice.** The same file's `_family_volume` (lines 412–483)
   documents this exact grain mismatch in its docstring — "*its whole coal fleet reports in one
   unsplit `COAL` bucket … aggregating the records would report a model coal volume of ZERO — a
   100 % error that is a scoring artifact, not a dispatch result (ERCOT 2023: 39.2 TWh read as
   0.0)*" — and reconciles it at family grain **for the gas_twh/coal_twh rows only** (L-VAL
   follow-up (b)). `scripts/calibration_verdict.py::PLANT_GROUP_MEMBERS` (v2.8, line ~676) bridges
   the identical seam for C8 materiality. The CO2 leg is the third consumer of the seam and the
   only one never bridged. The C1 fuelmix crossover rows are also still on the broken grain
   (model `COAL_PRB`/`COAL_LIGNITE` read 0.0 vs actual 45.1/15.3 TWh — the spurious ~60 TWh
   per-class FAIL rows in the same score files).
5. **What the rate chain shows.** The forecast emission-rate derivation
   (`use_plant_emission_rates`/`_v2`, spec + `docs/handoffs/emissions-co2-rate-plan-2026-07.md`)
   is validated by this decomposition, not implicated: own-rate vs bench-intensity agreement is
   within ±5 % everywhere (table §2.2, last column) — including at NYISO where the scored basis
   is fully mapped end-to-end.

**Secondary observations pinned during the trace** (context for the residual terms, not new
defects): the crossover fleet *representation switches* after the vintage/first solve years —
`n_gen` 2048→1069 (PJM, at 2024), 2205→1364 (MISO, at 2024), 630→466 (NYISO, at 2024), 623→233
(ERCOT, at 2025) — and the 2025 legs of all three coal ISOs flip coal to **over**-dispatch
(T_coal +24.6/+27.0/+60.0 Mt) against preliminary-vintage 2025 actuals (the family rows are
committed `gated: false` for exactly that reason). Both belong to the existing FC-4 volume story,
not to the CO2 instrument.

---

## 4. Adjudication

### 4.1 Against the pre-declared hypothesis (§1.3)

- **The discriminant IS the material coal fleet** — confirmed, and the NYISO control behaves
  exactly as the design demanded: the term the three share (DROP) is identically zero there.
- **But the shared mechanism is neither of the two pre-registered arms.** It is not fuel-volume
  error at correct rates (MISO's volumes are nearly perfect) and not the forecast emission-rate
  derivation (own rates within ±5 % of measured intensities everywhere). It is the scoring
  instrument dropping the model's coal class.
- Per-ISO pre-declared directions: **MISO** "rate/basis-dominated" → confirmed as **basis**
  (97–117 % DROP; rate proper −2/−3 %). **PJM** "mixed" → in fact DROP-dominated (75–98 %), with
  real coal-volume error (−15/−29 Mt) second. **ERCOT** "volume-dominated" → half-confirmed:
  2023/24 split ≈ 50 % real volume (−42.0/−38.5 Mt across coal+gas) vs 49/46 % DROP; the
  pre-declared "2025 needs a second term" was right — DROP is 103 % of the 2025 miss.
  **NYISO** → both terms small as declared; its +10 % misses are honest gas over-dispatch
  (+12.4 TWh across CC classes), the crossover measuring a real input gap.

### 4.2 Derivation defect vs honest input gap

**Derivation defect — fixable, scorer-side.** The admissibility test that separates the two: an
honest input gap is what FC-4 exists to measure (forward fuel prices vs delivered, statistical vs
actual outages, weather-year). The DROP term measures none of those — it is the instrument reading
the forecast leg's coal CO2 as zero because of a class-key mismatch between two internal
representations. The proof it is not an input gap: the *same physical dispatch* scored at bench
rates with coal mapped lands at −25 %…+13 % (§2.2 "if mapped"), and the independently-committed
physical CO2 corroborates those levels (§2.3).

**What remains after repair is the honest signal** (pre-declared in §5.2): ERCOT's 2023/24 real
volume gap (co-moving with its already-FAILing coal_twh −35/−44 % and gas_twh −20/−10 % rows —
same root, already on FC-4's books), MISO's 2025 evolved-fleet coal over-dispatch, and NYISO's gas
over-dispatch. Those stay with their existing lanes; no new mechanism is proposed for them here.

---

## 5. Recommended successor lane(s)

### 5.1 The repair (one lane, small, zero-solve)

**Fix the class-grain seam in the crossover scorer, at the same place the volume rows fixed it.**
In `scripts/score_crossover.py`, either (in order of preference):

- **(a) Split the model's coal at gmModel-build time** — in `build_gmmodel`, map each coal
  generator to its supply class via the canonical chain (`coal_supply_class` on `plant_code`,
  falling back to generic `COAL` exactly as `run_calibration_full.py::_coal_supply_class` does).
  This puts the crossover on the keeper's own basis, and repairs the spurious C1 fuelmix coal rows
  (~60 TWh phantom error per ISO-year) in the same stroke. One taxonomy chain, no second map
  (rule 19 `[R-ONE-MECH]`); **or**
- **(b) minimal:** value an unmapped model `COAL` bucket in `model_co2_mt_fullplant` at the
  bench's actual-coal-CO2-weighted mean intensity — the same family-grain reconciliation
  `_family_volume` already performs for volumes, with `PLANT_GROUP_MEMBERS` (v2.8) as the
  in-repo precedent. Smaller diff; leaves C1's coal rows on the broken grain.

**Admissibility (rule 13):** this is a scorer-side repair — no model input, rate, or curve
changes; nothing is fitted to any residual; the mapping is the repo's canonical plant-code → coal
rank chain, fully forward-reproducible and condition-responsive (a future coal fleet maps by the
same rule). No solve is needed to re-measure: rescore the committed bundles
(`scripts/rescore_forecast_verdicts.py` / `score_crossover.py --rescore` path) and re-emit the
verdicts. **Rule 28:** this tests no mechanism and adds no `ScenarioConfig` field — no matrix
cell; the repair PR needs no matrix row.

### 5.2 Pre-declared expectations for the re-measure (so it cannot be back-fitted)

On the committed ffr2a/capxd10 artifacts, repair (a) or (b) moves FC-4 co2 to (±0.5 pp for (b);
(a) may differ by up to ~2 pp from per-plant rank weighting; live ffr3a-leg re-measures carry the
same ≤ 3 pp offsets their volume rows already show):

| ISO | 2023 | 2024 | 2025 | expected FC-4 co2 outcome (existing bands, K unchanged) |
|---|---|---|---|---|
| ERCOT (K=1.5) | −25.3 % | −23.2 % | +1.3 % | 2023/24 still FAIL (>15 %) — the honest volume gap; 2025 PASS |
| PJM (K=3.0) | −7.6 % | −10.5 % | −1.3 % | 2023/25 PASS, 2024 CAVEAT — co2 leaves PJM's FC-4 FAIL set |
| MISO (K=3.0) | +1.2 % | −1.9 % | +13.4 % | 2023/24 PASS, 2025 CAVEAT — co2 leaves MISO's FC-4 FAIL set |
| NYISO (K=1.5) | +10.1 % | +10.3 % | +3.9 % | unchanged (control: repair must be a no-op here) |

The NYISO no-op is the repair's own control: any NYISO movement means the fix touched more than
the unmapped-coal seam. MISO's coal_twh and PJM's gas_twh rows must also be untouched (the family
rows were already grain-reconciled).

### 5.3 What is explicitly NOT recommended

- **No model/fleet retuning in response to these CO2 rows** — they were mismeasured.
- **The residual misses stay with their owners:** ERCOT's crossover volume gap (already measured
  by its coal_twh/gas_twh FAIL rows and its capacity-track retirement/addition FAILs) is FC-4's
  real finding and belongs to the ERCOT forecast lane; the three ISOs' 2025 coal over-dispatch
  belongs with the evolved-fleet/2025-actuals-vintage question (family rows are `gated: false`
  there); NYISO's gas over-dispatch is D10's open item.
- **Optional hygiene note for the successor PR** (report-only): the capacity-track co2 block's
  ERCOT/PJM state-sum actual (§2.3) is on a different basis than the FC-4 actual in the same
  file; worth a basis label so nobody decomposes across the two again.

---

## 6. Guardrail attestation

Zero solves; zero registrations; no `ff-verdicts.json` / `program-status.json` / dashboard /
matrix / backcast-surface edits; no out-of-training year touched (every read was a committed
2023–2025 artifact already on the record); no measured CO2/CEMS value was fed back into any input
(actuals used solely to attribute the measured miss); data profile stayed `code` (no raw-source
read was needed — the whole chain is committed score files + committed benches + repo source).
In-flight branches checked at start (`ercot-241`, `miso-190` present; `caiso-224` already gone):
no conflict — this lane touches only `docs/handoffs/`.
