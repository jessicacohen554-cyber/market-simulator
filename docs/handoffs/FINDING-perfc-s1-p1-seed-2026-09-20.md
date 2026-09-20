# FINDING — PERF-C S1: the same-year P1 basis seed is now independently gateable, with an optimality guard (2026-09-20)

**Shard:** PERF-C S1 (lever L1 of `docs/handoffs/PRECOMMIT-perfc-orchestration-2026-09-20.md`).
**Pinned HEAD:** `2a87343f8d7302ce84e66f45430a8d3b9e807d80`. **Branch:** `claude/perfc-s1-p1-seed`.
**No timing work was performed.** The owner stated there is already enough wall-clock data; this
shard ran no solve to measure speed. The only solves it ran are the NEISO byte-gate captures in §4,
whose purpose is to prove the *default* path is unchanged.

---

## 1. The defect this closes

`src/market_sim/pipeline/solve.py` gated the **same-year** P0→P1 basis seed on `_xwarm`, the
**cross-year** warm start:

```python
_p1_seed = (
    _xwarm                                                  # <- the coupling
    and xyear_warmstart is None
    and os.environ.get("MARKET_SIM_P1_BASIS_SEED", "0") != "0"
)
```

The two mechanisms are unrelated in what they carry. The cross-year warm start hands **year N's**
optimal basis to **year N+1**. The same-year seed hands **this year's P0** basis to **this year's
P1**, inside a single `run_energy_solve` call, on the cold-rebuilt second `DispatchModel` that a
P1-native floor bridge forces (ERCOT / NYISO gas commitment bridges, CAISO RA must-offer).

Rule 36 `[R-YEAR-ISOLATION]` (owner ruling 2026-09-19, miso-262) defaulted **both** env knobs OFF.
Its evidence is entirely cross-year — MISO's keeper reproduced the first year of each solve leg and
diverged by 7.1586 / 24.1796 / 4.0034 TWh in the later ones — and rule 36(d) says so in as many
words:

> `pipeline/solve.py` arms the second only inside the first's gate

That sentence is **the reason the same-year seed went dark**, and it is now stale (§6). Rule 36(e)
does separately withdraw the seed's own neutrality claim, citing MISO 2020 and 2023 — the
*leg-first* years, where no prior-year basis exists — moving by 0.0048 and 0.1440 TWh. That is a
real observation and this shard does not dispute it; it is also why the change ships with a guard
(§3) and leaves the default OFF (§5).

---

## 2. What changed (file:line, at the pushed commit)

### `src/market_sim/pipeline/solve.py`

| lines | change |
|---|---|
| 28–58 | Module docstring: the seed's "armed only inside the cross-year gate" paragraph rewritten for the un-nesting, the explicit goldens/replay pin and the guard. |
| 116–124 | **New** `_OPTIMAL_MODEL_STATUS = "Optimal"` — the string `DispatchModel.solve` stores in `DispatchResult.status` (`h.modelStatusToString(kOptimal)`), read only by the guard. |
| 137–141 | `take_pass_timing_log` docstring names the two seed keys. |
| 200–214 | `EnergySolveResult` docstring: `p1_seeded` restated as "the P1 this result REPORTS", plus the new `p1_seed_fallback`. |
| 226 | **New field** `p1_seed_fallback: Optional[str] = None`. |
| 487–521 | **The gate.** `_xwarm` → `_warm`; the comment records why, what it costs, and that the default does not move. |
| 762–770 | **The P0 export.** Was `model is not None and _xwarm and (xyear_cache is not None or _p1_seed)`; now `model is not None and (_p1_seed or (_xwarm and xyear_cache is not None))`, with the holder write re-guarded on `_xwarm` inside. This is the load-bearing half: **a seed-only pass must not write the cross-year holder.** |
| 717–722 | `_p1_seed_fallback` initialised beside `_p1_seeded` / `_p1_basis` so every route defines it. |
| 806–855 | **The optimality guard** (§3) and the extended `P1 basis seed:` info line (`fallback=…`). |
| 921–927 | `markup_parts["p1_post"]` comment: the export is now armed by either gate, and a discarded seeded `h.run()` lands here. |
| 949 / 973 | `p1_seed_fallback` on the pass-timing log entry and on the returned `EnergySolveResult`. |

**Gate, after:**

```python
_p1_seed = (
    _warm
    and xyear_warmstart is None
    and os.environ.get("MARKET_SIM_P1_BASIS_SEED", "0") != "0"
)
```

`_warm` replaces `_xwarm` rather than being dropped: the seed's *source* is the live P0
`DispatchModel`, and `MARKET_SIM_WARMSTART=0` builds none. The `model is not None` guard at the
export already enforced this, so naming it changes no route — it makes the gate self-documenting.
`xyear_warmstart is None` is untouched, so **the forecast path is untouched**: it passes an explicit
bool and never reads this env var.

### Callers and reproducibility pins

| file:line | change |
|---|---|
| `scripts/capture_keeper_goldens.py:193–201` | `DETERMINISM_ENV` now pins `MARKET_SIM_P1_BASIS_SEED: "0"`. |
| `scripts/replay_keeper.py:48–56` | `DETERMINISM_ENV` likewise. |
| `scripts/run_calibration.py:7634–7700` | `resolve_p1_basis_seed_default` docstring: the "necessary, not sufficient / only INSIDE the cross-year gate" paragraph replaced. **The code is unchanged — the default is still OFF.** |
| `scripts/run_calibration.py:7608–7623`, `run_calibration_full.py:10179–10195` | `--no-p1-basis-seed` help text: no longer claims "ON by default" (stale since rule 36) or "hard-OFF under `--no-xyear-warmstart`". |
| `scripts/run_calibration.py:7831–7836`, `run_calibration_full.py:14861–14867` | The startup log line reported `"ON" if (_p1_seed and _xwarm)`, which is now wrong. Reports `_p1_seed` alone. |

**Why the two `DETERMINISM_ENV` pins are part of this change, not scope creep.** Under the old gate,
`MARKET_SIM_WARMSTART_XYEAR=0` *implied* the seed off, and both scripts relied on that implication
rather than stating it. Un-nesting makes the implication false. An unstated implication that no
longer holds is not a pin, and a seeded P1 is warm-start class — exactly what a byte-identity golden
may not carry. Nothing else in the tree read the implication (verified by grep over
`MARKET_SIM_WARMSTART_XYEAR`).

### `docs/cross-year-warmstart.md`

Section "Same-year P1 basis seed" (~line 431): a superseded-twice box (rule 36's default flip, then
this un-nesting), the **Gate** paragraph rewritten as the three numbered conditions, a new **no
cross-year state, by construction and by test** paragraph, and a new **Optimality guard** paragraph.
The 2026-09-06 measured tables are left in place as history, under rule 36(e)'s caveat.

---

## 3. The optimality guard

`pipeline/solve.py`, on the seeded cold-P1 route only:

```python
try:
    p1 = _p1_model.solve(mc=mc_bid)
    _p1_status = str(getattr(p1, "status", "") or "")
    _seed_failure = None if _p1_status == _OPTIMAL_MODEL_STATUS else _p1_status
except Exception as exc:
    if not _p1_seeded:
        raise
    p1 = None
    _seed_failure = f"{type(exc).__name__}: {exc}"
if _p1_seeded and _seed_failure is not None:
    logger.warning(...)          # names the status
    _p1_seed_fallback = _seed_failure
    _p1_seeded = False
    _p1_model = None
    p1 = solve_dispatch(p1_fleet_arrays, demand, mc=mc_bid, **p1_dispatch_kwargs)
```

- **Trigger:** the seeded `h.run()` reports any model status other than `Optimal`, **or**
  `DispatchModel.solve` raises (it does so on an infeasible primal, which a corrupt alien basis can
  also produce).
- **Action:** WARNING naming the status, basis discarded, the same LP re-solved **cold** through
  `solve_dispatch` — byte-for-byte the answer an unseeded pass produces.
- **Cost of a false trigger:** one wasted `h.run()`. **Never an answer.**
- **Nothing is masked:** a genuinely infeasible LP raises again on the cold re-solve.
- **Scope:** only a pass that was actually seeded can roll back. When `apply_cross_year_basis`
  declined, or the route was never seeded, a non-`Optimal` status or a raise propagates exactly as
  before — the unseeded route is untouched.

**Provenance rides the existing channel (no new one).** `EnergySolveResult.p1_seeded` now means "the
P1 being returned was solved from a basis", so it reads `False` after a rollback; the sibling
`p1_seed_fallback` carries the offending status. Both appear on the `_PASS_TIMING_LOG` entry, and
the existing `P1 basis seed:` info line gained a `fallback=` field. `run_calibration.
_aggregate_pass_timing` reads only `build_s` / `solve_p0_s` / `solve_p1_s` / `parts`, so the added
key is inert for every consumer.

**Why a guard at all.** An alien basis is documented to be repairable by HiGHS, but rule 36(e) is
this repository's own record of a basis-neutrality claim that did not survive measurement. Checking
the answer costs one integer comparison on the ordinary path.

---

## 4. Byte gate — **PASS**

NEISO, keeper `2026-09-19-neiso112-mer-year-isolated`, six years 2020–2025, 8760 h, under
`capture_keeper_goldens.py`'s determinism pin.

```
python scripts/capture_keeper_goldens.py --iso NEISO --stage-tag perfc-s1-before   # at HEAD, pre-edit
python scripts/capture_keeper_goldens.py --iso NEISO --stage-tag perfc-s1-after    # post-edit
python scripts/regression_gate.py \
    --before results/regression-goldens/perfc-s1-before \
    --after  results/regression-goldens/perfc-s1-after  --mode byte
```

**Verdict: PASS at `atol=rtol=0`.** See §7 for the gate's own output.

The BEFORE capture was launched before the first edit and is single-process: it imports
`scripts.run_calibration_full` (and transitively `market_sim.pipeline.solve`) inside `capture_one`,
*before* its first log line, and Python's module cache then holds the pre-edit bytes for all six
years. Verified by timestamp — process start 18:34:09 UTC, first log line before 18:36:21,
first edit to `solve.py` at 18:36:54.

**What the gate proves and what it does not.** It proves the **default** path is byte-unchanged:
with `MARKET_SIM_P1_BASIS_SEED` unset the new gate resolves exactly as the old one did. It does
**not**, and must not, prove anything about a seeded run against an unseeded one — that is
warm-start class (marginal-tie reshuffle), the standard rule 36(e) withdrew and which no byte gate
can carry.

NEISO is also a *conservative* choice for this particular change: its keeper carries no P1-native
floor bridge, so its P1 re-solves the live P0 model and the seed is inert on it by route as well as
by gate. The byte gate therefore tests the gate logic and the callers, not the seeded branch; the
seeded branch is covered by the tests in §5.

---

## 5. Tests

`tests/unit/pipeline/test_xyear_warmstart_default.py` — **29 passed** (see §7).

**Two pre-existing failures at the pinned HEAD, both fixed here.** `TestResolveDefault::
test_default_on_when_unset` and `TestResolveP1BasisSeedDefault::test_default_on_when_unset` still
asserted the pre-rule-36 default **ON** for both resolvers. Rule 36 landed the flip in
`scripts/run_calibration.py` on 2026-09-19 without updating them, so the file was red at HEAD
before this shard touched it. Renamed to `test_default_off_when_unset` and flipped, each carrying
the reason in its docstring. **This is a report of found breakage, not a repair excursion:** they
are the `resolve_p1_basis_seed_default` tests this shard was sent to extend, in the file it edits.

**Rewritten:** `test_seed_inert_under_the_goldens_pin` asserted the old nesting (XYEAR=0 + SEED=1 →
no seed) and is the one thing the un-nesting deliberately inverts. It is now
`test_seed_fires_with_the_cross_year_gate_off`, and the invariant that replaces it is the one that
matters: **the cross-year holder stays empty**, so no state reaches the next year (rule 36's actual
concern), and the P1 cleared is still the unseeded P1.

**Added:**

| test | asserts |
|---|---|
| `TestP1BasisSeedGate::test_seed_fires_with_the_cross_year_gate_off` | XYEAR=0 + SEED=1 → `p1_seeded`; holder empty; dispatch/prices/objective equal the unseeded run. |
| `…::test_seed_does_not_fire_with_its_env_off` | SEED=0 → never seeded, under XYEAR both `0` and `1`. |
| `…::test_seed_needs_the_intra_year_warm_start` | `MARKET_SIM_WARMSTART=0` → inert however armed. |
| `TestP1SeedOptimalityGuard::test_non_optimal_status_falls_back_to_a_cold_resolve` | fallback recorded; WARNING logged; `p1_seeded` False; dispatch/prices equal the unseeded baseline; same provenance on the timing log. |
| `…::test_a_raising_seeded_solve_also_falls_back` | a raising seeded solve is retried cold, not propagated. |
| `…::test_an_optimal_seeded_solve_records_no_fallback` | the guard is silent on the ordinary path. |
| `…::test_a_declined_basis_is_not_rolled_back` | apply declined → nothing installed → guard must not fire. |

The guard tests use `_seeded_model_reporting`, a `DispatchModel` subclass that misreports **only on
instances whose `apply_cross_year_basis` ran**. That scoping is necessary rather than decorative:
`pipeline.solve` builds the P0 model through the same name, so a double that misreported
unconditionally would fail the P0 solve before reaching the P1 under test.

Also run: `tests/unit/pipeline/`, `tests/regression/test_pipeline_timing.py`,
`tests/regression/test_regression_smoke.py` — §7.

---

## 6. The CLAUDE.md sentence that is now stale

Rule 36 `[R-YEAR-ISOLATION]` clause **(d)**, verbatim:

> **(d) BOTH SOLVE-PATH KNOBS NOW DEFAULT OFF**, flipped together because
> `pipeline/solve.py` arms the second only inside the first's gate:
> `MARKET_SIM_WARMSTART_XYEAR` (`resolve_xyear_warmstart_default`) and
> `MARKET_SIM_P1_BASIS_SEED` (`resolve_p1_basis_seed_default`), both in
> `scripts/run_calibration.py`.

The stale clause is **"flipped together because `pipeline/solve.py` arms the second only inside the
first's gate"**. As of this commit it does not. **CLAUDE.md is not edited by this shard** (forbidden
by the shard prompt); the parent carries the amendment to the owner.

Nothing else in rule 36 is affected. **(a)** one shard per year, **(b)** a backcast has no span to
preserve, **(c)** the forecast is untouched, **(e)** the withdrawn neutrality claims and **(f)** the
cost statement all stand exactly as written — in particular (e) still withdraws the same-year
seed's neutrality claim, which is why this shard adds a guard and changes no default.

---

## 7. Raw results

### Byte gate

```
========================================================================
REGRESSION GATE  (mode=byte, atol=0.0, rtol=0.0)
========================================================================

[1] Golden bundle diff
    PASS  NEISO: 15 files, 53 numeric columns within tolerance (atol=0.0, rtol=0.0)

[2] Reshuffle localization (informational)
  NEISO 2020: total annual gen  cold 92267.7 GWh  warm 92267.7 GWh  Δ +0.0000 GWh
  NEISO 2020: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2021: total annual gen  cold 98721.8 GWh  warm 98721.8 GWh  Δ +0.0000 GWh
  NEISO 2021: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2022: total annual gen  cold 100369.2 GWh  warm 100369.2 GWh  Δ +0.0000 GWh
  NEISO 2022: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2023: total annual gen  cold 97005.5 GWh  warm 97005.5 GWh  Δ +0.0000 GWh
  NEISO 2023: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2024: total annual gen  cold 103937.0 GWh  warm 103937.0 GWh  Δ +0.0000 GWh
  NEISO 2024: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2025: total annual gen  cold 107309.9 GWh  warm 107309.9 GWh  Δ +0.0000 GWh
  NEISO 2025: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen

[3] Trivial-case smoke tests
    smoke: PASS (rc=0) 36 passed in 0.14s

[4] Quarantine + registry gates
    legitimacy(--keepers): FAIL (rc=1) ValueError: nyiso_li_lcr_tsl=True but no published
      Long Island transfer_security_limit for delivery year 2022/2023 …
    audit_keepers: FAIL (rc=1)
========================================================================
  PASS  golden-diff
  PASS  smoke
  FAIL  legitimacy
  FAIL  audit_keepers
========================================================================
RESULT: FAIL
```

**The byte gate this shard owes is check [1], and it is PASS** — 15 files, 53 numeric
columns, six years, at `atol=rtol=0`, with zero gross reshuffle on every year.

**Checks [4] are PRE-EXISTING and were verified so, not assumed.** Both were re-run at the
pinned HEAD with this shard's changes stashed (`git stash -u`) and fail identically:

- `legitimacy(--keepers)` — the `data/clean/capacity-deliverability` partition is absent on a
  fresh container. This is the documented control-red leg: desk-log
  `docs/handoffs/wallclock-desk-log-2026-09.md` §2.14 (b), *"`regression_gate` check [4]'s
  `legitimacy` leg is red by control on a fresh container and goes green once
  `data/clean/capacity-deliverability` is regenerated"*.
- `audit_keepers` — one **E13** failure in the **SOCO** lane: `2026-09-20-soco53g-prb-own-iso`
  is registered for SOCO but is neither the keeper nor stamped to it (a rule 35 `[R-PROMOTE]`
  (a) prune the promoting session owed). Another ISO's registry state, reachable by no code
  this shard touched; `prune_iso_runs.py` is forbidden to this shard, so it is reported here
  for the parent rather than fixed.

Both captures were fidelity-clean: `[NEISO] fidelity OK: 308 recorded flags replayed
identically (1 HEAD-only meta keys); scenario_config 856 matched, 0 drifted`, on BEFORE and
AFTER alike. Container: cgroup ceiling 13.36 GiB + 6 GiB swap; `memory peak:
cgroup_peak_rss_gib=8.12` on both arms.

### Tests

| command | result |
|---|---|
| `pytest tests/unit/pipeline/test_xyear_warmstart_default.py` | **29 passed** |
| `pytest tests/unit/pipeline/ tests/regression/test_pipeline_timing.py` | **320 passed, 61 subtests passed** (283 s) |
| `pytest tests/regression/test_regression_smoke.py` | **36 passed** |
| `ruff check` + `ruff format --check` on every touched file | clean |

At the pinned HEAD, before any edit, the same file was **2 failed, 21 passed** — the two stale
default assertions of §5.

---

## 8. The owner decision this surfaces

**Default the same-year P1 basis seed ON while the cross-year warm start stays OFF.**

Rule 36 flipped the two together for a mechanical reason that no longer holds. The question is now
separable, and these are the facts on each side — **no new numbers were produced by this shard**.

**For ON** — desk-log item B (`docs/handoffs/wallclock-desk-log-2026-09.md` §2.14, PR #5091, seed
OFF → ON, P1 wall / simplex iterations):

| ISO-year | `solve_p1` | iterations |
|---|---|---|
| ERCOT 2025 | 349.2 → 142.0 s | 273,893 → 78,856 |
| ERCOT 2024 pass 1 | 295.3 → 132.2 s | 252,042 → 83,748 |
| ERCOT 2024 pass 2 | 332.9 → 92.8 s | 250,291 → 69,667 |
| NYISO 2023 | 96.4 → 67.6 s | 268,305 → 108,037 |
| CAISO 2023 | 354.5 → 123.1 s | 290,022 → 94,098 |

Peak RSS on ERCOT 12.67 → 13.27 GB (+0.6 GB, inside the s3 12.1–13.4 GB envelope; neither arm
crosses the cgroup). The benefit is confined to ISOs whose keeper carries a P1-native floor bridge
(ERCOT, NYISO, CAISO) — it is inert on NEISO / PJM / MISO keepers.

**Against ON** — rule 36(e): the neutrality claim was withdrawn, and MISO 2020 / 2023, the
*leg-first* years where no cross-year basis exists, still moved by 0.0048 / 0.1440 TWh against a
pinned-cold replay. That residue is the same-year seed's own, and it is small but not zero.

**What this shard did about it:** nothing that presumes the answer. The gate is now separable, the
default is unchanged and OFF, the guard makes a bad basis cost iterations rather than an answer, and
the goldens/replay pins are explicit so a future flip cannot silently reach a byte gate. If the
owner flips it, every armed keeper's next re-solve carries a marginal-tie reshuffle and should say
so at full magnitude, exactly as rule 36(f) requires.
