"""capx D61 — PJM published reserve / regulation settlement scale from the in-repo DataMiner2 feeds (VALIDATION OBSERVABLES, rule 13).

Per (locale, service, year): the annual settlement POOL Σ(cleared MW × MCP × interval h) and the price a MW assigned in EVERY interval
would earn (Σ MCP × interval h, $/MW-yr). Interval lengths from the timestamps (2022 mixes hourly pre-May and 5-min post-May rows).
Run: python3 docs/handoffs/d61/as-pools-2026-09-05.py > docs/handoffs/d61/as-pools-2026-09-05.json
"""
import json, sys
import pandas as pd

OUT = {}
for y in (2022, 2023, 2024, 2025):
    df = pd.read_parquet(f"data/raw/PJM-AS/reserve_market_results_{y}.parquet")
    df["t"] = pd.to_datetime(df["datetime_beginning_utc"], format="mixed")
    OUT[f"rt_{y}"] = {}
    for (loc, svc), g in df.groupby(["locale", "service"]):
        g = g.sort_values("t")
        dt = (g["t"].diff().shift(-1).dt.total_seconds().fillna(300) / 3600.0).clip(upper=1.0)
        mw = g["as_mw"].fillna(g["total_mw"])
        OUT[f"rt_{y}"][f"{loc}/{svc}"] = {
            "covered_h": float(dt.sum()),
            "req_mean_mw": float(g["as_req_mw"].mean()),
            "cleared_mean_mw": float(mw.mean()),
            "pool_usd": float((mw * g["mcp"] * dt).sum()),
            "sum_mcp_usd_per_mw_yr": float((g["mcp"] * dt).sum()),
            "mcp_mean": float(g["mcp"].mean()),
        }
for y in (2023, 2024, 2025):
    df = pd.read_parquet(f"data/raw/PJM-AS/da_reserve_market_results_{y}.parquet")
    OUT[f"da_{y}"] = {}
    for (loc, svc), g in df.groupby(["locale", "service"]):
        h = 8760.0 / len(g)
        mw = g["as_mw"].fillna(g["total_mw"])
        OUT[f"da_{y}"][f"{loc}/{svc}"] = {
            "req_mean_mw": float(g["as_req_mw"].mean()),
            "cleared_mean_mw": float(mw.mean()),
            "pool_usd": float((mw * g["mcp"]).sum() * h),
            "sum_mcp_usd_per_mw_yr": float(g["mcp"].sum() * h),
            "mcp_mean": float(g["mcp"].mean()),
        }
json.dump(OUT, sys.stdout, indent=1)
