# PRECOMMIT — SPP-58: the wind gross-up the LP cannot re-curtail

**Session:** ercot-265 (continued into the SPP lane after ERCOT's own object was found
data-blocked). **Date:** 2026-09-09. **Branch:** `claude/ercot-uri-february-fuel-baynmi`.
**Lane:** SPP-DESK. **Keeper under test:** `2026-09-09-spp-51c-oversupply-curtailment`
(bundle `results/calibration/spp51c_oversupply`). **Nothing solved at the time of writing.**

Written and pushed BEFORE any arm is built or solved (rule 29 `[R-SCREEN]`).

---

## 1. Why this lane, and the rule-28 clearance

SPP is one of two ISOs reading **NOT-YET**, on four criteria: `fuelmix` (2024),
`price_mean` (2025), `price_shape` (2025), `price_tail` (2023/24/25). C3c is the only
LEDGERABLE criterion, so **if the other three close, a lone C3c reads CAVEAT and SPP reads
CALIBRATED** (rubric v3.3). That is the prize.

**This is the successor SPP's own record already named and left open.**
`FINDING-spp-51b-2026-09-09-session-b.md` **R-1**, verbatim: the unattributed mid-load wedge
*"is most likely the PRIMARY LANE'S OBJECT (the flat wind gross-up) … the LP runs 10.3–11.5 GW
of thermal in exactly the hours the market was curtailing wind. **A successor should test that
attribution before anything else**"*, with the stated prerequisite *"a lane with the keeper's
own `hourly/` sidecars"* — which are committed. The matrix cell
`vre_reference_rate_curtailment_grossup` reads **U**: footprint measured at zero LP by SPP-51b,
**no arm ever solved, no verdict minted**. Nothing here re-tests an `R`/`I`/`G` cell.

## 2. THE OBJECT, measured at zero LP on committed artifacts

`renewable_bound_provenance("SPP", y, "wind")` = **`forecast_uncurtailed`** in 2023/2024/2025:
the delivered EIA-930 profile is grossed up by SPP's measured reference curtailment rate,
`uncurtailed_cf = delivered_cf / (1 − rate)`. The construction's own stated precondition
(`renewables.py`) is *"real headroom, **endogenously re-curtailed**"*.

**It is not re-curtailed.** SPP 2024:

| quantity | value | source |
|---|---:|---|
| measured curtailment share (both legs metered) | **10.56 %** | `spp_wind_curtailment_annual.csv` (SPP MMU ASOM 1,483 MW ÷ GenMix 12,559 MW) |
| model re-curtailment (potential 120.9925 → dispatch 120.723 TWh) | **0.22 %** | keeper `hourly/class_hourly_2024.parquet` |

**A 48× miss on the mechanism's own precondition**, and it lands as energy:

| fuel | model TWh | actual (EIA-930) | Δ |
|---|---:|---:|---:|
| **wind** | **120.723** | **109.317** | **+11.406** |
| gas (all classes) | 76.941 | 83.208 | −6.267 |
| coal | 66.373 | 72.437 | −6.064 |

**THE ATTRIBUTION R-1 ASKED FOR, and it closes:** 120.9925 × (1 − 0.1056) = **108.2 TWh**, i.e.
curtailing at SPP's own measured rate removes **−12.5 TWh** of wind, against a measured thermal
shortfall of **−12.33 TWh**. The C1-2024 failing row is `ST_GAS` at **−8.227 TWh**, the largest
single share of it.

**THE CAUSE IS WRITTEN IN THIS REPO'S OWN CODE.** `renewables.py` explains why NYISO is kept
OUT of `_UNCURTAILED_FALLBACK_ISOS`: *"a NYCA-wide annual rate exists but is the wrong
instrument — **its curtailment is locally driven and the reduced network can't re-curtail a
gross-up**"*. SPP is IN that set, and its curtailment is locally driven in exactly the same way
(SPS / Texas-Panhandle and Oklahoma pockets). The 2-zone reduction collapses those constraints,
so the LP has no mechanism to spill and takes all 11.4 TWh at its −$26/MWh PTC bid — SPP-51b
measured wind AT its bound in **99.92/99.92/99.97 %** of hours.

## 3. THE MECHANISM — SPP's own instance of an ERCOT-precedented structure

`curtailment_share.py` already solves the identical problem for ERCOT (WP-B), and its docstring
states SPP's case verbatim: a zonal reduction collapses a wind corridor's binding **nodal**
transmission into one pipe that almost never binds, *"so the LP dispatches West/Panhandle wind
and solar well above what ERCOT's real grid delivered"*. The reduced-form stand-in is a
curtailment ceiling on the CF upper bound:

```
ceiling_frac(t) = 1 − depth × congestion_share(net_load_decile(t), hour_of_day(t), season(t))
```

**Rule 25 `[R-ISO-SCOPE]`: NOTHING TRANSFERS.** ERCOT's `depth` (0.1004 wind) and its share
table are ERCOT's. SPP enters as `U` and derives **its own** parameters from **its own** market:

- **SHAPE** — from SPP's own RTBM binding-constraint archive, `data/raw/spp-binding-constraints`
  (`RTBM-BC-YEARLY-2023/2024` + 12 monthly 2025 files; 5-minute `Constraint Name` /
  `Shadow Price` / `Monitored Facility`). Binned exactly as ERCOT's: net-load decile × hour ×
  season. Built **only** from measured binding incidence — never a curtailment volume, never a
  price residual.
- **LEVEL** (`depth`) — one per-tech coefficient centred on SPP's **published** measured
  curtailment MW (SPP MMU ASOM, already committed), the same construction ERCOT's uses.

**⚠ AVAILABILITY CORRECTION, and it matters beyond this lane.** §5.7 queue item 4 records the
binding-constraint archive as **token-blocked** (`portal.spp.org` requires `X-SPP-UI-Token`,
r#3 2026-09-06) and therefore records SPP-54/SPP-57 as un-issuable and owner card **P1**'s
ranking test as having *"no measured input"*. **The archive LANDED 2026-09-08** (69 MB on disk,
2023–2025 complete). This PRECOMMIT does **not** touch P1 — a reduced-form ceiling is expressly
the stand-in for a topology we are NOT adding, which is why ERCOT has one — but the desk should
know its blocker is gone.

## 4. SCREEN YEAR, NAMED NOW AND ON FOOTPRINT ONLY — **2024**

Rule 29(a). The mechanism's own measured driver quantity, in SPP's published data and its own
congestion archive, neither of which is a model residual:

| year | published curtailment | measured share | binding rows (rate) | intervals w/ binding |
|---|---:|---:|---:|---:|
| 2023 | 1,097 MW | 8.49 % | 438,418 (11.91 %) | 91.75 % |
| **2024** | **1,483 MW** | **10.56 %** | **504,804 (12.35 %)** | 94.21 % |
| 2025 | 1,382 MW | 9.90 % | 511,011 (9.24 %) | 94.26 % |

**2024 is the largest on the mechanism's own footprint** — the published curtailment MW and
share both peak there, and so does the binding-row rate. **DECLARED HONESTLY: 2024 is also the
C1 failing year, so footprint and residual coincide. The selection basis is the footprint** —
SPP's MMU published 1,483 MW independently of this model — and had they diverged, the footprint
would still have chosen. Rule 29 forbids gating the screen on the target residual, and the
gates in §5 are structural only.

## 5. PRE-REGISTERED GATES — STOP gates, structural, none on the target residual

The screen **may kill the arm and may never promote it**.

- **G-1 (identity, zero-LP):** off the flag the fleet/bound arrays are `array_equal` to the
  keeper's. A non-identical control is a stop-the-line defect, not a result.
- **G-2 (reach):** the ceiling reduces 2024 model wind dispatch by **8–16 TWh** — bracketing the
  −12.5 TWh the measured rate implies. Below 8 the mechanism is inert and the arm dies; above 16
  it is over-reaching and the arm dies.
- **G-3 (allocation):** the removed wind is concentrated, not spread — the top net-load-trough
  decile carries a strictly larger share of the reduction than the flat gross-up's uniform
  1.1068× implies. A flat reduction is the defect wearing a different hat and FAILS.
- **G-4 (no new forcing):** slack and dump stay exactly 0.0, and no `min_gen` floor gains
  binding hours. Displaced wind must be picked up by economic dispatch, not by forcing.
- **G-5 (no load-bearing regression):** no non-target load-bearing criterion (C2, C4, C6) flips
  PASS → FAIL.

**Sealed predictions** (scored in the RESULT whatever they do):
- **P1** wind 2024 falls into 108–113 TWh; ST_GAS rises and closes most of its −8.227 TWh.
- **P2** C3a-2025 moves DOWN (thermal displacing zero-cost wind at mid load should raise, not
  lower, prices — so **P2 is the prediction most likely to be wrong, and it is stated before the
  solve precisely for that reason**). SPP-51b's decomposition says the mid-load band is +26–40 %
  rich; if this arm makes it worse, that is a finding, not a reason to retune.
- **P3** C3c does not improve materially — SPP-55 adjudicated the tail a 5-minute object no
  hourly lever reaches. Any large C3c move is a red flag to investigate, not a win.
- **P4** the arm is NOT automatically a keeper; a structurally-correct mechanism stays in even
  if gates regress (rule 1 `[R-STRUCT]`), and the owner decides promotion (rule 31).

## 6. G-DRIFT (rule 29(b)) — recorded before the arm is solved

Keeper `spp51c_oversupply` `git.sha` = **`86e45462`**. The control is the keeper's **committed**
bundle (G-CTRL form 4); **no control solve will be spent** unless the drift audit finds a LIVE
hunk on SPP's backcast solve path, in which case only the screen year is re-run. The audit is
run and its classification appended to this file BEFORE the arm is launched.

## 7. Governance

Rule 32 `[R-SHARD]`: the parent solves nothing; the screen runs in a shard pinned to this
PRECOMMIT's full 40-char SHA, one year, own out-dir, own branch, reporting numbers rather than
pushing a bundle. Rule 16 `[R-ALLYEARS]`: the screen bundle is a throwaway probe, never
registered; the full span 2023–2025 runs as ONE invocation and ONE bundle only if the screen
clears. Rule 31 `[R-RETAIN]`: bundles gitignored, never `rm`'d, and the promotion question goes
to the owner before the session ends. Rule 22: 2023/2024/2025 are training tier — **no
`--holdout-authorized`**, and SPP holds no `complete` marker so no other year is touchable.
Rule 28: `vre_reference_rate_curtailment_grossup` and the new SPP cells are stamped in SPP's own
shard, in this session, whatever the outcome.
