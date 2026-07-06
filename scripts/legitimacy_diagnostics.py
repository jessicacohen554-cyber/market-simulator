"""Legitimacy diagnostic suite — D-1 / D-2 / D-4 / D-5 / D-9 (audit §7).

Implements the keeper-gating diagnostics from
``docs/model-legitimacy-audit-2026-07.md`` §7 against a calibration bundle
directory plus the committed dashboard payloads:

* **D-1 diurnal shape** — per plant-class hour-of-day mean profile, model vs
  CAMPD (``frontend/data/backcast/bench/<ISO>/<year>.json.gz``): profile
  correlation and the model/actual coefficient-of-variation ratio over the
  off-peak hours (h0-14 local). A peaker/intermediate class fails when
  r < 0.8 or model CV < 0.5 × actual CV — the caiso-42 flat-floor signature
  (model CV 0.000 vs actual 0.35-0.45).
* **D-2 forced-energy attribution** — TWh dispatched AT a binding
  ``min_gen`` floor, by class × mechanism, using the int8 mechanism-id array
  threaded through ``FleetArrays`` (``data.floor_mechanisms``). Gates:
  forced share < 10 % for peaker classes, < 30 % for any merchant class
  (nuclear / CHP-steam / coal-take-or-pay exempt).
* **D-4 off-window binding** — per driver-gated floor, the share of floored
  MWh outside its justified hour window; fail > 5 %.
* **D-5 forecast/backcast parity** — the mechanism set active for the same
  ScenarioConfig in ``mode="backcast"`` vs ``mode="forecast"`` (including
  entry-point wiring: a mechanism built only in ``scripts/run_calibration.py``
  and never in ``src/market_sim/runner.py`` is backcast-only in practice);
  every difference must be on the declared backcast-overlay list built from
  ``docs/backcast-measured-data-audit-2026-06.md``.
* **D-9 overlay quarantine** — assert the measured-outcome overlay probes are
  OFF in the bundle's ``run_config.json`` (``ct_deployment_overlay``,
  ``reliability_deployment_overlay``, ``ct_mustrun_per_plant``,
  ``ordc_reliability_deployment_mw``, ``caiso_gas_commitment_floor``) and
  that a non-ERCOT ISO resolves no offer band from the ERCOT-fitted generic
  fallback (``data/offer_curves.py`` ``_GAS_TRANCHE_SHARES`` + the
  ``getattr`` heat-rate-multiplier literals) — neutral/per-ISO bands only.
  ``--keepers`` sweeps every keeper bundle registered in
  ``frontend/data/backcast/keepers.json`` (the CI quarantine mode).
* **D-6 holdout quarantine (CI, in ``--keepers`` mode)** — assert NO
  registered bundle (keeper or probe) declares a solve year outside the
  2023-2025 calibration window unless its ISO carries a calibration-complete
  marker in ``frontend/data/backcast/calibration-complete.json`` (which
  authorizes the one-shot frozen-config holdout score of 2022 / H1-2026 —
  CLAUDE.md rule 22, amended 2026-07-04).
* **D-2 recompute-vs-committed (CI, in ``--keepers`` mode, gap G-06)** —
  re-derive each keeper's D-2 forced-energy shares from the bundle's own
  committed data (dashboard run payload + a deterministic floor rebuild) and
  diff against the committed ``<bundle>/legitimacy_diagnostics.json``. Fails
  only on a discrepancy between the two (a stale/hand-edited artifact) —
  never on a forced-share breach that the committed artifact already
  discloses (those are known NOT-YET findings, not this gate's job).
* **D-10 free-class-only rescore** — per (year, fuel) wind/solar renewable-
  bound provenance (``market_sim.data.renewables.renewable_bound_provenance``):
  flags rows riding the L1 delivered-outcome bound (§4) as ``PINNED`` so a
  C1-style pass on them is never quoted as forecast skill. Report-only —
  wind/solar are already advisory-only in ``calibration_verdict.py`` and
  never gate a keeper verdict.

Model dispatch source: ``<bundle>/dispatch/<year>_P2.parquet`` (falling back
to ``_P1``) when present; otherwise the committed dashboard run payload
(``frontend/data/backcast/runs/<id>.js``, located via the registry sidecar
whose ``bundle`` field matches). Floors source: ``<bundle>/floors/
<year>_<pass>.npz`` (written by ``run_calibration_full.py`` since this
change); otherwise rebuilt through the real calibration prep path
(``run_year(fleet_only=True)``) from the bundle's ``meta.json`` flags — the
same code the run used, minus the LP solves. The rebuild carries every
fleet-level floor; the P2-layer RA must-offer bridge needs the P1 solution
and is therefore absent from rebuilt floors (noted in the report).

Usage::

    python scripts/legitimacy_diagnostics.py --bundle <dir> --iso <ISO> \
        [--years 2023 2024 2025] [--report out.md] [--rebuild-floors]
    python scripts/legitimacy_diagnostics.py --keepers   # D-9/D-6/D-2 across keepers

Exits non-zero when any gate run in the invocation fails.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.data.floor_mechanisms import (  # noqa: E402
    D2_EXEMPT_MECHS,
    MECH_CAISO_GAS_COMMITMENT_FLOOR,
    MECH_CT_NETLOAD_DRAG,
    MECH_NAMES,
    MECH_RELIABILITY_FLOOR,
    NON_THERMAL_MECHS,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("legitimacy_diagnostics")

# ---------------------------------------------------------------------------
# Gate constants (audit §7). Every threshold cites its audit row.
# ---------------------------------------------------------------------------

# D-1: peaker/intermediate diurnal-shape gate (audit §7 D-1; §1.1 evidence).
D1_MIN_PROFILE_R: float = 0.8
D1_MIN_CV_RATIO: float = 0.5
D1_OFFPEAK_LAST_HOUR: int = 14  # off-peak window = local hours 0..14 inclusive
# Classes gated (peaker + intermediate duty); every class is still reported.
D1_GATED_CLASSES: tuple[str, ...] = ("CT_PEAKER", "ST_GAS")

# D-2: forced-share gates (audit §7 D-2 / §8 rule 19).
D2_PEAKER_CLASSES: tuple[str, ...] = ("CT_PEAKER",)
# Raised 0.10 -> 0.15 by owner amendment 2026-07-06 (CLAUDE.md rule 20 as
# amended; rubric v2.1). The calibration verdict (C8) gates each row's
# MEASURED forced_share against the rubric's own caps, so artifacts written
# under the old value re-score correctly without regeneration; this constant
# keeps future artifacts' embedded verdicts consistent with the rubric.
D2_PEAKER_MAX_SHARE: float = 0.15
D2_MERCHANT_MAX_SHARE: float = 0.30
# Materiality guard (owner directive, 2026-07-06): a merchant class is
# force-gated only when its own generation exceeds this share of total system
# load. A class dispatching < 2.5 % of load is not "the dispatch model" for
# anything, so a high forced SHARE on it is a near-zero-denominator artifact,
# not the rule-20 concern (floors propping up otherwise-economic dispatch). It
# is still reported per class (with load_share + an immaterial flag) but never
# raised to a FAIL. Total load = Σ payload fuelRows[*].m — the model's served-
# energy balance (per-fuel annual generation incl. signed net interchange).
D2_MATERIAL_MIN_LOAD_SHARE: float = 0.025
# Classes whose floors are structural must-run, exempt from the share gates
# (their mechanisms are also in D2_EXEMPT_MECHS; the class-level exemption
# covers CHP tranches floored by any mechanism).
D2_EXEMPT_CLASSES: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP", "nuclear")
# "At the floor" tolerance: quantization of the dashboard payload byte
# encoding (round(100*mw/nameplate) -> +-0.5% of nameplate) plus a relative
# band; a floor below FLOOR_MIN_MW is noise, not forcing.
D2_FLOOR_MIN_MW: float = 1.0
D2_REL_TOL: float = 0.02
# G-06: tolerance for the --keepers D-2 recompute-vs-committed check. The
# rebuild path (load_or_rebuild_floors) is deterministic given unchanged code
# + data, so a genuine drift shows up as many points of forced_share, not
# rounding noise from the 4-decimal-place summary; keep this tight so it
# still catches a real discrepancy.
D2_VERIFY_TOL: float = 0.0005

# D-4: justified hour windows per driver-gated floor mechanism, keyed
# (mechanism_id, plant_class) with None matching any class. Hours are local
# standard [start, end) — the model's t % 24 clock. Fail > 5 % off-window.
D4_MAX_OFFWINDOW_SHARE: float = 0.05
# CT reliability commitment is an evening-ramp phenomenon: the CAMPD
# derivation found overnight CT CF ~ 0 even at high net load
# (docs/caiso-ct-netload-drag-2026-06.md), so the justified window matches
# the ct_netload_drag ramp window [15, 22).
D4_WINDOWS: dict[tuple[int, str | None], tuple[int, int]] = {
    (MECH_RELIABILITY_FLOOR, "CT_PEAKER"): (15, 22),
    (MECH_RELIABILITY_FLOOR, "CT_CHP"): (15, 22),
    (MECH_CT_NETLOAD_DRAG, None): (15, 22),
    # Midday NG:NG slab window (h9-16) — the probe's own gate
    # (transmission.inject_caiso_gas_commitment_floor).
    (MECH_CAISO_GAS_COMMITMENT_FLOOR, None): (9, 17),
}

# D-9: overlay probes that must be OFF/zero in every keeper run_config.json
# (audit §7 D-9; measured-outcome pins, CLAUDE.md #13).
D9_FORBIDDEN_FLAGS: dict[str, object] = {
    "ct_deployment_overlay": False,
    "reliability_deployment_overlay": False,
    "ct_mustrun_per_plant": False,
    "ordc_reliability_deployment_mw": 0.0,
    "caiso_gas_commitment_floor": False,
}
# The ERCOT-fitted getattr fallback literals in the offer path
# (offer_curves.py:535-550): (plant groups, committed override, econ
# override + literal, peak override + literal).
D9_HR_FALLBACKS: tuple[tuple[tuple[str, ...], str, str, float, str, float], ...] = (
    (
        ("CC_REGULAR", "CC_CHP"),
        "cc_committed_hr_override",
        "cc_econ_hr_override",
        1.2,
        "cc_peak_hr_override",
        1.8,
    ),
    (
        ("ST_GAS",),
        "gas_st_committed_hr_override",
        "gas_st_econ_hr_override",
        1.0,
        "gas_st_peak_hr_override",
        1.5,
    ),
    (
        ("CT_CHP",),
        "ct_committed_hr_override",
        "ct_econ_hr_override",
        1.1,
        "ct_peak_hr_override",
        1.3,
    ),
)
# The ERCOT-mirrored generic gas tranche shares (offer_curves.py:130-143)
# engaged by config.gas_offer_curve on non-CAMPD fleets.
D9_GENERIC_SHARE_GROUPS: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "ST_GAS",
    "ST_CHP",
    "CT_PEAKER",
    "CT_CHP",
)

# D-6 holdout quarantine (CLAUDE.md rule 22, amended 2026-07-04): the in-sample
# calibration window. Any registered bundle carrying a solve year OUTSIDE this
# window is a holdout breach unless its ISO has a calibration-complete marker
# in frontend/data/backcast/calibration-complete.json (which authorizes the
# one-shot frozen-config holdout score). Extend only when a new year is
# formally promoted from holdout to in-sample with a new designated holdout.
D6_CALIBRATION_YEARS: frozenset[int] = frozenset({2023, 2024, 2025})
D6_MARKER_FILE = "frontend/data/backcast/calibration-complete.json"


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    """One diagnostic's verdict: rows for the report plus failure strings.

    ``summary`` carries per-(year, class) aggregate rows where the detail
    ``rows`` are finer-grained (D-2's rows are class × mechanism; its summary
    is the per-class total forced share the rule-19 gate and the rubric's C8
    criterion consume).
    """

    name: str
    rows: list[dict] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    summary: list[dict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return True when no gate failed."""
        return not self.failures


# ---------------------------------------------------------------------------
# D-1 — diurnal shape
# ---------------------------------------------------------------------------


def d1_shape_metrics(
    model_mw: np.ndarray, actual_mw: np.ndarray
) -> tuple[float, float, float]:
    """Return (profile r, model off-peak CV, actual off-peak CV) for a class.

    ``model_mw``/``actual_mw`` are aligned hourly class-total series
    (T = full 8760, or any multiple of 24 for the trivial-case tests). The
    profile is the hour-of-day mean; the CVs are taken over the profile's
    off-peak points h0-``D1_OFFPEAK_LAST_HOUR`` — the audit §1.1 statistic,
    where the caiso-42 flat floor scores model CV 0.000 vs actual 0.35-0.45
    (a per-sample pooled CV would hide the flat line behind the day gate's
    on/off day-to-day variance).
    """
    t = model_mw.size
    prof_m = model_mw.reshape(-1, 24).mean(axis=0)
    prof_a = actual_mw[:t].reshape(-1, 24).mean(axis=0)
    if prof_m.std() <= 0.0 or prof_a.std() <= 0.0:
        r = 0.0  # a constant profile carries no shape to correlate
    else:
        r = float(np.corrcoef(prof_m, prof_a)[0, 1])
    off = np.arange(24) <= D1_OFFPEAK_LAST_HOUR

    def _cv(x: np.ndarray) -> float:
        m = float(x.mean())
        return float(x.std() / m) if m > 1e-9 else 0.0

    return r, _cv(prof_m[off]), _cv(prof_a[off])


def run_d1(
    model_by_class: dict[str, np.ndarray],
    actual_by_class: dict[str, np.ndarray],
    year: int | str = "",
    gated_classes: tuple[str, ...] = D1_GATED_CLASSES,
) -> GateResult:
    """D-1 diurnal shape test over aligned per-class hourly series."""
    res = GateResult("D-1 diurnal shape")
    for klass in sorted(set(model_by_class) & set(actual_by_class)):
        model = np.asarray(model_by_class[klass], dtype=float)
        actual = np.asarray(actual_by_class[klass], dtype=float)
        if model.sum() <= 0.0 and actual.sum() <= 0.0:
            continue
        r, cv_m, cv_a = d1_shape_metrics(model, actual)
        ratio = cv_m / cv_a if cv_a > 1e-9 else float("nan")
        gated = klass in gated_classes
        fail_r = gated and r < D1_MIN_PROFILE_R
        fail_cv = gated and np.isfinite(ratio) and ratio < D1_MIN_CV_RATIO
        res.rows.append(
            {
                "year": year,
                "class": klass,
                "profile_r": round(r, 3),
                "model_offpeak_cv": round(cv_m, 3),
                "actual_offpeak_cv": round(cv_a, 3),
                "cv_ratio": round(ratio, 3) if np.isfinite(ratio) else None,
                "gated": gated,
                "verdict": "FAIL" if (fail_r or fail_cv) else "pass",
            }
        )
        if fail_r:
            res.failures.append(
                f"{year} {klass}: profile r {r:.3f} < {D1_MIN_PROFILE_R}"
            )
        if fail_cv:
            res.failures.append(
                f"{year} {klass}: off-peak CV ratio {ratio:.3f} "
                f"(model {cv_m:.3f} / actual {cv_a:.3f}) < {D1_MIN_CV_RATIO}"
            )
    return res


# ---------------------------------------------------------------------------
# D-2 — forced-energy attribution / D-4 — off-window binding
# ---------------------------------------------------------------------------


def at_floor_mask(
    dispatch: np.ndarray, min_gen: np.ndarray, npl: np.ndarray | None = None
) -> np.ndarray:
    """Boolean (n, T) mask of rows dispatched AT their binding min-gen floor.

    ``npl`` (per-row nameplate) widens the tolerance for payload-decoded
    dispatch, whose byte encoding quantizes to ~1 % of nameplate.
    """
    atol = np.full(dispatch.shape[0], D2_FLOOR_MIN_MW)
    if npl is not None:
        atol = atol + 0.01 * np.asarray(npl, dtype=float)
    return (min_gen > D2_FLOOR_MIN_MW) & (
        dispatch <= min_gen * (1.0 + D2_REL_TOL) + atol[:, None]
    )


def run_d2(
    dispatch: np.ndarray,
    min_gen: np.ndarray,
    mechanism: np.ndarray,
    klass: np.ndarray,
    year: int | str = "",
    npl: np.ndarray | None = None,
    ra_floor_missing: bool = False,
    total_load_mwh: float | None = None,
) -> GateResult:
    """D-2 forced-energy attribution over aligned (n, T) row arrays.

    Rows may be LP units or plants (floors aggregated per plant with the
    binding mechanism's id) — the arithmetic is identical. ``klass`` labels
    each row; forced energy is ``dispatch`` MWh in at-floor row-hours,
    attributed to the binding mechanism id.

    ``total_load_mwh`` (annual system load) activates the materiality guard:
    a merchant class whose own energy is < ``D2_MATERIAL_MIN_LOAD_SHARE`` of
    total load is immaterial — its forced share is reported but never a FAIL
    (owner directive 2026-07-06). ``None`` disables the guard (every class is
    gated, the pre-directive behaviour).
    """
    res = GateResult("D-2 forced-energy attribution")
    mask = at_floor_mask(dispatch, min_gen, npl)
    classes = np.unique(klass)
    mechs = [m for m in np.unique(mechanism[mask]) if m != 0]
    total_by_class = {
        k: float(np.clip(dispatch[klass == k], 0.0, None).sum()) for k in classes
    }
    forced_gated: dict[str, float] = {k: 0.0 for k in classes}
    for k in classes:
        rows = klass == k
        for m in mechs:
            sel = mask[rows] & (mechanism[rows] == m)
            mwh = float(dispatch[rows][sel].sum())
            if mwh <= 0.0:
                continue
            res.rows.append(
                {
                    "year": year,
                    "class": str(k),
                    "mechanism": MECH_NAMES.get(int(m), str(m)),
                    "forced_twh": round(mwh / 1e6, 4),
                    "class_total_twh": round(total_by_class[k] / 1e6, 4),
                    "share_of_class": round(mwh / total_by_class[k], 4)
                    if total_by_class[k] > 0
                    else 0.0,
                }
            )
            if int(m) not in D2_EXEMPT_MECHS and int(m) not in NON_THERMAL_MECHS:
                forced_gated[k] += mwh
    for k in classes:
        # The empty ('') class is the unclassified bucket: plants carrying no
        # CAMPD plant_group — nuclear / hydro / renewable must-run whose floors
        # are non-thermal/exempt by construction. It is NOT a merchant class,
        # so it never gates a forced-share limit, and its per-plant dispatch is
        # only reconstructible from the full dispatch frame (the run payload
        # carries these as scalar non-fossil aggregates, not per plant) — a
        # nuclear-inclusive '' denominator therefore diverges by an order of
        # magnitude between the parquet and payload paths. Excluding it keeps
        # the summary path-independent and every merchant row per-class
        # truthful (#1488, rule 20).
        if str(k) in D2_EXEMPT_CLASSES or str(k) == "" or total_by_class[k] <= 0.0:
            continue
        share = forced_gated[k] / total_by_class[k]
        limit = (
            D2_PEAKER_MAX_SHARE
            if str(k) in D2_PEAKER_CLASSES
            else D2_MERCHANT_MAX_SHARE
        )
        load_share = (
            total_by_class[k] / total_load_mwh
            if total_load_mwh and total_load_mwh > 0.0
            else None
        )
        immaterial = load_share is not None and load_share < D2_MATERIAL_MIN_LOAD_SHARE
        breach = share > limit and not immaterial
        res.summary.append(
            {
                "year": year,
                "class": str(k),
                "forced_twh": round(forced_gated[k] / 1e6, 4),
                "class_total_twh": round(total_by_class[k] / 1e6, 4),
                "forced_share": round(share, 4),
                "limit": limit,
                "load_share": round(load_share, 4) if load_share is not None else None,
                "immaterial": bool(immaterial),
                "lower_bound": bool(ra_floor_missing),
                "verdict": "FAIL" if breach else "pass",
            }
        )
        if breach:
            res.failures.append(
                f"{year} {k}: forced share {share:.1%} > {limit:.0%} "
                f"({forced_gated[k] / 1e6:.2f} of {total_by_class[k] / 1e6:.2f} TWh "
                "at binding non-exempt floors)"
            )
    if ra_floor_missing:
        res.notes.append(
            f"{year}: floors reconstructed via run_year(fleet_only=True) — the "
            "P2 RA must-offer bridge floor (needs the P1 solution) is NOT "
            "included, so CC/CT forced shares are lower bounds."
        )
    return res


def run_d4(
    dispatch: np.ndarray,
    min_gen: np.ndarray,
    mechanism: np.ndarray,
    klass: np.ndarray,
    year: int | str = "",
    npl: np.ndarray | None = None,
    windows: dict[tuple[int, str | None], tuple[int, int]] | None = None,
) -> GateResult:
    """D-4 off-window binding: floored MWh outside each declared window."""
    res = GateResult("D-4 off-window binding")
    windows = D4_WINDOWS if windows is None else windows
    mask = at_floor_mask(dispatch, min_gen, npl)
    t = dispatch.shape[1]
    hod = np.arange(t) % 24
    for (mech_id, k_filter), (start, end) in windows.items():
        in_window = (hod >= start) & (hod < end)
        sel_rows = (
            np.ones(dispatch.shape[0], dtype=bool)
            if k_filter is None
            else (klass == k_filter)
        )
        sel = mask[sel_rows] & (mechanism[sel_rows] == mech_id)
        total = float(dispatch[sel_rows][sel].sum())
        if total <= 0.0:
            continue
        off = sel & ~in_window[None, :]
        off_mwh = float(dispatch[sel_rows][off].sum())
        share = off_mwh / total
        label = f"{MECH_NAMES.get(mech_id, mech_id)}" + (
            f" × {k_filter}" if k_filter else ""
        )
        res.rows.append(
            {
                "year": year,
                "floor": label,
                "window": f"h{start}-{end - 1}",
                "floored_twh": round(total / 1e6, 4),
                "offwindow_twh": round(off_mwh / 1e6, 4),
                "offwindow_share": round(share, 4),
                "verdict": "FAIL" if share > D4_MAX_OFFWINDOW_SHARE else "pass",
            }
        )
        if share > D4_MAX_OFFWINDOW_SHARE:
            res.failures.append(
                f"{year} {label}: {share:.1%} of floored MWh outside its "
                f"justified window h{start}-{end - 1} (> "
                f"{D4_MAX_OFFWINDOW_SHARE:.0%})"
            )
    return res


# ---------------------------------------------------------------------------
# D-5 — forecast/backcast parity
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MechanismSpec:
    """One row of the D-5 parity registry.

    ``mode``: "backcast_only" / "forecast_only" / "both" — the *intended*
    availability by ScenarioConfig.mode. ``backcast_symbols`` /
    ``forecast_symbols``: builder symbols whose presence in the mode's entry
    script proves the mechanism is actually wired there (empty tuple = wired
    via shared modules, no entry-point call needed). ``declared``: on the
    declared backcast-overlay list (docs/backcast-measured-data-audit-2026-06
    .md), so a backcast/forecast difference is sanctioned.
    """

    name: str
    toggle: str | None  # scenario_config/calibration_flags key; None = always on
    mode: str
    declared: bool
    backcast_symbols: tuple[str, ...] = ()
    forecast_symbols: tuple[str, ...] = ()
    note: str = ""


# Declared backcast-overlay list, built from
# docs/backcast-measured-data-audit-2026-06.md (admissible measured-input
# overlays + the demoted default-off probes, which are declared *as probes* —
# D-9 separately enforces that they stay off in keepers).
D5_REGISTRY: tuple[MechanismSpec, ...] = (
    MechanismSpec(
        "historic_outage_overlay",
        "outage_source",
        "backcast_only",
        True,
        note="CAMPD outage windows (physical availability events)",
    ),
    MechanismSpec(
        "eia860_vintage_snapshot",
        None,
        "backcast_only",
        True,
        note="historical fleet vintage pin (runner.py:239 mode gate)",
    ),
    MechanismSpec(
        "retired_within_window_fleet",
        None,
        "backcast_only",
        True,
        note="within-window plant exits injected into the base fleet",
    ),
    MechanismSpec(
        "planned_additions_pipeline",
        None,
        "forecast_only",
        True,
        note="EIA-860 construction-committed pipeline — the declared "
        "forecast complement of the backcast fleet boundary",
    ),
    MechanismSpec(
        "renewable_cf_measured",
        None,
        "backcast_only",
        True,
        note="delivered EIA-930/HSL renewable CF upper bound (leakage L1)",
    ),
    MechanismSpec(
        "nuclear_flat_mustrun",
        None,
        "backcast_only",
        True,
        note="measured monthly nuclear CF + flat must-run floor (L3)",
    ),
    MechanismSpec(
        "ordc_floor_active_mask",
        None,
        "backcast_only",
        True,
        note="ERCOT scarcity-floor measured active-hours mask",
    ),
    MechanismSpec(
        "hydro_eia930_monthly",
        "hydro_eia930_monthly",
        "backcast_only",
        True,
        note="EIA-930 monthly hydro budgets (L6)",
    ),
    MechanismSpec(
        "gas_monthly_actuals",
        "gas_monthly_actuals",
        "backcast_only",
        True,
        note="F923 delivered monthly gas (admissible fuel input)",
    ),
    MechanismSpec(
        "gas_hub_basis_overlay",
        "gas_hub_basis_overlay",
        "backcast_only",
        True,
        note="measured monthly hub-spot basis overlay",
    ),
    MechanismSpec(
        "coal_plant_monthly_pricing",
        "coal_plant_monthly_pricing",
        "backcast_only",
        True,
        note="F923 per-plant delivered coal cost",
    ),
    MechanismSpec(
        "storage_as_commitment",
        "storage_as_commitment",
        "backcast_only",
        True,
        note="measured storage up-AS power reservation",
    ),
    MechanismSpec(
        "chp_export_floor_measured",
        "chp_export_floor_measured",
        "backcast_only",
        True,
        note="CHP export floor at measured class CF (mode-gated, L4)",
    ),
    MechanismSpec(
        "ct_mustrun_per_plant",
        "ct_mustrun_per_plant",
        "backcast_only",
        True,
        note="demoted probe — declared default-off; D-9 enforces off",
    ),
    MechanismSpec(
        "ct_deployment_overlay",
        "ct_deployment_overlay",
        "backcast_only",
        True,
        note="demoted probe — declared default-off; D-9 enforces off",
    ),
    MechanismSpec(
        "reliability_deployment_overlay",
        "reliability_deployment_overlay",
        "backcast_only",
        True,
        note="demoted probe — declared default-off; D-9 enforces off",
    ),
    MechanismSpec(
        "caiso_gas_commitment_floor",
        "caiso_gas_commitment_floor",
        "backcast_only",
        True,
        backcast_symbols=("inject_caiso_gas_commitment_floor",),
        note="demoted probe — declared default-off; D-9 enforces off",
    ),
    MechanismSpec(
        "reliability_floor",
        "reliability_floor",
        "both",
        True,
        backcast_symbols=("inject_reliability_floor",),
        forecast_symbols=("inject_reliability_floor",),
        note="declared admissible overlay (2026-06 audit); a wiring gap in "
        "the forecast entry is reported but sanctioned by the declaration",
    ),
    MechanismSpec(
        "gas_st_netload_drag",
        "gas_st_netload_drag",
        "both",
        False,
        backcast_symbols=("apply_gas_st_netload_drag_floor",),
        forecast_symbols=("apply_gas_st_netload_drag_floor",),
        note="forward-native drag — must be wired in BOTH modes",
    ),
    MechanismSpec(
        "ct_netload_drag",
        "ct_netload_drag",
        "both",
        False,
        backcast_symbols=("apply_ct_netload_drag_floor",),
        forecast_symbols=("apply_ct_netload_drag_floor",),
        note="forward-native drag — must be wired in BOTH modes",
    ),
    MechanismSpec(
        "caiso_ra_mustoffer",
        "caiso_ra_mustoffer",
        "both",
        False,
        backcast_symbols=("caiso_ra_mustoffer_min_gen",),
        forecast_symbols=("caiso_ra_mustoffer_min_gen",),
        note="RA must-offer is market design (mode-independent); the known "
        "w2-caiso-ra-p2 wiring gap makes it backcast-only in practice",
    ),
    MechanismSpec(
        "nyiso_synchronised_reserve",
        "nyiso_synchronised_reserve",
        "both",
        False,
        backcast_symbols=("reserve_adequacy_commit",),
        forecast_symbols=("reserve_adequacy_commit",),
        note="market-design reserve commitment — mode-independent by intent",
    ),
    MechanismSpec(
        "nyiso_local_selfsupply",
        "nyiso_local_selfsupply",
        "both",
        False,
        backcast_symbols=("inject_nyiso_local_selfsupply",),
        forecast_symbols=("inject_nyiso_local_selfsupply",),
        note="LMIC market-design rule — mode-independent by intent",
    ),
)


def _toggle_on(spec: MechanismSpec, cfg: dict) -> bool:
    """Return whether the spec's config toggle is on in a run_config dict."""
    if spec.toggle is None:
        return True
    val = cfg.get(spec.toggle)
    if spec.toggle == "outage_source":
        return val == "historic"
    return bool(val)


def run_d5(
    cfg: dict,
    iso: str,
    backcast_entry_src: str,
    forecast_entry_src: str,
) -> GateResult:
    """D-5 parity: diff the active mechanism sets, backcast vs forecast.

    ``cfg`` is the bundle's merged run-config (calibration_flags +
    scenario_config); the two ``*_src`` strings are the full text of the
    mode entry scripts (``scripts/run_calibration.py`` for backcast,
    ``src/market_sim/runner.py`` for forecast) so wiring is *measured*, not
    asserted — when the w2 gap is closed the diagnostic sees it.
    """
    res = GateResult("D-5 forecast/backcast parity")
    for spec in D5_REGISTRY:
        if not _toggle_on(spec, cfg):
            continue
        wired_b = all(s in backcast_entry_src for s in spec.backcast_symbols)
        wired_f = all(s in forecast_entry_src for s in spec.forecast_symbols)
        active_b = spec.mode != "forecast_only" and wired_b
        active_f = spec.mode != "backcast_only" and wired_f
        if active_b == active_f:
            continue
        side = "backcast-only" if active_b else "forecast-only"
        res.rows.append(
            {
                "mechanism": spec.name,
                "difference": side,
                "declared_overlay": spec.declared,
                "note": spec.note,
                "verdict": "declared" if spec.declared else "FAIL",
            }
        )
        if not spec.declared:
            res.failures.append(
                f"{spec.name}: active {side} for this config but NOT on the "
                "declared backcast-overlay list "
                "(docs/backcast-measured-data-audit-2026-06.md)"
            )
    return res


# ---------------------------------------------------------------------------
# D-9 — overlay quarantine
# ---------------------------------------------------------------------------


def run_d9(run_config: dict, iso: str, label: str = "") -> GateResult:
    """D-9 quarantine for one bundle's run_config.json (see module docstring)."""
    res = GateResult("D-9 overlay quarantine")
    sc = run_config.get("scenario_config", {})
    flags = run_config.get("calibration_flags", {})
    prefix = f"{label}: " if label else ""
    for key, required in D9_FORBIDDEN_FLAGS.items():
        val = sc.get(key, flags.get(key))
        ok = (not bool(val)) if required is False else (not val or float(val) == 0.0)
        res.rows.append(
            {
                "bundle": label or "-",
                "check": key,
                "value": val,
                "verdict": "pass" if ok else "FAIL",
            }
        )
        if not ok:
            res.failures.append(f"{prefix}{key} = {val!r} (must be {required!r})")
    if iso != "ERCOT":
        curves = sc.get("offer_curve_by_group") or {}
        if sc.get("gas_offer_curve"):
            uncovered = [g for g in D9_GENERIC_SHARE_GROUPS if g not in curves]
            if uncovered:
                res.failures.append(
                    f"{prefix}gas_offer_curve=True engages the ERCOT-mirrored "
                    f"generic tranche shares (_GAS_TRANCHE_SHARES) for "
                    f"{uncovered} — non-ERCOT ISOs must carry per-ISO or "
                    "neutral bands (offer_curves.py:130-143)"
                )
        for (
            groups,
            committed_key,
            econ_key,
            econ_lit,
            peak_key,
            peak_lit,
        ) in D9_HR_FALLBACKS:
            if sc.get(committed_key) is None:
                continue
            exposed = [g for g in groups if g not in curves]
            if not exposed:
                continue
            for key, lit in ((econ_key, econ_lit), (peak_key, peak_lit)):
                if sc.get(key) is None:
                    res.failures.append(
                        f"{prefix}{committed_key} set with {key} unset for "
                        f"{exposed}: the offer path falls back to the "
                        f"ERCOT-fitted literal {lit} (offer_curves.py:535-550)"
                    )
    return res


def run_d9_keepers(repo_root: Path) -> GateResult:
    """D-9 across every keeper bundle in frontend/data/backcast/keepers.json."""
    res = GateResult("D-9 overlay quarantine (all keepers)")
    keepers = json.loads(
        (repo_root / "frontend/data/backcast/keepers.json").read_text()
    )
    for run_id in keepers.get("keepers", []):
        side_path = repo_root / "frontend/data/backcast/registry" / f"{run_id}.json"
        side = json.loads(side_path.read_text())
        bundle = repo_root / side["bundle"]
        rc = json.loads((bundle / "run_config.json").read_text())
        sub = run_d9(rc, side.get("iso", ""), label=run_id)
        res.rows.extend(sub.rows)
        res.failures.extend(sub.failures)
    return res


def run_d2_keepers_verify(repo_root: Path) -> GateResult:
    """G-06: recompute D-2 forced-energy shares for every keeper, verbatim.

    Prior to this gate, CI trusted each bundle's committed
    ``legitimacy_diagnostics.json`` at face value — nothing re-derived it, so
    a stale artifact (hand-edited, or generated before a later code/data
    change) would sail through unnoticed. This recomputes D-2 straight from
    the bundle's own committed data (the dashboard run payload for dispatch
    when ``dispatch/*.parquet`` is gitignored-absent, per-plant floors
    rebuilt via ``run_year(fleet_only=True)`` when ``floors/*.npz`` is
    likewise absent — the same deterministic fallback ``diagnose_bundle``
    already uses for local `--bundle` runs) and diffs the recomputed
    ``forced_share`` against the committed one per (year, class).

    This is a staleness check, NOT a re-litigation of the D-2 threshold
    itself: a committed FAIL (e.g. the disclosed ercot32 CT_PEAKER 11.1%
    breach) that recomputes to the same FAIL is a `pass` here — it only
    fails when the recomputed number and the committed number disagree.
    """
    res = GateResult("D-2 forced-energy recompute (all keepers)")
    keepers_path = repo_root / "frontend/data/backcast/keepers.json"
    if not keepers_path.exists():
        return res
    keepers = json.loads(keepers_path.read_text())
    for run_id in keepers.get("keepers", []):
        side_path = repo_root / "frontend/data/backcast/registry" / f"{run_id}.json"
        side = json.loads(side_path.read_text())
        bundle = repo_root / side["bundle"]
        iso = side.get("iso", "")
        years = [int(y) for y in side.get("years", [])]
        committed_path = bundle / "legitimacy_diagnostics.json"
        if not committed_path.exists():
            res.notes.append(
                f"{run_id}: no committed legitimacy_diagnostics.json to verify "
                "against — skipped (see G-01/G-02)"
            )
            continue
        committed = json.loads(committed_path.read_text())
        committed_summary = {
            (row["year"], row["class"]): row
            for row in committed.get("diagnostics", {}).get("D2", {}).get("summary", [])
        }
        recomputed = diagnose_bundle(
            bundle, iso, years, repo_root=repo_root, only={"D2"}
        )
        d2 = next((r for r in recomputed if r.name.startswith("D-2")), None)
        recomputed_summary = (
            {(row["year"], row["class"]): row for row in d2.summary}
            if d2 is not None
            else {}
        )
        for key in sorted(set(committed_summary) | set(recomputed_summary)):
            year, klass = key
            c_row = committed_summary.get(key)
            r_row = recomputed_summary.get(key)
            # A class absent from one side's summary means run_d2's own
            # total_by_class[k] <= 0.0 filter dropped it there (e.g. a
            # non-thermal class with no dispatch in that recompute) — the
            # same substantive fact as an explicit forced_share of 0.0, not
            # a discrepancy. Comparing missing-as-zero still catches a real
            # drift (a class with a genuine nonzero share on one side and no
            # row on the other legitimately fails below).
            c_share = c_row["forced_share"] if c_row else 0.0
            r_share = r_row["forced_share"] if r_row else 0.0
            ok = abs(c_share - r_share) <= D2_VERIFY_TOL
            res.rows.append(
                {
                    "run": run_id,
                    "year": year,
                    "class": klass,
                    "committed_share": c_share,
                    "recomputed_share": r_share,
                    "verdict": "pass" if ok else "FAIL",
                }
            )
            if not ok:
                res.failures.append(
                    f"{run_id} {year} {klass!r}: committed forced_share "
                    f"{c_share} != recomputed {r_share} — committed "
                    "legitimacy_diagnostics.json is stale vs the bundle it "
                    "describes"
                )
    return res


# ---------------------------------------------------------------------------
# D-10 — free-class-only rescore (renewable-bound provenance)
# ---------------------------------------------------------------------------


def run_d10(
    iso: str, years: list[int], fuels: tuple[str, ...] = ("wind", "solar")
) -> GateResult:
    """D-10 free-class-only rescore: flag wind/solar rows pinned by L1.

    Report-only (wind/solar never gate a keeper verdict — they are advisory
    in ``calibration_verdict.py``), so this diagnostic never fails; it
    exists to make the L1 finding (docs/model-legitimacy-audit-2026-07.md
    §4: delivered EIA-930 output used as the renewable CF upper bound
    wherever no HSL/potential series exists) visible per bundle, per year,
    per fuel, so a C1-style pass on a "delivered_pinned" row is never quoted
    as forecast skill. Uses
    :func:`market_sim.data.renewables.renewable_bound_provenance` — the same
    logic the dispatch build consumes — never re-derives it.
    """
    from market_sim.data.renewables import (  # noqa: PLC0415 (optional heavy import)
        RENEWABLE_BOUND_DELIVERED_PINNED,
        renewable_bound_provenance,
    )

    res = GateResult("D-10 free-class-only rescore (renewable-bound provenance)")
    for year in years:
        for fuel in fuels:
            provenance = renewable_bound_provenance(iso, year, fuel)
            pinned = provenance == RENEWABLE_BOUND_DELIVERED_PINNED
            res.rows.append(
                {
                    "year": year,
                    "fuel": fuel,
                    "provenance": provenance,
                    "pinned": pinned,
                    "verdict": "PINNED (advisory-only, excluded from skill claims)"
                    if pinned
                    else "free",
                }
            )
    n_pinned = sum(1 for r in res.rows if r["pinned"])
    res.notes.append(
        f"{iso}: {n_pinned}/{len(res.rows)} wind/solar (year, fuel) rows ride "
        "the L1 delivered-outcome bound; their advisory-only C1 rows measure "
        "plumbing, not model skill (never gate the keeper verdict)."
    )
    return res


def load_calibration_complete(repo_root: Path) -> dict[str, dict]:
    """Return the per-ISO calibration-complete marker map (may be empty)."""
    path = repo_root / D6_MARKER_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("complete", {})


def run_d6_quarantine(repo_root: Path) -> GateResult:
    """D-6 holdout quarantine across EVERY registered bundle (CI mode).

    CLAUDE.md rule 22 (audit D-6, amended 2026-07-04): 2022 and H1-2026 are
    fully quarantined — no solves, no scoring, no data intake — until an ISO's
    calibration-complete marker exists in ``calibration-complete.json``. Any
    registry sidecar declaring a solve year outside ``D6_CALIBRATION_YEARS``
    for an unmarked ISO FAILs. Sweeps all registered runs (keepers AND
    probes): a quarantine breach is a breach wherever it is registered.
    """
    res = GateResult("D-6 holdout quarantine (all registered bundles)")
    complete = load_calibration_complete(repo_root)
    reg_dir = repo_root / "frontend/data/backcast/registry"
    for path in sorted(reg_dir.glob("*.json")):
        side = json.loads(path.read_text())
        iso = side.get("iso", "?")
        years = [int(y) for y in side.get("years", [])]
        breach = sorted(set(years) - D6_CALIBRATION_YEARS)
        if not breach:
            continue
        marked = iso in complete
        res.rows.append(
            {
                "run": path.stem,
                "iso": iso,
                "holdout_years": breach,
                "calibration_complete": marked,
                "verdict": "authorized one-shot" if marked else "FAIL",
            }
        )
        if not marked:
            res.failures.append(
                f"{path.stem}: solve year(s) {breach} outside the calibration "
                f"window {sorted(D6_CALIBRATION_YEARS)} with no {iso} "
                f"calibration-complete marker in {D6_MARKER_FILE} — holdout "
                "quarantine breach (CLAUDE.md rule 22)"
            )
    if not res.rows:
        res.notes.append(
            "no registered bundle carries a year outside "
            f"{sorted(D6_CALIBRATION_YEARS)} — quarantine intact."
        )
    return res


# ---------------------------------------------------------------------------
# Bundle / bench / payload data access
# ---------------------------------------------------------------------------


def _decode_cf_bytes(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Decode an 8760-byte CF%-encoded series to hourly MW.

    Bytes are ``round(100 * mw / nameplate)`` (render_calibration_html._b64);
    when the annual total is available the series is rescaled to it exactly,
    removing the byte quantization from every energy sum.
    """
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def load_bench(repo_root: Path, iso: str, year: int) -> dict[str, dict]:
    """Load the CAMPD bench file: plant id -> {group, zone, npl, mw}."""
    path = repo_root / "frontend/data/backcast/bench" / iso / f"{year}.json.gz"
    data = json.loads(gzip.open(path, "rt").read())
    plants = {}
    for pid, p in data["bench"]["plants"].items():
        if p.get("nodata") or not p.get("campd"):
            continue
        plants[pid] = {
            "group": p["group"],
            "zone": p.get("zone"),
            "npl": float(p.get("npl") or 0.0),
            "mw": _decode_cf_bytes(
                p["campd"], p.get("c_ann"), float(p.get("npl") or 0.0)
            ),
        }
    return plants


def find_registry_sidecar(repo_root: Path, bundle: Path) -> dict | None:
    """Find the dashboard registry sidecar whose ``bundle`` field matches."""
    rel = str(bundle.resolve().relative_to(repo_root.resolve()))
    reg_dir = repo_root / "frontend/data/backcast/registry"
    for path in sorted(reg_dir.glob("*.json")):
        side = json.loads(path.read_text())
        if side.get("bundle") == rel:
            return side
    return None


def load_payload_plants(
    repo_root: Path, sidecar: dict, year: int, bench: dict[str, dict]
) -> dict[str, np.ndarray]:
    """Decode the run payload's per-plant hourly model MW for one year."""
    txt = (repo_root / sidecar["file"]).read_text()
    blob = re.search(r'="(H4sI[^"]+)"', txt).group(1)
    run = json.loads(gzip.decompress(base64.b64decode(blob)))
    plants = run["years"][str(year)]["plants"]
    out = {}
    for pid, p in plants.items():
        if not p.get("m"):
            continue
        npl = bench.get(pid, {}).get("npl", 0.0)
        out[pid] = _decode_cf_bytes(p["m"], p.get("m_ann"), npl)
    return out


def load_payload_total_load_mwh(
    repo_root: Path, sidecar: dict, year: int
) -> float | None:
    """Total system load (~ served energy) for a payload year, in MWh.

    Sum of the per-fuel annual model generation ``fuelRows[*].m`` (TWh),
    including the signed net-interchange row — the model's served-energy
    balance, i.e. total load. This is the materiality denominator for the D-2
    force-gate (``D2_MATERIAL_MIN_LOAD_SHARE``). Returns ``None`` when the
    payload carries no ``fuelRows`` (older bundles / no sidecar), which leaves
    the guard disabled so no breach is hidden by a missing denominator.
    """
    txt = (repo_root / sidecar["file"]).read_text()
    match = re.search(r'="(H4sI[^"]+)"', txt)
    if match is None:
        return None
    run = json.loads(gzip.decompress(base64.b64decode(match.group(1))))
    rows = run.get("years", {}).get(str(year), {}).get("fuelRows") or []
    total_twh = sum((row.get("m") or 0.0) for row in rows)
    return total_twh * 1e6 if total_twh > 0.0 else None


def load_dispatch_parquet(bundle: Path, year: int):
    """Return the year's final-pass dispatch frame, or None when absent."""
    import pandas as pd

    for label in ("P2", "P1"):
        path = bundle / "dispatch" / f"{year}_{label}.parquet"
        if path.exists():
            return pd.read_parquet(path), label
    return None, None


def load_or_rebuild_floors(
    bundle: Path, iso: str, year: int, force_rebuild: bool = False
) -> tuple[dict, bool]:
    """Return unit-level floor arrays for a bundle-year.

    Prefers the persisted ``floors/<year>_<pass>.npz`` (P2 first — it carries
    the RA must-offer layer); otherwise rebuilds through
    ``run_year(fleet_only=True)`` with the bundle's own ``meta.json`` flags
    and caches the result as ``floors/<year>_rebuilt.npz``. Returns
    ``(arrays, ra_floor_missing)`` — the flag marks a rebuild, whose floors
    exclude the P1-dependent RA bridge.
    """
    floors_dir = bundle / "floors"
    if not force_rebuild:
        for name, ra_missing in (
            (f"{year}_P2.npz", False),
            (f"{year}_P1.npz", True),
            (f"{year}_rebuilt.npz", True),
        ):
            path = floors_dir / name
            if path.exists():
                with np.load(path, allow_pickle=False) as z:
                    return {k: z[k] for k in z.files}, ra_missing

    logger.info("%s %s: rebuilding floors via run_year(fleet_only=True)", iso, year)
    import inspect

    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    rename = {"commitment": "commitment_enabled"}
    kwargs = {}
    dropped = []
    for k, v in meta.items():
        k2 = rename.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
        else:
            dropped.append(k)
    logger.info("floors rebuild: %d flags passed, dropped %s", len(kwargs), dropped)
    gas_prices = meta.get("gas_prices", {})
    gas_price = float(gas_prices.get(str(year), gas_prices.get(year, 0.0)))
    state = run_year(
        year,
        iso,
        int(meta.get("hours", 8760)),
        gas_price,
        {},
        fleet_only=True,
        **kwargs,
    )
    fa = state["fleet_arrays"]
    if fa.min_gen is None:
        n, t = len(fa.unit_ids), int(fa.availability.shape[1])
        min_gen = np.zeros((n, t), dtype=np.float32)
        mech = np.zeros((n, t), dtype=np.int8)
    else:
        min_gen = fa.min_gen.astype(np.float32)
        mech = (
            fa.min_gen_mechanism
            if fa.min_gen_mechanism is not None
            else np.zeros(fa.min_gen.shape, dtype=np.int8)
        )
    groups = (
        fa.plant_group
        if fa.plant_group is not None
        else np.array([""] * len(fa.unit_ids), dtype=object)
    )
    arrays = {
        "min_gen": min_gen,
        "mechanism": np.asarray(mech, dtype=np.int8),
        "unit_ids": np.array(list(fa.unit_ids), dtype=str),
        "plant_code": np.asarray(fa.plant_code, dtype=np.int64),
        "plant_group": np.array([str(g) for g in groups], dtype=str),
    }
    floors_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(floors_dir / f"{year}_rebuilt.npz", **arrays)
    return arrays, True


def aggregate_floors_by_plant(
    arrays: dict,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Aggregate unit-level floors to plants: ids, floor sum, binding mech, class.

    The plant floor is the sum of its units' positive floors; the plant-hour
    mechanism is the id of the unit contributing the largest floor that hour
    (maximum-composition at plant level). Loops over plants, never hours.

    The plant class is the **most common non-empty** unit group in the plant —
    NOT the first unit's group. A single plant frequently mixes classified
    units with an unbinned/unclassified component (e.g. NEISO plant 546 carries
    8 ``ST_GAS`` units + 1 empty-group unit); taking the first unit's group let
    that lone empty label capture the whole plant into the ``''`` bucket, so its
    dispatch (and any binding floor) was mis-attributed away from its real
    merchant class and the class denominator was under-counted (#1488, rule 20).
    A plant whose units are *all* unclassified (nuclear / hydro / renewables,
    which carry no CAMPD plant_group) stays ``''`` — those non-thermal must-run
    rows are excluded from the merchant forced-share summary in ``run_d2``.
    """
    plant_code = np.asarray(arrays["plant_code"])
    keep = plant_code > 0
    pos = np.clip(np.asarray(arrays["min_gen"], dtype=float)[keep], 0.0, None)
    mech = np.asarray(arrays["mechanism"])[keep]
    groups = np.asarray(arrays["plant_group"]).astype(str)[keep]
    pc = plant_code[keep]
    order = np.argsort(pc, kind="stable")
    pos, mech, groups, pc = pos[order], mech[order], groups[order], pc[order]
    starts = np.flatnonzero(np.r_[True, pc[1:] != pc[:-1]])
    bounds = np.r_[starts, pc.size]
    t = pos.shape[1]
    n_plants = starts.size
    floor_sum = np.add.reduceat(pos, starts, axis=0)
    mech_plant = np.zeros((n_plants, t), dtype=np.int8)
    group_plant = np.empty(n_plants, dtype=object)
    hours_idx = np.arange(t)
    for i in range(n_plants):
        block = slice(bounds[i], bounds[i + 1])
        rel = np.argmax(pos[block], axis=0)
        mech_plant[i] = mech[block][rel, hours_idx]
        nonempty = groups[block][groups[block] != ""]
        if nonempty.size:
            vals, counts = np.unique(nonempty, return_counts=True)
            group_plant[i] = str(vals[counts.argmax()])
        else:
            group_plant[i] = ""
    mech_plant[floor_sum <= 0.0] = 0
    return pc[starts], floor_sum, mech_plant, group_plant.astype(str)


# ---------------------------------------------------------------------------
# Report / CLI
# ---------------------------------------------------------------------------


def _md_table(rows: list[dict]) -> str:
    """Render a list of dicts as a GitHub-flavored markdown table."""
    if not rows:
        return "_no rows_\n"
    cols = list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join(out) + "\n"


# Short ids for the machine artifact / rubric wiring: GateResult.name prefix
# -> key. The rubric's C7 reads D1; C8 reads D2's per-class summary.
_JSON_KEYS = {
    "D-10": "D10",  # checked before "D-1" (a prefix of "D-10") below
    "D-1": "D1",
    "D-2": "D2",
    "D-4": "D4",
    "D-5": "D5",
    "D-9": "D9",
    "D-6": "D6",
}


def build_json_report(
    results: list[GateResult], bundle: str, iso: str, years: list[int]
) -> dict:
    """Assemble the machine-readable diagnostics artifact for a bundle.

    This is the committed contract the calibration rubric's C7 (diurnal
    shape, D-1) and C8 (forced-energy share, D-2) criteria score from:
    ``scripts/calibration_verdict.py`` reads ``<bundle>/
    legitimacy_diagnostics.json`` — it never recomputes the diagnostics, so
    the S1 suite stays the single implementation. Gate thresholds are
    embedded so the verdict re-states, never re-types, them.
    """
    diagnostics = {}
    for res in results:
        key = next(
            (v for k, v in _JSON_KEYS.items() if res.name.startswith(k)), res.name
        )
        diagnostics[key] = {
            "name": res.name,
            "passed": res.passed,
            "rows": res.rows,
            "summary": res.summary,
            "failures": res.failures,
            "notes": res.notes,
        }
    return {
        "schema": "legitimacy-diagnostics/v1",
        "bundle": bundle,
        "iso": iso,
        "years": [int(y) for y in years],
        "diagnostics": diagnostics,
        "gates": {
            "d1_min_profile_r": D1_MIN_PROFILE_R,
            "d1_min_cv_ratio": D1_MIN_CV_RATIO,
            "d1_offpeak_last_hour": D1_OFFPEAK_LAST_HOUR,
            "d1_gated_classes": list(D1_GATED_CLASSES),
            "d2_peaker_max_share": D2_PEAKER_MAX_SHARE,
            "d2_merchant_max_share": D2_MERCHANT_MAX_SHARE,
            "d2_exempt_classes": list(D2_EXEMPT_CLASSES),
            "d4_max_offwindow_share": D4_MAX_OFFWINDOW_SHARE,
        },
    }


def render_report(
    results: list[GateResult], bundle: str, iso: str, years: list[int]
) -> str:
    """Render the full diagnostic report as markdown."""
    overall = all(r.passed for r in results)
    lines = [
        "# Legitimacy diagnostics report",
        "",
        f"Bundle: `{bundle}` · ISO: {iso} · years: {years}",
        f"Overall: **{'PASS' if overall else 'FAIL'}**",
        "",
        "Diagnostics per `docs/model-legitimacy-audit-2026-07.md` §7; "
        "generated by `scripts/legitimacy_diagnostics.py`.",
        "",
    ]
    for res in results:
        lines.append(f"## {res.name} — {'PASS' if res.passed else 'FAIL'}")
        lines.append("")
        if res.failures:
            lines.append("**Gate failures:**")
            lines.extend(f"- {f}" for f in res.failures)
            lines.append("")
        if res.notes:
            lines.extend(f"_{n}_" for n in res.notes)
            lines.append("")
        if res.summary:
            lines.append("**Per-class gate summary:**")
            lines.append("")
            lines.append(_md_table(res.summary))
        lines.append(_md_table(res.rows))
    return "\n".join(lines)


def diagnose_bundle(
    bundle: Path,
    iso: str,
    years: list[int] | None,
    repo_root: Path = REPO_ROOT,
    rebuild_floors: bool = False,
    only: set[str] | None = None,
) -> list[GateResult]:
    """Run the requested diagnostics against one calibration bundle."""
    run_config = json.loads((bundle / "run_config.json").read_text())
    meta_path = bundle / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    cfg = {
        **run_config.get("calibration_flags", {}),
        **run_config.get("scenario_config", {}),
    }
    if years is None:
        years = meta.get("years") or run_config.get("calibration_flags", {}).get(
            "years", []
        )
    only = only or {"D1", "D2", "D4", "D5", "D9", "D10"}
    sidecar = find_registry_sidecar(repo_root, bundle)
    results: list[GateResult] = []

    d1 = GateResult("D-1 diurnal shape")
    d2 = GateResult("D-2 forced-energy attribution")
    d4 = GateResult("D-4 off-window binding")
    for year in years:
        # Bench (per-plant nameplate + class) is needed by D-2/D-4 too, not
        # just D-1: it supplies each plant's ``npl`` for the payload dispatch
        # decode (``_decode_cf_bytes`` rescales to the annual total, falling
        # back to ``raw/100 * npl`` when a plant has no ``m_ann``) and for the
        # at-floor tolerance in ``at_floor_mask``. Loading it only for D-1 made
        # the D-2 recompute path (``only={"D2"}``) silently use a degraded
        # ``npl`` (``disp.max()`` / 0.0) and so disagree with the full
        # ``--bundle`` run that writes the committed artifact — the exact
        # path-divergence G-06 exists to catch (#1488).
        bench = load_bench(repo_root, iso, year) if {"D1", "D2", "D4"} & only else {}
        frame, pass_label = (
            load_dispatch_parquet(bundle, year)
            if {"D1", "D2", "D4"} & only
            else (None, None)
        )
        model_plants: dict[str, np.ndarray] = {}
        if frame is not None:
            sub = frame[frame["plant_code"] > 0]
            wide = (
                sub.groupby(["plant_code", "hour"], observed=True)["mw"]
                .sum()
                .unstack("hour", fill_value=0.0)
            )
            model_plants = {
                str(int(pc)): wide.loc[pc].to_numpy(dtype=float) for pc in wide.index
            }
            logger.info(
                "%s %s: model dispatch from dispatch/%s_%s.parquet (%d plants)",
                iso,
                year,
                year,
                pass_label,
                len(model_plants),
            )
        elif sidecar is not None and {"D1", "D2", "D4"} & only:
            model_plants = load_payload_plants(repo_root, sidecar, year, bench)
            logger.info(
                "%s %s: model dispatch from run payload %s (%d plants)",
                iso,
                year,
                sidecar["file"],
                len(model_plants),
            )

        if "D1" in only and model_plants and bench:
            model_by_class: dict[str, np.ndarray] = {}
            actual_by_class: dict[str, np.ndarray] = {}
            for pid, b in bench.items():
                if pid not in model_plants:
                    continue
                k = b["group"]
                model_by_class.setdefault(k, np.zeros(8760))
                actual_by_class.setdefault(k, np.zeros(8760))
                model_by_class[k] += model_plants[pid][:8760]
                actual_by_class[k] += b["mw"][:8760]
            sub_res = run_d1(model_by_class, actual_by_class, year=year)
            d1.rows.extend(sub_res.rows)
            d1.failures.extend(sub_res.failures)

        if {"D2", "D4"} & only and model_plants:
            arrays, ra_missing = load_or_rebuild_floors(
                bundle, iso, year, force_rebuild=rebuild_floors
            )
            pids, floor_sum, mech_plant, groups = aggregate_floors_by_plant(arrays)
            pid_strs = [str(int(p)) for p in pids]
            common = [i for i, p in enumerate(pid_strs) if p in model_plants]
            # Class totals need EVERY plant of the class, floored or not:
            # rows below carry all model plants, floors zero-filled outside
            # the floored set.
            klass_by_pid = dict(zip(pid_strs, groups))
            all_pids = [p for p in model_plants if p in klass_by_pid or p in pid_strs]
            # plants absent from the floors fleet (e.g. non-thermal payload
            # rows) are excluded — they carry no class in the model fleet.
            t = 8760
            disp = np.zeros((len(all_pids), t))
            floors = np.zeros((len(all_pids), t))
            mechs = np.zeros((len(all_pids), t), dtype=np.int8)
            klass = np.empty(len(all_pids), dtype=object)
            npl = np.zeros(len(all_pids))
            index = {p: i for i, p in enumerate(all_pids)}
            for p, i in index.items():
                disp[i] = model_plants[p][:t]
                klass[i] = klass_by_pid.get(p, "")
                npl[i] = bench.get(p, {}).get("npl", float(disp[i].max()))
            for j in common:
                p = pid_strs[j]
                if p in index:
                    floors[index[p]] = floor_sum[j][:t]
                    mechs[index[p]] = (
                        mech_plant[j][:, :t]
                        if mech_plant[j].ndim > 1
                        else mech_plant[j][:t]
                    )
            if "D2" in only:
                total_load_mwh = (
                    load_payload_total_load_mwh(repo_root, sidecar, year)
                    if sidecar is not None
                    else None
                )
                sub_res = run_d2(
                    disp,
                    floors,
                    mechs,
                    klass,
                    year=year,
                    npl=npl,
                    ra_floor_missing=ra_missing,
                    total_load_mwh=total_load_mwh,
                )
                d2.rows.extend(sub_res.rows)
                d2.failures.extend(sub_res.failures)
                d2.notes.extend(sub_res.notes)
                d2.summary.extend(sub_res.summary)
            if "D4" in only:
                sub_res = run_d4(disp, floors, mechs, klass, year=year, npl=npl)
                d4.rows.extend(sub_res.rows)
                d4.failures.extend(sub_res.failures)

    if "D1" in only:
        results.append(d1)
    if "D2" in only:
        results.append(d2)
    if "D4" in only:
        results.append(d4)
    if "D5" in only:
        backcast_src = (repo_root / "scripts/run_calibration.py").read_text()
        forecast_src = (repo_root / "src/market_sim/runner.py").read_text()
        results.append(run_d5(cfg, iso, backcast_src, forecast_src))
    if "D9" in only:
        results.append(run_d9(run_config, iso, label=bundle.name))
    if "D10" in only and years:
        results.append(run_d10(iso, list(years)))
    return results


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--bundle", type=Path, help="calibration bundle dir")
    parser.add_argument("--iso", help="ISO id (ERCOT/CAISO/PJM/MISO/NYISO/NEISO)")
    parser.add_argument("--years", type=int, nargs="*", default=None)
    parser.add_argument(
        "--only",
        nargs="*",
        choices=["D1", "D2", "D4", "D5", "D9", "D10"],
        default=None,
        help="run a subset of the diagnostics",
    )
    parser.add_argument(
        "--rebuild-floors",
        action="store_true",
        help="force floor reconstruction even when floors/*.npz exists",
    )
    parser.add_argument(
        "--keepers",
        action="store_true",
        help="run the D-9 quarantine, D-6 holdout quarantine, and the D-2 "
        "recompute-vs-committed staleness check across every keeper bundle "
        "(CI mode)",
    )
    parser.add_argument("--report", type=Path, help="write a markdown report")
    parser.add_argument(
        "--json-out",
        type=Path,
        help="write the machine-readable diagnostics artifact (the committed "
        "rubric contract for C7/C8 is <bundle>/legitimacy_diagnostics.json)",
    )
    args = parser.parse_args(argv)

    results: list[GateResult] = []
    bundle_label, iso, years = "-", args.iso or "-", args.years or []
    if args.keepers:
        results.append(run_d9_keepers(REPO_ROOT))
        results.append(run_d6_quarantine(REPO_ROOT))
        results.append(run_d2_keepers_verify(REPO_ROOT))
        bundle_label = "all keepers"
    if args.bundle:
        if not args.iso:
            parser.error("--iso is required with --bundle")
        bundle = args.bundle.resolve()
        results.extend(
            diagnose_bundle(
                bundle,
                args.iso,
                args.years,
                rebuild_floors=args.rebuild_floors,
                only=set(args.only) if args.only else None,
            )
        )
        bundle_label = str(bundle)
        if not years:
            meta_path = bundle / "meta.json"
            if meta_path.exists():
                years = json.loads(meta_path.read_text()).get("years", [])
    if not results:
        parser.error("nothing to do: pass --bundle/--iso and/or --keepers")

    report = render_report(results, bundle_label, iso, years)
    print(report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report)
        logger.info("report written to %s", args.report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(build_json_report(results, bundle_label, iso, years), indent=1)
            + "\n"
        )
        logger.info("machine artifact written to %s", args.json_out)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
