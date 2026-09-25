"""R-SOCO-B phase 0 (ZERO LP): per-year census of the three SOCO boundary repairs.

PRECOMMIT: ``docs/handoffs/r-soco/PRECOMMIT-r-soco-b-2026-09-25.md``. One
(year, side) per process, because the loaders are ``lru_cache``d:

* ``post`` — this branch as committed: R1 (2019 ``Total interchange`` sign
  window), R2 (Gulf plants dropped from the LP fleet) and R3 (PowerSouth
  ``AEC`` admitted in 2021 from September; excluded from the 2019-2020
  benchmark and from Jan-Aug 2021) all live.
* ``pre`` — the same code with the three repairs neutralised in-process
  (``EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC`` / ``ISO_BA_JOINS`` emptied,
  the fleet-side recode drop made the identity). That is exactly the base
  ``b5e3b914`` behaviour: with the joins empty the appended ``AEC`` rows of
  ``vintage_2021`` are filtered out by the BA code, as before they existed.

Both sides run the promoted keeper's recipe (``rsoco_corrected_inputs_span``
``meta.json`` through ``replay_keeper.run_year_kwargs``) with ``fleet_only=True``.
Writes one JSON: EIA-860 dir, per-group units / MW / availability energy, the
Gulf and PowerSouth MW and monthly availability energy, demand-with-interchange
TWh, served interchange TWh, and the raw EIA-923 membership frame per class.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

KEEPER = _ROOT / "results/calibration/rsoco_corrected_inputs_span"
GULF = {641, 643, 7715, 50310, 55242, 57502, 63754, 64757, 65036}
AEC = {53, 55, 56, 533, 6192, 7063, 56522, 64469}


def _sum_by(codes, groups, mw) -> dict[str, float]:
    """Sum MW per ``plant:group`` key (several LP units share one key)."""
    out: dict[str, float] = {}
    for c, g, p in zip(codes, groups, mw):
        key = f"{int(c)}:{g}"
        out[key] = round(out.get(key, 0.0) + float(p), 1)
    return out


def _neutralise() -> None:
    """Turn the three repairs off in-process (the base-SHA behaviour)."""
    import market_sim.config.constants as K
    import market_sim.data.ba_membership as bm
    import market_sim.data.fleet.eia860 as e860

    K.EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC = {}
    K.ISO_BA_JOINS = {}
    bm.ISO_BA_JOINS = {}
    e860.drop_current_ba_recoded_rows = lambda df, iso, plant_col="plant_id": df


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("year", type=int)
    ap.add_argument("side", choices=("pre", "post"))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.side == "pre":
        _neutralise()

    from market_sim.config.paths import active_eia860_dir
    from market_sim.data.eia930.envelopes import soco_net_interchange
    from market_sim.data.hydro import load_monthly_generation
    from market_sim.data.fleet.models import _hour_to_month_index
    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.setdefault("inject_biomass_mustrun", False)
    r = run_year(a.year, "SOCO", 8760, None, {}, fleet_only=True, **kw)
    fa = r["fleet_arrays"]
    fleet = r["fleet"]
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float).reshape(len(fleet), -1)
    code = np.asarray(fa.plant_code, int)
    groups = np.array([str(g.plant_group) for g in fleet])
    month = _hour_to_month_index(av.shape[1])
    out: dict = {
        "year": a.year,
        "side": a.side,
        "eia860_dir": str(active_eia860_dir().relative_to(_ROOT)),
        "groups": {},
        "demand_twh": round(float(np.asarray(r["demand"]).sum()) / 1e6, 4),
    }
    ix = soco_net_interchange(a.year)
    out["served_interchange_twh"] = (
        None if ix is None else round(float(ix.sum()) / 1e6, 4)
    )
    for grp in sorted(set(groups)):
        m = groups == grp
        out["groups"][grp] = {
            "units": int(m.sum()),
            "mw": round(float(pmax[m].sum()), 1),
            "avail_twh": round(float((av[m] * pmax[m][:, None]).sum()) / 1e6, 4),
        }
    for name, plants in (("gulf", GULF), ("aec", AEC)):
        m = np.isin(code, list(plants))
        e = av[m] * pmax[m][:, None]
        out[name] = {
            "units": int(m.sum()),
            "mw": round(float(pmax[m].sum()), 1),
            "by_plant_group_mw": _sum_by(code[m], groups[m], pmax[m]),
            "avail_twh": round(float(e.sum()) / 1e6, 4),
            "avail_gwh_by_month": [
                round(float(e[:, month == k].sum()) / 1e3, 1) for k in range(12)
            ],
        }
    gen = load_monthly_generation()
    f923 = rcf._eia923_frame(a.year, gen, "SOCO")
    out["eia923_frame_twh"] = {
        k: round(float(v) / 1e6, 4)
        for k, v in f923.groupby("klass")["annual_mwh"].sum().items()
    }
    for name, plants in (("gulf", GULF), ("aec", AEC)):
        sub = f923[f923["plant_id"].isin(plants)]
        out[f"eia923_{name}_twh"] = round(float(sub["annual_mwh"].sum()) / 1e6, 4)
    a.out.write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
