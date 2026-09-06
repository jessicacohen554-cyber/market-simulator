"""Rule-28(c) MATRIX-GAP SWEEP — the cross-ISO census, for any ISO lane.

**Why this exists.** nyiso-112 promoted a mechanism
(`nysdec_peaker_rule_availability`) that was found only because it had **no row
in the cross-ISO mechanism matrix at all** — a solve-affecting, ISO-live field
invisible to every session since it was written. nyiso-113 turned that anecdote
into a mechanical census for NYISO and measured the damage: **25 `nyiso_*`
fields absent from the matrix, 5 prose-only, and 17 of them ARMED ON THE KEEPER
with no cell anywhere**, four of which were carried in the keeper's own DOF
ledger and still had no cell.

**Why CI could not find them.** `check_mechanism_matrix.py`'s diff gate enforces
rule 28(c) only for fields **added in the same PR**. Every field predating the
gate is structurally invisible to it. That is a standing blind spot in *every*
ISO column, not a NYISO accident — which is what makes this a standing tool
rather than the one-lane probe it started as
(`scripts/probes/_nyiso113_matrix_gap_sweep.py`, superseded).

**What it measures**, per ISO, against the live `ScenarioConfig` (imported, so
the defaults are the *shipped* ones and not a parse of the source):

* **the ISO family** — every field carrying that ISO's own stem: is it mentioned
  in the matrix at all, which row owns it, what does that row's cell for this
  ISO say, and does the ISO's current keeper arm it?
* **live-but-invisible** — any field (ISO-exclusive or shared) that some bundle
  of this ISO sets **away from its shipped default** while the matrix never
  mentions it. That is exactly the shape of the 227-3 gap, and it is the one
  class that can hide a promotable mechanism.

and once, ISO-agnostically (y20):

* **absent-shared** — every SHARED field the matrix never mentions, armed or
  not. Both censuses above carry a qualifier a slipped field can simply not
  satisfy (an ISO stem; a backcast keeper arming it), so a forecast-only shared
  field with no row had no census at all — the hole
  ``docs/handoffs/FINDING-scn-mxr-2026-09-06.md`` §1.1 diagnosed after PR #4870
  merged two such fields five seconds after opening, past a red diff gate.

The output is evidence for adding matrix rows (rule 28(c)); it never adjudicates
a verdict on its own — a `U` cell is the most a census can mint (rule 25).

Usage:
    PYTHONPATH=.:src python scripts/mechanism_matrix_gap_sweep.py            # all six
    PYTHONPATH=.:src python scripts/mechanism_matrix_gap_sweep.py --iso PJM
    PYTHONPATH=.:src python scripts/mechanism_matrix_gap_sweep.py --write-baseline

Writes ``results/calibration/_matrix_gap_sweep_<ISO>.json`` per ISO scanned, and
(with ``--write-baseline``) refreshes the committed ratchet baseline
``docs/codebase-site/data/mechanism-matrix-gaps.json`` that
``check_mechanism_matrix.py`` enforces — see that script's ratchet leg.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.lib import mech_matrix  # noqa: E402  (after sys.path insert)

# The BASE file of the sharded store (2026-08-11); per-ISO cells/ev live in
# docs/codebase-site/data/mechanism-matrix/<ISO>.js and are read through
# scripts.lib.mech_matrix.
MATRIX = REPO / "docs/codebase-site/data/mechanism-matrix.js"
KEEPER_SHARD_DIR = REPO / "frontend/data/backcast/keepers"
CALIB_DIR = REPO / "results/calibration"
REGISTRY = REPO / "frontend/data/backcast/registry"
BASELINE = REPO / "docs/codebase-site/data/mechanism-matrix-gaps.json"

# Matrix cell order (the `isos[]` array of mechanism-matrix.js).
ISO_INDEX = {"ERCOT": 0, "CAISO": 1, "PJM": 2, "MISO": 3, "NYISO": 4, "NEISO": 5}

# Each ISO's own `ScenarioConfig` field stems. Beyond the ISO name itself these
# are the REGULATOR prefixes whose fields are that ISO's exclusively — NYSDEC
# rules bind only New York units, so `nysdec_*` is a NYISO field just as much as
# `nyiso_*` is. Stems are matched as `<stem>_`, never as a bare substring, so
# `carbon_price` is never mistaken for a CARB field. SINGLE-SOURCED in
# scripts/lib/mech_matrix.py since y20: this sweep WRITES the baselines and
# check_mechanism_matrix.py ENFORCES them, and the two carried separate copies.
ISO_STEMS: dict[str, tuple[str, ...]] = mech_matrix.ISO_FIELD_STEMS

# Fields the SHARED census must not count, each with the reason it is a false
# positive rather than a gap. Keep this list SHORT and every entry justified:
# it is an exemption from a rule-28(c) duty, so an unjustified entry is exactly
# the off-registry channel rule 24 [R-REGISTRY] exists to close. The admissible
# shape is a field that the RUN'S IDENTITY sets rather than a mechanism CHOICE —
# something every bundle of its kind necessarily moves, so "non-default" carries
# no information about which mechanisms are armed.
#
# The census reports these separately rather than dropping them silently, so an
# exemption stays visible and arguable instead of becoming invisible again.
SHARED_CENSUS_EXCLUSIONS: dict[str, str] = {
    "weather_year": (
        "run identity, not a mechanism: a backcast pins the weather year to the "
        "solve year by construction (ScenarioConfig.mode='backcast'), so every "
        "multi-year bundle necessarily records a non-default value for two of "
        "its three years. Nothing is armed and nothing is tunable — the pinning "
        "IS the backcast, and it is already governed by rule 13 [R-MEASURED] "
        "and the mode field rather than by a matrix cell."
    ),
}


def scenario_defaults() -> dict[str, object]:
    """Shipped ``ScenarioConfig`` defaults, from the live class (not a parse)."""
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
    """Every matrix row as ``{id, cells, blob}`` — blob is the row's text.

    Sharded store (2026-08-11): the row's mechanism-level source chunk comes
    from the BASE file, the six-char ``cells`` string is reassembled from the
    per-ISO shards (``scripts.lib.mech_matrix.load_merged``), and ``blob``
    appends the shards' per-ISO ev/note text for the row so a field named only
    in an ISO's citation still counts as mentioned — the same reach the old
    monolith blob had. The ``note:``-split "own_row" head in :func:`coverage`
    keeps seeing only the base chunk's pre-note region, as before.
    """
    src = MATRIX.read_text()
    chunks = re.split(r'\n\s*\{\s*id:\s*"', src)[1:]
    base_blobs = {ch.split('"', 1)[0]: ch.split('"', 1)[1] for ch in chunks}
    merged = mech_matrix.load_merged(REPO)
    rows = []
    for row in merged["rows"]:
        rid = row["id"]
        shard_bits = [str(v) for v in (row.get("ev") or {}).values()] + [
            str(v) for v in (row.get("iso_notes") or {}).values()
        ]
        rows.append(
            {
                "id": rid,
                "cells": row.get("cells"),
                "blob": "\n".join([base_blobs.get(rid, "")] + shard_bits),
            }
        )
    return rows


def run_configs(iso: str) -> dict[str, dict]:
    """Every bundle's ``ScenarioConfig`` for this ISO, keyed by bundle name.

    Selection is by the config's OWN ``iso`` field, not by the bundle's name
    prefix: bundle naming is a per-lane convention (``pjm134_…``) that some
    bundles do not follow, and both the flat
    (``results/calibration/<name>/``) and ISO-scoped
    (``results/calibration/<ISO>/<name>/``) layouts are in use.
    ``run_config.json`` wraps the config under ``scenario_config`` alongside
    provenance blocks (``git``, ``calibration_flags``, ``environment``); the
    census only cares about the config itself.
    """
    out: dict[str, dict] = {}
    for pattern in ("*/run_config.json", "*/*/run_config.json"):
        for cfg in sorted(CALIB_DIR.glob(pattern)):
            try:
                doc = json.loads(cfg.read_text())
            except Exception:  # noqa: BLE001 - a corrupt bundle must not stop the census
                continue
            sc = doc.get("scenario_config", doc)
            if str(sc.get("iso", "")).upper() != iso:
                continue
            out[cfg.parent.name] = sc
    return out


def keeper_config(iso: str, cfgs: dict[str, dict]) -> tuple[str, dict]:
    """The ISO's designated keeper id and the bundle config behind it."""
    shard = KEEPER_SHARD_DIR / f"{iso}.json"
    if not shard.exists():
        return "", {}
    keeper_id = json.loads(shard.read_text()).get("keeper", "")
    reg = REGISTRY / f"{keeper_id}.json"
    if reg.exists():
        bundle = json.loads(reg.read_text()).get("bundle", "")
        if bundle:
            return keeper_id, cfgs.get(Path(bundle).name, {})
    return keeper_id, {}


def _norm(v: object) -> object:
    """Normalise a config value for cross-source comparison (JSON vs python)."""
    if isinstance(v, tuple):
        return list(v)
    return v


def _stem_of(field: str, stems: tuple[str, ...]) -> str:
    """The field with its ISO prefix removed, or the field itself."""
    for s in stems:
        if field.startswith(f"{s}_"):
            return field[len(s) + 1 :]
    return field


def coverage(field: str, rows: list[dict], blob: str, stems: tuple[str, ...]) -> str:
    """How well the matrix covers a field — three materially different states.

    ``mention-anywhere`` is the CI checker's deliberate escape hatch (rule
    28(c)): a sub-scalar of an existing family belongs on the family's row, not
    its own. But a field mentioned ONLY inside an unrelated row's prose has no
    cell of its own, so no verdict is recorded for it anywhere — the same
    invisibility the 227-3 gap had, one level subtler. Distinguish:

    * ``own_row``    — the field has a row carrying its own cell + verdict.
    * ``prose_only`` — mentioned, but only inside some other row's text.
    * ``absent``     — not mentioned anywhere in the matrix.

    The matrix's own convention is that rows are **ISO-neutral mechanism
    families** and a per-ISO flag is that ISO's leg of the family (e.g.
    ``nyiso_gas_commitment_bridge`` is the NYISO leg of row
    ``gas_commitment_bridge``, whose ``def`` references it in the short form
    ``nyiso :2609``). So the STEM — the field with its ISO prefix removed — is
    what identifies the owning row, not the literal flag name. Matching
    literally would over-report gaps for correctly-registered legs.
    """
    stem = _stem_of(field, stems)
    for r in rows:
        if r["id"] in (field, stem):
            return "own_row"
        head = r["blob"].split("note:", 1)[0]
        if field in head or (stem and stem in head):
            return "own_row"
    return "prose_only" if field.lower() in blob else "absent"


def sweep_iso(iso: str, defaults: dict, rows: list[dict], blob: str) -> dict:
    """Run the census for one ISO and return its result document."""
    stems = ISO_STEMS[iso]
    idx = ISO_INDEX[iso]
    cfgs = run_configs(iso)
    keeper_id, keeper_cfg = keeper_config(iso, cfgs)

    def owners(field: str) -> list[dict]:
        """Matrix rows whose source text mentions this field."""
        return [
            {"row": r["id"], "cells": r["cells"], "cell": (r["cells"] or "??????")[idx]}
            for r in rows
            if field in r["blob"] or field == r["id"]
        ]

    family = sorted(f for f in defaults if any(f.startswith(f"{s}_") for s in stems))
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
                "coverage": coverage(f, rows, blob, stems),
                "owning_rows": own,
                "cells": sorted({o["cell"] for o in own}),
                "armed_in_bundles": sorted(
                    b for b, c in cfgs.items() if _norm(c.get(f)) not in (None, False)
                ),
            }
        )

    # live-but-invisible: non-default in a bundle of this ISO, absent from matrix
    live_invisible = []
    for f, dflt in defaults.items():
        if f.lower() in blob:
            continue
        movers = {
            b: _norm(c[f])
            for b, c in cfgs.items()
            if f in c and _norm(c[f]) != _norm(dflt)
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

    # THE SHARED-FIELD BLIND SPOT (nyiso-115). The `family` census above only
    # ever sees fields carrying an ISO's own stem, and the ratchet built on it
    # inherits that blindness — so a SHARED mechanism armed on a keeper with no
    # matrix row anywhere is invisible to both, which is the same 227-3 shape
    # one class wider. nyiso-114 closed NYISO's ISO-scoped column to 0/0/0 while
    # twelve shared fields sat armed on its keeper with zero matrix mention.
    #
    # Keyed on the ISO's DESIGNATED KEEPER rather than on "any bundle": a
    # keeper is the configuration the ISO is actually calibrated at, so a field
    # it arms with no cell is a mechanism shaping a published result that no
    # session can see. (`live_but_invisible` below stays the broader, noisier
    # any-bundle view and is reported, not ratcheted.)
    iso_scoped = tuple(s for ss in ISO_STEMS.values() for s in ss)
    shared_rows = []
    for f, dflt in sorted(defaults.items()):
        if any(f.startswith(f"{s}_") for s in iso_scoped):
            continue  # an ISO's own field — the `family` census owns it
        kv = keeper_cfg.get(f, "<absent>")
        if kv == "<absent>" or _norm(kv) == _norm(dflt):
            continue  # not armed on this keeper
        shared_rows.append(
            {
                "field": f,
                "default": _norm(dflt),
                "keeper_value": _norm(kv),
                "coverage": coverage(f, rows, blob, ()),
                "owning_rows": owners(f),
                "excluded": f in SHARED_CENSUS_EXCLUSIONS,
                "exclusion_reason": SHARED_CENSUS_EXCLUSIONS.get(f),
            }
        )
    shared_absent = [
        r["field"]
        for r in shared_rows
        if r["coverage"] == "absent" and not r["excluded"]
    ]
    shared_prose_only = [
        r["field"]
        for r in shared_rows
        if r["coverage"] == "prose_only" and not r["excluded"]
    ]

    # Two distinct rule-28(c) gaps: `absent` (the 227-3 shape — invisible
    # outright) and `prose_only` (named in some other row's note, so the CI
    # mention-anywhere gate passes, but NO cell records a verdict for it).
    absent = [r["field"] for r in family_rows if r["coverage"] == "absent"]
    prose_only = [r["field"] for r in family_rows if r["coverage"] == "prose_only"]
    armed_no_cell = [
        r["field"]
        for r in family_rows
        if r["coverage"] != "own_row" and r["keeper_arms_it"]
    ]
    return {
        "iso": iso,
        "keeper": keeper_id,
        "keeper_bundle_fields": len(keeper_cfg),
        "n_scenario_fields": len(defaults),
        "n_matrix_rows": len(rows),
        "n_bundles_scanned": len(cfgs),
        "family": family_rows,
        "family_matrix_gaps_absent": absent,
        "family_prose_only": prose_only,
        "armed_on_keeper_with_no_cell": armed_no_cell,
        "shared_armed_on_keeper": shared_rows,
        "shared_matrix_gaps_absent": shared_absent,
        "shared_prose_only": shared_prose_only,
        "shared_excluded": [r["field"] for r in shared_rows if r["excluded"]],
        "live_but_invisible": live_invisible,
    }


def absent_shared_census(
    defaults: dict[str, object], matrix_text: str
) -> tuple[list[str], list[str]]:
    """SHARED fields the matrix never mentions — the whole class, ISO-agnostic.

    The third and widest rule-28(c) census, and the one that closes the hole
    ``docs/handoffs/FINDING-scn-mxr-2026-09-06.md`` §1.1 diagnosed. The two
    censuses above each carry a qualifier that a slipped field can simply not
    satisfy: :func:`sweep_iso`'s ``family`` needs an ISO stem, and its
    ``shared_armed_on_keeper`` needs a designated BACKCAST keeper to arm the
    field — which a forecast-only field defaulting to ``None`` never can. A
    shared, keeper-unarmed field with no row therefore had no census at all, on
    either side of the merge. This one has no qualifier: every field that is not
    one ISO's own, by NAME.

    Returns ``(absent, disagreement)``. The census is taken over the UNION of
    the live dataclass's field names and the stdlib parse of the same source,
    because the CI checker can only run the parse — a union makes this baseline
    a superset of anything the checker can compute, so the checker can never be
    stricter than the sweep (the invariant nyiso-114 broke with ``\\b`` vs
    substring, pinned by tests/unit/config/test_mechanism_matrix_shared_ratchet).
    ``disagreement`` is the symmetric difference of the two field sets — empty
    at y20 (798 = 798) and reported loudly if it ever is not, because it would
    mean the parse has started missing real fields.

    ``SHARED_CENSUS_EXCLUSIONS`` is deliberately NOT applied here. Those are
    ARMING arguments ("non-default carries no information for this field"),
    which say nothing about whether a mechanism deserves a row; and an excluded
    field that is genuinely absent is simply baselined like any other, so
    honouring them would only make the two halves' predicates differ again.
    """
    live = set(defaults)
    parsed = mech_matrix.scenarioconfig_field_names(
        (REPO / "src/market_sim/config/scenarios.py").read_text(encoding="utf-8")
    )
    disagreement = sorted(live ^ parsed)
    return mech_matrix.absent_shared_fields(live | parsed, matrix_text), disagreement


def _report(res: dict) -> None:
    """Print one ISO's census."""
    iso = res["iso"]
    print(f"\n{'=' * 78}")
    print(
        f"{iso}: keeper {res['keeper'] or '<none>'} "
        f"({res['keeper_bundle_fields']} config fields), "
        f"{res['n_bundles_scanned']} bundles scanned"
    )
    print(f"{'=' * 78}")
    print(
        f"  family fields {len(res['family']):>4} | "
        f"ABSENT {len(res['family_matrix_gaps_absent']):>4} | "
        f"prose-only {len(res['family_prose_only']):>4} | "
        f"ARMED-NO-CELL {len(res['armed_on_keeper_with_no_cell']):>4} | "
        f"live-but-invisible {len(res['live_but_invisible']):>4}"
    )
    if res["armed_on_keeper_with_no_cell"]:
        print("  --- ARMED ON THE KEEPER WITH NO CELL ANYWHERE (the 227-3 shape) ---")
        for f in res["armed_on_keeper_with_no_cell"]:
            row = next(r for r in res["family"] if r["field"] == f)
            print(
                f"    {f:<46} = {str(row['keeper_value'])[:28]:<30} ({row['coverage']})"
            )
    if res["family_matrix_gaps_absent"]:
        print("  --- ABSENT from the matrix ---")
        for f in res["family_matrix_gaps_absent"]:
            row = next(r for r in res["family"] if r["field"] == f)
            print(
                f"    {f:<46} keeper={str(row['keeper_value'])[:20]:<22}"
                f"armed_in={len(row['armed_in_bundles'])}"
            )
    if res["shared_matrix_gaps_absent"] or res["shared_prose_only"]:
        print("  --- SHARED fields ARMED ON THE KEEPER with no matrix row ---")
        for f in res["shared_matrix_gaps_absent"] + res["shared_prose_only"]:
            row = next(r for r in res["shared_armed_on_keeper"] if r["field"] == f)
            print(
                f"    {f:<46} = {str(row['keeper_value'])[:28]:<30} ({row['coverage']})"
            )
    if res["shared_excluded"]:
        print(
            "  --- shared census EXCLUSIONS (declared false positives, "
            "SHARED_CENSUS_EXCLUSIONS) ---"
        )
        for f in res["shared_excluded"]:
            print(f"    {f}")
    if res["family_prose_only"]:
        print("  --- PROSE-ONLY (mentioned, but no cell of its own) ---")
        for f in res["family_prose_only"]:
            row = next(r for r in res["family"] if r["field"] == f)
            print(f"    {f:<46} rows={[o['row'] for o in row['owning_rows']][:3]}")
    if res["live_but_invisible"]:
        print(
            "  --- LIVE-BUT-INVISIBLE (non-default in a bundle, no matrix mention) ---"
        )
        for r in res["live_but_invisible"][:20]:
            print(
                f"    {r['field']:<46} dflt={str(r['default'])[:16]:<18}"
                f"keeper={str(r['keeper_value'])[:20]:<22}n={r['n_bundles_nondefault']}"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--iso",
        nargs="+",
        default=sorted(ISO_INDEX),
        choices=sorted(ISO_INDEX),
        help="ISOs to sweep (default: all six).",
    )
    ap.add_argument(
        "--write-baseline",
        action="store_true",
        help="refresh the committed ratchet baseline enforced by "
        "check_mechanism_matrix.py (docs/codebase-site/data/mechanism-matrix-gaps.json). "
        "The baseline may only SHRINK — closing a gap is what refreshes it.",
    )
    args = ap.parse_args()

    defaults = scenario_defaults()
    rows = matrix_rows()
    # Whole-store mention blob: base + every ISO shard (a field named only in
    # a shard's ev/note is still "mentioned in the matrix").
    matrix_text = "\n".join(
        p.read_text() for p in mech_matrix.all_matrix_paths(REPO) if p.is_file()
    )
    blob = matrix_text.lower()
    absent_shared, field_set_disagreement = absent_shared_census(defaults, matrix_text)
    print(f"ScenarioConfig fields : {len(defaults)}")
    print(f"matrix rows           : {len(rows)}")
    print(
        f"shared fields ABSENT  : {len(absent_shared)} "
        f"(no matrix mention anywhere — the absent_shared ratchet)"
    )
    if field_set_disagreement:
        print(
            "WARNING: the live ScenarioConfig and the stdlib parse disagree on "
            f"{len(field_set_disagreement)} field name(s): "
            f"{', '.join(field_set_disagreement[:8])}. The CI checker can only "
            "run the parse — investigate before trusting either census."
        )

    results = {}
    for iso in args.iso:
        res = sweep_iso(iso, defaults, rows, blob)
        results[iso] = res
        out = CALIB_DIR / f"_matrix_gap_sweep_{iso}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=2, default=str))
        _report(res)

    print(f"\n{'=' * 78}\nSUMMARY\n{'=' * 78}")
    print(
        f"{'ISO':<8}{'family':>8}{'absent':>9}{'prose':>8}{'armed-no-cell':>16}"
        f"{'shared-gap':>12}{'invisible':>12}"
    )
    for iso, res in results.items():
        print(
            f"{iso:<8}{len(res['family']):>8}{len(res['family_matrix_gaps_absent']):>9}"
            f"{len(res['family_prose_only']):>8}"
            f"{len(res['armed_on_keeper_with_no_cell']):>16}"
            f"{len(res['shared_matrix_gaps_absent']) + len(res['shared_prose_only']):>12}"
            f"{len(res['live_but_invisible']):>12}"
        )

    if args.write_baseline:
        if sorted(args.iso) != sorted(ISO_INDEX):
            raise SystemExit(
                "--write-baseline requires all six ISOs (a partial sweep would "
                "silently drop the un-swept ISOs' entries from the ratchet)"
            )
        prior = json.loads(BASELINE.read_text()) if BASELINE.exists() else {}
        prior_gaps = prior.get("absent", {})
        prior_shared = prior.get("shared_armed_on_keeper", {})
        prior_absent_shared = set(prior.get("absent_shared", ()))
        doc = {
            "_comment": (
                "Rule-28(c) ratchet baseline, enforced by "
                "scripts/check_mechanism_matrix.py. THREE blocks, because a "
                "mechanism can be invisible in three different ways. `absent` "
                "lists each ISO's <iso>_* ScenarioConfig fields with NO "
                "mention in mechanism-matrix.js. `shared_armed_on_keeper` "
                "lists the SHARED (non-ISO-prefixed) fields that an ISO's "
                "DESIGNATED KEEPER arms away from its shipped default while "
                "the matrix never mentions them — the nyiso-115 blind spot: "
                "the ISO-scoped ratchet cannot see these at all, so a shared "
                "mechanism shaping a published keeper had no cell anywhere. "
                "`absent_shared` (y20) is the same shared class with the "
                "keeper qualifier DROPPED — every shared field the matrix "
                "never mentions, armed or not: a forecast-only field that no "
                "backcast keeper can arm was invisible to all three of the "
                "older checks, on both sides of the merge "
                "(docs/handoffs/FINDING-scn-mxr-2026-09-06.md §1.1). It opens "
                "large because it is the first check ever to look at that "
                "class; the backlog is the owning desks' work and the ratchet "
                "only guarantees it never grows. CI FAILS if a field appears "
                "in any census that this file does not already allow, so all "
                "three lists can only SHRINK — a new mechanism must land with "
                "its matrix registration (rule 28(c)), and closing a legacy "
                "gap is what refreshes this file. Declared false positives "
                "live in the sweep's own SHARED_CENSUS_EXCLUSIONS, not here, "
                "so an exemption stays visible and arguable. Regenerate with "
                "scripts/mechanism_matrix_gap_sweep.py --write-baseline."
            ),
            "absent": {
                iso: sorted(results[iso]["family_matrix_gaps_absent"])
                for iso in sorted(ISO_INDEX)
            },
            # A RATCHET MUST NOT SHRINK BY ACCIDENT. This block is the only one
            # that needs a bundle on disk (the keeper's run_config.json), and
            # `data/` profiles mean a session can legitimately hold none of
            # them — `keeper_config` then returns {} and this ISO's census comes
            # out empty, which would silently FORGIVE whatever it had allowed.
            # The `--iso` guard below refuses a partial sweep for exactly this
            # reason; an unreadable keeper bundle is the same hazard arriving
            # through the checkout instead of the CLI, so the prior entry is
            # carried forward unchanged and the ISO is named in the report.
            "shared_armed_on_keeper": {
                iso: (
                    sorted(prior_shared.get(iso, []))
                    if not results[iso]["keeper_bundle_fields"]
                    else sorted(
                        results[iso]["shared_matrix_gaps_absent"]
                        + results[iso]["shared_prose_only"]
                    )
                )
                for iso in sorted(ISO_INDEX)
            },
            # NOT per-ISO: a shared field is shared. One flat list, taken over
            # the union of the live dataclass and the stdlib parse so the
            # stdlib-only checker can never be stricter than this writer.
            "absent_shared": absent_shared,
            # Declared false positives, written here so the CI checker — which
            # is stdlib-only and cannot import this module — reads the SAME
            # exclusions this sweep applied, instead of carrying a second copy
            # that could drift out of sync (the `\b`-vs-substring lesson).
            "shared_census_exclusions": SHARED_CENSUS_EXCLUSIONS,
        }
        BASELINE.write_text(json.dumps(doc, indent=2) + "\n")
        grew = {
            iso: sorted(
                (set(doc["absent"][iso]) - set(prior_gaps.get(iso, [])))
                | (
                    set(doc["shared_armed_on_keeper"][iso])
                    - set(prior_shared.get(iso, []))
                )
            )
            for iso in sorted(ISO_INDEX)
            if (set(doc["absent"][iso]) - set(prior_gaps.get(iso, [])))
            or (
                set(doc["shared_armed_on_keeper"][iso]) - set(prior_shared.get(iso, []))
            )
        }
        no_bundle = [
            i for i in sorted(ISO_INDEX) if not results[i]["keeper_bundle_fields"]
        ]
        print(f"\nwrote {BASELINE.relative_to(REPO)}")
        if no_bundle:
            print(
                "  NOTE: no keeper run_config.json on disk for "
                + ", ".join(no_bundle)
                + " — their shared-on-keeper entries were CARRIED FORWARD, not "
                "re-measured (hydrate that ISO's data profile to refresh them). "
                "The per-ISO _matrix_gap_sweep_<ISO>.json dumps are written from "
                "whatever bundles ARE present, so do not commit them from a "
                "partial checkout."
            )
        print(f"  {'ISO':<8}{'iso-scoped':>16}{'shared-on-keeper':>20}")
        for iso in sorted(ISO_INDEX):
            n_new, n_old = len(doc["absent"][iso]), len(prior_gaps.get(iso, []))
            s_new = len(doc["shared_armed_on_keeper"][iso])
            s_old = len(prior_shared.get(iso, []))
            mark = "  <-- GREW" if iso in grew else ""
            print(
                f"  {iso:<8}{f'{n_old} -> {n_new}':>16}"
                f"{f'{s_old} -> {s_new}':>20}{mark}"
            )
        # The shared block is ISO-agnostic, so it gets its own line and its own
        # growth check — the same shrink-only contract, one list.
        new_shared = sorted(set(absent_shared) - prior_absent_shared)
        print(
            f"  {'shared':<8}"
            f"{f'{len(prior_absent_shared)} -> {len(absent_shared)}':>36}"
            + ("  <-- GREW" if new_shared else "")
        )
        if grew or new_shared:
            if grew:
                print("\nWARNING: the ratchet GREW for " + ", ".join(grew))
            if new_shared:
                print(
                    "\nWARNING: the shared ratchet GREW by "
                    f"{len(new_shared)}: {', '.join(new_shared[:8])}"
                )
            print("Rule 28(c) says a new mechanism lands with its row in the SAME PR.")


if __name__ == "__main__":
    main()
