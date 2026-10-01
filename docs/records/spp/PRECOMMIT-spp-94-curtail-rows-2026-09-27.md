# PRECOMMIT — SPP-94: SPP's own published 2020 and 2021 wind-curtailment rates

**Lane** SPP-94 · keeper `2026-09-26-spp-86-coal-extract` (bundle `spp86_arm_span`, basis_sha `d72e5f10`) ·
written and committed **before any model output exists for this arm**. The census (§3) reads inputs only.

## 1. The lever, and why it is admissible

**What it is.** A data correction to an existing keeper mechanism, `vre_reference_rate_year_own` (cell **K**, SPP-67).
That mechanism grosses each year's delivered wind up to an uncurtailed potential using **that year's own** published
SPP curtailment rate. SPP-67 found no published figure for 2020 and 2021, so those two years fell back to the
2023–25 mean, **9.65 %**. SPP-67 listed this as its open gate (4): "2020 and 2021 are untouched because SPP
published no curtailment MW for them".

**The premise was wrong.** SPP-67 read only the 2023–25 State of the Market reports. The earlier editions publish
both years (fetched 2026-09-27, checksums in `data/raw/spp-planning/SHA256SUMS.txt`):

| year | avg hourly curtailment | source | year-own rate | rate applied today |
|---|---:|---|---:|---:|
| 2020 | **244 MW** | ASOM 2022 p. 53: "From 2020 to 2022, average hourly curtailments increased … from 244 MW to 1,260 MW" | **2.55 %** | 9.65 % |
| 2021 | **725 MW** | ASOM 2021 p. 60: "… from 136 MWh in 2019 to 725 MWh in 2021" | **6.37 %** | 9.65 % |

- **Basis.** Both are wind, average hourly MW, the same basis as every committed row. The 2021 sentence says "MWh",
  but it describes Figure 2-35, whose axis is "Average hourly curtailments", and its 2019 value (136) is the figure
  later editions restate as 137 MW. The 2022 edition's 2022 endpoint (1,260) equals the committed 2022 row.
- **Rate** = curtailed / (delivered + curtailed), with delivered = the committed GenMix rows (9,337.1 / 10,656.2 MW).
- **Rules.** Rule 14: a published measurement replaces an estimate standing in for it. Rule 13: the same published
  quantity exists for any past year, and a forecast year keeps the reference-rate path. Rule 23: a source-data
  change, cited. Rule 21: zero parameters. Rule 19: no new mechanism; the existing seam reads two more rows.
- **Why it targets this lane's objects.** SPP-86 Card B / SPP-87 / SPP-88 named the keeper's wind excess as the
  largest single counterpart of the 2021–22 gas deficit (+8 to +9 TWh against EIA-930). 2022 already uses its own
  rate; 2021 does not. It is not a fit to the residual: the direction on 2020 price is expected to be **adverse** (§4).
- **Not a re-test.** SPP-88's "do not re-level" line concerns re-levelling the gross-up against the residual. This
  lane changes no construction and uses SPP's own published number, which is new evidence.

**The change** is two rows in `data/raw/spp-hsl/spp_wind_curtailment_annual.csv` (sha256 `dd6c2898…`). No
`ScenarioConfig` field, no code path. The keeper recipe is solved unchanged.

## 2. G-DRIFT `d72e5f10` → HEAD (rule 29(b) form 4)

`d72e5f10` → `325674da`: ALL INERT (`docs/handoffs/spp93/gdrift_d72e5f10_to_325674da.md`). Audited here:
`325674da` → `ceeb47a4`, three commits touching the backcast path:

| commit | hunks | verdict for SPP |
|---|---|---|
| `7ee882e0` R-CAISO-8 | `caiso_intertie_partial_year_measured` (default off), CAISO ST_GAS registry value | INERT: another ISO's branch / default-off flag absent from the keeper recipe |
| `7b069a14` soco-81 | `coal_econ_marginal_hr_two_sided` (default off), its SOCO artifact reader, a `year` argument read only under the flag | INERT: default-off, absent from the keeper recipe; no SPP artifact |
| `b507e6a2` SPP-93 | `spp_zone_partition` (default `north_south`) and its West/East branches | INERT: default = the keeper topology; solve surface 317 → 317, 0 moved |

**All INERT.** This lane adds a docstring edit to `renewables.py` (INERT) and the two data rows (the arm).
**Post-solve proof, E2 below:** the five years whose inputs do not change must reproduce the keeper byte for byte.

## 3. Zero-LP census (inputs only; `scripts/probes/_spp94_curtail_rows_census.py` → `docs/handoffs/spp94/census.json`)

The keeper's wind upper bound, rebuilt through the production seam (`_oversupply_uncurtailed_cf`, year-own on):

| year | rate now → arm | wind headroom TWh now → arm | Δ potential TWh | hours with headroom | max \|Δ\| MW in top-500 net-load hours |
|---|---|---|---:|---|---:|
| 2019 | 1.59 % → same | 1.25 → 1.25 | 0 | 777 → 777 | 0 |
| **2020** | **9.65 % → 2.55 %** | **8.76 → 2.14** | **−6.62** | 2,744 → 1,174 | 0 |
| **2021** | **9.65 % → 6.37 %** | **9.92 → 6.32** | **−3.60** | 2,893 → 2,215 | 0 |
| 2022 | 9.36 % → same | 11.09 → 11.09 | 0 | same | 0 |
| 2023–25 | own rates → same | unchanged | 0 | same | 0 |

- Every year other than 2020 and 2021 builds a **byte-identical** bound.
- **Pre-solve STOP leg S1 (adequacy):** the removed headroom sits only in low-net-load hours, and the 500
  highest-net-load hours move by 0 MW in both years. **PASS.**
- **Pre-solve STOP leg S2 (basis):** both figures reconcile to the table's average-hourly-MW wind basis (§1). **PASS.**
- SPP-67 measured the keeper's 2020/2021 wind excess against bench at +8.60 / +8.95 TWh. The arm removes up to
  77 % / 40 % of the input-side headroom behind it.

## 4. Solve plan and expectations

**Seven shards, one per year 2019–2025** (rule 36), each pinned to the full SHA of the merge commit that lands this
doc and the data rows on `main`:

```
python scripts/replay_keeper.py results/calibration/spp86_arm_span --years <Y> \
  --out-dir results/calibration/spp94_arm_<Y> \
  --note "SPP-94 <Y>: SPP's own published 2020/2021 wind curtailment rows"
python scripts/probes/_spp94_shard_check.py --year <Y> --leg results/calibration/spp94_arm_<Y>
```

Each pushes its full bundle, including `dispatch/<Y>_P1.parquet`, to `claude/spp94-<Y>` via a `.gitignore` negation
and a plain `git add` (rule 34(a)). The parent composes (`_rspp_compose.py --side arm`, with the SPP-85/86 requires),
attests, runs `build_dof_ledger --check`, scores and registers (`--no-prune`), and lands the composite on `main`
before its PR merges (rule 33(f)).

| # | expectation (directional; declared so it cannot be fitted) |
|---|---|
| E1 | Shard check PASS on all 7 legs: recipe identical to the keeper, gas price, 7 input sha256, `-netloadmask-` extract, N/S topology, `dispatch/<Y>_P1.parquet` present. |
| E2 | **2019, 2022, 2023, 2024, 2025 reproduce the keeper**: every class within 1e-4 TWh and max hourly \|Δprice\| ≤ 1e-6. This is the G-DRIFT proof and makes the train tier unchanged by construction. |
| E3 | 2020 and 2021 P1 wind **falls**, by at most 6.62 / 3.60 TWh (the LP already re-curtailed part of the old headroom). |
| E4 | Thermal absorbs it roughly one for one. Demand-weighted price **rises or is flat** in 2020 and 2021. |
| E5 | 2020 / 2021 slack does not rise (keeper 0 MWh). |
| E6 | Declared cost, not a criterion: 2020 `price_mean` (+17.6 %) is expected to **worsen**; 2021 COAL_PRB (+11.4 TWh) may worsen; 2021 CC_REGULAR (−9.5 TWh) and gas NRMSE may improve. |

## 5. Recommendation rule (fixed now)

**Recommend PROMOTE iff all hold:** (a) E1 on every leg; (b) E2 on all five untouched years; (c) E3 in sign in both
years; (d) E5; (e) `build_dof_ledger --iso SPP --check` shows zero new free parameters.

**No validation-tier or train-tier gate outcome is a criterion in either direction** (rules 1, 14). If E2 fails, the
form-4 comparison is void for the failing years, the lane reports it as drift, and it does not recommend promotion.
The 0.93 offer multipliers are untouched. The owner rules on promotion (rule 31); nothing is deleted before that.

## 6. Retrievability and duties

- Each shard's bundle is pushed to its own branch; the parent fetches, verifies (`git ls-tree` non-empty, E1),
  composes, and lands the composite on `main` before archiving the shards (rules 33, 34).
- The data rows stand on `main` whatever the promotion outcome (rule 14 forbids reverting to the estimate). If the
  owner declines promotion, the keeper's committed 2020/2021 legs no longer match a HEAD replay; any later G-DRIFT
  must classify this commit as **LIVE for 2020 and 2021 only**.
- Update `SPP.js` cell `vre_reference_rate_year_own` with the outcome and add the §5.7 note (rule 28(b)).
