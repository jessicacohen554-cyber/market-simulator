# FINDING soco-94 — C3a year-pattern diagnosis (zero LP)

**Owner ruling in force (soco-93 card "Next lane"):** "C3a year-pattern diagnosis (Recommended)". Zero LP: no solve,
no registration, no mechanism tested, so no matrix cell moves. Keeper unchanged: `2026-09-30-soco93-pondage-bound`
(`results/calibration/soco93_span`), NOT-YET 7/4/0/1/2. soco-93's PR #6904 was still open at branch time, so this
branch sits on its head `38f0b9d786ba4c82bc373f41af982b61e2ddea9f`.

## Conclusion — no admissible lever; the "gas year" pattern is not a gas-level effect

1. **Fuel pass-through is faithful, gas and coal separately (§2).** Against each plant's own EIA-923 Sch. 2 delivered
   price, quantity-weighted by month, the model's gas is within −4.2 % to +2.9 % in every year, and coal is exact (the
   model already prices coal from its own plant's receipts). Re-pricing each hour's setter at the delivered price its
   own plant paid that month moves C3a by ≤ 0.6 pp wherever receipts are dense.
2. **The sign flip does not follow the gas price (§3).** At equal Henry Hub, the outcomes differ: 2019 ($2.57) is
   +14.1 % and 2023 ($2.54) is +2.4 %; 2020 ($2.03) is +14.4 % and 2024 ($2.19) is −3.5 %. Median λ is the same in
   each pair. The difference is entirely in λ's upper tail.
3. **What separates the years is λ's peak premium over the CT offer (§4).** In top-20 % λ hours a CT_PEAKER sets the
   model price in 37–68 % of hours. λ there implies a CT heat rate of **11.2–11.5 in 2019–20** (≈ the model's average
   HR, 11.1–11.2) but **12.8–16.3 in 2021–25**. The low-40 % offset (+$1.9 to +$3.3/MWh) is present in every year.
   2019–20 fail because no peak premium offsets it; 2022 fails because the premium swamps it.
4. **The premium is not a benchmark step, and not model tightness (§4).** It does not start at the CSV→XBRL switch
   (Jan 2021): by month it sits in summer peaks and winter cold snaps (Jan 2023–25 top-10 % λ at 1.8–3.6× the CT
   offer, Dec 2022 5.3×). The model's reserve margin in top-20 % λ hours is 0.26 in 2019 and 0.26–0.29 in 2022–25,
   so the model is as tight in 2019 as in the premium years.
5. **Setter mix differs, but not enough to matter.** Coal sets 32–43 % of top-20 % hours in 2019–20 against 4–13 %
   later, and gas sets 56–61 % against 70–85 %. Within the gas-set hours, though, the gap is −$0.1 to −$0.2 in
   2019–20 against −$1.7 to −$9.3 later. The mix shift follows the λ premium; it does not cause it.

The candidate objects for the premium are the same ones soco-89/90/91 named, and every one is adjudicated: CT start
and no-load recovery (owner NO), a daily or winter SE gas spike (owner "Don't buy"), and CT incremental HR (I). The
low-end offset is the soco-91 night CC setter at λ ≈ 0.75–0.83 × its offer (CC incremental HR, owner "Keep refused").

## 1. Method

Probe: `scripts/probes/_soco94_year_pattern.py` (new). For each year it does one `fleet_only` rebuild of the keeper
recipe (the soco-89/91 construction, now also carrying `plant_code` and VOM). It uses the soco-91 setter rule
(offer within ±$0.50 of the price and the setter's class-band interior that hour). For setter-matched hours it splits
the offer into `HR × fuel_model + other` (`other` = `mc_base − HR × fuel`: VOM, $2.0 CC to $4.5 coal). It looks up the
delivered $/MMBtu the setter's own plant paid that month
(`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`, Coal and Natural Gas groups). Then
`fuel_err = HR × (fuel_model − fuel_F923)` is the first-order part of the gap a measured plant-month price would
remove. C3a reproduces exactly: +14.1 / +14.4 / −2.4 / −12.4 / +2.4 / −3.5 / −1.5 %.

## 2. Does the model's fuel track the measured delivered fuel?

| year | HH | gas F923 / model $/MMBtu | coal F923 / model | C3a | C3a, setter at own plant-month F923 | setter hours with own-plant receipts |
|---|---:|---|---|---:|---:|---:|
| 2019 | 2.57 | 2.842 / 2.811 | 2.460 / 2.460 | +14.1 | +13.5 | 55 % |
| 2020 | 2.03 | 2.350 / 2.340 | 2.317 / 2.317 | +14.4 | +14.0 | 41 % |
| 2021 | 3.72 | 4.212 / 4.035 | 2.374 / 2.374 | −2.4 | −2.0 | 45 % |
| 2022 | 6.45 | 7.681 / 7.904 | 3.177 / 3.177 | −12.4 | −12.2 | 50 % |
| 2023 | 2.54 | 3.027 / 3.021 | 3.548 / 3.548 | +2.4 | +8.2 † | 53 % |
| 2024 | 2.19 | 2.830 / 2.855 | 3.168 / 3.168 | −3.5 | −3.3 | 51 % |
| 2025 | 3.52 | 4.182 / 4.127 | 2.928 / 2.928 | −1.5 | −0.9 | 52 % |

† 2023 is an artefact of thin CT receipts: CT plants that receive gas in small spot lots report $5–6/MMBtu in some
months against a $3.03 fleet average. Nearly all of the 2023 move is CT-set hours in the low-40 % and mid bands
(mean offer error −$26.7 and −$35.6/MWh there).

## 3. Equal gas price, different C3a (load-weighted gap by λ band, $/MWh)

| year | HH | low 40 % | mid | top 20 % | total | λ median / p90 / p99 |
|---|---:|---:|---:|---:|---:|---|
| 2019 | 2.57 | +2.54 | +1.52 | −0.27 | +3.78 | 26.3 / 33.1 / 49.7 |
| 2023 | 2.54 | +1.86 | +0.89 | −2.02 | +0.73 | 25.8 / 40.2 / 60.5 |
| 2020 | 2.03 | +1.87 | +1.53 | −0.25 | +3.15 | 18.8 / 29.3 / 43.8 |
| 2024 | 2.19 | +2.05 | +0.49 | −3.60 | −1.06 | 23.8 / 39.3 / 86.1 |
| 2022 | 6.45 | +3.27 | −1.66 | −11.67 | −10.07 | 60.8 / 123.6 / 223.1 |

An across-year OLS on HH gives model = 5.15 + 10.0 × HH and λ = −3.1 + 12.7 × HH. Read with the pairs above, that
slope is the tail premium arriving in 2021–25, not a pass-through coefficient: at the same HH, λ moves by 15 % and
the model by 4 %.

## 4. The top-20 % hours: setter mix and λ's implied CT heat rate

| year | gas-set share (gap) | coal-set share (gap) | hydro/storage share (gap) | CT setter P / λ | λ-implied CT HR vs model HR |
|---|---|---|---|---|---|
| 2019 | 0.56 (−0.08) | 0.43 (−0.19) | 0.00 | 35.4 / 36.0 | 11.2 vs 11.1 |
| 2020 | 0.61 (−0.17) | 0.32 (−0.10) | 0.06 | 30.0 / 31.2 | 11.5 vs 11.2 |
| 2021 | 0.70 (−2.05) | 0.04 (−0.20) | 0.26 (−0.67) | 56.0 / 67.5 | 12.8 vs 10.5 |
| 2022 | 0.80 (−9.25) | 0.04 (−0.64) | 0.15 (−1.78) | 105.5 / 152.6 | 15.6 vs 10.7 |
| 2023 | 0.85 (−1.70) | 0.13 (−0.30) | 0.02 | 37.6 / 46.1 | 13.9 vs 11.2 |
| 2024 | 0.82 (−2.83) | 0.13 (−0.59) | 0.05 | 35.1 / 50.9 | 16.3 vs 10.9 |
| 2025 | 0.78 (−3.70) | 0.11 (−0.50) | 0.11 | 49.2 / 70.3 | 16.0 vs 11.0 |

Implied HR = (λ − VOM) / model fuel in the same hours. Fuel is faithful (§2), so this is the premium in HR units.
Monthly top-10 % λ ÷ capacity-weighted CT offer is 0.83–1.25 in 2019–20. In 2021–25 it rises to 1.2–1.6 in Jun–Aug,
with cold-snap spikes (Dec 2021 1.9, Dec 2022 5.3, Jan 2023 1.8, Jan 2024 2.4, Jan 2025 3.6). There is no step at
January 2021. Model reserve margin (available capacity − demand, ÷ demand) in top-20 % λ hours:
0.26 / 0.33 / 0.35 / 0.26 / 0.27 / 0.29 / 0.26.

## 5. Admissibility (rules 1 / 13 / 14)

- **No measured, year-regenerable input closes either error.** Fuel is already the measured plant-level delivered
  price. The premium is not in any committed fuel series, and its seasonal and cold-snap timing is the signature of
  the adjudicated CT start / no-load and daily-gas families.
- **Offer-curve band channel.** It would need to lift the CT bands and cut the CC bands. soco-91 showed any value
  would be read off this residual, which condition (c) forbids. SOCO has declared no authorized price tuning.
- **Rule 14.** The benchmark is still like-for-like on every measurable axis (soco-89 §3). No misalignment is
  established that would justify an estimate over the measured λ.

## 6. Records

- Probe: `scripts/probes/_soco94_year_pattern.py` (`--out DIR` writes `year_<y>.json`, `regression.json` and the
  cached `fleet94_<y>.npz`).
- Keeper unchanged; NOT-YET 7/4/0/1/2. SOCO is not frontier.

## 7. Owner ruling 1 (decision card, 2026-09-30): "Reopen CT start/no-load" — checked at zero LP, refuted

Before any work, the reopen was checked against three facts. Together they close it on the benchmark's own
definition, not on a residual.

1. **Southern's λ has no start or no-load term.** Its Schedule VI formula is
   `λ = [(2aP + b)(FC + EC) + VOM + FH] × TPF` (soco-82 §3): incremental HR × (replacement fuel + emission cost), plus
   VOM, fuel handling and loss penalty. A start cost cannot appear in λ, so it cannot explain λ's premium.
2. **soco-92 §4 already bounded its reach.** A start amortized over SOCO's measured CT runs adds $0.2–3.3/MWh against
   a $6–47 premium, and the no-load half moves the CT offer down (wrong sign). Owner: "Close the reopen".
3. **The model has no CT block at λ's implied heat rate.** In top-20 % λ hours the model's available CT fleet is
   8.5–9.1 GW at a capacity-weighted HR of 11.4–11.6. Only 160–330 MW sits at HR ≥ 13, and 8.5–10.6 GW is offered
   above the price and left unused. λ's implied 12.8–16.3 in 2021–25 matches no material block of SOCO's CT stack, so
   a tighter peak would not reach it either.

Every term left in the formula is therefore closed or inadmissible. The incremental HR `2aP + b` for a CT is below
average (soco-92, wrong sign). The replacement fuel `FC` is the daily SE gas series (owner "Don't buy"). SOCO has no
emission price in `EC`. `TPF` is a few percent at most. **The premium's only candidate object is replacement fuel.**
Its timing (summer peaks and cold snaps; §4) is also the signature of SE daily gas spikes, which HH daily does not
carry (Elliott: HH 117.8 vs SE 406.8, soco-89 §4).

## 8. Owner ruling 2 (decision cards, 2026-09-30): "Rubric: ledger C3a vs λ" — implemented as rubric v3.11

The owner chose "Exact rows, direction-bound" for scope and "Spend the slot, downgrade" for budget. The rows are
`(SOCO, 2019, price_mean)` over, `(SOCO, 2020, price_mean)` over and `(SOCO, 2022, price_mean)` under, on the v3.10
scoped-ledger machinery with every guard unchanged (`scripts/calibration_verdict.py`; genealogy
`docs/governance/rule-history.md` §24; tests `tests/scoring/test_calibration_verdict_scoped_ledger.py`).

**Effect**, re-scored over all 11 registered runs × full span and every single-year subset (72 verdicts):

| scope | before | after |
|---|---|---|
| SOCO keeper, 2019–2025 | NOT-YET 7/4/0/1/2 (FAIL: price_mean, price_shape) | **NOT-YET 7/4/0/2/1** (FAIL: price_shape) |
| SOCO keeper, 2019 alone | NOT-YET | NOT-YET (budget: ledgered 2/1) |
| SOCO keeper, 2020 alone | NOT-YET | CALIBRATED-WITH-CAVEATS |
| SOCO keeper, 2022 alone | NOT-YET | NOT-YET (C3b 0.275) |
| every other run / year | — | byte-identical verdict |

**SOCO is not frontier.** Two things still stand between it and a clean determination. The C3b 2022 FAIL (0.275
vs ≤ 0.20) remains. And the ledgered budget is now 2 against 1 (C1 2019 COAL_BIT plus C3a), so even a C3b fix would
leave the full span NOT-YET unless the owner also rules on the budget.

Refreshed surfaces: `results/calibration/soco93_span/metrics.json` (`--write-metrics`), `frontend/data/backcast/status/`
(`build_status.py --iso SOCO`; `shared.js` moves only its `rubric_version`), the keeper sidecar's definition line,
and the SOCO matrix shard's keeper/gates stamp. No matrix cell moves: no mechanism was tested.
