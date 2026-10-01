# FINDING — caiso-136: the measured unit-availability window family (`unit_outage_short_windows` + `unit_partial_outage_windows`) is **STRUCTURALLY UNDERIVABLE for CAISO** and adjudicated **INERT**. The detector is COAL-ONLY; CAISO's entire coal fleet is **2 units / 50.0 MW** (0.16 % of fleet capacity, 0.04–0.07 % of keeper energy) at **one facility that reports no CAMPD data at all** — the CA extract carries 108–109 facilities with **ZERO coal-fuelled rows** in 2023/24/25. Both derives return **0 windows**, and no guard setting could change that because there is no input series to measure. STOPPED AT THE BRANCH POINT — no A/B, no solve (2026-07-28)

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED.** Nothing armed, no
`ScenarioConfig` field touched, **no LP built and no solver called**. This is the
lane task's own Step-1 branch point taken as specified: *"If the extracts are
empty/negligible for your coal fleet (plausible — CAISO/NYISO/NEISO are
coal-light), STOP: that is a finding, not a failure."*

Matrix citation (rule 28a): mechanism row `unit_outage_short_windows`
(`docs/codebase-site/data/mechanism-matrix.js`, cat `outage`). CAISO's cell was
**U**; it is now **I**. CAISO lever-queue item 5
(`docs/mechanism-testing-matrix.md` §5).

---

## §1 — Step 1, run as specified

```
python scripts/data/derive_campd_unit_outages.py --iso CAISO --short-windows   --years 2023 2024 2025
  → wrote 0 unit-outage windows to data/raw/campd-unit-outages-short-CAISO.csv

python scripts/data/derive_campd_unit_outages.py --iso CAISO --partial-windows --years 2023 2024 2025
  → wrote 0 partial-derate plateau windows to data/raw/campd-partial-outages-CAISO.csv
```

Coverage, as the task requires it be reported before anything is solved:

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| short windows | **0** | **0** | **0** |
| partial-derate windows | **0** | **0** | **0** |
| distinct units | 0 | 0 | 0 |
| MW-days removed | 0 | 0 | 0 |
| class mix | — | — | — |

Both artifacts are committed with their headers and no rows: the negative result
is the record, and it stops a future session re-running the intake.

## §2 — why it is zero, and why it is structural rather than a guard threshold

The detector is **COAL-ONLY** with a when-operable baseload guard (unit
CF ≥ 0.55). Three measurements, in the order that closes the question:

**(a) CAISO's coal fleet is two units.**

| unit_id | plant_code | zone | pmax | fuel |
|---|---|---|---|---|
| `10684_TG8` | 10684 | ZP26 | 25.0 MW | coal |
| `10684_TG9` | 10684 | ZP26 | 25.0 MW | coal |

50.0 MW of a 31,978.6 MW model fleet — **0.16 %** of capacity, at a single
facility (10684, Argus Cogen, Trona CA).

**(b) That facility reports NOTHING to CAMPD.** Facility 10684 is absent from
the CA unit-level extract in **all three years**, and from the facility-level
extract as well. It is not filtered out by a guard — there is no series to
filter:

| year | distinct CA facilities in CAMPD | facilities with a COAL primary fuel | rows with COAL fuel |
|---|---|---|---|
| 2023 | 109 | **0** | **0** |
| 2025 | 108 | **0** | **0** |

The CA extract's fuel mix is 104–105 Pipeline Natural Gas, 2 Natural Gas, 1
Other Gas, 1 Wood. There is no coal in California's CEMS record at all.

**(c) Even a perfectly-measured window could not matter.** From the keeper's own
committed `unit_hourly` sidecar:

| year | CAISO COAL energy | total | share |
|---|---|---|---|
| 2023 | 0.0935 TWh | 140.1 TWh | **0.0668 %** |
| 2024 | 0.0517 TWh | 136.8 TWh | **0.0378 %** |
| 2025 | 0.0830 TWh | 127.4 TWh | **0.0651 %** |

So the mechanism is inert on two independent grounds — no input data, and a
target class three orders of magnitude below materiality.

**No guard was touched** (rule 23 `[R-FROZEN-DERIVE]`). The CF ≥ 0.55 baseload
guard, the plateau constants and the coal-only class scope are unchanged, and
the detector was **not** extended to gas CC — the layup confound the task
names (economic single-train CC operation is indistinguishable from a partial
outage in CF) needs its own charter. Loosening anything here would have been
manufacturing windows, and in this case would not even have worked: the
denominator of every guard is a series that does not exist.

## §3 — the adjudication is CAISO's own, not a port of ERCOT's

Rule 25 `[R-ISO-SCOPE]` is explicit that ERCOT's `I` verdict does not fill
CAISO's cell, and this session did not use it. The two refusals are
**independent and different in kind**:

* **ERCOT-126** — the units and the CEMS series exist; the windows are derivable
  but *unhelpful* (day-scale windows against an intraday cv gate; zero partial
  windows returned).
* **caiso-136** — the windows are **underivable**: the class has no CEMS record
  in this ISO. Re-running ERCOT's reasoning here would have been a category
  error.

The practical difference matters for when the cell may be re-opened: ERCOT's
could move on a better gate, CAISO's can only move if CAISO gains a
CEMS-reporting coal unit.

## §4 — what this does and does not change

* **Keeper unchanged**, determination NOT-YET, fail set **{C3a-2025, C3c}**.
  Steps 2–3 (the A/B, scoring, dashboard registration) are **not reached** by the
  task's own branch point — no run was produced, so **no dashboard registration
  is due** (rule 15 `[R-DASHBOARD]` applies to completed runs).
* **Rule 28 `[R-MECH-MATRIX]` duty b discharged in-session:** the
  `unit_outage_short_windows` CAISO cell moves **U → I** with this finding cited.
  Cells string `IUKKIR` → `IIKKIR`. NEISO's `R` (neiso-69) and NYISO's `I` (nyiso-93) landed concurrently and are preserved untouched — rule 25: four independent per-ISO verdicts, and NYISO's cause differs from CAISO's (NYISO has no coal in the fleet at all; CAISO has 50 MW that is CEMS-invisible).
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only.
* **No DOF ledger entry is due** — nothing was armed, so there is no parameter to
  ledger.
* **No `src/market_sim/` change.** The only artifacts are the two empty extracts.

## §5 — DO-NOT-REDO (new, binding)

* **Re-running the `--short-windows` / `--partial-windows` intake for CAISO.**
  §1–§2: zero windows, because there is no coal in California's CEMS record.
  The committed empty artifacts are the record.
* **Loosening the CF ≥ 0.55 baseload guard, the plateau constants or the
  coal-only class scope to obtain CAISO windows.** Forbidden by rule 23
  `[R-FROZEN-DERIVE]`, and futile here regardless (§2b).
* **Extending the detector to CAISO gas CC in order to give this family
  something to bite on.** The layup confound is real and unresolved; a
  gas-scoped extension is its own charter, not a workaround for an empty coal
  extract.
* **Citing ERCOT-126 as the reason CAISO's cell is `I`.** §3: the two refusals
  are independent and different in kind (rule 25 `[R-ISO-SCOPE]`).

Carried forward unchanged: everything in `FINDING-caiso135` §10 (above all — the
committed-gas lane is CLOSED in every form: `min_load_frac` on any basis, the RA
quantity gate as cap or driver, and "the belly deficit is an under-commitment"),
`FINDING-caiso134` §9, `FINDING-caiso133` §9, `FINDING-caiso132` §10,
`FINDING-caiso131` §10, `FINDING-caiso130` §7, `FINDING-caiso129` §6 and
`FINDING-caiso127` §7.

Next number: caiso-137.
