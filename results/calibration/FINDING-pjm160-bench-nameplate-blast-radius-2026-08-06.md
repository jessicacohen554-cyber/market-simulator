# FINDING (pjm-160, task 1): the pjm-159 bench nameplate fix moves **3 of 26** PJM D-1 rows, all in the *improving* direction, and **flips no gate**. The keeper re-verifies CALIBRATED

**Session:** pjm-160 (task 1 — bench-regen blast radius)
**Date:** 2026-08-06
**Branch:** `claude/pjm-bench-regen-f3-closure-bj7q6o`
**Scope:** **Zero LP solves.** Committed artifacts in, committed artifacts out.
Keeper **UNCHANGED** at `2026-08-04-pjm-152-collapse`; no marker, no freeze, no
mechanism touched.

---

## §0 — the result

| | before | after |
|---|---|---|
| **Determination** | CALIBRATED, 0 fails, 0 caveats | **CALIBRATED, 0 fails, 0 caveats** |
| **D-1 rows moved** | — | **3 of 26** (all others byte-identical) |
| **D-2 rows moved** | — | **3 of 35**, all 2023, largest +0.33 TWh |
| **D-1 gate failures** | `2025 COAL_WC: profile r 0.749 < 0.8` | **identical** — same row, same value |
| **D-2 gate failures** | 3 × CT_PEAKER budget (16.4/16.7/16.8 %) | **identical to the decimal** |
| **D-4** | PASS | **PASS** |
| **Plant-years repaired** | — | 21 / 13.54 TWh (PJM 2022-2024; 2025 had none) |
| **Parity guard** | — | 194 / 197 / 197 / 196 plants re-encode **byte-identically** |

```
2023 COAL_BIT   profile_r 0.888 -> 0.892  (+0.004)   cv_ratio 0.890 -> 0.876
2023 ST_GAS     profile_r 0.970 -> 0.973  (+0.003)   cv_ratio 1.830 -> 1.583
2024 COAL_BIT   profile_r 0.869 -> 0.870  (+0.001)   cv_ratio 1.137 -> 1.136
```

**Rule 14 disposition: the accurate input is kept.** All three `profile_r` values
*improve* and `COAL_BIT`'s `cv_ratio` moves toward 1.0 in both years; D-2 moves
+0.33 TWh **against** the model (more measured forced coal — §4), on a class at
4.77 % of a 30 % budget, and is kept anyway. **Nothing to escalate: no gate
flips on either diagnostic.**

---

## §1 — what was regenerated, and why it needed a new tool

pjm-159 task C (`46bd8a6b`) unioned the within-window retiree EIA-860 vintage
into `render_calibration_html._eia860_plant_info`, fixing the `npl = 1 MW`
fall-through for plants that ran during the backcast window and retired before
the operable snapshot. Its own commit message is explicit that **no committed
bench part moved**: the payload rebuilds only when a run registers, and no PJM
run has registered since.

A full re-render is not available without a solve — `render_calibration_html`
needs the bundle's `system.parquet` and `dispatch/<year>_P1.parquet`, both
gitignored and absent in a fresh container, plus the `_shared/` input store. So
this session adds **`scripts/regen_bench_nameplate.py`**, a targeted repair on
the `regen_nyiso_bench_nuclear.py` precedent: it rewrites exactly `npl`, `name`
and the `campd` blob on the affected plants and leaves every other field and
every other plant byte-for-byte.

### §1.1 — the parity guard is what makes a targeted patch admissible

The script rebuilds the CAMPD per-plant hourly frame from `data/raw` with the
**solver's own builder** (`run_calibration_full._campd_hourly_frame`) and then
re-encodes every unaffected single-class plant at its committed nameplate. All
of them must come back byte-identical or the run aborts — a mismatch would mean
the rebuilt frame is not the frame the committed part was built from, and the
patch would silently mix two bases.

| bench part | plants verified byte-identical | plants repaired |
|---|---:|---:|
| PJM 2022 | 194 | 10 |
| PJM 2023 | 197 | 9 |
| PJM 2024 | 197 | 2 |
| PJM 2025 | 196 | **0** |

The only plants that failed byte-identity on the first (diagnostic) pass were
**exactly** the `npl == 1` population — 7 of 206 in 2023 — which is the
strongest available evidence that the rebuild reproduces the render's basis.

One detail worth recording because it would silently defeat a naive re-encode:
the committed `npl` field is `round(cap)` while the blob is encoded at the
**unrounded** `cap`. Re-encoding at the rounded value mismatches 113 of 206
plants; at the unrounded value, 199 of 206 match and the 7 that don't are the
defect population.

### §1.2 — what was repaired

21 plant-years / 13.54 TWh across PJM 2022-2024. The material ones:

| year | plant | class | npl | blob distinct bytes | at 250-clip | hourly L1 move |
|---|---|---|---:|---|---:|---:|
| 2022 | 2866 W H Sammis | COAL_BIT | 1 → 1,706 | 4 → 68 | 87.0 % → 0 % | 36.0 % |
| 2022 | 3122 Homer City | COAL_BIT | 1 → 2,012 | 3 → 52 | 80.8 % → 0 % | 32.6 % |
| 2022 | 384 Joliet 29 | ST_GAS | 1 → 1,320 | 4 → 82 | 15.7 % → 0 % | 67.3 % |
| 2022 | 10678 AES Warrior Run | COAL_BIT | 1 → 229 | 4 → 54 | 84.7 % → 0 % | 10.5 % |
| 2023 | 2866 W H Sammis | COAL_BIT | 1 → 1,706 | 4 → 57 | 22.5 % → 0 % | 48.5 % |
| 2023 | 3122 Homer City | COAL_BIT | 1 → 2,012 | 2 → 44 | 27.9 % → 0 % | 36.5 % |
| 2023 | 384 Joliet 29 | ST_GAS | 1 → 1,320 | 3 → 82 | 16.4 % → 0 % | 58.8 % |
| 2023 | 10678 AES Warrior Run | COAL_BIT | 1 → 229 | 3 → 63 | 72.6 % → 0 % | 26.4 % |
| 2024 | 10678 AES Warrior Run | COAL_BIT | 1 → 229 | 2 → 50 | 34.0 % → 0 % | 26.2 % |

The remaining 12 are sub-0.05 TWh entries the pjm-159 probe's materiality floor
hid (874 Joliet 9, 2379 Carlls Corner, 3809 Yorktown, 8008 Mickleton, 50799
Parlin, 55281 Southeast Chicago). They carry the same defect and are repaired
for consistency; several are all-zero series and move nothing.

**Per-plant hourly L1 movement is 10-67 % of the plant's own energy** — the
defect really did destroy the loading profile, exactly as pjm-159 characterized.
It nonetheless moves D-1 by ≤0.004 because these plants are 0.3-7.6 % of their
class (§3).

---

## §2 — the defect is TWO-SIDED, and the model half is NOT repaired here

**This is the caveat that governs how the D-1 delta may be read, and pjm-159's
commit did not state it.**

The model payload's per-plant blob is encoded through the **same** nameplate:
`render_calibration_html` writes `"m": _b64(100.0 * mw / cap)` with
`cap = npl_s.get(key) or 1.0` — the identical fall-through. Measured on the
keeper's committed payload:

| year | plant | model blob distinct bytes | at 250-clip |
|---|---|---:|---:|
| 2023 | 2866 | **2** | 32.9 % |
| 2023 | 3122 | **2** | 41.4 % |
| 2023 | 10678 | **2** | 72.6 % |
| 2024 | 10678 | **2** | 33.2 % |

So the model side of those plants is also a run indicator. Repairing it needs
`dispatch/<year>_P1.parquet`, i.e. a re-solve, so **after this repair D-1
compares a correct actual against a still-saturated model for those plants.**

Two things follow, and they matter in opposite directions:

1. **The naive expectation was a false degradation.** Both sides were flat-when-on
   before, so their correlation was spuriously *high* — both tracked the same
   commitment pattern. Fixing only the actual side should, on that reasoning,
   break the agreement and lower `profile_r`.
2. **It did the opposite.** `profile_r` rose in all three affected cells. The
   corrected actual profile is a *better* match to the model's real dispatch
   than the saturated one was, even with the model side still degraded. The
   repair therefore cannot be accused of manufacturing an improvement by
   symmetry, and the residual model-side defect is bounded above by the small
   movement observed.

**Recommendation, not action:** the model half closes for free the next time PJM
registers a solve, since `dashboard_add_run.py` re-renders the payload through
the fixed lookup. No re-solve is justified *for this defect alone* — §3 bounds
its remaining influence at a few thousandths of `profile_r`.

---

## §3 — the movement is fully attributed (exclusion diagnostic)

`regen_bench_nameplate.py --exclusion-diagnostic` reports each affected class's
energy share held by repaired plants, identified definitionally (present only in
the retiree EIA-860 vintage) so it reads the same before and after the repair:

| year | class | affected TWh | class TWh | share | D-1 moved? |
|---|---|---:|---:|---:|---|
| 2023 | COAL_BIT | 2.550 | 103.216 | **2.5 %** | yes (+0.004) |
| 2023 | ST_GAS | 0.708 | 9.372 | **7.6 %** | yes (+0.003) |
| 2024 | COAL_BIT | 0.316 | 104.542 | **0.3 %** | yes (+0.001) |
| 2023 | CC_REGULAR | 0.008 | 318.941 | 0.0 % | no |
| 2023/2024 | CT_PEAKER | 0.007 / 0.002 | 19.918 / 21.500 | 0.0 % | no |
| 2022 | COAL_BIT / ST_GAS | 9.330 / 0.588 | 131.600 / 8.811 | 7.1 % / 6.7 % | *(not scored — §5)* |

The model side's exposure is the same size (2023 COAL_BIT 2.8 %, ST_GAS 5.6 %;
2024 COAL_BIT 0.2 %), so neither half dominates.

**Every class that moved holds a repaired plant, every class that holds one at
≥0.3 % moved, and nothing else moved at all.** The delta is the repair and
nothing but the repair.

---

## §4 — the gates

**C7 does not exist any more.** The task brief anticipated "C7 (D-1 `profile_r` /
`cv_ratio`) and C8 may move", but C7 was **retired outright** by the rubric v3.1
owner amendment of 2026-08-06: `score_shape` and `C7_GATED_CLASSES` are deleted
per rule 26 `[R-DELETE]`. D-1 survives as a measurement and now binds **only**
through rule 21's grounded-above-budget escalation for C8. So the D-1 movement
above has exactly one gating route, and it is C8's.

**C8 does not move — but NOT for the reason a first reading suggests, and the
difference is worth stating because it was measured rather than argued.** An
earlier draft of this section claimed the bench `npl` cannot reach D-2 at all,
since `_decode_cf_bytes` ignores `npl` whenever `c_ann`/`m_ann` is present
(which is always). **That is wrong.** `npl` reaches D-2 through a second door:

```python
def at_floor_mask(dispatch, min_gen, npl=None):
    atol = np.full(dispatch.shape[0], D2_FLOOR_MIN_MW)
    if npl is not None:
        atol = atol + 0.01 * np.asarray(npl, dtype=float)   # <- here
```

The at-floor tolerance widens with nameplate, because the payload's byte encoding
quantizes to ~1 % of it. A plant sitting at `npl = 1` was therefore given a
tolerance of ~0.01 MW against a series quantized at ~17 MW — so its at-floor
hours were **under**-counted. The repair widens the tolerance to the correct
value and the measured forced energy goes **up**.

**Measured like-for-like** (identical bundle, identical rebuilt floors, identical
container; only the bench parts swapped between `origin/main` and the repair):

| year | class | mechanism | forced TWh | share of class |
|---|---|---|---:|---:|
| 2023 | COAL | `coal_mustrun` | 5.0838 → **5.4141** | 4.48 % → **4.77 %** |
| 2023 | ST_GAS | `st_netload_drag` | 4.8171 → **4.8378** | 50.89 % → **51.11 %** |
| 2023 | CT_PEAKER | `ct_netload_drag` | 2.2475 → **2.2481** | 10.89 % → 10.89 % |

**3 of 35 D-2 rows moved, all in 2023, and D-2's gate failures are byte-identical
before and after** — the same three CT_PEAKER budget breaches at the same
16.4 / 16.7 / 16.8 %. **D-4 PASSES on both sides.**

That the accurate input moves a *protective* metric **against** the model
(+0.33 TWh of measured forced coal) and is kept anyway is the rule-14 disposition
working as intended — and it lands nowhere near a cap: COAL at 4.77 % against a
30 % merchant budget, and ST_GAS 2023's 51.1 % is **immaterial** (1.4 % of ISO
load, below the 2 % gating floor) and was already 50.9 % before.

**None of the four C8 grounded notes is affected.** CT_PEAKER's repaired plants
are 0.0 % of the class in every year, and 2025 — which carries the ST_GAS note —
had **zero** repairs. D-1's `profile_r` / `cv_ratio` reach C8 only through those
four notes, whose margins are wide:

| note | profile_r | gate | off-peak CV | gate |
|---|---:|---|---:|---|
| 2023 CT_PEAKER 16.2 % | 0.927 | ≥0.8 | 0.719 | ≥0.5 |
| 2024 CT_PEAKER 16.4 % | 0.962 | ≥0.8 | 1.075 | ≥0.5 |
| 2025 CT_PEAKER 16.7 % | 0.974 | ≥0.8 | 0.836 | ≥0.5 |
| 2025 ST_GAS 39.9 % | 0.896 | ≥0.8 | 2.242 | ≥0.5 |

All four remain clean grounded PASSes.

**And C8 as *gated today* cannot have moved at all**, because
`calibration_verdict` reads C8 from the bundle's **committed**
`legitimacy_diagnostics.json`, which this session deliberately did not overwrite
(it was generated on the higher-fidelity `dispatch/*.parquet` path, which is
absent here). The D-2 numbers above are what a regeneration *would* read. Both
statements are reported because only together do they answer "did the gate
move?" — no, and it would not move if regenerated either.

**Verdict re-verified on committed artifacts, no solve:**

```
CALIBRATION DETERMINATION: CALIBRATED     scorable years 2023, 2024, 2025
C1 PASS · C2 PASS · C3a PASS · C3b PASS · C3c PASS · C4 PASS · C6 PASS · C8 PASS
D-10 free-class C1: all 16/16 · free 12/12        ZERO fails, ZERO caveats
```

### §4.1 — a pre-existing D-1 failure, unchanged and correctly non-gating

`2025 COAL_WC: profile r 0.749 < 0.8` fails D-1 **before and after**, at the same
value, and is already recorded in the committed `legitimacy_diagnostics.json`.
It is not a gate failure: C7 is retired, and COAL_WC is not over its C8 budget,
so rule 21's shape leg never engages for it. Noted so the next reader does not
mistake it for something this session introduced.

---

## §5 — PJM 2022 was repaired but is NOT re-scored

The 2022 bench part carries the largest stranded population (4 plants / 9.87 TWh,
7.1 % of COAL_BIT). It **is** repaired, because a measured input is applied
consistently across all years — the owner's 2026-08-06 clarification is explicit
that *"what is held out is the SCORE, never the DATA"* — and the holdout freeze's
own `frozen_operations` are solve / score / registration, with data intake named
in `not_frozen`.

**The 2022 touchpoint is NOT re-scored, and its committed
`legitimacy_diagnostics.json` is left alone.** Its D-1 rows are therefore on the
pre-repair bench basis; anyone re-quoting them should re-derive first. Re-scoring
2022 would be a validation-tier spend, and the freeze is ACTIVE.

---

## §6 — cross-ISO: not this session's to move (rule 25)

The same defect is live in MISO (Edwardsport 1004, Rush Island 6155 — 6.16 TWh),
NEISO (Mystic 1588 — 4.27 TWh) and CAISO (AES Redondo Beach 356 — 0.29 TWh).
`regen_bench_nameplate.py` takes a required `--iso` precisely so one ISO's
session cannot move another's gates; **only PJM was run.** Each of those ISOs'
keepers holds `COAL_BIT` / `COAL_PRB` / `CC_REGULAR` / `ST_GAS` classes that
would move, and MISO's Edwardsport is 1.19-1.88 TWh in a class far smaller than
PJM's, so its D-1 delta will be larger than PJM's and belongs in a session that
can own the result.

---

## §7 — reproduction

```
python scripts/regen_bench_nameplate.py --iso PJM --check                # dry run + parity guard
python scripts/regen_bench_nameplate.py --iso PJM                        # apply
python scripts/regen_bench_nameplate.py --iso PJM --exclusion-diagnostic # attribution
python scripts/legitimacy_diagnostics.py --bundle results/calibration/pjm152_collapse_A \
    --iso PJM --years 2023 2024 2025          # D-1 + D-2 + D-4
python scripts/calibration_verdict.py --run-id 2026-08-04-pjm-152-collapse
```

The D-2/D-4 half needs two things this container did not start with: the clean
tree (`python scripts/regenerate_clean.py`, for the floor rebuild) and the
`pjm-da-virtuals` corpus, which is **gitignored** and whose loader refuses to
degrade — `python scripts/data/fetch_pjm_da_virtuals.py --feeds hrl_da_incs_decs`
(2023-2025, in-sample, unrestricted). Worth recording as a general fact rather
than a session note: **that fetch is a prerequisite of ANY PJM solve or floor
rebuild in a fresh container**, not something specific to a holdout year.

The before/after is a true swap — the pre-fix bench parts were restored from
`origin/main`, the identical command re-run, and the parts put back — so the
floor rebuild, the container and the bundle are common to both sides and the
only difference is the bench.

Both sides run the **payload** dispatch path (the committed
`legitimacy_diagnostics.json` was generated with `dispatch/*.parquet` present,
which reproduces `profile_r` to ±0.001 but differs on the non-gated CHP classes'
`cv_ratio`, and shifts CT_PEAKER's D-2 share by ~0.2 pp). Comparing a
payload-path "after" against the committed "before" would have manufactured
deltas of exactly that size and attributed them to the repair; every number in
§0/§3/§4 is payload-path on both sides.

---

## §8 — governance

- **Rule 22.** No year solved, scored or registered. 2022's bench part is
  repaired as a measured input (§5), not scored. Freeze ACTIVE, untouched.
- **Rule 14 `[R-ACCURATE]`.** The accurate nameplate is kept; the movement is
  reported at full magnitude; no revert to the broken denominator. Nothing
  needed escalating — no gate moved.
- **Rule 15.** No run produced, so nothing is owed to either dashboard. The
  changed bench parts are committed with this finding.
- **Rule 25 / rule 28.** A shared data-builder repair is not a mechanism
  verdict; no cell moves, no matrix edit owed, PJM's lever queue untouched
  and still clear.
- **Rule 27 `[R-PUSH]`.** Opus. No existing source file ≥300 lines rewritten;
  one new script added.
- **Keeper UNCHANGED** at `2026-08-04-pjm-152-collapse`; `audit_keepers.py --iso
  PJM` re-run after the repair → **0 failures, 0 warnings**. The bundle's
  committed `legitimacy_diagnostics.json` was **not** overwritten.
- **Test suite.** `tests/curation` + `tests/scoring`: 1,650 passed, 8 failed —
  **none of them this session's.** Four (`test_curate_ercot_wtx_congestion.py`
  ×3, `test_dam_public_bids_expand_rle.py`) were a **missing `tzdata` package**
  in this container (`ZoneInfoNotFoundError: US/Central`, the same cause that
  failed the `ercot-wtx-congestion` clean regen) and **pass once it is
  installed**; two are the forecast-parity debt the session brief already named
  as pre-existing (ERCOT `ercot_storage_as_soc_reserve`, NYISO
  `nyiso_seam_deliverability_envelope`); one is a stale data-dictionary table for
  `som-competitive-conduct`, a datatype untouched here; one is a clean-vs-raw
  LMP parity check on the regenerated clean tree, reading no file this session
  modified.

**Next shorthand: pjm-161.**
