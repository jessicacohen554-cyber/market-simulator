# FH-4-NEISO — the NEISO leg of the FH-4 forward-skill battery

**Session.** FH-4-NEISO `[FABLE]`, Wave FH Phase A (manager dispatch pack §0ag,
the five sibling legs RELEASED). Branch `claude/fh-4-neiso-leg-j42x61`, off
`origin/main` `aa61791e`. The FH-4 lift is **UNCONDITIONAL** (Addendum AI.1:
the ERCOT step-0 gate PASSED at 0.0 %/0.0 %/0.0 % vs the 26.8 % FAIL
reference), so this leg carries **no step-0 gate** — the I6 invariant rides as
a stop-the-line check on both arms instead (§1.1). Protocol of record:
`docs/handoffs/fh-4-ercot-leg-2026-08-09.md`, executed for NEISO at **SHIPPED
DEFAULTS** — no keeper contact, no arming, no tuning. Standing NEISO gas-basis
facts (neiso-86) noted and untouched: the window is 2023–2025; nothing here
re-opens the 2018-era basis.

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any solve was launched.
Nothing in §1 changes after. Sections §2+ are filled in order, as produced.
This leg lands NO code change — the Arm K `demand_growth_vintage` wiring
(protocol §1.3) is already at HEAD from the ERCOT leg; the only new file
committed with this prereg is the solve-independent γ-rider probe
`scripts/probes/fh4_instrument_date_split_neiso.py`.*

### 1.1 The I6 rider, as written (this leg's stop-the-line check)

**Criterion (dispatch step 3, applied AS WRITTEN).** The I6 over-retirement
invariant of `scripts/check_forecast_invariants.py`: single-year
economically-retired capacity as a fraction of prior thermal MW, cap **0.20**
(`Thresholds.econ_retire_frac_cap`), measured per evolution year from each
run's own ledgers (at `<out-dir>/NEISO/<runtime-key>/`).

**Verdict rule.** Each arm's registered invariant battery must read **I6 =
PASS**. An I6 FAIL on either arm is a **stop-the-line report to the manager**:
the run is still registered, the verdict + numbers are committed, and **no
skill number is quoted from a failed-I6 leg**. All other invariants (I7, I12
included) are reported alongside at full magnitude — they are context, not the
criterion.

**Expectation (to test, never a target).** PASS is expected on both arms: the
FH-1 I6 FAIL signature was measured on ERCOT at the pre-fix posture, the
re-based posture read I6 PASS on every subsequent ERCOT arm, and no
NEISO-specific over-retirement signature is on record. NEISO is untested on
the T1-FF surface — these are the first NEISO full-forward runs — so the
rider is applied as written whatever comes out.

### 1.2 Arm R invocation (declared before solving)

SHIPPED DEFAULTS throughout: no capacity-screen flags (the §0ag shared
protocol — the ERCOT-only scarcity restoration cannot and does not arm, rule
25 `[R-ISO-SCOPE]`; `capacity_screen_unified_lookahead` and
`capacity_screen_scarcity_restoration` both resolve **False**, verified in the
prereg config build), `retirement_rule="pipeline"` via the shipped default,
`confirmed_exits_enabled=True` (default-on) with
`confirmed_registry_as_of = 2023-12-31`.

```
uv run python scripts/run_capacity_hindcast.py --iso NEISO \
  --forward-from-base --arm realized --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/neiso-2023-2025-t1ff-armr-fh4
```

Posture resolved at prereg (config cache key **`a2c8e092ed5ec930`**): gas
`hindcast_realized` (annual Henry Hub 2.54 / 2.19 / 3.53 $/MMBtu for
2023/24/25), per-solve-year weather (`crossover_solve_year_weather=True`, so
the demand-growth table never binds — `demand_growth_vintage=None`),
`mode="forecast"`. Registered id `neiso-2023-2025-t1ff-armr-fh4`, hindcast
namespace, `meta.kind="full_forward"`, regardless of verdict or reads.

### 1.3 Arm K invocation (declared before solving)

The protocol-§1.3 wiring (landed by the ERCOT leg, already at HEAD — nothing
armed here): `--arm asknown` at base 2023 sets
`demand_growth_vintage = 2023`, fail-closed, alongside its gas path.

```
uv run python scripts/run_capacity_hindcast.py --iso NEISO \
  --forward-from-base --arm asknown --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/neiso-2023-2025-t1ff-armk-fh4
```

Posture resolved at prereg (config cache key **`1c7271f2927c6542`**): gas
`hindcast_asknown_aeo2023` (nominal 5.48 / 4.34 / 3.80 $/MMBtu vs realized
2.54 / 2.19 / 3.53 — **+116 % / +98 % / +7.6 %**, the ex-ante AEO2023 error
Arm K exists to measure; Henry Hub is ISO-agnostic, and the NEISO basis rides
identically in both arms so it nets out of the K-vs-R spread); weather pinned
to 2023 for every solve year (`crossover_solve_year_weather=False`); demand
growth for 2024/25 at the **as-of-2023 ISO-NE CELT rate 2.03 %/yr** (2023
CELT, May 2023, Table 1.5.2: 122,057 GWh (2023) → 140,481 (2030)).
**Direction note, stated at prereg:** unlike ERCOT (live 8.5 %/yr vs as-known
2.433 %/yr), the NEISO as-known vintage grows FASTER than the live table's
1.3 %/yr near — the 2023 CELT expected growth that did not materialize
(ISO-NE 2026 CELT records 2025 net energy 116,679 GWh, BELOW the 2023 CELT's
122,057 GWh 2023 starting point) — so the vintage wiring pushes Arm K demand
UP against actuals in 2024/25, compounding the +98 % 2024 gas vintage on the
price side. Registered id `neiso-2023-2025-t1ff-armk-fh4`, hindcast
namespace, `meta.kind="full_forward"`, regardless of reads. Sequential after
Arm R (rule 12; 15 GB / 4-core container).

### 1.4 The skill reads (the §2.1b metric set), pre-registered

From `scripts/score_crossover.py` run verbatim per arm — no new metric, no
re-derivation: `dispatch_skill.metrics` = **fuelmix, price_mean, price_shape**
(+ `co2` reported) per scored year 2023–2025, each carrying `forecast_err`,
`keeper_backcast_err`, `input_gap = |forecast_err| / |keeper_backcast_err|`.
Keeper comparator: the CURRENT NEISO keeper at this head,
**`2026-08-06-neiso-87-control`** (**RE-VERIFIED** in
`frontend/data/backcast/keepers/NEISO.json` — the dispatch's "at this
writing" id holds; determination CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered
C3c caveat). The three-way read per metric-year (plan §2.1): keeper err →
Arm R err → Arm K err; the R-vs-keeper spread is the **overlay value**, the
K-vs-R spread the **driver-forecast error**. Both are the program's
deliverable, reported at full magnitude, never targets, never tuned toward.

**Pre-registered directions (to test, never targets):**

* **Arm R**: first NEISO T1-FF read — no defect reference and no
  pre-registered magnitude. Directions: input_gaps expected materially above
  1 everywhere (the forward stack loses the keeper's measured-overlay
  content: CAMPD outage windows, F923 delivered fuel, same-year CEMS rates,
  weather pinning); the keeper's ledgered C3c model-class limitation (0
  model hours > $300/MWh) carries to both arms a fortiori — no scarcity tail
  is expected to form in any lane, and NEISO's forward capacity-market
  footing carries no ORDC overlay (ERCOT-only, rule 25). Winter price_shape
  months are the expected locus of shape error (the keeper's known
  winter-scarcity family).
* **Arm K vs Arm R**: price errors expected HIGHER (shifted upward) in
  2023–2024 (+116 % / +98 % as-known gas on a gas-marginal system, plus the
  §1.3 demand-vintage push) and near-converged by 2025 (+7.6 % gas, though
  the demand push remains); fuel-mix expected to shift against gas in
  2023–2024, but with materially LESS switching headroom than ERCOT — NEISO
  carries ~0.4 GW of coal and no large non-gas thermal reserve, so the
  expected margin movers are oil/dual-fuel units and the fixed-profile
  import/nuclear base, and the K-vs-R fuelmix spread is expected SMALLER
  than ERCOT's. Directions only; the measured spread IS the result.
* **Quoting rule.** These reads are quoted as T1-FF skill ONLY if both arms
  ran the pre-registered posture and the arm's I6 rider PASSED (§1.1).
  Otherwise they are rider context only.

### 1.5 The γ rider: instrument-date split of the window's actual exits

**Purpose (AG.2 γ rider, carried by every leg).** The exit-side skill number
must never be mis-attributed: the T1-FF confirmed-exit channel is
information-gated at `confirmed_registry_as_of = date(vintage, 12-31)` =
**2023-12-31**, so a window exit whose enforceable instrument post-dates the
cutoff is invisible to that channel BY DESIGN — the information gate working,
not a screen miss.

**Method (solve-independent; computed from committed artifacts only).**
`scripts/probes/fh4_instrument_date_split_neiso.py` (committed with this
prereg, the ERCOT probe's construction verbatim with NEISO paths): take the
scorer's own target rows
(`data/raw/_validation-source/capacity_actuals_neiso.csv`,
`kind="retirement"`) for the leg's window 2023–2025; match
`(plant_id, generator_id)` against the confirmed-exit registry
`data/raw/confirmed-retirements/neiso.csv`; split the actual MW into
instrument-dated **≤ 2023-12-31** vs **after / no instrument**. Also reported
for 2021–2025 — the scorer's own unfiltered referent window
(`score_capacity_hindcast.score_retirements` reads the ENTIRE actuals file,
never the bundle's window; protocol §5).

**The split, computed AT PREREG (probe run before either arm solved):**

| Window | Actual exits (all) | Thermal | Instrumented ≤ cutoff | Instrumented after | No instrument in registry |
|---|---|---|---|---|---|
| 2023–2025 (the leg's) | 1,402.1 MW | 1,360.7 MW | **0.0 MW** | 345.6 MW | 1,056.5 MW |
| 2021–2025 (the scorer's referent) | 3,273.9 MW | 2,991.5 MW | **0.0 MW** | 345.6 MW | 2,928.3 MW |

Registry facts visible at prereg, stated for honesty: the NEISO registry
carries exactly two rows — Merrimack 1/2 (plant 2364), instrument the 2024
Clean Water Act consent decree dated **2024-03-29**, exit deadline 2028-06 —
both post-cutoff, and only Merrimack 2 (345.6 MW coal, physical cessation
2025) appears in the actuals window at all. ZERO MW of the window's actual
exits were confirmed-knowable at the vintage cutoff, so both arms' exit-side
rows measure the economic/announced channel only. The full attribution
narrative follows in §5 after the arms run.

### 1.6 Governance

* Holdout freeze read at launch by the harness (recorded in `meta.json`);
  solve years {2023, 2024, 2025} — training-tier only; no out-of-training
  backcast year solved/scored/registered; no measured H1-2026 contact
  anywhere; scoring never leaves 2023–2025 (the scorer refuses both bounds).
* Hindcast namespace ONLY — never the backcast registry, never
  `frontend/data/forecast/`. No keeper contact, no promotion, no shipped
  default flip, no matrix cell verdict beyond measurement citations. Bar
  re-levels, signal scaling, tuning toward any residual: refused by name.
  The NEISO keeper's open items (the P2 replay escalation, the stale-Aug-2025
  basis defect (i), the site-retention state) are the comparator's record —
  read, not acted on.
* ≤5 solve-years per invocation (3 here); years sequential within an
  invocation; invocations sequential in this container (15 GB / 4 cores).
* Registration commitment: every solved run registers REGARDLESS of verdict
  or reads. Commit order: prereg → rider verdicts → results → handoff, as
  they exist.
* The other sibling ISO legs and FH-5 are NOT this session's; re-litigating
  the lift is refused (the determination is the manager's record, Addendum
  AI.1).

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*

## 2. The I6 rider — **PASS on both arms** (skill quotable), with the wave reported at full magnitude

Both arms ran exactly as pre-registered (§1.2/§1.3), registered
`neiso-2023-2025-t1ff-armr-fh4` (runtime `cache_key=326cbab45b586c72`) and
`neiso-2023-2025-t1ff-armk-fh4` (runtime `cache_key=424eff2528407772`),
hindcast namespace, `kind="full_forward"`, solved `[2023, 2024, 2025]`,
bridged `[]`, `leakage_violations: []`, holdout freeze ACTIVE and read at
launch in both metas.

**The I6 criterion, applied as written — PASS in every year of both arms:**

| Year | Prior thermal | Arm R econ retired (I6 frac) | Arm K econ retired (I6 frac) |
|---|---|---|---|
| 2023 | 26.4 GW | 0.00 GW (**0.0 %**) | 0.00 GW (**0.0 %**) |
| 2024 | 26.4 GW | 4.72 GW (**17.9 %**) | 4.70 GW (**17.8 %**) |
| 2025 | 21.7 GW | 0.00 GW (**0.0 %**) | 0.00 GW (**0.0 %**) |

Full batteries: **Arm R 12 PASS / 1 FAIL / 1 WARN** — I6 PASS; **I7 FAIL**
(2025: accredited firm 25,549 < requirement 25,962 MW — the wave's fleet
minus entry leaves the floor breached by 413 MW); **I12 WARN** (2023 reserve
margin 28.7 % above the [0.2 %, 15.2 %] requirement-implied band, 2025
−1.3 % below it). **Arm K 13 PASS / 0 FAIL / 1 WARN** — I6 PASS, **I7
PASS** (floor held; 2025 margin +4.4 %), I12 WARN (2023 high side only).
The R-vs-K I7 split is the demand posture: Arm K's base-year-grown 2025
demand/peak sits below Arm R's realized-2025 construction.

**Reported at full magnitude, not the criterion:** the 2024 evolution step
executes a **4.7 GW gas_cc/gas_st economic wave in BOTH arms** (Arm R
4,720.1 MW = gas_cc 4,267.9 + gas_st 452.2; Arm K 4,704.6 MW = gas_cc
4,267.9 + gas_st 436.7; 53 tranches over 29 plants spanning
Central/Boston/Connecticut/North, largest plants 55170 638 MW, 55211
524 MW, 55068 456 MW) — 17.9 % of prior thermal, 2.1 points UNDER the 20 %
cap, against total actual 2023–2025 exits of 1.40 GW (§1.5). I6 as written
PASSES and the skill reads are quotable per §1.1; the wave itself is an
exit-side over-retirement reported in §4(5). It is nearly **arm-insensitive**
(4,720 vs 4,705 MW under a 2.2× gas-price difference): the 2023-priced
pro-forma margin the 2024 screen consumes moves revenue and fuel cost
together for gas units, so the decision is driver-robust — a structural
screen-level property, not a driver artifact.

## 3. Arm K — solved clean at the pre-registered posture

Meta records the full as-known posture: gas `hindcast_asknown_aeo2023`,
`weather_posture="base_year"` (2023 pinned for all three solve years),
`demand_growth_vintage: 2023` — the FH-2 §7 wiring's first NEISO armed
solve. The vintage table demonstrably bound: Arm K zone-sum demand reads
112.0 → 114.3 → 116.6 TWh, exactly ×1.0203/yr from the 2023 base (the cited
as-of-2023 CELT rate), vs Arm R's realized-weather 112.0 → 114.1 → 115.3.
Both capacity screens confirmed unarmed (shipped defaults) in both metas;
`retirement_rule="pipeline"` via the shipped default.

## 4. Skill reads — the three-way table

Scored by `score_crossover.py` verbatim against the committed bench and the
CURRENT keeper `2026-08-06-neiso-87-control`, per the prereg (§1.4).
Quotable as T1-FF skill: both arms ran the pre-registered posture and both
I6 riders PASSED. Errors at full magnitude; `gap` = input_gap = |arm err| /
|keeper err|. Keeper → Arm R spread = **overlay value**; Arm R → Arm K
spread = **driver-forecast error**.

**price_mean** (fraction of actual, signed = model − actual):

| Year | Keeper err | Arm R err (gap) | Arm K err (gap) |
|---|---|---|---|
| 2023 | +0.035 | **+0.065** (1.85) | **+0.607** (17.38) |
| 2024 | +0.057 | **+0.012** (0.21) | **+0.337** (5.88) |
| 2025 | +0.025 | **−0.231** (9.19) | **−0.245** (9.77) |

**price_shape** (monthly NRMSE): keeper 0.086 / 0.159 / 0.058; Arm R 0.295
(3.43) / 0.387 (2.43) / 0.577 (9.95); Arm K 0.660 (7.67) / 0.494 (3.11) /
0.571 (9.85).

**fuelmix** (TWh Σ|Δ| over scoreable classes): keeper 1.04 / 0.83 / —;
Arm R 15.89 (15.2) / 15.57 (18.8) / — ; Arm K 26.12 (25.0) / 25.95 (31.3)
/ — . (2025 is unscoreable in all three lanes — the preliminary EIA-923
vintage leaves no scoreable class; the FC-4 `gas_twh`/`coal_twh` family
rows are likewise reported-not-banded for 2025.)

**co2** (fraction, reported — keeper record carries no comparable): Arm R
−24.1 / −22.5 / −30.9 %; Arm K −42.1 / −39.1 / −31.8 %.

**Reading, honestly:**

1. **The dominant overlay-value finding is the forward demand/interchange
   construction, and it is measured, not inferred.** The forward stack
   serves a zone-sum LP demand of 112.0 TWh (2023, both arms) where the
   keeper's measured backcast basis carries 96.9 TWh on the identical
   5-zone frame (the keeper nets measured interchange out of load; the
   forward construction does not), and it fills the difference by running
   the HQ_import-node supply at bound: model import energy 28.1 / 27.4 /
   29.4 TWh (Arm R 2023/24/25; Arm K 33.5 / 31.0 / 30.0), with the
   HQ→Boston 2,000 MW and HQ→Connecticut 1,500 MW links pinned at TTC
   essentially all 8,760 hours (17.5 and 13.1 TWh annual each) — roughly
   2× ISO-NE's measured ~13–19 TWh/yr net imports. The residual lands on
   the marginal class: **CC_REGULAR dispatches −13.6 TWh under actual in
   both scored years of Arm R** (38.8 vs 52.4 in 2023, 43.0 vs 56.6 in
   2024) — the whole fuelmix error — while the keeper, on measured inputs,
   matches the gas family to 0.3 TWh (53.9 vs 54.2). Root cause belongs to
   the forward demand/interchange lanes (the NEISO interchange-mechanism
   matrix cells are untested `U`); nothing here was tuned (rule 1).
2. **Both arms miss the 2025 winter-priced year entirely — the overlay
   value on price at its clearest.** Actual 2025 RT mean was $65.89 with
   Jan/Feb/Dec at $135/$126/$130 (the winter events); the forward stack
   reads ~$51 in both arms (−23.1 % / −24.5 % vs the keeper's +2.5 %), and
   the 2025 shape NRMSE is ~0.57 in both arms against the keeper's 0.058.
   Without the measured overlays (winter basis, weather pinning, outage
   windows) the winter price formation does not form. This is the
   forward-stack, harder analogue of the keeper's own ledgered C3c
   winter/scarcity model-class limitation.
3. **The Arm R 2024 price_mean gap of 0.21 (nominally "better than the
   keeper") is a single-cell coincidence, not skill:** the same year's
   shape NRMSE is 0.387 vs the keeper's 0.159 — the annual mean lands
   close while the monthly profile is wrong. Quoted with that caveat only.
4. **Driver-forecast error (Arm K vs Arm R) realized every pre-registered
   direction, with no ERCOT-style compensation artifact.** The +116 % /
   +98 % as-known gas lifts price_mean from +6.5 % to **+60.7 %** (2023)
   and from +1.2 % to **+33.7 %** (2024) — on this gas-marginal system the
   ex-ante AEO2023 error lands raw on the price (ERCOT's Arm K had looked
   nominally better in 2023 only because its Arm R was deeply under). 2025
   near-converges (−24.5 vs −23.1 %; +7.6 % gas vintage). Fuel-mix moved
   AGAINST gas as pre-registered: CC_REGULAR drops another ~10 TWh (to
   −23.8 / −23.7 vs actual), backfilled by imports (33.5 TWh 2023), and
   the K−R mix spread (+10.2 TWh) is indeed far smaller than ERCOT's
   coal-switching response. The §1.3 demand-vintage direction also
   realized: Arm K 2024/25 demand runs above Arm R's realized construction
   (114.3/116.6 vs 114.1/115.3), compounding the 2024 gas overshoot.
5. **Exit side (with §5's rider attached):** both arms execute the same
   ~4.7 GW 2024 gas_cc/gas_st economic wave (§2) against 1.40 GW of actual
   in-window exits — scorer row `retirements.total_gw` model 4.72/4.71 vs
   the window-unfiltered 3.25 actual, **+45 % FAIL**, and the composition
   is wrong: gas_cc model 4.27 GW vs 0.14 actual (×29.6), while the actual
   coal / oil / gas_ct / biomass exits (2.63 GW combined) draw model 0.
   Unit recall: 0 of 4 reachable ≥300 MW target exits matched. Zero MW of
   the window's actual exits were confirmed-knowable at the vintage cutoff
   (§5), so these rows measure the economic/announced channel only.
6. **Entry side (reported, FFR-4/5 lanes' object):** decision-basis
   additions — wind 1.00 GW vs 0.225 actual (over, FAIL), solar 2.00 vs
   1.947 (PASS), gas_cc 1.00 vs 0.0, gas_ct 0.55/0.00 (R/K) vs 0.162,
   storage 0.0 vs 0.642 (the storage-entry miss). Total 4.55 (R) / 4.00
   (K) GW vs 2.98 GW actual.

## 5. The γ rider — instrument-date split

Computed at PREREG by `scripts/probes/fh4_instrument_date_split_neiso.py`
(§1.5 — probe and numbers committed before either arm ran); the table is
reproduced here with the attribution the solves now attach.

| Window | Actual exits (all) | Thermal | Instrumented ≤ 2023-12-31 | Instrumented after | No instrument |
|---|---|---|---|---|---|
| 2023–2025 (the leg's) | **1,402.1 MW** | 1,360.7 MW | **0.0 MW** | 345.6 MW | 1,056.5 MW |
| 2021–2025 (the scorer's referent) | **3,273.9 MW** | 2,991.5 MW | **0.0 MW** | 345.6 MW | 2,928.3 MW |

The 345.6 MW is
Merrimack 2 (coal, physical cessation 2025), instrument the 2024-03-29 CWA
consent decree — after the cutoff, and its registry `exit_year` (2028-06,
the decree deadline) lies outside the window besides. Every other window
exit carries no enforceable instrument in the registry at all.

**Attribution (the γ rider's point).** ZERO MW of the window's actual exits
were knowable-as-confirmed at the vintage cutoff: the T1-FF confirmed-exit
channel (`confirmed_registry_as_of = 2023-12-31`) could not carry ANY of
them, by the information gate's own design. The exit-side FAIL rows on
these arms are therefore an **economic/announced-channel miss measured
against exits that were not confirmed-knowable at the base date** — they
must not be read as the confirmed-exit mechanism failing, and equally must
not be excused: the miss here is two-sided (a 4.27 GW false gas_cc wave
alongside 2.63 GW of missed coal/oil/gas_ct/biomass exits), which is
precisely the FFR retirement-lane object, untouched here.

## 6. Governance close-out

* **The leg ran under the UNCONDITIONAL lift (Addendum AI.1)**; both I6
  riders PASSED, so the §4 reads are quotable as T1-FF skill. The
  remaining sibling legs and FH-5 are the manager's dispatches; nothing
  here re-litigates the lift.
* **Rule 22.** Solves were {2023, 2024, 2025} in both arms — training tier
  only; freeze ACTIVE and read at launch (recorded in both metas); no
  out-of-training year solved/scored/registered; no measured H1-2026
  contact; the scorer's bounds refused nothing because nothing
  out-of-bounds was asked. The NEISO gas-basis record (neiso-86) was not
  re-opened; the window is 2023–2025.
* **Rules 1/13/14.** Nothing tuned toward any residual: the
  demand/interchange construction finding, the 2025 winter-price miss, the
  4.7 GW arm-insensitive exit wave, Arm R's I7 FAIL and the entry-side
  wind/storage misses are all reported at full magnitude and left
  standing. No bar re-level, no signal scaling, no default flip, no keeper
  contact (the keeper's own open items — the P2 replay escalation, the
  stale Aug-2025 basis defect (i) — are its record, read not acted on).
* **Rule 28.** No new `ScenarioConfig` field. Duty (b): the
  `demand_growth_vintage` fc-NEISO cell stamped U→O with the FH-4-NEISO
  measurement citation (measured-not-adjudicated, matching the ERCOT
  stamp); no other cell moved — the capacity screens were not armed here
  and the NEISO interchange cells stay `U` (this leg cites them as
  untested context only).
* **Rule 27.** Fable; all edits local on-disk bytes over `git push`; no
  `push_files` on any ≥300-line file; no new workflows.
* **Registration.** Both runs registered regardless of reads:
  `neiso-2023-2025-t1ff-armr-fh4` + `neiso-2023-2025-t1ff-armk-fh4`,
  hindcast namespace only (`frontend/data/hindcast/`); the backcast
  registry and `frontend/data/forecast/` committed inputs are untouched.
  Commit order honored: prereg → results → registration → handoff.
* **Cost note for the manager:** NEISO T1-FF arms are cheap — each
  3-solve-year arm ran ~3.5 min wall (P0 41–67 s, P1 8–14 s per year) on
  the 15 GB / 4-core container, cold at this epoch, ~2.5× faster than the
  ERCOT legs.
