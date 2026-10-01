SESSION R-CAISO-29 — CAISO: OASIS PRC_FUEL decomposition (link 11). SCOPING ONLY, no build.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-28 (its session id is in your launch prompt) with mcp__Claude_Code_Remote__archive_session,
  only once its PR (branch `claude/r-caiso-28`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main: `claude/r-caiso-27`, `claude/r-caiso-28`.
- Work on a fresh branch off origin/main.

STATE (2026-10-01):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
- R-CAISO-21..-27 (zero LP): see their FINDINGs and the CAISO matrix shard.
- R-CAISO-28 (zero LP; docs/handoffs/r-caiso-28/, probe scripts/probes/_rcaiso28_eoh_soc.py): the one per-resource
  behavioural battery input is OASIS PUB_RTM_GRP MIN/MAXEOHSTATEOFCHARGE (optional RT-only EOH SOC range;
  0.2–4.7 % of storage MW in 2023, 3–16 % 2024, 16–23 % 2025). Its min floor peaks h13–16 and is released by
  h18–20, the wrong sign for 2024–25, inside the R-CAISO-24 bound (≤ $0.5/MWh at h18). It fails rule 13 as an
  input. R-CAISO-24 §5 stays closed. Owner card queued two later links (13, 14 below).

TASK — link 11 (owner-selected):
- SCOPING ONLY, no build. Decompose CAISO OASIS PRC_FUEL against the model's delivered
  gas (NGI CA composite, flow-dated, + CAISO_CITYGATE_TRANSPORT_ADDER 0.46). R-CAISO-25 §4: PRC_FUEL runs
  +2.9 (SCE/SDG&E) / +4.1 (PG&E) $/MMBtu above it year-round in 2024 (r ≈ 0.97). Evidence for the open
  transport-adder methodology ask (rule 14), not a C3c lever. The keeper's offer-band multipliers were set
  against the model's own delivered series, so the offset is not a price error until decomposed.
  Probe: scripts/probes/_rcaiso25_prc_fuel.py (OASIS returns empty for some months; retry slowly).
  End with a decision card.

QUEUED AFTER YOU (all owner-selected). Carry these into your end-of-session handoff in this order:
- Link 12, R-CAISO-30: DATA INTAKE ONLY, no solve, no arm. Intake CAISO OASIS `TRNS_USAGE` (DAM) hourly
  intertie OTC / seasonal TTC / TRM by ITC and direction, from the earliest retained month (present 2023-07-01,
  empty 2023-06-01; bisect the start) through 2025, via the `data-intake` skill (schema-first,
  write_clean/read_clean). Rolling OASIS retention: earliest months roll off while this waits; state what was
  lost. Purpose: a rule-14 measured basis for the corridor caps (today the p95 envelope of measured flows,
  caiso-162/280). caiso-280 found the envelope binds above actuals, so expect no fit gain; do not arm anything.
  Query: `queryname=TRNS_USAGE&market_run_id=DAM`, ~5 MB CSV/day, 11 days per request worked. Consider
  pairing with OASIS `TRNS_OUTAGE` (intertie outage curtailments, public, 2022+ retrievable — R-CAISO-27 §2;
  note `market_run_id` is an invalid parameter for TRNS_OUTAGE). End with a decision card.
- Link 13, R-CAISO-31: DATA INTAKE ONLY, REPORT-ONLY, no solve, no arm. Intake OASIS `PUB_RTM_GRP` storage
  end-of-hour SOC bounds (`MINEOHSTATEOFCHARGE` / `MAXEOHSTATEOFCHARGE`, per masked RESOURCEBID_SEQ, hourly) for
  2023–25 as a storage diagnostic (Run Explorer storage panel or a sidecar), via the `data-intake` skill. NEVER a
  solve input (R-CAISO-28 FINDING §1 point 4, rule 13). RTM zips are ~1.8 MB/day; fetcher
  `scripts/data/fetch_caiso_public_bids.py --market rtm` (check its CLI), 6–8 s spacing. Rolling OASIS retention:
  state what was lost. End with a decision card.
- Link 14, R-CAISO-32: SCOPING ONLY, no build. DMM Battery Special Report Fig 2.26 (2023, 2024; check for a 2025
  report): quarterly mean share of the fleet's charging range lost to SOC outages/derates (OMS upper/lower charge
  limits). Scope it as a physical availability input (rule 13: a physical derate, like unit outage windows).
  State that it is aggregate and digitize-only, and that its price reach sits inside the R-CAISO-24 bound.
  Look for an underlying OMS or OASIS series. End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-28, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6,
the R-CAISO-26 PRECOMMIT §6, the R-CAISO-27 FINDING §4 and the R-CAISO-28 FINDING §3.

NOTES:
- Fresh container: `pip install -e . pytest tzdata`, then `python3 scripts/hydrate_data.py --profile caiso`
  (a full clone reports "re-run with --force"; data is already present then).
- `git fetch origin main` can stall >2 min in a fresh container; run it in the background.
- Run `ruff format` as a separate command before any push. 4 unrelated tests in tests/unit/config fail on main.
- Shards can fail at start on the weekly limit. Relaunch once, then card the owner.
- Order is register → attest → register. A status/CAISO.js rebase conflict → re-run build_status.py --iso CAISO.
- check_registry_payload_parity flags your own gitignored legs locally (rule 31); they are absent in CI.
- Never `git grep` in a partial clone. Shards read long prompts from an immutable SHA
  (`git show <sha>:<path>`).
- The keeper's slim bundle has no per-plant dispatch, so link flows are not in the committed hourlies.
- caiso-218/222/224 FINDING docs are pruned from main; the CAISO matrix shard cells are the record.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is scoping only, so expect none). PR + rebase-merge. Archive every
  shard and report leftover shard branches.
- Then launch R-CAISO-30 (link 12) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
