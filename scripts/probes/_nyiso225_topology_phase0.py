"""nyiso-225 phase 0 (ZERO LP): does the topology split have an object to hold?

Regenerates every number in ``docs/FINDING-nyiso225-topology-split-closed-2026-09-10.md``
from committed inputs only:

* ``data/raw/NYISO/interface-flows/`` — MIS P-32 hourly flows + posted limits
* ``data/raw/lmp-data/NYISO/`` — NYISO zonal RT LBMP with its congestion component
* the preserved nyiso-224 arm sidecars (``network_2022.parquet`` /
  ``system_2022.parquet``) on branch ``claude/nyiso224-cutset-2022``

Four measurements, each of which independently bears on the successor:

1. **binding census** — which posted internal interfaces are ever constraints, both
   directions, every year.  Only ``CENTRAL EAST - VC`` is.
2. **basis decomposition** — how much of each boundary's zonal basis is the published
   congestion component rather than losses.
3. **arm overlap** — do the armed link's binding hours coincide with the market's own
   Central-East binding hours?  They are anti-correlated.
4. **seam incidence** — where the model's external border links sit against their bounds.

Writes ``results/calibration/_nyiso225_topology_phase0.json``.  Runs no solve.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_nyiso225_topology_phase0.py \
        [--arm-dir <dir with hourly/*.parquet from the preserved arm bundle>]
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import io
import json
import zipfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
FLOW_DIR = REPO / "data" / "raw" / "NYISO" / "interface-flows"
LMP_DIR = REPO / "data" / "raw" / "lmp-data" / "NYISO"
OUT = REPO / "results" / "calibration" / "_nyiso225_topology_phase0.json"

YEARS = (2022, 2023, 2024, 2025)
INTERNAL = [
    "CENTRAL EAST - VC",
    "TOTAL EAST",
    "MOSES SOUTH",
    "DYSINGER EAST",
    "WEST CENTRAL",
    "UPNY CONED",
    "SPR/DUN-SOUTH",
]
# NYISO zonal LBMP posting name -> load-zone letter.
ZONE_OF = {
    "WEST": "A", "GENESE": "B", "CENTRL": "C", "NORTH": "D", "MHK VL": "E",
    "CAPITL": "F", "HUD VL": "G", "MILLWD": "H", "DUNWOD": "I",
    "N.Y.C.": "J", "LONGIL": "K",
}
# The MIS posting carries +/-9999 MW as an "unbounded" sentinel; a sentinel is not a limit.
SENTINEL_MW = 9000.0
BIND_FRAC = 0.95  # an interface is "binding" at >=95% of its own posted limit


def _hour_key(local_ts: str) -> tuple[int, int, int, int] | None:
    """``YYYY-MM-DD HH:...`` -> (year, month, day, hour); None if unparseable."""
    try:
        return (int(local_ts[:4]), int(local_ts[5:7]), int(local_ts[8:10]), int(local_ts[11:13]))
    except (ValueError, IndexError):
        return None


def _lmp_hour_key(stamp: str) -> tuple[int, int, int, int]:
    """``MM/DD/YYYY HH:MM:SS`` -> (year, month, day, hour)."""
    date, time = stamp.split(" ")
    month, day, year = date.split("/")
    return (int(year), int(month), int(day), int(time[:2]))


def load_flows(year: int) -> tuple[dict, dict, dict]:
    """Return (flow, positive_limit, negative_limit), each interface -> {hour_key: MW}."""
    flow: dict = collections.defaultdict(dict)
    pos: dict = collections.defaultdict(dict)
    neg: dict = collections.defaultdict(dict)
    with gzip.open(FLOW_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz", "rt") as handle:
        for row in csv.DictReader(handle):
            key = _hour_key(row["interval_start_local"])
            if key is None:
                continue
            for target, column in ((flow, "flow_mw"), (pos, "positive_limit_mw"), (neg, "negative_limit_mw")):
                try:
                    target[row["interface"]][key] = float(row[column])
                except (TypeError, ValueError):
                    pass
    return flow, pos, neg


def load_zonal_prices(year: int) -> tuple[dict, dict, list]:
    """Return (lbmp, congestion_component) as zone letter -> hourly array, plus hour keys."""
    lbmp: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    mcc: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for month in range(1, 13):
        path = LMP_DIR / f"{year}{month:02d}01realtime_zone_csv.zip"
        if not path.exists():
            continue
        archive = zipfile.ZipFile(path)
        for name in archive.namelist():
            if not name.endswith(".csv"):
                continue
            text = archive.read(name).decode("utf-8", "replace")
            for row in csv.DictReader(io.StringIO(text)):
                zone = ZONE_OF.get(row["Name"].strip())
                if zone is None:
                    continue
                key = _lmp_hour_key(row["Time Stamp"])
                try:
                    lbmp[zone][key].append(float(row["LBMP ($/MWHr)"]))
                    mcc[zone][key].append(float(row["Marginal Cost Congestion ($/MWHr)"]))
                except (TypeError, ValueError):
                    pass
    keys = sorted(set.intersection(*[set(lbmp[z]) for z in ZONE_OF.values()]))
    price = {z: np.array([np.mean(lbmp[z][k]) for k in keys]) for z in ZONE_OF.values()}
    cong = {z: np.array([np.mean(mcc[z][k]) for k in keys]) for z in ZONE_OF.values()}
    return price, cong, keys


def binding_census() -> dict:
    """§1 — which posted internal interfaces are ever constraints, both directions."""
    out: dict = {}
    for year in YEARS:
        flow, pos, neg = load_flows(year)
        for name in INTERNAL:
            keys = sorted(set(flow[name]) & set(pos[name]))
            if not keys:
                continue
            f = np.array([flow[name][k] for k in keys])
            p = np.array([pos[name][k] for k in keys])
            n = np.array([neg[name].get(k, np.nan) for k in keys])
            live_p = p < SENTINEL_MW
            live_n = np.abs(n) < SENTINEL_MW
            out.setdefault(name, {})[str(year)] = {
                "hours": int(len(keys)),
                "pos_limit_posted_pct": round(float(live_p.mean() * 100), 2),
                "pos_bind_pct": (
                    round(float(np.mean(f[live_p] >= BIND_FRAC * p[live_p]) * 100), 4)
                    if live_p.any() else None
                ),
                "neg_bind_pct": (
                    round(float(np.mean(f[live_n] <= BIND_FRAC * n[live_n]) * 100), 4)
                    if live_n.any() else None
                ),
                "flow_mean_mw": round(float(f.mean()), 1),
                "pos_limit_mean_mw": round(float(p[live_p].mean()), 1) if live_p.any() else None,
            }
    return out


def parallel_leg() -> dict:
    """§2(b) — the non-Central-East leg of Total East: is it Moses South?"""
    out: dict = {}
    for year in YEARS:
        flow, _pos, _neg = load_flows(year)
        keys = sorted(set(flow["TOTAL EAST"]) & set(flow["CENTRAL EAST - VC"]) & set(flow["MOSES SOUTH"]))
        te = np.array([flow["TOTAL EAST"][k] for k in keys])
        ce = np.array([flow["CENTRAL EAST - VC"][k] for k in keys])
        ms = np.array([flow["MOSES SOUTH"][k] for k in keys])
        residual = te - ce
        out[str(year)] = {
            "total_east_mean_mw": round(float(te.mean()), 1),
            "central_east_mean_mw": round(float(ce.mean()), 1),
            "moses_south_mean_mw": round(float(ms.mean()), 1),
            "non_ce_leg_mean_mw": round(float(residual.mean()), 1),
            "corr_non_ce_leg_moses_south": round(float(np.corrcoef(residual, ms)[0, 1]), 4),
        }
    return out


def basis_decomposition(year: int = 2022) -> dict:
    """§2(c) — how much of each boundary's basis is congestion rather than losses.

    NYISO posts the congestion component with the opposite sign convention to the
    basis (a constrained-in zone carries a negative MCC), so the reported share is
    the magnitude ratio; its sign is the convention, not a result.
    """
    price, cong, _keys = load_zonal_prices(year)
    pairs = [
        ("E", "F", "CENTRAL EAST E->F"), ("C", "F", "C->F"),
        ("D", "E", "MOSES SOUTH D->E"), ("A", "C", "WEST CENTRAL A->C"),
        ("A", "B", "DYSINGER EAST A->B"), ("F", "G", "F|G (UPNY-SENY)"),
        ("G", "J", "G->J"), ("J", "K", "LI import J->K"),
    ]
    out = {"year": year, "boundaries": {}}
    for lo, hi, label in pairs:
        d_lbmp = float(np.mean(price[hi] - price[lo]))
        d_mcc = float(np.mean(cong[hi] - cong[lo]))
        out["boundaries"][label] = {
            "d_lbmp": round(d_lbmp, 2),
            "d_congestion_component": round(d_mcc, 2),
            "congestion_share_pct": round(abs(d_mcc) / abs(d_lbmp) * 100, 1) if abs(d_lbmp) > 1e-9 else None,
        }
    upstate = "ABCDE"
    tot = np.vstack([price[z] for z in upstate])
    con = np.vstack([cong[z] for z in upstate])
    out["within_upstate_west"] = {
        "total_spread_mean": round(float(np.mean(tot.max(0) - tot.min(0))), 2),
        "congestion_spread_mean": round(float(np.mean(con.max(0) - con.min(0))), 2),
    }
    out["zone_mean_lbmp"] = {z: round(float(price[z].mean()), 2) for z in "ABCDEFGHIJK"}
    return out


def arm_overlap(arm_dir: Path, year: int = 2022) -> dict:
    """§3 — do the armed link's binding hours coincide with the market's own?"""
    import pandas as pd

    net = pd.read_parquet(arm_dir / f"network_{year}.parquet")
    sysd = pd.read_parquet(arm_dir / f"system_{year}.parquet")
    net = net[(net["pass"] == "P1") & (net["kind"] == "link")]
    sysd = sysd[sysd["pass"] == "P1"]
    link = net[net["name"] == "Upstate_West>Capital_Hudson"].sort_values("hour")
    armed = link["dual"].to_numpy() != 0

    flow, pos, _neg = load_flows(year)
    keys = sorted(set(flow["CENTRAL EAST - VC"]) & set(pos["CENTRAL EAST - VC"]))
    ce = np.array([flow["CENTRAL EAST - VC"][k] for k in keys])
    cl = np.array([pos["CENTRAL EAST - VC"][k] for k in keys])
    market = ce >= BIND_FRAC * cl

    n = min(len(armed), len(market))
    a, m = armed[:n], market[:n]
    both = int((a & m).sum())
    expected = float(a.mean() * m.mean() * n)

    price, _cong, pkeys = load_zonal_prices(year)
    zonal = sysd.pivot_table(index="hour", columns="zone", values="price")
    up = zonal["Upstate_West"].to_numpy()
    ch = zonal["Capital_Hudson"].to_numpy()
    mk = min(len(price["A"]), n)
    meas_up = np.mean([price[z][:mk] for z in "ABCDE"], axis=0)
    meas_ch = np.mean([price[z][:mk] for z in "FG"], axis=0)

    return {
        "year": year,
        "arm_bind_hours": int(a.sum()),
        "arm_bind_pct": round(float(a.mean() * 100), 2),
        "market_ce_bind_hours": int(m.sum()),
        "market_ce_bind_pct": round(float(m.mean() * 100), 2),
        "overlap_hours": both,
        "expected_if_independent": round(expected, 1),
        "lift": round(both / expected, 3) if expected else None,
        "precision_pct": round(both / max(int(a.sum()), 1) * 100, 1),
        "recall_pct": round(both / max(int(m.sum()), 1) * 100, 1),
        "arm_mean_abs_dual_when_binding": round(float(np.abs(link["dual"].to_numpy()[armed]).mean()), 2),
        "arm_mean_loading_pct": round(float(link["mw"].mean() / link["limit_up"].mean() * 100), 1),
        "arm_spread_when_binding": round(float(np.mean((ch - up)[:n][a])), 2),
        "measured_spread_when_ce_binds": round(float(np.mean((meas_ch - meas_up)[m[:mk]])), 2),
    }


def seam_incidence(arm_dir: Path, year: int = 2022) -> dict:
    """§4 — where the model's external border links sit against their bounds."""
    import pandas as pd

    net = pd.read_parquet(arm_dir / f"network_{year}.parquet")
    net = net[(net["pass"] == "P1") & (net["kind"] == "link")]
    links = {}
    for name, grp in net.groupby("name", observed=True):
        if not str(name).startswith("NYISO_external>"):
            continue
        links[str(name)] = {
            "mean_mw": round(float(grp["mw"].mean()), 1),
            "limit_up_mean_mw": round(float(grp["limit_up"].mean()), 1),
            "at_upper_bound_pct": round(float((grp["mw"] >= 0.999 * grp["limit_up"]).mean() * 100), 1),
        }
    flow, _pos, _neg = load_flows(year)
    ext = {c: flow[c] for c in flow if c.startswith("SCH - ")}
    keys = sorted(set.intersection(*[set(v) for v in ext.values()]))
    measured = {c: round(float(np.mean([ext[c][k] for k in keys])), 1) for c in sorted(ext)}
    east = ["SCH - NE - NY", "SCH - NPX_1385", "SCH - NPX_CSC", "SCH - PJ - NY",
            "SCH - PJM_HTP", "SCH - PJM_NEPTUNE", "SCH - PJM_VFT"]
    return {
        "year": year,
        "model_links": links,
        "measured_schedules_mean_mw": measured,
        "measured_east_of_cutset_net_mw": round(sum(measured[c] for c in east), 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--arm-dir", type=Path, default=None,
        help="directory holding the preserved arm bundle's network_/system_<year>.parquet",
    )
    args = parser.parse_args()

    record: dict = {
        "session": "nyiso-225",
        "iso": "NYISO",
        "date": "2026-09-10",
        "solves": 0,
        "bind_threshold_frac": BIND_FRAC,
        "binding_census": binding_census(),
        "parallel_leg": parallel_leg(),
        "basis_decomposition_2022": basis_decomposition(2022),
    }
    if args.arm_dir is not None:
        record["arm_overlap_2022"] = arm_overlap(args.arm_dir)
        record["seam_incidence_2022"] = seam_incidence(args.arm_dir)
    else:
        record["arm_overlap_2022"] = "SKIPPED — pass --arm-dir with the preserved nyiso-224 sidecars"
        record["seam_incidence_2022"] = "SKIPPED — pass --arm-dir with the preserved nyiso-224 sidecars"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {OUT}")
    for name, per_year in record["binding_census"].items():
        cells = "  ".join(
            f"{y}:{(per_year[y]['pos_bind_pct'] if per_year[y]['pos_bind_pct'] is not None else float('nan')):6.2f}%"
            for y in map(str, YEARS) if y in per_year
        )
        print(f"  {name:22s} {cells}")


if __name__ == "__main__":
    main()
