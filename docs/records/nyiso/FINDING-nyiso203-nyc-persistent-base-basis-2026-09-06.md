# FINDING nyiso-203 — the NYC persistent-base limb's basis is **SOUND AS BUILT**: its window, its membership and its `pro_rata` operator are each measurably right, and the one real construction gap (a daily-mean statistic applied hourly, worth −0.0087) **provably cannot reach** the Astoria conviction that motivated the review

**Session:** nyiso-203 (`claude/nyiso-nyc-persistent-base-limb-4lrj23`), 2026-09-06.
**Keeper, unchanged: `2026-09-06-nyiso-202-startup-aware`** — CALIBRATED, grade 7/8, fails 0,
C3c the lone ledgered caveat.
**ZERO LP SPENT.** No solve, no screen, no span, no bundle, no registration, no keeper change.
Rule 29's phase 0 returned a negative and therefore no arm reached a solve, so no solve was
pre-registered — there was nothing to pre-register.
**Rule 22:** 2023–2025 only. No held-out year was touched in any way.
**Machine record:** `results/calibration/_nyiso203_nyc_base_phase0.json`.
**Reproduce:** `uv run python scripts/probes/_nyiso203_nyc_persistent_base_basis.py`.

**THERE ARE NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0**. C3c is the ledgered,
non-downgrading caveat (rubric v3.3/v3.6) and is **not an objective**. Nothing below was
selected because a residual moved, and no metrics file, price series or volume residual was
opened at any point in this session (rule 1 `[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`).

---

## 1. The result in one paragraph

nyiso-202 §8 handed forward one object: repeat nyiso-140's Long_Island basis analysis for the
NYC `ST_GAS` persistent-base limb, which — with the bridge floor removed at Astoria 8906 — is
that plant's sole remaining forcer and draws the keeper's 2023 D-4 conviction at 0.2271 TWh.
The analysis is done, from source data only, and it returns a **clean negative: the basis is
sound as built.** Three separate things could have been wrong and **each is measurably right**
— the all-hours **window** (§3), the **membership** (§4, confirming nyiso-201 §5 from an
independent angle), and the `pro_rata` **distribution operator** (§5, which also *refutes* the
`cheapest_first` alternative on the same data). Exactly **one** genuine construction gap
survives (§6): the coefficient is a **daily-mean** statistic applied **hourly**, so 0.1750
sits **5.0 % above** its basis-matched value of **0.1663**. It is reported at full magnitude
and **not taken** (§7), for three independent reasons, the decisive one being that it
**cannot reach the object**: the measured band between the two coefficients covers **0.13 %**
of Astoria 8906's hours, against the 5,400 hours its D-4 row binds in. The conviction is a
fact about **which hours an always-on floor selects**, not about its level, its membership or
its operator (§8) — and that is the correctly re-specified object this session hands forward.

## 2. Step 0 — the frozen coefficient reproduces from source

Every gap below is therefore a **basis** difference, not a pipeline difference. The
construction is `derive_nyiso_st_reliability_floor.py`'s `base_24h`: fleet gross ÷ fleet
available capacity, aggregated to a **daily mean over all 24 h**, p25 over cool days
(`tmax < 25 °C`), pooled over 2023–2025, on the guard-corrected outage extract.

| | value |
|---|---:|
| `base_24h` re-derived here | **0.17485** |
| frozen `floor_pct` in `reliability_floor_coeffs_NYISO.csv` | **0.17500** |
| absolute gap | 0.00015 |

**The object.** The one live `NYISO,NYC,ST_GAS,tmax,-50.0` row: `floor_pct` 0.175,
`distribution` `pro_rata`, `exclude_plant_codes` **empty**, `threshold_basis` *"persistent 24h
base: base_24h (when-available cool-day CF p25)"*. A −50 °C `tmax` threshold is never not met,
so the limb binds in all 8,760 h, and `pro_rata`
(`model/interchange/core.py::_apply_frac`) floors **every unit** at
`0.175 × pmax × availability[t]`. Three plants: Ravenswood 2500 (1,725 MW, HR 9.500),
Astoria 8906 (923 MW, HR 11.949), Arthur Kill 2490 (877 MW, HR 11.268).

## 3. The WINDOW is right — and unlike Long_Island it is right for **every** member

nyiso-140 §2's test, computed on NYC for the first time. Cool-day median when-available CF by
hour block:

| plant | MW | h00-05 | h06-13 | h14-21 | h22-23 | P(CF=0) | online |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ravenswood 2500 | 1,725 | 0.283 | 0.287 | 0.288 | 0.290 | 0.072 | 0.945 |
| Astoria 8906 | 923 | 0.323 | 0.326 | 0.326 | 0.325 | 0.390 | 0.704 |
| Arthur Kill 2490 | 877 | 0.111 | 0.119 | 0.184 | 0.112 | 0.247 | 0.811 |

Every plant is **positive in every block**, and for the two larger ones the profile is
essentially **flat around the clock** (block spread ≤ 0.007). That is what a persistent
24-hour baseline looks like in the meter. The all-hours window is correct and must not be
narrowed — narrowing it would be rule 1 `[R-STRUCT]` backwards.

Note the contrast that makes the Long_Island comparison informative: there, one member
(Port Jefferson) read a median of **exactly 0.000 in all 18 (year × block) cells**. On NYC the
**minimum** cell across all three plants is **0.111**.

## 4. The MEMBERSHIP is right — a second, independent confirmation of nyiso-201 §5

nyiso-201 closed the membership question negative on a zero-cell count (8906 is **0 of 18**,
pooled median 166 MW, online 66.7 %). §3 confirms it on a different statistic entirely — the
per-block cool-day median — and reaches the same place: **no NYC member is economically laid
up.** There is nothing for `reliability_floor_plant_exclusions` to exclude, which is why the
keeper's armed `reliability_floor_plant_exclusions=True` arms nothing at all on this limb.

**No per-plant list was typed, and none is warranted** (rule 1 `[R-STRUCT]`, rule 14
`[R-ACCURATE]`, and nyiso-144's 7314 ruling).

## 5. The `pro_rata` OPERATOR is right — and the same measurement REFUTES `cheapest_first`

This is the hypothesis the review existed to test, and it is the one that could most plausibly
have failed. The coefficient is identified on a **fleet aggregate** and applied **per unit**;
those two are only equivalent if the units' low hours coincide. They demonstrably do not, and
the arithmetic gap is large:

| | MW at full availability |
|---|---:|
| fleet-aggregate hourly p25 (as identified) — 0.1663 | **586.1** |
| sum of the three **per-unit** hourly p25s | **347.1** |

That is a 69 % over-statement, and it is Jensen's inequality on a percentile: the p25 of a sum
is not the sum of per-unit p25s. Taken alone it looks like an indictment of `pro_rata`.

**It is not, and the direct measurement says so.** Under `pro_rata` each unit's share of fleet
generation equals its share of fleet **available** capacity. Measured in the hours the limb
exists to represent — the fleet's own lowest-quartile when-available CF hours, the hours the
p25 is drawn from:

| plant | gen share | avail share | **g/a ratio** |
|---|---:|---:|---:|
| Ravenswood 2500 | 0.683 | 0.562 | **1.22** |
| Astoria 8906 | 0.125 | 0.100 | **1.25** |
| Arthur Kill 2490 | 0.192 | 0.338 | **0.57** |

**All three plants contribute, and roughly in proportion to available capacity.** The result is
robust across both the quantile and the day-type: over {cool days, all hours} × {q10, q25} the
ratios span **0.57–1.43** and no plant is anywhere near zero. The base is a *shared* baseline,
not a concentrated one.

**`cheapest_first` — the only alternative operator the engine offers — is refuted by the same
numbers.** The zonal target at 0.175 is **616.8 MW** of a 3,524.6 MW fleet, and the cheapest
plant (Ravenswood, HR 9.500) has 1,724.8 MW, so `cheapest_first` would place **100 % of the
target on Ravenswood alone** — at **0.358 of its own capacity**, *above* its own measured
median CF of 0.288 — while flooring Astoria and Arthur Kill at **zero**. The meters say
Ravenswood carries 68 %, not 100 %. Swapping the operator would replace a supported assertion
with a refuted one.

**So the fleet-aggregate identification and the `pro_rata` application are consistent after
all**, and the 586-vs-347 MW gap is the honest arithmetic of applying a percentile, not
evidence of a defect.

## 6. The ONE real gap: a daily-mean statistic applied hourly

The floor is applied hourly; the coefficient is identified on daily means. Basis-matching the
time aggregation and nothing else:

| basis (fleet-aggregate population, unchanged) | value |
|---|---:|
| **daily-mean** cool-day p25 — as identified, = frozen | **0.1748** |
| **hourly** cool-day p25 — as applied | **0.1663** |

**−0.0087 absolute, −5.0 % relative.** This is a real construction mismatch of exactly the
class nyiso-140 named. What differs from Long_Island is that there it was **−30 %** and was
**cancelled** by an offsetting membership error, leaving the coefficient unmoved at zero DOF.
Here it is six times smaller in relative terms and, membership being clean, **nothing cancels
it** — so correcting it would actually **move the coefficient**.

Sizing it, pooled 2023–2025 (`added` = Σ max(0, floor − metered gross), the energy the floor
compels above measured conduct):

| plant | added @ 0.1750 | added @ 0.1663 | Δ | **measured band %** |
|---|---:|---:|---:|---:|
| Ravenswood 2500 | 0.370 | 0.332 | −0.038 | 3.98 |
| Astoria 8906 | 0.214 | 0.203 | −0.011 | **0.13** |
| Arthur Kill 2490 | 0.926 | 0.842 | −0.085 | 0.53 |
| **FLEET** | **1.510** | **1.377** | **−0.133** | |

*"measured band %"* is the share of a plant's own hours whose metered CF falls in
[0.1663, 0.1750) — the **only** hours that can change binding state from the coefficient move,
so it bounds what the level can possibly reach.

For context the limb adds 1.510 TWh over three years on 19.210 TWh observed (7.9 %), of which
Arthur Kill carries 0.926 TWh (61.3 %) on 24.1 % of the fleet's output — non-trivial, but an
order of magnitude milder than Long_Island's Port Jefferson, which manufactured **2.26× its
own annual generation**. Arthur Kill's is **0.20×**.

## 7. Why the gap is REPORTED and NOT TAKEN

Three independent reasons, any one of which is sufficient:

1. **Rule 23 `[R-FROZEN-DERIVE]` has no trigger.** *"Measured-behaviour parameters re-derive
   only when their source data updates … Re-derivation commits must cite the data change."*
   **No source data has updated.** nyiso-140's re-derivation *did* cite one (the 6a8f285
   guard fix changed the outage extract); this one has nothing to cite.
2. **It would move the coefficient, which nyiso-140's did not.** That correction was accepted
   as **zero-DOF precisely because `floor_pct` was unchanged** (0.2666 vs 0.2620). A −5 %
   coefficient move with no source-data trigger is a different act, and whether the
   construction repair is itself an adequate identification under rule 21 `[R-DOF]` is an
   **owner call, not this lane's**.
3. **It cannot reach the object.** The review was opened by Astoria 8906's D-4 conviction —
   0.2271 TWh over **5,400 binding hours**. The coefficient move touches **0.13 %** of 8906's
   hours and **−0.011 TWh** of its forcing. Spending an LP on a lever that provably cannot
   move its target would be a screen with no subject.

And the standing one: NYISO reads **fails 0**. Taking an untriggered −5 % move on a live floor
in a model with no structural problem to solve is the shape rule 1 `[R-STRUCT]` exists to
refuse, whichever way the price happened to go — which is why this session never looked.

## 8. Handed forward — the object, correctly re-specified

**Astoria 8906's D-4 conviction is a fact about WHICH HOURS an always-on floor selects, and no
basis parameter reaches it.** The rider (`legitimacy_diagnostics.py`, `check: "unit-conduct"`)
scores a plant's conduct **conditional on the floor binding**, and the two readings of 8906
diverge completely:

| 8906, 2023 | value |
|---|---:|
| **unconditional** median CF (§3) / online share | 0.330 / 0.704 |
| **conditional on binding** — median MW over its 5,400 binding hours | **0.0** |
| conditional zero-share | **0.521** |

Both are true. The plant is a **cycler that is genuinely online two-thirds of the year**, and
the floor binds precisely in the third it is off — because the floor binds wherever the LP puts
the unit out of merit, and 8906 is the **most expensive** of the three (HR 11.949) in exactly
the hours it is really off. The selection is done by the **merit order**, not by the
coefficient. That is why §§3–6 all come back clean and the conviction survives all of them.

Consequences for a successor lane:

1. **Do not re-open window, membership or operator on this limb.** All three are now measured
   and clean; §§3–5 are the evidence a re-test would need to overcome.
2. **The level is not the instrument** (§7 reason 3). Any arm aimed at the 8906 conviction has
   to act on *which hours bind*, not on how much binds.
3. **The gap of §6 remains available as an owner-decided, fully-sized, zero-LP construction
   repair.** Everything needed to rule on it is in §6 and in the machine record; it needs a
   ruling, not another measurement.
4. **Watch C3b-2024** (0.185 against ≤ 0.20, the model's tightest margin) — unchanged by this
   session, which spent no LP and changed no solve-affecting input.
5. **Method (rule 25 `[R-ISO-SCOPE]` respected — method, not a verdict transfer):** a
   fleet-aggregate coefficient applied per unit is **not** by itself evidence of a defect. The
   percentile-of-a-sum gap (§5, 586 vs 347 MW) appears whenever unit low-hours are
   non-coincident, and it is diagnostic only when paired with the direct pro-rata test. Any
   ISO auditing an always-on `pro_rata` limb should run **both**.

## 9. G-DRIFT (rule 29(b)) — re-validated empirically at this HEAD

Re-ran `scripts/probes/nyiso198_rebuild_checks.py --year 2024`: the committed record
`results/calibration/_nyiso198_rebuild_checks_2024.json` regenerates **byte-identically**
(`git diff` clean after the re-run). The solve-path fleet build has not drifted since the
keeper's sha, so the keeper's committed bundle remains the valid control and its
`legitimacy_diagnostics.json` D-4 rows — the source of the 0.2271 TWh quoted throughout — are
quotable as-is. *(The record's own stored `VERDICT: STOP` is nyiso-198's frozen kill of the
refuted `cc_duct_peaking_row_scoped` arm, not a drift signal; its exact reproduction is the
drift signal.)* **No control solve was spent, and none was needed** — this session differenced
nothing against a solve.

## 10. Disposition

**KEEPER UNCHANGED: `2026-09-06-nyiso-202-startup-aware`.** No arm was built, no
`ScenarioConfig` field was added, no coefficient was edited, no solve-affecting file was
touched. Nothing is registered, because nothing was solved (rule 15 `[R-DASHBOARD]` registers
runs; there is no run). The NYISO mechanism-matrix shard is re-stamped in this session per
rule 26 `[R-MECH-MATRIX]` duty (b) — the `reliability_floor_plant_exclusions` cell stays **K**
and gains this NYC review as evidence, and its stale *"the adopted D-4 per-unit rider is NOT
yet implemented"* clause is corrected, the rider having since landed and being the very check
that convicts 8906.

**Reported and not ours to fix** — a main-side regression another lane owns. Confirmed
pre-existing by running the three files at this HEAD with this session's working tree holding
**only untracked new files** (the probe, its JSON record and this document), so no tracked
file this session could have affected is in play — **6 failed, 43 passed**:
`tests/scoring/test_collate_scenario_campaign_common_set.py::test_the_repair_holds_over_the_whole_committed_tree`
fails at `assertAlmostEqual(row["emissions_mt_delta"], STATUS_COMMON_SET_MT)` — **101.967
against an expected 18.83**, an 83.137 difference. It reads only
`results/scn-campaign-load-2026-09-06/`, `scripts/collate_scenario_campaign.py` and its own
file, and looks like the SCN-WS5A-LOAD lane landing CAISO as the sixth ISO without updating
`STATUS_COMMON_SET_MT`. Also pre-existing at HEAD:
`tests/unit/pipeline/test_forecast_xyear_warmstart_flag.py::TestFieldRegistration::test_default_cache_key_unmoved`
and four in `tests/scoring/test_ff_readiness_battery.py`
(`test_walk_inputs_trivial_single_year`, `test_resolve_report_no_hard_fail_full_horizon`,
`test_ercot_confirmed_horizon_is_reported_not_failed`,
`test_build_registration_scorecard_no_iso_gate_open`).

---

*(nyiso-203, 2026-09-06. Zero LP. A negative finding: the basis is sound as built, and the one
gap that is real is reported at full magnitude, sized, and left to the owner.)*
