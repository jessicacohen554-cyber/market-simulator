# RESULT — SPP-45 (2026-09-17): the Ponca extract defect, adjudicated at ZERO LP

**Base:** `d54cd9c571359b85cb1a8e1cd5cab68c080a6b0c`.
**Keeper:** `2026-09-16-spp-42-commitment-feasibility` (`spp42_span_a`) — **UNCHANGED**.
**2019–2022 rung:** `2026-09-16-spp-43-outage-intake` (`spp43_holdout_span`) — **UNCHANGED**.
**LP spent: none. Bundles produced: none. Runs registered: none. Cells armed: none.**
**Shards launched: none** (rule 32 `[R-SHARD]` (a): the parent never solves, and nothing
survived phase 0 that needed solving).

---

## 0. Headline

SPP-43 §7 item 1 — the frozen 2023–2025 block of `data/raw/campd-unit-outages-SPP.csv`
that does not reproduce at HEAD — is **closed at zero LP**. Its phase-0 stop gate
**CLOSES**: the 103 rows the block omits have **ZERO LP reach in every scored year**.

The route to that answer is not the one the lane brief predicted, and the brief's own
supporting measurement was wrong. Both are worth stating, because the gate could have
gone the other way at the last step.

1. **The gate does NOT close on "762 is not in the fleet".** Plant 762 **IS** in the LP
   fleet in **2025** — 4 ST_GAS tranches, 34.000 MW — and **37 of the 103 omitted rows
   start in 2025**. It is also in the fleet in **2019**.
2. **It closes on availability instead, and that is a stronger result.** In 2025 the
   added rows genuinely *reach* the overlay — they create a `(762, 'ST_GAS')` key with
   derate < 1.0 in **7,176 of 8,760 hours** — but they bite an availability array that is
   **identically zero across all 8,760 hours** (the COD/retirement mask). **0.000 MWh
   moves.** The null is not a broken pipe; the pipe demonstrably works and the answer is
   still zero.
3. **All 15 LP inputs hash byte-identical** — `availability`, `min_gen`,
   `min_gen_mechanism`, `pmax`, `pmin`, `heat_rate`, `vom`, `emission_rate`, `nox_rate`,
   `so2_rate`, `zone_idx`, `fuel_type_idx`, `efficiency_bin`, `plant_code`, `unit_ids` —
   in **2023, 2024 AND 2025**. The keeper's scored years cannot move.
4. **The brief's premise was false.** "Plant 762 is ABSENT from the LP fleet in all four
   years 2019–2022, so the 105 rows already in the extract are INERT" is wrong for 2019:
   762 is present there and those rows remove **201,656.459 MWh**. The conclusion drawn
   from it happened to hold; the reasoning did not.
5. **The repair is installed**, because it is provably free. See §4.

**No re-solve, no re-gate, no promotion is owed.**

---

## 1. Two measurement traps, both hit and both corrected

This lane got the wrong answer twice before getting the right one. Both traps are
general, both are cheap to hit, and neither announces itself — so they are recorded here
ahead of the result.

### 1.1 The unit-id convention trap — how "762 is absent" was manufactured

SPP unit ids come in **two** shapes. Most are
`<CLASS>_<zone>_p<plant>_<tranche>` (`ST_GAS_SPP-South_p762_peak`); a minority are
`<plant>_<unit>` (`210_1`). A `unit_id.startswith("762_")` test — the natural one — sees
only the second shape, finds nothing, and reports **absent**.

Measured on the committed `spp43_holdout_span` fleet parquets:

| year | rows | plant codes, `<plant>_` prefix only | plant codes, BOTH conventions | 762 present? |
|---|---|---|---|---|
| 2019 | 1126 | 137 | **315** | **YES** |
| 2020 | 1110 | 141 | 310 | no |
| 2021 | 1109 | 151 | 315 | no |
| 2022 | 1094 | 137 | 313 | no |

The prefix-only parse loses **~57 %** of the fleet's plant codes. That is the whole of
the brief's "absent in all four years".

### 1.2 The `lru_cache` trap — a monkeypatched-path arm/control that cannot differ

`outages.unit_outage_derate_factors` is `@lru_cache`d on its **arguments**
(`year, hours, bins_path, iso, flags`) — **never on the extract's contents**. An
arm/control that swaps the extract by monkeypatching `unit_outage_csv_for_iso` inside
**one process** therefore gets a **cache hit** on the second leg and silently re-reads the
**first leg's** factors.

The failure mode is maximally deceptive: it returns a delta of **exactly 0.000**, which is
indistinguishable from a real null and is exactly what a lane hoping to close a stop gate
wants to see. This lane produced precisely that spurious zero, and caught it only because
the overlay independently reported a `(762, 'ST_GAS')` derate over 7,392 hours that the
"measured" availability delta claimed had changed nothing — a contradiction that has no
innocent reading.

**Every leg below runs in its own process.** Any zero-LP probe that swaps a measured
input by path is exposed to this.

---

## 2. The stop gate, measured

Keeper 12's own recipe (`spp42_span_a`), fleet-only rebuild via
`replay_keeper.run_year_kwargs` + `derived_run_year_inputs`. **No LP is constructed and
none is solved.**

**Proxy validated first.** On 2019–2022 the fleet-only unit-id set is **identical** to the
committed post-LP `dispatch/<year>_P1_fleet.parquet` in all four years (`only_in_fo = 0`,
`only_in_pq = 0`), so it is a faithful stand-in for the scored years the slim keeper
bundle cannot answer directly.

**The omitted rows.** Re-deriving the frozen block at HEAD at the sidecar's frozen
settings (rule 23 `[R-FROZEN-DERIVE]`: `--years` differs, nothing else) reproduces
SPP-43's count exactly — **+103 rows, 0 removals, all plant 762**, units 3 (47) and 4
(56), ST_GAS — split **2023: 32, 2024: 34, 2025: 37**.

| year | 762 in LP fleet | overlay key created | 762 available energy, control → arm | LP inputs identical | fleet available energy (control = arm) |
|---|---|---|---|---|---|
| 2023 | **no** (1086 units) | no | 0.000 → 0.000 MWh | **15/15** | 335,652,747.693079 MWh |
| 2024 | **no** (1105 units) | no | 0.000 → 0.000 MWh | **15/15** | 327,408,849.067823 MWh |
| 2025 | **YES** — 4 tranches, 34.000 MW | **yes**, derate < 1.0 in **7,176/8,760 h** | 0.000 → 0.000 MWh | **15/15** | 339,256,583.891876 MWh |

**2025 is the whole result.** 762 is in the fleet, the rows reach the overlay, and the
derate is large — and it still moves nothing, because the plant's availability is already
**identically zero in all 8,760 hours** (min = max = 0, live hours 0/8760). Ponca is a
retired plant that enters the fleet through `load_retired_within_window` and is then
masked fully offline by the COD/retirement ramp. A derate applied to zero is zero.

**Footprint confinement.** Nothing outside plant 762 moves: fleet-wide available energy
is identical to the sixth decimal in all three years, and `min_gen` /
`min_gen_mechanism` hash identical — so the keeper's armed
`mustrun_commitment_feasibility_clip` does not pick the change up either.

---

## 3. Correction to the record: the 105 committed rows are NOT inert

The brief's inference was *"the 105 rows already in the extract are inert, so the 103
missing ones probably are too."* The premise is false.

Control = the committed extract; arm = the same extract with **every** plant-762 row
removed. Each leg in its own process.

| year | 762 in fleet | available energy WITHOUT rows → WITH rows | rows remove | live hours |
|---|---|---|---|---|
| **2019** | **YES**, 34.000 MW | 242,143.920 → **40,487.461 MWh** | **−201,656.459 MWh (−83.28 %)** | 8760 → **1368** |
| 2020 | no | — | 0.000 MWh | — |
| 2021 | no | — | 0.000 MWh | — |
| 2022 | no | — | 0.000 MWh | — |

The fleet-level delta is **−201,656.459 MWh**, *exactly* equal to the plant-level delta,
so the footprint is confined to plant 762 and nothing else moved.

**This changes no committed number.** Those rows were in the extract when
`spp43_holdout_span` solved, so the rung's 2019 results already include them — that is
correct behaviour, not a defect. What is wrong is only the *characterization*, and it
matters because the zero-reach conclusion for 2023–2025 was being rested on an analogy to
it. That analogy is void; the conclusion here rests on direct measurement instead.

The false claim appears in the **SPP-45 lane brief**, not in
`RESULT-spp-44-coal-deliverability-2026-09-16.md`, which makes no fleet-membership claim.
**No other lane's committed record is altered.**

---

## 4. The repair, installed — and why that is free

`data/raw/campd-unit-outages-SPP.csv` is now a **single 7-year derive** at the frozen
settings, in the deriver's canonical sort.

**Verified pure superset**: all **6,524** previously-committed rows reproduce with **every
field byte-identical** (0 rows differ, 0 removals); the only change is the **+103** Ponca
rows. 6,524 → 6,627 rows.

Why it is worth doing, and why it is safe:

* **It fixes a real provenance defect.** The old sidecar's `derive_invocation` recorded
  one 7-year invocation, but the file was a **concatenation of two blocks at different
  deriver scopes** — re-running the recorded command did **not** reproduce it. It does
  now.
* **It removes an internal inconsistency.** The 2019–2022 block carried Ponca; the
  2023–2025 block did not. One artifact, one scope.
* **Rule 23 `[R-FROZEN-DERIVE]` is satisfied, not bent.** This is a deriver-**scope**
  consistency repair with a **measured zero effect** — no residual moved, and none was
  consulted. The rule forbids re-deriving *against a residual*; that is not what this is.
* **Rule 14 `[R-ACCURATE]`**: the HEAD-scope derivation is the accurate one, and the
  stale block is not preserved to protect a fit.
* **It costs nothing**, and that is measured rather than asserted: §2's 15/15 byte-identity
  in all three scored years.

The sidecar's `composition_note` carries this entire measurement, including the
`lru_cache` trap, so the next lane does not re-derive the finding.

---

## 5. Rules

* **13 `[R-MEASURED]` / 14 `[R-ACCURATE]`** — a measured availability input is made
  complete and self-consistent; nothing is pinned to an outcome, no adder, no haircut.
* **15 `[R-DASHBOARD]`** — no completed calibration run, so nothing to register. The
  dashboard is unchanged and correct.
* **21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero free parameters, zero new tunables, no
  off-registry knob. `offer_curve_by_group` untouched.
* **23 `[R-FROZEN-DERIVE]`** — re-derived at the sidecar's frozen settings, `--years` the
  only difference; the commit cites the scope change. See §4.
* **25 `[R-ISO-SCOPE]`** — SPP's own extract only. The two shared-infra defects the brief
  lists were not patched.
* **28 `[R-MECH-MATRIX]`** — **no cell moves and none is owed**: no mechanism was tested.
  A missing/stale measured input is not a candidate mechanism (rule 29, the SPP-38/42/43
  precedent). No SPP cell asserts anything this lane contradicts (checked).
* **29 `[R-SCREEN]`** — zero-LP phase 0 only; no screen year owed, none named, because
  nothing survived phase 0 as a candidate mechanism. **G-DRIFT is moot** — no control
  differencing was performed, since no LP ran. For the record the working branch changes
  **nothing** on the solve path (`src/market_sim`, `scripts/run_calibration*.py`,
  `scripts/lib`): the only changes are one `data/raw` artifact and one probe.
* **31 `[R-RETAIN]`** — nothing deleted. No bundle produced. See §7.
* **32/33/34 `[R-SHARD*]`** — no shard launched, so nothing to archive and no branch to
  delete. The parent solved nothing.

---

## 6. Reported, not folded in

1. **Parity gate: the same two pre-existing REDs, no new ones** —
   `caiso279_ablate_dswcouple_span` (CAISO) and `soco15_spp_arm`. This lane created no
   bundle and so added none. `soco15_spp_arm`'s `meta.json` reads `iso = SPP`, so it *is*
   in SPP's rule-35(a) scope, but it is cited as live evidence by ten-plus docs across the
   SOCO, NWPP, PJM, MISO and NYISO lanes and rule 31 reserves that call for the owner.
   **Still red; still not pruned.**
2. **The four companion extracts** (`layup`, `layup-shortgas`, `shortgas`, `e923`) remain
   2023–2025 and were **not** extended — unchanged from SPP-43 §7 item 2, and outside this
   lane's object.
3. **`stamp_touchpoint_holdout.py`'s NEISO-specific caveat defaults** — reported, not
   patched (rule 25), unchanged from SPP-43 §7 item 3. **No re-stamp was performed and
   none is owed**, because no run was re-registered and no keeper id changed.
4. **The remaining open objects are untouched** — card R-be's within-day grain on plant
   3008, and SPP-43's two declared costs (2022's 563.6284 MWh of new slack, 2020's
   across-the-board degradation). Neither was this lane's object. See §8.
5. **This container ships no scientific stack.** `numpy pandas pyarrow pydantic pyyaml
   scipy highspy openpyxl` (**`openpyxl` included** — the eGRID boundary-heat-rate repair
   reads `.xlsx` and every fleet build dies without it) must be installed first, ~90 s.

---

## 7. Promotion question (rule 31 `[R-RETAIN]`) — asked, not pre-empted

**There is nothing to promote, and that is the finding rather than an omission.** No LP
was spent, no bundle was produced, no run was registered, no keeper file was touched, no
cell was armed. Nothing is stranded on ephemeral disk: the only artifact this lane
produced is the repaired extract, which is **committed**, and every number cited here is
in this document and reproducible by a committed probe.

**What the owner may want to rule on** is the one judgement call this lane made on its
own — **installing the extract repair** rather than merely recommending it. The case is
in §4: it is a pure superset, it fixes a genuine provenance defect, and all 15 LP inputs
are byte-identical in all three scored years so no scored number can move. **If the owner
would rather the frozen block stayed frozen, reverting is a one-file revert with no
re-solve either way** — the byte-identity runs in both directions.

---

## 8. What is still open for SPP

Unchanged by this lane, and stated so the next one does not re-derive it:

1. **SPP-43's two declared costs**, both on the 2019–2022 rung, both differenceable at
   **zero LP** against the committed `spp43_holdout_span` `hourly/` sidecars: 2022's
   563.6284 MWh of new slack with max system price 85.58 → 1102.55 $/MWh
   (`hourly/system_2022.parquet`), and 2020's across-the-board degradation with its new
   C1 `COAL_PRB` −10.85 TWh row (`hourly/class_hourly_2020.parquet`). **These are now the
   cheapest open objects SPP has** — both are zero-LP, both start from committed bytes.
2. **Card R-be's last residue** — the within-day grain on plant 3008 (Mooreland), the
   fleet's one measured two-shifter. Every cheap lever on it is already adjudicated `R`
   or refused; this needs a genuinely new idea, not a new solve.
3. **The coal↔gas crossover (C1/C3a/C3b/C4 on 2019–2022) stays fully data-blocked.**
   After the 2026-09-16 SPP-44 there is no identified forward-admissible instrument.
   Unblocking it needs a **new dataset** — a rail-performance or delivery-reliability
   series — not a different statistic on EIA-923. It is an owner **data-procurement**
   decision, the same shape as ERCOT's daily-Waha block, and **not** a modelling lane.

---

## 9. Probe committed (zero-LP, re-runnable)

| probe | what it establishes |
|---|---|
| `scripts/probes/_spp45_ponca_reach_phase0.py` | all four legs above: the extract census; the 2019–2022 reach of the committed rows; the 2023–2025 reach of the omitted rows; the 15-field LP-input hash comparison. **Forks one interpreter per leg** (§1.2) and matches **both** unit-id conventions (§1.1). |

Run: `PYTHONPATH=src python3 scripts/probes/_spp45_ponca_reach_phase0.py [scratch-dir]`
(it prints the frozen-settings re-derive command it needs, and refuses to guess it).
