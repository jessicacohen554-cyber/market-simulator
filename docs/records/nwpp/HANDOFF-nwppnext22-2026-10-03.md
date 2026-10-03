# HANDOFF — NWPP-NEXT-23 (from NWPP-NEXT-22, 2026-10-03)

```
SESSION NWPP-NEXT-23 — NWPP calibration: the NW price level against the seam anchors, keeper 2026-10-03-nwpp-next-22b-w0
DATA PROFILE: nwpp (plus data/raw/caiso-trns-usage: the CAISO token keeps it out of the nwpp sparse profile — a blobless
lane must hydrate that one directory too; a full clone already has it)
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 16, 19, 20, 21, 24, 25, 26, 28, 29 and 31–36.
The parent never solves (rule 32). Every backcast year gets its own shard (rule 36).

Read first: docs/records/nwpp/RESULT-nwppnext22-seam-headroom-2026-10-02.md (both runs; §W0 is the keeper) and
docs/records/nwpp/FINDING-nwppnext22-seam-headroom-2026-10-02.md (§D: the price-level routing).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01HJgvj9S6mHN2q6P2XKxDFk (NWPP-NEXT-22).
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
If another live NWPP session works the same lever, put that on an owner card before spending LP.
The backcast close-out desk (session_01ALecU5Wjde4tkbLrnMExT9) chartered an NWPP anchor lane under owner ruling R-28
("Keep old figures, fix later"): decouple nwpp_demand_plant_basis (data/raw/reference/nwpp_plant_basis_energy.csv,
derived from bench classFull) from the roster-dependent bench parts, re-derive it, re-solve NWPP on the current keeper.
It does not touch the seam code and serialises promotions with you. Coordinate with it by send_message before any
promotion; the NWPP bench parts stay at main's render (R-28) — revert any re-render a registration makes.

STATE ON MAIN
- Keeper: 2026-10-03-nwpp-next-22b-w0 (bundle results/calibration/nwppnext22b_span, 2019–2025, legs at pin
  2b8da72a979f5e5f1a29a82ffc752bee65677c02): the W0 fix-2 recipe + reference_price_interface + priced_interchange +
  nwpp_seam_measured_limits. Replay: `replay_keeper.py results/calibration/nwppnext22b_span --years Y` (preflight 0d clean
  at promotion; legs carry the registered-after-solve key spp_mmu_offer_repair None->False, SPP-only, inert).
- Rubric: NOT-YET. FAIL records (10): fuelmix CC_REGULAR 2019 +12.69 / 2024 +15.39 / 2025 +8.74 TWh; C4 gas
  2019 r 0.661, 2023 0.538, 2024 0.796; C3a 2023 −10.4 % / 2024 −27.1 %; C3b 2023 0.216 / 2024 0.789.
  PASS of note: C4 coal every year (2023 0.770), C3a 2025 −0.4 %, C3b 2025 0.127, D-2/C6, D-1 fails 14.
- Priced seams (TWh, model / measured): sum 22.9/6.7, 27.8/18.4, 27.6/20.7, 26.5/21.1, 28.2/18.2, 34.4/18.7, 19.0/15.2;
  COI 2023/24/25 6.57/1.13, 12.42/2.15, 9.03/3.03; BC 2023 17.59/9.48. Caps bind (COI at export cap 2,800–5,100 h/yr).

TASK — the regressions are gas filling an over-exporting COI/BC seam. Headroom is fixed at measured limits; what is
left is the PRICE LEVEL: the NW price sits $2–35/MWh below the seam anchors (NEXT-20 FINDING §D), so at price-taker
the seams export at the cap.
1. Zero-LP phase 0 (FINDING): decompose the NW-vs-anchor gap per seam/year/hour on the KEEPER's own prices:
   - the anchor construction (annual mean MALIN / BCHA ELAP ÷ (HH + basis) × CAISO net-load shape): is a flat annual HR
     on an hourly net-load shape over-pricing CAISO's shoulder/night hours relative to the measured MALIN hourly LMP?
     Compare the registered anchor price series hour by hour against the measured MALIN / ELAP_BCHA LMP (they are the
     anchor's own source; using the measured hourly series AS the price would be an overlay — say which forward
     analogue exists before proposing it, rule 13);
   - the hurdle (3.0 / 2.0 $/MWh): measured wheeling + losses + GHG (CARB border adder on NW→CA imports? WECC_PNW's
     side registers 3.0) — a structural input, never sized to the residual;
   - the NW side: which NW class sets price in the export hours (hydro water value vs gas), from the keeper's
     unit_marginal layer (committed for every year).
   Price-taker re-run (scripts/probes/_nwppnext22_headroom_phase0.py §D construction) for each candidate. Card the
   lever before any registry change.
2. If a lever is admissible: default-off key, matrix row + a cell in every shard (CI check_mechanism_matrix.py), tests
   first; PRECOMMIT; 7 shards replaying the keeper span with --set <key>=true (copy
   docs/records/nwpp/nwppnext22/shards_w0/shard_<Y>.txt; allow spp_mmu_offer_repair in hard stop (a)).
3. Compose (scripts/probes/_nwpp42_compose_span.py, 2023 first), legitimacy_diagnostics, attestation
   (scripts/gen_nwppnext22_attestation.py --basis w0 is the base to extend), dashboard_add_run --no-prune, verdict diff
   vs the keeper, ONE owner card on promotion + prune.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext21.
- NEXT-22: seam headroom (CAISO share of COI = 2/3 Path 66 ownership, BPA BC Intertie limit; NEVP has no published limit
  on its boundary) — DONE and in the keeper. Do not re-litigate the COI share or re-fetch BPA OPI.
- NEXT-21: the priced interface on full path ratings. NEXT-20: WECC_SW as a priced seam; the pooled NWPP_external bus;
  the Mid-C Peak anchor; a gas-scaled BC price 2019–22. NEXT-19: gas_daily_shape (R). NEXT-18/17/16 as before.

PROCEDURE GOTCHAS (NEXT-21/22)
- A keeper solved at an old pin is NOT promotable: promote_keeper.py preflight 0d refuses a recipe that does not replay
  at HEAD. Pin new solves to main HEAD + your code (G-DRIFT then = your own diff).
- Shard setup: `pip install --ignore-installed pyyaml==6.0.3 && pip install -r requirements.txt && pip install -e . --no-deps`;
  libs 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4. Shards must curate transfer-interface-limits (--isos NWPP CAISO) before solving.
- Tell shards: do NOT run legitimacy_diagnostics or any scorer; push without asking; launch the solve ONCE (record the PID).
- The parent's container: never `git worktree add` a full checkout (7 GB, fills the disk); build pins with a temp
  GIT_INDEX_FILE + commit-tree. check_registry_payload_parity.py fails on any unregistered bundle dir under
  results/calibration — move staged legs to the scratchpad before promoting.
- Fast lane under the nwpp sparse profile shows ~217 failures from other ISOs' absent data; run the full tree or CI.

KNOWN ISSUES on main (not NWPP's; report, do not fix)
- FR-22 parity red for CAISO; tests/unit/data/test_gas_offer_zonal_anchor_vintage.py.

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now: claude/nwppnext20, claude/nwppnext20-pin, claude/upbeat-bell-4p8c9c (NEXT-21 lane, merged #7065),
  claude/nwppnext21-2019 … -2025 (NEXT-21 held arm; numbers in its RESULT), claude/nwppnext22-2019 … -2025 and
  claude/nwppnext22-pin (the pin-basis run; numbers in RESULT-nwppnext22), claude/w0-nwpp-* (W0 lane, merged #7076;
  the W0 desk's call).
- Keep until the owner rules: claude/nwppnext22b-2019 … -2025 and claude/nwppnext22b-pin (the keeper's legs; the
  committed keeper bundle carries hourly/ sidecars but not dispatch/ or unit_hourly).
```
