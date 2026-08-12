# PREREG — miso-153 Phase 0: WHY does MISO keep cheap capacity available at its summer peak?

**Session** miso-153 · **ISO** MISO · **Date** 2026-08-12 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), UNCHANGED ·
**Model** `claude-opus-5` (rule 27 `[R-PUSH]`: this lane writes core
infrastructure; Sonnet ineligible).

**Pushed BEFORE any adjudicating statistic is computed.** Everything already
looked at is disclosed in §10.

**Rule 22 `[R-HOLDOUT]`:** MISO holds NO marker. Every statistic below is
computed on **2023 / 2024 / 2025 only**. No holdout year is read, solved or
scored anywhere in this session.

---

## 0. Re-verification of the keeper (committed artifacts, stdlib, pre-venv)

`scripts/calibration_verdict.py --run-id 2026-08-09-miso-148-basis-aware`
reproduces the expected §0 exactly:

* **NOT-YET**, failing set **{C3a, C3b}** (`price_mean`, `price_shape`)
* C3a-2025 **−15.6 %**; C3b-2025 NRMSE **0.212**
* C3c **ledgered, 1/1 slot SPENT** (CAVEAT rows 2023/2024/2025)
* C6 PASS; C8 PASS with ST_GAS grounded **34.1 / 35.8 / 48.4 %** and
  CT_PEAKER-2023 **16.8 %**
* C1 PASS (D-10 free 12/12), C2 PASS, C4 PASS

---

## 1. The object

From `DIAGNOSIS-miso152-c3a-lives-in-june-july-2026-08-11.md` (read, **not**
re-derived — DO-NOT-REDO): C3a is not a uniform level offset. 2025's miss
concentrates in **June (−27.9 %) and July (−30.9 %)** — 17 % of hours carrying
46 % of the annual mean gap. The model's Jun+Jul p99 ($59.1) and max ($75.1)
sit **below its own rest-of-year** p99 ($71.4) / max ($100.8): *the model forms
no summer peak*. Demand is exonerated (model peaks in July, 118.7 GW; top-200
demand hours 100 % summer). The realized price-vs-demand slope is
**$0.35/MWh per GW**.

**The question this phase answers, and the only one:** *why does the model
still have cheap capacity available at the top of MISO's summer load?* Phase 0
selects a lever; it does not test one.

**Phase 0 takes NO verdict on any mechanism and promotes nothing.** No run is
produced, so rule 15 is not engaged by this phase. The Phase-1 lever gets its
**own** PREREG (PREREG-B), pushed before its solve.

**Interpretive caution, carried forward (rule 1 `[R-STRUCT]`):** the $0.35/GW
realized price-vs-load slope and miso-145's $73.4591/GW fleet-cumulative
**offer** slope are different objects on different axes. Suggestive, **not**
evidence. They are never quoted as a matched pair in this session.

**Not chartered, and not opened here** (owner decision required): the
**across-unit dispersion** object (miso-151 G-5), and the **CT_PEAKER
fill-order** successor (miso-152). If D-1/D-3 point at either, this session
**puts it to the owner** rather than opening it (§6 branches P-C / P-E).

---

## 2. Construction (one probe, no LP)

`scripts/probes/_miso153_summer_cushion.py`. The fleet is assembled through the
**production chain**, reusing miso-134's `build_year` verbatim: fleet →
`generators_to_fleet_arrays` → `resolve_fuel_prices` → `assemble_mc` →
`apply_coal_tranches` → `apply_gas_offer_margin`. Prices, demand and dispatch
come from the keeper's **own committed** `hourly/` sidecars.

The LP's generator bound is `min_gen ≤ P ≤ pmax × availability`
(`model/commitment.py:1601`), so **available MW ≡ `pmax × availability`** —
the quantity the LP itself sees, not a proxy.

Carry zones for every price/demand aggregate: **MISO-East, MISO-Illinois,
MISO-Indiana, MISO-Plains, MISO-South, MISO-West** (6). `MISO_external` and
`MISO_external_South` are **import nodes** and are excluded from price
aggregates — and *included* only in the import measurement.

**Peak window (fixed here, before measurement):** the **top-200 hours of model
ISO demand** in each year, matching the miso-152 addendum's own construction so
the two are comparable. Jun+Jul is the secondary window, likewise fixed.

---

## 3. The four statistics, their gating status and their two-sided priors

All four are computed for **2023, 2024 and 2025**. 2023 currently **PASSES**
C3a at −0.3 % and is carried throughout as an **against-interest bound**: a
mechanism that produces the 2025 summer peak by also inflating 2023 is a
**regression**, not a fix, and §6 refuses it.

### D-1 SUMMER CUSHION — *gated on T-6 only; selects a branch, adjudicates nothing*

Statistic: at the top-200 model-demand hours, per class and in total for the
dispatchable thermal set {CC_REGULAR, CC_CHP, CT_PEAKER, CT_CHP, ST_GAS,
ST_CHP, COAL_BIT, COAL_PRB, COAL_LIGNITE}: available `Σ pmax×availability`,
dispatched `Σ mw`, and **idle headroom** = available − dispatched, in GW and as
a share of available.

**Two-sided prior (2025):** idle thermal headroom **12–28 GW**, i.e. **12–25 %**
of available thermal.

* **< 8 GW / < 8 %** — surprise LOW. The stack is genuinely tight at peak; a
  "too much capacity" story is **refuted** and the defect lives in the *offer
  level of the marginal band*, not in availability. → branch **P-A**.
* **> 32 GW / > 28 %** — surprise HIGH. → branch **P-B**.

### D-2 AVAILABILITY SEASONALITY — *gated on T-6; its "win" is a STOP*

Statistic: cap-weighted mean availability by class by month; **Jun+Jul minus
annual mean, in percentage points**, per class; and the absolute Jun+Jul level.

**Two-sided prior:** Jun+Jul availability sits **+0 to +8 pp ABOVE** the annual
mean for CC and coal — real MISO maintenance is spring/fall, so a summer *rise*
is correct behaviour, not a bug.

* **Jun+Jul more than 5 pp BELOW annual** — the overlay is mis-seasoned.
* **Jun+Jul absolute > 0.93 for CC/coal** — effectively no summer forced-outage
  derate at all (MISO's extract is **un-re-tuned, X_cc = 0.240**).

**Either surprise is an ESCALATION, not a lever.** Per the session charter,
re-tuning MISO's outage extract needs a **cross-ISO charter this lane cannot
self-authorize**. If D-2 fires, this session **STOPS on that item and reports
D-2's numbers to the owner** (branch **P-D**). It does not re-tune, and does not
quietly route around it into a different lever that would mask it.

### D-3 MARGINAL IDENTITY — *gated on T-6; selects a branch*

Statistic: at the top-200 demand hours, the **price-setting band** — the
class+band suffix whose effective marginal cost is the greatest mc **at or
below** the hour's zonal price — as a cap-weighted census over hours and zones.
Reported alongside: the mc distribution of **idle** capacity in the $0–20/MWh
band immediately above the clearing price (what the price would have had to
reach to bring it in).

**Two-sided prior (2025):** CC_REGULAR econ bands set price in **45–75 %** of
top-200 hours; CT_PEAKER in **10–35 %**.

* **CT_PEAKER > 50 %** — merit order already reaches peakers at peak, so the
  defect is the CT *offer level*, i.e. the **uncharted** miso-152 CT successor.
  → branch **P-E**, to the owner.
* **Coal > 30 %** — the coal ladder is the top of the summer stack. → **P-B**.

### D-4 RESERVE BINDING — *descriptive, ungated*

Read `hourly/reserve_family_<year>.parquet` — the only artifact in which a
locational family's binding is observable (`system.reserve_price` is the
cross-family SUM broadcast identically to every zone). Three families exist:
`miso_rbdc` (all zones), `miso_subregional_or_midwest` (5 Midwest zones),
`miso_zonal_or_miso_south` (MISO-South). Per family: count of Jun+Jul hours
with `dual` > $0.01 and with `shortfall_mw` > 0; mean/max of each; and the
**rest-of-year contrast**.

**Two-sided prior:** families bind in **0–5 %** of Jun+Jul hours with
essentially zero shortfall.

* **> 20 % of Jun+Jul hours bind** — reserves are already active in summer; a
  "reserves never bind" lever is **refuted** before it is proposed.
* **0 binding hours in every family all year** — reserve co-optimization is
  inert in MISO entirely, itself a named candidate. → branch **P-B**.

### IMPORTS AT PEAK — *confirmatory, ungated (charter: confirm, do not assume)*

`docs/multi-iso/miso-import-starvation-rootcause-2026-07.md` reports the model
**under**-importing — the wrong sign to cause a low-price defect. Confirmed
here **at peak hours specifically** before being dismissed: model `import`-class
MW at the top-200 hours, against its own annual mean and against the assembled
import-node capability.

**Two-sided prior:** peak imports are **at or near** their capability (headroom
exhausted), so imports cannot be the cheap cushion.

* **Peak imports materially ABOVE the annual mean with headroom remaining** —
  the model is buying cheap energy at peak and the starvation finding's sign
  **does not carry to peak hours**. That flips imports into a live candidate and
  is reported at full magnitude even though it contradicts the prior. → **P-B**.

---

## 4. What would make me WRONG about the whole framing

Stated in advance so it cannot be rationalised afterwards. The framing —
"too much cheap capacity is available at peak" — is **refuted** if **all** of:

1. D-1 idle thermal headroom at the top-200 hours is **< 8 GW**; and
2. D-3 shows the price-setting band is already the **most expensive** band with
   material capacity (nothing cheap left above the clearing price); and
3. D-2 shows summer availability correctly derated.

In that case the summer defect is **not** a cushion at all — it is the *level of
the whole offer surface*, and Phase 1 must not spend itself on an availability
or merit-order lever. This outcome is branch **P-A** and is reported as
prominently as any other.

---

## 5. Traps, each with its counter-measurement

| # | Trap | Counter-measurement (reported in both branches) |
|---|---|---|
| **T-1** | `_miso134`'s `BUNDLE` is **hard-wired to `miso132_ccmin_B`** — inheriting it silently screens the wrong keeper. | Repoint `_m134.BUNDLE` to `miso148_basis_B` at import and **assert** `run_config.json` exists. Report how many `run_config.scenario_config` keys matched `ScenarioConfig` fields and how many were dropped. |
| **T-2** | A silent `getattr(obj, field, default)` on the offer path **IS** the bug; `pmax` (FleetArrays) vs `pmax_mw` (Generator) are different names. | All offer-path fields read **directly**. A grep asserting **zero** 3-argument `getattr(` in the probe is run and its result reported. |
| **T-3** | The econ block is smoothed into `offer_curve_smoothing_n` sub-tranches (`econc00..econc05`); collapsing one-per-band keeps only the **dearest** and yields a spurious exact `0.0` on a healthy-looking run. | Dump the **full** band-suffix inventory (counts + capacity) before any aggregation. Assert Σ tranche `pmax` by class reconciles to assembled class capacity. **Disbelieve clean zeros** — any exact 0.0 is re-derived a second way before it is reported. |
| **T-4** | A `SimpleNamespace(pmax=…)` fixture encodes the same wrong field name as the code and cannot fail. | The probe's self-test builds its fixture from the **production types** (`generators_to_fleet_arrays`), per `tests/test_miso152_fillorder.py`. |
| **T-5** | `MISO_external` / `MISO_external_South` are **import nodes**; including them corrupts any price aggregate. | Carry-zone count asserted **== 6**; the import nodes appear only in the import statistic. |
| **T-6** | **(GATING)** The reconstruction may simply be wrong — wrong config, wrong overlay, wrong vintage — and a wrong reconstruction produces a confident wrong answer. | **Feasibility check:** the keeper's own committed dispatch must be **≤** reconstructed available MW, per class, at every top-200 hour. **Bar: violations ≤ 1 % of (class × hour) cells AND max violation ≤ 2 % of that class's assembled capacity.** **If the bar fails, D-1 and D-3 are DESCRIPTIVE ONLY** (branch **P-D**) and **no lever is selected from them.** Magnitude reported in both branches. |
| **T-7** | **Dual-fuel re-attribution**: a gas unit switched to backup oil is relabelled `klass="oil"` in `class_hourly` although the LP dispatched it on the **gas** tranche (`run_calibration_full.py:410-422`). This makes gas look over-available and `oil` look infeasible. | Measure `oil`-class MW at the top-200 hours. If **> 0.5 %** of thermal dispatch, pool {gas classes + oil} for the T-6 check and **say so explicitly**. |
| **T-8** | `wind`/`solar` are separate LP variables and `biomass`/`hydro`/`OTHER` are **must-run pseudo-classes netted out of LP demand** — none carries `pmax×availability` in `arrays`. Treating them as fleet classes fabricates headroom. | D-1/T-6 restricted to classes **actually present in the assembled fleet**; the excluded `class_hourly` classes and their dispatch share are listed. |
| **T-9** | COAL is split by `_coal_supply_class(plant_code)` into COAL_BIT/PRB/LIGNITE in `class_hourly`, but the fleet carries `plant_group == "COAL"`. Naive joining loses all coal. | The probe applies the **same** `coal_supply_class(plant_code)` split to the assembled fleet, and asserts the resulting class set covers the `class_hourly` coal classes. |

**A gate bar of "bit-identical" on floating-point data is unsatisfiable.** T-6
uses an explicit tolerance and its **magnitude is always reported**, in both
branches.

---

## 6. Pre-committed branches (fixed before measurement)

| Branch | Trigger | Phase-1 consequence |
|---|---|---|
| **P-A** | §4 refutation set (D-1 < 8 GW **and** D-3 nothing cheap above clearing **and** D-2 correctly derated) | The cushion framing is **refuted**. No availability/merit lever. Report the refutation; take the *offer-surface level* question to the owner rather than self-authorizing it (it neighbours the uncharted across-unit object). |
| **P-B** | A large cushion (D-1 high), or coal-topped stack (D-3), or wholly inert reserves (D-4), or over-importing at peak | **One** lever named from the item that fired, PREREG-B written with a two-sided prior and kill gates, solved `--year 2023 2024 2025` in **one** invocation against a **same-HEAD zero-delta control**, both registered (rule 15). |
| **P-C** | D-1/D-3 point at the **across-unit dispersion** object (miso-151 G-5) | **STOP. Put it to the owner.** Not self-authorized. |
| **P-D** | T-6 bar fails, **or** D-2 fires (mis-seasoned or un-derated summer availability) | **STOP on that item.** D-1/D-3 descriptive only. Escalate to the owner with D-2's numbers; **do not re-tune** MISO's outage extract inside this lane. |
| **P-E** | D-3 shows CT_PEAKER already price-setting > 50 % at peak | The object is the **uncharted CT offer-level successor**. **Put it to the owner.** |

**No branch permits bundling two mechanisms into one solve.** If more than one
branch fires, the session reports all of them and takes the **most restrictive**
(P-D > P-C/P-E > P-A > P-B).

**Against-interest bound, binding on Phase 1:** 2023 passes C3a at −0.3 %. Any
Phase-1 lever must state its expected 2023 effect **before** solving, and a
lever that lifts 2023's mean by more than **+3 %** is a **regression** even if
2025 improves.

---

## 7. Kill gates for Phase 1 (declared now, refined in PREREG-B)

* **Same-HEAD zero-delta control** — the A-leg is the identical HEAD with the
  mechanism off. Any delta not attributable to the mechanism invalidates both.
* **All three years, one invocation** (rule 16 `[R-ALLYEARS]`).
* **Leave-one-year-out within 2023–2025** before any promotion (rule 22).
* Both legs registered on the dashboard, keeper **or** rejected (rule 15).
* Matrix cell + §5.4 stamp in the same session (rule 28(b)); a new
  `ScenarioConfig` field carries its matrix row, its
  `_CACHE_KEY_OPTIONAL_FIELDS` registration and its declared default in the
  **same commit** (rule 28(c)).

---

## 8. What this phase will NOT do

* Not re-derive the monthly/seasonal C3a decomposition (DO-NOT-REDO).
* Not re-test miso-145's wall for universe sensitivity (miso-150: exactly
  invariant), the within-unit offer-shape family (miso-151: cell **R**), the
  base-band inversion (miso-152: CLOSED, immaterial), the model-side VRE
  universe fix (null, CLOSED), or the JJA corpus statistics (reproduced
  byte-identically twice).
* Not open the across-unit dispersion object or the CT_PEAKER fill-order
  successor (§1, branches P-C/P-E).
* Not re-tune the MISO outage extract (branch P-D).
* Not touch, solve, score or register **any** year outside 2023–2025.

---

## 9. Deliverable

A **plan of attack grounded in measurement**: the four D-items with their
magnitudes, the branch taken, and — if the branch is P-B — PREREG-B naming one
lever. If the branch is P-A/P-C/P-D/P-E, the deliverable is the escalation with
its numbers, and **no solve is run**.

---

## 10. Disclosure — everything looked at before this PREREG was pushed

Full disclosure, so no statistic below is post-hoc:

1. `DIAGNOSIS-miso152-c3a-lives-in-june-july-2026-08-11.md`, **in full** (the
   charter directs it: read, do not re-derive). All figures quoted in §1 come
   from it.
2. `scripts/calibration_verdict.py --run-id 2026-08-09-miso-148-basis-aware`
   — the §0 re-verification, committed artifacts only, no solve.
3. **Schema and inventory only** of the keeper's `hourly/` sidecars: column
   names of `system_2025` / `class_hourly_2025` / `reserve_family_2025`, the
   three **family names**, the 17 **class names**, the 8 **zone names**, row
   counts, and the first two rows of each frame as printed by the schema dump.
   **No aggregate, no binding count, no availability, no headroom** — no
   statistic that any prior in §3 could be checked against.
4. Source reads: `FleetArrays` field list (`data/fleet/__init__.py:310-375`);
   the LP bound form `min_gen ≤ P ≤ pmax × availability`
   (`model/commitment.py:1601`); `klass` derivation and the dual-fuel
   re-attribution in `run_calibration_full.py:340-470`; `build_year` and
   `_tranche_frame` in `_miso134_ct_night_order_screen.py`; the bundle-repoint
   and trap notes in `_miso152_fillorder.py`.
5. Host state: 15 GB RAM, no swap, 13 GB disk free; venv built with
   **pyarrow pinned to 25.0.0**, pandas 3.0.5, numpy 2.4.6, scipy 1.17.1,
   highspy imports (it has no `__version__`; that is expected, not an error).
6. Branch/session check: no concurrent MISO branch exists —
   `claude/miso-153-calibration-lxe031` is the only `claude/miso*` ref on
   `origin`.

**Any scope extension beyond this PREREG will be labelled NOT PRE-REGISTERED
where it appears, with its counter-measurement reported at full magnitude.**
