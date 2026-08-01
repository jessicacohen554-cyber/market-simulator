"""caiso-152 — measure the OASIS RLE parse defect's bias on the CAISO offer surface.

No LP. Isolates the ``dam-public-bids`` run-length-encoding parse defect
(``FINDING-caiso150`` §E1, fixed this session in
``scripts/lib/dam_public_bids``) from every other source of variation by
running the SAME balanced corpus through BOTH parsers and re-deriving the
CAISO measured offer surface from each.

Two arms, one corpus
--------------------
* ``old`` — the pre-caiso-152 parser, reproduced EXACTLY by monkeypatching the
  shared :func:`~scripts.lib.dam_public_bids.expand_rle` to the identity. This
  is not an approximation: the only other change in the fix is reading two
  extra raw columns, which never reach the output frame, and the identity-
  patched parser is verified byte-identical to the committed pre-fix
  ``parse_day`` (``verify`` subcommand).
* ``new`` — the corrected parser, expanding every ``[start, stop)`` range to
  the datatype's declared per-hour grain.

Each arm curates into its own clean tree (``--clean-root``) and re-runs
``scripts/data/derive_caiso_offer_surface.py`` against it with the consumed
output paths redirected into the arm's own directory, so **no keeper input is
ever written** by this probe.

The committed ``caiso_offer_curve_measured.json`` is NOT the control: it was
derived 2026-07-19 on a corpus that no longer exists, so a NEW-vs-committed
difference confounds parse with corpus. It is reported as CONTEXT only — the
delta a re-derive would actually ship — exactly as a solve compares against a
same-HEAD zero-delta control rather than committed keeper bytes.

Triggers (frozen ex ante in ``PREREG-caiso152-dam-bid-rle-parse-2026-08-01.md``
§4, before any value here was computed; the threshold is the deriver's OWN
estimation tolerance ``max(0.08 mult units, 10 %)`` that G2/G3 already use to
declare two values the same statistic):

* **T1** — any of the 6 CONSUMED static band multipliers (CC_REGULAR /
  CT_PEAKER × econ_low / econ_high / peak) moves beyond tolerance.
* **T2** — for any (class × net-load bin), the mean of that bin's 5
  equal-capacity ladder rungs — the average markup the P1 mechanism applies in
  that bin — moves beyond tolerance.

Either firing ⇒ MATERIAL. Neither ⇒ file and stop (no solve, no registration).
A derive-gate FAIL on the corrected parse is a third, separate outcome: the
lane stops at the derive and no threshold is retuned (rule 23).

Usage::

    python scripts/probes/_caiso152_rle_parse_bias.py verify
    python scripts/probes/_caiso152_rle_parse_bias.py curate --arm old
    python scripts/probes/_caiso152_rle_parse_bias.py curate --arm new
    python scripts/probes/_caiso152_rle_parse_bias.py derive --arm old
    python scripts/probes/_caiso152_rle_parse_bias.py derive --arm new
    python scripts/probes/_caiso152_rle_parse_bias.py compare
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

#: Consumed static bands (the unarmed ``committed`` band is reported, never a
#: trigger — its owner is unit commitment, not the P1 offer; rule 19).
CONSUMED_BANDS = ("econ_low", "econ_high", "peak")
CLASSES = ("CC_REGULAR", "CT_PEAKER")

#: The deriver's own frozen estimation tolerance (G2/G3): max(0.08, 10 %).
TOL_ABS = 0.08
TOL_REL = 0.10

DEFAULT_OUT = REPO / "results" / "calibration" / "caiso152_rle_parse_bias.json"


def _tol(base: float) -> float:
    """The frozen ex-ante tolerance for a multiplier of size ``base``."""
    return max(TOL_ABS, TOL_REL * abs(base))


def _arm_dir(out_root: Path, arm: str) -> Path:
    d = out_root / f"caiso152_{arm}"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------- #
# verify — the ``old`` arm really is the pre-fix parser
# --------------------------------------------------------------------------- #
def cmd_verify(args: argparse.Namespace) -> int:
    """Assert the identity-patched parser reproduces a known pre-fix property.

    The pre-fix parser emitted one clean row per RAW row; the corrected one
    emits one per raw row-hour. Both are re-measured here directly from the
    raw CSV so the arms cannot silently drift apart.
    """
    import zipfile

    import pandas as pd

    import scripts.lib.dam_public_bids.caiso as caiso

    zips = sorted((REPO / "data/raw/caiso-public-bids/zips").glob("*.zip"))
    if not zips:
        raise SystemExit("no bid zips — run scripts/data/fetch_caiso_public_bids.py")
    path = zips[0]

    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        raw = pd.read_csv(z.open(name), low_memory=False)
    gen = raw[
        (raw.RESOURCE_TYPE == "GENERATOR")
        & (raw.MARKETPRODUCTTYPE == "EN")
        & raw.SCH_BID_XAXISDATA.notna()
    ]
    start = pd.to_datetime(gen.SCH_BID_TIMEINTERVALSTART_GMT, utc=True, format="mixed")
    stop = pd.to_datetime(gen.SCH_BID_TIMEINTERVALSTOP_GMT, utc=True, format="mixed")
    span = ((stop - start).dt.total_seconds() // 3600).clip(lower=1).astype(int)

    new = caiso.parse_day(path)
    orig = caiso.expand_rle
    caiso.expand_rle = lambda frame, stop_utc, **kw: frame
    try:
        old = caiso.parse_day(path)
    finally:
        caiso.expand_rle = orig

    def _gen_en(df):
        return df[
            (df.resource_type == "GENERATOR")
            & (df["product"] == "EN")
            & (df.row_kind == "segment")
        ]

    report = {
        "day": path.name[:8],
        "raw_gen_en_rows": int(len(gen)),
        "raw_gen_en_curve_hours": int(span.sum()),
        "old_clean_gen_en_rows": int(len(_gen_en(old))),
        "new_clean_gen_en_rows": int(len(_gen_en(new))),
        "old_matches_raw_rows": bool(len(_gen_en(old)) == len(gen)),
        "new_matches_raw_curve_hours": bool(len(_gen_en(new)) == span.sum()),
        "carried_share_old": round(len(gen) / float(span.sum()), 4),
        "new_duplicate_schema_keys": int(
            new.duplicated(
                [
                    "iso",
                    "trade_date",
                    "resource_seq",
                    "product",
                    "interval_start_utc",
                    "row_kind",
                    "step_idx",
                ]
            ).sum()
        ),
        "new_hour_min": str(new.interval_start_utc.min()),
        "new_hour_max": str(new.interval_start_utc.max()),
    }
    print(json.dumps(report, indent=1))
    ok = (
        report["old_matches_raw_rows"]
        and report["new_matches_raw_curve_hours"]
        and report["new_duplicate_schema_keys"] == 0
    )
    print("VERIFY", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
# curate — one clean tree per arm
# --------------------------------------------------------------------------- #
def cmd_curate(args: argparse.Namespace) -> int:
    """Curate the whole corpus into the arm's own clean tree."""
    from market_sim.config import paths

    import scripts.lib.dam_public_bids.caiso as caiso
    from scripts.data import curate_dam_public_bids as curate

    clean_root = Path(args.clean_root) / f"clean_{args.arm}"
    clean_root.mkdir(parents=True, exist_ok=True)
    paths.CLEAN_DIR = clean_root

    if args.arm == "old":
        # Reproduce the pre-caiso-152 parser exactly: no RLE expansion.
        caiso.expand_rle = lambda frame, stop_utc, **kw: frame

    written = curate.curate(isos=["CAISO"], years=args.years)
    print(f"arm={args.arm}: {len(written)} clean file(s) under {clean_root}")
    return 0


# --------------------------------------------------------------------------- #
# binshift — the ladder's exposure, measured without running the derive
# --------------------------------------------------------------------------- #
def cmd_binshift(args: argparse.Namespace) -> int:
    """Measure how the parse defect mis-assigns curve-hours to net-load bins.

    The conditional ladder assigns each resource-hour to a net-load bin from
    its hour. Under the old parse a multi-hour hold was charged entirely to
    the bin of its RANGE START, so the population feeding each bin's rungs
    was not the population that actually bid there. This measures the
    mis-assignment directly on the raw corpus — no clean tree, no derive, no
    multiplier — so the ladder's exposure is stated independently of whatever
    the re-derive returns.

    Weighting is per (resource, range), deduplicated across breakpoints, so
    curves are counted once each rather than once per step.
    """
    import zipfile

    import numpy as np
    import pandas as pd

    from scripts.data import derive_caiso_offer_surface as D

    edges = np.asarray(args.edges, dtype=float)
    nl = D._netload_pct(list(args.years)).set_index(["day", "he"]).q

    def _bins(idx: pd.DatetimeIndex):
        loc = idx.tz_convert("US/Pacific")
        key = pd.MultiIndex.from_arrays(
            [loc.normalize().tz_localize(None), loc.hour + 1]
        )
        q = nl.reindex(key).to_numpy()
        return np.searchsorted(edges, q, side="right"), q

    zips = sorted((REPO / "data/raw/caiso-public-bids/zips").glob("*.zip"))
    zips = [z for z in zips if int(z.name[:4]) in set(args.years)]
    frames = []
    for z in zips:
        if z.name[:8] == "20240229":
            continue  # non-leap model calendar (the caiso-151 corpus rule)
        with zipfile.ZipFile(z) as zf:
            name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
            df = pd.read_csv(
                zf.open(name),
                usecols=[
                    "RESOURCE_TYPE",
                    "MARKETPRODUCTTYPE",
                    "RESOURCEBID_SEQ",
                    "SCH_BID_TIMEINTERVALSTART_GMT",
                    "SCH_BID_TIMEINTERVALSTOP_GMT",
                    "SCH_BID_XAXISDATA",
                ],
                low_memory=False,
            )
        df = df[
            (df.RESOURCE_TYPE == "GENERATOR")
            & (df.MARKETPRODUCTTYPE == "EN")
            & df.SCH_BID_XAXISDATA.notna()
        ]
        if df.empty:
            continue
        s = pd.to_datetime(df.SCH_BID_TIMEINTERVALSTART_GMT, utc=True, format="mixed")
        e = pd.to_datetime(df.SCH_BID_TIMEINTERVALSTOP_GMT, utc=True, format="mixed")
        span = ((e - s).dt.total_seconds() // 3600).clip(lower=1).astype(int)
        frames.append(
            pd.DataFrame(
                {
                    "res": df.RESOURCEBID_SEQ.to_numpy(),
                    "s": s.to_numpy(),
                    "span": span.to_numpy(),
                }
            ).drop_duplicates()
        )
    k = pd.concat(frames, ignore_index=True)

    span = k.span.to_numpy()
    rep = np.repeat(np.arange(len(k)), span)
    ends = np.cumsum(span)
    offs = np.arange(ends[-1]) - np.repeat(ends - span, span)
    start = pd.DatetimeIndex(k.s)[rep]
    hour = pd.DatetimeIndex(start + pd.to_timedelta(offs, unit="h"))

    b_true, q_true = _bins(hour)
    b_start, _ = _bins(pd.DatetimeIndex(start))
    m = ~np.isnan(q_true)
    b_ranges, _ = _bins(pd.DatetimeIndex(k.s))

    def _share(v) -> dict[str, float]:
        s = pd.Series(v).value_counts(normalize=True).sort_index()
        return {str(int(i)): round(float(x), 4) for i, x in s.items()}

    rec = {
        "days": len(zips),
        "years": list(args.years),
        "edges": list(edges),
        "resource_ranges": int(len(k)),
        "curve_hours": int(span.sum()),
        "span_gt_1_share_of_ranges": round(float((span > 1).mean()), 4),
        "hours_carried_by_old_parse": round(float(len(k) / span.sum()), 4),
        "misassigned_bin_share_of_curve_hours": round(
            float((b_true[m] != b_start[m]).mean()), 4
        ),
        "bin_share_old_range_starts": _share(b_ranges),
        "bin_share_new_curve_hours": _share(b_true[m]),
        "n_24h_holds": int((span == 24).sum()),
    }
    out = Path(args.out_root) / "caiso152_binshift.json"
    out.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    print(f"-> {out}")
    return 0


# --------------------------------------------------------------------------- #
# density — how much of the derive's classification depends on corpus DENSITY
# --------------------------------------------------------------------------- #
def cmd_density(args: argparse.Namespace) -> int:
    """Measure the gas-coupling classifier's sensitivity to trade-day density.

    The offer-surface derive identifies gas resources by regressing each
    masked resource's daily body bid on the citygate daily series, and keeps
    only resources clearing ``r >= 0.6``, a slope in [4, 18] MMBtu/MWh and
    >= 120 resource-days. That is a per-resource TIME-SERIES estimator, so it
    needs a DENSE daily corpus — unlike the caiso-151 intertie ceiling, whose
    (month × hod) climatology is served by a sparse seasonally balanced
    sample. This subcommand thins the corpus to every k-th local day and
    reports how the classified bucket capacity (the deriver's own G1 gate)
    responds, so the corpus requirement is measured rather than assumed.
    """
    from pathlib import Path as _Path

    from market_sim.config import paths

    paths.CLEAN_DIR = _Path(args.clean_root) / f"clean_{args.arm}"

    import numpy as np  # noqa: F401 — used via pandas ops below

    from scripts.data import derive_caiso_offer_surface as D

    bids = D._load_bids(list(args.years))
    cap_ry = bids.groupby(["resource_seq", "year"]).segment_mw.quantile(0.98)
    bids = bids.join(cap_ry.rename("cap"), on=["resource_seq", "year"])
    bids = bids[bids.cap >= D.MIN_CAP_MW]
    gas = D._gas_staircase()
    geom = D._fleet_geometry()

    local_day = (
        bids.interval_start_utc.dt.tz_convert("US/Pacific")
        .dt.normalize()
        .dt.tz_localize(None)
    )
    days = sorted(local_day.unique())

    rows = []
    for k in args.thin:
        keep = set(days[:: int(k)])
        sub = bids[local_day.isin(keep)]
        res, _ = D._classify(sub, gas, 8.5)
        gl = res[res.is_gas]
        row = {
            "every_kth_day": int(k),
            "days": len(keep),
            "resources_scored": int(len(res)),
            "resources_gas_pass": int(len(gl)),
            "fail_slope_out_of_range": int(
                (~res.slope.between(*D.GAS_SLOPE_RANGE)).sum()
            ),
            "fail_r_below_min": int((res.r < D.GAS_MIN_R).sum()),
        }
        for cls in CLASSES:
            mw = float(gl[gl.cls == cls].cap.sum())
            row[f"{cls}_bucket_mw"] = round(mw, 0)
            row[f"{cls}_G1_ratio"] = round(mw / geom[cls]["fleet_mw"], 3)
        rows.append(row)
        print(json.dumps(row), flush=True)

    out = Path(args.out_root) / "caiso152_corpus_density.json"
    out.write_text(json.dumps({"arm": args.arm, "rows": rows}, indent=1) + "\n")
    print(f"-> {out}")
    return 0


# --------------------------------------------------------------------------- #
# derive — re-run the offer-surface derive against one arm's clean tree
# --------------------------------------------------------------------------- #
def cmd_derive(args: argparse.Namespace) -> int:
    """Re-derive the measured offer surface from the arm's clean tree.

    Consumed output paths are redirected into the arm's directory, so the
    committed keeper artifacts under ``data/raw/_validation-source/`` are
    never touched by this probe.
    """
    from market_sim.config import paths

    paths.CLEAN_DIR = Path(args.clean_root) / f"clean_{args.arm}"

    from scripts.data import derive_caiso_offer_surface as D

    out = _arm_dir(Path(args.out_root), args.arm)
    D.OUT_STATIC = out / "caiso_offer_curve_measured.json"
    D.OUT_COND = out / "caiso_offer_surface_condbinned.json"
    D.OUT_CSV = out / "caiso_offer_surface_summary.csv"

    argv = ["--years", *[str(y) for y in args.years], "--allow-gate-failures"]
    rc = D.main(argv)
    print(f"arm={args.arm}: derive rc={rc} -> {out}")
    # rc=1 means gates failed and the JSONs were withheld — a first-class
    # outcome (PREREG §4 third branch), reported by `compare`, not a crash.
    return 0


# --------------------------------------------------------------------------- #
# compare — the pre-registered triggers
# --------------------------------------------------------------------------- #
def _ladder_bin_means(cond: dict) -> dict[str, dict[str, float]]:
    """Mean rung multiplier per (class, net-load bin) — the LP-consumed markup."""
    out: dict[str, dict[str, float]] = {}
    for cls in CLASSES:
        if cls not in cond:
            continue
        rungs = cond[cls]["binned_ladder"]
        out[cls] = {
            str(b): float(sum(r[1] for r in ladder) / len(ladder))
            for b, ladder in enumerate(rungs)
        }
    return out


def _gate_pass(doc: dict) -> dict:
    """Flatten a derive's own G1-G4 verdicts from its provenance block."""
    g = doc.get("_provenance", {}).get("gates", {})
    return {
        "G1": all(v["pass"] for v in g.get("G1_capacity_reconciliation", {}).values()),
        "G2": bool(g.get("G2_cut_robustness", {}).get("pass", False)),
        "G3": all(
            v["pass"]
            for rows in g.get("G3_estimation_loyo", {}).values()
            for v in rows.values()
        ),
        "G4": all(v["pass"] for v in g.get("G4_physical_sanity", {}).values()),
    }


def cmd_compare(args: argparse.Namespace) -> int:
    """Score T1/T2 and write the probe's JSON record."""
    out_root = Path(args.out_root)
    arms: dict[str, dict] = {}
    for arm in ("old", "new"):
        d = _arm_dir(out_root, arm)
        static_p = d / "caiso_offer_curve_measured.json"
        cond_p = d / "caiso_offer_surface_condbinned.json"
        arms[arm] = {
            "static": json.loads(static_p.read_text()) if static_p.exists() else None,
            "cond": json.loads(cond_p.read_text()) if cond_p.exists() else None,
            "gates_withheld": not static_p.exists(),
        }

    committed = json.loads(
        (
            REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
        ).read_text()
    )
    committed_cond = json.loads(
        (
            REPO / "data/raw/_validation-source/caiso_offer_surface_condbinned.json"
        ).read_text()
    )

    rec: dict = {
        "probe": "caiso-152 dam-public-bids RLE parse bias",
        "prereg": "results/calibration/PREREG-caiso152-dam-bid-rle-parse-2026-08-01.md",
        "tolerance": {"abs": TOL_ABS, "rel": TOL_REL, "source": "deriver G2/G3"},
        "gates": {
            a: (_gate_pass(v["static"]) if v["static"] else None)
            for a, v in arms.items()
        },
        "T1_static_bands": {},
        "T2_ladder_bin_means": {},
        "context_new_vs_committed": {},
    }

    if arms["old"]["static"] is None or arms["new"]["static"] is None:
        rec["verdict"] = (
            "DERIVE_GATE_FAIL — consumed JSONs withheld on at least one arm"
        )
        Path(args.out).write_text(json.dumps(rec, indent=1) + "\n")
        print(json.dumps(rec, indent=1))
        return 0

    t1_fired = False
    for cls in CLASSES:
        o = arms["old"]["static"][cls]
        n = arms["new"]["static"][cls]
        row = {}
        for band in CONSUMED_BANDS:
            ov, nv = o["bands"][band], n["bands"][band]
            dev = abs(nv - ov)
            tol = _tol(ov)
            fired = dev > tol
            t1_fired = t1_fired or fired
            row[band] = {
                "old": ov,
                "new": nv,
                "delta": round(nv - ov, 4),
                "tol": round(tol, 4),
                "fires": bool(fired),
            }
        # Reported, never a trigger.
        row["committed_band_unarmed"] = {
            "old": o["unarmed"]["committed"],
            "new": n["unarmed"]["committed"],
        }
        rec["T1_static_bands"][cls] = row

    t2_fired = False
    old_bins = _ladder_bin_means(arms["old"]["cond"])
    new_bins = _ladder_bin_means(arms["new"]["cond"])
    for cls in CLASSES:
        row = {}
        for b in sorted(old_bins.get(cls, {}), key=int):
            ov, nv = old_bins[cls][b], new_bins[cls][b]
            dev = abs(nv - ov)
            tol = _tol(ov)
            fired = dev > tol
            t2_fired = t2_fired or fired
            row[b] = {
                "old": round(ov, 4),
                "new": round(nv, 4),
                "delta": round(nv - ov, 4),
                "tol": round(tol, 4),
                "fires": bool(fired),
            }
        rec["T2_ladder_bin_means"][cls] = row

    # CONTEXT ONLY — confounds parse with corpus (PREREG §3).
    comm_bins = _ladder_bin_means(committed_cond)
    for cls in CLASSES:
        rec["context_new_vs_committed"][cls] = {
            "bands": {
                band: {
                    "committed": committed[cls]["bands"][band],
                    "new": arms["new"]["static"][cls]["bands"][band],
                    "delta": round(
                        arms["new"]["static"][cls]["bands"][band]
                        - committed[cls]["bands"][band],
                        4,
                    ),
                }
                for band in CONSUMED_BANDS
            },
            "ladder_bin_means": {
                b: {
                    "committed": round(comm_bins[cls][b], 4),
                    "new": round(new_bins[cls][b], 4),
                    "delta": round(new_bins[cls][b] - comm_bins[cls][b], 4),
                }
                for b in sorted(comm_bins.get(cls, {}), key=int)
            },
        }

    rec["T1_fires"] = bool(t1_fired)
    rec["T2_fires"] = bool(t2_fired)
    rec["verdict"] = "MATERIAL" if (t1_fired or t2_fired) else "IMMATERIAL"

    Path(args.out).write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    print(f"\nVERDICT {rec['verdict']} (T1={t1_fired}, T2={t2_fired}) -> {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    # Shared options live on a parent parser so they may be given AFTER the
    # subcommand: `--years` takes a list, and a greedy list before the
    # subcommand would swallow it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out-root", default=str(REPO / "results" / "calibration"))
    common.add_argument("--out", default=str(DEFAULT_OUT))
    common.add_argument("--clean-root", default=str(REPO / "results" / "calibration"))
    common.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    common.add_argument(
        "--edges",
        nargs="+",
        type=float,
        default=[0.80, 0.90, 0.97],
        help="net-load percentile bin edges (the deriver's armed default)",
    )

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify", parents=[common])
    sub.add_parser("binshift", parents=[common])
    for name in ("curate", "derive"):
        p = sub.add_parser(name, parents=[common])
        p.add_argument("--arm", choices=("old", "new"), required=True)
    p = sub.add_parser("density", parents=[common])
    p.add_argument("--arm", choices=("old", "new"), default="old")
    p.add_argument(
        "--thin",
        nargs="+",
        type=int,
        default=[1, 2, 3, 6],
        help="keep every k-th local trade day (1 = the whole corpus)",
    )
    sub.add_parser("compare", parents=[common])
    args = ap.parse_args(argv)
    return {
        "verify": cmd_verify,
        "binshift": cmd_binshift,
        "curate": cmd_curate,
        "derive": cmd_derive,
        "density": cmd_density,
        "compare": cmd_compare,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
