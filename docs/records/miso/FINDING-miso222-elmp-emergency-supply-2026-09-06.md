# FINDING miso-222 — THE ELMP / EMERGENCY-SUPPLY ASK, MEASURED BEFORE IT IS BUILT: the emergency-range MW **is already measured and curated in this repo** (miso-219's premise was half wrong), and at **1.7–2.0 GW** against a **5.6–22.0 GW** requirement it would reach **2 of the 45 object hours**. Structurally right, quantitatively insufficient. **Owner ask filed; nothing built, zero LP minutes** (2026-09-06)

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the
single ledgered caveat. **No solve, no screen, no bundle, no dashboard registration** —
rule 15 `[R-DASHBOARD]` registers completed runs and this session produced none. Rule 22:
2023–2025 only. Rule 29 `[R-SCREEN]` step 0 only; no mechanism armed, no `ScenarioConfig`
field minted, no matrix row.

Instruments: `scripts/probes/_miso222_removal_sizing_phase0.py` →
`_miso222_removal_sizing.json`; `scripts/probes/_miso222_emergency_range_phase0.py` →
`_miso222_emergency_range.json`. Both zero-solve.

---

## 0. Verdict in one paragraph

The charter sent this session to file the ELMP / emergency-supply mapping to owner court
on the ground miso-219 §9 stated: that *"the emergency-range MW is **neither
already-measured nor already-registered** in this repo"*. **The registered half stands;
the measured half is wrong.** MISO publishes `Economic Max` and `Emergency Max` per
masked unit per operating hour in its Market Reports conduct corpus, and this repo
already fetches it, already curates it, and already carries it in the data contract as
`energy-offers` with the fields `emergency_max_mw` / `emergency_min_mw` /
`emergency_flag` — landed at **miso-145 (2026-08-09), before miso-219 filed**. So the ask
was never "may we acquire a new measurement"; it is "may we use one we already have,
given its limits". Having corrected the premise, this session did the thing that changes
what the owner is deciding: it **measured the object**. The declared emergency range at
the 45 object hours is **1,866 / 1,954 / 1,664 MW** (mean, 2023/24/25). The capacity that
must leave the model's stack for the price to reach $200 at those same hours is
**21,991 / 16,119 / 5,577 MW** (mean). The mechanism is **3.4× to 11.8× too small**, and
per-hour it would reach **2 of 45 object hours** — both on 2025-07-28, the model's own
annual maximum day, and **zero in 2023 and zero in 2024**. **The ask is filed anyway**,
because rule 1 `[R-STRUCT]`'s first half is explicit that a structurally-correct
mechanism is never judged by whether it moves the residual — but the owner is told the
magnitude **before** paying for the build, which is the whole point of doing this at
phase 0.

## 1. THE PREMISE CORRECTION — what already exists

| what the ask needs | status | where |
|---|---|---|
| MISO publishes emergency-range MW | **YES** | `Economic Max` / `Emergency Max`, per masked `Unit Code` × operating hour, Market Reports `*_rt_co` / `*_da_co`, ~90-day lag |
| this repo fetches it | **YES** | `scripts/data/fetch_miso_energy_offers.py` |
| this repo curates it | **YES** | `scripts/data/curate_miso_energy_offers.py` |
| it is in the data contract | **YES** | `data/dictionary/schema/energy-offers.schema.yaml` — `emergency_max_mw`, `emergency_min_mw`, `emergency_flag` |
| landed span | **JJA 2023 / 2024 / 2025**, both markets, 552 files | corpus README (miso-145, 2026-08-09) |
| a `ScenarioConfig` field exists | **NO** | this is the half of miso-219 §9 that stands |
| a matrix row exists | **NO** | ditto |

This session re-fetched Jun–Jul RT for all three years (**183 files, 137.7 MB, 183/183
OK**) to measure against; the payload is gitignored by design, so nothing of it is
committed.

## 2. THE MEASUREMENT — sizing the removal object (charter item 1)

Merit-order displacement at fixed demand: the MW that must become unavailable for the
marginal offer to land at a target level is the capacity lying between the committed
clearing price and that level. First-order — no re-dispatch, no re-commitment — and
deliberately conservative for the ask, because it assumes every removed MW is replaced
from strictly above rather than from imports, storage or a neighbouring zone.

**MW that must leave the stack, over each year's 15 object hours:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| to **$200** (mean) | **21,991** | **16,119** | **5,577** |
| to $200 (min / max) | 13,773 / 28,916 | 4,315 / 32,236 | **329** / 12,618 |
| to the **oil floor** (mean) | 19,336 | 13,969 | 3,170 |
| to the measured actual (mean) | 21,539 | 17,340 | 8,092 |

**The cohort that must leave, by class\|band** (mean MW over the object hours):

| class \| band | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `CT_PEAKER\|econ` | **12,060** | **8,684** | **2,210** |
| `COAL\|econ` | 2,275 | 1,308 | 175 |
| `CC_REGULAR\|peak` | 1,765 | 1,153 | 845 |
| `CT_PEAKER\|committed` | 1,545 | 1,081 | 318 |
| `CT_PEAKER\|peak` | 940 | 994 | 827 |
| `ST_GAS\|econ` | 719 | 1,032 | 178 |
| `\|?` (non-tranche) | 991 | 753 | 610 |
| **share on the authorized offer channel** | **95.1 %** | **95.1 %** | **88.9 %** |

**A structural note that constrains every removal mechanism, not just this one.** The
must-leave cohort is **66.1 / 66.8 / 60.1 % `CT_PEAKER`** (14,545 / 10,759 / 3,355 MW of
it). A capacity-removal mechanism aimed at the object's hours therefore lands on the same
class whose C1 cell has **0.015 TWh** of headroom (`CT_PEAKER`-2023, −7.985 against
±8.00). Removal is a *different act* from miso-221's re-pricing and its energy cost is far
smaller — it bites only in the hours it is scoped to, not all 8,760 — but the cell is the
binding constraint for this family too, and any arm must pre-register it. Even scoped as
narrowly as possible, 14.5 GW × the 15 object hours is **0.218 TWh, already 15× the
headroom**; scoped to 2023's 72 declared emergency-window hours it is **1.05 TWh, 70×
over**. **A removal mechanism scoped to declared windows is not automatically cheap on
C1** — that has to be measured per arm, and this session does not.

## 3. THE MEASUREMENT — sizing the emergency range itself

From MISO's own conduct corpus, `max(0, Emergency Max − Economic Max)` summed over units
flagged available, at the object's own hours. **Rule 13 `[R-MEASURED]`:** only OFFER
columns are read; the award columns (`Cleared MW1`–`MW12`, `Target MW Reduction`) are
dispatch OUTCOMES and are dropped before anything else touches the frame, the same
discipline `curate_miso_energy_offers.OUTCOME_COLS` enforces. Clock: published fixed EST
interval-beginning, model fixed CST interval-beginning, so CST = EST − 1 h, no DST on
either side. **All 45 object hours are covered** (61 RT files per year, 1,172 / 1,218 /
1,294 masked units).

| declared emergency range, MW | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| at the object hours — mean | **1,866** | **1,954** | **1,664** |
| at the object hours — min / max | 1,418 / 2,867 | 1,594 / 3,152 | 1,272 / 2,132 |
| all Jun–Jul hours — mean / p95 / max | 2,458 / 4,490 / 6,051 | 2,817 / 5,243 / 7,074 | 2,581 / 4,858 / 6,931 |

## 4. THE TWO NUMBERS AGAINST EACH OTHER — the answer

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| available (emergency range, mean) | 1,866 MW | 1,954 MW | 1,664 MW |
| required (MW to $200, mean) | 21,991 MW | 16,119 MW | 5,577 MW |
| **shortfall factor** | **11.8×** | **8.2×** | **3.4×** |

**Per hour, the decisive test — would the emergency range cover the MW that must leave?**

| year | object hours reached |
|---|---|
| 2023 | **0 / 15** |
| 2024 | **0 / 15** |
| 2025 | **2 / 15** — `07-28 HE18` (need 1,044, have 1,323) and `07-28 HE19` (need 329, have 1,272) |
| **total** | **2 / 45** |

Against the oil floor — a lower bar in some hours, because oil at ~$241 is the first
price at which the unreachable block sets price — it reaches **0 / 0 / 6 of 15**.

For scale: C3c is model **3 / 7 / 0** hours above $200 against actual **30 / 37 / 88**.
Re-basing the tier onto the measured emergency range would move 2025 from 0 to about 2.

**Why the "is it inside our pmax?" question does not change this answer.** The build's
real design question is whether the model's assembled capacity already contains the
emergency range — if it does, re-basing REMOVES 1.7–2.0 GW from the economic stack (and
adds a $500 block above oil); if it does not, re-basing only adds the block. This session
does not settle it: the corpus is masked, so a per-unit comparison against our EIA-860
net-summer basis is not constructible, and an aggregate comparison is confounded by
population (the corpus covers offer-submitting units; our stack also carries must-run
nuclear, hydro, imports and renewables at their hourly CF). **It does not need settling
to answer the owner's question**, because the numbers above already assume the *most*
favourable case — that the whole range leaves the economic stack — and that case is
measured insufficient in every year. The question is a build-design question, not a
go/no-go one, and it is named in the ask as such.

## 5. THE OWNER ASK, written to be ruled on

**What is asked.** Authorization to re-base `maxgen_emergency_tier_pricing` from **load
slack** onto a **declared-emergency-range MW cohort**, using the already-curated
`energy-offers` `emergency_max_mw` / `emergency_flag` fields as the measured input.

**Why it is structurally right (rule 1 `[R-STRUCT]`, first half).** The mechanism is
armed in the keeper, correctly clocked on the miso-210-repaired `Etc/GMT+6`, and in a
**declared** MISO capacity-emergency window in **11 of 2025's 15 object hours** — and it
contributes **exactly $0**, because it prices unserved energy and the LP serves every
MWh (model slack 0.000 MWh in all 45 object hours; miso-219 §5). MISO's actual ELMP
prices an *emergency-range MW block* at the Event Step floors, not a shortage. The
model's keying is a mis-mapping of a real mechanism, and fixing a mis-mapping is
structural work whose merit does not depend on the residual.

**What the owner must weigh, stated plainly and against interest.**

1. **It will not close C3c.** 2 of 45 object hours, 0 in 2023 and 2024 (§4). This is
   measured at the most favourable interpretation, not assumed.
2. **The input cannot be attributed to a model class or zone.** Unit identity is masked;
   MISO publishes **no fuel or technology attribute**, and the offer-side class bridge was
   built and **REFUTED at miso-138**. Location is `Region` ∈ {North, Central, South}, a
   MISO market region, **not** a model zone. So the mechanism can only be **fleet-aggregate
   or region-aggregate** — never per-unit, never per-model-zone. That is a genuine rule 14
   `[R-ACCURATE]` misalignment and the owner should rule on whether an aggregate cohort is
   admissible or whether the misalignment disqualifies it.
3. **Coverage is JJA only.** The corpus is a summer corpus (Jun 1 – Aug 31, 2023–2025).
   A mechanism keyed to it is undefined for eight months of the year unless the fetch is
   widened or the cohort is held constant outside JJA — a design choice that itself needs a
   ruling, because holding a summer statistic constant year-round is a different input than
   the measured one.
4. **It costs a `ScenarioConfig` field and a matrix row** (rule 28c), and it touches
   `CT_PEAKER`, whose 2023 C1 cell has 0.015 TWh of headroom (§2). A build must
   pre-register that cell as its first kill.
5. **The rule-13 `[R-MEASURED]` forward-regeneration test — it PASSES, and this is the
   strongest thing about it.** The admissibility question is *"could this same quantity be
   produced for a forward year from forward drivers, and would it respond to changed
   conditions?"* The emergency range is a **unit physical characteristic** (the overload
   band between economic and emergency capability), declared ex ante by the operator, not
   an outcome. For a forecast year it regenerates as a per-class or fleet-aggregate
   emergency-range fraction applied to the forecast fleet, and it responds to changed
   conditions because the fleet changes. It is not a measured *outcome* fed back to force a
   match: it is availability physics, the same admissibility class as an outage window.
   **The offer columns are conduct declarations recorded ex ante; the award columns are
   outcomes and are dropped at curation and unreadable downstream.**

**What is NOT asked, and must not be read in.** No requirement repair, no curve change,
no ORDC lever — the reserve/scarcity family is closed arithmetically (miso-219: zero
shortfall in all 26,280 hours; the requirement would have to be 10.62× / 6.40× / 3.26×
published to bind) and `ordc_scarcity_overlay` remains `G` on miso-163's structural
grounds, re-affirmed at miso-204 and miso-219 and untouched here. Nothing in this session
is evidence against any of that.

**The recommendation.** Rule on (2) and (3) — the attribution and coverage
misalignments — **before** authorizing a build, because they are what make this a
judgment call rather than a data task. If the aggregate cohort is admissible, the build is
justified on structural-fidelity grounds and should be undertaken **with the C3c
expectation set at 2 of 45 hours, in writing, in its PREREG**, so that it is not later
read as a tail fix and so that its (predictable) failure to move C3c is not mistaken for a
defect. If the misalignment is disqualifying, the mechanism is closed and C3c's remaining
routes reduce to the supply-depth question in §6.

## 6. WHAT THE SIZING SAYS ABOUT C3c GENERALLY — the successor object

The requirement is **5.6–22.0 GW of supply depth** at the object's hours. Nothing in the
current lever set is of that magnitude:

| candidate | magnitude at the object hours | verdict |
|---|---|---|
| offer-curve reshape (miso-221) | reaches the right block, costs 450–516× the `CT_PEAKER`-2023 C1 headroom | **closed by measurement** |
| reserve requirement / ORDC (miso-219) | needs 3.26–10.62× the published requirement | **closed; `G` on structural grounds** |
| ELMP emergency range (**this session**) | **1.7–2.0 GW against 5.6–22.0 GW** | **3.4–11.8× short; 2/45 hours** |

**So the object is a supply-depth or demand-level question, and it is 2023/2024 that is
extreme, not 2025.** 2023 needs 22.0 GW and 2024 16.1 GW, against 2025's 5.6 GW — the
reverse of where the lane's attention has been. The model's 2023 object-hour prices are
**$34–$46** against actuals of **$122–$355**, with 13.8–28.9 GW of near-flat supply in
between, half of it a single `CT_PEAKER|econ` block. Two heads follow, and **neither is
proposed here**:

1. **Is the model's object-hour supply too deep, or its object-hour demand too shallow?**
   These are the same first-order arithmetic and the sizing cannot distinguish them. F-6
   (the model tracks the real fleet's utilisation to 0.4 pp) constrains the availability
   half; miso-205 measured the object hours as genuinely high-load in the model (load
   p83.4–p99.3). A session that separates the two would be the first to name the object
   rather than a lever.
2. **The South PRICE separation** (miso-213 O-4 / miso-211 D-3, +$0.16 model vs +$58
   measured) — untouched, independent, and sharpened rather than answered by miso-219's
   measurement of MISO-wide congestion as inert in the object's hours ($0.06 mean
   dispersion in 2025).

## 7. G-DRIFT — the delta since miso-221's audit (rule 29(b) form 4)

miso-221 pre-cleared `4545300d..b2bd9fdb`. The delta `b2bd9fdb..3dcf1b22` over the solve
path is **5 files, +286 / −12** — and `origin/main` has since moved to `5fdd4374` with
**zero further solve-path changes**, so this audit is current against main as well:

| file | Δ | class | reason |
|---|---:|---|---|
| `src/market_sim/data/egrid_sheets.py` | +151 | **INERT** | new module: a content-addressed parquet mirror serving the eGRID sheets without openpyxl on the solve path (wall-clock item A-2). Same frames; pinned by `tests/test_egrid_sheets.py` |
| `src/market_sim/data/fleet/eia860.py` | +12/−8 | **INERT** | `pd.read_excel` → `read_egrid_sheet`, same sheets, same columns |
| `src/market_sim/data/zone_assignment.py` | +9/−4 | **INERT** | ditto |
| `scripts/lib/holdout_policy.py` | +73 | **INERT for a solve** | adds `registration_refusals`, the REGISTRATION-time half of the rule-22 spend gate (owner ruling R-AZ). Not on the solve path; binds only when a run is registered, and this session registers none |
| `src/market_sim/results/cache.py` | +41 | **INERT** | cache-key epoch documentation; backcast calibration bundles are not keyed |

**Measured, not merely classified.** This session rebuilt the keeper's fleet and offer
basis at `3dcf1b22` and compared it against miso-221's rebuild at `b2bd9fdb` over **45
object hours × {committed clearing price, MW between price and $200}**: **0 differences.**
The eGRID refactor is empirically inert on the MISO fleet. **`miso220_nonsteamlift_B`
remains a valid form-4 control; no control solve is owed.**

## 8. Matrix bookkeeping (rule 28b)

**No cell verdict moved.** `maxgen_emergency_tier_pricing` stays **`K`** — it is armed in
the keeper and nothing here refutes it; what this session did is **size its object** and
**locate its input**. Evidence appended to the MISO shard, the miso-215 / miso-221
"evidence about the container, no verdict" form. No `ScenarioConfig` field was added, so
no base row was minted and no other ISO's shard was touched (rule 28c not engaged, rule 25
`[R-ISO-SCOPE]` intact).

## 9. Reproduction

```
python3 scripts/data/fetch_miso_energy_offers.py --years 2023 2024 2025 --months 6 7 --markets rt
python3 scripts/probes/_miso222_removal_sizing_phase0.py       # ~2 min/year
python3 scripts/probes/_miso222_emergency_range_phase0.py      # ~1 min, all years
```
Zero LP minutes. The fetch is 183 files / 137.7 MB into a gitignored raw mirror.
