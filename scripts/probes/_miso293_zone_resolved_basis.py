#!/usr/bin/env python3
"""miso-293 Stage 1 (ZERO LP): MISO C3a/C3b on the ZONE-RESOLVED load-weighted actual.

Rubric v2.4 defines the C3a/C3b actual as "the committed hourly actual weighted by
the same measured demand the model dispatches, **zone-resolved where a zonal archive
exists**". ``derive_actual_lmp._lw_fields`` implements the zone-resolved branch for
ERCOT only; every other ISO is scored on ONE system hub (MISO: INDIANA.HUB) weighted
by system demand, even though MISO has a committed zonal archive
(``actual_lmp_hourly_zonal_MISO.parquet``, one or more trading hubs per model zone).

This probe builds the zone-resolved fields exactly as the ERCOT branch does (per
model zone: its hub series, multi-hub zones averaged, weighted by that zone's
measured demand; then zone-demand-weighted across zones), patches them into the
keeper's bench IN MEMORY, and re-scores through ``calibration_verdict``. Nothing is
written to the bench or the reference. Rule 13: the actual is a benchmark, never an
input.

MISO-Plains has no hub; the staging's own declared proxy (MINN+ILLINOIS mean,
``zones_src``) is used, and the result is also reported with Plains dropped.

Usage::

    uv run python scripts/probes/_miso293_zone_resolved_basis.py --out results/calibration/_miso293_zone_resolved_basis.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import calibration_verdict as cv  # noqa: E402
from scripts.data import derive_actual_lmp as dal  # noqa: E402

RUN = "2026-09-28-miso-280-splitremap"
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
YEARS = tuple(range(2019, 2026))
PLAINS_PROXY = ("MINN.HUB", "ILLINOIS.HUB")


def zone_lw(year: int, drop_plains: bool) -> dict:
    """Zone-resolved ``{rt,da}_lw`` + ``_lw_mon`` for one MISO year (ERCOT construction)."""
    from market_sim.config.iso_configs import get_iso_config

    demand = dal._measured_zone_demand("MISO", year)
    z = pd.read_parquet(ZONAL)
    z = z[z["year"] == year]
    hubs: dict[str, dict[str, np.ndarray]] = {}
    zone_hubs: dict[str, set] = {}
    for (hub, zone), g in z.groupby(["hub", "zone"]):
        zone_hubs.setdefault(zone, set()).add(hub)
        g = g.sort_values("hour")
        for kind in ("rt", "da"):
            dense = np.full(dal._HOURS_PER_YEAR, np.nan)
            hr = g["hour"].to_numpy(int)
            ok = hr < dal._HOURS_PER_YEAR
            dense[hr[ok]] = g[kind].to_numpy(float)[ok]
            hubs.setdefault(hub, {})[kind] = dense
    if not drop_plains:
        zone_hubs["MISO-Plains"] = set(PLAINS_PROXY)
    names = [zn.name for zn in get_iso_config("MISO").zones]
    out: dict = {}
    for kind in ("rt", "da"):
        pairs = []
        for zi, zone in enumerate(names):
            hs = sorted(zone_hubs.get(zone, ()))
            w = demand[zi]
            if not hs or float(w.sum()) <= 0.0:
                continue
            p = np.nanmean(np.vstack([hubs[h][kind] for h in hs]), axis=0)
            annual, mon = dal._lw_stats(p, w)
            if np.isnan(annual):
                continue
            pairs.append((annual, mon, float(w.sum())))
        ws = sum(w for _, _, w in pairs)
        out[f"{kind}_lw"] = round(sum(a * w for a, _, w in pairs) / ws, 2)
        out[f"{kind}_lw_mon"] = [
            round(
                sum(m[i] * w for _, m, w in pairs if m[i] is not None)
                / sum(w for _, m, w in pairs if m[i] is not None),
                2,
            )
            if any(m[i] is not None for _, m, _ in pairs)
            else None
            for i in range(12)
        ]
    return out


def price_rows(verdict: dict) -> dict:
    """``{criterion-year: (status, magnitude)}`` for C3a/C3b."""
    rows = {}
    for crit in ("price_mean", "price_shape"):
        for r in verdict["criteria"][crit]["records"]:
            if r.get("key") is None:
                rows[f"{crit} {r['year']}"] = (
                    r["status"],
                    r.get("magnitude"),
                    r.get("model"),
                    r.get("actual"),
                )
    return rows


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    art = cv.load_artifacts(RUN)
    base = cv.determine_from_artifacts(RUN, art)
    res = {
        "base": {
            "determination": base.get("determination"),
            "reasons": base.get("reasons"),
            "rows": price_rows(base),
        }
    }
    for label, drop in (("zone_resolved", False), ("zone_resolved_no_plains", True)):
        art2 = copy.deepcopy(art)
        fields = {}
        for y in YEARS:
            f = zone_lw(y, drop)
            fields[str(y)] = {k: f[k] for k in ("rt_lw", "da_lw")}
            art2["bench"][y]["avgLMP"].update(f)
        v = cv.determine_from_artifacts(RUN, art2)
        res[label] = {
            "fields": fields,
            "determination": v.get("determination"),
            "reasons": v.get("reasons"),
            "rows": price_rows(v),
        }
    a.out.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
