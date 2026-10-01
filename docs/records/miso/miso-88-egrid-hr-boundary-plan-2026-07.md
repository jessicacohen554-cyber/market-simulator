# miso-88 — the eGRID heat-rate boundary contamination lane (charter)

**Date:** 2026-07-25. **Branch:** `claude/miso-88-egrid-hr-boundary-3xk7qp`.
**Lane:** LANE 1 of the miso-87 handoff — "fix the two C1 per-plant input
defects at their source and re-solve". **Keeper at charter time:**
`2026-07-24-miso-86-netrev-margin`, determination **NOT-YET** (FAIL C1
fuel-mix 2023 `CC_REGULAR` −8.62 TWh vs ±8.0; FAIL C3b shape 2025 NRMSE
0.204 vs veto ≤0.20).

Everything below was recomputed this session from the committed on-disk
sources (`data/raw/fleet-egrid/egrid2023_data_rev2.xlsx`,
`data/raw/eia-860/…`, `data/raw/campd-unit-level/…`) plus the registered
miso-86 bundle. Nothing is fit to a residual (rules 1/10/11). No year outside
2023–2025 was touched (rule 22 — MISO has no calibration-complete marker).

---

## 1. The charter revises the handoff on three points

The miso-87 handoff chartered this lane as: find the mystery CAMPD source
behind `bin_assignments_MISO.csv`, re-derive that table, and add two symmetric
guards (a below-nameplate capacity guard and a heat-rate plausibility guard).
Three of those premises do not survive verification.

**(a) `bin_assignments_MISO.csv` is an EXPORT, not a solve input.** It is
written by `scripts/export_iso_bin_assignments.py` as "a committed, reviewable
artifact". The only column any solve path reads is `Mixed_Facility`
(`data/fleet/campd_bins.py::ct_intermediate_plants`, for the multi-technology
CT exclusion). `Plant_Avg_HR_MMBtu_MWh` and `Nameplate_MW` are **written, never
read**. Re-deriving that table would not change a single LP coefficient. The
live values come from `eia860_generators.parquet` via
`fleet/eia860.py::load_fleet_from_csv` → `_rows_to_generators`.

**(b) There is no mystery CAMPD source.** Both plants are present in the
committed CAMPD extracts — `data/raw/campd-unit-level/WI_{2023,2024,2025}.parquet`
carries facility 55641 (35,040 rows = 4 units × 8760) and `TX_*.parquet`
carries 55358. The handoff's "appears in NO parquet" was a search miss. And the
"impossible" CAMPD series for Riverside (7.989 TWh on a 674.9 MW plant, CF 1.35)
is not corrupt: CEMS facility 55641 **covers two EIA plants** (§2).

**(c) Defect 2 (Cottonwood 55358) is NOT LIVE — it is already fixed.** The
`carry_operating_mothballs` channel (`load_mothballed_but_operating`, the
2026-07-16 Cottonwood lane, `docs/handoffs/miso-cc-vintage-undercarry-plan-2026-07.md`)
is **`True` in the miso-86 keeper's `run_config.json`**. Verified against the
live fleet:

| solve year | 55358 base | + mothball re-carry | total carried |
|---|---|---|---|
| 2023 | 580.4 MW | **+572.6 MW** | **1153.0 MW** |
| 2024 | 580.4 MW | **+568.7 MW** | **1149.1 MW** |
| 2025 | 580.4 MW | +0.0 MW | 580.4 MW |

The full plant is already carried in 2023 and 2024. Only 2025 under-carries,
and that is the **documented, owner-defaulted accepted gap** (charter §10 of the
undercarry plan: no `vintage_2025/` exists because the canonical snapshot *is*
the 2025 Early Release, so the vintage-status oracle has nothing to read).
miso-87's "ratio 0.405" came from reading the export table — which is built
with no `year` argument, so the re-carry never applies to it — and additionally
compared net-summer-of-OP (580.4) against nameplate-of-all-8 (1433.6), two
different bases. The like-for-like figure is 580.4 vs net-summer-of-all-8
(1156.6).

**Consequence: no below-nameplate capacity guard is added by this lane.** The
defect it was meant to catch does not exist, and such a guard would be actively
harmful — it would inflate capacity for units that are *genuinely* mothballed,
which is precisely the judgment the vintage-status oracle exists to make on
measured evidence.

---

## 2. Defect 1 (LIVE) — eGRID double-counts West Riverside's heat input

`eia860_generators.parquet` carries `heat_rate = 14.963746` for all three
generators of **Riverside Energy Center (EIA plant 55641**, Beloit WI, MISO-East,
3 × NGCC, in service 2004, 534.8 MW net summer). Sourced verbatim from eGRID
PLNT23 `PLHTRT` by `scripts/data/process_eia860.py::_join_egrid_heat_rate`.

Against its own class it is not a heat rate of anything: the other 237 operable
MISO CC generator rows run min 4.49 / median 7.31 / p75 7.64. At ~$3/MMBtu it
prices Riverside near **$45/MWh** against ~$20/MWh for comparable MISO CCs —
above most of the MISO coal fleet — so the LP declines to commit it: model CF
**0.01 / 0.05 / 0.01** against actual **0.60 / 0.57 / 0.56**, a 3-year
**−9.87 TWh**. Availability is not the cause (its CAMPD unit-outage derate has
mean availability 0.687 in 2023).

**Root cause, provable inside eGRID's own two rows.** A second plant,
**West Riverside Energy Center (EIA plant 64020**, 3 × NGCC + PV, in service
2020, 684.2 MW net summer), sits **454 m away** on the same site. CEMS reports
**both blocks under one facilityId, 55641**. eGRID PLNT23:

| | ORISPL | NAMEPCAP | CAPFAC | PLHTIAN (MMBtu) | PLNGENAN (MWh) | PLHTRT |
|---|---|---|---|---|---|---|
| Riverside | 55641 | 674.9 | 0.599 | **53,017,211** | 3,543,044 | **14,963.7** |
| West Riverside | 64020 | 727.6 | 0.668 | 28,265,611 | 4,259,326 | 6,644.9 |

The numerator and denominator are drawn on **different boundaries**:
`PLHTIAN` = 53,017,211 is the **whole CEMS facility** (byte-identical to the sum
of `heatInput` over all four units of facility 55641 in `WI_2023.parquet`:
53,017,211), while `PLNGENAN` = 3,543,044 covers **only the 674.9 MW EIA plant**
(confirmed by eGRID's own `CAPFAC` × `NAMEPCAP` × 8760 = 3.543 TWh). West
Riverside's heat input is counted **twice** — once inside 55641's total, and
again as 64020's own.

eGRID's unit sheet UNT23 states it outright:

| ORISPL | UNITID | HTIAN | UNTYRONL | HTIANSRC |
|---|---|---|---|---|
| 55641 | CT-01 | 12,294,400 | **2004** | EPA/CAPD |
| 55641 | CT-02 | 12,081,859 | **2004** | EPA/CAPD |
| 55641 | CT-03 | 13,597,198 | **2019** | EPA/CAPD |
| 55641 | CT-04 | 15,043,754 | **2019** | EPA/CAPD |
| 64020 | CTG3 | 13,404,362 | — | EIA Unit-level Data |
| 64020 | CTG4 | 14,861,249 | — | EIA Unit-level Data |

Plant 55641 has **no generator of 2019/2020 vintage** — all three EIA-860 rows
are 2004. CT-03/CT-04 are West Riverside's machines, and 64020 reports the same
two units independently from a different source. eGRID also flags the mismatch
in its own metadata: 55641 carries `NUMUNT = 4` CEMS units against
`NUMGEN = 3` EIA generators.

**The boundary-consistent value.** Riverside's own units are CT-01 + CT-02 =
**24,376,259 MMBtu**; against its own `PLNGENAN` of 3,543,044 MWh that is
**6.880 MMBtu/MWh** — a slightly-better-than-median 2004 F-class CC, exactly as
expected. Cross-validated three independent ways:

* sibling subtraction: (53,017,211 − 28,265,611) / 3,543,044 = **6.986**
* CEMS unit-level, gross basis, CT-01+CT-02 only: **6.624 / 6.642 / 6.646** for 2023/24/25
* CEMS unit-level, gross basis, CT-03+CT-04 (the West block): **6.647 / 6.678 / 6.768** — and eGRID's own independent `PLHTRT` for 64020 is **6.645**

All four agree at ~6.6–7.0. The 14.96 is arithmetic on mismatched boundaries,
nothing more.

**Rule posture.** This is the exact case rule 11 names as its legitimate
exception — "the data is defined on a different boundary than our
representation" — and the remedy rule 11 prescribes is to "prefer a
*reconciled* version of the real data over a pure guess". No appeal is made to
any model output, price residual or volume residual (rules 1/10 not engaged).
The correction is measured, cited, and regenerates from source.

---

## 3. Scope — one plant in six ISOs, established before writing the fix

Raw envelope screening (eGRID `PLHTRT` above the technology's physical band,
plants ≥200 MW) flags 19 plants / 10.7 GW across all six ISOs — but that test
over-selects badly: most flags are **low-utilisation idle-heat artifacts**
(Goose Creek CF 0.0001 → HR 102.6; Calumet CF 0.0008 → 20.6; Eddystone CF
0.0035 → 16.7), which are real measured inefficiency at near-zero output, not
contamination. Adding a utilisation discriminator (`CAPFAC ≥ 0.25`, so idle heat
cannot explain the value) leaves 5 plants, of which Riverside is the only one
materially over its band (**1.58×**; the other four are 1.01–1.09×).

A **general** vintage-attribution repair was designed, sized, and **refused**:
dropping every UNT23 unit whose commissioning vintage matches no EIA-860
generator at that plant touches **47 plants and damages 25 of them badly**
(French Island → HR 0.011, Ivanpah 3 → 0.873, V H Braunig → 0.502). The reason
is structural — EIA-860's operable snapshot omits retired units that CEMS still
reports, so removing their heat input guts the numerator while `PLNGENAN`
remains the whole-plant total. **That rule is not shipped.**

---

## 4. The fix — a self-validating double-count reconciliation, zero tuned parameters

Applied in the fleet loader (`fleet/eia860.py`), which is the single seam every
read path passes through (`load_fleet_from_csv`, the vintage reads, and
`load_mothballed_but_operating` all call `_rows_to_generators`). The curation
script keeps writing eGRID's value verbatim — raw curation stays faithful to
source; the model applies a documented, source-derived reconciliation. (The
curation script cannot be re-run here in any case: its `eia8602024.zip` input
is not committed.)

A plant's eGRID heat rate is replaced **only when all four hold**:

1. **The value is physically impossible for a combined cycle** — `PLHTRT`
   exceeds `HEAT_RATE_BINS["gas_ct"]["older"]` (11.5 MMBtu/MWh). A combined
   cycle recovers exhaust heat from its own topping turbine, so its plant heat
   rate cannot exceed that of a *bare simple-cycle GT of the same era*. This is
   a physics bound read off an existing cited constant, **not** a fitted
   multiple of the class mean. Scoped to `gas_cc` only, the one class where the
   bound is airtight.
2. **A co-located sibling independently reports its own heat input** — another
   eGRID plant within `EGRID_COLOCATION_RADIUS_KM` (1.0 km, site identity) with
   `PLHTIAN > 0`.
3. **The plant carries UNT23 units that belong to that sibling** — commissioning
   vintage within `EGRID_UNIT_VINTAGE_TOL_YEARS` (1 yr, the standard CEMS
   commissioning vs EIA in-service offset) of a sibling EIA-860 generator
   vintage and of **none** of its own; excluding them must leave ≥1 unit with
   positive heat input.
4. **The repair resolves the impossibility** — the recomputed rate must land at
   or below the same ceiling. Self-validating: the correction is accepted only
   because it moves an impossible value into the physical band.

**Selectivity, verified across all six ISOs: exactly one plant — 55641,
14.964 → 6.880.** Condition 4 is what makes it safe; without it the detector
also fires on Devon 544 (876.6 → 340.1, garbage either way and already dropped
by the pre-existing 3,000–30,000 Btu/kWh window) and King City 10294
(7.855 → 8.998, a *degradation* of an already-plausible value). Both are
correctly rejected — Devon by condition 4, King City by condition 1.

**Forward story (rule 13/23).** The quantity is a measured plant heat rate from
the current eGRID vintage, recomputed from that vintage's own unit rows. It
regenerates for any future eGRID release and responds to changed conditions: if
EPA/EIA fix the 55641 attribution in a later eGRID, condition 1 stops firing and
the reconciliation becomes a no-op automatically. Zero free parameters — the
output value 6.880 is arithmetic on eGRID fields, never chosen.

---

## 5. Pre-registered expectation (recorded BEFORE solving)

Restoring 534.8 MW of CC from ~$45/MWh to ~$20/MWh puts it back in the merit
order below coal. Therefore:

* **C1 fuel-mix should improve.** Riverside's 2023 gap is −3.51 TWh of the
  −8.62 TWh `CC_REGULAR` miss. Expect C1-2023 to move to roughly **−5.1 TWh**,
  inside the ±8.0 band → **C1 expected to PASS**. Displacement lands mostly on
  COAL_PRB, so watch the coal rows against their own bands.
* **C3b-2025 is expected to get WORSE, and that is accepted.** Adding cheap CC
  to the merit order pushes prices **down**, and C3b-2025 already fails as a
  low-price miss (−16.2% level, summer body ~$11–13/MWh short). The two
  crossings are **not jointly closable by this fix**. Per rule 1 the accurate
  input **stays in** whatever the determination does; per rule 11 a worse C3b is
  the discovered-bug signal, to be root-caused in its own lane (the miso-87
  LANE-2 summer-body charter), **never** offset with anything tuned.
* **Determination may remain NOT-YET.** That is an acceptable outcome for this
  lane. The deliverable is a structurally-correct input, registered and scored
  honestly — not a better headline.
* **Blast radius must be exactly one plant.** Verified by diffing the built
  fleet before and after; any second plant changing is a stop-the-line event.

## 6. Validation plan

1. Unit tests on the reconciliation: fires on 55641; no-ops on King City and
   Devon; no-ops when the sibling is absent; no-ops on a plausible input.
2. Fleet-build diff, all six ISOs: only 55641's `heat_rate` changes.
3. Solve **2023 + 2024 + 2025 in ONE bundle** (rule 16), **fresh — no
   `--reuse-solved`**, since an input changed and every year's LP moves.
4. Register (rule 15), run `legitimacy_diagnostics.py`, build the attestation,
   score with `calibration_verdict.py`, report the determination whatever it is.
5. Leave-one-year-out within 2023–2025 before any keeper promotion (rule 22).
