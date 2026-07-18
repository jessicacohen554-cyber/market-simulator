"""Leave-one-year-out validation of the forward per-plant CO2-rate estimator.

Certifies the estimator's skill **independently of any keeper's backcast fit**
(CLAUDE.md rule: the calibration fit never tunes the estimator). For each target
year Y, every plant's net CO2 intensity is predicted from the *other* years'
measured CAMPD history and scored against Y's actual intensity, gen-weighted.
This is the harness that chose the estimator's frozen constants
(``CO2_RATE_*`` in constants.py) and the design in
``docs/handoffs/emissions-co2-rate-plan-2026-07.md`` (§3).

Estimators compared (all leave-one-year-out except ``frozen``):

* ``frozen``   — the committed pooled artifact rate (leaky for its in-pool years;
                 the honest column is the year it does NOT contain).
* ``a_gw``     — gen-weighted trailing average (the shipped base).
* ``a_sm``     — simple mean of the other years' rates.
* ``a_rw``     — recency-weighted mean (linear weights by year).
* ``b_nn_oracle`` — nearest-neighbor conditioned on Y's ACTUAL CAMPD operation.
* ``b_nn_sim``    — nearest-neighbor conditioned on Y's MODEL operation (from a
                 keeper bundle's plant_hourly_fit / plant_cf_bands).
* ``b_reg``    — per-class delta regression (rate_dev ~ CF_dev), the pooled-slope
                 variant that degraded accuracy in the plan.

Metrics per target year and pooled (ALL): gen-weighted |rate error| %
(``wMAPE``) and fleet CO2 tons bias % (Σ pred·net / Σ actual·net − 1), overall
and per plant class.

Quarantined years (2022, H1-2026) are never read. Usage:

    python scripts/loyo_co2_rates.py --iso ERCOT --history-years 2023 2024 2025 \
        --keeper results/calibration/ercot_ordc_total_rtolcap_v1
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.emission_rates import (  # noqa: E402
    CF_BANDS,
    OperatingPoint,
    PlantHistory,
    forward_plant_co2_rate,
)
from scripts.lib import clean_io  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("loyo_co2_rates")

QUARANTINED_YEARS = frozenset({2022, 2026})
PROCESSED_DIR = paths.RAW_DATA_DIR / "_processed-legacy"
PARASITIC_PATH = PROCESSED_DIR / "parasitic_load_factors.parquet"
FROZEN_PATH = PROCESSED_DIR / "plant_emission_rates.parquet"
REGISTRY_PATH = paths.RAW_DATA_DIR / "reference" / "master-plant-registry.csv"


# ---------------------------------------------------------------------------
# History assembly
# ---------------------------------------------------------------------------
def _parasitic_maps() -> tuple[dict[tuple[int, int], float], dict[int, float]]:
    """Return ``({(plant,year): factor}, {plant: pooled_factor})``."""
    if not PARASITIC_PATH.exists():
        return {}, {}
    df = pd.read_parquet(PARASITIC_PATH)
    per = {
        (int(r.plant_id), int(r.year)): float(r.parasitic_factor)
        for r in df[df["year"] != 0].itertuples(index=False)
    }
    pooled = campd.pooled_factor_map(df)
    return per, pooled


def _plant_groups() -> dict[int, str]:
    """Return ``{plant_id: plant_group}`` from the master plant registry."""
    if not REGISTRY_PATH.exists():
        return {}
    reg = pd.read_csv(REGISTRY_PATH)
    if "plantid" not in reg or "plant_group" not in reg:
        return {}
    return {
        int(r.plantid): str(r.plant_group)
        for r in reg.itertuples(index=False)
        if pd.notna(r.plant_group)
    }


def _load_annual(years: list[int], states: set[str]) -> pd.DataFrame:
    """Load emissions-unit-annual for the ISO's states across ``years``.

    Returns unit-year rows filtered to ``states`` (quarantined years skipped).
    Requires the clean datatype (regenerate with
    ``scripts/data/curate_emissions_unit_annual.py``).
    """
    frames = []
    for y in years:
        if y in QUARANTINED_YEARS:
            continue
        if not clean_io.clean_exists("emissions-unit-annual", year=y):
            logger.warning("no emissions-unit-annual for %d; skipping", y)
            continue
        df = clean_io.read_clean("emissions-unit-annual", year=y, validate=False)
        frames.append(df[df["state"].astype(str).isin(states)])
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _cf_bands_from_bundle(
    bundle: Path,
) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], np.ndarray]]:
    """Return CAMPD and MODEL CF-band histograms keyed ``(plant, year)``.

    Reads the keeper bundle's ``plant_cf_bands.parquet`` (10 bands × plant-year,
    ``campd_hours`` / ``model_hours``), normalizing each to a probability vector.
    """
    path = bundle / "plant_cf_bands.parquet"
    if not path.exists():
        return {}, {}
    df = pd.read_parquet(path)
    campd_bands: dict[tuple[int, int], np.ndarray] = {}
    model_bands: dict[tuple[int, int], np.ndarray] = {}
    for (plant, year), sub in df.groupby(["plant_code", "year"], observed=True):
        sub = sub.sort_values("cf_lo")
        c = sub["campd_hours"].to_numpy(dtype=float)
        m = sub["model_hours"].to_numpy(dtype=float)
        if c.shape[0] != CF_BANDS or m.shape[0] != CF_BANDS:
            continue
        campd_bands[(int(plant), int(year))] = c / c.sum() if c.sum() > 0 else c
        model_bands[(int(plant), int(year))] = m / m.sum() if m.sum() > 0 else m
    return campd_bands, model_bands


def _model_gwh_from_bundle(bundle: Path) -> dict[tuple[int, int], float]:
    """Return ``{(plant, year): model_gwh}`` from plant_hourly_fit."""
    path = bundle / "plant_hourly_fit.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    return {
        (int(r.plant_code), int(r.year)): float(r.model_gwh)
        for r in df.itertuples(index=False)
    }


def build_history(
    years: list[int], states: set[str], bundle: Path | None
) -> pd.DataFrame:
    """Return a per-(plant, year) history frame for the LOYO.

    Columns: plant_id, year, net_mwh, co2_kg, net_rate, starts, group, and (when
    a bundle is given) campd_cf / model_cf / model_gwh operating descriptors.
    """
    annual = _load_annual(years, states)
    if annual.empty:
        return pd.DataFrame()
    per_paras, pooled_paras = _parasitic_maps()
    groups = _plant_groups()

    plant_year = (
        annual.groupby(["plant_id", "year"], observed=True)
        .agg(
            gross_mwh=("gross_mwh", "sum"),
            co2_kg=("co2_kg", "sum"),
            starts=("starts", "sum"),
        )
        .reset_index()
    )
    plant_year["plant_id"] = plant_year["plant_id"].astype(int)
    plant_year["year"] = plant_year["year"].astype(int)

    def _factor(row) -> float:
        return per_paras.get(
            (int(row.plant_id), int(row.year)),
            pooled_paras.get(int(row.plant_id), 1.0),
        )

    plant_year["parasitic"] = plant_year.apply(_factor, axis=1)
    plant_year["net_mwh"] = plant_year["gross_mwh"] * plant_year["parasitic"]
    plant_year = plant_year[plant_year["net_mwh"] > 0.0].copy()
    plant_year["net_rate"] = plant_year["co2_kg"] / plant_year["net_mwh"]
    plant_year["group"] = plant_year["plant_id"].map(groups).fillna("OTHER")

    campd_bands, model_bands = ({}, {})
    model_gwh = {}
    if bundle is not None:
        campd_bands, model_bands = _cf_bands_from_bundle(bundle)
        model_gwh = _model_gwh_from_bundle(bundle)
    flat = np.full(CF_BANDS, 1.0 / CF_BANDS)
    keys = list(zip(plant_year["plant_id"], plant_year["year"]))
    plant_year["campd_cf"] = [campd_bands.get(k, flat) for k in keys]
    plant_year["model_cf"] = [model_bands.get(k, flat) for k in keys]
    plant_year["model_gwh"] = [model_gwh.get(k, np.nan) for k in keys]
    # Scalar operation feature for the b_reg class regression: the mean CF of the
    # CAMPD duration curve (Σ band_share × band_center).
    centers = (np.arange(CF_BANDS) + 0.5) / CF_BANDS
    plant_year["cf_mean"] = [
        float(np.dot(cf, centers)) for cf in plant_year["campd_cf"]
    ]
    return plant_year


# ---------------------------------------------------------------------------
# Estimators (each returns predicted net rate for target year Y, or NaN)
# ---------------------------------------------------------------------------
def _hist_for(
    df: pd.DataFrame, plant: int, exclude_year: int, forward: bool = False
) -> pd.DataFrame:
    """Return the plant's history rows available for predicting ``exclude_year``.

    Leave-one-out by default (every other year, both sides). ``forward=True``
    restricts to years strictly BEFORE the target — the forward-chained variant
    that mirrors the real forecast task (predict Y from Y's past only), the
    honest direction for judging the trailing window / recency choice (plan
    §2.2's 7-year re-examination).
    """
    sub = df[df["plant_id"] == plant]
    if forward:
        return sub[sub["year"] < exclude_year]
    return sub[sub["year"] != exclude_year]


def _plant_history_obj(sub: pd.DataFrame, use_model_op: bool) -> PlantHistory:
    unit_years = sub.rename(columns={"plant_id": "unit_id"})[
        ["unit_id", "year", "net_mwh", "co2_kg"]
    ].copy()
    unit_years["unit_id"] = "ALL"  # plant-grain: one synthetic unit
    ops = {}
    for r in sub.itertuples(index=False):
        cf = r.model_cf if use_model_op else r.campd_cf
        ops[int(r.year)] = OperatingPoint(float(r.net_mwh), float(r.starts), cf)
    return PlantHistory(unit_years=unit_years, ops=ops)


def predict(
    df: pd.DataFrame,
    plant: int,
    year: int,
    target_row: pd.Series,
    estimator: str,
    frozen: dict[int, float],
    class_slopes: dict[str, float] | None = None,
    forward: bool = False,
) -> float:
    """Return the predicted net CO2 rate for ``plant`` in ``year``.

    Besides the named plan-§3 estimators, two parameterized families support
    the one-time constant sweeps (rule 23 — chosen ONCE from this harness,
    never from a keeper's fit):

    * ``a_gw_w<N>`` — gen-weighted average over the trailing ``N`` years of the
      available history (``a_gw`` is the ``N=all`` case);
    * ``b_gated_sim_g<G>`` / ``b_gated_oracle_g<G>`` — the SHIPPED composition:
      envelope-gated NN conditioning with gate ``G`` on top of the full-window
      gen-weighted base (inside the envelope -> base; outside -> NN year).
    """
    hist = _hist_for(df, plant, year, forward=forward)
    if estimator == "frozen":
        return frozen.get(int(plant), np.nan)
    if hist.empty:
        return np.nan
    rates = hist["net_rate"].to_numpy()
    gens = hist["net_mwh"].to_numpy()
    yrs = hist["year"].to_numpy()

    if estimator == "a_gw":
        return float((rates * gens).sum() / gens.sum()) if gens.sum() > 0 else np.nan
    if estimator.startswith("a_gw_w"):
        n = int(estimator[len("a_gw_w") :])
        keep = np.argsort(yrs)[-n:]
        r, g = rates[keep], gens[keep]
        return float((r * g).sum() / g.sum()) if g.sum() > 0 else np.nan
    if estimator == "a_sm":
        return float(rates.mean())
    if estimator == "a_rw":
        w = (yrs - yrs.min() + 1).astype(float)
        return float((rates * w).sum() / w.sum())
    if estimator in ("b_nn_oracle", "b_nn_sim") or estimator.startswith("b_gated_"):
        if estimator.startswith("b_gated_"):
            kind, g_str = estimator[len("b_gated_") :].split("_g")
            use_model = kind == "sim"
            gate = float(g_str)
        else:
            use_model = estimator == "b_nn_sim"
            # Ceiling variant: conditioning always exercised (gate 0), NOT the
            # shipped gated config — that is the b_gated_* family above.
            gate = 0.0
        obj = _plant_history_obj(hist, use_model_op=use_model)
        if use_model and not np.isnan(target_row["model_gwh"]):
            sim_gen = float(target_row["model_gwh"]) * 1000.0  # GWh -> MWh
            sim = OperatingPoint(
                sim_gen, float(target_row["starts"]), target_row["model_cf"]
            )
        else:
            sim = OperatingPoint(
                float(target_row["net_mwh"]),
                float(target_row["starts"]),
                target_row["campd_cf"],
            )
        res = forward_plant_co2_rate(
            obj, sim, None, conditioning_enabled=True, envelope_gate_l1=gate
        )
        return res.rate_kg_per_mwh_net
    if estimator == "b_reg":
        # Per-class pooled slope of rate_dev ~ cf_mean_dev applied to the plant's
        # base (plan §2.3: the class delta-regression that DEGRADED accuracy).
        base = float((rates * gens).sum() / gens.sum()) if gens.sum() > 0 else np.nan
        if class_slopes is None:
            return base
        slope = class_slopes.get(str(target_row["group"]), 0.0)
        plant_mean_cf = float(hist["cf_mean"].mean())
        return base + slope * (float(target_row["cf_mean"]) - plant_mean_cf)
    return np.nan


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def _wmape_bias(preds: np.ndarray, actual: np.ndarray, gen: np.ndarray) -> tuple:
    """Return (gen-weighted |rate err| %, fleet tons bias %) over valid rows."""
    ok = np.isfinite(preds) & np.isfinite(actual) & (actual > 0) & (gen > 0)
    if ok.sum() == 0:
        return np.nan, np.nan
    p, a, g = preds[ok], actual[ok], gen[ok]
    wmape = float((g * np.abs(p - a) / a).sum() / g.sum()) * 100.0
    bias = float((p * g).sum() / (a * g).sum() - 1.0) * 100.0
    return wmape, bias


def _class_slopes(df: pd.DataFrame) -> dict[str, float]:
    """Return ``{group: slope}`` of rate deviation vs CF-mean deviation.

    Pools every plant-year within a class: rate_dev = net_rate − the plant's
    gen-weighted mean rate; cf_dev = cf_mean − the plant's mean cf_mean. The
    no-intercept least-squares slope is the class conditioning coefficient
    (plan §2.3 found it mis-transfers across plants and degrades accuracy).
    """
    slopes: dict[str, float] = {}
    for group, sub in df.groupby("group", observed=True):
        rate_dev, cf_dev = [], []
        for _, p in sub.groupby("plant_id", observed=True):
            base = float((p["net_rate"] * p["net_mwh"]).sum() / p["net_mwh"].sum())
            rate_dev.extend((p["net_rate"] - base).tolist())
            cf_dev.extend((p["cf_mean"] - p["cf_mean"].mean()).tolist())
        x = np.array(cf_dev)
        y = np.array(rate_dev)
        denom = float((x * x).sum())
        slopes[str(group)] = float((x * y).sum() / denom) if denom > 0 else 0.0
    return slopes


DEFAULT_ESTIMATORS = [
    "frozen",
    "a_gw",
    "a_sm",
    "a_rw",
    "b_nn_oracle",
    "b_nn_sim",
    "b_reg",
]


def run(
    df: pd.DataFrame,
    years: list[int],
    frozen: dict[int, float],
    estimators: list[str] | None = None,
    forward: bool = False,
) -> pd.DataFrame:
    """Run every estimator over every target year; return a long table.

    ``forward=True`` scores the forward-chained variant: each target year is
    predicted from strictly-prior history only, and targets without at least
    three prior years are skipped (an estimator needs a real history).
    """
    estimators = estimators or DEFAULT_ESTIMATORS
    class_slopes = _class_slopes(df)
    targets = years
    if forward:
        targets = [y for y in years if sum(1 for h in years if h < y) >= 3]
    rows = []
    for est in estimators:
        for target in targets:
            tgt = df[df["year"] == target]
            preds, actual, gen = [], [], []
            for r in tgt.itertuples(index=False):
                row = pd.Series(r._asdict())
                preds.append(
                    predict(
                        df,
                        int(r.plant_id),
                        target,
                        row,
                        est,
                        frozen,
                        class_slopes,
                        forward=forward,
                    )
                )
                actual.append(float(r.net_rate))
                gen.append(float(r.net_mwh))
            wmape, bias = _wmape_bias(np.array(preds), np.array(actual), np.array(gen))
            rows.append(
                {
                    "estimator": est,
                    "target": target,
                    "wmape_pct": wmape,
                    "bias_pct": bias,
                }
            )
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--history-years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--keeper", type=Path, default=None, help="keeper bundle dir")
    ap.add_argument(
        "--forward-chain",
        action="store_true",
        help="predict each target from strictly-prior years only (the honest "
        "forward direction for the window/recency choice, plan §2.2)",
    )
    ap.add_argument(
        "--window-sweep",
        type=int,
        nargs="*",
        default=None,
        metavar="N",
        help="add a_gw_w<N> trailing-window estimators (rule-23 one-time sweep)",
    )
    ap.add_argument(
        "--gate-sweep",
        type=float,
        nargs="*",
        default=None,
        metavar="G",
        help="add b_gated_{sim,oracle}_g<G> envelope-gated estimators "
        "(the shipped composition; rule-23 one-time sweep)",
    )
    args = ap.parse_args(argv)

    bad = [y for y in args.history_years if y in QUARANTINED_YEARS]
    if bad:
        ap.error(f"quarantined years cannot enter the LOYO: {bad} (CLAUDE.md rule 22)")

    states = set(campd.states_for_iso(args.iso))
    frozen_df = pd.read_parquet(FROZEN_PATH) if FROZEN_PATH.exists() else pd.DataFrame()
    frozen = {}
    if not frozen_df.empty:
        pooled = frozen_df[frozen_df["year"] == 0]
        frozen = {
            int(r.plant_id): float(r.co2_kg_per_mwh_net)
            for r in pooled.itertuples(index=False)
        }

    df = build_history(args.history_years, states, args.keeper)
    if df.empty:
        logger.error("no history assembled — curate emissions-unit-annual first")
        return 1

    logger.info(
        "%s LOYO over %s: %d plant-years, %d plants",
        args.iso,
        args.history_years,
        len(df),
        df["plant_id"].nunique(),
    )
    estimators = list(DEFAULT_ESTIMATORS)
    for n in args.window_sweep or []:
        estimators.append(f"a_gw_w{n}")
    for g in args.gate_sweep or []:
        estimators.append(f"b_gated_sim_g{g:g}")
        estimators.append(f"b_gated_oracle_g{g:g}")
    if args.forward_chain:
        logger.info("forward-chained mode: targets need >=3 strictly-prior years")
    table = run(df, args.history_years, frozen, estimators, forward=args.forward_chain)
    pivot = table.pivot(index="target", columns="estimator", values="wmape_pct")
    print("\n=== gen-weighted |rate error| % by target year ===")
    print(pivot.round(2).to_string())
    print("\n=== fleet CO2 tons bias % by target year ===")
    print(
        table.pivot(index="target", columns="estimator", values="bias_pct")
        .round(2)
        .to_string()
    )
    print("\n=== pooled (mean over target years) wMAPE % ===")
    print(table.groupby("estimator")["wmape_pct"].mean().round(2).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
