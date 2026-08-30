"""Process-wide topology-variant context (caiso-224).

The base ISO topologies in :mod:`market_sim.config.iso_configs` are built by
scenario-blind factories, and ~40 call sites fetch them with a bare
``get_iso_config(iso)`` (renewables zone shares, hydro budgets, storage
fleets, zonal gas basis, …). A scenario-gated change to the ZONE SET
therefore cannot be threaded per-call without splitting the model's view of
the topology: the LP would run one zone count while the data layer built
another (the caiso-224 recon's largest silent-inconsistency hazard).

Instead, the active variant is set ONCE per solve from the ``ScenarioConfig``
field at the two lanes' existing config seams — the same pattern as
``config.paths.set_eia860_vintage``, which both lanes already call at the
same point — and read by ``get_iso_config`` and the ``zone_assignment``
carve, so every consumer sees the same topology for the whole solve. The
source of truth remains the registered ScenarioConfig field
(``caiso_fsno_subzonal_topology``, cache-key registered — rule 24
[R-REGISTRY]); this module is plumbing, never a knob: nothing here is
settable outside the config seams, and the run's ``run_config.json``
records the field like any other.

Currently the ONLY variant is the CAISO FSNO sub-zonal partition
(PRECOMMIT-caiso224-fsno-arm-2026-08-30.md §1/§3; the caiso-223 P-A'
partition). Default off — the base topology is byte-identical.
"""

from __future__ import annotations

_caiso_fsno_partition: bool = False


def set_caiso_fsno_partition(active: bool) -> None:
    """Arm/disarm the CAISO FSNO sub-zonal partition for this process.

    Called from the per-solve config seams (``scripts/run_calibration.py``
    ``run_year`` and ``runner.py`` ``run_scenario_iso``) with the value of
    ``ScenarioConfig.caiso_fsno_subzonal_topology`` — never from anywhere
    else. Idempotent; set before the first ``get_iso_config``/zone-lookup
    call of the solve so every cached consumer warms under the same variant.
    """
    global _caiso_fsno_partition
    _caiso_fsno_partition = bool(active)


def caiso_fsno_partition_active() -> bool:
    """Return True when the CAISO FSNO sub-zonal partition is armed."""
    return _caiso_fsno_partition
