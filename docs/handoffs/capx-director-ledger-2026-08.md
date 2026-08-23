# Capacity-Expansion Workstream Director — Ledger

Standing coordination ledger for the capacity-expansion (Forecast Finalization
Program) track. Maintained by the director session on branch
`claude/capx-director-ledger`; one refresh = one commit when anything changes.
The director charters sessions and tracks state — it never runs solves, never
edits `src/market_sim/`, and never charters backcast-calibration work (that
track is the owner's own CAISO/ERCOT/MISO sessions, watched here for
deconfliction only).

**Charter date:** 2026-08-23 · **Last refresh:** 2026-08-23 (first turn) ·
**HEAD at refresh:** `5ef739f`

---

## 1. Lane scoreboard

| lane | scope | status | branch (session) | model | evidence / notes |
|---|---|---|---|---|---|
| **D1 BOARD-REFRESH** | Correct `program-status.json` cross-ISO rows against the live committed FFR-3A-2/3A-3/3A-4 verdict records + current keepers; adjudicate the A1/I4 close-out; FINDING doc | **ISSUED 2026-08-23** | `claude/capx-d1-board-refresh` | Opus | Director pre-read (this ledger §3): I4 absent from every live FC-1 fail list — `frontend/data/forecast/ff-verdicts.json` un-suffixed `*-t1f` keys, all `scored_at_sha 8ba59281`, session FFR-3A-2. Board's `honest_unfit` I4/A1 row, `gate_reading`, PJM/MISO/CAISO `blocking_rows`, and all six top-level `keeper` display fields are stale. |
| **D2 ADEQUACY/A2 — NYISO** | Root-cause I7 base-year adequacy (live gap: 2026 36 MW, 2027 51 MW; I12 WARN 7.8% vs 8.0% floor) — accreditation accounting vs fleet-snapshot vintage vs requirement mismatch; hydro-in-ledger (FF-1C) is the named suspect | **ISSUED 2026-08-23** | `claude/capx-d2-adequacy-nyiso` | Fable | `ff-verdicts.json::nyiso-t1f`; `honest_unfit` I7/A2 row (hydro dispatched but excluded from `accredited_firm_capacity_mw`); open_frontier #6 (NYISO hydro fleet silently drops ~3.3 GW past last EIA-923 vintage). Board's "30.3 < 32.1 GW" figure is FF-2D-stale. |
| **D2 ADEQUACY/A2 — MISO** | Same lane, MISO (live gap: 2026 6,037 MW, 2027 3,659 MW) | QUEUED | — | Fable | Charter after D1 lands (board truth first); does not conflict with the MISO backcast lane (dispatch/offer side). |
| **D2 ADEQUACY/A2 — CAISO** | Same lane, CAISO (I7 + I12 FAIL 2026–2029 + FC-2 backstop share 65.5% > 30%) | QUEUED | — | Fable | Deepest adequacy miss of the six; hydro-in-ledger + ELCC (CR-3.1). |
| **D3 MISO RETIREMENT / G3 REGRESSION** | `retire.total_gw` PASS→FAIL under the G3 cap-grain fix (FFR-3A-3, t1h) | QUEUED — **re-scoped 2026-08-23** | — | Fable | The FC-2 I13 gas_ct cobweb half of the charter is NOT on the live record: `miso-t1f` (FFR-3A-2) reads I13 PASS. D1 adjudicates; if confirmed stale, D3 narrows to the t1h retirement-sweep regression (cite ffr-2b + retirement-rule redesign docs). |
| **D4 ERCOT I3 + FORECAST NET-REVENUE** | I3 scarcity slack 2027–2030; live record adds I12 FAIL (RM 9.1→−1.5%) and FC-2 sustained-VOLL FAIL (1,137 h/yr ≥ $500) | **BLOCKED — coordination question pending** | — | Fable | Owner asked 2026-08-23: has the ERCOT 2023 backcast scarcity arc settled a scarcity representation this lane should consume? Evidence says arc still in flight (ercot223 keeper 2026-08-20; ercot-231 landed 2026-08-23). If in flight, charter I3-invariant half only. |
| **D5 FC-4 CO2 CROSSOVER (ERCOT+PJM)** | Crossover CO2 43–58% attribution (emission-rate basis vs dispatch composition vs vintage conditioning) | QUEUED | — | Fable | MISO's crossover (FFR-3A-4) shows the same CO2 pattern (63/59/76%) — may widen to three ISOs; decide at charter time. |
| **D6 FC-3 CURVE-ON OVER-FIRE (T1-H)** | Four curve legs FAIL on curve-ON over-build in hindcast | QUEUED | — | Fable | Cite ff-g3-net-cone-forward + ff-2c flip execution docs. |
| **D7 T2 GATE RE-SCORE** | Re-run FF-2D per ISO once D1–D6 land; move gate-openers to T2 scheduling | QUEUED | — | Opus | PJM + NEISO closest (single small I7 miss each, gate (a) pass for both); NYISO joins if D2-NYISO clears FC-1. MISO/CAISO join on backcast `complete` re-declaration — watch every refresh. |

## 2. Backcast-track watch (deconfliction; last seen 2026-08-23 @ `5ef739f`)

| item | state |
|---|---|
| ERCOT keeper | `2026-08-20-ercot223-arm-eventrelease` — det NOT-YET (C3a-2023 + C3b-2023, the adjudicated 2023 model-class price object; C3c ledgered ×3). 2023 scarcity arc ACTIVE (ercot-231 tie-zonal-interchange landed 2026-08-23). |
| CAISO keeper | `2026-08-17-caiso-200-h1-memberpanel` — det NOT-YET (C3a sole: +4.1 PASS / +12.8 / +15.7%). caiso-217 crosswalk solve IN FLIGHT (2023 checkpoint on main 2026-08-23). |
| MISO keeper | `2026-08-22-miso-177-rho-measured` — det NOT-YET (C3a-2025 −11.7% sole). miso-180 anchored-spread A/B merged 2026-08-23 (keeper unchanged → probe/rejected; verify verdict on next refresh). |
| PJM / NYISO / NEISO | CALIBRATED, `complete` held: `2026-08-15-pjm-162-inputclock`, `2026-08-22-nyiso-152-duty-complete`, `2026-08-17-neiso-99-joint-p1`. **NYISO frontier RATIFIED by owner 2026-08-23** (commits `8cc636f`, `1948bc9`). |
| Markers | `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY; holdout spend freeze **ACTIVE**. |
| Gate-(a) reading | pass: PJM, NYISO, NEISO (= `complete` membership); fail on marker: ERCOT, CAISO, MISO. Board gate-(a) blocks re-keyed to live keepers 2026-08-23 (director-records v12 @ `1b8ddaca`). |

## 3. Director pre-read of the live verdict records (2026-08-23) — D1's verification targets

Read from `frontend/data/forecast/ff-verdicts.json` (un-suffixed `*-t1f` = FFR-3A-2
@ `8ba59281`; `-ff2d` suffixed = superseded FF-2D vintage). D1 re-verifies
independently; this is the director's evidence log, not the deliverable.

- **A1/I4 closed in ALL SIX ISOs** — no I4 in any live FC-1 fail list. Confirms and
  extends neiso-88 §1.1 (which verified NEISO/PJM/MISO/CAISO). The neiso-88-cited
  sidecar path `frontend/data/hindcast/*-2026-2030-ffr3a2-t1f.json` no longer exists
  at HEAD; the committed carrier of the FFR-3A-2 T1-F verdicts is `ff-verdicts.json`.
- **Live FC-1 fail sets:** ERCOT {I12, I3} · CAISO {I12, I3, I7} · PJM {I7: 2030,
  150,088 < 150,454 MW = 366 MW} · MISO {I7: 2026 −6,037 MW, 2027 −3,659 MW} ·
  NYISO {I7: 2026 −36 MW, 2027 −51 MW} · NEISO {I7: 2028 −218 MW}.
- **The dominant program blocker is I7/I12 adequacy (6/6 ISOs), not I4.**
- **MISO I13 cobweb: PASS** on the live record (board's FC-2 FAIL I13 row is FF-2D
  vintage). MISO FC-2 is CAVEAT (I12 WARN 2026/2027).
- **ERCOT FC-2** carries a row the board omits: sustained-VOLL FAIL (hours_ge_500
  peaks 1,137 h/yr > 800) alongside I12 FAIL.
- **CAISO FC-2 FAIL** includes backstop share 65.5% > 30% (administrative
  over-build) — deeper than the board's row set.
- **NYISO I7 magnitude:** the board's "firm 30.3 < 32.1 GW" (1.8 GW) is stale;
  live gap is 36/51 MW with I12 WARN at 7.8% vs 8.0% floor.

## 4. Owner-tier questions on file

| # | question | asked | answer |
|---|---|---|---|
| Q1 (D4 coordination) | Has the ERCOT 2023 backcast scarcity arc settled a scarcity representation the forecast net-revenue lane should build on, or is it still in flight (→ charter I3-invariant half only)? | 2026-08-23 (first report) | PENDING |

## 5. Prompt issuance record

| date | lane | branch | model | profile |
|---|---|---|---|---|
| 2026-08-23 | D1 BOARD-REFRESH | `claude/capx-d1-board-refresh` | Opus | code |
| 2026-08-23 | D2 ADEQUACY — NYISO | `claude/capx-d2-adequacy-nyiso` | Fable | nyiso |
