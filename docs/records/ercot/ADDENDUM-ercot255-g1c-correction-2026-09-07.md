# ADDENDUM — ercot-255 G-1c was WRONG as written, and G-3 needed splitting. Corrected BEFORE the screen solve.

> Amends `docs/PRECOMMIT-ercot255-zonal-spread-ep-reference-2026-09-07.md` §4.
> **Pushed before any LP was run.** The correction was found by running the
> pre-solve gates the PRECOMMIT itself registered — which is what they are for.
> Nothing else in the PRECOMMIT changes: the mechanism, the screen year (2025),
> the control form, and all eight 2021 predictions stand exactly as registered.

## 1. What was wrong

PRECOMMIT §4 registered **G-1c** as *"all West/Panhandle gas rows exactly 0.0
(owned by `ercot_west_netload_gas_shape`)"*, citing `RESULT-ercot254` §1's G-1″.

**That property belongs to ercot-254's arm, not to this one, and I transcribed it
without checking the mechanism.** `apply_ercot_west_netload_gas_shape` assigns

```
p_mean      = fuel_prices[west_rows, :].mean(axis=1)      # the INCOMING annual mean
deep_price  = max((p_mean - ffrac * firm_price) / cfrac, deliv_floor)
fuel_prices[west_rows, :] = where(collapse_mask, deep_price, firm_price)
```

so it is **annual-mean-preserving, not level-destroying**. ercot-254's monthly-EP
arm relocated the level *within* the year and left the annual mean untouched, so
`p_mean` did not move and West came out exactly inert. **This arm changes West's
annual mean by construction** — the mean-zero recentring cannot move the F923
group without moving the convention group — so West is expected to move, and
should.

## 2. The corrected gate, and what it measures

**G-1c (corrected): the West rows' ANNUAL MEAN delta equals the same per-zone
constant every other convention zone gets, i.e. the net-load step *inherits* the
corrected level rather than overriding it.** Measured, zero LP, on the
reconstructed fleets with each year's own measured monthly Henry Hub as the base
commodity:

| year | West Δ pre-step | West Δ post-step (annual mean) | preserved? | post-step hourly range |
|---|---|---|---|---|
| 2023 | +0.002984 | **+0.002984** | **yes** | +0.0000 .. +0.0994 |
| **2025** | −0.308237 | **+0.000000** | **NO — absorbed** | +0.0000 .. +0.0000 |
| 2021 | +3.510617 | **+3.510617** | **yes** | +0.0000 .. +8.3568 |

**2025 is a floor case, and it is the keeper's own mechanism doing it, not this
arm.** `deep_price` is floored at `ercot_west_gas_delivered_floor = 0.4`; in 2025
the unfloored value is deeply negative in *both* arms (the log's own
"floor-lifted from the negative hub tail"), so both land on the floor and West's
share of the redistribution is absorbed. That is a pre-existing property of
`ercot_west_netload_gas_shape` — it already breaks annual-mean preservation
whenever the floor binds — and it is **reported, not gated**, because gating it
would be gating a mechanism this arm does not touch.

The concentration in 2021 (+8.36 $/MMBtu on the collapse hours) is the same
arithmetic with the floor slack: a +3.511 annual-mean lift on 97 West units,
placed entirely on the 42 % of hours the collapse regime owns, is
+3.511/0.42 = +8.36. It is the step's design, not an artifact.

## 3. G-3 is split, and the mechanism's own seam still passes EXACTLY

PRECOMMIT §4 registered one level-neutrality gate at 1e-6. It is split, because
the two numbers answer different questions:

| gate | what it asks | 2023 | 2025 | 2021 | bar |
|---|---|---|---|---|---|
| **G-3 (gate)** | is *this mechanism* level-neutral, at its own seam (pre-west-step)? | −5.5e-17 | **−1.9e-17** | −4.9e-16 | > 1e-9 STOPs |
| **G-3b (reported)** | what survives the keeper's West floor? | −5.5e-17 | **+1.448e-02** | −4.3e-16 | reported |

**G-3 PASSES exactly — machine zero in all three years.** The arm is a pure
redistribution at the seam it acts on, which is the claim it had to earn.

G-3b's 2025 residual, +0.01448 $/MMBtu = **+0.106 $/MWh** at CC hr 7.29, is
exactly West's absorbed share: West is 2,813.03 / 59,889.53 = 4.697 % of ERCOT
gas capacity and its intended Δ was −0.308237, and 0.308237 × 0.04697 =
**+0.01448**. The identity closes to five decimals, so the residual is fully
attributed and nothing is unexplained. It is ~2 % of the screen year's own
footprint and it does **not** disturb prediction P6 (2021's G-3b is machine zero,
so 2021 is exactly level-neutral end to end).

## 4. The other pre-solve gates, as registered, all PASS

| gate | 2023 | 2025 | 2021 |
|---|---|---|---|
| **G-1a** per-zone Δ is one exact constant | spread 0.00e+00 | **≤ 8.88e-16** | ≤ 1.78e-15 |
| — F923 zones (North/Northeast/South_Central/South) | −0.001502 | **+0.155170** | −1.767281 |
| — convention zones (Houston, West) | +0.002984 | **−0.308237** | +3.510617 |
| **G-2** confinement, non-gas rows | 0.000e+00 | **0.000e+00** | 0.000e+00 |
| commodity floor touches (probe hygiene) | 0 / 15,978,240 | 0 | 0 |
| footprint, cap-weighted mean \|Δ\| | 0.0020 | **0.1919** | 2.3510 |

Every measured constant reproduces the PRECOMMIT §3 prediction to the sixth
decimal (predicted +0.155170 / −0.308237 for 2025; −1.767281 / +3.510617 for
2021). **G-1b** (the F923 identity `delivered = HH + raw[z]` up to the recentring
constant) is implied by G-1a + G-3 holding jointly and is not separately
reported. **G-4** (forward inertness) is carried by the unit tests rather than
by a fleet reconstruction, since a forecast year has no bundle to reconstruct.

**The screen year stays 2025** — its footprint, 0.1919 $/MMBtu post-step, is
96× 2023's and remains the largest in the training window. No gate is read
against C1.
