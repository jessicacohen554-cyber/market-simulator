# NYISO 59 — measured hourly reserve requirements (dynamic-RR, #1344 Ask-B) — KEEPER CANDIDATE

The `2026-07-07-nyiso-56-measured-zonal` keeper recipe VERBATIM with exactly
one change, a **measured-data** change (rules 12/13, zero new free
parameters): `nyiso_dynamic_reserve_requirements=True`. The in-LP
energy+reserve co-optimization's static published locational reserve
requirements are replaced by the **measured as-enforced hourly series** (the
Ask-B intake, `data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_{year}.csv`,
derived by the frozen `scripts/derive_nyiso_reserve_requirements_hourly.py`):

- **B3** — the published LRR base with the SENY 30-min **hourly step
  schedule** (1,300 HB0–5 / 1,550 HB6 / **1,800 HB7–21** / 1,550 HB22 /
  1,300 HB23, in force all of 2023–2025): the static 1,300 MW the design
  enforced was the overnight floor, 500 MW low in every peak hour.
- **B2** — TSA-window zeroing from the MIS event logs (NYC 10T/30T + SENY
  30T requirements drop to zero during Thunderstorm Alerts, v2021+ rule):
  185/227/120 h in 2023/24/25.

The measured reserve **prices** are the validation target and are never read
by the loader (it raises when the file is absent — no silent static
fallback). The series is a documented **lower bound** in non-TSA hours until
the B1 formal data request lands (condition-varying increments are not
freely published). This closes the data-blocked half of the keeper's open
item (2)/#1344.

## Result (vs the nyiso-56 keeper, v2.4 lw price basis)

Metrics **wash** on price level/shape; a real RT-like scarcity tail appears:

| metric | keeper nyiso-56 | nyiso-59 | actual |
|---|---|---|---|
| C3a 2023 / 2024 / 2025 | pass / −13.1% / −15.5% | pass / −13.2% / −15.7% | ±10% band |
| C3b NRMSE 2024 / 2025 | 0.220 / 0.215 | 0.221 / 0.215 | ≤0.20 band |
| C3c >$300 h 2023 / 2024 / 2025 | 21 / 0 / 14 | 23 / **1** / **25** | RT 10 / 12 / 42 (DA 1 / 0 / 12) |
| C5a CO2 caveat | 2024 −7.3% | 2025 +8.6% (2024 clears) | ±7% target / ±10% commercial |

C1 fuel-mix 14/14 PASS, C2 PASS, C4 PASS, C7 PASS, **C8 clean PASS**
(ST_GAS 30.3/44.5/38.0% forced — grounded above budget: all binding
mechanisms clear the cited D-4 windows, D-1 r 0.948–0.956). The 2024 mild
year gains its first modeled scarcity hour and 2025 moves 14→25 h toward
the 42 h RT actual (~26% of the residual RT-tail gap) — priced by the
measured requirement, never a tuned curve. The 2025 DA-expressible gate
reads 2.08× (25 vs 12 DA h) — the same G-20a scoring-basis artifact the
keeper ledgers for 2023 (the co-opt's single price is RT-like), ledgered.

**Determination: CALIBRATED-WITH-CAVEATS** (same as keeper; 3 ledgered
price caveats + C5a commercial band). Rule 1: kept and promoted on its
measured basis (measured hourly requirement > static stand-in — the exact
promotion logic of nyiso-56's measured load shares), not on residual
movement. Zero-forcing ablation twin registered alongside
(`2026-07-10-nyiso-59-dynamic-rr-ablation`; floors-off prices sit higher —
2023 33.08 vs 29.49, 2024 35.13 vs 31.90 simple-mean — the floors force
cheap steam-base energy, they do not manufacture the tail).

## Reproduce

CI replay of this recipe OOMs GitHub-hosted runners in `regenerate_clean`
(4 attempts 2026-07-10); solve locally with ≥15 GB + swap:

```
python scripts/regenerate_clean.py
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso59_dynamic_rr \
  --iso NYISO   # in-place re-solve; add --zero-forcing-ablation + --out-dir .../nyiso59_dynamic_rr-ablation for the twin
```
