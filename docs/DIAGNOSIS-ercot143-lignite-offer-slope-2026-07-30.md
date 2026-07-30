# DIAGNOSIS — ERCOT-143 Phase 2: the lignite mid-band offer SLOPE does not exist — LANE CLOSED

**Date** 2026-07-30 · **ISO** ERCOT · **Lane** ercot143-lignite-offer-slope ·
**Phase 2 — NO LP built, NO year solved, NO parameter changed** ·
**Keeper under test** `2026-07-30-ercot140-coal-peak-offer`
(bundle `results/calibration/ercot140_coal_peak_arm`) — **UNCHANGED** ·
**Chartered by** `docs/DIAGNOSIS-ercot142-lignite-shape-2026-07-30.md` §8 ·
**Queue item** `docs/mechanism-testing-matrix.md` §5.1 #3 ·
**Reproduce** `scripts/probes/ercot143_lignite_offer_slope.py`

---

## 0. Result in one paragraph

The chartered mechanism has **no measured object behind it**, and the lane
closes without spending a solve — the outcome ERCOT-142 §8.2 pre-registered
("if no non-fitted identification survives, the lane closes"). Measured
**per plant** instead of fleet-pooled, Oak Grove — the single plant carrying the
entire C7 miss — submits a **near-horizontal** SCED offer curve: unit 1 runs
`(0 MW @ $9.28) → (880 MW @ $9.64)`, a **$0.36** spread across its whole range;
unit 2 `$8.19 → $9.35`. **98.2 % of its capability is offered at or below $10.**
The model's Oak Grove curve spans **$13.14 → $38.94** (2023, spread $25.80,
cap-weighted $16.10). The model's lignite is therefore already **22–72× steeper**
(against the plant's own $1.16 / $0.36 spreads) and **$4–7/MWh dearer**, so the
charter's premise — that the model's lignite *lacks* mid-band slope — is
**backwards for the plant that carries the defect**. The fleet's "35.7 pp between
$17.5 and $25" is not within-plant slope at all: it is **cross-plant level
dispersion** of flat curves stacked at different heights (Oak Grove $9, Major Oak
$14.7, Martin Lake $22.2, San Miguel headroom $42–53), an object the model already
carries through per-plant fuel and heat rate and which ERCOT-137/138/140 already
calibrated on LEVEL. Two further findings close the door independently: the
identifying corpus **cannot see the defect window** (h0–h8 is 8.4 % of it, all from
the one year with no measured turndown, and no 2023 SCED disclosure exists), and in
the full-24-h DAM disclosure Oak Grove submits **no energy curve and holds no AS
award in any of 2023/2024/2025** — so its overnight backdown is not carried by a
priced energy offer in either market. **No mechanism promoted, no solve spent,
keeper unchanged.**

---

## 1. Step 1 (charter §8.1) — the re-measurement, and a correction to ERCOT-142 §6

ERCOT-142 §6 quoted Oak Grove's curve from the **ercot135-vintage** artifact and
flagged it as structure-only. Re-captured at the live LP seam
(`apply_coal_tranches`) on the **current ercot140 keeper**:

| year | plant | tranche ladder (share @ hour-mean bid) | spread |
|---|---|---|---|
| 2023 | **Oak Grove** | mustrun 45 %@\$13.14 \| committed 10 %@\$13.97 \| econhi 18 %@\$16.48 \| econlo 22 %@\$17.59 \| **peak 5 %@\$38.94** | \$25.80 |
| 2024 | Oak Grove | 45 %@\$13.14 \| 10 %@\$13.34 \| 18 %@\$15.69 \| 22 %@\$16.72 \| **5 %@\$34.84** | \$21.70 |
| 2025 | Oak Grove | 45 %@\$13.14 \| 10 %@\$15.01 \| 18 %@\$17.79 \| 22 %@\$19.02 \| **5 %@\$45.43** | \$32.29 |
| 2023 | Major Oak | 45 %@\$12.95 \| 10 %@\$14.64 \| 18 %@\$17.33 \| 22 %@\$18.52 \| 5 %@\$38.94 | \$25.99 |
| 2023 | San Miguel | 10 %@\$31.60 \| 55 %@\$35.39 \| 13 %@\$38.78 \| 5 %@\$38.94 \| 17 %@\$41.95 | \$10.35 |

**The ERCOT-142 §6 statement is superseded and must not be re-quoted.** "Oak
Grove's *entire* modelled offer curve tops at \$21.19, *below* the \$24.34
overnight price, so every MW is inframarginal" was true at ercot135 vintage. On
the current keeper the top is **\$38.94** (2023) — ERCOT-140's `_peak` tranche
already lifted it *above* the overnight price. What remains true is the weaker
claim: the top tranche is only **5 %** of the plant (89.8 MW), and the other
95 % is offered by \$17.59. The re-measurement narrows the alleged defect from
"the whole plant" to "the top 5 % is the only price-responsive part".

## 2. Step 2 (charter §8.2) — the identification, tested PER PLANT, and refuted

The charter directed the slope to be identified from `B2_supply_grid`. That
artifact is **fleet-pooled**. Resolved per resource on ERCOT-136 `section_b`'s
verbatim B2 construction (floored convention, share of HASL, all four subsets
pooled):

| resource | ≤\$0 | ≤\$10 | ≤\$17.5 | ≤\$20 | ≤\$25 | **pp[17.5, 25]** |
|---|---|---|---|---|---|---|
| **Oak Grove U1** | 0.592 | **0.983** | 0.983 | 0.999 | 0.999 | **0.016** |
| **Oak Grove U2** | 0.594 | **0.982** | 0.982 | 1.000 | 1.000 | **0.018** |
| **Major Oak 1** | 0.516 | 0.516 | 0.953 | 0.953 | 0.954 | **0.001** |
| **Major Oak 2** | 0.516 | 0.516 | 0.960 | 0.960 | 0.960 | **0.000** |
| **San Miguel** | 0.602 | 0.602 | 0.615 | 0.621 | 0.783 | 0.168 |
| Martin Lake 1 | 0.457 | 0.457 | 0.457 | 0.457 | 0.993 | 0.535 |
| Limestone 1 | 0.523 | 0.523 | 0.541 | 0.565 | 0.996 | 0.455 |
| W A Parish 5 | 0.419 | 0.419 | 0.440 | 0.520 | 0.979 | 0.539 |
| COAL FLEET | 0.450 | 0.506 | 0.603 | 0.671 | 0.916 | 0.313 |

**The charter's cited segment belongs to other plants.** The fleet's 31.3 pp
between \$17.5 and \$25 is carried by Martin Lake (0.535), Parish (0.539) and
Limestone (0.455). The three lignite plants contribute **0.016 / 0.018 / 0.001 /
0.000 / 0.168** — Oak Grove and Major Oak, which are 84 % of the class, are
essentially absent from it. Transferring the fleet segment onto the lignite
class is a fleet-to-plant transfer that the per-plant data refutes for exactly
the plants that carry the C7 cell.

**And the segment is not slope.** The submitted curves themselves, modal points
verbatim from the disclosure:

```
Oak Grove U1   (0MW @ $9.28) (317 @ $9.32) (408 @ $9.33) (493 @ $9.36)
               (575 @ $9.43) (658 @ $9.50) (743 @ $9.57) (880 @ $9.64)
Oak Grove U2   (0MW @ $8.19) … (880 @ $9.35)
Major Oak      (80MW @ $14.73) … (155 @ $14.74)
Martin Lake 1  (0MW @ $22.19) … (825 @ $22.26)
San Miguel     (0MW @ -$250) (220 @ -$249) (221 @ $42) (396 @ $43)
W A Parish 5   (156MW @ $20.01) (274 @ $20.59) … (667 @ $24.76)
```

Every ERCOT coal plant but Parish submits a **near-horizontal** curve; the plants
sit at different *heights*. The fleet aggregate rises smoothly only because flat
curves are stacked at different levels. **There is no within-plant mid-band slope
in the measured data to identify** — the measured object is cross-plant level
dispersion, which the model already represents through per-plant delivered fuel
and heat rate, and which ERCOT-137 (bottom), ERCOT-138 (crossing band) and
ERCOT-140 (top) already calibrated on LEVEL.

Model vs measured, the two curves side by side (Oak Grove, 2023):

| | bottom | cap-weighted | top | spread |
|---|---|---|---|---|
| **model** (ercot140 keeper) | \$13.14 | \$16.10 | \$38.94 | **\$25.80** |
| **measured** (own SCED TPO) | \$8.19 | ≈\$9.2 | \$9.64 | **\$0.36 / \$1.16** |

**The direction, stated without a solve.** The rule-14 `[R-ACCURATE]`-faithful
version of this mechanism — repricing each plant onto its *own* measured curve —
would move Oak Grove from (\$13.14 … \$38.94, spread \$25.80) to
(\$8.19 … \$9.64, spread ~\$1): **lower and flatter**, hence *strictly more*
inframarginal in every overnight hour and with *less* internal structure to back
down on. It cannot improve C7 and would very likely worsen it. So the **only**
version of the chartered mechanism that could clear C7 is the fleet-transfer
version that per-plant measurement refutes — which is rule 1 `[R-STRUCT]`'s
forbidden move ("never reach the right number through a mechanism that isn't
real") and rule 13 `[R-MEASURED]`'s (an input rescaled so the model's *output*
lands on the actuals). **Adopting it is refused.**

## 3. The corpus cannot see the defect window

Hour-of-day coverage of the identifying SCED corpus (COAL resource-intervals):

| subset | hours covered | rows |
|---|---|---|
| 2024_ercot74_tail_days | **h11–h22 only** | 23,021 |
| 2024_ercot75_control_days | **h11–h22 only** | 20,807 |
| 2025_ercot75_control_days | **h11–h22 only** | 19,265 |
| 2025_ercot86_tail_days | all 24 h | 18,113 |

Pooled, **h0–h8 is 8.44 %** of the corpus (6,853 of 81,206) and **100 % of it
comes from the single 2025-tail subset** — the year whose measured plant does not
cycle at all (ERCOT-142 §5: fall day-minus-night CF gap **−0.008**). There is no
2023 SCED disclosure on disk, and **2023 is the failing year**. Even had the
per-plant reading gone the other way, this instrument could not identify an
overnight-shape parameter: rule 14's own exception clause ("the data is defined
on a different time aggregation … so using it literally would make results less
reflective of reality") applies squarely.

## 4. The full-coverage instrument, and the successor hypothesis refuted in advance

The 60-Day **DAM** disclosure (`QSE submitted Curve-MW/Price1..10` + AS awards)
does carry full 24-h, full-year, **2023-inclusive** coverage. It closes the
question rather than reopening it:

| plant | year | resource-hours (online) | DAM curve present | AS award share | AS_up mean |
|---|---|---|---|---|---|
| **Oak Grove** (both units) | 2023 / 2024 / 2025 | 7,151–8,079 each | **0.000** | **0.000** | **0.0 MW** |
| **Major Oak** (both units) | 2023 / 2024 / 2025 | 7,249–8,312 each | **0.000** | **0.000** | **0.0 MW** |
| **San Miguel** | 2023 / 2024 / 2025 | 5,595–5,995 | 0.000 (0.049 in 2024) | 0.000 | 0.0 MW |
| Martin Lake 1 | 2023 / 2024 / 2025 | 649–8,032 | 0.838 / 0.975 / 0.963 | 0.34 / 0.43 / 0.27 | ~3 MW |
| Limestone 1 | 2023 / 2024 / 2025 | 6,118–7,154 | 0.000 | 0.37 / 0.57 / 0.05 | 18.5 / 24.3 / 1.6 |
| W A Parish 5 | 2023 / 2024 / 2025 | 5,952–8,021 | 0.000 | 0.39 / 0.42 / 0.04 | 17.9 / 12.6 / 0.7 |

Oak Grove submits **no** DAM energy curve and holds **no** AS award in any of the
three years. This also **refutes in advance the successor a next session would
naturally reach for**: a measured ancillary-service power reservation is the one
mechanism rule 13 `[R-MEASURED]` explicitly names as admissible, and Limestone
and Parish do carry real AS awards — but the lignite plants carry **zero**. An
AS-reservation mechanism cannot back Oak Grove down because Oak Grove sells no AS.

## 5. What the defect actually is — stated honestly, not chartered as a lever

The real Oak Grove offers ~\$9 and the overnight price is ~\$19–24, yet it sits
at **808 MW** — which is its **telemetered LSL** (measured LSL/HSL 0.49–0.72 per
unit; 808 MW is also exactly `COAL_MUSTRUN_BY_PLANT[6180] = 45.0`, the constant
ERCOT-142 §3(a) already verified as correct). A resource offered below the
clearing price that is nonetheless dispatched to its LSL is **not being cleared
on its energy offer**. The remaining candidates are therefore *outside* the offer
surface entirely: intra-zonal network/congestion binding on a North-zone
resource, or QSE self-scheduling / telemetered self-derate. Both are recorded as
**observations, not as a chartered lane**:

* An **intra-zonal** North constraint is not representable in a 7-zone reduced
  network — and ERCOT-117 **CLOSED** the topology-split family (do not re-open
  it as a topology change; CLAUDE.md and ERCOT-142 §9 both carry that closure).
* A **self-schedule/telemetry** driver has no forward analogue that responds to
  changed conditions, so importing the measured pattern would fail rule 13's
  admissibility test outright — it would be pinning the unit to observed conduct,
  which is the named forbidden move.

**No successor is chartered from this lane.** C7's ERCOT cell is left failing at
`2023 COAL_LIGNITE profile r 0.769 < 0.80`, 0.031 short, with its cause now
identified as a non-offer-curve driver that the current market representation
cannot legitimately carry.

## 6. Verdict and governance

**LANE CLOSED. No mechanism promoted, no `ScenarioConfig` field added, no solve
spent, keeper UNCHANGED (`2026-07-30-ercot140-coal-peak-offer`).** The ERCOT fail
set is unchanged at **{C3a, C3b, C3c, C7}**; C6 remains **UNATTESTED** (8
residual-identified DOF entries — not attested to buy a determination).

* **No precommit was pushed** because no solve was run; the charter's §8.4/§8.5
  obligations (hard kill, guards, `_CACHE_KEY_OPTIONAL_FIELDS`, six wiring seams,
  matrix row) are all conditional on an arm that does not exist.
* **No dashboard run registered** — no run was produced. Precedent:
  ERCOT-117 / ERCOT-130 / ERCOT-142 / miso-107 / caiso-140 (rule 15 governs runs).
* **Holdouts (rule 22 `[R-HOLDOUT]`)** — 2023/2024/2025 only. No 2022, 2019,
  ≤2021 or H1-2026 data was solved, scored or read; the on-disk `*_2026_*` DAM
  files were never opened (the probe enumerates `YEARS = (2023, 2024, 2025)`).
* **ERCOT-scoped (rule 25 `[R-ISO-SCOPE]`)** — no other ISO's files touched. The
  pjm-141 parallel ("PJM's overnight defect is a flat offer stack") is noted in
  the matrix as context only; no parameter or verdict crosses.
* **Rules 13/14 `[R-MEASURED]`/`[R-ACCURATE]`** — all measured conduct read as
  driver evidence and diagnosis. Nothing fed back as an answer key; no offer
  curve, sigmoid, derive value or measured parameter changed (rules 21/23
  `[R-FROZEN-DERIVE]`).
* **Rule 19 `[R-ONE-MECH]`** — no mechanism added, so nothing stacked. The
  enumeration of what prices the lignite mid-band today stands as ERCOT-142 §3
  recorded it: `_mustrun` = ERCOT-137 measured margin, `_committed`/`_econ*` =
  band HR multipliers × the lignite supply sigmoid, `_peak` = ERCOT-140 measured
  gas-parity level.
* **Matrix (rule 26 `[R-MECH-MATRIX]`)** — the `coal_min_load_floor` row's ERCOT
  cell carries this adjudication (the coal dispatch-band family's row, as
  ERCOT-142 §9 established); §5.1 queue item 3 is closed with this result. No new
  `ScenarioConfig` field, so rule 26(c) is n/a.
* **CLOSED, not re-opened** — everything ERCOT-142 §9 lists, plus, now: the coal
  **offer-curve** family end-to-end for C7 (this lane), and the AS-reservation
  successor (§4). P2 remains ARCHIVED and unused.

**Preconditions verified this session** (not assumed): `ScenarioConfig().cache_key()`
= `603c2498bf71d21d` (matches; the `nyiso_import_sil_retire` registration has
landed on `main` and that ERCOT-142 open ruling is CLOSED), `audit_keepers.py`
**PASS — 0 failures, 0 warnings** (the NEISO `status/NEISO.js` staleness the
handoff flagged as pre-existing has since been fixed in NEISO's own lane; recorded,
not touched), and the ERCOT-142 basis check reproduces D-1 **0.769 / 0.973 /
0.964 exactly**.

## 7. Open owner rulings carried forward (surfaced, not decided)

1. **Carried from ERCOT-137/138/139/141/142, still open:** delete outright vs
   leave inert the retired `coal_tranche_1_fuel_passthrough` pricing path and the
   legacy non-CAMPD `split_coal_tranches` `_t1/_t2/_t3` path (rule 26
   `[R-DELETE]`).
2. **Carried from ERCOT-138 §7.2, still open:** `ercot_offer_hrmult_ep_rebasis`
   and `_bands` are solve-affecting `ScenarioConfig` fields with **no
   mechanism-matrix row** — a rule-26(c) gap now predating seven lanes.
3. **NEW, surfaced by this lane:** the model's `COAL_LIGNITE` class holds Oak
   Grove / San Miguel / Major Oak, while **Martin Lake** (EIA 6146) — a
   lignite-burning plant in reality — is classed elsewhere. This is a
   pre-existing taxonomy question, immaterial to this closure (it would move a
   plant *into* the class whose measured curve sits at \$22.2, not one that
   changes the finding), and is **not** touched here. Recorded so a future
   class-composition lane can weigh it deliberately rather than discover it.
