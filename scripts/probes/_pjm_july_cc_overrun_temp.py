"""Cross the pjm-107 July CC over-run against plant-local temperature.

Owner question #1 of the 2026-07-14 July-gas diagnosis
(``docs/DIAGNOSIS-pjm-july-cc-overrun-2026-07.md``): on the days/hours the
named CC_REGULAR plants over-run (model MW >> actual), how hot was it at the
plants' locations? The temp-derate lever is justified only if the over-run
days are genuinely hot at the CC crossover (>= ~33-35 degC).

Method — everything is measured, nothing is re-solved:

* MODEL side: the committed pjm-107 dashboard payload
  (``frontend/data/backcast/runs/2026-07-14-pjm-107-gas-daily.js``) carries
  each plant's hourly LP dispatch as a base64 byte array of CF-percent vs
  nameplate (the ``dec()`` decoder in ``backcast-runs.html``). This is the
  keeper's exact P1 dispatch, byte-derived from the (gitignored) dispatch
  parquets at render time.
* ACTUAL side: CAMPD unit-level hourly gross load (the same benchmark array
  committed in ``frontend/data/backcast/bench/PJM/<year>.json.gz``).
* TEMPERATURE: the model's own zone TMAX series (``eia_loader.iso_zone_tmax``)
  — the exact input ``temp_dependent_derate`` / ``gt_ambient_derate`` consume.

Outputs, per July 2023/2024/2025: the named-plant model-vs-actual CF table,
daily over-run crossed against TMAX bins (share of over-run MWh per bin +
day-level correlation), the hour-of-day share of the over-run (a hot-afternoon
derate cannot act overnight), and the >=33 degC capability lower bound
(max observed gross / net-summer — the pjm-95 rule-24 test on these units).

Result (2026-07-14): corr(TMAX, over-run) = -0.14/-0.09/-0.09; >=33 degC days
carry 7-20 % of over-run MWh; 30-50 % accrues in hours 0-6; capability at
rating demonstrated on the hot hours. Temperature confirmation FAILS — the
over-run is a mild-day/overnight cycling + allocation residual, not a missing
ambient derate. Diagnostic only — no LP, no solve. Usage:
    python scripts/probes/_pjm_july_cc_overrun_temp.py [YEAR ...]
"""

import base64
import gzip
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
logging.disable(logging.WARNING)

from market_sim.data.eia_loader import iso_zone_tmax  # noqa: E402

RUN_JS = (
    REPO / "frontend" / "data" / "backcast" / "runs" / "2026-07-14-pjm-107-gas-daily.js"
)
BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench" / "PJM"

# The 12 named plants of the finding (EIA plant id == ORISPL, repo convention)
# with the model's own zone assignment (fleet.load_fleet_from_csv("PJM")).
PLANTS: dict[int, tuple[str, str]] = {
    62949: ("Guernsey", "PJM_AEP_Ohio"),
    59913: ("Greensville", "PJM_Dominion"),
    55524: ("York Energy", "PJM_Central_PA"),
    55736: ("Hanging Rock", "PJM_AEP_Ohio"),
    60356: ("South Field", "PJM_AEP_Ohio"),
    58260: ("Brunswick Co", "PJM_Dominion"),
    55939: ("Warren Co", "PJM_Dominion"),
    55502: ("Lawrenceburg", "PJM_AEP_Ohio"),
    55297: ("New Covert", "PJM_AEP_Ohio"),
    62926: ("Jackson Gen", "PJM_ComEd"),
    63931: ("CPV Three Rivers", "PJM_ComEd"),
    60368: ("Hummel", "PJM_Central_PA"),
}
TBINS = [(-99, 28), (28, 31), (31, 33), (33, 35), (35, 99)]


def _dec(b64: str) -> np.ndarray:
    """Decode a payload/bench base64 byte array (CF percent, 0-255)."""
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _load_run() -> dict:
    """Return the pjm-107 payload dict from the committed dashboard JS."""
    blob = re.search(r'="([^"]+)"', RUN_JS.read_text()).group(1)
    return json.loads(gzip.decompress(base64.b64decode(blob)))


def main(years: list[int]) -> None:
    """Print the July over-run x TMAX cross for each requested year."""
    run = _load_run()
    for year in years:
        bench = json.loads(
            gzip.decompress((BENCH_DIR / f"{year}.json.gz").read_bytes())
        )
        bp = bench["bench"]["plants"]
        mp = run["years"][str(year)]["plants"]
        jul = pd.date_range(
            f"{year}-07-01", f"{year}-08-01", freq="h", inclusive="left"
        )
        jidx = (
            ((jul - pd.Timestamp(f"{year}-01-01")).total_seconds() // 3600)
            .astype(int)
            .to_numpy()
        )
        tmax = {
            z: np.asarray(iso_zone_tmax("PJM", year, 8760, zone=z)[0], dtype=float)
            for z in {z for _, z in PLANTS.values()}
        }

        rows, daily = [], []
        for pid, (name, zone) in PLANTS.items():
            k = str(pid)
            if k not in mp or k not in bp:
                print(f"   ({year}: {name} absent from payload/bench — skipped)")
                continue
            npl = bp[k].get("npl", 1.0)
            m = _dec(mp[k]["m"])[jidx] * npl / 100.0  # model MW
            c = _dec(bp[k]["campd"])[jidx] * npl / 100.0  # CAMPD gross MW
            t = tmax[zone][jidx]
            d = pd.DataFrame({"m": m, "c": c, "T": t, "day": jul.day, "hod": jul.hour})
            d["over"] = (d["m"] - d["c"]).clip(lower=0)
            hb = d.groupby("hod")["over"].sum()
            rows.append(
                {
                    "name": name,
                    "cf_m": m.mean() / npl,
                    "cf_c": c.mean() / npl,
                    "over_gwh": d["over"].sum() / 1e3,
                    "night_share": hb.loc[0:6].sum() / hb.sum() if hb.sum() else np.nan,
                    # capability lower bound on the hot hours themselves
                    "hot33_max_r": (
                        (d.loc[d["T"] >= 33, "c"].max() / npl)
                        if (d["T"] >= 33).any()
                        else np.nan
                    ),
                }
            )
            dd = d.groupby("day").agg(over=("over", "sum"), tmax=("T", "max"))
            daily.append(dd)

        per = pd.DataFrame(rows)
        dall = pd.concat(daily)
        tot = dall["over"].sum()
        share = {
            f"{lo}-{hi}": dall.loc[
                (dall["tmax"] >= lo) & (dall["tmax"] < hi), "over"
            ].sum()
            / tot
            for lo, hi in TBINS
        }
        corr = float(np.corrcoef(dall["tmax"], dall["over"])[0, 1])
        print(f"== {year} July (exact pjm-107 dispatch vs CAMPD gross) ==")
        print(per.round(3).to_string(index=False))
        print(
            f"   named-12 over-run {per['over_gwh'].sum():.0f} GWh | "
            f"corr(TMAX, daily over-run) = {corr:+.2f}"
        )
        print(
            "   over-run share by TMAX degC: "
            + ", ".join(f"{k}: {v:.1%}" for k, v in share.items())
        )


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [2023, 2024, 2025])
