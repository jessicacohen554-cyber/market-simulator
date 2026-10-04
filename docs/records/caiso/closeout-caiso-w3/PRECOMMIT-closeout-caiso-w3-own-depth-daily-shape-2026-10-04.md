# PRECOMMIT closeout-CAISO-w3: 2021 own DSW depths + daily-shaped unprinted formula gas (2026-10-04)

Written before any solve. Evidence: `FINDING-closeout-caiso-w3-phase0-2026-10-04.md`.

## 1. Arm

The control recipe is the w2 probe's: the keeper plus `caiso_dsw_daytime_lateevening_unprinted_arm=true`. Two flags
are added on top, both default-off CAISO-only rule-14 measured inputs:
- **`caiso_dsw_clean_depth_own_year=true`** (L1): 2021 rows only.
- **`caiso_intertie_unprinted_daily_gas_shape=true`** (L2): unprinted hours only.

They are stacked as one arm because each is independently admissible on measurement, and splitting them would double
the shards. The RESULT attributes the effect by year and month: L1 touches only 2021; L2 touches only unprinted hours
(2019–20 and Jan–Apr 2021).

**Inert by construction in 2022–25.** There is no own-year row and the unprinted mask is empty. Fast-lane tests pin
this: `tests/iso/caiso/test_caiso_w3_own_depth_daily_shape.py`.

## 2. Control and drift

- **Control:** the w2 probe legs (solved at `e8570532`).
- **Shards:** pinned to the full SHA of this lane's build commit.
- **G-DRIFT** (addendum before launch):
  - fleet-only fingerprint of the w2 recipe at `e8570532` vs the build SHA, flags OFF, all 7 years;
  - hunk classification of `e8570532 → build` on the CAISO path.

## 3. Bars (fixed ex ante)

**Targets.**

| Gate | Bar |
|---|---|
| T1 C1 CC_REGULAR 2021 | +4.98 → ≤ +4.83 (PASS) |
| T2 C1 CC_REGULAR 2020 | +5.39 → ≤ +4.60 (PASS) |
| T3 C4 gas NRMSE 2020 / 2021 | reported; ≤ 0.30 is not claimed |

**C1 PASS→FAIL declared ex ante:** none.
- **Watch:** C1 CC_REGULAR 2019 (−1.75 on the control, band ±4.84) gets more negative as imports rise in 2019. Below
  −4.84 is a K1 kill.
- **Watch:** CT_PEAKER 2020 (−2.06, band ±4.60).

**Kills (any one stops promotion):**
1. **K1:** any C1 PASS → FAIL in any year.
2. **K2:** whole-year |DSW net import − EIA-930| grows by > 1.0 TWh in any fold year versus the control (control:
   +0.99 / −2.91 / −7.00).
3. **K3:** C4 gas NRMSE worsens by > 0.02 in any fold year versus the control (0.291 / 0.317 / 0.321).
4. **K4:** C3a 2021 worse than +13.6 % (control +12.6 %); C3b 2021 above 0.157.
5. **K5:** any 2022–25 record moves.
6. **K6:** C2 gas leaves its band in any year.

**Expected, first order:**
- DSW import +1.5 / +2.1 / +5.1 TWh in 2019 / 2020 / 2021 (L1 + L2).
- Realised at the w2 ratio of about 0.5–1.0× first order, that projects CC_REGULAR down by roughly 0.8–1.5 / 1–2 /
  2–4 TWh.
- T1 is likely. T2 is about even.

## 4. Decision rule

| Outcome | Action |
|---|---|
| All kills clear, and T1 or T2 met | Request a promotion slot superseding the w2 probe (and the keeper). The attestation declares L1/L2 as measured inputs alongside the R-63 transfer. |
| Kills clear, no target met | Report, with no slot request unless the desk asks. |
| Any kill | NOT PROMOTED; the cells move to R with the reason. |

## 5. DOF

Zero fitted parameters:
- the L1 rows are the rungs' existing statistic;
- the L2 shape is a measured series with no scalar;
- the L2 validation used a pre-fixed bar on out-of-fold printed years.

## Addendum A: G-DRIFT and launch (2026-10-04, before any result)

- **Drift `e8570532` → `90cea720`.** The hunks touch PJM (`pjm_elliott_outages`, `fleet/arrays.py` gated
  `_iso == "PJM"`) and NWPP (`nwpp_path76_*` in `pipeline/ttc.py`, `eia930/envelopes.py` / `demand.py`, and
  `scripts/run_calibration*.py`, all gated `iso == "NWPP"` plus default-off flags). **INERT** for CAISO.
- **`90cea720` → `519dbd84`.** The only hunks are this lane's two flags, byte-identical off (fast-lane tests, and the
  full fast lane: 11,514 passed).
- **Arm scope.** The fleet-only fingerprint of the w2 recipe at the build SHA, w3 flags off vs on
  (`_closeout_caiso_w2_gdrift_fingerprint.py`):
  - 2019 and 2020: only `mc_base` moves, on the 10 WECC_DSW hub-priced tranches;
  - 2021: `mc_base` moves, and pmax/availability move on the four DSW clean rungs only;
  - **2022–2025: identical on every component.**
- **Shards.** Pinned to `519dbd84dc2805193a1182d0101f67acb8ac231b`, environment `env_016R8xUY4maDbppZ6TEns5V8`:

  | Year | Shard session |
  |---|---|
  | 2019 | `session_01PVaEyu1SJPCSA7DJbBUZBF` |
  | 2020 | `session_01UEwKZ5fabprSPDQ4bpmXTq` |
  | 2021 | `session_012QA3JMykHh9QZstdYbyXRZ` |
  | 2022 | `session_01CpgWgYe6MQQWSoTsf9hS2B` |
  | 2023 | `session_01FVNTgZb1fKruTRHmPVnFyA` |
  | 2024 | `session_01LMFQFv6QYdbDWBooWKfkMk` |
  | 2025 | queued (6-alive cap) |
