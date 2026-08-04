"""ercot-165 Phase 0 — can the WP-B curtailment-pressure share be UNPOOLED by
diurnal family, identifiably and leave-one-year-out? No LP, committed data only.

The FINDING-ercot164 charter (§6.1) names the object: replace the single pooled
``congestion_share`` with per-family shares on the same (net-load decile x
hour-of-day x season) axis, family membership derived per year from each
element's own binding-hod placement. This probe answers the two questions that
must PASS before anything is built (the charter's Phase-0 kill gate):

1. **Is the split identifiable without a tuned threshold?** The rule used here
   is a pure LIFT test against the measured SCED-execution exposure, so the
   family boundary is the NULL, not a knob:

       day_share(c)   = share of element c's binding executions in h9-17
       exposure_day   = share of ALL SCED executions in h9-17 (measured/yr)
       family(c)      = "D" if day_share(c) > exposure_day else "N"

   An element joins family-D exactly when it binds MORE in daytime hours than
   its own exposure predicts. No cutoff, no minimum-n, no per-year tuning —
   contrast the ercot-164 probe's exploratory ``aft>0.30 & n>=200`` heuristic,
   which this replaces (rule 23: a source-data derive, frozen against
   residuals).

2. **Does membership generalize?** LOYO: derive membership on two years, apply
   it to the held-out year, and ask whether the resulting family shares
   reproduce the held-out year's OWN-membership family shares (hourly corr,
   hod-profile corr, level bias) — the anti-residual gate the pooled table
   already carries.

Also measured here, for the charter's component 2 (the Panhandle interface's
ONE owner, rule 19): the PNHNDL enforcement-incidence structure — active-set
hours, the measured ``limit_mean`` level when active vs the static 2,680 MW
stand-in ``data.gtc`` fills non-active hours with, split by hour-of-day. This
is the rule-14 misalignment evidence for arm A's stand-in reconciliation.

Vintage duty: this probe MEASURES ITS OWN station-resolution match rate against
each year's binding-station population, on the SAME spine the production
curation path uses (``data/raw/ercot-settlement-points`` NP4-160-SG bundle) —
ERCOT-164's 90.1-91.3 % / 92.5-94.4 % were measured on the
``ercot-network-model`` spine and a different population, and are NOT inherited.

Rule 22: years 2023-2025 only; the 2020-2022 NP6-86 archives are not read.
Rule 13: the actual-minus-model curtailment gap appears ONLY as a diagnostic
shape target (the ERCOT-121 reconciliation pattern) — no family, threshold or
share is fit to it.

Output: printed report + results/calibration/ercot165_family_split_phase0.json
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from market_sim.data.curtailment_share import hour_axes  # noqa: E402
from scripts.data.build_ercot_hsl import _prevailing_to_standard  # noqa: E402
from scripts.data.curate_ercot_wtx_congestion import (  # noqa: E402
    CORRIDOR_KV,
    WEST_LOAD_ZONE,
    load_substation_zone,
)

YEARS = (2023, 2024, 2025)  # rule 22 — no holdout year is read
HOURS = 8760
KEEPER_BUNDLE = REPO_ROOT / "results" / "calibration" / "ercot158_poolarm_B"
OUT = REPO_ROOT / "results" / "calibration" / "ercot165_family_split_phase0.json"

# Diurnal windows (ERCOT-164 §3 convention, kept identical for comparability).
DAYTIME = tuple(range(9, 18))  # h9-17 — the family-split exposure window
AFTERNOON = tuple(range(13, 18))  # h13-17
OVERNIGHT = (21, 22, 23, 0, 1, 2)

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


def load_np686_year(year: int) -> pd.DataFrame:
    """One year's NP6-86 rows on the fixed non-leap CST clock.

    Mirrors ``curate_ercot_wtx_congestion`` exactly: the main per-year archive
    plus the DST supplement (``_xhr_``) and retry side-files, deduplicated,
    Central-Prevailing stamps converted to the fixed CST model clock, Feb 29
    dropped.
    """
    d = paths.RAW_DIR / "iso-specific-transmission"
    files = sorted(d.glob(f"SCEDBTCNP686_SCEDBTCNP686_*{year}.parquet"))
    frames = []
    for p in files:
        import pyarrow.parquet as pq

        have = set(pq.ParquetFile(p).schema.names)
        frames.append(pd.read_parquet(p, columns=[c for c in _NP686_COLS if c in have]))
    df = pd.concat(frames, ignore_index=True).drop_duplicates(ignore_index=True)
    ts = _prevailing_to_standard(
        pd.to_datetime(
            df["SCEDTimeStamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
        ),
        df["RepeatedHourFlag"] if "RepeatedHourFlag" in df.columns else None,
    )
    df = df.assign(ts=ts)
    df = df[
        df["ts"].notna()
        & (df["ts"].dt.year == year)
        & ~((df["ts"].dt.month == 2) & (df["ts"].dt.day == 29))
    ]
    fs = df["FromStation"]
    return df.assign(
        is_station=fs.notna() & (fs.astype("string").str.strip() != ""),
        binding=df["ShadowPrice"] > 0,
    )


def corridor_masks(df: pd.DataFrame, sub2zone: dict[str, str]) -> dict[str, pd.Series]:
    """West-corridor row masks: the nodal tail and each export GTC separately."""
    fz = df["FromStation"].map(sub2zone)
    tz = df["ToStation"].map(sub2zone)
    kv = df["FromStationkV"].isin(CORRIDOR_KV) | df["ToStationkV"].isin(CORRIDOR_KV)
    nodal = kv & ((fz == WEST_LOAD_ZONE) | (tz == WEST_LOAD_ZONE))
    return {
        "nodal": nodal,
        "westex": (df["ConstraintName"] == "WESTEX") & ~df["is_station"],
        "pnhndl": (df["ConstraintName"] == "PNHNDL") & ~df["is_station"],
    }


def _hour_pos() -> pd.Series:
    """(month, day, hour) -> 0..8759 on the non-leap model clock."""
    cal = pd.date_range("2023-01-01", periods=HOURS, freq="h")
    return pd.Series(
        np.arange(HOURS, dtype="int64"),
        index=pd.MultiIndex.from_arrays([cal.month, cal.day, cal.hour]),
    )


def hourly_union_share(df: pd.DataFrame, mask: pd.Series) -> np.ndarray:
    """(8760,) fraction of the hour's SCED executions with >=1 masked row binding.

    The ``curate_ercot_wtx_congestion`` convention: denominator is distinct
    executions that hour over ALL constraints; hours with no archive coverage
    are dense zeros.
    """
    pos = _hour_pos()
    grp = [df["ts"].dt.month, df["ts"].dt.day, df["ts"].dt.hour]
    n_all = df.groupby(grp)["ts"].nunique()
    n_hit = df[mask & df["binding"]].groupby(grp)["ts"].nunique()
    denom = np.zeros(HOURS)
    idx = pos.reindex(n_all.index).to_numpy()
    ok = ~np.isnan(idx)
    denom[idx[ok].astype(int)] = n_all.to_numpy()[ok]
    hit = np.zeros(HOURS)
    idx = pos.reindex(n_hit.index).to_numpy()
    ok = ~np.isnan(idx)
    hit[idx[ok].astype(int)] = n_hit.to_numpy()[ok]
    out = np.zeros(HOURS)
    np.divide(hit, denom, out=out, where=denom > 0)
    return out


def exposure_day_share(df: pd.DataFrame) -> float:
    """Measured share of the year's SCED executions falling in h9-17.

    The NULL the family lift test is taken against — so the family boundary is
    the data's own exposure, not a chosen threshold.
    """
    ex = df.drop_duplicates(subset=["ts"])
    return float(ex["ts"].dt.hour.isin(DAYTIME).mean())


def element_families(
    df: pd.DataFrame, nodal: pd.Series, exposure: float
) -> pd.DataFrame:
    """Per-element binding-hod census + the lift family assignment.

    Returns one row per corridor-nodal ``ConstraintName`` with its binding
    execution count, daytime/afternoon/overnight shares, the daytime lift and
    the resulting family (``D`` daytime / ``N`` overnight).
    """
    sub = df[nodal & df["binding"]].drop_duplicates(subset=["ts", "ConstraintName"])
    hod = sub["ts"].dt.hour
    per = (
        pd.DataFrame(
            {
                "con": sub["ConstraintName"],
                "day": hod.isin(DAYTIME),
                "aft": hod.isin(AFTERNOON),
                "ovn": hod.isin(OVERNIGHT),
            }
        )
        .groupby("con")
        .agg(
            n=("day", "size"),
            day_share=("day", "mean"),
            aft_share=("aft", "mean"),
            ovn_share=("ovn", "mean"),
        )
        .sort_values("n", ascending=False)
    )
    per["lift"] = per["day_share"] / exposure
    per["family"] = np.where(per["lift"] > 1.0, "D", "N")
    return per


def hod_mean(series: np.ndarray) -> np.ndarray:
    """(24,) mean of an 8760 series by hour-of-day."""
    hod, _ = hour_axes(len(series))
    return np.array([float(series[hod == h].mean()) for h in range(24)])


def corr(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation, NaN-safe (returns 0.0 on a degenerate input)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def window_share(profile24: np.ndarray, hours: tuple[int, ...]) -> float:
    """Share of a 24-point hod profile's mass falling in ``hours``."""
    tot = float(profile24.sum())
    return float(profile24[list(hours)].sum() / tot) if tot > 0 else 0.0


def actual_curtailment(year: int) -> dict[str, np.ndarray]:
    """Measured HSL-minus-delivered wind/solar curtailment (the SHAPE target)."""
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


def hsl_potential(year: int) -> dict[str, np.ndarray]:
    """Measured system wind/solar HSL potential, plus LZ_WEST wind separately.

    ``hsl * share`` is the quantity the ceiling actually removes from the LP's
    renewable upper bound (and is the depth's own denominator), so the
    HSL-WEIGHTED share profile — not the bare share profile — is the shape the
    driver imposes on curtailment.
    """
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    z = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_zonal_hourly.parquet"
    )
    zw = z[(z["fuel"] == "wind") & (z["region"] == "lz_west")].set_index("hour")
    return {
        "wind": hsl["wind_hsl_mw"].to_numpy(),
        "solar": hsl["solar_hsl_mw"].to_numpy(),
        "wind_lzwest": zw["hsl_mw"].reindex(range(HOURS)).fillna(0.0).to_numpy(),
        "wind_lzwest_curt": np.clip(
            (zw["hsl_mw"] - zw["gen_mw"]).reindex(range(HOURS)).fillna(0.0).to_numpy(),
            0,
            None,
        ),
    }


def model_curtailment(year: int) -> dict[str, np.ndarray] | None:
    """Keeper model curtailment MW by tech from the committed hourly sidecar.

    Same construction as the ercot-164 probe: measured HSL potential minus the
    keeper's P1 dispatched MW for the tech.
    """
    p = KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet"
    if not p.is_file():
        return None
    ch = pd.read_parquet(p)
    ch = ch[ch["pass"] == "P1"]
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    out = {}
    for tech, col in (("wind", "wind_hsl_mw"), ("solar", "solar_hsl_mw")):
        disp = ch[ch["klass"] == tech].sort_values("hour")["mw"].to_numpy()
        if len(disp) != HOURS:
            return None
        out[tech] = np.clip(hsl[col].to_numpy() - disp, 0, None)
    return out


def pnhndl_enforcement(df: pd.DataFrame, masks: dict[str, pd.Series]) -> dict:
    """Measured PNHNDL enforcement-incidence + limit level, by hour-of-day.

    The rule-14 evidence for the charter's component 2: ``data.gtc`` fills
    every hour PNHNDL was NOT in SCED's active set with the link's static
    2,680 MW derived rating. If the measured enforced limit is systematically
    ABOVE that rating, the static fill over-constrains the corridor in exactly
    the hours the real constraint was NOT enforced.
    """
    pos = _hour_pos()
    sub = df[masks["pnhndl"]]
    if sub.empty or "Limit" not in sub.columns:
        return {}
    grp = [sub["ts"].dt.month, sub["ts"].dt.day, sub["ts"].dt.hour]
    lim = sub.groupby(grp)["Limit"].mean()
    hourly = np.full(HOURS, np.nan)
    idx = pos.reindex(lim.index).to_numpy()
    ok = ~np.isnan(idx)
    hourly[idx[ok].astype(int)] = lim.to_numpy()[ok]
    active = ~np.isnan(hourly)
    hod, _ = hour_axes(HOURS)
    by_hod = {
        int(h): {
            "active_hours": int(active[hod == h].sum()),
            "limit_mean": (
                float(np.nanmean(hourly[(hod == h) & active]))
                if active[hod == h].any()
                else None
            ),
        }
        for h in range(24)
    }
    bind = df[masks["pnhndl"] & df["binding"]]
    return {
        "active_hours": int(active.sum()),
        "limit_mean_active": float(np.nanmean(hourly[active])),
        "limit_p50_active": float(np.nanmedian(hourly[active])),
        "limit_min_active": float(np.nanmin(hourly[active])),
        "limit_p10_active": float(np.nanpercentile(hourly[active], 10)),
        "static_stand_in_mw": 2680.0,
        "limit_mean_active_afternoon": (
            float(np.nanmean(hourly[active & np.isin(hod, AFTERNOON)]))
            if (active & np.isin(hod, AFTERNOON)).any()
            else None
        ),
        "limit_mean_active_overnight": (
            float(np.nanmean(hourly[active & np.isin(hod, OVERNIGHT)]))
            if (active & np.isin(hod, OVERNIGHT)).any()
            else None
        ),
        "frac_active_hours_limit_above_static": float((hourly[active] > 2680.0).mean()),
        "binding_rows": int(len(bind)),
        "by_hod": by_hod,
    }


def main() -> None:  # noqa: C901 — one linear report
    """Run the Phase-0 identification report and write the JSON record."""
    sub2zone = load_substation_zone(paths.RAW_DIR)
    report: dict = {
        "probe": "ercot165_family_split_phase0",
        "keeper": "2026-08-03-ercot158-pool-arm",
        "spine": "data/raw/ercot-settlement-points (NP4-160-SG, production curate path)",
        "family_rule": (
            "family(c) = D iff day_share(c) > exposure_day(year); "
            "day window h9-17; no threshold, no minimum-n"
        ),
        "years": {},
    }
    members: dict[int, pd.DataFrame] = {}
    frames: dict[int, pd.DataFrame] = {}
    maskset: dict[int, dict[str, pd.Series]] = {}

    for year in YEARS:
        print(f"\n{'=' * 72}\n{year}\n{'=' * 72}")
        df = load_np686_year(year)
        masks = corridor_masks(df, sub2zone)
        frames[year], maskset[year] = df, masks

        # --- vintage duty: OUR OWN station match rate on OUR OWN population ---
        st_rows = df[df["is_station"] & df["binding"]]
        stations = pd.unique(
            pd.concat([st_rows["FromStation"], st_rows["ToStation"]]).dropna()
        )
        resolved = sum(1 for s in stations if str(s) in sub2zone)
        ep = pd.concat([st_rows["FromStation"], st_rows["ToStation"]]).dropna()
        ep_rate = float(ep.map(lambda s: str(s) in sub2zone).mean())
        match = {
            "binding_station_rows": int(len(st_rows)),
            "distinct_stations": int(len(stations)),
            "stations_resolved": int(resolved),
            "station_resolve_rate": float(resolved / max(len(stations), 1)),
            "endpoint_weight_rate": ep_rate,
        }
        print(
            f"A. match rate (this spine, this population): "
            f"{resolved}/{len(stations)} stations "
            f"({match['station_resolve_rate']:.3f}), endpoint weight {ep_rate:.3f}"
        )

        # --- the family split ---
        exposure = exposure_day_share(df)
        per = element_families(df, masks["nodal"], exposure)
        members[year] = per
        wD = float(per.loc[per["family"] == "D", "n"].sum())
        wN = float(per.loc[per["family"] == "N", "n"].sum())
        print(
            f"B. exposure_day (h9-17 share of SCED executions) = {exposure:.4f}\n"
            f"   corridor-nodal elements: {len(per)} "
            f"(D {int((per['family'] == 'D').sum())} / "
            f"N {int((per['family'] == 'N').sum())}); "
            f"binding weight D {wD / max(wD + wN, 1):.3f} / N {wN / max(wD + wN, 1):.3f}"
        )
        print(per.head(12).round(3).to_string())

        # interface GTC shapes, under the SAME rule (the WESTEX design call)
        iface_fam = {}
        for name in ("westex", "pnhndl"):
            b = df[masks[name] & df["binding"]].drop_duplicates(subset=["ts"])
            if b.empty:
                continue
            hh = b["ts"].dt.hour
            ds = float(hh.isin(DAYTIME).mean())
            iface_fam[name] = {
                "n": int(len(b)),
                "day_share": ds,
                "aft_share": float(hh.isin(AFTERNOON).mean()),
                "ovn_share": float(hh.isin(OVERNIGHT).mean()),
                "lift": ds / exposure,
                "family": "D" if ds / exposure > 1.0 else "N",
            }
            print(
                f"   iface {name.upper()}: n={len(b)} day={ds:.3f} "
                f"lift={ds / exposure:.3f} -> family {iface_fam[name]['family']}"
            )

        # --- per-family hourly union shares ---
        fam_masks = {
            "D": masks["nodal"]
            & df["ConstraintName"].isin(per.index[per["family"] == "D"]),
            "N": masks["nodal"]
            & df["ConstraintName"].isin(per.index[per["family"] == "N"]),
        }
        # WESTEX joins the family its own measured shape puts it in (charter §6.1).
        if "westex" in iface_fam:
            fam_masks[iface_fam["westex"]["family"]] = (
                fam_masks[iface_fam["westex"]["family"]] | masks["westex"]
            )
        series = {
            "D": hourly_union_share(df, fam_masks["D"]),
            "N": hourly_union_share(df, fam_masks["N"]),
            "pnhndl": hourly_union_share(df, masks["pnhndl"]),
            "pooled": hourly_union_share(
                df, masks["nodal"] | masks["westex"] | masks["pnhndl"]
            ),
        }

        act = actual_curtailment(year)
        mod = model_curtailment(year)
        hod, _ = hour_axes(HOURS)
        act_w = np.array([float(act["wind"][hod == h].sum()) for h in range(24)])
        act_s = np.array([float(act["solar"][hod == h].sum()) for h in range(24)])
        gap_w = None
        if mod is not None:
            g = np.clip(act["wind"] - mod["wind"], 0, None)
            gap_w = np.array([float(g[hod == h].sum()) for h in range(24)])

        sig = {}
        print(
            "C. signal    mean   peak   aft    ovn    day    gapHod  vsActWind vsActSolar"
        )
        for k, s in series.items():
            prof = hod_mean(s)
            row = {
                "mean": float(s.mean()),
                "peak_hod": int(np.argmax(prof)),
                "aft": window_share(prof, AFTERNOON),
                "ovn": window_share(prof, OVERNIGHT),
                "day": window_share(prof, DAYTIME),
                "hod_profile": [float(x) for x in prof],
                "gap_hod_corr": (corr(prof, gap_w) if gap_w is not None else None),
                "corr_act_wind": corr(prof, act_w),
                "corr_act_solar": corr(prof, act_s),
            }
            sig[k] = row
            print(
                f"   {k:8s} {row['mean']:.3f}  h{row['peak_hod']:<3d} "
                f"{row['aft']:.3f}  {row['ovn']:.3f}  {row['day']:.3f}  "
                f"{(row['gap_hod_corr'] if row['gap_hod_corr'] is not None else float('nan')):+.3f}"
                f"   {row['corr_act_wind']:+.3f}    {row['corr_act_solar']:+.3f}"
            )
        # The unpooled SUM — the pressure the driver would apply (additive over
        # families, NOT the saturating OR the pooled table takes).
        for combo, keys in (("D+N", ("D", "N")), ("D+N+PNHNDL", ("D", "N", "pnhndl"))):
            s = sum(series[k] for k in keys)
            prof = hod_mean(s)
            sig[combo] = {
                "mean": float(s.mean()),
                "peak_hod": int(np.argmax(prof)),
                "aft": window_share(prof, AFTERNOON),
                "ovn": window_share(prof, OVERNIGHT),
                "day": window_share(prof, DAYTIME),
                "hod_profile": [float(x) for x in prof],
                "gap_hod_corr": (corr(prof, gap_w) if gap_w is not None else None),
                "corr_act_wind": corr(prof, act_w),
                "corr_act_solar": corr(prof, act_s),
            }
            r = sig[combo]
            print(
                f"   {combo:8s} {r['mean']:.3f}  h{r['peak_hod']:<3d} "
                f"{r['aft']:.3f}  {r['ovn']:.3f}  {r['day']:.3f}  "
                f"{(r['gap_hod_corr'] if r['gap_hod_corr'] is not None else float('nan')):+.3f}"
                f"   {r['corr_act_wind']:+.3f}    {r['corr_act_solar']:+.3f}"
            )

        # --- E. the HSL-WEIGHTED bound reduction (the shape the ceiling imposes)
        # The bare share profile is NOT what the driver does to curtailment: the
        # ceiling removes ``depth * share(t) * HSL(t)`` MW from the renewable
        # bound, which is also the depth's own denominator. Normalizing that
        # profile gives the curtailment hod shape the variant predicts, and IS
        # the object to compare against the measured curtailment shape.
        pot = hsl_potential(year)
        act_lzw = np.array(
            [float(pot["wind_lzwest_curt"][hod == h].sum()) for h in range(24)]
        )
        eff = {}
        print(
            "E. HSL-weighted bound reduction (the imposed curtailment shape)\n"
            "   variant   tech    peak  aft    ovn    day    vsAct  vsGap  vsActLZW"
        )
        combos = {
            "pooled": series["pooled"],
            "D": series["D"],
            "N": series["N"],
            "pnhndl": series["pnhndl"],
            "D+N": series["D"] + series["N"],
            "D+N+PNHNDL": series["D"] + series["N"] + series["pnhndl"],
        }
        for name, s in combos.items():
            for tech, act_prof in (("wind", act_w), ("solar", act_s)):
                bite = s * pot[tech]
                prof = np.array([float(bite[hod == h].sum()) for h in range(24)])
                row = {
                    "peak_hod": int(np.argmax(prof)),
                    "aft": window_share(prof, AFTERNOON),
                    "ovn": window_share(prof, OVERNIGHT),
                    "day": window_share(prof, DAYTIME),
                    "corr_actual": corr(prof, act_prof),
                    "corr_gap": (corr(prof, gap_w) if gap_w is not None else None),
                    "corr_actual_lzwest_wind": (
                        corr(prof, act_lzw) if tech == "wind" else None
                    ),
                    "hod_profile": [float(x) for x in prof],
                }
                eff[f"{name}|{tech}"] = row
                gapv = row["corr_gap"] if row["corr_gap"] is not None else float("nan")
                lzw = (
                    row["corr_actual_lzwest_wind"]
                    if row["corr_actual_lzwest_wind"] is not None
                    else float("nan")
                )
                print(
                    f"   {name:10s} {tech:6s} h{row['peak_hod']:<3d} "
                    f"{row['aft']:.3f}  {row['ovn']:.3f}  {row['day']:.3f}  "
                    f"{row['corr_actual']:+.3f} {gapv:+.3f} {lzw:+.3f}"
                )
        act_prof_report = {
            "actual_wind_hod": [float(x) for x in act_w],
            "actual_solar_hod": [float(x) for x in act_s],
            "actual_lzwest_wind_hod": [float(x) for x in act_lzw],
            "actual_wind_aft": window_share(act_w, AFTERNOON),
            "actual_wind_ovn": window_share(act_w, OVERNIGHT),
            "actual_wind_day": window_share(act_w, DAYTIME),
            "actual_lzwest_wind_aft": window_share(act_lzw, AFTERNOON),
            "actual_lzwest_wind_ovn": window_share(act_lzw, OVERNIGHT),
            "actual_lzwest_wind_day": window_share(act_lzw, DAYTIME),
        }
        print(
            f"   ACTUAL     wind          "
            f"{act_prof_report['actual_wind_aft']:.3f}  "
            f"{act_prof_report['actual_wind_ovn']:.3f}  "
            f"{act_prof_report['actual_wind_day']:.3f}   (system)\n"
            f"   ACTUAL     lzw_wind      "
            f"{act_prof_report['actual_lzwest_wind_aft']:.3f}  "
            f"{act_prof_report['actual_lzwest_wind_ovn']:.3f}  "
            f"{act_prof_report['actual_lzwest_wind_day']:.3f}   (LZ_WEST corridor)"
        )

        pn = pnhndl_enforcement(df, masks)
        if pn:
            print(
                f"D. PNHNDL enforcement: active {pn['active_hours']} h; "
                f"limit mean {pn['limit_mean_active']:.0f} MW "
                f"(p10 {pn['limit_p10_active']:.0f}, min {pn['limit_min_active']:.0f}) "
                f"vs static stand-in 2680; "
                f"{pn['frac_active_hours_limit_above_static']:.3f} of active hours "
                f"above the stand-in"
            )

        report["years"][str(year)] = {
            "match_rate": match,
            "exposure_day": exposure,
            "n_elements": int(len(per)),
            "n_family_D": int((per["family"] == "D").sum()),
            "n_family_N": int((per["family"] == "N").sum()),
            "weight_family_D": float(wD / max(wD + wN, 1)),
            "interface_families": iface_fam,
            "signals": sig,
            "hsl_weighted_bite": eff,
            "actual_profiles": act_prof_report,
            "pnhndl_enforcement": pn,
            "top_elements": per.head(25).round(4).reset_index().to_dict("records"),
        }

    # ---------------- LOYO: does membership generalize? ----------------
    print(
        f"\n{'=' * 72}\nLOYO — train membership on 2 years, apply to the held-out\n{'=' * 72}"
    )
    loyo = {}
    for hold in YEARS:
        train = [y for y in YEARS if y != hold]
        # pooled train membership: element -> family by pooled daytime lift
        pooled = pd.concat([members[y][["n", "day_share"]] for y in train])
        agg = (
            pooled.assign(day_n=lambda x: x["n"] * x["day_share"])
            .groupby(level=0)
            .sum()
        )
        exp_train = float(
            np.mean([report["years"][str(y)]["exposure_day"] for y in train])
        )
        agg["day_share"] = agg["day_n"] / agg["n"]
        agg["family"] = np.where(agg["day_share"] / exp_train > 1.0, "D", "N")

        df, masks = frames[hold], maskset[hold]
        own = members[hold]
        shared = own.index.intersection(agg.index)
        agree = float(
            (
                own.loc[shared, "family"].to_numpy()
                == agg.loc[shared, "family"].to_numpy()
            ).mean()
        )
        w = own.loc[shared, "n"].to_numpy()
        agree_w = float(
            (
                (
                    own.loc[shared, "family"].to_numpy()
                    == agg.loc[shared, "family"].to_numpy()
                )
                * w
            ).sum()
            / max(w.sum(), 1)
        )
        cover = float(own.loc[shared, "n"].sum() / max(own["n"].sum(), 1))

        res = {
            "membership_agreement": agree,
            "weighted_agreement": agree_w,
            "held_out_weight_covered": cover,
            "families": {},
        }
        for fam in ("D", "N"):
            pred_mask = masks["nodal"] & df["ConstraintName"].isin(
                agg.index[agg["family"] == fam]
            )
            own_mask = masks["nodal"] & df["ConstraintName"].isin(
                own.index[own["family"] == fam]
            )
            pred = hourly_union_share(df, pred_mask)
            actual = hourly_union_share(df, own_mask)
            res["families"][fam] = {
                "hourly_corr": corr(pred, actual),
                "hod_corr": corr(hod_mean(pred), hod_mean(actual)),
                "level_bias": float(pred.mean() - actual.mean()),
                "pred_mean": float(pred.mean()),
                "own_mean": float(actual.mean()),
            }
            f = res["families"][fam]
            print(
                f"  hold {hold} family {fam}: membership agree {agree:.3f} "
                f"(weighted {agree_w:.3f}) | hourly corr {f['hourly_corr']:+.3f} "
                f"hod corr {f['hod_corr']:+.3f} bias {f['level_bias']:+.4f} "
                f"(pred {f['pred_mean']:.3f} vs own {f['own_mean']:.3f})"
            )
        loyo[str(hold)] = res
    report["loyo"] = loyo

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
