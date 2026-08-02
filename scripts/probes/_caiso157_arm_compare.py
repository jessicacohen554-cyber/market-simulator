"""caiso-157 probe — compare the four partition-restoration arms.

Read-only over the arms' own written bundles. Reports, per arm and per year:

* **K1 input-state fidelity** — the ``meta.shared_inputs`` pins, which is the
  only trustworthy statement of what a solve actually read (this session stages
  ``data/clean`` around each invocation; the pins are what verify the staging
  worked, never the staging itself).
* **K3 config equality** — every ScenarioConfig field that differs between arms,
  provenance keys excluded. Must be empty.
* **The seam** — hours whose total P1 ``import`` dispatch sits at the retired
  fitted 7,500 MW ``WECC_import_simultaneous`` cap, and the import distribution.
  The whole point of the restoration is that this count goes to zero.
* **λ** — load-weighted and simple mean zonal price, plus the A→B delta split by
  hour-of-day band, so the predicted overnight concentration (PREREG section 3.3)
  is testable rather than asserted.
* **Class dispatch** — annual TWh per class per arm, so the displaced resource
  is named rather than inferred.

Usage::

    PYTHONPATH=. python scripts/probes/_caiso157_arm_compare.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

#: The residual-identified fallback the CAISO import node uses when
#: deliverability Part A no-ops (DOF-ledger row WECC_import_simultaneous.cap_mw).
_FITTED_SEAM_MW: float = 7500.0
_AT_CAP_TOL_MW: float = 0.5

#: meta.json keys that legitimately differ between two arms of the same recipe.
_PROVENANCE_KEYS: frozenset[str] = frozenset(
    {"timestamp", "git_sha", "basis_sha", "note", "shared_inputs", "environment",
     "highspy_version"}
)

_ARMS: dict[str, str] = {
    "A_control": "caiso157_control_A",
    "B_restore": "caiso157_restore_B",
    "C_capdel": "caiso157_capdel_C",
    "D_ror": "caiso157_ror_D",
}


def _load_meta(bundle: Path) -> dict | None:
    """Return a bundle's ``meta.json``, or ``None`` when it has not been written."""
    path = bundle / "meta.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def _flatten(meta: dict) -> dict:
    """Flatten meta into comparable scalar fields, provenance keys dropped."""
    flat: dict = {}
    for key, value in meta.items():
        if key in _PROVENANCE_KEYS:
            continue
        if key == "coal_prb_sigmoid_overrides" and isinstance(value, dict):
            for sub, subval in value.items():
                flat[f"overrides.{sub}"] = subval
            continue
        flat[key] = json.dumps(value, sort_keys=True, default=str)
    return flat


def report_inputs(root: Path) -> pd.DataFrame:
    """K1: what each arm's own meta says it read."""
    rows = []
    for label, name in _ARMS.items():
        meta = _load_meta(root / name)
        if meta is None:
            rows.append({"arm": label, "bundle": name, "state": "NOT SOLVED"})
            continue
        pins = meta.get("shared_inputs") or {}
        rows.append(
            {
                "arm": label,
                "bundle": name,
                "state": "solved",
                "years": meta.get("years"),
                "capacity_deliverability": "capacity_deliverability" in pins,
                "hydro_plant_modes": "hydro_plant_modes" in pins,
                "git_sha": meta.get("git_sha"),
            }
        )
    return pd.DataFrame(rows)


def report_config_equality(root: Path) -> list[str]:
    """K3: ScenarioConfig fields that differ between any two solved arms."""
    flats = {}
    for label, name in _ARMS.items():
        meta = _load_meta(root / name)
        if meta is not None:
            flats[label] = _flatten(meta)
    if len(flats) < 2:
        return []
    keys = set().union(*(set(f) for f in flats.values()))
    diffs = []
    for key in sorted(keys):
        values = {label: flat.get(key) for label, flat in flats.items()}
        if len(set(map(str, values.values()))) > 1:
            diffs.append(f"{key}: {values}")
    return diffs


def _import_series(bundle: Path, year: int) -> pd.Series | None:
    """Return the P1 hourly total import MW for one arm-year."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.is_file():
        return None
    frame = pd.read_parquet(path)
    frame = frame[(frame["pass"] == "P1") & (frame["klass"] == "import")]
    if frame.empty:
        return None
    return frame.set_index("hour")["mw"].sort_index()


def report_seam(root: Path, years: list[int]) -> pd.DataFrame:
    """Hours pinned at the retired fitted cap, per arm-year."""
    rows = []
    for label, name in _ARMS.items():
        for year in years:
            imp = _import_series(root / name, year)
            if imp is None:
                continue
            at_cap = imp >= _FITTED_SEAM_MW - _AT_CAP_TOL_MW
            rows.append(
                {
                    "arm": label,
                    "year": year,
                    "hours_at_7500": int(at_cap.sum()),
                    "mean_MW": round(float(imp.mean()), 1),
                    "p95_MW": round(float(imp.quantile(0.95)), 1),
                    "max_MW": round(float(imp.max()), 1),
                    "TWh": round(float(imp.sum()) / 1e6, 3),
                }
            )
    return pd.DataFrame(rows)


def report_interface_groups(root: Path, years: list[int]) -> pd.DataFrame:
    """The seam evidence that matters: each interface group's LIMIT and DUAL.

    ``hourly/network_<year>.parquet`` records every link and interface group's
    hourly flow, dual and bounds, so this reads the constraint *as the LP saw
    it* rather than inferring it from dispatch. The simultaneous-import group
    is the row the restoration moves: at the degraded 7,500 MW fitted scalar it
    binds with a non-zero dual; at the published MIC it should sit above both
    corridor envelopes and price at exactly 0.000 in every hour (caiso-133).
    """
    rows = []
    for label, name in _ARMS.items():
        for year in years:
            path = root / name / "hourly" / f"network_{year}.parquet"
            if not path.is_file():
                continue
            frame = pd.read_parquet(path)
            frame = frame[(frame["pass"] == "P1") & (frame["kind"] == "group")]
            for group, part in frame.groupby("name", observed=True):
                rows.append(
                    {
                        "arm": label,
                        "year": year,
                        "group": str(group),
                        "limit_MW": round(float(part["limit_up"].max()), 1),
                        "binding_h": int((part["dual"].abs() > 1e-6).sum()),
                        "max_flow_MW": round(float(part["mw"].max()), 1),
                        "rent_$M": round(float((part["dual"] * part["mw"]).sum()) / 1e6, 3),
                    }
                )
    return pd.DataFrame(rows)


def _price_frame(bundle: Path, year: int) -> pd.DataFrame | None:
    """Return the P1 zonal price/demand frame for one arm-year."""
    path = bundle / "hourly" / f"system_{year}.parquet"
    if not path.is_file():
        return None
    frame = pd.read_parquet(path)
    frame = frame[frame["pass"] == "P1"]
    return frame if not frame.empty else None


def report_prices(root: Path, years: list[int]) -> pd.DataFrame:
    """Load-weighted and simple mean λ per arm-year, plus hour-of-day bands."""
    rows = []
    for label, name in _ARMS.items():
        for year in years:
            frame = _price_frame(root / name, year)
            if frame is None:
                continue
            lw = float((frame["price"] * frame["demand"]).sum() / frame["demand"].sum())
            hod = frame["hour"] % 24
            night = frame[hod.isin(range(0, 6))]
            belly = frame[hod.isin(range(9, 16))]
            evening = frame[hod.isin(range(17, 22))]
            rows.append(
                {
                    "arm": label,
                    "year": year,
                    "lw_mean": round(lw, 3),
                    "mean": round(float(frame["price"].mean()), 3),
                    "night_0_5": round(float(night["price"].mean()), 3),
                    "belly_9_15": round(float(belly["price"].mean()), 3),
                    "evening_17_21": round(float(evening["price"].mean()), 3),
                }
            )
    return pd.DataFrame(rows)


def report_classes(root: Path, years: list[int]) -> pd.DataFrame:
    """Annual TWh per class per arm-year (wide by arm for easy differencing)."""
    frames = []
    for label, name in _ARMS.items():
        for year in years:
            path = root / name / "hourly" / f"class_hourly_{year}.parquet"
            if not path.is_file():
                continue
            frame = pd.read_parquet(path)
            frame = frame[frame["pass"] == "P1"]
            twh = frame.groupby("klass")["mw"].sum() / 1e6
            frames.append(twh.rename((label, year)))
    if not frames:
        return pd.DataFrame()
    wide = pd.concat(frames, axis=1).round(3)
    wide.columns = pd.MultiIndex.from_tuples(wide.columns)
    return wide


def main() -> None:
    """Print every comparison section for whichever arms have been solved."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", default="results/calibration")
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = parser.parse_args()
    root = Path(args.results_root)

    print("=" * 78)
    print("K1 — input state, read back from each arm's OWN meta.shared_inputs")
    print("=" * 78)
    print(report_inputs(root).to_string(index=False))

    print("\n" + "=" * 78)
    print("K3 — ScenarioConfig equality across solved arms (must be empty)")
    print("=" * 78)
    diffs = report_config_equality(root)
    print("\n".join(diffs) if diffs else "no differences — K3 PASS")

    print("\n" + "=" * 78)
    print(f"SEAM — hours pinned at the retired fitted {_FITTED_SEAM_MW:.0f} MW cap")
    print("=" * 78)
    seam = report_seam(root, args.years)
    print(seam.to_string(index=False) if not seam.empty else "no hourly sidecars yet")

    print("\n" + "=" * 78)
    print("INTERFACE GROUPS — limit, binding hours (|dual| > 0) and congestion rent")
    print("=" * 78)
    groups = report_interface_groups(root, args.years)
    print(groups.to_string(index=False) if not groups.empty else "no network sidecars yet")

    print("\n" + "=" * 78)
    print("PRICE — P1 zonal λ, load-weighted and by hour-of-day band ($/MWh)")
    print("=" * 78)
    prices = report_prices(root, args.years)
    print(prices.to_string(index=False) if not prices.empty else "no sidecars yet")

    print("\n" + "=" * 78)
    print("CLASS DISPATCH — annual TWh (P1)")
    print("=" * 78)
    classes = report_classes(root, args.years)
    print(classes.to_string() if not classes.empty else "no sidecars yet")


if __name__ == "__main__":
    main()
