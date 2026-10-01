# FFR-3M — kill-resume drill re-run and FF-3E part-c adjudication

**Session:** FFR-3M (2026-08-04) · **Lane:** small · **HEAD at dispatch:** `d7363b0e` · **rebased onto:** `f53fff65` (mechanism re-verified unchanged there; `scenarios.py` line 9760→9834, `runner.py` 890/1431/2135 unmoved)
**Instrument:** `scripts/ff_readiness_battery.py kill-resume` (FFR-3J `ef5695b0` discriminator)
**Evidence:** `docs/handoffs/ffr-3m/` (three result JSONs + the probe driver)

---

## 0. Verdict

**FF-3E part c = MECHANISM 2, ALTERNATE OPTIMA.** The resumed solve lands on a
different vertex of the optimal face. Per the dispatch adjudication: **no basis is
pinned**, no tolerance widened, no drill disabled, and **no code was changed** — this
session is a measurement and a write-up.

The cause is identified, and confirmed causally rather than inferred:
**`ScenarioConfig.forecast_xyear_warmstart` (default `True`) warm-starts the control
leg's first post-kill year from the prior year's in-process basis, while the resumed
leg has no basis to inherit and solves that year cold.** Warm and cold land on
different vertices of a degenerate optimal face.

Because that is a solver-freedom question and not a plumbing defect, the
determinism-versus-freedom trade is escalated to the owner in §5 rather than decided
here.

---

## 1. What was run

Three cells, all NEISO 2026–2028 (the drill's own T0 window; rule 12 — years sequential,
≤2 concurrent invocations, NEISO is the light ISO). Driver:
`docs/handoffs/ffr-3m/ffr3m_probe.py`.

| cell | what it does | why |
|---|---|---|
| **A. drill-default** | the pre-specified drill, shipped config | the required adjudication |
| **B. control-vs-control** | two INDEPENDENT full-window runs, separate cache roots, **no kill** | the drill alone cannot separate "resume is nondeterministic" from "this config is nondeterministic at all" |
| **C. drill-noxyear** | the drill with `forecast_xyear_warmstart=False` | causal test of the named mechanism |

Cell B was added because `docs/cross-year-warmstart.md` §"Measured" names a **second**
alternate-optima source independent of resume: at default multi-threaded HiGHS "even
cold-vs-cold drifts, because parallel dual simplex breaks marginal ties
nondeterministically." Without B, a drill FAIL is unattributable between the two.

---

## 2. Results

### A. drill-default — FAIL (reproduces the FFR-3A-2 §6.4 signature)

`killed_mid_horizon` ✓ · `cache_key_match` ✓ · `cached_years_loaded_not_resolved` ✓ ·
`result_identical` ✗ · **`green` = false**

2026 and 2027 (cache-loaded) are **bit-identical on every field**. The resume plumbing
itself — key stability, load-not-re-solve, ledger reconstruction — is sound. All of the
divergence is in 2028, the first freshly-solved year after the resume:

| signal | control | resume | |
|---|---|---|---|
| `dispatch_shape` | `[419, 8760]` | `[419, 8760]` | same |
| `dispatch_sum` | 113461235.316 | 113461235.316 | same |
| `dispatch_hash` | `a45685089f83d177` | `4d5bfb6c7302fccd` | **DIFF** |
| `dispatch_sorted_hash` | `f39ece09d05911b1` | `3acb8156c208b2a1` | **DIFF** |
| **`dispatch_multiset_hash`** | `ad01eb3b702cf228` | `fafa5cc4db3c5828` | **DIFF** |
| `price_shape` | `[5, 8760]` | `[5, 8760]` | same |
| `price_sum` | 2454073.548 | **2454071.122** | **DIFF** |
| `price_hash` | `e94d20aab560b046` | `befd780ad2777427` | **DIFF** |
| **`price_multiset_hash`** | `4dd7ad73323e3761` | `19a1d79fbcba3d9a` | **DIFF** |

Ledger counts identical (`n_retire` 0/0, `n_thermal_add` 0/0, renew 0/0, storage 0/0).

**Reading the verdict off `*_multiset_hash` as instructed:** multiset hashes **differ**,
with `*_shape` identical on both arrays. Not a permutation — genuinely different numbers.
→ **Mechanism 2.** `*_shape` matters here: it rules out the `(a,b)` vs `(b,a)` twin that
`tobytes()` alone cannot separate, so "different numbers" is not an artifact of a
reshaped array.

### B. control-vs-control — byte-identical (this is what makes the attribution possible)

Two independent fresh runs of the same config, in separate cache roots:

| year | dispatch byte | dispatch mset | price byte | price mset |
|---|---|---|---|---|
| 2026 | same | same | same | same |
| 2027 | same | same | same | same |
| 2028 | same | same | same | same |

`cache_key_match` ✓, `identical` ✓. **The model is deterministic run-to-run at default
settings**, multi-threaded HiGHS included. This eliminates the second candidate source
and isolates the divergence to the resume path. Without this cell the FAIL would remain
ambiguous.

### C. drill-noxyear ablation — **GREEN**

`forecast_xyear_warmstart=False`, everything else identical:

`result_identical` ✓ · **`green` = true** — all three years byte-identical **including
2028**, which is freshly solved on resume in this cell too (`from_cache=false`).

This is the causal proof. One flag flips the drill from FAIL to GREEN.

**The most diagnostic number in the whole exercise:** in cell C, 2028's `price_sum` is
**2454071.122** — which equals the **resume** leg's value from cell A, *not* the control
leg's 2454073.548. In cell C both legs solve 2028 cold and agree. So the **cold solve is
the reproducible one, and the warm control leg is the outlier**. The resumed run was
producing the cold-canonical answer all along; the drill's "control" is the leg carrying
the warm-start perturbation.

---

## 3. The mechanism, in code

1. `ScenarioConfig.forecast_xyear_warmstart: bool = True` — `config/scenarios.py:9834`.
2. `runner.py:890` — `forecast_xyear_cache = [] if config.forecast_xyear_warmstart else None`.
3. `runner.py:2135` — passes `xyear_warmstart=config.forecast_xyear_warmstart` to
   `run_energy_solve` as an **explicit bool**.
4. `pipeline/solve.py:219-223` — an explicit bool is the caller's authoritative decision
   and **overrides** the env var; only `xyear_warmstart is None` defers to
   `MARKET_SIM_WARMSTART_XYEAR`.
5. `runner.py:1431` — `if is_cached(...): result = load_result(...)`. The cached branch
   **never enters the solve**, so it never exports a basis into `forecast_xyear_cache`.

Composition: in the control, 2027 solves in-process and hands its basis to 2028. In the
resume, 2027 is loaded from cache and exports nothing, so 2028 solves cold. The two legs
run the *same LP* from *different starting bases* and stop at different vertices of a
degenerate optimal face — identical total generation (energy balance), objective equal to
rounding, per-unit dispatch and zonal prices reshuffled among units tied at the margin.

`docs/cross-year-warmstart.md` §"Within-year neutrality does not survive that loop"
already describes exactly this effect and calls it "alternate-optima reshuffling among
units tied at the marginal price."

---

## 4. Two dispatch premises that did not hold

Recorded because both would mislead a successor.

**(a) "Cross-year warm start is RULED OUT (`MARKET_SIM_WARMSTART_XYEAR` defaults off)."**
The env var does default off, but **the forecast path never reads it.** It is gated
entirely by `forecast_xyear_warmstart`, which defaults `True` and overrides the env var
by design (`solve.py:219-223`, rule 24 `[R-REGISTRY]` — deliberately a registry field so
the calibration CLIs' default-ON env var cannot reach the forecast). Cross-year warm
start was not ruled out; it was the cause.

**(b) "The aggregates ALREADY match, and that is the entire finding."**
No longer true at this HEAD. `dispatch_sum` still matches exactly, but **`price_sum`
differs** (2454073.548 vs 2454071.122, ~1e-6 relative). The finding is narrower than
"identical aggregates, different bytes." This also means the standing instruction not to
weaken the drill into an aggregate comparison is doubly right: an aggregate check would
now fail too, but for a reason it could not explain.

Neither correction changes the adjudication — it strengthens it. Both point at genuinely
different numbers, i.e. Mechanism 2.

---

## 5. Owner design question — determinism vs solver freedom

Not decided here. The trade, stated:

**Option 1 — leave `forecast_xyear_warmstart=True` (status quo).**
Keeps the ~2.3× steady-state P0 speedup that motivated it. Cost: **a killed-and-resumed
forecast is not reproducible from its own cache.** Any year solved after a resume differs
from the same year solved in one pass. FF-3E part c stays red permanently — this is not a
bug the drill can ever pass, because a resumed run structurally cannot inherit a basis it
never solved. Worse for provenance: two bundles with the same `cache_key` can hold
different numbers depending on whether the run was interrupted, and nothing in the bundle
records which.

**Option 2 — `forecast_xyear_warmstart=False` for forecast bundles.**
Drill goes GREEN (measured, cell C). Resume-reproducibility becomes structural. Cost: the
P0 speedup, which on a 25-year horizon is the difference the flag was introduced to buy —
material for full-horizon T1 runs, negligible for a 3-year T0. Note the cold answer is
also the *canonical* one (§2C), so this makes the reproducible result the default result.

**Option 3 — pin a basis so warm and cold agree. Explicitly NOT recommended**, and the
dispatch forbids it. It would mean freezing a particular vertex of the optimal face as
"the" answer, which is a modelling claim the LP does not support: the units involved are
genuinely tied at the margin and the model is indifferent between them. Pinning buys byte
determinism by inventing a tie-break with no market meaning — and it would have to be
maintained against every future change to fleet ordering or offer construction.

**What pinning costs, concretely:** the reshuffle is not cosmetic on the forecast path.
`cross-year-warmstart.md` measures it tipping a retire/keep decision in ERCOT
(2027 reshuffle → different 2028 fleet, objective relΔ 8.3e-4, max |Δ zonal price| 0.19
$/MWh), because `capacity.evolve_fleet`'s retirement screen reads **per-unit dispatch
volumes**. So a pinned basis does not merely stabilise bytes; it silently selects which
marginal units retire. That is a market-structure consequence of a solver setting, which
is the kind of coupling rule 1 `[R-STRUCT]` exists to prevent.

My reading, offered as input and not as a decision: **Option 2 for anything whose bundle
is an artifact of record**, on the grounds that a forecast bundle that cannot be
reproduced from its own cache is not a provenance-bearing artifact, and that the speedup
is a convenience while reproducibility is a correctness property. But the horizon-scale
cost is real and is the owner's call, and it interacts with the open D-9 decision.

---

## 6. When it broke — bounded to a commit, but not to a minimal diff

Stating the limit plainly rather than guessing, per the dispatch.

A GREEN record does exist: the committed `frontend/data/hindcast/ff-3e-readiness.json`
at `b40f7405` carries `kill_resume_drill.green = true`, all three years equal, produced
**2026-07-20** by session FF-3E. The FAIL was recorded at `720a0c01` (FFR-3A-2,
2026-08-04). Only two versions of that artifact exist in history.

`forecast_xyear_warmstart` first appears at **`b40f7405`**, already defaulting `True`.
Its parent has **zero** occurrences of `forecast_xyear_warmstart` in `scenarios.py`,
**zero** occurrences of `xyear` in `runner.py`, no `scripts/ff_readiness_battery.py`, and
no `docs/cross-year-warmstart.md`.

**Why this is not a usable bisect:** `b40f7405` is a bulk "Add files via upload"
(2026-08-03) that introduced the drill script, the warm-start field, and the warm-start
doc *simultaneously*. The tree FF-3E actually ran against on 2026-07-20 is **not in this
repository's history** — it was collapsed by that upload. So the commit where the field
appears can be named, but no minimal diff that flipped GREEN→FAIL can be isolated, and
the 210-commit range between the two artifact versions is an artifact-commit range, not a
behaviour-change range.

What *is* established without the bisect: the pre-upload tree had no cross-year
warm-start on the forecast path at all (grep count 0), which is precisely the regime
`cross-year-warmstart.md` still describes, and precisely the regime cell C reproduces
GREEN. The GREEN record and the cold-only regime coincide; the FAIL record and the
warm-by-default regime coincide.

Corroborating detail: the GREEN artifact's per-year entries have **no** `*_multiset_hash`
keys, confirming it predates the FFR-3J instrumentation and was a byte-hash-only pass.

---

## 7. Scope notes and hygiene

- **No code changed.** Mechanism 1 would have licensed a determinism fix plus a
  regression test; Mechanism 2 does not. Nothing under `src/market_sim/` or `scripts/`
  was touched, so the "verify no keeper moves / STOP-THE-LINE if one does" check is
  vacuous by construction — no keeper *can* move. Keepers were read at session start and
  match the dispatch for all six ISOs.
- **No tolerance widened, no aggregate substitution, drill not disabled.**
- **No parameter moved in response to any score** (rules 1/11/14). Cell C is a controlled
  ablation for attribution, not a tuning change, and it is **not** a proposal to flip the
  shipped default — that is §5's owner question.
- **Holdout freeze respected.** All cells are forecast-mode 2026–2028, which the freeze
  explicitly does not block. No backcast year solved, no marker consulted as spendable.
- **Registration:** none. This session produced no forecast/hindcast run worth
  registering — three diagnostic drill cells, not a hindcast. Evidence is committed as
  flat JSON under `docs/handoffs/ffr-3m/` instead.
- **Rule 28 (mechanism matrix):** no cell claimed. The matrix is "one row per **model
  mechanism**"; `forecast_xyear_warmstart` is a solver warm-start flag whose design
  intent is result-neutrality, not a market mechanism, and this session tested no market
  mechanism in any ISO. `scripts/check_mechanism_matrix.py` passes at HEAD.
  **Observation for the owner:** that flag has no matrix row despite being
  solve-affecting on the forecast path — rule 28(c) binds PRs that *add* a field, and
  this one arrived via the bulk upload, so CI never saw it as new. Flagged, not
  unilaterally added.

## 8. Stale documentation found (not corrected here)

`docs/cross-year-warmstart.md` header states:

> **Status: default ON for the calibration/backcast path** … The forecast path
> (`runner.py`) stays **cold-only** — see [Why the forecast path is not wired].

and §"Why the forecast path is not wired" says the forecast wiring "was prototyped and
then **rejected**."

Both are **false at HEAD**: the forecast path *is* wired (`runner.py:2135`) and defaults
**on** (`scenarios.py:9834`), under what `runner.py:2022` cites as "plan §7 H-3, owner
decision D-9". CLAUDE.md makes code the source of truth, so the doc is stale.

Left uncorrected deliberately: the doc's §"Why the forecast path is not wired" is the
written record of the *reasoning* that the forecast feedback loop makes warm start
non-neutral — reasoning this session just confirmed empirically. Rewriting it is entangled
with the §5 owner decision (if Option 2 is chosen the doc becomes accurate again), so it
should be resolved by whoever settles §5, in one edit, rather than patched twice. Raised
here so it is not mistaken for an oversight.

---

## 9. Reproduction

```
uv sync && uv run python scripts/regenerate_clean.py     # prerequisites, in this order
uv run python docs/handoffs/ffr-3m/ffr3m_probe.py drill        --work-dir <wd> --out drill.json
uv run python docs/handoffs/ffr-3m/ffr3m_probe.py control      --work-dir <wd> --out control.json
uv run python docs/handoffs/ffr-3m/ffr3m_probe.py drill-noxyear --work-dir <wd> --out noxyear.json
```

`drill` is exactly `ff_readiness_battery.kill_resume_drill` with no modification;
`control` and `drill-noxyear` are the two added cells. Absolute hashes are HEAD-specific
(the model moved between FFR-3A-2 and here — e.g. 2027 `n_retire` is 34 at this HEAD vs
38 recorded in §6.4); the **within-session comparisons** are the evidence, and each cell
is internally self-consistent.
