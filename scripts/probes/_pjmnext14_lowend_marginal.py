"""PJM-NEXT-14 card 1 (zero LP): which keeper units price the LOW-END hours, and at what bid.

Reads a ``fleet_only`` dump written by ``_pjmnext13_fleet_dump.py`` (keeper recipe,
``mc_base`` + the P1 mid-curve markup) plus committed artifacts only: the keeper's
run payload (per-plant hourly MW, 1 %-of-nameplate bytes), its ``system_<y>`` hourly
sidecar (zonal P1 price, demand) and the PJM RT system price
(``_validation-source/actual_lmp_hourly_PJM.parquet``). No LP.

LOW-END HOURS: actual RT price below ``6.5 x`` the IMM's monthly PRODUCTION-area gas
(Dominion South + TGP Z4 + Leidy, ``som-competitive-conduct``), i.e. below an efficient
CC's fuel cost at production gas — the NEXT-13 card-2 definition.

MARGINAL CANDIDATE, per zone-hour: a payload plant whose hourly MW sits strictly inside
one of its rebuilt tranches (``pmax x availability`` stack, ±1.5 % of nameplate for the
byte quantization — the NEXT-13 ``card3_plants`` rule, extended from coal to every class
the payload carries). The candidate whose reconstructed bid is nearest the zone's P1
price is recorded. The reconstructed bid omits P1's startup-amortization markup (it is
built from the P0 dispatch, which needs an LP), so ``bid <= price`` is expected for
cycling classes; the gap is reported, never corrected.

Reported per year, load-weighted over zone-hours, low-end hours vs all hours:
class x tranche-kind share of the nearest candidate (``econ_floored`` = econ row whose
mid-curve markup raises it at that hour, ``econ_own`` = econ row at its own cost),
the share with no candidate, the median model price and the median nearest bid.
Writes ``results/calibration/_pjmnext14_lowend_marginal.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext10_coal_phase0 as P10  # noqa: E402

OUT = REPO / "results/calibration/_pjmnext14_lowend_marginal.json"
BUNDLE = P10.BUNDLE
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
SOM = REPO / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
#: Efficient-CC heat rate used to define a low-end hour (NEXT-12/13 convention).
LOW_HR = 6.5
#: Byte-quantization floor of the payload (NEXT-13 ``BOUNDARY_TOL``).
BOUNDARY_TOL = 0.015
TRANCHE_ORDER = (
    "mustrun",
    "committed",
    "sync",
    "econc00",
    "econc01",
    "econc02",
    "econc03",
    "econc04",
    "econc05",
    "peak",
)
MONTH = pd.date_range("2001-01-01", periods=8760, freq="h").month.to_numpy() - 1


def _rank(uid: str) -> int:
    """Position of a tranche suffix in the stack (unknown suffixes last)."""
    sfx = uid.rsplit("_", 1)[-1]
    for j, t in enumerate(TRANCHE_ORDER):
        if sfx == t or (t.startswith("econ") and sfx.startswith("econ") and sfx == t):
            return j
    return 50 + (0 if sfx.startswith("econ") else 1)


def _kind(uid: str) -> str:
    """Tranche kind of a unit id."""
    sfx = uid.rsplit("_", 1)[-1]
    if sfx.startswith("econ"):
        return "econ"
    if sfx.startswith("peak"):
        return "peak"
    return sfx if sfx in ("mustrun", "committed", "sync") else "other"


def prod_gas_hourly(y: int) -> np.ndarray:
    """IMM monthly production-area gas, broadcast to 8760 hours."""
    d = pd.read_csv(SOM)
    d = d[
        (d.iso == "PJM")
        & (d.year == y)
        & (d.metric == "spot_price_digitized_usd_per_mmbtu")
        & (d.fleet_segment == "production_gas")
        & d.period.str.startswith("month_")
    ]
    m = d.assign(mo=d.period.str[-2:].astype(int)).set_index("mo")["value"]
    return m.reindex(range(1, 13)).to_numpy(float)[MONTH]


def analyse(y: int, f: dict, run: dict) -> dict:
    """Nearest-bid partial-loading candidate per zone-hour, low-end vs all hours."""
    sysd = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    price = sysd.pivot_table(index="hour", columns="zone", values="price").sort_index()
    load = sysd.pivot_table(index="hour", columns="zone", values="demand").sort_index()
    act = pd.read_parquet(ACTUAL)
    rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:8760]
    low = rt < LOW_HR * prod_gas_hourly(y)

    uid = f["unit_ids"].astype(str)
    grp, pc, zn = f["plant_group"].astype(str), f["plant_code"].astype(str), f["zone"]
    zn = zn.astype(str)
    avail = (f["pmax"][:, None] * f["availability"])[:, :8760]
    mk = f.get("midcurve_markup")
    mk = np.zeros_like(avail) if mk is None else mk[:, :8760]
    bid = f["mc_base"][:, :8760] + mk
    b = P10.bench(y)["plants"]
    mp = run[str(y)]["plants"]

    zones = [z for z in price.columns if z in set(zn)]
    zi = {z: i for i, z in enumerate(zones)}
    best_gap = np.full((8760, len(zones)), np.inf)
    best_cls = np.full((8760, len(zones)), "", dtype=object)
    best_kind = np.full((8760, len(zones)), "", dtype=object)
    best_bid = np.full((8760, len(zones)), np.nan)
    pr = price[zones].to_numpy()[:8760]
    n_pl = 0
    for key, v in mp.items():
        code = key.split(":")[0]
        sel = np.where(pc == code)[0]
        if not len(sel):
            continue
        cls = str(b.get(key, {}).get("group") or grp[sel[0]])
        sel = sel[grp[sel] == cls] if (grp[sel] == cls).any() else sel
        z = zn[sel[0]]
        if z not in zi:
            continue
        npl = b.get(key, {}).get("npl") or float(f["pmax"][sel].sum())
        m = P10.decode(v["m"], v.get("m_ann"), npl)[:8760]
        order = sorted(sel, key=lambda i: _rank(uid[i]))
        cum = np.cumsum(avail[order], axis=0)
        lo = np.vstack([np.zeros(8760), cum[:-1]])
        tol = BOUNDARY_TOL * npl
        inside = (m[None, :] > lo + tol) & (m[None, :] < cum - tol)
        if not inside.any():
            continue
        n_pl += 1
        j = zi[z]
        for r, i in enumerate(order):
            h = inside[r]
            if not h.any():
                continue
            gap = np.abs(bid[i] - pr[:, j])
            better = h & (gap < best_gap[:, j])
            if not better.any():
                continue
            best_gap[better, j] = gap[better]
            best_cls[better, j] = cls
            k = _kind(uid[i])
            if k == "econ":
                k = np.where(mk[i] > 0.01, "econ_floored", "econ_own")[better]
            best_kind[better, j] = k
            best_bid[better, j] = bid[i][better]

    w = load[zones].to_numpy()[:8760]

    def table(mask_h: np.ndarray) -> dict:
        mh = np.broadcast_to(mask_h[:, None], w.shape)
        ww = np.where(mh, w, 0.0)
        tot = ww.sum()
        has = np.isfinite(best_gap)
        shares: dict[str, float] = {}
        for c, k, x in zip(best_cls[has], best_kind[has], ww[has]):
            shares[f"{c}:{k}"] = shares.get(f"{c}:{k}", 0.0) + x
        by_cls: dict[str, float] = {}
        for ck, x in shares.items():
            c = ck.split(":")[0]
            by_cls[c] = by_cls.get(c, 0.0) + x
        sel = has & mh
        return {
            "zonehour_weight_share_no_candidate": round(float(ww[~has].sum() / tot), 3),
            "by_class": {
                k: round(v / tot, 3)
                for k, v in sorted(by_cls.items(), key=lambda kv: -kv[1])
            },
            "by_class_kind": {
                k: round(v / tot, 3)
                for k, v in sorted(shares.items(), key=lambda kv: -kv[1])[:12]
            },
            "median_model_price": round(float(np.median(pr[mh])), 2),
            "median_nearest_bid": round(float(np.nanmedian(best_bid[sel])), 2),
            "median_abs_gap": round(float(np.median(best_gap[sel])), 2),
            "share_gap_le_1usd": round(float((best_gap[sel] <= 1.0).mean()), 3),
        }

    return {
        "n_payload_plants_partial": n_pl,
        "low_hour_share": round(float(low.mean()), 3),
        "median_actual_rt_low": round(float(np.median(rt[low])), 2)
        if low.any()
        else None,
        "median_prod_gas_x6p5": round(float(np.median(LOW_HR * prod_gas_hourly(y))), 2),
        "low_end_hours": table(low) if low.any() else None,
        "all_hours": table(np.ones(8760, bool)),
    }


def main() -> None:
    """Run card 1 for every dumped year given on the command line."""
    d = Path(sys.argv[1])
    years = [int(a) for a in sys.argv[2:]]
    run = P10.load_run()
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for y in years:
        z = np.load(d / f"pjmnext13_fleet_{y}.npz", allow_pickle=True)
        rec = analyse(y, {k: z[k] for k in z.files}, run)
        out[str(y)] = rec
        print(y, json.dumps(rec, indent=1), flush=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
