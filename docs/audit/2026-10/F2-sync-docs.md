# F2 — Doc/code sync of the 2026-10 audit mismatches

Session 2026-10-03, lane `claude/audit-followups-2026-10`. Source: §4 "Doc/code
mismatches" of `A-lp-dispatch-commitment.md` (W2–W4) and
`B-capacity-policy-forecast.md` (D1–D3, D5), each verified against source before
editing. Code is the source of truth; prose was fixed to match. Format:
`file: was → now (source file:line)`.

1. `docs/codebase/02-lp-dispatch.md`: "Source: `model/dispatch.py` (~2,400
   lines)" → `model/lp/model.py` (2,240 lines) + `rows.py`; `dispatch.py` is a
   34-line facade (`src/market_sim/model/dispatch.py`, 34 lines;
   `src/market_sim/model/lp/model.py:68`).
2. `docs/codebase/02-lp-dispatch.md`: "`DispatchModel` … (lines 1653–2149)" →
   "(`model/lp/model.py:68`)" (`src/market_sim/model/lp/model.py:68`).
3. `docs/codebase/02-lp-dispatch.md`: "P0→P1→P2 sequence cheap" → P0→P1 are the
   only two production passes; P2 archived behind `--enable-legacy-p2`
   (`scripts/run_calibration.py:8540`; CLAUDE.md "Dispatch and commitment").
4. `docs/codebase/03-capacity-and-commitment.md:3-4`: "`model/capacity.py`" /
   "P0→P1→P2 commitment screen" → `model/capacity_evolution/` (`capacity.py` a
   32-line shim) / P0→P1 sequence, P2 archived (`src/market_sim/model/capacity.py`,
   32 lines; `src/market_sim/model/capacity_evolution/__init__.py:6-17`).
5. `docs/codebase/03-capacity-and-commitment.md` §3.1: "six steps",
   "`capacity.py:1412`", order retire(2)→additions(3)→CCS(4) → steps 0–7,
   `capacity_evolution/evolve.py:129`, order confirmed(0) → announced + limb 1b
   fossil dates(1) → CCS(2) → economic retirement(3) → known additions(4) →
   entry(5) → backstop(6) → RPS dispatch(7)
   (`src/market_sim/model/capacity_evolution/evolve.py:487,533,556,687,804,875,1014,1130`).
6. `docs/codebase/03-capacity-and-commitment.md` Step 0: "the ONLY exogenous
   fossil exit channel" → one of two (limb 1b is the other)
   (`src/market_sim/model/capacity_evolution/evolve.py:541-556`).
7. `docs/codebase/03-capacity-and-commitment.md` Step 1: "for the whole fossil
   fleet this step is a default no-op" → owner-filed EIA-860 dates honoured via
   limb 1b, `fossil_announced_exits_enabled` default on, vintage-gated,
   reversal-checked, bypasses the reliability floor
   (`src/market_sim/config/scenarios.py:5303`;
   `src/market_sim/model/capacity_evolution/evolve.py:541-556`).
8. `docs/codebase/03-capacity-and-commitment.md` step headings: "Step 2 —
   Economic retirements (line 279)" → Step 3 (`retirements.py:3158`); "Step 4 —
   CCS retrofit (line 1257)" → Step 2 (`ccs.py:180`); new entry "line 928" →
   `new_entry.py:832`; backstop "line 1176" → `adequacy.py:866`
   (`src/market_sim/model/capacity_evolution/{retirements,ccs,new_entry,adequacy}.py`).
9. `docs/codebase/03-capacity-and-commitment.md` §3.2: "The P0→P1→P2 commitment
   sequence / Three LP solves per year" → "P0→P1 (P2 archived) / Two LP solves";
   P2 table row and heading marked ARCHIVED behind `--enable-legacy-p2`
   (`scripts/run_calibration.py:8193,8540`).
10. `docs/codebase/03-capacity-and-commitment.md` §3.2: (absent) → new
    "P1-native commitment mechanisms" subsection: the three P1-native bridges
    (CLAUDE.md "Dispatch and commitment") plus the default-off fourth family
    `ercot_commitment_posture` / `miso_commitment_posture` /
    `spp_commitment_posture` built by `_build_posture_energy_rows`
    (`src/market_sim/config/scenarios.py:14773,11008,9457`;
    `src/market_sim/model/lp/rows.py:1214`;
    `docs/codebase-site/data/mechanism-matrix.js:1759`).
11. `model-methodology-spec.md` §1.9: "No inter-hour generator ramp-rate
    constraints … Flagged as a future enhancement" → built but default off:
    `_build_ramp_rows` behind `ScenarioConfig.ramp_limits = False`
    (`src/market_sim/model/lp/rows.py:993`; `src/market_sim/config/scenarios.py:7162`;
    `src/market_sim/pipeline/year.py:207`).
12. `docs/calibration-and-validation-methodology.md:6`: "holdout-tested" →
    "determined over every registered year (there is no holdout regime — rule 22
    `[R-C3C]`)" (CLAUDE.md rule 22; `docs/governance/rule-history.md` §18).
13. `docs/calibration-and-validation-methodology.md` §3: (absent) → current-regime
    note: no holdout regime, any year may be solved/scored/registered, no year a
    certified out-of-sample number, ISO determination worst-of over every
    registered year; §3.1 title marked HISTORICAL
    (`scripts/calibration_verdict.py:4027` `iso_determination`, rubric v3.13;
    CLAUDE.md rules 22, 30; rule-history §18).
14. `docs/calibration-and-validation-methodology.md` §3.2 "Current state": "only
    NEISO carries a complete marker … other five ISOs remain fully quarantined"
    → no ISO quarantined; former locked-test scores are historical records
    (`scripts/calibration_verdict.py:4027`; rule-history §18).
15. `docs/calibration-and-validation-methodology.md` §4 table: marker purpose
    "Gating — authorizes the rule-22 holdout solves" → keeper designation and
    forecast gate-(a) input only (CLAUDE.md rule 22; rule-history §18).
16. `src/market_sim/pipeline/solve.py:60` docstring: "the calibration CLIs
    default ON" → "default OFF (owner ruling 2026-09-19, miso-262; rule 36)"
    (`scripts/run_calibration.py:8787-8792`; CLAUDE.md rule 36). No code change;
    `python3 -m py_compile` passes.
17. `docs/README.md` L3 table: (absent) → row "Third-party audits" indexing
    `audit/third-party-audit-2026-10.md`, `audit/2026-10/` and
    `audit/third-party-audit-2026-08.md` (`docs/audit/` listing; neither audit
    was indexed before).
18. `docs/audit/2026-10/E-model-positioning-matrix.md:88`: "five of nine ISOs
    read NOT-YET today" → seven of nine (NEISO, NYISO CALIBRATED), recomputed by
    `iso_determination` 2026-10-03, not read from status shards; the "Current
    determinations" row (`:21`) corrected to the same set and notes the status
    shards lag (`scripts/calibration_verdict.py:4027`).

Not touched (out of scope or already correct): B D4 (`forecast-development-plan`
"Current state" stamp) — not in the assignment; `frontend/data/forecast/
program-status.json` was already modified in the working tree before this
session and was not edited here.
