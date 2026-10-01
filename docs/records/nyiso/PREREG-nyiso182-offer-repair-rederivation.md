# PREREG — nyiso-182: repair `build_year()`, then re-derive what rested on it

**Session:** nyiso-182, NYISO backcast-calibration track, 2026-09-03.
**Keeper:** `2026-09-02-nyiso-177-vintage-matched` (`results/calibration/nyiso177_vintage_B1p`),
determination NOT-YET, target grade 5, fails 3 {C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}.

**Object, as handed forward by nyiso-181 §11 items 2–3.** `nyiso179_st_gas_offer_position.build_year()`
reconstructs the `ST_GAS` offer **outside** the solve and omits two armed, keeper-registered terms —
the measured RGGI allowance price and `apply_gas_offer_margin`. nyiso-181 proved this on an exact
identity (`max|d| = 0` on 88 units × 8,760 h × 3 years) and **deliberately did not edit the probe**,
because doing so would silently rewrite the basis of the published nyiso-179 record. This session
**repairs it non-silently** and **re-derives the three results that read the defective `mc`**:
nyiso-179's **G3** (`peak` exoneration), its **G4** (between-year channel decomposition), and — the
load-bearing one — the **62.4 / 24.6 / 13.0 split** of the 2025 top-decile `ST_GAS` deficit, which is
the sole basis for *"the `ST_GAS` C1 lane and the C3a-2025 lane are ONE OBJECT"* and for the standing
DO-NOT-OPEN on `ST_GAS` offer levers.

**This document is written and committed, together with its probe and the `build_year()` repair,
BEFORE any quantity on the REPAIRED basis has been computed or read.** §0 discloses in full
everything read at the time of writing, including the published defective-basis numbers the gates
below will re-derive.

**ZERO NON-CONTROL SOLVES, PRE-DECLARED IN EVERY BRANCH** (§3.4). Rule 15 therefore registers
nothing, which is the correct outcome and not an omission.

---

## 0. DISCLOSURE — everything read before these gates existed

Thirteen reads were performed before this file was written. **Twelve are code, artifact-schema,
config or git-history facts. E7/E8 are PUBLISHED MEASUREMENTS on the DEFECTIVE basis — the very
numbers the gates below re-derive — and that is disclosed here rather than glossed.** No quantity
on the **repaired** basis has been computed, read, or estimated.

| # | what was read | result |
|---|---|---|
| E1 | `docs/FINDING-nyiso181-itm-degeneracy-2026-09-03.md` §§4, 5, 7, 11 in full | The `max|d| = 0` identity, the two omitted terms, the second (population-mismatch) defect, the affected/not-affected partition, the five items handed forward. |
| E2 | `results/calibration/PREREG-nyiso181-itm-degeneracy.md` §§0–2 | The disclosure discipline, the inherited-tolerance construction, the declared-one-sided-in-advance construction. |
| E3 | `docs/mechanism-testing-matrix.md` §5.5 (NYISO lever queue, rewritten 2026-09-03) | The DO-NOT-REDO set, the retired `R` statistic, the standing block on C3a-2025, the three items this session is chartered on. |
| E4 | `scripts/probes/nyiso181_offer_reconstruction_repair.py` in full | The exact two-term repair form and its closure proof; the `EXACT` criterion `max|d| ≤ 1e-4`. |
| E5 | `scripts/probes/nyiso179_st_gas_offer_position.py` in full (≈760 lines) | `build_year`, the bar block, V1/V2, G0–G4, `main`. **G3 reads `st["mc"]` only**, so it re-derives on a repaired state with zero edits; **G4 rebuilds `mc` internally** as `hr × fuel + vom` and therefore carries the same defect independently. |
| E6 | `scripts/probes/nyiso178_offer_side_idling.py` helper block | `lp_fleet`, `model_hourly`, `measured_hourly`, `actual_price`, `KEEPER`/`YEARS`/`ISO`/`KLASS`/`HOURS`. `model_hourly` reads `class_hourly`'s `ST_GAS` row — trap (j), the dual-fuel oil undercount. |
| E7 | `results/calibration/_nyiso179_st_gas_offer_position.json`, the 2025 `G3` and `G1` blocks | **PUBLISHED MEASUREMENT, defective basis.** G3-2025: `peak_share_of_oom` 0.3359 (bar 0.40), `peak` OOM-hours 0.8062 (bar 0.90), ITM@actual 2,313.3 MW, measured 2,596.9 MW, model 1,441.9 MW. G1-2025: ITM@model top-decile 1,592.4 MW. |
| E8 | `docs/FINDING-nyiso179-st-gas-offer-position-2026-09-03.md` §7 and §7.1 | **PUBLISHED MEASUREMENT, defective basis.** The 62.4 / 24.6 / 13.0 split and its four anchors; the G4 channel table (FUEL −740.8, PRICE +1,163.1, AVAIL −239.9, net +182 MW) and its own `share_denominator_is_small` disclosure. |
| E9 | `src/market_sim/runner.py:2390–2500` | The exact assembly order the LP installs: `assemble_mc(fa, fuel, resolve_carbon_price(config, year), config.nox_price, so2=(fa.so2_rate, config.so2_price))`, then `apply_eac_to_mc`, `apply_coal_tranches`, then `apply_gas_offer_margin` at `:2494`. |
| E10 | `legacy_bins.assemble_mc`, `offer_curves.apply_gas_offer_margin`, `policy/carbon.resolve_carbon_price` | The carbon term is `fleet.emission_rate × carbon_price`; the margin term is `markup_hr[g] × (anchor − fuel[g,t])` on tranches with `markup_hr > 0`. |
| E11 | Keeper `run_config.json` fields + `resolve_carbon_price` on the keeper config | `nox_price` 0.0, `so2_price` 0.0, `carbon_price` 0.0, `carbon_price_delta` 0.0, `state_carbon_pricing` True, `gas_offer_net_revenue_margin` True, `gas_offer_margin_anchor` 3.9046, `dual_fuel_switching` True; RGGI $13.49 / $20.71 / $22.09. **Already published in nyiso-181 §4**; re-verified, not newly discovered. |
| E12 | `ls results/calibration/nyiso177_vintage_B1p/hourly/` + `.gitignore:541` | No `unit_hourly_*.parquet` in the committed bundle, any year. The instrument needs a replay. |
| E13 | `scripts/probes/nyiso181_replay_identity.py` | Gate I1's committed form and its inherited bar (0 of 52,560 price cells, 0 of 122,640 class-hour cells, per year). |

### 0.1 Why E7/E8 do not compromise these gates

Every bar below is **inherited from a source committed before nyiso-179 itself ran**, never chosen
here:

* **G-3R** uses `G3_OOM_SHARE_BAR = 0.40` and `G3_OOM_HOURS_BAR = 0.90` and the identical three-leg
  conjunction, taken verbatim from `nyiso179_st_gas_offer_position.py`, which fixed them in
  `PREREG-nyiso179-st-gas-offer-position.md` before that session measured anything.
* **G-4R** and **G-S1** use `G4_CARRIER_BAR = 0.60` from the same source. It is nyiso-179's own bar
  for *"one channel dominates a decomposition"*, which is exactly the question G-S1 asks of the
  split.
* **I1** is nyiso-181's bar verbatim. **I2** is `nyiso181_offer_reconstruction_repair.py`'s own
  `EXACT` criterion verbatim. **I3** is the published rounding precision of the artifact it checks.

I know from E7/E8 that the published split clears 0.60 by 2.4 points and that both G3 legs sit
**below** their bars. That knowledge cannot have selected the bars, because the bars are not mine.
It is nonetheless a real asymmetry and it is named here so a reader can weigh it.

### 0.2 One statistic that is NOT re-derived, by instruction

`R = mo / itm` is **RETIRED** (nyiso-181 §5, §11 item 1). It is not computed, quoted, or repaired
anywhere in this session, on either basis. Where a third term of the split needs an un-run quantity,
the **matched-population** form is used instead (§2.4).

---

## 1. The instrument, and why it needs a replay

The repair's correctness is an **identity against the LP's own installed offer**, and the only
artifact carrying that offer is `hourly/unit_hourly_<year>.parquet`'s `mc` column (PR #4650). It is
gitignored at 16–17 MB/yr (E12), so it exists in no committed bundle and is produced by a
**bit-identical control replay of the keeper's own recipe**:

    PYTHONPATH=.:src python scripts/run_calibration_full.py \
      --replay-bundle results/calibration/nyiso177_vintage_B1p \
      --out-dir results/calibration/nyiso182_control

Per the nyiso-180/181 precedent this is **an instrument, not a run: it is NOT registered** (rule 15),
its `unit_hourly` output stays uncommitted, and the 119 MB bundle is not committed. Rules 12 and 16:
one invocation, all three years from the bundle's own `meta.json`, years sequential.

**Every gate below is conditional on I1.**

---

## 2. Gates

### 2.0 The repair itself — stated before it is verified

`build_year()` gains an explicit, defaulted-OFF `legacy_defective_offer` argument. Default
(repaired):

```
mc = assemble_mc(fa, fuel, resolve_carbon_price(cfg_y, year),
                 cfg_y.nox_price, so2=(fa.so2_rate, cfg_y.so2_price))
apply_gas_offer_margin(mc, gens, fuel, cfg_y)
```

`legacy_defective_offer=True` reproduces the published form byte-for-byte
(`assemble_mc(fa, fuel, 0.0, 0.0, so2=(fa.so2_rate, 0.0))`, no margin). **The published nyiso-179
record therefore stays reproducible by an explicit opt-in rather than being silently overwritten** —
which is the condition under which nyiso-181 declined to make the edit. The repair uses the keeper's
own `nox_price` / `so2_price` (both 0.0, E11) rather than nyiso-179's hardcoded zeros, so it is the
runner's expression, not a value chosen to close anything.

### I1 — is the control replay THE keeper? **CAN FAIL.**

`scripts/probes/nyiso181_replay_identity.py`, run unmodified. **Bar inherited verbatim from
nyiso-181 §2 G-I I1:** 0 of 52,560 hourly zonal price cells and 0 of 122,640 class-hour cells differ,
**per year**. Any non-zero count fires **S1**.

### I2 — does the REPAIRED reconstruction equal the LP's installed offer? **CAN FAIL.**

Over every `ST_GAS` unit-hour in all three years, `max |mc_repaired − mc_LP| ≤ 1e-4` $/MWh.
**Tolerance inherited verbatim** from `nyiso181_offer_reconstruction_repair.py`'s `EXACT` criterion.
This is the gate nyiso-180's P-c could not be: it compares the **reconstruction to the LP**, not the
LP to itself.

### I2b — do the two routes to the ITM anchors agree? **CAN FAIL.**

The 2025 top-decile ITM-at-actual-price anchor computed (a) from the repaired reconstruction
(`pmax × availability`, the nyiso-179 route) and (b) from the LP's own `unit_hourly` `mc`/`cap_mw`
must agree to **≤ 0.05 MW** — the published rounding precision of the field it reproduces
(`round(..., 1)`). A corollary of I2; gated anyway, because a corollary that fails means one of the
two frames is misaligned.

### I3 — does the LEGACY path still reproduce the published record EXACTLY? **CAN FAIL.**

With `legacy_defective_offer=True`, `p179.g3_band_attribution` and `p179.g4_between_year` run
**unmodified** must reproduce `_nyiso179_st_gas_offer_position.json` to its published rounding:
**≤ 0.05** on fields rounded to 0.1 MW, **≤ 0.0005** on 4-dp shares, across all three years and every
band. This is a deterministic identity — it can fail only if the repair broke the legacy path — and
it is what makes the repaired-vs-published comparison like-for-like rather than a different
statistic (the nyiso-181 §4.4 discipline).

### G-3R — is the un-grounded `peak` 4.20 where the missing MW sits, on the REPAIRED offer? **CAN FLIP EITHER WAY.**

`p179.g3_band_attribution(states_repaired)`, **run unmodified**, with its own three-leg conjunction
and both bars inherited verbatim:

* **`PEAK-IMPLICATED`** iff 2025 `peak_share_of_oom` ≥ **0.40** AND 2025 `peak` top-decile OOM-hours
  ≥ **0.90** AND 2023 `peak` top-decile OOM-hours ≥ **0.90**.
* **`PEAK-EXONERATED`** otherwise.

**Declared in advance, before measurement:** the published legs are 0.3359 and 0.8062 (E7), *both
below their bars but not far below*, and the repair raises **every** band's `mc`. The OOM-hours legs
must therefore move **up** (weakly); the share leg is **ambiguous in sign**, because `peak` is
already the most out-of-the-money band ($415.94 mean `mc`, E7) so a uniform upward shift adds
proportionally more OOM MW to the other bands. **This gate is genuinely two-sided and is expected to
be close.**

### G-4R — what moves the offer position BETWEEN years, on the REPAIRED offer? **CAN FAIL.**

The repair introduces a channel nyiso-179's three-channel decomposition could not have: the RGGI
allowance charge is `emission_rate × carbon_price` and **both factors vary by year** ($13.49 → $22.09;
plant CO₂ rates are same-year CAMPD in backcast). Reported as a **2 × 2 grid** so the reader can
separate *the repair moved it* from *the method moved it*:

| | published method (3 channels, nyiso-179's complementary order pair) | extended method (4 channels, FULL Shapley over all 24 orderings) |
|---|---|---|
| **legacy offer** | must equal the published table (this is I3's G4 leg) | reported (CARBON ≡ 0 by construction) |
| **repaired offer** | reported | **PRIMARY** |

* **Bar inherited verbatim:** `G4_CARRIER_BAR = 0.60` on `|share|` of the net ΔITM(2023→2025).
  `CARRIER IDENTIFIED` iff the largest channel clears it, else `DIFFUSE`.
* **nyiso-179's own `share_denominator_is_small` disclosure is carried verbatim and is declared here,
  in advance, to be the honest reading**: when the net delta is small against the channel magnitudes
  the shares are a near-cancellation artifact and **the MW contributions are the reported output**.
  The verdict word is secondary and is reported as such whichever way it lands.
* **Structural certification, measured not assumed** (nyiso-179's own `band_drift` check, extended):
  `heat_rate`, `vom` and `markup_hr` max drift across 2023→2025 must be **exactly 0.0** for the
  three-/four-channel closure to hold. `emission_rate` drift is **measured and reported**; if
  non-zero it is carried inside the CARBON channel **by construction**, declared here in advance so
  it cannot be reassigned after the fact.

### 2.4 G-S — the 62.4 / 24.6 / 13.0 split. **THE LOAD-BEARING GATE. CAN FAIL, BOTH WAYS.**

Four anchors, on the 2025 top decile by **actual** RT price (`_decile_idx(price_rt(2025))[-1]`,
inherited):

| symbol | quantity | offer-dependent? |
|---|---|---|
| `M` | measured CAMPD `ST_GAS` MW | **no** |
| `A` | capacity in the money at the **ACTUAL** price | yes |
| `P` | capacity in the money at the **MODEL'S OWN** zonal price | yes |
| `D` | model `ST_GAS` dispatch | **no** |

The published three-term partition, verbatim in form:

    G  = M − D            (the gap)
    T2 = M − A            "offer position proper"      (published 284 MW, 24.6 %)
    T1 = A − P            "model price below actual"   (published 721 MW, 62.4 %)
    T3 = P − D            "un-dispatched at own signal" (published 150 MW, 13.0 %)
    G  = T1 + T2 + T3     (exact, by construction)

**`G` is offer-independent**, so the repair *redistributes a fixed gap* rather than resizing it — with
one correction, declared here in advance: **`D` is taken from the `unit_hourly` per-unit sum, not
from `class_hourly`'s `ST_GAS` row**, because the latter under-reports the class by the dual-fuel
oil-switched energy (trap (j); 10.014 → 10.169 TWh in 2025). The gate is read on the **corrected**
basis; the `class_hourly` basis is reported alongside for like-for-like with the published number.

**The third term is additionally repaired for the nyiso-181 §5 population mismatch**, exactly:

    T3a = Σ_g max(cap_mw − mw, 0) · 1{mc ≤ p_model}     ≥ 0   un-run IN-THE-MONEY capacity (matched)
    T3b = − Σ_g mw · 1{mc >  p_model}                   ≤ 0   dispatch of OUT-of-the-money bins
    T3  = T3a + T3b                                            (exact)

This is reported as a refinement; **G-S1/G-S2 are read on the published three-term partition** so the
comparison to 62.4 / 24.6 / 13.0 is like-for-like.

**G-S1 — dominance. Bar inherited: `G4_CARRIER_BAR = 0.60`.**
`PRICE-DOMINANT` iff `T1 / G ≥ 0.60`. (Published basis: 0.624 — clears by 2.4 points.)

**G-S2 — plurality. THRESHOLD-FREE.**
`PRICE-LARGEST` iff `|T1| > |T2|` and `|T1| > |T3|`.

**Lane verdict, pre-declared in all three branches:**

| verdict | condition | pre-declared consequence |
|---|---|---|
| **`PREMISE-CONFIRMED`** | G-S1 **and** G-S2 pass | The *"one object"* identification **STANDS on a repaired instrument**, the standing DO-NOT-OPEN on `ST_GAS` offer levers **STANDS**, and the lane **stays blocked** on owner-court C3a-2025. Task 2's conditional does not arm. **This is a legitimate, publishable result and is registered here in advance as such** — the session's value is then that a load-bearing premise survived its instrument being repaired. |
| **`PREMISE-WEAKENED`** | G-S2 passes, G-S1 fails | `T1` is still the plurality term but no longer a majority carrier. The *"one object"* claim is **DOWNGRADED from an identity to a plurality** and re-sized at its measured value. The DO-NOT-OPEN **still stands** — C3a-2025 is owner-court independently of any decomposition — but the `ST_GAS` offer-position component is re-sized in the queue for the successor. **No lever opened.** |
| **`PREMISE-OVERTURNED`** | G-S2 fails | `T1` is no longer even the largest term: **the lane's blocking premise has changed.** Task 2's conditional arms — the `ST_GAS` offer-position component becomes **openable** — and this session records the unblocking, re-sizes the queue entry and hands the opened object forward. **It does not build the lever** (§3.4), and it does not touch C3a-2025, which stays owner-court on its own footing. |

---

## 3. Pre-declared consequences and limits

### 3.1 What a `PEAK-IMPLICATED` flip does, and does not, license

It identifies the `peak` band as where the top-decile OOM MW sits **on a faithful offer**. It does
**not** open `offer_curve_by_group` (cell `K`, and the `peak` 4.20's grounding is a separate open
item), it does **not** license changing the 4.20, and no parameter moves this session. The cell is
annotated, not re-graded.

### 3.2 What is NOT re-derived

nyiso-179's **V1, V2, G0, G1 and G2** are out of scope. G1's `R` is retired (§0.2) and is not
repaired. G0 and G2 read `st["mc"]` only through report fields whose gated legs are offer-invariant
(G0 is a config/heat-rate question; G2's reach leg is a capacity share and its binding leg is a
fuel-price comparison **inside** `resolve_fuel_prices`, upstream of both omitted terms) — but they
are **not re-run or re-claimed here**, and this session makes no statement about them beyond naming
them out of scope.

### 3.3 What the repair does NOT touch

The keeper, its determination, target grade, fail set and every scored metric — the replay is
bit-identical by I1 and `metrics.json` is untouched. `src/market_sim/` is **not modified**: the only
source edit is to a probe under `scripts/probes/`. Every DO-NOT-REDO cell (nyiso-178/179/180/181)
stays closed. C3c is not opened (SUPPORTING, not lone). C3a-2025 stays owner-court in **every**
branch above, including `PREMISE-OVERTURNED`.

### 3.4 ZERO NON-CONTROL SOLVES, in every branch

Pre-declared: this session runs **one** control replay (the instrument) and **no** calibration run,
in every branch of every gate, including `PREMISE-OVERTURNED`. The brief's task 2 is registered as a
**conditional hand-forward, not a build** ("do not pre-build the lever"). Rule 15 therefore registers
nothing and rule 16 has nothing to span — that is the correct outcome, not an omission.

---

## 4. Stop conditions

* **S1 — instrument failure.** If **I1, I2, I2b or I3** fails, **every** re-derived verdict
  (G-3R, G-4R, G-S) is **WITHHELD**. The failure is reported at full magnitude, the repair is
  reported as unverified, and the re-derivation is handed forward unmade. **No bar is reinterpreted
  to rescue a verdict** — nyiso-181 honoured exactly this and paid for it in its headline; so will
  this session.
* **S2 — missing input.** If the replay cannot complete (time, memory, data), the session reports the
  re-derivation unmade rather than substituting a proxy for `unit_hourly`.
* **S3 — the repair does not close.** If I2 fails specifically, the *diagnosis* nyiso-181 published
  is **not** thereby overturned — it closed on its own probe — but **this session's repaired
  `build_year()` is reported as WRONG** and is not left in place as the default.

---

## 5. Honest expected value, written before the answer

* **No lever, in any branch**, and none is available: the two candidate cells are `K` and the one
  open lane is owner-court. The deliverable is a **repaired instrument plus three re-derived
  numbers**, one of which is load-bearing.
* **The C1-2023 `ST_GAS` +3.86 TWh gate is not moved and nothing here moves it.** This session
  re-sizes an *explanation*; it does not supply one.
* **A `PREMISE-CONFIRMED` outcome delivers no new object.** It is registered above as legitimate
  precisely so it cannot be re-read afterwards as a null result — but it is, honestly, the branch
  with the least forward value, and that is stated before the measurement rather than after.
* **`Ω`, the reserve rows, and carrier 2 are untouched.** nyiso-181's INCONCLUSIVE reading stands and
  is not an exoneration.
* **Reproducibility cost, inherited and named:** every number here needs the ~15-minute control
  replay, because `unit_hourly` stays uncommitted at 16–17 MB/yr.
* **The 2 × 2 G-4R grid cannot separate a genuine four-channel structure from a methodology
  artifact by itself** — full Shapley over 24 orderings is exact for the channels it is given, but
  the channel *partition* is a modelling choice, and assigning the offer margin to FUEL (it is a
  function of `fuel[g,t]`) is a choice made here, in advance, and named as one.

---

*Rules: 1 `[R-STRUCT]` (nothing adopted or rejected on whether it moved a fit), 12/16 (one
invocation, three years, sequential), 13 `[R-MEASURED]` (no pinning; every gated quantity is a
model-internal LP output on the keeper's own recipe), 14 `[R-ACCURATE]` (this session IS the rule,
applied to an instrument), 15 (the replay is an instrument, not a run — not registered), 19
`[R-ONE-MECH]` (nothing added), 21/23 (zero parameters touched, zero swept), 22 `[R-HOLDOUT]`
(2023/2024/2025 only; NYISO absent from both markers; no marker requested), 24 `[R-REGISTRY]` (no
new tunable), 25 `[R-ISO-SCOPE]` (NYISO only; NYISO shard only), 27 `[R-PUSH]` (the one edited file
is ≥300 lines and is edited locally and blob-verified after push), 28 `[R-MECH-MATRIX]` (§3.1).*
