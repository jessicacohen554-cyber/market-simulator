"""Read the measured online-gated reserve headroom multiplier ``rho``.

The model's *consumption seam* for
``scripts/data/derive_campd_online_reserve_rho.py`` →
``data/raw/_processed-legacy/campd_online_reserve_rho_{ISO}.csv``, consumed by
the online-gated class-2 branches of
:func:`market_sim.model.reserves.spec._nyiso_design`.

WHAT ``rho`` IS. The online-gated class-2 headroom row
(``model/lp/reserve_rows.py``) reads::

    R[c, z] - rho * sum_{g eligible in z} P[g, t] <= 0

so ``rho`` is the MW of 10-minute deliverable headroom that one MW of on-line
output carries with it. For a gated class this row **replaces** the capability
row ``sum_g P[g] + R[c,z] <= sum_g cap[g]`` rather than joining it, so ``rho``
is the SOLE bound on that class's reserve — which is why it has to be
identified against the operating record rather than at a hand-picked point.

WHY THIS SEAM EXISTS. ``spec.py`` declared ``rho`` as the eligible fleet's own
cap-weighted ``(pmax - pmin) / pmin``. That path is guarded by ``pmin > 0`` and
is **dead code on a binned/tranche fleet**, where must-run rides ``min_gen``
and ``pmin`` is identically zero: on NYISO's keeper only 4 of 851/849/705 LP
rows carry ``pmin > 0`` (the nuclear block, none quick-start eligible), so the
value that decided the mechanism was the literal ``1.0`` fallback in every
year and in BOTH gated branches. Record:
``results/calibration/FINDING-nyiso143-online-rho-unidentified-2026-08-18.md``.

WHICH MEASURED VALUE IS USED, and why (rule 14 ``[R-ACCURATE]``). The artifact
carries the headline plus two sensitivities:

* ``rho`` (**used**) — the aggregate ``sum(head) / sum(P)`` over every online
  unit-hour of the pooled window, ``head = min(HSL - P, ramp10_frac x HSL)``.
  This is the value that makes ``rho * sum P`` reproduce the fleet's MEASURED
  10-minute deliverable headroom over the operating record, on the LP's own
  hourly-average basis.
* ``rho_minload`` — the same fleet evaluated at its measured minimum stable
  load. The direct successor of the declared ``(pmax - pmin) / pmin`` basis,
  10-minute-limited. NOT used: because the gated row is the class's only
  bound, identifying at min load would grant roughly 4x the headroom the
  fleet actually carried in the typical hour.
* ``rho_fullhour`` — restricted to whole-hour operation; reports how much of
  the headline is partial-hour geometry.

The artifact is a committed measured input (it lives under ``data/raw``, not
the gitignored clean tree), so a missing file is a configuration error for a
run that armed a gated family, not a silent degradation: :func:`load_online_rho`
returns ``None`` and the caller falls back to the legacy ``pmin`` path with a
logged warning, exactly as it behaved before this seam existed.

Rule 13 ``[R-MEASURED]`` admissibility: a function of fleet composition and
class ramp physics evaluated over an operating record — it regenerates from the
CAMPD pipeline for any vintage, responds to fleet change (retire steam or add
fast-start capacity and it moves), and reads no price or volume residual. Rule
23 ``[R-FROZEN-DERIVE]``: re-derives only when its source data updates.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass

from market_sim.config.paths import PROCESSED_DIR

logger = logging.getLogger(__name__)

# Band the identified multiplier is clipped to.
#
# OWNER RULING 2026-08-22 (session nyiso-151, rule 22 D-5(b)): the 0.5 FLOOR
# IS DELETED — option A of
# docs/DECISION-CARD-nyiso145-rho-clip-band-2026-08-19.md, taken on the
# card's own recommendation. The floor had no primary citation and no
# physical basis (the true lower bound on 10-minute headroom per MW online
# is zero — a fleet at full load carries none); it was inherited across a
# change of estimand (written for the min-load `(pmax−pmin)/pmin` basis,
# where [0.5, 4.0] brackets f ∈ [0.2, 0.667], then applied to the
# as-operated `Σhead/ΣP` aggregate, which every measured fleet — MISO
# miso_reg_spin 0.1764, NYISO incity_obligation 0.3014, NYISO nyc_spin
# 0.2011 — sits below). Every measured row now solves at its own
# measurement, which is what makes the gated NYISO flags admissible on a
# data-identified coefficient (rule 21 [R-DOF]).
#
# The 4.0 CEILING STAYS: it has a real derivation on the min-load estimand
# (the deepest class turn-down in the model's own tables, NYISO ST_GAS
# f = 0.239, gives ≈ 3.2; f = 0.2 gives exactly 4.0) and is loose-but-
# harmless on the as-operated one.
#
# CROSS-LANE CONSEQUENCE, flagged not executed here (rule 25
# [R-ISO-SCOPE]): MISO's armed `miso_reserve_online_gated` keeper solved at
# the floor (0.5); its future replays now solve at the measurement (0.1764),
# which TIGHTENS its additive coupling row — the MISO lane re-gates on its
# own schedule (docs/calibration-log/governance.md, 2026-08-22 entry).
# History: FINDING-nyiso144-downstate-scarcity-and-rho-2026-08-18.md,
# FINDING-nyiso143-online-rho-unidentified-2026-08-18.md; the MISO
# primary-source leg of the refutation (BPM-002-r25: capability is
# ramp x deploy-time, the only 0.5 a regulation-range CEILING) and the
# ruling's MISO re-gate:
# FINDING-miso177-rho-clip-floor-identification-2026-08-22.md.
RHO_CLIP: tuple[float, float] = (0.0, 4.0)


@dataclass(frozen=True)
class OnlineReserveRho:
    """One family set's measured online-headroom multiplier and its provenance.

    Attributes:
        iso: The ISO the statistic was measured on.
        family_set: The online-gated family set key (e.g. ``incity_obligation``).
        mechanism: The ``ScenarioConfig`` flag that consumes it.
        rho: The headline aggregate ``sum(head)/sum(P)``, pre-clip.
        rho_minload: The min-stable-load sensitivity (reported, never used).
        rho_fullhour: The whole-hour-operation sensitivity (reported).
        online_unit_hours: Online unit-hours the headline was measured over.
        campd_coverage_frac: Metered capability as a fraction of the eligible
            model capacity — below 1.0 the statistic speaks for a subset.
        years: The pooled CAMPD vintage span.
    """

    iso: str
    family_set: str
    mechanism: str
    rho: float
    rho_minload: float
    rho_fullhour: float
    online_unit_hours: int
    campd_coverage_frac: float
    years: str

    @property
    def rho_used(self) -> float:
        """Return the headline multiplier clipped to :data:`RHO_CLIP`."""
        lo, hi = RHO_CLIP
        return min(max(self.rho, lo), hi)


def _artifact_path(iso: str):
    """Return the measured-``rho`` artifact path for *iso*."""
    return PROCESSED_DIR / f"campd_online_reserve_rho_{iso.upper()}.csv"


def load_online_rho(iso: str, family_set: str) -> OnlineReserveRho | None:
    """Return the measured ``rho`` for *iso*/*family_set*, or ``None``.

    ``None`` means the ISO has no artifact yet or the artifact carries no row
    for this family set — the caller keeps its legacy ``(pmax-pmin)/pmin``
    identification. Never raises on a missing file: an ISO that has not had the
    derivation run is a normal state (the derivation is per-ISO and additive),
    and every gated family is behind a default-off flag.

    Args:
        iso: The ISO name.
        family_set: The online-gated family set key, matching the
            ``family_set`` column written by
            ``scripts/data/derive_campd_online_reserve_rho.py``.
    """
    path = _artifact_path(iso)
    if not path.exists():
        logger.warning(
            "no measured online-reserve rho artifact for %s (%s) — the gated "
            "reserve class falls back to the (pmax-pmin)/pmin identification",
            iso,
            path.name,
        )
        return None
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("family_set") != family_set:
                continue
            return OnlineReserveRho(
                iso=row["iso"],
                family_set=row["family_set"],
                mechanism=row["mechanism"],
                rho=float(row["rho"]),
                rho_minload=float(row["rho_minload"]),
                rho_fullhour=float(row["rho_fullhour"]),
                online_unit_hours=int(row["online_unit_hours"]),
                campd_coverage_frac=float(row["campd_coverage_frac"]),
                years=row["years"],
            )
    logger.warning(
        "measured online-reserve rho artifact for %s carries no '%s' row — "
        "falling back to the (pmax-pmin)/pmin identification",
        iso,
        family_set,
    )
    return None
