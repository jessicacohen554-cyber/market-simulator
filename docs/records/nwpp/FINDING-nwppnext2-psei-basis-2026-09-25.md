# FINDING — NWPP-NEXT-2 item 4: PSEI's EIA-930 basis is a Colstrip double booking, and the Aug-2021 hole has a measured flag

**Lane:** NWPP-NEXT-2 · **LP spent in this finding:** zero · **Probe:** `scripts/probes/_nwppnext2_psei_basis.py`

## 1. The two questions, answered

**(a) Is PSEI's 1.21× EIA-930 / FERC 714 basis through 2020 a BA-boundary change or an EIA-930 artifact?**
It is an **EIA-930 artifact**: a double booking of PSE's share of Colstrip. It is not a boundary change.

| Measured (2019, 8,351 clock-aligned hours, FERC 714 at lag −1 h) | Value |
|---|---:|
| PSEI `Demand (Adjusted)` − FERC 714 PSE planning-area load | 4.897 TWh |
| PSEI `NG: COL` over the same hours | 4.228 TWh |
| Hourly corr(excess, `NG: COL`) | **0.927** |
| OLS slope / intercept | 0.903 / 129 MW |
| sd of the excess: raw → after removing `NG: COL` | 183 MW → **71 MW** |

- **PSEI books its Colstrip share as its own generation.** PSEI `NG: COL` is 4.475 / 2.163 / 0.003 / 0.000 TWh in
  2019 / 2020 / 2021 / 2022+. It stops at 2021-01-01, the same date as the basis change.
- **Colstrip sits in the NWMT BA, and NWMT books all of it.** NWMT `NG: COL` is 14.167 TWh in 2019, against CAMPD
  Colstrip (ORIS 6076) gross of 14.777 TWh. PSEI's 4.47 TWh is about 32 % of the plant, which matches PSE's ownership
  share.
- **PSEI's tie book still carries the same energy as an import**, so `D = NG − TI` counts it twice.
- **Why it is not a boundary change:**
  - FERC 714 PSE load is continuous across 2020/2021, at 2.78 GW mean.
  - PSEI's EIA-930 mean falls 3,383 → 2,753 MW, but no other pool member gains load at the boundary. BPAT is +0,
    SCL/TPWR are flat, and PGE/IPCO grow by their normal +90–115 MW.

**Pool consequence (rule 14):**
- The EIA-930 pool books Colstrip **1.3×** in 2019 and 2020.
- The LP's requirement is `Σ NG − GRID legs`, so it was over-asked by **4.48 TWh (2019)** and **2.15 TWh (2020)**.
- The C4 coal benchmark, the per-member EIA-930 sum, carried the same phantom coal.
- The 2020 FERC 714 fill was reconciled to that inflated basis at scale 1.19. On the corrected basis it is **1.06**.

**(b) Is there a measured flag for the 2021-08-02 → 08-15 defect?** Yes, and it needs no threshold.
- In **336** hours `Total interchange (Adjusted)` is NaN and `Demand (Adjusted) == Net generation (Adjusted)`
  exactly. The missing interchange was taken as zero, so the published "demand" is just PSEI's generation.
- It is **PSEI-2021-only**: the same test over all 17 members, 2019–2025, finds no other hour.
- The window runs 1,699 MW mean below FERC 714, a 0.570 TWh deficit.
- **It is energy-neutral for the LP.** The served export is `Σ(NG−D)`, so the system requirement `D + export`
  cannot see a demand-side error. The effect is purely zonal: 1.7 GW of PSEI load shows up as pool export instead of
  NWPP-NW demand.
- **Also found:** a rule-19 drift. `curate_zonal_shares.parse_nwpp_shares` re-implemented the member demand and
  still **interpolated** PSEI's missing hours, while the pool summed the FERC 714 fill. In 2020 the zonal regroup
  therefore built PSEI from 17.28 TWh of straight lines, against 28.41 TWh in the pool total, which understated the
  NWPP-NW share all year.

## 2. The repair (zero DOF, rules 14 / 19 / 21 / 24)

1. **`constants.EIA930_REMOTE_GENERATION_DOUBLE_BOOKED = {"PSEI": {"NG: COL": "NWMT"}}`.**
   - `frames._repair_double_booked_generation` subtracts PSEI's own published column from its NG and D (raw and
     Adjusted), then zeroes it. `Total interchange` is untouched.
   - It is applied through one seam, `_repair_published_extract`, together with the SOCO sign-window repair, at every
     place an extract is read off disk: the strict frame, the filled frame, the pool member frames and the hourly
     benchmark.
2. **`frames._mask_unbalanced_demand`** marks the non-balance hours as missing readings, so the existing FERC 714
   gap guard fills them.
3. **`frames._pool_member_demand`** is the one member-demand construction. Both the pool total and
   `parse_nwpp_shares` read it.

**Measured effect, old code → new code, via `_eia_hourly_frame` / `load_zonal_shares` / `_pool_hourly_benchmark` /
`nwpp_net_interchange`:**

| Year | Requirement (NG − legs) | Pool demand | Served export | Bench coal | Zonal shares |
|---|---:|---:|---:|---:|---|
| 2019 | −4.480 TWh | −4.407 | −0.073 | −4.480 | 8,636 h move, max 0.030 |
| 2020 | −2.152 TWh | −3.067 | +0.915 | −2.152 | 8,760 h, max 0.069 |
| 2021 | 0.000 | +0.570 | −0.570 | 0 | 336 h, max 0.045 |
| 2022–2025 | **byte-identical** | identical | identical | identical | identical |

- The FERC 714 reconciliation scale on the corrected basis is 1.0251 in 2019 (was 1.21) and 1.0619 in 2020 (was 1.19).
- `calibration_reference.json` NWPP demand moves **only** in 2019 (279.226 → 274.819), 2020 (273.368 → 270.301) and
  2021 (278.462 → 279.032). `generation_twh`, the EIA-923 C1 basis, is unchanged.
- Tests: `tests/unit/data/test_nwpp_psei_double_booking.py`. `test_nwpp_pool_gap_guard.py` now pins 2020 at 270.30.

## 3. What it does and does not claim

- The lower requirement is expected to take out the marginal class, mostly gas, in 2019 and 2020. Whatever that does
  to C1, the repair stays, because the input was wrong (rules 1 / 14). The span solve reports it at full magnitude.
- It does not touch the NWPP-45 demand-basis gap, which is 2022–2025 and is still waiting on an owner ruling.
