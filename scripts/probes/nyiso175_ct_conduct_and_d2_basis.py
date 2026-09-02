#!/usr/bin/env python3
"""nyiso-175 phase 0 — the CT deficit on the instrument nyiso-174 unlocked, and
the D-2 / ``class_hourly`` split-basis blocker that stands in front of it.

ZERO SOLVE. No parameter is touched, no band is swept, nothing is registered.
Every number here comes from committed artifacts plus the primary record, in the
nyiso-168 → 174 discipline. Decision rules are fixed in
``results/calibration/PREREG-nyiso175-ct-conduct-and-d2-basis.md``, committed
with this file **before either was run**.

Three objects, in the brief's order:

* **A — THE BLOCKER.** nyiso-174 §6 item 3 left D-2's ``class_total_twh`` and
  the keeper's P1 ``class_hourly`` sidecar disagreeing about the model's own
  turbine/steam split by 13-17x on ``ST_CHP`` and 1.6-1.8x on ``CT_CHP`` in the
  opposite direction, while agreeing on the CT+ST total to within 2.2 %. Until
  that is settled no model-side per-class CT/ST reading is identified. Gate A1
  reconstructs D-2's denominator under hypothesis H-A (payload dispatch, CHP
  behind-the-meter add-back, plant-majority label); gate A2 is its sign
  falsifier; A3 settles the rule 20 ``[R-FORCED-BUDGET]`` hazard from the code.

* **B — THE CT INSTRUMENT.** ``CT_CHP`` became identifiable at nyiso-174
  (anchor 4.933 on 1 unit -> 0.892 on 3). Measure the model's CT conduct against
  the market's at hourly grain — duration curves, hour-matching, starts and run
  lengths, load-band concentration — and decide LEVEL vs RESPONSE on the
  pre-registered B5 rule. ``CT_PEAKER`` is measured alongside for confirmation
  ONLY: its deficit is adjudicated to root (nyiso-88/90/91/96) and S4 forbids
  opening a lever on it.

* **C — EAST RIVER AND THE TRANCHE-DERIVE ATTRIBUTION AUDIT.** nyiso-174 §6
  item 2's successor object, plus the named candidate mechanism:
  ``derive_thermal_tranches._fleet_nameplate_and_group`` attributes a plant's
  FACILITY-SUMMED CAMPD net to the single group holding the most nameplate,
  which at a mixed plant is a guess. Kill conditions S2 (a)(b)(c), the
  one-plant-vs-fleet test S3, and the required-move bound S5.

Rule 13 ``[R-MEASURED]``: every input is a reproducible measured record used for
classification/attribution identification only; nothing is pinned to an outcome.
Rule 22 ``[R-HOLDOUT]``: 2023-2025 only.

Run: ``PYTHONPATH=.:src python scripts/probes/nyiso175_ct_conduct_and_d2_basis.py``
Writes: ``results/calibration/_nyiso175_ct_conduct_and_d2_basis.json``
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.chp import _chp_by_plant  # noqa: E402
from scripts.lib.campd_measured_classes import (  # noqa: E402
    campd_unittype_class,
    corrected_unit_class,
)

YEARS = (2023, 2024, 2025)
ISO = "NYISO"
BENCH = REPO / "frontend/data/backcast/bench/NYISO"
KEEPER = REPO / "results/calibration/nyiso159_lossarm_B"
RUN_JS = REPO / "frontend/data/backcast/runs/2026-08-30-nyiso-159-loss-surface.js"
OUT = REPO / "results/calibration/_nyiso175_ct_conduct_and_d2_basis.json"

EAST_RIVER = 2493
GAS_CLASSES = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
CT_CLASSES = ("CT_CHP", "CT_PEAKER")

#: The turbine-fired family, for the S2(a) split (mirrors
#: :data:`scripts.lib.campd_measured_classes.PRIME_MOVER_FAMILY`'s turbine half).
TURBINE_CLASSES = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER")

#: nyiso-168 §2's load bands, so the CT deficit is apportioned on the same axis
#: the C3a deficit was located on.
LOAD_BANDS = ((0, 50), (50, 80), (80, 90), (90, 95), (95, 99), (99, 99.9), (99.9, 100))

#: The online bar for starts / run lengths — a fraction of the class's own
#: demonstrated capacity, the nyiso-90 §1 / nyiso-96 §2 construction, so the
#: numbers here are directly comparable to the closed CT_PEAKER record.
ONLINE_FRAC = 0.02


# ----------------------------------------------------------------- loaders --


def _round(x, n=4):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(v) else round(v, n)


def chp_plants() -> set[int]:
    """EIA-860 CHP plant codes — the model's own CHP determination."""
    flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
    return {int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"}


def model_groups_by_plant(year: int) -> dict[int, dict[str, float]]:
    """``{plant_code: {plant_group: pmax MW}}`` from the model's own fleet."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    out: dict[int, dict[str, float]] = {}
    for g in load_fleet_from_csv(ISO, get_iso_config(ISO), year=year):
        code = int(g.plant_code)
        if code <= 0 or not g.plant_group:
            continue
        out.setdefault(code, {})
        out[code][g.plant_group] = out[code].get(g.plant_group, 0.0) + float(g.pmax_mw)
    return out


def campd_hourly(year: int) -> pd.DataFrame:
    """CAMPD NY unit-hourly, with the class each unit's PLANT actually carries.

    ``grossLoad`` NULL means a non-operating unit-hour (52 % of NY CC unit-hours
    in 2025) and is filled to ZERO explicitly — a NULL-propagating aggregation
    silently returns NaN (trap (d)). The class is
    :func:`scripts.lib.campd_measured_classes.corrected_unit_class`, never the
    bare ``unitType`` string (trap (f), the nyiso-174 repair).
    """
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=[
            "facilityId",
            "unitId",
            "unitType",
            "date",
            "hour",
            "grossLoad",
            "opTime",
        ],
    )
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    d["opTime"] = d["opTime"].fillna(0.0)
    d["facilityId"] = d["facilityId"].astype(int)
    chpset = chp_plants()
    mg = model_groups_by_plant(year)
    pairs = d[["facilityId", "unitType"]].drop_duplicates()
    kmap: dict[tuple[int, str], str | None] = {}
    for fid, ut in zip(pairs["facilityId"], pairs["unitType"]):
        raw = campd_unittype_class(ut, int(fid) in chpset)
        kmap[(int(fid), str(ut))] = corrected_unit_class(raw, mg.get(int(fid)))
    d["klass"] = [
        kmap[(int(f), str(u))] for f, u in zip(d["facilityId"], d["unitType"])
    ]
    # STD_TZ: the probe corpus works on the FIXED standard-time clock
    # ("Etc/GMT+5"); America/New_York raises on the DST-nonexistent hour
    # 2023-03-12 02:00 (trap (c)). Hour index = position in the year's own
    # standard-time calendar.
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    d["hix"] = ((ts - pd.Timestamp(f"{year}-01-01")) // pd.Timedelta("1h")).astype(int)
    return d


def measured_class_hourly(year: int) -> dict[str, np.ndarray]:
    """Measured CAMPD gross MW by corrected model class, 8760 hours."""
    d = campd_hourly(year)
    t = 8784 if year % 4 == 0 else 8760
    out: dict[str, np.ndarray] = {}
    for k, sub in d.groupby("klass"):
        if k is None:
            continue
        v = np.zeros(t)
        np.add.at(v, sub["hix"].to_numpy(), sub["grossLoad"].to_numpy(dtype=float))
        out[str(k)] = v[:8760]
    return out


def measured_plant_class_hourly(year: int, code: int) -> dict[str, np.ndarray]:
    """One plant's measured CAMPD gross MW by corrected class, 8760 hours."""
    d = campd_hourly(year)
    d = d[d["facilityId"] == code]
    t = 8784 if year % 4 == 0 else 8760
    out: dict[str, np.ndarray] = {}
    for k, sub in d.groupby("klass"):
        if k is None:
            continue
        v = np.zeros(t)
        np.add.at(v, sub["hix"].to_numpy(), sub["grossLoad"].to_numpy(dtype=float))
        out[str(k)] = v[:8760]
    return out


def bench_classes(year: int) -> dict[str, float]:
    """Committed grid-delivered class volumes (``classFull``), TWh."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["classFull"]


def model_class_hourly(year: int) -> dict[str, np.ndarray]:
    """The keeper's own P1 hourly class dispatch (rule 15: read, don't replay)."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    out = {}
    for k, sub in c.groupby("klass"):
        s = sub.sort_values("hour")["mw"].to_numpy(dtype=float)
        out[str(k)] = s[:8760]
    return out


def model_demand(year: int) -> np.ndarray:
    """The keeper's own hourly NYCA demand (sum over zones), 8760 hours."""
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return s.groupby("hour")["demand"].sum().sort_index().to_numpy(dtype=float)[:8760]


def payload() -> dict:
    """Decode the keeper's committed dashboard run payload."""
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', RUN_JS.read_text())
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def payload_plant_series(pay: dict, year: int) -> dict[str, np.ndarray]:
    """Per-(plant, class) model hourly MW from the payload, keyed as committed."""
    import scripts.legitimacy_diagnostics as ld

    bench = ld.load_bench(REPO, ISO, year)
    plants = pay["years"][str(year)]["plants"]
    out = {}
    for pid, p in plants.items():
        if not p.get("m"):
            continue
        npl = bench.get(pid, {}).get("npl", 0.0)
        out[pid] = ld._decode_cf_bytes(p["m"], p.get("m_ann"), npl)
    return out


# --------------------------------------------------------- A: the blocker --


def _d2_class_totals(diag: dict) -> dict[str, dict[str, float]]:
    """``{year: {class: class_total_twh}}`` over D-2's rows AND summary.

    A class with no forced energy has no DETAIL row but does carry a summary
    row (``CT_PEAKER`` at NYISO), and a class-exempt one (the three CHP
    classes) has detail rows but no summary row — so the union is the only
    complete view of the denominator D-2 actually used.
    """
    out: dict[str, dict[str, float]] = {}
    d2 = diag["diagnostics"]["D2"]
    for r in list(d2.get("rows", [])) + list(d2.get("summary", [])):
        out.setdefault(str(r["year"]), {}).setdefault(
            str(r["class"]), float(r["class_total_twh"])
        )
    return out


def a1_d2_basis() -> dict:
    """A1/A2 — reconstruct D-2's ``class_total_twh`` and test H-A.

    The authoritative reconstruction is the diagnostics module's own D-2 path,
    re-run at HEAD from committed artifacts (floors rebuilt via
    ``run_year(fleet_only=True)`` — a fleet build, NOT an LP). The
    pre-registered fallback, used verbatim if that cannot run in this container,
    is a self-contained payload + fleet reconstruction whose label rule is the
    plant-majority convention read off ``plant_class_rows``.
    """
    committed = json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())
    ref = _d2_class_totals(committed)

    recon: dict[str, dict[str, float]] = {}
    route = "diagnostics-recompute"
    err = None
    with tempfile.TemporaryDirectory() as td:
        jout = Path(td) / "d2.json"
        cmd = [
            sys.executable,
            str(REPO / "scripts/legitimacy_diagnostics.py"),
            "--bundle",
            str(KEEPER),
            "--iso",
            ISO,
            "--only",
            "D2",
            "--json-out",
            str(jout),
        ]
        env = {"PYTHONPATH": f"{REPO}:{REPO / 'src'}"}
        import os

        e = dict(os.environ)
        e.update(env)
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO), env=e)
        if jout.exists():
            recon = _d2_class_totals(json.loads(jout.read_text()))
        else:
            err = (p.stderr or p.stdout)[-2000:]

    if not recon:
        route = "fallback-payload-fleet"
        pay = payload()
        for y in YEARS:
            ser = payload_plant_series(pay, y)
            import scripts.lib.bench_multiclass as bm

            by_plant: dict[str, float] = {}
            for key, arr in ser.items():
                code = str(bm.plant_code_of_key(key))
                by_plant[code] = by_plant.get(code, 0.0) + float(
                    np.clip(arr, 0.0, None).sum()
                )
            mg = model_groups_by_plant(y)
            lab: dict[str, str] = {}
            for code, groups in mg.items():
                # plant-majority by UNIT COUNT is the D-2 rule; at generator
                # grain a tie resolves to the alphabetically-first class, which
                # is np.unique + argmax's own behaviour.
                names = sorted(groups)
                lab[str(code)] = names[0] if names else ""
            acc: dict[str, float] = {}
            for code, mwh in by_plant.items():
                k = lab.get(code, "")
                acc[k] = acc.get(k, 0.0) + mwh / 1e6
            recon[str(y)] = acc

    rows = []
    passed = True
    for y in YEARS:
        for k in sorted(set(ref.get(str(y), {})) | set(recon.get(str(y), {}))):
            a = ref.get(str(y), {}).get(k)
            b = recon.get(str(y), {}).get(k)
            if a is None or b is None:
                ok = False
                rel = None
            else:
                rel = abs(b - a) / a if a > 0 else None
                ok = (rel is not None and rel <= 0.005) or abs(b - a) <= 0.005
            rows.append(
                {
                    "year": y,
                    "class": k,
                    "committed_twh": _round(a),
                    "recon_twh": _round(b),
                    "rel_delta": _round(rel, 6),
                    "within_gate": bool(ok),
                }
            )
            if k in GAS_CLASSES or k == "hydro":
                passed = passed and ok

    # A2 — the sign falsifier: which class does East River's energy land on?
    mg = model_groups_by_plant(2025)
    er_groups = sorted(mg.get(EAST_RIVER, {}))
    return {
        "route": route,
        "recompute_error": err,
        "rows": rows,
        "gate_A1_pass": bool(passed),
        "east_river_model_groups": {
            k: _round(v, 1) for k, v in mg.get(EAST_RIVER, {}).items()
        },
        "east_river_majority_label_alpha_tie": er_groups[0] if er_groups else None,
        "note": (
            "gate A1 accepts H-A iff every gas class-year and hydro reproduces "
            "within 0.5 % relative (or 0.005 TWh absolute)"
        ),
    }


def a_posthoc_grain_identity() -> dict:
    """POST-HOC (added after gate A1 returned; NOT pre-registered, labelled as such).

    Gate A1's pre-registered route — recompute D-2 at HEAD — FAILS, and the
    failure identifies the basis rather than leaving it open: the committed
    artifact was built on the solve's own ``dispatch/<year>_P1.parquet`` (every
    model plant), while a HEAD recompute can only reach the 100-plant run
    payload. Two measurements settle what the committed denominator IS, both
    computable from committed artifacts alone:

    * **the untouched-class identity** — for a class with no mixed-class plant,
      D-2's ``class_total_twh`` must equal ``class_hourly``'s class sum exactly
      if and only if the committed D-2 ran on the full LP dispatch;
    * **the conservation identity** — if a mixed plant's whole energy is
      relabelled onto its plant-majority class, the pair's D-2-minus-
      ``class_hourly`` deltas must be equal and opposite.

    The plant-majority label itself is read off the floors arrays the
    diagnostics rebuild wrote (LP-unit grain, the D-2 rule), not inferred.
    """
    d2 = _d2_class_totals(
        json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())
    )

    per_year = {}
    for y in YEARS:
        ch = model_class_hourly(y)
        chs = {k: float(v.sum()) / 1e6 for k, v in ch.items()}
        row = d2.get(str(y), {})
        deltas = {
            k: _round(row.get(k, 0.0) - chs.get(k, 0.0))
            for k in sorted(set(row) | set(chs))
            if k not in ("",)
        }
        per_year[str(y)] = {
            "d2_class_total_twh": {k: _round(v) for k, v in sorted(row.items())},
            "class_hourly_twh": {k: _round(v) for k, v in sorted(chs.items())},
            "delta_d2_minus_class_hourly": deltas,
            "hydro_identical": bool(
                abs(row.get("hydro", 0.0) - chs.get("hydro", 0.0)) < 5e-4
            ),
            "ct_st_chp_transfer_residual_twh": _round(
                (row.get("CT_CHP", 0.0) - chs.get("CT_CHP", 0.0))
                + (row.get("ST_CHP", 0.0) - chs.get("ST_CHP", 0.0))
            ),
        }

    floors = {}
    for y in YEARS:
        f = KEEPER / f"floors/{y}_rebuilt.npz"
        if not f.exists():
            continue
        z = np.load(f, allow_pickle=True)
        pc = np.asarray(z["plant_code"])
        pg = np.asarray(z["plant_group"]).astype(str)
        uid = np.asarray(z["unit_ids"]).astype(str)
        mg = np.asarray(z["min_gen"], dtype=float)
        mech = np.asarray(z["mechanism"])
        sel = pc == EAST_RIVER
        counts: dict[str, int] = {}
        for g in pg[sel]:
            counts[str(g)] = counts.get(str(g), 0) + 1
        floors[str(y)] = {
            "east_river_lp_units_by_group": counts,
            "plant_majority_label": (
                max(sorted(counts), key=lambda k: counts[k]) if counts else None
            ),
            "east_river_units": [
                {
                    "unit": str(u),
                    "max_floor_mw": _round(float(g.max()), 2),
                    "hours_floored": int((g > 0).sum()),
                    "floor_energy_twh": _round(float(g.sum()) / 1e6),
                    "mechanisms": sorted(
                        {int(x) for x in m[g > 0].tolist()} if (g > 0).any() else set()
                    ),
                }
                for u, g, m in zip(uid[sel], mg[sel], mech[sel])
            ],
        }
    return {
        "labelled": "POST-HOC — added after gate A1 returned; not pre-registered",
        "by_year": per_year,
        "east_river_floors": floors,
    }


def a3_payload_vs_class_hourly() -> dict:
    """A3 — size the CHP behind-the-meter add-back, and settle the rule 20 hazard."""
    import scripts.legitimacy_diagnostics as ld
    import scripts.lib.bench_multiclass as bm

    pay = payload()
    out = {}
    for y in YEARS:
        ser = payload_plant_series(pay, y)
        by_class: dict[str, float] = {}
        for key, arr in ser.items():
            k = bm.parse_key(key)[1] if bm.KEY_SEP in key else None
            if k is None:
                continue
            by_class[k] = by_class.get(k, 0.0) + float(arr.sum()) / 1e6
        ch = model_class_hourly(y)
        out[str(y)] = {
            "payload_sliced_twh": {k: _round(v) for k, v in sorted(by_class.items())},
            "class_hourly_twh": {
                k: _round(float(v.sum()) / 1e6) for k, v in sorted(ch.items())
            },
        }
    return {
        "by_year": out,
        "d2_exempt_classes": list(ld.D2_EXEMPT_CLASSES),
        "d2_peaker_classes": list(ld.D2_PEAKER_CLASSES),
        "chp_classes_reach_gated_summary": bool(
            {"CC_CHP", "CT_CHP", "ST_CHP"} - set(ld.D2_EXEMPT_CLASSES)
        ),
        "committed_d2_summary_classes": sorted(
            {
                str(r["class"])
                for r in json.loads(
                    (KEEPER / "legitimacy_diagnostics.json").read_text()
                )["diagnostics"]["D2"]["summary"]
            }
        ),
    }


# ------------------------------------------------------- B: the CT instrument --


def _runs(on: np.ndarray) -> list[int]:
    """Contiguous run lengths of a boolean online mask."""
    idx = np.flatnonzero(np.diff(np.r_[0, on.astype(int), 0]))
    return list((idx[1::2] - idx[0::2]).astype(int))


def b_ct_conduct() -> dict:
    """B1-B5 — the model's CT conduct against the market's, at hourly grain."""
    out: dict[str, dict] = {}
    for y in YEARS:
        meas = measured_class_hourly(y)
        mod = model_class_hourly(y)
        bench = bench_classes(y)
        dem = model_demand(y)
        pct = pd.Series(dem).rank(pct=True).to_numpy() * 100.0
        year_rows = {}
        for k in CT_CLASSES:
            a = meas.get(k, np.zeros(8760))
            m = mod.get(k, np.zeros(8760))
            b = float(bench.get(k, 0.0))
            gross = float(a.sum()) / 1e6
            anchor = (b / gross) if gross > 0 else None
            aa = a * anchor if anchor else a  # level-anchored measured series
            # B2 duration curves
            sa, sm = np.sort(aa)[::-1], np.sort(m)[::-1]
            dec = []
            for i in range(10):
                lo, hi = i * 876, (i + 1) * 876
                ma, mm = float(sa[lo:hi].mean()), float(sm[lo:hi].mean())
                dec.append(
                    {
                        "decile": i,
                        "measured_anchored_mw": _round(ma, 2),
                        "model_mw": _round(mm, 2),
                        "ratio": _round(mm / ma, 4) if ma > 0 else None,
                    }
                )
            # B3 hour matching / starts / runs
            bar_a = ONLINE_FRAC * float(np.percentile(aa, 99.5))
            bar_m = ONLINE_FRAC * float(np.percentile(aa, 99.5))
            on_a, on_m = aa > bar_a, m > bar_m
            ra, rm = _runs(on_a), _runs(on_m)
            r = (
                float(np.corrcoef(aa, m)[0, 1])
                if aa.std() > 0 and m.std() > 0
                else None
            )
            covered = float(aa[on_m].sum() / aa.sum()) if aa.sum() > 0 else None
            # B4 load-band apportionment of the deficit
            bands = []
            gap = aa - m
            for lo, hi in LOAD_BANDS:
                sel = (pct > lo) & (pct <= hi) if lo > 0 else (pct <= hi)
                bands.append(
                    {
                        "band": f"{lo}-{hi}",
                        "hours": int(sel.sum()),
                        "deficit_gwh": _round(float(gap[sel].sum()) / 1e3, 3),
                        "share_of_deficit": _round(
                            float(gap[sel].sum() / gap.sum())
                            if gap.sum() != 0
                            else None
                        ),
                    }
                )
            q90a, q90m = float(np.percentile(aa, 90)), float(np.percentile(m, 90))
            lvl = (q90m / q90a) if q90a > 0 else None
            if lvl is None or r is None:
                verdict = "UNIDENTIFIED"
            elif lvl < 0.70 and r < 0.50:
                verdict = "BOTH"
            elif lvl < 0.70:
                verdict = "LEVEL"
            elif r < 0.50:
                verdict = "RESPONSE"
            else:
                verdict = "NEITHER"
            year_rows[k] = {
                "cems_gross_twh": _round(gross),
                "bench_classfull_twh": _round(b),
                "anchor": _round(anchor),
                "model_twh": _round(float(m.sum()) / 1e6),
                "class_error_pct": _round(100.0 * (m.sum() / 1e6 / b - 1.0), 2)
                if b > 0
                else None,
                "online_bar_mw": _round(bar_a, 2),
                "measured_on_hours": int(on_a.sum()),
                "model_on_hours": int(on_m.sum()),
                "measured_starts": len(ra),
                "model_starts": len(rm),
                "measured_run_mean_h": _round(np.mean(ra), 2) if ra else None,
                "model_run_mean_h": _round(np.mean(rm), 2) if rm else None,
                "measured_run_median_h": _round(np.median(ra), 1) if ra else None,
                "model_run_median_h": _round(np.median(rm), 1) if rm else None,
                "hourly_r": _round(r),
                "measured_energy_in_model_on_hours": _round(covered),
                "p90_measured_anchored_mw": _round(q90a, 2),
                "p90_model_mw": _round(q90m, 2),
                "q90_ratio": _round(lvl),
                "B5_verdict": verdict,
                "duration_deciles": dec,
                "load_bands": bands,
            }
        out[str(y)] = year_rows
    return out


# ------------------------------------- C: East River + the attribution audit --


def b6_east_river_plant_grain() -> dict:
    """POST-HOC (added after B returned; NOT pre-registered, labelled as such).

    B5 returns RESPONSE for ``CT_CHP`` in all three years, and the class is
    68.6 % East River by capacity — so the class result is read at the plant
    that carries it, on a SINGLE, stated basis.

    **The basis trap this measurement exists to avoid.** The payload's per-
    (plant, class) series carries a report-only CHP behind-the-meter add-back
    (``render_calibration_html``: ``mw += btm_mwh / T``, flat), while
    ``class_hourly`` and the LP carry the GRID series with the host self-supply
    held out. Comparing one to the other mixes bases. Here the add-back is
    REMOVED explicitly — ``grid = payload - share x e923_slice / T`` with the
    share read from :func:`market_sim.data.chp.chp_btm_pct` — so the model side
    is the LP's own grid dispatch, the same basis ``class_hourly`` and the
    scored C1 comparison use.
    """
    from market_sim.data.chp import chp_btm_pct

    g860 = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_generator_operable.parquet")
    e860 = g860[g860["Plant Code"] == EAST_RIVER]
    g923 = pd.read_parquet(
        RAW_DATA_DIR / "_processed-legacy/eia923_monthly_generation.parquet"
    )
    pay = payload()
    out = {}
    for y in YEARS:
        ser = payload_plant_series(pay, y)
        e = g923[(g923["plant_id"] == EAST_RIVER) & (g923["year"] == y)]
        pm = e.groupby("prime_mover")["netgen_annual_mwh"].sum()
        e923 = {"CT_CHP": float(pm.get("GT", 0.0)), "ST_CHP": float(pm.get("ST", 0.0))}
        meas = measured_plant_class_hourly(y, EAST_RIVER)
        mod_class = model_class_hourly(y)
        bench = bench_classes(y)
        rows = {}
        for k in ("CT_CHP", "ST_CHP"):
            raw = ser.get(f"{EAST_RIVER}:{k}")
            if raw is None:
                continue
            share = chp_btm_pct(EAST_RIVER, k, iso=ISO) / 100.0
            grid = np.clip(raw - share * e923[k] / 8760.0, 0.0, None)
            a = meas.get(k, np.zeros(8760))
            rows[k] = {
                "btm_share": _round(share, 3),
                "eia923_netgen_twh": _round(e923[k] / 1e6),
                "payload_twh_with_addback": _round(float(raw.sum()) / 1e6),
                "model_grid_twh": _round(float(grid.sum()) / 1e6),
                "model_grid_p05_mw": _round(float(np.percentile(grid, 5)), 2),
                "model_grid_p25_mw": _round(float(np.percentile(grid, 25)), 2),
                "model_grid_p50_mw": _round(float(np.percentile(grid, 50)), 2),
                "model_grid_p90_mw": _round(float(np.percentile(grid, 90)), 2),
                "measured_campd_twh": _round(float(a.sum()) / 1e6),
                "measured_min_mw": _round(float(a.min()), 2),
                "measured_p05_mw": _round(float(np.percentile(a, 5)), 2),
                "measured_p25_mw": _round(float(np.percentile(a, 25)), 2),
                "measured_p50_mw": _round(float(np.percentile(a, 50)), 2),
                "measured_p90_mw": _round(float(np.percentile(a, 90)), 2),
                "measured_zero_hours": int((a <= 0.0).sum()),
                "hourly_r_grid_vs_measured": (
                    _round(float(np.corrcoef(grid, a)[0, 1]))
                    if grid.std() > 0 and a.std() > 0
                    else None
                ),
            }
        # Scored-basis attribution: class_hourly (LP grid) vs classFull, the
        # nyiso-169b measurement-A basis nyiso-174 section 4.2 reproduced.
        cg = {}
        for k in ("CT_CHP", "ST_CHP"):
            m_cls = float(mod_class.get(k, np.zeros(8760)).sum()) / 1e6
            b_cls = float(bench.get(k, 0.0))
            er = rows.get(k, {})
            er_gap = (er.get("model_grid_twh") or 0.0) - (
                er.get("eia923_netgen_twh") or 0.0
            )
            cg[k] = {
                "class_model_twh": _round(m_cls),
                "class_bench_twh": _round(b_cls),
                "class_gap_twh": _round(m_cls - b_cls),
                "east_river_gap_twh": _round(er_gap),
                "east_river_share_of_class_gap": _round(
                    er_gap / (m_cls - b_cls) if (m_cls - b_cls) != 0 else None
                ),
            }
        out[str(y)] = {"bins": rows, "scored_basis_attribution": cg}
    return {
        "labelled": "POST-HOC — added after B returned; not pre-registered",
        "eia860_published_minimum_load_mw": {
            str(r["Generator ID"]).strip(): {
                "prime_mover": str(r["Prime Mover"]).strip().upper(),
                "min_load_mw": _round(r["Minimum Load (MW)"], 1),
                "summer_mw": _round(r["Summer Capacity (MW)"], 1),
            }
            for _, r in e860.iterrows()
        },
        "by_year": out,
    }


def b7_steam_host_driver() -> dict:
    """POST-HOC (added after B6 returned; NOT pre-registered, labelled as such).

    ``chp_steam_following`` is the SOLE mechanism forcing ``CT_CHP`` (rule 19
    enumeration below), and B5 types the class deficit as a RESPONSE deficit —
    the model reaches comparable output in the wrong hours. A steam-following
    mechanism is only identified if the host's steam demand is (a) MEASURED at
    hourly grain and (b) actually predicts the plant's electric conduct. Both
    are testable here without a solve: CAMPD meters East River's district-steam
    send-out on its two direct-fired boilers (``steamLoad``, klb/h), which is
    the same host load its turbine block serves.

    Reported, never armed: this names whether a driver EXISTS for a successor,
    and its absence would close the route.
    """
    out = {}
    for y in YEARS:
        raw = pd.read_parquet(
            RAW_DATA_DIR / f"campd-unit-level/NY_{y}.parquet",
            columns=["facilityId", "unitId", "date", "hour", "steamLoad", "grossLoad"],
        )
        raw["facilityId"] = raw["facilityId"].astype(int)
        raw = raw[raw["facilityId"] == EAST_RIVER]
        raw["steamLoad"] = raw["steamLoad"].fillna(0.0)
        raw["grossLoad"] = raw["grossLoad"].fillna(0.0)
        ts = pd.to_datetime(raw["date"]) + pd.to_timedelta(raw["hour"], unit="h")
        raw["hix"] = ((ts - pd.Timestamp(f"{y}-01-01")) // pd.Timedelta("1h")).astype(
            int
        )
        t = 8784 if y % 4 == 0 else 8760
        steam = np.zeros(t)
        np.add.at(steam, raw["hix"].to_numpy(), raw["steamLoad"].to_numpy(float))
        steam = steam[:8760]
        pc = measured_plant_class_hourly(y, EAST_RIVER)
        elec = pc.get("CT_CHP", np.zeros(8760))
        dem = model_demand(y)
        mod = model_class_hourly(y).get("CT_CHP", np.zeros(8760))
        by_unit = (
            raw.groupby("unitId")[["steamLoad", "grossLoad"]].sum().round(1).to_dict()
        )
        out[str(y)] = {
            "steam_klb_total": _round(float(steam.sum()), 0),
            "steam_by_unit_klb": {
                str(k): _round(v, 0) for k, v in by_unit.get("steamLoad", {}).items()
            },
            "gross_by_unit_mwh": {
                str(k): _round(v, 0) for k, v in by_unit.get("grossLoad", {}).items()
            },
            "r_measured_elec_vs_steam": (
                _round(float(np.corrcoef(elec, steam)[0, 1]))
                if elec.std() > 0 and steam.std() > 0
                else None
            ),
            "r_measured_elec_vs_load": (
                _round(float(np.corrcoef(elec, dem)[0, 1])) if elec.std() > 0 else None
            ),
            "r_model_class_vs_steam": (
                _round(float(np.corrcoef(mod, steam)[0, 1]))
                if mod.std() > 0 and steam.std() > 0
                else None
            ),
            "r_model_class_vs_load": (
                _round(float(np.corrcoef(mod, dem)[0, 1])) if mod.std() > 0 else None
            ),
            "steam_monthly_klb": [
                _round(float(steam[i * 730 : (i + 1) * 730].sum()), 0)
                for i in range(12)
            ],
            "measured_elec_monthly_gwh": [
                _round(float(elec[i * 730 : (i + 1) * 730].sum()) / 1e3, 2)
                for i in range(12)
            ],
        }
    return {
        "labelled": "POST-HOC — added after B6 returned; not pre-registered",
        "by_year": out,
    }


def c_east_river_and_attribution() -> dict:
    """S2 / S3 / S5 — the named candidate mechanism, and its kill conditions."""
    g923 = pd.read_parquet(
        RAW_DATA_DIR / "_processed-legacy/eia923_monthly_generation.parquet"
    )
    pay = payload()
    per_year = {}
    s2a, s2b, s2c = [], [], []
    for y in YEARS:
        # (a) turbine share of the plant's CAMPD grossLoad
        pc = measured_plant_class_hourly(y, EAST_RIVER)
        tot = sum(float(v.sum()) for v in pc.values())
        turb = sum(float(v.sum()) for k, v in pc.items() if k in TURBINE_CLASSES)
        share_turbine = (turb / tot) if tot > 0 else None
        # (b) EIA-923 GT : ST
        e = g923[(g923["plant_id"] == EAST_RIVER) & (g923["year"] == y)]
        by_pm = e.groupby("prime_mover")["netgen_annual_mwh"].sum()
        gt, st = float(by_pm.get("GT", 0.0)), float(by_pm.get("ST", 0.0))
        ratio_923 = (gt / st) if st > 0 else None
        # (c) the model's own split, from the payload slices
        ser = payload_plant_series(pay, y)
        m_ct = float(ser.get(f"{EAST_RIVER}:CT_CHP", np.zeros(8760)).sum())
        m_st = float(ser.get(f"{EAST_RIVER}:ST_CHP", np.zeros(8760)).sum())
        ratio_model_st_ct = (m_st / m_ct) if m_ct > 0 else None
        ratio_923_st_gt = (st / gt) if gt > 0 else None
        inversion = (
            ratio_model_st_ct / ratio_923_st_gt
            if ratio_model_st_ct and ratio_923_st_gt
            else None
        )
        s2a.append(share_turbine)
        s2b.append(ratio_923)
        s2c.append(inversion)
        per_year[str(y)] = {
            "campd_gross_twh_by_class": {
                k: _round(float(v.sum()) / 1e6) for k, v in sorted(pc.items())
            },
            "campd_turbine_share": _round(share_turbine),
            "eia923_gt_twh": _round(gt / 1e6),
            "eia923_st_twh": _round(st / 1e6),
            "eia923_gt_over_st": _round(ratio_923, 3),
            "model_payload_ct_chp_twh": _round(m_ct / 1e6),
            "model_payload_st_chp_twh": _round(m_st / 1e6),
            "model_st_over_ct": _round(ratio_model_st_ct, 3),
            "eia923_st_over_gt": _round(ratio_923_st_gt, 3),
            "inversion_x": _round(inversion, 3),
        }

    # S3 — one plant or a fleet-wide derive question?
    audit = []
    for y in YEARS:
        mg = model_groups_by_plant(y)
        d = campd_hourly(y)
        e = d.groupby(["facilityId", "klass"])["grossLoad"].sum()
        for code, groups in mg.items():
            if len(groups) < 2:
                continue
            primary = max(groups.items(), key=lambda kv: kv[1])[0]
            try:
                sub = e.loc[code]
            except KeyError:
                continue
            tot = float(sub.sum())
            if tot <= 0:
                continue
            carrier = str(sub.idxmax())
            frac = float(sub.max() / tot)
            if carrier != primary and frac >= 0.60:
                audit.append(
                    {
                        "year": y,
                        "plant_code": int(code),
                        "primary_group_by_nameplate": primary,
                        "campd_energy_carrier": carrier,
                        "carrier_share": _round(frac),
                        "campd_twh": _round(tot / 1e6),
                        "group_mw": {
                            k: _round(v, 1) for k, v in sorted(groups.items())
                        },
                        "nameplate_margin_mw": _round(
                            groups.get(primary, 0.0) - groups.get(carrier, 0.0), 1
                        ),
                    }
                )
    tot_mis = sum(r["campd_twh"] or 0.0 for r in audit)
    er_mis = sum(r["campd_twh"] or 0.0 for r in audit if r["plant_code"] == EAST_RIVER)

    # S5 — the required-move bound on C1 CT_CHP
    s5 = {}
    for y in YEARS:
        b = bench_classes(y)
        mod = model_class_hourly(y)
        m_ct = float(mod.get("CT_CHP", np.zeros(8760)).sum()) / 1e6
        b_ct = float(b.get("CT_CHP", 0.0))
        e = g923[(g923["plant_id"] == EAST_RIVER) & (g923["year"] == y)]
        gt = float(e.groupby("prime_mover")["netgen_annual_mwh"].sum().get("GT", 0.0))
        ser = payload_plant_series(payload(), y)
        m_er_ct = float(ser.get(f"{EAST_RIVER}:CT_CHP", np.zeros(8760)).sum())
        s5[str(y)] = {
            "class_error_pct": _round(100.0 * (m_ct / b_ct - 1.0), 2) if b_ct else None,
            "class_gap_twh": _round(m_ct - b_ct),
            "east_river_gt_gap_twh": _round((m_er_ct - gt) / 1e6),
            "bound_share_of_class_gap": _round(
                ((m_er_ct - gt) / 1e6) / (m_ct - b_ct) if (m_ct - b_ct) != 0 else None
            ),
        }

    return {
        "east_river": per_year,
        "S2a_campd_turbine_share": [_round(v) for v in s2a],
        "S2a_pass": bool(all(v is not None and v >= 0.90 for v in s2a)),
        "S2b_eia923_gt_over_st": [_round(v, 3) for v in s2b],
        "S2b_pass": bool(all(v is not None and v >= 2.0 for v in s2b)),
        "S2c_inversion_x": [_round(v, 3) for v in s2c],
        "S2c_pass": bool(sum(1 for v in s2c if v is not None and v >= 1.5) >= 2),
        "S3_misattributed_rows": audit,
        "S3_total_misattributed_twh": _round(tot_mis),
        "S3_east_river_twh": _round(er_mis),
        "S3_east_river_share": _round(er_mis / tot_mis) if tot_mis > 0 else None,
        "S3_pass_one_plant": bool(tot_mis > 0 and er_mis / tot_mis >= 0.50),
        "S5_required_move": s5,
        "tranche_rows_nyiso_chp": _tranche_chp_rows(),
    }


def _tranche_chp_rows() -> list[dict]:
    """The NYISO CHP tranche rows — the floor level source, read not assumed."""
    p = RAW_DATA_DIR / "_processed-legacy/thermal_tranches_NYISO.csv"
    d = pd.read_csv(p)
    d = d[d["plant_group"].isin(("CC_CHP", "CT_CHP", "ST_CHP"))]
    return json.loads(d.to_json(orient="records"))


# ------------------------------------------ C-enum: rule 19 [R-ONE-MECH] --


def rule19_enumeration() -> dict:
    """Everything that floors, gates or derates CT_PEAKER and CT_CHP."""
    from market_sim.data import outages

    committed = json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())
    d2 = committed["diagnostics"]["D2"]
    rows = [r for r in d2["rows"] if str(r["class"]) in CT_CLASSES]
    summary = [r for r in d2["summary"] if str(r["class"]) in CT_CLASSES]
    targets = {}
    for k in CT_CLASSES + ("ST_CHP", "ST_GAS", "CC_REGULAR"):
        try:
            targets[k] = repr(outages._generic_unit_outage_target(EAST_RIVER, {}, k))
        except Exception as exc:  # pragma: no cover - defensive
            targets[k] = f"ERROR: {exc}"
    cfg = json.loads((KEEPER / "run_config.json").read_text())
    return {
        "d2_rows_ct": rows,
        "d2_summary_ct": summary,
        "generic_unit_outage_target": targets,
        "keeper_flags": {
            k: cfg.get(k)
            for k in sorted(cfg)
            if any(
                s in k
                for s in (
                    "chp",
                    "floor",
                    "bridge",
                    "outage",
                    "reliability",
                    "commitment",
                    "offer",
                    "wefor",
                )
            )
        },
    }


def main() -> None:
    res = {
        "session": "nyiso-175",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "prereg": "results/calibration/PREREG-nyiso175-ct-conduct-and-d2-basis.md",
        "years": list(YEARS),
        "A_d2_basis": a1_d2_basis(),
        "A_posthoc_grain_identity": a_posthoc_grain_identity(),
        "A3_payload_vs_class_hourly": a3_payload_vs_class_hourly(),
        "B_ct_conduct": b_ct_conduct(),
        "B6_east_river_plant_grain": b6_east_river_plant_grain(),
        "B7_steam_host_driver": b7_steam_host_driver(),
        "C_east_river_attribution": c_east_river_and_attribution(),
        "rule19_enumeration": rule19_enumeration(),
    }
    OUT.write_text(json.dumps(res, indent=1, sort_keys=False) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
