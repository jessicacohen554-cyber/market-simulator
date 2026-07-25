# FINDING (miso-87, 2026-07-24) — the MISO keeper's C1 CC_REGULAR FAIL is two per-plant input defects, not an offer-curve, tranche-split or availability miss

**Context.** `2026-07-24-miso-86-netrev-margin` (bundle
`results/calibration/miso86_netrev_margin`) is the MISO keeper, determination
**NOT-YET** on two crossings. This finding root-causes the first:
**C1 fuel-mix, 2023 `CC_REGULAR` −8.62 TWh** against a ±8.0 TWh band. No LP was
re-solved — everything below is read off the keeper's committed artifacts
(`hourly/` sidecars, run payload, `bench/MISO/*.json.gz`) plus the measured
source records. Reproduce with
`python scripts/probes/_miso87_c1_plant_defects.py`.

The miso-86 log entry attributed the crossing to the net-revenue margin form
("the below-anchor firming sheds ~0.86 TWh of CC dispatch"), and the handoff
asked whether the residual sits in the offer **bands**, the
**committed-vs-economic tranche split**, or **CC availability**. It is none of
the three. The margin form contributed the last 0.86 TWh of an
already-−7.8 TWh miss whose cause is upstream of the LP entirely.

## 1. The miss is per-plant, and two plants carry it

Model-minus-actual `CC_REGULAR` energy, plant-matched on both sides (the
scorecard compares the *same* plant codes: model LP dispatch vs EIA-923 net
generation less BTM host supply):

| plant (ORIS) | zone | MW | 2023 CFm/CFa | 2024 CFm/CFa | 2025 CFm/CFa | 3-yr ΔTWh |
|---|---|---|---|---|---|---|
| **Riverside Energy Center** (55641) | MISO-East | 675 | **0.01** / 0.60 | **0.05** / 0.57 | **0.01** / 0.56 | **−9.87** |
| **Cottonwood Energy Co LP** (55358) | MISO-South | 1434 | 0.32 / 0.47 | 0.27 / 0.48 | **0.05** / 0.37 | **−8.42** |
| Blue Water Energy Center (62192) | MISO-East | 1267 | 0.61 / 0.74 | 0.61 / 0.67 | 0.61 / 0.75 | −3.67 |
| Magnet Cove (55714) | MISO-South | 746 | 0.35 / 0.52 | 0.45 / 0.65 | 0.38 / 0.55 | −3.58 |
| Fox Energy Center (56031) | MISO-East | 619 | 0.39 / 0.80 | 0.65 / 0.82 | 0.58 / 0.66 | −3.57 |

The two worst plants are **−18.30 TWh over three years (−6.10 TWh/yr)** against
a ±8.0 TWh band. They are not a class-wide tilt: the rest of the MISO CC fleet
brackets the actuals in both directions (Montgomery County +4.07, Union Power
+3.97, Holland +2.61, Marshalltown +2.59 over the same three years), which is
exactly what an offer-band or tranche-split error would *not* look like.

Availability is ruled out directly: the CAMPD unit-outage derate gives Riverside
a **mean availability of 0.687** in 2023 (min 0.0, max 1.0), so the LP has the
plant offerable in roughly two-thirds of hours and declines to commit it. The
plant is priced out of merit, not derated out.

## 2. Defect 1 — Riverside Energy Center's derived heat rate is ~2× physical

`data/raw/_processed-legacy/bin_assignments_MISO.csv` carries
`Plant_Avg_HR_MMBtu_MWh = 14.964` for ORIS 55641. Reproduced in the solve fleet
(`build_base_fleet`, `plant_level_fleet=True`, `use_campd_bins=True`): 8
tranches, heat rates **13.77 → 15.68**.

Against the rest of the MISO `CC_REGULAR` fleet in the same table — min **6.25**,
median **7.41**, max **8.89** — and against the plant's own technology (EIA-860:
three NGCC generators, `CTG1`/`CTG2`/`STG1`, in service **2004**, 674.9 MW
total), 14.96 is not attainable by any combined-cycle configuration. At ~$3/MMBtu
gas it puts Riverside's marginal cost near **$45/MWh** while comparable MISO CCs
offer near **$20/MWh** — above most of the MISO coal fleet. Hence CF 0.01.

Only two other MISO CCs exceed a 9.0 MMBtu/MWh plausibility line and both are
trivial (L L Wilkins 49.5 MW, Hutchinson #2 51.0 MW). Riverside is the sole
material case.

## 3. Defect 2 — Cottonwood's derived capacity is 40 % of its nameplate

The same table carries `Nameplate_MW = 580.4` for ORIS 55358 against an EIA-860
operable nameplate of **1433.6 MW** (8 NGCC generators, `CT1`–`CT4` +
`ST1`–`ST4`, in service 2003). Ratio **0.405**. It is the **only** MISO CC above
400 MW whose derived bin capacity falls below 75 % of nameplate.

This one is self-refuting inside the model's own inputs, with no appeal to any
actual: **580.4 MW × 8760 h = 5.084 TWh/yr**, while the benchmark's CAMPD series
for the same plant records **5.866 TWh in 2023**. The model's measured input for
the plant exceeds what the model's capacity for that plant can physically
produce.

## 4. Why calling these defects is rule-safe

Neither claim appeals to the price or volume residual, so CLAUDE.md rules 1/10
are not engaged. Each is refuted by a measured record independent of the model
output: Riverside by its own EIA-860 technology and vintage plus the heat-rate
distribution of its own class; Cottonwood by EIA-860 nameplate *and* by the
internal contradiction in §3. **Rule 11 applies in the forward direction** —
these are estimates standing where accurate data exists, and the accurate data
should replace them regardless of what it does to the fit.

Note the expected direction is *against* the C3b crossing: restoring ~1.4 GW of
under-offered CC to the merit order should push prices **down**, while C3b-2025
is already a low-price miss (see the companion finding). The two crossings are
not jointly closable by this fix, and it should not be adopted on the
expectation that it improves the determination (rule 1).

## 5. The systemic gap — the capacity reconciler is one-sided

`cc_capacity_reconcile_<ISO>.csv` guards CC capacity in **one direction only**.
Its check fires when a plant's CAMPD-derived pmax *exceeds* the EIA-860 trusted
bound — seven MISO plants trip it on every fleet build (55467, 55620, 1403,
55218, 55220, 55380, 55418; 1.03 GW removed from 55380 alone) — and there is no
counterpart for capacity falling far *below* nameplate. Cottonwood at 40 % sails
through. There is **no plausibility guard on the derived heat rate at all**.

Both guards are pure data-quality checks against primary sources (EIA-860
nameplate; the physical heat-rate envelope of the technology class), not
residual-tuned parameters, so adding them is admissible under rule 23 — they
respond to source data, never to a fit.

## 6. What this finding does NOT establish

The *provenance* of the two bad values is still open. Neither ORIS 55641 nor
55358 appears in any `data/raw/campd-unit-level/*.parquet` extract in the repo,
yet both carry `Committed_Source = campd` / `Peaking_Source = campd` in the bin
table and both have a CAMPD series in the committed benchmark — Riverside's
being itself impossible (7.989 TWh on 674.9 MW = CF **1.35**). So the derive
script that wrote `bin_assignments_MISO.csv` read a CAMPD source this session
could not locate, and that source is where both errors originate. Auditing that
derive path — and re-deriving the table against it, citing the source-data
correction per rule 23 — is the next session's work, together with the two
symmetric guards in §5 and a full 2023–2025 re-solve.
