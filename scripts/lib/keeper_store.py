"""Per-ISO keeper store — sharded keeper registry for the backcast dashboard.

Why shards: keeper promotions used to rewrite one shared
``frontend/data/backcast/keepers.json`` (plus the monolithic ``status.js``),
so any two sessions promoting keepers for DIFFERENT ISOs at the same time
collided and forced rebases. Since 2026-07-19 each ISO owns its own lane:

    frontend/data/backcast/keepers/index.json   # {"isos": [display order]}
    frontend/data/backcast/keepers/<ISO>.json   # one lane per ISO:
        {"iso": "ERCOT", "keeper": "<run id>",
         "frontier": {...}?, "note": "..."?}

A promotion edits ONLY its ISO's shard (and that ISO's ``status/<ISO>.js``
part via ``scripts/build_status.py --iso <ISO>``) — commits from parallel
per-ISO sessions merge cleanly. The old monolith is retired (removed from
git, ignored); this module still parses one if present so historical
checkouts, in-flight branches and test fixtures that write the legacy file
keep working (``load_merged`` returns exactly the legacy shape either way).

Stdlib-only, importable as ``from scripts.lib import keeper_store`` (the
repo root is on ``sys.path`` in every scripts/ entry point) or runnable:

    python scripts/lib/keeper_store.py --list
    python scripts/lib/keeper_store.py --set MISO 2026-07-18-miso-75-manitoba-meritcap
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO_DEFAULT = Path(__file__).resolve().parents[2]

# Display order for dashboards (mirrors build_status.ISO_ORDER; index.json is
# the runtime source of truth — this is only the fallback). ``iso_list`` appends
# any shard not named here rather than dropping it, so an unlisted region still
# appears; the tuple only decides order. SOCO added 2026-09-16 (lane SOCO-34) as
# the ninth registered region — it has no shard until lane SOCO-40 registers its
# first keeper, so this is pre-wiring, not a claim that one exists. SPP and NWPP
# are still absent and fall through to the append tail; those are their own desks'
# gaps, routed by SOCO-34. This module is deliberately STDLIB-ONLY, so it cannot
# import ``SUPPORTED_ISOS`` — hence the hand-maintained mirror.
DEFAULT_ISO_ORDER = ("ERCOT", "PJM", "CAISO", "NYISO", "NEISO", "MISO", "SOCO")


def _data_dir(repo_root: Path | str | None) -> Path:
    root = Path(repo_root) if repo_root is not None else _REPO_DEFAULT
    return root / "frontend" / "data" / "backcast"


def keepers_dir(repo_root: Path | str | None = None) -> Path:
    """The sharded keeper directory (``keepers/``)."""
    return _data_dir(repo_root) / "keepers"


def legacy_file(repo_root: Path | str | None = None) -> Path:
    """The retired pre-2026-07-19 monolith path (fallback parse only)."""
    return _data_dir(repo_root) / "keepers.json"


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _legacy_spec(repo_root: Path | str | None) -> dict:
    return _load_json(legacy_file(repo_root)) or {}


def iso_list(repo_root: Path | str | None = None) -> list[str]:
    """ISOs in display order (index.json → shard files → legacy monolith)."""
    d = keepers_dir(repo_root)
    idx = _load_json(d / "index.json")
    if idx and idx.get("isos"):
        return [str(i).upper() for i in idx["isos"]]
    if d.is_dir():
        found = sorted(
            p.stem for p in d.glob("*.json") if p.stem != "index" and p.stem.isupper()
        )
        if found:
            ordered = [i for i in DEFAULT_ISO_ORDER if i in found]
            return ordered + [i for i in found if i not in ordered]
    spec = _legacy_spec(repo_root)
    found = [k for k, v in spec.items() if k.isupper() and isinstance(v, str)]
    ordered = [i for i in DEFAULT_ISO_ORDER if i in found]
    return ordered + [i for i in found if i not in ordered]


def load_shard(iso: str, repo_root: Path | str | None = None) -> dict | None:
    """One ISO's keeper record (shard first, legacy monolith as fallback)."""
    iso = iso.upper()
    shard = _load_json(keepers_dir(repo_root) / f"{iso}.json")
    if shard is not None:
        return shard
    spec = _legacy_spec(repo_root)
    if isinstance(spec.get(iso), str):
        rec: dict = {"iso": iso, "keeper": spec[iso]}
        if iso in (spec.get("frontier") or {}):
            rec["frontier"] = spec["frontier"][iso]
        return rec
    return None


def keeper_ids(repo_root: Path | str | None = None) -> dict[str, str]:
    """``{ISO: keeper run id}`` for every ISO with a designated keeper."""
    out: dict[str, str] = {}
    for iso in iso_list(repo_root):
        rec = load_shard(iso, repo_root)
        if rec and isinstance(rec.get("keeper"), str) and rec["keeper"]:
            out[iso] = rec["keeper"]
    return out


def _has_shards(repo_root: Path | str | None) -> bool:
    d = keepers_dir(repo_root)
    return d.is_dir() and any(
        p.stem.isupper() for p in d.glob("*.json") if p.stem != "index"
    )


def keeper_list(repo_root: Path | str | None = None) -> list[str]:
    """Keeper run ids in ISO display order (the legacy ``keepers`` array).

    Legacy fallback honors the monolith's own ``keepers`` list verbatim when
    present — a pre-shard file (or test fixture) may carry ids without the
    per-ISO convenience keys.
    """
    if _has_shards(repo_root):
        return list(keeper_ids(repo_root).values())
    spec = _legacy_spec(repo_root)
    if spec.get("keepers"):
        return [r for r in spec["keepers"] if isinstance(r, str)]
    return list(keeper_ids(repo_root).values())


def frontier_map(repo_root: Path | str | None = None) -> dict:
    """``{ISO: frontier block}`` for shards that carry one (legacy shape)."""
    out: dict = {}
    for iso in iso_list(repo_root):
        rec = load_shard(iso, repo_root)
        if rec and rec.get("frontier"):
            out[iso] = rec["frontier"]
    return out


def load_merged(repo_root: Path | str | None = None) -> dict:
    """The full keeper spec in the LEGACY monolith shape.

    ``{<ISO>: <run id>, ..., "keepers": [ids...], "frontier": {ISO: {...}}}``
    — drop-in for every consumer that used to ``json.loads(keepers.json)``.
    """
    ids = keeper_ids(repo_root)
    merged: dict = dict(ids)
    merged["keepers"] = keeper_list(repo_root)
    fr = frontier_map(repo_root)
    if fr:
        merged["frontier"] = fr
    return merged


def write_keeper(
    iso: str,
    run_id: str,
    *,
    note: str | None = None,
    repo_root: Path | str | None = None,
) -> Path:
    """Set ``iso``'s keeper to ``run_id``, touching ONLY that ISO's shard.

    Preserves every other field already in the shard (``frontier`` blocks,
    notes). Returns the shard path. After a promotion, rebuild that ISO's
    status part (``python scripts/build_status.py --iso <ISO>``) and run the
    keeper-text auditor (``python scripts/audit_keepers.py --iso <ISO>``).
    """
    iso = iso.upper()
    d = keepers_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{iso}.json"
    rec = _load_json(path) or {"iso": iso}
    rec["iso"] = iso
    rec["keeper"] = run_id
    if note is not None:
        rec["note"] = note
    path.write_text(json.dumps(rec, indent=1, sort_keys=False) + "\n")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="print ISO → keeper map")
    ap.add_argument(
        "--set",
        nargs=2,
        metavar=("ISO", "RUN_ID"),
        help="set ISO's keeper (writes only keepers/<ISO>.json)",
    )
    ap.add_argument("--note", help="optional shard note to set with --set")
    args = ap.parse_args()
    if args.set:
        iso, rid = args.set
        path = write_keeper(iso, rid, note=args.note)
        print(f"wrote {path}")
        print(
            f"next: python scripts/build_status.py --iso {iso.upper()} && "
            f"python scripts/audit_keepers.py --iso {iso.upper()}"
        )
    if args.list or not args.set:
        for iso, rid in keeper_ids().items():
            print(f"{iso:6} {rid}")


if __name__ == "__main__":
    main()
