# ERCOT-96 — DAM thermal availability at class-HOUR grain (Lane A build + transport manifest)

**Session 2026-07-22, branch `claude/ercot-thermal-dam-grain-all6f0`** (based on
main `4ff3118b`, the post-ERCOT-95 tip). Charter: close the ERCOT 2023-summer
C3c tail miss on its MEASURED owner — re-derive the DAM thermal availability at
finer-than-class-day grain (ERCOT-95 Finding 6's ~0.7-1.1 GW raw / +216 MW
model-relevant phantom CC+CT on summer afternoons). NOT the reserve-side ORDC
lane (ERCOT-95 refuted it).

## Lane A-1 MEASURE result (solve-free; `scripts/probes/_ercot96_phantom_measure.py`)

On the 181 actual 2023 RT tail hours (system_lambda > $200; 56 days, 169 of
181 hours in hod 13-19; PRC median 5,648 / min 2,697 MW):

| component | mean | p90 | max | fixed by |
|---|---|---|---|---|
| hod-shape phantom (day-mean − hour, CC+CT) | +216 MW | +433 | +578 | class-HOUR grain |
| per-plant misallocation (class-hour still smears) | 259 MW | 338 | 502 | plant-hour grain |

Notes: (a) Finding 6's raw table (+668 avg / +805 hod15 / +1,147 max) is the
UNCLIPPED HSL phantom over all Jun-Sep days; under the derive's own
rating-clip semantics — what the model actually consumes — the tail-day
phantom is +216 mean / +578 max. (b) The per-plant component is capacity
REDISTRIBUTION (net-zero on the class total): its price channel is merit-mix/
zonal placement, not system tightness, and reality's tail-hour derate is
spread wide (top-10 sites = 25% of the 6.7 GW mean). (c) ST_GAS tail-hour
phantom ≈ 0 (−34 MW mean). (d) Keeper 2023 model tail = 40 h, overlap 38 of
181; the 143 missing hours price at merit-order CC ~$56.

**Build decision:** class×HOUR is the deployable core (owns the total-excess
channel; zero mapping risk; explicitly permitted by the charter). Plant×hour
needs a DAM-site → EIA-plant crosswalk that does not exist (ERCOT mnemonics:
DDPEC/CBECII/WHCCS2…; 58 CC + 189 CT + 46 ST sites); building one follows the
CAISO reviewed-crosswalk pattern (`build_caiso_resource_crosswalk.py`,
accepted-gated) and stays a follow-up. The derive's site×hour intermediate is
the ready input for it.

## The mechanism (zero fitted parameters)

`ercot_thermal_dam_availability_hourly` (ScenarioConfig, default off; ERCOT +
backcast + on top of `ercot_thermal_dam_availability`): the covered classes'
availability is water-filled per HOUR to the measured 60-Day DAM per-HE
fraction — same disclosure rows, same bidirectional restore/remove semantics
as the deployed day grain, NaN hours keep the statistical stack. Derive:
`scripts/data/derive_ercot_thermal_dam_availability.py --hourly-out` →
`data/raw/ercot-thermal-dam-availability-hourly.csv` (day CSV byte-identical
to committed under the refactor). Rules 13/23: same measured source, finer
grain; no residual-fitted value anywhere.

## Transport manifest (rule 27 — this commit)

`git push` 413s in this environment and four touched files are too large to
move whole through a model response (`fleet.py` 522 KB, `scenarios.py` 540 KB,
`run_calibration_full.py` 463 KB, `run_calibration.py` 231 KB — the
constants.py-truncation incident class), so the WHOLE code change travels as
ONE atomic git patch:

- **`docs/handoffs/ercot96-lane-a-core.patch`** — all 7 modified files
  (derive script, run_calibration.py, run_calibration_full.py, scenarios.py,
  fleet.py, outages.py, tests/test_outages.py), 573 lines. Apply from repo
  root with `git apply docs/handoffs/ercot96-lane-a-core.patch` against main
  `4ff3118b`.
- **`data/raw/ercot-thermal-dam-availability-hourly.csv`** (594 KB, derived
  data) is NOT shipped: regenerate byte-exactly with
  `.venv/bin/python scripts/data/derive_ercot_thermal_dam_availability.py`
  (also rewrites the day CSV byte-identically) and verify the sha256 below.

Post-apply verification (`git hash-object <file>` must equal):

```
f1ffb0b538bbfaa4e66a6c324667c6f389c911cb  scripts/data/derive_ercot_thermal_dam_availability.py
d70e0676a3a85a62314eeb00be08dae7ff877747  scripts/run_calibration.py
247cce4cc3cd965eee4f9ab8cc2ec716fcec6984  scripts/run_calibration_full.py
943382b6c93a82c2e7a786f3c9997b30f7251520  src/market_sim/config/scenarios.py
69c65b9df562ecfdc8bf706129ca3eeeb88f58a8  src/market_sim/data/fleet.py
637bf55491608388956852f46e9e4a80a1d3b061  src/market_sim/data/outages.py
eaa35b8afc33753240b9a02d5bc37ebbe6b6a5a8  tests/test_outages.py
```

```
sha256(data/raw/ercot-thermal-dam-availability-hourly.csv) =
137295bff2a86518271824425f041a6d09f3dcd4c3a1384aae4611f42197a73f
git blob = 7d93a2eb38b41b5beef1d9f25861a241ff5fe70d
```

Tests: `tests/test_outages.py::ErcotThermalDamAvailabilityTest` (5 pass —
includes the fixed stale 2-class assertion, a pre-existing tip-main failure
since the 2026-07-18 ST_GAS scope change) + `test_flag_registry` /
`test_recorded_cfg_fidelity` / `test_replay_keeper_strict` (27 pass; the one
`test_flag_registry` FAIL — `add_flag_arguments` missing — pre-exists on
pristine `4ff3118b`).

## A/B status (final, 2026-07-22)

Base = byte-recipe ercot91 replay on this tree: reproduces the keeper's 2023
EXACTLY (40 tail h, mean $36.94) — tree drift solve-neutral. Probe (+hourly
grain, 2023): C3c 40→51 h (in-actual 38→46; 5 spurious all Jun-18/19
near-misses), C3a mean-px gap −26.0%→−22.1%, summer hod corr 0.885→0.908,
trough untouched. Full span `2026-07-22-ercot96-dam-hourly-grain`: 2024 tail
13→13 (C3a −7.3%→−6.6%), 2025 tail 1→0 (removed hour was spurious). Verdict:
C7 PASS, C8 PASS, C3a −27.8% / C3b NRMSE 0.539 ledgered CAVEATs (improved
from −32.5% / 0.631), C3c NOT-YET driver (2024/2025 unledgered). LOYO clean
(zero fitted parameters). **OWNER-PROMOTED to ERCOT keeper 2026-07-22**
(directive this session: 'Promote this to keeper'; supersedes ercot91;
C3c ledgering NOT taken — a separate owner action). Lane B moved to ERCOT-97
by owner direction (2026-07-22, this session), joined by the plant-grain
crosswalk and the measured RUC-conduct lanes — see
`docs/handoffs/ercot97-plant-grain-ruc-laneb-2026-07.md`.

Full log entry: `docs/calibration-log/ercot.md` § 2026-07-22 — ERCOT-96.

## Oversized-artifact placement (owner step)

The registered run's `runs/<id>.js` payload (1.48 MB), the bundle's hourly
parquets + slims (attestation now OWNER-PROMOTED), the appended
`docs/calibration-log/ercot.md`, the registry SIDECAR with its keeper
`market_story` (held off the branch so it lands atomically WITH the payload —
the calibration-report hard rule), the promotion files (`keepers/ERCOT.json`
re-pointed + rebuilt `status/ERCOT.js`, `audit_keepers.py --iso ERCOT` PASS),
and the hourly CSV travel to the owner as `ercot96-oversized-artifacts.tar.gz`
via the session file channel; the accompanying `PLACEMENT-MANIFEST.md` +
`tar.sha256` carry the authoritative archive sha256 and per-file git blob
SHAs with the one-command placement. Until that tar is extracted + pushed,
the run (and the keeper promotion) is registered in-session but INVISIBLE on
the live dashboard.
