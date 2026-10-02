"""PJM close-out census 0b (zero-LP): Winter Storm Elliott unavailable-MW gap.

Plan ``docs/backcast-closeout-plan-2026-10.md`` §3.6 step 0b; research shard
``docs/records/governance/closeout-2026-10/SHARD-PJM-closeout-research-2026-10-02.md``
§2 (C3a 2022), §3 row 1, §4 L3. Reads committed artifacts only; never solves.

Question: hourly, 20-28 Dec 2022 (EPT hour-ending), is
``gap = published PJM forced outage MW - model unavailable MW`` >= 15 GW in
>= 18 hours?  (Pre-fixed reading: CONFIRMED iff yes, else NOT CONFIRMED.)

Inputs
------
* Published: ``data/raw/pjm-outages/by-year/gen_outages_by_type_<y>.csv``
  (Data Miner 2 ``gen_outages_by_type``), region ``PJM RTO``, ``lead_days == 0``.
  The feed is a DAILY snapshot posted 06:00 EPT; each delivery day's MW is
  broadcast flat across its 24 hours (the same broadcast
  ``market_sim.data.pjm_outages.pjm_outage_mw_series`` applies).
* Model: keeper ``results/calibration/pjmnext16_A_span/hourly/unit_marginal_<y>.parquet``
  (P1). ``cap_mw = pmax x availability`` (``run_calibration_full._unit_hourly_frame``).
  ``pmax`` is not in the sidecar and the fleet rebuild needs ``data/clean``
  partitions absent in this container, so installed MW per unit is PROXIED by
  the unit's max ``cap_mw`` over the year. That UNDERSTATES model unavailable MW
  for any unit never at full availability (the gap is therefore an UPPER bound
  on the true pmax-basis gap).

Clock: the PJM model clock is the EIA-930 local (prevailing Eastern) year, rows
UTC-ordered, hour-ending stamps (``data/eia930/demand._load_pjm_hourly_demand``,
``frames._clean_local_year_rows``); row k = local hour-ending k+1 of the year.
Spring-forward (23 rows) and fall-back (25 rows) net to zero by December, so
Dec d hour-ending HE maps to row ``(doy0(d)) * 24 + HE - 1`` with no offset.

Classes: VIRTUAL_* rows (DA virtual bids) are excluded; ``import`` pseudo-units
are reported separately and never counted as generation outage. ``thermal`` =
coal, CC, CT, ST, oil, nuclear; ``all`` = thermal + hydro.

Run: ``python scripts/probes/_pjmco_0b_elliott_census.py``
Writes ``results/phase0/pjm/_pjmco_0b_elliott_census.json`` and
``results/phase0/pjm/_pjmco_0b_elliott_census_hourly.csv``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/pjmnext16_A_span"
PUB_DIR = REPO / "data/raw/pjm-outages/by-year"
OUT_DIR = REPO / "results/phase0/pjm"
OUT_JSON = OUT_DIR / "_pjmco_0b_elliott_census.json"
OUT_CSV = OUT_DIR / "_pjmco_0b_elliott_census_hourly.csv"

#: Pre-fixed reading (PRECOMMIT, do not change).
GAP_MW = 15_000.0
MIN_HOURS = 18
DAYS = list(range(20, 29))  # 20..28 Dec 2022
BASE_DAYS = (20, 21, 22)  # pre-event baseline for the increment sensitivity
DOY0_DEC1 = 334  # non-leap day-of-year (0-based) of 1 Dec
NON_GEN = ("import",)


def hour_index(day: int, he: int) -> int:
    """Model-clock row of Dec ``day`` hour-ending ``he`` (EPT, 1..24)."""
    return (DOY0_DEC1 + day - 1) * 24 + he - 1


def published(year: int) -> pd.DataFrame:
    """Same-day (lead 0) PJM RTO outage rows for ``year``, indexed by date."""
    o = pd.read_csv(PUB_DIR / f"gen_outages_by_type_{year}.csv")
    r = o[(o.region == "PJM RTO") & (o.lead_days == 0)].copy()
    r["date"] = pd.to_datetime(r.forecast_date)
    return r.set_index("date").sort_index()


def model_unavailable(year: int) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Per-unit (unit x hour) unavailable MW on the max-cap proxy.

    Returns ``(unavail, klass, installed_proxy, exit_flag)`` where ``exit_flag``
    marks units at ~0 cap from some hour through year end and also through the
    whole Elliott window (retired/long-out units; ambiguous by construction).
    """
    x = pd.read_parquet(
        BUNDLE / f"hourly/unit_marginal_{year}.parquet",
        columns=["unit_id", "plant_group", "fuel", "hour", "cap_mw"],
    )
    x["k"] = x.plant_group.astype(str)
    blank = x.k == ""
    x.loc[blank, "k"] = x.loc[blank, "fuel"].astype(str)
    x = x[~x.k.str.startswith("VIRTUAL")]
    cap = x.pivot_table(index="unit_id", columns="hour", values="cap_mw", observed=True)
    klass = x.drop_duplicates("unit_id").set_index("unit_id").k.reindex(cap.index)
    mx = cap.max(axis=1)
    unav = cap.rsub(mx, axis=0)
    h0 = hour_index(DAYS[0], 1)
    exit_flag = (cap.loc[:, h0:] <= 0.5).all(axis=1) & (mx > 0)
    return unav, klass, mx, exit_flag


def main() -> dict:
    """Run the census and write the JSON/CSV outputs."""
    pub = published(2022)
    unav, klass, mx, exitf = model_unavailable(2022)
    gen = ~klass.isin(NON_GEN)
    thermal = gen & (klass != "hydro")
    hrs = [hour_index(d, he) for d in DAYS for he in range(1, 25)]

    def ssum(mask: pd.Series) -> np.ndarray:
        return unav.loc[mask, hrs].sum(axis=0).to_numpy()

    hourly = pd.DataFrame(
        {
            "day": np.repeat(DAYS, 24),
            "he_ept": np.tile(np.arange(1, 25), len(DAYS)),
            "model_hour": hrs,
        }
    )
    for col in ("forced_outages_mw", "planned_outages_mw", "maintenance_outages_mw", "total_outages_mw"):
        hourly["pub_" + col.split("_")[0]] = [
            float(pub.loc[pd.Timestamp(2022, 12, d), col]) for d in hourly.day
        ]
    hourly["model_thermal"] = ssum(thermal)
    hourly["model_all"] = ssum(gen)
    hourly["model_thermal_ex_exit"] = ssum(thermal & ~exitf)
    hourly["model_import_pseudo"] = ssum(~gen)
    hourly["gap_headline"] = hourly.pub_forced - hourly.model_thermal
    variants = {
        "forced_vs_all": hourly.pub_forced - hourly.model_all,
        "total_vs_thermal": hourly.pub_total - hourly.model_thermal,
        "total_vs_all": hourly.pub_total - hourly.model_all,
        "forced_vs_thermal_ex_exit": hourly.pub_forced - hourly.model_thermal_ex_exit,
        "total_vs_thermal_ex_exit": hourly.pub_total - hourly.model_thermal_ex_exit,
    }
    base = hourly.day.isin(BASE_DAYS)
    variants["event_increment_forced_vs_thermal"] = (
        hourly.pub_forced - hourly.pub_forced[base].mean()
    ) - (hourly.model_thermal - hourly.model_thermal[base].mean())
    for k, v in variants.items():
        hourly["gap_" + k] = v

    # Keeper scarcity signals
    rf = pd.read_parquet(BUNDLE / "hourly/reserve_family_2022.parquet")
    rf = rf[rf.hour.isin(hrs)]
    rfh = rf.groupby("hour").agg(dual_max=("dual", lambda s: float(np.abs(s).max())), shortfall=("shortfall_mw", "sum"))
    sy = pd.read_parquet(BUNDLE / "hourly/system_2022.parquet", columns=["hour", "price", "slack", "reserve_price"])
    sy = sy[sy.hour.isin(hrs)]
    syh = sy.groupby("hour").agg(price_max=("price", "max"), slack=("slack", "sum"), rprice=("reserve_price", "max"))
    hourly = hourly.join(rfh, on="model_hour").join(syh, on="model_hour")

    n_hit = int((hourly.gap_headline >= GAP_MW).sum())
    verdict = "CONFIRMED" if n_hit >= MIN_HOURS else "NOT CONFIRMED"
    var_counts = {k: int((v >= GAP_MW).sum()) for k, v in variants.items()}
    var_verdicts = {k: ("CONFIRMED" if c >= MIN_HOURS else "NOT CONFIRMED") for k, c in var_counts.items()}

    daily = hourly.groupby("day").agg(
        pub_forced=("pub_forced", "first"),
        pub_total=("pub_total", "first"),
        model_thermal=("model_thermal", "mean"),
        model_all=("model_all", "mean"),
        model_thermal_ex_exit=("model_thermal_ex_exit", "mean"),
        gap=("gap_headline", "mean"),
        gap_max=("gap_headline", "max"),
        hours_ge15=("gap_headline", lambda s: int((s >= GAP_MW).sum())),
        price_max=("price_max", "max"),
        reserve_dual_max=("dual_max", "max"),
        reserve_shortfall_max=("shortfall", "max"),
        slack_max=("slack", "max"),
    )

    # Window class breakdown (daily mean MW)
    win_cls = unav.loc[gen, hrs].groupby(klass[gen]).sum()
    win_cls = pd.DataFrame(
        win_cls.to_numpy().reshape(len(win_cls), len(DAYS), 24).mean(axis=2),
        index=win_cls.index,
        columns=DAYS,
    )

    # Secondary: annual means 2022-2025 and 2022 class split
    annual = {}
    cls2022 = None
    for y in (2022, 2023, 2024, 2025):
        p = published(y)
        u, kl, m, ef = model_unavailable(y) if y != 2022 else (unav, klass, mx, exitf)
        g = ~kl.isin(NON_GEN)
        th = g & (kl != "hydro")
        annual[y] = {
            "pub_total_mean": float(p.total_outages_mw.mean()),
            "pub_forced_mean": float(p.forced_outages_mw.mean()),
            "pub_planned_plus_maint_mean": float((p.planned_outages_mw + p.maintenance_outages_mw).mean()),
            "model_thermal_mean_proxy": float(u.loc[th].sum(axis=0).mean()),
            "model_all_mean_proxy": float(u.loc[g].sum(axis=0).mean()),
            "model_installed_proxy_gen": float(m[g].sum()),
        }
        if y == 2022:
            out_mean = u.loc[g].mean(axis=1).groupby(kl[g]).sum()
            inst = m[g].groupby(kl[g]).sum()
            cls2022 = pd.DataFrame({"installed_proxy_mw": inst, "unavail_mean_mw": out_mean})
            cls2022["unavail_frac"] = cls2022.unavail_mean_mw / cls2022.installed_proxy_mw
            fleet_rate = annual[y]["pub_total_mean"] / float(m[g].sum())
            cls2022["excess_vs_pub_fleet_rate_mw"] = cls2022.unavail_mean_mw - fleet_rate * cls2022.installed_proxy_mw
            annual[y]["pub_total_fleet_rate_on_proxy"] = fleet_rate

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(OUT_CSV, index=False)
    res = {
        "census": "pjmco-0b Elliott unavailable-MW gap (zero-LP)",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "window": "2022-12-20 HE01 .. 2022-12-28 HE24 EPT (216 h)",
        "clock": "EIA-930 local prevailing Eastern year, UTC-ordered, hour-ending; row=(doy0)*24+HE-1 (DST nets to 0 by Dec)",
        "published_basis": "gen_outages_by_type PJM RTO lead_days==0, 06:00 EPT daily snapshot broadcast flat over 24 h",
        "model_basis": "sum over units of (max_2022 cap_mw - cap_mw); cap_mw=pmax*availability; max-cap is the installed proxy (pmax not in sidecar; fleet rebuild blocked: data/clean absent)",
        "prefixed_reading": f"CONFIRMED iff gap >= {GAP_MW:.0f} MW in >= {MIN_HOURS} h",
        "headline": "published FORCED - model unavailable THERMAL",
        "hours_ge_15gw": n_hit,
        "verdict": verdict,
        "variant_hours_ge_15gw": var_counts,
        "variant_verdicts": var_verdicts,
        "verdict_flips_under_variant": sorted(k for k, v in var_verdicts.items() if v != verdict),
        "daily": daily.round(1).reset_index().to_dict(orient="records"),
        "window_model_unavail_by_class_daily_mean_mw": win_cls.round(0).to_dict(orient="index"),
        "exit_bucket_mw": float(mx[exitf & gen].sum()),
        "exit_bucket_by_class_mw": mx[exitf & gen].groupby(klass[exitf & gen]).sum().round(0).to_dict(),
        "secondary_annual_means": annual,
        "secondary_2022_by_class": cls2022.round(3).to_dict(orient="index"),
    }
    OUT_JSON.write_text(json.dumps(res, indent=1, default=float))
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("hours_ge_15gw", "verdict", "variant_hours_ge_15gw", "verdict_flips_under_variant")}, indent=1))
    print(pd.DataFrame(r["daily"]).to_string())
    print(pd.DataFrame(r["window_model_unavail_by_class_daily_mean_mw"]).T.to_string())
    print(json.dumps(r["exit_bucket_by_class_mw"]))
    print(pd.DataFrame(r["secondary_annual_means"]).round(0).to_string())
    print(pd.DataFrame(r["secondary_2022_by_class"]).T.round(2).T.to_string())
