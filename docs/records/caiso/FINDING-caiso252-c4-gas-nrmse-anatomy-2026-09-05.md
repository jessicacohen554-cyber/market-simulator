# FINDING — caiso-252: the C4 2025 cell is **not** the object the handoff named. CC_REGULAR carries **90 / 87 / 95 %** of the gas-fleet MSE in every year as a **DIURNAL** error — the model's CC over-generates at night and in the evening and under-generates mid-day — and, hour for hour, that error is the **mirror of the model's import diurnal shape** (too flat: night/evening −0.4…−1.7 GW, mid-day +1.4…+2.0 GW in 2025). The caiso-251 degradation (0.298 → 0.305) splits **56 % CC / 59 % CT** (cross-terms negative) and sits **entirely in Aug–Dec**; the CT half clears three modern LA-basin/SDGE peakers into the evening while **the real CT energy is ONE NP15 plant, Panoche** (0.74 / 1.42 / 0.85 TWh actual vs 0.16 / 0.13 / 0.05 model — 39 / 68 / 86 % of the CEMS-basis CT miss). The import-drop hours carry **2 %** of the ΔMSE. The night/evening imports the model lacks were **not economic imports** in the real market: measured CAISO DA sits within $0.3 of both hubs at night and exceeds hub + wheel in **2–5 %** of night hours, and the model's λ matches it within $0.5 — the model is short of price-taking import VOLUME at a matched price, and fills it with CC. **The DMM 2025 annual report has published and its RA-import figure is NOT like-for-like (methodology change)** — adjudicated under the rule-14 misalignment exception, recorded in the source. **ZERO SOLVES, NOTHING ARMED, keeper unchanged. 3 of 10 predictions hold, 7 FALSIFIED — most in the direction that makes the object HARDER.**

**Session caiso-252, 2026-09-05.** Branch
`claude/caiso-252-backcast-calibration-4xvfvn` off `main` `95739d60`. Keeper
**`2026-09-05-caiso-251-b1-nomargin`** (`caiso251_arm_nomargin`) **UNCHANGED**,
NOT-YET on the lone supporting-tier C4 2025 cell. Pre-registration
`PRECOMMIT-caiso252-c4-gas-nrmse-anatomy-2026-09-05.md`, pushed to `origin`
before the estimator was written and before any cell of the object was
computed; its §4 G-DRIFT audit (`90b2ef51 → 95739d60`, 26 files, every hunk
INERT) was recorded there and stands — no arm was solved, so it was not spent.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only; no `complete`/`final` marker; freeze
ACTIVE. Instrument: `scripts/probes/_caiso252_c4_gas_nrmse_anatomy.py` →
`results/calibration/_caiso252_c4_gas_nrmse_anatomy.json`.

---

## §1 — G-REPRO: the instrument IS the scorer

The probe rebuilds `calibration_verdict._cems_gas_hourly_fit` plant-for-plant
from the two committed run payloads and the three CAISO bench parts (85
CEMS-covered gas plants per year). All six (r, NRMSE) pairs reproduce the
committed `_verdict.json` rows **exactly** at 3 dp: keeper 0.877/0.285,
0.905/0.264, 0.870/0.305; prior keeper 0.879/0.283, 0.905/0.266, 0.872/0.298.
Everything below is read on the scorer's own basis, on the scorer's own clock.

Two basis facts the reader needs. (1) The fleet-level bias is fixed by the
fuel-row gap (2025: model 51.17 vs actual 50.84 TWh → mean error **+37 MW** on
a 5,805 MW mean; `mean(e)²` is **0.04 %** of the MSE). The cell is **shape**.
(2) The **CEMS-basis** CC_REGULAR level in 2025 is **+3.22 TWh** high (41.59
vs 38.36), while the C1 fuel-mix row for 2025 CC is **SKIPPED** (preliminary
EIA-923, 88 % reporting, 41.58 vs a partial 40.00). The over-run is real on the
metered basis and invisible to C1; it is concentrated in **Sep–Dec** (+361 /
+796 / +553 / +701 GWh) and January (+450), and the prior keeper already carried
+2.48 TWh of it — caiso-251 added +0.75.

---

## §2 — THE ANATOMY (pre-registered legs)

### §2.1 — By class: CC_REGULAR is the object, in every year

Exact covariance attribution `MSE_c = cov(e_c, e)`, share of `var(e)`:

| class | 2023 | 2024 | **2025** | 2025 bias (MW) | 2025 bias² / own MSE |
|---|--:|--:|--:|--:|--:|
| **CC_REGULAR** | **0.901** | **0.874** | **0.946** | **+368** | 0.04 |
| CT_PEAKER | 0.072 | 0.092 | 0.047 | −106 | 0.10 |
| CC_CHP | 0.019 | 0.018 | 0.003 | +4 | 0.00 |
| ST_GAS | 0.009 | 0.014 | 0.003 | −4 | 0.00 |
| CT_CHP | −0.000 | 0.002 | 0.001 | −2 | 0.01 |

CC_REGULAR is the top class in all three years (P-8 HOLDS), and the top five
plants carry 39 / 42 / **45 %** of the MSE (P-9 HOLDS; Delta 12.0 %, Colusa
9.1 %, Metcalf 8.2 %, Gateway 8.2 %, Moss Landing 7.9 % in 2025 — the NP15 CC
fleet). **P-2 is FALSIFIED upward** (0.946 > 0.75): CC is not the majority of
the object, it is the object. **P-6 is FALSIFIED on its level leg** (+368 MW is
outside the registered [+40, +150]) while its shape leg holds (bias² 4 %): the
CC error is a SHAPE error carrying a LARGE level term underneath it.

### §2.2 — By hour-of-day: the sign flips twice a day

CC_REGULAR mean error by hour-of-day, 2025 (MW, model − CEMS):

| Pacific hour | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| | +931 | +686 | +327 | +132 | +489 | +982 | **+1357** | +467 | −768 | −765 | −652 | −577 |
| **12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23** | | | | | | | | | | | |
| | −605 | −672 | −754 | −777 | −381 | +548 | +1425 | +1423 | +1379 | +1402 | **+1619** | +1617 |

The model's CC cycles **harder** than the real fleet: +0.9…+1.6 GW over at
night and in the evening, +1.0…+1.4 GW over in the 05–06 morning ramp, and
−0.6…−0.8 GW under through the solar belly. The same pattern holds in 2023 and
2024 with a smaller night term (2023 night was **negative**, −460…−940 MW —
see §3.1 for what changed). Because the sign alternates, the MSE is spread
across the day rather than peaked: evening 17–21 carries 0.239 and mid-day
10–15 0.251 (P-5 **FALSIFIED** both legs — the error is not an evening-ramp
error; it is a two-sided diurnal amplitude error).

### §2.3 — By month: the 2025 MSE and the whole ΔMSE sit in Aug–Dec

2025 MSE month shares: Aug 0.113, Sep 0.123, Oct 0.126, Nov 0.100, Dec 0.128
(59 % in five months). The **keeper-vs-prior ΔMSE** by month: Aug 0.26,
Sep 0.22, Oct 0.21, Nov 0.19, Dec 0.29 — **Sep–Nov carry 62 %** and Jan–Jul
net **−0.17**. **P-7 is FALSIFIED**: the degradation IS localized to the
caiso-246 daily-spot overlay months plus Aug and Dec. That is not because the
arm's offer delta is larger there (the arm added CC fairly evenly, +17…+119
GWh/month) but because the CC error was **already large and positive** there
(§1's Sep–Dec level over-run), so `e·Δe > 0`: the arm pushed CC up where the
model already over-ran.

### §2.4 — Keeper vs prior keeper: the degradation is HALF CT, and NOT the import-drop hours

Exact class split of the 2025 ΔMSE (+153,953 MW²): **CC_REGULAR +86,727
(56 %)**, **CT_PEAKER +91,556 (59 %)**, CC_CHP −8,278, ST_GAS −11,047,
`Δmean²` −5,217. **P-3 FALSIFIED** (56 % < 60 %): the newly clearing CT
tranches carry as much of the degradation as CC does. **P-10 FALSIFIED** in
both years (ΔMSE_CT **+125,562** in 2024, **+91,556** in 2025): the CT that
caiso-251 added clears in the **wrong hours**, at the **wrong plants** (§2.6).

The import leg: `r(ΔCC(h), Δimport(h)) = −0.646` (the first leg of P-4 holds —
CC does take the import's place), but the 822 hours with `Δimport < −500 MW`
(9.4 % of hours, mean ΔCC **+816 MW** — 0.67 of the arm's +0.74 TWh CC rise)
carry **2.1 %** of the ΔMSE. **P-4 FALSIFIED.** The CC-for-import
substitution happened mostly in hours where it was harmless (the afternoon,
where CC was UNDER); the MSE grew in the night/evening hours where ΔCC is
small on average but the error was already large. By hour-of-day the
keeper−prior Δ is: CC **+252…+404 MW over 00–05** against import
**−280…−403**; CT **+94…+161 MW over 17–23** against ST_GAS −20…−44 and
storage net −44…−139. The ΔMSE attribution (`Δe_c·(e_K+e_P)`) puts CT at
**+295…+559 k MW² per evening hour** and CC at +165…+342 k in hours 00–01 and
05–06.

---

## §3 — POST-REGISTRATION LEGS (labelled; none scored)

### §3.1 — The diurnal error budget names the counterpart: the IMPORT SHAPE

Model − measured (EIA-930 CISO, model clock) by day-block, 2025, MW:

| series | night 22–05 | morn 06–08 | day 09–15 | eve 16–21 |
|---|--:|--:|--:|--:|
| gas (CEMS basis) | **+790…+1601** | +331…+1196 | **−588…−898** | −589…+1344 |
| **net import** (model gross vs 930 net) | **−224…−1724** | −166…−1289 | **+1436…+2015** | −590…+1731 |
| solar | +35…+40 | +910…+4232 | +579…+2219 | −187…−3680 |
| hydro | −43…+163 | −785…+68 | −409…+25 | −0…+558 |

Hour for hour, the CC over-generation at night/evening is the model's import
**shortfall** in the same hours, and the mid-day CC under-generation is the
model's mid-day **over**-import. The model's import profile is too flat:
2025 measured net import swings **1.3 → 6.2 GW** across the day (a 4.9 GW
range), the model's **3.2 → 5.9 GW** (2.7 GW). The mid-day half is two
adjudicated objects (the clean-depth tranches at the raw Palo Verde hub, and
the P1 pass having **no export outlet** — `caiso_p1_export_sink_seam` R,
caiso-142/244 §3.2). The night/evening half is what changed between 2023 and
2025: measured overnight net import rose **5.3 → 6.2 GW** (+0.9 GW) while the
model's stayed **5.9 → 5.8 GW** — the firm block's level is a capability
(DMM RA imports, 2,323 → 3,371 → *3,371 carried*) and the spot ladder does not
fill the gap at night. In 2023 the model OVER-imported overnight (+0.6…+1.1 GW)
and UNDER-generated CC overnight (−0.5…−0.9 GW); by 2025 both signs flipped.
The DMM 2025 report confirms the direction from outside: California net
imports rose **+430 MW across all hours (17 %)** before, **+580 MW (26 %)**
after, WEIM dynamic transfers in 2025 vs 2024.

### §3.2 — The missing night/evening imports were NOT economic imports

If the real night imports cleared on a hub-plus-wheel delivered cost, the
measured CAISO price would sit above the hub by at least the wheel. It does
not. 2025, by day-block (measured CAISO system DA/RT vs the MALIN / PALOVRDE
hub; "delivered" = hub × (1 + loss) + wheel from `CAISO_IMPORT_DELIVERY_BASIS`):

| block | DA − Malin | DA − PV | model λ − Malin | model λ − PV | DA > delivered (Malin / PV) | model λ > delivered |
|---|--:|--:|--:|--:|--:|--:|
| night 22–05 | **−0.3** | **−0.0** | +0.2 | +0.5 | **0.02 / 0.05** | 0.06 / 0.11 |
| morning 06–08 | −9.5 | −2.3 | −2.2 | +5.1 | 0.00 / 0.18 | 0.12 / 0.46 |
| day 09–15 | −7.9 | +4.6 | −2.4 | +10.1 | 0.01 / 0.37 | 0.19 / 0.70 |
| evening 16–21 | +0.9 | +4.5 | −3.7 | −0.1 | 0.13 / 0.30 | 0.09 / 0.23 |

At night the measured price **equals the hubs** (DA 42.2 vs Malin 42.6 / PV
42.3) and the model's λ (42.8) matches it within $0.5. Both the market and the
model say: no delivered-cost import is in merit at night. The real market moved
6.2 GW anyway. So the 0.4–0.8 GW the model lacks at night (0.6–1.7 GW in the
evening) is **price-taking volume at a matched price** — contracted,
self-scheduled or WEIM-transferred energy of the kind the firm block and the
no-wheel `DSW_overnight_clean` row represent — and the model, short of that
volume at its capped depth, fills it with CC at the same λ. **This is a VOLUME
object at a degenerate margin, not a pricing object**: it explains why
caiso-251's small CC offer cut moved C4 (CC won more of a flat margin) while
moving C3a's night prices not at all.

### §3.3 — The CT leg is one plant: Panoche

CEMS-basis CT_PEAKER, 2025: actual **1.64 TWh**, keeper 0.71, prior 0.34. The
real energy is **Panoche Energy Center (56803, NP15, 432 MW): 0.852 TWh** —
52 % of the class — running **3,027 h, 1,994 h above half nameplate, 87–138 MW
overnight and 164–180 MW in the evening**. 2024 was the same and larger: 1.421
TWh, 4,839 h, 166–211 MW overnight. The model gives it **0.164 / 0.130 / 0.053
TWh**; it carries **0.57 / 1.29 / 0.80 TWh = 39 / 68 / 86 %** of the
CEMS-basis CT miss. Meanwhile the plants caiso-251's cheaper CT offers cleared
— Walnut Creek 0.20 vs 0.06 actual, Pio Pico 0.17 vs 0.06, Sentinel 0.18 vs
0.17 — are the modern LA-basin/SDGE LMS100 peakers, and they are the top three
plants by ΔMSE contribution (Walnut Creek +29.5 k, Sentinel +27.8 k, Pio Pico
+24.1 k MW²). 8 of 43 CT plants over-run (+0.29 TWh); 35 under-run (−1.22 TWh).
Panoche's conduct is not peaking — a 400 MW LMS100 station at 100–200 MW
overnight for 3,000–4,800 h is out-of-market committed capacity, exactly what
caiso-119 R4 called it. Object C (the CT volume miss) is therefore **not a
fleet-wide offer or availability question**; it is mostly one plant's
commitment, and the caiso-119 R4 guardrail governs it: **only a real
obligation-keyed instrument with a cited D-4 window is admissible; no
plant-level pin** (rule 13, rule 21).

### §3.4 — The DMM 2025 annual report: published, and NOT a like-for-like repair

`IMPORT_TRANCHES_BY_YEAR["CAISO"][2025]` carries 2024's DMM RA-import
capacity (3,371 MW) under an explicit OPEN DATA GAP note ("replace when the
DMM 2025 annual report lands"). It landed **2026-06-26**
(`caiso.com/documents/2025-annual-report-on-market-issues-and-performance.pdf`,
sha256 `7c89fdc42ef10968b194a3919dfb8f3ecf3ce52b53ffbe4bb9607e92a9915ea9`,
354 pp). Its Table 16.7 "Imports" row reads **1,710 MW** (Imports-MSS 201).
It is **not adopted**, under the rule-14 misalignment exception, because the
table's own basis changed: 2025 uses **60 availability-assessment hours, many
in spring** ("notably lower than in previous years that use the different
methodology"; total RA 46,169 MW vs 52,646 MW on the 2024 summer-day basis),
and the report states RA imports "were lower during the summer months but
higher during other periods compared to 2024". A spring-weighted average of a
summer-contracted product is a different aggregation from the 2023/2024 rows.
No like-for-like 2025 number exists in the report (Figure 16.9 is a chart of
peak-hour bid volumes by price bin). The note is rewritten at the source
(`interchange/spec.py`, `capacity_market.py`) to record the adjudication and
what a reconciled value would need (a same-basis summer cut, or the CPUC RA
compliance filings). **Nothing else in the code moves.**

---

## §4 — PREDICTIONS, SCORED AGAINST INTEREST

| # | registered | measured | verdict |
|---|---|---|---|
| P-1 | G-REPRO ≤ 0.001 on all six | exact | **HOLDS** |
| **P-2** | CC share in [0.45, 0.75] | **0.946** | **FALSIFIED (above)** — CC is the whole object |
| **P-3** | ΔMSE_CC ≥ 0.60·ΔMSE | 0.56 | **FALSIFIED** — CT carries 0.59 |
| **P-4** | r ≤ −0.5 AND import-drop hours ≥ 50 % of ΔMSE | r −0.646 ✓; **2.1 %** ✗ | **FALSIFIED** — the substitution hours are not the error hours |
| **P-5** | evening ≥ 0.35 AND mid-day ≤ 0.15 | 0.239 / 0.251 | **FALSIFIED** — two-sided diurnal error |
| **P-6** | CC bias in [+40, +150] MW AND bias² < 25 % | **+368** / 4 % | **FALSIFIED** on level — a +3.2 TWh CEMS-basis over-run |
| **P-7** | Sep–Nov ≤ 40 % of ΔMSE, no month > 20 % | **62 %** / 12.8 % | **FALSIFIED** — localized to Aug–Dec |
| P-8 | CC top class all years | yes | **HOLDS** |
| P-9 | top-5 plants ≥ 40 % | 45.4 % | **HOLDS** |
| **P-10** | ΔMSE_CT < 0 in 2024 and 2025 | **+125.6 k / +91.6 k** | **FALSIFIED** — the new CT clears in the wrong hours/plants |

**3 hold, 7 falsified.** Unlike caiso-251 §5.1, the failures here run
**against** the handoff's framing and against convenience: the object is
larger and less tractable than registered (P-2, P-6), the degradation has a
second carrier the handoff ranked last (P-3, P-10), the named suspect's
mechanism is not where the error grew (P-4), and the error is localized to
months a prior repair touched (P-7). The predictions bound.

---

## §5 — DISCLOSURES AGAINST INTEREST

1. **§3 is post-registration.** The diurnal budget, the spread test, the
   Panoche ranking and the monthly table were not in the PRECOMMIT's §1.2
   list. They are characterisation of a registered cell, reported as such
   and scored nowhere. The falsifications in §4 are on the registered legs.
2. **The demand basis confounds absolute budget rows.** The model dispatches
   205.6 TWh of grid-delivered load against 223.8 TWh of EIA-930 demand
   (caiso-247 §4.5), and the gap is mid-day-shaped (−5.8 GW at 10–12 in
   2025). §3.1 therefore leans only on the two supply-side rows that are
   measured on their own terms (CEMS gas; 930 net interchange), whose
   hour-by-hour mirror does not depend on the demand basis.
3. **The CEMS-basis CC level (+3.22 TWh) and the C1 row (SKIPPED) disagree
   on what 2025 CC did**, and I cannot say from committed artifacts whether
   the preliminary EIA-923 or CAMPD is closer to the final 923. C4 is scored
   on CAMPD; this finding reads CAMPD; the level term is reported, not
   asserted as the final answer.
4. **The spread test uses the SYSTEM DA/RT LMP** (`actual_lmp_hourly_CAISO`
   is not zonal) against zonal hubs; the model side is checked on both the
   load-weighted λ and the NP15 / SP15_rest duals and the two agree within
   $0.7 in every block. A zonal measured series would be sharper.
5. **Panoche is read from CEMS conduct, not from a contract record.** That it
   runs like committed capacity is measured; WHY is not established here.
6. **No arm, and I say why rather than solve something.** Every mechanism
   behind the carriers is either adjudicated (`caiso_p1_export_sink_seam` R;
   the clean-depth lane closed at caiso-244 §3.5; the storage charge-side
   census closed at caiso-168 §8 / caiso-250 §7; `gas_offer_net_revenue_margin`
   R), an owner methodology ask (the transport adder on a spot-indexed
   marginal offer, caiso-244 ask E — and §3.2 shows the adder is not where
   the night volume is), a data question with no like-for-like source yet
   (§3.4), or a per-plant commitment with no admissible instrument (§3.3).
   Solving any of them on this residual would be rule-1/13 fitting.
7. **The regenerated `data/clean` tree was built and not used.** No solve was
   spent; rule 29's screen was never reached.

---

## §6 — THE QUEUE, RE-RANKED

1. **Object A is RE-NAMED: the night/evening price-taking import VOLUME
   (2025).** The C4 cell is the CC mirror of a 0.4–1.7 GW night/evening
   import shortfall at a matched price. What it needs is a **measured,
   forward-regenerating source for the at-hub import volume beyond the RA
   capability** — the DMM's own "shown RA + non-RA contracted imports" native-
   load-need series (report §17, Figures 17.3–17.5, Malin and NOB by month)
   is the candidate object, and it is a **data-intake question first**
   (rule 13 admissibility to be adjudicated: it is a contracted-capability
   showing, not a realised flow). Not a ladder-price object (§3.2).
2. **Object C is RE-NAMED: Panoche.** 39 / 68 / 86 % of the CT miss. An
   instrument exists only if a public obligation keys its commitment; the
   caiso-119 R4 guardrail stands. Next step: find the instrument (RMR / CPM /
   exceptional-dispatch record) or close the object as un-groundable.
3. **The CT evening mis-allocation** (Walnut Creek / Sentinel / Pio Pico
   clearing where Panoche runs) — a within-class merit-order symptom of 2;
   not a separate lever.
4. **The 2025 DMM RA-import value** — reconcile on a same-basis source
   (§3.4) before it can replace the carried 2024 figure. A data ask, not a
   CAISO solve.
5. **Object B (the CC-hot half) is DEMOTED**: the CC price residual is a
   different observable from the CC diurnal volume error, and this session
   shows the volume error is an import-shape mirror, not an offer-form
   question. Its charter, if funded, must not be sold as a C4 lever.
6. Carried unchanged: D (the Pacific 07–08 slab — note §2.2 shows CC's
   morning-ramp over-run at 05–07, the same hours, +1.0…+1.4 GW), E (the
   per-zone sidecar instrument ask), F (the C3a weight basis), G (the stale
   forecast-board top-level keeper stamp), and the caiso-244 owner asks.
7. **Housekeeping, cross-ISO, not acted on**: all 14 bench parts read STALE
   at HEAD because PR #4808 edited one comment in a `BUILDER_SOURCES` file;
   and the same PR deleted the lane's named reusable probes (they are read
   from `d6891edd` when a construction is needed).

---

## §7 — DO-NOT-REDO ADDS

1. **Never read the C4 2025 cell as a CC_REGULAR OFFER question.** It is a
   diurnal VOLUME error and its hour-by-hour counterpart is the import shape
   (§3.1). Never propose a CC offer-level or offer-form move as a C4 lever.
2. **Never propose a ladder PRICE or adder change to recover the night/evening
   imports.** §3.2: the measured price equals the hubs at night and exceeds
   hub + wheel in 2–5 % of night hours; the model's λ matches. The object is
   price-taking volume, and a price lever would be fitting.
3. **Never quote the DMM 2025 Table 16.7 "Imports 1,710 MW" as the 2025 RA
   import capacity on the 2023/2024 basis.** Methodology change; rule-14
   misalignment recorded at the source.
4. **Never treat the CT volume miss as fleet-wide.** It is Panoche (§3.3);
   never pin Panoche to its CEMS conduct (rule 13); never re-price the CT
   class to reach it (caiso-119 R4 guardrail).
5. **Never attribute the caiso-251 C4 degradation to the import-drop hours.**
   2.1 % of the ΔMSE.
6. caiso-251 §8, caiso-250 §7, caiso-249 §7, caiso-248 §8, caiso-247 §8,
   caiso-246 §8, caiso-245 §7, caiso-244 §7, caiso-243 §10, caiso-242 §9,
   caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9, caiso-169,
   caiso-168 §8 stand in full.

---

## §8 — DELIVERABLES

`PRECOMMIT-caiso252-c4-gas-nrmse-anatomy-2026-09-05.md` (pushed first);
`scripts/probes/_caiso252_c4_gas_nrmse_anatomy.py` +
`results/calibration/_caiso252_c4_gas_nrmse_anatomy.json`; the rule-14
adjudication note in `src/market_sim/model/interchange/spec.py` and
`src/market_sim/config/capacity_market.py` (comments only); this finding; the
`docs/calibration-log/caiso.md` entry; evidence appends (no verdict move) on
the CAISO shard cells `gas_offer_net_revenue_margin` and
`caiso_firm_selfsched_floor`. **No run registered (none produced), no keeper
change, no `ScenarioConfig` field, no matrix verdict move.**


---

# PART II — THE ARM (owner-directed, same session): DISARM `caiso_dsw_daytime_evening_trim`. Screened on 2025 first, no control. **PROMOTED — DETERMINATION CALIBRATED, the lane's first.**

## §10 — What was solved and what it read

Owner instruction after §1–§8 above: *"tackle the next run in this session that
you think could address the 2025 miss on C4. Do not run a control and only run
2025 first to see if it passes then if it does run 2023 and 2024."* The arm and
its gates were registered in PRECOMMIT **Addendum A** before the override was
coded (`e03fa2b4`); the rule-29 screen on 2025 (`_caiso252_screen2025.json`)
cleared every registered gate and the owner criterion; the fresh
single-invocation 2023–2025 bundle **`caiso252_b1_notrim`** reproduces the
screen's 2025 to **0.0 MW in every class** and is registered as
**`2026-09-05-caiso-252-b1-notrim`**.

**The arm.** One recorded override-bag value on the caiso-251 recipe,
`caiso_dsw_daytime_evening_trim` **True → False**: the caiso-94 daytime WEIM
clean-transfer row (`WECC_DSW_DSW_daytime_clean`) is restored from hod 6–17 to
**hod 6–21** at the committed, frozen untrimmed depth (5,441 / 5,762 / 5,998
MW). Zero new parameters, zero new fields, no derive re-run; the DOF ledger is
unchanged at 9 entries / 6 residual. The `--caiso-dsw-daytime-evening-trim`
replay override (absent = byte-identical) is the only code added.

**Why it was the arm (Addendum A §A.1).** §3.1 above put the C4 cell's
counterpart at the import shape; the zero-LP read of the import stack found
**no at-hub clean-transfer row for hod 18–23** — caiso-93 covers 0–5, caiso-94
covered 6–21 until caiso-97 trimmed it to 6–17 because the 2026-07-18 keeper
OVER-imported the evening (+1.9/+2.1/+2.2 TWh). On the caiso-251 keeper that
sign had **reversed** (hod 18–21 under-imported by 0.6–1.0 GW with CC
over-generating +1.4 GW in exactly those hours) — the new evidence rule 28(a)
requires to re-test an owner-armed trim. The row's measured admissibility
(FINDING-caiso94 §4A: evening 18–21 raw-hub spread clean, 0 % wedge) was never
in question. A competing arm — pricing the firm RA-import blocks as
price-takers in the availability-assessment hours (CPUC D.20-06-028) — was
**killed at phase 0** (`_caiso252_firm_aah_phase0.json`): the blocks already
sit at 85 % of capability in those hours and the arm could deliver 0.16 TWh.

### §10.1 — Scores, keeper → arm

| criterion | tier | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| C4 gas r / NRMSE | supporting | 0.877/0.285 → **0.880/0.285** | 0.905/0.264 → **0.909/0.261** | 0.870/**0.305** → **0.877/0.297** (FAIL → PASS) |
| C3a price_mean (%) | load-bearing | +4.83 → **+4.65** | +9.44 → **+9.04** | +9.35 → **+8.86** |
| C3b NRMSE | load-bearing | 0.090 → 0.088 | 0.150 → 0.148 | 0.120 → 0.116 |
| C1 / C2 | load-bearing | 12/12, free 8/8; PASS | unchanged | unchanged |
| C3c tail (model h vs actual >$200) | supporting | 24 vs 47 **PASS** | 0 vs 35 **CAVEAT** (ledgered) | 0 vs 8 PASS |
| C6 / C8 | protective | attested PASS / PASS (CC forced 6.6 %) | PASS / 6.7 % | PASS / 8.8 % |
| **determination** | | **NOT-YET → CALIBRATED** | | |

`calibration_verdict`: **CALIBRATED**, 8 scored, target grade 7, fails 0,
ledgered 1 (C3c, 2024 only). Under the promotion rule registered in Addendum A
§A.7 — (a) G-FOOT / G-DIR / G-OVERSHOOT on 2025, (b) no load-bearing criterion
regresses to a new failure in any year, (c) governance holds — **C3a and C4
entered none of the conditions**; every one holds, and the run is promoted.

### §10.2 — Dispatch, keeper → arm (TWh)

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| daytime-clean row in hod 18–21 (keeper: 0 by construction) | +0.50 | +0.65 | **+0.94** |
| daytime-clean row in hod 6–17 | 2.26 | 3.67 | 2.08 (keeper ≈ same; −0.04) |
| `import` klass | +0.45 | +0.59 | +0.80 |
| CC_REGULAR | −0.39 | −0.48 | −0.69 |
| CT_PEAKER | −0.06 | −0.09 | −0.11 |
| hod-18–21 net import vs EIA-930 (keeper → arm) | −0.47 → **−0.05** | −0.44 → **+0.16** | −1.17 → **−0.28** |
| CC 22–23 error, arm − keeper (MW) | −10 | −51 | −66 |

**G-OVERSHOOT** — the caiso-97 objection re-armed as this arm's own falsifier —
passes in every year: the evening block lands within [−0.5, +0.8] TWh of the
measured total, and the trim's original justification (+1.9…+2.2 TWh of
excess) does not re-appear on this keeper.

### §10.3 — Predictions (Addendum A §A.6), scored against interest

| # | registered | measured | verdict |
|---|---|---|---|
| P-A1 | row rises [0.8, 2.0] TWh (2025) | +0.94 in its new window | **HOLDS** |
| **P-A2** | CC_REGULAR 18–21 falls ≥ 0.5 TWh | **−0.315** | **FALSIFIED** — evening storage discharge absorbed 0.47 TWh of the displacement; CC took less than half |
| P-A3 | hod-18 overshoots, 19–21 under, block inside band | hod 18 +108 MW; block −0.28 | **HOLDS** |
| P-A4 | 2025 C4 NRMSE in [0.285, 0.300) | 0.297 | **HOLDS** |
| P-A5 | 2025 C3a falls 0.3–1.0 pp, stays PASS | −0.49 pp | **HOLDS** |
| **P-A6** | `import` +1.0…+1.8 TWh | **+0.80** | **FALSIFIED (low)** |
| P-A7 | C4 does not worsen in 2023/2024; no new load-bearing failure | 0.285 / 0.261; none | **HOLDS** |
| P-A8 | 22–23 CC error within ±150 MW | −66 | **HOLDS** |

Six hold, two falsified — both against the arm's size (it did less to CC and
to the import total than registered), neither in its favour.

### §10.4 — Disclosures

1. **Seventh consecutive favourable direction on C3a**, declared in advance
   (Addendum A §A.4) and excluded from the promotion basis with C4. The
   promotion rests on the three structural gates, the absence of any new
   load-bearing failure, and governance — a reader may delete every C3a and
   C4 number above and still check it.
2. **The screen year was owner-directed** and coincides with the rule-29
   footprint criterion (2025 carries the largest phase-0 footprint). The
   owner's continuation criterion (C4-2025 passing) governed only whether
   2023/2024 were solved; it promoted nothing.
3. **No control solve** (owner rule); G-CTRL form 4 on the §4 G-DRIFT audit.
   The only LIVE hunk at solve time was this session's override, inert when
   absent.
4. **The registration re-rendered the three CAISO bench parts** (the stale
   fingerprint of §5). The prior keeper re-scores **record-for-record
   identical** on the refreshed parts (0 diffs), so only the stamp moved;
   `check_bench_freshness` now reads 0 stale / 3 with engine drift
   (advisory).
5. **The prior-prior keeper's artifacts were pruned on main mid-session**
   (`8066f77c`, after caiso-251's promotion); the §2 anatomy was computed
   before the rebase from its then-committed payload and the committed
   `_caiso252_c4_gas_nrmse_anatomy.json` is the record. The caiso-251 run
   stays on the site as the promoted keeper's control, the precedent caiso-251
   set with caiso-246.
6. **The screen bundle was deleted** after the 0.0 MW reproduction check;
   its numbers live in `_caiso252_screen2025.json`.
7. **The C3c caveat narrowed** (2023 24 h vs 47 now PASSES at 0.51×) without
   being targeted; the attestation ledgers 2024 only. The two carried
   `price_mean` exception entries from earlier attestations are inert (C3a
   passes) and untouched.

## §11 — Queue after the promotion

1. **The hod 22–23 gap** between the daytime (6–21) and overnight (0–5) clean
   windows: CC +1.55/+1.56 GW over at 22–23 in 2025, untouched by this arm by
   construction (−66 MW). The caiso-93 overnight window was "fixed by
   FINDING-caiso91c/92b"; extending it to 22–23 is a window question on a
   frozen derive and needs its own charter (the no-wedge test at 22–23 is
   already measured clean, §3.2).
2. **Panoche** (56803), 39/68/86 % of the CT volume miss — an obligation
   instrument or closure (§3.3).
3. **`complete` marker**: CAISO holds none. The determination is now
   CALIBRATED; declaring `complete` (rule 22, the validation-ladder
   authorization) is an owner act and is the step that would open the
   forecast board's gate (a).
4. The DMM 2025 RA-import basis (§3.4), the C3a weight-basis ask, and items
   E/G carried.

## §12 — DO-NOT-REDO adds (Part II)

1. **Never re-arm `caiso_dsw_daytime_evening_trim` on CAISO without
   re-measuring the evening sign.** It was right when the evening
   over-imported (caiso-97) and wrong once it under-imported (here); the
   measured admissibility of the row never changed. The falsifier is
   G-OVERSHOOT, not C4.
2. **Never read the C4 2025 pass as a C4 lever having worked.** The promotion
   basis excluded it; the arm is a window repair whose falsifier was the
   evening import total.
3. **Never extend the daytime window past 21 or the overnight window below 0
   to reach 22–23 without a charter** — the two windows were fixed by their
   own findings, and the 22–23 hours belong to neither by construction.
4. Part I §7 and everything it carries stand in full.

## §13 — Deliverables (Part II)

PRECOMMIT Addendum A (pushed before the override); the replay override +
CLI flag in `scripts/run_calibration_full.py`;
`scripts/probes/_caiso252_firm_aah_phase0.py` + JSON (the killed AAH arm);
`scripts/probes/_caiso252_evening_trim_phase0.py` + JSON;
`scripts/probes/_caiso252_screen2025.py` + `_caiso252_screen2025.json` +
`_caiso252_arm_vs_keeper_{2023,2024,2025}.json`; `scripts/gen_caiso252_attestation.py`;
the bundle `caiso252_b1_notrim` (slim files + `hourly/` sidecars,
`legitimacy_diagnostics.json`, attestation with DOF ledger, `metrics.json`,
`_verdict.json`); run **`2026-09-05-caiso-252-b1-notrim`** (KEEPER,
CALIBRATED) with its registry sidecar and payload; the refreshed CAISO bench
parts; `keepers/CAISO.json` + `status/CAISO.js`; the CAISO matrix shard
re-stamped (keeper, gates, `import_hub_pricing` evidence); the §5.2 prose
header rewritten in substance; the forecast board's gate-(a) stamp re-keyed;
this finding; the calibration-log entry.

**Next number: caiso-253.**
