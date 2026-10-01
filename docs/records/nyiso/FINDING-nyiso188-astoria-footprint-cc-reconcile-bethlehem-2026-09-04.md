# FINDING — nyiso-188 (`backcast-calibration` lane): the Astoria routing's remaining footprint (ramp envelopes + v2 emission rates) measured and A/B-solved; the registered `cc_capacity_reconcile` flag A/B-solved; Bethlehem 2539's applied heat rate attributed to an EIA-923 generator-filing artifact (+40 %) with the admissible instrument specified

**Session:** nyiso-188, `backcast-calibration` lane
(`claude/nyiso-188-backcast-calibration-tex4hz`), NYISO backcast-calibration
track, 2026-09-04. **Solves run: FIVE** — the same-HEAD control on the
committed artifacts (`results/calibration/nyiso188_control`, an instrument,
bit-identical to the keeper), three arms (`nyiso188_ramp`, `nyiso188_ramp_emis`,
`nyiso188_ccrecon`) and the combined promotion candidate (`nyiso188_combined`).
**Keeper at entry: `2026-09-04-nyiso-187-astoria-routing`** — NOT-YET, target
grade 5, fail set {C1-2024 `CC_REGULAR` +3.80 TWh / +3.1 pp, C3a-2025 −10.3 %
(owner-court, not touched), C3c}.
**Pre-registration:**
`results/calibration/PREREG-nyiso188-astoria-footprint-cc-reconcile-bethlehem.md`,
pushed at `40536e07` before any arm was solved; every bar below is read
verbatim. **Machine records:** `results/calibration/_nyiso188_ramp_footprint/`
(probe `scripts/probes/nyiso188_ramp_footprint.py`), the three bundles'
computed `calibration_attestation.json` (`scripts/gen_nyiso188_attestation.py`),
`results/calibration/_nyiso188_entry_shas.json`, the chain
`scripts/probes/_nyiso188_chain.sh`.

---

## 1. The result in one paragraph

Three objects, four registered solves, one promotion. **Object 1:** the
Astoria routing's two remaining artifacts are re-derived at zero parameters —
the ramp envelopes now bound Astoria Energy I and II separately and the
`(0, CC)` class-fraction fallback moves with its corrected pool (0.4907 /
0.5623 → 0.5000 / 0.5904, read by 14 small CC groups), which the LP answers
at degeneracy grain only (largest per-plant annual |Δ| 0.0005 TWh, every
criterion identical); the v2 emission-rate curate never applied the remap,
so Astoria Energy II priced CO2 at a fuel-factor default — repaired at the
curate seam, 12 rows move, its mean marginal cost falls $0.13–0.50/MWh, no
criterion moves. **Object 2:** the registered `cc_capacity_reconcile` flag
(per-plant `CC_REGULAR` LP capacity bounded at the CAMPD p99.9 demonstrated
peak, −740 MW over 12 plants, its table reproduced exactly plus the one row
the routing creates) moves the determination **NOT-YET → CALIBRATED** (grade
7, fails 0, C3c ledgered): C1-2024 `CC_REGULAR` +3.80 → +2.05 TWh and
C3a-2025 −10.3 → −6.9 %, with every regression in band and stated (C3a-2023
+4.8 → +7.9 %, C3a-2024 +0.5 → +3.8 %, C3b-2023 0.123 → 0.134). The combined
candidate (Object 1 artifacts + the flag) scores identically and is
**promoted** under the owner's standing formula — the first NYISO keeper to
read CALIBRATED; no marker is requested. **Object 3:** Bethlehem 2539's
applied heat rate 9.665 is an EIA-923 generator-filing artifact (+40 % on a
≈ 6.9–7.0 block: the steam generator's filed net generation collapses to
6 % / 0 % in 2023 / 2024 while the CTs run 8,000 h); no threshold-free
source-internal identity reaches the applied vintage, so the instrument is
specified and handed to the owner as a two-form decision, unsolved.

---

## 2. Object 1 — the Astoria routing's remaining footprint: measured, then A/B-solved

### 2.1 The ramp-envelope artifact (Arm 1R)

The committed `campd_ramp_envelopes_NYISO.csv` reproduces byte-identically
from its committed invocation with the two Astoria remap entries stripped, so
the whole diff below is the routing (rule 23: the data change is EIA-860's
plant boundary, nyiso-186 §3). Re-derived at HEAD:

| row | committed | arm | what it is |
|---|---|---|---|
| 55375 CC | 1,252 MW obs; 469 up / 622 dn; 26,106 online h | **626; 372 / 449; 25,016 h** | CT1 + CT2 only |
| 57664 CC | — (no row) | **626; 416 / 454; 26,106 h** | CT3 + CT4, new measured row |
| `(0, CC)` class fraction | 0.4907 up / 0.5623 dn (pool 26) | **0.5000 / 0.5904 (pool 27)** | the median over the corrected pool |
| CT / ST rows, every other plant | byte-identical | byte-identical | — |

**Who reads the moved fallback, at full magnitude.** Fourteen fleet CC groups
(1,355.3 MW) resolve to the `(0, CC)` row because they have no well-observed
CEMS trace: Selkirk 10725 (596.6 MW) and thirteen cogens / small CCs of
11–86 MW (Allegany 7784, Lederle 10521, CH Resources Beaver Falls 10617 /
Syracuse 10621, Carthage 10620, Cornell 50368, Indeck Yerkes 50451 / Olean
54076, Sterling 50744, Rensselaer 54034, Massena 54592, Batavia 54593, NYU
54808). Their summed up-envelope loosens 665.0 → 677.7 MW (+1.9 %) and
down-envelope 762.1 → 800.2 MW (+5.0 %). Six ST groups (2,234 MW) read the
`(0, ST)` row, which does not move. The drift is the population median
responding to a corrected population — the pool previously carried one
1,252 MW "plant" whose 469 / 622 MW envelope was two blocks' moves summed; no
constant changed (`scripts/probes/nyiso188_ramp_footprint.py`,
`results/calibration/_nyiso188_ramp_footprint/`).

### 2.2 The v2 emission-rate artifact (Arm 1RE − Arm 1R)

`curate_emissions_unit_annual.py` keyed rows on the raw CEMS `facilityId` and
did not apply `campd.CAMPD_UNIT_PLANT_REMAP`, unlike the plant-grain normalizer
and every other CAMPD-fed derive. So CT3 / CT4 sat under `plant_id` 55375 in
every year, 57664 had no row, and `apply_plant_emission_rates_v2` left Astoria
Energy II at the fleet default `heat_rate × FUEL_CO2_FACTOR_PER_MMBTU["gas_cc"]`
= 7.3792 × 0.057 = **0.4206 t/MWh** while 55375 priced at the FOUR-unit pooled
measured rate. **The repair (zero parameters):** the curate seam now applies
the same registry per `(facility, unit)` (rule 19: one registry, one seam
class; test `test_split_facility_unit_remap`), and the v2 derive gained a
year-scoped `--merge` (re-derive one ISO's rows, carry everything else
byte-frozen) plus `--out`. Re-curating NY + NJ (`states_for_iso("NYISO")`)
and re-deriving `--iso NYISO --years 2019 2020 2021 2023 2024 2025 --merge`:

| | committed | arm |
|---|---|---|
| rows | 33,250 | 33,250 |
| rows only on one side | (55375, CT3 / CT4) × 6 years | (57664, CT3 / CT4) × 6 years |
| every other row | `gross_mwh`, `heat_mmbtu`, `starts`, `op_hours` EXACT; CO2 / NOx / SO2 masses ≤ 1e-3 kg (2 rows at Astoria Gen 8906, float summation order) | |
| other-plant backcast rate, max |Δ| | 1.3e-12 t/MWh (2023), 1.1e-12 (2024), 7.4e-13 (2025) | |
| 55375 gas rate, 2023 / 2024 / 2025 | 0.3778 / 0.3807 / 0.3845 (CT1–CT4) | **0.3618 / 0.3639 / 0.3672** (CT1 + CT2) |
| 57664 gas rate | absent → default 0.4206 | **0.3947 / 0.3981 / 0.4144** (CT3 + CT4) |

NYISO parasitic factors are absent from `parasitic_load_factors.parquet` (650
plants, none in NY / NJ), so net = gross × 1.0 for every NY row on both sides
— the split is the only change. **Footprint not carried (declared):** the
2018 NYISO rows (the 2018 unit-level vintage was stripped at BLOAT-S2 and
cannot be re-derived) and the 2022 / 2026 rows (behind the one-shot
holdout-intake guard) keep CT3 / CT4 under 55375; no backcast year reads
them, but a NYISO FORECAST-mode estimator window that reaches 2026 does — a
forecast-lane item, stated here.

### 2.3 A/B, at full magnitude (control = same-HEAD replay on the committed artifacts, BIT-IDENTICAL to the keeper: 0 of 52,560 hourly zonal prices differ in every year; arms `2026-09-04-nyiso-188-ramp` and `2026-09-04-nyiso-188-ramp-emis`; G-DELTA computed: ZERO fields in both; G-INPUTS / G-DOF / G-ENGAGE PASS)

**Arm 1R (ramp) is ENGAGED but INERT at the annual grain.** The fleet reads the
re-derived artifact (61 ramp groups, 46 class-default rebases vs 45 — 57664 is
now its own measured group) and the LP responds at degeneracy grain only:

| year | price hours differing (of 52,560) | max abs Δprice | plant-hours differing | largest per-plant annual abs Δ |
|---|---|---|---|---|
| 2023 | 318 | $0.47 | 8,295 | 0.0005 TWh (Danskammer 2694) |
| 2024 | 2,565 | $0.37 | 8,150 | 0.0001 TWh (Flynn 7314) |
| 2025 | 5,307 | $1.07 | 7,231 | 0.0004 TWh (Cricket Valley 57185) |

Every scored number is identical to the keeper (C1 to 0.01 TWh, C3a to 0.1
pp, C3b to 0.001, C8 to 0.1 pp). Why: Astoria's two blocks never approach
their new separate envelopes — the largest non-outage hourly move at 55375 in
2024 is 141.6 MW against a 363 MW net envelope, and every larger move (538.6
MW, four hours) is an availability step the ramp rows exempt; the 14
fallback readers' envelopes loosen by 12.7 / 38.1 MW summed, which no hour
uses. **The ramp footprint is real in the artifact and nil in the dispatch.**

**Arm 1RE − 1R (v2 emission rates) moves Astoria's marginal cost and nothing
scored.** Astoria Energy II mean installed `mc` 25.39 → 25.06 / 29.42 →
28.92 / 42.27 → 42.13 $/MWh (−0.34 / −0.50 / −0.13); Astoria Energy I 24.17
→ 23.90 / 28.17 → 27.76 / 41.01 → 40.62 (−0.27 / −0.41 / −0.39); 57664
+0.024 / +0.028 / +0.002 TWh, 55375 +0.002 / +0.004 / +0.004; class
`CC_REGULAR` +0.017 / +0.017 / +0.002; 15,676 / 29,498 / 18,804 price hours
differ (max abs $2.18 / $3.50 / $3.62); load-weighted price 33.80 → 33.79 /
38.30 → 38.29 / 59.61 → 59.61.

| criterion | keeper | Arm 1R | Arm 1RE |
|---|---|---|---|
| C1 2024 `CC_REGULAR` | +3.80 TWh, +3.1 pp FAIL | +3.80 / +3.1 FAIL | +3.81 / +3.1 FAIL |
| C1 2023 `CC_REGULAR` / `ST_GAS` | +0.46 / +2.21 | +0.46 / +2.21 | +0.48 / +2.20 |
| C3a 2023 / 2024 / 2025 | +4.8 / +0.5 / −10.3 % | identical | +4.8 / +0.4 / −10.3 % |
| C3b | 0.123 / 0.173 / 0.192 | identical | identical |
| C8 `CC_REGULAR` / `ST_GAS` 2024 | 3.4 / 25.2 % | 3.4 / 25.2 | 3.4 / 25.2 |
| C3c / C2 / C4 / C6 | FAIL / PASS / PASS / PASS | identical (attested) | identical (attested) |
| determination | NOT-YET, grade 5, fails 3 | NOT-YET, grade 5, fails 3 | NOT-YET, grade 5, fails 3 |

**Verdict under PREREG §3 (verbatim):** no criterion flips; both arms are
**KEEPER CANDIDATES** on representation alone — the site's ramp envelopes and
CO2 / NOx / SO2 rates are now the measured ones for each block instead of a
two-block sum and a fuel-factor default, at zero parameters — and neither
buys a gate. LOYO reduces to the per-year record: the same sign in every
year (57664 gains energy as its measured rate replaces the default), largest
in 2024. Reported as rule-1 / rule-14 repairs, not levers.

---

## 3. Object 2 — `cc_capacity_reconcile` (cell U → tested)

### 3.1 The table, and what the keeper already reads from it

`derive_cc_capacity_reconcile.py --iso NYISO --mode both --years 2023 2024 2025`
reproduces the committed 14 rows EXACTLY and adds one row the routing creates:
**Astoria Energy 55375 `raise` 595.0 → 610.4** (CT1 + CT2 p99.9 on the
corrected boundary; before the routing the site's p99.9 sat inside the
1,221 MW booking and no row fired). The keeper's fleet loader ALREADY reads
`campd_p999_mw` from this table as the trusted bound `max(nameplate, p99.9)`
on the raw pmax sum (cell `cc_capacity_reconcile_path` K — Zeltmann's raw
662 MW is clipped to 560 there), after which `fleet_to_bins`' summer-derate
nameplate rescale lifts the LP capacity again (≈ 624 MW in the keeper). The
FLAG bounds the FINAL LP `capacity_mw` at `reconciled_mw` after that rescale.

Per-year demonstrated peaks (CAMPD net = gross × 0.975) against the caps —
the cost of a pooled p99.9, stated:

| plant | cap (MW) | p99.9 2023 / 2024 / 2025 | hours above cap | MWh above cap |
|---|---|---|---|---|
| Zeltmann 56196 | 560.0 | 553.8 / **682.5** / 547.9 | 6 / **21** / 0 | 96 / **2,268** / 0 |
| Cricket Valley 57185 | 1,086.9 | 1,079.8 / 1,067.9 / 1,088.1 | 4 / 0 / 23 | 49 / 0 / 35 |
| Athens 55405 | 1,064.7 | 1,054.2 / 1,066.1 / 1,064.9 | 1 / 13 / 9 | 8 / 47 / 143 |
| CPV Valley 56940 | 696.1 | 692.2 / 696.2 / 697.1 | 2 / 10 / 25 | 2 / 33 / 22 |
| Flynn 7314 | 108.2 | 106.5 / 106.5 / 109.2 | 1 / 3 / 40 | 1 / 2 / 22 |

Zeltmann's 2024 record is the one real tension: 21 hours at up to 682 MW
(2,268 MWh, 0.06 % of its 3.7 TWh) above a cap the 2023 / 2025 record
supports — the derive's pooled p99.9 is its frozen rule (rule 23), reported,
not adjusted.

### 3.2 A/B, at full magnitude (arm = `2026-09-04-nyiso-188-ccrecon`; control bit-identical to the keeper; G-DELTA computed: exactly `cc_capacity_reconcile` false → true; G-INPUTS / G-DOF / G-ENGAGE PASS)

**What the flag did to the fleet (P1 unit-hourly, plant-hour capacity max and
annual energy, TWh):** −740 MW of LP capacity over the 12 capped plants, +37 MW
over the 3 raised. The energy the 15 plants give up is −1.90 / −2.23 / −2.45
TWh (2023 / 2024 / 2025), of which the three nyiso-186 excess carriers are
Cricket Valley 1,266.6 → 1,048.9 MW (6.47 → 5.54 / 6.01 → 5.12 / 6.04 →
5.14), Zeltmann 602.0 → 540.4 MW (4.50 → 4.04 / 4.55 → 4.08 / 4.03 → 3.62)
and Athens 1,178.8 → 1,027.4 MW (1.89 → 1.71 / 4.09 → 3.66 / 3.29 → 2.97);
CPV Valley 743.5 → 671.7 (−0.35 / −0.40 / −0.36) and Flynn 199.9 → 104.4
(−0.22 / −0.27 / −0.32) carry the rest; the raises add Astoria Energy I +0.13,
Caithness +0.10, Carr Street +0.02–0.05 per year. Class `CC_REGULAR` 33.47 →
32.00 / 37.86 → 36.10 / 36.01 → 34.02; the energy lands on `ST_GAS` (+0.77 /
+0.75 / +0.97) and `CC_CHP` (+0.35 / +0.61 / n.a.) inside the pinned gas
family; load-weighted price 33.80 → 34.81 / 38.30 → 39.57 / 59.61 → 61.84
$/MWh (+3.0 % / +3.3 % / +3.7 %).

### 3.2.1 Criteria (scorer, committed artifacts only)

| criterion | keeper | arm |
|---|---|---|
| C1 2023 `CC_REGULAR` / `ST_GAS` / `CC_CHP` / `CT_PEAKER` | +0.46 / +2.21 / +0.85 / −1.75 PASS | −1.01 / **+2.98** / +1.20 / −1.65 PASS (band ±3.82 TWh, ±3 pp) |
| **C1 2024 `CC_REGULAR`** | **+3.80 TWh, +3.1 pp FAIL** | **+2.04 TWh, +1.8 pp PASS** |
| C1 2024 `ST_GAS` / `CC_CHP` / `CT_PEAKER` | −1.06 / +1.93 / −1.66 PASS | −0.31 / +2.54 / −1.58 PASS |
| C2 | PASS (2024 flagged `CC_REGULAR`) | PASS (all classes in band) |
| C3a 2023 / 2024 / **2025** | +4.8 / +0.5 / **−10.4 % FAIL** | **+7.9** / **+3.8** / **−6.9 % PASS** (band ±10 %) |
| C3b NRMSE 2023 / 2024 / 2025 | 0.123 / 0.173 / 0.192 PASS | **0.134** / **0.175** / 0.171 PASS |
| C3c (RT hours > $300) | 1 / 0 / 1 vs 10 / 13 / 42 FAIL | 3 / 0 / 4 — **CAVEAT** (lone failure, rubric v3.3 standing rule) |
| C4 gas r / NRMSE | 0.94 / 0.125; 0.904 / 0.13; 0.843 / 0.188 | 0.94 / 0.126; 0.902 / 0.131; 0.84 / 0.188 |
| C6 | PASS (attested) | PASS (attested, computed premises) |
| C8 `CC_REGULAR` D-2 | 5.0 / 3.4 / 3.2 % PASS | 5.0 / 2.8 / 2.7 % PASS |
| C8 `ST_GAS` D-2 | 19.0 / 25.2 / 20.3 % PASS | 17.1 / 22.3 / 17.3 % PASS |
| D-4 | `passed: false`, the five rider rows | the same rows less one (Caithness 56234, 2023 — no longer binds off-window at its raised capacity) |
| **determination** | **NOT-YET, grade 5, fails 3** | **CALIBRATED, grade 7, fails 0, C3c ledgered** |

**Verdict under PREREG §3 (verbatim):** no criterion flips PASS → FAIL; G-DELTA
holds; the arm is a **KEEPER CANDIDATE**, the first NYISO run to read
`CALIBRATED`. **Every regression, stated:** C3a-2023 +4.8 → +7.9 % and
C3a-2024 +0.5 → +3.8 % (both inside the ±10 % band; the price level rises in
every year because the cheapest 740 MW of `CC_REGULAR` headroom no longer
exists — the direction a capacity bound must produce); C3b-2023 0.123 →
0.134 and 2024 0.173 → 0.175 (in band; 2025 improves 0.192 → 0.171); C1-2023
`ST_GAS` +2.21 → +2.98 TWh (in band, but now 0.8 TWh from its edge) and
`CC_CHP` 2024 +1.93 → +2.54. **LOYO** reduces to the per-year record: the
same sign in every year for every moved quantity (class −1.5 / −1.8 / −2.0
TWh; price +3.0 / +3.3 / +3.7 %; C3b 2023–2024 worse, 2025 better), no fitted
scalar, largest where the record is (2025, the outage-rich year). Rule 1
reading: the mechanism is a measured capability bound (the plants never
sustained the capacity the fleet loader gave them; nyiso-186's phantom test
fired on it before any residual was read), so it is kept on structure; that
it also closes two load-bearing cells is reported, not the reason.

---

## 4. Object 3 — Bethlehem 2539: the applied heat rate is an EIA-923 generator-filing artifact

### 4.1 The decomposition (eGRID PLNT / UNT / GEN sheets, seven vintages; CAMPD unit-level; EIA-923 monthly)

| vintage | CT net (GEN 5 / 6 / 7, TWh) | ST net (GEN 8 "CA", TWh) | ST / CT | PLHTIAN / CT net | `PLHTRT` (applied basis) | block HR at the plant's own ST/CT 0.49 |
|---|---|---|---|---|---|---|
| 2018 | 3.445 | 1.697 | 0.492 | 10.33 | 6.923 | 6.93 |
| 2019 | 3.028 | 1.516 | 0.501 | 10.42 | 6.941 | 6.99 |
| 2020 | 3.332 | 1.644 | 0.494 | 10.26 | 6.868 | 6.88 |
| 2021 | 3.543 | 1.762 | 0.497 | 10.28 | 6.865 | 6.90 |
| 2022 | 2.805 | 1.457 | 0.519 | 12.55 | 8.261 | 8.42 |
| **2023 (the fleet's vintage)** | 4.090 | **0.268** | **0.065** | 10.30 | **9.665** | 6.91 |
| 2024 | 3.639 | **0.000** | **0.000** | 10.44 | 10.444 | 7.01 |

| CAMPD unit-level (three CTs) | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| gross / EIA-923 net | 0.67 | 0.66 | 0.67 | 0.67 | 0.82 | 0.96 | **1.53** | **1.53** |
| heat / gross (MMBtu/MWh) | 10.30 | 10.48 | 10.21 | 10.25 | 10.11 | 10.08 | **6.85** | **6.90** |

Three facts, each from a published field:

1. **The heat per CT-generator MWh is invariant** — 10.26–10.44 in every
   vintage except 2022 (EIA-923 files ZERO net generation for February and
   November 2022 — a net-side gap in that filing). The CTs' heat is the
   block's heat (the steam turbine burns nothing), so the block's rate is
   fixed by how much of the block's output the filing attributes to the
   steam generator.
2. **The steam generator's filed net generation collapses** from a third of
   the plant (0.49–0.52 of CT output, five vintages) to 6 % (2023) and exactly
   0.0 MWh (2024) while the three CTs report 7,900–8,000 operating hours each
   — a 3 × 1 F-class block whose CTs run 90 % of the year cannot have its
   heat-recovery steam turbine at zero. `PLNGENAN` is understated by the
   steam share, and `PLHTRT` = PLHTIAN / PLNGENAN inflates in step: 6.87 →
   8.26 → 9.665 → 10.44.
3. **CAMPD's gross-load convention changed the other way in 2024:** 2018–2023
   gross is CT-only (0.66–0.96 of EIA-923 net; running-hour HR 10.1–10.5 —
   the simple-cycle number), 2024–2025 gross is the whole block (1.53 × the
   understated EIA-923 net; HR **6.85 / 6.90**).

Three independent bases therefore agree on the block: eGRID 2018–2021
(6.87–6.94), CAMPD 2024–2025 full-block gross (6.85–6.90) and the CT-heat
identity at the plant's own steam share (6.88–7.01 in EVERY vintage, 2023 and
2024 included). The fleet prices Bethlehem at the eGRID 2023 `PLHTRT`
(`process_eia860.py::_join_egrid_heat_rate`, one vintage for every backcast
year): **9.665 against a physical ≈ 6.9–7.0, +40 %** — at 2024 delivered gas
(~$2.75/MMBtu) about +$7.5/MWh, which is what puts a 750 MW Capital-Hudson
combined cycle out of merit (nyiso-186 §5.3: loading 0.30 of available in
2023 against a 0.94 online share; −2.28 TWh against EIA-923 that year).
The same filing understates the plant's EIA-923 total in 2023–2024 (the unit
sidecar's EIA-923 column and nyiso-186 §2.1's per-plant comparison are on
that basis); the bench's CAMPD series is unaffected in 2024–2025 and CT-only
in 2018–2023.

### 4.2 The admissible instrument, adjudicated against the pre-registered rule (PREREG §3: zero-parameter, threshold-free, source-internal, per-vintage, AND reaching the applied 2023 vintage)

| candidate | reaches 2023? | verdict |
|---|---|---|
| (i) the identity derive's own rule applied to 2539 — pool over ALL vintages, no choice: ΣPLHTIAN / ΣPLNGENAN 2018–2024 = **7.85**, LOYO [7.51 (drop 2023), 8.05 (drop 2018)] | yes, by dilution | admissible in FORM but knowingly contaminated (two of seven vintages carry the artifact; the LOYO spread ±0.27 is itself the signal — Astoria's merged identity reads [7.36, 7.40]); and as a MECHANISM it is a fleet-wide basis change for every CAMPD-covered plant, not a footprint — **a lane, not a repair** |
| (ii) generator-completeness identity: every EIA-860 operating generator of the block reports `GENNTAN > 0` in the vintage | **no** — 2024 fails (CA = 0.0), 2023 passes (267,718 MWh) | threshold-free and source-internal, but it cannot exclude the vintage the fleet applies |
| (iii) the CT-heat identity `PLHTIAN / Σ_CT GENNTAN / (1 + ST/CT)` | yes | reaches 2023 only through a steam share: the plant's own 2018–2022 record (0.49–0.52) or the EIA-860 nameplate ratio 310.2 / 582.9 = 0.532 (→ 6.72; 2.6 % under the clean vintages) — a physical bound not in `constants.py`, i.e. a NEW mechanism class that needs the owner |
| (iv) the existing boundary repair `_egrid_boundary_hr_repairs` | no | needs PLHTRT > 11.5 (the `gas_ct` older bin) AND a co-located sibling reporting its own heat — neither holds |

**S4 fires: no candidate satisfies (a)–(d), so no solve.** What is handed to
the owner is a decision between two forms, each fully specified: (A) the
general pooled-vintage basis (candidate i) as a registered mechanism with its
own A/B — rule-consistent, but it leaves Bethlehem at 7.85 knowing the block
is 6.9; (B) candidate iii with the steam share as a cited physical constant
(the EIA-860 nameplate ratio is a published field; the plant's own five-vintage
record is a measured one) — reaches the truth, needs an owner-authorized
bound. Either is a new `ScenarioConfig` field with a matrix row (rule 28c);
neither is a per-plant carve (rule 24: the test runs over the population —
the same GEN-sheet collapse test can be run for every NYISO CC, which this
session did not do beyond 2539).

---

## 5. What this session does NOT claim, and what it hands forward

### 5.1 Not claimed

* Nothing on the 2024 `CC_REGULAR` disposition (nyiso-187 §2) is re-opened:
  no CC lever, no band, no markup, no load-pocket route; Object 2 is a
  registered flag over a measured capability table, tested because its
  phantom-capacity test fired (nyiso-186 §2.2), not because of the cell.
* The Bethlehem measurement is not a repair; the applied vintage's rate is
  what the fleet carries until the owner picks a form.
* No price claim anywhere; every criterion move is reported as read.

### 5.2 Handed forward (the §5.5 queue, in order)

1. **Bethlehem 2539 — an owner decision between two instrument forms (§4.2):**
   (A) a general pooled-vintage eGRID heat-rate basis (the identity derive's
   rule applied to every CAMPD-covered plant; 2539 → 7.85, LOYO [7.51, 8.05])
   as a registered mechanism with its own A/B; or (B) the CT-heat identity with
   the steam share as a cited physical constant (EIA-860 nameplate ratio 0.532,
   or the plant's own 2018–2022 record 0.49–0.52) — reaches ≈ 6.9–7.0, needs an
   owner-authorized bound. Both are new `ScenarioConfig` fields with a matrix
   row; the GEN-sheet collapse test should be run over every NYISO CC before
   either is built (rule 24: a population rule, never a carve).
2. **The 2024 `CC_REGULAR` cell** now reads PASS (+2.04 TWh) under the
   capacity bound; the residual +2.0 TWh is still the within-family fill of
   the CT / steam deficits nyiso-187 §2 attributed to out-of-market commitment
   (G) and the owner-accepted markup trade — the disposition stands, at a
   smaller magnitude.
3. **C3a-2025** at −6.9 % is inside the band but still the largest price miss;
   DECISION-CARD-nyiso148 Q1 (the 2025 offer-level remainder) remains the
   owner's.
4. **Zeltmann's 2024 cold-weather record** (21 h at up to 682 MW above the
   pooled 560 MW cap, 2,268 MWh): the reconcile derive's pooled p99.9 is its
   frozen rule; a per-year demonstrated peak would be a derive change under
   rule 23 (a source-data argument, not a residual one) — recorded, not
   proposed.
5. **The v2 artifact's frozen rows** (2018 / 2022 / 2026 keep CT3 / CT4 under
   55375): a NYISO forecast-mode estimator window that reaches 2026 reads the
   old routing — the forecast lane's item; the 2018 vintage is unrecoverable
   at tip (BLOAT-S2) and 2022 / 2026 sit behind the one-shot intake guard.
6. **NYISO parasitic factors** are absent from `parasitic_load_factors.parquet`
   (net = gross for every NY / NJ row of the v2 artifact) — a uniform basis
   today, and a measured input the derive could supply (rule 14).
7. Unchanged: the Astoria merit-panel stack-duplicate defect (nyiso-184 §4.1);
   the D-2 / C8 grain under-count escalation (nyiso-181 §6).

---

## 6. Governance

Rule 1: nothing adopted or rejected on a residual; every bar was pushed before
the first arm solved and read verbatim; the verdict rule before any solve.
Rules 5 / 21 / 23: zero parameters, zero new DOF entries (13 / 6 verbatim);
each re-derivation cites its data change (the routing identity; the CAMPD
vintages the reconcile derive pools). Rule 13: CAMPD diagnosed; the LP reads
re-derived measured artifacts and a measured capability table. Rule 14: the
license for the two artifact repairs and for testing the flag. Rule 15: every
non-control solve is registered; the bit-identical control registers nothing
(slim files committed as the instrument). Rules 16 / 12: one invocation per
arm, years sequential, at most two concurrent solves, no file-swapped arm
concurrent with anything. Rule 19: the ramp / emission arms re-derive inputs
an armed mechanism already reads; the flag arm arms a registered flag whose
table the keeper half-reads — nothing stacked. Rule 22: 2023–2025 only, no
marker requested; the v2 derive's quarantined rows stay frozen. Rule 24: no
field added; `--merge` / `--out` are derive tooling, not tunables. Rules 25 /
28: NYISO shard only; CAISO's remap rows and reconcile table untouched. Rule
27: on-disk bytes pushed, ≥300-line blobs verified.

## 7. ADDENDUM — the owner ruling, and what was executed

The owner's standing formula (delivered at nyiso-187, verbatim: *"Is this a
recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper.."*) is applied. This
session's recommendation on the registered combined candidate is **promote**:
two zero-parameter representation repairs at the ISO's largest merchant CC
site plus a registered measured-capability bound whose phantom-capacity test
fired independently of any residual; the determination moves NOT-YET →
CALIBRATED and every regression is in band and stated. **`2026-09-04-nyiso-188-combined`
is PROMOTED.** Executed in the same PR: `frontend/data/backcast/keepers/NYISO.json`
(keeper, promotion note, determination note re-verified from committed
artifacts; the prior keeper into the `superseded` chain); `scripts/build_status.py
--iso NYISO`; `scripts/audit_keepers.py --iso NYISO` (PASS); the forecast
gate-(a) stamp re-keyed (`check_gate_a_provenance.py --iso NYISO` OK; the
leg still reads FAIL on its marker condition — NYISO holds no `complete`
marker and none is requested); the NYISO matrix shard (keeper + gates
re-stamped; `cc_capacity_reconcile` U → K; `ramp_envelopes`,
`plant_emission_rates_v2`, `egrid_identity_heat_rates`,
`campd_per_unit_attribution` annotated; `check_mechanism_matrix.py` clean) and
the §5.5 header + queue; `docs/calibration-log/nyiso.md`. The three re-derived
artifacts (`campd_ramp_envelopes_NYISO.csv`, `plant_emission_rates_v2.parquet`
+ `.csv`, `cc_capacity_reconcile_NYISO.csv`) are committed as the keeper's
inputs. NYISO holds no `complete` marker, so no D-5(b) re-key; whether a
CALIBRATED keeper re-opens the `complete` question (withdrawn 2026-08-30) is
the owner's. Every number in §1–§6 stands; nothing was re-measured.
