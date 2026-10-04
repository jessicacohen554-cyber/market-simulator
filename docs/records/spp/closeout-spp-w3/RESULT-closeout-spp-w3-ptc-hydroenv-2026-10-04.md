# RESULT — closeout-SPP-w3: `wind_ptc_vintage_offers` + `hydro_dispatch_envelope` (7 shards). T1 met, K1 fired: no promotion request

- **PRECOMMIT:** `PRECOMMIT-closeout-spp-w3-ptc-hydroenv-2026-10-04.md`, pushed at `15d957c1` before any shard.
- **Control:** keeper `2026-10-03-closeout-spp-nuc-keeper` (`closeout_spp_nuc_span`). G-DRIFT `8c3ea461 → 90cea720`
  is all INERT, so there is no control solve (rule 29b). This was verified by array identity of the hydro min-flow,
  hydro envelope and demand loaders for SPP 2019–25.
- **Run:** probe `2026-10-04-closeout-spp-w3-ptc`, bundle `results/calibration/closeout_spp_w3_span`.
  - Composed by `scripts/probes/_closeoutsppw3_compose_span.py`. Every leg is the keeper recipe plus exactly the two
    arm fields; there is one solve-surface fingerprint, `4187973695945d73`.
  - The probe is registered **on branch `claude/closeout-spp-w3` only**: E13 refuses non-keeper registrations on
    `main`.
- **LP in the parent:** zero. Seven year-isolated shards ran at pin `15d957c1f0463b0c5128935723e66e352dcc62c1`.
  Every one was verified (17 files, P1 dispatch present, parent = pin), extracted, then archived.

| year | shard branch @ commit (transport, rule 33) |
|---|---|
| 2019 | `claude/closeout-spp-w3-2019` @ 17785ee7afcce2ef187d7549efe8e593efcd82bc |
| 2020 | `claude/closeout-spp-w3-2020` @ cb127749ebf12b70f94524dc7c6601e6c55e010f |
| 2021 | `claude/closeout-spp-w3-2021` @ 6ed45970e8ab3732c661c5aee54d6fa3527c94a2 |
| 2022 | `claude/closeout-spp-w3-2022` @ 39e15121a571b65cef1a729bb2666774d1511d79 |
| 2023 | `claude/closeout-spp-w3-2023` @ e68e98a8ad840f88e8624943658ead5a7f4dd497 |
| 2024 | `claude/closeout-spp-w3-2024` @ cd1e1b04800a1ebb25c0781baf993407fd62dc4a |
| 2025 | `claude/closeout-spp-w3-2025` @ 4f673f2f6cea1a0a41a8807473a8c446121d09ff |

## 1. Scored diff vs the keeper (`calibration_verdict.py`, rubric v3.20)

| record | keeper | arm | bar |
|---|---|---|---|
| **C3a 2024** | −11.2 % FAIL | **−9.2 % PASS** | **T1 met** (+2.0 pts; predicted +1.67) |
| C3b 2024 | 0.216 FAIL | 0.207 FAIL | T2 direction met; no flip (as predicted) |
| C3a 2023 / 2025 | −6.4 / −4.3 % | −4.5 / −2.1 % | T3 met |
| C3a 2021 | +7.1 % | +8.4 % | D2 met (≤ +10) |
| C3a 2019 / 2020 | +12.3 / +27.7 % | +12.9 / +28.8 % | D3 met (≤ 1.5 pts) |
| C3b 2019 / 2020 | 0.160 / 0.345 | 0.166 / 0.356 | D3 met (≤ 0.015) |
| **C1 CC_REGULAR 2025** | −7.86 TWh PASS | **−8.46 TWh FAIL** | **K1 FIRES** (undeclared PASS→FAIL) |
| C1 CC_REGULAR 2021 / 2022 | −8.92 / −9.16 FAIL | −9.54 / −9.89 FAIL | further away (already FAIL) |
| C1 COAL_PRB 2021 / 2022 | +10.98 / +10.75 FAIL | +10.28 / +10.13 FAIL | toward the band |
| C4 gas NRMSE 2021–25 | 0.276 / 0.313 / 0.194 / 0.224 / 0.248 | 0.293 / 0.326 / 0.203 / 0.239 / 0.262 | worse in every year (2022 already FAIL) |
| C3c 2019–22 | CAVEAT | FAIL (same magnitudes) | artifact: the unattested probe loses the rule-22 governance guard. Not a model change. |
| unserved / D-4 / C8 | 0 / — / PASS | 0 / — / PASS | K3 clear |
| hydro energy, every year | — | identical to 0.001 TWh | K4 clear |
| negative-price zone-hours | 44/196/970/1,460/1,134/1,268/1,145 | identical | K5 clear: the re-price is the mechanism |

## 2. Split (ex-ante attribution, `results/phase0/spp/_closeoutsppw3_split.json`)

The PTC part is the arm's price minus −26 at the keeper's floor zone-hours. The hydro part is the remainder.

| C3a pts | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| PTC vintage offer | +0.04 | +0.26 | +0.60 | +0.89 | +1.19 | **+1.08** | +0.98 |
| hydro envelope | +0.60 | +0.86 | +0.72 | +0.10 | +0.67 | **+0.94** | +1.14 |

- The PTC scoping re-prices 1,258 zone-hours in 2024, from −26.00 to a mean of −21.49. It changes no dispatch.
- **Alone it reads 2024 C3a ≈ −10.1 %, still FAIL by about 0.1.** That is not worth seven shards on a predicted miss.
- The hydro envelope causes the entire dispatch shift:
  - CT_PEAKER +0.4…+0.9 TWh and ST_GAS +0.2…+0.5 TWh;
  - CC_REGULAR −0.4…−0.7 TWh and COAL_PRB −0.2…−0.7 TWh.

  The capped peak-hour hydro moves into lower-priced hours, where it displaces CC/coal. Peakers backfill the peaks.
  The CC_REGULAR 2025 flip and the C4 gas degradation therefore belong to the envelope.

## 3. Verdicts (rule 28, `mechanism-matrix/SPP.js`)

- **`wind_ptc_vintage_offers`: I → O.** New evidence: wind is now marginal in 6–8 % of zone-hours, so SPP-51b's
  reach premise is void. Its effect is positive and dispatch-neutral, but too small to close 2024 alone. It stays open
  as a building block.
- **`hydro_dispatch_envelope`: U → R.** Killed by K1:
  - C1 CC_REGULAR 2025 goes PASS→FAIL;
  - C4 gas gets worse in 2021–25.

  The cap is structurally real. Its cost lands on the CC low side, which is the commitment-state object
  (SPP-74/75/88) that the UC-MILP program owns.

## 4. Decision (PRECOMMIT §4)

- K1 fired, so **no promotion slot is requested**.
- **Owner option, not the lane's recommendation.** Rule 1 keeps a structurally real mechanism in even when the fit
  worsens. The arm trades:
  - one load-bearing flip each way: C3a 2024 FAIL→PASS against C1 CC_REGULAR 2025 PASS→FAIL;
  - for a cap that measured data supports and three other keepers carry.

  The determination is NOT-YET either way. SPP still fails `fuelmix`, `price_mean` (2019/20), `price_shape`,
  `price_tail` and `dispatch_corr`.
- **Promotion cost if the owner rules it:**
  - one `promote_keeper.py` call; nothing is re-solved;
  - the slim span is on `claude/closeout-spp-w3`; dispatch is on the shard branches;
  - the arm has to move into SPP's recipe as two per-ISO overrides with `--no-` flags.

## 5. Queue

FINDING §2 has no further chartered candidate.
- The PTC part alone is a predicted miss.
- Commitment state (2019/20 body, CC low side, C1 2021/22) belongs to the UC-MILP program.
- The Oklahoma pocket is DATA-LIMITED. The 2024 DA and RTBM archives were re-checked today and carry no limit columns.
- C3c is model-class.
- The scorer-basis item (FINDING §3, SPP 2019–22 on the legacy equal-hour basis) is with the desk for an owner ruling.

**The SPP queue is exhausted with reasons.**

## 6. Rules

- **1/13/14:** both fields read measured inputs and tune nothing.
- **28:** both cells are updated with this evidence.
- **29/32/34/36:** the PRECOMMIT and G-DRIFT came before the shards; the shards were year-isolated, pinned, pushed
  with their full bundles, and verified before archiving.
- **31:** nothing was deleted. Leg bundles are on the shard branches and the span is on the lane branch.
- **37:** the rubric is untouched.
