SESSION R-CAISO-32 — CAISO: DMM Battery Special Report SOC-outage scoping (link 14). SCOPING ONLY, no build, no solve, no arm.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-31 (its session id is in your launch prompt) with mcp__claude-code-remote__archive_session,
  only once its PR (branch `claude/r-caiso-31`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main (`git cherry` shows "-"):
  `claude/r-caiso-27`, `claude/r-caiso-29`, `claude/r-caiso-30`, `claude/r-caiso-31` (once merged).
- Work on a fresh branch off origin/main.

STATE (2026-10-01):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
- R-CAISO-31 (zero LP; docs/records/caiso/r-caiso-31/FINDING-r-caiso-31-rtm-eoh-soc-intake-2026-10-01.md):
  OASIS PUB_RTM_GRP storage end-of-hour SOC bid bounds intaken for 2023–25 (1,095/1,096 days; hole
  2024-07-03). They are committed as a compact extract in data/raw/caiso-rtm-eoh-soc/ plus the clean datatype
  `storage-soc-bounds` (no consumer). Submitters hold 2.7 / 12.2 / 19.8 % of storage MW. The keeper's fleet SOC
  sits inside the submitters' mean bound envelope at every hour of day. Earliest RTM bid day OASIS serves
  (2026-10-01): 2021-09-01. Owner ruled CLOSE REPORT-ONLY and queued a Run Explorer panel as link 16. The
  pinned-window observation (FINDING §1) was NOT folded into link 14, so do not re-ask about it.

TASK — link 14 (owner-selected, R-CAISO-28 FINDING §3 point 2):
- SCOPING ONLY, no build. DMM Battery Special Report Fig 2.26 (2023, 2024; check for a 2025 report): the
  quarterly mean share of the fleet's charging range lost to SOC outages/derates (OMS upper/lower charge
  limits). Scope it as a physical availability input (rule 13: a physical derate, like unit outage windows).
  State that it is aggregate and digitize-only, and that its price reach sits inside the R-CAISO-24 bound.
  Look for an underlying OMS or OASIS series. End with a decision card.

QUEUED AFTER YOU (all owner-selected). Carry these into your end-of-session handoff in this order:
- Link 15, R-CAISO-33: JOINT GAS RE-BASIS — SCOPING + PRECOMMIT first, no solve in the scoping session.
  (R-CAISO-29 FINDING §1–§3.) Re-identify `CAISO_CITYGATE_TRANSPORT_ADDER` against the base it rides on (the NGI
  CA composite, flow-dated; EIA N3045CA3 − composite ≈ 1.15–1.28 $/MMBtu 2023–25; the comparator is the GHG fuel
  region, never non-GHG) AND re-derive the measured offer-surface denominator
  (`derive_caiso_offer_surface.py`, caiso-242/244) on the same delivered basis, so the multipliers still
  round-trip to the measured bids. Moving the adder alone double-shifts every gas offer by ~$5–8/MWh. Rule 14 is
  the basis, never the residual (rule 1). C4 2025 gas NRMSE has zero margin (caiso-257), so state the risk.
  Freeze the identification in a PRECOMMIT before any solve; a later full-span solve follows rules 32–36 (one
  shard per year). End with a decision card.
- Link 16, R-CAISO-34: RUN EXPLORER STORAGE PANEL — display only (R-CAISO-31 FINDING §4). Render the
  `storage-soc-bounds` envelope (submitters' mean min/max share of ceiling by Pacific hour of day, plus the
  coverage share) next to the keeper's storage SOC on the Run Explorer storage panel. Read the committed
  extract data/raw/caiso-rtm-eoh-soc/ or the probe JSON (scripts/probes/_rcaiso31_eoh_soc_diagnostic.py); label
  it as a self-selected subset and never as a target. No solve, no ScenarioConfig field.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-31, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6,
the R-CAISO-26 PRECOMMIT §6, the R-CAISO-27 FINDING §4, the R-CAISO-28 FINDING §3, the R-CAISO-29 FINDING §3,
the R-CAISO-30 FINDING §5 and the R-CAISO-31 FINDING §4.

NOTES:
- Fresh container: `pip install -e . pytest tzdata`, then `python3 scripts/hydrate_data.py --profile caiso`
  (a full clone reports "re-run with --force"; data is already present then).
- `git fetch origin main` can stall >2 min in a fresh container; run it in the background.
- Run `ruff format` as a separate command before any push. 4 unrelated tests in tests/unit/config fail on main.
- Shards can fail at start on the weekly limit. Relaunch once, then card the owner.
- Never `git grep` in a partial clone. Shards read long prompts from an immutable SHA (`git show <sha>:<path>`).
- `pkill -f <pattern>` matches your own shell's command line and kills it; use the PID.
- Never name a scratch script after a stdlib module (a `bisect.py` in the cwd broke `urllib.request`).
- OASIS: ERR_CODE 1000 = "No data returned"; ERR_CODE 1015 = GroupZip queued, so re-request before calling a
  date dead. GroupZip day requests are insensitive to a T07/T08 start; SingleZip windows are not.
- matplotlib is not installed by default (`pip install matplotlib` for probe charts).

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is scoping only, so expect none). PR + rebase-merge. Archive every
  shard and report leftover shard branches.
- Then launch R-CAISO-33 (link 15) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
