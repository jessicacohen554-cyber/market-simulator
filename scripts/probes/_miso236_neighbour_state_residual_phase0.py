"""miso-236 phase 0 — is MISO's missing seam variation a MISSING measured input,
an UNUSED one, or genuinely idiosyncratic? And is the model's own seam residual a
deterministic diurnal template? Zero LP.

Pre-registration:
``results/calibration/PREREG-miso236-neighbour-state-and-the-idiosyncratic-residual-2026-09-07.md``
(pushed at ``92de849b``, before any adjudicating quantity). Every decision rule
applied here is fixed there; nothing below selects anything.

The object is ``r_meas,s(t)`` — the measured seam flow's residual from the
miso-235 §3 OLS, which carries 78.5/79.4/83.5 % of MISO's interchange sigma
deficit and 100 % of it on SPP, South and Manitoba. Three questions:

* **Provenance gate (PREREG §1).** miso-235's ``sigma_measured_mw`` and
  ``sigma_resid_measured_mw`` are recomputed here on this code path and must agree
  with the committed JSON to <= 0.5 MW, or nothing else is read.
* **Q-A (PREREG §2, the adjudicating question).** A census of which seam DIBAs
  have an EIA-930 BALANCE neighbour-state series at all, then a three-way variance
  split of ``r_meas`` into what MISO's OWN state explains (Block B — information
  the model already has), what NEIGHBOUR state adds on top (Block A — information
  the model does not have), and what neither explains (idiosyncratic).
* **Q-B (PREREG §3, handoff item 3).** The deterministic (month x hod) template's
  explanatory share of each side's residual, gated for PJM.

Basis discipline (miso-234 §0a, miso-235 §0b): the price ``P`` is the Indiana-hub
**RT** series (the lane's scored basis); every OLS regressor is the Indiana-hub
**DA** series (the basis the seam ladders were Q-Q derived against). They
correlate only +0.402/+0.424/+0.553 and are never interchanged.

Usage: python3 scripts/probes/_miso236_neighbour_state_residual_phase0.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso233_sppseam_K"
BALANCE_DIR = REPO / "data/raw/eia-930"
INTERCHANGE = REPO / "data/raw/eia-930-interchange/MISO interchange hourly.parquet"
MISO235 = REPO / "results/calibration/_miso235_seam_variance_decomposition_phase0.json"
OUT = REPO / "results/calibration/_miso236_neighbour_state_residual_phase0.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"
FOUR_SEAM = ("PJM", "SPP", "South", "Manitoba")
BUS_OF_SEAM = {
    "PJM": "MISO_external",
    "SPP": "MISO_external",
    "South": "MISO_external_South",
    "Manitoba": "MISO_external",
}

# PREREG §1 provenance gate, fixed ex ante.
PROVENANCE_TOL_MW = 0.5
# PREREG §2a census bars, fixed ex ante.
COVERAGE_BAR = 0.95
GROSS_SHARE_BAR = 0.50
# PREREG §2b decision bars, fixed ex ante.
DR2_ADMISSIBLE_BAR = 0.10
DR2_NONE_BAR = 0.05
IDIOSYNCRATIC_BAR = 0.75
FRAGILE_RATIO_BAR = 0.5
# PREREG §3 bars, fixed ex ante (gated for PJM only).
TMPL_CONFIRM_BAR = 0.50
TMPL_RATIO_BAR = 3.0
TMPL_REFUTE_BAR = 0.25
TMPL_CELLS = 12 * 24

_MONTH_LEN = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0, *[24 * d for d in _MONTH_LEN]])[:12]


def ols_resid(x: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Residual of ``x = a + beta*z + r`` (the miso-235 §3 single-regressor OLS)."""
    zc = z - z.mean()
    var_z = float((zc * zc).mean())
    beta = float(((x - x.mean()) * zc).mean() / var_z) if var_z > 0 else 0.0
    return x - (x.mean() + beta * zc)


def _fit(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Least-squares coefficients for ``y ~ [1 | X]`` (z-scored X, intercept added)."""
    A = np.column_stack([np.ones(len(y)), X]) if X.size else np.ones((len(y), 1))
    return np.linalg.lstsq(A, y, rcond=None)[0]


def _r2(y: np.ndarray, X: np.ndarray, coef: np.ndarray | None = None) -> float:
    """R^2 of ``y`` on ``[1 | X]``; out-of-sample when ``coef`` is supplied."""
    A = np.column_stack([np.ones(len(y)), X]) if X.size else np.ones((len(y), 1))
    b = _fit(y, X) if coef is None else coef
    resid = y - A @ b
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return float(1.0 - (resid**2).sum() / ss_tot) if ss_tot > 0 else 0.0


def _z(a: np.ndarray) -> np.ndarray:
    """Z-score a regressor column; a constant column becomes zeros."""
    s = float(a.std())
    return (a - a.mean()) / s if s > 0 else np.zeros_like(a)


def hour_index(local_end: pd.Series) -> np.ndarray:
    """Hour-ending local wall clock -> the lane's fixed non-leap hour-of-year index.

    Identical construction to ``derive_miso_seam_ladders.load_joined`` (shift to
    hour-beginning, month-start offset, Feb 29 dropped as -1).
    """
    t = pd.to_datetime(local_end) - pd.Timedelta(hours=1)
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in t.dt.month])
    hr = base + (t.dt.day.to_numpy() - 1) * 24 + t.dt.hour.to_numpy()
    hr = np.where((t.dt.month == 2) & (t.dt.day == 29), -1, hr)
    return hr


_FUEL = {
    "wind": lambda c: c.startswith("Net Generation (MW) from Wind"),
    "solar": lambda c: c.startswith("Net Generation (MW) from Solar"),
    "hydro": lambda c: ("Hydropower" in c) or ("Pumped Storage" in c),
}


def load_balance() -> pd.DataFrame:
    """EIA-930 BALANCE 2023-2025 -> tidy (ba, utc, local, demand, wind, solar, hydro).

    Only the ``(Adjusted)`` columns are read (never ``(Imputed)``), matching
    ``scripts/data/derive_wecc_west_supply.py``.
    """
    import pyarrow.parquet as pq

    frames = []
    for year in YEARS:
        for half in ("Jan_Jun", "Jul_Dec"):
            path = BALANCE_DIR / f"EIA930_BALANCE_{year}_{half}.parquet"
            names = set(pq.ParquetFile(path).schema.names)
            fuel = {
                k: [
                    c
                    for c in names
                    if "(Adjusted)" in c and "Imputed" not in c and pred(c)
                ]
                for k, pred in _FUEL.items()
            }
            read = [
                "Balancing Authority",
                "Local Time at End of Hour",
                "UTC Time at End of Hour",
                "Demand (MW) (Adjusted)",
            ] + sorted({c for cols in fuel.values() for c in cols})
            df = pd.read_parquet(path, columns=read)
            out = pd.DataFrame(
                {
                    "ba": df["Balancing Authority"].astype(str),
                    "utc": pd.to_datetime(df["UTC Time at End of Hour"], utc=True),
                    "local": df["Local Time at End of Hour"],
                    "demand": pd.to_numeric(
                        df["Demand (MW) (Adjusted)"], errors="coerce"
                    ),
                }
            )
            for k, cols in fuel.items():
                out[k] = (
                    df[cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
                    if cols
                    else 0.0
                )
            frames.append(out)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    from market_sim.data.eia_loader import (
        measured_miso_spp_hub_prices,
        measured_seam_import_envelope,
    )
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_MANITOBA_SEAM_SPEC,
        MISO_SEAM_DIBA,
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    from _miso224_floor_anatomy_phase0 import actual_zone_price

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()

    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}
    specs["Manitoba"] = MISO_MANITOBA_SEAM_SPEC
    prior = json.loads(MISO235.read_text())["years"]

    bal = load_balance()
    bal_bas = set(bal["ba"].unique())

    # --- PREREG §2a census, part 1: DIBA presence (existence, non-adjudicating) ---
    census = {
        s: {
            "dibas": list(d),
            "present_in_balance": [x for x in d if x in bal_bas],
            "absent_from_balance": [x for x in d if x not in bal_bas],
        }
        for s, d in MISO_SEAM_DIBA.items()
    }

    # Per-seam gross flow share carried by the BALANCE-present DIBAs.
    ix = pd.read_parquet(INTERCHANGE)
    ix = ix.assign(hour=hour_index(ix["local_time"]))
    ix = ix.assign(
        year=(pd.to_datetime(ix["local_time"]) - pd.Timedelta(hours=1)).dt.year
    )
    ix = ix[(ix["hour"] >= 0) & (ix["hour"] < HOURS)]

    report = {
        "probe": "miso-236 phase 0 — neighbour state vs the idiosyncratic seam residual",
        "prereg": (
            "results/calibration/"
            "PREREG-miso236-neighbour-state-and-the-idiosyncratic-residual-2026-09-07.md"
            " (pushed 92de849b)"
        ),
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "price_basis": "P = Indiana hub RT (scored basis); every OLS regressor = Indiana hub DA",
        "bars": {
            "provenance_tol_mw": PROVENANCE_TOL_MW,
            "census_coverage": COVERAGE_BAR,
            "census_gross_share": GROSS_SHARE_BAR,
            "delta_r2_admissible": DR2_ADMISSIBLE_BAR,
            "delta_r2_none": DR2_NONE_BAR,
            "idiosyncratic_floor": IDIOSYNCRATIC_BAR,
            "fragile_ratio": FRAGILE_RATIO_BAR,
            "template_confirm": TMPL_CONFIRM_BAR,
            "template_ratio": TMPL_RATIO_BAR,
            "template_refute": TMPL_REFUTE_BAR,
        },
        "census": census,
        "years": {},
    }

    for seam, d in MISO_SEAM_DIBA.items():
        sub = ix[ix["diba"].isin(d)]
        gross = sub.assign(a=sub["mw"].abs()).groupby(["year", "diba"])["a"].sum()
        shares = {}
        for year in YEARS:
            tot = (
                float(gross.loc[year].sum())
                if year in gross.index.get_level_values(0)
                else 0.0
            )
            cov = float(
                sum(
                    gross.loc[year].get(x, 0.0)
                    for x in census[seam]["present_in_balance"]
                )
            )
            shares[str(year)] = round(cov / tot, 4) if tot > 0 else 0.0
        census[seam]["gross_flow_share_covered"] = shares

    # --- neighbour-state blocks, joined on UTC via MISO's own local<->UTC map ---
    miso_bal = bal[bal["ba"] == "MISO"].copy()
    miso_bal["hour"] = hour_index(miso_bal["local"])
    miso_bal["year"] = (
        pd.to_datetime(miso_bal["local"]) - pd.Timedelta(hours=1)
    ).dt.year
    miso_bal = miso_bal[(miso_bal["hour"] >= 0) & (miso_bal["hour"] < HOURS)]

    nbr = bal[bal["ba"] != "MISO"].copy()
    coverage: dict[str, dict[str, float]] = {}

    years_out: dict[str, dict] = {}
    provenance: dict[str, dict] = {}

    for year in YEARS:
        gy = g_all.loc[year]
        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)

        def dense(col: str) -> np.ndarray:
            return (
                gy[col]
                .reindex(range(HOURS))
                .interpolate(limit=3)
                .ffill()
                .bfill()
                .to_numpy(float)
            )

        border = dense("pjm_border")
        da = dense("da")
        spp_hub = np.asarray(measured_miso_spp_hub_prices("MISO", year, HOURS), float)

        # MISO's own hour <-> UTC map, read from the data (PREREG §0a fact 4).
        my = miso_bal[miso_bal["year"] == year].drop_duplicates("hour")
        hour_to_utc = pd.Series(my["utc"].to_numpy(), index=my["hour"].to_numpy())
        utc_grid = hour_to_utc.reindex(range(HOURS))

        def ba_series(bas: list[str], col: str) -> np.ndarray:
            """Sum ``col`` over ``bas`` on the MISO hour grid, joined on UTC."""
            sub = nbr[nbr["ba"].isin(bas)]
            agg = sub.groupby("utc")[col].sum(min_count=1)
            return agg.reindex(utc_grid.to_numpy()).to_numpy(float)

        def miso_series(col: str) -> np.ndarray:
            s = pd.Series(my[col].to_numpy(), index=my["hour"].to_numpy())
            return s.reindex(range(HOURS)).to_numpy(float)

        # Block B — MISO OWN state (information the model already has).
        miso_nl = miso_series("demand") - miso_series("wind") - miso_series("solar")
        miso_vre = miso_series("wind") + miso_series("solar")

        # Model-side reconstruction (miso-235 four-seam form, unchanged).
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus_price = {
            b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
            for b in set(BUS_OF_SEAM.values())
        }
        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
        regressor = {
            "PJM": da - border,
            "SPP": da - spp_hub,
            "South": da,
            "Manitoba": da,
        }

        model_net: dict[str, np.ndarray] = {}
        meas_net: dict[str, np.ndarray] = {}
        for seam in FOUR_SEAM:
            spec = specs[seam]
            width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
            pb = bus_price[BUS_OF_SEAM[seam]]
            if seam == "PJM":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"],
                    float,
                )
                in_merit = (pb - border)[None, :] > d[:, None]
            elif seam == "SPP":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][
                        "import"
                    ],
                    float,
                )
                in_merit = (pb - spp_hub)[None, :] > d[:, None]
            else:
                lad = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["import"], float)
                in_merit = pb[None, :] > lad[:, None]
            band_i = np.clip(
                np.asarray(env_i[seam], float)[None, :] - ks * width, 0.0, width
            )
            imp = (in_merit * band_i).sum(0)
            lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)
            band_e = np.clip(
                np.asarray(env_e[seam], float)[None, :] - ks * width, 0.0, width
            )
            exp = ((pb[None, :] < lade[:, None]) * band_e).sum(0)
            model_net[seam] = (imp - exp)[ok]
            meas_net[seam] = dense(seam)[ok]

        # --- PREREG §1 provenance gate ---
        prov = {}
        for seam in FOUR_SEAM:
            r_m = ols_resid(meas_net[seam], regressor[seam][ok])
            ref = prior[str(year)]["decomposition"][seam]
            prov[seam] = {
                "sigma_measured_mw": round(float(meas_net[seam].std()), 1),
                "sigma_measured_mw_miso235": ref["sigma_measured_mw"],
                "sigma_resid_measured_mw": round(float(r_m.std()), 1),
                "sigma_resid_measured_mw_miso235": ref["sigma_resid_measured_mw"],
            }
            prov[seam]["max_abs_delta_mw"] = round(
                max(
                    abs(prov[seam]["sigma_measured_mw"] - ref["sigma_measured_mw"]),
                    abs(
                        prov[seam]["sigma_resid_measured_mw"]
                        - ref["sigma_resid_measured_mw"]
                    ),
                ),
                2,
            )
        provenance[str(year)] = prov

        # --- coverage of each neighbour BA on this year's grid ---
        for ba in sorted(bal_bas - {"MISO"}):
            v = ba_series([ba], "demand")
            coverage.setdefault(ba, {})[str(year)] = round(
                float(np.isfinite(v).mean()), 4
            )

        # --- PREREG §2b: the three-way split, and §3: the template ---
        month = np.repeat(np.arange(12), [24 * d for d in _MONTH_LEN])
        hod = np.tile(np.arange(24), 365)
        cell = (month * 24 + hod)[ok]

        def template_r2(y: np.ndarray) -> tuple[float, float]:
            """(raw, dof-adjusted) between-cell variance share of the (month x hod) block."""
            df = pd.DataFrame({"c": cell, "y": y})
            fitted = df.groupby("c")["y"].transform("mean").to_numpy()
            ss_tot = float(((y - y.mean()) ** 2).sum())
            raw = float(1.0 - ((y - fitted) ** 2).sum() / ss_tot) if ss_tot > 0 else 0.0
            n = len(y)
            adj = 1.0 - (1.0 - raw) * (n - 1) / (n - TMPL_CELLS)
            return round(raw, 4), round(adj, 4)

        seams_out: dict[str, dict] = {}
        for seam in FOUR_SEAM:
            r_meas = ols_resid(meas_net[seam], regressor[seam][ok])
            r_model = ols_resid(model_net[seam], regressor[seam][ok])
            covered = census[seam]["present_in_balance"]

            block_b = np.column_stack([_z(miso_nl[ok]), _z(miso_vre[ok])])
            entry: dict = {
                "covered_dibas": covered,
                "r2_block_B_miso_own": round(_r2(r_meas, block_b), 4),
            }
            if covered:
                n_nl = (
                    ba_series(covered, "demand")
                    - ba_series(covered, "wind")
                    - ba_series(covered, "solar")
                )
                n_vre = ba_series(covered, "wind") + ba_series(covered, "solar")
                n_hyd = ba_series(covered, "hydro")
                good = (
                    np.isfinite(n_nl[ok])
                    & np.isfinite(n_vre[ok])
                    & np.isfinite(n_hyd[ok])
                )
                y = r_meas[good]
                bb = block_b[good]
                a_nohyd = np.column_stack([_z(n_nl[ok][good]), _z(n_vre[ok][good])])
                a_hyd = np.column_stack([a_nohyd, _z(n_hyd[ok][good])])
                r2_b = _r2(y, bb)
                r2_ab_nohyd = _r2(y, np.column_stack([bb, a_nohyd]))
                r2_ab_hyd = _r2(y, np.column_stack([bb, a_hyd]))
                entry.update(
                    {
                        "n_hours_block": int(good.sum()),
                        "r2_block_B_on_block_hours": round(r2_b, 4),
                        "r2_AB_nohydro": round(r2_ab_nohyd, 4),
                        "r2_AB_withhydro": round(r2_ab_hyd, 4),
                        # GATED value (PREREG §2b): the no-hydro block.
                        "delta_r2_A_nohydro": round(r2_ab_nohyd - r2_b, 4),
                        "delta_r2_A_withhydro": round(r2_ab_hyd - r2_b, 4),
                        "unexplained_share_nohydro": round(1.0 - r2_ab_nohyd, 4),
                    }
                )
                entry["_blocks"] = {
                    "y": y,
                    "B": bb,
                    "A": a_nohyd,
                    "members": {
                        "neighbour_net_load": _z(n_nl[ok][good]),
                        "neighbour_vre": _z(n_vre[ok][good]),
                        "neighbour_hydro": _z(n_hyd[ok][good]),
                    },
                }
                # ADDENDUM §B — per-member increment over Block B alone.
                # REPORTED, NOT GATED; it cannot move the seam's verdict.
                entry["delta_r2_A_by_member_reported_not_gated"] = {
                    name: round(_r2(y, np.column_stack([bb, col[:, None]])) - r2_b, 4)
                    for name, col in entry["_blocks"]["members"].items()
                }
            r_raw, r_adj = template_r2(r_model)
            m_raw, m_adj = template_r2(r_meas)
            entry.update(
                {
                    "template_r2_model_raw": r_raw,
                    "template_r2_model_adj": r_adj,
                    "template_r2_measured_raw": m_raw,
                    "template_r2_measured_adj": m_adj,
                    "template_ratio_adj": (
                        round(r_adj / m_adj, 2) if m_adj > 0 else None
                    ),
                    "sigma_resid_model_mw": round(float(r_model.std()), 1),
                    "sigma_resid_measured_mw": round(float(r_meas.std()), 1),
                }
            )
            seams_out[seam] = entry
        years_out[str(year)] = {"seams": seams_out}

    # --- PREREG §2b fragility leg: fit on one year, evaluate on the other two ---
    for seam in FOUR_SEAM:
        if not census[seam]["present_in_balance"]:
            continue
        oos: dict[str, float] = {}
        for fit_y in YEARS:
            blk = years_out[str(fit_y)]["seams"][seam]["_blocks"]
            cb = _fit(blk["y"], np.column_stack([blk["B"], blk["A"]]))
            cbb = _fit(blk["y"], blk["B"])
            vals = []
            for ev_y in YEARS:
                if ev_y == fit_y:
                    continue
                e = years_out[str(ev_y)]["seams"][seam]["_blocks"]
                vals.append(
                    _r2(e["y"], np.column_stack([e["B"], e["A"]]), cb)
                    - _r2(e["y"], e["B"], cbb)
                )
            oos[str(fit_y)] = round(float(np.mean(vals)), 4)
        in_year = float(
            np.mean(
                [years_out[str(y)]["seams"][seam]["delta_r2_A_nohydro"] for y in YEARS]
            )
        )
        mean_oos = float(np.mean(list(oos.values())))
        report.setdefault("fragility", {})[seam] = {
            "delta_r2_A_out_of_year_by_fit_year": oos,
            "mean_out_of_year": round(mean_oos, 4),
            "mean_in_year": round(in_year, 4),
            "fragile": bool(mean_oos < FRAGILE_RATIO_BAR * in_year),
        }

    for y in years_out.values():
        for e in y["seams"].values():
            e.pop("_blocks", None)

    # --- verdicts on the pre-registered bars ---
    verdicts: dict[str, dict] = {}
    for seam in FOUR_SEAM:
        cov_ok = all(
            coverage.get(b, {}).get(str(y), 0.0) >= COVERAGE_BAR
            for b in census[seam]["present_in_balance"][:1]
            for y in YEARS
        )
        share_ok = all(
            census[seam]["gross_flow_share_covered"][str(y)] >= GROSS_SHARE_BAR
            for y in YEARS
        )
        has_inst = bool(census[seam]["present_in_balance"]) and cov_ok and share_ok
        v: dict = {"has_neighbour_state_instrument": has_inst}
        if has_inst:
            d = [years_out[str(y)]["seams"][seam]["delta_r2_A_nohydro"] for y in YEARS]
            u = [
                years_out[str(y)]["seams"][seam]["unexplained_share_nohydro"]
                for y in YEARS
            ]
            if all(x >= DR2_ADMISSIBLE_BAR for x in d):
                v["driver_verdict"] = "ADMISSIBLE NEIGHBOUR-STATE DRIVER IDENTIFIED"
            elif all(x < DR2_NONE_BAR for x in d):
                v["driver_verdict"] = "NO NEIGHBOUR-STATE DRIVER"
            else:
                v["driver_verdict"] = "MIXED"
            v["delta_r2_A_nohydro_by_year"] = d
            v["unexplained_share_by_year"] = u
            v["predominantly_idiosyncratic"] = bool(
                all(x >= IDIOSYNCRATIC_BAR for x in u)
            )
            v["fragile"] = report.get("fragility", {}).get(seam, {}).get("fragile")
        else:
            v["driver_verdict"] = "NO INSTRUMENT — answered by data absence"
        tm = [years_out[str(y)]["seams"][seam]["template_r2_model_adj"] for y in YEARS]
        te = [
            years_out[str(y)]["seams"][seam]["template_r2_measured_adj"] for y in YEARS
        ]
        if all(
            a >= TMPL_CONFIRM_BAR and a >= TMPL_RATIO_BAR * b for a, b in zip(tm, te)
        ):
            v["template_verdict"] = "CONFIRMED"
        elif any(a < TMPL_REFUTE_BAR for a in tm):
            v["template_verdict"] = "REFUTED"
        else:
            v["template_verdict"] = "PARTIAL"
        v["template_gated"] = seam == "PJM"
        verdicts[seam] = v

    # --- ADDENDUM §A sizing restatement: REPORTED, NOT GATED ---
    # sigma_supply = sqrt(dR2_A_nohydro) * sigma_resid_measured, against the seam's
    # residual-sigma gap (both from the committed miso-235 JSON, reproduced here to
    # 0.00 MW by the provenance gate). An UPPER BOUND on what a perfect use of the
    # gated no-hydro block could contribute; it is NEVER a tuning target (rules 1/13).
    sizing: dict[str, dict] = {}
    for seam in FOUR_SEAM:
        if not verdicts[seam].get("has_neighbour_state_instrument"):
            continue
        rows = {}
        for y in YEARS:
            ref = prior[str(y)]["decomposition"][seam]
            d = years_out[str(y)]["seams"][seam]["delta_r2_A_nohydro"]
            sr_meas = float(ref["sigma_resid_measured_mw"])
            sr_model = float(ref["sigma_resid_model_mw"])
            supply = float(np.sqrt(max(d, 0.0)) * sr_meas)
            gap = sr_model - sr_meas
            rows[str(y)] = {
                "sigma_supply_mw": round(supply, 1),
                "resid_sigma_gap_mw": round(gap, 1),
                "share_of_gap": round(supply / abs(gap), 3) if gap else None,
            }
        sizing[seam] = rows
    report["sizing_reported_not_gated"] = sizing

    prov_max = max(
        p["max_abs_delta_mw"] for yr in provenance.values() for p in yr.values()
    )
    report["provenance_gate"] = {
        "max_abs_delta_mw": prov_max,
        "tolerance_mw": PROVENANCE_TOL_MW,
        "PASS": bool(prov_max <= PROVENANCE_TOL_MW),
        "by_year": provenance,
    }
    report["neighbour_ba_coverage"] = {
        b: coverage[b]
        for b in sorted({x for s in census.values() for x in s["present_in_balance"]})
        if b in coverage
    }
    report["years"] = years_out
    report["verdicts"] = verdicts

    OUT.write_text(json.dumps(report, indent=2, default=float) + "\n")

    # --- console readout ---
    g = report["provenance_gate"]
    print(
        f"PROVENANCE GATE: max |delta| {g['max_abs_delta_mw']:.2f} MW"
        f" vs {PROVENANCE_TOL_MW} MW bar -> {'PASS' if g['PASS'] else 'BROKEN'}"
    )
    if not g["PASS"]:
        print("instrument BROKEN — nothing below is read (PREREG §1)")
        return 1
    print("\nCENSUS (PREREG §2a)")
    for s, c in census.items():
        print(
            f"  {s:<9} present {c['present_in_balance']}  absent {c['absent_from_balance']}"
            f"  gross-share covered "
            + "/".join(f"{c['gross_flow_share_covered'][str(y)]:.3f}" for y in YEARS)
        )
    print("\nQ-A — three-way split of the MEASURED residual (no-hydro block gated)")
    print(
        f"  {'seam':<9} {'year':>5} {'R2_B own':>9} {'R2_AB':>7} {'dR2_A':>7}"
        f" {'unexpl':>7} {'dR2_A+hyd':>10}"
    )
    for seam in FOUR_SEAM:
        for y in YEARS:
            e = years_out[str(y)]["seams"][seam]
            if "delta_r2_A_nohydro" not in e:
                print(f"  {seam:<9} {y:>5}   -- no neighbour-state instrument --")
                continue
            print(
                f"  {seam:<9} {y:>5} {e['r2_block_B_on_block_hours']:>9.4f}"
                f" {e['r2_AB_nohydro']:>7.4f} {e['delta_r2_A_nohydro']:>7.4f}"
                f" {e['unexplained_share_nohydro']:>7.4f}"
                f" {e['delta_r2_A_withhydro']:>10.4f}"
            )
    print("\nQ-B — (month x hod) template, dof-ADJUSTED (gated for PJM)")
    print(f"  {'seam':<9} {'year':>5} {'model':>8} {'measured':>9} {'ratio':>7}")
    for seam in FOUR_SEAM:
        for y in YEARS:
            e = years_out[str(y)]["seams"][seam]
            print(
                f"  {seam:<9} {y:>5} {e['template_r2_model_adj']:>8.4f}"
                f" {e['template_r2_measured_adj']:>9.4f}"
                f" {e['template_ratio_adj']:>7.2f}"
            )
    print("\nVERDICTS (pre-registered bars)")
    for s, v in verdicts.items():
        extra = ""
        if v.get("predominantly_idiosyncratic") is not None:
            extra = (
                f"  idiosyncratic={v['predominantly_idiosyncratic']}"
                f"  fragile={v.get('fragile')}"
            )
        print(
            f"  {s:<9} driver: {v['driver_verdict']}{extra}\n"
            f"            template: {v['template_verdict']}"
            f" ({'GATED' if v['template_gated'] else 'reported'})"
        )
    print("\nADDENDUM §A — sizing, REPORTED NOT GATED (never a tuning target)")
    print(
        f"  {'seam':<9} {'year':>5} {'sigma_supply':>13} {'resid_sigma_gap':>16} {'share':>7}"
    )
    for seam, rows in sizing.items():
        for y in YEARS:
            r = rows[str(y)]
            print(
                f"  {seam:<9} {y:>5} {r['sigma_supply_mw']:>13.1f}"
                f" {r['resid_sigma_gap_mw']:>16.1f} {r['share_of_gap']:>7.3f}"
            )
    print("\nADDENDUM §B — per-member Block-A increment, REPORTED NOT GATED")
    for seam in FOUR_SEAM:
        for y in YEARS:
            e = years_out[str(y)]["seams"][seam]
            m = e.get("delta_r2_A_by_member_reported_not_gated")
            if not m:
                continue
            print(
                f"  {seam:<9} {y:>5} "
                + "  ".join(f"{k}={v:+.4f}" for k, v in m.items())
            )
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
