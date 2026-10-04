# HANDOFF — NWPP-NEXT-27 → NWPP-NEXT-28

```
SESSION NWPP-NEXT-28 — NWPP calibration: CC_REGULAR 2024 over-run as BA conduct (phase 0 first), keeper 2026-10-03-nwpp-next-27-path76
DATA PROFILE: nwpp (plus data/raw/caiso-trns-usage — the CAISO token keeps it out of the nwpp sparse profile)
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 16, 19, 20, 21, 24, 25, 26, 28, 29 and 31–37.
The parent never solves (rule 32). Every backcast year gets its own shard (rule 36).

Read first:
- docs/records/nwpp/RESULT-nwppnext27-path76-served-2019-2025-2026-10-04.md (incl. §Promotion)
- docs/records/nwpp/FINDING-nwppnext27-cc-conduct-path76-phase0-2026-10-03.md (§C conduct, §F not adopted)
- docs/records/nwpp/RESULT-nwppnext26-nevp-hae-2019-2025-2026-10-03.md

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01VNTEBe64my5sYZPhboL9cR (NWPP-NEXT-27).
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
- Keeper: 2026-10-03-nwpp-next-27-path76 (bundle results/calibration/nwppnext27_span, 2019–2025, legs at pin
  440ad14416cbfd3399e4877a17e7c974c4862fb9): keeper NEXT-26 recipe with nwpp_path76_served_schedule replacing
  nwpp_path76_alturas_link (WECC Path 76 NEVP<->BPAT served at its measured EIA-930 leg; zero WEIM transfers on the pair).
  Replay: `replay_keeper.py results/calibration/nwppnext27_span --years Y`.
- Rubric: NOT-YET. FAIL records (7): fuelmix CC_REGULAR 2024 +12.15 TWh; C4 gas 2019 r 0.679, 2023 0.530, 2024 0.803
  (NRMSE 0.305); C3a 2024 −9.96 $/MWh (−24.5 %); C3b 2023 0.202 (0.002 over the band) / 2024 0.767.
  Knife-edges: CC_REGULAR 2019 +7.50 (band 8.00). D-1 18 failure lines (14 coal).
- Price is unscored 2019–2022 (WEIM benchmark starts 2023-06, owner ruling R-9).

TASK — the CC_REGULAR 2024 over-run as a BA-conduct question, phase 0 first (zero LP).
- NEXT-27 phase 0 (FINDING §A–C): the excess is LOADING at the SNV/EAST CCs (Lake Side, Chuck Lenzie, Currant
  Creek, Higgins, Apex: model 0.93–0.98 of available capacity, CAMPD 0.60–0.75). Commitment and heat rate are CLOSED
  (CAMPD input-output curves linear, IHR 6.8 < average 7.1–7.3). Measured NEVP gas tracks NEVP net load (r 0.89) and
  ignores the NEVP WEIM LMP (r ≈ 0); CAMPD loading is flat 0.58–0.84 whether $10 out of or $40 in the money.
- Candidate structures to test at zero LP (none adjudicated): (a) BA reserve holding — BAL-002-WECC contingency
  (3 % load + 3 % generation, half spinning) + regulation per member BA, held on its own thermal/hydro (there is NO NWPP
  reserve design; iso_configs._nwpp_config docstring says a design is "a later card's work"); quantify the headroom it
  implies at SNV/EAST against the 0.25–0.35 loading gap BEFORE building; (b) WEIM base-schedule / resource-sufficiency
  structure (each BA balances native load on bilateral base schedules; WEIM trades imbalance only); (c) Path 16 / Path C
  transfer capability (measured WEIM transfers NEVP->IPCO 0.53–0.66 TWh/yr vs model SNV->INLAND 2.4 TWh; PACE->IPCO
  measured max 2,185 MW vs 1,250 MW rating). Check the measured-data constraints first (no public NWPP AS prices).
- Not adopted: Lake Side capability (~150 MW above CAMPD p99; cc_capacity_reconcile not armed for NWPP).
Then, if a lever is admissible: card it, add the default-off key + matrix row + a cell in every shard + tests, write the
PRECOMMIT, and run 7 shards. Copy docs/records/nwpp/nwppnext27/shards/shard_<Y>.txt (substitute pin, --set keys,
scenario-diff allowance — INCLUDE ('zonal_loss_demand_reconciliation', None, False) and anything else main added since
the keeper solved, expected zonal demand, replay source nwppnext27_span); CHECK that the generated prompt names an
EXISTING bundle dir at the pin before launching. Then compose (scripts/probes/_nwpp42_compose_span.py), extend
scripts/gen_nwppnext27_attestation.py, run dashboard_add_run --no-prune and the verdict diff vs the keeper
(calibration_verdict.py --run-id <id> --json, both runs), and put the promotion on ONE owner card.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext26.
- NEXT-27: CC part-load / incremental heat rate (IHR below average; would make the bands cheaper); CC commitment
  (online hours match CAMPD); Path 76 (now K, served).

PROCEDURE GOTCHAS
- Shard wrapper prompt: create_session with source_revision = the PROMPT commit, and a short prompt telling the shard to
  `git show <prompt-sha>:docs/records/nwpp/<lane>/shards/shard_<Y>.txt` and follow it. NEXT-27's shards finished in
  17–73 min (2019 is the slow one); six of seven stopped on the unlisted zonal_loss_demand_reconciliation tuple until
  ruled — put every new default-off main field in the allowance up front.
- promote_keeper preflight needs the clean data: `scripts/regenerate_clean.py --solve-profile NWPP` and
  `scripts/data/curate_transfer_interface_limits.py --isos NWPP CAISO` before it (and curate_hydro_plant_modes /
  curate_coal_stocks). It does NOT rewrite keepers/NWPP.json `superseded` — do that by hand (former_keeper + reason,
  prior entry into promotion_note PRIOR), then `audit_keepers.py --iso NWPP --check`.
- Ad-hoc probes and the attestation need PYTHONPATH=src:.; the attestation chain `git show`s 909cdd30 (fetch first).
- Parent: extract legs with `git archive <sha> results/calibration/<leg> | tar -x` into the scratchpad; move staged legs
  out of results/calibration before promote_keeper.
- Merging main mid-lane: mechanism-matrix.js conflicts are anchor-digit churn — take main's file, re-insert your row,
  run check_mechanism_matrix.py --fix-anchors.
- Tell shards: no legitimacy_diagnostics or scorer; push without asking; launch the solve ONCE.

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now: claude/nwppnext27-2019 … -2025 and claude/nwppnext27-pin (keeper legs; the committed keeper bundle
  carries the hourly/ sidecars; dispatch/ and unit_hourly are on these branches — delete once a byte replay is no longer
  needed); claude/nwppnext27 (after merge); claude/nwppnext26, claude/nwppnext26-2019 … -2025, claude/nwppnext26-pin
  (superseded keeper legs); claude/nwppnext25* and every branch listed in HANDOFF-nwppnext25/26.
```
