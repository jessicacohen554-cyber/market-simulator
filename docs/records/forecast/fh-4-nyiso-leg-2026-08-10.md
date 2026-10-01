# FH-4-NYISO — the NYISO leg of the forward-skill battery (shipped defaults)

**Session.** FH-4-NYISO `[FABLE]`, Wave FH Phase A sibling leg (manager
dispatch, prompt pack `docs/forecast-readiness-prompt-pack-2026-07.md`
§FH-4-NYISO; released by Addendum AI.1). Branch `claude/fh-4-nyiso-leg-iu4l9v`,
off `origin/main` `aa61791e`. **The FH-4 lift is UNCONDITIONAL** (Addendum
AI.1: the AG.2 condition was discharged by the ERCOT leg's step-0 gate PASS at
0.0 %), so this leg carries **no step-0 gate** — the I6 invariant remains as a
**stop-the-line RIDER** on both arms (§1.1). Protocol of record:
`docs/handoffs/fh-4-ercot-leg-2026-08-09.md`, executed for NYISO at **SHIPPED
DEFAULTS** per the dispatch: **no keeper contact, no arming, no tuning.**

**Baseline epoch.** Solved at HEAD `aa61791e` (cold container; `uv sync` +
full `regenerate_clean.py` before any solve). The FFR-9A storage vintage-seed
fix and the FFR-3V renewable vintage-seed fix ride automatically. Two UNGATED
NYISO input repairs also ride in both arms by construction (they are
constants/taxonomy, not flags): the nyiso-132 measured solar CF level
(`RENEWABLE_AVG_CF["NYISO"]["solar"]` = 0.1955, the 2026 Gold Book Table
III-2a identity) and the D-25 gas_st fuel-taxonomy correction. Both are also
embedded in the keeper comparator, so the three-way read is not confounded by
them.

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any solve was launched.
Nothing in §1 changes after. Sections §2+ are filled in order, as produced.
This leg lands NO code change — the Arm K `demand_growth_vintage` wiring
landed at FH-4-ERCOT and is engaged here by the harness arm selection alone.
The one new artifact committed with this prereg is the solve-independent
γ-rider probe `scripts/probes/fh4_nyiso_instrument_date_split.py` (§1.5).*

### 1.1 The I6 rider, as written

**Criterion (the FH-1 §3.3 invariant, applied AS WRITTEN as a rider).** The
I6 over-retirement invariant of `scripts/check_forecast_invariants.py`:
single-year economically-retired capacity as a fraction of prior thermal MW,
cap **0.20** (`Thresholds.econ_retire_frac_cap`), measured per evolution year
from each run's own ledgers, **on BOTH arms**. This is not a gate on the lift
(the lift is unconditional); it is the dispatch's stop-the-line rider:
**FAIL on either arm → the lane STOPS** — that arm's run is registered, the
verdict + numbers are committed, the record goes to the manager, and nothing
further runs. I7 and I12 are reported alongside at full magnitude — they are
the FH-1 signature's other two legs, not the criterion.

**Expectation (to test, never a target).** PASS is expected on both arms: the
committed NYISO capacity-hindcast record (base-2020 plain hindcasts,
`nyiso-2021-2025-realized*` sidecars) shows the model's NYISO exits carried by
the announced/confirmed nuclear channel (Indian Point 3, 1,036 MW model vs
1,012 MW actual) with essentially zero economic-wave content, and the ERCOT
leg's determined-posture probe read I6 PASS at base 2023. Whether that holds
for NYISO at shipped defaults (which, unlike the ERCOT leg, do NOT arm the
unified-lookahead/scarcity-restoration screens) is exactly what the rider
measures, and the criterion is applied as written whatever comes out.

### 1.2 Arm R invocation (declared before solving)

**Shipped-defaults posture, stated.** Unlike the ERCOT leg (which armed
`capacity_screen_unified_lookahead` + `capacity_screen_scarcity_restoration`
BY INVOCATION under the manager's AG.2 arming determination — a determination
scoped to that leg), this leg passes **no arming flags at all**: both screen
fields inherit the shipped default (**OFF**), `retirement_rule` `"pipeline"`
rides the shipped default (D-1), and the capacity-price posture is the
FFR-2E harness default `shipped` — which resolves **NYISO curve-OFF**
(`capacity_market_clearing_by_iso = {PJM, MISO, CAISO, NEISO: True}`, NYISO
deliberately absent, matching production; `scripts/lib/forecast_posture.py`).
NYISO carries **no `ISOConfig.default_scenario_overrides`**, and every
`nyiso_*` keeper-recipe mechanism flag ships `False`
(`nyiso_ordc_measured_step_span`, `nyiso_nyc_rcpf_step_curve`,
`nyiso_seny_rcpf_increment_step`, `nyiso_gas_commitment_bridge`, the zonal
gas-offer anchor and seam-envelope lineage, …), so the arms run **none of the
keeper recipe** — the keeper is the skill COMPARATOR only.

```
uv run python scripts/run_capacity_hindcast.py --iso NYISO \
  --forward-from-base --arm realized --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/nyiso-2023-2025-t1ff-armr-fh4
```

Config cache key **`90c7a76c8e25ee61`**, measured at prereg (gas
`hindcast_realized`, per-solve-year weather, `demand_growth_vintage=null` —
the registered cache-neutral default). Registered ONCE, id
**`nyiso-2023-2025-t1ff-armr-fh4`** (hindcast namespace,
`meta.kind="full_forward"`), regardless of verdict or reads.

### 1.3 Arm K invocation (per protocol §1.3, at this head)

**Arm K posture, resolved at this head** (base 2023): gas
`hindcast_asknown_aeo2023` (nominal 5.48 / 4.34 / 3.80 $/MMBtu vs realized
2.54 / 2.19 / 3.53 — **+116 % / +98 % / +7.6 %**, the ex-ante AEO2023 error
Arm K exists to measure); weather pinned to 2023 for every solve year; demand
growth on the rates **published as of 2023** — the NYISO 2023 Gold Book
(April 2023, Table I-1a Baseline Energy), mid near **0.54 %/yr**, selected by
the arm via the FH-2 §7 / FH-4 `demand_growth_vintage` wiring (vs the live
table's 1.22 %/yr the pre-wiring harness would have leaked). This is the
wiring's **first NYISO-armed solve**; Arm R and every other posture pass the
cache-neutral `None`. Config cache key **`30eedfd2d38e5b92`** at prereg.

```
uv run python scripts/run_capacity_hindcast.py --iso NYISO \
  --forward-from-base --arm asknown --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/nyiso-2023-2025-t1ff-armk-fh4
```

Registered id **`nyiso-2023-2025-t1ff-armk-fh4`**, hindcast namespace,
`meta.kind="full_forward"`, regardless of what the reads show. Runs
sequentially AFTER Arm R (rule 12; one container, years sequential within
each invocation).

### 1.4 The skill reads (the §2.1b metric set), pre-registered

From `scripts/score_crossover.py` run verbatim per arm — no new metric, no
re-derivation: `dispatch_skill.metrics` = **fuelmix, price_mean, price_shape**
(+ `co2` reported) per scored year 2023–2025, each carrying `forecast_err`,
`keeper_backcast_err`, `input_gap = |forecast_err| / |keeper_backcast_err|`.
Keeper comparator: the CURRENT NYISO keeper at this head,
**`2026-08-08-nyiso-132-cf-arm`** (**RE-VERIFIED** in
`frontend/data/backcast/keepers/NYISO.json` at branch time — the dispatch's
"at dispatch" id holds; determination CALIBRATED-WITH-CAVEATS, C3c the lone
ledgered caveat). The scorer reads the keeper's committed `determine()`
records — no solve. The three-way read per metric-year (plan §2.1): keeper
err → Arm R err → Arm K err; the R-vs-keeper spread is the **overlay value**,
the K-vs-R spread the **driver-forecast error**. Both are the program's
deliverable, reported at full magnitude, never targets, never tuned toward.

**Pre-registered directions (to test, never targets):**

* **Arm R price level (`price_mean`)**: UNDERSHOOT (signed negative) expected
  in all three years, with input_gap > 1. The keeper's C3a record is
  +8.8 / +0.8 / −3.4 % and its price level rests on armed conduct/scarcity
  content (zonal gas-offer margin anchor, NYC RCPF, ORDC measured step span,
  SENY increment) plus the backcast's measured delivered-fuel input; the
  shipped forward stack carries none of that, so the bare co-optimized LP
  dual is expected to sit low.
* **Arm R price shape (`price_shape`, monthly NRMSE)**: materially worse than
  the keeper, winter months especially — forward gas is annual Henry Hub plus
  a FLAT NYISO basis adder (`GAS_BASIS_DIFFERENTIAL`), which cannot carry the
  measured winter basis blowouts the backcast's delivered-fuel input carries.
* **Arm K vs Arm R**: price level HIGHER in 2023–2024 (the +116 % / +98 %
  as-known gas vintage), near-converged by 2025 (+7.6 %). **Named in
  advance:** if Arm K's 2023/2024 price errors print SMALLER in magnitude
  than Arm R's, that is the ERCOT leg's error-compensation artifact (a wrong
  driver masking missing conduct content), NOT skill — the reading discipline
  carries over verbatim. Fuel-mix: the expensive as-known gas depresses
  gas-fired energy in 2023–2024 relative to Arm R; NYISO's scoreable classes
  are gas + nuclear + hydro + VRE — there is **no coal** in the window fleet
  (the NY coal fleet exited pre-window), so the ERCOT leg's coal-zero
  headline cannot transfer. Whether an analogous structural zero appears in
  some other class is a read, not a prediction.
* **`co2`** is reported at full magnitude; where the keeper record carries no
  comparable, `input_gap` is null and the forecast error stands alone.
* **Quoting rule.** The lift is unconditional and both arms run the shipped
  posture, so the reads are quotable as T1-FF skill — UNLESS an arm's I6
  rider FAILs, in which case that arm's dispatch numbers are context to the
  stop-the-line report only, and no skill is quoted from it.

### 1.5 The γ rider: instrument-date split of the window's actual exits

**Purpose (AG.2 γ rider, carried by the protocol).** The exit-side skill
number must never be mis-attributed: the T1-FF confirmed-exit channel is
information-gated at `confirmed_registry_as_of = date(vintage, 12-31)` =
**2023-12-31**, so a window exit whose enforceable instrument post-dates the
cutoff is invisible to that channel BY DESIGN.

**Method (solve-independent; committed artifacts only).** The NYISO sibling
probe `scripts/probes/fh4_nyiso_instrument_date_split.py`, committed with
this prereg: the scorer's own target rows
(`data/raw/_validation-source/capacity_actuals_nyiso.csv`,
`kind="retirement"`) matched against the confirmed-exit registry
(`data/raw/confirmed-retirements/nyiso.csv`) on `(plant_id, generator_id)`,
split at the cutoff; reported for the leg's window 2023–2025 AND for
2021–2025 (the scorer's window-unfiltered referent), so the two windows'
numbers are never conflated.

**Registry fact visible at prereg, and the split it forces.** The NYISO
confirmed-exit registry is an **AUDITED ZERO** — zero qualifying rows, with
the audit trail in the file itself (researched 2026-07-05, re-queried
2026-07-31 and 2026-08-03): every NYISO completed deactivation notice in the
candidate set was reversed, withdrawn, or retained on a NYISO reliability
determination (Far Rockaway, Gowanus/Narrows, Pinelawn), and Danskammer is
HELD OUT for want of an unconditional instrument date. The split is therefore
**degenerate by registry content**, and the probe's committed output records
it: instrumented ≤ 2023-12-31 = **0.0 MW**; instrumented after = **0.0 MW**
(unlike ERCOT, where 477 MW acquired a post-cutoff instrument); no-instrument
= **100 %** of the window's actual exits — **578.9 MW** all-fuel / **474.2
MW** thermal in 2023–2025 (oil 328.9, gas_ct 142.9, biomass 60.3, hydro 35.9,
gas_cc 2.4, wind 7.5, storage 1.0), and **1,757.2 MW** all-fuel / **1,647.7
MW** thermal in the scorer's 2021–2025 referent (dominated by Indian Point
3's 1,012 MW April-2021 nuclear exit, which the vintage-2023 fleet basis
predates anyway).

**Attribution, pre-stated.** ZERO MW of the window's actual exits were
knowable-as-confirmed at the vintage cutoff — the confirmed-exit channel can
carry nothing for NYISO by the information gate's own design and the
registry's honest zero. The exit-side rows on these arms therefore measure
the **economic/announced channel only**, and must not be read as the
confirmed-exit mechanism failing; equally they must not be excused — whether
the economic screen should anticipate unconfirmed exits of this kind is the
FFR retirement lane's question, untouched here.

### 1.6 Governance

* Holdout freeze ACTIVE (steady state) — read at launch by the harness and
  recorded in `meta.json`; this leg stays legal under it: solve years
  {2023, 2024, 2025} — training-tier only (2022 auto-bridged, evolved but
  never solved, its data never read); no out-of-training backcast year
  solved/scored/registered; no measured H1-2026 contact anywhere; scoring
  never leaves 2023–2025 (the scorer refuses both bounds).
* Hindcast namespace ONLY — never the backcast registry, never
  `frontend/data/forecast/` committed inputs. No keeper contact, no
  promotion, no shipped-default flip, no matrix cell verdict beyond
  measurement citations. Bar re-levels, signal scaling, tuning toward any
  residual: refused by name.
* ≤5 solve-years per invocation; years sequential within an invocation;
  invocations sequential in this container (rule 12).
* Registration commitment: every solved run registers REGARDLESS of verdict
  or reads. Commit order: prereg → I6 rider verdicts → results → handoff, as
  they exist.
* The other sibling ISO legs and FH-5 are NOT this session's (FH-5 dispatches
  only after the full battery); re-litigating the lift is refused (the
  determination is the manager's record).
* Rule 27: Fable; edits are local on-disk bytes; any push touching a
  ≥300-line file is blob-verified; no new workflows.

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*

## 2. THE I6 RIDER — **PASS on both arms**; the lane proceeds

Both arms ran exactly as pre-registered, at shipped defaults, on the full
clean regeneration (50/50 datatypes, zero failures). Both runtime cache keys
equal their prereg-measured config keys — no config drift between prereg and
solve: Arm R `90c7a76c8e25ee61`, Arm K `30eedfd2d38e5b92`. Both metas record
solved `[2023, 2024, 2025]`, bridged `[]`, `leakage_violations: []`, freeze
ACTIVE and read at launch, both screen fields `false` (shipped),
`retirement_rule="pipeline"` via the shipped default,
`capacity_clearing_posture="shipped"` (NYISO resolves curve-OFF). Arm K's
meta additionally records the full as-known posture: gas
`hindcast_asknown_aeo2023`, `weather_posture="base_year"`,
`demand_growth_vintage: 2023` — the FH-2 §7 wiring's first NYISO-armed solve
(2024/25 demand grown at the cited as-of-2023 Gold Book 0.54 %/yr).

**The I6 criterion, applied as written — PASS in every year, on both arms:**

| Year | Prior thermal | Econ retired (R) | Econ retired (K) | I6 fraction |
|---|---|---|---|---|
| 2023 | 30.24 GW | 0.00 GW | 0.00 GW | **0.0 %** |
| 2024 | 30.24 GW | 0.00 GW | 0.00 GW | **0.0 %** |
| 2025 | 30.24 GW (R) / 30.52 GW (K) | 0.00 GW | 0.00 GW | **0.0 %** |

Total exits of ANY reason are 8.0 MW in both arms (one announced biomass
plant, 54782, 2025) — no economic wave forms in NYISO at shipped defaults,
without the ERCOT leg's unified-lookahead/scarcity-restoration arming. The
stop-the-line rider does not fire; both arms' reads are quotable (§1.4
quoting rule).

**Reported alongside at full magnitude (not the criterion):**

* **I7 FAIL on both arms** — the reliability-floor invariant finds the
  accredited firm fleet short of the requirement: Arm R 2023 32,441 vs
  32,612 MW (−171 MW) and 2025 32,729 vs 34,395 MW (−1,666 MW, the realized
  2025 peak 31,857 MW); Arm K 2023 −171 MW and 2024 32,702 vs 32,789 MW
  (−87 MW). This is a SHORTFALL invariant, not an over-retirement one — the
  vintage-2023 fleet plus the pipeline is simply short of the requirement in
  those years, and the model's reserve-margin backstop responds (below).
* **I12 WARN on both arms**, low side: Arm R reserve margin 2023 7.4 % /
  2025 2.7 % vs the requirement-implied floor band [8.0 %, 23.0 %]; Arm K
  2023 7.4 % / 2024 7.7 % (its 2025 sits at the band edge — base-2023
  weather and 0.54 %/yr growth give Arm K a much lower 2025 peak, 30,533 vs
  Arm R's realized 31,857 MW).
* The reserve-margin backstop (step 6) built gas_ct: Arm R 274.8 MW in
  2025; Arm K 274.8 MW in 2024 + 251.9 MW in 2025 — the arms' different
  demand paths shift its timing. Planned additions: 36.0 MW gas_ct (2025,
  vintage-2023 proposed sheet) in both arms.
* 14 checks per arm: 1 FAIL (I7), 1 WARN (I12), all else PASS — I1 energy
  balance closes to 1e-9 MW, I8 planned-additions gating clean, I13 no
  cobweb.

Both runs registered regardless of reads: **`nyiso-2023-2025-t1ff-armr-fh4`**
+ **`nyiso-2023-2025-t1ff-armk-fh4`**, hindcast namespace
(`frontend/data/hindcast/<id>.json`, `meta.kind="full_forward"`), never the
backcast registry.

## 3. Skill reads — the three-way table

Scored by `score_crossover.py` verbatim against the committed bench and the
CURRENT keeper **`2026-08-08-nyiso-132-cf-arm`**, per the prereg (§1.4).
Quotable as T1-FF skill: the lift is unconditional and both arms ran the
shipped posture with I6 PASS. Errors at full magnitude; `gap` = input_gap =
|arm err| / |keeper err|. Keeper → Arm R spread = **overlay value**; Arm R →
Arm K spread = **driver-forecast error**.

**price_mean** (fraction of actual, signed = model − actual; keeper signed
values are its C3a record +8.8 % / +0.8 % / −3.4 %):

| Year | Keeper err | Arm R err (gap) | Arm K err (gap) |
|---|---|---|---|
| 2023 | 0.088 | **+0.134** (1.52) | **+0.800** (9.12) |
| 2024 | 0.007 | **−0.092** (12.97) | **+0.305** (43.0) |
| 2025 | 0.035 | **−0.328** (9.50) | **−0.312** (9.04) |

**price_shape** (monthly NRMSE): keeper 0.130 / 0.172 / 0.155; Arm R 0.214
(1.65) / 0.285 (1.66) / 0.467 (3.01); Arm K 0.817 (6.29) / 0.413 (2.40) /
0.467 (3.01). (The two arms' 2025 NRMSE coincide at the artifact's stored
3-dp precision on genuinely different solves — their 2025 mean-LMP errors
differ, −32.8 % vs −31.2 %.)

**fuelmix** (TWh Σ|Δ| over scoreable classes): keeper 7.68 / 3.30; Arm R
27.26 (3.55) / 26.07 (7.89); Arm K 32.38 (4.22) / 34.44 (10.43). **2025 is
UNSCOREABLE for NYISO fuel-mix** (the preliminary EIA-923 vintage leaves all
five gas classes incomplete, so the scorer skips the year and the gas_twh
family row is reported-not-banded — unlike ERCOT, where the coal classes
remained scoreable).

**co2** (fraction, reported — keeper record carries no comparable): Arm R
−16.3 / −13.5 / −24.8 %; Arm K −29.2 / −31.2 / −30.6 %.

**Reading, honestly:**

1. **The overlay value is largest exactly where the market was tightest —
   2025 is the headline.** The keeper holds 2025 to −3.4 % on its armed
   conduct/scarcity content; the shipped forward stack reads **−32.8 %**
   (Arm R). 2024: −9.2 % vs +0.7 %. The keeper→R spread is ~10–30 pp of
   price level, and it is the measured price of everything the forecast
   stack does not carry: the measured delivered-fuel overlays AND the
   default-off NYISO conduct/scarcity recipe (gas-offer anchors, RCPF,
   measured ORDC span, commitment content).
2. **One pre-registered direction is REFUTED, on the record: Arm R
   OVERSHOOTS 2023 (+13.4 %), against the registered
   undershoot-in-all-years direction.** The 2024/2025 undershoots and the
   shape direction held. The overshoot year is the mild one — the forward
   stack's flat annual delivered-gas construction (HH + $0.55) and its
   missing conduct content push in opposite directions, and in 2023 the net
   sign is positive; the residual attribution (basis-year vs conduct) is a
   diagnosis for the fuel/conduct lanes, not this leg's, and nothing here
   was tuned (rule 1).
3. **The ERCOT error-compensation artifact did NOT materialize in NYISO —
   the as-known driver error passes straight through.** Arm K is worse than
   Arm R on every 2023/2024 read: +116 % as-known gas takes the 2023 price
   from +13.4 % to **+80.0 %** and 2024 from −9.2 % to +30.5 %. Because Arm
   R's 2023 error is already positive, the expensive as-known vintage
   amplifies rather than masks — there is no NYISO analogue of the ERCOT
   2023 gap-below-1 artifact, and no gap below 1 anywhere in this table.
   The pre-registered K-higher-in-2023/24 direction held; the 2025
   driver-spread near-convergence held too (−31.2 vs −32.8 % — the +7.6 %
   gas vintage moves the year less than 2 pp), which isolates the 2025 miss
   as structural (overlay side), not driver side.
4. **The dominant structural mix finding (the NYISO analogue of the ERCOT
   coal-zero): ST_GAS collapse + CC_CHP over-run — an intra-gas allocation
   failure, not a cross-fuel one.** In both arms the downstate steam-gas
   fleet barely runs (Arm R 1.49 / 1.94 TWh vs actual 8.70 / 11.07 in
   2023/2024) while CC_CHP over-runs ~2× its actual (21.0 / 21.7 vs 11.3 /
   13.5) and CC_REGULAR sits under (27.2 / 31.2 vs 35.3 / 38.0). Total
   gas-fired energy is much closer (Arm R 2023: 50.7 vs 58.5 TWh) than its
   allocation. In the keeper, ST_GAS is carried by the reliability floor +
   commitment/conduct content — all default-off here; nothing was armed to
   fix it (rule 1; the mechanisms exist and are the keeper lane's, their
   forecast-default adjudication is not this leg's).
5. **Fuel-mix moved WITH the as-known gas error as pre-registered, and that
   worsened it**: Arm K's expensive gas pushes every gas class down
   (CC_REGULAR 27.2 → 20.6 TWh in 2023), but CC_REGULAR was already under
   its actual, so Σ|Δ| rises (26.1 → 34.4 in 2024). A correctly-signed
   driver response over a mis-allocated base is still a worse forecast —
   reported as such.
6. **Exit side (with §4's rider attached):** both arms retire 8 MW
   (announced biomass) against the scorer's window-unfiltered 1.711 GW
   actual (2021–2025, thermal+biomass; the leg's own 2023–2025 window holds
   0.535 GW on that family set) — the under-side FAIL row
   (`err_frac −0.995`), with `false_retire` 0.0 GW PASS on both arms. Zero
   MW of the actual exits were confirmed-knowable at the vintage cutoff
   (§4), and 1.012 GW of the 1.711 is Indian Point 3, which exited in April
   2021 — before this leg's vintage-2023 fleet basis even begins.
7. **Entry side (reported; the FFR-4/5/9 lanes' object):** decision-basis
   additions Arm R 3.59 GW / Arm K 3.84 GW vs 3.375 GW actual — the total
   is close but the composition is not: solar 1.275 vs 2.197 GW (−42 %, the
   FFR-9B under-build signature in NYISO), a phantom 1.0 GW gas_cc (actual
   0.0), storage 0.0 vs 0.184 GW, wind 1.00 vs 0.89 GW (PASS), gas_ct
   0.31 (R) / 0.56 (K) vs 0.072 GW — the gas_ct excess including the
   reserve-margin backstop builds.

## 4. The γ rider — instrument-date split

Computed by `scripts/probes/fh4_nyiso_instrument_date_split.py` from the
committed artifacts only (§1.5 method), solve-independent; the probe and its
numbers were committed with the prereg, before either arm ran.

| Window | Actual exits (all) | Instrumented ≤ 2023-12-31 | Instrumented after | No instrument in registry |
|---|---|---|---|---|
| 2023–2025 (the leg's) | 578.9 MW | **0.0 MW** | 0.0 MW | 578.9 MW |
| 2021–2025 (the scorer's referent) | 1,757.2 MW | **0.0 MW** | 0.0 MW | 1,757.2 MW |

The registry is an audited zero (0 rows), so the split is degenerate exactly
as pre-stated: unlike ERCOT (where 477 MW acquired a post-cutoff
instrument), NOT ONE MW of NYISO's window exits ever acquired an enforceable
instrument — every candidate deactivation was reversed, withdrawn, or
retained by a reliability determination. **Attribution:** the exit-side FAIL
rows on these arms measure the economic/announced channel against exits that
were not confirmed-knowable at the base date (or, for Indian Point 3,
pre-date the fleet basis); they must not be read as the confirmed-exit
mechanism failing, and equally must not be excused — whether the economic
screen should anticipate unconfirmed exits remains the FFR retirement lane's
question, untouched here.

## 5. Governance close-out

* **Rule 22.** Solves were {2023, 2024, 2025} in both arms — training tier
  only; freeze ACTIVE and read at launch (recorded in both metas); no
  out-of-training year solved/scored/registered; no measured H1-2026
  contact; the scorer's bounds refused nothing because nothing out-of-bounds
  was asked.
* **Rules 1/13/14.** Nothing tuned toward any residual: the 2023 overshoot
  (a refuted prereg direction), the ST_GAS/CC_CHP allocation finding, the
  I7 FAILs, the exit-side under-miss, and the solar entry shortfall are all
  reported at full magnitude and left standing. No bar re-level, no signal
  scaling, no default flip, no keeper contact, no arming.
* **Rule 28, duty (b) — citations only.** The `demand_growth_vintage`
  fc-NYISO cell moves U → O with the Arm K measurement citation
  (measured-not-adjudicated; no shipped default reads the vintage table).
  The two capacity-screen rows are NOT touched — this leg ran them at their
  shipped OFF defaults and measured nothing about them (unlike the ERCOT
  leg, whose arming was by that leg's manager determination). No verdict
  cell moved anywhere.
* **Rule 27.** Fable; all edits local on-disk bytes; blob verification after
  any push touching a ≥300-line file; no new workflows; no `push_files` for
  ≥300-line files.
* **Registration.** Both runs registered regardless of reads:
  `nyiso-2023-2025-t1ff-armr-fh4` + `nyiso-2023-2025-t1ff-armk-fh4`,
  hindcast namespace only; the backcast registry and
  `frontend/data/forecast/` committed inputs are untouched (the register's
  reindex writes only the gitignored generated namespace).
* **Cost note for the remaining sibling legs** (manager's planning): each
  3-solve-year NYISO arm ran ~6–7 min wall on this 15 GB / 4-core container
  (P0 ~80–110 s, P1 ~25–56 s per year), cold at the 2026-08-10 head after a
  ~66-min `regenerate_clean.py`.
