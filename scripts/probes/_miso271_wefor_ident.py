#!/usr/bin/env python3
"""miso-271 phase 0 (zero LP): the caiso-187 frozen identification on MISO's keeper recipe.

``residual_c = max(0, W_c - X_c)`` per class and year, where

* ``W_c`` — the capacity-hour share the STATISTICAL forced-outage term removes
  from class ``c`` in the keeper recipe, measured as the fleet-only
  availability difference ``noW - B`` written by ``_miso271_cc_decomp.py``
  (``noW`` = the keeper recipe with ``wefor_residual=0`` on the class);
* ``X_loader`` — the capacity-hour share the LP's own overlay block removes,
  measured as ``noO - B`` (``noO`` = ``outage_source="statistical"``, which
  gates exactly the historic overlay block; ``wefor_residual`` is unset in the
  keeper so the statistical branch is unchanged). This is the GATING X: it is
  what the LP applies (caiso-187's shipped-loader reading);
* ``X_c`` — the capacity-hour share the MEASURED CAMPD windows remove,
  counted directly over the committed extracts the keeper arms
  (``-unitroute`` >= 5 d, ``-shortgas`` 1-5 d, ``-maxgen-unitroute``):
  ``sum(overlap_hours x unit MW) / (class MW x 8760)``. This is the loader-
  independent direct count caiso-187 used as its cross-check; it ignores
  window overlaps and so is an UPPER bound on the removal.

A class with ``X_c >= W_c`` in every year has ``residual_c = 0``: the
measured record already removes at least what the statistical term claims
exists, so the statistical term is a pure second count (rule 19).

Usage::

    uv run python scripts/probes/_miso271_wefor_ident.py --decomp DIR --out X.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
import pandas as pd  # noqa: E402

RAW = REPO / "data/raw"
CLASSES = ("CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP")
FILES = {
    "ge5d": RAW / "campd-unit-outages-unitroute-MISO.csv",
    "shortgas": RAW / "campd-unit-outages-shortgas-MISO.csv",
}
MAXGEN = RAW / "campd-unit-outages-maxgen-unitroute-MISO.csv"


def _overlap_mwh(df: pd.DataFrame, s: str, e: str, mw: str, year: int, end_inclusive: bool) -> pd.Series:
    """Per-class MWh of window overlap with calendar ``year``."""
    y0, y1 = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year + 1}-01-01")
    st = pd.to_datetime(df[s])
    en = pd.to_datetime(df[e]) + (pd.Timedelta(days=1) if end_inclusive else pd.Timedelta(0))
    hrs = (en.clip(upper=y1) - st.clip(lower=y0)).dt.total_seconds().clip(lower=0) / 3600.0
    return (hrs * df[mw]).groupby(df["plant_group"]).sum()


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--decomp", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    d = Path(args.decomp)
    ext = {k: pd.read_csv(p) for k, p in FILES.items()}
    mg = pd.read_csv(MAXGEN)
    rows = []
    for y in args.years:
        b = pd.read_parquet(d / f"{y}_B.parquet")
        w = pd.read_parquet(d / f"{y}_noW.parquet")
        o = pd.read_parquet(d / f"{y}_noO.parquet")
        xs = {k: _overlap_mwh(v, "outage_start", "outage_end", "unit_capacity_mw", y, True) for k, v in ext.items()}
        xs["maxgen"] = _overlap_mwh(mg, "window_start", "window_end", "derate_mw", y, False)
        for c in CLASSES:
            cap_h = float(b.loc[b.group == c, "pmax"].sum()) * 8760.0
            W = (float(w.loc[w.group == c, "avail_mwh"].sum()) - float(b.loc[b.group == c, "avail_mwh"].sum())) / cap_h
            XL = (float(o.loc[o.group == c, "avail_mwh"].sum()) - float(b.loc[b.group == c, "avail_mwh"].sum())) / cap_h
            parts = {k: float(v.get(c, 0.0)) / cap_h for k, v in xs.items()}
            X = sum(parts.values())
            rows.append(
                {"year": y, "class": c, "class_mw": round(cap_h / 8760.0, 1), "W": round(W, 4),
                 **{f"X_{k}": round(v, 4) for k, v in parts.items()}, "X_direct": round(X, 4),
                 "X_loader": round(XL, 4), "residual": round(max(0.0, W - XL), 4)}
            )
            print(json.dumps(rows[-1]))
    Path(args.out).write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
