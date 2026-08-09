"""miso-147 Q1/Q4 — dispatch composition per stratum, model vs actual (PREREG §4.1/§4.2).

Pair A: model sidecar (all 17 klasses + storage, NET, incl. the 17.2 GW import
tranches) vs EIA-930 MISO BA by fuel (NET, full universe; imports live in
-interchange). Pair B: model fossil classes vs CAMPD families (NET via the
pipeline's parasitic factors; fossil subset, unit counts both sides). Every row
carries MW, delta, own-side shares and its universe tag; the per-stratum
BA-identity residual is the Pair-A noise floor. Strata are never pooled.

Adjudicates PREREG P-1 (materiality, S1-2025), P-4 (2025-specificity) and P-7
(S3 sign echo, reported-only). Writes
``results/calibration/_miso147_composition.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _miso147_strata import (  # noqa: E402
    E930_KEY,
    FAMILY_TO_KLASSES,
    FAMILY_930_FUEL,
    MODEL_BUCKETS,
    REPO,
    YEARS,
    bucket_series,
    campd_family_hourly,
    campd_units,
    c3a_weight,
    e930,
    e930_demand,
    family_parasitic_factor,
    floor_for,
    hygiene,
    parasitic_map,
    sidecar_pivot,
    storage_net,
    strata,
    wmean,
)

OUT = REPO / "results" / "calibration" / "_miso147_composition.json"


def pair_a(year: int, s: dict, piv, bench: dict, dem930: np.ndarray, w: np.ndarray) -> dict:
    """Pair A — model buckets vs EIA-930, per stratum (NET, full universe).

    On MISO's own 930 fold (PREREG §4.1, adjusted to the BA's reporting,
    verified at run time): oil -> other, pumped storage -> hydro, battery
    reported only from 2025.
    """
    sto_ps = storage_net(year, ("pumped_storage",))
    sto_bat = storage_net(year, ("li_ion",))
    has_bat = "battery" in bench
    out: dict = {}
    for sname, mask in s["masks"].items():
        rows = {}
        model_rows: dict[str, float] = {}
        for b, kl in MODEL_BUCKETS.items():
            model_rows[b] = wmean(bucket_series(piv, kl), w, mask)
        model_rows["gas_total"] = model_rows["gas_merchant"] + model_rows["gas_chp"]
        model_rows["hydro_ps"] = model_rows.pop("hydro") + wmean(sto_ps, w, mask)
        model_rows["battery"] = wmean(sto_bat, w, mask)
        actual_rows = {
            "coal": wmean(bench["coal"], w, mask),
            "gas_total": wmean(bench["gas"], w, mask),
            "nuclear": wmean(bench["nuclear"], w, mask),
            "wind": wmean(bench["wind"], w, mask),
            "solar": wmean(bench["solar"], w, mask),
            "hydro_ps": wmean(bench["hydro"], w, mask),
            "other_oil_bio": wmean(bench["other"], w, mask),
            "net_import": wmean(-bench["interchange"], w, mask),
            "battery": wmean(bench["battery"], w, mask) if has_bat else None,
        }
        m_tot = sum(
            v for k, v in model_rows.items() if k not in ("gas_merchant", "gas_chp")
        )
        a_tot = sum(v for v in actual_rows.values() if v is not None)
        noise = wmean(np.abs(bench["net_gen"] - dem930 - bench["interchange"]), w, mask)
        for b in actual_rows:
            m, a = model_rows[b], actual_rows[b]
            if a is None:  # 930 has no series (MISO battery pre-2025): model-only row
                rows[b] = {"model_mw": round(m, 1), "actual_mw": None,
                           "note": "no EIA-930 series for this BA-year"}
                continue
            d = m - a
            rows[b] = {
                "model_mw": round(m, 1),
                "actual_mw": round(a, 1),
                "delta_mw": round(d, 1),
                "model_share": round(m / m_tot, 4) if m_tot else None,
                "actual_share": round(a / a_tot, 4) if a_tot else None,
                "floor_mw": round(floor_for(a), 1),
                "material": bool(abs(d) >= floor_for(a)),
                "below_noise_floor": bool(abs(d) < noise),
            }
        rows["gas_merchant_model_only"] = {"model_mw": round(model_rows["gas_merchant"], 1)}
        rows["gas_chp_model_only"] = {"model_mw": round(model_rows["gas_chp"], 1)}
        out[sname] = {
            "rows": rows,
            "model_total_mw": round(m_tot, 1),
            "actual_total_mw": round(a_tot, 1),
            "demand_control": {
                "model_sidecar_demand_mw": round(wmean(w, np.ones_like(w), mask), 1),
                "e930_demand_mw": round(wmean(dem930, w, mask), 1),
            },
            "ba_identity_noise_floor_mw": round(noise, 1),
            "n_hours": int(mask.sum()),
            "universe": (
                "model: keeper P1 all klasses incl. import tranches + storage (NET) | "
                "actual: EIA-930 MISO BA net gen by fuel + (-interchange) (NET)"
            ),
        }
    return out


def pair_b(year: int, s: dict, piv, bench: dict, w: np.ndarray) -> dict:
    """Pair B — model fossil classes vs CAMPD families (NET), per stratum."""
    units, meta = campd_units(year)
    factors = parasitic_map()
    fam_net = campd_family_hourly(units, "net", factors)
    fam_pf = family_parasitic_factor(units, factors)
    p99 = units.groupby(["family", "unit"])["gross"].quantile(0.99)
    on_units = units[units["gross"] > 0]
    out: dict = {"campd_meta": meta, "family_parasitic_factor": {k: round(v, 4) for k, v in fam_pf.items()}}
    for sname, mask in s["masks"].items():
        hrs = set(np.nonzero(mask)[0].tolist())
        rows = {}
        for fam, kl in FAMILY_TO_KLASSES.items():
            m = wmean(bucket_series(piv, kl), w, mask)
            a = wmean(fam_net[fam], w, mask)
            d = m - a
            n_act = int(
                on_units.loc[
                    (on_units["family"] == fam) & on_units["hoy"].isin(hrs), "unit"
                ].nunique()
            )
            cov_930 = wmean(bench[FAMILY_930_FUEL[fam]], w, mask)
            rows[fam] = {
                "model_mw": round(m, 1),
                "campd_net_mw": round(a, 1),
                "delta_mw": round(d, 1),
                "floor_mw": round(floor_for(a), 1),
                "material": bool(abs(d) >= floor_for(a)),
                "campd_units_on_in_stratum": n_act,
                "campd_sum_p99_gross_gw": round(float(p99.loc[fam].sum()) / 1e3, 3),
                "coverage_vs_930_fuel": round(a / cov_930, 4) if cov_930 else None,
            }
        out[sname] = {
            "rows": rows,
            "n_hours": int(mask.sum()),
            "universe": (
                "model: keeper P1 fossil klasses (NET) | actual: CAMPD MISO fossil units "
                "(GROSS x parasitic -> NET); imports/non-fossil OUTSIDE this universe"
            ),
        }
    del units
    return out


def adjudicate(res: dict) -> dict:
    """P-1 / P-4 / P-7 verdicts from the composition tables (PREREG §5)."""
    s1_25 = res["pair_B"]["2025"]["S1"]["rows"]
    a1_25 = res["pair_A"]["2025"]["S1"]["rows"]
    # P-1: materiality on BOTH pairs where the bucket exists (fossil buckets).
    mat_b = {f: r for f, r in s1_25.items() if r["material"]}
    # Pair-A fossil buckets are coal and gas_total (oil folds into other on
    # MISO's 930 and cannot be isolated on the actual side).
    fossil_a = {"coal": a1_25["coal"], "gas_total": a1_25["gas_total"]}
    mat_a = {b: r for b, r in fossil_a.items() if r["material"] and not r["below_noise_floor"]}
    p1_pass = bool(mat_b) and bool(mat_a)
    largest = max(s1_25, key=lambda f: abs(s1_25[f]["delta_mw"])) if s1_25 else None
    # any stratum materiality (for the charter close branch: immaterial EVERYWHERE)
    any_material = False
    for y in map(str, YEARS):
        for sname, blk in res["pair_B"][y].items():
            if sname in ("campd_meta", "family_parasitic_factor"):
                continue
            if any(r["material"] for r in blk["rows"].values()):
                any_material = True
    # P-4: 2025-specificity per material 2025 bucket
    p4 = {}
    for fam, r in mat_b.items():
        d25 = abs(r["delta_mw"])
        d23 = abs(res["pair_B"]["2023"]["S1"]["rows"][fam]["delta_mw"])
        d24 = abs(res["pair_B"]["2024"]["S1"]["rows"][fam]["delta_mw"])
        p4[fam] = {
            "abs_delta_2023": d23, "abs_delta_2024": d24, "abs_delta_2025": d25,
            "pass": bool(d23 <= 0.5 * d25 and d24 <= 0.5 * d25),
        }
    # P-7 (reported, never gating): S3 sign echo of the two largest S1 deltas
    top2 = sorted(s1_25, key=lambda f: -abs(s1_25[f]["delta_mw"]))[:2]
    s3_25 = res["pair_B"]["2025"]["S3"]["rows"]
    p7 = {
        f: {
            "s1_delta": s1_25[f]["delta_mw"],
            "s3_delta": s3_25[f]["delta_mw"],
            "sign_match": bool(np.sign(s1_25[f]["delta_mw"]) == np.sign(s3_25[f]["delta_mw"])),
        }
        for f in top2
    }
    return {
        "P1": {
            "pass": p1_pass,
            "material_families_S1_2025": {f: s1_25[f]["delta_mw"] for f in mat_b},
            "material_buckets_pairA_S1_2025": {b: mat_a[b]["delta_mw"] for b in mat_a},
            "largest_gap_family": largest,
            "any_material_any_stratum": any_material,
        },
        "P4": {"per_family": p4, "pass": bool(p4) and all(v["pass"] for v in p4.values())},
        "P7_reported_only": p7,
    }


def run() -> dict:
    hygiene()
    res: dict = {"session": "miso-147", "pair_A": {}, "pair_B": {}}
    for year in YEARS:
        s = strata(year)
        piv = sidecar_pivot(year)
        bench = e930(year)
        dem = e930_demand(year)
        w = c3a_weight(year)
        res["pair_A"][str(year)] = pair_a(year, s, piv, bench, dem, w)
        res["pair_B"][str(year)] = pair_b(year, s, piv, bench, w)
        res["pair_A"][str(year)]["S1_thr_usd"] = s["S1_thr_usd"]
    res["adjudication"] = adjudicate(res)
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    adj = r["adjudication"]
    print("P-1:", "PASS" if adj["P1"]["pass"] else "FAIL",
          "| material S1-2025 (Pair B):", adj["P1"]["material_families_S1_2025"],
          "| largest:", adj["P1"]["largest_gap_family"])
    print("P-4:", "PASS" if adj["P4"]["pass"] else "FAIL", adj["P4"]["per_family"])
    print("P-7 (reported):", adj["P7_reported_only"])
    print(f"-> {OUT}")
