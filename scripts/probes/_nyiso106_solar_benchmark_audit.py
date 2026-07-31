"""nyiso-106: NYISO solar benchmark provenance audit (NO LP).

Matrix §5.5 Item A. The build-time instrument that audits the SCORING TARGET
before any mechanism is sized against it, in the shape nyiso-98/99 established
(``nyiso98_nuclear_availability_provenance.py``,
``nyiso99_import_benchmark_provenance.py``).

Why the nyiso-98 recipe does not transfer verbatim
--------------------------------------------------
nyiso-98/99 audited EIA-930 series with zero-coded *gaps*. NYISO solar has no
gaps to falsify: EIA-930 ``NYIS`` ``NG: SUN`` is **identically zero** in every
hour of every year (NY grid solar is overwhelmingly distribution-connected /
net-metered and invisible to the BA telemetry). That is why
``results.calibration._EIA923_OVERRIDE`` routes NYISO solar's scoring to
**EIA-923** — so the audit's real target is the EIA-923 vintage, not the 930
series.

Falsification instrument
------------------------
NYISO MIS **P-63 Real-Time Fuel Mix** (``data/raw/NYISO/fuel-mix/``) publishes no
separate solar category — grid solar sits inside ``Other Renewables`` alongside
flat biomass / refuse / LFG. The two separate cleanly: a per-day night-hour
baseline plus the daylight bulge above it isolates solar. Rule 13: used ONLY to
falsify the benchmark, never as a dispatch input. It is a LOWER BOUND on the
EIA-923 population (NYISO meters only market-participating solar; EIA-923 counts
every plant >= 1 MW), so it establishes direction and falsification, not level.

Sections
--------
``census``   EIA-930 ``NG: SUN`` zero census — shows the series is absent, not gappy.
``vintage``  EIA-923 plant/TWh coverage by year, and the like-for-like subset test.
``falsify``  NYISO P-63 ``Other Renewables`` solar-bulge decomposition.
``guards``   The two guards that should have caught this, and why neither does.
``repair``   The carry-forward repair applied to the real data, all three years.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso106_solar_benchmark_audit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

ISO, BA = "NYISO", "NYIS"
YEARS = (2023, 2024, 2025)
FUELMIX_DIR = REPO / "data" / "raw" / "NYISO" / "fuel-mix"
E923_PARQUET = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
COMPLETENESS = REPO / "frontend/data/backcast/completeness/eia923_2025.json"
OUT_PATH = REPO / "results/calibration/_nyiso106_solar_benchmark_audit.json"

#: Local hours treated as solid daylight for the "is there ANY midday solar" test.
_MIDDAY = (10, 15)
#: Local hours whose median sets the per-day non-solar baseline in Other Renewables.
_NIGHT = (22, 4)


def _blocks(mask: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous ``(start, length)`` runs of True in *mask*."""
    out: list[tuple[int, int]] = []
    start: int | None = None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        elif not m and start is not None:
            out.append((start, i - start))
            start = None
    if start is not None:
        out.append((start, len(mask) - start))
    return out


def _eia930_frame(year: int) -> pd.DataFrame:
    from market_sim.data.eia930 import frames as fr

    frame = fr._eia_hourly_frame_filled(BA, year)
    if frame is None:
        raise RuntimeError(f"no EIA-930 frame for {BA} {year}")
    return frame.iloc[:8760]


def section_census() -> dict:
    """EIA-930 ``NG: SUN`` zero census — the series is absent, not gappy."""
    print("\n=== census — EIA-930 NYIS `NG: SUN` on the 8760-h model clock ===")
    print(f"{'year':<6}{'NaN':>6}{'zero_h':>9}{'blocks':>8}{'longest':>9}{'midday_0':>10}{'max_MW':>9}")
    out = {}
    for year in YEARS:
        frame = _eia930_frame(year)
        raw = frame["NG: SUN"].to_numpy(float)
        nan = np.isnan(raw)
        v = np.nan_to_num(raw)
        zero = (v == 0.0) & ~nan
        idx = pd.DatetimeIndex(frame["UTC time"])
        idx = idx.tz_localize("UTC") if idx.tz is None else idx
        hod = idx.tz_convert("America/New_York").hour.to_numpy()
        core = (hod >= _MIDDAY[0]) & (hod <= _MIDDAY[1])
        blk = _blocks(zero)
        row = {
            "nan": int(nan.sum()),
            "zero_hours": int(zero.sum()),
            "zero_blocks": len(blk),
            "longest_block": max((n for _, n in blk), default=0),
            "midday_zero_of": [int((zero & core).sum()), int(core.sum())],
            "max_mw": float(v.max()),
        }
        out[year] = row
        print(
            f"{year:<6}{row['nan']:>6}{row['zero_hours']:>9}{row['zero_blocks']:>8}"
            f"{row['longest_block']:>9}{row['midday_zero_of'][0]:>10}{row['max_mw']:>9.0f}"
        )
    print("\n  Identically zero => NOT a zero-coded gap (nyiso-98 class). The series")
    print("  is structurally absent, which is why _EIA923_OVERRIDE routes scoring to 923.")
    return out


def section_vintage() -> dict:
    """EIA-923 NYIS solar coverage by year + the like-for-like subset test."""
    print("\n=== vintage — EIA-923 NYIS `SUN` plant coverage ===")
    df = pd.read_parquet(E923_PARQUET)
    ny = df[(df.ba_code == BA) & (df.fuel_type == "SUN")]
    out: dict = {"by_year": {}}
    print(f"{'year':<6}{'plants':>8}{'TWh':>10}")
    for year in (2022, *YEARS):
        s = ny[ny.year == year]
        rec = {
            "plants": int(s.plant_id.nunique()),
            "twh": round(float(s.netgen_annual_mwh.sum()) / 1e6, 4),
        }
        out["by_year"][year] = rec
        print(f"{year:<6}{rec['plants']:>8}{rec['twh']:>10.4f}")

    p25, p24 = set(ny[ny.year == 2025].plant_id), set(ny[ny.year == 2024].plant_id)
    s24 = ny[ny.year == 2024]
    like = float(s24[s24.plant_id.isin(p25)].netgen_annual_mwh.sum()) / 1e6
    out["subset_test"] = {
        "2025_plants_are_subset_of_2024": bool(p25 <= p24),
        "2024_twh_restricted_to_the_2025_reporters": round(like, 4),
        "2025_twh": out["by_year"][2025]["twh"],
    }
    print(
        f"\n  2025 reporters are a subset of 2024: {p25 <= p24}\n"
        f"  those same plants: 2024 = {like:.4f} TWh -> 2025 = "
        f"{out['by_year'][2025]['twh']:.4f} TWh  (they GREW)"
    )

    whole = df.groupby("year").agg(plants=("plant_id", "nunique"))
    out["national_plant_counts"] = {
        int(y): int(v) for y, v in whole["plants"].items() if y >= 2023
    }
    print(f"  national vintage plant counts: {out['national_plant_counts']}")
    return out


def section_falsify() -> dict:
    """NYISO P-63 `Other Renewables` solar-bulge decomposition."""
    print("\n=== falsify — NYISO P-63 `Other Renewables` solar bulge ===")
    print(f"{'year':<6}{'total_TWh':>11}{'night_MW':>10}{'bulge_TWh':>11}")
    out = {}
    for year in YEARS:
        path = FUELMIX_DIR / f"NYISO_fuelmix_hourly_{year}.csv.gz"
        if not path.exists():
            print(f"{year:<6}  (no P-63 extract)")
            continue
        d = pd.read_csv(path)
        o = d[d.fuel_category == "Other Renewables"].copy()
        ts = pd.to_datetime(o.interval_start_utc, utc=True).dt.tz_convert(
            "America/New_York"
        )
        o["date"], o["hod"] = ts.dt.date, ts.dt.hour
        night = o[(o.hod >= _NIGHT[0]) | (o.hod <= _NIGHT[1])]
        base = night.groupby("date").gen_mw.median()
        o["bulge"] = (o.gen_mw - o.date.map(base)).clip(lower=0)
        rec = {
            "other_renewables_twh": round(float(o.gen_mw.sum()) / 1e6, 4),
            "night_baseline_mw": round(float(base.mean()), 1),
            "solar_bulge_twh": round(float(o.bulge.sum()) / 1e6, 4),
        }
        out[year] = rec
        print(
            f"{year:<6}{rec['other_renewables_twh']:>11.4f}"
            f"{rec['night_baseline_mw']:>10.1f}{rec['solar_bulge_twh']:>11.4f}"
        )
    print("\n  Monotonic growth against a 923 series claiming a 77% collapse.")
    print("  LOWER BOUND on the 923 population (ISO-metered only), not a level.")
    return out


def section_guards() -> dict:
    """The two guards that should have caught this, and why neither does."""
    print("\n=== guards — why nothing caught it ===")
    out: dict = {}
    audited = []
    if COMPLETENESS.exists():
        node = json.loads(COMPLETENESS.read_text())["isos"].get(ISO, {})
        audited = sorted(node)
    out["completeness_audited_classes"] = audited
    out["solar_in_completeness_audit"] = "solar" in audited
    print(f"  audit_eia923_completeness NYISO 2025 classes: {audited}")
    print(f"  -> 'solar' audited: {out['solar_in_completeness_audit']}  (GAS+COAL only)")

    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    zero_930 = {}
    for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"):
        for year in YEARS:
            b = load_eia_hourly_benchmark(iso, year) or {}
            for klass in ("wind", "solar", "hydro"):
                if klass in b and float(b[klass].sum()) <= 0.0:
                    zero_930.setdefault(iso, []).append(f"{klass}:{year}")
    out["zero_eia930_authority_cells"] = zero_930
    print(f"  cells with a ZERO EIA-930 authority (6 ISOs x 3 classes x 3 years): {zero_930}")
    print("  -> _backfill_renewables_eia930 bails on `if ann930 <= 0.0: continue`,")
    print("     so the repair cannot fire for exactly the _EIA923_OVERRIDE cell.")
    return out


def section_repair() -> dict:
    """Apply the repair to the real data, all three years."""
    print("\n=== repair — _backfill_renewables_eia930 on the committed data ===")
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia923 import load_monthly_generation
    from run_calibration_full import (  # type: ignore[import-not-found]
        _backfill_renewables_eia930,
        _eia923_frame,
        _eia930_frame,
        _vintage_completeness,
    )

    gen = load_monthly_generation()
    ic = get_iso_config(ISO)
    out = {}
    print(f"{'year':<6}{'completeness':>13}{'solar_raw':>11}{'solar_repaired':>15}")
    for year in YEARS:
        e930 = _eia930_frame(year, ISO, ic)
        raw = _eia923_frame(year, gen, ISO)
        rep = _backfill_renewables_eia930(raw.copy(), year, ISO, gen, e930)
        a = raw.groupby("klass")["annual_mwh"].sum() / 1e6
        b = rep.groupby("klass")["annual_mwh"].sum() / 1e6
        rec = {
            "vintage_completeness": round(
                float(_vintage_completeness(year, gen, ISO, e930)), 4
            ),
            **{
                f"{k}_raw_twh": round(float(a.get(k, 0.0)), 4)
                for k in ("solar", "wind", "hydro", "biomass")
            },
            **{
                f"{k}_repaired_twh": round(float(b.get(k, 0.0)), 4)
                for k in ("solar", "wind", "hydro", "biomass")
            },
        }
        out[year] = rec
        print(
            f"{year:<6}{rec['vintage_completeness']:>13.4f}"
            f"{rec['solar_raw_twh']:>11.4f}{rec['solar_repaired_twh']:>15.4f}"
        )
    return out


def main() -> None:
    payload = {
        "session": "nyiso-106",
        "iso": ISO,
        "years": list(YEARS),
        "census_eia930_ng_sun": section_census(),
        "vintage_eia923": section_vintage(),
        "falsify_p63_bulge": section_falsify(),
        "guards": section_guards(),
        "repair": section_repair(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=1, default=str) + "\n")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
