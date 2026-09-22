"""hydro-5 phase 0: SPP / NEISO / MISO hydro dispatch census and arm predictions (zero LP).

Three sections, every number from committed inputs and the designated keepers'
own committed ``hourly/`` sidecars — no solve:

* **census** — the keeper's P1 hourly conventional-hydro class, per year:
  annual TWh, hours below 1 MW, p05/p50/p95, the share of each month's water
  in the month's top-decile load hours (a flat fleet is 0.10), and the
  within-month daily-energy SD (mean over months of the SD of daily energy
  divided by the month's mean daily energy). Beside it, the ISO's own measured
  EIA-930 ``NG: WAT`` on the model clock, where that series is admissible for
  the conventional fleet (SPP every year; NEISO from
  ``EIA930_PS_SPLIT_COMPLETE_FROM``; MISO never — it folds pumped storage).
* **arm prediction** — ``build_hydro_fleet`` under the keeper's own hydro
  inputs (``backfill_year=2024``, ``eia930_monthly=True``) with and without the
  arm's flag: RoR-class plants / MW / share of budget energy, the stamped flat
  base by month, and the energy the nameplate clip removes from the RoR
  class. That clip is NOT a G2 mechanism: the budget row is ``<=`` and the
  control's hourly cap is the same nameplate, so a plant-month whose budget
  exceeds ``nameplate x hours`` is equally undeliverable in the control. The
  G2 prediction (``g2_bound``) splits the keeper's own shortfall against its
  budget into that INFEASIBLE excess (both legs lose it) and ECONOMIC spill
  (water the control could have turbined and chose not to — the only energy
  a flat or floored plant can recover). Where that spill is ~0 the predicted
  annual move is ~0; where it is not (MISO 2020), it is the scale of the
  move to expect. For SPP also the min-flow
  floor's allocated level and its forced share of the budget.
* **swing falsification** (nyiso-111's test) — where the measured series is
  clean: the measured mean-diurnal and median-day swing against the
  classifier's shapeable nameplate. A fleet cannot swing more than the MW that
  can shape.

Run: ``PYTHONPATH=.:src .venv/bin/python scripts/probes/_hydro5_phase0.py``
(requires ``scripts/data/curate_hydro_plant_modes.py --iso SPP NEISO MISO``).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from market_sim.config.constants import EIA930_PS_FOLDED_INTO_WAT  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia930.envelopes import _hydro_wat_month_hod  # noqa: E402
from market_sim.data.fleet import _hour_to_month_index  # noqa: E402
from market_sim.data.hydro import (  # noqa: E402
    build_hydro_fleet,
    eia930_wat_level_folded,
    hours_per_month,
)
from market_sim.data.hydro_modes import load_hydro_shapeable  # noqa: E402

# (ISO, [(bundle, years)]) — the designated keepers at 2026-09-22.
KEEPERS: dict[str, list[tuple[str, list[int]]]] = {
    "SPP": [
        ("spp71_ensemble_rung", [2019, 2020, 2021, 2022]),
        ("spp71_ensemble_span", [2023, 2024, 2025]),
    ],
    "NEISO": [("neiso112_mer_span", [2020, 2021, 2022, 2023, 2024, 2025])],
    "MISO": [("miso264_anchor_span", [2020, 2021, 2022, 2023, 2024, 2025])],
}
MI = _hour_to_month_index(8760)


def class_mw(bundle: str, year: int, klass: str = "hydro") -> np.ndarray | None:
    """Return a bundle's P1 hourly MW for one class, or ``None``."""
    p = (
        ROOT
        / "results/calibration"
        / bundle
        / "hourly"
        / f"class_hourly_{year}.parquet"
    )
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    sub = df[(df["klass"] == klass) & (df["pass"] == "P1")]
    out = np.zeros(8760, dtype=float)
    g = sub.groupby("hour")["mw"].sum()
    out[g.index.to_numpy(dtype=int)] = g.to_numpy(dtype=float)
    return out


def load_mw(bundle: str, year: int) -> np.ndarray | None:
    """Return a bundle's P1 ISO-total hourly demand, or ``None``."""
    p = ROOT / "results/calibration" / bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    tot = df.groupby("hour")["demand"].sum().sort_index()
    out = np.zeros(8760, dtype=float)
    out[tot.index.to_numpy(dtype=int)] = tot.to_numpy(dtype=float)
    return out


def top_decile_share(series: np.ndarray, load: np.ndarray) -> float:
    """Mean over months of the share of the month's energy in its top-10 % load hours."""
    out = []
    for m in range(12):
        sel = MI == m
        s, lo = series[sel], load[sel]
        if s.sum() <= 0:
            continue
        n = max(1, int(0.10 * len(s)))
        out.append(float(s[np.argsort(lo)[-n:]].sum() / s.sum()))
    return float(np.mean(out))


def within_month_daily_cv(series: np.ndarray) -> float:
    """Mean over months of SD(daily energy) / mean(daily energy)."""
    daily = series.reshape(365, 24).sum(axis=1)
    dmi = MI.reshape(365, 24)[:, 0]
    out = []
    for m in range(12):
        d = daily[dmi == m]
        if d.mean() > 0:
            out.append(float(d.std() / d.mean()))
    return float(np.mean(out))


def stats(series: np.ndarray, load: np.ndarray) -> dict:
    """The census row for one hourly hydro series."""
    s = np.nan_to_num(series, nan=0.0)
    return {
        "twh": round(float(s.sum()) / 1e6, 4),
        "hours_below_1mw": int((s < 1.0).sum()),
        "p05": round(float(np.percentile(s, 5)), 1),
        "p50": round(float(np.percentile(s, 50)), 1),
        "p95": round(float(np.percentile(s, 95)), 1),
        "top_decile_share": round(top_decile_share(s, load), 4),
        "daily_cv": round(within_month_daily_cv(s), 4),
    }


def measured(iso: str, year: int) -> np.ndarray | None:
    """Return the ISO's hourly EIA-930 ``NG: WAT`` on the model clock (8760)."""
    f = _hydro_wat_month_hod(iso, year)
    if f is None:
        return None
    mw = f["mw"].to_numpy(dtype=float)[:8760]
    if len(mw) < 8760:
        return None
    return pd.Series(mw).interpolate(limit_direction="both").to_numpy()


def swing(mw: np.ndarray) -> dict:
    """Mean-diurnal and median-day swing (max - min of the hour-of-day profile)."""
    day = mw.reshape(365, 24)
    mean_prof = day.mean(axis=0)
    med_day = np.median(day.max(axis=1) - day.min(axis=1))
    return {
        "mean_diurnal_swing_mw": round(float(mean_prof.max() - mean_prof.min()), 1),
        "median_daily_range_mw": round(float(med_day), 1),
        "p95_daily_range_mw": round(
            float(np.percentile(day.max(axis=1) - day.min(axis=1), 95)), 1
        ),
    }


def predict(iso: str, year: int) -> dict:
    """``build_hydro_fleet`` control vs arm(s) under the keeper's hydro inputs."""
    zones = get_iso_config(iso).zone_names
    kw = dict(backfill_year=2024, eia930_monthly=True)
    units, energy = build_hydro_fleet(iso, year, zones, **kw)
    hpm = hours_per_month().astype(float)
    rec: dict = {
        "plants": len(units),
        "nameplate_mw": round(sum(u.pmax_mw for u in units), 1),
        "budget_twh": round(float(energy.sum()) / 1e6, 4),
    }
    modes = load_hydro_shapeable(iso) or {}
    cls = np.array([modes.get(int(u.plant_code)) for u in units], dtype=object)
    ror = np.array([c is False for c in cls])
    unclassified = np.array([c is None for c in cls])
    caps = np.array([u.pmax_mw for u in units])
    flat = energy[ror] / hpm[np.newaxis, :]
    over = np.clip(flat - caps[ror][:, np.newaxis], 0.0, None)
    infeasible = np.clip(energy - caps[:, np.newaxis] * hpm[np.newaxis, :], 0.0, None)
    rec["infeasible_excess_twh"] = round(float(infeasible.sum()) / 1e6, 5)
    rec["ror"] = {
        "plants": int(ror.sum()),
        "mw": round(float(caps[ror].sum()), 1),
        "energy_share": round(float(energy[ror].sum() / energy.sum()), 4),
        "flat_base_mw_min": round(
            float(np.minimum(flat, caps[ror][:, None]).sum(0).min()), 1
        ),
        "flat_base_mw_max": round(
            float(np.minimum(flat, caps[ror][:, None]).sum(0).max()), 1
        ),
        "flat_base_by_month": [
            round(float(v), 1) for v in np.minimum(flat, caps[ror][:, None]).sum(0)
        ],
        "clip_plant_months": int((over > 0).sum()),
        "clip_removed_twh": round(float((over * hpm[np.newaxis, :]).sum()) / 1e6, 5),
        "clip_removed_pct_of_budget": round(
            100.0 * float((over * hpm[np.newaxis, :]).sum()) / float(energy.sum()), 4
        ),
        "unclassified_plants": int(unclassified.sum()),
        "unclassified_mw": round(float(caps[unclassified].sum()), 1),
        "unclassified_energy_share": round(
            float(energy[unclassified].sum() / energy.sum()), 4
        ),
        "shapeable_mw": round(float(caps[~ror].sum()), 1),
    }
    # Cross-check with the loader itself (the clip lives there).
    u_arm, e_arm = build_hydro_fleet(iso, year, zones, ror_split=True, **kw)
    stamped = [u for u in u_arm if getattr(u, "hydro_ror_flat_monthly_mw", None)]
    stamped_twh = sum(
        float(np.dot(np.asarray(u.hydro_ror_flat_monthly_mw), hpm)) for u in stamped
    )
    rec["ror"]["loader_stamped_plants"] = len(stamped)
    rec["ror"]["loader_stamped_twh"] = round(stamped_twh / 1e6, 4)
    if iso == "SPP" or not eia930_wat_level_folded(iso, year):
        u_f, e_f = build_hydro_fleet(iso, year, zones, min_flow_floor=True, **kw)
        fl = np.array(
            [
                np.asarray(u.hydro_min_flow_monthly_mw)
                if getattr(u, "hydro_min_flow_monthly_mw", None)
                else np.zeros(12)
                for u in u_f
            ]
        )
        lvl = fl.sum(axis=0)
        rec["floor"] = {
            "level_mw_min": round(float(lvl.min()), 1),
            "level_mw_max": round(float(lvl.max()), 1),
            "forced_share_of_budget": round(
                float((lvl * hpm).sum()) / float(e_f.sum()), 4
            ),
        }
    return rec


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    out: dict = {}
    for iso, legs in KEEPERS.items():
        for bundle, years in legs:
            for y in years:
                h = class_mw(bundle, y)
                load = load_mw(bundle, y)
                rec: dict = {"keeper_bundle": bundle}
                rec["keeper"] = stats(h, load) if h is not None else None
                rec["prediction"] = predict(iso, y)
                clean = (
                    iso not in EIA930_PS_FOLDED_INTO_WAT
                    and not eia930_wat_level_folded(iso, y)
                )
                act = measured(iso, y)
                if act is not None:
                    rec["measured_930_wat"] = stats(act, load)
                    rec["measured_930_wat"]["admissible_for_conventional"] = clean
                    if clean:
                        rec["measured_swing"] = swing(act)
                        # The RoR class alone can never deliver less than its
                        # flat base, so the measured WHOLE fleet going below
                        # it is evidence against the classifier. Telemetry
                        # zeros (< 1 MW, single gap hours) are excluded.
                        base = np.asarray(
                            rec["prediction"]["ror"]["flat_base_by_month"]
                        )
                        p01 = np.array(
                            [
                                np.percentile(act[(MI == m) & (act >= 1.0)], 1)
                                for m in range(12)
                            ]
                        )
                        rec["ror_base_vs_measured_p01"] = {
                            "months_base_above_p01": [
                                m + 1 for m in range(12) if base[m] > p01[m]
                            ],
                            "min_ratio_p01_over_base": round(
                                float(np.min(p01 / base)), 3
                            ),
                        }
                if h is not None:
                    pr = rec["prediction"]
                    short = pr["budget_twh"] - float(h.sum()) / 1e6
                    spill = short - pr["infeasible_excess_twh"]
                    rec["g2_bound"] = {
                        "keeper_shortfall_twh": round(short, 5),
                        "economic_spill_twh": round(spill, 5),
                        "max_upward_move_pct": round(
                            100.0 * max(spill, 0.0) / (float(h.sum()) / 1e6), 4
                        ),
                    }
                out[f"{iso} {y}"] = rec
                print(f"{iso} {y} done", file=sys.stderr)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
