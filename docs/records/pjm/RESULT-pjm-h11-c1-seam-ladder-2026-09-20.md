# RESULT — pjm-h11: C-1 (the 2020 seam ladder) measured, and a LARGER defect found behind it (2026-09-20)

**Session:** pjm-h11 · **Branch:** `claude/pjm-h11-calibration-tuning-mwod34` · **ZERO LP MINUTES
IN THE PARENT** (rule 32 `[R-SHARD]` (a)) — every solve ran in a per-year shard, one year per
container, which is rule 36 `[R-YEAR-ISOLATION]` (a).
**KEEPER PROMOTED 2026-09-20** on the owner ruling *"Promote anyway"*:
`2026-09-11-pjm-d4-4-gasoutage` → **`2026-09-19-pjm-h11-c1seam-span`** (CALIBRATED, 2023–2025, empty
determination basis, zero caveats), with `2026-09-19-pjm-h11-c1seam-touchpoint` (2020–2022) stamped
and folded to it under rule 30 `[R-TOUCHPOINT-FOLD]` (a). The outgoing keeper's three stores and its
touchpoint's were pruned in this same session per rule 35 `[R-PROMOTE]`. **§4 below is the question
as it was put to the owner and is left standing as written; §4b records the ruling and what was
executed.**
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-pjm-h11-2026-09-19.md` ·
**Measurements:** `docs/ADDENDUM-pjm-h11-the-2020-readout-2026-09-19.md` ·
**Infra finding:** `docs/FINDING-pjm-h11-the-pjm-oom-is-a-disk-ordering-bug-2026-09-19.md`

---

## 1. Headline

**C-1 works, is exactly as scoped as claimed, and is NOT the biggest thing this lane found.**

1. **C-1 armed and measured.** 2020 joins `PJM_SEAM_LADDER_BY_YEAR` — a rule 23 `[R-FROZEN-DERIVE]`
   re-derivation, **zero new parameters, zero `ScenarioConfig` fields**. 2020 now runs the keeper's
   own measured seam instead of the forecast gas-elastic track.
2. **Invariance is EXACT.** 2021–2025 arm-vs-control: `max|Δ| = 0.000000 TWh`, 0 classes moved, all
   five years. C-1 touches 2020 alone, confirmed through the solver.
3. **The ex-ante prediction held, and its mechanism landed to ~1 %.** The PRECOMMIT predicted the
   2020 export residual would worsen (direction **confirmed**, magnitude **under-predicted**), and
   predicted the price-gap driving it at **13.441 TWh** against a realized **13.282**.
4. **THE BIGGER FINDING: a committed input rebuild silently cost PJM 8.26 TWh on C1-2020's failing
   class.** The offer-midcurve table rebuild moves COAL_BIT **+16.90 → +25.16** with *no mechanism
   change at all*. That is larger than anything C-1 does, it is already latent in `main` for every
   PJM lane that re-solves, and it was invisible until a control was solved at HEAD.
5. **C-2 measured, refuting a prior finding.** The PJM seam shortfall is **~100 % export-side**.
   pjm-h10 §2.5's inferred "import-side excess" does not exist, and the "phantom imports displace
   CC_REGULAR" suspect is retired at the system boundary.
6. **The promotion question was put to the owner** (§4) because "is it an improvement" has three
   non-agreeing answers. **The owner ruled: promote** (§4b). Route 2 was executed — registered,
   promoted, and the drift named rather than absorbed.

## 2. What was measured

**2020, ARM − CONTROL** (the only year the arm can move): net export **40.391 → 28.344 TWh**
(measured 41.626), so the residual goes **−1.235 → −13.282**. CC_REGULAR **−3.975**, COAL_BIT
**−2.882**, CT_PEAKER −2.203, fossil total **−10.574**. Nuclear, wind, hydro, OTHER and biomass are
**identical to the milli-TWh** — the signature of a clean single-mechanism delta.

**Drift, per year, control vs committed keeper:** +1.580 / +1.236 / +0.211 / −0.008 / −0.000 /
−0.000 for 2020–2025. It **shrinks** with position inside a solve span where the rule-36 artifact
would **grow**, and 2024/2025 (the most warm-start-exposed years in the keeper) are exactly 0.000.
It matches the offer-midcurve rebuild's own pre-measured footprint instead. **So it is code drift,
and the rule-36 artifact is ≈0 for PJM on net export** — measured, not assumed.

**C1 on the rubric's own band** (`min(max(2 % load, 3 % gen), 8 TWh)`; the 8 TWh cap binds for PJM):

| | registered keeper | CONTROL @ HEAD | ARM @ HEAD |
|---|---|---|---|
| **COAL_BIT** (the only out-of-band class) | +16.90 FAIL | **+25.16 FAIL** | +22.27 FAIL |
| CC_REGULAR | +7.50 | +4.32 | **+0.35** |
| classes out of band | 1 | 1 | 1 |
| sum \|error\| | 48.2 | 52.37 | **47.05** |

**C-2, on a matched system-net-by-hour basis:** measured PJM gross import **0.000–0.603 TWh** across
six years; model **0.000–0.048**. The shortfall is entirely export-side, 9.0–12.3 TWh.

## 3. Gates

| gate | result |
|---|---|
| **G1** — existing entries byte-identical | **FAIL as written** (3 of 480 rungs, each +0.01), **PASS on intent** (0 of 240 shared rungs move when 2020 is added). The three are pre-existing hand-transcription truncations; they reproduce with no 2020 in the frame and are deliberately untouched (Q1). |
| **G2** — 2020 rungs monotone | PASS, all five seams |
| **G3** — no new field or scalar | PASS by construction |
| **G4** — pjm-160's own acceptance bar (added by this lane) | PASS: offline P9 volume error ≤ 0.04 TWh, duration RMSE 40–276 MW |
| **Invariance** (2021–2025) | **PASS, exact** |

## 4. THE PROMOTION QUESTION — open, with the numbers

The owner instructed "if it's an improvement, promote." **This lane did not self-promote**, because
the answer differs by comparison and one of them is a regression:

| comparison | verdict |
|---|---|
| ARM vs its own CONTROL (same code) | **improvement**, clearly — −5.32 TWh total error |
| ARM vs the REGISTERED keeper, total \|error\| | **marginal improvement** — 47.05 vs 48.2 |
| ARM vs the REGISTERED keeper, **on the failing class** | **REGRESSION** — +22.27 vs +16.90 |

Registering this arm would put a run on the dashboard whose **failing criterion reads worse than the
keeper it replaces**, for a cause C-1 did not create and only partly offsets. Rule 31 `[R-RETAIN]`
puts that decision with the owner rather than with a session's own reading of an ambiguous
instruction. **All twelve bundles are retained** (gitignored, full recovery shas in `.gitignore` and
in the ADDENDUM §0), so any of the three routes below costs zero re-solves:

1. **Promote anyway** — total error improves, structure improves, rules 14/23 are satisfied, and the
   COAL_BIT regression is pre-existing drift that lands whenever PJM next re-solves regardless.
2. **Promote and name the drift** (this lane's recommendation) — same registration, with the RESULT
   stating plainly that COAL_BIT +16.90 → +22.27 is the offer-midcurve rebuild and not C-1, so the
   next lane inherits a correct attribution and a named target.
3. **Hold C-1 and chase the drift first** — treat +8.26 TWh from a table rebuild as the larger
   defect and fix it before registering anything.

## 4b. THE RULING, AND WHAT WAS EXECUTED (2026-09-20)

**Owner, verbatim: "Promote anyway."** Route 2 of §4 — promote *and name the drift*. What that means
in practice, stated plainly so nobody later reads the dashboard as a clean win:

**PJM's only out-of-band C1 class now reads worse than the keeper it replaced** (+22.27 vs +16.90
TWh, summed over all six years). The owner promoted knowing that. The cause is a rebuilt committed
input, not C-1, and the attribution is measured rather than argued: a control solved at the **same
HEAD with no C-1** reads +25.16. On the scored training years taken individually, C1 passes 18/18
(14/14 free) — the +22.27 is a six-year sum, and it is the *holdout* years that carry it.

Executed in this session, in rule 35 `[R-PROMOTE]` order:

| step | result |
|---|---|
| Benchmark parquets rebuilt on both composed bundles (zero LP) | `--rebuild-benchmark`, shared-input frames regenerated |
| `calibration_attestation.json` written on both (C6) | carried forward from the outgoing keeper, `attested_by` / `note` / `delta_vs_incumbent` rewritten for this lane |
| `dashboard_add_run.py` × 2 | `2026-09-19-pjm-h11-c1seam-span` **CALIBRATED** · `2026-09-19-pjm-h11-c1seam-touchpoint` **NOT-YET** (same shape as the outgoing pair) |
| `stamp_touchpoint_holdout.py` | touchpoint folded to the keeper (rule 30(a)) |
| keeper shard + `build_status.py --iso PJM` | `[PJM:CALIBRATED]` |
| `calibration-complete.json` re-keyed + determination re-verified | D-5(b) / `audit_keepers` M1 |
| `audit_keepers.py --iso PJM` **before** the prune | E1 clean; E13 flagged the two superseded runs, which is the prune duty |
| `prune_iso_runs.py --iso PJM --force-uncite` | removed `2026-09-11-pjm-d4-4-gasoutage` (`pjm_d4_4_A`) and `2026-09-11-pjm-holdout-gasoutage-touchpoint` (`pjm_d4_4_TP`) — PJM only |
| `audit_keepers.py --iso PJM` after | **0 failures / 0 warnings** |
| mechanism matrix | PJM shard re-stamped; `reference_price_interface` cell updated — **stays K**, coverage moved, verdict did not |

**Year set did not shrink** (rule 35(c)): enumerated before the delete as {2020, 2021, 2022, 2023,
2024, 2025}; the incoming pair covers it exactly.

**One pre-existing parity RED is left alone and named:**
`results/calibration/caiso279_ablate_dswcouple_span` is tracked-and-unmapped on `origin/main` — a
CAISO-lane item, and rule 35(a) scopes a promoting lane to its own ISO. The twelve
`pjm_h11_{arm,ctl}_<year>` legs also show in that gate's unmapped list **locally only**; they are
gitignored, so CI stays green. That is the rule 31 `[R-RETAIN]` behaviour pjm-h8 corrected into the
rule on 2026-09-16, not a new defect — and none of them is deleted.

## 5. Open items for the owner

* **Q1 — three truncated ladder rungs.** 2023 Carolinas.import b2, 2024 Carolinas.export b2, 2025
  LGEE.import b3, each one cent below what the frozen formula produces, from hand transcription.
  They sit in the CALIBRATED training keeper's own scored years, so fixing them is a solve-affecting
  change with no data change to cite (rule 23). Untouched. Fix in a dedicated card, or accept as a
  documented transcription tolerance?
* **Q3 — the MER dual is UNGATED.** `model/lp/model.py::_marginal_emission_rate` has no
  `ScenarioConfig` field and runs a second HiGHS `run()` on every pass of every solve of every ISO,
  in the post-solve window where six of this lane's shards were OOM-killed. No shard can avoid it
  without a forbidden code edit.
* **Proposed rule 32 `[R-SHARD]` (c)(8) addendum** — for a heavy-hydration ISO, the shard prompt's
  first action must be `prepare_solve_container.py`, **before** hydration. The swapfile is sized
  `min(deficit, free_disk − 6 GiB)` at the moment it runs and is never grown, so provisioning it
  after hydration silently caps it several GiB short. Full record in the OOM finding.
* **The 192,229 MW artifact demand hour** (FINDING pjm-h10 §5.2) remains unarmed and needs its own
  charter.

## 6. Infrastructure findings (durable, beyond this lane)

* **The PJM shard OOM is a disk-ordering bug, not a memory bug.** MISO's fix is sound and already
  wired in; PJM defeated it by spending the disk the swapfile needs before the swapfile is sized.
  Measured demand ~18.3 GiB against a ceiling+swap of 18.4 — dying on a ~0.1 GiB margin. Fixed by a
  partial clone (`blob_limit_kb`) plus preflight-first: 11 of 12 relaunched shards then succeeded.
* **`replay_keeper.py` is rule-36 clean by construction** — it calls `solve_and_persist` directly
  and pins `MARKET_SIM_WARMSTART_XYEAR=0`, so both warm-start knobs were off in all twelve shards.
* **The SPP-48 directory-grain `.gitignore` trap bites `results/calibration/*/floors/`.** ARM 2022
  landed 15 files rather than 17 for exactly this reason. Neither missing file is
  registration-critical.
* **Branch deletion returns HTTP 403 here** and prints a misleading `Everything up-to-date`, exactly
  as rule 33(f)(5) documents. Stale shard branches were left in place and said so.

## 7. Ledger

**Armed:** one key in `PJM_SEAM_LADDER_BY_YEAR` (2020). **No `ScenarioConfig` field, no default
flipped, no scalar, no mechanism-matrix verdict moved** (the `reference_price_interface` cell stays
`K`; its coverage moved). **Two runs registered, the keeper promoted, PJM's superseded pair pruned**
— all per §4b, on the owner's ruling. Rule 31: the twelve per-year leg bundles are **retained**, not
deleted. All 24 shard sessions archived (rule 33(e)); none left alive.

*Superseded by §4b: this section originally read "no run registered, no keeper touched, no ISO
pruned", which was true when the lane stopped short of promoting and is no longer true.* The §1–§3
figures remain **parent-computed from committed class hourlies** — they predate any `metrics.json`,
because a single-year replay bundle carries none, and the C1 band is read from
`calibration_verdict.py` itself. The **scorer-emitted** verdicts now exist and are the registered
ones: CALIBRATED (training) and NOT-YET (touchpoint).
