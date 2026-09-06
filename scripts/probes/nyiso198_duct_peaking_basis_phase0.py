"""nyiso-198 PHASE 0 part 2 (NO LP) — the ``cc_duct_peaking_pct`` capacity
basis: how much of the peak (duct-burner) band the NYISO combined-cycle fleet
carries is EIA-860 rows the filing itself flags as having NO duct burner.

Part 1 (``nyiso198_cricket_partload_phase0.py``) decomposed Cricket Valley
57185's bucket (b-) by which LP bound binds and found 88.9 % of the 2024
deficit in hours where the model dispatches ~98 % of its in-the-money capacity
and the meter runs above it -- i.e. the plant's unused headroom is priced out
of the market.  At 57185 that headroom is the **peak band**: 245.64 MW of
1,086.9 MW (22.6 %) offered at 2.25x the plant heat rate (15.78 MMBtu/MWh,
$53.73/MWh against a $35.50 mean LMP).

That 22.6 % is ``fleet.campd_bins.cc_duct_peaking_pct``:

    duct-fired  <=>  ANY of the plant's CC generators has "Duct Burners" == Y
    peaking %    =   100 * max(0, SUM nameplate - SUM net-summer) / SUM nameplate

summed over **every** CC generator of the plant.  Two measured facts the filing
itself states contradict that sum, and this probe quantifies both:

* **The CT rows can carry no duct burner.**  A duct burner fires into the HRSG
  and raises the STEAM turbine's output; EIA-860 reports the attribute at that
  grain, and in the whole Generator_Y operable population **every** CT row
  reads ``Duct Burners = X`` (not applicable) while Y/N appear only on CA and
  CS rows.  So the CT rows' nameplate-vs-summer gap is site/ambient derate by
  construction, and the plant-level sum books it as duct capability.
* **The gap is a share of NAMEPLATE applied to a capacity base
  ``cc_capacity_reconcile`` has already cut to the CAMPD demonstrated peak.**
  The duct increment, if real, is the top of the nameplate range -- exactly the
  part the reconcile removed -- so the same percentage applied to the reduced
  base re-books demonstrated, routinely-achieved capacity as peaking.

Measurements, all from committed artifacts:

  **F-0**  per-plant census, every ISO: current pct, the Y/CS-row-scoped pct,
           the MW that changes band at the keeper's own LP capacity.
  **F-1**  the physical discriminator: the CAMPD observed maximum against the
           filing's nameplate / winter / summer capability, and the month it
           occurs.  A plant whose observed peak tracks WINTER capability and
           never approaches nameplate has an ambient gap, not a duct gap.
  **F-2**  the pre-solve dispatch delta at the keeper's own hourly LMP and
           availability: how much of the plant's (b-) deficit sits in capacity
           that is out of the money at the peak band's offer and in the money
           at the econ band's -- the arithmetic the mechanism claims to reach.
  **A-1**  the (b-) deficit re-attributed three ways -- availability short
           (meter above the LP's envelope), peak-band short, econ-band short.

**CORRECTION (nyiso-198 Addendum A, same session).**  Two numbers this probe
writes are WRONG and are superseded by
``_nyiso198_rebuild_checks_2024.json``, which measures the same quantities on
the actual rebuilt fleet:

* ``mw_rebanded_peak_to_econ`` is computed as ``lp_pmax * pct_row_scoped``, but
  the fleet builder sets ``peak_cap = grid_cap * pct_peak / (100 - pct_mr)``.
  At any plant with a must-run share the two differ.  The correct per-plant
  move is ``peak_off * pct_row / pct_cur``, which reproduces the rebuild to
  0.000 MW.  The fleet total is **726.53 MW across 17 plants**, not the 647.9
  across 11 this probe reports.
* the "override plant" split inferred here from
  ``|pct_current - lp_peak_band_share_pct| < 0.15`` misfiles four CHP plants
  (50006, 50458, 52168, 54131) for the same reason.  The override set is
  enumerable directly and exactly: ``_chp_layup_cohort`` u ``_chp_duty_curve``
  u ``_reserve_duty_cohort``.

Everything else here — the F-0 population census, the per-plant EIA-860 gap
decomposition, the (b-) three-way attribution and the meter-vs-capability
comparison — is unaffected.

Nothing here is gated on any residual.  Writes
``results/calibration/_nyiso198_duct_peaking_basis_phase0.json``.

Usage::

    python scripts/probes/nyiso198_duct_peaking_basis_phase0.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))
from market_sim.data.fleet.campd_bins import active_eia860_dir  # noqa: E402
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

KEEPER_ID = "2026-09-06-nyiso-196-extract-basis"
BUNDLE = ROOT / "results/calibration/nyiso196_extract_basis"
CC_GROUPS = ("CC_REGULAR", "CC_CHP")
T = 8760
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
ON_FRAC = 0.01


def _r(x, n=1):
    return round(float(x), n)


def _dec(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def _series(entry: dict, kb: str, ka: str, npl: float) -> np.ndarray | None:
    raw_b64 = entry.get(kb)
    if not raw_b64:
        return None
    raw = _dec(raw_b64)[:T]
    if raw.size < T:
        raw = np.pad(raw, (0, T - raw.size))
    ann = entry.get(ka)
    if ann not in (None, "", "None") and raw.sum() > 0:
        return raw * (float(ann) * 1e6 / raw.sum())
    return raw * npl / 100.0 if npl > 0 else None


def _month_of_hour() -> np.ndarray:
    m = np.zeros(T, dtype=int)
    for i in range(12):
        m[MONTH_STARTS[i] : MONTH_STARTS[i + 1]] = i + 1
    return m


def eia860_cc() -> pd.DataFrame:
    """Every EIA-860 operable combined-cycle generator row, typed."""
    df = pd.read_parquet(active_eia860_dir() / "eia860_generator_operable.parquet")
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    cc["pc"] = cc["Plant Code"].astype(float).astype(int)
    for c in (
        "Nameplate Capacity (MW)",
        "Summer Capacity (MW)",
        "Winter Capacity (MW)",
    ):
        cc[c] = pd.to_numeric(cc[c], errors="coerce")
    cc["duct"] = cc["Duct Burners"].astype(str).str.strip()
    return cc


def duct_pct_variants(cc: pd.DataFrame) -> dict[int, dict]:
    """Current plant-level pct against the row-scoped alternative, per plant."""
    out: dict[int, dict] = {}
    for code, g in cc.groupby("pc"):
        np_all = float(g["Nameplate Capacity (MW)"].sum())
        if np_all <= 0:
            continue
        ns_all = float(g["Summer Capacity (MW)"].sum())
        wi_all = float(g["Winter Capacity (MW)"].sum())
        is_duct = (g["duct"] == "Y").any()
        cur = round(100.0 * max(0.0, np_all - ns_all) / np_all, 1) if is_duct else 0.0
        y = g[g["duct"] == "Y"]
        np_y = float(y["Nameplate Capacity (MW)"].sum())
        ns_y = float(y["Summer Capacity (MW)"].sum())
        rowscoped = round(100.0 * max(0.0, np_y - ns_y) / np_all, 1) if is_duct else 0.0
        ct = g[g["duct"] == "X"]
        out[int(code)] = {
            "plant_name": str(g["Plant Name"].iloc[0]),
            "state": str(g["State"].iloc[0]).strip(),
            "n_rows": int(len(g)),
            "prime_movers": sorted(set(g["Prime Mover"].astype(str))),
            "duct_flags": sorted(set(g["duct"])),
            "is_duct_fired": bool(is_duct),
            "nameplate_mw": _r(np_all, 1),
            "summer_mw": _r(ns_all, 1),
            "winter_mw": _r(wi_all, 1),
            "gap_nameplate_minus_summer_mw": _r(np_all - ns_all, 1),
            "gap_nameplate_minus_winter_mw": _r(np_all - wi_all, 1),
            "gap_on_duct_Y_rows_mw": _r(max(0.0, np_y - ns_y), 1),
            "gap_on_nonduct_X_rows_mw": _r(
                max(
                    0.0,
                    float(ct["Nameplate Capacity (MW)"].sum())
                    - float(ct["Summer Capacity (MW)"].sum()),
                ),
                1,
            ),
            "pct_current": cur,
            "pct_row_scoped": rowscoped,
            "pct_delta": round(cur - rowscoped, 1),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    a = ap.parse_args()

    cc = eia860_cc()
    variants = duct_pct_variants(cc)

    # ---- F-0 population-level statement of the construction ---------------
    pm_flag = (
        cc.groupby(["Prime Mover", "duct"]).size().rename("rows").reset_index()
    )
    f0 = {
        "eia860_dir": str(active_eia860_dir().relative_to(ROOT)),
        "cc_generator_rows": int(len(cc)),
        "rows_by_prime_mover_and_duct_flag": {
            f"{r['Prime Mover']}/{r['duct']}": int(r["rows"])
            for _, r in pm_flag.iterrows()
        },
        "CT_rows_with_duct_flag_Y": int(
            ((cc["Prime Mover"] == "CT") & (cc["duct"] == "Y")).sum()
        ),
        "CT_rows_total": int((cc["Prime Mover"] == "CT").sum()),
        "note": (
            "the Duct Burners attribute is reported only on CA/CS (steam) rows; "
            "every CT row in the operable population reads X (not applicable), "
            "so a CT row's nameplate-vs-summer gap cannot be duct capability"
        ),
    }

    out = {
        "session": "nyiso-198",
        "status": "PHASE 0 part 2 — NO LP, MEASUREMENT ONLY (rule 29 step 0)",
        "keeper": KEEPER_ID,
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "object": (
            "cc_duct_peaking_pct takes the duct-burner peaking share as the "
            "WHOLE plant's nameplate-minus-net-summer gap whenever ANY generator "
            "row is flagged Duct Burners = Y; the CT rows in that sum are flagged "
            "X (no duct burner) by the same filing, so their ambient derate is "
            "booked as duct capability and priced at the 2.25x peak band."
        ),
        "F0_construction": f0,
        "years": {},
    }

    mon = _month_of_hour()
    for yr in a.years:
        state, meta = reconstruct_bundle_fleet(BUNDLE, yr)
        fa = state["fleet_arrays"]
        mc_base = np.asarray(state["mc_base"])
        pcode = np.asarray(fa.plant_code)
        pmax = np.asarray(fa.pmax)
        avail = np.asarray(fa.availability)
        uids = list(fa.unit_ids)

        def av_row(i):
            return avail[i] if avail.ndim > 1 else np.full(T, float(avail[i]))

        def mc_row(i):
            return mc_base[i] if mc_base.ndim > 1 else np.full(T, float(mc_base[i]))

        run = decode_run_js(
            (ROOT / f"frontend/data/backcast/runs/{KEEPER_ID}.js").read_text()
        )
        bench = json.load(
            gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{yr}.json.gz")
        )["bench"]
        sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{yr}.parquet")
        lmp_by_zone = {
            z: sysp[sysp.zone == z].sort_values("hour").price.to_numpy()[:T]
            for z in sysp.zone.unique()
        }

        # LP rows grouped by plant, split peak vs non-peak by unit id suffix
        rows_by_plant: dict[int, list[int]] = {}
        for i in range(len(pcode)):
            uid = uids[i]
            if not any(uid.startswith(g + "_") for g in CC_GROUPS):
                continue
            rows_by_plant.setdefault(int(pcode[i]), []).append(i)

        plants = {}
        tot = {
            "peak_band_mw": 0.0,
            "peak_band_mw_row_scoped": 0.0,
            "mw_rebanded": 0.0,
            "bminus_gwh": 0.0,
            "avail_short_gwh": 0.0,
            "peak_short_gwh": 0.0,
            "econ_short_gwh": 0.0,
            "reachable_gwh": 0.0,
            "footprint_capacity_hours_mwh": 0.0,
        }
        for code, idx in sorted(rows_by_plant.items()):
            v = variants.get(code)
            b = bench["plants"].get(str(code))
            peak_i = [i for i in idx if uids[i].endswith("_peak")]
            nonpeak_i = [i for i in idx if not uids[i].endswith("_peak")]
            pmax_tot = float(sum(float(pmax[i]) for i in idx))
            peak_mw = float(sum(float(pmax[i]) for i in peak_i))
            pct_cur = v["pct_current"] if v else None
            pct_row = v["pct_row_scoped"] if v else None
            peak_mw_row = (
                pmax_tot * pct_row / 100.0 if pct_row is not None else None
            )
            rec = {
                "plant_name": (v or {}).get("plant_name") or (b or {}).get("name"),
                "group": (b or {}).get("group"),
                "zone": (b or {}).get("zone"),
                "lp_pmax_mw": _r(pmax_tot, 2),
                "lp_peak_band_mw": _r(peak_mw, 2),
                "lp_peak_band_share_pct": _r(
                    100.0 * peak_mw / pmax_tot if pmax_tot else 0.0, 2
                ),
                "eia860": v,
                "peak_band_mw_row_scoped": (
                    _r(peak_mw_row, 2) if peak_mw_row is not None else None
                ),
                "mw_rebanded_peak_to_econ": (
                    _r(peak_mw - peak_mw_row, 2) if peak_mw_row is not None else None
                ),
            }

            # ---- F-1 / F-2 / A-1 need the meter and the payload ------------
            if b and not b.get("nodata") and str(code) in run["years"][str(yr)]["plants"]:
                npl = float(b["npl"])
                addback = float(b.get("btm") or 0.0) * 1e6 / T
                m = _series(run["years"][str(yr)]["plants"][str(code)], "m", "m_ann", npl)
                c = _series(b, "campd", "c_ann", npl)
                if m is not None and c is not None:
                    lp = np.clip(m - addback, 0.0, None)
                    zone = b.get("zone")
                    lmp = lmp_by_zone.get(zone)
                    env = np.zeros(T)
                    for i in idx:
                        env += float(pmax[i]) * av_row(i)
                    env_np = np.zeros(T)
                    for i in nonpeak_i:
                        env_np += float(pmax[i]) * av_row(i)

                    on_m = lp > ON_FRAC * npl
                    on_c = c > ON_FRAC * npl
                    bm = on_m & on_c & (lp < c)
                    deficit = np.where(bm, c - lp, 0.0)
                    # three-way attribution, exact partition of the deficit
                    avail_short = np.where(bm, np.maximum(0.0, c - env), 0.0)
                    cap_c = np.minimum(c, env)
                    peak_short = np.where(
                        bm, np.maximum(0.0, cap_c - np.maximum(lp, env_np)), 0.0
                    )
                    econ_short = np.where(
                        bm, np.maximum(0.0, np.minimum(cap_c, env_np) - lp), 0.0
                    )
                    # F-2 reachability: peak-band capacity out of the money at
                    # the peak offer but in the money at the dearest econ offer
                    if lmp is not None and peak_i and nonpeak_i:
                        mc_pk = np.mean([mc_row(i) for i in peak_i], axis=0)
                        mc_ec = np.max([mc_row(i) for i in nonpeak_i], axis=0)
                        gate = (lmp < mc_pk) & (lmp >= mc_ec)
                        reach = np.where(bm & gate, peak_short, 0.0)
                    else:
                        gate = np.zeros(T, dtype=bool)
                        reach = np.zeros(T)
                    # FOOTPRINT (rule 29 screen-year choice): the mechanism's own
                    # measured reach, with NO meter and NO residual in it — the
                    # re-banded MW, availability-weighted, in the hours the LMP
                    # sits between the econ and peak offers (where moving a MW
                    # between those bands can change dispatch at all).
                    if peak_i:
                        av_pk = np.mean([av_row(i) for i in peak_i], axis=0)
                    else:
                        av_pk = np.zeros(T)
                    reb_mw = (peak_mw - peak_mw_row) if peak_mw_row is not None else 0.0
                    fp = float(np.sum(reb_mw * av_pk * gate))
                    rec["footprint_capacity_hours_mwh"] = _r(fp, 1)
                    mx = float(c.max())
                    mx_h = int(np.argmax(c))
                    rec.update(
                        {
                            "meter_max_mw": _r(mx),
                            "meter_max_month": int(mon[mx_h]),
                            "meter_max_over_nameplate": (
                                _r(mx / v["nameplate_mw"], 3) if v else None
                            ),
                            "meter_max_over_winter": (
                                _r(mx / v["winter_mw"], 3)
                                if v and v["winter_mw"]
                                else None
                            ),
                            "meter_max_over_summer": (
                                _r(mx / v["summer_mw"], 3)
                                if v and v["summer_mw"]
                                else None
                            ),
                            "model_gwh": _r(lp.sum() / 1e3, 1),
                            "meter_gwh": _r(c.sum() / 1e3, 1),
                            "bminus_gwh": _r(deficit.sum() / 1e3, 1),
                            "bminus_avail_short_gwh": _r(avail_short.sum() / 1e3, 1),
                            "bminus_peak_band_short_gwh": _r(peak_short.sum() / 1e3, 1),
                            "bminus_econ_band_short_gwh": _r(econ_short.sum() / 1e3, 1),
                            "reachable_by_rebanding_gwh": _r(reach.sum() / 1e3, 1),
                            "hours_lmp_between_econ_and_peak_offer": int(gate.sum()),
                        }
                    )
                    tot["bminus_gwh"] += deficit.sum() / 1e3
                    tot["avail_short_gwh"] += avail_short.sum() / 1e3
                    tot["peak_short_gwh"] += peak_short.sum() / 1e3
                    tot["econ_short_gwh"] += econ_short.sum() / 1e3
                    tot["reachable_gwh"] += reach.sum() / 1e3
                    tot["footprint_capacity_hours_mwh"] += rec.get(
                        "footprint_capacity_hours_mwh", 0.0
                    )
            tot["peak_band_mw"] += peak_mw
            if peak_mw_row is not None:
                tot["peak_band_mw_row_scoped"] += peak_mw_row
                tot["mw_rebanded"] += peak_mw - peak_mw_row
            plants[str(code)] = rec

        out["years"][str(yr)] = {
            "n_cc_plants": len(plants),
            "fleet_totals": {k: _r(v, 2) for k, v in tot.items()},
            "plants": plants,
        }
        print(f"[nyiso-198 p2] {yr} done", flush=True)

    dest = ROOT / "results/calibration/_nyiso198_duct_peaking_basis_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
