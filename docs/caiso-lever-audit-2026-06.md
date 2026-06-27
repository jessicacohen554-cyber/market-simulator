# CAISO calibration-lever audit — dispatch *shape* vs class-total fitting

**Date:** 2026-06-27  **Mode:** diagnosis pass (no dashboard keeper produced)
**Keeper audited:** `2026-06-26-caiso-32-evening-export`
(`results/calibration/caiso32_eor_exportcap`), re-solved per-plant multi-zone
2023·2024·2025 with the keeper flag set.

---

## VERDICT FIRST — which levers fake the shape

| Lever | Real mechanism? | Reproduces hourly shape? | Verdict |
|---|---|---|---|
| **A. Gas commitment floor** (`caiso_gas_commitment_floor`, frac 0.80, h9–16) | **No** — pins the gas fleet to 0.80 × its *measured* EIA‑930 NG:NG generation; a measured-outcome overlay doing midday-**price** work | **No** — forces 19.3 TWh midday, holds CC_REGULAR ~2 GW above the real midday trough, fills the duck-curve belly the market empties | **REMOVE / replace with real RA commitment** |
| **B. CT_PEAKER local-RA floor** (`caiso_ct_reliability_floor`, base 0.049 + temp limb, h15–22) | **Partly** — temp limb is forward-derivable; the **flat 0.049 year-round baseline (61 % of binding hours) is a level target** | **No** — flat rectangle h15–22 vs the real sharp h18 evening peak | **REPLACE** — keep a real net-load-ramp-shaped RMR for named pocket units; drop the flat baseline |
| **C. CHP bands + EOR HR fix** (CHP must-run floor; `CAISO_EOR_TOPPING_FACTOR` 1.8×) | EOR HR fix **yes** (power-only HR, physical). CHP must-run **level** too high | CC_CHP flat shape is **real** (baseload cogens); CT_CHP band over-runs reporting cogens 6–8× | **KEEP EOR fix; re-derive CHP must-run level/shape** |
| **D. Solar overrun / negative offers** (`negative_renewable_offers`) | Negative offer is a real price (RPS/PTC keep-running value) | Solar **shape r≈0.92–1.00 is good**; the **level over-runs by ≈ the entire real curtailment volume** | **KEEP offer mechanism; fix under-curtailment at root** |
| **E. Interchange levers** (per-hub intertie, import-gas coupling, corridor caps, gas-hub basis) | **Yes** — each tracks a measured capability/price | Not implicated in the thermal-shape complaints | **KEEP** (separate interchange-shape check warranted) |

**Bottom line:** the owner's thesis is confirmed. Two levers — the **gas
commitment floor (A)** and the **flat baseline of the CT_PEAKER floor (B)** —
are flat must-run bands tuned to per-class energy levels / a midday price, and
they break the diurnal shape. They are exactly the "fitted adder / load proxy /
haircut tuned to the residual" CLAUDE.md #1 forbids. A real surprise the probes
surfaced: **the floors are *not* padding a gas total** — the model under-runs
total gas every year (76 vs 88 TWh measured); the floors *mis-allocate* the
(too-small) gas envelope into a flat midday slab on the wrong units.

---

## Method

- **Re-solved keeper**, 3 years, exact keeper flags (per-plant multi-zone P1).
- **Shape probe** (`scratch shape_probe.py`): model mean diurnal MW/hour-of-day
  per class from `dispatch/<yr>_P1.parquet` vs measured —
  - **CAMPD CEMS** per-unit `grossLoad` (`data/raw/campd-unit-level/CA_<yr>`),
    routed to a model class by **plant→class ∩ unitType** (so co-located mixed
    units at one facilityId — e.g. AES Alamitos old steam + new CCGT — split
    correctly instead of lumping);
  - **EIA-930** `CISO_fueltype` (`NG` gas total, `SUN` solar);
  - **CAISO production-&-curtailment** workbooks for solar curtailment.
  - Clocks all treated local-standard / no-DST (model uses a naive local clock;
    CEMS is local standard; EIA-930 UTC shifted a fixed −8 h).
- **Floor attribution** by recomputing each floor's `min_gen` target from its
  own source functions.
- **Lever-off probes** (2024-only, throwaway): gas-floor-off, CT-floor-off,
  both-floors-off, negative-offers-off — observe shape *and* total.

All numbers below are reproducible from the scratch scripts; metrics are hourly
Pearson *r* and the diurnal MW band, never an annual MAE.

---

## Per-class shape, 3-year (model vs CAMPD/EIA-930)

`band` = mean MW over h13–23 (h10–15 for solar). `band×` = model ÷ measured.

```
2023            mdl TWh meas TWh    r  NRMSE  mdl band meas band band x
CC_REGULAR        60.28   44.52  0.81  0.24      7129     5656   1.26
CT_PEAKER          1.92    3.05  0.68  0.10       478      614   0.78
CT_CHP             3.36    0.41  0.26  1.41       396       56   7.02
CC_CHP            10.15    7.47  0.69  0.29      1162      883   1.32
ST_GAS             0.75    1.38  0.61  0.11       155      220   0.71
solar             39.77   37.17  0.93  0.13     11385    10744   1.06
GAS TOTAL         76.46   88.01  0.83  0.11      9320    10803

2024            mdl TWh meas TWh    r  NRMSE  mdl band meas band band x
CC_REGULAR        57.37   40.82  0.74  0.26      6792     5174   1.31
CT_PEAKER          2.34    3.27  0.69  0.10       578      584   0.99
CT_CHP             3.34    0.38  0.24  1.42       397       53   7.47
CC_CHP             8.99    5.95  0.75  0.29      1028      709   1.45
ST_GAS             0.91    0.09  0.26  0.28       187       13  14.35
solar             47.58   44.74  0.92  0.15     13660    12695   1.08
GAS TOTAL         72.95   85.53  0.82  0.12      8982    10186

2025            mdl TWh meas TWh    r  NRMSE  mdl band meas band band x
CC_REGULAR        57.73   34.43  0.69  0.30      6509     4208   1.55
CT_PEAKER          1.97    1.65  0.43  0.11       477      248   1.92
CT_CHP             3.64    0.37  0.18  1.60       416       50   8.33
CC_CHP             8.66    6.09  0.89  0.25       983      712   1.38
ST_GAS             0.33    0.06  0.01  0.38        63        7   9.31
solar             53.34   49.66  1.00  0.03     15145    14144   1.07
GAS TOTAL         72.33   79.02  0.75  0.11      8448     9232
```

Two structural facts jump out and persist across all three years:
1. **CC_REGULAR over-runs (1.3–1.7×) and is too flat midday**, worsening as
   solar grows (band× 1.26 → 1.55, r 0.81 → 0.69).
2. **Gas TOTAL under-runs every year.** The floors are not hitting a gas total;
   they redistribute a short gas envelope into a flat midday slab.

---

## Lever A — gas commitment floor — **REMOVE**

**What it does.** `inject_caiso_gas_commitment_floor` imposes a hard `min_gen`
on the CC/CT gas fleet over h9–16 equal to **0.80 × the measured EIA-930 NG:NG**
month×hour-of-day profile, distributed cheapest-first by heat rate.

**Floor attribution (2024).** Target = **19.25 TWh forced midday** (mean 7 516
MW, peak 10 829 MW across h9–15) — ≈ 25 % of the model's whole-year gas. Because
it distributes cheapest-first, it lands on the lowest-HR units: CC_REGULAR
*and* the steam-credited CHP (it tops CT_CHP +~140 MW and CC_CHP +~70 MW midday).

**Shape evidence — CC_REGULAR diurnal (2024, MW/hour-of-day):**
```
hod        9    10    11    12    13    14    15
MEAS    3068  2979  2985  3086  3272  3629  4199     <- deep midday duck belly
baseline 6394  6353  6549  6712  6785  6700  6477     <- floor holds it ~2 GW high
no_gasfloor 4401 4277 4249 4248 4252 4275 4407       <- dip restored toward real
```
Turning the floor off: CC_REGULAR midday trough **6353 → 4277 MW** (real 2979),
hourly **r 0.74 → 0.82**, annual **57.4 → 53.4 TWh** (toward real 40.8). The
economic shape underneath the floor is markedly more faithful.

**It is a price lever, not a commitment.** With the floor **on**, midday LMP is
*lower* and more often ≤ $0, not higher:
```
                midday(h9-15) LMP mean   <=$0 share
gas floor ON  (baseline)      $29.78        13%
gas floor OFF (no_gasfloor)   $36.66         7%
```
So the floor manufactures CAISO's realistic ~$0 midday price by **forcing 19
TWh of gas long**, exactly the "long-midday floor … surplus exports/curtails at
~$0" its own docstring describes. That is the forbidden move: pin the fleet to
0.80 × its *measured* generation (a measured **outcome** with no forward
analogue — the builder returns `None` for any forecast year) to land the midday
price. Fails CLAUDE.md #11 (no pinning to measured generation) and #1 (price
reached by a non-real mechanism).

**Why removing it is right, and what replaces it.** A real RA must-offer
obligation is a *commitment* (the unit is online at **Pmin**, available to the
market), **not** an energy floor at 0.80 × measured output. CAISO's real midday
$0 comes from genuine oversupply — solar + imports + nuclear + run-of-river
hydro + true must-run **exceeding** load — and the surplus curtailing/exporting.
Replace with: (i) commit the RA fleet through the UC screen (min-up/down, Pmin)
and let it dispatch **down to Pmin** midday; (ii) get the $0 from real oversupply
(see Lever D — fix solar under-curtailment and let imports/solar set the midday
margin), not from a gas slab.

---

## Lever B — CT_PEAKER local-RA floor — **REPLACE (rip out the flat baseline)**

**What it does.** `inject_caiso_ct_reliability_floor` floors CT_PEAKER over
h15–22 at `frac = clip(0.049 + 0.047·(TMAX−25), 0.049, 0.46) ×` available
capacity.

**Floor attribution (2024).** Binds 2 928 hours; **61 % of binding hours sit at
the bare 0.049 flat baseline** — i.e. the dominant component is a year-round
*constant* CF floor, not the weather-responsive limb.

**Shape evidence — CT_PEAKER diurnal (2024, MW/hour-of-day):**
```
hod       14    15    16    17    18    19    20    21
MEAS     261   392   671   967  1068   966   752   532    <- sharp h18 evening peak
baseline  32   771   777   785   794   797   790   789    <- FLAT rectangle h15-22
no_ctfloor 32   41    59   105   131   149   128   122    <- peaky shape, but collapses
```
The floor turns a sharp evening-peak **triangle** (real h18 = 1068 MW) into a
**flat 771–797 MW rectangle**. Turning it off, the shape becomes *correctly
peaky* (max migrates to h18–19) **but collapses to 0.3 TWh** (real 3.27): the
economic merit order sends the evening-ramp energy to cheaper CC / imports, not
to the peakers.

**Verdict.** The temperature limb (39 % of binding, regressed CF vs TMAX,
forward-derivable, condition-responsive) is admissible. The **flat 0.049
baseline is not** — it is a constant tuned to the cool-day median CF (a level
target) and it is what makes the rectangle. Replace with a **net-load-ramp-shaped
RMR/local-capacity commitment** for *named* LA-Basin / Big-Creek-Ventura /
Bay-Area pocket units, binding in their real evening-ramp hours and **peaking at
h18–19, not flat across h15–22**.

**Discovered bug (do not paper over).** The collapse to 0.3 TWh when the floor
is off is the real defect: the evening-ramp scarcity that should make peakers
inframarginal isn't in the model, so cheap CC/imports serve the ramp instead.
Root-cause work: scarcity/ORDC-style evening pricing and/or evening import
availability — fix that so peakers clear on **merit** in the ramp, then the RMR
floor only has to cover genuine local must-run.

---

## Lever C — CHP bands + EOR heat-rate fix — **KEEP EOR fix; re-derive CHP level**

**EOR HR correction** (`CAISO_EOR_TOPPING_FACTOR` 1.8× on plants 10496/50134/
52169): lifts three Kern-County EOR cogens from their steam-credited EIA-923 HR
to a power-only (topping-cycle) basis so they clear like peakers, not baseload.
Physically grounded and forward-derivable. **Admissible — keep.** (CEMS coverage
of these three is thin, so it can't be validated on shape directly.)

**CC_CHP** (model 9.0 vs measured 6.0 TWh, 2024). The flat band **shape is
real** — Elk Hills (3.9 TWh) and Los Medanos (3.5 TWh) are large baseload cogens
that genuinely run flat (r 0.75–0.89). The issue is **level**: ~36–45 % over,
with no evening rise the real units show. Re-derive the CHP must-run CF/capacity
from the measured cogen output rather than a flat ~1 045 MW slab.

**CT_CHP** (model 3.3 vs CAMPD-mapped 0.41 TWh; r 0.18–0.26). The measured side
is **CEMS-coverage-limited** — most CT_CHP plants are small (<25 MW) QF cogens
below the CEMS threshold, so 0.41 TWh under-counts reality; treat the *level*
gap cautiously. But the **shape is genuinely wrong**: a flat ~400 MW band, and
the lever-off probe shows ~140 MW of that midday band is the **gas commitment
floor** topping the cheap CHP units (removed when Lever A is removed). The
remaining ~270 MW all-day baseline is a CHP must-run floor that should be shaped
to real host-steam behaviour, not held flat.

---

## Lever D — solar overrun / negative offers — **KEEP offer; fix under-curtailment**

**The overrun is under-curtailment, quantified exactly.** CAISO publishes
solar curtailment; the model is handed *uncurtailed potential* (HSL) and is
supposed to re-curtail endogenously:

```
year  model solar  EIA-930 delivered  CAISO curtailment  delivered+curt (=potential)
2023     39.77           37.17              2.51                 39.68
2024     47.58           44.74              3.19                 47.93
2025     53.34           49.66              2.52 (partial)       52.18
```

**The model dispatches solar ≈ the full uncurtailed potential every year,
curtailing ≈ 0** — the over-run (model − delivered) is essentially the *entire*
real curtailment volume (2.5–3.2 TWh/yr). Solar diurnal shape is otherwise
excellent (r 0.92–1.00).

**Negative offers are a minor contributor.** Disabling them (`no_negoffer`)
recovers only **0.6 TWh** of the ~2.8 TWh overrun (47.6 → 47.0 TWh). Even at
MC = 0 the model runs solar to the cap because nothing forces midday
curtailment. CAISO's real curtailment is ~70 % **local** (distribution/
sub-area congestion) — which the reduced 3-zone topology cannot see — plus
system oversupply.

**Verdict.** Keep negative offers as a real price mechanism (RPS/PTC
keep-running value), but it is **not** the solar fix and marginally worsens the
overrun. Fix the under-curtailment at root: represent the midday
oversupply/local-congestion that forces curtailment (the structurally correct
path), with "cap solar at delivered for backcast" as an explicitly-labelled
interim stopgap (already flagged as the `IMPORT_TRANCHES["CAISO"]`
"delivered-not-potential" P6 item). Curtailment is a market **behaviour** to
reproduce, not to suppress.

**IMPLEMENTED (Step D, 2026-06-27).** A structural local-deliverability derate
(`transmission.caiso_solar_deliverability_derate`, CAISO default-ON, the solar
analogue of the WECC corridor ATC derate) re-curtails the HSL potential off the
forward solar-penetration signal. Solar TWh now lands on delivered with curtailment
**2.42 / 3.34 / 2.96 TWh emerging endogenously** (real 2.51 / 3.17 / 2.52), r ≥ 0.93,
band× → ~1.0. The midday ~$0 price did **not** return — diagnosed as gated by the
midday CC over-run (fact #1), not solar — handed to the CC-back-down step. Full
write-up: `docs/caiso-lever-d-solar-curtailment-2026-06.md`.

---

## Lever E — interchange levers — **KEEP (separate check warranted)**

Per-hub signed intertie, import-gas coupling, measured-p95 corridor import/export
caps, and the monthly gas-hub-basis overlay each track a **measured capability or
price** (measured hub basis, measured ATC, signed corridor netting) and are
forward-derivable. None is implicated in the thermal-shape complaints; they
shape interchange/price, not the diurnal thermal allocation. They warrant their
own net-interchange-shape check (model net import diurnal vs EIA-930 interchange)
but are not shape-faking levers and are out of scope for this thermal-shape pass.

---

## Prioritized overhaul plan

Rip out the fitted bands in this order; each is a structural fix, judged on shape
not total. Expect class **totals to drop** when the bands come out — that is the
discovered bug to fix at root, never to re-bury in a floor (CLAUDE.md #1/#11).

1. **Remove the gas commitment floor (A) first.** It is the single largest
   distortion (19 TWh midday, a measured-outcome pin doing price work). Replace
   with a Pmin RA commitment via the UC screen. *Expected:* CC_REGULAR midday
   trough deepens toward real (6.4 → ~4.3 GW at h10), hourly r 0.74 → 0.82;
   midday $0 prices must then come from Lever D, not the slab.

2. **Rip out the flat 0.049 CT_PEAKER baseline (B); keep only the temp limb,
   reshaped to the net-load ramp.** Make local-RA a named-unit RMR that peaks
   h18–19. *Expected:* CT_PEAKER stops being a rectangle; the residual collapse
   to 0.3 TWh exposes the evening-scarcity bug to fix next.

3. **Fix evening-ramp scarcity pricing / import availability** (the root cause
   B exposes). Peakers should clear inframarginally in the ramp on merit so the
   RMR floor only covers true local must-run. This is the real replacement for
   both A's and B's energy.

4. **Fix solar under-curtailment (D)** — add the midday oversupply/congestion
   curtailment mechanism (interim: cap at delivered). Lets solar+imports set the
   midday margin and supplies the real $0 price A was faking.

5. **Re-derive the CHP must-run level/shape (C)** from measured cogen output;
   keep the EOR HR fix. Lower CC_CHP ~36 % and reshape CT_CHP off the flat band.

6. **(Lower priority) interchange-shape check (E)** — confirm net-import diurnal
   vs EIA-930 once A/D change how long the model sits midday.

**Not a keeper.** This pass produced no dashboard run by design; the lever
changes belong to a follow-up calibration session once the plan is agreed.

```
Reproduction: scratch scripts in the session scratchpad —
shape_probe.py (per-class diurnal + metrics), probe_compare.py (lever-off
overlays); probes under resolve/{caiso,probe_nogasfloor,probe_noctfloor,
probe_nofloors,probe_nonegoffer}.
```
