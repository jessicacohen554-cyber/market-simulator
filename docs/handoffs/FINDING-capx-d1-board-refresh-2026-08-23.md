# FINDING — capx-D1 board refresh: the A1/I4 close-out, adjudicated cross-ISO

**Session:** capx-D1 (capacity-expansion / Forecast Finalization track), 2026-08-24
**Branch:** `claude/capx-d1-board-refresh-nfb31y` · **Base:** `origin/main` @ `3ca40e9b6534`
**Chartered by:** the capacity-expansion director (`docs/handoffs/capx-director-ledger-2026-08.md` §3)
**Scope:** **RECORDS ONLY.** No LP was built, no year was solved, no forecast run was scored or
re-scored, nothing was registered on either dashboard, no mechanism was tested and no
mechanism-matrix cell was minted (rule 28d). No out-of-training backcast year was touched; the
holdout spend freeze is ACTIVE (rule 22). Every number below is read from a committed artifact.

**Deliverable:** `frontend/data/forecast/program-status.json` re-derived from the live committed
verdict records — **36 fields changed, 0 determinations, 0 verdicts and 0 gate outcomes moved** —
plus the cross-ISO A1/I4 adjudication that `neiso-88` §7 explicitly left for this lane.

---

## 0. Headline

> **The A1/I4 capacity-accounting leak is CLOSED, and closing it cleared FC-1 in exactly zero
> ISOs — because adequacy accounting was underneath it.** The board had been calling I4 the
> dominant T1-F blocker (4/6 ISOs) and promising that fixing it would clear PJM and NEISO. I4
> was in fact fixed on **2026-07-31** by the FFR-1A confirmed-derate recorder, three weeks before
> the board last claimed otherwise; PJM and NEISO did not clear FC-1, because each has an I7
> adequacy miss the leak had been masking on the board's own row.
>
> **The live dominant blocker is adequacy accounting, 6 of 6 ISOs:** I7 in CAISO/PJM/MISO/NYISO/
> NEISO, I12 in ERCOT/CAISO.

Two corrections run **against** the board's favour and are reported at full magnitude (rule 1):
ERCOT's I3 slack is 2.7×–20.5× worse than the board carried, and ERCOT's T1-X 2025 price no
longer converges into band.

---

## 1. What the board was reading, and why it was wrong

`frontend/data/forecast/ff-verdicts.json` carries **two vintages under different key shapes**:

| key shape | vintage | provenance |
|---|---|---|
| `<iso>-t1f` (un-suffixed) | **LIVE** | `session=FFR-3A-2`, `scored_at_sha=8ba59281` — all six |
| `<iso>-t1f-ff2d` | **SUPERSEDED, preserved** | `"FF-2D baseline, preserved verbatim by FFR-3A-2 before the bare key was refreshed. Quotable as the regression baseline."` |

The board's `blocking_rows`, `fc` maps, gate (b) details and both cross-ISO prose blocks had been
written from the **`-ff2d` vintage** and never re-derived when FFR-3A-2 refreshed the bare keys.
The `-ff2d` records are not stale by accident — they are *deliberately preserved* as the
regression baseline — so the defect is not that they exist, it is that the board was quoting a
baseline as if it were the current state.

**Live FC-1 fail sets, read directly from the un-suffixed keys:**

| ISO | live FC-1 FAIL | superseded `-ff2d` FC-1 FAIL |
|---|---|---|
| ERCOT | `{I12, I3}` | `{I3}` |
| CAISO | `{I12, I3, I7}` | `{I3, **I4**, I7, I9}` |
| PJM | `{I7}` | `{**I4**}` |
| MISO | `{I7}` | `{**I4**, I7}` |
| NYISO | `{I7}` | `{I7}` |
| NEISO | `{I7}` | `{**I4**}` |

The director's 2026-08-23 pre-read was **independently re-derived and confirmed on every item**,
with one addition it could not have seen: ERCOT's designated keeper moved again on 2026-08-24
(§4.1).

---

## 2. The A1/I4 close-out — cross-ISO adjudication

### 2.1 Verdict

**I4 appears in no live FC-1 fail set, in any of the six ISOs.** `neiso-88` §1.1 established this
for four (NEISO, PJM, MISO, CAISO) and left the cross-ISO row for this lane; it is confirmed here
and extended to the full six.

### 2.2 A precision the "6/6 closed" phrasing loses

The six ISOs are **not** in the same state, and this FINDING declines to flatten them:

- **REPAIRED LEAK — four ISOs.** CAISO (2027 `gas_st` off by 1,333.0 MW), PJM (2029 `coal` 742.6
  MW), MISO (2029 `coal` 1,639.8 MW), NEISO (2028 `coal` 54.0 MW) each carried a demonstrated I4
  failure in the `-ff2d` vintage and carry none live. For these, "closed" means *a leak was found
  and plugged*.
- **NEVER LEAKED — two ISOs.** ERCOT and NYISO carry no I4 failure in **either** vintage. Their
  "closed" reading is an absence of evidence of a leak, not evidence of a repair.

Reporting both as "closed in all six" would be true but would imply six repairs where there were
four. The load-bearing claim — *I4 is a blocker nowhere* — holds for all six.

### 2.3 Where the closure is recorded, and since when

Three independent committed records, none of which is a re-score:

1. **The mechanism.** `scripts/check_forecast_invariants.py::check_i4_capacity_accounting`
   docstring: *"`confirmed_derates` (FFR-1A / FR-1) are confirmed-registry rows that shrink a
   surviving plant-binned tranche in place — MW that leaves the fleet without a `retirements`
   row. Ledgers written before the FFR-1A recorder carry no such key; `led.get` keeps them
   scoreable (their derated MW is then genuinely unexplained, **which is exactly the A1 leak this
   invariant exists to catch**)."* The writer is
   `src/market_sim/model/capacity_evolution/evolve.py` (`events.setdefault("confirmed_derates", …)`).
2. **The date and the root cause.** `docs/handoffs/ffr-1a-confirmed-exit-accounting-2026-07-31.md`
   §1 — landed **2026-07-31**, finding FR-1, *"BLOCKER"*. Root cause verbatim: `apply_confirmed_exits`
   derates plant-binned tranches **in place** (the `unit_id` survives with a smaller `pmax_mw`)
   while the events recorder emitted retirement rows only for unit_ids *absent* from the surviving
   fleet, and the documented `confirmed_derates` ledger key *"had a reader … but **no writer**."*
   Captured live in the NEISO before-probe: `coal before 108.0 → after 54.0`, `retirements: []`,
   `confirmed_derates: <key absent>` → the exact `2028:coal off by 54.0 MW` the board still carried.
3. **The before/after, on committed arms.** `frontend/data/hindcast/invariant-failures.json`
   `wave1_note`: *"pjm-2026-2030-ffr1a-before and neiso-2026-2030-ffr1a-before carry I4, and
   neither of their arm1/arm2 successors does — the confirmed-exit derate ledgering (FR-1) closed
   I4 on both ISOs."*

That file's declared-failure ledger currently declares **zero** runs — i.e. **no committed
hindcast sidecar carries any invariant FAIL at HEAD**. Its `wave1_note` is a narrative about arms
whose sidecars are no longer committed; the live verdict evidence is `ff-verdicts.json`.

### 2.4 What the board's I4 row asserted, clause by clause

Former text: *"Steam/coal MW removed with no matching ledger retirements record — the dominant
T1-F blocker (4/6 ISOs). Fix A1 and NEISO + PJM clear FC-1. Un-actioned since FF-0B; the
ledger_version stamp did NOT touch it."*

| clause | status |
|---|---|
| "the dominant T1-F blocker (4/6 ISOs)" | **FALSE** — a blocker in 0/6 |
| "Fix A1 and NEISO + PJM clear FC-1" | **FALSE, and the most costly clause** — A1 *was* fixed and neither cleared: PJM fails I7 (2030, 366 MW), NEISO fails I7 (2028, 218 MW) |
| "Un-actioned since FF-0B" | **FALSE** — actioned at FFR-1A, 2026-07-31 |
| "the ledger_version stamp did NOT touch it" | true of the stamp; irrelevant, since the recorder did |

The second clause is the one that mattered: it pointed the program's remaining T1-F work at a
lane that had been closed for three weeks, and it did so for the two ISOs *closest to the gate*.

---

## 3. Path correction — `ff-verdicts.json` is the committed carrier

`neiso-88` §1.1 cites its evidence as
`frontend/data/hindcast/<iso>-2026-2030-ffr3a2-t1f.json` (e.g. `neiso-2026-2030-ffr3a2-t1f.json`).

**Those files do not exist at HEAD, and — verified with `git log --all --name-only` over the full
history — have never been committed at any point in this repository.** A search of every path in
every commit on every ref returns **zero** paths containing `2026-2030`. `frontend/data/hindcast/`
holds eight files at HEAD, all `2021-2025` realized legs plus `invariant-failures.json`.

This is a citation defect, **not** an evidence defect: every verdict `neiso-88` quoted is real and
committed, in `frontend/data/forecast/ff-verdicts.json` under the un-suffixed per-tier keys. The
FFR-3A-2 sidecars were session-local artifacts that were read but never committed; the verdict
snapshot is what got committed.

**Standing correction for any lane citing FFR-3A-2 T1-F evidence:** cite
`frontend/data/forecast/ff-verdicts.json` key `<iso>-t1f`, not a `frontend/data/hindcast/`
sidecar path. Recorded in the board's own `sources` list so the next reader hits it there too.

**A related vintage trap, recorded so nobody re-derives the wrong way.** The rule "un-suffixed =
live" holds for **t1f** but **not** for t1x/t1h. There the un-suffixed keys are also FFR-3A-2
(`8ba59281`), while the newer FFR-3A-3 / FFR-3A-4 re-measurements carry **explicit dated keys**
(`<iso>-2023-2027-crossover-ffr3a3-t1x`, `<iso>-2021-2025-realized-ffr3a3-t1h`,
`miso-2023-2027-crossover-ffr3a4-t1x`) at later shas (`e2a422c1`, `6fbd3f28eb9a`) — which the
board's own `t1x_provenance` / `t1h_provenance` notes already name correctly. For ERCOT and PJM
the two vintages are identical metric-for-metric, so nothing turned on it here; a future lane
reading t1x/t1h must resolve through the provenance note, not the key shape.

---

## 4. Every row changed — before / after / citation

36 fields. Grouped; the citation for every "after" is the live record named in its row.

### 4.1 Top-level `keeper` display fields — 6 changes

All six were stale. Re-keyed from `frontend/data/backcast/keepers/<ISO>.json`, determinations
re-read from `frontend/data/backcast/status/<ISO>.js` (committed artifacts; **no
`calibration_verdict.py` run, no solve**).

| ISO | before | after (live) | determination | full-span |
|---|---|---|---|---|
| ERCOT | `2026-08-03-ercot158-pool-arm` | `2026-08-24-231-tie-zone-measured` | NOT-YET | 2023-25 |
| CAISO | `2026-08-04-caiso164-zonal-loss-surface` | `2026-08-17-caiso-200-h1-memberpanel` | NOT-YET | 2023-25 |
| PJM | `2026-08-03-pjm-151-seam-envelope` | `2026-08-15-pjm-162-inputclock` | CALIBRATED | 2023-25 |
| MISO | `2026-08-04-miso-124-dualfuel-rearm` | `2026-08-22-miso-177-rho-measured` | NOT-YET | 2023-25 |
| NYISO | `2026-08-04-nyiso-120-c119-scope` | `2026-08-22-nyiso-152-duty-complete` | CALIBRATED | 2023-25 |
| NEISO | `2026-08-05-neiso-83-ca1-reclass` | `2026-08-17-neiso-99-joint-p1` | CALIBRATED | 2023-25 |

**ERCOT gate-(a) block re-keyed too** (`2026-08-20-ercot223-arm-eventrelease` →
`2026-08-24-231-tie-zone-measured`). This is **newer than the director's 2026-08-23 pre-read** —
the ercot-231 tie-zone / GTC-partition promotion landed 2026-08-24, after the director-records v12
stamp at `1b8ddaca2165`. **The gate verdict is unaffected:** both keepers are NOT-YET and ERCOT is
absent from `complete` on both sides. Same class of correction as the v12 NYISO/MISO re-keys.

**Gate (a) re-verified, unchanged:** `complete` block membership is exactly `{NEISO, NYISO, PJM}`;
`final` is empty. Pass = PJM/NYISO/NEISO, fail = ERCOT/CAISO/MISO on the marker. The board's
gate-(a) statuses were already correct and were **not** touched.

### 4.2 `fc` maps — 4 maps changed (5 cells)

| ISO | field | before | after | live basis |
|---|---|---|---|---|
| ERCOT | FC-2 | CAVEAT | **FAIL** | `ercot-t1f` FC-2 status FAIL (row1 I12 FAIL + row6 sustained-VOLL FAIL) |
| CAISO | FC-2 | CAVEAT | **FAIL** | `caiso-t1f` FC-2 FAIL (row1 I12 FAIL + row4 backstop 65.5% FAIL) |
| PJM | FC-2 | PASS | **CAVEAT** | `pjm-t1f` FC-2 CAVEAT (I12 WARN; backstop 23.6%) |
| MISO | FC-2 | FAIL | **CAVEAT** | `miso-t1f` FC-2 CAVEAT — I13 PASS, backstop 9.2% PASS |
| MISO | FC-4 | *(absent)* | **FAIL** | `miso-2023-2027-crossover-ffr3a4-t1x` FC-4 FAIL — the board's own `c_crossover_gap` already cited it; the map just omitted the row |

NYISO and NEISO `fc` maps were already correct and untouched.

### 4.3 `blocking_rows` — 6 changes

- **ERCOT** — added the I12 band failure (2027 9.1% → 2030 −1.5%, floor [13.8%, 28.7%]); corrected
  I3 from `0.01–0.03% of load` to the live `0.08 / 0.14 / 0.13 / 0.41%` (**2.7× to 20.5× worse,
  year for year**); added the non-gating FC-2 sustained-VOLL report row (1,137 h/yr ≥ $500 > 800)
  the board omitted entirely; corrected FC-4 (§4.5).
- **CAISO** — **removed** `I4 (2027 gas_st off 1333 MW, A1)` and `I9 (2030 sim chg+dis 0.26%)`,
  neither of which is in the live fail set; added I12 and the FC-2 backstop 65.5% FAIL; expanded
  I7 from "2026/2027" to the live **four** consecutive years (2026-2029, worst gap 9,243 MW).
- **PJM** — `I4 (2029 coal off 743 MW, A1) — sole T1-F blocker` → `I7 (2030: 150,088 < 150,454 MW,
  366 MW) — sole T1-F blocker`. **The "sole blocker" framing survives; its identity changes.**
- **MISO** — dropped I4; dropped the `FC-2 I13 gas_ct cobweb (NEW, flip-induced)` row (I13 PASSES
  live); corrected I7 from 2026-only to 2026 (6,037 MW) **and** 2027 (3,659 MW).
- **NYISO** — `firm 30.3 < 32.1 GW` (a 1,799 MW gap, `-ff2d` vintage) → live `2026: 32,085 <
  32,121 MW (36 MW)` and `2027: 32,339 < 32,390 MW (51 MW)`. **The board overstated NYISO's gap
  by 50×.** It is the smallest adequacy miss in the program, under 0.16% of requirement.
- **NEISO** — numbers already correct (neiso-88); the row's **citation** repaired to
  `ff-verdicts.json` (§3), and its "left for the cross-ISO lane" note updated to record that this
  refresh closed it.

### 4.4 `gate.b_t1f_verdict.detail` — 5 changes

Each rewritten to the live FC-1 fail set (ERCOT/CAISO/PJM/MISO/NYISO). **All five keep
`status: "fail"` and `HOLD`** — the fail *reasons* change, the verdicts do not. NEISO's was
already correct.

### 4.5 `gate.c_crossover_gap.detail` — 2 changes

- **ERCOT** — was `price 69%→9% (converges), CO2 43–50%`. That is `ercot-t1x-ff2d`, in which
  **2025 price PASSED at 8.6%**. On the live record (`ercot-2023-2027-crossover-ffr3a3-t1x`,
  identical to `ercot-t1x`): price **68.7 / 41.2 / 22.5%**, co2 **49.2 / 42.7 / 50.6%**, all six
  FAIL at `K_iso=1.5`, plus gas_twh and coal_twh failures. **ERCOT's crossover price no longer
  converges into band.** FC-4 was FAIL and is FAIL; the leg verdict does not move, but the
  narrative reverses.
- **PJM** — `CO2 43–58%; price 2025 17.5% CAVEAT` (`-ff2d`) → live `co2 45.1 / 40.4 / 54.2%`,
  `price 2025 15.7% CAVEAT`, `coal_twh 2024 23.9% FAIL`.
- **MISO** — already live (FFR-3A-4). Untouched.

### 4.6 `honest_unfit` — 4 rows rewritten

| id | before | after |
|---|---|---|
| `I4 / A1` | "Capacity-accounting leak … dominant T1-F blocker (4/6 ISOs)" | **CLOSED**, with the FFR-1A provenance chain of §2.3 and the repaired/never-leaked split of §2.2. `isos: []`, `isos_formerly: [CAISO, PJM, MISO, NEISO]` |
| `I7 / A2` → `I7 / I12 — A2` | "Base-year adequacy", isos `[CAISO, MISO, NYISO]`, *"NEISO closed via the FF-2C flip"* | **Adequacy accounting — THE dominant T1-F blocker (6/6)**. NEISO is **not** closed (I7 2028 is its sole blocker); PJM added. Root cause unchanged: hydro dispatched but excluded from `accredited_firm_capacity_mw`, which reads the persistent fleet |
| `I3` | ERCOT only, "0.01–0.03% of load" | live 0.08–0.41%; CAISO's single I3 year (2030) added. **A worse reading than the board carried, reported at full magnitude** |
| `I13` | "NEW, FF-2C flip-induced → FC-2 FAIL. Alternating gas_ct entry loop" | **CLOSED** — live reads `no cobweb (I13 PASS)`, FC-2 is CAVEAT. With the D3 note of §6 |

The `golden` row was accurate and is untouched. Row count is unchanged (4 rewritten, 1 kept, 0
added, 0 deleted) — a closed row stays on the board with its history, rather than vanishing.

**One display decision, recorded because it is a judgement call.** `forecast-status.html` renders
`honest_unfit[].isos` as a bare `.join(', ')`, so a semantically-correct `isos: []` on a closed row
renders as an empty `()` that reads like a rendering bug. The two CLOSED rows therefore carry
`isos: ["none - CLOSED"]`, with the machine-readable record preserved in a new `isos_formerly`
field (`[CAISO, PJM, MISO, NEISO]` for I4, `[MISO]` for I13). No renderer was edited. The only
other reference to `honest_unfit` in the codebase is `scripts/forecast_verdict.py`'s
`ATTESTATION_ASSERTIONS` key name `honest_unfit_referenced`, which does not parse this structure.

### 4.7 `open_frontier` rank 5 — 1 change

Read *"FF-2B partially closed (NEISO I7 now PASSES); CAISO/NYISO I7 stay FAIL"*. NEISO's I7 does
**not** pass live, and PJM/MISO fail it too. Corrected to the same fact as the `honest_unfit`
row — **left uncorrected it would have directly contradicted the row two blocks above it.** Rank,
title and lane untouched; only the `detail` line.

### 4.8 `headline`, `gate_reading`, `generated`, `sources` — 4 changes; `d1_board_refresh` added

`gate_reading` rewritten to the live story (§0). `sources` now leads with `ff-verdicts.json` as
**the carrier** and records the §3 path correction inline. `generated` → `2026-08-24`.

`d1_board_refresh` is a new provenance block that **deliberately avoids the
`forecast-provenance/v1` field names** (`scored_at_sha`, `scored_at_date`, `schema`) — same
discipline as the existing `gate_a_provenance` block — so `scripts/check_forecast_staleness.py`
can never read a records refresh as evidence of a re-score. **Verified:** the checker reads
`40 stamped, 8 scored` both before and after this refresh, unchanged.

---

## 5. ESCALATION — one item found, not edited

**CAISO and NYISO gate leg (c) still read `status: "na"` / "not run".**

Neither ISO has a T1-X run: no `caiso-t1x` or `nyiso-t1x` key exists in `ff-verdicts.json`, and
FC-4 reads `n/a` in every one of their verdicts. **That is the identical fact pattern `neiso-88`
used to move NEISO's leg (c) from `na` to `fail`** — charter §2.1b(c) requires the crossover input
gap (FC-4) *measured and reported*, and an unrun leg is not a measured one. NEISO's corrected cell
says so in as many words: *"NEISO has NO T1-X crossover run … only the readiness half is green, so
the leg does not pass."*

Applying that reading to CAISO and NYISO would move **two gate legs from `na` to `fail`** and add
`"c"` to both ISOs' `closed_on`. **That is a gate outcome, which is outside this refresh's
records-only remit, so it is escalated rather than edited** — per the charter's stop-and-escalate
instruction. It is recorded in the board's own `d1_board_refresh.escalated_not_edited` field so it
cannot be lost between sessions.

Both ISOs' overall gates are already `open: false` and closed on other legs, so nothing about the
program's schedulability turns on it. What turns on it is **consistency**: three ISOs with no
T1-X run, two scored `na` and one scored `fail`. Recommend the director resolve it one way for all
three in the next refresh.

**Two further staleness items observed but out of lane, flagged not edited:**

1. **`open_frontier` rank 8** cites *"Storage ε-tiebreak degeneracy at high penetration (I9, CAISO
   → 5.8% of throughput)"*. CAISO's t1f I9 now **passes** (it was 0.26% in the `-ff2d` vintage and
   is absent from the live fail set), but the 5.8% figure is from a different instrument I did not
   verify. **For the CAISO lane**, not for a board refresh.
2. **`tier_ladder`** still labels all three T1 tiers `"scored (FF-2D)"`, though t1f is FFR-3A-2 and
   t1x/t1h are FFR-3A-3/3A-4. Cosmetic; touching it risks implying a re-score. Left alone.

---

## 6. What D3 should now be — the MISO I13 cobweb

**D3 should not treat the I13 closure as a repair, because nobody has claimed one.**

The live `miso-t1f` record reads FC-2 row3 `PASS — "no cobweb (I13 PASS)"`, against the `-ff2d`
baseline's `cobweb (I13 WARN => row FAIL): gas_ct(3)`. So the board's *"NEW, FF-2C flip-induced →
FC-2 FAIL"* row is superseded and MISO's FC-2 is CAVEAT (on the I12 WARN row alone).

But the closure is a **scorer-read, not an attribution**:

- No session in the record claims to have fixed the alternating `gas_ct` entry loop.
- No control arm isolates what closed it. The FF-2C flip that *induced* it is still on.
- It closed somewhere between the FF-2D battery and FFR-3A-2 — a window that contains the whole
  of Wave 1 and Wave 2.

**Recommended D3 posture:** carry I13 as *closed-but-unattributed* and, if MISO's entry-sizing
lane is opened, spend one cheap step establishing **why** before assuming the cobweb cannot
return under a different flip. A blocker that closed for reasons nobody recorded is not the same
as one that was fixed.

**Explicitly NOT touched — the G3 cap-grain `retire.total_gw` t1h regression.** MISO's T1-H
`retire.total_gw` PASS → FAIL flip from FFR-3A-3 (the 3/3 retirement sweep not surviving the G3
cap-grain fix `2adfb49`) **stands untouched**. It is a different finding on a different tier from
the I13 cobweb, and this refresh made no claim about it. The board's `refresh` block, which
records it, is byte-unchanged.

---

## 7. Rule compliance

| rule | compliance |
|---|---|
| **1 `[R-STRUCT]`** | Two corrections make the board look **worse** (ERCOT I3 2.7-20.5× larger; ERCOT T1-X price no longer converging) and are reported at full magnitude. No row was softened. |
| **13 `[R-MEASURED]`** | No measured outcome fed back anywhere; nothing was scored. |
| **15 `[R-DASHBOARD]`** | Forecast namespace only. The backcast registry, keeper shards, `status/*.js` and `calibration-complete.json` were **read** and never written. Nothing registered on either dashboard. |
| **22 `[R-HOLDOUT]`** | No year solved, scored or registered. The holdout spend freeze is ACTIVE and untouched. Gate (a) marker membership re-read, never edited. |
| **27 `[R-PUSH]`** | Opus. `program-status.json` is >300 lines → blob-verified after push (§8). Edited on disk via a scripted round-trip that reproduces the file's exact `json.dumps(indent=1, ensure_ascii=True)` convention byte-for-byte; the pushed bytes are the on-disk bytes. |
| **28 `[R-MECH-MATRIX]`** | No mechanism tested, no cell minted. One matrix-adjacent observation (§5.1, CAISO I9) is flagged for the owning ISO's lane rather than edited into its shard. |

**Verification run before commit** (all committed artifacts, no solve):

- Every `t1f_determination`, `t1x_determination`, `t1h_determination`, `tier_reached`, `flip`,
  `marker_complete`, `marker_final`, `golden`, `candidate` and both `*_provenance` fields:
  **byte-unchanged** across all six ISOs.
- Every gate leg's `status` across all six ISOs: **byte-unchanged**. Gate (a) pass set
  `{NEISO, NYISO, PJM}` = the `complete` block membership; fail set `{CAISO, ERCOT, MISO}`.
- `program`, `readiness`, `tier_ladder`, `flip_config`, `iso_order`, `readiness_limits`,
  `refresh`, `gate_a_provenance`: **byte-unchanged**.
- `json.dumps(…, indent=1, ensure_ascii=True) + "\n"` round-trips the file byte-identically.
- `scripts/register_forecast_run.py --reindex --site-dir <tmp>` consumes the seed and wraps it
  into `program-status.js` cleanly (7 runs, manifest assembled).
- `scripts/check_forecast_staleness.py`: `40 stamped, 8 scored` — identical before and after.

---

## 8. Exit

**36 fields changed. 0 determinations, 0 verdicts, 0 gate outcomes moved. 1 escalation (§5), 2
out-of-lane staleness flags (§5.1, §5.2), 1 D3 posture note (§6).**

Files: `frontend/data/forecast/program-status.json` (corrected board) and this FINDING.
