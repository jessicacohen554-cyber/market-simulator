# FINDING — NWPP-NEXT-13 phase 0 (ZERO LP): coal WEFOR relief, the dispatched-bin denominator, and per-unit attribution

All numbers are fleet-only rebuilds (`run_year(fleet_only=True)`) of keeper #17
(`results/calibration/nwppnext12mr_span`) on its own recipe. No LP.
Probes: `scripts/probes/_nwppnext13_screened_wefor_phase0.py`, `scripts/probes/_nwppnext13_perunit_census.py`.
Raw output: `docs/records/nwpp/nwppnext13/{screened_wefor_phase0,perunit_census}.json`.

## 1. Lever 1 — the statistical coal WEFOR double count

### 1.1 The screened set

`derive_campd_unit_outages.py --iso NWPP --years 2019..2025 --short-windows --emit-screened-set` (to scratch first):
the short extract is **byte-identical** to the committed `campd-unit-outages-short-NWPP.csv` (sha `d53d6c7b…`). The
companion `campd-unit-outages-short-screened-NWPP.csv` has 146 coal unit-years (committed here; read only under
`wefor_residual_short_screened_coal`, which stays off).

### 1.2 Identification (caiso-187 formula): clean

| year | screened LP MW / coal LP MW | W_s (statistical) | X_s (≥5-d + short + partial) | residual |
|---|---|---:|---:|---:|
| 2019 | 10,643 / 11,727 | 4.6 % | 17.3 % | 0 |
| 2020 | 9,265 / 11,380 | 4.1 % | 23.3 % | 0 |
| 2021 | 9,309 / 10,795 | 4.2 % | 16.5 % | 0 |
| 2022 | 8,797 / 10,790 | 4.2 % | 16.0 % | 0 |
| 2023 | 4,418 / 9,428 | 4.5 % | 19.0 % | 0 |
| 2024 | 4,418 / 8,358 | 4.3 % | 23.5 % | 0 |
| 2025 | 7,536 / 10,048 | 4.0 % | 20.0 % | 0 |

The measured record removes 3.5–5.7× what the statistical term claims on the screened units. `wefor_residual = 0.0`
on that set is identified, not tuned.

### 1.3 But it cannot be armed on NWPP as built

1. **The prerequisite `unit_outage_dispatched_bin_denominator` is wrong on NWPP by construction (rule 14).** It moves
   only two plants, Centralia 3845 and Colstrip 6076, in 2020/21/22/25 (+0.4–1.1 TWh coal availability each). In
   those years the LP carries their **retired exit cohorts** (`_r202012` Centralia BW21, `_r202001` Colstrip 1–2)
   in the same bin, at zero availability all year. The incumbent denominator (670 / 1,480 MW, the live units) is
   right; the flag divides by the bin's pmax (1,340 / 2,094 MW), which includes the dead cohort. Measured case:
   Centralia BW22, the live unit, has CAMPD full outages 2021-04-03→06-26 and 2022-04-24→07-10. The incumbent
   zeroes it (0 MW available in May–Jun); the flag leaves 250–280 MW available through a measured full outage.
   **Cell → R.**
2. The screened share inherits the same dilution (Centralia 0.53, Colstrip 0.79 in those years).
3. `wefor_residual = 0.0` with NWPP's `wefor_residual_groups = None` zeroes WEFOR on **all coal and all CC/ST gas**
   (CC_REGULAR +2.5–2.9 TWh/yr available, unidentified), and the screened-share branch (`fleet/arrays.py`, an
   `elif` behind the covered-class test) never fires. MISO composes it only because its keeper already carries an
   identified gas `wefor_residual` on `{CC_REGULAR, ST_GAS, ST_CHP}`.
4. Jim Bridger 8066 (the C4-2023 plant) is **unscreened** in 2023, so no form of this relief reaches C4.

**Stop, per the handoff.** A clean arm needs a denominator that counts only live capacity (a change to miso-266's
shared mechanism, which MISO's keeper arms) plus a way to scope `wefor_residual` to screened coal alone. Routed.
`wefor_multiplier = 0.7` is untouched (rule 1).

## 2. Lever 2 — Clark 2322 CC routing: the per-unit crosswalk is right

### 2.1 EIA-860 decides it

Clark generators **11–22 are GT simple-cycle peakers** (12 × 60.5 MW, 2008). Only 9/10 (CA) and GT5–GT8 (CT) are
combined cycle. CAMPD reports the peakers as 24 units 11A…22B. The standard extract routes all 2,951 of their
≥5-day windows (idle-peaker stretches) onto **CC_REGULAR**. At Silverhawk 55841, A09/A10 are the 2024 GT peakers
CT3/CT4 (227.8 MW each), and their 46 windows go the same way.

### 2.2 The consequence is a physics violation (rule 14)

Clark CC_REGULAR (462 MW LP) available energy vs its own EIA-923 CC generation (CA + CT):

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| keeper #17 available, TWh | 0.682 | 0.488 | 0.656 | 0.503 | **0.025** | 0.143 | **0.002** |
| EIA-923 CC net, TWh | 0.446 | 0.561 | 0.699 | 0.770 | 0.433 | 0.861 | 0.665 |
| per-unit available, TWh | 3.693 | 3.693 | 3.693 | 3.693 | 3.694 | 3.693 | 3.693 |

Silverhawk CC: 1.822 / 1.719 TWh available vs 2.694 / 2.390 generated (2024 / 2025); per-unit +2.81 / +2.99.

### 2.3 The per-unit re-derives

- **Outage extract.** The HEAD standard re-derive is identical (sorted) to keeper #17's `-memberrepair-` extract,
  Boardman rows included. The `--per-unit-crosswalk` re-derive differs from it only by dropping those 2,997 windows.
  Nothing is added or regrouped; coal is byte-identical.
- **Tranche artifact** (the flag's other half, rule 19). Two deriver defects had to be fixed first
  (`scripts/data/derive_thermal_tranches.py`):
  1. `_fleet_nameplate_and_group` keyed on the coal **subclass** since COAL-SUB, so a HEAD re-derive silently
     emitted **no COAL rows**. With the fix, HEAD reproduces all 68 committed NWPP rows value-for-value.
  2. The per-unit resolver sent coal boilers through the gas-only crosswalk (every boiler → ST_GAS). At the two
     mixed coal/gas-steam plants (Naughton 4162, North Valmy 8224) the COAL row vanished. A coal-fuel guard now
     routes a unit whose CAMPD `primaryFuelInfo` names coal to the plant's COAL bin; it is inert where a plant has
     no COAL bin (every NYISO plant).

  With both fixes, per-unit attribution changes six rows and adds seven. Three incumbent rows were physically
  impossible:

  | plant | row | incumbent | per-unit |
  |---|---|---|---|
  | Silverhawk 55841 | CC_REGULAR median_cf / peaking | 115.0 % / 25.0 % | 61.8 % / 4.5 % |
  | Jim Bridger 8066 | ST_GAS median_cf | 106.6 % | 44.2 % |
  | Naughton 4162 | COAL median_cf / mustrun | 103.4 % / 31.4 % | 76.2 % / 23.3 % |
  | Tracy 2336, Harry Allen 7082 | CC peaking | 17.8 %, 14.7 % | 5.8 %, 3.1 % |
  | Jim Bridger 8066 | COAL | **no row** (primary group was ST_GAS) | measured: committed = mustrun 16.6 % |
  | Gadsby 3648, Tracy, Harry Allen, Silverhawk | CT_PEAKER | no row | measured rows |

### 2.4 What moves in the LP inputs (the flag alone)

- CC_REGULAR available: +3.0–3.7 TWh/yr (Clark), +2.8–3.0 TWh (Silverhawk 2024–25). No other class's availability moves.
- **Jim Bridger's take-or-pay must-run tranche falls from the class default 953.5 MW to the measured 351.8 MW**
  (2019–2023; scaled on the 1,028 MW coal bin in 2024–25). This is lever 3's "Jim Bridger has no measured COAL
  tranche row", closed by the same attribution repair.
- New committed CT tranches at Gadsby, Tracy, Harry Allen (and Silverhawk from 2024); Naughton's coal must-run falls.
- Heat rates, pmax totals and the unit roster per plant are otherwise unchanged.

Cells: `campd_per_unit_attribution` O → candidate (solve owed, PRECOMMIT-nwppnext13);
`unit_outage_dispatched_bin_denominator` U → R; `wefor_residual_short_screened_coal` O → G (blocked on §1.3);
`wefor_residual` stays O.

## 3. Routed, not absorbed

- **Dead exit cohorts in the fleet.** 2021/22/25 carry cohorts that exited in 2020 (zero availability). Harmless to
  dispatch, but any bin-pmax denominator counts them. Owner/MISO-lane question for miso-266's flag (§1.3.1).
- **HEAD tranche deriver regression (COAL-SUB)** affected every ISO's re-derive, not only NWPP. Fixed here; no
  committed artifact changes.
