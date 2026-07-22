# Holdout backcast readiness (PJM/NEISO/MISO) — recovery note, 2026-07-22

## TL;DR
The 2026-07-21 session's work was **lost** (3 commits + a portable patch committed
locally only, never pushed; the ephemeral container was reclaimed). This session,
on a fresh clone of `main`:

1. **Reconstructed + landed** the one rule-22-neutral piece — the EIA-930
   **demand-spike screen** — after discovering it had to be **re-targeted** (the
   original patch aimed at the pre-split `eia_loader.py` monolith; `main` split
   that module into the `eia930/` package on 2026-07-20). It now lives in
   `src/market_sim/data/eia930/demand.py`, **byte-verified on the branch**
   (blob `5aa5de93…`, commit `cea5417`).
2. **Logged the owner's re-authorization** of the PJM/MISO out-of-training data
   intake (lost with the 2026-07-21 commits) into `calibration-complete.json`'s
   `intake_log` (2026-07-22 entry, byte-verified).

## What is landed (branch `claude/holdout-backcast-readiness-x8jf60`)
`_screen_demand_spikes` in `eia930/demand.py`, wired into
`_load_{pjm,miso,neiso}_hourly_demand`. Hours above 2.5× the annual median are
metering artifacts (sentinels, 2^31 integer overflow) in the raw EIA-930 wide
extracts; dropped and linearly interpolated (the loaders' existing missing-hour
repair). Verified in-session:
- **Byte-identical no-op on every 2023–2025 training year** for PJM/MISO/NEISO
  (peak-to-median ratio ≈ 1.7× < 2.5×) → keeper-neutral (rule 22).
- Repairs out-of-sample PJM 2019 (417,669 MW → 155,276), 2020 (5 hrs → 192 GW),
  2021 (2^31 → 149,590).
- `ruff format`/`ruff check` clean; diff vs the exact remote base is only the
  screen + 3 call sites; pushed blob == local blob (rule-27 verified).

A data-quality bug fix, not an out-of-training intake/solve — not gated by the
quarantine.

## Landing mechanics (why this was hard, for the next session)
- **`git push`/`git fetch` hang** — the local clone is **shallow AND stale**
  (its `main`, `066fb98`, predates current `main`, `4ff3118`, incl. the
  2026-07-20 `eia930` split), so pack transfer over the git relay never
  completes. Ref ops (`ls-remote`) work; pack transfer does not.
- **REST *write* via curl is blocked** by the proxy ("Write access … not
  permitted"); **reads** (GET raw contents) work and were used to pull the exact
  remote base bytes (blob-verified) for local editing.
- **`push_files` (MCP) is the only write path.** For files ≥300 lines this means
  reproducing full content inline (the rule-27 risk), mitigated by fetching the
  exact base first (so only the surgical diff is authored) and **verifying the
  pushed blob hash equals the local `git hash-object`** after every push. Every
  push this session verified byte-identical.
- The earlier `docs/handoffs/holdout-demand-spike-screen-2026-07-22.patch`
  targeted the pre-split monolith and was **removed as stale** — the change is
  now landed directly in `eia930/demand.py`.

## Owner re-authorization (2026-07-22) — intake now permitted, solve still not
Owner instruction "land the patch then and I re authorize" is logged verbatim in
`frontend/data/backcast/calibration-complete.json` `intake_log` (2026-07-22).
Scope: **PJM/MISO out-of-training holdout DATA READINESS only** (2022 validation;
2019/H1-2026 locked as data lands). **No solve/score/register** — neither PJM nor
MISO has a `complete` marker, so the CI quarantine gates and the G-19 one-shot
HOLD stay in force. Intaken data is validated no-LP only.

## Next steps (now unblocked for DATA only)
1. **PJM/MISO 2022 emission-rate v2 rows** (the 2022 gap year). Blocked on the
   intake tools still requiring a **calibration-complete marker**, not just an
   `intake_log` entry — the 2026-07-21 gate-loosening (`_intake_authorized_isos`
   in `curate_emissions_unit_annual.py` / `derive_plant_emissions_v2.py`,
   accept a logged authorization) was lost and must be re-applied first. Then:
   `python -m scripts.curate_emissions_unit_annual --years 2022 --holdout-intake PJM`
   → `derive_plant_emissions_v2 --iso PJM --years 2022 --holdout-intake PJM`
   (and again for MISO). Writes `data/clean/` (gitignored) +
   `plant_emission_rates_v2.parquet` (committed binary — needs a non-`push_files`
   lander, since the API can't carry binary).
2. **`scripts/build_demand_profile_from_raw.py`** (new builder) — reconstructable
   on demand; materializes out-of-training CLEAN demand partitions.
3. **LMP bench** — PARKED per owner (PJM DataMiner-2 export; MISO 2022 truncated
   raw + `MISO_PRICING_API_KEY` unset; NEISO 2019 SMD workbook).

## Carried-forward open items
- **MISO 2022 outage windows:** absent (2023–25 only); deriving needs the
  detector-vintage adjudication (rule 23, keeper-adjacent). Not run.
- **PJM 2020 demand residual:** 2 isolated sub-2.5× spike hours (176/192 GW)
  survive the ISO-agnostic screen (repaired max 192,229 MW). Needs a per-ISO /
  local-outlier screen *if 2020 becomes a target*. Actual targets (2019/2022)
  are clean.
- **Markers:** no PJM/MISO calibration-complete marker → no 2019/2022 solve
  authorized regardless of data readiness.
