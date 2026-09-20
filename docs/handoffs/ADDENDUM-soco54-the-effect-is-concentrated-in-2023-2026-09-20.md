# ADDENDUM 2 to PRECOMMIT-soco-54 — the arm's offer-side effect is CONCENTRATED IN 2023, and 2023 is the failing year. Recorded against this lane, before the legs landed.

**Written BEFORE any arm leg landed** (pinned PRECOMMIT SHA
`d85e0c47567b0ae8258a99920d512fd3fe8fe1df`; no `claude/soco54-arm-*` branch existed when this
was committed). Rule 29 `[R-SCREEN]` (b): *"recorded in the PRECOMMIT or its addendum before the
arm is solved, so it cannot be written to fit the result."*

## 1. What PRECOMMIT §4 showed, and what it did not

PRECOMMIT §4 measured the merit-order reordering on **2023 only**. Extended to all three years —
same `fleet_only` rebuild, same thirteen plants that carry the defect, `mc` in $/MWh:

| plant | who | 2023 Δmc | 2024 Δmc | 2025 Δmc | 2023 actual TWh |
|---|---|---|---|---|---|
| 54538 | Hartwell CT | **+12.91** | +5.33 | **−12.66** | 0.207 |
| 55141 | Hawk Road CT | **+10.96** | +1.94 | +4.26 | 0.569 |
| 55244 | Doyle CT | **+9.48** | +1.26 | +4.87 | 0.054 |
| 6124 | McIntosh CT | +6.46 | +5.87 | +6.93 | 0.017 |
| 55409 | Calhoun CT | +3.71 | +1.09 | **−3.10** | 0.015 |
| 7709 | Dahlberg CT | +1.01 | **−0.65** | **−1.31** | 0.240 |
| 55061 | Tenaska GA CT | +0.99 | **−0.64** | **−1.28** | 0.237 |
| 55128 | Walton Co CT | +0.98 | +4.19 | +10.10 | 0.259 |
| **728** | **Yates ST** | **−6.26** | **+0.74** | −0.30 | 2.239 |
| 10 | Greene Co ST | −3.78 | −5.23 | −5.56 | 1.314 |
| 26 | Gaston ST | −2.29 | −1.08 | **−9.83** | 1.654 |
| 3 | Barry ST | −2.10 | **+0.43** | **+1.35** | 0.598 |
| 2049 | Watson ST | **+4.17** | −0.62 | +2.97 | 3.270 |

**2023 is the clean case and it is the only clean case.** There, every one of the eight
over-dispatched turbines rises and four of the five gas-steam plants fall — the single exception
being Jack Watson, which is the one ST_GAS plant the model already runs near its actual
(2.355 vs 3.270 TWh) and which therefore should *not* be pushed up.

**2024 is weaker and mixed** (Tenaska and Dahlberg fall; Yates rises $0.74).
**2025 is genuinely mixed**: Hartwell's own 2025 print is **$5.26/MMBtu — ABOVE** the $4.159
reference, so the contract that was 35 % below the footprint basis in 2023 is 26 % above it in
2025, and the arm makes Hartwell **cheaper** by $12.66.

**The contract-multiplier spread narrowed after 2023 and partly inverted by 2025.** PRECOMMIT §4's
seven-plant constant-multiplier family is a **2023** measurement and this addendum does not claim
it holds in the later years.

## 2. THE UNCOMFORTABLE COINCIDENCE, NAMED BY THIS LANE RATHER THAN BY A REVIEWER

**The arm's offer-side effect is largest in 2023, and 2023 is SOCO's only failing C1 year.**
A careful reader should look at that pattern and ask whether the lever was selected because of it.
Three facts answer that, and all three are checkable:

1. **Nothing was selected.** The arm is a **single pre-existing `ScenarioConfig` field returned to
   its own shipped default** (`gas_plant_monthly_fuel_pricing: bool = False`). There is no value,
   no threshold, no year scope and no class scope to have chosen. It is applied **identically to
   all three years** by one `--set`.
2. **Nothing was swept.** No variant was solved. The only A/B is on/off, and this addendum's own
   table is the whole ex-ante evidence base.
3. **The cross-year weakness is reported BEFORE the result, against the lane's own interest.**
   PRECOMMIT P1/P6 already banded 2024's `CT_PEAKER` fall at 0.8–2.0 TWh against 2023's 1.5–3.5,
   and P7 already said no 2025 C1 class row is scored at all (all seven SKIPPED, preliminary
   EIA-923 vintage). This addendum states *why* that asymmetry exists.

**What it genuinely costs the lane:** a structural repair that bites hard in one year and weakly
in another is **weaker evidence of a structural defect** than one that bites uniformly. A reader
is entitled to read the 2024/2025 tables as saying the 2023 contract spread was a 2023
phenomenon. This lane's position is that the *basis* argument — average delivered contract cost is
not a marginal dispatch cost — is a statement about the **input's construction**, true in every
year, whose *magnitude* happens to vary with how wide the contract spread was that year. That is
an argument, not a measurement, and it is labelled as one.

## 3. What this does NOT change

Rule 1 `[R-STRUCT]` still decides, and it decides on the basis argument, not on 2023's residual.
If the solve shows 2023 improving and 2024 flat, **that is the predicted outcome, not a success
to claim** — PRECOMMIT P1/P6 pre-registered exactly that shape. And PRECOMMIT P4's stated risk
(2024 `CC_REGULAR` consuming 81 % of its margin) is unaffected: a common basis shift moves the
whole gas block against coal in every year alike.
