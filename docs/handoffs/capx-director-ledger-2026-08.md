# Capacity-Expansion Workstream Director — Ledger

Standing coordination ledger for the capacity-expansion (Forecast Finalization
Program) track. Maintained by the director session on branch
`claude/capx-director-ledger`; one refresh = one commit when anything changes.
The director charters sessions and tracks state — it never runs solves, never
edits `src/market_sim/`, and never charters backcast-calibration work (that
track is the owner's own CAISO/ERCOT/MISO sessions, watched here for
deconfliction only).

**Charter date:** 2026-08-23 · **Last refresh:** 2026-08-24 (refresh #4) ·
**HEAD at refresh:** `d0c426b`

---

## 0b. Refresh #4 — Q1 ANSWERED (Y-C); D2-NYISO landed and REFUTED half of the director's own §0 hypothesis

**1. Card Y signed (Y-C) — HOLD THE LANE OPEN**, against the ERCOT lane's own Y-A
recommendation; both records stand (`0e53012`). The signature does NOT lift Q-B/R-A, does not
license any `R`/`I`/`G` re-test, and leaves the ercot-225 gate card open. Same session then
measured the one named-unmeasured object anyway: the **`NE_LOB` timing Phase-0 CLOSES on all
four zonal-grain drivers** (`144599b`, `33d7b70`).
→ **Q1 IS ANSWERED. The ERCOT 2023 arc stays LIVE, so D4 is chartered at the I3-INVARIANT HALF
ONLY** and the forecast net-revenue half stays held — exactly the original charter's fallback.

**2. A D2-NYISO session ran** (PR #4251, branch `claude/capx-d2-adequacy-nyiso-yxv6v0`) on the
prompt issued at refresh #1, which refresh #2 had marked withdrawn. It was worth running, and
its finding (`docs/handoffs/FINDING-capx-d2-adequacy-nyiso-2026-08-24.md`) is the best evidence
this track has produced:

- **THE DIRECTOR'S §0 HYPOTHESIS IS REFUTED FOR NYISO, and I record that against interest.**
  FFR-1C hydro accreditation is **already inside** the FFR-3A-2 verdicts, worth **1,763.3 MW**,
  reproduced to the digit: the pre-hydro ledger is **30,322.2 MW** — which *is* the board's
  stale "firm 30.3 GW" figure. So the 1.8 GW that closed between FF-2D and FFR-3A-2 IS the
  hydro fix. The I7 verdicts are **not** pre-fix, and a blanket six-ISO re-run is no longer
  justified on that ground. What survives from §0 is narrower and still true: the board's
  *stated root cause* is stale prose.
- **The residual 35.7 MW (0.111 %) is a BASE-YEAR SNAPSHOT result.** `evolve_fleet` is skipped
  when `fleet is None`, so the base year runs **no capacity evolution at all** — no adequacy
  backstop, no retirement screen, no entry. **No capacity mechanism can respond to it, by
  construction.** That reframes base-year I7 program-wide: it is not a capacity-evolution defect.
- **Forks 2 (fleet vintage) and 3 (requirement mismatch) are CLOSED on evidence.**
- **The one provable gap:** NYISO credits **ZERO external firm capacity**, while
  ERCOT/PJM/CAISO/NEISO all carry an `ADEQUACY_EXTERNAL_TIE_FIRM_MW` entry — and the model
  itself floors **900 MW of always-on HQ firm import** in NYISO dispatch.
- **No I7-closing fix was shipped, deliberately and correctly.** The in-repo 900 MW candidate is
  an inherited ladder constant, not a published RA accreditation; shipping it would breach
  rules 5 and 13 "in the one place where a wrong number is invisible: an invariant it happens to
  clear." Only a test-only hydro-vintage-clamp guard was committed (`7176c6d`).
- **Its pre-stated successor** is a bounded, unrestricted data intake — NYISO Gold Book external
  capacity — with the honesty test declared in advance: any real value is O(10²–10³) MW against a
  36 MW gap, **and that overshoot is the evidence it is honest rather than tuned**.

**3. Lane consequence.** D2-REMEASURE's blanket six-ISO re-run is **superseded by D2-B**: the
NYISO session proved the question is answerable from **committed artifacts with no solve at all**
(`results/ffr1c/{before,after}-{caiso,miso,nyiso}/` are committed; PJM/NEISO/ERCOT are not).
Records first, solves only where the records cannot answer.

---

## 0a. Refresh #3 — no chartered lane has started; the ERCOT arc put its own termination card to the owner

**Neither D2-REMEASURE nor D5 exists as a branch** (`git ls-remote` 2026-08-24: the only
`capx` ref is this ledger). Both prompts stand unchanged and are still the open batch; the
only thing that moved under them is `main` (`7cf572e` → `8fd031d`), so both must fetch fresh.

**Q1 now has an instrument, and it is not mine to sign.** The ERCOT backcast lane opened
`docs/DECISION-CARD-ercot233-2023-object-closure-2026-08-24.md` — **OPEN, awaiting owner
signature** — asking whether the ERCOT 2023 price object is *formally closed as an adjudicated
model-class limitation*, with the lane RESTING at the current keeper until **Door D**
(2026 SOM RTC+B-era anchors, ~mid-2027). Its own recommendation is **Y-A: CLOSE and REST, and
re-point ERCOT session bandwidth to the other ISOs' queues**; Y-B adds one read-only NE_LOB
Phase-0 epilogue; Y-C (hold open) is recommended against on an empty admissible-candidate list.

**Whichever way the owner signs it answers Q1 for this track**, because the card is exactly
the "has the arc settled?" question in the ERCOT lane's own words. Reading for D4:
- **Y-A or Y-B → D4 is chartered IN FULL.** A closed object is a settled record: the forecast
  net-revenue half consumes the adjudicated scarcity representation (Door A conduct closed and
  non-transferable, the ORDC/RTORPA decontamination lineage ercot-213/215, C3c as the ledgered
  model-class limit) rather than competing with a live arc. Card Y explicitly re-points
  bandwidth away from ERCOT backcast, which removes the collision risk the D4 hold was for.
- **Y-C → D4 stays at the I3-invariant half only**, exactly as the original charter said.
The keeper this rests on now reads 2023 **−38.0 % / 0.696 / 93** — and **C3c-2023 is a clean
PASS, the first ERCOT keeper ever to clear the 2023 tail criterion** (93 of 181 = 0.51×).

**A forecast-lane item was handed to this track by a backcast session** — see D9 below.

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
| **D2-REMEASURE** ~~(supersedes the per-ISO D2 charters)~~ **SUPERSEDED at refresh #4 by D2-B** | Re-run all six T1-F legs (2026–2030, forecast mode) at HEAD and re-score FC-1, so the I7/I12 verdicts sit on the post-FFR-1C hydro-accreditation code | **RETIRED, never run** | `claude/capx-d2-remeasure-t1f` | Fable | Retired because its premise was refuted (§0b.2): hydro accreditation is already in the FFR-3A-2 verdicts, so there is no pre-fix HEAD to re-measure off. §0 above. Forecast-mode 2026+ = unrestricted (rule 22). Register on the FORECAST namespace (rule 15). Expected: NYISO/PJM/NEISO I7 may close outright → three gate-(a) passers clear FC-1. |
| **D2-A2 per-ISO follow-ups** (NYISO / MISO / CAISO) | Root-cause whatever I7/I12 residual SURVIVES the re-measurement | **QUEUED — deliberately held** | — | Fable | Chartering a fix before the re-measurement would risk fixing what FFR-1C already fixed — the exact error D1 just caught on I4. CAISO is the deepest (I7 2026–2029 to 9,243 MW + I12 + 65.5% backstop share); MISO next (6,037 / 3,659 MW). |
| **D3 MISO RETIREMENT / G3** | The G3 cap-grain `retire.total_gw` PASS→FAIL t1h regression | QUEUED — re-scoped, confirmed | — | Fable | D1 §6 CONFIRMS the FC-2 I13 cobweb half is superseded (live `miso-t1f` reads I13 PASS, FC-2 CAVEAT). Carry I13 as **closed-but-unattributed** — no session claims the repair, no control isolates it, the inducing FF-2C flip is still on. The G3 t1h regression stands untouched and is D3's real scope. |
| **D4-I3 ERCOT SCARCITY-SLACK INVARIANT** (net-revenue half HELD) | I3 slack (now 0.08–0.41% of load) + I12 band; forecast-year scarcity-rent treatment in the entry/retirement screens | **UNBLOCKED at HALF scope — chartering next batch** | — | Fable | **Q1 ANSWERED 2026-08-24: card Y signed Y-C, hold the lane open** → the arc is live, so the net-revenue half STAYS HELD and only the I3 invariant is in scope. Prior note: keeper promoted 2026-08-24 (`231-tie-zone-measured`), and the owner granted a **rule-16 waiver for a 2023-only ERCOT keeper** on 2026-08-23 (regime-difference ground). D1's correction makes ERCOT's I3 miss 2.7×–20.5× worse than the board carried. |
| **D5 FC-4 CO2 CROSSOVER (PJM first, then ERCOT)** | Attribute the crossover CO2 miss; fix the input derivation, not the score | **ISSUED 2026-08-24** | `claude/capx-d5-crossover-co2` | Fable | PJM is the shortest path to the program's first T2 candidate: gate (a) already PASSES, leg (b) is one I7 miss (D2-REMEASURE), leg (c) fails on FC-4 CO2 **alone**. Close both and only (d) owner auth remains. |
| **D6 FC-3 CURVE-ON OVER-FIRE (T1-H)** | Four curve legs FAIL on curve-ON over-build | QUEUED | — | Fable | All four re-scored 2026-08-24 by the FFR-3A tool (`c0562d9`) — determinations unmoved (HOLD), now provenance-stamped. Note the new FC-7 FAIL (below) applies to these legs. |
| **D7 T2 GATE RE-SCORE** | Re-run FF-2D per ISO once lanes land; move gate-openers to T2 scheduling | QUEUED | — | Opus | Re-order after D2-REMEASURE: if I7 closes for PJM/NYISO/NEISO, D7 becomes the immediate next lane for those three. |
| **D8 FORECAST PROVENANCE DEBT** (NEW) | 7 forecast bundles track no `run_config.json` → FC-7 FAIL on every one; 3 `t1x-ffr2a` legs' FC-1/FC-2 are unreproducible from any checkout | QUEUED | — | Fable | Surfaced by `c0562d9` (not a lane I chartered). FC-7 is a *required* category — this is a standing provenance failure across the T1-H/T1-X evidence base, and it will block any clean gate reading later. Cheap to fix at registration time. |
| **D9 MISO FORECAST INTERCHANGE FALLBACK — `ba_code="SOCO"`** (NEW, handed in) | The forecast fallback routes MISO-South interchange through `ba_code="SOCO"` — the one counterparty MISO **essentially never exports to** (0.1–0.3 % of the pool's gross). Superseded in the keeper's BACKCAST years (the armed ladder overwrites every South band row) but **live in the FORECAST path** | QUEUED — **NEW** | — | Fable | Handed to this program explicitly by the MISO backcast lane (miso-183, `cbfc9a6`, calibration-log/miso.md ~L8618): *"live only in the forecast fallback — a forecast-lane rule-14 item, handed to that program."* Trace: `model/interchange/miso.py:280` → `import_nodes.py:598–628`. Rule 14 [R-ACCURATE]. **Likely bears on MISO's I7/I12** — import accounting feeds adequacy — so sequence it WITH the D2-A2 MISO follow-up, not before D2-REMEASURE. |
| **D2-B I7 LEDGER DECOMPOSITION** (NEW — replaces D2-REMEASURE) | Apply the NYISO session's method to the four other I7 ISOs (PJM, NEISO, MISO, CAISO): reproduce each I7 leg from committed ledgers, decompose the gap, adjudicate the same three forks. **Records first; a solve only where records cannot answer.** | **ISSUED 2026-08-24** | `claude/capx-d2b-i7-ledger` | Fable | `results/ffr1c/{before,after}-{caiso,miso,nyiso}/` are COMMITTED; PJM/NEISO/ERCOT are not, so those need another route. Carries the base-year no-evolution reframing (§0b.2) as a program-wide question, not a NYISO quirk. |
| **D2-NYISO** | Root-cause NYISO's I7 base-year miss | **LANDED** (PR #4251, `0a2238c`) | `claude/capx-d2-adequacy-nyiso-yxv6v0` | Opus | `FINDING-capx-d2-adequacy-nyiso-2026-08-24.md`. Root cause adjudicated; no I7-closing fix shipped, deliberately (§0b.2). Successor = D2-NYISO-INTAKE. |
| **D2-NYISO-INTAKE** (NEW) | Fetch the NYISO Gold Book external-capacity accreditation and add NYISO to `ADEQUACY_EXTERNAL_TIE_FIRM_MW` on the FF-2B construction | **ISSUED 2026-08-24** | `claude/capx-d2-nyiso-extcap-intake` | Fable | The pre-stated successor of the D2-NYISO finding §6. Data intake is UNRESTRICTED (rule 22 channel 1, no marker). Gold Book payloads are gitignored — re-fetch per `data/raw/NYISO/README.md`. NEVER the 4,350 MW Simultaneous Import Limit (a deliverability limit, the error CAISO's own entry explicitly rejects). |

## 2. Backcast-track watch (deconfliction; last seen 2026-08-24 @ `d0c426b`, refresh #4)

| item | state | Δ since refresh #1 |
|---|---|---|
| ERCOT keeper | **`2026-08-24-231-tie-zone-measured`** — full-span 2023–2025, det **NOT-YET** (fails `price_mean` + `price_shape`; C3c ledgered ×1, **C3c-2023 now PASSES** — spent caveat pruned) | **CHANGED** (was `ercot223-arm-eventrelease`). Tie-zone interchange + measured-GTC restoration. |
| ERCOT governance | **Owner waived rule 16 [R-ALLYEARS] for ERCOT 2023 specifically** (2026-08-23, verbatim: *"you can do a 1 year keeper on ERCOT 2023 because it is a fundamentally different market design… rule 16 be damned"*), pre-authorizing a 2023-only keeper if 3-yr retention degraded. Retention **held**, so the promoted keeper is the standard 3-year form and the waiver went unspent. | **NEW** |
| CAISO keeper | `2026-08-17-caiso-200-h1-memberpanel` — det NOT-YET (C3a sole) | unchanged. caiso-217 partial landing + caiso-218 Path-15/26 operating-limit survey → **decisive null + identifiability kill**. |
| MISO keeper | `2026-08-22-miso-177-rho-measured` — det NOT-YET (C3a-2025 sole) | unchanged. miso-180 anchored-spread → verdict **I** (inert); miso-181 coincident-peak seam envelope → **R** (refuted at its K-c conditioning kill). Queue fell back to D-3. |
| PJM / NYISO / NEISO | CALIBRATED, `complete` held: `pjm-162-inputclock`, `nyiso-152-duty-complete`, `neiso-99-joint-p1` | unchanged |
| Markers / freeze | `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY; holdout spend freeze **ACTIVE** | unchanged |
| Gate-(a) reading | pass: PJM, NYISO, NEISO (= `complete` membership); fail on marker: ERCOT, CAISO, MISO | unchanged — no ISO's gate (a) moved |
| **Refresh #3 movements (all backcast, none moved a keeper, marker or forecast gate)** | **ERCOT** ercot-232 exhaustion record + ercot-233 **card Y OPEN, awaiting owner signature** (§0a). **MISO** miso-183 South-seam basis adjudicated **V-TRADE — a real defect on a new basis-free measure** (measured MISO-South pushed ~2.4 GW out across its boundaries in the 2025 scarce set; the real RDT bound South→North in 32 of 2025's 47 scarce hours — *the keeper's internal posture runs backward*; object survives at ≥0.93 GW; wheel/basis-artifact hypothesis refuted three ways). **CAISO** caiso-219 §F.3a gen-pocket export-limit Phase-0 — **second decisive null** (no citable Kern/Tehachapi collector export limit in flow MW exists; the sub-zonal record is accreditation headroom, not a flow rating). **Entry-signal** L-1 dual-replay probe parameterized by ISO, CAISO arm added. | **NEW** |

**Deconfliction status: clean.** No chartered capacity-expansion lane has touched backcast
territory, and no backcast session has moved a forecast gate. The ERCOT keeper promotion
re-keyed the board's ERCOT display field (D1 picked it up) without moving gate (a).

## 3. Owner-tier questions on file

| # | question | asked | answer |
|---|---|---|---|
| ~~**Q1**~~ **ANSWERED** (D4 coordination) | Has the ERCOT 2023 backcast scarcity arc settled a scarcity representation the forecast net-revenue lane should build on, or is it still in flight (→ charter the I3-invariant half only)? Evidence since asking says **still in flight** — a keeper promoted 2026-08-24 and a rule-16 waiver granted 2026-08-23. | 2026-08-23, re-put 2026-08-24 | **ANSWERED 2026-08-24 — card Y signed (Y-C), hold the lane open, against the lane's own recommendation. D4 = I3-invariant half only; net-revenue half held.** |
| **Q2** (D1 escalation, §5 of its FINDING) | Gate leg (c) consistency: three ISOs have **no T1-X run at all** — NEISO scored `fail` on that basis (neiso-88 precedent), CAISO and NYISO still scored `na`. Apply the NEISO reading uniformly (→ both move `na`→`fail`, `"c"` added to `closed_on`)? **Director recommendation: YES, uniformly.** It is a gate outcome, so it is put to the owner rather than edited. **Zero schedulability impact** — both gates are already `open: false` on other legs. | 2026-08-24 | **PENDING** |

### Q3 (NEW, refresh #4) — `entry_lookahead_reprice` disarm, ERCOT forecast default

The ERCOT entry-signal disarm probe adjudicated the cell **fc K → O** (`2aaaffa`) and states
plainly: **"Arming the disarm as the lane default is the owner's decision."** The trade is
real in both directions — the disarm repairs measured signal defects L-1 attributed to this
mechanism (locational dispersion where the shipped object is zone-flat by construction, steady
long-duration storage entry, wind entering at all) but swaps a forward-looking-but-structurally-
wrong object for a structurally-right-but-backward-looking one, and worsens the terminal reserve
margin 25.19 % → 40.24 %. Neither construction is the developer pro-forma, so rule 1 cuts both
ways and the probe correctly refused to self-adopt. `entry_lookahead_reprice=True` is one of the
FF-2C shipping posture flips, so this is a **forecast-track default**. **PENDING — owner.**

## 4. Prompt issuance record

| date | lane | branch | model | profile | outcome |
|---|---|---|---|---|---|
| 2026-08-23 | D1 BOARD-REFRESH | `claude/capx-d1-board-refresh` | Opus | code | **LANDED** `c02f766` |
| 2026-08-23 | D2 ADEQUACY — NYISO | `claude/capx-d2-adequacy-nyiso` | Fable | nyiso | **WITHDRAWN, never run** — superseded by D2-REMEASURE (§0). Re-charter only for a residual that survives the re-measurement. |
| 2026-08-24 | D2-REMEASURE | `claude/capx-d2-remeasure-t1f` | Fable | all | issued |
| 2026-08-24 | D5 CROSSOVER CO2 | `claude/capx-d5-crossover-co2` | Fable | pjm | issued r#2; **NOT STARTED — re-issued r#4** |
| 2026-08-24 | D2-REMEASURE | `claude/capx-d2-remeasure-t1f` | Fable | all | **RETIRED r#4, never run** — premise refuted |
| 2026-08-24 | **D2-B I7 LEDGER DECOMPOSITION** | `claude/capx-d2b-i7-ledger` | Fable | code | issued r#4 |
| 2026-08-24 | **D2-NYISO-INTAKE** (Gold Book external capacity) | `claude/capx-d2-nyiso-extcap-intake` | Fable | nyiso | issued r#4 |
