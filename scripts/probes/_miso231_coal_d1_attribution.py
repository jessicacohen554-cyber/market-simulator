"""miso-231 phase 0 — attribute the keeper's COAL D-1 ``cv_ratio`` regression,
at ZERO LP cost, to hours, to offer bands, and to the metric's own arithmetic.

Reads only committed artifacts: the keeper bundle ``miso230_ctdrag_seam_K``,
its predecessor ``miso220_nonsteamlift_B``, and the CAMPD bench D-1 itself
scores against. Nothing is solved and nothing is tuned.

Handoff item (3): miso-230 took MISO's COAL D-1 diurnal FAILs from one to four
(COAL_PRB ``cv_ratio`` 0.488 / 0.492 / 0.389, COAL_BIT-2024 0.387). They do not
gate — rule 18 ``[R-FORCED-BUDGET]``'s shape leg binds only above the forced
cap and COAL sits at ~0.3 % forced — but three are new and two sit within 0.012
of the 0.5 line. This probe diagnoses the OBJECT, never the residual.

The three questions, and where each is answered:

1. WHERE in the day did COAL move, and does the move sit inside D-1's off-peak
   window h0-14 (``D1_OFFPEAK_LAST_HOUR``)?  -> ``profile_delta_mw``, the
   h0-9 / h10-14 / h15-23 splits, and the two hold-one-half counterfactuals.
2. Which OFFER BAND gave up the energy — the fuel-free ``mustrun``, the
   take-or-pay ``committed`` band rule 19 ``[R-ONE-MECH]`` names as the
   reconciliation target, or the price-responsive ``econ*``/``peak`` bands?
   -> ``bands``.
3. What is ``cv_ratio`` actually measuring on this class?  -> ``flat_block``,
   which splits the off-peak level into the numerically-flat bands and the
   shape-bearing ones and re-scores the CV of each alone.

Usage: python3 scripts/probes/_miso231_coal_d1_attribution.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
import legitimacy_diagnostics as ld  # noqa: E402  (path shim above)

ROOT = Path(".")
KEEPER = ROOT / "results/calibration/miso230_ctdrag_seam_K"
PRED = ROOT / "results/calibration/miso220_nonsteamlift_B"
YEARS = (2023, 2024, 2025)
COAL = ("COAL_PRB", "COAL_BIT")
OFF = ld.D1_OFFPEAK_LAST_HOUR + 1  # off-peak profile points h0..14 inclusive
DRAG = (10, 21)  # data/raw/reference/miso_ct_netload_drag.json, end-exclusive
# Bands whose keeper profile is numerically flat over the off-peak window are
# measured, not assumed: FLAT_STD_MW is the threshold in MW of hour-of-day
# standard deviation below which a band carries no shape at all. Set an order
# of magnitude under the smallest shape-bearing band observed (econ* at
# 10-140 MW) and an order above float noise.
FLAT_STD_MW = 2.0
CANDIDATE_FLAT = ("mustrun", "committed")


def profile(mw: np.ndarray) -> np.ndarray:
    """Hour-of-day mean profile of an 8760-length hourly series."""
    return mw.reshape(-1, 24).mean(axis=0)


def cv(prof: np.ndarray) -> float:
    """D-1's statistic: CV of the profile over its off-peak points h0..14."""
    off = prof[:OFF]
    m = float(off.mean())
    return float(off.std() / m) if m > 1e-9 else 0.0


def band_profiles(bundle: Path, year: int, klass: str) -> dict[str, np.ndarray]:
    """Per-band P1 hour-of-day profiles for one class."""
    f = pd.read_parquet(bundle / "hourly" / f"class_band_hourly_{year}.parquet")
    f = f[(f["pass"] == "P1") & (f["klass"] == klass)]
    return {
        str(b): profile(g.sort_values("hour")["mw"].to_numpy(dtype=float))
        for b, g in f.groupby("band", observed=True)
    }


def actual_profiles(year: int) -> dict[str, np.ndarray]:
    """Per-class actual hour-of-day profiles from the CAMPD bench D-1 scores on."""
    out: dict[str, np.ndarray] = {}
    for p in ld.load_bench(ROOT, "MISO", year).values():
        g = str(p["group"])
        if not g.startswith("COAL"):
            continue
        v = np.asarray(p["mw"], dtype=float)
        acc = out.setdefault(g, np.zeros(8760))
        acc[: v.size] += v[:8760]
    return {k: profile(v) for k, v in out.items()}


def committed_d1_rows() -> dict[str, object]:
    """The authoritative D-1 COAL rows from both bundles' committed artifacts.

    The per-class reconstruction above pairs class TOTALS; D-1 itself pairs
    per-plant bench keys and so covers only CAMPD-metered plants. Carrying
    both lets a reader see that the two agree on every DELTA, which is what
    the attribution rests on, without conflating them.
    """
    out: dict[str, object] = {}
    for tag, bundle in (("pred", PRED), ("keeper", KEEPER)):
        rows = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
        out[tag] = [
            r
            for r in rows["diagnostics"]["D1"]["rows"]
            if str(r.get("class", "")).startswith("COAL")
        ]
    return out


def main() -> None:
    report: dict[str, object] = {
        "probe": "miso-231 phase 0 — COAL D-1 cv_ratio attribution (zero LP)",
        "keeper": KEEPER.name,
        "predecessor": PRED.name,
        "offpeak_window_hours": [0, ld.D1_OFFPEAK_LAST_HOUR],
        "drag_window_hours": list(DRAG),
        "d1_min_cv_ratio": ld.D1_MIN_CV_RATIO,
        "flat_std_threshold_mw": FLAT_STD_MW,
        "years": {},
    }
    years: dict[str, object] = {}
    for year in YEARS:
        act = actual_profiles(year)
        yr: dict[str, object] = {}
        for klass in COAL:
            if klass not in act:
                continue
            pa = act[klass]
            cva = cv(pa)
            row: dict[str, object] = {"actual_offpeak_cv": round(cva, 4)}
            sides: dict[str, dict[str, np.ndarray]] = {}
            for tag, bundle in (("pred", PRED), ("keeper", KEEPER)):
                bands = band_profiles(bundle, year, klass)
                sides[tag] = bands
                tot = sum(bands.values())
                flat_names = sorted(
                    b
                    for b in CANDIDATE_FLAT
                    if b in bands and float(bands[b][:OFF].std()) < FLAT_STD_MW
                )
                flat = (
                    sum(bands[b] for b in flat_names)
                    if flat_names
                    else np.zeros(24)
                )
                var = tot - flat
                cvm = cv(tot)
                row[tag] = {
                    "model_offpeak_cv": round(cvm, 4),
                    "cv_ratio": round(cvm / cva, 3) if cva > 1e-9 else None,
                    "offpeak_mean_mw": round(float(tot[:OFF].mean()), 1),
                    "measured_flat_bands": flat_names,
                    "flat_mean_mw": round(float(flat[:OFF].mean()), 1),
                    "flat_std_mw": round(float(flat[:OFF].std()), 2),
                    "flat_share_of_level": round(
                        float(flat[:OFF].mean() / tot[:OFF].mean()), 4
                    ),
                    "shapebearing_mean_mw": round(float(var[:OFF].mean()), 1),
                    "shapebearing_std_mw": round(float(var[:OFF].std()), 2),
                    "cv_of_shapebearing_alone": round(cv(var), 4),
                    "cv_ratio_shapebearing_alone": (
                        round(cv(var) / cva, 3) if cva > 1e-9 else None
                    ),
                    # The identity the whole diagnosis rests on: with a flat
                    # block contributing no std, the class CV collapses to the
                    # shape-bearing std over the TOTAL level.
                    "cv_identity_check": round(
                        float(var[:OFF].std() / tot[:OFF].mean()), 4
                    ),
                }
            pk, pp = sum(sides["keeper"].values()), sum(sides["pred"].values())
            delta = pk - pp
            row["profile_delta_mw"] = [round(float(x), 1) for x in delta]
            row["delta_h0_h9_mw"] = round(float(delta[0:10].sum()), 1)
            row["delta_h10_h14_mw"] = round(float(delta[10:15].sum()), 1)
            row["delta_h15_h23_mw"] = round(float(delta[15:24].sum()), 1)
            # Hold one half of the off-peak window at the predecessor and
            # re-score, isolating each half's contribution to the CV move.
            cf1 = pk.copy()
            cf1[10:15] = pp[10:15]
            cf2 = pk.copy()
            cf2[0:10] = pp[0:10]
            row["offpeak_cv_if_h10_h14_unchanged"] = round(cv(cf1), 4)
            row["offpeak_cv_if_h0_h9_unchanged"] = round(cv(cf2), 4)
            bands_out: dict[str, object] = {}
            for b in sorted(set(sides["keeper"]) | set(sides["pred"])):
                zk = sides["keeper"].get(b, np.zeros(24))
                zp = sides["pred"].get(b, np.zeros(24))
                d = zk - zp
                bands_out[b] = {
                    "pred_offpeak_mean_mw": round(float(zp[:OFF].mean()), 1),
                    "keeper_offpeak_mean_mw": round(float(zk[:OFF].mean()), 1),
                    "keeper_offpeak_std_mw": round(float(zk[:OFF].std()), 2),
                    "delta_h0_h9_mw": round(float(d[0:10].sum()), 1),
                    "delta_h10_h14_mw": round(float(d[10:15].sum()), 1),
                    "delta_h15_h23_mw": round(float(d[15:24].sum()), 1),
                }
            row["bands"] = bands_out
            yr[klass] = row

        k_ct = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        p_ct = pd.read_parquet(PRED / "hourly" / f"class_hourly_{year}.parquet")

        def _ct(f: pd.DataFrame) -> np.ndarray:
            s = f[(f["pass"] == "P1") & (f["klass"] == "CT_PEAKER")]
            return profile(s.sort_values("hour")["mw"].to_numpy(dtype=float))

        dct = _ct(k_ct) - _ct(p_ct)
        yr["ct_peaker_profile_delta_mw"] = [round(float(x), 1) for x in dct]
        yr["ct_peaker_delta_in_drag_window_mw"] = round(
            float(dct[DRAG[0] : DRAG[1]].sum()), 1
        )
        yr["ct_peaker_delta_outside_drag_window_mw"] = round(
            float(dct.sum() - dct[DRAG[0] : DRAG[1]].sum()), 1
        )
        years[str(year)] = yr
    report["years"] = years
    report["committed_d1_rows"] = committed_d1_rows()

    out = ROOT / "results/calibration/_miso231_coal_d1_attribution.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {out}\n")

    for year in YEARS:
        y = years[str(year)]
        print(f"=== {year} ===")
        print(
            f"  CT_PEAKER profile delta "
            f"{y['ct_peaker_delta_in_drag_window_mw']:+.0f} MW inside [10,21), "
            f"{y['ct_peaker_delta_outside_drag_window_mw']:+.0f} outside"
        )
        for klass in COAL:
            r = y.get(klass)
            if not r:
                continue
            k, p = r["keeper"], r["pred"]
            print(
                f"  {klass}: cv_ratio {p['cv_ratio']:.3f} -> {k['cv_ratio']:.3f}"
                f"   (actual off-peak CV {r['actual_offpeak_cv']:.4f})"
            )
            print(
                f"    profile delta  h0-9 {r['delta_h0_h9_mw']:+.0f}"
                f"  h10-14 {r['delta_h10_h14_mw']:+.0f}"
                f"  h15-23 {r['delta_h15_h23_mw']:+.0f} MW"
                f"   | CV if h10-14 held {r['offpeak_cv_if_h10_h14_unchanged']:.4f},"
                f" if h0-9 held {r['offpeak_cv_if_h0_h9_unchanged']:.4f}"
            )
            print(
                f"    FLAT {'+'.join(k['measured_flat_bands']) or 'none':<18}"
                f" {k['flat_mean_mw']:8.0f} MW = {100*k['flat_share_of_level']:5.1f} %"
                f" of level, std {k['flat_std_mw']:6.2f} MW"
            )
            print(
                f"    SHAPE-BEARING bands       {k['shapebearing_mean_mw']:8.0f} MW,"
                f" std {k['shapebearing_std_mw']:6.2f} MW"
                f"  -> their CV alone {k['cv_of_shapebearing_alone']:.4f}"
                f" = cv_ratio {k['cv_ratio_shapebearing_alone']:.2f}"
            )
            print(
                f"    identity  std(shape)/mean(total) = {k['cv_identity_check']:.4f}"
                f"  vs class CV {k['model_offpeak_cv']:.4f}"
            )
        print()

    print("=== committed D-1 COAL rows (authoritative), pred -> keeper ===")
    cd = report["committed_d1_rows"]
    idx = {(r["year"], r["class"]): r for r in cd["pred"]}
    n_r_up = n_cv_dn = 0
    for r in cd["keeper"]:
        q = idx.get((r["year"], r["class"]))
        if not q:
            continue
        n_r_up += r["profile_r"] > q["profile_r"]
        n_cv_dn += r["cv_ratio"] < q["cv_ratio"]
        print(
            f"  {r['year']} {r['class']:13} profile_r {q['profile_r']:.3f} ->"
            f" {r['profile_r']:.3f}   cv_ratio {q['cv_ratio']:.3f} ->"
            f" {r['cv_ratio']:.3f}   {q['verdict']} -> {r['verdict']}"
        )
    print(
        f"  profile_r IMPROVES in {n_r_up}/{len(cd['keeper'])} coal cells;"
        f" cv_ratio falls in {n_cv_dn}/{len(cd['keeper'])}."
    )


if __name__ == "__main__":
    main()
