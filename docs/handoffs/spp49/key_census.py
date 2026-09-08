"""SPP-49 ex-ante cache-key census (zero LP): what the two repairs do to every committed key.

The two repairs land differently (PRECOMMIT-spp-49 §1):

* SEAM 1 — a REGISTERED ``ScenarioConfig`` gate, ``f923_gas_price_plausibility_screen``,
  default ON, declared through the (b'-1) route: frozen drop value ``"False"`` in
  ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS``, a ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS``
  entry, and a ``__post_init__`` coercion back to the frozen declaration wherever the
  seam is UNREACHABLE for the whole run — ``mode != "backcast"`` and not a hindcast, or
  ``gas_plant_monthly_fuel_pricing`` off — so a config the screen cannot touch keeps its
  key. A config the screen CAN touch resolves ``True``, no longer equals the drop value,
  ENTERS the hash and takes a new key: the designed re-key, never a same-key collision.

* SEAM 2 — a CONSTRUCTION (unconditional at the fleet seam, no field, no new surface
  value). It moves NO key by arithmetic; what it changes is recorded as a same-key
  invalidation scoped to the ISOs whose fleets carry a flagged plant (census.py).

This script hashes every committed ``run_config.json`` payload under (a) the live HEAD
rules, validated against the payload's own recorded ``cache_key`` exactly as
``scripts/lib/key_provenance`` does (both constructions), and (b) the post-edit rule for
seam 1 applied ARITHMETICALLY to the payload (the field inserted at the value the
coercion would resolve), so the ex-ante record (``scenarios.py`` untouched) and the
ex-post record (after the edit, ``--check-live``) are produced by one code path and must
agree. It reports total moves and OFF-TARGET moves (a move in a config the seam cannot
reach) and never collapses the two.

Usage:
    uv run python docs/handoffs/spp49/key_census.py --out docs/handoffs/spp49/key_census_pre.json
    uv run python docs/handoffs/spp49/key_census.py --check-live --out .../key_census_post.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib.key_provenance import (  # noqa: E402
    _committed_run_configs,
    head_key,
    load_exceptions,
)

FIELD = "f923_gas_price_plausibility_screen"
FROZEN_DROP_VALUE = False
POST_FLIP_DEFAULT = True


def reachable(sc: dict) -> bool:
    """The seam's own gate predicate with the year term dropped (plant_prices.py)."""
    mode_ok = sc.get("mode") == "backcast" or bool(sc.get("hindcast"))
    return mode_ok and bool(sc.get("gas_plant_monthly_fuel_pricing"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--check-live", action="store_true",
                    help="assert the live dataclass default is the post-flip value")
    a = ap.parse_args()
    if a.check_live:
        from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults
        live = getattr(ScenarioConfig(), FIELD, None)
        assert live == POST_FLIP_DEFAULT, f"live default {live!r} != {POST_FLIP_DEFAULT!r}"
        assert cache_key_drop_defaults().get(FIELD) == FROZEN_DROP_VALUE, "frozen drop value moved"
    exceptions = {e["path"] if isinstance(e, dict) else e for e in load_exceptions().get("exceptions", [])} \
        if isinstance(load_exceptions(), dict) else set()
    records = []
    for path in _committed_run_configs():
        rel = str(path.relative_to(REPO))
        payload = json.loads(path.read_text())
        sc = payload.get("scenario_config", payload)
        recorded = sc.get("cache_key") or payload.get("cache_key")
        base_decl = head_key(sc, surface=False)
        base_live = head_key(sc, surface=True)
        reproduces = recorded in (base_decl, base_live) if recorded else None
        # post-edit seam-1 rule: the field resolves to the coerced value
        post = dict(sc)
        explicit = FIELD in sc
        resolved = sc[FIELD] if explicit else POST_FLIP_DEFAULT
        if not reachable(sc):
            resolved = FROZEN_DROP_VALUE
        post[FIELD] = resolved
        # a live tree drops the field at the frozen value through the registry;
        # emulate that here so the ex-ante and ex-post arithmetic agree
        if post[FIELD] == FROZEN_DROP_VALUE:
            post.pop(FIELD)
        post_decl = head_key(post, surface=False)
        lane = "hindcast" if sc.get("hindcast") else sc.get("mode")
        records.append(dict(
            path=rel, iso=sc.get("iso"), lane=lane, recorded=recorded, reproduces=reproduces,
            reachable=reachable(sc), explicit=explicit, resolved=resolved,
            key_pre=base_decl, key_post=post_decl, moves=(post_decl != base_decl),
        ))
    n = len(records)
    validated = sum(1 for r in records if r["reproduces"])
    nokey = sum(1 for r in records if r["recorded"] is None)
    mism = [r["path"] for r in records if r["reproduces"] is False]
    moves = [r for r in records if r["moves"]]
    off_target = [r for r in moves if not r["reachable"]]
    by = Counter((r["iso"], r["lane"]) for r in moves)
    tot = Counter((r["iso"], r["lane"]) for r in records)
    print(f"{n} committed run configs: {validated} reproduce their recorded key, {nokey} carry no key, "
          f"{len(mism)} mismatch (the key-provenance exception census governs those)")
    print(f"seam-1 gate (default ON, coerced where unreachable): {len(moves)} keys move, "
          f"{len(off_target)} OFF-TARGET")
    for k in sorted(tot, key=str):
        print(f"  {k}: total {tot[k]}, moves {by.get(k, 0)}")
    for r in moves:
        print(f"  MOVE {r['iso']:5s} {r['lane']:9s} {r['path']}: {r['key_pre']} -> {r['key_post']}")
    print("seam-2 construction: 0 keys move by arithmetic (no field, no surface value changes)")
    if a.out:
        Path(a.out).write_text(json.dumps(dict(
            n=n, validated=validated, no_key=nokey, mismatches=mism,
            moves=len(moves), off_target=len(off_target),
            by_iso_lane={f"{k[0]}/{k[1]}": dict(total=tot[k], moves=by.get(k, 0)) for k in tot},
            records=records), indent=1))
    return 2 if off_target else 0


if __name__ == "__main__":
    sys.exit(main())
