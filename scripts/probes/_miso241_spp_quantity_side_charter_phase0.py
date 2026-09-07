"""miso-241 phase 0 — the SPP quantity-side charter: does a DOF-free form exist? Zero LP.

Pre-registration:
``results/calibration/PREREG-miso241-the-spp-quantity-side-charter-2026-09-07.md``
(pushed at ``6fbc5e83``, before any adjudicating quantity), extended by
``results/calibration/ADDENDUM-miso241-the-q2-instrument-gate-2026-09-07.md``
(pushed before the numbers it governs). Every decision rule applied here is fixed in one
of those two documents; nothing below selects anything.

The queue item is miso-237's named successor: neighbour net load and VRE explain 32/25/11 %
of the MEASURED SPP seam residual over and above everything MISO's own state explains
(miso-236), and a strictly richer price representation does not reach it (miso-237), so the
channel is quantity-side. What a charter owes at zero LP is the mechanism's own FORM, and
that cannot be answered without knowing which LP object actually sets the SPP seam's
quantity. Four legs:

* **Provenance gate (PREREG §1, seven legs + the ADDENDUM's G-P6).** miso-235's sigma
  column, miso-236's gated delta_r2, miso-235's incumbent harness, miso-238's PJM
  sat_share, miso-239's PJM gamma_MERIT, the PJM export leg's identical zero, the
  prefix/band-count identity on both legs of both reconstructions, and the Q-2 grid's
  exact reproduction of the committed envelope. If any leg fails the instrument is BROKEN
  and nothing in Q-1/Q-2/Q-3 is read.
* **Q-0 (PREREG §2).** The lane's four-seam reconstruction prices EVERY seam's export leg
  from the incumbent MISO-hub table against the bus-price LEVEL, while the keeper prices
  the PJM and SPP export bands at ``neighbour_hub(t) + delta_k^export`` against the SPREAD
  (PREREG §0 facts F2/F3/F4). Both variants are built and miso-235's own I-1/I-2
  superseding rule decides which one Q-1 reads.
* **Q-1 (PREREG §3).** Which argument of ``flow = min(env^eff, n*w)`` binds, per leg per
  hour, on the SPP seam: is its quantity CEILING-SET or MERIT-SET?
* **Q-2 (PREREG §4).** Does the envelope's OWN p90 estimator, on a partition refined by
  neighbour state, carry measurable signal? Measured data only, with a 200-permutation
  within-bucket null.

Basis discipline (PREREG §0b): the Indiana-hub **RT** series builds the finite-hour ``ok``
mask byte-identically to miso-236/237/238/239/240; every merit signal and regressor is the
Indiana-hub **DA**; the SPP anchor is the measured SPP NORTH hub DA. They are never
interchanged.

Usage: python3 scripts/probes/_miso241_spp_quantity_side_charter_phase0.py
"""

from __future__ import annotations

import importlib
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
CAL = REPO / "results/calibration"
MISO235 = CAL / "_miso235_seam_variance_decomposition_phase0.json"
MISO236 = CAL / "_miso236_neighbour_state_residual_phase0.json"
MISO238 = CAL / "_miso238_pjm_seam_channel_attribution_phase0.json"
MISO239 = CAL / "_miso239_merit_ladder_property_attribution_phase0.json"
OUT = CAL / "_miso241_spp_quantity_side_charter_phase0.json"

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
GATED_SEAM = "SPP"

# ---- PREREG §1 bars, fixed ex ante ----
TOL_SIGMA_MW = 0.5  # G-P1
TOL_DR2 = 0.005  # G-P2
TOL_CORR = 0.002  # G-P3 (corr leg)
TOL_LEVEL_MW = 0.5  # G-P3 (level leg)
TOL_SAT = 0.002  # G-P4
TOL_GAMMA = 0.5  # G-P5
TOL_ID_MW = 1e-6  # G-ID
TOL_ENV_MW = 1e-6  # G-P6 (ADDENDUM §A)

# ---- PREREG §3 bars, fixed ex ante ----
Q1_CEILING_BAR = 0.50
Q1_MERIT_BAR = 0.10

# ---- PREREG §4 bars, fixed ex ante ----
Q2_MIN_SAMPLES = 12
Q2_N_PERM = 200
Q2_SEED = 20260907
Q2_Z_BAR = 3.0
Q2_MATERIAL_FRAC = 0.10
Q2_INERT_FRAC = 0.02

# PREREG §1 reference values, restated HERE so the gate binds even if a predecessor
# artifact is missing (the PREREG's "survive the artifact being absent" duty).
REF_SAT_SHARE_PJM = (0.1740, 0.0068, 0.0000)
REF_GAMMA_MERIT_PJM = (-870.18, -930.93, -791.43)
REF_HARNESS_CORR4 = (0.9845, 0.9745, 0.9839)
REF_HARNESS_LEVEL4 = (49.4, 41.6, 55.3)

_MONTH_LEN = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

M8 = importlib.import_module("_miso238_pjm_seam_channel_attribution_phase0")
M6 = importlib.import_module("_miso236_neighbour_state_residual_phase0")

ols_resid = M8.ols_resid
gamma = M8.gamma
_z = M8._z
hour_index = M8.hour_index
load_balance = M6.load_balance
_r2 = M6._r2


def _json(path: Path):
    """Committed predecessor artifact, or ``None`` when absent (gate reports SKIPPED)."""
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def p90(vals: np.ndarray, pct: float) -> float:
    """The envelope's own estimator — ``np.percentile`` on the bucket's raw sample."""
    return float(np.percentile(vals, pct))


def build_recons(
    seam: str,
    year: int,
    pb: np.ndarray,
    anchors: dict[str, np.ndarray],
    env_i: dict[str, np.ndarray],
    env_e: dict[str, np.ndarray],
    width: float,
    ks: np.ndarray,
    ladders: dict,
) -> dict:
    """Both export variants of one seam's reconstruction, plus the identity operands.

    Returns per-variant ``imp``/``exp``/``net`` and the in-merit counts and effective
    ceilings the PREREG §3 classifier and the G-ID identity both read. The IMPORT leg is
    identical in both variants (only the export pricing differs, PREREG §2).
    """
    (LAD, HOURLY, HOURLY_SPP) = ladders
    # --- import leg (identical in both variants) ---
    if seam == "PJM":
        d_i = np.asarray(HOURLY[year]["PJM"]["import"], float)
        sig_i = pb - anchors["PJM"]
    elif seam == "SPP":
        d_i = np.asarray(HOURLY_SPP[year]["SPP"]["import"], float)
        sig_i = pb - anchors["SPP"]
    else:
        d_i = np.asarray(LAD[year][seam]["import"], float)
        sig_i = pb
    mi = (sig_i[None, :] > d_i[:, None]).astype(float)
    ei = np.asarray(env_i[seam], float)
    bi = np.clip(ei[None, :] - ks * width, 0.0, width)
    imp = (mi * bi).sum(0)

    ee = np.asarray(env_e[seam], float)
    be = np.clip(ee[None, :] - ks * width, 0.0, width)
    lad_e = np.asarray(LAD[year][seam]["export"], float)

    # INCUMBENT export leg — the lane's reconstruction, byte-for-byte (miso-235 line 237).
    me_inc = (pb[None, :] < lad_e[:, None]).astype(float)
    exp_inc = (me_inc * be).sum(0)

    # REPAIRED export leg — what the keeper's `_inject_seam_ladder` actually applies.
    if seam == "PJM":
        d_e = np.asarray(HOURLY[year]["PJM"]["export"], float)
        cost_e = anchors["PJM"][None, :] + d_e[:, None]
    elif seam == "SPP":
        d_e = np.asarray(HOURLY_SPP[year]["SPP"]["export"], float)
        cost_e = anchors["SPP"][None, :] + d_e[:, None]
    else:
        cost_e = np.broadcast_to(lad_e[:, None], (len(lad_e), len(pb)))
    me_rep = (pb[None, :] < cost_e).astype(float)
    exp_rep = (me_rep * be).sum(0)

    lim = width * ks.size
    return {
        "imp": imp,
        "exp_incumbent": exp_inc,
        "exp_repaired": exp_rep,
        "net_incumbent": imp - exp_inc,
        "net_repaired": imp - exp_rep,
        "n_i": mi.sum(0),
        "n_e_incumbent": me_inc.sum(0),
        "n_e_repaired": me_rep.sum(0),
        "env_i_eff": np.minimum(ei, lim),
        "env_e_eff": np.minimum(ee, lim),
        "mi": mi,
        "me_incumbent": me_inc,
        "me_repaired": me_rep,
    }


def identity_check(flow, n, env_eff, width) -> tuple[float, int]:
    """``flow == min(env^eff, n*w)`` (max |Δ| MW) and the prefix-violation hour count.

    The identity holds only if the in-merit set is the prefix ``{0..n-1}``; the second
    return value counts the hours in which it is not, gated at zero (PREREG §1, G-ID).
    """
    pred = np.minimum(env_eff, n * width)
    d = float(np.abs(flow - pred).max())
    return d, int((np.abs(flow - pred) > TOL_ID_MW).sum())


def classify_leg(n: np.ndarray, env_eff: np.ndarray, width: float) -> dict:
    """PREREG §3: which argument of the ``min`` binds, per hour.

    CEILING-SET iff ``env^eff <= n*w`` and ``n >= 1`` (a marginal ceiling change moves the
    leg); MERIT-SET iff ``n*w < env^eff`` (including ``n == 0``); exact ties counted as
    CEILING-SET and reported separately.
    """
    nw = n * width
    ceiling = (env_eff <= nw) & (n >= 1)
    tie = (env_eff == nw) & (n >= 1)
    return {
        "ceiling": ceiling,
        "merit": ~ceiling,
        "share_ceiling_set": float(ceiling.mean()),
        "share_merit_set": float((~ceiling).mean()),
        "share_tie": float(tie.mean()),
        "share_n_zero": float((n == 0).mean()),
        "mean_n": float(n.mean()),
    }


def tercile_spread(
    flow: np.ndarray,
    cond: np.ndarray,
    bucket: np.ndarray,
    pct: float,
) -> dict:
    """PREREG §4: the sample-weighted mean ``p90(T3) - p90(T1)`` and its permutation null.

    Within every ``(month x hod)`` bucket carrying at least ``Q2_MIN_SAMPLES`` finite
    paired samples, split by tercile of ``cond`` and take the SAME percentile the envelope
    uses in each tercile. The null permutes ``cond`` WITHIN each bucket, so it holds the
    bucket structure, the sample sizes and the flow distribution fixed and varies only the
    conditioning — the exact thing the candidate claims to use.
    """
    rng = np.random.default_rng(Q2_SEED)  # fresh per call: order-independent
    good = np.isfinite(flow) & np.isfinite(cond)
    flow, cond, bucket = flow[good], cond[good], bucket[good]
    order = np.argsort(bucket, kind="stable")
    flow, cond, bucket = flow[order], cond[order], bucket[order]
    edges = np.flatnonzero(np.diff(bucket)) + 1
    groups = np.split(np.arange(len(bucket)), edges)
    groups = [g for g in groups if len(g) >= Q2_MIN_SAMPLES]
    if not groups:
        return {"n_buckets": 0, "spread_mw": None, "z": None}

    def one(perm: bool) -> float:
        num = 0.0
        den = 0
        for g in groups:
            f = flow[g]
            c = rng.permutation(cond[g]) if perm else cond[g]
            k = len(g) // 3
            idx = np.argsort(c, kind="stable")
            lo, hi = f[idx[:k]], f[idx[len(g) - k :]]
            num += (p90(hi, pct) - p90(lo, pct)) * len(g)
            den += len(g)
        return num / den if den else 0.0

    real = one(False)
    null = np.array([one(True) for _ in range(Q2_N_PERM)])
    sd = float(null.std(ddof=1))
    return {
        "n_buckets": len(groups),
        "n_hours": int(sum(len(g) for g in groups)),
        "spread_mw": round(real, 2),
        "null_mean_mw": round(float(null.mean()), 2),
        "null_sd_mw": round(sd, 2),
        "z": round((real - float(null.mean())) / sd, 2) if sd > 0 else None,
    }


def main() -> int:  # noqa: PLR0912, PLR0915 - one linear probe, PREREG section order
    from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
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

    from _miso224_floor_anatomy_phase0 import actual_zone_price

    ladders = (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )
    pct = float(MISO_SEAM_FLOW_PERCENTILE)

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()

    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}
    specs["Manitoba"] = MISO_MANITOBA_SEAM_SPEC

    prior235 = _json(MISO235)
    prior236 = _json(MISO236)
    prior238 = _json(MISO238)
    prior239 = _json(MISO239)

    bal = load_balance()
    bal_bas = set(bal["ba"].unique())
    miso_bal = bal[bal["ba"] == "MISO"].copy()
    miso_bal["hour"] = hour_index(miso_bal["local"])
    miso_bal["year"] = (
        pd.to_datetime(miso_bal["local"]) - pd.Timedelta(hours=1)
    ).dt.year
    miso_bal = miso_bal[(miso_bal["hour"] >= 0) & (miso_bal["hour"] < HOURS)]
    miso_all = bal[bal["ba"] == "MISO"].copy()
    nbr = bal[bal["ba"] != "MISO"].copy()

    # --- the raw interchange rows, on the ENVELOPE's own key (ADDENDUM §A) ---
    raw = pd.read_parquet(INTERCHANGE)
    raw_local_end = pd.DatetimeIndex(raw["local_time"])
    raw_local_beg = raw_local_end - pd.Timedelta(hours=1)
    diba_to_seam = {d: s for s, ds in MISO_SEAM_DIBA.items() for d in ds}
    raw = raw.assign(
        seam=raw["diba"].astype(str).map(diba_to_seam),
        ts_beg=raw_local_beg,
        mwv=pd.to_numeric(raw["mw"], errors="coerce"),
    ).dropna(subset=["seam", "mwv"])
    per_ts = raw.groupby(["seam", "ts_beg"], observed=True)["mwv"].sum().reset_index()
    per_ts["net_import"] = -per_ts["mwv"]
    per_ts["year"] = per_ts["ts_beg"].dt.year
    per_ts["month"] = per_ts["ts_beg"].dt.month
    per_ts["hod"] = per_ts["ts_beg"].dt.hour

    report = {
        "probe": "miso-241 phase 0 — the SPP quantity-side charter: does a DOF-free form exist?",
        "prereg": (
            "results/calibration/PREREG-miso241-the-spp-quantity-side-charter-2026-09-07.md"
            " (pushed 6fbc5e83)"
        ),
        "addendum": (
            "results/calibration/ADDENDUM-miso241-the-q2-instrument-gate-2026-09-07.md"
        ),
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "gated_seam": GATED_SEAM,
        "price_basis": (
            "ok mask = Indiana hub RT finite; every merit signal and regressor = Indiana "
            "hub DA; SPP anchor = measured SPP NORTH hub DA"
        ),
        "bars": {
            "tol_sigma_mw": TOL_SIGMA_MW,
            "tol_delta_r2": TOL_DR2,
            "tol_corr": TOL_CORR,
            "tol_level_mw": TOL_LEVEL_MW,
            "tol_sat_share": TOL_SAT,
            "tol_gamma_mw_per_z": TOL_GAMMA,
            "tol_identity_mw": TOL_ID_MW,
            "tol_envelope_mw": TOL_ENV_MW,
            "q1_ceiling_bar": Q1_CEILING_BAR,
            "q1_merit_bar": Q1_MERIT_BAR,
            "q2_min_samples": Q2_MIN_SAMPLES,
            "q2_n_perm": Q2_N_PERM,
            "q2_seed": Q2_SEED,
            "q2_z_bar": Q2_Z_BAR,
            "q2_material_frac": Q2_MATERIAL_FRAC,
            "q2_inert_frac": Q2_INERT_FRAC,
        },
        "predecessor_artifacts": {
            "miso235": MISO235.name if prior235 else "ABSENT",
            "miso236": MISO236.name if prior236 else "ABSENT",
            "miso238": MISO238.name if prior238 else "ABSENT",
            "miso239": MISO239.name if prior239 else "ABSENT",
        },
        "years": {},
    }

    prov: dict[str, dict] = {}
    years_out: dict[str, dict] = {}

    for yi, year in enumerate(YEARS):
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
        anchors = {"PJM": border, "SPP": spp_hub}

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus_price = {
            b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
            for b in set(BUS_OF_SEAM.values())
        }
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
        committed = (
            cls.groupby("hour")["mw"]
            .sum()
            .reindex(range(HOURS))
            .fillna(0.0)
            .to_numpy(float)
        )[ok]

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

        R: dict[str, dict] = {}
        widths: dict[str, float] = {}
        for seam in FOUR_SEAM:
            widths[seam] = float(specs[seam].interface_limit_mw) / SEAM_FLOW_TRANCHES
            R[seam] = build_recons(
                seam,
                year,
                bus_price[BUS_OF_SEAM[seam]],
                anchors,
                env_i,
                env_e,
                widths[seam],
                ks,
                ladders,
            )

        meas_net = {s: dense(s) for s in FOUR_SEAM}

        # ================= §1 PROVENANCE GATE =================
        pv: dict[str, dict] = {}

        # G-P1 — miso-235's sigma column.
        gp1 = {}
        worst1 = 0.0
        for seam in FOUR_SEAM:
            m = meas_net[seam][ok]
            r_m = ols_resid(m, regressor[seam][ok])
            row = {
                "sigma_measured_mw": round(float(m.std()), 1),
                "sigma_resid_measured_mw": round(float(r_m.std()), 1),
            }
            if prior235:
                ref = prior235["years"][str(year)]["decomposition"][seam]
                row["miso235_sigma_measured_mw"] = ref["sigma_measured_mw"]
                row["miso235_sigma_resid_measured_mw"] = ref["sigma_resid_measured_mw"]
                d = max(
                    abs(row["sigma_measured_mw"] - ref["sigma_measured_mw"]),
                    abs(
                        row["sigma_resid_measured_mw"] - ref["sigma_resid_measured_mw"]
                    ),
                )
                row["abs_delta_mw"] = round(d, 3)
                worst1 = max(worst1, d)
            gp1[seam] = row
        pv["G_P1"] = {
            "seams": gp1,
            "max_abs_delta_mw": round(worst1, 3) if prior235 else None,
            "status": "SKIPPED — artifact absent" if not prior235 else None,
        }

        # G-P3 — miso-235's INCUMBENT four-seam harness.
        rec4_inc = sum(R[s]["net_incumbent"][ok] for s in FOUR_SEAM)
        rec4_rep = sum(R[s]["net_repaired"][ok] for s in FOUR_SEAM)
        harness = {}
        for tag, rec in (("incumbent", rec4_inc), ("repaired", rec4_rep)):
            harness[tag] = {
                "corr_recon_vs_committed": round(
                    float(np.corrcoef(rec, committed)[0, 1]), 4
                ),
                "mean_abs_level_error_mw": round(
                    abs(float(rec.mean() - committed.mean())), 1
                ),
                "recon_mean_mw": round(float(rec.mean()), 1),
                "recon_sigma_mw": round(float(rec.std()), 1),
            }
        ref_c = (
            prior235["years"][str(year)]["instrument"]["four_seam"]
            if prior235
            else None
        )
        pv["G_P3"] = {
            "corr_recomputed": harness["incumbent"]["corr_recon_vs_committed"],
            "corr_reference": (
                ref_c["harness_corr_recon_vs_committed"]
                if ref_c
                else REF_HARNESS_CORR4[yi]
            ),
            "level_recomputed": harness["incumbent"]["mean_abs_level_error_mw"],
            "level_reference": (
                ref_c["mean_abs_level_error_mw"] if ref_c else REF_HARNESS_LEVEL4[yi]
            ),
        }
        pv["G_P3"]["abs_delta_corr"] = round(
            abs(pv["G_P3"]["corr_recomputed"] - pv["G_P3"]["corr_reference"]), 4
        )
        pv["G_P3"]["abs_delta_level_mw"] = round(
            abs(pv["G_P3"]["level_recomputed"] - pv["G_P3"]["level_reference"]), 2
        )

        # G-P4 / G-P5 / G-X0 — the PJM legs, on miso-238's own predicates.
        my = miso_bal[miso_bal["year"] == year].drop_duplicates("hour")

        def miso_series(col: str) -> np.ndarray:
            s = pd.Series(my[col].to_numpy(), index=my["hour"].to_numpy())
            return s.reindex(range(HOURS)).to_numpy(float)

        miso_nl = (miso_series("demand") - miso_series("wind") - miso_series("solar"))[
            ok
        ]
        miso_vre = (miso_series("wind") + miso_series("solar"))[ok]
        s_own = np.column_stack([_z(miso_nl), _z(miso_vre)])

        # G-P2 — miso-236's gated delta_r2_A_nohydro, recomputed on this code path in
        # miso-236's OWN metric: the neighbour block's increment over MISO's own block on
        # the single-spread MEASURED residual, z-scored exactly as miso-236 z-scores it.
        hour_to_utc = pd.Series(my["utc"].to_numpy(), index=my["hour"].to_numpy())
        utc_grid = hour_to_utc.reindex(range(HOURS))

        def ba_series(bas: list[str], col: str) -> np.ndarray:
            sub = nbr[nbr["ba"].isin(bas)]
            agg = sub.groupby("utc")[col].sum(min_count=1)
            return agg.reindex(utc_grid.to_numpy()).to_numpy(float)

        dr2: dict[str, dict] = {}
        for seam in FOUR_SEAM:
            covered = [b for b in MISO_SEAM_DIBA[seam] if b in bal_bas]
            if not covered:
                dr2[seam] = {"status": "NO NEIGHBOUR-STATE INSTRUMENT"}
                continue
            r_meas_s = ols_resid(meas_net[seam][ok], regressor[seam][ok])
            n_nl = (
                ba_series(covered, "demand")
                - ba_series(covered, "wind")
                - ba_series(covered, "solar")
            )
            n_vre = ba_series(covered, "wind") + ba_series(covered, "solar")
            n_hyd = ba_series(covered, "hydro")
            good = (
                np.isfinite(n_nl[ok]) & np.isfinite(n_vre[ok]) & np.isfinite(n_hyd[ok])
            )
            yv = r_meas_s[good]
            bb = s_own[good]
            a_nh = np.column_stack([_z(n_nl[ok][good]), _z(n_vre[ok][good])])
            r2_b = _r2(yv, bb)
            r2_ab = _r2(yv, np.column_stack([bb, a_nh]))
            row = {"delta_r2_A_nohydro": round(r2_ab - r2_b, 4)}
            if prior236:
                ref = prior236["years"][str(year)]["seams"][seam].get(
                    "delta_r2_A_nohydro"
                )
                if ref is not None:
                    row["miso236"] = ref
                    row["abs_delta"] = round(abs(row["delta_r2_A_nohydro"] - ref), 5)
            dr2[seam] = row
        pv["G_P2"] = dr2

        sat = (R["PJM"]["n_i"][ok] >= SEAM_FLOW_TRANCHES).mean()
        ref_sat = (
            prior238["years"][str(year)]["seams"]["PJM"][
                "saturation_census_reported_not_gated"
            ]["sat_share"]
            if prior238
            else REF_SAT_SHARE_PJM[yi]
        )
        pv["G_P4"] = {
            "sat_share_recomputed": round(float(sat), 4),
            "reference": ref_sat,
            "abs_delta": round(abs(float(sat) - float(ref_sat)), 4),
        }

        # miso-239's gamma_MERIT: MERIT = sum_k (m_k - mbar_k) * bbar_k on PJM.
        mi_pjm = R["PJM"]["mi"][:, ok]
        bi_pjm = np.clip(
            np.asarray(env_i["PJM"], float)[None, :] - ks * widths["PJM"],
            0.0,
            widths["PJM"],
        )[:, ok]
        b_bar = bi_pjm.mean(axis=1)
        m_bar = mi_pjm.mean(axis=1)
        merit_pjm = ((mi_pjm - m_bar[:, None]) * b_bar[:, None]).sum(0)
        p1s = (da - border)[ok]
        g_merit = gamma(ols_resid(merit_pjm, p1s), s_own)
        ref_g = (
            prior239["years"][str(year)]["gamma_merit_mw_per_z"]
            if prior239
            else REF_GAMMA_MERIT_PJM[yi]
        )
        pv["G_P5"] = {
            "gamma_merit_recomputed": round(g_merit, 2),
            "reference": ref_g,
            "abs_delta": round(abs(g_merit - float(ref_g)), 3),
        }

        pv["G_X0"] = {
            "pjm_export_leg_max_abs_mw_incumbent": round(
                float(np.abs(R["PJM"]["exp_incumbent"][ok]).max()), 6
            ),
            "pjm_export_leg_max_abs_mw_repaired": round(
                float(np.abs(R["PJM"]["exp_repaired"][ok]).max()), 6
            ),
            "pjm_export_leg_nonzero_hours_repaired": int(
                (np.abs(R["PJM"]["exp_repaired"][ok]) > 1e-9).sum()
            ),
            "spp_export_leg_nonzero_hours_incumbent": int(
                (np.abs(R["SPP"]["exp_incumbent"][ok]) > 1e-9).sum()
            ),
            "spp_export_leg_nonzero_hours_repaired": int(
                (np.abs(R["SPP"]["exp_repaired"][ok]) > 1e-9).sum()
            ),
        }

        # G-ID — the prefix identity on both legs of both variants, all four seams.
        idmax = 0.0
        idviol = 0
        idrows = {}
        for seam in FOUR_SEAM:
            w = widths[seam]
            legs = {
                "import": (R[seam]["imp"], R[seam]["n_i"], R[seam]["env_i_eff"]),
                "export_incumbent": (
                    R[seam]["exp_incumbent"],
                    R[seam]["n_e_incumbent"],
                    R[seam]["env_e_eff"],
                ),
                "export_repaired": (
                    R[seam]["exp_repaired"],
                    R[seam]["n_e_repaired"],
                    R[seam]["env_e_eff"],
                ),
            }
            row = {}
            for tag, (f, n, e) in legs.items():
                d, v = identity_check(f[ok], n[ok], e[ok], w)
                row[tag] = {"max_abs_mw": float(f"{d:.3e}"), "violations": v}
                idmax = max(idmax, d)
                idviol += v
            idrows[seam] = row
        pv["G_ID"] = {
            "seams": idrows,
            "max_abs_mw": float(f"{idmax:.3e}"),
            "total_prefix_violations": idviol,
        }

        # G-P6 (ADDENDUM §A) — the Q-2 grid reproduces the committed envelope exactly.
        py = per_ts[per_ts["year"] == year]
        env_delta = {}
        for seam in FOUR_SEAM:
            sub = py[py["seam"] == seam]
            if sub.empty:
                env_delta[seam] = None
                continue
            worst = 0.0
            for direction, env in (("import", env_i), ("export", env_e)):
                tab = np.full((12, 24), np.nan)
                for (m, h), g in sub.groupby(["month", "hod"], observed=True):
                    v = g["net_import"].to_numpy(float)
                    tab[m - 1, h] = p90(-v if direction == "export" else v, pct)
                got = env.get(seam)
                if got is None:
                    continue
                # Compare on the model clock the envelope itself emits.
                rm = np.repeat(np.arange(12), [24 * d for d in _MONTH_LEN])
                rh = np.arange(HOURS) % 24
                mine = np.clip(tab[rm, rh], 0.0, None)
                fin = np.isfinite(mine)
                worst = max(
                    worst, float(np.abs(mine[fin] - np.asarray(got, float)[fin]).max())
                )
            env_delta[seam] = float(f"{worst:.3e}")
        pv["G_P6"] = {"per_seam_max_abs_mw": env_delta}

        prov[str(year)] = pv

        # ================= Q-0 (PREREG §2) =================
        q0 = {"harness": harness}
        per_seam = {}
        for seam in FOUR_SEAM:
            d = R[seam]
            disagree = np.abs(d["exp_incumbent"][ok] - d["exp_repaired"][ok]) > 1e-9
            per_seam[seam] = {
                "export_incumbent_mean_mw": round(
                    float(d["exp_incumbent"][ok].mean()), 1
                ),
                "export_repaired_mean_mw": round(
                    float(d["exp_repaired"][ok].mean()), 1
                ),
                "export_incumbent_sigma_mw": round(
                    float(d["exp_incumbent"][ok].std()), 1
                ),
                "export_repaired_sigma_mw": round(
                    float(d["exp_repaired"][ok].std()), 1
                ),
                "export_disagree_share": round(float(disagree.mean()), 4),
                "net_incumbent_mean_mw": round(float(d["net_incumbent"][ok].mean()), 1),
                "net_repaired_mean_mw": round(float(d["net_repaired"][ok].mean()), 1),
                "net_incumbent_sigma_mw": round(float(d["net_incumbent"][ok].std()), 1),
                "net_repaired_sigma_mw": round(float(d["net_repaired"][ok].std()), 1),
                "measured_sigma_mw": round(float(meas_net[seam][ok].std()), 1),
            }
        q0["per_seam"] = per_seam

        # miso-235 §4's own statistic, both variants (PREREG §2.3).
        rows235 = {}
        for seam in FOUR_SEAM:
            z = regressor[seam][ok]
            zc = z - z.mean()
            vz = float((zc * zc).mean())
            m = meas_net[seam][ok]
            b_meas = float(((m - m.mean()) * zc).mean() / vz) if vz > 0 else 0.0
            row = {
                "beta_measured": round(b_meas, 2),
                "sigma_resid_measured_mw": round(float(ols_resid(m, z).std()), 1),
            }
            for tag in ("incumbent", "repaired"):
                x = R[seam][f"net_{tag}"][ok]
                b = float(((x - x.mean()) * zc).mean() / vz) if vz > 0 else 0.0
                sr = float(ols_resid(x, z).std())
                row[tag] = {
                    "beta_model": round(b, 2),
                    "beta_ratio": round(b / b_meas, 2) if b_meas != 0 else None,
                    "sigma_model_mw": round(float(x.std()), 1),
                    "sigma_resid_model_mw": round(sr, 1),
                    "sigma_resid_ratio": (
                        round(sr / row["sigma_resid_measured_mw"], 2)
                        if row["sigma_resid_measured_mw"] > 0
                        else None
                    ),
                }
            rows235[seam] = row
        q0["miso235_s4_rows_both_variants"] = rows235

        # miso-235 §5's contribution-to-correlation ratios, both variants.
        p_rt = act[ok]
        sp = float(p_rt.std())

        contribs = {}
        for tag in ("incumbent", "repaired"):
            tot = sum(R[s][f"net_{tag}"][ok] for s in FOUR_SEAM)
            st = float(tot.std())
            contribs[tag] = {
                s: round(
                    float(
                        np.cov(R[s][f"net_{tag}"][ok], p_rt, bias=True)[0, 1]
                        / (sp * st)
                    ),
                    4,
                )
                for s in FOUR_SEAM
            }
            contribs[tag]["TOTAL"] = round(float(np.corrcoef(tot, p_rt)[0, 1]), 4)
        mtot = sum(meas_net[s][ok] for s in FOUR_SEAM)
        smt = float(mtot.std())
        contribs["measured"] = {
            s: round(
                float(np.cov(meas_net[s][ok], p_rt, bias=True)[0, 1] / (sp * smt)), 4
            )
            for s in FOUR_SEAM
        }
        contribs["measured"]["TOTAL"] = round(float(np.corrcoef(mtot, p_rt)[0, 1]), 4)
        contribs["committed_total"] = round(
            float(np.corrcoef(committed, p_rt)[0, 1]), 4
        )
        q0["miso235_s5_contributions"] = contribs

        # ================= Q-1 (PREREG §3) =================
        q1 = {}
        for seam in FOUR_SEAM:
            w = widths[seam]
            leg_i = classify_leg(R[seam]["n_i"][ok], R[seam]["env_i_eff"][ok], w)
            entry = {
                "import": {
                    k: v for k, v in leg_i.items() if not isinstance(v, np.ndarray)
                }
            }
            for tag in ("incumbent", "repaired"):
                leg_e = classify_leg(
                    R[seam][f"n_e_{tag}"][ok], R[seam]["env_e_eff"][ok], w
                )
                both = leg_i["ceiling"] | leg_e["ceiling"]
                entry[f"export_{tag}"] = {
                    k: v for k, v in leg_e.items() if not isinstance(v, np.ndarray)
                }
                entry[f"ceiling_active_share_{tag}"] = round(float(both.mean()), 4)
                entry[f"merit_active_share_{tag}"] = round(float((~both).mean()), 4)
            entry["env_i_mean_mw"] = round(float(R[seam]["env_i_eff"][ok].mean()), 1)
            entry["env_i_sigma_mw"] = round(float(R[seam]["env_i_eff"][ok].std()), 1)
            entry["env_e_mean_mw"] = round(float(R[seam]["env_e_eff"][ok].mean()), 1)
            entry["env_e_sigma_mw"] = round(float(R[seam]["env_e_eff"][ok].std()), 1)
            for tag in ("incumbent", "repaired"):
                both_zero = (R[seam]["n_i"][ok] == 0) & (R[seam][f"n_e_{tag}"][ok] == 0)
                entry[f"share_seam_exactly_zero_{tag}"] = round(
                    float(both_zero.mean()), 4
                )
            entry["env_i_zero_share"] = round(
                float((R[seam]["env_i_eff"][ok] <= 1e-9).mean()), 4
            )
            entry["env_e_zero_share"] = round(
                float((R[seam]["env_e_eff"][ok] <= 1e-9).mean()), 4
            )
            for tag in ("incumbent", "repaired"):
                x = R[seam][f"net_{tag}"][ok]
                entry[f"corr_net_vs_env_i_{tag}"] = round(
                    float(np.corrcoef(x, R[seam]["env_i_eff"][ok])[0, 1]), 4
                )
            q1[seam] = entry
        # round the float shares that came through classify_leg
        for seam, entry in q1.items():
            for k, v in list(entry.items()):
                if isinstance(v, dict):
                    entry[k] = {kk: round(vv, 4) for kk, vv in v.items()}

        # ================= Q-2 (PREREG §4) =================
        # Neighbour state on the raw interchange timestamps, joined through MISO's own
        # local(hour-ending) -> UTC map, then the neighbour BAs aggregated on UTC.
        loc_to_utc = pd.Series(
            miso_all["utc"].to_numpy(), index=pd.DatetimeIndex(miso_all["local"])
        )
        loc_to_utc = loc_to_utc[~loc_to_utc.index.duplicated()]
        miso_dem = pd.Series(
            miso_all["demand"].to_numpy(), index=pd.DatetimeIndex(miso_all["local"])
        )
        miso_dem = miso_dem[~miso_dem.index.duplicated()]
        miso_vr = pd.Series(
            (miso_all["wind"].to_numpy() + miso_all["solar"].to_numpy()),
            index=pd.DatetimeIndex(miso_all["local"]),
        )
        miso_vr = miso_vr[~miso_vr.index.duplicated()]

        def nbr_on_utc(bas: list[str], col: str) -> pd.Series:
            sub = nbr[nbr["ba"].isin(bas)]
            return sub.groupby("utc")[col].sum(min_count=1)

        q2: dict[str, dict] = {}
        for seam in FOUR_SEAM:
            bas = [b for b in MISO_SEAM_DIBA[seam] if b in bal_bas]
            sub = py[py["seam"] == seam]
            if sub.empty:
                q2[seam] = {"status": "no measured rows"}
                continue
            bucket = (sub["month"].to_numpy() - 1) * 24 + sub["hod"].to_numpy()
            flow_i = sub["net_import"].to_numpy(float)
            if not bas:
                q2[seam] = {
                    "status": "NO NEIGHBOUR-STATE INSTRUMENT — no US-BA record",
                    "dibas": list(MISO_SEAM_DIBA[seam]),
                }
                continue
            utc = loc_to_utc.reindex(
                pd.DatetimeIndex(sub["ts_beg"]) + pd.Timedelta(hours=1)
            )
            d_nb = nbr_on_utc(bas, "demand").reindex(utc.to_numpy()).to_numpy(float)
            w_nb = nbr_on_utc(bas, "wind").reindex(utc.to_numpy()).to_numpy(float)
            s_nb = nbr_on_utc(bas, "solar").reindex(utc.to_numpy()).to_numpy(float)
            local_end = pd.DatetimeIndex(sub["ts_beg"]) + pd.Timedelta(hours=1)
            miso_d = miso_dem.reindex(local_end).to_numpy(float)
            miso_w = miso_vr.reindex(local_end).to_numpy(float)
            conds = {
                "nl_nbr": d_nb - w_nb - s_nb,
                "vre_nbr": w_nb + s_nb,
                "nl_miso_own": miso_d - miso_w,  # REPORTED comparator, never gated
            }
            entry = {
                "covered_dibas": bas,
                "n_rows": int(len(sub)),
                "row_retention_after_join": round(
                    float(np.isfinite(conds["nl_nbr"]).mean()), 4
                ),
            }
            for cname, cond in conds.items():
                for direction, env in (("import", env_i), ("export", env_e)):
                    f = flow_i if direction == "import" else -flow_i
                    res = tercile_spread(f, cond, bucket, pct)
                    base = float(np.asarray(env[seam], float).mean())
                    res["env_mean_mw"] = round(base, 1)
                    res["material_bar_mw"] = round(Q2_MATERIAL_FRAC * base, 1)
                    res["inert_bar_mw"] = round(Q2_INERT_FRAC * base, 1)
                    entry[f"{cname}__{direction}"] = res
            q2[seam] = entry

        years_out[str(year)] = {
            "n_ok_hours": int(ok.sum()),
            "Q0_instrument_repair": q0,
            "Q1_binding_census": q1,
            "Q2_conditional_envelope": q2,
        }

    report["years"] = years_out
    report["provenance"] = prov

    # ---------------- gate verdicts ----------------
    def worst(fn) -> float:
        return max(fn(prov[str(y)]) for y in YEARS)

    gate = {
        "G_P1_max_abs_delta_mw": (
            worst(lambda p: p["G_P1"]["max_abs_delta_mw"] or 0.0) if prior235 else None
        ),
        "G_P3_max_abs_delta_corr": worst(lambda p: p["G_P3"]["abs_delta_corr"]),
        "G_P3_max_abs_delta_level_mw": worst(lambda p: p["G_P3"]["abs_delta_level_mw"]),
        "G_P4_max_abs_delta": worst(lambda p: p["G_P4"]["abs_delta"]),
        "G_P5_max_abs_delta_mw_per_z": worst(lambda p: p["G_P5"]["abs_delta"]),
        "G_X0_pjm_export_max_abs_mw_incumbent": worst(
            lambda p: p["G_X0"]["pjm_export_leg_max_abs_mw_incumbent"]
        ),
        "G_X0_pjm_export_max_abs_mw_repaired": worst(
            lambda p: p["G_X0"]["pjm_export_leg_max_abs_mw_repaired"]
        ),
        "G_ID_max_abs_mw": worst(lambda p: p["G_ID"]["max_abs_mw"]),
        "G_ID_total_prefix_violations": sum(
            prov[str(y)]["G_ID"]["total_prefix_violations"] for y in YEARS
        ),
        "G_P6_max_abs_mw": worst(
            lambda p: max(
                v for v in p["G_P6"]["per_seam_max_abs_mw"].values() if v is not None
            )
        ),
    }

    # G-P2 — miso-236's gated delta_r2, recomputed on this code path.
    deltas = [
        prov[str(y)]["G_P2"][seam]["abs_delta"]
        for y in YEARS
        for seam in ("PJM", "SPP", "South")
        if "abs_delta" in prov[str(y)]["G_P2"].get(seam, {})
    ]
    gate["G_P2_max_abs_delta"] = round(max(deltas), 5) if deltas else None
    gate["G_P2_cells"] = len(deltas)

    passes = {
        "G_P2": (gate["G_P2_max_abs_delta"] is None)
        or gate["G_P2_max_abs_delta"] <= TOL_DR2,
        "G_P1": (gate["G_P1_max_abs_delta_mw"] is None)
        or gate["G_P1_max_abs_delta_mw"] <= TOL_SIGMA_MW,
        "G_P3_corr": gate["G_P3_max_abs_delta_corr"] <= TOL_CORR,
        "G_P3_level": gate["G_P3_max_abs_delta_level_mw"] <= TOL_LEVEL_MW,
        "G_P4": gate["G_P4_max_abs_delta"] <= TOL_SAT,
        "G_P5": gate["G_P5_max_abs_delta_mw_per_z"] <= TOL_GAMMA,
        "G_X0": gate["G_X0_pjm_export_max_abs_mw_incumbent"] == 0.0,
        "G_ID": gate["G_ID_max_abs_mw"] <= TOL_ID_MW
        and gate["G_ID_total_prefix_violations"] == 0,
        "G_P6": gate["G_P6_max_abs_mw"] <= TOL_ENV_MW,
    }
    gate["passes"] = passes
    gate["all_pass"] = all(passes.values())
    report["gate"] = gate

    # ---------------- Q-0 verdict (PREREG §2) ----------------
    i1 = all(
        report["years"][str(y)]["Q0_instrument_repair"]["harness"]["repaired"][
            "corr_recon_vs_committed"
        ]
        > report["years"][str(y)]["Q0_instrument_repair"]["harness"]["incumbent"][
            "corr_recon_vs_committed"
        ]
        for y in YEARS
    )
    i2 = all(
        report["years"][str(y)]["Q0_instrument_repair"]["harness"]["repaired"][
            "mean_abs_level_error_mw"
        ]
        <= report["years"][str(y)]["Q0_instrument_repair"]["harness"]["incumbent"][
            "mean_abs_level_error_mw"
        ]
        for y in YEARS
    )
    superseding = "repaired" if (i1 and i2) else "incumbent"
    report["Q0_verdict"] = {
        "I1_corr_rises_all_years": bool(i1),
        "I2_level_error_not_worse_all_years": bool(i2),
        "verdict": (
            "REPAIRED SUPERSEDES" if superseding == "repaired" else "INCUMBENT STANDS"
        ),
        "superseding_instrument": superseding,
    }

    # ---------------- Q-1 verdict (PREREG §3) ----------------
    key = f"ceiling_active_share_{superseding}"
    shares = [
        report["years"][str(y)]["Q1_binding_census"][GATED_SEAM][key] for y in YEARS
    ]
    if all(s >= Q1_CEILING_BAR for s in shares):
        q1v = "CEILING-SET SEAM"
    elif all(s < Q1_MERIT_BAR for s in shares):
        q1v = "MERIT-SET SEAM"
    else:
        q1v = "MIXED"
    report["Q1_verdict"] = {
        "seam": GATED_SEAM,
        "instrument": superseding,
        "ceiling_active_share": shares,
        "verdict": q1v,
    }

    # ---------------- Q-2 verdict (PREREG §4) ----------------
    q2v: dict[str, object] = {"seam": GATED_SEAM}
    combos = []
    for cname in ("nl_nbr", "vre_nbr"):
        for direction in ("import", "export"):
            rows = [
                report["years"][str(y)]["Q2_conditional_envelope"][GATED_SEAM].get(
                    f"{cname}__{direction}"
                )
                for y in YEARS
            ]
            if any(r is None or r.get("spread_mw") is None for r in rows):
                combos.append({"combo": f"{cname}/{direction}", "status": "NO DATA"})
                continue
            zs = [abs(r["z"]) if r["z"] is not None else 0.0 for r in rows]
            sp = [r["spread_mw"] for r in rows]
            mb = [r["material_bar_mw"] for r in rows]
            ib = [r["inert_bar_mw"] for r in rows]
            combos.append(
                {
                    "combo": f"{cname}/{direction}",
                    "spread_mw": sp,
                    "z": [r["z"] for r in rows],
                    "material_bar_mw": mb,
                    "inert_bar_mw": ib,
                    "z_clears": all(v >= Q2_Z_BAR for v in zs),
                    "material_clears": all(abs(sp[i]) >= mb[i] for i in range(3)),
                    "sign_consistent": len({np.sign(v) for v in sp}) == 1,
                    "inert": all(abs(sp[i]) < ib[i] for i in range(3)),
                }
            )
    live = [
        c
        for c in combos
        if c.get("z_clears") and c.get("material_clears") and c.get("sign_consistent")
    ]
    inert = combos and all(c.get("inert") for c in combos if "inert" in c)
    q2v["combos"] = combos
    q2v["verdict"] = (
        "FOOTPRINT PRESENT" if live else ("INERT" if inert else "NOT MEANINGFUL")
    )
    q2v["clearing_combos"] = [c["combo"] for c in live]
    report["Q2_verdict"] = q2v

    # ---------------- C7 data census (PREREG §5) ----------------
    narrow_paths = [
        "data/raw/MISO",
        "data/raw/eia-930-interchange",
        "data/raw/iso-specific-transmission",
        "data/raw/campd-unit-level",
        "data/raw/outages",
        "data/raw/reference",
    ]
    narrow_tokens = ("outage", "derate", "eea", "alert", "tie", "conservative")
    # The WIDENED census declared by
    # ADDENDUM-miso241-the-census-is-too-narrow-2026-09-07.md §1. Monotone: a superset
    # of paths and of tokens can only ADD matches, never remove one.
    wide_tokens = (
        "outage",
        "derate",
        "forced",
        "unavail",
        "eea",
        "alert",
        "conservative",
        "emergency",
        "tie",
        "interface",
        "constraint",
        "transfer",
        "atc",
        "ttc",
        "flowgate",
        "curtail",
    )
    narrow: dict[str, list[str]] = {}
    for rel in narrow_paths:
        d = REPO / rel
        if not d.exists():
            narrow[rel] = ["ABSENT"]
            continue
        narrow[rel] = [
            q.name
            for q in sorted(d.rglob("*"))
            if q.is_file() and any(t in q.name.lower() for t in narrow_tokens)
        ][:20]

    raw_root = REPO / "data/raw"
    wide_top = sorted(
        q.name
        for q in raw_root.iterdir()
        if any(t in q.name.lower() for t in wide_tokens)
    )
    spp_children = sorted(
        q.name
        for q in raw_root.iterdir()
        if ("spp" in q.name.lower() or "swpp" in q.name.lower())
    )
    report["C7_census"] = {
        "narrow_as_committed": {"paths": narrow_paths, "matches": narrow},
        "wide_tokens": list(wide_tokens),
        "wide_top_level_matches": wide_top,
        "spp_or_swpp_children_in_full": spp_children,
    }

    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")

    # ---------------- stdout ----------------
    print(f"\nmiso-241 phase 0 -> {OUT.relative_to(REPO)}")
    print(f"GATE all_pass = {gate['all_pass']}")
    for k, v in passes.items():
        print(f"   {k:12s} {'PASS' if v else 'FAIL'}")
    print(
        f"   G-P1 {gate['G_P1_max_abs_delta_mw']} MW | G-P2 "
        f"{gate['G_P2_max_abs_delta']} ({gate['G_P2_cells']} cells) | G-P3 corr "
        f"{gate['G_P3_max_abs_delta_corr']} level {gate['G_P3_max_abs_delta_level_mw']} MW"
    )
    print(
        f"   G-P4 {gate['G_P4_max_abs_delta']} | G-P5 "
        f"{gate['G_P5_max_abs_delta_mw_per_z']} MW/z | G-ID {gate['G_ID_max_abs_mw']} MW "
        f"({gate['G_ID_total_prefix_violations']} violations) | G-P6 {gate['G_P6_max_abs_mw']} MW"
    )
    print(
        f"   G-X0 PJM export incumbent {gate['G_X0_pjm_export_max_abs_mw_incumbent']} MW"
        f" | repaired {gate['G_X0_pjm_export_max_abs_mw_repaired']} MW"
    )
    print(f"\nQ-0  {report['Q0_verdict']['verdict']}  (I1={i1}, I2={i2})")
    for y in YEARS:
        h = report["years"][str(y)]["Q0_instrument_repair"]["harness"]
        print(
            f"   {y}: corr inc {h['incumbent']['corr_recon_vs_committed']} -> rep "
            f"{h['repaired']['corr_recon_vs_committed']} | level inc "
            f"{h['incumbent']['mean_abs_level_error_mw']} -> rep "
            f"{h['repaired']['mean_abs_level_error_mw']} MW"
        )
    print(
        f"\nQ-1  {report['Q1_verdict']['verdict']}  ceiling_active_share "
        f"{report['Q1_verdict']['ceiling_active_share']}"
    )
    print(f"\nQ-2  {report['Q2_verdict']['verdict']}")
    for c in combos:
        print(f"   {c.get('combo')}: {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
