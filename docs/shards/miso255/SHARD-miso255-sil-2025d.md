# SHARD miso255-sil-2025 — MISO 2025, `miso_import_sil_measured_envelope` arm

Shard id `miso255-sil-2025D`. Pin `d0fec486fa2218afc55dbd2eb377bc2570e61699`.
Bundle (gitignored, on local disk only): `results/calibration/miso255_sil_2025/`
Control (committed): `results/calibration/miso_fuelvintage_A/`

Solve command, run unmodified:

```
uv run python scripts/replay_keeper.py results/calibration/miso_fuelvintage_A \
  --years 2025 --out-dir results/calibration/miso255_sil_2025 \
  --set miso_import_sil_measured_envelope=true \
  --note "miso-255 SIL measured-envelope arm 2025"
```

## G-1 marker (HARD STOP 4)

```
INFO: MISO 2025: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 4229 / max 8649 MW, export mean 629 / max 3015 MW; import below the scalar in 8760 h, export in 8760 h
```

## Container preflight

```
INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a096d4-4766-732e-84f3-45ba1774f9a7/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 10 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 10.0 = 23.3 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 23.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
```

## Memory peak

```
INFO: memory peak: cgroup_peak_rss_gib=13.34, cgroup_peak_rss_plus_swap_gib=18.80, process_vmhwm_gib=13.31, process_vmswap_now_gib=0.07
```

## Phase timing

```
INFO: year 2025 phase timing: data_prep=38.6s solve_p0=446.4s markup=17.7s solve_p1=188.6s results_write=49.9s total=741.1s (markup: setup=0.0s p0_post=7.7s markup=0.6s seam=0.7s p1_post=8.4s tail=0.0s other=0.3s) (results_write: state=1.0s frames=5.5s parquet=4.0s bench=9.6s sidecars=29.6s)
```

## Gate-scorer JSON

Produced by the committed scorer, unmodified:

```
uv run python scripts/probes/_miso255_screen_gates.py \
  --arm results/calibration/miso255_sil_2025 \
  --control results/calibration/miso_fuelvintage_A \
  --year 2025 --log /tmp/solve2025.log --out /tmp/gates2025.json
```

```json
{
  "year": 2025,
  "arm": "results/calibration/miso255_sil_2025",
  "control": "results/calibration/miso_fuelvintage_A",
  "G6_reported": {
    "import_twh_control": 20.34865217470169,
    "import_twh_arm": 19.015770370781897,
    "import_twh_meter": 18.951940463523233,
    "import_env_ceiling_twh": 37.0488826,
    "gas_twh_control": 200.7782986164093,
    "gas_twh_arm": 201.80200362205505,
    "cc_regular_twh_control": 136.2495574951172,
    "cc_regular_twh_arm": 136.7609405517578,
    "class_delta_twh": {
      "CC_CHP": 0.148,
      "CC_REGULAR": 0.511,
      "COAL_BIT": 0.1,
      "COAL_PRB": 0.192,
      "CT_CHP": 0.01,
      "CT_PEAKER": 0.277,
      "ST_CHP": 0.007,
      "ST_GAS": 0.07,
      "import": -1.333
    }
  },
  "direction_check": {
    "abs_import_move_twh": 1.3328818039197923,
    "note": "2022's move must exceed 2021's in absolute MWh (PRECOMMIT \u00a73)"
  },
  "gates": {
    "G1_liveness": {
      "pass": true,
      "detail": "INFO: MISO 2025: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 4229 / max 8649 MW, export mean 629 / max 3015 MW; import below the scalar in 8760 h, export in 8760 h"
    },
    "G2_confinement": {
      "pass": true,
      "max_import_violation_mw": 0.00019531249927240424,
      "max_export_violation_mw": 3.0517578125e-05,
      "hours_import_violating": 0,
      "hours_export_violating": 0
    },
    "G3_rail_broken": {
      "pass": true,
      "control_rail_hours": 0,
      "arm_rail_hours": 0
    },
    "G4_not_a_pin": {
      "pass": true,
      "frac_hours_at_99pct_of_envelope": 0.1886986301369863,
      "line": 0.8,
      "distinct_hourly_import_values_arm": 3249,
      "distinct_hourly_import_values_control": 4210
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

## Did any STOP fire?

No STOP fired. All four hard stops passed before the solve: HEAD matched the pin
`d0fec486fa2218afc55dbd2eb377bc2570e61699`; the two required test files passed (14 tests); the
control bundle carried both `meta.json` and `hourly/class_hourly_2025.parquet`; and free disk read
17 GiB, above the corrected 13 GiB floor. The preflight emitted a WARNING that ceiling+swap of
23.3 GiB sits below its own 24 GiB target, but it **provisioned its swap successfully** (10 GiB,
the same amount that carried miso-254 shard A), so that warning is advisory and not the
"cannot provision swap" condition that would have been a real stop — and the run bore this out,
peaking at 18.80 GiB rss+swap against 23.3 GiB available. HARD STOP 4 passed: the arm fired, with
the marker naming `declared scalar 8700 MW`. The solve completed in 741.1 s, well inside the
20-minute shard budget, and the gate scorer returned `no STOP fired` with G-1 through G-4 all
passing (G-5 is scored by the parent, not here — the arm bundle carries no `metrics.json` or
`legitimacy_diagnostics.json`). Nothing under `src/` or `scripts/` was edited, no infrastructure
was repaired, and the bundle is left on local disk untouched per rule 31.
