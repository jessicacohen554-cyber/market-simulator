# RESULT — SPP-76: SPP's heat rates are not why the coal/gas crossover is too gas-elastic

**Zero LP. No solve, no shard, no bundle.** Nothing owed under rule 15, nothing at risk under
rule 31. PRECOMMIT `PRECOMMIT-spp-76-crossover-heat-rates-2026-09-24.md` pushed at
`27874eb79804b84976558fb487a73ae0924a1311` before any number below was read. Base `b024e34c`.
Probe `scripts/probes/_spp76_crossover_hr.py`; all numbers in `results/calibration/_spp76_crossover_hr.json`.

**Verdict: the pre-registered test (4) FAILS. SPP's heat rates are within 2–3 % of CAMPD, and
correcting them moves coal by ≤ 0.1 TWh in the years that fail. No heat-rate lever is built.**

---

## 1. Step 1 reproduces both predecessors

C1 Δ (model − actual) TWh, grid-delivered, from `calibration_verdict.py --json` at base:

| class | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| COAL_PRB | −1.72 | **−6.89** | **+6.63** | **+9.60** | +0.79 | +0.39 | +5.31 |
| CC_REGULAR | +5.30 | +1.91 | −6.63 | −7.55 | −4.06 | −5.36 | −6.97 |
| ST_GAS | −5.25 | −5.53 | −4.35 | −5.42 | −5.46 | −7.34 | −9.19 |
| gas $/MMBtu | 2.57 | 2.03 | 3.72 | 6.45 | 2.54 | 2.19 | 3.52 |

This matches SPP-69 §4 in sign and shape, with drift of up to 0.47 TWh from keeper/rung updates
since SPP-69 (2021: +6.63 now vs +7.10 then). SPP-75 §2 reproduces **exactly**:
the model's CC+ST MW in RT≤0 hours is 3,548 / 1,767 / 426 / 277, against 3,507 / 3,229 / 2,070 / 2,176 measured.

## 2. Step 2: measured and model heat rates agree

The existing derives were run with `--iso SPP` into scratch; no artifact was written into
`data/raw`. Net basis, capacity-weighted, over `flag == ok` plants only:

| class | covered / class MW | model (eGRID) | CAMPD 2023–25 | Δ | CAMPD 2019–22 | Δ | dispersion (sd) model → measured |
|---|---|---:|---:|---:|---:|---:|---|
| CC_REGULAR | 8,114 / 9,974 (81 %) | 7.802 | 7.576 | **−2.9 %** | 7.653 | −1.8 % | 0.86 → 0.50 |
| ST_GAS | 9,669 / 10,192 (95 %) | 11.628 | 11.297 | **−2.8 %** | 11.412 | −1.8 % | 1.21 → 0.82 |
| COAL (all) | 18,810 / 19,197 (98 %) | 10.834 | 10.651 | **−1.7 %** | 10.652 | −1.7 % | 0.88 → 0.69 |

- **The hypothesis is wrong on coal.** The model's coal heat rate is slightly *too high*, not too low.
- **CC is almost exact.** 12 of the 16 applied CC plants are within ±1.5 %. The −2.9 % comes from two
  **blended-plant rows**, where eGRID's single plant average prices a coal unit and a CC unit at one
  rate. At GRDA (165) the CC is carried at 8.02 against 6.67 measured, and the coal unit at 8.02
  against 12.35. At Hawthorn (2079) the CC is carried at 11.79 against 8.38.
- **Measured heat rates are *less* dispersed than eGRID's in all three classes.** Measured rates
  would sharpen the knife-edge, not soften it.
- The 2023–25 and 2019–22 CAMPD windows agree to ≤ 1.1 pp, so the measurement is stable.

## 3. Step 3: the crossover barely moves

`g*` is the gas price at which the capacity-weighted CC offer equals the capacity-weighted PRB offer.
Δ is the merit-order re-dispatch of the LP's own served thermal MWh, measured HR minus model HR,
from the CAMPD 2023–25 artifact.

| year | gas | g* model → measured | ΔCOAL_PRB TWh | ΔCC_REG | ΔST_GAS | ΔCT_PEAKER | CC MW behind all PRB |
|---|---:|---|---:|---:|---:|---:|---|
| 2019 | 2.57 | 2.80 → 2.82 | +1.00 | −0.49 | +0.63 | −1.10 | 0 % → 0 % |
| **2020** | 2.03 | 2.71 → 2.73 | **+0.61** | −0.31 | +0.40 | −0.64 | 2.7 % → 0 % |
| **2021** | 3.72 | 2.63 → 2.65 | **−0.09** | −0.00 | +0.30 | −0.22 | 96.9 % → 96.9 % |
| **2022** | 6.45 | 3.20 → 3.23 | **−0.06** | −0.04 | +0.52 | −0.46 | 90.0 % → 85.8 % |
| 2023 | 2.54 | 2.95 → 2.97 | +0.38 | +0.69 | +0.19 | −1.15 | 0 % → 2.9 % |
| 2024 | 2.19 | 2.80 → 2.82 | +0.21 | +0.49 | +0.27 | −0.97 | 4.4 % → 4.4 % |
| 2025 | 3.52 | 2.71 → 2.73 | +0.53 | +0.50 | +0.01 | −0.84 | 10.8 % → 10.8 % |

The CAMPD 2019–22 window gives the same picture: ΔCOAL_PRB is +1.09 / +0.80 / +0.07 / +0.01 TWh for 2019–22.

**Proxy fidelity**, as proxy(model) ÷ P1 class TWh: COAL_PRB +2 to +7 %, CC_REGULAR +0 to +3 %. Both
are inside the PRECOMMIT's 25 % bar, so the coal and CC shifts are valid. ST_GAS is −30 to −48 % and
CT −3 to −16 %, because the LP's commitment floors are absent from a pure merit-order stack. So the
ST_GAS and CT shifts are **indicative only**.

## 4. Step 4: the decision (ex ante rule) — FAIL

The rule required ΔCOAL > +1.0 TWh in 2020 and < −1.0 TWh in both 2021 and 2022.

- **2020:** +0.61 TWh. Right direction, below threshold.
- **2021 / 2022:** −0.09 / −0.06 TWh. Essentially null.

This is the one-sided level move §1 of the PRECOMMIT predicted. It is not the elasticity repair.
**No shard was launched and no field was armed.**

## 5. Why a heat rate cannot do this, and what the data show instead

- The crossover is a **fuel-price knife-edge**. Delivered PRB is flat at $1.5–2.0/MMBtu.
  CC delivered fuel runs $1.8–3.1 by month in 2020, $2.8–6.5 in 2021 (February $29.30, Uri) and
  $5.4–8.2 in 2022. At CC 7.5 and PRB 10.6 MMBtu/MWh, a 2–3 % heat-rate correction is worth
  $0.3–1.1/MWh. The fuel spread between the years is $15–40/MWh.
- The model does what its inputs imply: 90–97 % of CC MW sits above every PRB offer in 2021–22.
  The real fleet kept CC online in 42–53 % of RT≤0 hours (SPP-75 §2). **That behaviour is not a
  cost the model mis-measures. The driver is not in the offer stack at all.**
- **Found incidentally, and routed rather than built:** a measured-input defect in F923 delivered
  gas. In **January 2022**, Hawthorn (2079) and State Line MO (7296) are priced at
  **$147.15/MMBtu** and Dogwood (55178) at **$47.94**, against $5–6 for their peers. That is
  1,426 MW of CC priced out for a month, and it survives into the offer arrays despite the F923 plausibility screen. It adds to the 2022 CC shortfall. It
  cannot be the elasticity defect, because it is one month in one year.

## 6. Failing rung rows and the object that owns each

| row | owning object | this lane |
|---|---|---|
| C1 COAL_PRB 2022 +9.60 TWh | the crossover's fuel-price elasticity: real CC commitment/dispatch is less fuel-responsive than the model's (SPP-69 §4 = SPP-75 §2) | **heat rates exonerated.** No measured driver found. |
| C4 gas 2022 NRMSE 0.321 | the same object (CC decommitted in low hours), plus the Jan-2022 F923 outlier | same; outlier routed |
| C3b 2020 / 2021 / 2022 (0.257 / 0.234 / 0.208) | the price body and shape (SPP-74) and the gas low side (SPP-75) | not reached |
| C3a 2020 +15.5 % | price level: the missing tail and congestion rent (SPP-70 R-bc, SPP-74) | not reached. A measured-HR arm would lower offers ~2 % and push C3a 2020 *down*, the right way, but that is not built here |

**Plainly: the heat rates are right, and the crossover defect has no measured driver in the offer
stack.** What remains is behavioural: utility self-commitment, hedged or contracted fuel versus
spot, and 2022 coal conservation. The dead list has already refused the gas-commitment family and
coal-inventory lanes, both for lack of a measured driver. **Route:** the next admissible input would
be a *published, per-year* SPP self-commitment share for gas CC (SPP MMU State of the Market). A
successor must measure that before proposing any commitment lever. Separately, route the
Jan-2022 F923 outliers to a fuel-price data lane.

## 7. Predictions (PRECOMMIT §4) scored

| # | prediction | outcome |
|---|---|---|
| P1 | reproduce SPP-69 §4 / SPP-75 §2 | **PASS**: SPP-75 exact; SPP-69 within 0.47 TWh, drift named |
| P2 | CC measured below model by 2–8 % | **PASS** on the applied window (−2.9 %). 2019–22 is −1.8 %, and the move comes from 2 blended rows |
| P3 | coal measured below model by 2–8 % | **MISS**: −1.7 %, just under the range. The sign is right, which contradicts the hypothesis |
| P4 | g* moves < $0.20 | **PASS**: +$0.02–0.03 every year |
| P5 | (4) FAILS | **PASS** |
| P6 | C3a 2020 would fall if armed | not scored (not armed) |

## 8. Secondary (SPP-75 §9.5 scoped CHP swap)

Not started. It needs a new field and a rule-28(c) PR, and its reach is ~10–14 % of the gas
low-side gap. It is left for its own lane, because the owner may prefer to hold it.

## 9. Standing items

- Matrix: SPP cells `measured_cc_heat_rates` / `measured_coal_heat_rates` /
  `measured_st_heat_rates` stay **U**, annotated with the zero-LP bound. They are not R or I: the
  field was not solved, and a rule-14 level correction of −1.7 to −2.9 % remains legitimate in its
  own right. The GRDA and Hawthorn blended rows are the strongest case for it. It is just not the
  crossover repair.
- `audit_keepers --iso SPP` and `check_mechanism_matrix` were re-run after the edit (see commit).
- No promotion question arises: nothing was solved.
