# ERCOT May-2024 scarcity — outage-vs-heat collision forensics (C3c-2024 depth/breadth thread)

**Session 2026-07-10 (ercot56 forensics). Keeper under test: `2026-07-10-ercot55-surface-ab`
(CALIBRATED-WITH-CAVEATS, rubric v2.4). Ledgered caveat under investigation: C3c-2024 —
27 model tail hours vs 68 DA actual (0.40×, gate ≥34 h = 0.5×). Owner hypothesis: the May-2024
highs were planned spring-maintenance outages colliding with unseasonable May-8-onward heat, and
the model's outage inputs understate the real May outage MW (a measured-input defect), so the
model has too much available capacity in exactly those hours and cannot form depth/breadth.**

**Verdict in one line: the outage inputs are FAITHFUL where it matters — the collision is in the
model at the right aggregate MW on the deep day (net −0.3 GW vs CEMS at the May-8 event hours)
and on the May-27 record-peak day (+0.1 GW vs DAM) — the C3c-2024 depth/breadth caveat stays the
already-filed G-22 offer-formation residual (a 2024 window-grain probe of the ONE real input
imprecision found, the nuclear refuel monthly smear, moves the tail 27 → 27 exactly); but that
nuclear imprecision is a genuine cross-month measured-input defect whose correction is a broad
structural improvement (final ercot56 bundle: May-8 depth $1,405 → $1,907 vs measured
$2,368–2,420; Nov-2024 −14.1 % → −3.9 %; Jan sign-flips +4.9 → −5.1 %; C3a-2024 −4.7 → −4.5 %;
C3b-2024 0.196 → 0.183), so it is fixed as measured data (rule 15) and re-solved as the
full-span ercot56 bundle — scores in the ERCOT-56 calibration-log entry.**

## 1. May-2024 reconstruction (all measured)

Keeper May-2024 monthly: model $28.78/MWh (lw, scorer basis) vs actual rt_lw $44.09 → **−34.7 %**,
the worst 2024 month (next: Mar −16.9 %). Surface arm barely moved May (ercot53: $28.62, −35.1 %).

Hourly decomposition (keeper payload `lmpDeltaHr` + zonal archive, HB_BUSAVG):

| May day | DA>200 h (max) | RT>200 h (max) | SCED λ max | model max (h>200) | PRC min | RTORPA max | model avail-excess GW* |
|---|---|---|---|---|---|---|---|
| 2 | 2 ($500) | 0 ($58) | $62 | $35 (0) | 6,451 | $0 | +2.3 |
| 8 | 6 ($2,221) | 5 ($3,049) | $2,420 | $1,405 (2) | 4,778 | $179 | +1.6 |
| 9 | 0 | 1 ($224) | $394 | $37 (0) | 6,450 | $0 | −0.2 |
| 13 | 2 ($372) | 0 ($179) | $180 | $33 (0) | 5,983 | $0 | +3.5 |
| 14 | 1 ($500) | 0 ($86) | $87 | $34 (0) | 6,237 | $1 | +2.3 |
| 17 | 3 ($688) | 0 ($101) | $100 | $34 (0) | 5,635 | $3 | +0.3 |
| 21 | 0 | 1 ($275) | $273 | $52 (0) | 5,634 | $0 | −0.1 |
| 24 | 4 ($654) | 0 ($88) | $104 | $50 (0) | 6,092 | $1 | −0.4 |
| 26 | 3 ($1,518) | 0 ($101) | $109 | $491 (1) | 6,215 | $2 | −0.4 |
| 27 | 1 ($266) | 0 ($131) | $204 | $46 (0) | 6,283 | $0 | −0.1 |

\* matched-basis day-structure deviation, §3.

May 8 alone carries ~71 % of the May equal-hour price gap (model day-mean $123 vs $346).
May 27 (Memorial Day): measured peak 77.13 GW (NP6-346); model demand input peaks 76.4 GW same
day/hour — captured. Demand hygiene: zero NaN/interpolated windows anywhere in 2024 (the
Dec-2025-style 48-h hole does not recur); HSL wind/solar file clean, no flat runs; the apparent
evening demand offset vs NP6-346 is the DST labeling convention (model standard-time clock),
shape matches within 0.2–0.3 GW at correct alignment.

2024 DA-tail composition (68 h): Jan 20, May 22, Aug 10, Apr 8, Oct 4, Mar 2, Jun 1. The model's
27 h sit ON the right days (Jan 15–16, Mar 4, Apr 16/28, May 7–8, Aug 18–21, Nov 10–11) — timing
is right, breadth-within-event and the DA-only shoulder days are what's missing.

## 2. Outage forensics — the core ask (model derate vs reality, May 2024)

Model side reproduced exactly (fleet captured at the P0 seam with the keeper config): historic
overlays = facility masks (coal/CC, CF<5 % ≥48 h) + unit-level derate (≥5-day windows,
`campd-unit-outages.csv`, CTs excluded) + partial-outage plateaus; windows are exact-dated, NOT
monthly-smeared. 2024: 516 tranches zeroed / 674 derated / 191 partial.

**Daily out-MW, model outage layers vs DAM-disclosure OUT status (60d Gen_Resource, config-
collapsed to physical trains, thermal+nuclear):** tracks reality's spring return-to-service ramp
(≈23 GW out May 2 → ≈12 GW May 27) within ±3.5 GW everywhere:

- May 8 (deep day): actual DAM-out 18.2 GW vs model 16.9 — and at the RT event hours (HE17-20)
  the CEMS test (at $3,049 nothing available idles) gives **16.66 GW off vs model 16.94 out —
  net −0.28 GW: the model was marginally MORE derated than reality**. Per-plant errors exist but
  CANCEL: misses (Stryker Creek 515, Mountain Creek 694, Graham 251, Ray Olinger 147 — all
  `ST_GAS_PEAKER_PLANTS` detector exclusions; Remy Jade 350 + Permian Basin 178 + Greens Bayou
  121 — CT-class exclusions; Handley-5 window starts 5/09 vs real out 5/08) vs over-derates
  (Sam Seymour 615 returned midday May 8 [DAM had it OUT — DA-basis faithful]; Tenaska Gateway
  631 net; Sandy Creek 482 partial-window overhang [CEMS shows it running]; Wolf Hollow II one
  train 364; Martin Lake 254 capacity basis).
- May 27 (77 GW peak): actual DAM-out 11.7 GW vs model 11.6 — dead even.
- Shoulder days May 4-6 / 10-16 / 31: model +2.0 to +3.5 GW under-derated (DAM basis) — the one
  half-month where the input is systematically fat (composition: nuclear smear ~1.3 GW §2.1 +
  CT/steamer exclusions + window edges).

Matched-basis day-structure (captured total availability incl. WEFOR/statistical layers vs
DAM-available, each normalized to its own healthy-fleet May-21-31 anchor): model runs **+1.5 to
+4.1 GW excess-available May 2-16** (worst May 6 +4.1, May 4 +3.6, May 13 +3.5), ≈0 May 21-30.

### 2.1 The one real event-grain input defect: nuclear refuels are monthly-smeared

`NUCLEAR_MONTHLY_CF_BY_YEAR` (measured EIA-923 fleet monthly CF — May 2024 = 0.78) applies
uniformly to all 4 reactors and all hours of the month. Reality (DAM disclosure NUC status,
hour-resolved; cross-checked against the reserves series):

- **STP-2 (1,280 MW): OUT 2024-03-23 → 2024-05-19** — spans the Apr-16, Apr-28 AND May-8 events;
- **Comanche Peak 1 (1,205 MW): OUT 2024-05-11 → 2024-05-16** (+partial edges 5/10, 5/17) — spans
  the May-13/14/16 DA-shoulder days (both reactors out simultaneously);
- STP-1: Oct 5 → Nov 7; CP-2: Oct 21 → Nov 17 (+short spring blips).

The 0.78 smear = the correct monthly ENERGY, mis-timed within the month: vs window-truth the
model is +1.28 GW too available on May 1-9 relative to its healthy-fleet level (incl. May 8),
+1.3–2.5 GW too available May 10-17, and −1.10 GW too TIGHT May 20-31 (all four units back;
includes the May-24/26/27 DA-shoulder days, where the model was already under-pricing). The
2023/2025 exposure is negligible for gates: 288 of 2023's 310 DA-tail hours are Jun-Sep (nukes
~full), 2025's 24 h are scattered/summer.

## 3. Attribution per event-day

- **(a) availability**: May 8 net ≈ 0 (−0.3 GW CEMS-basis; +1.28 GW window-basis nuclear only
  — see probe); May 13/14/16 +2.3–3.5 GW (nuclear + CT/steamer exclusions); May 24/26/27
  ≈ −0.1–0.4 GW (model slightly tight, nuclear −1.1 GW inside that); May 27 peak day even.
- **(b) demand/renewables input**: clean. May-27 peak captured (76.4 vs 77.1 GW, −0.9 %); wind
  6.4 GW / solar collapsing 4.1→0.2 GW into the May-8 peak — measured drivers faithful.
- **(c) offer formation (the filed G-22 residual)**: owns the rest — and reality's own reserve
  pricing proves it: on EVERY DA-shoulder day (May 2/13/14/17/24/26/27, 16 of May's 22 DA
  hours) **measured RTORPA ≤ $3 and RT settled ≤ $180** while DA cleared $266–1,518 — the real
  market formed those prices in the day-ahead through offers/risk premia at reserve levels the
  ORDC (real and modeled) prices near zero. No availability correction can reproduce them in an
  RT-physics LP; they are DA-boundary expectation formation (G-22 §5 / the Nov-17 family, of
  which May 9 midday — λ $394, PRC 7,011, RTORPA $0, model $37 — is another member).
  On May 8 itself the ORDC adder was only $179 of the $2,420 λ: the depth came from the energy
  OFFER wall (measured surface rungs $1,392–2,444 exist in the keeper; the LP cleared at
  $1,366-1,405 = one rung shy, so depth IS availability-elastic at the margin — probe below).

## 4. Rule-16 throwaway probe: window-grain nuclear (ercot56_diag_nucwin_2024)

Keeper config (surface arm), 2024 only, with the four reactors' availability (and their flat
must-run floors) replaced by the DAM-disclosure daily availability series (partial jack-bus days
carried; Feb-29 dropped). Never registered. Local keeper-reference 2024 solve first reproduced
the CI keeper EXACTLY (May lw $28.78, tail 27 h, annual −4.7 % — the ercot54 local-parity
precedent holds).

Result vs the keeper reference (2024):

- **C3c tail: 27 → 27 h — the gate does not move.** The missing 41 DA hours are not reachable
  through availability, exactly as the RTORPA≈$0 evidence predicted.
- **May 8 depth: HE18/19 $925/$1,405 → $1,362/$1,907** (measured λ $2,420/$2,368) — the clearing
  moves one rung deeper into the measured offer wall at the true reserve level; depth IS
  availability-elastic at the margin, and the window-grain input closes roughly half the
  remaining depth gap on the deep day.
- **Nov 2024: −14.1 % → −4.5 %** (the fall refuels — STP-1 out Oct 5–Nov 7, CP-2 Oct 21–Nov 17 —
  were smeared at 0.75 across November; window-grain concentrates them correctly around the
  Nov-10 event). **Jan: +4.9 % → −5.0 %** (sign flip, same magnitude: full nuclear restored
  during the Jan-15/16 winter event, the smear had phantom-derated it). **May: −34.7 % → −33.3 %**
  (May-8 depth gain partly offset by late-May loosening as all four units correctly return).
  **Aug: +25.2 % → +27.8 %** (the one worsening month). **Annual C3a −4.7 % → −4.2 %; C3b NRMSE
  0.196 → 0.191.**
- The keeper's spurious May-26 $491 hour — model-tight on a day reality had all reactors back —
  collapses to $51: it was a smear artifact, not structure.

## 5. Disposition

1. **Owner hypothesis (outage-input understatement drives the May-2024 depth/breadth miss):
   REFUTED in its load-bearing form.** The thermal outage overlay reproduces the real
   maintenance-collision MW day-by-day (±3.5 GW everywhere, net −0.3 GW at the May-8 event hours,
   +0.1 GW on May 27); demand and renewables inputs are clean; and reality's own reserve pricing
   (RTORPA ≤ $3 on every DA-shoulder day, $179 of the $2,420 on May 8) shows the missing prices
   were formed by offers/DA expectations, not by reserve physics a tighter fleet would replicate.
   The C3c-2024 caveat REMAINS LEDGERED as the G-22 offer-formation residual (rules 1/13: no
   retune; ORDC tariff params frozen, rule 26; envelope family exhausted at ercot41/43).
2. **The nuclear refuel monthly smear IS a confirmed measured-input imprecision** (rule 15:
   window-grain measured data exists and is more accurate), fixed as measured data:
   ``scripts/data/derive_ercot_nuclear_availability.py`` → ``data/raw/ercot-nuclear-availability.csv``
   (60-Day DAM disclosure NUC status daily series, 2023–2025: event days [raw < 0.90 — windows,
   trips, ramps, deep derates] kept exactly as measured and cross-validated against the EIA-930
   nuclear hourly; the ≥0.90 pool anchored per month to the existing EIA-923 energy, on-anchor to
   <0.01 % except two winter months where the anchor's own 1.0-cap binds ≤1.2 %), applied under
   ``ScenarioConfig.ercot_nuclear_unit_availability`` (default off; ERCOT backcast overlay;
   uncovered dates — Oct-2023 hole, Nov–Dec 2025 — keep the smear). Zero fitted parameters.
3. **ercot56 full-span bundle** (keeper recipe + the flag, 2023–2025 one bundle, rule 16) +
   zero-forcing ablation twin (rule 20) solved and registered; keeper promotion is the owner's
   call (keeper stays ercot55-surface-ab meanwhile). Registered scores in the ERCOT-56
   calibration-log entry.
4. **Residual availability-input lanes documented, not actioned** (mixed-sign, sub-gate):
   the `ST_GAS_PEAKER_PLANTS` detector exclusion (Stryker/Mountain Creek/Graham/Olinger idle-vs-out
   ambiguity — a deliberate, documented design choice; disclosure OUT-status could replace the CF
   inference for these plants as a future measured intake), CT-class maintenance windows (excluded
   by design), and window-edge precision (Handley-5 late start, Sam-Seymour DAM-vs-RT return,
   Tenaska-Gateway/Sandy-Creek over-derates). At the May-8 event hours these NET to ≈ −0.3 GW
   (slightly over-derated), so none of them is the depth/breadth answer either.
