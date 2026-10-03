# RESULT — NWPP-NEXT-22: priced interface + measured seam headroom on keeper #20, 2019–2025

PRECOMMIT: `PRECOMMIT-nwppnext22-seam-headroom-2019-2025-2026-10-02.md`. FINDING (phase 0):
`FINDING-nwppnext22-seam-headroom-2026-10-02.md`. The run was scored as probe `2026-10-02-nwpp-next-22-priced`, on the
bundle `results/calibration/nwppnext22_span`, composed locally from the seven shard legs. The registration is
withdrawn (rule 15) and the span is not committed. The leg SHAs below are its provenance (rule 33).

**Owner cards (2026-10-02):**

1. "Promote as keeper #21".
2. Then, once the promotion was found blocked: "Re-solve on W0 basis".

`promote_keeper.py` refuses this bundle at preflight (`ensure_replay_recipe`). Replaying its recipe at main HEAD would
not reproduce it, because the run solved at the pin `a5a72ec0`. That pin is NEXT-21's pin `86b73d6f` plus this lane's
code, and main's defaults have moved since:

- `backcast_actual_retirement_only`, recorded None, replays True;
- `cc_block_summer_rating`, recorded False, replays True;
- `cc_steam_part_capacity`, recorded False, replays True;
- `commission_year_cod_fallback`, recorded False, replays True;
- `cc_mustrun_conduct_window` and `ercot_ordc_published_curve`, recorded None, replay False.

Keeper #20 fails the same check today (17 fields). The W0 close-out lane opened PR #7076, which promotes
`2026-10-02-w0-nwpp-fix2`: keeper #20's recipe re-solved at main's defaults. **The arm is therefore re-solved on the W0
fix-2 legs at main HEAD once #7076 lands (NEXT-23), and promoted on the owner's ruling if the structural gates
hold.** This bundle is the evidence for that ruling, not a keeper.

## Legs (pin `a5a72ec04be06ef8cb861aa6d5c68689dfc9c688`, branch `claude/nwppnext22-pin`)

| year | leg SHA | wall time |
|---|---|---|
| 2019 | `107b2994400b10ddfba2ebe55eb3a37d238608ff` | ≈ 80 min (P0 35 min) |
| 2020 | `a4320d19a8079a10647509ea5a5385f0fc3848af` | |
| 2021 | `e41dee7019884195366eb9eb93d3c388c86cfde1` | |
| 2022 | `ba7a09deb51259990e8a5b225c3a48768edf9f56` | |
| 2023 | `74214d61f1c76d0f1080b2a4ff7c5a0b9262a866` | 20 min, peak 5.51 GiB |
| 2024 | `6a15797d68a8ac31f9bd52251c700999c8df1201` | 21 min, peak 13.36 GiB (1 GiB swap provisioned) |
| 2025 | `7e94321274543435c7fa7ac7d3cfaef5b2b80055` | 25 min, peak 6.10 GiB |

Every shard hard stop (a)–(h) passed. The parent re-verified:

- (h) the caps in every year: COI excess 0.0 MW in both directions, every year; BC 0.0 MW in 2023–25;
- demand frames exact (272.855 … 287.331 TWh);
- the dangling 2019–22 BC zone carries 0;
- the `scenario_config` diff is exactly `nwpp_seam_measured_limits` + `reference_price_interface`.

Hours at cap, from the shard printouts:

| year | COI at import cap | COI at export cap | BC at export cap |
|---|---:|---:|---:|
| 2023 | 1,965 | 2,831 | 6,350 |
| 2024 | 721 | 4,177 | 1,879 |
| 2025 | 1,504 | 3,310 | 130 |

## Gate (a) structural: PASS · (a′) headroom live: PASS

Net TWh, export-positive, model / measured (r = hourly correlation with the measured leg):

| seam | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| COI | 13.03 / 7.03 (0.750) | 16.53 / 15.26 (0.608) | 16.29 / 12.11 (0.611) | 17.61 / 12.50 (0.635) | 5.73 / 1.13 (0.396) | 11.80 / 2.15 (0.534) | 7.92 / 3.03 (0.569) |
| NEVP | 8.42 / −0.30 † (0.139) | 9.68 / 3.11 (0.109) | 10.39 / 8.60 (0.439) | 8.10 / 8.56 (0.449) | 3.47 / 7.56 (0.178) | 8.60 / 9.08 (0.303) | 4.95 / 9.40 (0.431) |
| BC | unpriced | unpriced | unpriced | unpriced | 17.45 / 9.48 (0.366) | 11.96 / 7.51 (0.282) | 2.86 / 2.77 (0.399) |

† NEVP 2019 is the near-zero leg the PRECOMMIT exempted from the sign test. Every other priced seam-year has the
measured sign, and every r is > 0.

**(e) Seam volume.** Summed priced seams, TWh:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| NEXT-22 | 21.4 | 26.2 | 26.7 | 25.7 | 26.6 | 32.4 | 15.7 |
| NEXT-21 | 27.7 | 33.3 | 35.2 | 32.7 | 30.2 | 36.8 | 17.1 |
| measured | 6.7 | 18.4 | 20.7 | 21.1 | 18.2 | 18.7 | 15.2 |

- COI 2020–22 comes close to measured.
- **COI 2023–25 stays 2.6–5.5× measured, and COI 2023 rose** against NEXT-21 (5.73 vs 4.69). This is the price-level
  gap FINDING §D routed: keeper #20's NW price sits below CAISO's MALIN anchor.

**(d) Wheel** (COI importing while BC exports): 2,244 h / 3.08 TWh (2023), 1,515 h / 1.83 TWh (2024),
2,027 h / 2.09 TWh (2025). NEXT-21 had 6.04 / 2.51 / 2.54 TWh.

## Gate (b): verdict diff against keeper #20, per (criterion, year, key)

Both runs are NOT-YET, failing on fuelmix, price_mean, price_shape and dispatch_corr. Failing records: keeper #20 6,
NEXT-22 8, NEXT-21 10.

| record | keeper #20 | NEXT-22 | |
|---|---|---|---|
| C4 coal 2023 | r 0.669 / NRMSE 0.313 FAIL | **0.784 / 0.287 PASS** | gain |
| C3a price mean 2023 | −21.4 % FAIL | **−6.5 % PASS** | gain |
| C1 CC_REGULAR 2025 | +9.60 TWh FAIL | **+7.57 PASS** | gain |
| C3b price shape 2023 | 0.303 FAIL | 0.202 FAIL | closer |
| C3b 2025 | 0.179 PASS | 0.130 PASS | |
| C3a 2024 | −27.7 % FAIL | −24.6 % FAIL | |
| C4 gas 2019 | 0.731 / 0.232 PASS | **0.655 / 0.326 FAIL** | regression |
| C4 gas 2023 | 0.781 / 0.181 PASS | **0.521 / 0.367 FAIL** | regression |
| C4 gas 2024 | 0.894 / 0.125 PASS | **0.785 / 0.319 FAIL** | regression |
| C1 CC_REGULAR 2019 | +1.10 TWh PASS | **+9.31 TWh FAIL** | regression |
| C1 CC_REGULAR 2024 | +6.60 TWh PASS | **+11.56 TWh FAIL** | regression |
| C3b price shape 2024 | 0.676 FAIL | **0.784 FAIL** | worse |

**Against NEXT-21:**

- Recovered: C4 gas 2020 (0.750 / 0.277) and 2022 (0.743 / 0.273), and C1 CC_REGULAR 2020 (+5.83 TWh).
- Lost: NEXT-21's C3b 2023 PASS (0.182), now 0.202.

**Coal hourly r** rises in 6 of 7 years against keeper #20 (2019 0.72 → 0.82; 2025 0.71 → 0.81).

**CT_PEAKER and ST_GAS** sit closer to actual in most years. For example, CT 2023 is −0.16 TWh (keeper −4.20), and
ST_GAS 2024 is −1.61 (keeper −3.72).

**Root cause of the regressions** is the same as NEXT-21's, now smaller: gas fills the residual seam export over-run,
and NW gas follows the CAISO net-load price shape on the seam.

## Gate (c): rule 20 and legitimacy

- D-2 forced energy PASS (0 forced in every class-year), and C6 governance PASS.
- D-1 diurnal failures fall from 18 (keeper #20, scored today) to 14. The remainder are coal rows, chiefly COAL_WC
  (immaterial) and 2019–22 COAL_BIT / PRB.

## Bundles and cost of a promotion

- Each leg's full bundle, including `dispatch/<Y>_P1.parquet` and `hourly/unit_hourly_<Y>.parquet`, is on its shard
  branch at the SHA above.
- The composed span (83 files, plus a derived `unit_marginal` layer and `fleet_census`) stays local and gitignored.
- The promotion path is NEXT-23's W0-basis re-solve, not this bundle (preflight refusal above).

## Matrix

`nwpp_seam_measured_limits`: **O**, with this evidence. The owner ruled to promote. The keeper is pending the
W0-basis re-solve.

`reference_price_interface` / `priced_interchange`: unchanged **O**.
