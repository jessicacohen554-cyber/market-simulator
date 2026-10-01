# RESULT — R-SOCO-B2: SOCO 2019–2025 on the repaired BA boundary — PROMOTED

**Keeper → `2026-09-25-r-soco-b2-boundary`** (bundle `results/calibration/rsocob2_boundary_span`). It was promoted
2026-09-25 on the owner's standing ruling: "Is this a recommended keeper candidate? If so plz promote. If
structural integrity improves but gates regress that may still be a keeper."

**Outgoing keeper.** `2026-09-24-r-soco-corrected-inputs` (2023–2025) was pruned under rule 35. Its registered year
union {2023, 2024, 2025} is covered, and 2019–2022 are added.

**Records.** `FINDING-r-soco-b2-boundary-2026-09-25.md`, `PRECOMMIT-r-soco-b2-2026-09-25.md`, and R-SOCO-B's
`PRECOMMIT-r-soco-b-2026-09-25.md`.

**Owner rulings.**
- (A) Repair the 2019 total-interchange sign.
- (B) PowerSouth joins on 2021-09-01.
- (C) Dated Gulf exit, at hour grain.

## 1. What was solved

There are seven year-isolated shards (rule 36), all at pinned `422915ca0efe89475800617de6b6e2a83a0dbc02`, running the
keeper recipe unchanged: every band is 1.0, and the five `--set` fields are true. Each shard pushed its full
bundle. The parent fetched and verified them, then archived the shards.

The legs, recorded as provenance only (rule 33(d)): 2019 `7fca4fc9`, 2020 `d62f8f1a`, 2021 `613c0a9a`, 2022 `0afec265`,
2023 `3f840189`, 2024 `7df3d192`, 2025 `dad5a322`. They were composed at zero LP with `rsocob_compose_span.py`,
followed by span shared inputs, `--restore-shared-inputs`, the diagnostics over 2019–2025, the DOF ledger (21
entries / 1 residual), `gen_soco60b`, `gen_rsoco` and `gen_rsocob` (both pass), and registration.

**Where the bytes are.** The composite (slim set + `hourly/`), its sidecar and its payload are on `main` via this
lane's PR. The per-year leg dirs are gitignored. Re-solving a leg costs ~10–15 min per year in its own shard.

**The four repairs were verified on every leg** (`rsocob_compose_span.py --check-only`):

| year | Gulf plants in the fleet | PowerSouth | demand, TWh |
|---|---|---|---|
| 2019 | 641 / 643 / 7715 / 55242 | — | **245.097** (R1) |
| 2020 | same | — | 231.593 |
| 2021 | same | 0 MWh Jan–Aug / 1,682.1 GWh Sep–Dec | 239.410 |
| 2022 | same; **2,759.0 GWh before the exit hour, 0.0 MWh from row 4637** | from Jan | 244.839 |
| 2023–2025 | none | from Jan | 239.625 / 249.506 / 252.590 |

## 2. Pre-registered expectations

- **E1 (2019–2022): HELD.** The Gulf capacity displaces CT_PEAKER and coal. Class moves against the R-SOCO-B legs,
  in TWh:
  - **2019:** CC_REGULAR +3.54, CT_PEAKER −2.45, COAL_PRB −2.69, COAL_BIT −0.88, ST_GAS −1.05.
  - **2020:** CC_REGULAR +2.65, CT_PEAKER −3.31, COAL_PRB −1.62, ST_GAS −0.82.
  - **2021:** CC_REGULAR +2.66, COAL_BIT −0.90, CT_PEAKER −0.87.
  - **2022:** CC_REGULAR +1.14, CT_PEAKER −0.80.

  Unserved is 0 in 2019–2024.
- **E2: HELD EXACTLY.** 2024 and 2025 equal the outgoing keeper, with max |Δ class TWh| of **0.0000**. 2023 equals
  R-SOCO-B's 2023 leg at **0.0000**. 2023 against the old keeper is the R2 effect already recorded in R-SOCO-B:
  CC_REGULAR −3.60, CT_PEAKER +2.14, COAL_PRB +0.86, ST_GAS +0.52 TWh.
- **E3: HELD, with no scope limit.** The `gen_soco60b` B1 check (930/923 fossil) reads 0.982 / 0.991 / 0.982 /
  0.985 / 1.002 / 0.981 for 2019–2024. For B2, 930 gas sits below 923 gas every year: 125.06 vs 129.08, 125.88 vs
  128.47, 120.99 vs 125.75, 130.64 vs 134.71, 129.59 vs 130.23 and 126.08 vs 129.54 TWh.
- **E4: HELD.** 2019 demand is 245.097 TWh, and PowerSouth is 0 in Jan–Aug 2021.
- **E5: HELD.** C3a/b/c are UNSCORABLE in every year, and C6 PASS.

## 3. Gates (`calibration_verdict.py`, rubric as registered) — no price claim

| criterion | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| C1 fuel mix | PASS | PASS | PASS | PASS | **FAIL** | PASS | skipped (preliminary 923) |
| C2 system volume | PASS | PASS | PASS | PASS | PASS | PASS | skipped |
| C3a/b/c price | UNSCORABLE | UNSCORABLE | UNSCORABLE | UNSCORABLE | UNSCORABLE | UNSCORABLE | UNSCORABLE |
| C4 dispatch corr | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| C6 governance | PASS | | | | | | |
| C8 forced share | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| unserved, MWh | 0 | 0 | 0 | 0 | 0 | 0 | 813.8 |

C4 gas / coal correlation: 2019 0.934 / 0.895, 2020 0.956 / 0.927, 2021 0.891 / 0.920, 2022 0.970 / 0.832.

**Determination: NOT-YET**, down from PHYSICALLY-CALIBRATED (PRICE UNSCORED). The only failure is **2023 C1
CT_PEAKER at +7.22 TWh** against a ±7.26 TWh tolerance, with share +3.0 pp against the 3 pp band. It is right at
the edge. It comes from R2 removing Gulf's 2,525 MW from 2023, which Gulf's measured exit makes correct. It is
byte-identical to R-SOCO-B's 2023 leg. This is a genuine root-cause lead (rule 14): SOCO's CT fleet is dispatched
too much once the boundary is right. It is not a reason to put Gulf back into 2023.

**Why this was promoted despite the gate regression (rules 1/14).** The supply boundary now matches the load
boundary EIA-930 measures, in every year and every hour. The four repairs are published records with zero free
parameters. The span grows from 3 to 7 years, and 2019–2022 pass every scored criterion.

## 4. Recorded, not repaired

- **2019 demand pair.** At the served hours 7148 / 7149 the model's zonal demand-with-interchange reads 22,976 /
  22,159 MW. The raw EIA-930 spike/dropout pair (35,329 / 6,913 MW, R-SOCO-B §1.1) is interpolated by the SOCO
  loader's standard fill. No new screen was added (rule 23).
- PowerSouth's Sep–Dec 2021 hydro budget is booked under `AEC` in EIA-923 (≤ 0.01 TWh).
- The 2025 unserved 813.8 MWh and the 2025 C1 skip are inherited unchanged from the outgoing keeper.
- `audit_keepers` E11: the composite meta's first-year `weather_year` (2019) and `gas_price_override` (2.57) are
  the 2019 leg's own per-year values. They are declared in the keeper shard and are not recipe changes.

## 5. Next lever (for the next lane)

The 2023 CT_PEAKER over-dispatch, at +7.22 TWh and +3.0 pp, is the whole NOT-YET. Take the lever from the SOCO queue
(`docs/mechanism-testing-matrix.md` §5.8) against the matrix cells. The candidates are the CT commitment / offer
structure. The offer-curve `peak` band channel is **not** a candidate here: SOCO has no price reference, so rule 1(c)
cannot identify it.
