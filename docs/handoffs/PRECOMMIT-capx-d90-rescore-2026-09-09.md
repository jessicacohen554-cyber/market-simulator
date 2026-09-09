# PRECOMMIT — capx D90: the `neiso-t3` re-score on D88-repaired code

**Lane:** capx D90-RESCORE · **Branch:** `claude/neiso-t3-d90-rescore-u4b5bw` · **Date:** 2026-09-09
**Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Authority:** OWNER RULING **Q63** (2026-09-08, capx ledger §0bg.3(a)) — *"Charter the re-score as its
own lane now."*
**Predecessor:** `docs/handoffs/FINDING-capx-d88-2026-09-08.md` (the repair being re-scored)

> **Everything below is fixed BEFORE the solve.** The predictions in §5 are graded against the
> realized re-score in the FINDING, whether they hit or miss. Rule 1 `[R-STRUCT]` governs: the D88
> repair is in because duplicate-free fleet identity is structurally correct, and it stays in
> whatever this re-score says. This lane produces the honest number; it does not vindicate D88.

---

## 0. STATUS OF THE BLOCKING DEPENDENCY

capx **D88 (PR #5661) HAS MERGED** — `725ada79`, an ancestor of this branch's base `796a1e18`.
The repair is present and verified in-tree, not assumed:

| artifact | site | verified |
|---|---|---|
| vintage-stamped re-mint | `model/capacity_evolution/ccs.py:702` — `f"gas_cc_ccs_{bin}_{zone}_r{year}"` | present |
| duplicate guard | `data/fleet/arrays.py:3314` — `"duplicate unit_id in fleet passed to generators_to_fleet_arrays"` | present |

The charter's "the STOP names an act, not a session" clause is therefore discharged with no wait.

---

## 1. PHASE 0(a) — WHICH RUN, CONFIRMED AT THIS HEAD

Re-derived from this branch's own bytes, not carried from the charter:

```
frontend/data/forecast/ff-verdicts.json  key            neiso-t3
  provenance.run_id                                     neiso-2026-2050-t3-golden3-d60
  provenance.cache_epoch                                f04fd06348e1623d
  provenance.scored_at_sha / date                       7ed062ba9a68 / 2026-09-06T03:59:42Z
  determination                                         HOLD
  provenance.known_defect                               PRESENT (the Q62 placeholder)
bundle                     results/ff-t3-neiso-golden/bau-d60/NEISO/f04fd06348e1623d
```

Every element of the charter's identification is confirmed. Additionally measured here:

* **Exactly ONE record in the committed `ff-verdicts.json` carries `known_defect`, and exactly one
  carries `cache_epoch = f04fd06348e1623d` — both are `neiso-t3`.** D88 §6's "four generated
  sidecars" is a statement about the *generated* `frontend/data/forecast/registry/` namespace
  (gitignored, rebuilt by `--reindex`), not about the committed snapshot. The committed surface this
  lane edits has one record.
* **`neiso-2026-2050-t3-golden3-d65br` is NOT re-scored here and has no verdict to replace.** Its
  bundle (`bau-d65br`, key `0fc42cb56c24d544`) is in D88's colliding set, but every `neiso-t3-*`
  record whose provenance points at it carries `run_id: None` (an UNSCORED stamp). Reported, not
  manufactured — the same posture D88 §6 took.

**Scope, stated as an inclusion and an exclusion.** RE-SCORED: `neiso-t3` alone. NOT re-scored: the
four other committed NEISO T3 goldens (`bau`, `bau-prera-2026-08-31`, `bau-d46`, `bau-d65br`) and the
eight `neiso-t3-pre-*` history records, none of which carries both a stamped `run_id` and the flag.

---

## 2. PHASE 0(b) — THE RECIPE, AND THE KEY THE RE-SOLVE WILL REALIZE

The committed bundle stores its recipe as `config.yaml` (799 keys — matching the standing verdict's
own FC-7 `run_config` row, "799 config keys"), a `yaml.safe_dump(asdict(config))` round-trip.

**The reconstruction reproduces the recorded key EXACTLY:**

```
recorded key (bundle dir name)                                    f04fd06348e1623d
reconstructed from its own config.yaml at HEAD (post-D88)         f04fd06348e1623d   ← IDENTICAL
unknown payload keys dropped in the reconstruction                0
```

…**once one HEAD-side defect is accounted for**, which is §3's first finding. Corroborating the
charter's own reasoning: ids are not hashed, and `solve_surface.SURFACE_MODULES` excludes
`data/fleet` and `model/capacity_evolution`, so **D88 moves no key**. This is a SAME-KEY
invalidation, exactly as D88's cache-epoch entry (rather than a re-key) asserted.

**The key the re-solve will actually realize is NOT `f04fd06348e1623d`** — see §3.1. That is a
*pure addressing* consequence of an unrelated, behaviourally inert HEAD defect, and it is
**benign for this lane**: a distinct key guarantees the re-solve cannot cache-hit or clobber the
stale bundle.

---

## 3. PHASE 0(c) — G-DRIFT, ON THE RECORDED-KEY BASIS

Per the charter, the basis is the bundle's **recorded cache key**, never
`git diff <keeper git_sha> HEAD` (dead after the 2026-08-16 history rewrite). Four channels can move
what a re-solve does. Each is audited and classified.

### 3.1 CHANNEL A — config fields · **ONE LIVE DEFECT FOUND, BEHAVIOURALLY INERT**

**STOP-THE-LINE, SURFACED FOR ITS OWNER.** At this HEAD **no committed run payload anywhere in the
repository reproduces its own recorded cache key — 0 of 173** — and the default key is off its pin:

```
ScenarioConfig().cache_key()  at HEAD          72341e34fd261997
_PINNED_DEFAULT_KEY (tests/unit/model/…)       547053bdfccd4264
```

**Attributed to a single field, by experiment rather than inspection.** Registering
`pjm_seam_neighbour_hourly_ladder` in `_CACHE_KEY_OPTIONAL_FIELDS` at a frozen `"False"`
(in memory only — no file edited) restores reproduction:

| | before | after |
|---|---|---|
| committed payloads reproducing their key | **0 / 173** | **78 / 173** |
| `bau-d60` (this lane's target) | ✗ `ae317e63263c8eef` | ✓ **`f04fd06348e1623d`** |
| `bau-d65br` (D88's control) | ✗ `4a5f9695eeae815a` | ✓ **`0fc42cb56c24d544`** |

The field was added by `f2a834de` (PJM hourly neighbour-anchored seam ladder) **without a
registration entry**, so it always enters the hash and moves every key in the program. That the
in-memory registration reproduces *D88's own reported control key to the character* corroborates
D88's audit and dates the regression after D88's measurement.

**This is D91's, not mine, and it is not repaired here** (charter boundary; the 16 red pin tests D88
§7 surfaced are the same signature). **It does not confound this re-score:**
`pjm_seam_neighbour_hourly_ladder` is referenced in exactly one module,
`model/interchange/pjm.py`, is PJM-scoped, and holds `False` — **INERT for a NEISO forecast solve.**
Its only effect here is the directory the arm lands in.

### 3.2 CHANNEL B — fields postdating the bundle · **ALL 29 INERT BY CONSTRUCTION**

29 `ScenarioConfig` fields are absent from the bundle's payload. For each, the value the bundle
*effectively ran at* (`registration_time_default`) is compared with the value a re-solve at HEAD
resolves. **All 29 AGREE; zero differ.** Each is default-off (`False` ×24, `None` ×4, `'off'` ×1),
covering `capacity_screen_peak_measured_hindcast`, `pjm_vre_accreditation_vintage`,
`f923_gas_price_plausibility_screen`, `hydro_budget_period_by_instrument`,
`netload_drag_merit_allocation`, `spp_gas_commitment_bridge` and the rest. **No behavioural drift
from schema growth.**

### 3.3 CHANNEL C — the D79 solve surface · **INERT, MEASURED**

```
solve_surface.moved_rows("NEISO")   {}   (empty)
solve_surface.applicable_epochs()   []   (empty)
solve_surface.SOLVE_EPOCHS          ()   (empty)
```

No registry table this ISO reads has moved off its declaration. The surface contributes nothing to
the key or to the solve.

### 3.4 CHANNEL D — resolved posture · **TWO GENUINELY LIVE HUNKS, AND THEY ARE PINNED OUT**

Assembling the config the way the CLI does today (`reference_config(iso="NEISO", 2026, 2050,
cmc=False, golden_posture=True)`) differs from the committed recipe in **8 fields**. Six are false
alarms and two are real:

| field | committed | HEAD CLI | verdict |
|---|---|---|---|
| `ordc_lolp_shift_sigma` | 0.0 | 0.5 | **INERT** |
| `ordc_lolp_sigma_mw` | 900.0 | 1400.0 | **INERT** |
| `ordc_mcl_mw` | 1200.0 | 3000.0 | **INERT** |
| `ordc_multistep_floor` | False | True | **INERT** |
| `ordc_voll` | 2000.0 | 5000.0 | **INERT** |
| `scarcity_price_overlay` | True | False | **INERT** |
| `ccs_retrofit_fixed_cost_co2_scaling` | **False** | **True** | **LIVE** |
| `ccs_retrofit_vom_adder` | **8.0** | **2.95** | **LIVE** |

**Why the six are INERT, established rather than assumed.** They are exactly
`iso_configs.get_iso_config("NEISO").default_scenario_overrides` (6 entries, read at HEAD and
reproduced field-for-field), applied at solve time and not by `reference_config`. They are
**identical in all five committed NEISO T3 goldens** — `bau`, `bau-prera`, `bau-d46`, `bau-d60`,
`bau-d65br` — i.e. unchanged across the whole family. The apparent difference is an artefact of
comparing against a pre-resolution config, not drift.

**Why the two are LIVE.** Both are capx D65 landings that postdate `bau-d60` and both bite from the
first retrofit year, 2028 — inside a horizon in which this recipe converts ~10.4 GW over 2028–2031.
The cross-golden table dates them precisely: `ccs_retrofit_vom_adder` is 8.0 in `bau`/`prera`/`d46`/
`d60` and 2.95 in `d65br` and at HEAD; `ccs_retrofit_fixed_cost_co2_scaling` is absent in the early
three, `False` in `d60`, `True` in `d65br` and at HEAD.

**Rule 29(b): a LIVE hunk earns a control solve — OR it is removed from the arm. This lane removes
it.** The charter's instruction is *"the committed recipe unchanged but for D88's repair being
present in the code"*, so both fields are **pinned back to their committed values**, making D88 the
only difference between the scored bundle and the arm. Pinning is preferred over a control solve
because it isolates D88 *exactly* rather than differencing two changes; and it is not a tuning
channel (rule 24 `[R-REGISTRY]`) — both values are recorded in `run_config.json`, and both are
*restorations of the scored run's own recipe*, chosen before any solve and never against a result.

### 3.5 CHANNEL E — DERIVED-INPUT drift · **THE ONE CHANNEL G-DRIFT CANNOT SEE, AND IT IS OPEN**

This is D88 §3's methodological finding and the charter's explicit warning. `data/clean` is
gitignored, derived and rebuilt per container; D88 found a 2027 ledger delta against the committed
bundle **in a year its own change is provably inert**, and attributed it 100 % to the rebuild.

**This container had no `data/clean` at all** (0 datatypes at session start; rebuilt here, ≈55 min).
It is therefore **not established** that the committed bundle is a valid *byte-level* control, and
this lane does not assume it is. **Pre-registered test, run before any attribution is made:**

> **T-REPRO.** Solve **2026–2031** on the pinned recipe and compare all six `evolution_<year>.json`
> to the committed bundle's. D88 is **provably inert** across that whole span — `ccs.py:187` and
> `ccs.py:366` both `return fleet, []` when `year < config.ccs_retrofit_available_year` (= 2028), so
> no converted representative exists before 2028 and no duplicate id can exist before the first
> collision in 2032. Any delta in 2026–2031 is therefore **container-derived-input drift, not D88.**
>
> * **T-REPRO PASSES (all six byte-identical)** ⇒ the committed bundle IS a valid byte-level control;
>   the arm is differenced directly against it and every delta is D88's.
> * **T-REPRO FAILS** ⇒ rule 29(b)'s LIVE case; a same-container **pre-D88 control** is solved (HEAD
>   with only D88's three files reverted, in a throwaway git worktree — nothing in this working tree
>   under `src/market_sim/` is edited, nothing is committed) and **that** is the control graded
>   against, exactly as D88 did. The delta is then reported as D88's own.

**A note on what T-REPRO can and cannot license.** It bears on *attribution* — which side of the
comparison owns a movement. It does not bear on the *verdict*: the re-score's headline is the honest
FF-2D reading of a run solved at HEAD on the scored recipe, and that is well defined either way.

### 3.6 G-DRIFT VERDICT

**Form 4 is VALID for the code channel: no code drift reaches a NEISO forecast solve except D88's own
repair.** One HEAD defect (§3.1) moves addressing only. Two live posture hunks (§3.4) are pinned out.
The derived-input channel (§3.5) is **open and tested empirically before attribution**, never assumed.

---

## 4. THE SOLVE — pre-registered, ONE INDIVISIBLE INVOCATION

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
uv run python scripts/run_full_horizon.py \
    --iso NEISO --start-year 2026 --end-year 2050 \
    --golden-posture --full-solve-authorized \
    --no-ccs-retrofit-fixed-cost-co2-scaling \
    --set ccs_retrofit_vom_adder=8.0 \
    --out-dir results/ff-t3-neiso-golden/d90-rescore
```

* **The horizon is NOT shortened.** Rule 12 `[R-PARALLEL]` makes years sequential within a run and
  the evolution chain links them, so the span cannot be sharded; a T3 golden scored on a truncated
  span is a different instrument.
* `ccs_retrofit_capex_co2_scaling` needs no flag — Q42 made it the dataclass default, and the
  committed recipe carries it armed.
* **Before the arm is graded, the resolved `run_config.json` is diffed field-for-field against the
  committed `config.yaml`.** The expected result is a **zero-field diff**, which would mean the arm
  realizes key `f04fd06348e1623d` under a correct registration — i.e. the arm and the scored bundle
  are the same recipe and differ only by D88's code. A non-zero diff is a STOP.

**Rule 31 `[R-RETAIN]` binds absolutely.** The bundle family's heavy artifacts are already gitignored
by the standing `/results/ff-t3-neiso-golden/*/*/*/*.parquet|*.npz|hourly/` rules; the control
bundle, if T-REPRO earns one, is gitignored in full before it is written. **Nothing solved in this
session is deleted, whatever the re-score says** — the ercot-255 incident is precisely this lane's
cost profile, and a 25-year NEISO T3 is dearer than what it cost there. The final report asks the
promotion question explicitly and states that the bundles live on local disk and will not survive
the container.

---

## 5. PHASE 0(d) — WHAT I EXPECT, PER LEG, BEFORE SOLVING

**The measured basis I am reasoning from** (D88 §2, on `bau-d65br` 2026–2040): retirements are a
**TIMING** shift, not a level shift — the same four `gas_cc_ccs` units totalling 955.076 MW move from
2040 to 2038, and a further 1,115.861 MW retires in 2040; cumulative through 2040 goes
962.7 → 2,078.6 MW (**2.16×**), and the 2040 reserve margin falls **0.090426 → 0.051645
(−3.88 pp)**.

**Which legs can move at all.** The 25-year golden feeds **FC-1, FC-2, FC-5, FC-7, FC-8**. **FC-3**
(T1-H hindcast, 2021–2025) and **FC-4** (T1-X crossover, 2023–2027) are scored from separate bundles
whose windows lie **entirely below `ccs_retrofit_available_year = 2028`**, so D88 is *provably* inert
in both (§3.5's citation) — they are carried, and that is a proof, not a convenience. **FC-6**'s
paired P1–P3 arms are separate solves; whether they are re-solved is decided on the arm's measured
wall time and reported either way.

| # | leg | now | **prediction** | reasoning · falsifier |
|---|---|---|---|---|
| **P1** | **FC-2 row2** terminal RM | **PASS**, final RM **5.3 %** in [3.8 %, 38.8 %] | **FLIPS to FAIL**; final RM in **[0.5 %, 4.5 %]** | Only **1.55 pp** of headroom sits above the band floor, and D88's measured 2040 RM depression is **−3.88 pp**. *Falsifier: final RM ≥ 3.8 %.* **The risk I am accepting:** 2050 RM is an *equilibrium* set by entry economics, not a fleet remnant — 2041–2050 gives economic entry ten years to rebuild against the higher prices a tighter fleet produces. If entry fully compensates, P1 is wrong. |
| **P2** | **FC-2 row1** I12 band | PASS | **degrades to CAVEAT or FAIL** — *low confidence, ~50/50* | A deeper 2038–2040 trough is what I12 is built to catch. Stated as a coin-flip rather than dressed up. |
| **P3** | **FC-2 row3** cobweb I13 | FAIL `gas_cc(13)` | **stays FAIL**, gas_cc count **≥ 13** | Earlier exits plus the entry response that chases them is more oscillation, not less. |
| **P4** | **FC-2 row4** backstop share | PASS 0.5 % ≤ 10 % | **stays PASS**, share rises, **< 10 %** | A tighter fleet pulls more backstop build; 0.5 % has two orders of headroom. |
| **P5** | **FC-1** I3 dump | FAIL, 2.36 %→7.97 % 2043–2050 | **stays FAIL**; magnitudes move **< 2 pp**. **I decline to call the sign** | Two effects oppose: retiring dispatchable thermal *reduces* the must-run floor that forces dumping, while renewable-weighted replacement entry *increases* it. I cannot rank them ex ante and will not pretend to. |
| **P6** | **FC-5** `co2@2040` | model 9.5792 vs table 4.4883 (**+113.4 %**) | **IMPROVES**: co2@2040 **falls**, gap narrows into **[+80 %, +110 %]** | Less gas capacity ⇒ less gas generation ⇒ less CO2, and the model is *far above* the table, so the movement is toward it. **This is the one leg where I expect D88 to help.** |
| **P7** | **FC-5** category | CAVEAT (26 divergences) | **stays CAVEAT**; divergence count moves by **≤ 2** | The list is long and structural; one improving row does not clear it. |
| **P8** | **FC-3 / FC-4** | FAIL / FAIL | **UNCHANGED — provably** | Both windows end before 2028; `ccs.py:187,366` return early, so no converted representative and no duplicate id can exist. |
| **P9** | **FC-7** | PASS, 7 DOF entries | **PASS**, **8–9** entries, all IDENTIFIED | The two §3.4 pins are now non-default and must be ledgered. *Risk: an UNIDENTIFIED entry fails FC-7.* |
| **P10** | **FC-8** | PASS, 6.7 min | **PASS**, wall **5–25 min** | Same ISO, same span, cold `data/clean`. |
| **P11** | **DETERMINATION** | **HOLD** | **HOLD → HOLD** | D88 cannot reach FC-3/FC-4 (P8) and cannot plausibly clear FC-1 I3 or FC-2 row3. Four gating FAILs cannot become zero. |

**My pre-declared one-sentence summary, to be graded as written:** *the repair will not move the
determination; it will most likely make FC-2 strictly WORSE at row level (P1) while nudging FC-5's
CO2 toward its corridor (P6) — i.e. the corrected trajectory scores somewhat worse on adequacy and
somewhat better on emissions, and stays HOLD.*

**And the disposition that follows either way.** Rule 1 `[R-STRUCT]`: if P1 hits and adequacy
degrades, **the repair still stays in** — a duplicate-free fleet identity is structurally correct and
a worse residual is not grounds to revert it; the correct response is to route the exposed adequacy
weakness as a root cause. If P1 misses and the re-score improves, that is reported as a measurement
and **still does not license the claim that D88 makes the model more accurate**, which is more than
one ISO's one run can carry.

---

## 6. THE FLAG — the exit condition, fixed in advance

`provenance.known_defect` on `neiso-t3` is D88's placeholder for this moment. Exactly two outcomes
are permitted, and the choice is not discretionary:

1. **Re-score completes** ⇒ the flag is **REMOVED** and the new verdict registered in the same commit.
   The board must never assert a defect is *pending resolution* once it is resolved.
2. **Re-score cannot complete**, for any reason ⇒ the flag is left **EXACTLY as it is**, byte for
   byte, and the FINDING says why. The flag is **never removed without a verdict to put in its
   place.**

---

## 7. BOUNDARIES

**No file under `src/market_sim/` is edited by this lane.** D88 owns `ccs.py`'s conversion block,
`arrays.py:3651` and `evolve.py`'s exempt-set lines; the concurrent **D91** lane owns the cache-key
pin tests — including the `pjm_seam_neighbour_hourly_ladder` registration gap this lane *found and
measured* in §3.1 but does **not** repair. If work reaches any of those, this lane STOPS and reports
the overlap. The 16 red pin tests are D91's; if still red at solve time they are reported and stepped
past, not fixed.

---

## ADDENDUM A — three pre-solve results, recorded BEFORE any LP is spent

Written and pushed while `data/clean` rebuilt, ahead of the arm. Nothing here is graded against a
result, because no result exists yet.

### A.1 The §4 pre-solve STOP check PASSES — the pinned recipe is the scored recipe

Assembling the arm's config exactly as the runner does — `reference_config("NEISO", 2026, 2050,
cmc=False, golden_posture=True, ccs_retrofit_fixed_cost_co2_scaling=False)`, the
`ccs_retrofit_vom_adder=8.0` pin, then `apply_iso_scenario_defaults(cfg, "NEISO")` — and comparing
field-for-field against the committed `config.yaml`:

```
FIELD DIFFS committed -> pinned CLI                                0     (zero)
pinned+resolved cache key                           f04fd06348e1623d
committed recipe key                                f04fd06348e1623d     ← IDENTICAL
```

**The arm IS the scored recipe.** Under a correct registration it would realize the scored bundle's
own key; at this HEAD it realizes a different one for the §3.1 reason alone, and it writes to its own
`--out-dir`, so it can neither cache-hit nor clobber the stale bundle. §3.4's two pins are hereby
verified to do exactly what they were declared to do, before the solve rather than after.

### A.2 THE SCORER IS VALIDATED — it reproduces the standing verdict byte-for-byte

The control is far stronger than §3.5 assumed: `results/ff-t3-neiso-golden/bau-d60/` commits not only
the 25 evolution ledgers but **`full_horizon_summary.json` (the full 25-year trajectory),
`run_config.json`, `dof_ledger.json`, `forecast_attestation.json` and `forecast_verdict.json`**.

Re-running `forecast_verdict.py --tier t3` over those committed artifacts reproduces the committed
`forecast_verdict.json` **exactly — identical in every category, row, status and detail string, with
only `provenance` differing.** The re-score is therefore a *controlled swap*: the arm's summary and
run-config replace d60's, every carried input is held byte-identical, and any verdict movement is
attributable to the solve alone.

**Which also settles FC-6's scope, on evidence rather than convenience.** Reproduction required
`bau-d46`'s `fc6/paired_invariants.json` and `fc6/driver-battery-neiso-2026-09-03.json` — i.e. **the
standing d60 verdict already CARRIES its FC-6 from d46 and never measured it on d60's own solve**
(the same carry its own notes disclose for FC-5). This lane therefore **carries FC-6 identically**,
so the input is held fixed on both sides and FC-6 cannot move spuriously. **Consequence, stated
rather than buried: FC-6 is structurally incapable of moving in this re-score, so no FC-6 reading
here is evidence about D88** — and the pre-existing staleness (d60's and now the arm's FC-6 paired
CO2/build rows are d46's numbers) is reported, not absorbed. Re-measuring it is a separate lane's
work.

### A.3 A PREDICTION MIS-ANCHORING, CORRECTED AGAINST MYSELF BEFORE THE SOLVE

**P6's bracket is mis-anchored and I am recording that now rather than quietly re-basing it later.**
§5's P6 cites "model 9.5792 vs table 4.4883 (+113.4 %)". That pair is **`bau-d46`'s**, quoted from the
standing verdict's notes. **`bau-d60`'s own `co2@2040` is 8.559 Mt**, so the control gap this lane is
actually moving from is **+90.7 %**, not +113.4 % — and the declared bracket "[+80 %, +110 %]"
straddles the control, which would make it nearly unfalsifiable.

**P6 is therefore graded on DIRECTION ONLY, and strictly:** it HITS iff `co2@2040` **< 8.559 Mt**, and
MISSES otherwise. The bracket is withdrawn as unfalsifiable rather than retained and claimed as a hit.
No other prediction is touched.

### A.4 The control trajectory, recorded so the arm is differenced against a fixed record

From the committed `full_horizon_summary.json` (`cache_key f04fd06348e1623d`, `total_wall_s` 402.4,
`global_peak_rss_mb` 3454.6, 25/25 years). Anchors this lane will difference:

| year | reserve_margin | co2_mt | lw_price | thermal_mw |
|---|---|---|---|---|
| 2035 | 0.0404 | 8.912 | 69.35 | 20326.3 |
| 2038 | 0.0907 | 8.631 | 69.02 | 22137.8 |
| 2040 | 0.0706 | 8.559 | 70.25 | 21858.2 |
| 2048 | **0.0360** | 9.798 | 77.05 | 22107.9 |
| 2050 | **0.0533** | 10.196 | 80.62 | 22320.6 |

**One observation that cuts against my own P1, recorded before the solve.** The control's reserve
margin is a **sawtooth** — it alternates roughly 0.040–0.048 against 0.070–0.091 through 2042, and
2048 already sits at **0.0360, BELOW the 0.0375 band floor**, before rebounding to 0.0608 and 0.0533.
So the terminal RM that FC-2 row2 gates on is a **noisy single-year read** whose neighbours straddle
the floor. This makes P1 easier to hit for a reason that has nothing to do with D88, and it is a
weakness of the gate rather than a strength of my prediction. **If P1 hits, it will be reported with
this caveat attached, not banked as a clean call.**

### A.5 T-REPRO is folded into the arm at zero extra LP

§3.5 pre-registered T-REPRO as a separate 2026–2031 solve. It is instead read off the **first six
years of the arm itself**, which is the identical object: D88's own PRECOMMIT §3 verified that
`config.end_year` reaches only the year-loop bound and two warning-message builders in
`policy/carbon.py`, entering no price, no screen and no decision. Same test, one fewer solve, and no
second partial bundle to retain. The pass/fail branches of §3.5 are unchanged.

---

## ADDENDUM B — a foreseen FC-7 artifact, and its handling rule, fixed BEFORE the solve

**The trap.** `build_forecast_dof_ledger.py` enumerates **non-default** `ScenarioConfig` fields, which
is why d60's own ledger has 7 entries and carries no CCS row at all (Q42 had made
`ccs_retrofit_capex_co2_scaling` the default — the standing verdict's P20 records exactly this). The
two §3.4 pins were **defaults when d60 was solved** and are **non-default now**, so the arm's ledger
will list them; and `CURATED_IDENTIFICATIONS` has a row for `ccs_retrofit_capex_co2_scaling` but
**none** for `ccs_retrofit_fixed_cost_co2_scaling` or `ccs_retrofit_vom_adder`. They would therefore
land **UNIDENTIFIED**, which by the instrument's own contract keeps the `unattested` token and pushes
**FC-7 PASS → CAVEAT**.

**Why that would be a false reading.** The pins are **restorations of the scored run's own recipe**,
not new degrees of freedom. §A.1 measured the arm's resolved config as a **zero-field diff** against
d60's committed `config.yaml`: the arm has *exactly* the free parameters d60 had. What changed is the
*ledger's description* of an unchanged recipe, because the dataclass defaults moved underneath it.
An FC-7 movement here would be **this lane's instrumentation, not D88** — the precise contamination
this re-score exists to avoid.

**Pre-registered handling rule — fixed now so it cannot be chosen by the result:**

1. Generate the arm's ledger with the standard instrument and score FC-7 on it. **If it reads PASS,
   that is the reading, full stop.**
2. **If and only if** it reads other than PASS *solely* because the two restoration pins appear as
   non-default/UNIDENTIFIED, report **both**, neither hidden:
   * **(i) the as-generated verdict** — the primary, headline number; and
   * **(ii) a secondary reading with d60's own committed `dof_ledger.json` carried**, which is
     admissible on exactly the ground the FC-6 carry is (§A.2): the input is held byte-identical on
     both sides, and here it is additionally *correct*, since the recipe is field-identical.
3. **Any other FC-7 movement — an UNIDENTIFIED entry from any other field, a failed attestation
   assertion, a `run_config` or overlay-off row change — is REAL and is reported as a real FAIL.**
   The carve-out is exactly two named fields and nothing else.
4. The DOF-ledger instrument is **not edited** to make this go away. Adding curated identifications
   would change the ledger for every other run in the program, which is not this lane's to do.

**P9 is graded against clause 1, not clause 2.** §5's P9 predicted "PASS, 8–9 entries, all
IDENTIFIED". On the evidence above the *entry count* half looks right and the *all IDENTIFIED* half
looks wrong, and P9 will be scored a **MISS** if the as-generated ledger carries an UNIDENTIFIED
entry — recorded here, before the solve, rather than reinterpreted afterwards.
