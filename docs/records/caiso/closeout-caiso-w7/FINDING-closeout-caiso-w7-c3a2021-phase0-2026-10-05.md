# FINDING closeout-CAISO-w7: C3a 2021 (+11.0 %), zero-LP phase 0 on the w6 basis (2026-10-05)

**Charter.** Desk, 05:13Z: work the remaining load-bearing failure, C3a 2021, on the w6 basis.
- Decompose it by month and hour.
- Name the marginal class.
- Check imports, hydro and gas.
- Search for unadjudicated mechanisms or rule-14 substitutions.

**Scope.** Zero LP. The basis is the w6 2021 leg, `results/calibration/closeout_caiso_w6_a1_2021` (shard commit
`8251547b`).

**Reference.**
- Scored: `rt_lw` = 51.07 $/MWh, the three trading hubs load-weighted, covering 2021-04-27 → Dec (the OASIS window).
- Model: 56.48, so C3a = +10.6 % on the scorer, +11.0 % as recorded.

## 1. The gap is a broad level offset, not a tail

Model demand-weighted λ (5 CAISO zones) vs the weighted trading-hub RT, Apr 27–Dec. This reproduces the scorer within
1 pp (+9.9 % here vs +10.6 %).

**By month.**

| Month | Apr* | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| gap $/MWh | +8.4 | +6.6 | +4.5 | **−3.8** | +7.4 | +3.3 | +8.5 | +8.0 | +8.8 |
| contribution (pp of C3a) | 0.25 | 1.52 | 1.16 | −1.11 | 1.36 | 0.86 | 1.96 | 1.75 | 2.11 |

**By hour (PST).** The model sits above RT in every hour except the 13–17 belly-to-peak:
- +$6–8 overnight;
- +$6–10 at hours 06–09;
- about −$5 at hours 16–17;
- +$10–13 at hours 20–23.

By block: night 0–5 +6.4 (2.7 pp), day 6–15 +4.3 (3.5 pp), evening 16–21 +3.3 (1.9 pp), late 22–23 +11.8 (1.9 pp).

**Marginal class.** Among zone-hours with an identifiable internal setter (offer within $0.50 of λ, 0 < MW < cap,
non-hydro):
- night: gas CC sets 97 %, at about $55;
- evening: gas CT sets 72 %, at about $73.

80 % of hours have a partially dispatched, hub-priced DSW/PNW import rung, i.e. the import ladder is marginal. Hydro
units carry the LP's "marginal" flag (they are energy-limited) but do not set λ.

## 2. Imports: right annual volume, wrong price basis

**Volume.**
- Net imports Apr 27–Dec: model 35.8 TWh vs EIA-930 37.4 TWh.
- The diurnal is mis-timed: the model is short 1.1–2.8 GW at hours 06–08 and 18–23, and long 0.7–1.4 GW midday.
- Neither intertie ever binds (DSW 10.6 GW limit vs about 6 GW flow; PNW 4.8 GW vs about 2 GW). Import volume is set
  by the ladder.

**Price.** The model's WECC_DSW node clears at roughly the CAISO λ, against measured Palo Verde RT:

| hour | 0 | 6 | 18 | 20 | 22 |
|---|--:|--:|--:|--:|--:|
| model WECC_DSW | 50.6 | 57.0 | 71.4 | 68.9 | 63.2 |
| PALOVRDE RT (measured) | 31.2 | 31.5 | 63.0 | 45.6 | 36.1 |
| PALOVRDE DAM (measured) | 47.6 | 52.0 | 99.7 | 70.1 | 53.8 |

**The structural point.** In printed hours the whole hub-priced import ladder is priced at the **OASIS DAM** intertie
print (`envelopes.py:586–767`, `wecc_intertie_lmp_hourly_CAISO.parquet`). This includes the DSW surplus, overnight,
daytime and late-evening clean rungs, and the CCGT, CT and scarcity tranches (hub + wheel + carbon).
- The measured RT − DAM spread at the interties is one-signed. It is measured on the model's own construction:
  delivered MCE + MCC + MCL, GHG excluded, nodes averaged per hub (`wecc_intertie_lmp_hourly_CAISO{,_rtm}.parquet`).
  - PALOVRDE: −5.8 $/MWh (2021 Apr–Dec), −15.9 (2022).
  - MALIN: −9.4 / −17.6.
  - Hourly, it is largest at hours 06 and 17–21 (MALIN −15 to −40 at hours 17–20).
  - The raw `LMP` column, which includes MGHG, reads larger: PV −13.9 / −20.7. The model never uses that basis.
- The model is an RT analogue scored on RT, and the rubric states that the DA−RT premium is a forward risk premium the
  LP must not price (`score_price_mean_da_diagnostic`).
- **Pricing the boundary at DAM imports that premium into λ through the import offers.** The model sits between DA
  and RT in every year: −5.0 % vs DA and +10.6 % vs RT in 2021.

**Reach (upper bound, greedy).** Lower λ by the hour's intertie RT−DAM, on the model's construction, in every hour
where a hub-priced rung is marginal (80 %), with no re-dispatch. This takes C3a 2021 from +9.9 % to **−2.5 %**.
Re-dispatch will absorb part of that, but the reach clearly exceeds the ~1 pp T1 needs.

## 3. Checked and excluded

| Candidate | Status |
|---|---|
| Hub-vs-DLAP C3a reference basis (+6.7 % on DLAPs vs +9.9 % on hubs) | **Closed ruling**: caiso-203 ruling 1, "C3a's RT basis is untouched". Also a rubric/reference change (rule 37). Not reopened. |
| DSW BAs' own EIA-930 net-load diurnal shape (the plan's "new zero-parameter lever") | **NOT CHARTERED** (closeout-CAISO-w2 §1, 0/4 years) and **DO-NOT-REDO** (closeout-CAISO-w4 S1). |
| `caiso_zonal_gas_basis` | Already in the keeper (w1 arm 2). Its 2021 effect was −0.1 pp. |
| DA/RT two-settlement (storage) | Closed (caiso-169/170, cell R). That is a storage-foresight object, not the intertie offer basis. |
| Gas price level | The CC offers track the measured monthly citygate × HR (SDGE CC econ bands $39 Jan → $63 Sep). No substitution found. |
| Hydro | Hydro is energy-limited and never the λ setter. 2021 drought is in the measured CF inputs. |

## 4. The candidate lever (one, new, rule 14)

**L1 `caiso_intertie_print_rt_basis` (default off, CAISO-only).**
- In hours where the measured **RTM** intertie print exists (PALOVRDE / MALIN), price the hub-priced import ladder at
  the RTM print instead of the DAM print.
- Elsewhere, the DAM print, then the existing gap-fill / formula chain, unchanged.
- One measured series swapped for another of the same market, on the settlement the LP and the scorer use.
- Zero fitted parameters.

**Data.**
- RTM intertie hourly is on disk for 2021 Apr 27–Dec and all of 2022, plus 1,272 hours of 2023.
- 2023-04-22+ through 2025 is fetchable from OASIS within its ~39-month retention (`fetch_caiso_oasis.py --datasets
  rtm --nodes PALOVRDE_ASR-APND MALIN_5_N101`).
- 2023 Jan–Apr 21 has aged out, so those hours stay on DAM.

**Admissibility question for the desk / owner.**
- The case for: the boundary price should be on the same settlement as the LP and the scorer, and the DAM print
  carries the very premium the rubric forbids the LP to price.
- The case against: most CAISO imports are DA-scheduled and paid the DA price, so an RT print could be read as a
  structurally wrong offer basis for import quantity decisions.
- This is the one judgement call in the lever. It is flagged rather than assumed.

## Addendum A: rule-13 circularity check (desk, 05:28Z). Legs held

**Method.** The intertie series are on the model's construction (MCE + MCC + MCL; MALIN = mean of MALIN_5_N101 and
CAPTJACK_5_N003). Each is compared hourly against the C3a reference (trading-hub RT LMP, weighted 0.3969 / 0.0646 /
0.5385).

| Year | Series | n | Pearson r | Spearman | Mean gap vs hub | MAE |
|---|---|--:|--:|--:|--:|--:|
| 2021 | PV RTM | 5,713 | 0.614 | 0.903 | −1.07 | 10.5 |
| 2021 | MALIN RTM | 5,713 | 0.868 | 0.853 | −1.90 | 6.2 |
| 2021 | PV DAM (incumbent) | 5,713 | 0.523 | 0.859 | +4.76 | 12.5 |
| 2021 | MALIN DAM (incumbent) | 5,713 | 0.503 | 0.835 | +7.48 | 13.2 |
| 2022 | PV RTM | 8,760 | 0.663 | 0.881 | −12.04 | 21.2 |
| 2022 | MALIN RTM | 8,760 | 0.739 | 0.683 | −10.25 | 22.0 |
| 2022 | PV DAM (incumbent) | 8,760 | 0.838 | 0.900 | +3.88 | 18.1 |
| 2022 | MALIN DAM (incumbent) | 8,760 | 0.837 | 0.883 | +7.31 | 19.2 |

**Reading.**
- The desk's numeric circularity test (r ≥ 0.95 with a small gap) is **not** met. The RTM intertie is no more
  correlated with the scored hub than the incumbent DAM print is.
- But both prints are outputs of the CAISO market itself.
- In 2021 the RTM intertie mean sits within $1–2 of the scored hub mean. C3a is a level test and the rung is marginal
  in 80 % of hours, so L1 would price the margin at about the answer's level exactly where it binds.
- In 2022 the RTM intertie runs $10–12 below the hub, which puts C3a 2022 (+7.1 %) at real risk of the low-side kill.

**No admissible external RT index on a free source:**
- EIA's ICE workbook is daily DA bilateral, peak block only.
- Powerdex and ICE hourly RT Palo Verde / Mid-C are licensed.
- SRP, APS and BPA publish no LMP.
- WEIM ELAP prices are CAISO-market outputs, so they are circular too.

**No forward-driver alternative.** A structural RT import-offer discount would be an offset sized to the DART residual,
which rule 13 forbids.

**Lane recommendation.** Record L1 as **I** (rule 13: same-market output, level ≈ the scored mean where it binds) unless
the owner rules otherwise as decision #22. The default-off build stays (rule 26 removal follows the ruling). No leg is
launched.
