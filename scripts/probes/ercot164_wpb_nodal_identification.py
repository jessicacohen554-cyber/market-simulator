"""ercot-164 Phase 0/1 — WP-B nodal curtailment layer IDENTIFICATION. No LP.

The §5.1 item-7 question, on committed data only (keeper UNCHANGED at
2026-08-03-ercot158-pool-arm): aggregate the station-to-station NP6-86 binding
rows that ``curate_gtc_limits._gtc_only`` drops, resolve their stations through
the NP4-160-SG spine committed at ERCOT-160 (``data/raw/ercot-network-model/``,
published 2026-07-29 — the ONLY vintage that exists; MIS retention ~31 d), and
ask whether the resulting measured curtailment-pressure frequency reproduces
the ERCOT-121 §4 shape: real 2025 wind curtailment peaks mid-afternoon
(h15–16, solar-flood congestion) while the keeper's model curtailment peaks in
the overnight economic troughs (h22–23; hod corr −0.079).

Vintage duty (ERCOT-160 README): the spine has no 2023–2025 vintage, so this
probe MEASURES ITS OWN per-year match rate against each target year's binding
station population — ERCOT-160's 186/191 and 50/50 were measured on a
different population (the CT fleet census) and are never inherited.

Rule 19 [R-ONE-MECH] context this probe informs: the keeper already arms
``ercot_wtx_curtailment_driver`` (pooled 2023–25 LZ_WEST+interface share,
broadcast identically to the West AND Panhandle zones) on top of the
endogenous Panhandle→North tie at measured PNHNDL limits
(``ercot_gtc_limits_measured``). The subsets below separate the signal the
pooled share mixes — interface GTC vs West-geo nodal vs Panhandle-geo nodal,
per year — which is exactly the attribution ERCOT-121 §4 flagged as opaque.

Committed inputs only:
- data/raw/iso-specific-transmission/SCEDBTCNP686_*_{2023,2024,2025}.parquet
- data/raw/ercot-network-model/Settlement_Points_*.csv  (NP4-160-SG spine)
- data/raw/hifld-substations/hifld_substations_TX.parquet (validation-grade
  coordinates; deterministic name tiers only, coverage REPORTED per subset)
- data/raw/ercot-hsl/ercot_<y>_hsl_hourly.parquet (+ _zonal_) — actual
  curtailment (the SHAPE TARGET, never an input to the pressure signal)
- data/raw/reference/ercot_wtx_curtailment_share.csv — the pooled share the
  keeper's driver actually applies (comparison baseline)
- results/calibration/ercot158_poolarm_B/hourly/class_hourly_<y>.parquet —
  keeper model dispatch (sanity anchor for the documented hod inversion)

Rule 22: years 2023–2025 only (the 2020–2022 NP6-86 archives are not read).
Output: printed report + results/calibration/ercot164_wpb_nodal_identification.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402
from market_sim.data.curtailment_share import (  # noqa: E402
    hour_axes,
    net_load_decile,
)
from scripts.data.build_ercot_hsl import _prevailing_to_standard  # noqa: E402
from scripts.data.derive_ercot_wtx_curtailment_share import (  # noqa: E402
    IN_SAMPLE_YEARS,
    _apply_table,
    _measured_net_load,
)

YEARS = IN_SAMPLE_YEARS  # (2023, 2024, 2025) — rule 22, no holdout year is read
KEEPER_BUNDLE = REPO / "results" / "calibration" / "ercot158_poolarm_B"
INTERFACE_GTCS = ("WESTEX", "PNHNDL")  # the corridor interfaces (endogenous ties)
CORRIDOR_KV = (138.0, 345.0)
WEST_LZ = "LZ_WEST"
PANHANDLE_LAT = 33.5  # zone_assignment._ercot_zone: Panhandle = lat>=33.5 & lon<-99.5
WEST_LON = -99.5
HOURS = 8760

_NP686_COLS = [
    "SCEDTimeStamp",
    "RepeatedHourFlag",
    "ConstraintName",
    "ShadowPrice",
    "Limit",
    "FromStation",
    "ToStation",
    "FromStationkV",
    "ToStationkV",
]

# Diurnal windows for the locus metric (ERCOT-121 §4): actual 2025 wind
# curtailment peaks h15–16; the keeper's model curtailment peaks h22–23.
AFTERNOON = tuple(range(13, 18))  # h13–17
OVERNIGHT = (21, 22, 23, 0, 1, 2)


def _norm(s: str) -> str:
    """Uppercase and strip every non-alphanumeric character."""
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def load_spine() -> pd.DataFrame:
    """NP4-160-SG Settlement_Points: SUBSTATION -> modal SETTLEMENT_LOAD_ZONE."""
    csvs = sorted((paths.RAW_DIR / "ercot-network-model").glob("Settlement_Points_*.csv"))
    if not csvs:
        raise FileNotFoundError("no Settlement_Points_*.csv under data/raw/ercot-network-model")
    sp = pd.read_csv(csvs[-1])
    sp = sp.dropna(subset=["SUBSTATION", "SETTLEMENT_LOAD_ZONE"])
    zone = (
        sp.groupby("SUBSTATION")["SETTLEMENT_LOAD_ZONE"]
        .agg(lambda s: s.mode().iloc[0])
        .reset_index()
    )
    zone["SUBSTATION"] = zone["SUBSTATION"].astype(str)
    return zone


def load_hifld_latlon() -> pd.DataFrame:
    """HIFLD TX substations with normalized name keys and coordinates."""
    h = pd.read_parquet(paths.RAW_DIR / "hifld-substations" / "hifld_substations_TX.parquet")
    h = h.dropna(subset=["NAME", "LATITUDE", "LONGITUDE"]).copy()
    h["norm"] = h["NAME"].map(_norm)
    # Drop the placeholder rows that carry no real name.
    h = h[~h["norm"].str.startswith(("UNKNOWN", "TAP"))]
    return h[["norm", "LATITUDE", "LONGITUDE"]]


def station_latlon(stations: list[str], hifld: pd.DataFrame) -> pd.DataFrame:
    """Deterministic tiered match of NP6-86 station codes to HIFLD coordinates.

    Tier 1: exact normalized equality.
    Tier 2: unique prefix — the station code (>=6 chars) is a prefix of exactly
    one HIFLD normalized name (VEALMOOR -> VEALMOOR..., TREADWEL -> TREADWELL).
    Anything else stays unmatched (reported, never guessed) — the WP-B build
    already showed contains-style fuzzy matching produces false positives.
    """
    by_norm = hifld.groupby("norm")[["LATITUDE", "LONGITUDE"]].mean()
    norms = by_norm.index.to_numpy()
    rows = []
    for st in stations:
        key = _norm(st)
        if key in by_norm.index:
            lat, lon = by_norm.loc[key]
            rows.append((st, lat, lon, "exact"))
            continue
        if len(key) >= 6:
            hits = [n for n in norms if n.startswith(key)]
            if len(hits) == 1:
                lat, lon = by_norm.loc[hits[0]]
                rows.append((st, lat, lon, "prefix"))
                continue
        rows.append((st, np.nan, np.nan, "unmatched"))
    return pd.DataFrame(rows, columns=["station", "lat", "lon", "tier"]).set_index("station")


def _geo_class(lat: float, lon: float) -> str:
    """Model-zone geography of a station (zone_assignment._ercot_zone bands)."""
    if np.isnan(lat) or np.isnan(lon):
        return "unresolved"
    if lon < WEST_LON:
        return "panhandle_geo" if lat >= PANHANDLE_LAT else "west_geo"
    return "outside_corridor"


def load_np686_year(year: int) -> pd.DataFrame:
    """One year's NP6-86 rows on the fixed CST clock (Feb 29 dropped)."""
    p = (
        paths.RAW_DIR
        / "iso-specific-transmission"
        / f"SCEDBTCNP686_SCEDBTCNP686_{year}.parquet"
    )
    df = pd.read_parquet(p, columns=_NP686_COLS)
    ts = _prevailing_to_standard(
        pd.to_datetime(df["SCEDTimeStamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce"),
        df["RepeatedHourFlag"] if "RepeatedHourFlag" in df.columns else None,
    )
    df = df.assign(ts=ts)
    df = df[
        df["ts"].notna()
        & (df["ts"].dt.year == year)
        & ~((df["ts"].dt.month == 2) & (df["ts"].dt.day == 29))
    ]
    fs = df["FromStation"]
    df = df.assign(
        is_station=fs.notna() & (fs.astype("string").str.strip() != ""),
        binding=df["ShadowPrice"] > 0,
    )
    return df


def hourly_freq(df: pd.DataFrame, mask: pd.Series) -> np.ndarray:
    """(8760,) fraction of the hour's SCED executions with >=1 masked row binding.

    Denominator: distinct SCEDTimeStamp over ALL rows that hour (any constraint
    active); hours with no NP6-86 rows are zero-congestion hours (dense zeros)
    — the ``curate_ercot_wtx_congestion`` convention.
    """
    cal = pd.date_range("2023-01-01", periods=HOURS, freq="h")
    pos = pd.Series(
        np.arange(HOURS, dtype="int64"),
        index=pd.MultiIndex.from_arrays([cal.month, cal.day, cal.hour]),
    )
    grp = [df["ts"].dt.month, df["ts"].dt.day, df["ts"].dt.hour]
    n_all = df.groupby(grp)["ts"].nunique()
    n_hit = df[mask & df["binding"]].groupby(grp)["ts"].nunique()
    out = np.zeros(HOURS)
    idx_all = pos.reindex(n_all.index).to_numpy()
    ok = ~np.isnan(idx_all)
    denom = np.zeros(HOURS)
    denom[idx_all[ok].astype(int)] = n_all.to_numpy()[ok]
    idx_hit = pos.reindex(n_hit.index).to_numpy()
    ok = ~np.isnan(idx_hit)
    hit = np.zeros(HOURS)
    hit[idx_hit[ok].astype(int)] = n_hit.to_numpy()[ok]
    np.divide(hit, denom, out=out, where=denom > 0)
    return out


def hourly_intensity(df: pd.DataFrame, mask: pd.Series) -> np.ndarray:
    """(8760,) mean distinct masked binding constraints per SCED execution."""
    cal = pd.date_range("2023-01-01", periods=HOURS, freq="h")
    pos = pd.Series(
        np.arange(HOURS, dtype="int64"),
        index=pd.MultiIndex.from_arrays([cal.month, cal.day, cal.hour]),
    )
    grp = [df["ts"].dt.month, df["ts"].dt.day, df["ts"].dt.hour]
    n_all = df.groupby(grp)["ts"].nunique()
    sub = df[mask & df["binding"]]
    # distinct (execution, constraint) pairs per hour / executions per hour
    pairs = (
        sub.drop_duplicates(subset=["ts", "ConstraintName"])
        .groupby([sub["ts"].dt.month, sub["ts"].dt.day, sub["ts"].dt.hour])["ts"]
        .size()
    )
    denom = np.zeros(HOURS)
    idx = pos.reindex(n_all.index).to_numpy()
    ok = ~np.isnan(idx)
    denom[idx[ok].astype(int)] = n_all.to_numpy()[ok]
    num = np.zeros(HOURS)
    idx = pos.reindex(pairs.index).to_numpy()
    ok = ~np.isnan(idx)
    num[idx[ok].astype(int)] = pairs.to_numpy()[ok]
    out = np.zeros(HOURS)
    np.divide(num, denom, out=out, where=denom > 0)
    return out


def hod_mean(series: np.ndarray) -> np.ndarray:
    """(24,) mean of ``series`` by hour-of-day."""
    hod, _ = hour_axes(len(series))
    return np.array([float(series[hod == h].mean()) for h in range(24)])


def corr(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation, NaN-safe."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def window_share(profile24: np.ndarray, hours: tuple[int, ...]) -> float:
    """Fraction of the 24-h profile's mass inside the given hod window."""
    tot = float(profile24.sum())
    return float(profile24[list(hours)].sum()) / tot if tot > 0 else float("nan")


def actual_curtailment(year: int) -> dict[str, np.ndarray]:
    """Hourly measured curtailment MW by tech (HSL − delivered, clipped >=0)."""
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    return {
        "wind": np.clip(
            hsl["wind_hsl_mw"].to_numpy() - hsl["wind_gen_mw"].to_numpy(), 0, None
        ),
        "solar": np.clip(
            hsl["solar_hsl_mw"].to_numpy() - hsl["solar_gen_mw"].to_numpy(), 0, None
        ),
    }


def zonal_curtailment(year: int) -> dict[str, np.ndarray]:
    """Per-region hourly wind curtailment MW where the zonal HSL file carries it."""
    p = paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_zonal_hourly.parquet"
    if not p.is_file():
        return {}
    z = pd.read_parquet(p)
    z = z[z["fuel"] == "wind"]
    out: dict[str, np.ndarray] = {}
    for region, g in z.groupby("region"):
        g = g.sort_values("hour")
        if len(g) != HOURS:
            g = g.set_index("hour").reindex(range(HOURS)).fillna(0.0)
            curt = np.clip(g["hsl_mw"].to_numpy() - g["gen_mw"].to_numpy(), 0, None)
        else:
            curt = np.clip(g["hsl_mw"].to_numpy() - g["gen_mw"].to_numpy(), 0, None)
        out[str(region)] = curt
    return out


def model_curtailment(year: int) -> dict[str, np.ndarray]:
    """Keeper model curtailment MW by tech from the committed hourly sidecar."""
    ch = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    out = {}
    for tech, col in (("wind", "wind_hsl_mw"), ("solar", "solar_hsl_mw")):
        disp = (
            ch[ch["klass"] == tech].sort_values("hour")["mw"].to_numpy()
        )
        out[tech] = np.clip(hsl[col].to_numpy() - disp, 0, None)
    return out


def main() -> None:  # noqa: C901 — one linear report
    spine = load_spine()
    sub2lz = dict(zip(spine["SUBSTATION"], spine["SETTLEMENT_LOAD_ZONE"]))
    hifld = load_hifld_latlon()
    share_table = pd.read_csv(paths.RAW_DIR / "reference" / "ercot_wtx_curtailment_share.csv")
    depth_wind, depth_solar = 0.1004, 0.1637  # keeper run_config (report context only)

    record: dict = {
        "probe": "ercot164_wpb_nodal_identification",
        "spine": "data/raw/ercot-network-model (NP4-160-SG, published 2026-07-29)",
        "years": list(YEARS),
        "per_year": {},
    }

    for year in YEARS:
        print(f"\n{'='*78}\n=== {year} ===")
        df = load_np686_year(year)
        b = df[df["binding"]]
        st_rows = b[b["is_station"]]
        n_st_rows = len(st_rows)

        # ---- A. MATCH RATE against THIS year's binding station population ----
        stations = (
            pd.concat([st_rows["FromStation"], st_rows["ToStation"]])
            .dropna()
            .astype(str)
            .str.strip()
        )
        stations = stations[stations != ""]
        st_weight = stations.value_counts()  # binding-row endpoint weight
        distinct = st_weight.index.tolist()
        resolved = [s for s in distinct if s in sub2lz]
        w_resolved = float(st_weight[resolved].sum()) / float(st_weight.sum())
        fz = st_rows["FromStation"].map(sub2lz)
        tz = st_rows["ToStation"].map(sub2lz)
        any_res = fz.notna() | tz.notna()
        both_res = fz.notna() & tz.notna()
        match = {
            "n_binding_station_rows": int(n_st_rows),
            "n_distinct_stations": len(distinct),
            "n_stations_resolved": len(resolved),
            "station_rate": len(resolved) / len(distinct),
            "endpoint_weight_rate": w_resolved,
            "row_any_endpoint_rate": float(any_res.mean()),
            "row_both_endpoint_rate": float(both_res.mean()),
        }
        print(
            f"A. spine match: {len(resolved)}/{len(distinct)} stations "
            f"({match['station_rate']:.3f}); binding-row any-endpoint "
            f"{match['row_any_endpoint_rate']:.3f}, both {match['row_both_endpoint_rate']:.3f}, "
            f"endpoint-weight {w_resolved:.3f}"
        )

        # ---- B. geography: HIFLD lat/lon for resolved corridor stations ----
        kv_ok = st_rows["FromStationkV"].isin(CORRIDOR_KV) | st_rows["ToStationkV"].isin(
            CORRIDOR_KV
        )
        west_any = (fz == WEST_LZ) | (tz == WEST_LZ)
        corridor_rows = st_rows[kv_ok & west_any]
        cor_st = (
            pd.concat(
                [
                    corridor_rows.loc[fz[corridor_rows.index] == WEST_LZ, "FromStation"],
                    corridor_rows.loc[tz[corridor_rows.index] == WEST_LZ, "ToStation"],
                ]
            )
            .astype(str)
            .str.strip()
        )
        cor_weight = cor_st.value_counts()
        geo = station_latlon(cor_weight.index.tolist(), hifld)
        geo["cls"] = [
            _geo_class(geo.loc[s, "lat"], geo.loc[s, "lon"]) for s in geo.index
        ]
        geo["weight"] = cor_weight
        wsum = float(cor_weight.sum())
        geo_w = geo.groupby("cls")["weight"].sum() / wsum
        print(
            "B. corridor(LZ_WEST) nodal endpoint-weight by geography: "
            + ", ".join(f"{k}={v:.3f}" for k, v in geo_w.items())
        )
        top = geo.sort_values("weight", ascending=False).head(15)
        print(top[["weight", "tier", "lat", "lon", "cls"]].to_string())

        # Panhandle-geo stations ANYWHERE (not just LZ_WEST): which LZ do they carry?
        all_geo = station_latlon(distinct, hifld)
        all_geo["lz"] = [sub2lz.get(s, "UNRESOLVED") for s in all_geo.index]
        all_geo["weight"] = st_weight
        ph = all_geo[
            (all_geo["lat"] >= PANHANDLE_LAT) & (all_geo["lon"] < WEST_LON)
        ]
        ph_lz = ph.groupby("lz")["weight"].sum().sort_values(ascending=False)
        print(
            "B2. panhandle-geo binding stations (HIFLD-matched only — coverage is "
            f"tiny and prefix-tier false positives are possible; unusable if it "
            f"disagrees with the LZ filter) LZ mix: {ph_lz.to_dict()}"
        )

        # ---- C. per-subset hourly pressure on the CST clock ----
        is_iface = df["ConstraintName"].isin(INTERFACE_GTCS) & ~df["is_station"]
        kv_all = df["FromStationkV"].isin(CORRIDOR_KV) | df["ToStationkV"].isin(CORRIDOR_KV)
        fz_all = df["FromStation"].map(sub2lz)
        tz_all = df["ToStation"].map(sub2lz)
        west_nodal_all = df["is_station"] & kv_all & (
            (fz_all == WEST_LZ) | (tz_all == WEST_LZ)
        )
        # geography split of the corridor-nodal rows via the matched endpoint(s)
        lat_f = df["FromStation"].map(geo["lat"])
        lon_f = df["FromStation"].map(geo["lon"])
        lat_t = df["ToStation"].map(geo["lat"])
        lon_t = df["ToStation"].map(geo["lon"])
        ph_end = ((lat_f >= PANHANDLE_LAT) & (lon_f < WEST_LON)) | (
            (lat_t >= PANHANDLE_LAT) & (lon_t < WEST_LON)
        )
        wg_end = ((lat_f < PANHANDLE_LAT) & (lon_f < WEST_LON)) | (
            (lat_t < PANHANDLE_LAT) & (lon_t < WEST_LON)
        )
        subsets = {
            "iface_gtc": is_iface,
            "iface_westex": (df["ConstraintName"] == "WESTEX") & ~df["is_station"],
            "iface_pnhndl": (df["ConstraintName"] == "PNHNDL") & ~df["is_station"],
            "corridor_nodal": west_nodal_all,
            "west_geo_nodal": west_nodal_all & wg_end & ~ph_end,
            "panhandle_geo_nodal": west_nodal_all & ph_end,
            "corridor_all": is_iface | west_nodal_all,
        }

        # Per-CONSTRAINT diurnal clustering of the corridor-nodal tail: the
        # nodal layer's native resolution axis is the ELEMENT, not geography.
        # Classify each corridor-nodal constraint by the hod placement of its
        # own binding weight, then aggregate the afternoon-heavy cluster as a
        # candidate signal of its own.
        nod = df[west_nodal_all & df["binding"]]
        nod_hod = nod["ts"].dt.hour
        per_con = (
            pd.DataFrame({"con": nod["ConstraintName"], "hod": nod_hod})
            .assign(
                aft=lambda x: x["hod"].isin(AFTERNOON),
                ovn=lambda x: x["hod"].isin(OVERNIGHT),
            )
            .groupby("con")
            .agg(n=("hod", "size"), aft_share=("aft", "mean"), ovn_share=("ovn", "mean"))
            .sort_values("n", ascending=False)
        )
        aft_cons = per_con[(per_con["aft_share"] > 0.30) & (per_con["n"] >= 200)]
        print(
            f"C. corridor-nodal constraints: {len(per_con)} distinct; "
            f"afternoon-heavy (aft>0.30, n>=200): {len(aft_cons)} carrying "
            f"{aft_cons['n'].sum() / max(per_con['n'].sum(), 1):.3f} of nodal binding weight"
        )
        print(per_con.head(12).round(3).to_string())
        subsets["nodal_afternoon_cluster"] = west_nodal_all & df["ConstraintName"].isin(
            aft_cons.index
        )
        freq = {k: hourly_freq(df, m) for k, m in subsets.items()}
        intensity = {"corridor_nodal": hourly_intensity(df, subsets["corridor_nodal"])}

        # ---- D. axes, actual + model curtailment, driver-as-armed share ----
        nl = _measured_net_load(year)
        dec = net_load_decile(nl)
        hod, season = hour_axes(HOURS)
        act = actual_curtailment(year)
        mod = model_curtailment(year)
        armed_share = _apply_table(share_table, year)  # the pooled share the driver applies

        act_wind_hod = np.array(
            [float(act["wind"][hod == h].sum()) for h in range(24)]
        )
        act_solar_hod = np.array(
            [float(act["solar"][hod == h].sum()) for h in range(24)]
        )
        mod_wind_hod = np.array(
            [float(mod["wind"][hod == h].sum()) for h in range(24)]
        )
        sanity = corr(act_wind_hod, mod_wind_hod)
        # The under-curtailment GAP itself (actual − model, positive part) —
        # the object the layer must explain. DIAGNOSTIC target only (like the
        # ERCOT-121 model-vs-reported reconciliation): the layer is identified
        # on measured binding frequency, never fit to this residual (rule 13).
        gap_wind = np.clip(act["wind"] - mod["wind"], 0, None)
        gap_solar = np.clip(act["solar"] - mod["solar"], 0, None)
        gap_wind_hod = np.array([float(gap_wind[hod == h].sum()) for h in range(24)])
        gap_solar_hod = np.array([float(gap_solar[hod == h].sum()) for h in range(24)])
        print(
            f"D. actual wind curt {act['wind'].sum()/1e6:.2f} TWh "
            f"(peak hod h{int(act_wind_hod.argmax())}); model (keeper sidecar) "
            f"{mod['wind'].sum()/1e6:.2f} TWh (peak h{int(mod_wind_hod.argmax())}); "
            f"hod corr model-vs-actual {sanity:+.3f}"
        )

        zc = zonal_curtailment(year)
        zonal_note = {}
        for region, curt in zc.items():
            prof = np.array([float(curt[hod == h].sum()) for h in range(24)])
            if prof.sum() > 0:
                zonal_note[region] = {
                    "curt_twh": round(float(curt.sum()) / 1e6, 3),
                    "peak_hod": int(prof.argmax()),
                    "afternoon_share": round(window_share(prof, AFTERNOON), 3),
                }

        # ---- E. the shape test ----
        results = {}
        print(
            f"E. shape targets: actual wind hod peak h{int(act_wind_hod.argmax())}, "
            f"afternoon share {window_share(act_wind_hod, AFTERNOON):.3f}, "
            f"overnight {window_share(act_wind_hod, OVERNIGHT):.3f}; "
            f"model afternoon {window_share(mod_wind_hod, AFTERNOON):.3f}, "
            f"overnight {window_share(mod_wind_hod, OVERNIGHT):.3f}"
        )
        print(
            f"   gap (actual−model, +part): wind {gap_wind.sum()/1e6:.2f} TWh "
            f"peak h{int(gap_wind_hod.argmax())} aft {window_share(gap_wind_hod, AFTERNOON):.3f}; "
            f"solar {gap_solar.sum()/1e6:.2f} TWh peak h{int(gap_solar_hod.argmax())}"
        )
        candidates = dict(freq)
        candidates["armed_pooled_share"] = armed_share
        candidates["corridor_nodal_intensity"] = intensity["corridor_nodal"]
        for name, series in candidates.items():
            prof = hod_mean(series)
            row = {
                "mean": round(float(series.mean()), 4),
                "hod_peak": int(prof.argmax()),
                "afternoon_share": round(window_share(prof, AFTERNOON), 4),
                "overnight_share": round(window_share(prof, OVERNIGHT), 4),
                "hod_corr_wind_curt": round(corr(prof, act_wind_hod), 3),
                "hod_corr_solar_curt": round(corr(prof, act_solar_hod), 3),
                "hod_corr_wind_gap": round(corr(prof, gap_wind_hod), 3),
                "hourly_corr_wind_curt": round(corr(series, act["wind"]), 3),
                "hourly_corr_solar_curt": round(corr(series, act["solar"]), 3),
                "hourly_corr_wind_gap": round(corr(series, gap_wind), 3),
                "hourly_corr_solar_gap": round(corr(series, gap_solar), 3),
                "hod_profile": [round(float(x), 4) for x in prof],
            }
            results[name] = row
            print(
                f"   {name:26s} mean={row['mean']:.3f} peak=h{row['hod_peak']:>2} "
                f"aft={row['afternoon_share']:.3f} ovn={row['overnight_share']:.3f} "
                f"hodCorr(wind)={row['hod_corr_wind_curt']:+.3f} "
                f"hodCorr(solar)={row['hod_corr_solar_curt']:+.3f} "
                f"gapHod(w)={row['hod_corr_wind_gap']:+.3f} "
                f"hourlyGap(w)={row['hourly_corr_wind_gap']:+.3f} "
                f"hourlyGap(s)={row['hourly_corr_solar_gap']:+.3f}"
            )

        # season-resolved hod placement for the two competing signal families
        # and the targets (the 2025 afternoon mode is expected spring-loaded).
        season_hod = {}
        for name, series in (
            ("iface_gtc", freq["iface_gtc"]),
            ("corridor_nodal", freq["corridor_nodal"]),
            ("actual_wind_curt", act["wind"]),
            ("gap_wind", gap_wind),
            ("actual_solar_curt", act["solar"]),
        ):
            tab = {}
            for s in range(4):
                m = season == s
                prof = np.array([float(series[m & (hod == h)].mean()) for h in range(24)])
                tab[["DJF", "MAM", "JJA", "SON"][s]] = {
                    "peak_hod": int(np.nanargmax(prof)),
                    "afternoon_share": round(window_share(np.nan_to_num(prof), AFTERNOON), 3),
                }
            season_hod[name] = tab
        for name, tab in season_hod.items():
            print(
                f"   season/hod {name:18s}: "
                + "  ".join(
                    f"{s}: peak h{v['peak_hod']:>2} aft {v['afternoon_share']:.3f}"
                    for s, v in tab.items()
                )
            )

        # ---- F. the rule-19 stack, timed: model Panhandle−North separation vs
        # measured PNHNDL binding. The keeper's endogenous tie binds thousands
        # of hours (ERCOT-121 §4) — but WHEN? If the model's separation sits
        # overnight while measured PNHNDL binding sits mid-morning/afternoon,
        # the stack's under-curtailment is a TIMING miss, not a depth miss.
        sysd = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        pz = sysd.pivot_table(index="hour", columns="zone", values="price")
        stack = {}
        for za, zb, label in (
            ("Panhandle", "North", "panhandle_minus_north"),
            ("West", "North", "west_minus_north"),
        ):
            if za not in pz.columns or zb not in pz.columns:
                continue
            sep = (pz[zb] - pz[za]).reindex(range(HOURS)).to_numpy()  # export cong: hub>gen zone
            sep_h = (np.abs(sep) > 1.0).astype(float)
            prof = hod_mean(sep_h)
            meas = hod_mean(freq["iface_pnhndl" if za == "Panhandle" else "iface_westex"])
            stack[label] = {
                "n_sep_hours": int(sep_h.sum()),
                "hod_peak": int(prof.argmax()),
                "afternoon_share": round(window_share(prof, AFTERNOON), 4),
                "overnight_share": round(window_share(prof, OVERNIGHT), 4),
                "hod_corr_vs_measured_iface": round(corr(prof, meas), 3),
                "hod_profile": [round(float(x), 4) for x in prof],
            }
            print(
                f"F. model {label}: {int(sep_h.sum())} sep-hours (|Δ|>$1), "
                f"peak h{int(prof.argmax())}, aft {window_share(prof, AFTERNOON):.3f} "
                f"ovn {window_share(prof, OVERNIGHT):.3f}, "
                f"hodCorr vs measured iface {corr(prof, meas):+.3f}"
            )

        # ---- G. PNHNDL enforcement structure (active coverage + limit by hod) —
        # the tie's non-active hours stand at the static rating (data.gtc), so
        # WHERE the measured enforcement concentrates is where the model's cap
        # deviates least from reality.
        gtc_rows = df[(df["ConstraintName"] == "PNHNDL") & ~df["is_station"]]
        grp = [gtc_rows["ts"].dt.month, gtc_rows["ts"].dt.day, gtc_rows["ts"].dt.hour]
        cal = pd.date_range("2023-01-01", periods=HOURS, freq="h")
        pos = pd.Series(
            np.arange(HOURS, dtype="int64"),
            index=pd.MultiIndex.from_arrays([cal.month, cal.day, cal.hour]),
        )
        active = np.zeros(HOURS, dtype=bool)
        limit_h = np.full(HOURS, np.nan)
        if len(gtc_rows):
            hourly_lim = gtc_rows.groupby(grp)["Limit"].mean()
            idx = pos.reindex(hourly_lim.index).to_numpy()
            ok = ~np.isnan(idx)
            active[idx[ok].astype(int)] = True
            limit_h[idx[ok].astype(int)] = hourly_lim.to_numpy()[ok]
        act_prof = hod_mean(active.astype(float))
        hod_arr, _ = hour_axes(HOURS)
        aft_m = np.isin(hod_arr, AFTERNOON) & active
        ovn_m = np.isin(hod_arr, OVERNIGHT) & active
        pnh = {
            "active_hours": int(active.sum()),
            "active_hod_peak": int(act_prof.argmax()),
            "active_afternoon_share": round(window_share(act_prof, AFTERNOON), 4),
            "limit_mean_afternoon_active": (
                round(float(np.nanmean(limit_h[aft_m])), 0) if aft_m.any() else None
            ),
            "limit_mean_overnight_active": (
                round(float(np.nanmean(limit_h[ovn_m])), 0) if ovn_m.any() else None
            ),
        }
        print(
            f"G. PNHNDL active (in SCED set): {pnh['active_hours']} h, "
            f"hod peak h{pnh['active_hod_peak']}, aft {pnh['active_afternoon_share']:.3f}; "
            f"limit_mean active aft/ovn = "
            f"{pnh['limit_mean_afternoon_active']}/{pnh['limit_mean_overnight_active']} MW"
        )

        # decile x season marginals for the nodal subsets (identification depth)
        marginals = {}
        for name in ("corridor_nodal", "west_geo_nodal", "panhandle_geo_nodal", "iface_gtc"):
            s = freq[name]
            tbl = (
                pd.DataFrame({"dec": dec, "season": season, "f": s})
                .groupby(["dec", "season"])["f"]
                .mean()
                .round(4)
            )
            marginals[name] = {f"{d}_{se}": v for (d, se), v in tbl.items()}

        record["per_year"][year] = {
            "match": match,
            "corridor_geo_weight": {k: round(float(v), 4) for k, v in geo_w.items()},
            "corridor_top_stations": [
                {
                    "station": s,
                    "weight": int(top.loc[s, "weight"]),
                    "tier": top.loc[s, "tier"],
                    "cls": top.loc[s, "cls"],
                }
                for s in top.index
            ],
            "panhandle_geo_lz_mix": {k: int(v) for k, v in ph_lz.items()},
            "actual": {
                "wind_curt_twh": round(float(act["wind"].sum()) / 1e6, 3),
                "solar_curt_twh": round(float(act["solar"].sum()) / 1e6, 3),
                "wind_hod_peak": int(act_wind_hod.argmax()),
                "wind_afternoon_share": round(window_share(act_wind_hod, AFTERNOON), 4),
                "wind_overnight_share": round(window_share(act_wind_hod, OVERNIGHT), 4),
                "wind_hod_profile_gwh": [round(float(x) / 1e3, 2) for x in act_wind_hod],
                "solar_hod_peak": int(act_solar_hod.argmax()),
            },
            "model_keeper": {
                "wind_curt_twh": round(float(mod["wind"].sum()) / 1e6, 3),
                "solar_curt_twh": round(float(mod["solar"].sum()) / 1e6, 3),
                "wind_hod_peak": int(mod_wind_hod.argmax()),
                "wind_afternoon_share": round(window_share(mod_wind_hod, AFTERNOON), 4),
                "wind_overnight_share": round(window_share(mod_wind_hod, OVERNIGHT), 4),
                "hod_corr_vs_actual": round(sanity, 3),
                "wind_hod_profile_gwh": [round(float(x) / 1e3, 2) for x in mod_wind_hod],
            },
            "zonal_actual_wind": zonal_note,
            "gap": {
                "wind_twh": round(float(gap_wind.sum()) / 1e6, 3),
                "solar_twh": round(float(gap_solar.sum()) / 1e6, 3),
                "wind_hod_peak": int(gap_wind_hod.argmax()),
                "wind_afternoon_share": round(window_share(gap_wind_hod, AFTERNOON), 4),
                "wind_hod_profile_gwh": [round(float(x) / 1e3, 2) for x in gap_wind_hod],
            },
            "nodal_constraint_clustering": {
                "n_constraints": int(len(per_con)),
                "n_afternoon_heavy": int(len(aft_cons)),
                "afternoon_heavy_weight_share": round(
                    float(aft_cons["n"].sum()) / max(float(per_con["n"].sum()), 1.0), 4
                ),
                "top_constraints": [
                    {
                        "con": c,
                        "n": int(per_con.loc[c, "n"]),
                        "aft_share": round(float(per_con.loc[c, "aft_share"]), 3),
                        "ovn_share": round(float(per_con.loc[c, "ovn_share"]), 3),
                    }
                    for c in per_con.head(12).index
                ],
            },
            "season_hod": season_hod,
            "model_zone_separation": stack,
            "pnhndl_enforcement": pnh,
            "signals": results,
            "decile_season_marginals": marginals,
        }

    out = REPO / "results" / "calibration" / "ercot164_wpb_nodal_identification.json"
    out.write_text(json.dumps(record, indent=1))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
