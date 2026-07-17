# NEISO forecast-prep prompts (2026-06-19 handoff)

> **⚠️ STALE (2026-07-17) — do not execute.** Overtaken by events: the NEISO forecast
> infeasibility was separately fixed (`docs/forecast-invariant-findings.md` F0) and
> NEISO has since completed 25/25 forecast years (full-horizon P-3A). Forecast
> planning now lives in `docs/forecast-development-plan-2026-07.md`.

Two self-contained prompts for fresh sessions, written off the backcast
sign-off in `results/calibration/DIAGNOSIS-neiso-ccsteam-2026-06-19.md`. NEISO is
**backcast-calibrated**; these are the only two items between it and a forecast
run. **F1 is mandatory** (a forecast has no measured interchange schedule to
serve); **F2 is polish** and is blocked on the U4 daily-AGT upload.

Both assume the standard discipline: read `claude.md` first; branch
`claude/neiso-<pack>-<slug>`; run the full test suite; **no magic numbers** (every
value from `ScenarioConfig`/`constants.py` with a citation in
`docs/parameter-citations.md`); **ERCOT/PJM/CAISO/NYISO regression guard** — their
calibration outputs stay byte-identical; log the pass in `docs/calibration-log.md`.
The keeper to compare against is `results/calibration/neiso_ccsteam_keeper_3yr`.

---

## F1 — Neighbor-convexity priced-import node (REQUIRED for forecast)

```
NEISO forecast prep: make the import/export seam price-responsive so NEISO can
run without a measured net-interchange schedule. Read
docs/reference-price-interface.md (the whole note — the PJM build/validation and
the step-2/step-3 over-export finding), src/market_sim/data/neighbor_price.py,
the INTERFACE_NEIGHBORS registry in config/constants.py,
model/transmission.py::build_import_generators / build_export_sinks
(constants.IMPORT_TRANCHES / EXPORT_TRANCHES), scripts/validate_neighbor_price.py,
scripts/derive_import_tranches.py, and docs/sessions/multi-iso/08-neiso-prompt-pack.md §3.4 (archived)
+ P9. Today NEISO's backcast serves the measured EIA-930 ISNE net interchange as
a fixed schedule (exact by construction); a forecast has no schedule, so the seam
must respond to NEISO's own price.

Context that is already in the repo: _neiso_config() already carries the
HQ_import zone (load_share 0) and the North/Boston/CT import links; the J1
priced-node machinery (build_import_generators/build_export_sinks) exists and is
exercised for PJM; --priced-interchange is gated to ISOs in INTERFACE_NEIGHBORS
(PJM only today). NEISO is a STEADY NET IMPORTER (~1.0-1.7 GW; EIA-930 ISNE net
interchange -8.13/-10.30/-15.14 TWh for 2025/24/23), dominated by HQ hydro.

1. Add NEISO to INTERFACE_NEIGHBORS with two seams, each anchored to the
   NEIGHBOR's own price formation (rule #11 — NEVER to NEISO's net-MWh flow):
   - HQ (HQ_import): cheap hydro baseload, NOT a gas heat rate. Anchor to an HQ
     export/hydro-marginal price proxy (a low, weakly load-shaped level); cite
     the proxy. This is the bulk of NEISO imports and is largely price-insensitive
     downward — model it as a near-must-import block up to the HVDC limit.
   - NYISO ties (Cross-Sound / Northport-Norwalk into Connecticut, and Highgate
     VT-HQ): anchor to NYISO's realized LBMP via neighbor_price = (HH + NY gas
     basis) x marginal_HR x load_shape(NY load), with the supply-curve convexity
     load_shape_exponent > 1 and the per-region HR anchored so the reference price
     reproduces NYISO's OWN annual LMP (mirror the PJM MISO/NYISO HR anchoring).
     Use the EIA-930 NYIS load extract already present for the seam.
2. Real interface limits (the PJM step-3 lesson — the unconstrained LP over-traded
   2.2-3.0x): cap each seam at its physical TTC — HQ Phase II HVDC ~2000 MW into
   NEMA/Boston, Highgate ~225 MW, Cross-Sound ~330 MW, Northport-Norwalk. Cite
   the RSP/operating-limit sources; seed Tier-3 where unposted (upload U6 refines).
3. Validate WITHOUT telling the model the target (this is the whole point):
   run scripts/validate_neighbor_price.py for NEISO 2023-2025 and confirm the
   priced node reproduces the measured EIA-930 net-import duration curve within
   ~+/-15% and the steady-importer sign, on the neighbors' own prices alone. NEISO
   is a net importer, so the failure analogue is OVER-import (the mirror of PJM's
   over-export) — diagnose with the interface caps + any structural must-import
   floor (HQ firm hydro), never by detuning the neighbor price.
4. Backcast guard: run the keeper command (the F-handoff command in the diagnosis
   doc) with --priced-interchange and confirm it does NOT regress the calibrated
   fuel mix / price level vs neiso_ccsteam_keeper_3yr (the measured-schedule run);
   the priced node should land on the measured interchange, not move it. Then the
   forecast path (no schedule) inherits the same seam.

Acceptance: NEISO in INTERFACE_NEIGHBORS with cited HQ + NYISO anchors and real
interface limits; validate_neighbor_price reproduces measured net import within
~+/-15% on neighbor prices alone; --priced-interchange backcast is calibration-
neutral vs the keeper; ERCOT/PJM/CAISO/NYISO byte-identical; parameter-citations +
calibration-log updated.
```

---

## F2 — Derived daily-AGT winter-oil convexity (polish; blocked on upload U4)

```
NEISO forecast prep: replace the FITTED daily-AGT convexity magic number with a
value DERIVED from measured daily Algonquin Citygate spot, so winter oil and the
>$200 price tail are forecast-grade. PREREQ: upload U4 (daily/monthly AGT spot
2023-2025) must have landed in data/raw/ — if it has not, STOP and file U4 as the
blocker; do not proceed on the fitted shape. Read docs/multi-iso/neiso-data-audit.md
§2c-2d, src/market_sim/data/fuel.py (iso_hub_daily_gas_prices,
AGT_DAILY_BASIS_CONVEXITY in constants.py), the --gas-hub-basis-daily /
dual_fuel_oil_reattribution path in run_calibration_full.py, and the rejected
probes neiso 18 (oil-agtdaily, overshot oil to 2.12 vs 1.24) and neiso 21 (keeper,
which rejected the fitted convexity).

The current state: AGT_DAILY_BASIS_CONVEXITY = 7.0 is FITTED to the backcast
(chosen to reproduce the measured oil/>$200 counts) — a magic number, off in the
keeper. The keeper prices winter gas on the measured MONTHLY AGT basis, which
never reaches distillate parity, so modeled winter oil is ~0 (vs EIA-930 NG:OIL
0.32/0.37/1.24) — the accepted monthly-granularity limit.

1. Build the measured daily AGT basis from U4 (daily citygate spot minus daily
   Henry Hub), per winter month, into the gas path — replacing the reconstructed
   demand^convexity shape with the real series. iso_hub_daily_gas_prices should
   consume the measured daily basis directly when present.
2. If a parametric convexity is still wanted for forecast years (no future daily
   spot), DERIVE the exponent from the observed 2023-2025 relationship: regress
   measured daily AGT basis on daily NEISO demand (or HDD) and report the fitted
   exponent + R^2; that derived value — cited to the regression, NOT tuned to the
   oil/>$200 counts — is what may be promoted into constants.py. Document the
   derivation so it is reproducible.
3. Validate: with the measured daily basis, modeled winter oil should reach the
   ORDER of EIA-930 NG:OIL without being fit to it (neiso 18 overshot to 2.12 vs
   1.24 on the fitted shape — the derived series should not), and the 2025 winter
   >$200 hour count should move toward the actual (~160) from the monthly
   plateau's 13. Re-check the Jan-2025 level (the keeper runs ~$18 hot there).
4. Promote to the keeper ONLY if the convexity is derived and the oil/price-tail
   match is a consequence, not a target. Re-run the keeper command (3yr) and
   register the new bundle; if it does not cleanly beat neiso_ccsteam_keeper_3yr,
   keep the monthly overlay and file U4-derived daily as a documented option.

Acceptance: winter gas priced on measured daily AGT (U4); any forecast convexity
DERIVED from the observed basis-vs-demand regression with citation (no fitted
constant); modeled winter oil within an order of magnitude of EIA-930 without
being fit to it; keeper updated only on a derived, not tuned, result;
ERCOT/PJM/CAISO/NYISO byte-identical; calibration-log + parameter-citations updated.
```

---

**Sequencing.** F1 and F2 are independent and can run in parallel sessions. F1
gates the forecast and needs no upload — do it first. F2 is blocked on U4 and is
polish (LMP-neutral for the backcast); schedule it when the daily-AGT spot lands.
After F1, a NEISO forecast smoke run (no measured schedule) is the next milestone.
