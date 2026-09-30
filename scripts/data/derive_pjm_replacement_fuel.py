"""Derive PJM's REPLACEMENT-COST fuel inputs (PJM-NEXT-13, owner ruling 2026-09-29).

Rule 23 ``[R-FROZEN-DERIVE]``: measured-behaviour tables. They re-derive ONLY when
their source data updates (a new EIA-923 vintage, a new IMM SOM figure, a new EIA
transport-rate or mine-level release). They never re-derive because a residual moved,
and a re-derivation commit cites the data change.

THE RULING. The owner ruled on the PJM-NEXT-13 card-2 decision card ("Hub + transport,
joint with coal"): a PJM dispatch offer is priced at **replacement cost**, which is the
traded commodity plus measured variable transport. It is priced this way for gas AND
coal, not at the EIA-923 monthly AVERAGE delivered print, because that print carries
reservation/demand charges and contract commodity prices amortized over the month's
takes (rule 14's misalignment clause; ``docs/FINDING-pjm-next-13-...md`` §card 2). The
zone map was ruled on the same card:

    east_gas        EMAAC, SWMAAC, Dominion        (TETCO M3 / Transco Z5-Z6)
    west_gas        ComEd, AEP_Ohio, ATSI          (Columbia Appalachia / Chicago)
    production_gas  West_APS, Central_PA           (Dominion South / TZ4 / Leidy)

The commodity series is the IMM's own Platts monthly spot (``som-competitive-conduct``,
``spot_price_digitized_usd_per_mmbtu``), which is the series the IMM prices PJM's LMP
fuel components at.

GAS — ``data/raw/reference/pjm_gas_variable_transport.csv``. The miso-225 estimator,
ported, with PJM's own receipts and PJM's own hubs (rule 25: the MISO numbers are not
transferred, only the construction). Per plant, the month's print less the region's
monthly spot is split as the tariff splits it:

    print[p,m] - hub[p,m] = v[p] + F[p] / burn[p,m]

``v`` is the volume-invariant wedge paid on the next MMBtu, which is the ruling's
"variable transport". ``F`` is the fixed monthly charge a dispatch offer must not carry.
The fit is burn-weighted least squares over the plant's own admissible months. It gives
ONE value per plant, pooled over every scored year 2019-2025 (rule 1 condition (b)). The
fallback ladder is own -> (zone, class) -> class -> PJM-wide, and the bars are declared
here and never swept. There is no clipping: a negative ``v`` is kept as measured.

COAL — ``data/raw/reference/pjm_coal_replacement.csv``. For every PJM coal plant-year:

* **Basin shares.** From the plant's own EIA-923 receipts (quantity x heat content).
  Each receipt's ``Coalmine Msha Id`` is mapped to EIA's own ``Coal Supply Region``
  (the EIA mine-level files; fallback (mine state, county) -> majority region).
* **Transport.** Per basin, the EIA *Coal Transportation Rates* value for (basin ->
  plant state, primary mode, year). EIA defines it as delivered cost minus commodity
  cost. The ladder is basin->state->mode (Tables 3a/3b/3c) -> basin x mode (Table 2) ->
  mode total (Table 2). It is divided by that basin's receipt heat content (MMBtu/ton).
* **Priceable share.** Only basins with an IMM Platts spot are priceable (Northern
  Appalachia -> ``napp_coal``, Central Appalachia -> ``capp_coal``, Powder River Basin ->
  ``prb_coal``), and only on a tabulated mode (rail / waterway / truck). Every other
  share (Illinois Basin, imports, conveyor / mine-mouth, withheld) is UNPRICED. It keeps
  the plant's own print in the applier: the construction is not extended where no
  measured commodity series exists (a declared scope limit, not a guess).

The applier (``market_sim.data.fuel.basis.pjm_replacement``) prices a coal row at
``sum_b s_b (spot_b,m + t_b) + s_unpriced * current``. 2025 has no receipts file and no
published rates, so a 2025 row uses the plant's pooled 2019-2024 shares and the 2024
transport (hold-last, declared).

Usage: ``PYTHONPATH=src python3 scripts/data/derive_pjm_replacement_fuel.py``
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BINS = ROOT / "data/raw/_processed-legacy/bin_assignments_PJM.csv"
F923 = ROOT / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
SOM = ROOT / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
RECEIPTS = str(ROOT / "data/raw/coal-receipts/coal_receipts_{y}.csv")
MINES = ROOT / "data/raw/eia-coal-mine-region"
RATES = ROOT / "data/raw/eia-coal-transport-rates"
OUT_GAS = ROOT / "data/raw/reference/pjm_gas_variable_transport.csv"
OUT_COAL = ROOT / "data/raw/reference/pjm_coal_replacement.csv"

#: Every scored PJM year (the owner's "every year"); ONE pooled gas ``v`` per plant.
YEARS: tuple[int, ...] = tuple(range(2019, 2026))
#: Years with an EIA-923 receipts file (coal basin shares).
RECEIPT_YEARS: tuple[int, ...] = tuple(range(2019, 2025))

#: The owner-ruled zone -> IMM gas region map (PJM-NEXT-13 decision card).
ZONE_GAS_REGION: dict[str, str] = {
    "PJM_EMAAC": "east_gas",
    "PJM_SWMAAC": "east_gas",
    "PJM_Dominion": "east_gas",
    "PJM_ComEd": "west_gas",
    "PJM_AEP_Ohio": "west_gas",
    "PJM_ATSI": "west_gas",
    "PJM_West_APS": "production_gas",
    "PJM_Central_PA": "production_gas",
}
#: EIA Coal Supply Region -> the IMM Platts spot segment that prices it.
BASIN_SPOT: dict[str, str] = {
    "Appalachia Northern": "napp_coal",
    "Appalachia Central": "capp_coal",
    "Powder River Basin": "prb_coal",
}
#: EIA transport-table basin label for each priceable supply region.
BASIN_RATE_LABEL: dict[str, str] = {
    "Appalachia Northern": "Northern Appalachia",
    "Appalachia Central": "Central Appalachia",
    "Powder River Basin": "Powder River Basin",
}
#: EIA-923 primary transport mode -> transport-rate table (tabulated modes only).
MODE_TABLE: dict[str, str] = {
    "RR": "3c",
    "RV": "3b",
    "WT": "3b",
    "TR": "3a",
}
MODE_T2_BLOCK: dict[str, str] = {"3c": "Railroad", "3b": "Waterway", "3a": "Truck"}

#: Gas classes of ``bin_assignments_PJM.csv`` (coal is the other leg).
GAS_GROUPS = ("CC_", "CT_", "ST_GAS", "ST_CHP")
COAL_GROUPS = ("COAL_BIT", "COAL_PRB")
#: A plant carries its OWN gas ``v`` only with this many admissible months and this
#: burn spread — the miso-225 bars, declared before any arm was solved, never swept.
MIN_MONTHS = 12
MIN_BURN_SPREAD = 2.0
#: A mine state maps to a supply region on the state alone only when EIA assigns at
#: least this share of its mines to that one region (declared, never swept).
STATE_REGION_PURITY = 0.95

STATE_NAME = {
    "DE": "Delaware", "IL": "Illinois", "IN": "Indiana", "KY": "Kentucky",
    "MD": "Maryland", "MI": "Michigan", "NJ": "New Jersey", "NC": "North Carolina",
    "OH": "Ohio", "PA": "Pennsylvania", "TN": "Tennessee", "VA": "Virginia",
    "WV": "West Virginia", "DC": "District of Columbia", "NY": "New York",
    "AL": "Alabama", "CO": "Colorado", "MT": "Montana", "WY": "Wyoming",
    "UT": "Utah", "ND": "North Dakota", "TX": "Texas", "NM": "New Mexico",
    "MO": "Missouri", "OK": "Oklahoma", "AZ": "Arizona", "LA": "Louisiana",
    "MS": "Mississippi", "AK": "Alaska", "WA": "Washington",
}  # fmt: skip


def imm_monthly(segment: str) -> dict[tuple[int, int], float]:
    """``{(year, month): $/MMBtu}`` for one IMM digitized spot segment."""
    s = pd.read_csv(SOM)
    s = s[
        (s.iso == "PJM")
        & (s.fleet_segment == segment)
        & (s.metric == "spot_price_digitized_usd_per_mmbtu")
        & s.period.str.startswith("month_")
    ]
    return {(int(r.year), int(r.period[-2:])): float(r.value) for r in s.itertuples()}


# --------------------------------------------------------------------------- gas


def _fit(wedge: np.ndarray, burn: np.ndarray, *, weighted: bool = True) -> tuple:
    """Fit ``wedge = v + F/burn`` (burn-weighted WLS); return ``(v, F, r2)``."""
    x = 1.0 / burn
    design = np.column_stack([np.ones_like(x), x])
    w = np.sqrt(burn) if weighted else np.ones_like(burn)
    coef, *_ = np.linalg.lstsq(design * w[:, None], wedge * w, rcond=None)
    resid = (wedge - design @ coef) * w
    mean = float((wedge * w**2).sum() / (w**2).sum())
    ss_tot = float((((wedge - mean) * w) ** 2).sum())
    r2 = 1.0 - float((resid**2).sum()) / ss_tot if ss_tot > 0 else float("nan")
    return float(coef[0]), float(coef[1]), r2


def gas_panel() -> pd.DataFrame:
    """The admissible (plant, year, month) gas wedge panel over the ruled hubs."""
    bins = pd.read_csv(BINS)
    gas = bins[bins["Plant_Group"].astype(str).str.startswith(GAS_GROUPS)].copy()
    gas["region"] = gas["Zone"].map(ZONE_GAS_REGION)
    gas = gas.dropna(subset=["region"])
    hubs = {r: imm_monthly(r) for r in set(ZONE_GAS_REGION.values())}
    f = pd.read_parquet(F923)
    f = f[
        (f.fuel_group == "Natural Gas")
        & f.year.isin(YEARS)
        & (f.quantity > 0)
        & (f.price_per_mmbtu > 0)
    ]
    rows = []
    for p in gas.itertuples():
        for rec in f[f.plant_id == int(p.Plant_Code)].itertuples():
            hub = hubs[p.region].get((int(rec.year), int(rec.month)))
            if hub is None:
                continue
            rows.append(
                {
                    "plant_id": int(p.Plant_Code),
                    "plant_name": str(p.Plant_Name),
                    "group": str(p.Plant_Group),
                    "zone": str(p.Zone),
                    "region": p.region,
                    "nameplate_mw": float(p.Nameplate_MW),
                    "burn_mmbtu": float(rec.quantity),
                    "wedge_usd_mmbtu": float(rec.price_per_mmbtu) - hub,
                }
            )
    # One row per (plant, group) bin: a plant with two gas classes appears once
    # per class, carrying the same receipts, which is what the ladder keys on.
    return pd.DataFrame(rows)


def derive_gas() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-plant gas variable transport + the pooled fallback rungs."""
    panel = gas_panel()
    wb = ("wedge_usd_mmbtu", "burn_mmbtu")
    zg = {
        k: _fit(*(g[c].to_numpy(float) for c in wb))[0]
        for k, g in panel.groupby(["zone", "group"])
        if len(g) >= MIN_MONTHS
    }
    gr = {
        k: _fit(*(g[c].to_numpy(float) for c in wb))[0]
        for k, g in panel.groupby("group")
        if len(g) >= MIN_MONTHS
    }
    iso = _fit(*(panel[c].to_numpy(float) for c in wb))[0]
    out = []
    for (pid, grp_name), g in panel.groupby(["plant_id", "group"]):
        burn = g.burn_mmbtu.to_numpy(float)
        wedge = g.wedge_usd_mmbtu.to_numpy(float)
        spread = float(burn.max() / burn.min()) if burn.min() > 0 else float("inf")
        v_fit, fixed, r2 = _fit(wedge, burn)
        key = (g.zone.iloc[0], grp_name)
        if len(g) >= MIN_MONTHS and spread >= MIN_BURN_SPREAD:
            v, src = v_fit, "own"
        elif key in zg:
            v, src = zg[key], "zone_group_pool"
        elif grp_name in gr:
            v, src = gr[grp_name], "group_pool"
        else:
            v, src = iso, "pjm_pool"
        out.append(
            {
                "plant_id": int(pid),
                "group": grp_name,
                "zone": key[0],
                "region": g.region.iloc[0],
                "nameplate_mw": float(g.nameplate_mw.iloc[0]),
                "n_months": len(g),
                "burn_spread": round(spread, 3),
                "v_usd_mmbtu": round(v, 6),
                "v_source": src,
                "fixed_usd_month": round(fixed, 3),
                "r2": round(r2, 4),
                "v_ols_usd_mmbtu": round(_fit(wedge, burn, weighted=False)[0], 6),
                "wedge_burn_weighted": round(
                    float((wedge * burn).sum() / burn.sum()), 6
                ),
            }
        )
    pool = pd.DataFrame(
        [{"rung": "zone_group", "key": f"{k[0]}|{k[1]}", "v_usd_mmbtu": round(v, 6)} for k, v in sorted(zg.items())]
        + [{"rung": "group", "key": k, "v_usd_mmbtu": round(v, 6)} for k, v in sorted(gr.items())]
        + [{"rung": "pjm", "key": "__PJM__", "v_usd_mmbtu": round(iso, 6)}]
    )  # fmt: skip
    return pd.DataFrame(out).sort_values(["plant_id", "group"]), pool


# -------------------------------------------------------------------------- coal


def _spreadsheetml(path: Path) -> pd.DataFrame:
    """Read an Excel 2003 SpreadsheetML workbook's first sheet (EIA 2021/2022)."""
    ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
    root = ET.parse(path).getroot()
    rows = []
    for row in root.find(".//ss:Worksheet", ns).iter(f"{{{ns['ss']}}}Row"):
        vals, i = [], 0
        for cell in row.findall("ss:Cell", ns):
            idx = cell.get(f"{{{ns['ss']}}}Index")
            if idx:
                while i < int(idx) - 1:
                    vals.append(None)
                    i += 1
            d = cell.find("ss:Data", ns)
            vals.append(d.text if d is not None else None)
            i += 1
        rows.append(vals)
    return pd.DataFrame(rows)


def _mine_frame(path: Path) -> pd.DataFrame:
    """One EIA mine-level file as ``MSHA ID / Mine State / Mine County / region``."""
    raw = (
        _spreadsheetml(path)
        if path.read_bytes()[:5] == b"<?xml"
        else pd.read_excel(path, header=None)
    )
    hdr = next(
        i for i in range(10) if "MSHA ID" in [str(x).strip() for x in raw.iloc[i]]
    )
    d = raw.iloc[hdr + 1 :].copy()
    d.columns = [str(x).strip() for x in raw.iloc[hdr]]
    d = d[["MSHA ID", "Mine State", "Mine County", "Coal Supply Region"]].dropna(
        subset=["MSHA ID"]
    )
    d["MSHA ID"] = pd.to_numeric(d["MSHA ID"], errors="coerce")
    return d.dropna(subset=["MSHA ID"])


def mine_regions() -> tuple[dict[int, str], dict[str, str]]:
    """``{msha: region}`` and ``{postal state: region}`` for single-region states.

    EIA-923 receipts carry the mine county as a FIPS code while the mine files carry
    its name, so a county key cannot join. The fallback is therefore the mine STATE,
    and only for a state whose mines EIA assigns to ONE supply region (at least
    ``STATE_REGION_PURITY`` of them). Ohio and Pennsylvania qualify. West Virginia
    and Kentucky, which EIA splits between basins, do not, so an unmatched WV/KY
    receipt stays unpriced.
    """
    frames = [_mine_frame(p) for p in sorted(MINES.glob("coalpublic*"))]
    m = pd.concat(frames, ignore_index=True)
    by_id = m.groupby("MSHA ID")["Coal Supply Region"].agg(lambda s: s.mode().iloc[0])
    postal = {v: k for k, v in STATE_NAME.items()}
    m["st"] = (
        m["Mine State"]
        .astype(str)
        .str.split(" (", regex=False)
        .str[0]
        .str.strip()
        .map(postal)
    )
    share = (
        m.dropna(subset=["st"])
        .groupby("st")["Coal Supply Region"]
        .agg(lambda s: (s.mode().iloc[0], float((s == s.mode().iloc[0]).mean())))
    )
    by_state = {k: v[0] for k, v in share.items() if v[1] >= STATE_REGION_PURITY}
    return {int(k): str(v) for k, v in by_id.items()}, by_state


def _rate_table(tab: str) -> pd.DataFrame:
    """Tables 3a/3b/3c as a long ``basin, state, year, usd_per_ton`` frame."""
    raw = pd.read_excel(RATES / f"Table_{tab}_Nominal.xlsx", header=None)
    hdr = raw.iloc[2].tolist()
    out = []
    for c0 in (0, 10):
        years = [(j, int(hdr[j])) for j in range(c0 + 2, len(hdr)) if isinstance(hdr[j], (int, float)) and not pd.isna(hdr[j]) and (c0 == 10 or j < 10)]  # fmt: skip
        for _, r in raw.iloc[3:].iterrows():
            basin, state = r.iloc[c0], r.iloc[c0 + 1]
            if not isinstance(basin, str) or not isinstance(state, str):
                continue
            for j, y in years:
                v = r.iloc[j]
                if isinstance(v, str) and v.startswith("$"):
                    out.append(
                        (basin.strip(), state.strip(), y, float(v[1:].replace(",", "")))
                    )
    return pd.DataFrame(out, columns=["basin", "state", "year", "usd_per_ton"])


def _table2() -> dict[tuple[str, str, int], float]:
    """Table 2 ``{(mode block, basin or 'Total', year): $/ton}``."""
    raw = pd.read_excel(RATES / "Table_2_Nominal.xlsx", header=None)
    hdr = raw.iloc[2].tolist()
    out: dict[tuple[str, str, int], float] = {}
    for c0 in (0, 9):
        years = [(j, int(hdr[j])) for j in range(c0 + 1, min(c0 + 10, len(hdr))) if isinstance(hdr[j], (int, float)) and not pd.isna(hdr[j])]  # fmt: skip
        block = None
        for _, r in raw.iloc[3:].iterrows():
            lab = r.iloc[c0]
            if not isinstance(lab, str):
                continue
            lab = lab.strip()
            if lab in ("Railroad", "Waterway", "Truck"):
                block = lab
                continue
            if block is None:
                continue
            key = "Total" if lab.endswith("[1]") else lab
            for j, y in years:
                v = r.iloc[j]
                if isinstance(v, str) and v.startswith("$"):
                    out[(block, key, y)] = float(v[1:].replace(",", ""))
    return out


def _rate(
    tabs: dict, t2: dict, region: str, state: str, mode_tab: str, year: int
) -> tuple:
    """EIA transport $/ton down the declared ladder; ``(value, rung)``."""
    basin = BASIN_RATE_LABEL[region]
    t = tabs[mode_tab]
    y = min(year, int(t.year.max()))  # 2025 -> hold the last published year
    hit = t[
        (t.basin == basin) & (t.state == STATE_NAME.get(state, state)) & (t.year == y)
    ]
    if len(hit):
        return float(hit.usd_per_ton.iloc[0]), "basin_state_mode"
    block = MODE_T2_BLOCK[mode_tab]
    for key, rung in ((basin, "basin_mode"), ("Total", "mode_total")):
        for yy in (y, y - 1, y + 1):
            if (block, key, yy) in t2:
                return t2[(block, key, yy)], rung
    return None, "none"


def derive_coal() -> pd.DataFrame:
    """Per (plant, year) basin shares + transport ($/MMBtu) for PJM coal plants."""
    bins = pd.read_csv(BINS)
    coal = bins[bins.Plant_Group.isin(COAL_GROUPS)]
    plants = {int(r.Plant_Code): str(r.Plant_Group) for r in coal.itertuples()}
    # The legacy bins file misses plants the plant-level fleet carries, so every
    # plant whose own receipts name the PJM balancing authority is added too; the
    # applier keys on plant code and applies to the COAL_BIT / COAL_PRB rows only.
    for y in RECEIPT_YEARS:
        d = pd.read_csv(
            RECEIPTS.format(y=y),
            low_memory=False,
            usecols=["Plant Id", "Balancing Authority Code", "FUEL_GROUP"],
        )
        for pid in (
            d[(d["Balancing Authority Code"] == "PJM") & (d.FUEL_GROUP == "Coal")][
                "Plant Id"
            ]
            .astype(int)
            .unique()
        ):
            plants.setdefault(int(pid), "receipts_pjm_ba")
    by_id, by_sc = mine_regions()
    tabs = {k: _rate_table(k) for k in ("3a", "3b", "3c")}
    t2 = _table2()
    recs = []
    for y in RECEIPT_YEARS:
        d = pd.read_csv(RECEIPTS.format(y=y), low_memory=False)
        d = d[d["Plant Id"].astype(int).isin(plants) & (d.FUEL_GROUP == "Coal")]
        d = d.assign(mmbtu=d.QUANTITY * d["Average Heat Content"])
        msha = pd.to_numeric(d["Coalmine Msha Id"], errors="coerce")
        reg = msha.map(lambda m: by_id.get(int(m)) if pd.notna(m) else None)
        st = d["Coalmine State"].astype(str).str.strip().tolist()
        reg = [
            r if isinstance(r, str) else by_sc.get(k)
            for r, k in zip(reg, st, strict=True)
        ]
        d = d.assign(region=reg, year=y)
        recs.append(d)
    r = pd.concat(recs, ignore_index=True)
    r["tab"] = r["Primary Transportation Mode"].map(MODE_TABLE)
    r["priceable"] = r.region.isin(BASIN_SPOT) & r.tab.notna()
    out = []
    for pid, grp_name in plants.items():
        rp = r[r["Plant Id"].astype(int) == pid]
        if rp.empty or rp.mmbtu.sum() <= 0:
            continue
        state = str(rp["Plant State"].iloc[0])
        for y in YEARS:
            ry = rp[rp.year == y]
            basis = "own_year"
            if ry.empty or ry.mmbtu.sum() <= 0:
                ry, basis = rp, "pooled_2019_2024"
            tot = float(ry.mmbtu.sum())
            row = {"plant_id": pid, "group": grp_name, "year": y, "share_basis": basis}
            priced = 0.0
            for region, seg in BASIN_SPOT.items():
                for tab in ("3c", "3b", "3a"):
                    sel = ry[(ry.region == region) & (ry.tab == tab)]
                    if sel.empty:
                        continue
                    rate, rung = _rate(tabs, t2, region, state, tab, y)
                    if rate is None:
                        continue
                    hc = float(sel.mmbtu.sum() / sel.QUANTITY.sum())
                    s = float(sel.mmbtu.sum()) / tot
                    priced += s
                    out.append({**row, "spot_segment": seg, "mode_table": tab, "share": round(s, 6), "transport_usd_per_ton": rate, "heat_content_mmbtu_per_ton": round(hc, 4), "transport_usd_mmbtu": round(rate / hc, 6), "rate_rung": rung})  # fmt: skip
            out.append({**row, "spot_segment": "UNPRICED", "mode_table": "", "share": round(1.0 - priced, 6), "transport_usd_per_ton": np.nan, "heat_content_mmbtu_per_ton": np.nan, "transport_usd_mmbtu": np.nan, "rate_rung": ""})  # fmt: skip
    return pd.DataFrame(out)


def main() -> None:
    """Write both tables and print their headline measurements."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    gas, pool = derive_gas()
    OUT_GAS.parent.mkdir(parents=True, exist_ok=True)
    with OUT_GAS.open("w") as h:
        h.write(
            "# PJM gas VARIABLE transport over the owner-ruled IMM region hub ($/MMBtu).\n"
        )
        h.write(
            "# scripts/data/derive_pjm_replacement_fuel.py; EIA-923 receipts x IMM Platts monthly, 2019-2025 pooled.\n"
        )
        h.write(
            "# Rule 23: re-derive ONLY on a source-data update. Ladder: own -> zone_group -> group -> pjm (sibling .pool.csv).\n"
        )
        gas.to_csv(h, index=False)
    pool.to_csv(OUT_GAS.with_suffix(".pool.csv"), index=False)
    coal = derive_coal()
    with OUT_COAL.open("w") as h:
        h.write(
            "# PJM coal replacement cost: basin shares x (IMM Platts spot + EIA transport), per plant-year.\n"
        )
        h.write(
            "# scripts/data/derive_pjm_replacement_fuel.py. UNPRICED share keeps the plant's own print. Rule 23 frozen.\n"
        )
        coal.to_csv(h, index=False)
    mw = gas.nameplate_mw.to_numpy(float)
    v = gas.v_usd_mmbtu.to_numpy(float)
    print(
        f"gas: {len(gas)} plant-classes, v cap-weighted {float((v * mw).sum() / mw.sum()):+.4f}"
    )
    for g, x in gas.groupby("group"):
        print(
            f"  {g:10s} v cap-w {float((x.v_usd_mmbtu * x.nameplate_mw).sum() / x.nameplate_mw.sum()):+.3f}  sources {x.v_source.value_counts().to_dict()}"
        )
    un = coal[coal.spot_segment == "UNPRICED"]
    print(
        f"coal: {coal.plant_id.nunique()} plants; mean unpriced share {un.share.mean():.3f}"
    )
    pr = coal[coal.spot_segment != "UNPRICED"]
    print(
        pr.groupby(["spot_segment", "mode_table"])
        .transport_usd_mmbtu.describe()
        .round(3)
    )
    print(pr.rate_rung.value_counts().to_dict())
    print(f"wrote {OUT_GAS}, {OUT_GAS.with_suffix('.pool.csv')}, {OUT_COAL}")


if __name__ == "__main__":
    main()
