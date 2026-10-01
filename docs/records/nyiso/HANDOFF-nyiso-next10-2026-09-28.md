# HANDOFF — NYISO-NEXT-10 (written by NYISO-NEXT-9, 2026-09-28)

This file is the prompt NYISO-NEXT-9 launched NYISO-NEXT-10 with, committed so the chain is auditable.

```
SESSION NYISO-NEXT-10: eastern over-delivery of NYISO imports (NEXT-7 FINDING sec. 2: 4.85-7.60 TWh/yr of import lands east of Central-East that NYISO actually received in Zone A or exported to NE). Step 1 is the neighbour-price INTAKE that NEXT-7 sec. 3(c) says the identification needs; step 2 is zero-LP identification of a per-neighbour construction; a solve happens only if a zero-DOF, identified construction exists. This parent never runs an LP (rule 32); any solve is year-isolated shards (rule 36).
DATA PROFILE: nyiso
MODEL: Opus or Fable (rule 27)

FIRST (standing owner directions — do these every session and pass them to every chained handoff verbatim):
1. Archive the previous NYISO session (NYISO-NEXT-9, session_01JbpXU44vZ92MnzsqEAmjSR) once its promotion PR is confirmed merged on main. If it is still open, drive it (it is NEXT-9's promotion PR) — do not redo its change.
2. Check for any unmerged branches or PRs for NYISO; determine if anything needs to be salvaged; integrate it into your branch and close the open PRs, or state what can be deleted (a session cannot delete refs — list them for the owner). Rebase and merge.
3. When done: promote if a good candidate (per the pre-registered rule), create a PR and merge, archive every shard, and launch the next handoff to continue NYISO calibration if rubric failures remain. Give that handoff these same standing directions, including: archive its predecessor when safe, and continue the chain. If you are at the session nesting limit, make your LAST MESSAGE a complete handoff prompt that starts a new chain.
4. Any decision for the owner is presented as clickable decision cards (AskUserQuestion), NOT inline text.
5. If the lane is CALIBRATED and the rubric clears for all years, check the complete / frontier declaration criteria, settle the keeper config and clear the tasks that block the declaration; if at complete / frontier, say so in the final message so the owner can approve.

READ FIRST. CLAUDE.md is binding, especially rules 1, 13, 14, 19, 20, 21, 23, 24, 25, 28, 31, 32, 33, 34, 35 and 36.
- docs/records/nyiso/FINDING-nyiso-next7-star-node-2026-09-27.md (sec. 2 the over-delivery numbers; sec. 3 why per-neighbour routing on the NY price is REFUSED and exactly which measured series would make it identifiable)
- docs/records/nyiso/RESULT-nyiso-next9-hq-floor-2026-09-28.md (current keeper; the HQ floor is gone, nyiso_firm_imports R)
- NYISO matrix shard docs/codebase-site/data/mechanism-matrix/NYISO.js: seam_neighbour_anchored_ladder (G — do NOT re-test without the neighbour-price intake: this lane IS that intake), import_hub_pricing (K), nyiso_firm_imports (R). Lever queue: docs/mechanism-testing-matrix.md sec. 5.5 ("Queue after NEXT-9").
- The MISO/PJM spread construction (miso_pjm_lmp_import_pricing / seam_neighbour_hourly_ladder class) transfers IN KIND ONLY (rule 25): offsets are re-derived from NYISO's own flows.

STATE
- Keeper: 2026-09-28-nyisonext9-hq-floor-span (bundle results/calibration/nyisonext9_span, 2022-2025) + stamped 2021 run 2026-09-28-nyisonext9-hq-floor-2021. Determination NOT-YET.
- Load-bearing failures: C3a 2022 -11.3 %, 2025 -11.4 % (model under-prices). C3c fails, not lone. C1, C2, C3b, C4, C6, C8 PASS every year; 2021 CALIBRATED.
- The model's total import LEVEL matches measured net import; its LOCATION is wrong (Capital_Hudson imports at cap where NYISO's attributed schedule is a net export; Upstate_West under-supplied).

TASK
1. INTAKE (use the data-intake skill; network permitting — if a host is denied, read the environment.network doc and tell the owner via a decision card):
   (a) IESO Ontario hourly price (HOEP / OZP), 2021-2025;
   (b) PJM DA/RT LMP at the NYIS interface pricing node plus the Neptune / HTP / VFT source pnodes, 2021-2025;
   (c) ISO-NE DA/RT LMP at the NY external nodes (Roseton AC, Shoreham CSC, Northport 1385), 2021-2025.
   Raw under data/raw with README + SHA256SUMS, schema-first, per-ISO registry, tmp-CLEAN_DIR tests.
2. Phase 0, ZERO LP: with the intake, test whether each neighbour's hourly flow co-moves with its own SPREAD (neighbour price vs the NY landing-zone price) where it did not with the NY price (NEXT-7 sec. 3(b) Spearman table). Decide ex ante: a per-neighbour spread construction (zero DOF, offsets derived from NYISO's own flows) or STOP with a FINDING. HQ stays a proxy/economic block (no market).
3. If a construction is identified: G-DRIFT from the keeper git_sha to your HEAD, PRECOMMIT with footprint, gates and promotion rule ex ante (rule 1: promote on structure, never on C3a moving); gated ScenarioConfig field => matrix row + a cell in EVERY ISO shard (rule 28(c)).
4. Solves: one shard per registered year 2021-2025 (rules 34/36), pinned to a FULL 40-char SHA ON MAIN (a session branch can be deleted by the environment mid-lane — NEXT-9's was; push the PRECOMMIT via a PR merged to main, or re-push, before pinning). SHARD PROMPT LESSONS (NEXT-8 + NEXT-9) — include ALL of these:
   - NEVER END THE TURN while a command is running: run regenerate_clean and the solve in the background with a log and poll to completion (NEXT-9's first 2024 shard ended its turn mid-regenerate and never resumed).
   - After hydrate, run `uv run python scripts/regenerate_clean.py` (data/clean is gitignored). It continues past a failing datatype: do NOT retry or repair a failing datatype (NEXT-9's 2024 retry looped ~90 min on an emissions-unit-annual OOM); proceed to the solve and STOP only if the solve itself needs the missing input.
   - Solve with `uv run python scripts/replay_keeper.py results/calibration/nyisonext9_span --years <y> --out-dir results/calibration/<lane>_<y> --set <field>=<value>` (2021 from results/calibration/nyisonext9_2021).
   - Push the full bundle via a `.gitignore` negation + plain `git add` (never -f / -A / .); hard stops, forbidden list and numeric report as in docs/records/nyiso/PRECOMMIT-nyiso-next8-hq-dedupe-2026-09-27.md sec. 6 and the NEXT-9 shard prompts.
   - Parent side: G-1 with scripts/probes/nyisonext9_compose_span.py (adapt DELTA/PIN; it already handles year-keyed fields and fields born since the keeper), gates with nyisonext9_gates.py, compose, `run_calibration_full.py --rebuild-benchmark <span>`, `legitimacy_diagnostics.py --bundle <span> --iso NYISO --json-out <span>/legitimacy_diagnostics.json`, attestation (nyisonext9_attest.py pattern), `run_calibration_full.py --restore-shared-inputs <2021 bundle>`, `dashboard_add_run.py --no-prune`, comparison `scripts/probes/nyisonext_compare.py --pair <keeper> <arm>`.
   - Promotion: keeper shard update incl. a rule-35/E11 de-arm declaration naming every moved recipe field; `stamp_touchpoint_holdout.py ... --holdout-year 2021`; program-status.json gate-(a) re-key (write with json indent=1, ensure_ascii=True to keep the diff small); `build_status.py --iso NYISO`; `audit_keepers.py --iso NYISO` BEFORE the prune (E11 needs the former bundle); `prune_iso_runs.py --iso NYISO --force-uncite --keep <new 2021 run id>`; the calibration-keeper-auditor agent.
5. Archive every shard once its bytes are verified (rule 33). Open a PR and merge. If CI is red only on known base-red, comment once, then merge.
6. If C3a 2022/2025 still fail, draft and launch the next handoff with these same standing directions. Remaining named objects after this one:
   - the >$300 RT tail (nyiso-242: worth $5.44/MWh in 2022, foreclosed by idle sub-gate capacity);
   - the in-city commitment requirement (MyNYISO access is owner-held);
   - the 2025 downstate level shortfall;
   - owner question: delete the now-unarmed nyiso_firm_imports mechanism under rule 26 (NEXT-9 RESULT sec. 4 item 6).

REPORT: numbers only for the intake coverage, phase 0 and gates per year, the verdict, the PR number and the next handoff.
```
