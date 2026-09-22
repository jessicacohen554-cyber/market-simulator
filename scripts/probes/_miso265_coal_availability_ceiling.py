"""miso-265 — is MISO's coal deficit an AVAILABILITY CEILING or economics? ZERO LP.

``RESULT-miso264`` §7 routed this session the claim that *"MISO's coal is held
off by something that is NOT its offer"*, reached from two price-side
instruments. That claim has a direct, cheap, quantity-side test that neither
instrument performed, and this script is it.

The LP's coal generators are bounded above by ``pmax * availability[g, t]``, so
the **most energy the LP could possibly have delivered** from a class in a year
is::

    ceiling_TWh = sum_{g in class} sum_t pmax[g] * availability[g, t] / 1e6

If that ceiling sits BELOW the measured actual, the class's shortfall is not a
dispatch or offer outcome at all — the solved dispatch was never able to reach
the actual, whatever the price did, and the object is the availability input.
If the ceiling sits comfortably ABOVE the actual, the headroom existed and the
shortfall is an economics / commitment outcome, which is where an offer or
commitment lever could bite.

The fleet is rebuilt through the sanctioned no-LP path
(:func:`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`), which carries every
flag the bundle recorded and hard-fails on a dropped gate. MISO's keeper is a
two-config partition split at 2023 (``RESULT-miso263`` §3), and the composite's
span ``meta.json`` carries the **2020 leg's** values — verified before use by
:func:`_assert_partition_leg`, so a 2023+ reconstruction from the same meta
cannot silently inherit the validation leg's reserve configuration.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

#: The two ``ScenarioConfig`` fields MISO's keeper partitions at 2023.
_PARTITION_FIELDS = ("miso_measured_reserve_requirements", "miso_reserve_online_gated")

#: Scored coal rank classes. The LP carries only the coarse ``COAL`` group.
COAL_CLASSES = frozenset({"COAL_BIT", "COAL_PRB", "COAL_LIGNITE"})


def _assert_partition_leg(meta: dict, year: int) -> None:
    """Fail loudly when the span meta's leg does not match ``year``'s leg.

    MISO's 2020-2022 leg runs both partition fields ``False`` (the measured
    reserve requirement table hard-errors before 2023); 2023-2025 runs them
    ``True``. A reconstruction that reads the span meta therefore only speaks
    for the leg that meta belongs to.
    """
    want = year >= 2023
    for field in _PARTITION_FIELDS:
        got = bool(meta.get(field, False))
        if got != want:
            raise SystemExit(
                f"PARTITION MISMATCH: span meta has {field}={got} but year {year} "
                f"belongs to the {'2023+' if want else '2020-2022'} leg "
                f"(expects {want}). Reconstructing {year} from this meta would "
                "measure a fleet the keeper never solved (RESULT-miso263 §3)."
            )


def load_bench(iso: str, year: int) -> dict:
    """Return the committed benchmark part for ``iso``/``year``."""
    path = REPO / "frontend/data/backcast/bench" / iso.upper() / f"{year}.json.gz"
    with gzip.open(path, "rt") as fh:
        return json.load(fh)["bench"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--classes", nargs="*", default=["COAL_BIT", "COAL_PRB", "COAL_LIGNITE"])
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    bundle = REPO / args.bundle
    meta = json.loads((bundle / "meta.json").read_text())
    _assert_partition_leg(meta, args.year)

    state, _ = reconstruct_bundle_fleet(bundle, args.year)
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    codes = np.asarray(fa.plant_code)

    # The LP's ``plant_group`` carries the COARSE class ("COAL"): the BIT / PRB /
    # LIGNITE rank split is a downstream scoring taxonomy, not an LP row label.
    # So coal rows are selected on unit physics (``fuel_type_idx``, rule 18
    # ``[R-PHYSICS]``) exactly as :func:`coal_fuel_inventory.coal_gen_idx` does,
    # and each row is then keyed to a SCORED class through the bench's own
    # per-plant ``group`` — the same crosswalk C1 is scored on.
    from market_sim.data.fleet import FUEL_TYPE_MAP

    # A plant split across classes (e.g. 1004 Edwardsport = CC_REGULAR + COAL_BIT)
    # must map to its COAL rank, never to whichever key happens to come first —
    # this array is only ever applied to rows already selected as coal fuel, and
    # taking the gas label silently drops that plant's whole coal ceiling.
    # VERIFIED for MISO 2020-2025: no plant splits across two coal ranks, so the
    # coal label is unique when it exists; asserted rather than assumed.
    bench_pre = load_bench(args.iso, args.year)
    code_to_class: dict[str, str] = {}
    for key, rec in bench_pre["plants"].items():
        base, grp = key.split(":")[0], rec.get("group", "?")
        if grp in COAL_CLASSES:
            if code_to_class.get(base) in COAL_CLASSES and code_to_class[base] != grp:
                raise SystemExit(f"plant {base} splits across two coal ranks — attribution undefined")
            code_to_class[base] = grp
        else:
            code_to_class.setdefault(base, grp)
    is_coal = np.asarray(fa.fuel_type_idx) == FUEL_TYPE_MAP["coal"]
    group = np.array(
        [code_to_class.get(str(c), "?") if ok else "" for c, ok in zip(codes, is_coal)],
        dtype=object,
    )

    T = avail.shape[1] if avail.ndim == 2 else 1
    # Ceiling energy per LP row: pmax * sum_t availability. Vectorized (rule 2).
    row_ceiling = pmax * avail.sum(axis=1) / 1e6 if avail.ndim == 2 else pmax * T / 1e6
    mean_avail = avail.mean(axis=1) if avail.ndim == 2 else np.ones_like(pmax)

    bench = load_bench(args.iso, args.year)
    cf = bench["classFull"]
    model_hourly = _class_hourly_model(bundle, args.year)

    print(f"=== {args.iso} {args.year} — COAL AVAILABILITY CEILING vs ACTUAL (zero LP) ===")
    print(f"bundle: {args.bundle}   LP rows: {len(pmax)}   hours: {T}")
    print()
    hdr = f"{'class':14} {'rows':>5} {'pmax GW':>8} {'ceiling':>9} {'model':>8} {'actual':>8} {'head':>8} {'util':>6}"
    print(hdr)
    print("-" * len(hdr))
    for klass in args.classes:
        sel = group == klass
        if not sel.any():
            print(f"{klass:14} {'--':>5}  (no rows)")
            continue
        ceil = float(row_ceiling[sel].sum())
        mw = float(pmax[sel].sum()) / 1e3
        act = float(cf.get(klass, 0.0))
        mod = model_hourly.get(klass, float("nan"))
        util = mod / ceil if ceil > 0 else float("nan")
        print(
            f"{klass:14} {int(sel.sum()):5d} {mw:8.2f} {ceil:9.2f} {mod:8.2f} {act:8.2f} "
            f"{ceil - act:+8.2f} {util:6.3f}"
        )
    print()
    print("  ceiling = sum_g pmax[g] * sum_t availability[g,t]  (the LP's hard upper bound)")
    print("  head    = ceiling - actual.  NEGATIVE => the actual was UNREACHABLE for the LP.")
    print("  util    = model / ceiling.   LOW util with POSITIVE head => economics, not availability.")

    # Per-plant, for the class carrying the gate failure.
    target = args.classes[0]
    sel = group == target
    per_plant_ceiling: dict[str, float] = defaultdict(float)
    per_plant_mw: dict[str, float] = defaultdict(float)
    per_plant_avail: dict[str, list] = defaultdict(list)
    for i in np.nonzero(sel)[0]:
        key = str(codes[i])
        per_plant_ceiling[key] += float(row_ceiling[i])
        per_plant_mw[key] += float(pmax[i])
        per_plant_avail[key].append((float(pmax[i]), float(mean_avail[i])))
    bp = {c: r for c, r in bench["plants"].items() if r.get("group") == target}
    rows = []
    for code, rec in bp.items():
        base = code.split(":")[0]
        ceil = per_plant_ceiling.get(base, 0.0)
        mws = per_plant_avail.get(base, [])
        wavail = (
            sum(m * a for m, a in mws) / sum(m for m, a in mws) if sum(m for m, a in mws) > 0 else 0.0
        )
        rows.append(
            {
                "code": code,
                "name": rec.get("name", "?"),
                "mw": per_plant_mw.get(base, 0.0),
                "ceiling": ceil,
                "actual": float(rec.get("e_ann") or 0.0),
                "campd": float(rec.get("c_ann") or 0.0),
                "avail": wavail,
            }
        )
    rows.sort(key=lambda r: r["ceiling"] - r["actual"])
    print()
    print(f"=== {target} per plant — ceiling vs actual (worst headroom first) ===")
    h2 = f"{'code':>12} {'plant':26} {'LP MW':>8} {'avail':>6} {'ceiling':>8} {'actual':>8} {'head':>8}"
    print(h2)
    print("-" * len(h2))
    for r in rows[: args.top]:
        print(
            f"{r['code']:>12} {r['name'][:26]:26} {r['mw']:8.0f} {r['avail']:6.3f} "
            f"{r['ceiling']:8.3f} {r['actual']:8.3f} {r['ceiling'] - r['actual']:+8.3f}"
        )
    short = [r for r in rows if r["ceiling"] < r["actual"] - 1e-9]
    print()
    print(
        f"plants whose CEILING is BELOW their measured actual: {len(short)} "
        f"(sum of the unreachable energy: {sum(r['actual'] - r['ceiling'] for r in short):.3f} TWh)"
    )
    return 0


def _class_hourly_model(bundle: Path, year: int) -> dict[str, float]:
    """Return model annual TWh per class from the bundle's committed sidecar."""
    import pandas as pd

    path = Path(bundle) / "hourly" / f"class_hourly_{year}.parquet"
    if not path.is_file():
        return {}
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    return {str(k): float(v) / 1e6 for k, v in df.groupby("klass")["mw"].sum().items()}


if __name__ == "__main__":
    sys.exit(main())
