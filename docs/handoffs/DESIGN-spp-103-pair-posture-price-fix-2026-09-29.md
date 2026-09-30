# DESIGN — SPP-103: pair the commitment posture with a price-level fix

**Lane** SPP-103 · owner card "Pair posture + price fix" (SPP-102, 2026-09-29) · DESIGN lane, **zero LP** ·
keeper `2026-09-28-spp-100-chp-scope` (bundle `spp100_arm_span`, 2019–2025) · posture arm = SPP-102 legs
(`RESULT-spp-102-commitment-posture-2026-09-29.md` §5) · probe `scripts/probes/_spp103_pairing_requirement.py`.

**Verdict: no candidate clears the admissible bar. Nothing solve-affecting is proposed.**

## 1. What the fix has to carry (phase 0)

Scorer basis (`calibration_verdict.py`, keeper): C3a 2023 / 2024 / 2025 = −6.7 / **−8.6** / −5.4 %. The posture
takes 2024 to **−10.3 %**. The band edge is −10 % of $25.45, so the minimum lift needed in 2024 is **+$0.08/MWh**.
A lift of +$0.42 cancels the posture's price effect completely.

Where the posture moves price. Arm − keeper, demand-weighted, split into SPP-79's RT buckets (probe; model-demand
weight, so levels differ from the scorer by a few points):

| year | Δprice | Δ body (RT < p67) | Δ upper tercile | arm error, body | arm error, upper tercile |
|---|---:|---:|---:|---:|---:|
| 2019 | −0.31 | −0.27 | −0.04 | +25 % | −20 % |
| 2020 | −0.43 | −0.39 | −0.05 | +33 % | −15 % |
| 2021 | −0.36 | −0.40 | +0.04 | +21 % | −25 % |
| 2022 | −0.58 | −0.54 | −0.04 | +9 % | −25 % |
| 2023 | −0.36 | −0.35 | −0.00 | +17 % | −25 % |
| 2024 | −0.42 | −0.41 | −0.01 | +19 % | −29 % |
| 2025 | −0.34 | −0.32 | −0.03 | +20 % | −27 % |

(Body error = low-side + ordinary contributions, as % of the annual RT mean.)

1. **The posture moves only the body**, and the body is over-priced in every year. It moves it toward the actuals.
2. **C3a 2024 "breaks" because of SPP-79's cancellation.** The train years pass C3a only because the body
   over-price offsets an upper-tercile under-price of −25 to −29 %. The posture cuts the offsetting half.
3. **So the pairing fix must live in the upper tercile**, and it must be larger in 2023–25 than in 2019–20. That is
   exactly SPP-79's constraint. A body-side or uniform lift re-breaks 2019–20. It would also undo the one thing the
   posture gets right.

## 2. Candidates screened

| candidate | status | why it fails |
|---|---|---|
| Upper-tercile premium: congestion, scarcity/ORDC, markup, net-load tightness | dead (SPP-80) | measured; none owns it |
| Heat-rate mix, gas timing/basis, ramp/uncertainty dispatch | dead (SPP-81) | measured; ≤ 14 % or wrong sign |
| Part-load / incremental HR, class mix, wind share, fast-start pricing, donor pool | dead (SPP-81b) | incremental HR < average HR, so any repair lowers price |
| Mitigated-offer content 2023+ (SPP-81's re-open route) | closed by SPP-81b's own data | RTBM offer q90 did not rise (50.6 / 40.1 → 48.4 / 42.3); a cost-policy change that raised offers would show there |
| Paid daily Mid-Con gas index (SPP-81 route) | not available | no license; HH-daily shaping already *widens* the residual (SPP-81) |
| Offline-offered +8 GW step (SPP-82) as commitment state | dead as a pairing (SPP-83) | re-clear differential +2.1 against +8.3 needed; overshoots 2019/20 and 2021 |
| Gas-price level | dead (SPP-89) | uniform −$1 moves 24–34 TWh off coal |
| Reserve co-opt / headroom | dead (SPP-96) | out of scope |
| **Missing CT outage** (SPP-84: keeper gas unavailability 1.3–2.4 GW below SPP's published gas outage; CT_PEAKER carries none) | **the only unexamined structural gap. Fails the pairing.** | see below |

**Missing CT outage in detail.** SPP-84's gas-only re-clear instrument, `_spp84_published_outage_phase0.json`:

| | 2019 | 2020 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| keeper − SPP gas outage, GW | −2.35 | −1.39 | −1.26 | −2.19 | unmeasured |
| Δprice, all hours | +0.97 | +1.11 | +0.47 | +3.34 | — |
| Δprice, upper tercile | +1.74 | +2.24 | +0.92 | +6.56 | — |

- **It fails SPP-79's pairing.** 2023 moves less than either 2019 or 2020. The 2019/20 − 2023/24 gas gap is flat
  (1.87 vs 1.73 GW), so 2024's size is one year's spring outage cluster, not a 2023+ driver.
- **It re-breaks 2019–20.** It adds about +$1/MWh there, taking C3a 2019 / 2020 from +10 / +25 % to about +15 / +31 %.
- **2025 is unmeasured.**
- **It has no admissible unit-level form.**
  - CEMS cannot tell an idle CT from an out CT, so rule 13's windowed-outage form cannot be derived.
  - Pro-rating availability to SPP's published hourly totals is the aggregate rebase SPP-84 closed (DO-NOT-REDO).
  - A GADS class EFORd would be a national-generic rate, not SPP's own. Its year differential would be zero by
    construction, so it still fails the pairing.

It remains a real structural gap (rules 1 / 14). But it is a separate availability question, not this lane's
price fix.

## 3. Rule notes

- **Rule 1 (c):** an `offer_curve_by_group` multiplier that cancels the posture's −$0.3–0.4 would be a value chosen to
  make C3a 2024 pass. That is refused.
- **Rule 13:** SPP's online capacity or outage totals must not be pinned.
- **Rule 17 / 21:** there is no candidate to specify, so there is no window and no parameter.
- **Rule 19:** the posture stays the one CC commitment mechanism.

## 4. Recommendation

- **Record `spp_commitment_posture` as a tested-but-unpaired structure.** Cell stays **R**, field stays default-off.
  - Its body effect is correct in every year.
  - It is unpromotable only while the upper tercile has no driver.
  - Re-open only when an upper-tercile driver exists that satisfies SPP-79.
- **Record the 2019–22 validation misses as model-class limits.** These are C3a 2019/20, C3b 2020, C1 CC_REGULAR /
  COAL_PRB 2021–22 and C4 gas 2022. They share SPP-79's root: no hourly LP commitment lever reproduces SPP's
  offline-offer step or the 2023+ upper-tercile premium, and no public per-class commitment cost exists (SPP-73/83).
- **Route "CT_PEAKER carries no outage" as its own availability lane, if the owner wants one.** Judge it on
  structure (rule 1), and expect it to worsen 2019–20.
- **Keeper unchanged.** No PRECOMMIT, no shards, no LP.

## 5. Owner ruling

**OWNER RULING (2026-09-29, decision card): "Record + CT outage lane."**
- The posture is recorded as **tested-but-unpaired**. Cell `spp_commitment_posture` stays **R** and the field stays
  default-off.
- The 2019–22 validation misses (§4) are recorded as **model-class limits** under SPP-79's root.
- **SPP-104 is chartered** as an availability lane for "CT_PEAKER carries no outage".
  - It is judged on structure (rules 1 / 14), not on whether it pairs with the posture or improves the residual.
  - It must find an SPP-own, forward-reproducible, unit- or class-level source.
  - It must not re-run SPP-84's aggregate rebase, and must not pin to published totals (rule 13).
  - Its expected cost of about +5 pts on C3a 2019 / 20 is stated in advance.
- Keeper unchanged.
