# FINDING miso-208 — the 8–11 GW is NOT peaking supply the model ran and the market did not: MISO's real summer-2025 afternoons ran the model's CT fleet to 0.02 GW, 3 GW LESS coal and 8 GW MORE gas, and cleared $44 higher; the model's surplus is ~5 GW of coal-side availability the published unplanned record puts at 7 GW — and the record is infeasible against MISO's own metered output on 24 of the 52 shoulder days, so feasibility-clipped it reaches 18 % of the shoulder and 0.5 % of the tail (2026-09-04)

**Keeper unchanged: `2026-09-03-miso-202-unitclip`.** NO LP, NO KEEPER MOVE, NO
MECHANISM ARMED, NO FIELD, NO RUN REGISTERED, NO CELL VERDICT MOVED. PREREG
`PREREG-miso208-find-the-supply-2026-09-04.md` pushed blind at `6a50d0fc`;
record `_miso208_find_the_supply.json`; instrument
`scripts/probes/_miso208_find_the_supply.py`. Second deliverable: miso-203's
G-D block repaired (`scripts/probes/_miso208_repair_miso203_gd.py`, §7).
Rule 22: 2023–2025 only.

---

## 0. Three things found before any candidate was measured

1. **The miso-207 FINDING and log entry never reached `main`** (PR #4678
   carried the JSON + probe + PREREG only; the branch was deleted). This
   session's log entry carries miso-207's record numbers so the lane has them.
2. **The model clock is CST hour-beginning, and every EST-labelled MISO file
   is one hour ahead of it.** Two independent witnesses at r = 1.000 on the
   winning shift: the keeper's own demand vs EIA-930 D (winner +2 under
   `period` → EST, i.e. `period` is an hour-ENDING UTC label and the model is
   UTC−6), and the published INDIANA.HUB LMP file (HE, EST) vs the committed
   zonal `rt` (winner +1). **Consequence, named not repaired:**
   `maxgen_events.MODEL_TZ_BY_ISO["MISO"] = "Etc/GMT+5"` places the declared
   windows on EST, so both armed keeper mechanisms that key on them —
   `maxgen_emergency_tier_pricing` **K** and `unit_outage_maxgen_events` **K**
   (the M-2 deriver "shares the clock convention" by design) — apply their
   windows **one hour late** on the model clock. A solve-affecting repair with
   its own A/B; not this session's.
3. **The keeper's armed outage envelope at HEAD is 35.36 GW annual-mean, not
   miso-195's 36.82** (N-5 miss of 1.46 GW, outside the ±0.15 pre-condition),
   on a 108.7 GW population vs miso-195's 115.3 — the miso-196…202 outage
   repairs (routing, steam basis, per-unit clip) and this instrument's DISPATCH
   fleet (`build_year`, post cc-steam-part reconciliation) vs miso-195's raw
   `load_fleet_from_csv` fleet. `P_U` reproduces to 0.005 GW. Item 1 is
   reported on the CURRENT keeper's envelope; on miso-195's deeper envelope
   every deficit below would read ~1.5 GW smaller. Direction unchanged.

Reproduction: N-1 exact (2025 thresholds 373.02, 15 / 351 h, 52 days; shoulder
gap −43.727, tail −636.862; cushion within $20 10.85 / 3.18 GW — identical to
`_miso207_bound_the_shoulder.json` to the decimal, same code path).

---

## 1. The map (item 0): the market ran the model's peakers, less of its coal, more of its gas

Two measured bases, both on the model clock, 2025, mean GW, **model − actual**.
EIA-930 by fuel (its fuel rows sum EXACTLY to the 930 net-generation total in
every population — no unattributed category; the 930 supply side exceeds 930
demand by ~2 GW, the file's own imbalance) and CAMPD unit-hourly, plants →
model group by the WP-3 construction (matched nameplate: coal 42.2 of 42.8 GW,
98.5 %; CC 24.9 / 27.4; CT_PEAKER 18.3 / 22.3, 82 %; ST_GAS 9.8 / 11.0;
CC_CHP over-matched 1.6×, its row unreliable). **CAMPD caveat:** only 239 of
474 plants carry a parasitic factor, so roughly half the matched output is
GROSS — coal/steam rows read ~3–7 % high, CT rows ~1–2 %.

| row | SHOULDER actual / model / Δ | TAIL actual / model / Δ | other Jun–Jul daytime Δ |
|---|---|---|---|
| **coal (930)** | 28.60 / 32.02 / **+3.43** | 30.17 / 31.92 / **+1.75** | +3.13 |
| coal (CAMPD, part-gross) | 32.36 / 32.02 / −0.34 | 34.44 / 31.92 / −2.52 | −0.32 |
| **gas, all (930)** | 42.60 / 34.79 / **−7.81** | 51.01 / 42.61 / **−8.40** | (2023 −7.3, 2024 −6.7) |
| — CC_REGULAR (CAMPD) | 20.97 / 20.06 / −0.91 | 21.20 / 20.38 / −0.82 | −0.60 |
| — **CT_PEAKER (CAMPD)** | **7.62 / 7.64 / +0.02** | **12.85 / 13.25 / +0.40** | +0.65 |
| — ST_GAS (CAMPD) | 5.30 / 3.26 / −2.04 | 6.59 / 5.02 / −1.58 | −1.82 |
| — CT_CHP / ST_CHP (CAMPD) | −0.36 / +0.32 | −0.34 / +0.40 | −0.30 / +0.27 |
| — CC_CHP (over-matched) | 4.74 / 2.81 / −1.93 | 4.86 / 2.84 / −2.02 | −1.92 |
| nuclear / hydro / solar (930) | −0.09 / +0.03 / 0.00 | −0.01 / −0.58 / 0.00 | |
| wind (930; the miso-206 gross-up) | +0.33 | +0.25 | +0.40 |
| other (930) | +0.50 | +0.07 | +0.70 |
| import (930 −TI) | +0.61 | **+2.17** | −0.45 |
| storage: li-ion / pumped vs 930 BAT | 0.21 / 0.96 vs 0.05 | 0.62 / 2.09 vs 0.26 | |

**The real CT fleet's online share in the shoulder is 0.417 of matched
nameplate; the model's CT dispatch is 0.4165 of its capability** (tail 0.704
vs 0.745). The CT cushion the charter aimed at is the same fleet in the same
state. Where the model and the market differ is upstream of the peakers: the
model runs its coal at **97.7 % of its own availability-derated capability**
(32.0 of 32.8 GW) while the real coal fleet delivered 28.6 GW (930) — the
model has ~3 GW of coal running that the market did not — and the market ran
**7.8 GW more gas**, almost none of it CT_PEAKER or CC_REGULAR: ST_GAS −2.0
(all three years: −0.03 / −1.56 / −2.04), the CHP rows, and ~3 GW of small gas
outside CAMPD's ≥25 MW coverage. The model's coal displaces reality's gas
steam. Imports carry +0.6 (shoulder) / +2.2 GW (tail; the closed seam lane's
object, miso-181/182); wind carries the flat +0.3 GW gross-up; the storage row
is a false positive (Ludington's pumped-storage discharge against a 930 `BAT`
series that carries batteries only).

**The model-excess supply, Σ_rows max(0, model − actual), re-priced up the
keeper's own idle census:** 930 basis **5.50 GW shoulder → lift $16.9, share
0.387**; **4.34 GW tail → $89, share 0.140**. CAMPD-refined basis 3.03 / 3.03
GW → 0.132 / 0.086. Under the line in the tail on both bases; the shoulder
reaches on the 930 basis only. Signs held in 2024 (coal +2.3, gas −6.7) and
2023 (coal +2.1, gas −7.3) at the same magnitude — this is a chronic
coal-for-gas substitution, not a 2025 scarcity signature (miso-197's
out-of-merit steam allocation defect, seen from the coal side).

**What this settles.** H1 ("8–11 GW of the model's capability idle within
$20") reproduces as a statement about the model's COST basis and FAILS as a
quantity claim about the peaking stack: reality had the same idle CT MW (58 %
of a fleet whose online share the model matches to 0.05 pp) and did not clear
them at $47–67. The model's actual surplus is **5.5 / 4.3 GW, on the coal
side plus imports**, half the charter's number and in a different place.
Whether reality's idle CTs were unavailable or offered above cost, item 0
cannot say; item 1 bounds the first.

---

## 2. Item 1 — the published unplanned-outage record on the shoulder days

MISO MOM `OUTAGE`, Derated + Forced + Unplanned, vs the keeper's armed
envelope M (108.7 GW thermal population), 2025:

| population | days | M armed | P_U | **deficit P_U − M** | binding hours | Central share | W6 violation days |
|---|---:|---:|---:|---:|---:|---:|---:|
| SHOULDER | 52 | 25.60 GW | 32.57 | **+7.05 GW** (p50 6.97) | 96.6 % | 53 % | **24 / 52** (19 cap-caused) |
| TAIL | 7 | 27.08 | 33.87 | **+6.79** | 100 % | 53 % | 6 / 7 |
| other Jun–Jul daytime | 56 | 28.28 | 32.88 | +4.99 | 80 % | 53 % | 20 / 56 |

W4 in the shoulder: leg A (deficit > total idle thermal, median 16.4 GW)
converts **8.0 %** of hours; leg B′ (deficit > idle within $20, median 10.8 GW)
**27.4 %**. In the tail 60 % / 93 %. **Re-priced up the keeper's own stack the
deficit lifts the shoulder by $48.6 mean (p50 $9.3, p90 $155) — share 1.11 —
and the tail by $185 — share 0.29.** The only candidate that reaches 0.25 in
BOTH populations, and the shoulder number is ABOVE the gap: in the ~27 % of
shoulder hours where 7 GW exhausts the within-$20 cushion the re-price climbs
into the model's $150+ tranches, so the mean is carried by a quarter of the
hours.

**And the record cannot be applied in that form.** On 24 of the 52 shoulder
days the capped availability (population − max(M, P_U)) sits BELOW MISO's own
metered daily-max coal+gas output (EIA-930), by 0.04–11.2 GW; 19 of the 24 are
cap-caused (the envelope alone is feasible) and **5 are not** — on Jun 23, Jun
24, Jul 24, Jul 28, Jul 29 the KEEPER'S OWN armed envelope leaves less
coal+gas capability than the real fleet delivered (Jul 28: 83.4 vs 86.6 GW).
This is miso-195's W6 at the shoulder grain and it is worse there (6/7 tail
days, 24/52 shoulder days vs 6 violation days in the top-200 set): the record's
numerator carries non-population MW (wind derates, nuclear, non-modelled
steel) with no fuel identity to strip. **Feasibility-clipped** (post-hoc,
disclosed: max(0, min(P_U, population − measured max) − M) per day) the
deficit is **4.94 GW mean in the shoulder (share 0.182) and 1.21 GW in the
tail (share 0.005)** — the clip binds on 67 % of shoulder hours and 93 % of
tail hours, because on the tail days the metered fleet delivered 81–87 GW of
coal+gas and the record leaves almost nothing to remove. **Feasibility-clipped,
item 1 reaches neither population's line.**

**Verdict, item 1: NOT CHARTERED as a lever; the cell `campd_outage_windows`
stays K with miso-195's remove-only cap R inside it.** What it establishes is
the identification the charter asked for: **the quantity the model has and the
market did not is AVAILABILITY, ~5 GW on the shoulder days by MISO's own
bookkeeping (7 raw, 4.9 feasibility-clipped), more than half of it in
Central** — and item 0 locates it: the model's coal fleet runs 3.4 GW above
the measured coal output at 97.7 % of its own capability, so the envelope's
missing outage MW sits on the coal/steam side, not on the CTs the charter
named. It converts to price in the shoulder at 18 % and in the tail at 0.5 %
— the tail's real dispatch was so deep that MISO's own metered output leaves
the record no room, which is the same thing miso-207 measured as a −5.2 GW
minimum margin: the model is ALREADY tight there. Its admissible successor
form is fuel-identified and unit-grain (§6), not the MOM cap.

Signs held all three years (deficit +1.47 / +1.72 / +7.05 GW shoulder; the
2025 step is the record's July inversion miso-195 §2 measured); 2023/2024
lift shares 0.18 / 0.15 shoulder, 0.006 / 0.03 tail — under the line.

---

## 3. Item 2 — CT_PEAKER conduct: INERT, and the most useful wrong prediction

P2b predicted the real CT fleet ABOVE the model's by ≥ 1.5 GW (reality "runs
deeper into gas"). Measured: **+0.02 GW shoulder, −0.40 tail** (2024: +0.10 /
−0.66; 2023: +1.24 / +0.56 — the one year the sign held, the over-priced year).
The model's 6.6 GW of idle-but-cheap CT is matched by 10.6 GW of real CT
nameplate that was likewise not running. **The CT cushion is not a
CT-availability object and not a "reality ran the peakers" object; it is the
same fleet in the same state at a different price.** Whether the real idle CTs
were unavailable (item 1's deficit is 7 GW on a fleet where CT+ST_GAS are the
first 9 GW of idle) or offered above $90 is the question the lane now owns.

---

## 4. Item 3 — deliverability: an energy object at the hub; a South wheel the LP does not see

* **INDIANA.HUB components in the shoulder: LMP 90.82 = MEC 87.88 + MCC 1.95
  + MLC 0.99.** |MCC| is **4.5 %** of the shoulder gap (tail: MCC 24.3 of 718,
  3.8 %). H4 transfers from the tail to the shoulder: **a system-energy
  object**; deliverability INTO the pocket that sets the comparator is refused
  by the price identity (P3a RIGHT).
* **The RDT bound South→North in 50.4 % of shoulder hours and 66.7 % of tail
  hours vs 32.5 % of the other Jun–Jul daytime hours** (2024: 54 % / 33 %;
  2023: 19 % / 67 %). P3c ("≤ 20 %") WRONG. M2M: Σ shadow 575 vs 357
  (1.6×, P3b marginally wrong), 1.9 vs 2.0 binding flowgates. The keeper's
  zone-price spread in the same hours is **$1.36 mean** — the LP's 2,500 MW
  S→N contract-path link is not binding where the real RDT was.
* **MISO-South holds 31.8 % of the within-$20 cushion (3.45 GW; tail 42.6 %,
  1.35 GW).** Stranding it in the real RDT-binding hours lifts the shoulder by
  $2.1 (share **0.048**) and the tail by $4.4 (0.007); stranding it in every
  hour 0.090 / 0.008. **REFUSED as a lever** (P3e RIGHT): the Midwest keeps
  7.4 GW of cushion within $20 without the South. NAMED: the LP's RDT
  representation does not bind in half the hours the real one did — a
  deliverability defect whose price reach at this keeper is < 10 %; it is not
  `measured_interface_limits` (R, miso-174 — the PJM/SPP seam imports) and not
  `m2m_seam_entitlement_cap` (G) — no cell carries it; not minted (no
  mechanism proposed, rule 28c does not fire).

---

## 5. Item 4 — declared emergencies: the tail is event-coincident, the shoulder is not

2025 registry on the model clock (CST, one hour earlier than the armed EST
placement): Jun 23 Step-1 (Midwest), Jun 24 Warning, Jul 24 Advisory, Jul
28 12:00–Jul 29 22:00 Advisory, Jul 28 14–22 Alert, Jul 29 Warning.

| | SHOULDER | TAIL |
|---|---:|---:|
| hours in any declared window | 58 / 351 = **16.5 %** | 11 / 15 = **73 %** |
| in Warning+ (tier-priced) | 41 | 8 |
| gap carried by in-window hours | **26.0 %** (Warning+: 23.5 %) | **76.6 %** |
| actual mean in / out of window | $130.9 / **$82.9** | $758.9 / $606.8 |
| model mean in / out of window | $62.0 / $44.1 | $93.5 / $48.3 |
| regspin binding hours (all in-window) | 6 / 6 | 4 / 4 |

**Out-of-window hours carry 74 % of the shoulder gap at an actual mean of
$83.** The shoulder is NOT an emergency-declaration regime (P4b decision
rule); the in-window quarter is the `ordc_scarcity_overlay` G's cousin and is
named, not built. The tail IS event-coincident (11/15). **The armed tier floor
is silent in every 2025 Warning+ hour** — model max $141.7, slack 0.0 MWh,
min idle thermal 2.18 GW in the (EST-placed) windows — because the LP has
supply: the same ~7 GW item 1 says the market did not (P4d RIGHT). In 2024
the floor DID print ($500, 19.4 GWh of slack in the Aug 26 window; outside
Jun–Jul). H3: all 6 shoulder regspin binding hours sit inside declared
windows — the tier/event state is the binder, not everyday reserves.

---

## 6. Verdict, and the successor

**P9 as pre-registered: nothing is chartered and no LP is spent.** The one
candidate reaching 0.25 in both populations on its raw form (item 1, 1.11 /
0.29) does so in a form MISO's own metered output refutes on half the shoulder
days; feasibility-clipped it reads 0.18 / 0.005, and its cell is R for exactly
that reason. Item 0's map reaches the shoulder on the 930 basis (0.39) and not
the tail (0.14). Items 2/3/4 refused on their own rules.

**What the charter's "8–11 GW" turned out to be.** Not peaking supply the
model runs and the market did not — the market ran the model's CT fleet to
0.02 GW. The model's cushion is a COST-basis statement: 10.85 GW of capability
whose mc sits within $20 of a $47 clearing price; reality's counterpart idle
MW did not clear at $91. The model's real surplus is **5.5 GW (shoulder) /
4.3 GW (tail) on the coal side plus imports**: coal run 3.4 GW above the
measured output at 97.7 % of the model's own capability, i.e. the armed outage
envelope is ~3–5 GW too shallow on the coal/steam fleet in the shoulder, which
is what MISO's published unplanned record says at fleet grain (7 GW raw, 4.9
feasibility-clipped, Central-weighted). Re-priced, that surplus is worth 18–39 %
of the shoulder gap and 0.5–14 % of the tail's: the shoulder's coal-side
availability object is REAL and worth building the admissible way; it is not
the tail's object, where the model is already tight (miso-207) and the price
is a Warning-window/RT-dynamics regime the LP cannot see (§5). Two readings of
the remaining ~60 % of the shoulder gap: (a) availability beyond what the
record's feasibility permits (none measurable here); (b) conduct that is not
an offer LEVEL (the offer family is R/I — the model is +$15 OVER the book at
the median rank): a commitment state (an idle CT is not online; ELMP prices
are set by online resources) or 5-minute RT dynamics — both already named
(miso-203, the ramp product's four objections).

**Successor, named and not built (rule 28a checked):** a **fuel-identified,
unit-grain unplanned-derate measurement** for the coal/CC/ST fleet — CAMPD
gross load below the unit's demonstrated capability while online (a partial
derate), which the zero-generation detector behind `campd_outage_windows`
cannot see and which the MOM record says is ~5–7 GW on the shoulder days and
item 0 locates on the coal side (+3.4 GW run above measured output). The
registered form is `unit_partial_outage_windows` (default OFF in the keeper;
registered under the `unit_outage_short_windows` row, MISO cell K), forward
analogue = per-class derate rates. Its phase 0 must show, BEFORE any solve:
(i) the per-unit partial-derate MW on the 52 shoulder days sums to a number
between the coal-side excess (3.4 GW) and the raw 7 GW, with the
feasibility-clipped 4.9 GW the expected value; (ii) it is
Central-weighted like the record; (iii) it is not already carried by the
armed envelope's statistical stack (rule 19 `[R-ONE-MECH]`, miso-195 W1
census); (iv) leave-one-year-out within 2023–2025 (2023/2024 deficits are
1.5–1.7 GW — a lever sized to 2025 must stay silent there).

---

## 7. The G-D repair (second deliverable)

`_miso203_summer_peak_anchor_phase0.json::g_d_reserve_binding` re-computed on
miso-203's OWN hour set, capability matrix and requirement, changing exactly
one thing (the COAL group's dispatch = the pooled COAL_* klass dispatch),
after the defective numbers were reproduced to ±5 MW (R-1 PASS, all three
years); defective block preserved under `pre_repair`:

| year | broad margin min (was → is) | broad margin mean | armed idle | G-D |
|---|---:|---:|---:|---|
| 2023 | 42,736 → **12,612 MW** | 47,644 → 18,139 | 15,789 (unchanged) | FAIL (0.01 %) |
| 2024 | 38,375 → **4,407** | 46,997 → 16,039 | 11,752 | FAIL (0.35 %) |
| 2025 | 30,533 → **−524** | 37,115 → **4,902** | 5,621 | FAIL (margin ≤ 0 at the min; 6.7 MW vs 4.9 GW mean = 0.14 %) |

miso-203's G-D refusal stands on the repaired numbers, and its LOCATION
ground (the hinge at its zero point in the object's hours) is untouched.
`temp_dependent_derate`'s MISO evidence is stamped with these values; the
42.7 / 38.4 / 30.5 GW figures are retired from every citation.

---

## 8. My prior, scored against interest

| # | prediction | conf. | measured | verdict |
|---|---|---:|---|---|
| P0a | demand within ±3 % | 0.7 | identical (930 is the loader) | RIGHT (trivial) |
| P0b | coal model +2 to +6 GW | 0.6 | **+3.43 on 930**; −0.34 on part-gross CAMPD (≈ +1.7 net-adjusted) | RIGHT (930), marginal (CAMPD) |
| P0c | gas model BELOW actual ≥ 2 GW | 0.65 | **−7.81 on 930**; CAMPD: ST_GAS −2.0, CC −0.9, CT +0.02 | RIGHT — but not in the classes the charter named |
| P0d | import model +1 to +3 | 0.6 | +0.61 shoulder / +2.17 tail | half |
| P0e | wind 1.05×, solar identical | 0.95 | +0.33 GW / 0.00 | RIGHT |
| P0f | nuclear+hydro within ±1 | 0.7 | −0.06 | RIGHT |
| P0g | model-excess 4–9 / 5–11 GW | 0.55 | 930: **5.50 / 4.34**; CAMPD 3.0 / 3.0 | RIGHT shoulder, WRONG tail (both bases) |
| P0h | excess share 0.20–0.45 / ≥ 0.25 | 0.5 | 930: 0.387 / **0.140**; CAMPD 0.13 / 0.09 | RIGHT shoulder (930), **WRONG tail** |
| P0i | CT actual > model ≥ 1.5; CC model > actual ≥ 1 | 0.6 / 0.55 | +0.02; CC −0.9 | **WRONG / WRONG** |
| P1a | deficit +4 to +8 / +5 to +9 | 0.65 | +7.05 / +6.79 | RIGHT |
| P1b | Central ≥ 50 % | 0.6 | 53 % | RIGHT |
| P1c | leg A ≤ 10 %, leg B′ 10–30 % | 0.6 | 8.0 % / 27.4 % | RIGHT |
| P1d | lift share 0.10–0.25 / 0.15–0.30 | 0.6 | **1.11** / 0.29 | **WRONG** (shoulder, by 4×) |
| P1e | W6 ≥ 3 violation days | 0.7 | 24 (5 not cap-caused) | RIGHT, under-stated 8× |
| P2b/c | actual CT ≥ model + 1.5 / + 2 | 0.6 | +0.02 / −0.40 | **WRONG — the result** |
| P3a | MCC small, ≤ 15 % | 0.7 | 4.5 % / 3.8 % | RIGHT |
| P3b | M2M ≤ 1.5× | 0.6 | 1.6× | wrong (marginal) |
| P3c | RDT S→N ≤ 20 % | 0.6 | **50 % / 67 %** | **WRONG** |
| P3d | South 20–40 %, spread ≤ $5 | 0.6 | 31.8 %, $1.36 | RIGHT |
| P3e | strand ≤ 0.10 | 0.75 | 0.048 / 0.007 | RIGHT |
| P4a | 15–35 % in window, ≤ 15 % Warning+ | 0.6 | 16.5 %, 11.7 % | RIGHT |
| P4b | in-window 25–50 % of gap; out-of-window ≥ $70 | 0.5 / 0.6 | 26.0 %; $82.9 | RIGHT |
| P4c | tail ≥ 8/15 in window | 0.6 | 11/15 | RIGHT |
| P4d | tier floor silent, slack 0 | 0.85 | max $141.7, slack 0 | RIGHT |
| P9 | nothing chartered, no solve | 0.75 | as stated | RIGHT |
| P10 | supply-side excess 5–11 GW in the tail | 0.55 | 4.34 (930) / 3.0 (CAMPD) | **WRONG** (marginal on 930) |
| N-5 | envelope reproduces miso-195 ±0.15 | — | 35.36 vs 36.82 | FAILED, cause identified (§0.3) |
| H1 | "8–11 GW idle within $20" is a QUANTITY claim about the peakers | — | CT fleet identical; the surplus is 5.5 / 4.3 GW on the coal side | **FAILS as stated; holds as a cost-basis one, and the quantity is half the size in a different class** |
| H4 | energy object transfers to the shoulder | — | MCC 4.5 % | holds |

Read honestly: the outage arithmetic (P1a–P1c), the coal/gas signs and the
deliverability / emergency censuses were predicted correctly; **the two
predictions that carried the charter's premise — that the real market ran
MORE peakers than the model (P2b) and that the surplus sits in the tail at
5–11 GW (P10) — were wrong**, and the record's raw conversion (P1d) was
under-predicted by 4× until the feasibility clip brought it back inside the
prediction. The eighth consecutive MISO session whose most useful output came
from the part of the prior that was wrong: the surplus is real, half the size,
and on the other side of the stack.

---

## 9. Governance

Rule 15: zero-solve, nothing registered. Rule 28(a): no R/I/G cell re-tested;
`campd_outage_windows` K / `temp_dependent_derate` K /
`m2m_seam_entitlement_cap` G / `maxgen_emergency_tier_pricing` K carry
appended evidence, no verdict moves; §5.4 stamp. Rule 28(c): no field. Rule
25: MISO's shard only. Rule 22: 2023–2025 only. Rule 13: every measured source
is a physical/market quantity read as a diagnostic; nothing entered a solve.
Rule 27: three ≥300-line files edited locally and blob-verified after push.
Rule 1: nothing moved, nothing armed.

**Records:** this file; `PREREG-miso208-find-the-supply-2026-09-04.md` @
`6a50d0fc`; `_miso208_find_the_supply.json`;
`scripts/probes/_miso208_find_the_supply.py`;
`scripts/probes/_miso208_repair_miso203_gd.py`; repaired
`_miso203_summer_peak_anchor_phase0.json` (G-D, `pre_repair` kept).

Next shorthand: **miso-209**.
