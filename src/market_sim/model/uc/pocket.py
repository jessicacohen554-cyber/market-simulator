"""VLR load-pocket commitment requirement for the MILP UC window.

``ScenarioConfig.vlr_pocket_commitment`` (lane UC-MISO-VLR, owner ruling
2026-10-15 r13 Q1 = "A"): every window hour, each load-pocket group of the
ISO's ``vlr-pocket-groups`` partition must hold at least
``constants.VLR_GROUP_MIN_COMMITTED_UNITS`` units committed among its plants'
commitment clusters. This module maps the source's units onto the
``(plant_code, family)`` clusters of :class:`~market_sim.model.uc.params.UcClusterParams`
and hands the window builder arrays only (rule 6); the rows themselves are
built in :meth:`~market_sim.model.uc.window.UcWindowModel._add_pocket_rows`.

Mapping rules (FINDING-ucmiso-vlr-phase0-2026-10-15 section 3):

* a group's cluster set is every cluster whose ``(plant_code, family)`` one of
  its units carries; a unit with no cluster in the fleet (retired, or absent
  from the model fleet) adds nothing, and a group with no cluster at all is
  recorded in :attr:`PocketRequirement.unmatched` and builds no row;
* groups that land on the SAME cluster set add their requirements (the
  source's groups are disjoint unit sets, so "one unit of each" is "that many
  units of the shared clusters" when the model cannot tell the units apart);
* groups whose cluster sets overlap without being equal are refused (no
  disjoint reading of the requirement exists);
* a requirement never exceeds the set's physical unit count.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_sim.model.uc.params import UcClusterParams


@dataclass(frozen=True)
class PocketRequirement:
    """Struct-of-arrays pocket requirement (one entry per merged cluster set).

    Attributes:
        set_ptr: ``(n_sets + 1,)`` CSR-style offsets into :attr:`set_clusters`.
        set_clusters: cluster indices (``UcClusterParams`` order) of every set.
        n_req: ``(n_sets,)`` units required committed in each set, per hour.
        labels: ``(n_sets,)`` ``"pocket:group[+group]"`` names for the log.
        unmatched: ``"pocket:group"`` names of groups with no fleet cluster.
    """

    set_ptr: np.ndarray
    set_clusters: np.ndarray
    n_req: np.ndarray
    labels: tuple[str, ...]
    unmatched: tuple[str, ...]

    @property
    def n_sets(self) -> int:
        """Number of merged cluster sets (rows per window hour)."""
        return int(self.n_req.size)

    def clusters_of(self, s: int) -> np.ndarray:
        """Cluster indices of set ``s``."""
        return self.set_clusters[self.set_ptr[s] : self.set_ptr[s + 1]]

    def log_rows(self, params: UcClusterParams) -> list[dict]:
        """Per-set rows for ``uc_solve_log`` (``engine.vlr_pocket.sets``)."""
        return [
            {
                "label": self.labels[s],
                "n_req": int(self.n_req[s]),
                "clusters": [
                    {
                        "plant_code": int(params.plant_code[c]),
                        "family": str(params.family[c]),
                        "n": int(params.n_units[c]),
                        "integer": bool(params.integer[c]),
                    }
                    for c in self.clusters_of(s)
                ],
            }
            for s in range(self.n_sets)
        ]


def build_pocket_requirement(
    params: UcClusterParams, groups: pd.DataFrame, min_units: int
) -> PocketRequirement:
    """Map the ``vlr-pocket-groups`` frame onto the cluster sets the window constrains.

    Args:
        params: The stage's cluster parameters.
        groups: The ISO's ``vlr-pocket-groups`` partition (one row per unit).
        min_units: Units required per source group
            (``constants.VLR_GROUP_MIN_COMMITTED_UNITS``).
    """
    if min_units < 0:
        raise ValueError(f"min_units must be >= 0 (got {min_units})")
    key_to_c = {
        (int(pc), str(fm)): c
        for c, (pc, fm) in enumerate(zip(params.plant_code, params.family))
        if int(pc) > 0
    }
    merged: dict[tuple[int, ...], list] = {}
    unmatched: list[str] = []
    for (pocket, group), rows in groups.groupby(["pocket", "group_id"], sort=True):
        clusters = sorted(
            {
                key_to_c[(int(pc), str(fm))]
                for pc, fm in zip(rows["plant_code"], rows["uc_family"])
                if (int(pc), str(fm)) in key_to_c
            }
        )
        name = f"{pocket}:{group}"
        if not clusters:
            unmatched.append(name)
            continue
        entry = merged.setdefault(tuple(clusters), [0, []])
        entry[0] += int(min_units)
        entry[1].append(name)
    sets = sorted(merged)
    for i, a in enumerate(sets):
        for b in sets[i + 1 :]:
            if set(a) & set(b):
                raise ValueError(
                    f"VLR groups {merged[a][1]} and {merged[b][1]} share clusters "
                    "without sharing the same cluster set; no disjoint reading "
                    "of the per-group requirement exists"
                )
    n_req = np.array(
        [min(merged[s][0], int(params.n_units[list(s)].sum())) for s in sets],
        dtype=int,
    )
    lengths = np.array([len(s) for s in sets], dtype=int)
    set_ptr = np.concatenate([[0], np.cumsum(lengths)]).astype(int)
    set_clusters = (
        np.concatenate([np.asarray(s, dtype=int) for s in sets])
        if sets
        else np.zeros(0, dtype=int)
    )
    labels = tuple("+".join(merged[s][1]) for s in sets)
    return PocketRequirement(
        set_ptr=set_ptr,
        set_clusters=set_clusters,
        n_req=n_req,
        labels=labels,
        unmatched=tuple(unmatched),
    )
