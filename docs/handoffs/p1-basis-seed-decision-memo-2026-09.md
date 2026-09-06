# B-0 owner decision memo — seeding the cold-rebuilt P1 from the same year's P0 basis (wallclock plan §6)

**STATUS: DECISION INPUT — for the owner. Wave 2a (`claude/wc-b-p1-basis-seed`) is gated on
the signature line at the end of this memo.** Written 2026-09-05 by B-0
(`claude/wc-b0-p1-seed-memo-9euk97`, main @ `2886235c` when the bench ran, rebased onto
`2cc135bb` — Y-14 landed in between, see §3.1), chartered by the WALLCLOCK desk
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
**287.1 s → 139.3 s** (2.06×), simplex iterations **273,893 →
78,856**, objective and total generation identical (objective relΔ 8e-16, total generation Δ = 0 MWh, served load / slack / dump / reserve price bit-identical), every zonal price identical to 1.1e-12 $/MWh with **zero** dual-degenerate hours, and the only movement 16 unit-hours of offsetting marginal-tie swaps (0.0007 % gross reshuffle). The owner's choice is
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
  **Y-14 landed on main while the arms ran** (#4872, owner ruling R-AW: the bare `ERCOT` key
  and `ERCOT__forward` now resolve to the composed bundle *sliced to its designated span
  2024–2025*, and `ERCOT__carveout-2023` is a retired capture key). It changes nothing here:
  the bundle and its forward-config `meta.json` are the same object, and the bench year 2025
  is inside the designated span. Wave 2a's captures (§5) simply use the bare `ERCOT` key.

### 3.2 Speed — the P1 solve, the iterations, the phase lines

| arm | `solve_p0` s | P0 iters | P0 objective | `solve_p1` s | P1 iters | P1 objective | basis export s | basis apply s | year `total` s | maxrss GB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| seed OFF (shipped) | 327.8 | 273,083 | 2,879,242,264.7545 | 287.1 | 273,893 | 3,085,008,028.5299 | — | — | 717.4 | 12.46 |
| seed ON | 335.4 | 273,083 | 2,879,242,264.7545 | 139.3 | 78,856 | 3,085,008,028.5299 | 16.9 | 3.0 | 581.5 | 13.07 |

Reading it. **The P1 solve falls from 287.1 s to 139.3 s (2.06×) and from 273,893 to 78,856 simplex
iterations (3.47×)** — the seeded model starts near the P1 optimum and spends its iterations on
the bridge's raised bounds and the re-costed objective rather than rebuilding a basis from
nothing. The P0 rows are the built-in control: **identical iteration count (273,083) and
identical objective to the last digit on both arms**, so nothing upstream of the seed moved and
the 327.8 → 335.4 s P0 wall is the ±10–15 % run-to-run noise of a cold HiGHS run on this box
(s3 finding §0). The seed's own cost is the **16.9 s basis export** (the `getBasis()` enum
materialization PERF-B measured at 10–16 s/yr, booked here in the `markup` residual as
`p0_post` 5.5 → 22.3 s) plus a **3.0 s apply**; net per seeded P1 pass on this year:
**−147.8 + 19.9 ≈ −128 s**. On the calibration CLI path (`MARKET_SIM_WARMSTART_XYEAR=1`) the
export already runs in that branch for the cross-year holder, so the marginal cost there is the
3 s apply alone. Year `total` 717.4 → 581.5 s (**−135.9 s, −19 %**); driver process wall
757.6 → 619.8 s. Peak RSS 12.46 → 13.07 GB: the carried `int8` vectors are ~22 MB, so the
+0.6 GB is HiGHS's alien-basis repair workspace and/or run-to-run variance (the s3 record spans
12.1–13.4 GB for this year); it is inside the recorded envelope but worth one `MEM_DEBUG`
sample in wave 2a alongside A-6, since the cold-P1 rebuild is already the year's RSS peak.

Phase lines (the six frozen fields + the `markup` clause, verbatim from each arm's log):

```
OFF  year 2025 phase timing: data_prep=83.1s solve_p0=327.8s markup=12.2s solve_p1=287.1s results_write=7.2s total=717.4s (markup: setup=0.0s p0_post=5.5s markup=0.1s seam=0.8s p1_post=5.8s tail=0.0s other=0.0s) (results_write: state=0.5s frames=2.8s parquet=2.7s bench=1.2s)   # process wall 757.6 s, maxrss 12.46 GB
ON   year 2025 phase timing: data_prep=69.3s solve_p0=335.4s markup=31.3s solve_p1=139.3s results_write=6.2s total=581.5s (markup: setup=0.0s p0_post=22.3s markup=0.1s seam=1.0s p1_post=7.9s tail=0.0s other=0.0s) (results_write: state=0.6s frames=2.2s parquet=2.9s bench=0.5s)   # process wall 619.8 s, maxrss 13.07 GB; p0_post carries the 16.9 s export
```

### 3.3 Neutrality — `diff_warmstart_bundles.py` + `hourly/system_2025.parquet` (the H2 shape)

Same standard the shipped cross-year warm start (P-2) and the persisted year-1 basis (H2) were
promoted under (`wallclock-baseline-2026-07.md` §H2; `cross-year-warmstart.md` "Bundle-level
gate"): objective and total generation identical; per-unit differences confined to marginal
ties; price differences confined to dual-degenerate hours.

| ISO-year | objective / total gen | max \|Δ zonal price\| | dual-degenerate hours | per-unit dispatch reshuffle |
|---|---|---|---|---|
| ERCOT 2025 (forward config) | objective 3,085,008,028.5298586 vs .529856 (relΔ 8e-16); total gen Δ = **0 MWh** (488.449982 TWh both); served load, slack, dump and `reserve_price` bit-identical (max \|Δ\| = 0) | **1.1e-12 $/MWh** (floating-point noise); mean price 29.358576 both | **0 / 61,320** (\|Δ\| > 1e-9) | 16 unit-hours in 12 hours, 11 of 2,335 units; max 895 MWh/unit (a SOLAR_South ↔ SOLAR_North curtailment swap at price 0); Σ\|hourly Δ\| 3.4 GWh = **0.0007 %** of gen; `total gen Δ = 0` |

`diff_warmstart_bundles.py` fleet-wide block, verbatim:

```
Fleet-wide:
  total annual gen  cold 488450.0 GWh  warm 488450.0 GWh  Δ +0.0000 GWh
  max  | annual Δ |  over all plants: 0.0610 GWh (plant 58005)
  mean | annual Δ |  over all plants: 0.0014 GWh
  plants with |annual Δ| > 1 GWh : 0
  plants with |annual Δ| > 0.1 GWh: 0
  max hourly |Δ| anywhere: 61.1 MW
  Σ|hourly Δ| (gross reshuffle): 0.5 GWh = 0.000% of total gen

  Top 8 plants by |annual Δ|:
     58005                      0.0610 GWh (cold 3520.44 -> warm 3520.38)
     55480                      0.0605 GWh (cold 9632.29 -> warm 9632.35)
      6180                      0.0576 GWh (cold 11575.99 -> warm 11575.93)
      6179                      0.0566 GWh (cold 5693.30 -> warm 5693.35)
      3439                      0.0000 GWh (cold 119.07 -> warm 119.07)
      3441                      0.0000 GWh (cold 2608.42 -> warm 2608.42)
      3453                      0.0000 GWh (cold 448.64 -> warm 448.64)
      3460                      0.0000 GWh (cold 3056.43 -> warm 3056.43)
```

Every moved unit-hour is a marginal tie, checked row by row rather than inferred: on each of
the 16 rows the P1 LMP is **identical on both arms** (max |Δlmp| = 0.0), and each swap has its
offsetting partner at the same price — Colorado Bend-class CC units 55480 ↔ 58005 in North at
hour 1643 (61.1 MW, LMP 24.02 both), lignite 6180 (North) ↔ PRB 6179 (South_Central) across
hours 5322/5323 at LMP 41.3765 in both hours (the storage link carries the 56.8 MW between the
two equally-priced hours), CC 55123 South between hours 1284/1288 at 27.34, and solar/wind
curtailment placement at the 0 / −26 $/MWh floors (West ↔ Panhandle solar, Panhandle wind
between hours 2056/2057). No unit off the margin moves; no price moves; no served load
moves. Against the H2 record this is *cleaner* than the shipped persisted-basis seed (ERCOT
2023: 6.8e-2 $/MWh over 30 dual-degenerate hours) and than the P-2 promotion evidence
(MISO 2025: 0.1495 $/MWh over 182 zone-hours): a same-year seed starts from the optimal face
of the *same* LP, so there is no cross-year vertex drift to land on a different dual.

### 3.4 Verdict of the measurement

**Neutral under the `diff_warmstart_bundles.py` standard, and faster by half a P1 solve.**
Objective and total generation identical; no non-marginal-tie unit difference; no price
difference outside floating-point noise; P1 2.06× on wall, 3.47× on iterations, at a 3 s
marginal cost where the export already runs. The desk's kill condition ("objective or total
generation differ, or any non-marginal-tie unit diff → do not flip") is not met on any leg.
Scope of the claim: one ISO-year, the one-pass 2025 forward config, under the determinism
pin — a **screen**, per rule 28 `[R-SCREEN]`: it may kill an arm and it did not; it promotes
nothing, and the 3-year / second-ISO bundle pair is wave 2a's gate (§6.6).

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
*is* asked to prove for wave 2a: `capture_keeper_goldens.py --iso ERCOT --stage-tag
wc-b-{before,after}` (the forward config on 2024–2025 since Y-14) on the merge-base tree and
the branch tree, then
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

- **(A) RECOMMENDED — Flip: calibration-CLI default ON with `--no-p1-basis-seed`, env var
  honored, seed inert under the goldens pin and on the forecast path; adaptive-pass second seed
  in the same PR, measured on a two-pass year before merge.** The measured case is the plan's own neutrality class at its cleanest (zero dual-degenerate
hours), the speedup is a full half of every cold P1 pass, and the machinery is already shipped
and already gated the same way for adjacent years. On the anchor numbers of §2 the reach is
~130–150 s per P1 pass on ERCOT (×2 on the adaptive years and the carve-out), ~50–85 s per pass
on NYISO, and CAISO's every year; NEISO/PJM/MISO are untouched. The cost is one more
solve-path switch of the P-2 shape and a +0.6 GB peak-RSS reading to confirm. What the owner is
signing: a *calibration-CLI default*, off under the goldens pin and on the forecast lane,
gated before merge on a 3-year ERCOT + NYISO bundle pair.
- **(B) NOT RECOMMENDED — Do not flip.** Coherent only on one of two grounds, neither of which this bench supports: (i) the owner wants
the calibration lane to be *vertex-identical* to the goldens rather than marginal-tie-equivalent
— but the lane already is not (cross-year warm start and the persisted year-1 basis are ON by
default there, both promoted on this same standard), so refusing the seed buys no invariant the
lane does not already lack; or (ii) the +0.6 GB peak-RSS reading is real and pushes an ERCOT
year over the 14 GB cgroup — resolvable by measuring it in wave 2a (and A-6 attacks the same
peak), not a reason to forgo 2× on the P1. If (B) is chosen, the desk strikes item B, the §3
numbers stay on record in `wallclock-opportunities-2026-09.md` §6.3, and the cold-P1 route is
left as shipped.

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

- [x] **(A) FLIP** — wave 2a proceeds on `claude/wc-b-p1-basis-seed` under the §6 surface and
      the §4/§5 gates; the desk unblocks item B.
- [ ] **(B) DO NOT FLIP** — item B is closed on this memo's evidence; the cold-P1 route stays
      as shipped and the desk strikes item B from the wave-2 board.
- [ ] Other / conditions (owner writes them here): ______________________________________

Signed: **Owner** — instruction given 2026-09-06 in the wave-2a implementation session
(`claude/wc-b-p1-basis-seed-9557mm`), verbatim: *"Tick the box"*, in reply to that session's
stop-if-unsigned report, which named **(A) FLIP** as this memo's own recommendation and the
only option that unblocks item B. The box was ticked by the worker on that instruction; the
owner's instruction is the signature and this line is its record.  Date: 2026-09-06

*(Recorded by the desk in `wallclock-desk-log-2026-09.md` §2 when signed; the signature is what
wave 2a is gated on. Rule 28 `[R-SCREEN]` note for the record: this bench is a throwaway
screen — it may kill the arm, it promotes nothing, and its bundles were deleted.)*
