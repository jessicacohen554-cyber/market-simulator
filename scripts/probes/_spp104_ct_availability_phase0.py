"""SPP-104 (zero LP): how the keeper represents CT_PEAKER availability, against SPP's own published gas outage.

Record: ``docs/handoffs/DESIGN-spp-104-ct-outage-2026-09-29.md``.

Rebuilds the designated keeper ``results/calibration/spp100_arm_span`` ``fleet_only`` per year
(``scripts.lib.bundle_fleet.reconstruct_bundle_fleet``, no LP) and measures, per thermal class,
unavailable MW on TWO bases:

* **rated basis** -- ``pmax - pmax x availability``, ``pmax`` the LP row's rated MW. Counts every
  component the keeper carries: the flat statistical WEFOR + derate, the shoulder POF, the summer
  ambient derate and the CAMPD windows.
* **SPP-84 basis** -- ``max_t(pmax x availability) - pmax x availability``: only the TIME-VARYING
  part. This is the metric SPP-84 used (its "row's maximum available MW"), so it is reproduced
  here to show what that metric hides.

Leading / trailing all-zero runs >= 30 days are excluded as COD / retirement masks (SPP-84's rule).
Solves nothing. Usage: ``python scripts/probes/_spp104_ct_availability_phase0.py --cache <dir> --out <json>``
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
BUNDLE = REPO_ROOT / "results/calibration/spp100_arm_span"
YEARS = tuple(range(2019, 2026))
EDGE_H = 30 * 24


def rebuild(y: int, cache: Path, variant: str = "keeper") -> dict:
    """``fleet_only`` rebuild of the keeper's year ``y`` (cached): rows, rated pmax, availability.

    ``variant="arm"`` / ``"arm_outage"`` rebuild with ``spp_ct_lole_efor`` armed (SPP-104's
    field; zero-LP prediction of its availability footprint).

    ``variant="outage"`` is a DECOMPOSITION instrument, never a config: it zeroes the two
    non-outage capacity terms of the statistical stack (the flat GADS weather/performance
    ``derate`` and the flat summer ambient class derate) so the remaining unavailability is the
    outage-type part (WEFOR, shoulder POF, CAMPD windows) -- the part SPP's CROW outage report can
    contain. SPP's MMU (Unavailable Generation Capacity, Dec 2025, s3.3.1.2) states ambient
    derates are not reported to CROW.
    """
    p = cache / f"fleet_{y}{'' if variant == 'keeper' else '_' + variant}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    from market_sim.data.fleet import arrays as _arr

    orig_out, orig_sum = _arr._thermal_outage, dict(_arr._SUMMER_CLASS_DERATE)
    from market_sim.config.scenarios import ScenarioConfig

    orig_post = ScenarioConfig.__post_init__
    if variant.startswith("arm"):

        def _armed(self):
            orig_post(self)
            object.__setattr__(self, "spp_ct_lole_efor", True)

        ScenarioConfig.__post_init__ = _armed
    if variant in ("outage", "arm_outage"):
        _arr._thermal_outage = lambda c, a: (*orig_out(c, a)[:2], 0.0)
        _arr._SUMMER_CLASS_DERATE.clear()
    try:
        st, _ = reconstruct_bundle_fleet(BUNDLE, y, verbose=False)
    finally:
        ScenarioConfig.__post_init__ = orig_post
        _arr._thermal_outage = orig_out
        _arr._SUMMER_CLASS_DERATE.clear()
        _arr._SUMMER_CLASS_DERATE.update(orig_sum)
    fa = st["fleet_arrays"]
    keys = ("unit_id", "fuel_type", "plant_group", "zone", "plant_code", "online_year")
    out = {
        "rows": [{k: getattr(g, k, None) for k in keys} for g in st["fleet"]],
        "pmax": np.asarray(fa.pmax, dtype=np.float32),
        "availability": np.asarray(fa.availability, dtype=np.float32),
        "min_gen": np.asarray(getattr(fa, "min_gen", np.zeros(1)), dtype=np.float32),
    }
    p.write_bytes(pickle.dumps(out))
    return out


def edge_mask(a: np.ndarray) -> np.ndarray:
    """True on leading / trailing all-zero runs of >= 30 days (COD / retirement)."""
    m = np.zeros(a.size, bool)
    nz = np.flatnonzero(a > 0)
    if nz.size == 0:
        m[:] = True
        return m
    if nz[0] >= EDGE_H:
        m[: nz[0]] = True
    if a.size - 1 - nz[-1] >= EDGE_H:
        m[nz[-1] + 1 :] = True
    return m


def year_stats(y: int, cache: Path, variant: str = "keeper") -> dict:
    """Per-class rated and SPP-84-basis unavailable GW, plus CT monthly profile."""
    fl = rebuild(y, cache, variant)
    r = pd.DataFrame(fl["rows"])
    cls = r.plant_group.replace("", np.nan).fillna(r.fuel_type).to_numpy()
    pm = fl["pmax"].astype(float)
    av = pm[:, None] * fl["availability"].astype(float)
    mask = np.array([edge_mask(a) for a in av])
    live = ~mask
    rated_un = np.where(live, pm[:, None] - av, 0.0)
    pk = av.max(1)
    s84_un = np.where(live, pk[:, None] - av, 0.0)
    mon = (
        pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(av.shape[1]), unit="h")
    ).month
    out: dict = {"year": y, "variant": variant, "classes": {}}
    for c in sorted(set(cls)):
        sel = cls == c
        if r.fuel_type[sel].iloc[0] not in (
            "gas_cc",
            "gas_ct",
            "gas_st",
            "coal",
            "oil",
        ):
            continue
        live_mw = np.where(live[sel], pm[sel][:, None], 0.0).sum(0)
        out["classes"][c] = {
            "n_rows": int(sel.sum()),
            "pmax_gw": round(float(pm[sel].sum() / 1e3), 3),
            "live_pmax_gw_mean": round(float(live_mw.mean() / 1e3), 3),
            "rated_unavail_gw": round(float(rated_un[sel].sum(0).mean() / 1e3), 3),
            "spp84basis_unavail_gw": round(float(s84_un[sel].sum(0).mean() / 1e3), 3),
            "rated_unavail_frac": round(
                float(rated_un[sel].sum(0).mean() / max(live_mw.mean(), 1)), 4
            ),
        }
        if c == "CT_PEAKER":
            ct = rated_un[sel].sum(0)
            out["ct_rated_unavail_monthly_gw"] = [
                round(float(ct[mon == m].mean() / 1e3), 3) for m in range(1, 13)
            ]
            ages = y - pd.to_numeric(r.online_year[sel], errors="coerce")
            out["ct_mw_weighted_age"] = round(
                float(np.nansum(ages * pm[sel]) / pm[sel].sum()), 1
            )
            out["ct_rows_min_avail"] = round(
                float(np.nanmin(np.where(live[sel], fl["availability"][sel], np.nan))),
                4,
            )
    gas = np.isin(r.fuel_type, ("gas_cc", "gas_ct", "gas_st"))
    out["gas_rated_unavail_gw"] = round(float(rated_un[gas].sum(0).mean() / 1e3), 3)
    out["gas_spp84basis_unavail_gw"] = round(float(s84_un[gas].sum(0).mean() / 1e3), 3)
    out["gas_rated_unavail_hourly_gw"] = (rated_un[gas].sum(0) / 1e3).round(3).tolist()
    return out


def main() -> None:
    """Rebuild every keeper year and write the per-class availability census."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="*", default=list(YEARS))
    ap.add_argument(
        "--variant", choices=("keeper", "outage", "arm", "arm_outage"), default="keeper"
    )
    a = ap.parse_args()
    a.cache.mkdir(parents=True, exist_ok=True)
    res = [year_stats(y, a.cache, a.variant) for y in a.years]
    a.out.write_text(
        json.dumps(
            {
                "lane": "SPP-104",
                "bundle": str(BUNDLE.relative_to(REPO_ROOT)),
                "per_year": res,
            }
        )
    )


if __name__ == "__main__":
    main()
