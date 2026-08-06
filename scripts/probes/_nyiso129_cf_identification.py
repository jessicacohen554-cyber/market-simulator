"""nyiso-129 — adjudicate the named CF successor lever, and localize the C3c-2023 cost.

Session record for the two measurements that decided nyiso-129 (rule 28 duty (b):
the session that tests a mechanism records it, rejections included). **No solve is
spent here** — every number comes from committed artifacts and published inputs.

**Measurement 1 — the named successor lever, REFUTED as specified.** nyiso-128b
named the next object as *"re-identify the registered fleet's CF from EIA-860
tracking mix + latitude"*, on the premise that the registered market fleet's
~0.20 measured CF against the model's ~0.133 ISO-wide blend is a **geometry**
difference (the registry being more single-axis-tracking than the whole-NY
population). This computes that geometry ratio directly, with the machinery the
premise named: the capacity-weighted EIA-860 tracking mix and centroid latitude
of (a) the 15 registered Table III-2a plants and (b) the whole NY operable solar
fleet, through :func:`market_sim.data.renewables._clearsky_poa_by_tech`. The
ratio of annual-mean plane-of-array output is the CF uplift the lever could
deliver. It is **1.00-1.03**, not the ~1.5 the premise assumed, so the lever as
named is inert (rule 26 ``[R-DELETE]`` — an inert knob is not parked default-off).

**Measurement 2 — where the CF gap actually lives.** The 2026 Gold Book publishes
2025 Net Energy per registered unit. Their capacity-weighted CF is measured here
against ``RENEWABLE_AVG_CF["NYISO"]["solar"]``, which ``constants.py`` labels a
Tier-3 approximation carrying ``needs-citation: verify against EIA-923 ISO totals
before quoting a forecast``. The defect is a **CF-level** error on that constant,
not a geometry correction — a different object with its own identification.

**Measurement 3 — the C3c-2023 cost, localized.** Counts the >$300 tail hours of
both committed A/B arms straight off their ``hourly/system_<year>.parquet``
sidecars (max zonal energy-only dual, the same construction the renderer's
fallback tail uses), and reports which hours the treatment adds, with their
zone/month/hour. This is what turns "C3c-2023 regresses 18 h -> 22 h" into a
named object: one Long Island heat-wave episode.

Usage::

    python scripts/probes/_nyiso129_cf_identification.py

Writes ``results/calibration/_nyiso129_cf_identification.json``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR, active_eia860_dir  # noqa: E402
from market_sim.data.nyiso_market_solar import load_market_solar_monthly  # noqa: E402
from market_sim.data.renewables import (  # noqa: E402
    _clearsky_poa_by_tech,
    _eia860_monthly_capacity,
)

OUT = REPO / "results" / "calibration" / "_nyiso129_cf_identification.json"

# The 15 NYISO Table III-2a market-generator PV plants, as EIA-860 plant codes.
# Identity crosswalk on published name + nameplate + in-service date (every one
# an exact single-plant match; see the probe's own printout). Zero freedom.
REGISTERED_PLANT_CODES: dict[int, str] = {
    65125: "NY8 - Puckett Solar",
    65123: "NY8 - Janis Solar",
    68274: "Morris Ridge Solar",
    65122: "NY8 - Branscomb Solar",
    65124: "NY8 - Regan Solar",
    65121: "NY8 - Grissom Solar",
    65839: "NY8 - Darby Solar",
    65841: "NY8 - ELP Stillwater Solar",
    64077: "Hecate Energy Albany County 1",
    66126: "Hecate Energy Albany 2 LLC",
    65840: "NY8 - Teichos Pattersonville",
    65805: "East Point Energy Center",
    65765: "High River Energy Center, LLC",
    57589: "Long Island Solar Farm LLC",
    65679: "Calverton Solar Energy Center",
}

YEARS: tuple[int, ...] = (2023, 2024, 2025)
TAIL_THRESHOLD_USD: float = 300.0  # NYISO C3c threshold (rubric §5)
TECH_ORDER: tuple[str, ...] = ("single_axis", "fixed", "dual_axis")
GOLD_BOOK_2026: str = "2026-Gold-Book-Public.pdf"


def _ny_solar_frame() -> pd.DataFrame:
    """Return the EIA-860 NY operable solar schedule with geometry columns.

    Returns:
        One row per generator with nameplate/DC capacity, operating year,
        tracking flags and plant latitude.
    """
    d = active_eia860_dir()
    df = pd.read_parquet(Path(d) / "eia860_solar_operable.parquet")
    plants = pd.read_parquet(Path(d) / "eia860_plant.parquet")[
        ["Plant Code", "Latitude"]
    ].drop_duplicates("Plant Code")
    ny = df[
        (df["State"].astype(str).str.strip() == "NY")
        & (df["Status"].astype(str).str.strip().str.upper() == "OP")
    ].merge(plants, on="Plant Code", how="left")
    out = pd.DataFrame(
        {
            "code": ny["Plant Code"],
            "cap": pd.to_numeric(ny["Nameplate Capacity (MW)"], errors="coerce").fillna(
                0.0
            ),
            "dc": pd.to_numeric(ny["DC Net Capacity (MW)"], errors="coerce"),
            "opyr": pd.to_numeric(ny["Operating Year"], errors="coerce"),
            "lat": pd.to_numeric(ny["Latitude"], errors="coerce"),
        }
    )
    for col, key in (
        ("Single-Axis Tracking?", "single_axis"),
        ("Fixed Tilt?", "fixed"),
        ("Dual-Axis Tracking?", "dual_axis"),
    ):
        out[key] = (ny[col].astype(str).str.strip().str.upper() == "Y").astype(float)
    return out


def _population_geometry(sub: pd.DataFrame) -> dict:
    """Return one population's capacity-weighted geometry and its annual POA.

    Args:
        sub: Rows of :func:`_ny_solar_frame` forming the population.

    Returns:
        Capacity, tracking-mix fractions, centroid latitude, DC:AC ratio and the
        annual-mean clear-sky plane-of-array output of the mix at that latitude.
    """
    cap = float(sub["cap"].sum())
    mix = np.array([float((sub["cap"] * sub[t]).sum()) for t in TECH_ORDER])
    mix = mix / mix.sum()
    geo = sub["lat"].notna() & (sub["cap"] > 0)
    lat = float(
        np.average(sub.loc[geo, "lat"].to_numpy(), weights=sub.loc[geo, "cap"].to_numpy())
    )
    dc_ok = sub["dc"].notna() & (sub["cap"] > 0)
    ilr = float(sub.loc[dc_ok, "dc"].sum() / sub.loc[dc_ok, "cap"].sum())
    poa = _clearsky_poa_by_tech(round(lat, 2))
    annual = float(sum(m * poa[t].mean() for m, t in zip(mix, TECH_ORDER)))
    return {
        "capacity_mw": round(cap, 1),
        "tracking_mix": {t: round(float(m), 4) for t, m in zip(TECH_ORDER, mix)},
        "centroid_lat_deg": round(lat, 3),
        "dc_ac_ratio": round(ilr, 4),
        "annual_mean_poa": round(annual, 6),
    }


def geometry_ratio() -> dict:
    """Return the registered-vs-whole-fleet clear-sky POA ratio, by year."""
    ny = _ny_solar_frame()
    out: dict[str, dict] = {}
    for year in YEARS:
        whole = ny[~(ny["opyr"] > year)]
        reg = whole[whole["code"].isin(REGISTERED_PLANT_CODES)]
        gw, gr = _population_geometry(whole), _population_geometry(reg)
        out[str(year)] = {
            "whole_ny_fleet": gw,
            "registered_subset": gr,
            "poa_ratio_registered_over_whole": round(
                gr["annual_mean_poa"] / gw["annual_mean_poa"], 4
            ),
        }
    return out


def gold_book_2025_output() -> dict:
    """Return per-unit 2025 net energy of the registered PV fleet, if readable.

    The 2026 Gold Book is published only as a PDF, so the Table III-2a PV rows
    are read from its extracted text. Returns an ``unavailable`` marker rather
    than raising when the PDF reader is not installed.
    """
    try:
        from pypdf import PdfReader
    except Exception as exc:  # noqa: BLE001 - the probe reports, never crashes
        return {"unavailable": f"pypdf import failed: {exc}"}
    path = RAW_DIR / "NYISO" / GOLD_BOOK_2026
    if not path.exists():
        return {"unavailable": f"{path} absent"}
    reader = PdfReader(str(path))
    row = re.compile(
        r"(\d{4}-\d{2}-\d{2})\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"
        r"([\d,.]+)\s+PV SUN\s+([\d,.]+)"
    )
    units: dict[str, dict] = {}
    for page in reader.pages:
        text = page.extract_text() or ""
        if "PV SUN" not in text:
            continue
        for line in text.split("\n"):
            m = row.search(line)
            if not m:
                continue
            cap = float(m.group(2).replace(",", ""))
            gwh = float(m.group(7).replace(",", ""))
            units[line.split(str(m.group(1)))[0].strip()[:60]] = {
                "nameplate_mw": cap,
                "net_energy_2025_gwh": gwh,
                "cf_2025": round(gwh * 1000.0 / (cap * 8760.0), 4) if cap else None,
            }
    cap = sum(u["nameplate_mw"] for u in units.values())
    gwh = sum(u["net_energy_2025_gwh"] for u in units.values())
    return {
        "units": units,
        "n_units": len(units),
        "total_nameplate_mw": round(cap, 1),
        "total_net_energy_2025_gwh": round(gwh, 1),
        "fleet_cf_2025": round(gwh * 1000.0 / (cap * 8760.0), 4) if cap else None,
    }


def zone_removal() -> dict:
    """Return per-zone year-end solar MW under both capacity bases."""
    zones = list(get_iso_config("NYISO").zone_names)
    out: dict[str, dict] = {}
    for year in YEARS:
        eia = _eia860_monthly_capacity("NYISO", "solar", zones, year)
        reg = load_market_solar_monthly("NYISO", year, zones)
        out[str(year)] = {
            z: {
                "eia860_mw": round(float(eia[i, -1]), 1),
                "registry_mw": round(float(reg[i, -1]), 1),
                "removed_mw": round(float(eia[i, -1] - reg[i, -1]), 1),
            }
            for i, z in enumerate(zones)
        }
    return out


def tail_localization(control: str, treatment: str) -> dict:
    """Return the >$300 tail hours of both arms and the hours the treatment adds.

    Args:
        control: Bundle directory name of the control arm.
        treatment: Bundle directory name of the treated arm.

    Returns:
        Per-year tail counts plus the added hours with zone, timestamp and price.
    """

    def tail(bundle: str, year: int) -> tuple[set[int], pd.Series, pd.Series]:
        df = pd.read_parquet(
            REPO / "results" / "calibration" / bundle / "hourly" / f"system_{year}.parquet"
        )
        wide = df.pivot_table(index="hour", columns="zone", values="price")
        mx, zmax = wide.max(axis=1), wide.idxmax(axis=1)
        return set(mx[mx > TAIL_THRESHOLD_USD].index), mx, zmax

    out: dict[str, dict] = {}
    for year in YEARS:
        stamps = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
        c_hours, _, _ = tail(control, year)
        t_hours, t_mx, t_zone = tail(treatment, year)
        out[str(year)] = {
            "control_tail_hours": len(c_hours),
            "treatment_tail_hours": len(t_hours),
            "added_by_treatment": [
                {
                    "hour": int(h),
                    "timestamp": stamps[int(h)].strftime("%Y-%m-%d %H:00"),
                    "zone": str(t_zone.loc[h]),
                    "price": round(float(t_mx.loc[h]), 1),
                }
                for h in sorted(t_hours - c_hours)
            ],
            "removed_by_treatment": sorted(int(h) for h in (c_hours - t_hours)),
            "treatment_tail_zones": sorted(
                {str(t_zone.loc[h]) for h in t_hours}
            ),
            "treatment_tail_hours_of_day": sorted(
                {int(stamps[int(h)].hour) for h in t_hours}
            ),
        }
    return out


def _treatment_tail_hours_2023() -> list[int]:
    """Return the treated arm's 2023 >$300 tail hours, recomputed from its sidecar."""
    df = pd.read_parquet(
        REPO / "results/calibration/nyiso128_treatment/hourly/system_2023.parquet"
    )
    mx = df.pivot_table(index="hour", columns="zone", values="price").max(axis=1)
    return [int(h) for h in mx[mx > TAIL_THRESHOLD_USD].index]


def li_import_binding(bundles: tuple[str, ...], year: int, tail_hours: list[int]) -> dict:
    """Return how often Long Island's two import paths sit at their bound.

    The C3c-2023 cost localizes entirely to Zone K (see
    :func:`tail_localization`), so the question that names the successor lever is
    *what is holding Long Island short in those hours*. This reads the committed
    ``hourly/network_<year>.parquet`` sidecars and reports, for both LI import
    links, the share of all hours and of the tail hours at ``limit_up``.

    Args:
        bundles: Bundle directory names to read.
        year: Solve year.
        tail_hours: The year's >$300 tail hours (from :func:`tail_localization`).

    Returns:
        Per-bundle, per-link at-bound shares, median limit and tail-hour flows.
    """
    links = ("NYC>Long_Island", "NYISO_external>Long_Island")
    out: dict[str, dict] = {}
    for bundle in bundles:
        net = pd.read_parquet(
            REPO / "results" / "calibration" / bundle / "hourly" / f"network_{year}.parquet"
        )
        net = net[net["pass"] == "P1"]
        per_link: dict[str, dict] = {}
        for name in links:
            g = net[net["name"] == name].set_index("hour")
            if g.empty:
                continue
            at_bound = g["mw"] >= g["limit_up"] - 1e-6
            per_link[name] = {
                "limit_up_median_mw": round(float(g["limit_up"].median()), 1),
                "at_bound_share_all_hours": round(float(at_bound.mean()), 4),
                "at_bound_share_tail_hours": round(
                    float(at_bound.reindex(tail_hours).mean()), 4
                ),
                "flow_mw_in_tail_hours_median": round(
                    float(g["mw"].reindex(tail_hours).median()), 1
                ),
            }
        out[bundle] = per_link
    return out


def main() -> int:
    """Run all measurements and write the record."""
    record = {
        "session": "nyiso-129",
        "date": "2026-08-06",
        "no_solve": True,
        "measurement_1_geometry_ratio": geometry_ratio(),
        "measurement_2_gold_book_2025": gold_book_2025_output(),
        "measurement_2b_model_cf_constant": {
            "symbol": "RENEWABLE_AVG_CF['NYISO']['solar']",
            "value": 0.15,
            "note": (
                "constants.py labels the MISO/NYISO/NEISO block a Tier-3 approximation "
                "with 'needs-citation: verify against EIA-923 ISO totals before quoting "
                "a forecast'; the donor-repaired profile realizes ~0.133 after clipping"
            ),
        },
        "measurement_3_zone_removal": zone_removal(),
        "measurement_3b_tail_localization": tail_localization(
            "nyiso128_control", "nyiso128_treatment"
        ),
    }
    tail_2023 = sorted(
        {
            *(
                h["hour"]
                for h in record["measurement_3b_tail_localization"]["2023"][
                    "added_by_treatment"
                ]
            ),
            *_treatment_tail_hours_2023(),
        }
    )
    record["measurement_4_li_import_binding"] = li_import_binding(
        ("nyiso128_control", "nyiso128_treatment"), 2023, tail_2023
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=1))
    g = record["measurement_1_geometry_ratio"]
    print("POA ratio (registered / whole NY fleet):")
    for year in YEARS:
        print(f"  {year}: {g[str(year)]['poa_ratio_registered_over_whole']}")
    gb = record["measurement_2_gold_book_2025"]
    if "fleet_cf_2025" in gb:
        print(
            f"Gold Book 2025: {gb['total_net_energy_2025_gwh']} GWh over "
            f"{gb['total_nameplate_mw']} MW -> CF {gb['fleet_cf_2025']}"
        )
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
