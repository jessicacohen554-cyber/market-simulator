# Forecast readiness audit — 2026-07-30

**Session:** `model-forecast-readiness-audit` (owner ask: "assess forecast readiness, audit, and
develop a plan to fix any issues or findings"). **Read-only audit — no LP solved, no parameter,
threshold, offer curve, or default changed; nothing registered on any dashboard** (rules 1/11/13/14/22).
Verified against `origin/main` HEAD `6c75265` (2026-07-30). Method: five parallel evidence sweeps
(capacity-evolution blockers, forecast-mode gating, program-state drift, validation/enforcement,
forward-input currency) over code + committed artifacts, anchored on the program's own §2.1b gate
board (`frontend/data/forecast/program-status.json`, generated 2026-07-20) and the FF-2D/FF-3E
gate evidence. *Caveat: the session clone is history-grafted at 2026-07-27, so pre-07-27 movement
was verified by reading code and committed records, not by diff.*

**Companion docs:** `docs/forecast-development-plan-2026-07.md` (THE program; §2.1b gate),
`docs/handoffs/ff-t1-gate-2026-07.md` (FF-2D verdicts), `docs/handoffs/ff-poc-closeout-2026-07.md`
(FF-3E scorecard), `docs/handoffs/ff-wave-manager-ledger-2026-07.md` (program state).

---

## 0. Verdict

**The model is NOT ready to produce trustworthy 2026–2050 forecasts, and the program's own
all-HOLD verdict (FF-2D, all six ISOs; §2.1b gate closed everywhere) is confirmed — but that
verdict is now ten days stale, and this audit finds the true state is simultaneously better and
worse than the board says.**

Better:

- **The dominant blocker is now root-caused.** The I4/A1 capacity-accounting leak (FC-1 blocker
  for 4/6 ISOs) is a ledger-recording defect: confirmed-exit rows applied to plant-binned tranches
  *derate* a surviving `unit_id`, while the ledger recorder only diffs *disappeared* `unit_id`s —
  and the documented `confirmed_derates` ledger key has a reader but **no writer** (§3.1, FR-1).
  Registry arithmetic matches the invariant failures to the decimal (CAISO 1333.0 MW, MISO
  1639.8 MW). This converts the program's #1 unknown into a specifiable fix.
- **The two highest-leverage mechanism fixes are already implemented — and dormant.** The
  redesigned retirement rule (FF-1A `retirement_rule="pipeline"`) and the entry-sizing dampers
  (`entry_rate_limits`, `entry_commissioning_lag`) exist in code but ship default-off; every
  default run still executes the refuted legacy counter rule that the board's rank-1 frontier item
  describes (§3.3).
- **PJM's backcast quietly became CALIBRATED** (keeper `2026-07-29-pjm-137-ctheatrate`, zero
  failing criteria, `audit_keepers` PASS) — gate (a) for PJM is now blocked by nothing but the
  owner's marker-declaration act. The board still shows PJM as a NOT-YET-era keeper (§2).
- Infrastructure is genuinely green (verified, not just asserted): I1–I14 and FC-1..FC-8 complete,
  the ≥2026 crossover quarantine refusal is the strongest guard in the repo, the readiness battery
  and registration path work, AEO2026 fuel landed, the hydro fleet-drop bug is fixed, DC zone
  shares are populated for PJM/ERCOT, demand-growth vintages are current (§3.6).

Worse:

- **Two defects new to this audit bias every default forecast with zero flags armed:** the thermal
  fleet **never ages** over the horizon (unit age is keyed to `weather_year`, not the solve year —
  2050 entrants get *negative* age), and a **measured 2025 turbine-fire derate** fires in every
  solve year of any run pinned to `weather_year=2025` — which the T1-X crossover harness pins by
  construction (FR-7, FR-8; direct rule-13 violations).
- **Confirmed exits with a first-half exit month never finish retiring** — Brandon Shores/Wagner
  would keep ~42 % of their capacity in 2030–2050 (FR-2, code-read, not yet measured).
- **The entire T1 gate evidence base is stale**: scored 2026-07-20 at a config identity that has
  since moved twice (cache-key epoch), against keepers that have all changed (~20 promotions), and
  before the NYISO forecast orchestrator was rewired (2026-07-30). No FC verdict has been
  re-scored; no mechanism exists to detect verdict/HEAD drift (§3.5).
- **Two enforcement holes and one documentation falsehood**: the plan claims the forecast
  invariants are "CI-wired" — no workflow has referenced them since 2026-07-14; and the §2.1b
  5-solve-year cap is enforced in only 2 of ~6 entry points that can schedule a 25-year forecast
  (§3.5, FR-24/FR-25).

**Bottom line.** FF-3E's conclusion stands and sharpens: compute is not the constraint — a golden
run today would execute cleanly and be structurally wrong in five known ways (no fleet aging,
leaked exit MW + ghost partial-exit MW, legacy retirement rule, bang-bang entry, 23-year-stale PJM
capacity-price anchor). The remediation is unusually tractable because most of it is either a
specified ledger fix, an arming decision on code that already exists, or a re-score. The plan in
§4 sequences it; realistic path to first gate-open (PJM or NEISO): **Phase 1 fixes → owner
decision batch → full re-baseline**, all inside T0/T1 windows (§2.1b-compliant, ≤5 solve-years
per invocation).

---

## 1. Readiness framework used

Readiness = the program's own §2.1b full-solve authorization gate, per ISO — (a) backcast keeper +
calibration-complete marker, (b) T1 rubric no-FAIL (FC-1 PASS, FC-2 no-FAIL, FC-3/FC-4 in-band,
FC-6 green), (c) crossover input gap + readiness battery + projected cost, (d) explicit owner
authorization — plus, beneath it, the question the gate assumes: *is the gate's evidence itself
current and are the mechanisms it scores correct?* This audit verifies both layers. It does not
propose an alternative readiness definition; §2.1b is the right gate and is working as designed
(it is correctly closed).

---

## 2. The §2.1b gate at HEAD — refreshed per-ISO scorecard

What changed vs the 2026-07-20 board (`program-status.json`): **every keeper id on the board is
stale; gate-(a) outcomes (5 fail / 1 pass) still hold, but for materially changed reasons.**
`calibration-complete.json` is unchanged at HEAD: `complete={NEISO}`, `withdrawn={NYISO}`.

| ISO | (a) keeper + marker @HEAD | Backcast determination @HEAD | (b) T1-F (scored 07-20, stale) | Gate distance @HEAD |
|---|---|---|---|---|
| **PJM** | keeper `2026-07-29-pjm-137-ctheatrate`; **no marker** | **CALIBRATED — zero failing criteria** (`audit_keepers --iso PJM` PASS; calibration-log: "no gate to chase"; C3c margin is thin: 1 h/2.5 h vs the 0.5× floor) | HOLD — FC-1 FAIL **I4 only** | **Nearest of all six**: owner marker declaration + the I4/A1 fix + re-score |
| **NEISO** | marker present (2026-07-07) but **frozen to a superseded keeper** (`neiso-54`/`neiso-60`); HEAD keeper `2026-07-23-neiso-61-netrev-margin`; holdout freeze HELD (governance 2026-07-26) | CALIBRATED-WITH-CAVEATS (ledgered C3c) | HOLD — FC-1 FAIL **I4 only** | I4/A1 fix + marker re-key decision + re-score |
| **ERCOT** | keeper `2026-07-30-ercot140-coal-peak-offer`; **no marker**; frontier designation **deleted** 2026-07-26 (supersedes "withdrawn 07-17") | NOT-YET — fails {C3a, C3b, C3c, C7}; C6 UNATTESTED (8 residual-identified DOF entries) | HOLD — FC-1 FAIL I3 (scarcity slack) + FC-4 | Long: 4 backcast gates + C6 + I3 structural |
| **MISO** | keeper `2026-07-28-miso-101b-tempgrain`; **no marker** | NOT-YET — C7 COAL_PRB shape; ledgered caveats 2/3 | HOLD — FC-1 FAIL I4, I7 + FC-2 FAIL I13 cobweb | I4 + I7 + I13 arming + C7 lane |
| **NYISO** | keeper `2026-07-30-nyiso-100-silretire`; marker **withdrawn**, not re-declared | NOT-YET — **C3c sole blocker, lever queue EMPTY** (all candidates adjudicated K-by-owner/G/G/G) | HOLD — FC-1 FAIL I7. **Stalest verdict**: the forecast orchestrator gained the downstate mechanism family 2026-07-30 (D-5 parity), after scoring | I7 (hydro) + C3c owner adjudication + re-calibration path + re-score |
| **CAISO** | keeper `2026-07-29-caiso139-dump-guard-offer`; **no marker** | NOT-YET — fails {C3a-2025, C3c}, **both lanes diagnosed-unclosed with EMPTY lever queues** (caiso-140 kill / caiso-141 walled / caiso-142 wrong-sign). Honest re-derived outage input (2026-07-24) replaced the board keeper's non-reproducible input state and *worsened* the score — the correct rule-11 outcome | HOLD — FC-1 FAIL I3, I4, I7, I9 | Hardest: structural backcast residuals with no live levers + 4 invariant families |
| *(all)* | (c) readiness battery GREEN (FF-3E, unchanged); (d) no authorization exists | | FC-5/FC-6 SKIPPED at T1; FC-7 CAVEAT "DOF ledger absent" for every forecast bundle | |

Reading: the board's headline ("PJM and NEISO closest; fix A1 and both clear FC-1") survives — and
strengthens: **PJM is now the lead candidate**, being the only ISO whose backcast is fully
CALIBRATED. The critical path for four ISOs runs through backcast calibration completion (gate
(a)), which is outside the forecast program by design; this audit does not re-plan the backcast
lanes, but §4 Phase 4 states each ISO's coupled path honestly.

---

## 3. Findings register

Severity: **BLOCKER** = gates T1→T2 or corrupts a default forecast; **HIGH** = wrong results in a
standard instrument or a governance hole; **MED** = latent/conditional defect or stale input that
shifts results; **LOW** = hygiene. Every finding carries its owning lane. "(agent-verified)" =
confirmed at file:line during this audit; the four highest-severity claims were independently
re-verified line-by-line in the main session.

### 3.1 Confirmed structural blockers (board items verified still open at HEAD)

| ID | Sev | Finding | Evidence | Lane |
|---|---|---|---|---|
| **FR-1** | BLOCKER | **I4/A1 capacity-accounting leak — root-caused.** `apply_confirmed_exits` derates plant-binned tranches in place (`_derate_generator` scales `pmax_mw` on a `model_copy`, same `unit_id`; full retirement only below `_CONFIRMED_EXIT_MW_EPS`), while the ledger recorder emits retirement rows only for unit_ids absent from the surviving fleet (`evolve.py:360-371` set-diff). The schema key `confirmed_derates` is documented (`evolution_ledger.py:22,41-45`) and read (`run_driver_battery.py:778-780`) but **written by nothing** (`new_events()` never creates it; repo-wide grep: zero writers). Registry sums reproduce the T1-F failures exactly: CAISO 2027 gas_st 1333.0 MW (Alamitos 3/4/5 + Huntington Beach 2), MISO 2029 coal 1639.8 MW (Monroe 3/4); PJM 743 MW and NEISO 54 MW consistent with the partial-year factor branch. No movement since the board: `git diff` over `capacity_evolution/`, `capacity.py`, `evolution_ledger.py` is empty in the visible window. | `src/market_sim/model/capacity_evolution/retirements.py:411-414,443-456`; `evolve.py:360-371`; `results/evolution_ledger.py:88-99`; `data/raw/confirmed-retirements/*.csv` | L-CAP |
| **FR-2** | HIGH | **Partial-year confirmed exits never complete (new, same mechanism).** For `exit_month ≤ 6` the derate factor blends the exit year (`factor = m/12 + (12−m)/12·reduced`), but registry rows apply once-only at `effective_year` — the tranche is never derated the rest of the way in year+1. A unit legally gone by May 2029 keeps ~41.7 % of its MW for 2030–2050. Bites exactly the two "closest" ISOs: PJM Brandon Shores/Wagner (month 5), NEISO Merrimack (month 6). *Code-read; not yet measured in a run.* | `retirements.py:336,401-407` (once-only selection documented intentional at `:282-297`) | L-CAP |
| **FR-3** | BLOCKER | **I7/A2 base-year adequacy: hydro absent from the accredited ledger — verbatim confirmed.** `accredited_firm_capacity_mw` sums storage ELCC, wind/solar × credit, firm imports, thermal — no hydro term exists, and hydro never enters the persistent fleet ("dispatch_fleet is transient; the persistent `fleet` (un-split, **no hydro**) carries to next year" — `runner.py:1094-1096`). `firm_clean_mw` over `_FIRM_CLEAN_FUELS=("hydro",)` is structurally 0. FF-2B measured the gap (CAISO 3,601 MW / NYISO 3,343 MW) and spec'd the fix to FF-1C; **no FF-1C hydro-in-ledger code or handoff exists.** A stale comment claims the opposite ("hydro included") — see FR-23. **CLOSED 2026-07-31 by FFR-1C** (`docs/handoffs/ffr-1c-hydro-accreditation-2026-07-31.md`): hydro now enters `accredited_firm_capacity_mw` at each ISO's published class factor (`HYDRO_ACCREDITATION_CREDIT_BY_ISO`); T0 2026 A/B moved I7 by exactly the cited credit × the model's own hydro nameplate (NYISO −1,799 → −36 MW, CAISO −11,201 → −6,577, MISO −7,507 → −6,037; all three still FAIL, residuals filed as findings). The `runner.py` `firm_clean_mw` display seam is NOT fixed — it rides FFR-3B. | `model/capacity_evolution/adequacy.py:131-198`; `runner.py:1094-1096,2458-2463`; `data/fleet/assembly.py:1531,1555`; `docs/handoffs/ff-2b-adequacy-basis-2026-07.md:174-181` | L-CAP |
| **FR-4** | BLOCKER | **Legacy retirement rule is still what every default run executes.** `retirement_rule: str = "legacy"` (`scenarios.py:1021`) with `retirement_years_coal=3` — the exact configuration measured to eliminate PJM's coal wave (recall 76 %→0) and false-retire 8.6 GW of MISO gas_st. The FF-1A redesign ("pipeline") is **implemented and complete** (FF-1A-C, 2026-07-18; owner D1/D2/D3 executed) but was "never the harness default pending FF-2C" — and the FF-2C flip memo never mentions it. The T1-H FC-3 curve-ON over-fire FAILs (all four curve legs) are this rule's live signature. | `config/scenarios.py:992,1021`; `docs/handoffs/ff-retirement-rule-implementation-2026-07.md:47,~121`; `ff-t1-gate-2026-07.md §4.1` | L-CAP |
| **FR-5** | HIGH | **Economic entry is bang-bang; dampers exist but are default-off (MISO I13 cobweb).** A tech with margin > 0 builds its entire remaining queue cap; ≤ 0 builds zero (`new_entry.py:1038-1039,1137`) — precisely the alternation `check_i13_cobweb` detects. The backstop fires the full deficit in one step unless `entry_rate_limits` is armed (`adequacy.py:344-351`); `entry_rate_limits=False`, `entry_commissioning_lag=False` (`scenarios.py:1967,1984`). FF-2A's "2.5→1.103 GW" result is a probe-arm measurement, not shipped behavior. | as cited | L-CAP |
| **FR-6** | HIGH | **ERCOT I3 scarcity slack is structural and unowned in code.** Slack = LP unserved energy at VOLL (`lp/bounds.py:193-194`, `lp/costs.py:127-134`); the adequacy backstop is disabled for energy-only ERCOT **by design** (`adequacy.py:258-266`), so a one-pass under-build has no corrective and lands as slack (0.01–0.03 % of load, 2027–2030, breach-set widened by AEO2026 fuel + entry-lookahead). Cause lives only in memos; no code comment/TODO marks it. Interacts with FR-4/FR-5 (entry/retirement correctness) and the #2064 non-monotone scarcity signature. | as cited; `ff-t1-gate-2026-07.md:137,290` | L-CAP / L-SCAR |

Also confirmed still open, unchanged: **PJM position-past-zero-cross pays $0** (BLK-3 R2/R3 —
gates PJM's quantitative flip effect) and **NYISO R5a Option B implemented-but-tainted** (FF-3D
pair evidence is rule-11-tainted pre-re-audit; regenerate before any NYISO flip) — both carried
from FF-2C/FF-2D records, not re-verified in code this session.

### 3.2 New defects (this audit; none on any board)

| ID | Sev | Finding | Evidence | Lane |
|---|---|---|---|---|
| **FR-7** | BLOCKER | **The thermal fleet never ages in a forecast.** `run_year = config.weather_year` feeds the age-based outage model (`_thermal_outage(gen.plant_group, run_year - gen.online_year)`), not the solve year — which *is* available in the same function but used only for the temperature derate. A 2050 solve with default `weather_year=2024` holds every unit at its 2024 age for 25 years (systematically overstating availability), and model-built entrants (`online_year=2035`) get **negative age**. Fires in every default forecast, no flags. | `data/fleet/arrays.py:392,568,581` (solve year available at `:358,466`) | L-SCAR / L-CAP |
| **FR-8** | BLOCKER | **A measured 2025 single-event derate leaks into forecast years.** `BIN_FORCED_DERATE_BY_YEAR["N_COAL4"]={2025:0.67}` (Martin Lake turbine fire/boiler explosion) is looked up by `run_year = weather_year` with **no mode or `outage_source` gate**. Backcast is correct (weather_year==solve year). A default T1-F (weather 2024) misses it — but the **T1-X crossover harness pins `weather_year=2025`**, so every crossover solve year (realized 2023–2025 *and* forward 2026–2027) applies a 2025 plant fire it should not. Direct [R-MEASURED] violation reachable with zero flags; the table's own header says it is an off-registry channel being retired. Same table re-read unguarded at three more sites. | `data/fleet/eia860.py:2411-2429`; `data/fleet/arrays.py:688,1292,1380,1450`; `scripts/run_capacity_hindcast.py:213-215` | L-SCAR |
| **FR-9** | HIGH | **Crossover neighbor-price seam ignores the forward gas path.** `runner.py:1352` passes `gas_scenario=config.gas_price_path` unconditionally; `neighbor_price.py:206,481` raw-indexes `HENRY_HUB_TRAJECTORIES[path][year]` (no `_hold_flat_extrapolate`). In a crossover, forward years therefore price the import seam off `hindcast_realized` (keys {2021,2023–2025} only) → KeyError or wrong basis, while `assert_forward_drivers` checks only `resolve_annual_gas_price` — blind to this seam. *Plausibly the reason the launched MISO crossover never registered (its import seam is live; ERCOT/PJM's completed legs may not traverse it) — unproven, worth one diagnostic re-run.* | `runner.py:1352`; `data/neighbor_price.py:206,481`; `config/fuel_trajectories.py:180-185` | L-VAL / L-INP |
| **FR-10** | MED | **`correlated_forced_outage` (default True) lacks the backcast coercion its siblings have.** Pinned only in `pipeline/backcast_config.py:1481`; mechanism no-ops in backcast, but the field is not in `_CACHE_KEY_OPTIONAL_FIELDS`, so any backcast built outside the builder (YAML/sweep) gets a spuriously distinct cache key for an identical solve. One-line fix, same pattern as `datacenter_load_path`/`entry_lookahead_reprice`. | `scenarios.py:2314`, `outages.py:1525-1528` | L-INP |
| **FR-11** | MED | **~20 backcast-only overlay fields have no forecast-mode guard at all** (`outage_source="historic"`, four measured-gas overlays gated on flag alone, measured reserve requirements, DAM availability, per-plant must-run, mothballs, hydro envelopes, …). All default off, so the shipped forecast is safe — but rule 13's "never fires in forecast" is enforced only by the front-end. The symmetric hard-error pattern already exists for `gas_price_factor` and `federal_ces_enabled`. | `data/fuel/resolve.py:129-213`; `__post_init__` inventory (`scenarios.py:8698-9144`) | L-INP |
| **FR-12** | MED | **Bare ERCOT multi-product AS co-opt in forecast falls through to the measured AS plan** (zero for forecast years — the exact failure the existing guards describe), because the two `__post_init__` guards fire only when endogenous storage/thermal AS is *also* armed. Adjacent: the whole reserve/AS layer keys measured artifacts on `weather_year` (correct in backcast; frozen 2024/2025 record if armed in forecast), and the ERCOT non-releasable-withholding regime test uses `weather_year` instead of the existing `ercot_market_regime(year)` seam — RTC+B-obsolete behavior for 2026–2050 if armed. | `scenarios.py:9109-9144`; `model/reserves/spec.py:1220,1237-1239,1303-1305,1896,2228,2533,2875`; `results/scarcity.py:643-661` | L-SCAR |
| **FR-13** | MED | **Latent I4 of the opposite sign when the commissioning-lag gate is armed:** step-4.5 commissioned pipeline units are added to the fleet *before* the additions baseline snapshot, so no `thermal_additions` row is ever emitted for them; arming FF-2A item 3 makes I4 fail by the commissioned MW in every COD year. Must be fixed before FR-5's dampers are armed. | `evolve.py:541,549,607`; `check_forecast_invariants.py:327` | L-CAP |
| **FR-14** | MED | **The capacity-hindcast validation instrument does not validate the shipped capacity-price formation.** Production forecast defaults run curve-ON (sloped VRR) for PJM/MISO/CAISO/NEISO; the hindcast harness passes `capacity_market_clearing_by_iso=None` unless `--capacity-market-clearing` is given — so FC-3 evidence is scored on fixed net-CONE pricing while the golden posture clears a curve. | `scenarios.py:1812-1819`; `run_capacity_hindcast.py:256-258` | L-VAL |
| **FR-15** | LOW | Latent/hygiene: `_pre_known`/`_pre_ccs` dict-collapse on duplicate `unit_id` (no live producer found); `runner.py:1379` hardcodes `mode="forecast"` into import-node reconciliation (reverse-leak risk); `build_import_node_reconciliation(mode="backcast")` default parameter embeds measured data (all live callers pass it); plain-forecast `eia860_vintage_year` silently ignored while still entering the cache key; three inert FF-3D CLI flags change cache keys while changing nothing (delete per rule 26); duplicate entries in the hand-maintained 103-literal `_CACHE_KEY_OPTIONAL_FIELDS`. | `evolve.py:308,409`; `runner.py:519-521,1379`; `model/interchange/nyiso.py:571`; `run_capacity_hindcast.py:275-288` | various |

**Cache-epoch precondition (applies to every fix above):** none of FR-1/2/7/8/9 moves a
`ScenarioConfig` cache key — fixing them changes forecast output under unchanged keys, so cached
2026+ bundles would be silently reused. Any remediation wave must bump the operator cache epoch
before re-solving (`results/cache.py:15-28` documents exactly this).

### 3.3 Dormant fixes — implemented, default-off, awaiting evidence or an owner decision

| Mechanism | State | What arming would address |
|---|---|---|
| `retirement_rule="pipeline"` (FF-1A) | complete, probe-armed only | FR-4; T1-H FC-3 over-fire; MISO gas_st inversion; PJM coal recall |
| `entry_rate_limits`, `entry_commissioning_lag`, `entry_vre_capacity_revenue` (FF-2A) | complete, default-off (FR-13 must land first) | FR-5; MISO I13 cobweb; BLK-10 backstop over-fire |
| `net_cone_forward_escalation` + `NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO` (FF-G3) | design landed, all rates 0.0, **no vintage re-anchored** | FR-19 (PJM 34 % stale anchor held flat 23 years) |
| `transmission_expansion_enabled` (FF-G1, engine applied 2026-07-26) | default-off, T1-F A/B never run | frozen base-year TTC for 25 years |
| Nuclear license/SLR registry (FF-G5: 59 units, loader built) | **consumed by nothing** in the solve path | ungrounded 2035–2050 clean-firm lifetimes (BLK-9) |
| FF-G4 load-shape memo (Option B recommended) | **BUILT 2026-08-03 (FFR-SA), default-off**: `electrification_path` + `add_load_layers` (DC = layer #1, joint relocation); NEISO heat_pump layer sourced (CELT HEF), ev/{other ISOs} ship `{}` pending D4 intakes; the zero stub is deleted | FR-16 (winter-flip now EXPRESSIBLE when armed; arming = owner box) |

### 3.4 Forward-input currency (top risks for a 2026–2050 BAU)

| ID | Sev | Finding |
|---|---|---|
| **FR-16** | HIGH | **Load-shape evolution absent**: one flat compound scalar on a frozen `weather_year` 8760 (`runner.py:274-289`); peak-CAGR ≡ energy-CAGR by construction; ISO-NE/NYISO published winter-peak flips (2035/36, ~2039) are unexpressible in any model year. **MECHANISM BUILT 2026-08-03 (FFR-SA, default-off)**: FF-G4 Option-B additive end-use layers (`electrification_path`, `data/datacenter.py::add_load_layers`) make the divergence expressible where a layer is sourced (NEISO heat_pump today); the finding stays open as a POSTURE gap until the owner arms it per ISO (§8-D2) and the remaining D4 intakes land (ev profiles; PJM/NYISO/CAISO/MISO anchors). |
| **FR-17** | HIGH | **Single pinned weather year (2024) for demand *and* renewables CF** across all 25 years; the widened per-ISO weather pool exists but is ensemble-only. One year's wind drought/heat event is presented as the 2026–2050 climate. Compounded by FR-7/FR-8 (the same pin drives fleet age and event derates). |
| **FR-18** | HIGH | **Confirmed-retirements registry horizon ends 2032; NYISO registry is empty (honest zero); ~~vintage 2026-07-05 (25 days stale)~~** **STALENESS CLEARED 2026-08-03 (FFR-PA refresh) — registry vintage now 2026-08-03** (prior 2026-07-31, 2026-07-05); all 36 rows re-queried against their sources with zero behavioural change (no row added/deleted, no `exit_year` moved). **The Eddystone §202(c) sub-item is ADJUDICATED, not closed:** DOE Order No. 202-26-24 expires **2026-08-22** and **no successor has been published** (DOE's 2026 log is current through No. 202-26-37, 2026-07-26), so the rows correctly stay `superseded=true` and the supersession flip is still pending — **re-query immediately after 2026-08-22**. Also found this pass: two MISO §202(c)-deferred coal clusters (Schahfer 17/18, Culley 2; 950.7 MW) **held out** because DOE's own orders source their exit dates to EIA-860 self-report, not to a binding instrument; and the MISO Attachment Y cross-check remains blocked but is now precisely characterised with named targets (`docs/handoffs/ffr-pa-confirmed-retirements-refresh-2026-08-03.md`). **Still open:** the 2032 horizon and the empty NYISO registry — 2033–2050 exits ride the economic screen alone, i.e. on FR-4's legacy rule today. |
| **FR-19** | HIGH | **Net-CONE anchors stale and frozen**: PJM last vintage 2027/28 (242.52 $/MW-day) vs the published 2028/29 clearing at 325.69 (+34 %), held flat 23 years; NYISO/MISO frozen at 2025-26 for 25 years. FF-G3's escalation machinery is inert at default. Direct driver of over-retirement/under-entry in the largest capacity market. |
| **FR-20** | MED | ~~**ATB vintage 2024** (two editions behind; the M1 manual download never landed)~~ **PARTLY CORRECTED 2026-07-31 (FFR-PB)** — the "two editions behind" premise was **wrong**: ATB **2024 is the current edition**; no 2025 or 2026 edition exists (re-verified against the publisher's own site `atb.nlr.gov` and the OEDI listing, which ends at `csv/2024/`). The real gap was a **point-version**: OEDI mirrored ATB 2024 **v4.0.0** on 2026-07-28 and the repo held **v3.0.0**. v4.0.0 is now **landed** (`data/raw/nrel-atb/atb_2024v4_*`, `atb_version` added to the datatype key); in this model's tech slice it changes **only Geothermal/DeepEGSFlash Moderate** CAPEX (≤+6.1 %) and Fixed O&M (≤+2.0 %) — every entry technology is byte-unchanged, so the cost-escalation concern below is **not** an ATB-vintage artifact. Constants remain pinned to v3.0.0 pending the FFR-SC re-derive. **Still open:** entry-cost mid case frozen at the 2026 snapshot with only Wright's-Law decline. **IRA/OBBBA**: ~~2033–36 "other-clean" steps triangulated from secondary sources (M2 open)~~ **M2 CLOSED** — verified against primary codified text (26 U.S.C. §45Y(d)(2)-(3), §48E(e)(2)-(3), OLRC `uscode.house.gov`); all four step years confirmed **unchanged**, and OBBBA §70512(a)(2) is found to have fixed the "applicable year" flatly at 2032, removing the emissions-determination contingency. NYISO Gold Book / MISO LTLF anchors superseded by 2026 editions (unchanged, still open). |

### 3.5 Evidence-currency & process findings

| ID | Sev | Finding |
|---|---|---|
| **FR-21** | HIGH | **The T1 gate evidence is stale and nothing detects it.** FF-2D scored at 07-20; since then: ~20 keeper promotions across all six ISOs; the pinned default config cache key moved twice (`2a1cb710→edbc1b10→603c2498`), was broken-and-restored once (miso-101), and absorbed a "sixth unregistered-field regression"; the NYISO forecast orchestrator was rewired 2026-07-30 (D-5 parity — a *backcast-only mechanism family* discovered missing from the forecast path). No FC verdict re-scored; `program-status.json` gate-(a) strings, the mechanism-matrix "last full audit" keeper line, and the FF plan §1.2/WAVE FI rows are all stale (WAVE FI says "prompt issued" for four **landed** lanes; the gap register still marks them OPEN). FC-6 (driver battery) has never been run at the flipped posture (last run 2026-07-12, pre-FF-2C/1F/2A/G2); FC-4's keeper-error comparators predate every current keeper; FC-4 family-volume rows are uncovered (scorer emits aggregate fuelmix only); crossover CO2 is partly a reconstruction-basis artifact; the MISO crossover never folded in. |
| **FR-22** | HIGH | **Backcast→forecast parity drift is systemic, not a one-off.** The D-5 wiring gap (three NYISO downstate mechanisms existing only on the backcast path) was found ad hoc by a backcast session. Keeper mechanisms land weekly; nothing asserts that a mechanism armed in an ISO's keeper posture has a forecast-orchestrator counterpart (or an explicit n/a). Without a parity check, every future keeper promotion is a chance to silently fork the two paths. |
| **FR-23** | MED | **Documentation that reads as "already fixed"**: `evolution_ledger.py:38-45` describes a `confirmed`/`announced`/`confirmed_derates` schema no writer produces; `retirements.py:109-114` claims hydro is routed through the accreditation rebuild ("hydro included") when it structurally cannot be; `ercot.md:336` claims ERCOT-93 machinery "MERGED" (false for main; patch rotted); the FF plan §1.1 claims invariants are "CI-wired" (see FR-24). Each actively misleads the next auditor. |
| **FR-24** | HIGH | **`check_forecast_invariants.py` is not CI-wired anywhere** — the `forecast-invariants.yml` workflow was deleted 2026-07-14 and never restored; CI runs only the checker's unit tests on synthetic runs. The plan's §1.1 "CI-wired" claim is false. Also: `ci.yml` path filters omit `frontend/data/hindcast/**` and `frontend/data/forecast/**` entirely (a forecast-registration commit triggers **no CI**), and the backcast registry parity checker has no mode/kind assertion keeping forecast runs out of the backcast namespace. |
| **FR-25** | HIGH | **The §2.1b 5-solve-year cap is enforced in 2 of ~6 schedulable entry points** (`run_full_horizon.py`, `run_ces_leg.py`). Unguarded: `market-sim matrix` (no year args; base YAML defaults to 2026–2050), `market-sim run/sweep/ensemble` (same default horizon), the PB-5 slice scripts (named DEFERRED by §2.1b; will silently re-solve uncached members), and `golden_forecast_bands.py seed` (a 15-solve-year invocation the close-out had to reason about by hand). |
| **FR-26** | MED | **Test-coverage inversions**: the two dominant structural blockers map to exactly-missing tests — no unit test asserts `fleet(after) == fleet(before) − retirements + builds` at the `evolve_fleet` seam (FR-1 would have died at seconds of cost), and none asserts which fuels enter the accredited ledger (FR-3). Zero tests for the registration path (639-line `register_forecast_run.py` **is** the Pages deploy assembly step), `run_full_horizon.py`'s body/resume path, `collate_full_horizon.py`, and the PB-5 slice scripts. The stale golden fixture causes no red anywhere (band test slow-gated + env-gated) and has no staleness expiry. |
| **FR-27** | LOW | FC-7 reads CAVEAT "DOF ledger absent" for every forecast bundle — the forecast side has no DOF-ledger builder (rule-21 analogue is Phase-B-required); `docs/forecasting-entry-exit-assessment.md`'s headline verdict predates the FF-2C flip; three registration CLIs remain live for "one registration path". |

### 3.6 Verified healthy (so the negatives above are calibrated)

Instruments: I1–I14 complete; FC-1..FC-8 complete with the tier-applicability matrix; the ≥2026
quarantine refusal is hard, called before any file open, and proven by
`test_no_2026_file_path_is_ever_opened`; `assert_forward_drivers` + vintage-leakage guards intact;
readiness battery (input walk 6 ISOs × 25 yr GREEN, config round-trip, kill-resume) verified;
registration `--reindex` is the deploy step and works. Mode gating: 25+ sites verified CLEAN,
including the F923 fuel overlay (best-constructed gate in the repo), confirmed-exits
(forecast-only, fail-loud), planned-additions, renewables profile selection, CAMPD outage block,
RTC+B regime seam, DC backcast hard-error. Inputs: AEO2026 fuel landed (hold-flat tails via the
helper); demand growth re-derived to 2025/26 vintages, 6/6 ISOs cited; DC zone shares populated
for PJM+ERCOT; hydro fleet-drop fixed and verified for 2026–2050 (`hydro.py:854-868`);
entry costs ATB-derived with source-consistency tests; IRA/OBBBA windows policy-correct;
PLANNING_RESERVE_MARGIN and MARKET_DESIGN registries complete 6/6. Uncertainty layer mature
(sampler strongest; PB-5 correctly deferred with honest-limitations stubs only). Backcast-tuned
offer curves verified NOT leaking into forecast defaults (rule-25 containment holds).

---

## 4. Remediation plan

> **Execution vehicle:** `docs/forecast-readiness-prompt-pack-2026-07.md` — the FFR wave/prompt
> pack (Opus/Fable assignments, file-disjoint parallel sessions per wave, copy-paste prompts).
> Dispatch from the pack; this section remains the findings-to-fix rationale.
> **Refreshed 2026-07-31** (pack §0a state delta: keepers/markers/freeze moved, zero FFR items
> executed) and peer-reviewed against commercial PCM/CEM practice —
> `docs/forecast-readiness-peer-review-2026-07.md` (adds FFR-2E for FR-14; promotes FFR-PA).

Sequencing logic: **(1)** fix what corrupts every default forecast and the dominant gate blocker
(no owner decision needed, all ≤ T0/T1 scale); **(2)** put the already-implemented mechanism
decisions in front of the owner as one batch with measured evidence; **(3)** re-baseline the
entire gate evidence at the post-fix HEAD so §2.1b is decided on current facts; **(4)** open gates
per ISO in the order the evidence supports; **(5)** charter the structural input work that
outlives this cycle. Every solve in Phases 1–3 stays inside T0/T1 windows (§2.1b cap; rule 22
untouched: no 2022/2019/H1-2026 anywhere). All sessions writing `src/market_sim/` or
`scripts/run_*/score_*` are **Opus/Fable only** (rule 27); each mechanism-touching session updates
its mechanism-matrix cell (rule 28) and registers its runs on the forecast namespace in-session
(rule 15).

**Do not hand-edit `program-status.json` piecemeal** — it is FF-2D/FF-3E evidence. It regenerates
in Phase 3 from re-scored verdicts; until then this audit is the drift record.

### Phase 1 — structural fixes + guardrails (parallel, file-disjoint; no owner decision)

| # | Session (model, lane) | Scope | Acceptance |
|---|---|---|---|
| P1-a | **FABLE, L-CAP** | **Confirmed-exit accounting (FR-1, FR-2, FR-13).** Arm 1 (bookkeeping, dispatch-inert): write `confirmed_derates` rows in the derate branch + the documented `reason` split; teach I4 to close the balance with derates; move the step-4.5 additions baseline snapshot; add the missing reconciliation unit test (`fleet_after == fleet_before − retire − derate + build`, per fuel). Arm 2 (behavioral, separate commit): complete partial-year exits in year+1 (FR-2) — registry semantics, cited per row. | Arm 1: byte-identical dispatch, I4 PASS on re-probed T1-F for NEISO+PJM (both clear FC-1 per FF-2D). Arm 2: T0 probes (NEISO/ERCOT) + affected-ISO T1-F re-runs; invariants green; cache-epoch bump logged. Fix docstring drift (FR-23) in the same PR. |
| P1-b | **FABLE, L-SCAR** | **Solve-year availability (FR-7, FR-8, FR-12-adjacent).** Key fleet age to the solve year; gate `BIN_FORCED_DERATE_BY_YEAR` (and its 3 sibling read sites) behind backcast/`outage_source="historic"`; route the ERCOT withholding regime test through `ercot_market_regime(year)`; sweep the reserve layer's `weather_year` lookups to solve-year or hard backcast gates. | Backcast byte-identity proven on all six keeper configs (weather_year==year ⇒ no-op there); T0 forecast probe shows monotone availability aging; entrant age ≥ 0 asserted in a unit test; cache-epoch bump. |
| P1-c | **OPUS, L-VAL** | **Crossover seam integrity (FR-9).** Hold-flat + crossover-aware gas path at the neighbor seam; extend `assert_forward_drivers` to cover it and `weather_year`-keyed overlays; diagnose why the MISO crossover never registered; re-run MISO T1-X (≤5 yr, quarantine-legal) and fold FC-4. Fold the two L-VAL follow-ups FF-2D routed (adapter fields into `score_crossover.py`; family-volume metrics). | MISO T1-X registered + scored; ERCOT/PJM crossovers re-verified unaffected or re-run; refusal tests still pass. |
| P1-d | **OPUS, L-VAL/infra** | **Enforcement wave (FR-24, FR-25, FR-10, FR-11, FR-15, FR-26-cheap).** CI: run `check_forecast_invariants` over the committed t1f/hindcast sidecars (no solve) or correct the plan text — prefer the job; add `frontend/data/{hindcast,forecast}/**` to `ci.yml` path filters; add a mode/kind assertion to the backcast parity checker. Guards: extend `assert_schedulable` to matrix/run/sweep/ensemble/PB-5/golden CLIs. Config hygiene: `correlated_forced_outage` backcast coercion; hard forecast-mode errors for the backcast-only overlay family; delete the three inert FF-3D flags (rule 26); dedupe `_CACHE_KEY_OPTIONAL_FIELDS`. Tests: registration-path smoke test (reindex on a fixture), golden-fixture staleness expiry (fail when a cache-key-affecting default moved since seed). | CI green with the new jobs; a >5-year unauthorized invocation refused from every entry point (tested); plan §1.1 text truthful. |
| P1-e | **OPUS→FABLE, L-CAP** | **Hydro in the accredited ledger (FR-3).** Implement the FF-2B spec: hydro accredited at its **published** per-ISO credit (CAISO NQC/RA, NYISO UCAP, MISO SAC wet/dry — cited constants, rule 5/13; never a value tuned to clear I7). | I7 re-probed at T0/T1 for CAISO/NYISO/MISO; movement attributable to cited credits only; parity with the FF-2B measured gaps (3.6/3.3 GW). |
| P1-f | **OPUS, L-VAL** | **Forecast-path parity check (FR-22).** A no-solve script asserting every keeper-armed mechanism family has a forecast-orchestrator counterpart or an explicit n/a registry entry (the D-5 gap, generalized); wire into CI. | The NYISO D-5 family passes; at least the current six keeper postures sweep clean or produce filed findings. |

### Phase 2 — owner-decision batch (one sitting; evidence attached from Phases 1/3)

> **Packet (FFR-2D, 2026-08-02):** `docs/handoffs/ffr-owner-sitting-2026-08-02.md` — the assembled batch with per-item evidence status, recommendations, and sign-off lines; D-5/D-6 arrive there as residues (the marker declarations executed 2026-07-31, pack §0a).

| # | Decision | Recommendation & evidence source |
|---|---|---|
| D-1 | `retirement_rule` default legacy→**pipeline** | Re-probe FF-1A at post-P1 HEAD (T-R battery + T-R10 no-inversion + LOYO 2023–2025, bands unchanged) — flip on evidence, not on the memo. Expected to clear the FC-3 over-fire family. |
| D-2 | Arm `entry_rate_limits` + `entry_commissioning_lag` (+ `entry_vre_capacity_revenue`) | After FR-13 lands (P1-a). Re-measure I13/BLK-10 on probe legs. |
| D-3 | Net-CONE currency (FR-19) | Re-anchor PJM to the published 2028/29 clearing (rule-23 data-change citation); decide FF-G3 escalation D1–D5. NYISO/MISO re-anchor as published data allows. |
| D-4 | FF-G2 fuel option A (pure AEO2026) vs B (near-term STEO blend) | Standing owner box from the FF-G2 deliverable. |
| D-5 | **PJM calibration-complete marker declaration** + NEISO marker re-key (marker names `neiso-54`/`neiso-60`; keeper is `neiso-61`; freeze-lift is the owner's per governance 2026-07-26) | PJM is CALIBRATED with zero failing criteria — the precedent memo pattern (`neiso-calibration-complete-memo`) applies. Rule 22 one-shots remain owner-run events outside this program. |
| D-6 | NYISO path: adjudicate C3c-sole-blocker (ledgered-caveat precedent vs stay-withdrawn) + order FF-3D pair-evidence regeneration (rule-11-tainted) | The lever queue is empty — this is now an adjudication, not an engineering queue. |
| D-7 | Golden-fixture reseed authorization (15-solve-year one-off, pre-written command) and weather-year posture for eventual goldens (single 2024 draw vs pool statement in the run's honest-unfit list) | FR-17; §2.1b(d) pattern. |

### Phase 3 — re-baseline the gate evidence (after Phase-1 merges; OPUS, L-VAL)

Re-run FF-2D at the post-fix HEAD: T1-F ×6, T1-X (ERCOT+PJM+MISO), T1-H re-scores where capacity
behavior moved, **FC-6 driver battery at the flipped posture** (first time), FC-4 comparators
against the *current* keepers. Regenerate `ff-verdicts.json`, `program-status.json`, the FF-3E
readiness battery, the mechanism-matrix header, plan §1.1/§1.2 + WAVE FI + gap-register rows
(FR-21's bookkeeping desync), and `forecasting-entry-exit-assessment.md`'s post-flip verdict.
**Add staleness machinery**: every verdict/board artifact carries scored-at SHA + cache-epoch, and
a CI check WARNs when solve-affecting paths moved ≥N commits past the scored SHA — this audit's
"ten days dark" failure mode becomes detectable.

### Phase 4 — per-ISO path to gate-open (post-re-baseline order)

1. **PJM** — marker (D-5) + FR-1 + BLK-3 position half; re-scored T1-F expected FC-1 PASS. Watch
   the thin C3c margin at re-gate.
2. **NEISO** — FR-1 alone clears FC-1; marker re-key (D-5); cheapest full horizon (~1 h).
3. **MISO** — FR-1 + FR-3 + D-2 (I13); backcast C7 lane continues in parallel.
4. **ERCOT** — FR-6 via D-1/D-2 + L-SCAR level work; backcast NOT-YET {C3a,C3b,C3c,C7} + C6
   attestation is the long pole; energy-only design means no backstop shortcut.
5. **NYISO** — FR-3 + D-6 + parity re-score (its verdict is the stalest); locked tests still
   unspent.
6. **CAISO** — FR-1/FR-3 help two invariants, but both backcast lanes are diagnosed-unclosed with
   empty lever queues; treat as owner-adjudication territory, not a fix queue.

### Phase 5 — structural input work (chartered, larger; parallel-anytime)

FF-G4 Option B load-shape implementation (FR-16; memo→code, NEISO→PJM first); nuclear-registry
consumption design (FR-18/BLK-9; rule 19: one exit mechanism); confirmed-retirements re-query
cadence + the **Eddystone 2026-08-22 expiry** (3 weeks out); ~~ATB 2025/2026 intake (M1) + §45Y/48E
statute verification (M2)~~ **both DONE 2026-07-31 by FFR-PB** (M1 landed as ATB 2024 **v4.0.0** —
there is no 2025/2026 edition; M2 closed against primary statute, values unchanged) — what remains
is the FFR-SC **re-derive** against the landed v4.0.0, not an intake; FF-G1 T1-F A/B; forecast
DOF-ledger builder (FR-27, Phase-B
prerequisite). PB-5 and all T2/T3 windows remain deferred behind §2.1b — nothing in this plan
schedules them.

---

## 5. What this audit did / did not do

- **Did:** verify the §2.1b gate state and every honest-unfit/open-frontier claim at HEAD;
  root-cause FR-1; find FR-2/FR-7/FR-8/FR-9/FR-13 (new); measure board/evidence drift (§3.5);
  produce the refreshed scorecard (§2) and the phased remediation plan (§4).
- **Did not:** solve any LP; change any default, threshold, curve, or mechanism; touch any
  out-of-training year (rule 22); register anything on any dashboard (no run was produced); edit
  `program-status.json`/`ff-verdicts.json` (Phase 3 regenerates them from re-scored evidence);
  test any mechanism (no mechanism-matrix cell changes — rule 28 duties fall on the Phase-1/2
  executing sessions).
