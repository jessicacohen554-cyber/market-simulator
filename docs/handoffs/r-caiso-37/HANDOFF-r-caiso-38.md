SESSION R-CAISO-38 — CAISO: PRE-COD BASIS NOTE FOR THE BATTERY OUTAGE CENSUS (link 20). Zero LP.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-37, the parent session that launched you, with mcp__claude-code-remote__archive_session. Do this
  only once its PR (branch `claude/r-caiso-37`) reads MERGED on the GitHub MCP (a rebase merge can show
  `merged: false` with a `merged_at` stamp; `merged_at` set and the commit on main is merged). If it has not merged,
  do not archive, and say so. The parent's session ID is in your launch prompt.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch, close the PRs
  you salvaged, and report which branches the owner can delete. Deleting a ref returns 403, so do not try. Known
  leftovers:
  - `claude/r-caiso-36` and `claude/r-caiso-37` (once merged) carry nothing absent from main.
  - `claude/r-caiso-34` (5ef930c5) is a superseded parallel link-16 build. Do not salvage it (rules 19 and 26); it is
    deletable.
- The `claude/closeout-caiso-*` and `claude/w0-caiso-*` branches, and the keeper's arm sequence
  (docs/mechanism-testing-matrix.md §5.2), belong to the parallel closeout-CAISO lane. Do not touch them.
- Work on a fresh branch off origin/main.

STATE (2026-10-02):
- Keeper: read frontend/data/backcast/keepers/CAISO.json. Determination NOT-YET. The closeout-CAISO lane owns it.
- R-CAISO-37 (link 19) closed report-only. Record: `docs/records/caiso/r-caiso-37/`.
  - EIA-860M (August 2026, operating sheet) is now a declared second source of the battery crosswalk review (ledger
    column `source = eia860m`, `match_method = reviewed_eia860m`). It covers only CAISO-zone batteries that the annual
    Final lacks.
  - 176 of 233 rows are accepted, covering 79.6 / 81.7 / 90.0 % of offline MW-h. T1 crosswalk-only reads 1 h
    (0.011 %). T1 primary is 0.548 %, CARRIED, and it is not re-opened.
- **The observation behind this link (R-CAISO-37 FINDING §0 point 4):**
  - All 7 resources matched from 860M carry 2025 CNOG outage episodes before their EIA COD (2026-03 to 2026-07).
  - The census numerator (offline MW from `caiso-dam-outage-windows.parquet`) includes them. The denominator
    (`derive_caiso_storage_shape.monthly_battery_fleet_mw`, annual EIA-860 by COD) does not.
  - In 2025 they hold 142 of 3,102 MW mean offline, about 1.07 pp of the 23.8 % `o_860`. The bias is conservative
    (it can only add T1 hours).

TASK (owner-selected, R-CAISO-37 FINDING §6 point 2): a pre-COD basis note. Zero LP, report-only.
- Measure the numerator/denominator mismatch across the WHOLE census, for every hour of 2023–2025.
  - Find the offline MW of resources whose plant is not in the denominator fleet at that hour. That covers two
    cases: an accepted crosswalk plant whose EIA COD (annual schedule, or 860M for `reviewed_eia860m` rows) is
    after the hour, and unaccepted resources.
  - Report each case separately, so the unknown-identity share is not mislabeled as pre-COD.
- Report the effect on `o_860` (mean / p99 / max) and on T1 primary and T2, with the pre-COD MW removed from the
  numerator. Present this as a sensitivity beside the adjudicated reading, never as a replacement for it.
  - T1 is not re-opened. The pre-registered bands (R-CAISO-35 PRECOMMIT §4) apply as written.
  - Write a short PRECOMMIT naming the measure before computing it.
- Use the existing probe (`scripts/probes/_rcaiso35_battery_outage_census.py`). Add a flag or a sibling probe, and
  leave the default output byte-identical. Do not edit the envelope, its derive script or the crosswalk thresholds.
- No consumer, no solve, no ScenarioConfig field, no matrix verdict move (evidence only on
  `storage_measured_anchors`, CAISO K). End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): every ruling cited in HANDOFF-r-caiso-37, R-CAISO-36 FINDING §6 and
R-CAISO-37 FINDING §6. In particular:
- the R-CAISO-32 erratum was NOT selected; its record stays as merged;
- the T2 basis study was NOT selected at links 18 and 19.

NOTES:
- Fresh container: `pip install -e . pytest pytest-xdist tzdata ruff matplotlib`, then
  `python3 scripts/hydrate_data.py --profile caiso`. The clone may be full, in which case the hydrate is a no-op.
- `git fetch origin main` can stall for more than 2 minutes in a fresh container; run it in the background.
- Run `ruff format` as a separate command before any push.
- Never `git grep` in a partial clone. `pkill -f <pattern>` kills your own shell; use the PID.

HARD RULES: CLAUDE.md is binding, especially rules 13, 14, 19, 23, 24, 27, 28, 31–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not exclusive),
never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is zero LP, so expect none). Open a PR and rebase-merge it; use a merge
  commit if GitHub refuses the rebase, and say so. Archive every shard and report leftover shard branches.
- Then launch the next owner-selected link as a nested session with these same directions. If no next link is
  selected, card the owner for one first. The child archives you when safe and continues the chain. Any link that
  solves launches its own year shards (rules 32–36).
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
