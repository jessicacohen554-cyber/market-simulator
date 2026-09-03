"""miso-204 phase 0 — DECOMPOSE THE C3a-2025 TAIL INTO ITS PUBLISHED MEC / MCC / MLC.

miso-202 located C3a-2025 in **15 hours** (the top 1 % of actual Jun-Jul hours)
that carry 99.9 % of the entire mean gap; miso-203 established those hours are an
**evening net-load ramp** window, not the hot or the peak-load hours.  Neither
session read the ACTUAL price's own components: both committed probes filter
``value == "LMP"`` and discard the ``MCC`` and ``MLC`` rows of the same file.

This probe reads them.  ``MEC = LMP - MCC - MLC`` is an identity, not an
estimate, and carries zero free parameters.  The question it answers is which
object the C3a-2025 residual is — system-wide ENERGY price formation, or
CONGESTION the model's six-zone representation cannot express — because the two
re-aim the lever queue at completely different (and differently adjudicated)
mechanism families.

Every gate, decision rule, population and trap counter-measurement is fixed in
``results/calibration/PREREG-miso204-lmp-component-decomposition-2026-09-03.md``,
pushed at ``fd6c4dff`` BEFORE any number in this file was computed.

Inputs are committed artifacts only; **no LP is solved**.  Rule 22
``[R-HOLDOUT]`` — 2023/2024/2025 only.

Usage::

    python3 scripts/probes/_miso204_lmp_component_decomposition.py
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER = REPO / "results/calibration/miso202_unitclip_B"
HUB_LMP = REPO / "data/raw/lmp-data/MISO"
OUT = REPO / "results/calibration/_miso204_lmp_component_decomposition.json"

HE = [f"he{i:02d}" for i in range(1, 25)]
MONTH_LENS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# TRAP 4 — the load-weighted robustness basis.  MISO's eight trading hubs mapped
# onto the six model zones.  MISO-Plains has no hub of its own (the model splits
# MISO North/Central-West where the real market publishes one MINN hub), so
# MINN.HUB carries MISO-West AND MISO-Plains.  Declared here rather than tuned;
# this basis is a ROBUSTNESS CHECK ONLY and by PREREG §4 TRAP 4 it can add a
# caveat, never flip the verdict.
HUB_TO_ZONES = {
    "MINN.HUB": ("MISO-West", "MISO-Plains"),
    "ILLINOIS.HUB": ("MISO-Illinois",),
    "INDIANA.HUB": ("MISO-Indiana",),
    "MICHIGAN.HUB": ("MISO-East",),
    "ARKANSAS.HUB": ("MISO-South",),
    "LOUISIANA.HUB": ("MISO-South",),
    "MS.HUB": ("MISO-South",),
    "TEXAS.HUB": ("MISO-South",),
}


def _hour_month(hours: int = HOURS) -> np.ndarray:
    """Calendar month per hour on the model's FIXED non-leap 8760 clock."""
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)])[
        :hours
    ]


def _model_stamp(h: int) -> str:
    """'MM-DD hHH' on the model's own 8760 clock (Feb is 28 days in every year)."""
    doy, hod = divmod(int(h), 24)
    m = 0
    while doy >= MONTH_LENS[m]:
        doy -= MONTH_LENS[m]
        m += 1
    return f"{m + 1:02d}-{doy + 1:02d} h{hod:02d}"


def _true_stamp(year: int, h: int) -> str:
    """TRAP 2 — the REAL calendar date of actual-series index ``h``.

    The committed construction takes ``arr[:8760]`` from the raw file, which has
    366 days in 2024, so every actual hour after Feb 28 of a leap year sits 24 h
    ahead of the model clock.  This reports the real date the component values
    belong to; the decomposition itself is immune because all three components
    are read at the same index of the same series.
    """
    doy, hod = divmod(int(h), 24)
    d = dt.date(year, 1, 1) + dt.timedelta(days=doy)
    return f"{d.isoformat()} HE{hod + 1:02d}"


def hub_component_matrix(year: int, label: str) -> tuple[np.ndarray, list[str]] | None:
    """(8 x 8760) matrix of one published component, and the hub order.

    Same construction as ``_miso202_c3a_2025_anatomy`` / ``_miso203_…`` — read
    the gz, filter the ``value`` label, pivot (date x he) per hub, ravel to a
    flat hourly series, truncate to 8760 — applied to each of the three labels
    so all three sit on the index that selected the 15 hours.
    """
    path = HUB_LMP / f"miso_hub_lmp_{year}_rt.csv.gz"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["value"] == label].copy()
    df["date"] = pd.to_datetime(df["date"])
    hubs = sorted(df["node"].unique())
    rows = []
    for hub in hubs:
        g = df[df["node"] == hub].groupby("date")[HE].mean().sort_index()
        arr = g.to_numpy().ravel()
        if len(arr) < HOURS:
            return None
        rows.append(arr[:HOURS])
    return np.vstack(rows), hubs


def model_price(year: int) -> np.ndarray:
    """The keeper's committed P1 zone-mean price — the anatomy's own construction."""
    sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    return sysd.groupby("hour")["price"].mean().sort_index().to_numpy()[:HOURS]


def zone_demand(year: int) -> dict[str, np.ndarray]:
    """The keeper's committed P1 zonal demand — the TRAP 4 weighting basis."""
    sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    return {
        z: g.sort_values("hour")["demand"].to_numpy()[:HOURS]
        for z, g in sysd.groupby("zone")
    }


def _shares(
    excess: np.ndarray, energy: np.ndarray, cong: np.ndarray, loss: np.ndarray
) -> dict:
    """PREREG §1.4 — the mean-share decomposition, plus the R-1 per-hour counts."""
    me = float(np.mean(excess))
    stack = np.vstack([energy, cong, loss])
    largest = np.argmax(np.abs(stack), axis=0)
    return {
        "n_hours": int(len(excess)),
        "mean_excess": round(me, 3),
        "mean_energy": round(float(np.mean(energy)), 3),
        "mean_cong": round(float(np.mean(cong)), 3),
        "mean_loss": round(float(np.mean(loss)), 3),
        "share_energy": round(float(np.mean(energy) / me), 4) if me else None,
        "share_cong": round(float(np.mean(cong) / me), 4) if me else None,
        "share_loss": round(float(np.mean(loss) / me), 4) if me else None,
        "r1_hours_largest_energy": int(np.sum(largest == 0)),
        "r1_hours_largest_cong": int(np.sum(largest == 1)),
        "r1_hours_largest_loss": int(np.sum(largest == 2)),
        "median_excess": round(float(np.median(excess)), 3),
        "median_energy": round(float(np.median(energy)), 3),
        "median_cong": round(float(np.median(cong)), 3),
        "median_loss": round(float(np.median(loss)), 3),
    }


def _dispersion(mat: np.ndarray, idx: np.ndarray) -> dict:
    """G-2 — cross-hub spread of one component over an hour population."""
    sub = mat[:, idx]
    return {
        "mean_max_minus_min": round(float(np.mean(sub.max(0) - sub.min(0))), 3),
        "median_max_minus_min": round(float(np.median(sub.max(0) - sub.min(0))), 3),
        "mean_sd": round(float(np.mean(sub.std(0, ddof=0))), 3),
    }


def main() -> None:
    report: dict = {
        "charter": (
            "miso-204 phase 0 — the charter's (a)/(b)/(c): decompose the actual "
            "price in the 15 scarce hours into its published MEC / MCC / MLC and "
            "state which object the C3a-2025 residual is. PRE-REGISTERED at "
            "PREREG-miso204-lmp-component-decomposition-2026-09-03.md, pushed "
            "BLIND at fd6c4dff before any number here existed."
        ),
        "keeper": "2026-09-03-miso-202-unitclip",
        "inputs": "committed artifacts only — no solve",
        "identity": "MEC = LMP - MCC - MLC (MISO settlement identity, zero DOF)",
        "prereg_commit": "fd6c4dff",
        "years": {},
    }

    for year in YEARS:
        y: dict = {}
        got = hub_component_matrix(year, "LMP")
        if got is None:
            report["years"][str(year)] = {"error": "no committed hub RT file"}
            continue
        lmp_m, hubs = got
        mcc_m, hubs_c = hub_component_matrix(year, "MCC")
        mlc_m, hubs_l = hub_component_matrix(year, "MLC")

        # ---- N-2: coverage alignment + the additive identity ----------------
        mec_m = lmp_m - mcc_m - mlc_m
        y["n2_identity"] = {
            "hub_order_identical": bool(hubs == hubs_c == hubs_l),
            "hubs": hubs,
            "max_abs_reconstruction_residual": float(
                np.max(np.abs(lmp_m - (mec_m + mcc_m + mlc_m)))
            ),
        }

        # ---- N-1: is MEC hub-invariant? (the sign-convention counter-meas.) --
        spread_pref = mec_m.max(0) - mec_m.min(0)
        alt_m = lmp_m + mcc_m + mlc_m  # the alternative convention, TRAP 1
        spread_alt = alt_m.max(0) - alt_m.min(0)
        month = _hour_month()
        jj_mask = (month == 6) | (month == 7)
        n1_pop = np.where(jj_mask | np.ones(HOURS, bool))[0]  # OBJ subset of JJ ⊂ all
        y["n1_hub_invariance"] = {
            "convention_tested": "MEC = LMP - MCC - MLC",
            "n_hours": int(len(n1_pop)),
            "frac_within_0.51": round(float(np.mean(spread_pref[n1_pop] < 0.51)), 6),
            "max_spread": round(float(np.max(spread_pref[n1_pop])), 4),
            "p99_spread": round(float(np.percentile(spread_pref[n1_pop], 99)), 4),
            "jun_jul_frac_within_0.51": round(
                float(np.mean(spread_pref[jj_mask] < 0.51)), 6
            ),
            "alt_convention_frac_within_0.51": round(
                float(np.mean(spread_alt[n1_pop] < 0.51)), 6
            ),
            "alt_convention_max_spread": round(float(np.max(spread_alt[n1_pop])), 4),
        }

        # ---- the populations, frozen in PREREG §1.3 -------------------------
        lmp = lmp_m.mean(0)
        mcc = mcc_m.mean(0)
        mlc = mlc_m.mean(0)
        mec = mec_m.mean(0)
        pmod = model_price(year)

        jj = np.where(jj_mask)[0]
        thr = float(np.percentile(lmp[jj], 99.0))
        obj = jj[lmp[jj] >= thr]
        yr1_thr = float(np.percentile(lmp, 99.0))
        yr1 = np.where(lmp >= yr1_thr)[0]

        y["populations"] = {
            "OBJ": {"n": int(len(obj)), "threshold_usd_per_mwh": round(thr, 2)},
            "JJ": {"n": int(len(jj))},
            "YR1": {"n": int(len(yr1)), "threshold_usd_per_mwh": round(yr1_thr, 2)},
        }

        # ---- G-1: the shares, equal-weighted hub basis (the VERDICT basis) --
        def decomp(idx: np.ndarray) -> dict:
            return _shares(
                lmp[idx] - pmod[idx], mec[idx] - pmod[idx], mcc[idx], mlc[idx]
            )

        y["g1_shares_equal_weighted"] = {
            "OBJ": decomp(obj),
            "JJ": decomp(jj),
            "YR1": decomp(yr1),
        }
        y["g1_levels_OBJ"] = {
            "mean_actual_lmp": round(float(np.mean(lmp[obj])), 2),
            "mean_actual_mec": round(float(np.mean(mec[obj])), 2),
            "mean_actual_mcc": round(float(np.mean(mcc[obj])), 2),
            "mean_actual_mlc": round(float(np.mean(mlc[obj])), 2),
            "mean_model_price": round(float(np.mean(pmod[obj])), 2),
            "mean_jj_actual_mec": round(float(np.mean(mec[jj])), 2),
            "mean_jj_model_price": round(float(np.mean(pmod[jj])), 2),
        }

        # ---- TRAP 4: the load-weighted hub basis (robustness only) ---------
        zd = zone_demand(year)
        w = np.zeros((len(hubs), HOURS))
        for i, hub in enumerate(hubs):
            zones = HUB_TO_ZONES[hub]
            share = sum(zd[z] for z in zones if z in zd)
            # a zone served by k hubs splits its demand equally across them
            k = sum(1 for h2 in hubs if set(HUB_TO_ZONES[h2]) & set(zones))
            w[i] = share / max(k, 1)
        w = w / w.sum(0, keepdims=True)
        lmp_w = (lmp_m * w).sum(0)
        mcc_w = (mcc_m * w).sum(0)
        mlc_w = (mlc_m * w).sum(0)
        mec_w = (mec_m * w).sum(0)
        y["trap4_shares_load_weighted"] = {
            "basis": (
                "hubs weighted by the keeper's own committed P1 zonal demand via "
                "HUB_TO_ZONES; MINN.HUB carries MISO-West AND MISO-Plains. "
                "ROBUSTNESS ONLY — cannot flip the verdict (PREREG TRAP 4)."
            ),
            "OBJ": _shares(
                lmp_w[obj] - pmod[obj], mec_w[obj] - pmod[obj], mcc_w[obj], mlc_w[obj]
            ),
        }

        # ---- G-2: cross-hub dispersion -------------------------------------
        y["g2_dispersion"] = {
            "LMP": {"OBJ": _dispersion(lmp_m, obj), "JJ": _dispersion(lmp_m, jj)},
            "MCC": {"OBJ": _dispersion(mcc_m, obj), "JJ": _dispersion(mcc_m, jj)},
            "MEC": {"OBJ": _dispersion(mec_m, obj), "JJ": _dispersion(mec_m, jj)},
        }
        # descriptive companion: the MODEL's own cross-zone spread in the same
        # hours, so "the hubs split" is read against whether the model splits.
        sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        zmat = np.vstack(
            [
                g.sort_values("hour")["price"].to_numpy()[:HOURS]
                for _, g in sysd.groupby("zone")
            ]
        )
        y["g2_dispersion"]["MODEL_zone_price"] = {
            "OBJ": _dispersion(zmat, obj),
            "JJ": _dispersion(zmat, jj),
        }
        jj_lmp_spread = y["g2_dispersion"]["LMP"]["JJ"]["mean_max_minus_min"]
        y["g2_dispersion"]["obj_over_jj_ratio_LMP"] = (
            round(
                y["g2_dispersion"]["LMP"]["OBJ"]["mean_max_minus_min"] / jj_lmp_spread,
                3,
            )
            if jj_lmp_spread
            else None
        )

        # ---- the per-hour table, with TRAP 2's true calendar date ----------
        y["hours"] = [
            {
                "hour_index": int(h),
                "model_clock_stamp": _model_stamp(h),
                "true_calendar_stamp": _true_stamp(year, h),
                "actual_lmp": round(float(lmp[h]), 2),
                "actual_mec": round(float(mec[h]), 2),
                "actual_mcc": round(float(mcc[h]), 2),
                "actual_mlc": round(float(mlc[h]), 2),
                "model_price": round(float(pmod[h]), 2),
                "excess": round(float(lmp[h] - pmod[h]), 2),
                "energy": round(float(mec[h] - pmod[h]), 2),
                "cong": round(float(mcc[h]), 2),
                "loss": round(float(mlc[h]), 2),
                "hub_lmp_max_minus_min": round(
                    float(lmp_m[:, h].max() - lmp_m[:, h].min()), 2
                ),
                "hub_mcc_max_minus_min": round(
                    float(mcc_m[:, h].max() - mcc_m[:, h].min()), 2
                ),
                "hub_mec_max_minus_min": round(
                    float(mec_m[:, h].max() - mec_m[:, h].min()), 4
                ),
            }
            for h in obj
        ]

        # ---- TRAP 2, stated numerically ------------------------------------
        leap = (year % 4 == 0 and year % 100 != 0) or year % 400 == 0
        y["trap2_calendar"] = {
            "raw_file_days": 366 if leap else 365,
            "model_clock_days": 365,
            "actual_vs_model_offset_after_feb28_hours": 24 if leap else 0,
            "note": (
                "The decomposition is computed entirely within the actual series "
                "at one index, so all three components belong to the same real "
                "hour and are unaffected. Any MODEL-vs-ACTUAL hour-matched "
                "quantity in a leap year is offset by the hours above."
            ),
        }

        # ---- SECTION E — POST-HOC, NON-ADJUDICATING, NOT PRE-REGISTERED ----
        # G-1 returned share_cong NEGATIVE, i.e. the eight trading hubs sit on
        # the CHEAP side of congestion in the object's hours, so the series C3a
        # scores the model against is BELOW MISO's own system energy price.  That
        # raises a question about the INSTRUMENT which the PREREG did not
        # anticipate and which this block only measures.  It carries NO gate, NO
        # decision rule and licenses NOTHING — the miso-203 G-E discipline.
        load = sysd.groupby("hour")["demand"].sum().sort_index().to_numpy()[:HOURS]
        wsum = float(load.sum())

        def lw(v: np.ndarray) -> float:
            return float(np.dot(v, load) / wsum)

        a_lmp, a_mec, m_p = lw(lmp), lw(mec), lw(pmod)
        y["e_posthoc_basis"] = {
            "status": (
                "POST-HOC, NOT PRE-REGISTERED, NO GATE, LICENSES NOTHING. "
                "Measured because G-1 returned a NEGATIVE congestion share."
            ),
            "load_weighted_annual": {
                "actual_hub_lmp": round(a_lmp, 4),
                "actual_system_mec": round(a_mec, 4),
                "model_price": round(m_p, 4),
                "hub_congestion_wedge": round(lw(mcc), 4),
                "hub_loss_wedge": round(lw(mlc), 4),
            },
            "c3a_face_on_lmp_basis_pct": round(100.0 * (m_p / a_lmp - 1.0), 4),
            "c3a_face_on_mec_basis_pct": round(100.0 * (m_p / a_mec - 1.0), 4),
            "concentration_on_mec_basis": {
                "annual_lw_energy_gap": round(lw(mec - pmod), 4),
                "obj_15h_contribution": round(
                    float(np.dot((mec - pmod)[obj], load[obj]) / wsum), 4
                ),
                "yr1_88h_contribution": round(
                    float(np.dot((mec - pmod)[yr1], load[yr1]) / wsum), 4
                ),
            },
        }

        report["years"][str(year)] = y

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(report, f, indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
