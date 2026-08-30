# FINDING — the 11 "STALE" bench parts are UNLABELLED, not wrong

**Date:** 2026-08-30 · **Base:** `origin/main` @ `3f7388e` · **Branch:**
`claude/bench-fingerprint-adjudication-iu89db`
**Scope:** adjudicate `scripts/check_bench_freshness.py`'s 11 HARD failures and clear
`scripts/audit_keepers.py` check S1. **No keeper moved. Nothing was regenerated. No
holdout year was spent.**

---

## 0. Verdicts, up front

| Question | Answer |
|---|---|
| `audit_keepers.py` (problem i, status staleness) | **GREEN — cleared.** 0 failures, 0 warnings. |
| Are the 11 unlabelled parts *wrong*? | **No — they are unlabelled.** Every measurement taken says the bytes are what HEAD produces. |
| Is any keeper's C1 verdict in doubt? | **No.** No keeper re-verification is required. |
| Do the benchmark inputs reproduce at HEAD? | **Yes — all three frames, all six ISOs, content-addressed byte-identical.** |
| Recommended remedy for problem (ii) | **RE-STAMP, do not regenerate.** Measured feasible on 20/20 parts. Owner's call; not done here. |
| Engine-drift warnings (9 parts) | **No CALIBRATED ISO is marginal.** Two NOT-YET ISOs carry tight C1 rows — listed in §5. |
| State problem (ii) was left in | **OPEN, pending the owner's ruling on the remedy.** `check_bench_freshness.py` still exits 1; it is not wired into CI. |

---

## 1. Read the flag before acting on it

All 11 HARD failures carry builder fingerprint **`(none: predates the stamp)`**. That string is
not evidence the payload is wrong. `scripts/lib/bench_stamp.py` — the thing that writes the
stamp — **did not exist** when those parts were written. It landed 2026-08-21 in `e1131187`
(nyiso-148). Every part written before that date is unstamped *by construction*, and
`check_bench_freshness.py` treats absence and mismatch identically (module docstring: "or is
ABSENT, which means the part predates the stamp").

The parts split into exactly two cohorts, and the split is the stamp's own arrival date:

| cohort | ISOs | parts | last written | stamp |
|---|---|---|---|---|
| pre-stamp | PJM, CAISO, NEISO | 11 | 2026-08-15 … 2026-08-17 | absent |
| post-stamp | ERCOT, MISO, NYISO | 9 | 2026-08-23 … 2026-08-24 | `dbea7bf45111` = HEAD |

Last-writing commits for the pre-stamp cohort: PJM 2023/2024 `c36ac42` (2026-08-15, the pjm-162
keeper registration), PJM 2025 `02094a4` (2026-08-07, byte-identical at pjm-162 — that
registration's own commit message records "2025.json.gz byte-identical"); PJM 2022 same family;
CAISO `5b2b253` (2026-08-16, caiso-197); NEISO `99dcb60` (2026-08-17, neiso-97).

**This did not settle it.** The builder sources *did* change after those dates — so "unstamped"
alone does not prove "current". That is what the measurements below are for.

### What would kill this story

The story is *"the pre-stamp parts are byte-current; only the label is missing."* It dies if
either of two things is true:

1. **Builder drift.** A change to one of the four `BUILDER_SOURCES` between the part's writing
   and HEAD that reaches a PJM / CAISO / NEISO bench payload. → §2.
2. **Input drift.** The benchmark input frames (EIA-923, EIA-930, CAMPD) no longer reproduce at
   HEAD from `data/raw`. This is the nyiso-148 failure mode — the one that moved a metered
   actual by ~4 TWh and flipped every registered NYISO run. → §3.

Both were measured. Both come back clean.

---

## 2. Builder drift — the complete change set in the window

`BUILDER_SOURCES` is four files. Enumerated over GitHub's commit history (the local clone is
shallow at 263 commits / 2026-08-23 and cannot see this window), the **complete** set of commits
touching any of them since the earliest pre-stamp part was written (2026-08-15) is three:

| commit | date | file(s) | reach |
|---|---|---|---|
| `01db36d` nyiso-147 | 2026-08-20 | `render_calibration_html.py` | **NYISO-gated** |
| `e1131187` nyiso-148 | 2026-08-21 | `backcast_artifacts.py`, + new `bench_stamp.py` | **adds `meta.builderFingerprint` only** |
| `28ac3c2` nyiso-149 | 2026-08-22 | `render_calibration_html.py` | **NYISO-gated** |

`scripts/render_backcast.py` has no commit since before 2026-08-01. So **three commits, of which
two are ISO-gated and one is the stamp itself.** The fingerprint mismatch is fully explained by
its own introduction plus two NYISO-scoped changes.

The gates, read at HEAD rather than taken from the commit messages:

* `render_calibration_html.py:1305` — the measured-CHP-BTM block is inside
  `if meta.get("iso") == "NYISO":`.
* `render_calibration_html.py:1632` — `_bcol = "btm_bench_twh" if "btm_bench_twh" in
  _by.columns else "btm_twh"`. `run_calibration_full._btm_frame` (line ~2665) sets
  `share_bench_by_plant = dict(share_by_plant)` and diverges only under `if iso == "NYISO":`,
  then `btm_bench_by_class = dict(btm_by_class) if share_bench_by_plant == share_by_plant else
  …`. **For every non-NYISO ISO the two columns are equal by construction**, so the column
  preference is a no-op. The code comment says so in as many words; the code agrees.

Corroboration rather than assertion: `tests/regression/test_btm_bench_basis_pin.py` +
`tests/scoring/test_backcast_artifacts.py` — **20 passed** at HEAD in this session. The latter
includes `test_committed_bench_parts_rewrite_byte_identical`, which requires that any byte
difference on re-write be *explained by the staleness stamp* and fails on unexplained writer
drift.

**Leg 1: no builder change in the window can reach a PJM / CAISO / NEISO bench payload.**

---

## 3. Input drift — the decisive measurement (content-addressed)

### Why the "obvious" measurement is impossible from committed artifacts

The prompt's ideal test — re-run the builder for one stale part and diff the bytes — cannot be
run from the committed tree, and this is worth recording because it is exactly why the check's
own remedy is expensive. `render_calibration_html.build_payload` reads
`<bundle>/dispatch/<year>_P1.parquet` and `<bundle>/system.parquet` (lines 1319–1349). Both are
**gitignored** (`.gitignore:458-459`, slim-bundle rules). Every bundle in
`results/calibration/` on disk is slim — `meta.json`, `run_config.json`,
`calibration_attestation.json`, `legitimacy_diagnostics.json`, `metrics.json`, `hourly/`.
A faithful end-to-end bench-part rebuild therefore needs an LP re-solve, which is precisely the
cost this session was told not to pay blind.

### What *is* measurable, and why it is the measurement that matters

The bench payload's **metered actuals** — `classFull`, `e930`, `co2`, `plants` — are reductions
over three benchmark input frames: EIA-923 (with CAMPD backfill), EIA-930, and CAMPD net.
`run_calibration_full.rebuild_benchmark` regenerates exactly those three from `data/raw`, and its
docstring is explicit that they "are pure functions of `(year, iso)` and the reference data; they
do not depend on the model dispatch" — **no LP re-solve**. They are then written to the
**content-addressed** shared store `results/calibration/_shared/<ISO>/<name>-<sha8>.parquet`, and
each bundle's `meta.json` records the reference it actually used.

So: regenerate at HEAD, read back the sha8, compare to the recorded one. **The filename *is* the
content hash of the decompressed frame** — a byte comparison of the metered-actual inputs, not an
mtime, not a gzip envelope.

This is also the *right* target. In nyiso-148 the drift was not in the serializer; it was
carried by "the ENGINE import closure (plant→class map, CHP shares, EIA-923 reconciliation)" —
all three of which enter through these frames (`_benchmark_eia923_frame` takes `group_by_code`
and `e930` directly).

### Result — all six ISOs, run on a copy, committed bundles untouched

Each ISO's **current keeper** bundle, regenerated at HEAD `3f7388e` under the
`requirements.txt`-pinned stack (numpy 2.4.6, pandas 3.0.3, pyarrow 24.0.0, scipy 1.17.1,
pydantic 2.13.4):

| ISO | keeper | eia923 | eia930 | campd | reproduces |
|---|---|---|---|---|---|
| **PJM** | 2026-08-15-pjm-162-inputclock | `e0bf0ae64c3e` | `a18e7d0dec0e` | `db315991835d` | **YES** |
| **CAISO** | 2026-08-17-caiso-200-h1-memberpanel | `8ca120c6637d` | `3697b3115384` | `48c0f1dd36b6` | **YES** |
| **NEISO** | 2026-08-17-neiso-99-joint-p1 | `a2384ce8cfeb` | `d398d867c742` | `28501f5539d0` | **YES** |
| ERCOT | 2026-08-25-236-swcap-clip-k33 | `4e3039759c22` | `aba4caff3283` | `9ac4ee9da248` | **YES** |
| NYISO | 2026-08-25-nyiso-155-hydro-repair | `920c8b8bc1b1` | `d866a7741788` | `521a01f3ccd1` | **YES** |
| MISO | 2026-08-26-miso-187-nucavail | `1a5b4475b1f3` | `a257b22934ed` | `0c8c8860e930` | **YES** |

**18 of 18 frames reproduce byte-identically at HEAD.** The three bold rows are the affected
ISOs, confirmed one per ISO as instructed so the conclusion is not generalised from a single
sample; the other three are the engine-drift control (§5). NYISO's `920c8b8bc1b1` is the same
hash nyiso-149's own commit message cites ("hash 920c8b8bc1b1 at both ends") — an independent
cross-check that the harness is measuring what it claims.

Method note: `rebuild_benchmark` writes the shared inputs and re-points `meta.json` *before* its
tail call to `report_run`, which needs the gitignored `system.parquet` and therefore raises. The
raise is after the measurement and does not affect it. Every run was on a
`_benchcheck_<ISO>` copy; the committed bundles were never mutated, and the scratch copies plus
the regenerated `_shared/` store were deleted afterwards.

**Leg 2: the benchmark inputs the parts were built from are exactly what HEAD produces.**

---

## 4. VERDICT and the costed recommendation

### Verdict: UNLABELLED-BUT-CORRECT

Builder unchanged for these ISOs (§2) **and** inputs reproduce byte-identically (§3). The 11
parts carry no fingerprint because the stamp did not exist when they were written — nothing more.

**No keeper re-verification is required. No C1 verdict is in doubt.** PJM and NEISO stay
`CALIBRATED`; CAISO stays `NOT-YET` for reasons that have nothing to do with this.

Residual, stated rather than buried: the CAISO part was written by caiso-197 (2026-08-16), whose
bundle has since been pruned by the top-15 retention, so §3's CAISO row is measured on caiso-200
(the keeper, 2026-08-17) rather than on the exact writing bundle. Every CAISO bundle still on
disk records the same three frame hashes, so the frame family is unchanged across that seam, but
caiso-197's own reference cannot be read back. This does not affect the PJM or NEISO rows, which
are the CALIBRATED ones.

### Recommendation: RE-STAMP the 11 parts. Do NOT regenerate.

**Re-stamping is mechanically available and was measured, not assumed.** Loading each committed
part and re-writing it through HEAD's `backcast_artifacts.write_bench_part` with its own meta:

```
parts where re-stamping changes NOTHING but the fingerprint: 20/20
```

All 20 committed parts, both cohorts: payload identical under canonical comparison, and the
**only** differing meta key is `builderFingerprint`. Committed payload sha256 for the 11
affected parts (sha256 of `json.dumps(part["bench"])`, the decompressed payload — gzip envelopes
excluded, since gzip embeds a timestamp):

| part | payload sha256 |
|---|---|
| CAISO/2023 | `710c426b44440fc607e2d1c1e3f179459bb1ea74f2f8703d884e1ea8611ae215` |
| CAISO/2024 | `01f8282df49d4cafa11327922271610f9387ef91671062697208d49ba68cfbc8` |
| CAISO/2025 | `47efc8cdba47420783f044b9da936b24845c20c06290e2ce1b1203801ef4e08c` |
| NEISO/2022 | `00eed91ccb70f1758e67467a55540aa83e2db44515694f07f0ad0348a6708bf2` |
| NEISO/2023 | `26c6b571c2e8bb5213615e9f1e656f72e6d655eb0c8914fde6ebced9b940cf20` |
| NEISO/2024 | `34b79dc28f258d559f74cfd7232e7d06c3c25461c52a18a892af59c05099d3cf` |
| NEISO/2025 | `ab63047cc09db0955e771d5d92041ea3a747a6b2780dda24ea3ef26556d4271a` |
| PJM/2022 | `e612bd46031fc91d8eecde1ea2b72c4fa1bf1aa9f9e199ee30d2b146bd0bfd7c` |
| PJM/2023 | `49f9dc08f343e88d75efd89fb48fcb882f854163d0ac48d8612da129d2b6921e` |
| PJM/2024 | `5d0e2b6d0b7fd0583bead2d2bee109daafe3a5759faf7767d54ab8770efdcbca` |
| PJM/2025 | `7ccfc46a900b488620c412a1d07f01818b437039f23e17f56fd694a89c21d3e7` |

**Cost comparison.**

| option | cost | what it buys |
|---|---|---|
| **Re-stamp** (recommended) | minutes; one small commit; no solve, no bundle regen, no keeper re-verification | the label the parts should already carry |
| Regenerate (the check's own remedy text) | 11 parts × 3 ISOs of `--rebuild-benchmark` **plus** a full LP re-solve per bundle (the dispatch parquets are gitignored — §3), then `dashboard_add_run.py`, then re-verification of two CALIBRATED keepers | nothing measurable: §3 says the inputs are byte-identical, so a faithful regeneration reproduces the same payload |

Regeneration here would be a five-ISO-scale spend against a signal that has now been measured
down to zero. That is the exact shape of this program's costliest recorded error — a benchmark
drift attributed on circumstantial evidence and refuted by one content-addressed hash — and it
is the reason this session took the hash first.

**Not done here, deliberately.** Re-stamping rewrites 11 committed artifacts that keepers score
against. Even though the payload provably does not move, that is an owner call, and this session
was scoped to the measurement. If the owner rules yes, the mechanism is `write_bench_part` with
each part's own loaded `meta`/`bench` — no new machinery, no new parameter.

A second, cheaper option the owner may prefer instead: **teach `check_bench_freshness.py` to
distinguish absent from mismatched.** An absent fingerprint is "unlabelled"; a *differing* one is
"provably written by another builder". Today they collapse into one HARD failure, which is what
made an 11-part non-event read like a determination-integrity event. That change costs one
branch and leaves every artifact untouched — but it is a gate-semantics change and is likewise
the owner's to authorise.

---

## 5. The engine-drift signal (9 parts) — reported, not acted on

`check_bench_freshness.py` reports these SOFT and never gates them: ERCOT 2023–2025 (9 commits
under `src/market_sim/data/` + `src/market_sim/config/` since 2026-08-24), MISO and NYISO
2023–2025 (11 commits since 2026-08-23; the prompt's "16" is the count over a wider window).

**The commits, and whether they could plausibly matter.** The builder imports the engine for the
plant→class map, the CHP shares and the EIA-923 reconciliation. Screened against that:

| commit | date | plausibly reaches a bench part? |
|---|---|---|
| `de53728` thermal-tranche arm-over-gap guard at the `bins_to_fleet` seam | 08-25 | **Yes in principle** — fleet/bin seam, and the non-ERCOT plant→class map is built from the per-plant EIA-860 fleet |
| `0001cca` miso-186 `unit_outage_fleet_status_scope` | 08-25 | Yes in principle — scopes CAMPD unit-outage events to the fleet |
| `dc84600` ercot-234 EASTEX zone crosswalk repair | 08-25 | Yes in principle — ERCOT zone assignment |
| `e8a3150` ercot-231 leap-year fix, tie-zone by-neighbor slice | 08-24 | Yes in principle — touches an hourly slice |
| `604e599` miso-183 MISO regional hourly load/generation intake | 08-24 | Additive intake |
| `a6ed2bf` `entry_forward_expectation_signal`, `d8a3c90` ercot-236 SWCAP clip (default-off), `a92c1f5` CAISO AS-revenue registry row, `682826d` capx-d2 NYISO tie-firm MW | 08-25 | Forecast/entry/adequacy surfaces — no bench-side path |

That screen is a *plausibility* read and would normally leave the question open. It does not have
to, because **§3 already answers it empirically for exactly these three ISOs**: ERCOT, MISO and
NYISO each reproduce all three benchmark frames byte-identically at HEAD, on their current
keeper bundles, *after* every one of those commits landed. Whatever those commits changed, they
did not move a metered actual. **The engine-drift signal closes clean, and it closes on a
measurement rather than on the code read.**

**Marginality, for completeness** (headroom = band − |model − actual|, computed from the
committed status parts; a C1 record needs BOTH the TWh and the share leg):

| ISO | determination | tightest C1 TWh row | headroom | tightest share row |
|---|---|---|---|---|
| **ERCOT** | **CALIBRATED** | 2023 CC_REGULAR, ǀΔǀ 3.018 vs ±8.00 | **4.98 TWh (62 % of band)** | 0.64 pp of ±3.0 |
| MISO | NOT-YET | 2024 CC_REGULAR, ǀΔǀ 8.037 vs ±8.00 | **−0.037 TWh (already FAIL, 0.5 % over)** | 1.66 pp of ±3.0 |
| MISO | " | 2024 ST_GAS, ǀΔǀ 7.679 vs ±8.00 | **+0.321 TWh (4.0 % of band) — MARGINAL** | 1.19 pp |
| NYISO | NOT-YET | 2024 CC_REGULAR, ǀΔǀ 2.711 vs ±3.98 | +1.27 TWh (32 %) | **2.64 pp of ±3.0 — 0.36 pp margin, MARGINAL on the share leg** |

**No CALIBRATED ISO is marginal.** ERCOT — the only CALIBRATED ISO in the drift set — has 62 % of
band on its tightest row; nothing a benchmark nudge could do would flip its C1. The two marginal
rows are both in ISOs already reading NOT-YET, so a move there cannot change a determination,
only the composition of an existing fail set. Combined with the §3 result that their frames
reproduce byte-identically, **this closes cheaply: nothing to regenerate.**

For symmetry, the affected-cohort ISOs: PJM's tightest C1 row has 4.55 TWh / 57 % of band; NEISO's
has 2.61 TWh / 89 %; CAISO's has 1.03 TWh / 19.5 % (NOT-YET). The two CALIBRATED ISOs whose parts
are unlabelled are not near a C1 edge either.

---

## 6. The separable half — status staleness (problem i), CLEARED

`audit_keepers.py` check S1 gates on `build_status.py --check`'s exit code alone; the
`[!] STALE BENCHMARK` lines that share its output are printed by `calibration_verdict` and have
never affected it. So S1's failure was **entirely** problem (i).

`python scripts/build_status.py` rebuilt all six parts. Verified leaf-by-leaf against a
pre-rebuild snapshot — **it is a re-render, not a re-adjudication**:

* **Changed, in PJM / CAISO / NEISO only:** `rubric_version` 3.4 → 3.5, and the addition of the
  `reported` block (C5a `co2`, REPORTED-ONLY since rubric v2.9 — contributes no status, no caveat
  budget and no reason line). Plus `generated` in all six.
* **Byte-identical in all six:** `determination`, `run_id`, keeper `label`, `caveats` (ledgered /
  protective / commercial_band / budget), `grade_summary`, `frontier`, `free_class_score`,
  `holdout_touchpoint`, `data_blocked_years`, `notes`, `reasons`, `scorable_years`,
  `target_years`, `ledger_entries`, `statmode_d7`, and every criterion record status.

No determination moved. ERCOT / PJM / NEISO stay `CALIBRATED`; CAISO / NYISO / MISO stay
`NOT-YET`. `build_status.py --check` → **6/6 in sync**; `audit_keepers.py` → **PASS, 0 failures,
0 warnings**.

Committed separately in `aa2ff61`, ahead of the measurement, per the push-first instruction.

---

## 7. State left, and what was NOT touched

* **Problem (i): CLOSED.** `audit_keepers.py` is green.
* **Problem (ii): OPEN pending the owner.** `check_bench_freshness.py` still exits 1 on the 11
  unstamped parts. It is **not** wired into CI as a hard gate (nyiso-148 deliberately left it
  off: "Nineteen of twenty committed parts are stale, so gating now would red-light every PR"),
  so nothing is blocked by leaving it open. The measurement says the parts are correct; the
  remedy — re-stamp, or split absent-vs-mismatched in the checker — is the owner's ruling.
* **Not touched, as instructed:** no `keepers/<ISO>.json`, no `calibration-complete.json`, no
  `holdout-freeze.json` (freeze is ACTIVE and was never approached), no dashboard registration,
  no mechanism-matrix cell (no mechanism was tested — rule 26), no bench part, no bundle, no
  `.github/workflows/`. No holdout year was solved, scored or registered — every measurement
  read committed artifacts and `data/raw` only (rule 22).
* **Environment note for the next lane:** this container had **no Python scientific stack
  installed** — `numpy` was absent, so any script importing the engine fails immediately.
  Installed from `requirements.txt` (plus `pytest`) to run the measurements. Worth knowing before
  concluding a tool is broken.

## 8. Reproduction

```
# Leg 2 — benchmark-input reproduction at HEAD, one ISO (runs on a COPY):
#   copy results/calibration/<keeper_bundle> to results/calibration/_benchcheck_<ISO>
#   from scripts.run_calibration_full import rebuild_benchmark; rebuild_benchmark(<copy>)
#   (the tail report_run() raises on the gitignored system.parquet — after the measurement)
#   compare meta.json["shared_inputs"] before vs after: the <sha8> IS the content hash
#
# Re-stamp feasibility — all 20 parts:
#   ba.write_bench_part(tmp, iso, year, part["meta"] minus "years", part["bench"])
#   assert the only differing meta key is "builderFingerprint"
#
# Contract pins at HEAD:
python -m pytest tests/regression/test_btm_bench_basis_pin.py \
                 tests/scoring/test_backcast_artifacts.py -q     # 20 passed
```
