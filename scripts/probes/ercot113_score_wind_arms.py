"""ERCOT-113 Task B scorer: A/B the per-zone ERCOT wind SHAPE.

Scores the treatment arm against the criteria fixed in
``results/calibration/PRECOMMIT-ercot113-wind-zone-shape-2026-07-26.md`` BEFORE
any result was read (rule 1):

* **W0 arming proof** — ``run_config.json`` records ``ercot_wind_zone_shape``
  and the zonal wind allocation differs from baseline in every year. An
  identical split means the run is INERT and no verdict is readable.
* **W1 aggregate-preservation falsifier** — annual ISO wind energy unchanged
  within 0.1 % every year. The mechanism is a pure spatial redistribution
  (``renewables._redistribute_preserving_total`` holds the ISO aggregate
  exactly every hour), so a larger move means it is mis-specified.
* **W2 PRIMARY quintile tilt** — the tilt spread (model-vs-actual % at the
  lowest actual-wind quintile minus at the highest) must narrow in >= 2 of 3
  years with no year widening by more than 1.0 pp.
* **W3 scarcity-hour cheap-stack surplus** — mean (model wind - actual wind) MW
  over hours with actual RT >= $200/MWh must not worsen by more than 150 MW.
* **W4 scarcity price** — C3a within 2 pp and C3c within 5 h of baseline, using
  the definitions pinned in ``scripts/probes/ercot112_score_coal_arms.py``.
* **W5 LOYO** (rule 24) — same direction test as W2, stated separately.

Annual wind TWh is deliberately NOT a criterion: the mechanism cannot move it
by construction, so it measures zero. It is printed as an invariant check (W1),
never as evidence of skill.

Model series are read from each bundle's committed ``hourly/`` sidecars
(rule 15 — no re-solve); actuals are the EIA-930 hourly benchmark.

Usage:
    python scripts/probes/ercot113_score_wind_arms.py \
        --baseline results/calibration/ercot_netrev_margin \
        --arm      results/calibration/ercot113_wind_zone_shape
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402

YEARS = (2023, 2024, 2025)
_N_QUINTILES = 5

# Thresholds — fixed in the pre-commit doc, never re-tuned here.
_W1_MAX_ANNUAL_MOVE_PCT = 0.1
_W2_MAX_WIDEN_PP = 1.0
_W3_MAX_WORSEN_MW = 150.0
_C3A_MAX_DEGRADE_PP = 2.0
_C3C_MAX_DEGRADE_HOURS = 5
_C3C_THRESHOLD = 200.0
# Same ORDC-inclusive price construction the ERCOT-112 scorer pinned.
_PRICE_PARTS = ("price", "ordc_adder", "rtordpa_overlay")


def _wind_hourly(bundle: Path, year: int) -> np.ndarray | None:
    """Model ISO-wide wind MW per hour from the class sidecar."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[(df["pass"] == "P1") & (df["klass"].astype(str).str.lower() == "wind")]
    if df.empty:
        return None
    return (
        df.groupby("hour")["mw"]
        .sum()
        .reindex(range(8760), fill_value=0.0)
        .to_numpy(dtype=float)
    )


def _system_price(bundle: Path, year: int) -> np.ndarray | None:
    """Load-weighted ORDC-inclusive system price per hour, or ``None``."""
    path = bundle / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"].copy()
    if df.empty:
        return None
    df["_p"] = sum(df[c] for c in _PRICE_PARTS if c in df.columns)
    lw = df.groupby("hour").apply(
        lambda d: np.average(d["_p"], weights=d["demand"]), include_groups=False
    )
    return lw.reindex(range(8760)).to_numpy(dtype=float)


def _actual_price(year: int) -> np.ndarray | None:
    """Actual ERCOT RT settlement price per hour, or ``None``."""
    path = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["year"] == year].sort_values("hour")
    return df["rt"].to_numpy(dtype=float) if not df.empty else None


def _zonal_wind(bundle: Path, year: int) -> pd.Series | None:
    """Per-zone annual model wind MWh, for the W0 arming proof.

    Returns ``None`` when the bundle carries no zone-resolved wind sidecar, in
    which case W0 falls back to the ``run_config.json`` gate record alone.
    """
    for name in (f"zone_hourly_{year}.parquet", f"zonal_{year}.parquet"):
        path = bundle / "hourly" / name
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if "klass" in df.columns:
            df = df[df["klass"].astype(str).str.lower() == "wind"]
        if df.empty or "zone" not in df.columns:
            continue
        col = "mw" if "mw" in df.columns else df.columns[-1]
        return df.groupby("zone")[col].sum()
    return None


def _zonal_price_signature(bundle: Path, year: int) -> pd.Series | None:
    """Per-zone mean P1 price — the downstream W0 arming proof.

    The committed ERCOT bundles carry no zone-resolved WIND sidecar (only
    ISO-wide ``class_hourly`` and per-zone ``system``), so a moved wind split
    cannot be read directly. It is still observable downstream: relocating wind
    between zones changes where the West/Panhandle ceiling and the zonal links
    bind, which moves the zonal duals. Identical zonal prices in every zone and
    every hour therefore mean the mechanism never reached the LP.
    """
    path = bundle / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    if df.empty or "zone" not in df.columns:
        return None
    return df.groupby("zone")["price"].mean()


def _gate_recorded(bundle: Path) -> bool | None:
    """Whether ``run_config.json`` records the wind-shape gate as armed."""
    path = bundle / "run_config.json"
    if not path.exists():
        return None
    cfg = json.loads(path.read_text())
    sc = cfg.get("scenario_config", {})
    cf = cfg.get("calibration_flags", {})
    for src in (sc, cf):
        if isinstance(src, dict) and "ercot_wind_zone_shape" in src:
            return bool(src["ercot_wind_zone_shape"])
    return None


def _quintile_tilt(model: np.ndarray, actual: np.ndarray) -> list[float]:
    """Model-vs-actual % by quintile of ACTUAL wind (lowest first)."""
    order = np.argsort(actual, kind="stable")
    out = []
    for chunk in np.array_split(order, _N_QUINTILES):
        a = actual[chunk].sum()
        m = model[chunk].sum()
        out.append((m / a - 1.0) * 100.0 if a > 0 else np.nan)
    return out


def year_row(bundle: Path, year: int) -> dict | None:
    """Wind totals, quintile tilt, scarcity surplus and C3a/C3c for a year."""
    model = _wind_hourly(bundle, year)
    act = load_eia_hourly_benchmark("ERCOT", year)
    if model is None or act is None:
        return None
    actual = np.asarray(act["wind"], dtype=float)
    q = _quintile_tilt(model, actual)

    a_price = _actual_price(year)
    surplus = np.nan
    if a_price is not None:
        hot = a_price >= _C3C_THRESHOLD
        if hot.any():
            surplus = float((model[hot] - actual[hot]).mean())

    price = _system_price(bundle, year)
    c3a = c3c = None
    if price is not None and a_price is not None:
        c3a = float((np.nanmean(price) / a_price.mean() - 1.0) * 100.0)
        c3c = int((price >= _C3C_THRESHOLD).sum())

    return {
        "year": year,
        "wind_twh": model.sum() / 1e6,
        "act_wind_twh": actual.sum() / 1e6,
        "quintiles": q,
        "tilt": q[0] - q[-1],
        "scarcity_surplus_mw": surplus,
        "c3a": c3a,
        "c3c": c3c,
        "zonal": _zonal_wind(bundle, year),
    }


def main(argv: list[str] | None = None) -> int:
    """Score the arm against the pre-committed W0-W5 criteria."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    args = ap.parse_args(argv)

    base = {y: year_row(args.baseline, y) for y in YEARS}
    arm = {y: year_row(args.arm, y) for y in YEARS}

    print(f"{'yr':<6}{'arm':<10}{'wind TWh':>10}{'actual':>9}"
          f"{'Q1':>8}{'Q2':>8}{'Q3':>8}{'Q4':>8}{'Q5':>8}{'tilt':>8}")
    for y in YEARS:
        for name, tbl in (("baseline", base), ("wind-shape", arm)):
            r = tbl[y]
            if r is None:
                print(f"{y:<6}{name:<10}  -- not solved --")
                continue
            qs = "".join(f"{v:8.1f}" for v in r["quintiles"])
            print(f"{y:<6}{name:<10}{r['wind_twh']:10.2f}{r['act_wind_twh']:9.2f}"
                  f"{qs}{r['tilt']:8.2f}")

    print("\n=== PRE-COMMITTED VERDICT ===")

    # --- W0 arming proof -------------------------------------------------
    gate = _gate_recorded(args.arm)
    zonal_moved, zonal_note = [], []
    for y in YEARS:
        b, a = base[y], arm[y]
        if b is None or a is None:
            continue
        zb, za = b["zonal"], a["zonal"]
        if zb is None or za is None:
            # No zone-resolved wind sidecar: fall back to the downstream proof
            # — a moved wind split must move the zonal duals.
            zonal_note.append(y)
            pb = _zonal_price_signature(args.baseline, y)
            pa = _zonal_price_signature(args.arm, y)
            if pb is None or pa is None:
                continue
            common = pb.index.intersection(pa.index)
            zonal_moved.append(bool(common.size and not np.allclose(
                pb[common].to_numpy(float), pa[common].to_numpy(float),
                rtol=1e-9)))
            continue
        common = zb.index.intersection(za.index)
        zonal_moved.append(bool(common.size and not np.allclose(
            zb[common].to_numpy(float), za[common].to_numpy(float), rtol=1e-9)))
    w0 = bool(gate) and (all(zonal_moved) if zonal_moved else True)
    detail = f"gate recorded={gate}"
    if zonal_moved:
        detail += f", zonal signal moved in {sum(zonal_moved)}/{len(zonal_moved)} yr"
    if zonal_note:
        detail += f" (no zone wind sidecar for {zonal_note}; zonal-price proof)"
    print(f"  W0 arming proof: {'PASS' if w0 else 'FAIL — INERT'}  ({detail})")

    # --- W1 aggregate-preservation falsifier ------------------------------
    w1_bad = []
    for y in YEARS:
        b, a = base[y], arm[y]
        if b is None or a is None:
            continue
        move = abs(a["wind_twh"] / b["wind_twh"] - 1.0) * 100.0
        if move > _W1_MAX_ANNUAL_MOVE_PCT:
            w1_bad.append(f"{y} {move:.3f}%")
        print(f"     W1 {y}: annual wind {b['wind_twh']:.3f} -> "
              f"{a['wind_twh']:.3f} TWh ({move:+.4f} %)")
    print(f"  W1 aggregate preserved (<= {_W1_MAX_ANNUAL_MOVE_PCT} %): "
          f"{'PASS' if not w1_bad else f'FAIL {w1_bad}'}")

    # --- W2 / W5 quintile tilt --------------------------------------------
    improved, widened = [], []
    for y in YEARS:
        b, a = base[y], arm[y]
        if b is None or a is None:
            continue
        db, da = b["tilt"], a["tilt"]
        ok = abs(da) < abs(db)
        improved.append(ok)
        if abs(da) - abs(db) > _W2_MAX_WIDEN_PP:
            widened.append(f"{y} {db:.2f}->{da:.2f}")
        print(f"     W2 {y}: tilt spread {db:6.2f} -> {da:6.2f} pp  "
              f"{'NARROWS' if ok else 'WIDENS'}")
    n_ok = sum(improved)
    w2 = n_ok >= 2 and not widened
    print(f"  W2 tilt narrows (>= 2/3, none widening > {_W2_MAX_WIDEN_PP} pp): "
          f"{'PASS' if w2 else f'FAIL (ok={n_ok}/3, widened={widened})'}")

    # --- W3 scarcity-hour surplus -----------------------------------------
    w3_bad = []
    for y in YEARS:
        b, a = base[y], arm[y]
        if b is None or a is None or not np.isfinite(b["scarcity_surplus_mw"]):
            continue
        d = a["scarcity_surplus_mw"] - b["scarcity_surplus_mw"]
        if d > _W3_MAX_WORSEN_MW:
            w3_bad.append(f"{y} +{d:.0f} MW")
        print(f"     W3 {y}: scarcity-hour wind surplus "
              f"{b['scarcity_surplus_mw']:+.0f} -> {a['scarcity_surplus_mw']:+.0f} MW "
              f"({d:+.0f})")
    print(f"  W3 scarcity surplus not worse by > {_W3_MAX_WORSEN_MW} MW: "
          f"{'PASS' if not w3_bad else f'FAIL {w3_bad}'}")

    # --- W4 scarcity price -------------------------------------------------
    c3_bad = []
    for y in YEARS:
        b, a = base[y], arm[y]
        if b is None or a is None or b["c3a"] is None or a["c3a"] is None:
            continue
        if a["c3a"] < b["c3a"] - _C3A_MAX_DEGRADE_PP:
            c3_bad.append(f"{y} C3a {b['c3a']:.1f}->{a['c3a']:.1f}")
        if a["c3c"] < b["c3c"] - _C3C_MAX_DEGRADE_HOURS:
            c3_bad.append(f"{y} C3c {b['c3c']}->{a['c3c']}")
        print(f"     W4 {y}: C3a {b['c3a']:6.1f} -> {a['c3a']:6.1f} % | "
              f"C3c {b['c3c']:4d} -> {a['c3c']:4d} h")
    print(f"  W4 scarcity price not degraded: "
          f"{'PASS' if not c3_bad else f'FAIL {c3_bad}'}")

    print(f"  W5 LOYO (>= 2/3 improve, none degrade > {_W2_MAX_WIDEN_PP} pp): "
          f"{'PASS' if w2 else 'FAIL'}")

    verdict = ("INERT" if not w0 else
               "FAIL (W1 falsifier)" if w1_bad else
               "CANDIDATE" if (w2 and not w3_bad and not c3_bad) else
               "REFUTED")
    print(f"\n  ==> ADJUDICATION: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
