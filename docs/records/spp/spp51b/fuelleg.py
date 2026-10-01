"""SPP-51b phase 0.2 (ZERO LP): is the level residual a FUEL-BASIS error (rule 14,
zero DOF) or a merit/heat-rate error?

Decomposes the mid-load over-pricing into its two multiplicative parts.  A model
price is ``HR_marginal x fuel_marginal + vom``; the measured price over the same
hours implies a market heat rate against SPP's own delivered gas.  So the residual
can be attributed to (a) the fuel the marginal unit is charged, or (b) which unit is
marginal at all.  These are different lanes: (a) is a rule-14 input repair, (b) is a
merit-order object no offer-curve band reaches.

Also reports the model's per-class marginal fuel price against the state delivered
reference, which is the test SPP-49 R-5 (the Waha / TX-blend boundary question) asks
for -- i.e. whether the surviving in-band prices are themselves too high.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).parent))

OUT = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "e7ea1db8-8d13-5aa9-9561-fc9c88bbd737/scratchpad/spp51b"
)
YEARS = (2023, 2024, 2025)
TOL = 0.25
MCF_TO_MMBTU = 1.036
GAS_REF = (
    REPO
    / "data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv"
)


def state_gas(year: int, states=("KS", "OK")) -> float:
    df = pd.read_csv(GAS_REF)
    sub = df[(df["state"].isin(states)) & (df["year"] == year)]
    return float(sub["price_usd_mcf"].mean()) / MCF_TO_MMBTU


def main() -> None:
    from prices import model_price, actual_rt

    print(f"gas reference: {GAS_REF.name}")
    for year in YEARS:
        a = np.load(OUT / f"head_arrays_{year}.npz")
        rows = pd.read_csv(OUT / f"head_rows_{year}.csv")
        mc, av, pmax = a["mc_base"], a["availability"], a["pmax"]
        hr, fuel, vom = a["heat_rate"], a["fuel_prices"], a["vom"]
        dem = a["demand"]
        T = mc.shape[1]
        price = model_price("2026-09-08-spp-50-rebaseline", year)[:T]
        act = actual_rt(year)[:T]
        load = (dem.sum(axis=0) if dem.ndim == 2 else dem)[:T]
        availmw = pmax[:, None] * (av if av.ndim == 2 else av[None, :])
        grp = rows["plant_group"].fillna("").to_numpy()
        grp = np.where(grp == "", rows["fuel_type"].astype(str).to_numpy(), grp)
        isgas = np.array([g.startswith(("CC", "CT", "ST_GAS")) for g in grp])
        iscoal = np.array([g.startswith("COAL") for g in grp])

        ok = np.isfinite(price) & np.isfinite(act) & np.isfinite(load)
        pct = np.full(T, np.nan)
        pct[ok] = pd.Series(load[ok]).rank(pct=True).to_numpy() * 100.0
        mid = ok & (pct >= 25) & (pct < 75)
        top = ok & (pct >= 95)
        gref = state_gas(year)

        print(f"\n================  {year}  ================")
        print(
            f"SPP KS/OK delivered gas to electric power (EIA N3045, /1.036): "
            f"${gref:.3f}/MMBtu"
        )
        for label, sel in (("MID 25-75", mid), ("TOP >=95", top)):
            idx = np.where(sel)[0]
            near = np.abs(mc[:, idx] - price[idx][None, :]) <= TOL
            w = near * availmw[:, idx]
            tot = w.sum()
            mp = float(np.average(price[idx], weights=load[idx]))
            ap = float(np.average(act[idx], weights=load[idx]))
            rw = w.sum(axis=1)
            hrw = float(np.average(hr, weights=rw))
            fw = float((w * fuel[:, idx]).sum() / tot)
            vw = float(np.average(vom, weights=rw))
            fg = float(
                (w[isgas] * fuel[isgas][:, idx]).sum() / max(w[isgas].sum(), 1e-9)
            )
            hg = (
                float(np.average(hr[isgas], weights=rw[isgas]))
                if rw[isgas].sum()
                else np.nan
            )
            fc = float(
                (w[iscoal] * fuel[iscoal][:, idx]).sum() / max(w[iscoal].sum(), 1e-9)
            )
            hc = (
                float(np.average(hr[iscoal], weights=rw[iscoal]))
                if rw[iscoal].sum()
                else np.nan
            )
            # what each single lever would have to do, alone, to close the gap
            fuel_only = (ap - vw) / max(hrw * fw, 1e-9)
            hr_only = (ap - vw) / max(fw, 1e-9)
            print(
                f"\n  [{label}]  model ${mp:.2f}  actual ${ap:.2f}  err {100 * (mp / ap - 1):+.1f}%"
            )
            print(
                f"    marginal mix: HR {hrw:.3f}  fuel ${fw:.3f}  vom ${vw:.2f}"
                f"   -> HR*fuel+vom = ${hrw * fw + vw:.2f}"
            )
            print(
                f"      gas rows : HR {hg:.3f}  fuel ${fg:.3f}   "
                f"(vs state ref ${gref:.3f}: {100 * (fg / gref - 1):+.1f}%)"
            )
            print(f"      coal rows: HR {hc:.3f}  fuel ${fc:.3f}")
            print(
                f"    market HR implied by ACTUAL price over state gas: "
                f"{ap / gref:.3f}   (model marginal physical HR {hrw:.3f})"
            )
            print("    TO CLOSE THE GAP WITH ONE LEVER ALONE:")
            print(
                f"      fuel   x {fuel_only:.4f}  -> marginal fuel ${fw * fuel_only:.3f}/MMBtu"
                f"   (gas rows would go to ${fg * fuel_only:.3f} vs ref ${gref:.3f})"
            )
            print(
                f"      HR     -> {hr_only:.3f} MMBtu/MWh (from {hrw:.3f}, "
                f"{100 * (hr_only / hrw - 1):+.1f}%)"
            )


if __name__ == "__main__":
    main()
