"""caiso-221 Phase 0 — the south-belly surplus-pricing DESIGN arithmetic.

The caiso-215 §F H4 object ("design a representation of the south-belly
surplus-pricing regime from measured quantities") is the only remaining
object sized to close C3a-2024/25 that is 2023-safe. This probe is its
kill-before-solve instrument: it measures, from committed bytes only, the
CEILING of every rule-13-admissible candidate representation against the
required moves (2024 −$0.85 / 2025 −$1.90 to the +10 % band edge; 2023
down-headroom −$7.56 — FINDING-caiso220 §A on keeper
`2026-08-26-caiso-220-c1-crosswalk`).

The candidate classes measured (each is a *quantity*-side input; no measured
price ever enters as an input, no adder/floor/derate is tuned to a residual):

* C-A  zonal RE-PLACEMENT of the measured curtailment add-back. The keeper
       already consumes the full reported curtailment as potential (the HSL
       analogue, `build_caiso_hsl.py`: EIA-930 delivered + reported
       curtailment), but `_distribute_by_eia860` smears that ISO-wide series
       across ALL zones by capacity x clear-sky shape — so a measured share
       of the curtailed MW is placed NORTH of Path 15, while the caiso-219
       census puts the off-peak (belly) constraint mass at PG&E Kern/Fresno
       and reality's record is 78-92 % Local-class. C-A moves the add-back's
       zonal placement south (census-informed), leaving the ISO total and
       the delivered half untouched.
* C-B  measured absorption reservation: reduce belly storage-charge power by
       an AS-award-scale reservation (the rule-13 canonical "measured
       ancillary-service power reservation" class), bounded generously at
       1-2 GW.
* C-E  the sub-zonal gen-pocket behind an export limit (the caiso-216 §F.3a
       object, census-relocated to Gates-Midway/Kern-Fresno by caiso-219).
       Measured here on LOAD-SHARE arithmetic, independent of the CEII
       rating wall: a gen-pocket floors prices only INSIDE the pocket, and
       the pocket's load share bounds its scored-C3a reach.
* C-F  the PERFECT-REGIME benchmark (not a candidate — the unreachability
       yardstick): set model south λ equal to the hub actual in exactly the
       convertible cells (reality-south-negative hours where the model sits
       above actual) and read the lw-$ move. If even this cleared less than
       the required move the object would die on sizing alone; it measures
       what any admissible instrument would have to reach.

Sections (stdout + JSON):

* A0 — controls: demand row-match vs the keeper sidecar; recon ISO renewable
  potential vs the HSL parquet (the add-back is already in the inputs);
  model endogenous spill re-measured on THIS keeper.
* A1 — the add-back audit: annual/belly add-back by fuel, its Local/System
  reason split (workbook), and its CURRENT zonal placement (the north-share
  the capacity-pro-rata distributor implies) vs the census geography.
* A2 — regime decomposition of reality's south-negative hours (TH_SP15 RT
  < 0): model price-state (floored vs above-floor) x curtailment class
  (Local-active / System-active / none) x TI-export, with each cell's
  south-zone gap-$ mass in scored lw-$ terms.
* A3 — the C-F perfect-conversion ceiling per year (and its 2023 cost).
* A4 — candidate ceilings: C-A re-placement (static cut-15 exceedance delta
  + the caiso-220 empirical static->scored transfer), C-B absorption cut
  (exceedance over path+storage-minus-reservation), C-E pocket load-share
  arithmetic.
* A5 — the verdict table: every ceiling against the required moves.

NO LP, NO SOLVE. The only reconstruction is the licensed caiso-105/131
``run_year(fleet_only=True)`` input assembly (caiso-202/216/218 pattern),
rebuilt from the caiso-220 keeper bundle's own ``meta.json``. Everything
else is committed: the keeper ``hourly/`` sidecars, the HSL parquets, the
curtailment workbooks, the trading-hub RTM CSVs (caiso-215 loader), the
EIA-930 CISO parquet, the caiso-219 census JSON.

Writes ``results/calibration/_caiso221_surplus_design.json`` (deterministic:
sorted keys, rounded floats, no timestamps).

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso221_surplus_design.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _caiso215_c3a_zonal_decomp as c215  # noqa: E402  (committed probe)
import _caiso216_belly_surplus as c216  # noqa: E402  (committed probe)

YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso220_c1_crosswalk"
HSL_DIR = REPO / "data/raw/caiso-hsl"
CENSUS = REPO / "results/calibration/_caiso219_deliverability_census.json"
OUT_JSON = REPO / "results/calibration/_caiso221_surplus_design.json"

CACHE = Path(
    os.environ.get(
        "CAISO221_CACHE",
        os.environ.get("CAISO216_CACHE", "/tmp/caiso221_cache"),
    )
)

CA_ZONES = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")
SOUTH4 = ("ZP26", "LA_BASIN", "SDGE", "SP15_rest")
# caiso-215 hub convention: each zone scored against its own trading hub.
HUB_OF = {
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
    "LA_BASIN": "TH_SP15_GEN-APND",
    "SDGE": "TH_SP15_GEN-APND",
    "SP15_rest": "TH_SP15_GEN-APND",
}
PATH15_SN_CAP = 5400.0  # armed WECC-catalog S->N rating (caiso-216 B2)
BELLY = (10, 15)

# Required C3a moves to the +10 % edge on THIS keeper (FINDING-caiso220 §A:
# model lw 56.31/38.96/39.76 vs RT 54.17/34.65/34.42).
REQUIRED = {"2023": -7.56, "2024": -0.85, "2025": -1.90}  # 2023 = headroom

# The caiso-220 empirical static->scored transfer: the crosswalk moved the
# static cut-15 L2 exceedance from 17/234/289 h (caiso-216 B2) to 121/480/742 h
# (committed `_caiso217_realized_membership.json`) and the SCORED C3a by
# −$0.05/−$0.10/−$0.07 (caiso-200 +4.1/+12.8/+15.7 -> caiso-220
# +4.0/+12.5/+15.5 on actuals 54.17/34.65/34.42). One committed point, used
# only as an order-of-magnitude ceiling scale; the static delta OVERSTATES the
# scored effect (the LP re-equilibrates: 742 static h -> 17 scored >$15 h in
# 2025), so a ceiling built on it is conservative in the kill direction.
TRANSFER_DPH = {  # $ per static-exceedance-hour added, per year
    "2023": 0.05 / (121 - 17),
    "2024": 0.10 / (480 - 234),
    "2025": 0.07 / (742 - 289),
}


def r2(x) -> float:
    """Round for the deterministic JSON."""
    return float(np.round(float(x), 2))


def r3(x) -> float:
    """Round for the deterministic JSON (3 dp)."""
    return float(np.round(float(x), 3))


def sidecars(year: int) -> dict:
    """Keeper per-zone hourly price/demand + ISO class MW + storage flows."""
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    out = {
        "price": d.pivot_table(index="hour", columns="zone", values="price"),
        "demand": d.pivot_table(index="hour", columns="zone", values="demand"),
    }
    c = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    out["klass"] = c.pivot_table(index="hour", columns="klass", values="mw")
    s = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    out["charge"] = s.groupby("hour")["charge_mw"].sum().reindex(range(HOURS))
    return out


def recon(year: int) -> dict:
    """The licensed fleet_only input assembly from the caiso-220 meta.json.

    Identical construction to the committed caiso-216 probe's ``recon`` (the
    caiso-105/131 pattern, including the override-dict renames a naive kwargs
    filter drops), pointed at the caiso-220 keeper bundle and cached under a
    caiso-221 key.
    """
    p = CACHE / f"caiso221_recon_{year}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in z.files}
    import inspect

    from run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {k: v for k, v in meta.items() if k in params and k not in skip}
    for meta_key, param in (
        ("coal_prb_sigmoid_overrides", "prb_overrides"),
        ("coal_bit_sigmoid_overrides", "bit_overrides"),
        ("coal_bit_passthrough_sigmoid", "coal_bit_sigmoid"),
    ):
        if meta_key in meta and param in params and param not in kwargs:
            kwargs[param] = meta[meta_key]
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    state = run_year(year, meta["iso"], HOURS, gas, {}, fleet_only=True, **kwargs)

    from market_sim.data.fleet import FUEL_TYPE_MAP

    inv = {v: k for k, v in FUEL_TYPE_MAP.items()}
    fa = state["fleet_arrays"]
    fuel = np.array([inv.get(int(i), str(i)) for i in np.asarray(fa.fuel_type_idx)])
    zone_idx = np.asarray(fa.zone_idx, dtype=int)
    n_zones = int(np.asarray(state["demand"]).shape[0])

    def zone_hourly(mask: np.ndarray, values: np.ndarray) -> np.ndarray:
        out = np.zeros((n_zones, HOURS), dtype=np.float64)
        np.add.at(out, zone_idx[mask], values[mask])
        return out

    avail = np.asarray(fa.availability, dtype=float)
    pmax_h = np.asarray(fa.pmax, dtype=float)[:, None] * avail
    lower = (
        np.asarray(fa.min_gen, dtype=float)
        if fa.min_gen is not None
        else np.asarray(fa.pmin, dtype=float)[:, None] * np.ones((1, HOURS))
    )
    lower = np.minimum(lower, pmax_h)

    stor_power = np.zeros(n_zones)
    for u in state["storage_units"]:
        stor_power[int(getattr(u, "zone_idx", 0))] += float(
            getattr(u, "power_cap_mw", 0.0)
        )

    out = {
        "demand": np.asarray(state["demand"], dtype=np.float64),
        "wind_pot": np.asarray(state["wind_cf"], dtype=np.float64)
        * np.asarray(state["wind_cap"], dtype=np.float64)[:, None],
        "solar_pot": np.asarray(state["solar_cf"], dtype=np.float64)
        * np.asarray(state["solar_cap"], dtype=np.float64)[:, None],
        "nuclear_mw": zone_hourly(fuel == "nuclear", pmax_h),
        "hydro_floor": zone_hourly(fuel == "hydro", lower),
        "storage_power": stor_power,
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, **out)
    return out


def hsl_series(year: int) -> dict[str, np.ndarray]:
    """The committed HSL parquet: delivered, potential, add-back per fuel."""
    df = pd.read_parquet(HSL_DIR / f"caiso_{year}_hsl_hourly.parquet")
    out = {}
    for fuel in ("wind", "solar"):
        out[f"{fuel}_gen"] = df[f"{fuel}_gen_mw"].to_numpy(dtype=float)
        out[f"{fuel}_hsl"] = df[f"{fuel}_hsl_mw"].to_numpy(dtype=float)
        out[f"{fuel}_add"] = out[f"{fuel}_hsl"] - out[f"{fuel}_gen"]
    return out


def curtailment_by_reason(year: int) -> dict[str, np.ndarray]:
    """Hourly Local/System curtailment MWh on the model's fixed 8760 clock.

    Maps the caiso-216 workbook loader's (day, hour-1..24, reason) rows onto
    the fixed non-leap clock with the same month/day/hour arithmetic as
    ``build_caiso_hsl.py`` (Feb 29 dropped), so the reason split rides the
    SAME clock convention as the HSL add-back it partitions.
    """
    curt = c216.curtailment_hourly(year)
    month_days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    month_start = np.array([sum(month_days[:m]) * 24 for m in range(12)])
    out = {
        "Local": np.zeros(HOURS),
        "System": np.zeros(HOURS),
    }
    month = curt["day"].dt.month.to_numpy()
    day = curt["day"].dt.day.to_numpy()
    hour = curt["hour"].to_numpy(dtype=int)
    keep = ~((month == 2) & (day == 29))
    hoy = month_start[month[keep] - 1] + (day[keep] - 1) * 24 + (hour[keep] - 1)
    total = (curt["wind"] + curt["solar"]).to_numpy(dtype=float)[keep]
    reason = curt["reason"].astype(str).to_numpy()[keep]
    for key in out:
        mask = reason == key
        np.add.at(out[key], hoy[mask], total[mask])
    return out


def main() -> None:  # noqa: PLR0915  (a linear report, sectioned by prints)
    out: dict = {"years": {}}
    hod = np.arange(HOURS) % 24
    belly = (hod >= BELLY[0]) & (hod <= BELLY[1])

    census = json.loads(CENSUS.read_text())
    out["census_offpeak_geography"] = {
        area.split(" Interconnection")[0]: f"{v['off_peak']}/{v['constraints']}"
        for area, v in census["summary"]["by_area"].items()
    }

    for year in YEARS:
        print("=" * 78)
        print(f"YEAR {year}")
        yr: dict = {}
        sc = sidecars(year)
        rc = recon(year)
        zmap = c216.match_zone_rows(rc["demand"], sc["demand"])
        missing = [z for z in CA_ZONES if z not in zmap]
        assert not missing, f"zone row match failed: {missing}"

        # ---- A0 controls ----
        hsl = hsl_series(year)
        pot_iso = {f: rc[f"{f}_pot"].sum(axis=0) for f in ("wind", "solar")}
        disp_iso = sc["klass"]["wind"].to_numpy() + sc["klass"]["solar"].to_numpy()
        spill = np.maximum(0.0, pot_iso["wind"] + pot_iso["solar"] - disp_iso)
        reasons = curtailment_by_reason(year)
        add_total = hsl["wind_add"] + hsl["solar_add"]
        yr["A0_controls"] = {
            "max_demand_row_err_mw": r2(
                max(
                    float(
                        np.nanmax(
                            np.abs(rc["demand"][zmap[z]] - sc["demand"][z].to_numpy())
                        )
                    )
                    for z in CA_ZONES
                )
            ),
            "recon_pot_vs_hsl_annual_ratio": {
                f: r3(pot_iso[f].sum() / max(hsl[f"{f}_hsl"].sum(), 1e-9))
                for f in ("wind", "solar")
            },
            "hsl_addback_twh": {
                f: r3(hsl[f"{f}_add"].sum() / 1e6) for f in ("wind", "solar")
            },
            "workbook_reason_twh": {k: r3(v.sum() / 1e6) for k, v in reasons.items()},
            "addback_vs_workbook_ratio": r3(
                add_total.sum()
                / max(reasons["Local"].sum() + reasons["System"].sum(), 1e-9)
            ),
            "model_spill_gwh": r2(spill.sum() / 1e3),
        }
        print("A0:", json.dumps(yr["A0_controls"], indent=1))

        # ---- A1 add-back audit: where does the distributor PLACE it? ----
        # Under the total-preserving redistribution, every ISO-wide MW in
        # hour t (delivered and add-back alike) lands on zone z in proportion
        # to z's share of that hour's zonal potential — measured here from
        # the recon per-zone potentials themselves.
        shares = {}
        ca_rows = [zmap[z] for z in CA_ZONES]
        for f in ("wind", "solar"):
            tot = np.maximum(rc[f"{f}_pot"][ca_rows].sum(axis=0), 1e-9)
            shares[f] = {z: rc[f"{f}_pot"][zmap[z]] / tot for z in CA_ZONES}
        add_north = sum(
            (hsl[f"{f}_add"] * shares[f]["NP15"]).sum() for f in ("wind", "solar")
        )
        add_all = max(add_total.sum(), 1e-9)
        add_north_belly = sum(
            (hsl[f"{f}_add"] * shares[f]["NP15"])[belly].sum()
            for f in ("wind", "solar")
        )
        yr["A1_addback_placement"] = {
            "addback_belly_share": r3(add_total[belly].sum() / add_all),
            "north_share_of_addback": r3(add_north / add_all),
            "north_share_belly_only": r3(
                add_north_belly / max(add_total[belly].sum(), 1e-9)
            ),
            "addback_north_twh": r3(add_north / 1e6),
            "local_share_of_record": r3(
                reasons["Local"].sum()
                / max(reasons["Local"].sum() + reasons["System"].sum(), 1e-9)
            ),
            "zone_solar_pot_share_annual": {
                z: r3(
                    rc["solar_pot"][zmap[z]].sum()
                    / max(rc["solar_pot"][[zmap[x] for x in CA_ZONES]].sum(), 1e-9)
                )
                for z in CA_ZONES
            },
        }
        print("A1:", json.dumps(yr["A1_addback_placement"], indent=1))

        # ---- A2 regime decomposition of reality's south-negative hours ----
        rtm = c215.load_market_csv("rtm", year, c215.HUBS)
        hub = {h: rtm["LMP"][h].to_numpy() for h in c215.HUBS}
        sp15 = hub["TH_SP15_GEN-APND"]
        sneg = sp15 < 0.0
        lam = {z: sc["price"][z].to_numpy() for z in CA_ZONES}
        dem = {z: sc["demand"][z].to_numpy() for z in CA_ZONES}
        dem_iso_year = float(sum(np.nansum(dem[z]) for z in CA_ZONES))

        # South gap-$ per hour on the caiso-215 per-hub convention.
        gap_h = np.zeros(HOURS)
        for z in SOUTH4:
            gap_h += dem[z] * (lam[z] - hub[HUB_OF[z]])
        gap_h = np.where(np.isnan(gap_h), 0.0, gap_h)

        floored = lam["SP15_rest"] <= 0.0
        loc_on = reasons["Local"] > 1.0
        sys_on = reasons["System"] > 1.0
        e930 = c216.e930_series(year)
        ti_exp = np.nan_to_num(e930["TI"]) > 0.0

        def cell(mask: np.ndarray) -> dict:
            m = sneg & mask
            return {
                "hours": int(m.sum()),
                "south_gap_musd": r2(gap_h[m].sum() / 1e6),
                "lw_usd": r3(gap_h[m].sum() / dem_iso_year),
                "model_sp15rest_lambda_p50": r2(
                    np.nanmedian(lam["SP15_rest"][m]) if m.any() else np.nan
                ),
            }

        yr["A2_regime_decomposition"] = {
            "sneg_hours": int(sneg.sum()),
            "sneg_total": cell(np.ones(HOURS, bool)),
            "model_already_floored": cell(floored),
            "model_above_floor": cell(~floored),
            "above_floor__local_active": cell(~floored & loc_on),
            "above_floor__system_active": cell(~floored & sys_on),
            "above_floor__no_curtailment": cell(~floored & ~loc_on & ~sys_on),
            "above_floor__ti_export": cell(~floored & ti_exp),
            "year_south_gap_musd": r2(gap_h.sum() / 1e6),
            "year_south_gap_lw_usd": r3(gap_h.sum() / dem_iso_year),
        }
        print("A2:", json.dumps(yr["A2_regime_decomposition"], indent=1))

        # ---- A2b the depth witness: the storage buffer under the split ----
        # In the convertible hours the model's southern λ sits at the
        # charge-parity band because the storage fleet still has charge
        # headroom — the buffer any admissible absorption-side reduction
        # would have to EXHAUST for λ to fall to the floor.
        chg = sc["charge"].to_numpy(dtype=float)
        conv_m = sneg & ~floored
        stor_iso = float(rc["storage_power"].sum())
        yr["A2b_depth_witness"] = {
            "iso_storage_power_mw": r2(stor_iso),
            "charge_in_convertible_p50_mw": r2(
                np.nanmedian(chg[conv_m]) if conv_m.any() else np.nan
            ),
            "charge_in_convertible_p95_mw": r2(
                np.nanpercentile(chg[conv_m], 95) if conv_m.any() else np.nan
            ),
            "min_power_headroom_in_convertible_mw": r2(
                (stor_iso - np.nanmax(chg[conv_m])) if conv_m.any() else np.nan
            ),
        }
        print("A2b:", json.dumps(yr["A2b_depth_witness"], indent=1))

        # ---- A3 the C-F perfect-conversion ceiling ----
        # Set model λ_z := its hub actual in exactly the convertible cells
        # (s-neg hours, south4 zones, model above actual). The lw-$ delta is
        # the ceiling ANY admissible instrument would have to approach.
        over_pos = np.zeros(HOURS)
        for z in SOUTH4:
            over = np.nan_to_num(lam[z] - hub[HUB_OF[z]], nan=0.0)
            over_pos += dem[z] * np.maximum(0.0, over)
        skirt20 = sp15 < 20.0  # the surplus regime's wider skirt
        yr["A3_perfect_conversion"] = {
            "sneg_lw_usd_ceiling": r3(-over_pos[sneg].sum() / dem_iso_year),
            "skirt_sub20_hours": int(np.nansum(skirt20)),
            "skirt_sub20_lw_usd_ceiling": r3(-over_pos[skirt20].sum() / dem_iso_year),
            "required_move": REQUIRED[str(year)],
            "sneg_clears_requirement": bool(
                over_pos[sneg].sum() / dem_iso_year >= -REQUIRED[str(year)]
            )
            if year != 2023
            else None,
        }
        print("A3:", json.dumps(yr["A3_perfect_conversion"], indent=1))

        # ---- A4 candidate ceilings ----
        # Cut-15 L2 net position (caiso-216 B2 layers, rebuilt here).
        zi_s = [zmap[z] for z in SOUTH4]
        dem_s = rc["demand"][zi_s].sum(axis=0)
        ren_s = rc["solar_pot"][zi_s].sum(axis=0) + rc["wind_pot"][zi_s].sum(axis=0)
        nuc_s = rc["nuclear_mw"][zi_s].sum(axis=0)
        inj_iso = np.zeros(HOURS)
        for kl in ("biomass", "OTHER"):
            if kl in sc["klass"].columns:
                inj_iso = inj_iso + sc["klass"][kl].to_numpy()
        zshare_s = sum(np.nansum(dem[z]) for z in SOUTH4) / dem_iso_year
        base15 = ren_s + nuc_s + inj_iso * zshare_s - dem_s
        stor_s = float(rc["storage_power"][zi_s].sum())

        # C-A: move the ENTIRE north-placed add-back south (upper bound).
        add_north_t = sum(
            hsl[f"{f}_add"] * shares[f]["NP15"] for f in ("wind", "solar")
        )
        varA = base15 + add_north_t
        # C-B: reserve 1 / 2 GW of southern charge power (AS-award scale).
        base_hours = int((base15 > PATH15_SN_CAP).sum())
        varA_hours = int((varA > PATH15_SN_CAP).sum())
        dph = TRANSFER_DPH[str(year)]
        yr["A4_candidates"] = {
            "base_L2_hours_over_path": base_hours,
            "base_L2_hours_over_path_plus_storage": int(
                (base15 > PATH15_SN_CAP + stor_s).sum()
            ),
            "south_storage_power_mw": r2(stor_s),
            "C_A_replacement": {
                "addback_north_belly_mean_mw": r2(add_north_t[belly].mean()),
                "hours_over_path": varA_hours,
                "delta_hours": varA_hours - base_hours,
                "ceiling_lw_usd": r3(-dph * (varA_hours - base_hours)),
            },
            "C_B_as_reservation": {
                f"reserve_{gw}gw_hours_over_path_plus_storage": int(
                    (base15 > PATH15_SN_CAP + stor_s - gw * 1000.0).sum()
                )
                for gw in (1, 2)
            },
            "C_E_pocket_load_share": {
                "zp26_demand_share": r3(np.nansum(dem["ZP26"]) / dem_iso_year),
                # Generous ceiling: the WHOLE ZP26 zone (a strict superset of
                # the Gates-Midway Kern/Fresno gen pocket) priced at the −$20
                # floor instead of the model's own λ through every s-neg hour.
                "ceiling_lw_usd": r3(
                    -np.nansum(
                        dem["ZP26"][sneg] * np.maximum(0.0, lam["ZP26"][sneg] + 20.0)
                    )
                    / dem_iso_year
                ),
            },
        }
        print("A4:", json.dumps(yr["A4_candidates"], indent=1))

        out["years"][str(year)] = yr

    # ---- A5 verdict table ----
    out["A5_required_moves_usd"] = REQUIRED
    out["A5_transfer_provenance"] = (
        "caiso-220 committed point: static cut-15 exceedance +104/+246/+453 h "
        "(caiso-216 L2 17/234/289 -> caiso-217 realized 121/480/742) bought "
        "scored C3a -$0.05/-$0.10/-$0.07; the LP re-equilibration crushed "
        "742 static h to 17 scored >$15 h in 2025, so static-hour ceilings "
        "OVERSTATE scored reach."
    )
    OUT_JSON.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT_JSON.relative_to(REPO)}")


if __name__ == "__main__":
    main()
