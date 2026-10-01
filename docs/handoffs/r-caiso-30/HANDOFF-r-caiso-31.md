SESSION R-CAISO-31 — CAISO: OASIS PUB_RTM_GRP storage EOH SOC bounds intake (link 13). DATA INTAKE ONLY, REPORT-ONLY, no solve, no arm.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-30 (its session id is in your launch prompt) with mcp__Claude_Code_Remote__archive_session,
  only once its PR (branch `claude/r-caiso-30`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main (`git cherry` shows "-"):
  `claude/r-caiso-27`, `claude/r-caiso-29`, `claude/r-caiso-30` (once merged).
- Work on a fresh branch off origin/main.

STATE (2026-10-01):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
- R-CAISO-30 (zero LP; docs/handoffs/r-caiso-30/FINDING-r-caiso-30-2026-10-01.md): OASIS TRNS_USAGE (DAM)
  intaken 2023-06-19..2025-12-31 into data/raw/caiso-trns-usage (COMMITTED, since retention rolls) and the
  `transfer-interface-limits` CAISO partition (no consumer). The earliest retained OASIS day was 2023-06-19.
  PNW import OTC (Malin+NOB+Cascade, provisional ITC set) averages ~4.1 GW against the armed p95 envelope's
  1.3–1.7 GW, which exceeds OTC in only 0.3–3.7 % of hours, so an OTC cap would not bind. DAM TRM = 0.
  Owner ruled REPORT-ONLY: no crosswalk scoping, no TRNS_OUTAGE intake (do not re-ask).
- Fetch pattern that worked (scripts/data/fetch_caiso_trns_usage.py): Pacific-day windows computed from
  local midnight (07Z in PDT, 08Z in PST), a lossless wide parquet per window into a gitignored `windows/`
  staging dir, a `--fold` into committed per-year parquets plus SHA256SUMS, and THREE disjoint date ranges
  run concurrently (~1–2 min per 11-day window each; no 429 seen).

TASK — link 13 (owner-selected):
- DATA INTAKE ONLY, REPORT-ONLY, no solve, no arm. Intake OASIS `PUB_RTM_GRP` storage end-of-hour SOC bounds
  (`MINEOHSTATEOFCHARGE` / `MAXEOHSTATEOFCHARGE`, per masked RESOURCEBID_SEQ, hourly) for 2023–25 as a
  storage diagnostic (Run Explorer storage panel or a sidecar), via the `data-intake` skill. NEVER a solve
  input (R-CAISO-28 FINDING §1 point 4, rule 13). RTM zips are ~1.8 MB/day; fetcher
  `scripts/data/fetch_caiso_public_bids.py --market rtm` (check its CLI), 6–8 s spacing. Rolling OASIS
  retention: bisect the earliest retained day first and state what was lost. If the raw is too large to
  commit, commit a compact derived extract of the EOH fields and say what was dropped. End with a decision
  card.

QUEUED AFTER YOU (all owner-selected). Carry these into your end-of-session handoff in this order:
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

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-30, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6,
the R-CAISO-26 PRECOMMIT §6, the R-CAISO-27 FINDING §4, the R-CAISO-28 FINDING §3, the R-CAISO-29 FINDING §3
and the R-CAISO-30 FINDING §5.

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
- OASIS ERR_CODE 1000 = "No data returned"; an error comes back as a ~650-byte zip holding XML.
- `transfer-interface-limits` IsoSpec now has `max_fill_hours` (None = PJM dense fill; an int = fill only
  short interior gaps, leave the rest absent). Reuse that pattern for any partial-year CAISO series.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is intake only, so expect none). PR + rebase-merge. Archive every
  shard and report leftover shard branches.
- Then launch R-CAISO-32 (link 14) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
