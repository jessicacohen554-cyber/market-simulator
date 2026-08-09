"""FFR-8B Phase-1: the E1 committed-capability dispersion decomposition.

Implements the PRE-REGISTERED method of
``docs/handoffs/ffr-8b-rebase-dispersion-2026-08-09.md`` §1.3 — a chain of
single-ingredient swaps between the arm's own E1 reserve quantity and the
measured RTOLCAP distribution, per year (2024, 2025), each read at matched
quantiles and knee-visit counts:

    C   (dump)  the arm's r_online: evolved fleet, forward net load,
                phys-headroom min(), arm storage-AS scalar
    C''         raw formula (no phys min), evolved fleet, arm net load,
                arm storage scalar          -> C vs C''  = phys-bind step
    C'          raw formula, ACTUAL fleet (vintage-2020 minus FFR-7C
                corrected exits), arm net load, arm storage scalar
                                            -> C'' vs C' = fleet-length step
    B~          raw formula, actual fleet, MEASURED realized net load
                (clean demand proxy - measured wind - solar), arm storage
                scalar                      -> C' vs B~  = net-load realization
    B           raw formula, actual fleet, measured net load, MEASURED
                storage-AS series (the derive fit basis)
                                            -> B~ vs B  = storage-term basis
    A           measured RTOLCAP (NP6-905-CD; 2025 truncated at RTC+B)
                                            -> B vs A   = commitment share

Share (3) — the outage part E4 ALREADY carries — is reported as the model's
own sigma_R (the dump's seasonal WEFOR variance) against the B->A within-cell
residual std, plus the tail view C - 2*sigma_R vs A's p1. The published
curve's intra-hour sigma appears NOWHERE here (different horizon — the
pre-registered double-count guard).

The measured RTOLCAP series is DIAGNOSIS-ONLY: it validates or refutes, it
parameterizes nothing (rule 13). Read-only; never solves. Usage::

    uv run python scripts/probes/ffr8b_e1_dispersion.py \
        --bundle results/hindcast/ercot-2021-2025-t1ff-armr-ffr8b-base \
        --out docs/handoffs/ffr-8b/e1-dispersion-2026-08-09.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    ERCOT_RTOLCAP_FWD_SEASON_BY_MONTH,
)
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    _ercot_rtolcap_fwd_decile,
    _ercot_rtolcap_fwd_month,
    ercot_rtolcap_forward_supply_cap_mw,
    ercot_storage_as_reserve_mw,
)

YEARS = (2024, 2025)
RTCB_GOLIVE_HOUR = 338 * 24  # 2025-12-05 RTC+B go-live, non-leap clock

# Fallback-curve knee levels (reserves at adder = $10/$100/$1000, lambda=$30)
# — the committed FFR-8A Part-A values (part-a-measured-2026-08-08.json).
KNEES_MW = {"$10": 7415.0, "$100": 6200.0, "$1000": 4578.0}

# FFR-7C corrected-target thermal exits by model class (the ffr8a ablation
# probe's construction, kept verbatim for comparability — subtracted whole,
# not COD-time-gated, exactly as the pre-epoch term-(c) re-price did).
ACTUAL_EXITS_BY_CLASS_MW: dict[str, float] = {
    "COAL": 1008.0,
    "ST_GAS": 882.0,
    "CC_REGULAR": 119.0,
}


class _ClassFleet:
    """Minimal FleetArrays stand-in: per-class pmax rows + plant_group."""

    def __init__(self, class_names, class_pmax):
        self.pmax = np.asarray(class_pmax, dtype=float)
        self.plant_group = np.asarray(class_names, dtype=object)


def _q(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    return {
        "n": int(x.size),
        "mean": round(float(x.mean()), 1),
        "p50": round(float(np.percentile(x, 50)), 1),
        "p25": round(float(np.percentile(x, 25)), 1),
        "p10": round(float(np.percentile(x, 10)), 1),
        "p5": round(float(np.percentile(x, 5)), 1),
        "p1": round(float(np.percentile(x, 1)), 1),
        "min": round(float(x.min()), 1),
    }


def _knees(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    return {k: int((x <= v).sum()) for k, v in KNEES_MW.items()}


def _formula_r_online(
    cfg, class_names, class_pmax, net_load, storage
) -> np.ndarray:
    """rows[0] of the raw forward formula (NO phys bound) on a class fleet."""
    T = int(len(net_load))
    fleet = _ClassFleet(class_names, class_pmax)
    storage_arr = (
        np.full(T, float(storage)) if np.isscalar(storage) else np.asarray(storage)[:T]
    )
    rows = ercot_rtolcap_forward_supply_cap_mw(
        cfg, fleet, T, net_load=np.asarray(net_load, dtype=float),
        storage_reserve=storage_arr, include_offline=True,
    )
    if rows is None:
        raise SystemExit("formula returned None (no plant_group)")
    return rows[0]


def _measured_reserves(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(hour_of_year, rtolcap) valid rows of the NP6-905-CD telemetry."""
    import pandas as pd

    path = RAW_DATA_DIR / "ercot" / f"ercot_{year}_ordc_reserves_hourly.parquet"
    df = pd.read_parquet(path)
    if year == 2025:
        df = df.iloc[:RTCB_GOLIVE_HOUR]
    rtolcap = df["rtolcap"].to_numpy(dtype=float)
    hour = df["hour"].to_numpy(dtype=int)
    ok = np.isfinite(rtolcap)
    return hour[ok], rtolcap[ok]


def _measured_net_load(year: int) -> np.ndarray:
    """Measured system net load, 8760 non-leap clock (clean generation store).

    Total generation stands in for served load (interchange < 1 % of ERCOT
    load — the ffr8a Part-A construction, kept verbatim); net load =
    total - wind - solar, the axis the share tables were derived on.
    """
    import pandas as pd

    path = REPO / "data/clean/generation/ERCOT" / f"generation_{year}.parquet"
    df = pd.read_parquet(path, columns=["interval_start_local", "fuel", "generation_mw"])
    ts = pd.to_datetime(df["interval_start_local"])
    df = df[(ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))]
    ts = pd.to_datetime(df["interval_start_local"])
    hour = (ts.dt.dayofyear - 1) * 24 + ts.dt.hour
    if int(year) % 4 == 0:
        after = (ts.dt.month > 2).to_numpy()
        hour = hour.to_numpy() - np.where(after, 24, 0)
    else:
        hour = hour.to_numpy()
    df = df.assign(hour=hour)
    piv = df.pivot_table(index="hour", columns="fuel", values="generation_mw", aggfunc="sum")
    piv = piv.reindex(range(8760)).interpolate(limit_direction="both")
    fuels = {str(c).lower(): c for c in piv.columns}
    wind = piv[fuels["wind"]].to_numpy(dtype=float) if "wind" in fuels else np.zeros(8760)
    solar = piv[fuels["solar"]].to_numpy(dtype=float) if "solar" in fuels else np.zeros(8760)
    total = piv.sum(axis=1).to_numpy(dtype=float)
    return total - wind - solar


def _cells(net_load_8760: np.ndarray) -> np.ndarray:
    """(season*100 + decile) cell id per hour, the formula's own conditioning."""
    month = _ercot_rtolcap_fwd_month()[: len(net_load_8760)]
    season = np.asarray(ERCOT_RTOLCAP_FWD_SEASON_BY_MONTH, dtype=int)[month - 1]
    decile = _ercot_rtolcap_fwd_decile(np.asarray(net_load_8760, dtype=float))
    return season * 100 + decile


def _within_cell_resid_std(resid: np.ndarray, cells: np.ndarray) -> dict:
    """Pooled within-cell std of a residual + the worst (top-net-load) cells."""
    tot_n = 0
    tot_var = 0.0
    per_cell = {}
    for c in np.unique(cells):
        r = resid[cells == c]
        if r.size < 5:
            continue
        v = float(np.var(r, ddof=1))
        tot_var += v * (r.size - 1)
        tot_n += r.size - 1
        per_cell[int(c)] = {"n": int(r.size), "std": round(float(np.sqrt(v)), 1),
                            "mean": round(float(r.mean()), 1)}
    pooled = float(np.sqrt(tot_var / max(tot_n, 1)))
    top = {k: v for k, v in per_cell.items() if k % 100 >= 9}  # top-decile bins
    return {"pooled_within_cell_std": round(pooled, 1), "top_decile_cells": top}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, help="the ffr8b-base out-dir")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    bundle = Path(args.bundle)
    iso_dir = bundle / "ERCOT"
    keys = sorted(d for d in iso_dir.iterdir() if d.is_dir())
    if len(keys) != 1:
        raise SystemExit(f"{iso_dir}: expected one cache-key dir, found {keys}")
    cache_dir = keys[0]
    cfg = ScenarioConfig(iso="ERCOT", mode="forecast")

    # Vintage-2020 classes from the 2021-solve dump; actual fleet = minus exits.
    with np.load(cache_dir / "screen_signal_diag_2021_for_2022.npz") as z:
        vintage_names = [str(c) for c in z["class_names"]]
        vintage_pmax = np.asarray(z["class_pmax_mw"], dtype=float)
    actual_pmax = np.array(
        [
            max(p - ACTUAL_EXITS_BY_CLASS_MW.get(c, 0.0), 0.0)
            for c, p in zip(vintage_names, vintage_pmax)
        ]
    )

    result: dict = {
        "probe": "ffr8b_e1_dispersion phase 1",
        "cache_dir": str(cache_dir),
        "actual_fleet_note": (
            "vintage-2020 classes minus FFR-7C corrected exits "
            f"({ACTUAL_EXITS_BY_CLASS_MW}), the ffr8a term-(c) construction"
        ),
    }

    dump_by_entering = {2024: "screen_signal_diag_2023_for_2024.npz",
                        2025: "screen_signal_diag_2024_for_2025.npz"}
    for year in YEARS:
        with np.load(cache_dir / dump_by_entering[year]) as z:
            d = {k: z[k] for k in z.files}
        T = int(d["net_load_system_mw"].shape[0])
        arm_names = [str(c) for c in d["class_names"]]
        arm_pmax = np.asarray(d["class_pmax_mw"], dtype=float)
        arm_nl = np.asarray(d["net_load_system_mw"], dtype=float)
        arm_storage_as = float(d["storage_as_mw"])
        phys = np.asarray(d["installed_headroom_mw"], dtype=float)
        sigma_r = np.asarray(d["sigma_r_mw"], dtype=float)

        C = np.asarray(d["r_online_mw"], dtype=float)
        C2 = _formula_r_online(cfg, arm_names, arm_pmax, arm_nl, arm_storage_as)
        # Self-check: C must equal min(C'', phys) (the runner's own identity).
        ident = float(np.max(np.abs(np.minimum(C2, phys) - C)))
        C1 = _formula_r_online(cfg, vintage_names, actual_pmax, arm_nl, arm_storage_as)

        nl_meas = _measured_net_load(year)
        Btilde = _formula_r_online(cfg, vintage_names, actual_pmax, nl_meas, arm_storage_as)
        storage_meas = ercot_storage_as_reserve_mw(year, 8760)
        B = _formula_r_online(cfg, vintage_names, actual_pmax, nl_meas, storage_meas)

        hour_meas, A = _measured_reserves(year)
        B_matched = B[hour_meas]
        resid = A - B_matched
        cells = _cells(nl_meas)[hour_meas]

        year_out = {
            "identity_check_max_abs_C_vs_min(C2,phys)": round(ident, 3),
            "series_quantiles_mw": {
                "A_measured_rtolcap": _q(A),
                "B_formula_measured_nl_measured_storage": _q(B_matched),
                "Btilde_formula_measured_nl_arm_storage": _q(Btilde),
                "Cprime_formula_arm_nl_actual_fleet": _q(C1),
                "C2_formula_arm_nl_evolved_fleet": _q(C2),
                "C_arm_r_online_phys_bounded": _q(C),
            },
            "knee_visits_h": {
                "A": _knees(A),
                "B": _knees(B_matched),
                "Btilde": _knees(Btilde),
                "Cprime": _knees(C1),
                "C2": _knees(C2),
                "C": _knees(C),
            },
            "steps_p1_p5_gaps_mw": {
                "phys_bind_C_vs_C2": {
                    "h_bound": int((C < C2 - 0.5).sum()),
                    "p1_delta": round(float(np.percentile(C, 1) - np.percentile(C2, 1)), 1),
                    "p5_delta": round(float(np.percentile(C, 5) - np.percentile(C2, 5)), 1),
                },
                "fleet_length_C2_vs_Cprime": {
                    "p1_delta": round(float(np.percentile(C2, 1) - np.percentile(C1, 1)), 1),
                    "p5_delta": round(float(np.percentile(C2, 5) - np.percentile(C1, 5)), 1),
                },
                "net_load_realization_Cprime_vs_Btilde": {
                    "p1_delta": round(float(np.percentile(C1, 1) - np.percentile(Btilde, 1)), 1),
                    "p5_delta": round(float(np.percentile(C1, 5) - np.percentile(Btilde, 5)), 1),
                },
                "storage_basis_Btilde_vs_B": {
                    "p1_delta": round(float(np.percentile(Btilde, 1) - np.percentile(B_matched, 1)), 1),
                    "arm_storage_as_mw": round(arm_storage_as, 1),
                    "measured_storage_as_q": _q(np.asarray(storage_meas)[hour_meas]),
                },
                "commitment_B_vs_A": {
                    "p1_delta": round(float(np.percentile(B_matched, 1) - np.percentile(A, 1)), 1),
                    "p5_delta": round(float(np.percentile(B_matched, 5) - np.percentile(A, 5)), 1),
                    "p50_delta": round(float(np.percentile(B_matched, 50) - np.percentile(A, 50)), 1),
                },
            },
            "commitment_residual_A_minus_B": {
                "overall_std": round(float(np.std(resid, ddof=1)), 1),
                "overall_mean": round(float(np.mean(resid)), 1),
                **_within_cell_resid_std(resid, cells),
            },
            "outage_share_already_carried": {
                "sigma_r_mw_q": _q(sigma_r),
                "sigma_r_over_within_cell_std": None,  # filled below
                "C_minus_2sigma_p1": round(
                    float(np.percentile(C - 2.0 * sigma_r, 1)), 1
                ),
                "A_p1": round(float(np.percentile(A, 1)), 1),
            },
        }
        s_resid = year_out["commitment_residual_A_minus_B"]["pooled_within_cell_std"]
        year_out["outage_share_already_carried"]["sigma_r_over_within_cell_std"] = (
            round(float(np.mean(sigma_r)) / s_resid, 3) if s_resid else None
        )
        result[str(year)] = year_out

    out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
