"""PJM-NEXT-29 supplementary (ZERO LP, POST HOC): where in the hour set the COAL_BIT gap sits.

Not a pre-registered reading (the FINDING §1 readings are in ``_pjmnext29_lowhour_setters``);
labelled post hoc in the FINDING §2. Three checks on keeper ``w0_pjm_span``:

* S1 — COAL_BIT model − CAMPD (TWh) by real implied-HR bin (real DA LMP / delivered gas, the
  NEXT-11 series), with the bin's mean model/real price ratio and hour share.
* S2 — hours with real implied HR >= :data:`HI_HR` (every coal unit in the money in both): model
  COAL_BIT MW, available ``cap_mw`` and CAMPD MW (bench plants with data), and the per-plant gap.
* S3 — accounting: model COAL_BIT TWh at plants the bench carries no COAL_BIT CAMPD record for.

Model: P1 ``class_hourly`` / ``unit_marginal`` sidecars (tree, else the ``origin/main`` blob).
CAMPD: ``frontend/data/backcast/bench/PJM/<y>.json.gz`` (``_pjmnext16_cc_loading._dec``).
Writes ``results/phase0/pjm/_pjmnext29_coalbit_bins.json``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
sys.path.insert(0, str(REPO))
from _pjmnext28_sunk_noload import _parquet, gas_daily  # noqa: E402
from _pjmnext29_lowhour_setters import real_low_hours  # noqa: E402

from scripts.probes._pjmnext16_cc_loading import _dec  # noqa: E402

BENCH = REPO / "frontend/data/backcast/bench/PJM"
OUT = REPO / "results/phase0/pjm/_pjmnext29_coalbit_bins.json"
YEARS = tuple(range(2019, 2026))
T = 8760
GROUP = "COAL_BIT"
#: Real implied-HR bin edges (MMBtu/MWh); 6.5 is the FINDING §1 population threshold.
EDGES = (0.0, 6.5, 8.0, 10.0, 13.0, np.inf)
HI_HR = 10.0
EXTERNAL_ZONE = "PJM_external"


def campd_by_plant(y: int) -> dict[int, np.ndarray]:
    """CAMPD hourly MW per COAL_BIT bench plant with data (split keys ``pc:GROUP`` folded)."""
    bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    out: dict[int, np.ndarray] = {}
    for k, bp in bench.items():
        if bp.get("group") != GROUP or bp.get("nodata") or not bp.get("campd"):
            continue
        a = np.zeros(T)
        v = _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))[:T]
        a[: len(v)] = v
        pc = int(str(k).split(":")[0])
        out[pc] = out.get(pc, 0.0) + a
    return out


def run_year(y: int, gas: pd.Series) -> dict:
    """S1-S3 for one year."""
    rl = real_low_hours(y, gas).reindex(range(T))
    hr = (rl["p_real"] / rl["gas"]).to_numpy()
    s = _parquet(f"system_{y}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"].astype(str) != EXTERNAL_ZONE)]
    s = s.assign(pw=s["price"] * s["demand"])
    g = s.groupby("hour")[["pw", "demand"]].sum().reindex(range(T))
    pm = (g["pw"] / g["demand"]).to_numpy()
    um = _parquet(
        f"unit_marginal_{y}.parquet",
        columns=["plant_code", "hour", "mw", "cap_mw"],
        filters=[("plant_group", "=", GROUP)],
    )
    m = um.groupby("hour")["mw"].sum().reindex(range(T)).fillna(0.0).to_numpy()
    cp = campd_by_plant(y)
    a = np.sum(list(cp.values()), axis=0) if cp else np.zeros(T)
    d = m - a

    b = np.digitize(hr, EDGES) - 1
    bins = []
    for k in range(len(EDGES) - 1):
        sel = b == k
        bins.append(
            {
                "bin": f"{EDGES[k]:g}-{EDGES[k + 1]:g}",
                "hour_share": round(float(sel.mean()), 3),
                "gap_twh": round(float(d[sel].sum()) / 1e6, 2),
                "model_over_real_price": round(
                    float(
                        np.nanmean(pm[sel]) / np.nanmean(rl["p_real"].to_numpy()[sel])
                    ),
                    3,
                )
                if sel.any()
                else None,
            }
        )

    hi = np.where(hr >= HI_HR)[0]
    u = um[um["hour"].isin(hi)]
    pp = u.groupby("plant_code")[["mw", "cap_mw"]].sum() / max(len(hi), 1)
    pp["campd"] = pd.Series({pc: float(v[hi].mean()) for pc, v in cp.items()})
    with_data = pp[pp["campd"].notna()]
    no_data_twh = float(um[~um["plant_code"].isin(list(cp))]["mw"].sum() / 1e6)  # S3
    gap = (with_data["mw"] - with_data["campd"]).sort_values(ascending=False)
    return {
        "year": y,
        "model_twh": round(float(m.sum()) / 1e6, 2),
        "campd_twh": round(float(a.sum()) / 1e6, 2),
        "S1_bins": bins,
        "S2_hi_hours": int(len(hi)),
        "S2_model_mw": round(float(with_data["mw"].sum())),
        "S2_model_cap_mw": round(float(with_data["cap_mw"].sum())),
        "S2_campd_mw": round(float(with_data["campd"].sum())),
        "S2_model_mw_over_cap": round(
            float(with_data["mw"].sum() / with_data["cap_mw"].sum()), 3
        ),
        "S2_campd_over_model_cap": round(
            float(with_data["campd"].sum() / with_data["cap_mw"].sum()), 3
        ),
        "S2_top10_gap_plants_mw": {
            int(k): round(float(v)) for k, v in gap.head(10).items()
        },
        "S3_model_twh_at_plants_without_campd": round(no_data_twh, 2),
    }


def main(years: list[int]) -> None:
    """Run every year and write the JSON."""
    gas = gas_daily()
    rows = []
    for y in years:
        r = run_year(y, gas)
        rows.append(r)
        print(
            f"{y}: gap {r['model_twh'] - r['campd_twh']:+.1f} TWh | "
            + " | ".join(
                f"[{x['bin']}] {x['gap_twh']:+.1f} ({x['model_over_real_price']})"
                for x in r["S1_bins"]
            )
            + f" | hi-hr mw/cap {r['S2_model_mw_over_cap']} campd/cap "
            f"{r['S2_campd_over_model_cap']} | no-campd {r['S3_model_twh_at_plants_without_campd']}",
            flush=True,
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "probe": "PJM-NEXT-29 supplementary (post hoc): COAL_BIT gap by real-price bin",
                "keeper_bundle": "results/calibration/w0_pjm_span",
                "edges": [str(e) for e in EDGES],
                "hi_hr": HI_HR,
                "method": __doc__,
                "years": rows,
            },
            indent=2,
        )
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
