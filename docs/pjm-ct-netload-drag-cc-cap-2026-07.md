# PJM CT_PEAKER net-load deployment drag + CC demonstrated-peak cap (2026-07)

**Question (pjm-75).** The pjm-74 keeper's C1 residual is a 2024-concentrated
CC-over / CT-under imbalance (2024 CC_REGULAR +16.57 TWh / +1.7pp over,
CT_PEAKER −8.76 TWh / −1.1pp under). The P2 commitment screen is off the table
(user decision) and the offer-multiplier axis is exhausted — run-74 proved
multiplier moves shift all three years uniformly (CC −4.4 TWh in each) and
cannot close a year-concentrated gap. What measured, forward-native levers
remain?

**Answer.** Two, both admissible under CLAUDE.md #12/#13 (reproducible
physical/market inputs that regenerate for a forward year and respond to
changed conditions), wired in `scripts/archive/run_pjm75_ct_drag_cc_cap.py`:

## 1. CT_PEAKER net-load deployment drag (`ct_netload_drag`)

The same mechanism validated as the ERCOT keeper
(`docs/ercot-ct-netload-drag-2026-06.md`, 2026-07-01-24-ct-drag-v1) and the
CAISO keeper default (`scripts/data/derive_caiso_ct_reliability_floor.py`): a
per-hour min-gen floor `clip(slope·netload_GW + intercept, 0, cap) ×
capacity` on the non-`_peak` CT_PEAKER tranches, gated to the
afternoon-evening ramp window h[15,22) local standard, over which the LP
dispatches economically. It stands in for the AS/RUC deployment energy the
merit order can't see — PJM's real CT fleet runs reserve-deployment /
supplemental-commitment energy at ~top-of-merit offers the hourly LP never
clears.

### The measured signature (`scripts/data/derive_pjm_ct_netload_drag.py`)

CAMPD hourly net for the model fleet's **pure-play** CT_PEAKER plants
(110 of 121 plants, 23.48 of 25.58 GW; mixed ORIS sites are excluded because
CAMPD's PJM extracts are plant-summed, so a co-located CC/coal unit would
contaminate the CT series) against PJM system net-load = EIA-930 `PJM` Demand
− wind − solar, shifted UTC→EST (−5 h, no DST) onto the model's 8760 clock.
CAMPD gross is netted by the simple-cycle parasitic factor (0.99) so the
regression target is on the same net basis as the model dispatch and the
EIA-923 C1 benchmark.

* Measured pure-play CT: 18.03 / 19.09 / 22.28 TWh (2023/24/25), CF
  0.088/0.093/0.108 — rising year over year with net-load.
* The ramp window is PJM's high-CF block (overnight CF ~0.015 at any
  net-load; ramp-window CF rises to 0.43–0.59 at 135 GW), and the
  relationship is monotonic and year-stable: ramp-window Spearman ρ =
  0.50 / 0.51 / 0.60.
* **Two-regime shape** (the PJM-specific finding): the binned ramp-window CF
  is flat ~0.07–0.09 below ~90–100 GW (routine economic peaking the merit
  order already prices) and then rises linearly to ~0.58 at 139 GW (the
  reliability-deployment regime). ERCOT/CAISO's curves are linear over their
  whole observed range, so their recipe — an unclipped least-squares line
  through all bins — IS the clipped line there. Applied blindly to PJM it
  misfits both regimes (over-floors 85–105 GW by ~2×, under-floors the top).

### Fit

The applied mechanism is `clip(slope·netGW + intercept, 0, cap)` — a hinge —
so the fit is that exact functional form: grid-search the hinge knee over the
2-GW bin centers, least-squares line on the bins at/above the knee, keep the
knee minimizing SSE of the **clipped** prediction over all bins (SSE 0.133 vs
0.176 for the unclipped line). No scipy.optimize (forbidden); the knee grid
is exact.

```
floor_frac = clip(0.01108 · netload_GW − 0.9987, 0, 0.46)   (zero below ~90.1 GW)
           applied for hour-of-day in [15, 22), else 0
```

Passed via `ct_drag_overrides` in the driver (PJM-specific coefficients — do
NOT reuse ERCOT's 0.00703/−0.1427/0.47 or CAISO's 0.00901/−0.1124/0.36).

* Floor energy 4.70 / 6.29 / 7.16 TWh (2023/24/25) — **not year-uniform**
  (rises with the tighter 2024/2025 net-load), exactly the property the
  offer axis lacked.
* Floored-total vs measured: 18.78 vs 18.03 / 20.40 vs 19.09 / 23.29 vs
  22.28 (+4/+7/+5%; the ERCOT keeper's same check ran +6–8%).

### Why not the alternatives

* `ct_deployment_overlay` / `ct_mustrun_per_plant` pin measured CEMS
  deployment energy / observed monthly generation — backcast-only artifacts
  with no forward analogue (CLAUDE.md #12 forbids them in a keeper). The
  net-load drag derives the same commitment from a forward-available driver.
* Offer retuning cannot produce a year-concentrated effect (run-74).

## 2. CC demonstrated-peak cap (`cc_capacity_reconcile`, mode="cap")

`docs/handoffs/pjm-cc-overgen-recommendation-2026-06.md` Rank 4, targeting
Miss #2 (the 95–100% CF pile): CC plants whose **model** nameplate exceeds
anything they ever sustained in the CEMS record over-run the top CF bands on
phantom capacity. `scripts/data/derive_cc_capacity_reconcile.py --iso PJM --mode
cap` bounds each pure-play CC_REGULAR plant's LP capacity at its demonstrated
CAMPD peak (p99.9 of net MW pooled 2023–2025, robust to single-hour
glitches), applied only where the model capacity exceeds the peak by >1.1×
(an economically idle top band is never mistaken for missing capability).
Rows carry `mode=cap`; `fleet._reconcile_cc_capacity` applies `min()` for cap
rows and `max()` for raise rows, and `fleet_to_bins` gains the same reconcile
hook `load_campd_bins` gives ERCOT (whose raise-only table has no `mode`
column and is byte-identical).

* 17 plants capped, −2,686 MW of phantom top-band capacity.
* EIA-860 winter ratings independently corroborate most caps (Key 774 vs
  winter 778, Camden 139 vs 145, Ontelaunee 590 vs 591, Sayreville 324 vs
  333) — the nameplate, not the CEMS record, is the outlier.
* **Cross-source feasibility guard:** a candidate is dropped when its
  EIA-923 annual net generation is infeasible at the CAMPD peak (implied CF
  > 0.90) — evidence the CEMS series understates the plant (units missing
  from the extract), so the "demonstrated peak" would be a telemetry
  artifact. Dropped: Hunterstown (implied CF 1.17), Ironwood (1.06),
  Allegheny 3-4-5 (1.27). This is the CLAUDE.md #13 misalignment exception,
  documented per rule.

Admissibility (rule #12): the cap is a capability/availability quantity —
measured sustained deliverability, the opposite-direction twin of the ERCOT
raise-only reconcile — not generation pinning. It regenerates from rolling
CEMS history for any fleet and binds hardest in high-CF hours, so its effect
is year-differentiated, unlike an offer multiplier.

## Deliberately not included

* `cc_peaking_per_plant`: PJM already defaults `cc_duct_peaking=True`
  (measured per-plant EIA-860 duct-burner shares supersede the class-wide
  8.0% estimate for every mapped plant), and the duct map takes precedence
  over the thermal-tranche artifact in `bins_to_fleet` — enabling it would
  touch only unmapped plants.
* Scarcity adders / ORDC overlays / tail decompression: blocked on the
  per-gen reserve thread (`docs/multi-iso/pjm-reserve-ordc.md` Phases 1–2).

Reproduce: `python scripts/data/derive_pjm_ct_netload_drag.py` and
`python scripts/data/derive_cc_capacity_reconcile.py --iso PJM --mode cap`.
Results: run `pjm 75 ct-drag cc-cap` on the backcast dashboard.
