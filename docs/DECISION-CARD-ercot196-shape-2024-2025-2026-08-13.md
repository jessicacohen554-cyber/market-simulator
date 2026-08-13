> Status: FOR THE OWNER SITTING — NOTHING IS DECIDED OR EXECUTED HERE.

# DECISION CARD — ercot-196: the 2024/2025 monthly-shape object, sized — what the shape queue can actually buy, and from which physical objects

**Session ercot-196 `[FABLE]`, 2026-08-13, branch
`claude/ercot-scar-shape-charter-1`, assembled at origin/main `5b05f84`.**
This is the measure-first charter assembly for the object card R re-pointed
ERCOT bandwidth to: the outage-season/fuel-shape monthly object named by
`docs/PRECOMMIT-ercot193-soc-regate-2026-08-13.md` §0(c) as *"2024/2025 shape
work for a later charter"*. The card performs exactly ONE new measurement — a
**read-only counterfactual re-scoring and attribution** of the keeper's
registered dashboard payload against committed bench actuals and the
committed hub-hourly actual series, using the rubric's own `_wmean`/`_nrmse`
(`scripts/probes/ercot196_shape_decomposition.py`, output
`results/calibration/ercot196_shape_decomposition.json`; the
ercot-189/ercot-193 footing). Actuals enter counterfactual *scoring and
attribution* only, never any model input (rule 13 `[R-MEASURED]`). No lever
is built, no LP is solved, no year is solved or scored, no run is registered,
the keeper is untouched.

**THE CEILING, STATED FIRST (card R consequence, mandatory):** 2024 C3b =
0.135 and 2025 C3b = 0.096 both already **PASS** (bar ≤ 0.20). This is
SHAPE-QUALITY and forecast-readiness work, never determination work —
**ERCOT's determination stays NOT-YET regardless of anything on this card**,
under the standing rulings **Q-B** (no C3a-2023 spend of any kind, final —
`docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md`)
and **R-A** (NOT-YET stands as the public claim; no C3b-2023-targeted
determination rounds —
`docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md`). 2023
appears on this card only in this ceiling citation.

**What the work can concretely buy** (the reported numbers that move, §3):
C3b-2024 0.135 → ≈ 0.08–0.10 and C3b-2025 0.096 → ≈ 0.05–0.06 at the
measured per-month ceilings; C3a-2025 back from −7.5 % (75 % of its ±10 %
band spent) toward the band centre; and the backcast twin of the forward
lane's measured missing-scarcity-content defect (FFR-6A: 96–100 % of every
fossil margin gap) shrinks where it is reachable.

**Keeper at assembly:** `2026-08-12-run192-arm-coal-peak` — determination
NOT-YET, fail set {C3a-2023, C3b-2023}, C3c ledgered ×3 (58/181, 22/53,
1/31); its registered payload is byte-identically reproduced by the
registered `2026-08-13-ercot193-arm-soc` replay (G-REPRO, 12/12 sidecar
sha256).

---

## 0. THE BOARD

| card | decision | blocking? | recommendation |
|---|---|---|---|
| **T** | Which (if any) of the named 2024/2025 shape options is chartered next, now that the object is sized and attributed? | blocks only the shape-queue sequencing — determination is unaffected by construction | **(T-1) charter the `gas_hh_monthly_shape` input-correctness A/B** (measured HH monthly shape, level-preserving, zero fitted scalars, fit gain NOT predicted — the ercot-145b posture), **with (T-3b)** the small published-adder overlay-completeness audit as its read-only companion; T-0 accepted meanwhile; T-2 stays with the owner (D2 freeze); T-4 refused and recorded |

One signable card. §1–§2 are its evidence; §4 is the option board.

## 1. THE MEASUREMENT — where the 2024 and 2025 residuals live, at full magnitude

From `results/calibration/ercot196_shape_decomposition.json` (rubric
arithmetic; model = the scorer's demand-weighted `pMon`, actual = bench
`rt_lw_mon`). The probe's year-grain tail counts reproduce the C3c ledger
exactly (2024: 53 actual / 22 model max-zonal > $200; 2025: 31 / 1), which
validates its month mapping.

**2024 — NRMSE 0.1352. Pure shape: uniform bias −0.20 $/MWh; removing it
leaves 0.1351.**

| 2024 | Jan | Feb | Mar | **Apr** | **May** | Jun | Jul | **Aug** | Sep | Oct | **Nov** | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model | 36.61 | 14.41 | 19.81 | **33.17** | **49.85** | 34.94 | 26.78 | **35.49** | 27.63 | 29.25 | **26.05** | 26.78 |
| actual | 39.80 | 15.17 | 23.72 | **27.01** | **44.31** | 31.79 | 24.61 | **41.31** | 27.01 | 27.66 | **33.43** | 27.35 |
| resid | −3.19 | −0.76 | −3.91 | **+6.16** | **+5.54** | +3.15 | +2.17 | **−5.82** | +0.62 | +1.59 | **−7.38** | −0.57 |
| sq-share | .051 | .003 | .076 | **.189** | **.153** | .049 | .024 | **.168** | .002 | .013 | **.271** | .002 |

Nov + Apr + Aug + May carry **78.1 %** of the squared monthly residual.
Counterfactual ceilings (that month scored perfect, all else as-is):
Nov → 0.1155; Nov+Apr → 0.0994; Nov+Apr+Aug → **0.0824**.

**2025 — NRMSE 0.0957. Level-dominated: every month is negative, uniform
bias −2.76 $/MWh; removing it leaves 0.0579.**

| 2025 | Jan | **Feb** | Mar | **Apr** | **May** | Jun | Jul | Aug | Sep | Oct | Nov | **Dec** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model | 34.42 | **36.60** | 29.76 | **30.79** | **32.39** | 30.73 | 34.83 | 38.53 | 32.35 | 32.74 | 34.17 | **34.47** |
| actual | 36.01 | **42.48** | 29.84 | **34.94** | **39.67** | 31.29 | 36.07 | 39.30 | 35.00 | 36.01 | 36.44 | **37.90** |
| resid | −1.59 | **−5.88** | −0.08 | **−4.15** | **−7.28** | −0.56 | −1.24 | −0.77 | −2.65 | −3.27 | −2.27 | **−3.43** |
| sq-share | .018 | **.239** | .000 | **.119** | **.367** | .002 | .011 | .004 | .049 | .074 | .036 | **.081** |

May + Feb + Apr carry **72.5 %**. Counterfactual ceilings: May → 0.0762;
May+Feb → 0.0601; May+Feb+Apr → **0.0501**. (The precommit §0(c) naming
"2025 worst April–May" is confirmed on the squared measure — May .367 +
Apr .119 — with February the second-largest single month at .239.)

## 2. THE ATTRIBUTION — measured, from committed artifacts only

**(a) Realized RT scarcity content the LP does not form — Nov-2024, Aug-2024,
and the broad 2025 sub-tail band.** Month-grain placement of the committed
hub-hourly actual series (`actual_lmp_hourly_ERCOT.parquet`, the
`derive_actual_tail.py` basis):

- **Nov-2024 (−7.38, the largest 2024 month):** actual carried 8 RT hours
  > $200 with a **$5.12/MWh** monthly tail wedge (mean − capped mean); the
  model forms 4. Actual RT ran **$7.22 ABOVE DA** for the month — a realized
  real-time volatility month, not a fundamentals month. Most of Nov-2024's
  miss is >$200 tail content.
- **Aug-2024 (−5.82):** actual tail wedge **$7.39** (6 h > $200; model forms
  2) — the wedge alone exceeds the residual, i.e. on capped prices the model
  is slightly OVER in Aug. The monthly miss is entirely missing tail.
- **2025, all months:** actual carried **217 hours > $100** (Dec 31, May 27,
  Apr 25, Jul 23, Feb/Nov 19 each) vs the model's **35**; > $200 is 31 vs 1.
  The tail wedges are modest (May $2.77, Apr $1.98, Feb $0.51), so 2025's
  miss is mostly the **$100–200 moderate-scarcity band plus broadly elevated
  sub-$100 hours** — a level object spread across every month, not an
  Aug-2023-style spike. Not gas level: the keeper's 2025 gas scalar (3.52
  $/MMBtu) is *above* both measured references (HH mean 3.45; EIA N3045TX3
  TX electric-power delivered ≈ 3.06), so the −2.76 $/MWh bias exists
  despite dear model fuel.

This family is physically the SAME object the record has adjudicated
model-class at the extreme tail (the C3c ledger, the ercot-95→163 exhaustion,
card R §2) — λ-led SCED conduct and adder content, here at sub-$200 scale.
FFR-6A measured the identical shape from the forward side (screens price
fossil margins at 0.04–4.4 % of measured, with the missing scarcity content
96–100 % of every gap term), and FINDING-ercot195 measured its third face
(merchant rent is regime/adder-led, ECRS = 50 % of 2023 net revenue).

**(b) The outage-season over-pricing remainder — Apr/May-2024.** The
committed DAM-availability input confirms Mar–May as the maintenance season
(monthly mean availability: COAL 0.61–0.68, CC_REGULAR 0.56–0.72, ST_GAS
0.43–0.56). In those months the model runs **over** (+6.16 / +5.54) *despite*
the actual months carrying $4.77 / $9.21 of > $200 wedge the model only
partly forms — on capped prices the over-read is materially larger than the
headline residual. Class grain (payload `volErr.zoneMon`): Apr-2024
COAL_PRB −0.93 TWh under actual (model substitutes dearer gas at the
margin), May-2024 −0.55. This is the post-repair remainder of the
ercot-166/172 maintenance-season availability object: April-2024 was "+72 %
over" before the ercot-185 fault-3 shaped-partial repair, and is +23 % now.
The lane's remaining faces are all governed: **fault 1 (composition
double-count) FROZEN by signed owner ruling D2**, fault 2 unit-scoping
REJECTED at ercot-174 (`R`), fault 3 repaired and PROMOTED at ercot-185
(`K`).

**(c) The fuel-shape months — measured HH monthly shape vs the generic
climatological shape.** The keeper prices ERCOT gas as one annual scalar
(2024: 2.19, 2025: 3.52 $/MMBtu) × the generic `GAS_MONTHLY_SEASONALITY` ×
the armed measured daily factors (`gas_daily_shape`, mean-preserving per
month) — so the **measured month-to-month commodity shape never enters**.
The wedge (keeper level × (measured HH shape − generic shape)):

- 2024: Jan **+0.65** $/MMBtu model-cheap (Winter Storm Heather month;
  resid −3.19, DA−RT +10.93), Feb **−0.69** / Mar **−0.74** / Apr **−0.42**
  model-dear (the post-Heather collapse the `gas_hh_monthly_shape` docstring
  itself names), Jun +0.50, Dec +0.42.
- 2025: Feb **+0.31** model-cheap (resid −5.88), Mar +0.52 (resid −0.08),
  H2-2025 wedges NEGATIVE (Aug −0.44) — model-dear in exactly the months the
  model already under-reads.

Sign agreement with the monthly residual is **4/12 months in 2024 and 6/12 in
2025**: the wedge supports Jan-2024, Apr-2024 (+6.16 over with −0.42 dear
gas ≈ $3–4/MWh of it at gas-marginal heat rates 7–10) and Feb-2025
(≈ $2–3/MWh of the −5.88), and is adverse in H2-2025 and Mar-2025. **The
measured record therefore supports `gas_hh_monthly_shape` as an input
correctness fix with real reach in named months, and does NOT support it as
a C3b fit lever** — the same honest posture the ercot-145b daily-shape
precommit pre-registered ("a fit gain is NOT predicted").

**(d) A measured scoring-basis wedge — the published-adder overlay is in the
actual but not in the scored model monthly price.** Verified on the keeper's
own sidecars: the scorer's `pMon` equals the demand-weighted energy-only
dual to the cent, while bench `rt_lw_mon` is settlement RTSPP (energy +
published RTORPA/RTORDPA adders). The keeper's own committed overlay is
worth **+0.25 $/MWh (2024) / +0.42 $/MWh (2025)** demand-weighted — and
**+1.50 $/MWh in Feb-2025 alone** (Jan-2025 +0.76, Mar-2025 +0.70), i.e.
~15 % of the 2025 uniform bias and ~25 % of Feb-2025's miss is a
basis-consistency artifact, not model error. The C3c tail already scores on
the settlement basis when the overlay is present (the G-20a owner-approved
convention); the monthly C3b basis does not.

**(e) Ruled out as carriers, from the same tables:** hydro/renewable months
(monthly class deltas for wind/solar/hydro are small in every top residual
month; the largest class deltas are thermal substitutions — Aug-2024 ST_GAS
+1.14 TWh vs CC_REGULAR −1.10 swap); the 2025 gas LEVEL (dear, not cheap —
(a) above); storage shape (monthly net storage discharge rises smoothly
through both years; the SOC re-gate at ercot-193 measured the storage arm
RG-PASS on every gate).

## 3. WHAT THE WORK BUYS — stated concretely, under the ceiling

- **C3b-2024** 0.135 → **0.0824** is the measured three-month ceiling
  (Nov+Apr+Aug perfect). The reachable part: Apr/May's over-read (options
  T-2, part of T-1); Nov/Aug are mostly model-class tail content (T-4,
  refused). A realistic non-tail repair lands ≈ 0.09–0.11.
- **C3b-2025** 0.096 → **0.0579** just by closing the uniform −2.76 $/MWh
  under-read; 0.0501 is the May+Feb+Apr ceiling. The identified reachable
  slices: ~0.42 $/MWh of basis wedge (T-3), ~$2–3/MWh in Feb from fuel shape
  (T-1); the rest is the sub-tail scarcity band (T-4, refused).
- **C3a-2025** −7.5 % (PASS, but 75 % of the ±10 % band is spent) moves
  toward centre with every 2025 slice above — this is the criterion with the
  least margin anywhere in ERCOT's PASS set, and it is protective headroom,
  not determination.
- **Forecast readiness**: the 2025 backcast under-read (217-vs-35 elevated
  hours) is the same physical family FFR-6A/FFR-8A measured as the forward
  screens' missing scarcity content (96–100 % of fossil margin gaps; the
  $100–200 band carries 37–62 % of attainable margin). Backcast slices that
  are honestly reachable (fuel shape, adder basis) transfer to the forward
  lane's price object; the model-class remainder is bounded and named, which
  is itself forecast-readiness information (the L-SCAR V0 lesson).

## 4. CARD T — THE OPTION BOARD

**(T-0) Do nothing — the honest baseline.** Both years already PASS; card R
already re-pointed determination work away. The measured bias it accepts:
2024 shape error concentrated 78 % in four months (worst single month
−7.38 $/MWh, Nov); 2025 a −2.76 $/MWh across-the-board under-read with
C3a-2025 at 75 % of its band and the forward lane inheriting the missing
moderate-scarcity content. Cost: zero. Risk: none to determination; the
stated biases persist in every dashboard and forward read.

**(T-1) The `gas_hh_monthly_shape` input-correctness A/B — RECOMMENDED
next shape charter.** (a) *External driver:* the measured Henry Hub monthly
commodity price (published; forward years keep the generic shape — the
futures-shape analogue — so it regenerates, rule 13). (b) *Admissibility:*
the field exists, built and default-off (`scenarios.py`; byte-identical when
off), is **level-preserving** (hour-weight-normalized so the trusted annual
level is exact — zero fitted scalars, rule 23), and is the record's own
named admissible descendant of the Run-77 rejection: the `G` cells
(`gas_monthly_actuals`, `gas_plant_monthly_pricing`) refused the biased
LEVEL swap and per-plant sparsity, explicitly not the shape
(PRECOMMIT-ercot145 §1b/§6.1). No adjudicated cell is re-tested; the field
carries **no matrix row** (the rule-26c gap ercot-145 §6 surfaced), so the
executing session closes that row gap when it arms the A/B. (c) *Expected
reach, bounded from §2(c):* real in named months (Jan-2024, Apr-2024,
Feb-2025, ≈ $2–4/MWh each at gas-marginal heat rates), adverse in H2-2025
and Mar-2025; net C3b movement in both years genuinely uncertain — **the
charter must carry the ercot-145b posture verbatim: armed on measured-input
correctness, fit gain NOT predicted, promotion on structural faithfulness +
pre-registered guards protecting every PASSing gate (C3a/C3b 2024+2025
bands, G-SHED, G-COAL148), with 2023 moves side-effect-reported under the
card-R ceiling.** (d) *Cost:* one full-span A/B (two solves, ~13 GB-class),
a precommit, and the matrix row — no new code.

**(T-2) The Apr/May-2024 outage-season remainder — OWNER-GATED, not
dispatchable.** (a) *Driver:* the measured CAMPD/DAM outage record already
in the availability construction. (b) *Admissibility:* the object is real
(+6.16/+5.54 over-read, larger capped; §2(b)) but every buildable face is
governed: fault 1 is FROZEN by signed ruling D2, fault 2 is an adjudicated
`R` (ercot-174), fault 3 is repaired and promoted (`K`, ercot-185). The only
route is the owner unfreezing the fault-1 composition lane — this card
supplies the sized evidence (Apr+May = 34 % of 2024's squared residual;
counterfactual C3b-2024 ≈ 0.10 with both perfect) and takes no step.
(c) *Reach:* up to ~0.03–0.04 of C3b-2024. (d) *Cost to this workstream:*
zero unless the owner rules.

**(T-3) The published-adder basis — two separable faces.** **(T-3a)**
Scoring C3b monthly on the settlement basis (model energy + committed
overlay, the C3c/G-20a convention extended to C3b) is a **rubric change —
owner-only**, recorded here as a question with its measured size (+0.25 /
+0.42 $/MWh; Feb-2025 +1.50), not proposed as session work. **(T-3b)**
An **overlay-completeness audit** for the ECRS era — does the committed
RTORPA/RTORDPA overlay capture the full published adder content of
2024/2025 RTSPP? — is admissible read work (published data intake +
comparison; no mechanism, no solve) and is the cheap companion that
determines whether T-3a's wedge is actually larger than the committed
overlay measures. Reach: bounds ≤ ~15 % of the 2025 bias unless the audit
finds the committed overlay incomplete. Cost: small; one data ask
(month-grain published adder series, not currently on disk).

**(T-4) The sub-tail scarcity content (Nov/Aug-2024 tail; the 2025
$100–200 band) — REFUSED, recorded so its absence is a decision.** It is
the largest single carrier in both years (§2(a)) and it is the
Q-B/R-A-closed model-class scarcity-formation object measured at smaller
amplitude: realized RT content formed on conduct the competitive-offer LP
does not represent (measured RTORPA ≈ $1–5 at the 2023 extreme; the same
λ-led family FFR-8A measured as "out of this object's reach by
construction" forward). No formation lever is proposed; the only route that
could ever reach it is card R's R-C program decision (an
equilibrium-conduct layer), which remains out of the calibration lane. Its
measured size here (2024: Nov+Aug ≈ 44 % of squared residual; 2025: most of
the −2.76 bias net of T-1/T-3 slices) is the honest bound on every other
option's reach.

**Recommendation: T-1 chartered next (with T-3b as its read-only
companion), T-0 accepted for everything else, T-2 left with the owner
alongside this card's §2(b) evidence, T-4 refused on the standing rulings.**
No option is executed in this session.

---

## 5. GOVERNANCE — DO-NOT-REDO, fences, and what this session did not touch

**Matrix cells checked before any option was named** (docs/mechanism-testing-matrix.md
§5.1 + the ERCOT shard, at 5b05f84): `gas_monthly_actuals` **G** and
`gas_plant_monthly_pricing` **G** (Run-77 level-swap and per-plant sparsity
refusals — respected; T-1 proposes neither), `gas_daily_shape` **K** (armed;
within-month only), `gas_hub_basis_overlay` **U**, `winter_citygate_daily`
**U**, `dual_fuel_switching` **U**, `gas_coldsnap_derate` **U**,
`winter_fuelsec_posture` **U** (all untested — no verdict disturbed; none
proposed here), `temp_dependent_derate` **R** (owner closure — not
proposed), `cc_nameplate_summer_derate` **U**, `historic_outage_overlay`
**U**, `ercot_dam_availability_coal_event_cap` **K** /
`_gas_event_cap` **K** / `_event_cap_reconciliation` **R** (ercot-173) /
`_event_cap_unit_scoped` **R** (ercot-174) — the two `R` cells are exactly
why T-2 is owner-gated, `ercot_partial_outage_shaped_derate` **K**
(ercot-185), `ordc_scarcity_overlay` **R** (ERCOT-97),
`ercot_rtordpa_overlay` **K** (T-3 reads it, changes nothing),
`maxgen_emergency_tier_pricing` **U**, `storage_measured_anchors` **K**
(re-gate discharged at ercot-193). **`diurnal_price_amplitude` stays `U`
untouched** — it is a cross-ISO audit row and the PRECOMMIT-ercot193 §0(b)
refusal is honored verbatim; nothing here re-adjudicates it. No `R`/`I`/`G`
cell is proposed for re-test; T-1's field has no cell, and the one cited as
its closest adjudication (`gas_monthly_actuals` G) refused a different
object.

**No matrix cell or row is edited by this session** — a card is a read, not
a mechanism test (the ercot-182/ercot-189 precedent); the rule-28 row duty
attaches to the session that arms T-1. No `ScenarioConfig` field is added.
No keeper, backcast-registry, or bench file is touched. Rule 22: ERCOT holds
no `complete`/`final` marker; every artifact read is inside {2023, 2024,
2025}, no year was solved or scored, and 2023 appears only in the ceiling
citation (rulings Q-B, R-A). Rule 13: measured actuals entered counterfactual
re-scoring of committed payloads only. The L-SCAR lane is stopped at V0 and
is not touched (`docs/FINDING-ercot195-lscar-v0-nonidentifiable-2026-08-13.md`);
its finding is cited as evidence only. The frozen composition lane (D2) is
not touched. The ercot-188/E2 P0 bit-identity forfeiture is inherited
unexpired and untouched. New artifacts of this session: the probe, its JSON,
this card, and the calibration-log entry — nothing else.
