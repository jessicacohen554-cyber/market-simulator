"""SPP-70 phase 0 reducer — the band-width attribution.

Reads the per-year blobs written by ``_spp70_stack_extent_phase0.py`` and
reports, in $/MWh, how wide SPP's thermal offer stack is and which
construction supplies (or withholds) that width.

The stack is the LP's own ``mc_base``, capacity-weighted by each row's
``pmax * mean availability`` -- i.e. the MW actually offered.  Width is the
capacity-weighted p05->p95 of the annual-mean marginal cost across thermal
rows, the same statistic RESULT-spp-69 §5 uses on the price side, so the two
are directly comparable.

Attribution is a two-sided counterfactual on the identity the LP builds:

    mc = heat_rate * fuel_price + vom + residual      (residual = carbon/NOx/EAC)

* ISOLATE  -- only that term keeps its per-row values, the rest collapse to
              their capacity-weighted means: the width this term could carry
              on its own.
* FLATTEN  -- only that term collapses to its mean, the rest stay actual:
              the width lost by removing it.

Neither is a decomposition on its own (the hr*fp product carries an
interaction term); reported together they bracket each term's contribution,
and the bracket is stated rather than hidden.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

QS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)


def _wq(v, w, qs=QS):
    v = np.asarray(v, float)
    w = np.asarray(w, float)
    ok = np.isfinite(v) & (w > 0)
    v, w = v[ok], w[ok]
    if v.size == 0:
        return {q: float("nan") for q in qs}
    o = np.argsort(v)
    v, w = v[o], w[o]
    cw = np.cumsum(w)
    cw = (cw - 0.5 * w) / cw[-1]
    return {q: float(np.interp(q, cw, v)) for q in qs}


def _wmean(v, w):
    v = np.asarray(v, float)
    w = np.asarray(w, float)
    ok = np.isfinite(v) & (w > 0)
    return float(np.average(v[ok], weights=w[ok])) if ok.any() else float("nan")


def _width(v, w, lo=0.05, hi=0.95):
    q = _wq(v, w, (lo, hi))
    return q[hi] - q[lo]


def load(year: int, src: Path) -> dict:
    blob = json.loads((src / f"y{year}.json").read_text())
    # meta["gas_prices"] only keys the bundle's FIRST year; read the
    # per-year run_config for the rest (trap (n): the seven years differ).
    cfg = json.loads((Path(blob["bundle"]) / f"run_config_{year}.json").read_text())
    blob["gas_price_override"] = cfg["scenario_config"]["gas_price_override"]
    r = blob["rows"]
    a = {k: np.asarray(v) for k, v in r.items()}
    th = a["thermal"].astype(bool)
    out = {k: v[th] for k, v in a.items()}
    out["w"] = out["pmax"].astype(float) * out["avail_mean"].astype(float)
    out["year"] = year
    out["gas_override"] = blob.get("gas_price_override")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2019, 2020, 2021, 2022, 2023, 2024, 2025],
    )
    args = ap.parse_args()

    D = {}
    for y in args.years:
        try:
            D[y] = load(y, args.src)
        except FileNotFoundError:
            print(f"  (year {y} blob missing — skipped)")
    years = sorted(D)

    # ------------------------------------------------------------------ A
    print("\n" + "=" * 86)
    print("A. THE THERMAL OFFER STACK AS THE LP SEES IT")
    print(
        "   capacity-weighted (pmax x mean availability) quantiles of annual-mean mc, $/MWh"
    )
    print("=" * 86)
    print(
        f"{'year':>5} {'gas$':>5} {'thMW':>7} {'p05':>7} {'p25':>7} {'p50':>7} {'p75':>7} {'p95':>7} "
        f"{'p05>p95':>8} {'p10>p90':>8}"
    )
    for y in years:
        d = D[y]
        q = _wq(d["mc_mean"], d["w"])
        print(
            f"{y:>5} {d['gas_override']:>5.2f} {d['w'].sum() / 1000:>7.1f} "
            f"{q[0.05]:>7.2f} {q[0.25]:>7.2f} {q[0.50]:>7.2f} {q[0.75]:>7.2f} {q[0.95]:>7.2f} "
            f"{q[0.95] - q[0.05]:>8.2f} {q[0.90] - q[0.10]:>8.2f}"
        )

    # ------------------------------------------------------------------ B
    print("\n" + "=" * 86)
    print("B. ATTRIBUTION — mc = heat_rate * fuel_price + vom + residual")
    print("   ISOLATE = only this term varies (width it can carry alone)")
    print("   FLATTEN = only this term is set to its mean (width lost by removing it)")
    print("   all values are capacity-weighted p05->p95 of annual-mean mc, $/MWh")
    print("=" * 86)
    hdr = (
        f"{'year':>5} {'FULL':>7} | {'iso_HR':>7} {'iso_FP':>7} {'iso_VOM':>7} {'iso_RES':>7} "
        f"| {'flat_HR':>7} {'flat_FP':>7} {'flatVOM':>7} {'flatRES':>7}"
    )
    print(hdr)
    B = {}
    for y in years:
        d = D[y]
        w = d["w"]
        hr = d["heat_rate"].astype(float)
        fp = d["fuel_mean"].astype(float)
        vom = d["vom"].astype(float)
        res = d["resid_mean"].astype(float)
        hb, fb, vb, rb = (_wmean(x, w) for x in (hr, fp, vom, res))
        full = _width(hr * fp + vom + res, w)
        iso = {
            "HR": _width(hr * fb + vb + rb, w),
            "FP": _width(hb * fp + vb + rb, w),
            "VOM": _width(hb * fb + vom + rb, w),
            "RES": _width(hb * fb + vb + res, w),
        }
        flat = {
            "HR": full - _width(hb * fp + vom + res, w),
            "FP": full - _width(hr * fb + vom + res, w),
            "VOM": full - _width(hr * fp + vb + res, w),
            "RES": full - _width(hr * fp + vom + rb, w),
        }
        B[y] = (full, iso, flat)
        print(
            f"{y:>5} {full:>7.2f} | {iso['HR']:>7.2f} {iso['FP']:>7.2f} {iso['VOM']:>7.2f} {iso['RES']:>7.2f} "
            f"| {flat['HR']:>7.2f} {flat['FP']:>7.2f} {flat['VOM']:>7.2f} {flat['RES']:>7.2f}"
        )

    # ------------------------------------------------------------------ C
    print("\n" + "=" * 86)
    print(
        "C. WHERE THE WIDTH LIVES — between class / within class / within plant (across bands)"
    )
    print("   capacity-weighted p05->p95 of annual-mean mc, $/MWh")
    print("=" * 86)
    print(
        f"{'year':>5} {'FULL':>7} {'between_class':>14} {'within_class':>13} {'within_plant':>13} {'across_plant':>13}"
    )
    for y in years:
        d = D[y]
        w, mc, k = d["w"], d["mc_mean"].astype(float), d["klass"]
        full = _width(mc, w)
        # between-class: every row replaced by its class capacity-weighted mean
        cmean = np.array([_wmean(mc[k == kk], w[k == kk]) for kk in k])
        between = _width(cmean, w)
        # within-class: row minus its class mean, re-centred
        within = _width(mc - cmean + _wmean(mc, w), w)
        # within-plant (across tranche bands): row minus its plant-group mean
        pid = np.array([u.rsplit("_", 1)[0] for u in d["unit_id"]])
        pmean = np.zeros_like(mc)
        for p in np.unique(pid):
            m = pid == p
            pmean[m] = _wmean(mc[m], w[m])
        wp = _width(mc - pmean + _wmean(mc, w), w)
        ap_ = _width(pmean, w)
        print(
            f"{y:>5} {full:>7.2f} {between:>14.2f} {within:>13.2f} {wp:>13.2f} {ap_:>13.2f}"
        )

    # ------------------------------------------------------------------ D
    print("\n" + "=" * 86)
    print("D. PER-CLASS STACK AND OVERLAP — capacity-weighted annual-mean mc, $/MWh")
    print("=" * 86)
    for y in years:
        d = D[y]
        w, mc, k = d["w"], d["mc_mean"].astype(float), d["klass"]
        tot = w.sum()
        print(
            f"\n  {y} (gas ${d['gas_override']:.2f}/MMBtu, thermal {tot / 1000:.1f} GW)"
        )
        print(
            f"    {'class':<18} {'GW':>6} {'p05':>7} {'p50':>7} {'p95':>7} {'width':>7} {'HR p50':>7} {'VOM':>6}"
        )
        rows = []
        for kk in sorted(set(k.tolist())):
            m = k == kk
            if w[m].sum() < 1.0:
                continue
            q = _wq(mc[m], w[m])
            rows.append(
                (
                    kk,
                    w[m].sum(),
                    q,
                    _wmean(d["heat_rate"].astype(float)[m], w[m]),
                    _wmean(d["vom"].astype(float)[m], w[m]),
                )
            )
        for kk, gw, q, hrm, vm in sorted(rows, key=lambda r: r[2][0.50]):
            print(
                f"    {kk:<18} {gw / 1000:>6.2f} {q[0.05]:>7.2f} {q[0.50]:>7.2f} {q[0.95]:>7.2f} "
                f"{q[0.95] - q[0.05]:>7.2f} {hrm:>7.2f} {vm:>6.2f}"
            )

    # ------------------------------------------------------------------ E
    print("\n" + "=" * 86)
    print("E. FUEL-PRICE DISPERSION WITHIN FUEL FAMILY (candidate (c))")
    print("   capacity-weighted, annual-mean plant fuel price $/MMBtu")
    print("=" * 86)
    print(
        f"{'year':>5} {'family':<7} {'n_rows':>7} {'distinct':>9} {'p05':>7} {'p50':>7} {'p95':>7} "
        f"{'p05>p95':>8} {'as $/MWh @p50 HR':>18}"
    )
    for y in years:
        d = D[y]
        k = d["klass"]
        gas = np.array([kk.startswith(("CC_", "CT_", "ST_")) for kk in k])
        coal = np.array([kk.startswith("COAL") for kk in k])
        for name, m in (("gas", gas), ("coal", coal)):
            if not m.any():
                continue
            fp = d["fuel_mean"].astype(float)[m]
            w = d["w"][m]
            hrm = _wmean(d["heat_rate"].astype(float)[m], w)
            q = _wq(fp, w)
            print(
                f"{y:>5} {name:<7} {m.sum():>7} {len(np.unique(np.round(fp, 4))):>9} "
                f"{q[0.05]:>7.3f} {q[0.50]:>7.3f} {q[0.95]:>7.3f} {q[0.95] - q[0.05]:>8.3f} "
                f"{(q[0.95] - q[0.05]) * hrm:>18.2f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
