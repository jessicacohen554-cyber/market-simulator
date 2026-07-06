"""Honesty gate for the MISO commitment-posture lever (design note §A).

Scores a ``miso_commitment_posture`` bundle against the MEASURED MISO ASM
series staged in ``data/raw/MISO-AS`` (fetched by ``fetch_miso_asm.py``):
regional RT cleared reserve MW (from the masked cleared-offers reports) and
zonal reserve MCPs. Per the design note the acceptance question is whether the
modeled ONLINE HEADROOM / cleared-reserve behaviour tracks the measured series
in LEVEL and EVENT-DAY DIRECTION — the >$200 price-tail count is NEVER the
gate (CLAUDE.md rules 1/13).

Checks reported per year:

* **G-P1 level** — modeled postured online headroom (Σ pools U − P, the
  capacity the LP holds online beyond dispatch) vs the measured total cleared
  reserve (reg + spin + supp + STR): annual means and their ratio. The two
  are different boundaries (model headroom includes non-cleared margin;
  measured cleared excludes fast-start offline supplemental headroom), so the
  gate is a band, not equality.
* **G-P2 event-day direction** — Pearson r between the DAILY series: modeled
  system reserve price (P1 balance dual) vs the measured Miso-Wide RT spin
  MCP, and modeled online headroom vs measured cleared MW. On the top-20
  measured spin-MCP days, the share where the model moves the same direction
  (headroom down / reserve price up vs its own median).
* **G-P3 regional split** — model zonal → MISO reserve-region crosswalk
  (South → South; Illinois/Indiana/East → Central; West/Plains → North —
  a rule-14 boundary reconciliation, documented here) share of online
  headroom vs the measured cleared-MW regional shares.

All hours Hour-Ending EST on both sides (MISO market reports never observe
DST; the model's MISO horizon is the EIA-930 hourly extract's fixed-offset
clock). Daily aggregation makes any residual one-hour convention slack
immaterial.

Usage:
    python scripts/report_miso_posture_gate.py \
        --bundle results/calibration/MISO/miso_43_commitment_posture \
        --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

ASM_DIR = RAW_DIR / "MISO-AS"

# Model zone -> MISO reserve region (rule-14 reconciliation: the model's
# 7-zone topology does not match MISO's 8 reserve zones; N/C/S is the
# coarsest published grouping both sides can be mapped onto).
ZONE_TO_REGION: dict[str, str] = {
    "MISO-South": "South",
    "MISO-Illinois": "Central",
    "MISO-Indiana": "Central",
    "MISO-East": "Central",
    "MISO-West": "North",
    "MISO-Plains": "North",
}


def _measured_cleared(year: int) -> pd.DataFrame:
    """Hourly measured cleared reserve MW by region (reg+spin+supp+str)."""
    df = pd.read_parquet(ASM_DIR / f"asm_rt_cleared_mw_{year}.parquet")
    piv = (
        df.groupby(["date", "hour_end_est", "region"])["cleared_mw"]
        .sum()
        .unstack("region")
        .fillna(0.0)
    )
    piv["total"] = piv.sum(axis=1)
    return piv.reset_index()


def _measured_spin_mcp(year: int) -> pd.Series:
    """Daily mean Miso-Wide RT spin MCP ($/MWh)."""
    df = pd.read_parquet(ASM_DIR / f"asm_rtmcp_zonal_{year}.parquet")
    wide = df[(df["zone"].str.lower() == "miso-wide") & (df["product"] == "GENSPINMCP")]
    he_cols = [c for c in wide.columns if c.startswith("he")]
    return wide.set_index("date")[he_cols].mean(axis=1)


def _model_frames(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (posture rows, system rows) for one year, P1 pass."""
    post = pd.read_parquet(bundle / "posture.parquet")
    post = post[(post["year"] == year) & (post["pass"] == "P1")]
    sys_df = pd.read_parquet(bundle / "system.parquet")
    sys_df = sys_df[(sys_df["year"] == year) & (sys_df["pass"] == "P1")]
    return post, sys_df


def _dispatch_by_pool(bundle: Path, year: int) -> pd.DataFrame | None:
    """Hourly postured-pool dispatch P (zone×fuel), from the dispatch frame."""
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["zone", "fuel", "hour", "mw"])
    return df.rename(columns={"mw": "dispatch_mw"})


def gate_year(bundle: Path, year: int) -> dict:
    """Compute the gate metrics for one year; returns a summary dict."""
    post, sys_df = _model_frames(bundle, year)
    q_pools = post[["zone", "fuel"]].drop_duplicates().shape[0]
    hours = post["hour"].max() + 1

    # Modeled online headroom per hour: Σ postured pools (U − pool dispatch).
    # posture.parquet carries U and pool R; pool dispatch P is recovered from
    # U − headroom identity via the dispatch frame when present, else the
    # conservative bound headroom ≥ R (joint row: P + R ≤ U).
    u_by_hour = post.groupby("hour")["online_mw"].sum()
    r_by_hour = post.groupby("hour")["reserve_mw"].sum()
    disp = _dispatch_by_pool(bundle, year)
    if disp is not None:
        keys = set(map(tuple, post[["zone", "fuel"]].drop_duplicates().values))
        disp["key"] = list(zip(disp["zone"], disp["fuel"]))
        p_by_hour = disp[disp["key"].isin(keys)].groupby("hour")["dispatch_mw"].sum()
        headroom = (u_by_hour - p_by_hour).clip(lower=0.0)
    else:
        headroom = r_by_hour.copy()

    # Measured cleared reserve.
    meas = _measured_cleared(year)
    n = min(len(meas), len(headroom))
    meas = meas.iloc[:n]
    headroom_v = headroom.to_numpy()[:n]

    # Daily aggregation.
    day = np.arange(n) // 24
    meas_total_d = pd.Series(meas["total"].to_numpy()).groupby(day[: len(meas)]).mean()
    headroom_d = pd.Series(headroom_v).groupby(day).mean()
    spin_d = _measured_spin_mcp(year)
    # Model reserve price: system frame is per zone-hour; reserve_price is
    # replicated across zones — take one zone's series.
    z0 = sys_df["zone"].iloc[0]
    rp = (
        sys_df[sys_df["zone"] == z0].sort_values("hour")["reserve_price"].to_numpy()[:n]
    )
    rp_d = pd.Series(rp).groupby(day).mean()

    k = min(len(meas_total_d), len(headroom_d), len(spin_d), len(rp_d))
    meas_total_d, headroom_d = meas_total_d.iloc[:k], headroom_d.iloc[:k]
    spin_v, rp_d = spin_d.iloc[:k].to_numpy(), rp_d.iloc[:k]

    r_price = float(np.corrcoef(rp_d, spin_v)[0, 1]) if rp_d.std() > 0 else float("nan")
    r_headroom = float(np.corrcoef(headroom_d, meas_total_d)[0, 1])

    # Event-day direction: top-20 measured spin-MCP days.
    top = np.argsort(spin_v)[-20:]
    hd_med, rp_med = float(np.median(headroom_d)), float(np.median(rp_d))
    same_dir = int(
        np.sum((headroom_d.to_numpy()[top] < hd_med) | (rp_d.to_numpy()[top] > rp_med))
    )

    # Regional split.
    post["region"] = post["zone"].map(ZONE_TO_REGION)
    model_share = (
        post.groupby("region")["online_mw"].sum()
        / max(float(post["online_mw"].sum()), 1e-9)
    ).to_dict()
    meas_share = {
        reg: float(meas[reg].sum()) / max(float(meas["total"].sum()), 1e-9)
        for reg in ("North", "Central", "South")
        if reg in meas.columns
    }

    return {
        "year": year,
        "pools": int(q_pools),
        "hours": int(hours),
        "model_headroom_mean_mw": float(np.mean(headroom_v)),
        "model_pool_reserve_mean_mw": float(r_by_hour.mean()),
        "measured_cleared_mean_mw": float(meas["total"].mean()),
        "level_ratio": float(np.mean(headroom_v) / max(meas["total"].mean(), 1e-9)),
        "daily_r_price_vs_spinmcp": r_price,
        "daily_r_headroom_vs_cleared": r_headroom,
        "event_top20_same_direction": same_dir,
        "model_region_share": {k2: round(v, 3) for k2, v in model_share.items()},
        "measured_region_share": {k2: round(v, 3) for k2, v in meas_share.items()},
        "model_startups_gw": float(post["startup_mw"].sum() / 1e3),
    }


def main() -> None:
    """CLI entrypoint: score the bundle and write SUMMARY-posture-gate.md."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    bundle = Path(args.bundle)

    rows = [gate_year(bundle, y) for y in args.years]
    lines = [
        "# MISO commitment-posture honesty gate (design note §A)",
        "",
        "Modeled online headroom / cleared-reserve behaviour vs the measured",
        "MISO ASM series (`data/raw/MISO-AS`). Level + event-day direction;",
        "the >$200 tail count is NEVER the gate (rules 1/13).",
        "",
    ]
    for r in rows:
        lines += [
            f"## {r['year']}",
            "",
            f"- postured pools: {r['pools']}, startups {r['model_startups_gw']:.1f} GW/yr",
            f"- G-P1 level: model online headroom mean {r['model_headroom_mean_mw']:.0f} MW"
            f" (pool cleared R mean {r['model_pool_reserve_mean_mw']:.0f} MW) vs measured"
            f" cleared {r['measured_cleared_mean_mw']:.0f} MW — ratio {r['level_ratio']:.2f}",
            f"- G-P2 direction: daily r(model reserve price, measured spin MCP) ="
            f" {r['daily_r_price_vs_spinmcp']:.2f}; daily r(headroom, cleared) ="
            f" {r['daily_r_headroom_vs_cleared']:.2f}; top-20 measured event days"
            f" same-direction {r['event_top20_same_direction']}/20",
            f"- G-P3 regional share: model {r['model_region_share']} vs measured"
            f" {r['measured_region_share']}",
            "",
        ]
        print("\n".join(lines[-6:]))
    out = bundle / "SUMMARY-posture-gate.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
