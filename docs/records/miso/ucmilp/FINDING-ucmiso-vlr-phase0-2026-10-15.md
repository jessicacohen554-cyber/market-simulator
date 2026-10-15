# FINDING — UC-MISO-VLR phase 0: VLR as a UC commitment requirement

```
LANE     : UC-MISO-VLR (chartered by UC-DESK session_01WX9W5tgYMre3Z134LZoGF6, owner ruling r13 2026-10-15)
SESSION  : session_01Y72HzBZvQKmeimJ5aWUoYj (Opus)
LP       : none (zero-LP phase 0). Nothing built, solved or registered.
READS    : keeper closeout_miso_nuc_span (committed bundle); UC-3-MISO arm A/B slim spans (uc-1.5);
           CAMPD unit-level hourly LA/TX 2019-2025 (data/raw/campd-unit-level); EIA-860 plant table.
READINGS : docs/records/miso/ucmilp/data/ucmiso_vlr_readings/ (CSV + the scripts as .txt)
```

## 0. Bottom line

1. **Form is now documented; level still is not.** MISO's own documents fix the form: VLR is a set of
   *minimum-commitment / minimum-capacity / binary* constraints in SCUC (Wang & Chen, FERC 2018). The operating
   guides set *how many* pocket resources to commit for the next day's peak hour, to survive N-1-G-1 / two
   contingencies (2025 SOM, fn 7). **No public source publishes the count, the MW or the pocket import limit**
   for any year 2019–2025. This confirms miso-280 §2 and miso-284 §3. New evidence (§1) narrows the gap but does
   not close it.
2. **Pocket→plant map: sourced.** MTEP15 VLR study (PUCT 46416, Exh. CWL-5 p.7–13) lists the op-guide VLR units
   by pocket, plus six "group-out" studies. Each one finds that losing that group causes N-1/P3 thermal or voltage
   violations at 2024 summer peak. That map is from source, not by hand.
3. **A replacement covers ~77 % of the floor, not all of it.** Of the energy the ST_GAS floor carries (keeper − arm
   B, model plant basis, 2019–22 mean), 7.7 of 10.0 TWh/yr sits on five MTEP15-listed plants. Harding Street (IN,
   1.08 TWh/yr) and ~1.2 TWh/yr on non-pocket South/Midwest steamers are **not VLR**. A VLR requirement drops
   them. Rule 19 says that is correct: a different phenomenon, self-commitment, should not ride on a VLR mechanism.
4. **Commitment alone recovers only a minority of the lost energy.** A "≥ 1 unit per MTEP15 group" u-floor at the
   UC's own min-load adds **~1.4–1.8 TWh/yr** over arm B (§4). The C1 gap arm B opened was 4.6–6.1 TWh/yr.
   The UC's `uc-params` min-load for these steamers (mlf 0.07–0.14) is about **half** what CEMS shows them
   operating at (P5-of-online 0.20–0.30; Nine Mile sits at its floor, P5 ≈ P25 ≈ 203 MW/unit). The rest of the
   floor's energy is out-of-merit **dispatch above min-load**, which a commitment requirement does not represent.
5. **Rule 13 (forward):** the *form* has a forward story (eligible sets shrink on dated retirements; documented
   relief criteria). The *level* does not, unless it is the structural minimum (§3, option A). No backcast series
   of the requirement exists either. **This is the owner's ruling (§5 Q1).**

## 1. Sources searched (step 1)

| source | on disk? | what it gives | class |
|---|---|---|---|
| MISO SOM 2022–2025 body, 2024 appendix (Potomac; 2023/24 sha256-verified against `data/raw/MISO/SHA256SUMS.txt`, 2025 likewise) | gitignored, re-fetched to scratch | DA/RT RSG $ for VLR by Midwest/South (e.g. DA VLR 2024 $11.2 M, 2025 $23.5 M); "two load pockets in MISO South"; SETEX op guide replaced Western op guide Aug 2022; WOTAB op guide updated Aug 2022 for a 1 GW CC (2021); SETEX aligned to reserve Zone 7 + STR via RPE from Sep 2025; **fn 7 (2025): op guides "tell them how many resources they need to commit for the next day … for the peak load hour"** | outcome ($); structure (form, dates) |
| Wang & Chen, *Uplift Allocation of VLR Constraints*, FERC tech conf 2018 (`ferc.gov/…/T3-2_Wang.pdf`, sha256 `1b328f40…`) | no | VLR = **minimum commitment, minimum capacity, complex binary** constraints in SCUC; commit-reason table by pocket exists inside MISO | form |
| MISO, *VLR Commitment in MTEP Economic Planning* (Dec 2018, `cdn.misoenergy.org/…125163.pdf`, `9a8e13ea…`) | no | MISO's **forward** representation: FBCO, commitment-only N1G1 flowgates (WOTAB, DSG) + Amite South interface = import limit − 850 MW; relief criteria (new transmission; base-load additions; 10-min quick-start ≥ largest-unit loss); load-trigger method considered and rejected | form + forward story; limits not published (CEII powerflow) |
| PUCT 46416 Exh. CWL-4/5 (MTEP15 VLR study, `interchange.puc.texas.gov/Documents/46416_65_921352.PDF`, `9fb334af…`) | no | op-guide VLR unit list by pocket (~10,850 MW); group-out scenarios A–F with MW; no requirement count/MW | **pocket→unit map** |
| MTEP24 Voltage Stability (PSC 2024-07-24, `cdn.misoenergy.org/…640142.pdf`, `e526f7fe…`) | no | 2029 model: Amite South instability at +3 GW load growth, DSG +3 GW (SOL 5,960 MW), SETEX +1 GW | margins (deltas), not base limits |
| MTEP22 Ch. 4 | no | qualitative pocket description; no limits | — |
| MISO `Resource_Uplift_by_Commitment_Reason.xlsx`, `Historical_RT_RSG_Commitment` (miso-284 §3) | no | post-DA / RT only; LRZ 9/10 absent | outcome |

`misoenergy.org` HTML still returns 403. `cdn.misoenergy.org` is reachable now (miso-284 hit a 403). The
miso-280 lead, a DA "Commit Reason" report back to 2019, was **not** found. **No intake is specified.** No
candidate carries the quantity, so fetching more would be speculative.

## 2. Rule-13 test (step 2)

| element | forward-producible from forward drivers? | responds to changed conditions? |
|---|---|---|
| eligible set per pocket (MTEP15 list ∩ fleet) | yes: shrinks on dated retirements (EIA-860) | yes (retirement); **no** for op-guide updates (Aug 2022 WOTAB/SETEX), which are dated events, not driver-derived |
| requirement count N or MW | **no public driver.** Physics (pocket load vs N-1-G-1 import) needs CEII limits and pocket load (neither published; EIA-930 MISO subregions are LRZ-scale) | — |
| "≥ 1 per group" (structural minimum, §3 A) | yes, held constant; relief only by documented, dated criteria (FBCO §2.3) | partially |
| N identified from CEMS conduct (§3 B) | re-derives from each CAMPD vintage (the incumbent floor's own class) | lags; fits the conduct it explains (refused by nyiso-97 §5 / miso-284 §4) |

**Plainly:** only a backcast trace of *conduct* exists (CEMS sync of the eligible units). There is no measured
series of the *requirement*. Precedent conflicts: the incumbent per-plant floor is conduct-identified and
admitted, while the per-pocket analogue was refused in miso-284 §4. Reconciling the two is an owner ruling.

## 3. Design options (step 3; all are u-floors in the UC window, never P floors)

The row, per pocket group k and window hour t, over the integer `u` of the group's plant clusters:

`Σ_{c ∈ G_k} u[c,t] ≥ min(N_k, Σ_{c ∈ G_k} avail_units[c,t])`

- Availability-relaxed, so an outage never forces an unavailable unit and the row is never infeasible.
- Committed units dispatch freely from `mlf·p̄·a` upward (rows (a)/(b) unchanged).
- It enters P1 only through the existing MECH 28 per-unit-hour bounds.
- No markup. Start/no-load paid once (uc-1.5 basis).

| option | N_k | window | driver | forward story | DOF | known risk |
|---|---|---|---|---|---|---|
| **A: structural minimum** (recommended for the test) | 1 per MTEP15 group present in the fleet. Group-out ⇒ violation is the source; ≥ 1 is the least commitment consistent with it. | all hours (daily next-day-peak commitment, fn 7) | op-guide N-1-G-1 pocket need (MTEP15, SOM) | hold; a group ends when its last unit retires (EIA-860) | 0 fitted; group sets from source | Amite South: the measured eligible-steam ≥ 1 share is 0.32–0.71 in 2021–25 (new in-pocket CCs relieved it). Floor binds where the meter is dark ⇒ **D-4 FAIL expected** (rule 17). |
| A′: A without Amite South from 2021 | as A | as A | + dated relief: St. Charles CC 2019 / SOM 2022 "three new CCs reduced the need" | as A | 0 fitted; 1 dated judgment | the date is read off conduct (the measured collapse) |
| B: conduct-identified N | P5 of measured eligible-unit count by pocket × month (pooled CEMS) | all hours | as A | re-derive per CAMPD vintage | ~4 pockets × 12 | the refused identification route |
| C: hold | — | — | — | — | — | keeps the floor (arm A, R) or arm B's 4.6–6.1 TWh/yr gap |

Groups in the model fleet (MTEP15 → model clusters, uc-1.5 logs):

| pocket | MTEP15 group | model cluster | N (A) |
|---|---|---|---|
| Amite South | A: Waterford 1,2 · Little Gypsy 1–3 | 8056 (n=1) ∪ 1402 (n=2) | 1 |
| DSG | B: Ninemile 3–5 · Michoud (retired 2016) | 1403 st_gas (n=2) | 1 |
| WOTAB | D: Sabine 1–3 · E: Sabine 4–5 · C: Nelson 4 (absent from fleet/CAMPD) | 3459 (n=4, one cluster) | 2 (D + E) |
| Western | F: Lewis Creek 1,2 (Frontier/San Jacinto are cogens, not in the ST_GAS fleet) | 3457 (n=2) | 1 |

Sabine's D/E split cannot be enforced within one n=4 cluster, so N=2 on the cluster approximates it (CEMS mean
online 1.7–2.6 units, 2019–25).

## 4. Zero-LP readings

**Floor energy by plant** (keeper − arm B, P1 `unit_marginal`, 2019–22 mean, TWh/yr; `split.py.txt`). This basis
reads ~10 TWh/yr, about twice the C1 basis (4.6–6.1 TWh/yr). C1 votes plant class from EIA-923; this table uses the
model's `plant_group`. Shares are comparable; levels are not.

| group | keeper | arm B | floor carries |
|---|---|---|---|
| MTEP15 pocket plants (Nine Mile, Sabine, Lewis Creek, Little Gypsy, Waterford) | 9.84 | 2.12 | **7.72** |
| Harding Street (IN, AES; not VLR) | 1.19 | 0.11 | 1.08 |
| all other floored steamers (Teche, Baxter Wilson, Big Cajun 2, Brame, Ames, …) | 2.29 | 1.06 | 1.24 |

**Measured eligible-steam synchronization by pocket** (CAMPD hourly; `pocket_sync_campd_2019_2025.csv`). Share of
hours with ≥ 1 eligible unit online:

| pocket | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Amite South | 0.91 | 0.80 | **0.39** | **0.58** | **0.32** | **0.65** | **0.71** |
| DSG | 0.94 | 0.94 | 0.81 | 0.92 | 0.75 | 0.90 | 0.95 |
| WOTAB (Sabine) | 0.95 | 1.00 | 1.00 | 0.88 | 0.90 | 0.83 | 0.88 |
| Western (Lewis Creek) | 1.00 | 0.94 | 0.97 | 0.95 | 0.82 | 0.90 | 0.93 |

Arm B holds those groups at 0–0.59 (uc_schedule on-share 2019/2022: Nine Mile 0.28/0.25, Sabine 0.09/0.09, Lewis
Creek 0.59/0.46, Little Gypsy 0.08/0.01).

**Option A sizing vs arm B** (unit-hours below N × cluster min-load; `sizing.py.txt`, `sizing_armB.csv`). Group A
is met by Little Gypsy, the cheapest member to hold (Waterford mlf 0.31):

| year | DSG+WOTAB+Western | + Amite South (LG) | arm-B C1 ST_GAS gap opened |
|---|---|---|---|
| 2019 | +1.36 TWh | +1.62 | 4.90 |
| 2020 | +1.11 | +1.37 | 6.05 |
| 2021 | +1.52 | +1.80 | 5.11 |
| 2022 | +1.37 | +1.63 | 4.60 |

This is a lower bound: committed units may dispatch above min-load where economic. The structural reading is that
a VLR commitment requirement restores roughly ¼–⅓ of what the floor carried.

**The min-load gap** (CEMS 2023–25, P5 of online gross / unit max vs UC `mlf`):

| plant | CEMS | UC `mlf` |
|---|---|---|
| Nine Mile 4, 5 | 0.26, 0.26 | 0.136 |
| Sabine | 0.20, 0.16, 0.37, 0.12 | 0.095 |
| Lewis Creek | 0.21, 0.21 | 0.107 |

At CEMS min-loads the option-A increment roughly doubles, to an estimated ~2.5–3.5 TWh/yr. That is a rule-14/23
question for the `uc-params` derive (it rides the r11 per-unit re-derive queue), not this lane's to change.

## 5. Owner questions (routed via UC-DESK)

1. **Level (rule 13/21):** A (structural ≥ 1 per MTEP15 group; Amite South D-4 risk declared) · A′ (+ dated Amite
   South relief) · B (conduct-identified, reversing miso-284 §4) · C (hold). **Recommendation: A**. It is the only
   option with zero fitted values. Its known D-4 exposure is declared ex ante, not hidden.
2. **Non-pocket floor energy** (Harding Street 1.08 + others 1.24 TWh/yr): accept the loss under one-mechanism
   (recommended), or charter self-commitment as its own phenomenon later. Do not keep the per-plant floor for these
   plants beside the VLR row: that would be two mechanisms on one class (rule 19).
3. **Min-load basis:** test at the `uc-params` mlf as is (recommended; rule 23), and route the CEMS LSL gap to the
   per-unit re-derive item already in the r11 queue.

## 6. Matrix

`scuc_load_pocket_commitment` (MISO) stays **G**: no LP has been run. This FINDING is new evidence (documented
form; sourced group map; forward-planning analogue). It supports reopening the cell, but the owner's r13 ruling
reopens it, not this lane. The cell is updated in the session that tests it (rule 28).
