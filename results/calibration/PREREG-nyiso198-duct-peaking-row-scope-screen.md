# PREREG nyiso-198 — the combined-cycle duct-burner peaking share taken at the grain EIA-860 reports the flag: `cc_duct_peaking_row_scoped`

**Session:** nyiso-198, 2026-09-06. **Branch:** `claude/nyiso-backcast-calibration-jnciv2`.
**Keeper (control, rule 29(b) form 4):** `2026-09-06-nyiso-196-extract-basis`, bundle
`results/calibration/nyiso196_extract_basis`, `basis_sha 5b5af5ab`, CALIBRATED, grade 7 of 8,
fails 0, C3c the lone ledgered caveat.
**Solves at the time of writing: ZERO.** Everything in §0–§5 is measured from committed
artifacts plus three `fleet_only` rebuilds (no LP).
**Machine records:** `results/calibration/_nyiso198_cricket_partload_phase0.json`,
`_nyiso198_duct_peaking_basis_phase0.json`; probes
`scripts/probes/nyiso198_cricket_partload_phase0.py`,
`scripts/probes/nyiso198_duct_peaking_basis_phase0.py`.

---

## 0. Phase 0 — the (b−) bucket resolved to ONE binding LP bound

The queue item is Cricket Valley 57185's part-load bucket **(b−) = 906.1 GWh in 2024** — the
plant-hours where the model and the meter are both online and the model runs BELOW the meter
(`FINDING-nyiso196` §6 item 3). The brief's three candidates are an availability object, a
min-load object, or an offer-position object. Inside this LP every dispatched MW sits between
two reconstructible bounds, `pmin[g,t] ≤ P[g,t] ≤ pmax[g]·availability[g,t]`, so the question is
decided without a solve by asking which bound binds in each (b−) hour.

**2024, Cricket Valley 57185** (`_nyiso198_cricket_partload_phase0.json`):

| binding bound | hours | deficit GWh | share | mean model / meter / envelope MW | mean LMP |
|---|---:|---:|---:|---|---:|
| **CAP_SCOPE** (at envelope, no outage — LP capacity too small) | 0 | 0.0 | 0.0 % | — | — |
| **CAP_OUTAGE** (at a derated envelope) | 950 | 100.5 | 11.1 % | 477.8 / 583.6 / 478.2 | $40.54 |
| **FLOOR** (at the commitment-bridge min-gen) | 0 | 0.0 | 0.0 % | — | — |
| **MERIT** (interior — headroom the LP declined) | 4,833 | 805.6 | **88.9 %** | 444.7 / 611.4 / 621.7 | $35.50 |

* **The min-load limb is dead.** The `nyiso_gas_commitment_bridge` floors **6.6 GWh** at this
  plant in 2024 across 29 binding hours (the keeper's own committed D-4 unit-conduct row) —
  0.7 % of (b−) at the outside, and 0 GWh inside it.
* **The capacity-scope limb is dead.** The meter exceeds the LP's 1,086.9 MW `pmax` in 53 of
  8,760 hours, for 0.3 GWh. `cc_capacity_reconcile` already set that capacity at the CAMPD
  demonstrated peak.
* **In the MERIT hours the LP dispatches 444.7 MW of a 451.9 MW mean in-the-money capacity
  (98.4 %)** — it is running essentially everything that clears the price, and 771.7 of the
  805.6 GWh sits in capacity the meter runs and the modelled price does not clear.

Re-attributing every (b−) hour against the LP's own bounds — an exact partition of the deficit
into *the extract caps below the meter* / *the headroom is in the peak band* / *the headroom is
in the econ band*:

| 2024, Cricket Valley | GWh | share |
|---|---:|---:|
| availability short (meter above the LP envelope) | 268.4 | 29.6 % |
| **peak-band short (envelope headroom sitting in the duct band)** | **512.5** | **56.6 %** |
| econ-band short | 126.6 | 14.0 % |

So (b−) is **majority an offer-position object, and the position in question is which capacity
the model puts in the duct/peak band** — not the band's price. The `CC_REGULAR` `peak`
multiplier is 2.25 and its `phys_peak` is 2.25 (the measured F-class duct ratio; markup
`max(0, 2.25 − 2.25) = 0`), so the band is already at pure physical cost and is untouchable
under rule 1 `[R-STRUCT]` ("never `phys_*`"). Nothing here proposes to move it.

## 1. The object — `cc_duct_peaking_pct` books non-duct rows' ambient derate as duct capability

`fleet.campd_bins.cc_duct_peaking_pct()` sets each CC plant's peaking share as

```
duct-fired  <=>  ANY of the plant's CC generator rows has "Duct Burners" == Y
pct_peak     =   100 * max(0, SUM_all_rows nameplate - SUM_all_rows net_summer) / SUM_all_rows nameplate
```

Two measured facts in the same filing contradict that sum.

**(a) The rows in it that cannot carry a duct burner.** A duct burner fires into the HRSG and
raises the **steam** turbine's output; EIA-860 reports the attribute at that grain. In the whole
Generator_Y operable combined-cycle population — 1,941 rows — the flag reads Y or N only on CA
and CS rows, and **every one of the 1,213 CT rows reads `X` (not applicable); `CT ∧ Y` is 0 of
1,213.** So a CT row's nameplate-vs-summer gap is site/ambient derate by construction, and the
plant-level sum books it as duct capability.

At Cricket Valley 57185 (EIA-860, applied vintage):

| rows | nameplate | net summer | winter | gap (np − summer) | Duct Burners |
|---|---:|---:|---:|---:|---|
| 3 × CA (steam) | 522.6 | 429.9 | 450.9 | **92.7** | **Y** |
| 3 × CT | 789.9 | 586.2 | 687.3 | **203.7** | **X** |
| plant | 1,312.5 | 1,016.1 | 1,138.2 | 296.4 | — |

`pct_current = 100 × 296.4 / 1312.5 = 22.6 %` → **245.64 MW of the LP's 1,086.9 MW offered at
15.78 MMBtu/MWh ($53.73/MWh) against a $35.50 mean zonal LMP.** 203.7 MW of the 296.4 — **69 %** —
sits on rows the filing itself marks as having no duct burner.

**(b) The repo already names this defect, and its existing remedy costs a DOF.**
`data/fleet/assembly.py:594` carries, verbatim: *"Cap the band at the F-class supplementary-firing
physical maximum: the raw nameplate-vs-net-summer gap **folds the ambient summer derate into the
duct band**, oversizing it for high-gap plants and dropping the price wall below the real duct
point."* The remedy in place is `cc_duct_peaking_cap_pct`, **a chosen number, set to 8.0 for PJM
and `None` for every other ISO** — which is why NYISO carries the raw gap. Carrying PJM's 8.0 to
NYISO is refused outright by rule 25 `[R-ISO-SCOPE]`, and choosing a NYISO cap would be a free
parameter selected against a residual. **This arm chooses nothing.**

**Corroboration, not ground:** row-scoping puts Cricket Valley at 7.1 %, which lands near the
F-class supplementary-firing maximum PJM's cap was set at — reached from the filing rather than
chosen. The ground is (a); this is a consistency check.

**The plant's own meter agrees.** Cricket Valley's CAMPD maximum in 2024 is 1,116.0 MW —
**0.85 × nameplate, 0.981 × winter capability** — and it occurs in **April**. On a gross-vs-net
comparison (CAMPD gross, EIA-860 net) the true ratio is lower still. A plant carrying 296 MW of
duct-fired capability would exceed its winter capability when firing it; this one never
approaches nameplate, and peaks in a cool month. That is an ambient gap, not a duct gap.

## 2. The mechanism — one registered field, ZERO free parameters

**`cc_duct_peaking_row_scoped: bool = False`** (`ScenarioConfig`, rule 24 `[R-REGISTRY]`;
default **off**, so every other ISO and every existing keeper is byte-identical). Armed, the
numerator is taken over the rows the filing flags — the denominator, the clip, the plant
selection rule and every consumer unchanged:

```
pct_peak = 100 * max(0, SUM_{rows: Duct Burners == Y} (nameplate - net_summer)) / SUM_all_rows nameplate
```

Same file, same columns, same formula, one grain finer — the grain at which the source reports
the flag. **Zero free parameters; nothing is selected, fitted, swept, or tuned; no residual
enters the construction.** It regenerates identically for a forecast year from that year's
EIA-860 (rule 13 `[R-MEASURED]`'s forward test), and it responds to changed conditions (a plant
that adds or retires duct firing moves).

**Arm = keeper recipe + exactly this one field True.** G-DELTA is computed and asserted at the
screen, not assumed.

## 3. Governance — the rule boundary, named rather than assumed

Rule 1 `[R-STRUCT]`'s carve-out lists the structural shares (`econ_low_share`, `pct_peaking`) as
**not** an authorized price-tuning channel. This arm changes what `pct_peaking` resolves to at a
CC plant, so the boundary must be stated rather than stepped over:

* The clause forbids **tuning** a structural share — selecting a value because it moves a price
  or a residual. **This arm selects no value.** The share is *computed* from EIA-860's own
  columns; the change is to which rows enter the sum, and the answer is whatever the filing says.
* The admitting rules are 14 `[R-ACCURATE]` (prefer the accurate/measured input; a construction
  that contradicts its own source is a discovered bug, not a tuning opportunity) and 13
  `[R-MEASURED]` (a reproducible physical input that regenerates forward — it does).
* **The governing precedent is this keeper's own promotion.** `unit_outage_extract_basis_share`
  (nyiso-196) likewise changed a *structural* quantity — the availability the LP is handed — by
  correcting a derivation against the extract's own columns, with zero DOF, pre-registered and
  screened by this lane without an owner ruling. This arm is the same shape on a different input.
* **What this arm is NOT:** no `offer_curve_by_group` band multiplier moves (rule 1's carve-out is
  not invoked and no owner ruling is claimed under it); no `phys_*` value moves; no adder, offset,
  haircut, proxy or cap is introduced; no cross-ISO value is transferred (rule 25 — the field is
  generic code, armed for NYISO alone, every other ISO's matrix cell enters `U` with its own
  census as the transfer question).

**Flagged to the owner court, not resolved here:** if the owner reads rule 1's `pct_peaking`
clause as covering a *derivation* repair and not only a *chosen value*, this arm needs a ruling
before promotion. It does not need one to be screened, and the screen may only kill it.

**DOF ledger:** the keeper's 13 / `n_residual` 6 carried verbatim; **no entry added.**

## 4. Screen year — **2024**, named by footprint before the screen runs

Rule 29 `[R-SCREEN]`: the screen year is the year the **mechanism's own measured footprint** is
largest, never the year the residual is largest. The footprint metric contains no meter and no
residual — it is the re-banded MW, availability-weighted, in the hours the zonal LMP sits between
the plant's econ and peak offers, i.e. the capacity-hours in which moving a MW between those two
bands can change dispatch at all:

| year | footprint, all CC plants (MWh) | footprint, `pct_peaking`-governed plants (MWh) |
|---|---:|---:|
| 2023 | 2,938,764 | 2,571,259 |
| **2024** | **3,177,375** | **2,732,133** |
| 2025 | 2,870,290 | 2,481,731 |

**Both measures name 2024 independently.** The MW re-banded is identical in all three years
(one EIA-860 applied vintage), so the year choice is made entirely by where that capacity is
price-relevant.

**Fleet footprint (2024), for the F-gates.** Re-banding moves **647.9 MW peak → econ across the
11 NYISO CC plants where `pct_peaking` actually governs the band**. It must move **nothing** at
the 20 plants whose peak band is set instead by `chp_layup_duty_curve` / `chp_layup_duty_split` /
`cc_reserve_duty_split` (those overrides are applied last and supersede `pct_peak`), and nothing
at the 9 non-duct CC plants (already 0.0). Largest movers: Cricket Valley 57185 −168.5 MW,
CPV Valley 56940 −100.2, Sithe 54547 −88.0, Astoria Energy II 57664 −87.8, Bethlehem 2539 −75.9,
Empire 56259 −48.4, Bethpage 50292 −45.4, Saranac 54574 −33.0; two plants move the other way
(Castleton 10190 +19.8, Kennedy 54114 +1.8) because their CT rows are filed with summer capacity
above nameplate, which the plant-level sum was netting against real steam-row gap.

**The direction is MIXED at the plant grain and is stated here, before the solve.** Of the
647.9 MW, the two largest movers are plants running UNDER their meters (Cricket Valley
−535 GWh, CPV Valley −628 GWh in 2024: 268.7 MW, 829 GWh of pre-solve reachable energy), while
Sithe (+1,204), Astoria II (+178) and Bethlehem (+451) are already OVER theirs (262 MW,
~430 GWh). **This arm is therefore not a "fix Cricket Valley" lever and is not offered as one** —
it is a fleet-wide construction repair whose plant-grain effects run both ways, which is the
signature of a mechanism chosen on its source rather than on a residual.

## 5. G-DRIFT — the keeper's committed bundle IS the control (rule 29(b), form 4)

`5b5af5ab..982ba9aa`, 26 non-merge commits on `src/market_sim`, `scripts/run_calibration*.py`,
`scripts/lib`, `data/raw/_validation-source`, `data/raw/reference`. **Every hunk classified INERT
for a NYISO `mode="backcast"` solve; no control solve is spent.**

**Two empirical checks, stronger than reading the diffs:**

1. **The keeper's own new mechanism reproduces to the digit at HEAD.**
   `unit_outage_derate_factors(2024, iso="NYISO", per_unit_crosswalk=True,
   merit_order_guard=True, extract_basis_share=True)` gives Cricket Valley
   `(57185, CC_REGULAR)` **mean 0.5763** — nyiso-196's committed G_ENGAGE value for that cell is
   **0.576**.
2. **A committed keeper-sha probe re-run at HEAD is byte-identical.**
   `scripts/probes/nyiso197_linden_rebuild.py --year 2024` regenerates
   `_nyiso197_linden_rebuild_2024.json` with **an empty `git diff`** — the whole fleet/offer/
   availability/delivered-gas input path (capacity ladder, heat rates, `mc_base` mean/p10/p90,
   availability mean/min, envelope, hub monthlies) reproduces exactly across `01ddbd23..HEAD`.

**Classification of the hunks the rebuilds do not reach:**

| commit / file | verdict | reason |
|---|---|---|
| `c2cb9a78` `pipeline/solve.py` | INERT | `malloc_trim()` at the P0→P1 seam; frees only allocator-free heap — LP rows, bounds and objective byte-identical |
| `1ab91a93` `runner.py` `assemble_mc` | INERT | partial-footprint carbon column fires only where a program maps membership **per zone** (PJM RGGI); NYISO's RGGI footprint is whole-ISO, so the scalar is returned as the SAME object — and the backcast runs through `run_calibration.py`, whose gate this commit copies |
| `1ab91a93` `interchange/spec.py` | INERT | `wecc_border_carbon_adder` — another ISO's branch (CAISO/WECC); no NYISO link reads it |
| `089eb401` / `SCN-WS2a` `model/lp/rows.py`, `model/lp/model.py`, `model/lp/__init__.py`, `runner.py` `_clean_region_arrays_for_year` | INERT | every changed hunk is inside `clean_region_zone_mask is not None`; gated on `miso_clean_tier_rows` (MISO) or `federal_ces_target_by_year` (unset) — a NYISO backcast composes `None` and adds no rows |
| `b1996141` `policy/carbon.py` federal-price floor | INERT | covered empirically by check 2 — `mc_base` carries `emission_rate × carbon_price` and is byte-identical |
| `4d5a59b2` `run_calibration_full.py` `_band_categorical` | INERT | output sidecar only; documented element-wise identical to the per-row construction it replaces |
| `be598ead` `data/cod_ramp.py`, `e0d55a5b` + `ddc907e1` `data/egrid_sheets.py`, `18f0ea25`, `data/outages.py`, `data/fleet/*` | INERT | covered empirically by checks 1 and 2 (COD ramp, eGRID heat rates, outage derate and fleet assembly all feed the byte-identical rebuild) |
| `9028992c` D62, `49999889` D65, `df4f055a`, `0fc2cc58`, `capacity_market.py`, `avoidable_cost_rate.py`, `datacenter.py`, `policy/clean_tiers.py`, `policy/federal_ces.py`, `scripts/lib/load_forecast/*` | INERT | forecast-only path (capacity evolution / capacity market / load forecast), default-off, and/or another ISO — a `mode="backcast"` run never enters them |
| `e299ae5d`, `3ce55518`, `d67da487`, `ee0c1676`, `069dbd9e`, `73e5351f`, `64cc970b`, `74168c9c`, `79034547`, `a66ea7c8`, `47ba0610`, `cf7170f4` | INERT | registration/CI/docs/reporting tooling and reported-only outputs; no solve-path reader |

**`ee0c1676` (R-AZ) is noted as binding on this session's registration**, not on the solve: any
run registered here is re-checked against the rule-22 tier marker at registration. This arm
solves 2023–2025 only, so the check is satisfied by the training tier.

## 6. Screen gates — STRUCTURAL, STOP-only, never gated on the target residual

The screen is **2024 only**, one arm, no control solve. Its bundle is a **throwaway diagnostic
probe**: never registered, never a keeper, never quoted as a keeper number, deleted from
`results/calibration/` before the PR merges (rule 29(c)); every number this session will ever
cite from it is recorded in the FINDING. It **may kill the arm; it can never promote it.**

**F-1 — footprint (zero LP, from the arm's rebuilt fleet).** PASS iff, against the keeper's
rebuilt 2024 fleet: the peak band falls by **647.9 ± 0.5 MW** in total; the change is confined to
**exactly** the 11 `pct_peaking`-governed plants named in §4 with each plant's ΔMW matching its
tabled value within 0.5 MW; **zero** change at all 20 override plants and all 9 non-duct plants;
and no non-CC (`CT_*`, `ST_*`, coal, nuclear, hydro, renewable, storage, import) fleet row changes
at all.

**F-2 — identity (zero LP).** PASS iff every plant's **total** LP `pmax` is unchanged
(Σ|Δpmax_plant| < 0.5 MW fleet-wide): the repair moves capacity between bands, it neither
creates nor destroys any. And G-DELTA against the keeper's `scenario_config` is **exactly**
`{cc_duct_peaking_row_scoped: False → True}`.

**S-3 — direction and magnitude bound (post-solve, meter-free).** The mechanism claims to move
capacity from a $53.73 band to a ~$29.6 band at plants where the LMP sits between them. PASS iff
(i) Cricket Valley's 2024 dispatch **rises** against the keeper's committed 2024, and (ii) the
rise is **bounded by the mechanism's own arithmetic**: `0 < Δ ≤ 622.1 GWh` (that plant's
footprint capacity-hours), and fleet-wide `0 < ΔCC ≤ 3,177.4 GWh`. A rise outside the bound means
the mechanism is not doing what its arithmetic says and the arm is killed. Reported alongside,
never gated: each moved plant's energy against the keeper payload and against its meter, and the
(b−) three-way re-attribution at Cricket Valley.

**S-4 — no load-bearing flip (STOP).** Scored the nyiso-195/196 way — every C1 class cell and the
same-weights price companions through `calibration_verdict.score_fuelmix` on the keeper's
committed payload with the screen's P1 class-energy deltas applied. **STOP iff any load-bearing
criterion (a C1 free class cell, C2, C3a, C3b) flips PASS → FAIL in 2024.** C3c is not
load-bearing and cannot stop the arm (rubric v3.3 standing rule).

**C8 / D-4 — protective (STOP).** STOP iff the arm's regenerated `legitimacy_diagnostics.json`
adds a D-4 off-window-binding failure absent from the keeper's, or pushes a material class above
its rule-20 forced-energy budget where the keeper was inside it.

**Not a gate, and deliberately so:** whether C1-2024 `CC_REGULAR` (the keeper's +3.01 TWh /
+2.5 pp against a 3.0 pp band) moves toward or away from actual. That is the target residual, and
gating on it is exactly the fitted-mechanism selection rule 1 forbids. It is **reported at full
magnitude** and it is the first number the FINDING will state.

## 7. If the screen clears

Full span `--year 2023 2024 2025` in ONE invocation and ONE bundle (rule 16 `[R-ALLYEARS]`),
registered the same session keeper or not (rule 15 `[R-DASHBOARD]`), NYISO matrix shard updated
in the same session (rule 26), the screen bundle deleted before merge (rule 29(c)). **No
promotion is proposed in this document**: whether a fleet-wide construction repair with mixed
plant-grain direction should displace a CALIBRATED keeper is a determination made on the full
span's measured result and, if §3's boundary reading requires it, on an owner ruling.

*(nyiso-198, 2026-09-06. Written and pushed BEFORE the arm was built and BEFORE any solve.)*
