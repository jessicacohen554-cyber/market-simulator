"""Two follow-ups that decide which lever the nyiso-96 characterisation licenses.

``nyiso96_ct_start_characterization`` establishes that the NYISO CT_PEAKER
fleet's missing starts are 82-88 % in hours the model prices BELOW the plant's
own SRMC, and that the measured below-SRMC energy is spread flat rather than
concentrated. Two objections have to be closed before that reading can carry a
lever choice:

**A. Is the below-SRMC result an artifact of the HUB price?** The scored LMP
series is the 11-zone NYISO hub, but the peaker fleet sits in NYC (Zone J) and
Long Island (Zone K), which price above it. If the locational premium is large
enough, the fleet might be earning its cost after all. This re-runs the
below-SRMC share on the hub price PLUS the measured zonal premium, taken from
the raw 5-minute RTD zonal files on disk (no network fetch) — so the headline is
stated against the price the fleet actually sees, not the one it is scored on.

**B. Does the model OFFER its CTs above their own SRMC?** The keeper prices
CT_PEAKER through ``offer_curve_by_group`` multipliers (committed 1.35, peak
4.0) on top of the measured heat rate. If those multipliers put the fleet's bid
well above its fuel cost, then the 12-18 % "model priced above SRMC" bucket is
not a puzzle — the model declined starts it could afford because its own bid,
not its cost, was the binding number. This reads each tranche's REVEALED offer
straight from the keeper's sidecars: the tranche's dispatch is a step function
of the zonal price, so the price band between "highest price at which it stayed
off" and "lowest price at which it ran" brackets the mc the LP charged it.
Reported against the same measured SRMC, per tranche, capacity-weighted.

Both read only committed artifacts. No LP is solved and no measured outcome
enters any model input.

Usage::

    python scripts/probes/nyiso96_ct_offer_reveal.py --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import collections
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.nyiso88_peaker_economics import (  # noqa: E402
    downstate_ct_gas_hourly,
)
from scripts.probes.nyiso96_ct_start_characterization import (  # noqa: E402
    LMP_PATH,
    measured_loaded_heat_rate_table,
    model_fleet_view,
    model_zone_price,
)
from scripts.legitimacy_diagnostics import load_bench  # noqa: E402

#: Model zone -> the zonal name used in the raw NYISO RTD zonal files.
ZONE_TO_RTD = {"NYC": "N.Y.C.", "Long_Island": "LONGIL"}


def zonal_premium(year: int) -> dict[str, float]:
    """Return measured {model zone: mean $/MWh premium over the 11-zone mean}.

    Only the months present in ``data/raw/lmp-data/NYISO/`` are used. The
    archive is partial (a summer and a winter sample in most years), so this is
    reported as a SAMPLE premium and used to bound the hub-vs-zonal objection,
    never as an hourly series.
    """
    prem: dict[str, list[float]] = collections.defaultdict(list)
    for path in sorted((REPO / "data/raw/lmp-data/NYISO").glob(
            f"{year}*realtime_zone_csv.zip")):
        zf = zipfile.ZipFile(path)
        df = pd.concat([pd.read_csv(io.BytesIO(zf.read(n))) for n in zf.namelist()])
        df.columns = [c.strip() for c in df.columns]
        price_col = next(c for c in df.columns if "LBMP" in c.upper())
        name_col = next(c for c in df.columns if "Name" in c)
        df["t"] = pd.to_datetime(df[df.columns[0]])
        wide = df.groupby(["t", name_col])[price_col].mean().unstack()
        mean11 = wide.mean(axis=1)
        for model_zone, rtd in ZONE_TO_RTD.items():
            if rtd in wide.columns:
                prem[model_zone].append(float((wide[rtd] - mean11).mean()))
    return {z: round(float(np.mean(v)), 2) for z, v in prem.items() if v}


def part_a(year: int) -> dict:
    """Return the below-SRMC share at hub price and at hub + zonal premium."""
    pure, _model_hr, vom = model_fleet_view(year)
    meas_hr = measured_loaded_heat_rate_table("NYISO")
    bench = load_bench(REPO, "NYISO", year)
    gas_by_zone = downstate_ct_gas_hourly(year) or {}
    prem = zonal_premium(year)

    lmp = pd.read_parquet(LMP_PATH)
    lmp = lmp[lmp["year"] == year].sort_values("hour")
    rt = lmp["rt"].to_numpy(dtype=float)[:8760]

    tot = below_hub = below_zonal = 0.0
    n_plants = 0
    for pid, rec in bench.items():
        code = int(str(pid).split(":")[0])
        if rec["group"] != "CT_PEAKER" or pure.get(code) != "CT_PEAKER":
            continue
        hr = meas_hr.get(code)
        zone = str(rec.get("zone") or "")
        gas = gas_by_zone.get(zone)
        if gas is None and gas_by_zone:
            gas = np.mean(list(gas_by_zone.values()), axis=0)
        if hr is None or gas is None:
            continue
        mw = np.asarray(rec["mw"], dtype=float)[:8760]
        if mw.sum() <= 0:
            continue
        srmc = gas * hr + vom
        # The premium is a per-zone mean over the sampled months; adding it to
        # the hub series is a LEVEL correction, deliberately not a shape claim.
        px_zonal = rt + prem.get(zone, 0.0)
        tot += float(mw.sum())
        below_hub += float(mw[(mw > 0) & (rt < srmc)].sum())
        below_zonal += float(mw[(mw > 0) & (px_zonal < srmc)].sum())
        n_plants += 1

    return {
        "plants": n_plants,
        "zonal_premium_sample_usd_mwh": prem,
        "measured_twh": round(tot / 1e6, 3),
        "energy_share_below_srmc_hub": round(below_hub / max(1e-9, tot), 4),
        "energy_share_below_srmc_zonal": round(below_zonal / max(1e-9, tot), 4),
    }


def part_b(bundle: Path, year: int) -> dict:
    """Return each CT_PEAKER tranche's REVEALED model offer vs measured SRMC."""
    df = pd.read_parquet(bundle / "hourly" / f"unit_hourly_{year}.parquet")
    df = df[df["plant_group"] == "CT_PEAKER"]
    df["plant_code"] = df["plant_code"].astype(int)
    prices = model_zone_price(bundle, year)
    meas_hr = measured_loaded_heat_rate_table("NYISO")
    _pure, _hr, vom = model_fleet_view(year)
    gas_by_zone = downstate_ct_gas_hourly(year) or {}

    by_tranche: dict[str, list[tuple[float, float, float]]] = collections.defaultdict(list)
    for (code, unit), g in df.groupby(["plant_code", "unit_id"], observed=True):
        zone = str(g["zone"].iloc[0])
        px = prices.get(zone)
        hr = meas_hr.get(int(code))
        gas = gas_by_zone.get(zone)
        if gas is None and gas_by_zone:
            gas = np.mean(list(gas_by_zone.values()), axis=0)
        if px is None or hr is None or gas is None:
            continue
        s = g.groupby("hour")["mw"].sum()
        mw = np.zeros(8760)
        mw[s.index.to_numpy()] = s.to_numpy()
        cap = float(g["cap_mw"].iloc[0])
        on = mw > max(0.5, 0.01 * cap)
        if not on.any():
            continue
        # HOUR-MATCHED, never a percentile against a mean: an affordable hour is
        # one where the model's OWN zonal price covers the plant's measured
        # SRMC in THAT hour. The capture rate — how many affordable hours the
        # tranche actually produced in — is the direct read of whether the
        # model's bid sits above its cost. A tranche bidding at SRMC captures
        # ~everything; a tranche bidding at 1.35x or 4x its SRMC captures little.
        srmc_h = gas * hr + vom
        affordable = px >= srmc_h
        # Revealed offer: the price the tranche's own dispatch switches on at,
        # read as the 5th percentile of the prices it DID run at (robust to a
        # single degenerate hour), reported beside the SRMC of those SAME hours.
        revealed = float(np.percentile(px[on], 5))
        srmc_on = float(np.average(srmc_h, weights=mw))
        tranche = str(unit).rsplit("_", 1)[-1]
        by_tranche[tranche].append((
            revealed, srmc_on, cap,
            int(affordable.sum()), int((affordable & on).sum()), int(on.sum()),
        ))

    out = {}
    for tranche, rows in sorted(by_tranche.items()):
        rev = np.array([r[0] for r in rows])
        srm = np.array([r[1] for r in rows])
        cap = np.array([r[2] for r in rows])
        aff = np.array([r[3] for r in rows], dtype=float)
        cap_h = np.array([r[4] for r in rows], dtype=float)
        on_h = np.array([r[5] for r in rows], dtype=float)
        out[tranche] = {
            "n_tranches": len(rows),
            "cap_mw": round(float(cap.sum()), 1),
            "revealed_offer_usd_mwh": round(float(np.average(rev, weights=cap)), 2),
            "srmc_of_run_hours_usd_mwh": round(float(np.average(srm, weights=cap)), 2),
            "affordable_hours": int(aff.sum()),
            "run_hours": int(on_h.sum()),
            "affordable_and_run_hours": int(cap_h.sum()),
            # The decisive number: share of hours the model could afford this
            # tranche in which it actually produced.
            "capture_rate": round(float(cap_h.sum() / max(1.0, aff.sum())), 4),
            # Complement: share of its run hours that were NOT affordable (the
            # tranche running below the plant's measured SRMC — the model doing
            # what the real fleet does).
            "run_hours_below_srmc_share": round(
                float((on_h.sum() - cap_h.sum()) / max(1.0, on_h.sum())), 4),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """Print both follow-ups for each year."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path,
                   default=REPO / "results/calibration/nyiso92_hydro_envfloor")
    p.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    p.add_argument("--json-out", type=Path)
    args = p.parse_args(argv)

    out: dict = {"years": {}}
    for year in args.years:
        a = part_a(year)
        b = part_b(args.bundle, year)
        out["years"][str(year)] = {"A_locational": a, "B_revealed_offer": b}
        print(f"\n{'=' * 72}\n{year}\n{'=' * 72}")
        print(f"[A] zonal premium sample {a['zonal_premium_sample_usd_mwh']}")
        print(f"    below-SRMC energy share  hub {a['energy_share_below_srmc_hub']}"
              f"   zonal {a['energy_share_below_srmc_zonal']}"
              f"   ({a['plants']} plants, {a['measured_twh']} TWh)")
        print("[B] hour-matched capture of affordable hours, by tranche:")
        for t, d in b.items():
            print(f"    {t:10s} cap {d['cap_mw']:7.1f} MW   affordable_h "
                  f"{d['affordable_hours']:6d}   run_h {d['run_hours']:6d}   "
                  f"CAPTURE {d['capture_rate']:.3f}   "
                  f"run-h below srmc {d['run_hours_below_srmc_share']:.3f}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
