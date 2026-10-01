# FINDING — caiso-141: the A2 water-state intake is **WALLED** — no public source anywhere separates CAISO pumped-storage from conventional hydro at hourly grain for 2023–2025. Helms (1,053 MW, 50.7 % of the fleet) and Eastwood (199.8 MW) have **no public hourly telemetry at all**; every hourly hydro series CAISO or EIA publishes is the same single PS-NET EMS feed. NO INTAKE, NO MECHANISM, NO SOLVE — filed per the charter's stop-if-walled discipline (2026-07-30)

**Keeper `2026-07-29-caiso139-dump-guard-offer` UNCHANGED** (NOT-YET, fail
{C3a-2025, C3c}). Nothing armed, no `ScenarioConfig` field, no LP built, no
curated partition written, `data/raw/` untouched. This is the charter's own
branch executing: the session was ordered to survey first and **STOP — file
the wall — and do NOT fabricate a shape** if no public source resolves the
split. None does. The joint A1+A2 D-gates (task step 3) were conditioned on
the split being measured and were therefore **not run**; the owner's rule-13
grant question on the A1 forcing family was **not posed**, because the joint
construction it was conditioned on cannot be built.

Instrument (committed, network probe — the one exception to the
committed-bytes probe norm, so the wall is re-checkable the day a source
appears):

* `scripts/probes/_caiso141_water_source_survey.py` — re-runs every
  verification below against the live public endpoints and prints
  `unchanged (WALL)` / `CHANGED` per check.

---

## §A — the survey: six source families, each checked to a verdict on live bytes

The target instrument (charter): an **hourly** CAISO pumped-storage net
series and/or an hourly conventional-hydro series, 2023–2025, separating the
two halves of the EIA-930 `WAT` cell — enough to adjudicate whether real PS
pumps ~700 MW through the Sep–Dec belly the way the model's unrestrained
2,078 MW fleet does (FINDING-caiso140 §B, the +793 MW wedge).

| # | source | checked (2026-07-30) | verdict |
|---|---|---|---|
| S1 | **EIA-930 `PS` fuel category** (API v2 `fuel-type-data`) | facet list carries `PS` ("Pumped storage") and `BAT`, but the CISO respondent returns **0 rows** for `PS` — CISO reports only the legacy 8 categories (batteries folded into `OTH`, which prints strongly negative) | **dead** — the category exists, CISO does not file it |
| S2 | **CAISO Today's Outlook fuel mix** (`/outlook/history/<date>/fuelsource.csv`, the Daily Renewables Watch successor; 5-min `Large Hydro` + `Small hydro`) | hydro prints **negative** in deep-surplus belly hours (−414 MW on 2025-10-15, hours 11:00–15:00 PT) — impossible for gross conventional generation — and matches EIA-930 `WAT` at corr 0.95 / mean \|diff\| 287 MW once WAT's hour-ending stamp is aligned | **dead** — the SAME net-of-pumping EMS feed as `WAT`, not a split |
| S3 | **CAISO Today's Outlook storage page** (`storage.csv`) | columns: `Total batteries, Stand-alone batteries, Hybrid batteries` | **dead** — battery-only (matches the LESR adjudication in FINDING-caiso140 §D) |
| S4 | **CDEC hourly telemetry** at the six PS plants' reservoirs (station ids from `cdec.water.ca.gov/misc/resinfo.html`) | **Courtright CTG, Wishon WSN (Helms) and Shaver SHV (Eastwood) carry ZERO hourly sensors** — PG&E and SCE do not report hourly to CDEC. Only DWR facilities report: San Luis SNL hourly storage (sensor 15) exists but was **out 2022-07-28 → 2024-01-19** (hourly elevation since 2003 is the fallback); Oroville ORO and Thermalito TAB are fully instrumented | **dead for the fleet** — the instrumentable share is the DWR 39.7 %; see §B |
| S5 | **EIA-930 sub-BA route** (`region-sub-ba-data`) | schema: one data column (`Demand`), facets `parent`/`subba` only | **dead** — demand-only by design, no fuel dimension |
| S6 | **CAISO OASIS** | `ENE_SLRS` carries system totals only (`TOT_GEN/LOAD/IMP/EXP_MW`, no pumping item); no OASIS queryname publishes actual generation by fuel (that is Today's Outlook = S2); public bid data (`data/raw/caiso-public-bids`) is masked bid-side with **no fuel/type identity** and is bids, not dispatch | **dead** |

Also ruled out, by publication design rather than live check: the retired
**Daily Renewables Watch** (`content.caiso.com/green/renewrpt/` — 404 from
2024-01 onward at time of check; its hourly `HYDRO` column was this same EMS
feed, and coverage ends before 2024-06 regardless); **DWR SWP operations
reports** and **USBR CVO San Luis reports** (daily grain — cannot place
energy within the day, which is the entire question); **EIA-923** (monthly —
already adjudicated FINDING-caiso140 §D: ±50–80 GWh/mo fleet nets, no hourly
shape).

## §B — why the partial (DWR-only) instrument does not resolve the split

Model PS fleet (the model's own EIA-860 loader,
`load_eia860_pumped_storage("CAISO", 2025)` — one aggregate NP15 unit,
2,077.6 MW):

| plant | MW | share | public hourly instrument |
|---|---|---|---|
| Helms (PG&E) | 1,053.0 | 50.7 % | **none** (CTG/WSN: zero hourly sensors; no other source found) |
| W. R. Gianelli (DWR/USBR) | 424.0 | 20.4 % | SNL hourly storage — **gap covers most of 2023**; hourly elevation needs an elevation→storage curve; net flow contaminated by Pacheco PP draws and O'Neill exchanges; AF→MWh needs a head/efficiency model |
| Edward C. Hyatt (DWR) | 293.1 | 14.1 % | ORO hourly storage/in/outflow — but Hyatt is primarily a conventional-release plant; pump-back is the minority mode |
| J. S. Eastwood (SCE) | 199.8 | 9.6 % | **none** (SHV: zero hourly sensors) |
| Thermalito (DWR) | 82.5 | 4.0 % | TAB hourly |
| O'Neill (DWR/USBR) | 25.2 | 1.2 % | forebay records |

The uninstrumented Helms+Eastwood share is **1,252.8 MW = 60.3 %** of the
fleet; Helms alone can pump ~900 MW — larger than the entire ~700 MW model
belly-pumping signal under adjudication. A DWR-only series (824.8 MW,
39.7 %, itself gappy in 2023 and requiring an AF→MWh derivation with
plant-specific head/efficiency parameters) can bound its own plants and
nothing more: the fleet answer would remain entirely open to the Helms
shape. It does not convict or exonerate the model's PS belly pumping, so it
fails the charter's admissibility bar for the intake — and building the
missing 60 % from an assumed shape is exactly the fabrication the charter
forbids.

One measured **bound** falls out of S2 and is worth recording with its
caveat: the net feed prints ≥400 MW of net fleet **pumping** in at least
some real belly hours (hydro −414 MW while conventional generation is ≥ 0),
so real PS belly pumping is not zero. A bound is not a split: it cannot
separate the +793 MW wedge into PS-over-pumping vs conventional-hydro
under-allocation, which is the decision the instrument must make
(FINDING-caiso140 §G's PS-caveat clause stands untouched).

## §C — what this leaves (owner decision, filed not built)

Per the charter, the owner decides the lane order from here. The live
options, with this session's evidence attached:

1. **A3 — the P1 export-sink seam goes first** (caiso-138 §D, already
   owner-chartered, cross-ISO). caiso-140 §C priced it: the 2.7–3.0 GW
   import-parity plateau holds 51–61 % of defect hours at constant λ, and no
   admissible supply-side instrument reaches the gate without the full
   wedge. Nothing in this session weakens that lane; the wall strengthens
   its priority by removing the only competing data-first route.
2. **Non-public data.** The hourly split exists — in CAISO settlement-
   quality meter data and in PG&E's plant records (the 2025 Helms FERC
   relicensing docket shows the operator holds it). Obtaining it is an
   owner-level action (data request / purchase), outside any session's
   reach.
3. **Accept C3a-2025 as diagnosed-unclosed** (the nyiso-97 C3c disposition):
   the closure arithmetic is exactly ledgered (FINDING-caiso140), both
   remaining instruments are walled (A2 here; A1 standalone delivers <half
   the gate and is DO-NOT-REDO standalone), and the defect's root sits in
   the P1 seam (A3). The gate would remain FAIL on the record with its
   diagnosis attached.

**A1 status:** unchanged — filed, not built, standalone-forbidden
(FINDING-caiso140 §G). The rule-13 grant question stays unposed until a
joint construction exists to attach it to (A2 landing via new data, or A3
changing the arithmetic).

## §D — what this changes on the record

* **Keeper unchanged**; no dashboard registration due (rule 15 applies to
  completed runs — nothing solved).
* **Matrix (rule 28): no cell changes** — no mechanism was proposed, tested,
  or adjudicated; the A2 ask was a data intake and it produced no
  `ScenarioConfig` field, no curated datatype, no solve-affecting change.
  The caiso-140 stamps (`cc_mustrun_per_plant` R, `netload_drag_floors` R)
  stand.
* **Rule 22:** no out-of-training year touched; the survey read only
  2023–2025 committed bytes and live public endpoints.

## §E — re-open conditions (mechanical — the probe checks all of them)

Re-open A2 iff any of:

* CISO begins filing the EIA-930 `PS` (or `BAT`) category (S1 flips to
  nonzero rows — the cleanest possible instrument, fleet-complete by
  construction);
* CAISO's outlook/storage page grows a pumped-storage trace, or any OASIS
  report begins publishing per-fuel actuals with a PS item (S3/S6);
* PG&E/SCE hourly telemetry appears in CDEC for CTG/WSN/SHV (S4) — then the
  fleet-instrumentable share jumps to ~90 % and a derived-but-measured
  reservoir-delta instrument becomes buildable;
* the owner lands non-public hourly data (§C option 2).

`scripts/probes/_caiso141_water_source_survey.py` re-runs the full check in
~30 s of network time.

## §G — DO-NOT-REDO (new, binding)

* **Re-surveying these six source families for an hourly PS/hydro split
  without a §E trigger.** The committed probe re-checks all of them
  mechanically; a session that wants the answer runs the probe, not the
  survey.
* **Intaking a DWR-only (Gianelli/Hyatt/Thermalito/O'Neill) hourly
  instrument as the fleet adjudicator.** §B: 39.7 % of the fleet, 2023 gap,
  AF→MWh derivation required — it leaves the Helms majority unobserved and
  cannot decide the wedge split. (A DWR-side intake may still be worth it
  *inside a future joint construction* that gets Helms another way — that is
  a new charter, not this one re-run.)
* **Deriving an hourly PS shape from monthly EIA-923 nets, from the model's
  own arbitrage profile, or from any assumed/fitted allocation.** That is
  the fabricated shape the charter forbids, and feeding it back would be a
  rule-13 outcome-pin wearing a data costume.
* **Quoting the S2 negative-hydro bound as a split or as adjudication of
  the model's PS conduct.** §B: it bounds net fleet pumping in specific real
  hours; it says nothing about the wedge decomposition. The
  FINDING-caiso140 §G PS-caveat clause continues to govern any hydro/PS
  claim's basis statement.
* **Re-posing the A1 rule-13 grant question standalone.** It was
  deliberately not posed here; it attaches only to a joint construction
  that can reach the gate arithmetic (FINDING-caiso140 §C/§D).

Carried forward unchanged: everything in `FINDING-caiso140` §G,
`FINDING-caiso139` §G, `FINDING-caiso138` §G, `FINDING-caiso137b` §6,
caiso-137 §7 first bullet, `FINDING-caiso136` §5, caiso-135 §10, caiso-134
§9, caiso-133 §9, caiso-132 §10, caiso-131 §10, caiso-130 §7, caiso-129 §6,
caiso-127 §7.

Next number: caiso-142.
