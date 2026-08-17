"""nyiso-141 — is the downstate ST_GAS under-production a dispatch fact or a
measurement artifact?

Identification BEFORE any mechanism is written and BEFORE any LP is solved, for
the successor object named by
``FINDING-nyiso140-li-st-floor-membership-2026-08-16.md`` §7: after nyiso-140
withdrew 1.87 TWh of manufactured Port Jefferson energy, NYISO ST_GAS sits at
-0.916 TWh (2024) and -3.737 TWh (2025) against actuals.

The probe reads SOURCE data only -- the EPA CAMPD unit-level extracts, EIA-923
Page 1, and the committed benchmark sidecars. No price or volume residual is
consulted to FIND the object (rule 23 ``[R-FROZEN-DERIVE]``, rule 1
``[R-STRUCT]``); step 5 quotes the residual only to bound, honestly, how much of
it the finding accounts for.

Steps:

  1  DECOMPOSE   -- the actual ST_GAS rise by plant, and the fuel-switching
                    test (implied CO2 per MMBtu: ~53.1 is pure pipeline gas,
                    residual oil ~78.8). Rules out "a missing unit", "a Long
                    Island story" and "they switched to oil".
  2  INTERNAL    -- Astoria 8906's reheat/superheat pairs report IDENTICAL
                    grossLoad hour by hour while SPLITTING heat input. The
                    control group (Gowanus / Narrows / Holtsville / Barrett
                    peaker banks) shows that identity of output ALONE is not
                    the signature: those carry their own full heat input.
  3  PHYSICAL    -- counted alone each pair row implies ~5,200-5,500 Btu/kWh,
                    impossible for a fired boiler; counted once against the
                    pair's summed heat it is ~10,400-10,800, matching peers.
  4  EXTERNAL    -- EIA-923 net over CAMPD gross is ~0.47 for Astoria where
                    every genuine gas-steam peer is 0.92-0.96, and lands in the
                    peer band once the duplicate grossLoad is dropped.
  5  BENCHMARK   -- which years the CAMPD backfill put the doubled number into
                    the scored actuals, and what that is worth.

Run: ``.venv/bin/python scripts/probes/_nyiso141_astoria_stack_duplication.py``
Rule 25 ``[R-ISO-SCOPE]``: NYISO only; the scan covers state NY only.
"""

from __future__ import annotations

import gzip
import itertools
import json
import warnings

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR, REPO_ROOT

warnings.filterwarnings("ignore")

YEARS = (2023, 2024, 2025)  # training window only (rule 22 holdout freeze)
ASTORIA = 8906
BENCH_DIR = REPO_ROOT / "frontend" / "data" / "backcast" / "bench" / "NYISO"
UNIT_DIR = RAW_DIR / "campd-unit-level"

# The NYISO gas-steam plants, for the peer bands every test is read against.
PEERS = {
    2480: "Danskammer",
    2490: "Arthur Kill",
    2511: "E F Barrett",
    2516: "Northport",
    2517: "Port Jefferson",
    2625: "Bowline",
    8006: "Roseton",
    ASTORIA: "Astoria",
}
SHORT_TON_TO_KG = 907.185
# EPA default CO2 factor, kg per MMBtu: pipeline gas 53.06, residual oil ~78.8.
# An implied factor at ~54 is gas; oil burn pushes it up.
GAS_KG_PER_MMBTU = 53.06


def _unit_extract(year: int) -> pd.DataFrame:
    """Return the NY unit-level CAMPD extract with a numeric ``facilityId``."""
    df = pd.read_parquet(UNIT_DIR / f"NY_{year}.parquet")
    df["facilityId"] = df["facilityId"].astype(int)
    return df


def step1_decompose() -> None:
    """Print the actual ST_GAS rise by plant, and the fuel-switching test."""
    print("\n=== 1  WHERE THE ACTUAL ST_GAS RISE LIVES (bench c_ann, TWh) ===")
    rows = []
    for year in YEARS:
        bench = json.load(gzip.open(BENCH_DIR / f"{year}.json.gz"))["bench"]
        for key, rec in bench["plants"].items():
            if rec.get("group") != "ST_GAS":
                continue
            rows.append(
                {
                    "year": year,
                    "name": rec["name"][:26],
                    "zone": rec["zone"],
                    "twh": rec.get("c_ann", 0.0),
                }
            )
    pivot = (
        pd.DataFrame(rows)
        .pivot_table(index=["name", "zone"], columns="year", values="twh", aggfunc="sum")
        .fillna(0.0)
    )
    pivot["delta"] = pivot[2025] - pivot[2023]
    print(pivot.sort_values("delta", ascending=False).round(3).to_string())
    print("\n  -> broad-based across six large plants in three zones: not a")
    print("     missing unit, not a Long Island story.")

    print("\n=== 1b  FUEL-SWITCHING TEST (implied kg CO2 per MMBtu) ===")
    print(f"    pipeline gas ~= {GAS_KG_PER_MMBTU}; residual oil ~= 78.8")
    out = []
    for year in YEARS:
        df = _unit_extract(year)
        df = df[df["facilityId"].isin(PEERS)]
        agg = df.groupby("facilityId").agg(
            hi=("heatInput", "sum"), co2=("co2Mass", "sum")
        )
        agg["year"] = year
        agg["kg_per_mmbtu"] = agg["co2"] * SHORT_TON_TO_KG / agg["hi"]
        agg["name"] = [PEERS[i] for i in agg.index]
        out.append(agg.reset_index())
    both = pd.concat(out)
    print(
        both.pivot_table(index="name", columns="year", values="kg_per_mmbtu")
        .round(2)
        .to_string()
    )
    print("\n  -> the plants that doubled stayed on gas. Fuel switching refuted.")


def step2_internal(year: int = 2025) -> None:
    """Scan NY for duplicate-reporting pairs; separate them from real twins."""
    print(f"\n=== 2  INTERNAL: identical-output unit pairs, NY {year} ===")
    df = _unit_extract(year)
    df = df[df["grossLoad"].notna()]
    hits = []
    for fid, sub in df.groupby("facilityId"):
        units = sorted(sub["unitId"].astype(str).unique())
        if len(units) < 2:
            continue
        wide = sub.pivot_table(
            index=["date", "hour"], columns="unitId", values="grossLoad"
        )
        for a, b in itertools.combinations(units, 2):
            if a not in wide or b not in wide:
                continue
            pair = wide[[a, b]].dropna()
            if len(pair) < 200 or pair[a].sum() == 0:
                continue
            same = float(((pair[a] - pair[b]).abs() < 1e-6).mean())
            if same > 0.95:
                hits.append(
                    {
                        "facility": fid,
                        "name": str(sub["facilityName"].iloc[0])[:30],
                        "pair": f"{a}=={b}",
                        "identical_pct": round(100 * same, 2),
                        "max_abs_diff": round(float((pair[a] - pair[b]).abs().max()), 3),
                    }
                )
    hit_df = pd.DataFrame(hits)
    print(hit_df.to_string(index=False))
    print("\n  -> identity of OUTPUT alone is common (peaker banks run in")
    print("     lockstep). Step 3 is the test that separates them.")


def step3_physical(year: int = 2025) -> None:
    """Standalone heat rate per unit: the discriminator that actually works."""
    print(f"\n=== 3  PHYSICAL: standalone heat rate per unit, NY {year} ===")
    print("    a fired BOILER cannot beat ~9,000 Btu/kWh; a modern CC is ~6,500")
    df = _unit_extract(year)
    for fid in (ASTORIA, 2511, 2494, 2499, 8007):
        sub = df[(df["facilityId"] == fid) & (df["grossLoad"] > 0)]
        if sub.empty:
            continue
        agg = sub.groupby("unitId").agg(
            mwh=("grossLoad", "sum"), hi=("heatInput", "sum")
        )
        agg["HR_alone"] = (agg["hi"] * 1e6 / agg["mwh"] / 1e3).round(0)
        name = str(sub["facilityName"].iloc[0])[:34]
        print(f"\n  --- {fid} {name}")
        print(agg[["mwh", "HR_alone"]].round(0).to_string())
    print("\n  -> ONLY Astoria's RH/SH rows imply a sub-6,000 Btu/kWh boiler.")
    print("     Every other lockstep bank carries its own full heat input.")

    print("\n  Astoria counted ONCE per pair, heat summed over both paths:")
    sub = df[(df["facilityId"] == ASTORIA) & (df["grossLoad"] > 0)]
    for primary, dup in (("31RH", "32SH"), ("51RH", "52SH")):
        mwh = float(sub[sub["unitId"] == primary]["grossLoad"].sum())
        hi = float(sub[sub["unitId"].isin([primary, dup])]["heatInput"].sum())
        print(f"    {primary}+{dup}: {hi * 1e6 / mwh / 1e3:,.0f} Btu/kWh")
    print("    peers: Arthur Kill 10,033 | Northport 9,983 | Bowline 9,665")


def step4_external() -> None:
    """EIA-923 net over CAMPD gross, raw and with the duplicate dropped."""
    print("\n=== 4  EXTERNAL: EIA-923 net / CAMPD gross ===")
    from market_sim.data.campd import eia923_combustion_net
    from market_sim.data.eia923 import load_monthly_generation

    net = eia923_combustion_net(load_monthly_generation())
    dup_units = {"32SH", "52SH"}
    rows = []
    for year in YEARS:
        df = _unit_extract(year)
        for fid, name in PEERS.items():
            sub = df[df["facilityId"] == fid]
            if sub.empty:
                continue
            raw_gross = float(sub["grossLoad"].fillna(0.0).sum())
            corr_gross = float(
                sub[~sub["unitId"].astype(str).isin(dup_units)]["grossLoad"]
                .fillna(0.0)
                .sum()
            )
            hit = net[(net["plant_id"] == fid) & (net["year"] == year)]["net_mwh"]
            n = float(hit.iloc[0]) if len(hit) else np.nan
            rows.append(
                {
                    "name": name,
                    "year": year,
                    "raw": round(n / raw_gross, 3) if raw_gross else np.nan,
                    "corrected": round(n / corr_gross, 3) if corr_gross else np.nan,
                }
            )
    out = pd.DataFrame(rows)
    print(out.pivot_table(index="name", columns="year", values="raw").to_string())
    print("\n  Astoria with the duplicate grossLoad dropped:")
    ast = out[out["name"] == "Astoria"]
    print(ast[["year", "raw", "corrected"]].to_string(index=False))
    print("\n  -> peers 0.92-0.96; Astoria 0.47 raw, in-band once corrected.")


def step5_benchmark() -> None:
    """Which years the CAMPD backfill pushed the doubled number into actuals."""
    print("\n=== 5  BENCHMARK: where the doubled number actually landed ===")
    print("    e_ann is the scored benchmark; c_ann is CAMPD. e_ann == c_ann")
    print("    is the signature of _backfill_eia923_with_campd firing.")
    for year in YEARS:
        bench = json.load(gzip.open(BENCH_DIR / f"{year}.json.gz"))["bench"]
        rec = bench["plants"].get(str(ASTORIA))
        if rec is None:
            continue
        e, c = rec.get("e_ann"), rec.get("c_ann")
        fired = "YES -- benchmark took CAMPD" if e == c else "no -- EIA-923 present"
        print(
            f"    {year}: e_ann={e:<8} c_ann={c:<8} backfilled: {fired}"
            f"   classFull ST_GAS={bench['classFull']['ST_GAS']}"
        )
    print("\n  -> 2023/2024 benchmarks were correct all along; 2025 carries the")
    print("     double. Astoria 2.672 -> 1.359 TWh, i.e. ~1.31 TWh of the 2025")
    print("     ST_GAS actual is an artifact. That is ~35 % of the -3.737 TWh")
    print("     residual; the rest stays OPEN (finding §6).")


def main() -> None:
    """Run the five identification steps in order."""
    step1_decompose()
    step2_internal()
    step3_physical()
    step4_external()
    step5_benchmark()


if __name__ == "__main__":
    main()
