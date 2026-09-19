"""caiso-287: difference a MER control replay against the committed CAISO keeper.

ZERO LP. Two jobs, per year:

1. **The marginal-carbon census.** The emissions dual ``marginal_emission_rate``
   landed on ``main`` 2026-09-18 and is not retroactive, so no committed keeper
   carries it. These replays produce it. A non-trivial share of zone-hours at
   exactly 0.0 **at the WECC_* import nodes is expected, not a defect** — their
   duals go degenerate (caiso-285 G1 measured 390 WECC_PNW zone-hours flipping
   between $0 and a binding value) — so the zero share is reported PER ZONE.

2. **The G-DRIFT form-4 check** (rule 29 ``[R-SCREEN]`` (b)): is the committed
   keeper a valid control at HEAD? The replay runs the keeper's own recipe, so
   a bit-identical result would confirm form 4 empirically.

**What this script must NOT do is call a non-identical result a regression on
its own.** ``price`` is an LP DUAL (rule 4 ``[R-DUALS]``), and a degenerate LP
has many optimal bases that price differently while the PRIMAL solution is
unchanged. So the report separates three things that a single max|delta| would
conflate:

* the **primal** solution (``slack``, ``dump``, ``demand``) — if these move, the
  dispatch itself changed and that IS a regression;
* the **scored** quantity (the load-weighted mean price, which is what C3a
  gates on) — the number a determination actually depends on;
* the **per-zone** dual spread — where degeneracy shows up, and whether the
  magnitude is confined to the import nodes that are known to carry it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent


def load_p1(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    return df[df["pass"] == "P1"].sort_values(["zone", "hour"]).reset_index(drop=True)


def main(keeper: Path, replay: Path, year: int, out: Path) -> None:
    k = load_p1(keeper / "hourly" / f"system_{year}.parquet")
    r = load_p1(replay / "hourly" / f"system_{year}.parquet")
    if not (
        (k["zone"].to_numpy() == r["zone"].to_numpy()).all()
        and (k["hour"].to_numpy() == r["hour"].to_numpy()).all()
    ):
        raise SystemExit("FAIL: zone/hour grids do not align; refusing to compare")

    w = k["demand"].clip(lower=0).to_numpy()
    kp, rp = k["price"].to_numpy(), r["price"].to_numpy()
    d = rp - kp
    lw_k = float(np.average(kp, weights=w))
    lw_r = float(np.average(rp, weights=w))

    # The PRIMAL legs. These moving is a real regression; the duals moving is
    # not, on its own.
    primal = {}
    for c in ("slack", "dump", "demand"):
        if c in k.columns and c in r.columns:
            primal[c] = float(np.max(np.abs(k[c].to_numpy() - r[c].to_numpy())))

    per_zone = {}
    for z, g in k.assign(d=d).groupby("zone"):
        ad = g["d"].abs()
        per_zone[str(z)] = {
            "n_differing": int((ad > 0).sum()),
            "share_differing": float((ad > 0).mean()),
            "max_abs_delta": float(ad.max()),
            "mean_delta": float(g["d"].mean()),
        }

    mer = {}
    if "marginal_emission_rate" in r.columns:
        m = r["marginal_emission_rate"]
        mer["present"] = True
        mer["all_null"] = bool(m.isna().all())
        mv = m.to_numpy(dtype=float)
        ok = ~np.isnan(mv)
        mer["load_weighted_mean"] = (
            float(np.average(mv[ok], weights=w[ok])) if ok.any() else None
        )
        mer["p10_median_p90"] = (
            [float(x) for x in np.quantile(mv[ok], [0.10, 0.50, 0.90])]
            if ok.any()
            else None
        )
        mer["share_exactly_zero_overall"] = float((mv[ok] == 0.0).mean()) if ok.any() else None
        mer["share_exactly_zero_by_zone"] = {}
        for z, g in r.groupby("zone"):
            gv = g["marginal_emission_rate"].to_numpy(dtype=float)
            gok = ~np.isnan(gv)
            mer["share_exactly_zero_by_zone"][str(z)] = (
                float((gv[gok] == 0.0).mean()) if gok.any() else None
            )
    else:
        mer["present"] = False

    ad = np.abs(d)
    nz = ad[ad > 0]
    rec = {
        "year": year,
        "keeper_bundle": str(keeper).replace(f"{REPO}/", ""),
        "replay_bundle": str(replay).replace(f"{REPO}/", ""),
        "keeper_git_sha": json.loads((keeper / "meta.json").read_text()).get("git_sha"),
        "replay_git_sha": json.loads((replay / "meta.json").read_text()).get("git_sha"),
        "zone_hours": int(len(k)),
        "PRIMAL_max_abs_delta": primal,
        "primal_identical": all(v == 0.0 for v in primal.values()),
        "SCORED_load_weighted_mean_price": {
            "keeper": lw_k,
            "replay": lw_r,
            "delta": lw_r - lw_k,
            "rel_delta": (lw_r - lw_k) / abs(lw_k) if lw_k else None,
        },
        "dual_drift": {
            "n_differing": int((ad > 0).sum()),
            "share_differing": float((ad > 0).mean()),
            "max_abs_delta": float(ad.max()),
            "share_of_differing_under_1cent": float((nz < 0.01).mean()) if nz.size else 0.0,
            "share_of_all_over_1dollar": float((ad > 1.0).mean()),
            "per_zone": per_zone,
        },
        "marginal_emission_rate": mer,
    }
    out.write_text(json.dumps(rec, indent=2, default=float))
    print(json.dumps(rec, indent=2, default=float))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("keeper", type=Path)
    ap.add_argument("replay", type=Path)
    ap.add_argument("year", type=int)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    main(a.keeper, a.replay, a.year, a.out)
