"""NWPP-NEXT-13 phase 0 (ZERO LP): the statistical coal WEFOR double count on keeper #17.

Fleet-only rebuilds (``run_year(fleet_only=True)``) of keeper #17
(``results/calibration/nwppnext12mr_span``) on its own recipe, per year, in four
variants:

* ``B``    — the keeper recipe;
* ``DEN``  — ``unit_outage_dispatched_bin_denominator`` ALONE (the prerequisite
  ``wefor_residual_short_screened_coal`` fails closed on; censused on its own,
  every class, because it is a second mechanism — rule 19 [R-ONE-MECH]);
* ``ARM``  — ``DEN`` + ``wefor_residual_short_screened_coal`` at
  ``wefor_residual = 0.0`` (the miso-273 relief);
* ``noWc`` — statistical WEFOR relieved on ALL coal (the upper bound).

Identification (the frozen caiso-187 formula, rule 23; miso-273 template), per
year over the SCREENED coal capacity only:

    W_s = sum_bins s_b x (avail_noWc_b - avail_B_b)       (the statistical term)
    X_s = measured window MWh on the screened unit-years, clipped to the year:
          >= 5-day (the keeper's -memberrepair- extract) + < 5-day short
          + partial plateaus x (1 - derate_factor)
    residual_s = max(0, W_s - X_s) / (screened MW x 8760)

Requires ``data/raw/campd-unit-outages-short-screened-NWPP.csv``
(``derive_campd_unit_outages.py --iso NWPP --short-windows --emit-screened-set``).

Usage::

    uv run python scripts/probes/_nwppnext13_screened_wefor_phase0.py --years 2023 --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLE = REPO / "results/calibration/nwppnext12mr_span"
COAL = ["COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC"]
VARIANTS = {
    "B": {},
    "DEN": {"unit_outage_dispatched_bin_denominator": True},
    "ARM": {
        "unit_outage_dispatched_bin_denominator": True,
        "wefor_residual": 0.0,
        "wefor_residual_short_screened_coal": True,
    },
    "noWc": {"wefor_residual": 0.0, "wefor_residual_groups": frozenset(COAL)},
}
RAW = REPO / "data/raw"
SCREENED = RAW / "campd-unit-outages-short-screened-NWPP.csv"
# name -> (path, start col, end col, MW expression)
WINDOWS = {
    "ge5d": (
        RAW / "campd-unit-outages-memberrepair-NWPP.csv",
        "outage_start",
        "outage_end",
        "full",
    ),
    "short": (
        RAW / "campd-unit-outages-short-NWPP.csv",
        "outage_start",
        "outage_end",
        "full",
    ),
    "partial": (
        RAW / "campd-partial-outages-NWPP.csv",
        "outage_start",
        "outage_end",
        "partial",
    ),
}


def _window_mwh(year: int, keys: set) -> dict[str, float]:
    """Measured window MWh on the screened ``(facility, unit)`` set, clipped to ``year``."""
    y0, y1 = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year + 1}-01-01")
    out = {}
    for name, (path, s, e, kind) in WINDOWS.items():
        df = pd.read_csv(path)
        m = [(int(f), str(u)) in keys for f, u in zip(df["facility_id"], df["unit_id"])]
        df = df[m]
        st = pd.to_datetime(df[s])
        en = pd.to_datetime(df[e]) + pd.Timedelta(days=1)  # inclusive end dates
        hrs = (en.clip(upper=y1) - st.clip(lower=y0)).dt.total_seconds().clip(
            lower=0
        ) / 3600.0
        mw = df["unit_capacity_mw"] * (
            (1.0 - df["derate_factor"]) if kind == "partial" else 1.0
        )
        out[name] = float((hrs * mw).sum())
    return out


def _frame(st: dict) -> pd.DataFrame:
    """One row per LP unit: plant, group, pmax, available MWh."""
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    return pd.DataFrame(
        {
            "unit_id": list(fa.unit_ids),
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "group": list(fa.plant_group),
            "pmax": pmax,
            "avail_mwh": pmax * (av.sum(axis=1) if av.ndim == 2 else av * 8760),
        }
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.outages import short_screened_coal_shares
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    scr = pd.read_csv(SCREENED)
    res: dict[str, dict] = {}
    for y in args.years:
        gas = henry_hub_actual(rcf._load_reference(), y)
        fr, armed = {}, {}
        for v, flips in VARIANTS.items():
            kw = run_year_kwargs(meta)
            kw.update(derived_run_year_inputs(BUNDLE, y))
            kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **flips}
            if y <= 2022:
                kw["prb_overrides"]["hydro_backfill_year"] = None
            st = run_year(y, "NWPP", 8760, gas, {}, fleet_only=True, **kw)
            cfg = st["config"]
            armed[v] = {k: getattr(cfg, k) for k in flips}
            fr[v] = _frame(st)
            set_eia860_vintage(None)
        b = fr["B"]
        coal_b = b[b.group.isin(COAL)]
        roster = coal_b.groupby("plant_code")["pmax"].sum()
        shares = short_screened_coal_shares(
            y,
            "NWPP",
            tuple(sorted(((int(k), "COAL"), float(v)) for k, v in roster.items())),
        )

        def by_plant(df):
            d = df[df.group.isin(COAL)]
            return d.groupby("plant_code")["avail_mwh"].sum()

        wb, wn = by_plant(b), by_plant(fr["noWc"])
        W_s = sum(
            s * (wn.get(k[0], 0.0) - wb.get(k[0], 0.0)) for k, s in shares.items()
        )
        scr_mw = sum(s * roster.get(k[0], 0.0) for k, s in shares.items())
        keys = {
            (int(f), str(u))
            for f, u, yy in zip(scr.facility_id, scr.unit_id, scr.year)
            if yy == y
        }
        X = _window_mwh(y, keys)
        X_s = sum(X.values())
        cap_h = scr_mw * 8760.0
        groups = sorted(b.group.unique())
        per_class = {
            v: {
                g: round(float(d.loc[d.group == g, "avail_mwh"].sum()) / 1e6, 4)
                for g in groups
            }
            for v, d in fr.items()
        }
        den_moved = (
            fr["DEN"].set_index("unit_id")["avail_mwh"]
            - b.set_index("unit_id")["avail_mwh"]
        ).abs()
        res[str(y)] = {
            "armed": {v: {k: str(x) for k, x in a.items()} for v, a in armed.items()},
            "screened_unit_years": len(keys),
            "screened_extract_mw": round(
                float(scr.loc[scr.year == y, "unit_capacity_mw"].sum()), 1
            ),
            "screened_plant_shares": {
                str(k[0]): round(s, 4) for k, s in shares.items()
            },
            "coal_lp_mw": round(float(roster.sum()), 1),
            "screened_lp_mw": round(scr_mw, 1),
            "W_screened_twh": round(W_s / 1e6, 4),
            "X_screened_twh": {k: round(x / 1e6, 4) for k, x in X.items()},
            "residual_share": round(max(0.0, W_s - X_s) / cap_h, 5) if cap_h else None,
            "W_share": round(W_s / cap_h, 5) if cap_h else None,
            "X_share": round(X_s / cap_h, 5) if cap_h else None,
            "avail_twh_by_variant": per_class,
            "DEN_minus_B_twh": {
                g: round(per_class["DEN"][g] - per_class["B"][g], 4) for g in groups
            },
            "ARM_minus_DEN_twh": {
                g: round(per_class["ARM"][g] - per_class["DEN"][g], 4) for g in groups
            },
            "noWc_minus_B_twh": {
                g: round(per_class["noWc"][g] - per_class["B"][g], 4) for g in groups
            },
            "DEN_units_moved": int(den_moved.gt(1e-6).sum()),
            "DEN_units_moved_by_group": fr["DEN"]
            .set_index("unit_id")
            .loc[den_moved[den_moved.gt(1e-6)].index, "group"]
            .value_counts()
            .to_dict(),
            "pmax_identical_all": all(
                bool((d["pmax"].values == b["pmax"].values).all()) for d in fr.values()
            ),
        }
        print(
            json.dumps(
                {
                    y: {
                        k: res[str(y)][k]
                        for k in (
                            "W_screened_twh",
                            "X_screened_twh",
                            "residual_share",
                            "DEN_units_moved",
                        )
                    }
                }
            ),
            flush=True,
        )
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
