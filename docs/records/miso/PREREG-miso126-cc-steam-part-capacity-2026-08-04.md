# PREREG miso-126 — the missing `CA` combined-cycle **steam part**: 290.4 MW of MISO capacity the fleet build drops

Session miso-126, 2026-08-04, branch `claude/miso-126-backcast-calibration-0ftvx3`,
off `origin/main` at `11d39ec0`. **Written and committed BEFORE any adjudicating
statistic, before any derive and before any solve** (the nyiso-120 / miso-125
standard, which is stricter than "before any arm").

Current MISO keeper: `2026-08-04-miso-124-dualfuel-rearm`
(`results/calibration/miso124_dualfuel_B`), determination `NOT-YET`, sole FAIL
C7 `COAL_PRB` diurnal shape ×3y, ledgered caveats {C3a, C3c}.
`audit_keepers --iso MISO` 0/0.

---

## 1. The lever, and why this one

`docs/mechanism-testing-matrix.md` §5.4 QUEUE STAMP 2026-08-04 (miso-125) leaves
§5.4 with **no** named, un-adjudicated, non-data-blocked item — but it names one
successor explicitly and deliberately declines to charter it:

> **MISO carries 290.4 MW of measurably missing `CA` combined-cycle steam
> capacity.** … This is **named, not chartered**. … It needs its own prereg.

This session is that prereg. The item is chartered **on rule 14 `[R-ACCURATE]`
grounds with a VERIFIED population** — it is not a search. Everything else in
§5.4 is spoken for: C7 `COAL_PRB` regulated self-commitment is CLOSED
(miso-111 `R` / 112 `R` / 113 `I`, confirmed 114; rule 19 `[R-ONE-MECH]` forbids
a fourth mechanism); items 1–2 are data-blocked at a **sourcing** step
(`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md` §8); item 3 is
`R` ex ante; items 4/5/6 are `K`/`I`/`I`; miso-122 executed the hybrid-cogen
scope gate, miso-123 closed the seam hour-of-day lane, and miso-125 adjudicated
the prime-mover grain `R`.

### 1.1 Rule 25 `[R-ISO-SCOPE]` scope, fixed up front

miso-125's census names five candidates. **Only MISO's two are in scope.**

| plant | ISO | MW | fuel | disposition here |
|---|---|---|---|---|
| 55088 Dearborn `ST1` | MISO | 250.0 | BFG | **IN SCOPE** |
| 50973 Motiva `GN31`/`GN32`/`GN33` | MISO | 40.4 | OG | **IN SCOPE** |
| 1004 Edwardsport | MISO | 555.0 | SGC | **NOT a defect** — its `SGC` steam part IS represented, as `COAL` 555.0. Excluded by the presence test, not by hand. Do not "fix" it. |
| 54912 Martinez `STG1` | CAISO | 20.0 | OG | **HANDED OFF, unstamped** — CAISO's lane derives its own parameters from its own market's data |
| 6081 Stony Brook `CA1` | NEISO | 96.0 | DFO | **HANDED OFF, unstamped** — and UNDETERMINED even on presence |

The mechanism ships **ISO-gated to MISO** so no other ISO's fleet can move on
this commit. Neither CAISO's nor NEISO's matrix cell is stamped.

### 1.2 The defect, at grain

`market_sim.data.fleet.eia860._map_fuel_type` maps a generator to a model fuel
type from `technology` / `Energy Source 1` / `Prime Mover`, and
`config.plant_taxonomy.classify_plant` then buckets it. **Both key on the
energy-source code.** `BFG` (blast-furnace gas) and `OG` (other gas) are not
`NG`, not coal, not oil/biomass/nuclear/wind/solar/hydro — so `_map_fuel_type`
returns `None`, the row is `continue`d out of the row loop, and **the capacity
never reaches the LP at all**. `classify_plant`'s own docstring says the residual
`OTHER` bucket is where "other/process gas, purchased steam, waste heat …" go.

But **EIA-860's `Energy Source 1` on a `CA` row describes the block's
supplementary / duct fuel**, not its primary energy input, which arrives as
turbine exhaust. `CA` is EIA's code for the *steam part of a combined cycle*.
The row is not an exotic process-gas machine; it is half of a gas-fired CC
block whose other half is already in the fleet.

Confirmed on disk (`data/raw/eia-860/eia860_generator_operable.parquet`, and
the processed `eia860_generators.parquet` the fleet actually loads):

| plant | gen | technology | pm | Unit Code | summer MW | ES1 | in LP fleet? |
|---|---|---|---|---|---|---|---|
| 55088 | `GT 1` | NG Fired Combined Cycle | `CT` | `SINT` | 175.0 | NG | yes, `CC_CHP` |
| 55088 | `GT2` | NG Fired Combined Cycle | `CT` | `SINT` | 175.0 | NG | yes, `CC_CHP` |
| 55088 | `GTP1` | NG Fired Combustion Turbine | `GT` | — | 165.0 | NG | yes, `CT_CHP` |
| 55088 | **`ST1`** | **Other Gases** | **`CA`** | **`SINT`** | **250.0** | **BFG** | **NO** |
| 50973 | `GN31`/`GN32`/`GN33` | Other Gases | `CA` | `BLK1` | 8.4 + 10.5 + 21.5 | OG | **NO** |
| 50973 | `GN35`/`GN41`–`GN44` | NG Fired Combined Cycle | `CT` | `BLK1` | 183.4 total | NG | yes |

The processed parquet **already carries these rows**, with the eGRID plant heat
rate joined (`55088` → 6.346441 on all four generators, identical to its `CT`
siblings). Nothing is missing from the data. The fleet build drops them.

### 1.3 Charter grounds, stated up front and binding

This is a **rule 14 `[R-ACCURATE]`** item — a real, published, measured capacity
that the model does not represent — **and nothing else.**

* It is **NOT** chartered as a C7 `COAL_PRB` instrument. It cannot close C7 and
  no result here may be quoted as C7 progress.
* It is **NOT** chartered as a C3a or C3c instrument.
* It **ships, or is refused, on whether the input is more accurate — whatever
  it does to the residual** (rule 1 `[R-STRUCT]`, both directions). A worse fit
  is a discovered bug elsewhere, not grounds to revert (rule 14 explicitly).
* Rule 13 `[R-MEASURED]` admissibility: a generator's existence, prime mover,
  unit code and summer capacity are EIA-860 **inputs**, published annually, that
  regenerate for any forward year and respond to changed conditions (a retired
  or re-rated machine changes them). This is not a measured *outcome* fed back
  to close a residual — nothing here is tuned against price or volume.

### 1.4 The two defects share ONE cause, so they move in ONE change (rule 19)

miso-125 §4 established that the same missing machine also corrupts the CHP
heat-rate denominator: eGRID's `PLNGENAN` = 5,259,825 net MWh at 55088 counts
`ST1`'s generation, while the LP holds only 515.0 MW, implying a **116.6 %**
capacity factor. At the repaired 765.0 MW it is **78.5 %**. So the incumbent
`measured_chp_heat_rates` rate (6.9573) is **already a block rate** — it is the
capacity, not the rate, that is wrong.

Therefore the arm **also re-derives** `chp_power_only_heat_rates_MISO.csv` onto
the repaired fleet, in the same change. Shipping the capacity without the
re-derive would leave 250 MW of new capacity recorded against a denominator that
assumes it. Rule 23 `[R-FROZEN-DERIVE]`: the re-derive commit cites the
**fleet / denominator change on measured grounds**, never a residual.

---

## 2. The construction, fixed before measurement

**The predicate.** An EIA-860 **operable** generator is the *steam part of a
gas-fired combined-cycle block* iff **all** of:

```
(a) Prime Mover == "CA"                       (EIA: combined-cycle steam part)
(b) Energy Source 1 != "NG"                   (else it already classes correctly)
(c) Unit Code is non-empty
(d) >= 1 sibling at the SAME Plant Code with the SAME Unit Code,
    Prime Mover == "CT" and Energy Source 1 == "NG"
```

This is miso-125's `ke_r` R4 diagnostic **verbatim**. Clause (d) is what
distinguishes a genuine CC steam part from a landfill-gas or oil standalone: the
shared `Unit Code` is EIA-860's own machine-level statement that the rows are
one block.

**The repair.** A matching generator enters the LP fleet as gas CC —
`CC_CHP` where the plant is CHP-flagged, `CC_REGULAR` otherwise — at the plant
heat rate the processed parquet already carries, i.e. exactly the rate its `CT`
siblings carry. It is then absorbed into the existing per-plant tranche
(`fleet_to_bins`, `plant_level_fleet=True`), so its capacity, outage overlay,
offer curve and heat rate are the block's, keyed on `(plant_code, plant_group)`.

**Arming.** A new `ScenarioConfig` field `cc_steam_part_capacity: bool = False`,
default **off** and byte-identical off (rule 26 `[R-REGISTRY]`: arming visible in
`run_config.json`; rule 28c: its matrix row lands in the same PR). ISO-gated to
MISO (rule 25).

**Zero fitted parameters** (rule 24 `[R-REGISTRY]`). Nothing is swept against a
residual. There is no threshold, no percentile and no band in the predicate —
every clause is an equality on a published categorical field.

### 2.1 The load-bearing assumptions, written down as numbered properties

*This section exists because of miso-125 §7 item 4: both of that session's
pre-declared magnitude routes failed to fire and the lever was still killed with
zero solves — by a **validity check on the construction's own stated
assumption**. Each property below carries its own falsifier. **If any falsifier
fires, the arm stops there**, whatever the magnitudes say.*

**P1 — ABSENCE.** The steam part's capacity is genuinely absent from the LP
fleet, so adding it is a repair and not a double count.
*Test:* the ISO's loaded fleet total at the plant equals the EIA-860 operable
plant total **excluding** the `CA` rows (±1 MW), **and** the EIA-860 plant total
**including** them exceeds that by more than 1 MW.
*Falsifier:* a candidate whose fleet total already matches the EIA-860 total
**including** `CA` is `REPRESENTED` and is excluded. This is the test that caught
1004 Edwardsport as a 555 MW false positive; presence is decided against the
plant's **EIA-860 TOTALS**, never against block siblings (miso-125 §6).

**P2 — ONE METER, ONE RATE.** The block's fuel is metered at its `CT` rows; the
steam part burns no fuel of its own that the plant's joined heat rate does not
already cover. So the correct LP representation is the *block* heat rate over the
*block's total* capacity, and adding the `CA` row must not change the block's
fuel-per-MWh intensity.
*Test (a):* the `CA` row's `heat_rate` in `eia860_generators.parquet` equals its
`CT` siblings' (it is an eGRID plant-average join, so it must).
*Test (b), the quantitative one:* the eGRID denominator that produced that rate
already contains the steam part's generation. Formally, the implied capacity
factor `PLNGENAN / (Σ fleet MW × 8760)` must be **impossible (> 100 %) on the
present fleet and possible (≤ 100 %) on the repaired fleet**.
*Falsifier:* if a candidate plant's **present-fleet** implied CF is already
≤ 100 %, the eGRID denominator is **not** evidence that the missing machine sits
inside it, the block-rate claim is unsupported for that plant, and that plant
does not enter. (55088 is expected to pass at 116.6 % → 78.5 %; **50973 has not
been measured and may fail this**, in which case it is excluded and the lever
becomes 250.0 MW, not 290.4 MW.)

**P3 — DESIGN-SHARE COHERENCE (the miso-125 §4 residual doubt, made
falsifiable).** miso-125 could not exclude the hypothesis that `ST1` is a
**let-down turbine on the three dark boilers** (7.3 M MMBtu, `dark_fuel_share`
0.166) rather than an HRSG on the `CT` exhaust. If that were true, the block-rate
claim of P2 would fail: the dark-fuel gate removes those boilers' fuel while the
steam turbine's generation stays in `PLNGENAN`, so the repaired block would be
priced too cheaply.
*Test:* the steam part's **implied generation share of the block** must be
consistent with its **EIA-860 nameplate share of the block** — the manufacturer's
own design split, a measured datum requiring no invented band:

```
implied_gen_share  = (PLNGENAN - Σ CEMS gross over the block's CT units - Σ CEMS gross
                      over the plant's other power-train units)
                     ÷ (that numerator + Σ CEMS gross over the block's CT units)
nameplate_share    = Σ nameplate of the block's CA rows ÷ Σ nameplate of ALL block rows
```

Declared **before measurement**: `|implied_gen_share − nameplate_share| ≤ 0.10`.
*Falsifier:* an implied share materially **above** the design share says the
steam turbine produces more than the gas turbines can drive it to — i.e. it has an
independent steam source, the let-down hypothesis is live, and the block-rate
assumption fails. **The arm stops and the item closes `R` on P3.** (`implied_gen_share`
is computed on a gross/net mixed basis and so is a *lower* bound on the true share;
that direction is stated because it makes the falsifier conservative — a
gross-basis correction can only move the implied share **up**, toward the
falsifier, never away from it.)

**P4 — ARTIFACT STABILITY.** Adding the `CA` row to `CC_CHP` must not perturb the
committed CHP measurement it depends on. Re-deriving
`chp_power_only_heat_rates_MISO.csv` on the repaired fleet must leave
`heat_rate`, `flag`, `thermal_share`, `dark_fuel_share`, `heat_rate_credited`,
`basis_heat_rate` and `model_heat_rate` **unchanged on every row**; only
`class_capacity_mw` (and any purely derived echo of it) may move.
*Falsifier:* any change to `heat_rate` or `flag` means the repair moves the
measurement it is justified by — circular — and the arm stops. In particular a
`(55088, CC_CHP)` flag flip from `ok` to `basis_mismatch` would silently
**disarm** `measured_chp_heat_rates` at the only plant it reaches in MISO, which
would make an A/B a two-mechanism confound (rule 19).

**P5 — NO OTHER ISO MOVES.** With `cc_steam_part_capacity=True` and ISO gating,
`load_fleet_from_csv` must return a **byte-identical generator list** for ERCOT,
CAISO, PJM, NYISO and NEISO, and an identical list for MISO when the flag is
off.
*Falsifier:* any non-MISO fleet delta is a rule 25 `[R-ISO-SCOPE]` breach and the
arm stops.

---

## 3. Kill criteria, pre-declared and in order

**KE1 — population verification (data-side gate).** Rebuild the miso-125 R4
census from `eia860_generator_operable.parquet` and re-run the fleet-presence
cross-check. Pre-declared expectation: **MISO 290.4 MW missing over exactly two
plants** (55088 `ST1` 250.0; 50973 `GN31`/`GN32`/`GN33` 40.4), 1004 Edwardsport
`REPRESENTED`. Mandatory guards, both from the miso-125 / miso-116 trap list:
(a) EIA-860 `Summer Capacity (MW)` is **NaN on some rows** (Edwardsport's
CT1/CT2) — a bare `.sum()` silently reads zero, so the probe asserts the
candidate frame is non-empty and reconciles the plant totals against
`Nameplate Capacity (MW)` as well; (b) the fleet side is built from the
**keeper's own** `run_config.json` settings, never `load_fleet_from_csv`'s
defaults (`measured_chp_heat_rates` defaults **False** while the keeper **arms**
it — the miso-116 measurement trap).
**A census that disagrees with miso-125 stops the session** — it would mean one
of the two published records is wrong, and that is adjudicated before anything
is armed.

**KE2 — the five properties of §2.1.** Every falsifier is evaluated **before**
any liveness statistic and before any solve. Any one firing closes the item
without an A/B.

**KE3 — INERT-BY-DISPATCH (zero-solve route).** The repaired capacity can only
matter in hours it would actually run. Compute, from the **committed** keeper
sidecars (`hourly/system_<year>.parquet` prices, `hourly/class_hourly_<year>.parquet`)
and the block's own marginal cost at the keeper's gas prices
($2.54 / $2.19 / $3.52 per MMBtu, `miso124_dualfuel_B/meta.json`), the share of
hours in which the added capacity's marginal cost is **at or above** the zonal
price — i.e. hours in which it would not dispatch.
Declare **`I` with zero solves** if, in all three years, the added capacity
would dispatch in **< 5 % of hours**, so its annual energy is bounded below
**0.05 %** of MISO load.
*Stated honestly ex ante:* this route is **expected not to fire**. A CC block at
6.9573 MMBtu/MWh is deep-inframarginal at MISO's prices, and unlike miso-119 /
121 / 122 / 125 this lever adds **new capacity** rather than re-pricing or
re-allocating existing capacity — there is **no zero-sum identity to bound it**.
The A/B is expected to be needed, and KE3 is declared so that the null is
falsifiable, not so that it is reached.

**KE4 — INERT-BY-BINDING (zero-solve route), reported honestly.** New capacity
at a plant that never reaches its existing cap adds nothing. The committed
sidecar schema is `(year, pass, klass, hour, mw)` at **CLASS** grain and carries
no bound flag, so **55088's own binding cannot be read from committed artifacts**
(the same limitation miso-125 recorded for its KE4 clause (a)). The probe
reports the class-level statistics the sidecar **does** support — `CC_CHP` hourly
dispatch against class capacity — and **states explicitly that this is not a
plant-grain binding measurement and is not offered as a proxy for one.** No `I`
is declared on this route from a class-grain statistic.

**KE5 — control integrity.** A same-HEAD zero-delta arm A must reproduce the
incumbent keeper's scorecard **exactly**: determination, all nine criterion
statuses, ledgered caveats, and every legitimacy-diagnostic verdict. Every A/B
delta is quoted against **arm A**, never against the committed keeper.

**KE6 — firing proof.** This is an **INPUT-DELTA** lever (fleet + heat rate), so
the warm-P1 heuristic does **not** apply — **both** passes carry it. Firing is
proven two ways, never inferred:
(a) a pre-arm `load_fleet_from_csv` check asserting 55088 goes
**3 generators / 515.0 MW → 4 generators / 765.0 MW**, that the added row carries
`plant_group == "CC_CHP"`, that its `heat_rate` matches its `CT` siblings', and
that its assigned zone matches theirs;
(b) a post-arm **per-class ENERGY** delta from the two bundles' `class_hourly`
sidecars.
A null is not trusted until both fire.

**KE7 — A/B verdict gate (K6-equivalent).** Modelled on
`scripts/probes/_miso124_dualfuel_rearm_ab.py`'s K6: the A/B scorer diffs the
**nine criterion statuses, the determination, the ledgered caveats AND every
legitimacy-diagnostic verdict** between arm A and arm B. A determination or
criterion regression is reported as such and **is not grounds to revert** the
capacity repair (rule 14, rule 1) — it is a discovered root-cause item. A
determination **improvement** is likewise not the ship criterion; accuracy is.

---

## 4. The five DO-NOT-MISREAD guards, applied ex ante

* **miso-119** — `max |Δoffer|` is an **upper bound only**; it over-predicted the
  realized price effect by two orders of magnitude. No liveness claim here rests
  on any offer-delta magnitude.
* **miso-121** — **binding is not marginality.** The p50 over binding hours
  over-predicted by five orders. KE3 is written on **would-it-dispatch**, not on
  a percentile of an offer delta, and KE4 explicitly refuses to substitute a
  class-grain proxy for a plant-grain marginality statistic.
* **miso-122** — `max_abs_class_hour_mw` is **not** a mechanism magnitude at
  MISO: it reads 912.5 MW for unrelated levers because it lands on the import
  class where one seam band flips. This session reads **per-class ENERGY
  deltas** and will not quote that statistic.
* **miso-124** — the price response is **not stable across keepers** (the same
  flag moved max zonal |dLMP| 0.0003 on miso-117b and 1.383 on miso-122b). No
  price magnitude is carried in from any prior MISO session; every bar is
  re-measured against `miso124_dualfuel_B`, the keeper actually replayed.
* **miso-125** — a **wrong-sign magnitude is a denominator defect, not a small
  effect**; and presence/absence must be tested against a plant's **EIA-860
  TOTALS**, never against block siblings. P1 and P3 above are that lesson written
  as falsifiers.

---

## 5. What is settled and is NOT re-opened (rule 28a DO-NOT-REDO)

* **The CHP prime-mover share split at MISO — `R` at miso-125.** No different
  share statistic is derived here. This session does **not** attribute `ST1`'s
  generation between the `CC` and `CT` families; it adds the machine's
  **capacity** to the block and keeps the block's single measured rate. P3 exists
  precisely so that the unresolved attribution question cannot silently become a
  load-bearing assumption of this construction.
* **C7 `COAL_PRB` regulated self-commitment — CLOSED** (miso-111 `R` / 112 `R` /
  113 `I`, confirmed 114). Not touched, not measured, not quoted. C7 is
  data-blocked on cost-side levers; route (i) needs the miso-78/79 congestion +
  sub-hourly-RT lane, route (ii) has no admissible source.
* **Seam hour-of-day shape — CLOSED at miso-123**, all three mechanism classes
  spent. `miso_seam_flow_percentile` is not swept.
* `dual_fuel_switching` `K` (armed, tested INERT), `gas_offer_margin_zonal_anchor`
  `I`, `hydro_budget_nameplate_aware` `I`, `pjm_da_virtual_bids` `R` ex ante,
  `measured_ct_heat_rates` `K`, `measured_chp_heat_rates` `K` + hybrid-cogen
  scope gate EXECUTED (miso-122) + prime-mover grain `R` (miso-125).

---

## 6. Rule 22 `[R-HOLDOUT]` — the training years and nothing else

MISO holds **no** `calibration-complete` marker. Therefore **2023, 2024 and 2025
only** may be solved, scored **or read**. No 2022, no 2019, no ≤2021, no H1-2026
— not as a solve, not as a probe, not as a sidecar read. Any A/B is
`--years 2023 2024 2025` in **ONE** invocation (rule 16 `[R-ALLYEARS]`; a per-year
chain writes `meta.json` with only the last year and breaks K5). A mechanism
change is scored leave-one-year-out within 2023–2025 before any promotion is
proposed.

---

## 7. Rule duties this session discharges

* **Rule 15 `[R-DASHBOARD]`** — every completed run is registered in-session,
  keeper or rejected; if a phase produces no LP run, that is stated explicitly.
* **Rule 16 `[R-ALLYEARS]`** — 2023 2024 2025, one bundle, one invocation.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the CHP re-derive commit cites the fleet /
  denominator change on measured grounds.
* **Rule 25 `[R-ISO-SCOPE]`** — MISO only; CAISO 54912 and NEISO 6081 handed off
  unstamped.
* **Rule 26 `[R-REGISTRY]`** — arming visible in `run_config.json`.
* **Rule 28b** — the tested cell is stamped in THIS session, rejection or inert
  verdict included. **Rule 28c** — the new `ScenarioConfig` field carries its
  matrix row in the SAME PR.
* **Rule 27 `[R-PUSH]`** — exact on-disk bytes; blob-verify line count + hash
  after any push touching a ≥300-line file.
