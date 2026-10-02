# Algonquin Citygates daily price intake — research report (retrieved 2026-10-02)

Files: `transcription.csv` (63 rows), `SHA256SUMS` (all saved PDFs/HTML), `dash/` (78 EIA New England Dashboard daily archive PDFs), `build.py` (regenerates CSV from saved files).

## Found

### A. EIA New England Dashboard daily archives (best source: explicit daily Algonquin number)
URL pattern `https://www.eia.gov/dashboard/new-england-energy-api/archives/YYYYMM/YYYYMMDD_new_england_dashboard.pdf`.
Each daily snapshot (≈10:00 AM ET) prints, as text, "<x> $/MMBtu  Spot natural gas price (Algonquin Citygate) <m/d/yy>".
Notes page: "This indicator shows the most recent spot price of natural gas at the Algonquin Citygate (Boston) ... S&P Global Market Intelligence is the source".
Weekend/holiday snapshots print "-- $/MMBtu" (no value): 2022-01-08/09/15/16/17/22/23/29/30, 2022-12-24/25/26/31, 2023-01-01/02, 2023-02-04/05, 2025-01-18/19/20/24/25/26, 2025-06-21/22/28. 2022-01-11 and 2022-01-31 archives return 404.
2025-01-24 is a weekday with "--".

Date basis: the source does not define it → CSV says `unspecified`. Evidence it is the FLOW (gas) day:
 - Dashboard 12/23/22 = 30.16 and 12/22/22 = 6.54 match ISO-NE IMM's statement that the gas price stepped from $6.66 to $30.05 at HE11 Dec 23 (start of gas day Dec 23).
 - Dashboard values track EIA NGWU (NGI, which reports by trade day) shifted by +1 day: NGWU Wed 2022-01-05 11.56 vs dash 1/6 11.32; Wed 1/12 18.96 vs 1/13 18.00; Wed 1/19 22.69 vs 1/20 22.75; Tue 1/25 24.62 vs 1/26 25.00; Wed 1/26 20.71 vs 1/27 21.20; Wed 2022-12-21 6.51 vs 12/22 6.54; Wed 2025-01-15 14.75 vs 1/16 14.89; Wed 2025-01-22 18.99 vs 1/23 19.25; Wed 2025-06-25 2.61 vs 6/26 2.63; Wed 2023-02-08 2.52 vs 2/9 2.52.
 - Dashboard 12/27/22 = 35.00 (Tue after the Christmas holiday Monday) is most likely the weekend/holiday package traded Fri 12/23 for flow 12/24–12/27; ISO-NE composite daily averages for Dec 24–27 were $33.52–35.99. Not stated by the source — do not assign it to 12/24–12/26 without that inference being declared.
Snapshot-time caveat: dashboard is a 10 AM "most recent" figure, not a published settled index; 2022-01-03 (5:16 PM), 2022-01-07 (11:55 AM), 2022-01-14 (2:39 PM) were updated at other times.

### B. EIA Natural Gas Weekly Update — mentions the repo scraper missed
 - 2023-02-09 release: "Last Thursday, February 2, the price at Algonquin Citygate spiked to $71.42/MMBtu" (NGI; calendar-dated → likely trade date 2/2 for flow 2/3).
 - 2022-01-27 release: daily high $24.62 "on Tuesday" (= 2022-01-25).
 - 2022-01-20 release: weekly high $26.94 "in advance of the holiday weekend" (day not named; report week 2022-01-13..19, MLK weekend → probably Fri 1/14 trade, not stated).
 - 2025-06-26 release: "mid-week high of $6.75/MMBtu" (day not named; week 2025-06-19..25).
 - 2022-12-29 and 2023-01-05 NGWU pages exist but are empty shells (no release) — confirmed.
 - EIA NGWU daily spot tables list only Henry Hub, New York, Chicago, Cal. Comp — no Algonquin.

### C. ISO-NE IMM reports — composite, NOT Algonquin-only
All ISO-NE IMM gas prices are "the weighted average of the Intercontinental Exchange next-day index values" over several hubs (W2023/W2022 QMR: Algonquin Citygates, Algonquin Non-G, Portland, TGP Z6-200L; 2022 AMR adds TGP North, TGP South, Maritimes & Northeast). "Next-day implies trading today (D) for delivery during tomorrow's gas day (D+1)."
**Conflict with the brief:** the 2022 AMR $35.37 (Dec 24–27) is this composite, not an Algonquin Citygates average.
Recorded (labelled composite in source_title): 35.37 avg Dec 24–27 2022; 6.66 (gas day 12/22) and 30.05 (gas day 12/23); 35.99 Dec 24 ("average system gas price"); 76.42 for the Feb 3 2023 gas day; 22.99 avg Jan 8–31 2022.
Not recorded as rows (ranges / undated): "December 24-27 ($33.52-$35.99/MMBtu) and February 3-4 ($37.47-49.68/MMBtu)" daily-average ranges (W2023 QMR PDF 9/printed 7); Winter 2023 max $49.68 (PDF 60/printed 58); "On February 3rd ... spot natural gas price rose to $76/MMBtu" (PDF 21/printed 19, rounded duplicate). W2022 QMR: max $29.42 on Dec 19–20 2021 (outside targets); "Algonquin Citygates trading hub trades infrequently (only once in Winter 2022)" on ICE — the IMM uses Algonquin Non-G as proxy (PDF 27/printed 20). Relevant: ICE Algonquin Citygates is illiquid; NGI/S&P assessments differ from ICE.

### D. EIA Today in Energy
 - id=51158: Algonquin averaged $20.55 in January 2022 (monthly avg, recorded); "exceeded $28/MMBtu on several days" (undated, not recorded).
 - id=66984: Jan 2025 avg $16.37, Feb 2025 avg $14.00 (monthly; not a target, not recorded).
 - id=55139, id=61563: no Algonquin numbers.

## Conflicts between sources
 1. Feb 2–3 2023: NGWU (NGI) $71.42 for Thu Feb 2; ISO-NE composite $76.42 for the Feb 3 gas day; EIA Dashboard (S&P, 10 AM snapshot) prints only $26.06 for 2/3/23. Dashboard 2/1/23 = 4.85 vs NGWU weekly high $13.49 on Tue 1/31. The Feb 2023 dashboard snapshots appear not to reflect final assessed indices for those days — treat 2023-01-31..02-03 dashboard values with caution.
 2. Dec 24 2022: ISO-NE composite $35.99 (electric-day vs gas-day basis not stated in that sentence) vs dashboard 35.00 (12/27 label; likely the holiday strip).
 3. ISO-NE W2023 QMR fn 4 says gas day ends "hour ending 11 on D+2", fn 42 says it "ends at HE 10 ... the following day"; fn 17 says "HE 10 on one day to HE 9" — internal inconsistency in gas-day hour definitions.

## Searched, not found / not usable
 - FERC-NERC Winter Storm Elliott final report (Nov 2023): ferc.gov returns 403/Cloudflare challenge to curl and WebFetch; nerc.com legacy URLs 404 and new globalassets path not found. Not checked.
 - ISO-NE Monthly Market Operations Reports Dec 2021→Jan 2022, Dec 2022, Jan 2023, Feb 2023: gas only as % change and charts — figure only, not transcribed. Jan/Jun 2025 report URLs (guessed pattern) not found.
 - Potomac Economics 2022 EMM report (iso-ne.com): "gas price indexes rose above $30/MMBtu" only.
 - EIA Dashboard 2022 snapshots: "Algonquin Citygate Basis to Henry Hub" stale (-0.27, dated 7/13/20) — unusable for 2022; 2022-12+ basis values are live but not transcribed (basis, not price).
 - ISO-NE markets committee presentation on Dec 24 2022 capacity scarcity: not located in time.
 - Target 2022-12-24/25/26 and 2023-02-04/05 (weekend) dailies: no single-day Algonquin print exists in any free source found; only the ISO-NE composite range/average and the dashboard 12/27 strip value.
