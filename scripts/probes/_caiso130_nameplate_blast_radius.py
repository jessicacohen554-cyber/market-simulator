"""caiso-130 gate 0 — cross-ISO blast radius of ``hydro_budget_nameplate_aware``.

The caiso-127 owner grant item 3 arms this flag in its OWN single-delta A/B and
requires its **cross-ISO blast radius checked before it enters any keeper**. The
flag lives in the SHARED ``data.hydro`` level-pinning path
(:func:`market_sim.data.hydro.load_hydro_budget`), not in a CAISO literal, so
"CAISO-scoped by construction" is a claim that has to be proven, not assumed.

**No LP is built or solved anywhere in this probe.** It calls
:func:`market_sim.data.hydro.build_hydro_fleet` — the same entry point
``data.fleet.assembly`` calls — twice per (ISO, year, path) with the flag off
and on, and diffs the returned ``(n_hydro, 12)`` monthly-budget arrays. Each
ISO is probed under **its own keeper's** hydro settings
(``hydro_eia930_monthly`` / ``hydro_backfill_year`` / ``hydro_ror_split`` /
``hydro_min_flow_floor``), read from the committed keeper bundles, so the
backcast rows answer the question actually asked: *would arming this change
that ISO's keeper recipe?*

Three surfaces are reported:

1. **Backcast (each ISO's keeper settings, 2023-2025)** — the rule-20 training
   window, the only years any keeper is solved on.
2. **Forecast (``forecast_budget=True``, 2026)** — the forward path pins the
   monthly level from the normal-water-year climatology, so it is exposed to
   the same defect even for ISOs whose backcast does not pin. Permitted by
   rule 20 (forecast-mode 2026+ uses no measured H1-2026 actuals).
3. **The undeliverable-energy defect itself** — MWh of per-plant-month budget
   above ``nameplate x hours-in-month`` under the uniform scale, i.e. the
   energy the LP silently clips (``P[g,t] <= pmax x availability``).

Usage:
    PYTHONPATH=.:src .venv/bin/python \
        scripts/probes/_caiso130_nameplate_blast_radius.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.hydro import build_hydro_fleet, hours_per_month  # noqa: E402

# Each ISO's CURRENT keeper bundle — the recipe the blast-radius question is
# about. Read from the committed bundles so the settings below are the
# keepers' own, never a guess.
KEEPER_BUNDLES = {
    "CAISO": "caiso126_rorsplit_B",
    "ERCOT": "ercot115_coal_floor_only",
    "MISO": "miso88_egrid_hr",
    "NEISO": "neiso61_netrev_margin",
    "NYISO": "nyiso87_cmeas_minrun",
    "PJM": "pjm121_ccbelt",
}
YEARS = (2023, 2024, 2025)  # rule 20: the training window, nothing else
FORECAST_YEAR = 2026  # rule 20: forecast-mode 2026+ is unrestricted


def keeper_hydro_settings(iso: str) -> dict:
    """Return the ISO keeper's hydro gate settings from its committed bundle."""
    bundle = REPO / "results" / "calibration" / KEEPER_BUNDLES[iso]
    meta = json.loads((bundle / "meta.json").read_text())
    scen = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    return {
        "eia930_monthly": bool(meta.get("hydro_eia930_monthly", False)),
        "backfill_year": meta.get("hydro_backfill_year"),
        "ror_split": bool(scen.get("hydro_ror_split") or False),
        "min_flow_floor": bool(scen.get("hydro_min_flow_floor") or False),
    }


def _overflow_mwh(units, monthly: np.ndarray) -> tuple[float, int]:
    """Undeliverable MWh (budget above nameplate-hours) and the plant-month count."""
    hpm = hours_per_month().astype(float)
    cap = np.array([u.pmax_mw for u in units], dtype=float)[:, None] * hpm[None, :]
    over = np.maximum(0.0, monthly - cap)
    return float(over.sum()), int((over > 1e-9).sum())


def probe(iso: str, year: int, *, forecast: bool, settings: dict) -> dict:
    """Build the hydro fleet with the flag off and on; return the diff summary."""
    zone_names = get_iso_config(iso).zone_names
    common = dict(
        zone_names=zone_names,
        backfill_year=None if forecast else settings["backfill_year"],
        eia930_monthly=False if forecast else settings["eia930_monthly"],
        forecast_budget=forecast,
        ror_split=settings["ror_split"],
        min_flow_floor=settings["min_flow_floor"],
    )
    units_a, mon_a = build_hydro_fleet(iso, year, nameplate_aware_target=False, **common)
    units_b, mon_b = build_hydro_fleet(iso, year, nameplate_aware_target=True, **common)
    if mon_a is None or mon_b is None:
        return {"iso": iso, "year": year, "forecast": forecast, "status": "NO_HYDRO"}
    assert len(units_a) == len(units_b), "flag changed the plant SET — investigate"
    over_a, n_over_a = _overflow_mwh(units_a, mon_a)
    over_b, n_over_b = _overflow_mwh(units_b, mon_b)
    delta = mon_b - mon_a
    # Flat RoR levels are stamped on the units; diff them too so the ror_split
    # interaction (caiso-126 K4's nameplate clip) is visible, not inferred.
    flat_delta = 0.0
    for ua, ub in zip(units_a, units_b):
        fa = getattr(ua, "hydro_ror_flat_monthly_mw", None)
        fb = getattr(ub, "hydro_ror_flat_monthly_mw", None)
        if fa is not None and fb is not None:
            flat_delta = max(
                flat_delta, float(np.abs(np.asarray(fb) - np.asarray(fa)).max())
            )
    return {
        "iso": iso,
        "year": year,
        "forecast": forecast,
        "status": "IDENTICAL" if np.abs(delta).max() < 1e-6 else "CHANGED",
        "n_plants": len(units_a),
        "budget_twh": mon_a.sum() / 1e6,
        "moved_mwh": float(np.abs(delta).sum() / 2.0),
        "moved_pct": 100.0 * float(np.abs(delta).sum() / 2.0) / max(mon_a.sum(), 1.0),
        "undeliverable_mwh_off": over_a,
        "undeliverable_plant_months_off": n_over_a,
        "undeliverable_mwh_on": over_b,
        "undeliverable_plant_months_on": n_over_b,
        "max_plant_month_delta_mwh": float(np.abs(delta).max()),
        "max_ror_flat_delta_mw": flat_delta,
        "month_total_max_drift_mwh": float(np.abs(delta.sum(axis=0)).max()),
    }


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    rows: list[dict] = []
    for iso in sorted(KEEPER_BUNDLES):
        settings = keeper_hydro_settings(iso)
        pins = settings["eia930_monthly"]
        print(
            f"\n### {iso} — keeper hydro settings: eia930_monthly={pins}, "
            f"backfill={settings['backfill_year']}, ror_split={settings['ror_split']}, "
            f"min_flow_floor={settings['min_flow_floor']}"
        )
        if not pins:
            print(
                "    BACKCAST: monthly_target_mwh is None on this keeper "
                "=> the flag is a STRICT NO-OP by construction "
                "(load_hydro_budget only consults it inside the "
                "`if monthly_target_mwh is not None` branch). Verified below."
            )
        for year in YEARS:
            try:
                row = probe(iso, year, forecast=False, settings=settings)
            except Exception as exc:  # noqa: BLE001 — probe reports, never crashes
                row = {"iso": iso, "year": year, "forecast": False, "status": f"ERR {exc}"}
            rows.append(row)
            print(f"    backcast {year}: {row}")
        try:
            row = probe(iso, FORECAST_YEAR, forecast=True, settings=settings)
        except Exception as exc:  # noqa: BLE001
            row = {
                "iso": iso,
                "year": FORECAST_YEAR,
                "forecast": True,
                "status": f"ERR {exc}",
            }
        rows.append(row)
        print(f"    forecast {FORECAST_YEAR}: {row}")

    out = REPO / "results" / "probes" / "caiso130_nameplate_blast_radius.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
