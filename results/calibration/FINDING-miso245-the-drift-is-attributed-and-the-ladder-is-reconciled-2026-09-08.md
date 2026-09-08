# FINDING miso-245 — **THE DRIFT IS ATTRIBUTED (`M` = 1) AND THE LADDER IS RECONCILED TO ITS OWN FROZEN DERIVE.** The attribution is measured at **LOW POWER** and I say so; the citation is re-worded to rest on what actually carries it

> **STATUS OF THIS DOCUMENT.** §§0–6 are final. §7 (the 2024 screen), §8 (the full span) and §9
> (governance / the promotion question) are written when their numbers exist; **no number below was
> written before its measurement, and no bar was moved after one.**

**Keeper at session start: `2026-09-07-miso-243-spp-pairing`** (bundle
`results/calibration/miso243_sppair_K`), DETERMINATION **CALIBRATED**, C3c the single ledgered
non-downgrading caveat, DOF ledger **41/2**. Rule 22 `[R-HOLDOUT]`: **2023–2025 only**; MISO holds no
`complete` marker and **no out-of-training year was solved, scored or registered.**

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** — miso-244 §7.1's named successor,
handed forward with its hypothesis, its decision rule and its three integer coordinates fixed, and
un-run because miso-244's own §2.4 pre-commitment (a drafting defect it recorded against interest)
forbade it.

Pre-registration: `PREREG-miso245-attribute-the-incumbent-ladder-drift-2026-09-08.md`, pushed with its
probe and **before either ran** (`65dd8164`). Two addenda, each pushed **before the numbers it
governs**: `ADDENDUM-miso245-the-test-passed-with-low-power-and-one-more-leg-can-still-kill-it-2026-09-08.md`
(`8b30c02b`) and `ADDENDUM-miso245-the-four-screen-gates-2026-09-08.md` (`c9134a43`). Probes:
`_miso245_ladder_drift_attribution_phase0.py` (`65dd8164`), `_miso245_gclamp_n.py` (`ca29f1b5`),
`_miso245_screen_gates.py` (`19f9a4d4`) — **each pushed before it ran.**

**Basis.** The ladder's coupling anchor is the measured Indiana-hub **DA**
(`actual_lmp_hourly_MISO.parquet` `da`, stored **float32**); row sets are the derive's own per-seam
`dropna`. The model basis, where it appears, is the keeper's committed **P1** bus price, and the South
bands are hosted on **`MISO_external_South`** (`miso_south_seam_split` armed on the keeper). They are
never interchanged, and miso-232's measured decile column (+1,303 / +1,384 / +948) is **not** restated
as reproduced by anything here.

---

## 0. STATED FIRST, AGAINST INTEREST

### 0a. **MY PRE-REGISTERED TEST PASSED, AND IT HAS LOW DISCRIMINATING POWER. THE STATISTIC THAT SHOWS THAT IS ONE I DECLARED DESCRIPTIVE-ONLY BEFORE RUNNING IT**

The verdict is `A-CONFIRMED` on `M` = 1 (§2). **And R-2 says the test nearly cannot fail.** The flip
distance `f_j` — the minimal count nudge that changes an entry's rounded cent — measured across all
**192** entries reads, over the **189 that did NOT drift**:

| | p05 | p25 | **p50** | p75 | p95 | `min f` over the 189 |
|---|---:|---:|---:|---:|---:|---:|
| `f` (hours) | 1 | 1 | **1** | 1 | 2 | **1** |

**The median non-drifting entry is also exactly one hour from a different cent**, and the three
drifted entries rank **4 / 39 / 91** of 192 — `separated: false`. One hour of duration count moves the
quantile position by `8759/8760 ≈ 0.9999` order statistics, and adjacent DA order statistics in this
price region are typically a cent or more apart, so **"reachable at ±1 hour" is closer to a property
of the estimator's sensitivity than of the drift.**

**The verdict stands as `A-CONFIRMED`** because that is the rule fixed before the number existed, and
because PREREG §2.4 pre-committed that R-2 "cannot move the verdict in either direction" — honoured
here in the direction that costs me. **What changes is what the verdict is claimed to prove**, and §1
re-words the citation rather than banking a result the instrument does not support.

### 0b. **A POST-HOC READING OF THE SAME STATISTIC FAVOURS ME. IT IS LABELLED POST-HOC AND USED FOR NOTHING**

Read the other way, the same distribution corroborates a *small* perturbation: if most of the 192
entries sit one hour from flipping, a drift of many hours would have flipped far more than **3**.
**Not pre-registered** — PREREG §2.4 declared R-2's reading as "whether the three drifted entries are
also the most rounding-fragile at HEAD", and the answer to *that* question is **NO** (ranks 4/39/91,
not separated). **The arithmetic showing it moves nothing:** the verdict is `A-CONFIRMED` with or
without it, R-2 is barred from moving it either way, and **no disposition in this document is
conditioned on it.** It is recorded because suppressing a reading that favours my own direction would
be as dishonest as suppressing one that does not.

### 0c. **MY PREREG'S R-4 ASKED THE WRONG QUESTION, AND I ADDED THE RIGHT ONE AS A LEG THAT COULD ONLY KILL**

R-4 asked whether the no-wash clamp binds *anywhere* under perturbation. It does
(`clamp_binds_anywhere_in_any_scan: true`) — unsurprising, since the scan sweeps the count over its
whole feasible range. **The question that mattered was narrower and I had not gated it:** if a
reaching value were the **clamp** rather than the quantile, `m_j` would measure a mechanism miso-244
already **REFUTED** as the cause. `G-CLAMP-N` was declared in a pushed addendum **before its number
existed**, written so it could only invalidate — and it passes (§4).

### 0d. **THE CACHE KEY DOES NOT SEE THIS RE-DERIVE.** Measured, not assumed, and handed forward as a defect in another lane's scope boundary

`surface_stamp("MISO", keeper_config)` is **byte-identical before and after** the reconciliation —
`8ee657ee4c7c49b0`, rows 208, `moved: {}`, `epochs: []` — because
`market_sim.model.interchange.spec` is **explicitly outside** the capx-D79 solve-surface fingerprint's
phase 1 (`config/solve_surface.py` docstring §2.3: it imports `data.fleet`, "routed to a later card").
So `cache_key()` is unchanged (`f130587822fbf565`) and **a populated `results/MISO/<key>/` cache would
serve a PRE-reconciliation solve to a POST-reconciliation config.**

**Verified for this session rather than assumed: `results/MISO/` does not exist in this container, so
the arm genuinely solved.** The hazard is general, it is not MISO's to fix, and it is handed forward
in §9 as a concrete cost for a known, deliberate scope gap.

---

## 1. **THE CITATION, RE-WORDED BEFORE THE COMMIT EXISTED — because §0a means `M` cannot carry it alone**

PREREG §4 said the re-derive "cites this session's attribution measurement as the data change rule 23
requires." Given §0a that over-claims, so addendum 1 §1 corrected it **before the commit was made**
and in the direction that asks LESS of my own result:

> **What carries the citation** is that the estimator is **frozen and unchanged** — `G-RAW` reads
> `max_abs_delta` **0.0** across all 192 entries at HEAD, and miso-244 §3 eliminated the whole
> `h = q·(n−1)` estimator family arithmetically — while the frozen estimator's output **on the source
> data as it stands at HEAD** differs from the committed table at exactly three entries. **A frozen
> formula whose output has moved has had its input move.** That inference is complete without `M`.
>
> **What `M` = 1 adds is a BOUND on the magnitude:** one hour of duration count at each affected
> depth, `1.14e-4` of the year, with the sign quantile monotonicity requires at every entry. It is
> corroborative, measured at low power, and reported as such.
>
> **What is still NOT identified, stated rather than papered over:** *which* hours of which source
> series differ, and on what date the vintage changed. P-1's provenance reading (§6) is a read of the
> record with no decision rule attached and cannot supply it, and the 2026-08-16 history rewrite makes
> sha archaeology unreliable by CLAUDE.md's own statement.

**Zero free parameters.** Reconciling three committed quantile values to the frozen estimator's own
output adds no degree of freedom; the DOF ledger stays **41/2**. **No residual, no criterion and no
band comparison enters the decision in either direction** (rule 1 `[R-STRUCT]`).

## 2. THE INSTRUMENT PASSES EVERYTHING FIRST, INCLUDING THE TWO LEGS THAT COULD HAVE ENDED THE SESSION

`FAILED_LEGS: []`. Every reference value is a **literal in the probe**, so each leg adjudicates even
if the predecessor's artifact is missing.

| leg | what it asserts, in the predecessor's own metric | bar | **measured** |
|---|---|---|---:|
| **G-RAW** | `round(raw, 2) == derive()` for all 192 entries | exact | **0.0** |
| **G-QUANT** *(mine, falsifiable)* | the hand-vectorised linear quantile reproduces `np.quantile` at `Δ=0`, 192 entries | ≤ 1e-12 | **0.0** |
| **G-COUNT** *(mine, falsifiable)* | every duration share × `n` is an integer, **and** the three counts are **5,415 / 3,259 / 3,044** | ≤ 1e-6; counts exact | **1e-12**; exact |
| **G-REPRO** | miso-244's published D-1′ record (`n`, `q`, `lo_index`, `frac`, `x_lo`, `x_hi`, `value`) | ≤ 1e-9 each | **PASS** |
| **G-LOC** | exactly **3** mismatches, at exactly the published coordinates and values | exact | **PASS** |
| **G-DIR** *(instrument, not evidence)* | the reaching perturbation carries the sign monotonicity requires | exact | **+1 / −1 / +1** |

**G-QUANT and G-COUNT each had the power to end the session**: the whole statistic is computed on a
hand-vectorised quantile evaluated at a reconstructed integer count, and if either were not the
estimator's own object, `M` would mean nothing.

## 3. **THE VERDICT: `A-CONFIRMED`, `M` = 1** — and the mechanism is legible entry by entry

| # | entry | `c` / `n` | `m` (h) | signed `Δ` | `v_raw(Δ)` | rounds to | committed |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | 2023 PJM **import** 5 | 5,415 / 8,760 | **1** | **+1** | — | 27.86 | 27.86 ✓ |
| 2 | 2023 South **export** 4 | 3,259 / 8,760 | **1** | **−1** | 27.6900005 | **27.69** | 27.69 ✓ |
| 3 | 2024 South **export** 5 | 3,044 / 8,760 | **1** | **+1** | 23.7730485 | **23.77** | 23.77 ✓ |

`M` = max = **1** against a bar of **≤ 1** ⇒ **`A-CONFIRMED`**. Each `m` is `1.14e-4` of the year.

**Entry 3 is the one worth reading, because it is the entry that REFUTED the estimator-family story
in miso-244 §3 and it is reproduced here mechanically.** At `Δ=0` the quantile sits inside a flat run
of the sorted DA array: `x_lo == x_hi == 23.760000`, and R-3 measures that run to be **exactly 2 hours
long** (indices 3,043–3,044) with the **next distinct value 23.780001** — the series skips `23.77`
entirely there. So no order-statistic convention can return `23.77`, which is why "the code's
convention changed" was eliminated; but **one extra hour of export duration moves the position onto
the `23.76 → 23.78` segment at `frac` 0.6525 and lands at `23.7730485`, i.e. exactly the committed
cent.** The committed value is an *interpolated* one that only exists one hour away.

## 4. `G-CLAMP-N` — the leg that could only invalidate, and the margins are not close

| entry | clamp `lim` | `v_raw` at the reaching `Δ` | **margin below the clamp** | clamped at `Δ ∈ {−1,0,+1}`? |
|---|---:|---:|---:|---|
| 2023 South export 4 | 50.9812138 | 27.6900005 | **23.291 $/MWh** | **no** |
| 2024 South export 5 | 57.8504834 | 23.7730485 | **34.077 $/MWh** | **no** |

Every reaching value is the **unclamped quantile**. `A-CONFIRMED` stands with one more way it could
have been false removed; **the leg adds no evidence and is not read as if it did.**

## 5. `G-DRIFT` `a667073f..HEAD` — **ZERO HUNKS ON THE BACKCAST SOLVE PATH**, so form 4 holds

`a667073f` is the sha miso-244 audited to and is an ancestor of `origin/main` (re-verified); the
keeper's own `git.sha = 710d4dad` is re-confirmed **ORPHANED** (`git cat-file -t` → MISSING).

> `git diff a667073f origin/main -- src/market_sim scripts/run_calibration.py`
> `scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
> → **EMPTY.**

**35 files moved in the range and not one is on the audited solve path** — docs and handoff ledgers,
forecast scripts (`run_full_horizon.py`, `run_ces_leg.py`, `register_forecast_run.py`), scoring tests,
PJM's matrix shard, a scenario-campaign rollup, and one NYISO-keyed data corpus (`data/raw/nid/`)
outside every audited root. **There is nothing to classify, so there is no LIVE hunk, no control solve
is earned, and the KEEPER'S COMMITTED BUNDLE IS THE CONTROL.** `surface_stamp("MISO")` reproduces
**`8ee657ee4c7c49b0`**, rows **208**, `moved: {}`, `epochs: []` — **disclosed as EXPECTED** (a
deterministic stamp over an unchanged surface), not as independent corroboration.

**The footprint was re-measured in-session, BEFORE the table was edited** (after the edit the two
ladders are the same object and the gate has nothing to measure): `max_L` **0.00981735** (86 h, 2024,
`MISO_external_South`), `max |Δq̂|` **3.681507 MW**, `SCREEN_YEAR` **2024** by `argmax_year L` — the
year of the mechanism's own largest measured footprint, **never a residual year**. It reproduces
miso-244's JSON **byte-for-byte**, and **that agreement is disclosed as EXPECTED** (pre-declared in
addendum 1 §0d), not as corroboration.

## 6. THE EDIT, AND THE PIN THAT NOW HOLDS ALL 192

Published in addendum 2 §0 **before it was made**, and then made exactly:

| year | seam | side | band | from | **to** | live on the keeper? |
|---|---|---|---|---:|---:|---|
| 2023 | PJM | import | 5 | 27.86 | **27.87** | **no** — displaced by the PJM hourly overlay |
| 2023 | South | export | 4 | 27.69 | **27.70** | **yes** |
| 2024 | South | export | 5 | 23.77 | **23.76** | **yes** |

**The other 189 entries are byte-identical — checked, not assumed.**
`_MISO244_KNOWN_LADDER_DIVERGENCES` is **DELETED, not zeroed** (rule 26 `[R-DELETE]`), and
`test_incumbent_registry_reproduces_the_frozen_derivation` now holds **all 192 at `atol=0.005` with no
exceptions**. **No tolerance was widened anywhere.** Falsified twice before it was kept:

| perturbation | expected | **observed** |
|---|---|---|
| restore a reconciled entry to its stale value | FAIL | **FAIL** |
| move an untouched 2025 South import band by 6 c | FAIL | **FAIL** |
| restore | PASS | **PASS** (whole file **29 passed**) |

**P-1, the source-data provenance reading (REPORTED-ONLY, no decision rule attached):** the
interchange file holds **241,872** rows on `(diba, mw, local_time)` and the LMP file **43,800** rows
over **2022–2026** with `da` stored **float32** (miso-244's D-6, reproduced). Each corpus carries a
`README.md` (**9,295** / **7,607** bytes) and **neither carries a `SHA256SUMS.txt`**. The interchange
README documents the product, the EIA-930 2018 publication floor and a `--merge` back-fill — **but
that back-fill is CISO's, and it records no MISO re-fetch, merge or revision event**; MISO's span is
stated flatly as 2023–2025. `git log --no-merges` on each parquet returns **exactly one** entry, a
post-rewrite commit dated **2026-09-06**, which is the 2026-08-16 history rewrite showing through.
**So the on-disk record cannot name the revision event, exactly as §1 states, and P-1 licenses
nothing by itself.** It is where an A-REFUTED successor would have started and where a future
vintage-identification session still starts.

## 7. **THE 2024 SCREEN — one gate FAILED, was published first, was repaired STRICTER, and all four then cleared**

**Screen year 2024**, named by `argmax_year L` on the mechanism's own re-measured footprint (§5),
never on a residual. Control = the keeper's **committed** bundle (form 4). **The screen is STOP-only:
it killed nothing, and it promoted nothing.**

### 7a. **`S-3(b)` FAILED, and the failure is mine**

`S-3(b)` demanded the arm's `scenario_config` be *identical to the keeper's on every field*. It failed
on **four**: `gas_price_override` 2.54 → **2.19**, `weather_year` 2023 → **2024**, and
`netload_drag_layup_window_mask` / `pjm_thermal_accreditation_vintage` absent → **false**.

**The gate was UNSATISFIABLE as written.** `run_config.json` carries **one** `scenario_config` and
`pipeline/backcast_config.py::backcast_config` builds it **per year**, so a `--year 2023 2024 2025`
bundle records **2023's** and a `--years 2024` replay records **2024's**: two of the four fields cannot
match for **any** arm, including one with no delta at all. The other two are **new-field defaults** —
the absent behaviour the keeper solved with — both already **MEASURED or classified INERT for MISO
backcast** by miso-244, and both landed **before** `a667073f`, inside that all-INERT audit.

**`S-1`, `S-2` and `S-3(a)` compared the RIGHT objects and were unaffected** (both bundles' *year-2024
solve outputs*, and the derive's own table). Published in the pushed addendum **before** the repair's
numbers existed, so the repair could not launder them:

| gate | bar | **measured** | |
|---|---|---:|---|
| **S-1** `Δ mean net import` | `0 ≤ Δ ≤ 40 MW` | **+0.039378 MW** | **PASS** |
| **S-2** hours changed > 1 MW | ≤ 860 | **288** (3.29 % of the year) | **PASS** |
| **S-3(a)** derive reproduces the solved table, 192 entries | 0.00 | **0.0** | **PASS** |

**The repair, `S-3(b′)`, declared before its numbers existed and NOT a loosened bar:** every field on
which the arm differs from the keeper must fall into one of **two closed, MEASURED classes** —
**(P)** per-year, meaning the keeper's own recipe reproduces *both* recorded values, or **(N)** a
new-field default that is absent from the keeper, equal to the dataclass default, and on a **closed
two-field list** each carrying miso-244's own inert finding. **Any field in neither STOPS the arm.**
It **PASSES with zero unexplained fields**, and class (P) is exact:

| field | keeper | arm | class | measured |
|---|---:|---:|---|---|
| `gas_price_override` | 2.54 | 2.19 | **P** | `backcast_config(2023)` = **2.54**, `(2024)` = **2.19** (measured Henry Hub actuals) |
| `weather_year` | 2023 | 2024 | **P** | `backcast_config(2023)` = **2023**, `(2024)` = **2024** |
| `netload_drag_layup_window_mask` | *absent* | false | **N** | default `False`; `_resolve_drag_layup_shares(…, "MISO", y, 8760)` **len 0** all years |
| `pjm_thermal_accreditation_vintage` | *absent* | false | **N** | default `False`; capacity-evolution path a `mode="backcast"` run never enters |

**A CONTROL SOLVE WAS AVAILABLE AND WAS NOT SPENT, and the addendum said so rather than leaving it
unsaid**: rule 29(b) earns one only on a **LIVE** hunk and this session's G-DRIFT is empty, the two new
fields are already **measured** inert rather than classified from their gate, and `S-3(b′)` closes the
enumeration at zero LP. The addendum also fixed, in advance, that **if the enumeration had not closed,
the control solve was the next step and the arm stopped until it was spent.**

### 7b. `S-4` — **zero collateral flips**

`scripts/screen_collateral_gate.py --years 2024`, bench held fixed at the keeper's committed parts:
**`[PASS] G-4 no collateral flip (0 flips)`**. Two rows reported and gated in neither direction: the
`da_diagnostic` `price_mean` is **SKIPPED on both sides**, and **governance is not scorable at a
screen** (a screen bundle carries no attestation) — reported as such, never as a flip.

### 7c. **WHAT THE SCREEN ACTUALLY MEASURED, and it cost me a prediction**

The LP's mean response is **+0.039 MW against a pre-solve `Δq̂` of +3.682 MW — 1.1 % of it.** The
**sign is the one the arithmetic requires** and the **size is two orders of magnitude below it**. That
is exactly what miso-244 §0e predicted when it measured the moving band to be the **marginal
price-setter in 82 of its 86 hours** (a marginal band that moves takes the price with it, so a
footprint frozen at the committed price overstates the LP's response). **The screen's lower bound was
set at `0` rather than at `Δq̂` for precisely this reason, and that looseness was declared in advance
rather than discovered here.**

Reported beside the gates and gated in neither direction: `max |Δ|` = **375.000 MW**, **exactly one
South band step** (`3000/8`) — the correction's own quantum and nothing else — spread over **151 hours
positive / 137 negative** for a net **+344.951 MWh** across the year. **288 changed hours against an
86-hour pre-solve footprint** is the LP re-optimising around the moved band, well inside the 860 bar,
and it is reported at full magnitude rather than presented as a match.

## 8. **THE FULL SPAN — and the honest headline is that NOTHING SCORED MOVED**

`replay_keeper.py results/calibration/miso243_sppair_K --years 2023 2024 2025`, **ONE invocation, ONE
bundle, years sequential** (rules 12 / 16 / 29), solved in-session and never on CI. Per-year LP:
**707.1 s / 670.6 s / 693.2 s**. The keeper's attestation was carried forward and re-stamped so C6
does not read `UNATTESTED`.

| | **arm** `2026-09-08-miso-245-ladderfix` | keeper `2026-09-07-miso-243-spp-pairing` |
|---|---|---|
| **DETERMINATION** | **CALIBRATED** | CALIBRATED |
| C1 fuel-mix | PASS — **16/16 all-class, 12/12 free-class** | PASS — 16/16, 12/12 |
| C2 sysvol · C3a price_mean · C3b price_shape | PASS · PASS · PASS | PASS · PASS · PASS |
| C3c price_tail | **CAVEAT** (ledgered, non-downgrading, rubric v3.6) | CAVEAT |
| C4 dispatch_corr · C6 governance · C8 forced_share | PASS · PASS · PASS | PASS · PASS · PASS |
| grade summary | scored 8 / target 7 / ledgered 1 / **fails 0** | scored 8 / target 7 / ledgered 1 / fails 0 |
| DOF ledger | **41 / 2** | 41 / 2 |

**MEASURED, NOT ASSERTED: 245 of the 246 numeric leaves of the two verdicts are BYTE-EQUAL.** The
single move is `reported.co2.records[0].model` **279.417 → 279.418** — a **+0.001 Mt** change on a
**REPORTED-ONLY** stream the rubric demoted out of the determination at v2.9, contributing no status,
no caveat budget and no reason line. Three C8 forced-share *magnitude strings* differ in the fourth
decimal of a TWh (133.0936 → 133.0938, 145.1119 → 145.1117, 3.3283 → 3.3286) and **none changes a
status**. Every other difference between the two verdicts is the run id, the label, and my own
attestation text.

**SO THIS KEEPER DOES NOT IMPROVE THE FIT, AND IT DOES NOT CLAIM TO.** It is promoted because the
committed input is now the frozen estimator's **own output on the current source data** — rule 14
`[R-ACCURATE]`'s plain instruction — **at zero cost to every gate and with zero free parameters
added.** Rule 1 `[R-STRUCT]` is the governing sentence in both directions: a structurally-correct
input goes in whether or not the residual moves, and a residual that did *not* move is not evidence
for it either.

**Legitimacy diagnostics are INHERITED, not new.** D-1 `False` / D-2 `False` / D-4 `True`, exactly as
on the predecessor, with **CT_PEAKER forced share 0.4118 / 0.2617 / 0.2386 IDENTICAL** to the
keeper's — so C8 continues to pass **only** through rule 18's grounded conditional route, unchanged.
The replay's "legitimacy diagnostics gate FAIL" warning is that same inherited condition and **not a
regression this session introduced**; it was verified against the predecessor's committed artifact
rather than assumed.

## 9. Governance, what is handed forward, and the non-claims

**Rule 1** `[R-STRUCT]`: argued on construction and rule 14 throughout; **no criterion, band or
residual appears in any bar** of the diagnosis, the screen or the decision, in either direction; the
screen's gates are structural and STOP-only and none is the target residual. **Rule 12**
`[R-PARALLEL]`: one invocation, years sequential. **Rule 13** `[R-MEASURED]`: no measured *outcome*
entered anything; the reconciled values are the frozen estimator's output on a measured price and a
measured flow series, and would regenerate for a forward year. **Rule 14** `[R-ACCURATE]`: **this rule
is the session's result** — a stale committed value is replaced by the accurate one, and the fact that
the fit did not move is reported rather than used as an argument. **Rule 15** `[R-DASHBOARD]`: the run
is registered, the keeper promoted, the predecessor pruned (`--force-uncite`; narrative citations
dangle by design), MISO carries exactly **one** registered run, and the keeper's `hourly/` sidecars
are committed. **Rule 16** `[R-ALLYEARS]`: 2023+2024+2025 in one bundle; the 2024 screen bundle is a
throwaway probe, never registered, and its year was re-solved inside the full bundle. **Rule 17 /
18 / 19**: no floor, no bridge, no mechanism added. **Rule 21** `[R-DOF]`: **41/2, unchanged** — zero
free parameters added; the reconciliation is the frozen estimator's own arithmetic. **Rule 22**
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker, none was sought, and no
out-of-training year was solved, scored or registered. **Rule 23** `[R-FROZEN-DERIVE]`: the re-derive
cites a **source-data change**, established from the frozen estimator's output having moved (§1), with
`M` = 1 as a magnitude bound and its low power disclosed. **Rule 24** `[R-REGISTRY]`: no field, no env
knob, no CLI flag. **Rule 25** `[R-ISO-SCOPE]`: MISO's shard, section, lane, tests and table only.
**Rule 26** `[R-DELETE]`: `_MISO244_KNOWN_LADDER_DIVERGENCES` **deleted, not zeroed**. **Rule 27**
`[R-PUSH]`: on-disk edits only; every pushed blob ≥ 300 lines verified against local after push.
**Rule 28**: the handoff's recommended item taken; every standing adjudication corroborated or
untouched, never re-tested; MISO's shard alone updated in-session, with the keeper and gates
re-stamped on promotion. **Rule 29** `[R-SCREEN]`: satisfied end to end (§5, §7). **Rule 31**
`[R-RETAIN]`: see the non-claims below.

**HANDED FORWARD:**

1. **THE CACHE KEY DOES NOT SEE A MISO SEAM-LADDER RE-DERIVE** (§0d). `market_sim.model.interchange.spec`
   is outside the capx-D79 solve-surface fingerprint's phase 1 by explicit design (`solve_surface.py`
   §2.3), so `surface_stamp` and `cache_key` (`f130587822fbf565`) are **byte-identical before and
   after** this reconciliation, and a populated `results/MISO/<key>/` cache would serve a
   *pre*-reconciliation solve to a *post*-reconciliation config. **Verified inert for this run** —
   `results/MISO/` does not exist in this container — and handed to the solve-surface lane as a
   concrete cost for a known scope gap. It is **not** MISO's to close.
2. **THE VINTAGE IS STILL UNIDENTIFIED.** `M` = 1 bounds the magnitude; it does not name *which* hours
   of which series moved or when. P-1's provenance read (§6) is where a successor starts, and the
   2026-08-16 history rewrite is why the on-disk record cannot answer it.
3. **THE STRUCTURAL ITEM RULE 1 NAMES IS UNTOUCHED**: the model's SPP seam is 0.70–0.79
   spread-correlated while the measured one is +0.0409 / −0.0200 / +0.0502. **The seam being idle is
   not the anomaly; its being spread-driven is.**
4. **C3c REMAINS THE DESIGNATED FRONTIER** (model 3 / 7 / 11 h > $200 vs measured 30 / 37 / 88),
   byte-unchanged. It opens only by a **new admissible measured identification under its own charter
   plus an owner ruling** — never by an offer adder, ORDC offset, scarcity multiplier or any level
   tuned to the tail. **None was proposed, computed or armed here.**
5. **A DRAFTING LESSON, recorded because it cost this session a gate** (§7a): a gate that compares a
   multi-year bundle's `run_config` against a single-year replay's is unsatisfiable by construction,
   because `backcast_config` builds that record **per year**. Write such a gate against the *outputs*,
   or against an enumerated, measured account of the per-year fields.

**NON-CLAIMS:**

1. **No mechanism exists.** No `ScenarioConfig` field created or changed, DOF unchanged at 41/2, no
   cell verdict moved in either direction — the `seam_flow_envelopes` cell stays **K**.
2. **Nothing scored improved**, and §8 says so in place rather than presenting an unchanged verdict as
   a win.
3. **The attribution is bounded, not identified** (§0a, §1), and the low power of the test that bounds
   it is disclosed at full magnitude rather than left for a reader to infer.
4. **Rule 31 `[R-RETAIN]`:** the 2024 **screen** bundle is on local disk **outside the repository**
   (the session scratchpad), was never committed and never registered, and **will not survive this
   container** — every number this session will ever cite from it is in §7 and in
   `_miso245_screen_gates.json` / `_miso245_g4.json`, which are committed. The **predecessor keeper's**
   bundle was pruned only **after** the owner's explicit promotion instruction, under rule 31's
   trigger (i), and remains recoverable from git history with its own ASSESSMENT doc.
5. **No out-of-training year was solved, scored or registered**, and no marker was sought.
6. **MISO has no failing gate**, this session did not invent one, and nothing here trades a passing
   gate for anything.
7. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage** and no 2025 C1 pass is read as
   evidence anywhere above.
