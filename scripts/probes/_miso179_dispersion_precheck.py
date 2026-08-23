"""miso-179 — the NO-LP pre-checks for the across-unit offer-level dispersion
object: K-PRE-a / K-PRE-b / K-PRE-c, thresholds frozen in the committed PREREG.

PREREG ``PREREG-miso179-offer-level-dispersion-2026-08-23.md`` (committed and
pushed BEFORE this probe existed — the miso-176 discipline). All three checks
are computed and reported in full even if an earlier one fires; adjudication
happens after measurement, in the frozen order a -> b -> c.

Model side: the ``_miso156.model_year`` path via the ``_miso178`` wrapper
(bundle repointed to the keeper ``miso177_rho_B``, import shim included),
with its own V1/V4 validity gates required to PASS before anything else is
read. Book side: the SAME loader and gas reference the identification derive
used (imported from ``derive_miso_offer_level_dispersion``), so the two can
never diverge in population or normalization.

Frozen constructions (PREREG §4):

* **H\\*** — the 221 JJA-2025 hours with the highest six-carry-zone total
  demand (the keeper's own committed ``system_2025.parquet``, P1 rows).
* **Model offer basis** — ``mc_base[g, t]`` (the committed-instrument
  lineage's offer surface; the P1 startup-amortization markup is a DISCLOSED
  understatement whose bias runs toward PROCEEDING).
* **Model affected stack** — econ/peak tranches of the offer-curve classes
  (plant_group matching ``^(CC_|CT_|ST_GAS|COAL)``; unit_id suffix matching
  ``_(econ|peak)``), availability-masked, weights ``availcap``.
* **K-PRE-a KILL**: S_mod >= 0.5 x S_book(BOOK-ELIG), S = p90 - p10
  cap-weighted pooled over H\\*.
* **K-PRE-b KILL**: (b-1) eligible share of the BOOK-ALL mass above
  P_mod(h) < 1/3; (b-2) S_book(BOOK-ELIG) < 0.5 x S_book(BOOK-ALL).
* **K-PRE-c KILL**: static-repricing predicted C3a-2023 outside +/-10 %
  (predictor overstates movement in both directions — a pass is strong
  evidence, a fire is precautionary). 2024/2025 predictions REPORTED only.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only. Rule 13 ``[R-MEASURED]``: reads
committed artifacts and the curated conduct corpus; feeds nothing to any
solve.

Usage::

    cd <repo root> && uv run --no-project \\
      --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml --python 3.12 \\
      python scripts/probes/_miso179_dispersion_precheck.py
"""

from __future__ import annotations

import gc
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (
    str(REPO),
    str(REPO / "src"),
    str(REPO / "scripts" / "probes"),
    str(REPO / "scripts" / "data"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# The wrapper performs the miso-178 import shim + repoints BOTH module globals
# to the keeper bundle miso177_rho_B, and pins V1 targets to the measured-rho
# keeper's C3a. Importing it does NOT run its main().
import _miso178_c3a_decomposition as _m178  # noqa: E402
from derive_miso_offer_level_dispersion import (  # noqa: E402
    QUANTILE_GRID,
    gas_reference,
    load_year_base_rows,
    weighted_quantiles,
)

_m156 = _m178._m156
BUNDLE = _m178.BUNDLE
OUT = REPO / "results/calibration/_miso179_dispersion_precheck.json"
ARTIFACT = REPO / "data/raw/_validation-source/miso_offer_level_dispersion.json"

CARRY = list(_m156.CARRY)
YEARS = (2023, 2024, 2025)
N_TOP = 221  # top decile of the 2,208 JJA-2025 hours (PREREG §4)
JJA = (6, 7, 8)
RANK_EPS = 0.01  # $/MWh, the frozen <= P_mod + eps rank cut
QPOINTS = (0.10, 0.50, 0.90, 0.95, 0.99)

_AFFECTED_SUFFIX = re.compile(r"_(econ\w*|peak\w*)$")
_AFFECTED_CLASS = re.compile(r"^(CC_|CT_|ST_GAS|COAL)")


def carry_price_demand(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (T,) demand-weighted carry-zone P1 price and (T,) carry demand."""
    sysf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"].isin(CARRY))]
    price = sysf.pivot_table(index="hour", columns="zone", values="price")
    dem = sysf.pivot_table(index="hour", columns="zone", values="demand")
    price = price.reindex(columns=CARRY).to_numpy(float)
    dem = dem.reindex(columns=CARRY).to_numpy(float)
    p_lw = (price * dem).sum(axis=1) / dem.sum(axis=1)
    return p_lw, dem.sum(axis=1)


def affected_mask(mb: dict) -> np.ndarray:
    """The frozen affected-stack selector (PREREG §2 scope)."""
    ids = np.array([str(g.unit_id) for g in mb["fleet"]])
    cls = mb["labels"]
    suf = np.array([bool(_AFFECTED_SUFFIX.search(u)) for u in ids])
    grp = np.array([bool(_AFFECTED_CLASS.match(str(c))) for c in cls])
    return suf & grp


def qdict(values: np.ndarray, weights: np.ndarray) -> dict:
    """Cap-weighted p10/50/90/95/99 + spread, the frozen estimator."""
    q = weighted_quantiles(values, weights, np.array(QPOINTS))
    d = {f"p{int(100 * p)}": round(float(v), 4) for p, v in zip(QPOINTS, q)}
    d["spread_p90_p10"] = round(d["p90"] - d["p10"], 4)
    d["n"] = int(values.size)
    d["weight_gw"] = round(float(weights.sum()) / 1e3, 2)
    return d


def static_prediction(
    mb: dict, year: int, aff: np.ndarray, q_grid: np.ndarray, q_vec: np.ndarray
) -> dict:
    """K-PRE-c's frozen static-repricing predictor for one year."""
    p_mod, w_dem = carry_price_demand(year)
    T = p_mod.size
    mc = np.asarray(mb["mc_base"], float)[aff][:, :T]
    av = mb["availcap"][aff][:, :T]
    wmask = av > 0
    below = wmask & (mc <= (p_mod[None, :] + RANK_EPS))
    tot = np.where(wmask, av, 0.0).sum(axis=0)
    r_star = np.where(tot > 0, np.where(below, av, 0.0).sum(axis=0) / np.where(tot > 0, tot, 1.0), np.nan)
    gref = _m156.measured_gas_monthly(year)  # (12,) HH + MISO basis
    mo = pd.date_range(f"{year}-01-01", periods=T, freq="h").month.to_numpy() - 1
    p_new = np.interp(r_star, q_grid, q_vec) * gref[mo]
    dead = ~np.isfinite(r_star) | ~np.isfinite(p_new)
    p_new = np.where(dead, p_mod, p_new)
    bench = float(_m156.bench_actuals(year)["rt_lw"])
    lw_old = float((p_mod * w_dem).sum() / w_dem.sum())
    lw_new = float((p_new * w_dem).sum() / w_dem.sum())
    return {
        "bench_rt_lw": bench,
        "model_lw_asis": round(lw_old, 4),
        "model_lw_predicted": round(lw_new, 4),
        "c3a_asis_pct": round(100 * (lw_old / bench - 1), 4),
        "c3a_predicted_pct": round(100 * (lw_new / bench - 1), 4),
        "predicted_shift_pp": round(100 * (lw_new - lw_old) / bench, 4),
        "hours_no_affected_mass": int(dead.sum()),
        "r_star_mean": round(float(np.nanmean(r_star)), 4),
        "r_star_p90": round(float(np.nanquantile(r_star, 0.9)), 4),
    }


def main() -> dict:
    art = json.loads(ARTIFACT.read_text())
    q_grid = np.array(art["quantile_grid"], float)
    q_vec = np.array(art["pooled"]["quantiles_mmbtu_per_mwh"], float)
    assert np.all(np.diff(q_grid) > 0), "quantile grid must be increasing"

    # Identification-vs-instrument consistency: the derive's JJA G_ref must be
    # byte-equal to the miso-156 measured_gas_monthly construction.
    gref_d = gas_reference()
    for (y, m), v in gref_d.items():
        v156 = float(_m156.measured_gas_monthly(y)[m - 1])
        assert abs(v - v156) < 1e-9, f"G_ref divergence {y}-{m}: {v} vs {v156}"

    out: dict = {
        "session": "miso-179",
        "prereg": "PREREG-miso179-offer-level-dispersion-2026-08-23.md",
        "keeper": "2026-08-22-miso-177-rho-measured",
        "bundle": BUNDLE.name,
        "artifact": ARTIFACT.name,
        "n_top_hours": N_TOP,
    }

    cfg = _m156.keeper_config()

    # ---- 2025: validity gates, H*, K-PRE-a, K-PRE-b, prediction (report) ----
    mb = _m156.model_year(cfg, 2025)
    v4 = {
        "n_gen": len(mb["fleet"]),
        "published_n_gen": _m156.V4_NGEN[2025],
        "carry_zones": len(mb["carry_idx"]),
        "pass": bool(
            len(mb["fleet"]) == _m156.V4_NGEN[2025] and len(mb["carry_idx"]) == 6
        ),
    }
    v1 = _m156.v1_c3a_gate(mb, 2025)
    out["validity_2025"] = {"V4": v4, "V1": {k: v1[k] for k in ("c3a_pct", "published_c3a_pct", "delta_pp", "pass")}}
    if not (v1["pass"] and v4["pass"]):
        out["ABORT"] = "V1/V4 validity gate failed for 2025 — nothing adjudicated"
        OUT.write_text(json.dumps(out, indent=1))
        print(json.dumps(out, indent=1))
        return out

    p_mod_25, w_dem_25 = carry_price_demand(2025)
    mo25 = pd.date_range("2025-01-01", periods=p_mod_25.size, freq="h").month.to_numpy()
    jja_hours = np.where(np.isin(mo25, JJA))[0]
    order = np.argsort(-w_dem_25[jja_hours], kind="stable")
    hstar = np.sort(jja_hours[order[:N_TOP]])
    out["hstar"] = {
        "n": int(hstar.size),
        "demand_min_gw": round(float(w_dem_25[hstar].min() / 1e3), 3),
        "demand_max_gw": round(float(w_dem_25[hstar].max() / 1e3), 3),
        "months": {str(m): int(np.isin(mo25[hstar], [m]).sum()) for m in JJA},
    }

    # Congestion caveat (T-21 form): cross-carry-zone spread > $1 share on H*.
    sysf = pd.read_parquet(BUNDLE / "hourly/system_2025.parquet")
    sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"].isin(CARRY))]
    pz = sysf.pivot_table(index="hour", columns="zone", values="price").to_numpy(float)
    out["hstar"]["congested_share"] = round(
        float(np.mean((pz[hstar].max(axis=1) - pz[hstar].min(axis=1)) > 1.0)), 4
    )

    # Model affected-stack distribution on H* (K-PRE-a model side).
    aff = affected_mask(mb)
    out["affected_stack"] = {
        "n_tranches": int(aff.sum()),
        "classes": sorted(set(map(str, mb["labels"][aff]))),
        "capacity_gw": round(float(np.asarray(mb["arrays"].pmax)[aff].sum() / 1e3), 2),
    }
    mc = np.asarray(mb["mc_base"], float)[aff]
    av = mb["availcap"][aff]
    sub_mc = mc[:, hstar].ravel()
    sub_av = av[:, hstar].ravel()
    keep = sub_av > 0
    model_q = qdict(sub_mc[keep], sub_av[keep])
    out["K_PRE_a"] = {"model_mc_base": model_q}

    # Across-plant base-level cut (report-only, the G-5 grain).
    plant = np.array([int(g.plant_code) for g in mb["fleet"]])[aff]
    pv, pw = [], []
    for h in hstar:
        m_h, a_h = mc[:, h], av[:, h]
        ok = a_h > 0
        df = pd.DataFrame({"p": plant[ok], "mc": m_h[ok], "w": a_h[ok]})
        gmin = df.groupby("p").agg(mc=("mc", "min"), w=("w", "sum"))
        pv.append(gmin["mc"].to_numpy())
        pw.append(gmin["w"].to_numpy())
    out["K_PRE_a"]["model_across_plant_base"] = qdict(
        np.concatenate(pv), np.concatenate(pw)
    )

    # Book side on H* (both populations), 2025 DA.
    book = load_year_base_rows(2025)
    book = book[np.isin(book["hour"].to_numpy(), hstar)]
    b_all = book[book["available"].to_numpy() & (book["w_all"].to_numpy() > 0)]
    b_el = book[book["eligible"].to_numpy() & (book["w_elig"].to_numpy() > 0)]
    q_all = qdict(b_all["base_level"].to_numpy(), b_all["w_all"].to_numpy())
    q_el = qdict(b_el["base_level"].to_numpy(), b_el["w_elig"].to_numpy())
    out["K_PRE_a"]["book_all"] = q_all
    out["K_PRE_a"]["book_elig"] = q_el

    s_mod = model_q["spread_p90_p10"]
    s_elig = q_el["spread_p90_p10"]
    s_all = q_all["spread_p90_p10"]
    out["K_PRE_a"]["S_mod"] = s_mod
    out["K_PRE_a"]["S_book_elig"] = s_elig
    out["K_PRE_a"]["ratio_mod_over_book_elig"] = round(s_mod / s_elig, 4)
    out["K_PRE_a"]["KILL_fires"] = bool(s_mod >= 0.5 * s_elig)

    # K-PRE-b: eligibility of the dispersed mass above the model's margin.
    pmod_of_row = p_mod_25[book["hour"].to_numpy()]
    above = book["base_level"].to_numpy() > pmod_of_row
    avail = book["available"].to_numpy()
    elig = book["eligible"].to_numpy()
    mass_all_above = float(book["w_all"].to_numpy()[avail & above].sum())
    mass_elig_above = float(book["w_elig"].to_numpy()[avail & above & elig].sum())
    share_b1 = mass_elig_above / mass_all_above if mass_all_above > 0 else float("nan")
    mass_elig_total = float(book["w_elig"].to_numpy()[elig].sum())
    out["K_PRE_b"] = {
        "book_all_mass_above_pmod_gwh_grain": round(mass_all_above / 1e3, 2),
        "eligible_mass_above_pmod_gwh_grain": round(mass_elig_above / 1e3, 2),
        "b1_eligible_share_of_above_mass": round(share_b1, 4),
        "b1_KILL_fires": bool(share_b1 < (1.0 / 3.0)),
        "b2_S_book_elig": s_elig,
        "b2_S_book_all": s_all,
        "b2_ratio_elig_over_all": round(s_elig / s_all, 4),
        "b2_KILL_fires": bool(s_elig < 0.5 * s_all),
        "report_share_of_elig_mass_above_pmod": round(
            mass_elig_above / mass_elig_total, 4
        )
        if mass_elig_total > 0
        else None,
        "KILL_fires": bool(share_b1 < (1.0 / 3.0) or s_elig < 0.5 * s_all),
    }

    # K-PRE-c prediction for 2025 (REPORT only).
    out["K_PRE_c_report_2025"] = static_prediction(mb, 2025, aff, q_grid, q_vec)
    del mb, mc, av, book, b_all, b_el
    gc.collect()

    # ---- 2023: the KILL year ----
    mb23 = _m156.model_year(cfg, 2023)
    v1_23 = _m156.v1_c3a_gate(mb23, 2023)
    v4_23 = bool(len(mb23["fleet"]) == _m156.V4_NGEN[2023] and len(mb23["carry_idx"]) == 6)
    out["validity_2023"] = {
        "V1_pass": bool(v1_23["pass"]),
        "V1_c3a_pct": v1_23["c3a_pct"],
        "V4_pass": v4_23,
    }
    if not (v1_23["pass"] and v4_23):
        out["ABORT"] = "V1/V4 validity gate failed for 2023"
        OUT.write_text(json.dumps(out, indent=1))
        print(json.dumps(out, indent=1))
        return out
    aff23 = affected_mask(mb23)
    out["K_PRE_c"] = static_prediction(mb23, 2023, aff23, q_grid, q_vec)
    pred23 = out["K_PRE_c"]["c3a_predicted_pct"]
    out["K_PRE_c"]["KILL_fires"] = bool(abs(pred23) > 10.0)
    del mb23
    gc.collect()

    # ---- 2024: report-only prediction ----
    mb24 = _m156.model_year(cfg, 2024)
    v1_24 = _m156.v1_c3a_gate(mb24, 2024)
    v4_24 = bool(len(mb24["fleet"]) == _m156.V4_NGEN[2024] and len(mb24["carry_idx"]) == 6)
    out["validity_2024"] = {
        "V1_pass": bool(v1_24["pass"]),
        "V1_c3a_pct": v1_24["c3a_pct"],
        "V4_pass": v4_24,
    }
    if v1_24["pass"] and v4_24:
        out["K_PRE_c_report_2024"] = static_prediction(
            mb24, 2024, affected_mask(mb24), q_grid, q_vec
        )
    del mb24
    gc.collect()

    out["ADJUDICATION"] = {
        "K_PRE_a": "KILL" if out["K_PRE_a"]["KILL_fires"] else "CLEAR",
        "K_PRE_b": "KILL" if out["K_PRE_b"]["KILL_fires"] else "CLEAR",
        "K_PRE_c": "KILL" if out["K_PRE_c"]["KILL_fires"] else "CLEAR",
        "PROCEED_TO_BUILD": bool(
            not out["K_PRE_a"]["KILL_fires"]
            and not out["K_PRE_b"]["KILL_fires"]
            and not out["K_PRE_c"]["KILL_fires"]
        ),
    }

    OUT.write_text(json.dumps(out, indent=1))
    a, b, c = out["K_PRE_a"], out["K_PRE_b"], out["K_PRE_c"]
    print(f"K-PRE-a  S_mod {a['S_mod']:.2f} vs S_book_elig {a['S_book_elig']:.2f} "
          f"(ratio {a['ratio_mod_over_book_elig']:.3f}, kill@>=0.5) -> "
          f"{'KILL' if a['KILL_fires'] else 'CLEAR'}")
    print(f"K-PRE-b  b1 eligible share above margin {b['b1_eligible_share_of_above_mass']:.3f} "
          f"(kill@<0.333); b2 elig/all spread {b['b2_ratio_elig_over_all']:.3f} "
          f"(kill@<0.5) -> {'KILL' if b['KILL_fires'] else 'CLEAR'}")
    print(f"K-PRE-c  2023 predicted C3a {c['c3a_predicted_pct']:+.2f}% "
          f"(as-is {c['c3a_asis_pct']:+.2f}%, kill@|.|>10) -> "
          f"{'KILL' if c['KILL_fires'] else 'CLEAR'}")
    print(f"PROCEED_TO_BUILD = {out['ADJUDICATION']['PROCEED_TO_BUILD']}")
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
