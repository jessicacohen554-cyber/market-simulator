"""ERCOT-68 leg J- realized-room decomposition (no LP solve — reads a bundle).

Reconstructs the v3 realized-room RTORPA inputs for a leg-J probe bundle
exactly per ``scarcity.ercot_ordc_realized_adder`` (env_all − Σ_elig P +
measured storage-AS + LR credit; offline = forward RTOFFCAP), verifies the
recomputed adder against the bundle's recorded ``ordc_adder`` column, then
decomposes the OVER-FIRE hours (model adder ≥ threshold while measured RTORPA
is quiet) into:

* the supply-mix excess: Σ_elig P_model − CAMPD on-line gross, class-resolved
  (the ERCOT-58 §4 anatomy — how much of the +2.4 GW remains post-storage-fix
  and how much is ST_GAS);
* the envelope-identification residual at those hours: measured RTOLCAP −
  (env_all − CAMPD gross + credits) — the part of the room bias the envelope
  itself owns (vs the identification gate's binding-regime score);
* month × hour-of-day incidence, model online room vs measured RTOLCAP, and
  the storage-discharge level at the same hours (the ERCOT-58 leading term).

Usage::

    python scripts/probes/_ercot68_room_decomp.py --bundle ercot68_legJ_2024 \
        --year 2024 [--adder-min 50]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from derive_ercot_rtolcap_forward import _class_hourly, _net_load  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.reserve_config import (  # noqa: E402
    QUICK_START_FUEL_TYPES,
    RESERVE_FUEL_TYPES,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    FUEL_TYPE_NAMES,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.results.scarcity import (  # noqa: E402
    ercot_load_resource_reserve_credit_mw,
    ercot_online_capacity_envelope_mw,
    ercot_rtolcap_forward_supply_cap_mw,
    ercot_storage_as_reserve_mw,
    scarcity_prices,
)

PRODUCTS = ("REGUP", "RRS", "ECRS", "NSPIN")  # validate_ercot_online_capacity.py:81

# klass values in dispatch/<year>_P1.parquet whose fuel types are
# reserve-eligible (RESERVE_FUEL_TYPES: gas_cc/gas_ct/gas_st/coal/nuclear/oil).
ELIG_KLASS_PREFIX = (
    "CC_",
    "COAL",
    "CT_",
    "ST_",
)
ELIG_KLASS_EXACT = ("nuclear", "oil")
# CAMPD-comparable envelope classes (RTOLCAP_CLASSES; nuclear has no CAMPD).
CAMPD_CLASSES = (
    "COAL",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
)

_CAL = pd.date_range("2023-01-01", periods=8760, freq="h")  # non-leap model clock


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="ercot68_legJ_2024")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--adder-min", type=float, default=50.0)
    args = ap.parse_args()
    year, hours = args.year, 8760
    bdir = REPO / "results" / "calibration" / args.bundle

    # ---- envelope (measured variant, thermavail fleet — the leg-J config) ---
    cfg = ScenarioConfig(
        iso="ERCOT",
        weather_year=year,
        mode="backcast",
        ercot_multiproduct_as_coopt=True,
        ercot_online_capacity_envelope_measured=True,
        ercot_thermal_dam_availability=True,
    )
    iso = get_iso_config("ERCOT")
    gens = load_fleet_from_csv("ERCOT", iso, year=year)
    fleet = generators_to_fleet_arrays(
        gens, [z.name for z in iso.zones], hours, iso="ERCOT", config=cfg, year=year
    )
    nl = _net_load(year)[:hours]
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet.fuel_type_idx])
    responsive = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
    quick = np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))
    fast_elig = responsive & ~quick
    headroom_eligible = np.vstack([fast_elig, responsive])
    headroom_products = np.zeros((2, len(PRODUCTS)), dtype=bool)
    headroom_products[1, :] = True
    headroom_products[0, 0] = True
    env = ercot_online_capacity_envelope_mw(
        cfg,
        fleet,
        hours,
        net_load=nl,
        headroom_eligible=headroom_eligible,
        headroom_products=headroom_products,
    )
    env_all = env[np.all(env < 1e8, axis=1)][0]

    # ---- model eligible dispatch from the bundle --------------------------
    disp = pd.read_parquet(
        bdir / "dispatch" / f"{year}_P1.parquet",
        columns=["pass", "klass", "hour", "mw"],
    )
    disp = disp[disp["pass"] == "P1"]
    elig = disp["klass"].str.startswith(ELIG_KLASS_PREFIX) | disp["klass"].isin(
        ELIG_KLASS_EXACT
    )
    P_elig = (
        disp[elig].groupby("hour")["mw"].sum().reindex(range(hours), fill_value=0.0)
    ).to_numpy()
    kl = (
        disp.groupby(["klass", "hour"], observed=True)["mw"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(columns=range(hours), fill_value=0.0)
    )

    # ---- credits, offline, lambda ------------------------------------------
    storage_as = ercot_storage_as_reserve_mw(year, hours)
    lr = ercot_load_resource_reserve_credit_mw(cfg, hours, year=year)
    online = np.clip(env_all - P_elig, 0.0, None) + storage_as + lr

    sc = ercot_rtolcap_forward_supply_cap_mw(
        cfg, fleet, hours, net_load=nl, storage_reserve=None
    )
    offline = (
        np.clip(sc[1, :hours] - sc[0, :hours], 0.0, None)
        if sc is not None and sc.shape[0] >= 2
        else np.zeros(hours)
    )

    sysq = pd.read_parquet(bdir / "system.parquet")
    sysq = sysq[(sysq["pass"] == "P1") & (sysq["year"] == year)].copy()
    for col in ("ordc_adder", "rtordpa_overlay"):
        if col not in sysq.columns:
            sysq[col] = 0.0
    sysq["lam0"] = sysq["price"] - sysq["ordc_adder"] - sysq["rtordpa_overlay"]
    lam = (
        sysq.groupby("hour")
        .apply(
            lambda g: float(
                (g["lam0"] * g["demand"]).sum() / max(g["demand"].sum(), 1e-9)
            ),
            include_groups=False,
        )
        .reindex(range(hours))
        .to_numpy()
    )
    adder_rec = (
        sysq.groupby("hour")["ordc_adder"].first().reindex(range(hours)).to_numpy()
    )

    # ---- verification -------------------------------------------------------
    adder_new = scarcity_prices(
        cfg, year, online + offline, lam, reserves_online_mw=online
    )["scarcity_adder"]
    diff = adder_new - adder_rec
    print(
        f"== reconstruction check: recomputed vs recorded adder — mean|diff| "
        f"${np.nanmean(np.abs(diff)):.2f}, hours |diff|>$5: {int((np.abs(diff) > 5).sum())} =="
    )

    # ---- measured series ----------------------------------------------------
    meas = pd.read_parquet(
        REPO / "data" / "raw" / "ercot" / f"ercot_{year}_ordc_reserves_hourly.parquet"
    ).set_index("hour")
    rtolcap = meas["rtolcap"].reindex(range(hours)).to_numpy()
    rtorpa = meas["rtorpa"].reindex(range(hours)).to_numpy()

    # ---- CAMPD side ----------------------------------------------------------
    _, _, _, _, online_gross = _class_hourly(year, chp_export_basis=True)
    gross = np.zeros(hours)
    for grp in CAMPD_CLASSES:
        gross += online_gross.get(grp, np.zeros(hours))[:hours]
    headroom_campd = env_all - gross + storage_as + lr

    # ---- over-fire mask ------------------------------------------------------
    fire = (adder_rec >= args.adder_min) & (np.nan_to_num(rtorpa, nan=0.0) < 10.0)
    n = int(fire.sum())
    print(
        f"\n== over-fire hours: adder >= ${args.adder_min:.0f} & measured RTORPA "
        f"< $10 -> {n} h =="
    )
    month = _CAL.month.to_numpy()
    hod = np.arange(hours) % 24
    if n:
        print("  by month:", dict(pd.Series(month[fire]).value_counts().sort_index()))
        blocks = pd.cut(
            hod[fire],
            bins=[-1, 5, 11, 16, 21, 23],
            labels=["h0-5", "h6-11", "h12-16", "h17-21", "h22-23"],
        )
        print("  by hod:", dict(pd.Series(blocks).value_counts().sort_index()))

        def m(x):
            return float(np.nanmean(x[fire]))

        print(f"\n  env_all            {m(env_all):9,.0f} MW")
        print(f"  sum P_elig (model) {m(P_elig):9,.0f} MW")
        print(f"  storage-AS credit  {m(storage_as):9,.0f} MW")
        print(f"  LR credit          {m(lr):9,.0f} MW")
        print(f"  offline (fwd)      {m(offline):9,.0f} MW")
        print(f"  online room MODEL  {m(online):9,.0f} MW")
        print(f"  measured RTOLCAP   {m(rtolcap):9,.0f} MW")
        print(f"  room gap (meas-mod){m(rtolcap - online):9,.0f} MW")
        print(
            f"    supply-mix term (P_model - CAMPD gross): {m(P_elig - gross - kl.loc[kl.index == 'nuclear'].sum(axis=0).to_numpy()[:hours] if 'nuclear' in kl.index else P_elig - gross):9,.0f} MW (incl. nuclear wedge)"
        )
        print(
            f"    envelope residual (RTOLCAP - CAMPD headroom): {m(rtolcap - headroom_campd):9,.0f} MW"
        )

        print(
            "\n  -- class-resolved model vs CAMPD gross at over-fire hours (mean MW) --"
        )
        for cls in CAMPD_CLASSES:
            rows = [
                c
                for c in kl.index
                if (c.startswith("COAL") if cls == "COAL" else c == cls)
            ]
            mm = (
                kl.loc[rows].sum(axis=0).to_numpy()[:hours] if rows else np.zeros(hours)
            )
            gg = online_gross.get(cls, np.zeros(hours))[:hours]
            print(
                f"    {cls:<11} model {float(np.nanmean(mm[fire])):8,.0f}  "
                f"CAMPD {float(np.nanmean(gg[fire])):8,.0f}  "
                f"diff {float(np.nanmean(mm[fire] - gg[fire])):+8,.0f}"
            )
        if "nuclear" in kl.index:
            nuc = kl.loc["nuclear"].to_numpy()[:hours]
            print(
                f"    {'nuclear':<11} model {float(np.nanmean(nuc[fire])):8,.0f}  (no CAMPD)"
            )

    # storage discharge at the over-fire hours (the ERCOT-58 leading term)
    st = bdir / "storage.parquet"
    if st.exists() and n:
        sdf = pd.read_parquet(st)
        if "pass" in sdf.columns:
            sdf = sdf[sdf["pass"] == "P1"]
        if "year" in sdf.columns:
            sdf = sdf[sdf["year"] == year]
        dis = (
            sdf.groupby("hour")["discharge_mw"]
            .sum()
            .reindex(range(hours), fill_value=0.0)
        ).to_numpy()
        print(
            f"\n  storage discharge at over-fire hours: mean {float(np.nanmean(dis[fire])):,.0f} MW"
        )


if __name__ == "__main__":
    main()
