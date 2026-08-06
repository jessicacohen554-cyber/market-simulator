# FFR-7C — FFR-6A's exit decode, re-derived on the CORRECTED retirement target

**Session.** FFR Wave 7, **COMMITTED-ARTIFACT MEASUREMENT lane** (manager charter, sitting
Addendum **W.4**). Branch `claude/ffr-7c-exit-decode-corrected-y3p9to`, off `origin/main`
`3b671bf5`. **No solve, no model change, no arming, no keeper contact, no registration.**

**Evidence chain.** FFR-6A `docs/handoffs/ffr-6a-margin-gap-decomposition-2026-08-05.md` §3.3
(the four-row exit decode that produced the "≈ 0 GW margin-driven exits" bound) →
FFR-7A `docs/handoffs/ffr-7a-scoring-target-hygiene-2026-08-06.md` §4 / §9.1 (the corrected
target is **larger**, thermal 1.534 → 2.294 GW, and contains +1.7 GW of physical exits the
FFR-6A decode never saw — so its bound "needs re-deriving on the corrected target before it
is relied on again").

**The question.** Was **any** newly-visible exit margin-driven? Restate the bound.

---

## 1. PRE-REGISTRATION

*Everything in this section was written and committed **before any margin was computed**
(commit "FFR-7C: pre-register the corrected-target exit decode"). Nothing in §1 changed
afterwards.*

### 1.1 The unit list — mechanical, from the committed corrected target

Selection rule, applied to `data/raw/_validation-source/capacity_actuals_ercot.csv`
(md5 `03b34821ba53854a410de42ca69afbc0`, written by FFR-7A at `bd2c972e`):

> every row with `kind == retirement`, `fuel ∈ score_capacity_hindcast.THERMAL_FUELS`
> (`{coal, gas_cc, gas_ct, gas_st, oil, nuclear, biomass}`), `mw ≥ 100.0`, and exit year in
> the scored window 2021–2025.

That is **5 units / 2,009.0 MW = 87.6 % of the corrected 2.294 GW thermal target**. Four are
newly visible (`change == added` in `docs/handoffs/ffr-7a/target-delta.csv`); one is the
pre-existing row FFR-6A already decoded.

| # | unit_id | plant | name | target fuel | MW | exit yr | in FFR-6A decode? |
|---|---|---:|---|---|---:|---:|---|
| 1 | `56611_S01` | 56611 | Sandy Creek Energy Station | `coal` | 1008.0 | 2025 | **NO — new** |
| 2 | `3612_2` | 3612 | V H Braunig 2 | `gas_ct` † | 252.0 | 2025 | **NO — new** |
| 3 | `3612_1` | 3612 | V H Braunig 1 | `gas_ct` † | 225.0 | 2025 | **NO — new** |
| 4 | `52120_G-66` | 52120 | — | `gas_cc` | 119.0 | 2023 | **NO — new** |
| 5 | `3548_2` | 3548 | Decker Creek 2 | `gas_ct` † | 405.0 | 2022 | yes (§3.3 row 2) |

† **The known `gas_st` ↔ `gas_ct` taxonomy seam** (FFR-7A §4.1): `data.fleet._map_fuel_type`
has no `gas_st` branch, so natural-gas **steam** units land in the target as `gas_ct`. Units
2/3/5 are physically tangentially-fired gas **steam boilers** (CAMPD `unitType`). **KNOWN and
OUT OF SCOPE — nothing is changed here.** Its only effect on this lane is *which bar* to
adjudicate against, so each of these three units is scored against **both** bars (§1.3) and
the verdict is reported as bar-invariant or not.

Newly-visible thermal MW covered: **1,604.0 of the 1,692.1 MW FFR-7A added (94.8 %)**; the
88.1 MW remainder is 5 rows, all < 100 MW (`52120_G-64` 64.8 gas_cc, `50118_GEN4` 7.6 gas_cc,
`50150_GEN7` 6.0 gas_ct, `59381_GT-1` 5.0 gas_ct, `58069_55M1` 4.7 oil). `50304_GEN1`
(45.9 MW, 2025) is fuel `other`, outside `THERMAL_FUELS`, and is not part of the 1,692.1 MW
thermal delta. Selection verified mechanically before commit: 5 rows / 2,009.0 MW against a
44-row, 2.294 GW-thermal target spanning 2021–2025.

### 1.2 The margin construction (FFR-6A §3.1 / the standing SOM replica — extended, not forked)

`M_u(y)` = pro-forma **attainable** margin at MEASURED prices, $/kW-yr, exactly the SOM
price-taker pro-forma the standing replica validates at **0.89–0.97** against published
Potomac-SOM net revenue (`scripts/probes/fom_scarcity_revenue_audit.py`,
`docs/handoffs/fom-scarcity-revenue-audit-2026-07-05.json`), reused by import:

```
M_u(y) = Σ_t max(0, p_t − mc_t) × (1 − 0.10) / 1000
mc_t   = HR × fuel_t + VOM
```

* `p_t` — measured ERCOT hourly RT hub price, `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`.
* `0.10` — the SOM total-outage assumption (2024 SOM fn. 48), as FFR-6A used it.
* gas `fuel_t` — daily Henry Hub `data/raw/gas-prices/henry_hub_daily.csv` (FFR-6A's basis,
  kept for comparability); an **ERCOT delivered-gas sensitivity** is reported alongside.
* coal `fuel` — the model's own measured delivered **PRB** basis for plant 56611
  (`COAL_PLANT_SUPPLY[56611] == "prb"`; EIA-923 monthly receipts +
  `constants.PRB_PRICE_BY_YEAR`), cross-checked against the SOM-cited 2024 coal
  mc ≈ $23.18/MWh FFR-6A used.

Two heat-rate variants per unit, both reported; **(ii) is the adjudicating column**:

* **(i) FFR-6A class proxy** — gas_ct/gas_st HR 10.5, gas_cc HR 7.0, VOM $4/MWh; coal at the
  SOM-cited mc. Reproduces FFR-6A's `measured-price-replica-2026-08-06.txt` numbers exactly
  (a validation gate on this session's arithmetic: it must reproduce, or the run is void).
* **(ii) UNIT-MEASURED** — the unit's own heat rate from committed CAMPD unit-level data
  (`Σ heatInput / Σ grossLoad` over its last full operating years), VOM from
  `constants.VOM[class]`. This is the read the charter asks for: FFR-6A's own stated
  comparability caveat is that class proxies misprice a specific unit, and Sandy Creek
  (supercritical) and Braunig (1960s-70s steam) sit on opposite sides of that.

Rule-13 posture: identical to FFR-6A's R2 — the replica **consumes** measured outcomes, so it
can never be a screen input; it exists only to size a unit's realized margin against its bar.
Nothing here is wired into any solve path.

### 1.3 The bars (shipped values, unchanged)

`B(f) = ScenarioConfig.fixed_om_<f> × retirement_fom_multiplier_<f>`:

| fuel | FOM | mult | **bar $/kW-yr** |
|---|---:|---:|---:|
| coal | 45.0 | 1.3 | **58.5** |
| gas_cc | 30.0 | 1.0 | **30.0** |
| gas_ct | 21.0 | 1.0 | **21.0** |
| gas_st | 35.0 | 1.0 | **35.0** |

FFR-6A §3.2 measured these bars as externally consistent (coal 58.5 vs the SOM-cited EIA
existing-coal FOM 61.60, −5 %); that finding is **not** re-opened here.

### 1.4 THE DECISION RULE (pre-registered)

For unit `u` with corrected-target exit year `Y_u` and fuel `f_u`:

* **PRIMARY — the charter's rule.** `u`'s exit is **economically consistent** iff
  `M_u(Y_u − 1) < B(f_u)`. One year, one bar, no discretion.
* **SECONDARY — screen-faithful timing.** The shipped R-NEW pipeline rule decides at the LOSS
  year `Y_u − L_f` and executes after the identified lag `L_f =
  ScenarioConfig.retirement_execution_lag_<f>` (`coal 3`, `gas_ct 2`, `gas_cc 1`, `gas_st 1`;
  `retirements.py:_apply_pipeline_retirements` component 4). Report `M_u` across the whole
  window `[Y_u − L_f, Y_u − 1]` and flag "consistent under the screen's own timing" iff
  `M_u(Y_u − L_f) < B(f_u)`.
* **Adjudication.** The PRIMARY rule decides the verdict. The SECONDARY is reported so a
  disagreement is visible rather than chosen between after the fact. A unit counts toward the
  restated margin-consistent total only on the PRIMARY rule.
* **Bar-seam handling.** For the three physically-gas-steam units, "consistent" requires the
  test to pass against the bar actually applied. Both bars (21.0 and 35.0) are computed; if
  the verdict is the same under both it is reported as bar-invariant, and if it differs, the
  unit is reported as **seam-dependent** and counted under the target's own taxonomy
  (`gas_ct`, bar 21.0) with the divergence stated.
* **Non-computable → not counted.** If a unit's characteristics or its year's prices cannot be
  read from committed artifacts, it is reported `UNRESOLVED`, never assumed either way.

### 1.5 Pre-registered expectation (stated before computing)

**Expectation: NO newly-visible exit is margin-driven; the ≈ 0 GW bound survives at the larger
denominator.** Basis, all from FFR-6A's already-published replica column (its
`measured-price-replica-2026-08-06.txt`, i.e. the *class-proxy* variant): in the relevant
years the measured-price margin clears every bar with room —
coal 2024 **75.4** vs 58.5 and 2022 **321.7** vs 58.5; gas_st-proxy 2022 **129.7** vs 35,
2024 **65.6** vs 35, 2025 **47.0** vs 35; gas_cc 2022 **176.4** vs 30.

The **one genuinely open case is Sandy Creek**, and it is open for reasons the class proxy
cannot settle: it is the only newly-visible unit whose bar is within ~1.3× of the class-proxy
margin (75.4 / 58.5 in 2024), it is the only unit in the list whose **unit heat rate is
plausibly better than the class proxy** (supercritical), and it is the only ≥ 300 MW coal exit
in the corrected target. If any unit flips the bound, the pre-registered guess is that it is
this one, and in the direction of *clearing more*, not less.

Also pre-registered: **Braunig 1/2 carry an enforceable public instrument** — ERCOT NSO
M-C031324-01, `instrument_date 2024-03-13`, already rows `ercot-nso-braunig-1/2` in
`data/raw/confirmed-retirements/ercot.csv`. **Sandy Creek carries no such row** (the ERCOT
registry holds only the three Braunig units). This is stated in advance because it is the fact
that would distinguish "instrument-driven" from "margin-driven" if the margins came out
ambiguous — and because a margin-consistent verdict for a unit that also has an instrument is
still a margin-consistent verdict, not a re-attribution.

### 1.6 What this lane will NOT do

1. No recommendation on **D-21(a)** (DEFERRED by the owner, sitting V.6) and none on the
   FH-4/FH-5 lift. §5 **reports** the implication; the manager takes it to the owner.
2. No change to `_map_fuel_type`, the `gas_st`/`gas_ct` seam, the bars, any `ScenarioConfig`
   field, any scorer, any target, or any registered bundle.
3. No decision on FFR-7A §9.3 (the OP-only vintage gate). §6 reports it as a measured table.
4. No mechanism tested ⇒ no matrix cell adjudicated (rule 28).

---

## 2. Results

*(filled after §1 was committed; nothing above this line changed after)*

### 2.0 Headline

**No newly-visible exit was margin-driven. ERCOT's margin-consistent exit total 2021–2025 on
the CORRECTED target is 0 MW of 2,294 MW thermal — the ≈ 0 GW bound SURVIVES, at the larger
denominator.** All five units in the pre-registered list clear their bar in the year before
exit, and in *every* window year, on *every* variant computed (class proxy, unit-measured
gross HR, unit-measured net HR, the model's own carried bin HR, and both fuel-price bases).
The pre-registered expectation held, including its guess that Sandy Creek would be the
closest call: at **73.4 vs 58.5 $/kW-yr** it clears by 1.25×, the narrowest margin anywhere
in the decode.

### 2.1 Reproduction gate — PASS

`scripts/probes/ffr7c_exit_decode.py` imports `price_taker_net_revenue` / `SOM_OUTAGE_RATE`
from the standing SOM replica and reproduces FFR-6A's published
`measured-price-replica-2026-08-06.txt` in **all five window years, all four classes**, to
< 0.06 $/kW-yr (`gas_ct`, `gas_cc`, `p_mean`, `gas_mean` are exact to the printed digit).

One methodological correction falls out of the gate, and it is in FFR-6A's favour. FFR-6A's
prose says its coal column used "the SOM-cited mc ≈ $23.18/MWh (2024; 2023/2025 via the same
PRB fuel-cost basis)". By inversion its published coal figures are reproduced in **every**
year by a **flat $23.18/MWh** (and nuclear by a flat $10.00/MWh) — the PRB basis was not
year-varied. This session's adjudicating column uses the unit's own measured heat rate against
the **measured monthly delivered PRB series** instead, so the correction is absorbed rather
than inherited. It moves nothing: at the true year-specific PRB cost Sandy Creek's margins are
within a few $/kW-yr of the flat-mc proxy in every year.

### 2.2 THE PER-UNIT MARGIN TABLE

Adjudicating column is **unit-net** (the unit's own measured CAMPD heat rate, grossed up to a
net heat rate by its class parasitic load, priced at `constants.VOM`). All figures $/kW-yr.
**Bold** = the pre-registered PRIMARY test year (exit year − 1).

**1. Sandy Creek 1 — `56611_S01`, 1,008 MW supercritical PRB coal, exit 2025. Bar 58.5.**

| year | measured HR (gross → net) | class proxy | model bin HR 9.50 | **unit-net** | unit-net @ model PRB | vs bar | CAMPD op-h / GWh |
|---:|---|---:|---:|---:|---:|---:|---|
| 2021 | 9.91 → 10.65 | 1013.3 | 1023.0 | 1013.8 | — | 17.3× | 7,735 / 5,721 |
| 2022 † | 10.66 → 11.46 | 321.7 | 322.9 | **298.7** ‡ | — | 5.1× | 6,669 / 4,177 |
| 2023 | 10.19 → 10.96 | 234.1 | 239.4 | 230.4 | 221.0 | 3.9× | 7,195 / 3,550 |
| **2024** | 10.35 → 11.13 | 75.4 | 81.8 | **73.4** | 67.2 | **1.25×** | 6,791 / 3,277 |
| 2025 | 10.05 → 10.81 | 97.2 | 115.5 | 103.9 | 84.5 | 1.78× | 1,320 / 768 |

† the pipeline rule's LOSS year for a 2025 coal exit (`retirement_execution_lag_coal = 3`).
‡ SECONDARY test: **298.7 vs 58.5, clears 5.1×** — the screen's own timing agrees with the
primary rule, emphatically.

**VERDICT: NOT margin-driven.** Clears on the primary rule (73.4 > 58.5), on the secondary
rule (298.7 > 58.5), in every window year, and on the conservative fuel sensitivity (the
model's own `PRB_PRICE_BY_YEAR` 2.00–2.15 $/MMBtu, above the measured 1.62–1.94: 67.2 > 58.5,
still +15 %). The 2025 collapse in output (1,320 operating hours, 768 GWh vs 3,277 GWh in
2024) is the physical cessation the corrected target dates — it is *not* preceded by a
margin failure.

**2. V H Braunig 1 — `3612_1`, 225 MW gas steam, exit 2025. Bars 21.0 (target `gas_ct`) / 35.0 (physical `gas_st`).**

| year | HR (gross → net) | class proxy | bin HR 8.49 | **unit-net** | unit-net @ ERCOT gas | CAMPD op-h / GWh |
|---:|---|---:|---:|---:|---:|---|
| 2021 | 10.77 → 11.34 | 945.1 | 957.3 | 941.3 | 822.9 | 2,140 / 199 |
| 2022 | 11.21 → 11.80 | 129.7 | 148.2 | 122.9 | 122.6 | 3,466 / 334 |
| 2023 † | 9.31 → 9.80 | 216.4 | 227.7 | **219.8** | 209.3 | 3,169 / 410 |
| **2024** ‡ | 9.09 → 9.57 | 65.6 | 75.7 | **69.7** | 64.1 | 2,344 / 327 |
| 2025 | 8.85 → 9.32 | 47.0 | 61.0 | 54.5 | 68.4 | 1,339 / 236 |

**3. V H Braunig 2 — `3612_2`, 252 MW gas steam, exit 2025. Same bars.**

| year | HR (gross → net) | class proxy | bin HR 8.49 | **unit-net** | unit-net @ ERCOT gas | CAMPD op-h / GWh |
|---:|---|---:|---:|---:|---:|---|
| 2021 | 10.98 → 11.56 | 945.1 | 957.3 | 940.4 | 820.5 | 1,358 / 133 |
| 2022 | 12.31 → 12.96 | 129.7 | 148.2 | 118.2 | 117.8 | 1,889 / 134 |
| 2023 † | 10.95 → 11.53 | 216.4 | 227.7 | **212.0** | 202.3 | 2,040 / 183 |
| **2024** ‡ | 10.53 → 11.08 | 65.6 | 75.7 | **63.4** | 58.3 | 1,143 / 114 |
| 2025 | 10.64 → 11.20 | 47.0 | 61.0 | 43.3 | 55.3 | 203 / 18 |

† LOSS year under the target's `gas_ct` taxonomy (lag 2). ‡ LOSS year under the physical
`gas_st` class (lag 1) — and also the primary test year.

**VERDICT (both): NOT margin-driven, BAR-INVARIANT.** Braunig 1 clears 3.3× (vs 21.0) /
2.0× (vs 35.0); Braunig 2 clears 3.0× / 1.8×. The secondary rule agrees under **both**
taxonomies (2023: 219.8 / 212.0 ≫ either bar; 2024: as above). The `gas_st`↔`gas_ct` seam
therefore **cannot change the verdict** for these units — noted, changed nothing. Even the
weakest cell anywhere in their history (Braunig 2 in 2025, its own exit year, 43.3) sits
above the higher of the two bars.

**4. Freeport Energy G-66 — `52120_G-66`, 119 MW, exit 2023. Bar 30.0.**

| year | class proxy (HR 7.0) | model bin HR 5.86 | vs bar |
|---:|---:|---:|---:|
| 2021 | 972.4 | 996.6 | 32.4× |
| 2022 † | **176.4** | 215.1 | **5.9×** |
| **2023** | (exit year) 240.0 | 263.1 | — |

† 2022 is BOTH the primary test year (exit − 1) and the LOSS year (`gas_cc` lag 1).

`UNRESOLVED` was pre-registered as the fallback if a unit's characteristics were unreadable.
It is **not** invoked: the unit is not a CAMPD reporter, but two committed non-CAMPD heat
rates bracket it — the SOM class proxy (7.0) and the model's own carried bin HR (5.86,
`H_CHP2`) — and both clear the bar by ≥ 5.9× in the test year, so the verdict is robust
across the whole plausible range and does not depend on the missing measurement.
**VERDICT: NOT margin-driven.**

Material context, not used in the adjudication: EIA-860 classes plant 52120 **`Industrial CHP`
(Sector 7, `Associated with CHP = Y`)**. A cogeneration block's retirement is governed by its
host's steam demand, not by merchant energy margin — the same category of driver as a
municipal fleet plan, and outside anything a margin screen models.

**5. Decker Creek 2 — `3548_2`, 405 MW gas steam, exit 2022. Bars 21.0 / 35.0. (FFR-6A's own row, re-derived.)**

| year | HR (gross → net) | class proxy | **unit-net** | unit-net @ ERCOT gas | CAMPD op-h / GWh |
|---:|---|---:|---:|---:|---|
| **2021** † | 11.61 → 12.22 | 945.1 | **937.8** | 813.3 | 5,876 / 672 |
| 2022 | 12.18 → 12.82 | 129.7 | 118.7 | 118.3 | 936 / 79 |

† primary test year, and the LOSS year under the physical `gas_st` lag of 1. The
target-taxonomy `gas_ct` lag of 2 would point at **2020**, which is outside this decode's
2021–2025 window and is **not evaluated** (ERCOT holds no `complete` marker; §7). The verdict
does not depend on it — 2021 alone settles it at 937.8 vs 21.0/35.0, i.e. **26.8–44.7×**.

**VERDICT: NOT margin-driven — FFR-6A's finding CONFIRMED and strengthened.** FFR-6A read
this row at the class proxy on the exit year (129.7 vs 35, "margin-POSITIVE 3.7× at exit");
on the pre-registered primary rule and the unit's own heat rate it is margin-positive by
**26.8×**, because 2021 is the Uri year.

### 2.3 Roll-up

| unit | MW | exit | primary-year margin | bar(s) | ratio | margin-consistent exit? |
|---|---:|---:|---:|---:|---:|---|
| Sandy Creek 1 | 1,008.0 | 2025 | 73.4 | 58.5 | 1.25× | **NO** |
| Decker Creek 2 | 405.0 | 2022 | 937.8 | 21.0 / 35.0 | 44.7× / 26.8× | **NO** |
| V H Braunig 2 | 252.0 | 2025 | 63.4 | 21.0 / 35.0 | 3.0× / 1.8× | **NO** |
| V H Braunig 1 | 225.0 | 2025 | 69.7 | 21.0 / 35.0 | 3.3× / 2.0× | **NO** |
| Freeport G-66 | 119.0 | 2023 | 176.4 | 30.0 | 5.9× | **NO** |
| **total** | **2,009.0** | | | | | **0 MW margin-consistent** |

Coverage: 2,009.0 of 2,294 MW thermal (87.6 %); 1,604.0 of the 1,692.1 MW newly visible
(94.8 %). The undecoded remainder is 285.0 MW across 23 sub-100 MW rows (88.1 MW of them
newly visible, 196.9 MW pre-existing; the largest is 75 MW) — at the bar ratios above, no
plausible small-unit result changes a 0-of-2,009 MW finding, and FFR-6A treated the same tail
the same way ("< 100 MW each, below the CAMPD per-plant fleet grain").

### 2.4 Two structural facts the decode surfaced (evidence, not adjudication)

Both come from `data/raw/reference/custom-bin-assignments.csv`, the committed sheet the arms'
`run_config` names as `campd_bins_path` with `use_campd_bins = True` — i.e. the model's actual
ERCOT fleet.

1. **Sandy Creek IS in the fleet, at its own grain.** `SC_COAL3`, plant 56611, 936.0 MW,
   carried HR 9.50 — a single-unit plant, so the bin *is* the unit. The charter's premise
   holds: this is a unit a screen could have retired, and the decode says it should not have.
   (For completeness, it is absent from `master-plant-registry.csv`'s ERCOT coal cohort — that
   file is a current-vintage snapshot and, per `campd_bins.load_plant_registry`'s own
   docstring, "is not consumed by dispatch directly". The bin sheet is what the fleet is built
   from. This is the likely origin of FFR-6A §3.3's "the FFR-5A coal cohort lists 9 plants".)
2. **Decker Creek 2 is NOT in the fleet — a second Deely-class row in the corrected target.**
   Plant 3548 appears in the bin sheet only as `CT8`, a 206.0 MW `CT_PEAKER` block (the eight
   GT-nA/nB units); the 405 MW steam unit 2 has no bin. So 405 MW of the corrected 2,294 MW
   thermal target is capacity the arm's fleet never carried and no screen could reach —
   exactly the pathology FFR-7A removed for Deely, still present for Decker. **Reported, not
   fixed** (out of this lane's scope, and it is a fleet-basis/target-alignment question, not a
   status-hygiene one).

   Braunig is a third grain fact, milder: `SC_STGAS3` is the **whole plant** at 1,138.0 MW
   (units 1+2+3 plus four CTs), so a screen can only retire the bin, never the 477 MW the
   target scores. Braunig 3 (417 MW) is still operating under an RMR through 2027.

---

## 3. WHICH FFR-6A CONCLUSIONS SURVIVE

FFR-6A's four load-bearing conclusions, each stated against this session's evidence.

| # | FFR-6A conclusion | status on the corrected target |
|---|---|---|
| 1 | **The gap is the forward PRICE OBJECT, not the margin construction** (§3.1/§3.2/§4a: repaired screens at 0.04–4.4 % of measured-price margin; object mean $9.5–10.5 vs measured $26.8–32.5; zero object hours > $100 vs 161/217 measured; 96–100 % of the gap is the energy price-level/tail term) | **UNTOUCHED — VERIFIED.** Every input to it is a model-side/measured-price quantity; not one of them is a function of the retirement target. This session independently re-derived the measured-price side of that comparison from the same sources and **reproduced FFR-6A's replica table exactly in all five years** (§2.1), so the gap arithmetic stands as published. Needed no re-derivation. |
| 2 | **The bar is NOT mis-leveled** (§4b: coal 58.5 vs SOM-cited EIA 61.60; nuclear 130 vs NEI ≈ 150; ATB gas FOMs unchallenged; bar term ≤ 5 % of any fuel's gap) | **UNTOUCHED — VERIFIED.** A bar-vs-external-benchmark comparison contains no target term. Independently corroborated here from the other side: the shipped bars correctly classify **all five** of the corrected target's large exits as non-economic, and would still do so with the coal bar moved anywhere below 73.4 or the `gas_st` bar anywhere below 63.4. The bars are not what is wrong. |
| 3 | **The exit DECODE** (§3.3's four rows: Deely a paper event outside the fleet, Decker margin-positive, small units sub-grain, Braunig absent from the actuals) | **RE-DERIVED — this session.** The row inventory was incomplete (Sandy Creek, Freeport G-66 and the papered Braunig rows were invisible in the old target) and one row's stated reason is superseded: Deely is **no longer in the target at all** (FFR-7A dropped it), so "the scorer's own target contains it" is now false, and Braunig is **no longer absent** from the actuals. Of the reasons that remain, Decker's is confirmed and strengthened (§2.2 row 5). |
| 4 | **THE BOUND: ERCOT's true margin-driven exit total 2021–2025 is ≈ 0 GW; a correct margin screen should execute approximately nothing in this window** | **SURVIVES — and is now stronger.** Restated on the corrected target it is **0 MW of 2,294 MW**, decoded over 87.6 % of the thermal target instead of the old four rows, with per-unit measured heat rates instead of class proxies, and with the two largest exits (Sandy Creek 1,008 MW, Decker 405 MW) each clearing on every variant. The 1.53 → 2.29 GW target growth **did not import any economic-exit content**. |

**The one FFR-6A sentence that must be retired**: §3.3's parenthetical dismissal of Deely as
"the scorer's own target contains it". FFR-7A removed that row; the accurate statement now is
that the corrected target's Deely-class residue is **Decker Creek 2 (405 MW)**, absent from
the fleet for a different reason (the bin sheet carries only 3548's CT block), and that this
is the sole remaining unreachable-by-construction MW in the ERCOT target.

**What FFR-6A's §5 recommendation card looks like after this session.** Row 1 (charter the
forward-object scarcity diagnosis) and rows 3/4 (the admissible AS-quantity input; refuse bar
re-levels and signal scaling) are untouched — none of them depends on the target. Row 2
("retirement scoring should stop chasing 1.534 GW as a margin target") is the one that FFR-7A
appeared to unsettle by making the number bigger; **this session settles it in FFR-6A's
favour**: the right number to stop chasing is now 2.294 GW, and the reason is unchanged and
better evidenced.

---

## 4. THE RESTATED BOUND

> **ERCOT's margin-consistent exit total, 2021–2025, on the CORRECTED retirement target, is
> 0 MW.**
>
> Denominator: 2.294 GW thermal (44 rows), of which 2,009 MW (87.6 %) across the five ≥ 100 MW
> units is decoded unit-by-unit here and none is margin-consistent. Every one of them clears
> its going-forward bar at measured ERCOT RT prices in the year before its exit — by 1.25×
> (Sandy Creek, the tightest), 1.8–3.3× (Braunig 1/2), 5.9× (Freeport G-66) and 26.8× (Decker
> Creek 2) — and also in the pipeline rule's own loss year, and on every heat-rate and
> fuel-price variant computed.
>
> The +1.7 GW of physical exits FFR-7A made visible added **zero** margin-driven exits. The
> +0.76 GW net growth in the target is entirely instrument-, cogeneration-host- and
> fleet-plan-driven capacity, plus one Deely-class row (Decker Creek 2, 405 MW) the model
> fleet does not carry at all.
>
> A correct margin screen's job in this window remains: retire **approximately nothing**,
> while the announced/confirmed-instrument channels carry the real exits. Both FFR-5D failure
> modes — shipped "fail everything at raw duals" and repaired "fail everything at the
> collapsed lookahead" — still get the in-window number right only through the admission cap.

**Every exit's actual driver, for the record** (all from committed registry/EIA data, none of
it used in the adjudication): Braunig 1/2 — ERCOT NSO M-C031324-01, `instrument_date`
2024-03-13, already carried as `ercot-nso-braunig-1/2` in
`data/raw/confirmed-retirements/ercot.csv` (an enforceable public instrument; its date falls
*after* the vintage-2020 information gate, so the confirmed-exit channel correctly does not
fire in this hindcast). Decker Creek 2 — Austin Energy municipal fleet plan. Freeport G-66 —
industrial CHP, host-driven. Sandy Creek — **no confirmed-exit registry row exists** (the
ERCOT file holds only the three Braunig units), so its driver is not established from
committed artifacts, and this document does not speculate about it. What *is* established is
that it was not a margin failure.

---

## 5. IMPLICATION FOR D-21(a) — REPORTED, NOT RECOMMENDED

D-21(a) is **DEFERRED by the owner** (sitting V.6). This lane recommends nothing about it or
about the FH-4/FH-5 lift; the manager takes the following to the owner.

The charter framed a fork. **The second branch is the one that obtains:**

> *"if Sandy Creek's exit was margin-driven, the corrected screen has a real in-window
> economic-exit target and the price-object diagnosis gains a validation case; if not, the
> ≈ 0 bound is restored at the larger denominator."*

**Sandy Creek's exit was not margin-driven** (73.4 vs 58.5 in 2024; 298.7 vs 58.5 in the
screen's own 2022 loss year). Therefore:

* **The ≈ 0 bound is restored at the larger denominator.** The corrected screen still has
  **no** in-window economic-exit target in ERCOT, and the price-object diagnosis gains **no**
  validation case from this window.
* **The FFR-5D unified arm's 10.9 GW `gas_st` wave remains a pure false-retire** — its
  false-retire fraction of 1.00 is not softened by anything in the corrected target, and
  FFR-7A's `err_frac` improvement 6.135 → 3.770 remains what FFR-7A said it was: denominator
  growth, not progress.
* **What this changes for D-21(a) is the *kind* of evidence available, not the diagnosis.**
  FFR-6A's price-object finding stands on its own measured decomposition (§3 row 1 above),
  which never depended on the target. What is now settled is that ERCOT 2021–2025 cannot
  supply a *positive* test of a repaired price object via retirements — a correct object must
  produce ≈ 0 economic exits here, so this window can falsify an over-retiring screen but can
  never confirm a correctly-retiring one. Any validation case for the price-object repair has
  to come from the price side (the 161/217 h > $100 the object misses), not the exit side.
* **A second-order consequence worth the owner's attention:** the corrected target's 405 MW
  Decker Creek 2 row is scored against a fleet that does not carry the unit, so ERCOT's
  recall-on-≥ 300 MW metric is currently unachievable-by-construction on one of its two
  members (the other being Sandy Creek, which a correct screen should *not* retire). The
  ≥ 300 MW recall gate is therefore measuring something no admissible screen can pass. Flagged
  for the owner as a scoring-target question; **not** acted on here.

---

## 6. FFR-7A §9.3 — WOULD AN OP-ONLY VINTAGE GATE CHANGE THE TARGET? (measured, reported)

FFR-7A §1.2 gated out units already `OS`/`RE` at the fleet vintage and explicitly left
"keep only units that were `OP` at the vintage" to the owner. `scripts/probes/ffr7c_op_only_gate.py`
measures it by re-running the shipped `build_capacity_actuals.build_retirements` read-only and
tagging every retained row with its EIA-860 `Status` at the RY2020 release. The rebuild
reproduces all five committed targets exactly (row counts and thermal GW match FFR-7A §2), so
the classification is of the shipped target, not a variant of it.

Two widenings are separable, so both are reported and the owner can adopt either alone:

| ISO | current rows | current thermal GW | **(a) OP-only: `SB`/`OA` dropped** | | | **(b) also drop absent-at-vintage** | | |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| | | | rows | MW | thermal MW | rows | MW | thermal MW |
| **ERCOT** | 44 | 2.294 | **1** | **7.6** | **7.6** | 3 | 112.0 | **0.0** |
| PJM | 305 | 15.062 | 18 | 150.5 | 126.5 | 13 | 1,167.8 | **1,167.8** |
| MISO | 289 | 17.369 | 84 | 426.0 | 392.7 | 2 | 3.0 | 3.0 |
| NYISO | 99 | 1.711 | 35 | 36.5 | 18.4 | 3 | 1.1 | 1.1 |
| NEISO | 85 | 3.253 | 7 | 21.5 | 21.5 | 0 | 0.0 | 0.0 |

Reading it:

* **ERCOT is essentially invariant.** (a) removes exactly one row — `50118_GEN4`, 7.6 MW
  `gas_cc`, `SB` at vintage (status series `2019:SB;…;2023:SB;2024:OS`) — i.e. **0.3 % of the
  thermal target**. (b) removes 3 non-thermal rows / 112 MW, of which the only unit ≥ 25 MW is
  `63737_CHS01` (100 MW storage, COD inside the window — a genuine in-window build, exactly
  the case the builder's docstring says should *not* be gated). **Nothing in §4's bound moves
  under either widening.**
* **(a) bites hardest on MISO** (84 rows, 392.7 MW thermal — mostly small `SB` units;
  largest are `10075_GEN1/GEN2`, 84 MW coal each, 2023) and on **NYISO by row count**
  (35 rows but only 18.4 MW thermal — sub-MW `SB` hydro/oil). It is a **row-count** effect
  almost everywhere, not a GW effect: across all five ISOs (a) removes 145 rows but only
  0.567 GW thermal, ≈ 1.4 % of the 39.7 GW five-ISO thermal total.
* **(b) is materially different in PJM and only in PJM: 1,167.8 MW, all thermal, 7.8 % of
  PJM's target.** It is four units plus nine small ones: `65285_ST1`/`ST2` (364 MW coal each,
  exit 2021) and `69979_GT8`/`GT9` (192 MW each, exit 2025 — the MPH Elwood plant-code change
  FFR-7A §5 already flagged as unreconciled). These are release-coverage/plant-code artifacts,
  not in-window builds, so they are the *opposite* of the case the docstring's counter-argument
  covers — which is precisely why (b) should be decided separately from (a) rather than folded
  into an "OP-only" label.
* **Recommendation: none.** Both are the owner's call. The measured fact this lane owns is
  narrow and unambiguous: **neither widening changes ERCOT's corrected target enough to affect
  §4's restated bound**, so the FFR-7C result is stable under either decision.

---

## 7. Governance

* **Rule 22 — nothing spent.** No solve, no score of any model output, no registration. Both
  probes read committed artifacts only and produce no model output of any kind; the
  measured-price replica is the same rule-13 *benchmark* construction FFR-6A used, consuming
  measured outcomes and therefore permanently unusable as a screen input. The decode window is
  **2021–2025**, the same span FFR-6A used. **ERCOT holds no `complete` and no `final` marker**
  (`frontend/data/backcast/calibration-complete.json`: `complete` = NEISO/NYISO/PJM only), and
  the **holdout spend freeze is ACTIVE** (`holdout-freeze.json`; the 2026-08-06 lift was
  narrow, single-purpose and NEISO-only, and was re-armed in the same session) — so the one
  place a pre-2021 year would have been convenient, Decker Creek 2's `gas_ct`-taxonomy loss
  year of **2020**, was **deliberately left unevaluated**. §2.2 row 5 shows the verdict does
  not depend on it.
* **Rule 13/14 posture.** Every input is a reproducible measured physical/market quantity
  (hourly RT prices, Henry Hub, the TX electric-power delivered-gas series, EIA-923 PRB
  receipts, CAMPD heat input/gross load, EIA-860 status and technology) used **only** as a
  diagnostic benchmark. Nothing is wired into a solve path; no residual was consulted; nothing
  was tuned toward any number.
* **Rule 15/16.** No run solved, none registered; no dashboard file touched. Both FFR-5D arms
  keep their existing registrations and their committed bundles are untouched.
* **Rule 28.** **No mechanism was proposed, tested, armed or refuted, so no matrix cell is
  adjudicated and no header re-stamp is due.** The ERCOT `capacity_screen_unified_lookahead`
  cell keeps verdict `O` with its FFR-6A evidence; this session neither arms nor refutes it.
* **Rule 27.** No file ≥ 300 lines was rewritten; the two new probes are new files pushed as
  on-disk bytes. `git status --short` was checked after every Python write — the ruff hook
  reformatted only this session's two new probe files and never touched
  `src/market_sim/config/constants.py`.
* **Rule 23.** Nothing was re-derived. The `$23.18` / `$10.00` constants in the probe are
  *recovered* FFR-6A reproduction anchors, not new parameters, and they feed only the
  comparability column — never the adjudicating one.
* **Owner-decision hygiene.** D-21(a) is **reported on, not re-opened** (§5); FFR-7A verdict
  row 5c (announced fossil dates) stays refused and is not mentioned as an option; the
  FH-4/FH-5 lift is not discussed.

## 8. What was NOT changed

1. No `ScenarioConfig` field, no model mechanism, no scorer, no target, no keeper, no bundle,
   no registration, no matrix cell.
2. **`data.fleet._map_fuel_type` and the `gas_st`↔`gas_ct` seam** — untouched. It touches
   three of the five decoded rows (Braunig 1/2, Decker Creek 2, all physically gas steam,
   all landing in the target as `gas_ct`); §2.2 shows the verdict is **bar-invariant** for
   every one of them, so the seam changes nothing here. Flagged where it lands, changed
   nowhere.
3. **The vintage gate** — measured in §6, not widened.
4. **The Decker Creek 2 fleet-absence** (§2.4 item 2) and the **≥ 300 MW recall-gate
   consequence** (§5) — reported, not fixed.
5. **FFR-6A's document** — not overwritten. §3 records which of its conclusions survive; it
   stands as the historical record of what was measurable at the time.

## 9. Artifacts

| path | what |
|---|---|
| `scripts/probes/ffr7c_exit_decode.py` | the decode: reproduction gate + per-unit margins, all variants |
| `docs/handoffs/ffr-7c/exit-decode-2026-08-06.json` | its output — per unit, per year, every variant, both bars, both loss years |
| `scripts/probes/ffr7c_op_only_gate.py` | the §6 OP-only measurement (shipped builder, read-only) |
| `docs/handoffs/ffr-7c/op-only-gate-2026-08-06.json` | its output — per-ISO census + the dropped-unit lists |

Reproduce with:

```
uv run python scripts/probes/ffr7c_exit_decode.py  --out docs/handoffs/ffr-7c/exit-decode-2026-08-06.json
uv run python scripts/probes/ffr7c_op_only_gate.py --out docs/handoffs/ffr-7c/op-only-gate-2026-08-06.json
```
