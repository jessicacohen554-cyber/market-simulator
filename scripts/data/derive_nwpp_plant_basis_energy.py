"""Derive NWPP's per-fuel-family annual plant-basis energy (EIA-923 basis).

Writes ``data/raw/reference/nwpp_plant_basis_energy.csv`` — one row per
``(year, family)`` — the annual energy the ``nwpp_demand_plant_basis`` served
schedule anchors each EIA-930 fuel family to (owner ruling on
``FINDING-nwpp-45`` §8 = framing 2, session NWPP-NEXT-3, 2026-09-25: *anchor the
demand construction to the same plant basis C1 scores on — EIA-930 hourly shape,
EIA-923 plant energy*).

Construction (closeout-nwpp-anchor, owner ruling R-28 "Keep old figures, fix
later", PR #7076): computed directly from the SOURCE data with the benchmark's
own builders, never from a rendered bench part. The earlier derive read
``frontend/data/backcast/bench/NWPP/<year>.json.gz:bench.classFull``, whose
plant -> class map is the keeper's EIA-860 fleet (``_fleet_group_by_code``), so
re-rendering the bench at a promotion that changed the roster (W0 admitted
SB/OA units and moved CHP membership) silently moved this anchor. Here:

* **Footprint** — the plants EIA-860 BA-codes to NWPP at load time
  (``run_calibration_full._iso_plant_ids``, the E.6 membership list), never
  the units a keeper's fleet carries.
* **Plant -> class map** — :func:`plant_class_map`: each footprint plant's
  EIA-923 class (``_classify_f923``: fuel, prime mover, the filed CHP flag)
  carrying its largest net generation in the year, else in the latest of the
  ``_CLASS_SHARE_MAX_PRIOR_YEARS`` prior years that reports it. It drives the
  CAMPD backfill, the missing-month repair, the dual-fuel oil re-attribution
  and the behind-the-meter CHP subtrahend — the four places the bench part
  reads the fleet map.
* **Per-class energy** — ``_benchmark_eia923_frame`` (EIA-923 + CAMPD backfill
  + missing months + EIA-930 renewable repair) minus the bench-basis BTM host
  supply (``_btm_frame`` ``btm_bench_twh``); wind / solar on the EIA-930 grid
  series where ``actuals_source`` says so; the combined fossil level reconciled
  to EIA-930 by ``render_calibration_html.reconcile_vintage_classes`` — the
  identical sequence the bench part runs.
* **Family** — each class maps to exactly one EIA-930 fuel family
  (:data:`CLASS_FAMILY`); an unmapped class FAILS. On a preliminary EIA-923
  vintage only the repaired fossil families are written
  (:data:`PRELIMINARY_VINTAGE_FAMILIES`); an absent family is left on EIA-930
  by the anchor.

Frozen against residuals (rule 23 ``[R-FROZEN-DERIVE]``): re-derive ONLY when
the EIA-923 vintage (``eia923_monthly_generation.parquet``), the NWPP footprint
list (EIA-860 BA membership / ``ba_membership``), or the EIA-923 class
crosswalk (``_classify_f923`` / :data:`CLASS_FAMILY`) changes — and cite that
source change in the commit. A keeper's roster, fleet admission rules or bench
re-render are NOT reasons to re-derive (none of them is read). Each row records
the EIA-923 artifact's sha256 so a vintage change is visible.

Run: ``python3 scripts/data/derive_nwpp_plant_basis_energy.py [--years 2023 ...]``
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_sim.data.eia923 import EIA923_MONTHLY_GENERATION_PATH  # noqa: E402
from market_sim.data.eia930.envelopes import (  # noqa: E402
    NWPP_PLANT_BASIS_CLASS_FAMILY as CLASS_FAMILY,
)
from market_sim.data.eia930.envelopes import (  # noqa: E402
    NWPP_PLANT_BASIS_ENERGY_PATH,
)

ISO = "NWPP"
#: The data-contract schema (data/dictionary/schema/<DATATYPE>.schema.yaml).
DATATYPE = "nwpp-plant-basis-energy"
COMPLETENESS_DIR = REPO / "frontend" / "data" / "backcast" / "completeness"
#: The backcast years the NWPP keeper carries (rule 16).
YEARS: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
FIELDS: tuple[str, ...] = ("year", "family", "twh", "source", "eia923_sha256")
SOURCE = (
    "EIA-923 Page 1 (+CAMPD backfill, EIA-930 VRE, fossil reconcile) of the "
    "EIA-860 NWPP footprint; class = plant's dominant EIA-923 class"
)

# On a PRELIMINARY EIA-923 vintage (a year with a committed completeness part,
# written by scripts/audit_eia923_completeness.py) the benchmark repairs only
# the audited fossil families (render_calibration_html.reconcile_vintage_classes
# and the CEMS anchor); every other class is the raw, incomplete preliminary
# survey (NWPP 2025 OTHER+biomass+oil 4.27 TWh against 8.17-8.85 in every
# complete year). Only these families are therefore a plant basis on such a
# year; the rest are omitted, which leaves them on EIA-930 (rule 14).
PRELIMINARY_VINTAGE_FAMILIES: frozenset[str] = frozenset({"COL", "NG"})


def is_preliminary(year: int) -> bool:
    """Whether ``year``'s EIA-923 vintage is preliminary (a completeness part exists)."""
    return (COMPLETENESS_DIR / f"eia923_{int(year)}.json").exists()


def _classify(frame: pd.DataFrame) -> list[str]:
    """EIA-923 class of each row (the benchmark's own crosswalk)."""
    from scripts import run_calibration_full as rcf

    return [
        rcf._classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(
            frame["fuel_type"], frame["prime_mover"], frame["chp"], frame["plant_id"]
        )
    ]


def plant_class_map(year: int, generation: pd.DataFrame) -> dict[int, str]:
    """Return the roster-independent ``{plant_id: class}`` map for ``year``.

    Every plant in the NWPP footprint (EIA-860 BA membership at load time) takes
    the EIA-923 class carrying its largest net generation in ``year``; a plant
    with no positive EIA-923 net generation that year takes it from the latest
    of the ``_CLASS_SHARE_MAX_PRIOR_YEARS`` prior years that reports it (the
    look-back the benchmark's class shares already use). A plant with no
    EIA-923 record in that window has no class and is never backfilled. The
    keeper's fleet is never read, so a roster change cannot move the map.
    """
    from scripts import run_calibration_full as rcf

    ids = rcf._iso_plant_ids(ISO, int(year), False)
    out: dict[int, str] = {}
    for y in range(int(year), int(year) - rcf._CLASS_SHARE_MAX_PRIOR_YEARS - 1, -1):
        df = generation[(generation["year"] == y) & generation["plant_id"].isin(ids)]
        if df.empty:
            continue
        df = df.assign(klass=_classify(df))
        tot = df.groupby(["plant_id", "klass"])["netgen_annual_mwh"].sum()
        tot = tot[tot > 0.0]
        for pid, sub in tot.groupby(level=0):
            if int(pid) not in out:
                out[int(pid)] = str(sub.droplevel(0).idxmax())
    return out


def class_energy(year: int, generation: pd.DataFrame) -> dict[str, float]:
    """Return ``{class: TWh}`` — the grid-delivered plant basis for ``year``.

    The bench part's ``classFull`` sequence on :func:`plant_class_map` in place
    of the keeper's fleet map (module docstring).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.results.calibration import EIA930_SOURCE, actuals_source
    from scripts import render_calibration_html as rch
    from scripts import run_calibration_full as rcf

    year = int(year)
    group_by_code = plant_class_map(year, generation)
    campd_year = rcf._campd_hourly_frame(
        year, ISO, rcf._parasitic_factor_map(), rcf._HOURS_PER_YEAR
    )
    campd_active = None
    if campd_year is not None:
        by_plant = campd_year.groupby("plant_id")["net_mw"].sum()
        campd_active = set(by_plant[by_plant > 0.0].index.astype(int))
    e930 = rcf._eia930_frame(year, ISO, get_iso_config(ISO))
    e923 = rcf._benchmark_eia923_frame(
        year, generation, ISO, campd_year, group_by_code, e930, None, campd_active
    )
    btm = rcf._btm_frame(
        year, "P1", generation, None, campd_active, iso=ISO, group_by_code=group_by_code
    )
    btm_bench = dict(zip(btm["klass"], btm["btm_bench_twh"])) if len(btm) else {}
    cls = e923.groupby("klass")["annual_mwh"].sum()
    out = {
        str(k): round(float(v) / 1e6 - float(btm_bench.get(str(k), 0.0)), 4)
        for k, v in cls.items()
    }
    series = {
        s: e930[e930["series"] == s]["mw"].to_numpy(float)
        for s in e930["series"].unique()
    }
    e930d = {
        f: round(float(series.get(f, np.zeros(1)).sum()) / 1e6, 3)
        for f in ("gas", "coal", "nuclear", "wind", "solar")
    }
    for f in ("other", "oil"):
        if f in series:
            e930d[f] = round(float(series[f].sum()) / 1e6, 3)
    for vre in ("wind", "solar"):
        if vre in out and vre in e930d and actuals_source(vre, ISO) == EIA930_SOURCE:
            out[vre] = round(float(e930d[vre]), 4)
    rch.reconcile_vintage_classes(out, e930d, ISO)
    return out


def family_energy(class_twh: dict[str, float], year: int) -> dict[str, float]:
    """Sum ``class_twh`` into EIA-930 fuel families; FAIL on an unmapped class."""
    unmapped = sorted(set(class_twh) - set(CLASS_FAMILY))
    if unmapped:
        raise ValueError(f"NWPP {year}: classes with no family {unmapped}")
    totals: dict[str, float] = {}
    for klass, twh in class_twh.items():
        fam = CLASS_FAMILY[klass]
        totals[fam] = totals.get(fam, 0.0) + float(twh)
    if is_preliminary(year):
        totals = {f: t for f, t in totals.items() if f in PRELIMINARY_VINTAGE_FAMILIES}
    return totals


def derive(years: tuple[int, ...] = YEARS) -> list[dict]:
    """Return the ``(year, family, twh, source, eia923_sha256)`` rows."""
    from scripts import run_calibration_full as rcf

    generation = rcf.load_monthly_generation()
    sha = hashlib.sha256(Path(EIA923_MONTHLY_GENERATION_PATH).read_bytes()).hexdigest()
    rows: list[dict] = []
    for year in years:
        totals = family_energy(class_energy(year, generation), year)
        for fam in sorted(totals):
            rows.append(
                {
                    "year": int(year),
                    "family": fam,
                    "twh": f"{totals[fam]:.4f}",
                    "source": SOURCE,
                    "eia923_sha256": sha,
                }
            )
    return rows


def validate_rows(rows: list[dict]) -> None:
    """Validate the rows against the ``nwpp-plant-basis-energy`` schema (schema-first)."""
    from scripts.lib.clean_io import validate_df

    frame = pd.DataFrame(rows, columns=list(FIELDS)).astype(
        {"year": "int64", "twh": "float64"}
    )
    validate_df(frame, DATATYPE)


def main(argv: list[str] | None = None) -> None:
    """Write the CSV (every year, or merge ``--years`` into it) and print totals."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    rows = derive(tuple(args.years))
    path = NWPP_PLANT_BASIS_ENERGY_PATH
    if set(args.years) != set(YEARS) and path.exists():
        kept = [
            r
            for r in csv.DictReader(path.open())
            if int(r["year"]) not in set(args.years) and set(r) == set(FIELDS)
        ]
        rows = sorted(kept + rows, key=lambda r: (int(r["year"]), r["family"]))
    validate_rows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(FIELDS))
        w.writeheader()
        w.writerows(rows)
    by_year: dict[int, float] = {}
    for r in rows:
        by_year[int(r["year"])] = by_year.get(int(r["year"]), 0.0) + float(r["twh"])
    for y, t in sorted(by_year.items()):
        print(f"{y}: {t:.3f} TWh")
    print(f"wrote {path.relative_to(REPO)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
