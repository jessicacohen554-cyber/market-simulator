# FINDING — miso-267: MISO's bench drift is two nyiso-240 repairs; one of them was one-sided. Builder repaired, MISO's parts regenerated once.

```
SESSION : miso-267        ISO: MISO        DATE: 2026-09-23        LP SPENT: ZERO
KEEPER  : 2026-09-22-hydro-5-miso-ror — UNCHANGED. Nothing promoted, nothing pruned.
OBJECT  : miso-266 Defect B (FINDING-miso266-bench-regeneration-hazard §6 -> miso-267 STEP 1)
ANSWER  : the ENTIRE move is nyiso-240's two benchmark repairs (03eed7e9c, 2026-09-19),
          landed after MISO's parts were written (408c363a5, 2026-09-17). Switch both
          off and the HEAD builder reproduces all six committed parts BYTE-FOR-BYTE.
DEFECTS : the dual-fuel oil re-attribution moved only POSITIVE rows (the negative
          oil actual), leaked into a class no bench row carries, and ran after the
          CEMS backfill (a double count); the missing-month fill also filled PRE-COD
          months. All repaired in the builder, zero free parameters.
BENCH   : MISO's six parts regenerated ONCE with the repaired builder. Keeper:
          full span NOT-YET -> NOT-YET, train tier 2023-2025 CALIBRATED -> CALIBRATED,
          ZERO status flips. No other ISO's part touched (census §7: zero
          determination moves in any of the 13 registered runs).
```

Instruments: `scripts/probes/_miso267_bench_move_decomposition.py`,
`_miso267_bench_refresh.py`, `_miso267_rescore.py`, `_miso267_builder_census.py`.
Tests: `tests/curation/test_dual_fuel_oil_reattribution.py`,
`tests/scoring/test_bench_classfull_sign.py`.

---

## 1. The move, and where it came from

MISO's parts were last written at **`408c363a5`** (miso-261, 2026-09-17), by
`--rebuild-benchmark` then `dashboard_add_run.py` at that commit. Between it and
`origin/main` (`ae48c640`), **no MISO input in `data/raw` changed** (EIA-923,
EIA-930 and CAMPD hourly untouched; the 40 changed paths are other ISOs, AZ CAMPD
and solve-side outage extracts), and the builder files changed in 17 commits.

**The control that separates builder from dispatch.** miso-266's gate failed on
plants 1393 and 1743, so its table mixed their contribution with everything else.
Here the keeper bundle's dispatch is rebuilt from the COMMITTED part's own plant
keys (`_miso257_bench_rebuild.py`), so the plant → class map is the committed
part's by construction. The benchmark frames are then rebuilt in-process at HEAD
with nyiso-240's two repairs switched off one at a time:

| variant | classFull / e930 / plant fields moved, 2020–2025 |
|---|---|
| HEAD (both repairs) | 12 / 1 / 18–21 per year — **miso-266's table, reproduced exactly** |
| R2 off (`_reattribute_dual_fuel_oil`) | 1–10 / 0 / 2–10 |
| R1 off (`_backfill_eia923_missing_months`) | 11–12 / 1 / 14–18 |
| **both off** | **0 / 0 / 0 in every year — byte-for-byte the committed parts** |

So the whole move is `03eed7e9c`'s **R1** (missing-month fill) and **R2** (dual-fuel
oil re-attribution) — no other builder commit, no engine drift, no data drift, no
dispatch contribution. miso-263/264's attribution to `e63f730a` (spp-49) was wrong,
as miso-264's own attestation suspected.

**The 1393 / 1743 "dispatch-scoped" failures are R2's, not the dispatch's.** Both
are multi-class plants without unit-level CEMS shares, so
`render_calibration_html.build_payload` splits their facility CEMS series by
**EIA-923 monthly shares** (`split == "e923_monthly"`). Any repair that edits their
923 rows moves `campd / c_ann / c_mon` — R S Nelson's 5 GWh of ignition oil (ST/DFO)
moving into COAL_PRB empties its ST_CHP slice (`nodata` in 2024–25); St Clair's
boiler oil does the same across COAL_BIT / CT_PEAKER in 2020–22. The miso-257 gate
calls those fields dispatch-scoped, which is true only for single-class plants.
`_miso267_bench_refresh.py` carries the corrected gate: identity fields byte-equal
everywhere, and at an `e923_monthly` plant the facility CEMS total (Σ slices) must
be conserved. It is, in every year (e.g. 1743 2020: 1.8834 → 1.8833 TWh).

## 2. Every moved field, classified

| field | owner | verdict | evidence |
|---|---|---|---|
| CC_REGULAR +0.17 / +0.63 / +0.64 / **+2.65** (2020/21/23/24), OTHER_FOSSIL 2021 +0.43, COAL_BIT 2024 +0.31 | R1, withheld months | **correction** | 24 plant-years; in every one EIA-923's published annual equals the sum of its reported months to 0.0 GWh, so the blank month is absent from the annual, and CEMS meters generation in it. 2024: Acadia (Aug), Attala, Ouachita (May), Union Power (Dec), Blue Water (Jan), Cayuga, George Neal South, Washington Parish. |
| CC_REGULAR 2022 **+0.34**, 2023 **+0.21** of its +0.64 | R1, **pre-COD** months | **not a correction for C1: excluded** | Blue Water (62192, COD 2022-06) Jan–May 2022, Delta Energy Park (63259, 2022-03) Jan–Feb 2022, R D Morrow (6061, 2023-03) Jan–Feb 2023. Those months are outside EIA-923's reporting window, not withheld; CEMS records commissioning test energy there, scheduled by the commissioning programme rather than merit order, and the keeper's fleet has all three at **0 MW** before COD (`cod_ramp.monthly_online_mask`). Rule 14's different-boundary case. |
| `oil` drained 86–100 %, **negative** in 2022 / 2025 | R2, one-sided | **regression → repaired** | only `annual > 0` rows moved, so a modelled plant's net-negative oil row (station service) stayed in `oil`. MISO 2022: raw EIA-923 oil **+0.3836** TWh → **−0.0731**; 2025 +0.3530 → −0.0124 (0.353 − 0.365 moved). |
| new class `COAL` 0.1–0.8 GWh/yr | R2, generic group | **regression → repaired** | a coal plant with no measured class shares was booked to the bare `COAL` model group; R0 and R1 map it to the supply class, R2 did not. In PJM that stray key has been switching C8's coal forced-share to SKIPPED (§7). |
| +5 to +30 GWh/yr of oil-fired MWh | R2 after R0 | **regression → repaired** | the annual CAMPD backfill rebuilds a class from CEMS, which already meters the unit's oil-fired output; R2 then added the 923 oil on top (St Clair 1743, 2020–22, the largest). |
| 1393 / 1743 `campd`, `c_ann`, `c_mon`, `nodata`; `e930.coal_cems` +0.004 to +0.028; `ctOnly` ratios | consequence of R2 | follows R2 | the e923-monthly split basis (§1). |
| every fossil class 2025, ±0.1–0.6 | consequence of R1 | follows R1 | 2025 is a preliminary vintage; the combined-fossil reconcile fires, so adding 1.9 TWh of withheld months re-scales the family. |
| `co2` (reported-only since v2.9) | consequence | follows classFull | |

**Disclosed:** I examined the pre-COD fills **because** the first repaired
regeneration flipped C1 2022 CC_REGULAR PASS → FAIL (−7.69 → −8.03 against ±8.00),
and the window rule moves both affected cells toward the model by construction
(the model cannot produce energy it has no unit for). The classification stands on
the COD boundary, not on the flip; both variants are reported here so the owner
can overrule it:

| cell | committed | R1 fills pre-COD | **R1 operating window (landed)** |
|---|---:|---:|---:|
| C1 2022 CC_REGULAR | −7.69 PASS | −8.03 **FAIL** | −7.69 PASS |
| C1 2023 CC_REGULAR (train) | −6.97 PASS | −7.61 PASS | −7.40 PASS |

## 3. The builder repair (`scripts/run_calibration_full.py`)

* `_reattribute_dual_fuel_oil` moves a modelled plant's oil row **whatever its
  sign**, and books the generic `COAL` group to `_coal_supply_class`. The residual
  `oil` class is now exactly the non-fleet plants' rows.
* `_benchmark_eia923_frame` runs it **first**, on the raw 923 frame, so the CEMS
  backfill's firing test and residual, and the missing-month commensurability
  ratio, see each plant's oil-fired MWh in its modelled class.
* `_backfill_eia923_missing_months` fills only months inside the plant's
  **operating window** — on/after its first unit's EIA-860 COD, inclusive, from
  the same `load_unit_cod_map` the fleet's COD ramp reads.

Zero ScenarioConfig fields, zero free parameters, no solve path touched (the only
solve-time call writes the post-LP benchmark frame). 11 hermetic tests; 5 of them
fail on the pre-fix builder.

## 4. What is left negative, and why none of it is the builder

| cell | value | cause |
|---|---:|---|
| SOCO 2023/24/25 `OTHER` | −0.51 / −0.48 / −0.65 | pumped storage PS/WAT net −0.65 to −0.70 TWh: pumping exceeds generation. **Measured.** |
| NEISO 2020 `COAL_PRB` | −0.0191 | Bridgeport 568 ST/SUB −19,082 MWh: an idle coal unit's station service. **Measured.** |
| MISO 2022 `oil` (regenerated) | −0.0480 | plant 7977, §5 |
| SPP 2022 `oil` (stale part) | −0.2482 | plant 1299, §5 (+0.001 of one-sided R2) |

**"A measured actual cannot be negative" is not true of net generation.** EIA-923
books net of station service and pumping, so a class of idle or pumping units can
measure negative and be right. What the builder must never do is MANUFACTURE a
negative — which is what R2 did.

## 5. ROUTED, NOT ABSORBED — EIA-923 respondent errors (kWh entered as MWh)

Four plants report a 2022/2024 net generation ~1000× their own history, all
physically impossible at their nameplate:

| ISO | yr | plant | row | that year | every other year |
|---|---|---|---|---:|---|
| MISO | 2022 | Granite Falls 2 (7977), 6.0 MW | IC/DFO | −107,000 MWh | −78 … −98 |
| SPP | 2022 | Larned (1299), 16.4 MW | IC/DFO | −311,800 MWh | −235 … −408 |
| NYISO | 2024 | OBP Cogen (57798), 4.6 MW | CT_CHP | −397,062 MWh | — |
| NEISO | 2024 | Stamford Health (64515), 10.4 MW | OTHER + oil | −108,615 MWh | — |

MISO's −0.107 TWh sat inside the committed 2022 `oil` (+0.3836) all along; the
repair only made it visible. A screen belongs in the builder, but a nameplate
bound is **not** it: over every ISO-year it flags 74 plants, most of them EIA-860
nameplate gaps in the payload's accessor (St Clair listed at 18.5 MW, Hoot Lake at
1.0 MW), not generation errors. The negative-and-impossible subset is clean (these
four). **Routed as its own lane** — it moves four ISOs, and a sign-only screen
would miss a ×1000 error inside a large positive class.

## 6. MISO's parts, regenerated once

`_miso267_bench_refresh.py --write` over the class-map-pinned bundle; corrected
gate PASS in all six years; only `frontend/data/backcast/bench/MISO/*.json.gz`
changed (sha256 over all 44 parts, before/after); `meta` changes only in its stamp
(`64b6829fb757` → HEAD's `fb56b7e445d9`; the dispatch-derived `groups` are carried
from the committed part, which the rebuilt dispatch cannot reproduce).
`check_bench_freshness --iso MISO`: **6 parts, 0 STALE** (all six were STALE).

| class, TWh | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| CC_REGULAR | +0.174 | +0.647 | +0.003 | +0.434 | +2.651 | −0.144 |
| COAL_BIT | +0.094 | +0.110 | +0.087 | +0.070 | +0.376 | −0.234 |
| COAL_PRB | +0.184 | +0.247 | +0.260 | +0.231 | +0.202 | −0.222 |
| CT_PEAKER | +0.006 | +0.198 | +0.053 | +0.079 | +0.068 | −0.070 |
| OTHER_FOSSIL | +0.001 | +0.432 | +0.006 | +0.002 | +0.003 | +0.617 |
| **oil** | 0.346 → 0.034 | 0.724 → 0.094 | 0.384 → **−0.048** | 0.462 → 0.034 | 0.397 → 0.036 | 0.353 → 0.009 |

**The keeper, re-scored on the new parts** (`_miso267_rescore.py`, same model side):

| | committed parts | regenerated parts |
|---|---|---|
| full span 2020–2025 | NOT-YET, scored 8 / target 4 / ledgered 1 / fails 3 | **NOT-YET, identical** |
| train tier 2023–2025 | CALIBRATED, fails 0 | **CALIBRATED, fails 0** |
| status flips | — | **0** (59 records move, full span) |
| C1 2020 COAL_BIT | −10.67 FAIL | −10.76 FAIL |
| C1 2022 COAL_PRB | +7.93 PASS | +7.67 PASS |
| C1 2022 CC_REGULAR | −7.69 PASS | −7.69 PASS |
| C1 2023 CC_REGULAR (train) | −6.97 | −7.40 (headroom 1.03 → 0.60 TWh) |
| C1 2024 CC_REGULAR (train) | +2.58 | −0.07 |
| C5a co2 (reported-only) | −6.6 … −1.2 % | −6.8 … −1.7 % |

MISO has one registered run, the keeper; no run is stamped to it. Its `meta.json`
`shared_inputs.eia923` is re-pointed to the repaired frame (`--rebuild-benchmark`,
the documented adoption path; audit E11 classes `shared_inputs` as provenance), so
the bundle's recorded benchmark input is the one its parts were built from. Its run
payload's `volErr` heatmap (display only; not read by the scorer) still reflects
the old frames — regenerating it needs the dispatch the slim bundle does not carry.

## 7. Every other ISO (rule 25), measured and NOT refreshed

`_miso267_builder_census.py` rebuilds every registered run's frames through the
pre-repair and repaired builders on identical inputs and re-scores each run against
its own committed parts plus the repair's increment:

| ISO | max \|Δ classFull\| | determination moves | notes |
|---|---:|---|---|
| CAISO | 0.0000 | none | |
| ERCOT | 0.076 (2021 CT_PEAKER) | none | |
| MISO | 0.216 (2022 CC_REGULAR, pre-COD) | none | regenerated here instead (§6) |
| NEISO | 0.085 (2022 ST_GAS) | none | |
| NWPP | 0.001 | none | |
| NYISO | 0.007 | none | |
| PJM | **0.259** (2022 CC_REGULAR, pre-COD) | none | C8 coal forced-share **SKIPPED → PASS** in 2020–2024; a phantom C1 `COAL` cell disappears |
| SOCO | 0.079 (2023 CC_REGULAR) | none | |
| SPP | 0.046 (2021 CT_PEAKER) | none | |

**PJM, reported because it is a real improvement hidden in a protective criterion.**
PJM's committed 2020–2024 parts carry `classFull.COAL` = 0.0001–0.0009 TWh — R2's
leak. `calibration_verdict._class_load_share` aggregates the coal fleet for C8's
materiality only when BOTH `gmModel["COAL"]` and `classFull["COAL"]` are exactly
zero, so that sliver made PJM's whole coal fleet read as 0 % of load and **skipped
the C8 coal forced-share check** on the keeper's own 2023–2024. The repair restores
it (PASS). Each ISO's lane refreshes its own parts; nothing here does.

## 8. The test the owner asked for, and why it is not the literal one

`tests/scoring/test_bench_classfull_sign.py`: every negative `classFull` entry in
every committed part must be a **verified measured negative** (listed with its
cause and re-verified against raw EIA-923 in the `fulldata` tier: the raw class
total is negative and the part passes it through) or a named, routed
**known defect** carried as `xfail(strict=True)` — MISO 2022 and SPP 2022 (§5), which
turn RED the moment their owner fixes them, forcing the entry out. An unlisted
negative fails with the instruction to classify it. The literal "no entry is
negative" would be false for SOCO's pumped storage and NEISO's idle unit, which are
measured and right.

## 9. Also repaired, and one gap routed

* **Composer** (`scripts/probes/_miso266_compose_span.py`): it copied leg 1's
  `calibration_flags.years` and one-year `shared_inputs` onto a six-year
  composite. Now it widens the years and re-spans `eia930 / eia923 / campd` over
  the composite (nwpp-42's `39c79724`, already in `_hydro5_compose_span.py`).
  `tests/iso/miso/test_miso266_compose_span_span_fields.py`, 2 tests, both fail on
  the old composer. **The charter's claim that `hydro5_miso_ror_span` carries the
  defect is stale:** measured, it records six-year frames and a six-year
  `calibration_flags.years`, and `audit_keepers --iso MISO` reads 0 warnings.
  `miso264_anchor_span` is no longer on disk.
* **ROUTED — the stamp cannot see this class of drift.** `bench_stamp`'s
  `PAYLOAD_SOURCES` are the three payload renderers; the frame builders live in
  `run_calibration_full.py`, outside it. That is why MISO's parts read
  `0 STALE` through miso-264/265/266 while nyiso-240 had moved them. Adding the
  whole file would mark every part stale on nearly every commit; a function-level
  AST fingerprint of the benchmark builders is the targeted fix, and it touches
  every ISO's stamp, so it is its own lane.
