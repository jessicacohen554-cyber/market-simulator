"""NYISO-NEXT-10 phase 0 (ZERO LP): does each seam's flow follow its OWN spread?

Implements ``docs/records/nyiso/PRECOMMIT-nyiso-next10-seam-spread-phase0-2026-09-28.md``
(committed before any statistic here was computed).  For every NYISO seam group
it aligns, on ``interval_start_utc``:

* the measured hourly net import (NYISO P-32 ``SCH -`` rows, + = into NY);
* the NY DA LBMP at the landing zone and at the NY proxy bus;
* the neighbour's own price at its interface node (PJM / ISO-NE DA LMP, IESO
  HOEP in USD at the Bank of Canada daily rate);
* the NY DA system-mean price (NEXT-7's comparator).

and reports Spearman rho of flow vs spread (landing and proxy) and vs the NY
price, then applies the PRECOMMIT's S1-S3 rule.  Reads raw inputs only.

Output: ``results/phase0/nyiso/_nyisonext10_phase0.json``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

YEARS = (2021, 2022, 2023, 2024, 2025)
RAW = REPO / "data" / "raw"
SNP = RAW / "seam-neighbour-price"
FLOW_DIR = RAW / "NYISO" / "interface-flows"
OUT = REPO / "results" / "phase0" / "nyiso" / "_nyisonext10_phase0.json"

#: PRECOMMIT §2 table: group -> (SCH rows, NY landing zone, NY proxy, neighbour key)
GROUPS: dict[str, tuple[tuple[str, ...], str | None, str, str]] = {
    "IESO": (("SCH - OH - NY",), "WEST", "O H", "IESO:HOEP"),
    "PJM_AC": (("SCH - PJ - NY",), None, "PJM", "PJM:NYIS"),
    "PJM_HTP": (("SCH - PJM_HTP",), "N.Y.C.", "PJM_GEN_HTP_PROXY", "PJM:HUDSONTP"),
    "PJM_VFT": (("SCH - PJM_VFT",), "N.Y.C.", "PJM_GEN_VFT_PROXY", "PJM:LINDENVFT"),
    "PJM_NEPTUNE": (
        ("SCH - PJM_NEPTUNE",),
        "LONGIL",
        "PJM_GEN_NEPTUNE_PROXY",
        "PJM:NEPTUNE",
    ),
    "NE_AC": (("SCH - NE - NY",), "CAPITL", "NPX", "NEISO:4011"),
    "NE_CSC": (("SCH - NPX_CSC",), "LONGIL", "NPX_GEN_CSC", "NEISO:4014"),
    "NE_1385": (("SCH - NPX_1385",), "LONGIL", "NPX_GEN_1385_PROXY", "NEISO:4017"),
}
NY_ZONES = (
    "CAPITL", "CENTRL", "DUNWOD", "GENESE", "HUD VL", "LONGIL",
    "MHK VL", "MILLWD", "N.Y.C.", "NORTH", "WEST",
)  # fmt: skip
S3_FLOOR = 0.30  # PRECOMMIT §4 decision threshold (not a model parameter)


def _spearman(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    m = a.notna() & b.notna()
    if m.sum() < 100:
        return float("nan"), int(m.sum())
    return float(a[m].rank().corr(b[m].rank())), int(m.sum())


def flows(year: int) -> pd.DataFrame:
    """Hourly SCH flows, wide by interface, indexed by UTC hour start."""
    df = pd.read_csv(FLOW_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz")
    df = df[df["interface"].astype(str).str.startswith("SCH -")]
    df["t"] = pd.to_datetime(df["interval_start_utc"], utc=True)
    return df.pivot_table(index="t", columns="interface", values="flow_mw")


def ny_prices(year: int) -> pd.DataFrame:
    """NYISO DA LBMP, wide by name, indexed by UTC hour start (DST via seq)."""
    with gzip.open(SNP / "nyiso" / f"NYISO_dam_proxy_lbmp_{year}.csv.gz", "rt") as f:
        d = pd.read_csv(f)
    local = pd.to_datetime(d["time_stamp"], format="%m/%d/%Y %H:%M")
    # Fall-back hour appears twice: seq order within the day is publication
    # order, so the first 01:00 is EDT, the second EST.
    d = d.assign(local=local).sort_values(["name", "date", "seq"])
    parts = []
    for _, g in d.groupby("name", sort=False):
        t = g["local"].dt.tz_localize("America/New_York", ambiguous="infer")
        parts.append(g.assign(t=t.dt.tz_convert("UTC")))
    d = pd.concat(parts)
    return d.pivot_table(index="t", columns="name", values="lbmp")


def neighbour_prices(year: int) -> pd.DataFrame:
    """Neighbour DA (PJM, ISO-NE) and HOEP-USD (IESO), wide, indexed by UTC."""
    out = {}
    p = pd.read_csv(SNP / "pjm" / f"PJM_ny_interface_lmp_{year}.csv")
    p = p[p["market"] == "DA"]
    p["t"] = pd.to_datetime(p["datetime_beginning_utc"]).dt.tz_localize("UTC")
    for name, g in p.groupby("pnode_name"):
        out[f"PJM:{name}"] = g.set_index("t")["total_lmp"]
    n = pd.read_csv(SNP / "neiso" / f"NEISO_ny_ext_node_lmp_{year}.csv")
    n = n.sort_values(["location_id", "date", "seq"])
    midnight = pd.to_datetime(n["date"]).dt.tz_localize("America/New_York")
    n["t"] = midnight.dt.tz_convert("UTC") + pd.to_timedelta(n["seq"], unit="h")
    for loc, g in n.groupby("location_id"):
        out[f"NEISO:{loc}"] = g.set_index("t")["da_lmp"]
    i = pd.read_csv(SNP / "ieso" / f"IESO_hourly_price_{year}.csv")
    fx = pd.read_csv(SNP / "ieso" / "BOC_FXUSDCAD.csv", parse_dates=["date"])
    fx = fx.set_index("date")["usd_cad"].asfreq("D").ffill()
    # IESO hours are EST all year: HE h starts at (h-1):00 EST = UTC-5.
    t = (
        pd.to_datetime(i["date"])
        + pd.to_timedelta(i["hour_ending_est"] - 1, unit="h")
        + pd.Timedelta(hours=5)
    ).dt.tz_localize("UTC")
    rate = fx.reindex(pd.to_datetime(i["date"])).to_numpy()
    out["IESO:HOEP"] = pd.Series(i["hoep_cad"].to_numpy() / rate, index=t)
    return pd.DataFrame(out)


def year_block(year: int) -> dict:
    """Per-group rho(flow, spread) and rho(flow, NY price) for one year."""
    fl, ny, nb = flows(year), ny_prices(year), neighbour_prices(year)
    ny_sys = ny[list(NY_ZONES)].mean(axis=1)
    res = {}
    for gname, (rows, landing, proxy, nkey) in GROUPS.items():
        present = [r for r in rows if r in fl.columns]
        if not present:
            res[gname] = {"error": "flow rows missing"}
            continue
        f = fl[present].sum(axis=1, min_count=len(present))
        idx = f.index
        pn = nb[nkey].reindex(idx)
        blk = {
            "hours_flow": int(f.notna().sum()),
            "hours_neighbour": int(pn.notna().sum()),
            "mean_flow_mw": round(float(f.mean()), 1),
            "twh": round(float(f.sum()) / 1e6, 3),
        }
        r_ny, n_ny = _spearman(f, ny_sys.reindex(idx).where(pn.notna()))
        blk["rho_ny_price"] = round(r_ny, 3)
        r_px, n_px = _spearman(f, ny[proxy].reindex(idx) - pn)
        blk["rho_spread_proxy"], blk["n"] = round(r_px, 3), n_px
        if landing is not None:
            r_ld, _ = _spearman(f, ny[landing].reindex(idx) - pn)
            blk["rho_spread_landing"] = round(r_ld, 3)
        blk["mean_spread_proxy"] = round(float((ny[proxy].reindex(idx) - pn).mean()), 2)
        res[gname] = blk
    return res


def verdict(per_year: dict) -> dict:
    """Apply PRECOMMIT §4 S1-S3 per group (landing spread; proxy where no landing)."""
    out = {}
    for g in GROUPS:
        key = "rho_spread_landing" if GROUPS[g][1] is not None else "rho_spread_proxy"
        rs = [per_year[y][g].get(key) for y in YEARS]
        rn = [per_year[y][g].get("rho_ny_price") for y in YEARS]
        pairs = [(a, b) for a, b in zip(rs, rn) if a is not None and not np.isnan(a)]
        s1 = all(a > 0 for a, _ in pairs)
        s2 = sum(a > b for a, b in pairs) >= len(pairs) - 1
        med = float(np.median([a for a, _ in pairs]))
        s3 = med >= S3_FLOOR
        out[g] = {
            "statistic": key,
            "S1": s1,
            "S2": s2,
            "S3_median": round(med, 3),
            "S3": s3,
            "identified": s1 and s2 and s3,
        }
    return out


def main() -> None:
    """Run all years, print the table, write the JSON record."""
    per_year = {y: year_block(y) for y in YEARS}
    v = verdict(per_year)
    rec = {"per_year": {str(k): v_ for k, v_ in per_year.items()}, "verdict": v}
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    for g in GROUPS:
        row = [g]
        for y in YEARS:
            b = per_year[y][g]
            row.append(
                f"{b.get('rho_ny_price')}/{b.get('rho_spread_landing', '-')}/"
                f"{b.get('rho_spread_proxy')}"
            )
        print(" | ".join(map(str, row)), "|", v[g])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
