"""Reassemble a gzip+base64, chunked raw-data file back to its original bytes.

Some 2026-07-10 rule-22 holdout-intake raw files (ERCOT/PJM/CAISO/MISO/NYISO
zone-specific-demand, 2018-2022 + H1-2026 years) were committed as
``<name>.gz.b64.partNNN`` chunks instead of the plain file. This is a
transport workaround, not a data change: the session's GitHub write path
(the ``push_files``/``create_or_update_file`` MCP tools) only carries UTF-8
text in a single tool-call argument, with an empirically small per-call
ceiling (roughly 100 KB) -- far below the multi-MB size of a raw annual
load file, and it cannot carry binary content (e.g. ``.xlsx``/``.zip``) at
all. gzip+base64, split into ~90 KB text chunks, is the smallest lossless
encoding that fits through that ceiling.

Usage
-----
    python scripts/data/reassemble_chunked_raw.py data/raw/zone-specific-demand/PJM_2018_hrl_load_metered.csv

Pass the target *plain* filename (no ``.gz.b64.partNNN`` suffix); the script
finds the matching ``<target>.gz.b64.part*`` siblings, concatenates them in
part order, base64-decodes, gunzips, and writes ``<target>``. Verifies the
part sequence is contiguous (no gaps) before decoding.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import sys
from pathlib import Path


def reassemble(target: Path) -> Path:
    """Rebuild ``target`` from its ``<target>.gz.b64.partNNN`` chunk siblings."""
    parts = sorted(target.parent.glob(f"{target.name}.gz.b64.part*"))
    if not parts:
        sys.exit(
            f"no chunks found for {target} (expected {target.name}.gz.b64.partNNN)"
        )

    expected = {f"{target.name}.gz.b64.part{i + 1:03d}" for i in range(len(parts))}
    found = {p.name for p in parts}
    if found != expected:
        missing = expected - found
        sys.exit(f"chunk sequence has gaps, missing: {sorted(missing)}")

    b64_text = "".join(p.read_text() for p in parts)
    raw = gzip.decompress(base64.b64decode(b64_text))
    target.write_bytes(raw)
    print(f"{target}: reassembled {len(parts)} chunks -> {len(raw):,} bytes")
    return target


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "target",
        type=Path,
        help="plain output filename (chunks are <target>.gz.b64.partNNN)",
    )
    args = ap.parse_args()
    reassemble(args.target)


if __name__ == "__main__":
    main()
