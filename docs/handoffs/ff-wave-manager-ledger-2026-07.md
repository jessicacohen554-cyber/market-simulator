# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `2144e12` (2026-07-17, turn 4).
- **Plan base SHA:** `c95176e`.

Status vocabulary: `not-sent` · `sent` · `landed` (merged, unverified) ·
`verified-pass` · `verified-issues` (itemized) · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **verified-pass** | rubric #2414 + scorer #2419. Complete pair. |
| FF-0A-fix | OPUS | 0 | L-VAL | — | **verified-pass** | #2419: forecast_verdict.py + 73 passing tests |
| FF-0B | OPUS | 0 | L-VAL | — | verified-issues → superseded by FF-0B-redo | #2412 non-delivery |
| FF-0B-redo | OPUS | 0 | L-VAL | — | **correction-sent** (turn 2) | in flight — no PR yet |
| FF-0C | FABLE | 0 | L-CAP | — (gates FF-1A) | **verified-pass** | #2418: retirement redesign memo; owner box D1/D2/D3 |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | #2413: audit doc, no source changes |
| FF-0E | OPUS | 0 | L-VAL | — | sent | in flight — no PR yet |
| FF-1A | FABLE | 1 | L-CAP | ⛔ **owner-gated** | **HELD on owner (prompt staged turn 4)** | FF-0C satisfied; awaiting D1 sign-off. Prompt keyed to Option B ready to fire. |
| FF-1B | FABLE | 1 | L-SCAR | — | **sent** (turn 2) | in flight — no PR yet |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | PR #2422 (87c803b+83518a8): demand refresh (5 ISOs re-vintaged + MISO wired), DC double-count fix (energy-invariant relocation, runner.py+datacenter.py, default-off byte-identical), hydro verified already-fixed (66c55fd), ZONE_SHARE/NEISO `{}` documented per charter, citations updated. Scope clean (no FF-1E constants/policy), rule-27 clean (constants.py 7097→7179), DC default still `off`. CAVEAT: numpy-tests not executable in mgr env (files updated + hydro tests/commit confirmed statically). |
| FF-1D | OPUS | 1 | L-VAL | — | not-sent | blocked: FF-0E not landed |
| FF-1E | OPUS | 1 | L-INP | — | **sent** (turn 4) | FF-0D ✅ + FF-1C merged ✅ — released |
| FF-2A | FABLE | 2 | L-CAP | ⛔ | not-sent | blocked: FF-1A merge |
| FF-2B | OPUS | 2 | L-CAP | — | not-sent | blocked: FF-2A merge |
| FF-2C | OPUS | 2 | L-CAP | owner-gated (per-ISO flip) | not-sent | blocked: FF-2B + owner |
| FF-2D | OPUS | 2 | L-VAL | ⛔ T1 gate | not-sent | blocked: W1/W2 merges (FF-0A ✅) |
| FF-3A | OPUS | 3 | L-VAL | ⛔ T2 | not-sent | blocked: FF-2D + owner |
| FF-3B | OPUS | 3 | L-CES | — | not-sent | blocked: W2 |
| FF-3C | FABLE | 3 | L-PERF | conditional (T2 breach) | not-sent | trigger-gated |
| FF-3D | OPUS | 3 | L-CAP | owner-gated (R5a option) | not-sent | blocked: owner |
| FF-4A | OPUS | 4 | L-VAL | ⛔ owner-gated (config freeze) | not-sent | blocked: FF-3A + owner |
| FF-4B | FABLE | 4 | L-VAL | — | not-sent | blocked: FF-4A |
| FF-4C | OPUS | 4 | L-VAL | owner-gated (PB-5 go) | not-sent | blocked: FF-4A + owner |
| FF-5A | OPUS | 5 | L-DASH | — (run LAST) | not-sent | blocked: Wave 4 |

Out-of-program merges this window: #2427 ercot-80 unit-only outages, #2426/#2425 miso-72
winter fuel security, #2420 caiso-94 daytime-clean.

---

## Owner decisions

**Received (verbatim, dated):** none yet.

**AWAITING — two live calls:**

1. **FF-0C §6 D1 (gates FF-1A).** A status-quo (blocks flips) · **B = R-NEW (rec)** ·
   B2 = B + pre-window seeding (separate A/B) · C minimal (not rec) · D rejected. Plus
   D2 delete staged-thinning at flip (rec), D3 gas_cc lag=1 (rec). FF-1A prompt staged,
   keyed to B — launching it is the sign-off.
2. **BAU DC posture — NOW ACTIONABLE (FF-1C evidence in).** `datacenter_load_path`
   default `off` vs `mid` for T1+/golden. Energy-equal at mid; the choice is DC hourly
   SHAPE. `mid` models DC flat → lower peak (ERCOT 2030 ~120 vs ~139 GW), less
   peaker over-build / phantom scarcity — structurally more faithful, now admissible
   (double-count fixed). FF-1C recommends the structural argument favors `mid` but it is
   a material golden-peak change → owner's call. Gates FF-4A; informs FF-1E/FF-2D runs.

**Other pending:** entry-lookahead (FF-2A), availability derate (FF-1B), per-ISO flips
(FF-2C), NYISO R5a (FF-3D), golden freeze (FF-4A), PB-5 (FF-4C).

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — **RESOLVED turn 3, verified-pass** (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — **open**, in flight (no PR).

---

## Turn log

- **turn 1 (program start).** HEAD `f0da036`. Dispatched Wave 0 (FF-0A..0E). Ledger created.
- **turn 2 (refresh).** `f0da036 → 6d6867b`. FF-0D verified-pass; FF-0A/FF-0B
  verified-issues → corrections FF-0A-fix + FF-0B-redo. Released FF-1B + FF-1C.
- **turn 3 (refresh).** `6d6867b → fa6959e`. FF-0A-fix + FF-0C landed verified-pass.
  FF-1A unblocked but owner-gated on D1; surfaced the box. (Owner asked for the prompt →
  turn 4 staged the FF-1A block keyed to Option B.)
- **turn 4 (refresh).** `fa6959e → 2144e12` (6 merges; only FF-1C in-program). **FF-1C
  verified-pass** (demand/DC currency + double-count fix + hydro-verify; scope/rule-27/
  DC-default all clean; tests not runnable in mgr env, statically confirmed). FF-1C
  merging unblocked **FF-1E → released** (drift-patched onto NEW_ENTRY_COSTS:4201 +
  resolve_new_entry_costs + on-disk ATB-2024 datatype). Surfaced the now-actionable BAU
  DC posture decision (rec: mid). FF-1A still held on D1. FF-0B-redo/FF-0E/FF-1B in
  flight. Frontier §1.2 unchanged.
