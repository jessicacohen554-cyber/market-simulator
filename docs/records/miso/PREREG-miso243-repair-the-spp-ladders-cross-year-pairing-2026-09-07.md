# PREREG miso-243 — **REPAIR THE PER-YEAR SPP HOURLY LADDER'S CROSS-YEAR PAIRING.** A CONSTRUCTION defect in a committed derive, argued on rule 14 `[R-ACCURATE]` and rule 23's own construction, **never on a residual**

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item — the only lever in this lane with
a confirmed construction defect behind it.** This is a **rule-23 `[R-FROZEN-DERIVE]` re-derive
commit CITING A CONSTRUCTION DEFECT, NOT A DATA CHANGE**, and it is a solve-affecting mechanism
change, so it owes the full rule-29 `[R-SCREEN]` ladder: zero-LP phase 0 → ONE screen year named on
the mechanism's OWN measured footprint → the full span only if the screen clears a pre-registered
STRUCTURAL STOP-only gate.

**Keeper at session start: `2026-09-07-miso-233-spp-hourly`** (bundle
`results/calibration/miso233_sppseam_K`), DETERMINATION **CALIBRATED**, C3c the single ledgered
caveat, DOF ledger **41/2**. Rule 22 `[R-HOLDOUT]`: **2023–2025 only**; MISO holds no `complete`
marker and **no out-of-training year will be solved, scored or registered**. MISO carries exactly
**one** registered run (rule 15) and will still carry exactly one when this session ends.

**This document is pushed BEFORE any adjudicating quantity is computed, together with the probe
that computes them** (`scripts/probes/_miso243_spp_pairing_repair_phase0.py`). Every decision rule
below is fixed here; none may be written after seeing a number.

---

## 0. The facts this rests on, established from SOURCE and COMMITTED CONFIG before this document was written

No adjudicating quantity is used in §0. Each item is a code reading, a committed-table reading or a
predecessor's published column, and each is cited.

**F1 — THE DEFECT, read from source.**
`scripts/data/derive_miso_seam_ladders.py::derive_spp_neighbour_hourly` does

```python
work = g.join(load_spp_hub_da(hub), how="left")
```

`load_spp_hub_da()` returns a **`(year, hour)`-MultiIndexed** Series. Both callers —
the CLI (`_print_ladder(str(year), df.loc[year])`) and the rule-23 pin test
(`tests/iso/miso/test_miso_seam_ladder.py::test_registry_reproduces_the_frozen_derivation`,
`dm.derive_spp_neighbour_hourly(joined.loc[year])`) — pass **`df.loc[year]`**, whose index is
**`hour` alone**. pandas partial-joins on the shared level name, so each of the year's 8,760 MISO
rows is replicated against **all three years'** SPP hub price for that hour.
`derive_pjm_neighbour_hourly` performs **no join** (`pjm_border` is already a column of `g`).

**F2 — miso-242 CONFIRMED this on three independently refuting legs plus a control**
(`ADDENDUM-miso242-the-derive-pairs-across-years-2026-09-07.md`,
`_miso242_derive_pairing_addendum.json`): V-1 join = **26,280 rows**, blocks
{2023: 8,760, 2024: 8,760, 2025: 8,760}, `da` and flow deviation **0.0**; V-2 the **mispaired**
frame reproduces the **COMMITTED** table at **0.0000** on all 48 entries; V-3 **CONTROL**, PJM's
no-join derive reproduces its own committed table at **0.0000**; V-5 the **POOLED** forward ladder
`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED` is **correctly paired** and reproduces at **0.0000**
(`df.loc[a:b]` keeps the MultiIndex). **This session re-derives all five from scratch as its
provenance gate (§1) and does not take them on trust.**

**F3 — WHAT IS AND IS NOT CONTAMINATED, stated exactly.** The 3× replication leaves every **flow**
exceedance share untouched (replicating a sample three times does not change a share), so the
estimator's **targets** `P(flow > +mid_k)` and `P(flow < −mid_k)` are **CORRECT**. What is
contaminated is precisely one thing: **the quantile is drawn from a three-year mixture of the
spread instead of the year's own spread.**

**F4 — the committed frozen table** (`src/market_sim/model/interchange/spec.py`,
`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR`), quoted so G-T can bind on it:

| year | `import` band 1…8 | `export` band 1…8 |
|---|---|---|
| 2023 | 14.10, 32.64, 54.43, 85.36, 145.25, 185.08, 185.08, 185.08 | −4.20, −24.96, −47.33, −92.59, −241.46, −521.38, −521.38, −521.38 |
| 2024 | 14.49, 35.59, 78.29, 212.51, 290.73, 290.73, 290.73, 290.73 | −2.15, −19.39, −33.38, −42.97, −54.84, −64.17, −70.15, −83.23 |
| 2025 | 21.85, 46.55, 87.43, 169.08, 216.02, 252.76, 276.99, 345.40 | 1.04, −14.46, −29.20, −45.92, −125.99, −316.80, −515.34, −515.34 |

**F5 — THE REPAIR, fixed here in full, before any number.** It has **three parts and no fourth**:

1. **The callers pass a frame that still carries the `year` level.** `_print_ladder(str(year),
   df.loc[[year]])` in the CLI and `dm.derive_spp_neighbour_hourly(joined.loc[[year]])` in the pin
   test. `df.loc[[year]]` preserves the `(year, hour)` MultiIndex, so the join becomes the proper
   two-level join it was always written to be.
2. **A ROW-COUNT INVARIANT inside `derive_spp_neighbour_hourly`**, which raises if the join changes
   the row count. This is the **correctness pin** the mispaired path never had, and it is what
   makes the defect impossible to reintroduce from either caller (§7).
3. **The frozen table is re-derived from the correctly paired frame** and committed, together with
   the pin test's own row-count assertion.

**NOTHING ELSE MOVES.** No damping factor, no change of `K`, no re-spacing of `δ_k`, no rounding
change, no envelope change, no percentile change, no interface-limit change, no new field, no new
gate (§6). The estimator (`_derive_one` / `qq_import` / `qq_export`), the midpoint-depth grid, the
measured flow series, the anchor hub (`SPPNORTH_HUB`, named on topology) and the no-wash
reconciliation are **byte-for-byte the incumbent ones**.

**F6 — THE BASIS OF THE CASE, and it is not the residual (rules 1 / 14 / 23).** The correctly
paired frame is the **accurate** representation of the quantity the estimator's own docstring
defines — "the DA price whose exceedance duration equals the measured duration of the seam flow
exceeding the band's midpoint depth", per year. Rule 14 `[R-ACCURATE]` governs directly, and its
misalignment exception **cannot apply**: the mispaired sample is not a differently-bounded measured
series, it is the same series joined wrongly. Rule 23 `[R-FROZEN-DERIVE]` asks that a re-derive
cite its cause; the cause cited here is a **CONSTRUCTION DEFECT IN THE JOIN**, not a source-data
update and not a residual that moved. **If the repaired ladder makes any scored band worse, it
stays** (rule 1 `[R-STRUCT]`, and the owner frame the handoff carries forward verbatim: *"If
structural integrity improves but gates regress that may still be a keeper."*).

**F7 — THE ONE THING THE REPAIR MUST NOT BE ALLOWED TO BECOME.** The pairing is **not** selected by
which arm scores better. Both arms' ladders are fully determined by the estimator before any solve
runs; there is no parameter to choose. Rule 21 `[R-DOF]`: the ledger stays **41/2** and this session
introduces **zero** free parameters — the repair removes an error, it does not add a knob.

### 0a. Basis discipline (the lane's standing rule, restated and binding)

The Indiana-hub **RT** series (`_miso224_floor_anatomy_phase0.actual_zone_price`, `values="rt"`)
builds the finite-hour `ok` mask, byte-identically to miso-235…242. Every **spread** is on the
Indiana-hub **DA** (the basis the ladders were Q-Q derived against). The SPP anchor is the measured
SPP **NORTH** hub DA. They correlate only +0.402 / +0.424 / +0.553 and are never interchanged.
miso-232's measured decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by
anything here. Every decile or correlation statement below **names its basis**.

### 0b. Row sets, named in advance

* **R_D — the DERIVE row set**: `dropna` on (SPP hub DA, MISO hub DA, measured SPP seam flow) after
  the join, the row set `derive_spp_neighbour_hourly` itself uses. Every phase-0 identity and
  footprint quantity runs here.
* **R_K — the KEEPER row set**: the `ok` mask on the dense/interpolated series (miso-241/242's).
  Used only where a model-side column is read, and named wherever it is.

### 0c. G-DRIFT — **RUN AND RECORDED BEFORE ANY ARM IS SOLVED** (rule 29(b))

`git diff e852c85c HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` (keeper `git.sha` = `e852c85c`, HEAD
`60f244e3`): 50 files, +13,717 / −147. **EVERY hunk classifies INERT for a MISO backcast on the
keeper's recipe**, hunk-by-hunk:

| changed path | classification | reason |
|---|---|---|
| `config/iso_configs.py` | INERT | PJM's `retirement_sector_gate` override (capx D78-ARM, a forecast-mode capacity screen a `mode="backcast"` run never enters) + SPP's ISOConfig docstring. Another ISO's branch. |
| `config/paths.py`, `data/fuel/basis/meanzero.py` | INERT | SPP path constants added; no existing constant moved. |
| `config/constants.py` | INERT | adds `SPP_GAS_BRIDGE_*` and `ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR`; MISO's solve-surface projection reads **`moved: {}`**. |
| `config/fuel_trajectories.py` | INERT | a CAISO 2022 carbon-auction row (another ISO, and a year outside MISO's span). |
| `config/scenarios.py` | INERT | **4 new fields** (`cc_summer_derate_reconciled_basis`, `ercot_ep_gas_basis_monthly`, `ercot_zonal_spread_ep_referenced`, `spp_gas_commitment_bridge`), **all default `False` and all absent from the keeper's recipe**; **0 fields retired**. |
| `config/scenarios.py` — **capx D76** | **INERT, verified at the object level** | `capacity_screen_peak_measured_hindcast` defaults `True` at HEAD, but the keeper's config is `mode="backcast"`, **`hindcast=False`**, so (i) the runner's seam predicate `config.hindcast and not is_crossover_forward_year` never fires and (ii) `__post_init__` **coerces the field back to `False`**. Rebuilt from the committed `scenario_config`: field reads `False`, `cache_key()` = `f130587822fbf565`. |
| `config/solve_surface_declared.py` | INERT | three ERCOT/SPP declared hashes appended; append-only, MISO projection unmoved. |
| `data/eia930/actuals.py` | **INERT BY MEASUREMENT** | `_screen_fuel_spike_columns` is a genuinely **shared** seam reaching MISO's LP wind/solar bound and its C1/C4 benchmark. **Measured: 0 repaired cells for MISO in 2023, 2024 and 2025** (all `NG:` columns). This is the one hunk that could not be classified from its gate alone and it was measured, not assumed. |
| `data/fleet/arrays.py` | INERT | `_reconciled_summer_ratios` is gated on `config.cc_summer_derate_reconciled_basis` (default `False`, absent from the recipe). |
| `data/floor_mechanisms.py` | INERT | a new mechanism id (24, SPP bridge) with `{"spp_gas_commitment_bridge": False}`; additive. |
| `data/renewables.py` | INERT | MISO's membership in `_UNCURTAILED_FALLBACK_ISOS` / `_WIND_ZONE_SHAPE_ISOS` is **unchanged** (only SPP added), and `_reference_curtailment_rate` **returns on MISO's own branch before** the new provider registry is consulted. |
| `data/transmission_expansion.py` | INERT | SPP's limit vintage 2025 → 2026. |
| `data/fuel/basis/ercot.py` | INERT | ERCOT-only. |
| `model/interchange/spec.py` | INERT | additions are **SPP's own** `NeighborInterface` rows (`MISO_West` / `MISO_South` as seen from SPP) and CAISO 2022 rows. **The MISO seam ladder tables are untouched** — `git diff` over `MISO_SEAM_LADDER*` / `MISO_SEAM_DIBA` / `SEAM_FLOW_TRANCHES` is **empty**. |
| `model/reserves/spec.py` | INERT | SPP's published CR demand curve (`iso == "SPP"` branch) + an ERCOT measured-requirement reader. |
| `pipeline/backcast_config.py` | INERT | `_SPP_OFFER_CURVE` added; **no MISO line changed**. |
| `pipeline/commitment.py`, `pipeline/year.py`, `runner.py`, `scripts/run_calibration*.py` | INERT | the SPP gas bridge. `build_spp_gas_bridge_p1_prep` returns `None` unless `config.spp_gas_commitment_bridge and iso == "SPP"`; the new CLI parameters default `None`. |
| `pipeline/kwargs.py` | INERT | an `elif iso == "SPP"` logging branch. |
| `pipeline/persist.py` | INERT | records `cache_key_path_roots` / `MARKET_SIM_DATA_ROOT` in `run_config.json`; **not an input to any key** and read by nothing in the solve. |
| `results/cache.py` | INERT | docstring (the D76 epoch narrative). |
| `results/scarcity.py` | INERT | a new ERCOT-only `ercot_as_measured_requirement_mw`. |
| `scripts/lib/key_provenance.py` | INERT | new file, **imported by nothing** under `src/market_sim` or either calibration CLI. |
| `scripts/lib/confirmed_retirements/spp.py`, `scripts/lib/transmission_expansion/spp.py` | INERT | SPP's own registry modules. |
| `data/raw/_validation-source/calibration_reference.json` | INERT | **only an `SPP` block added**; every pre-existing ISO block hashes byte-identically (`isos` and `egrid_benchmark` changed sub-keys: **none**). |
| `data/raw/_validation-source/actual_lmp.json` | INERT | **only `SPP` added**; zero changed keys. |
| other `data/raw` paths | INERT | SPP renewable-capacity / LMP / capacity-actuals files, a CAISO WECC intertie parquet and a CAISO 2022 demand CSV — another ISO's inputs. |

**Corroboration, independent of the hunk reading:** `surface_stamp("MISO", ScenarioConfig(mode="backcast"))`
at HEAD reads fingerprint **`8ee657ee4c7c49b0`**, **`rows: 208`**, **`moved: {}`**, **`epochs: []`** —
**identical to the fingerprint the keeper's `run_config.json` recorded at `e852c85c`.**

**CONCLUSION: G-CTRL FORM 4 IS VALID. The keeper's COMMITTED bundle IS the control, and NO CONTROL
SOLVE IS SPENT.** *(Disclosed against interest: **this session's own derive change is a LIVE hunk
by construction** — it moves `δ_k`, therefore the LP. That is exactly what the screen exists to
measure, and it is why the screen arm is solved at all.)*

---

## 1. THE PROVENANCE GATE — six legs. If ANY leg fails the instrument is BROKEN and no adjudicating quantity is read

Each leg reproduces a predecessor's published quantity **in the predecessor's own metric, reading
its estimator rather than its label**, on this session's independent code path. **Every reference
value is restated inside the probe, so each leg binds even if the predecessor's JSON artifact is
missing.**

| leg | what it reproduces | bar |
|---|---|---|
| **G-T** | the committed SPP + PJM hourly ladder tuples equal §0 F4's quotation, **and** import is non-decreasing / export non-increasing in `k`, both seams, all years | exact equality; **0** monotonicity violations |
| **G-V1** | miso-242's V-1: the **mispaired** join returns exactly **26,280** rows with blocks {2023: 8,760, 2024: 8,760, 2025: 8,760} and `da`/flow deviation **0.0** across the three hub-year blocks | exact row count; **0.0** |
| **G-V2** | miso-242's V-2: the **mispaired** frame reproduces the **COMMITTED** table in all **48** entries | ≤ **0.005** on all 48 |
| **G-V3** *(CONTROL)* | miso-242's V-3: PJM's **no-join** derive reproduces `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR` in all **48** entries | ≤ **0.005** on all 48 |
| **G-V5** | miso-242's V-5: the **POOLED** forward ladder is correctly paired and reproduces the committed pooled tuple in all **16** entries | ≤ **0.005** on all 16 |
| **G-DOC** | the derive script's **own docstring statistic** `corr(measured SPP seam flow, MISO DA − SPP hub DA)` = **+0.041 / −0.020 / +0.050** | ≤ **0.002** |

**G-V2 and G-V3 are jointly falsifiable and each can kill the diagnosis**: if the committed table
does *not* come from the mispaired path, or if PJM's no-join derive *also* fails to reproduce, then
the defect is not what §0 F1 says and **this session stops and publishes that instead**.

---

## 2. PHASE 0 — the zero-LP legs, all declared here with their bars BEFORE the probe runs

### 2.1 P-1 — **THE FALSIFIABLE IDENTITY LEG, AND IT CAN FAIL.** Does the repair close the Q-Q identity?

The estimator asserts an identity (miso-242 PREREG §0 F5): on the derive's own spread, the dead
band `[δ_1^export, δ_1^import]` captures `P(|flow| ≤ mid_1)` **by construction**. Define on **R_D**

* `Z_target` := `P(|measured SPP net flow| ≤ 250 MW)` — measured flow alone, no price;
* `Z_derive^committed` := `P(δ_1^exp ≤ (miso_da − spp_hub) ≤ δ_1^imp)` on the **committed** ladder;
* `Z_derive^repaired` := the same on the **correctly paired** ladder.

**Decision rule, fixed here.** `|Z_derive^repaired − Z_target| ≤ 0.005` in **all three years** ⇒
**IDENTITY RESTORED**. Otherwise ⇒ **IDENTITY NOT RESTORED**, which is a result **against** this
session's own hypothesis: it would mean the pairing is not the whole cause, it would be published
at full magnitude as this session's headline, and **the repair would not proceed to a screen**.

Bar justification, fixed before the numbers: the committed table is rounded to 2 dp and the
same-seam no-wash clamp may move an export band; 0.005 is **4× tighter than the ≤ 0.020 bar
miso-242's Q-A used**, so this leg cannot pass on slack. **Dead-band membership is evaluated in the
instrument's OWN two operand forms** (miso-242's §0a repair — the import leg a subtraction, the
export leg an addition), never in an algebraic rearrangement of them.

### 2.2 P-2 — **THE BYTE-IDENTITY LEG.** The caller change must move NOTHING ELSE

Passing `df.loc[[year]]` instead of `df.loc[year]` reaches `derive()`, `derive_pjm_neighbour()`,
`derive_pjm_neighbour_hourly()` and `offline_score()` as well. All four are column-only, so all four
**must** be unchanged.

**Decision rule, fixed here.** Under the repaired caller, the three incumbent registry ladders
(PJM / SPP / South), the Manitoba ladder, `derive_pjm_neighbour` and `derive_pjm_neighbour_hourly`
reproduce their committed values in **every** entry, all years. **Bar: ≤ 0.005 on every entry, zero
exceptions.** A failure here means the caller change is not confined and **the repair does not
proceed**.

### 2.3 P-3 — **THE MECHANISM'S OWN MEASURED FOOTPRINT, and the SCREEN-YEAR RULE, both fixed BEFORE the number exists**

**The footprint statistic**, declared here: on **R_D**, using the derive's own spread and **zero
model input**,

```
F(year) := share of R_D rows whose SPP band-count vector (n_import, n_export)
           DIFFERS between the committed ladder and the repaired ladder
```

**THE SCREEN-YEAR RULE, FIXED HERE:** the screen year is **`argmax_year F(year)`**; ties break to
the **earliest** year. This is the year the mechanism's own measured footprint is **largest**.

**It is a FOOTPRINT choice and it is NOT a residual choice**, and the distinction is the point: `F`
is computed from the measured MISO DA spread, the measured SPP hub DA and the two ladders alone. It
contains **no model output, no scored criterion, no gate and no residual**, so it cannot be the
year "with the biggest residual" that rule 29 forbids. **The chosen year is published in a pushed
ADDENDUM before the screen solve starts** (§3).

*Recorded for transparency and **NOT used as the rule**: miso-242 §5a reports 2023 as the year the
mixture displaced its table most (`|Z_derive − Z_target|` **0.0395** vs 0.0144 / 0.0089). Those
numbers are **UN-TARGETABLE** by the handoff's own instruction, this session **derives `F`
independently**, and if `F` names a different year **`F` wins** — the rule was fixed before either
number was computed.*

### 2.4 P-4 — **THE PRE-SOLVE PREDICTION**, computed BEFORE the screen and used to set the screen's own bars

Predict, per year, the **signed** change in the SPP seam's mean in-merit import bands and export
bands, and the implied **signed** change in mean net seam flow

```
Δq̂ = step × (Δn̄_import − Δn̄_export)  MW,      step = interface_limit_mw / SEAM_FLOW_TRANCHES = 500 MW
```

**On TWO bases, both declared here, and the one that sets G-3's bar is named now:**

* **the MODEL basis (R_K)** — `x = p_bus`, the keeper's committed `MISO_external` P1 price, which
  is the operand the LP actually clears the bands against. **THIS ONE SETS G-3's BAR.**
* **the DERIVE basis (R_D)** — `x = MISO hub DA`, the estimator's own operand. **Reported
  alongside**, never a bar, so the two are visible rather than conflated.

**Stated before the number, because it bounds what G-3 can mean:** the realized seam flow is
`min(envelope, n × w)`, so the measured `(month × hod)` ceiling can only **clip** the band
response. `Δq̂` is therefore an **upper bound in magnitude** on the solved change, and the binding
side of G-3's window is its **lower** limit. miso-241 §3's SPP `ceiling_active_share`
(0.2572 / 0.2952 / 0.2474) is the reason the window is a factor of 4 rather than something tighter,
and that reason is fixed here rather than after seeing the solve.

### 2.5 What phase 0 does NOT do

It does not solve, does not register, does not move a cell verdict, and **does not commit the
repair**. The repair is applied to the tree only **after** P-1 and P-2 both pass; if either fails,
the tree is left exactly as found and the failure is the session's result.

---

## 3. THE SCREEN — ONE year, and its gate is STRUCTURAL, STOP-ONLY, and NEVER the target residual

The screen year is `argmax_year F(year)` (§2.3), **published in a pushed ADDENDUM together with
G-2's and G-3's numeric bars — which are derived from P-4's pre-solve prediction — BEFORE the solve
is launched.** Control = **the keeper's committed bundle** (G-CTRL form 4, valid per §0c); **no
control solve is spent.**

**The four gates, in the miso-233 template. All four are STOP gates: they may KILL the arm, they may
NEVER promote it.**

| gate | what it asks | bar |
|---|---|---|
| **G-1 CONFINEMENT** | the arm introduces no infeasibility pressure and does not disturb must-take | zone **slack** and **dump** MWh **not above** the keeper's screen-year values (tolerance 1e-6 relative); wind + solar + nuclear + hydro delivered energy within **0.5 %** |
| **G-2 FOOTPRINT** | the response is **confined to the object the mechanism touches** | the **SPP** seam's annual gross-flow change is **strictly larger in magnitude** than each of the PJM, South and Manitoba seams' own changes; and total ISO load-serving energy moves ≤ **0.5 %** |
| **G-3 DIRECTION & ORDER OF MAGNITUDE** | the dispatch response has the **sign** P-4 predicts and is within a factor of **4** of `Δq̂` | sign match **required**; `0.25 ≤ Δq_solved / Δq̂ ≤ 4.0` |
| **G-4 COLLATERAL** | no non-target load-bearing criterion flips PASS → FAIL | **zero** flips, via `scripts/screen_collateral_gate.py --bundle <screen> --keeper-run-id 2026-09-07-miso-233-spp-hourly` |

**NOT GATED, REPORTED ONLY, AND NAMED HERE SO THE DISTINCTION IS ON RECORD BEFORE THE SOLVE:** the
measured-price **decile slope** (basis: named on every statement), the **committed-solve system
interchange ratio** 1.99 / 3.12 / 5.56×, `corr(imports, own price)`, C1/C2/C3a/C3b/C3c/C4 band
values, and every other residual. **A screen that reads "did the target residual improve" is the
fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, done one year at a time, and this session
does not run one.**

**A screen that kills the arm is the session's result**, published at full magnitude, and the
remaining two years are **never spent**.

---

## 4. THE FULL SPAN, and the promotion rule — fixed here, for every outcome

If and only if all four gates clear: `replay_keeper.py results/calibration/miso233_sppseam_K
--years 2023 2024 2025` in **ONE invocation** producing **ONE bundle** (rule 16 `[R-ALLYEARS]`),
years **sequential** (rule 12 `[R-PARALLEL]`), with the keeper's
`calibration_attestation.json` carried forward and its `governance.attested_by` + `disclosures`
rewritten (else C6 reads UNATTESTED and the determination is NOT-YET for that reason alone).

**The promotion rule, fixed here (miso-227), and the owner frame it sits inside:**

* Determination **CALIBRATED** or **CALIBRATED-WITH-CAVEATS** ⇒ **PROMOTE**.
* A **load-bearing NOT-YET** ⇒ **REPORT AND ESCALATE**, never decertify unilaterally.
* **Every band is published at full magnitude either way.** *"If structural integrity improves but
  gates regress that may still be a keeper"* — rule 1 already says a structurally-correct mechanism
  is never judged by the residual and is never reverted because the residual didn't move. **A
  regressed band is therefore NOT a reason to revert this repair**, and a regressed band is
  likewise **not** disguised: it is named on the determination basis and in the matrix cell.

**Rule 15 `[R-DASHBOARD]`:** whatever the outcome, the finished run is registered and the superseded
run pruned, so MISO still carries exactly one registered run. **Rule 31 `[R-RETAIN]`: no solved
bundle is deleted in this session under any circumstances** — screen and full span alike are
`.gitignore`d, kept on local disk, and the promotion question is surfaced explicitly in the final
report with the statement that they will not survive the container.

---

## 5. What this session may NOT do — fixed here, for EVERY outcome

### 5.1 Nothing measured here is a target

**Every number this session produces is UN-TARGETABLE.** No successor may size, scale, tune or
select any mechanism to land on any of them. miso-242 §5a's correctly-paired values
(import 13.44 / 17.26 / 18.58, export −2.39 / +1.44 / −2.37) are **reported for scoping by the
handoff and are un-targetable**; this session **derives its own** and, if they differ, publishes the
difference rather than reconciling to them.

### 5.2 The standing freezes, restated in advance and binding on every branch

**NO damping factor, NO change of `K`, NO re-spacing of `δ_k`, NO rounding change, NO envelope
change, NO percentile change, NO interface-limit change, NO new `ScenarioConfig` field, NO new
gate.** The **PJM** `δ_k` ladder stays derived, frozen and pinned by test; the measured
`(month × hod)` envelope, its p90 and every interface limit stay untouched (rule 14). The **POOLED**
forward ladder is **already correctly paired** (G-V5) and is **not touched** — rule 13's forward
story is intact and only the per-year backcast table is repaired.

### 5.3 No re-testing of settled adjudications (rule 28(a))

Queue item 1's **external-bus-price half** stays **CLOSED**; item 1's idle-seam question stays
**ANSWERED AND DECOMPOSED** and is not re-measured; the **merit test's sign and basis** stay
**REFUTED as a defect** (corr +0.7946 / +0.6989 / +0.7434); the **PJM/SPP idle contrast** stays a
**measured-record** fact; the **SPP quantity-side charter** stays **REFUSED — NO DOF-FREE FORM**
(miso-241 §5, C1–C7) and the C7 census is **not re-run**; the per-seam external-node split stays
**REFUSED at zero LP**; saturation stays **REFUTED**; miso-239 Q-A **MIXED** / Q-C **SURVIVES**;
miso-240 Q-B **UNRESOLVED**; the `(month × hod)` template hypothesis stays **REMOVED**; the PJM
import/export asymmetry stays **CLOSED FOR PJM**; South's neighbour-state route stays **CLOSED**;
`miso_manitoba_seam` stays **CLOSED as already-armed**; `internal_congestion_split` **G**;
`vre_reference_rate_curtailment_grossup` **K**; `measured_interface_limits` **R**;
`miso_rdt_measured_limit` **R**; `m2m_seam_entitlement_cap` **G**; `miso_south_firm_export_block`
**G**; `miso_south_export_ladder_rt_tail` **R**; `miso_south_gas_delivered_cost_basis` **R**.

### 5.4 C3c

**THERE IS NO RUBRIC FAILURE ANYWHERE IN THE PROGRAM AND THIS SESSION DOES NOT INVENT ONE.** C3c is
MISO's single ledgered, non-downgrading caveat and is **not** this session's object. It opens only
by a new admissible measured identification under its own charter **plus an owner ruling**, never
by an offer adder, an ORDC offset, a scarcity multiplier or any level tuned to the tail. **No such
thing is proposed, computed or armed here.**

### 5.5 Disclosure duties accepted in advance

If this session's own gate or instrument fails, the failure is published **first, at full
magnitude**; any repair is declared in a **pushed ADDENDUM before the repaired numbers exist**; **no
bar is moved**; and a repair that makes a gate **stricter** is preferred. Any quantity computed
post-hoc is **labelled POST-HOC** and shown arithmetically to move nothing. A non-gated leg that
would have read differently, a statistic that is not the predecessor's, and any advance suspicion
this session raises that is later refuted **or confirmed**, are all disclosed against interest.

---

## 6. Rule 19 `[R-ONE-MECH]` — the enumeration, written before the outcome

What already sets the MISO–SPP seam on the keeper: the armed **hourly SPP neighbour anchor**
(`miso_seam_neighbour_hourly_spp`, band `k` at `spp_hub(t) + δ_k`, import and export alike); the
**frozen Q-Q `δ_k` ladders** (`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR` — **the object this
session repairs**); the **incumbent MISO-hub Q-Q ladder** it displaces (`MISO_SEAM_LADDER_BY_YEAR
["SPP"]`, an alternative, never stacked); the **measured `(month × hod)` deliverability envelope**
in both directions under the merit-order waterfall; the seam's **4,000 MW** interface limit and its
eight **500 MW** bands; the `MISO_external` border-link TTCs; the **8,700 MW**
`MISO_simultaneous_import` SIL; and the published **CIL/CEL** deliverability groups.

**NOTHING IS ADDED.** This session **repairs one existing object in place** — it replaces the
mispaired table with the correctly paired one — so nothing stacks, nothing new must be reconciled,
and the mechanism count is unchanged.

---

## 7. The rule-23 pin test — repaired WITH the derive, in the same PR, and made STRICTER

`tests/iso/miso/test_miso_seam_ladder.py::test_registry_reproduces_the_frozen_derivation` invokes
`dm.derive_spp_neighbour_hourly(joined.loc[year])` — **the same defective call** — so it compares
the committed table against the same mispaired output and passes. It is a **consistency** pin, not a
**correctness** pin, and miso-242 §7 recorded that as naming no defect in the test.

This session repairs it **in the same PR as the derive** (it would otherwise fail) and makes it
**stricter**, never looser:

1. it passes `joined.loc[[year]]`, the correctly paired frame;
2. it **additionally asserts the join's ROW COUNT**, which is the assertion that would have caught
   this defect — and the same invariant is enforced **inside the derive itself** (§0 F5 part 2), so
   the defect cannot be reintroduced from any caller, tested or not.

**No `atol` is loosened and no assertion is removed.**

---

## 8. Non-claims, fixed in advance

1. **The forward ladder is not implicated and is not touched** (G-V5). Rule 13's forward story is
   intact; only the per-year backcast table is repaired.
2. **PJM is clean on every leg and no PJM object is touched or re-tested.**
3. **This repair does not close the structural item rule 1 names.** The model's SPP seam is
   0.70–0.79 spread-correlated while the measured one is +0.041 / −0.020 / +0.050; the seam being
   idle is not the anomaly, its being spread-driven is. A correctly paired ladder does **not**
   change that, and this session claims no such thing.
4. **MISO has no failing gate**, this session does not invent one, and nothing here trades a
   passing gate for anything.
5. **The screen is a throwaway diagnostic probe** (rule 29 clause 2): never registered, never a
   keeper, never quoted as a keeper number, and its year is re-solved inside the full bundle.
6. **No 2019–2022 or H1-2026 year is solved, scored or registered**, and MISO's `complete` /
   `final` markers are not sought, asserted or implied.
7. **Every number miso-242 published is un-targetable and none of it is a bar here.**
