"""nyiso-159 A/B scorer — the NYISO zonal loss surface, gates of PREREG-nyiso159 §5.

Scores the pre-registered gates of
``results/calibration/PREREG-nyiso159-zonal-loss-surface-2026-08-30.md`` §5 on
the two committed bundles (``nyiso159_lossctl_A`` control /
``nyiso159_lossarm_B`` arm). **No solve here, and no gate that is not in the
standing record.** Template: ``_nyiso157_par_ab_gates.py``.

Gate map (STOP gates fire => no promotion; the rest report at full magnitude):

* **K1** (STOP, standing single-delta discipline) — the arms' recorded configs
  differ in exactly ``{nyiso_zonal_loss_surface: False -> True}``.
* **K2** (STOP) — feasibility: zero slack, zero dump, BOTH arms, all years
  (losses consume real MWh; the fleet must cover them without scarcity
  artifacts).
* **K5** — off-state byte-identity: exercised by the unit suite
  (``tests/iso/nyiso/test_nyiso_zonal_loss_surface.py``); here the control run
  IS the off state at HEAD and K6 measures its reproduction. The control-vs-
  keeper drift (G1 class) is REPORTED, not gated.
* **K6** (STOP) — control C3a per year within +/-0.2 pp of the keeper's
  committed **+1.0 / -2.0 / -12.0 %**.
* **P1** (STOP) — measured-loss reproduction: per adjacent chain pair-year,
  the ARM-CONTROL annual mean zonal-dual spread delta within
  **[0.5x, 1.5x] of the measured mean dMCL** for that pair-year (recomputed
  live from the curated RT component record). 12 pair-years; pass =
  >= 10/12 in band with NO miss below 0.25x or above 2.0x.
* **W-K3d** (STOP) — no upstate relocation: |arm - control| Upstate_West
  annual mean dual <= $0.75/MWh every year.
* **ADVERSE** (STOP) — arm C3a-2023 stays <= +10 % and C3a-2024 within +/-10 %
  (phase-0 named adverse band).
* **C3c** — arm-vs-control criterion statuses reported only (nyiso-137 clock
  caveat); no absolute band claim.
* **LOYO** — P1 holding in each year separately; a year where it breaks
  indicts the identification (STOP), never a re-tune.

Usage::

    python scripts/probes/_nyiso159_loss_ab_gates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

ARM_A = REPO / "results/calibration/nyiso159_lossctl_A"
ARM_B = REPO / "results/calibration/nyiso159_lossarm_B"
KEEPER = REPO / "results/calibration/nyiso157_pararm_B"
OUT_PATH = REPO / "results/calibration/_nyiso159_loss_ab_gates.json"
CLEAN_RTM = REPO / "data/clean/lmp/NYISO/RTM"

#: The single key under test (PREREG-nyiso159 §1/§4).
FLAG = "nyiso_zonal_loss_surface"
#: PREREG §5 K6 — the keeper's committed C3a scorecard and the committed
#: actual RT load-weighted means the scorer used (nyiso-156 anchors, reproduced
#: to the digit from the keeper bundle before this probe was filed).
K6_KEEPER_C3A = {2023: 1.0, 2024: -2.0, 2025: -12.0}
K6_TOL_PP = 0.2
ACTUAL_RT_LW = {2023: 32.25, 2024: 38.12, 2025: 66.43}
#: PREREG §5 P1 — the adjacent chain pairs (near upstream, far downstream) and
#: the band. Outer floor/ceiling per the pjm-136 edge-miss precedent.
PAIRS = (
    ("Upstate_West", "Capital_Hudson"),
    ("Capital_Hudson", "Lower_Hudson"),
    ("Lower_Hudson", "NYC"),
    ("NYC", "Long_Island"),
)
P1_BAND = (0.5, 1.5)
P1_OUTER = (0.25, 2.0)
P1_MIN_IN_BAND = 10
#: PREREG §5 W-K3d — upstate relocation bound ($/MWh, annual mean).
WK3D_UW_USD = 0.75
#: PREREG §5 adverse band (C3a-2023 up-side cap; C3a-2024 symmetric band).
ADVERSE_2023_MAX_PCT = 10.0
ADVERSE_2024_ABS_PCT = 10.0
#: K2 slack/dump tolerance (LP epsilon, not a headroom).
SLACK_EPS_MW = 1e-6

#: The scoring crosswalk (derive_actual_lmp.NYISO_ZONE_MAP) — for the measured
#: dMCL benchmark, aggregated exactly as the derive/actuals aggregate.
ZONE_MAP = {
    "Upstate_West": ("WEST", "GENESE", "CENTRL", "NORTH", "MHK VL"),
    "Capital_Hudson": ("CAPITL",),
    "Lower_Hudson": ("HUD VL", "MILLWD", "DUNWOD"),
    "NYC": ("N.Y.C.",),
    "Long_Island": ("LONGIL",),
}


# --------------------------------------------------------------------------- #
# committed-bytes readers (nyiso-155/157 template)
# --------------------------------------------------------------------------- #
def _system(bundle: Path, year: int) -> pd.DataFrame:
    """P1 system hourly frame for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _ny_zones(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop any external interchange node rows."""
    return frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]


def _zone_price(bundle: Path, year: int, zone: str) -> np.ndarray:
    """One zone's hourly price vector."""
    frame = _system(bundle, year)
    s = (
        frame[frame["zone"] == zone]
        .set_index("hour")["price"]
        .sort_index()
        .reindex(range(8760))
    )
    return s.to_numpy(dtype=float)


def _lw_lambda(bundle: Path, year: int) -> float:
    """NYISO demand-weighted mean lambda (the nyiso-156 anchor arithmetic)."""
    ny = _ny_zones(_system(bundle, year))
    return round(float((ny["price"] * ny["demand"]).sum() / ny["demand"].sum()), 4)


def _c3a_pct(bundle: Path, year: int) -> float:
    """C3a on the committed-anchor basis (reproduces the scorer, nyiso-156)."""
    return round(100.0 * (_lw_lambda(bundle, year) / ACTUAL_RT_LW[year] - 1.0), 2)


def _max_zonal_dlmp(a: Path, b: Path, year: int) -> float:
    """Max abs zonal hourly price divergence between two bundles."""
    left = _system(a, year).set_index(["zone", "hour"])["price"].sort_index()
    right = _system(b, year).set_index(["zone", "hour"])["price"].sort_index()
    lj, rj = left.align(right, join="inner")
    return round(float((lj - rj).abs().max()), 4)


def _config_block(bundle: Path) -> dict:
    """Recorded config: scenario block merged over flat meta keys (nyiso-155)."""
    block: dict = {}
    cfg_path = bundle / "run_config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())
        block.update(cfg.get("scenario_config", {}) or {})
    meta_path = bundle / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        for k, v in meta.items():
            if k in (
                "timestamp",
                "note",
                "years",
                "shared_inputs",
                "git_sha",
                "basis_sha",
                "environment",
                "highspy_version",
            ):
                continue
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    block[f"{k}.{k2}"] = v2
            else:
                block.setdefault(k, v)
    return block


def _measured_dmcl(year: int) -> dict[tuple[str, str], float]:
    """Measured annual mean dMCL per adjacent pair from the curated RT record."""
    df = pd.read_parquet(CLEAN_RTM / f"lmp_{year}.parquet")
    members = [m for ms in ZONE_MAP.values() for m in ms]
    df = df[df["zone"].isin(members)]
    piv = df.pivot_table(
        index="interval_start_utc", columns="zone", values="loss_usd_per_mwh"
    )
    piv = piv[piv.notna().all(axis=1)]
    mcl = pd.DataFrame({z: piv[list(ms)].mean(axis=1) for z, ms in ZONE_MAP.items()})
    return {
        (near, far): round(float((mcl[far] - mcl[near]).mean()), 4)
        for near, far in PAIRS
    }


# --------------------------------------------------------------------------- #
# the pre-registered gates
# --------------------------------------------------------------------------- #
def k1_single_delta() -> dict:
    """K1 — exactly one differing recorded key, the flag under test."""
    a, b = _config_block(ARM_A), _config_block(ARM_B)
    diff = {
        k: {"A": a.get(k), "B": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "differing_keys": diff,
        "n_differing": len(diff),
        "expected": [FLAG],
        "passed": sorted(diff) == [FLAG],
    }


def k2_feasibility() -> dict:
    """K2 — zero slack, zero dump, BOTH arms, all years (PREREG §5)."""
    per_year, ok = {}, True
    for year in YEARS:
        row = {}
        for name, bundle in (("A", ARM_A), ("B", ARM_B)):
            frame = _ny_zones(_system(bundle, year))
            slack_h = int((frame["slack"] > SLACK_EPS_MW).sum())
            dump_h = int((frame["dump"] > SLACK_EPS_MW).sum())
            row[name] = {
                "slack_zone_hours": slack_h,
                "dump_zone_hours": dump_h,
                "max_slack_mw": round(float(frame["slack"].max()), 6),
                "max_dump_mw": round(float(frame["dump"].max()), 6),
            }
            ok = ok and slack_h == 0 and dump_h == 0
        per_year[year] = row
    return {"per_year": per_year, "passed": bool(ok)}


def k6_control_reproduces() -> dict:
    """K6 — control C3a within +/-0.2 pp of the keeper's committed scorecard."""
    per_year, ok = {}, True
    for year in YEARS:
        got = _c3a_pct(ARM_A, year)
        want = K6_KEEPER_C3A[year]
        per_year[year] = {
            "control_c3a_pct": got,
            "keeper_committed_pct": want,
            "delta_pp": round(got - want, 2),
        }
        ok = ok and abs(got - want) <= K6_TOL_PP
    return {"tolerance_pp": K6_TOL_PP, "per_year": per_year, "passed": bool(ok)}


def k5_drift_report() -> dict:
    """K5 report leg — control vs the committed keeper bundle (G1 drift class,
    reported not gated; the off-state build-path identity is the unit suite)."""
    return {
        "unit_suite": "tests/iso/nyiso/test_nyiso_zonal_loss_surface.py",
        "control_vs_keeper_max_zonal_dlmp": {
            y: _max_zonal_dlmp(ARM_A, KEEPER, y) for y in YEARS
        },
    }


def p1_measured_loss_reproduction() -> dict:
    """P1 — arm-control dual-spread delta in band of the measured dMCL."""
    rows, n_in, worst = [], 0, []
    for year in YEARS:
        meas = _measured_dmcl(year)
        for near, far in PAIRS:
            sa = float(
                np.nanmean(_zone_price(ARM_A, year, far))
                - np.nanmean(_zone_price(ARM_A, year, near))
            )
            sb = float(
                np.nanmean(_zone_price(ARM_B, year, far))
                - np.nanmean(_zone_price(ARM_B, year, near))
            )
            delta = sb - sa
            m = meas[(near, far)]
            ratio = delta / m if abs(m) > 1e-9 else float("nan")
            in_band = P1_BAND[0] <= ratio <= P1_BAND[1]
            in_outer = P1_OUTER[0] <= ratio <= P1_OUTER[1]
            n_in += int(in_band)
            if not in_outer:
                worst.append((year, f"{near}->{far}", round(ratio, 3)))
            rows.append(
                {
                    "year": year,
                    "pair": f"{near}->{far}",
                    "arm_minus_control_spread_delta_usd": round(delta, 4),
                    "measured_mean_dmcl_usd": m,
                    "ratio": round(ratio, 3),
                    "in_band": in_band,
                    "in_outer": in_outer,
                }
            )
    passed = n_in >= P1_MIN_IN_BAND and not worst
    return {
        "band": P1_BAND,
        "outer": P1_OUTER,
        "min_in_band": P1_MIN_IN_BAND,
        "n_in_band": n_in,
        "n_total": len(rows),
        "outer_misses": worst,
        "pair_years": rows,
        "passed": bool(passed),
    }


def wk3d_no_upstate_relocation() -> dict:
    """W-K3d — |arm - control| Upstate_West annual mean dual <= $0.75/MWh."""
    per_year, ok = {}, True
    for year in YEARS:
        a = float(np.nanmean(_zone_price(ARM_A, year, "Upstate_West")))
        b = float(np.nanmean(_zone_price(ARM_B, year, "Upstate_West")))
        d = abs(b - a)
        per_year[year] = {
            "control_uw_mean": round(a, 4),
            "arm_uw_mean": round(b, 4),
            "abs_delta": round(d, 4),
        }
        ok = ok and d <= WK3D_UW_USD
    return {"bound_usd": WK3D_UW_USD, "per_year": per_year, "passed": bool(ok)}


def adverse_band() -> dict:
    """Named adverse band — arm C3a-2023 <= +10 %, C3a-2024 within +/-10 %."""
    c23 = _c3a_pct(ARM_B, 2023)
    c24 = _c3a_pct(ARM_B, 2024)
    ok = c23 <= ADVERSE_2023_MAX_PCT and abs(c24) <= ADVERSE_2024_ABS_PCT
    return {
        "arm_c3a_2023_pct": c23,
        "cap_2023_pct": ADVERSE_2023_MAX_PCT,
        "arm_c3a_2024_pct": c24,
        "band_2024_abs_pct": ADVERSE_2024_ABS_PCT,
        "passed": bool(ok),
    }


def loyo_consistency() -> dict:
    """LOYO — P1 must hold in each year separately (no pooling to hide a year)."""
    p1 = p1_measured_loss_reproduction()
    by_year: dict[int, dict] = {}
    for row in p1["pair_years"]:
        y = row["year"]
        by_year.setdefault(y, {"n_in_band": 0, "outer_misses": 0})
        by_year[y]["n_in_band"] += int(row["in_band"])
        by_year[y]["outer_misses"] += int(not row["in_outer"])
    # Per-year form of the 10/12 aggregate: >= 3/4 in band, no outer miss.
    bad = [
        y
        for y, r in by_year.items()
        if r["n_in_band"] < 3 or r["outer_misses"] > 0
    ]
    return {"per_year": by_year, "breaking_years": bad, "passed": not bad}


# --------------------------------------------------------------------------- #
# reports (full magnitude, never gated)
# --------------------------------------------------------------------------- #
def prices_report() -> dict:
    """C3a / LW lambda / zonal gradient per arm-year (P3 honesty check)."""
    out = {}
    for year in YEARS:
        row: dict = {"c3a_pct": {}, "lw_lambda": {}, "zonal_mean_vs_uw": {}}
        for name, bundle in (("A", ARM_A), ("B", ARM_B)):
            row["c3a_pct"][name] = _c3a_pct(bundle, year)
            row["lw_lambda"][name] = _lw_lambda(bundle, year)
            uw = np.nanmean(_zone_price(bundle, year, "Upstate_West"))
            row["zonal_mean_vs_uw"][name] = {
                z: round(float(np.nanmean(_zone_price(bundle, year, z)) - uw), 3)
                for z in ZONE_MAP
                if z != "Upstate_West"
            }
        out[year] = row
    return out


def c3b_monthly_report() -> dict:
    """C3b passenger check — monthly LW error vs the committed bench rt_lw_mon."""
    import gzip

    bench_dir = REPO / "frontend/data/backcast/bench/NYISO"
    out = {}
    for year in YEARS:
        b = json.load(gzip.open(bench_dir / f"{year}.json.gz"))
        actual = np.asarray(b["bench"]["avgLMP"]["rt_lw_mon"], dtype=float)
        cal = pd.date_range("2023-01-01", periods=8760, freq="h")
        row = {}
        for name, bundle in (("A", ARM_A), ("B", ARM_B)):
            ny = _ny_zones(_system(bundle, year))
            piv_p = ny.pivot_table(index="hour", columns="zone", values="price")
            piv_d = ny.pivot_table(index="hour", columns="zone", values="demand")
            lw = (piv_p * piv_d).sum(axis=1) / piv_d.sum(axis=1)
            mon = pd.Series(lw.to_numpy(), index=cal).groupby(cal.month).mean()
            err = mon.to_numpy() - actual
            row[name] = {
                "rmse_norm": round(
                    float(np.sqrt((err**2).mean()) / actual.mean()), 4
                ),
                "monthly_err": [round(float(e), 2) for e in err],
            }
        out[year] = row
    return out


def scorecards() -> dict:
    """Determination + criterion statuses from each bundle's metrics.json."""
    out = {}
    for name, bundle in (("A_control", ARM_A), ("B_loss", ARM_B)):
        path = bundle / "metrics.json"
        if not path.exists():
            out[name] = None
            continue
        m = json.loads(path.read_text())
        out[name] = {
            "determination": m.get("determination"),
            "reasons": m.get("reasons"),
            "criteria": {
                k: (v.get("status") if isinstance(v, dict) else v)
                for k, v in (m.get("criteria") or {}).items()
            },
            "free_class_headline": (m.get("free_class_score") or {}).get("headline"),
        }
    return out


def main() -> int:
    """Score every pre-registered gate and write the A/B JSON."""
    gates = {
        "K1_single_delta": k1_single_delta(),
        "K2_feasibility": k2_feasibility(),
        "K6_control_reproduces": k6_control_reproduces(),
        "P1_measured_loss_reproduction": p1_measured_loss_reproduction(),
        "WK3d_no_upstate_relocation": wk3d_no_upstate_relocation(),
        "ADVERSE_band": adverse_band(),
        "LOYO_consistency": loyo_consistency(),
    }
    res = {
        "probe": "nyiso-159 zonal loss surface A/B",
        "prereg": [
            "results/calibration/PREREG-nyiso159-zonal-loss-surface-2026-08-30.md"
        ],
        "arms": {"A_control": ARM_A.name, "B_loss": ARM_B.name},
        "gates": gates,
        "report": {
            "K5_offstate_and_drift": k5_drift_report(),
            "prices": prices_report(),
            "c3b_monthly": c3b_monthly_report(),
            "scorecards": scorecards(),
        },
    }

    print("\n=== nyiso-159 pre-registered gates (PREREG §5) ===")
    for name, gate in gates.items():
        print(f"  {name:<34} {'PASS' if gate['passed'] else 'FAIL'}")

    print("\n=== C3a (committed-anchor basis) ===")
    for year in YEARS:
        row = res["report"]["prices"][year]
        print(
            f"  {year}: A {row['c3a_pct']['A']:+.2f}%  B {row['c3a_pct']['B']:+.2f}%  "
            f"(lw {row['lw_lambda']['A']:.2f} -> {row['lw_lambda']['B']:.2f})"
        )

    print("\n=== P1 pair-years ===")
    for row in gates["P1_measured_loss_reproduction"]["pair_years"]:
        print(
            f"  {row['year']} {row['pair']:<32} delta {row['arm_minus_control_spread_delta_usd']:+7.3f} "
            f"measured {row['measured_mean_dmcl_usd']:+7.3f} ratio {row['ratio']:5.2f}x "
            f"{'IN' if row['in_band'] else ('outer' if row['in_outer'] else 'OUTER-MISS')}"
        )

    print("\n=== determination ===")
    for name, sc in res["report"]["scorecards"].items():
        print(f"  {name:<10} {sc['determination'] if sc else 'no metrics.json'}")

    OUT_PATH.write_text(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {OUT_PATH}")
    return 0 if all(g["passed"] for g in gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
