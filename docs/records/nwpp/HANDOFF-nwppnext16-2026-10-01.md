# HANDOFF — NWPP-NEXT-16 (from NWPP-NEXT-15, session 01VviGf2)

This handoff supersedes levers 0–2 of `HANDOFF-nwppnext15-2026-09-30.md` (written by the parallel NEXT-14 lane): this
session built levers 1–2 and solved lever 0's alternative. The fenced block is the next session's prompt, verbatim.

```
SESSION NWPP-NEXT-16 — NWPP calibration: the COMBINED keeper run on pin (+ captive-mine arm)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 19, 21, 23, 24, 26, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01VviGf2wemHZyFrirToW7ye (NWPP-NEXT-15).
  Safe means: its PR has merged on main (PR #6947), and get_session shows it idle.
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

FIRST: CHECK FOR A PARALLEL LANE. Two NEXT-14 sessions ran the same handoff and collided: both promoted a "keeper #19",
and one deleted a field the other's keeper armed. The other lane also wrote HANDOFF-nwppnext15-2026-09-30.md, and may
have launched its own NEXT-15 session.
- Before any solve, list sessions and `git ls-remote --heads origin 'claude/*nwpp*'`, and check for open NWPP PRs.
- If another live NWPP session is working the same lever, put that on an owner card before spending LP.

STATE ON MAIN
- Keeper #19: 2026-09-30-nwppnext14-clark-hr-bridger (bundle results/calibration/nwppnext14_span, 2019–2025).
  Recipe: keeper #18 + eia923_cc_family_heat_rates + campd_unit_fuel_split (per-unit).
  NOT-YET on {dispatch_corr}, ONE record: C4 coal 2023 r 0.670 / NRMSE 0.317. Price UNSCORED. Solved OFF-PIN
  (highspy 1.15.1 etc.; requirements.txt pins 1.14.0 / pandas 3.0.3 / pyarrow 24.0.0 / pydantic 2.13.4).
- New, default-off, zero-LP, never solved:
  - coal_captive_marginal_fuel_price (owner "Build, no threshold"): at mixed-source coal plants the econ/peak tranches
    take the EIA-923 Page-5 non-captive price. Census: Bridger econ −$9.1/MWh in 2023, −$2–5 in 2019–21/2024, +$1.0
    in 2022; Hunter 2022 +$6.2 and Huntington 2019 −$7.6 on <1 % of volume; 2025 untouched (no Page-5 file).
  - unit_outage_dispatched_bin_live_denominator (sub-gate of unit_outage_dispatched_bin_denominator; coal-only
    wefor_residual scoping behind the same flag). It does not reach Bridger.
- Read first:
  - docs/handoffs/RESULT-nwppnext15-vintage-denominator-2019-2025-2026-09-30.md (head-to-head vs #19)
  - docs/handoffs/HANDOFF-nwppnext15-2026-09-30.md (the parallel lane's handoff: its PROCEDURE, hard stops and
    PARENT GOTCHAS are the template — use them)
  - docs/handoffs/PHASE0-nwppnext15-captive-mine-2026-09-30.md
  - docs/handoffs/FINDING-nwppnext14-bridger-and-clark-phase0-2026-09-30.md
  - docs/calibration-log/nwpp.md (both NEXT-14 entries + NEXT-15), mechanism-matrix/NWPP.js, matrix doc §5.9

TASK 1 — THE COMBINED RUN (owner, 2026-10-01: "should they be combined … handoff to the next session to do the combined
run as new keeper")
- Arm C = keeper #19 with campd_unit_fuel_split → false and campd_per_unit_vintage_denominator → true. Keep
  eia923_cc_family_heat_rates. The selector refuses both Bridger fixes at once (rule 19).
- Why: NEXT-15 solved the vintage denominator with the Clark fix, and it tied #19 on every gate (0 status changes;
  C4 within ±0.007). It is structurally broader: it also repairs North Valmy 8224's must-run (212.45 → 127.89 MW).
- If C is promoted, DELETE the per-unit fuel-split path (rule 26), as HANDOFF-nwppnext15 lever 0 says.
- Optional Arm D = C + coal_captive_marginal_fuel_price. Solve it in the same batch only if an owner card says so;
  each arm is 7 shards.
- SOLVE ON PIN (owner card 2026-10-01 "Merge now, fix recipe"):
  - Every shard prompt runs `pip install -r requirements.txt && pip install -e . --no-deps`.
  - Add a STEP-1 hard stop that prints highspy / pandas / pyarrow / pydantic and must match requirements.txt.
  - In G-DRIFT, classify the library change against #19 as LIVE. C differs from #19 only in the Bridger key, so the
    C-vs-#19 diff also carries the library drift. State that in the RESULT, and measure the drift if it is cheap (e.g.
    one control year of #19 on pin).
- Write a fresh PRECOMMIT on keeper #19's recipe, with the template and PARENT GOTCHAS from HANDOFF-nwppnext15.
  - Do NOT reuse docs/handoffs/nwppnext14/shards/* (they arm the deleted cc_subfloor field).
  - Use NEW out-dirs and branch names (e.g. nwppnext16c_<Y>, claude/nwppnext16-<Y>), and check with
    `git ls-remote` that they are free. NEXT-15 lost a launch to a name collision.
- Retrievability (rule 34(d)), compose (2023 leg first), diagnostics, attestation (wrap
  scripts/gen_nwppnext14_attestation.py), dashboard_add_run --no-prune, and a verdict diff per record vs #19.
- Promotion and prune approval go on one owner card. Rule 35 (year set, then audit_keepers between promote and
  prune), re-stamp the §5.9 header, and update the matrix cells (vintage denominator, fuel split, and captive mine if
  D runs).

TASK 2 — OPTIONAL, owner card first: the live-capacity denominator arm (five keys:
- unit_outage_dispatched_bin_denominator;
- unit_outage_dispatched_bin_live_denominator;
- wefor_residual_short_screened_coal;
- wefor_residual_groups = coal classes;
- wefor_residual = 0.0).
The parent flag's NWPP cell is R, a verdict given before the live sub-gate existed. That is a rule-1 question for the
card.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext15.
- Bridger Feb–May 2023 inventory conservation (outcome pin, rule 13); offer-multiplier tuning on C1 / C4 / CT.
- Clark's CC heat rate (settled at #19). cc_subfloor_eia923_heat_rates is DELETED; do not re-add it.
- A minimum non-captive share for the captive-mine flag (owner ruled "no threshold").
- The benchmark fossil reconcile is the scorer lane's.

KNOWN ISSUES on main (not NWPP's; report, do not fix)
- FR-22 parity is red for CAISO: caiso_eia930_clock_repair and caiso_tac_shares_standard_time have no
  forecast_parity_registry declaration.
- Fast-tier failures from other lanes: golden-manifest ERCOT provenance, the d53/d60/ccs pinned cache keys, the
  bare-COAL subtests, the gas_offer_zonal_anchor_vintage drift, and the off-pin keepers (NWPP #19, NYISO).

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Leftover branches: claude/nwppnext13-2019 … -2025, claude/nwppnext14, claude/nwppnext14-2019 … -2025,
  claude/nwppnext15-2019 … -2025, claude/charming-gates-b7riij, and every claude/nwppnext16-<Y> shard branch after
  TASK 1 lands.
```
