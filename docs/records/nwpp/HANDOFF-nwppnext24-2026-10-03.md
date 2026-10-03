# HANDOFF — NWPP-NEXT-25 (from NWPP-NEXT-24, 2026-10-03)

```
SESSION NWPP-NEXT-25 — NWPP calibration: C3a tail-day scarcity pricing (phase 0 first), keeper 2026-10-03-nwpp-next-24-head
DATA PROFILE: nwpp (plus data/raw/caiso-trns-usage — the CAISO token keeps it out of the nwpp sparse profile)
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 16, 19, 20, 21, 24, 25, 26, 28, 29 and 31–37.
The parent never solves (rule 32). Every backcast year gets its own shard (rule 36).

Read first: docs/records/nwpp/RESULT-nwppnext24-data-resolve-2026-10-03.md (incl. §Promotion) and
docs/records/nwpp/FINDING-nwppnext24-coi-depth-phase0-2026-10-03.md (§A–§C COI depth closed, §D C3a tail days).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01S4kCgLiLg2CVusXENBn5TW (NWPP-NEXT-24).
  Safe means: its PR has merged on main, and get_session shows it idle.
- Check for unmerged NWPP branches and PRs. Salvage anything needed into your branch, and close or merge the PRs.
  Say which branches can be deleted.
- Rebase and merge your work.
- Present every decision for the owner as clickable decision cards (AskUserQuestion), NEVER as inline text.
- When done: promote if it is a good candidate, create a PR and merge it, archive all your shards, and launch the next
  handoff session to continue calibration while rubric failures remain. Give it these same chain directions, including
  "archive the previous session when safe".
- If NWPP becomes calibrated and the rubric clears for all years, check the complete / frontier declaration criteria.
  Settle the keeper config and clear the tasks that enable declaration. If complete / frontier is reached, say so in
  your final message so the owner can approve.
- If you are at the session-nesting limit, make your last message a handoff prompt that starts a new chain.
- Owner standing ruling: promote if structural integrity improves, even if a gate regresses. Report every regression
  at full magnitude.

FIRST: CHECK FOR A PARALLEL LANE. List sessions, `git ls-remote --heads origin 'claude/*nwpp*'`, and open NWPP PRs.
If another live NWPP session works the same lever, put that on an owner card before spending LP. The backcast
close-out desk (session_01ALecU5Wjde4tkbLrnMExT9) serialises NWPP promotions: send it your session id, branch and pin
by send_message before launching shards, and do not run promote_keeper.py until it hands you the slot. The desk has
said it answers questions by send_message (AskUserQuestion blocks a session); route desk questions there, owner
decisions to cards.

STATE ON MAIN
- Keeper: 2026-10-03-nwpp-next-24-head (bundle results/calibration/nwppnext24_span, 2019–2025, legs at pin
  23beba2ac9c1baa00f276a6723e5af47217739ff): keeper NEXT-23's recipe (anchor + priced interface + measured seam headroom
  + nwpp_coi_pnw_delivery_basis) on main's coal stocks 2015–17 and NWPP 2019–22 nuclear rows. Replay:
  `replay_keeper.py results/calibration/nwppnext24_span --years Y`.
- Rubric: NOT-YET. FAIL records (9, HEAD bench render): fuelmix CC_REGULAR 2019 +12.17 / 2024 +14.90 TWh; C4 gas 2019
  r 0.651, 2023 0.534, 2024 0.789; C3a 2023 −11.6 % / 2024 −27.8 %; C3b 2023 0.225 / 2024 0.791. CC 2025 +7.99 PASS
  (band 8.00 — knife-edge). PASS of note: C4 coal every year, C3a/C3b 2025, D-2/C6; D-1 fails 13.
- Price is unscored 2019–2022 (WEIM benchmark starts 2023-06, owner ruling R-9).

TASK — C3a 2023/2024 (and C3b, same days) are a TAIL-DAY SCARCITY-PRICING gap (FINDING-nwppnext24 §D):
the top 10 days carry 52 % (2023) / 80 % (2024) of the price-mean gap; ex-tail both years are −6/−7 % (inside ±10 %).
Jan 12–17 2024: bench daily $236–782 (peaks $1,269) vs model $48–54; model dispatch matches EIA-930 within 0.3–0.8 GW;
slack 0. Not fuel (Jan 2024 delivered gas $4–6.4, Sumas weekly prints ≤ $6.5), not the hydro water value.
1. Zero-LP phase 0: is there a MEASURED, FORWARD-REPRODUCIBLE driver of NW scarcity pricing (rule 13)? Candidates:
   - WEIM resource-sufficiency-evaluation (RSE) failures / power-balance-constraint penalty pricing intervals for the
     NW BAAs (CAISO OASIS / WEIM reports) — the benchmark is the WEIM ELAP price, so its penalty-priced intervals are
     the mechanism the bench actually carries. Separate the instrument (a reserve/RSE requirement) from the outcome
     (a price).
   - An NW operating-reserve requirement with a demand curve (what reserve does NWPP carry today? rule-19 census of
     every existing tail mechanism: reserve rows, VOLL, any ORDC-style adder in other ISOs, scarcity overlays in
     results/).
   - Hydro capability limits in cold snaps (ice / low-flow) — measured CROHMS hourly output exists
     (data/raw/nwpp-hydro/crohms); is the model's hourly hydro max above measured in the event hours? (Rule 13: a
     capability limit, never pinned output.)
   Price-taker / zero-LP estimate of C3a effect per candidate. Card the lever before any registry change.
2. Also open, lower priority: CC_REGULAR 2019/2024 over-run + C4 gas — NW surplus filling COI/BC (seam depth lane
   CLOSED in NEXT-24: no transmission-quantity driver; do not reopen without new evidence).
3. Then (if a lever is admissible): default-off key + matrix row + a cell in every shard + tests; PRECOMMIT; 7 shards
   (copy docs/records/nwpp/nwppnext24/shards/shard_<Y>.txt; update the pin, the --set key, and the scenario-diff
   allowance; the replay source is nwppnext24_span — CHECK the generated prompt names an EXISTING bundle dir before
   launching); compose (scripts/probes/_nwpp42_compose_span.py), attestation (scripts/gen_nwppnext24_attestation.py
   is the base to extend), dashboard_add_run --no-prune, verdict diff vs the keeper, ONE owner card on promotion.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext23.
- NEXT-24: COI economic depth (ETC/TOR set-aside, CAISO firm-import block, BPA path share — FINDING §C); the NW
  monthly delivered-gas level as a C3a fix for 2024 (Jan 2024 delivered $4–6.4; gas_electric_power_monthly_level is
  inert for NWPP — no state-weight row); the hydro water value as the C3a 2024 driver (ex-tail −7 %).

PROCEDURE GOTCHAS
- Shard prompts: the shard checks out the PIN; give it a SHA where its prompt file lives and have it `git show` the file
  (NEXT-24 pattern: pin + separate prompt commit). Shards routinely sit PENDING 40+ min — archive and relaunch (2021
  needed four launches in NEXT-24).
- A sed rename of `nwppnextNN_` in the prompt templates ALSO renames the replay source `nwppnextNN_span` — NEXT-24 lost
  a wave to it. Grep the generated prompts for the replay dir and `ls` it at the pin.
- The attestation chain `git show`s 909cdd30 (an old nwpp49 attestation): `git fetch origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943`
  in a shallow clone first.
- Ad-hoc probe scripts run from outside the repo need PYTHONPATH=src:. (scripts.lib.clean_io).
- Parent: move staged legs out of results/calibration before promote_keeper (parity sweeps every bundle dir).
- Tell shards: no legitimacy_diagnostics or scorer; push without asking; launch the solve ONCE.

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now: claude/nwppnext24-2019 … -2025 and claude/nwppnext24-pin (keeper legs; the committed keeper bundle
  carries hourly/ sidecars; dispatch/ + unit_hourly are on these branches — delete once the owner no longer needs a
  byte replay), claude/nwppnext24 (after merge), claude/nwppnext23-2019 … -2025, claude/nwppnext23-pin,
  claude/nwppnext23, claude/closeout-nwpp-anchor-2019 … -2025, claude/closeout-nwpp-anchor-result,
  claude/desk-nwpp-keeper-audit, plus the branches listed in HANDOFF-nwppnext22/23.
```
