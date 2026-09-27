"""R-CAISO-6 Object 1 phase 0 (ZERO LP): which import CORRIDOR carries the midday excess?

The keeper's committed sidecars carry imports as ONE aggregate class; the
per-unit dispatch never reached ``main``. Per-tranche reconstruction from LP
duals works exactly for the economic tranches (validated on the 2019 leg's
committed dispatch: midC / DSW_CCGT / DSW_CT show 0 hours violating
complementary slackness) but cannot split the DSW clean-depth tranches, which
are priced AT the raw hub and tie with the hub dual. The PNW hub has no tied
tranches (firm block floored at its shaped capability + economic midC), so its
delivery IS identified; the DSW corridor's net is the aggregate minus PNW.

Compared per corridor, h8-16 / h18-23 means, with the measured EIA-930 corridor
net import (``derive_caiso_import_tranches.corridor_net_import``, model clock).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso6_corridor_split.py
"""

import contextlib
import io
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]
from scripts.data.derive_caiso_import_tranches import corridor_net_import


class m:  # keeper recipe fleet_only rebuild (replay_keeper.run_year_kwargs)
    BUNDLE = Path("results/calibration/rcaiso5_XE_span")

    @staticmethod
    def _rebuild(year):
        """Return the keeper recipe's fleet_only state for ``year``."""
        from replay_keeper import derived_run_year_inputs, run_year_kwargs
        from run_calibration import run_year
        from scripts.lib.bundle_fleet import clear_fleet_caches

        meta = json.load(open(m.BUNDLE / "meta.json"))
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(str(m.BUNDLE), year))
        clear_fleet_caches()
        with contextlib.redirect_stderr(io.StringIO()):
            return run_year(
                year,
                meta["iso"],
                8760,
                float(meta["gas_prices"][str(year)]),
                {},
                fleet_only=True,
                **kw,
            )


meas = corridor_net_import(years=(2022, 2023, 2024, 2025))
out = {}
for y in (2022, 2023, 2024, 2025):
    st = m._rebuild(y)
    fa = st["fleet_arrays"]
    zones = list(st["iso_config"].zone_names)
    zn = np.array([zones[i] for i in fa.zone_idx])
    ids = np.asarray(fa.unit_ids)
    mc = np.asarray(st["mc_base"], float)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    mg = np.asarray(fa.min_gen, float)
    lam = pd.read_parquet(m.BUNDLE / f"hourly/system_{y}.parquet").pivot(
        index="hour", columns="zone", values="price"
    )
    ch = pd.read_parquet(m.BUNDLE / f"hourly/class_hourly_{y}.parquet")
    agg = ch[ch.klass == "import"].set_index("hour").mw.reindex(range(8760)).to_numpy()
    pnw = np.zeros(8760)
    ties = 0
    for n in ("WECC_PNW_PNW_hydro_base", "WECC_PNW_PNW_midC"):
        i = int(np.flatnonzero(ids == n)[0])
        l = lam["WECC_PNW"].to_numpy()[:8760]
        c = cap[i]
        f = np.minimum(mg[i] if mg.ndim == 2 else np.full(8760, mg[i]), c)
        d = np.where(mc[i] < l - 0.05, c, f)
        tie = np.abs(mc[i] - l) <= 0.05
        ties += tie.sum()
        d = np.where(tie, (c + f) / 2, d)
        pnw += d
    dsw = agg - pnw
    M = meas.loc[y] if y in meas.index.get_level_values(0) else None
    hod = np.arange(8760) % 24
    mid = (hod >= 8) & (hod <= 16)
    eve = (hod >= 18) & (hod <= 23)
    r = {"ties_pnw_hours": int(ties)}
    for nm, arr in (("model_PNW", pnw), ("model_DSW_net", dsw), ("model_total", agg)):
        r[nm] = {
            "mid": round(float(np.nanmean(arr[mid]))),
            "eve": round(float(np.nanmean(arr[eve]))),
        }
    Mv = M.reindex(range(8760))
    for col in Mv.columns:
        a = Mv[col].to_numpy(float)
        r["930_" + str(col)] = {
            "mid": round(float(np.nanmean(a[mid]))),
            "eve": round(float(np.nanmean(a[eve]))),
        }
    out[y] = r
    print(y, json.dumps(r), flush=True)
json.dump(
    out, open("results/calibration/_rcaiso6/corridor_mid_eve.json", "w"), indent=1
)
