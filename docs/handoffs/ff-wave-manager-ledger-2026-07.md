# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `6d6867b` (2026-07-17, turn 2).
- **Plan base SHA:** `c95176e`.

Status vocabulary: `not-sent` · `sent` · `landed` (merged, unverified) ·
`verified-pass` · `verified-issues` (itemized) · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **verified-issues** | PR #2414 (a9f92ba): rubric doc ✅ + FC-5 inventory ✅; **`scripts/forecast_verdict.py` + unit tests MISSING** (deliverable 2 of 3). Correction FF-0A-fix. |
| FF-0B | OPUS | 0 | L-VAL | — | **verified-issues** | PR #2412 (b20ad74): **only `.gitignore` landed** — findings doc + dashboard registrations (the BEFORE legs) never committed. Non-delivery. Correction FF-0B-redo. |
| FF-0C | FABLE | 0 | L-CAP | — (gates FF-1A) | sent | in flight — no PR (merged or open) yet |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | PR #2413 (1a0a560): `ff-inputs-currency-audit-2026-07.md`, full CURRENT/STALE/UNWIRED table w/ citations + MANUAL-DOWNLOAD flags; net diff = 1 doc, **no source changes** (audit-only honored). |
| FF-0E | OPUS | 0 | L-VAL | — | sent | in flight — no PR (merged or open) yet |
| **FF-0A-fix** | OPUS | 0 | L-VAL | — | **correction-sent** (turn 2) | build `forecast_verdict.py` + tests to the merged rubric §0/§3/§8 |
| **FF-0B-redo** | OPUS | 0 | L-VAL | — | **correction-sent** (turn 2) | re-run T1-F, commit findings doc + register BEFORE legs |
| FF-1A | FABLE | 1 | L-CAP | ⛔ owner-gated (FF-0C sign-off) | not-sent | blocked: FF-0C not landed + owner |
| FF-1B | FABLE | 1 | L-SCAR | — | **sent** (turn 2) | independent lane; released |
| FF-1C | OPUS | 1 | L-INP | — | **sent** (turn 2) | FF-0D landed + verified-pass |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E not landed |
| FF-1E | OPUS | 1 | L-INP | — | not-sent | FF-0D ✅, but starts **after FF-1C merges** (shared constants.py) |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | not-sent | blocked: FF-1A merge |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A merge |
| FF-2C | OPUS | 2 | L-CAP | owner-gated (per-ISO flip) | not-sent | blocked: FF-2B + owner |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: FF-0A(-fix) + W1/W2 merges |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 |
| FF-3C | FABLE | 3 | L-PERF | conditional (T2 breach) | not-sent | trigger-gated |
| FF-3D | OPUS | 3 | L-CAP | owner-gated (R5a option) | not-sent | blocked: owner |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated (config freeze) | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated (PB-5 go) | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — (run LAST) | not-sent | blocked: Wave 4 |

Out-of-program merges since f0da036 (tracked, not FF): #2416 caiso-94 daytime-no-wedge,
#2415/#2416 CAMPD outage-detection consolidation (`scripts/lib/outage_detect.py`;
facility layer deleted; `data/outages.py` −237 lines — **drifts FF-1B**), #2411
ercot-79 corrected-outages keeper, #2410 caiso-93 keeper promotion.

---

## Owner decisions

**Received (verbatim, dated):** none yet.

**Pending (from plan closing note §, line 957–960):**

| Decision | Gates | Answerable now? |
|---|---|---|
| Retirement decision-rule choice (FF-0C decision box) | FF-1A | No — awaits FF-0C memo (in flight). |
| DC BAU posture: `datacenter_load_path` default `off` vs `mid` for T1+/golden | FF-1C, FF-4A | Owner may state a lean now; FF-1C brings corridor evidence. |
| Entry-lookahead default (`entry_lookahead_reprice` ON?) | FF-2A | No — awaits FF-2A probe evidence. |
| Forecast-availability derate default posture | FF-1B | No — awaits FF-1B probe evidence. |
| Per-ISO capacity-market flip sign-offs | FF-2C | No — awaits FF-1A/FF-2A gate scorecards. |
| NYISO R5a: Option A (lagged model-derived) vs B (NYCA static proxy; needs NYSRC App-D Table D.1.1 manual download) | FF-3D | Partially — owner can pre-authorize the Option-B manual download now if leaning B. |
| Golden config freeze (SHA + run_config) | FF-4A | No — after T2 pass. |
| PB-5 probability-band go | FF-4C | No — after golden. |

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2, 2026-07-17). FF-0A (PR #2414) merged an excellent
   rubric v1.0 but omitted deliverable 2 — `scripts/forecast_verdict.py` + unit tests
   — even though the merged rubric §8 documents its CLI. **Assignment [OPUS] (not
   FABLE):** the hard adjudication (what to measure / thresholds) is done and frozen in
   the merged rubric; implementing the no-LP scorer against §0's artifact contract with
   the `calibration_verdict.py` precedent is spec'd execution. Not a governance breach.
2. **FF-0B-redo [OPUS]** (turn 2, 2026-07-17). FF-0B (PR #2412) committed only a
   `.gitignore` line; its own PR body named the real deliverables (findings doc +
   dashboard sidecars) yet neither landed — the BEFORE-baseline legs every Wave-1/2
   change regresses against are absent. **Assignment [OPUS] unchanged:** the task is
   Opus-appropriate (solve campaign + findings + registration); the miss was
   follow-through, not difficulty — the redo carries an explicit deliverable contract
   and a "gitignore-only PR is not delivery" clause. Forecast-mode 2026-2030 solves are
   quarantine-legal (no governance breach).

---

## Turn log

- **2026-07-17 (turn 1, program start).** Fetched main (HEAD `f0da036`); no FF work
  landed since plan base `c95176e`. Drift-checked + dispatched Wave 0 (FF-0A..0E),
  collision-free. Created + pushed this ledger.
- **2026-07-17 (turn 2, refresh).** Main `f0da036 → 6d6867b` (8 PRs). Landed FF: FF-0A
  (#2414), FF-0B (#2412), FF-0D (#2413). FF-0C/FF-0E still in flight (no PR). Verified:
  **FF-0D verified-pass**; **FF-0A verified-issues** (scorer+tests missing); **FF-0B
  verified-issues** (only gitignore — non-delivery). No open PRs hold the missing
  pieces. Governance clean on all three (no quarantine contact, no residual tuning, no
  backcast-registry contamination, no band widening, no core-file shrink). Issued
  corrections FF-0A-fix + FF-0B-redo (both [OPUS]). Unblocked + released FF-1C (FF-0D
  satisfied) and FF-1B (independent L-SCAR lane), the latter drift-patched onto the
  consolidated `data/outages.py`/`outage_detect.py`. Frontier §1.2 unchanged (FF-0D
  populated row 6's findings but closed no row; fixes are FF-1C/FF-1E). Held: FF-1A
  (FF-0C+owner), FF-1D (FF-0E), FF-1E (after FF-1C merges).
