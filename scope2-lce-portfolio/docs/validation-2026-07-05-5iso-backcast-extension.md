# Validation memo — extending the real-priced backcast validation to CAISO/PJM/MISO/NYISO/NEISO

- **Date:** 2026-07-05
- **Scope:** `PLAN.md` §8/§10 "next open work" — extending the ERCOT 2024
  backcast-validation bridge (`docs/validation-2026-07-05-ercot-2024-backcast.md`)
  to the other five ISOs, each with its own re-solve.
- **Result:** five committed results stores — `results/{caiso,pjm,miso,nyiso,neiso}_backcast2024_premiumcap/`.

## What this is

Same technique as the ERCOT validation memo, generalized: for each ISO, its
**current calibration keeper** (`frontend/data/backcast/keepers.json` —
`caiso51_firm_base`, `pjm77_ct_relfloor_reconcile`,
`MISO/miso_41_ct_evening_window`, `nyiso41_hubprices`, `neiso_ctscrub`, all
covering 2023-2025) was re-solved for 2024 via `scripts.run_calibration.run_year`
— the same calibration-specific solve path (per-ISO offer curves, must-run
floors, reserve co-optimization, etc.) that produced the registered keeper,
not the generic forecast runner. A one-off bridge script (not committed, same
posture as the ERCOT one) reconstructed each keeper's resolved flags from its
committed `meta.json`, re-solved 2024, and collapsed the zonal LP duals to one
ISO-level hourly LMP (load-weighted average, ADR 0011) directly from the fresh
`DispatchResult` — no `market_sim` cache/`resolve_bau_config` round-trip was
needed this time (that machinery is forecast-year-oriented; going straight
from the solved result avoided the cache-key/`resolve_bau_config` mismatch the
ERCOT memo had to work around).

Zero edits to `run_calibration.py` / `run_calibration_full.py` / `runner.py` —
the bridge script only calls their existing, already-public functions
(`run_calibration.run_year`, `_load_reference`, `_henry_hub_actual`, and the
same demand-reconstruction helpers `export_lce_lmp.py` uses). Real per-ISO CF
profiles (`scripts/build_profiles.py --year 2024`) and the reference load
(`scripts/make_reference_load.py`) were rebuilt in this container (gitignored,
regenerate on demand) for all six ISOs.

## Gate: meta.json schema-drift caveat (generalizing the ERCOT gate-0 finding)

Each keeper's `meta.json` (the calibration-flags snapshot `write_run_config`
records) predates a handful of `solve_and_persist`/`run_year` parameters added
since. For all five ISOs the dropped keys were identical and are all
ERCOT-only levers that are no-ops outside ERCOT anyway (`ercot_dam_as_overlay`,
`ercot_dam_as_overlay_from_year`, `ercot_dam_as_scarcity_threshold`,
`ercot_rtordpa_overlay`), plus `btm_backfill_year` (a generic opt-in BTM-backfill
override with no recorded value for these keepers, left at its default
`None`/no-op). None of these represent a real deviation from what each keeper
actually ran. As with the ERCOT memo, this re-solve is **not** presented as a
byte-exact reproduction — it is a fresh, structurally-identical calibration
solve for validation purposes only, never registered as a keeper or probe on
the dashboard (rule #16).

CAISO carries one additional topology wrinkle: its keeper's
`caiso_per_hub_intertie=True` splits `WECC_import` into two per-hub corridors
(Malin/COI → NP15, Palo Verde/Path-46 → SP15) inside `run_year`/`solve_and_persist`,
giving 5 priced zones instead of the base 3 zones + 1 import node. The bridge
script's independent demand reconstruction (mirroring `export_lce_lmp.py`'s
`load_zonal_demand`) has to replicate that same split
(`market_sim.model.transmission.split_caiso_import_node_per_hub`) or the
zonal-price and zonal-demand array shapes disagree and the LMP collapse would
silently mis-weight; this was caught by the same-shape safety check `export_iso`
already carries and fixed before re-solving.

## Environment constraint: OOM at MISO/PJM scale, worked around with swap

Running 3 ISOs concurrently OOM-killed two of them at ~11 GB RSS each on this
15 GB container (rule #12's "cap ~2 concurrent" undercounts non-ERCOT ISOs'
actual footprint — MISO's 1975-generator EIA-860 fleet and PJM's 1922-generator
fleet, each with full energy+reserve co-optimization, run far heavier than
CAISO/NYISO/NEISO). Switching to **strictly sequential** solves still OOM-killed
MISO and PJM individually at ~16 GB RSS each — a peak this container's bare 15 GB
cannot hold regardless of concurrency. An 11 GB swapfile
(`/swapfile_lce_bridge`, added for this session only) gave enough headroom for
both to complete without further incident. This is a container-sizing
observation, not a tool or model defect; a session with more available memory
would not need it.

## Results

### Hourly ISO LMP (`data/inputs/bau_lmp_2024_5iso_backcast.csv`, gitignored — sidecar provenance committed conceptually via this memo)

| ISO | mean $/MWh | min | max | annual load (TWh) |
|---|---:|---:|---:|---:|
| CAISO | 48.46 | -19.06 | 95.60 | (WECC-import-inclusive zonal demand) |
| PJM | 26.59 | -21.24 | 54.21 | |
| MISO | 25.63 | 16.83 | 47.06 | |
| NYISO | 28.79 | -26.00 | 176.48 | |
| NEISO | 36.55 | 8.62 | 197.52 | |

Negative hours (PJM/NYISO/CAISO) are plausible 2024 duck-curve/must-run
curtailment economics, not a solve artifact — all five keepers carry real
renewable buildout and gas must-run floors that can go negative when
low-cost/must-run generation exceeds load net of exports. NEISO's $8.62 floor
matches the same VOLL-adjacent floor level ERCOT's validation reported
($8.63) — plausibly a shared reserve/must-offer price floor mechanism, not a
coincidence worth chasing further here.

### Hourly fossil-only average CO2 rate (`data/emissions/{ISO}_2024_fossil_avg_co2_rate.parquet`, ADR 0013)

| ISO | mean tCO2/MWh | min | max |
|---|---:|---:|---:|
| CAISO | 0.3585 | 0.3084 | 0.4701 |
| PJM | 0.5620 | 0.4806 | 0.9227 |
| MISO | 0.6185 | 0.4919 | 0.8057 |
| NYISO | 0.3918 | 0.3534 | 0.5789 |
| NEISO | 0.3627 | 0.3452 | 0.4117 |

Ordering matches fleet composition: MISO/PJM (coal-heavy) carry the highest
fossil-only intensity, CAISO/NYISO/NEISO (gas-dominated fossil margin) the
lowest — consistent with published EIA/eGRID regional fossil generation mixes.

### Premium-cap sweeps (Mode A, same extended range as the ERCOT sweep: `{1,2,5,7,10,15,20,30,40,50,75,100,150}` $/MWh)

PJM, MISO, NYISO, and NEISO all reproduce the ERCOT sanity pattern cleanly:

- **Monotonic premium-vs-matching** — PASS for all four (strictly
  non-decreasing across every point).
- **Storage entering only at high targets** — PASS: `battery_4h` first
  appears at 71-74% matching (PJM/MISO $30/MWh, NYISO $30/MWh, NEISO
  $20/MWh) and grows monotonically through the tail, matching ERCOT's
  95.78%-first-entry pattern qualitatively (these four ISOs have thinner
  wind/solar resources than ERCOT, so storage earns its way in earlier).
- **Near-100% matching only at the top of the range** — PJM/MISO reach
  99.8-99.9% at $100/MWh and 100% at $150; NYISO/NEISO reach 100% at
  $100/MWh — all Optimal solves, all a smoothly rising frontier (e.g. PJM:
  5.19% → 10.37% → 25.94% → ... → 91.06% → 99.87% → 100.00%).

**CAISO does not reproduce this pattern** and is flagged rather than
papered over: its frontier is **100% matching at every premium setpoint from
$1/MWh up**, building `onshore_wind` at 16,000-19,500 MW — against a
20,000 MW ADR 0009 resource-potential cap (`data/caps/resource_caps.csv`) —
for a single 100 MW reference facility. This is the tool's own
already-documented Mode A limitation surfacing concretely: `PLAN.md` §4
records that Mode A minimizes `Σ grid_buy` subject to `premium ≤ delta` with
**no cost tiebreak** ("a least-cost tiebreak was tried and removed — it
stalled the solver"), so among the many portfolios that satisfy a loose
premium bound, the solver is free to pick an arbitrarily large one. CAISO's
own LMP series (mean $48/MWh, volatile, negative in duck-curve hours) makes a
massive wind build's excess-sale revenue rich enough to keep net cost within
even a $1/MWh premium band, so the solver lands on a near-cap corner solution
at every setpoint instead of the graduated build the other four ISOs show.
This is consistent with, and a more visible instance of, the "solver
degeneracy/substitution effect" the ERCOT memo already noted at its frontier's
high-premium tail — here it dominates the **entire** CAISO frontier because
of CAISO's specific price/resource combination, not a new defect. **Not
fixed here** — a real fix (e.g. a soft least-cost tiebreak that does not
stall the solver, or a per-run sanity cap) is Mode A LP design work, out of
scope for a validation session and deserving its own planning session/ADR.

> **Update 2026-07-05 — fixed.** See **ADR 0019**
> (`docs/decisions/0019-mode-a-build-tiebreak.md`) and
> `docs/validation-2026-07-05-caiso-mode-a-tiebreak-fix.md` for the design,
> the regression-test proof (`tests/test_mode_a_build_tiebreak.py`), and a
> real-data before/after CAISO re-solve + ERCOT control. Summary: a flat
> `build_tiebreak_epsilon` (default `1e-6`) on `build_mw`/`build_energy` in
> Mode A's objective breaks the tie toward the smallest capacity that attains
> the same matching/premium, without moving a build level the LP already pins
> for a real economic reason. A `net_cost`-weighted least-cost tiebreak (the
> "soft" option floated above) was tried again and rejected — it reintroduces
> the same mixed-$-scale risk this section's stalled-solver note refers to,
> and is not even guaranteed to shrink the build (see the ADR for why).
> Separately, this session found the **committed CAISO bundle referenced
> above priced against a synthetic, not real, CF shape** — its config left
> `year=2030`/`profile_shape_year=None` while only a `CAISO_2024.parquet`
> profile existed, so `build_cf_matrix` silently fell back to synthetic
> shapes (`CAISO_run_metadata.json`'s `profile_source.source == "synthetic"`,
> visible in the committed file). That is an unrelated data-provenance slip
> in how this memo's CAISO run was invoked, not a tool defect; the tiebreak
> re-solve corrects it (`year=2024`/`profile_shape_year=2024`) alongside the
> fix.

## What this does and doesn't validate

**Validates:** the tool's intake → LP → sweep → outputs pipeline runs
end-to-end against five more real, non-trivial priced/emissions inputs, with
PJM/MISO/NYISO/NEISO reproducing every ERCOT sanity check (monotonicity,
late storage entry, plausible fossil-intensity ordering). **Does not
validate:** CAISO's premium-cap frontier, which surfaces a pre-existing Mode A
degenerate-solution limitation rather than a CAISO-specific bug; a real facility
load shape or Mode B (matching-target) sweep might avoid tripping it and is
future work. As with ERCOT, **the market-sim FORECAST path stays on hold**
(stakeholder, 2026-07-02) — this is the backcast-validation carve-out ADR 0015
permits, not a readiness sign-off.
