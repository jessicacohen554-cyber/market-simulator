# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `f0da036` (2026-07-17).
- **Plan base SHA:** `c95176e`. Commits since then are per-ISO calibration work
  (miso-72 winter gas overlay, ercot-79 phantom-outage audit, caiso-92/93 overnight
  CC imports, nyiso overrun/underrun) — **no FF-labeled work has landed yet.** This
  ledger opens at program start.

Status vocabulary: `not-sent` · `sent` · `landed` (merged, unverified) ·
`verified-pass` · `verified-issues` (itemized) · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **sent** (2026-07-17) | — |
| FF-0B | OPUS | 0 | L-VAL | — | **sent** (2026-07-17) | — |
| FF-0C | FABLE | 0 | L-CAP | — (gates FF-1A) | **sent** (2026-07-17) | — |
| FF-0D | OPUS | 0 | L-INP | — | **sent** (2026-07-17) | — |
| FF-0E | OPUS | 0 | L-VAL | — | **sent** (2026-07-17) | — |
| FF-1A | FABLE | 1 | L-CAP | ⛔ owner-gated (FF-0C sign-off) | not-sent | blocked: FF-0C + owner |
| FF-1B | FABLE | 1 | L-SCAR | — | not-sent | blocked: Wave 0 |
| FF-1C | OPUS | 1 | L-INP | — | not-sent | blocked: FF-0D merge |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E merge |
| FF-1E | OPUS | 1 | L-INP | — | not-sent | blocked: FF-0D merge; starts after FF-1C |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | not-sent | blocked: FF-1A merge |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A merge |
| FF-2C | OPUS | 2 | L-CAP | owner-gated (per-ISO flip) | not-sent | blocked: FF-2B + owner |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: FF-0A + W1/W2 merges |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 |
| FF-3C | FABLE | 3 | L-PERF | conditional (T2 breach) | not-sent | trigger-gated |
| FF-3D | OPUS | 3 | L-CAP | owner-gated (R5a option) | not-sent | blocked: owner |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated (config freeze) | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated (PB-5 go) | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — (run LAST) | not-sent | blocked: Wave 4 |

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
| Per-ISO capacity-market flip sign-offs | FF-2C | No — awaits FF-1A/FF-2A measured gate scorecards. |
| NYISO R5a: Option A (lagged model-derived) vs Option B (NYCA static proxy; needs NYSRC App-D Table D.1.1 manual download) | FF-3D | Partially — owner can pre-authorize the Option-B manual download now if leaning B. |
| Golden config freeze (SHA + run_config) | FF-4A | No — after T2 pass. |
| PB-5 probability-band go | FF-4C | No — after golden. |

---

## Corrections issued

None yet.

---

## Turn log

- **2026-07-17 (turn 1, program start).** Fetched main (HEAD `f0da036`); confirmed no
  FF work landed since plan base `c95176e`. Drift-checked all five Wave 0 prompts
  against HEAD: every referenced doc/script/source/symbol/flag verified present;
  `scripts/forecast_verdict.py`, `scripts/score_crossover.py`, and
  `run_capacity_hindcast.py --vintage` correctly absent (they are FF-0A/FF-0E
  deliverables); `data/raw/eia-860/vintage_2023/` present (FF-0E path accurate);
  harness hardcodes `VINTAGE_YEAR=2020` (FF-0E "generalize" accurate). No prompt text
  patched. Dispatched Wave 0 (all 5 — parallel, file-owner-disjoint across
  L-VAL/L-CAP/L-INP, collision-free). Listed pending owner decisions. Frontier table
  (§1.2) unchanged — no landed session yet closes/opens a row.
