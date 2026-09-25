"""R-ERCOT-3 phase 0: zero-LP census of the 2019/2020 ERCOT coal shortfall.

Rebuilds the keeper recipe's LP fleet with ``run_year(fleet_only=True)`` (the
sanctioned ``replay_keeper.run_year_kwargs`` reconstruction plus the year's
``config_partition_overrides`` overlay) and reports, per year:

(a) every coal LP row — plant, class, tranche, pmax, mean availability, mean
    and hourly-quantile ``mc_base`` (the fully assembled P0 objective, the
    offer the LP actually sees) and ``min_gen``;
(b) the gas CC/ST capacity-weighted ``mc_base`` quantiles, so the coal-vs-gas
    merit order the LP faces is visible without solving;
(c) every loader log line mentioning absent / fallback / missing / nearest,
    so year-scoped inputs that do not cover the year are named, not inferred.

Keeper: ``2026-09-25-r-ercot2-chp-off`` (bundle ``r_ercot2_chpoff_span``).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_r_ercot3_coal_census.py \
        --years 2019 2020 2023 --out <json>
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(p))

BUNDLE = REPO / "results/calibration/r_ercot2_chpoff_span"
FLAG_RE = re.compile(r"absent|fallback|fall back|missing|nearest|not found|no data|skipp", re.I)


def build(year: int, prb_extra: "dict | None" = None) -> "tuple[dict, list[str]]":
    """Return (fleet-only state, captured log lines) for ``year`` on the keeper recipe."""
    from replay_keeper import (apply_config_overlay, config_partition_overlay,
                               derived_run_year_inputs, run_year_kwargs)
    from run_calibration import run_year
    from run_calibration_full import _henry_hub_actual, _load_reference
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    apply_config_overlay(kw, config_partition_overlay(meta, year))
    if prb_extra:
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {}, **prb_extra)
    clear_fleet_caches()
    gp = float(_henry_hub_actual(_load_reference(), year))
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    root = logging.getLogger()
    old_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            st = run_year(year, "ERCOT", 8760, gp, {}, fleet_only=True, **kw)
    finally:
        root.removeHandler(handler)
        root.setLevel(old_level)
    lines = buf.getvalue().splitlines()
    st["_gas_price_hh"] = gp
    return st, lines


def _arr(fa, name, n):
    v = getattr(fa, name, None)
    return None if v is None else np.asarray(v)


def summarize(st: dict) -> dict:
    """Coal rows + gas merit reference from a fleet-only state."""
    fa = st["fleet_arrays"]
    n = len(fa.pmax)
    grp = np.array([str(g) for g in fa.plant_group])
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    mc = np.asarray(st["mc_base"], float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], av.shape[1] if av.ndim == 2 else 1, axis=1)
    names = _arr(fa, "plant_name", n)
    codes = _arr(fa, "plant_code", n)
    tranche = None
    for cand in ("tranche", "tranche_name", "bin_tranche", "tranche_label", "unit_name", "name"):
        tranche = _arr(fa, cand, n)
        if tranche is not None:
            break
    mg = _arr(fa, "min_gen", n)
    rows = []
    for i in np.where(np.char.find(grp.astype(str), "COAL") >= 0)[0]:
        a = av[i] if av.ndim == 2 else np.full(8760, av[i])
        rows.append({
            "code": None if codes is None else str(codes[i]),
            "name": None if names is None else str(names[i])[:28],
            "group": grp[i],
            "tranche": None if tranche is None else str(tranche[i])[:40],
            "pmax": round(float(pmax[i]), 1),
            "avail_mean": round(float(a.mean()), 3),
            "mc_mean": round(float(mc[i].mean()), 2),
            "mc_p10": round(float(np.percentile(mc[i], 10)), 2),
            "mc_p90": round(float(np.percentile(mc[i], 90)), 2),
            "min_gen_mean": None if mg is None else round(float(np.asarray(mg[i], float).mean()), 1),
        })
    gas = {}
    for g in ("CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER", "COAL_PRB", "COAL_LIGNITE"):
        m = grp == g
        if not m.any():
            continue
        w = (pmax[m][:, None] * (av[m] if av.ndim == 2 else av[m][:, None])).ravel()
        x = mc[m].ravel()
        o = np.argsort(x)
        c = np.cumsum(w[o])
        q = {f"p{p}": round(float(x[o][np.searchsorted(c, p / 100 * c[-1])]), 2) for p in (10, 25, 50, 75, 90)}
        gas[g] = {"avail_mw_mean": round(float(w.sum() / mc.shape[1]), 1), **q}
    fp = st.get("fuel_prices")
    fuel = {}
    if isinstance(fp, dict):
        for k, v in fp.items():
            try:
                fuel[str(k)] = round(float(np.mean(v)), 3)
            except Exception:  # non-numeric entry, report its type only
                fuel[str(k)] = type(v).__name__
    fa_fields = sorted(k for k in vars(fa)) if hasattr(fa, "__dict__") else []
    return {"coal_rows": rows, "merit_ref": gas, "fuel_price_means": fuel,
            "fleet_array_fields": fa_fields}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = {}
    for y in args.years:
        st, lines = build(y)
        rec = summarize(st)
        rec["hh_gas_price"] = st["_gas_price_hh"]
        rec["flag_lines"] = sorted({ln.strip()[:300] for ln in lines if FLAG_RE.search(ln)})
        rec["coal_lines"] = sorted({ln.strip()[:300] for ln in lines if "coal" in ln.lower()})
        res[str(y)] = rec
        print(y, "coal rows", len(rec["coal_rows"]), "flag lines", len(rec["flag_lines"]), flush=True)
    Path(args.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
