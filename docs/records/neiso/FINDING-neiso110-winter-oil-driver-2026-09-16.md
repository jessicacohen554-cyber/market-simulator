# FINDING — neiso-110: what drives ISO-NE's winter oil burn

**Session** neiso-110 (NEISO calibration lane), 2026-09-16.
**Charter** `docs/CHARTER-neiso110-winter-oil-driver-2026-09-16.md`.
**Keeper (control)** `2026-09-16-neiso109-gas-repair`, bundle
`results/calibration/neiso109_gasrepair_span`, years 2020–2025.
**LP SPENT: ZERO.** Phase 0 killed the arm; rule 29 `[R-SCREEN]`'s zero-LP phase 0
answered every question this session was opened to ask. No shard was launched, no
screen was solved, no control was spent, and the keeper is UNCHANGED.

---

## 0. HEADLINE

1. **The null is DEAD, and not merely insufficient — it is COUNTERPRODUCTIVE at the
   one event it would have to explain.** `dual_fuel_oil_daily_parity` *raises* the
   oil parity price on every day of Winter Storm Elliott, because distillate and gas
   both get dearer in a cold snap.
2. **The charter's hypothesis SURVIVES.** ISO-NE's winter oil burn is not produced by
   hourly gas/oil price parity. On the twelve largest actual oil-burn days of 2022,
   delivered gas sat **$3.69–$8.44/MMBtu BELOW** oil parity. The economic signal
   pointed the *opposite way* from what the fleet actually did.
3. **The defect is TWO independent defects, not one**, and they need different fixes.
   The charter treated the oil miss as a single allocation error; it is not.

## 1. THE CHARTER'S STATED PREMISE IS WRONG — CORRECTED HERE

The charter §4 and the session prompt §2 both state that the oil side of the parity
test is *"an ANNUAL constant (`resolve_annual_oil_price`: 18.00 in 2023/2024, 20.64 in
2025)"*, and name that grain mismatch as the null.

**It is not.** `data/fuel/dual_fuel.py::dual_fuel_oil_price_series` reaches
`resolve_annual_oil_price` **only when `config.mode == "forecast"`**. The keeper is
`mode="backcast"`. In backcast the oil side is the **measured monthly EIA-923
Schedule-5 delivered petroleum receipt series** (`iso_monthly_oil_prices`), with the
flat `OIL_PRICE_PER_MMBTU` = 18.0 filling only unreported months. NEISO reports in
every month of every year 2020–2025, so **the fallback is never reached**.

Measured F923 monthly oil parity, $/MMBtu (this is what the keeper actually used):

| year | Jan | Feb | Mar | … | Dec | annual mean |
|---|---:|---:|---:|---|---:|---:|
| 2020 | 17.66 | 15.84 | 16.37 | … | 13.35 | 11.764 |
| 2021 | 13.28 | 14.40 | 15.18 | … | 18.63 | 16.457 |
| 2022 | 27.29 | 21.95 | 32.90 | … | 20.98 | **29.188** |
| 2023 | 19.78 | 18.43 | 14.86 | … | 20.72 | 18.752 |
| 2024 | 18.45 | 11.89 | 14.14 | … | 14.14 | 13.679 |
| 2025 | 18.39 | 16.19 | 11.18 | … | 16.49 | 14.697 |

The prompt's own sizing figures (*"2023 mean 18.752 (range 12.408–22.020)"*) are this
series — a **range**, which a constant cannot have. The premise contradicted its own
evidence. The real grain question is **monthly vs daily**, not annual vs daily, and it
is far smaller than the charter assumed.

## 2. THE NULL, REFUTED STRUCTURALLY (rule 1 `[R-STRUCT]` — not on the residual)

`dual_fuel_oil_daily_parity` multiplies the monthly oil plateau by a **mean-preserving**
within-month daily shape built from measured NY Harbor ULSD spot quotes.

**(a) It is byte-identical in 2020 and 2021.** `data/raw/oil-prices/ny_harbor_ulsd_daily.csv`
carries quotes for **2022–2025 only**. `oil_daily_shape_factors` returns all-ones for
an uncovered year, so the arm cannot change a single hour of 2020 or 2021 — two of the
five years the model is short. Verified: `np.array_equal(off, on) == True` for both.

**(b) It adds ZERO parity-crossing hours in any year, and REMOVES 120 in 2025.**

| year | crossing hours OFF (keeper) | crossing hours ON (arm) | Δ |
|---|---:|---:|---:|
| 2020 | 0 | 0 | 0 |
| 2021 | 0 | 0 | 0 |
| 2022 | 48 | 48 | 0 |
| 2023 | 0 | 0 | 0 |
| 2024 | 24 | 24 | 0 |
| 2025 | 792 | 672 | **−120** |

**(c) It moves the price the WRONG WAY at Elliott.** The ULSD daily shape factor on
2022-12-24…27 is **above 1.0** — distillate got *dearer* in the cold snap, exactly as
physics says it should:

| day | shape factor | oil parity OFF | oil parity ON | gas | still short by |
|---|---:|---:|---:|---:|---:|
| Dec 24 | 1.0407 | 20.985 | **21.839** | 15.047 | 6.793 |
| Dec 25 | 1.0407 | 20.985 | **21.839** | 15.080 | 6.759 |
| Dec 26 | 1.0407 | 20.985 | **21.839** | 13.570 | 8.269 |
| Dec 27 | 1.0779 | 20.985 | **22.620** | 12.543 | 10.077 |

The required move at Elliott is a **$5.91/MMBtu LEVEL** change (+39.2% on peak gas).
The largest downswing the daily shape offers anywhere in 2022 is 22.4%, and on the
Elliott days themselves the shape is an **upswing**. No grain fix reaches it.

**The null is refused on structure, not on fit.** It is not that it fails to close the
residual — it is that the mechanism's own arithmetic moves oil away from the event.

### 2.1 An honest tension, recorded rather than resolved here

The daily ULSD shape **is** measured and **is** more accurate than a monthly plateau,
so rule 14 `[R-ACCURATE]` argues for arming it **on its own merits, independent of the
residual**. This session does **not** arm it, for two reasons stated plainly: it has no
2020/2021 coverage (inconsistent treatment across the span), and arming it today —
when its only measurable effect is to shave 120 hours off the single **overshoot** year
— would be indistinguishable from residual-shaving and would violate rule 1
`[R-STRUCT]`. It belongs to a future lane with its **own accuracy-motivated PRECOMMIT**
and its own screen year, and must never be sold as the oil driver. Cell recorded
accordingly (§6).

## 3. WHAT ACTUALLY HAPPENED — THE MEASURED RECORD

Hourly CAMPD, six New England states (CT/MA/ME/NH/RI/VT), 2022. Oil-attributed
generation = units whose `primaryFuelInfo` is Diesel/Residual/Other Oil, plus gas units
whose hourly CO2 rate falls in the distillate band (68–90 kg/MMBtu at heat input > 5).
Detector reproduces **1.9635 TWh against the bench actual 1.8521** (+6.0%), so it is
sound for shape; the level is not relied on.

**Monthly 2022 (TWh):** Jan **1.061 (54%)** · Feb 0.181 · Jul+Aug 0.163 (**8%, summer**)
· **Dec 0.499 (25%)**, of which **Dec 23–27 = 0.430 — 86% of December in five days.**
The four largest oil days of the entire year are **Dec 24, 25, 26, 27** — Elliott.

**The price signal on those same days:**

| date | actual oil (TWh) | gas $/MMBtu | oil parity | gas − oil | model switches? |
|---|---:|---:|---:|---:|:--|
| 2022-12-24 | 0.10677 | 15.05 | 20.98 | **−5.94** | no |
| 2022-12-25 | 0.09998 | 15.08 | 20.98 | **−5.90** | no |
| 2022-12-26 | 0.09799 | 13.57 | 20.98 | **−7.41** | no |
| 2022-12-27 | 0.08238 | 12.54 | 20.98 | **−8.44** | no |
| 2022-01-16 | 0.06939 | 22.61 | 27.29 | **−4.68** | no |
| 2022-01-27 | 0.06401 | 22.46 | 27.29 | **−4.82** | no |

**Not one of the twelve largest actual oil days crosses parity.** The two days the model
*does* switch — Feb 3 and Feb 14 — together carry **1.26%** of the year's actual oil
burn, and Feb 3 had essentially none (0.00018 TWh) while the model switched on it.

The July/August burn (0.163 TWh) settles it independently: 2022 summer gas ran
$6–8/MMBtu against a **$44.85/MMBtu** July oil parity. That is periodic dual-fuel
firing/testing — an obligation, at a price ratio no economic model would ever produce.

**Why 2022 and not 2025:** in reality the switching was driven by gas being *physically
unavailable* (pipeline-constrained at Elliott), not dear. The parity test substitutes a
**price** signal for an **availability** constraint. That is the charter's hypothesis,
now localized to a specific line of code.

## 4. THE DEFECT IS TWO DEFECTS

Decomposition, TWh. Actual oil-fleet is measured directly from CAMPD; actual dual-fuel
is **inferred by difference** from the bench total (so it inherits any CAMPD↔bench
boundary mismatch — direction is reliable, the last decimal is not). Model columns split
the keeper's own `oil` class by whether the hour is a parity crossing.

| year | ACTUAL oil-fleet | ACTUAL dual-fuel | ACTUAL total | MODEL oil-fleet | MODEL switched | MODEL total |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 0.1348 | 0.0142 | 0.149 | 0.0015 | 0.0000 | 0.0015 |
| 2021 | 0.2070 | 0.0320 | 0.239 | 0.0212 | 0.0000 | 0.0212 |
| 2022 | 0.8775 | 0.9745 | 1.852 | 0.0456 | 0.0850 | 0.1307 |
| 2023 | 0.2601 | 0.1299 | 0.390 | 0.0035 | 0.0000 | 0.0035 |
| 2024 | 0.2781 | 0.0339 | 0.312 | 0.0033 | 0.0452 | 0.0484 |
| 2025 | 0.8088 | 0.1002 | 0.909 | 0.0429 | 2.3532 | 2.3961 |
| **Σ** | **2.5663** | **1.2847** | **3.851** | **0.1180** | **2.4834** | **2.601** |

### DEFECT A — the real oil-fired fleet barely dispatches. Right shape, wrong level.

ISO-NE carries a **~4,000–4,800 MW oil-fired fleet** (CAMPD nameplate proxy) running at
a measured capacity factor of **0.3%–2.2%**. The model reproduces **4.6%** of its
energy — 0.118 TWh against 2.566 TWh over six years, a shortfall of **10×–90×** every
single year.

Critically, **correlation(actual, model) = +0.923**: the model knows *which years* are
heavy oil years and gets the *level* catastrophically wrong. That is a scaling /
commitment defect, which is a well-posed problem — not a shape mystery.

**This defect alone accounts for the shortfall in all five short years.** At
$21–29/MMBtu × a ~10 MMBtu/MWh heat rate the fleet sits at $210–290/MWh, far out of
merit; a perfect-foresight energy-only LP will never commit it. Real ISO-NE runs it for
fuel-security posture, local reliability and reserve.

### DEFECT B — the dual-fuel parity switch fires in the wrong years.

**correlation(actual, model) = −0.119.** The channel carries roughly the right six-year
total (2.48 TWh model vs 1.28 TWh actual, ~2× over) and distributes it almost inversely:

* **2022** — actual 0.975 TWh, model 0.085 TWh (**11.5× short**)
* **2025** — actual 0.100 TWh, model 2.353 TWh (**23.5× over**)

**98.2% of the model's 2025 oil is re-attributed switched gas**, not oil-fleet dispatch.
The single overshoot year in the whole window is this one channel misfiring.

## 5. RULE-19 `[R-ONE-MECH]` ENUMERATION — WHAT ALREADY FLOORS OIL

**Nothing does.** Measured from the keeper's own committed
`legitimacy_diagnostics.json` D-2 forced-energy attribution:

| mechanism | classes it forces | 2022 forced TWh |
|---|---|---:|
| `nuclear_mustrun` | (nuclear) | 27.09 |
| `reliability_floor` | CC_REGULAR, CT_PEAKER | 0.63–0.85 |
| `chp_steam` | CT_CHP | 0.023 |
| `winter_fuelsec_mustrun` | **COAL, ST_GAS only** | **0.0442** |

D-2 carries **four** mechanisms and **zero rows on any oil class**; D-1's class set
(`CC_CHP, CC_REGULAR, COAL_BIT, CT_CHP, CT_PEAKER, OTHER_FOSSIL, ST_GAS`) contains **no
oil class at all**.

The winter fuel-security must-run is **not dormant** — the C3c ledger's "DORMANT"
characterization is imprecise at D-2 resolution. It binds every year (0.026–0.057 TWh)
and it is **mis-targeted**: `_WINTER_FUELSEC_CLASSES = ("COAL", "COAL_BIT", "ST_GAS")`
excludes the oil-fired fleet entirely.

Its own docstring states the intended chain: *"it postures the fuel-secure classes at
minimum-stable on winter cold days, **at which point the dual-fuel oil limb burns on the
acute snaps** and the Component-A budget can bind."* **The chain is broken at the second
link.** Committing the steam fleet produces no oil, because the oil limb is gated on a
parity test the real event fails by $5.90/MMBtu. Component A's inventory budget is
therefore inert **as a consequence of Defect B**, not as an independent failure.

## 6. RULE-28 `[R-MECH-MATRIX]` — THE CHARTER'S BLOCKER DOES NOT EXIST

The charter §4 records a BLOCKER: six mechanisms *"have a row in `mechanism-matrix.js`
but NO CELL in `mechanism-matrix/NEISO.js`"*. **That is false at this head, and no
reconstruction work was needed.**

All 346 base rows carry a NEISO cell; the only base ids without one are the **14
category headers** (`structure`, `price`, `reserves`, …), which are not mechanisms. The
six fields are covered by **three** rows, because matrix row ids are not ScenarioConfig
field names — the rule-28(c) census close by **neiso-78 (2026-08-03)** registered the
family members literally inside each row's `def`:

| field | covering row | NEISO cell |
|---|---|---|
| `neiso_winter_fuel_mustrun`, `_inventory`, `neiso_oil_burn_budget`, `_fuelsec_*` | `winter_fuelsec_posture` | **K** |
| `dual_fuel_switching`, `dual_fuel_oil_daily_parity`, `dual_fuel_oil_reattribution` | `dual_fuel_switching` | **K** |
| `neiso_gas_coldsnap_derate` | `gas_coldsnap_derate` | **K** |

What *is* true, and weaker than the charter's claim: those three cells are bare
`{ cell: "K" }` with **no `ev` citation**, so the evidence lives only in the base row's
`def`/`note`. This session adds the `ev` for the `dual_fuel_switching` row recording the
zero-LP adjudication above. The daily-parity limb is recorded **REFUTED AS THE OIL
DRIVER**, and explicitly **still UNTESTED as a rule-14 accuracy improvement** (§2.1) —
those are different questions and are not conflated.

## 7. G-DRIFT — form 4 VALID, no control LP spent

Rule 29 `[R-SCREEN]` (b). `git diff b6ded93731fec2a0680a6bb7bf30d6c7caab7656 HEAD --
src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` → 37 files, +2,776/−75.

| file(s) | subject | verdict |
|---|---|---|
| `model/lp/{rows,bounds,costs,layout,model}.py`, `model/lp/hydro_cascade.py` | hydro cascade coupling | **INERT** — gated `hydro_cascade_coupling: bool = False`, absent from keeper recipe |
| `data/coal_fuel_inventory.py`, `data/coal_receipts.py`, LP coal rows | coal fuel inventory | **INERT** — gated `coal_fuel_inventory: bool = False`, absent from keeper recipe |
| `data/hydro.py`, `pipeline/{kwargs,spec}.py`, `runner.py` | cascade wiring (NWPP) | **INERT** — reached only under the cascade gate |
| `data/eia930/{actuals,envelopes,frames}.py` | NWPP pool frames + SOCO | **INERT** — NWPP/SOCO-scoped; corroborated mechanically below |
| `data/renewables.py`, `data/fuel/basis/meanzero.py` | SOCO renewables / basis | **INERT** — SOCO-scoped, new module |
| `data/fleet/offer_surfaces.py` | PJM min-load rung targeting | **INERT** — PJM-only, gated `pjm_offer_midcurve_minload_segments` default off |
| `config/paths.py`, `config/scenarios.py` | SOCO/NWPP paths + the two gates above | **INERT** |
| `scripts/run_calibration{,_full}.py` | CLI wiring for the two gates | **INERT** |
| `scripts/lib/keeper_store.py` | `DEFAULT_ISO_ORDER` append `"SOCO"` | **INERT** — display order; NEISO's index unchanged |
| `data/raw/_validation-source/calibration_reference.json` | +296 lines | **INERT** — **22 SOCO lines, 0 NEISO/ISNE lines** |
| `data/raw/reference/soco_seam_*.csv`, `coal-shared-storage-crosswalk.csv` | new SOCO inputs | **INERT** |

**MECHANICAL CORROBORATION (stronger than the reading).** `surface_stamp("NEISO", keeper_config)`
recomputed at HEAD `06268d5c`:

```
HEAD   : {"schema":1,"iso":"NEISO","fingerprint":"9d35c270c69e9eee","rows":197,"moved":{}}
KEEPER : {"schema":1,"iso":"NEISO","fingerprint":"9d35c270c69e9eee","rows":197,"moved":{}}
```

**Byte-identical fingerprint, identical row count, `moved_rows("NEISO") == {}`.** All
hunks INERT ⇒ form 4 valid ⇒ **the keeper's committed bundle IS the control**. Zero
control LP spent. (neiso-109 measured NEISO HEAD drift at exactly zero; it is still
exactly zero, so the charter's "a non-zero drift is itself a finding" does not fire.)

## 8. WHAT THIS SESSION DOES NOT CLAIM

* **No determination moves, and none was sought.** Oil sits below C1 materiality
  (~0.1–2.4 TWh against ~59 TWh of gas). The keeper reads CALIBRATED on all six years
  and still does; the oil miss stays ledgered in `calibration_attestation.json` as a
  MODEL MISS, not a caveat, spending no caveat slot.
* **No lever is proposed.** Rule 17 `[R-FLOOR-WINDOW]` requires a driver, a binding
  window and a forward story. This session can state the driver (WRP / IEP / OFSA
  posture and pipeline non-availability) but **cannot yet state the window**: the real
  oil fleet runs at a 0.3–2.2% capacity factor, so a naive extension of
  `_WINTER_FUELSEC_CLASSES` to the oil classes at 40% min-stable across all cold winter
  days would overshoot by more than an order of magnitude. Naming that as a lever
  without deriving its window from the unit record would be exactly the unjustified
  floor rule 17 forbids. **The window is the next lane's first deliverable.**
* **Nothing is tuned.** No adder, haircut, offset or rescaled input was introduced. The
  1.7 TWh 2022 gap is reported at full magnitude and remains open.
* **The gas repair is untouched** (rule 14 `[R-ACCURATE]`), as is the keeper.

## 9. WHAT THE NEXT LANE SHOULD DO

Ordered by evidence strength, not by residual size:

1. **Defect A first.** It is year-invariant, explains five of six years, has
   correlation +0.923 (right shape, wrong level), and is a commitment question with a
   measurable answer. **Derive the binding window from the CAMPD unit record** — which
   oil units ran, in which hours, at what load fraction, against ISO-NE's published
   WRP/IEP obligation periods. That derivation is the rule-17 (b) window and it is
   pure data prep, zero LP.
2. **Defect B is a quantity constraint wearing a price mask.** Any fix belongs on the
   **gas-availability** side (pipeline nomination / interruptible transport), not on
   the oil-price side. A per-plant delivered oil price and a burner-tip gas adder —
   the charter's other two price-construction candidates — are the same class of
   answer as the null and will fail the same way: they are level shifts of a few
   $/MMBtu against a $5.90 level gap whose sign is set by availability, not price.
3. **Do not re-run the null.** §2 is a complete structural refutation. Rule 28(a)'s
   DO-NOT-REDO applies.

---

**Artifacts:** none to promote — no solve was run, so there is no bundle, no
registration and no promotion question (rule 31 `[R-RETAIN]` has nothing to retain).
The keeper `2026-09-16-neiso109-gas-repair` is unchanged and remains NEISO's designated
keeper across all six years {2020, 2021, 2022, 2023, 2024, 2025}.
