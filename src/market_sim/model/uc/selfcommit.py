"""Self-commitment requirement for EIA-860 Sector-1 ST_GAS in the MILP UC window.

``ScenarioConfig.spp_selfcommit_sector1_st_gas`` (lane UC-SPP-SELFCOMMIT, owner
ruling R24; ``docs/records/spp/DESIGN-uc-spp-selfcommit-2026-10-19.md``): a
vertically integrated utility's gas steamer (EIA-860 Sector 1) holds at least
``constants.UC_SELFCOMMIT_MIN_UNITS_ONLINE`` unit online in each hour of its
measured committed window. The window is the plant's pooled CEMS
``online_frac`` (``thermal_tranches_<ISO>.csv``, the frozen
``derive_thermal_tranches.py`` statistic) times the year's hours, placed as
whole operating days ranked by the day's mean system load — the same signal,
ordering statistic and grain helpers (``data/fleet/arrays.py::
_commitment_day_order`` / ``_mustrun_window_hours``) the per-plant ST_GAS
floor (``st_gas_mustrun_per_plant``, SPP-64 / spp-27) places its window with.
It REPLACES that floor (rule 19): the floor forces MW in P1, this requirement
forces commitment state in the UC and the unit dispatches freely from its
measured min-load (``UcClusterParams.mlf``, the output-coupling row) up.

This module turns the inputs into arrays only (rule 6); the rows are built in
:meth:`~market_sim.model.uc.window.UcWindowModel._add_selfcommit_rows`.

Membership (self-targeting by measurement, rule 18): an integer ``st_gas``
cluster of a plant whose EIA-860 Sector is in the eligible set and whose
artifact row publishes a positive ``online_frac``. Every other ``st_gas``
cluster is recorded in :attr:`SelfCommitRequirement.skipped` with the reason.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

import numpy as np

from market_sim.data.fleet.arrays import _commitment_day_order, _mustrun_window_hours
from market_sim.model.uc.params import UcClusterParams

#: The ``uc-params`` family token of the gas steam clusters.
ST_GAS_FAMILY: str = "st_gas"

#: The thermal-tranche artifact group the ``online_frac`` row is keyed on.
ST_GAS_GROUP: str = "ST_GAS"


@dataclass(frozen=True)
class SelfCommitRequirement:
    """Struct-of-arrays self-commitment requirement (one entry per cluster).

    Attributes:
        clusters: ``(n_sel,)`` cluster indices (``UcClusterParams`` order).
        plant_code: ``(n_sel,)`` EIA plant code of each cluster.
        online_frac: ``(n_sel,)`` the pooled CEMS synchronization share.
        required: ``(n_sel, T)`` bool, the hours each cluster must hold
            :attr:`min_units` online (before the window's availability relief).
        min_units: Units required online in a required hour.
        skipped: ``"plant:reason"`` for every ``st_gas`` cluster left out.
    """

    clusters: np.ndarray
    plant_code: np.ndarray
    online_frac: np.ndarray
    required: np.ndarray
    min_units: int
    skipped: tuple[str, ...]

    @property
    def n_sel(self) -> int:
        """Number of clusters carrying the requirement."""
        return int(self.clusters.size)

    def sliced(self, t0: int, t1: int) -> "SelfCommitRequirement":
        """The requirement on the window ``[t0, t1)`` (``required`` sliced)."""
        return dataclasses.replace(self, required=self.required[:, t0:t1])

    def log_rows(self, params: UcClusterParams) -> list[dict]:
        """Per-cluster rows for ``uc_solve_log`` (``engine.selfcommit.clusters``)."""
        T = int(self.required.shape[1]) if self.required.ndim == 2 else 0
        return [
            {
                "plant_code": int(self.plant_code[i]),
                "n": int(params.n_units[c]),
                "mlf": float(params.mlf[c]),
                "online_frac": float(self.online_frac[i]),
                "required_hours": int(self.required[i].sum()),
                "hours": T,
            }
            for i, c in enumerate(self.clusters)
        ]


def build_selfcommit_requirement(
    params: UcClusterParams,
    sectors: dict[int, int],
    online_frac: dict[tuple[int, str], float],
    sys_load: np.ndarray,
    eligible_sectors: tuple[int, ...],
    min_units: int,
) -> SelfCommitRequirement:
    """Select the self-committed ST_GAS clusters and place each one's window.

    Args:
        params: The stage's cluster parameters (post budget-pin demotion, so a
            demoted cluster, which carries no ``u``, is skipped).
        sectors: ``{plant_code: EIA-860 Sector}`` at the run's vintage.
        online_frac: ``{(plant_code, group): online_frac}`` from the ISO's
            thermal-tranche artifact (pooled multi-year CEMS).
        sys_load: ``(T,)`` the year's system load (the window ranking signal).
        eligible_sectors: Sector codes that self-commit
            (``constants.UC_SELFCOMMIT_EIA860_SECTORS``).
        min_units: Units held online in a required hour
            (``constants.UC_SELFCOMMIT_MIN_UNITS_ONLINE``).
    """
    if min_units < 1:
        raise ValueError(f"min_units must be >= 1 (got {min_units})")
    load = np.asarray(sys_load, dtype=float)
    T = int(load.size)
    load_rank = np.argsort(-load, kind="stable")
    day_order = _commitment_day_order(load, T)
    sel: list[int] = []
    plants: list[int] = []
    fracs: list[float] = []
    masks: list[np.ndarray] = []
    skipped: list[str] = []
    for c in range(params.n_clusters):
        if str(params.family[c]) != ST_GAS_FAMILY:
            continue
        pc = int(params.plant_code[c])
        if pc <= 0:
            skipped.append(f"{pc}:legacy bin (no plant identity)")
            continue
        sector = sectors.get(pc)
        if sector not in eligible_sectors:
            skipped.append(f"{pc}:EIA-860 sector {sector}")
            continue
        f = float(online_frac.get((pc, ST_GAS_GROUP), 0.0))
        if not f > 0.0:
            skipped.append(f"{pc}:no measured online_frac")
            continue
        if not bool(params.integer[c]):
            skipped.append(f"{pc}:not an integer cluster")
            continue
        mask = np.zeros(T, dtype=bool)
        if f >= 1.0:
            mask[:] = True
        else:
            k = int(round(f * T))
            if k > 0:
                mask[_mustrun_window_hours(load_rank, day_order, k, True)] = True
        sel.append(c)
        plants.append(pc)
        fracs.append(min(f, 1.0))
        masks.append(mask)
    return SelfCommitRequirement(
        clusters=np.asarray(sel, dtype=int),
        plant_code=np.asarray(plants, dtype=int),
        online_frac=np.asarray(fracs, dtype=float),
        required=np.vstack(masks) if masks else np.zeros((0, T), dtype=bool),
        min_units=int(min_units),
        skipped=tuple(skipped),
    )
