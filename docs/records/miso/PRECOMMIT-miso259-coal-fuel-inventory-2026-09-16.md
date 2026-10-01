# PRECOMMIT — miso-259: the coal fuel-inventory monthly energy budget

```
SESSION : miso-259        ISO: MISO        KEEPER: 2026-09-12-miso-255-sil-measured
MECHANISM: coal_fuel_inventory (NEW ScenarioConfig field, default OFF, MISO-gated,
           backcast-only) — the missing CEILING on coal.
SCREEN  : ONE year, 2022, two shards (arm + control) at the SAME HEAD.
LP SPENT BY THE PARENT: ZERO (rule 32 [R-SHARD] (a)).
```

Written and pushed **before** either solve. Every number below is computed from
committed bytes at zero LP, and every design choice is pinned here rather than
after the result.

---

## 1. THE OBJECT

MISO's gas passthrough slope is **4.63 $/MWh per $/MMBtu against the real
market's 8.41 — 55 %** — propped by a fixed intercept, with
`corr(gas price, model error %) = −0.841` (`FINDING-miso256` §0). The proximate
cause is a **flat +4.3 GW coal block in every hour of 2022** (§3): coal carries
take-or-pay and must-run **floors** and the model has **no fuel-inventory state
for coal at all**.

Rule 19 `[R-ONE-MECH]` is clean by inspection: nothing in the model caps coal
energy today, so this is a **missing limb**, not a competing mechanism, and it is
never stacked on a coal floor.

## 2. PHASE 0 — REPRODUCED EXACTLY, AND G-FOOTPRINT PASSES

Reproduced at zero LP by `scripts/probes/_miso259_coal_budget_phase0.py` from the
keeper's own committed `hourly/` sidecars, the `coal-stocks` datatype and the new
`coal-receipts` datatype. Fleet heat rate is the measured
`miso_campd_marginal_hr_summary.csv` `base_hr` **10.661 MMBtu/MWh over 74 CAMPD
units** — not an assumption.

**Pre-registered footprint** (the owner-ruled construction, §3): modelled coal
generator plants **plus** shared-storage entities the committed crosswalk ties to
them.

| yr | open Mt | rate Mt | MMBtu/t | avail TWh | MODEL | slack | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 2020 | 35.63 | 157.20 | 18.10 | 327.9 | 199.3 | **+128.6** | inert |
| 2021 | 41.91 | 136.67 | 18.14 | 304.3 | 245.8 | **+58.5** | inert |
| **2022** | **25.03** | **126.26** | 18.11 | **257.4** | **265.7** | **−8.3** | **BINDS** |
| 2023 | 26.73 | 130.43 | 18.16 | 268.1 | 180.6 | **+87.5** | inert |
| 2024 | 37.10 | 126.61 | 18.18 | 279.5 | 167.5 | **+112.1** | inert |
| 2025 | 34.69 | 111.96 | 18.06 | 248.8 | 201.8 | **+47.0** | inert |

**G-FOOTPRINT's pre-registered condition — binds in 2022, inert in 2023/24/25 —
is satisfied exactly, and 2020/2021 are inert too.**

**Robustness, measured rather than asserted.** All four constructions tested give
the **same verdict pattern**; they differ only in how hard 2022 bites:

| construction | 2022 slack | other years |
|---|---:|---|
| generator plants only, all receipts (the miso-258 table, reproduced to ±0.1 TWh) | −16.1 | all inert |
| **+ shared storage 8841, all receipts (PRE-REGISTERED)** | **−8.3** | all inert |
| generator plants only, contracted receipts only | −22.9 | all inert |
| + 8841, contracted only | −15.0 | all inert |

So the construction choice **cannot** manufacture the gate verdict. That is why
it was safe to settle it on admissibility grounds alone.

## 3. THE OWNER'S RULING — taken ex ante, from three options, before any solve

Put to the owner 2026-09-16 with the table above in hand. Ruled:

1. **Delivery rate = (a) prior-years AVERAGE receipts**, mean of Y−2 and Y−1,
   **all purchase types**, spread **uniformly** across the year. This mirrors the
   NEISO oil precedent exactly — "a uniform average delivery rate, deliberately
   NOT timed to the coldest month, which would be tuning the mechanism to the
   residual". Option (b) contracted-only (94.8–98.0 % of MISO receipts) was
   declined as a second selection step for a ~4 % difference; option (c)
   rail/logistics capacity was declined because **no citable published
   MISO-footprint rail delivery capacity exists** — the data supports a rail
   *share* (RR 97.42 of 123.35 Mt in 2021, 79 %) and a share is not a capacity,
   so deriving one from the observed share would be the fitted mechanism rule 1
   `[R-STRUCT]` forbids.
2. **Include shared-storage entity 8841.** Rule 14 `[R-ACCURATE]`, and it **cuts
   against the mechanism**: `DTE-BRSC Shared Storage` received 32.01 Mt over
   2018–2024 while Belle River's own id 6034 files **zero** receipts, so
   including it LOOSENS the 2022 budget from −16.1 to −8.3 TWh of slack.
3. **Monthly grain, no stock carry.**

**Rule 21 `[R-DOF]` ledger entry.** One entry, and it is **not** a tuned value:

| parameter | value | identification source |
|---|---|---|
| `coal_fuel_inventory` delivery-rate construction | prior-years (Y−2, Y−1) mean receipts, all purchase types, uniform monthly spread | **Owner ruling 2026-09-16**, taken ex ante from three presented options with the gate table already fixed; construction mirrors `winter_fuel_inventory.build_winter_fuel_budget`. Measured: every option tested gives the same verdict pattern, so the ruling cannot have been selected on a result. |

Nothing else in the mechanism is free. The opening stock, the delivery rate, the
heat content and the fleet heat rate are all measured; the minimum operating
stock is **zero**, not a parameter.

## 4. DESIGN, PINNED EX ANTE

* **Monthly rows, no carry.** Twelve independent pooled-fleet rows:
  `(opening stock + delivery rate) × MMBtu/ton / 12`. Structurally the NEISO
  Component-A shape through the same `_build_oil_budget_rows` builder, reached by
  its **own `coal_*` kwarg family** so the two fuel budgets append as independent
  row families and can never silently overwrite one another.
  **Monthly-independent rows cannot carry stock across months — a stated
  limitation, not a defect.** A true SOC-style carry is a new LP row family and
  is deliberately not this arm.
* **Minimum operating stock = ZERO.** A real fleet never runs its piles to
  nothing, so this budget is **looser than physics**. It is left that way: a
  floor chosen to close the remaining residual is the fitted mechanism rule 1
  forbids. A floor may be added later only from a **cited days-of-burn source**.
* **MMBtu-correct.** The row sums `heat_rate[g] × P[g,t]`, so a
  heterogeneous-heat-rate fleet is priced on the fuel it consumes. Verified by
  unit test: a 6,000 MMBtu cap yields 600 MWh at HR 10, not 6,000 MWh.
* **Gates raise, they do not silently skip.** Arming for a non-MISO ISO or in
  forecast mode raises `ValueError`. A missing measured input returns `None` and
  logs a warning — the budget is **never** sized on a substitute.

**Rule 13 `[R-MEASURED]` — the forward story, which is the actual test.** In a
forecast year the opening stock is the model's **own carried inventory from the
prior simulated year** (the role a storage SOC boundary plays) and the rate is a
trailing or contracted volume over the years already simulated. Both regenerate
from forward drivers with no measured input, and both respond to changed
conditions. That is also why it matters forward: a model that cannot deplete a
stockpile will over-predict coal in exactly the high-gas scenarios a
decarbonization study is run to answer.

**Byte-identical off, measured.** Default `cache_key` is `9ca2c6052b4850ea` on
both `origin/main` and HEAD; armed hashes distinctly as `51e13b62907f1911`. The
`coal_*` dispatch keys are left `UNSET` when unarmed, so an unarmed run's kwargs
**key set** is unchanged.

## 5. G-DRIFT — COULD NOT BE COMPLETED AS SPECIFIED. A CONTROL IS SPENT.

Rule 29 `[R-SCREEN]` (b) makes the keeper's committed bundle the control
(**form 4**) provided a code-level drift audit finds every changed hunk INERT.
**That audit could not be completed here, for two reasons, both stated rather
than worked around:**

1. **The keeper's recorded `git_sha` `d0fec486` is UNREACHABLE.** `git cat-file`
   returns *"Not a valid object name"*. It was a shard-branch commit and the
   branch has since been deleted — precisely the failure rule 33
   `[R-SHARD-ARCHIVE]` (d) warns about. The literal G-DRIFT command cannot be
   run at all.
2. Substituting the commit that landed the keeper bundle on `main` (`3cd1021b`),
   the solve path has moved by **51 files and 5,280 insertions**. That is not a
   volume this session can responsibly certify hunk-by-hunk.

**What WAS established mechanically, and it is worth recording:**

* **MISO's solve-surface fingerprint is byte-identical at HEAD**:
  `9f0845000dc8af6e`, **210 rows, `moved: {}`** — exactly the value the keeper's
  own `run_config_2022.json` records. Every registry table MISO's solve reads is
  unchanged (capx D79 / owner ruling Q54).
* **Every MISO mention in the changed backcast-path files is set-membership
  expansion adding NWPP/SOCO** — `renewables.py` and `zone_assignment.py` add the
  two new ISOs to sets MISO was already in; MISO's own membership is untouched.
  The one `eia930/envelopes.py` mention is a comment.
* The default `cache_key` is unchanged.

That is strong for the data-registry half and silent on the shared code half, so
**form 4 is NOT claimed.** The LIVE-hunk branch applies and **one control solve
is spent, for the screen year only** — which is also strictly better evidence:
a same-HEAD A/B cannot be contaminated by drift at all.

## 6. THE PRE-REGISTERED STOP GATES — carried forward VERBATIM

Screen year **2022**, selected on the coal-CF gap (0.106 in 2022; next largest
0.025) and the stock table — **never on a price residual**.

1. **G-FOOTPRINT** — binds in 2022, **inert** in 2023/24/25. Binding in a
   loose-stock year kills the arm.
2. **G-DIRECTION** — coal falls toward CF ≤ 0.641 (the fleet's best demonstrated
   year) and the flat +4.3 GW decile offset compresses. **Overshoot below actual
   kills it.**
3. **G-DISPLACE** — released MWh land on **gas and imports**, not on slack/dump.
4. **G-NOFLIP** — no non-target load-bearing criterion goes PASS → FAIL; **C1
   2023–25 must not move.** The train tier is CALIBRATED; breaking it to fix a
   validation year is a loss.
5. **G-PIN** — the budget must be reconstructible from (opening stock, delivery
   rate) **alone**. If any step reads observed 2022 burn, stock path or receipts,
   the arm is **INADMISSIBLE regardless of its gates**.

STOP gates **only**: they may kill the arm, never promote it, and are **never**
scored on C3a/C3b.

**G-PIN is already discharged at the code level** and is covered by a unit test
(`test_solved_year_stock_and_receipts_are_never_read`): the builder reads
`opening_stock_tons(ids, year)` — December of `year−1` — and
`prior_years_delivery_rate(ids, year)` — years `Y−2`, `Y−1`. The reader module
deliberately exposes **no** function returning the target year's own receipts.

## 7. THE SHARDS

Two, at the same pinned HEAD, launched concurrently (rule 12 `[R-PARALLEL]`:
separate invocations, ≤2 for a per-plant multi-zone LP).

| shard | out-dir | branch | recipe |
|---|---|---|---|
| **control** | `results/calibration/miso259_screen_control` | `claude/miso259-screen-control` | `replay_keeper.py results/calibration/miso255_sil_keeper --years 2022` |
| **arm** | `results/calibration/miso259_screen_arm` | `claude/miso259-screen-arm` | same **+ `--set coal_fuel_inventory=true`** |

Single delta. Both push their bundles to their own branches per rule 34
`[R-SHARD-PROMOTABLE]` (a), including `dispatch/2022_P1.parquet`.

**Expected arm signature, stated before the solve so it cannot be written to
fit**: the run log must print a `coal fuel-inventory budget (MISO 2022)` line
carrying opening stock **25.03 Mt**, delivery rate **126.26 Mt/yr** from
**2020+2021**, and an annual budget of **≈257 TWh-equivalent at HR 10.661**. A
different number there means the footprint or the read is wrong, and the shard
stops.

## 8. WHAT THIS WILL NOT DO — stated now, not discovered later

* **The budget closes ~39 % of the 42.2 TWh model-actual 2022 coal gap on the
  annual form** (and the pre-registered footprint, which includes 8841, closes
  *less* than that — ~20 %). It is a **partial repair** and must not be presented
  as closing 2022.
* The falsification needs the coal fleet heat rate **above 10.0 MMBtu/MWh**; at
  exactly 10.0 the budget is non-binding. It is measured at 10.661 over 74 units.
  **One number carries it**, and that is stated rather than buried.
* Other terminals in the EIA record (`CCT Terminal` IL, `Four Rivers` KY,
  `Keystone`/`Conemaugh` PA) cannot be tied to a served plant from the data
  alone and are **omitted rather than guessed**, leaving the footprint
  conservatively tight by an unquantified amount.
* 2025 plant-level stocks are not published; 2025's opening stock is **December
  2024, which IS curated**, and its delivery rate is 2023+2024. Verified, not
  assumed — the 2025 row of §2 is computed, not estimated.

## 9. RULES

Rule 1 `[R-STRUCT]` (structure first; the construction was settled on
admissibility and is measured not to change the verdict) · rule 13
`[R-MEASURED]` (every sizing quantity predates the solved year; the forward story
is written down) · rule 14 `[R-ACCURATE]` (the shared-storage reconciliation,
taken in the direction that weakens the mechanism) · rule 19 `[R-ONE-MECH]` (a
missing limb; own kwarg family so the two fuel budgets cannot stack) · rule 21
`[R-DOF]` (one ledger entry, identified by the owner ruling) · rule 24
`[R-REGISTRY]` (cache-key registration + defaults ledger + TIER_TAGS in the same
commit; the crosswalk is a committed data file, not a code dict) · rule 25
`[R-ISO-SCOPE]` (MISO-gated by a raise; other ISOs enter the matrix as U) · rule
28 `[R-MECH-MATRIX]` (base row + a cell in all nine shards, same PR) · rule 29
`[R-SCREEN]` (zero-LP phase 0 first; one-year screen; G-DRIFT reported as
incomplete and the control spent) · rule 32 `[R-SHARD]` (the parent runs no LP)
· rule 34 `[R-SHARD-PROMOTABLE]` (both shards push their bundles).
