"""neiso-119 phase 0 (a), zero LP: what the class-preserving union would re-derive.

Runs the committed ST_GAS and CHP heat-rate derives twice each into a scratch
directory — (1) unchanged (must reproduce the committed artifact), (2) with the
derive's ``union_fleet`` swapped for the class-preserving form neiso-118 landed
(``klass=`` — for CHP, preserving either topping-cycle class) — and prints the
row-level diff. Never writes a committed artifact.

Usage: uv run python docs/handoffs/neiso119/phase0_rederive_st_chp.py <scratch_dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))


def _run(mod, out: Path, patch, extra=()) -> pd.DataFrame:
    orig = mod.union_fleet
    if patch is not None:
        mod.union_fleet = patch
    try:
        sys.argv = ["x", "--iso", "NEISO", "--out", str(out), *extra]
        mod.main()
    finally:
        mod.union_fleet = orig
    return pd.read_csv(out)


def main() -> None:
    scratch = Path(sys.argv[1])
    scratch.mkdir(parents=True, exist_ok=True)
    from scripts.data import derive_campd_gas_st_heat_rates as st
    from scripts.data import derive_chp_power_only_heat_rates as chp
    from scripts.lib import heat_rate_years as hry

    def chp_union(fleets, klass=None):
        latest = {}
        for y in sorted(fleets):
            for g in fleets[y]:
                k = str(g.unit_id)
                p = latest.get(k)
                if (
                    p is not None
                    and p.plant_group in chp.TARGET_CLASSES
                    and g.plant_group not in chp.TARGET_CLASSES
                ):
                    continue
                latest[k] = g
        return list(latest.values())

    only = sys.argv[2:] or ["st", "chp"]
    for name, mod, patch, committed in (
        (
            "st",
            st,
            lambda f, klass=None: hry.union_fleet(f, klass=st.TARGET_CLASS),
            "campd_st_heat_rates_NEISO.csv",
        ),
        ("chp", chp, chp_union, "chp_power_only_heat_rates_NEISO.csv"),
    ):
        if name not in only:
            continue
        extra = ("--detail",) if name == "st" else ()
        base = _run(mod, scratch / f"{name}_base.csv", None, extra)
        arm = _run(mod, scratch / f"{name}_arm.csv", patch, extra)
        comm = pd.read_csv(REPO / "data/raw/_processed-legacy" / committed)
        print(
            f"== {name}: base reproduces committed: {base.equals(comm)} "
            f"(rows base {len(base)} committed {len(comm)} arm {len(arm)})"
        )
        key = [
            c
            for c in ("plant_code", "year", "plant_group", "klass")
            if c in base.columns
        ]
        m = base.merge(arm, on=key, how="outer", suffixes=("_b", "_a"), indicator=True)
        hr = "heat_rate"
        diff = m[
            (m["_merge"] != "both")
            | ((m[f"{hr}_b"] - m[f"{hr}_a"]).abs() > 1e-9)
            | (m.get("flag_b") != m.get("flag_a"))
        ]
        cols = key + [
            c
            for c in (
                f"{hr}_b",
                f"{hr}_a",
                "flag_b",
                "flag_a",
                "model_heat_rate_egrid_a",
                "model_heat_rate_egrid_b",
                "_merge",
            )
            if c in m.columns
        ]
        print(diff[cols].to_string())


if __name__ == "__main__":
    main()
