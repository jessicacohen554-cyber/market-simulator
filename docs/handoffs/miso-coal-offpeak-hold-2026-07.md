# MISO COAL_BIT off-peak-hold lane — diagnosis, mechanism selection, honesty targets

**Date:** 2026-07-13. **Lane:** miso-60 handoff sanctioned lane 1
("commitment-posture window rows"). **Status: DIAGNOSIS COMPLETE, mechanism
re-selected on fresh evidence, coal_sync throwaway A/B probe in flight.**
Companion to `docs/multi-iso/miso-scarcity-posture-design-2026-07.md` (the §A
pooled-U lever, REJECTED as miso-43) and the coal Thread-D docstrings
(`config/scenarios.py` `coal_sync_srmc_tranche` / `coal_mustrun_online_pmin`).

## The residual (recorded before any build, per the diagnosis discipline)

The dominant free-C1 MISO residual under the keeper `miso-60-stgas-vlr`:

- **COAL_BIT under-generates ~15.7 TWh in BOTH 2023 and 2024** (aggregate coal:
  model 165.8 vs actual 175.0 TWh 2023; 150.5 vs 167.1 2024). In 2025 coal
  *over*-generates (+16.9, high gas $3.52) — a **separate** South-gas/RDT
  problem (lane 3), not this lane's target and not to be worsened.
- **CT_PEAKER over-generates +11.2 TWh in 2024** — the displaced energy.
- **D-1 diurnal shape (the decisive signature):** COAL_BIT model off-peak CV
  **0.104 vs actual 0.041, cv_ratio 2.50** (2023). Reality holds coal **flat**
  through the overnight trough; the model **sags/cycles** it. The phenomenon is
  a committed-band **min-load HOLD**, i.e. coal price-following down in cheap
  hours where the real unit stays synchronized at min-load.

## Why the handoff's "min-run/min-down on U bridge" framing is superseded

Fresh CAMPD measurement (2023-2025 unit-level hourly `grossLoad`, MISO coal
fleet, `scripts/probes/…` throwaway analysis):

| stat | 2023 | 2024 | 2025 |
|---|---|---|---|
| coal on-fraction | 0.575 | 0.563 | 0.590 |
| RUN length median / mean (h) | 264 / 511 | 236 / 509 | 239 / 497 |
| OFF window p10 / median (h) | 6 / 94 | 5 / 94 | 4 / 76 |
| off-blocks <16h (unit-hours/yr) | 796 | 820 | 1149 |
| off-blocks <48h (unit-hours/yr) | 5731 | 4942 | 6300 |

Coal's **physical min-DOWN is short** (p10 off-window ~5 h — real coal *does*
cycle with short breaks), and the total bridgeable short-gap volume is ~0.2 TWh
(<16 h) to ~1 TWh (<48 h) — **an order of magnitude below the 15.7 TWh
deficit.** A min-down gap-bridge (the CAISO RA / ERCOT gas-CC pattern) cannot
supply the residual. The deficit is a min-load HOLD through long committed
runs, not gap-bridging — exactly the D-1 flat-vs-sag signature.

## Mechanism selection (rule 20 — one mechanism per phenomenon)

Enumerating what already touches coal online-status under miso-60 (P1-only,
`commitment=False`):

1. `coal_mustrun_per_plant` (on) — sizes a **Pmin=0** cheap bid band; not a floor.
2. `coal_warm_committed` (on) — a startup-**amortization** exemption (offer/price
   lever); not a floor.
3. `commitment_screen_coal` (on) — carries the 36 h/16 h coal min-run/min-down
   window, but is **INERT in P1-only mode** (`fleet.py:5317-5318`: "P1-only
   keepers never touch `min_run_hours`"; the screen only runs in the archived P2).
4. `coal_sync_srmc_tranche` (**OFF**) — the ONLY mechanism that turns the coal
   min-load band into a forced-on `min_gen` floor (`MECH_COAL_MUSTRUN`), sized
   to the measured online Pmin (`coal_mustrun_online_pmin`), split by the
   measured EIA-923 take-or-pay contract share into a fuel-free contracted band
   (`_mustrun`) + a spot remainder priced at full SRMC (`_sync`), both forced on
   and **online%-scaled** by the measured synchronization fraction (supercritical
   → all 8760 h; cycler → top-load hours only).

`coal_sync_srmc_tranche`'s own docstring names this exact residual — *"coal
HOLDS volume at min-load instead of price-following all the way down (the step-2
residual: 2024 coal under)."* It is the rule-20-correct owner of the phenomenon,
built and measured (online Pmin + contract share + online frac), forward-
reproducible — and **never tried for MISO** (the one recorded A/B is an ERCOT
throwaway rejected in an unrelated ORDC-tail context; the MISO posture work went
down the miso-43 pooled-U path instead). Rule 20/11 require reconciling with it
before building any parallel coal floor.

## Honesty targets (recorded ex-ante; score movement is a by-product)

Acceptance is **structural**, not lowest-MAE (rules 1/11):

- **Direction:** COAL_BIT 2023/2024 rises toward actual (closing the −15.7);
  CT_PEAKER-2024 falls toward actual (closing the +11.2); **2025 coal does NOT
  worsen** materially (the floor is online%-scaled to the measured window, which
  the model already exceeds in high-gas 2025, so it should rarely bind there).
- **Shape (the real test):** COAL_BIT D-1 `model_offpeak_cv` moves toward the
  measured 0.041 (cv_ratio 2.50 → toward 1). A level fix that does NOT flatten
  the off-peak is the wrong mechanism.
- **Forced-energy budget (C8):** coal is a major class (≥2% load), 30% cap. The
  forced `_mustrun`+`_sync` band is the measured online Pmin (~20-30% nameplate,
  online%-scaled) — expected well under 30% of coal energy; if above, it escalates
  to the grounded-above-budget pass on D-4 window (the synchronization window is
  the measured online frac) + D-1 shape.
- **NOT a target, never tuned toward:** the 2025 South-gas over-generation
  (lane 3) and any price-tail count (rules 1/13).

## Plan / status

1. **THROWAWAY 2024 A/B probe** (`scripts/probes/_miso_coalsync_probe.py`, rule
   16, never registered): miso-60 replay + `coal_sync_srmc_tranche` +
   `coal_mustrun_online_pmin` + `coal_takeorpay_from_data`. Compare COAL_BIT TWh
   and D-1 off-peak CV to the scored miso-60 2024 baseline. **← in flight.**
2. If directionally right (coal up, off-peak flattens, CT_PEAKER down, C8 sane):
   promote to a full **2023-2024-2025** keeper build (rule 16), zero-forcing twin
   (note: `MECH_COAL_MUSTRUN` is `MECH_ABLATION_KEPT` — the coal_sync forcing
   stays ARMED in the twin as structural take-or-pay must-run, like nuclear; the
   twin disarms only the merchant floors, e.g. st_gas via `MECH_ABLATION_FIELDS`.
   If the rubric wants the `_sync` spot band ablated as merchant, adjudicate that
   as a separate `MECH_ABLATION_FIELDS` change), DOF ledger, attestation,
   register, LOYO within 2023-2025 before promotion (rule 22).
3. If the load-rank/online-frac sync **window is wrong-shaped** (holds the wrong
   hours), refine the window with the CAMPD run-length/off-window measurement
   (the lane's rule-23 deliverable — a `derive_campd_coal_run_lengths.py`
   analogue of the CT script), then re-solve.

## Refutations / settled
- min-DOWN gap-bridge (CAISO/ERCOT pattern) on coal: REFUTED for this deficit —
  measured physical min-down is short, bridgeable volume ~1 TWh ≪ 15.7 TWh.
- miso-43 pooled-U posture lever: REJECTED (honesty gate, 3.7-4.2× cleared reserve).
- 2025 coal over-generation is NOT this lane's target (lane 3); do not worsen it.
