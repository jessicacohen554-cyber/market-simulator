"""Honesty gate for the PJM commitment-posture lever (design note §A, PJM port).

Scores a ``pjm_commitment_posture`` bundle against the MEASURED PJM reserve-
market series in ``data/raw/PJM-AS/reserve_market_results_<year>.parquet`` (PJM
Data Miner RT reserve market results). Per the design note and its PJM port
(``docs/handoffs/pjm-commitment-posture-port-2026-07.md`` §3) the acceptance
question is whether the modeled ONLINE HEADROOM / cleared-reserve behaviour
tracks the measured series in LEVEL and EVENT-DAY DIRECTION — the >$150/$200
price-tail count is NEVER the gate (CLAUDE.md rules 1/13).

Measured comparators (PJM_RTO locale, cleared ``total_mw``):

* **online target = Synchronized Reserve (SR) + Regulation (REG)** — the
  products that by design must be supplied by ONLINE units, the direct
  measured analogue of the model's postured online headroom. 30MIN
  (~15-21 GW, largely non-synchronised/offline quick-start) is excluded.
* Primary Reserve (PR) cleared is reported as an upper-bound reference.
* SR market clearing price (MCP) drives the event-day direction check.
* MAD-subzone (``locale == "MAD"``) PR share drives the diagnostic split.

Checks reported per year (pre-committed thresholds, §3):

* **G-P1 level** (decisive): modeled postured online headroom (Σ pools U − P)
  vs measured online target (SR+REG). PASS iff ratio ∈ [0.7, 1.5] all years.
* **G-P2 event-day direction**: daily Pearson r (model reserve price vs SR
  MCP; headroom vs cleared) and top-20 SR-MCP event-day same-direction count.
  PASS iff both r > 0 AND same-direction ≥ 12/20, in ≥ 2 of 3 years.
* **G-P3 regional split** (advisory): model MAD-zone share of online headroom
  vs measured MAD PR share (~0.75-0.80).

Daily aggregation makes any residual one-hour DST/convention slack immaterial
(PJM RT reports are EPT; the model horizon is the EIA-930 fixed-offset clock).

Usage:
    python scripts/report_pjm_posture_gate.py \
        --bundle results/calibration/pjm82_commitment_posture \
        --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR
from market_sim.config.reserve_config import PJM_MAD_ZONES

AS_DIR = RAW_DIR / "PJM-AS"

# Pre-committed level band and event-day threshold (§3 decision rule).
LEVEL_BAND = (0.7, 1.5)
EVENT_MIN_SAME_DIR = 12


def _measured_rt(year: int) -> pd.DataFrame:
    """RT reserve-market results for one year (PJM_RTO + MAD locales)."""
    return pd.read_parquet(AS_DIR / f"reserve_market_results_{year}.parquet")


def _hourly_online_target(df: pd.DataFrame) -> pd.Series:
    """Hourly measured online reserve (SR + REG cleared MW), PJM_RTO locale.

    5-min ``total_mw`` averaged within each EPT hour, then SR + REG summed —
    the reserve products supplied by online capacity.
    """
    rto = df[df["locale"] == "PJM_RTO"].copy()
    rto["hour_ts"] = rto["_dt_ept"].dt.floor("h")
    piv = (
        rto[rto["service"].isin(["SR", "REG"])]
        .groupby(["hour_ts", "service"])["total_mw"]
        .mean()
        .unstack("service")
        .fillna(0.0)
    )
    return (piv.get("SR", 0.0) + piv.get("REG", 0.0)).sort_index()


def _daily_sr_mcp(df: pd.DataFrame) -> pd.Series:
    """Daily mean PJM_RTO Synchronized Reserve MCP ($/MWh)."""
    sr = df[(df["locale"] == "PJM_RTO") & (df["service"] == "SR")].copy()
    sr["date"] = sr["_dt_ept"].dt.date
    return sr.groupby("date")["mcp"].mean()


def _mad_pr_share(df: pd.DataFrame) -> float:
    """Measured MAD PR cleared / RTO PR cleared (annual means)."""
    rto_pr = df[(df["locale"] == "PJM_RTO") & (df["service"] == "PR")][
        "total_mw"
    ].mean()
    mad_pr = df[(df["locale"] == "MAD") & (df["service"] == "PR")]["total_mw"].mean()
    return float(mad_pr / max(rto_pr, 1e-9))


def _reference_pr(df: pd.DataFrame) -> float:
    """Measured PJM_RTO Primary Reserve cleared MW (upper-bound reference)."""
    return float(
        df[(df["locale"] == "PJM_RTO") & (df["service"] == "PR")]["total_mw"].mean()
    )


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
    hours = int(post["hour"].max()) + 1

    # Modeled online headroom per hour: Σ postured pools (U − pool dispatch),
    # recovered via the dispatch frame; conservative bound (headroom ≥ R) when
    # the frame is absent (joint row P + R ≤ U).
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

    # Measured series.
    meas = _measured_rt(year)
    online_h = _hourly_online_target(meas)
    online_mean = float(online_h.mean())
    ref_pr = _reference_pr(meas)

    n = min(len(online_h), len(headroom))
    headroom_v = headroom.to_numpy()[:n]

    # Daily aggregation for the direction checks.
    day = np.arange(n) // 24
    online_d = pd.Series(online_h.to_numpy()[:n]).groupby(day).mean()
    headroom_d = pd.Series(headroom_v).groupby(day).mean()
    sr_mcp_d = _daily_sr_mcp(meas)
    z0 = sys_df["zone"].iloc[0]
    rp = (
        sys_df[sys_df["zone"] == z0].sort_values("hour")["reserve_price"].to_numpy()[:n]
    )
    rp_d = pd.Series(rp).groupby(day).mean()

    k = min(len(online_d), len(headroom_d), len(sr_mcp_d), len(rp_d))
    online_d, headroom_d = online_d.iloc[:k], headroom_d.iloc[:k]
    sr_v, rp_d = sr_mcp_d.iloc[:k].to_numpy(), rp_d.iloc[:k]

    r_price = float(np.corrcoef(rp_d, sr_v)[0, 1]) if rp_d.std() > 0 else float("nan")
    r_headroom = (
        float(np.corrcoef(headroom_d, online_d)[0, 1])
        if headroom_d.std() > 0
        else float("nan")
    )

    top = np.argsort(sr_v)[-20:]
    hd_med, rp_med = float(np.median(headroom_d)), float(np.median(rp_d))
    same_dir = int(
        np.sum((headroom_d.to_numpy()[top] < hd_med) | (rp_d.to_numpy()[top] > rp_med))
    )

    # Regional split: MAD vs non-MAD share of postured online headroom.
    post = post.copy()
    post["is_mad"] = post["zone"].isin(PJM_MAD_ZONES)
    tot_u = max(float(post["online_mw"].sum()), 1e-9)
    model_mad_share = float(post[post["is_mad"]]["online_mw"].sum() / tot_u)

    ratio = float(np.mean(headroom_v) / max(online_mean, 1e-9))
    return {
        "year": year,
        "pools": int(q_pools),
        "hours": hours,
        "model_headroom_mean_mw": float(np.mean(headroom_v)),
        "model_pool_reserve_mean_mw": float(r_by_hour.mean()),
        "measured_online_mean_mw": online_mean,
        "measured_primary_ref_mw": ref_pr,
        "level_ratio": ratio,
        "level_pass": bool(LEVEL_BAND[0] <= ratio <= LEVEL_BAND[1]),
        "daily_r_price_vs_srmcp": r_price,
        "daily_r_headroom_vs_online": r_headroom,
        "event_top20_same_direction": same_dir,
        "direction_pass": bool(
            (r_price > 0 or np.isnan(r_price))
            and r_headroom > 0
            and same_dir >= EVENT_MIN_SAME_DIR
        ),
        "model_mad_headroom_share": round(model_mad_share, 3),
        "measured_mad_pr_share": round(_mad_pr_share(meas), 3),
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
    level_all = all(r["level_pass"] for r in rows)
    dir_pass_years = sum(1 for r in rows if r["direction_pass"])
    accepted = level_all and dir_pass_years >= 2

    lines = [
        "# PJM commitment-posture honesty gate (design note §A, PJM port)",
        "",
        "Modeled online headroom / cleared-reserve behaviour vs the measured",
        "PJM reserve-market series (`data/raw/PJM-AS`). Level + event-day",
        "direction; the >$150/$200 tail count is NEVER the gate (rules 1/13).",
        "",
        f"**Pre-committed decision (§3): {'ACCEPT' if accepted else 'REJECT'}** — "
        f"G-P1 level {'PASS' if level_all else 'FAIL'} all-years, "
        f"G-P2 direction PASS in {dir_pass_years}/3 years "
        f"(accept needs level all-years AND direction ≥2/3).",
        "",
    ]
    for r in rows:
        lines += [
            f"## {r['year']}",
            "",
            f"- postured pools: {r['pools']}, startups {r['model_startups_gw']:.1f} GW/yr",
            f"- G-P1 level [{'PASS' if r['level_pass'] else 'FAIL'}]: model online headroom"
            f" mean {r['model_headroom_mean_mw']:.0f} MW (pool cleared R mean"
            f" {r['model_pool_reserve_mean_mw']:.0f} MW) vs measured online target (SR+REG)"
            f" {r['measured_online_mean_mw']:.0f} MW — ratio {r['level_ratio']:.2f}"
            f" (Primary ref {r['measured_primary_ref_mw']:.0f} MW; band"
            f" {LEVEL_BAND[0]}-{LEVEL_BAND[1]})",
            f"- G-P2 direction [{'PASS' if r['direction_pass'] else 'FAIL'}]: daily r(model"
            f" reserve price, SR MCP) = {r['daily_r_price_vs_srmcp']:.2f}; daily r(headroom,"
            f" online) = {r['daily_r_headroom_vs_online']:.2f}; top-20 SR-MCP event days"
            f" same-direction {r['event_top20_same_direction']}/20 (need ≥{EVENT_MIN_SAME_DIR})",
            f"- G-P3 MAD share (advisory): model {r['model_mad_headroom_share']} vs measured"
            f" {r['measured_mad_pr_share']}",
            "",
        ]
        print("\n".join(lines[-6:]))
    out = bundle / "SUMMARY-posture-gate.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
