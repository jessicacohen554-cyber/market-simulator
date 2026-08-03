# FFR-3A-2 — the consolidated T1 battery: what closed, what moved, and what is still open

**Session.** FFR Wave 3, the battery-close lane
(`docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-3A, second half). FFR-3A ran the
T1-F half and stopped; FFR-3C attributed its headline finding; FFR-3D repaired the
instruments. This session runs what was left (regate §9) and regenerates the boards.

**Nothing is promoted. Nothing is tuned.** No `ScenarioConfig` default moved, no band
widened, no damper unarmed, no parameter adjusted in response to any score. Owner
decision Addendum D.1 — *HOLD PROMOTION, FIND ROOT CAUSE*, both mechanisms **stay
armed** — is honoured throughout.

**Base.** Branched off `origin/main` **`f0b8c025`**. The dispatch packet named
`01b6a6a`; main had advanced 9 merges by session start, and **four keepers had moved**
(see §0.1). Every citation below is taken at `f0b8c025`, not from the packet.

---

## 0. State re-verified at this HEAD (the packet was stale)

### 0.1 Keepers — four differ from the dispatch packet

| ISO | packet said | **actual at `f0b8c025`** | moved? |
|---|---|---|---|
| ERCOT | `2026-08-02-ercot150b-zonal-anchor` | `2026-08-02-ercot150b-zonal-anchor` | no |
| PJM | `2026-08-03-pjm-147b-chp-heat` | `2026-08-03-pjm-147b-chp-heat` | no |
| CAISO | `2026-08-03-caiso156-meter-screen-b` | `2026-08-03-caiso156-meter-screen-b` | no |
| **NYISO** | `2026-08-03-nyiso-117-nyc-rcpf` | **`2026-08-03-nyiso-118-seny-span`** | **yes (5th move)** |
| NEISO | `2026-08-03-neiso-caiso156-meter-screen` | `2026-08-03-neiso-caiso156-meter-screen` | no |
| MISO | `2026-08-03-miso-117b-ct-heat` | `2026-08-03-miso-117b-ct-heat` | no |

NYISO has now moved **five** times in three days. Markers unchanged: `complete` =
{NEISO, NYISO, PJM}, `final` **empty**. The **holdout spend freeze is ACTIVE** and was
neither spent nor worked around.

### 0.2 The environment was empty — both prerequisites, not one

The dispatch packet budgets `data/clean` (≈65 min). It does not mention that the
container ships **no Python environment at all**: `pandas`, `highspy`, `numpy`, `pyarrow`
— nothing. `scripts/regenerate_clean.py` fails instantly with `ModuleNotFoundError: No
module named 'pandas'` and reports *"50/50 datatype(s) failed"*, which reads exactly like
a data problem and is not one.

`uv` is present and `uv.lock` is the pinned source of truth, so **`uv sync`** is the fix
(~2 min). It also installs `tzdata`, so the documented
`ercot-wtx-congestion` / `ZoneInfoNotFoundError` blocker **does not arise on the uv
path** — that trap is specific to a bare `pip` environment.

> **Successor: run `uv sync` BEFORE `scripts/regenerate_clean.py`.** Budget
> ≈2 min (env) + ≈65 min (clean), not 65 alone.

---

## 1. Cache-key provenance — the load-bearing sub-task, and it did not go as briefed

The prompt directs: re-run each T1-F leg *at its recorded cache key* so the repaired
instrument emits `run_config.json`, and **EXPECT CACHE HITS**; a moved key is a finding.

Both halves of that expectation fail, for two independent reasons.

### 1.1 There is no cache to hit — the bundles are gitignored and died with the container

`results/ffr3a/` is matched by `.gitignore:531` and contains exactly one tracked file,
`README.md`. FFR-3A's six T1-F bundles were never committed (correctly — rule 15 routes
forecast legs to `frontend/data/forecast/`, not to tracked bundles). The container is
fresh. **So every leg is a cold solve regardless of its key**, and "expect cache hits"
cannot hold for any leg in a fresh container. This is a property of the lane's storage
design, not a defect.

### 1.2 The recorded golden-posture keys are NOT reproducible — at ANY FFR-3A commit

Method (no LP): rebuild each leg's config with `reference_config` and hash it, at HEAD
and in a worktree pinned to each FFR-3A in-session commit.

> **Instrument note for successors.** `ScenarioConfig.cache_key()` is path-invariant
> **only when `DATA_ROOT == REPO_ROOT`**. Setting `MARKET_SIM_DATA_ROOT` adds a second
> `<data_root>` sentinel to `_cache_key_path_roots()` and changes the payload, so a
> worktree probe run with that variable set produces keys that match nothing. Every
> probe below ran with **no** data-root override.

| leg | recorded (regate §6.3) | at `05a367e` (FFR-3A HEAD) | at `89d0e54` | at `f5da701` | reproduced? |
|---|---|---|---|---|---|
| NEISO golden | `bc01afd6e7866422` | `9a0c3e26c979b4be` | same | same | **NO** |
| ERCOT golden | `ab1d074828bebabe` | `a512ab1a06674d75` | same | same | **NO** |
| CAISO golden | `862d176d609252f9` | `e4a7995386361c18` | same | same | **NO** |
| **NYISO plain** | `2bd878d87848785c` | `2bd878d87848785c` | — | — | **YES, exact** |

All four posture variants were swept (`golden|plain` × `cmc=True|False`); none matches
for the golden legs. The probe is demonstrably live rather than inert: at `3e33f155`
(before the `f5da701` propagation fix) ERCOT-golden hashes `fbec2d086b46ece0`, which is
exactly the ERCOT **control** key at `05a367e` — the pre-fix mirrored literals *were* the
control config, and the probe sees that.

**Finding.** The five golden-posture T1-F cache keys recorded in regate §6.3 cannot be
re-derived from the repository at any commit in FFR-3A's session. The one plain-default
leg reproduces exactly, at FFR-3A's HEAD *and* at current HEAD — so the harness, the
config path and the hashing are sound; it is those five recorded values specifically
that are unanchored. **They should not be used as provenance anchors.** Open blocker
(§8.1).

### 1.3 HEAD vs FFR-3A HEAD: the golden keys move, and the cause is `83efe6c` ALONE

Substituting the pre-`83efe6c` five-ISO `GOLDEN_CMC_BY_ISO`
(`{PJM,MISO,NYISO,NEISO,CAISO}`, all `True`) into the **current** config reproduces
`05a367e`'s keys **exactly**:

| leg | HEAD | HEAD w/ pre-`83efe6c` dict | `05a367e` | identical? |
|---|---|---|---|---|
| NEISO | `d75885a2a7eaa49e` | `9a0c3e26c979b4be` | `9a0c3e26c979b4be` | **yes** |
| ERCOT | `b1bf77e3fcf7f7aa` | `a512ab1a06674d75` | `a512ab1a06674d75` | **yes** |
| CAISO | `22741d7713d5d541` | `e4a7995386361c18` | `e4a7995386361c18` | **yes** |
| NYISO (plain) | `2bd878d87848785c` | n/a — passes no dict | `2bd878d87848785c` | **unmoved** |

So the **only** key-moving change in `05a367e..HEAD` is
`capacity_market_clearing_by_iso`, i.e. **`83efe6c` (C.4(a) B1)**, which dropped NYISO
from the shipped mapping. Every other change in that range is **key-neutral**, which
independently confirms FFR-3D's byte-stability claims:

| change | commit | effect on key | why |
|---|---|---|---|
| D-3a `net_cone_forward_escalation` `hold_last`→`reindex_gross` | `e6f0cdb` | **neutral** | cache-key-optional, at default on both sides ⇒ dropped from the hash |
| new `nyiso_nyc_rcpf_step_curve` (default `False`) | `69f1aa07`/`fcdcac02` | **neutral** | registered optional, at default ⇒ dropped |
| CT_CHP override triple **deleted** | `a0fc302c` | **neutral** | all three registered in `_CACHE_KEY_RETIRED_FIELDS` at `None` and re-inserted before hashing |

A caveat worth stating precisely: FFR-3D §3 says *"passing the shipped mapping
explicitly is value-identical to inheriting it, so no cache key moves."* That is true
against **inheriting the default** and false against **the previous golden dict** — which
is the comparison a T1-F successor actually makes. Both statements can hold at once; the
one that matters for leg provenance is the second.

### 1.4 Nothing was hand-authored

No `run_config.json` was written into any existing bundle. The legs are re-solved and
their **new** keys recorded (§2). Authoring the artifact after seeing the score is what
rubric §4 forbids and is exactly why FFR-3A left this open.

---

## 2. T1-F re-run — results

*(pending; filled from `results/ffr3a2/t1f/*/full_horizon_summary.json`)*

---

## 3. T1-H re-solve — the four curve legs

### 3.1 The FFR-3A confound is GONE — stated explicitly

Regate §6.2 recorded a standing confound: `run_capacity_hindcast.py` pinned
`correlated_forced_outage=False` and `entry_lookahead_reprice=False` while production
ships **both `True`**, so any T1-H leg inherited a posture the forecast does not run.
Owner decision **C.4(c)** signed *UN-PIN — MATCH PRODUCTION* and FFR-3D executed it in
**`36ef1a1`**: both fields joined the `None`-sentinel dict (omit ⇒ inherit the shipped
default), and the run meta now reads the **solved** config rather than `args`.

**The confound no longer applies to any leg in this session.** Every un-pinned and
damper flag is *omitted* from the invocations in §3.3, so each inherits the shipped
default. Verified in the emitted meta, not assumed.

### 3.2 Why these RE-SOLVE rather than re-score

All four committed bundles carry the superseded posture on **five** solve-affecting
fields. Field-level diff of each `meta.json` against shipped `ScenarioConfig()`:

| field | bundle value | shipped | causal commit |
|---|---|---|---|
| `retirement_rule` | `legacy` | `pipeline` | `24b1602` (D-1) |
| `entry_rate_limits` | `False` | `True` | `3e33f15` (D-2) |
| `entry_commissioning_lag` | `False` | `True` | `3e33f15` (D-2) |
| `correlated_forced_outage` | `False` | `True` | `36ef1a1` (C.4(c)) |
| `entry_lookahead_reprice` | `False` | `True` | `36ef1a1` (C.4(c)) |

Identical for all four legs (`pjm-2021-2025-curve-ff2c`, `miso-2021-2025-curve-ff2c`,
`neiso-2021-2025-curve`, `nyiso-2021-2025-fixed`). A re-score cannot reach any of it.

### 3.3 Rule-22 legality of the 2021–2025 window — checked, not assumed

The window spans out-of-training years while the **holdout freeze is ACTIVE**, so it was
verified against the code rather than the prose. `scripts/lib/holdout_policy.py`
carries an explicit, enumerated capacity-hindcast carve-out:

- `HINDCAST_SEED_YEARS = {2021}` — solvable, **never scored**.
- `HINDCAST_BRIDGE_YEARS = {2022, 2026}` — evolved across, **never solved, data never read**.
- `HINDCAST_SOLVE_YEARS = CALIBRATION_YEARS ∪ {2021}` = `{2021, 2023, 2024, 2025}` — **4
  solve-years**, under the ≤5 cap.
- Scoring is bounded to 2023–2025 on both sides (`score_capacity_hindcast`,
  `score_crossover`'s ≥2026 refusal and its FH-1 symmetric <2023 lower bound).

`run_capacity_hindcast._validate_window` fail-closed enforces this, and the runner reads
the freeze file at launch and prints an explicit governance line. **No marker is spent,
no out-of-training year is scored, and the freeze is not implicated.**

### 3.4 Measured results

*(pending)*

---

## 4. T1-X crossover fold

### 4.1 The test applied, per leg

**Test.** A committed leg folds as-is iff its `meta.json` agrees with shipped
`ScenarioConfig()` on every field that can move dispatch. Otherwise it re-runs.

| leg | fields disagreeing with shipped | verdict |
|---|---|---|
| `ercot-2023-2027-crossover-ffr2a` | all five from §3.2 | **RE-RUN** |
| `pjm-2023-2027-crossover-ffr2a` | all five from §3.2 | **RE-RUN** |
| `miso-2023-2027-crossover-ffr2a` | all five from §3.2 | **RE-RUN** |

Two of the five (`correlated_forced_outage`, `entry_lookahead_reprice`) move dispatch in
**every** year; three (D-1/D-2) move capacity evolution in the forward years 2026–2027.
**No leg folds as-is.**

### 4.2 Measured results

*(pending)*

---

## 5. FC-6 driver response

*(pending)*

---

## 6. FF-3E readiness battery — RE-RUN AT THE CURRENT POSTURE

Parts **a**, **b** and **d** carry no LP; part **c** is a single T0 NEISO 2026–2028
solve. Artifacts: `results/ffr3a2/ff3e/ff3e_readiness_bundle.json`.

### 6.1 Part a — input-resolution walk (2026–2050, golden posture): **GREEN**

**0 hard fails** across all six ISOs, resolving every exogenous forward input for every
year 2026–2050. The walk reports 21 `[plateau]` notes (held-flat horizon tails on
`demand_growth_rate`, `datacenter_block_mw`, `rps_target`, `capacity_price_firm`) — these
are *descriptive*, not failures, and are the expected shape of a held-flat forward input.

One warning, expected and correct: `confirmed-retirements` has no NYISO clean partition.
NYISO is a **researched zero**; with the registry present for the other five the loader
degrades to a warning rather than refusing (regate §6.1).

### 6.2 Part b — config completeness: **GREEN, all six**

`ERCOT · CAISO · PJM · MISO · NYISO · NEISO` — 0 failed checks each. The golden-posture
`ScenarioConfig` round-trips through `run_config`/`config.yaml` with a stable
`cache_key`, and every §2.1a decision is reflected. **This is the first time the battery
has been run since `83efe6c` made NYISO resolve curve-OFF**, and the posture-parity check
(which FFR-3D rewrote to assert against the shipped field rather than against itself)
passes.

### 6.3 Part d — wall/RSS projection at the current posture

Refreshed from measured per-year anchors:

| ISO | lower h | projected h | late min/yr | peak GB | must run solo |
|---|---|---|---|---|---|
| ERCOT | 1.00 | 2.00 | 7.2 | 4.6 | no |
| CAISO | 1.39 | 2.78 | 10.0 | 5.5 | no |
| NYISO | 0.62 | 1.09 | 3.8 | 4.2 | no |
| NEISO | 0.54 | 0.95 | 3.2 | 4.3 | no |
| **PJM** | 1.63 | **7.34** | 31.3 | **10.0** | **yes** |
| **MISO** | 2.25 | **10.12** | 43.2 | **10.5** | **yes** |

Total serial wall under the rule-12 co-run plan: **21.33 h**. A 10-hour budget buys
**one** full-horizon golden ISO among {CAISO, ERCOT, NEISO, NYISO, PJM}; MISO alone
exceeds 10 h at the super-linear projection. Cheapest is NEISO at ~0.95 h.

### 6.4 Part c — kill-resume drill: **FAIL** (was GREEN at FF-2D)

```
killed_mid_horizon=True  cache_key_match=True  cached_loaded=True
result_identical=False  ->  FAIL
```

NEISO 2026–2028, killed after 2027, resumed from the per-year cache. The failure is
**narrow and precisely located**:

| year | resumed from cache | equal | dispatch_sum | price_sum | dispatch_hash | price_hash |
|---|---|---|---|---|---|---|
| 2026 | yes | **yes** | 110,209,668.869 | 2,252,019.757 | identical | identical |
| 2027 | yes | **yes** | 111,813,229.113 | 2,333,288.622 | identical | identical |
| **2028** | **no (freshly solved)** | **NO** | **113,465,187.662 — identical** | **2,554,741.327 — identical** | `07da96b1…` vs `187752af…` | `146f329e…` vs `75009894…` |

So the two cached years replay byte-exactly, and the **first freshly-solved year after
the resume** produces **identical aggregates to the last decimal** — total dispatch,
total price — with **different byte hashes**, and **identical evolution counts**
(`n_retire=0`, `n_thermal_add=1`, `n_renew_add=0`, `n_storage_add=0`).

**What this is not.** It is not a magnitude error and not an evolution-path divergence:
every scalar the trajectory and the invariants read is equal. The objective is the same.

**Two candidate mechanisms, NOT adjudicated here:**

1. **Array ordering.** The resumed run reconstructs fleet/zone arrays in a different
   order than the in-process control, making both vectors permutations of the control's.
   This explains identical sums, differing byte hashes, and identical counts in one step,
   and it explains why the *price* vector moves too (a zone re-order permutes prices).
2. **Alternate optima.** The resumed solve lands on a different vertex of the optimal
   face — identical objective, different per-element primal *and* degenerate dual.

**Cross-year warm start is ruled OUT as the cause**: `MARKET_SIM_WARMSTART_XYEAR`
defaults **off** (`docs/cross-year-warmstart.md`), so no basis is carried across years in
either arm.

**The discriminating test, for whoever takes this** (one drill re-run, no new solve
logic): have `_bundle_signature` additionally record `_arr_hash(np.sort(disp))` and
`_arr_hash(np.sort(price))`. If the **sorted** hashes match while the unsorted ones
differ, it is mechanism 1 (ordering) and the fix is in the cache-reload path; if the
sorted hashes also differ, it is mechanism 2 (alternate optima) and the question becomes
whether the resume path should pin a deterministic basis.

**Why this matters for §2.1b.** FF-3E part c exists precisely so a "wasted 10 hours"
plumbing bug dies at minutes of cost, and the FF-2D board records it GREEN for all six
ISOs. At this HEAD it is **FAIL for the drill's own ISO**, which means **a resumed
full-horizon run is not bit-reproducible against an uninterrupted one**. For a T2/T3
campaign — where resume is not optional at 7–10 h per ISO — that is a live provenance
risk against the "reproducible from `run_config.json`" requirement. It is reported, not
fixed (rules 1/14), and it is an **open blocker** (§8.3).

**Attribution is NOT claimed.** No commit is named. FF-2D's GREEN and this FAIL are
different sessions on different HEADs; establishing which change moved it needs a bisect
this session did not run.

---

## 7. The per-ISO §2.1b gate scorecard

*(pending)*

---

## 8. Open blockers

1. **The five recorded golden-posture T1-F cache keys are unanchored** (§1.2) — not
   reproducible at any FFR-3A commit under any posture variant, while the one
   plain-default leg reproduces exactly. Cause not established here. Until it is, regate
   §6.3's keys are not provenance anchors.
2. **`uv sync` is an undocumented hard prerequisite** (§0.2) — the container ships no
   Python environment, and the resulting failure mode reads as a `data/clean` failure
   (*"50/50 datatype(s) failed"*), which sends a successor to debug the wrong thing.
3. **FF-3E part c (kill-resume) is FAIL at this HEAD** (§6.4) — the first freshly-solved
   year after a resume has identical aggregates and identical evolution counts but
   different byte hashes on both dispatch and price. FF-2D records this GREEN for all six
   ISOs. A resumed full-horizon run is therefore not bit-reproducible against an
   uninterrupted one, which is a live provenance risk for any T2/T3 campaign (where
   resume is not optional at 7–10 h/ISO). The discriminating test is named in §6.4;
   attribution to a commit is not established here.
4. **`results/ffr3a/` is gitignored, so FFR-3A's T1-F bundles no longer exist** (§1.1).
   Any successor instructed to "replay a recorded key" in a fresh container will cold-
   solve instead. This is by design (rule 15) but is not stated anywhere a dispatching
   session reads, and it silently invalidates a "expect cache hits" budget.

*(further blockers pending — solve lanes still running)*

---

## 9. What this session did NOT measure

*(pending)*

---

## 10. Standing disclosure list

Carried verbatim from `docs/forecast-readiness-peer-review-2026-07.md` §4 (the single
wording authority):

> This forecast is produced by a chronological full-8760 LP dispatch model with a
> one-pass annual capacity-evolution loop. It does not include: MIP unit commitment;
> intertemporal capacity optimization or within-year entry/exit convergence; inter-hour
> ramp constraints; intra-ISO hurdle rates; demand-responsive fuel pricing. Unless
> produced by the weather ensemble, results are conditional on a single pinned weather
> year (stated in the run config). Uncertainty bands are dispatch-conditional: the
> fleet-path (capacity-expansion) component of structural error is unmeasured and
> excluded. Deterministic scenario cases are a range, not a probability distribution.
