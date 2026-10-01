# FINDING — caiso-146: measured loaded CT heat rates are a real, one-sided CAISO mispricing; armed, PROMOTED

**Session:** caiso-146 (2026-07-31). **Branch:**
`claude/caiso-measured-ct-heat-rates-003f79`.
**Lever:** `measured_ct_heat_rates`, mechanism-matrix §5.2 queue item 6, CAISO
cell **`U` → `K`**.
**Pre-registration:** `PREREG-caiso146-ct-heat-rates-2026-07-31.md`, committed
and pushed (`abaa952`) **before either arm solved**.
**Arms:** `2026-07-31-caiso146-control` (`caiso146_control_A`) /
`2026-07-31-caiso146-ct-heat-rates` (`caiso146_ctheatrate_B`).
**Outcome:** **NEW KEEPER `2026-07-31-caiso146-ct-heat-rates`**, determination
**CALIBRATED-WITH-CAVEATS** (0 FAILs, the same 2 ledgered caveats carried
forward, protective 0/1).

---

## A. What was wrong

eGRID publishes **one plant-average ANNUAL heat rate per plant**, and
`fleet/eia860.py::_rows_to_generators` hands that number to every combustion
turbine in the non-ERCOT fleet. For a peaker it is wrong twice:

1. **It is an annual average, not a loaded rate.** A peaker's annual average
   blends startup fuel, part-load hours and shutdown tails into the figure that
   sets its offer. The rate that sets an offer is the rate *at load*.
2. **At a mixed facility it is not even the right technology's rate.**

CAISO's **Glenarm (plant 422)** is defect #2 in the flesh. The model carries
**4 `CT_PEAKER` units (138.4 MW) and 2 `CC_REGULAR` units (84 MW)** there, all
on a single eGRID figure of **10.3895**. CAMPD tags the units separately —
GT3/GT4 are `Combustion turbine` (11.42 / 11.35 all-hours), GT5 is
`Combined cycle` (9.40). The artifact prices the turbines at their own measured
**10.6702** and leaves the CC blocks on eGRID. Glenarm is one of only **two**
plants where the measured rate is *dearer* than eGRID's — the blend was hiding
it.

## B. The artifact (STEP 1, no LP)

```
python scripts/data/derive_campd_ct_heat_rates.py --iso CAISO --years 2023 2024 2025 --detail
```

`data/raw/_processed-legacy/campd_ct_heat_rates_CAISO.csv` — **43 plant rows**,
**all `flag == "ok"`**, zero excluded by the physical band; 87 unit rows.

### B.1 Coverage — 76.8 % of capacity, **99.9 % of the class's measured energy**

| axis | covered | total | share |
|---|---|---|---|
| capacity | 5,848 MW | 7,616 MW | 76.8 % |
| **metered CAMPD CT energy** | **8.015 TWh** | **8.025 TWh** | **99.9 %** |

The energy axis is the one that matters for an offer swap, and it is why the
capacity number is not a hole:

| exclusion cause | plants | MW | % class MW | metered CT GWh |
|---|---|---|---|---|
| **A** — no CAMPD account at all | 90 | 1,627.8 | 21.4 % | **0.000** |
| **C** — has CT units, never cleared the loaded window | 1 | 141.0 | 1.9 % | 10.119 |

**Cause A is the Part-75 reporting boundary, not a selection effect.** Those 90
plants have a median size of **2.2 MW** and **zero metered CT energy** — there
is nothing to swap in, so they correctly keep eGRID. Cause C is one plant
(Stanton 60698). **No adverse selection:** covered capacity-weighted eGRID HR
**10.819** vs uncovered **11.004** — the applied map is not skimming a tail.

### B.2 Direction — **one-sided in CAISO**, unlike the NYISO and PJM precedents

* **cheaper: 41 plants / 5,649 MW.** **dearer: 2 plants / 198 MW** (Glenarm,
  Greenleaf One).
* `|Δ| > 0.5` MMBtu/MWh: **40 / 43**; `> 1.0`: **24**.
* **capacity-weighted −1.159 MMBtu/MWh (−10.7 %)**; generation-weighted
  **−0.884 (−8.9 %)**.
* ratio model/measured — min 0.943, median 1.117, **max 1.808**.

This is stated as CAISO's own result, not a transferred one (rule 25
`[R-ISO-SCOPE]`): NYISO found errors in *both* directions and PJM came out net
**+**0.229. The largest CAISO moves are exactly what defect #1 predicts — the
lowest-CF peakers carry the most start fuel in their annual average
(Grapeland 15.5477 → 9.5563, Center 14.5803 → 9.5251, Gilroy 11.5838 → 8.9884).

### B.3 One data-integrity limitation, sized and deliberately NOT repaired

**Delano (58122, 60.5 MW)** reads 6.5725 MMBtu/MWh — below any real
simple-cycle machine, yet **above** the derive's 6.0 plant-level floor, so the
guard passes it. Its loaded-hour rates run **p05 = 0.81 / p25 = 3.20** against a
median 7.89: a **broken heat-input channel**, not a machine. (Gilroy and
Grapeland, by contrast, sit tightly inside p25–p95 ≈ 9.3–10.1 — that is what a
real machine looks like.)

`scripts/probes/_caiso146_hourly_hr_integrity.py` measures the reach. **It is a
property of the SHARED derive in every ISO, not a CAISO defect:**

| ISO | sub-floor loaded hours | energy-wt unit HR as-is → hour-screened | Δ |
|---|---|---|---|
| CAISO | 2,537 / 73,346 (3.46 %) | 8.9312 → 9.0456 | **+0.114** |
| NYISO | 3,704 / 151,014 (2.45 %) | 10.2142 → 10.3360 | +0.122 |
| PJM | 8,435 / 544,586 (1.55 %) | 10.7227 → 10.8034 | +0.081 |
| MISO | 1,290 / 433,271 (0.30 %) | 11.2300 → 11.2439 | +0.014 |

**Not acted on here, on purpose.** An hour-grain screen would move the input of
**three committed keepers** (nyiso-89, pjm-137, miso-106) — not a CAISO
session's call (rules 24 `[R-FROZEN-DERIVE]` / 25). Filed as a cross-cutting
audit item with the numbers attached. The pre-registered **K6** gate proves the
verdict does not hinge on it (§D).

## C. Result — CT_PEAKER moves materially toward reality

Single-flag A/B, `--years 2023 2024 2025` in one invocation per arm, both at the
same HEAD.

### C.1 The class this lever is about

| year | control A | arm B | Δ | actual | A/act → B/act |
|---|---|---|---|---|---|
| 2023 | 1.088 | **1.727** | **+0.638** | 4.128 | 26 % → **42 %** |
| 2024 | 0.423 | **0.634** | **+0.211** | 4.326 | 10 % → **15 %** |
| 2025 | 0.272 | **0.455** | **+0.183** | 2.374 | 11 % → **19 %** |

The prereg predicted **+0.1 to +0.8 TWh** and explicitly predicted the gap would
**not** close. Both held.

**This answers caiso-119 R4 directly.** R4 attributed the CT_PEAKER defect to
"priced out" and set a standing guardrail: *"marking peaker offers down until
4 TWh appears is rule-1/13 forbidden."* This lever clears that guardrail by
construction — the magnitude is set by the meter, not by the gap. All three
plants R4 named rise:

| plant | 2023 | 2024 | 2025 |
|---|---|---|---|
| Panoche | 0.0632 → 0.0878 | 0.0171 → 0.0257 | 0.0082 → 0.0126 |
| Sentinel | 0.2270 → 0.3602 | 0.0745 → 0.1203 | 0.0341 → 0.0600 |
| Walnut Creek | 0.2230 → 0.3286 | 0.0790 → 0.1191 | 0.0423 → 0.0697 |

**A mispriced offer was part of R4's defect — but only part.** Even fully
re-priced on measured rates the class reaches 42/15/19 % of actual, so the
remaining 2.4–3.7 TWh is *not* a heat-rate problem. That is the same conclusion
nyiso-89 reached for NYISO, arrived at independently on CAISO's data.

### C.2 Where the energy came from

| class | 2023 | 2024 | 2025 | direction vs actual |
|---|---|---|---|---|
| CC_REGULAR | −0.399 | −0.130 | −0.093 | 94→93 / 94→93 / 90→90 % — **~1 pp worse** |
| ST_GAS | −0.165 | −0.061 | −0.037 | 35→22 % (worse) / 565→515 % / 221→180 % (**better**) |
| import | −0.067 | −0.023 | −0.058 | — |

A ~1 pp cost on CC_REGULAR against a **5–16 pp** gain on the most
under-produced class in the ISO. ST_GAS improves in two of three years.

### C.3 Prices — reported, not targeted

CA demand-weighted λ: **56.10 → 55.68 / 37.43 → 37.29 / 38.28 → 38.16**
(−$0.42 / −$0.15 / −$0.12), the direction §5.4 of the prereg predicted.

* **C3a** improves in all three years — +3.6 → +2.8 %, +8.2 → +7.8 %,
  **+11.3 → +11.0 %** — and 2025 stays outside the ±10 % band.
* **C3c is BIT-UNCHANGED**: model 0 h > $200 in every year of both arms. The
  re-price buys **zero** tail hours, exactly as prereg §5.5 predicted.

## D. Pre-registered gates

| gate | verdict | evidence |
|---|---|---|
| **K1** flag fidelity | **PASS** | B `true` / A `false`; 43/43 rows applied |
| **K2** control integrity | **PASS** *(as pre-registered)* | arm A reproduces the keeper's criterion statuses — same `{C3a, C3c}` failing set, all else PASS. **See §E: byte-level it does NOT, and that is a separate finding.** |
| **K3** liveness | **PASS** | max \|Δ CT_PEAKER\| **1660 / 1510 / 1709 MW** vs a 50 MW floor |
| **K4** single delta | **PASS** | `run_config` differs in exactly one boolean |
| **K5** year span | **PASS** | `[2023, 2024, 2025]`; no out-of-training year (rule 22) |
| **K6** Delano sensitivity | **PASS** | ex-Delano the class move keeps its sign at **80 / 84 / 66 %** of size (+0.513/+0.176/+0.121 vs +0.638/+0.211/+0.183 TWh) |

### D.1 Protective gates — hold, and **improve**

| gate | control A | arm B | floor |
|---|---|---|---|
| C7 D-1 `profile_r` CT_PEAKER | 0.903 / 0.951 / **0.837** | 0.885 / 0.936 / **0.864** | ≥ 0.80 |
| C7 D-1 `cv_ratio` CT_PEAKER | 2.635 / 2.048 / 2.087 | **1.613 / 1.805 / 2.172** | ≥ 0.50 |
| C8 D-2 forced share | 0.0032 / 0.0104 / 0.0012 | **0.0016 / 0.0055 / 0.0007** | ≤ 0.15 |

**2025 `profile_r` — the outgoing keeper's most exposed number, with only 0.036
of headroom, and the one the prereg flagged as the single biggest risk —
IMPROVES 0.837 → 0.864.** `cv_ratio` moves *toward* the measured off-peak
variability in two of three years. C8 falls because the denominator grew. D-4
off-window binding stays 0.000 on every floor; this arm arms no floor.

*(D-1's overall `passed: false` is the pre-existing ST_GAS 2024/2025
`profile_r`, identical in the keeper, the control and arm B — 0.244/−0.042,
0.245/−0.037, 0.229/−0.032. Not caused by this arm.)*

## E. OPEN ITEM — the outgoing keeper's committed bytes no longer reproduce at HEAD

The zero-delta control **does not** reproduce the committed caiso-139 keeper:

| year | max \|Δ\| class-hour | CC_REGULAR | import | total gen | CA λ |
|---|---|---|---|---|---|
| 2023 | 2,097 MW | +0.445 TWh | −0.466 | identical to 3 dp | +$0.19 |
| 2024 | 1,669 MW | +0.458 | −0.457 | identical | +$0.06 |
| 2025 | 3,240 MW | +0.854 | −0.866 | identical | +$0.14 |

**It is a CC ↔ import margin drift and it does NOT touch CT_PEAKER**
(+0.007 / 0.000 / 0.000 TWh). The A/B signal is an order of magnitude larger and
both arms sit at the **same HEAD** with one flag between them — which is exactly
why a same-HEAD control was solved rather than comparing arm B against the
committed keeper (the neiso-69 drift-control precedent). **The comparison is
clean; the keeper's stored bytes were not.**

**Promoting this arm re-bases CAISO's keeper onto HEAD, so the committed bytes
reproduce again.**

**The cause is NOT identified here.** 15 commits touched `src/market_sim/`
between the old keeper's basis (`fa9971b`) and HEAD (`db02071`); candidates
include `36b5421` (deleting 17 duplicate definitions shadowing `fleet/models.py`
imports), `edf2f7d` (the caiso-142 export-sink seam, flag-gated default-off) and
`8d1be7e` (carrying the caiso-139 dump-guard flag through the `solve_dispatch`
facade — which landed **after** the keeper solved on a dirty branch sha).
Bisecting needs full solves per candidate, so it is filed here rather than
absorbed silently or guessed at.

## F. Governance

* **Rule 13 `[R-MEASURED]`** — a unit's loaded heat rate is a physical
  characteristic of the machine; it regenerates forward from the same pipeline
  and responds to changed conditions. An **input**, never an outcome fed back.
* **Rule 14 `[R-ACCURATE]`** — the charter. Measured beats an annual plant
  average, independent of the residual.
* **Rule 19 `[R-ONE-MECH]`** — one flag, nothing stacked.
* **Rule 24 `[R-FROZEN-DERIVE]`** — zero fitted parameters; the artifact
  re-derives only on a CAMPD data change, and any such commit must cite it.
* **Rule 25 `[R-ISO-SCOPE]`** — CAISO's artifact from CAISO's data; no verdict
  or parameter transferred from the PJM / NYISO / MISO `K` cells.
* **Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only. CAISO holds **no**
  calibration-complete marker; none was written, and no out-of-training year was
  solved, scored or registered.
* **The ledger** — the two caveats are the **owner's** act of 2026-07-30
  (caiso-145), carried forward unchanged in substance with magnitudes
  re-measured. **No new caveat, no new slot** (still 2 of 3 non-protective, 0 of
  1 protective, 0 FAILs). C3c is bit-identical; C3a-2025 moved 0.3 pp, inside
  the 1.0 pp trigger fixed in the prereg, so **no leave-one-year-out re-scoring
  was required**.
* **Prereg §8 honoured** — the lever was selected off the §5.2 queue on
  caiso-119's CT finding, not to target a ledgered gate. C3a's improvement is
  **reported, not claimed as justification**, and neither caveat is closed.

## G. DO-NOT-REDO (binding on successors)

1. **Do not re-derive `campd_ct_heat_rates_CAISO.csv` against a residual.**
   Rule 24: source-data change only, and the commit must cite it.
2. **Do not add a CAISO-scoped heat-rate multiplier, band or exclusion.** The
   error is source noise, one-sided here but plant-specific; no scalar can stand
   in for it, and a CAISO-only screen on a shared derive is a rule-25 breach.
3. **Do not re-open "CT_PEAKER is priced out" as a heat-rate question.** It is
   now measured and answered: measured loaded rates are worth **+0.638 / +0.211
   / +0.183 TWh**, reaching 42/15/19 % of actual. The remaining 2.4–3.7 TWh is
   **not** a heat-rate defect. caiso-119 R4's guardrail still binds — any
   successor lever must be a real obligation-keyed mechanism with a cited D-4
   window, never an offer markdown sized to the gap.
4. **Do not treat the §B.3 hour-grain screen as a CAISO lane.** It is
   cross-cutting (all four ISOs measured) and touches three committed keepers'
   inputs; it needs its own charter, not a CAISO calibration session.
5. **Do not quote the C3a improvement as evidence for this mechanism**, and do
   not propose it as a C3a-2025 or C3c lever. Both caveats remain owner-adopted
   measured-input limitations, reopenable only by the two unfunded intakes named
   at caiso-145.
6. **The §E drift is not this lever's defect and must not be re-litigated as
   one.** If it is investigated, it is a reproducibility lane over
   `fa9971b..db02071`, scoped to the CC ↔ import margin.
