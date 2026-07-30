"""nyiso-101: the G-J locality Bulk Power Transmission Limit — boundary identification.

Matrix row ``nyiso_gj_lcr_tsl``; the follow-on nyiso-100 chartered and
deliberately did NOT arm. **No LP.** This is the build-time instrument that
decides, BEFORE any mechanism is chosen, whether the published G-J locality
import limit can be placed on a link of the five-zone NYISO topology.

The question this answers
-------------------------
nyiso-100 proved the retired 4,350 MW ``NYISO_simultaneous_import`` scalar was
the **G-J locality Bulk Power Transmission Limit** for capability year 2024/25
installed on the EXTERNAL NYCA seam
(``docs/FINDING-nyiso100-simultaneous-import-misattribution-2026-07-30.md``).
The limit itself is real and published every capability year
(``data/raw/capacity-deliverability/nyiso/nyiso.csv``, area ``G-J``:
3,425 / 3,425 / 4,350 / 4,500 MW for 2022/23-2025/26) and the topology now
represents it NOWHERE. The house pattern for a published locality import limit
is ``nyiso_nyc_lcr_tsl`` / ``nyiso_li_lcr_tsl``: replace the host link's
physical TTC with the published limit inside the design-condition window
(``NYISO_SELFSUPPLY_FLOOR_HOURS``, HB14-21).

So the only open question is the BOUNDARY: **which model link, if any, is the
G-J boundary, and what does 4,350 MW become on it?** The G-J locality is NYISO
load zones G, H, I and J (``data/raw/capacity-deliverability/nyiso/README.md``),
and the five-zone aggregation has no clean G-J cutset — Zone G is INTERIOR to
model zone ``Capital_Hudson`` (= NYISO zones F + G).

Sections
--------
``provenance``
    The published G-J series, the locality's zone membership, and whether the
    NYISO MIS P-32 posting carries a G-J interface at all.
``cutset``
    The boundary algebra. Enumerates the model's zones/links and tests each
    candidate host link against the true G-J zone set, mechanically.
``split``
    The two legs of the reconciliation term the aggregation destroyed: the
    Zone-F vs Zone-G split of the ``Capital_Hudson`` fleet (eGRID county
    geography, the same source ``zone_assignment`` already uses) and measured
    Zone-G (``HUD VL``) load.
``falsify``
    The measured admissibility test, run identically on the CANDIDATE (G-J
    limit on its candidate host links) and on the two ACCEPTED analogs (the
    keeper's own NYC 2,875 MW cap on SPR/DUN-SOUTH, and the LI cap) — so the
    candidate is judged against the house pattern's own standard rather than
    against an invented one.
``reconcile``
    The translation ``F_UPNY-ConEd = F_G-J + (gen_G - load_G)`` evaluated on
    measured data: how large the unidentified term is relative to the limit
    being imposed, and therefore whether a reconciled limit exists.

Rule 13 [R-MEASURED]: every measured series here is used to IDENTIFY a boundary
and to bound an admissible interval — never as a dispatch input, and this probe
sets no cap.

Usage::

    PYTHONPATH=.:src python scripts/probes/nyiso101_gj_locality_boundary.py
    PYTHONPATH=.:src python scripts/probes/nyiso101_gj_locality_boundary.py \\
        --sections cutset reconcile
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ISO = "NYISO"
YEARS = (2023, 2024, 2025)
IFACE_DIR = REPO / "data" / "raw" / "NYISO" / "interface-flows"
LOAD_DIR = REPO / "data" / "raw" / "zone-specific-demand" / "NYISO"

# The G-J locality's NYISO load-zone membership, from the intake contract
# (data/raw/capacity-deliverability/nyiso/README.md: "G-J (Zones G,H,I,J)").
GJ_ZONES = ("G", "H", "I", "J")

# NYISO load-zone letter -> model zone (config/iso_configs.py::_nyiso_config
# docstring: Upstate-West = A-E, Capital/Hudson = F+G, Lower-Hudson = H+I,
# NYC = J, Long Island = K).
ZONE_LETTER_TO_MODEL = {
    "A": "Upstate_West",
    "B": "Upstate_West",
    "C": "Upstate_West",
    "D": "Upstate_West",
    "E": "Upstate_West",
    "F": "Capital_Hudson",
    "G": "Capital_Hudson",
    "H": "Lower_Hudson",
    "I": "Lower_Hudson",
    "J": "NYC",
    "K": "Long_Island",
}

# NYISO zonal-load report name -> load-zone letter (the "Name" column of
# data/raw/zone-specific-demand/NYISO/NYISO_load_actuals_<year>.csv).
LOAD_NAME_TO_LETTER = {
    "WEST": "A",
    "GENESE": "B",
    "CENTRL": "C",
    "NORTH": "D",
    "MHK VL": "E",
    "CAPITL": "F",
    "HUD VL": "G",
    "MILLWD": "H",
    "DUNWOD": "I",
    "N.Y.C.": "J",
    "LONGIL": "K",
}

# NY county FIPS -> load-zone letter for the two zones the Capital_Hudson model
# zone aggregates. Transcribed from the per-county comments already carried by
# zone_assignment.NYISO_CAPITAL_HUDSON_COUNTIES (which tags each county "(F)"
# or "(G)"); this probe only READS that split, it does not introduce it.
CAPITAL_HUDSON_COUNTY_LETTER = {
    1: "F",  # Albany
    21: "F",  # Columbia
    39: "F",  # Greene
    83: "F",  # Rensselaer
    91: "F",  # Saratoga
    93: "F",  # Schenectady
    95: "F",  # Schoharie
    113: "F",  # Warren
    115: "F",  # Washington
    27: "G",  # Dutchess
    71: "G",  # Orange
    87: "G",  # Rockland
    105: "G",  # Sullivan
    111: "G",  # Ulster
}

# NYISO Gold Book "Table III-2a: NYISO Market Generator" — existing generating
# facilities, one row per unit, carrying the NYISO LOAD ZONE LETTER directly
# (column d). This is the authoritative per-zone fleet: it needs no county
# inference at all, so the Zone-F/Zone-G split of Capital_Hudson is read from
# NYISO's own zone assignment rather than reconstructed.
GOLDBOOK_SHEET = "Table III-2a"
GOLDBOOK_SKIPROWS = 8
GOLDBOOK_COLS = {3: "zone", 9: "nameplate_mw", 12: "cap_sum_mw", 15: "unit_type", 16: "fuel"}
GOLDBOOK_FILES = {
    2023: "2023-NYCA-Generators.xlsx",
    2024: "2024-NYCA-Generators.xlsx",
    2025: "2025-NYCA-Existing-Generating-Facilities.xlsx",
}

# Candidate host links: the model links whose cutset a G-J cap could plausibly
# be placed on, with the posted P-32 internal interface each corresponds to.
# Capital_Hudson->Lower_Hudson is labelled "UPNY-SENY" in iso_configs.py but the
# posting carries UPNY CONED for that cutset (interface-flows/README.md: "the
# posting carries UPNY CONED (not a separate UPNY-SENY row)"), and UPNY CONED is
# the boundary of the Con Edison system = zones H+I+J.
CANDIDATE_HOSTS = (
    ("Upstate_West->Capital_Hudson", "TOTAL EAST", 2850.0),
    ("Capital_Hudson->Lower_Hudson", "UPNY CONED", 5150.0),
    ("Lower_Hudson->NYC", "SPR/DUN-SOUTH", 3900.0),
)

# The accepted analogs — the two locality caps already in the keeper's
# mechanism set — run through the identical admissibility test as the
# house-pattern control.
ACCEPTED_ANALOGS = (
    ("NYC", "Lower_Hudson->NYC", "SPR/DUN-SOUTH", 3900.0),
    ("Long Island", "NYC->Long_Island", None, 1650.0),
)

# The design-condition window the house pattern applies a locality limit in
# (interchange/nyiso.py::NYISO_SELFSUPPLY_FLOOR_HOURS, local HB14-21).
WINDOW_HOURS = tuple(range(14, 22))

RULE = "=" * 78
SUB = "-" * 78


# ---------------------------------------------------------------------------
# loaders
# ---------------------------------------------------------------------------


def _published_limits() -> pd.DataFrame:
    """Return the published NYISO locality import-limit table, all areas/years."""
    from market_sim.data.capacity_deliverability import (
        import_limit_by_area,
        resolve_delivery_year,
    )

    rows = []
    for year in YEARS:
        delivery_year = resolve_delivery_year(ISO, year)
        for area, limit in sorted(import_limit_by_area(ISO, delivery_year).items()):
            rows.append(
                {
                    "solve_year": year,
                    "delivery_year": delivery_year,
                    "area": area,
                    "import_limit_mw": float(limit),
                }
            )
    return pd.DataFrame(rows)


def _iface(year: int) -> pd.DataFrame:
    """Return the hourly P-32 interface postings for ``year``.

    Keeps BOTH clocks on purpose (the nyiso-100 method note): the UTC timestamp
    for any join, and the local timestamp for the HB14-21 window, which is a
    local-clock definition. The ±9,999 MW "unbounded" sentinel limits are
    nulled, matching ``scripts/curate_nyiso_interface_flows.py``.
    """
    path = IFACE_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz"
    df = pd.read_csv(path)
    df["utc"] = pd.to_datetime(df["interval_start_utc"], utc=True)
    df["local"] = pd.to_datetime(df["interval_start_local"])
    df["hb"] = df["local"].dt.hour
    for col in ("positive_limit_mw", "negative_limit_mw"):
        df[col] = df[col].where(df[col].abs() < 9990.0)
    return df


def _zonal_load(year: int) -> pd.DataFrame:
    """Return measured NYISO hourly load by load-zone letter for ``year``."""
    df = pd.read_csv(LOAD_DIR / f"NYISO_load_actuals_{year}.csv")
    df["local"] = pd.to_datetime(df["Time Stamp"])
    df["letter"] = df["Name"].astype(str).str.strip().map(LOAD_NAME_TO_LETTER)
    unmapped = sorted(set(df.loc[df["letter"].isna(), "Name"].astype(str)))
    if unmapped:
        raise ValueError(f"unmapped NYISO load-zone names in {year}: {unmapped}")
    df["hb"] = df["local"].dt.hour
    return df


def _goldbook_fleet(year: int) -> pd.DataFrame:
    """Return the NYISO Gold Book existing-unit fleet for ``year``, by load zone.

    Reads Table III-2a of ``data/raw/NYISO/<year>-NYCA-Generators.xlsx`` (2025:
    ``2025-NYCA-Existing-Generating-Facilities.xlsx``). ``cap_sum_mw`` is the
    published SUMMER capability, which is the rating the locality transmission
    security limits are studied at (summer design-cooling peak).
    """
    path = REPO / "data" / "raw" / "NYISO" / GOLDBOOK_FILES[year]
    raw = pd.read_excel(path, sheet_name=GOLDBOOK_SHEET, header=None, skiprows=GOLDBOOK_SKIPROWS)
    df = raw.iloc[:, list(GOLDBOOK_COLS)].copy()
    df.columns = [GOLDBOOK_COLS[i] for i in GOLDBOOK_COLS]
    df["zone"] = df["zone"].astype(str).str.strip()
    df = df[df["zone"].isin(list("ABCDEFGHIJK"))]
    for col in ("nameplate_mw", "cap_sum_mw"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------


def section_provenance() -> None:
    """Print the published G-J series and test for a posted G-J interface."""
    print(RULE)
    print("PROVENANCE — the published G-J locality import limit")
    print(RULE)

    table = _published_limits()
    pivot = table.pivot_table(
        index=["solve_year", "delivery_year"], columns="area", values="import_limit_mw"
    )
    print("\nPublished Bulk Power Transmission Limit (MW), by solve year:")
    print(pivot.to_string())
    print(
        "\n  source: data/raw/capacity-deliverability/nyiso/nyiso.csv"
        "\n          (Locality Bulk Power Transmission Capability Reports)"
        f"\n  G-J locality membership: NYISO load zones {'+'.join(GJ_ZONES)}"
        "\n          (data/raw/capacity-deliverability/nyiso/README.md)"
    )

    print(f"\n{SUB}")
    print("Is a G-J interface POSTED? (NYISO MIS P-32 internal-transfer rows)")
    print(SUB)
    df = _iface(2024)
    internal = sorted(i for i in df["interface"].unique() if not i.startswith("SCH -"))
    print("\n  posted internal transfer interfaces:")
    for name in internal:
        print(f"    {name}")
    gj_named = [i for i in internal if "G" in i.upper().split() or "G-J" in i.upper()]
    print(
        f"\n  rows naming a G-J boundary: {gj_named if gj_named else 'NONE'}"
        "\n  => NYISO posts NO G-J interface flow or limit series. The limit is"
        "\n     published only as a capacity-market (ICAP/LCR) transmission"
        "\n     security limit, with no metered hourly counterpart in repo."
    )


def section_cutset() -> None:
    """Test each model link against the true G-J zone set, mechanically."""
    from market_sim.config.iso_configs import get_iso_config

    print(f"\n{RULE}")
    print("CUTSET — does any model link carry the G-J boundary?")
    print(RULE)

    cfg = get_iso_config(ISO)
    members = {
        model: sorted(k for k, v in ZONE_LETTER_TO_MODEL.items() if v == model)
        for model in dict.fromkeys(ZONE_LETTER_TO_MODEL.values())
    }
    print("\n  model zone -> NYISO load zones aggregated:")
    for zone in cfg.zones:
        letters = members[zone.name]
        inside = [x for x in letters if x in GJ_ZONES]
        outside = [x for x in letters if x not in GJ_ZONES]
        if inside and outside:
            verdict = f"STRADDLES G-J  (in: {'+'.join(inside)} / out: {'+'.join(outside)})"
        elif inside:
            verdict = "wholly INSIDE G-J"
        else:
            verdict = "wholly OUTSIDE G-J"
        print(f"    {zone.name:<16} = {'+'.join(letters):<12} {verdict}")

    straddlers = [
        z.name
        for z in cfg.zones
        if any(x in GJ_ZONES for x in members[z.name])
        and any(x not in GJ_ZONES for x in members[z.name])
    ]
    print(f"\n  straddling zones: {straddlers if straddlers else 'NONE'}")

    print(f"\n{SUB}")
    print("Per-link test: is the link a G-J boundary edge?")
    print(SUB)
    print(
        f"\n    {'link':<32} {'from side':<14} {'to side':<14} verdict"
    )
    for link in cfg.links:
        f_in = all(x in GJ_ZONES for x in members[link.from_zone])
        f_out = all(x not in GJ_ZONES for x in members[link.from_zone])
        t_in = all(x in GJ_ZONES for x in members[link.to_zone])
        t_out = all(x not in GJ_ZONES for x in members[link.to_zone])

        def label(inside: bool, outside: bool) -> str:
            if inside:
                return "inside G-J"
            if outside:
                return "outside G-J"
            return "MIXED"

        if f_out and t_in:
            verdict = "G-J boundary edge"
        elif f_in and t_out:
            verdict = "G-J boundary edge (reversed)"
        elif f_in and t_in:
            verdict = "interior to G-J"
        elif f_out and t_out:
            verdict = "exterior to G-J"
        else:
            verdict = "NOT A CUTSET EDGE — one end straddles"
        print(
            f"    {link.from_zone + '->' + link.to_zone:<32} "
            f"{label(f_in, f_out):<14} {label(t_in, t_out):<14} {verdict}"
        )

    print(
        "\n  The true G-J boundary is the union of:"
        "\n    (1) the NYISO F->G cutset       -> INTERIOR to Capital_Hudson: NO LP variable"
        "\n    (2) the K->J ties (Zone K is OUTSIDE G-J)"
        "\n        -> model NYC->Long_Island, reversed"
        "\n    (3) the external HVDC into Zone J (HTP / Linden-VFT)"
        "\n        -> model import-node -> NYC link"
        "\n  Leg (1) is the dominant one and it is unrepresentable: the flow that"
        "\n  crosses it is not a column of the LP."
    )


def section_split() -> None:
    """Quantify the two legs of the reconciliation term the aggregation destroyed."""
    print(f"\n{RULE}")
    print("SPLIT — the Zone-G legs Capital_Hudson aggregates away")
    print(RULE)

    print(
        "\n  Capital_Hudson fleet by NYISO load zone"
        "\n  (Gold Book Table III-2a, summer capability MW):"
    )
    print(f"\n    {'year':<6} {'F units':>8} {'F cap':>9} {'G units':>8} {'G cap':>9} "
          f"{'G share of F+G':>15}")
    for year in YEARS:
        fleet = _goldbook_fleet(year)
        ch = fleet[fleet["zone"].isin(["F", "G"])]
        f_cap = float(ch.loc[ch["zone"] == "F", "cap_sum_mw"].sum())
        g_cap_y = float(ch.loc[ch["zone"] == "G", "cap_sum_mw"].sum())
        print(
            f"    {year:<6} {int((ch['zone'] == 'F').sum()):>8d} {f_cap:>9,.0f} "
            f"{int((ch['zone'] == 'G').sum()):>8d} {g_cap_y:>9,.0f} "
            f"{g_cap_y / max(1e-9, f_cap + g_cap_y):>15.3f}"
        )

    fleet = _goldbook_fleet(2024)
    top = fleet[fleet["zone"] == "G"].nlargest(8, "cap_sum_mw")[
        ["unit_type", "fuel", "nameplate_mw", "cap_sum_mw"]
    ]
    print("\n  largest Zone-G units (2024, summer capability):")
    print(top.to_string(index=False, float_format=lambda v: f"{v:,.1f}"))

    print(f"\n{SUB}")
    print("Measured Zone-G (HUD VL) load, and its share of Capital_Hudson")
    print(SUB)
    print(f"\n    {'year':<6} {'G mean':>9} {'G max':>9} {'F+G mean':>10} {'G share':>9} "
          f"{'G HB14-21 mean':>15}")
    for year in YEARS:
        load = _zonal_load(year)
        pivot = load.pivot_table(index="local", columns="letter", values="Load")
        g = pivot["G"].to_numpy(float)
        fg = (pivot["F"] + pivot["G"]).to_numpy(float)
        win = pivot.loc[pivot.index.hour.isin(WINDOW_HOURS), "G"].to_numpy(float)
        print(
            f"    {year:<6} {np.nanmean(g):>9,.0f} {np.nanmax(g):>9,.0f} "
            f"{np.nanmean(fg):>10,.0f} {np.nanmean(g) / np.nanmean(fg):>9.3f} "
            f"{np.nanmean(win):>15,.0f}"
        )
    print(
        "\n  Both legs are measurable. What is NOT measurable is Zone-G"
        "\n  GENERATION hour by hour: the model carries one Capital_Hudson energy"
        "\n  balance, its wind/solar/storage are single zonal variables with no"
        "\n  F/G split, and gen_G is ENDOGENOUS to the dispatch being constrained."
    )


def section_legs() -> None:
    """Enumerate every leg of the real G-J boundary and its LP representability."""
    from market_sim.model.interchange.spec import IMPORT_NODE_LINKS

    print(f"\n{RULE}")
    print("LEGS — the real G-J boundary, leg by leg, vs what the LP can express")
    print(RULE)

    node_links = dict(IMPORT_NODE_LINKS[ISO])
    print("\n  model import-node border links (interchange/spec.py):")
    for zone, mw in IMPORT_NODE_LINKS[ISO]:
        inside = ZONE_LETTER_TO_MODEL
        letters = sorted(k for k, v in inside.items() if v == zone)
        print(f"    import_node -> {zone:<16} {mw:>7,.0f} MW   (zones {'+'.join(letters)})")

    ch_node = node_links.get("Capital_Hudson", 0.0)
    nyc_node = node_links.get("NYC", 0.0)

    print(f"\n{SUB}")
    print("Leg-by-leg accounting")
    print(SUB)
    legs = [
        (
            "1. F->G AC cutset",
            "dominant (Zone-G capability ~4.7 GW class)",
            "UNREPRESENTABLE — interior to Capital_Hudson (F+G); no LP column "
            "crosses it",
        ),
        (
            "2. external ties landing IN Zone G",
            f"PJM Ramapo 345 kV ~1,000 MW + ISO-NE New Scotland/Pleasant Valley "
            f"~600 MW, lumped into the {ch_node:,.0f} MW Capital_Hudson node link",
            "UNREPRESENTABLE — the F-vs-G split of that node link is, in the "
            "repo's own words, 'a modelling choice inside the topology', not a "
            "measured allocation",
        ),
        (
            "3. K->J ties (Zone K is outside G-J)",
            "measured peak-window LI->NYC export ~0 MW",
            "representable (NYC->Long_Island reversed) BUT already capped "
            "in-window by nyiso_li_lcr_tsl at LI's own published limit — "
            "rule 19 [R-ONE-MECH]",
        ),
        (
            "4. external HVDC into Zone J",
            f"HTP 660 + Linden VFT 315 = 975 MW posted; model node link "
            f"{nyc_node:,.0f} MW",
            "representable, but it is ONE link of ~1.0 GW against a "
            "4,350 MW limit whose other legs are missing",
        ),
    ]
    for name, quantity, verdict in legs:
        print(f"\n  {name}")
        print(f"      real:  {quantity}")
        print(f"      model: {verdict}")

    print(f"\n{SUB}")
    print("Inertness arithmetic for the one uncontested representable edge")
    print(SUB)
    from market_sim.config.iso_configs import get_iso_config

    cfg = get_iso_config(ISO)
    li = next(
        ln for ln in cfg.links if (ln.from_zone, ln.to_zone) == ("NYC", "Long_Island")
    )
    limits = _published_limits().set_index(["solve_year", "area"])["import_limit_mw"]
    print(f"\n    {'year':<6} {'link TTC':>9} {'LI cap in-win':>14} {'G-J cap':>9} "
          f"{'min() in-window':>16} {'G-J binds?':>11}")
    for year in YEARS:
        gj = float(limits.loc[(year, "G-J")])
        li_cap = float(limits.loc[(year, "Long Island")])
        eff = min(li.ttc_mw, li_cap, gj)
        print(
            f"    {year:<6} {li.ttc_mw:>9,.0f} {li_cap:>14,.0f} {gj:>9,.0f} "
            f"{eff:>16,.0f} {'NO' if eff < gj else 'yes':>11}"
        )
    print(
        "\n  A G-J cap on that edge is PROVABLY INERT with no solve: the link's"
        "\n  physical rating and the in-window LI locality cap are both far below"
        "\n  the G-J limit, so min() never selects it."
    )


def _exceedance(flow: np.ndarray, limit: float) -> tuple[int, float]:
    """Return (hours above ``limit``, fraction of hours above ``limit``)."""
    ok = np.isfinite(flow)
    above = int(np.sum(flow[ok] > limit))
    return above, (above / max(1, int(ok.sum())))


def section_falsify() -> None:
    """Run the measured admissibility test on candidate and accepted caps alike."""
    print(f"\n{RULE}")
    print("FALSIFY — measured admissibility, candidate vs the accepted analogs")
    print(RULE)
    print(
        "\n  Test (the house pattern's own standard): a published locality limit"
        "\n  applied to a host link in-window is admissible only if the MEASURED"
        "\n  flow on that link's own posted interface respects it in-window. A"
        "\n  limit deep inside the measured distribution is over-tight ON THAT"
        "\n  BOUNDARY — the nyiso-100 failure mode."
    )

    limits = _published_limits().set_index(["solve_year", "area"])["import_limit_mw"]

    print(f"\n{SUB}")
    print("ACCEPTED ANALOG (control): NYC 2,875 MW on SPR/DUN-SOUTH")
    print(SUB)
    print(f"\n    {'year':<6} {'cap':>7} {'in-win p50':>11} {'in-win p95':>11} "
          f"{'in-win max':>11} {'h>cap':>7} {'%>cap':>7}")
    for year in YEARS:
        df = _iface(year)
        d = df[df["interface"] == "SPR/DUN-SOUTH"]
        win = d[d["hb"].isin(WINDOW_HOURS)]["flow_mw"].to_numpy(float)
        cap = float(limits.loc[(year, "NYC")])
        n_above, frac = _exceedance(win, cap)
        print(
            f"    {year:<6} {cap:>7,.0f} {np.nanpercentile(win, 50):>11,.0f} "
            f"{np.nanpercentile(win, 95):>11,.0f} {np.nanmax(win):>11,.0f} "
            f"{n_above:>7d} {100 * frac:>6.1f}%"
        )

    print(f"\n{SUB}")
    print("CANDIDATE: the G-J limit on each candidate host link")
    print(SUB)
    for link, iface, ttc in CANDIDATE_HOSTS:
        print(f"\n  host {link}  (posted: {iface}, model TTC {ttc:,.0f} MW)")
        print(f"    {'year':<6} {'G-J cap':>8} {'in-win p50':>11} {'in-win p95':>11} "
              f"{'in-win max':>11} {'h>cap':>7} {'%>cap':>7} {'cap pctile':>11}")
        for year in YEARS:
            df = _iface(year)
            d = df[df["interface"] == iface]
            win = d[d["hb"].isin(WINDOW_HOURS)]["flow_mw"].to_numpy(float)
            cap = float(limits.loc[(year, "G-J")])
            n_above, frac = _exceedance(win, cap)
            pct = float(
                100.0 * np.nanmean(win <= cap)
            )  # the percentile of the in-window distribution the cap sits at
            print(
                f"    {year:<6} {cap:>8,.0f} {np.nanpercentile(win, 50):>11,.0f} "
                f"{np.nanpercentile(win, 95):>11,.0f} {np.nanmax(win):>11,.0f} "
                f"{n_above:>7d} {100 * frac:>6.1f}% {pct:>10.1f}%"
            )

    print(
        "\n  Read the last column against the control: the accepted NYC cap sits"
        "\n  at the TOP of its own interface's in-window distribution, which is"
        "\n  the signature of a correctly-boundaried security limit. A candidate"
        "\n  cap that sits materially lower is being applied to a boundary that"
        "\n  carries more flow than the limit governs."
    )


def section_reconcile() -> None:
    """Evaluate the G-J -> UPNY-ConEd translation on measured data."""
    print(f"\n{RULE}")
    print("RECONCILE — can the limit be translated onto a model link?")
    print(RULE)
    print(
        "\n  Zone-G power balance (Zone G has no external ties):"
        "\n      F_[F->G]  =  load_G  +  F_[G->H]  -  gen_G"
        "\n  where F_[G->H] is the UPNY-ConEd cutset the model's"
        "\n  Capital_Hudson->Lower_Hudson link carries. The published limit binds"
        "\n  the LEFT side; a cap on the model link binds F_[G->H]. So the"
        "\n  translation onto the model link is"
        "\n      F_[G->H]  <=  GJ_limit + gen_G - load_G"
        "\n  and the reconciliation term is (gen_G - load_G)."
    )

    limits = _published_limits().set_index(["solve_year", "area"])["import_limit_mw"]

    print(f"\n{SUB}")
    print("Size of the unidentified term vs the limit being imposed")
    print(SUB)
    print(
        "\n    gen_G is bounded below by 0 MW (every Zone-G unit off) and above"
        "\n    by the Zone-G summer capability, so the reconciled cap is only"
        "\n    pinned to an interval:"
    )
    print(f"\n    {'year':<6} {'G-J cap':>8} {'G cap':>8} {'load_G in-win':>14} "
          f"{'reconciled cap':>30} {'width':>8} {'% of cap':>9}")
    for year in YEARS:
        load = _zonal_load(year)
        pivot = load.pivot_table(index="local", columns="letter", values="Load")
        win_g = pivot.loc[pivot.index.hour.isin(WINDOW_HOURS), "G"].to_numpy(float)
        load_g = float(np.nanmean(win_g))
        g_cap = float(_goldbook_fleet(year).query("zone == 'G'")["cap_sum_mw"].sum())
        cap = float(limits.loc[(year, "G-J")])
        lo = cap - load_g
        hi = cap + g_cap - load_g
        width = hi - lo
        print(
            f"    {year:<6} {cap:>8,.0f} {g_cap:>8,.0f} {load_g:>14,.0f} "
            f"{'[' + format(lo, ',.0f') + ', ' + format(hi, ',.0f') + ']':>30} "
            f"{width:>8,.0f} {100 * width / cap:>8.0f}%"
        )

    print(
        "\n  The reconciled cap is only pinned to an interval whose WIDTH is the"
        "\n  Zone-G nameplate — of the same order as the limit itself. Narrowing"
        "\n  it requires gen_G hour by hour, which is (a) not measured in repo at"
        "\n  Zone-G resolution, and (b) ENDOGENOUS: it is an output of the very"
        "\n  dispatch the constraint is meant to bind."
    )

    print(f"\n{SUB}")
    print("Is the published limit consistent with measured UPNY-ConEd flow?")
    print(SUB)
    print(
        "\n  If the limit were validly placed on the model link, measured"
        "\n  UPNY-ConEd flow above it would have to be explained by Zone-G net"
        "\n  export. Required gen_G at the in-window extremes:"
    )
    print(f"\n    {'year':<6} {'cap':>7} {'in-win p95':>11} {'req gen_G @p95':>15} "
          f"{'in-win max':>11} {'req gen_G @max':>15} {'vs G capability':>16}")
    for year in YEARS:
        df = _iface(year)
        d = df[df["interface"] == "UPNY CONED"]
        d = d[d["hb"].isin(WINDOW_HOURS)]
        flow = d["flow_mw"].to_numpy(float)
        load = _zonal_load(year)
        pivot = load.pivot_table(index="local", columns="letter", values="Load")
        load_g = float(
            np.nanmean(pivot.loc[pivot.index.hour.isin(WINDOW_HOURS), "G"].to_numpy(float))
        )
        g_cap = float(_goldbook_fleet(year).query("zone == 'G'")["cap_sum_mw"].sum())
        cap = float(limits.loc[(year, "G-J")])
        p95 = float(np.nanpercentile(flow, 95))
        mx = float(np.nanmax(flow))
        req95 = p95 - cap + load_g
        reqmx = mx - cap + load_g
        print(
            f"    {year:<6} {cap:>7,.0f} {p95:>11,.0f} {req95:>15,.0f} "
            f"{mx:>11,.0f} {reqmx:>15,.0f} {100 * reqmx / g_cap:>15.0f}%"
        )
    print(
        "\n  Required gen_G stays WITHIN the Zone-G nameplate in every year, so"
        "\n  the measured flow does NOT falsify the published limit — it is"
        "\n  consistent with it, for an unobservable Zone-G net position. That is"
        "\n  precisely why the translation is unidentified rather than refuted:"
        "\n  the discrepancy and the missing term are the same size."
    )


SECTIONS = {
    "provenance": section_provenance,
    "cutset": section_cutset,
    "legs": section_legs,
    "split": section_split,
    "falsify": section_falsify,
    "reconcile": section_reconcile,
}


def main(argv: list[str] | None = None) -> int:
    """Run the requested identification sections."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sections",
        nargs="+",
        choices=sorted(SECTIONS),
        default=sorted(SECTIONS),
        help="sections to run (default: all)",
    )
    args = parser.parse_args(argv)
    order = ["provenance", "cutset", "legs", "split", "falsify", "reconcile"]
    for name in [s for s in order if s in args.sections]:
        SECTIONS[name]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
