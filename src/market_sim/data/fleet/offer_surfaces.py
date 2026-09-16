"""Measured offer-surface markups/markdowns (conditional, midcurve, cleared-share, fast-start, lowcurve).

Split out of ``data/fleet.py`` (11,199 ln) into the ``data/fleet`` package
(refactor-consolidation plan §5 item 8, 2026-07-23) as pure code motion:
every moved body is byte-identical; only this header and the census'd
``_pkg_ns()`` call-site routings are new. The package ``__init__`` re-exports
the full pre-split surface; patch semantics are preserved via
:func:`market_sim.data.fleet.models._pkg_ns`.
"""

from __future__ import annotations

from typing import NamedTuple

import json
import logging
import numpy as np
import pandas as pd

from functools import lru_cache
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.offer_curves import CONDITIONAL_SURFACE_GROUPS
from pathlib import Path
from market_sim.data.fleet.models import FleetArrays, Generator

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")


@lru_cache(maxsize=1)
def _load_ct_offer_surface() -> tuple[tuple[float, float, float], ...]:
    """Load the frozen measured CT/peaker offer-surface regimes.

    Reads ``data/raw/_validation-source/ercot_ct_offer_surface.json`` (produced by
    ``scripts/data/derive_ct_offer_surface.py`` from the 60-Day DAM disclosure) and
    returns its regimes as ``(q_lo, q_hi, offer_level)`` triples. Cached — the
    surface is frozen against residuals (rule 20); a re-derive is a data-update
    commit, not a solve-time knob.
    """
    from market_sim.config import paths

    path = paths.CALIBRATION_DIR / "ercot_ct_offer_surface.json"
    payload = json.loads(path.read_text())
    return tuple(
        (float(lo), float(hi), float(level)) for lo, hi, level in payload["regimes"]
    )


def apply_ercot_ct_offer_surface(
    mc_base: np.ndarray,
    generators: list[Generator],
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> bool:
    """Raise ERCOT CT/peaker econ+peak offers to the measured self-withholding level.

    The G-22 condition-responsive offer surface (filed structural conclusion #1
    of ``docs/FINDING-ercot-priceshape-2026-07.md`` §6; design note
    ``docs/handoffs/ercot-g22-offer-surface-2026-07.md``). In the missed tail
    hours the P1 LP offers every online CT/peaker economic+peak tranche at its
    flat marginal cost ``heat_rate x gas + VOM`` (~$50-150/MWh) — the "phantom
    sub-$200 spare" that caps the energy dual below the scarcity level the real
    market cleared. The real fleet's peakers had already offered themselves to
    the ERCOT cap band (~$1,500/MWh) by those hours: the 60-Day DAM disclosure
    shows the CT/peaker offer at 90% of HSL is cap-band, not heat-rate x gas
    (``scripts/data/derive_ct_offer_surface.py``).

    This posts the **measured** self-withholding offer level on the CT/peaker
    ``econ*``/``peak*`` tranches (the phantom-spare bands; the ``mustrun``/
    ``sync``/``committed`` min-gen scaffolding is untouched), keyed on a
    **net-load percentile** driver. The low regime is inert (level 0), so the LP
    applies ``max(mc, 0) = mc`` and every sub-hinge hour is byte-identical; only
    above the measured hinge — the net-load percentile at which even the peaker
    fleet's lower quartile has crossed to cap-band — is the offer raised. Unlike
    the REJECTED ercot33 static wall this is condition-responsive (inert in the
    ~90% of hours below the hinge, so no broad elevation) and touches only the
    CT/peaker class (no CC/ST peak-band repricing, the channel that moved measured
    volumes through the P0->P1 startup-amortization coupling). Both the trigger
    (net-load) and the level (measured offer) are forward-derivable and respond to
    changed conditions, so the mechanism is admissible in backcast and forecast
    (CLAUDE.md #10/#13); every parameter is measured and frozen (rules 20/26).

    Vectorised (no hour loop, rule 2). Modifies ``mc_base`` in place. Returns
    ``True`` when the surface was applied, ``False`` (byte-identical) when the
    flag is off, the ISO is not ERCOT, or the fleet has no CT/peaker econ/peak
    tranches.

    Args:
        mc_base: The P1 bid-cost matrix ``(n_gen, T)``, mutated in place.
        generators: The dispatch fleet, aligned row-for-row with ``mc_base``.
        net_load_mw: System net-load per hour (``load - wind - solar``), shape
            ``(T,)`` — the same LP-served convention the drag floors use.
        config: Scenario config supplying the enable flag and ISO.
    """
    if not getattr(config, "ercot_ct_offer_surface", False):
        return False
    if config.iso != "ERCOT":
        return False
    # The phantom-spare bands: CT_PEAKER economic (``econ``/``econc00``..) and
    # peak (``peak``/``peak2``..) tranches. The min-gen scaffolding
    # (``mustrun``/``sync``/``committed``) is commitment structure, never repriced.
    rows = [
        g
        for g, gen in enumerate(generators)
        if gen.plant_group == "CT_PEAKER"
        and (
            gen.unit_id.rpartition("_")[2].startswith("econ")
            or gen.unit_id.rpartition("_")[2].startswith("peak")
        )
    ]
    if not rows:
        return False

    regimes = _load_ct_offer_surface()
    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    # Per-hour measured offer level from the net-load-percentile regimes. A
    # percentile hinge maps to a net-load quantile threshold on this year's own
    # net-load distribution (forward-native: the same construction regenerates
    # from a forecast load+VRE net-load), so the surface tracks the year's
    # scarcity structure rather than an absolute MW line.
    level_series = np.zeros(hours)
    for q_lo, q_hi, level in regimes:
        if level <= 0.0:
            continue
        lo_mw = np.quantile(net_load, q_lo)
        if q_hi >= 1.0:
            mask = net_load >= lo_mw
        else:
            mask = (net_load >= lo_mw) & (net_load < np.quantile(net_load, q_hi))
        level_series[mask] = level

    row_idx = np.asarray(rows)
    mc_base[row_idx, :] = np.maximum(mc_base[row_idx, :], level_series[np.newaxis, :])
    hinge = min((lo for lo, _hi, lv in regimes if lv > 0.0), default=1.0)
    logger.info(
        "ERCOT CT/peaker offer surface applied: %d econ/peak tranche rows raised "
        "to the measured self-withholding level above the %.0fth net-load "
        "percentile (%d/%d hours)",
        len(rows),
        hinge * 100.0,
        int((level_series > 0.0).sum()),
        hours,
    )
    return True


@lru_cache(maxsize=4)
def _load_condbinned_surface(path: str) -> dict:
    """Load and cache the measured condition-binned offer surface JSON.

    Frozen against residuals (rule 20); a re-derive is a data-update commit
    (scripts/data/derive_dam_offer_hrmults.py --condition-binned), not a solve-time knob.
    """
    return json.loads(Path(path).read_text())


class _CondSurfaceSpec(NamedTuple):
    """Per-ISO wiring of the shared conditional-surface kernel.

    One row per ISO in :data:`_CONDITIONAL_SURFACE_SPECS`; every field is that
    ISO's own frozen wiring transplanted byte-for-byte from its pre-collapse
    wrapper (rules 23/25 — per-ISO values stay per-ISO, no generic merge):
    the enable flag / path / percentile-edges / min-bin / price-cap-fraction
    ScenarioConfig field names, the default surface JSON filename under
    ``CALIBRATION_DIR``, the priced class tuple, and the exact error wording
    of the edges-mismatch guard.
    """

    flag: str
    path_field: str
    default_filename: str
    pcts_field: str
    min_bin_field: str
    cap_frac_field: str
    groups: tuple[str, ...]
    err_name: str
    rederive_hint: str


#: Per-ISO conditional-surface wiring (see :class:`_CondSurfaceSpec`).
_CONDITIONAL_SURFACE_SPECS: dict[str, _CondSurfaceSpec] = {
    "ERCOT": _CondSurfaceSpec(
        flag="ercot_offer_surface_conditional",
        path_field="ercot_offer_surface_binned_path",
        default_filename="offer_curve_dam_hrmults_condbinned.json",
        pcts_field="ercot_offer_surface_netload_pcts",
        min_bin_field="ercot_offer_surface_min_bin",
        cap_frac_field="ercot_offer_surface_price_cap_frac",
        groups=CONDITIONAL_SURFACE_GROUPS,
        err_name="ercot_offer_surface",
        rederive_hint=(
            "re-derive with matching --condition-binned edges, or fix the config"
        ),
    ),
    "NEISO": _CondSurfaceSpec(
        flag="neiso_offer_surface_conditional",
        path_field="neiso_offer_surface_binned_path",
        default_filename="neiso_offer_surface_condbinned.json",
        pcts_field="neiso_offer_surface_netload_pcts",
        min_bin_field="neiso_offer_surface_min_bin",
        cap_frac_field="neiso_offer_surface_price_cap_frac",
        groups=("CT_PEAKER",),
        err_name="neiso_offer_surface",
        rederive_hint=(
            "re-derive scripts/data/derive_neiso_offer_surface.py with matching "
            "--edges, or fix the config"
        ),
    ),
    "PJM": _CondSurfaceSpec(
        flag="pjm_offer_surface_conditional",
        path_field="pjm_offer_surface_binned_path",
        default_filename="pjm_offer_surface_condbinned.json",
        pcts_field="pjm_offer_surface_netload_pcts",
        min_bin_field="pjm_offer_surface_min_bin",
        cap_frac_field="pjm_offer_surface_price_cap_frac",
        groups=("CC_REGULAR", "CT_PEAKER"),
        err_name="pjm_offer_surface",
        rederive_hint=(
            "re-derive scripts/data/derive_pjm_offer_surface.py with matching "
            "--edges, or fix the config"
        ),
    ),
    "CAISO": _CondSurfaceSpec(
        flag="caiso_offer_surface_conditional",
        path_field="caiso_offer_surface_binned_path",
        default_filename="caiso_offer_surface_condbinned.json",
        pcts_field="caiso_offer_surface_netload_pcts",
        min_bin_field="caiso_offer_surface_min_bin",
        cap_frac_field="caiso_offer_surface_price_cap_frac",
        groups=("CC_REGULAR", "CT_PEAKER"),
        err_name="caiso_offer_surface",
        rederive_hint=(
            "re-derive scripts/data/derive_caiso_offer_surface.py with matching "
            "--edges, or fix the config"
        ),
    ),
}

#: Provenance tag a within-season-conditioned PJM surface JSON carries.
_WITHIN_SEASON = "within-season"
#: Provenance tag of the legacy (and default) within-year vintage. A surface
#: JSON predating the tag is within-year by construction, so it is the default.
_WITHIN_YEAR = "within-year"


def _month_of_hour(hours: int, year: int | None = None) -> np.ndarray:
    """Calendar month (1-12) of each hour index in a Jan-1-based year array.

    Month boundaries depend only on the year's leap-ness, so an unknown year is
    resolved from the array length (8784 h = leap). Used to map hours onto
    :data:`market_sim.config.constants.PJM_SEASON_OF_MONTH` for the
    within-season tightness conditioning.
    """
    ref = year if year is not None else (2024 if hours >= 8784 else 2023)
    return pd.date_range(f"{ref}-01-01", periods=hours, freq="h").month.to_numpy()


def _tightness_hour_bin(
    net_load: np.ndarray,
    edges: "tuple[float, ...]",
    *,
    within_season: bool = False,
    year: int | None = None,
) -> np.ndarray:
    """Per-hour tightness bin from the year's OWN net-load percentiles.

    The single binning seam the PJM measured-offer-surface family shares, so
    the mid-curve and top-of-curve mechanisms can never carry contradictory
    definitions of the same tightness state (memo §2).

    ``within_season=False`` (the default, and every non-PJM ISO) ranks each
    hour against the whole year — the original construction, byte-identical.
    ``within_season=True`` ranks each hour against its OWN season's quantiles
    (:data:`~market_sim.config.constants.PJM_SEASON_OF_MONTH`), which is what
    removes the seasonal composition confound: PJM is summer-peaking in
    absolute net load, so an annual top-percentile bin is structurally a
    summer-only sample and can never classify a winter emergency as tight.

    Forward-native either way (rule 13): the thresholds come from the year's
    own (simulated, in a forecast) net load and the month->season map is
    calendar, so no measured data enters and the same quantity regenerates for
    a forward year.

    Args:
        net_load: ``(T,)`` LP-served net load, the conditioning driver.
        edges: Ascending percentile edges, e.g. ``(0.80, 0.90, 0.97)``.
        within_season: Rank within (year, season) rather than within year.
        year: Delivery year, for the month map's leap-ness. Inferred from
            ``net_load.size`` when omitted.

    Returns:
        ``(T,)`` integer bin index in ``0 .. len(edges)``.
    """
    net_load = np.asarray(net_load, dtype=float)
    if not len(edges):
        return np.zeros(net_load.size, dtype=int)
    if not within_season:
        thresholds = np.quantile(net_load, edges)
        return np.searchsorted(thresholds, net_load, side="right")

    from market_sim.config.constants import PJM_SEASON_OF_MONTH

    months = _month_of_hour(net_load.size, year)
    seasons = np.array(
        [PJM_SEASON_OF_MONTH.get(int(m), "shoulder") for m in months], dtype=object
    )
    hour_bin = np.zeros(net_load.size, dtype=int)
    for season in sorted(set(PJM_SEASON_OF_MONTH.values())):
        mask = seasons == season
        if not mask.any():
            continue
        thresholds = np.quantile(net_load[mask], edges)
        hour_bin[mask] = np.searchsorted(thresholds, net_load[mask], side="right")
    return hour_bin


def _assert_surface_vintage(
    surface: dict, within_season: bool, err_name: str, rederive_hint: str
) -> None:
    """Hard-fail when the surface JSON's vintage disagrees with the gate.

    The memo §2 vintage guard, strengthened to the owner's amendment: the
    within-year surfaces stay live and the within-season vintage lives in
    separate artifacts, so the JSON and the binning code must be paired
    explicitly. Arming the gate against a within-year JSON would price a
    season-conditioned mechanism off year-conditioned ladders (and vice
    versa) — a half-updated state that would silently mismeasure rather than
    fail. Mirrors the existing edges-mismatch guard's contract.
    """
    tag = str(surface.get("_provenance", {}).get("conditioning", _WITHIN_YEAR))
    want = _WITHIN_SEASON if within_season else _WITHIN_YEAR
    if tag != want:
        raise ValueError(
            f"{err_name}: surface vintage mismatch — the JSON is conditioned "
            f"{tag!r} but the run wants {want!r} "
            f"(pjm_offer_surface_within_season={within_season}). {rederive_hint}"
        )


#: Provenance tag the ERCOT-178 continuous-conditioning artifact vintage carries
#: (PRECOMMIT-ercot178 §2). The `ercot_offer_surface_continuous` gate and the
#: loaded artifact's vintage must agree in both directions — the PJM
#: within-season `_assert_surface_vintage` pattern applied at grain level.
_CONTPCT_TAG = "continuous-netload-pct"
#: Vintage implied by an artifact with no conditioning tag (every stepped
#: artifact predates the tag, so absence means stepped by construction).
_STEPPED_TAG = "stepped-netload-bins"
#: Provenance tag of the ERCOT-180 TOP-SCOPED vintage (PRECOMMIT-ercot180 §3):
#: frozen stepped values below p97, conduct-identified stepped sub-bins above,
#: ULP-pair step-encoded for the same interpolation machinery.
_TOPSCOPED_TAG = "topscoped-netload-bins"
#: Provenance tag of the ERCOT-181 POSITION-TAIL vintage (PRECOMMIT-ercot181
#: §3): the frozen stepped ladders byte-identical at and below p90, plus each
#: class-year-bin's measured MW-weighted empirical quantile function above
#: p90 on its own support — the position axis completed, never the level.
_POSITIONTAIL_TAG = "positiontail-netload-bins"

#: Refined-conditioning grain modes: gate field -> (vintage tag, artifact
#: filename suffix replacing "_condbinned.json", derive CLI flag). One gate,
#: one vintage, one derive mode — the guard logic reads this table so a new
#: grain form never forks the load path (rule 19: one mechanism family).
_CONTPCT_MODES: dict[str, tuple[str, str, str]] = {
    "continuous": (_CONTPCT_TAG, "_contpct.json", "--continuous"),
    "topscoped": (_TOPSCOPED_TAG, "_topscoped.json", "--top-scoped"),
}


def _contpct_mode(config: ScenarioConfig) -> "str | None":
    """Which refined-grain gate is armed: ``"continuous"``, ``"topscoped"`` or None.

    Arming both is a hard error (PRECOMMIT-ercot180 §3: one conditioning grain
    per family — the mixed-grain state the vintage guards exist to prevent).
    """
    cont = bool(getattr(config, "ercot_offer_surface_continuous", False))
    top = bool(getattr(config, "ercot_offer_surface_top_scoped", False))
    if cont and top:
        raise ValueError(
            "ercot_offer_surface_continuous and ercot_offer_surface_top_scoped "
            "both refine the measured offer-surface family's conditioning "
            "grain — arm at most one (PRECOMMIT-ercot180 §3)."
        )
    if cont:
        return "continuous"
    if top:
        return "topscoped"
    return None


def _positiontail_armed(config: ScenarioConfig, err_name: str) -> bool:
    """Whether the ERCOT-181 position-tail completion is armed, guard-checked.

    Arming it together with either conditioning-grain gate is a hard error
    (PRECOMMIT-ercot181 §3: the grain gates re-condition the hour axis, this
    gate completes the position axis — mixing vintages inside one family is
    the half-migrated state the vintage guards exist to prevent), and the
    form-(a)/(b) unmigrated-member compat guard is SHARED, not weakened.
    """
    if not bool(getattr(config, "ercot_offer_surface_position_tail", False)):
        return False
    if _contpct_mode(config) is not None:
        raise ValueError(
            f"{err_name}: ercot_offer_surface_position_tail cannot be armed "
            "together with a conditioning-grain gate "
            "(ercot_offer_surface_continuous / ercot_offer_surface_top_scoped)"
            " — one vintage per family (PRECOMMIT-ercot181 §3)."
        )
    _assert_contpct_compat(config, err_name, mode="positiontail")
    return True


def _assert_positiontail_vintage(
    surface: dict, err_name: str, rederive_hint: str, *, armed: bool
) -> None:
    """Hard-fail when the artifact vintage disagrees with the position-tail gate.

    Both directions (PRECOMMIT-ercot181 §3): the armed gate must consume a
    ``positiontail-netload-bins`` artifact, and every other path must refuse
    one — the PJM within-season / ERCOT-178/180 vintage-guard pattern.
    """
    tag = str(surface.get("_provenance", {}).get("conditioning", _STEPPED_TAG))
    if armed and tag != _POSITIONTAIL_TAG:
        raise ValueError(
            f"{err_name}: surface vintage mismatch — the JSON is conditioned "
            f"{tag!r} but ercot_offer_surface_position_tail wants "
            f"{_POSITIONTAIL_TAG!r}. {rederive_hint}"
        )
    if not armed and tag == _POSITIONTAIL_TAG:
        raise ValueError(
            f"{err_name}: surface vintage mismatch — the JSON is the "
            f"{_POSITIONTAIL_TAG!r} vintage but "
            "ercot_offer_surface_position_tail is not armed. "
            f"{rederive_hint}"
        )


def _positiontail_xy(
    ladder_q: np.ndarray,
    base_vals: np.ndarray,
    tail_pts: "list | None",
) -> "tuple[np.ndarray, np.ndarray]":
    """Extend one bin's (x, y) interp vectors with its measured tail points.

    ``tail_pts`` is the artifact's per-bin list of ``[x, mult]`` step points
    with x strictly above the frozen grid's top (0.9). An empty/absent tail
    returns the frozen vectors unchanged — the zero-support rule (today's
    end-clamp behavior, byte-identical). np.interp below the appended region
    is unaffected by construction, so the sub-p90 read never moves.
    """
    if not tail_pts:
        return ladder_q, base_vals
    tx = np.asarray([p[0] for p in tail_pts], dtype=float)
    ty = np.asarray([p[1] for p in tail_pts], dtype=float)
    keep = tx > float(ladder_q[-1])
    if not keep.any():
        return ladder_q, base_vals
    return (
        np.concatenate([ladder_q, tx[keep]]),
        np.concatenate([base_vals, ty[keep]]),
    )


def _netload_rank_pct(net_load: np.ndarray) -> np.ndarray:
    """Within-year percentile rank (0, 1] of each hour's net load.

    The solve-side conditioner of the ERCOT-178 continuous grain
    (PRECOMMIT-ercot178 §2): the exact mirror of the derives'
    ``rank(pct=True)`` node coordinate (ties averaged), on the model's own
    net load — forward-native exactly as the stepped ``np.quantile`` +
    ``searchsorted`` binning it replaces (rule 13: a forecast year ranks its
    own simulated net load).
    """
    return pd.Series(np.asarray(net_load, dtype=float)).rank(pct=True).to_numpy()


def _assert_contpct_vintage(
    surface: dict,
    err_name: str,
    rederive_hint: str,
    *,
    armed: bool = True,
    mode: str = "continuous",
) -> None:
    """Hard-fail when the artifact vintage disagrees with the armed grain gate.

    Arming a refined-grain gate against a stepped JSON would price a refined
    mechanism off pooled-bin ladders; arming it against the OTHER refined
    vintage would price one pre-registered mechanism off another's artifact;
    and the legacy path consuming any refined-node JSON is the reverse — all
    the half-migrated states the PJM within-season vintage guard pattern
    exists to prevent (PRECOMMIT-ercot178 §2; PRECOMMIT-ercot180 §3).
    """
    tag = str(surface.get("_provenance", {}).get("conditioning", _STEPPED_TAG))
    want = _CONTPCT_MODES[mode][0] if armed else _STEPPED_TAG
    if tag != want:
        raise ValueError(
            f"{err_name}: surface vintage mismatch — the JSON is conditioned "
            f"{tag!r} but the run wants {want!r} "
            f"(armed grain mode: {mode if armed else 'none'}). {rederive_hint}"
        )


def _assert_contpct_compat(
    config: ScenarioConfig, err_name: str, *, mode: str = "continuous"
) -> None:
    """Hard-fail on family members with no migrated refined-grain geometry.

    PRECOMMIT-ercot178 §2 / PRECOMMIT-ercot180 §3: the refined vintages
    migrate the four ARMED family members only (conditional peak surface,
    cleared-share wall, RT leg, fast-start pool). Any other member armed
    alongside a grain gate would mix stepped and refined conditioning inside
    one family — loud, never silent. Shared by both grain modes; this guard
    is intentional and is never weakened to get a run through.
    """
    gate = {
        "continuous": "ercot_offer_surface_continuous",
        "topscoped": "ercot_offer_surface_top_scoped",
        "positiontail": "ercot_offer_surface_position_tail",
    }[mode]
    unmigrated = [
        f
        for f in (
            "ercot_offer_surface_cleared_share_state",
            "ercot_offer_surface_cleared_share_steam",
            "ercot_shoulder_online_span",
            "ercot_offer_surface_lowcurve",
            "ercot_offer_surface_lowcurve_floorscoped",
            "ercot_offer_surface_midcurve_conditional",
            "ercot_offline_commit_offer",
        )
        if getattr(config, f, False)
    ]
    if int(getattr(config, "ercot_offer_surface_min_bin", 0) or 0) != 0:
        unmigrated.append("ercot_offer_surface_min_bin != 0")
    if unmigrated:
        raise ValueError(
            f"{err_name}: {gate} carries no migrated refined-grain geometry "
            f"for: {', '.join(unmigrated)} — disarm them or leave the grain "
            "gate off (PRECOMMIT-ercot178 §2; PRECOMMIT-ercot180 §3)."
        )


def _interp_rows(x_t: np.ndarray, xq: np.ndarray, y_rows: np.ndarray) -> np.ndarray:
    """Per-hour ``np.interp(x_t[t], xq, y_rows[t, :])``, vectorized over hours.

    The continuous grain's rel-geometry step: each hour carries its OWN
    interpolated ladder (``y_rows`` is ``(T, n_q)``), and the row's rel
    coordinate ``x_t`` may be time-varying (per-hour boundary). End behavior
    mirrors ``np.interp`` exactly: clamped flat at the terminal quantiles.
    """
    xq = np.asarray(xq, dtype=float)
    j = np.clip(np.searchsorted(xq, x_t, side="right") - 1, 0, xq.size - 2)
    x0 = xq[j]
    x1 = xq[j + 1]
    rows = np.arange(x_t.size)
    y0 = y_rows[rows, j]
    y1 = y_rows[rows, j + 1]
    # np.interp's own arithmetic (slope form) so a node table that encodes the
    # stepped ladder reproduces the stepped builders BIT-exactly (SP-3):
    # slope*(x - x0) + y0, end-clamped to the terminal values.
    with np.errstate(divide="ignore", invalid="ignore"):
        slope = (y1 - y0) / (x1 - x0)
    out = slope * (x_t - x0) + y0
    out = np.where(x_t <= xq[0], y_rows[:, 0], out)
    out = np.where(x_t >= xq[-1], y_rows[:, -1], out)
    return out


def _contpct_curve(
    tbl: dict, x_key: str, y_key: str, p_t: np.ndarray, n_q: int | None = None
) -> "np.ndarray | None":
    """Interpolate one node table onto the solve hours.

    Returns ``(T,)`` for a scalar-valued table (``n_q is None``) or
    ``(T, n_q)`` for a ladder-valued one; ``None`` when the table is absent or
    malformed. Nodes are the corpus's own hours (PRECOMMIT-ercot178 §2);
    ``np.interp`` clamps flat beyond the terminal nodes, so nothing is
    extrapolated beyond the tightest measured hour.
    """
    xs = np.asarray(tbl.get(x_key, ()), dtype=float)
    ys = np.asarray(tbl.get(y_key, ()), dtype=float)
    if xs.size == 0 or ys.shape[0] != xs.size:
        return None
    if n_q is None:
        if ys.ndim != 1:
            return None
        return np.interp(p_t, xs, ys)
    if ys.ndim != 2 or ys.shape[1] != n_q:
        return None
    return np.stack([np.interp(p_t, xs, ys[:, q]) for q in range(n_q)], axis=1)


def _ercot_gas_day(year: int, hours: int) -> np.ndarray:
    """Delivered-gas day series on the model clock (HH daily + ERCOT basis).

    The continuous builders' copy of the stepped bodies' inline normalizer —
    identical construction (the derives' own price normalizer), factored out
    so the ERCOT-178 branches never touch the stepped lines (SP-2 gate-off
    byte-identity is a code-path property, not just an assertion).
    """
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    return daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)


def build_offer_surface_conditional_markup(
    iso: str,
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build ``iso``'s conditional offer-surface markup from its spec-registry row.

    The single body behind the four per-ISO
    ``build_<iso>_offer_surface_conditional_markup`` aliases (fleet-package
    split sub-task (b)): gate on the spec's enable flag and the config ISO,
    resolve the frozen surface JSON (explicit path field, else the spec's
    default under ``CALIBRATION_DIR``), enforce the config-vs-derive
    percentile-edge agreement, and hand the spec's class tuple / min-bin /
    price-cap wiring to :func:`_conditional_surface_markup`. Behavior is the
    pre-collapse wrappers' byte-for-byte; see each alias's docstring for the
    ISO-specific provenance and mechanism history.
    """
    spec = _CONDITIONAL_SURFACE_SPECS[iso]
    if not getattr(config, spec.flag, False):
        return None
    if config.iso != iso:
        return None
    # ERCOT-178/180 refined conditioning grains (rule 25: ERCOT-gated; every
    # other ISO keeps the stepped path byte-identical).
    grain_mode = _contpct_mode(config) if iso == "ERCOT" else None
    if grain_mode is not None:
        return _conditional_surface_markup_contpct(
            fleet_arrays,
            generators,
            fuel_prices,
            net_load_mw,
            config,
            spec=spec,
            mode=grain_mode,
        )
    # PJM-only within-season vintage (rule 25): armed, the default filename
    # resolves to the `_withinseason` artifact and the binning below ranks
    # per season. Every other ISO is untouched and stays within-year.
    within_season = iso == "PJM" and bool(
        getattr(config, "pjm_offer_surface_within_season", False)
    )
    filename = spec.default_filename
    if within_season:
        filename = filename.replace(".json", "_withinseason.json")
    path = getattr(config, spec.path_field, None)
    if not path:
        from market_sim.config import paths as _paths

        default = _paths.CALIBRATION_DIR / filename
        if not default.exists():
            # An ARMED within-season gate whose vintage artifact is missing is
            # a half-migrated family, not a no-op: silently falling back to
            # "mechanism off" would let a future session think it had armed a
            # season-conditioned top-of-curve surface when it had armed
            # nothing. pjm-132 could not migrate this surface (its base-HR
            # fleet basis, the pjm98_cc_mustrun bundle, is absent from disk
            # AND from git, so re-deriving it would change the fleet basis as
            # well as the ranking scope — memo §4 forbids that), so this path
            # is reachable and must fail loudly.
            if within_season:
                raise FileNotFoundError(
                    f"{spec.err_name}: pjm_offer_surface_within_season is armed "
                    f"but {default.name} does not exist. The within-season "
                    "vintage of THIS surface has not been derived — see "
                    "docs/handoffs/pjm-132-midcurve-reconditioning-charter-"
                    "2026-07.md §6. Derive it (on its ORIGINAL fleet basis) or "
                    "leave the gate off."
                )
            return None
        path = str(default)
    surface = _load_condbinned_surface(str(path))
    if iso == "PJM":
        _assert_surface_vintage(
            surface, within_season, spec.err_name, spec.rederive_hint
        )
    if iso == "ERCOT":
        # Reverse half of the ERCOT-178 vintage guard: the legacy stepped path
        # must never consume a continuous-node JSON via a path override.
        _assert_contpct_vintage(surface, spec.err_name, spec.rederive_hint, armed=False)

    edges = tuple(float(x) for x in getattr(config, spec.pcts_field))
    json_edges = tuple(
        float(x) for x in surface.get("_provenance", {}).get("netload_pct_edges", ())
    )
    if json_edges and json_edges != edges:
        raise ValueError(
            f"{spec.err_name}: config netload_pcts "
            f"{edges} disagree with the derived surface's edges {json_edges} "
            f"({spec.rederive_hint})."
        )
    return _conditional_surface_markup(
        fleet_arrays,
        generators,
        fuel_prices,
        net_load_mw,
        config,
        surface=surface,
        edges=edges,
        groups=spec.groups,
        min_bin=int(getattr(config, spec.min_bin_field, 0) or 0),
        price_cap=float(getattr(config, spec.cap_frac_field, 0.95))
        * float(getattr(config, "voll", 5000.0)),
        label=iso,
        within_season=within_season,
    )


def build_ercot_offer_surface_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build the P1-only condition-responsive gas peak-band offer markup ``(n_gen, T)``.

    The ERCOT G-22 §8 / ercot37-filed HETEROGENEITY-PRESERVING offer surface
    (ScenarioConfig.ercot_offer_surface_conditional). Returns an additive markup on
    the P1 bid MC that reprices ONLY the gas peak-band rungs (CC/CT/ST — split
    equal-capacity at the resolved peak height by the backcast-config no-op) and ONLY
    in anticipated-tight hours, so that the top of the offer stack prices like the
    measured QSE scarcity wall exactly there. Contrast the two rejected predecessors:

      * the flat ``ercot_ct_offer_surface`` posted one p50 level on EVERY CT
        econ/peak row above a hinge → collapsed offer heterogeneity, removed ~3.2 GW
        of spare in one step, overshot (calibration-log 2026-07-06);
      * the STATIC ``peak_ladder`` wall posted the measured ladder in ALL 8760 hours
        → perturbed P0 run lengths and swapped ~8 TWh CT<->ST through the startup-
        amortization coupling (docs/FINDING-ercot-priceshape-2026-07.md §6).

    This mechanism fixes both: it is applied to the P1 clearing objective ONLY (P0 is
    byte-identical → no CT<->ST coupling), the loose bins never lower an offer (ratio
    clamped >= 1 → loose hours byte-identical), and within a tight hour the lower
    rungs stay at the resolved peak while only the upper rungs (p70/p90) reach the
    cap band (heterogeneity preserved). Both the trigger (net-load percentile,
    forward-native) and the level (measured QSE offer quantiles) are rule-13
    admissible; parameters are measured (rule 21) and frozen (rule 20).

    For each priced gas class, the peak-rung row ``g`` (rung index ``r``) in hour
    ``t`` (net-load bin ``b``) is repriced from its baked height (the resolved
    ``peak`` multiplier the fleet built the rung at) to the measured bin/rung
    multiplier::

        ratio       = max(1.0, binned_ladder[cls][b][r] / resolved_peak[cls])
        energy      = heat_rate[g] * fuel_prices[g, t]          # the row's fuel MC
        ratio_cap   = min(ratio, price_cap / energy)            # keep offer < VOLL
        markup[g,t] = energy * (ratio_cap - 1.0)                # additive, >= 0

    Vectorised over hours (rule 2). Returns ``None`` (P1 unchanged) when the flag is
    off, the ISO is not ERCOT, the surface path is unset/empty, or the fleet carries
    no priced gas peak rungs.

    Args:
        fleet_arrays: The vectorized fleet (``heat_rate`` supplies each rung's base).
        generators: The dispatch fleet, aligned row-for-row with ``fleet_arrays``.
        fuel_prices: The ``(n_gen, T)`` delivered fuel price (same array assemble_mc
            used), so the repriced offer scales with the hour's fuel like every other
            band.
        net_load_mw: System net-load per hour (``load - wind - solar``), shape
            ``(T,)`` — the same LP-served convention the drag floors / CT surface use.
        config: Scenario config supplying the enable flag, ISO, surface path, bin
            edges and price cap.
    """
    return build_offer_surface_conditional_markup(
        "ERCOT", fleet_arrays, generators, fuel_prices, net_load_mw, config
    )


def build_neiso_offer_surface_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build the NEISO P1-only fast-start offer-surface markup ``(n_gen, T)``.

    The ISO-NE analogue of :func:`build_ercot_offer_surface_conditional_markup`
    (``ScenarioConfig.neiso_offer_surface_conditional`` — winter scarcity
    charter Limb B): the measured fast-start offer distribution from ISO-NE's
    public DA Energy Market historical offer data
    (``scripts/data/derive_neiso_offer_surface.py``), condition-binned by
    within-year net-load percentile, posted onto the CT_PEAKER peak-band rungs
    in the P1 clearing objective only. Same mechanics, clamps and rule-13/20/21
    discipline as the ERCOT surface (the shared
    :func:`_conditional_surface_markup` core); NEISO-only, its own frozen
    surface JSON, no cross-ISO fallback (rule 25).
    """
    return build_offer_surface_conditional_markup(
        "NEISO", fleet_arrays, generators, fuel_prices, net_load_mw, config
    )


def build_pjm_offer_surface_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build the PJM P1-only energy-offer-surface markup ``(n_gen, T)``.

    The PJM analogue of :func:`build_ercot_offer_surface_conditional_markup`
    (``ScenarioConfig.pjm_offer_surface_conditional`` — G-22 lever A): the
    measured top-of-curve offer distribution from PJM's public DataMiner2
    ``energy_market_offers`` feed (``scripts/data/derive_pjm_offer_surface.py``),
    condition-binned by within-year net-load percentile, posted onto the
    CC_REGULAR + CT_PEAKER peak-band rungs in the P1 clearing objective only
    — the two classes whose idle supply is offered above the model price but
    below the actual DA price at the missed summer peaks
    (docs/handoffs/pjm-summer-peak-price-formation-g22-2026-07.md §1-2).
    Same mechanics, clamps and rule-13/20/21 discipline as the ERCOT/NEISO
    surfaces (the shared :func:`_conditional_surface_markup` core); PJM-only,
    its own frozen surface JSON, no cross-ISO fallback (rule 25).
    """
    return build_offer_surface_conditional_markup(
        "PJM", fleet_arrays, generators, fuel_prices, net_load_mw, config
    )


def build_caiso_offer_surface_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build the CAISO P1-only measured-offer-surface markup ``(n_gen, T)``.

    The CAISO analogue of :func:`build_pjm_offer_surface_conditional_markup`
    (``ScenarioConfig.caiso_offer_surface_conditional`` — the C1
    CC-over/CT-under lane's measured route, WP-A 2026-07-16): the measured
    top-of-curve bid distribution from CAISO's OASIS Public Bid Data
    (``scripts/data/derive_caiso_offer_surface.py``), condition-binned by
    within-year net-load percentile, posted onto the CC_REGULAR + CT_PEAKER
    peak-band rungs in the P1 clearing objective only. The derive nets the
    CARB allowance cost out of the measured tops at the resolved-peak heat
    rate, so the fuel-only repricing here round-trips the measured bid.
    Same mechanics, clamps and rule-13/23 discipline as the ERCOT/NEISO/PJM
    surfaces (the shared :func:`_conditional_surface_markup` core);
    CAISO-only, its own frozen surface JSON, no cross-ISO fallback
    (rule 25).
    """
    return build_offer_surface_conditional_markup(
        "CAISO", fleet_arrays, generators, fuel_prices, net_load_mw, config
    )


def _conditional_surface_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    *,
    surface: dict,
    edges: tuple[float, ...],
    groups: tuple[str, ...],
    min_bin: int,
    price_cap: float,
    label: str,
    within_season: bool = False,
) -> "np.ndarray | None":
    """Shared condition-binned peak-rung repricing core (ERCOT/NEISO wrappers).

    Behavior is exactly the pre-refactor ERCOT body: peak-rung rows of the
    ``groups`` classes are repriced from their resolved peak height to the
    measured ``binned_ladder`` multiplier of the hour's net-load bin, clamped
    never to lower an offer (ratio >= 1) and never to reach ``price_cap``.
    """
    n_bins = len(edges) + 1

    # Peak-rung rows per priced gas class, tagged with their rung index (peak -> 0,
    # peakN -> N-1). The resolved peak height each rung was built at comes straight
    # from the class offer curve so the ratio recovers the measured multiplier.
    curves = getattr(config, "offer_curve_by_group", None) or {}
    class_rows: dict[str, list[tuple[int, int]]] = {}
    resolved_peak: dict[str, float] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or getattr(gen, "efficiency_bin", None)
        if cls not in groups or cls not in surface:
            continue
        sfx = gen.unit_id.rpartition("_")[2]
        if sfx == "peak":
            rung = 0
        elif sfx.startswith("peak") and sfx[4:].isdigit():
            rung = int(sfx[4:]) - 1
        else:
            continue
        class_rows.setdefault(cls, []).append((g, rung))
        resolved_peak.setdefault(cls, float(curves.get(cls, {}).get("peak", 0.0)))
    if not class_rows:
        return None

    hours = int(fuel_prices.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    # Per-hour tightness bin on the year's OWN net-load percentiles (forward-native:
    # the identical construction the derive used, so bin b at solve time is the same
    # scarcity state as bin b in the measurement). ``within_season`` (PJM only,
    # default off) ranks within (year, season) instead — the paired half of the
    # within-season surface vintage, never armed independently of it.
    hour_bin = _tightness_hour_bin(
        net_load, edges, within_season=within_season
    )  # (T,), 0..n_bins-1
    # Optional floor: engage the wall only at/above min_bin (protect mild hours
    # from any residual peak-rung repricing). Below it the ratio is forced to 1
    # (byte-identical). 0 → the full measured distribution applies in every bin.
    heat_rate = fleet_arrays.heat_rate
    markup = np.zeros((len(generators), hours), dtype=float)
    n_priced = 0
    for cls, rows in class_rows.items():
        pk = resolved_peak.get(cls, 0.0)
        ladders = surface[cls].get("binned_ladder") or []
        if pk <= 0.0 or len(ladders) != n_bins:
            continue
        # ratio[bin, rung] = measured multiplier / resolved peak, clamped >= 1 so a
        # loose bin never lowers the offer below the keeper's peak height.
        n_rungs = max((r for _, r in rows), default=0) + 1
        ratio = np.ones((n_bins, n_rungs), dtype=float)
        for b in range(n_bins):
            if b < min_bin:
                continue  # mild bin: leave ratio at 1.0 (no repricing)
            lad = ladders[b] or []
            for r in range(n_rungs):
                if r < len(lad):
                    ratio[b, r] = max(1.0, float(lad[r][1]) / pk)
        for g, rung in rows:
            energy = heat_rate[g] * fuel_prices[g, :hours]  # (T,) fuel MC of the rung
            row_ratio = ratio[hour_bin, min(rung, n_rungs - 1)]  # (T,)
            # Cap the repriced offer below VOLL so the peak band never ties the load-
            # shed slack (which would let the LP dump load instead of clearing it).
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio_cap = np.where(energy > 0.0, price_cap / energy, row_ratio)
            eff = np.minimum(row_ratio, np.maximum(1.0, ratio_cap))
            markup[g, :] = energy * (eff - 1.0)
            n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        return None
    tight = int((hour_bin >= n_bins - 1).sum())
    logger.info(
        "%s conditional offer surface: repriced %d gas peak-rung rows across "
        "%d net-load bins (tightest bin binds %d/%d hours); P1-only, loose hours "
        "byte-identical",
        label,
        n_priced,
        n_bins,
        tight,
        hours,
    )
    return markup


def _conditional_surface_markup_contpct(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    *,
    spec: "_CondSurfaceSpec",
    mode: str = "continuous",
) -> "np.ndarray | None":
    """ERCOT-178/180 refined-grain body of the conditional peak-rung surface.

    The stepped core's arithmetic with the bin lookup replaced by node
    interpolation (PRECOMMIT-ercot178 §2; the ercot-180 top-scoped vintage
    reuses the identical load/interp path with its own step-encoded node
    tables, PRECOMMIT-ercot180 §3): per hour, each peak rung's measured
    multiplier is ``np.interp``-olated over the artifact's nodes at the
    hour's within-year net-load percentile rank; the ``ratio >= 1`` clamp, the
    resolved-peak reference, the per-rung VOLL cap and the row scope are the
    stepped body's own lines. Zero fitted scalars; the stepped artifact and
    code path are untouched.
    """
    _assert_contpct_compat(config, spec.err_name, mode=mode)
    _tag, suffix, flag = _CONTPCT_MODES[mode]
    gate = (
        "ercot_offer_surface_continuous"
        if mode == "continuous"
        else "ercot_offer_surface_top_scoped"
    )
    path = getattr(config, spec.path_field, None)
    if not path:
        from market_sim.config import paths as _paths

        default = _paths.CALIBRATION_DIR / spec.default_filename.replace(
            "_condbinned.json", suffix
        )
        if not default.exists():
            raise FileNotFoundError(
                f"{spec.err_name}: {gate} is armed but "
                f"{default.name} does not exist — derive it "
                f"(scripts/data/derive_dam_offer_hrmults.py {flag}) or "
                "leave the gate off (PRECOMMIT-ercot178 §2: never a silent "
                "fallback to the stepped vintage)."
            )
        path = str(default)
    surface = _load_condbinned_surface(str(path))
    _assert_contpct_vintage(
        surface,
        spec.err_name,
        f"derive scripts/data/derive_dam_offer_hrmults.py {flag}",
        mode=mode,
    )

    curves = getattr(config, "offer_curve_by_group", None) or {}
    class_rows: dict[str, list[tuple[int, int]]] = {}
    resolved_peak: dict[str, float] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or getattr(gen, "efficiency_bin", None)
        if cls not in spec.groups or cls not in surface:
            continue
        sfx = gen.unit_id.rpartition("_")[2]
        if sfx == "peak":
            rung = 0
        elif sfx.startswith("peak") and sfx[4:].isdigit():
            rung = int(sfx[4:]) - 1
        else:
            continue
        class_rows.setdefault(cls, []).append((g, rung))
        resolved_peak.setdefault(cls, float(curves.get(cls, {}).get("peak", 0.0)))
    if not class_rows:
        return None

    hours = int(fuel_prices.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    p_t = _netload_rank_pct(net_load)  # (T,)
    price_cap = float(getattr(config, spec.cap_frac_field, 0.95)) * float(
        getattr(config, "voll", 5000.0)
    )

    heat_rate = fleet_arrays.heat_rate
    markup = np.zeros((len(generators), hours), dtype=float)
    n_priced = 0
    for cls, rows in class_rows.items():
        pk = resolved_peak.get(cls, 0.0)
        cont = surface[cls].get("cont") or {}
        n_rungs_meas = int(cont.get("n_rungs", 0) or 0)
        if pk <= 0.0 or n_rungs_meas <= 0:
            continue
        mult_t = _contpct_curve(cont, "pct", "mult", p_t, n_q=n_rungs_meas)
        if mult_t is None:
            continue
        # ratio_t[t, r] = measured multiplier / resolved peak, clamped >= 1 so
        # a loose hour never lowers the offer below the keeper's peak height —
        # the stepped body's own clamp, per hour instead of per bin.
        ratio_t = np.maximum(1.0, mult_t / pk)  # (T, n_rungs)
        for g, rung in rows:
            energy = heat_rate[g] * fuel_prices[g, :hours]  # (T,) fuel MC
            # Rungs beyond the measured ladder keep ratio 1 — the stepped
            # body's own convention (a rung the surface never measured is
            # never repriced), mirrored exactly.
            if rung < n_rungs_meas:
                row_ratio = ratio_t[:, rung]  # (T,)
            else:
                row_ratio = np.ones(hours)
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio_cap = np.where(energy > 0.0, price_cap / energy, row_ratio)
            eff = np.minimum(row_ratio, np.maximum(1.0, ratio_cap))
            markup[g, :] = energy * (eff - 1.0)
            n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        return None
    logger.info(
        "ERCOT conditional offer surface (continuous grain, ERCOT-178): "
        "repriced %d gas peak-rung rows over the corpus's own hour nodes; "
        "P1-only, loose hours self-gating",
        n_priced,
    )
    return markup


#: Model class -> measured physics segment of the PJM mid-curve surface
#: (scripts/data/derive_pjm_offer_midcurve.py). CHP classes are deliberately
#: absent (steam-host economics, small idle footprint).
#: The min-load rungs of a model plant's tranche ladder -- the block at or
#: below its minimum stable level. `sync` is NOT one of them: PJM coal's sync
#: rung sits at within-plant share 0.871, ABOVE the econ band, and reads
#: 1.31-1.40x the measured offer, so it is a top-of-curve rung (pjm-h8).
_PJM_MINLOAD_SUFFIXES = frozenset({"mustrun", "committed"})

_PJM_MIDCURVE_SEGMENT_OF = {
    "CC_REGULAR": "CC_LIKE",
    "CT_PEAKER": "CT_FAST",
    "COAL": "LONG_RUN",
    "COAL_BIT": "LONG_RUN",
    "COAL_PRB": "LONG_RUN",
    "ST_GAS": "LONG_RUN",
}


class _PjmMidcurveContext(NamedTuple):
    """Everything the PJM mid-curve surface needs to price one row.

    Built once by :func:`_pjm_midcurve_context` and shared by the mid-curve
    floor/level markup and the CT_FAST max()-seam target, so the two read the
    SAME frozen surface, the SAME net-load binning and the SAME within-plant
    capacity-share ladder (a divergence between them would be an invisible
    second mechanism, rule 19).

    Attributes:
        hour_bin: ``(T,)`` within-year net-load percentile bin of each hour.
        gas_day: ``(T,)`` delivered-gas day series (HH daily + PJM basis).
        shares: ``(n_shares,)`` capacity-share grid the ladders are keyed on.
        n_bins: Number of net-load bins the surface carries.
        tables: ``segment -> (n_bins, n_shares)`` multiplier tables.
        rows: One ``(g, share, suffix, segment)`` per mapped fleet row, the
            share being the row's within-plant cumulative-capacity midpoint.
        voll_cap: The absolute price ceiling any target is clamped to.
        year_tables: The loaded segments whose ladders came from the delivery
            year's own table rather than the pooled fallback (log provenance).
    """

    hour_bin: np.ndarray
    gas_day: np.ndarray
    shares: np.ndarray
    n_bins: int
    tables: dict[str, np.ndarray]
    rows: list[tuple[int, float, str, str]]
    voll_cap: float
    year_tables: frozenset[str]


def _pjm_midcurve_context(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
    segments: set[str],
) -> "_PjmMidcurveContext":
    """Load the frozen PJM mid-curve surface and place every fleet row on it.

    Args:
        fleet_arrays: The vectorized fleet (``pmax`` sizes the share ladder).
        generators: The dispatch fleet, aligned row-for-row with ``mc_base``.
        mc_base: ``(n_gen, T)`` base marginal cost — its annual mean orders
            each plant's tranches into the rising curve the share reads off.
        net_load_mw: ``(T,)`` LP-served net load, the surface's conditioning
            driver.
        config: ScenarioConfig — supplies ``pjm_offer_midcurve_path``/``voll``.
        year: Delivery year (selects the surface's year table, pooled
            fallback for an unmapped/forward year).
        segments: Which measured segments' multiplier tables to load.

    Returns:
        The populated :class:`_PjmMidcurveContext`.

    Raises:
        ValueError: The surface JSON carries no bin edges / share grid.
    """
    # Within-season vintage (default off, owner-amended memo §2): armed, the
    # default filename resolves to the `_withinseason` artifact and the binning
    # below ranks per season — the JSON and the seam move together, never
    # independently, and the vintage guard enforces the pairing.
    within_season = bool(getattr(config, "pjm_offer_surface_within_season", False))
    path = getattr(config, "pjm_offer_midcurve_path", None)
    if not path:
        from market_sim.config import paths as _paths

        filename = (
            "pjm_offer_midcurve_condbinned_withinseason.json"
            if within_season
            else "pjm_offer_midcurve_condbinned.json"
        )
        path = str(_paths.CALIBRATION_DIR / filename)
    surface = json.loads(Path(path).read_text())
    _assert_surface_vintage(
        surface,
        within_season,
        "pjm_offer_midcurve",
        "re-derive scripts/data/derive_pjm_offer_midcurve.py with a matching "
        "--conditioning, or fix the config",
    )
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    shares = np.asarray(prov.get("shares", ()), dtype=float)
    if not edges or shares.size == 0:
        raise ValueError(
            "pjm_offer_midcurve: surface JSON carries no edges/shares — "
            "re-derive scripts/data/derive_pjm_offer_midcurve.py"
        )
    n_bins = len(edges) + 1

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    hour_bin = _tightness_hour_bin(
        net_load, edges, within_season=within_season, year=year
    )  # (T,)

    # Delivered-gas day series on the model clock (the derive's own price
    # normalizer: HH daily + PJM basis, forward-filled).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["PJM"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Per-segment (n_bins, n_shares) mult tables for this delivery year
    # (pooled fallback for an unmapped year, e.g. a forward year).
    tables: dict[str, np.ndarray] = {}
    year_tables: set[str] = set()
    for seg in set(_PJM_MIDCURVE_SEGMENT_OF.values()) & segments:
        entry = surface.get(seg)
        if not entry:
            continue
        own_year = entry.get("years", {}).get(str(year))
        ladders = own_year or entry.get("pooled")
        if not ladders or len(ladders) != n_bins:
            continue
        tables[seg] = np.array(
            [[float(pt[1]) for pt in lad] for lad in ladders], dtype=float
        )  # (n_bins, n_shares)
        if own_year:
            year_tables.add(seg)

    # Target rows + within-plant shares. A plant key is the unit_id prefix
    # (everything before the tranche suffix); the share base is EVERY
    # tranche of the plant ordered by its annual-mean base cost, so the
    # model's own rising tranche curve defines each row's curve position.
    prefixes: dict[str, list[int]] = {}
    row_cls: dict[int, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or ""
        if cls not in _PJM_MIDCURVE_SEGMENT_OF:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
        row_cls[g] = cls

    pmax = fleet_arrays.pmax
    mean_mc = mc_base.mean(axis=1)
    rows: list[tuple[int, float, str, str]] = []
    for plant_rows in prefixes.values():
        rows_arr = np.asarray(plant_rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            sfx = generators[g].unit_id.rpartition("_")[2]
            rows.append((int(g), float(s_g), sfx, _PJM_MIDCURVE_SEGMENT_OF[row_cls[g]]))

    return _PjmMidcurveContext(
        hour_bin=hour_bin,
        gas_day=gas_day,
        shares=shares,
        n_bins=n_bins,
        tables=tables,
        rows=rows,
        voll_cap=0.95 * float(getattr(config, "voll", 5000.0)),
        year_tables=frozenset(year_tables),
    )


def _pjm_midcurve_row_target(
    ctx: "_PjmMidcurveContext", segment: str, share: float
) -> np.ndarray:
    """Return the ``(T,)`` measured offer level for one row of ``segment``.

    The row's within-plant capacity ``share`` is interpolated on the measured
    ladder of each net-load bin, mapped onto the hour's bin and multiplied by
    that hour's delivered gas price, then clamped below VOLL. Hours whose bin
    ladder carries a non-finite entry come back NaN (no measured coverage).
    """
    table = ctx.tables[segment]  # (n_bins, n_shares)
    mult_b = np.array(
        [
            np.interp(share, ctx.shares, table[b])
            if np.isfinite(table[b]).all()
            else np.nan
            for b in range(ctx.n_bins)
        ]
    )
    return np.minimum(mult_b[ctx.hour_bin] * ctx.gas_day, ctx.voll_cap)


def build_pjm_offer_midcurve_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "np.ndarray | None":
    """Build the PJM P1-only MID-CURVE offer-floor markup ``(n_gen, T)``.

    G-22 lever A' (``ScenarioConfig.pjm_offer_midcurve_conditional``): the
    pjm-99 probe proved the measured TOP-of-curve surface is inert in PJM —
    the dual is capped by the ~21 GW idle mid-curve (COAL / CT_PEAKER /
    ST_GAS / CC econ bands) offered at $28-45 where the measured fleet
    prices the same curve region $35-83+, and the depth sweep showed +10 GW
    of procurement depth buys only +$2-4/MWh on that too-cheap body. This
    mechanism floors each targeted econ-tranche row's P1 bid at the
    MEASURED capacity-share-matched offer level of its physics segment
    (``scripts/data/derive_pjm_offer_midcurve.py``):

        target[g, t] = mult(segment, year, bin(t), share_g) x gas_day(t)
        markup[g, t] = max(0, min(target, 0.95 x VOLL) - mc_base[g, t])

    * ``share_g`` is the row's WITHIN-PLANT cumulative-capacity midpoint
      (scale-free — immune to the model-fleet vs measured-segment capacity
      mismatch), read off the model's own tranche structure ordered by
      base cost.
    * Targeted rows: the econ tranches (``econ*`` suffixes) of the mapped
      classes, plus the LONG_RUN classes' ``peak`` tranche (CC/CT peak
      rungs stay owned by the pjm-99 top-of-curve surface — one mechanism
      per row, rule 19). Committed / must-run / sync tranches are not
      touched BY DEFAULT (their pricing is owned by the coal
      take-or-pay/passthrough sigmoids and the commitment scaffolding).
      ``ScenarioConfig.pjm_offer_midcurve_minload_segments`` (default
      off) extends the targeting to a listed segment's ``mustrun`` /
      ``committed`` rungs, in LEVEL form — the measured offer REPLACES
      that construction rather than stacking a floor on it, so exactly
      one mechanism sets the row's bid (rule 19). ``sync`` stays out in
      every case: it is not a min-load rung (PJM coal's sits at
      within-plant share 0.871, ABOVE the econ band, reading 1.31-1.40x
      measured). pjm-h8 measured the default exclusion against PJM's own
      published offers: ``mustrun`` 0.180/0.207/0.205 and ``committed``
      0.721/0.774/0.792 of the measured offer at the rung's own capacity
      share (2023/2024/2025), against 0.93-1.08 for the rungs this
      surface already governs.
      ``ScenarioConfig.pjm_offer_midcurve_peak_segments`` (default off)
      extends the targeting to a listed segment's own ``peak*`` rungs, in
      LEVEL form — the measured top belt REPLACES the fitted rung there,
      which a raise-only floor cannot do. Config validation rejects arming
      it together with the top-of-curve surface (same rows, summed markups).
    * P1-only (the ``mc_bid_adjust`` seam): P0 run lengths and the startup
      amortization coupling are unperturbed — the pjm-99 finding's explicit
      caution for econ-band repricing (the rejected ERCOT flat-CT
      precedent).
    * The floor only ever RAISES a bid to the measured level (max(0, .)),
      mirroring the top-of-curve surface's ratio >= 1 clamp, and is capped
      below VOLL so no tranche ties the load-shed slack.

    Measured OFFER prices are the input; clearing prices stay
    validation-only (rule 13); the surface JSON is frozen against
    residuals (rule 20). PJM-only, no cross-ISO fallback (rule 25).
    """
    if not getattr(config, "pjm_offer_midcurve_conditional", False):
        return None
    if config.iso != "PJM":
        return None

    # Optional measured-segment scope (ScenarioConfig.pjm_offer_midcurve_segments):
    # None floors every mapped segment (pjm-101/102, byte-identical); a tuple
    # restricts the floor to those segments so another mechanism can own the
    # rest of the stack (rule 19 — e.g. ("LONG_RUN",) leaves the CT_FAST rows
    # to the fast-start startup amortization).
    seg_scope = getattr(config, "pjm_offer_midcurve_segments", None)
    scoped = (
        set(_PJM_MIDCURVE_SEGMENT_OF.values())
        if seg_scope is None
        else {str(s) for s in seg_scope}
    )
    # LEVEL-form scope (ScenarioConfig.pjm_offer_midcurve_level_segments,
    # default off): segments here are SET to the measured level rather than
    # floored at it — the signed markup may LOWER a fitted band that sits
    # above the measured ladder. Always intersected with the floor scope so a
    # segment outside ``scoped`` is never priced by either form (rule 19).
    lvl_cfg = getattr(config, "pjm_offer_midcurve_level_segments", None)
    level_scope = {str(s) for s in lvl_cfg} & scoped if lvl_cfg else set()
    # PEAK-row scope (ScenarioConfig.pjm_offer_midcurve_peak_segments, default
    # off): extends the targeting to the segment's ``peak*`` rungs, which the
    # base predicate excludes for every segment but LONG_RUN. Those rows are
    # ALWAYS priced in level form — the measured top belt exists precisely to
    # replace a fitted rung sitting above it, which a floor can never do
    # (pjm-122 §3). Intersected with the floor scope like the level scope.
    peak_cfg = getattr(config, "pjm_offer_midcurve_peak_segments", None)
    peak_scope = {str(s) for s in peak_cfg} & scoped if peak_cfg else set()
    # MIN-LOAD-row scope (ScenarioConfig.pjm_offer_midcurve_minload_segments,
    # default off): extends the targeting to the segment's min-load rungs,
    # which the base predicate excludes for every segment. Those rows are
    # ALWAYS priced in LEVEL form -- the measured offer REPLACES the
    # take-or-pay/sigmoid construction that currently owns them, so exactly
    # one mechanism sets the row's bid (rule 19 [R-ONE-MECH]); a floor would
    # leave the replaced construction live in every hour it exceeded the
    # measured level. Intersected with the floor scope like the others.
    minload_cfg = getattr(config, "pjm_offer_midcurve_minload_segments", None)
    minload_scope = {str(s) for s in minload_cfg} & scoped if minload_cfg else set()

    ctx = _pjm_midcurve_context(
        fleet_arrays, generators, mc_base, net_load_mw, config, year, scoped
    )
    hour_bin, n_bins, tables = ctx.hour_bin, ctx.n_bins, ctx.tables

    markup = np.zeros_like(mc_base)
    n_priced = 0
    for g, s_g, sfx, seg in ctx.rows:
        is_peak_row = sfx.startswith("peak")
        peak_targeted = is_peak_row and seg in peak_scope
        # The min-load block is the `mustrun` + `committed` rungs. `sync` is
        # deliberately NOT here: it is not a min-load rung (PJM coal's sits at
        # within-plant share 0.871, above the econ band) -- pjm-h8 §"sync".
        minload_targeted = sfx in _PJM_MINLOAD_SUFFIXES and seg in minload_scope
        is_target = (
            (sfx.startswith("econ") or (sfx == "peak" and seg == "LONG_RUN"))
            or peak_targeted
            or minload_targeted
        )
        if not is_target or seg not in tables:
            continue
        target = _pjm_midcurve_row_target(ctx, seg, s_g)  # (T,)
        if seg in level_scope or peak_targeted or minload_targeted:
            # LEVEL form: the bid IS the measured target (clamped >= 0,
            # VOLL-capped above) — a signed markup that may lower the
            # fitted band. Hours with no measured coverage (NaN target)
            # stay unpriced, matching the floor form's no-op there.
            row = np.where(
                np.isfinite(target),
                np.maximum(target, 0.0) - mc_base[g, :],
                0.0,
            )
        else:
            row = np.maximum(0.0, np.nan_to_num(target, nan=0.0) - mc_base[g, :])
        if row.any():
            markup[g, :] = row
            n_priced += 1

    # != (not >) so an all-lowering LEVEL-only scope is not discarded; for the
    # floor form the two tests are equivalent (markup >= 0 by construction).
    if n_priced == 0 or not np.any(markup != 0.0):
        return None
    tight = int((hour_bin >= n_bins - 1).sum())
    logger.info(
        "PJM mid-curve offer surface: priced %d econ/long-run tranche rows "
        "at the measured capacity-share offer level (%d net-load bins, "
        "tightest bin %d/%d hours, year table %s, level scope %s, peak scope "
        "%s); P1-only",
        n_priced,
        n_bins,
        tight,
        int(mc_base.shape[1]),
        str(year) if ctx.year_tables else "pooled",
        sorted(level_scope) or "-",
        sorted(peak_scope) or "-",
    )
    return markup


def build_pjm_ct_measured_max_target(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "np.ndarray | None":
    """Build the PJM CT_FAST measured max()-seam bid TARGET ``(n_gen, T)``.

    ``ScenarioConfig.pjm_ct_measured_max_reprice`` (default off, PJM-gated).
    The measured CT_FAST corpus prices the fast-start ladder at 22.5-39.6 x
    delivered gas — $96-174 at 2025 tight-strata gas — against a model
    marginal CT bid of $47-80, a too-cheap idle mid-merit shelf that pins the
    dual where the market cleared far higher (pjm-121 §3, pjm-122 §3).

    The returned array is a bid **LEVEL**, not a markup: the pipeline applies
    it as ``mc_bid = max(mc_bid, target)`` at the ``p1_bid_max_target`` seam,
    AFTER the startup amortization and every additive bid adjustment. That is
    the whole point of the mechanism. pjm-101/102 armed the same measured
    level as a FLOOR against ``mc_base`` alone and it over-expressed (CT -12
    TWh, C3a +12 %) because the CT stack is already owned by the pjm-103
    start-cost amortization and the two markups SUMMED. Here the measured
    level and the amortization are reconciled rather than stacked (rule 19):
    whichever prices the row higher owns it, and the measured level binds only
    where the model is cheaper than the corpus.

    Targeted rows are the CT_FAST-mapped classes' ``econ*`` and ``peak*``
    tranches — the idle shelf plus the top of the CT curve. Committed /
    must-run / sync rungs are never touched (commitment scaffolding, rule 19).
    Rows and hours with no measured coverage come back 0.0 (no-op under the
    max()). Measured OFFER prices are the input; clearing prices stay
    validation-only (rule 13); the surface JSON is frozen against residuals
    (rule 20). PJM-only, no cross-ISO fallback (rule 25).

    Args:
        fleet_arrays: The vectorized fleet the LP consumes.
        generators: The dispatch fleet, aligned row-for-row with ``mc_base``.
        mc_base: ``(n_gen, T)`` base marginal cost (shape + curve ordering).
        net_load_mw: ``(T,)`` LP-served net load, the conditioning driver.
        config: ScenarioConfig carrying the gate and the surface path.
        year: Delivery year (selects the surface's year table).

    Returns:
        The ``(n_gen, T)`` target level array, or ``None`` when the gate is
        off, the ISO is not PJM, or no row resolved a measured level.
    """
    if not getattr(config, "pjm_ct_measured_max_reprice", False):
        return None
    if config.iso != "PJM":
        return None

    ctx = _pjm_midcurve_context(
        fleet_arrays, generators, mc_base, net_load_mw, config, year, {"CT_FAST"}
    )
    if "CT_FAST" not in ctx.tables:
        return None

    target = np.zeros_like(mc_base)
    n_priced = 0
    for g, s_g, sfx, seg in ctx.rows:
        if seg != "CT_FAST" or not (sfx.startswith("econ") or sfx.startswith("peak")):
            continue
        row = _pjm_midcurve_row_target(ctx, "CT_FAST", s_g)  # (T,)
        # An uncovered hour must be a max() no-op, so NaN -> 0.0 (never a
        # negative level, which would clamp the bid downward).
        row = np.maximum(0.0, np.nan_to_num(row, nan=0.0))
        if row.any():
            target[g, :] = row
            n_priced += 1

    if n_priced == 0:
        return None
    logger.info(
        "PJM CT_FAST measured max()-seam reprice: %d CT econ/peak tranche rows "
        "carry a measured target level (%d net-load bins, year table %s); "
        "P1-only, applied as max(bid, target) after the startup amortization",
        n_priced,
        ctx.n_bins,
        str(year) if ctx.year_tables else "pooled",
    )
    return target


#: Model plant_group -> measured class key of the ERCOT mid-curve surface
#: (scripts/data/derive_ercot_offer_midcurve.py). CC_CHP shares the CC measured
#: offers (CHP is a plant attribute, not a DAM Resource Type). ST_GAS is
#: absent — the drag-floor structure owns it (rule 19).
_ERCOT_MIDCURVE_CLASS_OF = {
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "CT_PEAKER": "CT_PEAKER",
}


def build_ercot_offer_midcurve_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "np.ndarray | None":
    """Build the ERCOT P1-only MID-CURVE offer-floor markup ``(n_gen, T)``.

    G-22 lever A' (``ScenarioConfig.ercot_offer_surface_midcurve_conditional``),
    the ERCOT analogue of ``build_pjm_offer_midcurve_conditional_markup``. The
    existing ``ercot_offer_surface_conditional`` reprices only the gas PEAK rungs
    (top ~263 h/yr); this floors each targeted gas ``econ*`` tranche's P1 bid at
    the MEASURED capacity-share-matched day-ahead offer level of its class
    (``scripts/data/derive_ercot_offer_midcurve.py`` — the 60-Day DAM disclosure
    body, 18-22x at within-unit shares 0.95-0.99):

        target[g, t] = mult(class, year, bin(t), share_g) x gas_day(t)
        markup[g, t] = max(0, min(target, 0.95 x VOLL) - mc_base[g, t])

    * ``share_g`` is the row's WITHIN-PLANT cumulative-capacity midpoint
      (scale-free — immune to the model-fleet vs measured-fleet capacity
      mismatch), read off the model's own CAMPD tranche structure ordered by
      base cost, exactly as the PJM mid-curve does.
    * Targeted rows: the gas econ tranches (``econ*`` suffixes) of the mapped
      classes (CC_REGULAR/CC_CHP -> CC, CT_PEAKER). The gas PEAK rungs stay
      owned by ``ercot_offer_surface_conditional`` (one mechanism per row, rule
      19); ST_GAS is excluded (the drag-floor owns it). The floor only ever
      RAISES a bid to the measured level (max(0, .)) and is capped below VOLL.
    * P1-only (the ``mc_bid_adjust`` seam): P0 run lengths and the startup
      amortization coupling are byte-identical.

    Measured OFFER prices are the input; clearing prices stay validation-only
    (rule 13); the surface JSON is frozen against residuals (rule 23).
    ERCOT-only, no cross-ISO fallback (rule 25).
    """
    if not getattr(config, "ercot_offer_surface_midcurve_conditional", False):
        return None
    if config.iso != "ERCOT":
        return None
    path = getattr(config, "ercot_offer_surface_midcurve_path", None)
    if not path:
        from market_sim.config import paths as _paths

        path = str(_paths.CALIBRATION_DIR / "ercot_offer_midcurve_condbinned.json")
    surface = json.loads(Path(path).read_text())
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    shares = np.asarray(prov.get("shares", ()), dtype=float)
    if not edges or shares.size == 0:
        raise ValueError(
            "ercot_offer_midcurve: surface JSON carries no edges/shares — "
            "re-derive scripts/data/derive_ercot_offer_midcurve.py"
        )
    n_bins = len(edges) + 1

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    # Delivered-gas day series on the model clock (the derive's own price
    # normalizer: HH daily + ERCOT basis, forward-filled).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Per-class (n_bins, n_shares) mult tables for this delivery year (pooled
    # fallback for an unmapped/forward year).
    tables: dict[str, np.ndarray] = {}
    for cls_key in set(_ERCOT_MIDCURVE_CLASS_OF.values()):
        entry = surface.get(cls_key)
        if not entry:
            continue
        ladders = entry.get("years", {}).get(str(year)) or entry.get("pooled")
        if not ladders or len(ladders) != n_bins:
            continue
        tables[cls_key] = np.array(
            [[float(pt[1]) for pt in lad] for lad in ladders], dtype=float
        )  # (n_bins, n_shares)

    # Target rows + within-plant shares. A plant key is the unit_id prefix
    # (everything before the tranche suffix); the share base is EVERY tranche
    # of the plant ordered by its annual-mean base cost, so the model's own
    # rising CAMPD tranche curve defines each row's curve position.
    prefixes: dict[str, list[int]] = {}
    row_cls: dict[int, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or ""
        if cls not in _ERCOT_MIDCURVE_CLASS_OF:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
        row_cls[g] = cls

    pmax = fleet_arrays.pmax
    voll_cap = 0.95 * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    n_priced = 0
    mean_mc = mc_base.mean(axis=1)
    for rows in prefixes.values():
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            sfx = gen.unit_id.rpartition("_")[2]
            if not sfx.startswith("econ"):
                continue
            cls_key = _ERCOT_MIDCURVE_CLASS_OF[row_cls[g]]
            if cls_key not in tables:
                continue
            table = tables[cls_key]  # (n_bins, n_shares)
            mult_b = np.array(
                [
                    np.interp(s_g, shares, table[b])
                    if np.isfinite(table[b]).all()
                    else np.nan
                    for b in range(n_bins)
                ]
            )
            target = mult_b[hour_bin] * gas_day  # (T,)
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, np.nan_to_num(target, nan=0.0) - mc_base[g, :])
            if row.any():
                markup[g, :] = row
                n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        logger.info(
            "ERCOT mid-curve offer surface: no econ row floored (measured "
            "offers <= model econ bids at every share/bin) — byte-identical"
        )
        return None
    tight = int((hour_bin >= n_bins - 1).sum())
    logger.info(
        "ERCOT mid-curve offer surface: floored %d gas econ tranche rows at "
        "the measured capacity-share offer level (%d net-load bins, tightest "
        "bin %d/%d hours, year table %s); P1-only",
        n_priced,
        n_bins,
        tight,
        hours,
        str(year)
        if any(str(year) in (surface.get(c, {}).get("years", {})) for c in tables)
        else "pooled",
    )
    return markup


#: Model plant_group -> measured class key of the ERCOT DAM cleared-share
#: boundary artifact (scripts/data/derive_ercot_dam_cleared_share.py). Deliberately
#: NARROWER than the mid-curve map: CC_CHP is excluded (steam-host cogens
#: self-schedule — the ERCOT-70/71 decomposition measures the model's CC_CHP
#: within +12 MW of actual on the target windows, so there is no composition
#: error to price there), ST_GAS is owned by the drag structure (rule 19).
_ERCOT_CLEARED_SHARE_CLASS_OF = {
    "CC_REGULAR": "CC",
    "CT_PEAKER": "CT",
}

# ERCOT-77 steam extension (ercot_offer_surface_cleared_share_steam): the
# legacy gas-steam class joins the wall's scope, priced from the artifact's
# "ST" block (GSREH/GSNONR/GSSUP — the ERCOT-73 leg-c participation cliff).
_ERCOT_CLEARED_SHARE_STEAM_CLASS_OF = {"ST_GAS": "ST"}


def build_ercot_offer_surface_cleared_share_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "np.ndarray | None":
    """Build the ERCOT P1-only DAM CLEARED-SHARE boundary markup ``(n_gen, T)``.

    The ERCOT-72 covered-CC / CT composition mechanism
    (``ScenarioConfig.ercot_offer_surface_cleared_share``). ERCOT has no DAM
    must-offer; the 60-Day disclosure measures that on moderate days only
    ~0.49-0.64 of CC live capability (CT: 0.03-0.47) clears the DAM for energy
    — the remainder is not in the day-ahead supply at any price, while the
    model's econ tranches span ~92% of every plant at the econ multipliers.
    This floors each merchant gas ``econ*`` tranche row whose WITHIN-PLANT
    cumulative-capacity midpoint ``share_g`` exceeds the hour's net-load bin's
    MEASURED cleared share at the bin's MEASURED above-boundary offer wall::

        rel          = (share_g - boundary(bin)) / (1 - boundary(bin))
        target[g, t] = interp(rel, ladder_q, ladder_mult(bin)) x gas_day(t)
        markup[g, t] = max(0, min(target, cap_frac x VOLL) - mc_base[g, t])

    * ``boundary`` (cleared share of live capability) and the wall ladder
      (MW-weighted quantiles of offered-but-uncleared curve-segment prices as
      effective-HR multipliers) are both measured per net-load-percentile bin
      (condition-responsive: measured CC boundary 0.33 loose -> 0.64 tight),
      never day-pinned; zero fitted scalars (rules 13/14/26).
    * Targeted rows: ``econ*`` tranches of CC_REGULAR / CT_PEAKER only. The
      PEAK rungs stay owned by ``ercot_offer_surface_conditional``, the
      committed/mustrun blocks by the bridge/floor structure, ST_GAS by the
      drag, CC_CHP is measured composition-clean (rule 19). Mutually exclusive
      with ``ercot_offer_surface_midcurve_conditional`` (same econ rows — one
      owner per row): arming both is a hard error.
    * The floor only ever RAISES a bid (``max(0, .)``) and is capped below
      VOLL; rows at/below the boundary and bins with no measured data are
      byte-identical. P1-only (the ``mc_bid_adjust`` seam): P0 run lengths and
      the startup-amortization coupling are untouched.
    * ``ercot_offer_surface_cleared_share_state`` (ERCOT-73, default off)
      multiplies each walled row-hour's markup by the MEASURED
      commitment-loading state weight ``w_c(t)`` (the unloaded fraction of
      the class's above-DA-position online capability —
      ``scripts/data/derive_ercot_commitment_loading_state.py``, frozen rule 23):
      the floored bid becomes ``base + w x (wall - base)``. Moderate regimes
      (w ~ 1) keep the full wall; regimes where reality RUC/self-commits the
      un-offered capacity online near cost stand it down (w -> 0). Backcast
      years read the year's own measured hourly series (the CAMPD
      outage-overlay pattern); years absent from the artifact fall back to
      its pooled climatology (net-load-percentile bin x 4-hour block,
      forward-native). Zero fitted scalars.
    * ``ercot_offer_surface_cleared_share_rt`` (ERCOT-86, default off)
      re-prices the SAME above-boundary CC/CT rows at the MEASURED SCED
      spare-offer ladder (``scripts/data/derive_ercot_sced_offer_wall.py`` —
      the RT/SCED data-basis correction of the wall's measured-cheap DAM
      ladder, ERCOT-84 Finding 1). ``_rt_mode`` selects composition
      ``"replace"`` (A: RT-measured bins swap ladder source) or ``"tier"``
      (B: floor at max(state-weighted DAM, RT)). YEAR-SCOPED (rule 13): no
      pooled fallback — years absent from the RT artifact keep the DAM basis
      byte-identical. The RT leg is never state-weighted (the SCED spare is
      measured on the online fleet — the commitment state is already
      conditioned into the surface). ST_GAS stays DAM-basis (rule 19).
    * ``ercot_offer_surface_cleared_share_rt_room`` (ercot-242, default off)
      conditions the SAME RT ladder read per (class × net-load bin ×
      measured RTOLCAP room bin) from the room-binned artifact
      (``derive_ercot_sced_offer_wall.py --room-binned``): where the year's
      embedded measured hourly room bin and the cell exist, the cell's
      ladder (+ its own ercot-181 position tail) replaces the year-level
      bin ladder in the interp — one mechanism, finer conditioning
      (rule 19), zero fitted scalars. NaN-room hours, unmeasured cells and
      years absent from the room artifact keep the incumbent RT basis
      byte-identical (year-scoped, rule 13; PRECOMMIT-ercot242 §1.3).
      Requires the RT leg; refuses the span re-anchor and the
      conditioning-grain vintages.
    * ``ercot_faststart_pool_offer`` (ERCOT-88) is a SEPARATE builder
      (:func:`build_ercot_faststart_pool_markup`) that REPLACES every
      surface's markup — this wall's included — on the fast-start rows above
      the measured offline-pool boundary (the caller composes by mask, one
      owner per row-hour; see that builder's docstring).
    * ``ercot_shoulder_online_span`` (ERCOT-89, default off) re-anchors the
      wall/RT ladder's rel geometry on the measured CONDITIONAL online span
      (mean telemetered ON share of non-OUT capability per net-load bin x
      season x 4h block): rel = (share - boundary) / (span - boundary),
      clipped to the ladder top above the span — the SCED spare ladder is
      measured on the ONLINE fleet, and the span stops it being stretched
      over capability that is telemetered OFF at the same conditions
      (charter §8.1's measured 8-10x phantom-headroom wedge). Requires the
      RT leg and the fast-start pool leg armed (the above-span increment is
      PRICED by the pool at the caller, never capped — charter §3(ii)).
      Year-scoped (rule 13): absent years keep this geometry byte-identical.
    """
    state_flag = getattr(config, "ercot_offer_surface_cleared_share_state", False)
    steam_flag = getattr(config, "ercot_offer_surface_cleared_share_steam", False)
    rt_flag = getattr(config, "ercot_offer_surface_cleared_share_rt", False)
    if not getattr(config, "ercot_offer_surface_cleared_share", False):
        if state_flag and config.iso == "ERCOT":
            raise ValueError(
                "ercot_offer_surface_cleared_share_state scopes the "
                "cleared-share wall — arm ercot_offer_surface_cleared_share "
                "too (the state weight has nothing to scope on its own)."
            )
        if steam_flag and config.iso == "ERCOT":
            raise ValueError(
                "ercot_offer_surface_cleared_share_steam extends the "
                "cleared-share wall — arm ercot_offer_surface_cleared_share "
                "too (the steam scope has no wall to extend on its own)."
            )
        if rt_flag and config.iso == "ERCOT":
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt re-prices the "
                "cleared-share wall's ladder — arm "
                "ercot_offer_surface_cleared_share too (the RT basis has no "
                "wall to re-price on its own)."
            )
        if (
            getattr(config, "ercot_offer_surface_cleared_share_rt_room", False)
            and config.iso == "ERCOT"
        ):
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt_room conditions the "
                "cleared-share wall's RT ladder — arm "
                "ercot_offer_surface_cleared_share and "
                "ercot_offer_surface_cleared_share_rt too (the room axis has "
                "no RT ladder to condition on its own)."
            )
        if (
            getattr(config, "ercot_shoulder_online_span", False)
            and config.iso == "ERCOT"
        ):
            raise ValueError(
                "ercot_shoulder_online_span re-anchors the cleared-share "
                "wall's ladder geometry — arm ercot_offer_surface_cleared_"
                "share too (the span has no wall geometry to re-anchor on "
                "its own)."
            )
        if (
            getattr(config, "ercot_offer_surface_position_tail", False)
            and config.iso == "ERCOT"
        ):
            raise ValueError(
                "ercot_offer_surface_position_tail completes the cleared-"
                "share wall's RT ladder position axis — arm "
                "ercot_offer_surface_cleared_share too (there is no ladder "
                "to complete on its own)."
            )
        return None
    if config.iso != "ERCOT":
        return None
    rt_mode = str(
        getattr(config, "ercot_offer_surface_cleared_share_rt_mode", "replace")
    )
    if rt_flag and rt_mode not in ("replace", "tier"):
        raise ValueError(
            "ercot_offer_surface_cleared_share_rt_mode must be 'replace' "
            f"(composition A) or 'tier' (composition B), got {rt_mode!r}"
        )
    # ercot-242 room-axis extension of the RT leg (PRECOMMIT-ercot242 §1.3):
    # conditions the SAME RT ladder read per (class x net-load bin x measured
    # room bin). Requires the RT leg; refuses the shoulder-span re-anchor and
    # the conditioning-grain vintages (one vintage per family, the ercot-181
    # guard pattern).
    room_flag = getattr(config, "ercot_offer_surface_cleared_share_rt_room", False)
    if room_flag and not rt_flag:
        raise ValueError(
            "ercot_offer_surface_cleared_share_rt_room conditions the RT/SCED "
            "ladder per measured room bin — arm "
            "ercot_offer_surface_cleared_share_rt too (there is no RT ladder "
            "to condition without it)."
        )
    if room_flag and getattr(config, "ercot_shoulder_online_span", False):
        raise ValueError(
            "ercot_offer_surface_cleared_share_rt_room and "
            "ercot_shoulder_online_span both re-shape the RT ladder read — "
            "arming both is undeclared composition (PRECOMMIT-ercot242 §1.1); "
            "arm exactly one."
        )
    if room_flag and _contpct_mode(config) is not None:
        raise ValueError(
            "ercot_offer_surface_cleared_share_rt_room cannot be armed "
            "together with a conditioning-grain gate "
            "(ercot_offer_surface_continuous / ercot_offer_surface_top_scoped)"
            " — one vintage per family (PRECOMMIT-ercot242 §1.1)."
        )
    # ERCOT-181 position-tail completion (PRECOMMIT-ercot181 §3): the wall's
    # tail extends the RT/SCED ladder — the measured population whose top
    # decile the p90 end-clamp truncates — so the RT leg must be armed.
    pt_armed = _positiontail_armed(config, "ercot_offer_surface_position_tail")
    if pt_armed and not rt_flag:
        raise ValueError(
            "ercot_offer_surface_position_tail completes the RT/SCED "
            "ladder's position axis — arm ercot_offer_surface_cleared_share_"
            "rt too (the DAM ladder is not extended; PRECOMMIT-ercot181 §3)."
        )
    # Effective class scope: the base merchant CC/CT map, plus the ST_GAS ->
    # "ST" extension when the ERCOT-77 steam flag is armed.
    class_of = dict(_ERCOT_CLEARED_SHARE_CLASS_OF)
    if steam_flag:
        class_of.update(_ERCOT_CLEARED_SHARE_STEAM_CLASS_OF)
    if getattr(config, "ercot_offer_surface_midcurve_conditional", False):
        raise ValueError(
            "ercot_offer_surface_cleared_share and "
            "ercot_offer_surface_midcurve_conditional both price the gas econ "
            "rows — one mechanism per row (rule 19); arm exactly one."
        )
    # ERCOT-178/180 refined conditioning grains: same rows, same boundary/
    # ladder statistics, bin lookup -> node interpolation (PRECOMMIT-ercot178
    # §2/§4; PRECOMMIT-ercot180 §3).
    grain_mode = _contpct_mode(config)
    if grain_mode is not None:
        return _cleared_share_markup_contpct(
            fleet_arrays,
            generators,
            mc_base,
            net_load_mw,
            config,
            year,
            class_of=class_of,
            rt_flag=rt_flag,
            rt_mode=rt_mode,
            mode=grain_mode,
        )
    path = getattr(config, "ercot_offer_surface_cleared_share_path", None)
    if not path:
        from market_sim.config import paths as _paths

        path = str(_paths.CALIBRATION_DIR / "ercot_dam_cleared_share_condbinned.json")
    surface = json.loads(Path(path).read_text())
    # Reverse half of the ERCOT-178 vintage guard (the gate-on branch returned
    # above): the stepped path must never consume a continuous-node JSON.
    _assert_contpct_vintage(
        surface,
        "ercot_offer_surface_cleared_share",
        "re-derive scripts/data/derive_ercot_dam_cleared_share.py",
        armed=False,
    )
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    ladder_q = np.asarray(prov.get("ladder_quantiles", ()), dtype=float)
    if not edges or ladder_q.size == 0:
        raise ValueError(
            "ercot_offer_surface_cleared_share: surface JSON carries no "
            "edges/quantiles — re-derive scripts/data/derive_ercot_dam_cleared_share.py"
        )
    n_bins = len(edges) + 1

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    # ERCOT-73 commitment-loading state weight per class-hour (1.0 = full
    # wall). Year table = the measured backcast overlay; climatology = the
    # forward/holdout fallback on the SAME bin edges (asserted) x hour block.
    state_w: dict[str, np.ndarray] = {}
    if state_flag:
        spath = getattr(config, "ercot_offer_surface_cleared_share_state_path", None)
        if not spath:
            from market_sim.config import paths as _paths

            spath = str(_paths.CALIBRATION_DIR / "ercot_commitment_loading_state.json")
        state = json.loads(Path(spath).read_text())
        sprov = state.get("_provenance", {})
        sedges = tuple(float(x) for x in sprov.get("netload_pct_edges", ()))
        if sedges != edges:
            raise ValueError(
                "ercot_offer_surface_cleared_share_state: state artifact bin "
                f"edges {sedges} != wall edges {edges} — re-derive "
                "scripts/data/derive_ercot_commitment_loading_state.py"
            )
        block_h = int(sprov.get("hour_block_hours", 4))
        hod_block = (np.arange(hours) % 24) // block_h  # (T,)
        for cls_key in set(class_of.values()):
            entry = state.get(cls_key)
            if not entry:
                continue
            yr_tbl = entry.get("years", {}).get(str(year))
            if yr_tbl is not None and len(yr_tbl) >= hours:
                state_w[cls_key] = np.clip(
                    np.asarray(yr_tbl[:hours], dtype=float), 0.0, 1.0
                )
            else:
                clim = np.asarray(
                    state.get("climatology", {}).get(cls_key, ()), dtype=float
                )
                if clim.ndim != 2 or clim.shape[0] != n_bins:
                    continue
                w = clim[hour_bin, np.minimum(hod_block, clim.shape[1] - 1)]
                state_w[cls_key] = np.clip(np.nan_to_num(w, nan=1.0), 0.0, 1.0)

    # Delivered-gas day series on the model clock (the derive's own price
    # normalizer: HH daily + ERCOT basis, forward-filled).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Per-class boundary (n_bins,) + wall table (n_bins, n_q) for this delivery
    # year (pooled fallback for an unmapped/forward year).
    boundaries: dict[str, np.ndarray] = {}
    walls: dict[str, np.ndarray] = {}
    for cls_key in set(class_of.values()):
        entry = surface.get(cls_key)
        if not entry:
            continue
        tbl = entry.get("years", {}).get(str(year)) or entry.get("pooled")
        if not tbl:
            continue
        share = np.asarray(tbl.get("cleared_share", ()), dtype=float)
        lad = tbl.get("ladder", ())
        if share.size != n_bins or len(lad) != n_bins:
            continue
        boundaries[cls_key] = share
        walls[cls_key] = np.array(
            [[float(pt[1]) for pt in lad_b] for lad_b in lad], dtype=float
        )  # (n_bins, n_q)

    # ERCOT-86 RT/SCED-basis ladder (data-basis correction of the wall's
    # price surface — same boundary, same rows, same bin geometry, the
    # measured SCED online-spare offer ladder instead of the measured-cheap
    # DAM offered-but-uncleared ladder). YEAR-SCOPED by design (rule 13): only
    # a year present in the RT artifact gets an RT ladder — no pooled
    # fallback, so a 2024/2025-derived surface can never reach 2023's
    # conservative-ops regime; absent years keep the DAM basis byte-identical.
    rt_walls: dict[str, np.ndarray] = {}
    rt_tails: dict[str, list] = {}
    if rt_flag:
        rt_path = getattr(config, "ercot_offer_surface_cleared_share_rt_path", None)
        if not rt_path:
            from market_sim.config import paths as _paths

            rt_path = str(
                _paths.CALIBRATION_DIR
                / (
                    "ercot_sced_offer_wall_positiontail.json"
                    if pt_armed
                    else "ercot_sced_offer_wall_condbinned.json"
                )
            )
        rt_surface = json.loads(Path(rt_path).read_text())
        _assert_positiontail_vintage(
            rt_surface,
            "ercot_offer_surface_cleared_share_rt",
            "re-derive scripts/data/derive_ercot_sced_offer_wall.py --position-tail",
            armed=pt_armed,
        )
        rt_prov = rt_surface.get("_provenance", {})
        rt_edges = tuple(float(x) for x in rt_prov.get("netload_pct_edges", ()))
        rt_q = np.asarray(rt_prov.get("ladder_quantiles", ()), dtype=float)
        if rt_edges != edges or not np.array_equal(rt_q, ladder_q):
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt: RT artifact bin "
                f"geometry (edges {rt_edges}, quantiles {rt_q.tolist()}) != "
                f"DAM wall geometry (edges {edges}, quantiles "
                f"{ladder_q.tolist()}) — re-derive "
                "scripts/data/derive_ercot_sced_offer_wall.py"
            )
        for cls_key in set(class_of.values()):
            entry = rt_surface.get(cls_key)
            if not entry:
                continue
            tbl = entry.get("years", {}).get(str(year))  # year-scoped: no pooled
            if not tbl:
                continue
            lad = tbl.get("ladder", ())
            if len(lad) != n_bins:
                continue
            rt_walls[cls_key] = np.array(
                [[float(pt[1]) for pt in lad_b] for lad_b in lad], dtype=float
            )  # (n_bins, n_q)
            if pt_armed:
                # ERCOT-181: the bin's measured tail step points above the
                # frozen p90 grid point (empty list per bin = zero-support,
                # byte-identical end-clamp behavior).
                tails = tbl.get("tail", ())
                if len(tails) == n_bins:
                    rt_tails[cls_key] = tails
        if not rt_walls:
            logger.info(
                "ERCOT cleared-share RT basis: year %s absent from the RT "
                "artifact — DAM basis retained byte-identical (year-scoped, "
                "rule 13)",
                year,
            )

    # ercot-242 room-axis extension (PRECOMMIT-ercot242 §1.3): the measured
    # (class x net-load bin x room bin) surface conditions the SAME RT ladder
    # read where the year's measured room bin and the cell exist; NaN-room
    # hours, unmeasured cells and years absent from the room artifact keep
    # the incumbent RT basis byte-identical (year-scoped, rule 13). The room
    # leg carries its own per-cell position tails (the ercot-181 statistic on
    # each cell's own population), read through the same _positiontail_xy.
    rt_room: dict[str, np.ndarray] = {}  # cls -> (n_bins, n_room, n_q)
    rt_room_tails: dict[str, list] = {}  # cls -> [n_bins][n_room] tail lists
    room_hour: "np.ndarray | None" = None  # (T,) int room bin, -1 = no room
    if room_flag and rt_walls:
        room_path = getattr(
            config, "ercot_offer_surface_cleared_share_rt_room_path", None
        )
        if not room_path:
            from market_sim.config import paths as _paths

            room_path = str(
                _paths.CALIBRATION_DIR / "ercot_sced_offer_wall_roombinned.json"
            )
        room_surface = json.loads(Path(room_path).read_text())
        room_prov = room_surface.get("_provenance", {})
        if str(room_prov.get("conditioning")) != "room-binned-rtolcap-pct":
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt_room: surface vintage "
                f"mismatch — the JSON is conditioned "
                f"{room_prov.get('conditioning')!r} but the room gate wants "
                "'room-binned-rtolcap-pct'. Re-derive scripts/data/"
                "derive_ercot_sced_offer_wall.py --room-binned"
            )
        room_edges_a = tuple(float(x) for x in room_prov.get("netload_pct_edges", ()))
        room_q = np.asarray(room_prov.get("ladder_quantiles", ()), dtype=float)
        room_pct_edges = tuple(float(x) for x in room_prov.get("room_pct_edges", ()))
        if room_edges_a != edges or not np.array_equal(room_q, ladder_q):
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt_room: room artifact bin "
                f"geometry (edges {room_edges_a}, quantiles {room_q.tolist()})"
                f" != DAM wall geometry (edges {edges}, quantiles "
                f"{ladder_q.tolist()}) — re-derive "
                "scripts/data/derive_ercot_sced_offer_wall.py --room-binned"
            )
        if not room_pct_edges:
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt_room: room artifact "
                "carries no room_pct_edges — re-derive "
                "scripts/data/derive_ercot_sced_offer_wall.py --room-binned"
            )
        n_room = len(room_pct_edges) + 1
        rbh = room_surface.get("room_bin_hourly", {}).get(str(year))
        if rbh is not None and len(rbh) >= hours:
            room_hour = np.asarray(rbh[:hours], dtype=int)
            if room_hour.max() >= n_room:
                raise ValueError(
                    "ercot_offer_surface_cleared_share_rt_room: embedded "
                    f"room_bin_hourly max {int(room_hour.max())} exceeds the "
                    f"artifact's {n_room} room bins — re-derive"
                )
        for cls_key in set(class_of.values()):
            tbl = (
                room_surface.get(cls_key, {}).get("years", {}).get(str(year))
            )  # year-scoped: no pooled fallback
            if not tbl:
                continue
            parent = np.array(
                [[float(pt[1]) for pt in lad_b] for lad_b in tbl.get("ladder", ())],
                dtype=float,
            )
            base = rt_walls.get(cls_key)
            if (
                base is None
                or parent.shape != base.shape
                or not np.allclose(parent, base, equal_nan=True)
            ):
                raise ValueError(
                    "ercot_offer_surface_cleared_share_rt_room: the room "
                    f"artifact's {cls_key} {year} parent ladder does not "
                    "match the armed RT artifact's — the two vintages have "
                    "drifted apart; re-derive both from the same corpus "
                    "(PRECOMMIT-ercot242 §1.3 geometry assert)"
                )
            lr = tbl.get("ladder_room", ())
            if len(lr) != n_bins:
                continue
            arr = np.full((n_bins, n_room, ladder_q.size), np.nan)
            for b in range(n_bins):
                for r in range(min(n_room, len(lr[b]))):
                    cell = lr[b][r]
                    if cell:
                        arr[b, r, :] = [float(pt[1]) for pt in cell]
            rt_room[cls_key] = arr
            rt_room_tails[cls_key] = tbl.get("tail_room")
        if room_hour is None or not rt_room:
            logger.info(
                "ERCOT cleared-share RT room axis: year %s absent from the "
                "room artifact — RT basis retained byte-identical "
                "(year-scoped, rule 13)",
                year,
            )
            room_hour = None
            rt_room = {}

    # ERCOT-89 shoulder online-span anchor (ercot_shoulder_online_span): the
    # measured CONDITIONAL online span (mean telemetered ON share of non-OUT
    # capability per net-load bin x season x 4h block,
    # scripts/data/derive_ercot_shoulder_online_span.py) re-anchors this
    # wall's ladder GEOMETRY — rel maps the walled rows onto the ladder over
    # [boundary, span] instead of [boundary, 1.0] — because the SCED spare
    # ladder is measured on the ONLINE fleet, and stretching it over
    # capability that is telemetered OFF at the same conditions is the
    # measured 8-10x phantom-headroom wedge (charter §8.1,
    # docs/handoffs/ercot-shoulder-online-envelope-2026-07.md). Rows above
    # the span clamp at the ladder top HERE; the fast-start subset of them is
    # REPLACED by the pool leg's start-inclusive ladder at the caller
    # (REPLACE-BY-MASK — hence the required ercot_faststart_pool_offer arm),
    # so the above-span increment is PRICED, never capped (charter §3(ii)
    # no-cap line: the rejected ercot41/43 envelope family is not re-opened).
    # YEAR-SCOPED (rule 13): an absent year keeps span_h empty and the
    # full-span geometry byte-identical.
    span_flag = getattr(config, "ercot_shoulder_online_span", False)
    span_h: dict[str, np.ndarray] = {}
    if span_flag:
        if not rt_flag:
            raise ValueError(
                "ercot_shoulder_online_span re-anchors the RT/SCED wall "
                "ladder's geometry — arm ercot_offer_surface_cleared_share_rt "
                "too (there is no measured online-spare ladder to re-anchor "
                "without it)."
            )
        if not getattr(config, "ercot_faststart_pool_offer", False):
            raise ValueError(
                "ercot_shoulder_online_span prices the above-span increment "
                "on the fast-start pool's start-inclusive ladder (charter "
                "§3(ii): re-price the offline increment, never cap/clamp-"
                "only) — arm ercot_faststart_pool_offer too."
            )
        span_tables, _season_idx, _block_idx = _load_ercot_online_span_tables(
            config, year, edges, hours
        )
        for _k, _tbl in span_tables.items():
            span_h[_k] = _tbl[hour_bin, _season_idx, _block_idx]  # (T,)

    # Target rows + within-plant share midpoints: every tranche of the plant
    # ordered by its annual-mean base cost — the model's own rising CAMPD
    # tranche curve defines each row's curve position (the mid-curve
    # construction, scale-free against fleet-capacity mismatches).
    prefixes: dict[str, list[int]] = {}
    row_cls: dict[int, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or ""
        if cls not in class_of:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
        row_cls[g] = cls

    pmax = fleet_arrays.pmax
    voll_cap = float(
        getattr(config, "ercot_offer_surface_price_cap_frac", 0.95)
    ) * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    n_priced = 0
    n_rt_priced = 0
    mean_mc = mc_base.mean(axis=1)
    for rows in prefixes.values():
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            sfx = gen.unit_id.rpartition("_")[2]
            # Row-family scope (rule 19, recorded in the steam flag's config
            # comment): CC/CT wall econ* rows only (committed stays owned by
            # the bridge/floor structure); the ERCOT-77 steam extension prices
            # BOTH the committed and econ* ST_GAS tranches — the flat
            # committed offer level is exactly the measured leg-c defect, and
            # the drag keeps only the min-gen QUANTITY scaffolding (floors
            # compose independently of bids). Peak rungs are never touched
            # (ercot_offer_surface_conditional's rows).
            if row_cls[g] == "ST_GAS":
                if not (sfx.startswith("econ") or sfx == "committed"):
                    continue
            elif not sfx.startswith("econ"):
                continue
            cls_key = class_of[row_cls[g]]
            if cls_key not in boundaries:
                continue
            bnd = boundaries[cls_key]  # (n_bins,)
            wall = walls[cls_key]  # (n_bins, n_q)
            rtw = rt_walls.get(cls_key)
            rtl = rt_tails.get(cls_key) if pt_armed else None
            sp = span_h.get(cls_key) if span_flag else None
            if sp is None:
                # Per-bin target multiplier: 0 (no floor) at/below the
                # boundary or where the bin carries no measured boundary/wall.
                mult_b = np.zeros(n_bins)
                for b in range(n_bins):
                    if not np.isfinite(bnd[b]) or bnd[b] >= 1.0 or s_g <= bnd[b]:
                        continue
                    if not np.isfinite(wall[b]).all():
                        continue
                    rel = (s_g - bnd[b]) / (1.0 - bnd[b])
                    mult_b[b] = float(np.interp(rel, ladder_q, wall[b]))
                # ERCOT-86 RT ladder for the SAME above-boundary rows (same
                # boundary test, the SCED spare-offer quantile ladder as the
                # price source). rt_has marks bins the RT artifact measures —
                # only those bins ever leave the DAM basis.
                rt_mult_b = np.zeros(n_bins)
                rt_has = np.zeros(n_bins, dtype=bool)
                if rtw is not None:
                    for b in range(n_bins):
                        if not np.isfinite(bnd[b]) or bnd[b] >= 1.0 or s_g <= bnd[b]:
                            continue
                        if not np.isfinite(rtw[b]).all():
                            continue
                        rel = (s_g - bnd[b]) / (1.0 - bnd[b])
                        if rtl is not None:
                            # ERCOT-181 position-tail: same interp, the bin's
                            # own measured support appended above p90 —
                            # rel <= 0.9 reads are unaffected by construction.
                            xs, ys = _positiontail_xy(ladder_q, rtw[b], rtl[b])
                            rt_mult_b[b] = float(np.interp(rel, xs, ys))
                        else:
                            rt_mult_b[b] = float(np.interp(rel, ladder_q, rtw[b]))
                        rt_has[b] = True
                mult_h = mult_b[hour_bin]  # (T,); 0 where no floor
                rt_mult_h = rt_mult_b[hour_bin]
                rt_has_h = rt_has[hour_bin]
                # ercot-242 room axis: where the hour's measured room bin and
                # the (class, nl bin, room bin) cell exist, the RT ladder
                # read uses the cell's ladder (+ its own tail) — same rel,
                # same interp; everywhere else the incumbent RT value stands
                # byte-identical (PRECOMMIT-ercot242 §1.3).
                if room_hour is not None and cls_key in rt_room:
                    rr = rt_room[cls_key]  # (n_bins, n_room, n_q)
                    rr_tails = rt_room_tails.get(cls_key)
                    room_mult_b = np.full(rr.shape[:2], np.nan)
                    for b in range(n_bins):
                        if not np.isfinite(bnd[b]) or bnd[b] >= 1.0 or s_g <= bnd[b]:
                            continue
                        if not rt_has[b]:
                            continue
                        rel = (s_g - bnd[b]) / (1.0 - bnd[b])
                        for r in range(rr.shape[1]):
                            vals = rr[b, r]
                            if not np.isfinite(vals).all():
                                continue
                            cell_tail = (
                                rr_tails[b][r]
                                if pt_armed and rr_tails is not None
                                else None
                            )
                            if cell_tail:
                                xs, ys = _positiontail_xy(ladder_q, vals, cell_tail)
                                room_mult_b[b, r] = float(np.interp(rel, xs, ys))
                            else:
                                room_mult_b[b, r] = float(
                                    np.interp(rel, ladder_q, vals)
                                )
                    rh_safe = np.where(room_hour >= 0, room_hour, 0)
                    room_vals_h = room_mult_b[hour_bin, rh_safe]
                    use_room = (room_hour >= 0) & np.isfinite(room_vals_h) & rt_has_h
                    rt_mult_h = np.where(use_room, room_vals_h, rt_mult_h)
            else:
                # ERCOT-89 span-anchored geometry: rel is TIME-varying — the
                # ladder is stretched over [boundary, span(cell)] instead of
                # [boundary, 1.0]. Rows above the measured span (or above a
                # zero-width span) take the ladder top; the fast-start subset
                # of those row-hours is replaced by the pool leg at the
                # caller (one owner per row-hour, rule 19).
                bnd_t = bnd[hour_bin]  # (T,)
                span_eff = np.maximum(sp, bnd_t)  # span never below DA share
                above = (s_g > bnd_t) & np.isfinite(bnd_t) & (bnd_t < 1.0)
                width = span_eff - bnd_t
                rel_t = np.full(hours, np.nan)
                in_span = above & (width > 0.0) & (s_g <= span_eff)
                rel_t[in_span] = (s_g - bnd_t[in_span]) / width[in_span]
                rel_t[above & ~in_span] = 1.0
                mult_h = np.zeros(hours)
                rt_mult_h = np.zeros(hours)
                rt_has_h = np.zeros(hours, dtype=bool)
                for b in range(n_bins):
                    sel = (hour_bin == b) & np.isfinite(rel_t)
                    if not sel.any():
                        continue
                    if np.isfinite(wall[b]).all():
                        mult_h[sel] = np.interp(rel_t[sel], ladder_q, wall[b])
                    if rtw is not None and np.isfinite(rtw[b]).all():
                        rt_mult_h[sel] = np.interp(rel_t[sel], ladder_q, rtw[b])
                        rt_has_h[sel] = True
            if not mult_h.any() and not rt_has_h.any():
                continue
            target = mult_h * gas_day  # (T,); 0 where no floor
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, target - mc_base[g, :])
            if state_flag:
                # ERCOT-73: floored bid = base + w x (wall - base) — the
                # measured commitment-loading regime scales the markup.
                w = state_w.get(cls_key)
                if w is None:
                    if not rt_has_h.any():
                        continue  # no measured state for the class: no wall
                    row = np.zeros_like(row)  # DAM leg dead; RT leg may floor
                else:
                    row = row * w
            if rt_has_h.any():
                # RT leg is NEVER state-weighted: the SCED spare ladder is
                # measured on the ONLINE fleet (Base Point -> HASL is the
                # un-loaded remainder per interval), so the commitment state
                # the w-weight corrects for is already conditioned into the
                # surface — weighting it again would double-count.
                rt_target = rt_mult_h * gas_day  # (T,)
                rt_target = np.minimum(rt_target, voll_cap)
                rt_row = np.maximum(0.0, rt_target - mc_base[g, :])
                rt_row = np.where(rt_has_h, rt_row, 0.0)
                if rt_mode == "replace":
                    # Composition A: one wall, one ladder source per bin —
                    # RT-measured bins take the RT floor (even where it is
                    # BELOW the DAM ladder: the DAM basis is refuted there,
                    # not composed with); unmeasured bins keep the DAM basis.
                    row = np.where(rt_has_h, rt_row, row)
                else:
                    # Composition B: the state-weighted DAM wall stands
                    # everywhere; the RT tier rides above its reach.
                    row = np.maximum(row, rt_row)
                if rt_row.any():
                    n_rt_priced += 1
            if row.any():
                markup[g, :] = row
                n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        logger.info(
            "ERCOT cleared-share offer boundary: no econ row floored (every "
            "row at/below the measured cleared share, or measured walls <= "
            "model econ bids) — byte-identical"
        )
        return None
    logger.info(
        "ERCOT cleared-share offer boundary: floored %d gas econ tranche rows "
        "above the measured DAM cleared share (%d net-load bins, year table "
        "%s)%s; P1-only",
        n_priced,
        n_bins,
        str(year)
        if any(
            str(year) in surface.get(c, {}).get("years", {})
            for c in set(class_of.values())
        )
        else "pooled",
        (
            "; commitment-loading state weight ON (measured "
            + (
                "year series"
                if any(str(year) in state.get(c, {}).get("years", {}) for c in state_w)
                else "climatology fallback"
            )
            + ")"
        )
        if state_flag
        else "",
    )
    if rt_flag and rt_walls:
        logger.info(
            "ERCOT cleared-share RT basis (ERCOT-86): %s composition — %d "
            "rows carry the measured SCED spare-offer ladder (year table %s, "
            "classes %s; RT leg un-state-weighted by construction)",
            rt_mode,
            n_rt_priced,
            year,
            sorted(rt_walls),
        )
    if room_flag and rt_room and room_hour is not None:
        logger.info(
            "ERCOT cleared-share RT room axis (ercot-242): %d of %d hours "
            "carry a measured room bin (year %s, classes %s); NaN-room hours "
            "and unmeasured cells keep the incumbent RT basis byte-identical",
            int((room_hour >= 0).sum()),
            hours,
            year,
            sorted(rt_room),
        )
    return markup


def _cleared_share_markup_contpct(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
    *,
    class_of: dict[str, str],
    rt_flag: bool,
    rt_mode: str,
    mode: str = "continuous",
) -> "np.ndarray | None":
    """ERCOT-178/180 refined-grain body of the cleared-share wall + RT leg.

    The stepped builder's arithmetic with every per-bin lookup replaced by
    node interpolation over the artifact's nodes (PRECOMMIT-ercot178 §2; the
    ercot-180 top-scoped vintage reuses the identical load/interp path with
    its own step-encoded node tables, PRECOMMIT-ercot180 §3): per-hour
    boundary (cleared share), per-hour DAM/RT ladders, the same rel
    geometry, gas-day normalization, VOLL cap, ``max(0, target − mc)`` markup,
    ``replace``/``tier`` RT composition, class scope, row scope and P1-only
    seam. Zero fitted scalars; the stepped artifact and code path stay
    byte-untouched. Year scoping preserved exactly: RT tables are per-year
    with no pooled fallback; the DAM wall falls back to its pooled table for
    an unmapped year.
    """
    _assert_contpct_compat(config, "ercot_offer_surface_cleared_share", mode=mode)
    _tag, suffix, flag = _CONTPCT_MODES[mode]
    path = getattr(config, "ercot_offer_surface_cleared_share_path", None)
    if not path:
        from market_sim.config import paths as _paths

        path = str(_paths.CALIBRATION_DIR / f"ercot_dam_cleared_share{suffix}")
    surface = json.loads(Path(path).read_text())
    _assert_contpct_vintage(
        surface,
        "ercot_offer_surface_cleared_share",
        f"derive scripts/data/derive_ercot_dam_cleared_share.py {flag}",
        mode=mode,
    )
    prov = surface.get("_provenance", {})
    ladder_q = np.asarray(prov.get("ladder_quantiles", ()), dtype=float)
    if ladder_q.size == 0:
        raise ValueError(
            "ercot_offer_surface_cleared_share: refined-grain surface JSON "
            "carries no ladder_quantiles — derive "
            f"scripts/data/derive_ercot_dam_cleared_share.py {flag}"
        )
    n_q = int(ladder_q.size)

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    p_t = _netload_rank_pct(net_load)  # (T,)

    # Per-class per-hour boundary + DAM wall ladder from the node tables
    # (years table, pooled fallback — the stepped builder's own precedence).
    bnd_t: dict[str, np.ndarray] = {}
    wall_t: dict[str, np.ndarray] = {}
    year_tables: set[str] = set()
    for cls_key in set(class_of.values()):
        entry = surface.get(cls_key)
        if not entry:
            continue
        tbl = entry.get("years", {}).get(str(year))
        if tbl:
            year_tables.add(cls_key)
        else:
            tbl = entry.get("pooled")
        if not tbl:
            continue
        share = _contpct_curve(tbl, "share_pct", "share", p_t)
        wall = _contpct_curve(tbl, "pct", "ladder", p_t, n_q=n_q)
        if share is None or wall is None:
            continue
        bnd_t[cls_key] = share
        wall_t[cls_key] = wall

    # ERCOT-86 RT/SCED-basis ladder, continuous vintage. YEAR-SCOPED exactly
    # as the stepped artifact: per-year node tables only, no pooled fallback —
    # an absent year keeps the DAM basis byte-identical (rule 13).
    rt_t: dict[str, np.ndarray] = {}
    if rt_flag:
        rt_path = getattr(config, "ercot_offer_surface_cleared_share_rt_path", None)
        if not rt_path:
            from market_sim.config import paths as _paths

            rt_path = str(_paths.CALIBRATION_DIR / f"ercot_sced_offer_wall{suffix}")
        rt_surface = json.loads(Path(rt_path).read_text())
        _assert_contpct_vintage(
            rt_surface,
            "ercot_offer_surface_cleared_share_rt",
            f"derive scripts/data/derive_ercot_sced_offer_wall.py {flag}",
            mode=mode,
        )
        rt_q = np.asarray(
            rt_surface.get("_provenance", {}).get("ladder_quantiles", ()), dtype=float
        )
        if not np.array_equal(rt_q, ladder_q):
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt: refined-grain RT artifact "
                f"ladder quantiles {rt_q.tolist()} != DAM wall quantiles "
                f"{ladder_q.tolist()} — re-derive "
                f"scripts/data/derive_ercot_sced_offer_wall.py {flag}"
            )
        for cls_key in set(class_of.values()):
            entry = rt_surface.get(cls_key)
            if not entry:
                continue
            tbl = entry.get("years", {}).get(str(year))  # year-scoped: no pooled
            if not tbl:
                continue
            rtw = _contpct_curve(tbl, "pct", "ladder", p_t, n_q=n_q)
            if rtw is not None:
                rt_t[cls_key] = rtw
        if not rt_t:
            logger.info(
                "ERCOT cleared-share RT basis (continuous): year %s absent "
                "from the RT artifact — DAM basis retained byte-identical "
                "(year-scoped, rule 13)",
                year,
            )

    gas_day = _ercot_gas_day(year, hours)  # (T,)

    # Target rows + within-plant share midpoints — the stepped builder's own
    # construction, unchanged.
    prefixes: dict[str, list[int]] = {}
    row_cls: dict[int, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or ""
        if cls not in class_of:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
        row_cls[g] = cls

    pmax = fleet_arrays.pmax
    voll_cap = float(
        getattr(config, "ercot_offer_surface_price_cap_frac", 0.95)
    ) * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    n_priced = 0
    n_rt_priced = 0
    mean_mc = mc_base.mean(axis=1)
    for rows in prefixes.values():
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            sfx = gen.unit_id.rpartition("_")[2]
            # Row-family scope: CC/CT wall econ* rows only (the ST_GAS steam
            # extension hard-errors with the gate, so the stepped ST branch is
            # unreachable here).
            if not sfx.startswith("econ"):
                continue
            cls_key = class_of[row_cls[g]]
            if cls_key not in bnd_t:
                continue
            bnd = bnd_t[cls_key]  # (T,)
            # Above-boundary row-hours: the stepped per-bin test per hour.
            above = (s_g > bnd) & np.isfinite(bnd) & (bnd < 1.0)
            if not above.any():
                continue
            with np.errstate(divide="ignore", invalid="ignore"):
                rel_t = np.where(above, (s_g - bnd) / (1.0 - bnd), 0.0)
            mult_h = np.where(
                above, _interp_rows(rel_t, ladder_q, wall_t[cls_key]), 0.0
            )
            rtw = rt_t.get(cls_key)
            if rtw is not None:
                rt_mult_h = np.where(above, _interp_rows(rel_t, ladder_q, rtw), 0.0)
                rt_has_h = above
            else:
                rt_mult_h = np.zeros(hours)
                rt_has_h = np.zeros(hours, dtype=bool)
            if not mult_h.any() and not rt_has_h.any():
                continue
            target = mult_h * gas_day  # (T,); 0 where no floor
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, target - mc_base[g, :])
            if rt_has_h.any():
                # RT leg composition — the stepped builder's own lines.
                rt_target = rt_mult_h * gas_day
                rt_target = np.minimum(rt_target, voll_cap)
                rt_row = np.maximum(0.0, rt_target - mc_base[g, :])
                rt_row = np.where(rt_has_h, rt_row, 0.0)
                if rt_mode == "replace":
                    row = np.where(rt_has_h, rt_row, row)
                else:
                    row = np.maximum(row, rt_row)
                if rt_row.any():
                    n_rt_priced += 1
            if row.any():
                markup[g, :] = row
                n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        logger.info(
            "ERCOT cleared-share offer boundary (continuous): no econ row "
            "floored — byte-identical"
        )
        return None
    logger.info(
        "ERCOT cleared-share offer boundary (continuous grain, ERCOT-178): "
        "floored %d gas econ tranche rows over the corpus's own hour nodes "
        "(year table %s); P1-only",
        n_priced,
        sorted(year_tables) if year_tables else "pooled",
    )
    if rt_flag and rt_t:
        logger.info(
            "ERCOT cleared-share RT basis (continuous, ERCOT-86): %s "
            "composition — %d rows carry the measured SCED spare-offer node "
            "ladder (year %s, classes %s)",
            rt_mode,
            n_rt_priced,
            year,
            sorted(rt_t),
        )
    return markup


def _load_ercot_online_span_tables(
    config: ScenarioConfig,
    year: int,
    wall_edges: tuple[float, ...],
    hours: int,
) -> "tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]":
    """Resolve the ERCOT-89 conditional online-span artifact for ``year``.

    Returns ``(tables, season_idx, block_idx)`` where ``tables`` maps the
    measured class key (``"CC"``/``"CT"``) to its resolved
    ``(n_bins, n_seasons, n_blocks)`` conditional ON-share table
    (``scripts/data/derive_ercot_shoulder_online_span.py``), and
    ``season_idx`` / ``block_idx`` are the ``(hours,)`` calendar coordinates
    on the model's fixed-CST non-leap clock. Cells the corpus never covers
    (null in the artifact) resolve to **1.0** — full-span geometry, i.e. the
    mechanism is inert for those hours (no measured conditional, no
    correction). A year absent from the artifact returns ``({}, ...)`` — the
    caller stays byte-identical (YEAR-SCOPED, rule 13: no pooled fallback;
    a 2024/2025-derived table never reaches 2023's conservative-ops regime).
    """
    span_path = getattr(config, "ercot_shoulder_online_span_path", None)
    if not span_path:
        from market_sim.config import paths as _paths

        span_path = str(
            _paths.CALIBRATION_DIR / "ercot_shoulder_online_span_condbinned.json"
        )
    surface = json.loads(Path(span_path).read_text())
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    season_of_month = [int(x) for x in prov.get("season_of_month", ())]
    block_h = int(prov.get("hour_block_hours", 0))
    if edges != tuple(wall_edges):
        raise ValueError(
            "ercot_shoulder_online_span: span artifact bin edges "
            f"{edges} != cleared-share wall edges {tuple(wall_edges)} — "
            "re-derive scripts/data/derive_ercot_shoulder_online_span.py"
        )
    if len(season_of_month) != 12 or block_h <= 0:
        raise ValueError(
            "ercot_shoulder_online_span: span artifact carries no "
            "season_of_month/hour_block_hours — re-derive "
            "scripts/data/derive_ercot_shoulder_online_span.py"
        )
    # Calendar coordinates on the model's fixed-CST non-leap 8760 clock (the
    # derive's own hoy convention): month via cumulative month-start hours,
    # 4h block via hour-of-day.
    month_start_h = (
        np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24
    )  # (12,) Jan..Dec starts
    hoy = np.arange(hours)
    month_idx = np.searchsorted(month_start_h[1:], hoy % 8760, side="right")  # 0..11
    season_idx = np.asarray(season_of_month, dtype=int)[month_idx]  # (hours,)
    block_idx = (hoy % 24) // block_h  # (hours,)

    tables: dict[str, np.ndarray] = {}
    for cls_key in ("CC", "CT"):
        tbl = surface.get(cls_key, {}).get("years", {}).get(str(year))
        if not tbl:
            continue
        span = np.array(
            [
                [[np.nan if v is None else float(v) for v in row] for row in mat]
                for mat in tbl.get("span", ())
            ],
            dtype=float,
        )
        if span.ndim != 3 or span.shape[0] != len(edges) + 1:
            continue
        # Uncovered cells -> 1.0: full-span geometry, mechanism inert there.
        tables[cls_key] = np.nan_to_num(span, nan=1.0)
    if not tables:
        logger.info(
            "ERCOT shoulder online span (ERCOT-89): year %s absent from the "
            "span artifact — full-span wall geometry retained byte-identical "
            "(year-scoped, rule 13)",
            year,
        )
    return tables, season_idx, block_idx


def _plant_unit_physics(
    generators: list[Generator], prefixes: "dict[str, list[int]]"
) -> "tuple[dict[str, float], dict[str, float]]":
    """Per-plant-prefix ``(min_down_hours, min_run_hours)`` for a rule-18 gate.

    Unit physics is a property of the **plant**, and fleet assembly records it
    at plant grain: the UC-coupling tags ``min_run_hours``/``min_down_hours``
    are carried by the plant's ``committed`` anchor slice alone (a bid tranche
    must acquire no commitment coupling), and the ercot-186 repair additionally
    stamps the same assembled values on every row as
    ``plant_min_*_hours``. A rule-18 ``[R-PHYSICS]`` gate read at TRANCHE-ROW
    grain is therefore **vacuous in both directions** — every ``econ*``/
    ``peak*`` row reads 0, so a ``<= 2 h`` test admits all of them and a
    ``>= 4 h`` test rejects all of them — and its effective scope collapses onto
    the caller's class map, i.e. the hard-coded class tuple rule 18 forbids.

    The read is the **max over the prefix's rows of both fields**. Under CAMPD
    per-plant binning the two coincide (the stamp writes the same value the
    committed anchor carries); taking the max keeps the read correct, and never
    more permissive than the row read, on a fleet path that does not stamp.
    A plant whose bin sheet records no physics reads 0 — disclosed, not
    papered over: against an UPPER-bound gate it licenses identically to the
    published class table (``CT_COMMITMENT_PARAMS``, min-down 1 h at every heat
    rate), so no fallback ladder is introduced here (rule 19 ``[R-ONE-MECH]``);
    a tier with a LOWER bound must revisit that.

    This is the ercot-176 Amendment-2 construction
    (``build_ercot_offline_commit_target``, which reads it inline) generalized
    to a shared helper for the ERCOT-88 fast-start pool's two bodies.
    """
    md: dict[str, float] = {}
    mr: dict[str, float] = {}
    for pref, rows in prefixes.items():
        md[pref] = max(
            max(
                float(getattr(generators[g], "plant_min_down_hours", 0) or 0),
                float(getattr(generators[g], "min_down_hours", 0) or 0),
            )
            for g in rows
        )
        mr[pref] = max(
            max(
                float(getattr(generators[g], "plant_min_run_hours", 0) or 0),
                float(getattr(generators[g], "min_run_hours", 0) or 0),
            )
            for g in rows
        )
    return md, mr


def build_ercot_faststart_pool_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "tuple[np.ndarray, np.ndarray] | None":
    """Build the ERCOT-88 offline fast-start pool ``(markup, own_mask)``.

    The §6.2 mechanism of
    ``docs/handoffs/ercot-residual-midband-formation-lane-2026-07.md`` (§9,
    ``ScenarioConfig.ercot_faststart_pool_offer``). The ERCOT-87 measurement
    adjudicated that the actual $150-500 moderate-tightness band prices on the
    OFFLINE startable CT pool (telemetered OFFQS/OFFNS — ~5x the online
    spare's in-band offer mass; 12-18 CT starts per covered band hour), not on
    any online-spare or unmitigated-CC surface. This builder offers that
    capability to the LP at its measured price::

        boundary(bin) = 1 - pool_frac(bin)          # measured pool share
        rel           = (share_g - boundary) / (1 - boundary)
        target[g, t]  = interp(rel, ladder_q, pool_ladder(bin)) x gas_day(t)
        markup[g, t]  = max(0, min(target, cap_frac x VOLL) - mc_base[g, t])

    on the merchant CT rows (the cleared-share wall's measured "CT" class
    scope) whose WITHIN-PLANT cumulative-capacity midpoint lies above the
    hour-bin's measured pool boundary — the top-of-curve capacity that in
    reality is telemetered offline-startable.

    * **Eligibility is unit physics** (rule 12 / charter §9.2):
      ``min_down_hours <= constants.FASTSTART_POOL_MIN_DOWN_HOURS`` — the
      SCED-startable-intra-hour inequality. CC rows fail by physics (4-8 h),
      ST_GAS by its 8-12 h min-down; no class tuple gates eligibility.
      **Evaluated per PLANT** (ercot-186, card D3; UNCONDITIONAL since
      ercot-204): read on a bid ROW the test was vacuous — assembly carries the
      UC-coupling tags on the committed anchor alone, so every
      ``econ*``/``peak*`` row reads 0 and the inequality was False for every row
      the builder can reach, leaving the class map as the only real filter. The
      gate reads ``_plant_unit_physics`` and skips the whole plant, which is
      what makes the rule-18 test bind. The pre-repair row-grain read and its
      transitional ``ercot_faststart_pool_plant_physics`` flag were DELETED at
      ercot-204 (rule 26 ``[R-DELETE]``) once a re-solve existed that no longer
      referenced them.
    * **Replace composition, by mask** (rule 19 / charter §9.1): the returned
      ``own_mask`` (n_gen, T) marks the row-hours the pool owns; the caller
      REPLACES every other offer surface's markup there (conditional peak
      surface, cleared-share wall, RT leg alike) — that capability is
      offline, so an online-basis price is refuted for it by status. One
      owner per row-hour, enforced at the composition site. In a measured
      row-hour whose pool target sits below the model's base cost the markup
      is 0 and the row bids cost (the pool is OFFERED, never forced).
    * **An offer-availability, never a floor**: no ``min_gen`` is touched —
      forced-energy (D-2) and off-window-binding (D-4) exposure is vacuous by
      construction, so the rule-17 hazard (a CT floor binding overnight at
      CF ~ 0) is structurally impossible.
    * **Above-LSL basis**: the ladder is derived from the pool's above-LSL
      startable increment only (``derive_ercot_faststart_pool.py``) — the
      negative below-LSL min-gen curve bottoms never enter, and the markup
      only ever RAISES a bid.
    * **Year-scoped** (rule 13): no pooled fallback — a year absent from the
      artifact returns None (every surface byte-identical; 2024/2025 only,
      the RT wall's own 2023 input-blocked bar). Zero fitted scalars; the
      artifact is frozen against residuals (rule 23).
    * **ERCOT-89 span boundary** (``ercot_shoulder_online_span``, default
      off): the boundary generalizes from ``1 - pool_frac(bin)`` to the
      measured conditional online span (charter §6 shape (a) — the FULL
      offline increment of merchant CT priced at the pool's start-inclusive
      ladder, clamped below by the bin's DA cleared share). Span years
      absent from the span artifact keep the static boundary byte-identical.
    * P1-only via the shared ``mc_bid_adjust`` seam: P0 run lengths and the
      startup-amortization coupling are untouched.

    Requires the cleared-share wall armed (the recipe context the §9.1
    rule-19 enumeration was performed against); arming the pool leg without
    it is a hard error.
    """
    if not getattr(config, "ercot_faststart_pool_offer", False):
        return None
    if config.iso != "ERCOT":
        return None
    if not getattr(config, "ercot_offer_surface_cleared_share", False):
        raise ValueError(
            "ercot_faststart_pool_offer composes against the cleared-share "
            "wall's row pricing (charter §9.1 enumeration) — arm "
            "ercot_offer_surface_cleared_share too."
        )
    # ERCOT-178/180 refined conditioning grains: same rows, same pool_frac +
    # ladder statistics, bin lookup -> node interpolation (PRECOMMIT-ercot178
    # §2/§4; PRECOMMIT-ercot180 §3); own_mask composition unchanged.
    grain_mode = _contpct_mode(config)
    if grain_mode is not None:
        return _faststart_pool_markup_contpct(
            fleet_arrays,
            generators,
            mc_base,
            net_load_mw,
            config,
            year,
            mode=grain_mode,
        )
    from market_sim.config.constants import FASTSTART_POOL_MIN_DOWN_HOURS

    # ERCOT-181 position-tail completion (PRECOMMIT-ercot181 §3): armed, the
    # pool ladder's position axis is completed above p90 from the offline
    # pool's own measured population, via the positiontail artifact vintage.
    pt_armed = _positiontail_armed(config, "ercot_faststart_pool_offer")
    pool_path = getattr(config, "ercot_faststart_pool_offer_path", None)
    if not pool_path:
        from market_sim.config import paths as _paths

        pool_path = str(
            _paths.CALIBRATION_DIR
            / (
                "ercot_faststart_pool_positiontail.json"
                if pt_armed
                else "ercot_faststart_pool_condbinned.json"
            )
        )
    pool_surface = json.loads(Path(pool_path).read_text())
    _assert_positiontail_vintage(
        pool_surface,
        "ercot_faststart_pool_offer",
        "re-derive scripts/data/derive_ercot_faststart_pool.py --position-tail",
        armed=pt_armed,
    )
    prov = pool_surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    ladder_q = np.asarray(prov.get("ladder_quantiles", ()), dtype=float)
    if not edges or ladder_q.size == 0:
        raise ValueError(
            "ercot_faststart_pool_offer: pool artifact carries no "
            "edges/quantiles — re-derive scripts/data/derive_ercot_faststart_pool.py"
        )
    # Same bin geometry as the wall artifacts by construction (the derive
    # imports the shared NETLOAD_PCT_EDGES/LADDER_QUANTILES); assert against
    # the wall artifact when the wall is armed so a drifted re-derive is loud.
    wall_path = getattr(config, "ercot_offer_surface_cleared_share_path", None)
    if not wall_path:
        from market_sim.config import paths as _paths

        wall_path = str(
            _paths.CALIBRATION_DIR / "ercot_dam_cleared_share_condbinned.json"
        )
    wall_prov = json.loads(Path(wall_path).read_text()).get("_provenance", {})
    wall_edges = tuple(float(x) for x in wall_prov.get("netload_pct_edges", ()))
    if wall_edges and wall_edges != edges:
        raise ValueError(
            "ercot_faststart_pool_offer: pool artifact bin edges "
            f"{edges} != cleared-share wall edges {wall_edges} — re-derive "
            "scripts/data/derive_ercot_faststart_pool.py"
        )
    n_bins = len(edges) + 1

    tbl = pool_surface.get("CT", {}).get("years", {}).get(str(year))
    if not tbl:  # year-scoped: no pooled fallback (rule 13)
        logger.info(
            "ERCOT fast-start pool (ERCOT-88): year %s absent from the pool "
            "artifact — every surface byte-identical (year-scoped, rule 13)",
            year,
        )
        return None
    frac = np.asarray(tbl.get("pool_frac", ()), dtype=float)
    lad = tbl.get("ladder", ())
    if frac.size != n_bins or len(lad) != n_bins:
        return None
    pool_bnd = 1.0 - np.clip(frac, 0.0, 1.0)  # (n_bins,)
    pool_wall = np.array(
        [[float(pt[1]) for pt in lad_b] for lad_b in lad], dtype=float
    )  # (n_bins, n_q)
    # ERCOT-181: per-bin measured tail step points above the frozen p90 grid
    # point (empty per-bin list = zero-support, byte-identical end-clamp).
    pool_tails = None
    if pt_armed:
        tails = tbl.get("tail", ())
        if len(tails) == n_bins:
            pool_tails = tails

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    # ERCOT-89 shoulder online-span boundary (ercot_shoulder_online_span):
    # when armed, the pool boundary generalizes from the measured OFFQS/OFFNS
    # pool share (1 - pool_frac per bin) to the measured CONDITIONAL online
    # span (charter §6 shape (a): the FULL offline increment of merchant CT
    # is priced at the pool's start-inclusive ladder, not just its
    # quick-start slice). The span is clamped below by the bin's measured
    # DA cleared share (DA-cleared capability is committed, so the online
    # span can never sit below it — the wall leg uses the same clamp).
    # YEAR-SCOPED (rule 13): a year absent from the span artifact keeps the
    # ERCOT-88 static boundary byte-identical.
    span_ct: "np.ndarray | None" = None
    if getattr(config, "ercot_shoulder_online_span", False):
        span_tables, _season_idx, _block_idx = _load_ercot_online_span_tables(
            config, year, edges, hours
        )
        span_tbl = span_tables.get("CT")
        if span_tbl is not None:
            wall_surface = json.loads(Path(wall_path).read_text())
            wall_ct = wall_surface.get("CT", {})
            wall_tbl = wall_ct.get("years", {}).get(str(year)) or wall_ct.get("pooled")
            bnd_ct = (
                np.asarray(wall_tbl.get("cleared_share", ()), dtype=float)
                if wall_tbl
                else np.full(n_bins, np.nan)
            )
            if bnd_ct.size != n_bins:
                bnd_ct = np.full(n_bins, np.nan)
            span_raw = span_tbl[hour_bin, _season_idx, _block_idx]  # (T,)
            bnd_t = np.where(np.isfinite(bnd_ct[hour_bin]), bnd_ct[hour_bin], 0.0)
            span_ct = np.maximum(span_raw, bnd_t)

    # Delivered-gas day series (the wall's own price normalizer).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Row universe: the wall's measured merchant-CT class scope (the pool
    # ladder's own measured class); ELIGIBILITY within it is unit physics.
    ct_groups = {
        grp for grp, key in _ERCOT_CLEARED_SHARE_CLASS_OF.items() if key == "CT"
    }
    prefixes: dict[str, list[int]] = {}
    for g, gen in enumerate(generators):
        if (getattr(gen, "plant_group", None) or "") not in ct_groups:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)

    # ercot-186 rule-18 [R-PHYSICS] GRAIN REPAIR (card D3), UNCONDITIONAL since
    # ercot-204: the physics gate is evaluated on the PLANT and inherited by its
    # bid rows. The pre-repair row-grain read is DELETED, not disabled (rule 26
    # [R-DELETE]) — it was vacuous by construction, since assembly stamps
    # min_down only on the committed anchor slice and every econ*/peak* bid row
    # it could reach reads 0 (see _plant_unit_physics).
    plant_md = _plant_unit_physics(generators, prefixes)[0]
    pmax = fleet_arrays.pmax
    voll_cap = float(
        getattr(config, "ercot_offer_surface_price_cap_frac", 0.95)
    ) * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    own_mask = np.zeros_like(mc_base, dtype=bool)
    n_priced = 0
    n_plants_excluded = 0
    mean_mc = mc_base.mean(axis=1)
    for pref, rows in prefixes.items():
        # Rule-18 physics gate at PLANT grain: SCED-startable intra-hour.
        if plant_md[pref] > FASTSTART_POOL_MIN_DOWN_HOURS:
            n_plants_excluded += 1
            continue
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            # Committed and must-run blocks stay with their own floor structure
            # (rule 19) — only the bid tranches (econ*/peak*) join the pool
            # universe. The physics gate itself is applied at plant grain above.
            sfx = gen.unit_id.rpartition("_")[2]
            if not (sfx.startswith("econ") or sfx.startswith("peak")):
                continue
            if span_ct is None:
                # ERCOT-88 static boundary: the measured OFFQS/OFFNS pool
                # share per net-load bin.
                mult_b = np.zeros(n_bins)
                has_b = np.zeros(n_bins, dtype=bool)
                for b in range(n_bins):
                    pb = pool_bnd[b]
                    if not np.isfinite(pb) or pb >= 1.0 or s_g <= pb:
                        continue
                    if not np.isfinite(pool_wall[b]).all():
                        continue
                    rel = (s_g - pb) / (1.0 - pb)
                    if pool_tails is not None:
                        # ERCOT-181 position-tail: same interp, the bin's own
                        # measured support appended above p90 — rel <= 0.9
                        # reads are unaffected by construction.
                        xs, ys = _positiontail_xy(ladder_q, pool_wall[b], pool_tails[b])
                        mult_b[b] = float(np.interp(rel, xs, ys))
                    else:
                        mult_b[b] = float(np.interp(rel, ladder_q, pool_wall[b]))
                    has_b[b] = True
                if not has_b.any():
                    continue
                mult_h = mult_b[hour_bin]  # (T,)
                mask = has_b[hour_bin]  # (T,)
            else:
                # ERCOT-89 span boundary: the row-hours ABOVE the measured
                # conditional online span take the pool's start-inclusive
                # ladder (rel over (span, 1]); hours whose span reaches 1.0
                # (fully-online cells, or cells the corpus never covers)
                # are never pool-owned.
                own_t = (s_g > span_ct) & (span_ct < 1.0)
                rel_t = np.zeros(hours)
                rel_t[own_t] = (s_g - span_ct[own_t]) / (1.0 - span_ct[own_t])
                mult_h = np.zeros(hours)
                mask = np.zeros(hours, dtype=bool)
                for b in range(n_bins):
                    sel = (hour_bin == b) & own_t
                    if not sel.any():
                        continue
                    if not np.isfinite(pool_wall[b]).all():
                        continue
                    mult_h[sel] = np.interp(rel_t[sel], ladder_q, pool_wall[b])
                    mask[sel] = True
                if not mask.any():
                    continue
            target = mult_h * gas_day  # (T,)
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, target - mc_base[g, :])
            markup[g, :] = np.where(mask, row, 0.0)
            own_mask[g, :] = mask
            n_priced += 1

    if not own_mask.any():
        logger.info(
            "ERCOT fast-start pool (ERCOT-88): no fast-start row above the "
            "measured pool boundary — byte-identical"
        )
        return None
    logger.info(
        "ERCOT fast-start pool (ERCOT-88%s): %d fast-start rows carry the "
        "offline-pool above-LSL SCED2 ladder (year table %s; physics gate "
        "min_down <= %.0f h at %s grain, %d plants excluded; replace-by-mask "
        "composition, never state-weighted)",
        ("; ERCOT-89 conditional online-span boundary" if span_ct is not None else ""),
        n_priced,
        year,
        FASTSTART_POOL_MIN_DOWN_HOURS,
        "PLANT (ercot-186)",
        n_plants_excluded,
    )
    return markup, own_mask


def _faststart_pool_markup_contpct(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
    *,
    mode: str = "continuous",
) -> "tuple[np.ndarray, np.ndarray] | None":
    """ERCOT-178/180 refined-grain body of the ERCOT-88 fast-start pool.

    The stepped builder's arithmetic with the per-bin ``pool_frac`` boundary
    and ladder replaced by node interpolation over the artifact's nodes
    (PRECOMMIT-ercot178 §2; the ercot-180 top-scoped vintage reuses the
    identical load/interp path with its own step-encoded node tables,
    PRECOMMIT-ercot180 §3): per-hour boundary ``1 − pool_frac(p_t)``,
    per-hour above-LSL SCED2 ladder, the same physics gate, row universe,
    VOLL cap, ``own_mask`` replace-by-mask composition and P1-only seam.
    Year-scoped with no pooled fallback, exactly as the stepped artifact.
    """
    _assert_contpct_compat(config, "ercot_faststart_pool_offer", mode=mode)
    _tag, suffix, flag = _CONTPCT_MODES[mode]
    from market_sim.config.constants import FASTSTART_POOL_MIN_DOWN_HOURS

    pool_path = getattr(config, "ercot_faststart_pool_offer_path", None)
    if not pool_path:
        from market_sim.config import paths as _paths

        pool_path = str(_paths.CALIBRATION_DIR / f"ercot_faststart_pool{suffix}")
    pool_surface = json.loads(Path(pool_path).read_text())
    _assert_contpct_vintage(
        pool_surface,
        "ercot_faststart_pool_offer",
        f"derive scripts/data/derive_ercot_faststart_pool.py {flag}",
        mode=mode,
    )
    ladder_q = np.asarray(
        pool_surface.get("_provenance", {}).get("ladder_quantiles", ()), dtype=float
    )
    if ladder_q.size == 0:
        raise ValueError(
            "ercot_faststart_pool_offer: refined-grain pool artifact carries "
            "no ladder_quantiles — derive "
            f"scripts/data/derive_ercot_faststart_pool.py {flag}"
        )
    n_q = int(ladder_q.size)

    tbl = pool_surface.get("CT", {}).get("years", {}).get(str(year))
    if not tbl:  # year-scoped: no pooled fallback (rule 13)
        logger.info(
            "ERCOT fast-start pool (continuous, ERCOT-88): year %s absent "
            "from the pool artifact — every surface byte-identical "
            "(year-scoped, rule 13)",
            year,
        )
        return None

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    p_t = _netload_rank_pct(net_load)  # (T,)
    frac_t = _contpct_curve(tbl, "frac_pct", "pool_frac", p_t)
    wall_t = _contpct_curve(tbl, "pct", "ladder", p_t, n_q=n_q)
    if frac_t is None or wall_t is None:
        return None
    pool_bnd_t = 1.0 - np.clip(frac_t, 0.0, 1.0)  # (T,)

    gas_day = _ercot_gas_day(year, hours)  # (T,)

    # Row universe + physics gate — the stepped builder's own lines.
    ct_groups = {
        grp for grp, key in _ERCOT_CLEARED_SHARE_CLASS_OF.items() if key == "CT"
    }
    prefixes: dict[str, list[int]] = {}
    for g, gen in enumerate(generators):
        if (getattr(gen, "plant_group", None) or "") not in ct_groups:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)

    # ercot-186 rule-18 grain repair — the stepped builder's own construction,
    # unconditional since ercot-204 (rule 26 [R-DELETE]).
    plant_md = _plant_unit_physics(generators, prefixes)[0]
    pmax = fleet_arrays.pmax
    voll_cap = float(
        getattr(config, "ercot_offer_surface_price_cap_frac", 0.95)
    ) * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    own_mask = np.zeros_like(mc_base, dtype=bool)
    n_priced = 0
    n_plants_excluded = 0
    mean_mc = mc_base.mean(axis=1)
    for pref, rows in prefixes.items():
        if plant_md[pref] > FASTSTART_POOL_MIN_DOWN_HOURS:
            n_plants_excluded += 1
            continue
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            sfx = gen.unit_id.rpartition("_")[2]
            if not (sfx.startswith("econ") or sfx.startswith("peak")):
                continue
            mask = (s_g > pool_bnd_t) & np.isfinite(pool_bnd_t) & (pool_bnd_t < 1.0)
            if not mask.any():
                continue
            with np.errstate(divide="ignore", invalid="ignore"):
                rel_t = np.where(mask, (s_g - pool_bnd_t) / (1.0 - pool_bnd_t), 0.0)
            mult_h = np.where(mask, _interp_rows(rel_t, ladder_q, wall_t), 0.0)
            target = mult_h * gas_day  # (T,)
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, target - mc_base[g, :])
            markup[g, :] = np.where(mask, row, 0.0)
            own_mask[g, :] = mask
            n_priced += 1

    if not own_mask.any():
        logger.info(
            "ERCOT fast-start pool (continuous, ERCOT-88): no fast-start row "
            "above the measured pool boundary — byte-identical"
        )
        return None
    logger.info(
        "ERCOT fast-start pool (continuous grain, ERCOT-178): %d fast-start "
        "rows carry the offline-pool above-LSL SCED2 node ladder (year %s; "
        "physics gate min_down <= %.0f h at %s grain, %d plants excluded; "
        "replace-by-mask composition)",
        n_priced,
        year,
        FASTSTART_POOL_MIN_DOWN_HOURS,
        "PLANT (ercot-186)",
        n_plants_excluded,
    )
    return markup, own_mask


def build_ercot_offline_commit_target(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "tuple[np.ndarray, np.ndarray] | None":
    """Build the ERCOT-176 offline-increment SLOW-START ``(target, own_mask)``.

    ``ScenarioConfig.ercot_offline_commit_offer`` — the owner-authorized
    ERCOT-151 §3 design round
    (``docs/PRECOMMIT-ercot176-offline-increment-2026-08-07.md``).

    The defect: the model's availability basis is only-OUT-is-out (correct —
    startability is physical, rule 13), so every non-outaged unit is offered
    to the LP at its base/wall-basis curve **whether or not serving the next
    MW would require a start**. P1's startup amortization is the only start
    term and is the wrong identification by ~30x (physical startup $/MW over
    min-run at LSL ~ $20-30/MWh). Measured SCED conduct prices that same
    capability start-inclusive — the CT tier's own ladder reads p50 $271-707.
    This builder closes the gap for the SLOW-START band, at that band's OWN
    measured ladder::

        boundary(bin) = 1 - pool_frac(bin)          # measured offline share
        rel           = (share_g - boundary) / (1 - boundary)
        target[g, t]  = min(interp(rel, ladder_q, ladder(bin)) x gas_day(t),
                            cap_frac x VOLL)

    on the merchant bid rows whose WITHIN-PLANT cumulative-capacity midpoint
    lies above the hour-bin's measured boundary.

    **It returns a bid LEVEL, not a markup** — the one deliberate departure
    from :func:`build_ercot_faststart_pool_markup`, whose construction this
    otherwise reproduces exactly against the ``"CC"`` block of the same
    artifact rather than ``"CT"`` (and without the ERCOT-89 span
    generalization, which is measured for the fast-start pool only). The
    level goes to ``run_energy_solve``'s ``p1_bid_max_target`` seam, which
    applies ``max(bid, target)`` AFTER the startup amortization
    (:func:`market_sim.pipeline.solve.apply_bid_max_target`).

    That is forced by rule 19 ``[R-ONE-MECH]``, not a style choice. The
    ``mc_bid_adjust`` seam is additive against a bid that already carries
    P1's monthly startup amortization (``mc_bid = mc_base + markup +
    adjust``), so an additive form of THIS tier would price the row at
    ``ladder + startup`` — double-counting the start, because the measured
    ladder is already start-INCLUSIVE. The bid-max seam exists for precisely
    this failure (the additive pjm-101/102 form over-expressed at CT -12
    TWh); here the amortization keeps ownership wherever it already prices
    the row above the measured corpus, and the measured level binds only
    where the model is cheaper. It also makes the no-markdown property
    structural: ``max`` can never LOWER a bid another measured surface set.

    The remaining differences from the fast-start pool are the physics band:

    * **Eligibility is unit physics** (rule 18 ``[R-PHYSICS]``), never a class
      tuple: ``OFFLINE_COMMIT_MIN_DOWN_HOURS_MIN <= min_down_hours <=
      OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX`` **and** ``min_run_hours <=
      OFFLINE_COMMIT_MIN_RUN_HOURS_MAX``, evaluated **per PLANT and inherited
      by its bid rows** — fleet assembly records unit physics on the
      ``committed`` tranche only, so at tranche-row grain the test is vacuous
      in both directions (ERCOT-176 §Amendment 2). CT rows fail by min-down (1 h) —
      the ERCOT-88 tier owns them, so the two tiers are **disjoint by
      physics**, never by agreement. ST_GAS and coal fail by min-run (24/48
      h), which is what keeps the ERCOT-91-``R`` steam lane closed rather
      than silently re-tested (rule 19 ``[R-ONE-MECH]``).
    * **Bid tranches only** (``econ*``/``peak*`` suffixes): must-run and
      committed blocks keep their own floor structure, so
      ``ercot_gas_commitment_bridge`` — which owns the ON committed CC
      min-gen state — stays disjoint by object (it sets a bound; this sets a
      price).
    * **Reconciling composition, never additive** (rule 19): the returned
      ``own_mask`` marks the row-hours this tier covers (a diagnostic and the
      seam-proof's disjointness handle); the LEVEL reconciles with every
      other surface and with the startup amortization via ``max``, so no
      mechanism stacks on another's residual and the start is counted once.
    * **An offer-availability, never a floor**: no ``min_gen`` is touched and
      the level can only RAISE a bid, so forced-energy (D-2) and
      off-window-binding (D-4) exposure is vacuous by construction — the
      rule-17 ``[R-FLOOR-WINDOW]`` hazard is structurally impossible.
    * **Above-LSL basis**: the ladder derives from the startable increment's
      above-LSL segments only, so below-LSL min-gen curve bottoms never enter.
    * **Year-scoped** (rule 13): no pooled fallback — a year absent from the
      artifact returns None and every surface stays byte-identical. Zero
      fitted scalars; the artifact is frozen against residuals (rule 23).
    * P1-only via the shared ``mc_bid_adjust`` seam: P0 run lengths and the
      startup-amortization coupling are untouched.

    Requires the cleared-share wall armed — the same recipe context the
    rule-19 enumeration was performed against; arming this leg without it is
    a hard error.
    """
    if not getattr(config, "ercot_offline_commit_offer", False):
        return None
    if config.iso != "ERCOT":
        return None
    if not getattr(config, "ercot_offer_surface_cleared_share", False):
        raise ValueError(
            "ercot_offline_commit_offer composes against the cleared-share "
            "wall's row pricing (PRECOMMIT-ercot176 §2 enumeration) — arm "
            "ercot_offer_surface_cleared_share too."
        )
    from market_sim.config.constants import (
        OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX,
        OFFLINE_COMMIT_MIN_DOWN_HOURS_MIN,
        OFFLINE_COMMIT_MIN_RUN_HOURS_MAX,
    )

    art_path = getattr(config, "ercot_offline_commit_offer_path", None)
    if not art_path:
        art_path = getattr(config, "ercot_faststart_pool_offer_path", None)
    if not art_path:
        from market_sim.config import paths as _paths

        art_path = str(_paths.CALIBRATION_DIR / "ercot_faststart_pool_condbinned.json")
    surface = json.loads(Path(art_path).read_text())
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    ladder_q = np.asarray(prov.get("ladder_quantiles", ()), dtype=float)
    if not edges or ladder_q.size == 0:
        raise ValueError(
            "ercot_offline_commit_offer: artifact carries no edges/quantiles "
            "— re-derive scripts/data/derive_ercot_faststart_pool.py"
        )
    # Same bin geometry as the wall artifacts by construction; assert against
    # the wall so a drifted re-derive is loud (the ERCOT-88 check).
    wall_path = getattr(config, "ercot_offer_surface_cleared_share_path", None)
    if not wall_path:
        from market_sim.config import paths as _paths

        wall_path = str(
            _paths.CALIBRATION_DIR / "ercot_dam_cleared_share_condbinned.json"
        )
    wall_prov = json.loads(Path(wall_path).read_text()).get("_provenance", {})
    wall_edges = tuple(float(x) for x in wall_prov.get("netload_pct_edges", ()))
    if wall_edges and wall_edges != edges:
        raise ValueError(
            "ercot_offline_commit_offer: artifact bin edges "
            f"{edges} != cleared-share wall edges {wall_edges} — re-derive "
            "scripts/data/derive_ercot_faststart_pool.py"
        )
    n_bins = len(edges) + 1

    tbl = surface.get("CC", {}).get("years", {}).get(str(year))
    if not tbl:  # year-scoped: no pooled fallback (rule 13)
        logger.info(
            "ERCOT offline-increment slow-start tier (ERCOT-176): year %s "
            "absent from the artifact — every surface byte-identical "
            "(year-scoped, rule 13)",
            year,
        )
        return None
    frac = np.asarray(tbl.get("pool_frac", ()), dtype=float)
    lad = tbl.get("ladder", ())
    if frac.size != n_bins or len(lad) != n_bins:
        return None
    bnd = 1.0 - np.clip(frac, 0.0, 1.0)  # (n_bins,)
    wall = np.array(
        [[float(pt[1]) for pt in lad_b] for lad_b in lad], dtype=float
    )  # (n_bins, n_q)

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    # Delivered-gas day series (the wall's own price normalizer).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Row universe: the wall's measured CC class scope (the ladder's own
    # measured class); ELIGIBILITY within it is unit physics.
    cc_groups = {
        grp for grp, key in _ERCOT_CLEARED_SHARE_CLASS_OF.items() if key == "CC"
    }
    prefixes: dict[str, list[int]] = {}
    for g, gen in enumerate(generators):
        if (getattr(gen, "plant_group", None) or "") not in cc_groups:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)

    # Unit physics is a property of the PLANT, and fleet assembly records it
    # on the ``committed`` tranche only — every ``econ*``/``peak*`` row (the
    # bid rows this tier prices) carries min_down = min_run = 0. So the
    # rule-18 band MUST be evaluated per plant and inherited by its bid rows;
    # read at tranche-row grain it is vacuous in both directions (a
    # ``>= 4 h`` test rejects every bid row, a ``<= 2 h`` test admits every
    # bid row) and would not be a physics gate at all.
    plant_md: dict[str, float] = {}
    plant_mr: dict[str, float] = {}
    for pref, rows in prefixes.items():
        plant_md[pref] = max(
            float(getattr(generators[g], "min_down_hours", 0) or 0) for g in rows
        )
        plant_mr[pref] = max(
            float(getattr(generators[g], "min_run_hours", 0) or 0) for g in rows
        )

    pmax = fleet_arrays.pmax
    voll_cap = float(
        getattr(config, "ercot_offer_surface_price_cap_frac", 0.95)
    ) * float(getattr(config, "voll", 5000.0))
    target_lvl = np.zeros_like(mc_base)
    own_mask = np.zeros_like(mc_base, dtype=bool)
    n_priced = 0
    mean_mc = mc_base.mean(axis=1)
    for pref, rows in prefixes.items():
        # Rule-18 physics gate, evaluated on the PLANT (see plant_md/plant_mr):
        # the SLOW-START band — a start that cannot happen inside the
        # operating hour, but still a within-day start-and-run decision.
        # Disjoint from the ERCOT-88 fast-start pool by min-down.
        md = plant_md[pref]
        mr = plant_mr[pref]
        if not (
            OFFLINE_COMMIT_MIN_DOWN_HOURS_MIN <= md <= OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX
        ):
            continue
        if mr > OFFLINE_COMMIT_MIN_RUN_HOURS_MAX:
            continue
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            # Committed and must-run blocks stay with their own floor
            # structure (rule 19 — the gas commitment bridge owns them);
            # only the bid tranches join this tier's universe.
            sfx = gen.unit_id.rpartition("_")[2]
            if not (sfx.startswith("econ") or sfx.startswith("peak")):
                continue
            mult_b = np.zeros(n_bins)
            has_b = np.zeros(n_bins, dtype=bool)
            for b in range(n_bins):
                pb = bnd[b]
                if not np.isfinite(pb) or pb >= 1.0 or s_g <= pb:
                    continue
                if not np.isfinite(wall[b]).all():
                    continue
                rel = (s_g - pb) / (1.0 - pb)
                mult_b[b] = float(np.interp(rel, ladder_q, wall[b]))
                has_b[b] = True
            if not has_b.any():
                continue
            mult_h = mult_b[hour_bin]  # (T,)
            mask = has_b[hour_bin]  # (T,)
            target = np.minimum(mult_h * gas_day, voll_cap)  # (T,) bid LEVEL
            # A non-positive entry is a no-op at the bid-max seam, so an
            # uncovered row-hour keeps whatever the rest of the stack priced.
            target_lvl[g, :] = np.where(mask, target, 0.0)
            own_mask[g, :] = mask
            n_priced += 1

    if not own_mask.any():
        logger.info(
            "ERCOT offline-increment slow-start tier (ERCOT-176): no "
            "slow-start row above the measured boundary — byte-identical"
        )
        return None
    logger.info(
        "ERCOT offline-increment slow-start tier (ERCOT-176): %d slow-start "
        "rows carry the offline above-LSL SCED2 ladder (year table %s; "
        "physics gate min_down in [%.0f, %.0f] h and min_run <= %.0f h; "
        "bid-LEVEL max() reconciliation, never additive)",
        n_priced,
        year,
        OFFLINE_COMMIT_MIN_DOWN_HOURS_MIN,
        OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX,
        OFFLINE_COMMIT_MIN_RUN_HOURS_MAX,
    )
    return target_lvl, own_mask


# Model tranche suffixes carrying the gas fleet's committed (LSL) block and the
# economic ramp — the rows the low-curve markdown reprices. ``econc``-prefixed
# suffixes are the N-slice smoothed econ ramp (``_econ_curve_steps``); ``econ``/
# ``econlo``/``econhi`` are the unsmoothed variants. Peak rungs are the TOP
# surface's rows and are never touched here (disjoint by construction, rule 19).
_LOWCURVE_ECON_SUFFIXES: tuple[str, ...] = ("econ", "econlo", "econhi")


def _lowcurve_row_family(unit_id: str) -> str | None:
    """Return ``"committed"`` / ``"econ"`` for a low-curve-eligible row, else None."""
    sfx = str(unit_id).rpartition("_")[2]
    if sfx == "committed":
        return "committed"
    if sfx in _LOWCURVE_ECON_SUFFIXES:
        return "econ"
    if sfx.startswith("econc") and sfx[5:].isdigit():
        return "econ"
    return None


def build_ercot_offer_surface_lowcurve_markdown(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    p0_dispatch: "np.ndarray | None" = None,
) -> "np.ndarray | None":
    """Build the P1-only conditional low-curve gas offer markdown ``(n_gen, T)``.

    The trough-price-formation MIRROR of
    :func:`build_ercot_offer_surface_conditional_markup`
    (``ScenarioConfig.ercot_offer_surface_lowcurve``): where the adopted top leg
    restores the measured offer distribution's UPPER tail in anticipated-tight
    net-load bins (clamped never to lower an offer), this leg restores its LOWER
    tail — the committed fleet's cheap segments the all-hours p50 band collapse
    deleted (clamped never to RAISE one). Measured bands from the same 60-Day
    DAM disclosure corpus, committed/online resources only
    (``scripts/data/derive_dam_offer_hrmults.py --low-curve-binned``):

    * ``binned_committed_p50`` — the Min-Gen-Cost (LSL block) multiplier per
      net-load bin. Committed units bid their LSL far below SRMC
      (cycling-avoidance / stay-on bidding), and MORE so in tight bins (CC p50
      0.585 loose -> 0.133 tight vs the model's resolved ~1.0). Applied to each
      plant's ``_committed`` tranche as a class-level ratio
      ``min(1, measured / resolved_committed)`` — plant heterogeneity rides on
      each plant's own heat rate, exactly the top leg's resolved-peak
      construction.
    * ``binned_low_body`` — the lower-body incremental-curve multiplier per
      curve-position band (rel < 0.22 / 0.44 / 0.67) per bin, matched to each
      plant's own rising econ ramp position-for-position (a cross-fleet RANK
      mapping conflated plant cheapness with curve position, eroding the
      mild-day evening margin and shuffling dispatch from coal — the v1 probe
      finding). With the keeper's delta-adjusted econ ramp already at/below the
      measured band medians, the <= 1 clamp leaves the econ rungs largely
      byte-identical — kept for completeness and forward honesty, not effect.

    ``p0_dispatch`` (the P0 base-cost solution, ``(n_gen, T)``) gates the
    markdown to plant-hours the model's OWN commitment discovery runs the plant
    (plant dispatch > 1 MW): the measured discounts are committed-unit bidding,
    and the model analogue of "committed" is its own P0 solve — the
    forward-regenerating construction the CAISO RA bridge and the PJM path-B
    reserve scoping already use. Without the gate, offline plants' discounted
    blocks undercut coal/ST in P1 and steal dispatch reality's committed-state
    bidding cannot (the v1 probe's -1.7 TWh coal shuffle). ``None`` applies the
    markdown ungated (unit tests / diagnostics).

    P1-only via the shared ``mc_bid_adjust`` seam: P0 run lengths, the
    startup-amortization coupling and every floor are byte-identical. Gas
    classes only (coal untouched — take-or-pay/passthrough governs its low
    bids, rule 19; peak rungs are the top leg's — disjoint). Zero fitted
    scalars: the trigger (net-load percentile) and every level (measured QSE
    quantiles) are rule-13-admissible, derived from source data only (rule 21)
    and frozen against residuals (rule 20).

    Returns ``None`` (P1 unchanged) when the flag is off, the ISO is not ERCOT,
    the surface JSON is absent, or no eligible rows exist.
    """
    if not getattr(config, "ercot_offer_surface_lowcurve", False):
        return None
    if config.iso != "ERCOT":
        return None
    path = getattr(config, "ercot_offer_surface_lowcurve_path", None)
    if not path:
        from market_sim.config import paths as _paths

        default = _paths.CALIBRATION_DIR / "offer_curve_dam_lowcurve_condbinned.json"
        if not default.exists():
            return None
        path = str(default)
    surface = _load_condbinned_surface(str(path))

    edges = tuple(float(x) for x in config.ercot_offer_surface_netload_pcts)
    json_edges = tuple(
        float(x) for x in surface.get("_provenance", {}).get("netload_pct_edges", ())
    )
    if json_edges and json_edges != edges:
        raise ValueError(
            "ercot_offer_surface_lowcurve: config netload_pcts "
            f"{edges} disagree with the derived surface's edges {json_edges} "
            "(re-derive with matching --low-curve-binned edges, or fix the config)."
        )
    n_bins = len(edges) + 1
    rel_bands = tuple(
        float(x)
        for x in surface.get("_provenance", {}).get(
            "rel_bands", (0.0, 0.22, 0.44, 0.67)
        )
    )

    heat_rate = np.asarray(fleet_arrays.heat_rate, dtype=float)
    hours = int(fuel_prices.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges) if len(edges) else np.array([])
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    curves = getattr(config, "offer_curve_by_group", None) or {}

    # Plant grouping: rows keyed by the unit_id prefix up to the tranche suffix,
    # families tagged committed/econ. All of a plant's rows (any suffix) feed
    # the P0 online mask.
    plant_committed: dict[str, int] = {}
    plant_econ: dict[str, list[int]] = {}
    plant_rows: dict[str, list[int]] = {}
    plant_cls: dict[str, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None)
        if cls not in surface or not isinstance(surface.get(cls), dict):
            continue
        key = str(gen.unit_id).rpartition("_")[0]
        plant_rows.setdefault(key, []).append(g)
        plant_cls[key] = cls
        fam = _lowcurve_row_family(gen.unit_id)
        if fam == "committed":
            plant_committed[key] = g
        elif fam == "econ":
            plant_econ.setdefault(key, []).append(g)
    if not plant_committed:
        return None

    markdown = np.zeros((len(generators), hours), dtype=float)
    n_repriced = 0
    for key, crow in plant_committed.items():
        cls = plant_cls[key]
        entry = surface[cls]
        committed_p50 = entry.get("binned_committed_p50") or []
        low_body = entry.get("binned_low_body") or []
        resolved_c = float((curves.get(cls) or {}).get("committed", 0.0) or 0.0)
        if resolved_c <= 0.0 or len(committed_p50) != n_bins:
            continue

        # P0 online gate: the plant runs this hour in the model's own base-cost
        # commitment discovery. None -> ungated (all hours eligible).
        if p0_dispatch is not None:
            rows = np.asarray(plant_rows[key], dtype=int)
            online = p0_dispatch[rows, :hours].sum(axis=0) > 1.0  # (T,)
        else:
            online = np.ones(hours, dtype=bool)

        # committed (LSL) tranche: class-level ratio per bin on the resolved band.
        ratio_c = np.ones(n_bins, dtype=float)
        for b in range(n_bins):
            v = committed_p50[b]
            if v is not None and np.isfinite(v):
                ratio_c[b] = min(1.0, float(v) / resolved_c)
        row_ratio = np.where(online, ratio_c[hour_bin], 1.0)  # (T,)
        if np.any(row_ratio < 1.0):
            energy = heat_rate[crow] * fuel_prices[crow, :hours]
            adj = energy * (row_ratio - 1.0)
            adj = np.maximum(adj, np.minimum(0.0, 1.0 - energy))
            if np.any(adj < 0.0):
                markdown[crow, :] = adj
                n_repriced += 1

        # econ ramp rungs: within-plant curve position -> measured rel-band
        # median (largely clamped to no-op on the keeper's delta-adjusted ramp).
        erows = plant_econ.get(key)
        if not erows or len(low_body) != n_bins:
            continue
        plant_hr = heat_rate[crow] / resolved_c  # the plant's base heat rate
        order = sorted(erows, key=lambda g: heat_rate[g])
        n_e = len(order)
        for i, g in enumerate(order):
            rel = (i + 0.5) / n_e * rel_bands[-1]  # position within [0, 0.67]
            k = int(np.searchsorted(np.asarray(rel_bands[1:]), rel, side="right"))
            if k >= len(rel_bands) - 1:
                continue
            rung_mult = heat_rate[g] / plant_hr
            if rung_mult <= 0.0:
                continue
            ratio_e = np.ones(n_bins, dtype=float)
            moved = False
            for b in range(n_bins):
                bands = low_body[b] or []
                v = bands[k] if k < len(bands) else None
                if v is not None and np.isfinite(v) and float(v) < rung_mult:
                    ratio_e[b] = float(v) / rung_mult
                    moved = True
            if not moved:
                continue
            row_ratio = np.where(online, ratio_e[hour_bin], 1.0)
            energy = heat_rate[g] * fuel_prices[g, :hours]
            adj = energy * (row_ratio - 1.0)
            adj = np.maximum(adj, np.minimum(0.0, 1.0 - energy))
            if np.any(adj < 0.0):
                markdown[g, :] = adj
                n_repriced += 1

    if n_repriced == 0 or not np.any(markdown < 0.0):
        return None
    loose = int((hour_bin == 0).sum())
    logger.info(
        "ERCOT conditional low-curve surface: marked down %d gas committed/econ "
        "rows across %d net-load bins (loosest bin %d/%d hours); P1-only, "
        "ratio clamped <= 1, %s",
        n_repriced,
        n_bins,
        loose,
        hours,
        "P0-online-gated" if p0_dispatch is not None else "ungated",
    )
    return markdown


def build_ercot_offer_surface_lowcurve_floorscoped_markdown(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    bridge_floor_mask: "np.ndarray | None",
) -> "np.ndarray | None":
    """Build the FLOOR-SCOPED committed-LSL P1 markdown ``(n_gen, T)`` (ERCOT-64).

    The enumerated price-side lever from the ERCOT-63 adjudication
    (``ScenarioConfig.ercot_offer_surface_lowcurve_floorscoped``;
    docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md §7): the measured
    committed-CC LSL (Min-Gen-Cost) bid — the SAME frozen ERCOT-62 quantile
    artifact the v2 markdown reads (``binned_committed_p50`` per net-load bin,
    ``offer_curve_dam_lowcurve_condbinned.json``) — applied to each gas plant's
    ``_committed`` tranche ONLY in the hours the ERCOT gas commitment bridge
    floors that plant (``bridge_floor_mask``), where the tranche genuinely
    plays its LSL role. The tranche-wide v2
    (:func:`build_ercot_offer_surface_lowcurve_markdown`) was probe-refuted
    even in composition with the bridge because it repriced the tranche's
    ABOVE-floor mid-merit capacity at the LSL bid in every online hour
    (spread compression, CT/CC overshoot — diagnosis §5/§7); this variant
    keeps every non-floored hour byte-identical.

    Scope deltas vs the v2 (deliberate, both remove refuted surface):

    * **Committed tranche only** — no econ low-body leg. The econ rungs were
      "largely clamp-inert, kept for completeness" in the v2; in bridged gap
      hours they are not playing an LSL role (the plant is held AT min-load
      by the floor), so there is nothing measured to reprice them to.
    * **Hour gate = the bridge's own floor mask, never P0-online.** P0-online
      is FALSE in bridged gap hours by construction — the floor exists
      because the base-cost P0 cycled the plant off — so the v2 gate zeroes
      the markdown exactly where this variant must act (the ERCOT-64 charter
      wiring trap #1). The mask is computed ONCE by the bridge and shared
      (``pipeline.commitment.build_ercot_gas_bridge_p1_preps``), never
      re-detected here.

    Rule-19 bookkeeping: a BID change on already-floored hours — no new
    floor, no D-2 id; composes with the bridge (the committed STATE) and is
    disjoint from the top-leg surface (peak rungs). Zero fitted scalars:
    trigger = the bridge floor mask + within-year net-load bin (both the
    model's own / forward-native), levels = the frozen measured QSE
    quantiles (rules 13/20/21). P1-only via the shared ``mc_bid_adjust``
    seam — P0 run lengths, the startup coupling and every floor
    byte-identical; the repriced energy part is floored at $1/MWh and the
    ratio clamped <= 1 (a markdown can only lower).

    PROBE VERDICT (ERCOT-64, 2026-07-13): provably INERT on the keeper — the
    bridge floor clips at the committed tranche's own capacity for every
    bridged plant, so the tranche is exactly pinned (``min_gen == pmax ×
    availability``) in this markdown's entire window and its bid coefficient
    cannot move the LP solution or duals (2023 probe byte-identical to the
    keeper). Recorded as the closure of the LSL price-side enumeration; see
    the ScenarioConfig field docstring and diagnosis §8.

    Args:
        bridge_floor_mask: ``(n_gen, T)`` boolean — the gen-hours the ERCOT
            gas commitment bridge floored (``bridge_floor > 0``). A plant is
            "in its LSL role" in hour ``t`` when ANY of its rows is floored.
            ``None`` / all-False returns ``None`` (no bridged hours — the
            markdown has no window).

    Returns ``None`` (P1 unchanged) when the flag is off, the ISO is not
    ERCOT, the surface JSON is absent, the mask is empty, or no committed row
    moves.
    """
    if not getattr(config, "ercot_offer_surface_lowcurve_floorscoped", False):
        return None
    if config.iso != "ERCOT":
        return None
    if bridge_floor_mask is None or not np.any(bridge_floor_mask):
        return None
    # Same frozen artifact + path field as the v2 (one measured source,
    # rule 23); the default resolves to the ERCOT-62 derive output.
    path = getattr(config, "ercot_offer_surface_lowcurve_path", None)
    if not path:
        from market_sim.config import paths as _paths

        default = _paths.CALIBRATION_DIR / "offer_curve_dam_lowcurve_condbinned.json"
        if not default.exists():
            return None
        path = str(default)
    surface = _load_condbinned_surface(str(path))

    edges = tuple(float(x) for x in config.ercot_offer_surface_netload_pcts)
    json_edges = tuple(
        float(x) for x in surface.get("_provenance", {}).get("netload_pct_edges", ())
    )
    if json_edges and json_edges != edges:
        raise ValueError(
            "ercot_offer_surface_lowcurve_floorscoped: config netload_pcts "
            f"{edges} disagree with the derived surface's edges {json_edges} "
            "(re-derive with matching --low-curve-binned edges, or fix the config)."
        )
    n_bins = len(edges) + 1

    heat_rate = np.asarray(fleet_arrays.heat_rate, dtype=float)
    hours = int(fuel_prices.shape[1])
    mask = np.asarray(bridge_floor_mask, dtype=bool)[:, :hours]
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges) if len(edges) else np.array([])
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    curves = getattr(config, "offer_curve_by_group", None) or {}

    # Plant grouping: identical prefix keying to the v2 builder — all of a
    # plant's rows (any tranche suffix) feed its floored-hours mask.
    plant_committed: dict[str, int] = {}
    plant_rows: dict[str, list[int]] = {}
    plant_cls: dict[str, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None)
        if cls not in surface or not isinstance(surface.get(cls), dict):
            continue
        key = str(gen.unit_id).rpartition("_")[0]
        plant_rows.setdefault(key, []).append(g)
        plant_cls[key] = cls
        if _lowcurve_row_family(gen.unit_id) == "committed":
            plant_committed[key] = g
    if not plant_committed:
        return None

    markdown = np.zeros((len(generators), hours), dtype=float)
    n_repriced = 0
    floored_plant_hours = 0
    for key, crow in plant_committed.items():
        cls = plant_cls[key]
        committed_p50 = surface[cls].get("binned_committed_p50") or []
        resolved_c = float((curves.get(cls) or {}).get("committed", 0.0) or 0.0)
        if resolved_c <= 0.0 or len(committed_p50) != n_bins:
            continue

        # THE scope: hours the bridge floors this plant (any of its rows).
        rows = np.asarray(plant_rows[key], dtype=int)
        floored = mask[rows, :].any(axis=0)  # (T,)
        if not np.any(floored):
            continue
        floored_plant_hours += int(floored.sum())

        # committed (LSL) tranche: class-level ratio per bin on the resolved
        # band — the v2 construction, gated to the floored hours.
        ratio_c = np.ones(n_bins, dtype=float)
        for b in range(n_bins):
            v = committed_p50[b]
            if v is not None and np.isfinite(v):
                ratio_c[b] = min(1.0, float(v) / resolved_c)
        row_ratio = np.where(floored, ratio_c[hour_bin], 1.0)  # (T,)
        if np.any(row_ratio < 1.0):
            energy = heat_rate[crow] * fuel_prices[crow, :hours]
            adj = energy * (row_ratio - 1.0)
            adj = np.maximum(adj, np.minimum(0.0, 1.0 - energy))
            if np.any(adj < 0.0):
                markdown[crow, :] = adj
                n_repriced += 1

    if n_repriced == 0 or not np.any(markdown < 0.0):
        return None
    logger.info(
        "ERCOT floor-scoped LSL markdown: %d gas committed tranches marked "
        "down over %d bridge-floored plant-hours (%d net-load bins); P1-only, "
        "committed rows only, ratio clamped <= 1",
        n_repriced,
        floored_plant_hours,
        n_bins,
    )
    return markdown
