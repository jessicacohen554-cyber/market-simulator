# DIAGNOSIS — CAISO evening merit stack: one defect, two symptoms (C1 CC-over/CT-under + the C3c summer DA tail)

**Session 2026-07-16 (Lane B, C3c tail-undershoot handoff + owner directive on the
C1 cluster). Status: diagnosis complete; winter half fixed by caiso-90
(`caiso_citygate_flow_date`); summer/evening half chartered, not built.**

All numbers below are measured on the caiso-89 keeper recipe re-solved at HEAD
(bundle `results/calibration/caiso89_chp_steam_floor`), CEMS = CAMPD
facility-level CA parquets (never EIA-930 for CAISO gas — the fabricated-block
trap), actual prices = `actual_lmp_hourly_CAISO.parquet` (DA basis for C3c per
rubric v2).

## 1. The C3c actual DA >$200 tail decomposes into two regimes

2023 (80 h): **winter gas 39 h** (Jan 3-6/13/18/25, morning hod 5-10 + evening
15-23, RT companions also elevated — real fuel-cost pricing at spiked daily
citygate) + **summer/fall evening 41 h** (Jul-Aug hod 17-19 singles, the Aug
15-16 heat event to $1,175, Oct 18-19). 2024 (52 h): **winter storm 28 h**
(Jan 15-16, Winter Storm Heather) + **summer/fall 24 h** (Jul 9-12/23-25,
Aug 2-6, Sep 4-6, all hod 16-19). 2025: zero. The summer singles clear
$200-1175 in DA while RT settles $52-172 in all but the Aug-16-2023 EEA hours:
a DA-expectation premium, not realized scarcity.

## 2. Winter half — the gas-calendar defect (FIXED: caiso-90)

The daily citygate series is a next-day-delivery index placed on TRADE days:

* The keeper's only 2023 tail day is Jan-12 (16 h flat ~$203 — the $24.29
  print's trade day), a day the actual tail does NOT contain; the actual tail
  day Jan-13 is that print's flow day. Jan-17 ($21.82) pairs with the actual
  Jan-18 tail the same way.
* The Fri Jan-12-2024 print ($17.34; HH $13.08 — the national freeze) is the
  MLK-weekend package covering Sat Jan-13 → Tue Jan-16 flow — exactly the
  actual storm-tail days — which trade-dated linear interpolation instead
  decays toward the $5.00 Jan-16 print, pricing the storm days $8-11/MMBtu
  (keeper model prices them $62-104).

`caiso_citygate_flow_date` places prints on trade+1 with a forward-fill
staircase (weekend packages); flag-off byte-identical; monthly means move ≤3 %
except Jan-2024 +14 % (the storm package). **Disclosed source gap:** the EIA
NG Weekly archive skipped its Dec-29-2022 and Jan-5-2023 issues, so trading
days Dec-22-2022..Jan-4-2023 do not exist in the source — the actual
Jan-3..6-2023 cluster (22 h) is unreachable by ANY placement of this series.
Candidate replacement source (own charter): the CAISO OASIS daily gas price
index (the market's own DEB fuel input).

## 3. Summer half — the overlay is honest-inert; adjudicated CLOSED, with evidence

In the 41 summer/fall 2023 tail hours the model clears **$71-98** (2024
tail hours: $52-68) — CC-econ/duct level — with 1.9-4.7 GW thermal-online
+ 0.8-5.0 GW quick-start-offline + 2.4-7.6 GW storage-power headroom left.
The CAISO LOLP overlay (`caiso_scarcity_pricing`, IN the scored prices) adds
$0-37 there: reserves are genuinely fat, so the overlay cannot honestly fire
(caiso-85 already showed corridor import headroom 0 — imports maxed).

* **SOC-aware storage reserve credit: REFUTED, no LP.** The schedule-derived
  conservative form (future-drawdown lower bound on stored energy) fires
  2,328 h >$200 in 2023 (29× the 80 actual) and explodes hourly MAE
  15.4 → 122.9 — every day's discharge-end becomes phantom scarcity. The
  true-SOC form is degeneracy-pinned (the LP's SOC level is not identified at
  the optimum). Any σ/MCL/VOLL re-fit that makes LOLP fire at 6-12 GW
  reserves is rule-11 tail fitting. CLOSED.
* **CT rungs are not the miss** — CT_PEAKER peak (4.0×, ~$210-235 at summer
  gas) is simply never reached because cheaper in-model supply genuinely
  remains (see §4). Storage sizing CHECKED: model Aug-2023 cap 8.0 GW ≈ real
  installed batteries+PS; not the phantom.
* The admissible route to the DA-expectation tail is the **measured offer
  surface**: CAISO publishes masked DAM bid curves (OASIS Public Bids, 90-day
  lag) — the CAISO analogue of the measured ERCOT/PJM/NEISO offer surfaces in
  `data/raw/_validation-source/`. Named-uncharted (intake + derive, own
  session).

## 4. The C1 cluster is the volume symptom of the same evening stack

Keeper grid TWh (model − bench actual): CC_REGULAR +1.81/+5.37/+2.52
(2023/24/25); CT_PEAKER −3.31/−3.65/−2.06 (model runs the class at 16-19 % of
its real energy); CT_CHP −1.80/−1.74/−1.07; ST_GAS −0.88/+0.52/+0.03.

Hour-of-day (2024, CEMS gross vs model):

* **CT_PEAKER**: the real class runs round the clock — 38-121 GWh per hod
  bucket even overnight/midday, January its second-biggest month (0.43 TWh vs
  model 0.028 — the same winter-peak hours as the price tail), evening peak
  0.36-0.39 TWh/hod vs model 0.07 (5× deficit at the peak, 20×+ off-peak).
* **CC_REGULAR**: model over-runs +0.55-0.69 TWh/hod OVERNIGHT (real CC
  cycles down; model holds flat — the RA bridge explains only ~2.3 TWh/yr of
  it) and +0.32-0.86 EVENING (model serves the ramp with CC where reality
  runs CTs). Midday is clean (±0.09).

**Concentration finding:** top-15 plants carry 91 % of actual CT_PEAKER
energy; **Panoche Energy Center (56803, 388 MW LMS100s, NP15) alone is
736/1,425/852 GWh (2023/24/25, CF 22/42/25 %)** vs model 30 GWh — a PG&E
tolling/RA unit that runs block-loaded (median online CF 78.9 %, 10,942
online hours pooled). Its measured HR is 9.35; the model's econ rung for it
(1.10× DEB shape + carbon) lands ~$55 vs an NP15 belly ~$45-50 — a $5-10
marginal-economics miss, not a missing floor. The measured tranche artifact
already carries its committed_pct 19.1.

## 5. Charter directions (owner decision; nothing built this session)

1. **CAISO reserve co-optimization (#1492, deferred with anchors collected):**
   spin/non-spin held on ONLINE units (pergen/ramp10 + online-quality
   scoping), tariff §27.1.2.3.5 ASDCs, BAL-002-WECC-3 ~6 % requirement.
   Withholds CC headroom from evening energy → CTs clear on merit → both C1
   volume sides AND the evening dual move together. The caiso-57-era
   suppressor of the last structural attempt (P2 UC decommit stripping
   LCR/ramp-cleared CT) is ARCHIVED — P1-only scoring changes the arithmetic
   of that whole family. This is the structurally-correct build for the
   shared evening defect (rule 19: one mechanism, two symptoms).
2. **Panoche-class committed-tranche gate (CAISO evidence, per-plant,
   self-targeting):** the G-20 CT_PEAKER exclusion from
   `cc_mustrun_per_plant` rests on PJM (Dominion) overnight-offline evidence;
   Panoche's own multi-year evidence is the opposite (block-loaded when
   online). Any revisit needs its own D-4 window and the rule-17
   driver/window/forward story.
3. **Overnight CC cycling:** the model's flat overnight CC (+0.6 GW) vs the
   real fleet's deeper duck — the ERCOT-63 committed-state lesson applied in
   reverse; likely coupled to (1) via evening commitment carrying into the
   night.
4. **Winter data completion:** OASIS daily gas index intake for the
   Dec-2022..Jan-4-2023 window (and as a general replacement/cross-check for
   the EIA weekly compact table).
