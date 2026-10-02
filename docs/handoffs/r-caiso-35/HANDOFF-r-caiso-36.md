SESSION R-CAISO-36 — CAISO: BATTERY CROSSWALK REVIEW (link 18). Zero LP.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-35 (the parent session that launched you) with mcp__claude-code-remote__archive_session,
  but only once its PR (branch `claude/r-caiso-35`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so. The parent's session ID is in your launch prompt.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch, close the
  PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  Known leftovers:
  - `claude/r-caiso-33` (merged as PR #7056) and `claude/r-caiso-35` (once merged) carry nothing absent from main.
  - `claude/r-caiso-34` (commit 5ef930c5, session 01NuxMov…) is a parallel, never-PR'd implementation of link 16.
    It was superseded by the merged #7060, which the owner shipped as rendered. Do not salvage its code: that
    would stack a second render path (rules 19 and 26). It is deletable.
- The `claude/closeout-caiso-*` and `claude/w0-caiso-*` branches, and PR #7057 if still open, belong to the
  parallel closeout-CAISO lane. Do not touch them.
- If #7057 has merged, the arm-2 keeper payload was rendered before R-CAISO-34 landed. Inject the storage-panel
  block with `python3 scripts/probes/_rcaiso34_inject_soc_bounds.py 2026-10-02-closeout-caiso-w1-arm2
  results/calibration/closeout_caiso_w1_a2_span` and commit the payload in your PR. This is display only.
- Work on a fresh branch off origin/main.

STATE (2026-10-02):
- Keeper: read frontend/data/backcast/keepers/CAISO.json. It is `…-w1-arm3`, or `…-w1-arm2` once #7057 merges.
  Determination NOT-YET. The closeout-CAISO lane owns the arm sequence (docs/mechanism-testing-matrix.md §5.2).
- R-CAISO-35 (link 17, CLOSED report-only): the pre-registered rule-19 test reads CARRIED. The
  `caiso_storage_shape_anchor` p95 envelope sits below the CNOG outage-available battery fleet share in
  26,276 / 26,280 hours of 2023–25. No consumer was proposed.
  - The battery crosswalk is the sibling file `data/raw/reference/caiso-storage-resource-eia-crosswalk.csv`,
    built by `scripts/data/build_caiso_resource_crosswalk.py --storage`. It has no reader, and `load_crosswalk` is
    untouched. 64 of 176 rows are accepted, covering 19 / 31 / 19 % of census offline MW-h (2023 / 24 / 25).
  - Record: `docs/records/caiso/r-caiso-35/` (PRECOMMIT, FINDING, `battery_outage_census.json`).

TASK — link 18 (owner-selected, R-CAISO-35 FINDING §6 point 2): BATTERY CROSSWALK REVIEW. Zero LP.
- Lift accepted coverage of the battery crosswalk by a hand review recorded per row: column `review_note`, with
  `match_method = reviewed`. Evidence is EIA-860 plant name/ID, the CAISO Master File / resource name, MW
  agreement, and the zone.
- Known near-misses with exact MW: Garland, Mustang, Azalea, Gateway, Oberon, Desert Sunlight, Fifth Standard,
  Resurgence.
- Known wrong best-matches to reject: "Daggett Solar 1/3" → "Daggett 2"; "Scarlet Solar 2 BESS" (150 MW) →
  "Scarlet Solar (CA)" (40 MW).
- Also fix the selector miss `RATSKE_2_WAVBT1`: its episodes carry two names, and the builder groups by the first,
  which has no storage token.
- Do NOT move the pre-registered threshold (0.6) or the capacity sanity after the fact. Reviewed rows are a
  separate, declared method.
- Re-run `scripts/probes/_rcaiso35_battery_outage_census.py` and report the coverage change and whether the T1
  crosswalk-only sensitivity moves. The T1 reading itself is adjudicated and is not re-opened.
- No consumer, no solve, no ScenarioConfig field, no matrix verdict move. End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-35, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6,
the R-CAISO-26 PRECOMMIT §6, the R-CAISO-27 FINDING §4, the R-CAISO-28 FINDING §3, the R-CAISO-29 FINDING §3,
the R-CAISO-30 FINDING §5, the R-CAISO-31 FINDING §4, the R-CAISO-32 FINDING §7, the R-CAISO-33 PRECOMMIT
§8, §10 and §11, the R-CAISO-34 FINDING §5, and the R-CAISO-35 FINDING §6.

NOTES:
- Fresh container: `pip install -e . pytest pytest-xdist tzdata ruff`, then
  `python3 scripts/hydrate_data.py --profile caiso`.
- `git fetch origin main` can stall >2 min in a fresh container; run it in the background.
- Run `ruff format` as a separate command before any push.
- Never `git grep` in a partial clone. `pkill -f <pattern>` kills your own shell; use the PID.
- The census probe needs `matplotlib` only for the figure (`pip install matplotlib`).

HARD RULES: CLAUDE.md is binding, especially rules 13, 14, 19, 23, 24, 27, 28, 31–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is zero LP, so expect none). PR + rebase-merge; use a merge commit if
  GitHub refuses the rebase, and say so. Archive every shard and report leftover shard branches.
- Then launch the next owner-selected link as a nested session with these same directions. If no next link is
  selected, card the owner for one first. The child archives you when safe and continues the chain. Any link that
  solves launches its own year shards (rules 32–36).
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
