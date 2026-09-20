# FINDING — nyiso-248: the daily citygate is ALREADY ARMED at full measured amplitude, and the object that replaces it is a CONDITIONER defect in the lane's own evidence

**Session** nyiso-248 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container, and zero
shards launched**).
**Date** 2026-09-20. **Base** `origin/main` at `c6a350c4`.
**Keeper (UNCHANGED, untouched)** `2026-09-20-nyiso247-fuel-invariance-disarm`, bundle
`results/calibration/nyiso247_fuelinv_span`, years {2022, 2023, 2024, 2025}. **NYISO stays
CALIBRATED.** No `ScenarioConfig` field moved, no solve was spent, no keeper number changed.

> ## HEADLINE
> 1. **THE LANE'S OBJECT DOES NOT EXIST.** The assigned object was "the keeper's delivered gas is
>    smooth where the real NYC/Transco Z6 winter citygate is spiky at DAILY grain." Measured:
>    **100 % of NYISO gas capacity already carries a daily delivered-gas series** (271–342 distinct
>    values/yr, every class, all four years), and it already **takes its within-month shape from the
>    measured Transco Z6 NY daily prints on their true calendar days, mean-preserving**.
> 2. **AND IT IS NOT ATTENUATED.** The array the LP actually prices gas on carries **90–120 % of the
>    measured source's within-month dispersion** for CC_REGULAR, CC_CHP, CT_CHP and ST_GAS in every
>    year. There is no amplitude repair to make either.
> 3. **THE PREMISE CAME FROM THE WRONG ARRAY.** The percentiles the lane prompt quotes
>    (2024 `2.170 / 2.309 / … / 6.060`, `max == p97` in all four years) are `_gas_series`
>    (`gas_<year>.npy`) — which is a **pure 12-value MONTHLY STEP** and is *not* what any gas unit is
>    priced on.
> 4. **WHAT IS REAL IS A DEFECT IN THE LANE FAMILY'S OWN EVIDENCE PIPELINE.** That same 12-value
>    monthly step is the **gas coordinate nyiso-245 / -246 / -247 binned the P-27 offer book on**. So
>    "gas ≥ p90 hours" in those sessions means *an hour in one of the year's ~1.2 dearest MONTHS*,
>    not a dear DAY.
> 5. **AND IT BITES, UNEVENLY AND MEASURABLY.** Re-binning the same window on the daily series moves
>    the TIGHT set by Jaccard **0.18 in 2022** (winter share **100 % → 21.0 %**) and **0.68–0.71 in
>    2025**, while 2023/2024 are near-stable (0.82 / 0.90). **A DO-NOT-REDO claim carried into this
>    lane's prompt — "gas ≥ p90 hours are 98–100 % WINTER" — is FALSIFIED for 2022.**
> 6. **NOTHING HERE TOUCHES THE nyiso-247 KEEPER.** Its promotion rested on G-A (an exact
>    conditioner-free identity on the offer slope), G-C, G-D and G-F. Only G-B's *interpretation* is
>    affected. §6 states this at full magnitude rather than burying it.

---

## 1. WHAT WAS ASKED, AND WHY NO GATE TABLE WAS EVER WRITTEN

The lane was handed the daily citygate as a rule 14 `[R-ACCURATE]` measured-input repair, with six
pre-registration duties (a)–(f) owed in a PRECOMMIT before any gated number.

**Duty (a) — "THE SOURCE, and it is the whole ballgame" — killed the object before a gate could be
written.** (a) requires naming the exact daily series and checking *what is already on disk under
`data/raw/gas-prices/` before assuming an intake is needed*. Doing exactly that found
`transco_z6_ny_daily.csv` **committed**, and then found it **already wired, already armed in the
keeper, and already mean-preserving**. There is no PRECOMMIT because there is no arm: pre-registering
gates for a mechanism that is already on would be theatre.

This is the ordering rule 29 `[R-SCREEN]` clause (0) survives as: *a lane that can compute an answer
without an LP still should.* Total cost of this session: **one fleet-cache rebuild (~4 min) and four
probes. Zero LP, zero shards, zero container-hours of solve.**

---

## 2. G-1 — THE GRAIN. **100 % DAILY, EVERY CLASS, EVERY YEAR.**

`scripts/probes/nyiso248_gas_grain_census.py` → `results/calibration/_nyiso248_gas_grain_census.json`.
Reads the committed keeper's own assembled `fuel_prices` out of the fleet cache. A row is MONTHLY
iff its mean within-month CV is < 1e-9.

| year | gas rows | gas MW | **DAILY-grain MW share** | distinct values/row |
|---|---:|---:|---:|---|
| 2022 | 443 | 23,417 | **100.00 %** | 330–342 |
| 2023 | 443 | 23,417 | **100.00 %** | 298–315 |
| 2024 | 448 | 23,424 | **100.00 %** | 289–308 |
| 2025 | 448 | 23,424 | **100.00 %** | 271–331 |

**Zero MW of NYISO gas is on a monthly plateau**, in any year. The mechanism is
`_nyiso_hub_daily_gas_prices` (`data/fuel/hubs.py`), reached because the keeper arms
`gas_hub_basis_overlay` **and** `gas_hub_basis_daily`; it places the measured Transco Z6 NY quotes on
their true calendar days and renormalises the day factors to exactly 1.0 per month.

### 2.1 Two of my own premises, falsified by this gate before anything was designed

* **FALSIFIED — "the gas side of the dual-fuel `min()` is a monthly plateau."** I expected
  `gas_plant_monthly_fuel_pricing=True` to overwrite the daily shape with the EIA-923 monthly print,
  making `dual_fuel_oil_daily_parity` (armed, daily on the oil side) a one-sided grain. It does not:
  the hub overlay runs **after** the plant-monthly pass and re-writes those cells. That docstring's
  stated premise — *"the gas side of the same min() comparison is already DAILY"* — **holds.**
* **FALSIFIED — "NYISO's daily gas shape is the national Henry Hub shape."** `gas_daily_shape_factors`
  is indeed Henry-Hub-derived, but NYISO does not use it for this: `iso_hub_daily_gas_prices`
  branches to a **NYISO-specific leg on Transco Z6 NY** before ever reaching the Henry Hub path. The
  MISO-72 `miso_winter_citygate_daily` analogue this lane was pointed at is therefore **already
  discharged for NYISO, by a different and earlier mechanism.**

---

## 3. G-2 — THE AMPLITUDE. **90–120 % OF THE SOURCE SWING SURVIVES INTO THE LP.**

`scripts/probes/nyiso248_shape_attenuation.py` → `_nyiso248_shape_attenuation.json`.
The comparator is deliberately **level-free**, so nothing here can be read as a level claim: mean
over months of (std/mean) of the **calendar-day** series *inside* each month. Two series at different
levels with the same relative shape score identically.

**Within-month CV, as a percentage of the measured Transco Z6 daily source:**

| stage | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| `1_transco_raw` (the source) | 0.2802 | 0.2800 | 0.2646 | 0.3639 |
| **`2_iso_gas_series`** | **0.0 %** | **0.0 %** | **0.0 %** | **0.0 %** |
| `3_delivered_CC_REGULAR` | 96.8 % | 98.6 % | 105.1 % | 95.4 % |
| `3_delivered_ST_GAS` | 94.8 % | 92.7 % | 104.4 % | 89.5 % |
| `3_delivered_CC_CHP` | 111.0 % | 118.9 % | 120.3 % | 117.5 % |
| `3_delivered_CT_CHP` | 105.9 % | 115.6 % | 118.1 % | 101.5 % |
| `3_delivered_CT_PEAKER` | 69.9 % | 43.6 % | 51.3 % | 52.8 % |

**Read it honestly, in both directions:**

* **The price-setting classes are not attenuated.** CC_REGULAR and ST_GAS — 16.4 GW, the rungs that
  set a NYISO price — carry **89–105 %** of the measured source swing. A mean-preserving multiplicative
  shape is supposed to preserve relative dispersion exactly, and it measurably does.
* **CT_PEAKER's 44–70 % is arithmetic, not attenuation.** That class alone is SET to the LDC-delivered
  index (`nyiso_downstate_ct_gas_daily`, armed), whose **level** is far higher (2023 p50 3.982 against
  the hub's 1.700). A CV divides by that larger mean. Its *absolute* swing is not smaller.
* **`_gas_series` reads EXACTLY 0.0000 in all four years.** Not "low" — flat. §4.

### 3.1 Why the lane prompt's percentiles looked smooth

The prompt's per-year figures (`2022 6.239/8.702/9.962/11.067/12.745/12.745`, and `max == p97` in
**all four years**) are `gas_<year>.npy` = `_gas_series`. `max == p97` is the signature of a 12-value
monthly step, where the dearest month covers ~8.3 % of hours. **Those numbers are real; they are just
not a property of any gas unit's delivered price.**

---

## 4. G-3 — THE CODE DEFECT, PROVEN MECHANICALLY RATHER THAN READ

`scripts/probes/nyiso248_series_invariant.py` → `_nyiso248_series_invariant.json`.
`_hub_overlay_series` (`data/fuel/hubs.py`) documents an explicit invariant:

> *"used by `_gas_series` so gas-keyed coal passthrough sigmoids see **the same delivered gas price
> the merit order sees**."*

It calls `iso_hub_monthly_gas_prices` and expands — **unconditionally**. `apply_hub_basis_overlay`,
the array path, branches on `gas_hub_basis_daily` into `iso_hub_daily_gas_prices`. The single-series
analogue **has no such branch**, so it silently ignores the daily gate the array path honours.

Both functions called on the keeper's own resolved config, same year:

| year | `iso_hub_daily_gas_prices` distinct / max | `_gas_series` distinct / max | max abs diff | **invariant** |
|---|---|---|---:|---|
| 2022 | 342 / $39.616 | 12 / $12.745 | **28.549** | **False** |
| 2023 | 315 / $43.965 | 12 / $5.095 | **38.869** | **False** |
| 2024 | 308 / $22.303 | 12 / $6.060 | **16.243** | **False** |
| 2025 | 330 / $84.967 | 12 / $14.095 | **70.872** | **False** |

**The daily object is built and available; `_gas_series` just never asks for it.**

**Blast radius, stated rather than asserted.** Live *solve-path* consumers of `_gas_series` are the
gas-keyed **COAL passthrough sigmoids** (`runner.py:3038`, `run_calibration.py:4798`) and
`data/fuel/zonal_anchor.py:124`. For **this** keeper the anchor path is **inert** — nyiso-247
disarmed `gas_offer_net_revenue_margin`. NYISO carries **1,487 MW of COAL, 5.97 % of thermal
capacity**, whose energy share is far smaller still.

**This is NOT proposed as a NYISO arm, and the reason is rule 25 `[R-ISO-SCOPE]`, not the residual.**
`_hub_overlay_series` is a **shared** path: repairing it moves MISO, NEISO and CAISO — their coal
sigmoids *and* their `gas_offer_net_revenue_margin` anchors, which are live in those ISOs. A NYISO
lane may not make that change (rule 25), and for NYISO alone it would be a near-null solve against a
coal fleet that barely runs. **Routed, not absorbed: it is a cross-ISO / owner-court item.** §7.

---

## 5. G-4 — THE OBJECT THAT REPLACES THE LANE'S: THE SUCCESSOR'S GAS COORDINATE IS A **MONTH SELECTOR**

`scripts/probes/nyiso248_conditioner_swap.py` → `_nyiso248_conditioner_swap.json`.

`derive_nyiso_offer_level_dispersion.state_windows` bins its gas coordinate on
`gas_series_by_year()` — **the 12-value monthly step**. With
`gb = searchsorted(quantile(gas, (0.80, 0.90, 0.97)), gas)`, the condition `gas_bin >= 2` therefore
selects *"an hour inside one of the year's ~1.2 dearest **months**"*. The reported
`tight_winter_share` of 98–100 % is then **near-tautological**: the dearest month of a NYISO year *is*
a winter month.

Everything below holds `state_windows`' registered construction fixed — same `NETLOAD_PCTS` ladder,
same within-year percentile basis, same net load, same `tight = gas_bin ≥ 2 AND load_bin ≥ 2` — and
swaps **only** the gas coordinate.

| year | coordinate | distinct | tight h | days | months | winter % | **Jaccard vs monthly** | kept |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **2022** | monthly step | 12 | 45 | 15 | 2 | 100.0 % | — | — |
| | hub daily | 342 | 138 | 17 | 4 | **21.0 %** | **0.1806** | 0.622 |
| | fleet daily | 351 | 138 | 17 | 4 | **21.0 %** | **0.1806** | 0.622 |
| 2023 | monthly step | 12 | 18 | 5 | 2 | 100.0 % | — | — |
| | hub / fleet daily | 315 / 329 | 22 | 7 | 3 | 100.0 % | 0.8182 | 1.000 |
| 2024 | monthly step | 12 | 68 | 16 | 2 | 100.0 % | — | — |
| | hub / fleet daily | 308 / 323 | 61 | 12 | 2 | 100.0 % | 0.8971 | 0.897 |
| **2025** | monthly step | 12 | 129 | 25 | 2 | 100.0 % | — | — |
| | hub daily | 330 | 108 | 18 | 3 | 100.0 % | **0.7050** | 0.760 |
| | fleet daily | 346 | 105 | 17 | 3 | 100.0 % | 0.6835 | 0.736 |

**What this does and does not establish:**

* **The two daily candidates agree almost exactly** (2022 identical to four decimals; 2025 within
  0.02 Jaccard). The result is therefore a property of *daily grain*, not of which daily series is
  chosen — which is what makes it a finding rather than a construction artifact.
* **2022 is decisive.** Jaccard **0.1806**: the daily conditioner keeps only 62 % of the monthly
  tight hours, triples the set (45 → 138 h), spreads it across **4 months instead of 2**, and drops
  the winter share to **21.0 %**. In 2022 the monthly step's p90 is simply *December*; the daily
  series finds dear gas days in three other months as well.
* **2023 and 2024 are near-stable** (0.82 / 0.90, 100 % / 90 % retained). The defect is **real but
  year-dependent, and it does not overturn those years.** Saying otherwise would overstate it.
* **A carried-forward DO-NOT-REDO claim is falsified.** This lane's own prompt carries, from
  nyiso-245/246: *"gas ≥ p90 hours are 98–100 % WINTER."* Under the correct daily coordinate that is
  **21.0 % in 2022**. The claim is true of a *monthly* gas rank and not of a daily one.

---

## 6. WHAT THIS DOES **NOT** DO — the nyiso-247 keeper is untouched, stated plainly

**The promotion does not rest on the affected gate.** nyiso-247 cleared G-A (the identity: median
armed-row `d(mc)/d(fuel)` 7.7475 → 9.5758, exactly the median markup, max slope error 0.0), G-C
(loading shape, 4 of 4 against nyiso-195's own killing margin), G-D (no C1/C2 status move) and G-F
(rule 19 by removal). **None of those four is gas-conditioned**; G-A in particular is an algebraic
identity over all 8760 hours.

**G-B, the sign guard, IS gas-conditioned** — its `Q_mod` divides `mc` by this `gas` array and its
tight/ordinary windows come from `state_windows`. So G-B's ranks are **month** ranks. What that
changes is **interpretation, not arithmetic**: the disarm's effect on the offer's fuel slope is exact
and conditioner-free, and the direction G-B reports (the armed term's implied heat rate falls as gas
rises; the book's rises) is a property of the term's algebra, not of the binning.

**What it does put in question is the SUCCESSOR's measured magnitudes** — nyiso-246's conditional
level-dispersion object (`G3a = 25.845` MMBtu/MWh; `Q_book +2.035 / +11.928 / +27.880` at p50/p75/p90).
Those were measured on the book conditioned on these windows. **Before a form is designed for that
object, it should be re-measured on the daily coordinate.** §7.

**Nothing was re-scored, re-registered or re-keyed.** NYISO's registry carries exactly one run, the
keeper; `frontend/data/backcast/keepers/NYISO.json` is untouched; no determination moved.

---

## 7. WHAT THE NEXT LANE SHOULD DO — routed, with the cost of each stated

1. **DO NOT re-propose the daily citygate for NYISO.** It is armed
   (`gas_hub_basis_overlay` + `gas_hub_basis_daily` → `_nyiso_hub_daily_gas_prices`), at 90–120 % of
   the measured source swing. **This is a DO-NOT-REDO from this session** (rule 28(a)); the matrix
   cell is stamped.
2. **RE-MEASURE THE SUCCESSOR'S OBJECT ON THE DAILY COORDINATE — this is the live blocker.** Both
   `Q_book` and `Q_mod` must move together, because the book side is conditioned on the same windows.
   **Cost: a re-fetch.** The P-27 genbids payload is a converted corpus — only
   `data/raw/nyiso-bid-data/genbids/SHA256SUMS.txt` is tracked, the 48 monthly archives (172 MB) are
   untracked and **not on disk**, so recovery is re-fetch from `mis.nyiso.com` (no auth), not a git
   restore. The reduced artifact `nyiso_offer_level_dispersion.json` carries pooled quantiles **only**
   and cannot be re-conditioned. **Still zero LP.**
3. **`_hub_overlay_series`' missing daily branch is a CROSS-ISO item, not a NYISO arm.** Rule 25
   forbids a NYISO lane from moving a shared path that re-prices MISO/NEISO/CAISO anchors and coal
   sigmoids; and NYISO's own exposure is a 1,487 MW coal fleet that barely runs. It needs an owner
   ruling and a cross-ISO census, exactly as the `gas_hub_basis_overlay` R cell records the
   cost-convention question being owner court.
4. **Two unrelated open objects are untouched and stay open**: D-4 reads `passed=False` in every year
   (`reliability_floor × ST_GAS`, `nyiso_gas_commitment_bridge × CC_REGULAR`) while C8 passes; and the
   **G2 HYDRO LOSS** (Upstate_West ≤ $0 price fabrication) still needs a new candidate after
   nyiso-238 killed all four at zero LP.

---

## 8. ONE INFRASTRUCTURE REPAIR MADE, AND WHY

`scripts/probes/nyiso242_tail_reachability.py` pinned `BUNDLE` to the literal
`nyiso241_ctcommitted_span`. Rule 35 `[R-PROMOTE]` (a) deletes the outgoing keeper's bundle dir **in
the promoting session**, so that probe — and `_nyiso245_fleet_cache.py`, which imports its
`fleet_state` — raised `FileNotFoundError` the moment nyiso-247 promoted. It now resolves
**keeper shard → registry sidecar → `bundle`**, so it follows the designation automatically and
survives the next promotion; `NYISO_KEEPER_BUNDLE` overrides for a deliberate non-keeper A/B.
This is why a hardcoded bundle id is a latent break in any probe that outlives one promotion.

## 9. ARTIFACTS

| path | gate | what |
|---|---|---|
| `scripts/probes/nyiso248_gas_grain_census.py` → `_nyiso248_gas_grain_census.json` | **G-1** | per-row grain census, per class, 4 years |
| `scripts/probes/nyiso248_shape_attenuation.py` → `_nyiso248_shape_attenuation.json` | **G-2** | level-free within-month dispersion, source → ISO series → delivered |
| `scripts/probes/nyiso248_series_invariant.py` → `_nyiso248_series_invariant.json` | **G-3** | both overlay paths called and diffed; NYISO blast radius |
| `scripts/probes/nyiso248_conditioner_swap.py` → `_nyiso248_conditioner_swap.json` | **G-4** | tight-window movement under a daily gas coordinate |
| `scripts/probes/nyiso242_tail_reachability.py` | — | keeper-bundle resolution repair (§8) |

**Shards launched: none. Bundles produced: none. Rule 31 `[R-RETAIN]` has nothing to protect in this
session, and no promotion question is owed** — the keeper is unchanged and no candidate was solved.
