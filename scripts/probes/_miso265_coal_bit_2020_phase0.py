"""miso-265 phase 0 — localize MISO's 2020 COAL_BIT deficit, at ZERO LP.

The predecessor (``RESULT-miso264`` §7) routed this session a named object:
*"in 2020 the price residual and the coal-volume residual demand OPPOSITE offer
moves, so MISO's coal is held off by something that is NOT its offer — a
QUANTITY / COMMITMENT object."* Before any lever is proposed, that claim needs
a footprint: **which plants** carry the 10.92 TWh, and is the shortfall spread
across the COAL_BIT fleet or concentrated in a few units?

Everything here reads COMMITTED artifacts only — the registered run payload
(per-plant model annual/monthly energy) and the committed bench part (per-plant
CAMPD and EIA-923 actuals). No solve, no fleet rebuild, nothing fetched.

Two bases are reported side by side deliberately, because they answer different
questions and the MISO log records a session that crossed them
(``docs/calibration-log/miso.md``, the miso-127 ``apply_other_fossil_scoring``
correction): ``gmModel``/``classFull`` is the C1 GATING basis, while the
per-plant ``m_ann``/``c_ann`` pair is the reconstruction basis. Coal carries no
``OTHER_FOSSIL`` re-bucketing and no CHP add-back, so for the coal classes the
two agree; the script asserts that rather than assuming it.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: Registered MISO keeper at the time of writing (rule 15 keeper-only retention).
DEFAULT_RUN = "2026-09-20-miso-264-anchor-vintage"


def load_payload(run_id: str) -> dict:
    """Return the decoded run payload for ``run_id``.

    The dashboard payload is stored as a base64 gzip blob inside a ``.js``
    assignment, so it is decoded rather than parsed as JSON.
    """
    path = REPO / "frontend/data/backcast/runs" / f"{run_id}.js"
    blob = re.search(r'runGz\["[^"]+"\]="([^"]+)"', path.read_text())
    if blob is None:
        raise SystemExit(f"no runGz payload in {path}")
    return json.loads(gzip.decompress(base64.b64decode(blob.group(1))))


def load_bench(iso: str, year: int) -> dict:
    """Return the committed benchmark part for ``iso``/``year``."""
    path = REPO / "frontend/data/backcast/bench" / iso.upper() / f"{year}.json.gz"
    with gzip.open(path, "rt") as fh:
        return json.load(fh)["bench"]


def plant_table(payload: dict, bench: dict, year: int, klass: str) -> list[dict]:
    """Return per-plant model/actual rows for one class, deficit-sorted.

    ``c_ann`` (CAMPD) is preferred as the actual because it is the metered
    stack-level series; ``e_ann`` (EIA-923) is carried alongside so a plant whose
    two actuals disagree is visible rather than silently averaged.
    """
    model = payload["years"][str(year)]["plants"]
    rows = []
    for code, rec in bench["plants"].items():
        if rec.get("group") != klass:
            continue
        m = model.get(code) or {}
        rows.append(
            {
                "code": code,
                "name": rec.get("name", "?"),
                "zone": rec.get("zone", "?"),
                "npl_mw": float(rec.get("npl") or 0.0),
                "model": float(m.get("m_ann") or 0.0),
                "campd": float(rec.get("c_ann") or 0.0),
                "e923": float(rec.get("e_ann") or 0.0),
                "in_model": code in model,
                "nodata": bool(rec.get("nodata")),
            }
        )
    for r in rows:
        r["delta"] = r["model"] - r["campd"]
    rows.sort(key=lambda r: r["delta"])
    return rows


def _cf(twh: float, mw: float) -> float:
    """Capacity factor from annual TWh and nameplate MW (0.0 when MW is zero)."""
    return 0.0 if mw <= 0 else twh * 1e6 / (mw * 8784.0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", default=DEFAULT_RUN)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--klass", default="COAL_BIT")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    payload = load_payload(args.run)
    bench = load_bench(args.iso, args.year)
    rows = plant_table(payload, bench, args.year, args.klass)

    gm = float(payload["years"][str(args.year)]["gmModel"].get(args.klass, 0.0))
    cf_bench = float(bench["classFull"].get(args.klass, 0.0))

    print(f"=== {args.iso} {args.year} {args.klass} — per-plant, ZERO LP ===")
    print(f"run     : {args.run}")
    print(f"C1 gating basis : model {gm:.2f}  actual {cf_bench:.2f}  d {gm - cf_bench:+.2f} TWh")
    tot_m = sum(r["model"] for r in rows)
    tot_c = sum(r["campd"] for r in rows)
    tot_e = sum(r["e923"] for r in rows)
    print(
        f"per-plant sum   : model {tot_m:.2f}  campd {tot_c:.2f}  e923 {tot_e:.2f} "
        f"| {len(rows)} plants"
    )
    print(
        f"  basis check   : |per-plant model - gmModel| = {abs(tot_m - gm):.4f} TWh ; "
        f"|per-plant e923 - classFull| = {abs(tot_e - cf_bench):.4f} TWh"
    )
    print()
    hdr = (
        f"{'code':>6} {'plant':28} {'zone':12} {'MW':>7} {'model':>8} {'campd':>8} "
        f"{'e923':>8} {'delta':>8} {'cf_m':>6} {'cf_a':>6}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows[: args.top]:
        flag = "" if r["in_model"] else "  <-- NOT IN MODEL"
        print(
            f"{r['code']:>6} {r['name'][:28]:28} {r['zone'][:12]:12} {r['npl_mw']:7.0f} "
            f"{r['model']:8.3f} {r['campd']:8.3f} {r['e923']:8.3f} {r['delta']:+8.3f} "
            f"{_cf(r['model'], r['npl_mw']):6.3f} {_cf(r['campd'], r['npl_mw']):6.3f}{flag}"
        )
    print()
    neg = [r for r in rows if r["delta"] < 0]
    pos = [r for r in rows if r["delta"] > 0]
    absent = [r for r in rows if not r["in_model"] and r["campd"] > 0.01]
    zero_m = [r for r in rows if r["in_model"] and r["model"] < 0.01 and r["campd"] > 0.01]
    print(
        f"SUMMARY: {len(neg)} plants short (sum {sum(r['delta'] for r in neg):+.2f} TWh), "
        f"{len(pos)} long (sum {sum(r['delta'] for r in pos):+.2f} TWh)"
    )
    print(
        f"  plants in the bench but ABSENT from the model payload, with actual > 0: "
        f"{len(absent)} (sum {sum(r['campd'] for r in absent):.2f} TWh actual)"
    )
    for r in absent:
        print(f"    {r['code']:>6} {r['name'][:30]:30} {r['npl_mw']:7.0f} MW  actual {r['campd']:.3f}")
    print(
        f"  plants in the model at ~ZERO with actual > 0: {len(zero_m)} "
        f"(sum {sum(r['campd'] for r in zero_m):.2f} TWh actual)"
    )
    for r in zero_m:
        print(f"    {r['code']:>6} {r['name'][:30]:30} {r['npl_mw']:7.0f} MW  actual {r['campd']:.3f}")
    print()
    # Concentration: how many plants carry the first half of the deficit?
    run = 0.0
    half = sum(r["delta"] for r in neg) / 2.0
    for i, r in enumerate(rows, 1):
        run += r["delta"]
        if run <= half:
            print(f"  concentration: {i} plants carry half the shortfall ({run:+.2f} of {sum(r['delta'] for r in neg):+.2f} TWh)")
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
