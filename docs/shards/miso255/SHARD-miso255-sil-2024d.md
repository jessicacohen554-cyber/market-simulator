# SHARD miso255-sil-2024 — MISO 2024, `miso_import_sil_measured_envelope` arm

Shard `miso255-sil-2024D`. Pin `d0fec486fa2218afc55dbd2eb377bc2570e61699`.
Arm bundle: `results/calibration/miso255_sil_2024/` (gitignored, on local disk).
Control: `results/calibration/miso_fuelvintage_A/` (committed; rule 29(b) form 4 — no control solve).

## Gate-scorer JSON

```json
{
  "year": 2024,
  "arm": "results/calibration/miso255_sil_2024",
  "control": "results/calibration/miso_fuelvintage_A",
  "G6_reported": {
    "import_twh_control": 27.5043496252594,
    "import_twh_arm": 26.389417750728608,
    "import_twh_meter": 23.0786135,
    "import_env_ceiling_twh": 40.57397340000001,
    "gas_twh_control": 218.46138048171997,
    "gas_twh_arm": 219.33695697784424,
    "cc_regular_twh_control": 149.17886352539062,
    "cc_regular_twh_arm": 149.5016326904297,
    "class_delta_twh": {
      "CC_CHP": 0.096,
      "CC_REGULAR": 0.323,
      "COAL_BIT": 0.054,
      "COAL_LIGNITE": 0.008,
      "COAL_PRB": 0.164,
      "CT_CHP": 0.009,
      "CT_PEAKER": 0.294,
      "ST_CHP": 0.007,
      "ST_GAS": 0.147,
      "import": -1.115
    }
  },
  "direction_check": {
    "abs_import_move_twh": 1.1149318745307923,
    "note": "2022's move must exceed 2021's in absolute MWh (PRECOMMIT \u00a73)"
  },
  "gates": {
    "G1_liveness": {
      "pass": true,
      "detail": "INFO: MISO 2024: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 4632 / max 8124 MW, export mean 246 / max 2085 MW; import below the scalar in 8760 h, export in 8760 h"
    },
    "G2_confinement": {
      "pass": true,
      "max_import_violation_mw": 0.00019531250018189894,
      "max_export_violation_mw": 2.7465820295446974e-05,
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
      "frac_hours_at_99pct_of_envelope": 0.2271689497716895,
      "line": 0.8,
      "distinct_hourly_import_values_arm": 3852,
      "distinct_hourly_import_values_control": 4822
    },
    "G5_non_target": {
      "pass": null,
      "note": "score with scripts/calibration_verdict.py; C2/C6/C8 must not flip",
      "arm_metrics_present": false,
      "arm_legitimacy_present": true
    }
  },
  "verdict": "no STOP fired"
}```

## Runner log lines

```
INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a096d3-e5b1-7519-b134-09de2b4c4aa4/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 10 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 10.0 = 23.3 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 23.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
INFO: year 2024 phase timing: data_prep=39.5s solve_p0=391.3s markup=17.7s solve_p1=189.6s results_write=49.2s total=687.4s (markup: setup=0.0s p0_post=7.8s markup=0.7s seam=0.5s p1_post=8.2s tail=0.0s other=0.4s) (results_write: state=1.1s frames=5.7s parquet=4.3s bench=11.0s sidecars=27.1s)
INFO: memory peak: cgroup_peak_rss_gib=13.34, cgroup_peak_rss_plus_swap_gib=18.93, process_vmhwm_gib=13.30, process_vmswap_now_gib=0.06
```

## G-1 marker (verbatim)

```
INFO: MISO 2024: aggregate simultaneous-transfer limit REPLACED by the measured coincident boundary envelope -- declared scalar 8700 MW -> import mean 4632 / max 8124 MW, export mean 246 / max 2085 MW; import below the scalar in 8760 h, export in 8760 h
```

## Did any STOP fire?

No STOP fired. All four pre-solve hard stops passed: HEAD matched the pinned SHA
exactly; both gate test files passed (14 tests); the control bundle carried both
`meta.json` and `hourly/class_hourly_2024.parquet`; and free disk was 17 GiB,
above the 13 GiB floor. The container preflight provisioned 10 GiB of swap on its
own, reaching a 23.3 GiB ceiling+swap, and emitted a WARNING that this sits below
its 24 GiB target — that warning is advisory and is not the prompt's stop
condition, which is a preflight that *cannot* provision swap; provisioning
succeeded, and the measured peak of 18.93 GiB rss+swap landed comfortably inside
the 23.3 GiB actually available, matching the known MISO-year precedent. The
solve ran 687.4 s wall (inside the 20-minute shard budget), exited 0, wrote a
complete bundle, and the arm fired — the G-1 marker is present with the declared
scalar 8700 MW. The committed screen-gate scorer returned `"verdict": "no STOP
fired"` with G-1 through G-4 all passing; G-5 is `null` by construction, deferred
to `scripts/calibration_verdict.py` in the parent, and the arm bundle carries
`legitimacy_diagnostics.json` for it.
