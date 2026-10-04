# FINDING closeout-SOCO-w3 phase 0b: the CC over-run the holdout exposed — coal commitment state is NOT CHARTERED

Lane closeout-SOCO-w3, 2026-10-04. Zero LP. Desk direction (2026-10-04): go after the CC over-run the holdout
exposed, stacked on the holdout recipe, with probe `2026-10-04-closeout-soco-w3-btm` as the control.

Control: `results/calibration/closeout_soco_w3_span` (probe payload and bench parts on `claude/closeout-soco-w3-reg`).
Probes: `scripts/probes/_closeout_socow3_coal_hold.py`; census `coal_census_probe.csv`.

## 1. Shape (model − CEMS, by hour of day, probe)

| Year | CC_REGULAR night (00–04h) / afternoon (13–19h), MW | COAL_BIT, every hour, MW | CT_PEAKER daytime, MW |
|---|---|---|---|
| 2019 | +2,160 to +2,250 / +300 to +750 | −900 to −1,450 | +850 to +1,150 |
| 2021 | +1,490 to +1,670 / +20 to +360 | −490 to −720 | −160 to +230 |
| 2023 | +1,520 to +1,670 / −240 to +320 | −390 to −610 | +900 to +1,200 |

CC over-runs at night and coal BIT under-runs around the clock in every year. This is the closeout-SOCO-2 §b shape,
now larger, because the holdout restored 7–9 TWh/yr of net load.

## 2. Where the coal deficit sits (CEMS vs model, per plant, `coal_census_probe.csv`)

| Plant | What differs | 2019 | 2023 | 2024 |
|---|---|---|---|---|
| Bowen (703) | **loading**: online share matches (0.93 / 1.00 / 0.99 both), night MW model vs metered | 944 vs 1,300 | 893 vs 1,215 | 899 vs 1,262 |
| Gaston (26) | **loading**: online share matches; night MW below the metered online P5 (409–552 MW) | 193 vs 345 | 112 vs 222 | 115 vs 225 |
| Barry (3) | **commitment**: online share model vs metered | 0.53 vs 0.95 | 0.36 vs 0.45 | 0.34 vs 0.20 |
| Wansley (6052) | **commitment** | 0.02 vs 0.43 | — | — |
| Miller, Scherer, Daniel | near actual (must-run bands at availability) | | | |

**It is not availability.** Hours where Bowen's metered output exceeds the model's available Bowen capacity carry only
0.51 / 0.28 / 0.66 TWh (2019 / 2023 / 2024). Bowen's and Gaston's committed bands are offered at $34 / $47 per MWh
against CC at about $20, so the LP loads them only to their must-run bands (which run at availability in every hour).

## 3. Candidate: a coal commitment state (relaxed UC: online state, measured min-load, start cost, min-down)

This is the SPP/ERCOT posture construction ported to SOCO coal. It would need a new ISO-scoped field. It is U in
spirit; no SOCO cell exists because the posture fields are ISO-exclusive.

**What it can reach.** A commitment state keeps a unit online through a trough when the start cost exceeds the night
saving. It holds the unit at its minimum. It cannot load a unit that is already online above its minimum.

**Upper bound** (`_closeout_socow3_coal_hold.py`): hold every coal plant at its metered online P5 through every day
the model already has it online.

| Year | Held coal (TWh) | Of which Barry | Probe CC_REGULAR vs band |
|---|---|---|---|
| 2019 | 1.66 | 0.45 | +6.23 TWh (passes on share) |
| 2020 | 0.95 | 0.67 | +3.46 (PASS) |
| 2021 | 0.96 | 0.37 | **+8.63; needs ≈ −1.5 TWh to re-enter the 7.10 band** |
| 2022 | 0.75 | 0.39 | +4.80 (PASS) |
| 2023 | 1.00 | 0.87 | **+7.57; needs ≈ −0.5 TWh (band 7.04)** |
| 2024 | 0.88 | 0.54 | +6.48 (PASS) |
| 2025 | 0.83 | 0.59 | (skipped, preliminary vintage) |

**Bar (stated with the reading, not pushed ahead of it: the desk's target is the two undeclared flips):** charter only if the upper bound can return both undeclared flips (CC 2021 and
2023) to PASS at full displacement from CC. **2021 fails at 100 % displacement** (0.96 < 1.53 TWh). 2023 would need
≥ 53 % of the held coal to displace CC, with no margin left for the CT daytime over-run. **NOT CHARTERED.**

The commitment *decision* gaps (Barry, Wansley) and the Bowen/Gaston *loading* gap are a price question: Southern
loads coal its own F923 books price $13–16/MWh above CC (closeout-SOCO-2 §b). The routes that would change that
price are adjudicated G/R in `SOCO.js`: take-or-pay as a price was refuted on pre-fixed gates (closeout-SOCO-3 S1/S2),
and `coal_takeorpay_committed` is G. A commitment state cannot produce it.

## 4. Other levers checked for this object

| Lever | Reading | Disposition |
|---|---|---|
| `coal_sync_srmc_tranche` + `coal_mustrun_online_pmin` (+ `coal_sync_ensemble_level`) | requires re-sizing must-run to the online Pmin: Bowen 60 % → 14.1 %, Scherer 34.9 % → 16.5 % of nameplate. That removes about 1.5 GW of cheap coal floor where coal is already short, against about 0.5 GW of new forced floor at Barry/Gaston/Crist/Wansley (online Pmin × online share) | wrong sign; not chartered |
| `coal_committed_nested_on_mustrun` | lowers the committed band of always-online plants | wrong sign |
| CT daytime over-run (+0.9–1.2 GW) | the CT/ST split recorded as start/no-load physics (`tranche_startup_amortization` G, owner closed the reopen at soco-92) | no new evidence |

## 5. Verdict

The CC over-run exposed by the holdout is the SOCO-F1 object, sharpened: the remaining gap is coal **loading** at
Bowen and Gaston plus coal **commitment** at Barry/Wansley, against offers 1.7–2.4× CC's. A commitment state reaches
at most 0.8–1.7 TWh/yr and cannot clear CC 2021. No other admissible lever is open. The lane's candidate list is
exhausted. This is new evidence for frontier row SOCO-F1 (the census above), and its re-open condition (Georgia PSC
FCR / Alabama ECR fuel testimony on burn plans) is unchanged.
