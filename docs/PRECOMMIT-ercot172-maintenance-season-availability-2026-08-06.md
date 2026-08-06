# PRECOMMIT — ercot-172: the 2024 maintenance-season availability defect, attributed at MW grain

**Session ercot-172, 2026-08-06. Charter: mechanism-testing-matrix §5.1, the H4
item-4 object (`FINDING-ercot166-2023-diagnosis-triage-2026-08-05.md` §5 + §7 H4),
and the standing GATE on the ercot-167 SOC-reserve re-gate
(`FINDING-ercot167-storage-soc-reserve-ab-2026-08-05.md` §3 reopen condition).
PHASE 0 — NO LP, no solve, keeper UNCHANGED (`2026-08-05-run168b-year-curves`),
no `ScenarioConfig` field written.** This document is committed and pushed
**before** any capture, derive or probe is run. Every threshold, band, coverage
bar and verdict branch below is fixed here and **may not be moved after
measurement, in either direction**.

## 0. The object — enumerated BEFORE this document was written

Read from the keeper's own committed hourly sidecars
(`results/calibration/ercot168_yearcurves_B/hourly/`) and from raw ERCOT
settlement data. This is object *identification* — which hours, on which
calendar days, at what magnitude — not the measured attribution the decision
rule below governs. It is stated here so the object cannot drift.

**The 2024 defect is exactly two hours, and they are the only two shed hours in
the year:**

| model hour-of-year | timestamp (CST, model clock) | shed (slack) MW | model $/MWh | actual RT $/MWh |
|---|---|---|---|---|
| 2827 | 2024-04-28 19:00 | **565.1** | 5,015.9 | 1,259.83 |
| 3067 | 2024-05-08 19:00 | **550.3** | 5,000.0 | 3,048.98 |

Shed-hour census on the keeper: **2023 → 4** (Jun 20, Aug 17, Aug 25, Aug 30 —
the item-11 "phantom shed hours", scarcity season), **2024 → 2** (above),
**2025 → 0**. Day-mean model-minus-actual system price: **+375.0** (Apr 28,
model 500.9 vs actual 126.0) and **+227.3** (May 8, model 573.6 vs actual
346.3); year MAE 13.04 on a year mean of model 29.96 vs actual 26.82. Scarcity
hours (`reserve_price > 0`) are Apr 28 h16–22 and May 8 h15–20.

**CALENDAR CORRECTION, recorded here because every instrument lookup depends on
it.** `FINDING-ercot166` §5 and the `ercot_dam_availability_gas_event_cap`
matrix note both label these days **"Apr 27" and "May 7"**. The true calendar
dates are **2024-04-28** and **2024-05-08**. Verified against the primary source
(`data/raw/lmp-data/RTMLZHBSPP_2024.zip`, `HB_HUBAVG`): April's highest day is
2024-04-28 at a **$126.86** day-mean / **$1,259.83** peak hour and May's is
2024-05-08 at **$345.99** / **$3,048.98** — matching both the keeper's actual
series and the price magnitudes the ercot-149 matrix note itself quotes
($1,260 / $3,049). The one-day-early labels are a **naive-leap-index artifact**:
an 8760-long index built on a 2024 calendar *without* dropping Feb 29 relabels
every hour after Feb 28 one day early. The hours and prices in those records are
correct; only the printed date labels are off by one, systematically, in the
2024 diagnostics. Peak prevailing **HE21** = **19:00–20:00 CST** = model hour
`h19`, so the model's error hour and ERCOT's event hour are the same hour.

**Both days are REAL ERCOT tight evenings that the model over-amplifies into a
shortage.** ERCOT did not shed load on either date. The model does — 565 MW and
550 MW at VOLL. The object is therefore a *capacity-shortage* defect, not an
offer-curve level defect, and rule 14 `[R-ACCURATE]` governs it.

**Why this session exists.** The object is the named root cause of the only
failing 2024 leg (C3b-2024 0.206, a +0.006 band cross) and the cited **reopen
condition** for the ercot-167 SOC-reserve re-gate. It is also the object the
ERCOT-149 promotion recorded against itself: its one tripped guard (C3c
spurious-2024 3→7) named these same evenings.

## 1. Instruments — imported verbatim, never re-implemented

* **`scripts/probes/ercot148_availability_capture.py`** (ERCOT-148) — the no-LP
  fleet-availability capture at the seam, wrapping
  `generators_to_fleet_arrays` and aborting before the solve. Used **unmodified,
  as a subprocess**, twice for 2024: capture **A** = the keeper config verbatim;
  capture **B** = the same config with **only**
  `ercot_dam_availability_coal_event_cap=false` and
  `ercot_dam_availability_gas_event_cap=false` overridden through its existing
  `--set` channel. No other flag is touched. Re-implementing the capture would
  make this session's MW incomparable to the ERCOT-148/149 record it must bridge.
* **`market_sim.data.outages`** — `ercot_thermal_dam_availability_hourly_series`
  (class-hour COP fraction), `ercot_thermal_dam_availability_plant_series`
  (plant-hour COP fraction over `accepted=1` crosswalk rows),
  `unit_outage_derate_factors` / `partial_outage_derate_factors` (the armed
  event-window family). Imported, never re-derived.
* **`data/raw/ercot-thermal-dam-availability-site-hourly.parquet`** — the
  60-Day DAM COP site×HE `live_mw` / `rating_mw` intermediate, for the MW-grain
  (not fraction-grain) reading and the rating-basis term.
* **CAMPD hourly unit data** (`data/raw/campd-unit-level/`) and the window
  extract `data/raw/campd-unit-outages.csv` — the physical operating record and
  the ≥5-day window family, read through the existing loaders.
* **Model side** — the keeper bundle `results/calibration/ercot168_yearcurves_B`;
  dispatch and prices from its committed `hourly/` sidecars (P1). **No LP.**
* **Clock**: everything is joined on the model's fixed non-leap CST clock
  (`outages._hour_of_year`), which is what both DAM series already return. Rule
  22 `[R-HOLDOUT]`: **2024 only for the object; 2023 and 2025 read only as
  neutrality controls.** No year outside 2023–2025 is read, solved or scored.

## 2. The attribution identity — exact, and fixed HERE

Scope set **S = {COAL, CC_REGULAR, ST_GAS, CT_PEAKER}** — exactly the classes
the event cap covers (`fleet/arrays.py` `_evcap_scope`). At a shed hour `h`:

```
A_pin(h)   = Σ_{g∈S} pmax_g · avail_g^B(h)     capture B — every overlay EXCEPT the event cap
A_final(h) = Σ_{g∈S} pmax_g · avail_g^A(h)     capture A — the keeper, event cap applied
E(h)       = A_pin(h) − A_final(h)             capability the EVENT CAP removed, exactly
```

The event cap is a pure `np.minimum`, so the identity is exact by construction
and **`E(h) ≥ 0` elementwise**. Two construction gates, both stop-the-session:

* **G-EXACT** — any `g ∈ S` with `avail^A > avail^B + 1e-9` at either hour is a
  construction error. Reported, not patched; the session stops.
* **G-SEAM** — every `g ∉ S` must satisfy `avail^A == avail^B` **exactly** over
  all 8760 hours. If the toggle moves a class outside the cap's scope it is not
  isolating the cap, and the session stops.

The second, independent term — the model's class nameplate against ERCOT's
registered rating, which the *fraction*-grain pin cannot see:

```
A_cop(h) = Σ_{sites ∈ class} live_mw(date, HE)        ERCOT-declared available MW
R(h)     = A_cop(h) − A_pin(h)                        RATING-BASIS gap (signed)
```

`R` is measured and reported at MW grain but is **not** this lane's object; a
material `R` re-points to the fleet-scope/crosswalk lane (item 11), it does not
license a mechanism here.

**Per-plant split**, aggregated over each plant's LP tranches:

```
E_p(h) = Σ_{g ∈ plant p, g∈S} pmax_g · (avail_g^B(h) − avail_g^A(h))
```

`E_named ≡ Σ_p E_p over plants with E_p(h) ≥ 25 MW`, each listed in the FINDING
by name, EIA plant code, class, MW and share. Everything below 25 MW is the
residual and is reported as one line.

### 2a. G-FOOT — the footing gate, run BEFORE anything else

The site-hourly parquet aggregated to class×HE must reproduce
`ercot-thermal-dam-availability-hourly.csv`'s fractions for 2024 to
**≤ 1e-3 absolute** on ≥ 99 % of covered class-hours. If it does not, the two
files are not the same instrument, the MW-grain reading is unlicensed, and the
verdict is **FILED-UNLICENSED** with the discrepancy reported. (The ercot-171 §1
discipline: establish that the pipeline reproduces the committed construction
before attributing any movement to the object.)

## 3. Licensing and the NEUTRALITY gate

### 3a. Coverage licence — fixed here, not lowered in either direction

* **L1 — COP resolvability ≥ 0.90.** The share of `E(h)` belonging to plants for
  which the accepted DAM crosswalk resolves a COP declaration
  (`ercot_thermal_dam_availability_plant_series` has a finite fraction at `h`)
  must be **≥ 0.90 at both shed hours**. Below it, the question "was the removed
  capability really available?" cannot be answered on committed data for the
  bulk of the object ⇒ **FILED-UNLICENSED**. This is the ercot-170 L1 bar and
  the ercot-169 §1b symmetry applies: a biased instrument manufactures a false
  confirmation as easily as a false refutation, so the bar is not lowered
  *against* the hypothesis either.
* **L2 — ambiguity budget ≤ 0.10.** `E` carried by LP rows whose `plant_code`
  does not resolve to a physical plant must be ≤ 10 % of `E`.

### 3b. Certificates — REPORTED per plant, both directions, never selected on

For every plant in `E_named`, both are measured and both are reported whatever
they say:

* **K-COP** — the plant's COP fraction at the shed hour is > 0 (the QSE filed
  live HSL, i.e. declared it available).
* **K-CEMS** — the plant's CAMPD hourly gross load exceeds 2 % of its capacity
  in at least one hour within **±7 days** of the shed hour (it demonstrably
  operated the same fortnight, so the dead stop bounding the shed hour is not a
  weeks-long mechanical stop).

A plant with **K-COP true and K-CEMS true** is capability the overlays removed
that both measured instruments say was there. A plant with **both false** is
capability the model correctly holds out. Mixed plants are reported as mixed and
are **not** silently assigned to either side.

### 3c. G-NEUT — the neutrality gate on any population restriction

This is the ercot-171 §3 gate, transplanted, and it is the load-bearing one.
**If — and only if — branch 3 is reached and a restriction of the event-window
population is proposed**, that restriction is admissible only if it fixes
*coverage/classification* and not *level*:

* **(a) It is a RULE, applied identically to every year and every class in S.**
  Never a named-plant exclusion list, never a month or season scope, never a
  2024 scope, never a scope keyed to the two days.
* **(b) The ERCOT-148-certified coal dead stops SURVIVE it.** Coleto Creek's
  mothball block, Limestone LIM1's 21.6-day Feb-2023 dead stop and W A Parish 5's
  74-day dead stop must each retain **≥ 0.95** of their windowed hours under the
  rule. These are the blocks ERCOT-148 exists to enforce; a rule that dissolves
  them is repealing the coal precedence, not reclassifying a gas misfiling.
* **(c) Level-neutrality on the licensed years.** Under the rule, the 2023
  shed-hour count must stay at 4 (it may not fall), and the ERCOT-148/149
  committed above-ceiling dispatch (coal 4.36/4.98/5.01 TWh, gas 4.27/5.93/4.14
  TWh) may not fall by more than **0.5 TWh** in any year.

Failing (a), (b) or (c) ⇒ the restriction is a level-selecting filter, exactly
as ercot-171's S1 was on limb C ⇒ the branch **collapses to FILED-NULL**, no arm
is named, and none may be built on this record (rule 13 `[R-MEASURED]`).

## 4. The decision rule — PRE-REGISTERED, branches evaluated in order, first to fire is the verdict

1. **FILED-UNLICENSED** — G-FOOT fails, **or** L1 < 0.90, **or** L2 > 0.10.
   Magnitudes MAY be surfaced (they are the session's substantive content) but
   they are **not verdicts and not a licence to arm anything**. Name exactly what
   data would unblock it. File and stop.
2. **FILED-REDIRECTED** — licensed, but **either** `E(h) < shed(h)` at either
   shed hour (the removed capability cannot cover the shed, so the shortage is
   not principally an event-cap object) **or** **P-ERR < 0.60**, where P-ERR is
   the share of the two days' summed `|model − actual|` price error sitting in
   hours with `E(h) > 0`. Report which term owns the object — the rating-basis
   `R`, renewables, storage, demand or the reserve requirement — re-point item
   4, and stop.
3. **ACTIONABLE** — licensed, `E_named(h) ≥ shed(h)` at **both** hours, and
   `E_named / E ≥ 0.60`, with every contributing plant named at MW grain and
   both certificates reported. The object is then a rule-14 `[R-ACCURATE]`
   precedence defect on the **existing** `ercot_dam_availability_*_event_cap`
   channel. This session **specifies** the correction and its kill gates (§5); it
   does **not** build or arm it without an explicit owner adjudication taken
   in-session.
4. **FILED-NULL** — otherwise (licensed, `E` covers the shed, but
   `E_named / E < 0.60`). Real and not per-unit attributable on committed data.
   File and stop, naming the blocking data. Per the ercot-170 precedent a null
   result is a complete session.

**The bars, and why they are these numbers, stated before measuring.**
`E_named(h) ≥ shed(h)` is not a tunable: the shed MW is the exact quantity that
must be restored for the VOLL price to collapse, so anything less cannot close
the object. The two **0.60** bars are a majority plus margin, so that the *named*
units and the *scarcity hours* — not the residual and not a broad day-long
over-tightness — carry the object; below that, any mechanism premise would again
rest on an unattributed aggregate, which is what ERCOT-163 §3 forbids. **P-ERR
is the chartered actionability fraction** and it can genuinely fail: if the two
days' error is spread across hours where no capability was removed, the event cap
is not the object however large `E` is.

## 5. If a mechanism follows — kill gates, fixed HERE

Reached **only** under branch 3 **and** only on an explicit in-session owner
adjudication. Any A/B is full-span `--year 2023 2024 2025` in **one** bundle
(rules 15/16) and **every** run is registered whatever the outcome, keeper or
rejected.

* **G-BIT — CONDITIONAL, with the condition fixed now.** If the correction is
  2024-scoped, G-BIT is live: all 2023 **and** 2025 hourly sidecars
  (`class_hourly`, `system`, `reserve_family`) must be sha256-byte-identical
  A→B. **But** §3c(a) forbids a year-scoped rule, so a G-NEUT-admissible
  correction will touch all three years and G-BIT is then **declared N/A with
  that reason recorded pre-solve** and replaced by **G-SPAN**. The two are
  mutually exclusive; whichever applies is stated before the solve, never after.
* **G-SPAN** (the G-BIT replacement) — in 2023 and 2025: no class's annual energy
  moves more than **0.5 %**, the shed-hour count does not increase, and the three
  ledgered C3c tail counts (2023 61/181, 2025 3/31) do not degrade.
* **G-SHED** — the 2024 shed-hour count must **fall**, and no year's shed count
  may rise.
* **G-SPUR** — the C3c spurious mid-band tail-hour count must not increase in any
  year. (This is the guard ERCOT-149 tripped on these very evenings; a correction
  that fixes the shed by re-manufacturing spurious hours elsewhere fails.)
* **G-C3c** — the three ledgered tail counts (61/181, 25/53, 3/31) must not
  degrade.
* **G-COAL148** — the ERCOT-148 coal adjudication must survive: coal dispatch
  above the measured-window ceiling may not rise more than **0.5 TWh** in any
  year. Rule 19 `[R-ONE-MECH]`: the incumbent precedence is reconciled, never
  repealed as a side effect.
* **G-DOF** — **zero** new fitted scalars. Every number is a measured MW, a
  measured duration, or an accepted crosswalk row (rule 20 `[R-DOF]`). A residual
  that can only be closed by a tuned value is an open root-cause issue, not a
  parameter.
* **G-D2** — no class's forced share may cross its rule-20 `[R-FORCED-BUDGET]`
  cap as a result of the arm.
* **Rule 22 LOYO** — leave-one-year-out within 2023–2025 before any promotion.

Failing any live gate ⇒ **REJECTED-AS-ARMED**, reported as such. The gates are
not renegotiated after the solve.

## 6. Scope fences and DO-NOT-REDO honoured

Standing, all carried unchanged and none re-opened: the "~8 GW cheap CC offline
block" **DOES NOT EXIST** (ercot-163); the CC headroom per-unit crosswalk is
**FILED-UNLICENSED** (ercot-170 — not re-attempted here, and item 11's
data-intake blocker is not this session's object);
`COAL_OFFER_MARGIN_LEVEL`'s 2023 application is **RETIRED BY VERIFICATION**
(ercot-171 limb A); `COAL_PEAK_OFFER_LEVEL`'s 2023 application is
**NOT-IDENTIFIABLE-2023 CONFIRMED** and a resource-scoped restriction is
**REFUTED** for that limb (ercot-171 limb C); `energy_online_capability_cap` `R`
(ercot-159); `ercot_storage_rt_offer_surface` `R` (ercot-162); per-year CT
re-identification **REFUSED** (ERCOT-147); lignite offer SLOPE (ERCOT-143 as
adjudicated); `coal_min_load_floor` both grains; lignite daily unit commitment;
coal seasonal LEVEL split; `coal_offer_level_rebasis` `R`;
`tranche_startup_amortization` `G`; ercot-168 **OPTION B** stays DEFERRED; the
West/Panhandle topology split is **CLOSED**
(`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10).

**Additional hard fences for this lane.** Whatever the verdict, this session will
NOT propose: a per-hour telemetered-HSL or COP cap on dispatch (rule 13
`[R-MEASURED]`-forbidden — it pins the model to a measured outcome); an aggregate
capability cap; a re-pricing of any class; a scarcity/ORDC parameter change; a
demand or reserve-requirement adjustment tuned to these two hours. The **only**
admissible channel is the precedence rule inside the existing
`ercot_dam_availability_*_event_cap` block.

**Item 11's extreme-hour face** (the 2023 phantom shed hours and the 1.7–3.1 GW
gas shortness at the top-10 actual hours) stays chartered under item 11 and is
**out of scope**; 2023's four shed hours are read here only as a §3c(c)
neutrality control.

**Carried forward, surfaced NOT decided** (no owner direction is assumed):
(1) the ercot-167 SOC-reserve re-gate is conditional on this defect — if a fix
lands, the re-gate of the **identical** arm is the named successor, full-span
A/B, both runs registered, never a single-year keeper; (2) ercot-171's named
limb-C successor, an instrument for `COAL_PEAK_OFFER_LEVEL` that does **not**
select on the tail, is unchartered and needs its own owner adjudication;
(3) ercot-165's daytime curtailment mode needs an owner decision on a per-family
weight (a DOF the ercot-164 charter fences).

## 7. Governance

Rule 25 `[R-ISO-SCOPE]`: ERCOT-scoped throughout; no other ISO's cell or artifact
is read or written. Rule 15 `[R-DASHBOARD]`: no solve ⇒ no bundle ⇒ no dashboard
registration; if any solve is run, every run is registered across all three
training years in one bundle (rule 16 `[R-ALLYEARS]`). Rule 22 `[R-HOLDOUT]`:
2023–2025 only; ERCOT holds no `complete` marker, so 2022 and every locked-test
year stay quarantined and are not read. Rule 23 `[R-FROZEN-DERIVE]`: no derive is
re-run and no measured-behaviour constant is re-identified — this session reads
the frozen extracts as they stand. Rule 28(b)/(c) `[R-MECH-MATRIX]`: matrix §5.1
is stamped in this session, and any mechanism cell this session tests is
re-cited, rejections included. Rule 27 `[R-PUSH]`: every push touching a
≥300-line file is blob-verified.

**Next shorthand: ercot-173.**
