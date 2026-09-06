# FINDING — Y-21: the R-AE flip set back to 6 of 6

**Session:** Y-21, Model Audit & Release-Finalization Program.
**Branch:** `claude/y21-flipset-repair-f4i63c`. **Base:** `origin/main` `1aab49a0`
(reproduced first at `369e8fbb`; rebased mid-session when main advanced, and the
whole battery re-run on the rebased tree — §6).
**Scope:** CI repair only. Zero LP. No solve, score or registration; no keeper
shard, marker, freeze file, bundle, matrix cell or `program-status.json`.

---

## 0. Result

**Five defects, four root causes, all repaired.** The charter named eight test /
lint failures across three causes plus ruff. All eight reproduced locally before
any edit. Two further reds were found that the charter did not name, both inside
flip-set jobs and both therefore blocking on 6-of-6:

| # | cause | job(s) reddened | charter? |
|---|-------|-----------------|----------|
| 1 | capx D62 facade omission | Structural refactor guards **+** Fast test tier | yes |
| 2 | SCN-WS1c test-double gap | Fast test tier | yes |
| 3 | SCN-WS1c **production** mass-cap crash | Fast test tier | yes |
| 4 | SCN-LOAD ruff (1 import + **9** files, not 8) | Ruff lint + format | partly — the 9th file is new |
| 5 | SCN-LOAD dangling script-reference (`spp.py`) | Structural refactor guards | **no** |

Every one of the five was verified **pre-existing on unmodified `main`** (by
`git stash` + re-run) before it was touched. No test was skipped, xfailed,
quarantined or relaxed anywhere in this repair.

---

## 1. Cause (1) — capx D62 (`9028992c`): one symbol, two red jobs

### Reproduction (before)

```
$ uv run --frozen python -m pytest -q tests/regression/test_constants_facade.py ...
FAILED tests/regression/test_constants_facade.py::test_moved_surface_is_complete
E  AssertionError: market_sim.config.capacity_market grew names the facade does
   not re-export: ['resolve_capacity_going_forward_bar_published']
1 failed, 34 passed
EXIT: 1
```

### Root cause, at the line

`src/market_sim/config/capacity_market.py:926` defines
`resolve_capacity_going_forward_bar_published`, the **third member of the
module's per-ISO capacity-gate family** (its own docstring says so). Its two
siblings — `resolve_capacity_market_clearing` and
`resolve_capacity_market_supply_clearing` — are both in the frozen
`MOVED_SURFACE` inventory and both re-exported from `config/constants.py`. D62
added the third with neither.

### The decision the charter asked for: public, or private?

**Public**, decisively — it has three importers outside its own module:

```
src/market_sim/model/capacity_evolution/retirements.py:84   (production)
scripts/run_capacity_hindcast.py:146                        (a standing script)
tests/unit/model/test_d62_published_going_forward_bar.py:29
```

Making it private would break all three to satisfy a guard. So the module is
right and the inventory is stale.

### Fix, and why this fix

Two lines, the documented repair: register it in `MOVED_SURFACE`
(`tests/regression/test_constants_facade.py:258`) **and** re-export it from the
facade (`src/market_sim/config/constants.py:131`). This is the **fifth** time
this exact omission has been repaired this way in this file — FFR-1C, FFR-4D,
FFR-4F and the PJM RGGI lane are all recorded there in the same form, each with
its own comment. The new entry carries one too.

**What was NOT done:** the test's exclusion filter (`not n.startswith("__")`,
`n != "dataclass"`) is untouched. Widening it would disarm the guard for every
future symbol, which is what the charter forbids. Adding a name to the frozen
inventory is the opposite act: it *extends* the contract the guard enforces,
because `test_every_moved_name_resolves_from_constants_facade` immediately
requires the new name to resolve from `constants` **and be the same object**.
The registration is checked, not merely tolerated.

### After

```
35 passed   EXIT: 0
```

---

## 2. Cause (2) — SCN-WS1c (`b1996141`) test-double half: 5 parity failures

### Reproduction (before)

```
FAILED tests/regression/test_interchange_parity.py::test_caiso_per_hub_parity[0.0]
FAILED ...::test_caiso_per_hub_parity[12.34]
FAILED ...::test_caiso_reference_seam_parity
FAILED ...::test_caiso_mode_mutual_exclusion_ladder
FAILED ...::test_caiso_per_hub_topology_split
E  AttributeError: '_FakeConfig' object has no attribute 'carbon_price_path'
```

### Root cause, at the line

SCN-WS1c's floor made `policy/carbon.py::resolved_base_trajectory_price` read
`config.carbon_price_path` as a **bare attribute** (the `max`'s second operand,
through `rff_path_price`). Every other carbon toggle on that path is read
through `getattr(..., default)` — `carbon_price_delta`, `mass_cap_enabled`,
`state_carbon_pricing` — which is why this one field, and only this one, breaks
the stand-in.

### Fix, and why this fix

`_FakeConfig` gains `carbon_price_path: str = "zero"` — **read from
`scenarios.py:2742`, not invented**. `"zero"` is the real `ScenarioConfig`
default, which keeps the parity oracle on the zero path so the comparison it
performs is unchanged: `CARBON_PRICE_PATHS["zero"]` is `0.0` in every year, so
the floor's `max` returns the program operand exactly as before the field
existed.

**The alternative rejected:** making the production read a `getattr` fallback.
That would hide the next such gap instead of surfacing it, and it puts a default
for a registered `ScenarioConfig` field in a second place — rule 24
`[R-REGISTRY]` territory. The test double is what was out of date, so the test
double is what was fixed.

### After

`test_interchange_parity.py` — all pass (see §5's combined run).

---

## 3. Cause (3) — SCN-WS1c **production** half: the mass-cap crash

This is the one that matters, and it is **not** a test-double gap.

### Reproduction (before)

```
FAILED tests/unit/pipeline/test_runner.py::
       TestMassCapPerUnitMembershipWiring::test_pjm_cap_coeffs_reach_dispatch_kwargs
E  TypeError: float() argument must be a string or a real number, not 'NoneType'
   src/market_sim/policy/carbon.py:171 in resolved_base_trajectory_price
```

*(The charter cited `carbon.py:100`/`:108`; at this head the crash line is
`:171`. Same statement, renumbered by the S2 docstring.)*

### WHICH input is None, and WHY it is reachable

`resolve_carbon_program` has exactly **two** construction sites
(`policy/cap_and_trade.py`):

* **line 325–326, the ADDER path** — `price_adder=float(price or 0.0)`. This can
  never be `None`. So the `None` does not come from a missing price.
* **line 274, the ROW path** — `CarbonProgramResolution(membership=..., cap_spec=cap_spec)`,
  leaving `price_adder` at its `None` default.

The row path is entered when `mass_cap_enabled` is set and a power-sector cap is
configured — precisely what the failing test's name says it is testing. There
`price_adder is None` is **the class's own documented invariant**, asserted in
`CarbonProgramResolution.__post_init__`: *"Exactly one of `price_adder` /
`cap_spec` is non-`None` — the core two-source design invariant."* It is `None`
because on the row path the allowance price is **ENDOGENOUS** — the LP dual of
the mass-cap row — and does not exist at config-resolution time.

Confirmed empirically rather than by reading:

```
$ ScenarioConfig(iso="NYISO", mode="forecast", mass_cap_enabled=True, ...)
  price_adder = None   cap_spec set = True   -> row path confirmed: True
```

**Why the S2 refactor made it reachable.** Pre-S2 (`b1996141^`) the guard was a
*truthiness* test, which absorbed both `None` and `0.0`:

```python
if resolution is not None and resolution.price_adder:      # row path falls through
    return float(resolution.price_adder)
# ... fall through to the path
```

S2 rewrote it as an *existence* test, dropping the row-path guard:

```python
program = float(resolution.price_adder) if resolution is not None else 0.0
```

That is the whole defect: `is not None` on the **resolution** was substituted for
truthiness on the **adder**. It silently narrowed a two-case guard to one case,
and S2's own commit message claim — *"the resolver's returned values are
unchanged on every path"* — is false for exactly this path, which now raises.

### Fix, and why this fix rather than the alternatives

Restore the truthiness guard, at **both** sites carrying the defect
(`carbon.py:186` and `:402`):

```python
program = float(resolution.price_adder or 0.0) if resolution is not None else 0.0
```

**Why this is not "a None-guard that silently returns 0.0".** The charter's
warning is against papering over a *missing program trajectory*. That is not what
is happening. The function's contract is the **exogenous** base trajectory. On
the row path the program contributes no exogenous price *by design* — its price
is the LP dual — so the floor correctly reduces to the federal path alone, and
the row's own price reaches marginal cost through the LP, not through this
function. The `0.0` is the correct value of a well-defined operand, not a
fallback for an absent one. Three independent confirmations:

1. **It is the established idiom for this exact case.** Every *other*
   `price_adder` consumer already uses it, and for the same reason:
   `cap_and_trade.py:553` (`carbon_mc_column`: `if resolution is None or not
   resolution.price_adder: return`) and `run_calibration.py:4039`. The S2 site
   was the odd one out.
2. **It restores pre-S2 behaviour exactly**, so it makes S2's own byte-identity
   claim true instead of false.
3. **It is byte-identical for every non-crashing config.** On the adder path
   `x or 0.0 == x` for any float, so nothing there moves; and no committed run
   can ever have been on the row path, because it raised.

**Alternatives rejected:** returning the cap's dual (it does not exist at
config-resolution time — it is an LP output); raising a typed error (it would
break every `mass_cap_enabled` run for a condition that is the design, not an
error).

### The second site — found here, not in the charter

`carbon_path_below_program_warning` (`carbon.py:402`) carried the **identical**
statement. It is reachable at `ScenarioConfig.__post_init__`, which wires this
guard, so any forecast mass-cap config naming a non-`"zero"` path would have
crashed **at config construction**. Its `if not program: continue` on the next
line already intends the falsy case to be skipped — the `float(None)` just
crashed before it could. With the fix, a row-path year is skipped, which is
correct: there is no exogenous program trajectory for a named path to resolve
below, so there is no invariant to breach.

### Residual to route to the SCN-WS1c desk

**None.** The honest fix turned out to be smaller than the crash suggested — a
one-token restoration of a guard the refactor dropped — so nothing is deferred.
One observation is worth the desk's attention but is *not* a defect and is not
this lane's to decide: the S2 floor is now defined over the **exogenous** channels
only, and the row path's endogenous price composes with the federal RFF path
nowhere at all. Under `carbon_price_path="zero"` (every committed keeper and
forecast bundle) that is vacuous. Whether a named federal path should floor a
**mass-cap** run's endogenous dual is a genuine open design question in the same
family as the already-open cards D-1(b) and D-1(c), and it is the owner's.

### After

`tests/unit/pipeline/test_runner.py` — all pass; `tests/unit/policy/` 311 passed.

---

## 4. Cause (4) — SCN-LOAD (`d14a7ed0`, PR #4970): ruff, both legs

### Reproduction (before)

```
$ uv run --frozen ruff check .
F401 [*] `._xlsx.numeric_records` imported but unused
  --> scripts/lib/load_forecast/pjm.py:36:34
Found 1 error.

$ uv run --frozen ruff format --check .
9 files would be reformatted, 1345 files already formatted
```

### `numeric_records` — dead, not a re-export

Checked before removing, as the charter required. It is **not** an intended
re-export: `pjm.py` has no `__all__`; nothing anywhere imports it *from* `pjm`;
and the only real consumer, `caiso.py:40`, imports it straight from `._xlsx`.
`pjm.py` simply never calls it — a copy-paste leftover from the sibling module's
import line. **Removed. No `noqa`, no artificial use.**

### The ninth file

The charter listed eight files for `ruff format`; the tree has **nine** —
`tests/scoring/test_audit_keepers_pointers.py` landed after the charter was
written. `ruff format` was run over all of them, since both legs must be green.

**Proof the reformat changed no logic.** `git diff --ignore-all-space` still
shows hunks (ruff re-wraps and re-joins lines), so whitespace-blindness is not
sufficient evidence. Each file was instead parsed at `HEAD` and at the working
tree and the two ASTs compared:

```
AST-IDENTICAL scripts/data/curate_load_forecast.py
AST-IDENTICAL scripts/lib/load_forecast/__init__.py
AST-IDENTICAL scripts/lib/load_forecast/caiso.py
AST-IDENTICAL scripts/lib/load_forecast/neiso.py
AST-IDENTICAL scripts/render_data_dictionary.py
AST-IDENTICAL tests/curation/test_curate_load_forecast.py
AST-IDENTICAL tests/scoring/test_audit_keepers_pointers.py
AST-IDENTICAL tests/unit/data/test_datacenter.py
AST-IDENTICAL tests/unit/data/test_electrification_layers.py
```

All nine identical: the reformat carries **zero** logic change.

### After

```
ruff check          → All checks passed!          EXIT: 0
ruff format --check → 1356 files already formatted  EXIT: 0
```

---

## 5. Cause (5) — NOT in the charter: a dangling script-reference, same job as (1)

Found because the charter's verification battery covers only **four** of the ten
facade files the `Structural refactor guards` job actually runs, and none of its
other two steps. Running the real job surfaced:

```
$ uv run --frozen python scripts/ci_refactor_guards.py
script-refs: 1 FAILURE(S) (12 known-dangling tolerated)
refactor-guards FAILED:
  - tests/curation/test_curate_load_forecast.py: references missing script
    'scripts/lib/load_forecast/spp.py'
EXIT: 1
```

Verified pre-existing on unmodified `main` (identical output with the branch
stashed). It arrived with SCN-LOAD, the same commit as cause (4), and has been
reddening this job **for every PR** since.

### Root cause, at the line

`tests/curation/test_curate_load_forecast.py:149`:

```python
with pytest.raises(ValueError, match="scripts/lib/load_forecast/spp.py"):
    lf.parse_iso("SPP", self.raw_root)
```

The path is the **expected substring of an error message**, not an invocation:
the registry answers an unregistered ISO by naming the module a contributor would
have to add, and the test pins that message. `ci_refactor_guards.py`'s regex
(`scripts/[\w/.\-]+\.py`) cannot tell a match-string from a call site.

### Fix, and why this fix

One `KNOWN_DANGLING` entry with a cited reason — the guard's **designed** route
for a benign non-reference (*"Keep this list exhaustive"*, its own header), with
seven same-category precedents already in the list: the six file-integrity-guard
fixture paths, and `scripts/fake_builder.py`, which **Y-13 added in this same
program for this same job**.

**Alternatives rejected:**

* *Create `scripts/lib/load_forecast/spp.py`.* Wrong on the merits: SPP is not a
  model ISO, and the sibling test `test_every_model_iso_is_registered` pins the
  registry to exactly the six. This would add an unregistered seventh ISO to
  placate a lint.
* *Reword the test to `match="spp"`.* That is relaxing a test to reach green,
  which the charter forbids — the exact path **is** the assertion's content, and
  weakening it would stop the test from checking that the message tells a
  contributor where to put the module.

The entry notes what the deletion-provenance entries above it do not: this target
can never "land", so unlike them the entry is permanent by construction.

### After

```
script-refs: OK (13 known-dangling tolerated)
refactor-guards passed.   EXIT: 0
```

---

## 6. Verification — read directly, on the rebased tree

`main` advanced from `369e8fbb` to `1aab49a0` mid-session, and one of the nine
reformatted files (`tests/scoring/test_audit_keepers_pointers.py`) was edited on
main in that window. The branch was rebased and **the entire battery re-run**;
every number below is from the post-rebase tree, not the pre-rebase one.

| command | before | after |
|---|---|---|
| `ruff check .` | **1** (F401) | **0** — All checks passed |
| `ruff format --check .` | **1** (9 files) | **0** — 1356 formatted |
| `compileall src scripts` | 0 | **0** |
| `scripts/ci_refactor_guards.py` | **1** (spp) | **0** |
| ten facade files (the real job) | **1** | **0** — 90 passed |
| charter's four facade files | **1** (1 failed, 34 passed) | **0** — 35 passed |
| pinned-key job (2 files) | 0 | **0** — 24 passed |
| `test_interchange_parity.py` + `test_runner.py` | **1** (6 failed, 75 passed) | **0** — 81 passed |
| `tests/unit/policy/` | 0 | **0** — 311 passed |

All four commands the charter names exit 0, as do the two further job steps it
did not cover.

### One pre-existing red, out of scope, deliberately not chased

`tests/unit/model/test_d62_published_going_forward_bar.py` — 15 failed / 13
passed, **identical with the branch stashed**, so not this lane's:

```
E  market_sim.data.avoidable_cost_rate.PublishedBarUnavailable: no published
   avoidable-cost-rate partition for PJM: run
   scripts/data/curate_capacity_market_avoidable_cost_rate.py
```

This is an **environmental** artifact of this session's `DATA PROFILE: code`
(the curated partition is not hydrated), not a code defect, and it is not in the
charter's scope. It is recorded here rather than silently passed over. Whether
the `Fast test tier` runner reproduces it depends on that job's sparse-checkout
set — §7 reads the answer off the actual CI run.

---

## 7. Flip-set reading on this PR's CI run, job by job

R-AE's six required checks: **Ruff lint + format** · **Pinned default cache key** ·
**Structural refactor guards** · **Cache-key registration guard** ·
**Fast test tier** · **Rule-22 quarantine gates**.

*(Filled in from the API on this PR's run, read job by job rather than off the
rollup — the form §6 of `FINDING-y15-flipset-sweep-2026-09-06.md` uses.)*

