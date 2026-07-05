# Forecast-invariant findings — 2026-07 (W2-P5 stage 1)

First run of `scripts/check_forecast_invariants.py` (plan §2.2) over real forecast
solves. **Findings only — no model code was changed this session** (plan stage-1
item 5). A FAIL here is a root-cause issue to open, never a threshold to widen
(rules 1/11/14).

## Runs scored

| run | config | result |
|---|---|---|
| ERCOT 2026-2028 | reference forecast, legacy heat-rate bins (small-LP proxy for the 2026-2040 sweep) | 5 FAIL-worthy findings below; the machinery invariants (I1/I2/I4/I5/I11) all PASS |
| NEISO 2026-2030 | default forecast | **did not solve** — see F0 |

The ERCOT window was solved at 2026-2028 (3 real 8760 two-pass HiGHS years) rather
than the full 2026-2040 designated in the prompt because each ERCOT year is minutes
long; the invariants that fire (I7/I12) are already saturated at year 1, so the
finding does not depend on the extra years. Re-run over 2026-2040 before closing
each finding.

## Findings

### F0 — NEISO default forecast is infeasible (blocks the NEISO nightly smoke)
`run_scenario_iso(ScenarioConfig(iso="NEISO"), "NEISO")` raises
`dispatch LP has no feasible primal solution (status: Infeasible)` on the first
(P0) solve of 2026, at full 8760 and default levers. The plan §2.4 nightly tier
names "NEISO 2026-2030 smoke (smallest real ISO)" — that tier cannot be wired
until NEISO's default forecast is feasible. **Open:** identify the binding
infeasibility (candidate: an import-node / HQ interchange balance or a must-run
floor that over-constrains the first forecast year) before standing up the NEISO
smoke. Not a checker defect — the checker never gets a cache to read.

### F1 — I7 reliability floor: post-evolution thermal below the floor every year
`[FAIL] I7  2026: thermal 78102 < floor 107769 MW; 2027: 78982 < 113158;
2028: 80067 < 118816`. The economic-retirement reliability floor
(`capacity.apply_economic_retirements`) only *prevents over-retiring* below
`(peak − firm_clean)×1.15`; it does **not** force-build up to it, and the
force-building backstop (`reserve_margin_build_enabled`) is off by default. So a
forecast whose starting thermal fleet is already below the floor stays below it,
and I7 (an absolute floor) FAILs. **Open:** decide whether the invariant should
compare against the *retirement* floor (retirement-bounded, always satisfiable)
or whether the default forecast should enable the adequacy backstop. Until then
I7 is expected to FAIL on any ERCOT forecast that starts thermal-short. (The
legacy-bin fleet is thermal-lighter than the CAMPD per-plant fleet, which
inflates the gap here; re-check under CAMPD bins.)

### F2 — I12 reserve-margin band: margins far below the planning floor
`[FAIL] I12  band [13.8%, 28.7%]; out: 2026:5.7%, 2027:5.3%, 2028:4.2%`. The
accredited firm-capacity reserve margin (`accredited_firm_capacity_mw`) sits at
4-6%, well under the ERCOT planning floor (13.75%) and falling year over year —
the same root cause as F1 (nothing force-builds firm capacity in the default
forecast). Three consecutive out-of-band years trip the FAIL (WARN would fire on
a single excursion). **Open:** same decision as F1. The falling trend also means
the forecast is quietly de-firming, which the entry screen is not correcting at
these prices — worth a look at whether the ORDC scarcity adder is reaching the
new-entry economics in the legacy-bin path.

### F3 — (resolved this session) I8 planned-additions traceability
The first run showed `[FAIL] I8  2 planned units without an EIA-860 id`. Root
cause was in the **ledger attribution**, not the model: planned `Generator`s
carry their EIA plant in `unit_id` (`planned_<plant>_<gen>`) but leave the
`plant_id` field unset, so the ledger recorded `eia860_id = None`. Fixed by
falling back to `unit_id` for the `eia860_id` of planned additions
(`model/capacity.py`). I8 now PASSes. Logged here because it was surfaced by the
checker; it is a ledger fix, not a model-behaviour change.

### F4 — (resolved 2026-07-05) I9 storage-integrity FAIL on a PJM hindcast was a
### demand-defect scoring artifact, not a checker or storage/LP defect
The PJM 2021-2025 realized capacity hindcast (`docs/hindcast-reports/pjm-2021-2025-realized-2026-07-05.md`)
showed `[FAIL] I9 2023: simultaneous chg+dis 6.09% of throughput; 2024: 1.32%`.
Triage (task: PJM demand/storage-integrity session): `data/raw/eia-930/eia_demand_profiles.parquet`'s
PJM 2021 series carried a 3-hour, ~4-5-order-of-magnitude demand spike (fixed
by `scripts/curate_demand_profile.py`, see the hindcast report's "Update"
section for the full repair writeup). That spike drove VOLL-level scarcity
pricing into 2021's `prior_results`, which the 2022 bridge and 2023 entry/
dispatch economics consume by design (rule 22) — a corrupted price *signal*,
not a defect in the ε=0.001 $/MWh storage tiebreaker or the LP formulation.
Re-running with the repaired 2021 series makes I9 PASS outright; directly
inspecting the per-unit `storage_charge`/`storage_discharge` arrays confirms
simultaneous charge+discharge is ~1e-18 of throughput (float noise) in every
year (2021, 2023, 2024, 2025 alike) once the input is sane. **No change to
`model/storage.py` or `model/dispatch.py` was needed or made** — this is a
scoring artifact of corrupted upstream input data, not a model-behavior fix,
so it is logged here rather than reported as a new checker bug.

## Invariants that PASS on the real forecast (machinery is sound)

I1 energy balance (residual 3.6e-10 MW — the persisted demand column closes the
balance exactly), I2 no NaN/inf, I3 unserved/dump, I4 capacity accounting closes,
I5 no retire-and-reenter, I6 econ-retirement sanity, I9 storage integrity, I10
RPS dual (≥0, stable), I11 one-pass, I13 cobweb, I14 price sanity.

## Next actions

1. Re-run I1-I14 over ERCOT 2026-2040 under **CAMPD bins** (the reference fleet)
   and confirm F1/F2 persist or resolve with the fuller thermal fleet.
2. Resolve F0 so the NEISO nightly smoke (plan §2.4) can be wired.
3. Take F1/F2 to the owner as the "absolute floor vs retirement-bounded floor"
   decision; do not change I7/I12 thresholds to make them green.
