# Endogenous WECC import node — design/handoff (caiso-110)

**Owner-granted 2026-07-21 (caiso-109 P1-A redirect): "Build the endogenous WECC
node."** This doc is the blueprint for the multi-session structural build. It is
the disciplined first increment (design + data foundation); the LP wiring +
3-year A/B run in caiso-110+. Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED.

## 1. Why this exists — the two prior kills

The CAISO keeper's load-bearing fail is C5a (CO2), driven by a ~8 TWh/yr
belly/daytime **over-import that displaces gas ~1:1** (P0,
`FINDING-caiso109-gas-underdispatch-economic`). Two attempts to fix it by
setting the belly clean-import **depth** as a function of an observable have both
been killed by derive-first measurement:

- caiso-107: CA **price** observables (net-load, PaloVerde/Malin hub level,
  hub−CA basis) — all fail year-stability (CV 0.33–1.62).
- caiso-109 P1-A: **west-wide surplus QUANTITY** (WECC-West solar /
  solar-penetration / net-gen surplus) — all fail too (CV/LOYO), with a monotone
  CA-side year-drift (+560 MW/yr at every fixed west-surplus level;
  `FINDING-caiso109-westwide-surplus-derive`).

**The lesson that sets the design:** the belly transfer is **endogenous to the
co-evolving CA + West fleets** (CA solar +1.5 GW/yr, storage ~2×; West solar
growing too). No *conditioned static depth tranche* — the current caiso-87/93/94
construction — can be forward-stable, because a fixed capability priced at a hub
cannot express "how much the West can export depends on both sides' hourly
balance." The fix is to make the flow **clear on prices/quantities from both
sides**, i.e. give the neighbor a real supply curve that the LP co-optimizes,
not a number the LP clears below.

## 2. What exists today (the head start)

`config/iso_configs.py::_caiso_config` already carries the neighbor as a node:

- `Zone(name="WECC_import", iso="CAISO", load_share=0.0)` — a node, no load.
- Ties: `WECC_import→NP15` (Path 66/COI, 4800 MW), `WECC_import→SP15_rest`
  (Path 46/WOR, 10623 MW); interface limit `WECC_import_simultaneous` (~7500 MW,
  or the measured MIC under `capacity_deliverability_limits`).

Today the node is fed by **import tranches** attached as pseudo-generators
(`transmission.build_caiso_per_hub_intertie` + the firm blocks + caiso-87/93/94
clean depth), each a fixed capability at a static/hub price. Every other ISO's
neighbor (NEISO HQ, NYISO ties) is the same import-node-with-tranches pattern —
**a neighbor with a real fleet is new architecture.**

## 3. Design — two options, phased

> **UPDATE 2026-07-21 (from the data foundation, §4).** The reduced Option B's
> clean rung as first drafted — `max(0, West_renewables − West_demand)` — is
> **degenerate**: the WECC-West aggregate is a large net-load region (solar
> 6.8/9.5/11.8 GW belly vs demand ~54–57 GW), so renewables never exceed demand
> and the "surplus over demand" is ~0 in every hour. The West still *net-exports*
> ~+2.2 GW on average — its cheap marginal hydro/solar undercuts CAISO — but that
> export is a **price/congestion outcome**, not a renewable-surplus threshold.
> This is the same lesson as the two kills, one level deeper: **no measured West
> *quantity* used as a conditioned availability will work; the export must clear
> on the West's endogenous price.** ⇒ **Build Option A (full co-optimized zone)
> directly; Option B is retained below only as the rejected-degenerate record.**
> The data foundation (West demand + solar/wind/hydro available + thermal
> capacity) is exactly Option A's input and is delivered this session.

### Option B (REDUCED endogenous supply curve) — build FIRST

Replace the caiso-87/93/94 clean-depth tranches at `WECC_import` with an
**endogenous export supply curve** derived from the West's own measured hourly
balance:

1. **Clean surplus rung** — the West's measured net renewable surplus
   `S_clean[t] = max(0, West_solar[t] + West_wind[t] + West_hydro[t] −
   West_demand[t])` (EIA-930 BALANCE Region NW+SW), offered at ~$0 + ε (clean,
   EF 0). This is the physically-available clean export in hour t; it co-evolves
   forward (as West solar grows, S_clean grows) and it is bounded by the West's
   own load — the flat 5 GW capability's missing physics.
2. **Dispatchable thermal rung(s)** — the West's remaining gas/coal capability
   above its own net position, priced at the West's marginal cost
   (`HR × gas_hub + carbon` for the carbon-priced share; AZ/NV uncarbonized per
   caiso-87). One or two rungs (CCGT, CT/scarcity).
3. The LP clears CAISO imports against this curve up to the tie TTC. Crucially
   the **quantity that flows is endogenous**: in the belly, if CAISO's own price
   is ~$0 (CA-flush) the clean rung only flows to the extent CAISO has *use*
   for it (load / storage charging / displacing dumpable CA renewable), and the
   thermal rung stays out — so the belly over-import self-limits instead of
   flooding a flat capability.

Why B first: it reuses the existing tranche/injection machinery and the corridor
links; the only new object is a measured hourly **supply-curve profile** (a
rule-13 input: the West's physical net position, regenerable forward). It is a
single-delta A/B against the keeper. It directly targets the belly over-import
(caps the clean rung at the West's actual surplus).

**Risk B carries:** if CAISO belly price and the clean rung are both ~$0, the LP
can still import up to `min(S_clean, TTC)` to charge storage / curtail CA solar.
Whether that reproduces the measured belly transfer is the empirical question
the A/B answers — but unlike the killed depth gate, the ceiling is now the
West's *physical* surplus, not a fitted 5 GW, so it is forward-honest either way.

### Option A (FULL co-optimized WECC-West zone) — escalate only if B underfits

`WECC_import` becomes a real zone: nonzero demand (West load), renewable
decision variables (W/S with CF = measured available ÷ capacity), a reduced
thermal + hydro fleet, its own storage. The one ISO-agnostic LP then
co-dispatches CA + West and the tie flow is a pure congestion outcome. Most
correct and fully forward-endogenous, but the largest build (a neighbor fleet +
its evolution, demand, renewables, storage) and it stresses the ISO-agnostic
layer (a second "ISO" inside one config). Specify only if B's A/B shows the
reduced curve cannot hold both the belly volume and the evening/overnight
import.

## 4. Data foundation (this session delivers the derive)

Source: `data/raw/eia-930/EIA930_BALANCE_*.parquet` (already on disk, all 66
BAs, 2018–2026; the caiso-109 P1-A probe proved it loads). WECC-West = EIA-930
Region **NW + SW**, CISO excluded, aggregated by UTC hour then mapped to the
CAISO model clock (the `_caiso_interchange_model_clock` alignment the corridor
loaders use). Per hour it yields: demand, solar, wind, hydro, gas, coal,
nuclear net generation → the Option-B profiles:

- `S_clean[t]` = max(0, solar+wind+hydro − demand)   (clean export MW)
- `thermal_headroom[t]` and the West gas/coal MC inputs for the thermal rung(s).

Schema-first intake (per the `data-intake` contract): the
`data/dictionary/schema/wecc-west-supply.schema.yaml` schema + the
`scripts/data/derive_wecc_west_supply.py` derive writing the clean frame via
`write_clean` (the derived parquet is gitignored/disposable; the raw BALANCE and
the derive script are the committed provenance). Heterogeneous-schema handling
(old single-solar vs new split-battery columns; int/float drift) is already
solved in `scripts/probes/_caiso109_westwide_surplus.py::_read_balance_file` —
lift it into the derive.

**Rule-13 admissibility:** `S_clean` is the West's physical net renewable
position — a measured input that *regenerates for a forward year from forward
drivers* (West solar/load trajectories) and *responds to changed conditions*.
It is NOT a fit to the CAISO residual (that is exactly what caiso-107/109 refused
and what the year-drift disqualified). It enters as a supply curve the LP clears,
never as a pinned CAISO import.

## 5. Gating, mutual exclusion, DOF ledger

- New `ScenarioConfig.caiso_endogenous_wecc_node: bool = False` (default off).
- When on, it **supersedes** `caiso_dsw_surplus_clean` / `_overnight_clean` /
  `_daytime_clean` at `WECC_import` (mutually exclusive — one mechanism per
  phenomenon, rule 18). The firm self-schedule floor (caiso-77) and PNW_midC /
  DSW_CCGT spot rungs may remain (they are the contract + spot layers, not the
  clean-surplus depth being replaced) — the A/B decides.
- DOF ledger: the supply-curve profile is a measured input (0 free params); the
  thermal rung's HR/VOM are the West fleet's published values, not tuned. No
  new tunable enters `run_config.json`.

## 6. A/B plan (caiso-110, next session)

Single-delta B-leg vs a fresh same-machine `caiso102_repro_A`, **all three years
one bundle** (rule 16), sequential solves (~8 min/yr, in-session — never CI).
Pre-register BEFORE solving:

- **PRIMARY C5a**: CO2 −11.1/−9.1/−12.1 % → toward 0 all three years (gas TWh
  rises toward 74.2/61.0/51.6), without overshooting past +7 %.
- **C4**: gas NRMSE 0.333 (2023) < 0.30; r stays ≥ 0.70.
- **C3c**: scarcity-tail hours rise toward RT actual 47/35/8.
- **GUARD**: C3a mean LMP + C3b shape STAY PASS; belly/evening/overnight
  residuals not materially worsened; net-import annual toward actual
  28.9/32.4/36.2 TWh (not past it).
- **C8**: if a floor/must-take is used at the node, forced-share within budget
  (rule 20).
- **Rule 22**: leave-one-year-out within 2023–2025 before any promotion.
- **KILL**: import reduction leaks into the belly and breaks C3a/C3b; OR the
  clean rung still floods midday (B underfits → escalate to Option A); OR gas
  overshoots (over-correction).

## 7. What this session delivered / what's next

- **This session (caiso-109 tail):** this design doc + the WECC-West **derive**
  (`scripts/data/derive_wecc_west_supply.py`) + its schema
  (`data/dictionary/schema/wecc-west-supply.schema.yaml`), runnable and verified
  on-disk through the `write_clean` contract (West demand ~54–57 GW, solar
  6.8/9.5/11.8 GW belly-peaked and growing, net export +2.2 GW). The derive also
  established the **Option-B-degenerate** finding (§3). No core LP touched (rule
  26/27 — no unvalidatable core-infra edit).
- **caiso-110 next:** wire **Option A** — give `WECC_import` nonzero demand +
  renewable-CF-capped W/S decision vars + a reduced thermal/hydro fleet from the
  clean `wecc-west-supply` frame, aligned UTC→model clock via the corridor map;
  gate on `caiso_endogenous_wecc_node` (default off), superseding the
  caiso-87/93/94 clean-depth tranches; A/B per §6; rule-22 LOYO before promotion.
  The full-zone build stresses the ISO-agnostic layer (a neighbor fleet inside
  one config) — scope it as its own first step, fleet-construction before the
  A/B.
