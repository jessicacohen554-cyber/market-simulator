# PRECHECK — caiso-188: the published-MIC seam limit vs the fitted 7,500 MW scalar

**Written BEFORE the solve. No scored criterion has been read for either arm.**
The gates below are pre-registered in the rule-1 `[R-STRUCT]` sense: the arm is
built because a fitted scalar is measured to be binding and is falsified by the
measured record, **not** because of anything it does to a residual. C3a is a
live FAIL on this ISO and is reported, never targeted (rule 1 / rule 13
`[R-MEASURED]`).

## 1. The object, measured pre-solve (no LP)

`scripts/probes/_caiso188_import_tranche_census.py` +
`_caiso188_seam_cap_forensics.py`, on committed bytes only:

* The keeper `2026-08-09-caiso-184-c1-lpbasis` carries
  `capacity_deliverability_limits = True` in its `run_config.json`, whose
  backcast half (Part A) is supposed to **replace** the baked
  `WECC_import_simultaneous` cap (**7,500 MW — a scalar `iso_configs.py` itself
  labels "a fitted scalar" and the DOF ledger carries as a residual row**) with
  the published branch-group **Maximum Import Capability** sum
  (**16,055 / 16,452 / 16,148 MW** for 2023/24/25).
* **It did not.** The keeper's own committed `hourly/class_hourly_<year>.parquet`
  pins total net import at **exactly 7,500.0 MW in 764 / 477 / 809 hours**
  (8.7 / 5.4 / 9.2 % of the year), never exceeds it, and every single pinned
  hour is one where the two corridors' measured p95 envelopes would have
  allowed more (envelope sum ≥ 7,511 MW in the tightest pinned hour).
* Part A resolves the MIC through a **gitignored, non-auto-built clean
  partition** (`data/clean/capacity-deliverability/`). Absent, it logs a warning
  and **silently no-ops while `run_config.json` still records the flag as True**.
* Onset is dated in the committed bundles: caiso-124 … caiso-174 carry import
  maxima of 9,169–11,625 MW (MIC in force); **every bundle from caiso-175
  (2026-08-06) onward — 175, 180, 183, 184 c0/c1 — maxes at exactly 7,500.0 MW**
  with 456–905 pinned hours.
* Rule 14 `[R-ACCURATE]` falsification of the fitted bound, from the same
  EIA-930 bytes the corridor envelopes are built from: the **real** CAISO system
  carried more than 7,500 MW of total net import in **271 / 293 / 681 hours**,
  reaching **13,136 / 13,312 / 15,080 MW**. The published MIC envelopes those
  maxima; the fitted 7,500 does not. This is the `retire_misattributed_sil`
  (nyiso-100) pattern exactly.

## 2. The arms

Both at HEAD, same container, same data, single delta, full span (rule 16), years
sequential (rule 12):

| arm | bundle | delta |
|---|---|---|
| **A (control)** | `caiso188_d0_control` | keeper recipe, `capacity_deliverability_limits=false` — i.e. the LP the keeper actually solved (7,500 MW baked cap) |
| **B (arm)** | `caiso188_d1_micseam` | keeper recipe, `capacity_deliverability_limits=true` **with the clean partition materialised** — the published MIC seam limit in force |

Driver: `scripts/replay_keeper.py <keeper> --out-dir <arm> --set …` (the
single-delta A/B channel; `prb_overrides` applies last, so the `--set` value
governs).

## 3. Pre-registered gates

* **G-SEAM — plumbing, MUST PASS, else the A/B measured nothing.** Arm B logs
  `seam import cap set to 16055 / 16452 / 16148 MW` for the three years and its
  total net import exceeds 7,500 MW in ≥ 1 hour of every year. Arm A's total net
  import maxes at exactly 7,500.0 MW.
* **G-CTRL — control fidelity, REPORTED not gating.** Arm A vs the committed
  keeper: max |Δ| per class-hour and per scored metric. The keeper solved at
  `03914d8`; HEAD carries 22 changed `src/` files since, so a non-zero drift is
  possible and is **disclosed**, never absorbed.
* **G-IMPORT — structural, REPORTED.** In the hours arm A is pinned at 7,500,
  arm B's total net import against the **measured** EIA-930 total for the same
  hours. `FINDING-caiso133` §5 refused relaxing the *measured corridor envelope*
  because the model already over-imports it by ~2 GW; that refusal stands and
  is untouched here — this arm relaxes a *different*, **fitted**, falsified
  limit while every measured corridor envelope stays in force and keeps binding.
  If arm B moves further from measured flow in those hours it is **published as
  a cost of the repair**, and the residual becomes a named root-cause issue
  (rule 14's own instruction), not a reason to restore the fitted scalar.
* **G-RUBRIC — REPORTED, NEVER A TARGET.** Full v3.1 re-score of arm B, all
  criteria, all three years, whatever it says. **C3a cannot accept or reject
  this repair in either direction** (rule 1 `[R-STRUCT]`, rule 13
  `[R-MEASURED]`): an improvement is not the reason to keep it and a
  degradation is not a reason to revert it.
* **G-LOYO — promotion pre-condition.** If arm B's determination differs from
  arm A's in any year, the change is scored leave-one-year-out within 2023–2025
  before any promotion is *proposed*. **This session proposes no promotion**:
  CAISO's `complete` marker is withdrawn, the owner sitting is prepared and
  pending, and no declaration file is touched.
* **Quarantine.** 2023–2025 only. No out-of-training year is solved, scored or
  registered (rule 22).

## 4. What each outcome means, stated in advance

* **G-SEAM passes and the arm changes dispatch** → the fitted 7,500 was binding,
  the keeper's declared mechanism was inert, and the DOF ledger row
  `WECC_import_simultaneous.cap_mw` must be rewritten from "superseded on the
  binding path / forecast-path residual only" to **LIVE and binding**. The
  repair is kept on rule 14 regardless of the rubric line.
* **G-SEAM passes and the arm is inert** → the pin was reachable but never
  economic; the ledger row still needs the correction (the mechanism was inert
  for a different reason than the ledger claims), and no keeper question arises.
* **G-SEAM fails** → the 7,500 attribution is wrong; the finding is withdrawn
  in full and the session reports the census alone.
