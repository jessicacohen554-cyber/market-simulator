# FINDING nyiso-217 — the C1/C4 benchmark debt on `_screen_fuel_spike_columns` is **PAID and CLOSED**: the screen moves exactly one NYISO number, and **both** switches between it and C1 are shut. A **clean negative**, measured rather than argued — with two latent channels named that the clamp does **not** protect

**Session:** nyiso-217, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-bzuqb3`, on `main` at `12e71b89`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **keeper unchanged; nothing promoted, armed,
screened, registered or regenerated, no marker moved.**
**Pre-registration:** `results/calibration/PREREG-nyiso217-eia930-fuel-spike-screen-bench-debt.md`,
committed and pushed at `d27b3705` **before P1–P5 were measured** and not edited since.
**Machine record:** `results/calibration/_nyiso217_screen_bench_debt.json`.
**Instrument:** `scripts/probes/nyiso217_screen_bench_debt.py`.
**ZERO LP: no solve was spent.** No screen bundle, no control bundle, nothing under
`results/calibration/` to delete before merge under rule 29(c).

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES.** NYISO's keeper reads **CALIBRATED** with **zero**
failing criteria across 2023–2025, C3c the lone ledgered caveat. Nothing below was selected because
a residual moved (rule 1 `[R-STRUCT]`); no residual was consulted at any point, and the 2022
held-out rung is named nowhere as a target (rule 22 `[R-HOLDOUT]`).

---

## 0. The result in one paragraph

nyiso-215 §7 flagged `_screen_fuel_spike_columns` and was out of scope; nyiso-216 §1 discharged it
for the **fleet** path by execution and explicitly passed the **benchmark** half forward. This
session pays it, and the answer is a **clean negative with the arithmetic attached**. The screen
moves exactly **one** NYISO number in 2022–2025 — the EIA-930 `other` series in **2024**, `3.3846 →
3.3197 TWh`, from **one** flagged hour (h6759, `NG: OTH`, 16,117 MW against a p99.9 of 3,290) —
reproducing SPP-41's own declared NYISO effect **to four decimal places**, and nothing else moves in
any year, any series (P2). That number reaches C1 through exactly one channel,
`reconcile_vintage_classes`, and that channel has **two independent switches in series**: the
`max(0, classFull.OTHER + classFull.biomass − e930.other)` clamp, and the `_VINTAGE_RECONCILE_FRAC`
band. **In 2024 both are shut** — the clamp holds with 0.3590 TWh of headroom at the tighter
(screened) end, so `∂_tgt/∂e930.other = 0` exactly, and the reconcile provably did not fire.
`∂classFull/∂e930.other = 0`, the per-class move is **0.000000000 TWh**, and **C1 is unmoved**
(P3, case 3a). C2's gas-family actual, which has no band in its way, moves by **0** for the same
clamp (P4). C4 is immune on **both** counts it was predicted immune on: NYISO is not in
`CEMS_GAS_ANCHOR_ISOS` (only CAISO is, onset 2023), so C4 reads a committed payload value, **and**
the screen flags **zero** hours in `NG: NG` and `NG: COL` in every year (P5). And the whole reading
rests on an executed provenance check, not on code-reading: the keeper scores **byte-identically**
(43,261 characters, rc 0) with the screen live and with it monkey-patched to the identity (P1).
**All five predictions fired.** What went wrong was **mine, in the PREREG**: P3's declared
determination of whether the reconcile fired asserted a mutual exclusivity that **does not hold**,
and §4 reports the defect and what it leaves undetermined rather than restating the gate. Two
latent channels the clamp does **not** protect are named in §5 — **2022's clamp is open**, and
NYISO's **wind** mirror runs the opposite direction to solar's.

**Verdict: outcome-partition branch (B) — QUANTIFIED NULL. The debt is DISCHARGED and CLOSED.**

---

## 1. P1 — provenance, verified by EXECUTION: **FIRES**

Declared: score the keeper twice at this HEAD — once unmodified, once with
`market_sim.data.eia930.actuals._screen_fuel_spike_columns` monkey-patched to the identity — and
require the two verdict outputs to be identical; VOID if the patch cannot be shown to be in force.

| | unmodified | patched to identity |
|---|---:|---:|
| return code | 0 | 0 |
| stdout length (chars) | 43,261 | 43,261 |
| stdout | \multicolumn{2}{c}{**identical**} ||

The patch was verified in force by two in-child assertions before the scorer ran (the symbol is not
the original, and it returns its input frame unchanged for a synthetic `NG: X` column carrying a
1e9 MW spike). **P1 FIRES, and it does not VOID.**

**What it establishes.** The chain the PREREG read from source (C-1/C-2) is confirmed by execution:
`scripts/calibration_verdict.py` scores NYISO's keeper from **committed artifacts** —
`frontend/data/backcast/bench/NYISO/<year>.json.gz` for C1/C2 and `frontend/data/backcast/runs/
<keeper>.js` `fuelRows` for C4 — and never reaches the live EIA-930 loader. **A code change to the
screen cannot move a keeper score at all until a bundle regenerates the bench part and is
re-registered.** The keeper bundle carries no `inputs/`, so it cannot regenerate its own part.

That is the direct answer to the handoff's question (a), and it is the answer that had to be
established *first*, because it determines whether anything downstream could move a score.

## 2. P2 — does the screen move NYISO's live benchmark at all? **FIRES, exactly as declared**

Construction: `load_eia_hourly_benchmark("NYISO", year)` called twice per year at this HEAD, screen
live vs. monkey-patched to the identity, diffed on annual TWh, max per-hour delta and changed-hour
count, with a recording wrapper counting flagged hours per `NG:` column.

**Moved set over 2022–2025 × every series: `{2024: other}` and nothing else.**

| 2024 series | screen OFF (TWh) | screen ON (TWh) | Δ | hours changed |
|---|---:|---:|---:|---:|
| **other** | **3.3846** | **3.3197** | **−0.064890** | **9** |
| gas | 67.8019 | 67.8019 | 0 | 0 |
| coal | 0.0000 | 0.0000 | 0 | 0 |
| wind | 6.0116 | 6.0116 | 0 | 0 |
| solar | 0.0000 | 0.0000 | 0 | 0 |
| nuclear | 26.9554 | 26.9554 | 0 | 0 |
| hydro | 26.7777 | 26.7777 | 0 | 0 |
| oil | 0.2908 | 0.2908 | 0 | 0 |
| net_gen | 130.1135 | 130.1135 | 0 | 0 |
| interchange | −20.3469 | −20.3469 | 0 | 0 |

**2022, 2023 and 2025 are byte-identical in every series.** Flagged columns across all four years:
`{2024: "NG: OTH": 1}` — one hour, h6759.

**The bar is met with room to spare.** SPP-41's docstring claims NYISO 2024 `other`
`3.3846 → 3.3197`; measured `3.3846 → 3.3197`, i.e. **0.0000 TWh** against a declared **≤ 0.001 TWh**
bar, and the flagged-hour index h6759 matches exactly. The declared **hurts** limb — any additional
NYISO series or year moving, especially `gas`/`coal`/`wind`/`solar` — **does not fire**.

**A statistic I measured but did not gate on, reported in place.** The screen flags **1** hour but
the *delivered* `other` series changes in **9**. That is not a contradiction and it is not a defect:
it is the mechanism the screen's own docstring documents for exactly this hour — h6759 is a
16,117 MW `NG: OTH` spike immediately followed by a 9-hour NaN reporting gap, and NaN-ing the spike
lets the loader's `interpolate().bfill().ffill()` bridge spike **and** gap together from the last
real hour to the next, instead of interpolating *through* the spike and then smearing it forward.
I did not pre-register a changed-hour count and I am not classifying on it; I report it because a
reader comparing "1 flagged" against "9 changed" would otherwise have to reconstruct why.

## 3. P5 — C4's immunity: **FIRES on both declared counts**

* `NYISO ∉ CEMS_GAS_ANCHOR_ISOS`. The set is `{CAISO}` alone, onset 2023. So `score_dispatch_corr`
  reads the committed `ypay["fuelRows"]` for both families and never recomputes from `ybench`.
* The screen flags **zero** hours in `NG: NG` and `NG: COL` — the only two series C4's `gas` and
  `coal` families are built from — in **every** year 2022–2025.

Both limbs hold, so the two-count immunity argument stands as written and the partial-result clause
(count (i) alone) is not reached. The declared hurts limb — NYISO being a CEMS-anchor ISO in some
scored year — does not fire.

## 4. P3 — does the move reach `classFull`, and therefore C1? **FIRES (case 3a)** — and **my declared construction carried a defect, corrected here rather than restated**

### 4.1 The measurement

`e930` reaches `classFull` through exactly two writers (PREREG C-6). The VRE mirror is disposed of
by P2 (it can only fire if `wind`/`solar` move; neither does). For `reconcile_vintage_classes`:

| year | Δ`e930.other` | clamp headroom, **tighter (screened)** end | deflation, committed → screened | `∂_tgt` | reconcile | max per-class `classFull` move |
|---|---:|---:|---:|---:|:--|---:|
| 2022 | 0 | **−0.0408** | 0.0408 → 0.0408 | 0 | undetermined (§4.2) | 0.000000000 |
| 2023 | 0 | +1.9232 | 0 → 0 | 0 | **provably did not fire** (band headroom 1.2139 TWh) | 0.000000000 |
| **2024** | **−0.064890** | **+0.3590** | **0 → 0** | **0** | **provably did not fire** (band headroom **0.1777 TWh**) | **0.000000000** |
| 2025 | 0 | +0.4989 | 0 → 0 | 0 | undetermined (§4.2) | 0.000000000 |

`_VINTAGE_RECONCILE_FRAC = 0.97`. For 2024: `classFull.OTHER + classFull.biomass = 2.2014 + 0.7597
= 2.9611` against `e930.other` of `3.3850` committed and `3.3197` screened, so
`max(0, 2.9611 − x) = 0` at **both** values with **0.3590 TWh** of headroom at the tighter end —
comfortably past the declared **≥ 0.001 TWh** bar. Hence `∂_tgt/∂e930.other = 0` **exactly**, and
`classFull` is byte-identical **whether or not** the reconcile fires. **The prediction holds and
the outcome lands in declared sub-case (3a).** The declared hurts limb — `D > 0` at either `x`
*and* the reconcile firing — does not fire in 2024.

**C1 is unmoved.** Every gated class's `classFull` is unchanged, so `a_gen`, the volume band and
every `share_pp` denominator are unchanged, and no C1 record can move.

### 4.2 The defect in my own P3 construction

The PREREG's step 3 declared that testing `Σ committed fossil classFull == _tgt` (fired) against
the band test (did not fire) gives outcomes that are *"mutually exclusive and jointly exhaustive
given the code"*. **That is wrong.** Firing forces `post == _tgt`, and `_tgt` is trivially inside
the ±3 % band around itself — so the band test evaluated on the **post** sum returns True whenever
the reconcile fired. The two are not exclusive, and the first reading of the instrument returned
`fired=True, in_band=True` for 2022 and 2025, which is a state my declared partition said could not
occur.

Only one direction is sound, and the instrument now implements it:

* `post ≠ _tgt` ⇒ the reconcile **provably did not fire** (firing forces equality). Then
  `post == pre`, the band test on `post` *is* the band test on `pre`, and it is meaningful.
* `post == _tgt` ⇒ the reconcile fired, **or** it did not fire and `pre` coincidentally equalled
  `_tgt`. **The committed part cannot separate these**: pre-reconcile `classFull` is not
  recoverable without the bundle's `inputs/`, which the slim keeper bundle does not carry (C-2).
  Recorded as **UNDETERMINED**, and treated conservatively as *fired* wherever a sensitivity is
  computed, because that is the case in which `classFull` would move.

**What this leaves un-isolated, stated rather than guessed:** for **2022 and 2025** I do not know
whether the reconcile fired. I did not isolate it and do not claim to have.

**It changes no conclusion, and the reason is not that the defect is small.** In 2024 — the only
year in which anything moves — the reconcile provably did **not** fire, so the undetermined case is
not reached; and even if it had, the clamp is shut, which blocks the channel on its own. In 2022
and 2025 the reconcile state is undetermined but `Δe930.other = 0`, so `∂_tgt = 0` regardless. The
per-class move is `0.000000000 TWh` in all four years on either reading.

## 5. P4 — C2, and the two latent channels the clamp does **not** protect

**P4 FIRES.** C2's gas-family actual subtracts `bs.gas_foldin_deflation(cf, e930, iso)` directly,
with no reconcile band in the way — so it is the tighter test. Measured change:
**0.000000000 TWh** in every year, by the same clamp. The declared bar (0 when clamped, exactly
`|Δ|` when not) is met on its clamped limb. The declared hurts limb — a C2 move alone defeating the
clean negative — does not fire.

**Now the part that cuts against the comfortable reading, reported in place rather than absorbed.**
"Doubly protected" is true of NYISO **2024** and is **not** a structural property. Two channels are
live and merely unexercised:

* **2022's clamp is OPEN.** `classFull.OTHER + classFull.biomass = 2.1823 + 1.0615 = 3.2438`
  against `e930.other = 3.2030` — headroom **−0.0408 TWh**, so the deflation is a strictly positive
  `0.0408` and `∂_tgt/∂e930.other = +1` there. The screen happens to move nothing in 2022, so
  nothing moves. But the clamp is a **measured fact per year, not a guarantee**, and NYISO 2022 is
  on the wrong side of it. (2022 is a validation-tier year; nothing here solves, scores or
  registers it — this is arithmetic on a committed benchmark *input*, which rule 22's "what is held
  out is the SCORE, never the DATA" leaves unrestricted.)
* **NYISO's `wind` mirror runs the OPPOSITE direction to solar's**, and the clamp does not touch it.
  Verified by execution, not by reading the comment: `actuals_source("wind", "NYISO") == "eia930"`
  and `actuals_source("solar", "NYISO") == "eia923"`. So the render sets
  `classFull["wind"] ← e930["wind"]` — a **1:1** channel with no clamp and no band in it. Had the
  screen flagged a single `NG: WND` hour, `classFull.wind` and therefore `a_gen` would have moved
  by the full amount. It flagged none (P5), so nothing moves; I state the derivative and stop
  short of claiming any C1 record would have flipped, because I did not measure that.

**Neither is a defect to fix and neither is a lever.** They are named so a future NYISO lane that
sees a `NG:` flag land on `wind`, or on `other` in a year whose clamp is open, knows the channel is
open before it starts.

## 6. 2024 sits 0.1777 TWh inside a 3 % band — and the screen pushes it the safe way

Worth recording because it is the tightest number in the analysis. NYISO 2024's fossil `classFull`
sum is **65.9456 TWh** against a reconcile target of **67.8020**; the band's lower edge is
`0.97 × 67.8020 = 65.7679`, so the total sits only **0.1777 TWh** — 0.26 % — from the point at which
the reconcile would start rescaling every gas and coal class.

The direction matters and it is favourable, so I state it rather than leaving it as an implied
worry: the screen **lowers** `e930.other`, which (were the clamp open) would **raise** the deflation
and **lower** `_tgt`, moving the lower band edge **down** and 2024 **further inside** the band. The
screen cannot push 2024 into firing. What could is anything that raises `_tgt` by ≥ 0.183 TWh —
which is not this session's object and is not investigated here.

## 7. The ungated statistic — reported whatever it says

Declared in the PREREG: the **committed-vs-HEAD-rebuild** difference for NYISO's `e930` block,
which mixes the screen's effect with any other engine drift since the part was written and
therefore cannot isolate the screen (that is P2's job).

| year | worst-disagreeing series | committed | HEAD, screen ON | Δ |
|---|---|---:|---:|---:|
| 2022 | solar | 1.6295 | 0.0000 | **−1.6295** |
| 2023 | solar | 2.0479 | 0.0000 | **−2.0479** |
| 2024 | solar | 2.9008 | 0.0000 | **−2.9008** |
| 2025 | solar | 2.5673 | 0.0000 | **−2.5673** |

**The solar row is a BASIS difference, not drift**, and I verified that rather than asserting it:
NYISO's EIA-930 extract carries no solar at all (the loader returns 0.0000 in every year), and
`actuals_source("solar", "NYISO") == "eia923"` **by execution**, so the render deliberately writes
the EIA-923 utility-scale total *into* the `e930` slot — the branch whose own comment names NYISO
and the "spurious zero" it exists to avoid. The committed part is right and HEAD's raw loader is
not the comparator for that one series.

**Every other series agrees to ≤ 0.0005 TWh in every year**, the largest disagreement being 2024
`other` at **−0.0653** — which *is* the screen (−0.0649) plus the committed part's 3-decimal
rounding (3.385 vs 3.3846). So, setting the solar basis aside: **the committed NYISO bench part
reproduces what HEAD's builder would produce, and the screen is the only thing standing between
them.** That is the strongest form the clean negative can take, and it is why branch (B) rather
than (C) is the right closure.

## 8. An un-pre-registered check the screen's own docstring demanded

`_screen_fuel_spike_columns` names **three** consumers: the C1/C4 benchmark, the
`calibration_reference.json` builder, and **the model's delivered wind/solar profile**
(`load_eia_hourly_renewable_gen` → `renewables._eia_hourly_cf_profile` → the LP's wind bound). P2
covers the first. The third is checked here **because the docstring names it** — it is **not** a
pre-registered gate and nothing is classified on it.

Measured, screen live vs. identity, all four years: `wind` and `solar` **0 hours changed, max
per-hour delta 0.0** in every year. The LP's NYISO wind bound is untouched.

Together with nyiso-216 §1's fleet check, all three of the screen's declared consumers are now
measured inert for NYISO.

## 9. The verdict against the declared partition

The PREREG declared four exhaustive branches. The outcome lands in exactly one:

* **(A) nothing moves** — not reached: 2024 `other` moves.
* **(B) exactly SPP-41's declared set moves, and no scored quantity moves** — **THIS IS THE
  OUTCOME.** The moved set is exactly `{2024: other}`; C1, C2 and C4 are all measured unmoved, by
  arithmetic that is exact rather than approximate (`∂_tgt = 0` from a clamp with 0.3590 TWh of
  headroom, not a small residual). **The debt is DISCHARGED and CLOSED**, with the latent exposures
  of §5 named as the partition's "(3b)-style" clause required.
* **(C) a scored quantity moves** — not reached.
* **(D) a series outside SPP-41's declared set moves** — not reached; no escalation is owed to
  another lane.

**No outcome landed in a gap between branches.** (The defect of §4.2 was in P3's *internal*
determination of a sub-fact, not in the outcome partition.)

## 10. Governance, environment, and things found on the way

* **Rule 29 `[R-SCREEN]`:** step 0 only. **No screen, no control, no bundle, no LP.** Nothing to
  delete before merge under 29(c). **G-DRIFT** was re-measured `51f2fc2d` → `12e71b89` in the
  PREREG §0 (C-10) — **22 files, +9,879 / −23**, eight more than nyiso-216 audited at `71e62675`;
  the reasoning is inherited, the set is re-measured, per-file. **Twenty-one INERT** (SPP-44 bridge
  wiring across seven files, its constants and registry drops, CAISO 2022 rows in three files, two
  new default-off flags absent from the keeper's recipe, the D76 flip whose `__post_init__`
  coercion restores the frozen `False` for `not hindcast`, the SPP-only `_SPP_OFFER_CURVE` refactor,
  the ERCOT gas-basis branch, and SPP/CAISO validation-source artifacts), **one LIVE** —
  `data/eia930/actuals.py`, **which is this session's object** and is measured rather than argued
  about. The keeper's `run_config.json` confirms the D76 predicate by inspection: `mode = backcast`,
  `hindcast = False`, `capacity_screen_peak_measured_hindcast = False`.
* **Rule 29(b), stated as a scope limit:** this session used the keeper's committed artifacts as its
  **object of study**, never as a control for an arm, so no number here depends on the keeper bundle
  being a valid control. No control solve was contemplated.
* **Rule 22 `[R-HOLDOUT]`:** **no out-of-training year was solved, scored or registered.** 2022
  appears only as a loader-input diff and as arithmetic on a committed benchmark *input* — data
  preparation, explicitly unrestricted ("what is held out is the SCORE, never the DATA"). `complete`
  / `frontier` and the locked-test freeze are untouched; **2020/2021 stay unspent and were not this
  session's spend**; `final` remains never granted. No promotion contemplated, so D-5(b) does not
  attach.
* **Rule 15 `[R-DASHBOARD]`:** no run produced, nothing to register; keeper-only retention untouched.
  **No bench part was regenerated** — doing so would change what every registered NYISO run is
  scored against and is not a lane decision.
* **Rule 14 `[R-ACCURATE]`:** the screen is **not** weakened, haircut, bypassed or proposed for
  reversion under any outcome, and none was needed — it is measured inert for every NYISO scored
  quantity rather than tolerated.
* **Rule 23 `[R-FROZEN-DERIVE]`:** no derive script was run or re-derived; no source data changed.
* **Rule 25 `[R-ISO-SCOPE]`:** **no other ISO's bench was touched, read for comparison or
  regenerated.** Every number is NYISO's. SPP-41's declared cross-ISO effects are quoted from its
  docstring as the *claim under test*, never re-measured for another BA.
* **Rule 28 `[R-MECH-MATRIX]`:** `_screen_fuel_spike_columns` is a **data-loader repair, not a
  solve-affecting mechanism** — it is no `ScenarioConfig` field, no CLI flag and no matrix row, and
  it does not enter `cache_key()` ("data is not in the key", per its own docstring). It has no cell
  to stamp, and none is invented. No mechanism was tested, so no NYISO cell verdict moves.
* **Environment, measured at HEAD `12e71b89`:** `data/clean` built with
  `curate_capacity_deliverability.py` + `curate_nyiso_interface_flows.py` only. Fleet instrument
  validated: `scripts/probes/nyiso196_rebuild_checks.py --year 2024` exit 0 and
  `git status --porcelain -uno` **EMPTY** — its committed record reproduced byte-identically.
  Keeper `cache_key` **re-measured at this HEAD is `95d4d8d167373eb7`** — unchanged from
  nyiso-216's reading at `71e62675`, so the capx D79 solve-surface fingerprint did **not** move
  NYISO's key across this span; recorded, not used, since no solve was spent.
* **Test set run this session, named rather than inherited:**
  `tests/scoring/test_gate_a_provenance.py`, `tests/unit/data/test_cc_summer_derate_reconciled_basis.py`,
  `tests/scoring/test_holdout_render_parity.py`, `tests/unit/data/test_campd_bins.py`, plus
  `tests/scoring/test_bench_stamp_ast.py` (added because this session's object is the bench chain)
  — **83 passed, 2 skipped, 1 FAILED**. `ruff format --check .` reads **1,406 files already
  formatted** and `ruff check` passes.
* **THE ONE FAILURE IS PRE-EXISTING AT `main` AND IS NOT NYISO'S.**
  `test_gate_a_provenance.py::test_live_board_passes` fails because **SPP**'s
  `gate.a_keeper_marker` cites the superseded keeper `2026-09-07-spp-2-crosswalk-hydro` while
  `frontend/data/backcast/keepers/SPP.json` designates `2026-09-07-spp-3-screened-input`. Verified
  pre-existing **by execution, not by inference**: `git stash -u` to a clean `main` tree reproduces
  the identical failure (1 failed, 12 passed). It is the SPP lane's to repair (audit board F-5) and
  is **not repaired here** — rule 25, and the same discipline nyiso-216 applied to the stale
  `metrics.json`.
* **The stale-`metrics.json` trap is unchanged and was not walked into**: the keeper's committed
  `metrics.json` still reads `determination: NOT-YET` on a stale in-run reason while
  `scripts/calibration_verdict.py --run-id` returns **CALIBRATED** (P1 read the scorer, twice). It
  remains systemic across six bundles in five ISOs and is **not repaired here** — out of this lane.
* **Still no unit test covers `cc_reserve_duty_split`'s split behaviour** (nyiso-215's finding,
  nyiso-216's re-check). This session does **not** add one, for the reason both gave: a guard
  encoding the *current* membership would lock in both the two-basis defect and the
  pooled-denominator defect. This session adds no test at all, because it changed no behaviour —
  the instrument *is* the re-checkable record, and it re-runs in seconds.
* **No `check_bench_freshness.py` HARD gate is implicated, and that is by construction, not luck.**
  `bench_stamp.PAYLOAD_SOURCES` is exactly the three render/artifact scripts; the engine
  (`src/market_sim/`) is deliberately excluded and reported only in the SOFT tier. The screen is
  engine code, so the part it would change is not marked stale by the gate. §7 measures directly
  what the gate cannot see, and finds ≤ 0.0005 TWh of disagreement outside the screen and the solar
  basis.

## 11. Reported at full magnitude

* **All five pre-registered predictions FIRED**, and **none** of the five declared "hurts" limbs —
  each written to defeat the clean-negative answer I preferred — fired. Unlike nyiso-216 this
  session has no failed prediction, and I state that plainly rather than dressing a confirmation as
  a discovery: the object was a *verification debt*, and the honest result of paying a verification
  debt is usually confirmation. What makes it evidence rather than assumption is that P1 was
  settled **by execution** and P2/P4 by **exact arithmetic**, not by reading the docstring that
  made the claim.
* **My own PREREG carried a construction defect (§4.2)** — P3's fired/did-not-fire determination
  asserted a mutual exclusivity that does not hold. It is corrected in the instrument and reported
  as a defect; **the gate was not rewritten after the number was seen** (the prediction, the bar and
  the sub-partition are all untouched, and the outcome still lands in declared sub-case 3a).
* **What I did not isolate:** whether the reconcile fired in **2022** and **2025**. The committed
  part cannot separate "fired" from "did not fire, `pre` coincidentally equalled `_tgt`", because
  pre-reconcile `classFull` needs the bundle `inputs/` a slim bundle does not carry. Stated, not
  guessed. It changes nothing, for the reasons in §4.2.
* **Two statistics that cut against the comfortable reading are disclosed in place** and neither is
  absorbed: **2022's clamp is open** (headroom −0.0408 TWh, deflation strictly positive), and
  **NYISO's `wind` mirror is a 1:1 unclamped channel from `e930` into `classFull`** — so "doubly
  protected" is a fact about **2024**, not a structural property of NYISO. I state the wind
  derivative and stop short of claiming a C1 record would have flipped, which I did not measure.
* **A statistic measured but not gated on:** the screen flags 1 hour and the delivered `other`
  series changes in 9. Documented mechanism (the h6759 spike abuts a 9-hour reporting gap), reported
  rather than left for a reader to reconstruct.
* **§8's VRE-profile check was NOT pre-registered.** It is labelled as such, nothing is classified
  on it, and it is included only because the screen's own docstring names that consumer and skipping
  it would have left the debt two-thirds paid.
* **The ungated committed-vs-HEAD comparison cannot isolate the screen** and is not offered as if
  it could; its solar row is a basis difference verified by execution, and it is reported in full
  including the rows that look alarming before that verification.
* **Nothing here is dispatch evidence, at plant grain or any other grain.** Every number is a
  loader output, a committed benchmark value, or arithmetic over those. No claim requires a replay
  and none is made.
* **Nothing is built, armed, sized, screened or recommended**, no marker moved, no bench part
  regenerated, **no eighth owner card opened** — the seven pending rulings are untouched and cards
  (vi) and (vii) get no form.

---

*(nyiso-217, 2026-09-07. Zero LP. The gates were written and pushed before the first number was
read. The object was a debt two sessions had carried — nyiso-215 flagged it, nyiso-216 discharged
its fleet half by execution and passed the benchmark half forward — and it is now paid: the screen
moves exactly one NYISO number, that number's only route to a score passes through a clamp that is
shut with 0.36 TWh to spare, and the scorer could not have seen a code change in the first place
because it reads committed artifacts. The debt closes as a clean negative; what it leaves behind is
not a lever but two named open channels and the instrument to re-check them in seconds.)*
