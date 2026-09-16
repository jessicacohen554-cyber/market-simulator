# PRECOMMIT — neiso-110: condition the cold-snap derate's dual-fuel exemption

**Session** neiso-110 · **ISO** NEISO · **Written BEFORE any solve.**
**Control** the keeper's committed bundle — `2026-09-16-neiso109-gas-repair`,
`results/calibration/neiso109_gasrepair_span`, years 2020–2025. **No control LP is spent**
(G-DRIFT form 4 valid, §4).
**Phase-0 evidence** `docs/FINDING-neiso110-winter-oil-driver-2026-09-16.md`.

---

## 1. THE ARM — ONE GATE, ZERO NEW PARAMETERS

`neiso_coldsnap_derate_dualfuel_unswitched: bool = False` → `True`.

This is a **scope correction to `neiso_gas_coldsnap_derate`**, not a mechanism beside it
(rule 19 `[R-ONE-MECH]`). It adds **no floor, no curve, no scalar**, and leaves every
coefficient of the parent derate untouched — `t0 = −7.0 °C`, `slope = 0.018/°C`,
`cap = 0.20` — so rule 23 `[R-FROZEN-DERIVE]` is not engaged. It changes only **which
unit-hours the one existing derate reaches**.

**The defect it repairs is a premise stated as a fact.** The parent derate exempts every
EIA-860 dual-fuel unit, and its own docstring gives the reason: *"they keep running on
distillate when gas is short — that switch is already modelled by `apply_dual_fuel_pricing`
(their marginal cost becomes the oil parity), so derating them too would double-count the
constraint."* But that switch is `mc = min(gas, oil)`: it fires **only where delivered gas
has reached the oil parity**. Where it has not, the unit is burning pipeline gas — the very
commodity the derate says it cannot get — and the exemption removes nothing while
double-counting nothing.

**Measured on the keeper, zero LP** (FINDING §3–§4): across Winter Storm Elliott
(2022-12-23…27) Algonquin gas ran **$12.54–15.08/MMBtu** against an oil parity of
**$20.985** — the switch is **$5.9–8.4/MMBtu from firing** — while **6,896 MW, 39.3 % of
NEISO gas capacity**, sat exempt. Over those five days the model produced ~730 GWh of
gas-fired energy against a measured **339 GWh**, and **0.82 GWh** of oil against a measured
**429.62 GWh**.

**Rule 17 `[R-FLOOR-WINDOW]` — inherited unchanged from the parent, not newly asserted:**
* **(a) DRIVER** — the gas-electric pipeline constraint in deep cold (NERC/FERC Winter
  Storm Elliott analysis). Identical to the parent's. It is the *exemption* that has no
  driver evidence behind it.
* **(b) WINDOW** — identical: `NEISO_COLDSNAP_FLOOR_HOURS` (hours 6–9, 17–20) on days whose
  NEISO load-weighted daily TMIN falls below `t0`. No new window is introduced.
* **(c) FORWARD** — identical: regenerates from a forecast year's pinned TMIN, and the
  switch condition regenerates from the same forward gas/oil series the parity test already
  uses.

**The property that bounds it, and why it cannot overreach:** where the premise holds, the
arm is **byte-identical** to the legacy exemption — proven, not asserted
(`tests/iso/neiso/test_neiso_coldsnap_dualfuel_exemption.py::test_switch_always_active_is_byte_identical_to_legacy`).
It can only remove an exemption that was **never earned**. It never widens the derate to a
unit whose oil limb is genuinely carrying it, and it never touches a non-dual-fuel row.

## 2. SCREEN YEAR — **2022**, ON THE MECHANISM'S OWN FOOTPRINT

Rule 29 `[R-SCREEN]` requires the screen year be the year the **mechanism's own measured
footprint is largest**, never the year with the biggest residual. The footprint here is
exactly computable with no solve: exempt MW × derate fraction × cold-snap window hours in
which the switch is **not** active.

| year | window hours with `frac > 0` | of those, switch inactive | capacity-hours removed |
|---|---:|---:|---:|
| 2020 | 144 | 144 | 53.8 GWh |
| 2021 | 184 | 184 | 65.2 GWh |
| **2022** | **336** | **328** | **164.1 GWh** |
| 2023 | 72 | 72 | 36.3 GWh |
| 2024 | 144 | 144 | 45.8 GWh |
| 2025 | 304 | **168** | 54.9 GWh |

**2022 wins by 2.5×** over the next-largest year. **Stated plainly because it matters:**
2022 is *also* the largest-residual year, and that coincidence is not the reason it was
chosen — the quantity in the last column is computed from the temperature series, the window
constant and the gas/oil comparison, and contains no residual term of any kind. Had the
footprint ranking favoured another year, the screen would run there.

2025 is the discriminating row: its window hours drop **304 → 168** under the conditioning,
because 2025 is the one year the switch genuinely fires (792 crossing hours). The
conditioning is doing real work, not acting as a blanket removal.

## 3. STOP GATES — STRUCTURAL, PRE-REGISTERED, AND ABLE TO PASS ON A CORRECT ARM

Rule 29: the screen **may kill the arm; it may never promote it.** No gate below reads the
oil residual, the price residual, or any scored criterion as a target. Written to avoid the
neiso-109 failure mode the charter names — a gate that fires on the arm's own correct
behaviour.

| # | gate | passes if | kills the arm if |
|---|---|---|---|
| **G1** | **Footprint identity** | derated dual-fuel capacity-hours land within **±2 %** of the pre-solve 164.1 GWh prediction | off by >2 % → the mechanism is not doing what its arithmetic says |
| **G2** | **Window confinement** | **zero** availability change outside `NEISO_COLDSNAP_FLOOR_HOURS` ∩ `TMIN < t0` ∩ switch-inactive. Measured on the **availability array**, not on prices | any touched hour outside the declared window (rule 17) |
| **G3** | **Exemption purity** | in hours where the switch **is** active, dual-fuel availability is **bit-identical** to the control | any change there → the correction overreached its own premise |
| **G4** | **Non-dual invariance** | non-dual-fuel rows **bit-identical** to the control in all 8,760 hours | any change → the scope correction leaked |
| **G5** | **Direction** | model oil energy **rises** and model gas energy **falls**, both non-trivially (>10 % of their own control value) | oil falls, or gas rises → the response contradicts the mechanism |
| **G6** | **No load-bearing regression** | no non-target load-bearing criterion (C1/C2/C3a/C3b) flips PASS → FAIL | any such flip |
| **G7** | **Feasibility** | slack and dump do not **increase** vs the control | either rises → capacity was removed past feasibility |

**G7 is stated as a delta against the control on purpose.** neiso-109 wrote an absolute
"slack = dump = 0 in both legs" gate on a year whose control already dumps 1,380.617467 MWh
against a negative zone demand; that gate failed on a correct arm. This one compares like
with like.

**G2 is measured on availability, not price.** The LP has a documented cyclic-storage
coupling that moves prices in untouched hours (~0.13 % of movement, energy-conserving to
0.007 %); a price-confinement gate would fire on that. The availability array is the object
the mechanism actually writes.

**What is NOT a gate:** whether the 1.72 TWh 2022 oil gap closes. It will not — the arm
addresses the *capacity-availability* half of the chain, and the FINDING's Defect A (the
real oil fleet dispatching at 4.6 % of actual, downstream of a price tail that reaches
$249 against an oil MC of $210–294) is a separate defect. **A screen that clears every gate
above while closing little of the residual is a PASS**, and the full span then measures how
much of the chain moves.

## 4. G-DRIFT — FORM 4 VALID, NO CONTROL LP

Established in FINDING §7 and unchanged: all 37 changed files between the keeper's
`basis_sha b6ded93731fec2a0680a6bb7bf30d6c7caab7656` and HEAD classify **INERT** (hydro
cascade and coal fuel inventory, both default-off gates absent from the recipe; SOCO/NWPP
scoping; a PJM-only offer gate; a `DEFAULT_ISO_ORDER` display append; and a
`calibration_reference.json` delta carrying **22 SOCO lines and 0 NEISO/ISNE lines**).

Corroborated mechanically: `surface_stamp("NEISO", keeper_config)` at HEAD reproduces the
keeper's stamp exactly — fingerprint `9d35c270c69e9eee`, 197 rows, `moved {}`.

**This session's own code changes are additive and default-off**, and the cache key proves
it: the field is registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`
at `"False"`, so the pinned default key is **unmoved** (`test_caiso_ra_mpb_anchor.py` passes)
and every existing bundle — every ISO's keepers included — keeps its key. An armed run earns
a distinct key.

## 5. EXECUTION

* **Screen**: ONE shard, `--year 2022`, arm only (the control is the keeper's committed
  bundle, §4). Rule 34 `[R-SHARD-PROMOTABLE]`: the shard **pushes its bundle** to its own
  branch via a `.gitignore` negation + plain `git add`, including `dispatch/2022_P1.parquet`.
* **Full span only if the screen clears every gate**: ONE shard, ONE
  `--year 2020 2021 2022 2023 2024 2025` invocation, ONE bundle (rules 16 / 32(b)), covering
  the full registry year union {2020, 2021, 2022, 2023, 2024, 2025}.
* **The parent runs zero LP** (rule 32(a)).
* **Nothing is deleted** until the owner rules on promotion (rule 31 `[R-RETAIN]`).

## 6. WHAT WOULD MAKE ME REPORT A NULL

If the screen clears G1–G4 (the mechanism does exactly what it claims) but G5 shows oil
essentially unmoved, the honest finding is that **the exemption was real but not
load-bearing** — the capacity it protected was not what kept the oil fleet out of merit, and
the residual sits entirely in the price-tail chain. That is a publishable result and it
would be reported as one, not re-cut until something moves.
