"""miso-171 — decompose MISO's reserve requirements into synchronised vs supplemental (READ-ONLY, no LP).

THE PREREQUISITE of the miso-171 charter (FINDING-miso170-scarcity-reserve-
supply-anatomy-2026-08-19.md §5): before any gating lever may be pre-registered,
the `miso_subregional_or_midwest` and `miso_rbdc` requirements must be
decomposed into their SYNCHRONISED (regulating + spinning — products BPM-002
defines as requiring a resource synchronised to the grid) and NON-SYNCHRONISED
(supplemental — legitimately providable by OFFLINE quick-start resources)
components, from MISO's OWN measured cleared series. Gating a supplemental
requirement to synchronised capacity would be a rule-1 [R-STRUCT] breach, so
this measurement decides whether the lever exists at all.

Everything here is a MEASUREMENT of committed artifacts; nothing is fed back
into a solve (rule 13 [R-MEASURED]). The product split uses the SAME parquet,
hour mapping and product sets as the solve-path loader
(`market_sim.data.reserve_requirements.load_miso_reserve_requirements`), so the
decomposition is exactly the split the LP families would see.

Sources, all committed:
  measured RT cleared reserve MW   data/raw/MISO-AS/asm_rt_cleared_mw_<y>.parquet
                                   (region North/Central/South x product reg/spin/supp/str)
  keeper P1 zonal demand           results/calibration/miso170_layup_B2/hourly/system_<y>.parquet
  keeper P1 reserve families       results/calibration/miso170_layup_B2/hourly/reserve_family_<y>.parquet

Stages:
  1 split     — per (region-set x product) cleared MW: annual mean, summer mean,
                and the 47-scarce-hour mean (top-47 by keeper system load within
                Jun-Sep, the FINDING-miso167 §1 / FINDING-miso170 §7 set)
  2 shares    — the synchronised (reg+spin) share of each family's OR
                requirement, with the hourly share distribution in the scarce set
  3 identity  — cross-checks: Midwest + South == market (the loader contract),
                and each keeper reserve-family requirement against the measured
                series it claims (rbdc == market, midwest == N+C, regspin ==
                market reg+spin, south == South)
  4 mcp       — MISO's own published DA/RT ASM MCP by PRODUCT in the 2025
                scarce hours, split DA-foreseen vs RT-only (miso-167 §5's
                DA>$150 line): how much of the published reserve price sits on
                the synchronised products vs supplemental
  5 liveness  — per-region aggregate online-headroom precursor (H_on = rho x
                online output of reserve-eligible ramp-capable units, from the
                committed miso169_gated_A unit_hourly — bit-identical to the
                miso-160-era keeper P1; the miso-170 lay-up census delta is
                DISCLOSED, direction conservative) vs the regional regspin
                requirement, at the solved rho (RHO_CLIP floor 0.5) and the
                CAMPD-measured rho (0.1764)

Hour key: the model's fixed non-leap 8760 EST calendar via the loader's own
`_to_model_hour` (MISO market reports never observe DST).

Run:  python3 scripts/probes/_miso171_reserve_product_decomposition.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.data.reserve_requirements import (  # noqa: E402
    MIDWEST_REGIONS,
    OR_PRODUCTS,
    REGSPIN_PRODUCTS,
    SOUTH_REGION,
    _to_model_hour,
    cleared_mw_path,
)

BUNDLE = ROOT / "results" / "calibration" / "miso170_layup_B2" / "hourly"
OUT = ROOT / "results" / "calibration" / "_miso171_reserve_product_decomposition.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760

# Fixed non-leap calendar: Jun 1 00:00 and Oct 1 00:00 hour-of-year bounds of
# the miso-167 §1 summer window (months 6-9).
SUMMER_LO, SUMMER_HI = 3624, 6552
N_SCARCE = 47

# Region sets mirroring the loader's family legs (reserve_requirements.py).
REGION_SETS: dict[str, tuple[str, ...]] = {
    "market": ("North", "Central", "South"),
    "midwest": tuple(MIDWEST_REGIONS),
    "south": (SOUTH_REGION,),
}

PRODUCTS = ("reg", "spin", "supp")


def hourly_series(df: pd.DataFrame, regions: tuple[str, ...], products: tuple[str, ...], year: int) -> np.ndarray:
    """Sum cleared MW over ``regions x products`` onto the 8760 model clock.

    ffill/bfill over posting gaps, the loader's documented tolerance.
    """
    sub = df[df["region"].isin(regions) & df["product"].isin(products)].copy()
    series = np.full(HOURS, np.nan)
    hourly = sub.groupby("_hour")["cleared_mw"].sum()
    idx = hourly.index.to_numpy(dtype=int)
    keep = (idx >= 0) & (idx < HOURS)
    series[idx[keep]] = hourly.to_numpy(dtype=float)[keep]
    return pd.Series(series).ffill().bfill().to_numpy(dtype=float)


def scarce_hours(year: int) -> np.ndarray:
    """Top-``N_SCARCE`` hours by keeper system load within Jun-Sep."""
    s = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    load = s.groupby("hour")["demand"].sum()
    summer = load[(load.index >= SUMMER_LO) & (load.index < SUMMER_HI)]
    return np.sort(summer.nlargest(N_SCARCE).index.to_numpy(dtype=int))


def stats(series: np.ndarray, scarce: np.ndarray) -> dict:
    summer = series[SUMMER_LO:SUMMER_HI]
    return {
        "annual_mean_mw": round(float(np.mean(series)), 1),
        "summer_mean_mw": round(float(np.mean(summer)), 1),
        "scarce47_mean_mw": round(float(np.mean(series[scarce])), 1),
        "scarce47_min_mw": round(float(np.min(series[scarce])), 1),
        "scarce47_max_mw": round(float(np.max(series[scarce])), 1),
    }


def share_stats(num: np.ndarray, den: np.ndarray, scarce: np.ndarray) -> dict:
    """Hourly share distribution of ``num/den`` (annual + scarce set)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        share = np.where(den > 0, num / den, np.nan)
    sc = share[scarce]
    return {
        "annual_mean_of_hourly_share": round(float(np.nanmean(share)), 4),
        "annual_share_of_means": round(float(np.mean(num) / np.mean(den)), 4),
        "scarce47_share_of_means": round(
            float(np.mean(num[scarce]) / np.mean(den[scarce])), 4
        ),
        "scarce47_hourly_share_p5": round(float(np.nanpercentile(sc, 5)), 4),
        "scarce47_hourly_share_p50": round(float(np.nanpercentile(sc, 50)), 4),
        "scarce47_hourly_share_p95": round(float(np.nanpercentile(sc, 95)), 4),
        "scarce47_hourly_share_min": round(float(np.nanmin(sc)), 4),
    }


def family_requirements(year: int, scarce: np.ndarray) -> dict:
    r = pd.read_parquet(BUNDLE / f"reserve_family_{year}.parquet")
    r = r[r["pass"] == "P1"]
    out = {}
    for fam, sub in r.groupby("family"):
        sub = sub.sort_values("hour")
        req = sub["requirement_mw"].to_numpy(dtype=float)
        dual = sub["dual"].to_numpy(dtype=float)
        out[str(fam)] = {
            "annual_mean_requirement_mw": round(float(np.mean(req)), 1),
            "scarce47_mean_requirement_mw": round(float(np.mean(req[scarce])), 1),
            "hours_dual_positive": int(np.sum(dual > 1e-9)),
            "scarce47_hours_dual_positive": int(np.sum(dual[scarce] > 1e-9)),
        }
    return out


def mcp_series(path: Path, products: dict[str, str], year: int, wide_label: str) -> dict[str, np.ndarray]:
    """Per-product market-wide MCP on the 8760 clock from an ASM MCP rollup."""
    df = pd.read_parquet(path)
    df = df[df["zone"] == wide_label]
    he_cols = [f"he{h:02d}" for h in range(1, 25)]
    out = {}
    for name, code in products.items():
        sub = df[df["product"] == code].copy()
        long = sub.melt(id_vars=["date"], value_vars=he_cols, var_name="he", value_name="mcp")
        long["hour_end_est"] = long["he"].str[2:].astype(int)
        long["_hour"] = _to_model_hour(long["date"], long["hour_end_est"], year)
        long = long[long["_hour"] >= 0]
        series = np.full(HOURS, np.nan)
        hourly = long.groupby("_hour")["mcp"].mean()
        idx = hourly.index.to_numpy(dtype=int)
        keep = idx < HOURS
        series[idx[keep]] = hourly.to_numpy(dtype=float)[keep]
        out[name] = pd.Series(series).ffill().bfill().to_numpy(dtype=float)
    return out


def stage4_mcp(scarce: np.ndarray) -> dict:
    """2025 published ASM MCP by product: scarce-47 split DA-foreseen vs RT-only."""
    year = 2025
    products = {"reg": "GENREGMCP", "spin": "GENSPINMCP", "supp": "GENSUPPMCP"}
    rt = mcp_series(ROOT / "data/raw/MISO-AS" / f"asm_rtmcp_zonal_{year}.parquet", products, year, "Miso-Wide")
    da = mcp_series(ROOT / "data/raw/MISO-AS" / f"asm_damcp_zonal_{year}.parquet", products, year, "MISO Wide")
    actual = pd.read_parquet(ROOT / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet")
    actual = actual[actual["year"] == year].set_index("hour").sort_index()
    da_lmp = actual["da"].reindex(range(HOURS)).to_numpy(dtype=float)
    # miso-167 §5's split of the 47 scarce hours: DA-foreseen = DA LMP > $150.
    foreseen = scarce[da_lmp[scarce] > 150.0]
    rt_only = scarce[da_lmp[scarce] <= 150.0]
    rec: dict = {
        "n_scarce": int(len(scarce)),
        "n_da_foreseen": int(len(foreseen)),
        "n_rt_only": int(len(rt_only)),
    }
    for label, hours_set in (("scarce47", scarce), ("da_foreseen", foreseen), ("rt_only", rt_only)):
        rec[label] = {}
        for market, series_map in (("rt_mcp", rt), ("da_mcp", da)):
            vals = {p: round(float(np.mean(s[hours_set])), 2) for p, s in series_map.items()}
            vals["regspin"] = round(vals["reg"] + vals["spin"], 2)
            vals["total"] = round(vals["reg"] + vals["spin"] + vals["supp"], 2)
            rec[label][market] = vals
    return rec


# Stage-5 instrument: the EXACT miso-169 §3 pre-check H_on construction
# (scripts/probes/_miso169_online_gated_precheck.py::hourly_headroom),
# replicated at REGIONAL grain — reserve-eligible fuels, plant-grain online
# threshold, headroom = cap − mw on online plants. Instrument continuity with
# the pre-registered K-PRE-A/B is the point; no new headroom concept.
LIVENESS_FUELS = ("coal", "gas_cc", "gas_ct", "gas_st", "nuclear", "oil")
ONLINE_THRESHOLD_MW = 1.0
LIVENESS_BUNDLE = ROOT / "results" / "calibration" / "miso169_gated_A" / "hourly"


def stage5_liveness(year: int, scarce: np.ndarray, regspin_mw: dict[str, np.ndarray]) -> dict:
    """Per-region online-headroom precursor vs the regional regspin requirement.

    H_on(region, t) = sum over reserve-eligible plants IN the region whose
    plant-level dispatch exceeds the online threshold of (cap − mw) — the
    miso-169 pre-check's own definition, from the committed miso169_gated_A
    unit_hourly (bit-identical to the miso-160-era keeper P1). DISCLOSED
    caveat: the current keeper (miso170_layup_B2) additionally lays up the
    15-plant ST_GAS census, removing ~0.5–0.95 TWh/yr of online output, so
    this measurement mildly OVERSTATES the current keeper's online headroom;
    the shortness counts below are correspondingly a floor.
    """
    u = pd.read_parquet(
        LIVENESS_BUNDLE / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "fuel", "zone", "hour", "mw", "cap_mw"],
    )
    u = u[(u["pass"] == "P1") & u["fuel"].isin(LIVENESS_FUELS)]
    u["region"] = np.where(u["zone"] == "MISO-South", "south", "midwest")
    g = (
        u.groupby(["region", "plant_code", "fuel", "hour"], observed=True)
        .agg(mw=("mw", "sum"), cap_mw=("cap_mw", "sum"))
        .reset_index()
    )
    online = g["mw"] > ONLINE_THRESHOLD_MW
    g["h_on"] = np.where(online, np.maximum(g["cap_mw"] - g["mw"], 0.0), 0.0)
    on = g.groupby(["region", "hour"])["h_on"].sum().unstack(0)
    rec: dict = {}
    shorts: dict[str, np.ndarray] = {}
    h_on_by_region: dict[str, np.ndarray] = {}
    for region in ("midwest", "south"):
        h_on = on[region].reindex(range(HOURS)).fillna(0.0).to_numpy(dtype=float)
        h_on_by_region[region] = h_on
        req = regspin_mw[region]
        short = h_on < req
        shorts[region] = short
        rec[region] = {
            "hours_short_all_year": int(np.sum(short)),
            "share_short_all_year": round(float(np.mean(short)), 5),
            "hours_short_scarce47": int(np.sum(short[scarce])),
            "share_h_on_meets_req_scarce47": round(float(np.mean(~short[scarce])), 4),
            "scarce47_mean_h_on_mw": round(float(np.mean(h_on[scarce])), 1),
            "scarce47_mean_req_mw": round(float(np.mean(req[scarce])), 1),
            "scarce47_min_margin_mw": round(float(np.min((h_on - req)[scarce])), 1),
            "scarce47_p10_margin_mw": round(float(np.percentile((h_on - req)[scarce], 10)), 1),
        }
    # The INCREMENTAL surface: hours a regional regspin leg is short while the
    # MARKET-WIDE regspin gate (miso-169, already keeper-armed) is NOT — the
    # only hours a locational extension can price beyond what the armed
    # mechanism already reaches. Market H_on is the two regions' sum; the
    # market requirement is the regional legs' sum (loader identity).
    market_h_on = h_on_by_region["midwest"] + h_on_by_region["south"]
    market_req = regspin_mw["midwest"] + regspin_mw["south"]
    market_short = market_h_on < market_req
    regional_short = shorts["midwest"] | shorts["south"]
    incremental = regional_short & ~market_short
    rec["market"] = {
        "hours_short_all_year": int(np.sum(market_short)),
        "hours_short_scarce47": int(np.sum(market_short[scarce])),
    }
    rec["incremental_regional_only"] = {
        "hours_all_year": int(np.sum(incremental)),
        "hours_scarce47": int(np.sum(incremental[scarce])),
        "midwest_only_hours_scarce47": int(
            np.sum((shorts["midwest"] & ~market_short)[scarce])
        ),
        "south_only_hours_scarce47": int(
            np.sum((shorts["south"] & ~market_short)[scarce])
        ),
    }
    return rec


def main() -> None:
    record: dict = {
        "session": "miso-171",
        "keeper_bundle": "results/calibration/miso170_layup_B2",
        "loader_contract": {
            "or_products": list(OR_PRODUCTS),
            "regspin_products": list(REGSPIN_PRODUCTS),
            "midwest_regions": list(MIDWEST_REGIONS),
            "south_region": SOUTH_REGION,
        },
        "years": {},
    }

    for year in YEARS:
        df = pd.read_parquet(cleared_mw_path(year))
        df = df[df["product"].isin(OR_PRODUCTS)].copy()
        df["_hour"] = _to_model_hour(df["date"], df["hour_end_est"], year)
        df = df[df["_hour"] >= 0]
        scarce = scarce_hours(year)

        yrec: dict = {"scarce47_hours": scarce.tolist(), "region_sets": {}}
        series: dict[tuple[str, str], np.ndarray] = {}
        for rname, regions in REGION_SETS.items():
            rrec = {"products": {}}
            for prod in PRODUCTS:
                s = hourly_series(df, regions, (prod,), year)
                series[(rname, prod)] = s
                rrec["products"][prod] = stats(s, scarce)
            or_s = sum(series[(rname, p)] for p in OR_PRODUCTS)
            rs_s = sum(series[(rname, p)] for p in REGSPIN_PRODUCTS)
            series[(rname, "or")] = or_s
            series[(rname, "regspin")] = rs_s
            rrec["or_total"] = stats(or_s, scarce)
            rrec["regspin"] = stats(rs_s, scarce)
            rrec["regspin_share_of_or"] = share_stats(rs_s, or_s, scarce)
            rrec["supp_share_of_or"] = share_stats(
                series[(rname, "supp")], or_s, scarce
            )
            yrec["region_sets"][rname] = rrec

        # Stage 3 — identities.
        mkt = series[("market", "or")]
        mw_plus_s = series[("midwest", "or")] + series[("south", "or")]
        yrec["identity_midwest_plus_south_vs_market_max_abs_mw"] = round(
            float(np.max(np.abs(mkt - mw_plus_s))), 6
        )
        yrec["keeper_families"] = family_requirements(year, scarce)
        if year == 2025:
            yrec["stage4_published_mcp_by_product"] = stage4_mcp(scarce)
            # Continuity with miso-167 §3 (its $484.87 total was measured on
            # the 47 summer hours whose ACTUAL RT exceeded $200): the same
            # product split on that set.
            actual167 = pd.read_parquet(
                ROOT / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet"
            )
            actual167 = actual167[actual167["year"] == year]
            rt167 = (
                actual167.set_index("hour")["rt"].reindex(range(HOURS)).to_numpy(dtype=float)
            )
            kpre167 = np.flatnonzero(
                (np.arange(HOURS) >= SUMMER_LO)
                & (np.arange(HOURS) < SUMMER_HI)
                & (rt167 > 200.0)
            )
            yrec["stage4_published_mcp_by_product_rt200"] = stage4_mcp(kpre167)
        regional_regspin = {
            "midwest": series[("midwest", "regspin")],
            "south": series[("south", "regspin")],
        }
        yrec["stage5_liveness_precursor_top47load"] = stage5_liveness(
            year, scarce, regional_regspin
        )
        if year == 2025:
            # Instrument continuity: the miso-169 K-PRE scarce set (summer
            # hours whose ACTUAL RT > $200 — n=47 in 2025 by coincidence of
            # count with the top-47-by-load set; the two sets overlap but
            # differ).
            actual = pd.read_parquet(
                ROOT / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet"
            )
            actual = actual[actual["year"] == year]
            rt = actual.set_index("hour")["rt"].reindex(range(HOURS)).to_numpy(dtype=float)
            kpre = np.flatnonzero(
                (np.arange(HOURS) >= SUMMER_LO)
                & (np.arange(HOURS) < SUMMER_HI)
                & (rt > 200.0)
            )
            yrec["stage5_liveness_precursor_rt200"] = stage5_liveness(
                year, kpre, regional_regspin
            )
            yrec["stage5_liveness_precursor_rt200"]["n_hours"] = int(kpre.size)
        fam = yrec["keeper_families"]
        yrec["family_vs_measured_scarce47_mw"] = {
            "miso_rbdc_minus_market_or": round(
                fam["miso_rbdc"]["scarce47_mean_requirement_mw"]
                - float(np.mean(mkt[scarce])),
                1,
            ),
            "miso_subregional_or_midwest_minus_midwest_or": round(
                fam["miso_subregional_or_midwest"]["scarce47_mean_requirement_mw"]
                - float(np.mean(series[("midwest", "or")][scarce])),
                1,
            ),
            "miso_rbdc_regspin_minus_market_regspin": round(
                fam["miso_rbdc_regspin"]["scarce47_mean_requirement_mw"]
                - float(np.mean(series[("market", "regspin")][scarce])),
                1,
            ),
            "miso_zonal_or_miso_south_minus_south_or": round(
                fam["miso_zonal_or_miso_south"]["scarce47_mean_requirement_mw"]
                - float(np.mean(series[("south", "or")][scarce])),
                1,
            ),
        }
        record["years"][str(year)] = yrec

    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")

    # Console headline: the decomposition verdict inputs.
    for year in YEARS:
        y = record["years"][str(year)]
        for rname in ("market", "midwest", "south"):
            r = y["region_sets"][rname]
            print(
                f"{year} {rname:8s} OR scarce47 {r['or_total']['scarce47_mean_mw']:7.1f} MW"
                f"  regspin {r['regspin']['scarce47_mean_mw']:7.1f}"
                f"  supp {r['products']['supp']['scarce47_mean_mw']:6.1f}"
                f"  regspin share {r['regspin_share_of_or']['scarce47_share_of_means']:.3f}"
                f"  (annual {r['regspin_share_of_or']['annual_share_of_means']:.3f})"
            )


if __name__ == "__main__":
    main()
