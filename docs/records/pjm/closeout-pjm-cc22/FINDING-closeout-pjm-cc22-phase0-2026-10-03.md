# FINDING — closeout-PJM-cc22 phase 0: the 2022 CC_REGULAR over-run has no admissible lever with reach (ZERO LP)

**Verdict: NOT CHARTERED.** Nothing built, solved or registered. Keeper `2026-10-03-closeout-pjm-nuc-keeper` is
unchanged. Owner ruling R-56. Bars: `PRECOMMIT-closeout-pjm-cc22-phase0-2026-10-03.md`.

Probes (zero LP) and their outputs:
- `scripts/probes/_closeoutpjm_cc22_plants.py` → `_closeoutpjm_cc22_plants.json` (per plant × year)
- `scripts/probes/_closeoutpjm_cc22_ledger.py` → `_closeoutpjm_cc22_ledger.json` (system ledger vs EIA-930 and the bench)
- `scripts/probes/_pjmnext16_cc_loading.py`, re-run on this keeper → `_closeoutpjm_cc22_loading.json` (LOAD / ON / OFF
  by hour class)
- `scripts/probes/_closeoutpjm_cc22_window_reach.py` → `_closeoutpjm_cc22_window_reach.json` (candidate A)

All outputs are under `results/phase0/pjm/`.

## 1. Decomposition of 2022 C1 CC_REGULAR (+8.96 TWh, model 306.92 vs bench 297.97)

**By month** (model − actual, TWh, bench plants):

| J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|
| +0.04 | +0.07 | +1.31 | +1.00 | +1.79 | +1.11 | +0.86 | +0.88 | +0.76 | +0.83 | +1.14 | **−0.83** |

**By zone**, 2022 against the other years:

| zone | 2019 | 2020 | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Central_PA | +5.5 | +4.4 | +2.3 | **+5.4** | +3.5 | +2.9 | +1.1 |
| ComEd | +1.2 | +2.0 | +2.8 | **+3.9** | +4.6 | +4.4 | +5.0 |
| EMAAC | +10.2 | +5.3 | +5.2 | **+3.2** | +8.7 | −1.2 | −9.6 |
| Dominion | −9.8 | −5.8 | −7.5 | **−2.4** | −12.6 | −4.3 | −1.8 |
| SWMAAC | −4.3 | −4.0 | −3.5 | **−1.6** | +0.5 | −4.1 | −4.2 |
| class | +3.6 | +6.0 | +0.8 | **+9.0** | +3.4 | −5.0 | −12.6 |

**Hour class** (NEXT-16 split; LOAD = both on, ON = model on / actual off, OFF = actual on only):

| TWh | 2019 | 2020 | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| LOAD | +0.6 | +0.9 | −3.4 | **+3.7** | −0.4 | −8.4 | −12.6 |
| ON + OFF | +2.8 | +5.0 | +3.7 | **+5.2** | +3.9 | +3.4 | −0.1 |

- 2022 LOAD is +3.2 night / +0.5 day. It falls in the three lowest demand deciles (+1.7 / +1.2 / +0.9).
- The hourly correlation of LOAD with Δcoal is −0.45: in 2022 troughs the model loads CC where the real fleet held coal.

**Class offsets in 2022**, model − bench:

| Class | TWh |
|---|---|
| CT_PEAKER | −5.38 |
| ST_GAS | +2.70 |
| CC_CHP | +1.19 |
| COAL_BIT | +6.97 |
| COAL_PRB | +1.76 |

- Model generation exceeds `classFull` by **+15.8 TWh**, the largest of any year (2019 +12.8, 2021 +8.6, 2023 +6.3,
  2024 −0.6).
- This sits in `U_a` = EIA-930 net generation − `classFull` = **21.7 TWh**. That is generation EIA-930 carries and
  the 923 bench does not.
- Model demand equals EIA-930 demand to within 0.1 TWh. Model net export is 9.9 TWh short of real.

## 2. Answers

- **Q1 Elliott: no.** December CC is −0.83 (under). Elliott is the C3a/C3b 2022 object (R-26), not the CC one.
- **Q2 Gas-price months: no.** The excess is flat at about +1 TWh a month from March to November. It does not peak in
  the Aug–Sep price peak, and January/February are about 0.
- **Q3 Capability / availability: no.**
  - Plant-months with the model on and actual dark total 0.17 TWh in 2022 (0.26 in 2021, 0.29 in 2023).
  - Heat rate and summer capability are already falsified (pjm-h1, pjm-h21).
  - The NEXT-16 2022 boundary hole (Morgantown 1573, Waukegan 883) is closed: both plants are in the 2022 LP fleet
    under `partial_plant_exit_carry` (K, W0).
- **Q4 The measured-nuclear displacement: trigger, not cause.** It moved CC by +1.0 TWh (RESULT R2). The pre-existing
  +7.95 TWh had stood 0.05 TWh inside the band.
- **Root cause: three persistent structures, one 2022 term, and a broken zonal cancellation.**
  1. **ON/OFF commitment surplus**, +2.8 to +5.2 TWh every year. Its levers are adjudicated R (`pjm_gas_commitment_bridge`,
     `cc_mustrun_conduct_window`).
  2. **The CT_PEAKER deficit** (−5.4 in 2022). This is the R-36 frontier, out-of-merit CT commitment, and is not a
     lever. Gas the model does not burn in CTs lands in CCs.
  3. **North-over / south-under locational split** (pjm-h21). Its levers are W5, `zonal_gas_basis` (hub series
     DATA-BLOCKED) and `internal_congestion_split` (G).
  4. **The 2022 trough term** (LOAD +3.7, against −3.4 in 2021 and −0.4 in 2023). The coal and CC econ ladders sit
     within $3 in 2022 (61.7 vs 58.9, NEXT-16), so the trough split between them is a knife-edge.
     - The keeper's 2022 coal offer runs **+11.0 $/MWh above measured going cost**. In NEXT-34's dark spells the
       sigmoid at its 1.32 ceiling adds +8.1 and the mid-curve floor +8.3.
     - That offer sits about 4 $/MWh above PJM's own measured LONG_RUN offers.
  5. **The zonal cancellation fails in 2022.** Dominion's usual under-run (mean −7.4 in the other years) is only
     −2.4.
     - Five Dominion CCs carry **+6.7 TWh** of the 2022-specific anomaly (model Δ − actual Δ vs the 2021/2023 mean):
       Greensville +1.76, Tenaska VA +1.22, Bear Garden +1.21, Brunswick +1.12, Potomac +0.99.
     - Dominion's relative CC cost tracks this: +15 % over the fleet mean in 2022 against +45 % in 2023. That cost
       comes from the EIA-923 receipts, i.e. the Dominion basis question.

## 3. Reach table (static, keeper P1 dispatch; CC class Δ at replacement share s = 0.35 / 0.50)

| candidate | 2022 CC Δ | B1 (≤ −0.96) | other years | admissibility |
|---|---|---|---|---|
| **(A)** `mustrun_online_frac_per_year`: CC committed window at own-year CEMS share. The pooled window is the 2023–25 vintage applied to 2020–22. Existing field, artifact on disk, zero src. | **−0.37 / −0.28** (released 0.95 TWh, forced 0.38). Released MW is in Doswell, Tenaska VA, CPV St Charles, Warren: already-UNDER Dominion/SWMAAC plants. | ✗ | 2020 +0.09/+0.07, 2021 −0.34/−0.26, 2023 −0.67/−0.52, 2024 +0.03/+0.02, 2025 −0.13/−0.10 (already FAIL −12.64), 2019 none (no own-year row) | admissible (rule 14/17 vintage repair; coal sibling `coal_sync_online_frac_per_year` is K). Wrong zones for this object. |
| **(B)** nuclear CF row un-clip (the R-35 rows clip at 1.0; model nuclear −0.78 vs the 923 bench in 2022) | ≤ −0.37 (at the R2 share 0.48) | ✗ | every year, same sign | needs a derive-convention change (rule 23 question); not sized beyond the upper bound |
| (A) + (B) jointly | −0.65 to −0.74 → **+8.22 to +8.31** | ✗ | — | — |
| (C) coal offer toward PJM's measured offers in 2022 troughs | moves CC → COAL_BIT about 1:1 | knife-edge | COAL_BIT 2022 +6.97 has 1.03 TWh of headroom against CC's 0.96 need | the channels are adjudicated (`coal_passthrough_sigmoids` gas_mid R; `pjm_replacement_cost_fuel` R); a year-specific cut would be a tuned value (rule 1). Not chartered. |
| (D) Dominion zonal basis (daily Z5/M3) | would restore the cancellation, not fix CC | — | — | DATA-BLOCKED (R-26 / §3.6 L4) |

**C3a/C3b 2022.** No candidate moves the Elliott hours. They stay R-26 data-limited.

## 4. Reading

The 2022 flip is the sum of four standing, already-adjudicated structures, plus a coal/CC trough knife-edge whose only
operands are adjudicated offer channels. No admissible lever reaches B1, alone or paired.

(A) is a genuine rule-14/17 vintage defect: CC windows for 2020–22 are sized on 2023–25 CEMS, while coal's already
runs per year. It is recommended as hygiene to ride with the next PJM re-solve, and not as the CC 2022 fix: it cuts
CC in the zones that are already under.

**Recommendation to the desk:** record 2022 C1 CC_REGULAR as a NOT-YET criterion with this attribution:
- CT frontier R-36;
- the zonal basis W5 / DATA-BLOCKED;
- the trough knife-edge.

The owner rules. Charter no shards.

## 5. Desk items (not patched here)

1. **Generation-accounting residual.** In every keeper year, model generation − net export − storage net − demand is
   +2.2 / +2.2 / +2.6 / +3.1 / +2.5 / +3.4 / +4.0 TWh, with zero slack and zero dump.
   - NEXT-16 booked this as "losses". The PJM LP has no line losses (`link_loss` is MISO-only).
   - It is unattributed energy that fossil supplies. It is worth one zero-LP trace (hydro/pumped storage or
     curtailment accounting).
2. **The by-year artifact has no 2019 rows**, so (A) is inert in 2019.

## 6. Matrix (PJM shard only)

| Cell | Change |
|---|---|
| `mustrun_online_frac_per_year` | stays **U**; evidence appended: sized at phase 0 (§3 A), not solved, admissible, below the bar for this object, recommended as hygiene |
