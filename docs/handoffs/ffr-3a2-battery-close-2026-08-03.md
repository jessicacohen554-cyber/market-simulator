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
