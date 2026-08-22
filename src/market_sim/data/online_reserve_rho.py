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

# Band the identified multiplier is clipped to, carried over UNCHANGED from the
# legacy pmin path in model/reserves/spec.py so this seam cannot be read as
# re-banding the coefficient while it re-identifies it.
#
# HONEST STATUS, because it is now load-bearing: the band has NO primary
# citation anywhere in the repo — the two call sites described it only as "the
# same [0.5, 4.0] physical band the path-A family uses", which is
# self-referential. It never mattered before, because the legacy path was dead
# code on a binned fleet and the fallback 1.0 sits inside the band.
#
# It matters now: BOTH measured NYISO values fall BELOW the 0.5 floor
# (incity_obligation 0.3014, nyc_spin 0.2011), so :attr:`OnlineReserveRho.rho_used`
# returns the FLOOR, not the measurement. A run that arms a gated family today
# is therefore still deciding its only reserve bound with a number chosen by an
# uncited guardrail rather than by data — the same rule 21 [R-DOF] defect the
# measurement was meant to close, moved one level out. Resolving the band is an
# owner call (rule 22 D-5(b)), not a session's; until it is resolved, neither
# gated NYISO flag is admissible in a keeper. Record:
# results/calibration/FINDING-nyiso144-downstate-scarcity-and-rho-2026-08-18.md
#
# miso-177 (2026-08-22) completed the identification hunt for the MISO leg of
# that escalation: the 0.5 floor is REFUTED as a citable parameter — MISO's
# own BPM-002-r25 limits per-resource reserve by ramp x deploy-time
# (§4.2.1.46–47), its only capability-role 0.5 is the §4.2.1.37 CEILING on
# the regulation range, and the physical lower bound of headroom-per-MW-online
# is zero. The 4.0 CEILING keeps its (1−f)/f min-load derivation (decision
# card §3) and is not disturbed. The band itself is UNCHANGED here — it
# remains the owner's nyiso-145 decision card — but MISO's gated consumption
# may bypass the refuted floor via ScenarioConfig.miso_online_rho_no_floor
# (:attr:`OnlineReserveRho.rho_used_no_floor`), scoped so no other ISO moves
# (rule 25). Record:
# results/calibration/FINDING-miso177-rho-clip-floor-identification-2026-08-22.md
RHO_CLIP: tuple[float, float] = (0.5, 4.0)


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

    @property
    def rho_used_no_floor(self) -> float:
        """Return the headline multiplier bounded by the cited ceiling alone.

        The measured as-operated statistic consumed as measured: the 0.5 floor
        — refuted as a citable parameter on MISO's primary record
        (FINDING-miso177-rho-clip-floor-identification-2026-08-22.md; the
        physical lower bound of headroom-per-MW-online is zero) — is not
        applied; the 4.0 ceiling keeps its ``(1−f)/f`` min-load derivation and
        cannot bind on any as-operated measurement. Consumed only where a
        ``ScenarioConfig`` gate selects it (``miso_online_rho_no_floor``);
        :attr:`rho_used` and the shared :data:`RHO_CLIP` band are untouched.
        """
        return min(self.rho, RHO_CLIP[1])


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
