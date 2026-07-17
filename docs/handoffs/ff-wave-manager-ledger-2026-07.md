# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `fa6959e` (2026-07-17, turn 3).
- **Plan base SHA:** `c95176e`.

Status vocabulary: `not-sent` · `sent` · `landed` (merged, unverified) ·
`verified-pass` · `verified-issues` (itemized) · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **verified-pass** | rubric #2414 + scorer #2419 (FF-0A-fix). Complete pair. |
| FF-0A-fix | OPUS | 0 | L-VAL | — | **verified-pass** | PR #2419 (b744383+0075537): `forecast_verdict.py` (1767L, no-LP, `--tier {t1f,t1x,t1h,t2,t3}`, full §0 artifact contract) + `test_forecast_verdict.py` (73 tests **pass** 0.22s). |
| FF-0B | OPUS | 0 | L-VAL | — | verified-issues → superseded by FF-0B-redo | PR #2412 non-delivery (only .gitignore) |
| FF-0B-redo | OPUS | 0 | L-VAL | — | **correction-sent** (turn 2) | in flight — no PR yet |
| FF-0C | FABLE | 0 | L-CAP | — (gates FF-1A) | **verified-pass** | PR #2418 (d860041): `ff-retirement-rule-redesign-2026-07.md` (531L, memo-only). All parts (a-d): diagnosis, field survey, 4 candidates graded + R-NEW composite, T-R10 no-inversion guard + LOYO, identification plan, **owner-decision box §6** (D1/D2/D3). No code/solve. |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | PR #2413: audit doc, no source changes |
| FF-0E | OPUS | 0 | L-VAL | — | sent | in flight — no PR yet |
| FF-1A | FABLE | 1 | L-CAP | ⛔ **owner-gated** | **unblocked, HELD on owner** | FF-0C satisfied; awaiting owner sign-off on FF-0C §6 **D1** (rule choice), D2, D3 |
| FF-1B | FABLE | 1 | L-SCAR | — | **sent** (turn 2) | in flight — no PR yet |
| FF-1C | OPUS | 1 | L-INP | — | **sent** (turn 2) | in flight — no PR yet |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E not landed |
| FF-1E | OPUS | 1 | L-INP | — | not-sent | FF-0D ✅, but starts **after FF-1C merges** (shared constants.py) |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | not-sent | blocked: FF-1A merge |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A merge |
| FF-2C | OPUS | 2 | L-CAP | owner-gated (per-ISO flip) | not-sent | blocked: FF-2B + owner |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: W1/W2 merges (FF-0A rubric+scorer ✅ ready) |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 |
| FF-3C | FABLE | 3 | L-PERF | conditional (T2 breach) | not-sent | trigger-gated |
| FF-3D | OPUS | 3 | L-CAP | owner-gated (R5a option) | not-sent | blocked: owner |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated (config freeze) | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated (PB-5 go) | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — (run LAST) | not-sent | blocked: Wave 4 |

Out-of-program merges tracked earlier: #2416 caiso-94, #2415/#2416 CAMPD outage
consolidation, #2411 ercot-79, #2410 caiso-93. (None since 6d6867b — turn 3's three
merges are all FF/mgr.)

---

## Owner decisions

**Received (verbatim, dated):** none yet.

**AWAITING NOW — FF-0C §6 decision box (gates FF-1A):**

- **D1 (the rule):** A status-quo (blocks all flips) · **B = R-NEW (memo's
  recommendation)** · B2 = B + pre-window seeding (separate A/B; needed for any PJM
  in-window coal recall but changes hindcast information set) · C minimal (not rec) ·
  D hysteresis (rejected). *Surfaced to owner turn 3 via AskUserQuestion.*
- **D2 (if B/B2):** delete `staged_oversupply_thinning` at flip (rec) vs keep gated-off.
- **D3:** adopt measured gas_cc execution lag = 1 (rec, rule 14) vs hold at 2.

**Other pending (unchanged):**

| Decision | Gates | Answerable now? |
|---|---|---|
| DC BAU posture: `datacenter_load_path` `off` vs `mid` | FF-1C, FF-4A | Owner may lean; FF-1C brings corridor evidence. |
| Entry-lookahead default | FF-2A | After FF-2A probe. |
| Forecast-availability derate default | FF-1B | After FF-1B probe. |
| Per-ISO capacity-market flip sign-offs | FF-2C | After FF-1A/FF-2A scorecards. |
| NYISO R5a: Option A vs B (B needs NYSRC App-D manual download) | FF-3D | Partially — can pre-authorize the download. |
| Golden config freeze | FF-4A | After T2. |
| PB-5 go | FF-4C | After golden. |

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — **RESOLVED turn 3, verified-pass.** Built
   `forecast_verdict.py` + 73 passing tests to the merged rubric (PR #2419).
2. **FF-0B-redo [OPUS]** (turn 2) — **open**, in flight. Re-run T1-F + commit findings
   doc + register BEFORE legs; explicit "gitignore-only PR is not delivery" contract.

---

## Turn log

- **2026-07-17 (turn 1, program start).** HEAD `f0da036`; no FF work landed since plan
  base `c95176e`. Dispatched Wave 0 (FF-0A..0E). Created + pushed ledger.
- **2026-07-17 (turn 2, refresh).** Main `f0da036 → 6d6867b`. Landed FF-0A/0B/0D.
  FF-0D verified-pass; FF-0A verified-issues (scorer missing); FF-0B verified-issues
  (non-delivery). Corrections FF-0A-fix + FF-0B-redo (OPUS). Released FF-1C (FF-0D
  satisfied) + FF-1B (independent lane, drift-patched onto consolidated outages.py).
- **2026-07-17 (turn 3, refresh).** Main `6d6867b → fa6959e` (3 merges). Landed:
  **FF-0A-fix** (#2419 — scorer+tests, 73 pass, no-LP; completes FF-0A → verified-pass)
  and **FF-0C** (#2418 — retirement redesign memo, verified-pass, all parts + owner
  box). Both governance-clean. FF-0B-redo/FF-0E/FF-1B/FF-1C still in flight (no PRs).
  FF-0C's landing unblocks FF-1A but it is owner-gated on §6 D1 — surfaced the D1/D2/D3
  decision to the owner (recommendation B / delete-at-flip / adopt-measured); FF-1A
  HELD until the call lands in chat. No new worker prompt dispatched (Wave-1 remainder
  blocked on FF-0E / FF-1C-merge / the D1 call). Frontier §1.2 unchanged.
