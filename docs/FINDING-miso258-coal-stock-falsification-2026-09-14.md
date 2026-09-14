# FINDING — miso-258: the 2022 coal data block was never real, and the model's
# 2022 coal dispatch is falsified by measured inventory alone

```
SESSION : miso-258          ISO: MISO          KEEPER: 2026-09-12-miso-255-sil-measured
ASK     : (1) MISO's ISO headline (governance).  (2) is the 2022 coal intake unblocked?
RESULT  : (1) AUTHORIZED and EXECUTED. MISO's card reads CALIBRATED on its train tier.
          (2) THE INTAKE IS UNBLOCKED — stated as a fact, not a plan. Plant-level monthly
              coal stocks ship in EIA-923's FREE, KEYLESS bulk workbook. Landed as the
              `coal-stocks` clean datatype. The model's 2022 MISO coal dispatch would end
              the year at MINUS 9.69 Mt of inventory — physically impossible.
LP SPENT: ZERO. The parent solved nothing and NO SHARD WAS LAUNCHED (rule 32 [R-SHARD] (a)).
SCOPE   : Intake only, on the owner's ruling. NO mechanism was built: no ScenarioConfig
          field, no LP constraint, no matrix cell moved, no solve.
```

---

## 1. RESULT

> **`FINDING-miso256` §5 recorded MISO-footprint coal stocks as "not on disk", named an
> `EIA_API_KEY` as the unblocker, and reported the EIA API as blocked. The API route *is*
> key-gated — `api.eia.gov/v2/coal/...` returns HTTP 403 without a key, re-confirmed this
> session. But the same quantity ships in EIA-923's free annual bulk workbook, worksheet
> `Page 2 Coal Stocks Data`, which needs no credential at all.**
>
> This is the same failure shape that document's own §0 records for the MISO LMP families:
> an exhaustive-looking audit of an **incomplete search space**. Three route audits there
> searched two report families while the record sat in a third; here the audit tested the
> API and not the bulk file.

| | miso-256 §5 status | now |
|---|---|---|
| MISO-footprint coal stocks, monthly | **not on disk**; needs `EIA_API_KEY` | **on disk**, 2018–2024, keyless |
| national-vs-footprint rule-14 misalignment | open, needs a reconciled construction | **dissolved** — the footprint is measured directly |
| delivery rate | assumed available with the stocks | **STILL OPEN** — see §5. This is the real remaining blocker. |

## 2. THE MEASUREMENT — MISO's own footprint, not a national proxy

`coal-stocks` clean datatype, joined to the keeper's own bench-part plant set:
**66 of 67 model coal plants matched.** Month-ending stock, Mt:

| year | Jan | Dec | annual change | note |
|---|---:|---:|---:|---|
| 2018 | 32.21 | 27.24 | −4.97 | |
| 2019 | 25.94 | 33.69 | +7.75 | |
| 2020 | 35.03 | 39.83 | **+4.80** | building |
| **2021** | 36.00 | 25.01 | **−10.99** | **the borrow** |
| **2022** | **23.10** | 25.74 | **+2.64** | **lowest January in the record**; Aug low 21.38 Mt is the series minimum |
| 2023 | 25.83 | 36.12 | **+10.29** | rebuild |
| 2024 | 33.24 | 33.37 | +0.13 | |

This reproduces the national MER T06.03 story (`FINDING-miso256` §4: 2021 −39.5 Mt, 2022
≈flat, 2023 +44.2 Mt) **on MISO's own plants, with MISO's own magnitudes** — same signs,
same ordering. The rule 14 `[R-ACCURATE]` misalignment miso-256 flagged ("national ≠ MISO
footprint, needing a reconciled construction, not a literal one") therefore **does not
arise**: there is nothing to reconcile, because the footprint is measured directly.

**2021 is the cause, not a counterexample** — exactly as miso-256 §4 argued from national
data. The fleet funded 2021's high burn out of its stockpile and opened 2022 at the lowest
January stock in seven published years.

## 3. THE ZERO-LP FALSIFICATION

Built strictly from quantities that **predate the year being tested** — opening stock is
December 2021, the delivery rate is the 2020–2021 average, the heat content is the
2020–2021 average. **No 2022 quantity is read.** Coal fleet heat rate is the measured
`miso_campd_marginal_hr_summary.csv` `base_hr` **10.661 MMBtu/MWh** across 74 units, not an
assumption.

| | Mt | TWh |
|---|---:|---:|
| opening stock (Dec-2021) | 25.01 | |
| + delivery rate (avg 2020–21) | 121.89 | |
| **= available** | **146.90** | **249.5** |
| MODEL 2022 coal | 156.59 | 266.0 |
| ACTUAL 2022 coal (implied) | 131.75 | 223.8 |

> **Closing stock if the MODEL's 2022 coal dispatch had actually run: −9.69 Mt.**
> A negative stockpile. The real fleet closed 2022 at **+25.74 Mt**.
> Closing stock at the actual burn: +15.15 Mt — the right side of zero.

The model's 2022 coal is not merely high against a benchmark; it is **infeasible against
the fuel that physically existed**, and that statement contains no price, no residual and
no benchmark — only tons.

**Sensitivity, since one number carries the result.** The conclusion holds across the
plausible heat-rate range and is *conservative* at the measured value:

| heat rate | budget TWh | vs MODEL | closing stock if MODEL ran |
|---:|---:|---:|---:|
| 10.000 | 266.0 | +0.0 | +0.01 Mt |
| 10.500 | 253.4 | −12.6 | −7.33 Mt |
| **10.661 (measured)** | **249.5** | **−16.5** | **−9.69 Mt** |
| 11.000 | 241.9 | −24.2 | −14.67 Mt |

At 10.0 the budget is exactly non-binding — so the finding *does* depend on the fleet heat
rate exceeding 10.0. It is measured at 10.661. Stated rather than buried.

## 4. WHAT THIS DOES **NOT** ESTABLISH

Reported at full magnitude, because the arithmetic is inviting and the conclusion is
narrower than it looks:

* **The budget does not close the gap.** Model−actual is 42.2 TWh; this annual budget
  removes **16.5 TWh, about 39 %**. It carries **no minimum-operating-stock floor** (a real
  fleet never runs to zero), which would tighten it — but that floor is another parameter,
  and inventing one to close the remaining 61 % would be the fitted mechanism rule 1
  `[R-STRUCT]` forbids.
* **An annual budget is the wrong grain.** The real mechanism is monthly with stock carry —
  the storage-SOC shape — which is what makes 2021's borrow and 2022's constraint a single
  consistent story. The annual form above is a *falsification*, not a proposed design.
* **No mechanism was tested.** No `ScenarioConfig` field, no LP row, no solve, no matrix
  cell verdict. Nothing here is evidence that a coal-inventory constraint *would* improve
  any criterion, and it must not be quoted as such.

## 5. THE REMAINING BLOCKER IS THE DELIVERY RATE, NOT THE STOCK

The stock side is closed. The delivery side is **not**, and the precedent cuts against the
obvious route:

> `market_sim/data/winter_fuel_inventory.py` (the NEISO oil mechanism, and the precedent
> miso-256 §5 itself cites): *"This supersedes the rejected `fuel.py:load_oil_burn_budget`
> (F923 petroleum **receipts**, a measured deliveries-to-tank OUTCOME inadmissible under
> CLAUDE.md #13). Here the budget is DERIVED from forward-regenerable capacity/logistics
> quantities — start-of-season tank fill, re-supply delivery rate, boiler firing rate."*

So **EIA-923 Page 5 receipts for the target year are not an admissible delivery rate**, and
neither is the target year's own stock path, which embeds the burn being reproduced
(`ending[m] = ending[m−1] + receipts[m] − burn[m]`). §3 above respects this: its rate is a
**prior-years average**, which is the same construction NEISO uses (a uniform average
delivery rate, deliberately not timed to the binding month).

Whether a prior-years-average rate is the right admissible construction, or whether a
contracted/logistics capacity should be derived instead, is a **methodology judgement that
has not been made** and is not made here. It is the first question any chartered mechanism
must answer, and G-PIN is the gate that enforces it.

## 6. THE PRE-REGISTERED STOP GATES — carried forward VERBATIM

Copied unchanged from `FINDING-miso256` §6 for the successor's PRECOMMIT. Screen year
**2022**, selected on the coal-CF gap (0.106 in 2022, next largest 0.025) and the stock
table, **never on a price residual**.

1. **G-FOOTPRINT** — binds in 2022, **inert** in 2023/24/25 (stocks rebuilt). Binding in a
   loose-stock year kills the arm.
2. **G-DIRECTION** — coal falls toward CF ≤ 0.641 and the flat +4.3 GW decile offset
   compresses. Overshoot below actual kills it.
3. **G-DISPLACE** — released MWh land on gas and imports, not slack/dump.
4. **G-NOFLIP** — no non-target load-bearing criterion goes PASS → FAIL; C1 2023–25 must
   not move.
5. **G-PIN** — the budget must be reconstructible from (opening stock, delivery rate)
   **alone**. If any step reads observed 2022 burn, the arm is **inadmissible regardless of
   its gates**.

STOP gates only: they may kill an arm, never promote one, and are never scored on C3a/C3b.

**§2–§3 above already satisfy G-PIN's construction** and are the evidence G-FOOTPRINT's
premise rests on. They are *not* a screen: no solve was run.

## 7. WHAT LANDED

| artifact | what it is |
|---|---|
| `data/dictionary/schema/coal-stocks.schema.yaml` | the contract — plant × rank × month, short tons |
| `data/raw/coal-stocks/` | verbatim `Page 2 Coal Stocks Data` extracts 2018–2024 + README + SHA256SUMS (752 KB) |
| `scripts/data/fetch_eia923_coal_stocks.py` | keyless bulk fetch; source workbooks not retained, re-fetch is the recovery route |
| `scripts/data/curate_coal_stocks.py` | wide → tidy long, through `write_clean` |
| `src/market_sim/data/coal_stocks.py` | read seam + `opening_stock_tons` (the admissible read) |
| `tests/test_curate_coal_stocks.py` | 6 tests, trivial case first |
| `scripts/regenerate_clean.py` | datatype registered |

Two data-quality decisions, both documented rather than silent:

* **Plant `999999` is excluded.** EIA's synthetic *"State-Fuel Level Increment"* — the
  imputed residual for sub-threshold plants, 141–172 rows/yr. It is not a plant, and it is
  the sole reason a naive `(plant, rank)` key looks ~30 % duplicated. With it removed,
  genuine duplicate pairs are **0 in five of seven years** (2 in 2019, 1 in 2024).
* **`.` / `W` cells are dropped, never zeroed.** A withheld stock is not an empty
  stockpile.

**2025 is a stated gap**: EIA's 2025 release carries no plant-level coal sheet — its
combined `Page 2 Stocks Data` is census-division aggregate in thousand tons with withheld
cells (67 rows). The plant split arrives with the Final Revision. `DATA NEEDED` is recorded
in the raw README.

## 8. THE ISO HEADLINE — task 1, authorized and executed

MISO's status card read **NOT-YET** while its train tier read **CALIBRATED**, purely
because MISO carries its held-out years **inside** the keeper bundle — which rules 16
`[R-ALLYEARS]` and 34(c) `[R-SHARD-PROMOTABLE]` now *require* — while ERCOT/PJM/CAISO/NEISO
reached the same place through folded companion runs. **The pooled read was an artifact of
bundle shape, not of calibration.**

Executed on owner authorization (2026-09-14): a `config_partition` on MISO's keeper shard,
one recipe over two tiers — `{tier train, 2023–2025}` + `{tier validation, 2020–2022}` —
the same mechanism and the same `tier` field ERCOT's own `carveout-validation-2021-2022`
leg uses. Scored live:

| span | determination |
|---|---|
| **train 2023–2025 (gating)** | **CALIBRATED** — grade 7, zero fails, C3c the lone ledgered caveat |
| validation 2020–2022 (non-gating) | NOT-YET — `{fuelmix, price_mean, price_shape, dispatch_corr}` |
| registered full span (preserved) | NOT-YET |

**Nothing scored moved.** `registered_determination` keeps the six-year NOT-YET at full
magnitude, every criterion keeps its own number, the validation rungs render with their own
determination, and no other ISO's files were touched. `audit_keepers --iso MISO`: **0
failures** (the E3 `meta.json`-vs-`calibration_flags` warning is pre-existing).

## 9. RULES

Rule 13 `[R-MEASURED]` (the stock is an admissible *state*; the trap is stated at the schema,
the reader and the README — §5) · rule 14 `[R-ACCURATE]` (the footprint measurement replaces
a national proxy; the misalignment dissolves) · rule 19 `[R-ONE-MECH]` (coal inventory is a
*missing limb*, not a competing mechanism — nothing today caps coal energy) · rule 25
`[R-ISO-SCOPE]` (national grain, ISO scoping at read time, no per-ISO branch) · rule 29
`[R-SCREEN]` clause 0 (zero-LP phase 0 first — and it produced the falsification without a
solve) · rule 30(c) (held-out years are reported and never downgrade MISO) · rule 31
`[R-RETAIN]` (nothing deleted; no bundle was produced) · rule 32 `[R-SHARD]` (a) (the parent
ran no LP and launched no shard) · rule 33 `[R-MECH-MATRIX]` (no mechanism tested, so no cell
moves; the MISO lever queue's now-false "data-blocked" sentence is corrected in place).
