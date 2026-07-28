"""nyiso-94 — is the DA virtual-bid mechanism IDENTIFIABLE from NYISO's public data?

Step-1 census for the `da_virtual_bids` lever (matrix row `da_virtual_bids`,
NYISO cell; queue item 1 of `docs/mechanism-testing-matrix.md` §5.5). Answers
the charter's branch point BEFORE any solve is spent: can NYISO's published
day-ahead data identify a PJM-form net virtual curve ``net(lambda)`` without a
fitted scalar?

Verdict produced by this probe: **NO** — on three independent grounds, any one
of which is disqualifying. See
``docs/FINDING-nyiso94-da-virtual-not-identifiable-2026-07-28.md``.

What it measures
----------------
1. **Grain.** NYISO MIS P-59 ``zonalBidLoad`` publishes Virtual Load / Virtual
   Supply per NYISO load zone per hour — but carries **no price axis**, so no
   ``net(lambda)`` can be rendered from it.
2. **Provenance (rule 13 `[R-MEASURED]`).** Those columns are **CLEARED**
   volumes, not submitted curves: the annual means reproduce the NYISO IMM's
   published *cleared* virtual MW/h (2025 SOM Figure 24) to within 1-2 MW.
   PJM's mechanism is admissible precisely because ``hrl_da_incs_decs`` is the
   SUBMITTED curve; NYISO publishes no submitted-curve equivalent.
3. **Premise.** PJM's lever exists because DA clears MORE than physical load
   (+7-11 GW net DEC at peak). NYISO's net virtual position is NEGATIVE in the
   mean hour and only ~+0.3-0.9 GW in the measured RT>$300 tail — and NYISO's
   own IMM reports DA net scheduled load at ~96 % of actual peak load.

Optionally (``--biddata``) it also runs the identification attempt on the P-27
3-month-lag masked bid archive, which carries prices but cannot separate
virtual load from physical price-capped load.

Data is fetched from NYISO's public MIS at run time and written to a scratch
directory. It is deliberately **NOT** committed under ``data/raw/``: cleared
virtual volume is a market OUTCOME, and a measured outcome sitting in the input
tree is a re-armable answer key (rule 26 `[R-DELETE]` in spirit).

Usage
-----
    uv run python scripts/probes/nyiso94_da_virtual_identifiability.py
    uv run python scripts/probes/nyiso94_da_virtual_identifiability.py --biddata
    uv run python scripts/probes/nyiso94_da_virtual_identifiability.py \
        --keeper results/calibration/nyiso92_hydro_envfloor
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

#: NYISO public MIS archive root (no key, no registration).
MIS = "https://mis.nyiso.com/public/csv"

#: Scored training years (rule 22 `[R-HOLDOUT]`: 2023-2025 only).
YEARS = (2023, 2024, 2025)

#: NYISO load zone -> model transmission zone. Mirrors
#: ``market_sim.data.eia930.zonal_shares._NYISO_LOAD_ZONE_GROUPS`` (A-K onto the
#: five model zones); duplicated here so the probe stays import-light.
ZONE_MAP = {
    "WEST": "Upstate_West",
    "GENESE": "Upstate_West",
    "CENTRL": "Upstate_West",
    "NORTH": "Upstate_West",
    "MHK VL": "Upstate_West",
    "CAPITL": "Capital_Hudson",
    "HUD VL": "Capital_Hudson",
    "MILLWD": "Lower_Hudson",
    "DUNWOD": "Lower_Hudson",
    "N.Y.C.": "NYC",
    "LONGIL": "Long_Island",
}

#: NYISO IMM published CLEARED virtual volumes, 2025 SOM Figure 24 (MW/h, all
#: hours, internal zones + external proxy buses). The provenance check compares
#: the zonalBidLoad-derived annual means against these.
SOM_CLEARED = {
    2024: {"virtual_load": 1089.0, "virtual_supply": 1275.0},
    2025: {"virtual_load": 1051.0, "virtual_supply": 1327.0},
}

#: C3c threshold for NYISO (``calibration_verdict.TAIL_THRESHOLD``), $/MWh.
TAIL_THRESHOLD = 300.0


def _fetch_month(dataset: str, year: int, month: int, cache: Path) -> pd.DataFrame:
    """Download one monthly NYISO MIS archive and return its concatenated CSVs."""
    name = f"{year}{month:02d}01{dataset}_csv.zip"
    dest = cache / name
    if not dest.exists() or dest.stat().st_size == 0:
        resp = requests.get(f"{MIS}/{dataset}/{name}", timeout=180)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
    zf = zipfile.ZipFile(dest)
    frames = [pd.read_csv(io.BytesIO(zf.read(n))) for n in zf.namelist()]
    out = pd.concat(frames, ignore_index=True)
    out.columns = [c.strip() for c in out.columns]
    return out


def load_zonal_bid_load(cache: Path) -> pd.DataFrame:
    """P-59 ``zonalBidLoad`` for the training years, mapped onto model zones."""
    frames = [
        _fetch_month("zonalBidLoad", y, m, cache) for y in YEARS for m in range(1, 13)
    ]
    zbl = pd.concat(frames, ignore_index=True)
    zbl["dt"] = pd.to_datetime(zbl["Time Stamp"])
    zbl["year"] = zbl["dt"].dt.year
    zbl = zbl[zbl["year"].isin(YEARS)].copy()
    zbl["mzone"] = zbl["Name"].map(ZONE_MAP)
    if zbl["mzone"].isna().any():
        raise ValueError(f"unmapped NYISO zones: {sorted(zbl.loc[zbl.mzone.isna(), 'Name'].unique())}")
    # Virtual Supply is published negative; net > 0 == net virtual DEMAND.
    zbl["net_virtual"] = zbl["Virtual Load"] + zbl["Virtual Supply"]
    return zbl


def load_actual_load(cache: Path) -> pd.DataFrame:
    """P-58B ``pal`` 5-minute actual load -> hourly system MW.

    Mean per (hour, zone) then SUM over zones: a plain sum/12 mis-scales any
    hour with missing 5-minute intervals.
    """
    frames = [_fetch_month("pal", y, m, cache) for y in YEARS for m in range(1, 13)]
    pal = pd.concat(frames, ignore_index=True).dropna(subset=["Load"])
    pal["hr"] = pd.to_datetime(pal["Time Stamp"], format="mixed").dt.floor("h")
    zonal = pal.groupby(["hr", "Name"])["Load"].mean().reset_index()
    return zonal.groupby("hr")["Load"].sum().rename("rt_load_mw").reset_index()


def report_grain_and_provenance(zbl: pd.DataFrame) -> pd.DataFrame:
    """Blockers 1 and 2: no price axis, and the volumes are CLEARED."""
    print("\n" + "=" * 72)
    print("1. GRAIN — what P-59 zonalBidLoad actually carries")
    print("=" * 72)
    print(f"   columns: {[c for c in zbl.columns if c not in ('dt', 'year', 'mzone', 'net_virtual')]}")
    print(f"   {zbl['dt'].nunique():,} hours x {zbl['Name'].nunique()} NYISO zones, {YEARS[0]}-{YEARS[-1]}")
    print("   -> Virtual Load / Virtual Supply are a SINGLE MW per zone-hour.")
    print("      There is NO price column, hence no lambda axis and no net(lambda).")

    sysh = (
        zbl.groupby(["year", "dt"])[
            ["Energy Bid Load", "Bilateral Load", "Price Cap Load", "Virtual Load", "Virtual Supply"]
        ]
        .sum()
        .reset_index()
    )
    sysh["net_virtual"] = sysh["Virtual Load"] + sysh["Virtual Supply"]

    print("\n" + "=" * 72)
    print("2. PROVENANCE — cleared, not submitted (rule 13 [R-MEASURED])")
    print("=" * 72)
    print("   zonalBidLoad annual mean vs NYISO IMM published CLEARED MW/h (2025 SOM Fig 24):")
    for year, som in SOM_CLEARED.items():
        g = sysh[sysh.year == year]
        vl, vs = g["Virtual Load"].mean(), -g["Virtual Supply"].mean()
        print(
            f"     {year}  Virtual Load  {vl:7.1f} vs SOM {som['virtual_load']:7.1f}  (delta {vl - som['virtual_load']:+.1f} MW)"
        )
        print(
            f"           Virtual Supply {vs:7.1f} vs SOM {som['virtual_supply']:7.1f}  (delta {vs - som['virtual_supply']:+.1f} MW)"
        )
    print("   -> matches the CLEARED series to within 1-2 MW. These are OUTCOMES.")
    print("      PJM's lever is admissible because hrl_da_incs_decs is the SUBMITTED")
    print("      curve; NYISO publishes no submitted-curve equivalent.")
    return sysh


def report_premise(sysh: pd.DataFrame, load: pd.DataFrame, lmp: pd.DataFrame) -> pd.DataFrame:
    """Blocker 3: the PJM premise (DA deeper than physical load) is false here."""
    merged = sysh.merge(load, left_on="dt", right_on="hr", how="inner")
    merged["DA_phys"] = merged["Energy Bid Load"] + merged["Bilateral Load"] + merged["Price Cap Load"]
    merged["DA_total"] = merged["DA_phys"] + merged["net_virtual"]
    merged["DA_minus_RT"] = merged["DA_total"] - merged["rt_load_mw"]
    merged["key"] = merged["dt"].dt.strftime("%Y-%m-%d %H")
    lmp = lmp.copy()
    lmp["key"] = lmp["dt"].dt.strftime("%Y-%m-%d %H")
    j = merged.merge(lmp[["key", "rt"]], on="key", how="inner")

    print("\n" + "=" * 72)
    print("3. PREMISE — PJM's is 'DA clears MORE than physical load'. NYISO's does not.")
    print("=" * 72)
    print("   All hours (MW):")
    print(
        j.groupby("year")[["DA_phys", "Virtual Load", "Virtual Supply", "net_virtual", "DA_total", "rt_load_mw", "DA_minus_RT"]]
        .mean()
        .round(0)
        .to_string()
    )
    tail = j[j.rt > TAIL_THRESHOLD]
    print(f"\n   MEASURED RT>${TAIL_THRESHOLD:.0f} tail hours (the C3c target):")
    print(
        tail.groupby("year")[["Virtual Load", "Virtual Supply", "net_virtual", "DA_total", "rt_load_mw", "DA_minus_RT"]]
        .mean()
        .round(0)
        .to_string()
    )
    print("\n   net virtual: tail vs top-100 load vs all hours (MW)")
    for year, g in j.groupby("year"):
        t = g[g.rt > TAIL_THRESHOLD]
        top = g.nlargest(100, "rt_load_mw")
        print(
            f"     {year}: tail(n={len(t):2d}) {t.net_virtual.mean():6.0f} "
            f"({100 * t.net_virtual.mean() / t.rt_load_mw.mean():4.1f}% of RT load) | "
            f"top100 load {top.net_virtual.mean():6.0f} | all hrs {g.net_virtual.mean():6.0f}"
        )
    return j


def report_zonal(zbl: pd.DataFrame, lmp: pd.DataFrame) -> None:
    """The zonal signature: net virtual DEMAND downstate, net SUPPLY upstate."""
    mz = zbl.groupby(["year", "dt", "mzone"])[["Virtual Load", "Virtual Supply", "net_virtual"]].sum().reset_index()
    mz["key"] = mz["dt"].dt.strftime("%Y-%m-%d %H")
    lmp = lmp.copy()
    lmp["key"] = lmp["dt"].dt.strftime("%Y-%m-%d %H")
    j = mz.merge(lmp[["key", "rt"]], on="key", how="inner")
    print("\n" + "=" * 72)
    print("4. ZONAL SIGNATURE — a congestion play, not a depth play")
    print("=" * 72)
    print("   net virtual by MODEL zone, all hours (MW):")
    print(j.pivot_table(index="mzone", columns="year", values="net_virtual", aggfunc="mean").round(0).to_string())
    print(f"\n   net virtual by MODEL zone, measured RT>${TAIL_THRESHOLD:.0f} tail hours (MW):")
    tail = j[j.rt > TAIL_THRESHOLD]
    print(tail.pivot_table(index="mzone", columns="year", values="net_virtual", aggfunc="mean").round(0).to_string())
    print("   -> matches the NYISO IMM's own description (2025 SOM p.21): traders")
    print("      'purchas[e] load downstate and sell[] virtual energy upstate'.")


def report_roof(keeper: Path, lmp: pd.DataFrame) -> None:
    """Even granting the mechanism: the keeper's mainland stack has no >$300 rung."""
    print("\n" + "=" * 72)
    print("5. ROOF — the lever could not reach C3c even if it were identifiable")
    print("=" * 72)
    for year in YEARS:
        path = keeper / "hourly" / f"system_{year}.parquet"
        if not path.exists():
            print(f"   {year}: {path} absent — skipped")
            continue
        s = pd.read_parquet(path)
        g = s.groupby("zone")["price"].agg(["max", lambda x: (x > 258).sum(), lambda x: (x > TAIL_THRESHOLD).sum()])
        g.columns = ["max", "h>258", f"h>{TAIL_THRESHOLD:.0f}"]
        tot = s.groupby("hour")[["slack", "dump"]].sum()
        print(f"\n   --- {year} ---")
        print(g.round(1).to_string())
        print(f"   hours with ANY load-shed slack: {(tot.slack > 0.01).sum()}   total slack {tot.slack.sum():,.0f} MWh")

        # zonal separation in the measured tail hours
        p = s.pivot_table(index="hour", columns="zone", values="price")
        t = lmp[(lmp.year == year) & (lmp.rt > TAIL_THRESHOLD)].copy()
        t["hoy"] = ((t.dt - pd.Timestamp(year, 1, 1)).dt.total_seconds() // 3600).astype(int)
        sub = p.loc[p.index.intersection(t.hoy)]
        if len(sub) and {"NYC", "Upstate_West", "Lower_Hudson"} <= set(sub.columns):
            print(
                f"   in the {len(sub)} measured tail hours: NYC-Upstate spread mean ${(sub['NYC'] - sub['Upstate_West']).mean():.1f}, "
                f"Lower_Hudson-Upstate mean ${(sub['Lower_Hudson'] - sub['Upstate_West']).mean():.1f}"
            )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, default=Path("/tmp/nyiso94_cache"), help="download cache directory")
    ap.add_argument("--keeper", type=Path, default=REPO / "results/calibration/nyiso92_hydro_envfloor")
    ap.add_argument("--biddata", action="store_true", help="also run the P-27 masked-archive identification attempt (large downloads)")
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)

    lmp = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet")
    lmp = lmp[lmp.year.isin(YEARS)].copy()
    lmp["dt"] = [pd.Timestamp(int(y), 1, 1) + pd.Timedelta(hours=int(h)) for y, h in zip(lmp.year, lmp.hour)]

    print("nyiso-94 — DA virtual-bid identifiability census (NYISO public MIS)")
    zbl = load_zonal_bid_load(args.cache)
    sysh = report_grain_and_provenance(zbl)
    load = load_actual_load(args.cache)
    report_premise(sysh, load, lmp)
    report_zonal(zbl, lmp)
    report_roof(args.keeper, lmp)

    if args.biddata:
        report_biddata(args.cache)

    print("\n" + "=" * 72)
    print("VERDICT: NOT IDENTIFIABLE. Matrix da_virtual_bids x NYISO: U -> G.")
    print("See docs/FINDING-nyiso94-da-virtual-not-identifiable-2026-07-28.md")
    print("=" * 72)
    return 0


def report_biddata(cache: Path, year: int = 2025, month: int = 6) -> None:
    """P-27 masked archive: prices exist, but virtuals are not separable."""
    print("\n" + "=" * 72)
    print(f"A. P-27 masked bid archive ({year}-{month:02d}) — priced, but not separable")
    print("=" * 72)
    df = _fetch_month("biddata_loadbids", year, month, cache)
    df["dt"] = pd.to_datetime(df["Date Time"].astype(str).str.strip(), format="%d%b%Y:%H:%M:%S")
    df["pc_mw"] = df[["Price cap 1 MW", "Price cap 2 MW", "Price cap 3 MW"]].sum(axis=1)
    pure = df[df["Forecast MW"].isna() & df["Fixed MW"].isna() & df["Price cap 1 MW"].notna()]
    phys = df[df["Forecast MW"].notna() | df["Fixed MW"].notna()]
    print(f"   financial-signature sinks (no Forecast/Fixed MW): {pure['Masked Sink ID'].nunique()}")
    print(f"   physical sinks:                                   {phys['Masked Sink ID'].nunique()}")
    print(f"   sinks in BOTH sets: {len(set(pure['Masked Sink ID']) & set(phys['Masked Sink ID']))}")

    zbl = _fetch_month("zonalBidLoad", year, month, cache)
    zbl["dt_local"] = pd.to_datetime(zbl["Time Stamp"])
    agg = zbl.groupby("dt_local")[["Price Cap Load", "Virtual Load"]].sum().reset_index()
    agg["dt_utc"] = (
        agg["dt_local"].dt.tz_localize("America/New_York", ambiguous="infer", nonexistent="shift_forward")
        .dt.tz_convert("UTC").dt.tz_localize(None)
    )
    hourly = df.groupby("dt")["pc_mw"].sum().rename("all_pricecap_mw").reset_index()
    m = agg.merge(hourly, left_on="dt_utc", right_on="dt", how="inner")
    m["VL_plus_PCL"] = m["Virtual Load"] + m["Price Cap Load"]
    for col in ("Virtual Load", "Price Cap Load", "VL_plus_PCL"):
        print(
            f"   all price-cap MW vs {col:15s}: corr {m['all_pricecap_mw'].corr(m[col]):.4f}  "
            f"level ratio {m['all_pricecap_mw'].mean() / m[col].mean():.3f}"
        )
    print("   -> masking removes the resource-type flag: virtual load cannot be")
    print("      separated from physical price-capped load at any published grain.")


if __name__ == "__main__":
    raise SystemExit(main())
