# FINDING — PJM-NEXT-31: COAL_BIT whole-unit dark hours the keeper's outage windows miss (zero LP)

Lane `PJM-NEXT-31` (branch `claude/pjm-next-31`, from `bd6516d7`). **Zero LP.** Keeper unchanged:
`2026-10-02-w0-pjm-fix2` (bundle `results/calibration/w0_pjm_span`, 2019–2025). Successor to PJM-NEXT-30, whose
§2 found that 62–89 % of the COAL_BIT derate + offline gap falls in plant-hours where at least one CAMPD unit is dark
(`opTime = 0`), outside the keeper's windows. Owner ruling (NEXT-30 §4): build the outage repair, kept on structure
even if 2023/24 regress.

§1 is committed **before** any number in §2 exists. Nothing in §1 is re-read after the probe runs.

## §1 Readings, fixed ex ante

### Keeper outage surface (from `w0_pjm_span/run_config.json`)

Three committed CAMPD unit extracts feed the keeper's COAL_BIT availability:

| layer | flag (keeper value) | file |
|---|---|---|
| long, ≥ 5 d | `unit_outage_full_rederive` + `_rederive_peaker_windows` + `_exit_cohort_repair` + `_unit_fuel_routing` (all on) | `campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv` |
| short, 1–5 d, coal, unit CF ≥ `SHORT_BASELOAD_CF` | `unit_outage_short_windows` (on) | `campd-unit-outages-short-rederive-PJM.csv` |
| short gas | `unit_outage_short_windows_gas` (on) | `campd-unit-outages-shortgas-PJM.csv` |

Every window passes `outage_detect.filter_revealed_outages` (PJM's EIA-930 key is present, so the net-load mask is
live): a span is kept iff it is down through ≥ `MIN_INMERIT_HOURS` local high-net-load hours, or is a full stop
(mean CF < `FULL_STOP_OVERRIDE_CF`) of ≥ `FULL_STOP_OVERRIDE_DAYS`. Windows are day-grain
(`unit_outage_window_hour_grain` off).

### Population and quantities

- **Years:** 2019–2025. **Hours:** all 8760 (or 8784), plus the NEXT-30 S2 subset `H_y` (real implied HR ≥ 10,
  `_pjmnext29_coalbit_bins.HI_HR`), so the S2 numbers line up with NEXT-30's pieces.
- **Plants:** COAL_BIT plants in the keeper's `unit_marginal_<y>`. **Units:** their CAMPD units
  (`data/raw/campd-unit-level/<ST>_<y>.parquet`, matched on `facilityId` = EIA plant code). A unit enters year `y`
  only if it has at least one hour with `grossLoad > 0` in `y`. Whole-year-dark units are excluded here; they belong to
  the exit and `campd_dark_unit_year_windows` question, which is counted separately.
- **Unit-dark hour:** `opTime = 0`, or no CAMPD row on the full-year clock (zero-filled, as the detector does).
- **Dark run:** a maximal run of consecutive unit-dark hours. Its length `L` classifies every hour in it.
- **Unit share:** `u` = the unit's annual max `grossLoad` ÷ the Σ of that over the plant's units in `y`.
- **Covered:** the unit-hour lies inside a window of any of the three committed extracts for that
  (`facility_id`, `unit_id`), expanded at day grain the way the loader expands it.
- **Reflected in model cap:** per plant-hour, `K(h)` = keeper `cap_mw` (Σ tranches), `K*` = its annual max.
  Dark MW = `K*` × Σ `u` over dark units. Model reduction = `K*` − `K(h)`. **Unreflected dark MW** =
  max(0, dark MW − model reduction). This is the dispatch-independent census quantity. It is comparable with the
  NEXT-30 `K`-twin derate + offline pieces, not with the `M` pieces.

### Classes for an uncovered unit-dark hour (ordered, first match wins)

| class | rule | what it names |
|---|---|---|
| **C0** | covered by an extract window | the window exists; any unreflected MW is a downstream routing/denominator loss |
| **C1** | `L` < 24 h | below every extract floor (the short layer's floor is 1 day) |
| **C2** | 24 ≤ `L` < 120 h, unit annual CF < `SHORT_BASELOAD_CF` | the short layer's baseload-eligibility guard |
| **C3** | 24 ≤ `L` < 120 h, eligible, and `filter_revealed_outages` (PJM mask, the committed constants) drops the run | the revealed-availability filter, short band |
| **C4** | `L` ≥ 120 h and the filter drops the run | the revealed-availability filter, long band |
| **C5** | anything else | detector-shape residue (for example, the averaged real-run rule folding < 24 h running spells into a window, or a unit-id mismatch). Reported, not chartered. |

### Forced vs economic (rule 13)

From CEMS alone a dark coal unit is either unavailable (forced/maintenance) or in an economic reserve shutdown.
The admissible discriminator is the one the committed filter already uses: **exogenous EIA-930 net load**. An
uncovered dark hour is **revealed-tight** if it falls in a local high-net-load hour (`high_load_mask("PJM", y)`).
A coal unit dark when the system is tight is revealed unavailable. The S2 flag (LMP-based) is reported as
information only. It never enters a detector rule, because the extract must stay price-free.

### Readings

| id | question | decision rule |
|---|---|---|
| Q1 | Does the census account for NEXT-30's unit-dark pieces? | Pooled 2019–21, `H_y`-mean unreflected dark MW ÷ the NEXT-30 `K`-twin (derate + offline) × its unit-dark share. **Accounts** if ≥ 0.5. Otherwise the shortfall is named: the NEXT-30 pieces are measured against revealed net output, not against unit status. |
| Q2 | Why do the extracts miss it? | Share of uncovered unit-dark MWh (unit-share weighted, `u` × `K*`) by class, in `H_y` and over all hours, pooled 2019–25 and 2019–21 separately. A class is **dominant** if ≥ 50 % in `H_y` pooled 2019–25. Otherwise the top two are named. |
| Q3 | Is the dominant (or larger) class admissible? | Its revealed-tight share (all hours). **Admissible** if ≥ 0.5: most of its dark hours fall where the unit would be called. If < 0.5, the class is mostly ambiguous with economic shutdown, and a window built on it would admit economic idling. NOT ADMISSIBLE at that grain. |
| Q4 | Is a repair chartered? | **Chartered** iff Q2's dominant (or larger) class is a detector gate (C1–C4) AND Q3 holds. The repair family follows the class: C1 → a sub-day tier under the same revealed test; C2 → the eligibility guard; C3/C4 → the in-merit test. The exact rule, its constants (none new if avoidable, each cited if not) and its ScenarioConfig field go into the PRECOMMIT after §2. If C0 dominates, the charter is a downstream routing repair instead. If C5 dominates, or Q3 fails, NOT CHARTERED, and the result goes to the owner. |
| Q5 | Which years does it move? | Per year, `H_y`-mean unreflected dark MW per MW of `K` in the Q4 class. Information only: it sizes the expected C1 delta per year (NEXT-30 expected 2023/24 to move with the fail years). |

Every Q4 branch is a routing statement. A solve follows only through a PRECOMMIT.

## §2 Result

*(written after the probe runs)*
