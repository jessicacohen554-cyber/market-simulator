"""miso-151 gate probe — footing, the rule-13 census, and the P-1 measurement.

Runs the pre-registered Phase-0 gates of
``results/calibration/PREREG-miso151-measured-offer-surface-2026-08-11.md``
and writes ``results/calibration/_miso151_surface.json``.

Gates
-----
``G-F2``  rule-13 column census on the WRITTEN clean partitions (bar: 0 outcome
          columns).  Measured on the files, not read off ``OUTCOME_COLS`` — the
          constant and the artifact are different claims.
``G-F3``  LEVEL invariance of the measured object, on REAL data: shift every
          unit's whole curve by a constant and the derived surface must be
          bit-identical.  This is the property the entire mechanism rests on
          (miso-145 measured the real book CHEAPER at matched position, so a
          level transfer would move C3a the wrong way), so it is measured here
          rather than argued from the algebra.
``G-1``   P-1: the measured own-curve rise at the model's own clearing position
          band, against the model's OWN rise there.  Pre-registered prior 3.0x,
          band [1.2x, 12x].

Nothing here arms anything or touches an LP.

Usage::

    MISO147_CACHE=/tmp/x PYTHONPATH=$PWD python scripts/probes/_miso151_surface.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("_miso151_surface")

OUT = REPO / "results" / "calibration" / "_miso151_surface.json"
ARTIFACT = (
    REPO / "data" / "raw" / "_validation-source" / "miso_offer_surface_positioned.json"
)

#: Dispatch AWARDS that must never reach the clean datatype (rule 13).
OUTCOME_COLS = {
    "MW",
    "Target MW Reduction",
    *(f"Cleared MW{i}" for i in range(1, 13)),
}


def g_f0_footing() -> dict:
    """Re-run miso-150's footing IN PROCESS and compare to its committed block.

    Deliberately calls :func:`_miso150_universe.footing` directly rather than
    the ``--footing`` CLI: that CLI writes ``_miso150_universe.json`` containing
    ONLY the footing block, which DESTROYS miso-150's committed ``measurement``
    block.  A footing check must never damage the artifact it is checking.

    The bar is stronger than "PASS": this session's re-run must reproduce the
    committed footing block **byte-identically**, which is what certifies that
    the full-year refetch and the streaming curator rewrite left the JJA corpus
    miso-145/150 measured completely unchanged (PREREG G-F0/G-F1).
    """
    from scripts.probes._miso150_universe import footing

    fresh = footing()
    committed = json.loads(
        (REPO / "results" / "calibration" / "_miso150_universe.json").read_text()
    )["footing"]
    identical = json.dumps(fresh, sort_keys=True) == json.dumps(
        committed, sort_keys=True
    )
    return {
        "bar": "byte-identical to the committed footing block",
        "verdict_self": fresh.get("verdict"),
        "n_out_of_tolerance": fresh.get("G_F0_miso145_reproduction", {}).get(
            "n_out_of_tolerance"
        ),
        "byte_identical_to_committed": identical,
        "verdict": "PASS" if (identical and fresh.get("verdict") == "PASS") else "HARD STOP",
    }


def g_f2_outcome_census() -> dict:
    """Census the written partitions for any dispatch-award column."""
    from market_sim.config import paths

    norm = {c.lower().replace(" ", "_") for c in OUTCOME_COLS}
    per_file: dict[str, dict] = {}
    total_hits = 0
    for market in ("DA", "RT"):
        for year in (2023, 2024, 2025):
            path = paths.clean_path("energy-offers", iso="MISO", year=year, market=market)
            cols = set(pq.read_schema(path).names)
            hits = sorted(
                (cols & OUTCOME_COLS)
                | {c for c in cols if c.lower().replace(" ", "_") in norm}
            )
            total_hits += len(hits)
            per_file[f"{market}-{year}"] = {
                "rows": int(pq.read_metadata(path).num_rows),
                "outcome_columns": hits,
            }
    return {
        "bar": "0 outcome columns in any written partition",
        "per_partition": per_file,
        "total_outcome_columns": total_hits,
        "verdict": "PASS" if total_hits == 0 else "HARD STOP",
    }


def g_f3_level_invariance(market: str = "DA", year: int = 2025, month: int = 7) -> dict:
    """Shift a real month's whole curves by a constant; Delta must not move."""
    from market_sim.config import paths

    from scripts.data.derive_miso_offer_surface import _READ_COLS, _prepare_frame

    path = paths.clean_path("energy-offers", iso="MISO", year=year, market=market)
    lo = pd.Timestamp(year=year, month=month, day=1, tz="UTC")
    hi = lo + pd.offsets.MonthBegin(1)
    df = pd.read_parquet(
        path,
        columns=_READ_COLS,
        filters=[("interval_start_utc", ">=", lo), ("interval_start_utc", "<", hi)],
    )
    base, _ = _prepare_frame(df)
    shift = 137.42
    df2 = df.copy()
    df2["step_price_usd_per_mwh"] = df2["step_price_usd_per_mwh"] + shift
    shifted, _ = _prepare_frame(df2)

    a, b = base["delta"].to_numpy(), shifted["delta"].to_numpy()
    identical = bool(a.shape == b.shape and np.array_equal(a, b))
    return {
        "bar": "Delta bit-identical under a constant curve shift",
        "population": f"{market}-{year}-{month:02d}, {len(a):,} segments",
        "shift_usd_per_mwh": shift,
        "max_abs_delta_of_delta": float(np.max(np.abs(a - b))) if identical else None,
        "bit_identical": identical,
        "verdict": "PASS" if identical else "HARD STOP",
    }


def g1_p1_measured_vs_model() -> dict:
    """P-1 — measured own-curve rise vs the model's own, at matched position.

    The model side is the keeper's own assembled offer curve: for every
    above-base MISO gas tranche the mechanism would touch, its rise over its
    plant's base row, load-weight-free and taken at the training-window anchor
    gas so it is a single number per position bin rather than a time series.
    """
    art = json.loads(ARTIFACT.read_text())
    ladder = np.asarray(art["markets"]["DA"]["ladder"], dtype=float)
    pos_edges = np.asarray(art["_provenance"]["position_bins"], dtype=float)

    # Measured: median over gas/state bins per position bin, weight-aware.
    measured = []
    for q in range(ladder.shape[2]):
        cell = ladder[:, :, q, :]
        w = cell[..., 2]
        d = cell[..., 1]
        ok = np.isfinite(d) & (w > 0)
        measured.append(float(np.average(d[ok], weights=w[ok])) if ok.any() else float("nan"))

    # Model side, from the keeper bundle's registered offer curve.
    cfg = json.loads(
        (REPO / "results" / "calibration" / "miso148_basis_B" / "run_config.json").read_text()
    )
    sc = cfg.get("scenario_config", cfg)
    anchor = float(sc["gas_offer_margin_anchor"])
    curve = sc["offer_curve_by_group"]
    gas_groups = [g for g in curve if not g.startswith("COAL")]

    # The model's above-base rise, in the same $/MWh units: for each gas class,
    # (mult_band - mult_committed) x HR_base x anchor, using the class's own
    # registered multipliers. HR_base is the class's measured heat rate; take
    # the ScenarioConfig default CC/CT/ST heat rates as the scale.
    base_hr = {"CC": 7.0, "CT": 10.5, "ST": 10.3}
    rows = []
    for g in gas_groups:
        band = curve[g]
        hr = base_hr["CC" if g.startswith("CC") else ("CT" if g.startswith("CT") else "ST")]
        cm = float(band.get("committed", 1.0))
        for name in ("econ_low", "econ_high", "peak"):
            if name in band:
                rows.append(
                    {
                        "group": g,
                        "band": name,
                        "model_rise_usd_per_mwh": (float(band[name]) - cm) * hr * anchor,
                    }
                )
    model_rises = np.array([r["model_rise_usd_per_mwh"] for r in rows], dtype=float)

    # Compare at the top of the curve, where the wall lives.
    measured_top = float(np.nanmax(measured))
    model_top = float(np.nanmax(model_rises))
    ratio = measured_top / model_top if model_top > 0 else float("inf")
    return {
        "prior": {"central": 3.0, "band": [1.2, 12.0], "P": 0.75},
        "measured_rise_by_position_bin": [round(x, 4) for x in measured],
        "position_bins": [float(x) for x in pos_edges],
        "model_above_base_rises": sorted(
            rows, key=lambda r: -r["model_rise_usd_per_mwh"]
        )[:8],
        "measured_top_usd_per_mwh": round(measured_top, 4),
        "model_top_usd_per_mwh": round(model_top, 4),
        "ratio_measured_over_model": round(ratio, 4),
        "anchor_usd_per_mmbtu": anchor,
        "verdict": "FIRES" if ratio > 1.2 else "DOES NOT FIRE",
        "note": (
            "Model rise uses each class's REGISTERED band multipliers at the "
            "training-window anchor gas and a class-level base heat rate, so it "
            "is a level comparison of the two curves' shapes, not a solve "
            "result. The solve's own answer is the arm."
        ),
    }


def main() -> None:
    """Run every Phase-0 gate and write the record."""
    rec: dict = {"session": "miso-151", "keeper": "2026-08-09-miso-148-basis-aware"}
    rec["G_F0_footing"] = g_f0_footing()
    log.info("G-F0 %s", rec["G_F0_footing"]["verdict"])
    if rec["G_F0_footing"]["verdict"] != "PASS":
        OUT.write_text(json.dumps(rec, indent=1))
        raise SystemExit("G-F0 footing FAILED — HARD STOP (PREREG §2)")
    rec["G_F2_outcome_census"] = g_f2_outcome_census()
    log.info("G-F2 %s", rec["G_F2_outcome_census"]["verdict"])
    rec["G_F3_level_invariance"] = g_f3_level_invariance()
    log.info("G-F3 %s", rec["G_F3_level_invariance"]["verdict"])
    if ARTIFACT.is_file():
        rec["G_1_P1"] = g1_p1_measured_vs_model()
        log.info("G-1 %s", rec["G_1_P1"]["verdict"])
    else:
        rec["G_1_P1"] = {"verdict": "SKIPPED", "reason": f"no artifact at {ARTIFACT}"}
    OUT.write_text(json.dumps(rec, indent=1))
    log.info("wrote %s", OUT)


if __name__ == "__main__":
    main()
