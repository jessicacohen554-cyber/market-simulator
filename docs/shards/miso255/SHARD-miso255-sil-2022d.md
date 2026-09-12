# SHARD miso255-sil-2022 — MISO 2022 SIL measured-envelope arm

Shard id: `miso255-sil-2022D`. Pinned to `d0fec486fa2218afc55dbd2eb377bc2570e61699`.

Arm:     `results/calibration/miso255_sil_2022` (gitignored, on local disk — rule 31 `[R-RETAIN]`)
Control: `results/calibration/miso251_screen2022`
Config delta: `miso_import_sil_measured_envelope=true`, one year (2022), replay of the control's recipe.

## Gate-scorer JSON (`scripts/probes/_miso255_screen_gates.py`, verbatim)

```json
{
  "year": 2022,
  "arm": "results/calibration/miso255_sil_2022",
  "control": "results/calibration/miso251_screen2022",
  "G6_reported": {
    "import_twh_control": -22.58256523778534,
    "import_twh_arm": 13.83488843227291,
    "import_twh_meter": 30.9655045,
    "import_env_ceiling_twh": 49.570919800000006,
    "gas_twh_control": 175.8751003742218,
    "gas_twh_arm": 147.70682406425476,
    "cc_regular_twh_control": 111.50921630859375,
    "cc_regular_twh_arm": 98.74368286132812,
    "class_delta_twh": {
      "CC_CHP": -2.914,
      "CC_REGULAR": -12.766,
      "COAL_BIT": -4.025,
      "COAL_LIGNITE": -0.115,
      "COAL_PRB": -4.075,
      "CT_CHP": -0.358,
      "CT_PEAKER": -9.43,
      "ST_CHP": -0.589,
      "ST_GAS": -2.112,
      "import": 36.417
    }
  },
  "direction_check": {
    "abs_import_move_twh": 36.41745367005825,
    "note": "2022's move must exceed 2021's in absolute MWh (PRECOMMIT \u00a73)"
  },
  "gates": {
    "G1_liveness": {
      "pass": true,
      "detail": "INFO: MISO 2022: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 5659 / max 8711 MW, export mean 218 / max 2985 MW; import below the scalar in 8730 h, export in 8760 h"
    },
    "G2_confinement": {
      "pass": true,
      "max_import_violation_mw": 0.00019531250018189894,
      "max_export_violation_mw": 3.6621093613575795e-05,
      "hours_import_violating": 0,
      "hours_export_violating": 0
    },
    "G3_rail_broken": {
      "pass": true,
      "control_rail_hours": 2609,
      "arm_rail_hours": 0
    },
    "G4_not_a_pin": {
      "pass": true,
      "frac_hours_at_99pct_of_envelope": 0.026484018264840183,
      "line": 0.8,
      "distinct_hourly_import_values_arm": 2345,
      "distinct_hourly_import_values_control": 4169
    },
    "G5_non_target": {
      "pass": null,
      "note": "score with scripts/calibration_verdict.py; C2/C6/C8 must not flip",
      "arm_metrics_present": false,
      "arm_legitimacy_present": false
    }
  },
  "verdict": "no STOP fired"
}```

## Container preflight

```
INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a096d3-2338-765e-a050-4de756bfc5fa/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 10 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 10.0 = 23.3 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 23.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
```

## Memory peak

```
INFO: memory peak: cgroup_peak_rss_gib=13.34, cgroup_peak_rss_plus_swap_gib=16.44, process_vmhwm_gib=13.31, process_vmswap_now_gib=0.05
```

## Phase timing

```
INFO: year 2022 phase timing: data_prep=40.8s solve_p0=492.3s markup=17.3s solve_p1=130.1s results_write=57.8s total=738.3s (markup: setup=0.0s p0_post=7.7s markup=0.6s seam=0.2s p1_post=8.6s tail=0.0s other=0.3s) (results_write: state=1.2s frames=7.5s parquet=4.4s bench=15.2s sidecars=29.5s)
```

## G-1 liveness marker (verbatim)

```
INFO: MISO 2022: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 5659 / max 8711 MW, export mean 218 / max 2985 MW; import below the scalar in 8730 h, export in 8760 h
```

## Did any STOP fire?

No STOP fired. All four hard stops passed before the solve: HEAD was the pinned
`d0fec486fa2218afc55dbd2eb377bc2570e61699`; the two named test files ran 14 passed; the control
bundle carried both `meta.json` and `hourly/class_hourly_2022.parquet`; and free disk read 17 GiB,
above the 13 GiB floor. The solve ran the runner unmodified with no `--no-container-preflight` and
no hand-provisioned swap — the runner's own preflight found a 13.34 GiB cgroup ceiling with zero
swap and provisioned 10 GiB, reaching 23.3 GiB against its 24 GiB target; it logged a warning that
this is below target and that a per-plant MISO year may be OOM-killed, but the run completed
normally and the measured peak (16.44 GiB rss+swap) sat comfortably inside what was provisioned, so
that warning was advisory and not a stop. HARD STOP 4 passed: the arm fired, and the liveness line
carries the required `declared scalar 8700 MW`. The gate scorer returned `"verdict": "no STOP
fired"` with G1–G4 all true; G5 is reported `null` by design — it is the non-target criterion check,
which the scorer defers to `scripts/calibration_verdict.py` rather than computing itself, and the
arm bundle carries no `metrics.json` / `legitimacy_diagnostics.json` for it to read. Scoring G5 is
the parent's job, not this shard's.
