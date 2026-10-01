# PRECOMMIT miso-232 — the HOURLY neighbour-anchored PJM seam ladder, FULL SPAN under OWNER RE-CHARTER

**Written and pushed while the full-span LP runs, before any year's bundle is opened.**
Every bar, comparator, non-claim and the G-DRIFT classification below is fixed here so
nothing can be written to fit a result.

**KEEPER (the control, rule 29(b) form 4): `2026-09-06-miso-230-ctdrag-seam`**
(`miso230_ctdrag_seam_K`, git sha `284722a04`), CALIBRATED, C3c the single ledgered
caveat. Rule 22: **2023–2025 only**; MISO holds no `complete` marker, so no holdout year
is solved, scored or registered. DOF ledger **41/2, unchanged** — the mechanism adds no
free parameter (miso-231 PRECOMMIT §2: every `delta_k` is a quantile of a measured
series at a structurally fixed depth grid, derived and frozen under rule 23).

---

## 0. THE SCREEN DID NOT CLEAR ITS GATE. The span is solved under OWNER RE-CHARTER.

This is stated first because it is the fact a promotion would tempt a write-up to
soften. miso-231's screen (`FINDING-miso231-hourly-seam-screen-2026-09-06.md`) was
**KILLED on G-1 by 0.0183**: the pre-registered bar (Addendum A.1, fixed before any arm
number existed) required `corr(imports, own model hub price)` to fall **≥ 0.30** from
the keeper's own 2024 **+0.4461**; the measured fall was **0.2817** (+0.4461 → +0.1644).
Rule 29 `[R-SCREEN]`'s screen is a STOP gate, miso-231 correctly refused to move it,
and the remaining years were not spent.

**The owner re-chartered the full span anyway**, under the standing steer of 2026-09-06
(*"if structural integrity improves but gates regress that may still be a keeper"*).
That steer IS rule 29(2)'s owner step, and miso-231's PRECOMMIT §5 pre-registered
escalation for exactly this outcome. **The grant is: solve the full span.** It is NOT a
finding that the gate passed and it does NOT retroactively lower the bar. Every write-up
this session produces states, in place: *the screen failed G-1 by 0.0183 and the span
was authorized by owner re-charter.*

**Why the owner re-chartered — recorded, not re-argued.** On the miso-225/226 PUBLISHED
comparator basis (deciles and correlation of the MEASURED Indiana hub price, which every
prior seam comparator on record uses) the 2024 arm landed on the measured value:

| statistic, 2024 | keeper | arm | MEASURED |
|---|---:|---:|---:|
| corr(imports, measured hub price) | +0.3211 | **−0.0636** | **−0.039** |
| price-decile slope d1−d10 | −3,321.6 MW | **+111.2 MW** | **+1,384 MW** |
| corr(imports, own model price) — the G-1 basis | +0.4461 | +0.1644 | (−0.101, 2023 ref) |

The decile slope **changed sign** — 100 % of the sign error closed where miso-226's
annual form closed 10 %; no arm on record had flipped it. G-3 PASS (slack 0.0196 →
0.0196 TWh, dump 0.0000 both; wind/solar/nuclear/hydro unchanged to 0.00 TWh). G-5
PASS, cheap-hour imports 2,129.3 → 3,321.6 MW (+1,192 against a ≥ +150 bar, vs the
annual form's +581). Six of nine fossil C1 cells moved toward actual, CT_PEAKER −2.21 →
−1.13 among them.

## 1. The command — single delta on the keeper recipe, ONE invocation, ONE bundle (rule 16)

```
MARKET_SIM_HIGHS_THREADS=4 python3 scripts/replay_keeper.py \
  results/calibration/miso230_ctdrag_seam_K --years 2023 2024 2025 \
  --out-dir results/calibration/miso232_hourlyseam_K \
  --set miso_seam_neighbour_hourly_ladder=true \
  --note "miso-232 full span: HOURLY neighbour-anchored PJM seam ladder"
```

Years run sequentially within the invocation (rule 12). The bundle's `run_config.json`
is the keeper's with exactly one field moved.

## 2. G-DRIFT (rule 29(b)) — extended from `284722a04` over everything main added. **ALL INERT. Form 4 holds. NO control solve.**

```
git diff --stat 284722a04 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source \
    data/raw/reference
```
= 18 files, +1,864 / −69. miso-231 §4b audited this through the branch, and Addendum B
through `origin/main 6f074049` (the one solve-path mover, ercot-251's
`_renewable_bound_is_delivered_pinned`, gated `iso == "ERCOT"` + ERCOT-only flags).
**What main added after `6f074049`, through this session's base `b6f690bf`** — four
files, +108 / −31, every hunk classified:

| changed area | class | reason |
|---|---|---|
| `scripts/run_calibration.py` (−31/+8) | **INERT** | REVERTS the ercot-251 helper back to the `load_hsl_hourly(iso, year) is None` test at the same two call sites; both remain inside `if getattr(config, "ercot_gtc_limits_measured"/"ercot_wtx_curtailment_driver", False) and iso == "ERCOT"` — another ISO's branch (rule 25) |
| `src/market_sim/config/constants.py` (+1) | **INERT** | an added re-export `PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE` from `config.capacity_market`; an import line, PJM capacity-market constant, no MISO reader |
| `src/market_sim/config/iso_configs.py` (+67) | **INERT** | `_pjm_config` `default_scenario_overrides` arms `pjm_vre_accreditation_vintage` (capx D75-R-ARM, owner ruling Q55) — a PJM ISOConfig override a MISO config never reads; the field itself is forecast-path (capacity accreditation) and the shared `ScenarioConfig` default stays `False`, so no MISO key moves |
| `src/market_sim/results/cache.py` (+32) | **INERT** | cache-epoch docstring ledger entry for the same D75-R arm; no code |

**Measured, not asserted:** `surface_stamp("MISO", ScenarioConfig(iso="MISO",
mode="backcast"))` at this session's HEAD reads `moved: {}`, `epochs: []` — MISO's
solve-surface fingerprint and cache key are byte-identical to the keeper's.

**Conclusion: the keeper's committed bundle IS the control (form 4). No control solve is
spent.** Recorded before any year of the arm completed.

## 3. Scoring and the promotion rule (miso-227's, unchanged)

`scripts/calibration_verdict.py` on the registered run (rule 15, `calibration-report`
skill). **Promote on CALIBRATED / CALIBRATED-WITH-CAVEATS; on a LOAD-BEARING NOT-YET,
report and escalate to the owner rather than decertifying the ISO.** All six ISO keepers
currently read CALIBRATED.

## 4. What the full span must watch — named in advance from the 2024 screen

- **G-4 collateral was NEVER SCORED at the screen** (§6 below), so this is the first look
  at 2023 and 2025 collateral. The named risk is **CT_PEAKER**: the mechanism
  REDISTRIBUTES rather than adds (2024 annual imports 31.29 → 29.75 TWh while cheap-hour
  imports rose +1,192 MW), so energy leaves the expensive hours — and CT_PEAKER-2023 at
  ±8.00 is the cell miso-227 died on. The keeper sits at **−4.32** there, ~3.7 TWh of
  headroom. Checked FIRST when the bundle lands.
- The two adverse 2024 cells, re-checked in every year: **ST_GAS** (+1.35 → +1.78) and
  **CC_CHP** (−15.70 → −15.93). C3a 2024 moved +2.9 % → +4.2 %, inside ±10 %.
- **2025 C1 is SKIPPED** on the preliminary EIA-923 vintage (every gas and coal class),
  and C2 skips 2025 too. A 2025 C1 pass is not evidence and is not read as such.

## 5. Pre-committed NON-CLAIMS — carried onto the determination basis if it promotes

1. **The decile slope is repaired in SIGN, not in magnitude** (+111 MW against a measured
   +1,384 in 2024). A partial repair, and it says so.
2. **C3c is UNTOUCHED.** No scarcity claim of any kind is made; C3c stays the designated
   frontier (2026-07-20), opened only by a NEW admissible measured identification under
   its own charter, never an offer adder tuned to the tail.
3. **G-2 (annual volume) was WITHDRAWN as a gate, not passed.** Imports FELL 1.54 TWh in
   2024. The annual import move is reported at full magnitude in every year.
4. **The screen failed G-1 by 0.0183.** The span exists by owner re-charter.

## 6. The G-4 defect, fixed in passing — `scripts/screen_collateral_gate.py`

miso-231 found G-4 unscorable: `calibration_verdict.py` resolves only a REGISTERED run
and rule 29(2) forbids registering a screen bundle, so only three of five gates were
live — a hole in every future screen for every ISO. The new standing tool runs **the
same scorer in memory** on an unregistered bundle: the payload is assembled exactly as
`dashboard_add_run.py` / `render_backcast.generate` assemble it at registration and
round-tripped through the `runs/<id>.js` codec; the bench (actuals) side is the
COMMITTED per-(ISO, year) parts the keeper's verdict reads, held fixed; nothing is
written under `frontend/`. It compares record-by-record against the keeper's committed
verdict — a flip is PASS→FAIL on C1 / C2 / C3a / C3b / C6, C3c excluded; every other
move is reported, never gated; an unattested C6 is "not scorable at a screen", not a
flip. STOP-only by construction (exit 1 on a flip; nothing it prints is a
determination). Unit-pinned in `tests/scoring/test_screen_collateral_gate.py`.

It is exercised on this session's arm bundle before registration, so the record shows
the 2023/2024 collateral the screen could not, from the same instrument a future screen
will use.

## 7. Already settled — not re-opened here

The COAL D-1 regression (attributed and closed without a build, miso-231; rule 28(a)
DO-NOT-REDO binds); `ct_mustrun_per_plant` (refused, rule 13); the CT_PEAKER offer
level (closed by `ct_netload_drag`); MISO's drag window `[10,21)` (frozen, rule 23);
the `delta_k` spread ladder (derived and frozen, zero DOF — never re-derived, re-tuned
or swept); C3c (frontier, no LP spent here).

## 8. Governance

Rule 1 `[R-STRUCT]`: the screen bar is not moved; the span is an owner step, stated as
such. Rule 13 `[R-MEASURED]`: the hourly border price is a purchased-input price with a
forward analogue already in the code (miso-231 §1). Rule 15: registered on the
dashboard in this session, keeper-only retention applied on a promotion. Rule 16: one
invocation, one bundle, all three years. Rule 19 `[R-ONE-MECH]`: displaces the annual
overlay, never stacks. Rule 21 `[R-DOF]`: ledger 41/2. Rule 22: 2023–2025. Rule 23: no
derive re-run. Rule 28(b): the `seam_neighbour_hourly_ladder` MISO cell is updated in
this session, promotion or rejection alike. Rule 29: phase 0, the screen and G-DRIFT
all precede this; the keeper is the control; no control solve.
