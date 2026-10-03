"""closeout-loss-transfer (zero LP): the PJM loss-surface balance trace, transferred to CAISO and NYISO.

Charter: backcast close-out desk, lane closeout-loss-transfer (owner ruling R-59, 2026-10-03, "Fix PJM
first, then others"). The PJM finding (``docs/records/pjm/closeout-pjm-balance/``) showed that the keeper's
generation-accounting residual is the energy dissipated on the ``pjm_zonal_loss_surface`` links, counted a
second time against a loss-inclusive demand row. This probe repeats that decomposition on the two other
keepers that arm a zonal loss surface:

* CAISO ``2026-10-02-closeout-caiso-w1-arm2`` (``results/calibration/closeout_caiso_w1_a2_span``,
  ``caiso_zonal_loss_surface``);
* NYISO ``2026-10-02-w0-nyiso`` (``results/calibration/w0_nyiso_span``, ``nyiso_zonal_loss_surface``).

Per registered year it computes:

1. the residual ``R = gen (incl. the import node) - storage net charge - demand`` from the committed hourly
   sidecars, reusing :func:`_closeoutpjm_balance_trace.balance`;
2. ``L = sum_l,t eps_l,t * F_l,t`` on the one-way internal links, with ``F`` from each leg's committed
   ``flows.parquet`` (read by full shard SHA, :data:`LEG_SHA`) and ``eps`` rebuilt exactly as
   ``build_caiso_link_loss`` / ``build_nyiso_link_loss`` build it (the ISO's own internal-link predicate and,
   for CAISO, the FSNO -> NP15 surface-row inheritance), and ``R - L``;
3. ``L`` by receiving zone, which is the share option A would take off each zone's demand row;
4. the demand basis against EIA-930: ``D - (NG - TI)`` for the BA, and model demand minus EIA-930 ``D``;
5. a first-order attribution of ``L`` to classes by a merit-order peel of ``unit_marginal``. Two variants:
   ``econ`` peels, highest P1 offer ``mc`` first, only units that are economically dispatched
   (``mc <= zone price + 1 $/MWh``; a unit dispatched above its zone's price sits on a floor and would not
   back down) and lets the priced import node peel; ``pjm`` is the PJM probe's convention (every dispatched
   non-nuclear, non-hydro, non-import, non-virtual unit). The ``econ`` peel also gives the per-hour change of
   the marginal offer, the first-order C3a estimate;
6. the C1 rows (``calibration_verdict`` fuel-mix records) with the repaired class volume and share
   (model class TWh minus its ``econ`` peel; the rubric's own ``_gen_totals`` model generation minus every
   peeled class it counts), and a PASS/FAIL flip flag;
7. the C3a rows under two first-order price estimators: ``step`` (the ``econ`` peel's mean change of the top
   economic offer, an upper end: it ignores zonal separation) and ``slope`` (the keeper's own load-weighted
   system price regressed on system demand per month, times the hour's loss, demand-weighted).

Reads only committed bytes plus the leg ``flows.parquet`` it is pointed at. Writes
``results/phase0/governance/_closeout_loss_transfer_trace.json``.

Usage::

    python scripts/probes/_closeout_loss_transfer_trace.py --legs <dir with <ISO>/<year>/flows.parquet>
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.loss_surface import load_zone_month_deviation
from market_sim.model.interchange.caiso import _caiso_internal, _caiso_loss_surface_row
from market_sim.model.interchange.nyiso import _nyiso_internal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import calibration_verdict as _cv  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/phase0/governance/_closeout_loss_transfer_trace.json"
E930 = REPO / "data/raw/eia-930"
TWH = 1e6
A = " (MW) (Adjusted)"

_spec = importlib.util.spec_from_file_location(
    "_closeoutpjm_balance_trace", REPO / "scripts/probes/_closeoutpjm_balance_trace.py"
)
_pjm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pjm)
balance = _pjm.balance
MONTH_OF_HOUR = _pjm.MONTH_OF_HOUR

ISOS = {
    "CAISO": {
        "run_id": "2026-10-02-closeout-caiso-w1-arm2",
        "bundle": REPO / "results/calibration/closeout_caiso_w1_a2_span",
        "ba": "CISO",
        "internal": _caiso_internal,
        "row": _caiso_loss_surface_row,
        # RESULT-closeout-caiso-w1-arm2-2026-10-02.md, leg table.
        "leg_sha": {
            2019: "1ca02579594490fff199211726b16eebcb225b65",
            2020: "07535d603a74f94f56ce1ab3bf283942ed469ac4",
            2021: "905067f84abef9f4500dc431cd4ec5da2400438b",
            2022: "3a53b2ceab09756b2d7d03424f70774a50b0ab59",
            2023: "9794740e58ffe46c6a8563d7c23ae7f6cdb981f3",
            2024: "61f6ad9322336d2a17264bce294927626976375c",
            2025: "ebeacb2b9b3555dbfffec665c07cc33a4da07e34",
        },
    },
    "NYISO": {
        "run_id": "2026-10-02-w0-nyiso",
        "bundle": REPO / "results/calibration/w0_nyiso_span",
        "ba": "NYIS",
        "internal": _nyiso_internal,
        "row": lambda surf, z: np.asarray(surf[z], dtype=float),
        # PR #7041 shard provenance (short SHAs there; resolved to full SHAs on GitHub).
        "leg_sha": {
            2021: "2bf25795eee138dd36914aa79d9e0d9db7834200",
            2022: "ae7708c1b4cfd00d510de8e57b566a17b5f3ce08",
            2023: "95ad95473c6dd2da1d9a225c71dfda1504f6bafc",
            2024: "d96a1edc87967e4140e3630f77d3580467529a20",
            2025: "8025f6d099bb9aacc600674f41cf0d9453e7ef9b",
        },
    },
}
# Not movable at the margin in a first-order peel (energy-budgeted or must-run).
FIXED = {"nuclear", "hydro"}
# A dispatched unit priced above its zone's dual by more than this sits on a floor (D-2 forced energy).
ECON_TOL = 1.0


def link_losses(iso: str, flows: pd.DataFrame, year: int) -> pd.DataFrame:
    """Return per-(link, hour) dissipated MW ``eps * F`` as the ISO's ``build_<iso>_link_loss`` books it."""
    spec = ISOS[iso]
    surf = load_zone_month_deviation(iso, year)
    f = flows[flows["pass"] == "P1"].copy()
    f = f[[spec["internal"](a, b) for a, b in zip(f.from_zone, f.to_zone)]]
    eps = np.zeros(len(f))
    for (a, b), idx in f.groupby(["from_zone", "to_zone"]).groups.items():
        dev_a, dev_b = spec["row"](surf, a), spec["row"](surf, b)
        eps_m = np.maximum(0.0, (dev_b - dev_a) / (1.0 + dev_b))
        pos = f.index.get_indexer(idx)
        eps[pos] = eps_m[MONTH_OF_HOUR[f.loc[idx, "hour"].to_numpy()]]
    f["eps"] = eps
    f["loss_mw"] = eps * f.mw.clip(lower=0.0)
    return f


def e930(ba: str, year: int) -> dict:
    """Annual BA totals (TWh) from EIA-930 BALANCE, Adjusted columns; TI is net export (+)."""
    d = pd.concat(
        pd.read_parquet(p)
        for p in sorted(E930.glob(f"EIA930_BALANCE_{year}_*.parquet"))
    )
    d = d[d["Balancing Authority"] == ba]
    col = {
        "demand": "Demand" + A,
        "ng": "Net Generation" + A,
        "ti_export": "Total Interchange" + A,
    }
    out = {
        k: float(pd.to_numeric(d[c], errors="coerce").sum() / TWH)
        for k, c in col.items()
    }
    out["d_minus_ng_minus_ti"] = out["demand"] - (out["ng"] - out["ti_export"])
    return out


def peel(bundle: Path, year: int, loss_hour: np.ndarray) -> dict:
    """First-order class attribution of the hourly loss, and the marginal-offer change (econ peel)."""
    um = pd.read_parquet(
        bundle / f"hourly/unit_marginal_{year}.parquet",
        columns=["pass", "fuel", "plant_group", "zone", "hour", "mw", "mc"],
    )
    um = um[(um["pass"] == "P1") & (um.mw > 0.0)]
    um = um[
        ~um.fuel.astype(str).isin(FIXED)
        & ~um.plant_group.astype(str).str.startswith("VIRTUAL")
    ]
    fuel = um.fuel.astype(str)
    grp = um.plant_group.astype(str)
    um = um.assign(
        grp=np.where(fuel == "import", "import", np.where(grp == "", fuel, grp))
    )
    sysd = pd.read_parquet(
        bundle / f"hourly/system_{year}.parquet",
        columns=["pass", "zone", "hour", "price"],
    )
    sysd = sysd[sysd["pass"] == "P1"]
    um = um.merge(sysd[["zone", "hour", "price"]], on=["zone", "hour"], how="left")
    res = {}
    variants = {
        "econ": um[um.mc <= um.price + ECON_TOL],
        "pjm": um[um.grp != "import"],
    }
    for name, u in variants.items():
        u = u.sort_values(["hour", "mc"], ascending=[True, False])
        mw = u.mw.to_numpy()
        cum = u.groupby("hour").mw.cumsum().to_numpy()
        need = loss_hour[u.hour.to_numpy()]
        take = np.clip(need - (cum - mw), 0.0, mw)
        by = pd.Series(take).groupby(u.grp.to_numpy()).sum() / TWH
        res[name] = {
            "by_class_twh": {
                k: round(float(v), 3)
                for k, v in by.sort_values(ascending=False).items()
                if v > 0.0005
            },
            "covered_twh": round(float(take.sum() / TWH), 3),
        }
        if name == "econ":
            top = u.groupby("hour").mc.first()
            # The new marginal offer: the first unit (desc mc) not fully peeled.
            left = u.assign(left=mw - take)
            left = left[left["left"] > 1e-6]
            new = left.groupby("hour").mc.first()
            dp = (new.reindex(top.index) - top).fillna(0.0)
            dp = dp.reindex(range(8760), fill_value=0.0)
            res[name]["mean_marginal_offer_change_usd"] = round(float(dp.mean()), 3)
            res[name]["hours_offer_moves"] = int((dp < -0.01).sum())
            res[name]["_class"] = by.to_dict()
    return res


def verdict_rows(run_id: str) -> dict:
    """The C1 fuel-mix and C3a mean-LMP records of the committed keeper (``calibration_verdict --json``),
    plus the rubric's own C1 generation totals per year (``calibration_verdict._gen_totals``)."""
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            run_id,
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO,  # exits 1 on NOT-YET
    ).stdout
    v = json.loads(out)
    rows: dict = {"fuelmix": {}, "price_mean": {}, "gen_totals": {}, "class_keys": {}}
    for crit in ("fuelmix", "price_mean"):
        for r in v["criteria"][crit]["records"]:
            rows[crit].setdefault(r["year"], []).append(r)
    art = _cv.load_artifacts(run_id)
    for y, ypay in art["payload"]["years"].items():
        yb = art["bench"].get(int(y)) or art["bench"].get(y) or {}
        rows["gen_totals"][int(y)] = _cv._gen_totals(ypay, yb)
        rows["class_keys"][int(y)] = set((yb.get("classFull") or {}).keys())
    return rows


def c1_after(
    recs: list[dict], removed: dict, totals: tuple[float, float], keys: set
) -> list[dict]:
    """Re-test each C1 row: class volume minus its peel, the rubric's model generation total minus
    every peeled class it counts (the import node is not in ``classFull``, so its peel moves no total)."""
    m_gen, a_gen = totals
    m_gen1 = m_gen - sum(float(v) for k, v in removed.items() if k in keys)
    out = []
    for r in recs:
        if not isinstance(r.get("model"), (int, float)) or not isinstance(
            r.get("actual"), (int, float)
        ):
            continue
        m = re.search(r"= ±([0-9.]+) TWh", r.get("tol") or "")
        band = float(m.group(1)) if m else None
        x = float(removed.get(r["key"], 0.0))
        d0 = r["model"] - r["actual"]
        d1 = d0 - x
        sh0 = 100 * (r["model"] / m_gen - r["actual"] / a_gen)
        sh1 = 100 * ((r["model"] - x) / m_gen1 - r["actual"] / a_gen)
        gated = r["status"] in ("PASS", "FAIL")
        ok1 = band is not None and abs(d1) <= band and abs(sh1) <= 3.0
        flip = None
        if gated and r["status"] == "PASS" and not ok1:
            flip = "PASS->FAIL"
        elif gated and r["status"] == "FAIL" and ok1:
            flip = "FAIL->PASS"
        out.append(
            {
                "key": r["key"],
                "status": r["status"],
                "band_twh": band,
                "delta_twh": round(d0, 2),
                "share_pp": r.get("share_pp"),
                "share_pp_check": round(sh0, 2),
                "peel_twh": round(x, 3),
                "delta_after_twh": round(d1, 2),
                "share_pp_after": round(sh1, 2),
                "flip": flip,
            }
        )
    return out


def slope_price_change(bundle: Path, year: int, loss_hour: np.ndarray) -> float:
    """Second C3a estimator: the keeper's own load-weighted system price against system demand, a linear
    slope per month, times the hour's loss; returned as the demand-weighted mean change ($/MWh)."""
    sysd = pd.read_parquet(
        bundle / f"hourly/system_{year}.parquet",
        columns=["pass", "zone", "hour", "price", "demand"],
    )
    sysd = sysd[(sysd["pass"] == "P1") & (sysd.demand > 0)]
    g = sysd.assign(pd_=sysd.price * sysd.demand).groupby("hour")
    d = g.demand.sum().reindex(range(8760)).to_numpy()
    p = (g.pd_.sum() / g.demand.sum()).reindex(range(8760)).to_numpy()
    dp = np.zeros(8760)
    for m in range(12):
        h = MONTH_OF_HOUR == m
        lo, hi = np.nanpercentile(p[h], [1, 99])
        k = h & (p >= lo) & (p <= hi)
        slope = np.polyfit(d[k], p[k], 1)[0]
        dp[h] = -max(slope, 0.0) * loss_hour[h]
    return float(np.sum(dp * d) / np.sum(d))


def c3a_after(recs: list[dict], dps: dict) -> list[dict]:
    """Shift the model mean LMP by each estimator's mean price change; re-test against the row's band."""
    out = []
    for r in recs:
        if not isinstance(r.get("model"), (int, float)) or not isinstance(
            r.get("actual"), (int, float)
        ):
            out.append(
                {"key": r.get("key"), "status": r["status"], "note": r.get("magnitude")}
            )
            continue
        m = re.search(r"±\s*([0-9.]+)\s*%", r.get("tol") or "")
        band = float(m.group(1)) if m else None
        row = {
            "key": r.get("key"),
            "status": r["status"],
            "band_pct": band,
            "model": round(r["model"], 2),
            "actual": round(r["actual"], 2),
            "err_pct": round(100 * (r["model"] / r["actual"] - 1), 2),
        }
        for name, dp in dps.items():
            e1 = 100 * ((r["model"] + dp) / r["actual"] - 1)
            flip = None
            if band is not None and r["status"] == "PASS" and abs(e1) > band:
                flip = "PASS->FAIL"
            elif band is not None and r["status"] == "FAIL" and abs(e1) <= band:
                flip = "FAIL->PASS"
            row[f"err_pct_after_{name}"] = round(e1, 2)
            row[f"flip_{name}"] = flip
        out.append(row)
    return out


def main() -> None:
    """Run the trace for CAISO and NYISO and write the JSON payload."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--legs",
        type=Path,
        required=True,
        help="dir holding <ISO>/<year>/flows.parquet",
    )
    args = ap.parse_args()
    out: dict = {}
    for iso, spec in ISOS.items():
        rows = verdict_rows(spec["run_id"])
        res = {
            "run_id": spec["run_id"],
            "bundle": str(spec["bundle"].relative_to(REPO)),
            "leg_sha": spec["leg_sha"],
            "years": {},
        }
        for y in spec["leg_sha"]:
            b = balance(spec["bundle"], y)
            fl = link_losses(
                iso, pd.read_parquet(args.legs / iso / str(y) / "flows.parquet"), y
            )
            loss_hour = (
                fl.groupby("hour")
                .loss_mw.sum()
                .reindex(range(8760), fill_value=0.0)
                .to_numpy()
            )
            gap = b["_resid_hour"] - loss_hour
            L = float(loss_hour.sum() / TWH)
            lossy = fl[fl.eps > 0]
            pl = peel(spec["bundle"], y, loss_hour)
            removed = pl["econ"].pop("_class")
            dp_slope = slope_price_change(spec["bundle"], y, loss_hour)
            sysd = pd.read_parquet(spec["bundle"] / f"hourly/system_{y}.parquet")
            sysd = sysd[sysd["pass"] == "P1"]
            e = e930(spec["ba"], y)
            row = {k: round(v, 3) for k, v in b.items() if not k.startswith("_")}
            row.update(
                {
                    "loss_twh": round(L, 3),
                    "residual_minus_loss_twh": round(float(gap.sum() / TWH), 4),
                    "hours_abs_gap_gt_1mw": int((np.abs(gap) > 1.0).sum()),
                    "max_abs_hourly_gap_mw": round(float(np.abs(gap).max()), 2),
                    "loss_pct_of_demand": round(100 * L / b["demand"], 3),
                    "flow_on_lossy_links_twh": round(float(lossy.mw.sum() / TWH), 2),
                    "flow_weighted_eps_pct": round(
                        float(100 * lossy.loss_mw.sum() / max(lossy.mw.sum(), 1e-9)), 3
                    ),
                    "loss_peak_hour_mw": round(float(loss_hour.max()), 1),
                    "loss_by_link_twh": {
                        f"{a}>{c}": round(float(v / TWH), 3)
                        for (a, c), v in fl.groupby(["from_zone", "to_zone"])
                        .loss_mw.sum()
                        .sort_values(ascending=False)
                        .items()
                        if v / TWH > 0.001
                    },
                    "loss_by_receiving_zone_twh": {
                        z: round(float(v / TWH), 3)
                        for z, v in fl.groupby("to_zone")
                        .loss_mw.sum()
                        .sort_values(ascending=False)
                        .items()
                        if v / TWH > 0.001
                    },
                    "model_demand_by_zone_twh": {
                        z: round(float(v / TWH), 2)
                        for z, v in sysd.groupby("zone").demand.sum().items()
                        if v > 0
                    },
                    "e930": {k: round(v, 3) for k, v in e.items()},
                    "model_demand_minus_e930_d": round(b["demand"] - e["demand"], 3),
                    "peel": pl,
                    "mean_price_change_slope_usd": round(dp_slope, 3),
                    "c1": c1_after(
                        rows["fuelmix"].get(y, []),
                        removed,
                        rows["gen_totals"][y],
                        rows["class_keys"][y],
                    ),
                    "c3a": c3a_after(
                        rows["price_mean"].get(y, []),
                        {
                            "step": pl["econ"]["mean_marginal_offer_change_usd"],
                            "slope": dp_slope,
                        },
                    ),
                }
            )
            res["years"][str(y)] = row
            print(
                iso,
                y,
                row["residual"],
                row["loss_twh"],
                row["residual_minus_loss_twh"],
                pl["econ"]["by_class_twh"],
                pl["econ"]["mean_marginal_offer_change_usd"],
                round(dp_slope, 3),
            )
        out[iso] = res
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT.relative_to(REPO))


if __name__ == "__main__":
    main()
