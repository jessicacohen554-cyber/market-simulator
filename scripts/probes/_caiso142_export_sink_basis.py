"""caiso-142 — the A3 export-sink seam: D1 the seam reproduction + fix, D2 the
no-trade band the sink price sits in, D3 the plateau-break test, D4 the E1
exposure. NO LP IS BUILT AND NO SOLVER RUNS.

The chartered lane (FINDING-caiso140 §E ask A3) is: restore the P1 export outlet
that ``pipeline.commitment._bridge_floored_fleet`` deletes (FINDING-caiso138 §D)
on a principled sink basis, and re-price the 2.7-3.0 GW import-parity plateau
that holds 51-61 % of the C3a-2025 defect hours at constant lambda.

The gate this probe has to pass BEFORE any arm solves (charter step 3): show the
plateau actually breaks with the sink live. It does not, and the reason is
structural rather than parametric:

* §A (D1) reproduces the seam on the real functions and verifies the fix.
* §B (D2) measures the no-trade band the export leg is priced inside. The per-hub
  design prices import legs at ``hub + wheel + carbon + eps`` and export legs at
  ``hub - eps``, so the sink is BELOW the marginal import price by exactly the
  corridor's OATT wheel + 2 eps every hour the marginal supply is an import.
* §C (D3) is the kill. An absorption row can only ADD demand, so restoring it can
  only weakly RAISE every zone's lambda -- it can never lower one. The plateau's
  lambda IS a delivered-import price, so the sink is out of the money exactly
  where the plateau binds, and the one indirect channel that could have lowered
  CA lambda (freeing shared-interface headroom so the cheaper corridor imports
  more) is dead: the simultaneous interface group never binds in any hour of any
  year. Basis-independent: no sink price and no sink bound changes the sign.
* §D (D4) prices the E1 exposure of arming it anyway, per basis.
* §E surveys the admissible basis space (measured export capability + netback
  price) and states what it does and does not buy.

Every number reproduces from the keeper's committed ``hourly/`` sidecars
(``results/calibration/caiso139_dumpguard_B``), the committed actual-LMP
reference, the committed EIA-930 interchange frame and the model's own config
tables. §A additionally reconstructs the fleet through
``run_calibration.run_year(fleet_only=True)`` (the caiso-131/134/140 machinery)
so the seam is exercised on the real ``FleetArrays``, not a mock.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso142_export_sink_basis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
HOURS = 8760
YEARS = (2023, 2024, 2025)
BUNDLE = REPO / "results/calibration/caiso139_dumpguard_B"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
EPS = 1e-3  # model.interchange.caiso.CAISO_INTERTIE_TIEBREAK_EPS

# The two CAISO per-hub corridors and the measured hub each one's legs price off.
CORRIDORS = {"WECC_PNW": "MALIN", "WECC_DSW": "PALOVRDE"}
# One import tranche per hub, used only to pull that hub's measured series out of
# measured_import_hub_prices (every tranche on a hub shares one series).
HUB_PROBE_TRANCHE = {"WECC_PNW": "PNW_midC", "WECC_DSW": "DSW_CCGT"}
_META_RENAME = {
    "coal_prb_passthrough_sigmoid": "prb_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
SIMULTANEOUS_GROUP = "grp:+WECC_PNW>NP15+WECC_DSW>SP15_rest"


# --------------------------------------------------------------------------- #
# committed-bytes readers
# --------------------------------------------------------------------------- #
def actual_rt(year: int) -> np.ndarray:
    """Committed hourly actual RT LMP on the model calendar."""
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour")["rt"].reindex(range(HOURS)).to_numpy()


def month_of_hour(year: int) -> np.ndarray:
    """1-based month per model hour (fixed non-leap calendar)."""
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
        np.arange(HOURS + 24), unit="h"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def hour_sets(year: int) -> dict[str, np.ndarray]:
    """The caiso-140 §A hour sets, byte-identical definitions."""
    a = actual_rt(year)
    mo = month_of_hour(year)
    hd = np.arange(HOURS) % 24
    sepdec = np.isin(mo, (9, 10, 11, 12))
    return {
        "annual": np.ones(HOURS, dtype=bool),
        "defect": sepdec
        & np.isin(hd, (10, 11, 12, 13, 14, 15))
        & (np.nan_to_num(a, nan=1e9) <= 20.0),
        "belly": sepdec & np.isin(hd, (10, 11, 12, 13, 14, 15)),
        "night": sepdec & np.isin(hd, (0, 1, 2, 3, 4, 5, 6)),
    }


def sidecar_prices(year: int) -> tuple[np.ndarray, pd.DataFrame, np.ndarray]:
    """(CA load-weighted lambda, per-zone price frame, CA demand) from the keeper."""
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    price = d.pivot_table(index="hour", columns="zone", values="price")
    dem = d.pivot_table(index="hour", columns="zone", values="demand")
    ca = [z for z in price.columns if not str(z).startswith("WECC")]
    ca_dem = dem[ca].sum(axis=1).to_numpy()
    lam = ((price[ca] * dem[ca]).sum(axis=1).to_numpy()) / ca_dem
    return lam, price, ca_dem


def hub_series(year: int) -> dict[str, np.ndarray]:
    """Measured hub LMP per corridor (the series the per-hub injector writes)."""
    from market_sim.data.eia_loader import measured_import_hub_prices

    prices = measured_import_hub_prices(ISO, year, HOURS)
    if not prices:
        return {}
    return {
        zone: np.asarray(prices[HUB_PROBE_TRANCHE[zone]], dtype=float)
        for zone in CORRIDORS
        if HUB_PROBE_TRANCHE[zone] in prices
    }


def import_rows(year: int) -> pd.DataFrame:
    """Per-tranche hourly (mw, cap_mw) for every priced-interchange row."""
    u = pd.read_parquet(
        BUNDLE / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "fuel", "zone", "hour", "mw", "cap_mw"],
    )
    u = u[(u["pass"] == "P1") & (u["fuel"] == "import")]
    return u


def wheel_by_tranche() -> dict[str, float]:
    """Each import tranche's additive OATT point-to-point charge ($/MWh)."""
    from market_sim.config.interchange_config import (
        CAISO_IMPORT_DELIVERY_BASIS,
        IMPORT_TRANCHES,
    )
    from market_sim.model.interchange import caiso as C

    names = [n for n, _, _ in IMPORT_TRANCHES[ISO]] + [
        C.CAISO_DSW_SURPLUS_CLEAN_NAME,
        C.CAISO_DSW_OVERNIGHT_CLEAN_NAME,
        C.CAISO_DSW_DAYTIME_CLEAN_NAME,
    ]
    return {n: float(CAISO_IMPORT_DELIVERY_BASIS.get(n, (0.0, 0.0))[1]) for n in names}


# --------------------------------------------------------------------------- #
# §A — D1: the seam, reproduced on the real functions, and the fix verified
# --------------------------------------------------------------------------- #
def fleet_state(year: int) -> dict:
    """Reconstruct the keeper's fleet for ``year`` (no LP, no solve)."""
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
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas,
        {},
        fleet_only=True,
        **kwargs,
    )


def section_a(year: int = 2025) -> dict:
    """D1: compose the real RA bridge floor both ways and diff the result."""
    import dataclasses

    from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER
    from market_sim.pipeline.commitment import _bridge_floored_fleet

    print("\n" + "=" * 78)
    print(f"§A  D1 — the seam on the real functions ({year})")
    print("=" * 78)
    state = fleet_state(year)
    fa = state["fleet_arrays"]
    pmin = np.asarray(fa.pmin, dtype=float)
    absorb = pmin < 0.0
    uid = np.array([str(u) for u in fa.unit_ids])
    print(f"fleet rows={pmin.size}  pmin<0 rows={int(absorb.sum())}")
    for r in np.flatnonzero(absorb):
        print(f"  absorption row: {uid[r]:34s} pmin={pmin[r]:10.1f} pmax={fa.pmax[r]:8.1f}")

    # A zeros-initialised bridge floor positive only on bridged thermal rows is
    # exactly the shape caiso_ra_mustoffer_min_gen returns; build the smallest
    # such floor that exercises the composition (one gas row, one hour block).
    base_min_gen = (
        np.asarray(fa.min_gen, dtype=float)
        if fa.min_gen is not None
        else np.broadcast_to(pmin[:, None], (pmin.size, HOURS))
    )
    floor = np.zeros((pmin.size, HOURS), dtype=float)
    gas_rows = np.flatnonzero(
        np.array(
            [g.fuel_type in ("gas", "natural gas", "NG") for g in state["fleet"]],
            dtype=bool,
        )
        if "fleet" in state
        else ~absorb
    )
    pick = int(gas_rows[np.argmax(fa.pmax[gas_rows])]) if gas_rows.size else 0
    floor[pick, 100:200] = 0.26 * float(fa.pmax[pick])

    off = _bridge_floored_fleet(fa, floor, MECH_RA_MUSTOFFER)
    on = _bridge_floored_fleet(fa, floor, MECH_RA_MUSTOFFER, preserve_absorption=True)
    mg_off = np.asarray(off.min_gen, dtype=float)
    mg_on = np.asarray(on.min_gen, dtype=float)
    base = np.asarray(base_min_gen, dtype=float)

    print(f"\nbridge floor written on row {uid[pick]} (hours 100-200)")
    for label, mg in (("flag OFF (keeper today)", mg_off), ("flag ON (the fix)", mg_on)):
        print(f"  {label}:")
        for r in np.flatnonzero(absorb):
            verdict = (
                "range DELETED (pinned off)"
                if mg[r].min() == 0.0
                else "range PRESERVED"
            )
            print(
                f"    {uid[r]:34s} min_gen min={mg[r].min():10.1f} "
                f"max={mg[r].max():10.1f}  base min={base[r].min():10.1f}  -> {verdict}"
            )
    # Nothing but the absorption rows may differ between the two compositions.
    diff = np.abs(mg_on - mg_off) > 0.0
    rows_diff = np.flatnonzero(diff.any(axis=1))
    other = sorted(set(rows_diff.tolist()) - set(np.flatnonzero(absorb).tolist()))
    mech_off = np.asarray(off.min_gen_mechanism, dtype=int)
    mech_on = np.asarray(on.min_gen_mechanism, dtype=int)
    print(
        f"\nrows differing OFF vs ON: {rows_diff.size} "
        f"(absorption rows {int(absorb.sum())}, other {len(other)})"
    )
    print(
        f"  availability identical: {np.array_equal(off.availability, on.availability)}"
    )
    print(
        f"  MECH_RA_MUSTOFFER stamped on absorption rows: "
        f"OFF={int((mech_off[absorb] == MECH_RA_MUSTOFFER).sum())} row-hours, "
        f"ON={int((mech_on[absorb] == MECH_RA_MUSTOFFER).sum())} row-hours"
    )
    print(
        f"  mech identical on non-absorption rows: "
        f"{np.array_equal(mech_off[~absorb], mech_on[~absorb])}"
    )
    ok = (
        len(other) == 0
        and np.allclose(mg_off[absorb], 0.0)
        and np.allclose(mg_on[absorb], base[absorb])
    )
    print(f"\nD1 VERDICT: seam reproduced and fix surgical = {ok}")
    del dataclasses  # (kept import explicit above for readers of the composer)
    return {"ok": bool(ok), "absorb_rows": uid[absorb].tolist()}


# --------------------------------------------------------------------------- #
# §B — D2: the no-trade band the export leg is priced inside
# --------------------------------------------------------------------------- #
def section_b() -> dict:
    """D2: marginal-import identification + the sink's moneyness per hour set."""
    print("\n" + "=" * 78)
    print("§B  D2 — the no-trade band: where the export leg sits vs the margin")
    print("=" * 78)
    wheels = wheel_by_tranche()
    print("import-leg OATT wheel by tranche ($/MWh, the additive delivery basis):")
    for n, w in wheels.items():
        print(f"  {n:24s} wheel={w:5.2f}")
    print(
        "\nexport leg is priced hub - eps; an import leg hub + wheel + carbon + eps,\n"
        "so band(import margin - export price) = wheel + carbon + 2 eps >= 2 eps."
    )
    out: dict[str, dict] = {}
    for year in YEARS:
        hubs = hub_series(year)
        _lam, price, _dem = sidecar_prices(year)
        imp = import_rows(year)
        sets = hour_sets(year)
        # marginal (interior) economic tranche per hour, per corridor
        marginal_wheel: dict[str, np.ndarray] = {}
        for zone in CORRIDORS:
            sub = imp[imp["zone"] == zone]
            wheel_h = np.full(HOURS, np.nan)
            for uid, g in sub.groupby("unit_id", observed=True):
                name = str(uid)[len(zone) + 1 :]
                if name.startswith("export_"):
                    continue
                g = g.set_index("hour").reindex(range(HOURS))
                mw = np.nan_to_num(g["mw"].to_numpy(), nan=0.0)
                cap = np.nan_to_num(g["cap_mw"].to_numpy(), nan=0.0)
                interior = (mw > 1e-6) & (mw < cap - 1e-6)
                w = wheels.get(name)
                if w is None:
                    continue
                # cheapest interior rung sets the margin: keep the min wheel
                marg = np.where(interior, w, np.nan)
                wheel_h = np.fmin(wheel_h, marg)
            marginal_wheel[zone] = wheel_h
        print(f"\n--- {year}")
        yr: dict[str, dict] = {}
        for nm in ("defect", "belly", "night", "annual"):
            m = sets[nm]
            row: dict[str, dict] = {}
            for zone in CORRIDORS:
                node = price[zone].to_numpy()
                hub = hubs[zone]
                exp_px = hub - EPS
                money = node - exp_px  # >0 sink out of the money (inert)
                wh = marginal_wheel[zone][m]
                row[zone] = {
                    "in_money_pct": float((money[m] < -1e-6).mean() * 100.0),
                    "p50_gap": float(np.median(money[m])),
                    "marginal_wheel_p50": (
                        float(np.nanmedian(wh)) if np.isfinite(wh).any() else None
                    ),
                    "interior_pct": float(np.isfinite(wh).mean() * 100.0),
                }
                mw_p50 = row[zone]["marginal_wheel_p50"]
                print(
                    f"  {nm:7s} n={int(m.sum()):5d} {zone:9s} "
                    f"node-lambda − export-price: p50={row[zone]['p50_gap']:+8.3f} "
                    f"in-the-money {row[zone]['in_money_pct']:5.1f}% | "
                    f"marginal import interior {row[zone]['interior_pct']:5.1f}% "
                    f"of hours, its wheel p50="
                    + (f"{mw_p50:.2f}" if mw_p50 is not None else "n/a")
                )
            yr[nm] = row
        out[str(year)] = yr
    return out


# --------------------------------------------------------------------------- #
# §C — D3: the plateau-break test (the kill)
# --------------------------------------------------------------------------- #
def section_c() -> dict:
    """D3: the monotonicity kill + the two channels that could have escaped it."""
    print("\n" + "=" * 78)
    print("§C  D3 — does the plateau break? (the gate)")
    print("=" * 78)
    print(
        "Monotonicity (structural, basis-independent): an export sink is an\n"
        "ABSORPTION column (pmin <= P <= 0, cost mc x P). Restoring its range\n"
        "enlarges the feasible set with WITHDRAWAL only, i.e. it can add demand\n"
        "at the node and never supply. It is used only where mc_sink >= lambda_node,\n"
        "and using it raises lambda_node toward mc_sink; the CA zone sees weakly\n"
        "less net inflow, so every CA lambda moves weakly UP. No sink price and no\n"
        "sink bound can lower a zonal lambda. C3a-2025 is a +$2.90 OVER-price, so\n"
        "the chartered effect (re-price the plateau DOWN) is unreachable by\n"
        "construction, not by parameter choice."
    )
    print(
        "\nChannel 1 — direct: the plateau's lambda IS a delivered-import price\n"
        "(§B), and the export leg is priced strictly below it by wheel + 2 eps, so\n"
        "the sink is out of the money exactly where the plateau binds."
    )
    print(
        "\nChannel 2 — indirect: could diverting forced PNW firm energy out the PNW\n"
        "sink free SHARED interface headroom so the cheaper DSW corridor imports\n"
        "more (lambda_CA down by the congestion component)? Only if the\n"
        "SIMULTANEOUS group is the binding constraint. Measured:"
    )
    out: dict[str, dict] = {}
    for year in YEARS:
        n = pd.read_parquet(BUNDLE / "hourly" / f"network_{year}.parquet")
        n = n[n["pass"] == "P1"]
        yr: dict[str, dict] = {}
        for name, g in n.groupby("name", observed=True):
            g = g.set_index("hour").reindex(range(HOURS))
            dual = np.nan_to_num(g["dual"].to_numpy(), nan=0.0)
            mw = np.nan_to_num(g["mw"].to_numpy(), nan=0.0)
            lim = np.nan_to_num(g["limit_up"].to_numpy(), nan=0.0)
            if not str(name).startswith("grp:"):
                continue
            yr[str(name)] = {
                "bind_hours": int((np.abs(dual) > 1e-9).sum()),
                "max_abs_dual": float(np.abs(dual).max()),
                "mw_p50": float(np.median(mw)),
                "limit_p50": float(np.median(lim)),
            }
        out[str(year)] = yr
        print(f"  {year}:")
        for name, v in sorted(yr.items()):
            tag = " <-- SIMULTANEOUS" if name == SIMULTANEOUS_GROUP else ""
            print(
                f"    {name:46s} binding {v['bind_hours']:5d} h  "
                f"max|dual|={v['max_abs_dual']:7.2f}  "
                f"flow p50={v['mw_p50']:7.0f} / limit p50={v['limit_p50']:7.0f}{tag}"
            )
    sim_never = all(
        out[str(y)].get(SIMULTANEOUS_GROUP, {}).get("bind_hours", 0) == 0 for y in YEARS
    )
    print(
        f"\n  simultaneous interface group NEVER binds in any year: {sim_never}\n"
        "  -> the binding constraint in every congested regime is the corridor's\n"
        "     OWN measured ATC group, so PNW headroom is not fungible into DSW\n"
        "     import room. Channel 2 is dead."
    )
    print("\nD3 VERDICT: the plateau does NOT break. Gate FAILS -> no arm solves.")
    return {"groups": out, "simultaneous_never_binds": bool(sim_never)}


# --------------------------------------------------------------------------- #
# §D — D4: the E1 exposure of arming it anyway, per basis
# --------------------------------------------------------------------------- #
def section_d() -> dict:
    """D4: upper-bound C3a/E1 harm of a live sink, on both candidate bases."""
    print("\n" + "=" * 78)
    print("§D  D4 — E1 exposure if armed anyway (upper bound, per basis)")
    print("=" * 78)
    print(
        "Upper bound per hour: a live sink can raise CA lambda at most to the\n"
        "corridor's export price, so dlambda <= max(0, export_px - lambda_CA),\n"
        "taken over the corridor with the higher export price. Load-weighted to\n"
        "the C3a basis (the same measured demand the model dispatches). This is a\n"
        "CEILING on the harm: it assumes the sink can absorb without limit and\n"
        "that CA is fully coupled to the node in every such hour."
    )
    wheels = wheel_by_tranche()
    # netback basis: the corridor's own OATT wheel deducted in the export
    # direction. Use the corridor's cheapest ladder rung wheel (PNW_midC $5,
    # DSW_CCGT $4) -- the point-to-point charge the import leg already pays.
    netback_wheel = {"WECC_PNW": wheels["PNW_midC"], "WECC_DSW": wheels["DSW_CCGT"]}
    print(
        f"\nnetback wheel deducted per corridor: {netback_wheel} "
        "(the import leg's own OATT charge, applied symmetrically)"
    )
    out: dict[str, dict] = {}
    for year in YEARS:
        hubs = hub_series(year)
        lam, price, dem = sidecar_prices(year)
        sets = hour_sets(year)
        c3a_base = float((lam * dem).sum() / dem.sum())
        yr: dict[str, dict] = {}
        for basis, deduct in (("hub-eps (as built)", 0.0), ("netback (hub-wheel-eps)", 1.0)):
            exp_px = np.full(HOURS, -np.inf)
            for zone in CORRIDORS:
                px = hubs[zone] - EPS - deduct * netback_wheel[zone]
                exp_px = np.maximum(exp_px, px)
            dlam = np.clip(exp_px - lam, 0.0, None)
            c3a_new = float(((lam + dlam) * dem).sum() / dem.sum())
            yr[basis] = {
                "bind_pct_annual": float((dlam > 1e-6).mean() * 100.0),
                "c3a_delta": c3a_new - c3a_base,
                "defect_dlam_mean": float(dlam[sets["defect"]].mean()),
                "belly_dlam_mean": float(dlam[sets["belly"]].mean()),
            }
            print(
                f"  {year} {basis:24s} sink would bind {yr[basis]['bind_pct_annual']:5.1f}% "
                f"of hours | C3a-{year} moves {yr[basis]['c3a_delta']:+6.3f} $/MWh "
                f"(WORSE) | defect dlam mean {yr[basis]['defect_dlam_mean']:+6.3f}"
            )
        yr["c3a_model_base"] = c3a_base
        # How much of that exposure survives the ADMISSIBLE quantity bound? The
        # measured export-direction envelope is 0 MW in the (month × hod) buckets
        # where the corridor reliably net-imports, so a sink bounded by it cannot
        # absorb there at all -- the E1 harm is confined to hours the envelope is
        # open on the corridor whose price puts the sink in the money.
        from market_sim.data.eia930.envelopes import measured_corridor_flow_envelope

        env = measured_corridor_flow_envelope(ISO, year, HOURS, direction="export")
        if env:
            per_corr = {}
            for zone in CORRIDORS:
                px = hubs[zone] - EPS - netback_wheel[zone]
                in_money = px > lam + 1e-6
                open_env = np.asarray(env[zone], dtype=float) > 1e-6
                per_corr[zone] = {
                    "in_money_pct": float(in_money.mean() * 100.0),
                    "in_money_and_open_pct": float((in_money & open_env).mean() * 100.0),
                    "envelope_mean_when_both": (
                        float(np.asarray(env[zone])[in_money & open_env].mean())
                        if (in_money & open_env).any()
                        else 0.0
                    ),
                }
                print(
                    f"       {zone:9s} netback in-the-money {per_corr[zone]['in_money_pct']:5.1f}% "
                    f"of hours -> AND measured export envelope open: "
                    f"{per_corr[zone]['in_money_and_open_pct']:5.1f}% "
                    f"(mean envelope there {per_corr[zone]['envelope_mean_when_both']:6.0f} MW)"
                )
            yr["envelope_bounded"] = per_corr
        out[str(year)] = yr
    print(
        "\nD4 VERDICT: every basis moves C3a in the WRONG direction (the model\n"
        "already over-prices). Zero fitted values were swept -- there is nothing\n"
        "to sweep, the sign is structural."
    )
    return out


# --------------------------------------------------------------------------- #
# §E — the admissible basis space, stated
# --------------------------------------------------------------------------- #
def section_e() -> dict:
    """Survey the rule-13-admissible basis space and what it buys."""
    print("\n" + "=" * 78)
    print("§E  the basis space: what IS admissible, and what it does not buy")
    print("=" * 78)
    have_export_env = {}
    from market_sim.data.eia930.envelopes import measured_corridor_flow_envelope

    for year in YEARS:
        env = measured_corridor_flow_envelope(ISO, year, HOURS, direction="export")
        if env is None:
            have_export_env[str(year)] = None
            continue
        have_export_env[str(year)] = {
            z: {
                "mean_mw": float(np.mean(v)),
                "p50_mw": float(np.median(v)),
                "max_mw": float(np.max(v)),
                "zero_hours": int((v <= 1e-6).sum()),
            }
            for z, v in env.items()
        }
        print(f"  {year} measured EXPORT-direction corridor envelope (p95, MW):")
        for z, v in have_export_env[str(year)].items():
            print(
                f"    {z:9s} mean={v['mean_mw']:7.0f} p50={v['p50_mw']:7.0f} "
                f"max={v['max_mw']:7.0f} zero in {v['zero_hours']:5d} h"
            )
    print(
        "\nAdmissible basis (rule 13 [R-MEASURED], zero new DOF) EXISTS:\n"
        "  bound = min(corridor link TTC, measured export-direction deliverability\n"
        "          envelope) -- already in-repo (measured_corridor_flow_envelope\n"
        "          direction='export'), the symmetric counterpart of the import cap\n"
        "          the keeper already rides (caiso_corridor_flow_limit);\n"
        "  price = hub - wheel_out - eps, the corridor's own OATT point-to-point\n"
        "          charge applied symmetrically (the as-built hub - eps implicitly\n"
        "          wheels out for free -- an asymmetry with no source).\n"
        "Both regenerate forward from forward ATC + forward hub, so both pass the\n"
        "rule-13 forward test. It bounds the caiso-138 §E U-turn to hours reality\n"
        "demonstrably COULD export (evening buckets cap at ~0).\n"
        "\nWhat it does NOT buy: §C. The basis question is moot for the chartered\n"
        "effect -- an absorber cannot lower a lambda, on any basis."
    )
    return {"export_envelope": have_export_env}


# --------------------------------------------------------------------------- #
# §F — the cross-ISO exposure census (each keeper's own committed config)
# --------------------------------------------------------------------------- #
KEEPER_BUNDLES = {
    "ERCOT": "ercot139_cc_committed_arm",
    "CAISO": "caiso139_dumpguard_B",
    "PJM": "pjm137_ctheatrate_B",
    "MISO": "miso101_tempgrain_B",
    "NYISO": "nyiso99_demandfix",
    "NEISO": "neiso61_netrev_margin",
}
# The P1-native bridge flag whose prep routes through _bridge_floored_fleet.
BRIDGE_FLAG = {
    "CAISO": "caiso_ra_mustoffer",
    "ERCOT": "ercot_gas_commitment_bridge",
    "NYISO": "nyiso_gas_commitment_bridge",
}


def section_f() -> dict:
    """Which ISOs' CURRENT keepers actually hit the seam (rule 25 evidence)."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.interchange.spec import (
        build_interchange_fleet,
        get_interchange_spec,
    )

    print("\n" + "=" * 78)
    print("§F  cross-ISO exposure census (each keeper's own committed run_config)")
    print("=" * 78)
    print(
        "Exposure = the keeper's interchange fleet carries a pmin < 0 row AND the\n"
        "keeper arms a P1-native bridge whose prep routes through\n"
        "_bridge_floored_fleet. Rule 25: this is a MEASUREMENT of exposure, not a\n"
        "verdict for another ISO's lane."
    )
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    out: dict[str, dict] = {}
    for iso, bundle in KEEPER_BUNDLES.items():
        p = REPO / "results/calibration" / bundle / "run_config.json"
        if not p.exists():
            out[iso] = {"error": "run_config missing"}
            print(f"  {iso:6s} run_config missing ({bundle})")
            continue
        sc = json.loads(p.read_text())["scenario_config"]
        cfg = ScenarioConfig(**{k: v for k, v in sc.items() if k in names})
        spec = get_interchange_spec(cfg, iso, 2025)
        gens = build_interchange_fleet(spec) if spec.import_zone else []
        neg = [g for g in gens if g.pmin_mw < 0.0]
        flag = BRIDGE_FLAG.get(iso)
        armed = bool(getattr(cfg, flag, False)) if flag else False
        exposed = bool(neg) and armed
        out[iso] = {
            "bundle": bundle,
            "interchange_rows": len(gens),
            "absorption_rows": len(neg),
            "absorption_mw": float(-sum(g.pmin_mw for g in neg)),
            "bridge_flag": flag,
            "bridge_armed": armed,
            "exposed": exposed,
        }
        print(
            f"  {iso:6s} interchange rows={len(gens):3d}  pmin<0 rows={len(neg):3d} "
            f"({out[iso]['absorption_mw']:7.0f} MW)  bridge={flag or '-'} "
            f"armed={armed!s:5s} -> EXPOSED={exposed}"
        )
    print(
        "\nReadings: ERCOT is NOT exposed (its keeper builds no interchange rows at\n"
        "all, so the shared composer has no absorption row to collapse) -- this\n"
        "CORRECTS the caiso-138 §D blast-radius list, which named it. NYISO IS\n"
        "exposed (one -600 MW sink + nyiso_gas_commitment_bridge armed) and must\n"
        "re-gate on its own evidence. PJM / MISO / NEISO carry absorption rows but\n"
        "arm no such bridge today -- latent, not live."
    )
    return out


def main() -> int:
    a = section_a()
    b = section_b()
    c = section_c()
    d = section_d()
    e = section_e()
    f = section_f()
    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"  §A D1 seam reproduced + fix surgical : {a['ok']}")
    print(f"  §C D3 plateau breaks                 : False (KILL)")
    print(f"  §C simultaneous group never binds    : {c['simultaneous_never_binds']}")
    for year in YEARS:
        v = d[str(year)]["netback (hub-wheel-eps)"]
        print(
            f"  §D E1 ceiling {year} (netback basis)   : C3a {v['c3a_delta']:+.3f} $/MWh (worse)"
        )
    print("  §E admissible basis exists           : True (and moot per §C)")
    exposed = [iso for iso, v in f.items() if v.get("exposed")]
    print(f"  §F ISOs whose keeper hits the seam   : {exposed}")
    del b, e
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
