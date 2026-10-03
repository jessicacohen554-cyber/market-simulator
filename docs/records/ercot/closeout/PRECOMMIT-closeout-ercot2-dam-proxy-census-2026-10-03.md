# PRECOMMIT: ERCOT closeout-2, R-25 DAM-proxy census (zero LP)

Lane `closeout-ERCOT-2` (desk session_01ALecU5Wjde4tkbLrnMExT9), plan §3.5 / §5.0 R-25. Written 2026-10-03 **before any census number exists**. Zero LP; no shard.

## 0. Definition (pinned from the record)

R-25 (plan §5.0; W0 phase-3 RESULT §2 ruling 7): *"IMM licence: raw data stays out. ERCOT DAM-proxy census: chartered. Census gate: presence-only."* The DAM proxy is gap **G2** of `docs/records/governance/closeout-2026-10/SHARD-ERCOT-closeout-research-2026-10-02.md` §6: the free NP3-966-ER 60-Day DAM Gen Resource disclosure (`QSE submitted Curve-MW/Price1..10`) as the **cheaper proxy for G1**, the NP3-965-ER 60-Day SCED `Submitted TPO` curves that the keeper's coal construction is built on (ERCOT-144 static levels, ercot-168 year table; `scripts/data/derive_coal_perplant_offer.py`). The census asks whether the on-disk window says the 2019-22 DAM intake (R-7, deferred under R-17) would be an adequate proxy, and what it would buy for 2019/20 C1 COAL_PRB (−10.5 / −11.8 TWh) and C3b (0.219 / 0.221).

## 1. Inputs (all on disk, ercot profile)

- DAM: `data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*` and `data/raw/ercot/DAM/` (delivery years read from `Delivery Date`).
- SCED: `data/raw/ercot/SCED/` (publication 2023-03..2024-03 = delivery 2023 + Jan 2024) and the loose 2025 tail-day extract.
- Keeper `results/calibration/closeout_ercot_l1_span`: `run_config_<Y>.json` (`coal_perplant_offer_curves` static 2024-25 curves; `coal_perplant_offer_curves_yearly["2023"]`), `hourly/unit_marginal_<Y>.parquet`, `hourly/system_<Y>.parquet`.
- Resource → plant crosswalk: `PREFIX_TO_PLANT` in `derive_coal_perplant_offer.py` (10 coal plants), CLLIG/coal resource types.

## 2. Construction (fixed now)

**Level statistic.** Per plant and year, the ERCOT-144 modal construction applied to DAM: per resource, the modal submitted (MW, price) curve over the year's hours with a non-empty curve; resources merged per plant into one price-sorted step curve; the **level** is the capacity-weighted mean price over the merged curve's MW, excluding points ≤ −$249 (`COAL_PERPLANT_SELF_SCHED_FLOOR` convention). The same level statistic is computed on the keeper's static curve and on the ercot-168 2023 year table (capacity-weighted over its windows).

**Q1 Proxy fidelity.** Bias = DAM level − SCED-basis level, (a) delivery 2023 DAM vs the ercot-168 2023 table, (b) delivery 2024-25 DAM vs the keeper's static (2024-25 SCED) curves. Fleet bias is weighted by plant curve MW.

**Q2 Required shift Δ\*.** For Y ∈ {2019, 2020}: the smallest uniform downward shift Δ of the COAL_PRB committed/econ tranche `mc` (keeper P1 `unit_marginal`) such that the static re-dispatch gain Σ_t Σ_g (cap_mw − mw)·1[mc − Δ < zonal P1 price] reaches the C1 COAL_PRB miss (10.5 / 11.8 TWh). Static (no price feedback), so Δ\* is a **lower bound** on the conduct change the intake must reveal.

**Q3 Direction from the window.** Per plant, DAM level by delivery year over the on-disk window (2022-11 → 2025) against the year-mean Henry Hub. Fleet slope b ($/MWh per $/MMBtu) by MW-weighted least squares on plant-year levels with plant fixed effects.

## 3. Pre-fixed readings

- **P1 (proxy adequate):** in both (a) and (b), |fleet bias| ≤ max($1.00, 0.25·Δ\*_min) **and** ≥ 8 of the plants present within ±$2.00. Else **P1 FAIL**: the DAM intake is not an adequate licence-free proxy for the SCED construction; G1 (SCED) stays the only route.
- **P2 (window says the intake would close C1 PRB):** predicted 2019/20 conduct shift b·(HH_Y − HH_2024-25 mean) is ≤ −Δ\*_Y (downward, at least the lower bound) **and** b is significant (|t| ≥ 2). If |t| < 2 or the level spread across window years is < $1.00 at fleet grain, the reading is **P2 INDETERMINATE (fuel-invariant on the window)**: the window carries no evidence that 2019/20 offers were lower, the intake's buy is unidentified ex ante, and the 2019/20 C1 PRB row is written data-limited with route = R-7. If b predicts an upward or insufficient shift, **P2 FAIL**: the intake is not expected to close C1 PRB by conduct level alone.
- **C3b:** direction only (coal displacing summer CC lowers the summer over-price that carries 61-73 % of the SSE); no size without an LP. Recorded, not gated.

No reading here arms a mechanism, changes a solve or edits the exceptions ledger. `coal_offer_level_rebasis` (R) is not re-tested: this census reads measured conduct, it does not re-couple offers to fuel.

## 4. Also in this lane (no gate)

W4 hygiene (`unit_marginal`, `authorized_price_tuning`, 2023 configuration-exception wiring) and the draft data-limited ledger rows go to the desk in the FINDING; nothing is backfilled outside a promotion.
