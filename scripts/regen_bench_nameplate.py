#!/usr/bin/env python3
"""Re-encode a committed bench part's per-plant hourly blob on the CORRECTED
EIA-860 nameplate union (no LP solve).

Rule-14 follow-through for the cross-ISO nameplate fix in
``render_calibration_html._eia860_plant_info`` (pjm-159 task C, commit
``46bd8a6b``). That commit unioned the within-window retiree EIA-860 vintage
into the bench nameplate lookup, but **committed bench parts were left
pre-fix** — they are rewritten only when a run registers, and no PJM run has
registered since. This script applies the correction to the committed parts
directly, so the blast radius can be measured without a re-solve.

THE DEFECT, RESTATED. The per-plant hourly series is stored as
``uint8 round(100 * mw / nameplate)`` **clipped at 250**
(``render_calibration_html._b64``). A plant absent from the operable EIA-860
snapshot fell through the ``or 1.0`` guard to ``npl = 1 MW``, so every real
generation hour saturated at the clip and the blob collapsed to a run
indicator (2-6 distinct byte values). Energy is unaffected — consumers rescale
by the committed ``c_ann`` (``legitimacy_diagnostics._decode_cf_bytes``), which
is why no annual gate ever caught it — but the loading profile inside committed
hours is lost, which is what D-1 diurnal shape reads.

SCOPE — deliberately three fields, on the affected plants only:

* ``npl``   — the corrected union nameplate (rounded, as the render rounds it);
* ``name``  — the real plant name (the pre-fix entries carry a bare code);
* ``campd`` — the blob re-encoded at the corrected, UNROUNDED nameplate.

Every other field (``group``, ``zone``, ``nodata``, ``c_ann``, ``c_mon``,
``e_ann``, ``btm``, ``e_mon``, ``split``) and every other plant is left
byte-for-byte, as are the part's ``classFull`` / ``e930`` / ``avgLMP`` /
``storage`` / ``co2`` / ``ctOnly`` blocks.

THE PARITY GUARD is what makes a targeted patch admissible instead of a
re-render. This script rebuilds the CAMPD per-plant hourly frame from
``data/raw`` with the solver's own builder
(``run_calibration_full._campd_hourly_frame``) and then re-encodes EVERY
unaffected single-class plant in the part at its committed nameplate. All of
them must come back **byte-identical**; a single mismatch aborts the run,
because it would mean the rebuilt frame is not the frame the committed part
was built from and the patch would silently mix two bases. Measured on PJM
2023 at the fix: 199/206 identical, and the 7 that differ are exactly the
``npl == 1`` population.

WHAT THIS SCRIPT DOES **NOT** FIX — read this before quoting a D-1 delta. The
defect is TWO-SIDED. The model half of the payload
(``frontend/data/backcast/runs/<id>.js``, ``plants[*].m``) is encoded through
the same ``cap`` and is saturated for the same plants (measured on the PJM
keeper: plant 2866/3122/10678 blobs carry 2 distinct byte values). Regenerating
it requires ``dispatch/<year>_P1.parquet``, which is gitignored and absent
outside a solve. So after this repair D-1 compares a CORRECT actual against a
still-saturated model for those plants, and any resulting movement is an
encoding artifact, not a model property. Use ``--exclusion-diagnostic`` to
measure the affected classes with the affected plants dropped from BOTH sides,
which is the only like-for-like read available without a re-solve.

Rule 22: reads and writes measured-input artifacts only. No year is solved,
scored or registered here; the freeze's ``frozen_operations`` are
solve/score/registration and its ``not_frozen`` list names data intake
explicitly, so repairing an out-of-training year's bench part is permitted —
and required, since a measured input is applied consistently across all years
(owner clarification 2026-08-06).

Rule 25: a shared data-builder repair is not a mechanism verdict; nothing
transfers between ISOs. ``--iso`` is required so one ISO's session never moves
another ISO's gates.

Usage::

    python scripts/regen_bench_nameplate.py --iso PJM --check
    python scripts/regen_bench_nameplate.py --iso PJM
    python scripts/regen_bench_nameplate.py --iso PJM --exclusion-diagnostic
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
for _p in (str(_REPO / "src"), str(_REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.render_calibration_html as rch  # noqa: E402
import scripts.run_calibration_full as rcf  # noqa: E402
from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import bench_multiclass as bm  # noqa: E402

BENCH_DIR = _REPO / "frontend" / "data" / "backcast" / "bench"

#: The ``or 1.0`` guard's own value — a committed nameplate at or below this is
#: the defect signature, never a real plant capacity in a CAMPD-benched fleet.
NPL_FLOOR_MW = 1.0

#: Full-year hour count the blob is padded/truncated to (``_b64``'s ``_T``).
HOURS = 8760


def _campd_by_plant(iso: str, year: int) -> dict[int, np.ndarray]:
    """Rebuild ``{plant_id: 8760-hour net MW}`` from ``data/raw`` for ``year``.

    Uses the solver's own builder so the frame is the one the bench part was
    rendered from — the parity guard below proves that, plant by plant.
    """
    frame = rcf._campd_hourly_frame(year, iso, rcf._parasitic_factor_map(), HOURS)
    if frame is None or frame.empty:
        raise SystemExit(f"{iso} {year}: no CAMPD extract — cannot rebuild the frame")
    out: dict[int, np.ndarray] = {}
    for code, g in frame.groupby("plant_id", observed=True):
        a = np.nan_to_num(g.sort_values("hour")["net_mw"].to_numpy(float))
        out[int(code)] = np.concatenate([a, np.zeros(max(0, HOURS - a.shape[0]))])[
            :HOURS
        ]
    return out


def _retiree_only_codes() -> set[int]:
    """Plant codes carried ONLY by the within-window retiree EIA-860 vintage.

    The defect population, stated definitionally: these are exactly the plants
    the operable snapshot omits, so before the union they fell through the
    ``or 1.0`` guard. Reading it this way lets the exclusion diagnostic identify
    the same set before and after the bench parts are repaired.
    """
    import pandas as pd

    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.fleet import EIA_860_PARQUET_NAME
    from market_sim.data.fleet.eia860 import EIA_860_RETIRED_WINDOW_PARQUET_NAME

    def _codes(name: str) -> set[int]:
        path = EIA_860_DIR / name
        if not path.exists():
            return set()
        return set(pd.read_parquet(path, columns=["plant_id"])["plant_id"].astype(int))

    return _codes(EIA_860_RETIRED_WINDOW_PARQUET_NAME) - _codes(EIA_860_PARQUET_NAME)


def _decode(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Consumer-side decode (mirrors ``legitimacy_diagnostics._decode_cf_bytes``)."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def _bench_years(iso: str) -> list[int]:
    """Every committed bench year for ``iso``, ascending."""
    return sorted(
        int(p.stem.split(".")[0]) for p in (BENCH_DIR / iso).glob("*.json.gz")
    )


def regen_year(
    iso: str, year: int, *, check: bool, verbose: bool = True
) -> tuple[list[dict], int]:
    """Repair one bench part. Returns ``(repaired rows, n plants guarded)``."""
    path = BENCH_DIR / iso / f"{year}.json.gz"
    if not path.exists():
        raise SystemExit(f"missing bench part {path}")
    part = ba.load_bench_part(path)
    plants = part["bench"]["plants"]

    cn_p = _campd_by_plant(iso, year)
    npl_map = rch._nameplates()
    name_map = rch._plant_names()

    repaired: list[dict] = []
    guarded = 0
    for key, p in plants.items():
        committed_npl = float(p.get("npl") or 0.0)
        code = int(bm.plant_code_of_key(key))
        stranded = committed_npl <= NPL_FLOOR_MW
        if bm.KEY_SEP in key:
            # Multi-class slices carry a SPLIT series (bench_multiclass), which
            # this targeted patch does not reproduce. None is stranded in PJM;
            # refuse rather than guess if another ISO ever hits one.
            if stranded and float(p.get("c_ann") or 0.0) > 0.0:
                raise SystemExit(
                    f"{iso} {year}: stranded MULTI-CLASS slice {key!r} — the "
                    "measured-series split is not reproduced here; re-render "
                    "this ISO's bundle instead of patching."
                )
            continue
        cn = cn_p.get(code)
        if cn is None:
            # Bench plant absent from the rebuilt frame (never seen in PJM).
            if stranded:
                raise SystemExit(
                    f"{iso} {year}: stranded plant {code} is absent from the "
                    "rebuilt CAMPD frame — cannot re-encode its blob."
                )
            continue

        if not stranded:
            # PARITY GUARD. The committed blob was encoded at the UNROUNDED
            # nameplate; ``npl`` is its rounded display copy. Re-encoding at the
            # unrounded value must reproduce the committed bytes exactly.
            cap = float(npl_map.get(code, 0.0)) or 1.0
            if rch._b64(100.0 * cn / cap) != p["campd"]:
                raise SystemExit(
                    f"{iso} {year}: plant {code} ({p.get('group')}, committed "
                    f"npl {committed_npl:g} MW) does NOT re-encode to its "
                    "committed blob from the rebuilt CAMPD frame — the part was "
                    "built on a different basis. Refusing to patch."
                )
            guarded += 1
            continue

        # ---- the repair ----
        cap_new = float(npl_map.get(code, 0.0))
        if cap_new <= NPL_FLOOR_MW:
            print(
                f"  {iso} {year}: plant {code} is stranded and STILL has no "
                f"EIA-860 nameplate in either vintage ({cap_new:g} MW) — left "
                "unrepaired; its hourly blob remains unusable.",
                file=sys.stderr,
            )
            continue
        blob_new = rch._b64(100.0 * cn / cap_new)
        c_ann_committed = float(p.get("c_ann") or 0.0)
        c_ann_rebuilt = round(float(cn.sum()) / 1e6, 4)
        # GUARD (energy identity): the repair re-encodes the SAME series, so the
        # committed annual must reproduce. A drift here means the rebuilt series
        # is not the committed one and the c_ann rescale would silently relevel.
        if abs(c_ann_rebuilt - c_ann_committed) > 5e-4:
            raise SystemExit(
                f"{iso} {year}: plant {code} c_ann {c_ann_committed} does not "
                f"reproduce from the rebuilt frame ({c_ann_rebuilt}); refusing."
            )
        old_series = _decode(p["campd"], c_ann_committed, committed_npl)
        new_series = _decode(blob_new, c_ann_committed, float(round(cap_new)))
        raw_old = np.frombuffer(base64.b64decode(p["campd"]), dtype=np.uint8)
        raw_new = np.frombuffer(base64.b64decode(blob_new), dtype=np.uint8)
        row = {
            "iso": iso,
            "year": year,
            "code": code,
            "group": str(p.get("group") or "?"),
            "name_old": str(p.get("name") or "?"),
            "name_new": name_map.get(code, str(code)),
            "npl_old": committed_npl,
            "npl_new": round(cap_new),
            "c_ann": c_ann_committed,
            "distinct_old": int(np.unique(raw_old).size),
            "distinct_new": int(np.unique(raw_new).size),
            "pct_clip_old": round(100.0 * float((raw_old == 250).mean()), 1),
            "pct_clip_new": round(100.0 * float((raw_new == 250).mean()), 1),
            # How much the DECODED hourly series moves, as a share of its own
            # energy — the quantity D-1 actually reads.
            "shape_l1_pct": round(
                100.0
                * float(np.abs(new_series - old_series).sum())
                / max(float(old_series.sum()), 1e-9),
                1,
            ),
        }
        repaired.append(row)
        if verbose:
            print(
                f"  {iso} {year} {code:>6} {row['group']:<11} "
                f"npl {committed_npl:g} -> {row['npl_new']} MW  "
                f"({row['name_new']}) blob {row['distinct_old']} -> "
                f"{row['distinct_new']} distinct bytes, clip "
                f"{row['pct_clip_old']}% -> {row['pct_clip_new']}%, "
                f"hourly L1 {row['shape_l1_pct']}% of energy"
            )
        if check:
            continue
        p["npl"] = row["npl_new"]
        p["name"] = row["name_new"]
        p["campd"] = blob_new

    if repaired and not check:
        ba.write_bench_part(BENCH_DIR, iso, year, part["meta"], part["bench"])
    return repaired, guarded


def exclusion_diagnostic(
    iso: str, years: list[int], affected: set[tuple[int, int]]
) -> None:
    """Report each affected class's actual energy share held by repaired plants.

    The like-for-like read. The D-1 movement this repair produces is confined
    to classes holding a repaired plant, and its scale is bounded by that
    plant's share of the class's actual energy — so a D-1 delta on a class whose
    affected share is 3 % cannot be a model finding, and one on a class at 25 %
    is dominated by the encoding change on the actual side alone (the model side
    of those same plants is NOT repaired; see the module docstring).

    ``affected`` is the ``{(year, plant_code)}`` set the repair pass reports, so
    the diagnostic identifies the population the same way whether it runs before
    or after the parts are written.
    """
    print("\nexclusion diagnostic — repaired plants' share of their class actual")
    print(
        f"{'year':>5} {'class':<12} {'affected TWh':>13} {'class TWh':>11} {'share':>7}"
    )
    for year in years:
        part = ba.load_bench_part(BENCH_DIR / iso / f"{year}.json.gz")
        by_class: dict[str, float] = {}
        hit: dict[str, float] = {}
        for key, p in part["bench"]["plants"].items():
            grp = str(p.get("group") or "?")
            c_ann = float(p.get("c_ann") or 0.0)
            by_class[grp] = by_class.get(grp, 0.0) + c_ann
            if (year, int(bm.plant_code_of_key(key))) in affected:
                hit[grp] = hit.get(grp, 0.0) + c_ann
        for grp, twh in sorted(hit.items()):
            tot = by_class.get(grp, 0.0)
            print(
                f"{year:>5} {grp:<12} {twh:>13.3f} {tot:>11.3f} "
                f"{(100.0 * twh / tot if tot else 0.0):>6.1f}%"
            )


def main() -> None:
    """Repair (or report on) one ISO's committed bench parts."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True, help="ISO id (rule 25: one lane only)")
    ap.add_argument(
        "--years", type=int, nargs="*", default=None, help="default: every bench year"
    )
    ap.add_argument(
        "--check", action="store_true", help="report without writing the parts"
    )
    ap.add_argument(
        "--exclusion-diagnostic",
        action="store_true",
        help="print each affected class's energy share held by repaired plants",
    )
    args = ap.parse_args()

    iso = args.iso.upper()
    years = args.years or _bench_years(iso)
    if not years:
        raise SystemExit(f"no committed bench parts for {iso}")

    if args.exclusion_diagnostic:
        # Identify the population DEFINITIONALLY (present only in the retiree
        # vintage) rather than by ``npl <= 1``, so the diagnostic reads the same
        # before and after the parts are repaired.
        retiree_only = _retiree_only_codes()
        affected = {
            (year, int(bm.plant_code_of_key(key)))
            for year in years
            for key, p in ba.load_bench_part(BENCH_DIR / iso / f"{year}.json.gz")[
                "bench"
            ]["plants"].items()
            if int(bm.plant_code_of_key(key)) in retiree_only
            and float(p.get("c_ann") or 0.0) > 0.0
        }
        exclusion_diagnostic(iso, years, affected)
        return

    all_rows: list[dict] = []
    for year in years:
        rows, guarded = regen_year(iso, year, check=args.check)
        print(
            f"{iso} {year}: {len(rows)} plant(s) repaired, {guarded} verified "
            "byte-identical (parity guard)"
        )
        all_rows.extend(rows)

    twh = sum(r["c_ann"] for r in all_rows)
    verb = "would repair" if args.check else "repaired"
    print(f"\n{verb} {len(all_rows)} plant-year(s) / {twh:.2f} TWh across {years}")
    if all_rows and not args.check:
        print(
            "NOTE: the MODEL half of the payload (runs/<id>.js plants[*].m) is "
            "encoded through the same nameplate and is NOT repaired here — see "
            "this module's docstring before quoting a D-1 delta."
        )


if __name__ == "__main__":
    main()
