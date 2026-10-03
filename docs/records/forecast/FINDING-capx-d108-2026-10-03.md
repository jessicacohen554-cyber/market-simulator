# FINDING — capx D108: the T1-F battery is insensitive to what moved the trajectory (owner decision card)

**Lane** capx D108 (desk-computed, zero LP) · **date** 2026-10-03 · **read at** `origin/main` `51422d1b` ·
**inputs** the four committed `results/ff-t1f-{d50,d105}/neiso/` and `results/ff-t1f-{d60,d106}/nyiso/`
`full_horizon_summary.json` (`trajectory[]`) and `frontend/data/forecast/ff-verdicts.json` · **authority** capx ledger
§0bn.4c standing read ("a rubric question for FF rubric §3, not a solve question").

## 1. The verdict rows did not move

| verdict key | determination | FC-1 | FC-2 | FC-3 | FC-4 | FC-5 | FC-6 | FC-7 | FC-8 |
|---|---|---|---|---|---|---|---|---|---|
| `neiso-t1f-pre-d105` (D50, `18515067bf4d2fbe`) | PROMOTE | PASS | PASS | n/a | n/a | SKIPPED | SKIPPED | PASS | PASS |
| `neiso-t1f` (D105, `66fb439918cbefd6`) | PROMOTE | PASS | PASS | n/a | n/a | SKIPPED | SKIPPED | PASS | PASS |
| `nyiso-t1f-pre-d106` (D60, `19a9690bb12c8459`) | PROMOTE | PASS | PASS | n/a | n/a | SKIPPED | SKIPPED | PASS | PASS |
| `nyiso-t1f` (D106, `374fa81075c95ff8`) | PROMOTE | PASS | PASS | n/a | n/a | SKIPPED | SKIPPED | PASS | PASS |

## 2. The trajectory did (prior → new, per year)

**NEISO, D50 → D105**

| year | CO2 Mt | LW price $/MWh | max hourly $/MWh | hours ≥ 100 | reserve margin | gas_cc_ccs TWh | gas_cc TWh |
|---|---|---|---|---|---|---|---|
| 2026 | 16.31 → 16.01 (−2 %) | 52.1 → 51.7 | 69.7 → 65.9 | 0 → 0 | 0.155 → 0.168 | 0 → 0 | 40.4 → 39.6 |
| 2027 | 17.60 → 17.21 (−2 %) | 53.3 → 51.2 | 280.4 → 236.6 | 5 → 3 | 0.046 → 0.048 | 0 → 0 | 40.2 → 39.8 |
| 2028 | 16.81 → 9.90 (**−41 %**) | 58.1 → 52.2 | 283.6 → 239.5 | 13 → 4 | 0.032 → 0.040 | 2.4 → 22.4 | 36.6 → 17.6 |
| 2029 | 15.35 → 4.73 (**−69 %**) | 62.5 → 51.4 | 284.9 → 240.9 | 9 → 3 | 0.033 → 0.044 | 10.6 → 36.6 | 24.1 → 4.2 |
| 2030 | 14.98 → 5.97 (**−60 %**) | 69.7 → 53.7 (−23 %) | 282.8 → **84.3** | 2 → 0 | 0.066 → 0.084 | 19.2 → 26.2 | 14.5 → 8.7 |

Window: cumulative CO2 81.0 → 53.8 Mt (−34 %); mean LW price 59.1 → 52.1; builds 4,050 → 4,000 MW; retirements
2,371 → 2,757 MW.

**NYISO, D60 → D106**

| year | CO2 Mt | LW price $/MWh | max hourly $/MWh | hours ≥ 100 | reserve margin | gas_cc_ccs TWh | gas_cc TWh |
|---|---|---|---|---|---|---|---|
| 2026 | 23.74 → 24.17 (+2 %) | 50.2 → 50.9 | 64.8 → 66.0 | 0 → 0 | 0.184 → 0.185 | 0 → 0 | 55.3 → 55.5 |
| 2027 | 24.64 → 25.06 (+2 %) | 49.2 → 49.8 | 62.6 → 64.6 | 0 → 0 | 0.181 → 0.177 | 0 → 0 | 57.4 → 57.8 |
| 2028 | 24.24 → 17.64 (**−27 %**) | 54.1 → 51.3 | 65.1 → 66.6 | 0 → 0 | 0.178 → 0.170 | 10.4 → 22.8 | 45.5 → 35.7 |
| 2029 | 23.78 → 14.12 (**−41 %**) | 55.4 → 49.1 | 69.3 → 66.8 | 0 → 0 | 0.220 → 0.208 | 14.7 → 29.9 | 38.4 → 28.5 |
| 2030 | 20.98 → 11.49 (**−45 %**) | 61.1 → 55.1 (−10 %) | 77.3 → 74.3 | 0 → 0 | 0.217 → 0.201 | 24.7 → 37.8 | 28.1 → 20.1 |

Window: cumulative CO2 117.4 → 92.5 Mt (−21 %); mean LW price 54.0 → 51.2; builds 3,843 → 3,853 MW.

## 3. Why the battery cannot see it — by construction, not by defect

Rubric §3's `t1f` column requires FC-1 (invariants), FC-2 (adequacy rows 1/3/4), FC-7 (provenance) and FC-8 (runtime,
never blocking). FC-3/FC-4 are `—` at t1f, FC-5 is report-only and FC-6 is optional (SKIPPED here). Every row the tier
scores is an **admissibility** test; none compares a trajectory against a reference or against its own predecessor. A
T1-F re-solve on a moved posture therefore re-certifies admissibility and is silent on what moved. The skill and
response categories that could see the shift (FC-3/4 imported scores, FC-5 corridor, FC-6 driver battery) are required
only at t2/t3.

The deltas are not obviously wrong: the 2028+ timing matches the converted `gas_cc_ccs` fleet dispatching ahead of
unabated CC once the Q47 adder (8.0 → 2.95 $/MWh) and the CO2-scaled retrofit capex land. They are also not
attributed — one instrument per ISO, no control (D105/D106 both said so). There is no external reference against which
a 2028–2030 trajectory delta could be scored PASS/FAIL; a gating row would score *stability between config vintages*,
which penalizes a real fix as readily as a regression (rule 1).

## 4. Card (D108) — served in the r#70 closing report

> **The T1-F battery is insensitive to the W0 keeper and the Q47 CCS re-pricing while the trajectory is not
> (CO2 −27 to −69 % in 2028–2030; NEISO 2030 price tail 283 → 84 $/MWh). What should FF rubric §3 do?**
>
> 1. **Report-only supersession-delta row (recommended).** Rubric v1.2: when a verdict supersedes a preserved prior
>    (`<key>-pre-<lane>`), the scorer prints the per-year CO2 / LW price / max-price / hours ≥ 100 / CCS-share deltas
>    as an `rpt` annotation at every tier. Never gates. Zero verdicts move (computed: all four keys stay PROMOTE).
>    Implementation is one Fable code lane, zero LP.
> 2. **Accept PROMOTE as-is.** T1-F stays an admissibility tier; trajectory content is judged at t2/t3 by FC-3–6.
>    Record the insensitivity in rubric §7 (honest limits) only.
> 3. **Make FC-6 required at t1f.** The driver battery becomes the t1f sensitivity instrument. Costs LP per ISO
>    (battery rungs on a five-year window); both current t1f verdicts would read HOLD (FC-6 SKIPPED) until re-run.

Rule 37 binds the *backcast* determination rubric only; the forecast rubric is not under its freeze, but the desk
treats any FF rubric change as an owner ruling all the same.

## 5. RULING (owner, 2026-10-03, this desk session)

**"Report-only delta row."** Option 1 adopted: FF rubric v1.2 adds a report-only supersession-delta annotation; it
never gates and moves no verdict. Implemented by lane **D111** (Fable code shard, zero LP, branch
`claude/capx-d111-ff-rubric-delta`).
