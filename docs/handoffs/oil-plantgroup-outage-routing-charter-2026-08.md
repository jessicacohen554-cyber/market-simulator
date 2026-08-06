# CHARTER — the oil-unit `plant_group` gap and CAMPD outage mis-routing (cross-ISO lane)

**Chartered:** 2026-08-05, session neiso-84 · **Status:** OPEN, Phase 0 complete, unstarted
**Filed by:** neiso-83 §5(c) (`FINDING-neiso83-stonybrook-ca1-2026-08-05.md`), disposition
note (v) of `frontend/data/backcast/keepers/NEISO.json`
**Phase-0 census:** `scripts/probes/_neiso84_oil_plantgroup_census.py` →
`results/calibration/_neiso84_oil_plantgroup_census.json`; narrative
`results/calibration/FINDING-neiso84-frontier-recheck-2026-08-05.md` §4
**Scope:** ISO-agnostic fleet taxonomy + outage overlay. **NOT a NEISO lever** — rule 25
`[R-ISO-SCOPE]` forbids fixing it inside one ISO's lane.
**Model assignment:** Opus or Fable (writes `src/market_sim/`) — rule 27 `[R-PUSH]`.

---

## 1. The defect, stated exactly

`src/market_sim/data/fleet/eia860.py` assigns `plant_group` **only to coal and gas
generators**. Every oil, nuclear and biomass unit therefore carries an **empty**
`plant_group`. Two consequences follow mechanically, and both are live today:

**Leg 1 — the derate denominator drops them.**
`src/market_sim/data/outages.py::_iso_plant_capacity` builds
`{(plant_code, plant_group): MW}` and skips any group-less unit:

```python
if code <= 0 or not g.plant_group:
    continue
```

So an oil unit's capacity is absent from the denominator that
`removed_mw / plant_capacity_mw` divides by.

**Leg 2 — the deriver routes their outages to somebody else's bin.**
`scripts/data/derive_campd_unit_outages.py::_resolve_unit_group` (≈ line 507) short-circuits
on the facility's single recorded group **before** it ever consults the unit's own
`unitType`:

```python
if is_coal:
    return "COAL"
if fac_group in QUALIFYING_PLANT_GROUPS and fac_group != "COAL":
    return str(fac_group)          # <-- the short-circuit
ut = str(unit_type).strip().lower()
if "combined cycle" in ut: ...     # <-- never reached at a single-group plant
if "combustion turbine" in ut: ...
```

`group_by_code` keeps **one** group per plant code. At a plant whose only *modelled* group
is a single gas bin — which is exactly what happens when the plant's other units are oil
and therefore group-less — **every** non-coal CAMPD unit's outage window is routed into
that bin, oil peakers included.

**The two legs compound.** The plant's oil capacity is missing from the denominator *and*
the oil unit's outage MW is charged against the surviving gas bin, so the derate removes
capacity from a machine that never went out.

### The worked case (NEISO 6081 Stony Brook, measured)

CAMPD units 004/005 = EIA-860 generators `1` and `2`, **diesel combustion turbines**, carry
`plant_group = CC_REGULAR` in `campd-unit-outages-NEISO.csv`. In 2024 and 2025 they are the
**only** source of the plant's outage rows while the CC block's own units 001/002/003 have
none:

| year | 001 | 002 | 003 | **004** | **005** |
|---|---|---|---|---|---|
| 2023 | 5 | 7 | 4 | 12 | 8 |
| **2024** | **0** | **0** | **0** | **10** | **12** |
| **2025** | **0** | **0** | **0** | **15** | **13** |

Result: the model derates a **fully-available** CC block to **29.5 % / 19.4 %** availability
in 2024 / 2025.

---

## 2. Phase 0 — the census, DONE. Do not redo it; extend it.

**No LP.** Reproduce with `uv run python scripts/probes/_neiso84_oil_plantgroup_census.py`.

### 2a. The fleet gap is universal

Units carrying no `plant_group`, fleet loaded as the outage deriver itself loads it
(EIA-860 + `load_retired_within_window`):

| ISO | fleet units | oil units | oil MW | nuclear MW | biomass MW | un-grouped MW |
|---|---|---|---|---|---|---|
| ERCOT | 1,463 | 292 | 672.6 | 4,980.0 | 150.1 | 5,802.7 |
| CAISO | 808 | 27 | 142.7 | 2,240.0 | 847.3 | 3,230.0 |
| PJM | 2,103 | 469 | 4,465.6 | 33,491.8 | 1,860.2 | 39,817.6 |
| MISO | 2,029 | 589 | 3,339.0 | 11,519.3 | 1,935.5 | 16,793.8 |
| NYISO | 474 | 59 | 2,926.8 | 3,325.9 | 447.4 | 6,700.1 |
| NEISO | 454 | 140 | 5,345.2 | 3,355.4 | 1,048.8 | 9,749.4 |

**1,576 oil units / 16.9 GW across six ISOs.**

### 2b. Actual exposure is 493 rows at 6 plants — and the naive count over-states it

A raw "oil unit in a gas bin" count returns 885 rows at 10 plants. **That is wrong.** A
dual-fuel oil-fired **steam** unit routed to `ST_GAS` (PJM 3148 Martins Creek, NEISO 546
Montville) is **correctly** modelled in that bin — the model *does* represent those
machines there. The discriminator that isolates the real defect is the deriver's own
`unitType` branches, i.e. exactly the ones the short-circuit skips.

| ISO | extract rows | matched | naive oil-in-gas | **DEFECT rows** | plants |
|---|---|---|---|---|---|
| ERCOT | 53 | 0 | 0 | **0** | 0 |
| CAISO | 4,328 | 4,108 | 0 | **0** | 0 |
| PJM | 10,670 | 10,406 | 312 | **33** | 1 |
| MISO | 10,445 | 10,163 | 217 | **217** | 2 |
| NYISO | 4,423 | 4,386 | 52 | **42** | 1 |
| NEISO | 3,189 | 3,045 | 304 | **201** | 2 |
| **total** | | | 885 | **493** | **6** |

ERCOT is **structurally outside the population**: it keeps its bin-sheet group verbatim
(`ugroup = group if iso == "ERCOT"`). CAISO has no oil exposure.

**All 493 rows share one signature: an oil-fired COMBUSTION TURBINE in a steam or
combined-cycle bin.**

| ISO | plant | bin | defect rows / total | units | CAMPD type | MW |
|---|---|---|---|---|---|---|
| NEISO | 6081 Stony Brook | `CC_REGULAR` | 148 / 207 | 004, 005 | Combustion turbine | 166.0 |
| NEISO | 1595 Kendall Green | `CC_CHP` | 53 / 77 | S6 | Combustion turbine | 21.0 |
| MISO | **2001 New Ulm** | `ST_CHP` | **114 / 114** | 7 | Combustion turbine | 27.5 |
| MISO | 8056 Waterford 1 & 2 | `ST_GAS` | 103 / 143 | 4 | Combustion turbine | 41.0 |
| NYISO | 2516 Northport | `ST_GAS` | 42 / 270 | UGT001 | Combustion turbine | 13.0 |
| PJM | 593 Edge Moor | `ST_GAS` | 33 / 207 | 10 | Combustion turbine | 12.5 |

**MISO 2001 New Ulm is the worst case: every single one of the plant's 114 outage rows
comes from a 27.5 MW oil CT charged against the `ST_CHP` bin.**

### 2c. The mechanism is wider than the oil gap — REPORTED AGAINST INTEREST

The oil gap is one *cause*; the line-509 short-circuit is the shared *mechanism*. Counting
**any** `unitType`/bin contradiction, oil or not:

| ISO | CAISO | MISO | NYISO | NEISO | PJM | ERCOT | **total** |
|---|---|---|---|---|---|---|---|
| rows | 358 | 735 | 341 | 302 | 140 | 0 | **1,876** |

**≈ 3.8× the oil-only count, and it reaches CAISO — which has zero oil exposure.** A fix
scoped only to "give oil a `plant_group`" repairs 493 of 1,876 rows and leaves the same
mechanism live elsewhere. **Scope the lane to both legs or state explicitly why not.**

---

## 3. Phase 1 — what the lane must decide (no code until these are answered)

1. **Does `oil` get a `plant_group`, or does the routing stop short-circuiting?** These are
   different fixes with different blast radii:
   - *(A) Taxonomy:* give oil (and possibly biomass/nuclear) real groups in
     `eia860.py`. Fixes leg 1 **and** leg 2's cause, but changes the fleet every ISO
     builds, every `(plant_code, plant_group)` key, and every derate denominator.
   - *(B) Routing:* reorder `_resolve_unit_group` so `unitType` is consulted **before** the
     `fac_group` short-circuit, and drop a row whose resolved bin is absent from the fleet
     (the function's docstring already says such rows are correctly skipped downstream).
     Fixes leg 2 and all 1,876 rows without touching the fleet. Leaves leg 1's denominator
     gap live.
   - *(C) Both,* sequenced B → A so the routing fix's effect is measurable alone.
   **Recommendation: start at (B).** It is the smaller, more targeted change, it covers the
   wider 1,876-row population, and it is the one whose correctness is checkable from the
   deriver's own declared semantics rather than from a dispatch result.
2. **What happens to a resolved bin the fleet does not model?** An oil CT at a plant with no
   `CT_*` bin has nowhere correct to go. Dropping the row is the honest answer (no outage is
   better than someone else's outage) but it *removes* derate MW — expect availability to
   rise. That is a **move toward** physical truth, so rule 1 `[R-STRUCT]` applies: it stays
   in even if a backcast fit degrades.
3. **Which extracts must be regenerated, and does rule 23 permit it?** Rule 23
   `[R-FROZEN-DERIVE]` freezes derive scripts against *residuals* and requires a
   re-derivation commit to cite its driver. Here the driver is a **code correctness fix**,
   not a data update and not a residual — cite it as such explicitly. All five non-ERCOT
   `campd-unit-outages-<ISO>.csv` extracts (plus the `short-` / `layup-` / `e923-` siblings
   that share `_resolve_unit_group`, and `derive_campd_maxgen_outages.py`, which reuses the
   routing **verbatim**) must be regenerated and **diffed deliberately, per ISO**.
4. **Is any current keeper's determination at risk?** Six ISOs hold keepers. Any change to
   the derate envelope is a structural change to every one of them, so each ISO's re-audit
   is that ISO's own lane (rule 25) and each needs its own A/B against a same-HEAD control.

## 4. Binding constraints on whoever takes this

- **Rule 25 `[R-ISO-SCOPE]`.** The code is ISO-agnostic, so a change here touches all six
  fleets. Prove the untouched ISOs are byte-unchanged the way neiso-83 did — by **running**
  the loader per ISO and comparing fleets and derate maps, not by reading the diff.
- **Rule 1 `[R-STRUCT]`.** This is a correctness fix. It stays in whether or not any
  backcast residual improves; equally, it is not adopted *because* a residual improved.
- **Rule 19 `[R-ONE-MECH]`.** Do not stack a compensating floor or derate on whatever the
  fix exposes. If availability rises and a class over-produces, that is a separate root
  cause.
- **Rule 15 / 16.** Any solve is 2023 + 2024 + 2025 in one bundle and gets registered.
- **Rule 22 `[R-HOLDOUT]`.** The spend freeze is ACTIVE. `--year` strictly {2023, 2024,
  2025}. NEISO's locked test has **NEVER BEEN GRANTED** (*corrected 2026-08-06, owner
  decision D-23 — this read "is SPENT and never re-grantable", which was false; either way
  this charter touches no out-of-training year*).
- **Rule 28 `[R-MECH-MATRIX]`.** A new `ScenarioConfig` gate needs its matrix row in the
  same PR; each ISO's verdict is its own cell and never transfers (28d).

## 5. DO-NOT-REDO

- **The Phase-0 census is done.** Re-run the probe to reproduce; do not re-derive it by hand.
- **`cc_steam_part_reclass` is `K` and closed** (neiso-83). This lane is the *outage
  routing* half that finding filed — not a re-test of the classification fix, and not an
  extension of its ISO registry.
- **`cc_steam_part_capacity` stays `I`** (neiso-80). Not armed, not re-stamped.
- **NEISO 1595 Kendall's capacity basis stays ADJUDICATED-ARTIFACT** (neiso-73). Kendall
  appears in the defect set above on *outage routing*, which is a different question.
  Do not re-open the capacity adjudication.
- **ERCOT is out of population** by construction (bin-sheet path). Do not "extend" the fix
  to it without new evidence.
