"""miso-141 — the two follow-ups the basis probe's own numbers demand.

PREREG: ``results/calibration/PREREG-miso141-summer-derate-basis-2026-08-07.md``.
Companion to ``_miso141_summer_derate_basis.py``.  **No LP solved.**

**(A) CC_REGULAR's negative nameplate->summer gap, decomposed.**  The basis probe
measured MISO CC_REGULAR at ``net_summer / nameplate = 1.0138`` — the registered
SUMMER rating ABOVE nameplate, which EIA-860's own schema forbids.  That is the
component/total double-filing ``fleet.cc_summer_capacity`` already clamps
(``ns_sum = min(ns_sum, np_sum)``) and the loader's own reconciliation warns
about.  An aggregate contaminated by known-corrupt filings is not a measurement
of the physical gap, so the class is split into CLEAN rows (``ns <= np``) and
CORRUPT rows (``ns > np``) and the ratio reported on the clean subset alone.
*A correction is not verified by the commit that makes it, and the instrument
that checks it needs checking too* (miso-140b).

**(B) G-4's cushion, from the keeper's OWN committed hourly sidecar.**  The
restored MW is meaningless without the idle capability it has to cross
(miso-139 §7: 13.7-18.8 GW).  Rebuilt here on the same basis miso-139 used —
the armed classes' own idle headroom plus unloaded coal capability in summer
h12-17 — so the two numbers are comparable.  DIAGNOSTIC, NOT LICENSING: the
repair ADDS capability, so its price sign is DOWN, the wrong way for a model
already -14.1 % low in 2025.  No C3a claim attaches.

Rule 13 ``[R-MEASURED]``: EIA-860 registration ratings and the keeper's own
committed dispatch sidecar; no price or benchmark enters.  Rule 22: 2023-2025.

Usage::

    .venv/bin/python scripts/probes/_miso141_cc_rows_and_cushion.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)

sys.path.insert(0, str(REPO / "scripts" / "probes"))
from _miso141_summer_derate_basis import (  # noqa: E402
    CONTROLS,
    SCOPE,
    SUMMER_MONTHS,
    W_AFT,
    _hour_month,
    _hour_of_day,
    eia860_ratings,
    fleet_frame,
    keeper_config,
)

ISO = "MISO"
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/miso132_ccmin_B"
OUT = REPO / "results/calibration/_miso141_cc_rows_and_cushion.json"

# miso-139 §7's cushion basis, reproduced so the two figures are comparable.
CUSHION_CLASSES = ("CT_PEAKER", "CT_CHP", "CC_REGULAR", "CC_CHP")
CUSHION_EXTRA = ("COAL",)


def a_cc_rows(year: int) -> dict:
    """Split each class's EIA-860 rows into CLEAN (ns<=np) and CORRUPT (ns>np)."""
    cfg = keeper_config(year)
    df = fleet_frame(year, cfg)
    out = {}
    for cls in SCOPE + CONTROLS:
        sub = df[
            (df["plant_group"] == cls)
            & df["net_summer_mw"].notna()
            & df["nameplate_mw"].notna()
            & (df["net_summer_mw"] > 0)
            & (df["nameplate_mw"] > 0)
        ]
        if sub.empty:
            continue
        corrupt = sub[sub["net_summer_mw"] > sub["nameplate_mw"] * 1.0001]
        clean = sub[sub["net_summer_mw"] <= sub["nameplate_mw"] * 1.0001]
        rec = {
            "n_rows": int(len(sub)),
            "n_corrupt_rows": int(len(corrupt)),
            "corrupt_share_of_rows": len(corrupt) / len(sub),
            "corrupt_nameplate_mw": float(corrupt["nameplate_mw"].sum()),
            "corrupt_net_summer_mw": float(corrupt["net_summer_mw"].sum()),
            "clean_nameplate_mw": float(clean["nameplate_mw"].sum()),
            "clean_net_summer_mw": float(clean["net_summer_mw"].sum()),
            "clean_winter_mw": float(clean["winter_mw"].sum()),
            "all_ratio_ns_over_np": float(
                sub["net_summer_mw"].sum() / sub["nameplate_mw"].sum()
            ),
            "clean_ratio_ns_over_np": (
                float(clean["net_summer_mw"].sum() / clean["nameplate_mw"].sum())
                if len(clean)
                else None
            ),
            "clean_gap_nameplate_to_summer_pct": (
                100.0 * (1.0 - clean["net_summer_mw"].sum() / clean["nameplate_mw"].sum())
                if len(clean)
                else None
            ),
            # Capacity-weighted per-row ratio on the clean subset, so a few very
            # large plants cannot carry the aggregate on their own.
            "clean_unit_p50_gap_pct": (
                float(
                    100.0
                    * (1.0 - (clean["net_summer_mw"] / clean["nameplate_mw"])).median()
                )
                if len(clean)
                else None
            ),
        }
        rec["corrupt_plants"] = sorted(
            {int(p) for p in corrupt["plant_code"].tolist()}
        )[:20]
        out[cls] = rec
    return out


def b_cushion(year: int) -> dict:
    """Idle capability in summer h12-17 from the keeper's committed sidecar.

    miso-139 §7 basis: the armed classes' own idle headroom (capability minus
    P1 dispatch) plus unloaded coal capability, in the same hours.
    """
    cfg = keeper_config(year)
    gens = load_fleet_from_csv(
        ISO,
        get_iso_config(ISO),
        year=year,
        measured_ct_heat_rates=bool(getattr(cfg, "measured_ct_heat_rates", False)),
        measured_chp_heat_rates=bool(getattr(cfg, "measured_chp_heat_rates", False)),
        cc_steam_part_capacity=bool(getattr(cfg, "cc_steam_part_capacity", False)),
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
    )
    zones = [z.name for z in get_iso_config(ISO).zones]
    fa = generators_to_fleet_arrays(gens, zones, 8760, iso=ISO, config=cfg, year=year)
    cap = fa.pmax[:, None] * fa.availability
    groups = np.array([g.plant_group for g in gens])

    mon, hod = _hour_month(8760), _hour_of_day(8760)
    aft = np.isin(mon, SUMMER_MONTHS) & np.isin(hod, W_AFT)
    n_aft = int(aft.sum())

    path = KEEPER / "hourly" / f"class_hourly_{year}.parquet"
    dfh = pd.read_parquet(path)
    dfh = dfh[dfh["pass"].astype(str).str.upper() == "P1"] if "pass" in dfh else dfh
    if dfh.empty:
        dfh = pd.read_parquet(path)
    piv = dfh.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    piv = piv.reindex(range(8760)).fillna(0.0)

    # The sidecar splits coal by rank (COAL_BIT / COAL_LIGNITE / COAL_PRB) while
    # the model's ``plant_group`` is the bare ``COAL``.  Mapped EXPLICITLY and
    # asserted below: an unmapped class silently reads zero dispatch and would
    # hand its ENTIRE capability back as phantom headroom (caught here on the
    # first run — coal alone would have added ~32 GW of fictitious cushion).
    SIDECAR_ALIAS = {"COAL": ("COAL_BIT", "COAL_LIGNITE", "COAL_PRB")}

    rows = {}
    total_headroom = 0.0
    for cls in CUSHION_CLASSES + CUSHION_EXTRA:
        sel = groups == cls
        if not sel.any():
            continue
        cols = [c for c in SIDECAR_ALIAS.get(cls, (cls,)) if c in piv.columns]
        assert cols, (
            f"class {cls!r} has no sidecar column (available: "
            f"{sorted(str(c) for c in piv.columns)}) — an unmapped class would "
            "read zero dispatch and inflate the cushion by its whole capability"
        )
        capability = float(cap[sel][:, aft].sum()) / n_aft
        disp = float(sum(piv[c][aft].sum() for c in cols)) / n_aft
        head = max(0.0, capability - disp)
        rows[cls] = {
            "capability_mw": capability,
            "dispatch_mw": disp,
            "headroom_mw": head,
            "loaded_frac": (disp / capability) if capability else None,
            "sidecar_cols": cols,
        }
        total_headroom += head
    return {
        "window": "summer h12-17",
        "n_hours": n_aft,
        "classes": rows,
        "cushion_mw": total_headroom,
        "sidecar": str(path.relative_to(REPO)),
        "sidecar_classes": sorted(str(c) for c in piv.columns),
    }


def main() -> None:
    out: dict = {
        "prereg": "results/calibration/PREREG-miso141-summer-derate-basis-2026-08-07.md",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "a_eia860_row_quality": {},
        "b_cushion": {},
    }
    for y in YEARS:
        print(f"[miso-141b] year {y} …", flush=True)
        out["a_eia860_row_quality"][str(y)] = a_cc_rows(y)
        out["b_cushion"][str(y)] = b_cushion(y)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"[miso-141b] wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
