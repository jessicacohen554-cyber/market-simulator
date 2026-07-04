# Forecast-layer diagnostics: sensitivity tornado + MIP UC cross-benchmark

*2026-07-04. Index + synthesis for two containment diagnostics built this
session: PP-3.1 (sensitivity tornado) and PP-3.4 (MIP unit-commitment
cross-benchmark). Both are **measurement, not tuning** — no calibrated value,
keeper, or production code path was changed.*

## What was built

| Diagnostic | Script | Tests | Report(s) |
|---|---|---|---|
| Sensitivity tornado (PP-3.1) | `scripts/run_sensitivity_tornado.py` | `tests/test_sensitivity_tornado.py` | `sensitivity-tornado-ercot-2026-07-04.md` (+`.json`) |
| MIP UC cross-benchmark (PP-3.4) | `scripts/diag_uc_mip_crossbench.py` | — (one-time diagnostic) | `mip-uc-crossbench-ercot-2026-gas_cc-mlf{100,050}-2026-07-04.md` (+`.json`) |

Both scripts reuse the production builders read-only. The tornado only perturbs
`ScenarioConfig` fields (no off-registry channel, rule 24) and solves years
sequentially at ≤2 concurrent processes (rule 12). The MIP script is **strictly
diagnostic** — production stays pure LP (CLAUDE.md stack rule); nothing in
`src/` imports it, and it introduces integrality only in its own throwaway
Highs model built from the captured LP.

---

## 1. Sensitivity tornado (PP-3.1)

**Design.** One-at-a-time ± band runs of the ~15 highest-leverage
emissions-trajectory knobs (gas price, load growth, carbon path, coal/gas FOM
bars + multiplier, reliability floor, consecutive-loss years, renewable
buildout/CF, storage deployment, battery adder, VOLL) on one small ISO over a
short forecast horizon. Each band is a `ScenarioConfig` override whose
`cache_key` captures the perturbation; the driver reads annual CO₂ (Mt),
load-weighted-ish average price, and cumulative thermal retirements back out of
the per-year cache bundles, then ranks parameters by the |high − low| swing in
each metric. Feeds the **DOF ledger** (rule 21): the forecast-category knobs
with the largest CO₂ leverage are the free parameters most in need of an
identification source in each keeper attestation.

**Run.** ERCOT, 2026–2028, legacy equal-width fleet (`use_campd_bins=False`, for
runtime; the leverage *ranking* is robust to fleet granularity), 2 workers.

**Reproduce.**
```
python scripts/run_sensitivity_tornado.py --iso ERCOT \
    --start-year 2026 --end-year 2028 --workers 2 --out docs/handoffs
```

### Results (ERCOT 2026–2028, 31 forward solves, ~56 min wall)

Base case: 173.9 Mt CO₂ (2028), 494.1 Mt horizon total, $23.09/MWh, 0 GW
retired. Full ranked tables in `sensitivity-tornado-ercot-2026-07-04.md`.

**CO₂ final-year leverage (|high − low|):**

| Rank | Parameter | Cat. | Swing (Mt) | Low → High |
|---:|---|---|---:|---|
| 1 | Demand growth path | forecast | **56.1** | 154.4 → 210.5 |
| 2 | Henry Hub gas price level | forecast | 10.5 | 166.7 → 177.3 |
| 3 | Carbon price path | forecast | 9.7 | 173.9 → 164.2 |
| 4 | Renewable CF scalar | dispatch | 9.4 | 179.0 → 169.6 |
| 5 | Battery dispatch adder | dispatch | 0.7 | 173.9 → 174.6 |
| 6 | Storage deployment pace | forecast | 0.3 | 174.1 → 173.8 |
| 7–15 | all retirement-screen knobs¹ | forecast | **0.0** | — |

¹ coal FOM multiplier, reliability floor, coal/gas-CC/gas-CT FOM bars, gas-CC &
coal consecutive-loss years, renewable buildout pace, VOLL.

Price leverage ranks gas ($5.7) > carbon ($3.5) > demand ($1.7); the retirement
knobs move price $0 too.

### The finding

Two clean results feed the DOF ledger:

1. **Demand growth is the dominant emissions DOF** by ~5×, then a tight cluster
   of gas / carbon / renewable-CF (~10 Mt each). These four are where a keeper's
   emissions band is actually made or lost — they need the strongest
   identification sources in the attestation (rule 21). Notably the emissions
   band is set by **input drivers**, not by the calibrated retirement/FOM knobs.

2. **Every retirement-screen knob has *zero* near-term leverage, and 0 GW
   retires in any variant** (including ±band coal FOM, reliability floor, FOM
   bars, consecutive-loss years). Over a 3-year ERCOT horizon with ~5 %/yr load
   growth, no economic thermal retirement fires — so the whole retirement-DOF
   block is inert here. This corroborates **CX-2** (one-pass myopia: the fleet
   lags the load ramp and incumbent fossil fills the gap) and the audit's
   "retirements are floor- not economics-driven" note. Their leverage is a
   longer-horizon phenomenon; a tornado run out to ~2035 is required to exercise
   them (much longer runtime — the retirement DOFs cannot be gated on this
   near-term window alone).

**Reproduce/extend.** Re-run with `--end-year 2035` (and optionally
`--campd-bins`) to surface retirement-DOF leverage once the horizon is long
enough for economic exits to fire.

---

## 2. MIP unit-commitment cross-benchmark (PP-3.4)

**Design.** Take the exact production LP for one ISO-month, add true integer
commitment (binary on/off `u`, min-load block, min-up/min-down, explicit startup
cost) on the CAMPD *committed* tranches, and solve as a MIP. Three solutions are
compared on the committed tranches and system CO₂:

- **P1-LP** — production forecast/scored path as-is (`pmin=0` on every tranche,
  DP-1 → min-load is emergent).
- **LP-relax** — the UC model with `u/su/sd` relaxed to `[0,1]`.
- **MIP-UC** — the same model with `u` integer.

`MIP-UC − LP-relax` is the **pure integrality bias** (identical objective and
constraints); `MIP-UC − P1-LP` also folds in the base-cost-vs-amortized-bid
difference and the added min-load structure — the "vs what production ships"
view.

**Run.** ERCOT 2026, first 744 h (January), gas_cc committed tranches (40 units,
29,760 binaries), solved to optimality (gap < 1e-6) in ~1–3 min. Two min-load
fractions: 1.0 (committed tranche = full sync block) and 0.5 (partial min-stable
load).

**Reproduce.**
```
python scripts/diag_uc_mip_crossbench.py --iso ERCOT --year 2026 \
    --hours 744 --fuel gas_cc --min-load-frac 1.0 --time-limit 300 --out docs/handoffs
```

### Results (one month, gas_cc committed tranches)

| Min-load frac | Solution | Committed energy (MWh) | Committed starts | System CO₂ (t) |
|---:|---|---:|---:|---:|
| 1.0 | P1-LP | 2,960,907 | 664 | 17,399,055 |
| 1.0 | LP-relax | 3,984,130 | 85 | 17,386,510 |
| 1.0 | **MIP-UC** | 3,977,021 | 85 | 17,389,768 |
| 0.5 | P1-LP | 2,960,907 | 664 | 17,399,055 |
| 0.5 | LP-relax | 3,924,302 | 66 | 17,387,308 |
| 0.5 | **MIP-UC** | 3,924,019 | 66 | 17,387,318 |

**Integrality bias (MIP − LP-relax):** negligible at both fractions —
≤ 7,109 MWh (< 0.2 % of committed energy), **0** extra/fewer starts, +3.3 kt /
+0.01 kt CO₂. The UC LP relaxation is essentially integral here.

**vs production P1 (MIP − P1):** large and consistent —
**+1.02 TWh / +0.96 TWh** committed CC energy (≈ +34 %), **−579 / −598 starts**
(664 → ~85, a ~90 % cut), **−9.3 kt / −11.7 kt** system CO₂.

### The finding

The LP-relaxation *commitment* bias this diagnostic was built to quantify is
**near zero**: within the tranche offer-curve structure, the LP relaxation of a
properly UC-constrained model already lands at an integer commitment. The large
gap is **entirely between "commitment-constrained" and "production P1"**, and it
is driven by the *absence of any min-load constraint* in P1 (`pmin=0`, **DP-1**),
not by integer relaxation:

- **Committed CC energy is under-booked ~34 %** by P1 — it ramps committed
  tranches continuously from 0 instead of holding them at a min-load block once
  synced. That ~1 TWh/month of sustained CC output displaces marginal units and
  is why enforcing min-load *lowers* system CO₂ ~9–12 kt/month here.
- **Starts are over-booked ~7×** by P1 (664 vs ~85) — the LP cycles committed
  tranches on/off for free because nothing prices min-up/min-down. This is the
  cycling the P2 heuristic screen exists to tame, and it under-books the startup
  fuel/CO₂ that **EM-5** flags as unmodeled.

**Implication.** Reducing LP-dispatch commitment bias is about **adding a
min-load floor** to the scored P1 path (the DP-1 remediation), not about
switching to a MIP — the relaxation gap is not where the error lives. A pure-LP
min-load mechanism (a `min_gen` floor on the committed tranche, gated per rule 14
with a driver + window + forward story) would capture ~all of the measured bias
while keeping the stack pure-LP.

### Caveats

- Integer set restricted to gas_cc for tractability; widen `--fuel`/`--hours`
  when runtime allows. One month is a commitment snapshot, not an annual bias.
- `min_load_frac=1.0` treats the committed tranche as a full sync block (the
  strongest min-load); the 0.5 run confirms the finding is insensitive to it.
- Both diagnostics are self-contained; the MIP never enters production.
