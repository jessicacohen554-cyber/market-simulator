"""miso-237 phase 0 — is MISO's seam-state channel a PRICE-REPRESENTATION deficiency
or a QUANTITY-SIDE channel? And what does MISO's own state, an input the keeper already
has, actually explain? Zero LP.

Pre-registration:
``results/calibration/PREREG-miso237-price-representation-or-quantity-channel-2026-09-07.md``
(pushed at ``887c7cad``, before any adjudicating quantity). Every decision rule applied
here is fixed there; nothing below selects anything.

miso-236 measured what neighbour state explains **over and above a SINGLE LINEAR hub-pair
spread**, and said against its own interest (§6.3) that "non-price" there is an operational
label, not an economic claim. Two mechanism classes fit that number and they are not
interchangeable: a quantity-side channel no price representation can reach, or a
price-representation deficiency the model's single-difference merit test cannot express.
This probe distinguishes them, before anything is proposed.

* **Provenance gate (PREREG §1).** Two legs. (G-P1) miso-235's ``sigma_measured_mw`` and
  ``sigma_resid_measured_mw`` for all four seams x three years reproduce to <= 0.5 MW.
  (G-P2) miso-236's gated ``delta_r2_A_nohydro`` for PJM/SPP/South x three years reproduces
  **in miso-236's own metric** to <= 0.005. Either leg failing declares the instrument
  BROKEN and nothing else is read.
* **Q-1 (PREREG §2, the adjudicating question).** Nested price blocks P1 (the model's
  single linear spread), P2 (ladder-equivalent: the same series non-parametrically, which
  is what the band ladder can already express) and P3 (rich: P2 plus each leg of the
  spread entered separately and non-parametrically). The survival ratio
  ``rho = dR2_S|P3 / dR2_S|P1`` says whether the state increment is a price object or not.
  GATED on SPP for the neighbour block.
* **Q-2 (PREREG §3, handoff item 2).** The same form question for MISO's OWN state (gated
  on PJM/SPP/South), plus the transmission check and the model-side share and signs.
* **Q-3 (PREREG §4).** How much a better price representation reaches at all. REPORTED,
  NOT GATED, and never a tuning target.
* **A-A (ADDENDUM §A, gated on PJM).** Whether purging the own-state block from the
  model's seam residual moves its price alignment toward the measured seam's — a
  candidate cause for the item-3 defect miso-236 left with none.
* **A-B (ADDENDUM §B, reported not gated).** The same survival ratio with the OTHER
  state block held in every price base, i.e. under miso-236's conditioning. ADDENDUM §0
  discloses that the PREREG's increment is unconditional and is never presented as
  miso-236's own quantity.

Basis discipline (miso-234 §0a, miso-235 §0b, miso-236 §0b): the Indiana-hub **RT** series
builds the finite-hour ``ok`` mask (byte-identically to miso-236, so the hour set is the
predecessor's) and is used for nothing else; every regressor is the Indiana-hub **DA**
series. They correlate only +0.402/+0.424/+0.553 and are never interchanged.

Usage: python3 scripts/probes/_miso237_price_representation_vs_state_phase0.py
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
MISO235 = REPO / "results/calibration/_miso235_seam_variance_decomposition_phase0.json"
MISO236 = REPO / "results/calibration/_miso236_neighbour_state_residual_phase0.json"
OUT = REPO / "results/calibration/_miso237_price_representation_vs_state_phase0.json"

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
# PREREG §2a: the seams for which a neighbour hub price series exists at all.
# South (SOCO/TVA are not organised markets) and Manitoba (MHEB) have none, so
# P3 == P2 there BY CONSTRUCTION — a declared data boundary, not a result.
SEAMS_WITH_NEIGHBOUR_PRICE = ("PJM", "SPP")

# PREREG §1 provenance gate, fixed ex ante.
PROVENANCE_TOL_MW = 0.5
PROVENANCE_TOL_DR2 = 0.005
# PREREG §2b decision bars, fixed ex ante.
RHO_QUANTITY_BAR = 0.50
RHO_PRICE_BAR = 0.25
DR2_ABS_FLOOR = 0.05
# PREREG §2a: 20 sample-quantile bins -> 19 dummies per price series.
VENTILES = 20
# PREREG §2b gating scope, fixed ex ante.
GATED_SEAMS_NEIGHBOUR = ("SPP",)
GATED_SEAMS_OWN = ("PJM", "SPP", "South")
# ADDENDUM §A bars, fixed ex ante (gated on PJM only).
PURGE_CAUSE_BAR = 0.50
PURGE_REFUTE_BAR = 0.20
PURGE_GATED_SEAM = "PJM"

_MONTH_LEN = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0, *[24 * d for d in _MONTH_LEN]])[:12]


def ols_resid(x: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Residual of ``x = a + beta*z + r`` (the miso-235 §3 single-regressor OLS)."""
    zc = z - z.mean()
    var_z = float((zc * zc).mean())
    beta = float(((x - x.mean()) * zc).mean() / var_z) if var_z > 0 else 0.0
    return x - (x.mean() + beta * zc)


def _design(X: np.ndarray, n: int) -> np.ndarray:
    """``[1 | X]`` with an intercept, tolerating an empty regressor block."""
    return np.column_stack([np.ones(n), X]) if X.size else np.ones((n, 1))


def _r2_raw(y: np.ndarray, X: np.ndarray) -> float:
    """In-sample R^2 of ``y`` on ``[1 | X]`` (miso-236's metric, no dof adjustment)."""
    A = _design(X, len(y))
    resid = y - A @ np.linalg.lstsq(A, y, rcond=None)[0]
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return float(1.0 - (resid**2).sum() / ss_tot) if ss_tot > 0 else 0.0


def r2_adj(y: np.ndarray, X: np.ndarray) -> tuple[float, float, int]:
    """(raw, dof-ADJUSTED, rank) R^2 of ``y`` on ``[1 | X]``.

    PREREG §2a fixes the adjustment as ``1 - (1 - R2)(n - 1)/(n - k - 1)`` with ``k`` the
    NUMERICAL RANK of the design (excluding the intercept), never the nominal column
    count — P3's legs are collinear by construction (``spread = DA - neighbour``), so a
    nominal count would over-penalise it. The ADJUSTED value is the gated one.
    """
    n = len(y)
    raw = _r2_raw(y, X)
    k = int(np.linalg.matrix_rank(_design(X, n))) - 1
    adj = 1.0 - (1.0 - raw) * (n - 1) / (n - k - 1) if n - k - 1 > 0 else float("nan")
    return raw, adj, k


def _z(a: np.ndarray) -> np.ndarray:
    """Z-score a regressor column; a constant column becomes zeros."""
    s = float(a.std())
    return (a - a.mean()) / s if s > 0 else np.zeros_like(a)


def ventile_dummies(a: np.ndarray, bins: int = VENTILES) -> np.ndarray:
    """``bins``-quantile step function of ``a`` as ``bins - 1`` dummies (first dropped).

    PREREG §2a's non-parametric price representation: this is exactly the class of
    response the model's band ladder can already express in the spread, which is why P2
    exists and is measured apart from P1.
    """
    edges = np.quantile(a, np.linspace(0.0, 1.0, bins + 1)[1:-1])
    idx = np.searchsorted(edges, a, side="right")
    cols = [(idx == b).astype(float) for b in range(1, bins)]
    return np.column_stack(cols) if cols else np.zeros((len(a), 0))


def hour_index(local_end: pd.Series) -> np.ndarray:
    """Hour-ending local wall clock -> the lane's fixed non-leap hour-of-year index.

    Identical construction to ``derive_miso_seam_ladders.load_joined`` and to
    ``_miso236_neighbour_state_residual_phase0.hour_index``.
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

    Byte-identical to ``_miso236_neighbour_state_residual_phase0.load_balance``; only the
    ``(Adjusted)`` columns are read, never ``(Imputed)``.
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


def purge(r: np.ndarray, S: np.ndarray) -> np.ndarray:
    """ADDENDUM §A: ``r`` with the state block ``S`` projected out (OLS residual).

    A DIAGNOSTIC PROJECTION, not a proposed mechanism — nothing here proposes removing a
    term from the model.
    """
    A = _design(S, len(r))
    return r - A @ np.linalg.lstsq(A, r, rcond=None)[0]


def _verdict(rhos: list[float], dr2_p3: list[float]) -> str:
    """PREREG §2b decision rule, applied identically to the neighbour and own blocks."""
    if all(r >= RHO_QUANTITY_BAR for r in rhos) and all(
        d >= DR2_ABS_FLOOR for d in dr2_p3
    ):
        return "QUANTITY-SIDE FORM"
    if all(r < RHO_PRICE_BAR for r in rhos):
        return "PRICE-REPRESENTATION FORM"
    return "MIXED"


def main() -> int:  # noqa: PLR0915 - one linear probe, mirrors the PREREG section order
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
    prior235 = json.loads(MISO235.read_text())["years"]
    prior236 = json.loads(MISO236.read_text())["years"]

    bal = load_balance()
    bal_bas = set(bal["ba"].unique())
    # Same covered-DIBA lists miso-236 used, so G-P2 reproduces its object and not a
    # lookalike (SIKE's nominal presence included, exactly as there — ADDENDUM §C).
    covered_of = {s: [x for x in d if x in bal_bas] for s, d in MISO_SEAM_DIBA.items()}

    miso_bal = bal[bal["ba"] == "MISO"].copy()
    miso_bal["hour"] = hour_index(miso_bal["local"])
    miso_bal["year"] = (
        pd.to_datetime(miso_bal["local"]) - pd.Timedelta(hours=1)
    ).dt.year
    miso_bal = miso_bal[(miso_bal["hour"] >= 0) & (miso_bal["hour"] < HOURS)]
    nbr = bal[bal["ba"] != "MISO"].copy()

    report: dict = {
        "probe": "miso-237 phase 0 — price representation vs quantity channel on MISO's seams",
        "prereg": (
            "results/calibration/"
            "PREREG-miso237-price-representation-or-quantity-channel-2026-09-07.md"
            " (pushed 887c7cad)"
        ),
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "price_basis": (
            "Indiana hub RT builds the ok mask only (miso-236's hour set); every "
            "regressor is Indiana hub DA"
        ),
        "bars": {
            "provenance_tol_mw": PROVENANCE_TOL_MW,
            "provenance_tol_dr2": PROVENANCE_TOL_DR2,
            "rho_quantity_side": RHO_QUANTITY_BAR,
            "rho_price_representation": RHO_PRICE_BAR,
            "dr2_absolute_floor": DR2_ABS_FLOOR,
            "ventiles": VENTILES,
            "purge_candidate_cause": PURGE_CAUSE_BAR,
            "purge_refute": PURGE_REFUTE_BAR,
        },
        "gated_seams": {
            "neighbour_block": list(GATED_SEAMS_NEIGHBOUR),
            "own_block": list(GATED_SEAMS_OWN),
        },
        "seams_with_neighbour_price": list(SEAMS_WITH_NEIGHBOUR_PRICE),
        "years": {},
    }

    provenance: dict[str, dict] = {}
    years_out: dict[str, dict] = {}

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

        my = miso_bal[miso_bal["year"] == year].drop_duplicates("hour")
        hour_to_utc = pd.Series(my["utc"].to_numpy(), index=my["hour"].to_numpy())
        utc_grid = hour_to_utc.reindex(range(HOURS))

        def ba_series(bas: list[str], col: str) -> np.ndarray:
            sub = nbr[nbr["ba"].isin(bas)]
            agg = sub.groupby("utc")[col].sum(min_count=1)
            return agg.reindex(utc_grid.to_numpy()).to_numpy(float)

        def miso_series(col: str) -> np.ndarray:
            s = pd.Series(my[col].to_numpy(), index=my["hour"].to_numpy())
            return s.reindex(range(HOURS)).to_numpy(float)

        miso_nl = (miso_series("demand") - miso_series("wind") - miso_series("solar"))[
            ok
        ]
        miso_vre = (miso_series("wind") + miso_series("solar"))[ok]
        s_own = np.column_stack([_z(miso_nl), _z(miso_vre)])

        # Model-side reconstruction — miso-235's four-seam form, unchanged.
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
        p1_of = {
            "PJM": da - border,
            "SPP": da - spp_hub,
            "South": da,
            "Manitoba": da,
        }
        nbr_price_of = {"PJM": border, "SPP": spp_hub}

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

        # ---------------- PREREG §1 provenance gate ----------------
        prov: dict[str, dict] = {}
        for seam in FOUR_SEAM:
            p1 = p1_of[seam][ok]
            r_meas = ols_resid(meas_net[seam], p1)
            ref = prior235[str(year)]["decomposition"][seam]
            row = {
                "sigma_measured_mw": round(float(meas_net[seam].std()), 1),
                "sigma_measured_mw_miso235": ref["sigma_measured_mw"],
                "sigma_resid_measured_mw": round(float(r_meas.std()), 1),
                "sigma_resid_measured_mw_miso235": ref["sigma_resid_measured_mw"],
            }
            row["max_abs_delta_mw"] = round(
                max(
                    abs(row["sigma_measured_mw"] - ref["sigma_measured_mw"]),
                    abs(
                        row["sigma_resid_measured_mw"] - ref["sigma_resid_measured_mw"]
                    ),
                ),
                2,
            )
            # G-P2 — miso-236's gated delta, recomputed in miso-236's OWN metric.
            covered = covered_of[seam]
            ref236 = prior236[str(year)]["seams"][seam].get("delta_r2_A_nohydro")
            if covered and ref236 is not None:
                n_nl = (
                    ba_series(covered, "demand")
                    - ba_series(covered, "wind")
                    - ba_series(covered, "solar")
                )[ok]
                n_vre = (ba_series(covered, "wind") + ba_series(covered, "solar"))[ok]
                n_hyd = ba_series(covered, "hydro")[ok]
                good = np.isfinite(n_nl) & np.isfinite(n_vre) & np.isfinite(n_hyd)
                y236 = r_meas[good]
                bb = s_own[good]
                aa = np.column_stack([_z(n_nl[good]), _z(n_vre[good])])
                got = _r2_raw(y236, np.column_stack([bb, aa])) - _r2_raw(y236, bb)
                row["delta_r2_A_nohydro"] = round(got, 4)
                row["delta_r2_A_nohydro_miso236"] = ref236
                row["max_abs_delta_r2"] = round(abs(got - float(ref236)), 5)
            prov[seam] = row
        provenance[str(year)] = prov

        # ---------------- PREREG §2/§3/§4 — the nested blocks ----------------
        seams_out: dict[str, dict] = {}
        for seam in FOUR_SEAM:
            p1s = p1_of[seam][ok]
            P1 = _z(p1s)[:, None]
            P2 = np.column_stack([P1, ventile_dummies(p1s)])
            if seam in SEAMS_WITH_NEIGHBOUR_PRICE:
                P3 = np.column_stack(
                    [
                        P2,
                        ventile_dummies(da[ok]),
                        ventile_dummies(nbr_price_of[seam][ok]),
                    ]
                )
            else:
                P3 = (
                    P2  # declared data boundary (PREREG §2a): no neighbour price exists
                )

            x = meas_net[seam]
            r_meas = ols_resid(x, p1s)
            r_model = ols_resid(model_net[seam], p1s)

            def inc(y: np.ndarray, P: np.ndarray, S: np.ndarray) -> dict:
                """dof-ADJUSTED increment of state block ``S`` over price block ``P``."""
                base_raw, base_adj, base_k = r2_adj(y, P)
                full_raw, full_adj, full_k = r2_adj(y, np.column_stack([P, S]))
                return {
                    "base_r2_adj": round(base_adj, 4),
                    "base_rank": base_k,
                    "full_r2_adj": round(full_adj, 4),
                    "full_rank": full_k,
                    "delta_r2_adj": round(full_adj - base_adj, 4),
                    "delta_r2_raw": round(full_raw - base_raw, 4),
                }

            entry: dict = {"covered_dibas": covered_of[seam]}

            # --- Q-2(a): the own-state block, on every ok hour ---
            own = {p: inc(x, P, s_own) for p, P in (("P1", P1), ("P2", P2), ("P3", P3))}
            d1, d3 = own["P1"]["delta_r2_adj"], own["P3"]["delta_r2_adj"]
            own["rho_P3_over_P1"] = round(d3 / d1, 3) if d1 > 0 else None
            entry["own_state"] = own

            # --- Q-1: the neighbour-state block, on the finite neighbour hours ---
            covered = covered_of[seam]
            if covered:
                n_nl = (
                    ba_series(covered, "demand")
                    - ba_series(covered, "wind")
                    - ba_series(covered, "solar")
                )[ok]
                n_vre = (ba_series(covered, "wind") + ba_series(covered, "solar"))[ok]
                n_hyd = ba_series(covered, "hydro")[ok]
                good = np.isfinite(n_nl) & np.isfinite(n_vre) & np.isfinite(n_hyd)
                s_nbr = np.column_stack([_z(n_nl[good]), _z(n_vre[good])])
                xg = x[good]
                nb = {
                    p: inc(xg, P[good], s_nbr)
                    for p, P in (("P1", P1), ("P2", P2), ("P3", P3))
                }
                d1n, d3n = nb["P1"]["delta_r2_adj"], nb["P3"]["delta_r2_adj"]
                nb["rho_P3_over_P1"] = round(d3n / d1n, 3) if d1n > 0 else None
                nb["n_hours_block"] = int(good.sum())
                # Neighbour net-load sign on the P3-conditioned flow (REPORTED).
                A = _design(np.column_stack([P3[good], s_nbr]), int(good.sum()))
                nb["neighbour_net_load_coef_given_P3"] = round(
                    float(np.linalg.lstsq(A, xg, rcond=None)[0][-2]), 2
                )
                entry["neighbour_state"] = nb

            # --- Q-2(b)/(c): transmission check, model-side share, signs (REPORTED) ---
            pbus = bus_price[BUS_OF_SEAM[seam]][ok]
            entry["own_state_reported"] = {
                "r2_model_bus_price_on_own_state_adj": round(r2_adj(pbus, s_own)[1], 4),
                "r2_resid_measured_on_own_state_adj": round(
                    r2_adj(r_meas, s_own)[1], 4
                ),
                "r2_resid_model_on_own_state_adj": round(r2_adj(r_model, s_own)[1], 4),
                "own_net_load_coef_resid_measured": round(
                    float(
                        np.linalg.lstsq(
                            _design(s_own, len(r_meas)), r_meas, rcond=None
                        )[0][1]
                    ),
                    2,
                ),
                "own_net_load_coef_resid_model": round(
                    float(
                        np.linalg.lstsq(
                            _design(s_own, len(r_model)), r_model, rcond=None
                        )[0][1]
                    ),
                    2,
                ),
            }

            # --- Q-3: what a better price representation reaches (REPORTED, NOT GATED) ---
            _, a1, k1 = r2_adj(x, P1)
            _, a2, k2 = r2_adj(x, P2)
            _, a3, k3 = r2_adj(x, P3)
            entry["price_representation_reported_not_gated"] = {
                "r2_P1_adj": round(a1, 4),
                "r2_P2_adj": round(a2, 4),
                "r2_P3_adj": round(a3, 4),
                "delta_P2_over_P1": round(a2 - a1, 4),
                "delta_P3_over_P1": round(a3 - a1, 4),
                "ranks": [k1, k2, k3],
                "P3_equals_P2_by_data_boundary": seam not in SEAMS_WITH_NEIGHBOUR_PRICE,
            }

            # --- ADDENDUM §A: the own-state purge on the price-alignment defect ---
            # P is the Indiana-hub RT price, the scored basis miso-235 §4b used.
            def align(r: np.ndarray) -> float:
                return abs(float(np.corrcoef(r, act[ok])[0, 1]))

            a_model, a_meas = align(r_model), align(r_meas)
            a_model_p, a_meas_p = (
                align(purge(r_model, s_own)),
                align(purge(r_meas, s_own)),
            )
            gap = a_model - a_meas
            entry["own_state_purge_addendum_A"] = {
                "alignment_model": round(a_model, 4),
                "alignment_model_purged": round(a_model_p, 4),
                "alignment_measured": round(a_meas, 4),
                "alignment_measured_purged": round(a_meas_p, 4),
                "gap_model_minus_measured": round(gap, 4),
                "phi_movement_fraction": (
                    round((a_model - a_model_p) / gap, 3) if gap != 0 else None
                ),
                "gated": seam == PURGE_GATED_SEAM,
            }

            # --- ADDENDUM §B: rho under the OTHER block's conditioning ---
            cond: dict = {}
            if covered:
                base_o = {
                    p: np.column_stack([P, s_own]) for p, P in (("P1", P1), ("P3", P3))
                }
                dn = {}
                for p in ("P1", "P3"):
                    b = base_o[p][good]
                    dn[p] = (
                        r2_adj(xg, np.column_stack([b, s_nbr]))[1] - r2_adj(xg, b)[1]
                    )
                cond["rho_nbr_given_own"] = (
                    round(dn["P3"] / dn["P1"], 3) if dn["P1"] > 0 else None
                )
                cond["delta_r2_nbr_given_own"] = {p: round(v, 4) for p, v in dn.items()}
                do = {}
                for p, P in (("P1", P1), ("P3", P3)):
                    b = np.column_stack([P[good], s_nbr])
                    do[p] = (
                        r2_adj(xg, np.column_stack([b, s_own[good]]))[1]
                        - r2_adj(xg, b)[1]
                    )
                cond["rho_own_given_nbr"] = (
                    round(do["P3"] / do["P1"], 3) if do["P1"] > 0 else None
                )
                cond["delta_r2_own_given_nbr"] = {p: round(v, 4) for p, v in do.items()}
                entry["conditioned_addendum_B_reported_not_gated"] = cond
            seams_out[seam] = entry
        years_out[str(year)] = {"seams": seams_out}

    # ---------------- provenance verdict ----------------
    max_mw = max(
        p["max_abs_delta_mw"] for yr in provenance.values() for p in yr.values()
    )
    dr2_vals = [
        p["max_abs_delta_r2"]
        for yr in provenance.values()
        for p in yr.values()
        if "max_abs_delta_r2" in p
    ]
    max_dr2 = max(dr2_vals) if dr2_vals else 0.0
    report["provenance_gate"] = {
        "G_P1_max_abs_delta_mw": max_mw,
        "G_P1_tolerance_mw": PROVENANCE_TOL_MW,
        "G_P2_max_abs_delta_r2": round(max_dr2, 5),
        "G_P2_tolerance_r2": PROVENANCE_TOL_DR2,
        "G_P2_cells_checked": len(dr2_vals),
        "PASS": bool(max_mw <= PROVENANCE_TOL_MW and max_dr2 <= PROVENANCE_TOL_DR2),
        "by_year": provenance,
    }
    report["years"] = years_out

    # ---------------- PREREG §2b / §3a verdicts ----------------
    verdicts: dict[str, dict] = {}
    for seam in FOUR_SEAM:
        v: dict = {}
        for label, key, gated in (
            ("neighbour_state", "neighbour_state", seam in GATED_SEAMS_NEIGHBOUR),
            ("own_state", "own_state", seam in GATED_SEAMS_OWN),
        ):
            rows = [years_out[str(y)]["seams"][seam].get(key) for y in YEARS]
            if any(r is None for r in rows):
                v[label] = {"verdict": "NO BLOCK — data absence", "gated": gated}
                continue
            rhos = [r["rho_P3_over_P1"] for r in rows]
            d3 = [r["P3"]["delta_r2_adj"] for r in rows]
            d1 = [r["P1"]["delta_r2_adj"] for r in rows]
            v[label] = {
                "gated": gated,
                "verdict": (
                    _verdict([x for x in rhos if x is not None], d3)
                    if all(x is not None for x in rhos)
                    else "UNDEFINED — non-positive P1 increment"
                ),
                "rho_by_year": rhos,
                "delta_r2_P1_by_year": d1,
                "delta_r2_P3_by_year": d3,
            }
        verdicts[seam] = v
    report["verdicts"] = verdicts

    # --- ADDENDUM §A verdict, gated on PJM only ---
    phis = [
        years_out[str(y)]["seams"][PURGE_GATED_SEAM]["own_state_purge_addendum_A"][
            "phi_movement_fraction"
        ]
        for y in YEARS
    ]
    if any(p is None for p in phis):
        pv = "UNDEFINED — zero alignment gap"
    elif any(p < PURGE_REFUTE_BAR for p in phis):
        pv = "REFUTED AS THE CAUSE"
    elif all(p >= PURGE_CAUSE_BAR for p in phis):
        pv = "CANDIDATE CAUSE IDENTIFIED"
    else:
        pv = "PARTIAL"
    report["addendum_A_verdict"] = {
        "seam": PURGE_GATED_SEAM,
        "phi_by_year": phis,
        "verdict": pv,
        "note": (
            "Names an object for a successor's charter and charters nothing; phi is "
            "NEVER a tuning target (ADDENDUM §A)."
        ),
    }

    OUT.write_text(json.dumps(report, indent=2, default=float) + "\n")

    # ---------------- console readout ----------------
    g = report["provenance_gate"]
    print(
        f"PROVENANCE GATE  G-P1 max |delta| {g['G_P1_max_abs_delta_mw']:.2f} MW"
        f" (bar {PROVENANCE_TOL_MW})   G-P2 max |delta R2| {g['G_P2_max_abs_delta_r2']:.5f}"
        f" over {g['G_P2_cells_checked']} cells (bar {PROVENANCE_TOL_DR2})"
        f"  ->  {'PASS' if g['PASS'] else 'BROKEN'}"
    )
    if not g["PASS"]:
        print("instrument BROKEN — nothing below is read (PREREG §1)")
        return 1

    for label, title in (
        ("neighbour_state", "Q-1 — NEIGHBOUR state (GATED: SPP)"),
        ("own_state", "Q-2a — MISO's OWN state (GATED: PJM, SPP, South)"),
    ):
        print(f"\n{title}")
        print(
            f"  {'seam':<9} {'year':>5} {'dR2|P1':>8} {'dR2|P2':>8} {'dR2|P3':>8}"
            f" {'rho':>7}"
        )
        for seam in FOUR_SEAM:
            for y in YEARS:
                e = years_out[str(y)]["seams"][seam].get(label)
                if e is None:
                    print(f"  {seam:<9} {y:>5}   -- no block --")
                    continue
                rho = e["rho_P3_over_P1"]
                print(
                    f"  {seam:<9} {y:>5} {e['P1']['delta_r2_adj']:>8.4f}"
                    f" {e['P2']['delta_r2_adj']:>8.4f} {e['P3']['delta_r2_adj']:>8.4f}"
                    f" {('n/a' if rho is None else f'{rho:.3f}'):>7}"
                )

    print("\nQ-2b/c — transmission check and signs (REPORTED, NOT GATED)")
    print(
        f"  {'seam':<9} {'year':>5} {'R2(bus price|own)':>18} {'R2(r_meas|own)':>15}"
        f" {'R2(r_model|own)':>16} {'b_nl meas':>10} {'b_nl model':>11}"
    )
    for seam in FOUR_SEAM:
        for y in YEARS:
            e = years_out[str(y)]["seams"][seam]["own_state_reported"]
            print(
                f"  {seam:<9} {y:>5} {e['r2_model_bus_price_on_own_state_adj']:>18.4f}"
                f" {e['r2_resid_measured_on_own_state_adj']:>15.4f}"
                f" {e['r2_resid_model_on_own_state_adj']:>16.4f}"
                f" {e['own_net_load_coef_resid_measured']:>10.1f}"
                f" {e['own_net_load_coef_resid_model']:>11.1f}"
            )

    print(
        "\nQ-3 — reach of a better price representation (REPORTED, NOT GATED, NEVER A TARGET)"
    )
    print(
        f"  {'seam':<9} {'year':>5} {'R2(P1)':>8} {'R2(P2)':>8} {'R2(P3)':>8}"
        f" {'P2-P1':>8} {'P3-P1':>8}"
    )
    for seam in FOUR_SEAM:
        for y in YEARS:
            e = years_out[str(y)]["seams"][seam][
                "price_representation_reported_not_gated"
            ]
            tag = (
                "  (P3==P2, data boundary)"
                if e["P3_equals_P2_by_data_boundary"]
                else ""
            )
            print(
                f"  {seam:<9} {y:>5} {e['r2_P1_adj']:>8.4f} {e['r2_P2_adj']:>8.4f}"
                f" {e['r2_P3_adj']:>8.4f} {e['delta_P2_over_P1']:>8.4f}"
                f" {e['delta_P3_over_P1']:>8.4f}{tag}"
            )

    print("\nADDENDUM §A — own-state purge on the price alignment (GATED: PJM)")
    print(
        f"  {'seam':<9} {'year':>5} {'|corr| model':>13} {'purged':>8} {'measured':>9}"
        f" {'meas purged':>12} {'phi':>7}"
    )
    for seam in FOUR_SEAM:
        for y in YEARS:
            e = years_out[str(y)]["seams"][seam]["own_state_purge_addendum_A"]
            phi = e["phi_movement_fraction"]
            print(
                f"  {seam:<9} {y:>5} {e['alignment_model']:>13.4f}"
                f" {e['alignment_model_purged']:>8.4f} {e['alignment_measured']:>9.4f}"
                f" {e['alignment_measured_purged']:>12.4f}"
                f" {('n/a' if phi is None else f'{phi:.3f}'):>7}"
            )
    av = report["addendum_A_verdict"]
    print(f"  -> PJM verdict: {av['verdict']}  (phi {av['phi_by_year']})")

    print(
        "\nADDENDUM §B — rho under the OTHER block's conditioning (REPORTED, NOT GATED)"
    )
    print(
        f"  {'seam':<9} {'year':>5} {'rho_nbr (pre)':>14} {'rho_nbr|own':>12}"
        f" {'rho_own (pre)':>14} {'rho_own|nbr':>12}"
    )
    for seam in FOUR_SEAM:
        for y in YEARS:
            se = years_out[str(y)]["seams"][seam]
            c = se.get("conditioned_addendum_B_reported_not_gated")
            if not c:
                continue
            pre_n = se["neighbour_state"]["rho_P3_over_P1"]
            pre_o = se["own_state"]["rho_P3_over_P1"]

            def f(v: float | None) -> str:
                return "n/a" if v is None else f"{v:.3f}"

            print(
                f"  {seam:<9} {y:>5} {f(pre_n):>14} {f(c['rho_nbr_given_own']):>12}"
                f" {f(pre_o):>14} {f(c['rho_own_given_nbr']):>12}"
            )

    print("\nVERDICTS (pre-registered bars)")
    for seam, v in verdicts.items():
        for label, row in v.items():
            print(
                f"  {seam:<9} {label:<16} {row['verdict']}"
                f"  ({'GATED' if row['gated'] else 'reported'})"
            )
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
