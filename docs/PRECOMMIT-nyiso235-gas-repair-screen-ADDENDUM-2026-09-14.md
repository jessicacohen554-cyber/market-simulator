# ADDENDUM — nyiso-235: G-DRIFT re-verification and the two PRE-SOLVE gate results

**Session** nyiso-235 · **Date** 2026-09-14 · **Parent**
`docs/PRECOMMIT-nyiso234-gas-repair-screen-2026-09-14.md`, which this document does **not** amend:
the screen year, the gates and the not-a-gate list stand exactly as pre-registered. Written and
pushed **BEFORE the arm solves**, per rule 29 `[R-SCREEN]` (1) and (b).

This addendum exists because rule 29(b) requires the **G-DRIFT** audit to be taken against *the
head the arm actually solves on*, and nyiso-235's head is not nyiso-234's. It records what changed
in between, and it decides the two gates that are computable with **zero LP**.

---

## 1. G-DRIFT, RE-RUN AT THIS SESSION'S HEAD — the audit is materially larger than nyiso-234's

**Keeper `git_sha` `0ef1fac3` → this session's head `dd33fc270150f211bfa74b13b08fc2d7a971a0bb`.**

The parent PRECOMMIT §5 recorded "zero LIVE hunks in `src/market_sim/`", and at nyiso-234's head
that was true of a handful of files. **It is not the same diff here.** Between the keeper and this
head the repository merged a week of other lanes — the NWPP region onboarding (lane NWPP-20), PJM
Route-A coal work, CAISO intake — and the solve-path diff is:

```
git diff 0ef1fac3 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
→ 37 files changed, 2,144 insertions(+), 58 deletions(-)
```

Every hunk is classified below. **The verdict is unchanged — ZERO LIVE hunks for NYISO — but it is
now carried by measurement rather than by the small size of the diff.**

### 1.1 The classification

| class | files | rule 29(b) INERT ground |
|---|---|---|
| **NWPP region onboarding** — new `"NWPP"` keys in dispatch dicts, new `_nwpp_*` functions, `_nwpp_config` | `campd.py`, `renewables.py`, `zone_assignment.py`, `eia930/{__init__,demand,envelopes,frames}.py`, `iso_configs.py`, `interchange/{spec,registry}.py`, `constants.py`, `capacity_market.py`, `fuel_trajectories.py`, `transmission_expansion.py`, `scripts/lib/*/nwpp.py` | **another ISO's branch** |
| **Forecast-only path** | `capacity_market.py`, `fuel_trajectories.py`, `transmission_expansion.py`, `confirmed_retirements/`, `nuclear_license_status/`, `load_forecast/` | a `mode="backcast"` run never enters capacity evolution / capacity market |
| **Default-off new flag** — `committed_band_measured_basis: bool = False` (PJM Route-A), its `offer_curves.py` functions and its `legacy_bins.py` / `assembly.py` call sites | `scenarios.py`, `offer_curves.py`, `legacy_bins.py`, `assembly.py`, `run_calibration*.py` | **default-off AND absent from the keeper's recipe** (verified: not in `run_config.json`; frozen cache-key drop value `"False"`, so the keeper's key does not move) |
| **Dead read seam** — new module, **zero importers** in `src/market_sim`, no `ScenarioConfig` flag; its own docstring: *"There is no LP consumer yet… Nothing here changes a solve."* | `coal_stocks.py` | not on the solve path at all |
| **Shared refactor, value-identical for 1:1 regions** — `ISO_TO_BA_CODE.get(iso)` → `ba_codes(iso)`, `== code` → `.isin(codes)`, 13 call sites | `fleet/{models,eia860,campd_bins}.py`, `hydro.py`, `zone_assignment.py` | **verified empirically**, §1.2 |

### 1.2 The three shared-code risks, verified rather than argued

The refactor and two dict edits are the only hunks that touch code NYISO's backcast executes. Each
was checked by measurement, not by reading its comment:

1. **`ba_codes` refactor.** `ba_codes("NYISO") == ("NYIS",)`, so `.isin(("NYIS",))` selects exactly
   the rows `== "NYIS"` selected. Verified for all seven 1:1 regions; only NWPP is many-to-one.
   NYISO's hydro fleet (the largest consumer, via four `hydro.py` call sites) is therefore
   unaffected.
2. **New NERC admission predicate.** `ISO_NERC_REGION_ADMISSION == {"NWPP": "WECC"}` — a single key.
   NYISO is absent, so it admits on the BA code alone, byte-identical to before.
3. **New `_egrid_boundary_hr_repairs()` entry.** The accepted set went `{55641: 6.880}` →
   `{7350: 6.918, 55641: 6.880}`. Plant **7350 is Coyote Springs, balancing authority PGE
   (Oregon)** and plant 55641 is MISO; **neither is among NYISO's 1,088 plants.**

### 1.3 The deletion census — the check that cannot be gamed by reading only additions

Every deleted line in `src/market_sim` between the two shas is one of: the `ba_codes` refactor of
§1.2(1); a docstring or comment; or a set literal that gained `"NWPP"` while **keeping NYISO's
membership unchanged** (`_UNCURTAILED_FALLBACK_ISOS`, which NYISO was never in and still is not;
`_EIA860_BA_ZONE_ISOS`, which NYISO was in and still is). There is no other deletion.

**The only four occurrences of the string `NYISO` in the entire `src/` diff are two comments and
that one set literal.** No NYISO builder, offer curve, floor, reserve family or interchange spec is
touched.

### 1.4 The decisive empirical confirmation

The repo's own per-ISO solve-surface machinery (capx D79) answers this question directly, and it
agrees:

```
moved_rows("NYISO")                    → {}        (0 rows moved vs the frozen declaration)
surface_stamp("NYISO").fingerprint     → bd2b4657f9b5df7e   rows 210   moved {}
keeper run_config.solve_surface        → bd2b4657f9b5df7e   rows 210   moved {}
```

**The keeper's own recorded fingerprint reproduces byte-identically at this head.** (ERCOT and
CAISO *do* carry moved rows — `NUCLEAR_MONTHLY_CF_BY_YEAR`, `STATE_CARBON_PRICE_BY_ISO` — which is
those lanes' business under rule 25 `[R-ISO-SCOPE]` and is reported here, not touched.)

**CONCLUSION: G-DRIFT finds ZERO LIVE hunks. Rule 29(b) form 4 is VALID — the keeper's committed
bundle is the control, and NO control solve is spent.** The control numbers are already on disk:
the slim committed keeper carries `hourly/system_2022.parquet`, `class_hourly_2022.parquet`,
`class_band_hourly_2022.parquet` and `reserve_family_2022.parquet`.

## 2. The footprint reproduces the PRECOMMIT exactly — screen year 2022 stands

Re-measured at this head by `scripts/probes/_nyiso234_gas_repair_footprint.py`, old inputs taken
from the pre-repair commit `1955b2a6`:

| year | footprint (Σ&#124;Δ&#124;) | hours moved | max Δ |
|---|---:|---:|---:|
| **2022** | **3,983** | 1,464 (16.7 %) | **+31.57** |
| 2025 | 1,354 | 2,928 (33.4 %) | +0.97 |
| 2024 | 1,069 | 3,672 (41.9 %) | +7.91 |
| 2023 | 597 | 3,600 (41.1 %) | +0.71 |

Identical to PRECOMMIT §2 in every cell. **Screen year 2022, on footprint, 2.9× lead.**

## 3. G-1 IS DECIDED NOW — it is an input-side gate, and it **PASSES**

G-1 is written over "**the delivered gas array**", not over any LP output, so it needs no solve.

The delivered array for 2022 moves in **1,464 hours spanning 2022-11-01 … 2022-12-31 — one
contiguous 61-day run.** That is wider than the Elliott days, and the reason is structural and
declared: the daily construction is **mean-preserving against the monthly anchor**, so repairing any
day in a month renormalizes that whole month.

The question G-1 actually asks is whether that footprint is confined to what the repaired inputs
touch. Measured on the inputs themselves:

| input | what it touches in 2022 |
|---|---|
| `transco_z6_ny_daily.csv` | **10 dates, in months 11 and 12 only** — 11-17, 11-18, 11-21, 11-22, 12-22, 12-23, 12-27, 12-28, 12-29, 12-30 |
| `gas_basis_by_iso_month.csv` (NYISO) | **months 11 and 12 only** — 2022-11 `0.7490 → 1.3122`, 2022-12 `3.5705 → 5.5376` |

**Hours moved outside months 11–12: `0`.** The array moves in exactly the two months the repaired
inputs touch, and in none of the other ten. **G-1 PASSES.**

*Recorded because it is the sort of thing that must not be settled after seeing a result:* the
61-day span was measured **before any LP ran**, and the reading of "touched dates" as "the months
the mean-preserving anchor touches" is fixed here, in advance, on the construction's own
documented behaviour — not chosen to accommodate an outcome.

**Rule 25 `[R-ISO-SCOPE]`, re-verified on the shared basis file:** of 940 rows, **30 moved and every
one is NYISO** (0 added, 0 removed, no other ISO's row touched).

## 4. G-3's pre-solve prediction, registered BEFORE the arm

G-3 compares the realized price response against what `Δmc` admits. That prediction is computed now
so it cannot be fitted afterwards. Over **Dec 22–23** the delivered gas delta is **mean +29.625,
max +31.566 $/MMBtu**, giving, at each class's base heat rate:

| class | base HR (MMBtu/MWh) | Δmc mean ($/MWh) | Δmc max ($/MWh) |
|---|---:|---:|---:|
| CC_REGULAR | 7.000 | +207.38 | +220.96 |
| CC_CHP | 7.500 | +222.19 | +236.75 |
| CT_CHP | 9.000 | +266.63 | +284.10 |
| ST_GAS | 11.000 | +325.88 | +347.23 |
| CT_PEAKER | 13.000 | +385.13 | +410.36 |

**A realized load-weighted price rise on those days that sits inside this band is a repricing; one
that materially exceeds the CT_PEAKER ceiling is the LP amplifying, and STOPs the arm.**

One thing stated at the gate rather than discovered later: the repaired Dec 23 delivered gas
(**$39.62/MMBtu**) is **above the measured dual-fuel oil-parity cap of $24.85/MMBtu**, and
`dual_fuel_switching` is CLOSED in this model (nyiso-179). The keeper does carry
`dual_fuel_oil_daily_parity` and `dual_fuel_oil_reattribution`, so the oil-parity channel is armed;
whether it binds in these hours is a **reported observation of the arm**, not a gate, and not a
reason to touch anything.

## 5. What is unchanged

The screen year, all five gates, the not-a-gate list (C3a / C1 / C3b and every other criterion),
and the commitment that a STOP will not be rescinded and no gate re-cut after seeing a number —
**all exactly as the parent PRECOMMIT wrote them.** No `ScenarioConfig` field moves; the arm is the
keeper's recipe replayed byte-faithfully on 2022 via `scripts/replay_keeper.py`, with the repaired
data as the **only** difference.

## 6. Execution

Rule 32 `[R-SHARD]`: the parent runs zero LP. ONE shard, ONE year (2022), pinned to this document's
commit SHA, pushing its bundle per rule 34 `[R-SHARD-PROMOTABLE]` (a) — `.gitignore` negation plus a
**plain** `git add`, `dispatch/2022_P1.parquet` included. The negation form rule 34(a) prescribes
was **verified against this repo's `.gitignore` before launch** (`git add --dry-run`: the one-line
`!results/calibration/<out-dir>/**` does re-include both `dispatch/` and the bundle-root
`system.parquet`, despite line 651's directory exclusion).
