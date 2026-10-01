# ADDENDUM to PRECOMMIT-caiso260 — phase 0 measured, screen year fixed, C4-2025 direction recorded. **Pushed before the screen is launched.**

**Session caiso-260, 2026-09-06.** Keeper `2026-09-06-caiso-257-b1-ctonly`
UNCHANGED. Artifacts: `results/calibration/_caiso260_demand_vintage_phase0.json`
(probe `scripts/probes/_caiso260_demand_vintage_phase0.py`, the artifact
RESTORED to committed bytes on exit) and
`results/calibration/_caiso260_gdrift_at_solve.json`
(`_caiso255_gdrift_identity.py --keeper-sha c78f6d94`, re-pointed at the
caiso-257 bundle since the caiso-252 one is pruned).

## §1 — G-REPRO: PASS on all three legs

| leg | registered | measured |
|---|---|---|
| R-1 | derive's own guards pass unchanged | PASS (anchors 62.21 / 54.59 / 44.43; annual 207.47 / 212.16 / 204.84 TWh inside `_ANNUAL_GUARD`) |
| R-2 | max \|Δ\| 1,452 / 863 / 583 MW; annual +69 / −33 / −753 GWh | **1,451.7 / 862.8 / 583.3 MW; +69.4 / −33.0 / −752.7 GWh** |
| R-3 | only `cems_gas_grid_mw` moved; Δflat constant | PASS — netgen / ng_cell / ti byte-identical; **Δflat = −204.9 / −136.2 / −136.2 MW** (the cogen block 8.399 → 6.604 TWh in 2023: 1.8 TWh moved from a flat term into the hourly CEMS term) |

## §2 — Phase 0

**Plant attribution (P-3).** Least squares of Δcems on the two plants named
ex ante: 2024 coef **1.000 / 1.000, R² 0.999998**; 2025 **1.000 / 1.000,
R² 0.99997**; 2023 **1.279 / 1.047, R² 0.932**. So in 2024–25 the delta IS
El Segundo (57901) + Desert Star (55077), to the MW. In 2023 the same two
carry 100 % of the gross magnitude but 6.8 % of the variance is a further
term (top single-plant correlations after 55077 and 57901: Redondo Beach
356, Malburg 56041, La Paloma 55151 at 0.52–0.57 — plant-map differences in
the 2023 bench between vintages). **P-3 holds in 2024/2025 and holds
marginally in 2023** (the un-named residual is 6.8 % of variance, under the
registered 10 %).

**Shape.** Δdemand by block (mean MW):

| year | night 0–5 | belly 10–15 | evening 17–21 | **hod 22–23** | annual |
|---|--:|--:|--:|--:|--:|
| 2023 | +30 | −83 | +127 | **+86** | +69 GWh |
| 2024 | +17 | −65 | +56 | **+60** | −33 GWh |
| 2025 | −69 | −106 | −77 | **−64** | −753 GWh |

2023/24: demand moves *from* the belly *to* the evening and night (the two
plants' hourly profile replacing a flat block). 2025: down in every hour
(Desert Star's 2025 series is small, 0.39 TWh, so the flat block it replaces
dominates). **P-4 (Δ at 22–23 in 2025 negative) HOLDS: −64 MW.**

**C4-2025 direction (§0.3).** `S = Σ e_t Δd_t` = **−5.8e6 / −1.15e8 /
−8.9e7 MW²h** (2023/24/25) — negative in every year, expected direction
**better**; the first-order bound on |ΔMSE| is **1.40 / 1.75 / 1.22 %** of
the keeper's MSE, i.e. at most ±0.002 on the 2025 NRMSE of 0.300. **P-5
HOLDS.** The bound is a bound: the solve decides, and C4 stays excluded.

**Footprint and screen year (§2 item 4).** `F(y) = Σ|Δd|`: **2023 1,976
GWh, 2024 1,310, 2025 1,093.** The gross rule names **2023**. **P-2 is
FALSIFIED** — the handoff expected 2025 on the net −753 GWh; the gross swings
of the shape change are largest in 2023. The rule was fixed before F was
computed and it governs: **the screen year is 2023.** (Recorded against
interest: 2023 is also the year with the smallest expected C4 movement.)

**G-DRIFT (§2 item 6), by measurement.** `c78f6d94 → HEAD`: **ALL LP INPUTS
BIT-IDENTICAL** in all three years (with the artifact committed). Instruments
1–2 flag 3 changed constants (`CAMPD_BINNING_ISOS`, `EIA930_PS_FOLDED_INTO_WAT`,
`RGGI_MEMBER_STATES_BY_YEAR`) and 1 added (`RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO`),
each settled empirically by the bit-identity of every array. **G-CTRL form 4
holds; no control solve.** The demand matrix difference — the arm — is the
R-2 table above, and it is the only live input hunk.

## §3 — Predictions scored so far

P-1 HOLDS · **P-2 FALSIFIED** (screen year 2023, not 2025) · P-3 HOLDS
(2024/25 exact; 2023 marginal) · P-4 HOLDS · P-5 HOLDS · P-6/P-7/P-8 await the
screen and the full span.

## §4 — What is launched next

The regenerated artifact is written to disk (`--keep`), then ONE year:

```
MARKET_SIM_P1_BASIS_SEED=0 PYTHONPATH=.:src uv run python scripts/replay_keeper.py \
    results/calibration/caiso257_ctonly \
    --out-dir results/calibration/caiso260_screen2023 --years 2023 \
    --note "caiso-260 rule-29 SCREEN of the demand-artifact vintage re-derive: keeper replay with the re-derived supply-consistent demand on disk; throwaway, deleted before merge"
```

scored by `scripts/probes/_caiso260_screen.py` on the PRECOMMIT §3 gates.
Every other gate, the exclusions and the stop rule are unchanged.
