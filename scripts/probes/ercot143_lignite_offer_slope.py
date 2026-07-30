"""ERCOT-143 Phase 2 — the measured lignite mid-band offer SLOPE: does it exist?

No LP, no solve, no parameter changed. The ERCOT-142 charter
(``docs/DIAGNOSIS-ercot142-lignite-shape-2026-07-30.md`` §8) pre-registered
Phase 2 as: re-measure the lignite offer curve on the CURRENT keeper, identify
the mid-band slope from the measured SCED TPO supply curve with **zero swept
parameters**, and — explicitly — **close the lane if no non-fitted
identification survives**. This probe is the measurement that decides it.

Four sections, each an independent test of whether the chartered mechanism has
a measured object behind it:

1. **MODEL** — the CURRENT ``ercot140_coal_peak_arm`` keeper's own lignite offer
   curve, captured at the LP seam (``apply_coal_tranches``), per plant, per
   tranche, for 2023/2024/2025. The ERCOT-142 §6 table is ercot135-vintage and
   is structure-only evidence; this is the re-measurement §8.1 required.
2. **MEASURED, PER PLANT** — the same 60-Day SCED ``Submitted TPO`` corpus that
   identified ERCOT-136/137/138/140, but resolved **per resource** instead of
   fleet-pooled, on ERCOT-136 ``section_b``'s verbatim B2 construction. This is
   the test the charter's fleet-level read never ran.
3. **HOUR COVERAGE** — what share of that corpus actually observes the hours the
   C7 defect lives in (h0-h8).
4. **DAM** — the 60-Day DAM ``QSE submitted Curve`` disclosure, which unlike the
   SCED probe-day subsets carries full 24-h, full-year, 2023-inclusive
   coverage: does the plant submit a priced energy curve there at all, and does
   it hold an AS award?

Usage::

    python scripts/probes/ercot143_lignite_offer_slope.py \
        --bundle results/calibration/ercot140_coal_peak_arm

``--skip-model`` runs sections 2-4 only (no fleet build, seconds instead of
minutes) — the sections that carry the adjudication.

Rule notes: measurement only (rules 13/14 ``[R-MEASURED]``/``[R-ACCURATE]`` —
measured conduct read as driver evidence, never fed back as an answer key),
ERCOT-scoped (rule 25 ``[R-ISO-SCOPE]``), training years 2023-2025 only
(rule 22 ``[R-HOLDOUT]``; the on-disk 2026 DAM files are never opened).
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from scripts.probes.ercot123_coal_sced_reach import (  # noqa: E402
    SUBSETS,
    TPO_MW,
    TPO_PR,
    load_sced,
)

YEARS = (2023, 2024, 2025)

#: EIA plant code -> ERCOT 60-Day disclosure ``Resource Name``s. The three
#: plants of the model's COAL_LIGNITE class (ERCOT-142 §2.3), plus the two
#: fleet plants that carry the charter's cited $17.5-$25 segment, kept as
#: named controls so the cross-plant reading is checkable rather than asserted.
LIGNITE_RES: dict[int, tuple[str, ...]] = {
    6180: ("OGSES_UNIT1A", "OGSES_UNIT2"),  # Oak Grove SES
    6183: ("SANMIGL_G1",),  # San Miguel
    7030: ("TNP_ONE_TNP_O_1", "TNP_ONE_TNP_O_2"),  # TNP One / Twin Oaks
}
PLANT_NAMES = {6180: "Oak Grove", 6183: "San Miguel", 7030: "Major Oak"}
CONTROL_RES = {
    "MLSES_UNIT1": "Martin Lake 1",
    "LEG_LEG_G1": "Limestone 1",
    "WAP_WAP_G5": "W A Parish 5",
}

#: ERCOT-136 ``FINE_GRID``-compatible price grid ($/MWh).
GRID: tuple[float, ...] = (0, 2, 4.5, 7.5, 10, 12.5, 15, 17.5, 20, 25, 30, 40, 100, 500)

#: The D-1 off-peak window's own boundary (``d1_offpeak_last_hour`` = 14) and
#: the ERCOT-142 §2.3 night window the defect is measured in.
D1_OFFPEAK_LAST = 14
NIGHT_LAST = 8

DAM_MW = [f"QSE submitted Curve-MW{k}" for k in range(1, 11)]
DAM_PR = [f"QSE submitted Curve-Price{k}" for k in range(1, 11)]
DAM_AS = [
    "RegUp Awarded",
    "RRSPFR Awarded",
    "RRSFFR Awarded",
    "RRSUFR Awarded",
    "NonSpin Awarded",
    "ECRSSD Awarded",
]
DAM_BASE = [
    "Delivery Date",
    "Hour Ending",
    "Resource Name",
    "HSL",
    "LSL",
    "Resource Status",
]


class _Captured(Exception):
    """Raised to abort the replay once the offer seam has been recorded."""


# --------------------------------------------------------------------------
# 1 — the MODEL side, on the CURRENT keeper
# --------------------------------------------------------------------------


def capture_model_offer(bundle: Path, year: int, scratch: Path) -> dict:
    """Capture the keeper's coal bid array at the seam the LP consumes.

    Patches the ``apply_coal_tranches`` copy imported into
    ``scripts.run_calibration`` (the live seam; ``market_sim.runner`` holds a
    second, dead copy — the ERCOT-135 ``capture_coal_offer_surface`` trap),
    calls the real implementation so every repricing mechanism fires, records
    the coal rows, then aborts before any LP matrix is built.
    """
    import os

    os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"
    from scripts import replay_keeper as rk
    from scripts import run_calibration as rc
    from scripts import run_calibration_full as rcf

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = scratch / str(year)

    real = rc.apply_coal_tranches
    box: dict = {}

    def _spy(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config=None):
        real(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config)
        rows = np.flatnonzero(
            np.array(
                [str(getattr(g, "fuel_type", "")) == "coal" for g in generators],
                dtype=bool,
            )
        )
        arr = np.asarray(mc, dtype=float)
        box.update(
            plant_code=np.array(
                [int(getattr(generators[g], "plant_code", 0) or 0) for g in rows]
            ),
            unit_id=[str(fleet_arrays.unit_ids[g]) for g in rows],
            pmax=np.asarray(fleet_arrays.pmax, dtype=float)[rows],
            heat_rate=np.asarray(fleet_arrays.heat_rate, dtype=float)[rows],
            fuel_price=np.asarray(fuel_prices, dtype=float)[rows].mean(axis=1),
            bid=arr[rows].mean(axis=1),
        )
        raise _Captured

    rc.apply_coal_tranches = _spy
    try:
        rcf.solve_and_persist(**kwargs)
    except _Captured:
        pass
    finally:
        rc.apply_coal_tranches = real
    if not box:
        raise RuntimeError(f"coal offer seam never reached for {year}")
    return box


def section_model(bundle: Path, scratch: Path) -> list[dict]:
    """1 — the CURRENT keeper's lignite offer curve, per plant, per tranche."""
    print(f"\n{'=' * 78}\n1 — MODEL: the CURRENT keeper's lignite offer curve")
    print(f"    bundle {bundle.name}  (ERCOT-142 §6 is ercot135-vintage; this supersedes it)")
    print("=" * 78)
    out: list[dict] = []
    for year in YEARS:
        cap = capture_model_offer(bundle, year, scratch)
        print(f"\n  --- {year} ---")
        for code, name in PLANT_NAMES.items():
            sel = [i for i in range(len(cap["unit_id"])) if int(cap["plant_code"][i]) == code]
            if not sel:
                continue
            tot = float(sum(cap["pmax"][i] for i in sel))
            order = sorted(sel, key=lambda i: cap["bid"][i])
            parts = " | ".join(
                f"{cap['unit_id'][i].rpartition('_')[2]} "
                f"{cap['pmax'][i] / tot * 100:.0f}%@${cap['bid'][i]:.2f}"
                for i in order
            )
            lo = float(min(cap["bid"][i] for i in sel))
            hi = float(max(cap["bid"][i] for i in sel))
            print(f"    {name:<11} spread ${hi - lo:>6.2f}   {parts}")
            out.append(
                {
                    "year": year,
                    "plant": name,
                    "plant_code": code,
                    "pmax_mw": round(tot, 1),
                    "bid_bot": round(lo, 2),
                    "bid_top": round(hi, 2),
                    "spread": round(hi - lo, 2),
                    "tranches": [
                        {
                            "tranche": cap["unit_id"][i].rpartition("_")[2],
                            "share": round(float(cap["pmax"][i]) / tot, 4),
                            "bid": round(float(cap["bid"][i]), 2),
                        }
                        for i in order
                    ],
                }
            )
    return out


# --------------------------------------------------------------------------
# 2 — the MEASURED side, PER PLANT (the test the fleet read never ran)
# --------------------------------------------------------------------------


def b2_grid(g: pd.DataFrame) -> dict[str, float]:
    """ERCOT-136 ``section_b`` B2, floored convention, verbatim — one group.

    ``supply(x) = clip(max{MW_k : price_k <= x}, LSL, HASL)`` with
    ``supply(-inf) = LSL`` and denominator ``HASL``. Reproduced rather than
    imported because ERCOT-136 pools by class; the whole point here is to
    resolve the same construction per resource.
    """
    P = g[TPO_PR].to_numpy(float)
    M = g[TPO_MW].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(M)
    hsl = g["HSL"].to_numpy(float)
    hasl = np.clip(g["HASL"].to_numpy(float), 0.0, hsl)
    lsl = np.clip(g["LSL"].to_numpy(float), 0.0, hsl)
    prev = lsl.copy()
    rec: dict[str, float] = {}
    for x in GRID:
        s = ok & (P <= x)
        sup = np.max(np.where(s, M, -np.inf), axis=1)
        sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), lsl, hasl)
        sup = np.maximum(sup, prev)
        rec[f"<={x:g}"] = float(sup.sum())
        prev = sup
    tot = float(hasl.sum())
    return {k: (v / tot if tot > 0 else float("nan")) for k, v in rec.items()}


def modal_curve(g: pd.DataFrame, top: int = 1) -> list[str]:
    """Return the most-submitted TPO curve(s) of a resource, as printable text."""
    P = g[TPO_PR].to_numpy(float)
    M = g[TPO_MW].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(M)
    keys = [
        tuple(np.round(np.sort(P[i][ok[i]]), 2)) for i in range(len(P)) if ok[i].any()
    ]
    if not keys:
        return ["(no curve submitted)"]
    out = []
    for key, n in Counter(keys).most_common(top):
        i = next(
            j
            for j in range(len(P))
            if ok[j].any() and tuple(np.round(np.sort(P[j][ok[j]]), 2)) == key
        )
        pr = np.round(P[i][ok[i]], 2)
        mw = np.round(M[i][ok[i]], 0)
        o = np.argsort(pr)
        pts = "  ".join(f"({mw[o][k]:.0f}MW @ ${pr[o][k]:g})" for k in range(len(o)))
        out.append(f"x{n:<5} {pts}")
    return out


def section_measured_perplant() -> list[dict]:
    """2 — the measured SCED TPO curve resolved PER RESOURCE."""
    print(f"\n{'=' * 78}\n2 — MEASURED, PER PLANT: the SCED TPO curve the charter read fleet-pooled")
    print("=" * 78)
    frames: dict[str, pd.DataFrame] = {}
    for tag, _year, _fam in SUBSETS:
        r = load_sced(tag)
        if r is not None:
            frames[tag] = r[0][r[0].cls == "COAL"]
    if not frames:
        print("  FATAL: no SCED subset on disk")
        return []

    pooled = pd.concat(frames.values())
    rows: list[dict] = []
    hdr = " ".join(f"{g:>6g}" for g in GRID)
    print("\n  All four subsets pooled — share of HASL offered at or below each price")
    print(f"  {'resource':<20}{'resh':>7}  {hdr}   pp[17.5,25]")
    named = {n: lbl for v, lbl in [(v, PLANT_NAMES[k]) for k, v in LIGNITE_RES.items()] for n in v}
    named.update(CONTROL_RES)
    for name in list(named) + ["__FLEET__"]:
        g = pooled if name == "__FLEET__" else pooled[pooled["Resource Name"] == name]
        if g.empty:
            continue
        grid = b2_grid(g)
        seg = grid["<=25"] - grid["<=17.5"]
        lbl = "COAL FLEET" if name == "__FLEET__" else f"{named[name]}"
        print(
            f"  {lbl:<20}{len(g):>7}  "
            + " ".join(f"{grid[f'<={x:g}']:>6.3f}" for x in GRID)
            + f"   {seg:>8.3f}"
        )
        rows.append(
            {
                "resource": name,
                "label": lbl,
                "res_intervals": int(len(g)),
                "grid": {k: round(v, 4) for k, v in grid.items()},
                "pp_17p5_to_25": round(float(seg), 4),
            }
        )

    print("\n  The submitted curve itself — modal TPO points per resource:")
    for name, lbl in named.items():
        g = pooled[pooled["Resource Name"] == name]
        if g.empty:
            continue
        P = g[TPO_PR].to_numpy(float)
        M = g[TPO_MW].to_numpy(float)
        ok = np.isfinite(P) & np.isfinite(M)
        print(f"    {lbl:<16} curve_present={ok.any(axis=1).mean():.3f}")
        for line in modal_curve(g):
            print(f"      {line}")
    return rows


# --------------------------------------------------------------------------
# 3 — can the corpus even see the defect window?
# --------------------------------------------------------------------------


def section_hour_coverage() -> dict:
    """3 — hour-of-day coverage of the SCED TPO corpus."""
    print(f"\n{'=' * 78}\n3 — HOUR COVERAGE: can the identifying corpus see the defect window?")
    print("=" * 78)
    total = np.zeros(24)
    per: dict[str, list[int]] = {}
    for tag, _year, _fam in SUBSETS:
        r = load_sced(tag)
        if r is None:
            continue
        c = r[0][r[0].cls == "COAL"].copy()
        c["hr"] = c["ts"].dt.hour
        cnt = c.groupby("hr").size().reindex(range(24), fill_value=0).to_numpy()
        total += cnt
        per[tag] = [int(v) for v in cnt]
        print(f"\n  {tag}   rows {int(cnt.sum()):>7}")
        print("    " + " ".join(f"{h:>4}" for h in range(24)))
        print("    " + " ".join(f"{v:>4}" for v in cnt))
    tot = float(total.sum())
    night = float(total[: NIGHT_LAST + 1].sum())
    offpk = float(total[: D1_OFFPEAK_LAST + 1].sum())
    print(
        f"\n  POOLED  h0-{NIGHT_LAST} (defect window) {night:.0f}/{tot:.0f} = {night / tot:.4f}"
        f"   h0-{D1_OFFPEAK_LAST} (D-1 off-peak) {offpk / tot:.4f}"
    )
    return {
        "per_subset": per,
        "pooled_night_share": round(night / tot, 4),
        "pooled_offpeak_share": round(offpk / tot, 4),
    }


# --------------------------------------------------------------------------
# 4 — the full-coverage instrument: does the plant offer into DAM at all?
# --------------------------------------------------------------------------


def section_dam() -> list[dict]:
    """4 — the 60-Day DAM ``QSE submitted Curve`` disclosure (24-h, 2023-25)."""
    print(f"\n{'=' * 78}\n4 — DAM: the full-24h, 2023-inclusive instrument")
    print("=" * 78)
    import pyarrow.parquet as pq

    names = {n: PLANT_NAMES[k] for k, v in LIGNITE_RES.items() for n in v}
    names.update(CONTROL_RES)
    rows: list[dict] = []
    for year in YEARS:
        files = sorted(
            glob.glob(
                str(
                    REPO
                    / "data/raw/ercot"
                    / f"60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{year}_*.parquet"
                )
            )
        )
        if not files:
            print(f"  {year}: no DAM disclosure on disk")
            continue
        parts = []
        for f in files:
            have = set(pq.ParquetFile(f).schema_arrow.names)
            cols = [c for c in DAM_BASE + DAM_MW + DAM_PR + DAM_AS if c in have]
            d = pd.read_parquet(f, columns=cols)
            d = d[d["Resource Name"].isin(names)]
            if len(d):
                parts.append(d)
        if not parts:
            continue
        d = pd.concat(parts, ignore_index=True)
        for c in [c for c in DAM_MW + DAM_PR + DAM_AS + ["HSL", "LSL"] if c in d.columns]:
            d[c] = pd.to_numeric(d[c], errors="coerce")
        for c in DAM_AS:
            if c not in d.columns:
                d[c] = 0.0
        d = d[d["Resource Status"].astype(str).str.upper().str.startswith("ON")]
        print(f"\n  --- {year} ---   online resource-hours {len(d)}")
        print(
            f"    {'plant':<13}{'resource':<18}{'n':>7}{'curve_present':>15}"
            f"{'AS>0 share':>12}{'AS_up mean MW':>15}"
        )
        for name, lbl in names.items():
            g = d[d["Resource Name"] == name]
            if g.empty:
                continue
            present = float(g[[c for c in DAM_MW if c in g.columns]].notna().any(axis=1).mean())
            asup = g[DAM_AS].fillna(0.0).sum(axis=1)
            print(
                f"    {lbl:<13}{name:<18}{len(g):>7}{present:>15.3f}"
                f"{float((asup > 0).mean()):>12.3f}{float(asup.mean()):>15.1f}"
            )
            rows.append(
                {
                    "year": year,
                    "resource": name,
                    "label": lbl,
                    "resource_hours": int(len(g)),
                    "dam_curve_present": round(present, 4),
                    "as_award_share": round(float((asup > 0).mean()), 4),
                    "as_up_mean_mw": round(float(asup.mean()), 2),
                }
            )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bundle",
        type=Path,
        default=REPO / "results/calibration/ercot140_coal_peak_arm",
        help="keeper bundle whose offer curve is re-measured (section 1)",
    )
    ap.add_argument(
        "--skip-model",
        action="store_true",
        help="skip section 1 (the fleet build); sections 2-4 carry the adjudication",
    )
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument(
        "--scratch",
        type=Path,
        default=REPO / "results/calibration/_ercot143_scratch",
        help="throwaway run_dir for the section-1 replay (never registered)",
    )
    args = ap.parse_args()

    print("=" * 78)
    print("ERCOT-143 Phase 2 — the measured lignite mid-band offer SLOPE")
    print("measurement only: no LP, no solve, no parameter changed")
    print("=" * 78)

    blob: dict = {"lane": "ercot143-lignite-offer-slope", "phase": 2, "no_lp": True}
    if not args.skip_model:
        args.scratch.mkdir(parents=True, exist_ok=True)
        blob["keeper_bundle"] = args.bundle.name
        blob["S1_model_offer"] = section_model(args.bundle, args.scratch)
    blob["S2_measured_perplant"] = section_measured_perplant()
    blob["S3_hour_coverage"] = section_hour_coverage()
    blob["S4_dam_participation"] = section_dam()

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(blob, indent=2, default=float))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
