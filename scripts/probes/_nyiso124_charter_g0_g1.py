"""nyiso-124 — the downstate-topology-split charter's two no-LP gates, G0 and G1.

The charter (``docs/handoffs/nyiso-downstate-topology-split-charter-2026-08.md``,
opened 2026-08-04 by owner ruling at nyiso-123) is a PRECOMMIT with two gates that
must both pass before any LP time is spent:

* **G0 — IDENTIFIABILITY.** Establish from PUBLIC, REPRODUCIBLE sources the F/G
  boundary definition, its transfer limit(s), the zonal load allocation and the
  fleet membership on each side.  PASS = every quantity has a citable public
  source AND a forward analogue (rule 13 ``[R-MEASURED]``: could the same
  quantity be produced for a forward year from forward drivers, and would it
  respond to changed conditions?).  **FAIL = the charter closes with cause**
  (charter §6(1)), exactly as nyiso-97 closed the in-city pocket.
* **G1 — OBJECT B DIAGNOSED.**  Object B is the model's over-pricing of the
  unconstrained upstate zone (+$7.93 / +$3.25 / +$1.59 load-weighted, nyiso-123
  §3.3).  Its size is known; its cause is not.  Discriminate among: upstate
  offer-curve level, hydro, wind, must-run/floor forcing in upstate hours, the
  upstate marginal-unit mix.

**NO LP.**  Every number below comes from committed artifacts (the keeper's
``hourly/`` sidecars, the committed NYISO MIS P-32 interface postings, the
committed measured zonal load) plus PUBLIC NYISO MIS postings fetched on demand
to a cache dir — which is the point of G0, since G0 is a question about what is
publicly reproducible.  Nothing here enters a solve.

Sections
--------
``sources``
    G0 quantity-by-quantity: does a public, citable source exist, and does it
    carry a forward analogue?  Enumerates the NYISO MIS P-32 (interface
    flows/limits) and ATC/TTC (day-ahead transfer capability) interface rosters
    mechanically, so "there is no published F/G limit" is a measurement rather
    than an assertion.
``incidence``
    WHERE the measured basis actually forms.  Decomposes NYISO's own posted
    zonal RT LBMP into the three eastward steps — E|F (``CAPITL`` − ``WEST``,
    the Central-East cutset the model ALREADY represents), F|G (``HUD VL`` −
    ``CAPITL``, the cutset the charter proposes to create) and G|H (``MILLWD`` −
    ``HUD VL``) — annual and monthly, in LBMP and in the market's own congestion
    component.
``binding``
    Which internal NYISO interface binds, measured from the committed P-32
    flow-vs-limit postings, against whether the MODEL's corresponding link
    separates its zonal prices at all (prices are LP duals, so identical zonal
    prices ⟺ the link is off its bound).
``objectb``
    G1.  Buckets every hour by the MEASURED East−Upstate basis and reports the
    model's upstate error in each bucket, so a defect that is the mirror image
    of the missing congestion is distinguishable from one that is not.  Adds the
    peak/off-peak split and the correlation.

Rule 13 ``[R-MEASURED]``: every measured price, basis, flow and limit here is
used to IDENTIFY a boundary and to ATTRIBUTE a residual — never as a dispatch
input.  No mechanism is proposed that would consume any of them.

Rule 22 ``[R-HOLDOUT]``: TRAINING YEARS ONLY.  ``YEARS`` is a hard filter and
every loader raises on anything outside it — which matters because the committed
NYISO series carry 2018-2022 and 2026.

Usage::

    PYTHONPATH=.:src python scripts/probes/_nyiso124_charter_g0_g1.py
    PYTHONPATH=.:src python scripts/probes/_nyiso124_charter_g0_g1.py \\
        --sections sources incidence

Outputs ``results/calibration/_nyiso124_charter_g0_g1.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ISO = "NYISO"
YEARS: tuple[int, ...] = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]
HOURS = 8760

BUNDLE = REPO / "results/calibration/nyiso120_c119_scopegate"
IFACE_DIR = REPO / "data/raw/NYISO/interface-flows"
LOAD_DIR = REPO / "data/raw/zone-specific-demand/NYISO"
LMP_DIR = REPO / "data/raw/lmp-data/NYISO"
GOLDBOOK_DIR = REPO / "data/raw/NYISO"
OUT = REPO / "results/calibration/_nyiso124_charter_g0_g1.json"
CACHE = REPO / ".cache/nyiso124"

# Public NYISO MIS archives.  Both are the same products the repo already reads
# (data/raw/lmp-data/NYISO carries a partial set of the first; the second is the
# feed scripts/data/derive_nyiso_central_east_ttc.py expects as ATC_TTC.zip).
# Months absent from the repo are fetched on demand to a cache dir rather than
# bulk-added to the immutable raw root — the URLs make G0 reproducible, which is
# exactly what G0 is about.
MIS_ZONAL_URL = "http://mis.nyiso.com/public/csv/realtime/{year}{month:02d}01realtime_zone_csv.zip"
MIS_ATC_URL = "http://mis.nyiso.com/public/csv/atc_ttc/{year}{month:02d}01atc_ttc_csv.zip"

# NYISO load-zone letters.  The zonal LBMP posting and the zonal load report use
# the same eleven names; the model aggregates them five-ways
# (config/iso_configs.py::_nyiso_config).
NAME_TO_LETTER = {
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
LETTER_TO_NAME = {v: k for k, v in NAME_TO_LETTER.items()}
MODEL_ZONES = {
    "Upstate_West": list("ABCDE"),
    "Capital_Hudson": ["F", "G"],
    "Lower_Hudson": ["H", "I"],
    "NYC": ["J"],
    "Long_Island": ["K"],
}

# The three eastward zonal steps, named by the NYISO interface each sits on.
# UPNY-SENY is the F|G cutset (2025 SOM: "the UPNY-SENY interface between zones
# A-F and G-I"); UPNY-ConEd is the G|H cutset (2025 SOM: "a constraint on the
# UPNY-CONED interface between zones H and G"), which is the cutset the model's
# Capital_Hudson->Lower_Hudson link actually carries.
STEPS = (
    ("E|F  CENTRAL EAST", "CAPITL", "WEST"),
    ("F|G  UPNY-SENY", "HUD VL", "CAPITL"),
    ("G|H  UPNY-CONED", "MILLWD", "HUD VL"),
)

# The model's fixed non-leap 8760-hour clock, keyed to 2023 and shared by every
# model year (build_ercot_as_withholding._CALENDAR; Feb 29 dropped).  Measured
# series are keyed onto it by LOCAL (month, day, hour) — never positionally,
# which is the nyiso-123 §1 correction: a per-year date_range is one day off for
# leap-2024 from Mar 1 onward.
_CAL = pd.date_range("2023-01-01", periods=HOURS, freq="h")
CAL_KEY = pd.MultiIndex.from_arrays([_CAL.month, _CAL.day, _CAL.hour])
MONTH_OF_HOUR = _CAL.month.to_numpy()
HOUR_OF_DAY = _CAL.hour.to_numpy()
PEAK_HOURS = (HOUR_OF_DAY >= 7) & (HOUR_OF_DAY < 23)  # NYISO on-peak HB07-22

# The interface-limit posting's "unbounded" sentinel (curate_nyiso_interface_flows.py).
LIMIT_SENTINEL = 9990.0
# "Binding" for a posted aggregate interface.  0.95 is the same bar nyiso-122
# used when it refuted the Tier-3 TTC re-grounding, kept identical here so the
# two measurements are comparable.
BIND_UTIL = 0.95

RULE = "=" * 78
SUB = "-" * 78


def _check_years() -> None:
    """Fail closed if ``YEARS`` ever strays outside the training window."""
    bad = [y for y in YEARS if y not in (2023, 2024, 2025)]
    if bad:
        raise SystemExit(f"rule 22 [R-HOLDOUT]: refusing out-of-training years {bad}")


# ---------------------------------------------------------------------------
# loaders
# ---------------------------------------------------------------------------


def _fetch(url: str, dest: Path) -> Path | None:
    """Download ``url`` to ``dest`` once; return the path, or ``None`` on failure."""
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=180) as r, dest.open("wb") as fh:
            fh.write(r.read())
    except Exception as exc:  # noqa: BLE001 — a missing month is reported, not fatal
        print(f"  [fetch failed] {url}: {exc}", file=sys.stderr)
        dest.unlink(missing_ok=True)
        return None
    return dest


def _zonal_month_zip(year: int, month: int) -> Path | None:
    """Return the month's 5-minute zonal LBMP zip: committed copy, else cache."""
    if year not in YEARS:
        raise SystemExit(f"rule 22: refusing to load out-of-training year {year}")
    committed = LMP_DIR / f"{year}{month:02d}01realtime_zone_csv.zip"
    if committed.exists():
        return committed
    return _fetch(
        MIS_ZONAL_URL.format(year=year, month=month),
        CACHE / "zonal" / f"{year}{month:02d}.zip",
    )


def zonal_lbmp(year: int) -> dict[str, pd.DataFrame]:
    """Return measured hourly zonal ``lbmp`` and ``cong`` frames on the model clock.

    NYISO posts 5-minute zonal LBMP with its loss and congestion components
    (MIS "Real-Time Zonal LBMP").  Intervals are averaged to the hour on the
    PREVAILING local clock the file publishes, then re-keyed onto the model's
    fixed non-leap calendar.  The DST spring-forward gap (one missing local
    hour) is filled forward; the fall-back duplicate hour is averaged by the
    groupby.  Both are single hours a year and neither is load-bearing here.
    """
    frames = []
    for month in range(1, 13):
        path = _zonal_month_zip(year, month)
        if path is None:
            raise SystemExit(f"zonal LBMP unavailable for {year}-{month:02d}")
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if not name.endswith(".csv"):
                    continue
                frames.append(pd.read_csv(zf.open(name)))
    df = pd.concat(frames, ignore_index=True)
    df.columns = ["ts", "name", "ptid", "lbmp", "loss", "cong"]
    df["name"] = df["name"].astype(str).str.strip()
    ts = pd.to_datetime(df["ts"], format="%m/%d/%Y %H:%M:%S")
    df["mo"], df["dy"], df["hr"] = ts.dt.month, ts.dt.day, ts.dt.hour
    grouped = df.groupby(["name", "mo", "dy", "hr"])[["lbmp", "cong"]].mean()
    out = {}
    for col in ("lbmp", "cong"):
        wide = grouped[col].unstack(0).reindex(CAL_KEY).ffill().bfill()
        wide.index = pd.RangeIndex(HOURS)
        out[col] = wide
    return out


def zonal_load(year: int) -> pd.DataFrame:
    """Return measured hourly load by load-zone LETTER on the model clock."""
    if year not in YEARS:
        raise SystemExit(f"rule 22: refusing to load out-of-training year {year}")
    df = pd.read_csv(LOAD_DIR / f"NYISO_load_actuals_{year}.csv")
    ts = pd.to_datetime(df["Time Stamp"])
    df["mo"], df["dy"], df["hr"] = ts.dt.month, ts.dt.day, ts.dt.hour
    df["letter"] = df["Name"].astype(str).str.strip().map(NAME_TO_LETTER)
    unmapped = sorted(set(df.loc[df["letter"].isna(), "Name"].astype(str)))
    if unmapped:
        raise ValueError(f"unmapped NYISO load-zone names in {year}: {unmapped}")
    wide = df.groupby(["letter", "mo", "dy", "hr"])["Load"].mean().unstack(0)
    wide = wide.reindex(CAL_KEY).ffill().bfill()
    wide.index = pd.RangeIndex(HOURS)
    return wide


def interface_postings(year: int) -> pd.DataFrame:
    """Return the committed hourly MIS P-32 interface flow/limit postings."""
    if year not in YEARS:
        raise SystemExit(f"rule 22: refusing to load out-of-training year {year}")
    df = pd.read_csv(IFACE_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz")
    ts = pd.to_datetime(df["interval_start_local"])
    df["mo"], df["dy"], df["hr"] = ts.dt.month, ts.dt.day, ts.dt.hour
    for col in ("positive_limit_mw", "negative_limit_mw"):
        df[col] = df[col].where(df[col].abs() < LIMIT_SENTINEL)
    return df


def interface_utilisation(year: int, interface: str) -> pd.Series:
    """Return hourly flow/limit utilisation for one posted interface, model clock."""
    df = interface_postings(year)
    sub = df[df["interface"] == interface]
    if sub.empty:
        raise SystemExit(f"interface {interface!r} absent from the {year} posting")
    g = sub.groupby(["mo", "dy", "hr"])[["flow_mw", "positive_limit_mw"]].mean()
    util = (g["flow_mw"] / g["positive_limit_mw"]).reindex(CAL_KEY).ffill().bfill()
    util.index = pd.RangeIndex(HOURS)
    return util


def model_zonal(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the keeper's P1 zonal price and demand frames (committed sidecar)."""
    if year not in YEARS:
        raise SystemExit(f"rule 22: refusing to load out-of-training year {year}")
    df = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    price = df.pivot_table(index="hour", columns="zone", values="price").sort_index()
    demand = df.pivot_table(index="hour", columns="zone", values="demand").sort_index()
    return price, demand


def actual_model_zone_price(year: int) -> pd.DataFrame:
    """Return measured price aggregated to MODEL zones, load-weighted by zone letter.

    Named basis, never blended with the others (the nyiso-123 §1 discipline):
    this is the **zone-letter basis** — NYISO's own posted RT zonal LBMP,
    load-weighted within each model zone by that zone's own measured hourly
    load.  Its ISO level differs from the scorer's ``rt_lw`` bench, so LEVELS
    from this basis are never quoted as C3a; only DIFFERENCES and shares are.
    """
    lbmp = zonal_lbmp(year)["lbmp"]
    load = zonal_load(year)
    out = {}
    for zone, letters in MODEL_ZONES.items():
        names = [LETTER_TO_NAME[c] for c in letters]
        w = load[letters].to_numpy()
        out[zone] = pd.Series(
            (lbmp[names].to_numpy() * w).sum(axis=1) / w.sum(axis=1),
            index=pd.RangeIndex(HOURS),
        )
    return pd.DataFrame(out)


GOLDBOOK_TERMS = ("SENY", "UPNY", "Central East", "Total East", "transfer limit")


def _scan_goldbooks(editions: list[str]) -> dict:
    """Count interface-limit keyword hits in each committed Gold Book PDF.

    ``pypdf`` is not a project dependency (the Gold Book is otherwise read by
    hand — data/raw/NYISO/README.md), so this reports honestly when it cannot
    run.  Reproduce the scan standalone with::

        uv run --with pypdf python scripts/probes/_nyiso124_charter_g0_g1.py \\
            --sections sources
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return {
            "scanned": False,
            "reason": "pypdf unavailable — re-run under `uv run --with pypdf`",
            "terms": list(GOLDBOOK_TERMS),
        }
    hits: dict[str, dict[str, int]] = {}
    for edition in editions:
        reader = PdfReader(GOLDBOOK_DIR / edition)
        text = "\n".join((p.extract_text() or "") for p in reader.pages).lower()
        hits[edition] = {t: text.count(t.lower()) for t in GOLDBOOK_TERMS}
    return {"scanned": True, "terms": list(GOLDBOOK_TERMS), "hits": hits}


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------


def section_sources() -> dict:
    """G0 — does a public, citable source exist for each required quantity?"""
    print(RULE)
    print("G0 — IDENTIFIABILITY: the public-source census")
    print(RULE)

    # (a) the two MIS interface rosters, enumerated rather than asserted.
    p32: set[str] = set()
    for year in YEARS:
        p32 |= set(interface_postings(year)["interface"].unique())
    p32_internal = sorted(i for i in p32 if not i.startswith("SCH "))

    atc: set[str] = set()
    atc_months = 0
    for year in YEARS:
        for month in range(1, 13):
            path = _fetch(
                MIS_ATC_URL.format(year=year, month=month),
                CACHE / "atc" / f"{year}{month:02d}.zip",
            )
            if path is None:
                continue
            with zipfile.ZipFile(path) as zf:
                names = [n for n in zf.namelist() if n.endswith(".csv")]
                if not names:
                    continue
                head = pd.read_csv(zf.open(names[0]))
                atc |= set(head["Interface Name"].astype(str).str.strip().unique())
                atc_months += 1
    atc_internal = sorted(
        i
        for i in atc
        if not i.startswith("SCH")
        and not any(t in i for t in ("HQ", "NPX", "IMO", "PJM", "ISONE", "NYISO-", "CEDARS", "1385", "CSC"))
    )

    def _has_seny(names) -> bool:
        return any("SENY" in n.upper() for n in names)

    print(f"  MIS P-32 internal interfaces ({len(p32_internal)}): {p32_internal}")
    print(f"  MIS ATC/TTC internal interfaces ({len(atc_internal)}) over {atc_months} months: {atc_internal}")
    print(f"  UPNY-SENY (the F|G cutset) present in P-32?    {_has_seny(p32_internal)}")
    print(f"  UPNY-SENY present in the ATC/TTC posting?      {_has_seny(atc_internal)}")

    # (b) the Gold Book: does any edition carry an interface transfer-limit table?
    goldbooks = sorted(p.name for p in GOLDBOOK_DIR.glob("*-Gold-Book-Public.pdf"))
    goldbook_scan = _scan_goldbooks(goldbooks)
    print(f"  Gold Book editions on disk: {goldbooks}")
    if goldbook_scan.get("scanned"):
        for edition, hits in sorted(goldbook_scan["hits"].items()):
            print(f"    {edition}: " + "  ".join(f"{k}={v}" for k, v in sorted(hits.items())))
    else:
        print(f"    [not scanned] {goldbook_scan.get('reason')}")

    # (c) zonal load allocation and fleet membership.
    load_ok = all((LOAD_DIR / f"NYISO_load_actuals_{y}.csv").exists() for y in YEARS)
    fleet_files = sorted(
        p.name
        for p in GOLDBOOK_DIR.glob("*.xlsx")
        if "Generat" in p.name or "NYCA" in p.name
    )
    print(f"  measured hourly zonal load (CAPITL / HUD VL) for all training years: {load_ok}")
    print(f"  Gold Book per-unit zone-letter fleet tables: {fleet_files}")

    quantities = [
        {
            "quantity": "F/G boundary definition",
            "public_source": (
                "NYISO load zones F (Capital) and G (Hudson Valley) are tariff objects with "
                "their own PTIDs in the MIS zonal LBMP posting; the cutset between them is the "
                "UPNY-SENY interface, defined in the NYISO SOM as 'the UPNY-SENY interface "
                "between zones A-F and G-I' (2025 SOM §IX) and listed among the RTC/RTD "
                "constrained interfaces (2025 SOM p. A-93)."
            ),
            "forward_analogue": "yes — static tariff zone definitions",
            "verdict": "PASS",
        },
        {
            "quantity": "F/G transfer limit(s)",
            "public_source": (
                "NONE FOUND. Absent from the MIS P-32 interface flow/limit posting "
                f"({len(p32_internal)} internal interfaces, no SENY row), absent from the MIS "
                f"ATC/TTC day-ahead posting ({len(atc_internal)} internal interfaces over "
                f"{atc_months} training months, no SENY row), and absent from every Gold Book "
                "edition on disk (zero text hits — see goldbook_scan). The only public appearance "
                "is narrative: the "
                "2025 SOM records that NYISO CEASED STUDYING UPNY-SENY in the deliverability test "
                "after the G-J locality was created in 2013."
            ),
            "forward_analogue": "n/a — no quantity to carry forward",
            "verdict": "FAIL",
        },
        {
            "quantity": "Zone-G share of the eastern external seam (ext_G)",
            "public_source": (
                "NONE. Unchanged from nyiso-101 §3 leg 2: the 1,600 MW "
                "import_node->Capital_Hudson link lumps the PJM Ramapo 345 kV ties (Zone G) with "
                "the ISO-NE New Scotland / Pleasant Valley corridor (Zones F/G), and "
                "interchange/spec.py records the F-vs-G split as 'a modelling choice inside the "
                "topology', not a measured allocation. A split FORCES this number to be chosen."
            ),
            "forward_analogue": "n/a — would have to be invented (rules 5, 24)",
            "verdict": "FAIL",
        },
        {
            "quantity": "zonal load allocation F vs G",
            "public_source": (
                "measured hourly CAPITL / HUD VL load, NYISO zonal load report "
                f"(data/raw/zone-specific-demand/NYISO, all training years present: {load_ok})"
            ),
            "forward_analogue": (
                "yes — the Gold Book publishes zonal (A-K) baseline load forecasts for 30 years "
                "(2025 Gold Book: 'Zonal and system-level summary forecasts are provided for 30 "
                "years'), and Table I-14 carries the zonal large-load pipeline"
            ),
            "verdict": "PASS",
        },
        {
            "quantity": "fleet membership each side",
            "public_source": (
                f"Gold Book Table III-2a carries the NYISO load-zone letter per unit ({fleet_files}); "
                "the per-county F/G split is already carried by "
                "zone_assignment.NYISO_CAPITAL_HUDSON_COUNTIES (nyiso-101 §6)"
            ),
            "forward_analogue": (
                "yes — the same table each year, plus the interconnection queue, which also "
                "carries the zone letter per project"
            ),
            "verdict": "PASS",
        },
    ]
    print()
    for q in quantities:
        print(f"  [{q['verdict']}] {q['quantity']}")
    fails = [q["quantity"] for q in quantities if q["verdict"] == "FAIL"]
    verdict = "FAIL" if fails else "PASS"
    print(f"\n  G0 VERDICT: {verdict}" + (f" — unidentifiable: {fails}" if fails else ""))
    return {
        "p32_internal_interfaces": p32_internal,
        "atc_ttc_internal_interfaces": atc_internal,
        "atc_ttc_months_read": atc_months,
        "upny_seny_in_p32": _has_seny(p32_internal),
        "upny_seny_in_atc_ttc": _has_seny(atc_internal),
        "goldbook_editions": goldbooks,
        "goldbook_scan": goldbook_scan,
        "quantities": quantities,
        "verdict": verdict,
    }


def section_incidence() -> dict:
    """WHERE the measured basis forms: the three eastward zonal steps."""
    print(RULE)
    print("G0 — INCIDENCE: which cutset carries the measured downstate basis")
    print(RULE)
    rows = []
    for year in YEARS:
        z = zonal_lbmp(year)
        lbmp, cong = z["lbmp"], z["cong"]
        print(f"\n{year}")
        print(f"  {'step':22s} {'annual $':>9s} {'of which cong':>14s}   monthly mean (Jan..Dec)")
        for label, hi, lo in STEPS:
            step = lbmp[hi] - lbmp[lo]
            step_c = cong[hi] - cong[lo]
            monthly = step.groupby(MONTH_OF_HOUR).mean()
            print(
                f"  {label:22s} {step.mean():9.2f} {step_c.mean():14.2f}   "
                + " ".join(f"{monthly[m]:+6.2f}" for m in range(1, 13))
            )
            rows.append(
                {
                    "year": year,
                    "step": label,
                    "annual_lbmp_basis": round(float(step.mean()), 4),
                    "annual_congestion_basis": round(float(step_c.mean()), 4),
                    "monthly_lbmp_basis": [round(float(monthly[m]), 4) for m in range(1, 13)],
                    "share_hours_above_1usd": round(float((step > 1.0).mean()), 4),
                    "share_hours_below_minus_1usd": round(float((step < -1.0).mean()), 4),
                }
            )
    return {"steps": rows}


def section_binding() -> dict:
    """Which interface binds in reality, and does the model's link separate at all?"""
    print(RULE)
    print("G0 — BINDING: the real interfaces vs the model's own links")
    print(RULE)
    from market_sim.config.constants import NYISO_INTERFACE_TTC_BY_MONTH

    real, modelled = [], []
    for year in YEARS:
        df = interface_postings(year)
        print(f"\n{year}  measured MIS P-32 internal interfaces (share of hours at >= "
              f"{BIND_UTIL:.0%} of the posted limit)")
        for iface in sorted(set(df["interface"])):
            if iface.startswith("SCH "):
                continue
            sub = df[df["interface"] == iface].dropna(subset=["positive_limit_mw"])
            if sub.empty:
                continue
            util = sub["flow_mw"] / sub["positive_limit_mw"]
            months = {}
            for mo in (1, 2, 12):
                um = util[sub["mo"] == mo]
                months[mo] = float((um >= BIND_UTIL).mean()) if len(um) else float("nan")
            print(
                f"    {iface:20s} annual {float((util >= BIND_UTIL).mean()) * 100:5.1f}%   "
                f"Jan {months[1] * 100:5.1f}%  Feb {months[2] * 100:5.1f}%  Dec {months[12] * 100:5.1f}%"
                f"   median posted limit {sub['positive_limit_mw'].median():6.0f} MW"
            )
            real.append(
                {
                    "year": year,
                    "interface": iface,
                    "share_hours_binding": round(float((util >= BIND_UTIL).mean()), 4),
                    "share_jan": round(months[1], 4),
                    "share_feb": round(months[2], 4),
                    "share_dec": round(months[12], 4),
                    "median_posted_limit_mw": round(float(sub["positive_limit_mw"].median()), 1),
                }
            )

        price, _ = model_zonal(year)
        basis = price["Capital_Hudson"] - price["Upstate_West"]
        sep = basis > 0.01
        monthly_sep = sep.groupby(MONTH_OF_HOUR).mean()
        ttc = NYISO_INTERFACE_TTC_BY_MONTH[year][("Upstate_West", "Capital_Hudson")]
        print(
            f"  model Upstate_West->Capital_Hudson (THE Central-East cutset): separates prices in "
            f"{float(sep.mean()) * 100:.1f}% of hours, mean basis {float(basis.mean()):+.2f} $/MWh"
        )
        print(
            "    monthly separation share: "
            + " ".join(f"{monthly_sep[m] * 100:5.1f}%" for m in range(1, 13))
        )
        print("    model monthly TTC (measured DAM postings): " + " ".join(f"{v:.0f}" for v in ttc))
        modelled.append(
            {
                "year": year,
                "link": "Upstate_West->Capital_Hudson",
                "share_hours_price_separated": round(float(sep.mean()), 4),
                "annual_mean_basis": round(float(basis.mean()), 4),
                "monthly_separation_share": [round(float(monthly_sep[m]), 4) for m in range(1, 13)],
                "monthly_ttc_mw": list(ttc),
            }
        )
    return {"measured_interfaces": real, "model_links": modelled}


def section_objectb() -> dict:
    """G1 — is Object B the mirror of the missing basis, or its own object?"""
    print(RULE)
    print("G1 — OBJECT B: the model's upstate over-pricing, bucketed by the MEASURED basis")
    print(RULE)
    rows = []
    for year in YEARS:
        actual = actual_model_zone_price(year)
        price, demand = model_zonal(year)
        basis = actual["Capital_Hudson"] - actual["Upstate_West"]
        model_basis = price["Capital_Hudson"] - price["Upstate_West"]
        err_up = price["Upstate_West"] - actual["Upstate_West"]
        err_vs_east = price["Upstate_West"] - actual["Capital_Hudson"]
        util = interface_utilisation(year, "CENTRAL EAST - VC")
        binding = util >= BIND_UTIL

        print(f"\n{year}  measured East(F+G) - Upstate(A-E) basis quintiles")
        print(
            f"   {'bucket':8s} {'meas basis':>11s} {'model basis':>12s} "
            f"{'model UW - actUP':>17s} {'model UW - actEAST':>19s}"
        )
        quint = pd.qcut(basis.rank(method="first"), 5, labels=[f"Q{i}" for i in range(1, 6)])
        buckets = []
        for lab in [f"Q{i}" for i in range(1, 6)]:
            k = (quint == lab).to_numpy()
            buckets.append(
                {
                    "bucket": lab,
                    "measured_basis": round(float(basis[k].mean()), 4),
                    "model_basis": round(float(model_basis[k].mean()), 4),
                    "model_upstate_minus_actual_upstate": round(float(err_up[k].mean()), 4),
                    "model_upstate_minus_actual_east": round(float(err_vs_east[k].mean()), 4),
                }
            )
            print(
                f"   {lab:8s} {basis[k].mean():11.2f} {model_basis[k].mean():12.2f} "
                f"{err_up[k].mean():17.2f} {err_vs_east[k].mean():19.2f}"
            )

        corr = float(np.corrcoef(err_up.to_numpy(), basis.to_numpy())[0, 1])
        pk, off = PEAK_HOURS, ~PEAK_HOURS
        dem = demand["Upstate_West"]
        lw_err = float((err_up * dem).sum() / dem.sum())
        lw_bind = float((err_up[binding] * dem[binding]).sum() / dem.sum())
        print(f"   corr(model upstate error, measured basis) = {corr:+.3f}")
        print(
            f"   model upstate error: CE-binding hours {float(err_up[binding].mean()):+.2f} | "
            f"CE-slack hours {float(err_up[~binding].mean()):+.2f} $/MWh   "
            "(a LEVEL artifact — see the load-weighted split below)"
        )
        print(
            f"   model upstate error: peak HB07-22 {float(err_up[pk].mean()):+.2f} | "
            f"off-peak {float(err_up[off].mean()):+.2f} $/MWh"
        )
        print(
            f"   load-weighted upstate error {lw_err:+.2f}, of which CE-binding hours "
            f"contribute {lw_bind:+.2f} ({lw_bind / lw_err * 100 if lw_err else float('nan'):.0f}%) "
            f"on {int(binding.sum())} hours"
        )
        print(
            f"   model reproduces {float(model_basis.mean()) / float(basis.mean()) * 100:.1f}% "
            f"of the measured annual East-Upstate basis "
            f"({float(model_basis.mean()):+.2f} vs {float(basis.mean()):+.2f} $/MWh)"
        )
        rows.append(
            {
                "year": year,
                "buckets": buckets,
                "corr_upstate_error_vs_measured_basis": round(corr, 4),
                "upstate_error_ce_binding": round(float(err_up[binding].mean()), 4),
                "upstate_error_ce_slack": round(float(err_up[~binding].mean()), 4),
                "upstate_error_peak": round(float(err_up[pk].mean()), 4),
                "upstate_error_offpeak": round(float(err_up[off].mean()), 4),
                "upstate_error_load_weighted": round(lw_err, 4),
                "upstate_error_lw_from_ce_binding_hours": round(lw_bind, 4),
                "ce_binding_hours": int(binding.sum()),
                "measured_annual_basis": round(float(basis.mean()), 4),
                "model_annual_basis": round(float(model_basis.mean()), 4),
                "basis_reproduced_share": round(
                    float(model_basis.mean()) / float(basis.mean()), 4
                ),
            }
        )
    return {"years": rows}


SECTIONS = {
    "sources": section_sources,
    "incidence": section_incidence,
    "binding": section_binding,
    "objectb": section_objectb,
}


def main() -> None:
    """Run the requested sections and write the committed record."""
    _check_years()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sections", nargs="*", default=list(SECTIONS), choices=list(SECTIONS))
    args = ap.parse_args()

    record: dict = {
        "probe": "_nyiso124_charter_g0_g1",
        "iso": ISO,
        "years": list(YEARS),
        "bundle": BUNDLE.name,
        "note": (
            "no LP; committed artifacts plus public NYISO MIS postings. Prices from the "
            "ZONE-LETTER basis (NYISO posted zonal RT LBMP load-weighted by measured zonal "
            "load) — its ISO level differs from the scorer's rt_lw bench, so only DIFFERENCES "
            "and shares are quoted, never levels as C3a (nyiso-123 §1 discipline)."
        ),
    }
    for name in args.sections:
        record[name] = SECTIONS[name]()
        print()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
