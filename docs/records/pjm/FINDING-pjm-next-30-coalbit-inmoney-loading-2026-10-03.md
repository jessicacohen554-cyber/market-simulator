# FINDING — PJM-NEXT-30: COAL_BIT in-money loading, decomposed per plant (zero LP)

Lane `PJM-NEXT-30` (branch `claude/pjm-next-30`, from `f81d0c40`). **Zero LP.** Keeper unchanged:
`2026-10-02-w0-pjm-fix2` (bundle `results/calibration/w0_pjm_span`, 2019–2025). Successor to PJM-NEXT-29, whose
post-hoc S2 re-pointed the COAL_BIT C1 operand to deep-in-the-money loading: model COAL_BIT output ÷ its available
`cap_mw` is 0.98 / 0.95 / 0.99 / 0.92 / 0.81 / 0.80 / 0.94 (2019–25), against CAMPD ÷ the same `cap_mw` at
0.90 / 0.88 / 0.91 / 0.83 / 0.78 / 0.80 / 0.89.

§1 (definitions and readings) is committed **before** any number in §2 exists. Nothing in §1 is re-read after the
probe runs.

## §1 Readings, fixed ex ante

### Population and quantities

- **Hours `H_y`:** the NEXT-29 S2 hours, real implied HR ≥ 10 (real PJM DA LMP ÷ NEXT-11 delivered gas;
  `_pjmnext29_coalbit_bins.HI_HR`). Unchanged definition, so the totals reproduce NEXT-29 S2.
- **Plants:** COAL_BIT plants in the keeper's `unit_marginal_<y>` with a bench CAMPD record (the NEXT-29 S2 set).
  Model grain is the plant (tranches summed), so "per unit" is per plant. CAMPD unit-level hourly
  (`data/raw/campd-unit-level/<ST>_<y>.parquet`) is used only for the unit-dark split below.
- Per plant `p`, hour `h`:
  - `M` = model P1 MW (Σ tranches);
  - `K` = model available `cap_mw` (Σ tranches; it already carries the keeper's outage windows and availability);
  - `A` = bench CAMPD MW (CAMPD hourly shape rescaled to the EIA-923 annual net; net basis, same as NEXT-29).
- **Revealed capability** from `A`, computed over ALL hours of the year (not only `H_y`):
  - `Y` = annual p99 of `A`;
  - `W(h)` = max of `A` over the 168-hour block of hour-of-year containing `h` (block = ⌊h / 168⌋).
- **Gap** `D = M − A`, split into four ordered pieces that sum to `D` exactly:
  1. **basis** = `M − min(M, Y)`: model output above the plant's whole-year revealed maximum. This is the cap_mw
     basis question (net vs gross, nameplate vs seasonal rating).
  2. **derate** = `min(M, Y) − min(M, W)`: above this week's revealed maximum but within the year's. These are
     partial derates and outages lasting a week or more that the keeper's windows do not carry.
  3. **offline** = `min(M, W) − A` in hours with `A = 0`: the plant is dark this hour but ran this week. These are
     short full outages, or decommitment.
  4. **loading** = `min(M, W) − A` in hours with `A > 0`: the plant is running, below this week's own maximum. This
     piece holds reserve and regulation headroom, economic backdown, and ramp or offer-curve loading.
- **Dispatch-independent twin.** The same four pieces with `K` in place of `M`. This is the capability overstatement
  that would bind if the model ran at cap. Reading R2 uses both.
- **Unit-dark split** (inside pieces 2 + 3): the share of the piece's MW-hours that falls in plant-hours where at
  least one CAMPD unit of the plant has `opTime = 0` (whole unit dark), rather than all units running at reduced
  output. Plants are matched by `facilityId` = EIA plant code; non-matching plants are reported as unmatched.
- **Reserve bound** (2019–21 only, the years with IMM rows on one basis): coal-held reserve MW =
  RTO average Tier-1 MW × the coal Tier-1 MW share, plus RTO average Tier-2 MW × the coal Tier-2 share, plus
  coal regulation MW-h ÷ 8760. Sources: `results/phase0/pjm/_pjmco_0c_som_sec10_reserve_by_unit_type.csv`
  (IMM SOM §10, cited per row).

### Readings

| id | question | decision rule |
|---|---|---|
| R1 | Which piece carries the gap? | A piece is **dominant** if it holds ≥ 50 % of Σ `D` over `H_y`, pooled over 2019–21. Otherwise the gap is **mixed**, and the two largest pieces are named. |
| R2 | Which piece separates the years? Fail set F = {2019, 20, 21, 22, 25}; pass set P = {2023, 24}. | For each piece, compute its MW per MW of `K` in each year, then take the mean over F minus the mean over P. If the `M`-based piece differs by ≥ 0.03, the piece is **year-discriminating**. Then: if the `K`-based twin also differs by ≥ 0.03, it is **level** (the real quantity differs by year); if the twin differs by < 0.03, it is **binding-only** (the same overstatement every year, consumed only when the model runs coal at cap). |
| R3 | Is the gap concentrated in a few plants? | **Concentrated** if the top-10 plants by `D` (pooled 2019–21) carry ≥ 60 % of the gap, AND the dominant (or largest) piece at those ten is the same as fleet-wide. |
| R4 | Can reserves explain the loading piece? | Compare the reserve bound with the loading piece's MW (`H_y`-mean) in each of 2019 / 20 / 21. If the bound is < 25 % of the loading piece in every one of those years, reserves are **not the operand**, consistent with closeout 0c. |
| R5 | Is there an admissible arm? | **Chartered only if** the R1-dominant (or larger mixed) piece is year-discriminating under R2 AND it maps to a measured quantity that could be produced for a forward year (rule 13). The pieces map as follows: <br>• **basis** → a rating-basis input. The candidate cells are `coal_nameplate_summer_derate` (U) and `seasonal_capacity_basis` (K, already armed). <br>• **derate** / **offline** with unit-dark ≥ 50 % → outage-window coverage. Same-year CAMPD windows are a rule-13 overlay. The `unit_outage_*` family is K, so the census must name the missing windows. <br>• **derate** with unit-dark < 50 % → `unit_partial_outage_windows`. This was screened by R-PJM 2026-09-24: the deriver emits 0 because of the revealed-outage filter, so the piece would mean a detector build. <br>• **loading** → NOT an availability defect. Pinning loading to observed output is rule-13 forbidden. Route it to the offer family (all adjudicated), so NOT CHARTERED. |

Every R5 branch is a routing statement, not a solve. If an arm is chartered, its PRECOMMIT follows this FINDING
and carries the Tait 55248→2847 remap as the rule-14 rider (closeout census §6).

## §2 Result

_(pending — written after the probe runs)_
