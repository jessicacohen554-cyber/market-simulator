SESSION R-CAISO-34 — CAISO: RUN EXPLORER STORAGE PANEL (link 16). Display only. No solve.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-33 (session_01Hk5iBxXCm9KeyeKcNdd8Y4) with mcp__claude-code-remote__archive_session,
  only once its PR #7056 (branch `claude/r-caiso-33`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch, close the
  PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  Known leftovers that carry nothing absent from main: `claude/caiso-dmm-battery-soc-tnw2ww` (R-CAISO-32,
  merged by rebase), `claude/r-caiso-33` (once merged). `claude/r-caiso-27/-29/-30/-31` were already gone from
  the remote on 2026-10-02.
- Work on a fresh branch off origin/main.

STATE (2026-10-02):
- Keeper `2026-10-02-closeout-caiso-w1-arm3` (bundle `results/calibration/closeout_caiso_w1_a3_span`, 2019–2025 in one
  span), promoted 2026-10-02 by the closeout-CAISO lane (W0 EIA-860 settlement re-solve, then `caiso_ra_min_load_frac`
  0.26 → measured 0.570). Determination NOT-YET (C1 CC_REGULAR 2019–21, C3a 2021, C4 gas 2019–21; C3c 2024 ledgered).
  The close-out sequence is in docs/mechanism-testing-matrix.md §5.2 and docs/backcast-closeout-plan-2026-10.md §3.7;
  check it before acting, because the closeout-CAISO lane is running in parallel. Do not touch its arms.
- R-CAISO-33 (zero LP; docs/records/caiso/r-caiso-33/PRECOMMIT-r-caiso-33-joint-gas-rebasis-2026-10-02.md
  §0–§11): link 15 (joint gas re-basis) is CLOSED, keeper unchanged, no solve. The owner ruled "keep 0.46, repair
  the denominator, solve"; stage 1 re-derived the offer surface on composite + 0.46 (G1–G4 pass), but the
  pre-registered round-trip gate failed, and the hour-grain re-gate (Amendment A, pushed before computing) failed
  on 2 of 18 per-year cells (CC and CT peak 2024; all pooled cells ≤ $0.03/MWh). Owner card: close as
  pre-registered. The derive edit was reverted; 0.46 keeps its original citation. RECORDED, not levers: (a) at hour
  grain the keeper's measured gas bands sit +$3.6–6.4/MWh above the fleet's own DAM bids (pooled, every consumed
  class and band); (b) the re-fetched OASIS bid corpus moves the CT/ST partition (st_cut 11.74 → 11.19, ~1.5 GW
  CT → ST_GAS) while consumed bands move ≤ 0.022 — any future re-derive inherits this. The cell is adjudicated
  (rule 28): re-opening needs new evidence or an explicit owner override.

TASK — link 16 (owner-selected, R-CAISO-31 FINDING §4): RUN EXPLORER STORAGE PANEL — display only.
- Render the `storage-soc-bounds` envelope (submitters' mean min/max share of ceiling by Pacific hour of day,
  plus the coverage share) next to the keeper's storage SOC on the Run Explorer storage panel. Read the committed
  extract data/raw/caiso-rtm-eoh-soc/ or the probe JSON (scripts/probes/_rcaiso31_eoh_soc_diagnostic.py); label
  it as a self-selected subset and never as a target.
- Optional: the R-CAISO-32 digitized SOC-outage shares (docs/records/caiso/r-caiso-32/dmm_soc_outage_digitized.json)
  may sit on the same panel as a quarterly reference band, labelled DMM, digitized (not selected by the owner,
  not refused).
- No solve, no ScenarioConfig field. Frontend only (docs/codebase-site/ Run Explorer; check how the storage
  panel reads the keeper's `hourly/storage_<year>.parquet` sidecar and whether a static JSON is needed under
  frontend/data/). Generated dashboard files are rebuilt by the Pages deploy (CLAUDE.md "Git and pushing").
- End with a decision card (ship as rendered / changes).

QUEUED AFTER YOU (owner-selected). Carry into your end-of-session handoff:
- Link 17, R-CAISO-35: BATTERY-OUTAGE CENSUS — zero LP (R-CAISO-32 FINDING §4, §7). Extend the CNOG resource
  crosswalk (data/raw/reference/caiso-resource-eia-crosswalk.csv, scripts/data/build_caiso_resource_crosswalk.py)
  to battery resources, then measure whether the `caiso_storage_shape_anchor` p95 envelope
  (data/raw/reference/caiso-storage-shape-envelope.csv) already carries the measured battery MW outages
  (14–21 % of fleet MW, scripts/probes/_rcaiso32_soc_derate_reach.py Part B): the rule-19 test. No consumer is
  proposed until that test is adjudicated. End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-33, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6,
the R-CAISO-26 PRECOMMIT §6, the R-CAISO-27 FINDING §4, the R-CAISO-28 FINDING §3, the R-CAISO-29 FINDING §3,
the R-CAISO-30 FINDING §5, the R-CAISO-31 FINDING §4, the R-CAISO-32 FINDING §7 and the R-CAISO-33 PRECOMMIT §8, §10 and §11.

NOTES:
- Fresh container: `pip install -e . pytest tzdata`, then `python3 scripts/hydrate_data.py --profile caiso`
  (a full clone reports "re-run with --force"; data is already present then).
- `git fetch origin main` can stall >2 min in a fresh container; run it in the background.
- Run `ruff format` as a separate command before any push. A few unrelated tests fail on main
  (tests/unit/config, test_fetch_miso_hub_lmp_monthly, test_gas_offer_zonal_anchor_vintage).
- Shards can fail at start on the weekly limit. Relaunch once, then card the owner.
- Never `git grep` in a partial clone. Shards read long prompts from an immutable SHA (`git show <sha>:<path>`).
- `pkill -f <pattern>` matches your own shell's command line and kills it; use the PID.
- Never name a scratch script after a stdlib module.
- matplotlib and pdfplumber are not installed by default (`pip install matplotlib pdfplumber`).
- The CAISO public-bid zips are gitignored and the derive's reduced store is not on disk; a re-derive needs
  the fetch (~2 h at the OASIS spacing) plus the pass-1 reduce (~15 min).

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is display-only, so expect none). PR + rebase-merge. Archive every
  shard and report leftover shard branches.
- Then launch R-CAISO-35 (link 17) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
