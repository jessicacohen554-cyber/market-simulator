"""nyiso-242 item 1 — CAN a cold-hour availability derate be IDENTIFIED for NYISO? (owner-chartered, zero LP)

ZERO LP (rule 32 ``[R-SHARD]`` (a)). This is the feasibility measurement that
decides whether the chartered identification intake is worth issuing, run
BEFORE the charter rather than after it.

**THE IDENTIFICATION DESIGN, stated before any number.** In an hour when the
real market cleared at $300–750/MWh, **every** available thermal unit in the
fleet was economic — no plausible offer keeps a gas or oil unit out of merit at
those prices. So a unit metering **zero** in CAMPD during such an hour was
**unavailable**, not un-economic. That is what makes this an identification and
not a fit: the magnitude comes from the ISO's own realized price and the EPA's
own meter, never from the model's residual (rules 1 ``[R-STRUCT]`` / 13
``[R-MEASURED]``), and the same construction regenerates for any year.

**WHAT WOULD DEFEAT IT, declared up front.** The keeper already arms
``campd_outage_windows``, so CAMPD-observed outages are ALREADY in the model's
availability. The mechanism only exists if the existing overlay **misses**
capacity that CAMPD says was not running in those hours. So the measured
quantity is the GAP:

    model-believed available MW  −  CAMPD-observed running-or-startable MW

If that gap is small, the overlay already captures the event, no new mechanism
is identified, and the charter should NOT be issued — which is a legitimate and
useful outcome. If it is large and concentrated in the extreme-price hours, the
derate is identified and its magnitude is measured rather than tuned.

**THE CONTROL that separates "unavailable" from "not needed".** The same gap is
measured in ordinary hours. A derate that is equally large when the market is
cheap is not a cold-snap availability signal — it is the model's ordinary
unused headroom, and it identifies nothing.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso242_coldhour_identification.py [--year 2022]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
CAMPD = REPO / "data" / "raw" / "campd-unit-level"
HUB = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"
#: The C3c gate threshold; also the price above which "every unit is economic"
#: is not a contestable claim.
EXTREME = 300.0
THERMAL_TOKENS = ("CC", "CT", "ST", "COAL", "OIL", "OTHER_FOSSIL")


def _is_thermal(k: str) -> bool:
    return any(t in k.upper() for t in THERMAL_TOKENS)


def model_side(year: int):
    """Model-believed available thermal MW per hour, and the fleet's plant set."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    st = run_year(year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
    fa = st["fleet_arrays"]
    klass = np.array([str(k) for k in fa.plant_group])
    pmax = np.asarray(fa.pmax, dtype=float)
    av = np.asarray(fa.availability, dtype=float)
    if av.ndim == 1:
        av = np.repeat(av[:, None], 8760, axis=1)
    codes = np.asarray(fa.plant_code)
    tm = np.array([_is_thermal(k) for k in klass])
    avail_h = (pmax[tm][:, None] * av[tm, :]).sum(axis=0)
    # Per-plant believed-available, for the plant-level attribution below.
    per_plant: dict[int, np.ndarray] = {}
    for c in {int(x) for x in codes[tm]}:
        m = tm & (codes == c)
        per_plant[c] = (pmax[m][:, None] * av[m, :]).sum(axis=0)
    return avail_h, per_plant, float(pmax[tm].sum())


def campd_side(year: int, plants: set[int]) -> tuple[np.ndarray, dict[int, np.ndarray]]:
    """CAMPD observed gross load per hour, total and per plant, for ``plants``."""
    p = CAMPD / f"NY_{year}.parquet"
    df = pd.read_parquet(
        p, columns=["facilityId", "date", "hour", "opTime", "grossLoad"]
    )
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df[df["facilityId"].isin(plants)]
    ts = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"], unit="h")
    df = df.assign(h=((ts - pd.Timestamp(f"{year}-01-01")) // pd.Timedelta("1h")).astype(int))
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    n = 8760
    tot = np.zeros(n)
    g = df.groupby("h")["grossLoad"].sum()
    idx = g.index.to_numpy()
    ok = (idx >= 0) & (idx < n)
    tot[idx[ok]] = g.to_numpy()[ok]
    per_plant: dict[int, np.ndarray] = {}
    for c, sub in df.groupby("facilityId"):
        a = np.zeros(n)
        s = sub.groupby("h")["grossLoad"].sum()
        i = s.index.to_numpy()
        m = (i >= 0) & (i < n)
        a[i[m]] = s.to_numpy()[m]
        per_plant[int(c)] = a
    return tot, per_plant


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument(
        "--out",
        default=str(REPO / "results" / "calibration" / "_nyiso242_coldhour_identification.json"),
    )
    args = ap.parse_args()
    year = args.year

    avail_h, per_plant_avail, nameplate = model_side(year)
    plants = set(per_plant_avail)
    campd_h, per_plant_campd = campd_side(year, plants)

    hub = pd.read_parquet(HUB)
    hub = hub[hub["year"] == year].sort_values("hour")["rt"].to_numpy()
    n = min(len(avail_h), len(campd_h), len(hub))
    avail_h, campd_h, hub = avail_h[:n], campd_h[:n], hub[:n]

    month = pd.date_range(f"{year}-01-01", periods=n, freq="h").month.to_numpy()
    extreme = hub > EXTREME
    winter_ex = extreme & np.isin(month, (1, 2, 12))
    # CONTROL: ordinary hours, defined by price rather than by season so the
    # comparison is not circular.
    ordinary = hub < np.percentile(hub, 50)

    # CAMPD covers only its own reporting fleet, so the LEVEL of the two series
    # is not commensurable; what is commensurable is each hour's ratio against
    # that same fleet's own annual CAMPD maximum -- a within-series statistic.
    campd_ceiling = float(np.percentile(campd_h, 99.9))

    out: dict = {
        "year": year,
        "threshold": EXTREME,
        "campd_plants_matched": len(set(per_plant_campd) & plants),
        "model_thermal_plants": len(plants),
        "model_thermal_nameplate_mw": round(nameplate, 1),
        "campd_p999_mw": round(campd_ceiling, 1),
    }
    for label, sel in (
        ("extreme_price", extreme),
        ("extreme_winter", winter_ex),
        ("ordinary_price", ordinary),
        ("all_hours", np.ones(n, dtype=bool)),
    ):
        if not sel.any():
            continue
        out[label] = {
            "hours": int(sel.sum()),
            "model_believed_available_mw_median": round(float(np.median(avail_h[sel])), 1),
            "campd_observed_mw_median": round(float(np.median(campd_h[sel])), 1),
            # The identification quantity: how much of its own demonstrated
            # ceiling was the CAMPD fleet actually delivering?
            "campd_pct_of_own_p999": round(
                float(100.0 * np.median(campd_h[sel]) / campd_ceiling), 1
            ),
            "actual_price_median": round(float(np.median(hub[sel])), 2),
        }

    # ------------------------------------------------------------------
    # THE DISCRIMINATOR — and it is what decides the whole design.
    #
    # A gap measured only in extreme-price hours has THREE candidate causes and
    # the raw number separates none of them: (i) genuine unavailability, which
    # is the mechanism; (ii) day-ahead COMMITMENT lag, since NYISO's 2022 DA
    # tail is 10 hours against an RT tail of 101 — a slow-start unit not
    # committed day-ahead cannot be online for an unanticipated RT spike; and
    # (iii) a fast-start unit correctly HELD as 10-minute reserve, which meters
    # zero precisely because it is available.
    #
    # Conditioning on the DA price separates (i) from (ii): in hours the DA
    # market ANTICIPATED, commitment lag cannot be the excuse, so a genuine
    # cold-snap unavailability signal must still be there. And a genuine
    # signal must DEEPEN with price. A ratio that is FLAT across every price
    # condition is neither — it is the fleet's ordinary coincidence factor
    # against its own annual peak, and it identifies nothing.
    # ------------------------------------------------------------------
    da = pd.read_parquet(HUB)
    da = da[da["year"] == year].sort_values("hour")["da"].to_numpy()[:n]
    disc: dict = {}
    for lbl, sel in (
        ("DA_gt_300", da > 300),
        ("DA_gt_200", da > 200),
        ("DA_gt_150", da > 150),
        ("DA_gt_100", da > 100),
        ("RT_gt_300_DA_anticipated", (hub > EXTREME) & (da > EXTREME)),
        ("RT_gt_300_DA_surprise", (hub > EXTREME) & (da <= EXTREME)),
        ("ordinary_price", ordinary),
    ):
        if sel.sum() < 3:
            disc[lbl] = {"hours": int(sel.sum()), "note": "too few to read"}
            continue
        disc[lbl] = {
            "hours": int(sel.sum()),
            "rt_median": round(float(np.median(hub[sel])), 1),
            "da_median": round(float(np.median(da[sel])), 1),
            "campd_pct_of_own_p999": round(
                float(100.0 * np.median(campd_h[sel]) / campd_ceiling), 1
            ),
        }
    out["discriminator"] = disc

    # PLANT-LEVEL: in the extreme-price hours, which plants the model believes
    # available metered ZERO? Those are the identification's carriers -- read
    # ONLY together with the discriminator above.
    if winter_ex.any():
        rows = []
        for c, av in per_plant_avail.items():
            cm = per_plant_campd.get(c)
            if cm is None:
                continue
            bel = float(np.median(av[:n][winter_ex]))
            obs = float(np.median(cm[:n][winter_ex]))
            if bel <= 1.0:
                continue
            rows.append(
                {
                    "plant_code": int(c),
                    "model_believed_mw": round(bel, 1),
                    "campd_observed_mw": round(obs, 1),
                    "gap_mw": round(bel - obs, 1),
                    "zero_metered": bool(obs < 1.0),
                }
            )
        rows.sort(key=lambda r: -r["gap_mw"])
        zero = [r for r in rows if r["zero_metered"]]
        out["winter_extreme_plant_attribution"] = {
            "plants_compared": len(rows),
            "plants_metering_zero_while_believed_available": len(zero),
            "mw_believed_available_but_metering_zero": round(
                sum(r["model_believed_mw"] for r in zero), 1
            ),
            "total_gap_mw": round(sum(r["gap_mw"] for r in rows), 1),
            "top_10_by_gap": rows[:10],
        }

    print(json.dumps({k: v for k, v in out.items() if k != "winter_extreme_plant_attribution"}, indent=2))
    w = out.get("winter_extreme_plant_attribution")
    if w:
        print("\nwinter extreme-price hours, plant attribution:")
        for k, v in w.items():
            if k != "top_10_by_gap":
                print(f"  {k}: {v}")
        print("  top 10 by gap:")
        for r in w["top_10_by_gap"]:
            print(
                f"    {r['plant_code']:>6}  believed={r['model_believed_mw']:8.1f}  "
                f"campd={r['campd_observed_mw']:8.1f}  gap={r['gap_mw']:8.1f}"
                f"{'   ZERO' if r['zero_metered'] else ''}"
            )
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
