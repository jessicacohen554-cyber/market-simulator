# FINDING closeout-parasitic-backfill: measured parasitic factors for every ISO (zero LP)

Lane closeout-parasitic-backfill, 2026-10-05. Chartered by the backcast close-out desk from closeout-SOCO-w3
phase 0c §4 (the cross-ISO census, `docs/records/soco/closeout-soco-w3/parasitic_census_all_iso.csv` on that
lane's branch). No LP solve. Rules 14 (measured beats estimate) and 23 (a derive re-runs only on a data change).

**Main carries the script, its tests and this census. The new rows are branch-only**, at
`claude/closeout-parasitic-backfill-rows`, until the owner rules (§6). Every keeper reads the pooled map, the
CALIBRATED NYISO and NEISO among them.

Evidence: `parasitic-backfill/` next to this file.

## 1. The construction, and proof it reproduces

`scripts/data/derive_parasitic_load.py` builds the map with `campd.compute_parasitic_factors`:

- Per plant-year, factor = EIA-923 Page-1 combustion net ÷ CAMPD gross.
- The pooled `year == 0` row sums net and gross over the run's years, then divides.
- A ratio outside [0.80, 1.00], or one with no net, falls back to `class_default`.

Every consumer reads only the pooled row (`campd.pooled_factor_map`).

The construction was rerun over every state in `campd.ISO_STATES` for 2019–2025. It was compared with every
committed per-year row the two share (`--check`; `reproduction_check.csv`). Pooled rows are excluded because each
was pooled over its own first run's year set.

| Shared plant-years | Result |
|---|---|
| 2,165 | CAMPD gross **byte-identical** on every row |
| 1,228 measured in both | 1,227 within ±0.005 (p99 diff 0.000) |
| 825 class-default in both | identical |
| 1 measured row off by 0.030 | plant 1554, 2025: the EIA-923 2025 FINAL refresh (2026-10-02) moved its net |
| 112 class-default → measured | net was 0 when written: 2023/24 on the old ERCO-only generation table (`out-of-sample-results-2026-07.md`, "27 PJM plants") and 2025 on the preliminary release |

**The method reproduces exactly.** Every difference comes from an EIA-923 revision since the row was written.
None of those committed rows is moved (rule 23).

## 2. Script changes (on main)

- **`--iso` takes several ISOs, or `ALL`.** CAMPD is read one state-year at a time and reduced to annual plant totals
  before the next is read. Every total is a sum, so the result equals one call over the full frame. The test
  asserts this.
- **`--check [--tol] [--check-out]`** reproduces the committed rows and writes nothing. It is the gate a back-fill
  runs first.
- **`--merge` fix 1: pooled row keyed on itself.** The old merge added a pooled row only for a plant with no row
  at all. The 2022 back-fill left **106 plants with 2022 rows but no pooled row**, so they could never gain one, and
  the pooled row is the only one read. Examples: Monroe, J H Campbell, Belle River, St. Clair, Zimmer, Covert, Blue
  Water. The merge now keys on the pooled row itself. A committed pooled row still never moves.
- **`--merge` fix 2: measured rows only.** `class_default` takes its class from the plant registry. The registry
  carries a `plant_group` for 1 of the 871 plants new to the file. So every new "default" would have been the
  generic 0.97 whatever the class: coal 0.97 for 0.93, CT 0.97 for 0.99. A back-fill now adds measured rows only.
  An unmeasurable plant stays absent, and each consumer keeps the fallback it applies today.
- Tests: `tests/curation/test_derive_parasitic_load.py`.

## 3. Coverage after the back-fill (`coverage_by_plant.csv`)

Fleet = the SOCO-w3 census plant list (CEMS-reporting coal/CC/CT/ST plants per ISO).

| ISO | Plants | Already pooled (measured / default) | **Newly measured** | Unmeasurable |
|---|---|---|---|---|
| CAISO | 73 | 0 / 0 | **44** (19.7 GW) | 29 out of band |
| ERCOT | 91 | 75 / 14 | **2** (1.9 GW) | 0 |
| MISO | 194 | 24 / 25 | **128** (77.7 GW) | 17 out of band |
| NEISO | 43 | 20 / 23 | 0 | 0 |
| NWPP | 47 | 0 / 0 | **42** (23.8 GW) | 5 out of band |
| NYISO | 49 | 1 / 0 | **36** (16.1 GW) | 12 out of band |
| PJM | 199 | 122 / 65 | **9** (5.3 GW) | 3 out of band |
| SOCO | 45 | 0 / 0 | **39** (42.5 GW) | 6 out of band |
| SPP | 109 | 0 / 14 | **80** (37.2 GW) | 14 out of band, 1 with no CAMPD row |

These are exactly the desk's missing counts, e.g. MISO 145 = 128 + 17.

**Why the 86 out-of-band plants can't be measured:** the CAMPD and EIA-923 unit sets differ at the plant.

- **net/gross > 1** (about half): CEMS meters only part of the plant. Usually a CC whose steam turbine is not in
  CEMS gross (Pastoria, Bethlehem, McWilliams), or EIA-923 net includes non-CEMS units.
- **< 0.80** (the rest): CEMS covers units that EIA-923 books elsewhere or under another plant code.

The plant ratio cannot separate station service from unit-set mismatch, so these keep their class fallback. A
unit-level reconciliation would be its own derive.

The registry back-fill (`--no-registry`) was not run, so `master-plant-registry.csv` is untouched.

The branch file also adds 4,809 measured per-year rows: missing years of new plants, and 2019–2021 for already
covered plants. Today no solve-path consumer reads per-year rows. The v2 emission-rate derive reads them only when
re-run.

## 4. Impact census, zero LP

Only the 380 newly pooled plants move anything. The tables below compare main with the branch.

**HR artifacts** (`impact_hr_by_iso_class{,_year}.csv`):

- Each `flag == ok` row of `campd_{coal,cc,ct,st}_heat_rates_<ISO>.csv` is rescaled: HR_net × (old factor / new
  factor).
- The result is priced at the plant's own EIA-923 delivered price for that year. The ISO-year median is used where
  the plant has no price.
- Figures are capacity-weighted over 2019–2025 rows, in $/MWh of offer. Positive means the offer rises.

**Benchmark** (`impact_benchmark_cems_net_by_iso_year.csv`): the CEMS-net series (`_campd_hourly_frame`) maps a
plant absent from the map at **1.0** (gross = net), not at a class default. So every newly measured plant lowers
that series.

That series is the C4 hourly level, plus the EIA-923 backfill path for plants that EIA-923 under-reports. The
EIA-923 annual class totals do not otherwise move.

| ISO | CC | Coal | CT | ST | Coal − CC spread, per year | CEMS-net TWh/yr (Δ%) |
|---|---|---|---|---|---|---|
| CAISO | +0.53 | — | +4.48 | +0.36 | — | −1.5 to −2.3 of 51 (−3.9 %) |
| ERCOT | +0.02 | 0.00 | 0 | 0 | −0.04 to 0.00 | −0.2 to −0.5 of 216 (−0.1 %) |
| MISO | +0.22 | +0.22 | +1.38 | +0.14 | −0.26 to +0.26 | **−15.4 to −18.6** of 385 (−4.4 %) |
| NEISO | 0 | 0 | 0 | 0 | 0 | 0 |
| NWPP | +0.04 | +0.59 | +1.02 | +1.40 | **+0.42 to +0.74** | −5.8 to −7.7 of 116 (−5.6 %) |
| NYISO | +0.24 | −0.02 | +3.47 | +0.52 | −0.30 to −0.18 | −1.1 to −1.8 of 40 (−3.7 %) |
| PJM | 0.00 | +0.03 | 0.00 | 0 | 0.00 to +0.06 | −0.1 to −0.9 of 465 (−0.1 %); 2019–22 are the 2022-only plants |
| SOCO | +0.13 | +0.92 | +2.31 | +0.87 | **+0.52 to +0.74** | −6.8 to −9.1 of 171 (−4.6 %) |
| SPP | +0.29 | +0.26 | +2.34 | +0.80 | −0.42 to +0.10 | −7.3 to −8.7 of 149 (−5.4 %) |

**Sign, in short:**

- **NEISO and ERCOT:** do not move.
- **PJM:** no material movement. The 106 per-year-only plants now get a pooled row; most are PJM or MISO units
  retired before 2023.
- **Everywhere else:**
  - Offers rise: measured station service is larger than the class default.
  - CT moves most. CT measured factors average 0.915, matching the committed ERCOT/PJM CT mean of 0.923, against a
    0.99 default.
  - Coal moves more than CC, so coal falls further behind CC in merit order in SOCO and NWPP (+$0.4–0.7/MWh).
    This is the SOCO-w3 §4 sign, which deepens that ISO's CC over-run.
  - The CEMS-net benchmark falls 4–6 %.

**Caveats:**

- A few rows show extreme $ values (max +$64/MWh, SPP plant 3008 in 2021). These are fuel-price outliers in
  EIA-923 (Uri 2021, $53/MMBtu), not factor outliers.
- Pooled artifact rows are priced at 2023.

## 5. Pre-existing defect, left unchanged

**249 committed `class_default` pooled rows carry the generic 0.97, not their class default**
(`committed_generic_default_rows.csv`). The cause is the same registry gap. Affected:

- PJM 66 plants (CT 39, CC 14, coal 9, ST 4)
- MISO 26
- NEISO 25
- SPP 15
- ERCOT 7

Example: the 9 PJM coal plants are converted at 0.97 where the class default is 0.93. Per rule 23 these rows are
not moved here. Re-keying them, or deleting them so consumers apply their own class fallback, is an owner decision
(§6).

## 6. For the owner

- **Land the branch rows?** Every ISO except NEISO re-keys. ERCOT and PJM move negligibly. NYISO (CALIBRATED)
  moves: CT +$3.5/MWh, benchmark −3.7 %.
- **The 249 generic-0.97 committed defaults** (§5): fix the class, or drop them.
- **The 86 out-of-band plants** need a unit-level net/gross reconciliation, a separate derive.
- After either change, the HR artifacts that read the map must re-derive in the same commit (rule 23, citing this
  data change):
  - coal, CC, CT and ST measured-HR derives;
  - `derive_thermal_tranches` and its siblings;
  - `derive_cc_committed_pct` and `derive_cc_conduct_profile`;
  - plant emissions;
  - the ERCOT `campd_bins` ramp.
