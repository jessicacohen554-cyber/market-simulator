# FINDING — miso-125: the split is backwards because a 250 MW steam turbine is missing, and eGRID has been paying its generation into a heat rate the LP charges to gas turbines that cannot produce it

**Date:** 2026-08-04 · **ISO:** MISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry AND at exit:** `2026-08-04-miso-124-dualfuel-rearm`
(`results/calibration/miso124_dualfuel_B`), `NOT-YET`, sole FAIL C7 `COAL_PRB`
×3y, ledgered caveats {C3a, C3c}. **UNCHANGED — nothing was armed, solved or
shipped.**

**Prereg (committed BEFORE any statistic, any derive and any solve):**
`results/calibration/PREREG-miso125-chp-prime-mover-split-2026-08-04.md`,
commit `77f18a37`.
**Probe (no LP):** `scripts/probes/_miso125_chp_prime_mover_split.py`.
**Records:** `results/calibration/_miso125_prime_mover_split.json`,
`PROBE-miso125-chp-prime-mover-split-2026-08-04.txt`.

**Rule 15 `[R-DASHBOARD]`, discharged explicitly: this session produced NO
run.** No LP was built, no solve was launched, no bundle was created and no
dashboard registration was made or is owed. The adjudication is entirely from
committed artifacts and published source data.

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **KE2** | how much of MISO does the grain defect actually reach? | **exactly one** applied multi-class plant: 55088, `CC_CHP` 350.0 + `CT_CHP` 165.0 = **515.0 MW**, both `ok`, both carrying the same plant-grain **6.9573** | **PASS** — defect confirmed, scope is one plant |
| **KE1** | does CAMPD resolve the prime movers at unit grain? | 6 units → **2 `CC` + 1 `CT` power-train, 3 dark boilers**; zero unmapped; CEMS total reconciles to the committed artifact at **1.000000** | **PASS** |
| **KE3** | is the split big enough to matter? | max \|rel delta\| **4.76 / 3.05 / 3.17 %** vs a pre-declared 2 % band | **LIVE** — but see the sign |
| **KE3 (sign)** | does it agree with turbine physics? | **`hr_CC` 7.09 > `hr_CT` 6.63** — a combined cycle measured *less* efficient than a simple-cycle turbine | **BACKWARDS** — denominator-defect signature |
| **KE4** | is the CHP class pinned, so the LP could not respond anyway? | **No.** `CC_CHP` cv 0.23, 1,084–1,563 distinct values; `CT_CHP` **8,466 distinct values in 8,760 h**; at-annual-min share ≤ 0.0009 | **NOT INERT** — the pre-declared marginality route does not fire |
| **KE-R** | is the construction's own stated assumption true? | eGRID `PLNGENAN` **5,259,825** net MWh ÷ CEMS power-train **gross** 3,648,140 = **1.4418**. Net cannot exceed gross. Implied CF on the LP's 515 MW = **116.6 %** | **REFUTED** |
| — | what is the missing machine? | EIA-860 **`ST1`**: prime mover **`CA`**, Unit Code **`SINT` shared with the two NG `CT` turbines**, **250 MW**, Energy Source 1 **`BFG`** — no CEMS stack, no fleet row | the boundary, named |
| — | the outcome | **no derive change, artifact byte-identical, keeper untouched** | `R` on the repair, **zero solves** |

---

## §1 — the defect is real, and it is exactly where miso-118 said

`scripts/data/derive_chp_power_only_heat_rates.py` writes **one row per
`(plant_code, plant_group)`**, and
`market_sim.data.fleet.campd_bins.measured_chp_heat_rates` applies it on that
**pair** — its docstring is explicit that "one plant can host more than one CHP
class". But the *rate* comes from `egrid_chp_split(vintage)`, which is
**plant**-grain. The row keying advertises a per-class rate the derive never
computes.

KE2 measured the blast radius, and it is one plant. Of MISO's four multi-class
plants (50973, 55088, 56309, 58161), three are `not_unfired_topping` on **every**
row and so apply nothing. Only **55088 Dearborn Industrial Generation** is `ok`
on both:

| class | capacity | applied rate | eGRID credited |
|---|---|---|---|
| `CC_CHP` | 350.0 MW | **6.9573** | 6.3464 |
| `CT_CHP` | 165.0 MW | **6.9573** | 6.3464 |

`measured_chp_heat_rates = True` on the keeper, so both are live in the LP
today. 6.9573 sits at the **bottom of MISO's `CC_CHP` `ok` band** (6.96–11.21)
and **below the entire `CT_CHP` band** (8.05–12.42) — the blend charges a
165 MW simple-cycle turbine a combined-cycle heat rate.

## §2 — the pre-registered repair, and why it was chosen

Prereg §2 fixed the construction before measurement: over CEMS power-train units
(annual `grossLoad > 0`, the exact complement of miso-122's dark set, so boiler
fuel is removed once and cannot re-enter),

```
f_m = heat input share of family m      g_m = gross load share of family m
hr_m = hr_plant × (f_m / g_m)
```

It was chosen over the alternatives because it is a **ratio of shares, never a
level**: it preserves `Σ_m g_m·hr_m = hr_plant` exactly (measured identity error
**3.0e-05**, pure rounding of the 4-dp plant rate), so it re-allocates inside the
plant and smuggles in no re-basing; and it needs only that the gross-to-net
factor be **common across families at one plant**, not equal to 1 — strictly
weaker than the CHP-specific gross-to-net reconciliation `compute_parasitic_factors`
cannot supply, which is what blocked the CEMS route at miso-98 §6.1.

That "common across families" clause is the load-bearing assumption. It is
written down in the prereg as property 2. **It is false at 55088.**

## §3 — KE3 came back live, and backwards

| year | `f_CC` | `g_CC` | `hr_CC` | `f_CT` | `g_CT` | `hr_CT` | max \|Δ\| |
|---|---|---|---|---|---|---|---|
| 2023 | 0.7286 | 0.7151 | **7.0892** (+1.90 %) | 0.2714 | 0.2849 | **6.6262** (−4.76 %) | 4.76 % |
| 2024 | 0.7183 | 0.7094 | 7.0443 (+1.25 %) | 0.2817 | 0.2906 | 6.7449 (−3.05 %) | 3.05 % |
| 2025 | 0.7387 | 0.7301 | 7.0388 (+1.17 %) | 0.2613 | 0.2699 | 6.7367 (−3.17 %) | 3.17 % |

Above the 2 % band, so the pre-declared **INERT-BY-ARITHMETIC** route does not
fire. Neither does **INERT-BY-MARGINALITY**: the keeper's committed sidecars show
`CT_CHP` taking **8,466 distinct values across 8,760 hours** — very nearly a free
variable — and `CC_CHP` at cv 0.23 over 1,084–1,563 distinct values. Both classes
are material (19.7 TWh and 5.5 TWh). *(Recorded honestly: the sidecar schema is
`(year, pass, klass, hour, mw)` and carries **no** marginality or bound flag, so
prereg KE4 clause (a) is **not answerable from committed artifacts**. Only
clause (b), dispatch freedom, is reported, and it is not offered as a proxy for
marginality.)*

So on the pre-registered criteria the lever was live and headed for an A/B. The
reason it did not get one is the **sign**: `hr_CC` > `hr_CT` says a combined
cycle burns more fuel per MWh than a simple-cycle turbine. Per-unit CEMS gross
rates say the same thing — GT3100 10.47, GT2100 9.94 against GTP1 **9.55**. That
is not a physical ordering. It is the signature of a **denominator defect**, and
prereg §4's miso-119 guard (a magnitude is an upper bound, never an argument)
applies with equal force to a magnitude whose *sign* is wrong.

## §4 — KE-R: the assumption is false, and the arithmetic proves it before any model is invoked

This check was **not pre-registered**. It was forced by §3's sign, and it is
recorded as unregistered rather than presented as planned.

**R1.** eGRID `PLNGENAN` = **5,259,825** net MWh. CEMS power-train **gross** =
1,398,184 + 1,210,432 + 1,039,524 = **3,648,140** MWh. Ratio **1.4418**.
*Net cannot exceed gross on the same machines.* **1,611,685 MWh** is inside
eGRID's denominator and outside CEMS's entirely.

**R2.** That generation against the capacity the LP actually holds:
5,259,825 ÷ (515.0 MW × 8,760 h) = **116.6 %**. Impossible. The incumbent rate's
denominator is generation the modelled fleet cannot produce.

**R3.** EIA-860 names the machine. There are **four** generators at 55088, not
three:

| gen | technology | prime mover | unit code | summer MW | energy source |
|---|---|---|---|---|---|
| GT 1 | NG Fired Combined Cycle | `CT` | `SINT` | 175.0 | NG |
| GT2 | NG Fired Combined Cycle | `CT` | `SINT` | 175.0 | NG |
| GTP1 | NG Fired Combustion Turbine | `GT` | — | 165.0 | NG |
| **ST1** | **Other Gases** | **`CA`** | **`SINT`** | **250.0** | **BFG** |

`ST1` is the **steam part of the `SINT` combined-cycle block** — same Unit Code
as the two gas turbines whose exhaust drives it. It has **no CEMS stack** (the
probe's six CEMS units are the three GTs and three boilers), so its output is
absent from `grossLoad`; and it has **no model fleet row** — the fleet carries
exactly 3 generators totalling 515.0 MW = 765.0 − 250.0.

**Mechanical cause.** `market_sim.config.plant_taxonomy.classify_plant` keys on
**Energy Source 1**. `BFG` is not `NG`, not coal, not oil/biomass/wind/solar/
nuclear, so it falls to the residual `OTHER` bucket — as that function's own
docstring says it will ("other/process gas, purchased steam, waste heat …").
EIA-860's `Energy Source 1` for a `CA` row describes its **supplementary/duct
fuel**, not the block's primary energy input, which arrives as turbine exhaust.

**Why this refutes the repair.** `g_CC` omits `ST1`'s MWh while `f_CC` carries
the fuel that produced them, and `GTP1` — a standalone simple-cycle machine with
no HRSG — has no such omission. The gross-to-net factor is therefore **not**
common across the two families, `g_CC` is structurally understated, and `hr_CC`
is inflated exactly as measured. The assumption named in prereg §2 property 2 is
false, at the only plant the mechanism reaches.

**Why no repaired split is shipped.** Attributing `ST1`'s output would decide the
answer. CAMPD's own `unitType` says GT2100/GT3100 are in combined-cycle service
and GTP1 is not, which argues the steam belongs to the `CC` family — but 55088
also runs **three dark boilers burning 7.3 M MMBtu**, and a let-down turbine on
that process steam cannot be excluded from any available source. The choice is
not measurable here, and a chosen attribution would be a fitted parameter
wearing a physical label. This is rule 14 `[R-ACCURATE]`'s **named
different-boundary exception**: the datum is defined on a boundary the model does
not represent, so it is not applied — and it is not replaced by a guess either.

## §5 — what shipped: nothing

Per rule 23 `[R-FROZEN-DERIVE]`, a re-derive commit must cite a scope-gate logic
change on measured grounds. The measured grounds here **refuse** the change, so:

* `scripts/data/derive_chp_power_only_heat_rates.py` — **unmodified**.
* `data/raw/_processed-legacy/chp_power_only_heat_rates_*.csv` — **byte-identical**,
  all five ISOs.
* `ScenarioConfig` — **no new field**, no arming change, no matrix row minted.
* Keeper `2026-08-04-miso-124-dualfuel-rearm` — **untouched**.

The grain defect is left standing and documented rather than papered over with a
correction whose own premise fails. That is the rule 1 `[R-STRUCT]` reading: the
mechanism must be right, not merely different.

## §6 — the successor this NAMES but does not charter

The census (KE-R R4) generalises the diagnostic: a `CA`-prime-mover generator
whose own `Energy Source 1` is not `NG` **but which shares a Unit Code with `NG`
`CT` siblings** is the steam part of a gas-fired combined-cycle block, and is
dropped to `OTHER`. Presence is decided against **each plant's EIA-860 totals**,
not against block siblings — a sibling-relative test mis-reads a plant's
out-of-block generators (55088's standalone GTP1) as the missing steam part, and
the first cut of this probe did exactly that.

| plant | ISO | MW | fuel | status |
|---|---|---|---|---|
| 55088 Dearborn `ST1` | MISO | **250.0** | BFG | **MISSING** |
| 50973 Motiva `GN31`/`GN32`/`GN33` | MISO | **40.4** | OG | **MISSING** |
| 1004 Edwardsport | MISO | 555.0 | SGC | **NOT a defect** — represented, as `COAL` 555.0 |
| 54912 Martinez `STG1` | CAISO | 20.0 | OG | MISSING — **handed off, unstamped** |
| 6081 Stony Brook `CA1` | NEISO | 96.0 | DFO | UNDETERMINED — **handed off, unstamped** |

**MISO carries 290.4 MW of measurably missing combined-cycle steam capacity.**
Edwardsport is called out because it would have been a **555 MW false positive**:
its `SGC` steam part *is* in the fleet, classified `COAL`, and only the
fleet-presence cross-check caught it.

This is **named, not chartered**. It is a fleet-build change, not an offer-curve
change — a different mechanism at a different seam (rule 19 `[R-ONE-MECH]`), and
adopting it mid-session after seeing the data is precisely what the
pre-registration exists to prevent. It needs its own prereg, and its A/B is not
free: adding 250 MW of CHP capacity in MISO-East changes the fleet, and the
55088 heat rate would have to be re-derived **onto the repaired denominator** in
the same change, since the two defects share one cause.

Rule 25 `[R-ISO-SCOPE]`: only MISO's cell is stamped. CAISO's and NEISO's rows
are reported so those lanes can run their own checks, and neither is adjudicated
here.

## §7 — for the next session

1. **Do not re-test the prime-mover share split at MISO.** It is `R` on measured
   grounds. Re-opening needs an admissible attribution of `ST1`'s generation
   between the `CC` and `CT` families — not a different share statistic.
2. **The queue head is spent.** §5.4 again has no named, un-adjudicated,
   non-data-blocked item. The two bounded NON-solve steps stand: item 1's Form
   580 tonnage **count** (a sourcing pass) and miso-114 §6's CAMPD `CT_PEAKER` +
   `ST_GAS` overnight-online measurement.
3. **The 290.4 MW capacity item is the strongest named successor**, and it is
   rule 14 grounds with a verified population. Charter it deliberately.
4. **A methodological note worth carrying.** The pre-registered inertness routes
   (KE3 arithmetic band, KE4 marginality) **both failed to fire**, and the lever
   was still killed with zero solves — by a **validity** check on the
   construction's own stated assumption, not by a magnitude. Writing the
   assumption down explicitly in the prereg is what made it falsifiable. Prefer
   that to another percentile.
