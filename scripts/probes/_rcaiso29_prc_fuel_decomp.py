"""R-CAISO-29 probe (zero LP): decompose CAISO OASIS ``PRC_FUEL`` against the keeper's delivered gas.

CAISO's fuel-region gas price is published as ``GAS INDEX + TRANSPORT`` per region (the monthly
"Gas Price Component of Projected Proxy Cost" template, CAISO Tariff §39.6.1.6.1). Each non-GHG
region has a ``…GHG`` twin: same index, lower transport. The twin gap is the LDC cap-and-trade
pass-through that a covered-entity generator does not pay through the LDC (it surrenders allowances
itself). This probe splits ``PRC_FUEL(region) − model delivered`` into:

1. hub basis       = CAISO hub index − NGI CA composite (flow-dated)  [index basis]
2. tariff gap      = GHG-twin transport − CAISO_CITYGATE_TRANSPORT_ADDER [intrastate transport]
3. LDC C&T charge  = non-GHG transport − GHG-twin transport            [carbon, already in model mc]

The daily hub index is not public, so transport is identified as ``PRC_FUEL − measured citygate
print`` on days where EIA's weekly narrative carries a PG&E / SoCal citygate print
(``pge_socal_citygate_weekly.csv``), print placed on its flow day (trade + 1). The construction is
validated against the published Oct–Dec 2025 transport components before it is applied to 2022–24.

The model series is rebuilt through the keeper's own code path
(``hubs._caiso_hub_daily_gas_prices`` with the keeper's ``scenario_config``) plus the transport
adder, exactly as ``apply_hub_basis_overlay`` layers it. Scoping evidence only; nothing feeds a solve.

Usage::

    python3 scripts/probes/_rcaiso29_prc_fuel_decomp.py --out <scratch dir> --start 2022-01 --end 2025-12
"""

from __future__ import annotations

import argparse
import dataclasses
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import CAISO_CITYGATE_TRANSPORT_ADDER
from market_sim.config.paths import GAS_PRICES_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel import hubs

OASIS = (
    "https://oasis.caiso.com/oasisapi/SingleZip?queryname=PRC_FUEL&fuel_region_id=ALL"
    "&startdatetime={s}T{hs}:00-0000&enddatetime={e}T{he}:00-0000&version=1&resultformat=6"
)
KEEPER_RUN_CONFIG = Path("results/calibration/rcaiso20_A_span/run_config.json")
# Region families compared (PG&E index vs SoCal index); each with its GHG twin.
PAIRS = {
    "PGE": ["FRPGE1", "FRPGE2", "FRPGE3", "FRPGE4", "FRPGE7"],
    "SOCAL": ["FRSCE1", "FRSCE2", "FRSCE3", "FRSCE5", "FRSDG1", "FRSDG2", "FRSDG3"],
}
REGIONS_KEEP = sorted(
    {r for v in PAIRS.values() for r in v}
    | {r + "GHG" for v in PAIRS.values() for r in v}
    | {"FRCISO", "FRKERN", "FRPGE"}
)


def _utc_hour(day: pd.Timestamp) -> str:
    """UTC hour of Pacific midnight on ``day`` ("07" in PDT, "08" in PST)."""
    off = day.tz_localize("America/Los_Angeles").utcoffset().total_seconds() / 3600
    return f"{int(-off):02d}"


def fetch_month(m0: pd.Timestamp, cache: Path) -> pd.DataFrame | None:
    """Fetch one month of PRC_FUEL (all regions), keep daily first print of REGIONS_KEEP."""
    f = cache / f"prc_fuel_{m0:%Y%m}.csv"
    if f.exists():
        return pd.read_csv(f, parse_dates=["OPR_DT"])
    m1 = m0 + pd.offsets.MonthBegin(1)
    # OASIS wants the window on Pacific-day boundaries: 07Z under PDT, 08Z under PST.
    url = OASIS.format(
        s=f"{m0:%Y%m%d}", e=f"{m1:%Y%m%d}", hs=_utc_hour(m0), he=_utc_hour(m1)
    )
    for attempt in range(4):
        try:
            raw = urllib.request.urlopen(url, timeout=180).read()
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                name = z.namelist()[0]
                if name.endswith(".csv"):
                    d = pd.read_csv(
                        z.open(name), usecols=["OPR_DT", "FUEL_REGION_ID", "PRC"]
                    )
                    d = d[d.FUEL_REGION_ID.isin(REGIONS_KEEP)]
                    d = d.groupby(
                        ["OPR_DT", "FUEL_REGION_ID"], as_index=False
                    ).PRC.first()
                    d.to_csv(f, index=False)
                    time.sleep(6)
                    return pd.read_csv(f, parse_dates=["OPR_DT"])
        except Exception as exc:  # noqa: BLE001 - OASIS throttles; retry slowly
            print(f"  {m0:%Y-%m} attempt {attempt}: {exc}")
        time.sleep(15 * (attempt + 1))
    print(f"  {m0:%Y-%m}: EMPTY after retries")
    return None


def keeper_config() -> ScenarioConfig:
    """Rebuild the keeper's ScenarioConfig from its committed run_config (fields only)."""
    sc = json.loads(KEEPER_RUN_CONFIG.read_text())["scenario_config"]
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in sc.items() if k in names})


def model_delivered(cfg: ScenarioConfig, years: list[int]) -> pd.Series:
    """Daily delivered CA gas the keeper's gas units see (hub overlay + transport adder)."""
    out = []
    for y in years:
        h = hubs._caiso_hub_daily_gas_prices(
            cfg,
            y,
            spot_level=True,
            spot_coverage=bool(cfg.caiso_citygate_spot_coverage),
        )
        days = pd.date_range(f"{y}-01-01", periods=365, freq="D")
        days = days[~((days.month == 2) & (days.day == 29))]
        dd = h.reshape(-1, 24)[:, 0] if h is not None else np.full(365, np.nan)
        # non-leap model clock: map day index → calendar day skipping Feb 29
        cal = pd.date_range(f"{y}-01-01", f"{y}-12-31", freq="D")
        cal = cal[~((cal.month == 2) & (cal.day == 29))]
        out.append(pd.Series(dd[: len(cal)], index=cal))
    return pd.concat(out) + CAISO_CITYGATE_TRANSPORT_ADDER


def flow_dated_prints() -> pd.DataFrame:
    """EIA weekly-narrative PG&E / SoCal citygate prints placed on their flow day (trade + 1)."""
    w = pd.read_csv(
        GAS_PRICES_DIR / "pge_socal_citygate_weekly.csv", parse_dates=["date"]
    )
    w["date"] = w["date"] + pd.Timedelta(days=1)
    return w.set_index("date").rename(
        columns={"pge_citygate_usd_mmbtu": "PGE", "socal_citygate_usd_mmbtu": "SOCAL"}
    )


def composite_flow() -> pd.Series:
    """NGI CA composite on its flow day, forward-filled (the caiso_citygate_flow_date placement)."""
    c = pd.read_csv(GAS_PRICES_DIR / "caiso_citygate_daily.csv", parse_dates=["date"])
    s = c.set_index("date").ca_composite_usd_mmbtu
    s.index = s.index + pd.Timedelta(days=1)
    return s.reindex(
        pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=3))
    ).ffill()


def main() -> None:
    """Fetch, decompose and write ``decomp.json`` + daily CSV to ``--out``."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--start", required=True, help="YYYY-MM")
    ap.add_argument("--end", required=True, help="YYYY-MM")
    a = ap.parse_args()
    cache = a.out / "oasis"
    cache.mkdir(parents=True, exist_ok=True)
    months = pd.date_range(a.start + "-01", a.end + "-01", freq="MS")
    frames = [f for m in months if (f := fetch_month(m, cache)) is not None]
    prc = pd.concat(frames).pivot_table(
        index="OPR_DT", columns="FUEL_REGION_ID", values="PRC"
    )
    got = sorted({f"{d:%Y-%m}" for d in prc.index})
    missing = [f"{m:%Y-%m}" for m in months if f"{m:%Y-%m}" not in got]

    years = sorted({d.year for d in prc.index})
    model = model_delivered(keeper_config(), years).reindex(prc.index)
    comp = composite_flow().reindex(prc.index)
    prints = flow_dated_prints().reindex(prc.index)

    rows = {}
    daily = pd.DataFrame(
        {
            "model": model,
            "composite": comp,
            "PGE_print": prints.PGE,
            "SOCAL_print": prints.SOCAL,
        }
    )
    for fam, regs in PAIRS.items():
        idx_print = prints[fam]
        for r in regs:
            if r not in prc or r + "GHG" not in prc:
                continue
            nonghg, ghg = prc[r], prc[r + "GHG"]
            daily[r] = nonghg
            daily[r + "GHG"] = ghg
            for y in years:
                sel = prc.index.year == y
                if not sel.any():
                    continue
                t_ghg = (ghg - idx_print)[sel].dropna()
                ct = (nonghg - ghg)[sel].dropna()
                total = (nonghg - model)[sel].dropna()
                total_ghg = (ghg - model)[sel].dropna()
                basis = (idx_print - comp)[sel].dropna()
                rows[f"{r}|{y}"] = {
                    "days": int(total.size),
                    "print_days": int(t_ghg.size),
                    "total_nonGHG_minus_model_med": round(float(total.median()), 3),
                    "total_GHG_minus_model_med": round(float(total_ghg.median()), 3),
                    "ldc_cnt_charge_med": round(float(ct.median()), 3),
                    "transport_ghg_med": round(float(t_ghg.median()), 3)
                    if t_ghg.size
                    else None,
                    "transport_ghg_iqr": [
                        round(float(t_ghg.quantile(q)), 3) for q in (0.25, 0.75)
                    ]
                    if t_ghg.size
                    else None,
                    "hub_basis_vs_composite_med": round(float(basis.median()), 3)
                    if basis.size
                    else None,
                }
    report = {
        "window": [a.start, a.end],
        "months_missing": missing,
        "transport_adder_model": CAISO_CITYGATE_TRANSPORT_ADDER,
        "model_minus_composite_med_by_year": {
            str(y): round(float((model - comp)[prc.index.year == y].median()), 3)
            for y in years
        },
        "rows": rows,
    }
    daily.to_csv(a.out / "decomp_daily.csv")
    (a.out / "decomp.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
