# Capacity-Expansion Workstream Director — Ledger

Standing coordination ledger for the capacity-expansion (Forecast Finalization
Program) track. Maintained by the director session on branch
`claude/capx-director-ledger`; one refresh = one commit when anything changes.
The director charters sessions and tracks state — it never runs solves, never
edits `src/market_sim/`, and never charters backcast-calibration work (that
track is the owner's own CAISO/ERCOT/MISO sessions, watched here for
deconfliction only).

**Charter date:** 2026-08-23 · **Last refresh:** 2026-08-24 (refresh #2) ·
**HEAD at refresh:** `d84a95e`

---

## 0. Refresh #2 headline — the I7 blocker is measured on a pre-fix HEAD

**D1 landed and did its job** (PR #4242, `c02f766`): 36 board fields corrected, 0
determinations moved, and the A1/I4 leak adjudicated CLOSED cross-ISO. It promoted
**I7/I12 adequacy accounting** to the dominant-blocker row (6/6 ISOs) in I4's place.

**The director's own re-read says that row is repeating I4's mistake one level down.**
The board states the I7 root cause as *"unchanged, and still the live one: hydro is
dispatched but excluded from the accredited firm-capacity ledger —
`accredited_firm_capacity_mw` reads the persistent fleet, which never contains hydro."*
At HEAD that is **false**:

- `src/market_sim/model/capacity_evolution/adequacy.py:328` calls `_hydro_firm_mw(fleet, iso, year)`
  **unconditionally** — no gate, no flag. Its docstring names the fix: hydro is credited from the
  hydro-budget loader, *"never from the persistent `fleet`, which structurally never contains
  hydro; **FFR-1C, audit FR-3**"*.
- `HYDRO_ACCREDITATION_CREDIT_BY_ISO` ships published per-ISO credits with citations —
  CAISO 0.7041 (CPUC/CAISO CY2025 NQC), NYISO 0.3844 (NYISO 2025-26 Final CAF),
  MISO 0.62 (PY2025-26 Indicative DLOL), PJM 0.38 (2026/27 BRA ELCC class rating);
  NEISO falls back to the generic `RENEWABLE_CAPACITY_CREDIT["hydro"]`.
- **It landed 2026-08-19** (`15b107f`, PR #4162). **Every I7 FAIL on the board is scored at
  `8ba59281` = FFR-3A-2, 2026-08-03** — sixteen days earlier.

**Magnitude check:** NYISO's miss is 36 / 51 MW; PJM's 366 MW; NEISO's 218 MW. NYISO alone
carries multi-GW conventional hydro. An un-credited hydro fleet is orders of magnitude larger
than all three misses combined.

**Consequence for the lane plan:** the first move on adequacy is **NOT a code fix — it is a
re-measurement**. D2's per-ISO charters are superseded by **D2-REMEASURE**, and the T1-F legs
are cheap enough to make this near-free: recorded FC-8 wall times are ERCOT 0.8 min, CAISO
0.7, NYISO 0.7, NEISO 9.2; PJM and MISO are memory-bound (8.8 / 9.6 GB peak RSS, no co-run)
but not slow. All six re-run in roughly one session.

---

## 1. Lane scoreboard

| lane | scope | status | branch (session) | model | evidence / notes |
|---|---|---|---|---|---|
| **D1 BOARD-REFRESH** | Correct `program-status.json` against live verdict records; adjudicate A1/I4 cross-ISO | **LANDED `c02f766`** (PR #4242, 2026-08-24) | `claude/capx-d1-board-refresh-nfb31y` | Opus | `docs/handoffs/FINDING-capx-d1-board-refresh-2026-08-23.md`. 36 fields, 0 determinations/verdicts/gates moved. Two against-interest corrections kept at full magnitude: ERCOT I3 slack 0.08–0.41% (not 0.01–0.03%), ERCOT T1-X 2025 price no longer converges (22.5% FAIL). Handed back: 1 escalation (→ Q2), 2 out-of-lane staleness flags, 1 D3 posture note. |
| **D2-REMEASURE** (NEW — supersedes the per-ISO D2 charters) | Re-run all six T1-F legs (2026–2030, forecast mode) at HEAD and re-score FC-1, so the I7/I12 verdicts sit on the post-FFR-1C hydro-accreditation code | **ISSUED 2026-08-24** | `claude/capx-d2-remeasure-t1f` | Fable | §0 above. Forecast-mode 2026+ = unrestricted (rule 22). Register on the FORECAST namespace (rule 15). Expected: NYISO/PJM/NEISO I7 may close outright → three gate-(a) passers clear FC-1. |
| **D2-A2 per-ISO follow-ups** (NYISO / MISO / CAISO) | Root-cause whatever I7/I12 residual SURVIVES the re-measurement | **QUEUED — deliberately held** | — | Fable | Chartering a fix before the re-measurement would risk fixing what FFR-1C already fixed — the exact error D1 just caught on I4. CAISO is the deepest (I7 2026–2029 to 9,243 MW + I12 + 65.5% backstop share); MISO next (6,037 / 3,659 MW). |
| **D3 MISO RETIREMENT / G3** | The G3 cap-grain `retire.total_gw` PASS→FAIL t1h regression | QUEUED — re-scoped, confirmed | — | Fable | D1 §6 CONFIRMS the FC-2 I13 cobweb half is superseded (live `miso-t1f` reads I13 PASS, FC-2 CAVEAT). Carry I13 as **closed-but-unattributed** — no session claims the repair, no control isolates it, the inducing FF-2C flip is still on. The G3 t1h regression stands untouched and is D3's real scope. |
| **D4 ERCOT I3 + FORECAST NET-REVENUE** | I3 slack (now 0.08–0.41% of load) + I12 band; forecast-year scarcity-rent treatment in the entry/retirement screens | **BLOCKED — Q1 still pending** | — | Fable | The 2023 arc is demonstrably still live: keeper promoted 2026-08-24 (`231-tie-zone-measured`), and the owner granted a **rule-16 waiver for a 2023-only ERCOT keeper** on 2026-08-23 (regime-difference ground). D1's correction makes ERCOT's I3 miss 2.7×–20.5× worse than the board carried. |
| **D5 FC-4 CO2 CROSSOVER (PJM first, then ERCOT)** | Attribute the crossover CO2 miss; fix the input derivation, not the score | **ISSUED 2026-08-24** | `claude/capx-d5-crossover-co2` | Fable | PJM is the shortest path to the program's first T2 candidate: gate (a) already PASSES, leg (b) is one I7 miss (D2-REMEASURE), leg (c) fails on FC-4 CO2 **alone**. Close both and only (d) owner auth remains. |
| **D6 FC-3 CURVE-ON OVER-FIRE (T1-H)** | Four curve legs FAIL on curve-ON over-build | QUEUED | — | Fable | All four re-scored 2026-08-24 by the FFR-3A tool (`c0562d9`) — determinations unmoved (HOLD), now provenance-stamped. Note the new FC-7 FAIL (below) applies to these legs. |
| **D7 T2 GATE RE-SCORE** | Re-run FF-2D per ISO once lanes land; move gate-openers to T2 scheduling | QUEUED | — | Opus | Re-order after D2-REMEASURE: if I7 closes for PJM/NYISO/NEISO, D7 becomes the immediate next lane for those three. |
| **D8 FORECAST PROVENANCE DEBT** (NEW) | 7 forecast bundles track no `run_config.json` → FC-7 FAIL on every one; 3 `t1x-ffr2a` legs' FC-1/FC-2 are unreproducible from any checkout | QUEUED | — | Fable | Surfaced by `c0562d9` (not a lane I chartered). FC-7 is a *required* category — this is a standing provenance failure across the T1-H/T1-X evidence base, and it will block any clean gate reading later. Cheap to fix at registration time. |

## 2. Backcast-track watch (deconfliction; last seen 2026-08-24 @ `d84a95e`)

| item | state | Δ since refresh #1 |
|---|---|---|
| ERCOT keeper | **`2026-08-24-231-tie-zone-measured`** — full-span 2023–2025, det **NOT-YET** (fails `price_mean` + `price_shape`; C3c ledgered ×1, **C3c-2023 now PASSES** — spent caveat pruned) | **CHANGED** (was `ercot223-arm-eventrelease`). Tie-zone interchange + measured-GTC restoration. |
| ERCOT governance | **Owner waived rule 16 [R-ALLYEARS] for ERCOT 2023 specifically** (2026-08-23, verbatim: *"you can do a 1 year keeper on ERCOT 2023 because it is a fundamentally different market design… rule 16 be damned"*), pre-authorizing a 2023-only keeper if 3-yr retention degraded. Retention **held**, so the promoted keeper is the standard 3-year form and the waiver went unspent. | **NEW** |
| CAISO keeper | `2026-08-17-caiso-200-h1-memberpanel` — det NOT-YET (C3a sole) | unchanged. caiso-217 partial landing + caiso-218 Path-15/26 operating-limit survey → **decisive null + identifiability kill**. |
| MISO keeper | `2026-08-22-miso-177-rho-measured` — det NOT-YET (C3a-2025 sole) | unchanged. miso-180 anchored-spread → verdict **I** (inert); miso-181 coincident-peak seam envelope → **R** (refuted at its K-c conditioning kill). Queue fell back to D-3. |
| PJM / NYISO / NEISO | CALIBRATED, `complete` held: `pjm-162-inputclock`, `nyiso-152-duty-complete`, `neiso-99-joint-p1` | unchanged |
| Markers / freeze | `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY; holdout spend freeze **ACTIVE** | unchanged |
| Gate-(a) reading | pass: PJM, NYISO, NEISO (= `complete` membership); fail on marker: ERCOT, CAISO, MISO | unchanged — no ISO's gate (a) moved |

**Deconfliction status: clean.** No chartered capacity-expansion lane has touched backcast
territory, and no backcast session has moved a forecast gate. The ERCOT keeper promotion
re-keyed the board's ERCOT display field (D1 picked it up) without moving gate (a).

## 3. Owner-tier questions on file

| # | question | asked | answer |
|---|---|---|---|
| **Q1** (D4 coordination) | Has the ERCOT 2023 backcast scarcity arc settled a scarcity representation the forecast net-revenue lane should build on, or is it still in flight (→ charter the I3-invariant half only)? Evidence since asking says **still in flight** — a keeper promoted 2026-08-24 and a rule-16 waiver granted 2026-08-23. | 2026-08-23, re-put 2026-08-24 | **PENDING** |
| **Q2** (D1 escalation, §5 of its FINDING) | Gate leg (c) consistency: three ISOs have **no T1-X run at all** — NEISO scored `fail` on that basis (neiso-88 precedent), CAISO and NYISO still scored `na`. Apply the NEISO reading uniformly (→ both move `na`→`fail`, `"c"` added to `closed_on`)? **Director recommendation: YES, uniformly.** It is a gate outcome, so it is put to the owner rather than edited. **Zero schedulability impact** — both gates are already `open: false` on other legs. | 2026-08-24 | **PENDING** |

## 4. Prompt issuance record

| date | lane | branch | model | profile | outcome |
|---|---|---|---|---|---|
| 2026-08-23 | D1 BOARD-REFRESH | `claude/capx-d1-board-refresh` | Opus | code | **LANDED** `c02f766` |
| 2026-08-23 | D2 ADEQUACY — NYISO | `claude/capx-d2-adequacy-nyiso` | Fable | nyiso | **WITHDRAWN, never run** — superseded by D2-REMEASURE (§0). Re-charter only for a residual that survives the re-measurement. |
| 2026-08-24 | D2-REMEASURE | `claude/capx-d2-remeasure-t1f` | Fable | all | issued |
| 2026-08-24 | D5 CROSSOVER CO2 | `claude/capx-d5-crossover-co2` | Fable | pjm | issued |
