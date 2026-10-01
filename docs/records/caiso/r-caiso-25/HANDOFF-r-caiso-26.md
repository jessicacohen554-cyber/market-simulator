SESSION R-CAISO-26 — CAISO: NW-stress import-driver scoping (link 8). SCOPING-ONLY PRECOMMIT, no build.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-25 (its session id is in your launch prompt) with mcp__Claude_Code_Remote__archive_session,
  only once its PR (branch `claude/r-caiso-25`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main: `claude/r-caiso-22`,
  `claude/caiso-midday-rt-spread-root-cause-u0q8et`, `claude/r-caiso-24`, `claude/r-caiso-25`.
- Work on a fresh branch off origin/main.

STATE (2026-10-01):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
- R-CAISO-21..-24 (zero LP): evening = DART basis + C3c tail; no lever for C3c 2024; midday N–S spread
  ledgered (data-availability limited); h18 body residual ledgered as a shape residual.
- R-CAISO-25 (zero LP; docs/handoffs/r-caiso-25/, probe scripts/probes/_rcaiso25_prc_fuel.py): NO public
  same-day CA gas series exists for 2022–25 (NGI, ICE next-day and CAISO OASIS PRC_FUEL are all next-day;
  same-day is licensed ICE only). CAISO DMM Jan-2024: CA gas moderate; the event drivers were NW shortage,
  a forced NOB outage all weekend, Oregon transmission outages and Malin congestion. PRC_FUEL for SCE/SDG&E
  on MLK was 13.4–16.8 vs the model's 17.80, so the event's HR 15.5 is NW import parity — this link's object.

TASK — link 8 (owner cards 2026-09-30 / 2026-10-01):
- SCOPING-ONLY PRECOMMIT, no build. Find a measured, forward-regenerating state variable that reduces
  firm-import delivery when the NW/DSW is short. R-CAISO-22 §2: the firm floor stays at 2.4 GW while measured
  net import fell to 0.6–0.8 GW (Malin $230–255). R-CAISO-23 FINDING §4: on Jan 13 and 15 2024 the model's PNW
  node prices at $0 while Malin DAM was $177–219 (the node is long). NEW from R-CAISO-25: the DMM Jan-2024
  report names a forced NOB outage (whole MLK weekend) and Oregon transmission outages limiting S→N transfers;
  a measured intertie outage/derate record is a candidate physical availability input (rule 13), never a
  shadow price or a flow outcome.
- State up front: the delta is 2024-specific (2022/2023 events −1.2/−0.75 GW); the C3c payoff is bounded at
  ≤ 1 hour (R-CAISO-22 §3); caiso-150 §H's DO-NOT-REDO list (the self-schedule ceiling, the direction wall)
  binds. End with a decision card.

QUEUED AFTER YOU (all owner-selected). Carry these into your end-of-session handoff in this order:
- Link 9, R-CAISO-27: SCOPING ONLY, no build. Look for a measured, backcast-admissible transmission-outage or
  derate record for the Path-15 / Gates–Midway complex, 2022–25. It is the only re-arm route for
  `caiso_fsno_subzonal_topology` (R; caiso-224 caps falsified). It must be a physical availability input
  (rule 13), never a constraint shadow price or curtailment outcome. caiso-218 found no published
  internal-path operating-limit series 2023–25. End with a decision card.
- Link 10, R-CAISO-28: SCOPING ONLY, no build. Look for a per-class behavioural battery input for CAISO,
  2023–25: per-resource (or per-duration-class) SOC, or unmasked battery bid curves (OASIS PUB_DAM_GRP is
  masked with no fuel tag; caiso-176/178 found it does not identify a battery offer parameter). The only new
  evidence that could re-open R-CAISO-24 §5. State up front that the R-CAISO-24 bound is ≤ $0.5/MWh at h18.
  End with a decision card.
- Link 11, R-CAISO-29 (ADDED by the R-CAISO-25 owner card 2026-10-01): SCOPING ONLY, no build. Decompose
  CAISO OASIS PRC_FUEL (per-fuel-region gas price CAISO uses for cost-based bids) against the model's delivered
  gas (NGI CA composite, flow-dated, + CAISO_CITYGATE_TRANSPORT_ADDER 0.46). R-CAISO-25 §4: PRC_FUEL runs
  +2.9 (SCE/SDG&E) / +4.1 (PG&E) $/MMBtu above it year-round in 2024 (r ≈ 0.97). Evidence for the open
  transport-adder methodology ask (rule 14), not a C3c lever. Note that the keeper's offer-band multipliers
  were set against the model's own delivered series, so the offset is not a price error until decomposed.
  Probe: scripts/probes/_rcaiso25_prc_fuel.py (OASIS returns empty for some months; retry slowly).
  End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-25, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7 and the R-CAISO-25
FINDING §6.

NOTES:
- Fresh container: `pip install -e . pytest tzdata`, then `python3 scripts/hydrate_data.py --profile caiso`.
- Run `ruff format` as a separate command before any push. 4 unrelated tests in tests/unit/config fail on main.
- Shards can fail at start on the weekly limit. Relaunch once, then card the owner.
- Order is register → attest → register. A status/CAISO.js rebase conflict → re-run build_status.py --iso CAISO.
- check_registry_payload_parity flags your own gitignored legs locally (rule 31); they are absent in CI.
- Never `git grep` in a partial clone. Shards read long prompts from an immutable SHA
  (`git show <sha>:<path>`).
- The zero-LP offer-stack rebuild takes ~90 s per year (R-CAISO-22 `--stack`).

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is scoping only, so expect none). PR + rebase-merge. Archive every
  shard and report leftover shard branches.
- Then launch R-CAISO-27 (link 9) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
