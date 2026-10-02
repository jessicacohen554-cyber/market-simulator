SESSION R-CAISO-37 — CAISO: EIA-860M INTAKE FOR THE UNMATCHED BATTERY ROWS (link 19). Zero LP.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-36, the parent session that launched you, with mcp__claude-code-remote__archive_session. Do this
  only once its PR (branch `claude/r-caiso-36`) reads MERGED on the GitHub MCP. If it has not merged, do not archive,
  and say so. The parent's session ID is in your launch prompt.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch, close the PRs
  you salvaged, and report which branches the owner can delete. Deleting a ref returns 403, so do not try. Known
  leftovers:
  - `claude/r-caiso-35` and `claude/r-caiso-36` (once merged) carry nothing absent from main.
  - `claude/r-caiso-34` (5ef930c5) is a superseded parallel link-16 build. Do not salvage it (rules 19 and 26); it is
    deletable.
- The `claude/closeout-caiso-*` and `claude/w0-caiso-*` branches, and the keeper's arm sequence
  (docs/mechanism-testing-matrix.md §5.2), belong to the parallel closeout-CAISO lane. Do not touch them.
- Work on a fresh branch off origin/main.

STATE (2026-10-02):
- Keeper: read frontend/data/backcast/keepers/CAISO.json. Determination NOT-YET. The closeout-CAISO lane owns it.
- R-CAISO-36 (link 18) closed report-only. Record: `docs/records/caiso/r-caiso-36/`.
  - The battery crosswalk `data/raw/reference/caiso-storage-resource-eia-crosswalk.csv` has 233 rows, 168 accepted
    (83 name-token, 85 reviewed). It has no reader.
  - Accepted rows cover 78–85 % of CNOG battery offline MW-h.
  - The review ledger is `data/raw/reference/caiso-storage-crosswalk-review.csv`, applied by
    `scripts/data/build_caiso_resource_crosswalk.py --storage` (`apply_storage_review`).
  - The census selector bug is fixed in `is_battery_resource`. T1 still reads CARRIED (0.548 % ≤ 1 %), and it is not
    re-opened.
- **65 rows are unaccepted.** Each carries a review note. Most say "no operable EIA-860 unit in a CAISO zone", for
  example Dracker, Sol Catcher, Rosamond West, Tropico, Marvel, Nighthawk, Bateria del Sur 2, Aratina, Atlas 8A,
  Black Diamond, Hummingbird and Ventasso. Others are ambiguous (the EdSan / Edwards Sanborn family) or outside the
  CAISO zones (Vikings in IID, Yellow Pine II in NEVP, Townsite in WALC). Together they hold 15–22 % of offline MW-h.

TASK (owner-selected, R-CAISO-36 FINDING §6 point 2): an EIA-860M intake for the unmatched rows. Zero LP.
- EIA-860M is already on disk at `data/raw/eia-860m/` (August 2026 vintage; read its README first). Check whether
  its operating inventory, energy-storage technology rows in CA/NV/AZ, names the units the annual Final 2025 release
  lacks.
- For each match, add a reviewed ledger row with evidence: plant name/ID, generator IDs, MW agreement, county/BA and
  the CAISO node prefix. Then rebuild the crosswalk.
  - An accepted reviewed row must still resolve to a plant the builder can validate. Today that means the annual
    storage operable schedule in a CAISO zone.
  - If EIA-860M plants are not in that schedule, extend the review lookup to EIA-860M through the data contract.
  - That is a declared, separate source. Do not move the 0.6 threshold or the capacity sanity.
- Resolve the EdSan family only if EIA-860M generator IDs make it unambiguous.
- Re-run `scripts/probes/_rcaiso35_battery_outage_census.py --out docs/records/caiso/r-caiso-37/battery_outage_census.json`.
  Report the coverage change, split by `match_method`, and whether the T1 crosswalk-only sensitivity moves.
- No consumer, no solve, no ScenarioConfig field, no matrix verdict move. End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): every ruling cited in HANDOFF-r-caiso-36 plus the R-CAISO-36 FINDING §6.
In particular, the R-CAISO-32 erratum and the patch to its duplicated selector were NOT selected. Leave that record
as merged.

NOTES:
- Fresh container: `pip install -e . pytest pytest-xdist tzdata ruff matplotlib`, then
  `python3 scripts/hydrate_data.py --profile caiso`.
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
