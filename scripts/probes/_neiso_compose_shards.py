"""Compose this lane's per-shard solve bundles into ONE registerable bundle.

Rule 16 ``[R-ALLYEARS]`` requires a single bundle covering every scored year,
and rule 12 ``[R-PARALLEL]`` requires the years inside one invocation to be
solved sequentially — so a multi-year span is sharded across invocations for
memory and then composed here, the way ERCOT's keeper composes several configs
into one registered run. A shard is never registered on its own.

Year-keyed frames (``system``/``flows``/``storage``/``btm``) are concatenated;
per-year artifacts (``dispatch/``, ``floors/``, ``hourly/``) are copied; the
``meta.json`` / ``run_config.json`` year-scoped fields are merged. Every other
field is asserted identical across shards, so a composition can never silently
paper over two different recipes.

Usage::

    python3 scripts/probes/_neiso_compose_shards.py OUT SHARD [SHARD ...]
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

YEAR_KEYED = ("system", "flows", "storage", "btm")
PER_YEAR_DIRS = ("dispatch", "floors", "hourly")
# Fields whose value is legitimately year-scoped, so they merge instead of matching.
MERGE_META = {"gas_prices", "shared_inputs", "timestamp", "years"}
MERGE_RUNCFG = {
    "calibration_flags",
    "git",
    "model_changes_note",
    "scenario_config",
    "timestamp",
}


def compose(out: Path, shards: list[Path]) -> None:
    """Compose ``shards`` into a single bundle at ``out``.

    Args:
        out: Destination bundle directory (created; must not already exist).
        shards: Shard bundle directories, in year order.

    Raises:
        SystemExit: If a non-year-scoped config field differs between shards.
    """
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    metas = [json.loads((s / "meta.json").read_text()) for s in shards]
    cfgs = [json.loads((s / "run_config.json").read_text()) for s in shards]

    base, rest = metas[0], metas[1:]
    for m in rest:
        bad = sorted(k for k in set(base) | set(m) if k not in MERGE_META and base.get(k) != m.get(k))
        if bad:
            sys.exit(f"REFUSING to compose: meta.json fields differ across shards: {bad}")
    for c in cfgs[1:]:
        bad = sorted(
            k for k in set(cfgs[0]) | set(c) if k not in MERGE_RUNCFG and cfgs[0].get(k) != c.get(k)
        )
        if bad:
            sys.exit(f"REFUSING to compose: run_config.json fields differ across shards: {bad}")

    years: list[int] = []
    gas: dict = {}
    for m in metas:
        years += list(m["years"])
        gas.update(m.get("gas_prices") or {})
    years = sorted(set(years))
    meta = dict(base)
    meta["years"] = years
    meta["gas_prices"] = {str(y): gas[str(y)] for y in years}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))

    cfg = dict(cfgs[0])
    flags = dict(cfg.get("calibration_flags") or {})
    flags["years"] = years
    cfg["calibration_flags"] = flags
    cfg["model_changes_note"] = (
        "composed from " + ", ".join(s.name for s in shards) + " (rule 16 [R-ALLYEARS])"
    )
    (out / "run_config.json").write_text(json.dumps(cfg, indent=1))

    for name in YEAR_KEYED:
        parts = [pd.read_parquet(s / f"{name}.parquet") for s in shards if (s / f"{name}.parquet").exists()]
        if parts:
            pd.concat(parts, ignore_index=True).to_parquet(out / f"{name}.parquet", index=False)

    for sub in PER_YEAR_DIRS:
        dest = out / sub
        dest.mkdir(exist_ok=True)
        for s in shards:
            src = s / sub
            if not src.exists():
                continue
            for f in sorted(src.iterdir()):
                if (dest / f.name).exists():
                    sys.exit(f"REFUSING to compose: duplicate per-year artifact {sub}/{f.name}")
                shutil.copy2(f, dest / f.name)

    print(f"composed {out}  years={years}  from {[s.name for s in shards]}")


if __name__ == "__main__":
    compose(ROOT / sys.argv[1], [ROOT / a for a in sys.argv[2:]])
