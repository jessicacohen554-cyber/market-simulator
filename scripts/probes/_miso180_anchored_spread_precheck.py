"""miso-180 — anchor identification + NO-LP pre-checks for the anchored
SPREAD-ONLY across-unit dispersion object (K-a / K-b / K-c), every rule frozen
in the committed PREREG.

PREREG ``PREREG-miso180-anchored-spread-2026-08-23.md`` (committed and pushed
BEFORE this probe existed — the miso-176/177/179 discipline). One edited
descendant of ``_miso179_dispersion_precheck.py``: same wrapper imports, same
frozen constructions, same estimator.

The frozen anchor rule (PREREG §2, candidate (i)): with GRID the committed
199-point grid and the two K-PRE-a H\\* constructions evaluated on the full
grid, ``D(p) = Q_mod_H*(p) − Q_book_elig_H*(p)`` and **r_anchor = max{p in
GRID : D(p) >= 0}** — guards g1 (no crossing), g2 (> 0.975), g3 (<= 0.50) all
STOP-IDENTIFICATION. The anchor is computed ONCE; no variant is tried
(PREREG §2 anti-sweep clause).

Pre-checks (PREREG §4, adjudicated a -> b -> c after measurement):

* **K-a STOP**: rho_a = mean above-anchor rise of the model's H\\* curve over
  the eligible book's >= 0.5 (the model already carries half the object).
* **K-b KILL**: the anchored static-repricing predictor (K-PRE-c machinery,
  one line changed: raise-only above the anchor from the model's own monthly
  anchor level) lands 2023 outside +/-10 %.
* **K-c STOP -> I**: the same predictor's 2025 shift < +0.5 pp (inert).

Substrate verification (PREREG §4 V-gates, executed at the INTENT level —
see the manifest note in the output record): the refetched + curated book
must reproduce every committed miso-179 H\\* book statistic to its committed
rounding, and the curated DA row counts must equal the derive-recorded ones.
The whole-file manifest digest is NOT reproducible by construction (the
manifest embeds ``fetched_utc``), discovered at intake and recorded — the
content-level checks above are strictly stronger for what the anchor
consumes.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only. Rule 13 ``[R-MEASURED]``: reads
committed artifacts and the curated conduct corpus; feeds nothing to any
solve.

Usage::

    cd <repo root> && uv run --no-project \\
      --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml --python 3.12 \\
      python scripts/probes/_miso180_anchored_spread_precheck.py
"""

from __future__ import annotations

import gc
import hashlib
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
OUT = REPO / "results/calibration/_miso180_anchored_spread_precheck.json"
ARTIFACT = REPO / "data/raw/_validation-source/miso_offer_level_dispersion.json"
PRIOR = REPO / "results/calibration/_miso179_dispersion_precheck.json"
MANIFEST = REPO / "data/raw/miso-energy-offers/manifest.json"

#: PREREG §3/§4 frozen artifact digest.
ARTIFACT_SHA256 = "b4e723127de638068cfacae84dd78c911e5c9a322b8738671c0dc1895eefde28"
#: The derive-recorded whole-file manifest digest (NOT reproducible — see
#: the substrate block; recorded for the disclosure).
DERIVE_MANIFEST_SHA256 = (
    "825c9f7c696dabbc343f26923047670436948a2724e2b80e7cdcf9d5b16eb23e"
)

CARRY = list(_m156.CARRY)
YEARS = (2023, 2024, 2025)
N_TOP = 221  # top decile of the 2,208 JJA-2025 hours (frozen at miso-179)
JJA = (6, 7, 8)
RANK_EPS = 0.01  # $/MWh, the frozen <= P_mod + eps rank cut (K-PRE-c verbatim)
QPOINTS = (0.10, 0.50, 0.90, 0.95, 0.99)

#: PREREG §2 anchor guards.
ANCHOR_MAX = 0.975
ANCHOR_MIN = 0.50
#: PREREG §4 kill thresholds.
KA_STOP_RATIO = 0.5
KB_BAND_PCT = 10.0
KC_MIN_SHIFT_PP = 0.5

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
    """The frozen affected-stack selector (PREREG-miso179 §2 scope, verbatim)."""
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


def anchored_prediction(
    mb: dict,
    year: int,
    aff: np.ndarray,
    q_grid: np.ndarray,
    q_vec: np.ndarray,
    a: float,
) -> dict:
    """K-b/K-c's frozen anchored static-repricing predictor for one year.

    The K-PRE-c machinery verbatim, with the one line changed (PREREG §4):
    hours whose clearing rank exceeds the anchor are repriced RAISE-ONLY to
    ``max(P_mod, A_m + (Q(r*) − Q(a)) × G_ref)``; all other hours unchanged.
    """
    p_mod, w_dem = carry_price_demand(year)
    T = p_mod.size
    mc = np.asarray(mb["mc_base"], float)[aff][:, :T]
    av = mb["availcap"][aff][:, :T]
    wmask = av > 0
    below = wmask & (mc <= (p_mod[None, :] + RANK_EPS))
    tot = np.where(wmask, av, 0.0).sum(axis=0)
    r_star = np.where(
        tot > 0,
        np.where(below, av, 0.0).sum(axis=0) / np.where(tot > 0, tot, 1.0),
        np.nan,
    )
    gref = _m156.measured_gas_monthly(year)  # (12,) HH + MISO basis
    mo = pd.date_range(f"{year}-01-01", periods=T, freq="h").month.to_numpy() - 1

    # A_m: the graft's own monthly anchor level (PREREG §3 — pmax weights,
    # month-mean mc, the frozen weighted-quantile estimator).
    pmax_aff = np.asarray(mb["arrays"].pmax)[aff].astype(float)
    a_month = np.full(12, np.nan)
    for m in range(12):
        hrs = mo == m
        if not hrs.any():
            continue
        mc_m = mc[:, hrs].mean(axis=1)
        a_month[m] = float(weighted_quantiles(mc_m, pmax_aff, np.array([a]))[0])

    q_a = float(np.interp(a, q_grid, q_vec))
    q_rs = np.interp(r_star, q_grid, q_vec)
    rise = np.clip(q_rs - q_a, 0.0, None) * gref[mo]
    graft_target = a_month[mo] + rise
    exposed = np.isfinite(r_star) & (r_star > a) & np.isfinite(graft_target)
    p_new = np.where(exposed, np.maximum(p_mod, graft_target), p_mod)

    bench = float(_m156.bench_actuals(year)["rt_lw"])
    lw_old = float((p_mod * w_dem).sum() / w_dem.sum())
    lw_new = float((p_new * w_dem).sum() / w_dem.sum())
    dead = ~np.isfinite(r_star)
    # Per-month split of the predicted raise mass (pp of C3a), PREREG §4 K-c.
    dp = (p_new - p_mod) * w_dem
    month_pp = {
        str(m + 1): round(100 * float(dp[mo == m].sum()) / float(w_dem.sum()) / bench, 4)
        for m in range(12)
        if (mo == m).any() and abs(float(dp[mo == m].sum())) > 0
    }
    return {
        "bench_rt_lw": bench,
        "model_lw_asis": round(lw_old, 4),
        "model_lw_predicted": round(lw_new, 4),
        "c3a_asis_pct": round(100 * (lw_old / bench - 1), 4),
        "c3a_predicted_pct": round(100 * (lw_new / bench - 1), 4),
        "predicted_shift_pp": round(100 * (lw_new - lw_old) / bench, 4),
        "hours_no_affected_mass": int(dead.sum()),
        "hours_exposed_above_anchor": int(exposed.sum()),
        "mean_raise_on_exposed_usd": round(
            float((p_new - p_mod)[exposed].mean()) if exposed.any() else 0.0, 4
        ),
        "max_raise_usd": round(float((p_new - p_mod).max()), 4),
        "r_star_mean": round(float(np.nanmean(r_star)), 4),
        "r_star_p90": round(float(np.nanquantile(r_star, 0.9)), 4),
        "anchor_levels_monthly_usd": [
            round(float(x), 4) if np.isfinite(x) else None for x in a_month
        ],
        "predicted_raise_pp_by_month": month_pp,
    }


def main() -> dict:
    art_bytes = ARTIFACT.read_bytes()
    art_sha = hashlib.sha256(art_bytes).hexdigest()
    art = json.loads(art_bytes)
    q_grid = np.array(art["quantile_grid"], float)
    q_vec = np.array(art["pooled"]["quantiles_mmbtu_per_mwh"], float)
    assert np.all(np.diff(q_grid) > 0), "quantile grid must be increasing"
    assert art_sha == ARTIFACT_SHA256, f"artifact sha mismatch: {art_sha}"
    assert np.allclose(q_grid, QUANTILE_GRID), "artifact grid != frozen grid"

    prior = json.loads(PRIOR.read_text())

    # Identification-vs-instrument consistency (miso-179 verbatim).
    gref_d = gas_reference()
    for (y, m), v in gref_d.items():
        v156 = float(_m156.measured_gas_monthly(y)[m - 1])
        assert abs(v - v156) < 1e-9, f"G_ref divergence {y}-{m}: {v} vs {v156}"

    out: dict = {
        "session": "miso-180",
        "prereg": "PREREG-miso180-anchored-spread-2026-08-23.md",
        "keeper": "2026-08-22-miso-177-rho-measured",
        "bundle": BUNDLE.name,
        "artifact": ARTIFACT.name,
        "artifact_sha256": art_sha,
        "n_top_hours": N_TOP,
    }

    # ---- Substrate verification: manifest + curated rows (PREREG §4, at the
    # gate's INTENT level — the whole-file digest embeds fetched_utc and can
    # never reproduce across fetches; discovered at intake, disclosed here,
    # carried by the strictly stronger content-level checks below).
    man = json.loads(MANIFEST.read_text())
    man_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    statuses = [f["status"] for f in man["files"]]
    sub = {
        "manifest_sha256_refetch": man_sha,
        "manifest_sha256_derive_recorded": DERIVE_MANIFEST_SHA256,
        "manifest_digest_reproducible": False,
        "manifest_digest_note": (
            "manifest.json embeds fetched_utc, so whole-file digest equality "
            "across fetches is unsatisfiable by construction; the PREREG V-gate "
            "is executed at intent level: n_files + statuses + curated row "
            "counts + exact reproduction of every committed miso-179 H* book "
            "statistic (below)"
        ),
        "n_files": int(man["n_files"]),
        "n_files_expected": int(art["raw_manifest_n_files"]),
        "all_fetched": bool(all(s == "fetched" for s in statuses)),
    }
    from market_sim.config import paths  # noqa: E402  (probe-local import)
    import pyarrow.parquet as pq  # noqa: E402

    rows = {}
    for y in YEARS:
        p = paths.clean_path("energy-offers", iso="MISO", year=y, market="DA")
        rows[f"DA/{y}"] = int(pq.ParquetFile(p).metadata.num_rows)
    sub["clean_rows_refetch"] = rows
    sub["clean_rows_derive_recorded"] = art["clean_rows"]
    sub["rows_match"] = bool(rows == art["clean_rows"])
    sub["PASS"] = bool(
        sub["n_files"] == sub["n_files_expected"]
        and sub["all_fetched"]
        and sub["rows_match"]
    )
    out["substrate"] = sub
    if not sub["PASS"]:
        out["ABORT"] = "substrate verification failed — book is not miso-179's"
        OUT.write_text(json.dumps(out, indent=1))
        print(json.dumps(out["substrate"], indent=1))
        return out

    cfg = _m156.keeper_config()

    # ---- 2025: validity gates, H*, the ANCHOR, K-a, K-c report ----
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
    out["validity_2025"] = {
        "V4": v4,
        "V1": {k: v1[k] for k in ("c3a_pct", "published_c3a_pct", "delta_pp", "pass")},
    }
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
    # H* must reproduce the committed miso-179 block exactly (PREREG §4).
    ph = prior["hstar"]
    out["hstar"]["matches_committed"] = bool(
        out["hstar"]["n"] == ph["n"]
        and out["hstar"]["demand_min_gw"] == ph["demand_min_gw"]
        and out["hstar"]["demand_max_gw"] == ph["demand_max_gw"]
        and out["hstar"]["months"] == ph["months"]
    )

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
    model_q5 = qdict(sub_mc[keep], sub_av[keep])

    # Book side on H* (both populations), 2025 DA — miso-179 construction
    # verbatim; the 5-point dicts must REPRODUCE the committed record.
    book = load_year_base_rows(2025)
    book = book[np.isin(book["hour"].to_numpy(), hstar)]
    b_all = book[book["available"].to_numpy() & (book["w_all"].to_numpy() > 0)]
    b_el = book[book["eligible"].to_numpy() & (book["w_elig"].to_numpy() > 0)]
    q_all5 = qdict(b_all["base_level"].to_numpy(), b_all["w_all"].to_numpy())
    q_el5 = qdict(b_el["base_level"].to_numpy(), b_el["w_elig"].to_numpy())
    pmod_of_row = p_mod_25[book["hour"].to_numpy()]
    above = book["base_level"].to_numpy() > pmod_of_row
    avail = book["available"].to_numpy()
    elig = book["eligible"].to_numpy()
    mass_all_above = float(book["w_all"].to_numpy()[avail & above].sum())
    mass_elig_above = float(book["w_elig"].to_numpy()[avail & above & elig].sum())
    repro = {
        "model_mc_base": model_q5,
        "book_all": q_all5,
        "book_elig": q_el5,
        "kpreb_mass_all_above_gwh_grain": round(mass_all_above / 1e3, 2),
        "kpreb_mass_elig_above_gwh_grain": round(mass_elig_above / 1e3, 2),
    }
    pk = prior["K_PRE_a"]
    pb = prior["K_PRE_b"]
    repro["matches_committed"] = bool(
        model_q5 == pk["model_mc_base"]
        and q_all5 == pk["book_all"]
        and q_el5 == pk["book_elig"]
        and repro["kpreb_mass_all_above_gwh_grain"]
        == pb["book_all_mass_above_pmod_gwh_grain"]
        and repro["kpreb_mass_elig_above_gwh_grain"]
        == pb["eligible_mass_above_pmod_gwh_grain"]
    )
    out["substrate_reproduction"] = repro
    if not (repro["matches_committed"] and out["hstar"]["matches_committed"]):
        out["ABORT"] = (
            "H*/book substrate does not reproduce the committed miso-179 "
            "record — the corpus or machinery drifted; nothing adjudicated"
        )
        OUT.write_text(json.dumps(out, indent=1))
        print(json.dumps({k: out[k] for k in ("hstar", "substrate_reproduction")}, indent=1))
        return out

    # ---- THE ANCHOR (PREREG §2 frozen rule; computed ONCE) ----
    q_mod_grid = weighted_quantiles(sub_mc[keep], sub_av[keep], QUANTILE_GRID)
    q_book_grid = weighted_quantiles(
        b_el["base_level"].to_numpy(), b_el["w_elig"].to_numpy(), QUANTILE_GRID
    )
    d_vec = q_mod_grid - q_book_grid
    ge_idx = np.where(d_vec >= 0)[0]
    anchor: dict = {
        "grid_q_mod_usd": [round(float(x), 4) for x in q_mod_grid],
        "grid_q_book_elig_usd": [round(float(x), 4) for x in q_book_grid],
        "sign_changes": int(np.sum(np.diff((d_vec >= 0).astype(int)) != 0)),
    }
    if ge_idx.size == 0:
        anchor["guard"] = "g1: no rank with D>=0 — model under everywhere"
        out["anchor"] = anchor
        out["ADJUDICATION"] = {"STOP_IDENTIFICATION": "g1", "PROCEED_TO_BUILD": False}
        OUT.write_text(json.dumps(out, indent=1))
        print("STOP-IDENTIFICATION g1")
        return out
    ia = int(ge_idx.max())
    r_anchor = float(QUANTILE_GRID[ia])
    anchor.update(
        {
            "r_anchor": r_anchor,
            "anchor_grid_index": ia,
            "q_mod_at_anchor_usd": round(float(q_mod_grid[ia]), 4),
            "q_book_at_anchor_usd": round(float(q_book_grid[ia]), 4),
            "under_gridpoints_below_anchor": int(np.sum(d_vec[:ia] < 0)),
            "guard": None,
        }
    )
    if r_anchor > ANCHOR_MAX:
        anchor["guard"] = f"g2: r_anchor {r_anchor} > {ANCHOR_MAX} — no interior room"
    elif r_anchor <= ANCHOR_MIN:
        anchor["guard"] = f"g3: r_anchor {r_anchor} <= {ANCHOR_MIN} — premise broken"
    out["anchor"] = anchor
    if anchor["guard"]:
        out["ADJUDICATION"] = {
            "STOP_IDENTIFICATION": anchor["guard"],
            "PROCEED_TO_BUILD": False,
        }
        OUT.write_text(json.dumps(out, indent=1))
        print(f"STOP-IDENTIFICATION {anchor['guard']}")
        return out

    # ---- K-a: above-anchor spread ratio (PREREG §4) ----
    above_g = np.arange(QUANTILE_GRID.size) > ia
    num = float(np.mean(q_mod_grid[above_g] - q_mod_grid[ia]))
    den = float(np.mean(q_book_grid[above_g] - q_book_grid[ia]))
    ka: dict = {
        "mean_rise_model_usd": round(num, 4),
        "mean_rise_book_elig_usd": round(den, 4),
    }
    if den <= 0:
        ka["degenerate_book"] = True
        out["K_a"] = ka
        out["ADJUDICATION"] = {
            "STOP_IDENTIFICATION": "degenerate book tail (K-a denominator <= 0)",
            "PROCEED_TO_BUILD": False,
        }
        OUT.write_text(json.dumps(out, indent=1))
        print("STOP-IDENTIFICATION degenerate book")
        return out
    i95 = int(np.argmin(np.abs(QUANTILE_GRID - 0.95)))
    i99 = int(np.argmin(np.abs(QUANTILE_GRID - 0.99)))
    ka.update(
        {
            "ratio": round(num / den, 4),
            "STOP_fires": bool(num / den >= KA_STOP_RATIO),
            "rise_p95_model_usd": round(float(q_mod_grid[i95] - q_mod_grid[ia]), 4),
            "rise_p95_book_usd": round(float(q_book_grid[i95] - q_book_grid[ia]), 4),
            "rise_p99_model_usd": round(float(q_mod_grid[i99] - q_mod_grid[ia]), 4),
            "rise_p99_book_usd": round(float(q_book_grid[i99] - q_book_grid[ia]), 4),
            "continuity_spread_p90_p10_model": model_q5["spread_p90_p10"],
            "continuity_spread_p90_p10_book_elig": q_el5["spread_p90_p10"],
        }
    )
    out["K_a"] = ka

    # ---- K-c: 2025 reach (report + STOP threshold), computed while loaded ----
    out["K_c_2025"] = anchored_prediction(mb, 2025, aff, q_grid, q_vec, r_anchor)
    del mb, mc, av, book, b_all, b_el
    gc.collect()

    # ---- 2023: K-b (the KILL year) ----
    mb23 = _m156.model_year(cfg, 2023)
    v1_23 = _m156.v1_c3a_gate(mb23, 2023)
    v4_23 = bool(
        len(mb23["fleet"]) == _m156.V4_NGEN[2023] and len(mb23["carry_idx"]) == 6
    )
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
    out["K_b_2023"] = anchored_prediction(
        mb23, 2023, affected_mask(mb23), q_grid, q_vec, r_anchor
    )
    out["K_b_2023"]["KILL_fires"] = bool(
        abs(out["K_b_2023"]["c3a_predicted_pct"]) > KB_BAND_PCT
    )
    del mb23
    gc.collect()

    # ---- 2024: report-only prediction ----
    mb24 = _m156.model_year(cfg, 2024)
    v1_24 = _m156.v1_c3a_gate(mb24, 2024)
    v4_24 = bool(
        len(mb24["fleet"]) == _m156.V4_NGEN[2024] and len(mb24["carry_idx"]) == 6
    )
    out["validity_2024"] = {
        "V1_pass": bool(v1_24["pass"]),
        "V1_c3a_pct": v1_24["c3a_pct"],
        "V4_pass": v4_24,
    }
    if v1_24["pass"] and v4_24:
        out["K_c_report_2024"] = anchored_prediction(
            mb24, 2024, affected_mask(mb24), q_grid, q_vec, r_anchor
        )
    del mb24
    gc.collect()

    kc_shift = out["K_c_2025"]["predicted_shift_pp"]
    out["K_c_2025"]["STOP_fires"] = bool(kc_shift < KC_MIN_SHIFT_PP)
    out["ADJUDICATION"] = {
        "r_anchor": r_anchor,
        "K_a": "STOP" if out["K_a"]["STOP_fires"] else "CLEAR",
        "K_b": "KILL" if out["K_b_2023"]["KILL_fires"] else "CLEAR",
        "K_c": "STOP_INERT" if out["K_c_2025"]["STOP_fires"] else "CLEAR",
        "PROCEED_TO_BUILD": bool(
            not out["K_a"]["STOP_fires"]
            and not out["K_b_2023"]["KILL_fires"]
            and not out["K_c_2025"]["STOP_fires"]
        ),
    }

    OUT.write_text(json.dumps(out, indent=1))
    a_, b_, c_ = out["K_a"], out["K_b_2023"], out["K_c_2025"]
    print(f"ANCHOR  r_anchor = {r_anchor} (guards clear; sign changes "
          f"{anchor['sign_changes']}, model@a {anchor['q_mod_at_anchor_usd']}, "
          f"book@a {anchor['q_book_at_anchor_usd']})")
    print(f"K-a  mean above-anchor rise model {a_['mean_rise_model_usd']:.2f} vs "
          f"book {a_['mean_rise_book_elig_usd']:.2f} (ratio {a_['ratio']:.3f}, "
          f"stop@>=0.5) -> {'STOP' if a_['STOP_fires'] else 'CLEAR'}")
    print(f"K-b  2023 predicted C3a {b_['c3a_predicted_pct']:+.2f}% "
          f"(as-is {b_['c3a_asis_pct']:+.2f}%, kill@|.|>10, "
          f"{b_['hours_exposed_above_anchor']} exposed h) -> "
          f"{'KILL' if b_['KILL_fires'] else 'CLEAR'}")
    print(f"K-c  2025 predicted shift {c_['predicted_shift_pp']:+.3f} pp "
          f"(stop@<+0.5; {c_['hours_exposed_above_anchor']} exposed h, "
          f"mean raise ${c_['mean_raise_on_exposed_usd']:.2f}) -> "
          f"{'STOP_INERT' if c_['STOP_fires'] else 'CLEAR'}")
    print(f"PROCEED_TO_BUILD = {out['ADJUDICATION']['PROCEED_TO_BUILD']}")
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
