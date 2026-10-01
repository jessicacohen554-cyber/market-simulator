# FINDING — SCN-WS2b: the CES premium ladder re-proved at HEAD on ERCOT and NEISO, a national clearing script, and a CCS emission-rate seam that inverts the sign of NEISO's headline CO2 answer

**Lane:** SCN-WS2b · **Branch:** `claude/scn-ws2b-ces-clearing-y40sks` · **Date:** 2026-09-06
**Charter:** `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §3 WS-2 items 3–6 / §7 "WS-2b"
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-scn-ws2b-2026-09-06.md` (pushed before the first solve)
**Model:** `claude-opus-5` (rule 27 `[R-PUSH]`) · **Data profile:** `ercot`, then `neiso`
**Base:** `origin/main` `af6269cf` at the PRECOMMIT, rebased to `3dcf1b22` mid-session

---

## 0. Bottom line

**Item 1 (re-prove) — the DIRECTION holds table by table; the LEVELS do not, and every level change
is charged to a named flip or reported as unattributed.** All six legs solve, all six register.
Against the July FF-3B surface: `clean_share` still rises monotonically with the premium,
negative-price hours still rise from exactly 0 in BAU (July's 0, reproduced), both VRE captured
prices and the average price still fall monotonically, and **the invariant pattern reproduces
July's F-2 exactly** — BAU I3+I12 FAIL / I14 WARN, both premium arms adding I9. What has changed is
large: ERCOT's BAU commissioned VRE collapses **14 GW → 0.65 GW**, its CES-40 build falls
**37 GW → 24 GW**, and the ERCOT ladder now **saturates between $20 and $40** because the binding
constraint in every premium year is `iso_budget_exhausted`, not economics.

**Item 2 (clearing script) — delivered, tested, and the bracket CLOSES for one cell.** SCN-WS2a's
target-row probe landed on `main` during this session, so the uniform-share half exists after all:
at NEISO 2026 both representations read **0.3447**, gap **0.00 pp** — and they agree because
*neither moves anything* (the premium is dispatch-inert there; the 0.55 target row escapes at its
ACP). The cross-ISO spread under a uniform price grows **8.7 pp (2026) → 35.2 pp (2030)**.

**THE SESSION'S MOST IMPORTANT RESULT IS A DEFECT THE RE-PROVE EXISTS TO CATCH, AND IT IS NOT A CES
DEFECT.** In NEISO the premium's entire response is `gas_cc_ccs` — 17.1 → 59.7 TWh at 2030 — and
**those retrofitted units carry an UNCAPTURED emission rate in the dispatch fleet while being
credited at 0.95 by the CES.** Measured on a single unit across its own retrofit year: `fuel_type`
flips `gas_cc → gas_cc_ccs` ✓, `heat_rate` rises 7.5101 → 8.4113 (×1.12, the parasitic penalty) ✓,
and `emission_rate` stays **0.3745 → 0.3745**, unchanged to four decimals ✗. Three writes in the
same block of `ccs.py`; two persist, one is overwritten downstream. The consequence is that
**NEISO's 2030 CO2 answer is sign-flipped**: as scored the premium *raises* CO2 +9.99 Mt; with the
intended 90 % capture applied as an accounting recomputation at fixed dispatch it *cuts* it
−6.01 Mt. **Not fixed here** — `ccs.py`, `data/fleet/` and `runner.py` are all outside this lane's
regions and the CCS seam is the capx D50/D60/D65 lane's. Routed in §8 with the arithmetic attached.

**The leakage line the charter asked for: the CES premium does NOT leak the way a carbon price
does — it leaks in reverse.** WS-0 measured a $25/t adder exporting two thirds of its NEISO
reduction across the NYISO seam. The premium does the opposite: `import_co2_mt_reported` **falls**
6.38 → 3.36 Mt at 2030 (−3.02 Mt) as 17.5 TWh of imports are repatriated. The §6 pre-registered
prediction was right on that direction and wrong about what it would mean, because the repatriated
energy lands on the mis-rated CCS fleet.

---

## 1. What ran

Six ladder legs (3 ERCOT + 3 NEISO), one leg per invocation (rule 12 `[R-PARALLEL]`), years
sequential inside each, never more than two invocations concurrent, all in-session — no CI runner.
Plus a three-arm rule-29 screen (§2), which is a throwaway and is not committed.

| ISO | case | cache key | per-year wall (s) | leg total | s/solve-yr | peak RSS | invariants |
|---|---|---|---|---|---|---|---|
| ERCOT | BAU | `d88c8585e76f2935` | 132/57/62/81/66 | 6.6 min | 80 | 4.03 GB | FAIL I3,I12 · WARN I14 |
| ERCOT | CES-20 | `075e6aa30813f061` | 135/61/60/68/61 | 6.4 min | 77 | 4.05 GB | FAIL I3,I9,I12 · WARN I14 |
| ERCOT | CES-40 | `383509581661faba` | 133/64/62/67/58 | 6.4 min | 77 | 4.05 GB | FAIL I3,I9,I12 · WARN I14 |
| NEISO | BAU | `5e2c52ea81694c10` | 118/34/47/50/43 | 4.9 min | 59 | 3.27 GB | none |
| NEISO | CES-20 | `43b921da2f0bcfc7` | 114/33/50/49/40 | 4.8 min | 57 | 3.46 GB | none |
| NEISO | CES-40 | `7d36e0b517ffb0e3` | 122/36/50/48/44 | 5.0 min | 60 | 3.48 GB | none |

**Against the FF §2.4 budget (ERCOT ~2.4 min/solve-year, NEISO ~1.5): ERCOT came in at 1.3 min and
NEISO at 1.0 min.** July measured ERCOT CES at 132–137 s/yr; HEAD is 77–80 s/yr — roughly half,
consistent with the wallclock A-series work merged in the interval. RSS is essentially unchanged
(July 3.69–4.24 GB; HEAD 4.03–4.05 GB), and July's observation that the premium adds RSS but not
wall time still holds. The first year of every leg carries ~60–80 s of fleet-load setup.

Data prerequisite (FF §2.4, and SCN-WS0 §5 item 4): `scripts/data/curate_confirmed_retirements.py`
was run first — five partitions, ERCOT 3 live rows, NEISO 16.

**Base configs.** ERCOT re-uses the July POC's own base `configs/scenarios/ercot_ces_poc_2026_2030.yaml`,
so the base file is not a source of drift. NEISO has no CES POC base and uses the committed campaign
REF `configs/scenarios/neiso_scenario_base_2026_2030.yaml` (SCN-WS0's file, **read, never written**),
which differs from ERCOT's only by the `entry_screen_diagnostics` observability flag. Both declared in
the PRECOMMIT before the solve.

---

## 2. The rule-29 screen — ERCOT 2026, three arms, verdict PASS (it killed nothing, and it promoted nothing)

Screen year 2026, named in the PRECOMMIT before the solve and **forced rather than chosen**: rule 29
wants the year of largest measured footprint, which here is 2030, but a forecast year N is the
output of a one-pass capacity evolution seeded by years 1…N−1, so 2030 cannot be solved alone. The
window's first year is the only solvable single-year screen.

| # | gate | measured (BAU / CES-20 / CES-40) | verdict |
|---|---|---|---|
| G1 | monotone clean share | 0.4320 / 0.4320 / 0.4320 | PASS (weakly; see below) |
| G2 | credited columns only | only solar moves, +0.0002 TWh on 74.39; every credit-0 column (coal, gas_cc/ct/st, hydro, nuclear) identical to 4 dp | PASS |
| G3 | negative-price hours rise, CES-40 > BAU strictly | 521.9 / 599.7 / 599.7 | PASS |
| G4 | captured prices and avg price fall monotonically | wind 27.84 / 26.05 / 24.27; solar 32.86 / 32.79 / 32.71; avg 30.57 / 29.20 / 27.84 | PASS |
| G5 | no non-target load-bearing flip | 0 FAIL / 0 WARN in all three arms | PASS |

**What the screen actually taught, and it is not in the gate.** In the window's first year the
premium moves **prices and negative-price hours but not one credited MWh**: quantities are identical
to rounding across a $0→$40 range. That is correct behaviour, not inertness — ERCOT's credited fleet
is already dispatched to its zero-MC limit and year 1's fleet is fixed, so the credit can only move
the *dual* in the hours a credited unit is marginal (−$1.37/MWh of average price per $20 of premium)
and deepen the negative-price epoch. **It follows that the 2026–2030 ladder's clean-share response is
entirely a capacity-evolution response.** That inference was formed *after* the screen and is recorded
as such; it is not part of the PRECOMMIT and it changed no gate, whose five checks were fixed before
the solve.

Screen legs `dce59bf0c1ff952b` / `1fec9c741d9f36b6` / `602e2834016c49f7`. Not registered, not a
keeper, not quoted as one; the year was re-solved inside the full bundle (rule 29 clause 2) and the
bundle is deleted rather than committed (clause c's discipline, applied to a forecast lane).

---

## 3. ERCOT — the 2030 surface, table by table against July

July's table is `ff-3b-ces-poc-2026-07.md` "Machinery proof". Same metrics, same year, same report
generator.

| metric (2030) | July BAU | HEAD BAU | July CES-20 | HEAD CES-20 | July CES-40 | HEAD CES-40 | direction |
|---|---|---|---|---|---|---|---|
| `clean_share` | 0.400 | **0.3205** | 0.492 | **0.4751** | 0.506 | **0.4756** | ✓ holds (monotone ↑) |
| `negative_price_hours` | 0 | **0.0** | 1017 | **843.7** | 1111 | **874.4** | ✓ holds (0 → >0, ↑) |
| `avg_price` $/MWh | 57.52 | **2098.99** | 54.39 | **1409.26** | 53.02 | **1407.18** | ✓ holds (↓ with premium) |
| solar build GW (commissioned) | 9 | **0.1** | 19 | **14.0** | 20 | **14.0** | ✓ holds (↑ with premium) |
| wind build GW (commissioned) | 5 | **0.55** | 13 | **10.0** | 17 | **10.0** | ✓ holds (↑ with premium) |
| solar captured price $/MWh | 30.02 | **2308.56** | 11.89 | **780.04** | 1.36 | **771.56** | ✓ holds (↓ with premium) |
| wind captured price $/MWh | 50.43 | **1513.64** | 40.74 | **848.33** | 30.36 | **845.62** | ✓ holds (↓ with premium) |
| `premium_capture_rate` | 0.801 | **0.9422** | 0.877 | **0.9206** | 0.872 | **0.9218** | ✗ **ORDER INVERTS** |
| invariants | I3,I12 F / I14 W | **identical** | +I9 | **identical** | +I9 | **identical** | ✓ exact |

**Seven of eight directions hold. One inverts** — `premium_capture_rate`, which in July rose with
the premium (0.801 → 0.877) and at HEAD falls (0.9422 → 0.9218). §4 P8 pre-registered this as
"roughly unchanged, and a large move is an unattributed level change"; it moved and it inverted, and
the inversion is explicable from the definition: the rate is credited *delivered* over credited
*potential*, so adding 24 GW of new VRE potential to the denominator lowers it whenever the added
MWh are curtailed at the margin — ERCOT's curtailment doubles (4.91 → 9.97 TWh) in the premium arms.
July's arms added VRE too, so this is a change in *how much of the added potential is spilled*, not
in the metric. **Recorded as attributed-with-lower-confidence**, not as a clean flip explanation.

**Two level changes are regime changes, not level changes, and must be read that way.** ERCOT at
HEAD is in deep adequacy failure across the window — reserve margin **+14.8 % (2026) → −7.1 % (2030)**
and **17.7 TWh unserved in BAU 2030** — so `avg_price` and both captured prices are VOLL-dominated
and the 36× gap to July's $57.52 is a scarcity artifact, not a CES effect. This is the plan's own
G-S4 NO-GO (R1/R2, `ces-w3r-readiness-2026-07.md`) showing up quantitatively: **the ERCOT CES
*dispatch* response is readable; its *price* and *deployment* levels are not campaign-grade**, and
nothing in this lane changes that.

**A new structural fact, absent from July: the ERCOT ladder SATURATES between $20 and $40.**
CES-20 and CES-40 commission identical builds (14.0 GW solar, 10.0 GW wind), reach clean shares
0.4751 vs 0.4756, and emit 257.680 vs 257.637 Mt. July's arms differed materially (0.492 vs 0.506).
The reason is in the entry diagnostics, not in a residual: in **every** premium year the binding cap
is `iso_budget_exhausted` — the ISO's 12 GW/yr queue budget, not the price. Above ~$20/MWh the ERCOT
premium buys nothing more because the queue is already full.

---

## 4. Attribution — the pre-registered predictions, scored

The PRECOMMIT charged each expected level change to a named flip **before the 2030 surface existed**.
Scored honestly, misses at full magnitude.

| # | prediction | verdict | evidence |
|---|---|---|---|
| **P1** | solar and wind build fall in every arm, premium increment falling more | **SPLIT — right on the commissioned basis, WRONG on the decided basis** | commissioned: BAU 14 → 0.65 GW, CES-40 37 → 24 GW ✓. But the screen *decides* **45.3 GW** of VRE under CES-40 at HEAD (wind 19.4 + solar 25.9 + geo 2.0), **more** than July's 37 GW. The gap is entirely `entry_commissioning_lag` |
| **P2** | clean share falls in every arm, most in the premium arms | **HALF RIGHT** | BAU 0.400 → 0.3205 ✓ (−7.9 pp); premium arms 0.492/0.506 → 0.4751/0.4756, i.e. −1.7/−3.0 pp — the premium arms fell LESS, not more |
| **P3** | BAU `avg_price` rises, charged to F1 + F13 | **RIGHT DIRECTION, WRONG CAUSE** | it rose 57.52 → 2098.99, but the ERCOT window retires only **446 MW** in total (2029) — the retirement channel cannot carry a 36× price move. The cause is the adequacy collapse on the entry side |
| **P4** | the premium's price delta narrows | **WRONG** | July −$4.50/MWh; HEAD **−$691.81**/MWh. Under scarcity the premium's 8.25 TWh of avoided unserved energy is worth VOLL, not $/MWh of energy |
| **P5** | negative-price hours fall in the premium arms but stay > 0 | **RIGHT** | 1017/1111 → 843.7/874.4, both > 0 |
| **P6** | captured prices rise (less collapse) | **RIGHT in relative terms** | solar collapses to 33 % of its BAU value at HEAD vs 4.5 % in July; wind to 56 % vs 60 %. Absolute levels are scarcity-inflated |
| **P7** | any CCS-credited MWh in 2028–2030 is lower or zero, charged to F14 | **RIGHT — zero** | ERCOT's by-fuel table carries **no `gas_cc_ccs` row at all** in any arm; the screen lists it `unprofitable` (2030 BAU) / `per_tech_cap_zero` (2030 CES-40). D50's carbon-0 closure (owner Q42) reproduced |
| **P8** | `premium_capture_rate` roughly unchanged | **WRONG** | 0.801/0.877/0.872 → 0.9422/0.9206/0.9218; the ordering inverts (§3) |
| **P9** | DC posture explains nothing | **RIGHT** | `datacenter_load_path` is `mid` in both postures; no result is charged to it |

### 4.1 What the entry diagnostics name, and what they do not

`entry_screen_diagnostics: true` on the ERCOT base gives the binding cap per candidate per year.
Reading them (`evolution_20XX.json`, `binding_cap`):

- **BAU 2027 and 2028: wind and solar are `unprofitable`** — margins −$1,922 and −$13,684/MW-yr in
  2027, attribute revenue $0. **This is an economics failure, not a damper.** P1's charge to
  `entry_rate_limits` + `entry_commissioning_lag` is therefore **wrong about the first two years**:
  the rate ladder never gets a chance to bind on a candidate the screen already declined.
- **BAU 2029: `margin_exhausted`** on both, with margins now *positive* (+43,534 solar / +23,577
  wind) — gas_cc and gas_ct took the ISO budget first in the margin walk. That label is produced
  only by the margin-walk branch, i.e. by **F9 `entry_margin_exhaustion`** (an ERCOT
  `default_scenario_overrides` entry armed 2026-08-25/30/31, after July).
- **BAU 2030: `iso_budget_exhausted`** (solar takes 4 GW) / `per_tech_cap_zero` (wind gets nothing
  left) — the 12 GW ISO queue budget, an older constraint, not a July→HEAD flip.
- **CES-20 and CES-40, every year: `iso_budget_exhausted`.** The premium moves wind from
  −$1,922 to **+$120,412**/MW-yr of margin in 2027 and the binding constraint becomes the queue.

**The premium's entry-screen footprint is an exact identity, and it checks out.** The screen's
`attribute_revenue_per_mw_yr` is `premium × CF_expected × 8760` and nothing else: wind at CES-40,
0.34913 × 8760 × 40 = $122,335 against the recorded **$122,334**; solar 0.25866 × 8760 × 40 =
$90,647 against **$90,636**. The credit reaches the deployment screen through exactly one channel,
at exactly its own arithmetic — the deployment-side counterpart of the screen's G2.

### 4.2 `entry_commissioning_lag` measured, not asserted

Every `entry_pipeline` row carries `decision_year` and `cod_year`, and the gap is **exactly two
years** in every row of both arms. So under CES-40, 2029's and 2030's decisions (10 GW wind +
12 GW solar + 2 GW geothermal) have COD 2031/2032 and **never appear inside the window**; under BAU
the only VRE decision at all (4 GW solar, 2030) COD's in 2032. July's numbers were decided =
commissioned. **This alone accounts for the CES-40 gap between 45.3 GW decided and 23.3 GW
commissioned**, and it is F3, named in the PRECOMMIT.

### 4.3 What I cannot attribute, stated plainly

**Why ERCOT BAU wind and solar are `unprofitable` at HEAD when July's screen built 14 GW is NOT
decomposed by this lane.** Seven entry-side flips landed between the two postures (F2, F3, F5, F6,
F8, F9, F10 in the PRECOMMIT's census), the 2027 wind margin is a near-miss at −$1,922/MW-yr, and
the diagnostics name the *binding cap*, not *which flip moved the signal*. A per-flip decomposition
is seven single-lever ERCOT arms at the measured 6.5 min/leg ≈ **45 min of LP**. That is affordable
but it is **not in this lane's PRECOMMIT**, and spending an unplanned solve to make an attribution
land would be exactly the discipline rule 29 exists to protect. **Reported as an unattributed level
change and routed (§8 item 2) with its measured cost.**

---

## 5. NEISO — the ladder, the leakage line, and the CCS seam

### 5.1 The surface

| metric (2030) | BAU | CES-20 | CES-40 |
|---|---|---|---|
| `clean_share` | 0.5005 | 0.6218 | **0.8277** |
| `emissions_mt` | 14.887 | 16.505 | **24.878** |
| `import_co2_mt_reported` | 6.3816 | 4.8176 | **3.3615** |
| `avg_price` $/MWh | 66.84 | 52.72 | 41.46 |
| wind / solar captured price | 66.72 / 63.43 | 52.63 / 50.88 | 40.71 / 39.89 |
| `negative_price_hours` | 0 | 0 | 0 |
| `unserved_mwh` | 0 | 0 | 0 |
| commissioned builds (MW) | gas_cc 1000, gas_ct 50, solar 2000, wind 1000 | **identical** | **identical** |

**The premium adds ZERO economic entry in NEISO.** Every committed MW in all three arms is the
known/planned-additions pipeline. NEISO's whole CES response is a *dispatch* response.

### 5.2 The leakage line the charter asked for — answered, with the opposite sign to a carbon price

WS-0 measured a $25/t carbon adder on NEISO cutting modeled in-ISO CO2 −2.71 Mt while raising
`import_co2_mt_reported` +1.85 Mt on the single `NYISO_CT_peak` rung: about two thirds of the
headline reduction left the scored basis. **The premium does the reverse, and the PRECOMMIT's §6
reasoning for why is confirmed.**

| 2030, NEISO | BAU | CES-40 | Δ |
|---|---|---|---|
| `emissions_mt` (scored, in-ISO) | 14.887 | 24.878 | **+9.991** |
| `import_co2_mt_reported` (disclosure) | 6.3816 | 3.3615 | **−3.020** |
| imported energy (TWh) | 33.000 | 15.482 | **−17.518** |
| sum of the two CO2 lines | 21.269 | 28.240 | **+6.971** |

A carbon price raises in-ISO fossil cost and leaves the import tranche untouched, so the cheapest
substitute is someone else's gas across the seam. A clean-attribute premium lowers in-ISO *credited*
offers and leaves both in-ISO fossil and import cost untouched, so it pushes credited generation
below both and **repatriates** imports. **The premium does not leak the way a carbon price does.**
That comparison had never been made; it is cheap and it is now on record.

**The asymmetry that makes this read worse than it is, declared in the PRECOMMIT before the solve:**
`import` is a `FUEL_TYPE_MAP` fuel and is **not** in `federal_ces_eligible_fuels`, so NEISO's firm,
zero-carbon Hydro-Québec tranches earn **no CES credit**. The premium is, in NEISO specifically, a
subsidy to in-ISO credited generation *against* an uncredited zero-carbon import. Real CES designs
generally credit delivered zero-carbon imports; this one does not. That is a **modelling posture and
a disclosure item for the campaign**, not a defect, and it is a large part of why the import line
falls.

### 5.3 THE FINDING — retrofitted CCS units are credited 0.95 and emit as if uncaptured

**What the premium actually buys in NEISO** (2030, BAU → CES-40, generation TWh):

| fuel | BAU | CES-40 | Δ | CO2 Mt (CES-40) |
|---|---|---|---|---|
| **gas_cc_ccs** | 17.128 | **59.745** | **+42.617** | **24.174** |
| gas_cc | 17.022 | 0.837 | −16.185 | 0.322 |
| import | 33.000 | 15.482 | −17.518 | 0 (by design) |
| biomass | 8.398 | 1.526 | −6.872 | 0.240 |
| gas_ct / gas_st | 1.908 / 0.474 | 0.358 / 0.099 | −1.550 / −0.375 | 0.112 / 0.030 |
| nuclear, hydro, wind, solar | 26.482 / 6.973 / 6.282 / 5.768 | **identical** | 0.000 | 0 |

The credited zero-carbon fleet is **byte-identical across arms** — already fully dispatched. The
entire response is `gas_cc_ccs`, which the CES credits at **0.95** (`clean_capture`) and which the
model dispatches at **24.174 Mt / 59.745 TWh = 0.4046 t/MWh** — *higher* than the unabated gas_cc
fleet's 0.3719.

**The retrofit is not reducing the emission rate.** `ccs.py:565-575` executes three writes on the
same generator object in the same loop iteration. Tracked through the cached `FleetContext` for one
unit across its own retrofit year (NEISO BAU, key `5e2c52ea81694c10`):

| year | `fuel_type` | `heat_rate` | `emission_rate` |
|---|---|---|---|
| 2027 | `gas_cc` | 7.5101 | 0.3745 |
| **2028 (retrofit)** | **`gas_cc_ccs`** ✓ | **8.4113** ✓ (= 7.5101 × 1.12, the parasitic penalty) | **0.3745** ✗ |
| 2029 | `gas_cc_ccs` | 8.4113 | 0.3745 |
| 2030 | `gas_cc_ccs` | 8.4113 | 0.3745 |

Two of the three writes persist; `gen.emission_rate_co2 *= (1 − 0.90)` does not. Reproduced on all
six units in the 2028 retrofit cohort. Fleet-wide at NEISO 2030 the `gas_cc_ccs` class carries
pmax-weighted **0.4149 t/MWh** against unabated gas_cc's **0.4663** — a 47-unit, 9.0 GW class that
is nominally 90 %-captured and is dispatched, priced and accounted as essentially uncaptured.

Note the internal inconsistency this leaves behind: **the heat rate rose 12 % and the emission rate
did not move at all.** A rate re-derived from the new heat rate would have *risen*; a rate carrying
the capture would have *fallen* by 90 %. It did neither, which points at a plant-keyed restoration
of the measured rate downstream of evolution (`plant_emission_rates_v2` is the leading candidate)
rather than a recomputation. **Stated as the leading candidate, not as a conclusion** — the owning
lane should confirm the mechanism before repairing it.

### 5.4 The magnitude: NEISO's headline CO2 answer is sign-flipped

Applying the intended 0.90 capture to the `gas_cc_ccs` rows as an **accounting recomputation at
fixed dispatch**:

| year | case | CCS TWh | CCS Mt (as scored) | total Mt as scored | total Mt with capture applied |
|---|---|---|---|---|---|
| 2028 | BAU / CES-20 / CES-40 | 1.10 / 22.62 / 23.04 | 0.62 / 7.96 / 8.10 | 16.961 / 18.043 / 18.029 | 16.403 / 10.881 / 10.736 |
| 2029 | BAU / CES-20 / CES-40 | 8.26 / 39.38 / 45.85 | 3.22 / 14.29 / 16.70 | 15.386 / 18.204 / 19.754 | 12.488 / 5.340 / 4.722 |
| **2030** | BAU / CES-20 / CES-40 | 17.13 / 32.85 / 59.75 | 6.40 / 12.39 / 24.17 | **14.887 / 16.505 / 24.878** | **9.128 / 5.354 / 3.121** |

**As scored, the CES-40 premium RAISES NEISO's 2030 CO2 by +9.99 Mt. With the capture applied it
CUTS it by −6.01 Mt.** The sign of the campaign's headline answer for this ISO depends entirely on
this seam.

**This recomputation is arithmetic, not a simulation, and must not be quoted as a result.** A
corrected emission rate would also change the *dispatch*: NEISO carries an RGGI carbon price, so a
90 %-captured unit would pay one tenth of the carbon adder in its marginal cost and the LP would
order differently. The corrected column is an upper bound on how much of the scored CO2 is
mis-attribution, not a prediction of the repaired run. **The repaired run is the routed work.**

### 5.5 NEISO 2026–2027: the premium is exactly inert, and that is the right answer

All three arms are identical to four decimals in 2026 and 2027 — same clean share (0.3447 / 0.3402),
same CO2, same prices, same imports. `ccs_retrofit_available_year` is 2028, so before then NEISO has
no `gas_cc_ccs` at all, and its credited fleet (nuclear 26.5, hydro 7.0, wind 6.3, solar 5.8 TWh) is
already fully dispatched with nothing left for a credit to move. The ladder's NEISO response begins
in **2028**, the first retrofit year — i.e. the entire NEISO CES response is downstream of the CCS
seam in §5.3.

---

## 6. Item 2 — `scripts/ces_national_clearing.py`, and the bracket

**Delivered, zero-solve, 20 synthetic-curve tests** with hand-computed closed-form answers
(`tests/scoring/test_ces_national_clearing.py`): linear, saturating, flat/inert, met-at-floor,
two-ISO aggregate clearing where neither ISO individually carries the national share,
energy-weighted rather than ISO-counted aggregation, mismatched ladders, and a missing ISO-year
excluded-and-named rather than zeroed. Three refusals are load-bearing and each is tested: it never
extrapolates past the solved ladder; it never calls a partial-coverage aggregate "national"; and it
leaves the uniform-share column empty with an explicit note rather than inventing it.

**Run on the real two-ISO ladder** (denominator: total modeled generation including imports — the
same basis `clean_share` uses; a statutory CES obligates retail sales and no loss factor is
invented):

| year | system share at $0 | at $40 | illustrative flat 0.45 target | ISO spread at clearing (pp) |
|---|---|---|---|---|
| 2026 | 0.4166 | 0.4166 | NOT_REACHED | 8.73 |
| 2027 | 0.3907 | 0.3907 | NOT_REACHED | 6.06 |
| 2028 | — | 0.4214 | NOT_REACHED | 11.44 |
| 2029 | — | 0.4852 | **CLEARED at $15.56/MWh** | 18.93 |
| 2030 | — | 0.5254 | **CLEARED at $13.83/MWh** | 15.66 |

The plan's own illustrative `{2026: 0.55, 2035: 0.80, 2050: 1.00}` ramp is **NOT_REACHED in every
year** of this two-ISO system inside the $0–$40 ladder; the script reports the attainable share and
declines to name a price. Every level here is **illustrative** — owner box **D-2 is OPEN**, the
`{10, 20, 30}` ladder stands from D8, and `{20, 40}` is the July instrument used as the charter
names it.

**The cross-ISO-trade uncertainty is the result, and it grows.** The spread between the two ISOs'
shares at a single uniform price runs **8.7 pp (2026) → 35.2 pp (2030)** on the 0.55-knot run. A
uniform *share* would be 0 pp by construction. That gap is G-S2's bracket width.

**The bracket CLOSES for one cell — and the charter's contingency did not need to fire.**
SCN-WS2a's target-row probe landed on `main` during this session
(`neiso-2026-2026-scn-ws2a-neiso-2026-t0-{ref,target}`), so the uniform-share half exists:

| year | ISO | uniform-price share | target-row share (WS-2a) | gap |
|---|---|---|---|---|
| 2026 | NEISO | 0.3447 | **0.3447** | **0.00 pp** |
| 2026 | ERCOT | 0.4320 | — (no WS-2a arm) | — |
| 2027–2030 | both | measured | — (no WS-2a arm) | — |

**A zero gap here means the question is not yet live in 2026, not that the two representations
coincide.** The premium is dispatch-inert in NEISO 2026 (§5.5) and WS-2a's 0.55 target row lands in
the escape regime — dual = the $50 ACP exactly, escape 24.03 TWh, every credited column
byte-identical to REF (`FINDING-scn-ws2a-2026-09-05.md` §4). Both representations deliver NEISO's
physical 0.3447 because neither can buy a single additional credited MWh there. **The bracket has
real width only where the premium is live, and WS-2a has no arm in those years or in ERCOT.**

One basis note, checked rather than assumed: WS-2a's row RHS is `target × Σ demand` (LP demand)
while this script's denominator is served generation. For NEISO 2026 the two agree to four decimals
(40.37 TWh / 117.09 TWh demand = 0.3448 vs `clean_share` 0.3447), so the comparison is safe in this
cell. It would need re-basing in an ISO where storage or exports open a gap.

The target-row input is `results/scn-ws2-ladder/ws2a_target_row_results.csv`, one row, transcribed
from WS-2a's own FINDING §4 and its committed sidecar; its `clean_share` is the REF value, which is
valid precisely because WS-2a measured the credited columns byte-identical across its pair.

---

## 7. Mechanism matrix (rule 28 duty b)

Two cells re-stamped with HEAD-posture evidence, as the last commit after `git fetch origin main` +
rebase, one appended line each (desk ledger §4 protocol items 2 / 3a):

- **ERCOT `federal_ces`** — stays `O`. The machinery is proven again at HEAD and the direction holds
  table by table, but the deployment and price levels are not campaign-grade (adequacy collapse,
  §3), the ladder saturates above ~$20/MWh on the queue budget, and G-S4's NO-GO stands. `O`, not
  `K`, and not `R`.
- **NEISO `federal_ces`** — moves `U` → `O`. First NEISO evidence: the mechanism is wired end-to-end
  and right-signed on clean share, price and imports; it adds no entry; and its CO2 read-out is
  currently governed by the §5.3 CCS seam, so it is **open, not accepted**.

No `ScenarioConfig` field was added, so duty (c) does not apply. `scripts/check_mechanism_matrix.py`
exits 0 at HEAD (integrity OK, 6 shards; the 244 anchor warnings are pre-existing and untouched).

---

## 8. Routed to SCN-DESK

1. **THE CCS RETROFIT EMISSION-RATE SEAM (§5.3) — highest priority, and it is not this lane's
   file.** `ccs.py:572`'s `gen.emission_rate_co2 *= (1 − ccs_retrofit_capture_rate)` does not reach
   the dispatch fleet, while the two writes bracketing it (`heat_rate`, `fuel_type`) do. Leading
   candidate: a plant-keyed restoration of the measured CEMS rate downstream of evolution
   (`plant_emission_rates_v2`), which would also explain why the rate did not follow the 12 % heat-rate
   rise. **Owner: the capx CCS lane (D50 / D60 / D65), which holds `ccs.py`; this lane holds none of
   `ccs.py`, `data/fleet/`, `runner.py`.** Consequences that should travel with the route: every ISO
   that retrofits carries mis-stated CO2 (NEISO retrofits 8.8 GW by 2030 in BAU and 9.0 GW under CES-40 — the 3 GW/yr ISO cap binding in 2028-2030 of both arms; D50's finding
   records NEISO clearing 12.38 GW under RGGI even after the capex repair); the CCS unit's *marginal
   cost* is also wrong wherever a carbon price applies, because the carbon adder is
   `emission_rate × carbon_price`, so this is a **dispatch** defect as well as an accounting one; and
   the `federal_ces` 0.95 credit against an uncaptured rate is what makes it visible.
2. **The ERCOT BAU entry collapse is unattributed (§4.3)** and needs a seven-arm single-lever
   decomposition over F2/F3/F5/F6/F8/F9/F10 to close. **Measured cost: ~6.5 min/leg × 7 ≈ 45 min of
   in-session LP.** Not spent here because it is outside this lane's PRECOMMIT.
3. **`import` is CES-ineligible (§5.2)** — a modelling posture with a large effect on a
   program/import ISO. Worth an owner box beside D-2: should delivered zero-carbon imports earn the
   federal credit? Real CES designs generally say yes.
4. **The ERCOT ladder saturates on the queue budget above ~$20/MWh (§3).** A campaign ladder of
   `{10, 20, 30}` (D8) would sit almost entirely inside the saturated region in ERCOT. The
   discriminating axis there is the queue budget, not the premium — worth knowing before the
   campaign's rungs are fixed.
5. **G-S5 IS CLOSED and its register rows are NOT edited here.** The plan's §2.2 G-S5 entry
   and its §8 findings row still read "CES-POC sidecars pruned … the POC survives as a handoff
   doc only". Item 1 restored that evidence at HEAD in the forecast namespace, so both rows are
   stale — but they sit outside this lane's named regions (§5.1 and ledger §3 only), so they are
   **routed rather than edited**, per the shared-file protocol.
6. **The clearing script's bracket is one cell wide.** Closing it needs WS-2a target-row arms in the
   years and ISOs where the premium is actually live (NEISO 2028+, ERCOT any year) — NEISO 2026 is
   structurally incapable of discriminating (§6).

**No file outside this lane's declared regions was edited.** `policy/federal_ces.py`,
`policy/clean_tiers.py`, `model/lp/rows.py`, `config/scenarios.py`'s `federal_ces_*` block,
`scripts/report_ces_campaign.py`, `scripts/report_scenario_deltas.py`,
`scripts/register_forecast_run.py`, `configs/scenario_campaign_matrix.yaml` and
`frontend/data/forecast/program-status.json` are all untouched. No default moved, no
`ScenarioConfig` field was added, no CI workflow was created, and no solve was run that the
PRECOMMIT did not name.

---

## 9. Artifacts

- **Registered**, forecast namespace, `kind=scenario`, campaign `scn-ws2-ladder`, reference `BAU`:
  `ercot-2026-2030-scn-ws2-ladder-{bau,ces-20,ces-40}` and
  `neiso-2026-2030-scn-ws2-ladder-{bau,ces-20,ces-40}`. The committed inputs are the six
  `frontend/data/hindcast/*.json` sidecars; `registry/`, `runs/`, `manifest.js` are generated and
  gitignored (rule 15 `[R-DASHBOARD]`, FF plan §7.5), rebuilt by the Pages deploy. **The backcast
  registry is untouched.**
- **`results/scn-ws2-ladder/` (584 KB, slim only)** — each leg's `full_horizon_summary.json` +
  `run_config.json`, both matrix bundles, both nine-table report sets, the national-clearing outputs
  at the 0.55-knot and the illustrative flat-0.45 target, and the one-row WS-2a target-row input.
  The per-ISO LP caches are the already-ignored `/results/ERCOT/` `/results/NEISO/` class.
- **`scripts/ces_national_clearing.py`** + `tests/scoring/test_ces_national_clearing.py` (20 tests,
  passing; `ruff check` and `ruff format` clean).
- **Not committed:** the rule-29 screen bundle (`results/scn-ws2b-screen/`). Every number this
  session will cite from it is in §2; git history is the record, and the bundle is deleted before
  merge (rule 29 clause c's discipline).
