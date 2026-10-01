# FINDING — nyiso-240: the Feb/Nov "winter" lead is a BENCHMARK artifact with TWO named causes. The ISO's own meter says the model is not over-burning fossil in those months at all

**Session** nyiso-240 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **the parent ran ZERO LP, and no shard was launched**).
**Date** 2026-09-19. **Base** `origin/main` at `d95d45b6`.
**Keeper** `2026-09-17-nyiso239-bench-oil-basis` (bundle `results/calibration/nyiso239_bench_span`), years {2022, 2023, 2024, 2025} — **UNCHANGED by this session. Nothing armed, screened, solved, promoted or registered.** `solve_surface.fingerprint` `bd2b4657f9b5df7e`, confirmed unchanged.
**Promotion verified on `main`**: the handoff's `afe941ee` is not a resolvable object here (the branch was auto-merged and deleted), but the three stores are all present — `keepers/NYISO.json` names the keeper, `registry/` + `runs/` carry it, and `results/calibration/nyiso239_bench_span` is committed. The promotion **is** on `main`.

> ## HEADLINE
> 1. **THE HANDOFF'S LEAD DOES NOT SURVIVE THE ISO'S OWN METER.** Against NYISO's published
>    hourly fuel mix (`Natural Gas + Dual Fuel + Other Fossil` — fuel-agnostic ISO telemetry), the
>    model's **total fossil** in 2022 is **+2.0 % in February** and **+0.8 % in November**, and
>    **−1.1 % for the year**. The model is **not** burning extra fossil in the fuel-delivery months.
>    The real month-grain outliers are **January −7.6 %** and **December −10.6 %**, both *under*-runs.
>    **Winter gas deliverability / pipeline constraint / dual-fuel switching are NOT indicated**, and
>    `nyiso_iroquois_winter_spread` (`R`) already proved at the LP that no fuel-side lever can make a
>    downstate winter premium here. The `CC_REGULAR` over-run is **intra-fossil misallocation**.
> 2. **61 % of the annual miss in two months is a RULER artifact, and the ruler has a NAME.**
>    **Bethlehem Energy Center (plant 2539), a 750 MW CC_REGULAR, is ENTIRELY ABSENT from EIA-923
>    for February and November 2022** — both monthly cells *and* the published annual, which is the
>    sum of the ten reported months. CAMPD meters **596.0 GWh** there. Bethlehem alone is
>    **56 % of the Feb+Nov miss** and **28 % of the whole +3.139 TWh `CC_REGULAR` over-run** (§2).
> 3. **The existing CAMPD backfill CANNOT catch it, by construction**: `_backfill_eia923_with_campd`
>    gates on an **annual** floor of 50 GWh and Bethlehem's annual reads 4,262 GWh. **Ten good months
>    hide two missing ones.** This is the nyiso-239 defect class one layer over — the ruler, not the
>    model — and it is invisible at the grain the guard checks.
> 4. **A SECOND, independent boundary defect**: EIA-923 routes 100 % of a dual-fuel plant's
>    oil-burn MWh to the `oil` class, while the model books **every** MWh of Astoria Energy, Astoria
>    II, Zeltmann and Richard M Flynn as `CC_REGULAR / gas_cc` — verified at the unit layer, where
>    the model's *entire* `oil`-fuel fleet is **11.1 GWh across four tiny plants** against a bench
>    `oil` class of **1,843.7 GWh** (§3).
> 5. **THE CROSS-ISO CENSUS IS MEASURED, NOT ASSERTED — and this is what nyiso-239 could not do.**
>    Defect (2) occurs in **67 plant-years across nine BAs** (79 plant-class rows, 57 (ISO, year, class) cells); both repairs were scored through
>    `calibration_verdict.determine()` against **every ISO's designated keeper**: **42 C1 rows move
>    ≥ 0.05 pp, ZERO change status, and ZERO of the eight determinations flip** (§5).
> 6. **The margin, which is what this session was pointed at**: NYISO 2022 `CC_REGULAR`
>    **+2.95 → +1.93 pp** against a ±3.0 pp band — headroom **0.05 pp → 1.07 pp, a 21× improvement**,
>    and the largest single row move in any ISO. **Stated at full magnitude: it does NOT close the
>    object** — 2023 `ST_GAS` (+2.85 → +2.70) and 2024 `CC_REGULAR` (+2.46 → +2.44) are barely
>    touched, and **+2.26 TWh of the 2022 over-run is real** (§4).
> 7. **REALISING IT FOR NYISO COSTS ZERO LP.** nyiso-239's four shard SHAs **still resolve** (I
>    fetched and checked out all four, `dispatch/` and `unit_hourly/` included, 155 MB, now on local
>    disk). The NYISO half is fetch → compose → `--rebuild-benchmark` → re-score → re-register, with
>    **no solve** (§6). nyiso-239 §7 assumed a ~18 min four-shard re-solve; that assumption is
>    **falsified**, in NYISO's favour.
> 8. **NOT LANDED. §8 is the decision, and it is the owner's** — both repairs are shared bench
>    constructions reaching every ISO (rule 25 `[R-ISO-SCOPE]`, and the explicit nyiso-239 precedent).

---

## 0. WHAT THE HANDOFF ASKED, AND THE ANSWER

> *"THAT ASYMMETRY IS THE LEAD — hot in the fuel-delivery months, cold in the heat months, is not an
> offer-level story. It points at winter gas deliverability / dual-fuel switching and at summer
> capability. … RULE OUT A BENCHMARK ARTIFACT FIRST."*

**Ruled out is the wrong verb: the benchmark artifact is ruled IN, twice, and the asymmetry it was
built on is mostly not there.** The handoff's Feb +788 / Nov +774 GWh is measured against EIA-923.
Measured against **CAMPD** — the fuel-agnostic per-unit meter — the same two months read **+560** and
**+371**, and against the **ISO's own hourly telemetry** the model's whole fossil fleet is within
**2 %** in both. What remains after the two benchmark repairs is a **broad, mildly seasonal
intra-fossil misallocation**, not a winter fuel event.

---

## 1. THE ISO'S OWN METER — the arbiter that decides the framing

`data/raw/NYISO/fuel-mix/NYISO_fuelmix_hourly_2022.csv.gz`, categories
`Natural Gas + Dual Fuel + Other Fossil Fuels` (NYISO publishes **no** `oil` category; oil-capable
units file as `Dual Fuel`), summed to calendar months in `America/New_York`, against the keeper's
committed `hourly/class_hourly_2022.parquet` summed over every fossil class:

| mo | model fossil GWh | NYISO published GWh | Δ | Δ% |
|---|---:|---:|---:|---:|
| 1 | 5,447.9 | 5,897.5 | −449.7 | **−7.6 %** |
| **2** | 4,884.3 | 4,786.3 | **+98.0** | **+2.0 %** |
| 3 | 4,441.3 | 4,367.2 | +74.1 | +1.7 % |
| 4 | 4,539.4 | 4,402.8 | +136.6 | +3.1 % |
| 5 | 5,386.0 | 5,279.6 | +106.4 | +2.0 % |
| 6 | 5,585.4 | 5,545.6 | +39.8 | +0.7 % |
| 7 | 7,827.8 | 7,893.5 | −65.7 | −0.8 % |
| 8 | 7,720.4 | 7,761.1 | −40.7 | −0.5 % |
| 9 | 5,023.7 | 5,046.7 | −22.9 | −0.5 % |
| 10 | 4,535.2 | 4,595.1 | −59.9 | −1.3 % |
| **11** | 4,899.0 | 4,860.8 | **+38.1** | **+0.8 %** |
| 12 | 4,677.4 | 5,233.9 | −556.5 | **−10.6 %** |
| **year** | **64,967.7** | **65,670.1** | **−702.3** | **−1.1 %** |

**February and November are two of the model's most accurate months.** Any mechanism proposed to
suppress fossil output there would be fixing a miss that the ISO's meter says does not exist.
The class-level `CC_REGULAR` over-run is therefore matched, almost MWh for MWh, by under-runs in
`CC_CHP` (−1.02), `ST_GAS` (−0.92), `CT_PEAKER` (−0.59) and `OTHER_FOSSIL` (−0.78, where the model
generates **zero**).

---

## 2. DEFECT R1 — EIA-923 drops whole months, and the annual drops them with it

### 2.1 The instance

`data/raw` EIA-923 Page 1, plant 2539, 2022, all four rows (CA/CT × KER/NG):

```
netgen_february_mwh = NaN     netgen_november_mwh = NaN
netgen_annual_mwh   = 1,457,184 (CA NG) + 2,805,326 (CT NG) = 4,262,510
                    = EXACTLY the sum of the ten reported months
```

`netgen_annual_mwh` is EIA's own published *"Net Generation (Megawatthours)"* column
(`scripts/data/process_f923_fuel_costs.py:229`), not a derived sum — so **EIA itself published an
annual that omits two months**. The bench's `e_mon` for Bethlehem reads
`[356.8, 0.0, 32.8, 36.4, 519.9, 526.8, 522.9, 576.7, 546.3, 597.3, 0.0, 546.8]` GWh; CAMPD's
`c_mon` reads `[246.8, 232.4, 22.2, 25.0, 353.8, 358.3, 353.7, 383.2, 363.9, 400.6, 363.6, 380.3]`.

Corroboration the plant genuinely ran: Bethlehem's **2021** EIA-923 Feb = 332.6 GWh and Nov =
433.9 GWh; its **2023** Feb = 296.9 GWh. CAMPD's 232.4 / 363.6 sit inside that envelope.

### 2.2 Why the existing guard misses it, and the magnitude

`_backfill_eia923_with_campd` (`scripts/run_calibration_full.py:2345`) fires only when a plant's
**annual** for its mapped grid class is below `_CAMPD_BACKFILL_MIN_MWH = 50,000`. Bethlehem's is
4,262,510. **The guard is annual-grain and the defect is month-grain.**

CAMPD under-meters Bethlehem by a fixed factor — CEMS meters the two CT stacks of this 2×1 CC, and
the steam turbine (the `CA` prime-mover row, 34.2 % of net) has no stack. Measured over the **ten
months EIA-923 does report**: `Σe_mon / Σc_mon = 1.476`. Two estimators, both reported:

| estimator | added to `CC_REGULAR` 2022 | actual | Δ model−actual | share | headroom vs ±3.0 |
|---|---:|---:|---:|---:|---:|
| committed (no repair) | — | 33.259 | +3.139 | **+2.95 pp** | **0.05 pp** |
| raw CAMPD net | 596.0 GWh | 33.855 | +2.543 | +2.61 pp | 0.39 pp |
| **CAMPD × the plant's own 10-month ratio** | **879.6 GWh** | **34.138** | **+2.260** | **+2.44 pp** | **0.56 pp** |

The ratio is **measured from the same plant in the same year** — zero free parameters (rules 21 / 24)
— and it is the same "scale CAMPD's shape to a target" arithmetic `_book()` already performs. The
verdict is identical on either estimator; the ratio is preferred under rule 14 `[R-ACCURATE]`
because the raw CAMPD number is *known* to be short by a measured 32 %.

**Independent confirmation at the plant grain** (from the retrieved `unit_hourly_2022.parquet`):
model Bethlehem = 5,009.7 GWh; CAMPD × 1.476 = 5,143 GWh. **The model's Bethlehem is essentially
exact against the scaled meter** — its entire apparent +747 GWh "over-run" is the two missing months.

### 2.3 The cross-ISO census of R1 — 67 plant-years, nine BAs

Detection rule, applied to every committed bench part: a backfill-eligible non-CHP grid plant
(`CC_REGULAR / CT_PEAKER / ST_GAS / COAL_*`) for which **every** EIA-923 row of that (plant, year)
is NaN in month *m*, while CAMPD meters generation in *m*. Largest implied `classFull` shortfalls:

| ISO | yr | class | GWh | ISO | yr | class | GWh |
|---|---|---|---:|---|---|---|---:|
| MISO | 2024 | CC_REGULAR | **2,651.1** | SOCO | 2025 | CC_REGULAR | 900.4 |
| SOCO | 2023 | CC_REGULAR | **1,330.5** | NWPP | 2023 | COAL | 794.7 |
| **NYISO** | **2022** | **CC_REGULAR** | **879.6** | MISO | 2020 | COAL_PRB | 765.8 |
| MISO | 2023 | CC_REGULAR | 642.7 | MISO | 2021 | CC_REGULAR | 633.6 |
| MISO | 2025 | CC_REGULAR | 615.9 | PJM | 2022 | CC_REGULAR | 609.1 |
| ERCOT | 2023 | COAL_PRB | 589.1 | PJM | 2020 | CC_REGULAR | 517.1 |
| PJM | 2024 | CC_REGULAR | 457.6 | **NYISO** | **2025** | **CC_REGULAR** | **334.5** |

**67 distinct (ISO, year, plant)**, 79 plant-class rows, **57 (ISO, year, class) cells**; the full table regenerates from the probe. Every BA is affected; CAISO's exposure is trivial
(2.1 GWh).

---

## 3. DEFECT R2 — the dual-fuel class boundary, one layer below nyiso-239's

nyiso-239 repaired the gas↔oil boundary at the **930/923 reconcile target**. The same boundary is
still crossed at the **923 class split itself**: `_classify_f923` routes **100 %** of DFO / RFO / JF /
KER / WO / PC to the `oil` class, so a dual-fuel CC's oil hours leave `CC_REGULAR` — while the model
never moves that unit anywhere.

**Verified at the unit layer** (`hourly/unit_hourly_2022.parquet`, retrieved from the shard):

```
55375 Astoria Energy      -> CC_REGULAR/gas_cc 4,504.9 GWh   (no oil unit)
57664 Astoria Energy II   -> CC_REGULAR/gas_cc 4,046.7 GWh   (no oil unit)
56196 Zeltmann            -> CC_REGULAR/gas_cc 3,558.9 GWh   (no oil unit)
2516  Northport           -> ST_GAS/gas_st     1,816.6 GWh
2500  Ravenswood          -> CC_REGULAR 1,670.8 / ST_GAS 921.7
model `oil`-FUEL fleet, ALL plants, whole year:  11.1 GWh  (4 plants)
bench `classFull.oil`:                        1,843.7 GWh
```

`dual_fuel_switching` (cell **K**) prices these units at `min(gas, oil)` — it changes the unit's
*fuel price*, never its class. So the model's books and EIA-923's books disagree about where a
switched hour lands, by construction.

EIA-923 oil-fuel MWh re-attributed to the burning plant's own bench class (GWh):

| yr | ST_GAS | CC_REGULAR | CC_CHP | others | `oil` class after |
|---|---:|---:|---:|---:|---:|
| 2022 | +778.0 | +666.2 | +78.7 | +145.4 | 1,843.7 → 175.4 |
| 2023 | +185.1 | +48.8 | +18.6 | +24.9 | 421.7 → 144.4 |
| 2024 | +106.5 | +30.4 | +13.0 | +38.0 | 322.5 → 134.5 |
| 2025 | +580.5 | +264.8 | +106.4 | +18.4 | 1,148.7 → 178.5 |

The residual `oil` class is the plants that are **not in the model fleet** — the right place for it.
The monthly shape is the physical signature: Astoria II 2022 books Jan 124.4 / Feb 14.5 / Dec 62.3,
Zeltmann Jan 102.7 / Dec 53.0 — **cold months only**, which is what dual-fuel oil burn is.

**Reported at full magnitude, because it cuts both ways (rule 1 `[R-STRUCT]`):** R2 *helps*
`CC_REGULAR` in every year and `ST_GAS` in 2023 (+2.85 → +2.70 pp), and *hurts* `ST_GAS` in 2022
(−0.61 → −1.17 pp) and 2025 (−2.74 → −3.14 pp). **It is not selected on the residual.** The
discriminating evidence is a class-membership identity at the unit layer (above) and a burn shape,
neither of which is a fit statistic.

---

## 4. WHAT THE TWO REPAIRS DO TO NYISO — scored with the real scorer

`calibration_verdict.score_fuelmix` against the keeper's committed payload, share pp (band ±3.0):

| yr | class | committed | R1 | R2 | **R1+R2** |
|---|---|---:|---:|---:|---:|
| **2022** | **CC_REGULAR** | **+2.95** | +2.44 | +2.43 | **+1.93** |
| 2022 | ST_GAS | −0.61 | −0.57 | −1.22 | −1.17 |
| **2023** | **ST_GAS** | **+2.85** | — | +2.70 | **+2.70** |
| **2024** | **CC_REGULAR** | **+2.46** | — | +2.44 | **+2.44** |
| 2025 | CC_REGULAR *(SKIPPED, preliminary vintage)* | +1.94 | +1.75 | +1.74 | +1.55 |
| 2025 | ST_GAS *(SKIPPED)* | −2.74 | −2.71 | −3.17 | −3.14 |

**Full determination**, `calibration_verdict.determine()` on all four variants:
**`CALIBRATED`, grade 7, fails 0, `price_tail` (C3c) the lone ledgered caveat — identically, in all
four.** No criterion moves; no caveat is added or removed. **These repairs carry no determination
risk in either direction**, which is exactly the property the session was asked for: *margin*.

**Stated plainly: this does not close the object.** Two of the three tight rows barely move, and
**+2.26 TWh of the 2022 `CC_REGULAR` over-run survives both repairs.**

---

## 5. THE CROSS-ISO VERDICT CENSUS — the measurement nyiso-239 explicitly could not make

nyiso-239 §7: *"I have **not** measured the other 11 cells' verdict impact; doing so needs each ISO's
hydrated profile and is a cross-lane job."* **It does not.** Every ISO's keeper payload and every
bench part are committed, so the whole census runs in-process at zero LP. Each ISO's designated
keeper re-scored through `determine()` against a repaired copy of its own bench:

| ISO | keeper | base | R1 | R1+R2 |
|---|---|---|---|---|
| CAISO | `2026-09-12-caiso-275-gascoupling` | CALIBRATED 7/0 | **same** | **same** |
| ERCOT | `2026-09-09-ercot265-receipts-fallback` | CALIBRATED 7/0 | **same** | **same** |
| MISO | `2026-09-16-miso-260-seam-ladder` | NOT-YET 4/3 | **same** | **same** |
| NEISO | `2026-09-16-neiso110-dualfuel-derate-scope` | CALIBRATED 7/0 | **same** | **same** |
| NYISO | `2026-09-17-nyiso239-bench-oil-basis` | CALIBRATED 7/0 | **same** | **same** |
| PJM | `2026-09-11-pjm-d4-4-gasoutage` | CALIBRATED 8/0 | **same** | **same** |
| SOCO | `2026-09-17-soco53-measured-ct-hr` | NOT-YET 4/1 | **same** | **same** |
| SPP | `2026-09-16-spp-42-commitment-feasibility` | CALIBRATED 7/0 | **same** | **same** |

"same" = identical determination, identical grade, identical failing-criteria set, identical failing
C1 rows. **42 C1 rows move ≥ 0.05 pp; 0 change status; 0 determinations flip.** Largest movers:

| ISO | yr | class | pp before | pp after | Δ |
|---|---|---|---:|---:|---:|
| **NYISO** | **2022** | **CC_REGULAR** | +2.95 | **+1.93** | **−1.02** |
| NEISO | 2022 | CC_REGULAR | +1.01 | +0.14 | −0.87 |
| NYISO | 2022 | ST_GAS | −0.61 | −1.17 | −0.56 |
| MISO | 2022 | COAL_PRB | +1.56 | +1.22 | −0.34 |
| MISO | 2024 | CC_REGULAR | +0.88 | +0.62 | −0.26 |
| SOCO | 2023 | CC_REGULAR | +0.86 | +0.61 | −0.25 |

MISO's two **failing** C1 rows (`COAL_BIT/2020`, `CC_REGULAR/2022`) both move slightly *toward*
passing (+0.08, +0.09 pp) without flipping. SOCO's two failing rows do not move.

**Caveat on this census, stated rather than buried:** 34 of 44 committed bench parts are **STALE**
at HEAD (`check_bench_freshness.py` — ERCOT, NEISO, PJM, SOCO, SPP and some MISO/SPP years do not
reproduce under the builder at HEAD; this is the nyiso-239 §4.1 correction in force, and those lanes
have not re-solved since). **NYISO's four parts are fresh.** The census is therefore exact for
NYISO and an estimate elsewhere — but it is an estimate built on each ISO's *own registered numbers*,
which is the same basis its published determination rests on today.

---

## 6. COST — ZERO LP FOR NYISO. nyiso-239 §7's re-solve assumption is FALSIFIED

nyiso-239 recorded four recovery SHAs in `.gitignore` and predicted a ~18 min four-shard re-solve
would be needed because *"a bench part is regenerated only from a bundle's `dispatch/` +
`system.parquet`, and the keeper bundle on `main` carries neither."* **The four SHAs still resolve.**
Verified this session, two days on:

```
git fetch origin <sha> && git checkout <sha> -- results/calibration/nyiso239_bench_<yr>
  2022  5802986acd77b69cfeb13720a8f0167f6ccb80a7
  2023  0f03dd49b1daee41a1fd0244474e6c4cea7c0c9b
  2024  ce299f37da628cf7299cba5422f52f4ab05765bb
  2025  9859790c33415e9c6dc54ecfb1c799ecc8fb76da
```

All four are **on local disk now** (155 MB, 17 files each), carrying `dispatch/<YR>_P1.parquet`,
`dispatch/<YR>_P1_fleet.parquet`, `system.parquet` **and** `hourly/unit_hourly_<YR>.parquet` — the
per-plant layer §2.2 and §3 are measured on. They remain gitignored at `.gitignore:2400` (rule 31
`[R-RETAIN]`: ignored, never `rm`'d).

**So the NYISO realisation is:** fetch (done) → compose → `run_calibration_full.py
--rebuild-benchmark <dir>` → re-score → carry the attestation across → re-register. **No solve.**
The dispatch stays the keeper's exact dispatch — the same bytes gate G-1 verified to
5.0 × 10⁻⁷ TWh — so **what changes is only the benchmark**, and G-1 byte-identity is preserved by
construction rather than re-argued.

*(G-DRIFT for the record: `git diff 3edb8ad8 HEAD` over the solve path is 14 files / +3,176 lines,
including `model/lp/model.py` and `scenarios.py`. That matters for a future **re-solve**, and is
precisely why the re-render route — which never re-enters the LP — is the correct one here.)*

---

## 7. THE SUCCESSOR OBJECT, RE-AIMED: `CT_PEAKER` collapses out of merit from 2023

With the winter/deliverability framing withdrawn, the intra-fossil misallocation has one dominant
signature, and it is **not** seasonal:

| yr | model CT_PEAKER TWh | actual | model hrs > 1 MW | mean MW when on | model ST_GAS | actual ST_GAS |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | **2.429** | 2.829 | 3,939 | 616.6 | 7.292 | 8.106 |
| 2023 | **0.246** | 2.114 | 1,076 | 228.4 | **11.540** | 8.141 |
| 2024 | **0.300** | 1.911 | 2,373 | 126.6 | 9.451 | 9.913 |
| 2025 | **0.771** | 2.812 | 7,151 | 107.8 | 9.793 | 13.522 |

**Capacity is intact** — model CT_PEAKER peaks at ~1,940–2,370 MW in *every* year — so this is an
**economic merit-order** effect, not availability, and `nysdec_peaker_rule_availability` (24 rows of
small GTs) is far too small to explain it. The energy the CTs do not make is exactly what shows up
as 2023 `ST_GAS` **+3.40 TWh** and 2024 `CC_REGULAR` **+2.94** / `CC_CHP` **+2.16** — i.e. **the two
C1 rows the benchmark repairs do NOT touch.** One mechanism plausibly owns both.

**Matrix status, read before proposing anything (rule 28 `[R-MECH-MATRIX]` (a)):**
* `nyiso_ct_peaker_bands_measured` — **R**, with a *sharpened* re-test condition (nyiso-200): the
  three-way arm on **2025** under FINDING-nyiso200 §7's corrected gates, C3a-2025 the named risk,
  span only if it clears, **never alone**. Not re-tested here, and no new evidence is offered against it.
* `ct_peaker_committed_measured` — **U**, and explicitly *"an ASK FOR THE NYISO LANE"*: NYISO's
  `_NYISO_OFFER_CURVE` `CT_PEAKER.committed` is **1.35** against its own measured `phys_committed`
  **0.843** (ratio **1.60, the largest in the model**), resting on a three-way NYISO↔CAISO↔NEISO
  citation ring in which **no ISO cites a measurement**. Grounding NYISO's band on NYISO's own
  0.843 is a rule-14 / rule-25 repair, not a transfer — and it lowers CT offers, which is the
  direction the table above wants. **This is the recommended next lever.** It is an
  `offer_curve_by_group` band multiplier, so it is the rule-1 authorized channel and must be set
  **ex ante, one config across every scored year, declared in the PREREG, never swept against the
  gates**, and carried in the DOF ledger (rule 21).

**No matrix cell moves in this session** — a bench construction has no matrix row (the nyiso-239
precedent), and no `ScenarioConfig` field was touched.

---

## 8. THE DECISION — the owner's, and it is open

Both repairs are **shared bench constructions** in `scripts/run_calibration_full.py`:

* **R1** — extend `_backfill_eia923_with_campd` to the **month grain**: for an already-eligible
  non-CHP grid plant, a month every EIA-923 row reports as NaN is filled from CAMPD net scaled by
  that plant's own reported-month `Σe_mon / Σc_mon`, and added to the annual. The annual firing test
  is untouched, so **no plant the guard reaches today changes**.
* **R2** — route a dual-fuel plant's EIA-923 oil-fuel MWh to the **class its own units are modelled
  in**, leaving the `oil` class to plants outside the model fleet.

**Zero LP to develop, zero `ScenarioConfig` fields, zero free parameters, no mechanism-matrix cell.**
Rule 25 `[R-ISO-SCOPE]` and the nyiso-239 precedent (*"a NYISO lane does not quietly change seven
ISOs' benchmarks"*) both say this lane does not land them alone — **even though §5 now shows zero
verdict impact anywhere**, which is the fact nyiso-239 lacked.

**Three questions:**
* **Q1.** Land **R1** (the month-grain backfill)? It is the larger and cleaner of the two: a pure
  data-completeness repair with an unambiguous right answer, 67 plant-years, no ISO's verdict moving.
* **Q2.** Land **R2** (dual-fuel class re-attribution)? Directionally mixed by row (§3) and therefore
  the one that most needs to be judged on the class-membership identity rather than on the residual.
* **Q3.** If either: does this lane re-render and re-register NYISO now (**zero LP**, ~15 min of
  wall clock, §6), or does that wait on a cross-ISO re-render pass?

**Nothing is at risk while the answer takes time in the repository** — this session solved nothing,
so rule 31 `[R-RETAIN]` protects no new bundle. **But the four retrieved nyiso-239 legs live on this
container's disk and will not survive its reclamation** (they are recoverable again from the SHAs
above for as long as those refs live, which is not guaranteed). That is the whole of the exposure.

---

## 9. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — nothing armed, no offer-curve multiplier moved, `authorized_price_tuning`
  **NONE**. The determination is reported as a *consequence* in §4 and is not the selection
  criterion; the selecting evidence is the ISO's own meter (§1), a published reporting gap (§2), and
  a class-membership identity at the unit layer (§3). §3 reports R2's adverse rows at full magnitude.
* **Rule 13 / 14 `[R-MEASURED]` / `[R-ACCURATE]`** — both repairs prefer the accurate measurement
  over a silently-truncated one. R1's scaling ratio is measured from the same plant in the same year;
  R2 is rule 14's misalignment case (a benchmark class defined on a *fuel* boundary against a model
  class defined on a *unit* boundary), remedied with the reconciled version rather than a guess.
* **Rule 21 `[R-DOF]`** — **zero free parameters**; no literal, threshold or share introduced. The
  existing `_CAMPD_BACKFILL_MIN_MWH` deadband is untouched and its firing test is unchanged.
* **Rule 25 `[R-ISO-SCOPE]`** — §5 is the census that makes the shared edit judgeable, and it was run
  **before** anything was landed. No verdict transfers between ISOs and no ISO's number was fitted.
* **Rule 28 `[R-MECH-MATRIX]`** — the §5.5 lever queue and `mechanism-matrix/NYISO.js` were read
  before anything was proposed. **No cell moves.** The DO-NOT-REDO set was honoured: the Central-East
  seam, `nyiso_total_east_cutset_ttc`, the hourly-TTC grain, the West export outlet, the firm-import
  floor, the hydro equality floor, the hydro period lengths, `nyiso_ct_peaker_bands_measured` (R) and
  `nuclear_unit_availability` (K) are **untouched and not re-tested**. §1 *withdraws* the handoff's
  dual-fuel-deliverability lead on evidence rather than re-testing `dual_fuel_switching` (K).
* **Rule 29 `[R-SCREEN]`** — clause (0) zero-LP phase 0 answered the question outright; no screen was
  owed and none was spent.
* **Rule 31 `[R-RETAIN]` / 32 `[R-SHARD]` / 33 `[R-SHARD-ARCHIVE]`** — the parent ran no LP and
  launched no shard, so there is nothing to archive. The four retrieved legs are **gitignored, not
  deleted**, and their full-SHA recovery lines at `.gitignore:2400` are **re-verified working**.
* **Rule 15 `[R-DASHBOARD]`** — no run was produced, so no registration is owed and the keeper's
  dashboard entry is untouched.

### Reported, not fixed — all pre-existing and none NYISO's

* **`tests/scoring` carries 20 failures on clean `main`** (`test_audit_keepers_lineage`,
  `test_golden_manifest_provenance`, `test_forecast_parity`, `test_gate_a_provenance`,
  `test_replay_keeper_strict`). This session changed no code, so it adds none. **Nobody owns this.**
* **34 of 44 committed bench parts are STALE at HEAD** (§5) — ERCOT, NEISO, PJM, SOCO, SPP and
  several MISO years. Each is its own lane's to regenerate; NYISO's four are fresh.
* **Class-E parity**: `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` remain pre-existing
  unmapped REDs and are not NYISO's. This session's four retrieved leg dirs will also appear in that
  list locally — expected, and exactly the corrected rule-31 clause (the gate walks the
  **filesystem**; CI checks out only what is committed and stays green).
* **NEISO's §5.x matrix prose header still does not name its designated keeper** — that lane's
  rule-28 duty, still owed.
* **`dashboard_add_run.py`'s docstring still describes `enforce_registration_marker_gate`**, removed
  with `[R-HOLDOUT]` on 2026-09-09. Harmless but stale.
* **The G2 hydro energy loss** (−55.2 / −25.5 GWh in 2022 / 2023) carries over **unchanged as a
  LEDGERED OPEN ROOT-CAUSE ISSUE** (rule 21), not an accepted limitation. Untouched here.
* **C3c** (7 / 0 / 0 / 3 h > $300 against 101 / 10 / 13 / 42) stays the ledgered, non-downgrading
  energy-only-LMP model-class limitation. Not this session's object.
