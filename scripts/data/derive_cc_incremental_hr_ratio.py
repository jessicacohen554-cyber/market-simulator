"""Derive per-plant CC_REGULAR INCREMENTAL / AVERAGE heat-rate ratios from CAMPD CEMS.

The artifact behind ``ScenarioConfig.cc_econ_incremental_hr`` (closeout-CAISO-w8;
desk GO 2026-10-05). The combined-cycle sibling of
``derive_coal_incremental_hr_ratio.py`` (soco-81), built on the identical
identification. A CC_REGULAR tranche is priced at ``plant AVERAGE operating HR x
band multiplier`` (``campd_cc_heat_rates_<ISO>.csv``: sum(heatInput) /
sum(grossLoad) over the plant's steady CC hours). The average carries the
unit's no-load heat. Once the unit is committed, that heat is sunk in its
committed (min-load) tranche, so each MWh above it costs the INCREMENTAL rate,
which this script measures per plant-year.

Construction (FROZEN, rule 23 [R-FROZEN-DERIVE]; no new parameter):

* Unit-hours: ``derive_campd_cc_heat_rates._campd_cc_hours`` unchanged (CAMPD
  unit-level hourly, ``unitType`` combined cycle, the CEMS-to-EIA split-plant
  remap applied before the fleet filter), then the CC deriver's own steady
  screen: ``opTime >= _MIN_OPTIME``, ``grossLoad > 0``, ``heatInput > 0`` and
  the implied hourly rate inside ``[_HR_MIN_GROSS, _HR_MAX_GROSS]``.
* Incremental HR per unit-year: ``derive_campd_marginal_hr.derive_unit_bands``
  unchanged (LSL/HSL = p3/p97, normalized-quadratic I/O fit, econ_low at
  x = 0.5, econ_high at x = 0.9), the construction the coal ratio reads.
* Plant-year: generation-weighted over the plant's CC units, divided by the CC
  HR artifact's ``heat_rate_gross`` for the SAME plant-year. Both are gross on
  the same CEMS units, so the parasitic factor and any steam-turbine boundary
  scaling cancel, and the ratio applies directly to the net average the tranche
  is priced at.
* ``year == 0`` (pooled, the forward construction, rule 13): the plain mean of
  the plant's ``ok`` year ratios.

A plant-year is written only where the CC HR artifact carries that plant-year
with ``flag == ok``. ``flag`` is ``ok`` when both ratios are finite and inside
(0.5, 1.2), else ``no_fit``.

Source: EPA CAMPD unit-level hourly emissions (``data/raw/campd-unit-level/``,
``scripts/data/fetch_campd_unit_level.py``), already committed for CA 2019–2026.

Scope (rule 25 [R-ISO-SCOPE]): ``ISO_SCOPE``. Each ISO derives its own artifact.

Usage::

    PYTHONPATH=src:scripts/data uv run python \
        scripts/data/derive_cc_incremental_hr_ratio.py --iso CAISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive_campd_cc_heat_rates import (  # noqa: E402
    _HR_MAX_GROSS,
    _HR_MIN_GROSS,
    _MIN_OPTIME,
    _campd_cc_hours,
)
from derive_campd_marginal_hr import derive_unit_bands  # noqa: E402

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402

#: ISOs whose lane has derived and reviewed this artifact (rule 25).
ISO_SCOPE: tuple[str, ...] = ("CAISO",)
#: derive_unit_bands NaNs a multiple outside (0, 5); dividing by 10 keeps a CC
#: (~6-8 MMBtu/MWh) inside that window. It cancels exactly below (x BASE).
BASE = 10.0
#: Physical plausibility of an incremental/average ratio for a CC.
RATIO_BAND: tuple[float, float] = (0.5, 1.2)
YEARS: tuple[int, ...] = tuple(range(2019, 2026))


def derive(iso: str) -> pd.DataFrame:
    """Return the per-plant-year (and pooled) incremental/average ratio table."""
    art = pd.read_csv(PROCESSED_DIR / f"campd_cc_heat_rates_{iso}.csv")
    art = art[art["flag"].astype(str) == "ok"]
    avg = art.set_index(["plant_code", "year"])["heat_rate_gross"]
    names = art.groupby("plant_code")["plant_name"].first()
    c = _campd_cc_hours(iso, list(YEARS), set(int(p) for p in art["plant_code"]))
    op = (c["opTime"] >= _MIN_OPTIME) & (c["grossLoad"] > 0) & (c["heatInput"] > 0)
    c = c[op].copy()
    c["hr"] = c["heatInput"] / c["grossLoad"]
    c = c[(c["hr"] >= _HR_MIN_GROSS) & (c["hr"] <= _HR_MAX_GROSS)]
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
    ok = py["ratio_econ_low"].between(*RATIO_BAND) & py["ratio_econ_high"].between(
        *RATIO_BAND
    )
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
        "CAMPD unit-level hourly (derive_campd_cc_heat_rates._campd_cc_hours: CC "
        "unitType, split-plant remap; opTime>=0.99, hourly HR in [5,20]); "
        "incremental HR = derive_campd_marginal_hr.derive_unit_bands (p3/p97, "
        "normalized quadratic, econ_low x=0.5 / econ_high x=0.9), gen-weighted "
        "over units; / campd_cc_heat_rates heat_rate_gross of the same plant-year; "
        "year 0 = mean of ok year ratios"
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
    """CLI entry: write ``cc_incremental_hr_ratio_<ISO>.csv``."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    a = ap.parse_args(argv)
    iso = a.iso.upper()
    if iso not in ISO_SCOPE:
        raise SystemExit(f"{iso} is not in ISO_SCOPE {ISO_SCOPE} (rule 25)")
    tab = derive(iso)
    out = PROCESSED_DIR / f"cc_incremental_hr_ratio_{iso}.csv"
    tab.to_csv(out, index=False)
    print(tab[tab["year"] == 0].drop(columns=["source"]).to_string(index=False))
    print(f"wrote {out} ({len(tab)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
