# PRECOMMIT — lane NWPP-32: the hydro energy budget (288 plants) and NWPP-36's specification

**Lane** NWPP-32 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-14 ·
**Branch** `claude/happy-newton-rdab8x` (the session's harness-designated branch; the charter's
stem `claude/nwpp-32-hydro-budget-<4 chars>` could not be used because the harness fixes the
push branch per session — stated here so the desk does not look for the stem) ·
**Base sha** `d54cd9c571359b85cb1a8e1cd5cab68c080a6b0c` (= `origin/main` at session start) ·
**DATA PROFILE** `nwpp` · **Zero LP** (rule 32 `[R-SHARD]`: this lane runs no solve; rule 31's
promotion question does not fire).

Charter: `docs/multi-iso/nwpp-addition-plan-2026-09.md` §2.7 (in full), §3 card N3 (RULED: build
cascade coupling first), §5 row NWPP-32, §8 W3 prompt NWPP-32, §8.0 collision rules; CLAUDE.md
rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 23 `[R-FROZEN-DERIVE]`, 27 `[R-PUSH]`,
28 `[R-MECH-MATRIX]`.

---

## 0. Honesty note on ordering — what was and was not read before this document

Written **before** any artifact was built and before any per-plant number, any river/mode table,
any within-month statistic or any instrument text was read. Two things WERE read first, as
zero-LP reconnaissance while verifying the preconditions, and the rules in §3 below are therefore
**not** pre-registered against them:

* the loader's population counts (`_load_hydro_generation("NWPP", y)` → 280 / 280 / 25 plants;
  `_load_hydro_nameplate("NWPP")` → 288 plants, 35,799.5 MW);
* the pooled EIA-930 `NG: WAT` monthly level against the EIA-923 `HY` monthly total for all three
  years (930/923 annual ratio 0.9748 / 0.9748 / 1.4871; monthly r 0.997 / 0.993 / 0.989).

Everything else in this document — the reconciliation gate (§2), the instrument admissibility rule
(§4) and the four §2.7 measurement definitions (§5) — is registered here before the numbers exist.

## 1. Preconditions — verified at `d54cd9c5`

| Precondition | Verified how | State |
|---|---|---|
| NWPP-20 LANDED | `get_iso_config("NWPP")` returns five zones `NWPP-NW / OR / INLAND / EAST / SNV`; `ba_codes("NWPP")` returns the 17-tuple; `data/hydro.py` reads `ba_codes(iso)` (the scalar inverse is gone) | MET |
| NWPP-11's extract present | `data/raw/nwpp-hydro/{README.md, nwpp_hydro_monthly_923.parquet (7,212 rows), nwpp_hydro_monthly_923_flags.csv (601 rows)}` | MET |
| Pool frame for EIA-930 | `_ISO_TO_HOURLY_BA["NWPP"]` is the 17-member pool; `measured_monthly_hydro("NWPP", y)` and `measured_hydro_min_flow_level("NWPP", y)` return arrays | MET (no loader branch needed) |
| Published-inventory sources on disk | `data/raw/ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx` (hydrated this session; columns incl. `Water`, `Mode`, `Dam_Own`, `HUC`, `FC_Dock`); `data/raw/hilarri/HILARRI_v4.csv` (NID id, GRanD id, HydroLAKES id, HUC-12, USGS gage) | MET |

## 2. Gate A — THE BUDGET RECONCILES TO EIA-923 ANNUAL, BY PLANT (the charter's gate)

**Population rule.** The budget population for year *y* is exactly the loader's: EIA-923 rows with
`prime_mover == "HY"` whose `ba_code` is one of the 17 (`P923(y)`: 290 / 286 / 25). The envelope
population is EIA-860 `HY` in the 17 BAs (`P860`: 288, 35,799.5 MW). Pumped storage (`PS`, one
plant, 314.0 MW, BPAT) is **excluded by design** from both — it is storage, not inflow, and is the
storage block's object.

**Per plant-year test.** `budget_annual = Σ_{m=1..12} netgen_mwh[m]` (raw extract, negative months
RETAINED in the artifact) versus the extract's `netgen_annual_mwh` (EIA-923's own annual column).
**Pass iff `|budget_annual − netgen_annual_mwh| ≤ 1.0 MWh`** (EIA files whole MWh; 1 MWh is the
rounding tolerance and nothing else). Reported per plant-year with a status column:

| status | meaning | action |
|---|---|---|
| `RECONCILED` | passes the test | in the budget |
| `MISMATCH` | fails the test | **FLAGGED, NOT ADJUSTED** — the artifact carries both numbers |
| `NO_923_SERIES` | in `P860`, absent from `P923(y)` | **FLAGGED, NOT FILLED** (rule 13) — 2025 is the known case |
| `NO_860_NAMEPLATE` | in `P923(y)`, absent from `P860` | envelope falls back to the loader's own peak-monthly-average rule, flagged |
| `ALL_ZERO` / `NON_POSITIVE` | `budget_annual ≤ 0` | in the artifact, flagged; the loader drops it (documented behaviour) |

**Loader cross-check (the artifact is what the LP will actually see).** For each complete year,
`load_hydro_budget("NWPP", y).monthly_energy` must equal the artifact's monthly series **clipped at
zero** for every plant the loader keeps, to 1e-6 MWh; the MWh removed by the loader's negative-month
clip and the plants it drops are reported as a number, not hidden.

**Predictions (P1–P3):** P1 — every 2023/2024 plant-year reads `RECONCILED` (same source file, same
columns; a `MISMATCH` would be a defect in the extract, not in the source). P2 — the loader keeps
280 of 290 / 286: the 7 / 3 `all_zero` plant-years and the all-negative plants are the drop. P3 —
2025 carries 25 `RECONCILED` and 263 `NO_923_SERIES`.

## 3. Gate B — the power envelope, and the 2025 posture

**Envelope.** `max_mw` = EIA-860 nameplate (`P860`), nothing else; `min_mw = 0` — **no floor is
stamped by this lane**, because a floor needs a driver, a window and a forward story (rule 17
`[R-FLOOR-WINDOW]`) and the measured Q95 min-flow level is reported under §5(c) as evidence for the
W4/W5 posture decision (`hydro_min_flow_floor`, default-off), never armed here. The 31 `cf_over_1`
plant-years NWPP-11 flagged are listed with their MW and energy share as an envelope inconsistency
under rule 14 — surfaced, not clipped.

**2025 (the early-release year) — decision rule, with the §0 caveat that the level numbers were seen
first.** Nothing is filled in the artifact. For the W4 solve the lane recommends the posture that
uses the most measured 2025 information with no invented number, chosen by this rule: repin
(`eia930_monthly=True` on top of `backfill_year=2024`) is recommended **iff** the pooled 930/923
ratio is stable across the two complete years (|Δratio| ≤ 0.01) and the monthly r ≥ 0.95 in both —
i.e. the 930 pool is the same physical series on a stable basis, so a 2025 level taken from it is
on the 923 basis to within that stable ratio, which is then DECLARED at full magnitude. Otherwise
backfill alone, with the like-for-like 25-plant wetness (+6.1 % / +7.5 %) declared as the bias.

## 4. `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NWPP"]` — the admissibility rule for an entry

An entry is written **only if all three hold**: (i) a **published instrument** governing that
project's water (treaty, IJC/international order, FERC licence article, Corps/Reclamation operating
plan, court-ordered operation) has been **read in this session**; (ii) it states the period over
which the project's energy may be reallocated **in words** (the St. Lawrence precedent) or gives a
pondage / elevation band whose conversion to hours needs **only published numbers** (the Niagara
precedent); and (iii) rule 19 `[R-ONE-MECH]`: the plant is **not** in the hydraulically-coupled
chain NWPP-36 will govern — a coupled plant's within-period freedom is set by the coupling rows,
and a period entry stacked on it would be two mechanisms for one phenomenon.

**Candidates to examine, listed before any is read:** the Columbia River Treaty (1961/1964) and its
2024 agreement-in-principle; the Pacific Northwest Coordination Agreement (PNCA); the Mid-Columbia
Hourly Coordination Agreement (the seven mid-Columbia projects); the Hanford Reach Fall Chinook
Protection Program / Vernita Bar Agreement (Priest Rapids); the Columbia River System Operations
Record of Decision (2020) and its lower-Snake minimum-operating-pool provisions; the IJC Kootenay
Lake Order (1938); the FERC licences of Boundary (P-2144), Rocky Reach (P-2145), Wells (P-2149),
Priest Rapids (P-2114), Rock Island (P-943), Hells Canyon (P-1971), Pelton Round Butte (P-2030),
Skagit (P-553). A document that cannot be retrieved is recorded with its URL and status and
**yields no entry** (no value from memory).

**Prediction P4:** the entry set is **EMPTY** — the mainstem and lower-Snake instruments state flow,
elevation and spill conditions, not energy conservation periods, and the plants they govern are in
NWPP-36's chain (condition iii); the independent tributary projects' periods live in unretrieved
FERC licence articles. An empty set is a complete outcome.

## 5. The four §2.7 constraints — measurement definitions (NWPP-36's specification)

All four are measured on committed data; the only external reads are instrument texts for (c) and
published hydrological references for (a), each recorded with URL and status.

**(a) Hydraulic coupling down the mainstem.** Chain membership is READ from the ORNL EHA FY2024
`Water` field (a published federal inventory): a plant is on the US Columbia mainstem iff `Water`
∈ {`Columbia River`, `Columbia And Snake Rivers`, `Snake And Columbia Rivers`} and its `HUC` is a
Columbia mainstem HUC; ordered upstream→downstream by the published dam sequence, cross-checked
against latitude/longitude. Tributary chains (Snake, Pend Oreille/Clark Fork, Kootenai, Flathead,
Spokane, Skagit, Lewis, Cowlitz, Deschutes, Willamette) are tabulated the same way. Reported: MW
and 2023/2024 energy of the chain, as a share of the 35,799.5 MW / ~107 TWh; the desk's "eight ≥ 1 GW
plants" list re-checked against the river field (a ≥ 1 GW plant NOT on the mainstem is reported as
such). What the mechanism must express: the identity `outflow(upstream, t) → inflow(downstream,
t + τ)`; the published travel times are sourced if retrievable and otherwise named as NWPP-36's to
source.

**(b) Within-month shaping the monthly budget cannot see.** On the pooled `NG: WAT` hourly series
and the four largest hydro BAs (BPAT, CHPD, GCPD, DOPD) per calendar month: (i) diurnal amplitude =
mean over days of (daily max − daily min) ÷ monthly mean MW; (ii) day-to-day signal = CV of daily
energy within the month, and the first-week ÷ last-week daily-energy ratio (the freshet ramp);
(iii) the budget's granted freedom = nameplate-hours ÷ budget (= 1/CF) for the mainstem plants,
against the measured hourly max ÷ monthly mean; (iv) the pooled series' Q5 / Q95 hourly levels per
month (the two-sided envelope the existing `hydro_dispatch_envelope` / `hydro_min_flow_floor`
machinery would stamp).

**(c) Non-power constraints (fish / flow / spill) and what published instrument sets each.** An
instrument table (name, issuer, date, what it constrains, which plants, URL, retrieval status) and
the magnitudes measurable on disk: the mainstem run-of-river plants' April–August capacity factor
against their nameplate-hours (the spill-season signature), and the pooled Q5 sustained level as
the size of the "minimum release" the pure-budget LP is free to ignore. Any published foregone-
generation figure is quoted only if retrieved, with its URL.

**(d) Storage vs run-of-river and how much of 35,799.5 MW is dispatchable.** EHA `Mode` by MW and
plant count over the 288; HILARRI reservoir linkage (GRanD / HydroLAKES / NID id present) as the
completion for Mode-NaN plants, following `curate_hydro_plant_modes.py`'s documented rule but **not
curating** (the `hydro_ror_split` classifier arm is a W4/W5 posture, not this lane's); and the
measured pooled hourly range (P95 − P5) ÷ nameplate as the empirical shaped fraction.

## 6. What this lane does NOT do

No `src/` edit (if the loader needed an NWPP branch the lane would STOP and route — §1 shows it does
not); no `ScenarioConfig` field (NWPP-36's single exception under gate G8 as amended is not this
lane's); no other region's hydro rows; no solve; no shared record (plan, ledger, `nwpp.md`,
matrix shard — the desk writes those from the FINDING's `## Log entry`). The artifacts land under
`data/raw/nwpp-hydro/` beside NWPP-11's extract, with README rows, and are regenerable by one script.
