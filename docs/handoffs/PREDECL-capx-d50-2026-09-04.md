# PRE-DECLARATION — capx D50: the CCS retrofit capex-scaling repair (D49 §1.5 seams 1–3), built default-off, A/B'd on the ERCOT / NEISO / PJM t1f surfaces

**Lane:** capx D50 (Fable). Branch `claude/capx-d50-ccs-capex-scaling-hkwpbe` (the
harness-assigned name for the charter's `claude/capx-d50-ccs-capex-scaling`), FRESH off
`origin/main` `a35c9f9` (PR #4721). **Date:** 2026-09-04. **Pushed BEFORE any repair code
exists on the branch** — the finding grades every line of §2–§5 at full magnitude, misses
included, and nothing here is re-narrated after a result is read.

**What this lane does.** Builds the three seams D49 §1.5 named, as ONE gated
`ScenarioConfig` field, **default-off**, zero DOF; proves the off path byte-inert on the
committed `ercot-t1f` recipe; solves three SUFFIXED t1f A/B arms (`<iso>-t1f-d50-ccscapex`,
never a bare key); measures the blast radius a default flip would carry; returns the
arming question to the owner. **NOTHING ARMS.** No keeper, shard verdict, marker or
backcast artifact moves. Rules 5, 12, 13, 14, 21, 22, 24, 25, 27, 28 hold.

**Data profile:** `ercot, neiso, pjm` — this container arrived with `data/raw` fully
hydrated and an EMPTY `data/clean`; the full `regenerate_clean.py` tree is rebuilding in
the background (the D46 §2 / D48 §1 prerequisite) so every arm solves on the same input
surface its control did.

---

## 0. Disclosure — what was read and computed before this text was written

D49 §1 in full (the 14 reconstructed rows, the PJM/MISO like-for-like, the seam
statement), D41 (the ATB basis, the §6.2 blast-radius precedent), D44 §1 (the b′-1
default-flip mechanics), D46 §4.5 (the CCS axis in the three t1f windows), D48 (the
Phase-0/Phase-1 gated-field pattern), spec §5.6, `ccs.py::apply_ccs_retrofit`,
`NEW_ENTRY_COSTS`, `HEAT_RATE_BINS`, the matrix `ccs_retrofit_screen` row and every
shard's cell, and the three control ledgers' `ccs_retrofits` rows (unit id + MW only —
the retrofit-log decomposition is not persisted, D41 §7 item 5).

**Computed zero-solve, and disclosed as an INPUT to §2 rather than a prediction:** the
scaled-bar test of §1.2 applied to every converting row D49 reconstructed (its committed
`results/calibration/capxd49_ccs_reconstruction.json` carries each row's `hr`, `er`,
`eford`, `vom`), on the learned-capex path the ARM will actually see (no own retrofit GW
fed back — computed with the repo's own `CumulativeDeployment` + `_adjust_retrofit_capex`)
and on each ISO's resolved gas path. The NEISO rows were NOT reconstructed by D49 and the
NEISO fleet cannot be rebuilt until `data/clean` exists; §2.3 therefore states NEISO's
expectation from the threshold arithmetic alone, and a unit-grain addendum (§2.3a) is
pushed before the repair code if the fleet loads in time — never after a solve.

---

## 1. The repair, as it will be built (rule 28c: one field, one row, six cells)

### 1.1 The field

`ScenarioConfig.ccs_retrofit_capex_co2_scaling: bool = False` — GATED, default OFF,
registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at
`"False"` (the shared cluster, tuple end, HOUSE-3), `TIER_TAGS` tier 2, exposed on
`run_full_horizon.py` as `--ccs-retrofit-capex-co2-scaling`. The off path never enters
the scaling branch and never touches the candidate filter, so it is byte-identical by
construction; §4 proves it on the committed key.

### 1.2 Seam 1 — capex scaled to captured CO2 flow (zero DOF)

```
captured_t_per_mwh = er_host × ccs_retrofit_capture_rate            (what the screen already credits §45Q on)
captured_ref       = ccs_retrofit_capture_rate × hr_ref × FUEL_CO2_FACTOR_PER_MMBTU["gas_cc"]
                   = 0.90 × 6.3 × 0.057 = 0.32319 t/MWh
retrofit_capex_per_mw = adjusted_capex_kw × 1000 × (captured_t_per_mwh / captured_ref)
```

`hr_ref = min(HEAT_RATE_BINS["gas_cc"]) = 6.3` MMBtu/MWh (EIA Table 8, newest H-class) —
the SAME host heat rate `new_entry._emerging_lcoe` charges the ATB `gas_cc_ccs` increment
against (`base_hr = min(HEAT_RATE_BINS["gas_cc"].values())`), so the retrofit and
new-build screens size the ATB capture island to one reference host. (ATB 2024's own NG-CC
F-frame heat rate is 6.36; the 1 % difference is stated, and the model-internal value is
used because it is the basis D41's increment is already applied to.) Every term is an
existing cited constant; nothing is fitted (rule 21/23). The Wright's-Law learning
(`_adjust_retrofit_capex`) still applies to the reference-host increment BEFORE scaling.

**What linear capex scaling does and does not close, stated now.** Per captured tonne the
§45Q credit net of transport is $70 (85 − 15); the ATB increment amortized over the 12-yr
window at the reference host is $110,300 / (0.323 × 8,322 h) ≈ **$41/t** at the hour
ceiling, plus the ΔFOM ($35,000/MW-yr) and the per-MWh HR-penalty + VOM adder, which stay
sized per MW / per MWh and therefore DILUTE per tonne as `er` rises. So under seam 1 the
retrofit margin is still increasing in host emissions above a threshold; the threshold
moves from `er ≥ ~0.46` (D49 §1.2) to the values in §2, it does not vanish. That residual
(a per-tonne ΔFOM and VOM adder) is a fourth seam this lane does NOT build — D49 named
three and the charter says build those; it is recorded in the finding for the director.

### 1.3 Seam 2 — CHP hosts EXCLUDED from the retrofit candidate set (option 1, cited)

A unit whose `plant_group == "CC_CHP"` is not a retrofit candidate when the gate is on.
Published basis, three limbs: (i) the cost basis — NREL ATB 2024 NG-CC-CCS and the NETL
NGCC-retrofit series (D41 §3) are electric-only NGCC costings; no published capture-island
$/kW exists for a cogeneration host's combined flue gas at the electric plant's cost basis;
(ii) the rate basis — the fleet carries CAMPD CEMS CO2 per NET ELECTRIC MWh, which for a
CHP charges the steam host's fuel to electricity (eGRID publishes a CHP-adjusted rate
precisely because the unadjusted one is not the electric rate; the model has no
useful-thermal-output intake to apply that allocation); (iii) the margin basis — the
screen's uplift is the electric-market margin only, and a cogen capture project is
decided on the industrial host's steam economics the model does not represent. Option 2
(rate on electric-only fuel) needs the EIA-923 Page-3 useful-thermal-output intake and is
routed, not built. This is a candidate-set rule on a physical attribute the fleet already
stamps (`plant_group`, loader provenance), not a class-name commitment gate (rule 18 is
about commitment physics; this is eligibility of a cost basis).

### 1.4 Seam 3 — the p55470 row flagged, not filtered

`data/raw/reference/custom-bin-assignments.csv` row `CC_CHP,Houston,9,H_CHP9,55470,Green
Power 2,611.0,34.75,…`: `Plant_Avg_HR_MMBtu_MWh = 34.75` and the derived CO2 rate 2.061
t/MWh are a CHP plant's CEMS fuel charged to net electric MWh. Recorded as a data-quality
item in `data/raw/reference/README.md`; the row stays exactly as it is.

---

## 2. Expected conversions, per ISO, under the repair (graded at full magnitude)

**The arithmetic (from `ccs.py`, D49 §1.2, with the capex scaled).** A host can convert
only if it clears at the HOUR CEILING:

```
Δ    = 63·er − 0.12·hr·gas − 8 + 0.9·er·carbon         ($/MWh per in-merit hour)
ceil = Δ·(1−EFORd)·8760 − 35,000                        ($/MW-yr)
bar  = capex_learned/12 × (0.9·er / 0.32319)            (the scaled bar; flat bar × er/0.3591)
```

Learned capex the ARM sees (no own GW fed back, the repo's tracker from
`CumulativeDeployment.initial()`): 2028 **1,323.6**, 2029 **1,271.8**, 2030 **1,232.3** $/kW
(the controls' 2029–2030 values are lower, 1,218 / 1,201 / 1,132, because their own
conversions fed the tracker). Gas (mid HH + basis): ERCOT 3.17 / 3.34 / 3.98; PJM 4.34 /
4.51 / 5.15; NEISO 4.77 / 4.94 / 5.58; MISO 3.97 / 4.14 / 4.78. Carbon: ERCOT / PJM / MISO
0; NEISO RGGI **29.83 / 31.92 / 34.15** $/t (the resolved program price).

**Two structural facts that make the 2028 predictions near-deterministic.** (1) The 2028
screen reads the 2027 price signal, and the arm's 2026–2027 solves are identical to the
control's (the gate touches nothing before the first screen year), so the arm's 2028
candidate pool and surface ARE the control's; only the bar is higher. Hence the arm's 2028
converting set ⊆ the control's 2028 converting set wherever the control was not cap-bound
(ERCOT, PJM). (2) A host below the reference rate (`er < 0.359`) gets a cheaper island
under seam 1 but can still clear only if `220,010·er ≥ 999·hr·gas + 101,576` (2028,
carbon 0), i.e. `er ≥ 0.46` even at `hr → 0` — no sub-reference host can appear.

### 2.1 ERCOT (control `ercot-2026-2030-d46-remeasure`, key `873d8c0e6cab52ae`: 2028 11 rows / 2,130.9 MW; 2029 3 / 610.9; 2030 0)

| 2028 row | MW | er | hr | ceil $k | flat bar | scaled bar | ceil/scaled | clears |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| CC_CHP_Houston_p55464_econ | 352.8 | 0.530 | 5.94 | 157.6 | 110.3 | 162.9 | 0.968 | N (and CHP-excluded) |
| CC_CHP_Houston_p55464_peak | 117.6 | 0.530 | 8.61 | 149.1 | 110.3 | 162.9 | 0.916 | N (CHP) |
| CC_CHP_Houston_p55470_econ | 213.8 | 2.061 | 34.75 | 868.9 | 110.3 | 633.0 | **1.373** | **Y at the ceiling — EXCLUDED by seam 2** |
| CC_REGULAR_Houston_p56806_committed | 294.5 | 0.553 | 11.13 | 153.1 | 110.3 | 169.9 | 0.901 | N |
| CC_REGULAR_Houston_p56806_econ | 187.4 | 0.553 | 9.94 | 156.9 | 110.3 | 169.9 | 0.924 | N |
| CC_REGULAR_South_p3631_committed | 106.0 | 0.561 | 10.95 | 157.8 | 110.3 | 172.3 | 0.916 | N |
| CC_REGULAR_South_p3631_econ | 67.5 | 0.561 | 9.78 | 161.5 | 110.3 | 172.3 | 0.938 | N |
| CC_REGULAR_South_Central_p4937_committed | 316.0 | 0.561 | 11.33 | 156.8 | 110.3 | 172.4 | 0.910 | N |
| CC_REGULAR_South_Central_p4937_econ | 201.1 | 0.561 | 10.12 | 160.7 | 110.3 | 172.4 | 0.932 | N |
| CC_REGULAR_West_p56233_econ | 53.9 | 0.468 | 8.21 | 117.8 | 110.3 | 143.7 | 0.819 | N |
| CC_REGULAR_West_p56349_econ | 220.2 | 0.470 | 8.53 | 118.0 | 110.3 | 144.4 | 0.817 | N |
| **2029 rows** (capex 1,271.8, gas 3.34) | | | | | | | | |
| CC_REGULAR_South_Central_p7900_econ | 278.6 | 0.439 | 7.37 | 104.1 | 106.0 | 129.6 | 0.803 | N |
| CC_REGULAR_West_p56233_committed | 84.6 | 0.468 | 9.20 | 113.1 | 106.0 | 138.1 | 0.819 | N |
| CC_REGULAR_West_p56349_committed | 247.7 | 0.470 | 9.38 | 113.7 | 106.0 | 138.8 | 0.819 | N |

**P1 (HIGH, near-deterministic): ERCOT converts 0 rows / 0 MW in 2028.** Every regular-CC
row sits at 0.82–0.94 of the scaled ceiling bar; the one row above it is the p55470 CHP
row seam 2 removes. **P2 (HIGH): 0 in 2029 and 2030** — the highest-er regular hosts
(p4937 / p56806 / p3631, er 0.55–0.56, hr 10–11.3) need `er ≥ 0.58–0.60` at 2029 gas and
`≥ 0.60` at 2030's $3.98 gas; none of the control's ceiling-clearing 3.79 GW carries it
(D49 §1.2: the regular-CC hosts' rates are physical, 0.47–0.56). Window total: **0 MW vs
2,741.8 MW**. Falsifier for P1: any 2028 conversion. Falsifier for P2: a regular-CC
conversion in 2029–2030 with `er < 0.58`.

### 2.2 PJM (control `pjm-2026-2030-d45r-remeasure`, key `321f04e9060787f0`: 2028 16 rows / 2,832.6 MW; 2029 3 / 752.1; 2030 0)

| 2028 row | MW | er | hr | ceil $k | scaled bar | ceil/scaled | clears |
|---|---:|---:|---:|---:|---:|---:|---|
| CC_CHP p10030 committed / econ | 18.5 / 36.4 | 0.515 | 7.34 / 6.99 | 136.5 / 138.0 | 158.1 | 0.863 / 0.873 | N (CHP) |
| CC_CHP p10633 committed / econ | 93.1 / 269.0 | 0.645 | 8.08 / 7.70 | 201.4 / 203.0 | 198.0 | **1.017 / 1.025** | Y at ceiling — **EXCLUDED** |
| CC_CHP p10805 committed / econ | 13.6 / 10.9 | 0.658 | 7.43 / 7.08 | 211.4 / 212.9 | 202.2 | **1.045 / 1.053** | Y — EXCLUDED |
| CC_CHP p55216 committed / econ / peak | 55.3 / 90.2 / 48.5 | 0.729 | 6.66 / 6.34 / 9.19 | 251.7 / 253.0 / 240.7 | 223.8 | **1.124 / 1.130 / 1.075** | Y — EXCLUDED |
| CC_REGULAR p55337 committed / econ | 228.8 / 501.6 | 0.606 | 7.91 / 7.33 | 181.6 / 184.1 | 186.0 | 0.976 / **0.990** | N |
| CC_REGULAR p55710 committed / econ | 306.9 / 235.7 | 0.528 | 6.81 / 6.31 | 145.5 / 147.7 | 162.1 | 0.898 / 0.912 | N |
| CC_REGULAR p55976 committed / econ | 374.2 / 408.2 | 0.607 | 7.73 / 7.16 | 183.2 / 185.7 | 186.5 | 0.983 / **0.996** | N |
| CC_CHP p58933_econ | 141.7 | 0.685 | 10.36 | 212.9 | 210.5 | 1.011 | Y — EXCLUDED |
| **2029** (capex 1,271.8, gas 4.51): CC_REGULAR p55701 committed / econ | 230.2 / 422.0 | 0.507 | 7.58 / 7.02 | 130.0 / 132.6 | 149.6 | 0.869 / 0.886 | N |
| CC_CHP p58933_committed | 99.9 | 0.685 | 10.88 | 208.8 | 202.3 | 1.032 | Y — EXCLUDED |

**P3 (HIGH): PJM converts 0 rows in every year (0 MW vs 3,584.7 MW).** The nearest regular
host, p55976_econ, sits at 0.996 of the bar AT THE CEILING — it would need ≥ 8,725 in-merit
hours of 8,760 on the 2027 surface, which no PJM CC has. **P4 (HIGH, the seam-2 reading):
seam 2 is LOAD-BEARING at PJM** — 722.2 MW of the control's 2028 conversions (p10633,
p10805, p55216, p58933) and 99.9 MW of 2029's clear the scaled ceiling at 1.01–1.13 and
are removed ONLY by the CHP exclusion; under seam 1 alone PJM would still convert
≈ 0.5–0.8 GW in 2028. The finding reports the seam-1-only ceiling count as the measure of
how much the CHP rule carries. Falsifier for P3: any conversion; for P4: fewer than 500 MW
of the control's CHP rows clearing the scaled ceiling in the finding's census.

### 2.3 NEISO (control `neiso-2026-2030-d46-remeasure`, key `6690e4d6d66bc819`: 2028 17 rows / 2,999.6 MW; 2029 23 / 2,994.4; 2030 10 / 2,948.6 — the cap binds every year)

Under RGGI the avoided-carbon leg adds `0.9·er·carbon` per hour, so the net ceiling slope
in `er` is `(63 + 0.9·29.83)·8,322 − 307,157 ≈ 441,000` $/MW-yr per t/MWh (2028), against
`999·hr·gas + 101,576`: a NEISO host clears the scaled ceiling at **`er ≥ 0.31` (hr 7) …
`0.34` (hr 10)** — i.e. essentially every gas-CC in New England (physical rate at hr 6.3 is
already 0.359). The scaled bar therefore does NOT unbind the cap at NEISO.

**P5 (HIGH for 2028, MED for 2029–2030): the 3 GW/yr cap still binds in every NEISO year;
window MW within cap-packing granularity of the control (2,850–3,000 MW each year; total
8,700–9,000 vs 8,942.6).** This is the ISO where the repair is expected to change WHO
converts, not HOW MUCH: **P6 (MED): the composition re-ranks toward LOWER-er (efficient)
hosts** — payback is now `capex·(er/0.359)/uplift`, which restores the docstring's
"efficient hosts win" ordering that D49 §1.4 showed inverted — and the control's CC_CHP
rows (2028 p50002 117.0 + p58159 22.7 MW; 2029 p1595 204.8 + p57666 13.3 + p58084 8.7;
2030 p58084 8.4) leave the set under seam 2 and are back-filled by regular-CC MW.
Graded: MW-weighted mean `er` of the arm's converting set ≤ the control's in each year.
Falsifier for P5: any NEISO year below 2,700 MW. A NEISO year where the arm converts MORE
MW than the control by ≤ 60 MW is cap-packing, not a STOP (§3).

**§2.3a (to be pushed as an addendum before the repair code if the rebuilt fleet is
available in time; otherwise stated as not pre-registered):** the per-unit table for the
control's 50 NEISO rows on the scaled bar, the same form as §2.1.

### 2.4 MISO — D49 §5 item 2, restated under the repair (solved ONLY if PJM contradicts §2.2)

D49 §5 item 2 expected the PJM/MISO corrected-constant re-solve to bind the cap in 2028
because 5.0–5.7 GW of gas_cc clears at the ceiling. Under the repair that expectation is
**withdrawn**: MISO's 14 converting 2028 rows are all CC_CHP (0 under seam 2; 7 of 14 would
survive seam 1 alone, 1,546 MW); its 2029 regular-CC rows (p1007, p7985, er 0.576–0.578)
sit at 0.985–1.003 of the scaled ceiling bar at the arm's capex — at most p7985_econ
(334.5 MW) marginal; 2030's 17 rows are all ≤ 0.72. **P7 (MED, not solved here): MISO
under the repair converts ≤ 0.35 GW in the window vs 8,983.6 in the stale S123 ledger.**
The PJM result decides whether MISO is solved (charter): it is solved only if §2.2 misses.

### 2.5 The whole-fleet census (the finding's §1 table)

For each of ERCOT / NEISO / PJM (and MISO), the count and MW of gas-CC that clear the
scaled ceiling in 2028 with and without seam 2, against D49's flat-bar census (ERCOT 3.79
GW, PJM 5.74, MISO 5.00). Prediction **P8 (MED)**: carbon-0 ISOs ≤ 0.5 GW each with seam 2
(ERCOT ≤ 0.1 GW: only p55470 clears and it is CHP); NEISO ≥ 80 % of its gas-CC fleet.

---

## 3. STOP conditions (binding, checked before any registration)

1. **More MW anywhere (rule 14).** The arm converts MORE MW than its control in any
   ISO-year where the control was NOT cap-bound (control < 2,940 MW), OR exceeds a
   cap-bound control year by > 60 MW (one cap-packing unit). Either is the
   wrong-direction signature: STOP, diagnose from the ledger, no registration until
   explained.
2. **A sub-reference host converting at carbon 0** (`er < 0.359` in ERCOT or PJM) — §2's
   fact (2) says it cannot; if it does, the arithmetic in §1.2 is not the screen's.
3. **Any realized cache key ≠ its §4 value**, or any collision with a committed key.
4. **The byte-inertness proof failing** (§4): the repair does not land at all.

---

## 4. Keys, posture, cost — resolved at HEAD `a35c9f9` through the harness path

Every control key was re-resolved via `run_full_horizon.reference_config(iso, 2026, 2030,
False, golden_posture=True)` → `apply_iso_scenario_defaults` → `cache_key()` and **all six
match their committed bundles**; the arm keys are EMULATED by inserting
`ccs_retrofit_capex_co2_scaling: true` into the same hash payload (exact for a registered
cache-optional field, which drops at `False` and enters at `True`):

| ISO | control (bare key, untouched) | arm `<iso>-t1f-d50-ccscapex` (expected) | solved this lane |
|---|---|---|---|
| ERCOT | `873d8c0e6cab52ae` (`ercot-t1f`) | **`0c3e9cd5b5993bdf`** | yes (∥ NEISO) |
| NEISO | `6690e4d6d66bc819` (`neiso-t1f`) | **`18515067bf4d2fbe`** | yes (∥ ERCOT) |
| PJM | `321f04e9060787f0` (`pjm-t1f`) | **`167e65187f32056b`** | yes (solo) |
| MISO | `8d8bc63a0d4378a9` (`miso-t1f`) | `f3f96e14bb75c9d9` | only if §2.2 misses |
| NYISO | `cc7d1050a8090c76` | `b9e4c79e188ab01e` | no (blast radius only) |
| CAISO | `772b1e5abc7fc80c` | `29f8eb372810195f` | no (blast radius only) |

**Byte-inertness proof (before any solve):** after the field lands, `ercot-t1f`'s recipe
re-resolves to `873d8c0e6cab52ae` with the field absent AND with it explicitly `False`;
the pinned default key `4c6b03ae098b6e3e` / backcast `8211c72bb1960adc` are unmoved
(`test_persisted_identity.py`); `check_cache_key_registration.py` clean; and a 24-hour
trivial-fixture screen with the gate off is byte-identical to HEAD's (unit test).

**Posture, every arm:** `--golden-posture` 2026–2030, `fossil_announced_exits_enabled=True`
(D44), the D41 constants 1521.4 / 65.0, the ISO's shipped `default_scenario_overrides`
(ERCOT's scarcity/lookahead family, NEISO's ORDC family — read off the resolved config, not
`args`), `forecast_xyear_warmstart=False`, the field `True`. Nothing else differs from the
control. Scored `forecast_verdict.py --tier t1f --summary … --run-config … --dof-ledger …`
with the ledger built by `build_forecast_dof_ledger.py` from the arm's own
`run_config.json` (the D46 instrument-parity step — declared now: where a control's FC-7
reads CAVEAT for a missing ledger (ERCOT), the arm may read PASS for that row and that is
an instrument difference, never a model gain). Registered
`register_forecast_run.py --summary … --kind t1f --label d50-ccscapex` → run id
`<iso>-2026-2030-d50-ccscapex` → `VERDICT_MAP` row → suffixed key `<iso>-t1f-d50-ccscapex`.
The bare keys, `program-status.json` and every board block are untouched.

**Cost (D45-R / D46 measured rates):** ERCOT ~12 min / 3.3 GB, NEISO ~8 min / 3.3 GB
(paired, rule 12), PJM ~21–28 min / 8.8–9.9 GB (solo). MISO if triggered ~24–65 min. STOP
at 2× the measured price; years never trimmed.

---

## 5. The FC rows (graded at full magnitude)

**P9 (HIGH): no FC-1 or FC-2 row changes STATUS in any of the three arms; every
determination is unchanged** — ERCOT HOLD→HOLD (FC-1 FAIL `[I12, I3]`; FC-2 row1 FAIL,
row3 PASS, row4 PASS, row6 FAIL non-gating), PJM HOLD→HOLD (FC-1 FAIL; FC-2 row1 FAIL,
row3 PASS, row4 FAIL; FC-8 CAVEAT), NEISO PROMOTE→PROMOTE (all PASS; FC-2 row4 backstop
share 1.2 % ± 0.5). Reason: a retrofit keeps the unit's MW, zone and accreditation, so
I4/I7/I12 and every adequacy row are capacity-identical; what moves is 2028–2030 dispatch
at the margin (a converted unit bids `hr×1.12×gas + vom + 8 + 0.9·er·15` with no §45Q in
the dispatch bid, spec §5.6 known simplification), which changes prices, dump and CO2
slightly but no gated row's status. Falsifier: any FC-1/FC-2 status flip. **Read, not
graded:** the window CO2 delta (ERCOT: the 2.74 GW of retrofits no longer capturing;
NEISO: composition only) and the I3 dump magnitude at ERCOT.

---

## 6. The blast radius the default flip would carry (measured in the finding; expectation stated now)

Under b′-1 (D44 §1) a flipped default enters the hash, so **every forecast-mode config
re-keys** — the D41 §6.2 pattern. Census at HEAD: **145 committed forecast-mode
`run_config.json`** (26 t1f windows, 16 full-horizon NEISO golden legs, 103 T1-H/T1-X
windows), of which **21 verdict keys carry a live `provenance.run_id`**. Behaviour moves
ONLY where a solve year ≥ 2028 exists and a gas-CC retrofit was decided: the six bare
t1f keys and GOLDEN-3 (`neiso-t3`); every T1-H/T1-X window ends ≤ 2027 and is
byte-identical (a cache-key formality, never a re-measure on the merits). Backcast keys
also advance (as D44's did) with byte-identical behaviour. The finding prices the
re-measure of the seven behaviour-moving keys in solve-minutes at the D45-R / D46 rates
and lists every affected key; that number goes on the owner's card.

---

## 7. Kills

- **K-a** — no parameter value moves, no second field, no scaling of ΔFOM or the VOM adder
  (recorded as residual, §1.2), no change to the cap, life floor, HR penalty or transport
  cost. A miss that "wants" a constant is routed (rule 21).
- **K-b** — rule 22: t1f 2026–2030 on forward drivers only; no holdout year; nothing scored
  against measured H1-2026.
- **K-c** — rules 13/14: no residual consulted; the sign (fewer conversions at carbon 0)
  is stated here before any solve; a NEISO re-ranking that raises MW by ≤ 60 MW is
  cap-packing and is reported as such.
- **K-d** — rule 25: three ISO readings; MISO/NYISO/CAISO receive a `U` cell for the new
  row (no transfer); ERCOT/NEISO/PJM cells carry their own measured evidence.
- **K-e** — rule 27: exact on-disk bytes pushed; every pushed file ≥ 300 lines
  (`scenarios.py`, `ccs.py`, `run_full_horizon.py`, `register_forecast_run.py`,
  `ff-verdicts.json`, the matrix base and shards, `run_config.json`s, the ledgers, the
  finding) blob-verified against the remote before the next commit.
- **K-f** — collision: D48 owns `pjm-t1h`; D51 MISO, D52 NYISO disjoint; nothing but the
  three suffixed t1f keys (four if MISO fires) is written to `ff-verdicts.json`.

## 8. What this lane commits

The field + registrations + CLI flag + the screen change + the README flag + tests
(byte-inert off, scaled bar on, CHP exclusion, `captured_ref` pinned to its derivation);
the matrix base row `ccs_retrofit_capex_co2_scaling` + a cell in all six shards; the
census probe `scripts/probes/_capxd50_scaled_ceiling_census.py` + its JSON; three (or four)
slim bundles under `results/ff-t1f-d50/<iso>/` with `.gitignore` carve-outs on the D46
template; the `VERDICT_MAP` rows and `ff-verdicts.json` entries; the ERCOT/NEISO/PJM
shard cell stamps; spec §5.6 and CLAUDE.md step-2 amendments;
`docs/handoffs/FINDING-capx-d50-2026-09-04.md` with this pre-declaration graded.
