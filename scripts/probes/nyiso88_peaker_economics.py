"""Test whether NYISO's real peaker fleet runs on ENERGY economics at all.

The nyiso-88 charter asks for "a REAL reason to run" for the NYISO CT_PEAKER
class, whose level collapsed to 0.46 TWh against a ~2.3 TWh actual once the
owner-adjudicated-inaccurate h14-21 boxcar was removed (nyiso-87). It names
three admissible directions and tells this session to test direction (c) —
"if peak prices formed correctly, peakers would clear economically" — FIRST,
because a positive result would make the other two unnecessary.

``nyiso88_peaker_price_coupling.py`` refutes (c) on the model's own offer
surface (a maximally-generous peak-price uplift recovers only 12-17 % of the
gap). This probe asks the complementary, model-free question directly of the
MEASURED market:

    At what actual NYISO price does the real downstate peaker fleet produce
    its energy, and how does that compare with its own fuel-based SRMC?

If the fleet earns above SRMC, the residual is a merit-order/price-formation
problem and belongs to the offer curves. If it produces the bulk of its energy
BELOW its own SRMC, then no price-formation or heat-rate fix can reach it — the
fleet is running for a non-energy reason (commitment obligation, synchronized
reserve, regulation, local reliability), which is the charter's direction (a).

Everything is read from committed artifacts and measured sources (rule 14):

* the committed CAMPD bench (``frontend/data/backcast/bench/NYISO/<year>.json.gz``)
  for the plant-level actual the D-1 gate itself scores against,
* the model fleet's own class assignment, to restrict to PURE combustion-turbine
  plants (no steam or combined-cycle units) so no mixed-plant attribution
  question contaminates the series,
* ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`` — the scored
  NYISO DA/RT hub price,
* the KEEPER's OWN downstate-CT delivered-gas seam — the per-zone
  ``nyiso-downstate-gas`` daily index (``nyiso_downstate_ct_gas_daily``), so the
  SRMC the fleet is judged against is the very cost the LP charges it. Using the
  superseded statewide firm city-gate stand-in instead overstates that cost by
  ~$15-22/MWh and manufactures a spurious uneconomic-dispatch result; see
  :func:`downstate_ct_gas_hourly`.

No LP is solved and no measured outcome enters any model input — this is
scoring-side characterisation only.

CLOCK: the committed bench series and the committed LMP parquet share the
model's non-leap 8760 local-standard clock, so they are index-aligned with no
remap (contrast ``nyiso85_tail_anatomy._utc_of_hour``, needed only when joining
to wall-clock sources such as the raw CAMPD files).

Usage::

    python scripts/probes/nyiso88_peaker_economics.py --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402
from scripts.legitimacy_diagnostics import load_bench  # noqa: E402

PEAKER_CLASS = "CT_PEAKER"

#: Committed NYISO hub DA/RT hourly price (the C-criteria scoring series).
LMP_PATH = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"

#: Variable O&M for a gas combustion turbine ($/MWh) — the model's own value,
#: read from the fleet so the SRMC below is the LP's cost, not a new number.
_FALLBACK_VOM = 5.0


def pure_ct_plants(year: int) -> tuple[set[int], float]:
    """Return (plant codes whose model units are ALL CT_PEAKER, their VOM).

    Restricting to pure-CT plants removes every mixed steam/CC facility, so the
    plant-level CEMS series used below is unambiguously combustion-turbine
    energy and the result cannot be an artifact of how a mixed plant is
    attributed to a class.
    """
    gens = load_fleet_from_csv("NYISO", get_iso_config("NYISO"), year=year)
    classes: dict[int, set[str]] = collections.defaultdict(set)
    voms: list[float] = []
    for g in gens:
        code = int(getattr(g, "plant_code", 0) or 0)
        group = getattr(g, "plant_group", "") or ""
        if code and group:
            classes[code].add(group)
        if group == PEAKER_CLASS:
            voms.append(float(getattr(g, "vom", 0.0) or 0.0))
    pure = {code for code, cls in classes.items() if cls == {PEAKER_CLASS}}
    vom = float(np.median(voms)) if voms else _FALLBACK_VOM
    return pure, vom


def measured_loaded_heat_rate(year: int, plants: set[int]) -> float:
    """Return the fleet gen-weighted LOADED heat rate (MMBtu/MWh) from CAMPD.

    Per unit, the heat rate is taken over hours at or above 80 % of that unit's
    p95 gross load — the loaded (near-full-output) rate that sets an offer,
    rather than the annual average that blends in part-load and startup fuel.
    NYISO's downstate peaker fleet spans NY and NJ state files (Bayonne Energy
    Center is physically in NJ and delivers into Zone J over a dedicated tie).
    """
    frames = []
    for state in ("NY", "NJ"):
        path = REPO / f"data/raw/campd-unit-level/{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path, columns=["facilityId", "unitId", "unitType", "grossLoad", "heatInput"]
        )
        frames.append(df[df["unitType"] == "Combustion turbine"])
    if not frames:
        return float("nan")
    df = pd.concat(frames)
    df["facilityId"] = df["facilityId"].astype(int)
    df = df[df["facilityId"].isin(plants)].dropna(subset=["grossLoad", "heatInput"])
    df = df[(df["grossLoad"] > 0) & (df["heatInput"] > 0)]
    num = den = 0.0
    for _, g in df.groupby(["facilityId", "unitId"]):
        cap = g["grossLoad"].quantile(0.95)
        hi = g[g["grossLoad"] >= 0.8 * cap]
        if len(hi) < 50:
            continue
        mwh = float(g["grossLoad"].sum())
        num += mwh * float(hi["heatInput"].sum() / hi["grossLoad"].sum())
        den += mwh
    return num / den if den > 0 else float("nan")


def downstate_ct_gas_hourly(year: int) -> dict[str, np.ndarray] | None:
    """Return the KEEPER's own downstate-CT delivered gas ($/MMBtu) per zone.

    This must be the seam the keeper actually runs, or the SRMC below is not the
    cost the LP charges. The NYISO keeper sets ``nyiso_downstate_ct_gas_daily``
    (and ``nyiso_downstate_ct_gas_basis=False``), so a downstate CT_PEAKER's
    delivered index is the curated per-zone ``nyiso-downstate-gas`` daily series
    — measured Transco Zone 6 NY daily spot plus the measured monthly LDC
    NON-FIRM TRANSPORTATION rate for that unit's zone (KEDNY SC-22 for NYC,
    KEDLI SC-19 for Long Island; nyiso-55 / gap G-13).

    The superseded monthly construction (``nyiso_downstate_ct_gas_premium``, the
    statewide EIA N3050NY3 FIRM city-gate stand-in) runs ~$1.5-2.3/MMBtu dearer
    and is NOT what the keeper prices — using it would overstate peaker SRMC by
    ~$15-22/MWh and manufacture an uneconomic-dispatch result. Returns ``None``
    when the curated series is unavailable.
    """
    try:
        from market_sim.data.fuel.basis.nyiso import (
            _downstate_delivered_gas_hourly_by_zone,
        )

        by_zone = _downstate_delivered_gas_hourly_by_zone("NYISO", year, 8760)
    except Exception:
        return None
    if not by_zone:
        return None
    return {z: np.asarray(a, dtype=float)[:8760] for z, a in by_zone.items()}


def measured_locational_premium(year: int) -> dict[str, float]:
    """Return measured {zone: mean $/MWh premium over the 11-zone mean}.

    The SRMC comparison below uses the committed NYISO HUB series (the 11-zone
    mean the C criteria score against), while the peaker fleet sits in NYC
    (Zone J) and Long Island (Zone K), which price above it. This measures that
    premium directly from the raw 5-minute zonal RTD files on disk, so the
    conclusion can be checked against the locational price the fleet actually
    sees rather than asserted to be robust.

    Only the months present in ``data/raw/lmp-data/NYISO/`` are used (no network
    fetch); for 2023 that is June and December — a summer and a winter sample.
    Returns ``{}`` when no zonal file for *year* is on disk.
    """
    import io
    import zipfile

    lmp_dir = REPO / "data/raw/lmp-data/NYISO"
    prem: dict[str, list[float]] = collections.defaultdict(list)
    for path in sorted(lmp_dir.glob(f"{year}*realtime_zone_csv.zip")):
        zf = zipfile.ZipFile(path)
        df = pd.concat([pd.read_csv(io.BytesIO(zf.read(n))) for n in zf.namelist()])
        df.columns = [c.strip() for c in df.columns]
        price_col = next(c for c in df.columns if "LBMP" in c.upper())
        name_col = next(c for c in df.columns if "Name" in c)
        df["t"] = pd.to_datetime(df[df.columns[0]])
        wide = df.groupby(["t", name_col])[price_col].mean().unstack()
        mean11 = wide.mean(axis=1)
        for zone in ("N.Y.C.", "LONGIL"):
            if zone in wide.columns:
                prem[zone].append(float((wide[zone] - mean11).mean()))
    return {z: round(float(np.mean(v)), 2) for z, v in prem.items()}


def heat_rate_bias(year: int, plants: set[int], vom: float) -> dict:
    """Return the model-vs-measured heat-rate bias and its $/MWh cost effect.

    The model's non-ERCOT fleet carries an eGRID **plant-average annual** heat
    rate, identical across every generator of a plant. For a low-capacity-factor
    peaker that average is not the rate that sets an offer, and at a mixed
    steam/CT facility it is not even the right technology's rate. This compares
    it with the CAMPD unit-level LOADED rate (:func:`measured_loaded_heat_rate`)
    and converts the difference to $/MWh at the keeper's own delivered gas — the
    amount by which the LP over- or under-charges the fleet's marginal cost.
    """
    gens = load_fleet_from_csv("NYISO", get_iso_config("NYISO"), year=year)
    weighted: dict[int, list[float]] = collections.defaultdict(lambda: [0.0, 0.0])
    for g in gens:
        if (getattr(g, "plant_group", "") or "") != PEAKER_CLASS:
            continue
        code = int(getattr(g, "plant_code", 0) or 0)
        pmax = float(getattr(g, "pmax_mw", 0.0) or 0.0)
        weighted[code][0] += pmax * float(getattr(g, "heat_rate", 0.0) or 0.0)
        weighted[code][1] += pmax
    model_hr = {k: v[0] / v[1] for k, v in weighted.items() if v[1] > 0}

    bench = load_bench(REPO, "NYISO", year)
    gas_by_zone = downstate_ct_gas_hourly(year) or {}
    num_m = num_x = den = gas_w = 0.0
    n = 0
    for pid, rec in bench.items():
        if rec["group"] != PEAKER_CLASS or int(pid) not in plants:
            continue
        hr_meas = measured_loaded_heat_rate(year, {int(pid)})
        hr_model = model_hr.get(int(pid))
        series = np.asarray(rec["mw"], dtype=float)[:8760]
        if not np.isfinite(hr_meas) or hr_model is None or series.sum() <= 0:
            continue
        w = float(series.sum())
        gas = gas_by_zone.get(str(rec.get("zone")))
        if gas is None and gas_by_zone:
            gas = np.mean(list(gas_by_zone.values()), axis=0)
        num_m += w * hr_meas
        num_x += w * hr_model
        gas_w += w * float(np.average(gas, weights=series)) if gas is not None else 0.0
        den += w
        n += 1
    if den <= 0:
        return {}
    hr_meas_f, hr_model_f, gas_f = num_m / den, num_x / den, gas_w / den
    return {
        "plants": n,
        "model_heat_rate": round(hr_model_f, 2),
        "measured_loaded_heat_rate": round(hr_meas_f, 2),
        "ratio": round(hr_model_f / hr_meas_f, 3),
        "delivered_gas": round(gas_f, 2),
        "srmc_bias_usd_mwh": round((hr_model_f - hr_meas_f) * gas_f, 2),
    }


def analyse(year: int) -> dict:
    """Return the measured price-vs-SRMC statistics for one year."""
    pure, vom = pure_ct_plants(year)
    bench = load_bench(REPO, "NYISO", year)
    gas_by_zone = downstate_ct_gas_hourly(year)
    mw = np.zeros(8760)
    # Fuel cost is per-zone (the LI gas island and the NYC system carry
    # materially different LDC transport rates), so the fleet SRMC is built as
    # the generation-weighted sum of each plant's own zonal delivered index
    # rather than one statewide number.
    fuel_cost = np.zeros(8760)
    cap = 0.0
    used: set[int] = set()
    hr_fleet = measured_loaded_heat_rate(year, pure)
    for pid, rec in bench.items():
        if rec["group"] != PEAKER_CLASS or int(pid) not in pure:
            continue
        plant_mw = np.asarray(rec["mw"], dtype=float)[:8760]
        mw += plant_mw
        cap += float(rec["npl"])
        used.add(int(pid))
        if gas_by_zone:
            gas = gas_by_zone.get(str(rec.get("zone")))
            if gas is None:
                gas = np.mean(list(gas_by_zone.values()), axis=0)
            hr_p = measured_loaded_heat_rate(year, {int(pid)})
            if not np.isfinite(hr_p):
                hr_p = hr_fleet
            fuel_cost += plant_mw * (gas * hr_p + vom)

    lmp = pd.read_parquet(LMP_PATH)
    lmp = lmp[lmp["year"] == year].sort_values("hour")
    da = lmp["da"].to_numpy(dtype=float)[:8760]
    rt = lmp["rt"].to_numpy(dtype=float)[:8760]

    hr = hr_fleet
    # Generation-weighted fleet SRMC per hour (undefined where nothing runs).
    srmc = np.divide(fuel_cost, mw, out=np.zeros(8760), where=mw > 0) if gas_by_zone else None

    total = float(mw.sum())
    out: dict = {
        "year": year,
        "plants": len(used),
        "capacity_mw": round(cap),
        "actual_twh": round(total / 1e6, 3),
        "hours_online": int((mw > 1.0).sum()),
        "mean_mw_when_online": round(float(mw[mw > 1.0].mean()), 1) if total else 0.0,
        "measured_loaded_heat_rate": round(hr, 2),
        "vom": round(vom, 2),
        "energy_wtd_da_when_running": round(float(np.average(da, weights=mw)), 2),
        "energy_wtd_rt_when_running": round(float(np.average(rt, weights=mw)), 2),
        "all_hours_mean_da": round(float(da.mean()), 2),
    }
    if srmc is not None:
        out["energy_wtd_srmc_when_running"] = round(float(np.average(srmc, weights=mw)), 2)
        below = mw[(da < srmc)].sum()
        out["energy_below_own_srmc_twh"] = round(float(below) / 1e6, 3)
        out["energy_below_own_srmc_share"] = round(float(below) / total, 3)
        margin = da - srmc
        out["energy_wtd_da_minus_srmc"] = round(float(np.average(margin, weights=mw)), 2)
    bands = []
    for lo, hi in ((0, 20), (20, 30), (30, 40), (40, 50), (50, 60), (60, 80), (80, 120), (120, 1e9)):
        sel = (da >= lo) & (da < hi)
        bands.append(
            {
                "da_band": f"{lo}-{hi if hi < 1e9 else '+'}",
                "hours": int(sel.sum()),
                "twh": round(float(mw[sel].sum()) / 1e6, 3),
                "share": round(float(mw[sel].sum()) / total, 3) if total else 0.0,
            }
        )
    out["energy_by_actual_da_band"] = bands
    # Robustness: the margin above is against the 11-zone HUB. If the measured
    # NYC/LI premium exceeded the shortfall, the fleet could still be in-merit
    # locationally and the conclusion would not hold.
    out["measured_locational_premium"] = measured_locational_premium(year)
    # The model's own cost error on this fleet, for comparison with the margin
    # above: if the bias exceeds the margin the fleet actually earns, the LP
    # cannot clear it and no new market mechanism is needed to explain that.
    out["heat_rate_bias"] = heat_rate_bias(year, pure, vom)
    return out


def main(argv: list[str] | None = None) -> int:
    """Run the economics probe and print/emit the per-year statistics."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)

    rows = [analyse(y) for y in args.years]
    for r in rows:
        print(json.dumps({k: v for k, v in r.items() if k != "energy_by_actual_da_band"}, indent=2))
        print("  energy by actual DA band:")
        for b in r["energy_by_actual_da_band"]:
            print(f"    ${b['da_band']:<9} {b['hours']:>5} h  {b['twh']:>6.3f} TWh ({b['share']:>6.1%})")
        print()
    print("--- summary: does the real peaker fleet earn its own SRMC? ------")
    print(f"{'year':>6} {'TWh':>7} {'DA when running':>16} {'own SRMC':>10} {'margin':>8} {'% below SRMC':>13}")
    for r in rows:
        print(
            f"{r['year']:>6} {r['actual_twh']:>7.2f} {r['energy_wtd_da_when_running']:>16.2f} "
            f"{r.get('energy_wtd_srmc_when_running', float('nan')):>10.2f} "
            f"{r.get('energy_wtd_da_minus_srmc', float('nan')):>8.2f} "
            f"{r.get('energy_below_own_srmc_share', float('nan')):>12.1%}"
        )
    print()
    print("--- the model's own cost error on the same fleet -----------------")
    print(f"{'year':>6} {'model HR':>9} {'measured HR':>12} {'ratio':>7} {'SRMC bias':>10} {'fleet margin':>13}")
    for r in rows:
        b = r.get("heat_rate_bias") or {}
        if not b:
            continue
        print(
            f"{r['year']:>6} {b['model_heat_rate']:>9.2f} {b['measured_loaded_heat_rate']:>12.2f} "
            f"{b['ratio']:>7.3f} {b['srmc_bias_usd_mwh']:>+10.2f} "
            f"{r.get('energy_wtd_da_minus_srmc', float('nan')):>+13.2f}"
        )
    if args.json_out:
        args.json_out.write_text(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
