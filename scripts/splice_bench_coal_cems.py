"""Splice the CEMS-net coal total into every committed bench part (G-21b).

Adds ``e930["coal_cems"]`` — the CAMPD/CEMS coal-family net generation (TWh,
gross×parasitic-factor net map, ISO-scoped plant ids, model coal fleet-group
membership) — to ``frontend/data/backcast/bench/<ISO>/<year>.json.gz``. This is
the measured split anchor ``calibration_verdict._fallback_coal_anchor`` uses so
the C2 preliminary-vintage family fallback stops gating the raw EIA-930
per-fuel cell, whose BA-reported gas/coal attribution disagrees with CEMS by
−17..−21 TWh/yr (MISO, 930 low) and +7..+11 (PJM, 930 high) on the complete
vintages (reproduction: ``scripts/probes/_g21_cross_iso_reconcile.py``).

The construction is byte-identical to that probe's ``campd_coal`` column:
``run_calibration_full._campd_hourly_frame(year, iso, parasitic_factors)``
summed per plant, filtered to the ISO's plant ids whose model fleet group
starts with ``COAL``. Every other bench field is left untouched and the write
reuses the deterministic gzip (compresslevel=9, mtime=0) of
``render_backcast._write_bench_part``, so re-running is idempotent and
unchanged parts never show up as a git diff.

Usage: .venv/bin/python scripts/splice_bench_coal_cems.py [ISO ...]
       (default: every ISO with a bench dir)
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
for _p in (str(_REPO / "src"), str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_calibration_full as rcf  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402

BENCH_DIR = _REPO / "frontend" / "data" / "backcast" / "bench"


def _group_by_code(iso: str, year: int) -> dict[int, str]:
    """Plant→fleet-group map, mirroring the G-21 probe (ERCOT: CAMPD bin sheet)."""
    if iso == "ERCOT":
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import load_campd_bins

        b = load_campd_bins(ScenarioConfig().campd_bins_path)
        return dict(zip(b["Plant_Code"].astype(int), b["Plant_Group"]))
    return rcf._fleet_group_by_code(iso, get_iso_config(iso), year)


def cems_coal_twh(iso: str, year: int, factors: dict) -> float | None:
    """CEMS-net coal-family total (TWh) for (iso, year); None when no CAMPD."""
    plant_ids = rcf._iso_plant_ids(iso)
    gbc = _group_by_code(iso, year)
    frame = rcf._campd_hourly_frame(year, iso, factors, 8760)
    if frame is None:
        return None
    per_plant = frame.groupby("plant_id")["net_mw"].sum() / 1e6
    return float(
        sum(
            float(t)
            for pid, t in per_plant.items()
            if pid in plant_ids and str(gbc.get(int(pid), "")).startswith("COAL")
        )
    )


def main(isos: list[str]) -> None:
    factors = rcf._parasitic_factor_map()
    for iso in isos:
        for path in sorted((BENCH_DIR / iso).glob("*.json.gz")):
            year = int(path.stem.split(".")[0])
            part = json.loads(gzip.decompress(path.read_bytes()))
            coal = cems_coal_twh(iso, year, factors)
            if coal is None:
                print(f"{iso} {year}: no CAMPD frame — part left untouched")
                continue
            e930 = part["bench"].setdefault("e930", {})
            old = e930.get("coal_cems")
            e930["coal_cems"] = round(coal, 3)
            path.write_bytes(
                gzip.compress(json.dumps(part).encode(), compresslevel=9, mtime=0)
            )
            print(f"{iso} {year}: coal_cems {old} -> {e930['coal_cems']} TWh")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args or sorted(p.name for p in BENCH_DIR.iterdir() if p.is_dir()))
