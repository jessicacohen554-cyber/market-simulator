> Status: CHARTERED (2026-10-03) — the MILP unit-commitment program: feasibility verdict, architecture, phases, testing protocol, desk charter and owner decision queue. Owner: jessicacohen554. **Chartered 2026-10-03** (R1, R2 in §8.1): D-0 charter, D-1 signed. Zero LP so far; no `src/`, spec, `CLAUDE.md`, keeper, matrix or rubric change yet. Evidence under `docs/records/governance/uc-milp-2026-10/`.

# MILP unit-commitment program — plan (October 2026)

**The answer in one paragraph.** A MILP unit commitment (UC) is feasible with the pinned stack: HiGHS 1.14 via `highspy` is a MILP solver and the integrality, gap, time-limit and warm-start calls work (verified, `ASSESSMENT` §3). It is **layered, not a rebuild**: a MILP has no duals, so it cannot be the scored run (rule 4); it sits between P0 and P1 as a rolling-horizon day-ahead stage that *chooses* the commitment, and P1 prices it exactly as today with the commitment entering as per-unit-hour bounds through the hook the three commitment bridges already use. A full-year MILP is intractable here (22–30 M columns); a 36-hour window is ~100 k columns with a few thousand integers and is routine. What integrality buys is the one thing no LP form in this repo could: fixed costs of being online (start, no-load), whole-unit min-load and min-up/down, and an online capacity equal to the units actually on — the measured object the relaxed posture missed by 3.7–4.2×. The program is gated by a zero-LP benefit screen that ranks ISO-years, a wallclock ladder that measures the cost before any full-span shard, and per-ISO A/Bs with pre-fixed readings. Calibration gains are measured, not promised: records already bound the *energy* effect small for SPP CC 2021/22 and non-discriminating for PJM coal; the live promise is price formation (trough depth, body level, reserve scarcity, uplift) and forecast realism.

## 1. Architecture

```
                 today                                         with the UC stage (gate `unit_commitment_milp`)
  ┌──────────┐   ┌────────┐   ┌──────────┐          ┌──────────┐  ┌────────┐  ┌──────────────────────┐  ┌──────────┐
  │ P0 LP    │─► │ markup │─► │ P1 LP    │          │ P0 LP    │─►│ markup │─►│ UC: 365 rolling MILPs │─►│ P1 LP    │
  │ 8760 h   │   │+bridge │   │ 8760 h   │          │ 8760 h   │  │        │  │ 24 h commit + 12 h   │  │ 8760 h   │
  │ base mc  │   │ floors │   │ SCORED   │          │ base mc  │  │        │  │ look-ahead, integer u │  │ SCORED   │
  └──────────┘   └────────┘   └──────────┘          └──────────┘  └────────┘  └──────────────────────┘  └──────────┘
                                                        │ SOC, water values, duals ─► window boundaries   ▲
                                                        │ run pattern ──────────────► warm start          │
                                                        └─ schedule u[c,t] ──► p1_fleet_prep: ceiling = avail·u/n, floor = mlf·p̄·u (MECH 28)
  prices = P1 duals (rule 4) ─ unchanged form, unchanged bundle, every diagnostic unchanged
```

| Property | Today | With UC | Rule |
|---|---|---|---|
| scored run | P1 LP | P1 LP (same builder, same outputs) | 4, 8 |
| commitment state | detected from P0 by a bridge (3 ISOs) or none | **chosen** by the MILP over a DA horizon | 1, 17 |
| start cost | amortized $/MWh markup in P1 bids | paid once in the UC objective for integer clusters; markup zeroed on them; fast-start CTs keep the markup | 19 |
| no-load cost | absent | paid in the UC objective (measured CAMPD regression) | 13, 21 |
| min-load | `min_gen` floors (floor mechanisms) | whole-unit floor when on; floors the UC replaces are refused at validation | 19 |
| online capacity for reserves | every available MW | online MW only (the online gate the reserve rows say "needs an online binary") | — |
| uplift | none | reported sidecar (make-whole), never in the LMP | — |
| year isolation, one pass, 8760 | yes | yes: windows sequential inside one year, one shard per ISO-year | 10, 12, 36 |

Rejected forms and why: P1 as a year-long MILP (intractable, no duals); DA/RT two-settlement rebuild (months of engine work; this stage *is* the DA half and leaves the door open); integer posture in-LP (pools are capacity, not unit counts; still year-long). Details: `ASSESSMENT` §4.

## 2. What changes where

| Area | Change | Touched? |
|---|---|---|
| `model/lp/*` (layout, bounds, costs, rows, reserve_rows, model) | **untouched** — the window builder *calls* the existing vectorized block builders on a T-slice | no |
| `model/uc/` (new) | `params.py` (cluster struct-of-arrays: n, p̄, mlf, start $/MW, no-load $/h, UT, DT, integer flag), `window.py` (slice + integer columns + logic/min-up/min-down rows, kron-vectorized), `solve.py` (HiGHS MILP, warm start, gap/time log), `schedule.py` (stitch windows → `u[c,t]`), `uplift.py` | new |
| `pipeline/uc.py` (new) | `build_uc_p1_prep(config, fleet, fleet_arrays, mc_base, mc_bid, r0) -> p1_fleet_prep hook`; boundary extraction from `r0`; the markup zeroing for integer clusters | new |
| `pipeline/solve.py::run_energy_solve` | one hook registration after the markup step; byte-identical when the gate is off | 1 hunk |
| `pipeline/commitment.py::_bridge_floored_fleet` | reused as-is for the floor/ceiling injection | no |
| `data/floor_mechanisms.py` | `MECH_UC_SCHEDULE = 28` + name + ablation entry | small |
| `config/scenarios.py` | the fields in §6; validators refusing stacks (bridges, posture) | small |
| `config/solve_surface_declared.py` | append-only declaration via `solve_surface_register.py --declare` | generated |
| `scripts/data/derive_uc_cluster_params.py` (new) | frozen derive (rule 23) of cluster physics from CAMPD/ASOM/NREL/DAM sources; writes `data/clean/uc-params/<ISO>` under the data contract (`/data-intake`) | new |
| `scripts/probes/_ucmilp_compose_span.py` (new) | ISO-parameterized copy of `_miso260_compose_span.py` (no partition) | new |
| `scripts/lib/uc_bench.py` + `scripts/diagnostics/bench_uc_ladder.py` (new) | the wallclock ladder on the captured LP (`bench_cold_solve.py` seam) | new |
| bundle sidecars | `hourly/uc_schedule_<y>.parquet` (int8 `u`, `n`, cluster labels), `uc_solve_log.json` (per window: build s, MILP s, nodes, gap, time-limit hit, integers, columns), `hourly/uc_uplift_<y>.parquet` | new |
| `docs/codebase-site/data/mechanism-matrix.js` + every `mechanism-matrix/<ISO>.js` | row `unit_commitment_milp` (+ sub-field rows) with a cell per ISO (`U` at birth) | CI-enforced |
| `tests/` | toy UC tests (1 cluster, 1 zone, 24 h; min-up/min-down; warm start; no-load decommit), off-gate byte-identity, injection bounds; one `slow` window test on a captured LP | new |
| `CLAUDE.md` "Dispatch and commitment", spec §1.6/§1.9 | the amendment (§7), landed only on ruling D-1 | owner |

## 3. Phases

| Phase | Lane(s) | LP | Deliverable | Exit gate | Owner card |
|---|---|---|---|---|---|
| **UC-0 charter + benefit screen** | desk + 1 research lane (zero LP, `DATA PROFILE: code` + the keeper bundles) | 0 | the ranked 9 × 7 board of commitment-state exposure (`GATESPEC` §1–2), cluster census per ISO, rule-19 floor census per ISO, DOF ledger draft | board published; top 3 ISO-years + 2 controls named ex ante | **D-1** amendment ruling; D-0 charter |
| **UC-1 engine + ladder** | 1 engine lane (Opus/Fable; `src/` + tests + matrix row + derive); bench shards | ladder only (1 window → 1 month → 1 year), on the top-ranked ISO-years and NEISO | the gated stage, default-off, byte-identical off; `uc_solve_log.json`; the wallclock table (`GATESPEC` §3) | fast tests green; off-gate byte-identity on every ISO's keeper recipe (zero-LP G-DRIFT audit + one golden replay per ISO in shards); L3 wall ≤ ceiling | **D-2** wall ceiling; D-3 pricing treatment |
| **UC-2 A/B, full span** | per-ISO lanes (one PRECOMMIT each), one shard per ISO-year | 7 per ISO | composed span bundles, `calibration_verdict`, `legitimacy_diagnostics`, RESULT with the pre-fixed readings (`GATESPEC` §4) | readings answered; no PASS→FAIL flip in controls; D-2 attribution under MECH 28 | **D-4** rule-20 treatment; D-5 rule-19 census outcomes |
| **UC-3 forecast parity** | 1 lane | 1 shard (NEISO forecast span) | forecast dashboard registration (`register_forecast_run.py`); wall and invariant table | forecast invariants hold; wall reported | — |
| **UC-4 promotion** | desk slot, one ISO at a time | 0 (bundles from UC-2 are promotable: full bundles pushed, rule 34) | `promote_keeper.py` per ruling; matrix cells; `/sync-docs` for spec §1.6/§1.9 | per rule 35 | **D-6** per ISO |

Sequencing rule (as the close-out desk's): **rulings first, zero-LP censuses second, shards last**; no full-span shard before the ladder has printed the wall for that ISO.

## 4. Efficiency design — "glean the MILP's benefit at the least wall clock"

| # | Lever | What it does | Measured by |
|---|---|---|---|
| E1 | **integer set by physics** | only slow-start clusters carry `u` (pool min-down > 2 h or start ≥ $30/MW — the posture gate inverted, rule 18); CTs, renewables, storage, hydro, nuclear (must-run), CHP (steam floors) stay continuous | integer count per window in the log |
| E2 | **rolling DA window** | 24 h commit + 12 h look-ahead (declared fields); 365 small MILPs instead of one of 8760 h; faithful to DA SCUC's horizon | windows × mean MILP s |
| E3 | **warm start** | previous window's incumbent shifted 24 h + P0 dispatch for the new tail (`setSolution`); root LP basis from the previous window | nodes per window; share of windows at 0 nodes |
| E4 | **tight, compact formulation** | clustered integer counts (not binaries per unit), Rajan–Takriti min-up/down, `v`/`w` continuous; gap 1e-3 declared | root gap p50/p95; nodes |
| E5 | **reachability pre-fixing** (conservative) | clusters P0 ran at full output through the window with margin ≥ max start+no-load are fixed on; clusters with `mc` above the window's max P0 dual by a margin are fixed off; the margins are declared constants, and the log records the count fixed | integers removed; post-hoc check that no fixed-off cluster would have been in-merit |
| E6 | **incremental model** | one HiGHS model per window *shape*; successive windows update bounds, costs and RHS (`changeColsBounds`, `changeColsCost`, `changeRowsBounds`), never rebuild | build s per window |
| E7 | **threads** | measured, not assumed (the solve container pins `MARKET_SIM_HIGHS_THREADS=1`; HiGHS MIP parallelism is limited) | wall at 1 vs 4 threads on the ladder |
| E8 | **P1 unchanged** | the pricing pass stays the existing warm-from-P0 LP; the UC adds bounds only | P1 s vs baseline |
| E9 | **checkpointing** | the schedule is written per completed month so a shard near its budget always has an artifact (rule 32 stop rule) | — |
| E10 | *contingency* month-parallel UC sub-shards | only if L3 exceeds the ceiling after E1–E7; **needs a rule-36 amendment** (one year, one container) | owner card |

Acceptance bars proposed for D-2: **efficient** = UC stage ≤ 1.5× the ISO's baseline P0+P1 wall; **ceiling** = ≤ 3×; above the ceiling the stage does not arm for that ISO until E10 or a wider window (48 + 24 h, 183 windows) is measured.

## 5. Formulation (per window; the existing blocks sliced, plus the lines marked NEW)

```
min  Σ_t [ Σ_g mc_g,t·P_g,t + ε·(Chg+Dis) + dis_cost·Dis + VOLL·Slack + dump_cost·Dump + reserve terms ]   (existing, sliced)
     + Σ_c Σ_t [ SU_c·p̄_c·v_c,t + NL_c·u_c,t ]                                                             NEW: start $, no-load $/h
s.t. energy balance, flows, storage SOC, renewables, reserve rows, ramp envelopes                          (existing, sliced)
     mlf_c·p̄_c·a_c,t·u_c,t ≤ Σ_{g∈c} P_g,t ≤ p̄_c·a_c,t·u_c,t                                             NEW: output coupled to units on
     u_c,t − u_c,t−1 = v_c,t − w_c,t                                                                      NEW: logic
     Σ_{k=t−UT_c+1}^{t} v_c,k ≤ u_c,t ;   Σ_{k=t−DT_c+1}^{t} w_c,k ≤ n_c − u_c,t                           NEW: min-up / min-down
     u_c,t ∈ {0,…,n_c} integer ; v, w ≥ 0                                                                 NEW: integer set = E1
     boundary: SOC_end, cascade levels = P0's; initial u, hours-on/off, ramp state = window w−1
mc: integer clusters at mc_base (their start/no-load are explicit); every other unit at the P1 bid (markup included)
keep the first 24 h of u; advance 24 h
```

Parameter sources (all measured or published, zero fitted; DOF ledger drafted in UC-0): start $/MW — NREL SR-5500-55433 class tables already in `constants.py` (`CC_COMMITMENT_PARAMS`, `BIN_STARTUP_COST_PER_MW`), PJM `energy-offers` hot/cold start (class-level); no-load $/h — CAMPD `heatInput = a + b·grossLoad` intercept × delivered fuel (PJM decommit B0 PASS, R² 0.96–0.98; class table fallback where no CAMPD unit matches), PJM `energy-offers` `no_load_cost_usd_per_h` as the cross-check; mlf — ERCOT 60-Day DAM LSL/HSL (0.574), CAMPD WP-3 reconstruction per ISO (`campd_gas_commitment_params_<ISO>.csv`), `MIN_STABLE_PCT_PHYSICAL`; UT/DT — CAMPD run-length percentiles, SPP ASOM, the ERCOT per-plant CSV.

## 6. Registry, governance, tests

| Item | Requirement | Where |
|---|---|---|
| fields | `unit_commitment_milp` (gate), `uc_window_hours` 24, `uc_lookahead_hours` 12, `uc_mip_rel_gap` 1e-3, `uc_window_time_limit_s` (from the ladder), `uc_integer_scope`, `uc_noload_source`, `uc_boundary_mode`; all default off/declared; per-ISO arm later via `iso_configs` overrides + `--no-unit-commitment-milp` | `scenarios.py`; rule 5, 24 |
| cache key | each field in `_CACHE_KEY_OPTIONAL_FIELDS` with its declared default (CI `check_cache_key_registration`) | `scenarios.py` |
| solve surface | `solve_surface_register.py --declare` for the new tables (append-only) | `solve_surface_declared.py` |
| matrix | row `unit_commitment_milp` + one cell line per shard (`U`), same PR (CI `check_mechanism_matrix --base`); the `R` cells on `online_capacity_envelope` / `spp_commitment_posture` are **not re-tested** — integer state is a different object (rule 28) | `mechanism-matrix.js`, `mechanism-matrix/<ISO>.js` |
| rule 19 refusals | `unit_commitment_milp` + any `*_gas_commitment_bridge`, `*_commitment_posture`, `caiso_ra_mustoffer` → validation error; markup zeroed on integer clusters | `scenarios.py` validators |
| D-2 | `MECH_UC_SCHEDULE = 28`, named, with an ablation entry; rule-20 treatment per D-4 | `floor_mechanisms.py`, `legitimacy_diagnostics.py` |
| tests | fast: toy UC (1 cluster/1 zone/24 h; no-load → multi-hour off; UT/DT; warm start accepted; integer-empty UC ≡ LP), off-gate byte-identity (goldens), injection bounds; `slow`: one captured-LP window | `tests/unit/model/uc/`, `tests/golden` |
| CI | lint, fast tier, repo checks, file-integrity guard (no core file shrinks) | existing workflows only; **no new workflow, no CI solve** |
| keeper hygiene | `promote_keeper.py` preflight learns the three sidecars at UC-4 | rule 15/35 |
| docs | spec §1.6 rewritten by `/sync-docs` after UC-1 merges; `docs/codebase/` module page for `model/uc/` | rule 11 |

## 7. The amendment the program needs (copy-paste for the owner's ruling; lands in its own PR on D-1)

```
CLAUDE.md, "Dispatch and commitment (per year)" — replace
  "P0 base-cost → P1 bid-cost are the only two passes; P1 is the run everything is scored on. Pure LP, no MIP."
with
  "P0 base-cost → [UC] → P1 bid-cost; P1 is the run everything is scored on and is a pure LP (prices are its
   duals, rule 4). The optional UC stage (`unit_commitment_milp`, default off, ISO-armed) is a rolling-horizon
   MILP over the year that chooses the commitment of slow-start clusters (rule 18 physics) and enters P1 only
   as per-unit-hour bounds (MECH 28); it replaces the commitment bridges and the posture family wherever it is
   armed (rule 19), pays start and no-load cost once (markup zeroed on its clusters), and reports uplift as a
   sidecar, never in the LMP. No other pass is a MIP."
model-methodology-spec.md §1.6 first paragraph and §1.9 bullet "Pure LP. No MIP, no binary variables." —
  same substitution; §1.9 keeps "Prices are LP duals" unchanged and adds: "The UC stage is the only mixed-integer
  program in the model; it never prices."
docs/governance/rule-history.md — new entry: "Dispatch and commitment — the MILP UC stage (owner, <date>)",
  owner instruction verbatim, what the sentence said before, what it says now, what is KEPT (rule 4, the stack rule,
  the P0/P1 shape, every keeper unchanged), enforcement (validators + matrix row + CI).
```

Why this is safe to sign: the stack rule is untouched (direct CSC → HiGHS); no keeper changes; the stage is default-off and byte-identical off (tested); duals stay available everywhere because the MILP never prices.

## 8. Owner decision queue

| ID | Decision | Options (recommendation first) | When |
|---|---|---|---|
| **D-0** | Charter the program and the desk as written here | charter · charter with changes · decline | now |
| **D-1** | Amend "pure LP, no MIP" per §7 | sign · sign with edits · do not sign (program stops at UC-0's board, which is still useful) | before UC-1 |
| **D-2** | Wall-clock bars | efficient ≤ 1.5× / ceiling ≤ 3× of baseline year wall · other numbers | after UC-1 L3 |
| **D-3** | Pricing treatment of integer clusters | restricted pricing + uplift sidecar (markup zeroed) · keep amortized markup on them (ELMP-like) as a declared variant | before UC-2 |
| **D-4** | Rule 20 and UC min-load energy | reported under MECH 28, not budgeted (the LP chose it, as the posture precedent) · budgeted like a floor | before UC-2 scoring |
| **D-5** | Rule-19 census outcomes per ISO | which existing floors the UC replaces beyond the bridges and posture (coal conduct floors are the hard case) | per ISO, before its PRECOMMIT |
| **D-6** | Promotion per ISO | promote on structure · record `R`/`I` with evidence · hold | after each UC-2 RESULT |

### 8.1 Rulings (verbatim, numbered; desk-recorded, never re-litigated)

| # | Card | Date | Ruling (owner's words / selected option, verbatim) | Recorded by |
|---|---|---|---|---|
| R1 | D-0 | 2026-10-03 | "Charter (Recommended)" — program and desk chartered as written | UC-DESK r01 `session_01WX9W5tgYMre3Z134LZoGF6` (decision card) |
| R2 | D-1 | 2026-10-03 | "Sign §7 text (Recommended)" — the §7 amendment, as written, lands in its own PR (a lane owning `CLAUDE.md`, spec, rule-history; not the desk) | UC-DESK r01 `session_01WX9W5tgYMre3Z134LZoGF6` (decision card) |

## 9. Roadmap and cost

| Wave | Content | Shards | Wall (container-hours, order) | Exit |
|---|---|---|---|---|
| 0 | D-0, D-1; UC-0 board + censuses | 0 | 0 | board published, D-1 ruled |
| 1 | UC-1 engine PR (default-off, tests, matrix row); off-gate golden replays | 9 (one keeper replay per ISO, pinned recipe, byte-compare) | ~3 | byte-identity proven on every ISO |
| 2 | ladder on the top 3 ISO-years + NEISO control: L1+L2 in one bench shard, L3 in a second | 8 | ~6 | wall table printed; D-2 ruled |
| 3 | UC-2 A/B full span on the 2–3 ISOs the board and ladder clear (+ NEISO regression span) | 14–28 | ~10–30 | RESULTs with pre-fixed readings |
| 4 | UC-3 forecast parity (NEISO span) | 1 | ~1–3 | invariants hold |
| 5 | UC-4 promotions, one slot at a time; `/sync-docs` | 0 | 0 | keeper(s) carry the stage or cells read `R`/`I` |

## 10. Risks (full list `ASSESSMENT` §9)

Wall above the ceiling for PJM/MISO (E10 is an owner decision); a passing control year moving (pre-fixed no-flip bars arm the stage per ISO only); boundary approximation for storage (reported, alternative mode tested only if shown); stacking with a conduct floor (per-ISO census, refusals); the benefit being in form only (then the cells read `I`/`R` honestly and the stage stays default-off — the program still delivers the structural capability and the forecast realism).

## 11. Desk log (append-only; one line per sitting: date · desk session · main HEAD · what was chartered or ruled)

- 2026-10-03 · planning session `session_01A2fEZSxeS8xbpDUPLQhDHD` · main `dd28b645` · plan, assessment, gate spec, charter and handoff written; no lane chartered; awaiting D-0/D-1.
- 2026-10-03 · UC-DESK r01 `session_01WX9W5tgYMre3Z134LZoGF6` (Opus by owner instruction) · branch `claude/ucmilp-desk-r01` · main `8e4b87ab` · gates: audit_keepers PASS (0 fail, 4 warn), registry/payload parity OK (9 runs), mechanism matrix ratchets OK, cache-key registration OK (409/409), rubric freeze OK (diff modes not run: no base) · **ruled D-0 = charter (R1), D-1 = sign §7 (R2)** · chartered UC-0 (benefit screen, zero LP) · amendment lane UC-AM (D-1 PR) named for next sitting · no shards.

## 12. Lane register (desk-maintained; one row per chartered lane, newest last)

| Lane | Session | Branch (issued stem → realised) | Scope (plan ref) | LP | State |
|---|---|---|---|---|---|
| UC-0 benefit screen | `<UC0_SESSION>` | `claude/ucmilp-0-benefit-screen-tx8t` → *(unrealised; dispatch unconfirmed until a branch exists)* | §3 UC-0; GATESPEC §1–2; HANDOFF B | 0 | chartered 2026-10-03 (Fable) |
