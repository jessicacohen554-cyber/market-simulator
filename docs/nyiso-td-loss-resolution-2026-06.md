# NYISO td_loss / gas-total deficit — resolution (2026-06)

**Verdict: `td_loss_factor` stays `0.0` for NYISO. No model change.** The
reopened "starve-gas-because-no-loss-gross-up" hypothesis is **refuted by the
NYISO Gold Book itself**: the demand the model serves already includes T&D
losses, so a gross-up would double-count (rule #11/#12). The residual gas-total
deficit is the documented EIA-923-vs-EIA-930 *benchmark-basis* reconciliation
plus the priced import node's economic deviation from measured interchange —
neither is a dispatch error, and neither is closable by an honest knob.

This supersedes the speculative item-1 ("DOMINANT ~6 TWh td_loss gross-up") in
`docs/nyiso-load-basis-handoff.md` and **confirms with direct evidence** the
prior `td_loss = 0` decision in `docs/calibration-best-so-far-nyiso.md`.

## The decisive evidence: the served demand already includes T&D losses

NYISO **Gold Book Table I-2 (NYCA TOTAL, Annual Energy, GWh)**, the official
"Load & Capacity Data" — *actual* historical column:

| year | Gold Book actual NYCA Annual Energy | source | model served demand (EIA-930) |
|---|---|---|---|
| 2023 | **147,050 GWh** | 2024 & 2025 Gold Book, Table I-2 | 147,050 GWh |
| 2024 | **150,938 GWh** | 2025 Gold Book, Table I-2 | 150,460 GWh |

Gold Book Table I-2 **Note 1 (verbatim, all three books): "All results in the
Section I tables include transmission & distribution losses."** So the Gold
Book's Annual Energy *is* the net-energy-for-load on the busbar / generation-
requirement basis (load **plus** T&D losses). It equals the EIA-930 `NYIS
hourly` demand the model serves (definitional — NYISO reports this same load to
EIA). 2023 matches to the GWh; 2024 to 0.3%.

**Therefore the model's served demand is already grossed up for T&D losses.**
`generation = demand − net_interchange` already carries the loss volume. Setting
`td_loss_factor > 0` would add the losses a **second** time — a fitted adder
with no forward analogue (the loss is already in the input), exactly what rules
#11/#12 forbid. This is the head-on answer to the handoff's item-4 challenge
("explain why gas should equal load−imports with no loss volume"): because
**`load` here already contains the loss volume** — it is NYISO's loss-inclusive
net energy for load, not metered end-use.

The Gold Book gives **no explicit transmission-loss percentage** anywhere (only
Note 1's statement that the energy is loss-inclusive). The handoff's premise
that "the authoritative loss factor lives in the Gold Book" does not hold; what
the Gold Book authoritatively establishes is the *basis* (loss-inclusive), which
is what settles the question.

## Why the handoff over-estimated the gap (the 125 vs 129.7 error)

The handoff's "~6 TWh / 4.5%" came from comparing the EIA-930 demand basis to
the **full** EIA-923 plant net generation (129.67 TWh, 2023). But the dashboard
C1/C2 scorer (`scripts/calibration_verdict.py`, `score_fuelmix`/`score_sysvol`)
benchmarks against the **grid-delivered** `classFull` total (EIA-923 − BTM CHP
self-supply = **125.0 TWh**, 2023) — model-grid vs actual-grid. Against the
basis that is actually scored, the gap is **1–3%/yr, not 4.5%**.

## Baseline (current keeper config, P1, all 3 years) — confirmed numbers

Re-solved `--gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily
--priced-interchange --energy-reserve-coopt --nyiso-local-selfsupply
--nyiso-firm-imports` (the keeper config, no `--commitment`; bundle
`results/calibration/_diag_nyiso_baseline`):

| year | model gas | bench gas (grid) | gas Δ | model imports | measured net interchange | in-state gen, model | EIA-923 grid total | residual @ measured imports |
|---|---|---|---|---|---|---|---|---|
| 2023 | 60.95 | 59.17 | **+3.0%** | 18.53 | 23.45 | 128.73 | 125.0 | −1.4 (−1.0%) |
| 2024 | 59.98 | 67.80 | **−11.5%** | 21.65 | 20.35 | 128.98 | 134.56 | −4.3 (−2.9%) |
| 2025 | 63.80 | 70.25 | **−9.2%** | 21.63 | 19.09 | 130.17 | 133.95 | −1.5 (−1.0%) |

Demand is fully served every year (no slack/dump). The "residual @ measured
imports" column is what the in-state fleet would land at if the import node
cleared the *measured* net interchange — i.e. the pure EIA-923/EIA-930 dataset
reconciliation: **1.0% / 2.9% / 1.0% short**. That is the floor; it is a
difference between two EIA datasets, not a model error (rule #1: do not chase a
benchmark-basis difference with a fitted knob).

## The two real (smaller) effects, and why neither is the prescribed fix

1. **The 2023 "+3.0% gas" is itself an import artifact.** The priced node
   *under*-imports in 2023 (18.53 vs measured 23.45 TWh) because the deep import
   tranches price above NY's low-gas-year clearing price and the firm-import
   floor sits below the measured baseload. The in-state fleet (gas, the swing)
   fills the ~4.9 TWh shortfall, which is the *only* reason 2023 gas reads on.
   Correct the imports to measured and 2023 gas drops to ≈ −5% — i.e. the
   deficit is **uniform ~1–3% across all three years** once imports are
   accurate. So 2023 is not a counter-example to a real shortfall; it is the
   same shortfall masked by under-importing.

2. **Import reconciliation is zero-sum on the backcast.** Pinning the node to
   measured net interchange (rule #11: measured > economic-clearing) adds
   +1.3 / +2.5 TWh gas in 2024/25 but *removes* 4.9 TWh in 2023. Net ≈ 0 across
   years, and it trades the 2023 match for the 2024/25 match. The prior team
   already rejected import scaling as "degrading a measured match to paper over
   a benchmark-basis difference" (`calibration-best-so-far-nyiso.md`). It is a
   legitimate accuracy improvement to the *imports* in isolation, but it does
   **not** create the 6–8 TWh of gas the handoff sought, because that energy
   does not exist in the balance: demand already includes losses, and
   `gen = demand − net_imports`.

## Adjacent observations (separate issues, NOT this task)

- **2024 non-gas over-runs displace ~2.6 TWh of gas:** oil 1.95 vs bench 0.32
  (+1.63), biomass 1.38 vs 0.76 (+0.62), hydro +0.38. Bringing oil/biomass to
  band would recover a few TWh of gas — an offer-curve / dual-fuel issue, not
  td_loss.
- **2025 hydro budget is data-incomplete:** the solve logs "3 plants,
  21,048 GWh" for 2025 vs "154 plants, 28,403 GWh" for 2023; hydro lands 21.05
  vs bench 24.10 (−3.05). This is a 2025 EIA-923-preliminary data gap in the
  hydro energy budget, worth a separate fix.

## Bottom line

`td_loss_factor = 0` for NYISO is correct and now **Gold-Book-confirmed**, not
merely conventional. The gas-total "deficit" is (a) a 1–3% EIA-923/EIA-930
benchmark-dataset reconciliation (documented floor, not a dispatch error) and
(b) import-node economics that are zero-sum to reconcile. There is **no honest
knob** that adds the handoff's 6 TWh of gas, and the prescribed td_loss
gross-up is a double-count. The keeper is unchanged.
