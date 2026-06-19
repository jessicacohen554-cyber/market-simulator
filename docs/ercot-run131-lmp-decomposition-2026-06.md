# ERCOT run131 — decomposing the 2025/2024 co-opt LMP hot bias

**Date:** 2026-06-18
**Branch:** `claude/ercot-run131-offer-mults-v5pz98`
**Baseline-to-beat:** run129 (`ercot_dam_offers_cconly_3yr`, the CC-only measured
DAM-offer curve + energy/reserve co-opt). Companion:
`docs/ercot-lmp-cooling-session-prompt.md` (the handoff),
`docs/lmp-decomposition-2026-06.md`, `docs/ordc-overlay.md`,
`docs/ercot-dam-offer-hrmults-2026-06.md`.

This is the handoff's mandated **first-hour decomposition**: which lever owns the
2025 LMP hot bias, *before* sweeping. Headline: the bias is the **co-opt ORDC
reserve adder over-firing in a comfortable year**, not the offer curve. The
sub-$20 price floor is the measured CC body and is not independently fixable
without a markup.

## Environment / provenance note

These numbers were produced during the input-recovery window, before
`data/raw/eia-930-hourly/ERCO hourly.parquet` was committed to `main`. At the
time the loader's extract was unavailable and `api.eia.gov` (the canonical
`scripts/fetch_eia930_hourly.py` source) is egress-blocked here, so the extract
was rebuilt offline by reshaping the already-committed region (D/NG/TI) and
fuel-type series (`data/raw/ERCO_region.parquet` / `data/raw/ERCO_fueltype.parquet`)
with the fetcher's exact pivot + local-time transform — a pure reshape, no
egress, no fabricated values. That rebuild reproduced run129's **documented 2025
signature exactly (6 hours <$20)**, confirming it was faithful for demand and
the fuel mix.

`main` now ships the canonical 10.76 MB `ERCO hourly.parquet` directly, so the
offline rebuild is no longer needed. The **qualitative decomposition below is
robust** (it is a structural energy-only-vs-co-opt and floor-on-vs-off split,
not a fitted result); the **exact $/MWh figures should be re-confirmed against
the shipped extract** before they anchor a keeper — they are expected to move at
most a dollar or two.

## Method

run129 recipe (the handoff command, with the `data/raw/_validation-source/`
relocation of the offer-curve JSONs and `--offer-curve-json` replacing the
renamed `--offer-curve-override-json`), 2025 single-year, three variants:

1. **co-opt ON** — the run129 recipe as-is.
2. **co-opt OFF** (energy-only) — drop `--energy-reserve-coopt`; strips the
   reserve adder, leaving the pure energy (offer-curve) price.
3. **floor OFF** — monkeypatch `ercot_ordc_demand_steps(multistep_floor=False)`
   to test the OBDRR048 $20/$10 floor.

Demand-weighted system price, P1 pass, vs actual RTSPP
(`actual_lmp_hourly_ERCOT.parquet`).

## Result

| 2025 series | mean $ | p1 $ | hrs <$20 | hrs [20,26) | hrs >$200 |
|---|---|---|---|---|---|
| **co-opt ON (run129)** | **45.1** | 21.4 | 6 | 2455 | 71 |
| **energy-only (no co-opt)** | **33.8** | 21.4 | 6 | 2448 | 6 |
| floor OFF (co-opt) | 45.1 | 21.4 | 6 | 2455 | 71 |
| actual RTSPP | ~32.5 | — | ~2329 | — | 31 |

Three separable conclusions:

1. **The +$11 mean overshoot is the co-opt ORDC reserve adder, not the offer
   curve.** Energy-only 2025 (mean **33.8**) already lands on actual (**32.5**);
   the co-opt adder lifts every hour ~$11 to 45.1 and over-builds the tail
   (**71 vs 31** actual >$200 hours). This is the fixable, defensible LMP target.
2. **The $21 floor / "only 6 hrs <$20 vs 2329 actual" is the measured CC energy
   body, not the reserve adder** — it is *identical* with co-opt off (p1 21.4,
   6 hrs <$20 in both). The cheapest CC tranche (the cc_merit_ramp delta pulls
   CC_REGULAR `econ_low` to 0.72×, ~$18–20 at 2025 gas $3.52) sets it. Lowering
   it below the measured DAM curve would be a **calibration markup**, not a
   measured change — out of scope per the honesty gate.
3. **The OBDRR048 $20/$10 multi-step floor is ruled out** — at reserves ≤7000 MW
   the VOLL-anchored LOLP penalty is already **$25.68**, so `max(penalty, floor)`
   never raises a band. Disabling it changes nothing (floor-OFF ≡ co-opt-ON).
   (CT/ST offer heights were already ruled out by run130.)

## Why the co-opt adder over-fires in a comfortable year

The in-LP reserve-demand curve fires on the *model's* reserve tightness. The
co-opt reserve supply counts thermal headroom + **storage** (`reserve_storage=
True`) but **omits ERCOT's load-side Reserves** (Load Resources providing
RRS/ECRS). The measured AS-by-restype data
(`data/raw/ercot-AS/ercot_2025_as_by_restype_hourly.parquet`, `load` column)
shows **~877 MW mean (median 908, p90 1159, max ~2 GW)** of load-side AS the
model never credits — so the model's reserve clears lower on the ORDC curve than
reality, pricing a scarcity adder in non-scarce hours.

## Proposed run131 lever (measured, GATED) — load-resource reserve credit

Credit the measured hourly load-side AS MW into the co-opt reserve balance by
reducing the reserve-balance requirement RHS by `load_mw(t)` in
`ercot_reserve_coopt_inputs`. Because the ORDC steps are priced by absolute
reserve level, this makes the marginal step price at total reserve
`R_gen + load_mw` — physically exact, no λ/double-count.

**Market-design check (per the 2023↔2024/25 question).** All of 2023–2025 is one
regime — ORDC/RTORPA reserve adders (in force to 2025-12-04; RTC+B AS demand
curves go live 2025-12-05, after the backcast). Load Resources supplied RRS/ECRS
in **all three years** (the `load` column exists for 2023/24/25), so the credit
is physically correct regardless of regime. It is **self-targeting**: ~877 MW is
negligible against 2023's GW-scale August scarcity (the 2023 tail, ~151/88,
survives), but meaningfully relieves the comfortable 2024/25 hours where the
adder over-fires. The 2023 reliability-deployment scarcity (erroneous ECRS
conservatism) is a separate, regime-gated offset and is untouched.

**This is a GATED change** (it re-runs dispatch, hence volumes). Acceptance:
re-run 3yr and hold run129's volume gate (≥12/18, no ST_GAS crater / CT over-run),
keep the 2023 >$200/>$500 tail (~151/88), and pull 2024/2025 monthly-LMP MAE
*down* toward actual. Implementation + 3-year gate is the next step.

## Status

- Faithful run129 reproduction + this 2025 decomposition: **done** (single-year).
- Load-resource credit implementation + 3-year re-gate + dashboard registration:
  **pending** (the gated step).
