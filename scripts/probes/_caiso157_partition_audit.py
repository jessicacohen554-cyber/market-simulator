"""caiso-157 probe — audit the derived-CLEAN-partition state of every bundle.

Read-only. Answers three questions the caiso-157 pre-registration is built on,
each from committed bytes only (no LP, no solve, no network):

1. **Which bundles solved on which derived inputs?** ``meta.shared_inputs`` pins
   exactly the derived-not-committed inputs a solve read
   (``scripts.lib.bundle_io.write_derived_solve_inputs``), and an ABSENT
   partition records nothing — so a bundle whose config ARMS a
   partition-backed mechanism but carries no pin for it solved with that
   mechanism silently inert. Reports every such (bundle, mechanism) pair across
   all ISOs, which both dates the CAISO regression and bounds its blast radius.

2. **Does the retired fitted import scalar actually bind?** For a CAISO bundle
   with committed ``hourly/class_hourly_<year>.parquet`` sidecars, counts the P1
   hours whose total ``import`` dispatch sits at
   ``iso_configs`` ``WECC_import_simultaneous.cap_mw`` (7,500 MW) — the value the
   keeper's own DOF ledger declares "not in the keeper binding path". Breaks the
   count out by hour-of-day and month, and reports the Sep-Dec 2025 share (the
   window of the ledgered C3a-2025 caveat).

3. **What would the accurate seam be?** Resolves the published CAISO
   branch-group MIC sum per solve year through the SAME loader the solve uses
   (``interchange.spec`` Part A: ``import_limit_by_area`` -> ``aggregate_by_zone``
   -> ``IMPORT_ZONE``), so the reported number is the one the LP would receive.

Usage::

    PYTHONPATH=. python scripts/probes/_caiso157_partition_audit.py
    PYTHONPATH=. python scripts/probes/_caiso157_partition_audit.py \
        --bundle results/calibration/caiso153_reid_B
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

#: Mechanism -> (config-field lookup, ``shared_inputs`` pin key). The field is
#: read from ``meta.json`` top level first, then from the generic override
#: channel ``coal_prb_sigmoid_overrides`` (where the CAISO keeper carries it).
_PARTITION_MECHANISMS: dict[str, tuple[str, str]] = {
    "capacity_deliverability_limits": (
        "capacity_deliverability_limits",
        "capacity_deliverability",
    ),
    "hydro_ror_split": ("hydro_ror_split", "hydro_plant_modes"),
}

#: The residual-identified fallback the CAISO import node falls back to when
#: deliverability Part A no-ops (``iso_configs`` CAISO ``interface_limits``,
#: DOF-ledger row ``WECC_import_simultaneous.cap_mw``, scalar-remediation
#: B-CAI-1). Not a tunable here — the probe only *detects* it binding.
_CAISO_FITTED_SEAM_MW: float = 7500.0

#: At-cap tolerance in MW. The LP writes the bound exactly; 0.5 MW absorbs
#: float32 sidecar round-trip only.
_AT_CAP_TOL_MW: float = 0.5


def _armed(meta: dict, field: str) -> bool:
    """Return whether ``field`` is armed in a bundle's meta, either channel."""
    if bool(meta.get(field)):
        return True
    overrides = meta.get("coal_prb_sigmoid_overrides") or {}
    return bool(overrides.get(field))


def audit_bundles(root: Path) -> pd.DataFrame:
    """Return one row per (bundle, mechanism) with armed/pinned state."""
    rows: list[dict] = []
    for meta_path in sorted(root.glob("*/meta.json")):
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:  # a partial/aborted bundle is not an audit finding
            continue
        pins = meta.get("shared_inputs") or {}
        for mech, (field, pin) in _PARTITION_MECHANISMS.items():
            armed = _armed(meta, field)
            if not armed:
                continue
            rows.append(
                {
                    "iso": meta.get("iso"),
                    "timestamp": meta.get("timestamp", ""),
                    "bundle": meta_path.parent.name,
                    "mechanism": mech,
                    "armed": armed,
                    "pinned": pin in pins,
                    "degraded": armed and pin not in pins,
                }
            )
    return pd.DataFrame(rows).sort_values(["iso", "timestamp", "mechanism"])


def _load_meta(bundle: Path) -> dict | None:
    """Return a bundle's ``meta.json``, or ``None`` when it is absent/unreadable."""
    path = bundle / "meta.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def audit_keepers() -> pd.DataFrame:
    """Return the same armed-vs-pinned check for each ISO's DESIGNATED keeper.

    The bundle sweep answers "which runs were degraded"; this answers the
    question that actually matters — "is any ISO's *current keeper* advertising
    a mechanism that never ran". Resolves each ISO's keeper shard to its bundle
    through the registry sidecar, so it reads exactly what the dashboard claims.
    """
    rows: list[dict] = []
    for shard in sorted(Path("frontend/data/backcast/keepers").glob("*.json")):
        if shard.name == "index.json":
            continue
        keeper = json.loads(shard.read_text())
        iso, run_id = keeper.get("iso"), keeper.get("keeper")
        sidecar = Path(f"frontend/data/backcast/registry/{run_id}.json")
        if not sidecar.is_file():
            rows.append({"iso": iso, "keeper": run_id, "state": "sidecar absent"})
            continue
        bundle = Path(json.loads(sidecar.read_text()).get("bundle", ""))
        meta = _load_meta(bundle)
        if meta is None:
            rows.append({"iso": iso, "keeper": run_id, "state": "bundle absent"})
            continue
        pins = set(meta.get("shared_inputs") or {})
        degraded = [
            f"{flag} -> {pin}"
            for flag, (field, pin) in _PARTITION_MECHANISMS.items()
            if _armed(meta, field) and pin not in pins
        ]
        rows.append(
            {
                "iso": iso,
                "keeper": run_id,
                "state": "solved",
                "degraded": "; ".join(degraded) if degraded else "none",
            }
        )
    return pd.DataFrame(rows)


def audit_seam_binding(bundle: Path) -> pd.DataFrame:
    """Count P1 hours whose total import sits at the fitted CAISO seam cap."""
    rows: list[dict] = []
    for path in sorted((bundle / "hourly").glob("class_hourly_*.parquet")):
        year = int(path.stem.rsplit("_", 1)[1])
        frame = pd.read_parquet(path)
        frame = frame[(frame["pass"] == "P1") & (frame["klass"] == "import")]
        if frame.empty:
            continue
        imp = frame.set_index("hour")["mw"].sort_index()
        at_cap = imp >= _CAISO_FITTED_SEAM_MW - _AT_CAP_TOL_MW
        stamps = pd.to_datetime(
            pd.Series(imp.index, index=imp.index), unit="h", origin=f"{year}-01-01"
        )
        sep_dec = stamps.dt.month.isin([9, 10, 11, 12])
        rows.append(
            {
                "year": year,
                "hours_at_cap": int(at_cap.sum()),
                "share_pct": round(100.0 * float(at_cap.mean()), 2),
                "mean_import_mw": round(float(imp.mean()), 1),
                "p95_import_mw": round(float(imp.quantile(0.95)), 1),
                "max_import_mw": round(float(imp.max()), 1),
                "top_hours_of_day": (
                    pd.Series((imp.index % 24)[at_cap.to_numpy()])
                    .value_counts()
                    .head(5)
                    .index.tolist()
                ),
                "top_months": (
                    stamps.dt.month[at_cap.to_numpy()].value_counts().head(5).index.tolist()
                ),
                "sep_dec_at_cap": int(at_cap[sep_dec.to_numpy()].sum()),
                "sep_dec_hours": int(sep_dec.sum()),
                "sep_dec_share_pct": round(
                    100.0 * float(at_cap[sep_dec.to_numpy()].mean()), 2
                ),
            }
        )
    return pd.DataFrame(rows)


def resolve_published_seam(years: list[int]) -> pd.DataFrame:
    """Resolve the published MIC seam the solve would receive, per year."""
    from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
    from market_sim.data import capacity_deliverability as capdel
    from market_sim.model.interchange.spec import IMPORT_ZONE

    rows: list[dict] = []
    for year in years:
        delivery_year = capdel.resolve_delivery_year("CAISO", year)
        season = capdel.resolve_season("CAISO")
        by_area = capdel.import_limit_by_area("CAISO", delivery_year, season)
        types = capdel.area_types_by_area("CAISO", delivery_year, season, "import_limit")
        by_zone, _ = aggregate_by_zone("CAISO", by_area, types)
        rows.append(
            {
                "year": year,
                "delivery_year": delivery_year,
                "n_areas": len(by_area),
                "seam_mw": by_zone.get(IMPORT_ZONE.get("CAISO")),
                "fitted_fallback_mw": _CAISO_FITTED_SEAM_MW,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Print the three audit sections."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-root",
        default="results/calibration",
        help="root holding the bundle directories",
    )
    parser.add_argument(
        "--bundle",
        default="results/calibration/caiso153_reid_B",
        help="CAISO bundle whose committed hourlies carry the seam-binding test",
    )
    args = parser.parse_args()

    print("=" * 78)
    print("1. ARMED-BUT-UNPINNED derived partitions, every bundle on disk")
    print("=" * 78)
    audit = audit_bundles(Path(args.results_root))
    if audit.empty:
        print("no bundle arms a partition-backed mechanism")
    else:
        print(audit.to_string(index=False))
        degraded = audit[audit["degraded"]]
        print(
            f"\n  DEGRADED: {len(degraded)} of {len(audit)} armed (bundle, mechanism) "
            f"pairs; ISOs affected: {sorted(degraded['iso'].dropna().unique().tolist())}"
        )

    print()
    print("=" * 78)
    print("1b. The same check on each ISO's DESIGNATED KEEPER")
    print("=" * 78)
    print(audit_keepers().to_string(index=False))

    print()
    print("=" * 78)
    print(f"2. Does the RETIRED fitted seam ({_CAISO_FITTED_SEAM_MW:.0f} MW) bind? "
          f"— {args.bundle}")
    print("=" * 78)
    binding = audit_seam_binding(Path(args.bundle))
    print(binding.to_string(index=False) if not binding.empty else "no hourly sidecars")

    print()
    print("=" * 78)
    print("3. The PUBLISHED MIC seam the accurate input would apply")
    print("=" * 78)
    years = sorted(binding["year"].tolist()) if not binding.empty else [2023, 2024, 2025]
    try:
        print(resolve_published_seam(years).to_string(index=False))
    except Exception as exc:  # partition absent is itself the answer
        print(f"could not resolve the published seam ({exc!r}) — is the clean "
              "partition present? run scripts/data/curate_capacity_deliverability.py")


if __name__ == "__main__":
    main()
