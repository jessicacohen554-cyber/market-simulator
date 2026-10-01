SESSION R-CAISO-30 — CAISO: OASIS TRNS_USAGE intertie OTC intake (link 12). DATA INTAKE ONLY, no solve, no arm.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-29 (its session id is in your launch prompt) with mcp__Claude_Code_Remote__archive_session,
  only once its PR (branch `claude/r-caiso-29`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main (`git cherry` shows "-"):
  `claude/r-caiso-27`, `claude/r-caiso-28`, `claude/r-caiso-29`.
- Work on a fresh branch off origin/main.

STATE (2026-10-01):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
- R-CAISO-21..-28 (zero LP): see their FINDINGs and the CAISO matrix shard.
- R-CAISO-29 (zero LP; docs/handoffs/r-caiso-29/, probe scripts/probes/_rcaiso29_prc_fuel_decomp.py): PRC_FUEL's
  +2.9/+4.1 gap = ~1.8 LDC cap-and-trade double count (non-GHG comparator) + hub basis + intrastate transport
  (GHG twin 0.07–2.6 by region vs model 0.46). On EIA N3045CA3 the model's delivered gas is 0.7–0.8 $/MMBtu low
  (2023–25): the 0.46 was measured vs EIA citygate but rides on the NGI composite. Owner: queue a JOINT re-basis
  as link 15 (below). OASIS tip: windows must sit on Pacific-day boundaries (07Z in PDT months, 08Z in PST);
  08Z in a PDT month returns an empty zip.

TASK — link 12 (owner-selected):
- DATA INTAKE ONLY, no solve, no arm. Intake CAISO OASIS `TRNS_USAGE` (DAM) hourly intertie OTC / seasonal TTC /
  TRM by ITC and direction, from the earliest retained month (present 2023-07-01, empty 2023-06-01; bisect the
  start — and re-test June with a 07Z window before calling it empty, see the OASIS tip above) through 2025, via
  the `data-intake` skill (schema-first, write_clean/read_clean). Rolling OASIS retention: earliest months roll
  off while this waits; state what was lost. Purpose: a rule-14 measured basis for the corridor caps (today the
  p95 envelope of measured flows, caiso-162/280). caiso-280 found the envelope binds above actuals, so expect no
  fit gain; do not arm anything. Query: `queryname=TRNS_USAGE&market_run_id=DAM`, ~5 MB CSV/day, 11 days per
  request worked. Consider pairing with OASIS `TRNS_OUTAGE` (intertie outage curtailments, public, 2022+ —
  R-CAISO-27 §2; `market_run_id` is an invalid parameter for TRNS_OUTAGE). End with a decision card.

QUEUED AFTER YOU (all owner-selected). Carry these into your end-of-session handoff in this order:
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
- Link 15, R-CAISO-33: JOINT GAS RE-BASIS — SCOPING + PRECOMMIT first, no solve in the scoping session.
  (R-CAISO-29 FINDING §1–§3.) Re-identify `CAISO_CITYGATE_TRANSPORT_ADDER` against the base it rides on (the NGI
  CA composite, flow-dated; EIA N3045CA3 − composite ≈ 1.15–1.28 $/MMBtu 2023–25; comparator is the GHG fuel
  region, never non-GHG) AND re-derive the measured offer-surface denominator
  (`derive_caiso_offer_surface.py`, caiso-242/244) on the same delivered basis, so the multipliers still
  round-trip to the measured bids. Moving the adder alone double-shifts every gas offer by ~$5–8/MWh. Rule 14 is
  the basis, never the residual (rule 1); C4 2025 gas NRMSE has zero margin (caiso-257) — state the risk. Freeze
  the identification in a PRECOMMIT before any solve; a later full-span solve follows rules 32–36 (one shard per
  year). End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-29, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6,
the R-CAISO-26 PRECOMMIT §6, the R-CAISO-27 FINDING §4, the R-CAISO-28 FINDING §3 and the R-CAISO-29 FINDING §3.

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
- `pkill -f <pattern>` matches your own shell's command line and kills it; use the PID.
- The keeper's slim bundle has no per-plant dispatch, so link flows are not in the committed hourlies.
- caiso-218/222/224 FINDING docs are pruned from main; the CAISO matrix shard cells are the record.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is intake only, so expect none). PR + rebase-merge. Archive every
  shard and report leftover shard branches.
- Then launch R-CAISO-31 (link 13) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
