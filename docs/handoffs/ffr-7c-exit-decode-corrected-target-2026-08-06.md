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

<!-- FFR-7C-RESULTS-ANCHOR -->
