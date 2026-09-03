#!/usr/bin/env python3
"""nyiso-183 Phase 0 — is Ravenswood's availability a MIS-BOOKING, or an OFFER?

Scores the gates of ``results/calibration/PREREG-nyiso183-ravenswood-availability.md``
for **zero solves**, entirely from committed bytes:

* ``data/raw/campd-unit-outages-perunitmerit-NYISO.csv`` — the keeper's own
  availability basis (sha256 ``45bc4f7c…`` in the keeper's ``resolved_inputs``);
* ``data/raw/campd-unit-outages-layup-perunitmerit-NYISO.csv`` — the companion
  the merit-order guard writes, i.e. exactly the windows stage 3 removed;
* ``data/raw/campd-unit-outages-perunit-NYISO.csv`` — the UNGUARDED basis;
* ``data/raw/campd-unit-level/NY_<year>.parquet`` — the meter;
* the guard's OWN panel, rebuilt through
  :func:`scripts.lib.outage_detect.build_merit_order_panel` at its committed
  constants — imported rather than re-implemented, so the ``srmc`` / ``rcc``
  this probe reads are the ones the deriver classified on.

The gates, verbatim from the pre-registration:

``G0``  instrument — reproduce nyiso-177 §2.1/§2.3's published mean
        availabilities for ``(2500, ST_GAS)`` to within ±0.005 on BOTH paths.
        Failing G0 stops the session (PREREG §6 S0).
``G1``  discrimination — capacity-weighted ``oom_run`` over Ravenswood's
        ``ST_GAS`` units ≥ ``MERIT_OOM_FRAC`` in ≥ 2 of 3 years.
``G2``  materiality — keeper-path minus unguarded-path mean availability for
        ``(2500, ST_GAS)`` ≥ 0.40 in 2023.
``G3``  selectivity — the proposed repair's restore share, ``sel_fleet`` ≤ 0.75
        AND at least one ``ST_GAS`` unit keeps a guard-removed window.
``G4a`` / ``G4b`` — hypothesis B's measured legs (peer SRMC, in-merit share).
        ``G4c`` needs the model's own offer and is scored elsewhere.

Nothing here reads a price residual, a metrics file or any solve output.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402
from scripts.lib.outage_detect import (  # noqa: E402
    FULL_STOP_OVERRIDE_CF,
    FULL_STOP_OVERRIDE_DAYS,
    MERIT_OOM_FRAC,
    MERIT_RCC_PCTL,
    REAL_RUN_CF,
    build_merit_order_panel,
)

RAW = _REPO / "data" / "raw"
YEARS = (2023, 2024, 2025)
ISO = "NYISO"
RAVENSWOOD = 2500
CLASS = "ST_GAS"

# nyiso-177 §2.1 / §2.3, the published values G0 must reproduce.
G0_KEEPER_EXPECT = {2023: 0.772, 2024: 0.465, 2025: 0.297}
G0_UNGUARDED_EXPECT = {2023: 0.129, 2024: 0.097, 2025: 0.111}
G0_TOL = 0.005

# PREREG §4 bars, fixed before any measurement.
G1_BAR = MERIT_OOM_FRAC  # 0.90 — the guard's own frac, no new number
G1_MIN_YEARS = 2
G2_BAR = 0.40
G3_SEL_FLEET_BAR = 0.75

# The downstate steam peer set (PREREG §4 G4a).
PEERS = {
    2490: "Arthur Kill",
    8906: "Astoria Gen",
    2516: "Northport",
    2511: "E F Barrett",
    2625: "Bowline Point",
}


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------
def _hours(year: int) -> int:
    return len(pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h"))


def availability(year: int, *, guard: bool) -> dict[tuple[int, str], np.ndarray]:
    """The engine's OWN availability builder on the keeper's kwargs.

    ``guard`` selects the ``-perunitmerit-`` (keeper) or ``-perunit-``
    (unguarded) extract through :func:`unit_outage_csv_for_iso`, exactly as
    ``campd_attribution_selectors`` does for the solve.
    """
    return unit_outage_derate_factors(
        year,
        hours=_hours(year),
        iso=ISO,
        per_unit_crosswalk=True,
        merit_order_guard=guard,
    )


def load_meter(year: int) -> pd.DataFrame:
    """NYISO CAMPD unit-level meter for ``year`` on the full-year clock."""
    frames = []
    for state in campd.states_for_iso(ISO):
        path = RAW / "campd-unit-level" / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df.dropna(subset=["facilityId"])
        df["facilityId"] = df["facilityId"].astype(int)
        df["date"] = pd.to_datetime(df["date"])
        df["hour"] = pd.to_numeric(df["hour"], errors="coerce").astype("Int64")
        df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
        frames.append(df.dropna(subset=["hour"]))
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    start = pd.Timestamp(f"{year}-01-01")
    out["h"] = (
        (out["date"] - start).dt.days * 24 + out["hour"].astype(int)
    ).astype(int)
    return out


def unit_series(meter: pd.DataFrame, year: int) -> dict[tuple[int, str], np.ndarray]:
    """``{(facility, unit): hourly grossLoad}`` on the full-year clock."""
    n = _hours(year)
    out: dict[tuple[int, str], np.ndarray] = {}
    for (fac, uid), g in meter.groupby(["facilityId", "unitId"], sort=False):
        arr = np.zeros(n, dtype=float)
        h = g["h"].to_numpy()
        ok = (h >= 0) & (h < n)
        np.add.at(arr, h[ok], g["grossLoad"].to_numpy()[ok])
        out[(int(fac), str(uid))] = arr
    return out


def panel_for(year: int):
    """The guard's own :class:`MeritOrderPanel`, at its committed constants."""
    return build_merit_order_panel(
        ISO,
        year,
        _hours(year),
        campd.merit_panel_states_for_iso(ISO),
        MERIT_RCC_PCTL,
        member_facilities=None,
    )


def read_windows(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["facility_id"] = df["facility_id"].astype(int)
    df["unit_id"] = df["unit_id"].astype(str)
    df["outage_start"] = pd.to_datetime(df["outage_start"])
    df["outage_end"] = pd.to_datetime(df["outage_end"])
    return df


def window_hours_in_year(row, year: int) -> tuple[int, int]:
    """Half-open ``[lo, hi)`` hour index of a window clipped to ``year``."""
    start = pd.Timestamp(f"{year}-01-01")
    end = pd.Timestamp(f"{year}-12-31 23:00")
    s = max(row.outage_start, start)
    # ``outage_end`` is the last DAY of the window; the deriver formatted it
    # from ``clock[e - 1]``, so the exclusive bound is that day + 24 h.
    e = min(row.outage_end + pd.Timedelta(hours=24), end + pd.Timedelta(hours=1))
    if e <= s:
        return 0, 0
    return int((s - start).total_seconds() // 3600), int(
        (e - start).total_seconds() // 3600
    )


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------
def run() -> dict:
    out: dict = {
        "session": "nyiso-183",
        "prereg": "results/calibration/PREREG-nyiso183-ravenswood-availability.md",
        "keeper": "2026-09-02-nyiso-177-vintage-matched",
        "constants": {
            "MERIT_OOM_FRAC": MERIT_OOM_FRAC,
            "MERIT_RCC_PCTL": MERIT_RCC_PCTL,
            "REAL_RUN_CF": REAL_RUN_CF,
            "FULL_STOP_OVERRIDE_CF": FULL_STOP_OVERRIDE_CF,
            "FULL_STOP_OVERRIDE_DAYS": FULL_STOP_OVERRIDE_DAYS,
        },
        "bars": {
            "G0_tol": G0_TOL,
            "G1_bar": G1_BAR,
            "G1_min_years": G1_MIN_YEARS,
            "G2_bar": G2_BAR,
            "G3_sel_fleet_bar": G3_SEL_FLEET_BAR,
        },
        "years": {},
    }

    kept = read_windows(RAW / f"campd-unit-outages-perunitmerit-{ISO}.csv")
    layup = read_windows(RAW / f"campd-unit-outages-layup-perunitmerit-{ISO}.csv")

    g0_rows, g1_rows, g2_rows = [], [], []
    per_unit: dict[tuple[int, str], dict] = defaultdict(dict)

    for year in YEARS:
        n = _hours(year)
        av_k = availability(year, guard=True)
        av_u = availability(year, guard=False)

        def mean_av(av, key):
            arr = av.get(key)
            return float(np.mean(arr)) if arr is not None else 1.0

        mk = mean_av(av_k, (RAVENSWOOD, CLASS))
        mu = mean_av(av_u, (RAVENSWOOD, CLASS))
        g0_rows.append(
            {
                "year": year,
                "keeper": round(mk, 4),
                "keeper_expect": G0_KEEPER_EXPECT[year],
                "keeper_ok": abs(mk - G0_KEEPER_EXPECT[year]) <= G0_TOL,
                "unguarded": round(mu, 4),
                "unguarded_expect": G0_UNGUARDED_EXPECT[year],
                "unguarded_ok": abs(mu - G0_UNGUARDED_EXPECT[year]) <= G0_TOL,
            }
        )
        g2_rows.append(
            {"year": year, "share_reclass": round(mk - mu, 4), "keeper": round(mk, 4),
             "unguarded": round(mu, 4)}
        )

        meter = load_meter(year)
        series = unit_series(meter, year) if len(meter) else {}
        panel = panel_for(year)

        yr: dict = {
            "n_hours": n,
            "panel_priced_units": None if panel is None else len(panel.srmc),
            "units": {},
        }

        # every NYISO unit the guard touched this year, plus every ST_GAS unit
        # carrying a kept window — the population the gates are measured over.
        pop: set[tuple[int, str]] = set()
        for df in (kept, layup):
            sel = df[
                (df["outage_start"] <= pd.Timestamp(f"{year}-12-31 23:00"))
                & (df["outage_end"] >= pd.Timestamp(f"{year}-01-01"))
            ]
            pop |= {
                (int(r.facility_id), str(r.unit_id)) for r in sel.itertuples(index=False)
            }

        for key in sorted(pop):
            fac, uid = key
            gross = series.get(key)
            rec: dict = {
                "facility_id": fac,
                "unit_id": uid,
                "plant_group": None,
                "cap_mw": None,
            }
            for df in (layup, kept):
                sel = df[(df["facility_id"] == fac) & (df["unit_id"] == uid)]
                if len(sel):
                    rec["plant_group"] = str(sel.iloc[0]["plant_group"])
                    rec["cap_mw"] = float(sel.iloc[0]["unit_capacity_mw"])
                    break

            # ---- window-hour ledger, clipped to the year ----
            def hours_and_oom(df: pd.DataFrame) -> tuple[int, float | None, list]:
                sel = df[(df["facility_id"] == fac) & (df["unit_id"] == uid)]
                tot, wsum, spans = 0, [], []
                for r in sel.itertuples(index=False):
                    lo, hi = window_hours_in_year(r, year)
                    if hi <= lo:
                        continue
                    tot += hi - lo
                    share = (
                        panel.out_of_merit_share(key, lo, hi)
                        if panel is not None
                        else None
                    )
                    if share is not None:
                        wsum.append((hi - lo, share))
                    spans.append((lo, hi, share))
                oom = (
                    float(sum(w * s for w, s in wsum) / sum(w for w, _ in wsum))
                    if wsum
                    else None
                )
                return tot, oom, spans

            lay_h, oom_down, lay_spans = hours_and_oom(layup)
            kept_h, oom_kept, kept_spans = hours_and_oom(kept)
            rec["layup_hours"] = lay_h
            rec["oom_down"] = None if oom_down is None else round(oom_down, 4)
            rec["kept_hours"] = kept_h
            rec["oom_kept"] = None if oom_kept is None else round(oom_kept, 4)

            # ---- the G1 statistic: the SAME test on the unit's RUNNING hours ----
            oom_run, run_h, cf = None, 0, None
            if gross is not None and panel is not None:
                peak = float(np.max(gross)) if gross.size else 0.0
                if peak > 0:
                    running = gross / peak >= REAL_RUN_CF
                    run_h = int(running.sum())
                    srmc = panel.srmc.get(key)
                    if srmc is not None and run_h:
                        ok = running & np.isfinite(srmc) & np.isfinite(panel.rcc)
                        if ok.any():
                            oom_run = float(
                                (srmc[ok] > panel.rcc[ok]).sum()
                            ) / float(ok.sum())
                    cf = float(gross.sum() / (peak * len(gross)))
            rec["run_hours"] = run_h
            rec["oom_run"] = None if oom_run is None else round(oom_run, 4)
            rec["meter_cf_vs_peak"] = None if cf is None else round(cf, 4)
            rec["identified_by_panel"] = bool(
                panel is not None and key in panel.srmc
            )
            rec["separation"] = (
                None
                if (oom_down is None or oom_run is None)
                else round(oom_down - oom_run, 4)
            )

            # ---- R1's own premise: would stage 2b have overridden these? ----
            fs_h = 0
            if gross is not None:
                peak = float(np.max(gross)) if gross.size else 0.0
                for lo, hi, _ in lay_spans:
                    if peak <= 0:
                        continue
                    span_cf = float(np.mean(gross[lo:hi]) / peak)
                    if (hi - lo) / 24.0 >= FULL_STOP_OVERRIDE_DAYS and (
                        span_cf < FULL_STOP_OVERRIDE_CF
                    ):
                        fs_h += hi - lo
            rec["layup_hours_fullstop_shaped"] = fs_h

            # ---- G4a/G4b: measured merit position ----
            if panel is not None and key in panel.srmc:
                s = panel.srmc[key]
                good = np.isfinite(s) & np.isfinite(panel.rcc)
                if good.any():
                    rec["srmc_mean"] = round(float(np.nanmean(s[good])), 3)
                    rec["rcc_mean"] = round(float(np.nanmean(panel.rcc[good])), 3)
                    rec["in_merit_share_year"] = round(
                        float((s[good] <= panel.rcc[good]).sum()) / float(good.sum()), 4
                    )
            yr["units"][f"{fac}:{uid}"] = rec
            per_unit[key][year] = rec

        out["years"][str(year)] = yr

        # ---------- G1 (capacity-weighted over Ravenswood ST_GAS units) ----------
        rav = [
            r
            for r in yr["units"].values()
            if r["facility_id"] == RAVENSWOOD
            and r["plant_group"] == CLASS
            and r["oom_run"] is not None
        ]
        wsum = sum((r["cap_mw"] or 0.0) for r in rav)
        g1_rows.append(
            {
                "year": year,
                "n_units": len(rav),
                "cap_mw": round(wsum, 1),
                "oom_run_capwt": (
                    round(
                        sum((r["cap_mw"] or 0.0) * r["oom_run"] for r in rav) / wsum, 4
                    )
                    if wsum
                    else None
                ),
                "oom_down_capwt": (
                    round(
                        sum(
                            (r["cap_mw"] or 0.0) * (r["oom_down"] or 0.0)
                            for r in rav
                            if r["oom_down"] is not None
                        )
                        / max(
                            sum(
                                (r["cap_mw"] or 0.0)
                                for r in rav
                                if r["oom_down"] is not None
                            ),
                            1e-9,
                        ),
                        4,
                    )
                    if any(r["oom_down"] is not None for r in rav)
                    else None
                ),
                "run_hours": sum(r["run_hours"] for r in rav),
            }
        )

    out["G0"] = {
        "rows": g0_rows,
        "passed": all(r["keeper_ok"] and r["unguarded_ok"] for r in g0_rows),
    }
    fired_years = [
        r["year"]
        for r in g1_rows
        if r["oom_run_capwt"] is not None and r["oom_run_capwt"] >= G1_BAR
    ]
    out["G1"] = {
        "rows": g1_rows,
        "years_at_or_above_bar": fired_years,
        "fired": len(fired_years) >= G1_MIN_YEARS,
    }
    out["G2"] = {
        "rows": g2_rows,
        "fired": any(
            r["year"] == 2023 and r["share_reclass"] >= G2_BAR for r in g2_rows
        ),
    }

    # ---------------- G3: what R2 would restore, with no solve ----------------
    # R2: the guard is inert for a unit whose OWN running hours are out of merit
    # at >= MERIT_OOM_FRAC.  Fail-safe direction: the window is KEPT.
    r2_restore_stgas = r2_all_stgas = 0
    r2_restore_fleet = r2_all_fleet = 0
    units_keeping_layup: set[str] = set()
    for year in YEARS:
        for name, rec in out["years"][str(year)]["units"].items():
            h = rec["layup_hours"]
            if not h:
                continue
            r2_all_fleet += h
            is_st = rec["plant_group"] == CLASS
            if is_st:
                r2_all_stgas += h
            inert = rec["oom_run"] is not None and rec["oom_run"] >= MERIT_OOM_FRAC
            if inert:
                r2_restore_fleet += h
                if is_st:
                    r2_restore_stgas += h
            elif is_st:
                units_keeping_layup.add(name.split(":")[0])
    out["G3_R2"] = {
        "layup_hours_stgas": r2_all_stgas,
        "restored_hours_stgas": r2_restore_stgas,
        "sel_stgas": round(r2_restore_stgas / r2_all_stgas, 4) if r2_all_stgas else None,
        "layup_hours_fleet": r2_all_fleet,
        "restored_hours_fleet": r2_restore_fleet,
        "sel_fleet": round(r2_restore_fleet / r2_all_fleet, 4) if r2_all_fleet else None,
        "stgas_plants_keeping_a_layup_window": sorted(units_keeping_layup),
    }
    sel_f = out["G3_R2"]["sel_fleet"]
    out["G3_R2"]["passes_selectivity"] = bool(
        sel_f is not None
        and sel_f <= G3_SEL_FLEET_BAR
        and len(units_keeping_layup) >= 1
    )

    # R1's premise: share of guard-removed ST_GAS window-hours that stage 2b
    # would itself have overridden as mechanical.
    fs_h = st_h = 0
    for year in YEARS:
        for rec in out["years"][str(year)]["units"].values():
            if rec["plant_group"] != CLASS:
                continue
            st_h += rec["layup_hours"]
            fs_h += rec["layup_hours_fullstop_shaped"]
    out["G3_R1_premise"] = {
        "layup_hours_stgas": st_h,
        "fullstop_shaped_hours": fs_h,
        "share": round(fs_h / st_h, 4) if st_h else None,
        "admissible_premise": bool(st_h and fs_h / st_h >= 0.50),
    }

    # ---------------- G4a / G4b: measured merit position ----------------
    g4 = []
    for year in YEARS:
        units = out["years"][str(year)]["units"]

        def capwt(fac: int, field: str) -> float | None:
            rows = [
                r
                for r in units.values()
                if r["facility_id"] == fac
                and r["plant_group"] == CLASS
                and r.get(field) is not None
            ]
            w = sum((r["cap_mw"] or 0.0) for r in rows)
            return (
                round(sum((r["cap_mw"] or 0.0) * r[field] for r in rows) / w, 4)
                if w
                else None
            )

        row = {
            "year": year,
            "ravenswood_srmc": capwt(RAVENSWOOD, "srmc_mean"),
            "ravenswood_in_merit_share": capwt(RAVENSWOOD, "in_merit_share_year"),
        }
        peer_srmc = [
            v for f in PEERS if (v := capwt(f, "srmc_mean")) is not None
        ]
        row["peer_srmc_median"] = (
            round(float(np.median(peer_srmc)), 3) if peer_srmc else None
        )
        row["peers"] = {PEERS[f]: capwt(f, "srmc_mean") for f in PEERS}
        row["peers_in_merit_share"] = {
            PEERS[f]: capwt(f, "in_merit_share_year") for f in PEERS
        }
        g4.append(row)
    out["G4ab"] = {"rows": g4, "note": "G4c needs the model's own offer (unit_hourly)"}

    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(_REPO / "results" / "calibration" / "_nyiso183_ravenswood_availability.json"),
    )
    args = ap.parse_args()
    res = run()
    Path(args.out).write_text(json.dumps(res, indent=2, default=str))

    print("\n=== G0 instrument (bar +/- %.3f) ===" % G0_TOL)
    print(pd.DataFrame(res["G0"]["rows"]).to_string(index=False))
    print("G0 PASSED:", res["G0"]["passed"])
    if not res["G0"]["passed"]:
        print("\nPREREG S0 FIRES — instrument failure, no gate is scored.")
        return
    print("\n=== G1 discrimination at Ravenswood (bar oom_run >= %.2f in >=%d yrs) ==="
          % (G1_BAR, G1_MIN_YEARS))
    print(pd.DataFrame(res["G1"]["rows"]).to_string(index=False))
    print("G1 FIRED:", res["G1"]["fired"], res["G1"]["years_at_or_above_bar"])
    print("\n=== G2 materiality (bar >= %.2f in 2023) ===" % G2_BAR)
    print(pd.DataFrame(res["G2"]["rows"]).to_string(index=False))
    print("G2 FIRED:", res["G2"]["fired"])
    print("\n=== G3 selectivity of R2 (bar sel_fleet <= %.2f) ===" % G3_SEL_FLEET_BAR)
    print(json.dumps(res["G3_R2"], indent=1))
    print("\n=== G3 R1 premise (bar share >= 0.50) ===")
    print(json.dumps(res["G3_R1_premise"], indent=1))
    print("\n=== G4a/G4b measured merit position ===")
    print(pd.DataFrame(res["G4ab"]["rows"]).to_string(index=False))
    print("\nwritten:", args.out)


if __name__ == "__main__":
    main()
