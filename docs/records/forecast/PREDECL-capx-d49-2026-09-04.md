# PRE-DECLARATION — capx D49: the two D46 Phase-0s (ERCOT CCS at carbon = 0; the MISO exit-side margin)

**Lane:** capx D49, a ZERO-SOLVE diagnostic over artifacts D46 committed. Branch
`claude/capx-d49-d46-phase0s-eaw7am`, fresh off `origin/main` `8a18e9e1`.
**Date:** 2026-09-04. **Pushed before either probe script runs** — the grading in
the finding is against this text, misses included.

**What this lane does not do.** No solve, no arming, no `ScenarioConfig` field
touched, no keeper / shard verdict / marker moved, no repair landed. Every number
is read from committed ledgers, dumps and constants by probe scripts committed
with the finding. Rules 13, 14, 21, 22, 25, 27, 28 hold; a half-1 defect is
routed to the director as a candidate repair lane, never fixed here.

**Data profile.** Dispatched at `code`; this container arrived with `data/raw`
fully hydrated (all profiles) and an EMPTY `data/clean`. `regenerate_clean.py`
is running in the background so the ERCOT / PJM / MISO base fleets can be built
through the repo's own `build_base_fleet` for per-unit heat rate, CO2 rate,
EFORd, VOM and vintage. Stated here because the dispatch said to say so: the
widening is to READ unit parameters, not to solve.

---

## 0. Disclosure — what had already been read when this was written

A pre-declaration that hides prior peeks is worse than one that declares them.
Before writing this text I had read, in full or in part: D46 §4.2 / §4.5 / §9,
D41 (all), D43 (all), the D31/D32/D42 findings (via a summary), spec §5.2 / §5.6,
`model/capacity_evolution/ccs.py`, `retirements.py` (the screen, the pipeline
rule, the floor), `config/capacity_market.py` (the MISO curve seam), and the
**committed ledgers themselves** at the following grain:

- the three t1f `run_config.json` files diffed on every screen-relevant field
  (§1.1 below records the result — it is an input to the candidates, so it is
  disclosed rather than "predicted");
- the ERCOT t1f `ccs_retrofits` rows (14 unit ids / MW) and the 2027–2029
  `pipeline_events` rows' zone-price means and gas_cc failing depths;
- the MISO D46 and D42-control `pipeline_events` **event counts per year**,
  the per-fuel medians of the failing rows' net revenue / capacity revenue /
  bar, the ledger `capacity_reserve_position` per year, and the npz dumps'
  zone-mean prices;
- `capacity_price_per_firm_mw_yr` evaluated at those ledger positions.

Nothing below was computed at unit grain yet, no decomposition was run, and
the two probe scripts do not exist yet. The discriminators in §2 are fixed
BEFORE those scripts run; the candidate rankings in §1 are informed by the
disclosed reads and say so where they are.

---

## 1. Half 1 — ERCOT CCS conversions at carbon = 0

### 1.1 Disclosed input: the config diff

Across the three committed t1f bundles (ERCOT `873d8c0e6cab52ae` @ `dd10e9fe`,
PJM `31a19d815fa319a7` @ `54ca19a`, MISO `587dc5b32ba71ceb` @ `54ca19a`) every
field the CCS screen reads is IDENTICAL except:

| field | ERCOT | PJM / MISO |
|---|---|---|
| `ccs_retrofit_capex_kw` | 1521.4 (D41 corrected) | 900.0 (stale, pre-D41) |
| `fixed_om_gas_cc_ccs` | 65.0 (D41 corrected) | 25.0 (stale) |
| `scarcity_price_overlay` | True | False |
| `capacity_screen_scarcity_restoration` | True | False |

`carbon_price` 0.0, `eac_price_gas_cc_ccs` 0.0, `federal_ces_enabled` False,
`co2_transport_storage_cost` 15.0, `ccs_retrofit_vom_adder` 8.0,
`ccs_retrofit_hr_penalty` 0.12, capture 0.9, cap 3 GW/yr, min life 15,
`ira_45q_credit_window_years` 12, `ira_ccus_45q_last_year` 2032 — all three.
Gas basis: ERCOT −0.50, PJM +0.67, MISO +0.30 $/MMBtu on the same `mid` Henry
Hub path (2027 $3.62, 2028 $3.67, 2029 $3.84).

**So the PJM/MISO ledgers' conversions (PJM 45 rows / 8,995 MW, MISO 61 rows /
8,992 MW, 2028–2030, cap-bound every year) were decided at the STALE constants.**
Nobody has solved PJM or MISO at the corrected values; D41 §4.3's "nothing
clears" is an analytic claim on CLASS-AVERAGE hosts (er 0.382 t/MWh, hr 6.3–7.5).
The like-for-like comparison this lane owes is therefore: the identical
per-unit reconstruction, on the CORRECTED constants, on each ISO's own
converting units' MEASURED parameters.

### 1.2 The arithmetic being reconstructed (from `ccs.py`, exact)

Per candidate unit, per screen year, with the prior year's zonal price row `p`:

```
b_unab  = hr·gas + vom                                   (carbon = 0, attr = 0)
b_post  = hr·(1+0.12)·gas + vom + 8 + captured·15 − q45,  captured = 0.9·er,  q45 = 85·captured
Δ       = b_unab − b_post = 63·er − 0.12·hr·gas − 8          ($/MWh, the per-hour uplift CEILING)
uplift_window = Σ_t [max(0, p−b_post) − max(0, p−b_unab)]·avail − ΔFOM,   ΔFOM = 35,000 $/MW-yr
clears  ⇔ uplift_window > 0  AND  payback(capex_learned, uplift_window, uplift_post, 12) < remaining_life
```

Because `uplift_post` (no 45Q) is negative for every host, the two-segment
payback reduces to `capex_learned ≤ 12 × uplift_window`. Learned capex on the
shared tracker: 2028 **1,323.6** $/kW, 2029 **1,200.5**, 2030 **1,132.0** (D41's
path × 1521.4/900). Hence the bar, in $/MW-yr of in-window uplift:
**110,300 (2028) / 100,040 (2029) / 94,330 (2030)**, i.e. Σ-term ≥ 145,300 /
135,040 / 129,330. At the hour ceiling (every hour at Δ): **Δ·avail ≥ 16.6 /
15.4 / 14.8 $/MWh.** With avail ≈ 0.9 and hr 7 at ERCOT's $3.12 gas, that needs
**er ≥ ~0.46 t/MWh** (2028), against the 0.382 class average D41 used.

### 1.3 Candidates, ranked, each with its decision rule

Ranked by what the disclosed reads make likely; the reconstruction decides.

**(c) — construction: the 45Q term is sized on a per-MWh CO2 rate that is not
the host's electric-side physics.** ERCOT's plant-binned tranches carry the
plant's MEASURED CAMPD CO2 rate per net MWh; for a CHP host (three of the 14
converting rows are `CC_CHP_Houston_*`) the CEMS rate per net ELECTRIC MWh
includes the steam-side fuel, and for an old / duct-fired CC it can exceed
0.46. The screen then credits 45Q on captured tonnes per electric MWh while
charging capex per electric kW — the capture island the credit is paid on is
larger than the one the capex buys. *Decision rule:* the converting units'
`emission_rate_co2` (a) exceeds the class physical rate `hr_physical × 0.0531`
by > 15 % for ≥ half the converting MW, AND (b) re-running the reconstruction
with `er := hr_physical × 0.0531` (or the plant's own `hr × 0.0531` for the
tranche) drops those units below the bar. If (a) holds but (b) does not, the
rate is not what clears them and (c) is refuted for this reading.

**(c′) — construction: the tranche's `heat_rate` is an offer-curve construct
(`hr_peak = base_hr × HR_Mult_peak`), so `b_unab` is a marked-up bid, widening
the band `b_post ≤ p < b_unab` the post-retrofit unit earns in.** Two `_peak`
tranches convert (117.6 MW). *Decision rule:* a converting `_peak` or
`_committed` tranche whose per-hour uplift comes ≥ 50 % from that band, and
which falls below the bar when `b_unab` is priced at the plant's base hr.
Only material if such tranches are a material share of the converting MW.

**(a) — economics: the ERCOT hosts' measured (er, hr, avail) make Δ·avail·H
clear the corrected bar on their own physics, and PJM/MISO hosts with the same
measured parameters would clear too.** *Decision rule:* the converting units'
Δ·avail ≥ the 2028 ceiling requirement on their PHYSICAL rates (i.e. (c) fails
its rule (b)), AND the PJM/MISO converting units evaluated identically on the
corrected constants show H* ≤ 8760 for a non-trivial share. Under (a) the
finding's verdict is that **D41 §4.3 was a class-average artifact** — the
zero-clearing claim does not survive per-unit measured rates in PJM/MISO
either — and the D46 "does not extend past PJM/MISO" reading is bounded the
other way.

**(b) — an ERCOT-specific screen path.** The disclosed config diff leaves only
`scarcity_price_overlay` / `capacity_screen_scarcity_restoration` (the price
signal's ORDC tail). Δ is a per-hour CEILING, so a tail cannot raise the uplift
in hours where both states clear; it can only add hours to the band. *Decision
rule:* (b) holds only if the ERCOT units clear on the ERCOT stand-in surface
AND fail at the hour ceiling H = 8760 on a tail-free surface — which is
arithmetically impossible (the ceiling is the max), so (b) is expected to be
REFUTED unless a term I have not found (`attr`, cap, eligibility) differs.
Ranked last.

### 1.4 The price surface, stated before use

No forecast bundle commits hourly prices (D30 §8 / D41 §7 item 5). The ERCOT
t1f 2027 zone-mean prices ARE in the ledger's 2027 `pipeline_events` rows
(`screen_price_mean` $35.3 North … $41.4 Houston 2028-row). For the duration
SHAPE the probe uses the committed ERCOT T1-H D46 dump
`screen_signal_diag_2024_for_2025.npz` `econ_prices_usd_mwh` (the forecast
machinery's own ERCOT LP duals + overlay, 7 zones, 265 h ≥ $100) re-levelled
to the ledger's 2027 zone means as a **stand-in**, and reports every unit at
THREE points: (i) the hour ceiling (Δ·avail·8760 − ΔFOM, the exact upper
bound), (ii) the stand-in surface, (iii) the D41 class-average construction.
A unit that fails (i) cannot have converted on this arithmetic — that would be
a defect by itself. Verdicts are drawn on (i) and on which TERM moves (i)
across the bar; (ii) is corroboration only.

### 1.5 Predictions, graded in the finding

| # | prediction | conf |
|---|---|---|
| P1 | No config term other than the D41 pair and the two ERCOT scarcity flags differs across the three bundles' screen inputs (disclosed; graded as a check that the diff is exhaustive over the screen's reads). | — |
| P2 | ≥ 10 of the 14 converting ERCOT rows carry `emission_rate_co2` ≥ 0.46 t/MWh; the converting MW's capacity-weighted er ≥ 0.50. | MED |
| P3 | At the hour ceiling every one of the 14 clears (else defect). | HIGH |
| P4 | With er replaced by the physical `hr × 0.0531`, ≥ 8 of 14 fall below the 2028 ceiling bar → verdict (c) with the seam named as the CO2-rate-per-electric-MWh ↔ capex-per-electric-kW mismatch, NOT (a). | MED |
| P5 | PJM and MISO's own converting units, on the corrected constants and their measured rates, are NOT all below the ceiling bar: ≥ 20 % of PJM's converting MW and ≥ 20 % of MISO's carry er ≥ 0.46 and would clear at the ceiling. I.e. D41 §4.3's "nothing clears" does not survive unit grain in PJM/MISO either. | MED |
| P6 | The `_peak` tranches' clearing is (c′)-driven (marked-up `b_unab`); immaterial in MW (117.6 of 2,741.8). | LOW |
| P7 | Physical-plausibility line: no merchant gas-CC CCS retrofit has cleared on 45Q alone in any US market; if (c) holds the model's 2.7 GW is a construction artifact and the line is satisfied by the seam, not by a band. If (a) holds instead, the finding must say the model claims something the market has not done, and route it. | — |

Falsifier for the whole half: if the reconstruction on the committed
constants does NOT reproduce the 14-row / 3-row 2028/2029 pattern at the hour
ceiling (a converting unit that cannot clear even at 8760 h), the arithmetic
in §1.2 is not the screen's and the finding says so before drawing any verdict.

---

## 2. Half 2 — the MISO exit-side margin

### 2.1 Disclosed inputs (the census already read)

From the D46 MISO ledgers (`eff2c890746ec966`), `pipeline_events` per screen
year: 2022 (bridge) **1,497 `entry_capped`, 0 decided**; 2023 **948
`entry_capped`, 0 decided**; 2024 **none**; 2025 **none**. Every failing row in
2022/2023 carries `capacity_revenue_usd = 0.0`; the failing rows' median net
revenue is 0 $/kW-yr against bars of 21–58.5. Ledger
`capacity_reserve_position` (the position the screens CONSUMED, per the
runner's D45 note): 2023 **1.032186**, 2024 **0.976427**, 2025 **0.948813**.
`capacity_price_per_firm_mw_yr` at those positions on the year's vintage:
2023 **$0** (2021–24 vintages are the vertical PRA step, zero when long), 2024
**$123.5/kW-yr** (vertical step, gross-CONE anchor, position < 1), 2025
**$498.2/kW-yr** (RBDC cap plateau at 0.949). The D42-control (dates OFF)
2024 screen: 1,236 failing rows, capacity revenue 0 for all, position > 1.

The retirement screen at MISO consumes `price_signal` = the lookahead
stack signal (`entry_lookahead_reprice=True`; zone-flat time-mean MC step —
the failing rows' `screen_price_max` is one value across all zones), NOT the
LP's zonal duals. So "the LP's own realized price dispersion discarded" is
literal for this screen.

### 2.2 The two hypotheses, and a third the census forces me to name

- **H-WALL** — the undated cohort's screen margins cluster within a band of
  the bar narrower than the dispersion the D43 construction would carry, so
  priced dispersion would push a tail below it.
- **H-BAR** — the cohort sits far above the bar and the miss is the bar or
  the capacity-revenue term.
- **H-FLOOR** (named now because the disclosed census shows it and hiding it
  would be dishonest) — in the years the cohort FAILS the bar, exits are
  blocked by the admission floor, so the margin side is not what decides;
  the D43 construction is inert there whatever the band.

### 2.3 Numeric discriminators, fixed in advance

Per screen year y ∈ {2022, 2023, 2024, 2025}, over the UNDATED thermal cohort
(every screened unit not exempt via `dated_plant_unit_ids`; the dated set is
the ledger's `announced_fossil_schedule` plants), per unit:
`gap = net_revenue − going_forward_cost` in $/kW-yr, from the ledger rows
where the unit failed; reconstructed for units the ledger does not carry
(2024/2025, where nothing fails) as `energy_leg + capacity_term`, with the
energy leg taken from the same unit's D42-control 2024 row (same price
object, stated approximation) and the capacity term from
`capacity_revenue_per_mw_yr` at the ledger position on the year's vintage.

**Dispersion band** (the D43 construction mirrored onto exits): for each
unit, `band = energy_leg(duals) − energy_leg(stack signal)`, both on the same
year's npz (`econ_prices_usd_mwh` vs `price_base + adder`) at the unit's
`mc_mean` and `availability_mean` from its ledger row. The band is the
largest move a dispersion-carrying expectation could make in the unit's
energy leg — D43 §1(d): the realized duals are the ceiling.

- **H-WALL holds** iff, in a year where the cohort has failing members,
  ≥ 30 % of the undated cohort's MW that ACTUALLY EXITED (the published
  record) sits with `|gap| ≤ |band|` — i.e. would cross the bar under the
  construction. Sign check: a unit below the bar can only be pushed further
  below by a band that is negative (duals leg < stack leg); the construction
  cannot rescue the direction rule 14 requires.
- **H-BAR holds** iff, in the years no unit fails, ≥ 70 % of the undated
  cohort's MW sits > |band| above the bar AND the capacity term alone exceeds
  the bar for ≥ 70 % of that MW.
- **H-FLOOR holds** iff, in the years units fail, ≥ 70 % of the undated
  cohort's actually-exited MW fails the bar AND is `entry_capped`.

Decomposition against the −43.6 % (7.570 GW) miss: split the actual 17.369 GW
into (i) exits the dates channel produced (the ledger's announced +
announced-derate MW matched to the record), (ii) dated-but-deferred /
Dec-rolled MW the screen cannot reach (exempt), (iii) the UNDATED cohort's
actual exits — the only MW a margin-side object can recover. (iii) is then
split by year into H-FLOOR / H-BAR / H-WALL MW using the rules above, and
each is stated as a fraction of 7.570 GW.

### 2.4 Predictions

| # | prediction | conf |
|---|---|---|
| Q1 | H-WALL accounts for < 5 % of the 7.570 GW. The MISO stack signal and the run's own duals differ by < $5/MWh in mean and the duals carry ≤ 5 h ≥ $100 (2023: 0; 2024: 4 VOLL hours), so |band| < $8/kW-yr for ≥ 90 % of cohort MW, against gaps of −20 to −58 (2022/23) or +65 to +500 (2024/25). | HIGH |
| Q2 | H-FLOOR is the 2022/2023 reading: ≥ 70 % of the undated actually-exited MW present in the fleet fails the bar and is entry-capped in BOTH 2022 and 2023. | HIGH |
| Q3 | H-BAR is the 2024/2025 reading: the capacity term alone ($123.5 × (1−EFORd) in 2024; $498 × (1−EFORd) in 2025) exceeds every bar for ≥ 95 % of the cohort MW, so no undated unit can fail whatever its energy leg. | HIGH |
| Q4 | The margin-side object is the POSITION, not the curve: the model's consumed positions (0.976 / 0.949) sit 5–9 pts SHORT of the market's own (PY24/25 offered ÷ PRMR 1.034; PY25/26 cleared 1.0174), where D31 had closed the gap to < 1 pt at dates-OFF (1.0321 / 1.0571). The dates channel removes ~8–10 GW of dated capacity that the 0.8546 internal-supply accounting ratio (D31 leg 1, identified against the PRA on a census fleet that still carried those units) was already absorbing — the same exits netted twice. | MED |
| Q5 | The decomposition: the undated cohort's actual exits (iii) are ≈ 3.5–4.5 GW of the 7.570 GW miss; the rest is exempt MW (deferred / Dec-roll). Of (iii), H-FLOOR ≥ 70 %, H-BAR the complement (units that were still in the fleet in 2024/25), H-WALL ≈ 0. | MED |
| Q6 | Rule-14 sign line: a faithful position (re-identified ratio on the post-dates fleet) moves the 2024 capacity term back toward $0 and the cohort back BELOW the bar — exits get HARDER only in 2025 (RBDC at ~1.0 pays ~$110/kW-yr vs the market's $79), and in 2024 the screen returns to the floor-capped regime. Nothing is sized by the residual. | — |

Falsifiers: Q1 fails if any year shows ≥ 30 % of exited cohort MW within
band; Q3 fails if any undated unit fails in 2024/2025 (the ledger says none
does, so the reconstruction must reproduce that or be wrong); Q4 fails if the
consumed positions reproduce the market's own within 2 pts.

### 2.5 Routing, pre-committed

- If H-WALL: route to the D43 wall's record (D39 §3.2 / D43 §8.3), no lane.
- If H-FLOOR + H-BAR with Q4 confirmed: a named margin-side object — the
  screen's consumed reserve position under the dates posture — with its
  identified repair (re-identify `ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"]`
  on the model fleet in the SAME posture the run applies, i.e. net of the
  dated exits, against the same PRA offered totals; zero DOF, published
  source `data/raw/miso-pra/`) and its source (D31 §2's identification fleet).
  Routed as a candidate repair lane, not fixed here.

---

## 3. What this lane will commit

`scripts/probes/_capxd49_ercot_ccs_reconstruction.py`,
`scripts/probes/_capxd49_miso_exit_margin.py`, their JSON outputs under
`results/calibration/`, `docs/handoffs/FINDING-capx-d49-2026-09-04.md`, and
evidence-citation appends to the ERCOT `ccs_retrofit_screen` cell and the
MISO retirement cells in the matrix shards (no verdict letter moves).
