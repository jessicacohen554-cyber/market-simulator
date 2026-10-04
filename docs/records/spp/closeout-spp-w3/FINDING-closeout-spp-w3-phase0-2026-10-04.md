# FINDING — closeout-SPP-w3 phase 0 (zero LP): two measured-input levers whose reach is mostly in 2023–25, and a scorer-basis gap in 2019–22

- **Lane:** closeout-SPP-w3, desk `session_01ERkBTm23ZAP4CTZnJVD9Ss`. Branch `claude/closeout-spp-w3`, cut from
  `90cea7206f4f3daf56ecb7bf29989f534da7a14d`. DATA PROFILE: spp.
- **Keeper (control, read only):** `2026-10-03-closeout-spp-nuc-keeper`, bundle `closeout_spp_nuc_span`, legs at
  `8c3ea461`. Rubric v3.20. Determination **NOT-YET**.
- **LP spent:** zero. **Probe:** `scripts/probes/_closeoutsppw3_phase0.py` →
  `results/phase0/spp/_closeoutsppw3_phase0.json`.

## 1. Root-cause decomposition (sections A, D of the probe)

| failing record | where the residual sits | mechanism in the LP that sets it |
|---|---|---|
| C3a 2019 +12.3 %, 2020 +27.7 %; C3b 2020 0.345 | Hours where measured RT ≤ 0, and the $0–20 body. In RT ≤ 0 hours the model clears at +$13–17. Its thermal output there is 1–4 GW below EIA-930 and its wind is up to 4.5 GW above. November 2020 alone is 36 % of the 2020 C3b SSE (model $21.4 vs actual $9.7). | Commitment state: the pure LP backs thermal down instead of curtailing wind (SPP-74/75/88; frontier SPP-F2). The **UC-MILP program has already named SPP 2019/2020 as its targets** (plan §Log, UC-0). This lane does not duplicate that work. |
| C3a 2024 −11.2 %, C3b 2024 0.216 | Upper-tercile compression common to all train years (Jul–Aug: 23 % of 2024's C3b SSE), plus Sep–Oct Oklahoma congestion (52 % of SSE) | Upper tercile: a flat gas stack. 2,029–2,220 h/yr where the budget LP puts hydro above its measured ceiling; wind marginal at a flat −$26. Sep–Oct: DATA-LIMITED (F1, re-confirmed: the 2024 DA and RTBM binding-constraint archives on portal.spp.org carry no limit columns, checked today). |
| C1 2021/22 CC −8.9/−9.2, PRB +11.0/+10.8; C4 gas 2022 0.313 | Wind delivered model vs EIA-930/923: +1.3/+2.1/+5.2/+9.2/+8.4/+11.4/+10.8 TWh in 2019–25. This is curtailment the model does not perform (SPP-88), and gas is its counterpart. | Commitment state again, plus the W5 basis (F3). |
| C3c 2023–25 | 5-min scarcity, model-class (F4) | — |

**What is new here.** The re-open condition on `wind_ptc_vintage_offers` (cell I, SPP-51b) is now met.
- SPP-51b scored it INERT because wind was interior in only 7/7/3 hours.
- Since SPP-51c (`vre_curtailment_oversupply_allocation`, K), the keeper clears at the wind floor in **1,125 / 1,258 /
  1,112 zone-hours** in 2023/24/25 (964 / 1,460 in 2021/22), at exactly −$26.000.
- That floor is the flat `ira_ptc_wind`. The measured offer is −PTC_statutory(y) × the EIA-860 in-window share. The
  statutory PTC is $28/29/30 and the eligible share is 0.74 / 0.74 / 0.71, so the offer is **−$20.9 / −$21.6 / −$21.3**.
- So the cell's own reach premise has flipped. Its direction premise ("only less negative — wrong way") was written
  for the over-priced 2019/20 regime. On the under-priced train tier it now points the right way.

## 2. Candidates (rule 28: cells read first)

| candidate | SPP cell | new evidence | reach, zero LP (scorer basis) | verdict |
|---|---|---|---|---|
| **`wind_ptc_vintage_offers`** (existing field, ISO-agnostic, default off) | I (SPP-51b) | §1: wind is now marginal 6–8 % of zone-hours in 2021–25 | C3a 2023/24/25 +1.13 / **+1.04** / +0.88 pts; 2019/20 +0.04 / +0.24; C3b 2024 −0.007 | **chartered (arm)** |
| **`hydro_dispatch_envelope`** (existing field, ISO-agnostic; K in CAISO/NYISO/NWPP, transfer enters SPP as U) | U | Model hydro within-day std is 1.8–1.9× EIA-930 WAT. The model's daily max is 3.1 GW against a measured 2.2–2.8 GW. 1.34–2.15 TWh/yr sits above the measured month × hod p95 in 2,029–2,564 h. This is the **upper half** of the two-sided family whose lower half (`hydro_min_flow_floor`) SPP already arms (hydro-5; NYISO-92 armed both as one family, rule 19). | stack walk: C3a 2024 **+0.62**, 2025 +0.82, 2023 +0.54; 2019/20 +0.38 / +0.60; C3b 2021 −0.011 | **chartered (arm)** |
| both | — | — | **C3a 2024 −11.2 → −9.5 % (PASS by ~0.5)**; C3b 2024 0.216 → ~0.209 (stays FAIL) | the arm |
| commitment state (UC MILP) | UC program | targets SPP 2019/20 already | — | not this lane |
| Oklahoma pocket limits | O / U | DA + RTBM 2024 archives re-listed today: no limit columns | ~9 pts | DATA-LIMITED (F1 unchanged) |
| rule-1 offer bands, curtailment ceiling, gas bridge, posture, co-opt | R / I / do-not-redo | none | — | not re-tested |

## 3. Scorer basis: SPP 2019–22 are the only legacy-basis ISO-years in the repo (desk ask, not applied)

`actual_lmp.json` carries `rt_lw`/`rt_lw_mon` for every ISO-year on disk **except SPP 2019–2022**. The 2019 rows of
CAISO and NWPP have no price at all. SPP 2019–22 are therefore gated on the **legacy equal-hour** fallback: model
load-weighted against actual equal-hour. Both inputs the v2.4 retrofit needs are committed: the hourly hub series for
2019–22 and the measured demand. Running the unchanged `derive_actual_lmp._lw_fields` for SPP:
- reproduces the committed 2023–25 values exactly (25.13 / 25.45 / 28.60);
- for 2019–22 it yields the following.

| year | legacy rt → rt_lw | C3a legacy → lw | C3b legacy → lw |
|---|---|---|---|
| 2019 | 20.85 → 21.84 | +12.2 → **+7.2 %** (FAIL→PASS) | 0.160 → 0.133 |
| 2020 | 16.52 → 17.54 | +27.7 → +20.3 % | 0.345 → 0.315 |
| 2021 | 37.36 → 40.93 | +7.1 → −2.3 % | 0.176 → **0.288** (PASS→FAIL) |
| 2022 | 44.09 → 48.41 | −4.8 → **−13.3 %** (PASS→FAIL) | 0.175 → **0.215** (PASS→FAIL) |

- The fix is like-for-like and uses no new code.
- It is net adverse: one flip FAIL→PASS and three PASS→FAIL.
- It changes scored readings with no LP, so it is an owner/desk item (rule 37 adjacency). It is **not applied here**.

## 4. Rules

- **1 / 13 / 14:** both levers replace an estimate with a measured input that a forward year can regenerate:
  - the PTC offer comes from EIA-860 vintages and the IRS statute;
  - the hydro ceiling comes from EIA-930 WAT, with the climatology fallback forward.

  No value is chosen on a residual.
- **19:** the envelope completes the family the min-flow floor opened. It does not stack with it. The PTC scoping is
  a bid change on the wind column only.
- **25:** no other ISO's verdict fills the SPP cells. Both fields are generic and neutral.
- **28:** the SPP shard is updated in this lane after the solve.
