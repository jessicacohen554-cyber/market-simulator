"""Derive per-plant coal INCREMENTAL / AVERAGE heat-rate ratios from CAMPD CEMS.

The artifact behind ``ScenarioConfig.coal_econ_marginal_hr_two_sided`` (soco-81;
owner ruling 2026-09-27 on FINDING-soco-75 §6). A coal tranche is priced at
``plant average HR x band multiplier`` (``campd_coal_heat_rates_<ISO>.csv``,
``sum(heatInput)/sum(grossLoad)``), and the average carries the no-load heat of
the boiler. Above a measured must-run floor that heat is already sunk, so the
next MWh costs the unit's INCREMENTAL rate. This script measures that ratio per
plant-year.

Construction (FROZEN, rule 23 [R-FROZEN-DERIVE]; no new parameter):

* Unit-hours: CAMPD unit-level hourly for the ISO's states, coal
  ``primaryFuelInfo`` (the coal heat-rate derive's own token list), ``opTime >=
  0.99``, ``grossLoad > 0``, ``heatInput > 0`` and the implied hourly rate inside
  the coal HR artifact's physical band [8, 25] MMBtu/gross MWh. These are the
  same hours ``derive_campd_coal_heat_rates.py`` averages.
* Incremental HR per unit-year: ``derive_campd_marginal_hr.derive_unit_bands``
  unchanged (LSL/HSL = p3/p97, normalized-quadratic I/O fit, econ_low at x = 0.5,
  econ_high at x = 0.9) — the construction the registered class floor
  ``coal_econ_marginal_hr_bound`` already reads.
* Plant-year: generation-weighted over the plant's coal units, divided by the
  coal HR artifact's ``heat_rate_gross`` for the SAME plant-year. Both are gross,
  so the parasitic factor cancels and the ratio applies directly to the net
  average the tranche is priced at.
* ``year == 0`` (pooled, the forward construction, rule 13): the plain mean of
  the plant's ``ok`` year ratios — soco-75's pooled basis.

A plant-year is written only where the coal HR artifact carries that plant-year
(the fleet then pairs a year ratio with a year average, and a pooled ratio with a
pooled average). ``flag`` is ``ok`` when both ratios are finite, else ``no_fit``.

Scope (rule 25 [R-ISO-SCOPE]): ``ISO_SCOPE``. Each ISO derives its own artifact.

Usage::

    PYTHONPATH=src:scripts/data .venv/bin/python \
        scripts/data/derive_coal_incremental_hr_ratio.py --iso SOCO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive_campd_marginal_hr import UNIT_LEVEL_DIR, derive_unit_bands  # noqa: E402

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data.campd import states_for_iso  # noqa: E402

#: ISOs whose lane has derived and reviewed this artifact (rule 25).
ISO_SCOPE: tuple[str, ...] = ("SOCO",)

#: Coal fuel tokens: derive_campd_coal_heat_rates.py's list, verbatim.
COAL_TOKENS: tuple[str, ...] = (
    "coal",
    "bituminous",
    "lignite",
    "anthracite",
    "petroleum coke",
)
#: The coal HR artifact's per-hour physical band (MMBtu per gross MWh).
HR_BAND: tuple[float, float] = (8.0, 25.0)
#: derive_unit_bands NaNs a multiple outside (0, 5); dividing by 10 keeps coal
#: (~9-11 MMBtu/MWh) inside that window. It cancels exactly below (x BASE).
BASE = 10.0
YEARS: tuple[int, ...] = tuple(range(2019, 2026))


def load_unit_hours(iso: str, plants: set[int]) -> pd.DataFrame:
    """Steady-state coal unit-hours of ``plants`` over :data:`YEARS`."""
    cols = [
        "facilityId",
        "unitId",
        "grossLoad",
        "heatInput",
        "opTime",
        "primaryFuelInfo",
    ]
    frames = []
    for st in states_for_iso(iso):
        for y in YEARS:
            p = UNIT_LEVEL_DIR / f"{st}_{y}.parquet"
            if not p.exists():
                continue
            d = pd.read_parquet(p, columns=cols)
            d["facilityId"] = d["facilityId"].astype(int)
            d = d[d["facilityId"].isin(plants)]
            d["year"] = y
            frames.append(d)
    c = pd.concat(frames, ignore_index=True)
    fuel = c["primaryFuelInfo"].astype(str).str.lower()
    c = c[fuel.apply(lambda s: any(t in s for t in COAL_TOKENS))]
    op = (c["grossLoad"] > 0) & (c["heatInput"] > 0) & (c["opTime"] >= 0.99)
    c = c[op].copy()
    c["hr"] = c["heatInput"] / c["grossLoad"]
    return c[(c["hr"] >= HR_BAND[0]) & (c["hr"] <= HR_BAND[1])]


def derive(iso: str) -> pd.DataFrame:
    """Return the per-plant-year (and pooled) incremental/average ratio table."""
    art = pd.read_csv(PROCESSED_DIR / f"campd_coal_heat_rates_{iso}.csv")
    art = art[art["flag"].astype(str) == "ok"]
    avg = art.set_index(["plant_code", "year"])["heat_rate_gross"]
    names = art.groupby("plant_code")["plant_name"].first()
    c = load_unit_hours(iso, set(int(p) for p in art["plant_code"]))
    rows = []
    for (f, _uid, y), u in c.groupby(["facilityId", "unitId", "year"]):
        r = derive_unit_bands(u, BASE)
        if r is None:
            continue
        rows.append(
            {
                "plant_code": int(f),
                "year": int(y),
                "gross_mwh": float(u["grossLoad"].sum()),
                "marg_lo": r["marg_econ_low"] * BASE,
                "marg_hi": r["marg_econ_high"] * BASE,
            }
        )
    pu = pd.DataFrame(rows)
    out = []
    for (pc, y), g in pu.groupby(["plant_code", "year"]):
        if (pc, y) not in avg.index:
            continue
        rec = {
            "plant_code": pc,
            "year": y,
            "n_units": len(g),
            "gross_mwh": round(g["gross_mwh"].sum(), 1),
        }
        for k in ("marg_lo", "marg_hi"):
            m = g[k].notna()
            rec[k] = (
                float(np.average(g.loc[m, k], weights=g.loc[m, "gross_mwh"]))
                if m.any()
                else np.nan
            )
        rec["heat_rate_gross"] = float(avg[(pc, y)])
        rec["ratio_econ_low"] = rec["marg_lo"] / rec["heat_rate_gross"]
        rec["ratio_econ_high"] = rec["marg_hi"] / rec["heat_rate_gross"]
        out.append(rec)
    py = pd.DataFrame(out)
    ok = np.isfinite(py["ratio_econ_low"]) & np.isfinite(py["ratio_econ_high"])
    py["flag"] = np.where(ok, "ok", "no_fit")
    pooled = (
        py[py["flag"] == "ok"]
        .groupby("plant_code")
        .agg(
            n_units=("n_units", "max"),
            gross_mwh=("gross_mwh", "sum"),
            ratio_econ_low=("ratio_econ_low", "mean"),
            ratio_econ_high=("ratio_econ_high", "mean"),
        )
        .reset_index()
    )
    pooled["year"] = 0
    pooled["flag"] = "ok"
    tab = pd.concat([pooled, py], ignore_index=True)
    tab["plant_name"] = tab["plant_code"].map(names)
    tab["iso"] = iso
    tab["source"] = (
        "CAMPD unit-level hourly (opTime>=0.99, coal primaryFuelInfo, hourly HR in "
        "[8,25]); incremental HR = derive_campd_marginal_hr.derive_unit_bands "
        "(p3/p97, normalized quadratic, econ_low x=0.5 / econ_high x=0.9), "
        "gen-weighted over units; / campd_coal_heat_rates heat_rate_gross of the "
        "same plant-year; year 0 = mean of ok year ratios"
    )
    cols = [
        "plant_code",
        "year",
        "plant_name",
        "n_units",
        "gross_mwh",
        "marg_lo",
        "marg_hi",
        "heat_rate_gross",
        "ratio_econ_low",
        "ratio_econ_high",
        "flag",
        "iso",
        "source",
    ]
    tab = tab.reindex(columns=cols).sort_values(["plant_code", "year"])
    for k in (
        "marg_lo",
        "marg_hi",
        "heat_rate_gross",
        "ratio_econ_low",
        "ratio_econ_high",
    ):
        tab[k] = tab[k].round(4)
    return tab


def main(argv: list[str] | None = None) -> int:
    """CLI entry: write ``coal_incremental_hr_ratio_<ISO>.csv``."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    a = ap.parse_args(argv)
    iso = a.iso.upper()
    if iso not in ISO_SCOPE:
        raise SystemExit(f"{iso} is not in ISO_SCOPE {ISO_SCOPE} (rule 25)")
    tab = derive(iso)
    out = PROCESSED_DIR / f"coal_incremental_hr_ratio_{iso}.csv"
    tab.to_csv(out, index=False)
    print(tab.drop(columns=["source"]).to_string(index=False))
    print(f"wrote {out} ({len(tab)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
