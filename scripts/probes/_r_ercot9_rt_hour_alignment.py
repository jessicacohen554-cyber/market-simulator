"""R-ERCOT-9 phase 0: hour-alignment audit of the ERCOT actual RT LZ series (zero LP).

For each year, correlates the scorer's actual load-zone RT series (the committed
``actual_lmp_zonal_ERCOT.parquet``, via ``derive_actual_lmp``) against (i) the
measured NP6-905 SCED system lambda (``ercot_<y>_ordc_reserves_hourly``) and
(ii) the keeper's P1 price, at hour shifts -2..+2. Prices clipped at $5,000.

Usage: ``python3 scripts/probes/_r_ercot9_rt_hour_alignment.py``.
Record: ``docs/handoffs/FINDING-r-ercot-9-2023-scarcity-2026-09-27.md``.
"""

import sys
from pathlib import Path

sys.path[:0] = [".", "src", "scripts"]
import numpy as np
import pandas as pd
import scripts.data.derive_actual_lmp as D

B = "results/calibration/r_ercot8_fusco_span/hourly"
zp = pd.read_parquet(D.HOURLY_OUT / D.ERCOT_ZONAL_PARQUET)


def series(z, sp):
    d = np.full(8784, np.nan)
    g = z[z.settlement_point == sp]
    hr = g.hour.to_numpy(int)
    d[hr[hr < 8784]] = g.rt.to_numpy(float)[hr < 8784]
    return d


def corr(x, y, s):
    n = min(len(x), len(y))
    x, y = x[:n], y[:n]
    if s > 0:
        x, y = x[s:], y[:-s]
    elif s < 0:
        x, y = x[:s], y[-s:]
    m = ~(np.isnan(x) | np.isnan(y))
    return np.corrcoef(np.clip(x[m], -250, 5000), np.clip(y[m], -250, 5000))[0, 1]


for y in range(2019, 2026):
    z = zp[zp.year == y]
    hub = series(z, "HB_HOUSTON") if "HB_HOUSTON" in set(z.settlement_point) else None
    lz = series(z, "LZ_HOUSTON")
    s = pd.read_parquet(f"{B}/system_{y}.parquet")
    s = s[(s["pass"] == "P1") & (s.zone == "Houston")].sort_values("hour")
    m = s.price.to_numpy(float)
    f = Path(f"data/raw/ercot/ercot_{y}_ordc_reserves_hourly.parquet")
    lam = None
    if f.exists():
        o = pd.read_parquet(f).sort_values("hour")
        lam = np.full(8784, np.nan)
        lam[o.hour.to_numpy(int)] = o.system_lambda.to_numpy(float)
    row = [f"{y}:"]
    for sh in (-1, 0, 1):
        r = f" s{sh:+d} act~model {corr(lz, m, sh):.3f}"
        if lam is not None:
            r += f" act~lam {corr(lz, lam, sh):.3f}"
        row.append(r)
    if lam is not None:
        row.append(f" | model~lam s0 {corr(lam, m, 0):.3f}")
    print(" ".join(row))
