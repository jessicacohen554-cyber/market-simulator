# B-0 owner decision memo — seeding the cold-rebuilt P1 from the same year's P0 basis (wallclock plan §6)

**STATUS: DECISION INPUT — for the owner. Wave 2a (`claude/wc-b-p1-basis-seed`) is gated on
the signature line at the end of this memo.** Written 2026-09-05 by B-0
(`claude/wc-b0-p1-seed-memo-9euk97`, main @ `2886235c`), chartered by the WALLCLOCK desk
(`docs/handoffs/wallclock-desk-log-2026-09.md` §2.2, wave 1f): *"the plan-§6 memo for seeding
the cold-rebuilt P1 model from the same year's P0 basis … the owner cannot sign a flip memo
without the number, and the wave-2 implementation is gated on the signature, so the
measurement is yours."* The lever is item B of
`docs/handoffs/wallclock-opportunities-2026-09.md` (§3, ranked #4 in §5); this memo supplies
the measurement that doc's `<!-- ERCOT_BENCH_TABLE -->` placeholder was waiting for, and the
same PR fills that placeholder and adds the doc's §6.3 bench record.

**Ground rules this memo lives under.** Wall-clock only: the LP, its objective, bounds and rows
are untouched, and the change is classed **WARM-START CLASS** (gate:
`scripts/diagnostics/diff_warmstart_bundles.py`, marginal-tie only, owner memo before any
default flips) — it cannot be proved on `regression_gate.py --mode byte`, which is exactly why
it needs this memo. **No repo code was changed to measure it**: the seeded arm ran through a
scratch monkeypatch driver (§3.1) that was never committed. No `ScenarioConfig` default, keeper
shard, marker, matrix shard, registry or workflow is touched; nothing is promoted or
dashboard-registered; the two probe bundles were deleted after the diff.

---

## 0. The decision in one paragraph

On the three ISOs whose keeper carries a P1-native floor bridge — **ERCOT** (gas commitment
bridge), **NYISO** (gas commitment bridge), **CAISO** (RA must-offer) — the P1 pass cannot
re-cost the live P0 model in place, so `run_energy_solve` builds a **second `DispatchModel`**
for P1 and solves it **with no starting basis at all**, even though the P0 model of the same
year has the identical column/row layout and an optimal basis in hand. The proposal is to hand
that basis to the second model through the shipped `apply_cross_year_basis` before its first
solve. Nothing about the floored LP changes; only the simplex starting point does. Measured on
the ERCOT forward keeper config, 2025, under the determinism pin (§3): `solve_p1`
**{{P1_OFF_S}} s → {{P1_ON_S}} s** ({{P1_X}}×), simplex iterations **{{P1_OFF_IT}} →
{{P1_ON_IT}}**, objective and total generation {{NEUTRAL_HEADLINE}}. The owner's choice is
§7: flip the calibration-CLI default ON (opt-out flag, env var honored, goldens pin keeps it
off), or do not flip.

## 1. What changes — the simplex starting point, nothing else

**The route today** (`src/market_sim/pipeline/solve.py::run_energy_solve`, the cold-P1
branch). A `p1_fleet_prep` floor (the bridge) or a `p1_kwargs_prep` override replaces the P1
fleet / kwargs. The in-place refloor (`lp.inplace_floor.refloor_thermal_inplace`) is tried and
**declines on every ERCOT keeper year**, because the bridge's availability raise also feeds
reserve-headroom / pool-cap / ramp *row* bounds (the log line on both arms of this bench:
`P1 route: COLD REBUILD on a floored fleet — MARKET_SIM_P1_FLOOR_INPLACE off (default); would
have been DECLINED anyway (availability changed and feeds a row)`). So the branch exports the
P0 basis into the cross-year holder *if* `_xwarm` is armed, sets `model = None` to release
the P0 workspace, and calls `solve_dispatch(p1_fleet_arrays, demand, mc=mc_bid, …)` — which
builds a fresh `DispatchModel` and runs HiGHS from scratch.

**The change.** In that same branch: export the P0 model's basis **before** `model = None`
(the export already exists there for the cross-year holder; the seed reuses it), build the
second model exactly as today, call `model.apply_cross_year_basis(basis)` on it, then solve.
Same `T`, same `unit_ids`, same zones/storage/links, so `_cross_year_column_map` is the
**identity** on every per-hour block; HiGHS loads it as an *alien* basis and repairs the few
statuses the bridge's raised availability makes bound-inconsistent. That is the machinery
D-9/P-2 already ship for *adjacent* years (`docs/cross-year-warmstart.md`), applied to the
one place in a year it was never reached.

**What it is not.**
- It is **not C-4** (the refuted in-place refloor): no live model is edited; the cold rebuild
  stays byte-for-byte what it is today. The seed is added *after* the rebuild.
- It is **not an LP change**: objective vector, bounds, rows and coefficients of the second
  model are identical on both arms — the P0 solve, the markup, the bridge floors and the
  second build are all upstream of the seed and untouched by it (the P0 records of the two
  arms in §3.2 are the built-in check: iterations, objective and `solve_time` agree).
- It is **not a new tunable**: an LP's optimum is basis-independent, so a wrong or partial seed
  costs iterations, never correctness (`cross-year-warmstart.md`, "Key structural fact").

**One honest note on how much of the basis is copied.** The shipped
`apply_cross_year_basis` copies every column status and the two row families it can identify
across years — the energy-balance rows and the storage-SOC rows — and defaults every *other*
row (reserve, ramp, pool caps, interface groups, …) to basic-slack. For a same-year seed the
row sets are identical and a full 1:1 row copy is possible; **this bench used the shipped
method as-is**, so §3 measures the conservative form. A same-year full-row copy is a possible
tightening for wave 2a, gated exactly like the seed itself; it was not measured here and no
number in this memo depends on it.

## 2. Who pays today — the cold-P1 keepers, and the P1 ≈ P0 signature

The signature of a cold P1 is that it costs about as much as P0. On the warm-P1 ISOs it costs
~0.3–0.4× P0. From the anchor tables on record (all determinism-pin keeper replays):

| keeper | why P1 is cold | `solve_p0` / `solve_p1` on record | source |
|---|---|---|---|
| ERCOT `2026-09-05-ercot248-two-config-keeper`, forward config (2024/2025; registered 3-year) | `ercot_gas_commitment_bridge` raises availability; feeds reserve/ramp rows → refloor declines | 2023: 398.6 / **762.0** (two passes); 2024: 446.3 / **715.3** (two passes); 2025: 524.0 / **351.3** (one pass after C-1a) | `docs/FINDING-perfb-s3-adaptive-pass-2026-09.md` §5 (shipped tree) |
| ERCOT same keeper, carve-out config (2023) | same bridge | 381.1 / **795.4** (two passes) | same |
| ERCOT ercot213 recipe (pre-s3 anchor) | same bridge | 473.0/416.7/416.1 vs **447.1/321.8/344.8** | `wallclock-baseline-2026-07.md` §PERF-B anchor |
| NYISO `2026-09-05-nyiso-192-astoria-panel` (nyiso-140 recipe anchor) | `nyiso_gas_commitment_bridge` + co-opt + ramp | 180.1/149.5/97.7 vs **170.7/172.7/99.7** | same anchor |
| CAISO `2026-09-05-caiso-251-b1-nomargin` | `caiso_ra_mustoffer` (default-on) → same cold route | not in any anchor table; route confirmed from the code path, not a timing line | `pipeline/solve.py` P1 route |
| NEISO / PJM / MISO | no bridge — P1 re-costs the live model | NEISO 105.8/104.1/114.1 vs **43.3/35.0/36.1** (0.3–0.4×) | same anchor |

Two readings of the table. First, on ERCOT and NYISO the P1 pass is a **full second cold
solve per pass** — and on the ERCOT adaptive years (2023/2024, and the carve-out) there are
*two* such P1 solves per year (C-1b removed the second P0, not the second P1). Second, the
ERCOT 2025 P1 (351 s against a 524 s P0) is the one-pass year, which is why the desk named
it for the bench: it is exactly the two-HiGHS-run year C-1a reduces to, so the seed's effect is
read off one P1 run with nothing else moving.

## 3. The measurement — ERCOT forward config, 2025, seed OFF vs ON

### 3.1 Conditions

- **Config and year.** Capture key `ERCOT__forward` resolved through
  `capture_keeper_goldens.resolve_capture_targets` → keeper
  `2026-09-05-ercot248-two-config-keeper`, bundle
  `results/calibration/ercot248_two_config_keeper` (its `meta.json` carries the FORWARD
  config; 2025 in the composite was solved by `2026-08-25-234-eastex-identity`);
  `build_solve_kwargs(meta, solve_and_persist)` → `solve_and_persist([2025], "ERCOT", 8760,
  …)`. Same driver mechanics as a golden capture, into a throwaway scratch dir — **never a
  golden, never registered**.
- **Determinism pin** on both arms: `MARKET_SIM_HIGHS_THREADS=1`, `MARKET_SIM_WARMSTART=1`,
  `MARKET_SIM_WARMSTART_XYEAR=0` (`capture_keeper_goldens.pin_determinism_env`). One ERCOT
  solve at a time; 6 GiB swapfile armed; 4 vCPU / 15 GB box; HiGHS 1.14.0 (`uv.lock` env).
- **Arms.** Both arms run the *same* scratch driver; the only difference is the `on`/`off`
  switch. The driver subclasses `DispatchModel` and rebinds the name in
  `market_sim.pipeline.solve` (the P0 model) and `market_sim.model.lp` (the model
  `solve_dispatch` builds for the cold P1). On **ON**: after the P0 model's first solve its
  basis is exported (`export_cross_year_basis`, the same export the shipped branch does before
  `model = None` when the cross-year gate is armed); the next model constructed applies it
  (`apply_cross_year_basis`, identity column map, `alien=True`) before its first solve. On
  **OFF** nothing is exported or applied — the shipped behaviour. Both arms log
  `simplex_iteration_count` and `objective_function_value` per solve from `HighsInfo`.
- **HEAD** `2886235c` (post-C-1a/C-1b/C-2), so 2025 is exactly two HiGHS runs per arm.

### 3.2 Speed — the P1 solve, the iterations, the phase lines

| arm | `solve_p0` s | P0 iters | P0 objective | `solve_p1` s | P1 iters | P1 objective | basis export s | basis apply s | year `total` s | maxrss GB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| seed OFF (shipped) | {{P0_OFF_S}} | {{P0_OFF_IT}} | {{P0_OFF_OBJ}} | {{P1_OFF_S}} | {{P1_OFF_IT}} | {{P1_OFF_OBJ}} | — | — | {{TOT_OFF}} | {{RSS_OFF}} |
| seed ON | {{P0_ON_S}} | {{P0_ON_IT}} | {{P0_ON_OBJ}} | {{P1_ON_S}} | {{P1_ON_IT}} | {{P1_ON_OBJ}} | {{EXPORT_S}} | {{APPLY_S}} | {{TOT_ON}} | {{RSS_ON}} |

{{SPEED_READING}}

Phase lines (the six frozen fields + the `markup` clause, verbatim from each arm's log):

```
{{PHASE_OFF}}
{{PHASE_ON}}
```

### 3.3 Neutrality — `diff_warmstart_bundles.py` + `hourly/system_2025.parquet` (the H2 shape)

Same standard the shipped cross-year warm start (P-2) and the persisted year-1 basis (H2) were
promoted under (`wallclock-baseline-2026-07.md` §H2; `cross-year-warmstart.md` "Bundle-level
gate"): objective and total generation identical; per-unit differences confined to marginal
ties; price differences confined to dual-degenerate hours.

| ISO-year | objective / total gen | max \|Δ zonal price\| | dual-degenerate hours | per-unit dispatch reshuffle |
|---|---|---|---|---|
| ERCOT 2025 (forward config) | {{NEUT_OBJ}} | {{NEUT_PRICE}} | {{NEUT_HOURS}} | {{NEUT_UNITS}} |

`diff_warmstart_bundles.py` fleet-wide block, verbatim:

```
{{DIFF_BLOCK}}
```

{{NEUTRALITY_READING}}

### 3.4 Verdict of the measurement

{{VERDICT}}

## 4. The neutrality class and its gate

This is the class every shipped warm start already lives in — intra-year (`MARKET_SIM_WARMSTART`),
cross-year (`MARKET_SIM_WARMSTART_XYEAR`, P-2), the persisted year-1 basis (H2) — and its gate
is the same one: a **single-bundle re-score**, cold vs seeded, diffed by
`scripts/diagnostics/diff_warmstart_bundles.py` and a price/served-load check on
`hourly/system_<year>.parquet`, passing iff

1. objective and total generation are identical (display-rounding 1e-7 relative is the
   documented allowance),
2. every per-unit annual/hourly difference is a marginal-tie swap with an offsetting partner
   (`total gen Δ = 0`), and
3. every price difference sits in a dual-degenerate hour (an equally-optimal clearing dual,
   never a level shift).

A seed that fails any of the three is not "a slower warm start"; it is a bug in the seam and
the arm is dead. What the gate does **not** do: it does not certify byte-identity, and it must
not be run as `regression_gate.py --mode byte` between a cold and a seeded bundle — that
comparison is expected to fail on marginal-tie rows and would say nothing. The byte gate's job
under this proposal is a different one (§5).

Rule 1 `[R-STRUCT]` is not engaged: the seed is a solver starting point, not a market
mechanism, and no residual, score or determination enters the gate. The P-2 flip was decided
on exactly this evidence shape (`cross-year-warmstart.md` "Bundle-level gate": ERCOT + MISO,
3-year, cold vs warm), and the desk's charter names the same standard for this lever.

## 5. What stays cold — the goldens/replay pin

Every reproducibility baseline (`scripts/capture_keeper_goldens.py`, `scripts/replay_keeper.py`,
the D-13 `bench-repro.yml` gate, the merge-base control captures the wallclock desk gates on)
pins `MARKET_SIM_WARMSTART_XYEAR=0`, so keeper goldens are **cold-vs-cold at one thread and
basis-independent**. The proposal keeps that invariant by construction: the seed is gated on
the same `_xwarm` gate the cross-year export already sits behind in the cold-P1 branch — under
`XYEAR=0` **no basis is exported and none is applied**, so the seeded tree is byte-identical to
today's tree on every golden, replay and control capture. That is the one thing the byte gate
*is* asked to prove for wave 2a: `capture_keeper_goldens.py --iso ERCOT__forward --stage-tag
wc-b-{before,after}` on the merge-base tree and the branch tree, then
`regression_gate.py --mode byte` at `atol=rtol=0` — PASS is required and expected, because
under the pin the new code is dead. (Check [4] legitimacy fails on main for a pre-existing NYISO
data gap and is reported by control, as every wallclock PR does.)

Two consequences worth stating so nobody re-derives them:
- **Keeper goldens do not move.** A registered keeper's golden is captured under the pin; a
  seeded calibration run of the same recipe lands on a marginal-tie-equivalent vertex, which is
  the class the goldens were always blind to (they are cold-vs-cold, not cold-vs-any).
- **A keeper's committed bundle is still the control** (rule 28 `[R-SCREEN]` (b)) — the seed
  changes no number the G-CTRL form-4 difference reads at scoring resolution, exactly as P-2
  did not.

## 6. The proposed surface (what wave 2a would ship, for the owner to sign or refuse)

1. **Calibration CLIs default ON, opt-out flag, env var honored** — the P-2 shape. A new
   switch `MARKET_SIM_P1_BASIS_SEED` resolved by a sibling of
   `run_calibration.resolve_xyear_warmstart_default` with the same precedence:
   `--no-p1-basis-seed` forces OFF; an explicitly-set env var is honored as-is; otherwise ON.
   Set only on the fresh-solve path of `run_calibration.py` / `run_calibration_full.py`
   (`--report` / `--replay-bundle` / `--rebuild-benchmark` and the direct `solve_and_persist`
   callers stay at the global default OFF, exactly as the cross-year switch does).
2. **Armed only inside the cross-year gate.** In `run_energy_solve`'s cold-P1 branch the seed
   fires iff `_xwarm and p1_basis_seed` — so `MARKET_SIM_WARMSTART_XYEAR=0` (the goldens pin,
   `--no-xyear-warmstart`) implies seed OFF with no second knob to remember (§5). The export
   that already runs there when `_xwarm` is armed is reused; the seed adds one
   `apply_cross_year_basis` call on the second model, before `solve`.
3. **Forecast path unchanged.** `runner.py` passes `xyear_warmstart=config.forecast_xyear_warmstart`
   explicitly and every shipped forecast runner passes `False` (D-10, `forecast_posture.
   shipped_forecast_xyear_warmstart`), so `_xwarm` is False on every forecast bundle and the seed
   is inert there by construction — no `ScenarioConfig` field, no cache-key movement, no
   resume-reproducibility exposure (the D-10 defect was a *cross-year* inheritance; a same-year
   seed has no cross-year state, but the forecast lane is left cold anyway so K.3 is not
   re-opened by a side door).
4. **The adaptive pass is seeded a second time per year.** On the ercot-221/230 and caiso-205
   routes pass 2 reaches `run_energy_solve` with `reuse_p0_from` (C-1b): there is no P0 model
   on that pass to export from, but the previous pass's **P1** model was the identical floored
   LP under a different storage discharge cost, so its basis is the closer seed. Surface: the
   cold-P1 branch exports the P1 model's basis onto `EnergySolveResult` (a `p1_basis` field,
   int8 vectors, ~tens of MB) before the pass returns, and a reused pass seeds its P1 from
   `reuse_p0_from.p1_basis`. **Measured here only on the plain two-run 2025 year** (C-1a
   skipped 2025's pass 2, so there was no second P1 to seed); the adaptive-pass leg carries the
   same class and gate and is measured on a 2023/2024 ERCOT year in wave 2a before it ships.
5. **Pinning tests** extend `tests/unit/pipeline/test_xyear_warmstart_default.py` (it exists at
   that path at HEAD — the desk log §2.3 looked for it at the `tests/` root; the wave-2a
   prompt should say *extend*, not *create*): precedence of flag / env / default, seed
   inert under `XYEAR=0`, seed inert on the forecast (`xyear_warmstart=False`), and the
   `_CapturingDispatchModel` contract (the seed must be a `getattr`-tolerant call, as the
   timing reads are).
6. **Gate before merge** (desk charter): fast tier; the §5 byte gate (merge-base control vs
   branch under the pin, expected byte-identical); and the §4 neutrality gate on one
   3-year calibration-CLI bundle pair for ERCOT (`--year 2023 2024 2025`, seed off vs on,
   `diff_warmstart_bundles.py` per year) plus NYISO as the co-opt ISO that also pays — the P-2
   precedent used ERCOT + MISO; here MISO is warm-P1 and inert, so NYISO is the informative
   second ISO. `docs/handoffs/wallclock-baseline-2026-07.md` gets its dated row; CHANGELOG entry;
   the mechanism-matrix CI guard warns on a new calibration CLI flag with no matrix touch, and
   the flag is a solve-path knob like `forecast_xyear_warmstart`'s row, so wave 2a notes it the
   same way that row does ("SOLVE-PATH knob, NOT a market mechanism").

What the surface does **not** include: no `ScenarioConfig` field (rule 24 `[R-REGISTRY]` governs
tunables that change a solve's *answer*; a starting basis cannot, and the P-2 switch is the
precedent), no golden refresh, no keeper re-capture, no change to any P1 route decision, no
in-place refloor.

## 7. Options for the owner

- **(A) {{OPT_A_LABEL}} — Flip: calibration-CLI default ON with `--no-p1-basis-seed`, env var
  honored, seed inert under the goldens pin and on the forecast path; adaptive-pass second seed
  in the same PR, measured on a two-pass year before merge.** {{OPT_A_TEXT}}
- **(B) {{OPT_B_LABEL}} — Do not flip.** {{OPT_B_TEXT}}

Either way the ranked list in `wallclock-opportunities-2026-09.md` §5 is unchanged in its
byte-identical items (A-1/A-2/A-3/A-6/A-4/A-5); this memo decides item 4 only.

## 8. Verified-at-HEAD checklist (2026-09-05, main @ `2886235c`)

| Claim | Where verified |
|---|---|
| Cold-P1 branch exports the P0 basis only when `_xwarm`, then `model = None`, then `solve_dispatch` (fresh model, no basis) | `src/market_sim/pipeline/solve.py` ~L644–660 |
| `_xwarm` = `MARKET_SIM_WARMSTART_XYEAR != "0"` on every backcast caller; explicit `xyear_warmstart` bool wins on the forecast | `pipeline/solve.py` ~L406–412; `runner.py` ~L3467 |
| `apply_cross_year_basis` maps columns by `unit_id` + positional blocks, copies energy + storage rows, defaults the rest basic, loads `alien=True`; must precede the first solve | `src/market_sim/model/lp/model.py` L1470–1526, `_cross_year_column_map` L1530+ |
| `solve_dispatch` builds `DispatchModel(...)` and calls `model.solve(mc=…)` with no basis | `src/market_sim/model/lp/__init__.py` L536–648 |
| Determinism pin values | `scripts/capture_keeper_goldens.py` L146–148 |
| `ERCOT__forward` resolves to the composite keeper whose `meta.json` carries the forward config | `frontend/data/backcast/keepers/ERCOT.json` `config_partition`; `results/calibration/ercot248_two_config_keeper/composite_provenance.json` |
| P-2 precedence resolver the new switch mirrors | `scripts/run_calibration.py` L6654–6690 (`resolve_xyear_warmstart_default`) |
| Pinning-test file exists (contrary to desk log §2.3's root-path lookup) | `tests/unit/pipeline/test_xyear_warmstart_default.py` (10 tests) |
| Every shipped forecast runner passes `forecast_xyear_warmstart=False` (D-10) | `scripts/lib/forecast_posture.py::shipped_forecast_xyear_warmstart` |
| C-1a made ERCOT 2025 a two-run year; C-1b keeps a reused pass off the P0 export | `docs/FINDING-perfb-s3-adaptive-pass-2026-09.md` §2–§3 |

---

## Owner decision

**Decision requested:** plan-§6 item B — seed the cold-rebuilt P1 from the same year's P0
basis on the calibration path (proposed surface §6), or leave the cold-P1 route as shipped.

- [ ] **(A) FLIP** — wave 2a proceeds on `claude/wc-b-p1-basis-seed` under the §6 surface and
      the §4/§5 gates; the desk unblocks item B.
- [ ] **(B) DO NOT FLIP** — item B is closed on this memo's evidence; the cold-P1 route stays
      as shipped and the desk strikes item B from the wave-2 board.
- [ ] Other / conditions (owner writes them here): ______________________________________

Signed: ______________________________  Date: ______________

*(Recorded by the desk in `wallclock-desk-log-2026-09.md` §2 when signed; the signature is what
wave 2a is gated on. Rule 28 `[R-SCREEN]` note for the record: this bench is a throwaway
screen — it may kill the arm, it promotes nothing, and its bundles were deleted.)*
