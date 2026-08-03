"""nyiso-113 probe A — the rule-28(c) MATRIX-GAP SWEEP for NYISO.

nyiso-112 promoted a mechanism (`nysdec_peaker_rule_availability`) that was
found only because it had **no row in the cross-ISO mechanism matrix at all** —
a rule 28(c) hygiene gap that made a solve-affecting, NYISO-live field invisible
to every session since it was written. The standing lesson recorded in
`docs/calibration-log/nyiso.md` §5 (nyiso-111/112) is that the exhausted-queue
finding was true of the *queue*, and the queue was incomplete.

This probe generalises that finding into a mechanical census over the live
`ScenarioConfig` (imported, so defaults are the shipped ones — not a parse of
the source) crossed against `docs/codebase-site/data/mechanism-matrix.js`:

* **the NYISO family** — every `nyiso_*` / `nysdec_*` field: is it mentioned in
  the matrix at all, which row owns it, what does that row's NYISO cell say,
  and does the current keeper arm it?
* **live-but-invisible** — any field (NYISO-exclusive or shared) that some
  NYISO bundle on disk sets **away from its shipped default** while the matrix
  never mentions it. That is exactly the shape of the 227-3 gap, and it is the
  one class that can hide a promotable mechanism.

The output is evidence for adding matrix rows (rule 28(c)); it never adjudicates
a verdict on its own — a `U` cell is the most a census can mint (rule 25).

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso113_matrix_gap_sweep.py
Writes: results/calibration/_nyiso113_matrix_gap_sweep.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MATRIX = REPO / "docs/codebase-site/data/mechanism-matrix.js"
KEEPER_SHARD = REPO / "frontend/data/backcast/keepers/NYISO.json"
CALIB_DIR = REPO / "results/calibration"
REGISTRY = REPO / "frontend/data/backcast/registry"
OUT = CALIB_DIR / "_nyiso113_matrix_gap_sweep.json"

ISO_INDEX = {"E": 0, "C": 1, "P": 2, "M": 3, "N": 4, "Q": 5}


def scenario_defaults() -> dict[str, object]:
    """Shipped `ScenarioConfig` defaults, from the live class (not a parse)."""
    import dataclasses  # noqa: PLC0415

    from market_sim.config.scenarios import ScenarioConfig  # noqa: PLC0415

    out: dict[str, object] = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.default is not dataclasses.MISSING:
            out[f.name] = f.default
        elif f.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
            out[f.name] = f.default_factory()  # type: ignore[misc]
        else:
            out[f.name] = "<required>"
    return out


def matrix_rows() -> list[dict]:
    """Every matrix row as {id, cells, blob} — blob is the row's whole source."""
    src = MATRIX.read_text()
    chunks = re.split(r'\n\s*\{\s*id:\s*"', src)[1:]
    rows = []
    for ch in chunks:
        rid = ch.split('"', 1)[0]
        body = ch.split('"', 1)[1]
        m = re.search(r'cells:\s*"([KRIGOU.]{6})"', body)
        rows.append({"id": rid, "cells": m.group(1) if m else None, "blob": body})
    return rows


def run_configs() -> dict[str, dict]:
    """Every NYISO bundle's ScenarioConfig on disk, keyed by bundle name.

    `run_config.json` wraps the config under `scenario_config` alongside
    provenance blocks (`git`, `calibration_flags`, `environment`); the census
    only cares about the config itself.
    """
    out: dict[str, dict] = {}
    for cfg in sorted(CALIB_DIR.glob("nyiso*/run_config.json")):
        try:
            doc = json.loads(cfg.read_text())
        except Exception:  # noqa: BLE001 - a corrupt bundle must not stop the census
            continue
        out[cfg.parent.name] = doc.get("scenario_config", doc)
    return out


def _norm(v: object) -> object:
    """Normalise a config value for cross-source comparison (JSON vs python)."""
    if isinstance(v, tuple):
        return list(v)
    return v


def main() -> None:
    defaults = scenario_defaults()
    rows = matrix_rows()
    blob = MATRIX.read_text().lower()
    cfgs = run_configs()
    keeper_id = json.loads(KEEPER_SHARD.read_text())["keeper"]

    keeper_cfg: dict = {}
    reg = REGISTRY / f"{keeper_id}.json"
    if reg.exists():
        bundle = json.loads(reg.read_text()).get("bundle", "")
        keeper_cfg = cfgs.get(Path(bundle).name, {})
    if not keeper_cfg:
        keeper_cfg = cfgs.get("nyiso112_combined_D", {})

    def owners(field: str) -> list[dict]:
        """Matrix rows whose source text mentions this field."""
        return [
            {"row": r["id"], "cells": r["cells"], "nyiso": (r["cells"] or "??????")[ISO_INDEX["N"]]}
            for r in rows
            if field in r["blob"] or field == r["id"]
        ]

    def coverage(field: str) -> str:
        """How well the matrix covers a field — three materially different states.

        `mention-anywhere` is the CI checker's deliberate escape hatch (rule
        28(c)): a sub-scalar of an existing family belongs on the family's row,
        not its own. But a field mentioned ONLY inside an unrelated row's prose
        has no cell of its own, so no verdict is recorded for it anywhere —
        the same invisibility the 227-3 gap had, one level subtler. Distinguish:

        * ``own_row``   — the field has a row carrying its own cell + verdict.
        * ``prose_only`` — mentioned, but only inside some other row's text.
        * ``absent``    — not mentioned anywhere in the matrix.

        The matrix's own convention is that rows are **ISO-neutral mechanism
        families** and a per-ISO flag is that ISO's leg of the family (e.g.
        `nyiso_gas_commitment_bridge` is the NYISO leg of row
        `gas_commitment_bridge`, whose `def` references it in the short form
        ``nyiso :2609``). So the stem — the field with its ISO prefix removed —
        is what identifies the owning row, not the literal flag name. Matching
        literally would over-report gaps for correctly-registered legs.
        """
        stem = field[len("nyiso_") :] if field.startswith("nyiso_") else field
        for r in rows:
            if r["id"] in (field, stem):
                return "own_row"
            head = r["blob"].split("note:", 1)[0]
            if field in head or (stem and stem in head):
                return "own_row"
        return "prose_only" if field.lower() in blob else "absent"

    # --- (1) the NYISO-exclusive family census -------------------------------
    family = sorted(f for f in defaults if f.startswith("nyiso_") or f.startswith("nysdec"))
    family_rows = []
    for f in family:
        own = owners(f)
        kv = keeper_cfg.get(f, "<absent>")
        family_rows.append(
            {
                "field": f,
                "default": _norm(defaults[f]),
                "keeper_value": _norm(kv),
                "keeper_arms_it": bool(kv) if kv != "<absent>" else None,
                "mentioned_in_matrix": f.lower() in blob,
                "coverage": coverage(f),
                "owning_rows": own,
                "nyiso_cells": sorted({o["nyiso"] for o in own}),
                "armed_in_bundles": sorted(
                    b for b, c in cfgs.items() if _norm(c.get(f)) not in (None, False)
                ),
            }
        )

    # --- (2) live-but-invisible: non-default in a bundle, absent from matrix --
    live_invisible = []
    for f, dflt in defaults.items():
        if f.lower() in blob:
            continue
        movers = {
            b: _norm(c[f]) for b, c in cfgs.items() if f in c and _norm(c[f]) != _norm(dflt)
        }
        if movers:
            live_invisible.append(
                {
                    "field": f,
                    "default": _norm(dflt),
                    "keeper_value": _norm(keeper_cfg.get(f, "<absent>")),
                    "n_bundles_nondefault": len(movers),
                    "bundles": dict(sorted(movers.items())[:6]),
                }
            )
    live_invisible.sort(key=lambda d: -d["n_bundles_nondefault"])

    # --- (3) NYISO-family fields with no CELL of their own -------------------
    # Two distinct rule-28(c) gaps: `absent` (the 227-3 shape — invisible
    # outright) and `prose_only` (named in some other row's note, so the CI
    # mention-anywhere gate passes, but NO cell records a verdict for it).
    family_gaps = [r for r in family_rows if r["coverage"] == "absent"]
    prose_only = [r for r in family_rows if r["coverage"] == "prose_only"]
    armed_no_cell = [
        r for r in family_rows if r["coverage"] != "own_row" and r["keeper_arms_it"]
    ]

    result = {
        "probe": "nyiso-113 matrix-gap sweep",
        "keeper": keeper_id,
        "keeper_bundle_fields": len(keeper_cfg),
        "n_scenario_fields": len(defaults),
        "n_matrix_rows": len(rows),
        "n_bundles_scanned": len(cfgs),
        "nyiso_family": family_rows,
        "nyiso_family_matrix_gaps_absent": [r["field"] for r in family_gaps],
        "nyiso_family_prose_only": [r["field"] for r in prose_only],
        "armed_on_keeper_with_no_cell": [r["field"] for r in armed_no_cell],
        "live_but_invisible": live_invisible,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=str))

    print(f"ScenarioConfig fields   : {len(defaults)}")
    print(f"matrix rows             : {len(rows)}")
    print(f"NYISO bundles scanned   : {len(cfgs)}")
    print(f"keeper                  : {keeper_id}  ({len(keeper_cfg)} config fields)")
    print()
    print(f"=== NYISO-family census ({len(family)} fields) ===")
    print(f"{'field':<44}{'dflt':<7}{'keeper':<8}{'mtx':<5}{'N-cell':<8}{'armed in bundles'}")
    for r in family_rows:
        cells = ",".join(c for c in r["nyiso_cells"]) or "-"
        print(
            f"{r['field']:<44}{str(r['default'])[:6]:<7}{str(r['keeper_value'])[:7]:<8}"
            f"{('YES' if r['mentioned_in_matrix'] else 'NO'):<5}{cells:<8}"
            f"{len(r['armed_in_bundles'])}"
        )
    print()
    print(f"=== rule-28(c) ABSENT from the matrix: {len(family_gaps)} ===")
    for r in family_gaps:
        print(f"  {r['field']:<44} keeper={r['keeper_value']} armed_in={len(r['armed_in_bundles'])}")
    print()
    print(f"=== PROSE-ONLY (mentioned, but no cell of its own): {len(prose_only)} ===")
    for r in prose_only:
        print(f"  {r['field']:<44} keeper={r['keeper_value']} rows={[o['row'] for o in r['owning_rows']]}")
    print()
    print(f"=== ARMED ON THE KEEPER WITH NO CELL ANYWHERE: {len(armed_no_cell)} ===")
    for r in armed_no_cell:
        print(f"  {r['field']:<44} coverage={r['coverage']}")
    print()
    print(f"=== LIVE-BUT-INVISIBLE (non-default in a NYISO bundle, no matrix mention): {len(live_invisible)} ===")
    for r in live_invisible:
        print(f"  {r['field']:<44} dflt={str(r['default'])[:20]:<22} keeper={str(r['keeper_value'])[:24]:<26} n={r['n_bundles_nondefault']}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
