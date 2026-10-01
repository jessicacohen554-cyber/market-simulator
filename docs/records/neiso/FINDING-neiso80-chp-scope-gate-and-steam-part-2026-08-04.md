# FINDING — neiso-80: the CHP dark-fuel scope gate lands at NEISO; Stony Brook's steam part was never missing

**Session:** neiso-80 · **ISO:** NEISO · **Date:** 2026-08-04
**Prereg:** `results/calibration/PREREG-neiso80-chp-scope-gate-and-steam-part-2026-08-04.md`
(pushed as commit `e89d08b5`, **before** any arm and before any adjudicating statistic)
**Probe:** `scripts/probes/_neiso80_stonybrook_presence.py`
**Record:** `results/calibration/_neiso80_stonybrook_presence.json`
**Keeper:** `2026-08-03-neiso-caiso156-meter-screen` — **UNCHANGED.**

## §0 — the verdict in one table

| item | question | verdict | cell |
|---|---|---|---|
| 1 | miso-122 hybrid-cogen dark-fuel scope gate, unapplied at NEISO | **APPLIED.** Artifact re-derived; every property holds; **score-inert on the designated keeper by construction** | `measured_chp_heat_rates` NEISO **stays `O`** |
| 2 | NEISO 6081 Stony Brook `CA1`, 96.0 MW — is the steam part missing? | **NO. `REPRESENTED`** — it is already in the LP at 96.0 MW. The mechanism is **provably byte-identical** at NEISO | `cc_steam_part_capacity` NEISO **`U` → `I`** |

**NO LP RUN WAS PRODUCED THIS SESSION — no solve, no bundle, no dashboard
registration** (rule 15 `[R-DASHBOARD]`, stated explicitly rather than left
implied). Both items were adjudicated from committed EIA-860 / eGRID / CAMPD
artifacts and one fleet-loader diff. Item 1 needed no arm because its inertness
is a property of the keeper's own recorded config; item 2 needed none because
its pre-registered falsifier fired.

---

## §1 — Item 1: the gate lands, and it reproduces to 4 dp

`scripts/data/derive_chp_power_only_heat_rates.py` has carried scope gate 3
(miso-122, 2026-08-03) since it was written, and its own module docstring names
the NEISO number. What was missing was the **artifact**: miso-122 re-derived only
MISO's and nyiso-120 only NYISO's, each handing NEISO's off with a number
(rule 25 `[R-ISO-SCOPE]`). NEISO's, PJM's and CAISO's were last written at
PR #3410, before the gate existed — 19 columns, no `dark_fuel_share`.

Re-derived at `--vintage 2023`, every pre-registered property holds:

| property | test | result |
|---|---|---|
| **P1 CONSUMPTION** | sole consumer of the artifact | `campd_bins.measured_chp_heat_rates` → `chp.apply_measured_chp_heat_rates` → `eia860.py:1686`, gated on the flag. **One caller, one gate.** |
| **P2 STRICT NO-OP** | 6 frozen columns bit-identical on all 40 rows | **holds** — only `(1595, CC_CHP)`'s `heat_rate` moves, and only downward. Flag census unchanged: `not_unfired_topping` 22 / `ok` 12 / `no_egrid_row` 5 / `basis_mismatch` 1 |
| **P3 MAGNITUDE REPRODUCES** | `dark_fuel_share ≈ 0.0121`, `heat_rate` 9.5584 → 9.4423 | **holds to 4 dp** |
| **P4 RECONCILIATION** | `cems_vs_egrid_total` in (0.9, 1.1) | **holds** — 1.0; flag stays `ok`, so the share is applied rather than the row excluded |
| **P5 NO CROSS-ISO WRITE** | files changed on disk | **holds** — exactly one, NEISO's |

The only other movement is `model_over_measured` 0.6003 → 0.6076, which is a
derived echo of the same ratio (5.7376 / 9.4423) and is not a frozen column.

**The gate is a stable physical feature of the plant, not a one-year artifact.**
Measured on NEISO's own CAMPD at unit grain, all three training years:

| year | plant heat input | dark (fuel, zero gross load, all year) | `dark_share` | corrected rate |
|---|---|---|---|---|
| 2023 | 14,563,531.2 MMBtu | 176,823.5 | **0.012142** | **9.4423** |
| 2024 | 14,898,069.5 | 142,780.7 | **0.009584** | 9.4668 |
| 2025 | 14,764,651.8 | 218,491.1 | **0.014798** | 9.4170 |

which reproduces the hand-off series 1.21 / 0.96 / 1.48 % exactly. The committed
artifact is the 2023 vintage, so **9.4423** is the number of record; the other
two are stability evidence and are not applied (gate 3 measures at the same year
as `--vintage`, no vintage mixing).

CEMS validation is unchanged: `(PLHTIAN + CHPCHTI)` reproduces metered heat
input within 1 % on 4/4 covered NEISO plants, median ratio 1.00000.

### §1.1 — the ceiling, measured rather than asserted

The prereg declared ex ante that this gate **cannot flip the `O` cell**, on the
ground that it moves one plant's rate by 1.21 % against the +27.96 % seam move
that produced the neiso-70 overshoot. That claim is now measured on the artifact
itself:

| | cap-wt model (incumbent) | cap-wt measured PRE-gate | POST-gate | seam dearness |
|---|---|---|---|---|
| repriced population (12 rows, 429.7 MW) | 7.1718 | 9.7598 | 9.7041 | +36.08 % → **+35.31 %** |
| `CC_CHP` only (3 rows, 378.2 MW of a 494 MW class) | 6.9636 | 9.5208 | 9.4576 | +36.72 % → **+35.81 %** |

**The gate walks the seam back by 2.15 % of the move that overshoots** — about
one part in forty-six. `measured_chp_heat_rates` NEISO is `O` because neiso-70
measured the mechanism **live but structurally incomplete**: `CC_CHP` crosses
from over- to under-generating in every year (2023 |error| 0.224 → 0.369 TWh)
because NEISO's merchant `CC_CHP` carries no host-steam obligation floor. A
2.15 % walk-back does not touch that, and this session does not claim it does.

**The artifact ships anyway, and the reason is the rule, not the fit.** Rule 23
`[R-FROZEN-DERIVE]` permits exactly two re-derivation grounds — a new eGRID
vintage, or a **scope gate's logic changing on measured grounds** — and this is
the second. Rule 14 `[R-ACCURATE]` governs in both directions: the corrected
input goes in because it is the corrected input. **No residual was consulted,
and none could have been:** the designated keeper records
`measured_chp_heat_rates = false`, so the artifact is not read on the keeper's
solve path at all.

**That is the honest statement of item 1's reach: it is score-inert on the
designated NEISO keeper by construction, not by measurement.** No solve can show
otherwise and none is owed. Its value is that NEISO's artifact now carries the
same three scope gates as MISO's and NYISO's, so whenever the `O` cell is
re-opened it will be re-opened against a correct input.

**Hand-off, unchanged in kind (rule 25).** PJM's and CAISO's artifacts remain
un-gated at 19 columns. miso-122 measured both as carrying **no dark fuel above
0.1 %**, so their re-derive is expected to move no rate — but that is *their*
lanes' measurement to make, and **no PJM or CAISO cell is stamped here**.

---

## §2 — Item 2: the steam part was never missing, and the totals test could not have said so

miso-126 §8-2 handed this off as presence `UNDETERMINED` *even on its own
basis-consistent test* — fleet 435.7 MW against EIA-860 446.6 including `CA` /
350.6 excluding it — and required this lane to resolve presence first.

**Q1 and Q2 reproduce the hand-off exactly and still cannot decide it.** Both
capacity bases agree (Stony Brook has **zero** NaN-summer rows, so
summer-only and summer-else-nameplate are the same number here) and both return
`UNDETERMINED`: 435.7 matches neither 350.6 nor 446.6.

**Q3 passes.** `(6081, 'CA1')` is in the national predicate population — one of
exactly four rows, with `(1004, 'ST')`, `(54912, 'STG1')` and `(55088, 'ST1')`.
`CA1` is prime mover `CA`, `Energy Source 1` `DFO` ≠ `NG`, Unit Code `CC1`,
three `NG`/`CT` siblings on the same Unit Code, and commissioned 1981 — the same
year as all three. Vintage-coherent, exactly as miso-126 recorded.

**Q4's falsifier fires, and it is decisive.**

```
_map_fuel_type("Petroleum Liquids", "DFO", "CA")  ->  'oil'      (not None)
```

The fuel map **does not drop the row**. `6081_CA1` is in NEISO's loaded fleet at
**96.0 MW**. The capacity the item exists to restore is already in the LP, and
adding it would be a double count.

This is miso-126's 1004 Edwardsport pattern recurring at NEISO: the predicate
matches, but the repair *only ever restores a row the fuel map drops* and this
row resolves. The difference is that Edwardsport resolved through its technology
string carrying "coal"; `CA1` resolves through `Petroleum Liquids` / `DFO`.

### §2.1 — why the TOTALS test degenerated, resolved at row grain

| EIA-860 row | pm | ES1 | eff MW | in the fleet? |
|---|---|---|---|---|
| `1` | GT | DFO | 65.0 | `6081_1` |
| `2` | GT | DFO | 65.0 | `6081_2` |
| **`5051S`** | **PV** | **SUN** | **6.9** | **no** |
| **`BS#1`** | **IC** | **DFO** | **2.0** | **no** |
| **`BS#2`** | **IC** | **DFO** | **2.0** | **no** |
| `CA1` | CA | DFO | 96.0 | **`6081_CA1`** |
| `CT1` / `CT2` / `CT3` | CT | NG | 69.7 each | `6081_CT1/2/3` (`CC_REGULAR`, `gas_cc`) |
| `EDSI` | IC | DFO | 0.6 | `6081_EDSI` |

```
446.6  -  10.9  =  435.7  ==  fleet total 435.7      (exact)
        (6.9 PV + 2.0 + 2.0 blackstart IC)
```

**The reconciliation is exact.** Stony Brook carries 10.9 MW of rows a thermal
fleet loader legitimately never loads — a 6.9 MW solar array and two 2 MW
blackstart reciprocating sets — so the plant total is 10.9 MW above the fleet's
in *both* the `MISSING` and `REPRESENTED` directions and the totals test can
only return `UNDETERMINED`.

**This is a real limit of the miso-125/126 presence test, and it is recorded as
one rather than worked around.** The totals test is correct where it decides —
it is what caught Edwardsport as a 555 MW false positive, and it is right that
presence is never decided against block *siblings*. But at a plant carrying
legitimately-excluded rows it is **under-determined by construction**, and the
question has to move to row grain: *is this specific generator id in the loaded
fleet?* The two tests are complements, not substitutes.

### §2.2 — inertness proven at the loader grain, not inferred

miso-126 §4's discipline is that a fleet-loader firing check is not sufficient
proof of *firing*. The mirror of that is that reading a predicate is not
sufficient proof of *inertness*. So it was run:

```
CC_STEAM_PART_REPAIR_ISOS patched to {MISO, NEISO}, cc_steam_part_capacity=True
  NEISO fleet size   off 431   armed 431
  added   (none)
  removed (none)
  changed (none)
  BYTE-IDENTICAL: True
```

**`cc_steam_part_capacity` is provably inert at NEISO** — not merely gated off
by `CC_STEAM_PART_REPAIR_ISOS`, but a strict no-op *even with NEISO enrolled*,
because the row it would restore is one the fuel map never drops. The cell is
stamped **`I`**, and NEISO is **not** added to `CC_STEAM_PART_REPAIR_ISOS`.

Q5 (re-running miso-126's five properties on NEISO's own data) and Q6 (`DFO` as
duct fuel vs primary input) are **not reached**: both are downstream of a
`MISSING` verdict that did not occur. Q6's evidence was gathered anyway and
feeds the successor below.

---

## §3 — a named successor, gathered but deliberately NOT adjudicated

`6081_CA1` sits in the LP as a **96.0 MW `oil` generator with an empty
`plant_group`**, while its three `CT` siblings on the same Unit Code `CC1` are
`CC_REGULAR` / `gas_cc`. The block's steam part is priced on distillate.

Q6's evidence bears on whether that is right, and it points one way:

* The `CT` siblings are `NG` primary with `DFO` as **Energy Source 2** — dual-fuel
  gas turbines, oil-backup.
* CAMPD meters five units at 6081. Units **001/002/003** report
  `Pipeline Natural Gas`, `unitType` **Combined cycle** — the `CT1`–`CT3` block.
  Units **004/005** report `Diesel Oil`, `unitType` Combustion turbine — the two
  65 MW simple-cycle `GT` rows.
* **`CA1` has no CAMPD unit of its own.** The block's fuel is metered as pipeline
  natural gas at the `CT` rows — which is miso-126's "ONE METER, ONE RATE"
  picture, and is what its whole premise predicts for a `CA` row whose energy
  input arrives as its siblings' exhaust.

That is a **classification / repricing** question, not a capacity-presence one,
and it belongs to a different matrix family than the lever this session tested.
It is written up as an **OPEN successor needing its own charter with its own
measured identification**, and **no cell is stamped for it**. Sizing note for
whoever opens it, stated so the item is not oversold: the whole plant meters
73–91 GWh/yr of gross generation across all five CAMPD units, so this is a
small-capacity-factor plant and the lever is a correctness question before it is
a magnitude one.

**CAISO 54912 Martinez `STG1` (20.0 MW `OG`) remains CAISO's** and is untouched
here (rule 25). miso-126 measured it `MISSING` against CAISO's fleet; nothing in
this session bears on it, and **no CAISO cell is stamped**.

---

## §4 — the six DO-NOT-MISREAD guards, as applied

1. **miso-119** (max |Δ| is an upper bound). No magnitude here is derived from a
   max; §1.1's ceiling is a capacity-weighted mean over the repriced population.
2. **miso-121** (binding ≠ marginality). Nothing was sized from a binding count.
3. **miso-122** (`max_abs_class_hour_mw` is not a magnitude). No class-hour
   statistic was quoted; no dispatch statistic was needed at all.
4. **miso-124** (price response is not stable across keepers). No delta is
   quoted against any keeper — **no solve was run**, and the keeper's role here
   is solely as the source of the fleet-loader settings (§5) and of the recorded
   `measured_chp_heat_rates=false` that makes item 1 inert.
5. **miso-125** (a wrong-sign magnitude is a denominator defect; presence is
   tested against the plant's EIA-860 TOTALS). Applied, **and its limit found**:
   §2.1 records that the totals test is under-determined at a plant with
   legitimately-excluded rows, and resolves at row grain instead. This is an
   extension of the guard, not a departure from it — presence was still never
   decided against block siblings.
6. **miso-126** (a loader firing check is not sufficient proof / a conservation
   violation is a boundary defect). Applied in the mirror direction: §2.2 proves
   inertness by **running** the armed loader and diffing, rather than by reading
   the predicate and asserting it.

---

## §5 — the miso-116 measurement trap, honoured

`load_fleet_from_csv` defaults `measured_chp_heat_rates=False` while keepers arm
it, so the probe builds its model side from the NEISO keeper's own
`run_config.json`:

```
keeper fleet-loader settings: {'measured_ct_heat_rates': True,
                               'measured_chp_heat_rates': False}
```

For NEISO the trap runs the *other* way — the keeper does **not** arm CHP — and
that fact is itself item 1's answer (§1.1), which is why it is read from the
keeper rather than assumed in either direction.

---

## §6 — what shipped

* `data/raw/_processed-legacy/chp_power_only_heat_rates_NEISO.csv` — re-derived
  under scope gate 3. 19 → 22 columns (`cems_dark_heat_mmbtu`,
  `dark_fuel_share`, `heat_rate_all_fuel`); one rate moves,
  `(1595, CC_CHP)` 9.5584 → 9.4423. Rule 23 citation: **the miso-122 gate-3
  scope change**, on measured grounds. No residual.
* `scripts/probes/_neiso80_stonybrook_presence.py` + record
  `_neiso80_stonybrook_presence.json` — the Q1–Q6 screen, the row-grain
  reconciliation and the loader-grain inertness proof. No LP.
* Matrix: `cc_steam_part_capacity` NEISO **`U` → `I`**;
  `measured_chp_heat_rates` NEISO **stays `O`** with its note extended (an input
  correction with no mechanism surface does not move a cell verdict — the
  caiso-156/159 precedent).
* `scripts/data/derive_chp_power_only_heat_rates.py` — **unchanged**. The gate
  was already there; only the artifact was stale.

## §7 — for the next session

1. **Do not re-test `cc_steam_part_capacity` at NEISO.** It is `I` and the proof
   is a byte-identical armed fleet, not an argument.
2. **`measured_chp_heat_rates` NEISO stays `O` and its blocker is unchanged** —
   the neiso-70 `CC_CHP` overshoot, which is a missing host-steam obligation,
   which neiso-71 closed as *"NEISO's merchant `CC_CHP` genuinely carries no
   host-steam obligation"*. That DO-NOT-REDO stands. The gate-3 correction moves
   2.15 % of it and was never offered as a route.
3. **The live successor is the `6081_CA1` classification question** (§3) — a
   `CA` steam part priced as 96 MW of distillate while its block is metered on
   pipeline gas. Needs its own charter. Not stamped.
4. **PJM's and CAISO's CHP artifacts are still un-gated** (19 columns). miso-122
   measured both at < 0.1 % dark fuel, so the expected rate movement is zero —
   but each is its own lane's call.
5. **The presence-test limit in §2.1 is worth carrying**: the EIA-860 totals test
   returns `UNDETERMINED` by construction at any plant holding rows the thermal
   fleet legitimately excludes (solar, sub-MW blackstart sets). Row grain
   decides those; totals decide the rest.
