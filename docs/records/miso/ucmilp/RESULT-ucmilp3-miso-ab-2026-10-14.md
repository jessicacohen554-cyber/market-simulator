# RESULT: UC-3-MISO, clean MILP-UC A/B at uc-1.5

**Arm A (UC + every floor kept): R.** **Arm B (UC + ST_GAS per-plant must-run floor off): structure supports un-stack, on 4 of 7
years.** The energy cost is real and is stated beside that verdict.

PRECOMMIT: `PRECOMMIT-ucmilp3-miso-ab-2026-10-14.md` (§§0–5, Addenda 0, A–E), written before any number. Lane session
`session_01XhMwoXKrbRPUQzQ9UuZRbB`, branch `claude/ucmilp-3-miso-ab`.

- **Pin:** uc-1.5 `2dd69d5a`, merged into the lane branch at `054dc883` (every shard's `source_revision`).
- **Control:** keeper `closeout_miso_nuc_span`, committed bundle (rule 29(b)). G-DRIFT `eab17188 → 580c4fbf → 2dd69d5a`: UC path
  only, solve surface 0 moved, so the control is INERT.
- **Scoring:** rubric 3.20. The control reproduces 8 scored / 4 target / 1 ledgered / 3 FAIL, NOT-YET.
- **Nothing registered or promoted (E13).**

## 0. Gate table, control → arm A → arm B

C1 = model − EIA-923 TWh. C3a = mean LMP vs RT. C3b = monthly price NRMSE. C4 = gas fleet hourly NRMSE (r ≥ 0.70, NRMSE ≤ 0.30).
C8 = ST_GAS forced share. "—" = arm B not solved (Addenda D–E).

| year | C1 ST_GAS | C1 CC_REGULAR | C3a | C3b | C4 gas NRMSE | C8 ST_GAS | unserved MWh |
|---|---|---|---|---|---|---|---|
| 2019 | −8.71 F → −8.44 F → −13.61 F | +3.17 → −0.25 → +3.50 | +6.2 % → +6.9 % → **+13.3 % F** | 0.091 → 0.097 → 0.190 | 0.196 → 0.209 → 0.211 | 26.3 % → **31.7 % F** → 3.8 % | 0 → 0 → 0 |
| 2020 | −7.09 → **−8.06 F** → **−13.14 F** | −1.24 → −4.31 → −0.45 | +10.2 % F → +11.3 % F → +15.2 % F | 0.147 → 0.156 → 0.188 | 0.201 → 0.217 → 0.213 | 20.0 % → 25.0 % → 2.6 % | 0 → 0 → 0 |
| 2021 | −5.36 → −4.77 → **−10.47 F** | −8.15 F → −13.94 F → −8.69 F | −8.4 % → −7.6 % → −3.2 % | 0.219 F → 0.214 F → **0.197 P** | 0.291 → **0.310 F** → **0.306 F** | immaterial | 0 → 0 → 0 |
| 2022 | −5.67 → −5.87 → **−10.27 F** | −5.48 → **−16.04 F** → **−9.44 F** | −6.9 % → −9.0 % → −5.5 % | 0.127 → 0.129 → 0.099 | 0.246 → 0.296 → 0.279 | immaterial | 0 → 0 → 0 |
| 2023 | −1.48 → −4.20 → — | −0.87 → −5.87 → — | +4.8 % → +3.7 % → — | 0.078 → 0.064 → — | 0.165 → 0.195 → — | 15.4 % → 22.4 % → — | 0 → 0 → — |
| 2024 | −2.43 → −5.84 → — | +2.61 → −1.62 → — | +2.5 % → +0.4 % → — | 0.082 → 0.077 → — | 0.151 → 0.183 → — | 14.9 % → 23.8 % → — | 8,356.9 → 8,678.6 (+321.7) → — |
| 2025 | SKIPPED | SKIPPED | −3.7 % → −4.0 % → — | 0.085 → 0.083 → — | 0.173 → 0.197 → — | 20.0 % → 25.5 % → — | 0 → 0 → — |

**C3c.** The probe spans carry no attestation, so C6 reads UNATTESTED and every CAVEAT reads FAIL: the artefact declared in UC-2 §3
and carried here. Compared on magnitude only (model hours > $200 vs RT actual):

| year | control | arm A | arm B | actual |
|---|---|---|---|---|
| 2019 | 0 | 3 | 50 | 17 |
| 2020 | 0 | 0 | 20 | 8 |
| 2021 | 0 | 2 | 18 | 48 |
| 2022 | 0 | 0 | 8 | 116 |
| 2023 | 0 | 0 | — | 30 |
| 2024 | 7 | 7 | — | 37 |
| 2025 | 9 | 9 | — | 88 |

Arm B's **2020** row is a genuine model PASS → FAIL: 20 h vs 8 h breaks the small-count |Δ| ≤ 10 h tolerance.

**Coverage.** Arm A has 7 of 7 years. Arm B has 4 of 7: 2023, 2024 and 2025 were OOM-killed in six attempts (two per year), on containers provisioned at
16.4–17.4 GiB ceiling + swap. Every completed leg had 22.4 GiB and peaked at 16.5–17.9 GiB (Addenda D–E). Four of those kills came
after a clean UC stage (365/365 windows Optimal), so the gap is P1 memory, not the UC engine.

## 1. Verdicts

**Arm A: R.** By UC-2 §7, both triggers fire:
- **Kill #3 (four model flips vs control):**
  - C1 CC_REGULAR 2022: −5.48 → −16.04 TWh.
  - C1 ST_GAS 2020: −7.09 → −8.06.
  - C4 gas 2021: NRMSE 0.291 → 0.310.
  - C8 ST_GAS 2019: 26.3 → 31.7 %, above the cap and not grounded, because the uc_schedule floor has no declared D-4 window.
- **T1 moves the wrong way past control:** 2020 C3a +10.2 → +11.3 %.

Also:
- T2 has the right sign but is below its bar: 2021 C3b 0.219 → 0.214, bar ≤ 0.2095.
- T3 does not move: reserve dormancy 1.000 / 0.999 / 0.998 is unchanged in 2023–25; mean MCP $0.00 → 0.03, 0.23 → 0.25,
  0.17 → 0.24 vs actual $2.3–3.1.
- T4 has the right sign: hours ≤ $15 in 2020 go 8 → 46 and in 2024 6 → 125 (actual 1,021 / 597).
- Unserved stays inside the bound (+321.7 MWh).
- One new D-4 FAIL row appears (plant 1439, 2020).

**Arm B (Addendum 0, structure rows, on the 4 solved years): supports un-stack.**

| row | reading | 2019 / 2020 / 2021 / 2022 | reads |
|---|---|---|---|
| B-i(b) | ST_GAS starts ÷ CEMS (control → B) | 5.06 → 0.75 · 6.38 → 1.08 · 4.74 → 0.82 · 3.15 → 0.64 | toward 1.0 in every year; no overshoot below 1/control |
| B-ii | ST_GAS D-2 forced energy (control → B) | 4.85 → 0.35 TWh (26.3 → 3.8 %) · 4.33 → 0.30 (20.0 → 2.6 %) · 2021/22 immaterial | falls; MECH 28 re-forces 0.30–0.35 TWh, ≪ the floor removed |
| B-ii | D-4 FAIL rows | control 5 (plant 990 reliability_floor ×4; 1081 in 2019) → **B 0** | no new FAIL; every control FAIL clears |
| B-iii | P1 unserved | 0 / 0 / 0 / 0 | holds |
| B-i(a) | **energy cost:** C1 ST_GAS gap | −8.71 → −13.61 · −7.09 → −13.14 · −5.36 → −10.47 · −5.67 → −10.27 TWh | widens 4.6–6.1 TWh/yr; PASS → FAIL in 2020/21/22 |
| B-iv | C3a / C3b (reported) | C3a +6.2 → +13.3 (F) · +10.2 → +15.2 · −8.4 → −3.2 · −6.9 → −5.5 %; C3b 2021 0.219 → **0.197 (T2 met; FAIL → PASS)**, 2019 0.091 → 0.190 | price body up |

**B-i(a) and B-i(b) disagree:** ST_GAS starts land near CEMS while ST_GAS energy falls ~5 TWh/yr further below EIA-923. Per Addendum 0,
this is **a finding routed to the owner, not resolved here**:
- With the measured floor gone, the UC commits ST_GAS only where the economics clear, and MISO's steamers ran out of merit. The floor's
  own provenance is the Entergy VLR / self-commitment steamers (`scenarios.py` `st_gas_mustrun_p25_level` rationale; MISO SOM).
- So the floor carries a real out-of-market commitment that offer prices cannot recover.
- Removing it fixes cycling and conduct but loses the energy.
- A structurally faithful replacement would be a commitment requirement inside the UC, not a dispatch floor beside it. That is a new
  mechanism and needs an owner ruling.

Reported for arm B, not binding (Addendum 0):
- Model flips C1 COAL_PRB 2019 (+4.56 → +8.07), C1 CC_REGULAR 2022 (−9.44) and C4 gas 2021 (0.306).
- C3a 2019 FAIL.
- C3c 2020.

## 2. Diagnosis (zero LP, from the bundles; `ucmilp3_readings/price_diag.json`)

**Arm B prices rise in high-load hours.** Load-weighted P1 $/MWh, control → B:

| year | top 5 % load | high 20 % | h14–21 | bottom 25 % |
|---|---|---|---|---|
| 2019 | 30.6 → 36.5 | 29.8 → 34.0 | 28.7 → 32.1 | 23.4 → 23.5 |
| 2021 | 46.4 → 52.7 | 42.4 → 46.8 | — | 29.6 → 29.5 |
| 2022 | 80.8 → 86.6 | — | — | 48.0 → 46.8 |

- **Price-setting class** (highest-mc marginal unit per hour): ST_GAS falls from 13.5 % / 17.0 % / 5.5 % / 10.7 % of hours to 6.1 % in 2019 and out of the top six in 2020–22.
  CT_PEAKER enters at 8–12 % of hours; it was outside the control's top six.
- **Why:** the decommitted steamers' peak-hour energy is replaced by peakers, which also produces the > $200 hours (17 in 2019).

**Arm A price moves are small and two-sided.** Bottom-25 % load hours fall ($0.2–2.2) and top-5 % load hours rise ($0.6–2.1). Price-setting
shifts from CC_REGULAR (2019: 23.5 → 15.6 %) and ST_GAS to COAL_PRB.
- **Mechanism:** the UC commits CC in long blocks (starts ÷ CEMS 1.1–1.6 → 0.30–0.45) and dispatches less CC energy (−0.4 to −10.6
  TWh/yr), which leaves coal on the margin.
- This CC under-cycling is the source of the arm-A C1 CC and C4 gas flips.

**2024 26-Aug event (arm A).** It is the same event: hours 5701–5705 in both runs. Unserved 8,356.9 MWh (East 4,223 / Indiana 2,888 /
West 1,246) becomes 8,678.6 MWh (West 5,546 / Indiana 2,597 / Plains 536), plus 824.7 MWh dump in MISO_external_South. The UC moves the
shortfall west; it does not create it.

## 3. Engine and cost readings

| arm | year | integers / gate (demoted) | TL hits | forced `_peak` @MECH 28, TWh | uplift % | UC Σ s | total ÷ (P0+P1) |
|---|---|---|---|---|---|---|---|
| A | 2019 | 71/167 (96) | 0 | 0.037 | 0.54 | 3,447 | 3.64 |
| A | 2020 | 76/164 | 0 | 0.025 | 0.50 | 6,140 | 3.17 |
| A | 2021 | 75/161 (86) | 0 | 0.020 | 0.93 | 3,689 | 3.03 |
| A | 2022 | 77/157 | 0 | 0.019 | 1.04 | 3,707 | 2.06 |
| A | 2023 | 74/147 | 0 | 0.037 | 0.41 | 4,970 | 3.25 |
| A | 2024 | 77/144 (67) | 0 | 0.039 | 0.40 | 4,280 | 4.96 |
| A | 2025 | 74/139 | 0 | 0.003 | 0.45 | 4,752 | 2.69 |
| B | 2019 / 20 / 21 / 22 | 71 / 76 / 75 / 77 of the same gates | 0 | 0.023 / 0.022 / 0.001 / 0.027 | 0.06 / 0.06 / 0.09 / 0.16 | 4,176 / 3,811 / 3,617 / 3,952 | phase lines not collected |

- **Engine version:** uc-1.5 on every leg; 0 non-optimal windows in all 11 legs.
- **Forced peak-tranche energy ≈ 0** (UC-2 ERCOT read 5.8 TWh under defect 6), so defect 6 is confirmed gone on MISO.
- **Starts ÷ CEMS:** coal is unchanged in both arms (COAL_PRB 1.1–3.0, COAL_BIT 1.6–5.0), because ruling (a) leaves 65–96 yard-pinned
  coal clusters to their budget identity. CC_REGULAR: A 0.30–0.45, B 0.26–0.39.
- **Walls:** A's walls include container-speed variance (2020 P0 1,559 s vs 552 s at UC-2) because the ratio uses the same container.

## 4. Where the evidence is; what a promotion would cost

| what | where | status |
|---|---|---|
| 11 leg bundles (full, incl. `dispatch/<y>_P1`; split parts sha256-verified) | `claude/ucmilp3-miso-a-<y>` (7) and `claude/ucmilp3-miso-b-<y>` (2019–22) @ the SHAs in `ucmilp3_readings/leg_ledger_partial.md` and PRECOMMIT Addendum D | shard branches: transport, not storage (rule 33); owner cuts after merge |
| slim spans | `docs/records/miso/ucmilp/data/ucmilp3_miso_{a,b}_span/` (system, uc_schedule, uc_uplift, unit_marginal, uc_solve_log, run_config, regenerated diagnostics, meta, metrics) | in this PR |
| readings | `docs/records/miso/ucmilp/data/ucmilp3_readings/` (verdict JSONs, cost rows, walls, M1/M3/M4, price diagnosis, scratch scripts as `.txt`) | in this PR |
| composites | `results/calibration/ucmilp3_miso_{a,b}_span` in the lane container (gitignored via local exclude; never committed, rule 29(c)) | lost with the container |

- **No promotion is proposed.** Arm A is R and arm B is a diagnostic arm (desk ruling).
- **Cost to reproduce arm B's 3 missing years:** three shards on ≥ 22.4 GiB containers, about 2–2.5 h each.

## 5. D-6 card (verbatim-ready)

> **UC-3-MISO (pin uc-1.5 `2dd69d5a`, clean engine).**
>
> **Arm A (keeper + UC, every floor kept): R.** Kill #3: C1 CC_REGULAR 2022, C1 ST_GAS 2020, C4 gas 2021 and C8 ST_GAS 2019 flip.
> T1 moves the wrong way (2020 C3a +10.2 → +11.3 %). The UC over-corrects CC cycling (starts 1.1–1.6× → 0.30–0.45× CEMS; CC energy −0.4
> to −10.6 TWh/yr), and the kept ST_GAS floor stacks on top (ST_GAS forced share +5 to +9 pt). With defect 6 gone this R is structural,
> not an engine artefact: forced peak ≈ 0, uplift 0.4–1.0 %, 0 TL hits.
>
> **Arm B (UC, ST_GAS per-plant floor off; diagnostic, 2019–22 only, 2023–25 lost to container OOM): structure supports un-stack.**
> ST_GAS starts 3.2–6.4× → 0.64–1.08× CEMS; forced share 26 → 4 %; D-4 FAIL rows 5 → 0; unserved 0; T2 met (2021 C3b 0.219 → 0.197).
> The cost: the ST_GAS energy gap widens 4.6–6.1 TWh/yr (C1 PASS → FAIL 2020–22) and the price body rises in high-load hours, where
> peakers replace steamers (2019 C3a +13.3 %).
>
> **Owner question:** the floor encodes measured out-of-market (VLR) commitment that economics cannot recover. Represent it as a UC
> commitment requirement (one mechanism, rule 19) or keep the floor without the UC?
>
> Options: record R (A) · record arm-B finding and charter a VLR-commitment design · hold.

## 6. Engine-version caveat: uc-1.6 landed after these solves

While this RESULT was being written, `main` merged **uc-1.6** (UC-1-FIX-6, #7253, `1aec8c4e`): *"an offline integer cluster carries no
reserve"*.
- **What it changes.** Inside the UC window an integer member's reserve headroom becomes `pmax·a·u/n` instead of `pmax·a`. It is a
  no-op without reserve co-optimization; P1 rows are unchanged.
- **MISO is probably exposed.** MISO's P1 carries the `miso_rbdc` reserve family in every year (`hourly/reserve_family_<y>`), so the UC
  window very likely co-optimizes reserve, and uc-1.6 is probably **LIVE for both arms in all years**.
- **Direction and size are not measured here.** A cluster credited with reserve while offline relaxes the UC's commitment need. Fixing
  it should commit more slow units, which pushes in the direction of the arm-A CC and ST_GAS energy shortfalls. The size needs a solve.
- **So both verdicts carry this caveat.** A uc-1.6 relaunch, under the same PRECOMMIT with only the pin moving and on ≥ 22.4 GiB
  containers, is UC-DESK's call. This lane does not relaunch on its own.

## Log entry

- 2026-10-14 · UC-3-MISO · pin uc-1.5 `2dd69d5a` (lane `054dc883`) · 14 shards → 11 legs:
  - A 7/7 years. B 2019–22; B 2023–25 OOM on 16.4–17.4 GiB containers, twice each (2024's first launch was also rate-limited, Addendum C).
  - Every window Optimal, 0 TL hits.
- **A: R** (4 flips + T1 wrong way). **B: structure supports un-stack** with a 4.6–6.1 TWh/yr ST_GAS energy cost, owner question
  raised. No new defect found in uc-1.5. uc-1.6 (reserve headroom on offline integer clusters) merged after these solves and is probably live for MISO: both verdicts carry that caveat (§6).
