"""ercot-165 A/B scorer — the PRE-REGISTERED gates, on committed bundle artifacts.

Scores the two WP-B v2 arms against the keeper on exactly the criteria
`docs/PRECOMMIT-ercot165-wpb-v2-unpooled-curtailment-2026-08-04.md` §3
registered BEFORE either arm solved:

* **[3e] curtailment VOLUME** — model wind/solar curtailment TWh (measured HSL
  potential minus the run's P1 dispatch) vs reported (HSL minus delivered).
* **The §4 SHAPE** — model wind curtailment hour-of-day correlation vs actual,
  with afternoon (h13-17) / overnight (h21-02) / daytime (h9-17) mass shares.
  The keeper is +0.645 / +0.462 / -0.077 (2023/24/25); the 2025 leg going
  positive is the headline target.
* **C2-adjacent gas displacement** — per-class annual TWh, arm vs keeper.
* **Kill gates K1-K5** — over-curtailment, shape regression, zonal starvation,
  C2 collapse, spurious scarcity.

This is a QUANTITY object (rule 1 [R-STRUCT]): a ceiling-clipped variable is
never marginal, so no price criterion is a verdict on it. The C3a level and the
tail counts are REPORTED as a guard, never as the pass/fail.

Reads committed bundle sidecars only (``hourly/class_hourly_<y>.parquet`` and
``hourly/system_<y>.parquet``) plus the measured ``data/raw/ercot-hsl``
series — no LP, no re-solve. Rule 22: 2023-2025 only.

Output: printed report + results/calibration/_ercot165_unpooled_ab.json
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from market_sim.data.curtailment_share import hour_axes  # noqa: E402

YEARS = (2023, 2024, 2025)  # rule 22 — no holdout year is scored
HOURS = 8760
CAL = REPO_ROOT / "results" / "calibration"
ARMS = {
    "keeper": CAL / "ercot158_poolarm_B",
    "A_tie": CAL / "ercot165_unpooled_tie_A",
    "B_share": CAL / "ercot165_unpooled_share_B",
}
OUT = CAL / "_ercot165_unpooled_ab.json"

AFTERNOON = tuple(range(13, 18))
OVERNIGHT = (21, 22, 23, 0, 1, 2)
DAYTIME = tuple(range(9, 18))
# Material gas classes for the K4 C2-collapse gate.
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")

# Pre-registered kill-gate thresholds (PRECOMMIT §3). Fixed before any solve.
K1_OVER_CURTAIL_FRAC = 0.25  # model curtailment > reported by this -> FAIL
K2_KEEPER_2025_WIND_HOD_CORR = -0.077  # arm must not fall below the keeper
K3_ZONAL_STARVATION_FRAC = 0.40  # corridor zone dispatch loss vs keeper
K4_C2_DEGRADE_PP = 3.0  # class volume error degradation, percentage points
K5_SPURIOUS_TAIL_HOURS = 10  # new >$300 hours outside the actual tail
TAIL_THRESHOLD = 300.0


def hsl(year: int) -> pd.DataFrame:
    """Measured ERCOT HSL potential and delivered generation for one year."""
    return pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")


def class_hourly(bundle, year: int) -> pd.DataFrame:
    """A bundle's committed P1 class-hourly sidecar."""
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return ch[ch["pass"] == "P1"]


def dispatch(ch: pd.DataFrame, klass: str) -> np.ndarray:
    """(8760,) P1 dispatch MW for one class, zero-filled where absent."""
    sub = ch[ch["klass"] == klass].sort_values("hour")
    if sub.empty:
        return np.zeros(HOURS)
    return sub.set_index("hour")["mw"].reindex(range(HOURS)).fillna(0.0).to_numpy()


def corr(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation, NaN-safe (0.0 on a degenerate input)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def window_share(profile24: np.ndarray, hours) -> float:
    """Share of a 24-point hod profile's mass in ``hours``."""
    tot = float(profile24.sum())
    return float(profile24[list(hours)].sum() / tot) if tot > 0 else 0.0


def hod_sum(series: np.ndarray) -> np.ndarray:
    """(24,) hour-of-day totals of an 8760 series."""
    hod, _ = hour_axes(HOURS)
    return np.array([float(series[hod == h].sum()) for h in range(24)])


def score_year(bundle, year: int) -> dict:
    """Every pre-registered quantity for one (bundle, year)."""
    h = hsl(year)
    ch = class_hourly(bundle, year)
    out: dict = {}

    for tech, pot_col, gen_col in (
        ("wind", "wind_hsl_mw", "wind_gen_mw"),
        ("solar", "solar_hsl_mw", "solar_gen_mw"),
    ):
        pot = h[pot_col].to_numpy()
        act_curt = np.clip(pot - h[gen_col].to_numpy(), 0, None)
        mod_curt = np.clip(pot - dispatch(ch, tech), 0, None)
        a_hod, m_hod = hod_sum(act_curt), hod_sum(mod_curt)
        out[tech] = {
            "model_curtail_twh": float(mod_curt.sum() / 1e6),
            "actual_curtail_twh": float(act_curt.sum() / 1e6),
            "volume_ratio": float(mod_curt.sum() / max(act_curt.sum(), 1.0)),
            "hod_corr": corr(m_hod, a_hod),
            "model_aft": window_share(m_hod, AFTERNOON),
            "model_ovn": window_share(m_hod, OVERNIGHT),
            "model_day": window_share(m_hod, DAYTIME),
            "actual_aft": window_share(a_hod, AFTERNOON),
            "actual_ovn": window_share(a_hod, OVERNIGHT),
            "actual_day": window_share(a_hod, DAYTIME),
            "model_dispatch_twh": float(dispatch(ch, tech).sum() / 1e6),
        }

    out["class_twh"] = {
        k: float(dispatch(ch, k).sum() / 1e6)
        for k in GAS_CLASSES + ("COAL_PRB", "COAL_LIGNITE", "nuclear")
    }

    sysp = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysp = sysp[sysp["pass"] == "P1"]
    lam = sysp.groupby("hour").apply(
        lambda g: float(np.average(g["price"], weights=np.maximum(g["demand"], 1e-9))),
        include_groups=False,
    )
    lam = lam.reindex(range(HOURS)).fillna(0.0).to_numpy()
    dem = sysp.groupby("hour")["demand"].sum().reindex(range(HOURS)).fillna(0.0)
    out["price"] = {
        "load_weighted_mean": float(
            np.average(lam, weights=np.maximum(dem.to_numpy(), 1e-9))
        ),
        "tail_hours_gt300": int((lam > TAIL_THRESHOLD).sum()),
        "tail_hour_index": [int(i) for i in np.where(lam > TAIL_THRESHOLD)[0]],
    }
    return out


def main() -> None:
    """Score every arm on the pre-registered gates and write the JSON record."""
    missing = [n for n, b in ARMS.items() if not (b / "meta.json").is_file()]
    if missing:
        raise SystemExit(f"bundle(s) not solved yet: {missing}")

    scores = {
        name: {str(y): score_year(bundle, y) for y in YEARS}
        for name, bundle in ARMS.items()
    }

    print("=== [3e] curtailment VOLUME (model / reported TWh) ===")
    for tech in ("wind", "solar"):
        for name in ARMS:
            row = " ".join(
                f"{scores[name][str(y)][tech]['model_curtail_twh']:6.2f}/"
                f"{scores[name][str(y)][tech]['actual_curtail_twh']:5.2f}"
                for y in YEARS
            )
            print(f"  {tech:6s} {name:9s} {row}")

    print("\n=== the §4 SHAPE: model wind-curtailment hod corr vs actual ===")
    for name in ARMS:
        row = " ".join(
            f"{scores[name][str(y)]['wind']['hod_corr']:+.3f}" for y in YEARS
        )
        aft = " ".join(
            f"{scores[name][str(y)]['wind']['model_aft']:.3f}" for y in YEARS
        )
        ovn = " ".join(
            f"{scores[name][str(y)]['wind']['model_ovn']:.3f}" for y in YEARS
        )
        print(f"  {name:9s} corr {row} | aft {aft} | ovn {ovn}")
    act = " ".join(
        f"{scores['keeper'][str(y)]['wind']['actual_aft']:.3f}" for y in YEARS
    )
    acto = " ".join(
        f"{scores['keeper'][str(y)]['wind']['actual_ovn']:.3f}" for y in YEARS
    )
    print(f"  {'ACTUAL':9s} {' ' * 26}| aft {act} | ovn {acto}")

    print("\n=== C2-adjacent gas displacement (TWh, arm - keeper) ===")
    for name in ("A_tie", "B_share"):
        for k in GAS_CLASSES:
            d = [
                scores[name][str(y)]["class_twh"][k]
                - scores["keeper"][str(y)]["class_twh"][k]
                for y in YEARS
            ]
            if max(abs(x) for x in d) >= 0.05:
                print(f"  {name:9s} {k:11s} " + " ".join(f"{x:+7.2f}" for x in d))

    print("\n=== KILL GATES (pre-registered) ===")
    gates: dict = {}
    for name in ("A_tie", "B_share"):
        g: dict = {}
        # K1 — over-curtailment.
        k1 = {
            f"{tech}_{y}": scores[name][str(y)][tech]["volume_ratio"]
            for tech in ("wind", "solar")
            for y in YEARS
        }
        g["K1_over_curtailment"] = {
            "breach": any(v > 1.0 + K1_OVER_CURTAIL_FRAC for v in k1.values()),
            "ratios": k1,
        }
        # K2 — 2025 wind shape must not fall below the keeper.
        c2025 = scores[name]["2025"]["wind"]["hod_corr"]
        g["K2_shape_regression"] = {
            "breach": c2025 < K2_KEEPER_2025_WIND_HOD_CORR,
            "arm_2025_hod_corr": c2025,
            "keeper_reference": K2_KEEPER_2025_WIND_HOD_CORR,
        }
        # K3 — corridor VRE dispatch loss vs the keeper.
        k3 = {
            f"{tech}_{y}": (
                scores[name][str(y)][tech]["model_dispatch_twh"]
                / max(scores["keeper"][str(y)][tech]["model_dispatch_twh"], 1e-9)
            )
            for tech in ("wind", "solar")
            for y in YEARS
        }
        g["K3_zonal_starvation"] = {
            "breach": any(v < 1.0 - K3_ZONAL_STARVATION_FRAC for v in k3.values()),
            "dispatch_vs_keeper": k3,
        }
        # K4 — gas class volume degradation vs the keeper, in TWh (the
        # percentage-point conversion needs the actual, which
        # calibration_verdict.py scores; this reports the raw delta and the
        # verdict run supplies the pp side).
        k4 = {
            f"{k}_{y}": (
                scores[name][str(y)]["class_twh"][k]
                - scores["keeper"][str(y)]["class_twh"][k]
            )
            for k in GAS_CLASSES
            for y in YEARS
        }
        g["K4_c2_delta_twh"] = k4
        # K5 — spurious tail hours vs the keeper's set.
        k5 = {}
        for y in YEARS:
            keep = set(scores["keeper"][str(y)]["price"]["tail_hour_index"])
            arm = set(scores[name][str(y)]["price"]["tail_hour_index"])
            k5[str(y)] = len(arm - keep)
        g["K5_spurious_tail"] = {
            "breach": any(v > K5_SPURIOUS_TAIL_HOURS for v in k5.values()),
            "new_tail_hours_vs_keeper": k5,
        }
        gates[name] = g
        breaches = [k for k, v in g.items() if isinstance(v, dict) and v.get("breach")]
        print(
            f"  {name:9s} {'BREACH: ' + ', '.join(breaches) if breaches else 'ALL CLEAR'}"
        )
        print(
            f"            K2 2025 wind hod corr {c2025:+.3f} "
            f"(keeper {K2_KEEPER_2025_WIND_HOD_CORR:+.3f}); "
            f"K5 new tail hours {k5}"
        )

    print("\n=== level guard (REPORTED, not a gate — quantity object, rule 1) ===")
    for name in ARMS:
        row = " ".join(
            f"{scores[name][str(y)]['price']['load_weighted_mean']:6.2f}" for y in YEARS
        )
        tails = " ".join(
            f"{scores[name][str(y)]['price']['tail_hours_gt300']:3d}" for y in YEARS
        )
        print(f"  {name:9s} load-weighted mean LMP {row} | >$300 hours {tails}")

    OUT.write_text(json.dumps({"scores": scores, "kill_gates": gates}, indent=1))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
