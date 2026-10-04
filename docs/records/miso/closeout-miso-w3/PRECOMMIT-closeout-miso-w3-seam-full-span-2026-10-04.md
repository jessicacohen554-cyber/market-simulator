# PRECOMMIT — closeout-MISO-w3: the hourly neighbour seam ladder over the full span (2019–2022 offsets), seven legs

Written and pushed **before any solve**; every bar below is fixed ex ante. Evidence: `FINDING-closeout-miso-w3-phase0-2026-10-04.md` (same directory).

```
LANE      : closeout-MISO-w3 (desk session_01ERkBTm23ZAP4CTZnJVD9Ss)
KEEPER    : 2026-10-03-closeout-miso-nuc-r (results/calibration/closeout_miso_nuc_span), the control (rule 29b; no control solve)
ARM       : the keeper recipe + miso_seam_neighbour_hourly_full_span=true (one field, default off; nothing else moves)
LEGS      : 2019-2025, one shard per year at the pushed lane SHA (rules 32/34/36); probe bundle closeout_miso_w3_span
OFF-PLAN  : plan §3.3 queue is exhausted (closeout-MISO-w2); this lever is new evidence on a K cell (rule 28): the data
            boundary miso-252/miso-261 recorded for the 2019-2022 overlays has moved
```

## Mechanism, driver, forward story

- **Mechanism.** `seam_neighbour_hourly_ladder` (K) is armed in every keeper leg, but it fires only in 2023–2025 because its offset tables stop there. The arm merges `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_FULL_SPAN_BY_YEAR` (PJM) and `..._SPP_FULL_SPAN_BY_YEAR` (SPP) under those tables. In 2019–2022, PJM and SPP band k is then offered at `anchor(t) + δ_k`, not at one annual price.
- **Driver (rule 13, rule 14).** The anchor is the measured neighbour DA price: the PJM western-border hubs (Data Miner 2 CSVs) and SPPNORTH_HUB. It is the same quantity, at the same solve-time seam, that the keeper already admits for 2023–2025. A forward run reads the forecast neighbour price.
- **Construction.**
  - Zero fitted parameters (rule 21). δ_k comes from the frozen `derive_miso_seam_ladders.py`.
  - Rule-23 trigger: the source-data extension. The border parquet gains its 2019–2022 rows, and 2023–2025 stay byte-identical.
  - The derive reproduces every committed 2023–2025 offset; the pin is tested in `TestHourlyOverlayFullSpan`.
  - Rule 19: adds years, never a mechanism; refused without the parent flag; the SPP rows ride the existing SPP sub-gate.
- **Exact config delta.** `--set miso_seam_neighbour_hourly_full_span=true`. Expected inert on 2023–2025: the 2023–2025 tables win on every shared key, so those legs differ from the keeper only by G-DRIFT.

## Expected reading (zero-LP, static census; LP attenuation unknown, 0.27 is the prior lanes' constant)

| record | keeper | static bound | at 0.27 |
|---|---:|---:|---:|
| C3b 2021 | 0.219 FAIL | 0.146 | 0.198 PASS |
| C1 CC_REGULAR 2021 | −8.15 FAIL | fall-2021 import cut −6.0 TWh, CC_REGULAR 58 % of Sep–Nov marginal hours | ≥ −7.6 PASS (expected) |
| C3a 2020 | +10.2 % FAIL | +11.5 % | +10.6 % (stays FAIL; wrong sign, declared) |
| C3a 2021 / 2022 | −8.4 % / −6.9 % | −1.2 % / −0.2 % | −6.6 % / −5.1 % |
| C3a 2019 | +6.2 % | +7.6 % | +6.6 % |

## Bars

**Targets** (either one counts as a moved record):
- **T1.** C1 CC_REGULAR 2021 moves by ≥ +0.5 TWh (to ≥ −7.65 TWh).
- **T2.** C3b 2021 NRMSE moves down by ≥ 0.010 (to ≤ 0.209).

**Declared possible PASS→FAIL** (each is reported at full magnitude; a declared crossing is not a kill):
- C1 COAL_PRB 2021 (+5.03, band 8.00).
- C1 COAL_PRB 2022 (+5.72) and COAL_BIT 2022 (+5.17): the 2022 import cut lands partly on coal (PRB 27 % of 2022 marginal hours).
- C3a 2019 crossing +10 % is **not** declared; it is a kill (K4).

**C3a / C3b band discipline.**
- No C3a year other than 2020 may leave ±10 %.
- No C3b year may cross 0.20.
- C3a 2020 may worsen by at most +2.0 pts (to ≤ +12.2 %).

**Kills** (any one kills the arm; it is recorded R in MISO's cell with this RESULT):
- **K1.** T1 and T2 both fail.
- **K2.** C1 CC_REGULAR 2021 or C3b 2021 moves the wrong way.
- **K3.** Any C1 gas row (CC_REGULAR / CT_PEAKER / ST_GAS / CC_CHP / ST_CHP) 2019–2022 goes PASS→FAIL.
- **K4.** Any C3a year other than 2020 leaves ±10 %, or any C3b year crosses 0.20.
- **K5.** C3a 2020 worsens by more than +2.0 pts.
- **K6.** A 2023–2025 leg differs from the keeper by more than its G-DRIFT attribution. The arm is inert there by construction, so a difference is a bug: stop and report.
- **K7.** Seam diagnostic: model net import 2019–2022 moves *away* from EIA-930 per-seam measured in ≥ 3 of 4 years by > 2 TWh (the ladder is meant to reproduce measured volume).

**Beats the keeper** iff no kill fires and the count of failing (criterion, year) records falls (keeper: fuelmix 2019 + 2021, price_mean 2020, price_shape 2021).

## Process

G-DRIFT f98c4564 → pin is in `GDRIFT-closeout-miso-w3-keeper-to-pin.md`. Seven shards run at the pushed SHA, ≤ 6 alive at once. The parent composes `closeout_miso_w3_span` and scores it with `calibration_verdict.py` and `legitimacy_diagnostics.py`. The RESULT lands beside this file. No promotion from this lane: on a beat, the desk gets the scored flips plus the promotion cost.
