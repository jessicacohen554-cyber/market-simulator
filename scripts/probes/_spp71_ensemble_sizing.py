"""SPP-71 (card R-bc) — size the ENSEMBLE COAL SYNCHRONIZATION FLOOR at ZERO LP.

The candidate replaces the coal synchronization floor's PLACEMENT rule — today a
top-k window by system load (``fleet/arrays.py``, the ``coal_sync_any`` block) —
with the continuous-relaxation image of the same measured commitment:

    floor_p(t) = coal_sync_pmin_mw_p x online_frac_p      (every hour)

instead of

    floor_p(t) = coal_sync_pmin_mw_p  on the top round(frac x 8760) hours by
                 system load, and 0 in every other hour.

Both spend the SAME measured annual synchronized MWh; only the placement moves.
Neither adds a parameter: both read ``mustrun_online_pct`` and ``online_frac``
from ``data/raw/_processed-legacy/thermal_tranches_SPP.csv``.

This script sizes the four R-bc success conditions from keeper 14's COMMITTED
hourly sidecars, so the predictions can be pre-registered before any shard runs.
It is an AGGREGATE estimate: it applies the fleet-total floor to the fleet-total
coal dispatch, where the LP applies a per-plant floor clipped to that plant's
``pmax x availability``.  The per-plant clip can only REDUCE the applied floor,
so every displacement number here is an UPPER bound.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.probes._spp71_phase0 import (  # noqa: E402
    BUNDLES,
    COAL_CLASSES,
    GAS_CLASSES,
    CHP_CLASSES,
    WIND_OFFER,
    _bundle_hourly,
)

TRANCHES = REPO / "data" / "raw" / "_processed-legacy" / "thermal_tranches_SPP.csv"


def ensemble_floor_mw() -> tuple[float, float, pd.DataFrame]:
    """Fleet ensemble floor sum(pmin x frac) and the top-k full level sum(pmin)."""
    df = pd.read_csv(TRANCHES)
    coal = df[df["plant_group"].astype(str).str.upper().str.startswith("COAL")].copy()
    coal["pmin_mw"] = (
        coal["nameplate_mw"] * coal["mustrun_online_pct"].fillna(0.0) / 100.0
    )
    coal["frac"] = coal["online_frac"].fillna(0.0)
    return (
        float((coal["pmin_mw"] * coal["frac"]).sum()),
        float(coal["pmin_mw"].sum()),
        coal,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=sorted(BUNDLES))
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    ens, full, coal_tbl = ensemble_floor_mw()
    print(
        f"ENSEMBLE floor  sum(pmin x online_frac) = {ens:9.1f} MW   ({len(coal_tbl)} COAL plants)"
    )
    print(f"FULL     level  sum(pmin)               = {full:9.1f} MW")
    print(
        f"current bottom-hour floor sum(pmin | frac>=0.99) = {float(coal_tbl.loc[coal_tbl['frac'] >= 0.99, 'pmin_mw'].sum()):.1f} MW\n"
    )

    out = []
    for y in args.years:
        ch = _bundle_hourly(y, "class_hourly")
        ch = ch[ch["pass"] == "P1"]
        piv = ch.pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
        ).fillna(0.0)

        def col(*names: str) -> np.ndarray:
            o = np.zeros(len(piv))
            for n in names:
                if n in piv.columns:
                    o += piv[n].to_numpy(dtype=float)
            return o

        coal = col(*COAL_CLASSES)
        gas = col(*GAS_CLASSES)
        chp = col(*CHP_CLASSES)
        wind = col("wind")

        sysdf = _bundle_hourly(y, "system")
        sysdf = sysdf[sysdf["pass"] == "P1"]
        pz = sysdf.pivot_table(
            index="hour", columns="zone", values="price", observed=True
        )
        zone_min = pz.min(axis=1).to_numpy(dtype=float)
        hub = pz.mean(axis=1).to_numpy(dtype=float)

        # Where the ensemble floor BITES: hours the LP put coal below it.
        bite = np.maximum(0.0, ens - coal)
        bite_h = int(np.sum(bite > 1e-6))
        added_twh = float(bite.sum() / 1e6)

        # What absorbs it: gas first (down to zero), then wind.
        gas_absorbed = np.minimum(bite, gas)
        wind_displaced = np.maximum(0.0, bite - gas)
        # Hours that would NEWLY have wind on the margin: the floor exhausts the
        # gas buffer AND the hour is not already at the wind offer.
        already = np.isclose(zone_min, WIND_OFFER, atol=1e-6)
        new_offer = int(np.sum((wind_displaced > 1e-6) & (~already)))

        out.append(
            {
                "year": y,
                "ensemble_floor_mw": ens,
                "bite_hours": bite_h,
                "bite_share": bite_h / len(piv),
                "coal_added_twh_upper": added_twh,
                "gas_displaced_twh_upper": float(gas_absorbed.sum() / 1e6),
                "wind_displaced_twh_upper": float(wind_displaced.sum() / 1e6),
                "model_wind_twh": float(wind.sum() / 1e6),
                "hours_at_offer_now": int(already.sum()),
                "hours_at_offer_new_upper": new_offer,
                "hours_at_offer_projected": int(already.sum()) + new_offer,
                "hub_neg_hours_now": int(np.sum(hub < 0.0)),
                "mean_bite_mw": float(bite[bite > 1e-6].mean()) if bite_h else 0.0,
                "mean_gas_in_bite_mw": float(gas[bite > 1e-6].mean())
                if bite_h
                else 0.0,
                "mean_chp_in_bite_mw": float(chp[bite > 1e-6].mean())
                if bite_h
                else 0.0,
            }
        )

    print(
        f"{'yr':>5} {'bite h':>7} {'bite%':>6} {'mean bite':>10} {'gas in bite':>12} | {'coal+TWh':>9} {'gas-TWh':>8} {'wind-TWh':>9} | {'@offer now':>11} {'new':>6} {'proj':>6}"
    )
    for r in out:
        print(
            f"{r['year']:>5} {r['bite_hours']:>7d} {r['bite_share']:>6.3f} {r['mean_bite_mw']:>10.1f} "
            f"{r['mean_gas_in_bite_mw']:>12.1f} | {r['coal_added_twh_upper']:>9.3f} "
            f"{r['gas_displaced_twh_upper']:>8.3f} {r['wind_displaced_twh_upper']:>9.3f} | "
            f"{r['hours_at_offer_now']:>11d} {r['hours_at_offer_new_upper']:>6d} {r['hours_at_offer_projected']:>6d}"
        )

    if args.json_out:
        args.json_out.write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
