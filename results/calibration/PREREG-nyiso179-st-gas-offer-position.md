# PREREG — nyiso-179: the NYISO `ST_GAS` offer **POSITION**

**Session:** nyiso-179, NYISO backcast-calibration track, 2026-09-03.
**Keeper at entry:** `2026-09-02-nyiso-177-vintage-matched`
(`results/calibration/nyiso177_vintage_B1p`), determination **NOT-YET**, target
grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}.
**Committed BEFORE the probe runs**, with the probe, per the standing
pre-registration discipline (thirteenth consecutive session).

---

## 0. DISCLOSURE — everything read or measured BEFORE these gates existed

Stated in full so no gate can be accused of having been shaped around a number
it was supposed to test.

### 0.1 Residual-adjacent quantities I hold, ALL of them inherited from the brief

The `ST_GAS` year signature (model 11.999 / 9.799 / 10.014 TWh against actual
8.141 / 9.913 / 13.712), nyiso-178's actual-price-band ratios for 2023
(1.233 … 1.009) and 2025 (0.919 … 0.555), and its top-three-decile saturation
(1,603 → 1,429 → 1,442 MW against a ~3,650 MW envelope and a ~2,500 MW measured
fleet). **These are nyiso-178's measurements, restated by my brief. I have
computed no residual, no price series and no dispatch series of my own.** They
are what defines the OBJECT; the gates below are deliberately written on
quantities that are *not* among them (reach, binding, in-the-money MW, band
attribution, between-year decomposition), so that each gate can fail
independently of the signature that motivated it.

### 0.2 Code read before the gates were written (no execution)

`data/offer_curves.py::split_gas_tranches`,
`pipeline/backcast_config.py::_NYISO_OFFER_CURVE`,
`data/fuel/dual_fuel.py`, `data/fleet/eia860.py::_dual_fuel_plant_groups`,
`data/fuel/resolve.py` (application order),
`data/fleet/legacy_bins.py::assemble_mc`,
`data/fleet/assembly.py::bins_to_fleet` (band construction and `unit_id`
naming), `config/constants.py::ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO`,
`scripts/probes/nyiso178_offer_side_idling.py` (`lp_fleet` and helpers).

### 0.3 Committed data/config VALUES read before the gates were written

* The keeper's `run_config.json` flag values: `dual_fuel_switching=True`,
  `dual_fuel_oil_daily_parity=True`, `nyiso_zonal_gas_basis=True`,
  `gas_hub_basis_overlay=True`, `gas_hub_basis_daily=True`,
  `gas_monthly_actuals=True`, `use_campd_bins=True`, `plant_level_fleet=True`,
  `campd_per_unit_attribution=True`, `campd_outage_merit_order_guard=True`,
  `nyiso_gas_commitment_bridge=True`, `historic_outage_overlay=False`,
  `gas_st_committed_hr_override=None`, `nyiso_downstate_ct_gas_basis=False`,
  `carbon_price = nox_price = so2_price = 0.0`, and **`gas_offer_margin`
  ABSENT** (so every `phys_*` key on the NYISO curve is inert at runtime).
* The registered NYISO `ST_GAS` offer curve: `committed` 1.05, `econ_low` 1.08,
  `econ_high` 1.13, **`peak` 4.20**, `econ_low_share` 0.50, `pct_peaking` 15.0.
* `data/raw/reference/nyiso_campd_marginal_hr_summary.csv`, `ST_GAS` row
  (base_hr 10.614, n_units 25, `avg_committed_p50` **1.104**, `avg_econ_low_p50`
  1.028, `avg_econ_high_p50` 0.905, `marg_committed_p50` 0.818,
  `marg_econ_low_p50` 0.830, `marg_econ_high_p50` 0.828). Read to answer the
  brief's starting point (1); it is a measured artifact, not a residual.
* Sidecar schemas only (`system_*.parquet` columns; `actual_lmp_hourly_NYISO`
  carries `rt`/`da` at **ISO level, no zonal actuals**).

### 0.4 A FINDING ALREADY REACHED BY CODE READING, disclosed here rather than
### presented later as a gate outcome

**The brief's starting point (1) is very probably INERT for this keeper.**
`ScenarioConfig.gas_st_committed_hr_mult = 1.32` is consumed at exactly one
site, `offer_curves.split_gas_tranches`, the **legacy non-CAMPD** gas path. The
keeper runs `use_campd_bins=True` / `plant_level_fleet=True`, whose committed
band is set in `assembly.bins_to_fleet` as `base_hr × offer["committed"]` =
`base_hr × 1.05`. Separately, NYISO's own measured `avg_committed_p50` is
**1.104** and is **already registered on the curve** as `phys_committed` — so
the rule-14 substitution the brief proposes is both (a) probably unreachable on
the keeper's path and (b) already carried, within 0.054, by the live band.
**G0 below formalises this so that it is still measured and can still FAIL**, on
the LP's own arrays, rather than being asserted from a code read.

### 0.5 What I have NOT done

No solve. No score. No parameter written or swept. No year outside 2023–2025
read, solved or scored. No holdout marker requested. No C3c lever. C3a-2025 not
opened.

---

## 1. THE OBJECT

**What moves the NYISO `ST_GAS` class's offer POSITION between years.** Not its
availability envelope (nyiso-178 G1: `OFFER-SIDE`, the whole
measured-availability-input family CLOSED in both directions), and not its offer
SHAPE (nyiso-178 G3: `NEITHER`, the duty-curve successor REFUTED for zero
solves). The signature to explain is a near-uniform multiplicative over-offer in
2023 and a **top-weighted** under-offer in 2025.

## 2. THE INSTRUMENT, and why it is exact

Zero solves. For each year, the **exact LP marginal-cost array** is rebuilt by
calling the engine:

```
lp_fleet(year, cfg)            # nyiso-178's validated instrument:
                               #   load_or_synthesize_bins -> bins_to_fleet
                               #   -> generators_to_fleet_arrays
resolve_fuel_prices(cfg, fa, year)   # F923 overlay -> zonal basis -> oil cap
assemble_mc(fa, fuel_prices, 0.0, 0.0, so2=(fa.so2_rate, 0.0))
```

`resolve_fuel_prices` applies, **in this order and inside one call**, the F923
plant-monthly overlay, the per-ISO zonal gas basis
(`apply_nyiso_zonal_gas_basis`) and finally the dual-fuel oil-parity cap
(`apply_dual_fuel_pricing`) — verified by reading `data/fuel/resolve.py`, not
assumed. Because the keeper carries `carbon_price = nox_price = so2_price = 0`,
`mc = heat_rate × delivered_fuel + vom` exactly. Band membership is read from
the `unit_id` suffix (`f"{bin_id}_{suffix}"`, `assembly.py:1371`).

**Prices.** `ITM_model` uses the keeper's **own P1 zonal prices** (exact, per
bin's zone, from `hourly/system_<year>.parquet`). `ITM_actual` uses the
**ISO-level** actual RT LBMP, because no zonal actual series exists in the
committed validation artifact. **The direction of that limitation is stated
here, before it is used:** NYC/LI steam faces a *higher* zonal price than the
ISO mean, so an ISO-level price **understates** `ITM_actual`, which makes the
"the model's offer is priced too high" conclusion **harder** to reach, never
easier. The bias is conservative against this session's preferred answer.

### 2.1 INSTRUMENT VALIDATION — fixed here, and read BEFORE any gate

nyiso-178 had three construction defects (two caught by code reading, one by the
probe's own output falsifying a reconstructed ceiling at p99). Two validators
are pre-committed; **if either fails, the INSTRUMENT is repaired and the repair
disclosed — never the gate softened.**

* **V1** — for every non-bypassed NYISO `ST_GAS` bin, the reconstructed band
  heat rate must equal `base_hr × offer_curve_by_group["ST_GAS"][band]` to
  within `1e-9`. This proves the array being measured is the LP's real offer.
* **V2** — the class availability envelope reconstructed here must agree with
  nyiso-178's committed `_nyiso178_offer_side_idling.json` envelope to within
  **0.1 %** in every year. A cross-session agreement check on a shared
  instrument.

**No gate result is read until V1 and V2 both pass.**

---

## 3. GATES

Every bar below is fixed here, before execution. Each has a branch that fails.

### G0 — is `gas_st_committed_hr_mult` LIVE on this keeper? *(brief item 1)*

Build the LP fleet at the keeper's exact config and classify every NYISO
`ST_GAS` bin's committed band heat rate against `base_hr × 1.05` (the offer
curve), `base_hr × 1.32` (the `ScenarioConfig` scalar) and `base_hr × 1.15`
(`campd_bins._DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"]`, the class default
reached only through the `ST_GAS_PEAKER_PLANTS` bypass).

* **G0 = INERT** iff **0 MW** of NYISO `ST_GAS` capacity resolves the 1.32
  scalar. ⇒ starting point (1) CLOSES; 1.32 is not touched, and
  `caiso_st_gas_committed_measured` is **not** armed for NYISO (it would also
  hard-error: NYISO has no entry in
  `ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO`, and adding one for a class no
  NYISO bin can reach would be an unreachable registry entry).
* **G0 = LIVE** iff **> 0 MW** resolves it. ⇒ derive NYISO's own committed
  multiplier from NYISO conduct and carry it to G5.

### G1 — is the `ST_GAS` OFFER what governs its dispatch? *(the type test)*

The successor to nyiso-178's G1, asking of the **offer** what that gate asked of
the **envelope**. Per hour `t`, over `ST_GAS` bins:

```
ITM_model(t) = Σ_g pmax[g] · availability[g,t] · 1{ mc[g,t] ≤ P_model[zone(g), t] }
R(t)         = model_MW(t) / max(ITM_model(t), 1.0)
```

* **OFFER-GOVERNED** iff the **median** `R` over all 8,760 h lies in
  **[0.70, 1.43]** in EVERY year **and** the top-actual-price-decile **mean** `R`
  lies in **[0.70, 1.43]** in EVERY year.
* **NOT-OFFER-GOVERNED** otherwise.

The bar is **two-sided on purpose**: `R > 1.43` says forcing channels (floors,
the commitment bridge), not the offer, put the MW on the bar; `R < 0.70` says
in-the-money capacity is withheld by something that is not its price
(transmission, reserve co-optimisation, commitment). Either branch refutes "the
offer position is the governing object" and fires **S1**.

### G2 — rule 19 `[R-ONE-MECH]`: does the ARMED oil-parity cap REACH and BIND on `ST_GAS`? *(brief item 3)*

`dual_fuel_switching` is **already armed** on this keeper. Before any fuel-side
mechanism may be proposed, rule 19 requires establishing what the armed one
does.

* **(a) REACH** — share of NYISO `ST_GAS` LP capacity whose
  `(plant_code, "ST_GAS")` key is in
  `fleet.eia860.dual_fuel_plant_groups()`.
* **(b) BIND** — an **input-side A/B with no LP**: `resolve_fuel_prices` with
  `dual_fuel_switching` on vs off. Report the share of `ST_GAS` bin-hours the
  cap lowers, the MW-weighted mean relief in $/MMBtu, and both restricted to
  each year's top actual-price decile.

Branches:

* **LINE CLOSED** iff reach ≥ **0.50** of `ST_GAS` capacity **and** the cap
  binds in ≥ **5 %** of 2025 top-decile bin-hours. ⇒ the job is already done;
  **S2** fires and no new dear-hour fuel mechanism is proposed.
* **WIRING GAP** iff reach < **0.50**. ⇒ a discovered defect (rules 14/19) with
  zero new parameters; it becomes the candidate arm, subject to G5.
* **REACHES BUT INERT** iff reach ≥ 0.50 and top-decile binding < 5 %. ⇒
  reported with its cause and handed forward, **not armed this session**:
  raising the gas side or lowering the oil side to make it bind would be a value
  chosen against a known residual (rule 21 `[R-DOF]`).

### G3 — is the un-grounded `peak` 4.20 where the missing MW sits? *(brief item 2)*

Band-decompose the `ST_GAS` stack by `unit_id` suffix. In each year's top
actual-price decile report, per band: capacity, in-the-money capacity at the
ACTUAL RT price, and out-of-the-money (OOM) capacity.

* **PEAK-IMPLICATED** iff ALL of: in 2025's top decile the `peak` band holds
  ≥ **0.40** of the class's OOM MW; it is OOM in ≥ **0.90** of those hours; and
  it is **not** in the money in 2023's top decile in ≥ 0.90 of hours either
  (the sign-asymmetry the brief demands — a band already clearing in 2023 cannot
  be re-priced downward without deepening the 2023 over-run).
* **PEAK-EXONERATED** otherwise ⇒ **S3** fires; the 4.20 is not touched and
  stays recorded as un-grounded.

**Pre-declared so this gate cannot become a licence to tune:** even under
`PEAK-IMPLICATED`, **no replacement value may be chosen from the residual**.
`nyiso_campd_marginal_hr_summary.csv` carries **no peak column** (nyiso-169b's
own finding), so absent a new measured NYISO artifact the outcome of this gate
is a **specification, not an arm**, and the band stays un-grounded.

### G4 — what moves the offer position BETWEEN years? *(the chartered object)*

`ΔITM_actual(2023 → 2025)` is decomposed over exactly three varying channels
(the fourth, the band/heat-rate structure, is constant by construction and is
reported to confirm it contributes 0):

1. **FUEL** — the delivered `(n_gen, T)` price (gas level, seasonality, hub and
   daily basis, zonal basis, oil cap);
2. **PRICE** — the actual RT LBMP distribution;
3. **AVAILABILITY** — the envelope.

Each channel is swapped between its 2023 and 2025 value with the others held,
in **both orders, averaged** (a Shapley-symmetric two-point decomposition), so
the attribution does not depend on path.

* **CARRIER IDENTIFIED** iff one channel accounts for ≥ **0.60** of
  `|ΔITM_actual|`.
* **DIFFUSE** otherwise ⇒ **S4** fires: no single-channel arm is identified;
  the decomposition is reported and the session stops.

### G5 — the SIGN-SYMMETRY bar, applied to any candidate BEFORE it is built

The brief's own requirement, made a gate. Any candidate that changes the
`ST_GAS` offer position is first evaluated **on the offer stack alone, zero
solve**: recompute `ITM_actual` under the candidate and require it to move
**TOWARD** the measured MW in **BOTH** 2023 (down) and 2025 (up).

* A candidate **FAILS G5** if it moves `ITM_actual` the same direction in both
  years, or the wrong direction in either.
* **A candidate that fails G5 is NOT built and NOT solved.**

This is the gate that refuses a uniform band re-level, which is the failure mode
the brief names explicitly.

---

## 4. STOP CONDITIONS

* **S1** — G1 `NOT-OFFER-GOVERNED` ⇒ the offer-position type is REFUTED at the
  standing on which nyiso-178 refuted the availability type. No arm is built;
  the object is re-typed and handed forward. **Zero solves.**
* **S2** — G2 `LINE CLOSED` ⇒ the downstate-basis / `dual_fuel_switching`
  dear-hour line CLOSES with a stated re-open condition; no new fuel mechanism.
* **S3** — G3 `PEAK-EXONERATED` ⇒ the `peak` 4.20 is not touched.
* **S4** — G4 `DIFFUSE` ⇒ no single-channel arm identified; report and stop.
* **S5** — any candidate failing G5 is not built and not solved.
* **S6** — standing: no C3c lever; C3a-2025 not opened (owner-court,
  `DECISION-CARD-nyiso148-2025-level-remainder`, Q1 pending); no year outside
  2023–2025 solved, scored or registered; no holdout marker requested; the
  holdout spend freeze untouched; `THERMAL_AVAILABILITY`, `MERIT_OOM_FRAC`,
  `MERIT_RCC_PCTL`, every offer band and every hr-mult are **READ, never written
  or swept**, unless a candidate passes its own gate AND G5 on **measured**
  grounding.
* **S7** — `gas_st_startup_cost` stays **DO-NOT-REDO** (nyiso-172, two
  independent refusals). The measured-availability-input family stays
  DO-NOT-REDO (nyiso-178 (a)); `campd_outage_merit_order_guard` stays
  DO-NOT-REDO (nyiso-178 (b)); an `ST_GAS` duty curve stays DO-NOT-REDO
  (nyiso-178 (c)). None is re-tested here.

## 5. SOLVE BUDGET

**At most ONE A/B, arm-only.** The committed keeper reproduces bit-identically
at HEAD (nyiso-177 G-CONTROL: 0 of 52,560 hourly zonal prices differ in all
three years), so it is a valid control and no control leg is solved. Any arm
runs as ONE invocation, `--year 2023 2024 2025`, ONE bundle, years sequential
(rules 12/16), registered on the backcast dashboard and committed+pushed this
session (rule 15) whether it is a keeper or a rejected probe.

**If no candidate passes G5, the session runs ZERO solves and registers
nothing** — which is the correct outcome, not an omission.

## 6. GOVERNANCE

Rule 1 `[R-STRUCT]` — no mechanism is adopted or rejected on whether it moved a
fit. Rule 13 `[R-MEASURED]` — nothing pinned to actuals; measured series are the
comparison basis only. Rule 14 `[R-ACCURATE]` — a measured-for-estimate
substitution is kept even if the backcast worsens, and the root cause opened.
Rule 19 `[R-ONE-MECH]` — G2 enumerates the armed channel before anything new is
proposed. Rule 21 `[R-DOF]` — no residual-chosen value; G3 and G2's INERT branch
say so explicitly. Rule 23 `[R-FROZEN-DERIVE]` — no artifact re-derived except
on a cited data or defect change. Rule 24 `[R-REGISTRY]` — any new tunable
appears in `ScenarioConfig` **and** `run_config.json`. Rule 25 `[R-ISO-SCOPE]` —
NYISO artifacts only; every other ISO's tranche/outage CSV stays byte-untouched
and only the NYISO matrix shard is edited. Rule 22 `[R-HOLDOUT]` — 2023–2025
only. Rule 28 `[R-MECH-MATRIX]` — every cell tested is updated in the NYISO
shard this session, rejections included.

---

## 7. AMENDMENTS — construction defects found by CODE READING, before any execution

Recorded here, before the probe is committed or run, so that each correction is
auditable rather than asserted. This mirrors nyiso-178 §5, which caught two
defects the same way and a third from its own output.

### 7.1 The band-suffix vocabulary was WRONG, and would have hollowed out G3

The first draft of `scripts/probes/nyiso179_st_gas_offer_position.py` split LP
tranches on the strings `econ_low` / `econ_high` — the keys of the **registered
offer curve**. Those are **not** the LP's tranche suffixes. Reading
`fleet/assembly.py` (the `tranches` list at `assembly.py:1264` and the econ
split at `909–1005`) and `offer_curves.py::_econ_curve_steps`, the actual
vocabulary is `mustrun / sync / committed / commitcyc / econlo / econhi / econ /
econcNN / peak`, and a unit id is `f"{bin_id}_{suffix}"` with
`bin_id = f"{group}_{zone}_p{plant_code}"` (+ an optional `_r{YYYYMM}` cohort
tag). Every suffix is a **single token containing no underscore**, so the band
is exactly `unit_id.rsplit("_", 1)[-1]`.

**Why it mattered.** `econ_low` matches nothing, so the entire economic ramp —
the bulk of the class's dispatchable capacity — would have fallen into an
`other` bucket. G3's denominator (`total_oom_mw_top_decile`) would then have
been dominated by a mislabelled residual, and the `peak` band's share of it
would have been computed against a meaningless total. **The defect biases G3
toward `PEAK-IMPLICATED`** — the brief's own starting point (2) — because
collapsing the econ ramp out of the named bands inflates `peak`'s relative
standing among the bands that remain. It is corrected before execution for
exactly that reason. The bars in §3 G3 are unchanged.

### 7.2 G4's mc reconstruction omitted VOM

The first draft's G4 decomposition built `mc = hr × fuel` while G1 and G3 used
the engine's `assemble_mc`, which is `hr × fuel + vom` (carbon/NOx/SO2 prices
are all 0 on this keeper, §0.3). A VOM-free `mc` is uniformly **cheaper**, so
it would have reported more capacity in the money in every year and every
channel. Corrected to carry `fleet.vom` from the same arrays, so all three
gates read one identical marginal-cost definition.

### 7.3 The BAND channel of G4 is MEASURED, not assumed

§3 G4 asserts that the fourth channel — the band/heat-rate structure — is
constant across years by construction. That is a claim about the code, and the
probe now **measures** it rather than asserting it: `band_heat_rate_max_drift`
and `band_vom_max_drift` are computed over the common bin set and reported with
the decomposition. **Pre-declared action:** if either drift exceeds `1e-6`, the
three-channel decomposition is INVALID as specified, G4 is recorded
`INVALID — BAND CHANNEL LIVE`, and the carrier claim is **withheld** rather
than reported against a decomposition that does not close. The gate is not
softened to absorb it.

### 7.4 One instrument limitation restated, because it bounds every gate above

Per-generator **model dispatch** is in no keeper artifact (the standing
nyiso-172 §2.5 / nyiso-173 limit). `class_hourly` carries the class aggregate,
so G1's `R` and G3's model column are class-level, while `ITM`, the band
decomposition and the OOM attribution are per-bin offer-side quantities that
need no dispatch. **Consequence, stated before the gates are read:** G3 can
show *where the model's un-cleared capacity sits in its own offer stack*, and
cannot show which individual bin the LP actually ran. No gate below is written
to require the latter.

### 7.5 V1 was WRONG ON THE CODE — a third pricing route exists — and is restructured

§2.1's V1 asserted that every non-bypassed `ST_GAS` bin's band heat rate equals
`base_hr × offer_curve_by_group["ST_GAS"][band]`, and would have called any
departure an **instrument failure**. Reading `bins_to_fleet` further shows that
is false: there is a **third pricing route**. At `assembly.py:796`,
`if ov is not None:` — the **per-plant tranche sheet** — overwrites
`committed_hr` and `peak_hr` with the *sheet's* own `hr_mc` / `hr_pk`
multipliers, and this keeper runs `campd_per_unit_attribution=True`. A
sheet-priced bin is still **the LP's real offer**; it is simply not priced by
the class curve. The original V1 would have reported an instrument failure for a
correctly-built array.

**V1 is therefore split, and only the half that is genuinely about the
instrument can fail:**

* **V1(a) — INSTRUMENT, CAN FAIL.** Within each bin the LP heat rates must
  satisfy `econlo ≤ econhi ≤ peak`, the rising-ramp contract every pricing
  route obeys. This is what breaks if the band parsing of §7.1 is wrong, which
  is exactly what a validator is for. Tolerance `1e-9` absolute on the
  inversion.
* **V1(b) — REPORT, CANNOT FAIL.** The share of committed-band MW whose heat
  rate reproduces the registered class multiplier (1.05) exactly, versus MW
  priced by the per-plant sheet, versus MW on the `ST_GAS_PEAKER_PLANTS`
  bypass. This is *information about where the offer comes from*, and it is
  fed to G0 rather than being allowed to gate anything.

**§2.1's `1e-9` band-equality bar is WITHDRAWN and replaced by V1(a).** The
substitution makes the validator *weaker as a test of the class curve* and
*correct as a test of the instrument*, which is the right trade: nothing in
this session's gates depends on the class curve being the sole pricing rule,
and G3's band decomposition is valid under all three routes because it reads
the LP's own heat rates, never a multiplier.

### 7.6 G0's verdict is STRUCTURAL, not inferred from heat rates

A consequence of §7.5. Because a non-1.05 committed multiplier can now come
from the per-plant sheet, "some MW is not at 1.05" no longer implies "the 1.32
scalar is live". G0's verdict is therefore read off the **call-site gate**
instead: `gas_st_committed_hr_mult` is consumed at exactly one site,
`offer_curves.split_gas_tranches`, which `bins_to_fleet` calls only from its
non-CAMPD limb under `not use_campd_bins and config.gas_offer_curve`
(`assembly.py:1912`) — the same limb whose coal sibling was **deleted as
unreachable** at ercot-188. `G0 = LIVE` iff that limb is entered;
`G0 = INERT` otherwise. The heat-rate attribution of V1(b) is reported
alongside as corroboration, not as the test.
