"""Phase-0 measurement: what CAISO storage actually earns from ancillary services.

The CAISO value-stack lane (D-9, `docs/FINDING-entry-screen-t1h-2026-08.md` §6;
charter `docs/FINDING-entry-signal-disarm-2026-08.md` §5.4/§6): the model's
forecast-lane storage entry screen credits CAISO storage **$0** of AS revenue
(`as_revenue_enabled=False` and `AS_REVENUE_PER_KW_YR_BY_ISO` carries no CAISO
row — an honest, ERCOT-only registry). This probe measures the honest CAISO
number from CAISO's own market data, BEFORE any effect-on-entry arithmetic is
taken (rule 13 [R-MEASURED] / rule 21 [R-DOF]: the value is identified from AS
market data alone, never from what it does to the storage-entry gap).

Measurement = award-weighted DAM AS revenue of the CAISO battery fleet:

    revenue[product, hour] = award_mw[product, hour] x ASMP[product, hour]

* **Awards** — `data/clean/storage-as-awards/CAISO` (CAISO Daily Energy Storage
  Report quarterly xlsx, curated by `scripts/data/curate_storage_as_awards.py`;
  DA battery award means reproduce the DMM-published ~1,040 MW (2023) /
  ~1,500 MW (2024) hourly battery AS procurement to ~1%): hourly IFM award MW
  held by battery (LESR) + hybrid (HYBD) resources, products RU/RD/SR/NR.
* **Prices** — `data/raw/CAISO-AS/asprc_ALL_*.csv` (OASIS `PRC_AS` DAM, fetched
  by `scripts/data/fetch_caiso_oasis.py --datasets asprc`; OASIS caps PRC_AS at
  one trade day per request, hence day files): hourly $/MW clearing-price
  contribution per AS region and product. CAISO's AS regions NEST
  (`AS_CAISO_EXP` ⊃ `AS_CAISO` ⊃ {`AS_NP26[_EXP]`, `AS_SP26[_EXP]`}) and the
  published rows are per-constraint shadow-price contributions — verified in
  the data itself: sub-region rows are usually 0 and always small relative to
  the system row, impossible if rows were totals. A resource's settlement ASMP
  is the SUM over the regions containing it, so an internal battery earns
  `AS_CAISO + AS_CAISO_EXP` plus its own sub-region's `AS_NP26(+_EXP)` or
  `AS_SP26(+_EXP)` adder.
* **Region reconciliation (rule 14 [R-ACCURATE], documented misalignment)** —
  the DESR award series is SYSTEM-level (not split north/south), so the
  sub-region adder a given awarded MW earns is not observable. The probe
  reports three brackets: LOW (system contribution + min sub-region adder),
  HIGH (+ max adder), CENTRAL (+ requirement-share-weighted adder, weights =
  each sub-region's share of the system regional-minimum AS requirement from
  the measured AS_REQ series on disk). The bracket width is reported; it is
  small because the sub-regional constraints bind rarely.
* **Fleet denominator** — the measured EIA-860 CAISO battery fleet via the
  model's own loader (`model.storage.load_eia860_storage`,
  `storage_vintage_ramp=True`), li-ion only (pumped storage is not an LESR),
  averaged over the year's months. Same basis as the model's own storage
  accounting (rule 14).

Omissions, both conservative (they can only make the true AS revenue LARGER
than the DA-leg number reported here, and both are bounded in the output):

* **Real-time incremental AS** — RTPD awards settle incrementally against the
  DA award at RT prices; RT AS prices are a separate (15-minute) OASIS series
  not intaken. The probe reports the mean RTM-vs-DAM award delta per product
  so the omitted leg's size is visible.
* **Regulation mileage** — CAISO pays regulation mileage (RMU/RMD) on top of
  capacity; the DESR carries no mileage award MW. The DMM cross-validation
  below absorbs both omissions.

Cross-validation (external anchor, never an input): the DMM 2023/2024 Special
Reports on Battery Storage give battery net market revenue $103 (2022) → $78
(2023) → $53/kW-yr (2024) with energy = ~62% (2023) / ~82% (2024) and RT bid
cost recovery = 7% / 4% — leaving ≈$24 (2023) / ≈$7/kW-yr (2024) for AS +
other. The probe's DA-leg $/kW-yr must land at or below those remainders and
reproduce the collapse.

No LP, no solve, no ScenarioConfig change; reads committed/curated data only.
Run:

    PYTHONPATH=. uv run python scripts/probes/caiso_storage_as_revenue_phase0.py \
        --out results/calibration/caiso_storage_as_revenue_phase0.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

YEARS = (2023, 2024, 2025)

#: Product taxonomy map, identical to the storage-as-awards / ancillary-services
#: schemas (CAISO RU/RD/SR/NR -> reconciled names).
PRODUCTS = {"RU": "reg_up", "RD": "reg_down", "SR": "spin", "NR": "nonspin"}

#: PRC_AS XML_DATA_ITEM per product (the price sits in the MW column).
_CLR = {"RU": "RU_CLR_PRC", "RD": "RD_CLR_PRC", "SR": "SP_CLR_PRC", "NR": "NS_CLR_PRC"}


def _load_prices(raw_dir: Path, year: int) -> pd.DataFrame:
    """Hourly per-product price contributions by region group for ``year``.

    Returns a frame indexed by UTC hour with columns
    ``(product, {'sys','np26','sp26'})`` in $/MW: ``sys`` is the system
    contribution (AS_CAISO + AS_CAISO_EXP) every internal resource earns;
    ``np26``/``sp26`` are the sub-region adders (internal + _EXP rows summed).
    """
    files = sorted(glob.glob(str(raw_dir / f"asprc_ALL_{year}*.csv")))
    if not files:
        raise FileNotFoundError(f"no asprc files for {year} under {raw_dir}")
    frames = []
    for f in files:
        df = pd.read_csv(
            f,
            usecols=[
                "INTERVALSTARTTIME_GMT",
                "ANC_TYPE",
                "ANC_REGION",
                "XML_DATA_ITEM",
                "MW",
            ],
        )
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df = df[df["ANC_TYPE"].isin(PRODUCTS)]
    # Keep only the capacity clearing-price item for each product (drops the
    # RMU/RMD mileage rows, which have their own ANC_TYPE anyway).
    df = df[
        df.apply(lambda r: r["XML_DATA_ITEM"] == _CLR.get(r["ANC_TYPE"], ""), axis=1)
    ]
    df["ts"] = pd.to_datetime(df["INTERVALSTARTTIME_GMT"], utc=True)
    group_of = {
        "AS_CAISO": "sys",
        "AS_CAISO_EXP": "sys",
        "AS_NP26": "np26",
        "AS_NP26_EXP": "np26",
        "AS_SP26": "sp26",
        "AS_SP26_EXP": "sp26",
    }
    df["grp"] = df["ANC_REGION"].map(group_of)
    df = df.dropna(subset=["grp"])
    out = (
        df.pivot_table(
            index="ts",
            columns=["ANC_TYPE", "grp"],
            values="MW",
            aggfunc="sum",
        )
        .sort_index()
        .fillna(0.0)
    )
    return out


def _load_req_weights(raw_dir: Path, year: int) -> pd.DataFrame:
    """Sub-region shares of the system regional-minimum AS requirement.

    From the measured AS_REQ series (`asreq_ALL_*.csv`): per product-hour,
    ``w_np26 = NP26_min / (NP26_min + SP26_min)`` (0.5 where both are zero).
    Used ONLY to weight the sub-region price adders in the CENTRAL bracket.
    """
    files = sorted(glob.glob(str(raw_dir / "asreq_ALL_*.csv")))
    frames = []
    for f in files:
        base = os.path.basename(f)
        span = base.replace("asreq_ALL_", "").replace(".csv", "")
        y0, y1 = int(span[:4]), int(span[9:13])
        if y1 < year or y0 > year:
            continue
        df = pd.read_csv(
            f,
            usecols=[
                "INTERVALSTARTTIME_GMT",
                "ANC_TYPE",
                "ANC_REGION",
                "XML_DATA_ITEM",
                "MW",
            ],
        )
        df = df[df["ANC_TYPE"].isin(PRODUCTS)]
        df = df[df["XML_DATA_ITEM"].str.endswith("_REQ_MIN_MW")]
        df = df[df["ANC_REGION"].isin(["AS_NP26", "AS_SP26"])]
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no asreq files covering {year} under {raw_dir}")
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["INTERVALSTARTTIME_GMT"], utc=True)
    df = df[df["ts"].dt.year == year]
    piv = (
        df.pivot_table(
            index="ts", columns=["ANC_TYPE", "ANC_REGION"], values="MW", aggfunc="sum"
        )
        .sort_index()
        .fillna(0.0)
    )
    out = {}
    for p in PRODUCTS:
        np26 = piv.get((p, "AS_NP26"), pd.Series(0.0, index=piv.index))
        sp26 = piv.get((p, "AS_SP26"), pd.Series(0.0, index=piv.index))
        tot = np26 + sp26
        w = np.where(tot > 0, np26 / tot.replace(0, np.nan), 0.5)
        out[p] = pd.Series(np.nan_to_num(w, nan=0.5), index=piv.index)
    return pd.DataFrame(out)


def _load_awards(clean_dir: Path, year: int) -> pd.DataFrame:
    """Hourly DAM award MW per product (battery + hybrid) and the RTM deltas."""
    df = pd.read_parquet(clean_dir / f"storage-as-awards_{year}.parquet")
    return df


def _fleet_avg_mw(year: int) -> float:
    """Monthly-average measured CAISO battery (li-ion) fleet power, MW."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.storage import load_eia860_storage

    cfg = ScenarioConfig(iso="CAISO", mode="backcast", storage_vintage_ramp=True)
    units = load_eia860_storage("CAISO", year, cfg)
    tot = 0.0
    for u in units:
        if u.tech_name != "li_ion":
            continue
        prof = u.monthly_power_mw
        tot += float(np.mean(prof)) if prof is not None else float(u.power_cap_mw)
    return tot


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--out",
        default=str(REPO / "results/calibration/caiso_storage_as_revenue_phase0.json"),
    )
    ap.add_argument(
        "--years", nargs="+", type=int, default=list(YEARS), help="years to measure"
    )
    args = ap.parse_args()

    raw_dir = REPO / "data/raw/CAISO-AS"
    clean_dir = REPO / "data/clean/storage-as-awards/CAISO"

    result: dict = {
        "probe": "caiso_storage_as_revenue_phase0",
        "lane": "caiso-value-stack-d9",
        "method": (
            "DAM battery+hybrid AS award MW (Daily Energy Storage Report, curated) "
            "x DAM per-product ASMP (OASIS PRC_AS, nested-region contributions "
            "summed: sys=AS_CAISO+AS_CAISO_EXP; sub-region adders bracketed "
            "LOW/CENTRAL/HIGH), / measured EIA-860 CAISO battery fleet "
            "(monthly-average, li-ion only)"
        ),
        "years": {},
    }

    rates_central = {}
    fleets = {}
    for year in args.years:
        prices = _load_prices(raw_dir, year)
        hours_expected = 8784 if year % 4 == 0 else 8760
        n_price_hours = len(prices)
        if n_price_hours < hours_expected - 24:
            raise SystemExit(
                f"{year}: only {n_price_hours}/{hours_expected} price hours on disk "
                "— asprc fetch incomplete; refusing to report a partial-year rate."
            )
        weights = _load_req_weights(raw_dir, year)
        awards = _load_awards(clean_dir, year)
        dam = awards[awards["market"] == "DAM"]
        rtm = awards[awards["market"] == "RTM"]

        yr: dict = {"products": {}, "n_price_hours": n_price_hours}
        rev_low = rev_central = rev_high = 0.0
        for code, product in PRODUCTS.items():
            a = (
                dam[dam["product"] == product]
                .groupby("interval_start_utc")["award_mw"]
                .sum()
            )
            sys_p = prices.get((code, "sys"), pd.Series(0.0, index=prices.index))
            np_p = prices.get((code, "np26"), pd.Series(0.0, index=prices.index))
            sp_p = prices.get((code, "sp26"), pd.Series(0.0, index=prices.index))
            idx = a.index.intersection(sys_p.index)
            a = a.reindex(idx).fillna(0.0)
            sys_p = sys_p.reindex(idx).fillna(0.0)
            np_p = np_p.reindex(idx).fillna(0.0)
            sp_p = sp_p.reindex(idx).fillna(0.0)
            w = (
                weights[code].reindex(idx).ffill().fillna(0.5)
                if code in weights
                else pd.Series(0.5, index=idx)
            )
            lo = float((a * (sys_p + np.minimum(np_p, sp_p))).sum())
            ce = float((a * (sys_p + w * np_p + (1.0 - w) * sp_p)).sum())
            hi = float((a * (sys_p + np.maximum(np_p, sp_p))).sum())
            rev_low += lo
            rev_central += ce
            rev_high += hi
            r = rtm[rtm["product"] == product]
            rtm_mean = float(
                r.groupby("interval_start_utc")["award_mw"].sum().mean() or 0.0
            )
            yr["products"][product] = {
                "dam_award_mean_mw": round(float(a.mean()), 1),
                "dam_price_sys_mean_usd_mw": round(float(sys_p.mean()), 3),
                "np26_adder_mean": round(float(np_p.mean()), 4),
                "sp26_adder_mean": round(float(sp_p.mean()), 4),
                "revenue_central_usd_m": round(ce / 1e6, 2),
                "rtm_award_mean_mw": round(rtm_mean, 1),
            }

        fleet = _fleet_avg_mw(year)
        fleets[year] = fleet
        rate_lo = rev_low / fleet / 1000.0
        rate_ce = rev_central / fleet / 1000.0
        rate_hi = rev_high / fleet / 1000.0
        rates_central[year] = rate_ce
        yr.update(
            {
                "dam_as_revenue_usd_m": {
                    "low": round(rev_low / 1e6, 2),
                    "central": round(rev_central / 1e6, 2),
                    "high": round(rev_high / 1e6, 2),
                },
                "fleet_avg_mw_eia860": round(fleet, 0),
                "rate_usd_per_kw_yr": {
                    "low": round(rate_lo, 2),
                    "central": round(rate_ce, 2),
                    "high": round(rate_hi, 2),
                },
            }
        )
        result["years"][year] = yr

    # Saturation shape: implied exponent of (fleet_ref / fleet)^k between the
    # measurement years, against the shipped shared ERCOT_AS_SATURATION_EXPONENT.
    ys = sorted(rates_central)
    sat = {}
    for y0, y1 in zip(ys, ys[1:]):
        if rates_central[y0] > 0 and rates_central[y1] > 0:
            k = float(
                np.log(rates_central[y1] / rates_central[y0])
                / np.log(fleets[y0] / fleets[y1])
            )
            sat[f"{y0}->{y1}"] = {
                "rate_ratio": round(rates_central[y1] / rates_central[y0], 3),
                "fleet_ratio": round(fleets[y1] / fleets[y0], 3),
                "implied_exponent": round(k, 2),
            }
    result["saturation"] = sat
    result["dmm_cross_validation"] = {
        "battery_net_market_revenue_usd_per_kw_yr": {
            "2022": 103,
            "2023": 78,
            "2024": 53,
        },
        "energy_share": {"2023": 0.62, "2024": 0.82},
        "rt_bcr_share_of_total": {"2023": 0.07, "2024": 0.04},
        "implied_as_plus_other_usd_per_kw_yr": {"2023": 24.1, "2024": 7.4},
        "source": (
            "CAISO DMM, 2023 Special Report on Battery Storage (Jul 16 2024) "
            "§1.2/§2.8.1; 2024 Special Report on Battery Storage (May 29 2025) "
            "§1.2/§2.9.1"
        ),
        "note": (
            "implied = total x (1 - energy share) - RT BCR; includes the 'other' "
            "settlement bucket, so it is an UPPER bound on AS capacity revenue — "
            "the probe's DA-leg central rate must land at or below it and "
            "reproduce the 2023->2024 collapse."
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
