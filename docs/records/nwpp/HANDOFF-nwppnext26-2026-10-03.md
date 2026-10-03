# HANDOFF — NWPP-NEXT-27 (from NWPP-NEXT-26, 2026-10-03)

```
SESSION NWPP-NEXT-27 — NWPP calibration: residual CC_REGULAR 2024 over-run / C4 gas (phase 0 first), keeper 2026-10-03-nwpp-next-26-nevp
DATA PROFILE: nwpp (plus data/raw/caiso-trns-usage — the CAISO token keeps it out of the nwpp sparse profile)
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 16, 19, 20, 21, 24, 25, 26, 28, 29 and 31–37.
The parent never solves (rule 32). Every backcast year gets its own shard (rule 36).

Read first:
- docs/records/nwpp/RESULT-nwppnext26-nevp-hae-2019-2025-2026-10-03.md (incl. §Promotion)
- docs/records/nwpp/FINDING-nwppnext26-nevp-hae-phase0-2026-10-03.md (§F: what was not reached)
- docs/records/nwpp/RESULT-nwppnext25-served-schedule-2019-2025-2026-10-03.md

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01BuB3gbRTk8R1wMLRBWgvVr (NWPP-NEXT-26).
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
If another live NWPP session works the same lever, put that on an owner card before spending LP. A backcast close-out
DESK is live (session_01ERkBTm23ZAP4CTZnJVD9Ss, "Backcast closeout desk handoff"; re-check with list_sessions — a newer
desk may have replaced it): send it your session id, branch and pin by send_message before launching shards, and
request the NWPP promotion slot there. The promotion itself still goes on ONE owner card.

STATE ON MAIN
- Keeper: 2026-10-03-nwpp-next-26-nevp (bundle results/calibration/nwppnext26_span, 2019–2025, legs at pin
  30c0e01790f3ee4085042193be816d47cc704c31): keeper NEXT-25 recipe + nwpp_seam_in_service_vintage (CAISO_NEVP priced
  only after the Harry Allen–Eldorado intertie entered service 2020-08-12; before it the measured leg is served at SNV).
  Replay: `replay_keeper.py results/calibration/nwppnext26_span --years Y`.
- Rubric: NOT-YET. FAIL records (7): fuelmix CC_REGULAR 2024 +12.77 TWh; C4 gas 2019 r 0.669, 2023 0.533, 2024 0.797
  (NRMSE 0.316); C3a 2024 −25.3 %; C3b 2023 0.209 (0.009 over the band) / 2024 0.772.
  Knife-edges: CC_REGULAR 2019 +7.61 (band 8.00, margin 0.39), C4 coal 2019 r 0.754. D-1 fails 17 class-years.
- Price is unscored 2019–2022 (WEIM benchmark starts 2023-06, owner ruling R-9).

TASK — the CC_REGULAR 2024 over-run and C4 gas, phase 0 first (zero LP).
- 2024 seam exports (TWh, model vs measured): COI 8.97 vs 2.15, BC 11.36 vs 7.51, NEVP 10.13 vs 9.18. The CC excess
  (+12.8) is roughly the COI + BC over-export. NEXT-20..24 closed the COI depth / ETC / TOR / firm-block / CARB-wedge /
  delivery-basis questions; read those CLOSED items before proposing anything at COI.
- Supply side, never adjudicated for CC (agent census in this session): a CC-specific availability lever
  (CAMPD outage windows for CCs, `wefor_residual` is O, `cc_winter_capability_basis` / `temp_dependent_derate` U),
  part-load / incremental heat rates (no lever ever tested), per-plant delivered gas basis (`zonal_gas_basis`,
  `gas_hub_basis_overlay`, `gas_plant_monthly_pricing` all U — check the measured-data constraints in HANDOFF-nwppnext20:
  no public daily NW hub series). Long plants 2024: SNV (Harry Allen 55322, 55687, 55514, Clark 2322, Silverhawk 55841),
  EAST (Lake Side 56237, Currant Creek 56102) — FINDING-nwppnext25-cc §A.
- Unclosed leftovers: HANDOFF-nwppnext14 lever 2 (per-plant CT-under vs CC-over check) and HANDOFF-nwppnext15 lever 3
  (per-plant decomposition of Clark energy).
Then, if a lever is admissible: card it, add the default-off key + matrix row + a cell in every shard + tests, write the
PRECOMMIT, and run 7 shards. Copy docs/records/nwpp/nwppnext26/shards/shard_<Y>.txt (generated from the NEXT-25 set by
substitution: pin, --set key, scenario-diff allowance, expected zonal demand, replay source nwppnext26_span); CHECK that
the generated prompt names an EXISTING bundle dir at the pin before launching. A key that changes only some years makes
the others exact controls — verify them to 0.0000 and archive early. Then compose
(scripts/probes/_nwpp42_compose_span.py), extend scripts/gen_nwppnext26_attestation.py for the attestation, run
dashboard_add_run --no-prune and the verdict diff vs the keeper (calibration_verdict.py --run-id <id> --json, both
runs), and put the promotion on ONE owner card.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext25.
- NEXT-26: the CAISO_NEVP seam before Harry Allen–Eldorado (now K in the keeper). 2021–2025 NEVP is on its real rating
  (2024 10.13 vs 9.18 measured) — not an over-run source.

PROCEDURE GOTCHAS
- Shard wrapper prompt: create_session with source_revision = the PROMPT commit, and a short prompt telling the shard to
  `git show <prompt-sha>:docs/records/nwpp/<lane>/shards/shard_<Y>.txt` and follow it; the file checks out the PIN.
  NEXT-26's shards all started within ~35 min (none needed a relaunch). One shard may leave its leg on the prompt commit
  instead of the pin: accept it only if `git diff <pin> <prompt> -- src scripts tests data configs` is empty.
- Ad-hoc probes and the attestation need PYTHONPATH=src:. (scripts.lib.clean_io); the transfer-interface-limits clean
  partition needs `scripts/data/curate_transfer_interface_limits.py --isos NWPP CAISO` before a zero-LP seam check.
- The attestation chain `git show`s 909cdd30: `git fetch origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943` first.
- Parent: extract legs with `git archive <sha> results/calibration/<leg> | tar -x`. Move staged legs out of
  results/calibration before promote_keeper. Do NOT put results/calibration patterns in .git/info/exclude.
- promote_keeper needs --attested-by "<lane>; owner card '<ruling>'; <date>" and the same --label used at
  dashboard_add_run (the run id is derived from it). After it: stamp NWPP.js (keeper + gates + cell), the §5.9 header in
  docs/mechanism-testing-matrix.md (check_mechanism_matrix warns on drift), and docs/calibration-log/nwpp.md.
- Merging main mid-lane: mechanism-matrix.js conflicts are anchor-digit churn — take main's file, re-insert your row,
  run check_mechanism_matrix.py --fix-anchors.
- Tell shards: no legitimacy_diagnostics or scorer; push without asking; launch the solve ONCE.

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now:
  - claude/nwppnext26-2019 … -2025 and claude/nwppnext26-pin (keeper legs; the committed keeper bundle carries the
    hourly/ sidecars; dispatch/ and unit_hourly are on these branches — delete once the owner no longer needs a byte
    replay);
  - claude/nwppnext26 (after merge);
  - claude/nwppnext25, claude/nwppnext25-2019 … -2025, claude/nwppnext25-pin (superseded keeper legs);
  - every branch listed in HANDOFF-nwppnext25.
```
