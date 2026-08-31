# FINDING — caiso-226: the SoCalGas OFO declaration record is INTAKEN, and it is rule-13 admissible as an INPUT. The caiso-131 A3 ask is discharged for the SoCalGas half (PG&E remains `DATA NEEDED`). One result changes the arm's design before it starts: **the OFO event record does NOT inherit the citygate threshold's automatic 2025 inertness** — 25 low OFOs were declared in 2025, 9 of them in January — so a naive "OFO day" trigger fires in the one year whose C3c already PASSES and whose C3a is the sole open gate. Intake-only: no mechanism, no `ScenarioConfig` field, no matrix row, no solve.

**Session:** caiso-226 · **Date:** 2026-08-31 · **Keeper at session:**
`2026-08-26-caiso-220-c1-crosswalk` (NOT-YET on C3a alone; C3c the single
ledgered caveat) · **Charter:** funded caiso-131 A3 data intake, C3c-side,
strictly orthogonal to C3a · **Solves run:** none.

---

## §1 — what landed

| artifact | path |
|---|---|
| schema (the contract) | `data/dictionary/schema/gas-ofo-events.schema.yaml` |
| raw snapshots (immutable) | `data/raw/gas-ofo-events/caiso/` + `README.md` |
| fetch | `scripts/data/fetch_socalgas_ofo_events.py` |
| registry package | `scripts/lib/gas_ofo_events/` (`__init__.py`, `caiso.py`) |
| curation | `scripts/data/curate_gas_ofo_events.py` |
| clean partition | `data/clean/gas-ofo-events/CAISO/gas-ofo-events.parquet` |
| tests | `tests/curation/test_curate_gas_ofo_events.py` (10, tmp-CLEAN_DIR) |

**2,590 rows**, one per `(iso, utility, gas_day, side)`: **678 low** OFO/EFO
days (2015-12-06 → 2026-03-23) and **1,912 high** OFO days (1997-05-24 →
2026-08-31), all SoCalGas. The intake is unrestricted across years under rule
22 `[R-HOLDOUT]` — data is never held out, only *scores* are — so the full
published span is committed, not a 2023–2025 slice. Nothing here is read by a
solve.

The datatype is ISO-agnostic by construction: `side`/`stage`/`tolerance_pct`/
`waived` are the publisher's own fields, the registry keys on ISO with each
utility declaring its own `OfoSource` + reader, and no shared code branches on
an ISO name. PG&E (NP15) and the NEISO/NYISO/PJM interstate-pipeline analogues
are each one module or one `OfoSource` away, with no shared-file edit.

## §2 — verification: the curated frame reproduces the caiso-225 source record exactly

The caiso-225 §A3 archaeology embedded the 2023–2025 low-OFO event lists and
the per-year counts in `results/calibration/_caiso225_watch_results.json`. The
curated parquet was checked against them, not merely fetched:

- **Per-year counts, low side, 2015–2026** — exact match, all 12 years
  (2023/2024/2025 = 43/34/25).
- **Per-year counts, high side, 2022–2026** — exact match, all 5 years
  (2023/2024/2025 = 196/102/189).
- **Event strings, 2023–2025 low side** — all 102 rows re-render
  **byte-identically** to the caiso-225 strings from the parquet's parsed
  fields (`"January 3, Stage 3.1, -5%"`, `"…-5% (WAIVED)"`). This is a full
  round-trip proof: nothing was lost or invented between the HTML and the
  clean columns.
- The **Jan-2023 blowout cluster** the charter named (Jan 3/4/5/12/13/19) is
  present, and is in fact a **15-day** January-2023 low-OFO month
  (3,4,5,12,13,19,22,23,24,25,26,28,29,30,31).

The parser refuses to be lossy: any non-blank ledger cell that does not match
the published grammar **raises** rather than being skipped, so a future ENVOY
format change fails loudly instead of silently shrinking the record. Every
row carries the `source_doc` it came from, and the clean file's parquet footer
carries each snapshot's URL, retrieval timestamp, byte count and SHA-256.

## §3 — three source facts the 2023–2025 scan could not have shown

Intaking the **full** published span (rather than the charter's working span)
surfaced three things that bear directly on any future mechanism:

1. **The stage vocabulary is wider than the 2023–2025 record.** The charter
   named stages 1/2/3/3.1/3.2/3.3/EFO. The full ledger also carries **Stage 4**
   (16 low days: Feb-2018, Jul-2018, Feb-2019, Feb-2021, Dec-2022; 1 high day,
   Dec-2022) and **Stage 5** (1 low day, 2022-12-13). A stage allow-list built
   from 2023–2025 alone would have rejected the December-2022 cold snap — the
   event immediately preceding the January-2023 cluster.
2. **The high ledger has a pre-2018 unstaged vintage.** 950 of 1,912 high rows
   (1997–2018) carry **no stage at all** — SoCalGas began printing a stage on
   high OFOs only in mid-2018. `stage` is nullable for exactly this reason, and
   a consumer that treats null as "no event" would be wrong.
3. **`stage` and `tolerance_pct` are NOT monotone in each other.** Measured on
   the low ledger, the *widest* tolerance bands sit at **Stage 1** (mean −6.04,
   min −18) while **Stage 3.2** is uniformly −5. They are two independently-set
   dials, not a single severity scale. (An earlier draft of this schema
   asserted the opposite; it was corrected against the data before commit.)

## §4 — the rule-13 `[R-MEASURED]` adjudication, in writing

**Verdict: ADMISSIBLE as a reproducible physical/market INPUT.** The full
argument, against rule 13's own admissibility test:

> *"Could this same quantity be produced for a forward year from forward
> drivers, and would it respond to changed conditions?"*

**(a) It is an event, not an outcome.** An OFO is a declaration by a *gas*
utility about *its own* pipeline and storage system's ability to absorb a daily
imbalance. It is generated outside the electricity market entirely. It is not
a price, not a dispatch, not a quantity the LP is asked to reproduce, and it
carries no information about what CAISO's λ did on that day. This is the
decisive line: rule 13 forbids feeding a measured *outcome* back to force a
match, and an OFO declaration is categorically not one.

**(b) It is the same class as an input the model already uses.** The CAMPD
unit-outage windows are measured physical availability events, applied in
backcast mode, admitted under rule 13. An OFO is the *fuel-side* member of
exactly that class: a physical availability event on the delivery system rather
than on the unit. caiso-131 §5 already characterised it this way; the record
now exists to act on.

**(c) It responds to changed conditions.** OFO frequency tracks the physical
state of the SoCalGas system, and the record shows it moving with that state
rather than with anything about the power market: **109 low OFOs in 2019**
(Aliso Canyon storage still deeply restricted) decaying to **59/60/38** in
2020–2022 and **43/34/25** in 2023–2025 as storage was restored. A driver keyed
to this record inherits that responsiveness; a fitted constant does not.

**(d) The forward analogue — stated, and deliberately left open.** A forecast
year holds no published OFO ledger, so a forward mechanism cannot read this
table directly. It needs a **regeneration story**, and this session does not
choose one: that is the arm's job, on the arm's evidence. The two shapes
available, named so the arm starts from them rather than inventing a third:
- an **OFO-day climatology** — a per-(month, temperature-bin) declaration
  hazard estimated from the ledger and driven forward by the forecast year's
  own weather/load drivers; or
- a **gas-scarcity driver** — an OFO probability conditioned on forward gas
  system state (storage inventory, citygate/border spread, sendout vs.
  capacity), which is what actually causes a declaration.

Either regenerates for a forward year from forward drivers and responds to
changed conditions, which is what rule 13 requires. **Neither is built, chosen,
or endorsed here**, and the backcast-side overlay must not be armed on the
assumption that a forward analogue will be found — that ordering is
pre-registered in §5 as gate D3.

**(e) What this record may NEVER become.** Binding, and carried into the
PRECOMMIT:
- **No threshold tuned to a residual.** caiso-131 §10 already forbids deriving
  a citygate threshold that makes C3c-2024 clear. The identical prohibition
  binds here with more force, because the OFO record offers *more* dials to
  tune (side, stage, tolerance, waived, run-length). Choosing among them by
  which makes a gate clear is rule 24 `[R-DOF]` failure, not identification.
- **No adder, haircut or offset** keyed to the price or volume residual
  (rule 13), and **no fitted per-hour magnitude**. An OFO day is a binary
  physical fact about gas delivery; whatever it gates must be identified from
  gas-system physics or published tariff mechanics, never from the tail-hour
  count it needs to reach.
- **No selection of the trigger definition by its coverage of the measured
  tail.** See §5 D0 — the definition is fixed *before* its coverage is
  measured, and this session deliberately did **not** measure that coverage.

**(f) Rule 1 `[R-STRUCT]` note.** Gas deliverability is real market structure
CAISO's LP does not represent; caiso-131 §6 established that the model's gas
*passthrough* works correctly on the 2023/2024 tail days and still leaves a
$150–200/MWh gap because 22.6/27.5 GW of headroom remains. If an OFO-driven
mechanism is structurally faithful, it stays in **even if the residual does not
move** — and equally, it may not be kept because the residual moved if the
mechanism is not real.

## §5 — the pre-registration, and the one design fact that changes it

Full falsifiable design: **`results/calibration/PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`**.

The finding that must reach the arm before it picks a trigger, derivable from
the **source record alone** (no model output, no solve):

> **The OFO event record does not inherit the citygate threshold's automatic
> 2025 inertness.**

caiso-131 §6 valued a gas trigger partly because a citygate threshold is
*inert in 2025 by construction* — 2025's citygate never exceeds $5.61/MMBtu
against 2023's $24.29 — which matters because C3c-2025 already PASSES and
C3a-2025 is CAISO's only open gate, so a mechanism that lifts 2025 makes the
live failure worse. **The OFO record has no such property.** SoCalGas declared
**25 low OFOs in 2025** (9 in January, 5 in February, 6 in March), against 43
in 2023 and 34 in 2024. A trigger reading "any low-OFO gas day" fires on ~25
days of 2025.

This does not sink the ask — it *specifies* it. It means the arm's trigger must
be discriminating on grounds **internal to the gas record** (which is what §3.3
warns is not as simple as ranking by stage), and that its 2025 no-harm
behaviour is a **pass/fail criterion to be pre-registered and tested**, not a
property inherited for free. That criterion is written into the PRECOMMIT as
**G2**, and the honest possibility that no non-fitted definition satisfies it
is written in as an explicit **kill** outcome.

## §6 — DO-NOT-REDO (new, binding)

- **Re-running the source archaeology.** caiso-225 §5/§9.2 answered
  availability; this session answered retrieval. Both endpoints, their spans,
  the cell grammar, and the two unused routes (per-gas-day cycle detail;
  Critical Notices) are recorded in `data/raw/gas-ofo-events/README.md`.
- **Re-deriving the parse.** The 2023–2025 low record round-trips
  byte-identically (§2) and the per-year counts match both sides. A future
  session that doubts the frame should re-run the committed test, not re-parse
  the HTML.
- **Re-measuring the OFO-day counts, stage mix or tolerance/stage
  relationship.** §3 and the committed parquet carry them; they need no fetch.
- **Deriving ANY trigger threshold by its coverage of the measured tail
  hours** — the caiso-131 §10 prohibition, restated in §4(e) and pre-registered
  as PRECOMMIT gate D0. This session did not compute that coverage *precisely
  so that* the arm's trigger definition is fixed on physical grounds before its
  yield is known.
- **Assuming an OFO trigger is inert in 2025** (§5). It is not, and any design
  that relies on inherited inertness is already refuted.
- **Treating this intake as C3a-side.** It is C3c-side root-cause work. C3c
  remains the keeper's single ledgered caveat regardless of what the arm finds;
  rubric v3.3 does not downgrade a determination for it. Nothing here is a gate
  need.

Carried forward unchanged: the whole caiso-131 §10 DO-NOT-REDO, the caiso-222
Q1 terminal rest, and every `R`/`I`/`G` cell in
`docs/codebase-site/data/mechanism-matrix/CAISO.js`. The mechanism matrix is
**untouched** by this session — correctly, since no mechanism was tested
(rule 26 `[R-MECH-MATRIX]` duty (b) attaches to the arm session, which adds the
row with its `ScenarioConfig` field).

Next number: caiso-227.
