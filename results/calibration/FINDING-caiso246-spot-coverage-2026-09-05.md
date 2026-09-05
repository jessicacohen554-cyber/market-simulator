# FINDING — caiso-246: the 2025 hub-overlay COVERAGE GAP was a GATE ARTIFACT, the arm covers Sep–Nov 2025 on the measured daily spot the keeper already prices gas at, EVERY pre-registered gate PASSES, the F923 fallback is retired from the training window (0 reachable months in 36) and D3 closes by consequence — PROMOTED. Three of six post-solve predictions FALSIFIED, reported at full size

**Session caiso-246, solved 2026-09-05 (pre-registered and armed 2026-09-04 by the
first caiso-246 session, which stopped mid-solve after checkpointing 2023; this
session re-solved all three years fresh in ONE invocation).** Branch
`claude/caiso-backcast-calibration-wh2iqt` off `main` `3cdf1ca`. Keeper at open:
**`2026-09-04-caiso-243-b1-f923`** (`caiso243_b1_f923_fallback_guard`, `git_sha
b053e3b8`), NOT-YET, C3a the sole load-bearing FAIL **+3.9 / +12.3 / +14.4 %**.
Pre-registration: `PRECOMMIT-caiso246-spot-coverage-2026-09-04.md` (`4f573fe`,
pushed before the arm was coded and before any LP). No `complete` / `final`
marker; holdout freeze ACTIVE; every read and the one solve stayed inside
2023–2025.

---

## §1 — HEADLINE

**Keeper `2026-09-04-caiso-243-b1-f923` → `2026-09-05-caiso-246-b1-spot`**
(bundle `caiso246_b1_spot_coverage`, run_config `git.sha` `900402b`, clean tree).
Determination **UNCHANGED at NOT-YET**: C1 12/12 free 8/8, C2 / C3b / C4 PASS,
C3c the single ledgered caveat (2023 / 2024; 2025 PASSES at 0 h > $200), C6
attested, C8 PASS, DOF ledger **9 entries / 6 residual, unchanged**. C3a stays
the sole load-bearing FAIL at **+3.9 / +12.3 / +11.4 %** (2025 from +14.4;
no verdict flips in any year). **One bundle, three years, one invocation; NO
control solve spent** (G-CTRL form 2).

**The object** (PRECOMMIT §0.2; queue item C of caiso-244 / caiso-245): the
keeper prices every CAISO gas unit at the measured daily CA-composite citygate
spot (`caiso_citygate_spot_level`, caiso-84) — but a month counted as covered
only where the EIA **N3050CA3 monthly survey** carried a basis row, and EIA
publishes that survey as **NA for 2025-09 / -10 / -11** (evidence committed by
the first session: `data/raw/gas-prices/eia_citygate_CA_monthly.csv` + the
fetched xls). The daily spot the keeper uses has **21 / 22 / 12 prints** in
those months. Under `spot_level` the survey VALUE is never used where prints
exist, so the survey row was a **gate and nothing else** — and the three
months it withheld fell to the F923 plant layer (caiso-242 §5, caiso-243's
object, D3's 55077 own row, the autumn-2025 slab).

**The arm:** `ScenarioConfig.caiso_citygate_spot_coverage` (default off,
backcast-only by construction, requires `spot_level`, CAISO-only per rule 25) —
a month with daily prints of its own is covered; its day series is built
exactly as every other spot-level month (flow-date staircase, +0.46 transport
adder layered as today). **Zero new numbers, zero free parameters** (rule 21):
an already-committed measured series reaches the months a gate keyed to a
DIFFERENT series had excluded it from. Rule 14: measured daily spot over the
F923 gap-fill estimate. Rule 19: one mechanism reaching the months it was
designed for; nothing stacked.

**Structural result, the promotion basis (rule 1 `[R-STRUCT]`, C3a excluded
by pre-registration):** the live solve logs *"hub-basis overlay (CAISO 2025,
daily): 1453 gas generators repriced at the measured hub spot in **12/12**
months"* against the keeper's 9/12 — the F923 nearby-fallback layer, whose
D1/D2 defects caiso-243 repaired, now has **zero reachable months in the
36-month training window**, and plant 55077's own $96.161/MMBtu November row
(defect **D3**, 0.27 TWh of capability) is overwritten by the overlay at
$3.76 — **closed by consequence, not by a cut.**

---

## §2 — GATES, ALL SCORED ARM − KEEPER (`_caiso246_arm_vs_keeper.json`). EVERY ONE PASSES

| gate | registered test | measured | verdict |
|---|---|---|---|
| G-SOURCE | EIA NA cells committed as evidence | `eia_citygate_CA_monthly.csv` rows 2025-09/10/11 = NA (first session, `82c162e`) | PASS |
| G-STRUCT (pre-solve) | gas rows × Sep–Nov-2025 hours ONLY; 0 rows 2023/2024; hourly grain | 1,453 / 1,453 gas rows, 29,277.8 MW, months {9, 10, 11}; **0 cells moved outside Sep–Nov at hourly grain**; 0 non-gas; 0 rows 2023 / 2024 (`_caiso246_coverage_footprint.json`) | PASS |
| G-CTRL form 2 | 2023 / 2024 reproduce the keeper at 0.000 TWh per class and 0.000 $/MWh | class energy max Δ **0.0** TWh both years; lw price Δ **0.0**; zonal price arrays `max_abs_diff` **0.0** | PASS |
| G-INERT | 2025 moves | max class Δ 1.531 TWh | PASS |
| G-C3a envelope | ΔC3a-2025 ∈ [−3.1376, +0.1849]; 2023 / 2024 exactly 0 | **−0.9988** / 0.0 / 0.0 | PASS |
| G-C1 / G-C3b / G-C8 / G-CAVEAT / G-C6 | no scored verdict regresses; ≤ 1 ledgered / 0 protective; C6 attested | verdict identity on every criterion (`differing: {}`); C3c CAVEAT ledgered ×1; C6 PASS | PASS |

Live-solve cross-check of G-STRUCT: 2023 / 2024 overlay lines identical to the
keeper's (1443 / 1448 units, 12/12, winter max 24.75 / 17.80); 2025 **12/12**
(winter max 6.07) where the keeper logged 9/12.

**Promotion rule (PRECOMMIT §4), applied as written:** every named gate
passes; the basis is structural; C3a's verdict is reported and excluded. No
scored gate regressed, so the owner-escalation clause does not fire.

---

## §3 — THE DISPATCH RESPONSE, 2025 (arm − keeper, TWh)

| class | keeper | arm | Δ |
|---|--:|--:|--:|
| CC_REGULAR | 39.377 | 40.844 | **+1.467** |
| import (gross; the pass exports nothing, caiso-244 §3.2) | 41.242 | 39.711 | **−1.531** |
| CC_CHP | 7.595 | 7.615 | +0.020 |
| ST_GAS | 0.095 | 0.120 | +0.025 |
| CT_PEAKER | 0.348 | 0.360 | +0.012 |
| CT_CHP | 1.201 | 1.202 | +0.001 |
| COAL | 0.082 | 0.080 | −0.002 |
| solar / hydro | 52.458 / 21.267 | 52.456 / 21.266 | −0.002 / −0.000 |

Monthly, the whole response sits in the three repriced months: CC_REGULAR
**+447 / +846 / +450 GWh** in Sep / Oct / Nov against import **−444 / −605 /
−425 GWh**. Load-weighted price 2025: **39.361 → 38.362 $/MWh** (actual RT
34.42): C3a-2025 **+14.4 → +11.4 %**, required move −1.498 → **≈ −0.50 $/MWh**.

**Model − actual RT by month, 2025** (keeper → arm): Sep **+5.76 → +2.88**,
Oct **+7.69 → +2.44**, Nov **+3.13 → +0.26**; Dec **+9.20 → +8.60**; Aug
+1.76 → +1.66; Jan −1.04 → −1.14; every other month **0.000**.

---

## §4 — PREDICTIONS, SCORED AGAINST INTEREST (PRECOMMIT §2)

| # | registered | measured | verdict |
|---|---|---|---|
| P-1 | G-STRUCT exact, Sep–Nov 2025 only, 0 rows 2023/2024 | as above (pre-solve) | **HOLDS** |
| P-2 | Nov-2025 cap-weighted CA gas 4.38 → 3.5–3.8 $/MMBtu; 55077 Nov to the same band | 5.5714 → **3.7643**; 55077 96.161 → **3.764** (pre-solve) | **HOLDS** |
| P-3 | ΔC3a-2025 ∈ [−1.0, −0.2]; no verdict flips | **−0.9988**; no flips | **HOLDS — at the edge**: 0.0012 $/MWh inside the lower bound. Reported as such; the window was nearly wrong on the large side |
| P-4 | ΔC3a-2023 = ΔC3a-2024 = 0 exactly | 0.0 / 0.0 | **HOLDS** |
| **P-5** | CC_REGULAR-2025 +0.3–1.0 TWh; imports fall by MORE than CC rises; CT_PEAKER falls | CC **+1.467** (47 % above the window's top); imports −1.531 (that leg holds); CT_PEAKER **+0.012** (rises) | **FALSIFIED on two of three legs** |
| **P-6** | Sep / Oct / Nov slab shrinks ≥ 1.0 each; December moves ≤ 0.3 | −2.88 / −5.25 / −2.86 (that leg holds); **December −0.60** | **FALSIFIED on the December leg** — see §5.1 |
| P-7 | C3c-2025 0 h; C1 12/12 free 8/8; C8 PASS; DOF 9 / 6 unchanged | 0 h; 12/12, 8/8; PASS; 9 / 6 | **HOLDS** |
| **P-8** | import-marginal share 2025 rises ≥ 1 point | 23.01 → 23.62 % (**+0.61**) | **FALSIFIED** |

Pre-solve: 2 / 2 hold. Post-solve: **3 of 6 hold, 3 falsified.** The
falsifications are all on the SIZE and SHAPE of the dispatch response; no gate
depends on any of them and none is argued away below.

---

## §5 — DISCLOSURES AGAINST INTEREST

### §5.1 — December, January and August moved with NO fuel-input change: LP coupling through storage, measured

G-STRUCT was measured at **hourly grain** and found **0 cells moved outside
Sep–Nov 2025** — the gas price array is byte-identical to the keeper's in every
other hour of 2025. Yet the December slab moved −0.60, August −0.10 and January
−0.10, and December CC_REGULAR fell **−180 GWh** (mean 5,086 → 4,843 MW). The
carrier is **storage**: monthly discharge (arm − keeper, GWh) **Jan +43, Aug
+91, Sep −23, Oct −261, Nov −94, Dec +235**, net −8 over the year; hydro is flat
(−0.09 GWh annual, 0.0 in every month). The LP moves battery cycling OUT of the
now-cheaper autumn INTO the adjacent months across the cyclic SOC boundary and
the cycling budget, and the extra December discharge displaces gas at the
margin. **P-6's December leg was written on the premise that December's price
formation is independent of its neighbours' fuel; it is not, by ~$0.6/MWh, and
the December slab (+8.60 remaining) is still not this object** — caiso-245 §3's
reading (a level common to import- and domestic-marginal hours) stands.

### §5.2 — THE FIFTH CONSECUTIVE FAVOURABLE DIRECTION

caiso-241 → -246 have each moved C3a in the helpful direction; PRECOMMIT §0.6
declared it as this session's hazard before any solve. It is a property of
where this lane's defects have sat — every one an over-priced or withheld
domestic gas offer that lets imports win — and it is **never** an argument. The
promotion basis excludes C3a by pre-registration, and the verdict did not flip.

### §5.3 — The dispatch response is LARGER than registered, and CT_PEAKER did not fall

P-5's window (+0.3–1.0 TWh) was set from caiso-243's +0.442 TWh CC response to
a ~$9/MMBtu November correction on 25.5 GW; this arm corrects **three** months
by 0.58 / 1.13 / 1.81 $/MMBtu on the full 29.3 GW and the CC response is
**3.3×** caiso-243's. I under-registered the elasticity of CC_REGULAR to a
whole-fleet repricing; that is recorded as an estimator miss, not re-fitted.
CT_PEAKER rose 0.012 TWh (Oct +14 GWh, Nov +11 GWh): cheaper spot gas makes a
few peaker hours clear that the F923 state mean had priced out. The residual
CT_PEAKER volume miss (caiso-244 §2.2: on-recipe price gap $1.4–3.7 median)
is untouched and remains item F of the queue.

### §5.4 — P-3 held by 0.0012 $/MWh

The registered window's lower bound was −1.0 and the measured move is −0.9988.
It holds, and it is reported as a near-miss on the large side rather than as
confirmation: the price response, like the dispatch response, was larger than
registered.

### §5.5 — Imports still fall by more than CC_REGULAR rises

−1.531 vs +1.467 TWh: the caiso-243 §7.1 displacement signature repeats at
3.2× the size. It lands on the standing north-corridor firm block object
(caiso-244 §3.5 / caiso-245 §6), not on this repair, and nothing here touches
it.

### §5.6 — The first caiso-246 session's partial bundle

The 2026-09-04 session checkpointed only 2023 before stopping. This session
deleted those sidecars (`20a47b5`, merged as #4739) before re-solving so the
solver could not silently keep a stale `class_band_hourly_2023.parquet` (it
skips an existing one), and solved all three years fresh in one invocation.
The fresh 2023 reproduces the keeper at 0.0 MW in every class-hour, as the
first session's checkpoint also would have.

---

## §6 — WHAT THIS DOES NOT DO

The north-corridor firm block (the import LEVEL object; caiso-245 §6 forms
(iv) and the two fitted firm prices), the fuel-invariant-margin flatness
(caiso-242 §3.5), the transport adder on a spot-indexed offer (caiso-244 ask
E), the residual CT_PEAKER volume miss, caiso-238 objects 3/4, the SoCalGas
OFO arm and the DOF-provenance instrument are all untouched. The December
slab (+8.60) and the +12.3 % of 2024 (12/12 covered, so NOT a coverage
object) are the C3a residual now, and neither is a coverage question.

---

## §7 — OWNER ASKS CARRIED

1. **Whether the EIA NA months are back-filled for the other ISOs' lanes**
   where their surveys carry NA (PRECOMMIT §5.1; not measured here, rule 25).
2. **Storage cross-month coupling as a scoring caveat for future P-6-style
   predictions** (§5.1): any month-scoped arm moves adjacent months through
   the cyclic SOC boundary by up to ~$0.6/MWh; register that, don't predict 0.
3. caiso-245 §8 items entire; caiso-244 asks E and F; caiso-243 §9 items 5–7.

---

## §8 — DO-NOT-REDO ADDS

1. **The 2025 overlay coverage gap is CLOSED.** Never re-propose an F923-side
   repair for Sep–Nov 2025; the F923 fallback has 0 reachable months in the
   training window on this keeper.
2. **Never predict a month-scoped fuel arm leaves adjacent months at 0.000**
   (storage coupling, §5.1).
3. **Never quote caiso-243's +0.442 TWh as the CC_REGULAR elasticity to a
   repricing** — it was a one-month, one-zone-pool correction; the whole-fleet
   figure is 1.467 TWh per three months (§5.3).
4. caiso-245 §7, caiso-244 §7 and caiso-243 §10 stand in full.

---

## §9 — DELIVERABLES

`PRECOMMIT-caiso246-spot-coverage-2026-09-04.md` (first session); the
`caiso_citygate_spot_coverage` field, CLI flag, replay override, cache-key
registration, unit test and matrix row + six shard cells (first session,
`82c162e`); `scripts/probes/_caiso246_{coverage_footprint,arm_vs_keeper}.py`
+ artifacts; `scripts/gen_caiso246_attestation.py`; this finding; run
**`2026-09-05-caiso-246-b1-spot`** (**keeper**); the calibration-log entry;
matrix cell `caiso_citygate_spot_coverage` → **K** with the CAISO shard
re-stamped; the forecast board's gate-(a) stamp re-keyed (R-T).

**Next number: caiso-247.**
