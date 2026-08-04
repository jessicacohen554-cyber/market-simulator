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

### 1.2 A REQUEST-side key is not the key a run is cached under — the measurement that matters

> **⚠ CORRECTION, made in-session before any conclusion was carried forward.** The
> analysis in §1.2/§1.3 hashes the config `reference_config` **returns**. That is the
> **REQUEST**. The key a run is actually cached and recorded under is the **RESOLVED**
> key: `runner.run_scenario_iso` re-binds the ISO, applies `resolve_policy_bundle` and may
> apply per-ISO overrides before the solve, and `save_result` dumps *that* config. FFR-3D
> §5.2 states the distinction explicitly, and this session measured it: ERCOT's
> request-side key is **`b1bf77e3fcf7f7aa`** while its on-disk resolved key is
> **`a55b0e43fdc2f990`**.
>
> **regate §6.3's recorded keys are RESOLVED keys.** So comparing them against
> request-side hashes — which is what the table immediately below does — compares two
> different quantities, and its "NOT reproducible at any FFR-3A commit" conclusion is
> **RETRACTED**. It was measured on the wrong object.
>
> **What replaces it is a direct like-for-like comparison** — this session's resolved
> on-disk key against regate §6.3's recorded resolved key, per leg — reported in §2.
> ERCOT's is already in: recorded `ab1d074828bebabe` vs measured **`a55b0e43fdc2f990`**,
> so that key **did** move; the cause is not established by the request-side analysis and
> is not claimed here.
>
> The request-side analysis is **retained below, demoted to an instrument note**, because
> it still establishes something true and useful: *which config fields enter the hash at
> all*. Its D-3a / new-NYISO-field / CT_CHP conclusions in §1.3 are statements about the
> hashing rules and stand on their own.

Method (no LP): rebuild each leg's config with `reference_config` and hash it, at HEAD
and in a worktree pinned to each FFR-3A in-session commit. **Request-side hashes** —
see the correction above.

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

**What this table does and does not show, after the correction.** It shows that the
**request-side** hash of the golden-posture legs is stable across FFR-3A's whole commit
range and differs from the recorded values — which is now expected, because the recorded
values are resolved keys and these are not. It is **not** evidence that FFR-3A's records
are unanchored, and that claim is withdrawn.

One observation does survive intact and is worth keeping: **NYISO's plain-default
request-side key equals its recorded key exactly** (`2bd878d87848785c`), at FFR-3A's HEAD
and at current HEAD. For that leg request and resolution evidently coincide — consistent
with it being the one leg that passes no `capacity_market_clearing_by_iso` mapping and
takes no per-ISO posture override.

### 1.3 Which fields enter the hash at all (request-side; an instrument note)

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

All legs cold-solved post-epoch, 2026–2030, shipped posture per regate §4.3
(`--golden-posture` everywhere except NYISO, which takes the plain default so it
resolves curve-OFF). `curve` is the RESOLVED per-ISO gate.

| leg | yrs | resolved cache key | curve | determination | FC-1 | FC-2 | FC-7 | invariant FAIL | WARN |
|---|---|---|---|---|---|---|---|---|---|
| ERCOT | 5/5 | `a55b0e43fdc2f990` | OFF ✓ | **HOLD** | FAIL | **FAIL** | CAVEAT | I3, **I12** | I14 |
| CAISO | 5/5 | `e5822277b72184f6` | ON ✓ | **HOLD** | FAIL | **FAIL** | CAVEAT | I3, **I7**, **I12** | — |
| NYISO | 5/5 | `2bd878d87848785c` | OFF ✓ | **HOLD** | FAIL | CAVEAT | CAVEAT | I7 | I12 |
| NEISO | 5/5 | `9f2cc6ecd30704ca` | ON ✓ | **HOLD** | FAIL | CAVEAT | CAVEAT | I7 | I12 |
| *ERCOT **control*** | *5/5* | `e80c9b0c1a20c651` | *OFF* | ***HOLD*** | *FAIL* | *CAVEAT* | *CAVEAT* | *I3* | *I12, I14* |

*(PJM and MISO run solo after phase 1 — see §9 for whether they landed.)*

### 2.1 The D-1/D-2 adequacy collapse REPRODUCES, cold and post-epoch

Independently re-measured at a different HEAD, with the C.4(c) un-pin and D-3a landed,
and it matches FFR-3A **to the digit**:

| quantity | FFR-3A (regate §6.4) | **this session** | match |
|---|---|---|---|
| ERCOT reserve margin | 9.1 → 3.8 → 3.0 → −1.5 % | 14.8 → **9.1 → 3.8 → 3.0 → −1.5 %** | **exact** |
| ERCOT unserved (I3) | to 0.41 % of load | to **0.41 %** of load | **exact** |
| ERCOT `hours_ge_500` | 1,137 h/yr | **1,137** h/yr | **exact** |
| CAISO reserve margin | 1.8 %, −3.1 %, −0.3 %, … | **1.8, −3.1, −0.3**, 12.3, 15.3 % | **exact** |

**The paired ERCOT attribution reproduces at rubric level**, which is the stronger
evidence because it is the scorer's own category verdict moving under the control:

| | TREATMENT (D-1+D-2, shipped) | CONTROL (pre-decision) |
|---|---|---|
| **FC-2** | **FAIL** | **CAVEAT** |
| I12 reserve margin | **FAIL** — 4-yr decline to **−1.5 %** | **WARN** — 2030 only, **12.4 %** |
| reserve margin path | 14.8 / 9.1 / 3.8 / 3.0 / **−1.5** % | 14.8 / 14.1 / 14.2 / 14.7 / 12.4 % |
| `hours_ge_500` (max) | **1,137** | **63** |
| FC-2 row 6 sustained-VOLL | **FAIL** (>800 h/yr) | *does not fire* |

Both arms took distinct resolved keys (`a55b0e43fdc2f990` vs `e80c9b0c1a20c651`),
confirming they are genuinely different scenarios. **Nothing was tuned or unarmed in
response** (Addendum D.1: HOLD PROMOTION, FIND ROOT CAUSE).

### 2.2 ⚠ NEW — BLK-10 backstop sizing is measurable for the first time, and CAISO FAILs it

This is the evidence **D-2 was meant to re-open** and that **could not be scored at all**
before: FC-2 row 4 SKIPPED on every leg at FF-2D and FFR-3A because the trajectory
carried no per-channel split. FFR-3D `34c2f25` made the split emit; a second defect then
kept it unread (§2.3). With both closed, the numbers are:

| ISO | cumulative reserve-backstop / total additions | row 4 |
|---|---|---|
| **CAISO** | **65.5 %** | **FAIL — administrative over-build** (>30 %) |
| NYISO | 23.8 % | CAVEAT |
| NEISO | 11.7 % | CAVEAT |
| ERCOT | 0.0 % | PASS |
| ERCOT control | 0.0 % | PASS |

**CAISO builds roughly two-thirds of its capacity additions through the administrative
reliability backstop** — a channel the rubric's own pre-registered rationale calls "a
single-digit-percent residual in real markets" (`BACKSTOP_SHARE_PASS = 0.10`). That is
what drives CAISO's FC-2 to FAIL alongside its negative reserve margins, and it is a
structural finding about *how* the model closes CAISO's adequacy gap, not a band problem.
**It is reported, not fixed** (rules 1/14).

**A sharpening of FFR-3C's ERCOT attribution, worth stating.** ERCOT's backstop share is
**0.0 % in BOTH arms**. So ERCOT's collapse is **not** a backstop-sizing story at all —
it is entirely the retirement/entry asymmetry FFR-3C attributes it to (exit throughput
uncapped, entry throughput capped). The backstop finding is CAISO's and the downstate/
New-England ISOs', and rule 25 `[R-ISO-SCOPE]` forbids carrying any of it across.

### 2.3 The recorded-vs-measured key comparison (the like-for-like one)

Resolved on-disk key at this HEAD against regate §6.3's recorded resolved key:

| leg | recorded (§6.3) | measured here | moved? |
|---|---|---|---|
| **NYISO** (plain default) | `2bd878d87848785c` | **`2bd878d87848785c`** | **NO — exact** |
| ERCOT | `ab1d074828bebabe` | `a55b0e43fdc2f990` | yes |
| CAISO | `862d176d609252f9` | `e5822277b72184f6` | yes |
| NEISO | `bc01afd6e7866422` | `9f2cc6ecd30704ca` | yes |
| ERCOT control | `e9e5e1c911c6424c` | `e80c9b0c1a20c651` | yes |

**NYISO's key is unmoved and exact** — the one leg that passes no
`capacity_market_clearing_by_iso` mapping. Every leg that DOES pass that mapping moved,
and `83efe6c` (C.4(a) B1) is the change that altered it, dropping NYISO from the shipped
dict. That is consistent with the request-side analysis in §1.3 and with the observation
that request and resolution coincide precisely for the leg that takes no posture
override. **A cold re-solve was required for all of them regardless** (§1.1), so no work
was lost to the movement.

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

### 3.2b PRE-REGISTERED attribution — half the un-pin is structurally inert in all four legs

Recorded **before** the legs were scored, from the constants alone, so it is a
pre-registration and not a post-hoc reading.

`CORRELATED_OUTAGE_CURVE` (`constants.py:1747`) contains **`['ERCOT']` and nothing else**,
and its own header states the rule-25 reason: *"ERCOT-fitted; the table carries no generic
fallback — a curve fitted on one ISO's events never crosses an ISO boundary."* The
mechanism matrix already carries this as `correlated_forced_outage` cells `K.....` /
fc `KIIIII` — **inert in the five non-ERCOT ISOs**.

**All four T1-H curve legs are PJM / MISO / NEISO / NYISO. None is ERCOT.** Therefore
`correlated_forced_outage=True` — half of what C.4(c) un-pinned — is **structurally
inert in every one of them**: the flag flips, and no curve exists for it to apply.

**Consequence for the per-verdict attribution scope item 1 asks for.** In these four legs
an FC-3 movement can only come from:

| candidate | can it move these legs? |
|---|---|
| `correlated_forced_outage` (un-pin half 1) | **NO — structurally inert, no curve for these ISOs** |
| `entry_lookahead_reprice` (un-pin half 2) | yes |
| `retirement_rule` → `pipeline` (D-1) | yes |
| `entry_rate_limits` + `entry_commissioning_lag` (D-2) | yes |
| the cache epoch (cold post-epoch re-solve) | yes — and it is not a rule change |

So "moved because of the un-pin" can only ever mean the **`entry_lookahead_reprice`
half** in these four legs. That halves the un-pin's attributable surface before a single
leg is scored, and it means an ERCOT-only mechanism must never be credited with a PJM,
MISO, NEISO or NYISO movement (rule 25 `[R-ISO-SCOPE]`).

#### CONFIRMED AT RUNTIME — the model says so itself

The pre-registration above was derived from the constants. The solves then **confirmed it
empirically**, which upgrades it from inference to measurement. Each of the four T1-H legs
logs, once per solved year:

```
correlated forced-outage derate armed but no curve/weather coverage — no-op
```

| leg | occurrences (solve years 2021, 2023, 2024, 2025) |
|---|---|
| PJM | **4** |
| MISO | **4** |
| NEISO | **4** |
| NYISO | **4** |

Four legs × four solved years = **16/16 solve-years explicitly no-op**. The flag is armed
and the mechanism does nothing, exactly as predicted and now stated by the model rather
than by me. (The same line appears in the T1-X PJM leg's forward years.) This makes the
"not the `correlated_forced_outage` half" clause of every attribution below **airtight
rather than merely argued**.

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

### 3.4 FC-7 fails on EVERY T1-H leg by construction — the unfixed analogue of blocker 7

`run_capacity_hindcast.py` writes **`run_config.yaml`** at the bundle root. FC-7 row 1
requires **`run_config.json`**. So every T1-H bundle this runner produces FAILs FC-7
*"run_config.json absent"* for reasons having nothing to do with the run — exactly the
defect FFR-3D fixed in `run_full_horizon.py` (blocker 7, `34c2f25`) and **did not fix in
the hindcast runner**.

Consequences, both worth stating:

* **FC-7 does not differentiate anything at T1-H.** It is FAIL on every leg, so it
  carries no information about leg quality and must not be read as one.
* **It is deliberately NOT fixed here.** Authoring the artifact *after* seeing the score
  is what rubric §4 forbids, and it is precisely why FFR-3A left the T1-F case open for a
  successor rather than patching it mid-battery. Logged as blocker §8.5 for an
  instrument lane to fix **before** the next T1-H battery, the same sequencing that made
  FFR-3D's T1-F fix admissible.

### 3.5 ⚠ D-2's commissioning lag CENSORS the T1-H additions bands — they no longer measure what they used to

This is a methodological finding, and it changes how the additions half of FC-3 must be
read across the D-2 boundary.

T1-H solves `{2021, 2023, 2024, 2025}` and **scores `{2023, 2024, 2025}`**. D-2's
`entry_commissioning_lag` commissions entry at `decision_year + ENTRY_COD_LAG_YEARS (2)`.
So:

| decision year | COD | inside the scored window? |
|---|---|---|
| 2021 | 2023 | yes |
| 2023 | 2025 | yes |
| **2024** | **2026** | **NO** |
| **2025** | **2027** | **NO** |

**Half the solved decision years now commission outside the scored window by
construction.** In-window additions are therefore mechanically suppressed relative to any
pre-D-2 bundle, independently of whether the model's entry *decisions* got better or
worse. Measured in NEISO: `storage` additions 0.72 → **0.0 GW** and `gas_ct` 0.5 → **0.0
GW`, both flipping their bands adverse, while the model still decides entry — it just
decides it into 2026/2027.

**Consequence:** an additions band that moves across the D-2 boundary is **not**
attributable to entry skill without correcting for this censoring, and a
pre-D-2-vs-post-D-2 additions comparison is not like-for-like. FFR-3C recorded the same
mechanism as a caveat on *cumulative* T1-F reads (§3(d)); here it bites the T1-H
**scoring window** directly. Reported, not corrected — correcting it means either
scoring COD-shifted additions or lengthening the window, both of which are design
decisions, not this session's to take.

### 3.6 Refreshed FC-3 — NEISO

Determination **unchanged: FC-3 FAIL** (as at FF-2D). Band-level movement, old committed
bundle (`neiso-2021-2025-curve`, pre-epoch, both mechanisms pinned OFF) vs this session's
(post-epoch, shipped posture):

| metric | actual | OLD model / band | NEW model / band | direction |
|---|---|---|---|---|
| `retire.total_gw` | 0.951 | 9.325 FAIL | **8.221** FAIL | closer, still 8.6× actual |
| `retire.unit_recall_gt300` | — | **PASS** | **FAIL** | **adverse** |
| `retire.false_retire` | — | FAIL | FAIL | unchanged |
| `add.by_tech.wind` | 0.225 | 4.0 FAIL | **1.0** FAIL | much closer |
| `add.by_tech.solar` | 1.947 | 8.0 FAIL | **1.028** FAIL | much closer (now under) |
| `add.by_tech.gas_ct` | 0.163 | 0.5 FAIL | **0.0** FAIL | **adverse — censored (§3.5)** |
| `add.by_tech.storage` | 0.642 | 0.72 **PASS** | **0.0 FAIL** | **adverse — censored (§3.5)** |

**Attribution — un-pin, D-1/D-2, or neither?** Stated per the scope item, and stated
honestly:

* **NOT the `correlated_forced_outage` half of the un-pin.** Pre-registered in §3.2b and
  it holds: NEISO has no entry in `CORRELATED_OUTAGE_CURVE`, so that flag is structurally
  inert here. **Ruled out, not merely unlikely.**
* **The additions movement is consistent with D-2**, and its storage/gas_ct legs are at
  least partly the §3.5 censoring artifact rather than a skill change.
* **The retirement movement is consistent with D-1**, whose whole purpose is to change
  which units the screen retires.
* **But NONE of it is ATTRIBUTED**, because this session ran **no T1-H control arm** and
  the legs also cross the **cache epoch** — and FFR-2B measured that the epoch alone
  moved PJM's retirement total 18.157 → 29.373 GW with *no* rule or posture change. With
  three candidate causes and one measurement, the honest verdict is **refreshed, not
  attributed**. A paired T1-H control at explicit pre-decision defaults is the single
  measurement that would separate them.

### 3.7 Refreshed FC-3 — NYISO, and here D-1 IS attributed: it is PROVABLY INERT

Determination **unchanged: FC-3 FAIL**. But NYISO admits a real attribution that NEISO
does not, and it comes from the retirement side being **exactly unmoved**.

| metric | actual | OLD (`nyiso-2021-2025-fixed`) | NEW (shipped) | direction |
|---|---|---|---|---|
| `retire.total_gw` | 1.488 | 1.036 FAIL | **1.036** FAIL | **IDENTICAL** |
| `retire.unit_recall_gt300` | — | PASS | PASS | unchanged |
| `retire.false_retire` | — | PASS | PASS | unchanged |
| `add.by_tech.wind` | 0.890 | 4.0 FAIL | **0.951 PASS** | **improved to PASS** |
| `add.by_tech.solar` | 2.197 | 8.0 FAIL | **0.891** FAIL | much closer (now under) |
| `add.by_tech.gas_ct` | 0.072 | 0.0 FAIL | 0.5 FAIL | over |
| `add.by_tech.storage` | 0.184 | 0.0 FAIL | 0.0 FAIL | unchanged |

**The retirement total is identical to three decimals across the cache epoch, D-1, the
C.4(c) un-pin AND D-2.** The evolution ledgers say why:

| per-fuel model retirement | OLD | NEW |
|---|---|---|
| nuclear | 1.036 | **1.036** |
| biomass / gas_cc / gas_ct / oil | 0.0 | **0.0** |

and across all five ledger years the run books **exactly one retirement event**, in 2022,
with reason **`announced`**. **Zero economic retirements in any year, in either arm.**

**Attribution, and this one is real:**

* **D-1 is PROVABLY INERT in NYISO's T1-H window.** The economic-retirement screen never
  fires, so the rule that governs it cannot move anything. This is the same structural
  inertness FFR-3C established for MISO in T1-F — but derived independently from NYISO's
  own evidence, so it is rule-25 `[R-ISO-SCOPE]` clean and is **not** imported.
* **NYISO's FC-3 retirement bands are therefore NOT evidence about D-1.** They measure
  the announced-exit channel against actuals: 1.036 GW booked vs 1.488 GW actual, a −30 %
  miss that is entirely "the economic screen retires nothing in NYISO 2023–2025".
* **The additions movement is D-2 plus the §3.5 censoring**, with the
  `correlated_forced_outage` half of the un-pin ruled out structurally (§3.2b) — leaving
  `entry_lookahead_reprice` and the epoch as the only unseparated candidates on that half.

**A first PASS in the T1-H set.** `add.by_tech.wind` moves 4.0 → 0.951 GW against 0.890
actual — from a 4.5× over-build to inside the band. That is the only band in either
refreshed leg to reach PASS, and it is reported as measured, not claimed as skill: the
same §3.5 censoring that pushed NEISO's storage to zero also trims NYISO's wind, and this
session cannot separate "better entry decisions" from "entry deferred past the scoring
window" without the control arm named above.

### 3.8 Refreshed FC-3 — PJM, where D-1 fires hard and REPRODUCES FFR-3C's split

Determination **unchanged: FC-3 FAIL**. But PJM is the leg where the retirement screen
actually fires, and what it does is the D-1 signature — recomposing *which fuel* exits
while making the *level* worse.

| metric | actual | OLD (`pjm-2021-2025-curve-ff2c`) | NEW (shipped) | direction |
|---|---|---|---|---|
| `retire.total_gw` | 11.121 | 18.157 FAIL | **22.415** FAIL | **worse level** (2.0× actual) |
| `retire.unit_recall_gt300` | — | **FAIL** | **PASS** | **better membership** |
| `retire.false_retire` | — | FAIL | FAIL | unchanged |

Per-fuel model GW — a wholesale recomposition, not a rescaling:

| fuel | OLD | NEW |
|---|---|---|
| **coal** | 0.0 | **18.309** |
| **gas_st** | 10.358 | **0.0** |
| **gas_ct** | 3.693 | **0.0** |
| nuclear | 4.097 | 4.097 (announced — unmoved) |
| biomass | 0.009 | 0.009 |

**This is attributable to D-1, and the corroboration is external.** FFR-2B measured the
legacy→pipeline flip in PJM **against a paired control** and recorded *"PJM gas_st 10.358
→ 0.0 and gas_ct 11.379 → 0.0, coal 3.530 → 14.756, recall 9/17 → 13/17"*. This session's
independent, post-epoch, shipped-posture re-solve reproduces that signature — **`gas_st`
10.358 → 0.0 to the megawatt** — plus the recall band flipping FAIL → PASS. The
mechanism, the direction and the magnitude all match a result that *was* controlled, so
naming D-1 here is not a bare inference from one arm.

**⚠ It independently reproduces FFR-3C's MEMBERSHIP-vs-CALENDAR split** (§4 of that
memo), which is the finding the owner's decision rests on:

| FFR-3C term | its verdict | what PJM's refreshed FC-3 shows |
|---|---|---|
| *which* units retire | **REAL** economics; the corrected rule identifies them better | `unit_recall_gt300` **FAIL → PASS** |
| *when* they leave / how deep | **GRAIN ARTIFACT** | `retire.total_gw` **18.157 → 22.415** against 11.121 actual — the level gets **worse** |

So the same leg gets **more right about membership and more wrong about depth**, in one
measurement, exactly as FFR-3C's split predicts. **This is corroboration of the existing
attribution, not a new one, and it changes nothing about the owner's decision** — rule 1
`[R-STRUCT]`: a structurally better mechanism is not reverted because a level band moved
against it, and the depth residual is the chartered G-31 lane's (Addendum F.1), not
this session's to touch.

### 3.9 Refreshed FC-3 — MISO: **every retirement band now PASSES**

Determination **unchanged: FC-3 FAIL** — but *why* it fails has changed completely, and
this is the cleanest T1-H result in the set.

| metric | actual | OLD (`miso-2021-2025-curve-ff2c`) | NEW (shipped) | direction |
|---|---|---|---|---|
| `retire.total_gw` | 15.227 | 10.814 **FAIL** | **13.734 PASS** | **FLIPPED** |
| `retire.unit_recall_gt300` | — | **FAIL** | **PASS** | **FLIPPED** |
| `retire.false_retire` | — | **FAIL** | **PASS** | **FLIPPED** |

Per-fuel: **coal 1.387 → 12.95 GW**, **gas_st 8.643 → 0.0**, nuclear 0.768 and biomass
0.016 unmoved (announced). Same D-1 signature as PJM, and the same one FFR-2B measured in
MISO **against a paired control** (*"gas_st econ exits 12.920 → 0.0 GW and coal 1.497 →
11.932, recall 2/17 → 13/17, false-retire 12.920 → 0.997"*) — the fuel inversion the
legacy rule caused is gone.

**MISO's FC-3 now fails on the ADDITIONS half ALONE:**

```
band FAIL: add.by_tech.{wind, solar, gas_cc, gas_ct, storage}
           add.shares.{wind, solar, storage}
```

**Every failing band is an additions band, and additions are exactly what §3.5 shows
D-2's commissioning lag censors inside this scoring window.** So MISO's refreshed FC-3
reads: *the retirement half is fully passing under D-1, and the only thing still holding
FC-3 at FAIL is the half this session independently showed to be mechanically suppressed
by D-2.*

**The two signed decisions pull in opposite directions on FC-3**, and MISO is where that
is cleanest. Neither is tuned or unarmed here (Addendum D.1); the observation is routed
to the owner, and the additions-censoring question is an instrument/design decision
(§3.5), not a parameter.

### 3.10 T1-H summary — all four curve legs refreshed

| leg | det | FC-3 | FC-7 | retirement bands | additions | what moved it |
|---|---|---|---|---|---|---|
| **MISO** | HOLD | FAIL | FAIL* | **3/3 PASS** | all FAIL | D-1 (attributed, FFR-2B-corroborated); additions censored by D-2 |
| **PJM** | HOLD | FAIL | FAIL* | recall **FAIL→PASS**, level worse | FAIL | D-1 (attributed); reproduces FFR-3C's membership/calendar split |
| **NYISO** | HOLD | FAIL | FAIL* | **identical** (1.036 GW) | wind→**PASS** | **D-1 PROVABLY INERT** (zero economic exits) |
| **NEISO** | HOLD | FAIL | FAIL* | recall PASS→FAIL | FAIL | refreshed, **NOT attributed** (3 candidates, no control) |

\* FC-7 is FAIL on all four for the same instrument reason (§3.4) and differentiates
nothing.

**Every FC-3 verdict in `ff-t1-gate-2026-07.md` §4.1 is now REFRESHED** — post-epoch
**and** shipped-posture, clearing both stacked invalidations that table records. **No
determination flipped: all four were FC-3 FAIL and all four remain FC-3 FAIL.** What
changed is the *composition* of the failure — and in MISO's case it is now confined
entirely to the censored half.

**The FFR-3A confound is gone** (§3.1). But note what limits attribution in its place:
with `correlated_forced_outage` structurally inert in all four ISOs (§3.2b), the un-pin's
attributable surface is only `entry_lookahead_reprice`, and **no T1-H control arm was
run** — so each ISO's attribution rests on structural inertness (NYISO), external
corroboration from a controlled experiment (PJM, MISO via FFR-2B), or is **withheld**
(NEISO).

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

### 4.2 Measured results — ERCOT

Re-run at vintage 2023, window 2023–2027 (5 solve-years), all damper/un-pin flags omitted
so each inherits the shipped default. **Determination HOLD**; FC-4 **FAIL**.

**Rule-22 compliance is verified by the scorer, not asserted:** FC-4 row 1
*quarantine* → **PASS**, *"≥2026 refusal marker present and clean"*. The forward years
2026–2027 are solved as pure forecast years and no bench/actual is read for them.

| FC-4 row | verdict | |
|---|---|---|
| quarantine | **PASS** | ≥2026 refusal marker present and clean |
| dispatch skill | **FAIL** | see below |
| input-gap ratio | PASS | report-only |

#### ⚠ The price convergence FF-2D reported is GONE

| metric | FF-2D (`ercot-t1x`) | **now** | |
|---|---|---|---|
| price 2023 | 69.2 % | **68.7 %** | unchanged |
| price 2024 | 42.7 % | **41.2 %** | unchanged |
| **price 2025** | **8.6 % — PASS** | **22.5 % — FAIL** | **REGRESSED** |

FF-2D's headline for this leg was *"ERCOT converges 69 % → 9 % by 2025"*, and that
convergence — the cleanest positive dispatch-skill signal in the whole T1-X set — **no
longer holds**. 2023 and 2024 are essentially unmoved, so this is specifically the
terminal year losing its fit.

**Not attributed.** The crossover's scored years are hindcast years on realized inputs, but
its fleet is evolved across 2023 → 2025, so D-1's retirement recomposition (measured hard
in PJM and MISO, §3.8/§3.9) is a plausible route to a changed 2025 fleet and therefore a
changed 2025 price. It is only plausible: **no T1-X control arm was run**, and the leg also
crosses the cache epoch. Recorded as an open regression (§9 blocker), not a claim.

#### Family-volume rows are newly COVERED — not a regression

FF-2D reported these **uncovered**: *"the emitter computes only aggregate `fuelmix` …
neither of which maps to the rubric's fractional `gas_twh`/`coal_twh` family-volume bands —
so FC-4 scores price + CO2 only; the family-volume rows are uncovered and reported here,
never silently passed."* That L-VAL follow-up has since landed (`d12b4a8` folded the
adapter into `score_crossover.py`), and this run bands **11 rows with 1 uncovered**:

| newly banded | 2023 | 2024 | 2025 |
|---|---|---|---|
| `gas_twh` | 19.6 % FAIL | 10.0 % FAIL | *uncovered — preliminary EIA-923 vintage* |
| `coal_twh` | 35.0 % FAIL | 44.1 % FAIL | 37.2 % FAIL |

These are **new coverage, not new failures** — the same distinction as FC-2 row 4 (§7.2).
The one remaining `uncovered` row is declared with its reason (incomplete 2025 class
actuals would bias the band) rather than silently passed, which is the correct behaviour.

CO2 stays FAIL at 49.2 / 42.7 / 50.6 %, and FF-2D's caveat still applies: crossover CO2 is
reconstructed on the keeper's full-plant basis via bench intensities, so it is directional.
**Price remains the load-bearing input-gap measurement** — which is exactly why the 2025
regression above matters.

### 4.3 Measured results — PJM, and the asymmetry that matters

**Determination HOLD**; FC-4 **FAIL**; quarantine row **PASS**. But PJM is **essentially
unchanged from FF-2D**, which is the point:

| metric | FF-2D (`pjm-t1x`) | **now** | |
|---|---|---|---|
| price 2023, 2024 | in-band | **in-band** (not flagged) | unchanged |
| **price 2025** | **17.5 % CAVEAT** | **15.7 % CAVEAT** | **slightly better** |
| CO2 2023–2025 | 43–58 % FAIL | **45.1 / 40.4 / 54.2 % FAIL** | same range |
| `gas_twh` 2024 | *uncovered* | 6.7 % CAVEAT | newly covered |
| `coal_twh` 2023 / 2024 | *uncovered* | 13.0 % CAVEAT / 23.9 % FAIL | newly covered |

#### ⚠ The two crossover legs move in OPPOSITE directions

| leg | price 2025, FF-2D → now | direction |
|---|---|---|
| **ERCOT** | **8.6 % PASS → 22.5 % FAIL** | **regressed** |
| **PJM** | 17.5 % CAVEAT → **15.7 % CAVEAT** | flat / marginally better |

Both legs ran the same signed decisions, the same un-pin, the same cache epoch and the
same instrument. **Only ERCOT's terminal-year price skill regressed.**

That asymmetry is *consistent with* the D-1/D-2 story rather than with a generic
instrument or epoch effect — ERCOT is the energy-only ISO where D-1 has no capacity
revenue to offset the going-forward-cost screen, where FFR-3C attributes the collapse
against a control, and where this session's T1-F reserve margin runs to −1.5 % while PJM's
FC-2 is only CAVEAT. A pure epoch or scorer effect would be expected to move both.

**It remains NOT ATTRIBUTED.** Two legs is not a control, the ISOs differ in market design
as well as in exposure to D-1, and the ERCOT-only `correlated_forced_outage` curve is a
further ERCOT/PJM asymmetry (§3.2b) that this comparison does not eliminate. Recorded as
the strongest available *circumstantial* evidence on the T1-X half, and as a named open
question (§9).

---

## 5. FC-6 driver response — run BOUNDED, and the bound is measured, not asserted

### 5.1 What the full battery costs, from this session's own anchors

| anchor | measured here |
|---|---|
| ERCOT T1-F, cold, 5 solve-years | 10.0 min ⇒ **2.0 min / solve-year** |
| PJM T1-F, cold, 5 solve-years | 19.0 min ⇒ **3.8 min / solve-year**, and PJM must run **solo** (8.8 GB) |
| full driver battery | 9 ladders × 3–4 rungs ≈ **29 rungs**, each a full forward solve over the window |

| leg | rungs × solve-years × min | projected |
|---|---|---|
| ERCOT (2026–2030) | 29 × 5 × 2.0 | **≈ 4.8 h** |
| PJM (2026–2030) | 29 × 5 × 3.8 | **≈ 9.2 h**, cannot co-run |
| **specified ERCOT + PJM battery** | | **≈ 14 h serial** |

**FC-6 is `OPTIONAL` at t1f** (`forecast_verdict.CATEGORY_GATING`) and REQUIRED only at
t2/t3, and **no leg in this battery is promotable — every determination is HOLD.** So the
full battery gates nothing this session could have delivered, and spending 14 h on it
ahead of the scorecard would have been the wrong trade.

### 5.2 The bound, stated so it is never mistaken for the whole battery

| | |
|---|---|
| **ISO** | **ERCOT only** — cheapest per solve-year, and the only ISO where D-1 is attributed against a paired control (FFR-3C §5). Rule 25 `[R-ISO-SCOPE]` forbids reading any ERCOT verdict across. |
| **Window** | **2026–2027** (2 solve-years, not the battery's 5) |
| **Ladders run** | **T1.1** carbon `{0,25,50,100}` · **T1.3** gas `{0.5,1.0,1.5}×` |
| **Ladders OMITTED** | T1.2 adder/cap duality · T1.4 load · T1.5 IRA cliff · T1.6 RPS/ACP · T1.7 net-CONE · T1.8 tech cost · T1.9 storage-ELCC saturation — **and PJM entirely** |

**Why those two and not a truncated version of all nine.** T1.1 and T1.3 are the
pure-**dispatch** directional ladders — a 2-year window exercises them honestly. The
entry/exit-economics ladders (T1.5–T1.9) are **omitted rather than truncated**, because a
2-year window *cannot* exercise them honestly: D-2's `ENTRY_COD_LAG_YEARS = 2` means an
entry decided in 2026 commissions in **2028**, outside the window entirely — the same
censoring measured at §3.5. Running them short would produce directional verdicts on
mechanisms the window structurally prevents from acting, which is worse than not running
them.

**No silent caps.** Everything omitted is named above. FC-6 remains **SKIPPED** on every
T1-F leg's rubric verdict in §2, because a bounded ERCOT-only battery is not the
committed driver-battery artifact the scorer keys on and must not be presented as one.

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

## 7. Regression vs FF-2D — every moved metric with its causal commit

Diffed against the FF-2D rubric snapshot, preserved verbatim by this session under
`<iso>-t1f-ff2d` before the bare keys were refreshed (§6 of the merge tool's rationale).

**No determination moved. All six were HOLD at FF-2D; all six are HOLD now.** FC-1, FC-3,
FC-4, FC-5, FC-6 and FC-7 are unchanged in every ISO. **Every movement is inside FC-2**,
and it splits cleanly into three causes that must not be conflated:

### 7.1 GENUINE metric movement — the signed decisions

| ISO | row | FF-2D | now | causal commit |
|---|---|---|---|---|
| **ERCOT** | row1 reserve-margin | CAVEAT | **FAIL** | `24b1602` (D-1) + `3e33f15` (D-2) — **attributed against the paired control** (§2.1) |
| **ERCOT** | row6 sustained-VOLL | *did not fire* | **FAIL** (1,137 h/yr) | `24b1602` + `3e33f15` — control does not fire it (63 h/yr) |
| **CAISO** | row1 reserve-margin | CAVEAT | **FAIL** | `24b1602` + `3e33f15` — **observation, not attributed** (no CAISO control) |
| **PJM** | row1 reserve-margin | *PASS* | CAVEAT | I12 WARN appears; **not attributed** (no control) |
| **NEISO** | row1 reserve-margin | *PASS* | CAVEAT | I12 WARN appears; **not attributed** (no control) |
| MISO / NYISO | row1 | CAVEAT | CAVEAT | unchanged |

### 7.2 ⚠ NEWLY SCORABLE — not regressions, previously invisible

**FC-2 row 4 was SKIPPED on every leg** at FF-2D and FFR-3A (blocker 8: the trajectory
carried no `reserve_backstop` split). It is scorable for the first time here, so its
values are **new measurements, not movements**:

| ISO | row 4 now | causal commits |
|---|---|---|
| **CAISO** | **FAIL 65.5 %** | `34c2f25` (FFR-3D — emit the split) + `0830d134` (this session — actually read it) |
| NYISO | CAVEAT 23.8 % | same |
| PJM | CAVEAT 23.6 % | same |
| NEISO | CAVEAT 11.7 % | same |
| MISO | PASS 9.2 % | same |
| ERCOT (+control) | PASS 0.0 % | same |

Reading these as "FC-2 got worse" would be wrong: **the metric did not move, the
instrument started reporting it.** Without `0830d134` every one of them would have read a
false `PASS 0 %` (§2.2).

### 7.3 ⚠ A GENUINE IMPROVEMENT, and the first positive evidence for D-2

| ISO | row | FF-2D | now |
|---|---|---|---|
| **MISO** | row3 cobweb | **FAIL** — `cobweb (I13 WARN ⇒ row FAIL): gas_ct(3)` | **PASS** — `no cobweb (I13 PASS)` |

This is the FF-2C-induced MISO gas_ct cobweb the mechanism matrix records (*"MISO … induced
the I13 gas_ct cobweb → FC-2 FAIL, routed to BLK-10"*). **At this HEAD it is gone.**

`entry_commissioning_lag` is D-2's **structural anti-cobweb** — decide in year Y, commission
at Y+2, so decision and commissioning separate and the oscillation damps. FFR-2B could not
test it and said so: *"(c) The anti-cobweb claim is UNTESTED, not won — I13 PASSES in BOTH
arms, so this window contained no cobweb to damp."* **MISO's FF-2D leg did have one**, and
it is the one case in the program where the claim was testable at all.

**Stated at the right strength: this is CONSISTENT WITH the anti-cobweb claim, not an
attribution.** The FF-2D leg differs from this one in more than D-2 — cache epoch, the
FFR-2C net-CONE re-anchor, the C.4(c) un-pin and D-1 all moved too — and no paired control
was run. What is established is narrow and worth the owner's attention anyway: **the only
measured cobweb in the program has disappeared under the configuration D-2 armed**, which is
the first evidence pointing *for* D-2 in a battery otherwise dominated by adverse D-2
findings (§2.1 adequacy, §3.5 additions censoring).

### 7.4 FC-7 — against FFR-3A rather than FF-2D

FF-2D reads FC-7 CAVEAT, but only because it worked around the missing artifact with a
scoring-time helper (`scripts/_ff2d_emit_run_config.py`). Measured against **FFR-3A**,
which scored the producer as it actually was:

| | FFR-3A | now | causal commits |
|---|---|---|---|
| FC-7, every T1-F leg | **FAIL** (`run_config.json` absent by construction) | **CAVEAT** (only the DOF ledger remains) | `34c2f25` (FFR-3D) + `05690366` (this session — without which the emitter never ran) |

---

## 8. The per-ISO §2.1b gate scorecard

**This is the artifact the owner's gate-open conversation happens on.** Assembled by
`scripts/build_ffr3a2_scorecard.py` from committed artifacts only — it scores nothing
itself, every verdict is read from an artifact another instrument produced, and it
re-derives without a solve. Machine copy: `results/ffr3a2/scorecard/scorecard.json`.

`scored_at_sha` `def7cbf8` · `cache_epoch` 2026-08-03 · **holdout freeze ACTIVE**

The §2.1b gate opens per ISO on four criteria (plan §0/§2.1b): **(a)** completed backcast
calibration, **(b)** green T1 proof-of-concept gates, **(c)** measured worth-the-compute
evidence, **(d)** explicit per-campaign owner authorization.

| ISO | (a) backcast determination | marker | (b) t1f | t1h | t1x | (c) proj h | solo | **gate** |
|---|---|---|---|---|---|---|---|---|
| **PJM** | **CALIBRATED** (clean, 16/16) | `complete` | HOLD | HOLD | HOLD | 7.34 | **yes** | **CLOSED on (b)** |
| **NEISO** | CALIBRATED-WITH-CAVEATS | `complete` | HOLD | HOLD | — | 0.95 | no | **CLOSED on (b)** |
| **NYISO** | CALIBRATED-WITH-CAVEATS | `complete` | HOLD | HOLD | — | 1.09 | no | **CLOSED on (b)** |
| **CAISO** | CALIBRATED-WITH-CAVEATS | **none** | HOLD | — | — | 2.78 | no | **CLOSED on (a) + (b)** |
| **ERCOT** | **NOT-YET** | **none** | HOLD | — | HOLD | 2.00 | no | **CLOSED on (a) + (b)** |
| **MISO** | **NOT-YET** | **none** | HOLD | HOLD | — | 10.12 | **yes** | **CLOSED on (a) + (b)** |

### 8.1 The reading, PJM first

**No ISO clears the gate, and criterion (b) is what closes it for all six** — every T1-F,
T1-H and T1-X determination measured in this session is **HOLD**. That is unchanged from
FF-2D in kind, and this session did not move a single determination (§7).

* **PJM is the closest, and by a wide margin.** It is the only ISO with a **clean
  `CALIBRATED`** backcast (every criterion passing, 16/16, zero caveats) *and* a `complete`
  marker. Its T1-F blocker is **one invariant, marginal**: I7 short by **366 MW on a
  150,454 MW requirement — 0.24 %, in 2030 only**. Its FC-2 is CAVEAT, not FAIL, and its
  reserve margin never leaves the requirement-implied band except in that terminal year.
  If the owner opens a gate for any ISO on this evidence, PJM is the candidate — and the
  honest caveat is that its projected cost (**7.34 h, must run solo at 10.0 GB**) is the
  second-heaviest of the six.
* **NEISO and NYISO** also hold `complete` markers with caveated determinations, and are
  by far the **cheapest** (0.95 h and 1.09 h, both co-runnable). NEISO's T1-F blocker is
  likewise a single I7 miss (218 MW in 2028).
* **CAISO and MISO and ERCOT fail (a) as well as (b)** — none holds a `complete` marker,
  and ERCOT and MISO are `NOT-YET` on their own backcast determinations. For those three
  the forecast gate is not the binding constraint; the backcast is.
* **ERCOT and CAISO are the two ISOs whose T1-F FC-2 is FAIL** (not CAVEAT), on negative
  reserve margins — ERCOT to −1.5 %, CAISO to −3.1 % — and CAISO additionally fails FC-2
  row 4 at a **65.5 %** backstop share (§2.2).

### 8.2 Criterion (d) is NOT evaluated here

`final` is **empty**, deliberately, and no ISO carries a per-campaign authorization.
**(d) is the owner's decision and this session neither makes it nor recommends it.** The
scorecard reports (a)–(c) as measured and leaves (d) blank by construction — the
assembler emits the literal string *"NOT MEASURED HERE — an explicit, per-campaign owner
decision"* rather than a verdict.

### 8.3 What the readiness half says

FF-3E parts a/b/d are **GREEN for all six ISOs** (§6) — the input-resolution walk resolves
every forward input 2026–2050 with 0 hard fails, and the golden-posture config round-trips
with a stable cache key. **Part c is FAIL** (§6.4), and the registered
`ff-3e-readiness.json` therefore records **`green=False`**, with `gate_open=False` for
every ISO. Compute is still not the binding constraint; the T1 structural blockers are —
the same conclusion FF-2D reached, now with a resume-path defect added to it.

---

## 8. Open blockers

1. **A request-side `cache_key()` is not the key a run is recorded under, and nothing
   says so at the call site** (§1.2). `reference_config(...).cache_key()` returns
   `b1bf77e3fcf7f7aa` for ERCOT; the run lands at `a55b0e43fdc2f990`. The distinction is
   documented only inside `write_run_config`'s docstring (FFR-3D §5.2). Any successor who
   pre-computes a key to "check whether it moved" — as this session did, and as the
   dispatch packet's "re-run each leg at its recorded cache key" instruction invites —
   will compare the wrong object and reach a wrong conclusion. A `resolved_cache_key()`
   helper, or a loud note on `reference_config`, would close it.
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
