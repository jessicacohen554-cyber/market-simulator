"""caiso-216 Phase 0 — does the MODEL's south even HAVE a belly surplus?

The caiso-215 zonal decomposition localized the C3a 2024/25 overrun to the
southern solar belly (model south belly clears at the CC/storage-charge band
$22-27 where reality clears <=$0 in ~1.0-1.2 kh/yr and splits NP15 over SP15
by +$12-21 through S->N congestion the model never forms). This probe answers
the ONE measurement caiso-215 deferred, which decides the lever class:

* If the model's south is NOT in physical surplus in those hours (net-load
  positive), NO price-formation change can create the surplus regime — the
  upstream driver is the ZONAL ALLOCATION of zero-MC supply (the measured
  plant-location -> zone crosswalk), and that is where a lever must act.
* If the model's south IS in surplus but the surplus is fully absorbed
  (S->N path headroom + storage charge + spill-at-positive-λ), the missing
  piece is the surplus PRICE-FORMATION / absorption representation.

NO LP, NO SOLVE — committed bytes only. The only reconstruction is the
licensed caiso-105/131 ``run_year(fleet_only=True)`` input assembly (the same
pattern as the committed caiso-202 probe), which rebuilds the keeper's own
zonal demand, renewable bounds (cf x cap), fleet arrays and storage fleet
from the committed inputs + the bundle's ``meta.json`` kwargs. Every other
series is a committed artifact: the keeper's ``hourly/`` sidecars, the raw
trading-hub RTM CSVs (via the committed caiso-215 probe's loader), CAISO's
published production-and-curtailments workbooks, and the EIA-930 CISO
region parquet (D / NG / TI).

Sections (stdout + JSON):

* B0 — controls: recon demand rows == sidecar demand (row-matched by value);
  ISO-wide renewable potential vs sidecar wind+solar dispatch -> the model's
  own spill series (endogenous curtailment), vs reality's reported record.
* B1 — the model's zonal renewable inputs: capacity & annual-potential
  shares per zone; the lat-cut straddle bands (capacity within +-0.25 deg of
  the Path 15 / Path 26 latitude cuts — the allocation uncertainty mass);
  the ATL_PNODE_MAP membership witnesses (DIABLO, and hub row counts).
* B2 — THE DECIDING TABLE: hourly zero-MC-plus-must-run net position of the
  south, at both cuts (cut26 = LA_BASIN+SDGE+SP15_rest; cut15 = +ZP26),
  stacked in labeled layers (renewables-only; +nuclear; +biomass/OTHER
  injection; +hydro-at-min-floor), against the armed S->N directional path
  caps (Path 26 3,000 MW / Path 15 5,400 MW) and the in-cut storage charge
  power. Counted over (a) all belly hours (hod 10-15 PST), (b) reality's
  south-surplus hours (TH_SP15 RT < 0), (c) reality's split hours
  (NP15-SP15 > $15).
* B3 — the model's price-side state in those same hours: per-zone λ
  distribution, hours λ<=0, storage charge interior-vs-saturated, dump.
* B4 — reality's curtailment record (2023/24/25): annual GWh by fuel,
  Local-vs-System share, belly share, monthly profile; model spill vs it.
* B5 — the export witness: EIA-930 CISO TI (total interchange, +=export)
  belly distribution vs the model's import-class belly dispatch.
* B6 — the pre-registered verdict logic printed with its inputs.

Writes ``results/calibration/_caiso216_belly_surplus.json`` (deterministic:
sorted keys, rounded floats, no timestamps).

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso216_belly_surplus.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _caiso215_c3a_zonal_decomp as c215  # noqa: E402  (committed probe)

YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso200_h1_memberpanel"
CURT_DIR = REPO / "data/raw/caiso-curtailment"
E930_REGION = REPO / "data/raw/CISO_region.parquet"
ATLAS = REPO / "data/raw/caiso-atlas/ATL_PNODE_MAP.csv"
OUT_JSON = REPO / "results/calibration/_caiso216_belly_surplus.json"

# Reconstruction cache (session-scratch, never committed).
CACHE = Path(
    os.environ.get(
        "CAISO216_CACHE",
        "/tmp/claude-0/-home-user-market-simulator/294f0cbd-321d-58ea-bc7e-5129f1f0a036/scratchpad",
    )
)

CA_ZONES = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")
SOUTH3 = ("LA_BASIN", "SDGE", "SP15_rest")  # south of Path 26
SOUTH4 = ("ZP26", "LA_BASIN", "SDGE", "SP15_rest")  # south of Path 15
# The keeper's ARMED directional S->N ratings (caiso_asymmetric_path_ratings,
# model/interchange/caiso.py CAISO_PATH_DIRECTIONAL_RATINGS — WECC Path
# Rating Catalog): Path 26 S->N 3,000 MW bounds cut26; Path 15 S->N 5,400 MW
# bounds cut15.
SN_CAP = {"cut26": 3000.0, "cut15": 5400.0}
CUT_ZONES = {"cut26": SOUTH3, "cut15": SOUTH4}
BELLY = (10, 15)  # hod window, inclusive, PST — caiso-215 Z6 convention


def hod_of_hour() -> np.ndarray:
    """Hour-of-day (PST, fixed clock) for the committed 8760 hour index."""
    return np.arange(HOURS) % 24


def sidecars(year: int) -> dict:
    """Keeper per-zone hourly price/demand/dump + ISO class MW + storage."""
    d = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    out = {
        "price": d.pivot_table(index="hour", columns="zone", values="price"),
        "demand": d.pivot_table(index="hour", columns="zone", values="demand"),
        "dump": d.pivot_table(index="hour", columns="zone", values="dump"),
    }
    c = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    out["klass"] = c.pivot_table(index="hour", columns="klass", values="mw")
    s = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    out["charge"] = s.groupby("hour")["charge_mw"].sum().reindex(range(HOURS))
    out["discharge"] = s.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS))
    return out


def recon(year: int) -> dict:
    """The caiso-105/131 fleet_only input assembly, reduced to what B1/B2 need.

    Cached per year. Everything is derived from the keeper bundle's own
    ``meta.json`` kwargs, so the rebuilt inputs are the solve's inputs.
    """
    p = CACHE / f"caiso216_recon_{year}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in z.files}
    import inspect

    from run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {k: v for k, v in meta.items() if k in params and k not in skip}
    # The meta.json override dicts are stored under their calibration-flag
    # names but run_year takes them under the short param names (the same
    # mapping run_calibration_full uses at its run_year call site). The
    # prb-overrides dict is where the keeper's caiso_* ScenarioConfig
    # overrides (supply-consistent demand, clock realign, DSW cleans, ...)
    # actually live, so dropping it silently rebuilds a ~5 % different
    # demand — caught by the B0 row-match control.
    for meta_key, param in (
        ("coal_prb_sigmoid_overrides", "prb_overrides"),
        ("coal_bit_sigmoid_overrides", "bit_overrides"),
        ("coal_bit_passthrough_sigmoid", "coal_bit_sigmoid"),
    ):
        if meta_key in meta and param in params and param not in kwargs:
            kwargs[param] = meta[meta_key]
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    state = run_year(year, meta["iso"], HOURS, gas, {}, fleet_only=True, **kwargs)

    from market_sim.data.fleet import FUEL_TYPE_MAP

    inv = {v: k for k, v in FUEL_TYPE_MAP.items()}
    fa = state["fleet_arrays"]
    fuel = np.array([inv.get(int(i), str(i)) for i in np.asarray(fa.fuel_type_idx)])
    zone_idx = np.asarray(fa.zone_idx, dtype=int)
    n_zones = int(np.asarray(state["demand"]).shape[0])

    def zone_hourly(mask: np.ndarray, values: np.ndarray) -> np.ndarray:
        """Sum a (n_gen, T) per-unit series into (n_zones, T) by zone."""
        out = np.zeros((n_zones, HOURS), dtype=np.float64)
        np.add.at(out, zone_idx[mask], values[mask])
        return out

    avail = np.asarray(fa.availability, dtype=float)
    pmax_h = np.asarray(fa.pmax, dtype=float)[:, None] * avail
    lower = (
        np.asarray(fa.min_gen, dtype=float)
        if fa.min_gen is not None
        else np.asarray(fa.pmin, dtype=float)[:, None] * np.ones((1, HOURS))
    )
    lower = np.minimum(lower, pmax_h)  # a floor never exceeds available cap

    nuclear_mw = zone_hourly(fuel == "nuclear", pmax_h)
    hydro_floor = zone_hourly(fuel == "hydro", lower)
    hydro_pmax = zone_hourly(fuel == "hydro", pmax_h)

    stor_power = np.zeros(n_zones)
    stor_zone_names: dict[int, float] = {}
    for u in state["storage_units"]:
        zi = int(getattr(u, "zone_idx", 0))
        pw = float(getattr(u, "power_cap_mw", 0.0))
        stor_power[zi] += pw
        stor_zone_names[zi] = stor_zone_names.get(zi, 0.0) + pw

    out = {
        "demand": np.asarray(state["demand"], dtype=np.float64),
        "wind_pot": np.asarray(state["wind_cf"], dtype=np.float64)
        * np.asarray(state["wind_cap"], dtype=np.float64)[:, None],
        "solar_pot": np.asarray(state["solar_cf"], dtype=np.float64)
        * np.asarray(state["solar_cap"], dtype=np.float64)[:, None],
        "wind_cap": np.asarray(state["wind_cap"], dtype=np.float64),
        "solar_cap": np.asarray(state["solar_cap"], dtype=np.float64),
        "nuclear_mw": nuclear_mw,
        "hydro_floor": hydro_floor,
        "hydro_pmax": hydro_pmax,
        "storage_power": stor_power,
        "wind_mc_min": np.array(
            [float(np.min(state["wind_mc"])), float(np.max(state["wind_mc"]))]
        ),
        "solar_mc_min": np.array(
            [float(np.min(state["solar_mc"])), float(np.max(state["solar_mc"]))]
        ),
        "storage_zone_names": np.array(
            [f"{k}:{v:.0f}" for k, v in sorted(stor_zone_names.items())]
        ),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, **out)
    return out


def match_zone_rows(recon_demand: np.ndarray, side_demand: pd.DataFrame) -> dict:
    """Map model zone-name -> recon row index by matching demand series.

    The fleet_only arrays carry no zone names; the keeper sidecar does. A
    row matches a sidecar zone when the two 8760-hour demand series agree to
    float tolerance — a self-verifying join (also the B0 control).
    """
    mapping: dict[str, int] = {}
    for zone in side_demand.columns:
        col = side_demand[zone].to_numpy()
        diffs = np.nanmax(np.abs(recon_demand - col[None, :]), axis=1)
        j = int(np.argmin(diffs))
        if diffs[j] < 0.5:  # MW tolerance; sidecar is float32-rounded
            mapping[str(zone)] = j
    return mapping


def hub_actuals(year: int) -> dict[str, np.ndarray]:
    """Per-hub RT actual LMP on the committed clock (caiso-215 loader)."""
    rtm = c215.load_market_csv("rtm", year, c215.HUBS)
    return {h: rtm["LMP"][h].to_numpy() for h in c215.HUBS}


def curtailment_hourly(year: int) -> pd.DataFrame | None:
    """Hourly curtailment MWh by fuel x reason from the published workbook.

    The Curtailments sheet is a sparse record of 5-minute intervals with
    nonzero curtailment: Date (day stamp), Hour (1-24, local prevailing),
    Interval (1-12), Wind/Solar Curtailment (MW over the interval), Reason
    (Local / System). MW-per-interval is established against the published
    annual total: 2024 raw-sum/12 = 3.423 TWh, CAISO's reported ~3.4 TWh
    (raw-sum alone would read 41 TWh). Aggregated here to hour x (fuel,
    reason) MWh (sum/12) on the local-prevailing day/hour — the belly/annual
    aggregates this probe uses are insensitive to the 1-hour PST/PDT wobble
    vs the model clock, which is why no interval-level clock join is
    attempted.
    """
    path = CURT_DIR / f"productionandcurtailmentsdata_{year}.xlsx"
    if not path.exists():
        return None
    cache = CACHE / f"caiso216_curt_{year}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["Curtailments"]
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(rows)]
    idx = {name: i for i, name in enumerate(header)}
    date_i = idx.get("Date")
    hour_i = idx.get("Hour")
    wind_i = next((i for n, i in idx.items() if "Wind" in n), None)
    solar_i = next((i for n, i in idx.items() if "Solar" in n), None)
    reason_i = next(
        (i for n, i in idx.items() if n in ("Reason", "Curtailment Type")), None
    )
    rec = []
    for r in rows:
        if r is None or date_i is None or r[date_i] is None:
            continue
        day = pd.Timestamp(r[date_i]).date()
        hr = int(r[hour_i]) if r[hour_i] is not None else 0
        reason = str(r[reason_i]).strip() if reason_i is not None else "?"
        wind = float(r[wind_i] or 0.0) if wind_i is not None else 0.0
        solar = float(r[solar_i] or 0.0) if solar_i is not None else 0.0
        rec.append((day, hr, reason, wind, solar))
    wb.close()
    df = pd.DataFrame(rec, columns=["day", "hour", "reason", "wind", "solar"])
    df = df.groupby(["day", "hour", "reason"], as_index=False)[["wind", "solar"]].sum()
    df[["wind", "solar"]] /= 12.0  # MW per 5-min interval -> MWh per hour
    df["day"] = pd.to_datetime(df["day"])
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache)
    return df


def e930_series(year: int) -> dict[str, np.ndarray]:
    """EIA-930 CISO Demand / Net-generation / Total-interchange, model clock.

    TI sign is the EIA-930 convention: positive = net EXPORT from CISO.
    """
    df = pd.read_parquet(E930_REGION)
    idx = c215.local_hour_index(year)
    out = {}
    for code in ("D", "NG", "TI"):
        sub = df[df["type"] == code].set_index("period")["value_mwh"]
        sub.index = pd.DatetimeIndex(sub.index).tz_convert("Etc/GMT+8")
        out[code] = sub.reindex(idx).to_numpy(dtype=float)
    return out


def pct(x: np.ndarray, q: float) -> float:
    """NaN-safe percentile."""
    x = x[~np.isnan(x)]
    return float(np.percentile(x, q)) if x.size else float("nan")


def surplus_stats(
    s: np.ndarray,
    belly_mask: np.ndarray,
    south_neg: np.ndarray,
    split_h: np.ndarray,
    cap: float,
    stor: float,
) -> dict:
    """The B2 stat block for one net-position series (MW, +=surplus)."""
    sb = s[belly_mask]
    return {
        "hours_pos": int((s > 0).sum()),
        "hours_pos_belly": int((sb > 0).sum()),
        "belly_mean_mw": float(np.round(sb.mean(), 2)),
        "belly_p95_mw": float(np.round(pct(sb, 95), 2)),
        "max_mw": float(np.round(np.max(s), 2)),
        "pos_twh": float(np.round(np.maximum(0.0, s).sum() / 1e6, 3)),
        "pos_twh_in_south_neg": float(
            np.round(np.maximum(0.0, s[south_neg]).sum() / 1e6, 3)
        ),
        "hours_over_path": int((s > cap).sum()),
        "hours_over_path_plus_storage": int((s > cap + stor).sum()),
        "south_neg_hours_pos": int((s[south_neg] > 0).sum()),
        "south_neg_hours_mean_mw": float(
            np.round(s[south_neg].mean() if south_neg.any() else np.nan, 2)
        ),
        "split_hours_pos": int((s[split_h] > 0).sum()),
        "split_hours_mean_mw": float(
            np.round(s[split_h].mean() if split_h.any() else np.nan, 2)
        ),
    }


def r2(x: float) -> float:
    """Round for the deterministic JSON."""
    return float(np.round(x, 2))


def main() -> None:  # noqa: PLR0915  (a linear report, sectioned by prints)
    out: dict = {"years": {}}
    hod = hod_of_hour()
    belly_mask = (hod >= BELLY[0]) & (hod <= BELLY[1])

    # ---- B1 static: straddle-band capacity + ATL membership witnesses ----
    from market_sim.data import zone_assignment as za

    loc = za._oris_to_location()
    # The loader's own membership filter: build_zone_lookup(iso) covers the
    # eGRID CISO balancing-authority plants only — the same population
    # _eia860_monthly_capacity places (renewables.py L878).
    zone_lookup = za.build_zone_lookup("CAISO")
    straddle: dict = {}
    for fuel, fname in (
        ("solar", "eia860_solar_operable.parquet"),
        ("wind", "eia860_wind_operable.parquet"),
    ):
        df = pd.read_parquet(REPO / "data/raw/eia-860" / fname)
        cap = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0)
        code = pd.to_numeric(df["Plant Code"], errors="coerce")
        rows = []
        for c, mw in zip(code, cap):
            if not np.isfinite(c) or mw <= 0:
                continue
            zone = zone_lookup.get(int(c))
            tup = loc.get(int(c))
            if zone is None or tup is None:
                continue
            lat, lon, st, cty = tup
            rows.append((lat, st, cty, zone, mw))
        t = pd.DataFrame(rows, columns=["lat", "st", "cty", "zone", "mw"])
        tot = float(t["mw"].sum())
        by_zone = t.groupby("zone")["mw"].sum().to_dict()
        band15 = t[(t["lat"] >= 36.25) & (t["lat"] < 36.75)]["mw"].sum()
        band26 = t[(t["lat"] >= 34.75) & (t["lat"] < 35.25)]["mw"].sum()
        # Boundary-sensitive masses feeding the B2b what-if arithmetic: the
        # capacity currently placed on the NORTH side of each cut that a
        # membership-based crosswalk could move south — (i) the ZP26 plants
        # in the Path-26 lat band's northern half (Tehachapi/Mojave ridge,
        # electrically TRTP -> Vincent = TH_SP15), (ii) the NP15 plants in
        # the Path-15 band's northern half (Fresno/Westlands, electrically
        # Gates/Mustang = TH_ZP26), and (iii) the central-coast county-lift
        # plants (Monterey 53 / San Luis Obispo 79 / San Benito 69 -> NP15,
        # the same lift that puts DIABLO in NP15 against CAISO's own
        # TH_ZP26_GEN membership).
        band26_north = t[(t["zone"] == "ZP26") & (t["lat"] >= 35.0) & (t["lat"] < 35.25)]
        band15_north = t[(t["zone"] == "NP15") & (t["lat"] >= 36.5) & (t["lat"] < 36.75)]
        cc_lift = t[
            (t["zone"] == "NP15")
            & (t["st"] == 6)
            & (t["cty"].isin([53, 69, 79]))
        ]
        straddle[fuel] = {
            "total_mw": r2(tot),
            "by_zone_mw": {k: r2(v) for k, v in sorted(by_zone.items())},
            "band_path15_pm25_mw": r2(float(band15)),
            "band_path26_pm25_mw": r2(float(band26)),
            "movable_zp26_band26_mw": r2(float(band26_north["mw"].sum())),
            "movable_np15_band15_mw": r2(float(band15_north["mw"].sum())),
            "movable_np15_cc_lift_mw": r2(float(cc_lift["mw"].sum())),
        }
    atlas = pd.read_csv(ATLAS)
    diablo = atlas[atlas["PNODE_ID"].str.contains("DIABLO", na=False)][
        "APNODE_ID"
    ].value_counts()
    hub_counts = atlas["APNODE_ID"].value_counts()
    # B1b — crosswalk-intake feasibility: can the boundary-sensitive plants
    # be joined to CAISO's own hub membership by pnode-name fragment? A
    # name-prefix witness scan over the largest movable plants (not the
    # intake itself — the intake is the packet's funded work).
    witnesses = {
        "DIABLO": "DIABLO",  # nuclear, cc-lift canonical case
        "TOPAZ": "TOPAZ",  # SLO solar, cc-lift
        "SOLAR_STAR": "SOLARS",  # Antelope Valley solar
        "ALTA_TEHACHAPI": "ALTA",  # Tehachapi wind, band26
        "WINDHUB": "WINDHUB",  # Tehachapi TRTP collector
        "MIDWAY": "MIDWAY",  # the Path 15/26 corner substation
        "WHIRLWIND": "WHIRLWIND",  # TRTP collector
        "CALIFORNIA_VALLEY": "CVSR",  # SLO solar (CVSR)
        "MUSTANG": "MUSTANG",  # Westlands-area solar, band15
        "GATES": "GATES",  # Path 15 south terminal
    }
    hub_of = {}
    for label, frag in witnesses.items():
        sub = atlas[atlas["PNODE_ID"].str.contains(frag, na=False)]
        hub_of[label] = {
            str(k): int(v) for k, v in sub["APNODE_ID"].value_counts().items()
        }
    out["B1_allocation"] = {
        "straddle": straddle,
        "atlas_diablo_membership": {str(k): int(v) for k, v in diablo.items()},
        "atlas_hub_rows": {
            str(k): int(v)
            for k, v in hub_counts.items()
            if str(k).startswith("TH_")
        },
        "atlas_name_witnesses": hub_of,
    }
    print("=" * 78)
    print("B1 — zonal allocation inputs")
    print(json.dumps(out["B1_allocation"], indent=1))

    for year in YEARS:
        print("=" * 78)
        print(f"YEAR {year}")
        yr: dict = {}
        sc = sidecars(year)
        rc = recon(year)
        zmap = match_zone_rows(rc["demand"], sc["demand"])

        # ---- B0 controls ----
        missing = [z for z in CA_ZONES if z not in zmap]
        demand_err = {
            z: float(
                np.nanmax(
                    np.abs(rc["demand"][zmap[z]] - sc["demand"][z].to_numpy())
                )
            )
            for z in zmap
        }
        pot_iso = rc["wind_pot"].sum(axis=0) + rc["solar_pot"].sum(axis=0)
        disp_iso = (
            sc["klass"]["wind"].to_numpy() + sc["klass"]["solar"].to_numpy()
        )
        spill = np.maximum(0.0, pot_iso - disp_iso)
        yr["B0_controls"] = {
            "zone_rows_matched": sorted(zmap),
            "zone_rows_missing": missing,
            "max_demand_row_err_mw": {k: r2(v) for k, v in demand_err.items()},
            "model_spill_gwh": r2(float(spill.sum() / 1e3)),
            "model_spill_belly_share": r2(
                float(spill[belly_mask].sum() / max(spill.sum(), 1e-9))
            ),
            "renewable_offer_floor_range": {
                "wind": [r2(v) for v in rc["wind_mc_min"]],
                "solar": [r2(v) for v in rc["solar_mc_min"]],
            },
        }
        print("B0:", json.dumps(yr["B0_controls"], indent=1))
        if missing:
            print(f"!! zone match failed for {missing} — aborting year")
            out["years"][str(year)] = yr
            continue

        # ---- B2 the deciding table ----
        # Injected must-run (biomass + OTHER): the runner splits each class
        # across zones by annual demand share (run_calibration_full
        # _must_run_profiles); reproduce that split from the sidecar series.
        dem_z = np.stack([sc["demand"][z].to_numpy() for z in CA_ZONES])
        zshare = dem_z.sum(axis=1) / dem_z.sum()
        inj_iso = np.zeros(HOURS)
        for kl in ("biomass", "OTHER"):
            if kl in sc["klass"].columns:
                inj_iso = inj_iso + sc["klass"][kl].to_numpy()
        actual = hub_actuals(year)
        np15 = actual["TH_NP15_GEN-APND"]
        sp15 = actual["TH_SP15_GEN-APND"]
        south_neg = sp15 < 0.0
        split_h = (np15 - sp15) > 15.0

        cuts: dict = {}
        for cut, zones in CUT_ZONES.items():
            zi = [zmap[z] for z in zones]
            zsel = [CA_ZONES.index(z) for z in zones]
            dem = rc["demand"][zi].sum(axis=0)
            ren = rc["solar_pot"][zi].sum(axis=0) + rc["wind_pot"][zi].sum(axis=0)
            nuc = rc["nuclear_mw"][zi].sum(axis=0)
            hyd = rc["hydro_floor"][zi].sum(axis=0)
            inj = inj_iso * float(zshare[zsel].sum())
            stor = float(rc["storage_power"][zi].sum())
            cap = SN_CAP[cut]

            layers = {
                "L0_renewables_only": ren - dem,
                "L1_plus_nuclear": ren + nuc - dem,
                "L2_plus_injected": ren + nuc + inj - dem,
                "L3_plus_hydro_floor": ren + nuc + inj + hyd - dem,
            }
            row: dict = {
                "zones": list(zones),
                "sn_path_cap_mw": cap,
                "storage_charge_cap_mw": r2(stor),
                "demand_belly_mean_mw": r2(float(dem[belly_mask].mean())),
                "renewable_pot_belly_mean_mw": r2(float(ren[belly_mask].mean())),
                "nuclear_belly_mean_mw": r2(float(nuc[belly_mask].mean())),
                "injected_belly_mean_mw": r2(float(inj[belly_mask].mean())),
                "hydro_floor_belly_mean_mw": r2(float(hyd[belly_mask].mean())),
            }
            for name, s in layers.items():
                row[name] = surplus_stats(s, belly_mask, south_neg, split_h, cap, stor)
            row["reality_hours"] = {
                "south_neg": int(south_neg.sum()),
                "split_gt15": int(split_h.sum()),
            }
            cuts[cut] = row
            if cut == "cut15":
                cuts["_base15"] = layers["L2_plus_injected"]
                cuts["_stor15"] = stor
            else:
                cuts["_base26"] = layers["L2_plus_injected"]
                cuts["_stor26"] = stor
        base15, stor15 = cuts.pop("_base15"), cuts.pop("_stor15")
        base26, stor26 = cuts.pop("_base26"), cuts.pop("_stor26")

        # ---- B2b what-if arithmetic (allocation sensitivities, no LP) ----
        # Pure input-side counterfactuals on the L2 series, each an UPPER
        # BOUND pending the real membership crosswalk intake: (a) DIABLO to
        # ZP26 — CAISO's own ATL_PNODE_MAP membership vs the model's
        # central-coast county lift; (b) the movable straddle masses of B1
        # moved across their cut, shaped by the source zone's own per-zone
        # CF profile.
        def shifted_pot(src_zone: str, mw: dict[str, float]) -> np.ndarray:
            s = np.zeros(HOURS)
            j = zmap[src_zone]
            for fuel, key in (("solar", "solar"), ("wind", "wind")):
                capz = float(rc[f"{fuel}_cap"][j])
                if capz > 0 and mw.get(key, 0.0) > 0:
                    s = s + rc[f"{fuel}_pot"][j] * (mw[key] / capz)
            return s

        mv = {
            f: {
                "b26": straddle[f]["movable_zp26_band26_mw"],
                "b15": straddle[f]["movable_np15_band15_mw"],
                "cc": straddle[f]["movable_np15_cc_lift_mw"],
            }
            for f in ("solar", "wind")
        }
        diablo = rc["nuclear_mw"][zmap["NP15"]]
        shift15 = shifted_pot(
            "NP15",
            {
                "solar": mv["solar"]["b15"] + mv["solar"]["cc"],
                "wind": mv["wind"]["b15"] + mv["wind"]["cc"],
            },
        )
        shift26 = shifted_pot(
            "ZP26", {"solar": mv["solar"]["b26"], "wind": mv["wind"]["b26"]}
        )
        sens = {
            "S1_cut15_plus_diablo": surplus_stats(
                base15 + diablo, belly_mask, south_neg, split_h, 5400.0, stor15
            ),
            "S2_cut15_plus_diablo_plus_crosswalk": surplus_stats(
                base15 + diablo + shift15,
                belly_mask,
                south_neg,
                split_h,
                5400.0,
                stor15,
            ),
            "S3_cut26_plus_crosswalk": surplus_stats(
                base26 + shift26, belly_mask, south_neg, split_h, 3000.0, stor26
            ),
        }
        cuts["B2b_sensitivities"] = sens
        yr["B2_surplus"] = cuts
        print("B2:", json.dumps(cuts, indent=1))

        # ---- B3 price-side state ----
        lam = {z: sc["price"][z].to_numpy() for z in CA_ZONES}
        chg = sc["charge"].to_numpy(dtype=float)
        total_power = float(rc["storage_power"][[zmap[z] for z in CA_ZONES]].sum())
        chg_b = chg[belly_mask]
        yr["B3_price_state"] = {
            "zone_hours_le0": {z: int((lam[z] <= 0).sum()) for z in CA_ZONES},
            "zone_hours_le5": {z: int((lam[z] <= 5).sum()) for z in CA_ZONES},
            "zone_belly_p05": {z: r2(pct(lam[z][belly_mask], 5)) for z in CA_ZONES},
            "zone_belly_p50": {z: r2(pct(lam[z][belly_mask], 50)) for z in CA_ZONES},
            "storage_total_power_mw": r2(total_power),
            "belly_charge_p50_mw": r2(pct(chg_b, 50)),
            "belly_charge_p95_mw": r2(pct(chg_b, 95)),
            "belly_charge_max_mw": r2(float(np.nanmax(chg_b))),
            "belly_hours_charge_ge_90pct_power": int(
                (chg_b >= 0.9 * total_power).sum()
            ),
            "dump_hours_nonzero": int(
                (sum(sc["dump"][z].to_numpy() for z in CA_ZONES) > 1.0).sum()
            ),
            # The one zonal separation the model DOES produce: SDGE's one-way
            # LCT import cap binding southward — proof the pocket machinery
            # separates prices when a real limit exists in the topology.
            "sdge_only_le0_hours": int(
                ((lam["SDGE"] <= 0) & (lam["SP15_rest"] > 0)).sum()
            ),
        }
        print("B3:", json.dumps(yr["B3_price_state"], indent=1))

        # ---- B4 reality's curtailment record ----
        curt = curtailment_hourly(year)
        if curt is not None:
            tot = curt[["wind", "solar"]].sum()
            by_reason = curt.groupby("reason")[["wind", "solar"]].sum()
            hb = curt[(curt["hour"] - 1 >= BELLY[0]) & (curt["hour"] - 1 <= BELLY[1])]
            monthly = (
                curt.assign(m=curt["day"].dt.month)
                .groupby("m")[["wind", "solar"]]
                .sum()
                .sum(axis=1)
            )
            yr["B4_reality_curtailment"] = {
                # Span label, measured from the rows (the corpus README's
                # "report discontinued 2025-06-01" line does NOT truncate
                # the committed 2025 workbook — it carries all 12 months).
                "record_span": [
                    str(curt["day"].min().date()),
                    str(curt["day"].max().date()),
                ],
                "annual_gwh": {
                    "wind": r2(float(tot["wind"] / 1e3)),
                    "solar": r2(float(tot["solar"] / 1e3)),
                },
                "reason_share_of_total": {
                    str(k): r2(float(v / max(tot.sum(), 1e-9)))
                    for k, v in by_reason.sum(axis=1).items()
                },
                "belly_share": r2(
                    float(
                        hb[["wind", "solar"]].sum().sum() / max(tot.sum(), 1e-9)
                    )
                ),
                "top3_months_gwh": {
                    str(k): r2(float(v / 1e3))
                    for k, v in monthly.nlargest(3).items()
                },
                "model_spill_vs_reported_ratio": r2(
                    float(spill.sum() / max(tot.sum(), 1e-9))
                ),
            }
            print("B4:", json.dumps(yr["B4_reality_curtailment"], indent=1))

        # ---- B5 export witness ----
        e930 = e930_series(year)
        ti_b = e930["TI"][belly_mask]
        imp = sc["klass"]["import"].to_numpy() if "import" in sc["klass"] else None
        yr["B5_export_witness"] = {
            "actual_TI_belly_p05_mw": r2(pct(ti_b, 5)),
            "actual_TI_belly_p50_mw": r2(pct(ti_b, 50)),
            "actual_TI_belly_p95_mw": r2(pct(ti_b, 95)),
            "actual_belly_export_hours": int(np.nansum(ti_b > 0)),
            "model_import_belly_p50_mw": r2(pct(imp[belly_mask], 50))
            if imp is not None
            else None,
            "model_import_belly_p05_mw": r2(pct(imp[belly_mask], 5))
            if imp is not None
            else None,
            "model_belly_export_hours": 0,  # structural: no export column in P1
        }
        print("B5:", json.dumps(yr["B5_export_witness"], indent=1))

        out["years"][str(year)] = yr

    # ---- B6 verdict logic (numbers above; statement in the FINDING) ----
    out["B6_verdict_rule"] = (
        "ALLOCATION-CLASS if L2 surplus <= 0 through reality's south-surplus "
        "hours (the model's south has nothing to price at surplus); "
        "ABSORPTION/PRICE-FORMATION-CLASS if L2 > 0 in those hours but below "
        "path+storage absorption (the model pools/absorbs what reality "
        "strands); MECHANISM-GAP if L2 exceeds absorption yet zone lambda "
        "stays at the charge band (spill must then exist and lambda must sit "
        "on the renewable offer floor — check B3)."
    )
    OUT_JSON.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT_JSON.relative_to(REPO)}")


if __name__ == "__main__":
    main()
