# Temperature-dependent derate: full keeper rerun playbook (2026-07)

## Background

`ScenarioConfig.temp_dependent_derate` (default off) is a new, physically-derived
alternative to the flat EIA-860 net-summer / `_SUMMER_CLASS_DERATE` capacity
treatment, added on `claude/temp-dependent-derates-21ayw9` (merged to `main`).
Thermal available capacity is derated by a per-class curve in measured hourly
zone dry-bulb temperature instead of a flat season-average net-summer number:

- **CC/CT** (gas turbines, air-density/mass-flow limited): the curve is
  rescaled so its Jun-Sep mean reproduces the existing net-summer capability —
  a capacity-**neutral reshape**, not a level change. Heatwave hours fall
  below net-summer (the scarcity driver); cooler hours rise toward full
  rating.
- **COAL / ST_GAS** (condenser-limited, no prior summer derate): gain a pure
  **additive** hot-hour derate.
- Nuclear excluded. Zones without weather coverage fall back to the flat
  derate. Availability is always clipped to `[0, 1]`.

See `src/market_sim/data/fleet.py` (`generators_to_fleet_arrays`, the
`temp_dependent_derate` block) and `src/market_sim/config/scenarios.py`
(field docstring, slopes/reference temps with citations) for the full
mechanism and its physical sourcing (arXiv:2311.07001, CPUC R.21-10-002).

**Single-year validation** (`scripts/probes/_pjm_tempderate_ab.py`,
`_ercot_tempderate_ab.py`; bundles `results/calibration/{pjm_tempderate25_on,
ercot_tempderate23_on}` etc.) showed a real, physically-grounded improvement
in the C3c scarcity-tail gap against `frontend/data/backcast/tail/actual_tail.json`:
ERCOT 2023 hoursGt200 3->75 (actual 311, 23% of the undershoot closed); PJM
2025 hoursGt200 0->4 (actual 51, 8% of the undershoot closed). The mechanism
is directionally confirmed but does not single-handedly close the gap —
this full-keeper rerun is to see its effect across all three train years and
every ISO, not to declare victory prematurely.

## Objective (per ISO)

Reproduce the ISO's **current keeper's exact configuration**, for **all three
train years in one bundle** (rule 16 — never a single-year keeper), with only
`temp_dependent_derate=True` added, plus its **rule-20 zero-forcing ablation
twin**. Register both as **PROBES** on the dashboard (never touch
`keepers.json` — promotion is a deliberate, separate owner decision after
reviewing results). Score and report back.

## Step 0 — orient

1. `git fetch origin main && git checkout -B <your-branch> origin/main` — main
   already carries the mechanism (verify:
   `grep -c temp_dependent_derate src/market_sim/config/scenarios.py` should
   be >= 1). Branch name: `claude/temp-derate-keeper-<iso-lowercase>`.
2. Re-read `frontend/data/backcast/keepers.json` on **your fresh checkout** —
   it may have moved since this playbook was written. Confirm your assigned
   ISO's keeper id and bundle path in the corresponding
   `frontend/data/backcast/registry/<keeper-id>.json` (`bundle` field).
3. Find the true next-available shorthand number for your ISO by scanning
   `frontend/data/backcast/registry/` (do not just increment the current
   keeper's number — rejected/probe runs already consume higher numbers).
   Example: `git ls-tree -r --name-only origin/main --
   frontend/data/backcast/registry/ | grep -i <iso>`. Follow that ISO's own
   existing dash/no-dash naming convention (they differ: `pjm-93`,
   `ercot48`, `caiso-68`, `miso-49`, `nyiso-58`, `neiso-55` — verify, don't
   assume).

## Step 1 — write the probe script

Model it directly on the two proven, already-working templates in
`scripts/probes/`: `_pjm_tempderate_ab.py` and `_ercot_tempderate_ab.py`
(single-year versions of exactly this pattern), and `_pjm_interchange_ab.py`
(the original template these were built from). Do **not** hand-translate the
keeper's flags into a CLI invocation — reconstructing nested dict flags
(`offer_curve_overrides`, `coal_prb_sigmoid_overrides`, etc.) via CLI args is
fragile; calling `solve_and_persist` directly with the keeper's own recorded
`calibration_flags` dict is the reliable, already-validated path.

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "<keeper bundle dir from Step 0.2>"


def main(mode: str) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    ablate = mode == "ablation"
    out = ROOT / ("<iso><NN>_tempderate" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        cf["years"],  # ALL THREE years in one call (rule 16) -- not [year]
        cf["iso"],
        cf["hours"],
        _load_reference(),
        commitment=cf["commitment"],
        screen_coal=cf["commitment_screen_coal"],
        run_dir=out,
        # ... every other cf[...] key, mapped 1:1 to the same-named
        # solve_and_persist kwarg. BEFORE running, verify EVERY key in cf
        # actually binds:
        #   python3 -c "
        #   import inspect, sys, json
        #   sys.path.insert(0, 'scripts')
        #   from run_calibration_full import solve_and_persist
        #   cf = json.load(open('<bundle>/run_config.json'))['calibration_flags']
        #   sig = inspect.signature(solve_and_persist).parameters
        #   missing = [k for k in cf if k not in sig and k not in
        #              ('iso','years','hours','git_sha')]
        #   print('unmapped keys:', missing)"
        # A nonempty `missing` list means this ISO's keeper uses a flag path
        # solve_and_persist doesn't expose directly -- read main()'s config-
        # assembly code (search run_calibration_full.py for that flag name)
        # to find how it's actually threaded, and/or check meta.json (not
        # just run_config.json's calibration_flags) the way
        # _pjm_interchange_ab.py pulls gas_monthly_actuals from meta.json --
        # calibration_flags is a curated subset, not always exhaustive.
        temp_dependent_derate=True,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "<iso><NN>_tempderate").name if ablate else None,
        note=f"temp-derate full-keeper {mode} -- <keeper id> config + temp_dependent_derate, 2023-2025",
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
```

Run `main` first, then `ablation`, once `main`'s bundle dir exists (needed
for `ablation_of`).

## Step 2 — run (concurrency)

**CLAUDE.md rule 12**: per-plant multi-zone LP solves cap at ~2 concurrent,
system-wide, to avoid OOM. Your own keeper + ablation pair already consumes
that budget by itself — **do not start a second ISO's solves on the same
machine/environment while yours are running.** If another session is running
a different ISO's temp-derate rerun concurrently, check with the user before
launching, or confirm you're in an isolated compute environment. Launch with
`run_in_background`, confirm no early traceback, then wait for the
completion notification rather than polling.

## Step 3 — verify

- Bundle exists with `meta.json`, `run_config.json`, `system.parquet`, etc.
- `grep temp_dependent_derate <bundle>/run_config.json` shows `true` in
  **both** `calibration_flags` and `scenario_config` (the
  `calibration_flags` allowlist was fixed on `claude/temp-dependent-derates-21ayw9`
  to include this key — if it's missing from `calibration_flags` specifically
  but present in `scenario_config`, that fix didn't make it into your branch;
  pull `main` again).
- `python scripts/calibration_verdict.py results/calibration/<bundle>` runs
  clean and produces a determination.

## Step 4 — compare and report

Compute, per year, at minimum:

- `hoursGt200` (zonal-max hourly price >= threshold) vs the keeper's own
  value vs `frontend/data/backcast/tail/actual_tail.json`'s `da_gt` — the
  same metric used in the single-year validation.
- Aggregate fuel-mix deltas by plant_group (CAMPD/EIA-923 net-to-grid, if the
  ISO has that benchmark) vs the keeper's own numbers — capacity reshaping
  can shift dispatch mix, not just price.
- Any change in `calibration_verdict.py`'s C1-C8 determination vs the current
  keeper, especially C3c (scarcity tail), C7 (diurnal shape), C8 (forced
  energy — capacity tightening can push floors/bridges over their budget).

## Step 5 — register (probe, not promotion)

Use the `calibration-report` skill (or `scripts/dashboard_add_run.py` +
`scripts/build_manifest.py` directly) to register **both** bundles — the
main run and its ablation twin — as numbered probes at the shorthand number
from Step 0.3. Follow rule 14 (every completed run goes on the dashboard,
keeper or not) and the top-15-per-ISO retention convention. **Do not edit
`frontend/data/backcast/keepers.json`.** Promotion is the user's call after
reviewing your report across all six ISOs together.

## Step 6 — push

Never `git push` for anything beyond a trivial diff on this remote — large
result payloads (parquet-adjacent JSON, bench files) reliably hit HTTP 413.
Use `scripts/archive/ci_api_upload.py` (reads files from disk, commits via the
GitHub Data API, exactly matches this exact use case — dashboard registration
files + bundle sidecars) or `mcp__github__push_files` for small file sets.
Small source-only diffs (the probe script itself) may use `git push`, but if
it 413s, fall back to the same API path immediately rather than retrying.

## Step 7 — final report format

For each ISO, report: bundle path, registered probe id, `hoursGt200`
before/after/actual per year, C1-C8 verdict delta vs the current keeper, and
an explicit **recommendation** (promote / hold for more investigation / not
grounded) with your reasoning — but do not act on the recommendation
yourself. CLAUDE.md rule 1 applies: never judge this mechanism by whether it
improves the backcast fit alone — it's a real physical mechanism regardless;
report what changed structurally (fuel mix, scarcity shape, forced-energy
budget) alongside the fit numbers.
