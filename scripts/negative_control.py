#!/usr/bin/env python3
"""D-14 negative-control probes for a calibration keeper (scalar-remediation
program batch B-DIAG-2; see docs/handoffs/scalar-remediation-plan-2026-07.md
§4.5 and docs/model-legitimacy-audit-2026-07.md §7 D-14).

Clones a keeper's config, corrupts exactly ONE physical input, re-solves ONE
year (2024 only — the same rule-16 probe exemption D-11 uses; never touches
the 2022/H1-2026 quarantine, rule 22), and asserts the backcast fit
*worsens* beyond a floor delta. A model correctly grounded in physical
inputs must get WORSE when a physical input is corrupted; if it does not,
some other fitted knob is silently compensating for the corruption (the
nyiso-32 pattern) — insensitivity is the finding, not a passing grade.

Controls (``--control``):
  * ``gas_price``      — scale the year's Henry Hub reference price x1.5
    (:func:`corrupt_gas_price`). Composes with :func:`scripts.knob_jacobian.
    solve_year` via its existing ``reference`` parameter — no monkeypatching.
  * ``outage_shuffle``  — permute the (outage_start, outage_end,
    duration_days) WINDOW across units within the target year, preserving
    the exact multiset of windows (so total system outage-days for the year
    is conserved) but breaking the unit<->window correspondence
    (:func:`shuffle_outages_within_year`). Wired in via a scoped monkeypatch
    of ``market_sim.data.outages._load_unit_outage_events`` around the solve
    (that function's caller, ``unit_outage_derate_factors``, is
    ``lru_cache``d, so the cache is cleared before AND after the patched
    solve to prevent cross-contamination with the clean baseline solve run
    in the same process).

Both controls need a CLEAN baseline solve of the same one year (dispatch
parquet is gitignored/derived, so a keeper's own committed bundle has none
to compare against) plus the corrupted solve; the two are scored on the same
error-based C2 (gas/coal family |model-actual| TWh)/C3b (monthly price
NRMSE) metrics :mod:`scripts.knob_jacobian` already computes for D-11, reused
directly here rather than re-derived.

If the corrupted run does NOT worsen beyond the floor delta, this is exactly
the D-14 "insensitivity" finding: report the (input, knob) pair by cross-
referencing the metric that failed to move against an existing
``<bundle>/knob_jacobian.json`` (D-11 output for the SAME bundle, if one has
been produced) — the top-ranked knob for that metric is the suspected
compensator. This is a cheap best-effort cross-reference against an
already-computed Jacobian, not a fresh from-scratch D-11 sweep on the
corrupted config (which would be a second O(n_knobs) solve batch).

Every solve is labelled a diagnostic probe (``"diagnostic": true``) — never a
keeper (CLAUDE.md rule 16). One control per ISO per release is the cadence
(plan §4.5); this harness lands the machinery and a smoke run only.

Usage::

    python scripts/negative_control.py results/calibration/<bundle> \\
        --iso ERCOT --control gas_price
    python scripts/negative_control.py results/calibration/<bundle> \\
        --iso NYISO --control outage_shuffle --seed 1
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import scripts.derive_offer_curve_jacobian as docj  # noqa: E402
import scripts.knob_jacobian as kj  # noqa: E402
from scripts.calibration_verdict import COAL_CLASSES, GAS_CLASSES  # noqa: E402

CONTROLS = ("gas_price", "outage_shuffle")
DEFAULT_YEAR = kj.DEFAULT_YEAR  # 2024-only, rule-16 probe exemption
GAS_PRICE_FACTOR = 1.5
# Floor deltas: the WORSENING an identified physical input must produce to
# count as "the model responded" (report-only defaults; tune once real
# per-ISO runs establish typical corruption magnitudes — CLAUDE.md rule 15's
# "never re-tune to a residual" does not apply to a diagnostic's OWN gate,
# but any change here should cite the runs that motivated it).
FLOOR_DELTA_C2_TWH = 0.5  # |model-actual| gas/coal family TWh must grow >= this
FLOOR_DELTA_C3B_NRMSE = 0.01  # monthly price NRMSE must grow >= this

_WINDOW_COLS = ("outage_start", "outage_end", "duration_days")


# ---------------------------------------------------------------------------
# Corruptions (pure, unit-testable — no solve, no I/O beyond what's passed in)
# ---------------------------------------------------------------------------
def corrupt_gas_price(
    reference: dict, year: int, factor: float = GAS_PRICE_FACTOR
) -> dict:
    """Return a copy of the calibration reference dict with ``year``'s Henry
    Hub price scaled by ``factor`` (default x1.5) — the ``gas_price`` control.

    Mirrors ``scripts.run_calibration._henry_hub_actual``'s lookup exactly
    (reference table first, then the model's own hardcoded fallback table)
    so the corrupted value is a scaled version of whatever price the solve
    would actually have used, never a value pulled from thin air.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import run_calibration as rc  # noqa: PLC0415

    ref = copy.deepcopy(reference) if reference else {}
    table = ref.setdefault("henry_hub_actual", {})
    base = float(table.get(str(year), rc._HENRY_HUB_FALLBACK.get(year, 3.0)))
    table[str(year)] = round(base * factor, 4)
    return ref


def shuffle_outages_within_year(
    df: pd.DataFrame, year: int, seed: int = 0
) -> pd.DataFrame:
    """Permute the outage WINDOW across units within ``year``; totals preserved.

    Each row's ``(outage_start, outage_end, duration_days)`` triple is
    reassigned to a different row's unit identity (``facility_id``,
    ``unit_id``, ...) among the rows whose ``outage_start`` falls in
    ``year``, via a random permutation. This exactly conserves the multiset
    of windows (so total system outage-days for the year is unchanged bit
    for bit) while breaking any genuine physical unit<->outage-timing
    correspondence — the D-14 ``outage_shuffle`` control. Rows outside
    ``year`` are returned byte-identical. A no-op when fewer than 2 rows fall
    in ``year`` (nothing to permute).
    """
    out = df.copy()
    out_year = pd.to_datetime(out["outage_start"]).dt.year
    mask = out_year == year
    idx = out.index[mask]
    if len(idx) > 1:
        rng = np.random.default_rng(seed)
        perm = rng.permutation(len(idx))
        window = out.loc[idx, list(_WINDOW_COLS)].to_numpy()
        out.loc[idx, list(_WINDOW_COLS)] = window[perm]
    return out


# ---------------------------------------------------------------------------
# Solving: one clean baseline + one corrupted solve, one year only
# ---------------------------------------------------------------------------
def _clear_outage_caches() -> None:
    """Clear ``unit_outage_derate_factors``'s lru_cache between solves.

    Both the clean and corrupted solve happen in the SAME process; without
    this, a cache hit keyed on (year, hours, bins_path, iso) would silently
    serve one solve's outage data to the other.
    """
    from market_sim.data import outages as outages_mod

    outages_mod.unit_outage_derate_factors.cache_clear()


def solve_clean(
    bundle: Path, iso: str, year: int, out_dir: Path, reference: dict
) -> Path:
    """Uncorrupted one-year replay of ``bundle`` — the negative control's baseline."""
    _clear_outage_caches()
    return kj.solve_year(bundle, iso, year, {}, out_dir, reference)


def solve_gas_price_corrupted(
    bundle: Path,
    iso: str,
    year: int,
    out_dir: Path,
    reference: dict,
    factor: float = GAS_PRICE_FACTOR,
) -> Path:
    """One-year replay with the Henry Hub reference price scaled by ``factor``."""
    _clear_outage_caches()
    corrupted_ref = corrupt_gas_price(reference, year, factor)
    return kj.solve_year(bundle, iso, year, {}, out_dir, corrupted_ref)


def solve_outage_shuffle_corrupted(
    bundle: Path, iso: str, year: int, out_dir: Path, reference: dict, seed: int = 0
) -> Path:
    """One-year replay with unit outage windows shuffled across units for ``year``."""
    from market_sim.data import outages as outages_mod

    original = outages_mod._load_unit_outage_events

    def _shuffled(csv_path, iso_arg):
        raw = original(csv_path, iso_arg)
        return raw if raw is None else shuffle_outages_within_year(raw, year, seed)

    _clear_outage_caches()
    try:
        with mock.patch.object(outages_mod, "_load_unit_outage_events", _shuffled):
            out = kj.solve_year(bundle, iso, year, {}, out_dir, reference)
    finally:
        _clear_outage_caches()
    return out


_CORRUPT_SOLVERS = {
    "gas_price": solve_gas_price_corrupted,
    "outage_shuffle": solve_outage_shuffle_corrupted,
}


# ---------------------------------------------------------------------------
# Scoring: error-based C2/C3b (bigger = worse fit), reusing D-11's machinery
# ---------------------------------------------------------------------------
def score_verdict(bundle_dir: Path, year: int, cache: dict | None = None) -> dict:
    """C2 (|model-actual| gas/coal family TWh) + C3b (price NRMSE) for one solve.

    Reuses ``derive_offer_curve_jacobian.error_blocks`` (model-actual, the
    same source of truth D-11 and the offer-curve Jacobian use) and
    ``knob_jacobian._monthly_price_nrmse`` (C3b proxy) rather than
    re-deriving either.
    """
    cache = {} if cache is None else cache
    b = kj._load_bundle(bundle_dir)
    err = docj.error_blocks(b, cache)
    twh_err = err[(err["metric"] == "twh") & (err["year"] == year)].set_index("key")[
        "err"
    ]
    c2_gas = abs(sum(float(twh_err.get(c, 0.0)) for c in GAS_CLASSES))
    c2_coal = abs(sum(float(twh_err.get(c, 0.0)) for c in COAL_CLASSES))
    return {
        "c2_gas_abs_err_twh": c2_gas,
        "c2_coal_abs_err_twh": c2_coal,
        "c3b_price_nrmse": kj._monthly_price_nrmse(b, year),
    }


# ---------------------------------------------------------------------------
# Compensating-knob cross-reference (cheap: reads an EXISTING D-11 jacobian)
# ---------------------------------------------------------------------------
def find_suspected_compensator(
    jacobian_path: Path, metric_key: str, top_n: int = 3
) -> list[dict]:
    """Top ``top_n`` knobs ranked by ``metric_key`` sensitivity in a committed
    D-11 ``knob_jacobian.json`` — the (input, knob) pair report for an
    insensitive control. Returns ``[]`` when no jacobian file exists (D-11
    hasn't been run for this bundle yet) rather than raising.
    """
    if not jacobian_path.exists():
        return []
    data = json.loads(jacobian_path.read_text())
    rows = [r for r in data.get("rows", []) if r.get(metric_key) is not None]
    rows.sort(key=lambda r: -abs(r[metric_key]))
    return [{"knob": r["knob"], metric_key: r[metric_key]} for r in rows[:top_n]]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_negative_control(
    bundle: Path,
    iso: str,
    control: str,
    year: int = DEFAULT_YEAR,
    out_root: Path | None = None,
    seed: int = 0,
    gas_price_factor: float = GAS_PRICE_FACTOR,
    floor_delta_c2: float = FLOOR_DELTA_C2_TWH,
    floor_delta_c3b: float = FLOOR_DELTA_C3B_NRMSE,
    jacobian_path: Path | None = None,
    solve_clean_fn=solve_clean,
    solve_corrupt_fn=None,
    score_fn=score_verdict,
    reference: dict | None = None,
) -> dict:
    """Run one D-14 negative-control probe end to end; return the verdict dict.

    ``solve_clean_fn``/``solve_corrupt_fn``/``score_fn`` are injected so tests
    can stand in trivial synthetic fixtures instead of running a real LP
    solve; the CLI always calls this with the real solvers.
    """
    if control not in CONTROLS:
        raise ValueError(f"control must be one of {CONTROLS}, got {control!r}")
    if solve_corrupt_fn is None:
        if control == "gas_price":
            solve_corrupt_fn = lambda b, i, y, o, r: _CORRUPT_SOLVERS[control](  # noqa: E731
                b, i, y, o, r, factor=gas_price_factor
            )
        else:
            solve_corrupt_fn = lambda b, i, y, o, r: _CORRUPT_SOLVERS[control](  # noqa: E731
                b, i, y, o, r, seed=seed
            )

    own_tmp = out_root is None
    out_root = out_root or Path(tempfile.mkdtemp(prefix="negative_control_"))
    out_root.mkdir(parents=True, exist_ok=True)
    if reference is None:
        sys.path.insert(0, str(REPO / "scripts"))
        import run_calibration_full as rcf  # noqa: PLC0415

        reference = rcf._load_reference()

    clean_dir = solve_clean_fn(bundle, iso, year, out_root / "_clean", reference)
    corrupt_dir = solve_corrupt_fn(
        bundle, iso, year, out_root / f"_corrupt_{control}", reference
    )
    cache: dict = {}
    clean = score_fn(clean_dir, year, cache)
    corrupt = score_fn(corrupt_dir, year, cache)

    deltas = {
        k: (corrupt[k] - clean[k])
        for k in clean
        if clean.get(k) is not None and corrupt.get(k) is not None
    }
    worsened_metrics = {
        k: d
        for k, d in deltas.items()
        if (k.startswith("c2_") and d >= floor_delta_c2)
        or (k == "c3b_price_nrmse" and d >= floor_delta_c3b)
    }
    sensitive = bool(worsened_metrics)

    suspects: dict[str, list[dict]] = {}
    if not sensitive:
        jpath = jacobian_path or (bundle / "knob_jacobian.json")
        metric_map = {
            "c2_gas_abs_err_twh": "c2_gas_twh_per_unit",
            "c2_coal_abs_err_twh": "c2_coal_twh_per_unit",
            "c3b_price_nrmse": "c3b_price_nrmse_per_unit",
        }
        for verdict_key, jac_key in metric_map.items():
            top = find_suspected_compensator(jpath, jac_key)
            if top:
                suspects[verdict_key] = top

    result = {
        "diagnostic": True,
        "schema": "negative-control/v1",
        "bundle": str(bundle),
        "iso": iso,
        "control": control,
        "year": year,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "clean": clean,
        "corrupt": corrupt,
        "deltas": deltas,
        "floor_delta_c2_twh": floor_delta_c2,
        "floor_delta_c3b_nrmse": floor_delta_c3b,
        "sensitive": sensitive,
        "verdict": (
            "PASS: backcast fit worsened beyond the floor delta — the model "
            "responds to this physical input as expected."
            if sensitive
            else "FAIL: backcast fit did NOT worsen beyond the floor delta — "
            "insensitivity suggests a compensating knob (the nyiso-32 pattern)."
        ),
        "suspected_compensators": suspects,
    }
    if own_tmp:
        result["_solve_root"] = str(out_root)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI: run one D-14 control and print/write its verdict. Exits 1 on FAIL
    (insensitivity — never a keeper-blocking gate, just the diagnostic's own
    exit code for scripting)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "bundle", type=Path, help="bundle dir, e.g. results/calibration/<name>"
    )
    ap.add_argument("--iso", required=True)
    ap.add_argument("--control", required=True, choices=CONTROLS)
    ap.add_argument("--year", type=int, default=DEFAULT_YEAR)
    ap.add_argument("--seed", type=int, default=0, help="outage_shuffle RNG seed")
    ap.add_argument("--gas-price-factor", type=float, default=GAS_PRICE_FACTOR)
    ap.add_argument(
        "--jacobian",
        type=Path,
        default=None,
        help="D-11 knob_jacobian.json to cross-reference on insensitivity "
        "(default: <bundle>/knob_jacobian.json)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path (default: <bundle>/negative_control_<control>.json)",
    )
    ap.add_argument("--solve-root", type=Path, default=None)
    args = ap.parse_args()

    result = run_negative_control(
        args.bundle,
        args.iso,
        args.control,
        year=args.year,
        out_root=args.solve_root,
        seed=args.seed,
        gas_price_factor=args.gas_price_factor,
        jacobian_path=args.jacobian,
    )
    out = args.out or (args.bundle / f"negative_control_{args.control}.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {out}\n{result['verdict']}")
    if not result["sensitive"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
