"""caiso-182 P0-2 — prove the streaming curation path is byte-equivalent.

The incumbent ``curate_dam_public_bids._curate_spec`` holds every day-frame and
``pd.concat``s them, then ``write_clean`` makes a full ``pa.Table.from_pandas``
copy on top — which is why caiso-178 measured a full CAISO year at ~14.3 GB
against a ~15 GB ceiling (README ``data/raw/caiso-public-bids``). This probe
checks that the streaming replacement (``clean_io.write_clean_iter``) writes the
*same data* over a bounded span, so the fix can be used as a pure-engineering
substitution with zero model semantics.

Three legs, all reported:

* **BE-A content** — the frame read back from the streaming file equals the
  frame read back from the concat file, exactly (``DataFrame.equals`` plus an
  explicit dtype and row-order check).
* **BE-B layout** — identical row-group count and per-row-group row counts.
* **BE-C data bytes** — identical sha256 over the parquet file with the two
  metadata fields that are timestamps/commit stamps by construction
  (``created_utc``, ``git_commit``) normalised out. Byte-identity of the raw
  file is impossible by construction because ``_build_metadata`` stamps
  ``created_utc`` at write time; BE-C is the strongest identity actually
  available, and it is checked rather than assumed.

Usage:
    python scripts/probes/_caiso182_curate_stream_be.py [--days 40]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

OUT = REPO / "results/calibration/_caiso182_curate_stream_be.json"

#: Metadata keys that are stamped at write time and therefore can never match
#: between two runs of the same writer, let alone two writers.
_VOLATILE_META = (b"market_sim.created_utc", b"market_sim.git_commit")


def _normalised_sha(path: Path) -> str:
    """sha256 of the parquet file's data with volatile metadata neutralised.

    Rewrites the table with the volatile provenance keys blanked (values, not
    keys, so the schema shape is untouched) into a temp file and hashes that.
    Both sides go through the identical rewrite, so any difference the hash
    reports is a difference in the data or the layout, never in the stamp.
    """
    table = pq.read_table(path)
    md = dict(table.schema.metadata or {})
    for key in _VOLATILE_META:
        if key in md:
            md[key] = b""
    table = table.replace_schema_metadata(md)
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as fh:
        tmp = Path(fh.name)
    try:
        pq.write_table(table, tmp)
        return hashlib.sha256(tmp.read_bytes()).hexdigest()
    finally:
        tmp.unlink(missing_ok=True)


def _row_group_layout(path: Path) -> list[int]:
    md = pq.read_metadata(str(path))
    return [md.row_group(i).num_rows for i in range(md.num_row_groups)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=40)
    ap.add_argument("--row-group-rows", type=int, default=1024 * 1024)
    args = ap.parse_args(argv)

    # CLEAN_DIR is redirected to a scratch tree so the probe never touches the
    # real data/clean contract (the data-intake skill's tmp-CLEAN_DIR rule).
    scratch = Path(tempfile.mkdtemp(prefix="caiso182_be_"))
    os.environ["MARKET_SIM_CLEAN_DIR"] = str(scratch)

    from scripts.lib import clean_io
    from scripts.lib.dam_public_bids import DATATYPE, load_specs
    from market_sim.config import paths

    paths.CLEAN_DIR = scratch  # type: ignore[misc]
    clean_io.paths.CLEAN_DIR = scratch  # type: ignore[misc]

    spec = load_specs(["CAISO"])[0]
    files = sorted(spec.raw_dir.glob(spec.file_glob))[: args.days]
    if not files:
        print("no raw day files present — cannot run", file=sys.stderr)
        return 2
    print(f"span: {len(files)} day files, {files[0].name} .. {files[-1].name}")

    src = f"caiso-182 BE probe ({len(files)} daily files)"

    # Both legs write the SAME partition keys (iso/year/market) — otherwise the
    # embedded `market_sim.year` differs and BE-C would fail on a probe
    # artifact rather than on the writer. They are kept apart by redirecting
    # CLEAN_DIR between the two writes instead.
    def _redirect(sub: str) -> None:
        d = scratch / sub
        d.mkdir(parents=True, exist_ok=True)
        paths.CLEAN_DIR = d  # type: ignore[misc]
        clean_io.paths.CLEAN_DIR = d  # type: ignore[misc]

    # --- leg 1: the INCUMBENT path (parse-all, concat, write_clean) ----------
    _redirect("concat")
    t0 = time.time()
    frames = [spec.parse_day(f) for f in files]
    df_concat = pd.concat(frames, ignore_index=True)
    n_rows = len(df_concat)
    concat_path = clean_io.write_clean(
        df_concat, DATATYPE, iso="CAISO", year=2023, market="DAM", source=src
    )
    concat_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
    concat_s = time.time() - t0
    del frames, df_concat

    # --- leg 2: the STREAMING path (write_clean_iter, day at a time) --------
    _redirect("stream")
    t1 = time.time()
    stream_path = clean_io.write_clean_iter(
        (spec.parse_day(f) for f in files),
        DATATYPE,
        iso="CAISO",
        year=2023,
        market="DAM",
        source=src,
        row_group_rows=args.row_group_rows,
    )
    stream_s = time.time() - t1

    # --- BE-A content -------------------------------------------------------
    a = pq.read_table(concat_path).to_pandas()
    b = pq.read_table(stream_path).to_pandas()
    be_a_shape = a.shape == b.shape
    be_a_cols = list(a.columns) == list(b.columns)
    be_a_dtypes = [str(t) for t in a.dtypes] == [str(t) for t in b.dtypes]
    be_a_equals = bool(a.equals(b))
    be_a = be_a_shape and be_a_cols and be_a_dtypes and be_a_equals

    # --- BE-B layout --------------------------------------------------------
    lay_a, lay_b = _row_group_layout(concat_path), _row_group_layout(stream_path)
    be_b = lay_a == lay_b

    # --- BE-C data bytes ----------------------------------------------------
    sha_a, sha_b = _normalised_sha(concat_path), _normalised_sha(stream_path)
    be_c = sha_a == sha_b

    rec = {
        "span_days": len(files),
        "first_file": files[0].name,
        "last_file": files[-1].name,
        "rows": int(n_rows),
        "row_group_rows": args.row_group_rows,
        "BE_A_content": {
            "pass": be_a,
            "shape": be_a_shape,
            "columns": be_a_cols,
            "dtypes": be_a_dtypes,
            "frame_equals": be_a_equals,
        },
        "BE_B_layout": {"pass": be_b, "concat": lay_a, "stream": lay_b},
        "BE_C_data_bytes": {"pass": be_c, "concat_sha256": sha_a, "stream_sha256": sha_b},
        "timing_s": {"concat": round(concat_s, 1), "stream": round(stream_s, 1)},
        "concat_peak_rss_gb": round(concat_peak, 3),
        "note": (
            "Raw-file byte identity is impossible by construction: "
            "_build_metadata stamps created_utc (and git_commit) at write time. "
            "BE-C normalises exactly those two values on BOTH sides and is the "
            "strongest identity available."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    print()
    verdict = "PASS" if (be_a and be_b and be_c) else "FAIL"
    print(f"BE-A content {be_a} | BE-B layout {be_b} | BE-C data bytes {be_c} -> {verdict}")
    return 0 if (be_a and be_b and be_c) else 1


if __name__ == "__main__":
    sys.exit(main())
