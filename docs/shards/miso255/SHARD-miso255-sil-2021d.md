# SHARD miso255-sil-2021D — MISO 2021, `miso_import_sil_measured_envelope` arm

Pin: `d0fec486fa2218afc55dbd2eb377bc2570e61699`
Arm bundle: `results/calibration/miso255_sil_2021` (gitignored, on local disk)
Control: `results/calibration/miso251_tp2021` (committed; rule 29(b) form 4)
Command: `replay_keeper.py results/calibration/miso251_tp2021 --years 2021 --out-dir results/calibration/miso255_sil_2021 --set miso_import_sil_measured_envelope=true`

## G-1 marker (verbatim)

```
INFO: MISO 2021: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 5665 / max 9064 MW, export mean 0 / max 137 MW; import below the scalar in 8520 h, export in 8760 h
```

## Gate-scorer JSON (`scripts/probes/_miso255_screen_gates.py`, full)

```json
{
  "year": 2021,
  "arm": "results/calibration/miso255_sil_2021",
  "control": "results/calibration/miso251_tp2021",
  "G6_reported": {
    "import_twh_control": 75.9260931826172,
    "import_twh_arm": 49.340422444213864,
    "import_twh_meter": 35.512724,
    "import_env_ceiling_twh": 49.6213078,
    "gas_twh_control": 115.39531207084656,
    "gas_twh_arm": 136.955632686615,
    "cc_regular_twh_control": 72.3575439453125,
    "cc_regular_twh_arm": 89.0836181640625,
    "class_delta_twh": {
      "CC_CHP": 2.071,
      "CC_REGULAR": 16.726,
      "COAL_BIT": 1.241,
      "COAL_LIGNITE": 0.131,
      "COAL_PRB": 3.617,
      "CT_CHP": 0.137,
      "CT_PEAKER": 0.937,
      "ST_CHP": 0.173,
      "ST_GAS": 1.515,
      "import": -26.586,
      "oil": 0.015
    }
  },
  "direction_check": {
    "abs_import_move_twh": 26.58567073840332,
    "note": "2022's move must exceed 2021's in absolute MWh (PRECOMMIT §3)"
  },
  "gates": {
    "G1_liveness": {
      "pass": true,
      "detail": "INFO: MISO 2021: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 5665 / max 9064 MW, export mean 0 / max 137 MW; import below the scalar in 8520 h, export in 8760 h"
    },
    "G2_confinement": {
      "pass": false,
      "max_import_violation_mw": 0.0003906250003637979,
      "max_export_violation_mw": 1603.800048828125,
      "hours_import_violating": 0,
      "hours_export_violating": 3
    },
    "G3_rail_broken": {
      "pass": false,
      "control_rail_hours": 8650,
      "arm_rail_hours": 198
    },
    "G4_not_a_pin": {
      "pass": false,
      "frac_hours_at_99pct_of_envelope": 0.9474885844748858,
      "line": 0.8,
      "distinct_hourly_import_values_arm": 422,
      "distinct_hourly_import_values_control": 110
    },
    "G5_non_target": {
      "pass": null,
      "note": "score with scripts/calibration_verdict.py; C2/C6/C8 must not flip",
      "arm_metrics_present": false,
      "arm_legitimacy_present": false
    }
  },
  "verdict": "STOP"
}
```

## Container preflight / memory peak (verbatim)

```
INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a096d2-c5c2-70de-b121-bc2e1230be05/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 10 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 10.0 = 23.3 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 23.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
INFO: memory peak: cgroup_peak_rss_gib=13.34, cgroup_peak_rss_plus_swap_gib=16.50, process_vmhwm_gib=13.31, process_vmswap_now_gib=0.05
```

## Phase timing (verbatim)

```
INFO: year 2021 phase timing: data_prep=63.2s solve_p0=564.1s markup=33.5s solve_p1=155.7s results_write=94.8s total=911.4s (markup: setup=0.0s p0_post=13.7s markup=1.3s seam=0.8s p1_post=17.3s tail=0.0s other=0.4s) (results_write: state=1.7s frames=12.6s parquet=7.0s bench=28.1s sidecars=45.4s)
```

## Did any STOP fire?

No shard-prompt HARD STOP fired: the pin matched, both test files passed (14 tests), the control bundle carried its `meta.json` and `hourly/class_hourly_2021.parquet`, free disk was 17 GiB against the 13 GiB floor, and HARD STOP 4 — the arm's liveness marker with `declared scalar 8700 MW` — was present, so the solve ran to completion and wrote its bundle in 911.4 s. The **gate scorer**, however, returned `verdict: STOP`: G-1 passes, G-5 is unscored (`null` — `replay_keeper` writes no `metrics.json`/`legitimacy_diagnostics.json` into the bundle), and three structural gates read `false`. G-2 fails on the export side only — imports sit inside the injected envelope to 0.0004 MW across all 8760 hours, but exports exceed the measured export envelope by up to 1,603.800 MW in 3 hours. G-3 fails literally, on its `arm_rail_hours == 0` test: the old scalar rail is largely broken (8,650 h → 198 h), but the measured envelope's import max of 9,064 MW exceeds the 8,700 MW scalar, so 198 hours still sit at or above it. G-4 fails widest — 94.75 % of hours sit at ≥99 % of the envelope against a pre-registered 80 % line, i.e. the arm relocates the rail onto the envelope rather than removing it, though hourly import resolution does rise (110 → 422 distinct values). Reported, gating nothing: import 75.926 → 49.340 TWh against a 35.513 TWh meter and a 49.621 TWh envelope ceiling, with gas taking up the 26.586 TWh (CC_REGULAR 72.358 → 89.084 TWh, +16.726). No infrastructure was touched, nothing was re-run with different flags, and the bundle is left on disk under rule 31.
