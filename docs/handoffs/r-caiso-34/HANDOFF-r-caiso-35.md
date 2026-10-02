SESSION R-CAISO-35 — CAISO: BATTERY-OUTAGE CENSUS (link 17). Zero LP.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-34 (the parent session that launched you) with mcp__claude-code-remote__archive_session,
  but only once its PR (branch `claude/modest-clarke-ov7ad3`) reads MERGED on the GitHub MCP. If it is not
  merged, do not archive, and say so. The parent's session ID is in your launch prompt.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch, close the
  PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  Known leftovers that carry nothing absent from main: `claude/r-caiso-33` (merged as PR #7056) and
  `claude/modest-clarke-ov7ad3` (once merged). `claude/caiso-dmm-battery-soc-tnw2ww` was already gone on
  2026-10-02.
- The `claude/closeout-caiso-*` and `claude/w0-caiso-*` branches, and PR #7057 if still open, belong to the
  parallel closeout-CAISO lane. Do not touch them.
- Work on a fresh branch off origin/main.

STATE (2026-10-02):
- Keeper: `2026-10-02-closeout-caiso-w1-arm3`, or `2026-10-02-closeout-caiso-w1-arm2` if the closeout lane's
  PR #7057 has merged. Read frontend/data/backcast/keepers/CAISO.json for the truth. Determination NOT-YET.
  The close-out sequence is in docs/mechanism-testing-matrix.md §5.2 and docs/backcast-closeout-plan-2026-10.md
  §3.7. The closeout-CAISO lane runs in parallel; do not touch its arms.
- R-CAISO-34 (link 16, display only, CLOSED): the Run Explorer storage panel now shows the submitted EOH
  SOC-bound envelope beside the keeper's SOC for 2023–25, plus the DMM quarterly SOC-outage card
  (`scripts/lib/storage_compare.py::build_soc_bounds`; record `docs/records/caiso/r-caiso-34/`).
  Owner card: ship as rendered. Every future render carries the block. If a CAISO keeper payload on main lacks
  `storageCmp.socBounds` (a promotion rendered before R-CAISO-34 merged, e.g. arm 2), run
  `python3 scripts/probes/_rcaiso34_inject_soc_bounds.py <run_id> <bundle_dir>` and commit the payload. This is
  display only and not a promotion.
- Link 15 (joint gas re-basis) is CLOSED (R-CAISO-33 PRECOMMIT §10–§11); re-opening needs new evidence or an
  explicit owner override.

TASK — link 17 (owner-selected, R-CAISO-32 FINDING §4, §7): BATTERY-OUTAGE CENSUS. Zero LP.
- Extend the CNOG resource crosswalk (data/raw/reference/caiso-resource-eia-crosswalk.csv,
  scripts/data/build_caiso_resource_crosswalk.py) to battery resources.
- Then measure whether the `caiso_storage_shape_anchor` p95 envelope
  (data/raw/reference/caiso-storage-shape-envelope.csv) already carries the measured battery MW outages
  (14–21 % of fleet MW, scripts/probes/_rcaiso32_soc_derate_reach.py Part B). This is the rule-19 test: does
  an existing mechanism already floor/cap this phenomenon?
- Pre-register the test and its pass/fail reading in a PRECOMMIT before computing.
- No consumer is proposed until that test is adjudicated. No solve, no ScenarioConfig field.
- End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-34, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6,
the R-CAISO-26 PRECOMMIT §6, the R-CAISO-27 FINDING §4, the R-CAISO-28 FINDING §3, the R-CAISO-29 FINDING §3,
the R-CAISO-30 FINDING §5, the R-CAISO-31 FINDING §4, the R-CAISO-32 FINDING §7, the R-CAISO-33 PRECOMMIT
§8, §10 and §11, and the R-CAISO-34 FINDING §5.

NOTES:
- Fresh container: `pip install -e . pytest pytest-xdist tzdata ruff`, then
  `python3 scripts/hydrate_data.py --profile caiso` (a full clone reports "re-run with --force"; data is
  already present then).
- `git fetch origin main` can stall >2 min in a fresh container; run it in the background.
- Run `ruff format` as a separate command before any push. A few unrelated tests fail on main
  (tests/unit/config, test_fetch_miso_hub_lmp_monthly, test_gas_offer_zonal_anchor_vintage).
- Shards can fail at start on the weekly limit. Relaunch once, then card the owner.
- Never `git grep` in a partial clone. Shards read long prompts from an immutable SHA (`git show <sha>:<path>`).
- `pkill -f <pattern>` matches your own shell's command line and kills it; use the PID.
- Never name a scratch script after a stdlib module.
- matplotlib and pdfplumber are not installed by default (`pip install matplotlib pdfplumber`).
- A full payload re-render (`scripts/render_backcast.py`) needs the bundle's gitignored `system.parquet` and
  the shared inputs (`run_calibration_full.py --restore-shared-inputs <bundle>` restores the latter only).
- Headless page checks: `pip install playwright`, then launch with
  `executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'` and `ignore_https_errors=True`, so the
  d3 CDN loads through the proxy.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is zero LP, so expect none). PR + rebase-merge; use a merge commit if
  GitHub refuses the rebase, and say so. Archive every shard and report leftover shard branches.
- Then launch the next owner-selected link as a nested session with these same directions. It archives you when
  safe, salvages and closes CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and
  archives shards. Any link that solves launches its own year shards (rules 32–36). If no next link is
  selected, card the owner for one.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
