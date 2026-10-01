"""PJM-NEXT-15 card 2b (zero LP): where does the keeper's CC commitment floor bind vs reality?

``cc_mustrun_per_plant`` forces each CC_REGULAR plant's committed tranche
(``committed_pct`` of nameplate, ``thermal_tranches_PJM.csv``) on in the top
``online_frac`` share of hours ranked by SYSTEM load, where ``online_frac`` is the plant's
POOLED multi-year CEMS synchronization share (``campd_bins.thermal_tranche_online_frac``).
This probe rebuilds that window per plant-year from the keeper's own hourly system demand
(``hourly/system_<y>.parquet``, summed over zones) and reads it against the plant's CAMPD
hourly profile (bench, the same basis as ``_pjmnext15_cc_commitment.py``):

* ``floor_twh``        : committed MW x window hours (upper bound: availability ignored);
* ``floor_off_twh``    : that energy in window hours the real plant was OFF (< 5 % nameplate);
* ``pooled_vs_year``   : committed-MW-weighted pooled ``online_frac`` minus the plant's own
                          on-share in that year (> 0 = the floor over-commits this year).

Aggregated by year and actual-CF third. Writes ``results/phase0/pjm/_pjmnext15_cc_floor_window.json``.
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
from _pjmnext15_cc_commitment import BENCH, KLASS, ON_FRAC, YEARS, _dec  # noqa: E402

BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"
TRANCHES = REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
OUT = REPO / "results/phase0/pjm/_pjmnext15_cc_floor_window.json"


def main() -> None:
    """Rebuild each plant's floor window per year and read it against CAMPD."""
    tt = pd.read_csv(TRANCHES)
    tt = tt[(tt["plant_group"] == KLASS) & tt["online_frac"].notna()]
    meta = {
        str(int(r.plant_code)): (float(r.online_frac), float(r.committed_pct) / 100.0)
        for r in tt.itertuples()
        if np.isfinite(r.committed_pct)
    }
    res = {"what": __doc__.splitlines()[0], "years": {}}
    for y in YEARS:
        sysd = pd.read_parquet(
            BUNDLE / f"hourly/system_{y}.parquet", columns=["pass", "hour", "demand"]
        )
        load = (
            sysd[sysd["pass"] == "P1"]
            .groupby("hour")["demand"]
            .sum()
            .reindex(range(8760))
            .to_numpy(float)
        )
        rank = np.empty(8760, dtype=int)
        rank[np.argsort(-load)] = np.arange(8760)
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        rows = []
        for pid, bp in bench["plants"].items():
            if bp.get("group") != KLASS or bp.get("nodata") or not bp.get("campd"):
                continue
            pc = pid.split("|")[0].split(":")[0]
            npl = float(bp.get("npl") or 0.0)
            if pc not in meta or npl <= 0:
                continue
            of, cp = meta[pc]
            act = _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))
            on_a = act > ON_FRAC * npl
            win = rank < int(round(of * 8760))
            cmw = cp * npl
            rows.append(
                dict(
                    pc=pc,
                    npl=npl,
                    cmw=cmw,
                    cf=float(act.sum()) / (npl * 8760),
                    floor=cmw * win.sum() / 1e6,
                    floor_off=cmw * (win & ~on_a).sum() / 1e6,
                    pooled=of,
                    year_on=float(on_a.mean()),
                )
            )
        df = pd.DataFrame(rows).sort_values("cf")
        cw = df["npl"].cumsum() / df["npl"].sum()
        df["third"] = np.minimum((cw * 3 - 1e-9).astype(int), 2)

        def agg(d: pd.DataFrame) -> dict:
            return {
                "n": int(len(d)),
                "committed_gw": round(d["cmw"].sum() / 1e3, 2),
                "floor_twh": round(d["floor"].sum(), 2),
                "floor_off_twh": round(d["floor_off"].sum(), 2),
                "pooled_minus_year_on": round(
                    float(np.average(d["pooled"] - d["year_on"], weights=d["cmw"])), 3
                ),
            }

        rec = {"all": agg(df)}
        for i, t in enumerate(("low", "mid", "high")):
            rec[t] = agg(df[df["third"] == i])
        res["years"][str(y)] = rec
        print(y, json.dumps(rec), flush=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
