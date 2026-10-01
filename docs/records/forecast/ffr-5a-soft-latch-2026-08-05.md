# FFR-5A — The soft latch reverses the coal cohort because the bar's PRICE OBJECT changes between screens, not because anything recovered

**Session.** FFR Wave 5, root-cause diagnosis lane (manager-chartered, sitting Addendum R.4 —
same class as FFR-4E: diagnoses why an EXISTING mechanism behaves as measured). Branch
`claude/ffr-5a-soft-latch-diagnosis-5exu8o`, off `origin/main` `c686beb1` (two merges past the
packet's verified `4d8f0c06`; the only intervening `src/` movement is the default-off,
NEISO-gated `cc_steam_part_reclass` — verified inert for ERCOT shipped defaults by diff, so
D-13 remains the sole shipped solve-affecting delta vs FFR-3Q-3's base `68e7bfcd`).

**This lane lands no fix, flips no default, tunes nothing, promotes nothing.** The one code
change is the chartered ledger enrichment (§3): diagnostic row fields on `pipeline_events`,
no behavior change, no tunable (rule 24 untouched).

---

## 0. Headline

1. **The reversal reproduces at HEAD, on the recorded key** (`6a824992b5fb1baf` — identical to
   FFR-3Q-3's Arm A; the packet predicted a key move from D-13, but the D-13 field lands at a
   hash-dropped default). Decided 29 / 8,218 MW all-coal at `decided_year=2021`, re-confirmed
   2023 on byte-identical margins, reversed 2024 — the cohort's own execute year — executed 0.
2. **The reserve leg — FFR-3Q-3's first suspect — is MEASURED DEAD at both screens.** Reserve
   uplift is exactly $0.0/kW-yr on every enriched row, decide and reverse alike. The 2021 ORDC
   adder is two Uri hours (mean $1.13/MWh, max $4,935) whose hours coal already clears on
   energy; the 2023 and 2024 adders are identically zero (mean $0.00, 0 hours > $10).
3. **The mover is the bar's PRICE OBJECT.** The decide screen (into 2022) consumed raw zonal
   2021 duals + overlay because the entering year was THE BRIDGE — the rule-22 guard suppresses
   `entry_lookahead_reprice` there (`runner.py:2545-2546`) — and failed the cohort at
   $22.4/kW-yr vs the $58.5 bar. The reverse screen (into 2024) consumed the lookahead
   stack-reprice for the entering year (mean **$65.38**/MWh vs the year's raw duals mean
   **$15.77**, pro-forma scarcity > $1000 in 88 h, max $5000) and cleared all 29 at
   **$341.5/kW-yr — six times the bar — 100 % energy leg**.
4. **On a consistent basis there is no counter-price paradox and no reversal.** Recomputed
   against raw 2023 duals (max $29.8/MWh all year), the same 29 units sit at **$1.3/kW-yr**
   (max $12.2) — **0/29 clear**. Margins moved WITH price direction ($22.4 → ~$1.3 as the mean
   fell $23.40 → $15.77); the cohort would have re-confirmed and executed 8.2 GW at 2024. The
   "recovery on a cheaper year" is entirely the measurement-object swap.
5. **The latch is not the defect — its INPUT is.** The code matches the design record exactly
   (§5): "restores viability" is DEFINED as clearing the same bar at a later screen. The design
   presumes the bar is one measurement; in any bridged window the decide screen is
   bridge-adjacent (raw duals) and every later screen is lookahead-based BY CONSTRUCTION, so
   which object a screen consumes — not unit economics — determines the pipeline's output.
   Fix class (a), escalated (§6); class (b) memory/hysteresis is measured MOOT (no identifiable
   band survives a 6×-bar clearance); with a class-(c) rider: NEITHER consistent basis
   reproduces the real 1.534 GW of exits, which reframes FH-4/FH-5 (§6.3).

---

## 1. Step 0 — reproduction, posture verified before any read

Command (every optional flag omitted so shipped defaults inherit):

```
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr5a-pipeline
```

Realized config verified off the runtime banner BEFORE any downstream read — the FFR-3Q-3 §2
posture exactly: `retirement_rule=pipeline`, `entry_rate_limits=True`,
`entry_commissioning_lag=True`, `exit_rate_limits=False`, `crossover_solve_year_weather=True`,
`gas_price_path=hindcast_realized`. Also realized and load-bearing for this diagnosis:
`entry_lookahead_reprice=True` (shipped FF-2A default, inherited via the FFR-3D None-sentinel),
`correlated_forced_outage=True` (2021 carries the Uri derate — peak 14,351 MW removed at hour
1104), `scarcity_pricing_enabled=True` (harness master switch,
`run_capacity_hindcast.py::build_config`) + `scarcity_price_overlay=True` (ERCOT
`ISOConfig.default_scenario_overrides`), `screen_reserve_value_enabled=True`,
`ercot_thermal_as_endogenous=False`, `energy_reserve_coopt=False`, `entry_price_signal_alpha=1.0`
(EWMA pass-through), `coal_supply_repricing=True`, `coal_plant_monthly_pricing=True`,
`ira_ptc_credit_window_years=10` (D-13 realized).

* **Cache key `6a824992b5fb1baf`, taken from the runtime `cache_key=` log line** (request-side
  keys not consulted — FFR-3A-2 §1.2). Identical to FFR-3Q-3's recorded Arm A key: the packet's
  predicted D-13 key move did not materialize because the field hashes out at its shipped
  default. Cold solve (fresh container; `results/` gitignored).
* Bridge contract VERIFIED on the completed run: realized
  `solved [2021, 2023, 2024, 2025], bridged [2022]` (harness completion assertion passed);
  `evolution_2022.json` written by the bridge branch; **no `year_2022.parquet`** (4 parquets
  total); zero 2022 measured reads.
* Event census, exactly FFR-3Q-3's 1,205: 2022 ledger decided 29 + entry_capped 582; 2023
  re_confirmed 29 + entry_capped 536; 2024 reversed 29 (and entry_capped **0** — the lookahead
  object fails no one); 2025 none. `executed = 0` in every year.
* Ledger reserve margins 48.5 % / 34.8 % / 39.8 % / 47.8 % (2021/2023/2024/2025) vs FFR-3Q-3's
  48.5 / 34.8 / 40.9 / 49.0. **The 2024-25 drift under the IDENTICAL cache key is itself a
  finding worth recording:** D-13 (`ira_ptc_credit_window_years` None→10) moved wind-PTC entry
  economics — later-year fleets shift — while the key did not move, because the field is
  excluded from the hash at its shipped default on both sides of the flip. That is a
  collision-class hazard for WARM caches (a pre-D-13 cached year could be served under a
  post-D-13 config); harmless here (cold container, and D-10 keeps forecast-bundle cross-year
  warm start off), but successors comparing "same key" runs across the D-13 boundary must not
  read byte-identity into it. The cohort/latch behavior this lane diagnoses is identical on
  both sides.
* Ledgers read at `<out-dir>/ERCOT/6a824992b5fb1baf/` (never the out-dir root); files
  enumerated before any zero was interpreted; `decided_year` read off event rows, not the
  ledger year (the 2022 ledger carries `decided_year=2021` rows — the ffr-3q3 §3.2 trap).

Reproduction: **decided 29 / 8,218 MW (all coal) in the 2022 ledger with `decided_year=2021`,
`execute_year=2024`; re_confirmed 29 in 2023; reversed 29 in 2024; executed 0 everywhere** —
the FFR-3Q-3 finding, exactly, at HEAD.

---

## 2. The bar is not the same object year over year

The screens consume `prior_results` of the LAST SOLVED year (the runner's bridge branch leaves
`prior_results`/`last_solved_year` untouched across 2022), so the four screens ran on:

| ledger year | screen basis | price object consumed | events |
|---|---|---|---|
| 2022 | 2021 solve | **raw zonal duals + 2021 overlay** (lookahead SUPPRESSED: entering year 2022 ∈ `HINDCAST_BRIDGE_YEARS`, `runner.py:2545-2546`) | decided 29 / 8,218 MW; entry_capped 582 / 58,684 MW |
| 2023 | 2021 solve again (2022 bridged) | same object — margins byte-identical to the 2022 rows (verified) | re_confirmed 29; entry_capped 536 / 57,960 MW |
| 2024 | 2023 solve | **lookahead stack-reprice for entering 2024** (`runner.py:2575`, `_lookahead_reprice_signal` at `runner.py:479`) | **reversed 29** — zero failing units anywhere |
| 2025 | 2024 solve | lookahead stack-reprice for entering 2025 | none — zero failing units |

Three basis boundaries sit between the decide screen and the reverse screen; the enrichment
(§3) sizes each:

**(a) The price object — THE mover (+$319/kW-yr of +$319 total).**
`entry_lookahead_reprice=True` is the shipped forecast default; the screen's price object is
`prior_results.price_signal` (`evolve.py` replaces `prices` with it). The runner builds it at
year Y for the ENTERING year Y+1, except when Y+1 is a bridge year — the rule-22 guard then
leaves `price_signal = econ_prices` (`runner.py:2536`). So the decide screen for any cohort
formed off the base year is ALWAYS bridge-adjacent in this window design (2021→2022), and every
re-screen of that cohort is lookahead-based. The two objects are structurally different
measurements:

* raw 2021 duals + overlay, zonal: mean $29.38 in the cohort's zones, max $5,000 (two Uri
  overlay hours; raw dual max $68.8 — this reconciles FFR-3Q-3's "max hourly price $68.78, no
  scarcity anywhere": the raw duals never spike, the overlay does, twice).
* lookahead reprice for 2024, system-wide: mean **$65.38** vs raw-2023-duals mean $15.77 —
  a 4.1× level ratio — with pro-forma scarcity > $200 in 122 h and > $1000 in 88 h (max
  $5000), produced on a fleet whose in-year 2023 LP formed ZERO scarcity (raw dual max
  $29.8/MWh, ORDC adder identically zero).

  Why the pro-forma is that hot on a 34.8 %-reserve-margin fleet (`_lookahead_reprice_signal`,
  `runner.py:479-538`): the stack is **thermal-only** (storage never enters `fleet_arrays`
  pmax — the same stack FFR-4A measured "cannot see its own committed pipeline" also cannot
  see storage at all), net load subtracts **prior-year VRE OUTPUT** (not entering-year
  capacity), capacity is derated by **time-mean availability** (≈0.79-0.85 applied to peak
  hours where real availability is higher — maintenance is scheduled off-peak), and in a
  full-forward leg the entering-year demand is the **growth-scaled fallback**, not measured
  load (`is_crossover_forward_year` branch — rule-22-correct). Reserves = thermal stack −
  net load goes ≈0/negative in the top ~100 hours and the ORDC tail saturates.

**(b) The reserve leg — dead at both screens ($0.0 of the +$319).**
`reserve_price_signal = overlay_adder` of the prior solved year (`runner.py:2649`; co-opt and
endogenous-AS both off; coal is synchronized-tier eligible). Measured: 2021 adder mean
$1.13/MWh concentrated in 2 Uri hours — in exactly those hours coal's energy spread already
exceeds the adder, so `max(energy, reserve)` never picks reserve and the uplift is $0.0;
2023/2024 adders are identically zero. The AS *mechanism* is stable across screens
(`as_pricing="hourly_signal"` on every row, annual credits suppressed); its magnitude
contributes nothing. **FFR-3Q-3 §3.5's "first place a successor should look" is adjudicated:
not the reserve leg.**

**(c) The coal fuel-cost basis — real but second-order (≈ +$15-17/kW-yr of the +$319).**
`apply_coal_supply_pricing` returns early for years before the 2023+ trajectory
(`data/fuel/coal.py:136-139`), so the 2021 solve's coal mc used the generic resolved price
(`COAL_PRICE_BASE["ERCOT"]` = $2.00/MMBtu, AEO-shape escalated) while the 2023 solve repriced
lignite plants to $1.45/MMBtu flat and PRB plants to measured 2023 monthly actuals (annual
$2.15; passthrough 1.0). Cap-weighted cohort mc: **$26.80 → $24.41/MWh**. Under the lookahead
object (~6,900 in-merit available-hours) that is worth ≈ $16/kW-yr — an order of magnitude
below the price-object term.

Availability is effectively same-object (0.798 → 0.790 cap-weighted; 2021's Uri derate is a
real physical event, not a basis drift). The GFC side is byte-identical across screens: same
`fixed_om_coal` 45.0 × 1.3 = $58.5/kW-yr bar, same pmax, same multiplier. **The bar's cost side
is one object; its revenue side is not.**

---

## 3. The per-unit decomposition (the chartered ledger enrichment)

Landed this session (commit `5a10b520`, behavior-neutral — 231 capacity-evolution tests pass
unchanged; row fields, no knob): every `pipeline_events` row carries `net_revenue_usd`,
`going_forward_cost_usd`, `energy_margin_usd`, `reserve_uplift_usd`, `attribute_revenue_usd`,
`capacity_revenue_usd`, `as_annual_credit_usd`, `as_pricing`, and the screen-basis descriptors
(`screen_price_mean/max_usd_mwh`, `reserve_signal_mean_usd_mwh`, `availability_mean`,
`mc_mean_usd_mwh`). Schema documented in `results/evolution_ledger.py`.

Cap-weighted over the 29-unit cohort (8,218 MW; per-unit table in the run ledgers):

| screen | net_rev | bar | energy | reserve uplift | attr | cap rev | AS annual | p_mean | p_max | mc_mean | avail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| decide (2022 ledger, 2021 basis) | **22.4** | 58.5 | 22.4 | **0.0** | 0.0 | 0.0 | 0.0 | 29.38 | 5,000 | 26.80 | 0.798 |
| re-confirm (2023 ledger) | 22.4 (byte-same) | 58.5 | 22.4 | 0.0 | 0.0 | 0.0 | 0.0 | 29.38 | 5,000 | 26.80 | 0.798 |
| reverse (2024 ledger, 2023 basis) | **341.5** | 58.5 | **341.5** | **0.0** | 0.0 | 0.0 | 0.0 | **65.38** | 5,000 | 24.41 | 0.790 |

Per-unit spread at the reverse screen: $332–362/kW-yr — every unit clears by ≥ 5.7×. Answering
the charter's quantification directly: **the reserve-price share of the 2023 attainable margin
is 0 %; the energy leg is 100 %, and its level is set by the lookahead price object, not by
2023's dispatch prices.**

**The consistent-basis counterfactual (measured, not inferred).** Recomputing the same 29
units' energy pro-forma against the persisted raw 2023 zonal duals (flat per-unit
`mc_mean_usd_mwh`, `availability_mean` — approximation validated on the 2021 side, where it
reproduces $16.5 of the recorded $22.4, the remainder being the two overlay hours + flat-mc
bias): **$1.3/kW-yr cap-weighted, range $0.1–12.2, 0/29 clearing $58.5.** On the decide
screen's own object-kind the cohort is failing ~17× deeper in 2023 than in 2021 — with, not
against, price direction — and would have executed 8,218 MW at 2024.

**Fleet-wide context, same enrichment.** The decide screen's `entry_capped` rows: 582 units /
58,684 MW spanning ALL merchant thermal fuels (gas_cc 30.7 GW, gas_ct 11.0, gas_st 11.3, coal
overflow 5.7). On raw prior-year perfect-foresight duals the ENTIRE merchant fleet fails the
bar — the s2/s3 revenue-understatement posture is ambient — and the adequacy admission cap
picks the 29 deepest $/kW shortfalls, which is exactly the coal fleet because coal's bar is
1.3 × 45.0 while gas bars are $21-35. Conversely at the lookahead-based screens (2024, 2025
ledgers) there are ZERO failing units of any fuel — the into-2025 screen's revenue-stack log
(2024 prior, lookahead for 2025: mean $58.90, 74 h > $1000) shows every class clearing by
4-13×: coal $296.7 vs $58.5, gas_cc $329.9 vs $30, gas_ct $267.0 vs $21, gas_st $216.1 vs $35,
nuclear $522.8 vs $130. **The raw-duals object fails everything; the lookahead object clears
everything.** The pipeline's content is decided by which object a screen consumes.

---

## 4. Year-over-year basis audit (charter question 2, itemized)

| bar component | same object? | measured |
|---|---|---|
| price object | **NO** | raw zonal duals+overlay (decide/re-confirm) vs system lookahead stack-reprice with ORDC tail (reverse); mean 29.38 vs 65.38; the +$319/kW-yr mover |
| reserve source | mechanism yes, magnitude moves, leg dead | overlay adder both; 1.13 → 0.00 $/MWh mean; uplift $0.0 at BOTH screens |
| fuel-cost basis (mc) | **NO** (trajectory boundary) | generic $2.00/MMBtu (2021, pre-trajectory) vs lignite 1.45 / PRB 2.15 measured (2023); 26.80 → 24.41 $/MWh; ≈ +$16/kW-yr, second-order |
| availability | yes (real weather difference only) | 0.798 → 0.790 (2021 carries the Uri correlated derate — physical, not basis) |
| pmax / FOM / multiplier (GFC side) | **yes, byte-identical** | $58.5/kW-yr both screens |
| EWMA / alpha | yes (pass-through) | `entry_price_signal_alpha=1.0` |

A basis drift between the 2021 screen and the 2023 screen was the packet's hypothesis for
"counter-price recovery with no economics at all" — confirmed, located in the price object, and
quantified: the drift IS the whole reversal.

---

## 5. Intent vs code — the latch behaved as designed; the design presumes one bar

Design record: `docs/handoffs/ff-retirement-rule-redesign-2026-07.md`. §3.6 component 3: a
pipelined unit "leaves the pipeline ONLY if its margin clears the same bar (net_revenue ≥
going_forward_cost) at a later screen. No band, no new parameter. … economic recovery and
policy rescue are the two real reversal channels"; "a price recovery cancels a pending exit
only if it actually restores that unit's viability." §3.4 (hysteresis band): REJECTED because
"nothing on disk pins `h`" — the latch is adopted as "asymmetry without a band," and the
docstring's "one good year no longer erases the distress history unless it actually restores
viability" is that sentence compressed: the CONTRAST is the legacy counter's reset-on-any-blip
(one good year erased a multi-year streak REQUIREMENT and restarted the clock); under the
pipeline a good year that clears the bar is DEFINED as viability restoration. The code
(`retirements.py:1457` comparison; `:1462` pop; the latch runs before the due-set build at
`:1515`, so a unit clearing at its own execute year reverses rather than executes) implements
the design faithfully. **Adjudication: the 2023 re-clear is NOT a genuine viability
restoration — on the decide screen's own object-kind the cohort is at $1.3/kW-yr — and the
latch's INPUT, not its logic, is the defect. The design's implicit premise ("the same bar")
is violated by the screen sequence, not by the latch.**

---

## 6. Fix class — (a), escalated; (b) foreclosed; with a (c) rider

**6.1 Class (a): basis-inconsistency defect in the bar's input. ESCALATED, not landed.**
The exact seam: `runner.py:2536-2553` — `price_signal = econ_prices` default, replaced by
`_lookahead_reprice_signal` for the entering year EXCEPT when `lookahead_next_ok` excludes a
bridge year (2546). The interaction of two individually-correct gates (the rule-22 bridge
guard; the FF-2A default-ON lookahead) guarantees that in ANY bridged window a base-year
cohort is decided on raw duals and re-screened on the lookahead object. No single line is
"wrong"; which price object the capacity screens should own is a rule-19 one-mechanism DESIGN
decision the owner has to make, and it interacts with the entry side (the same signal feeds
the new-entry and storage screens) and with two open owner items already on the books
(FFR-4A's owner-nominated relocation of the anti-cobweb guard INTO the lookahead; FFR-3V's
measured no-tail-vs-tail contrast). The owner's option space, enumerated without
recommendation:
  1. pin a cohort's re-screens to the OBJECT-KIND that decided it (measurement consistency
     within a cohort lifetime);
  2. lookahead everywhere, including bridge-adjacent screens (the growth-scaled fallback the
     full-forward leg already uses keeps rule 22 intact — no measured read);
  3. lookahead nowhere in the retirement screen (revert to raw duals+overlay; re-opens the
     s2/s3 understatement that motivated FF-2A);
  4. repair the lookahead object's level: the stack omits storage entirely, nets prior-year
     VRE output, applies time-mean availability to peak hours — three identified completeness
     gaps that jointly manufacture 122 pro-forma scarcity hours on a 34.8 %-RM fleet.
Any change is a structural mechanism change: leave-one-year-out scoring within 2023-2025
before promotion (rule 22), and the matrix cells it touches move in that session, not this one.

**6.2 Class (b): memory/hysteresis — MEASURED MOOT. Do not design one.** The design record
already rejected the band as unidentifiable (§3.4); this lane adds the quantitative closure:
the reverse-screen margin is $341.5/kW-yr against a $58.5 bar, so any hysteresis band
h < $283/kW-yr still reverses — no identifiable memory mechanism survives a 6×-bar clearance.
The phenomenon is not "the latch forgets distress"; it is "the bar's revenue side quadrupled
by construction."

**6.3 Class (c) rider — consistency alone does not rescue the exit half.** On the consistent
raw-duals basis the whole 66.9 GW merchant fleet fails every screen: the cohort executes
8.2 GW at 2024 and the cap admits successors — against 1.534 GW of actual 2023-25 exits, an
over-retirement in composition and size (and the same understatement the s2 root-cause already
names). On the consistent lookahead basis nothing ever fails and shipped behavior (0.000 GW,
recall 0/3) is reproduced without any bridge asymmetry. **The two objects bracket reality so
widely that the pipeline's output is determined by bridge geometry, not unit economics.** The
real exits (three units > 300 MW) happened for reasons this signal cannot resolve at either
extreme. That REFRAMES FH-4/FH-5 — the exit half of the retirement layer cannot be validated
until the owner's price-object decision lands — and it does NOT unblock them (the lift is a
manager box, Addendum I.1; this lane reports).

---

## 7. What this lane did NOT separate

* **No lookahead-off control arm was solved.** The attribution rests on the enriched
  descriptors plus the raw-duals counterfactual recomputed from the run's own persisted
  prices — arithmetic on one run, not an A/B. A `--no-entry-lookahead-reprice` control would
  make the counterfactual a solved fact (including its effect on entry and on later-year
  fleets) at the cost of another 4-year cold solve; it was not chartered and the recomputation
  already bounds it (flat-mc approximation validated within ~$6/kW-yr on the 2021 side, an
  error two orders below the effect).
* **The Uri-derate contribution is not isolated from the price-object contribution inside the
  2021 margin** (both sat on the decide side; separating them changes nothing about the
  reversal, which is a reverse-screen phenomenon).
* **No statement about WHICH price object is correct.** That is the owner's §6.1 decision;
  this lane measured what each object does, not what the screen should see.
* **The admission-cap composition question** (why exactly 29 units / why all-coal — the 1.3×
  FOM bar making coal the deepest shortfall is measured here, but whether depth-first
  admission is the right competition is untouched).
* **2022 was never solved and its data never read** — the bridge contract held; nothing in
  this diagnosis required touching it.

---

## 8. Governance position

* No out-of-training year solved, scored, or registered; 2022 bridged (contract verified on
  the realized ledgers); scoring bounded to 2023-2025 on both sides. ERCOT holds no marker and
  needed none — the window is legal by the enumerated carve-out; the holdout freeze is
  orthogonal and untouched.
* Nothing armed, unarmed, promoted, tuned, or reverted. The ledger enrichment adds row fields,
  not parameters (rule 24); the decision path consumed `net_revenue` vs `going_forward_cost`
  before any row is written, and 231 capacity-evolution tests pass unchanged.
* Run registered to `frontend/data/hindcast/` as
  `ercot-2021-2025-t1ff-armr-ffr5a-pipeline` (`meta.kind="full_forward"`) — EVIDENCE for this
  diagnosis, expected to be superseded when keepers settle (Q.2). Never the backcast registry.
* Rule 28: `economic_retirement_screen` ERCOT `fc` cell — evidence recorded in this session,
  **cell stays O** (a diagnosis lane adjudicates no verdict; the located defect is upstream of
  the rule and its resolution is an owner decision). No other ISO's column touched.
* FH-4/FH-5: the lift remains a MANAGER box (Addendum I.1). This lane reports; green does not
  lift, and §6.3 is not green anyway.

---

## Appendix A — per-unit bar decomposition (from the enriched run ledgers)

Columns: `dec:` = decide screen (2022 ledger, 2021 basis) and `rev:` = reverse screen (2024
ledger, 2023 basis), each as net revenue / bar / energy leg / reserve uplift in $/kW-yr; then
the reverse screen's price mean/max ($/MWh, lookahead object), the unit's mc drift
(2021 basis → 2023 basis, $/MWh) and availability drift. Regenerate with the §1 command —
ledgers are the reproducible artifact per the results/hindcast slim-set convention; the 2023
re-confirmation rows are byte-identical to the decide rows and omitted.

```
unit_id                               mw  | dec: net  gfc  energy resv | rev: net   gfc  energy resv | p_mean  p_max   mc21->mc23  avail21->23
COAL_Houston_p3470_committed             489 |  13.8  58.5   13.8  0.0 |  332.3  58.5  332.3  0.0 |  65.38    5000 29.25->27.05 0.781->0.769
COAL_Houston_p3470_peak                  122 |  13.6  58.5   13.6  0.0 |  332.1  58.5  332.1  0.0 |  65.38    5000 29.35->27.34 0.781->0.769
COAL_North_p298_committed                462 |  18.3  58.5   18.3  0.0 |  345.4  58.5  345.4  0.0 |  65.38    5000 27.89->25.82 0.817->0.815
COAL_North_p298_peak                      92 |  17.6  58.5   17.6  0.0 |  345.0  58.5  345.0  0.0 |  65.38    5000 28.11->26.21 0.817->0.815
COAL_North_p6180_committed               180 |  23.9  58.5   23.9  0.0 |  361.7  58.5  361.7  0.0 |  65.38    5000 26.33->20.32 0.819->0.821
COAL_North_p6180_peak                     90 |  22.5  58.5   22.5  0.0 |  358.2  58.5  358.2  0.0 |  65.38    5000 26.68->21.20 0.819->0.821
COAL_North_p7030_committed                35 |  18.1  58.5   18.1  0.0 |  342.5  58.5  342.5  0.0 |  65.38    5000 27.87->21.44 0.802->0.804
COAL_North_p7030_mustrun                 140 |  31.0  58.5   31.0  0.0 |  351.3  58.5  351.3  0.0 |  65.38    5000 24.82->19.23 0.802->0.804
COAL_North_p7030_peak                     17 |  17.4  58.5   17.4  0.0 |  339.8  58.5  339.8  0.0 |  65.38    5000 28.09->22.22 0.802->0.804
COAL_Northeast_p6146_committed           595 |  16.7  58.5   16.7  0.0 |  332.9  58.5  332.9  0.0 |  65.38    5000 28.14->26.05 0.781->0.769
COAL_Northeast_p6146_econ               1071 |  28.9  58.5   28.9  0.0 |  337.3  58.5  337.3  0.0 |  65.38    5000 25.06->23.24 0.781->0.769
COAL_Northeast_p6146_mustrun             595 |  28.9  58.5   28.9  0.0 |  337.3  58.5  337.3  0.0 |  65.38    5000 25.06->23.24 0.781->0.769
COAL_Northeast_p6146_peak                119 |  16.2  58.5   16.2  0.0 |  332.6  58.5  332.6  0.0 |  65.38    5000 28.34->26.42 0.781->0.769
COAL_South_Central_p6179_committed       338 |  14.6  58.5   14.6  0.0 |  335.9  58.5  335.9  0.0 |  65.38    5000 29.04->26.86 0.795->0.783
COAL_South_Central_p6179_econ            845 |  25.3  58.5   25.3  0.0 |  339.2  58.5  339.2  0.0 |  65.38    5000 25.84->23.95 0.795->0.783
COAL_South_Central_p6179_mustrun         422 |  25.3  58.5   25.3  0.0 |  339.2  58.5  339.2  0.0 |  65.38    5000 25.84->23.95 0.795->0.783
COAL_South_Central_p6179_peak             84 |  14.3  58.5   14.3  0.0 |  335.8  58.5  335.8  0.0 |  65.38    5000 29.16->27.17 0.795->0.783
COAL_South_Central_p7097_committed       298 |  13.4  58.5   13.4  0.0 |  346.8  58.5  346.8  0.0 |  65.38    5000 29.75->27.51 0.819->0.821
COAL_South_Central_p7097_econ            744 |  23.4  58.5   23.4  0.0 |  349.3  58.5  349.3  0.0 |  65.38    5000 26.46->24.51 0.819->0.821
COAL_South_Central_p7097_mustrun         372 |  23.4  58.5   23.4  0.0 |  349.3  58.5  349.3  0.0 |  65.38    5000 26.46->24.51 0.819->0.821
COAL_South_Central_p7097_peak             74 |  13.3  58.5   13.3  0.0 |  346.7  58.5  346.7  0.0 |  65.38    5000 29.81->27.76 0.819->0.821
COAL_South_p6178_committed               124 |  17.5  58.5   17.5  0.0 |  338.3  58.5  338.3  0.0 |  65.38    5000 28.05->25.96 0.802->0.790
COAL_South_p6178_econ                    311 |  30.1  58.5   30.1  0.0 |  343.0  58.5  343.0  0.0 |  65.38    5000 24.98->23.16 0.802->0.790
COAL_South_p6178_mustrun                 156 |  30.1  58.5   30.1  0.0 |  343.0  58.5  343.0  0.0 |  65.38    5000 24.98->23.16 0.802->0.790
COAL_South_p6178_peak                     31 |  16.9  58.5   16.9  0.0 |  338.0  58.5  338.0  0.0 |  65.38    5000 28.25->26.35 0.802->0.790
COAL_South_p6183_committed                41 |  12.1  58.5   12.1  0.0 |  345.4  58.5  345.4  0.0 |  65.38    5000 30.37->23.26 0.811->0.804
COAL_South_p6183_econ                    184 |  21.1  58.5   21.1  0.0 |  353.8  58.5  353.8  0.0 |  65.38    5000 27.00->20.81 0.811->0.804
COAL_South_p6183_mustrun                 164 |  21.1  58.5   21.1  0.0 |  353.8  58.5  353.8  0.0 |  65.38    5000 27.00->20.81 0.811->0.804
COAL_South_p6183_peak                     20 |  12.1  58.5   12.1  0.0 |  344.0  58.5  344.0  0.0 |  65.38    5000 30.38->23.88 0.811->0.804
```

Cap-weighted (8,218 MW): decide net $22.4 (energy 22.4, reserve 0.0) vs bar $58.5, p_mean
$29.38, mc $26.80, avail 0.798; reverse net $341.5 (energy 341.5, reserve 0.0) vs bar $58.5,
p_mean $65.38, mc $24.41, avail 0.790, r_mean 0.000. Consistent-basis counterfactual on raw
2023 duals: $1.3/kW-yr, range $0.1–12.2, 0/29 clear.
