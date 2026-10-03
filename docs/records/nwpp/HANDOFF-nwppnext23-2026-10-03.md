# HANDOFF — NWPP-NEXT-24 (from NWPP-NEXT-23, 2026-10-03)

```
SESSION NWPP-NEXT-24 — NWPP calibration: COI economic depth + re-solve on the new coal-stock / nuclear data, keeper 2026-10-03-nwpp-next-23-coi
DATA PROFILE: nwpp (plus data/raw/caiso-trns-usage — the CAISO token keeps it out of the nwpp sparse profile)
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 16, 19, 20, 21, 24, 25, 26, 28, 29 and 31–36.
The parent never solves (rule 32). Every backcast year gets its own shard (rule 36).

Read first: docs/records/nwpp/RESULT-nwppnext23-coi-pnw-basis-2026-10-03.md (incl. §Promotion) and
docs/records/nwpp/FINDING-nwppnext23-price-level-phase0-2026-10-03.md (§B decomposition, §E measured flow-vs-spread).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01KhvMnwAnBWJ47mPg92eAJk (NWPP-NEXT-23).
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
by send_message before launching shards, and do not run promote_keeper.py until it hands you the slot.

STATE ON MAIN
- Keeper: 2026-10-03-nwpp-next-23-coi (bundle results/calibration/nwppnext23_span, 2019–2025, legs at pin
  33dc564771e1006ce69ffd2789053107ed4801cc): the NEXT-22b recipe on the roster-free plant-basis anchor +
  nwpp_coi_pnw_delivery_basis (COI export leg priced (band − 5)/1.05, CAISO's PNW_midC basis). Replay:
  `replay_keeper.py results/calibration/nwppnext23_span --years Y`.
- Rubric: NOT-YET. FAIL records (10): fuelmix CC_REGULAR 2019 +11.94 / 2024 +14.80 / 2025 +8.02 TWh; C4 gas 2019 r 0.657,
  2023 0.533, 2024 0.791; C3a 2023 −11.6 % / 2024 −27.9 %; C3b 2023 0.225 / 2024 0.791. PASS of note: C4 coal every year,
  C3a 2025 −1.6 %, C3b 2025 0.127, D-2/C6, D-1 fails 14.
- Priced seams TWh model/measured: COI 11.75/7.03, 14.90/15.26, 15.37/12.11, 17.02/12.50, 4.95/1.13, 10.46/2.15,
  6.91/3.03; BC 2023–25 17.64/9.48, 13.27/7.51, 4.90/2.77; NEVP 2023–25 4.25/7.56, 9.22/9.08, 5.75/9.40.

LIVE DATA DRIFT SINCE THE KEEPER'S LEGS (both on main, neither in the keeper; this lane's solve carries them)
- #7134 EIA-923 coal stocks 2015–17 (9f2fe6df): NWPP yard maxima rise in 65 plant-years (Boardman 400→999 kt,
  Bonanza 511→1,013, Valmy 8224 456→765, 3845 1,014→1,396) — the take floor / monthly pile read S_max over years ≤ Y−1.
- SolveEpoch 2026-10-03b: NWPP 2019–2022 NUCLEAR_MONTHLY_CF_BY_YEAR rows (Columbia; owner ruling R-35).
Any NWPP solve now differs from the keeper by these two inputs. Measure their effect: either (a) one control-free
7-shard replay of the keeper recipe at main HEAD (a rule-14 data re-solve, promotable on structure), or (b) fold them
into the depth arm's span and attribute with a zero-LP decomposition. Card the choice.

TASK — the regressions are gas filling an over-exporting COI/BC. The hurdle is now aligned (NEXT-23). What is left is
the DEPTH: measured CISO-leg flow saturates at ~600–800 MW (BC ~1,400–1,700) at any spread, while the LP exports at the
cap (COI 2,800–5,100 MW measured caps) once the spread clears the hurdle (FINDING-nwppnext23 §E).
1. Zero-LP phase 0: find a FORWARD-REPRODUCIBLE driver of the economic depth (rule 13 — never an envelope sized on the
   measured flow). Candidates to test, in order:
   - CAISO OASIS TRNS_USAGE DAM schedules on MALIN500/CASCADE (data/raw/caiso-trns-usage): the OTC already committed to
     non-economic schedules (ETCs / TORs / firm imports) — is OTC minus the firm/ETC share the economic headroom?
     The schedule is an outcome; an ETC/TOR reservation is a contract (forward-admissible). Separate the two.
   - CAISO's own firm-import representation (CAISO_FIRM_IMPORT_TRANCHES, PNW_hydro_base): is part of the COI flow
     already a contracted block on CAISO's side (rule 19 — one representation)?
   - BPA's own load-service obligation on the intertie (the 1.6–2× COI-path vs CISO-leg ratio, FINDING-nwppnext22 §C).
   Price-taker re-run (probe _nwppnext23_price_level_phase0.py §D) per candidate. Card the lever before any registry change.
2. Or, if no admissible depth driver exists: card closing the seam lane and pivoting to C3a 2024 (−27.9 %; the NW
   price is the hydro water value — hydro is marginal in 99.7 % of NW/OR unit-hours, FINDING-nwppnext23 §C).
3. Then: default-off key + matrix row + a cell in every shard + tests; PRECOMMIT; 7 shards (copy
   docs/records/nwpp/nwppnext23/shards/shard_<Y>.txt; update the pin, replay source nwppnext23_span, the --set key,
   and hard stop (d)'s demand frame if the anchor moved); compose (scripts/probes/_nwpp42_compose_span.py),
   gen attestation (scripts/gen_nwppnext23_attestation.py is the base to extend), dashboard_add_run --no-prune,
   verdict diff vs the keeper, ONE owner card on promotion.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext22.
- NEXT-23: the NW price level as such (anchor vs MALIN: +$2–4 in export hours; NW model vs WEIM benchmark: +$1–4); the
  CARB unspecified GHG wedge on NW→CA exports (H1 — refuted by the measured $0–5 zero crossing and CAISO's EF-0 PNW
  tranches; inverts NEVP); the COI PNW delivery basis (K, in the keeper).
- NEXT-22: seam headroom (CAISO 2/3 share of COI, BPA BC Intertie limit). NEXT-21/20/19 as before.

PROCEDURE GOTCHAS
- Shard prompts: the shard checks out the PIN; give it a SHA where its prompt file lives and have it `git show` the file
  (NEXT-23 pattern). A shard can sit PENDING for 45+ min without starting — archive and relaunch it.
- Pin new solves to main HEAD + your code (preflight 0d). Parent venv: `uv sync` (python-calamine is now a dependency).
- Parent: move staged legs out of results/calibration before promote_keeper (parity sweeps every bundle dir);
  copy the legs' dispatch/<Y>_P1*.parquet into the span's gitignored dispatch/ for preflight.
- Tell shards: no legitimacy_diagnostics or scorer; push without asking; launch the solve ONCE.

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now: claude/nwppnext23-2019 … -2025 and claude/nwppnext23-pin (keeper legs; the committed keeper bundle
  carries hourly/ sidecars; dispatch/ + unit_hourly are on these branches — delete once the owner no longer needs a
  byte replay), claude/nwppnext22b-2019 … -2025, claude/nwppnext22b-pin, claude/nwppnext22, claude/nwppnext23 (after
  merge), claude/closeout-nwpp-anchor, plus the NEXT-20/21/22 branches listed in HANDOFF-nwppnext22.
```
