# DECISION CARD nyiso-143 — `nyiso_iroquois_winter_spread` has no verdict-bearing cell in any shard, and the two guards that should catch that both pass

**Session nyiso-143, 2026-08-18.** Filed, not executed: the remedy is a
base-file + all-six-shards edit, which rule 28(c) itself calls "the single
non-parallel edit by design" and which a single-ISO lane must not make. **No
mechanism was tested, no cell verdict moved on this account, no solve spent.**
This card asks for a governance round, not a calibration decision.

---

## 1. THE FACTS, ALL RE-VERIFIED AT HEAD

`nyiso_iroquois_winter_spread` is a solve-affecting `ScenarioConfig` boolean:

| | |
|---|---|
| field | `src/market_sim/config/scenarios.py:4640` (`bool = False`) |
| cache key | `scenarios.py:13264` |
| CLI | `scripts/run_calibration_full.py --nyiso-iroquois-winter-spread` |
| cells in `docs/codebase-site/data/mechanism-matrix/<ISO>.js` | **0 — in all six shards** |
| mentions in `mechanism-matrix.js` | 3, all prose; the load-bearing one is inside the `def:` head of the **sibling** row `gas_hub_basis_overlay` |

Its actual status, from that sibling row's own note: *"stays OFF and stays
OPEN, tested ON CONSTRUCTION ONLY at nyiso-122 … **DELIBERATELY NOT
ADJUDICATED `R`**"*. NYISO's cell **on that row** reads **`K`** — a verdict
about the *overlay*, which is armed on the keeper. One character cannot carry
two booleans whose statuses differ.

## 2. BOTH GUARDS PASS — this is a taxonomy hole, not a registration hole

* `scripts/check_mechanism_matrix.py` → **integrity OK**. By design: the CI leg
  is *mention-anywhere*, and ercot-177 already recorded that it "checks
  registration, not taxonomy", so a field living in a sibling's prose passes it
  yet can never carry a verdict in any ISO.
* `scripts/mechanism_matrix_gap_sweep.py --iso NYISO` → **41/45 family, 0
  absent, 0 prose-only, 0 armed-no-cell, 0 invisible**. Also by design:
  `coverage()` returns `own_row` for any field appearing in a row's `def` head
  (correct for a genuine per-ISO *leg* of a family, e.g.
  `nyiso_gas_commitment_bridge` under `gas_commitment_bridge`) — but this field
  is not a leg of the overlay, it is a distinct mechanism with a distinct
  status.

So the census that exists precisely to find this class of gap **cannot see
it**, and reports NYISO's column as complete.

## 3. WHY IT MATTERS BEYOND BOOKKEEPING

Frontier is the declaration that everything testable has been tested. A named,
admissible, **open** object that is structurally incapable of ever recording a
verdict is the exact thing that declaration cannot survive — and it is invisible
to both instruments a reviewer would reach for. nyiso-143's frontier assessment
lists it as one of three objects still open
(`results/calibration/ASSESSMENT-nyiso143-frontier-redeclaration-2026-08-18.md` §4).

## 4. THE TWO DECISIONS REQUESTED

**D1 — Split the row (the ercot-177 remedy).** Give
`nyiso_iroquois_winter_spread` its **own base row** plus one cell line in every
shard: **NYISO `O`** (open — its construction gates PASS at nyiso-122, it is
refused ex ante *as the C3a-2025 winter lever* on reach, and its standalone
rule 14 `[R-ACCURATE]` case survives untested), and **`.` for the other five**
(the field is NYISO-gated and unreachable elsewhere). Rule 28(d) is respected:
no verdict is minted from another ISO. Precedent: `coal_nameplate_summer_derate`
split out at ercot-177; `cc_capacity_reconcile` / `_path`; `wefor_residual` at
caiso-187.

**D2 — Close the hole that hid it.** Add a `check_mechanism_matrix.py` leg
asserting that every solve-affecting `ScenarioConfig` field resolves to a row
**whose cell it owns**, not merely to a row that *mentions* it — with an
explicit allow-list for genuine per-ISO legs of a shared family. This is the
generalization of the item ercot-177 filed (every non-`U` cell must carry an
`ev` key) and it would have caught both cases. It belongs to a governance
round, not a calibration lane.

## 5. WHAT THIS CARD DOES **NOT** ASK

**The arming decision is untouched and stays the owner's.** Arming
`nyiso_iroquois_winter_spread` would improve a measured input (the committed
construction spreads the measured annual NYISO-SOM Iroquois-Transco spread
**flat across months**, under-reading the constrained winter months of a
Connecticut trading point inside the New England complex — rule 14
`[R-ACCURATE]`) while **degrading C3a-2025** — a rule 22 D-5(b) escalation.
nyiso-122 measured its reach and refused it *as a C3a lever*; that refusal is
not re-litigated here, and this card neither proposes nor implies arming it.
Giving it a cell records the `O` it already is.
