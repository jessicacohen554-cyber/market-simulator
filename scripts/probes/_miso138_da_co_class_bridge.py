"""miso-138 — demonstrate or refute an OFFER-SIDE-ONLY class bridge for MISO's ``da_co`` corpus.

Executes ``results/calibration/PREREG-miso138-da-co-class-bridge-2026-08-06.md``
exactly as pre-registered (pushed at ``848d387a`` before any adjudicating
statistic). Charter lane (b); the section 5.4 standing chartered item from
``FINDING-miso136-ct-offer-conduct-corpus-exists-2026-08-06.md`` section 6.

The question: can masked units in MISO's daily submitted-offer corpus be
assigned to the model's thermal classes (CT_PEAKER / CC_REGULAR / coal steam)
using OFFER-SIDE declarations only, well enough that the resulting class
aggregates reproduce EIA-860's MISO fleet aggregates?

Design, per PREREG section 4: the discriminant is a Gaussian naive Bayes over
(``logcap``, ``derate``, ``minfrac``) identified on EIA-860 generators OUTSIDE
MISO and validated against EIA-860 INSIDE MISO -- zero parameters fitted to
the corpus, zero to MISO. Gates run in the pre-registered order; G-0 (basis
reconciliation) and G-1 (identification on ground truth) are GATING.

Rule 13 ``[R-MEASURED]`` / rule 24 ``[R-REGISTRY]``: nothing here is sized to a
residual and no parameter is derived. Rule 22 ``[R-HOLDOUT]``: 2023-2025
report days only. Charter DATA GATE: the corpus is read from a transient
scratch directory and is never written under ``data/raw/``.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.plant_taxonomy import (  # noqa: E402
    NG_CC_PRIME_MOVERS,
    NG_CT_PRIME_MOVERS,
)

# --- PREREG section 3: the circularity bar, machine-enforced -----------------
# Classifying by the offer curve is classifying by the very conduct statistic
# the successor lever would measure (miso-136 section 6). These columns are
# never loaded, and their absence from the loaded frame is asserted.
FORBIDDEN_COLUMNS: frozenset[str] = frozenset(
    [f"Price{i}" for i in range(1, 11)]
    + [f"MW{i}" for i in range(1, 11)]
    + [f"Cleared MW{i}" for i in range(1, 13)]
    + ["Slope", "Curtailment Offer Price", "MW", "Target MW Reduction"]
)

CORPUS_COLUMNS: tuple[str, ...] = (
    "Region",
    "Unit Code",
    "Date/Time Beginning (EST)",
    "Economic Max",
    "Economic Min",
    "Emergency Max",
    "Emergency Min",
    "Economic Flag",
    "Emergency Flag",
    "Must Run Flag",
    "Unit Available Flag",
    "Self Scheduled MW",
    "MinEnergyStorageLevel",
    "MaxEnergyStorageLevel",
    "EmerMinEnergyStorageLevel",
)

# EIA-860 ``Energy Source 1`` codes that are coal ranks (the model's COAL_*
# supply classes all roll up here for this test's purpose).
COAL_FUELS: frozenset[str] = frozenset({"BIT", "SUB", "LIG", "RC", "WC", "ANT", "SGC"})

TARGET_CLASSES: tuple[str, ...] = ("CT", "CC", "COAL")
ALL_CLASSES: tuple[str, ...] = ("CT", "CC", "COAL", "NUC")

# PREREG section 4 exclusion screen 2: a thermal unit's declared capability moves
# only with ambient (within-day CV ~0.03-0.05); a variable-output resource's
# tracks its forecast. Fixed before any corpus number was seen.
VER_CV_THRESHOLD: float = 0.15

# PREREG section 6(ii): size-preserving label-permutation null.
N_PERMUTATIONS: int = 1000
PERMUTATION_SEED: int = 138


# --- EIA-860 side -----------------------------------------------------------


def _class_of(prime_mover: str, fuel: str) -> str:
    """Model-taxonomy class for one EIA-860 generator row.

    Uses the repo's own prime-mover tables so this probe can never drift from
    ``plant_taxonomy.classify_plant`` on how a plant is bucketed.
    """
    pm = str(prime_mover or "").strip().upper()
    fl = str(fuel or "").strip().upper()
    if fl == "NUC":
        return "NUC"
    if fl in COAL_FUELS and pm == "ST":
        return "COAL"
    if fl == "NG":
        if pm in NG_CC_PRIME_MOVERS:
            return "CC"
        if pm in NG_CT_PRIME_MOVERS:
            return "CT"
    return "OTHER"


def load_eia860(repo: Path) -> pd.DataFrame:
    """EIA-860 operable generators with BA code, model class and the three features."""
    gen = pd.read_parquet(repo / "data/raw/eia-860/eia860_generator_operable.parquet")
    plant = pd.read_parquet(repo / "data/raw/eia-860/eia860_plant.parquet")
    ba = plant[["Plant Code", "Balancing Authority Code"]].drop_duplicates("Plant Code")
    df = gen.merge(ba, on="Plant Code", how="left")

    df["klass"] = [
        _class_of(pm, fl)
        for pm, fl in zip(df["Prime Mover"], df["Energy Source 1"], strict=False)
    ]
    for col in (
        "Summer Capacity (MW)",
        "Winter Capacity (MW)",
        "Minimum Load (MW)",
        "Nameplate Capacity (MW)",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["is_miso"] = df["Balancing Authority Code"].astype(str).str.upper() == "MISO"
    return df


def _features_from_capacities(
    summer: pd.Series, winter: pd.Series, minload: pd.Series
) -> pd.DataFrame:
    """The three pre-registered features from summer/winter capacity and min load."""
    summer = summer.where(summer > 0)
    winter = winter.where(winter > 0)
    return pd.DataFrame(
        {
            "logcap": np.log10(summer),
            "derate": 1.0 - summer / winter,
            "minfrac": minload / summer,
        }
    )


def eia860_at_grain(df: pd.DataFrame, grain: str) -> pd.DataFrame:
    """Return the EIA-860 fleet at ``generator`` grain or ``cc_block`` grain.

    PREREG section 7 / K6: the corpus's commercial unit model registers a whole
    combined-cycle block as one market unit while EIA-860 splits it into CT and
    CA generators. Both grains are computed and never blended; a verdict that
    flips across them is reported NOT ASSERTED.
    """
    if grain == "generator":
        out = df.copy()
        feats = _features_from_capacities(
            out["Summer Capacity (MW)"],
            out["Winter Capacity (MW)"],
            out["Minimum Load (MW)"],
        )
        return pd.concat(
            [out[["klass", "is_miso", "Summer Capacity (MW)"]], feats], axis=1
        ).rename(columns={"Summer Capacity (MW)": "cap"})

    if grain != "cc_block":
        raise ValueError(f"unknown grain {grain!r}")

    is_cc = df["klass"] == "CC"
    cc = df[is_cc].copy()
    cc["_block"] = (
        cc["Plant Code"].astype(str)
        + "|"
        + cc["Unit Code"].fillna("CCBLK").astype(str).str.strip()
    )
    agg = cc.groupby("_block", dropna=False).agg(
        summer=("Summer Capacity (MW)", "sum"),
        winter=("Winter Capacity (MW)", "sum"),
        minload=("Minimum Load (MW)", "sum"),
        is_miso=("is_miso", "first"),
    )
    agg["klass"] = "CC"
    rest = df[~is_cc]
    rest_frame = pd.DataFrame(
        {
            "summer": rest["Summer Capacity (MW)"].to_numpy(),
            "winter": rest["Winter Capacity (MW)"].to_numpy(),
            "minload": rest["Minimum Load (MW)"].to_numpy(),
            "is_miso": rest["is_miso"].to_numpy(),
            "klass": rest["klass"].to_numpy(),
        }
    )
    both = pd.concat([agg.reset_index(drop=True), rest_frame], ignore_index=True)
    feats = _features_from_capacities(both["summer"], both["winter"], both["minload"])
    out = pd.concat([both[["klass", "is_miso"]], feats], axis=1)
    out["cap"] = both["summer"].to_numpy()
    return out


# --- the pre-specified classifier (Gaussian naive Bayes, hand-rolled) --------


def gnb_fit(x: np.ndarray, y: np.ndarray, classes: tuple[str, ...], uniform_prior: bool) -> dict:
    """Fit Gaussian naive Bayes; priors are the TRAINING population's frequencies."""
    means, variances, priors = [], [], []
    for k in classes:
        rows = x[y == k]
        means.append(rows.mean(axis=0))
        variances.append(rows.var(axis=0) + 1e-9)
        priors.append(1.0 / len(classes) if uniform_prior else len(rows) / len(y))
    return {
        "classes": classes,
        "mean": np.vstack(means),
        "var": np.vstack(variances),
        "prior": np.asarray(priors),
    }


def gnb_predict(model: dict, x: np.ndarray) -> np.ndarray:
    """Argmax-posterior class label for each row of ``x``."""
    mean, var, prior = model["mean"], model["var"], model["prior"]
    # log N(x | mu, var) summed over independent features, plus the log prior.
    ll = -0.5 * (
        ((x[:, None, :] - mean[None, :, :]) ** 2 / var[None, :, :])
        + np.log(2.0 * np.pi * var[None, :, :])
    ).sum(axis=2)
    return np.asarray(model["classes"])[np.argmax(ll + np.log(prior)[None, :], axis=1)]


def balanced_accuracy(truth: np.ndarray, pred: np.ndarray, classes: tuple[str, ...]) -> float:
    """Mean per-class recall -- the pre-registered G-1 statistic."""
    recalls = [
        float((pred[truth == k] == k).mean()) for k in classes if (truth == k).any()
    ]
    return float(np.mean(recalls)) if recalls else float("nan")


def g1_identification(fleet: pd.DataFrame, rng: np.random.Generator) -> dict:
    """G-1 (GATING): 5-fold CV balanced accuracy in the held-out non-MISO population."""
    train = fleet[(~fleet["is_miso"]) & fleet["klass"].isin(ALL_CLASSES)].dropna(
        subset=["logcap", "derate", "minfrac"]
    )
    x = train[["logcap", "derate", "minfrac"]].to_numpy(float)
    y = train["klass"].to_numpy()
    order = rng.permutation(len(y))
    x, y = x[order], y[order]
    folds = np.arange(len(y)) % 5
    scores = []
    for f in range(5):
        model = gnb_fit(x[folds != f], y[folds != f], ALL_CLASSES, uniform_prior=False)
        scores.append(balanced_accuracy(y[folds == f], gnb_predict(model, x[folds == f]), ALL_CLASSES))
    per_class = {}
    full = gnb_fit(x, y, ALL_CLASSES, uniform_prior=False)
    pred_in = gnb_predict(full, x)
    for k in ALL_CLASSES:
        per_class[k] = {
            "n_train": int((y == k).sum()),
            "recall_insample": float((pred_in[y == k] == k).mean()),
        }
    return {
        "n_train": int(len(y)),
        "cv_balanced_accuracy": float(np.mean(scores)),
        "cv_folds": [float(s) for s in scores],
        "per_class": per_class,
        "passes": bool(np.mean(scores) >= 0.70),
    }


# --- corpus side ------------------------------------------------------------


def load_corpus_day(path: Path) -> pd.DataFrame:
    """Read one ``da_co`` zip, offer-side columns only, with the forbidden set asserted absent."""
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as fh:
            header = pd.read_csv(fh, nrows=0)
        available = [c for c in CORPUS_COLUMNS if c in header.columns]
        with z.open(name) as fh:
            df = pd.read_csv(fh, usecols=available, low_memory=False)
    leaked = FORBIDDEN_COLUMNS.intersection(df.columns)
    if leaked:
        raise AssertionError(f"circularity bar breached: forbidden columns loaded {sorted(leaked)}")
    return df


def corpus_unit_features(scratch: Path, year: int, days: dict[str, tuple[str, ...]]) -> pd.DataFrame:
    """Per-masked-unit offer-side features for one sampled year (PREREG section 4)."""
    per_season: dict[str, pd.DataFrame] = {}
    extras: list[pd.DataFrame] = []
    for season, daylist in days.items():
        frames = []
        for day in daylist:
            df = load_corpus_day(scratch / f"{day}_da_co.zip")
            for col in (
                "Economic Max",
                "Economic Min",
                "Emergency Max",
                "Self Scheduled MW",
                "Must Run Flag",
                "Unit Available Flag",
                "MinEnergyStorageLevel",
                "MaxEnergyStorageLevel",
                "EmerMinEnergyStorageLevel",
            ):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df["_day"] = day
            frames.append(df)
        day_df = pd.concat(frames, ignore_index=True)

        # Per-unit-day capability declaration and within-day dispersion.
        by_unit_day = day_df.groupby(["Unit Code", "_day"])["Economic Max"].agg(
            ["max", "mean", "std", "count"]
        )
        by_unit_day["cv"] = by_unit_day["std"] / by_unit_day["mean"].replace(0, np.nan)
        valid = by_unit_day[by_unit_day["max"] > 0]
        per_season[season] = pd.DataFrame(
            {
                "cap": valid.groupby("Unit Code")["max"].max(),
                "valid_days": valid.groupby("Unit Code")["max"].size(),
                "cv": valid.groupby("Unit Code")["cv"].median(),
            }
        )
        extras.append(day_df)

    allday = pd.concat(extras, ignore_index=True)
    pos = allday[allday["Economic Max"] > 0].copy()
    pos["_minfrac"] = pos["Economic Min"] / pos["Economic Max"]
    pos["_emerg"] = (pos["Emergency Max"] - pos["Economic Max"]) / pos["Economic Max"]
    other = pd.DataFrame(
        {
            "minfrac": pos.groupby("Unit Code")["_minfrac"].median(),
            "emerg_headroom": pos.groupby("Unit Code")["_emerg"].median(),
            "selfsched_frac": allday.groupby("Unit Code")["Self Scheduled MW"].apply(
                lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())
            ),
            "mustrun_frac": allday.groupby("Unit Code")["Must Run Flag"].apply(
                lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())
            ),
            "avail_frac": allday.groupby("Unit Code")["Unit Available Flag"].apply(
                lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())
            ),
            "region": allday.groupby("Unit Code")["Region"].first(),
        }
    )
    storage_cols = [
        c
        for c in ("MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel")
        if c in allday.columns
    ]
    other["is_storage"] = (
        allday.groupby("Unit Code")[storage_cols].apply(lambda g: bool(g.notna().any().any()))
        if storage_cols
        else False
    )

    s, w = per_season["summer"], per_season["winter"]
    units = pd.DataFrame(index=sorted(set(s.index) | set(w.index)))
    units["cap_summer"] = s["cap"]
    units["cap_winter"] = w["cap"]
    units["days_summer"] = s["valid_days"].fillna(0)
    units["days_winter"] = w["valid_days"].fillna(0)
    units["cv"] = pd.concat([s["cv"], w["cv"]], axis=1).median(axis=1)
    units = units.join(other, how="left")

    units["cap"] = units[["cap_summer", "cap_winter"]].max(axis=1)
    units["logcap"] = np.log10(units["cap_summer"].where(units["cap_summer"] > 0))
    units["derate"] = 1.0 - units["cap_summer"] / units["cap_winter"]
    units["year"] = year
    return units


def apply_screens(units: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """PREREG section 4 exclusion screens: storage, variable-output, coverage."""
    n0 = len(units)
    is_storage = units["is_storage"].fillna(False).astype(bool)
    is_ver = units["cv"].fillna(0.0) > VER_CV_THRESHOLD
    covered = (units["days_summer"] >= 2) & (units["days_winter"] >= 2)
    keep = (~is_storage) & (~is_ver) & covered
    keep &= units[["logcap", "derate", "minfrac"]].notna().all(axis=1)
    audit = {
        "units_total": int(n0),
        "excluded_storage": int(is_storage.sum()),
        "excluded_ver": int((is_ver & ~is_storage).sum()),
        "excluded_ver_capacity_mw": float(units.loc[is_ver & ~is_storage, "cap"].sum()),
        "excluded_coverage": int((~covered & ~is_ver & ~is_storage).sum()),
        "kept": int(keep.sum()),
        "kept_capacity_mw": float(units.loc[keep, "cap_summer"].sum()),
    }
    return units[keep].copy(), audit


# --- gates ------------------------------------------------------------------


def g0_basis(corpus_kept_mw: float, corpus_kept_n: int, miso860: pd.DataFrame) -> dict:
    """G-0 (GATING): does the corpus's declared capability reconcile with EIA-860 MISO?"""
    ref = miso860[miso860["klass"].isin(ALL_CLASSES)]
    ref_mw = float(ref["cap"].sum())
    ref_n = int(len(ref))
    d_mw = corpus_kept_mw / ref_mw - 1.0
    d_n = corpus_kept_n / ref_n - 1.0
    return {
        "corpus_mw": corpus_kept_mw,
        "corpus_n": corpus_kept_n,
        "eia860_miso_mw": ref_mw,
        "eia860_miso_n": ref_n,
        "rel_mw": float(d_mw),
        "rel_n": float(d_n),
        "passes": bool(abs(d_mw) <= 0.30 and abs(d_n) <= 0.40),
        "hard_stop": bool(abs(d_mw) > 1.0),
    }


def class_aggregates(frame: pd.DataFrame, label_col: str, cap_col: str) -> dict:
    """Per-class count, capacity and the p50/p90 the G-3 shape test reads."""
    out = {}
    for k in ALL_CLASSES:
        sub = frame[frame[label_col] == k]
        caps = sub[cap_col].dropna().to_numpy(float)
        out[k] = {
            "n": int(len(sub)),
            "mw": float(caps.sum()),
            "p50": float(np.percentile(caps, 50)) if len(caps) else float("nan"),
            "p90": float(np.percentile(caps, 90)) if len(caps) else float("nan"),
        }
    return out


def g3_discrepancy(corpus_agg: dict, ref_agg: dict) -> float:
    """Summed |ratio-1| over p50 and p90 across the target classes (lower is better)."""
    total = 0.0
    for k in TARGET_CLASSES:
        for q in ("p50", "p90"):
            a, b = corpus_agg[k][q], ref_agg[k][q]
            total += abs(a / b - 1.0) if (b and np.isfinite(a) and np.isfinite(b)) else 10.0
    return float(total)


def permutation_null(
    labels: np.ndarray, caps: np.ndarray, ref_agg: dict, rng: np.random.Generator
) -> dict:
    """PREREG section 6(ii): size-preserving label permutation, the trap's own test."""
    draws = []
    for _ in range(N_PERMUTATIONS):
        shuffled = rng.permutation(labels)
        agg = class_aggregates(
            pd.DataFrame({"k": shuffled, "cap": caps}), "k", "cap"
        )
        draws.append(g3_discrepancy(agg, ref_agg))
    arr = np.asarray(draws)
    return {
        "null_p05": float(np.percentile(arr, 5)),
        "null_p50": float(np.percentile(arr, 50)),
        "null_min": float(arr.min()),
    }


def main() -> int:
    """Run every pre-registered gate in order and write the record."""
    repo = Path(__file__).resolve().parents[2]
    scratch = Path(sys.argv[1])
    rng = np.random.default_rng(PERMUTATION_SEED)
    from _miso138_fetch_da_co import SAMPLE_DAYS  # noqa: PLC0415 - sibling probe

    record: dict[str, Any] = {
        "prereg": "PREREG-miso138-da-co-class-bridge-2026-08-06.md",
        "prereg_commit": "848d387ab761755a9c190c10e69b844f292943b2",
        "sample_days": {str(y): {s: list(d) for s, d in v.items()} for y, v in SAMPLE_DAYS.items()},
        "grains": {},
    }

    raw860 = load_eia860(repo)
    for grain in ("generator", "cc_block"):
        fleet = eia860_at_grain(raw860, grain)
        g1 = g1_identification(fleet, np.random.default_rng(PERMUTATION_SEED))
        grain_rec: dict[str, Any] = {"G1": g1}
        record["grains"][grain] = grain_rec
        if not g1["passes"]:
            grain_rec["verdict"] = "REFUTED_ON_IDENTIFICATION"
            continue

        train = fleet[(~fleet["is_miso"]) & fleet["klass"].isin(ALL_CLASSES)].dropna(
            subset=["logcap", "derate", "minfrac"]
        )
        miso860 = fleet[fleet["is_miso"] & fleet["klass"].isin(ALL_CLASSES)].dropna(subset=["cap"])
        ref_agg = class_aggregates(miso860, "klass", "cap")
        grain_rec["eia860_miso"] = ref_agg

        for uniform in (False, True):
            model = gnb_fit(
                train[["logcap", "derate", "minfrac"]].to_numpy(float),
                train["klass"].to_numpy(),
                ALL_CLASSES,
                uniform_prior=uniform,
            )
            key = "uniform_prior" if uniform else "primary"
            per_year: dict[str, Any] = {}
            for year, days in SAMPLE_DAYS.items():
                units = corpus_unit_features(scratch, year, days)
                kept, audit = apply_screens(units)
                pred = gnb_predict(model, kept[["logcap", "derate", "minfrac"]].to_numpy(float))
                kept = kept.assign(pred=pred)
                agg = class_aggregates(kept, "pred", "cap_summer")
                g0 = g0_basis(audit["kept_capacity_mw"], audit["kept"], miso860)
                sep = {
                    k: {
                        "S_cap": float(agg[k]["mw"] / ref_agg[k]["mw"] - 1.0)
                        if ref_agg[k]["mw"]
                        else float("nan"),
                        "S_count": float(agg[k]["n"] / ref_agg[k]["n"] - 1.0)
                        if ref_agg[k]["n"]
                        else float("nan"),
                    }
                    for k in TARGET_CLASSES
                }
                obs = g3_discrepancy(agg, ref_agg)
                null = permutation_null(
                    kept["pred"].to_numpy(), kept["cap_summer"].to_numpy(float), ref_agg, rng
                )
                total_cap = sum(agg[k]["mw"] for k in ALL_CLASSES)
                per_year[str(year)] = {
                    "screens": audit,
                    "G0": g0,
                    "corpus_classified": agg,
                    "G2_separation": sep,
                    "G3_discrepancy": obs,
                    "G3_null": null,
                    "G3_beats_null": bool(obs < null["null_p05"]),
                    "G4_nuclear": {
                        "corpus_n": agg["NUC"]["n"],
                        "eia860_n": ref_agg["NUC"]["n"],
                        "d_n": int(agg["NUC"]["n"] - ref_agg["NUC"]["n"]),
                        "rel_mw": float(agg["NUC"]["mw"] / ref_agg["NUC"]["mw"] - 1.0)
                        if ref_agg["NUC"]["mw"]
                        else float("nan"),
                    },
                    "max_class_share": float(
                        max(agg[k]["mw"] for k in ALL_CLASSES) / total_cap
                    )
                    if total_cap
                    else float("nan"),
                    "secondary_features": {
                        k: {
                            "emerg_headroom_p50": float(
                                kept.loc[kept["pred"] == k, "emerg_headroom"].median()
                            ),
                            "selfsched_frac_p50": float(
                                kept.loc[kept["pred"] == k, "selfsched_frac"].median()
                            ),
                            "mustrun_frac_p50": float(
                                kept.loc[kept["pred"] == k, "mustrun_frac"].median()
                            ),
                            "derate_p50": float(kept.loc[kept["pred"] == k, "derate"].median()),
                            "minfrac_p50": float(kept.loc[kept["pred"] == k, "minfrac"].median()),
                        }
                        for k in ALL_CLASSES
                    },
                }
            grain_rec[key] = per_year

    out = repo / "results/calibration/_miso138_da_co_class_bridge.json"
    out.write_text(json.dumps(record, indent=1, default=float))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
