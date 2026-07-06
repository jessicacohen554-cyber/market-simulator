#!/usr/bin/env python3
"""D-11 knob-perturbation Jacobian for one calibration keeper (scalar-remediation
program batch B-DIAG-2; see docs/handoffs/scalar-remediation-plan-2026-07.md §4.3
and docs/model-legitimacy-audit-2026-07.md §7 D-11).

For a keeper bundle, reads the DOF ledger's ``free_parameters`` (built by
``scripts/build_dof_ledger.py`` if the bundle's attestation doesn't carry one
yet), perturbs each numeric knob +-10% one at a time, re-solves ONE year
(2024 only — CLAUDE.md rule 16's probe exemption; never touches the 2022/
H1-2026 quarantine, rule 22), and scores the result against the same
class-TWh / dispatch-shape / price machinery ``scripts/derive_offer_curve_
jacobian.py`` already uses for its regression targets — reused here directly
(``Bundle``, ``class_totals``, ``bundle_metrics``) rather than re-derived, so
this diagnostic and the offer-curve Jacobian never disagree about what a
class's TWh or dispatch-shape NRMSE means.

Knob population (today's harness; extend as the DOF ledger grows per-field
override plumbing for other families):
  * every ``offer_curve_by_group[class][band]`` heat-rate-band multiplier for
    the four price bands (committed/econ_low/econ_high/peak) — the dominant
    ~40-54-knob-per-ISO population the ledger's `offer_curve_by_group` entry
    covers (audit C-8/C-11/C-13).
  * top-level scalar ScenarioConfig knobs at a non-default value:
    ``wefor_multiplier``, ``battery_dispatch_adder``,
    ``pumped_storage_dispatch_adder``.
  Constants.py-resident families the ledger also lists (coal sigmoid
  parameters, CHP_BTM_PCT_BY_SECTOR, CAISO TAC weights,
  IMPORT/EXPORT_TRANCHES, netload-drag hinge coefficients) are not
  yet perturbable through the generic ``prb_overrides`` override channel at
  per-parameter granularity and are out of scope for this batch; each needs
  its own ScenarioConfig passthrough before it can join this harness.

Headline metrics per knob (finite-difference sensitivity, ``(plus - minus) /
(2 x step)``):
  * ``twh_per_unit.<CLASS>`` — d(model class TWh)/d(knob)     [class-TWh, required]
  * ``c2_gas_twh_per_unit`` / ``c2_coal_twh_per_unit`` — d(gas/coal family
    TWh)/d(knob)                                              [C2 sysvol proxy]
  * ``c3b_price_nrmse_per_unit`` — d(monthly price NRMSE)/d(knob) [C3b price-
    shape proxy; computed directly from system.parquet + the committed
    actual-LMP reference, mirroring calibration_verdict.score_price_shape's
    metric exactly but without building the full dashboard payload]
  * ``c4_shape_gas_nrmse_per_unit`` / ``c4_shape_coal_nrmse_per_unit`` —
    d(hourly non-CHP gas/coal NRMSE vs EIA-930)/d(knob) [C4 dispatch-shape
    proxy; docj's "shape" block]

Every solve is labelled a diagnostic (``"diagnostic": true`` in the emitted
JSON) — never a keeper (CLAUDE.md rules 16/26: probes are quarantine-exempt
but never promoted). Cost: O(2 x n_knobs) one-year LP solves plus one
baseline solve, so real batches run this per ISO as a background job
(``--one-sided`` halves the cost when the two-sided estimate isn't needed).

Usage::

    python scripts/knob_jacobian.py results/calibration/<bundle> --iso ERCOT
    python scripts/knob_jacobian.py results/calibration/<bundle> --iso ERCOT \\
        --max-knobs 5 --out /tmp/knob_jacobian_smoke.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import scripts.derive_offer_curve_jacobian as docj  # noqa: E402
from scripts.build_dof_ledger import build_ledger  # noqa: E402
from scripts.calibration_verdict import COAL_CLASSES, GAS_CLASSES  # noqa: E402
from scripts.calibration_verdict import _nrmse as _cv_nrmse  # noqa: E402

# D-11 spec: one year only, labelled diagnostic (rule 16 probe exemption).
DEFAULT_YEAR = 2024
PERTURB_FRAC = 0.10

# Top-level scalar ScenarioConfig fields the ledger flags as free parameters
# with a directly-perturbable numeric value (see module docstring: the
# constants.py-resident families need per-field override plumbing first).
_SCALAR_KNOB_FIELDS: dict[str, float] = {
    "wefor_multiplier": 1.0,  # neutral value; only perturb when != default
    "battery_dispatch_adder": 0.0,
    "pumped_storage_dispatch_adder": 0.0,
}

# The committed actual-LMP reference (scripts/derive_actual_lmp.py's product);
# used for the C3b monthly price-NRMSE proxy. NOT scripts/derive_offer_curve_
# jacobian.py's (stale, pre-W1-reorg) ACTUAL_LMP_JSON constant.
ACTUAL_LMP_JSON = REPO / "data" / "raw" / "_validation-source" / "actual_lmp.json"


@dataclass(frozen=True)
class Knob:
    """One perturbable scalar: an offer-curve band multiplier or a top-level
    ScenarioConfig field."""

    name: str
    field: str  # ScenarioConfig field name this knob lives in
    value: float
    klass: str | None = None  # offer_curve_by_group class (None for scalars)
    band: str | None = None  # offer_curve_by_group band (None for scalars)


# ---------------------------------------------------------------------------
# Knob discovery
# ---------------------------------------------------------------------------
def offer_band_knobs(curves: dict) -> list[Knob]:
    """Every price-band multiplier in ``offer_curve_by_group`` as a ``Knob``.

    Restricted to the four price bands (``docj.PRICE_BANDS``) — the same
    bands the offer-curve Jacobian's trust region governs; ``econ_low_share``
    / ``pct_peaking`` are fractions of a different unit and excluded, mirroring
    ``derive_offer_curve_jacobian.py``'s own convention.
    """
    out = []
    for klass in sorted(curves):
        for band in docj.PRICE_BANDS:
            v = curves[klass].get(band)
            if v is None:
                continue
            out.append(
                Knob(
                    name=f"offer_curve_by_group.{klass}.{band}",
                    field="offer_curve_by_group",
                    value=float(v),
                    klass=klass,
                    band=band,
                )
            )
    return out


def scalar_knobs(scenario_config: dict) -> list[Knob]:
    """Top-level scalar ScenarioConfig knobs at a non-default (engaged) value."""
    out = []
    for field, default in _SCALAR_KNOB_FIELDS.items():
        v = scenario_config.get(field)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v != default:
            out.append(Knob(name=field, field=field, value=float(v)))
    return out


def discover_knobs(bundle: Path, iso: str) -> list[Knob]:
    """All perturbable knobs for a bundle, cross-checked against its DOF ledger.

    The ledger (built fresh, not read from a possibly-stale attestation) says
    WHICH parameter families are free; the actual current values come from
    ``run_config.json`` (the ledger's own ``offer_curve_by_group`` display
    value is band names, not levels — see ``build_dof_ledger.config_entries``).
    A bundle whose ledger carries no ``offer_curve_by_group``/scalar entry at
    all still perturbs nothing (empty ``entries`` -> empty knob list), so this
    never invents a knob the ledger doesn't attest to.
    """
    sc = json.loads((bundle / "run_config.json").read_text()).get("scenario_config", {})
    ledger = build_ledger(bundle, iso)
    ledger_fields = {e["name"] for e in ledger["entries"]}
    knobs: list[Knob] = []
    if "offer_curve_by_group" in ledger_fields:
        knobs += offer_band_knobs(sc.get("offer_curve_by_group") or {})
    for k in scalar_knobs(sc):
        if k.field in ledger_fields:
            knobs.append(k)
    return knobs


# ---------------------------------------------------------------------------
# Perturbation
# ---------------------------------------------------------------------------
def perturbed_override(knob: Knob, direction: int, frac: float = PERTURB_FRAC) -> dict:
    """The single-field ``prb_overrides`` dict for one +-frac move of ``knob``.

    ``direction`` is +1 or -1. Offer-band knobs carry the WHOLE (single-leaf-
    changed) ``offer_curve_by_group`` dict, since the generic override channel
    (``ScenarioConfig.with_overrides`` = ``dataclasses.replace``) replaces a
    field wholesale rather than deep-merging it.
    """
    if direction not in (1, -1):
        raise ValueError(f"direction must be +1 or -1, got {direction!r}")
    delta = knob.value * frac * direction
    new_value = round(knob.value + delta, 6)
    if knob.field == "offer_curve_by_group":
        return {"offer_curve_by_group": {knob.klass: {knob.band: new_value}}}
    return {knob.field: new_value}


def _safe_slug(name: str) -> str:
    """Filesystem-safe slug for a knob name (used as its solve-dir basename)."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "knob"


# ---------------------------------------------------------------------------
# Solve (the real, expensive step — mockable via the ``solve_fn`` parameter)
# ---------------------------------------------------------------------------
def solve_year(
    bundle: Path,
    iso: str,
    year: int,
    overrides: dict,
    out_dir: Path,
    reference: dict | None = None,
) -> Path:
    """Real one-year replay solve of ``bundle``'s keeper config plus ``overrides``.

    Mirrors ``scripts/replay_keeper.py``'s ``meta.json`` -> kwargs mapping so
    this always replays the committed keeper's exact mechanism set (never a
    hand-rebuilt config that could drift), restricted to ``year`` only and
    with ``overrides`` layered on top via the generic ``prb_overrides``
    channel — the same channel ``replay_keeper.py --set`` uses for single-
    delta A/B probes.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import replay_keeper  # noqa: PLC0415
    import run_calibration_full as rcf  # noqa: PLC0415

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = replay_keeper.build_kwargs(meta)
    kwargs["years"] = [int(year)]
    kwargs["iso"] = iso
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = reference if reference is not None else rcf._load_reference()
    kwargs["run_dir"] = out_dir
    prb = dict(kwargs.get("prb_overrides") or {})
    prb.update(overrides)
    kwargs["prb_overrides"] = prb
    kwargs["note"] = (
        f"D-11 knob-jacobian diagnostic solve of {bundle.name} {year} "
        f"(overrides: {sorted(overrides)}) — advisory, never a keeper."
    )
    return rcf.solve_and_persist(**kwargs)


# ---------------------------------------------------------------------------
# Score (parquet-native; reuses derive_offer_curve_jacobian's machinery)
# ---------------------------------------------------------------------------
def _load_bundle(path: Path) -> docj.Bundle:
    """Build one ``docj.Bundle`` for an already-known solved dir.

    Mirrors ``discover_bundles``'s per-item body for a single path rather than
    scanning a directory of many bundles.
    """
    cfg = json.loads((path / "run_config.json").read_text())
    sc = cfg.get("scenario_config", {})
    meta = (
        json.loads((path / "meta.json").read_text())
        if (path / "meta.json").exists()
        else {}
    )
    git = cfg.get("git") or {}
    disp = sorted((path / "dispatch").glob("*_P1.parquet"))
    return docj.Bundle(
        name=path.name,
        path=path,
        iso=meta.get("iso") or sc.get("iso") or "?",
        timestamp=meta.get("timestamp") or cfg.get("timestamp") or "",
        years=sorted(int(f.name.split("_")[0]) for f in disp),
        curves=sc.get("offer_curve_by_group") or {},
        note=str(cfg.get("model_changes_note") or ""),
        sha=git.get("sha") or meta.get("git_sha") or "",
        scenario={k: v for k, v in sc.items() if k != "offer_curve_by_group"},
    )


def _monthly_price_nrmse(b: docj.Bundle, year: int) -> float | None:
    """C3b proxy: monthly load-weighted price NRMSE vs the actual-LMP reference.

    Mirrors ``calibration_verdict.score_price_shape``'s metric exactly (same
    ``_nrmse`` masked-mean implementation, reused directly), computed from
    ``system.parquet`` instead of the rendered dashboard payload — cheap
    enough to run once per +-10% knob solve instead of building the full
    per-run JS payload every time.
    """
    sysp_path = b.path / "system.parquet"
    if not sysp_path.exists() or not ACTUAL_LMP_JSON.exists():
        return None
    actual_all = json.loads(ACTUAL_LMP_JSON.read_text()).get(b.iso) or {}
    actual = (actual_all.get(str(year)) or {}).get("rt_mon") or (
        actual_all.get(str(year)) or {}
    ).get("da_mon")
    if not actual:
        return None
    sysp = pd.read_parquet(
        sysp_path, columns=["year", "pass", "hour", "price", "demand"]
    )
    sysp = sysp[sysp["year"] == year]
    if "pass" in sysp.columns and (sysp["pass"] == "P1").any():
        sysp = sysp[sysp["pass"] == "P1"]
    if sysp.empty:
        return None
    month = np.searchsorted(
        docj._MONTH_START_HOUR, sysp["hour"].to_numpy(), side="right"
    ).clip(1, 12)
    g = sysp.assign(month=month, pd_=sysp["price"] * sysp["demand"]).groupby("month")
    agg = g.agg(pd_=("pd_", "sum"), d=("demand", "sum"))
    model_mon = [
        float(agg.loc[m, "pd_"] / agg.loc[m, "d"])
        if m in agg.index and agg.loc[m, "d"] > 0
        else None
        for m in range(1, 13)
    ]
    return _cv_nrmse(model_mon, list(actual))


def score_bundle(bundle_dir: Path, year: int, cache: dict | None = None) -> dict:
    """Headline metrics for one solved bundle-year: raw values, not deltas.

    Returns ``{"twh": {class: TWh}, "shape": {"gas"/"coal"/"cf_emd": NRMSE},
    "price_nrmse": float|None}``. ``twh``/``shape`` reuse ``derive_offer_
    curve_jacobian``'s ``class_totals``/``bundle_metrics`` verbatim.
    """
    cache = {} if cache is None else cache
    b = _load_bundle(bundle_dir)
    totals = docj.class_totals(b, cache)
    twh = {
        str(r.klass): float(r.model_twh)
        for r in totals.itertuples()
        if int(r.year) == year
    }
    metrics = docj.bundle_metrics(b, cache)
    shape = {
        str(r.key): float(r.value)
        for r in metrics.itertuples()
        if int(r.year) == year and r.metric == "shape"
    }
    return {
        "twh": twh,
        "shape": shape,
        "price_nrmse": _monthly_price_nrmse(b, year),
    }


# ---------------------------------------------------------------------------
# Jacobian assembly
# ---------------------------------------------------------------------------
def _family_twh(twh: dict, classes: tuple[str, ...]) -> float:
    return sum(twh.get(c, 0.0) for c in classes)


def _finite_diff(plus, minus, step: float) -> float | None:
    """Central finite difference, or ``None`` when either side is missing/NaN."""
    if plus is None or minus is None or abs(step) < 1e-12:
        return None
    if not (np.isfinite(plus) and np.isfinite(minus)):
        return None
    return (plus - minus) / step


def jacobian_row(knob: Knob, plus: dict, minus: dict, frac: float) -> dict:
    """One knob's finite-difference sensitivity row across all headline metrics."""
    step = 2.0 * abs(knob.value) * frac
    twh_sens = {
        c: _finite_diff(plus["twh"].get(c), minus["twh"].get(c), step)
        for c in sorted(set(plus["twh"]) | set(minus["twh"]))
    }
    twh_sens = {c: v for c, v in twh_sens.items() if v is not None}
    c2_gas = _finite_diff(
        _family_twh(plus["twh"], GAS_CLASSES),
        _family_twh(minus["twh"], GAS_CLASSES),
        step,
    )
    c2_coal = _finite_diff(
        _family_twh(plus["twh"], COAL_CLASSES),
        _family_twh(minus["twh"], COAL_CLASSES),
        step,
    )
    c3b = _finite_diff(plus["price_nrmse"], minus["price_nrmse"], step)
    c4_gas = _finite_diff(plus["shape"].get("gas"), minus["shape"].get("gas"), step)
    c4_coal = _finite_diff(plus["shape"].get("coal"), minus["shape"].get("coal"), step)
    headline = {
        "c2_gas_twh_per_unit": c2_gas,
        "c2_coal_twh_per_unit": c2_coal,
        "c3b_price_nrmse_per_unit": c3b,
        "c4_shape_gas_nrmse_per_unit": c4_gas,
        "c4_shape_coal_nrmse_per_unit": c4_coal,
    }
    finite_headline = [v for v in headline.values() if v is not None]
    return {
        "knob": knob.name,
        "field": knob.field,
        "klass": knob.klass,
        "band": knob.band,
        "baseline_value": knob.value,
        "twh_per_unit": twh_sens,
        **headline,
        "max_abs_sensitivity": max((abs(v) for v in finite_headline), default=0.0),
    }


def compute_jacobian(
    bundle: Path,
    iso: str,
    year: int = DEFAULT_YEAR,
    knobs: list[Knob] | None = None,
    frac: float = PERTURB_FRAC,
    max_knobs: int | None = None,
    one_sided: bool = False,
    solve_fn=solve_year,
    score_fn=score_bundle,
    out_root: Path | None = None,
    reference: dict | None = None,
) -> dict:
    """Assemble the full D-11 knob-jacobian result dict for ``bundle``.

    ``solve_fn``/``score_fn`` are injected so tests can stand in trivial
    synthetic fixtures instead of running a real 8760-hour LP solve; the CLI
    always calls this with the real :func:`solve_year`/:func:`score_bundle`.
    """
    if knobs is None:
        knobs = discover_knobs(bundle, iso)
    if max_knobs is not None:
        knobs = knobs[:max_knobs]
    own_tmp = out_root is None
    out_root = out_root or Path(tempfile.mkdtemp(prefix="knob_jacobian_"))
    out_root.mkdir(parents=True, exist_ok=True)

    rows = []
    for knob in knobs:
        plus_dir = solve_fn(
            bundle,
            iso,
            year,
            perturbed_override(knob, +1, frac),
            out_root / f"{_safe_slug(knob.name)}_plus",
            reference,
        )
        plus = score_fn(plus_dir, year)
        if one_sided:
            # One-sided: treat the unperturbed baseline as the "minus" side so
            # a single solve still yields a finite-difference slope (half the
            # cost of the two-sided default; noisier).
            base_dir = solve_fn(
                bundle, iso, year, {}, out_root / "_baseline", reference
            )
            minus = score_fn(base_dir, year)
            row = jacobian_row(knob, plus, minus, frac / 2.0)
        else:
            minus_dir = solve_fn(
                bundle,
                iso,
                year,
                perturbed_override(knob, -1, frac),
                out_root / f"{_safe_slug(knob.name)}_minus",
                reference,
            )
            minus = score_fn(minus_dir, year)
            row = jacobian_row(knob, plus, minus, frac)
        rows.append(row)

    rows.sort(key=lambda r: -r["max_abs_sensitivity"])
    result = {
        "diagnostic": True,
        "schema": "knob-jacobian/v1",
        "bundle": str(bundle),
        "iso": iso,
        "year": year,
        "perturb_frac": frac,
        "one_sided": one_sided,
        "n_knobs": len(knobs),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": (
            "+-10% one-year (2024-only, rule-16 probe exemption) resolve per "
            "knob; finite-difference sensitivity on class TWh, gas/coal family "
            "TWh (C2 proxy), monthly price NRMSE (C3b proxy), and gas/coal "
            "hourly dispatch-shape NRMSE (C4 proxy, docj 'shape' block). "
            "Advisory only — never registered as a keeper."
        ),
        "rows": rows,
    }
    if own_tmp:
        result["_solve_root"] = str(out_root)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI: emit ``<bundle>/knob_jacobian.json`` for one keeper bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "bundle", type=Path, help="bundle dir, e.g. results/calibration/<name>"
    )
    ap.add_argument("--iso", required=True)
    ap.add_argument("--year", type=int, default=DEFAULT_YEAR)
    ap.add_argument("--frac", type=float, default=PERTURB_FRAC)
    ap.add_argument(
        "--max-knobs",
        type=int,
        default=None,
        help="perturb only the first N discovered knobs (cheap smoke runs)",
    )
    ap.add_argument(
        "--one-sided",
        action="store_true",
        help="one solve per knob (vs the baseline) instead of two-sided +-10%%",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path (default: <bundle>/knob_jacobian.json)",
    )
    ap.add_argument(
        "--solve-root",
        type=Path,
        default=None,
        help="dir to solve the perturbed bundles into (default: a temp dir)",
    )
    args = ap.parse_args()

    result = compute_jacobian(
        args.bundle,
        args.iso,
        year=args.year,
        frac=args.frac,
        max_knobs=args.max_knobs,
        one_sided=args.one_sided,
        out_root=args.solve_root,
    )
    out = args.out or (args.bundle / "knob_jacobian.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    top = result["rows"][0]["knob"] if result["rows"] else "n/a"
    print(f"wrote {out} ({result['n_knobs']} knobs, top sensitivity: {top})")


if __name__ == "__main__":
    main()
