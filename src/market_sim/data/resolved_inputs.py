"""What the solve's disposable inputs ACTUALLY resolved to — recorded, not assumed.

The companion to :mod:`market_sim.data.input_completeness`. That module answers
"is the data the armed flag needs on disk?" and refuses the solve when it is
not; this one answers the question the committed artifacts could never answer
afterwards: **which value did the LP actually solve against?**

caiso-188 (`results/calibration/FINDING-caiso188-import-tranche-dof-2026-08-09.md`
§4/§6) measured why that second question matters. ``capacity_deliverability_
limits: true`` resolves the published CAISO MIC through
``data/clean/capacity-deliverability/`` — derived, disposable, gitignored, and
built by no solve. Absent, ``import_limit_by_area`` returns nothing,
``_seam_mw`` is falsy, ``apply_deliverability_seam_limit`` is never called and
the LP keeps the baked 7,500 MW ``WECC_import_simultaneous`` fitted scalar —
while ``run_config.json`` still records the flag as ``True``. Every CAISO
bundle from caiso-175 onward, the designated keeper included, pinned total net
import at exactly 7,500.0 MW in 456-905 h/yr that way, and **nothing committed
distinguished those bundles from ones that solved on the published MIC**. The
FINDING names the durable fix in as many words: *"persist the resolved seam cap
into run_config.json"*. This module is that fix.

Two halves, and the split is deliberate:

* **Recorded at resolution time.** :func:`record_seam_resolution` is called by
  ``model.interchange.spec.apply_interchange_topology`` — the one place the
  seam cap is decided — so what lands in ``run_config.json`` is the value the
  LP was handed, not a re-derivation that could drift from it. A re-derivation
  is exactly the failure class this session exists to close (caiso-188 §7 item
  5: *check the DATA the gate resolves through*).
* **Read at record time.** The hydro-plant-modes and CAMPD-extract facts are
  static disk state for the life of a run, so :func:`resolved_inputs_block`
  reads them directly when the record is written. No recorder needed, and no
  way for them to go stale.

**This module can never change a solve.** It holds no ScenarioConfig field, no
threshold and no tunable; :func:`resolve_seam_import_cap` is a pure function of
(config, iso, year, iso_config) and the recorder is write-only output state.
Rule 24 ``[R-REGISTRY]`` is about channels that can *decide* a limit — this one
only writes down the decision someone else made.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "SeamCapResolution",
    "baked_seam_cap",
    "record_seam_resolution",
    "recorded_seam_resolutions",
    "reset_recorded",
    "resolve_seam_import_cap",
    "resolved_inputs_block",
]

#: ``resolved_inputs`` payload version. Bump on a BREAKING shape change only —
#: adding a key is additive and does not move it.
SCHEMA_VERSION = 1

#: Largest file this module will hash inline. The CAMPD per-ISO unit-outage
#: extracts are ~0.5 MB, so the cap only ever trips on something unexpected;
#: past it the record keeps size + path and says the sha was skipped, rather
#: than making a solve wait on a hash it never asked for.
_MAX_SHA_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True)
class SeamCapResolution:
    """The import-seam cap one (iso, year) resolved to, and where it came from.

    Attributes:
        iso: Model ISO name.
        year: Solve year whose delivery year was resolved.
        flag_armed: Whether ``capacity_deliverability_limits`` was on.
        cap_mw: The seam cap the LP solves against, MW. ``None`` when the ISO
            carries no simultaneous-import limit at all.
        source: How ``cap_mw`` was arrived at — one of ``"mic_partition"``
            (the published per-area import limits resolved and were applied),
            ``"baked_fallback"`` (the flag was ARMED but the partition did not
            resolve, so the baked fitted scalar governs — the caiso-188
            defect), or ``"flag_off"`` (the mechanism was never armed, so the
            baked value is the intended, declared limit).
        delivery_year: The RA delivery-year label Part A resolved for.
        season: The RA season label Part A resolved for.
        import_zone: The model zone the seam limit lands on.
    """

    iso: str
    year: int
    flag_armed: bool
    cap_mw: float | None
    source: str
    delivery_year: str | None
    season: str | None
    import_zone: str | None


#: (iso, year) -> the resolution ``apply_interchange_topology`` performed. A
#: write-only OUTPUT record; nothing reads it to decide anything.
_RECORDED: dict[tuple[str, int], SeamCapResolution] = {}


def reset_recorded() -> None:
    """Drop every recorded seam resolution (test isolation / a fresh run)."""
    _RECORDED.clear()


def record_seam_resolution(resolution: SeamCapResolution) -> None:
    """Record what one (iso, year)'s seam cap resolved to.

    Keyed by ``(iso, year)`` so a multi-year bundle records every year and a
    re-solve of the same year overwrites rather than accumulates.
    """
    _RECORDED[(resolution.iso.upper(), int(resolution.year))] = resolution


def recorded_seam_resolutions() -> dict[tuple[str, int], SeamCapResolution]:
    """Return a copy of every seam resolution recorded so far."""
    return dict(_RECORDED)


def baked_seam_cap(iso_config, iso: str) -> float | None:
    """Return the baked simultaneous-import cap on ``iso_config``, MW.

    The interface limit whose links all originate at the ISO's import zone —
    for CAISO the ``WECC_import_simultaneous`` scalar that governs whenever
    Part A does not resolve. ``None`` when the topology carries no such limit.
    """
    from market_sim.model.interchange.spec import IMPORT_ZONE

    import_zone = IMPORT_ZONE.get(iso)
    if import_zone is None:
        return None
    return next(
        (
            lim.cap_mw
            for lim in iso_config.interface_limits
            if lim.links and all(pair[0] == import_zone for pair in lim.links)
        ),
        None,
    )


def resolve_seam_import_cap(config, iso: str, year: int, iso_config):
    """Resolve the import-seam cap for one (iso, year) — THE single derivation.

    ``model.interchange.spec.apply_interchange_topology`` resolves the seam
    through this function and then applies the result, so the value recorded
    into ``run_config.json`` and the value the LP is handed cannot disagree.
    Statically pinned by
    ``tests/unit/data/test_resolved_inputs.py::TestSpecResolvesThroughHelper``.

    Args:
        config: The resolved ``ScenarioConfig`` for the run.
        iso: Model ISO name.
        year: Solve year (selects the RA delivery year).
        iso_config: The ISO topology, import node already extended, BEFORE the
            deliverability seam limit is applied.

    Returns:
        SeamCapResolution: The cap, its provenance, and the RA coordinates it
        was looked up under.
    """
    from market_sim.model.interchange.spec import IMPORT_ZONE

    import_zone = IMPORT_ZONE.get(iso)
    baked = baked_seam_cap(iso_config, iso)

    if not getattr(config, "capacity_deliverability_limits", False):
        return SeamCapResolution(
            iso=iso,
            year=int(year),
            flag_armed=False,
            cap_mw=baked,
            source="flag_off",
            delivery_year=None,
            season=None,
            import_zone=import_zone,
        )

    from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
    from market_sim.data import capacity_deliverability as capdel

    delivery_year = capdel.resolve_delivery_year(iso, year)
    season = capdel.resolve_season(iso)
    imp_area = capdel.import_limit_by_area(iso, delivery_year, season)
    imp_types = capdel.area_types_by_area(iso, delivery_year, season, "import_limit")
    imp_by_zone, _ = aggregate_by_zone(iso, imp_area, imp_types)
    seam_mw = imp_by_zone.get(import_zone) if import_zone else None

    # Truthiness, not ``is not None`` — mirrors the pre-caiso-190 branch in
    # apply_interchange_topology exactly, so a 0.0 keeps falling through to the
    # baked cap the way it always did.
    if seam_mw:
        return SeamCapResolution(
            iso=iso,
            year=int(year),
            flag_armed=True,
            cap_mw=float(seam_mw),
            source="mic_partition",
            delivery_year=delivery_year,
            season=season,
            import_zone=import_zone,
        )
    return SeamCapResolution(
        iso=iso,
        year=int(year),
        flag_armed=True,
        cap_mw=baked,
        source="baked_fallback",
        delivery_year=delivery_year,
        season=season,
        import_zone=import_zone,
    )


def _sha256(path: Path) -> str | None:
    """Return the hex sha256 of ``path``, or ``None`` when it is not hashable."""
    try:
        if path.stat().st_size > _MAX_SHA_BYTES:
            return None
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:  # pragma: no cover - unreadable file is recorded as absent
        return None


def _hydro_plant_modes_block(config, iso: str) -> dict[str, Any]:
    """Presence + classified-plant count for the ``hydro-plant-modes`` partition.

    caiso-188 §6: the keeper arms ``hydro_ror_split`` and the classifier
    returns ``None``, so the LP is unchanged and *nothing committed says so*.
    The count is what makes the engagement checkable from the bundle alone.
    """
    armed = bool(getattr(config, "hydro_ror_split", False))
    block: dict[str, Any] = {
        "flag_armed": armed,
        "partition_present": None,
        "classified_plants": None,
        "shapeable_plants": None,
    }
    try:
        from market_sim.data.hydro_modes import load_hydro_shapeable

        modes = load_hydro_shapeable(iso)
    except Exception:  # pragma: no cover - a probe never breaks the record
        logger.warning("resolved_inputs: hydro-plant-modes probe failed", exc_info=True)
        return block
    block["partition_present"] = modes is not None
    if modes is not None:
        block["classified_plants"] = len(modes)
        block["shapeable_plants"] = sum(1 for v in modes.values() if v)
    return block


def _thermal_tranche_block(config, iso: str) -> dict[str, Any]:
    """Identity of the CAMPD thermal-tranche artifact the fleet builder reads.

    The sibling of :func:`_campd_unit_outages_block`, and added for the same
    reason (nyiso-176): the tranche artifact is a COMMITTED measured input under
    rule 13 ``[R-MEASURED]`` that sets per-plant committed / must-run / peaking
    shares and the CHP p-min floors, and a bundle that cannot name the bytes it
    consumed cannot be reproduced from its own record. Resolved WITH the
    ``campd_per_unit_attribution`` gate, so an armed run records the
    ``-perunit-`` companion it consumed rather than the incumbent it did not.

    ``armed`` is False only where the ISO has no artifact at all (ERCOT runs the
    CAMPD bin sheet instead), since the per-plant loaders are self-targeting: a
    plant absent from the artifact falls back to its group default.
    """
    block: dict[str, Any] = {
        "armed": None,
        "path": None,
        "present": None,
        "sha256": None,
        "bytes": None,
    }
    try:
        from market_sim.config.paths import REPO_ROOT
        from market_sim.data.fleet.campd_bins import thermal_tranche_csv_for_iso

        path = Path(
            thermal_tranche_csv_for_iso(
                iso,
                bool(getattr(config, "campd_per_unit_attribution", False)),
                bool(getattr(config, "campd_outage_merit_order_guard", False)),
            )
        )
    except Exception:  # pragma: no cover - a probe never breaks the record
        logger.warning("resolved_inputs: thermal-tranche probe failed", exc_info=True)
        return block
    try:
        block["path"] = str(path.relative_to(REPO_ROOT))
    except ValueError:
        block["path"] = str(path)
    block["present"] = path.exists()
    block["armed"] = path.exists()
    if block["present"]:
        block["bytes"] = path.stat().st_size
        block["sha256"] = _sha256(path)
    return block


def _campd_unit_outages_block(config, iso: str) -> dict[str, Any]:
    """Identity of the CAMPD unit-outage extract the overlay reads.

    Unlike the two clean partitions this extract is COMMITTED under
    ``data/raw``, so absence is an environment condition (a sparse checkout)
    rather than the caiso-157 "no solve builds it" class. Its sha is recorded
    all the same: the overlay is a measured input under rule 13
    ``[R-MEASURED]``, and a bundle that cannot name the bytes it consumed
    cannot be reproduced from its own record.

    The path is resolved WITH the routing gates
    (``unit_outage_mixed_gas_routing``, ``campd_per_unit_attribution``), so an
    armed run records the companion it consumed rather than the incumbent it
    did not.
    """
    armed = str(getattr(config, "outage_source", "") or "").lower() == "historic"
    block: dict[str, Any] = {
        "armed": armed,
        "path": None,
        "present": None,
        "sha256": None,
        "bytes": None,
    }
    try:
        from market_sim.config.paths import REPO_ROOT
        from market_sim.data.outages import unit_outage_csv_for_iso

        # Record the path the overlay ACTUALLY reads, gates included
        # (nyiso-176). Without the gates this block names the incumbent extract
        # for a run that consumed a '-unitroute-' or '-perunit-' companion —
        # a bundle claiming an input it did not use, which is the exact
        # reproducibility failure this record exists to prevent.
        path = Path(
            unit_outage_csv_for_iso(
                iso,
                bool(getattr(config, "unit_outage_mixed_gas_routing", False)),
                bool(getattr(config, "campd_per_unit_attribution", False)),
                bool(getattr(config, "campd_outage_merit_order_guard", False)),
                # nyiso-229: the grain gate too, for the same reason the three
                # gates above are here -- without it this block names the
                # day-grain extract for a run that consumed the
                # '-perunitmerithour-' companion.
                bool(getattr(config, "unit_outage_window_hour_grain", False)),
                # SOCO-61: the dark-unit-year companion gate, same reason.
                dark_unit_years=bool(
                    getattr(config, "campd_dark_unit_year_windows", False)
                ),
            )
        )
    except Exception:  # pragma: no cover - a probe never breaks the record
        logger.warning("resolved_inputs: CAMPD extract probe failed", exc_info=True)
        return block
    try:
        block["path"] = str(path.relative_to(REPO_ROOT))
    except ValueError:
        block["path"] = str(path)
    block["present"] = path.exists()
    if block["present"]:
        block["bytes"] = path.stat().st_size
        block["sha256"] = _sha256(path)
    return block


def resolved_inputs_block(config, iso: str) -> dict[str, Any]:
    """Assemble the ``resolved_inputs`` block for ``run_config.json``.

    Additive OUTPUT provenance: nothing here is read back to configure a solve,
    so it moves no cache key and adds no ``ScenarioConfig`` field.

    ``seam_import_cap.status`` is ``"unrecorded"`` when no solve in this
    process resolved a seam for ``iso`` — a meta-only writer, or a
    ``--reuse-solved`` bundle whose years were copied rather than solved. That
    is reported honestly rather than back-filled with a re-derivation, because
    a re-derivation done at record time could disagree with what the LP was
    handed, which is the defect class this block exists to close.

    Args:
        config: The resolved ``ScenarioConfig`` recorded for the run.
        iso: Model ISO name.

    Returns:
        The JSON-ready provenance mapping.
    """
    iso_key = iso.upper()
    by_year = {
        str(yr): asdict(res)
        for (recorded_iso, yr), res in sorted(_RECORDED.items(), key=lambda kv: kv[0])
        if recorded_iso == iso_key
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "iso": iso_key,
        "seam_import_cap": {
            "status": "recorded" if by_year else "unrecorded",
            "by_year": by_year,
        },
        "hydro_plant_modes": _hydro_plant_modes_block(config, iso),
        "campd_unit_outages": _campd_unit_outages_block(config, iso),
        "thermal_tranches": _thermal_tranche_block(config, iso),
    }
