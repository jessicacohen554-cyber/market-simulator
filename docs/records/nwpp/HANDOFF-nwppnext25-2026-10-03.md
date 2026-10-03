# HANDOFF — NWPP-NEXT-26 (from NWPP-NEXT-25, 2026-10-03)

```
SESSION NWPP-NEXT-26 — NWPP calibration: residual CC_REGULAR over-run / C4 gas (phase 0 first), keeper 2026-10-03-nwpp-next-25-served
DATA PROFILE: nwpp (plus data/raw/caiso-trns-usage — the CAISO token keeps it out of the nwpp sparse profile)
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 16, 19, 20, 21, 24, 25, 26, 28, 29 and 31–37.
The parent never solves (rule 32). Every backcast year gets its own shard (rule 36).

Read first:
- docs/records/nwpp/RESULT-nwppnext25-served-schedule-2019-2025-2026-10-03.md (incl. §Promotion)
- docs/records/nwpp/FINDING-nwppnext25-cc-served-schedule-phase0-2026-10-03.md
- docs/records/nwpp/FINDING-nwppnext25-scarcity-phase0-2026-10-03.md (C3a tail days CLOSED)

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_0176bv4hLEFeoeeqAhchxXgr (NWPP-NEXT-25).
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
close-out desk (session_01ALecU5Wjde4tkbLrnMExT9) was ARCHIVED during NEXT-25: there is no desk to serialise the NWPP
promotion slot, so put the promotion on an owner card (NEXT-25 did, owner answered "Promote"). If a new desk session
exists (list_sessions), send it your session id, branch and pin by send_message first.

STATE ON MAIN
- Keeper: 2026-10-03-nwpp-next-25-served (bundle results/calibration/nwppnext25_span, 2019–2025, legs at pin
  d3965589f5d0b400e05560380de64d49ae0c6959): keeper NEXT-24 recipe + nwpp_served_schedule_zonal_attribution (the
  served schedule's measured EIA-930 per-DIBA legs at each reporting member's zone). Replay:
  `replay_keeper.py results/calibration/nwppnext25_span --years Y`.
- Rubric: NOT-YET. FAIL records (8): fuelmix CC_REGULAR 2019 +12.73 / 2024 +12.77 TWh; C4 gas 2019 r 0.649, 2023 0.533,
  2024 0.797 (NRMSE 0.316); C3a 2024 −25.3 %; C3b 2023 0.209 (0.009 over the band) / 2024 0.772. PASS of note: C3a 2023
  −3.2 % and 2025 +0.3 %; CC 2020 +7.51 (band 8.00 — close), CC 2025 +6.82; C4 coal every year; D-2/C6. D-1 fails 16.
- Price is unscored 2019–2022 (WEIM benchmark starts 2023-06, owner ruling R-9).

TASK — the residual CC_REGULAR over-run (2019, 2024) and C4 gas, phase 0 first.
NEXT-25 moved the served schedule to the right zones: SNV gas fell 1.7–7.7 TWh toward NEVP EIA-930, and COI/BC
exports fell. The footprint CC total moved only −2.3…+0.8 TWh. SNV's freed capacity now leaves through the NEVP
seam: 2019 10.47 vs −0.30 measured, 2020 11.98 vs 3.11. The surplus is priced at the seams. Open questions,
zero LP first:
1. The NEVP seam (CAISO_NEVP), 2019–2022. It keeps a registered 1,933 MW rating with no published limit, and its
   reference price is CISO net load. Why does model SNV export 10–12 TWh into CAISO in 2019–20 when NEVP measured
   ~0–3? Check the NEVP seam's reference price vs measured (CAISO SP15 / PALOVRDE in data/raw/_validation-source/
   wecc_intertie_lmp_hourly_CAISO.parquet).
2. CC capacity factor. CC sits at 0.87–0.91 of available capacity with mc $16–22 under a ~$29 price
   (FINDING-nwppnext25-cc §A). Even at the MEASURED NW price a price-taker CC runs ~67 TWh vs 57 actual
   (FINDING-nwppnext19 §3). So part of the gap is supply-side: availability (CAMPD outages), heat rates, the delivered
   gas basis per plant. Do not reopen anything in the CLOSED list.
3. D-1 rose 13 → 16 (2019 COAL_BIT, 2022 CT_PEAKER, 2022 ST_GAS). Read before choosing a lever.
Then, if a lever is admissible: card it, add the default-off key + matrix row + a cell in every shard + tests, write the PRECOMMIT,
and run 7 shards. Copy docs/records/nwpp/nwppnext25/shards/shard_<Y>.txt; update the pin, the --set key, the
scenario-diff allowance and the expected zonal demand. The replay source is nwppnext25_span; CHECK that the generated
prompt names an EXISTING bundle dir before launching. Then compose (scripts/probes/_nwpp42_compose_span.py), extend
scripts/gen_nwppnext25_attestation.py for the attestation, run dashboard_add_run --no-prune and the verdict diff vs
the keeper, and put the promotion on ONE owner card.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext24.
- NEXT-25: C3a tail-day scarcity pricing (WEIM RSE / PBC penalty, BAL-002-WECC-3 contingency reserve, hydro capability
  in cold snaps, CA citygate daily fuel — FINDING-nwppnext25-scarcity-phase0). energy_reserve_coopt stays U with a
  zero-LP inert estimate.
- NEXT-25: the served-schedule zonal placement (now K in the keeper).

PROCEDURE GOTCHAS
- Shard prompts: the shard checks out the PIN. Give it a SHA where its prompt file lives and have it `git show` the file
  (pin commit + separate prompt commit). Shards sit PENDING 30–45 min: archive and relaunch (2025 needed three launches
  in NEXT-25).
- Never `sed` the run prefix across the prompt templates; the replay source dir must stay the keeper's. Grep the
  generated prompts for the replay dir and `ls` it at the pin.
- The attestation chain `git show`s 909cdd30 (an old nwpp49 attestation). In a shallow clone, run
  `git fetch origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943` first.
- Ad-hoc probe scripts run from outside the repo need PYTHONPATH=src:. (scripts.lib.clean_io).
- Parent: extract legs with `git archive <sha> results/calibration/<leg> | tar -x`. Move staged legs out of
  results/calibration before promote_keeper (parity sweeps every bundle dir). Do NOT put results/calibration patterns
  in .git/info/exclude: it silently drops the keeper bundle from the promotion commit.
- promote_keeper needs --attested-by "<lane>; owner card '<ruling>'; <date>".
- nwpp_seam_measured_limits needs `scripts/regenerate_clean.py transfer-interface-limits` before a zero-LP probe can
  read the limits.
- Tell shards: no legitimacy_diagnostics or scorer; push without asking; launch the solve ONCE.

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now:
  - claude/nwppnext25-2019 … -2025 and claude/nwppnext25-pin (keeper legs; the committed keeper bundle carries the
    hourly/ sidecars; dispatch/ and unit_hourly are on these branches — delete once the owner no longer needs a byte
    replay);
  - claude/nwppnext25 (after merge);
  - claude/nwppnext24, claude/nwppnext24-2019 … -2025, claude/nwppnext24-pin (superseded keeper legs);
  - every branch listed in HANDOFF-nwppnext24.
```
