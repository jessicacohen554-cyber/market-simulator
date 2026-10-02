# HANDOFF — NWPP-NEXT-22 (from NWPP-NEXT-21, 2026-10-02)

```
SESSION NWPP-NEXT-22 — NWPP calibration: seam headroom for the priced interface (NWPP-56), keeper #20
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 16, 19, 20, 21, 24, 25, 26, 28, 29 and 31–36.
The parent never solves (rule 32). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01LP9kkHDK9XimFi6RRJJmfQ (NWPP-NEXT-21).
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
If another live NWPP session works the same lever, put that on an owner card before spending LP. The close-out W0
lane owns claude/w0-nwpp-* (EIA-860 settlement re-solves): not yours, but if W0 lands a new NWPP keeper basis, the
next re-solve must start from it. Re-check whether the CAISO lane has ruled on card N4 / R-a (Path 66's 4,800 MW on
both sides) — still unruled at NEXT-21, and NEXT-21's headroom evidence bears on it (below).

STATE ON MAIN
- Keeper #20 unchanged: 2026-10-01-nwppnext16c-combined-vintage (bundle results/calibration/nwppnext16c_span, 2019–2025,
  pin 33014efc). Under today's rubric (R-9 landed: 2023–25 price scored against the WEIM ELAP benchmark) it is
  NOT-YET on fuelmix (CC_REGULAR 2025 +9.6 TWh), price_mean / price_shape (2023 −21.4 % / NRMSE 0.303; 2024 −27.7 % /
  0.676) and dispatch_corr (C4 coal 2023 r 0.669 / NRMSE 0.313).
- NEXT-21 (read first): docs/records/nwpp/RESULT-nwppnext21-priced-interface-2026-10-02.md and its PRECOMMIT.
  The priced interface solved all 7 years. Owner card: "Hold #20, fix seam headroom". Matrix cells
  reference_price_interface / priced_interchange = O.
  - Structural gate PASS (signs + hourly r > 0); D-2/C6 PASS; D-1 failures 22 -> 14.
  - Gains: C4 coal 2023 0.781 PASS; C3a 2023 −0.3 % PASS; C3b 2023 0.182 PASS; C1 CC 2025 PASS.
  - Regressions: C4 gas PASS->FAIL 2019/20/22/23/24 (2023 0.781 -> 0.465); C1 CC_REGULAR PASS->FAIL 2019/20/24
    (+10.9/+9.7/+12.5 TWh); CT_PEAKER 1.5–2.4x actual; C3b 2024 0.676 -> 0.787.
  - Root cause: priced seams export 27.7/33.3/35.2/32.7/30.2/36.8/17.1 TWh vs 6.7/18.4/20.7/21.1/18.2/18.7/15.2
    measured (COI 2024 17.4 vs 2.2; BC 2023 22.5 vs 9.5 at the limit 8,700 h), because each seam offers its FULL
    path rating (COI 4,800, NEVP 1,933, BC 3,150 MW). BC<->CA wheel 3,034 h / 6.0 TWh (2023).
  - NEXT-21 legs by full SHA (pin 86b73d6f, replay = keeper leg + both keys):
    2019 4d6cb87ed4af3961caf6cef03db27c5bd62bf143 · 2020 7cdb53da881b400ee9f3406d610fefa181a5bed4 ·
    2021 542733eaef5b5232e3d02a5c9a83197a6ddef473 · 2022 876d4faa32cf580848b4fa763ea51b319ad96932 ·
    2023 3f52175627fcda2c1cf1c3b093ea96929413319c · 2024 8ffeaed04b7bdf5a1c79b794f6f9121574ab772c ·
    2025 3d36a7b093469538892363af1a7d0ce2d6f8fbf1
    (shard branches claude/nwppnext21-<Y> — they are transport, not storage; fetch by SHA while they exist).

HEADROOM EVIDENCE (NEXT-21, zero LP; RESULT §"Headroom evidence")
- CAISO OASIS TRNS_USAGE DAM (data/raw/caiso-trns-usage/, 2023–25; curated as clean datatype transfer-interface-limits,
  series "<ti_id>|<I|E>|<OTC|TTC|TRM|MTC>"): MALIN500_ISL import (into CAISO) seasonal TTC 3,007/3,129/3,351, hourly
  OTC mean 2,737/2,732/2,717, DAM net schedule 713/823/864 MW; COTPISO_ITC OTC 81/116/133; export direction
  MALIN500 OTC 1,710/1,851/1,893. NOB (PDCI) is NOT in CAISO_COI.
- The registered CAISO_COI 4,800 MW is Path 66's full rating; CAISO's market sees ~2,730 MW of it after derates; the
  rest is COTP/TANC capacity scheduled outside CAISO (the same fact N4 turns on).

TASK
1. Zero-LP phase 0 (FINDING): for each priced seam, the measured headroom the market had, per hour and per direction.
   - CAISO_COI: MALIN500_ISL (+ CASCADE/SUMMIT if they belong to the NW border) OTC by direction, 2023–25.
   - CAISO_NEVP: identify which CAISO ITCs carry the NEVP<->CISO leg (registered 1,933 MW = the NWPP-20 summand);
     read their OTC.
   - WECC_CAN: Path 3 (BC-US) — find a free measured hourly/seasonal transfer capability (BPA OASIS ATC/TTC, WECC
     path rating catalog); the CAISO feed does not cover it.
   - 2019–2022: OASIS retention starts 2023 for TRNS_USAGE. State what measured basis exists for 2019–22 (seasonal
     TTC? the same TI_IDs in older OASIS queries?) and put "headroom only in measured years vs seasonal TTC elsewhere"
     on an owner card (the BC anchored-years precedent).
   - Rule 13 test, stated in the FINDING: OTC/TTC is an operating-condition input (derates, like outage windows),
     forward-reproducible as the seasonal TTC; NEVER the measured flow or schedule (that would pin the answer).
   - Price-taker re-run of NEXT-20 §D with the measured limits: do the seams' price-taker exports fall toward measured?
     Report per seam/year. If they do not, the overshoot is a price-level problem, not headroom — card it.
2. Registry: hour-varying seam limits from the measured OTC (default-off key; matrix row + a cell in EVERY shard,
   CI check_mechanism_matrix.py), only after the phase-0 card. Tests first (trivial 1-zone/24-h cases).
3. PRECOMMIT, new pin (= main with the code), G-DRIFT vs 33014efc, 7 shards (one per year) replaying keeper #20's legs
   with --set reference_price_interface=true --set priced_interchange=true --set <headroom key>=true.
   BOTH interface keys are required: replay_keeper routes priced_interchange as its own kwarg and keeper #20's meta
   records false; with only reference_price_interface the solve rebuilds the keeper.
   Copy NEXT-21's shard template (docs/records/nwpp/nwppnext21/shards/shard_<Y>.txt; parent tells each shard to read its
   file with `git show FETCH_HEAD:<path>` from the parent branch): STEP-1 zero-LP construction line, hard stops, the
   arm demand frame (native + served residual): 272.855 / 274.573 / 268.646 / 277.900 / 262.091 / 271.477 / 287.331 TWh.
4. Compose, score, register (probe), diff calibration_verdict per (criterion, year, key) against keeper #20 AND
   against NEXT-21 (scripts/gen_nwppnext21_attestation.py is the attestation wrapper — extend it with the headroom
   key). One owner card on promotion + prune.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext20.
- NEXT-21: the priced interface on full path ratings (solved, held — do not re-solve it unchanged).
- NEXT-20: WECC_SW as a priced seam; the pooled NWPP_external bus; the Mid-C Peak anchor; a gas-scaled BC price 2019–22.
- NEXT-19: gas_daily_shape for NWPP (R). NEXT-18: hydro_budget_period_by_instrument. NEXT-17: Bridger seasonal offer.
  NEXT-16: captive-mine price, live-capacity screened-coal WEFOR, offer-multiplier tuning on C1/C4/CT.

PROCEDURE FOR ANY SOLVE (PARENT GOTCHAS, NEXT-15/16/19/21)
- Shard setup: `pip install --ignore-installed pyyaml==6.0.3 && pip install -r requirements.txt && pip install -e . --no-deps`;
  STEP-1 hard stop prints highspy/pandas/pyarrow/pydantic = 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4.
- Tell every shard: do NOT run legitimacy_diagnostics or any scorer; push without asking.
- Stage legs: `git checkout <sha> -- <leg dir>` then `git rm -r -q --cached <leg dir>`; gitignore the family.
- Compose: scripts/probes/_nwpp42_compose_span.py --skip-diagnostics (2023 leg first); legitimacy_diagnostics.py --bundle B
  --iso NWPP --years 2019 … 2025 --json-out B/legitimacy_diagnostics.json; attestation (the chain reads ancestor commit
  909cdd30 — `git fetch origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943` first if it is missing);
  dashboard_add_run.py --no-prune; calibration_verdict.py --run-id <id> --json for every compared run.
- Promotion + prune on ONE owner card; rule 35 (promote_keeper.py; audit_keepers --iso NWPP; prune_iso_runs.py --iso NWPP;
  re-stamp §5.9 and the matrix keeper/gates; check_forecast_parity NWPP UNACCOUNTED 0). Rule 15: promote_keeper.py
  preflight derives unit_marginal_<Y>.parquet; keeper #20 lacks it (do not backfill outside a promotion).
- A rejected/held probe: remove its registry sidecar + runs/<id>.js, revert bench parts; never commit the span bundle.
- Never `ln -sf` onto a system path.

KNOWN ISSUES on main (not NWPP's; report, do not fix)
- Fast lane under the nwpp sparse profile: ~211 failures, other ISOs' data absent; two pre-existing code failures on main
  (tests/iso/spp/test_spp_mmu_offer_unavailability.py::TestAvailabilitySeam::test_bands_after_overlays,
  tests/unit/data/test_local_capacity.py::TestLocalCapacityT5RhsBuilder::test_rhs_clips_to_zero_below_the_import_cap).
- FR-22 parity red for CAISO; tests/unit/data/test_gas_offer_zonal_anchor_vintage.py (2 tests).

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now: claude/nwppnext20 (merged). claude/nwppnext20-pin: keep while the NEXT-21 legs are the reference
  (they are pinned to it); deletable once NEXT-22 has a new pin and the owner no longer needs NEXT-21 replayable.
- claude/nwppnext21-2019 … -2025: shard transport; deletable once the owner rules NEXT-21's legs need not survive
  (they are the held arm's only copy — rule 31).
- claude/upbeat-bell-4p8c9c (NEXT-21's lane branch): deletable after its PR merges.
```
