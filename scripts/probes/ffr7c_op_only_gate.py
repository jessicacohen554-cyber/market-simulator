"""FFR-7C §6: what an OP-only vintage gate would do to the corrected target.

Reports (never decides) FFR-7A §9.3 / §1.2's deliberately-not-taken scope
question: the shipped rule-5a gate drops units already ``OS``/``RE`` at the
fleet vintage; widening it to "keep only units that were ``OP`` at the vintage"
would also drop ``SB``/``OA``-at-vintage units, and — as a separate, stricter
third step — units absent from the vintage release altogether.

Committed-artifact measurement only: no solve, no scoring, no target rewrite.
The shipped builder (``scripts/data/build_capacity_actuals.py``) is imported
and called read-only; nothing is written to ``data/``.

Two candidate widenings are tabulated separately so the owner can adopt either
independently:

* **OP-only (observed)** — drop retained rows whose vintage status is ``SB``
  or ``OA``. This is the literal §1.2 wording.
* **+ absent-at-vintage** — additionally drop rows for units the vintage
  release does not carry at all. Reported apart because the builder's own
  docstring gives the counter-argument ("a unit merely *absent* from the
  vintage is not gated — it was built inside the window, and the model can
  build it too"), which is true of a genuine in-window build but not of a unit
  the vintage release simply failed to report.

Usage::

    uv run python scripts/probes/ffr7c_op_only_gate.py \\
        --out docs/handoffs/ffr-7c/op-only-gate-2026-08-06.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.data.build_capacity_actuals import (  # noqa: E402
    FLEET_VINTAGE_YEAR,
    _iso_to_ba,
    build_retirements,
    load_release_history,
)

ISOS = ("ERCOT", "PJM", "MISO", "NYISO", "NEISO")  # CAISO has no committed target
THERMAL_FUELS = frozenset(
    {"coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear", "biomass"}
)


def vintage_status_map(bas: set[str]) -> dict[tuple[int, str], str]:
    """``{(plant_id, generator_id): Status}`` at the fleet vintage release."""
    hist = load_release_history(bas)
    if hist.empty:
        return {}
    at = hist[hist["release_year"] == FLEET_VINTAGE_YEAR]
    return {(int(r.plant_id), r.generator_id): r.status for r in at.itertuples()}


def classify(iso: str) -> pd.DataFrame:
    """Retained retirement rows for one ISO, tagged with vintage status."""
    bas = _iso_to_ba(iso)
    df = build_retirements(bas)
    vmap = vintage_status_map(bas)
    # unit_id is "<plant>_<generator>"; recover the generator half by stripping
    # the plant prefix (generator ids may themselves contain "_").
    gen = [str(u)[len(str(p)) + 1 :] for u, p in zip(df["unit_id"], df["plant_id"])]
    df = df.assign(
        vintage_status=[
            vmap.get((int(p), g), "ABSENT") for p, g in zip(df["plant_id"], gen)
        ]
    )
    df["iso"] = iso
    return df


def main(argv: list[str] | None = None) -> int:
    """Tabulate the two candidate widenings per ISO and write the JSON."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=None, help="JSON output path.")
    args = p.parse_args(argv)

    frames = [classify(iso) for iso in ISOS]
    allrows = pd.concat(frames, ignore_index=True)

    payload: dict = {
        "fleet_vintage": FLEET_VINTAGE_YEAR,
        "note": (
            "Rows are the CURRENT (shipped-gate) target. vintage_status is the "
            "unit's EIA-860 Status at the fleet-vintage release; ABSENT means "
            "that release does not carry the unit (a genuine in-window build, "
            "or a release coverage gap). OS/RE cannot appear — the shipped "
            "gate already drops those."
        ),
        "per_iso": {},
    }

    hdr = (
        "| ISO | rows | thermal GW | SB/OA rows | SB/OA MW | SB/OA thermal MW "
        "| ABSENT rows | ABSENT MW | ABSENT thermal MW |"
    )
    print(hdr)
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for iso in ISOS:
        d = allrows[allrows["iso"] == iso]
        th = d[d["fuel"].isin(THERMAL_FUELS)]
        sboa = d[d["vintage_status"].isin(("SB", "OA"))]
        absent = d[d["vintage_status"] == "ABSENT"]
        row = {
            "rows": int(len(d)),
            "thermal_gw": round(float(th["mw"].sum()) / 1000.0, 3),
            "sb_oa_rows": int(len(sboa)),
            "sb_oa_mw": round(float(sboa["mw"].sum()), 1),
            "sb_oa_thermal_mw": round(
                float(sboa[sboa["fuel"].isin(THERMAL_FUELS)]["mw"].sum()), 1
            ),
            "absent_rows": int(len(absent)),
            "absent_mw": round(float(absent["mw"].sum()), 1),
            "absent_thermal_mw": round(
                float(absent[absent["fuel"].isin(THERMAL_FUELS)]["mw"].sum()), 1
            ),
            "status_census": {
                str(k): int(v)
                for k, v in d["vintage_status"].value_counts().sort_index().items()
            },
            "sb_oa_units": [
                {
                    "unit_id": r.unit_id,
                    "fuel": r.fuel,
                    "mw": float(r.mw),
                    "year": int(r.year),
                    "vintage_status": r.vintage_status,
                }
                for r in sboa.sort_values("mw", ascending=False).itertuples()
            ],
            "absent_units_ge_25mw": [
                {
                    "unit_id": r.unit_id,
                    "fuel": r.fuel,
                    "mw": float(r.mw),
                    "year": int(r.year),
                }
                for r in absent[absent["mw"] >= 25.0]
                .sort_values("mw", ascending=False)
                .itertuples()
            ],
        }
        payload["per_iso"][iso] = row
        print(
            f"| {iso} | {row['rows']} | {row['thermal_gw']} | {row['sb_oa_rows']} | "
            f"{row['sb_oa_mw']} | {row['sb_oa_thermal_mw']} | {row['absent_rows']} | "
            f"{row['absent_mw']} | {row['absent_thermal_mw']} |"
        )

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(payload, indent=1))
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
