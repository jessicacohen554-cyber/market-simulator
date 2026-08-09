"""caiso-185 — what arming ``cc_capacity_reconcile`` ACTUALLY does, through the shipped path.

Converts the analytic composition argument of ``_caiso185_seasonal_stack.py`` into a
MEASURED one: the CAISO bin frame and fleet arrays are built twice with the shipped
code (``load_or_synthesize_bins`` -> ``bins_to_fleet`` -> ``generators_to_fleet_arrays``),
identical in every respect except ``ScenarioConfig.cc_capacity_reconcile``, and the
per-plant **effective seasonal capability** ``max_t (pmax x availability)`` is read off
each side. Nothing is asserted about how the derate composes — it is observed.

The ScenarioConfig is rebuilt from the INCUMBENT KEEPER's own recipe
(``replay_keeper.build_kwargs`` over ``results/calibration/caiso184_c1_lpbasis/meta.json``),
never a remembered flag list, so the off arm is the keeper's own fleet.

Discharges, in one pass:

* **G-XGROUP** (PRECHECK §4) — ``_reconcile_cc_capacity`` zips over ``bins["Plant_Code"]``
  with NO group filter, so a plant carrying a non-CC bin alongside its CC block would have
  that bin reconciled too. Bar: **no non-CC bin may change capacity.**
* **H-GUARD** (PRECHECK §4) — the composition with the always-on merchant-CC
  summer-capacity clip, reported as the live bin capacity before and after.
* **THE SEASONAL-STACK CONTRADICTION** (discovered in P0, NOT pre-registered) — summer
  and off-summer effective capability, armed vs unarmed, against the plant's own
  CEMS-demonstrated seasonal peaks from ``_caiso185_seasonal_stack.json``.

NO LP IS SOLVED. Usage::

    python scripts/probes/_caiso185_arm_capability.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ISO = "CAISO"
YEAR = 2024
KEEPER = REPO / "results" / "calibration" / "caiso184_c1_lpbasis"
STACK = REPO / "results" / "calibration" / "_caiso185_seasonal_stack.json"
OUT = REPO / "results" / "calibration" / "_caiso185_arm_capability.json"


def _config(arm: bool):
    """Build the incumbent keeper's ScenarioConfig with one field overridden.

    Read from the keeper bundle's OWN committed ``run_config.json``
    ``scenario_config`` block — the persisted config the keeper solved on, which
    round-trips into ``ScenarioConfig`` with zero unmapped keys — never a
    remembered CLI string (rule: recipes are reconstructed from the bundle).
    """
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    sc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    unmapped = [k for k in sc if k not in fields]
    assert not unmapped, f"run_config carries unmapped keys: {unmapped}"
    kw = {k: v for k, v in sc.items() if k in fields}
    kw["cc_capacity_reconcile"] = arm
    return ScenarioConfig(**kw)


def _bins_and_fleet(cfg):
    """Return ``(bins, generators, fleet_arrays)`` for a config, shipped path only."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.arrays import generators_to_fleet_arrays
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    iso_cfg = get_iso_config(ISO)
    bins = load_or_synthesize_bins(cfg, ISO, iso_cfg, [])
    zone_names = [z.name for z in iso_cfg.zones]
    gens, _ = bins_to_fleet(bins, zone_names, cfg)
    fa = generators_to_fleet_arrays(
        gens, zone_names, hours=8760, iso=ISO, config=cfg, year=YEAR
    )
    return bins, gens, fa


def _seasonal_capability(gens, fa) -> dict[tuple[int, str], dict[str, float]]:
    """Per (plant, group): effective summer / off-summer capability in MW.

    ``pmax x availability`` summed over the plant's tranches, then the maximum
    over the hours of each season — i.e. the most the LP could ever dispatch
    from that plant in that season.
    """
    from market_sim.data.fleet.arrays import _SUMMER_MONTHS

    clock = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h")
    summer = np.isin(clock.month.to_numpy(), list(_SUMMER_MONTHS))
    eff = fa.pmax[:, None] * fa.availability
    out: dict[tuple[int, str], dict[str, float]] = {}
    acc: dict[tuple[int, str], np.ndarray] = {}
    for i, g in enumerate(gens):
        key = (int(g.plant_code), str(g.plant_group))
        a = acc.get(key)
        acc[key] = eff[i] if a is None else a + eff[i]
    for key, arr in acc.items():
        out[key] = {
            "pmax_sum_mw": float(arr.max()),
            "summer_capability_mw": float(arr[summer].max()),
            "offsummer_capability_mw": float(arr[~summer].max()),
        }
    return out


def main() -> None:
    """Build both arms, diff every bin, and score G-XGROUP + the seasonal stack."""
    off_cfg, on_cfg = _config(False), _config(True)
    assert off_cfg.cc_capacity_reconcile is False
    assert on_cfg.cc_capacity_reconcile is True
    print(f"off key={off_cfg.cache_key()}  on key={on_cfg.cache_key()}")

    bins_off, gens_off, fa_off = _bins_and_fleet(off_cfg)
    bins_on, gens_on, fa_on = _bins_and_fleet(on_cfg)

    key_cols = ["Plant_Code", "Plant_Group"]
    a = bins_off.set_index(key_cols)["capacity_mw"]
    b = bins_on.set_index(key_cols)["capacity_mw"]
    assert list(a.index) == list(b.index), "bin membership moved — not a capacity-only delta"
    moved = [
        {
            "plant_code": int(k[0]),
            "plant_group": str(k[1]),
            "capacity_off_mw": round(float(a.loc[k]), 3),
            "capacity_on_mw": round(float(b.loc[k]), 3),
            "delta_mw": round(float(b.loc[k]) - float(a.loc[k]), 3),
        }
        for k in a.index
        if abs(float(b.loc[k]) - float(a.loc[k])) > 1e-6
    ]
    noncc_moved = [m for m in moved if not m["plant_group"].startswith("CC")]

    cap_off = _seasonal_capability(gens_off, fa_off)
    cap_on = _seasonal_capability(gens_on, fa_on)
    stack = {int(r["plant_code"]): r for r in json.loads(STACK.read_text())["rows"]}

    rows: list[dict] = []
    for m in moved:
        key = (m["plant_code"], m["plant_group"])
        o, n = cap_off.get(key, {}), cap_on.get(key, {})
        s = stack.get(m["plant_code"], {})
        rec = {
            **m,
            "mode": s.get("mode"),
            "plant_name": s.get("plant_name"),
            "summer_capability_off_mw": round(o.get("summer_capability_mw", 0.0), 1),
            "summer_capability_on_mw": round(n.get("summer_capability_mw", 0.0), 1),
            "offsummer_capability_off_mw": round(
                o.get("offsummer_capability_mw", 0.0), 1
            ),
            "offsummer_capability_on_mw": round(
                n.get("offsummer_capability_mw", 0.0), 1
            ),
            "cems_summer_p999_mw": s.get("cems_summer_p999_mw"),
            "cems_offsummer_p999_mw": s.get("cems_offsummer_p999_mw"),
        }
        sp = rec["cems_summer_p999_mw"]
        if sp:
            rec["summer_on_over_cems"] = round(rec["summer_capability_on_mw"] / sp, 4)
            rec["summer_off_over_cems"] = round(rec["summer_capability_off_mw"] / sp, 4)
            # A model asserting a plant cannot reach an output the CEMS record
            # shows it produced is a MEASURED CONTRADICTION (rules 13 / 14).
            rec["summer_contradiction_on"] = bool(
                rec["summer_capability_on_mw"] < sp * 0.99
            )
            rec["summer_contradiction_off"] = bool(
                rec["summer_capability_off_mw"] < sp * 0.99
            )
        op = rec["cems_offsummer_p999_mw"]
        if op:
            rec["offsummer_on_over_cems"] = round(
                rec["offsummer_capability_on_mw"] / op, 4
            )
            rec["offsummer_off_over_cems"] = round(
                rec["offsummer_capability_off_mw"] / op, 4
            )
        rows.append(rec)

    out = {
        "iso": ISO,
        "year": YEAR,
        "keeper": KEEPER.name,
        "cache_key_off": off_cfg.cache_key(),
        "cache_key_on": on_cfg.cache_key(),
        "bins_total": int(len(a)),
        "bins_moved": len(moved),
        "net_capacity_delta_mw": round(sum(m["delta_mw"] for m in moved), 1),
        "g_xgroup_noncc_bins_moved": noncc_moved,
        "g_xgroup_pass": len(noncc_moved) == 0,
        "rows": rows,
        "summer_contradictions_on": [
            r["plant_code"] for r in rows if r.get("summer_contradiction_on")
        ],
        "summer_contradictions_off": [
            r["plant_code"] for r in rows if r.get("summer_contradiction_off")
        ],
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
