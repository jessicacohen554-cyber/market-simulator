"""Diagnostic: CAISO per-hub import decomposed by tranche and hour-of-day.

For a solved per-hub bundle, show the average 24-hour profile of:
  * net interchange (model vs EIA-930 actual),
  * each import tranche's imported MW (which tranche fills the midday over-import),
  * the measured MALIN / PALOVRDE hub prices,
so we can confirm the diurnal residual is the flat cheap-hub stack flooding
midday, not the genuinely-cheap surplus block alone.

Usage: python scripts/probes/_caiso_diurnal_import_decomp.py <bundle_dir> <year>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.eia_loader import (  # noqa: E402
    load_eia_hourly_benchmark,
    measured_import_hub_prices,
)


def main() -> None:
    bundle = Path(sys.argv[1])
    year = int(sys.argv[2])
    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    imp = disp[disp["fuel"] == "import"].copy()
    imp["hod"] = imp["hour"] % 24

    # Net interchange (model): -(sum of import-fuel mw) per hour. Import tranches
    # are +mw, export legs are -mw, so the negation gives EIA sign (+ = export).
    by_hour = imp.groupby("hour", observed=True)["mw"].sum()
    model_ix = -by_hour.sort_index().to_numpy(float)  # + = net export
    n = model_ix.shape[0] - model_ix.shape[0] % 24
    d24m_imp = -model_ix[:n].reshape(-1, 24).mean(axis=0)  # + = net import (GW below)

    bench = load_eia_hourly_benchmark("CAISO", year)
    ix = np.asarray(bench["interchange"], dtype=float)  # + = net export
    na = ix.shape[0] - ix.shape[0] % 24
    d24a_imp = -ix[:na].reshape(-1, 24).mean(axis=0)  # + = net import

    corr = float(np.corrcoef(d24m_imp, d24a_imp)[0, 1])
    print(f"\n=== CAISO {year} diurnal import decomposition ===")
    print(f"net-import diurnal corr (model vs actual): {corr:+.3f}")
    print(
        f"model net interchange: {model_ix.sum() / 1e6:+.2f} TWh   "
        f"actual: {ix.sum() / 1e6:+.2f} TWh"
    )

    # Per-tranche imported MW by hour-of-day.
    piv = imp.groupby(["unit_id", "hod"], observed=True)["mw"].mean().unstack("hod")
    hubs = measured_import_hub_prices("CAISO", year, disp["hour"].max() + 1)
    malin = (
        np.asarray(hubs["PNW_hydro_base"])[:n].reshape(-1, 24).mean(axis=0)
        if hubs and "PNW_hydro_base" in hubs
        else None
    )
    palo = (
        np.asarray(hubs["DSW_solar_PV"])[:n].reshape(-1, 24).mean(axis=0)
        if hubs and "DSW_solar_PV" in hubs
        else None
    )

    blocks = [0, 3, 6, 9, 12, 15, 18, 21]
    hdr = "  hour          " + "".join(f"h{h:02d}   " for h in blocks)
    print("\n  net import (GW), model vs actual:")
    print(hdr)
    print("  model         " + "".join(f"{d24m_imp[h] / 1000:5.1f} " for h in blocks))
    print("  actual        " + "".join(f"{d24a_imp[h] / 1000:5.1f} " for h in blocks))
    if malin is not None:
        print("\n  measured hub price ($/MWh):")
        print("  MALIN(PNW)    " + "".join(f"{malin[h]:5.0f} " for h in blocks))
        print("  PALOVRDE(DSW) " + "".join(f"{palo[h]:5.0f} " for h in blocks))
    print("\n  imported MW by tranche (mean by hour-of-day):")
    print(hdr)
    for uid in piv.index:
        row = piv.loc[uid]
        print(f"  {uid:22s}" + "".join(f"{row.get(h, 0) / 1000:5.1f} " for h in blocks))

    # In-state midday marginal price proxy: mean LMP across in-state trading
    # zones (NP15/SP15/ZP26) by hour-of-day, from the dispatch lmp column.
    ins = disp[disp["zone"].isin(["NP15", "SP15", "ZP26"])].copy()
    if len(ins):
        zp = ins.groupby(["zone", "hour"], observed=True)["lmp"].mean().reset_index()
        zp["hod"] = zp["hour"] % 24
        wp = zp.groupby("hod", observed=True)["lmp"].mean()
        print("\n  model in-state LMP (mean of NP15/SP15/ZP26) by hour-of-day:")
        print(
            "  price         "
            + "".join(f"{wp.get(h, float('nan')):5.0f} " for h in blocks)
        )


if __name__ == "__main__":
    main()
