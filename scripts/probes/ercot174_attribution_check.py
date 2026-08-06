#!/usr/bin/env python3
"""ercot-174 PRE-SOLVE attribution checks AT-1 / AT-2 and the P-2024 face.

No LP. Reads only the committed loaders, so it measures exactly the ceiling the
event-cap block will build:

* **AT-1** — how many scoped bin-hours the unit-scoped composition switches
  from the incumbent product to ``min()`` (i.e. the window and partial layers
  share a CAMPD unit there), and the share of both-layers-active bin-hours that
  is.
* **AT-2 (STOP RULE)** — per year,
  ``rho = sum(ceil_unit_scoped - ceil_product) / sum(ceil_min - ceil_product)``
  over scoped bin-hours: the share of the REJECTED ercot-173 blanket arm's
  total ceiling lift that survives unit scoping. Pre-registered expectation
  ``rho`` well below 0.5; **rho >= 0.5 in any year stops the session before the
  solve** (the attribution is not discriminating and the arm is the blanket arm
  in disguise).
* **P-2024 / P-NULL** — the ercot-172 named plants at the two 2024 shed hours:
  whether the layers actually share a unit there, and the resulting ceilings
  under all three compositions. No shared unit at those plants ⇒ the arm is
  INERT and FINDING-ercot173 §3's structural claim is REFUTED.
* **Robustness (REPORTED, NON-SELECTING)** — ``rho`` recomputed under
  STRICTER attribution thresholds, as a pure reprojection of the committed
  extract's own ``ceiling_ratio`` column (no re-derive, no second threshold in
  the production path). Reported so the verdict is visibly not an artifact of
  the frozen ``_CEILING_FRAC``; **never used to select** — the frozen-constant
  test is the mechanism, fixed in the precommit. Looser thresholds need no
  measurement: attribution is monotone (a looser test carries a superset of
  units ⇒ a superset of shared hours ⇒ ``rho`` can only RISE).

Pre-registration:
``docs/PRECOMMIT-ercot174-unit-attributed-partial-outage-2026-08-06.md`` §4.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.paths import CAMPD_BINS_CSV  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    partial_outage_active_units,
    partial_outage_derate_factors,
    shared_unit_hours,
    unit_outage_active_units,
    unit_outage_derate_factors,
)

# The keeper's event-cap class scope (coal + gas event caps both armed on
# run168b): COAL from ercot_dam_availability_coal_event_cap, the three gas
# classes from ercot_dam_availability_gas_event_cap.
EVCAP_SCOPE = ("COAL", "CC_REGULAR", "ST_GAS", "CT_PEAKER")

# The two ercot-172 shed hours (model clock, non-leap 8760), from
# FINDING-ercot172 §3: h2827 = 2024-04-28 19:00 CST, h3067 = 2024-05-08 19:00.
SHED_HOURS_2024 = {2827: "2024-04-28 19:00", 3067: "2024-05-08 19:00"}
# The plants FINDING-ercot172 §3 named at those hours.
NAMED_PLANTS = {3470: "W A Parish", 3612: "V H Braunig", 6146: "Martin Lake",
                55153: "Guadalupe", 55230: "Jack County", 55168: "Bastrop",
                7097: "J K Spruce", 7900: "Sand Hill", 56611: "Sandy Creek",
                3601: "Sim Gideon"}


def _rho_at_threshold(year: int, hours: int, frac: float) -> tuple[float, int]:
    """Return ``(rho, min_composed_bin_hours)`` under a stricter carry test.

    A pure reprojection of :data:`PARTIAL_OUTAGE_UNITS_CSV`: only attributed
    rows whose measured ``ceiling_ratio`` is below ``frac`` are treated as
    carrying. Diagnostic ONLY — the production path always uses the frozen
    ``_CEILING_FRAC`` (rule 23), and this band is reported, never selected on.
    """
    import pandas as pd

    from market_sim.data.outages import (
        PARTIAL_OUTAGE_UNITS_CSV,
        _unit_outage_target,
        outage_hour_mask,
    )

    df = pd.read_csv(PARTIAL_OUTAGE_UNITS_CSV)
    df = df[(df["year"] == year) & df["ceiling_ratio"].notna()]
    df = df[df["ceiling_ratio"] < frac]
    p_units: dict[tuple[int, str], dict[str, np.ndarray]] = {}
    for r in df.itertuples(index=False):
        tgt = _unit_outage_target(int(r.oris_code), str(r.unit_id), r.plant_group)
        if tgt is None:
            continue
        mask = outage_hour_mask(r.outage_start, r.outage_stop, year, hours)
        if not mask.any():
            continue
        arr = p_units.setdefault(tgt, {}).setdefault(
            str(r.unit_id), np.zeros(hours, dtype=bool)
        )
        arr |= mask

    w_fac = unit_outage_derate_factors(year, hours, str(CAMPD_BINS_CSV), "ERCOT")
    p_fac = partial_outage_derate_factors(year, hours, class_grain=True)
    w_units = unit_outage_active_units(year, hours, iso="ERCOT")
    lift_u = lift_m = 0.0
    n_min = 0
    for key, fp in p_fac.items():
        if key[1] not in EVCAP_SCOPE:
            continue
        fw = w_fac.get(key)
        if fw is None:
            continue
        prod, mn = fw * fp, np.minimum(fw, fp)
        shared = shared_unit_hours(w_units.get(key), p_units.get(key), hours)
        lift_u += float((np.where(shared, mn, prod) - prod).sum())
        lift_m += float((mn - prod).sum())
        n_min += int((shared & (fw < 1.0) & (fp < 1.0)).sum())
    return ((lift_u / lift_m) if lift_m > 0 else 0.0), n_min


def main() -> None:
    """Measure AT-1 / AT-2 / P-2024 and write the pre-solve attribution record."""
    hours = HOURS_PER_YEAR
    out: dict = {"years": {}, "shed_face": {}}
    for year in (2023, 2024, 2025):
        w_fac = unit_outage_derate_factors(year, hours, str(CAMPD_BINS_CSV), "ERCOT")
        p_fac = partial_outage_derate_factors(year, hours, class_grain=True)
        w_units = unit_outage_active_units(year, hours, iso="ERCOT")
        p_units = partial_outage_active_units(year, hours, iso="ERCOT")

        both_hours = 0        # bin-hours where BOTH layers are active
        min_hours = 0         # ...of which the unit sets intersect (AT-1)
        lift_unit = 0.0       # sum(ceil_unit_scoped - ceil_product)
        lift_min = 0.0        # sum(ceil_min      - ceil_product)
        bins_shared: list[dict] = []
        for key, fp in p_fac.items():
            plant, grp = key
            if grp not in EVCAP_SCOPE:
                continue
            fw = w_fac.get(key)
            if fw is None:
                continue
            prod = fw * fp
            mn = np.minimum(fw, fp)
            shared = shared_unit_hours(w_units.get(key), p_units.get(key), hours)
            unit_scoped = np.where(shared, mn, prod)
            active = (fw < 1.0) & (fp < 1.0)
            both_hours += int(active.sum())
            min_hours += int((shared & active).sum())
            lift_unit += float((unit_scoped - prod).sum())
            lift_min += float((mn - prod).sum())
            if shared.any():
                bins_shared.append(
                    {
                        "plant": plant,
                        "name": NAMED_PLANTS.get(plant, ""),
                        "group": grp,
                        "shared_hours": int(shared.sum()),
                        "shared_and_active_hours": int((shared & active).sum()),
                        "shared_units": sorted(
                            set(w_units.get(key, {})) & set(p_units.get(key, {}))
                        ),
                    }
                )
        rho = (lift_unit / lift_min) if lift_min > 0 else 0.0
        out["years"][str(year)] = {
            "both_layers_active_bin_hours": both_hours,
            "AT1_min_composed_bin_hours": min_hours,
            "AT1_share_of_both_active": round(min_hours / both_hours, 6)
            if both_hours
            else 0.0,
            "ceiling_lift_unit_scoped": round(lift_unit, 3),
            "ceiling_lift_blanket_min": round(lift_min, 3),
            "AT2_rho": round(rho, 6),
            "AT2_stop": bool(rho >= 0.5),
            "shared_bins": sorted(
                bins_shared, key=lambda d: -d["shared_and_active_hours"]
            ),
        }

    # P-2024 face: the two shed hours, per named plant, all three ceilings.
    w_fac = unit_outage_derate_factors(2024, hours, str(CAMPD_BINS_CSV), "ERCOT")
    p_fac = partial_outage_derate_factors(2024, hours, class_grain=True)
    w_units = unit_outage_active_units(2024, hours, iso="ERCOT")
    p_units = partial_outage_active_units(2024, hours, iso="ERCOT")
    for h, label in SHED_HOURS_2024.items():
        rows = []
        for key, fp in p_fac.items():
            plant, grp = key
            if grp not in EVCAP_SCOPE:
                continue
            fw = w_fac.get(key)
            if fw is None or (fw[h] >= 1.0 and fp[h] >= 1.0):
                continue
            shared = shared_unit_hours(w_units.get(key), p_units.get(key), hours)
            rows.append(
                {
                    "plant": plant,
                    "name": NAMED_PLANTS.get(plant, ""),
                    "group": grp,
                    "f_window": round(float(fw[h]), 4),
                    "f_partial": round(float(fp[h]), 4),
                    "ceil_product": round(float(fw[h] * fp[h]), 4),
                    "ceil_min": round(float(min(fw[h], fp[h])), 4),
                    "ceil_unit_scoped": round(
                        float(min(fw[h], fp[h]) if shared[h] else fw[h] * fp[h]), 4
                    ),
                    "shares_unit": bool(shared[h]),
                    "window_units": sorted(w_units.get(key, {})),
                    "partial_units": sorted(p_units.get(key, {})),
                }
            )
        out["shed_face"][str(h)] = {"label": label, "plants": rows}

    # Robustness band (REPORTED, NON-SELECTING): does the verdict survive a
    # much stricter attribution? Looser needs no measurement — rho is monotone
    # non-decreasing in how inclusive the carry test is.
    out["robustness_nonselecting"] = {
        str(y): {
            f"{f:.2f}": {"rho": round(r, 6), "min_composed_bin_hours": n}
            for f, (r, n) in (
                (f, _rho_at_threshold(y, hours, f)) for f in (0.50, 0.30, 0.10, 0.02)
            )
        }
        for y in (2023, 2024, 2025)
    }
    print("\nrobustness (REPORTED, non-selecting) — rho at stricter carry tests:")
    for y, band in out["robustness_nonselecting"].items():
        print(
            f"  {y}: frozen 0.65 rho={out['years'][y]['AT2_rho']:.4f}  "
            + "  ".join(f"<{f} rho={d['rho']:.4f}" for f, d in band.items())
        )

    dest = REPO / "results" / "calibration" / "ercot174_attribution_check.json"
    dest.write_text(json.dumps(out, indent=2))
    for y, d in out["years"].items():
        print(
            f"{y}: AT-1 min-composed {d['AT1_min_composed_bin_hours']:,} / "
            f"{d['both_layers_active_bin_hours']:,} both-active bin-hours "
            f"({d['AT1_share_of_both_active']:.3%});  AT-2 rho={d['AT2_rho']:.4f}"
            f"{'  *** STOP ***' if d['AT2_stop'] else ''}"
        )
        for b in d["shared_bins"]:
            print(
                f"    shared: {b['plant']} {b['name']} {b['group']} "
                f"{b['shared_and_active_hours']} h  units={b['shared_units']}"
            )
    for h, d in out["shed_face"].items():
        print(f"\nh{h} ({d['label']}):")
        for r in d["plants"]:
            print(
                f"  {r['plant']:>6} {r['name']:<14} {r['group']:<11} "
                f"w={r['f_window']:.4f} p={r['f_partial']:.4f} "
                f"prod={r['ceil_product']:.4f} min={r['ceil_min']:.4f} "
                f"unit={r['ceil_unit_scoped']:.4f} shared={r['shares_unit']}"
            )
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
