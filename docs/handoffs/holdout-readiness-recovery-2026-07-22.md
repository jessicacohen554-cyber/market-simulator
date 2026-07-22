# Holdout backcast readiness (PJM/NEISO/MISO) — recovery note, 2026-07-22

## TL;DR
The 2026-07-21 session's work was **lost**: its 3 commits and its portable patch
were committed *locally only* and never pushed, and the ephemeral container was
reclaimed. This session's fresh container cloned `main` clean — none of that
work, nor the branch (`claude/holdout-backcast-data-check-ihyecp`), survives.
Confirmed by direct check: `git cat-file` finds none of `dc4a646`/`c881968`/
`a3548cb`; neither holdout branch exists on the remote; and the 2026-07-21
PJM/MISO intake authorization the prior handoff said was "logged verbatim in
`calibration-complete.json`" **is not in the `intake_log`** (it ends 2026-07-13,
NEISO/NYISO only). It was in the lost commits too.

Only one piece has been reconstructed **and tested** here, because it is the
sole item that is independently justified and needs **no** out-of-training
authorization: the **EIA-930 demand-spike screen**. It ships as an apply-ready
patch (below), pushed to the remote branch so it *survives* reclamation — the
flaw that lost the prior work.

## What is reconstructed + tested (this branch)
`_screen_demand_spikes` in `src/market_sim/data/eia_loader.py`, wired into
`_load_{pjm,miso,neiso}_hourly_demand`. Hours above 2.5× the annual median are
metering artifacts (sentinels, 2^31 integer overflow, unit slips) in the raw
EIA-930 wide extracts; they are dropped and linearly interpolated (the same
repair the loaders already apply to missing meter hours).

Verified in-session with the venv:
- **Byte-identical no-op on every 2023–2025 training year** for PJM/MISO/NEISO
  (max observed peak-to-median ratio ≈ 1.7×, well under 2.5×) → **keeper-neutral,
  rule 22**.
- Repairs out-of-sample PJM 2019 (417,669 MW → 155,276), 2020 (5 hrs → 192 GW),
  2021 (2,147,483,648 ≈ 2^31 → 149,590).

This is a **data-quality bug fix**, not an out-of-training intake/solve/score/
register — so it is not gated by the rule-22 quarantine. It is scope-safe to land
independently of any holdout authorization.

## The landing constraint (environment-level, same wall as 2026-07-21)
- **`git push` and `git fetch` hang** in this container (pack transfer is dead;
  `push`/`fetch` terminate at timeout). Only ref ops (`ls-remote`) and the GitHub
  API (`push_files`) work.
- **`push_files` cannot safely carry the 3271-line `eia_loader.py`**: it requires
  the full file content inline, which is the rule-27-forbidden "regenerated
  full-file content from the model's response" pattern (truncation risk — the
  incident rule 27 exists to prevent). New/small files are fine.

**Therefore the change ships as a patch**, not as a modified-file push. The diff
is tiny (55 insertions, 3 deletions) and `git apply`s the exact bytes:

```
git checkout -b <branch> origin/main
git apply docs/handoffs/holdout-demand-spike-screen-2026-07-22.patch
# then land from a working-git environment, or push_files from one
```
`docs/handoffs/holdout-demand-spike-screen-2026-07-22.patch` applies clean on
`origin/main` (verified; pushed blob is byte-identical to the local patch).
It reproduces commit `8a01814` on this branch.

## NOT reconstructed — needs explicit owner action first
Everything below depends on the **lost 2026-07-21 PJM/MISO intake
authorization**. Per CLAUDE.md rule 22, out-of-training (2022 validation, 2019
locked) data intake requires **explicit, session-logged owner authorization**,
and no PJM/MISO calibration-complete marker exists. That authorization must be
**re-established in a new session log** before any of this proceeds:

1. **PJM/MISO 2022 emission-rate v2 rows** — data intake; needs authorization +
   a re-logged `intake_log` entry. (Writes `data/clean/` (gitignored) +
   `plant_emission_rates_v2.parquet` under `PROCESSED_DIR`, committed binary.)
2. **`--holdout-intake` gate-loosening** (`_intake_authorized_isos`, accept a
   logged authorization as an alternative to the marker) — a **governance-gate
   relaxation**; wants explicit owner sign-off, and is inert until a real
   `intake_log` entry exists.
3. **`scripts/build_demand_profile_from_raw.py`** (new builder) — dormant infra;
   materializes out-of-training CLEAN demand partitions when run, so running it
   for 2019/2022 is gated the same way. Reconstructable on demand.

I did **not** fabricate the authorization log entry or produce any out-of-training
data — that would forge owner authorization (rule 22 / legitimacy rules).

## Carried-forward open items (unchanged from 2026-07-21 handoff)
- **LMP bench (PARKED per owner):** PJM 2022+2019 need a DataMiner-2 UI export;
  MISO 2022 raw on disk but truncated (DA→Dec 9, RT→Nov 11), tail+2019 need
  `MISO_PRICING_API_KEY` (unset); NEISO 2019 needs a 2019 ISO-NE SMD workbook.
- **MISO 2022 outage windows:** absent (2023–25 only). Deriving needs the
  detector-vintage adjudication (rule 23, keeper-adjacent). Not run.
- **PJM 2020 demand residual:** 2 isolated sub-2.5× spike hours (176/192 GW)
  survive the ISO-agnostic screen (repaired max 192,229 MW confirms this). Needs
  a per-ISO / local-outlier screen *if 2020 becomes a target*. All actual target
  years (2019/2022) are clean.
- **Markers:** no PJM/MISO calibration-complete marker → no 2019/2022 solve
  authorized regardless of data readiness.

## Recommended next step
Owner to decide the landing mechanism (apply the patch from a working-git
environment) and, separately, whether to **re-authorize** the PJM/MISO
out-of-training data intake in a fresh session log. Until re-authorized, the lane
stops at the (now-durable) demand-spike fix.
