"""caiso-186 — P0-5 / G-SIXISO: byte-equivalence, scope, and the contradiction decomposition.

Four legs, all read-only, **no LP**:

* **BE-1** — ``cc_winter_capability_basis`` defaults ``False`` on a freshly-built config for
  all six ISOs, and each ISO's DEFAULT-CONFIG ``cache_key()`` is unchanged against the
  values measured at ``origin/main`` before the field landed. This is what the
  ``_CACHE_KEY_OPTIONAL_FIELDS`` + ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`` registration in
  the field's own commit buys (caiso-184 omitted it and needed an FFR-8A backfill).
* **BE-3** — with ``cc_nameplate_summer_derate=False`` the flag is a **no-op**: bin
  capacities and the availability matrix are identical armed vs unarmed. Proven on ERCOT
  and MISO, the two ISOs whose keepers do NOT arm the parent.
* **BE-5** — the sha256 ledger over every data artifact the mechanism reads, before and
  after, so rule 23 ``[R-FROZEN-DERIVE]`` is discharged by measurement (no derive was run
  and no data byte was written).
* **DECOMP** — the arithmetic behind each G-NOCONTRA violation: per contradicted plant,
  ``capability = B x max_t availability``, the published basis B, the nameplate headroom the
  incumbent basis supplies, and the plant's own CEMS-demonstrated peak. This is what turns
  "the gate failed" into a named root cause.

Usage::

    python scripts/probes/_caiso186_be_proof.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")
OUT = REPO / "results" / "calibration" / "_caiso186_be_proof.json"
SIZING = REPO / "results" / "calibration" / "_caiso186_seasonal_capability.json"
# Default-config cache keys measured at origin/main (e9f99e66) BEFORE the field
# landed, so BE-1 is a comparison against a recorded baseline, not a self-check.
BASELINE_DEFAULT_KEYS = {
    "ERCOT": "603c2498bf71d21d",
    "CAISO": "51b2892ed6f0d742",
    "PJM": "5cfabdff9bfd6de6",
    "MISO": "ea1c7983d5c54ec4",
    "NYISO": "1462c74e6775a24b",
    "NEISO": "62923af03d1c9bac",
}


def _sha(path: Path) -> str | None:
    """sha256 of a file, or ``None`` when it is absent."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _be1() -> dict:
    """Default-off on every ISO, and every ISO's default cache key unmoved."""
    from market_sim.config.scenarios import ScenarioConfig

    rows = {}
    for iso in ISOS:
        cfg = ScenarioConfig(iso=iso)
        rows[iso] = {
            "default_value": bool(cfg.cc_winter_capability_basis),
            "default_cache_key": cfg.cache_key(),
            "baseline_cache_key": BASELINE_DEFAULT_KEYS[iso],
            "key_unmoved": cfg.cache_key() == BASELINE_DEFAULT_KEYS[iso],
        }
    return {
        "rows": rows,
        "pass": all(
            not r["default_value"] and r["key_unmoved"] for r in rows.values()
        ),
    }


def _be3(iso: str) -> dict:
    """With the PARENT flag off, arming this flag changes nothing."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet.arrays import generators_to_fleet_arrays
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    iso_cfg = get_iso_config(iso)
    zone_names = [z.name for z in iso_cfg.zones]
    caps, avails = [], []
    for arm in (False, True):
        cfg = ScenarioConfig(
            iso=iso,
            mode="backcast",
            weather_year=2024,
            cc_nameplate_summer_derate=False,
            cc_winter_capability_basis=arm,
        )
        bins = load_or_synthesize_bins(cfg, iso, iso_cfg, [])
        gens, _ = bins_to_fleet(bins, zone_names, cfg)
        fa = generators_to_fleet_arrays(
            gens, zone_names, hours=8760, iso=iso, config=cfg, year=2024
        )
        caps.append(np.asarray(bins["capacity_mw"], dtype=float))
        avails.append(np.asarray(fa.availability, dtype=float))
    return {
        "iso": iso,
        "bins": int(caps[0].size),
        "capacity_identical": bool(np.array_equal(caps[0], caps[1])),
        "availability_identical": bool(np.array_equal(avails[0], avails[1])),
        "max_abs_availability_delta": float(np.abs(avails[0] - avails[1]).max()),
    }


def _decomp() -> dict:
    """The arithmetic behind every G-NOCONTRA violation the sizing probe found."""
    if not SIZING.exists():
        return {"available": False}
    d = json.loads(SIZING.read_text())
    rows = {r["plant_code"]: r for r in d["rows"]}
    items = d["g_nocontra_new"] + d["g_nocontra_deepened"]
    out = []
    seen = set()
    for it in items:
        key = (it["plant_code"], it["season"])
        if key in seen:
            continue
        seen.add(key)
        r = rows[it["plant_code"]]
        b = r["published_basis_B_mw"]
        npl = r["eia860_nameplate_mw"]
        cems = it["cems_p999_mw"]
        arm = it["arm_max_mw"]
        keep = it["keeper_max_mw"]
        out.append(
            {
                "plant_code": it["plant_code"],
                "season": it["season"],
                "eia860_nameplate_mw": npl,
                "eia860_net_summer_mw": r["eia860_net_summer_mw"],
                "eia860_winter_mw": r["eia860_winter_mw"],
                "published_basis_B_mw": b,
                "cems_p999_mw": cems,
                # Does the plant BEAT its own published seasonal rating?
                "cems_over_published_basis": round(cems / b, 4) if b else None,
                "keeper_max_mw": keep,
                "arm_max_mw": arm,
                "arm_over_cems": round(arm / cems, 4) if cems else None,
                # The implied peak availability each arm reaches: capability / pmax.
                "arm_implied_max_availability": round(arm / b, 4) if b else None,
                "keeper_implied_max_availability": (
                    round(keep / npl, 4) if npl else None
                ),
                # The headroom the INCUMBENT nameplate basis supplies over the
                # published rating — the buffer that absorbs the statistical
                # forced-outage derate on the keeper.
                "nameplate_headroom_over_basis": round(npl / b, 4) if b else None,
            }
        )
    return {"available": True, "violations": out}


def main() -> None:
    """Score BE-1 / BE-3 / BE-5 and decompose the G-NOCONTRA violations."""
    from market_sim.config.paths import EIA_860_DIR, cc_capacity_reconcile_path

    ledger_paths = {
        "eia860_generator_operable.parquet": EIA_860_DIR
        / "eia860_generator_operable.parquet",
        **{
            f"cc_capacity_reconcile_{iso}.csv": Path(cc_capacity_reconcile_path(iso))
            for iso in ISOS
        },
    }
    out = {
        "be1_default_off_and_keys_unmoved": _be1(),
        "be3_parent_off_noop": [_be3("ERCOT"), _be3("MISO")],
        "be5_data_sha256": {
            k: _sha(v) for k, v in sorted(ledger_paths.items())
        },
        "decomposition": _decomp(),
    }
    out["be3_pass"] = all(
        r["capacity_identical"] and r["availability_identical"]
        for r in out["be3_parent_off_noop"]
    )
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
