"""Derive the PER-PLANT measured coal offer supply curves for an ISO (ERCOT-144).

The identification artifact of the ``coal_perplant_offer_level`` mechanism
(``constants.COAL_PERPLANT_OFFER_CURVE_BY_ISO``) — the DOF-retirement lane
ERCOT-143 §2 chartered: measured PER RESOURCE, every ERCOT coal plant submits
a near-flat 60-Day SCED ``Submitted TPO`` curve at a plant-specific level, so
the fleet's smooth supply curve is CROSS-PLANT LEVEL DISPERSION — an object
the residual-identified ``offer_curve_by_group`` COAL_* band multipliers and
the gas-keyed supply sigmoids were standing in for. This derive replaces that
fitted composition with each plant's own submitted curve.

Construction (zero fitted parameters, every step deterministic):

1. For each coal (CLLIG) resource in the four on-disk 60-Day SCED probe-day
   subsets (2024–2025; no 2023 disclosure exists — the 2023 application is a
   DECLARED EXTRAPOLATION, exactly as ERCOT-137/139/140 declared theirs), take
   the **modal** submitted TPO curve — the most-often-submitted (price-tuple)
   curve across all pooled subsets. Modal, not mean: the modal curve is a real
   submitted object (Oak Grove's repeats identically x1436 across subsets AND
   years — the time-stability evidence that licenses a LEVEL identification;
   ERCOT-143 §3 forbids any hourly/seasonal/diurnal identification off this
   corpus).
2. Map each resource to its EIA plant (the ERCOT-144 handoff crosswalk) and
   MERGE the plant's resources into one price-sorted step supply curve
   (jointly-owned units — Fayette J01/J02, Sandy Creek J01–J04 — are separate
   QSE resources with genuinely different curves; the merged curve is the
   plant's actual aggregate offer).
3. Emit the merged curve verbatim as ``(cumulative_MW, price)`` breakpoints.
   Points at or below the ~-$250 offer floor (San Miguel's 220 MW block) are
   KEPT in the curve but are excluded from level statistics by the consumer:
   they are a price-taker self-schedule signal, not a marginal cost
   (``constants.COAL_PERPLANT_SELF_SCHED_FLOOR``).

The consumer (``fleet.legacy_bins.apply_coal_tranches``) maps each CAMPD
committed/econ tranche's capacity window onto this curve and prices the
tranche at the window's capacity-weighted measured price — a LEVEL read at
the tranche (capacity) grain, never a time-shape.

Rule-23 frozen derive: re-run ONLY when the source disclosure subsets are
regenerated from new data, and cite that change in the re-derivation commit.
NEVER because a residual moved.

Reporting/derivation tool only — default-off in every solve path. The model
artifact it informs is the hand-set ``COAL_PERPLANT_OFFER_CURVE_BY_ISO``
entry in ``config/constants.py`` (cited back to this script), consumed by the
harness only under ``--coal-perplant-offer-level``.

Usage::

    python scripts/data/derive_coal_perplant_offer.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from scripts.probes.ercot123_coal_sced_reach import (  # noqa: E402
    SUBSETS,
    TPO_MW,
    TPO_PR,
    load_sced,
)

#: Resource-name prefix -> EIA plant code (the ERCOT-144 handoff crosswalk,
#: extending ercot143's LIGNITE_RES to all 10 model coal plants).
PREFIX_TO_PLANT: dict[str, int] = {
    "OGSES": 6180,  # Oak Grove SES
    "SANMIGL": 6183,  # San Miguel
    "TNP_ONE": 7030,  # Major Oak (TNP One / Twin Oaks)
    "MLSES": 6146,  # Martin Lake
    "LEG": 298,  # Limestone
    "WAP": 3470,  # W A Parish (coal units only; class filter is CLLIG)
    "COLETO": 6178,  # Coleto Creek
    "FPPYD": 6179,  # Fayette (FPP)
    "CALAVERS": 7097,  # Calaveras / J K Spruce
    "SCES": 56611,  # Sandy Creek
}
PLANT_NAMES = {
    298: "Limestone",
    3470: "W A Parish",
    6146: "Martin Lake",
    6178: "Coleto Creek",
    6179: "Fayette",
    6180: "Oak Grove",
    6183: "San Miguel",
    7030: "Major Oak",
    7097: "JK Spruce",
    56611: "Sandy Creek",
}


def _plant_of(resource: str) -> int | None:
    """Map a 60-Day disclosure Resource Name to its EIA plant code."""
    for pref, code in PREFIX_TO_PLANT.items():
        if resource.startswith(pref):
            return code
    return None


def modal_curve(g: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, int] | None:
    """The most-submitted TPO curve of one resource: (mw, price, count)."""
    P = g[TPO_PR].to_numpy(float)
    M = g[TPO_MW].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(M)
    keys = [
        tuple(np.round(np.sort(P[i][ok[i]]), 2)) for i in range(len(P)) if ok[i].any()
    ]
    if not keys:
        return None
    key, n = Counter(keys).most_common(1)[0]
    i = next(
        j
        for j in range(len(P))
        if ok[j].any() and tuple(np.round(np.sort(P[j][ok[j]]), 2)) == key
    )
    pr = P[i][ok[i]]
    mw = M[i][ok[i]]
    o = np.argsort(mw)
    return mw[o], pr[o], int(n)


def merge_plant_curve(
    unit_curves: list[tuple[np.ndarray, np.ndarray]],
) -> list[tuple[float, float]]:
    """Merge unit step curves into one price-sorted plant supply curve.

    Each unit curve is a step function: point k covers (mw[k-1], mw[k]] at
    price[k] (the first point covers 0..mw[0], and a first point at 0 MW is a
    zero-width marker carrying the curve's bottom price — kept as the price of
    the first nonzero segment). Segments from all units are pooled, sorted by
    price, and cumulated. Returns ``[(cum_mw, price), ...]``.
    """
    segs: list[tuple[float, float]] = []  # (width, price)
    for mw, pr in unit_curves:
        edges = np.concatenate([[0.0], mw])
        widths = np.diff(edges)
        for k in range(len(pr)):
            if widths[k] > 0:
                segs.append((float(widths[k]), float(pr[k])))
    segs.sort(key=lambda s: s[1])
    out: list[tuple[float, float]] = []
    cum = 0.0
    for w, p in segs:
        cum += w
        # coalesce equal-price neighbours
        if out and abs(out[-1][1] - p) < 1e-9:
            out[-1] = (round(cum, 1), p)
        else:
            out.append((round(cum, 1), round(p, 2)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    frames = []
    for tag, _year, _fam in SUBSETS:
        r = load_sced(tag)
        if r is not None:
            f = r[0][r[0].cls == "COAL"].copy()
            frames.append(f)
    if not frames:
        raise SystemExit("no SCED probe-day subset on disk")
    pooled = pd.concat(frames, ignore_index=True)
    pooled["plant_code"] = pooled["Resource Name"].map(_plant_of)

    registry: dict[int, list[tuple[float, float]]] = {}
    provenance: dict[int, list[dict]] = {}
    for code in sorted(PLANT_NAMES):
        g_pl = pooled[pooled.plant_code == code]
        curves = []
        prov = []
        for rn in sorted(g_pl["Resource Name"].unique()):
            mk = modal_curve(g_pl[g_pl["Resource Name"] == rn])
            if mk is None:
                continue
            mw, pr, n = mk
            curves.append((mw, pr))
            prov.append(
                {
                    "resource": rn,
                    "modal_count": n,
                    "points": [
                        [round(float(a), 1), round(float(b), 2)] for a, b in zip(mw, pr)
                    ],
                }
            )
        if not curves:
            raise SystemExit(f"plant {code} ({PLANT_NAMES[code]}) absent from corpus")
        registry[code] = merge_plant_curve(curves)
        provenance[code] = prov

    print("# COAL_PERPLANT_OFFER_CURVE_BY_ISO['ERCOT'] — paste into constants.py")
    print('    "ERCOT": {')
    for code, curve in registry.items():
        pts = ", ".join(f"({a:g}, {b:g})" for a, b in curve)
        print(f"        {code}: ({pts}),  # {PLANT_NAMES[code]}")
    print("    },")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(
                {
                    "lane": "ercot144-coal-perplant-offer",
                    "registry": {str(k): v for k, v in registry.items()},
                    "provenance": {str(k): v for k, v in provenance.items()},
                    "subsets": [t for t, _y, _f in SUBSETS],
                },
                indent=2,
            )
        )
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
