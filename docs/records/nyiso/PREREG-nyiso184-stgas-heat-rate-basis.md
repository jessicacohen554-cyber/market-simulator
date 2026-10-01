# PRE-REGISTRATION — nyiso-184 (`stgas-heat-rate-basis` lane): WHERE does Ravenswood's 9.50 come from, is Astoria the same object, and what is the zero-parameter repair?

**Session:** nyiso-184, NYISO backcast-calibration track, 2026-09-04.
**Branch:** `claude/nyiso-184-stgas-heat-rate-90z3qr`, fresh off `origin/main`
at `b168260e`.
**Keeper at entry:** `2026-09-02-nyiso-177-vintage-matched`
(`results/calibration/nyiso177_vintage_B1p`) — determination **NOT-YET**,
target grade 5, fail set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**.

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE FIRST GATE
MEASUREMENT.** Every bar, stop condition, admissible and forbidden repair form
below is fixed here. No gate statistic, no reconstruction, no footprint
enumeration and no solve output of this session's own making exists at the time
of writing. What DOES exist is a source-data trace (§0 item C) — the brief's
step 3 ("trace the join, from source data, never from a residual") — and it is
disclosed in full so a reader can judge what it could have contaminated.

---

## §0 — DISCLOSURE: every read held at writing time

### A. Inherited record

1. `docs/FINDING-nyiso183-ravenswood-availability-2026-09-03.md` — in full.
   Supplies: the availability route is REFUTED and DO-NOT-REDO (G1 separation
   +0.33 / +0.64 / +0.81, G3 `sel_fleet` 0.867 / 0.923); hypothesis B fires
   3/3 on the merit-position inversion (model rank 3 of 11, measured 8/8/6 of
   10); the G4d locator — model base **9.50** at Ravenswood (committed tranche
   9.975 ÷ 1.05 = peak 39.900 ÷ 4.20), CC_REGULAR base ≈ **8.80**, CAMPD
   steam-only measured **10.71**, eight-peer model ÷ measured cluster
   **1.596–1.749** (median 1.699 / 1.685 / 1.685), Ravenswood 1.382 / 1.417 /
   1.454, Astoria **3.365 / 3.419 / 3.464** at measured HR 5.39–5.55; the §8
   hypothesis (plant-grain eGRID `PLHTIAN`/`PLNGENAN`/`PLHTRT` join, facility
   blend 8.24) explicitly NOT adjudicated; the unexplained CC/ST base split
   (8.80 vs 9.50); the corrected keeper availability 0.786 / 0.478 / 0.309.
2. `results/calibration/PREREG-nyiso183-ravenswood-availability.md` — in full.
   Its §5 forbidden-form list (F1–F8) and §8 amendment (a mis-specified bar is
   recorded FAILED and re-anchored on HARDER evidence, never moved) are binding
   precedent here.
3. `docs/FINDING-nyiso177-availability-basis-root-cause-2026-09-02.md` §5.4 and
   §10.2 — the facility-summed-denominator defect family repaired on the OUTAGE
   (`_resolve_unit_group`) and TRANCHE (`_fleet_nameplate_and_group`) paths;
   the four integrity gains a promotion rests on (accuracy, no off-registry
   channel, reproducibility, internal consistency).
4. `docs/FINDING-nyiso181b-stgas-floor-overgeneration-2026-09-03.md` §5 and §12
   — Ravenswood +5.472 / +2.787 / +1.618 TWh over its meter, economic not
   forced; the other ten plants −5.197 / −6.776 / −7.957 TWh economically short;
   the DO-NOT-REDO list (floor deletion/narrowing, volume-buying levers); the
   D-2 / C8 grain under-count (escalated, scorer lane, not mine).
5. `docs/mechanism-testing-matrix.md` §5.5 (the NYISO header and the nyiso-183
   lever queue; top of queue = this object).
6. `docs/codebase-site/data/mechanism-matrix/NYISO.js` — the keeper/gates
   stamp; cells `offer_curve_by_group`, `campd_per_unit_attribution`,
   `campd_outage_merit_order_guard`, `egrid_identity_heat_rates`,
   `thermal_tranche_artifact_coverage`, `gas_offer_net_revenue_margin`,
   `p1_bidcost_pass`.
7. The keeper's `run_config.json` — every `*heat_rate*` / `egrid*` / `gas_st_*`
   / `campd_*` / `use_campd_bins` / `plant_level_fleet` field (values in §1),
   and its `git` block (`sha 0b757c3a`, `basis_sha d06e6866…`); its
   `meta.json` key list and `git log d06e6866..HEAD` over `src/market_sim`,
   `scripts/run_calibration*.py` (**23 commits touch LP-relevant code since
   the keeper's basis**, so a control replay is REQUIRED, per nyiso-183's
   standing clause).

**Not opened:** `metrics.json`, `legitimacy_diagnostics.json`,
`calibration_attestation.json` of any bundle; no residual, score or price of
any run.

### B. Source code, read

`src/market_sim/data/fleet/eia860.py` (`_COLUMN_ALIASES`;
`_egrid_boundary_hr_repairs` / `_egrid_boundary_hr_repairs_for` /
`_apply_egrid_boundary_hr_repairs`; `_rows_to_generators` in full;
`_load_fleet_from_parquet`; `_load_fleet_from_clean` signature;
`egrid_identity_heat_rates_for` / `apply_egrid_identity_heat_rates`;
`load_fleet_from_csv` in full; **`_correct_mixed_facility_steam_hr`**);
`src/market_sim/data/fleet/models.py` ll. 280–307 (**`MIXED_FACILITY_STEAM_HR
= {2500: 9.5, 315: 11.85, 335: 11.85}`** and its citation comment);
`scripts/data/process_eia860.py` (`_join_egrid_heat_rate`: plant-grain
`PLNT23.PLHTRT` from `egrid2023_data_rev2.xlsx`, window 3,000–30,000 Btu/kWh,
every generator at a plant inherits the plant value); `src/market_sim/data/
campd.py` ll. 245–380 (`CAMPD_STACK_DUPLICATE_UNITS = {8906: {"32SH": "31RH",
"52SH": "51RH"}}`, `stack_duplicate_mask`, `merge_stack_duplicate_units`) and
ll. 548–625 (`_normalize_campd` applies the mask); `scripts/lib/outage_detect.py`
(grep only: `build_merit_order_panel` reads the CAMPD parquets with
`pd.read_parquet` directly and carries NO reference to the stack-duplicate
helpers); `scripts/lib/campd_measured_classes.py` and
`scripts/data/derive_campd_unit_outages.py` (grep only: neither references the
helpers); `scripts/lib/bundle_fleet.py` in full; `scripts/probes/
nyiso183_g4c_offer_position.py` (`model_offer`, `stgas_units`) and
`nyiso183_g4d_offer_anatomy.py` in full; `src/market_sim/config/scenarios.py`
(the `egrid_identity_heat_rates` field block and its two registry lists);
`scripts/run_calibration.py` and `scripts/run_calibration_full.py` (the
`egrid_identity_heat_rates` threading at every site, the `--replay-bundle`
path and its override composition); `src/market_sim/data/fleet/assembly.py`
(the three `load_fleet_from_csv` call sites); `scripts/check_mechanism_matrix.py`
docstring; `docs/codebase-site/data/mechanism-matrix.js` (the
`egrid_identity_heat_rates` and `measured_chp_heat_rates` rows);
`tests/unit/data/test_egrid_identity_heat_rates.py` in full;
`tests/regression/test_fleet_facade.py` (the facade names only);
`data/raw/fleet-egrid/README.md`; `data/raw/_processed-legacy/
SOURCES_campd_ct_heat_rates.md`.

### C. Source data, read — THE JOIN TRACE (the brief's step 3, disclosed at full magnitude)

These are reads of committed inputs, not gate statistics; none is a residual,
score or model output. They are what the gates below are written knowing.

* **`data/raw/eia-860/eia860_generators.parquet`, plants 2500 and 8906:**
  Ravenswood carries FIVE `OP` rows — generators 1, 2, 3 (`ST`, 364.5 / 375.2
  / 985.1 MW net summer, 1963 / 1963 / 1965) and 4 / 4S (`CT` / `CA`, the
  2003 combined cycle, 149.8 / 72.4 MW) — and **every one of the five carries
  `heat_rate = 8.800451`**. Astoria carries 2, 3, ST5 (`ST`, `OP`) plus 1
  (`GT`, `OS`) and 4 (`ST`, `OS`), every row at **11.94939**.
* **`data/raw/campd-unit-level/NY_2023.parquet`, facility 2500:** units 10 /
  20 / 30 (`Tangentially-fired`, peaks 384 / 379 / 1,030 MW) at all-hours
  gross HR 10.81 / 10.53 / 11.47 (running-hour 10.58 / 10.12 / 11.16), gross
  281.7 / 226.2 / 375.5 GWh; `UCC001` (`Combined cycle`, peak 268) at 7.14,
  1,965.9 GWh; `CT0001` / `CT0010` / `CT0011` ≤ 0.8 GWh. So the combined cycle
  carried **69 %** of the site's 2023 gross energy and the steam **31 %**.
* **`NY_2023.parquet`, facility 8906:** `31RH` and `32SH` carry BYTE-IDENTICAL
  gross (378.063 GWh, peak 380, 2,998 running hours) at heat 2.122 / 2.032
  TBtu; `51RH` / `52SH` identical gross 387.945 GWh at 2.177 / 2.195 TBtu;
  unit 20 at 13.71; `CT0001` 1.1 GWh. Counted per row each half reads HR
  5.3–5.7; counted ONCE against the pair's summed heat, unit 3 reads **10.99**
  and unit 5 **11.27** gross.
* **eGRID 2020 and 2021 workbooks** (the only two I opened; **2022, 2023 and
  2024 are on disk and were NOT opened** — their family values are Phase-0
  measurements below): sheets `PLNT`, `UNT`, `GEN` for ORISPL 2500, 8906,
  2516, 2511, 2490. For 2500: `PLHTRT` 8,858.6 (2020) / 8,482.4 (2021) =
  `PLHTIAN` ÷ `PLNGENAN` exactly; UNT rows 10 / 20 / 30 (`PRMVR ST`) and
  `UCC001` (`CT`) carry their own `HTIAN`; GEN rows 1 / 2 / 3 (`ST`) and 4 /
  4S (`CT` / `CA`) carry their own `GENNTAN`. The steam-family rate
  Σ`HTIAN`(ST) ÷ Σ`GENNTAN`(ST) reads **12.06 (2020) / 12.58 (2021)** and the
  CC family **7.44 / 7.33**. For 8906, `PLNGENAN` is NaN in 2021 (no plant
  rate that vintage). For 2516 / 2511 / 2490 the ST family differs from the
  plant rate by ≤ 0.5 MMBtu/MWh.
* `data/raw/_processed-legacy/egrid_identity_heat_rates_NYISO.csv` (one row,
  7784) and the header of `campd_ct_heat_rates_NYISO.csv` (2511 covered at
  16.69 on CT_PEAKER; 2500 / 8906 absent).

**What the trace establishes BEFORE any gate, stated so it is not later
dressed as a discovery:** the CC_REGULAR base 8.80 IS the plant-grain eGRID
2023 `PLHTRT` (§B's `_join_egrid_heat_rate`), and the ST_GAS base 9.50 IS
`MIXED_FACILITY_STEAM_HR[2500]` lifting the same 8.80 (`gen.heat_rate <
target`). That resolves nyiso-183 §8's "second term" on the code alone; G1
below turns it into a measured identity rather than an assertion.

---

## §1 — RULE 19 `[R-ONE-MECH]`, DISCHARGED FROM THE CODE BEFORE ANY PROPOSAL

**Question: which armed mechanism SETS an NYISO `ST_GAS` unit's base heat rate
on this keeper, and which one OWNS Ravenswood's 9.50?** In application order:

| # | mechanism | keeper | scope | reaches (2500, ST_GAS)? |
|---|---|---|---|---|
| 1 | `process_eia860._join_egrid_heat_rate` — plant-grain eGRID-2023 `PLHTRT` written into the committed parquet at curation | committed input | every generator of every plant | **YES — writes 8.800451 to all five rows** |
| 2 | `HEAT_RATE_BINS[fuel][vintage]` fallback (`_rows_to_generators`) | committed | only where #1 is blank | no (join hit) |
| 3 | `_apply_egrid_boundary_hr_repairs` (frame level) | always on | `gas_cc` plants above `EGRID_CC_HR_PHYSICAL_CEILING` with a co-located sibling; accepted set `{55641}` | no |
| 4 | `measured_ct_heat_rates` (row loop) | **ON** | `CT_PEAKER` rows the CAMPD artifact covers | no (class-disjoint; 2500 absent) |
| 5 | **`_correct_mixed_facility_steam_hr` / `MIXED_FACILITY_STEAM_HR`** | **always on, ungated, no `ScenarioConfig` field** | `ST_GAS` rows of the three listed plants, when below the listed value | **YES — lifts 8.80 → 9.50. OWNS THE 9.50.** |
| 6 | `measured_chp_heat_rates` | **ON** | `CC_CHP` / `CT_CHP` rows the artifact covers | no |
| 7 | `egrid_identity_heat_rates` | **ON** | plant 7784 | no |
| 8 | `_correct_chp_steam_credit_hr` | always on | CHP hand-factor ISOs | no |
| 9 | `offer_curve_by_group` tranche multipliers (committed 1.05 … peak 4.20) | committed | class-uniform | multiplies, never sets the base |
| 10 | `gas_offer_net_revenue_margin` `phys_*` basis | ON | the `mc` composition, not `heat_rate` | nyiso-183 §7 proved the array carries the plain form |

**ANSWER: mechanism 5 owns the 9.50, and mechanism 1 owns the 8.80 it lifts.**
Together they are the whole of the CC/ST split nyiso-183 could not explain.
Three properties of mechanism 5, read off `models.py` ll. 280–307 and recorded
here because they decide what an admissible repair may look like:

* It is a **hardcoded per-plant dict** — rule 24 `[R-REGISTRY]` names this
  class verbatim, and nyiso-177 removed its sibling
  (`outages._FLEET_GROUP_OVERRIDE = {2500: "ST_GAS"}`) from this very plant.
* Its 9.5 is **not a measurement.** Its own comment derives it by "backing the
  CC out at plausible 2023 capacity factors (CC ~0.6, steam ~0.15)" from an
  assumed CC rate "~7.5". With the plant's own 222 MW of CC and 1,725 MW of
  steam those assumed CFs put **66 %** of the site's energy on the steam; the
  2023 meter (§0 C) puts **31 %** there. The value is arithmetic on assumed
  inputs, i.e. a hand estimate — exactly the thing rule 14 `[R-ACCURATE]`
  says was "silently compensating".
* It **cannot see a vintage** and cannot respond to changed conditions: the
  same 9.5 applies in 2019 and in 2050. It fails rule 13's forward test as
  written.

**Rule-19 consequence, binding on this session:** any repair must REPLACE
mechanism 5's role at the plants it covers with a construction that reads
the same eGRID source mechanism 1 reads, at a finer grain — never a
mechanism 11 stacked on top of 5, and never an edit of the 9.5 to another hand
number (§5 F1).

---

## §2 — THE TWO OBJECTS, DECIDED EX ANTE: Ravenswood and Astoria are NOT one object

The brief asks for this decision before any measurement. It is made here on
the §0 C trace alone:

* **Ravenswood (2500) is a MODEL-SIDE object.** Its measured steam rate is
  physically ordinary (10.1–11.5 gross per unit, the NYISO gas-steam band);
  the model's 9.50 is the artifact (§1).
* **Astoria (8906) is a MEASURED-SIDE INSTRUMENT ARTIFACT.** Its model base
  11.949 is the eGRID plant rate and physically ordinary for a 1958–62
  boiler fleet. Its "measured" 5.39–5.55 is the CAMPD stack-duplicate double
  count `campd.py` already identified at nyiso-141 on three independent
  channels (`CAMPD_STACK_DUPLICATE_UNITS`): the RH/SH halves each repeat the
  generator's FULL `grossLoad` while splitting `heatInput`. nyiso-183's
  `measured_hr` and `stgas_units` read the raw parquet without
  `merge_stack_duplicate_units` / `stack_duplicate_mask`, so they halved
  Astoria's heat rate; the "heat-recovery halves" reading in nyiso-183 §6.1
  was a misdescription (they are boiler monitoring paths, and they ARE the
  plant's `ST_GAS` units). **Prediction (G3):** with the pair merged,
  Astoria's G4d ratio lands INSIDE the eight-peer cluster and there is no
  model-side Astoria object at all.
* **A second, named consequence of the same artifact, sized only (§4 G3b, §5
  F4):** `outage_detect.build_merit_order_panel` reads the raw halves too, so
  the merit-order guard prices Astoria's SRMC at half its physical rate. That
  is an instrument defect on the AVAILABILITY path, which nyiso-183 closed
  (DO-NOT-REDO). It is handed to the outage-derive lane with its sizing, not
  repaired here.

---

## §3 — THE HYPOTHESIS AND THE ADMISSIBLE REPAIR FORM, FIXED NOW

**H (the join).** The plant-grain eGRID join hands a mixed-prime-mover plant
one generation-weighted blend, and the model then repairs the steam half of
ONE such plant with a hand number. The correct construction is the SAME
eGRID source at PRIME-MOVER-FAMILY grain: eGRID publishes per-unit heat input
(`UNT<yy>.HTIAN`, keyed by `PRMVR`) and per-generator net generation
(`GEN<yy>.GENNTAN`, keyed by `PRMVR`) for every plant, so a family rate

```
HR_family(plant, F) = Σ HTIAN over UNT rows of plant with PRMVR ∈ F
                    ÷ Σ GENNTAN over GEN rows of plant with PRMVR ∈ F
```

exists on the identical net-annual boundary as the plant rate every peer
carries, with **zero free parameters**.

**R1 — the ONLY admissible repair form.** `ScenarioConfig.egrid_family_heat_rates`
(bool, default **False**, byte-identical off), CLI `--egrid-family-heat-rates`
on both calibration entry points, reading a per-ISO committed artifact
`data/raw/_processed-legacy/egrid_family_heat_rates_<ISO>.csv` written by
`scripts/data/derive_egrid_family_heat_rates.py --iso <ISO>`. Fixed here:

1. **Families**, by prime-mover code on BOTH sides (eGRID `PRMVR`, EIA-860
   `prime_mover`): `ST` = {ST}; `CC` = {CT, CA, CS, CC}; `GT` = {GT, IC}. No
   other grouping, no fuel split within a family.
2. **Predicate (which plants the artifact covers):** a plant with **≥ 2
   families each carrying `HTIAN` > 0 AND `GENNTAN` > 0** in the applied
   vintage. Single-family plants are untouched by construction — their plant
   rate IS their family rate.
3. **Applied vintage = the vintage `_join_egrid_heat_rate` reads
   (`egrid2023_data_rev2.xlsx`, sheets `PLNT23` / `UNT23` / `GEN23`)**, so the
   family rate replaces the blend on the identical boundary and year. The
   derive ALSO records every on-disk vintage's family value (2018–2024) in a
   companion `_vintages.csv` for the reader; **none of those is applied and no
   pooling rule is chosen after seeing them** (§5 F9).
4. **Window:** a family rate outside the curation script's own
   `[3.0, 30.0]` MMBtu/MWh window is written with a `flag` and NOT applied —
   the identical constant the plant join uses, not a new one.
5. **Seam and precedence (rule 19):** applied at FRAME level inside
   `_rows_to_generators`, immediately after `_apply_egrid_boundary_hr_repairs`
   — the eGRID-input seam — so every class-specific measured mechanism keeps
   its existing precedence unchanged (`measured_ct_heat_rates` in the row
   loop, `measured_chp_heat_rates` / `egrid_identity_heat_rates` after load).
   Rows keyed by (plant, family of the row's own `prime_mover`); nuclear rows
   excluded (they carry no eGRID heat input and their own must-run model).
6. **Mechanism 5 is SUPERSEDED, not stacked:** `_correct_mixed_facility_steam_hr`
   skips every plant the armed artifact covers. Off, it runs exactly as today,
   so CAISO 315 / 335 are byte-identical (their entries are CAISO's lane;
   §5 F7).
7. **Rule 13 forward story:** regenerates for any year from whichever eGRID
   vintage the fleet join reads, from published fields alone; responds to
   changed conditions (a retrofit, a re-powering or a changed duty moves it);
   uses no model output and no measured outcome.
8. **Rule 25:** the artifact is per-ISO; an ISO with no committed artifact is
   a no-op even with the flag on.

**What R1 will ALSO do, stated in advance so it cannot be read as a
surprise:** at Ravenswood the CC family gets its OWN rate (2020 / 2021 read
7.44 / 7.33 against the 8.80 blend), so `CC_REGULAR` at 2500 gets CHEAPER
while `ST_GAS` gets dearer — the two halves of one blend moving apart. At any
other NYISO plant the predicate covers (steam + peaking GTs: 2511, 2516, 2490
and the like) the ST family moves by the amount the GTs were distorting the
blend (≤ 0.5 MMBtu/MWh in the 2020 / 2021 reads) and the GT family takes its
own rate unless `measured_ct_heat_rates` already covers it. G4 enumerates the
whole footprint before any solve.

---

## §4 — THE GATES, WITH BARS FIXED NOW

### G0 — INSTRUMENT (run first; S0 on failure)

`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` on the keeper, 2023 /
2024 / 2025, must reproduce nyiso-183's committed
`_nyiso183_g4d_offer_anatomy.json` `model_hr` for every `ST_GAS` plant to
within **±0.005**, and the recovered Ravenswood bases (committed-tranche ÷
1.05 and peak ÷ 4.20) must read **9.50 ± 0.01** for `ST_GAS` and **8.80 ±
0.01** for `CC_REGULAR`.

### G1 — THE JOIN, AS A MEASURED IDENTITY (not an assertion)

From `egrid2023_data_rev2.xlsx` `PLNT23`: `PLHTRT`(2500) ÷ 1000 must equal the
parquet's 8.800451 to **≤ 1e-5**, and `PLHTIAN` ÷ `PLNGENAN` must equal
`PLHTRT` to the same tolerance. **G1 FIRES iff both hold.** If G1 does not
fire the join hypothesis is refuted on its own terms and NO repair is built
(S1).

### G2 — THE FAMILY CONSTRUCTION IS GROUNDED AT RAVENSWOOD (the repair is proposed iff G2 fires)

Compute the 2023-vintage ST-family rate at 2500 per §3 R1 items 1–4. All
three must hold:

* **G2a** — inside the `[3.0, 30.0]` window.
* **G2b** — **≥ the CAMPD 2023 steam-only gross running-hour HR** measured by
  nyiso-183's own `measured_hr` (10.71). A net annual rate cannot sit below a
  gross loaded one; a family rate that did would be evidence of a broken
  eGRID row, not of efficiency.
* **G2c — the like-for-like statistic.** `r(plant) = eGRID-2023 rate the
  model would carry ÷ CAMPD-2023 steam-only gross running-hour HR`, where for
  each of nyiso-183's EIGHT peers (2527, 2625, 2516, 2490, 2517, 2480, 8006,
  2511) the eGRID rate is the plant `PLHTRT` they carry today and for
  Ravenswood it is the ST-family rate under R1. **G2c holds iff
  `r(2500)` lies within `[min, max]` of the eight peers' `r`.** The peers'
  range is computed and printed BEFORE Ravenswood's value in the probe. No
  new number: the band is the peers' own spread on the identical statistic.

**G2 FIRES iff G2a ∧ G2b ∧ G2c. If G2 fires, R1 is built and the A/B (G5)
runs. If G2 does not fire, NO solve is spent**: the family construction is
recorded as not reconciling with the class's measured relationship at this
plant, the finding reports which leg failed at full magnitude, and the object
stays open (S2).

### G3 — ASTORIA IS A MEASURED-SIDE ARTIFACT (two objects), and G3b sizes the guard consequence

Recompute nyiso-183's G4d ratio for 8906 in 2023 / 2024 / 2025 with the
CAMPD halves merged (`merge_stack_duplicate_units` to relabel,
`stack_duplicate_mask` to count gross once; heat summed over both paths) —
the model side unchanged from the committed JSON. **G3 FIRES (Astoria is a
measured-side artifact and NOT a model-side object) iff the merged ratio lies
inside that year's eight-peer `[min, max]` from the committed G4d rows in
≥ 2 of 3 years.** If G3 does not fire, Astoria is recorded as a SECOND open
model-side object and is NOT folded into R1 by assumption.

**G3b (size only, no bar, no repair — §5 F4):** the share of Astoria's
`ST_GAS` window-hours in the keeper's `-perunitmerit-` extract, and of its
`-layup-` rows, plus the panel's Astoria SRMC with and without the merge, so
the outage-derive lane receives a sized object.

### G4 — THE FOOTPRINT, ENUMERATED BEFORE ANY SOLVE (no LP)

Every NYISO (plant, family) the R1 predicate covers under the 2023 vintage,
with incumbent vs family rate, MW, class, and whether a class-specific
mechanism (4 / 6 / 7 in §1) retains precedence on that row. Reported at full
magnitude in the finding. No bar — it is the honest scope of one generic
rule — but **S3 fires if any covered family rate is outside the window
(those rows are simply not applied, by §3 item 4) AND the remaining applied
set no longer includes (2500, ST)**, since then the repair does not reach the
object it was built for.

### G5 — THE A/B (only if G2 fires)

* **Arm:** `scripts/run_calibration_full.py --replay-bundle
  results/calibration/nyiso177_vintage_B1p --egrid-family-heat-rates --year
  2023 2024 2025` — ONE invocation, years SEQUENTIAL (rules 16, 12), the
  keeper's recorded recipe plus exactly one field.
* **Control:** the same replay WITHOUT the flag, because 23 LP-relevant
  commits sit between the keeper's `basis_sha d06e6866` and this HEAD. Its
  bit-identity to the committed keeper is re-measured (hourly zonal prices,
  all three years); **a bit-identical control replay is an INSTRUMENT and
  registers nothing** (nyiso-183 §6 clause). A non-identical control is
  registered as the A/B's baseline and the drift named.
* **Pre-declared expectations (falsifiable, not bars):** (i) Ravenswood
  `ST_GAS` energy FALLS in every year; (ii) the C1-2023 `ST_GAS` cell moves
  toward zero; (iii) **2024 and 2025 `ST_GAS` DEEPEN** — the other ten plants
  are −6.776 / −7.957 TWh short economically and this repair removes volume
  from the eleventh (the nyiso-140 precedent; an EXPECTED outcome of a
  correct repair, reported at full magnitude, disposition to the owner —
  never withheld and never compensated by a second lever); (iv) Ravenswood
  `CC_REGULAR` energy RISES (its family rate falls); (v) **C3a: no price
  claim is banked** — the change is a within-NYC merit reshuffle whose price
  sign is not predicted here; C3a-2025 stays owner-court whatever it does.
* **Scored** on the standard rubric, all criteria, and **leave-one-year-out
  within 2023–2025** before any promotion is proposed.
* **Verdict rule, fixed now.** The arm is a **REJECTED PROBE** if any
  load-bearing criterion OTHER than C1 (`C2`, `C3a`, `C3b`) or the protective
  `C8` flips PASS → FAIL against the control. Otherwise it is a **KEEPER
  CANDIDATE** put to the owner with the C1 movement in ALL THREE years at
  full magnitude, the four rule-1 / 14 / 21 / 24 integrity gains (a measured
  construction replacing a hand number; the per-plant dict superseded;
  vintage-reproducible; the CC and ST halves of one blend on one basis) and
  every regression named. **This session does not promote on its own
  authority.**

---

## §5 — ADMISSIBLE AND FORBIDDEN, FIXED IN ADVANCE

**Admissible:** R1 (§3) and nothing else.

**Forbidden (named now so a later temptation is already answered):**

* **F1** — any per-plant value: editing `MIXED_FACILITY_STEAM_HR[2500]` to a
  different number, adding 8906 or any plant to it, or any new dict / carve
  keyed on a plant id in `src/`, `scripts/` or a config. Rule 24; the
  nyiso-177 `_FLEET_GROUP_OVERRIDE` incident on this very plant.
* **F2** — any heat-rate value, multiplier, pooling window or vintage choice
  selected against a residual, a price gap, the C1-2023 cell or any A/B
  outcome. Rules 5 / 21.
* **F3** — pinning Ravenswood (or any unit) to its same-year CAMPD heat rate
  or generation; any input rescaled so the model's OUTPUT lands on the
  actuals. Rule 13. (The CAMPD steam-only rate DIAGNOSES in G2b / G2c; it is
  never the input.)
* **F4** — re-opening the availability route in any form: the merit-order
  guard, its constants, `_resolve_unit_group`, the outage extract, or
  repairing G3b's panel defect here. nyiso-183 DO-NOT-REDO. G3b is SIZED and
  handed forward.
* **F5** — deleting, narrowing or re-weighting any `ST_GAS` floor, or any
  volume-buying lever. nyiso-181 DO-NOT-REDO.
* **F6** — touching C3a-2025 (owner-court, `DECISION-CARD-nyiso148` Q1) or
  the D-2 / C8 grain under-count (escalated, scorer lane, code-generic).
* **F7** — editing any non-NYISO matrix shard's verdicts, or CAISO's 315 /
  335 dict entries (their retirement under R1 is CAISO's lane to test; the
  flag's default-off leaves them byte-identical). Rules 25 / 28. *(The one
  deliberately non-parallel edit rule 28c REQUIRES — a `U` cell line for the
  new field in every shard — is not a verdict edit and is made.)*
* **F8** — any year outside 2023–2025: NYISO holds neither `complete` nor
  `final`, the holdout freeze is ACTIVE, 2019 / H1-2026 are NEVER GRANTED,
  and **no marker is requested**. Rule 22.
* **F9** — choosing the applied eGRID vintage or a pooling rule after
  reading the per-vintage family values. The applied vintage is the join's
  own (§3 item 3), fixed here before 2022 / 2023 / 2024 are opened.
* **F10** — a second solve-affecting lever in the same arm (a compensating
  offer, floor or availability change to offset the expected 2024 / 2025
  deepening). The arm is exactly one field.

---

## §6 — STOP CONDITIONS (each fires on its own terms, whatever the residual)

* **S0** — G0 fails ⇒ STOP, report an instrument failure, score nothing.
* **S1** — G1 does not fire ⇒ the join hypothesis is refuted; no repair
  built; report.
* **S2** — G2 does not fire ⇒ no solve spent; R1 is not proposed; the
  failing leg reported at full magnitude.
* **S3** — G4's applied set does not reach (2500, ST) ⇒ no solve spent.
* **S4** — no new tunable beyond the ONE default-off boolean and its
  artifact; no env var; no per-plant dict; no constant moved or swept
  (`HEAT_RATE_BINS`, the [3, 30] window, every `MERIT_*` constant, every
  tranche multiplier are READ at their committed values).
* **S5** — the A/B is 2023 + 2024 + 2025 in ONE invocation, years
  SEQUENTIAL, at most 2 concurrent invocations (arm + control), LOYO-scored
  before any promotion is proposed; a bit-identical control replay registers
  nothing.
* **S6** — every non-control solve that completes is registered on the
  backcast dashboard THIS session, keeper candidate or rejected probe (rule
  15); the NYISO matrix shard is re-stamped and the new field's row + shard
  cell lines land in the same PR (rule 28c).

---

## §7 — WHAT THIS SESSION WILL NOT BE ABLE TO CLAIM

1. **If G2 fails, nothing is repaired** — the session will have traced the
   join to source, named the owner of the 9.50 and adjudicated Astoria, and
   will say exactly that.
2. **A better C1-2023 is not evidence for R1, and a worse 2024 / 2025 is not
   evidence against it** (rule 1). R1 stands or falls on G1–G2 and on the
   integrity of its construction; the A/B measures its consequence.
3. **C3a-2025 is not this session's.** Whatever the arm does to it is
   reported and left owner-court.
4. **G3b sizes, it does not repair.** Astoria's guard-panel defect is an
   availability-path object and is handed to that lane.
5. **The eGRID family rate is an annual net average**, like every peer's
   plant rate; it is not a loaded rate. A future measured-loaded construction
   (the `measured_ct_heat_rates` template) is a different mechanism and is
   not built or pre-judged here.
6. **The D-2 / C8 grain under-count stays escalated** and untouched.
