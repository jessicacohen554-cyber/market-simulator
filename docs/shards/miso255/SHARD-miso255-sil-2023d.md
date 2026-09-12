# SHARD miso255-sil-2023D — MISO 2023, `miso_import_sil_measured_envelope` arm

Pinned SHA `d0fec486fa2218afc55dbd2eb377bc2570e61699`. Arm bundle
`results/calibration/miso255_sil_2023` (gitignored, on local disk only);
control `results/calibration/miso_fuelvintage_A` (committed — rule 29(b) form 4,
no control solve).

## Gate-scorer JSON (`scripts/probes/_miso255_screen_gates.py`, verbatim)

```json
{
  "year": 2023,
  "arm": "results/calibration/miso255_sil_2023",
  "control": "results/calibration/miso_fuelvintage_A",
  "G6_reported": {
    "import_twh_control": 43.1923685240593,
    "import_twh_arm": 41.94401733432388,
    "import_twh_meter": 37.913029,
    "import_env_ceiling_twh": 55.228547400000004,
    "gas_twh_control": 201.39804553985596,
    "gas_twh_arm": 202.25716352462769,
    "cc_regular_twh_control": 138.1505584716797,
    "cc_regular_twh_arm": 138.50222778320312,
    "class_delta_twh": {
      "CC_CHP": 0.077,
      "CC_REGULAR": 0.352,
      "COAL_BIT": 0.066,
      "COAL_LIGNITE": 0.01,
      "COAL_PRB": 0.305,
      "CT_CHP": 0.009,
      "CT_PEAKER": 0.256,
      "ST_CHP": 0.009,
      "ST_GAS": 0.156,
      "import": -1.248
    }
  },
  "direction_check": {
    "abs_import_move_twh": 1.2483511897354127,
    "note": "2022's move must exceed 2021's in absolute MWh (PRECOMMIT §3)"
  },
  "gates": {
    "G1_liveness": {
      "pass": true,
      "detail": "INFO: MISO 2023: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 6305 / max 9364 MW, export mean 1 / max 241 MW; import below the scalar in 8549 h, export in 8760 h"
    },
    "G2_confinement": {
      "pass": true,
      "max_import_violation_mw": 0.00019531250018189894,
      "max_export_violation_mw": 1.52587890625e-05,
      "hours_import_violating": 0,
      "hours_export_violating": 0
    },
    "G3_rail_broken": {
      "pass": true,
      "control_rail_hours": 3,
      "arm_rail_hours": 0
    },
    "G4_not_a_pin": {
      "pass": true,
      "frac_hours_at_99pct_of_envelope": 0.2632420091324201,
      "line": 0.8,
      "distinct_hourly_import_values_arm": 3673,
      "distinct_hourly_import_values_control": 4552
    },
    "G5_non_target": {
      "pass": null,
      "note": "score with scripts/calibration_verdict.py; C2/C6/C8 must not flip",
      "arm_metrics_present": false,
      "arm_legitimacy_present": true
    }
  },
  "verdict": "no STOP fired"
}
```

## G-1 marker line (verbatim, `/tmp/solve2023.log:41`)

```
INFO: MISO 2023: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 6305 / max 9364 MW, export mean 1 / max 241 MW; import below the scalar in 8549 h, export in 8760 h
```

## Container preflight and memory peak (verbatim)

```
INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a096d3-848b-774a-b4c4-9dc8cdb3dc23/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 10 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 10.0 = 23.3 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 23.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
INFO: memory peak: cgroup_peak_rss_gib=13.34, cgroup_peak_rss_plus_swap_gib=18.91, process_vmhwm_gib=13.32, process_vmswap_now_gib=0.06
```

The 24 GiB-target warning fired and was **not** fatal: the peak landed at
18.91 GiB rss+swap inside the 23.3 GiB provisioned, exactly the miso-254
shard A precedent. Free disk at launch was 17 GiB (HARD STOP 3 floor is
13 GiB), and the runner sized its own 10 GiB swapfile — no memory env var,
no hand-provisioned swap, no `--no-container-preflight`.

## Phase timing (verbatim)

```
INFO: year 2023 phase timing: data_prep=36.9s solve_p0=360.7s markup=16.7s solve_p1=182.3s results_write=43.0s total=639.6s (markup: setup=0.0s p0_post=7.4s markup=0.6s seam=0.5s p1_post=7.9s tail=0.0s other=0.2s) (results_write: state=1.1s frames=4.0s parquet=3.9s bench=8.3s sidecars=25.6s)
```

## Did any STOP fire?

No STOP fired. All four hard stops passed before the solve: HEAD was the pinned
SHA; both test files passed (14 tests); the control bundle carried `meta.json`
and `hourly/class_hourly_2023.parquet`; and free disk read 17 GiB against the
13 GiB floor. The solve ran the command unmodified, finished in 639.6 s of
in-year phase time, and HARD STOP 4 passed — the arm fired, with the marker
naming the `declared scalar 8700 MW`. The committed gate scorer then returned
`"verdict": "no STOP fired"`, with G-1 through G-4 all `true`. G-5 is
`pass: null` by construction, not by failure: the scorer defers the non-target
criterion check to `scripts/calibration_verdict.py` and reports
`arm_metrics_present: false` because a `replay_keeper` bundle writes
`legitimacy_diagnostics.json` but no `metrics.json` — scoring it is the
parent's job, not this shard's. The one adverse line in the solve log is the
replayed bundle's `legitimacy diagnostics gate FAIL`, which the runner emits
after writing the artifact; it is reported here and left to the parent, since
repairing or re-running is outside this shard's scope.
