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

**Per-year mode (ercot-168, matrix §5.1 item 12 — rule-23 re-derivation
trigger: the ercot-157 delivery-2023 corpus landing dissolved the "no 2023
SCED exists" extrapolation premise).** ``--year 2023`` reads the full-year
NP3-965 corpus (``data/raw/ercot/SCED/``, publication-month-keyed shards,
delivery = filename − 2) under the SAME row filters and emits the
year-resolved registry ``COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO`` — the
same modal construction at the corpus's own submission grain: the effective
curve of (resource, month, hour) is the hour's modal price-tuple curve iff
that key repeats on a strict majority (>0.5) of the month's live days at
that hour, else the month's pooled modal curve (the ercot-144
modal/time-stability license at day grain; every admitted hour cell is
recorded with its day-share in the provenance JSON). Timestamps are
converted CPT -> fixed CST at derivation so emitted hour windows sit on the
model's clock (the ercot-166 DST-defect class, closed at the source).
Construction and convention-boundary disclosure:
``docs/PRECOMMIT-ercot168-coal-perplant-year-curves-2026-08-05.md`` §0/§1e.

Reporting/derivation tool only — default-off in every solve path. The model
artifact it informs is the hand-set ``COAL_PERPLANT_OFFER_CURVE_BY_ISO``
entry in ``config/constants.py`` (cited back to this script), consumed by the
harness only under ``--coal-perplant-offer-level`` — plus, in per-year mode,
``COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO`` consumed under
``--coal-perplant-offer-yearly``.

Usage::

    python scripts/data/derive_coal_perplant_offer.py [--json-out PATH]
    python scripts/data/derive_coal_perplant_offer.py --year 2023 \
        [--json-out PATH]
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


#: THE RTC+B BOUNDARY — this lane stops at delivery 2025-12-04. The
#: ``glob("*.parquet")`` in :func:`load_corpus_coal` is NON-RECURSIVE on
#: purpose: the RTC+B-format parts (deliveries 2025-12-05..31) sit in the
#: ``rtcb-format-2026/`` subdirectory because RTC+B REMOVES ``HASL``, a required
#: entry of :data:`_CORPUS_COLS`, and drops the trailing space from
#: ``Telemetered Net Output ``. Never make that glob recursive — RTC+B
#: deliveries are calendar-2025, so the delivery-year filter would keep them.
#: They are readable only through ``scripts.lib.sced_rtcb_adapter`` (owner card
#: D / signature D1, ``docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md``).
SCED_CORPUS_DIR = REPO / "data" / "raw" / "ercot" / "SCED"

#: Columns the per-year mode reads from each corpus shard (the ercot-123
#: load_sced filter set: ONLINE status, HSL>0, HSL>LSL, HASL & net-output
#: non-null — replicated on the raw 187-column all-string schema).
_CORPUS_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
    "HASL",
    "LSL",
    "Telemetered Net Output ",
]


def load_corpus_coal(year: int) -> pd.DataFrame:
    """Delivery-``year`` CLLIG rows from the NP3-965 corpus, filter-matched.

    Applies the SAME row filters as :func:`ercot123_coal_sced_reach.load_sced`
    (ONLINE telemetered status, numeric coercion, ``HSL > 0``, ``HSL > LSL``,
    HASL and net-output non-null) plus the delivery-year filter that drops the
    publication-window bleed (2022-12-31 / early-Jan rows in edge shards).
    Timestamps convert CPT (prevailing, the disclosure clock) -> fixed CST
    (the model clock): fall-back ambiguity resolves to standard time, the
    spring-forward hole shifts forward — a dozen 5-minute rows per resource
    at stake, disclosed here rather than silently mixed.
    """
    from market_sim.config import paths  # noqa: F401  (repo-root resolution)

    import pyarrow.dataset as pads

    from scripts.probes.ercot123_coal_sced_reach import ONLINE

    files = sorted(SCED_CORPUS_DIR.glob("*.parquet"))
    if not files:
        raise SystemExit(f"no NP3-965 corpus shards under {SCED_CORPUS_DIR}")
    cols = _CORPUS_COLS + TPO_MW + TPO_PR
    frames = []
    for f in files:
        t = pads.dataset(f).to_table(
            columns=cols, filter=pads.field("Resource Type") == "CLLIG"
        )
        if t.num_rows:
            frames.append(t.to_pandas())
    df = pd.concat(frames, ignore_index=True)
    df = df[df["Telemetered Resource Status"].astype(str).str.strip().isin(ONLINE)]
    for c in ["HSL", "HASL", "LSL", "Telemetered Net Output "] + TPO_MW + TPO_PR:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    loc = ts.dt.tz_localize(
        "America/Chicago", ambiguous=False, nonexistent="shift_forward"
    )
    df["ts"] = loc.dt.tz_convert("Etc/GMT+6").dt.tz_localize(None)
    df = df[(df["HSL"] > 0) & (df["HSL"] > df["LSL"])]
    df = df[df["HASL"].notna() & df["Telemetered Net Output "].notna()]
    df = df[df["ts"].dt.year == year]
    if df.empty:
        raise SystemExit(f"no delivery-{year} CLLIG rows survived the filters")
    df["month"] = df["ts"].dt.month
    df["hour"] = df["ts"].dt.hour
    df["day"] = df["ts"].dt.normalize()
    return df.reset_index(drop=True)


def _row_keys(g: pd.DataFrame) -> pd.Series:
    """The modal-construction curve key of every row: rounded sorted prices."""
    P = g[TPO_PR].to_numpy(float)
    M = g[TPO_MW].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(M)
    keys = [
        tuple(np.round(np.sort(P[i][ok[i]]), 2)) if ok[i].any() else None
        for i in range(len(g))
    ]
    return pd.Series(keys, index=g.index)


def _curve_of_key(g: pd.DataFrame, key: tuple) -> list[tuple[float, float]]:
    """The (mw, price) points of the first row carrying ``key`` (ercot-144)."""
    P = g[TPO_PR].to_numpy(float)
    M = g[TPO_MW].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(M)
    i = next(
        j
        for j in range(len(g))
        if ok[j].any() and tuple(np.round(np.sort(P[j][ok[j]]), 2)) == key
    )
    pr = P[i][ok[i]]
    mw = M[i][ok[i]]
    o = np.argsort(mw)
    return list(zip(mw[o].tolist(), pr[o].tolist()))


def derive_year_windows(
    df: pd.DataFrame,
) -> tuple[dict[int, list], dict]:
    """The per-year windowed registry: plant -> [(months, hours, curve)].

    Construction (precommit §0, one rule, uniform, no scope carve-outs):
    the effective curve of (resource, month, hour) is the hour's modal
    price-tuple curve iff that key repeats on a strict majority (>0.5) of the
    month's live days at that hour, else the month's pooled modal curve.
    Identical adjacent cells merge into windows; resources merge to plants via
    :func:`merge_plant_curve` per cell; a plant with zero live resources in a
    month carries its year-pooled plant curve for that month.
    """
    df = df.copy()
    df["key"] = _row_keys(df)
    df = df[df["key"].notna()]
    df["plant_code"] = df["Resource Name"].map(_plant_of)

    # effective per (resource, month, hour) curve, plus the disclosure record
    eff: dict[tuple[str, int, int], tuple] = {}  # (rn, mo, h) -> key
    curves_by_key: dict[tuple[str, tuple], list] = {}  # (rn, key) -> points
    admitted: list[dict] = []
    refused: list[dict] = []
    for (rn, mo), g in df.groupby(["Resource Name", "month"]):
        month_key, _n = Counter(g["key"]).most_common(1)[0]
        curves_by_key.setdefault((rn, month_key), _curve_of_key(g, month_key))
        live_days = g["day"].nunique()
        for h, gh in g.groupby("hour"):
            key, _hn = Counter(gh["key"]).most_common(1)[0]
            if key != month_key:
                dshare = gh[gh["key"] == key]["day"].nunique() / live_days
                cell = {
                    "resource": rn,
                    "month": int(mo),
                    "hour": int(h),
                    "day_share": round(float(dshare), 3),
                    "top": float(max(key)),
                }
                if dshare > 0.5:
                    curves_by_key.setdefault((rn, key), _curve_of_key(gh, key))
                    eff[(rn, mo, h)] = key
                    admitted.append(cell)
                    continue
                refused.append(cell)
            eff[(rn, mo, h)] = month_key
        # hours with no rows in this month fall back to the month key
        for h in range(24):
            eff.setdefault((rn, mo, h), month_key)

    # year-pooled per-resource modal (the zero-live-month plant fallback)
    pooled: dict[str, list] = {}
    for rn, g in df.groupby("Resource Name"):
        key, _n = Counter(g["key"]).most_common(1)[0]
        pooled[rn] = _curve_of_key(g, key)

    live_months: dict[str, set[int]] = {
        rn: set(g["month"].unique()) for rn, g in df.groupby("Resource Name")
    }

    # plant-grain merge per (month, hour), then window collapse
    registry: dict[int, list] = {}
    plants = sorted({c for c in df["plant_code"].dropna().unique().astype(int)})
    res_by_plant: dict[int, list[str]] = {
        int(code): sorted(g["Resource Name"].unique())
        for code, g in df.groupby("plant_code")
    }
    for code in plants:
        units = res_by_plant[code]
        cell_curves: dict[tuple[int, int], tuple] = {}
        for mo in range(1, 13):
            live = [rn for rn in units if mo in live_months[rn]]
            for h in range(24):
                if live:
                    unit_curves = [
                        (
                            np.array(
                                [p[0] for p in curves_by_key[(rn, eff[(rn, mo, h)])]]
                            ),
                            np.array(
                                [p[1] for p in curves_by_key[(rn, eff[(rn, mo, h)])]]
                            ),
                        )
                        for rn in live
                    ]
                else:
                    # zero live resources this month: year-pooled plant curve
                    unit_curves = [
                        (
                            np.array([p[0] for p in pooled[rn]]),
                            np.array([p[1] for p in pooled[rn]]),
                        )
                        for rn in units
                    ]
                merged = merge_plant_curve(unit_curves)
                cell_curves[(mo, h)] = tuple(
                    (round(a, 1), round(b, 2)) for a, b in merged
                )
        # collapse: per month -> maximal hour runs of identical curves,
        # then merge (hours, curve)-identical entries across months.
        per_month: dict[int, list[tuple[tuple[int, ...], tuple]]] = {}
        for mo in range(1, 13):
            runs: list[tuple[list[int], tuple]] = []
            for h in range(24):
                cv = cell_curves[(mo, h)]
                if runs and runs[-1][1] == cv:
                    runs[-1][0].append(h)
                else:
                    runs.append(([h], cv))
            per_month[mo] = [(tuple(hs), cv) for hs, cv in runs]
        groups: dict[tuple[tuple[tuple[int, ...], tuple], ...], list[int]] = {}
        for mo in range(1, 13):
            sig = tuple(per_month[mo])
            groups.setdefault(sig, []).append(mo)
        entries = []
        for sig, months in sorted(groups.items(), key=lambda kv: kv[1][0]):
            for hours, cv in sig:
                entries.append((tuple(months), hours, cv))
        registry[code] = entries

    prov = {
        "admitted_hour_cells": admitted,
        "refused_hour_cells": refused,
        "n_admitted": len(admitted),
        "n_refused": len(refused),
    }
    return registry, prov


def emit_year_mode(year: int, json_out: Path | None) -> int:
    """Run the per-year derivation and print the constants paste block."""
    df = load_corpus_coal(year)
    n_days = df["day"].nunique()
    print(
        f"# delivery-{year} corpus: {len(df):,} CLLIG rows, {n_days} days, "
        f"{df['Resource Name'].nunique()} resources"
    )
    registry, prov = derive_year_windows(df)

    print(
        "# COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO['ERCOT'][%d] — paste into "
        "constants.py" % year
    )
    print('    "ERCOT": {')
    print(f"        {year}: {{")
    for code, entries in registry.items():
        print(f"            {code}: (  # {PLANT_NAMES.get(code, code)}")
        for months, hours, cv in entries:
            # Trailing commas are LOAD-BEARING: a one-point curve emitted as
            # "((1760, 60.26))" collapses to a flat 2-tuple in Python, not a
            # 1-tuple of points — and single-point curves are exactly the
            # Oak Grove overnight windows this lane exists for. Same for a
            # one-element months/hours tuple.
            pts = ", ".join(f"({a:g}, {b:g})" for a, b in cv)
            mo = ", ".join(f"{m:d}" for m in months)
            hr = ", ".join(f"{h:d}" for h in hours)
            print(f"                (({mo},), ({hr},), ({pts},)),")
        print("            ),")
    print("        },")
    print("    },")

    if json_out:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(
            json.dumps(
                {
                    "lane": "ercot168-coal-perplant-year-curves",
                    "year": year,
                    "registry": {
                        str(k): [
                            [list(months), list(hours), [list(p) for p in cv]]
                            for months, hours, cv in v
                        ]
                        for k, v in registry.items()
                    },
                    "provenance": prov,
                    "corpus": {
                        "dir": str(SCED_CORPUS_DIR.relative_to(REPO)),
                        "rows": int(len(df)),
                        "days": int(n_days),
                    },
                },
                indent=1,
            )
        )
        print(f"wrote {json_out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument(
        "--year",
        type=int,
        default=None,
        help="per-year mode (ercot-168): derive the windowed year registry "
        "from the full NP3-965 corpus instead of the pooled 2024-25 "
        "probe-day registry",
    )
    args = ap.parse_args()
    if args.year is not None:
        return emit_year_mode(args.year, args.json_out)

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
