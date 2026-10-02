# FINDING — PJM-NEXT-28: sunk no-load in the committed rung is not the floor lever (zero LP, NOT CHARTERED)

**Keeper unchanged:** `2026-10-02-w0-pjm-fix2` (bundle `w0_pjm_span`). **Zero LP, zero shards, nothing registered.**
Probe `scripts/probes/_pjmnext28_sunk_noload.py` → `results/phase0/pjm/_pjmnext28_sunk_noload.json`.
Context: owner ruling on PJM-NEXT-27 *"Hold; closeout wave 1"*. The closeout lane killed R-13 (desk R), closed L2
at phase 0 (#7073), and promotes nothing.

## Hypothesis (side card a)

The closeout L2 RESULT named the remaining floor route: no-load folded into the committed rung. Once P0 fixes
commitment, no-load is sunk in P1, and PJM's LMP excludes it (it is paid through make-whole). Pricing the committed
rung at the plant's measured CAMPD incremental HR (L2 artifact, `d8cf825a`) would lower the low-end floor. Per
PJM-NEXT-17 card 1b, that floor drives the COAL_BIT over-loading.

## Pre-fixed readings and result

The gates were fixed before any number was computed:
- **R2:** p10 implied-HR shift ≥ 0.5 MMBtu/MWh in 2019, 2020 and 2021.
- **R3:** COAL_BIT unload ≥ 3 TWh in 2019 and 2021, and smaller in 2023/24.

| year | committed CC+coal marginal share | mean Δp in those hours ($/MWh) | p10 implied HR old→new | COAL_BIT unload bound (TWh) |
|---|---|---|---|---|
| 2019 | 0.051 | 0.14 | 7.01→7.02 | 0.33 |
| 2020 | 0.053 | 0.24 | 7.03→7.02 | 0.31 |
| 2021 | 0.070 | 0.81 | 6.98→6.96 | 0.60 |
| 2022 | 0.074 | 2.10 | 7.51→7.44 | 0.29 |
| 2023 | 0.034 | 0.74 | 7.69→7.67 | 0.11 |
| 2024 | 0.061 | 0.26 | 8.49→8.46 | 0.10 |
| 2025 | 0.023 | 1.11 | 7.82→7.81 | 0.09 |

**R2 FAIL:** the largest shift is 0.07. **R3 FAIL:** 0.33 and 0.60 TWh, against C1 gaps of +16 to +22. The year
ordering holds, but the size is 10–50× too small.

Hours priced below 6.5 × gas move from 2.6 % to 3.1 % in 2019, against 36 % real. The Δp column is a first-order
upper bound: no re-dispatch and no change in which unit is marginal.

## Why it fails

- **Committed rungs rarely set price.** CC and coal committed tranches are the attributed price-setter in only 2–7 %
  of load-hours.
- **Coal has nothing to remove.** The keeper's coal committed rung is already priced at 0.51–0.68 × average HR, below
  any incremental HR, so there is no folded no-load.
- **The CC drop is often negative.** In 2019–20 most marginal committed CCs have a measured incremental HR *above*
  their committed-rung HR (only 24–30 % sit below).

**Method.** Each zone-hour is attributed to the marginal unit whose `mc` is closest to the zone price, within 6 %.
That covers 67–75 % of load; the unattributed rest is left unchanged.

## Consequence

The floor gap (model p10 7.0–8.5 × gas vs real 4.8–5.5) does not come from no-load in committed rungs. The
low-end price-setters are econ and other tranches, not committed ones. COAL_BIT side card (a) stays **OPEN, not a
model-class limit**. No field is built and no matrix row is added (nothing was built).

Side card (b), the Tait 55248→2847 remap: scoped in `FINDING-pjm-closeout-wave1-censuses-2026-10-02.md` §6. It rides
the next PJM solve as a rule-14 repair, one delta per solve.
