"""R-CAISO-25 probe (zero LP): CAISO's own published gas price vs the model's delivered gas.

Fetches CAISO OASIS ``PRC_FUEL`` (the per-fuel-region daily gas price CAISO uses for
cost-based bids; public) for chosen regions and windows, and compares it with the
keeper's delivered CA gas: the NGI CA Composite print placed on its FLOW day (trade + 1,
weekend packages forward-filled, ``caiso_citygate_flow_date``) plus
``CAISO_CITYGATE_TRANSPORT_ADDER``. Scoping evidence only; nothing here feeds a solve.

Usage::

    python3 scripts/probes/_rcaiso25_prc_fuel.py --out <scratch dir> \
        --start 2024-01-01 --end 2024-12-31 --regions FRPGE2 FRSCE2 FRSDG2
"""

from __future__ import annotations

import argparse
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from market_sim.config.constants import CAISO_CITYGATE_TRANSPORT_ADDER
from market_sim.config.paths import GAS_PRICES_DIR

OASIS = (
    "https://oasis.caiso.com/oasisapi/SingleZip?queryname=PRC_FUEL&fuel_region_id={reg}"
    "&startdatetime={s}T08:00-0000&enddatetime={e}T08:00-0000&version=1&resultformat=6"
)


def fetch_prc_fuel(region: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Return the daily PRC_FUEL price ($/MMBtu) for one fuel region, month by month."""
    out = []
    for m0 in pd.date_range(start.to_period("M").start_time, end, freq="MS"):
        m1 = m0 + pd.offsets.MonthBegin(1)
        url = OASIS.format(reg=region, s=m0.strftime("%Y%m%d"), e=m1.strftime("%Y%m%d"))
        raw = urllib.request.urlopen(url, timeout=120).read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            name = z.namelist()[0]
            if name.endswith(".csv"):
                out.append(pd.read_csv(z.open(name)))
        time.sleep(5)  # OASIS rate limit
    d = pd.concat(out)
    s = d.groupby("OPR_DT").PRC.first()
    s.index = pd.to_datetime(s.index)
    return s.loc[start:end]


def model_delivered(start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Return the keeper's delivered CA gas: flow-dated composite + transport adder."""
    c = pd.read_csv(GAS_PRICES_DIR / "caiso_citygate_daily.csv", parse_dates=["date"])
    s = c.set_index("date").ca_composite_usd_mmbtu
    s.index = s.index + pd.Timedelta(days=1)
    s = s.reindex(pd.date_range(s.index.min(), end)).ffill()
    return (s + CAISO_CITYGATE_TRANSPORT_ADDER).loc[start:end]


def main() -> None:
    """Fetch, compare and write ``prc_fuel_vs_model.json`` to ``--out``."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--regions", nargs="+", default=["FRPGE2", "FRSCE2", "FRSDG2"])
    a = ap.parse_args()
    start, end = pd.Timestamp(a.start), pd.Timestamp(a.end)
    frame = pd.DataFrame({r: fetch_prc_fuel(r, start, end) for r in a.regions})
    frame["model"] = model_delivered(start, end)
    frame = frame.dropna()
    diff = frame[a.regions].sub(frame.model, axis=0)
    report = {
        "window": [a.start, a.end],
        "days": len(frame),
        "corr_with_model": frame.corr()["model"].round(3).to_dict(),
        "region_minus_model": diff.describe().round(2).to_dict(),
    }
    a.out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(a.out / "prc_fuel_vs_model.csv")
    (a.out / "prc_fuel_vs_model.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
