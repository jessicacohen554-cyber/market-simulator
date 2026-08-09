"""ULP-pair step-encoding of piecewise-constant rank ladders (ercot-180).

The single encoder behind the four ``--top-scoped`` derive modes and the
ercot-180 seam probe (PRECOMMIT-ercot180-top-scoped-grain-2026-08-08.md §3):
a piecewise-constant function on the within-year net-load RANK axis —
``len(edges) + 1`` bins, bin ``j`` = ``(edges[j-1], edges[j]]`` with the
open-ended first and last bins — becomes a node table consumed by the merged
form-(a) interpolation machinery (``offer_surfaces._contpct_curve`` /
``_interp_rows``), with NO representable query point inside any transition:

* at each edge ``e`` the node pair is ``(e, v_below)`` and
  ``(np.nextafter(e, 1.0), v_above)`` — no double exists strictly between
  them, so every query lands on an exactly-flat segment or an exact node;
* a query at exactly ``e`` reads ``v_below``, matching the solve-side stepped
  control's value-space assignment of an exact-rank-boundary hour to the
  LOWER bin (PRECOMMIT-ercot180 §5 SP-3'; ties are the disclosed residual
  risk the seam proof adjudicates on real inputs);
* ``np.interp`` end-clamps flat below the first edge (bin 0's value) and
  above the terminal node at 1.0 (the top bin's value).

Zero parameters; pure geometry. [R-DOF]
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

#: The topscoped vintage's provenance tag — must match
#: ``offer_surfaces._TOPSCOPED_TAG`` (the vintage guard reads the artifact's
#: ``_provenance.conditioning`` against the armed gate).
TOPSCOPED_TAG = "topscoped-netload-bins"

#: The committed edge-identification record (PRECOMMIT-ercot180 §2's probe
#: output) — the ONLY admissible source of the new above-p97 edges.
EDGE_ID_JSON = (
    Path(__file__).resolve().parents[2]
    / "results"
    / "calibration"
    / "ercot180_edge_identification.json"
)


def load_identified_edges(path: "Path | None" = None) -> list[float]:
    """The conduct-identified above-p97 edges from the committed probe record.

    Raises when the record is absent or carries no accepted edges — the
    precommit's EXHAUSTED-AT-IDENTIFICATION outcome, under which no derive
    (and no solve) is licensed.
    """
    p = Path(path) if path else EDGE_ID_JSON
    rec = json.loads(p.read_text())
    edges = [float(e) for e in rec.get("accepted_edges", ())]
    if not edges:
        raise ValueError(
            f"{p.name}: no accepted edges — the form-(b) lever is "
            "EXHAUSTED-AT-IDENTIFICATION (PRECOMMIT-ercot180 §2); no "
            "topscoped derive is licensed"
        )
    return edges


def rows_from_pairs(ladder_bins: list) -> list[list[float]]:
    """``[[q, mult], ...]`` pair-ladders per bin -> plain per-bin value rows."""
    return [[float(pt[1]) for pt in lad_b] for lad_b in ladder_bins]


def encode_step_nodes(
    edges: "list[float] | tuple[float, ...]",
    bin_rows: "list[list[float]]",
) -> tuple[list[float], list[list[float]]]:
    """Encode ``len(edges)+1`` per-bin value rows as an ULP-pair node table.

    ``bin_rows[j]`` is bin ``j``'s value row (a list of floats — a ladder, or
    a single-element list for a scalar series such as ``cleared_share`` /
    ``pool_frac``). Every value must be finite: a non-finite encoded bin would
    silently change level vs the stepped control (NaN has no stepped-path
    meaning at the contpct seam), so it raises instead.

    Returns ``(pct_nodes, value_rows)`` with ``pct_nodes`` strictly
    increasing, ``2 * len(edges) + 1`` nodes.
    """
    edges = [float(e) for e in edges]
    if sorted(edges) != edges or len(set(edges)) != len(edges):
        raise ValueError(f"edges must be strictly increasing, got {edges}")
    if len(bin_rows) != len(edges) + 1:
        raise ValueError(
            f"need {len(edges) + 1} bin rows for {len(edges)} edges, "
            f"got {len(bin_rows)}"
        )
    rows = [[float(v) for v in row] for row in bin_rows]
    width = {len(r) for r in rows}
    if len(width) != 1:
        raise ValueError(f"bin rows have mixed widths {sorted(width)}")
    for j, row in enumerate(rows):
        if not all(np.isfinite(v) for v in row):
            raise ValueError(
                f"bin {j} carries a non-finite value {row} — a NaN bin cannot "
                "be step-encoded without changing level (PRECOMMIT-ercot180 "
                "§1 zero-support rule: inherit the parent bin instead)"
            )
    xs: list[float] = []
    ys: list[list[float]] = []
    for j, e in enumerate(edges):
        if not (0.0 < e < 1.0):
            raise ValueError(f"edge {e} outside (0, 1)")
        xs.append(e)
        ys.append(rows[j])
        xs.append(float(np.nextafter(e, 1.0)))
        ys.append(rows[j + 1])
    xs.append(1.0)
    ys.append(rows[-1])
    if any(b <= a for a, b in zip(xs, xs[1:])):
        raise ValueError(f"node x-grid not strictly increasing: {xs}")
    return xs, ys


def split_top_bin(
    legacy_edges: "list[float] | tuple[float, ...]",
    legacy_rows: "list[list[float]]",
    new_edges: "list[float] | tuple[float, ...]",
    top_sub_rows: "list[list[float] | None]",
) -> tuple[list[float], list[list[float]]]:
    """Compose the top-scoped bin geometry: frozen below p97, sub-bins above.

    ``legacy_edges``/``legacy_rows`` are the FROZEN stepped artifact's own
    edges and per-bin rows (byte-copied by the caller — the last legacy edge
    is the p97 family top edge, ``legacy_rows[-1]`` the former top bin).
    ``new_edges`` are the conduct-identified edges strictly above the last
    legacy edge; ``top_sub_rows[k]`` is sub-bin ``k``'s computed row, or
    ``None`` for a zero-support sub-bin, which INHERITS the frozen parent
    top-bin row (PRECOMMIT-ercot180 §1: behaves byte-identically to today —
    never NaN, never a cross-year borrow, never an interpolation).

    Returns ``(edges, rows)`` ready for :func:`encode_step_nodes`.
    """
    legacy_edges = [float(e) for e in legacy_edges]
    new_edges = [float(e) for e in new_edges]
    if len(legacy_rows) != len(legacy_edges) + 1:
        raise ValueError(
            f"{len(legacy_edges)} legacy edges need {len(legacy_edges) + 1} "
            f"rows, got {len(legacy_rows)}"
        )
    top = legacy_edges[-1]
    if any(e <= top for e in new_edges):
        raise ValueError(f"new edges {new_edges} must sit above {top}")
    if len(top_sub_rows) != len(new_edges) + 1:
        raise ValueError(
            f"{len(new_edges)} new edges need {len(new_edges) + 1} sub-bin "
            f"rows, got {len(top_sub_rows)}"
        )
    parent = legacy_rows[-1]
    rows = list(legacy_rows[:-1]) + [
        list(parent) if sub is None else list(sub) for sub in top_sub_rows
    ]
    return legacy_edges + new_edges, rows
