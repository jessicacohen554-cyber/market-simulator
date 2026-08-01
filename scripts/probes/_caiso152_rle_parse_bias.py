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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-root", default=str(REPO / "results" / "calibration"))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--clean-root", default=str(REPO / "results" / "calibration"))
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    for name in ("curate", "derive"):
        p = sub.add_parser(name)
        p.add_argument("--arm", choices=("old", "new"), required=True)
    sub.add_parser("compare")
    args = ap.parse_args(argv)
    return {
        "verify": cmd_verify,
        "curate": cmd_curate,
        "derive": cmd_derive,
        "compare": cmd_compare,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
