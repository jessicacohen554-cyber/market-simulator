"""miso-128 probe — what MISO's 2025-only C7 ``COAL_PRB`` failure actually is.

Executes ``results/calibration/PREREG-miso128-c7-2025-diurnal-organization-2026-08-04.md``
exactly as pre-registered. **NO LP IS SOLVED.** Every dispatch number is read
from committed artifacts:

* ``frontend/data/backcast/bench/MISO/<year>.json.gz`` — the committed CAMPD
  bench, per-plant ``campd``, which is D-1's own actual side.
* ``frontend/data/backcast/runs/2026-08-04-miso-127-onlinepmin.js`` — the
  KEEPER's registered payload, per-plant model dispatch ``m``, which is D-1's
  own model side when no ``dispatch/`` parquet is present.
* ``results/calibration/miso127_onlinepmin_B/hourly/class_hourly_<year>.parquet``
  — the keeper's UNQUANTIZED P1 class aggregate, carried as the pre-registered
  second grain (P2) on the payload's uint8 encoding.
* ``results/calibration/miso127_onlinepmin_B/legitimacy_diagnostics.json`` — the
  committed gated statistic the construction must reproduce (P1).

The measurement answers miso-127 §5's named successor. C7 ``COAL_PRB`` is
MISO's sole failing criterion and now fails in 2025 alone (cv_ratio 0.347
against the 0.5 gate) in the year whose *actual* off-peak CV is also lowest.
The pre-registration's reading R is that this is not a new 2025 defect but the
2025 projection of a standing, year-invariant defect in ONE dimension — the
hour-of-day organisation of MISO coal's off-peak output — through a ratio-form
gate whose denominator fell for a driver (gas +61 %) the model reproduces.

The gated statistic factors exactly:

    cv_ratio = R_tot x R_dfrac x R_level

with ``dfrac`` the share of a series' off-peak dispersion that is diurnally
organised, ``R_tot`` the total-dispersion ratio, and ``R_level`` the inverse
level ratio. P5 tests whether 2025 is a single-factor move.

P9 additionally adjudicates, at two grains and with no solve, whether the one
lever the session brief names — ``coal_tranche_1/2/3_frac``, the ERCOT-fitted
step sizes carried as open issue #1336 — is reachable **at all** on MISO's own
CAMPD-binned solve path. Grain 2 assembles the real MISO 2025 dispatch fleet
twice, at HEAD, under the keeper's own config with the fractions perturbed, and
compares the resulting ``pmax_mw`` and ``fuel_fracs`` vectors elementwise.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only — MISO holds no ``complete`` marker, so
no out-of-training year is solved, scored or read. Rule 15: no run is produced,
so there is nothing to register.

Usage::

    python scripts/probes/_miso128_c7_diurnal_organization.py [--skip-grain2]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import scripts.legitimacy_diagnostics as LD  # noqa: E402

#: the designated MISO keeper this measurement is taken on.
KEEPER_RUN = "2026-08-04-miso-127-onlinepmin"
KEEPER_BUNDLE = REPO / "results/calibration/miso127_onlinepmin_B"

YEARS = (2023, 2024, 2025)
_T = 8760

#: D-1's own off-peak window and gate, imported rather than restated so the
#: probe cannot drift from the scorer (rule 5 [R-NO-MAGIC]).
OFF_LAST = LD.D1_OFFPEAK_LAST_HOUR
OFF = np.arange(24) <= OFF_LAST
HOD = np.tile(np.arange(24), 365)
OFF_HOURS = np.isin(HOD, np.arange(OFF_LAST + 1))
GATE = LD.D1_MIN_CV_RATIO

#: the target class and the two control classes (PREREG P8).
TARGET = "COAL_PRB"
CONTROLS = ("COAL_BIT", "COAL_LIGNITE")

#: PREREG bars, all declared before measurement.
P1_TOL = 0.02  # reproduction of the committed cv_ratio
P2_MIN_R = 0.98  # payload-vs-parquet hour-of-day profile correlation
P2_REL_TOL = 0.10  # payload-vs-parquet std/mean agreement, relative
P3_MAX_NOISE_FRAC = 0.05  # quantization bound as a share of the flat threshold
P4_REL_TOL = 1e-6  # exactness of the three-factor decomposition
P5_DFRAC_DROP = 0.80  # R_dfrac(2025) must be below this x R_dfrac(2024)
P6_TOL = 1e-9  # non-increasing, exact
P7_STABLE = 0.10  # allowed drift in the non-diurnal ratio across years
FLAT_THRESHOLD = 0.01  # off-peak profile std below 1 % of nameplate = "flat"

#: PREREG P9 grain 2: a materially different split of the same total capacity.
#: Chosen to move every tranche and to keep the fractions summing to 1.0, so a
#: null cannot be explained by a degenerate perturbation.
TRANCHE_PERTURB = {
    "coal_tranche_1_frac": 0.10,
    "coal_tranche_2_frac": 0.15,
    "coal_tranche_3_frac": 0.75,
}

#: the keeper's own measured gas price path, read from its committed flags. It
#: sizes nothing and no parameter is fitted to it (PREREG KILL-4).
GAS_PRICE_FLAG = "gas_prices"


# ---------------------------------------------------------------------------
# artifact access
# ---------------------------------------------------------------------------


def load_sides(year: int, sidecar: dict) -> tuple[dict, dict]:
    """Return ``(bench, model_plants)`` for one year, D-1's own two sides."""
    bench = LD.load_bench(REPO, "MISO", year)
    return bench, LD.load_payload_plants(REPO, sidecar, year, bench)


def matched_keys(bench: dict, model: dict, klass: str) -> list[str]:
    """Return the bench keys of ``klass`` present on BOTH sides.

    Matching is D-1's own convention (``run_d1`` intersects the two class maps),
    and it is what removes coverage bias: a plant the model carries with no
    bench counterpart would otherwise read as pure model amplitude.
    """
    return sorted(
        k
        for k in bench
        if bench[k]["group"] == klass and k in model and bench[k]["npl"] > 0.0
    )


def class_series(keys: list[str], get) -> np.ndarray:
    """Sum a per-plant accessor over ``keys`` into one 8760 class series."""
    out = np.zeros(_T)
    for k in keys:
        out += np.asarray(get(k), float)[:_T]
    return out


# ---------------------------------------------------------------------------
# the decomposition
# ---------------------------------------------------------------------------


def decompose(model: np.ndarray, actual: np.ndarray) -> dict:
    """Factor D-1's gated ``cv_ratio`` into dispersion x organisation x level.

    ``cv_ratio = R_tot x R_dfrac x R_level`` where, per side,
    ``tot_std`` is the standard deviation of the raw hourly series over the
    off-peak hours, ``prof_std`` that of the hour-of-day mean profile over
    h0-``D1_OFFPEAK_LAST_HOUR``, and ``dfrac = prof_std / tot_std`` the share of
    off-peak dispersion that is diurnally organised. The identity is exact:
    ``cv = prof_std / mean = (tot_std x dfrac) / mean``.
    """
    out: dict = {}
    for lbl, s in (("model", model), ("actual", actual)):
        prof = s.reshape(-1, 24).mean(axis=0)
        out[lbl] = {
            "mean": float(prof[OFF].mean()),
            "prof_std": float(prof[OFF].std()),
            "tot_std": float(s[OFF_HOURS].std()),
            "cv": float(prof[OFF].std() / prof[OFF].mean()),
            "dfrac": float(prof[OFF].std() / s[OFF_HOURS].std()),
            "profile": [round(float(v), 1) for v in prof],
        }
    m, a = out["model"], out["actual"]
    out["R_tot"] = m["tot_std"] / a["tot_std"]
    out["R_dfrac"] = m["dfrac"] / a["dfrac"]
    out["R_level"] = a["mean"] / m["mean"]
    out["cv_ratio"] = m["cv"] / a["cv"]
    out["product"] = out["R_tot"] * out["R_dfrac"] * out["R_level"]
    return out


def online_day_stats(bench: dict, model: dict, keys: list[str]) -> dict:
    """Per-plant off-peak stats restricted to FULLY-ONLINE days.

    A day counts when every off-peak hour is above 5 % of nameplate on that
    side, which removes outage on/off from both sides and isolates the
    *loading* decision — the dimension the C7 gate scores. Capacity-weighted.
    """
    out: dict = {}
    for lbl, get in (
        ("actual", lambda k: bench[k]["mw"]),
        ("model", lambda k: model[k]),
    ):
        prof, resid, lvl, w = [], [], [], []
        for k in keys:
            npl = bench[k]["npl"]
            d = np.asarray(get(k), float)[:_T].reshape(-1, 24)[:, : OFF_LAST + 1]
            d = d[(d > 0.05 * npl).all(axis=1)]
            if d.shape[0] < 60:
                continue
            p = d.mean(axis=0)
            prof.append(p.std() / npl)
            resid.append((d - p[None, :]).std() / npl)
            lvl.append(p.mean() / npl)
            w.append(npl)
        w = np.asarray(w)
        out[lbl] = {
            "n_plants": int(w.size),
            "prof_std_frac": float(np.average(prof, weights=w)),
            "resid_std_frac": float(np.average(resid, weights=w)),
            "level_frac": float(np.average(lvl, weights=w)),
        }
    out["R_prof"] = out["model"]["prof_std_frac"] / out["actual"]["prof_std_frac"]
    out["R_resid"] = out["model"]["resid_std_frac"] / out["actual"]["resid_std_frac"]
    out["R_level"] = out["model"]["level_frac"] / out["actual"]["level_frac"]
    return out


def flat_census(bench: dict, model: dict, keys: list[str]) -> dict:
    """Share of class nameplate on plants whose off-peak profile is flat."""
    out: dict = {}
    for lbl, get in (
        ("actual", lambda k: bench[k]["mw"]),
        ("model", lambda k: model[k]),
    ):
        flat_mw = 0.0
        tot_mw = 0.0
        n_flat = 0
        for k in keys:
            npl = bench[k]["npl"]
            p = np.asarray(get(k), float)[:_T].reshape(-1, 24).mean(axis=0)
            tot_mw += npl
            if p[OFF].std() / npl < FLAT_THRESHOLD:
                flat_mw += npl
                n_flat += 1
        out[lbl] = {
            "n_flat": n_flat,
            "n": len(keys),
            "flat_mw": round(flat_mw, 1),
            "class_mw": round(tot_mw, 1),
            "flat_share": round(flat_mw / tot_mw, 4) if tot_mw else None,
        }
    return out


def amplitude_vs_level(rows: list[dict], side: str) -> dict:
    """Capacity-weighted LS fit of per-plant amplitude on per-plant loading.

    Reality's coal plants swing MORE in absolute terms when they are loaded
    harder (more room above min-load to move in); a model whose per-plant
    amplitude is a fixed fraction of nameplate has no such response, and in a
    year when loading rises it therefore loses amplitude that reality keeps.
    """
    e = [r for r in rows if r["side"] == side]
    x = np.array([r["cf_off"] for r in e])
    y = np.array([r["std_frac"] for r in e])
    w = np.array([r["npl"] for r in e])
    a = np.vstack([x, np.ones_like(x)]).T
    beta = np.linalg.lstsq(a * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)[0]
    pred = a @ beta
    ybar = np.average(y, weights=w)
    r2 = 1.0 - (w * (y - pred) ** 2).sum() / (w * (y - ybar) ** 2).sum()
    return {
        "slope": float(beta[0]),
        "intercept": float(beta[1]),
        "weighted_r2": float(r2),
        "n": int(x.size),
    }


# ---------------------------------------------------------------------------
# P2 — the unquantized second grain
# ---------------------------------------------------------------------------


def parquet_class_profile(year: int, klass: str) -> np.ndarray | None:
    """Return the keeper's UNQUANTIZED hour-of-day class profile, or None."""
    path = KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    col = "klass" if "klass" in df.columns else "class"
    sub = df[df[col] == klass]
    if sub.empty:
        return None
    s = sub.groupby("hour", observed=True)["mw"].sum()
    return s.reindex(range(_T), fill_value=0.0).to_numpy(float).reshape(-1, 24).mean(0)


# ---------------------------------------------------------------------------
# P3 — the quantization floor
# ---------------------------------------------------------------------------


def quantization_bound() -> dict:
    """Bound the uint8 CF% encoding's contribution to ``std_frac``.

    Bytes are ``round(100 * mw / nameplate)``, so per-hour error is uniform on
    +/-0.5 % of nameplate, sd ``0.005/sqrt(3)``. An hour-of-day profile point
    averages 365 independent days, so the profile's per-point noise sd is that
    over ``sqrt(365)``; the std of 15 such points is bounded by the same scale.
    """
    per_hour = 0.005 / np.sqrt(3.0)
    per_profile_point = per_hour / np.sqrt(365.0)
    return {
        "per_hour_sd_frac_of_npl": float(per_hour),
        "profile_point_sd_frac_of_npl": float(per_profile_point),
        "flat_threshold_frac_of_npl": FLAT_THRESHOLD,
        "noise_over_threshold": float(per_profile_point / FLAT_THRESHOLD),
        "bar": P3_MAX_NOISE_FRAC,
        "verdict": (
            "PASS"
            if per_profile_point / FLAT_THRESHOLD <= P3_MAX_NOISE_FRAC
            else "FAIL"
        ),
    }


# ---------------------------------------------------------------------------
# P9 — the lever wiring adjudication, two grains
# ---------------------------------------------------------------------------


def _keeper_config():
    """Rebuild the keeper's own ScenarioConfig from its committed run_config."""
    from market_sim.config.scenarios import ScenarioConfig

    raw = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(
        **{k: v for k, v in raw["scenario_config"].items() if k in names}
    )


def lever_wiring(year: int = 2025) -> dict:
    """Adjudicate whether ``coal_tranche_*_frac`` reaches MISO's solve path.

    Grain 1 (construction): does MISO's own fleet synthesis produce a NON-EMPTY
    ``campd_bins`` frame? ``fleet.assembly.build_dispatch_fleet`` branches on
    ``campd_bins is not None``, and ``split_coal_tranches`` — the sole consumer
    of the fractions outside probe scripts — lives only in the ``else`` limb.

    Grain 2 (measurement): assemble the real dispatch fleet twice at HEAD under
    the keeper's own config, once with the committed fractions and once with
    :data:`TRANCHE_PERTURB`, and compare ``pmax_mw`` and ``fuel_fracs``
    elementwise. A zero difference on a materially perturbed split is the
    pre-registered INERT-BY-WIRING verdict; any difference REFUSES it.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import (
        build_base_fleet,
        build_dispatch_fleet,
        fleet_to_bins,
        load_fleet_from_csv,
        thermal_tranche_overrides,
    )

    cfg = _keeper_config()
    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]

    raw_fleet = load_fleet_from_csv(
        "MISO",
        iso_config,
        year=year,
        measured_ct_heat_rates=cfg.measured_ct_heat_rates,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        cc_steam_part_capacity=cfg.cc_steam_part_capacity,
    )
    bins = fleet_to_bins(raw_fleet, "MISO", cfg)

    grain1 = {
        "use_campd_bins": bool(cfg.use_campd_bins),
        "plant_level_fleet": bool(cfg.plant_level_fleet),
        "thermal_tranche_overrides_present": bool(thermal_tranche_overrides("MISO")),
        "campd_bins_rows": int(len(bins)),
        "campd_bins_empty": bool(bins.empty),
        "branch_taken": "campd_bins"
        if not bins.empty
        else "legacy/split_coal_tranches",
        "sole_consumer": (
            "market_sim.data.offer_curves.split_coal_tranches "
            "(data/offer_curves.py:70-72), called only from the else limb of "
            "fleet/assembly.py build_dispatch_fleet's `if campd_bins is not None`"
        ),
    }

    def _assemble(config):
        base = build_base_fleet(
            bins,
            "MISO",
            iso_config,
            zone_names,
            config,
            [],
            [],
            year,
            None,
            vintage_year=year,
            legacy_n_bins=0,
        )
        fleet, fuel_fracs, _, _ = build_dispatch_fleet(
            base, bins, [], "MISO", year, zone_names, config
        )
        return fleet, np.asarray(fuel_fracs, float)

    base_fleet, base_ff = _assemble(cfg)
    pert = dataclasses.replace(cfg, **TRANCHE_PERTURB)
    pert_fleet, pert_ff = _assemble(pert)

    same_len = len(base_fleet) == len(pert_fleet) and base_ff.size == pert_ff.size
    if same_len:
        pmax_a = np.array([g.pmax_mw for g in base_fleet], float)
        pmax_b = np.array([g.pmax_mw for g in pert_fleet], float)
        d_pmax = float(np.abs(pmax_a - pmax_b).max())
        d_ff = float(np.abs(base_ff - pert_ff).max())
        n_pmax = int((pmax_a != pmax_b).sum())
        n_ff = int((base_ff != pert_ff).sum())
    else:
        d_pmax = d_ff = float("nan")
        n_pmax = n_ff = -1

    live = (not same_len) or n_pmax > 0 or n_ff > 0
    grain2 = {
        "perturbation": TRANCHE_PERTURB,
        "committed": {
            "coal_tranche_1_frac": cfg.coal_tranche_1_frac,
            "coal_tranche_2_frac": cfg.coal_tranche_2_frac,
            "coal_tranche_3_frac": cfg.coal_tranche_3_frac,
        },
        "n_generators": len(base_fleet),
        "same_shape": bool(same_len),
        "max_abs_dpmax_mw": d_pmax,
        "n_pmax_changed": n_pmax,
        "max_abs_dfuel_frac": d_ff,
        "n_fuel_frac_changed": n_ff,
    }
    return {
        "grain1_construction": grain1,
        "grain2_measurement": grain2,
        "verdict": "LIVE — wiring kill REFUSED" if live else "INERT BY WIRING at MISO",
        "consequence": (
            "coal_tranche_1/2/3_frac is not a MISO tuning channel; issue #1336 "
            "is a split-fleet-ISO debt, not a MISO one, and no arm is solved on "
            "it here."
            if not live
            else "the lever is reachable at MISO; it still may not be swept "
            "against the C7 residual (rules 1/24) and needs its own rule-23 "
            "re-derive session citing a SOURCE-data change."
        ),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    """Run every pre-registered property and write the record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--skip-grain2",
        action="store_true",
        help="skip the P9 grain-2 fleet assembly (dispatch-only re-run)",
    )
    args = ap.parse_args()

    sidecar = LD.find_registry_sidecar(REPO, KEEPER_BUNDLE)
    if sidecar is None or sidecar.get("id") != KEEPER_RUN:
        raise SystemExit(
            f"keeper sidecar for {KEEPER_BUNDLE} not found / not {KEEPER_RUN}"
        )

    committed = json.loads((KEEPER_BUNDLE / "legitimacy_diagnostics.json").read_text())
    d1_rows = committed["diagnostics"]["D1"]["rows"]
    committed_cv = {
        int(r["year"]): r["cv_ratio"]
        for r in d1_rows
        if r["class"] == TARGET and r["cv_ratio"] is not None
    }
    flags = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())
    gas = json.loads((KEEPER_BUNDLE / "meta.json").read_text()).get("kwargs", {})

    res: dict = {
        "probe": "miso-128 C7 2025 diurnal organization",
        "prereg": "results/calibration/PREREG-miso128-c7-2025-diurnal-organization-2026-08-04.md",
        "keeper_run": KEEPER_RUN,
        "bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
        "years": list(YEARS),
        "gate": {"d1_min_cv_ratio": GATE, "offpeak_last_hour": OFF_LAST},
        "no_lp_solved": True,
    }

    per_year: dict = {}
    plant_rows: list[dict] = []
    for year in YEARS:
        bench, model = load_sides(year, sidecar)
        keys = matched_keys(bench, model, TARGET)
        m = class_series(keys, lambda k: model[k])
        a = class_series(keys, lambda k: bench[k]["mw"])
        dec = decompose(m, a)
        dec["n_matched"] = len(keys)
        dec["committed_cv_ratio"] = committed_cv.get(year)
        dec["repro_abs_err"] = (
            abs(dec["cv_ratio"] - committed_cv[year]) if year in committed_cv else None
        )
        dec["online_days"] = online_day_stats(bench, model, keys)
        dec["flat_census"] = flat_census(bench, model, keys)
        dec["controls"] = {}
        for klass in CONTROLS:
            ck = matched_keys(bench, model, klass)
            if not ck:
                continue
            cd = decompose(
                class_series(ck, lambda k: model[k]),
                class_series(ck, lambda k: bench[k]["mw"]),
            )
            dec["controls"][klass] = {
                k: cd[k] for k in ("R_tot", "R_dfrac", "R_level", "cv_ratio")
            }

        # P2 — the unquantized second grain, on SHAPE (the parquet carries the
        # full class, the payload the matched subset, so levels differ by
        # construction and only shape is comparable).
        pq = parquet_class_profile(year, TARGET)
        if pq is None:
            dec["P2"] = {"verdict": "UNAVAILABLE", "note": "no class_hourly parquet"}
        else:
            pm = m.reshape(-1, 24).mean(axis=0)
            r = float(np.corrcoef(pm, pq)[0, 1])
            cv_pay = pm[OFF].std() / pm[OFF].mean()
            cv_pq = pq[OFF].std() / pq[OFF].mean()
            rel = abs(cv_pay - cv_pq) / cv_pq
            dec["P2"] = {
                "profile_r": round(r, 5),
                "payload_offpeak_cv": round(float(cv_pay), 5),
                "parquet_offpeak_cv": round(float(cv_pq), 5),
                "rel_diff": round(float(rel), 5),
                "bars": {"min_r": P2_MIN_R, "rel_tol": P2_REL_TOL},
                "verdict": "PASS" if (r >= P2_MIN_R and rel <= P2_REL_TOL) else "FAIL",
            }

        for k in keys:
            npl = bench[k]["npl"]
            for lbl, s in (("actual", bench[k]["mw"]), ("model", model[k])):
                p = np.asarray(s, float)[:_T].reshape(-1, 24).mean(axis=0)
                plant_rows.append(
                    {
                        "year": year,
                        "key": k,
                        "npl": npl,
                        "side": lbl,
                        "cf_off": float(p[OFF].mean() / npl),
                        "std_frac": float(p[OFF].std() / npl),
                    }
                )
        per_year[str(year)] = dec

    res["per_year"] = per_year

    # ---- P1 ---------------------------------------------------------------
    errs = [per_year[str(y)]["repro_abs_err"] for y in YEARS]
    res["P1_reproduction"] = {
        "abs_err": [round(e, 4) for e in errs],
        "tol": P1_TOL,
        "verdict": "PASS" if all(e <= P1_TOL for e in errs) else "FAIL",
        "note": (
            "the committed artifact was computed from the solve-time dispatch/ "
            "parquet; this construction uses the registered payload, which is "
            "D-1's own fallback grain."
        ),
    }
    if res["P1_reproduction"]["verdict"] == "FAIL":
        res["KILL_1"] = "P1 failed — no statistic below is read (PREREG KILL-1)."
        _write(res)
        return 1

    res["P2_two_grain"] = {str(y): per_year[str(y)]["P2"] for y in YEARS}
    res["P3_quantization"] = quantization_bound()

    # ---- P4 / P5 ----------------------------------------------------------
    rel = [
        abs(per_year[str(y)]["product"] - per_year[str(y)]["cv_ratio"])
        / per_year[str(y)]["cv_ratio"]
        for y in YEARS
    ]
    res["P4_decomposition_exact"] = {
        "max_rel_err": float(max(rel)),
        "tol": P4_REL_TOL,
        "verdict": "PASS" if max(rel) <= P4_REL_TOL else "FAIL",
    }
    r_tot = {y: per_year[str(y)]["R_tot"] for y in YEARS}
    r_df = {y: per_year[str(y)]["R_dfrac"] for y in YEARS}
    r_lv = {y: per_year[str(y)]["R_level"] for y in YEARS}
    c1 = r_tot[2025] > r_tot[2024]
    c2 = r_lv[2025] < r_lv[2024]
    c3 = r_df[2025] < P5_DFRAC_DROP * r_df[2024]
    res["P5_single_factor"] = {
        "R_tot": {str(y): round(r_tot[y], 4) for y in YEARS},
        "R_dfrac": {str(y): round(r_df[y], 4) for y in YEARS},
        "R_level": {str(y): round(r_lv[y], 4) for y in YEARS},
        "cond_R_tot_2025_gt_2024": bool(c1),
        "cond_R_level_2025_lt_2024": bool(c2),
        "cond_R_dfrac_2025_lt_080x_2024": bool(c3),
        "verdict": "PASS" if (c1 and c2 and c3) else "FAIL",
    }

    # ---- P6 — the absolute-deficit test (R') -------------------------------
    dm = [
        per_year[str(y)]["actual"]["prof_std"] - per_year[str(y)]["model"]["prof_std"]
        for y in YEARS
    ]
    dn = [
        d / per_year[str(y)]["actual"]["mean"] for d, y in zip(dm, YEARS, strict=True)
    ]
    dc = [
        per_year[str(y)]["actual"]["cv"] - per_year[str(y)]["model"]["cv"]
        for y in YEARS
    ]

    def _nonincreasing(v):
        return v[1] <= v[0] + P6_TOL and v[2] <= v[1] + P6_TOL

    res["P6_absolute_deficit"] = {
        "deficit_mw": [round(v, 1) for v in dm],
        "deficit_over_actual_mean": [round(v, 5) for v in dn],
        "cv_deficit": [round(v, 5) for v in dc],
        "nonincreasing": {
            "mw": bool(_nonincreasing(dm)),
            "normalised": bool(_nonincreasing(dn)),
            "cv": bool(_nonincreasing(dc)),
        },
        "verdict": (
            "PASS"
            if all(_nonincreasing(v) for v in (dm, dn, dc))
            else "FAIL — R' refuted"
        ),
    }

    # ---- P7 — dimension specificity on fully-online days -------------------
    rr = [per_year[str(y)]["online_days"]["R_resid"] for y in YEARS]
    rp = [per_year[str(y)]["online_days"]["R_prof"] for y in YEARS]
    resid_drift = max(rr) - min(rr)
    prof_drop = rp[1] - rp[2]
    res["P7_dimension_specific"] = {
        "R_resid": [round(v, 4) for v in rr],
        "R_prof": [round(v, 4) for v in rp],
        "R_level": [
            round(per_year[str(y)]["online_days"]["R_level"], 4) for y in YEARS
        ],
        "resid_drift": round(float(resid_drift), 4),
        "prof_drop_2024_to_2025": round(float(prof_drop), 4),
        "bar": P7_STABLE,
        "verdict": (
            "PASS" if (resid_drift < P7_STABLE and prof_drop > P7_STABLE) else "FAIL"
        ),
    }

    # ---- P8 — control classes (a fork, not a kill) -------------------------
    ctl = {
        klass: {
            str(y): per_year[str(y)]["controls"].get(klass, {}).get("R_dfrac")
            for y in YEARS
        }
        for klass in CONTROLS
    }
    collapsed = {
        klass: (
            v["2025"] is not None
            and v["2024"] is not None
            and v["2025"] < P5_DFRAC_DROP * v["2024"]
        )
        for klass, v in ctl.items()
    }
    res["P8_controls"] = {
        "R_dfrac": {
            k: {y: (round(x, 4) if x is not None else None) for y, x in v.items()}
            for k, v in ctl.items()
        },
        "collapsed_in_2025": collapsed,
        "fork": (
            "coal-fleet-wide hour-of-day defect"
            if all(collapsed.values())
            else "COAL_PRB-specific"
            if not any(collapsed.values())
            else "mixed — reported per class"
        ),
    }

    # ---- the amplitude-vs-level relation -----------------------------------
    res["amplitude_vs_level"] = {
        side: amplitude_vs_level(plant_rows, side) for side in ("actual", "model")
    }
    res["flat_census"] = {str(y): per_year[str(y)]["flat_census"] for y in YEARS}

    # ---- the measured driver ----------------------------------------------
    gp = flags.get("calibration_flags", {}).get(GAS_PRICE_FLAG) or gas.get(
        GAS_PRICE_FLAG
    )
    res["driver"] = {
        "gas_price_mmbtu": gp,
        "offpeak_mean_mw": {
            str(y): {
                "actual": round(per_year[str(y)]["actual"]["mean"], 1),
                "model": round(per_year[str(y)]["model"]["mean"], 1),
            }
            for y in YEARS
        },
        "offpeak_level_change_2024_2025": {
            "actual": round(
                per_year["2025"]["actual"]["mean"] / per_year["2024"]["actual"]["mean"]
                - 1.0,
                4,
            ),
            "model": round(
                per_year["2025"]["model"]["mean"] / per_year["2024"]["model"]["mean"]
                - 1.0,
                4,
            ),
        },
        "note": (
            "reported as the measured driver of the 2025 denominator move. It "
            "sizes nothing — PREREG KILL-4 forbids sizing any parameter on any "
            "quantity in this probe."
        ),
    }

    # ---- P9 — the lever wiring adjudication --------------------------------
    if args.skip_grain2:
        res["P9_lever_wiring"] = {"verdict": "SKIPPED (--skip-grain2)"}
    else:
        res["P9_lever_wiring"] = lever_wiring()

    _write(res)
    _report(res)
    return 0


def _write(res: dict) -> None:
    """Persist the record beside the other calibration probe records."""
    out = REPO / "results/calibration/_miso128_c7_diurnal_organization.json"
    out.write_text(json.dumps(res, indent=2, sort_keys=False, default=float) + "\n")
    print(f"\nwrote {out.relative_to(REPO)}")


def _report(res: dict) -> None:
    """Print the pre-registered verdicts in the order they were declared."""
    print("\n=== miso-128 — pre-registered properties ===")
    for key in (
        "P1_reproduction",
        "P4_decomposition_exact",
        "P5_single_factor",
        "P6_absolute_deficit",
        "P7_dimension_specific",
        "P3_quantization",
    ):
        v = res.get(key, {})
        print(f"  {key:26s} {v.get('verdict')}")
    for y, v in res.get("P2_two_grain", {}).items():
        print(
            f"  P2 two-grain {y}            {v.get('verdict')}  r={v.get('profile_r')} rel={v.get('rel_diff')}"
        )
    print(f"  P8 fork                    {res.get('P8_controls', {}).get('fork')}")
    print(
        f"  P9 lever wiring            {res.get('P9_lever_wiring', {}).get('verdict')}"
    )
    print("\n=== the decomposition ===")
    print(
        f"{'year':>6} {'R_tot':>7} {'R_dfrac':>8} {'R_level':>8} {'cv_ratio':>9} {'gate':>6}"
    )
    for y in YEARS:
        d = res["per_year"][str(y)]
        print(
            f"{y:>6} {d['R_tot']:7.3f} {d['R_dfrac']:8.3f} {d['R_level']:8.3f} "
            f"{d['cv_ratio']:9.3f} {'pass' if d['cv_ratio'] >= GATE else 'FAIL':>6}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
