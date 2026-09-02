# FINDING — capx T16-A: T1.6 re-pointed to `entry_rate_limits` (owner ruling Q27), the two rungs run, FC-6 re-scored

**Session:** T16-A (capacity-expansion / Forecast Finalization track), branch
`claude/capx-t16a-ladder-repoint`. **Date:** 2026-09-02. **HEAD at launch:** `69b6c8d9`
(origin/main). **Authorization:** owner ruling **Q27**, capx r#27 sitting, 2026-09-01
(`docs/handoffs/capx-director-ledger-2026-08.md` §3) — *"RE-POINT T1.6 TO
`entry_rate_limits`, at the T16 recommendation … Execution = T16-A (Opus; 2 rungs +
artifact-only re-score, no golden re-solve), HELD until the golden session closes … The
re-point-vs-amend question (T1.6's cell names an economic condition, not a config field)
is verified and stated by the execution lane."*

**Sections §§1–4 are the PRE-DECLARATION** — written and committed BEFORE the two rungs
were solved (the T3-GOLDEN pattern; rules 13/21 discipline). §§5+ carry the measured
record and were written after.

---

## 1. Scope discipline (what this lane may and may not do)

- **Two rungs, one ladder, one ISO.** T1.6 / NEISO / 2026–2050, legacy heat-rate bins
  (the battery's own documented runtime trade). Priced at **~12 min** (D21 measured
  696.5 s for this exact ladder shape); actuals in §5.
- **No golden re-solve** — Q25 is SPENT, and a third campaign needs a new owner act.
- **Artifact-only FC-6 re-score of `neiso-t3`**, control-first: the committed FC-6 record
  is reproduced before anything is re-scored (§4).
- **STOP if anything beyond `neiso-t3`'s FC-6 rows would move.** FC-1/2/3/4/5/7/8 read
  from the same committed artifacts on both sides; the paired P1/P2/P3 rows read from the
  same committed `fc6/paired_invariants.json`. The ONLY row this lane can move is FC-6's
  **battery gate rows**.
- **Rule 28:** `entry_rate_limits` already exists (armed by owner decision D-2,
  2026-08-02) — **no field is added and no default moves**. The T1.6 registry record and
  the NEISO matrix shard are updated with the Q27 citation.
- **Nothing in the backcast namespace.** No keeper, no ISO keeper shard, no
  `calibration-complete.json`, no `status/*.js`, no `bench/`. No holdout year touched
  (this is a forecast-mode 2026–2050 run, unrestricted per rule 22's 2026 clause).
- **No new GitHub Actions workflow**; the rungs solve in-session.

## 2. THE FIRST DELIVERABLE — re-point WITHIN the pre-registration, not an amendment

**Verdict: RE-POINT. Plan §2 is not edited, and does not need to be.**

Plan §2's Tier-1 table (`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`,
the "Ladder" column) was read live this session. T1.6's cell reads, verbatim:

> **NEISO or CAISO forecast, VRE fleet held short vs long**

That is an **economic condition**, not an implementation. It is the only Tier-1 row that
names no config field:

| Row | Plan §2 "Ladder" cell | Names a config field? |
|---|---|:--:|
| T1.1 | `carbon_price` ∈ {0, 25, 50, 100} $/t | yes |
| T1.2 | `mass_cap_enabled` with `mass_cap_tons` … | yes |
| T1.3 | `gas_price_factor` ∈ {0.5, 1.0, 1.5} | yes |
| T1.4 | `demand_growth_path` low/mid/high | yes |
| T1.5 | Build years straddling `ira_wind_solar_last_year` | yes |
| **T1.6** | **"NEISO or CAISO forecast, VRE fleet held short vs long"** | **NO — an economic condition** |
| T1.7 | PJM `net_cone_per_kw_yr` × {0, 1, 2} | yes |
| T1.8 | `tech_cost_path` low/mid/high | yes |
| T1.9 | Storage fleet seeded at {5, 15, 25} GW (ERCOT) | no — a quantity |

Two consequences follow, and both are load-bearing:

1. **`renewable_buildout_pace` was the 2026-07-12 session's implementation choice made
   UNDER the pre-registration, never the pre-registration itself.** Swapping the
   instrument for one that genuinely holds the VRE fleet short vs long therefore leaves
   the pre-registered claim intact. The precedent is already in the registry: T1.9's
   `_storage_seed_gw` probe patch has exactly this relationship to its own
   "seeded at {5, 15, 25} GW" quantity row.
2. **The expectations are byte-identical across the delete and the re-point.** T1.6a
   (`rps_dual_over_acp` `le_target` 1.0) and T1.6b (`rps_dual_over_acp` `monotone_down`)
   are untouched — deliberately, and now pinned by a test
   (`TestT16Repoint::test_expectations_are_unchanged_by_the_repoint`). It was the
   instrument that failed, not the claim.

**The one thing a re-point still owes**, discharged here rather than assumed: the new
lever must actually hold the VRE fleet short vs long. Verified in code, not asserted —
`runner.py:1575` builds `entry_prior_max_gw` from
`data.build_throughput.max_annual_build_gw_by_tech` only when `entry_rate_limits` is
true, and `runner.py:1901` turns it into `entry_rate_caps_mw = ENTRY_GROWTH_LIMIT_MULTIPLE
(2.0) × prior-max` per technology; with the field false the caps are `None` and entry is
uncapped. `data/build_throughput.py`'s own docstring: *"Wind/solar come from their EIA-860
technology sheets"* — the ladder is not thermal-only. So `True` = short (throughput-limited),
`False` = long (uncapped), which is the plan's condition expressed in the model's own
mechanism.

**Recorded as a re-point, not silently.** This section is the statement Q27 asked the
execution lane for. No plan §2 text is edited by this lane; the ladder's registry comment
in `scripts/run_driver_battery.py` carries the same verification at its use site.

### 2.1 The declared confound (stated, not hidden)

`entry_rate_limits` also gates **thermal** entry and, through the adequacy path, the
reserve-margin backstop. The arm is therefore **broader than VRE alone**, and the ladder
isolates "VRE fleet short vs long" only up to that co-movement. This was disclosed in the
T16 recommendation and is carried into the registry comment rather than left implicit;
the rungs' own `renewable_build_gw` / `entry_thermal_gw` / `reserve_margin_final` metrics
are reported in §5 so the co-movement is measurable rather than argued.

### 2.2 What is NOT repaired here

Plan §2 line 99's third T1.6 clause — *"nuclear does not move the dual (once the CX-6a row
half lands)"* — has never been implemented, and is not implemented here. Q27 re-pointed
the VRE lever; it did not charter the nuclear leg. **T1.6 remains a two-of-three
implementation of its own pre-registration**, and that is stated rather than quietly
carried (it was first surfaced by T16 §6 and is repeated here so the next reader of the
re-pointed ladder does not mistake it for complete).

## 3. Pre-registered outcome map (written before the solve, so no result can be chosen)

**The honesty clause, carried verbatim from T16 §6 and binding by Q27:** in **both** D21
rungs the REC dual sat pinned **at** the $50 ACP ceiling in every year
(`rps_dual_over_acp` = 1.0) with 33.0 GW of VRE already built. **A correctly-wired lever
may still not move it. If it does not, that is a REAL finding about the RPS/ACP stack —
the dual escaping to its cap, NEISO's target unreachable at any plausible VRE build —
reported as the outcome. It is NEVER grounds for trying a third lever until one moves**
(rules 1/11/14; Q27 verbatim).

The three reachable outcomes and what each means, declared now:

| # | Measured `rps_dual_over_acp` across (vre_short, vre_long) | T1.6a / T1.6b | FC-6 battery row | Reading |
|---|---|---|---|---|
| A | falls (short > long) | PASS / PASS, non-vacuous | **PASS** | the lever discriminates; the ladder tests what it pre-registers for the first time |
| B | constant (both at the cap) | PASS / PASS **flagged vacuous** | **CAVEAT** | **the RPS/ACP finding** — the dual escapes to its cap and no VRE volume this lever can reach pulls it off |
| C | rises (short < long) | PASS / **FAIL** | **FAIL** | a directional violation — a root-cause issue to open, never a threshold to widen |

Outcome B is **not** a failure of this lane and is **not** re-run for a better draw: the
scorer's constant-series detector (`forecast_verdict._vacuous_pass_reason`, which exempts
neither `le_target` nor `monotone_down`) labels it vacuous either way, and the caveat's
*reason* becomes a measured statement about the RPS/ACP stack rather than an instrument
defect. Either rung outcome is a valid result.

**FC-6's category status is not in play under any of the three.** FC-6 already reads
**FAIL** on the golden-2 record through the **paired P2** leg ("year 2050: wrong:
gas_cc↓" — the new root-caused finding golden-2 §7.1 left standing, routed to D35).
Outcomes A and B both leave that FAIL exactly where it is; only the battery row moves.
This lane therefore cannot, and does not claim it can, clear FC-6.

## 4. The control (control-first, before any re-score)

`forecast_verdict.py --tier t3` was run at this session's HEAD (`69b6c8d9`) over the
**committed golden-2 artifact set** — the campaign's `full_horizon_summary.json` (also
supplying the invariants vector), `run_config.json`, `dof_ledger.json`,
`forecast_attestation.json`, its own `fc6/paired_invariants.json` and
`fc6/driver-battery-neiso-2026-09-01.json`, the committed T1-H score
(`results/hindcast/neiso-2021-2025-curve/NEISO/2ba529574d4982ea/score.json`), the
committed D14 T1-X crossover score
(`results/hindcast/neiso-2023-2027-crossover-capxd14/NEISO/07e416f3f8072e7c/crossover_score.json`),
the re-authored corridor disposition table and the committed benchmark anchors.

| check | result |
|---|---|
| verdict JSON vs committed `results/ff-t3-neiso-golden/bau/forecast_verdict.json` | **IDENTICAL outside `provenance`** (whole-document compare, every category and row) |
| determination | HOLD both |
| FC-6 battery row | `CAVEAT — no gate FAIL but 2 vacuous row(s) … ['T1.6/T1.6a', 'T1.6/T1.6b']` both |
| `cache_epoch` | `706e7ba8e6582d42` both |
| `scored_at_sha` | control `69b6c8d9793a` vs committed `7726d91e98b4` — the only intended difference |

The control reproduces, so the re-score in §6 differs from the committed record by exactly
one input: the battery JSON.

---

## 5. The measured record — both rungs, at full magnitude

**Solved:** NEISO forecast 2026–2050, legacy heat-rate bins, years sequential within each
rung, the two rungs concurrent (rule 12). **Wall: 654.5 s = 10.9 min** against the ~12 min
Q27 pricing — inside it. Cache keys minted distinct and verified so pre-solve:
`vre_short` (`entry_rate_limits=True`) `b0b2fed9022abfbb` → runtime `e4c79ce0e1f4a76c`;
`vre_long` (`False`) `8fa63b0cc9fe85cb` → runtime `bf26a9eb5dacf56c`. Both rungs
`status: ok`, neither cached. Prerequisite, not part of the pricing: the gitignored
`data/clean` tree was rebuilt from `data/raw` first (`scripts/regenerate_clean.py`, 53/53
datatypes, **0 failures**, 35.2 min) — a fresh container has no derived tree, and the
first attempt failed fast on exactly that (`confirmed-retirements: clean partition for
NEISO is absent`), which is the guard working.

### 5.1 Every extracted metric, both rungs

| metric | `vre_short` (capped) | `vre_long` (uncapped) | Δ |
|---|---:|---:|---:|
| **`rps_dual_over_acp`** | **1.0** | **1.0** | **0.0** |
| `renewable_build_gw` | 33.0 | 33.0 | **0.0** |
| `entry_thermal_gw` | 1.0 | 0.0 | −1.0 |
| `total_build_gw` | 34.72 | 33.72 | −1.0 |
| `retired_thermal_gw` | 2.015 | 3.015 | +1.0 |
| `economic_retired_thermal_gw` | 0.1603 | 0.1603 | 0.0 |
| `exogenous_retired_thermal_gw` | 0.124 | 0.124 | 0.0 |
| `reserve_margin_final` | 0.0853 | 0.05527 | −0.030 |
| `co2_mt_total` (Mt) | 197.1768 | 193.9864 | −3.190 |
| `gas_cc_twh` | 423.4149 | 415.5949 | −7.820 |
| `coal_twh` | 0.7568 | 0.7568 | 0.0 |
| `lw_price` ($/MWh) | 66.500 | 66.224 | −0.276 |
| `scarcity_hours` | 0 | 0 | 0 |
| `storage_fleet_mw` | 3355.0 | 3355.0 | 0.0 |
| `storage_cap_value_per_mw` | 0.38343 | 0.38343 | 0.0 |
| `storage_fleet_avg_elcc` | 0.88937 | 0.88937 | 0.0 |
| `storage_new_longdur_share` | 1.0 | 1.0 | 0.0 |
| `net_cone` | 108.94 | 108.94 | 0.0 |

**Gate rows as scored by the battery:** `T1.6a` **PASS** (`all ≤ 1.0`) · `T1.6b` **PASS**
(`↓ [1.0, 1.0]`). Both are then flagged **vacuous** by the FC-6 scorer's constant-series
detector (§6) — which is the pre-registered outcome **B**, and the correct reading.

### 5.2 The lever is LIVE — this is not a second disconnected knob

The distinction matters and is stated first, because it is the one thing this run
establishes beyond doubt. `renewable_buildout_pace` produced **18 of 18 identical**
extracted values (D21 §5.1) — the signature of a field no model code reads.
`entry_rate_limits` moves **8 of the 18** comparable metrics, materially: 1.0 GW of gas-CC
entry appears in the capped arm and vanishes in the uncapped one, thermal retirements move
by the same 1.0 GW, the final reserve margin falls 8.53 % → 5.53 %, cumulative CO₂ falls
3.19 Mt and gas-CC generation 7.82 TWh. **The re-point is correctly wired.** Q27's premise
holds.

### 5.3 …but its VRE half RE-PHASES WITHOUT RE-SIZING — the ladder still does not construct its own condition

This is the finding that was not predicted, and it is the honest headline. Read from the
two rungs' own evolution ledgers:

| | `vre_short` (`entry_rate_limits=True`) | `vre_long` (`False`) |
|---|---|---|
| build years | **22** — every year 2029–2050 | **11** — alternating 2029, 2031, … 2049 |
| per-build-year tranche | alternating 1,089.4 solar + 712.6 wind / 910.6 solar + 287.4 wind | 2,000.0 solar + 1,000.0 wind |
| **cumulative VRE additions** | **33,000 MW** | **33,000 MW** |
| **terminal 2050 VRE fleet** | **37.1 GW** | **37.1 GW** |
| max inter-arm VRE gap | 1.198 GW, odd years only | — |

The growth ladder converts eleven alternate-year 3,000 MW tranches into twenty-two
consecutive-year rate-limited ones and **arrives at the identical fleet, to the MW**. It
re-phases; it does not re-size. That is the same signature FFR-2B recorded on the MISO
backstop (*"cumulative backstop 11,195.3 → 11,187.7 MW, −0.07 %, i.e. INVARIANT. It
RE-PHASES"*) — now measured on the VRE half, in NEISO, for the first time.

**Consequence for T1.6, stated plainly: the re-pointed ladder does not hold the VRE fleet
short vs long either.** It holds the *cadence* short vs long. Because
`rps_dual_over_acp` is measured on the **final-year** dual against a **final** fleet that
is identical in both arms, the ladder cannot discriminate on its own metric by
construction — and that is a second, independent reason the series is constant, on top of
the RPS/ACP result in §5.4. The binding constraint on NEISO VRE *volume* in this window is
not the growth ladder but the **per-tech queue cap** (2,000 MW solar / 1,000 MW wind per
decision year, the ceiling the uncapped arm sits exactly on). Naming that is not testing
it: **no third lever was tried, and none is proposed** (Q27, rules 1/11/14). It is filed
as the successor's open object in §8.

### 5.4 THE RPS/ACP FINDING — the dual escapes to its cap, and never comes back

The pre-registered clause fires, and the evidence is stronger than the two-point ladder it
was written for. The REC dual is **$50.00/MWh — exactly the ACP ceiling — in all 25 years
of BOTH arms, 50 arm-years without a single exception**, while the VRE fleet grows from
**4.1 GW to 37.1 GW (9.0×, +33.0 GW)**:

| year | dual `vre_short` | dual `vre_long` | VRE `vre_short` (GW) | VRE `vre_long` (GW) |
|---|---:|---:|---:|---:|
| 2026 | 50.0 | 50.0 | 4.1 | 4.1 |
| 2030 | 50.0 | 50.0 | 7.1 | 7.1 |
| 2035 | 50.0 | 50.0 | 14.902 | 16.1 |
| 2040 | 50.0 | 50.0 | 22.1 | 22.1 |
| 2045 | 50.0 | 50.0 | 29.902 | 31.1 |
| 2049 | 50.0 | 50.0 | 35.902 | 37.1 |
| 2050 | 50.0 | 50.0 | 37.1 | 37.1 |

*(All 25 years are in `fc6/_battery_metrics/`'s source ledgers; the seven above are a
readable sample of a series that is constant at 50.0 throughout.)*

**Reported as the outcome, exactly as pre-registered.** NEISO's RPS target is unreachable
at every VRE volume this model builds across a quarter-century, so the ACP escape column —
not the physical REC balance — sets the attribute price in every year, and the dual is
pinned at its ceiling. That is a **REAL statement about the RPS/ACP stack**, not a wiring
failure: the same 9× fleet expansion that fails to move it *does* move CO₂, gas-CC
generation, reserve margin and thermal entry, so the model is responding to VRE elsewhere
— just not through this dual.

**Two honest limits on that statement**, neither of which softens it:
1. The 33.0 GW ceiling is itself the queue cap's (§5.3), so this measures "unreachable at
   the volumes the entry stack will build", not "unreachable at any conceivable volume".
2. The ladder's own two-point comparison is degenerate for the reason §5.3 gives. The
   force of the finding comes from the **within-arm** 25-year series — 4.1 → 37.1 GW at a
   flat $50.00 — not from the between-arm comparison.

**No third lever was tried, and none will be** (Q27, verbatim: *"never a third lever tried
until one moves"*). Nothing was tuned, re-run for a better draw, or softened.

## 6. The FC-6 re-score — one leaf moves, and it is the right one

The §4 control and the re-score differ by **exactly one input**: the battery JSON. A
whole-document recursive diff of the two verdicts (provenance excluded) returns
**one differing leaf**:

```
PATH: .categories.FC-6.rows[0].detail
  control : … 2 vacuous row(s) …: ['T1.6/T1.6a', 'T1.6/T1.6b']
  rescored: … 2 vacuous row(s) …: ['T1.6/T1.6a (all-constant series [1.0, 1.0])',
                                   'T1.6/T1.6b (all-constant series [1.0, 1.0])']
```

Everything else — FC-1, FC-2, FC-3, FC-4, FC-5, FC-7, FC-8, the paired P1/P2/P3 rows, the
`reasons`, the `caveats`, the `determination` — is byte-identical. **The STOP rule is
satisfied by measurement, not by assertion.**

### 6.1 FC-6 battery-leg status after: **CAVEAT**, with the named reason

| | before (golden-2 record) | **after (this lane)** |
|---|---|---|
| battery gate rows | CAVEAT | **CAVEAT** |
| reason | 2 vacuous rows — ladder **OUT OF SERVICE**, the model was never asked | 2 vacuous rows — **all-constant series [1.0, 1.0]**, the model was asked and answered the same twice |
| rungs solved | 0 | **2** |
| FC-6 category | FAIL (on paired **P2**) | **FAIL** (on paired **P2**) |
| determination | HOLD | **HOLD** |

**The battery leg is scored, not skipped — and it still reads CAVEAT.** That is the
pre-registered outcome B and it is not a disappointment: the row moves from *"we never
ran the experiment"* to *"we ran it and the metric did not respond"*, which is a strictly
more informative artifact backed by 50 arm-years of measured dual. Per §3, no outcome
available to this lane could have cleared FC-6, which fails on the **P2** merit-order leg
golden-2 root-caused and routed to D35 — untouched here.

**No preserved verdict key is minted.** The program's preserve-then-overwrite discipline
attaches to a record whose *content* is replaced; here every status, every other row and
the determination are identical and the one moving leaf is a reason string becoming true —
the interaction T16 §10 anticipated in advance (*"the detail string legitimately changes …
while its status does not"*). The one-leaf diff above is the evidence that nothing was
lost; the golden-2 `session_note` is preserved verbatim and extended, not replaced.

## 7. What was written

| artifact | change |
|---|---|
| `scripts/run_driver_battery.py` | T1.6 re-pointed: `out_of_service` cleared, two `entry_rate_limits` rungs, registry comment carrying Q27, the §2 verification, the rejected alternatives, the declared confound and the honesty clause |
| `tests/scoring/test_driver_battery.py` | `TestT16Repoint` (lever, rung order, expectations unchanged) + `TestOutOfServiceLadder` (T16's machinery stays exercised now no ladder uses it) |
| `results/ff-t3-neiso-golden/bau/fc6/driver-battery-neiso-2026-09-02.{json,md}` | the new battery record — **added beside**, never over, the 2026-09-01 out-of-service record |
| `…/fc6/_battery_metrics/NEISO/*.json` | the two rungs' memoized metric sidecars |
| `results/ff-t3-neiso-golden/bau/forecast_verdict.json` | re-scored (one leaf + provenance) |
| `frontend/data/forecast/ff-verdicts.json` | `neiso-t3` re-scored; `session_note` extended; **1 of 56 keys moved**, asserted |
| `docs/codebase-site/data/mechanism-matrix/NEISO.js` | `entry_dampers` gains this ISO's `ev` citation; **cell and `fc` stay `U`** |

**Not touched:** plan §2 (§2 above is why); the T1.6 expectations; any `ScenarioConfig`
field or default; the golden's solved bundle; `forecast_attestation.json`;
`paired_invariants.json`; the FC-5 disposition table; any other ISO's shard; anything in
the backcast namespace; any GitHub Actions workflow.

**Rule 28 duties.** (a) DO-NOT-REDO: NEISO's `entry_dampers` cell was `U`/`U` — no
`R`/`I`/`G` verdict was re-tested. (b) The cell is stamped in this session with the
evidence. (c) No new `ScenarioConfig` mechanism, so no base-matrix row is owed. (d) The
cell **stays `U`**: a ladder perturbation of an already-armed field is an instrument, not
an arming adjudication, so no verdict is minted and none transfers to another ISO.
`check_mechanism_matrix.py` passes (integrity OK, 0 unresolvable anchors beyond the
ratchet, keeper stamps and §5.x headers matched).

### 7.1 Test and guard controls

| check | unmodified `origin/main` (`d697cd83`) | this branch | verdict |
|---|---|---|---|
| `tests/scoring`, FULL | 4 failed / 1198 passed / 3 skipped / 1 xfailed | 4 failed / 1198 passed / 3 skipped / 1 xfailed | **identical set** |
| the 4 failing names | `test_ff_readiness_battery::test_marker_state_reflects_committed_markers`, `::test_build_registration_scorecard_no_iso_gate_open`, `test_forecast_parity::test_all_six_keepers_resolve`, `test_gate_a_provenance::test_live_board_passes` | same four | **pre-existing, name-for-name** |
| `ScenarioConfig().cache_key()` | `7a57fadff595ca83` | `7a57fadff595ca83` | **unmoved** |
| `check_cache_key_registration.py` | — | ok, 767 fields, 220 optional all resolve, 220 declared defaults match HEAD | pass |
| `check_mechanism_matrix.py` | integrity OK | integrity OK, 0 unresolvable anchors beyond the ratchet | pass |

The four reds were measured on a clean `origin/main` checkout of this same tree (stash →
`git checkout origin/main` → re-run → restore), not inferred. **This lane introduces no
new test failure and fixes none**; the reds are another lane's object (they read the live
board / keeper resolution, not anything this lane writes) and are disclosed rather than
absorbed. The 34 tests in `tests/scoring/test_driver_battery.py` — including the five
added here — all pass.

## 8. Routed to the director — one open object, deliberately not tested here

**The VRE-volume constraint in NEISO is the per-tech queue cap, not the growth ladder**
(§5.3). Two consequences the successor owns, neither actioned by this lane:

1. **T1.6's instrument question is NOT fully closed by Q27.** The re-point is correct on
   its own terms — `entry_rate_limits` is the real, cited, consumed, owner-armed VRE-pace
   mechanism, exactly as T16 argued — but in NEISO's 2026–2050 window it re-phases VRE
   without re-sizing it, so the ladder's *cadence* contrast cannot exercise a *final-year*
   metric. Whether T1.6 should therefore (i) stand as-is with this measured limitation on
   the record, (ii) score an intermediate-year dual where the arms genuinely differ (1.198
   GW in odd years), or (iii) point at the queue cap, is a **plan §2 instrument decision
   and needs a new owner act**. This lane makes no attempt at any of them: Q27 binds
   ("never a third lever tried until one moves"), and the correct response to a
   non-moving lever is this report, not another lever.
2. **The RPS/ACP result is the more valuable half and stands on its own** (§5.4), because
   it is a *within-arm* 25-year measurement that does not depend on the ladder
   discriminating at all. If NEISO's RPS target is genuinely unreachable at every
   buildable VRE volume, that is a structural statement about the RPS/ACP stack worth its
   own examination — and it is the reason FC-6's battery CAVEAT is now an honest
   measurement rather than an instrument defect.

**Also still open, from T16 §6 and unchanged:** plan §2 line 99's *"nuclear does not move
the dual"* clause has no rung, expectation or scoring path — T1.6 remains a two-of-three
implementation of its own pre-registration (§2.2). And T16's second-order note stands
untested: `retirement_aggressiveness` has the identical dead-knob signature
`renewable_buildout_pace` had, and deserves D21's measured treatment before anyone acts.

## 9. Reproduction record

```
git fetch origin main && git checkout -B <branch> origin/main       # 69b6c8d9
python3 -m venv .venv-t16a && .venv-t16a/bin/pip install -r requirements.txt pytest
PYTHONPATH=.:src .venv-t16a/bin/python scripts/regenerate_clean.py  # 53/53, 0 failures

# the two rungs (654.5 s)
PYTHONPATH=src .venv-t16a/bin/python scripts/run_driver_battery.py \
  --iso NEISO --start-year 2026 --end-year 2050 --tests T1.6 --workers 2 \
  --out <out> --cache-root <cache>

# the FC-6 score (identical invocation for the control and the re-score, differing
# ONLY in --driver-battery: …-2026-09-01.json vs …-2026-09-02.json)
B=results/ff-t3-neiso-golden/bau
PYTHONPATH=src .venv-t16a/bin/python scripts/forecast_verdict.py --tier t3 \
  --summary $B/full_horizon_summary.json --invariants $B/full_horizon_summary.json \
  --paired-invariants $B/fc6/paired_invariants.json \
  --driver-battery $B/fc6/driver-battery-neiso-2026-09-02.json \
  --hindcast-score results/hindcast/neiso-2021-2025-curve/NEISO/2ba529574d4982ea/score.json \
  --crossover-score results/hindcast/neiso-2023-2027-crossover-capxd14/NEISO/07e416f3f8072e7c/crossover_score.json \
  --corridor results/ff-corridor/dispositions/neiso-t3.json \
  --benchmark-corridor results/ff-corridor/benchmark-corridor-anchors.json \
  --run-config $B/run_config.json --dof-ledger $B/dof_ledger.json \
  --attestation $B/forecast_attestation.json --json-out <out>.json

PYTHONPATH=src .venv-t16a/bin/python scripts/check_mechanism_matrix.py
PYTHONPATH=src:. .venv-t16a/bin/python -m pytest tests/scoring -q
```
