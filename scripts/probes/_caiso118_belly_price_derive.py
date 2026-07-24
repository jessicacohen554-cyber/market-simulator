"""caiso-118 LEG-1 DERIVE: why does the model CAISO belly (hod 10-15) clear at
gas (~$28) instead of the actual ~$15 (curtailable-solar / cheap-import margin)?
DERIVE-FIRST, NO SOLVE (rule #1).

The caiso-117 redirect: the belly VOLUME cap fixes C5a but BREAKS C3a in 2025
because the model belly is over-PRICED (clears at gas ~$28, actual ~$15). Before
re-arming the volume cap we must make the belly clear near actual. Two suspects
the handoff named:

  (1) SOLAR MARGINALITY — is solar fully absorbed (at its potential, inframarginal)
      so it can never set the belly dual, forcing the marginal unit up to gas?
      caiso_solar_endogenous_spill is ON in the keeper (the pre-LP CF derate is
      SKIPPED; full solar potential is passed), so the question is whether solar
      actually SPILLS (curtails) in the belly. If it never spills, the belly is
      supply-short of cheap MWh and gas/import is genuinely marginal → the lever
      is NOT "let solar be marginal" (it already can be) but "why isn't it".

  (2) IMPORT HUB PRICING — the model belly marginal import clears at the PNW
      ($28 ladder / $28.6 hub) or a domestic CC (~$28) rung, while the measured
      DESERT-SW (Palo Verde) belly hub is only ~$10.5. If the belly's marginal
      rung were the cheap DSW hub, the belly dual would fall toward ~$10-15.
      caiso_import_hub_prices is OFF; the DSW clean-depth tranches ARE priced at
      the measured hub but are CAPACITY-CAPPED (measured depth + corridor ATC),
      so once exhausted the belly falls back to the $28 rung.

This probe measures, per year, from the COMMITTED keeper-proxy hourlies
(caiso104_m1_B: class_hourly + system, reproduces the keeper C4 digit-for-digit)
+ the LP's own renewable potential (load_renewable_profiles) + the measured hub
series (measured_import_hub_prices):

  INV1 — model belly price by hod & the marginal-unit merit (what class's MC
         sits at the belly dual).
  INV2 — solar SPILL in the belly: potential vs dispatched. Is solar at its
         bound (curtailment ~0 → cannot be marginal) or spilling (should be $0)?
  INV3 — the belly supply stack vs demand: the cheap-MWh residual. After
         solar(full) + nuclear + wind + hydro + firm/clean imports, how much
         belly demand is left for the $28 dispatchable rung to fill (and thus
         set the price)?
  INV4 — import merit in the belly: which import tranche is marginal, its ladder
         price vs its measured hub price (the suspect-2 magnitude: PNW $28.6 vs
         DSW $10.5), and how much cheap DSW headroom is left unused.

Run:  PYTHONPATH=<repo> python scripts/probes/_caiso118_belly_price_derive.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia930.envelopes import measured_corridor_flow_envelope
from market_sim.data.eia_loader import measured_import_hub_prices
from market_sim.data.renewables import load_renewable_profiles

REPO = "/home/user/market-simulator"
PROXY = f"{REPO}/results/calibration/caiso104_m1_B/hourly"
CISO_HOURLY = f"{REPO}/data/raw/eia-930-hourly/CISO hourly.parquet"
BELLY = [10, 11, 12, 13, 14, 15]
EVENING = [17, 18, 19, 20, 21]
YEARS = (2023, 2024, 2025)
HOURS = 8760
GAS_KLASS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
# handoff actual DAM hub-avg intraday (Pacific): 2024 belly 14.9, evening 54.4
ACTUAL_BELLY = {2024: 14.9}


def _keeper_config(year: int) -> ScenarioConfig:
    """A ScenarioConfig matching the keeper flags that affect renewable potential.

    Only the fields that change solar_cf/solar_cap matter here (endogenous spill
    → no pre-LP derate, so the potential the probe reconstructs == the LP's
    solar upper bound). All other flags are irrelevant to load_renewable_profiles.
    """
    return ScenarioConfig(
        iso="CAISO",
        start_year=year,
        end_year=year,
        weather_year=year,
        mode="backcast",
        caiso_solar_deliverability=True,
        caiso_solar_endogenous_spill=True,
    )


def _solar_potential(year: int) -> np.ndarray:
    """LP solar upper bound (MW, system) per hour = Σ_zone solar_cf × solar_cap.

    With caiso_solar_endogenous_spill ON the runner SKIPS the deliverability
    derate, so this raw potential IS the LP's solar upper bound (byte-match to
    what the belly LP can dispatch)."""
    iso_config = get_iso_config("CAISO")
    cfg = _keeper_config(year)
    _wcf, _wcap, solar_cf, solar_cap = load_renewable_profiles(
        "CAISO", year, iso_config, cfg
    )
    # solar_cf: (n_zone, hours); solar_cap: (n_zone,)
    return (solar_cf * solar_cap[:, None]).sum(axis=0)[:HOURS]


def _load_hourlies(year: int):
    ch = pq.read_table(f"{PROXY}/class_hourly_{year}.parquet").to_pandas()
    sy = pq.read_table(f"{PROXY}/system_{year}.parquet").to_pandas()
    ch["hod"] = ch["hour"] % 24
    sy["hod"] = sy["hour"] % 24
    return ch, sy


def _class_series(ch: pd.DataFrame, klass: str) -> np.ndarray:
    """System MW for one class over 8760 hours (0 where absent)."""
    g = ch[ch["klass"] == klass].groupby("hour")["mw"].sum()
    out = np.zeros(HOURS)
    out[g.index.to_numpy()] = g.to_numpy()
    return out


def _lw_price_by_hod(sy: pd.DataFrame) -> pd.Series:
    """CA load-weighted price by hod (exclude external WECC zones)."""
    ca = sy[~sy["zone"].astype(str).str.startswith("WECC")]

    def lw(g):
        d = g["demand"].to_numpy()
        p = g["price"].to_numpy()
        return float((p * d).sum() / d.sum()) if d.sum() > 0 else np.nan

    return ca.groupby("hod").apply(lw)


def main() -> None:
    print("=" * 78)
    print("caiso-118 belly price-formation DERIVE  (NO SOLVE; keeper-proxy caiso104_m1_B)")
    print("=" * 78)

    for year in YEARS:
        ch, sy = _load_hourlies(year)
        price_hod = _lw_price_by_hod(sy)
        belly_price = float(price_hod.loc[BELLY].mean())
        eve_price = float(price_hod.loc[EVENING].mean())

        # class stacks (system MW)
        cls = {
            k: _class_series(ch, k)
            for k in (
                "solar", "wind", "nuclear", "hydro", "import", "biomass",
                "CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "OTHER",
            )
        }
        solar_pot = _solar_potential(year)
        # CA demand (system, exclude external zones)
        ca_dem = (
            sy[~sy["zone"].astype(str).str.startswith("WECC")]
            .groupby("hour")["demand"].sum().reindex(range(HOURS), fill_value=0.0).to_numpy()
        )
        hod = np.arange(HOURS) % 24
        bmask = np.isin(hod, BELLY)

        # INV1 — belly price
        print(f"\n### {year}  belly(10-15) CA LW price = {belly_price:6.2f} $/MWh"
              f"   evening(17-21) = {eve_price:6.2f}"
              + (f"   [actual belly {ACTUAL_BELLY[year]}]" if year in ACTUAL_BELLY else ""))

        # INV2 — solar spill in the belly
        sd = cls["solar"][bmask]
        sp = solar_pot[bmask]
        spill = np.clip(sp - sd, 0, None)
        spill_frac = spill.sum() / sp.sum() if sp.sum() > 0 else 0.0
        hrs_spilling = int((spill > 1.0).sum())
        print(f"  INV2 solar belly: dispatched {sd.mean():6.0f} MW  potential {sp.mean():6.0f} MW"
              f"  SPILL {spill.mean():6.0f} MW ({spill_frac*100:4.1f}% of pot)"
              f"  hrs spilling>1MW {hrs_spilling}/{bmask.sum()}")

        # INV3 — cheap-MWh residual: demand minus MC<=~5 supply
        cheap = (
            cls["solar"] + cls["wind"] + cls["nuclear"] + cls["hydro"] + cls["biomass"]
        )
        resid_after_cheap = ca_dem - cheap  # imports+gas still needed
        rb = resid_after_cheap[bmask]
        print(f"  INV3 belly residual after solar+wind+nuc+hydro+bio: {rb.mean():6.0f} MW"
              f"  (demand {ca_dem[bmask].mean():6.0f})  -> filled by import+gas")
        # what fills it: import vs gas
        imp_b = cls["import"][bmask].mean()
        gas_b = (cls["CC_REGULAR"] + cls["CC_CHP"] + cls["CT_PEAKER"]
                 + cls["CT_CHP"] + cls["ST_GAS"])[bmask].mean()
        print(f"       belly import {imp_b:6.0f} MW   belly gas {gas_b:6.0f} MW"
              f"   (CC_REG {cls['CC_REGULAR'][bmask].mean():5.0f}"
              f"  CC_CHP {cls['CC_CHP'][bmask].mean():5.0f})")

        # INV4 — import merit: ladder vs measured hub + the model's OWN solved
        # WECC import-node duals + the corridor belly cap. Is the cheap border
        # energy corridor-stranded (congestion) and are imports at the cap?
        hub = measured_import_hub_prices("CAISO", year, HOURS)
        wecc = sy[sy["zone"].astype(str).str.startswith("WECC")]
        wecc_belly = {
            str(z): float(zg[zg["hod"].isin(BELLY)]["price"].mean())
            for z, zg in wecc.groupby("zone", observed=True)
        }
        try:
            env = measured_corridor_flow_envelope("CAISO", year, HOURS)
            cap = np.nan_to_num(
                sum(np.asarray(v, float) for v in env.values())
                if isinstance(env, dict)
                else np.asarray(env, float)
            )
            corridor_cap = float(cap[bmask].mean())
        except Exception:
            corridor_cap = float("nan")
        if hub:
            pnw = np.nanmean(np.asarray(hub["PNW_midC"], float)[bmask])
            dsw = np.nanmean(np.asarray(hub["DSW_CCGT"], float)[bmask])
            print(f"  INV4 measured belly hub: PNW(Malin) {pnw:6.2f}   DSW(PaloVerde) {dsw:6.2f}"
                  f"   (ladder PNW_midC 36 / DSW_CCGT 68)")
        print(f"       model WECC import-node belly duals {wecc_belly}"
              f"   corridor belly cap {corridor_cap:5.0f} MW  (model import {imp_b:.0f})")

        # INV5 — the KILLER comparison: model vs actual belly gas / demand / solar
        # / import. Reality runs 2-3x MORE belly gas yet clears LOWER -> the model
        # UNDER-commits belly gas (state, not price). Raw EIA-930 CISO.
        w = pd.read_parquet(CISO_HOURLY)
        wlt = pd.to_datetime(w["Local time"])
        wy = w[(wlt.dt.year == year) & (wlt.dt.hour.isin(BELLY))]
        a_gas = float(pd.to_numeric(wy["NG: NG"], errors="coerce").mean())
        a_dem = float(pd.to_numeric(wy["Demand"], errors="coerce").mean())
        a_sun = float(pd.to_numeric(wy["NG: SUN"], errors="coerce").mean())
        a_imp = float(-pd.to_numeric(wy["Total interchange"], errors="coerce").mean())
        m_gas = sum(cls[k] for k in GAS_KLASS)[bmask].mean()
        print(f"  INV5 belly MODEL vs ACTUAL:  gas {m_gas:6.0f} / {a_gas:6.0f} MW"
              f"   demand {ca_dem[bmask].mean():6.0f} / {a_dem:6.0f}"
              f"   solar {cls['solar'][bmask].mean():6.0f} / {a_sun:6.0f}"
              f"   net-import {imp_b:5.0f} / {a_imp:5.0f}")
        print(f"       -> reality runs {a_gas / max(m_gas,1):.1f}x the belly gas at ~$15;"
              f" the model backs gas off & over-imports, clearing at full-MC gas.")

    print("\n" + "=" * 78)
    print("READ (rule #1 derive-first):")
    print(" * solar is ~98% absorbed -> a $0 curtailable-solar rung is INERT (suspect 1 refuted)")
    print(" * WECC border already cheap but corridor-capped; reprice is a VOLUME lever (suspect 2 coupled)")
    print(" * reality runs 2-3x MORE belly gas yet prices ~$15: the model UNDER-COMMITS belly gas.")
    print("   Lever = the committed-gas belly STATE (caiso_ra_mustoffer floor), not solar/import price.")
    print("=" * 78)


if __name__ == "__main__":
    main()
