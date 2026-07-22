"""Build the ERCOT DAM-resource-site -> EIA-plant crosswalk (Lane A-1, ERCOT-97).

The 60-Day DAM disclosure identifies generators by ERCOT resource mnemonics
(``DDPEC_CC1``, ``CBECII_CC3``, ``WHCCS2_CC2`` ...); the model keys thermal
plants by EIA ``Plant_Code`` (``custom-bin-assignments.csv``). The measured
class-HOUR DAM availability grain (ERCOT-96 keeper) water-fills each covered
class to its measured per-hour fraction but cannot place WHICH plant is derated
inside the class. Plant×hour availability (Lane A-2,
``ercot_thermal_dam_availability_plant``) needs a DAM-site -> EIA-plant map;
this script proposes one, the CAISO way
(:mod:`build_caiso_resource_crosswalk`): a **reviewable** CSV with per-row
evidence and an ``accepted`` gate, and the availability loader consumes only
accepted rows, so an unreviewed guess never enters a solve (CLAUDE.md rules
1/11 — crosswalk rows are identification metadata, not a tuning channel).

Why this is harder than CAISO. ERCOT resource mnemonics are substation codes,
not plant names — ``DDPEC``/``CBECII``/``WHCCS2`` do NOT token-match the EIA
names (``Colorado Bend II``, ``Wolf Hollow II`` ...), and two-letter initialisms
collide (``WH`` = Wharton *and* Wolf Hollow). So a single name score cannot be
trusted; every proposed row carries the full evidence stack the charter names:

  * ``p98_rating_mw``      — the site's 98th-pct DAM HSL (its measured rating)
  * ``capacity_ratio``     — p98 rating / model plant nameplate
  * ``settlement_points``  — DAM Settlement Point Name(s) (the substation token)
  * ``qse``                — Qualified Scheduling Entity (operator signal)
  * ``match_score``        — blended capacity + distinctive-abbreviation score
  * ``match_method``       — how the top candidate was proposed

**Auto-accept is deliberately conservative** (charter: "AUTO-ACCEPT only
unambiguous rows — capacity within tolerance AND name/SP corroboration"). A row
flips to ``accepted=1`` only when the abbreviation corroboration is *strong and
distinctive* (an exact initialism or a >=4-char token/mnemonic prefix — never a
2-char initials-prefix), the capacity ratio sits in a full-plant band, AND no
other in-class plant also clears the strong-corroboration bar (uniqueness). A
config-collapsed single train whose capacity is ~half its EIA plant
(``KMCHI`` -> 1.37 GW Kiamichi) will NOT auto-accept on capacity — those, and
every other ambiguous site, stay ``accepted=0`` and fall back to the class-hour
envelope. Known hand-forensic mappings from
``ercot_noncampd_dam_crosswalk.csv`` are seeded as accepted where in scope.

The 58 CC sites (30.8 GW) are the coverage priority; CT's ~166 small sites can
stay largely unaccepted without hurting the class-hour fallback (ERCOT-97
charter, Lane A step 1).

Output: ``data/raw/reference/ercot-dam-plant-crosswalk.csv``

Usage::

    python scripts/data/build_ercot_dam_resource_crosswalk.py \
        [--years 2023] [--out data/raw/reference/ercot-dam-plant-crosswalk.csv]

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the DAM disclosure or
the model plant registry updates — never because a price residual moved.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_thermal_dam_availability import (  # noqa: E402
    RESTYPE_TO_CLASS,
    _RATING_QUANTILE,
    _site,
)

DAM_DIR = REPO / "data" / "raw" / "ercot"
REFERENCE_DIR = REPO / "data" / "raw" / "reference"
BIN_ASSIGN = REFERENCE_DIR / "custom-bin-assignments.csv"
FORENSIC = REFERENCE_DIR / "ercot_noncampd_dam_crosswalk.csv"
DEFAULT_OUT = REFERENCE_DIR / "ercot-dam-plant-crosswalk.csv"

# Covered classes (the DAM-availability scope; CHP/coal/nuclear excluded — see
# derive_ercot_thermal_dam_availability). CC first: the coverage priority.
COVERED_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")

# Capacity plausibility band for auto-accept. Auto-accept is gated primarily on
# a *unique, distinctive* abbreviation corroboration (n_strong == 1); capacity is
# the secondary sanity check. A config-collapsed DAM site is one physical train,
# so a correct match to a 2-/3-train EIA plant lands at ~0.5 / ~0.33 of the plant
# nameplate — a train fraction is EXPECTED, not disqualifying. The band only
# rejects gross size mismatches (a stem coincidentally prefix-matching a plant
# several times its size, or an over-rating read). Full-plant matches sit near
# 1.0; the lower bound admits clean single trains of multi-train sites.
_CAP_LO, _CAP_HI = 0.30, 1.30

# Corroboration score at/above which a match is "strong" (distinctive
# abbreviation) and thus eligible for auto-accept.
_STRONG = 0.85

# Corporate suffixes + generic plant nouns dropped before name tokenizing.
_STOP = {
    "energy", "center", "centre", "power", "station", "facility", "facilities",
    "plant", "project", "generating", "generation", "the", "of", "and", "co",
    "corp", "company", "llc", "lp", "llp", "inc", "unit", "units", "site",
    "ii", "iii", "iv", "i", "1", "2", "3", "4", "st", "county",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Config / turbine suffixes stripped from a mnemonic to expose the substation
# stem (order matters: longest first).
_MNEM_SUFFIXES = ("CCS", "CCU", "CCGT", "CC", "GT", "ST", "CT", "SW", "SYD")


def _plant_tokens(name: object) -> list[str]:
    if not isinstance(name, str):
        return []
    return [t for t in _TOKEN_RE.findall(name.lower()) if t not in _STOP and len(t) > 1]


def _mnem_stem(site: str) -> str:
    """Letters-only substation stem of a DAM site key (strip config/turbine tags)."""
    s = re.sub(r"[^A-Za-z]", "", str(site)).upper()
    changed = True
    while changed and len(s) > 3:
        changed = False
        for suf in _MNEM_SUFFIXES:
            if s.endswith(suf) and len(s) - len(suf) >= 2:
                s = s[: -len(suf)]
                changed = True
                break
    return s


def _consonants(tok: str) -> str:
    return "".join(c for c in tok.upper() if c not in "AEIOU")


def corroboration(site: str, plant_name: str) -> tuple[float, str]:
    """Distinctive-abbreviation corroboration in [0, 1] + the method label.

    Only distinctive signals score "strong" (>= _STRONG): an exact initialism,
    a >=4-char token prefix either way, or a full consonant-skeleton match. A
    bare 2-char initials-prefix is explicitly capped low (it collides across
    plants — "WH" is both Wharton and Wolf Hollow), so it can propose a
    candidate but never auto-accept it.
    """
    stem = _mnem_stem(site)
    toks = _plant_tokens(plant_name)
    if not stem or not toks:
        return 0.0, "none"
    initials = "".join(t[0] for t in toks).upper()
    joined = "".join(toks).upper()

    # Exact initialism (distinctive when >= 3 letters): CBEC == Colorado Bend...
    if len(initials) >= 3 and stem == initials:
        return 0.95, "initialism_exact"
    # >=4-char token prefix either direction: FRNY <-> FREESTONE / FORNEY
    for t in toks:
        tu = t.upper()
        if len(stem) >= 4 and len(tu) >= 4 and (tu.startswith(stem) or stem.startswith(tu[:4])):
            return 0.90, "token_prefix"
    # Consonant skeleton of any token equals the stem (distinctive, >= 3):
    for t in toks:
        cons = _consonants(t)
        if len(cons) >= 3 and (stem == cons or stem == cons[: len(stem)] and len(stem) >= 4):
            return 0.88, "consonant_skeleton"
    # Whole-name letter prefix (joined tokens): distinctive when >= 4.
    if len(stem) >= 4 and joined.startswith(stem):
        return 0.86, "name_prefix"
    # --- below here: proposal-only signals, never strong enough to auto-accept
    if len(initials) >= 3 and (stem.startswith(initials) or initials.startswith(stem)):
        return 0.55, "initials_prefix"

    def _subseq(a: str, b: str) -> bool:
        it = iter(b)
        return all(c in it for c in a)

    if _subseq(stem, joined):
        return 0.45, "letter_subsequence"
    return 0.0, "none"


def load_dam_sites(years: list[int]) -> pd.DataFrame:
    """Per (class, site): p98 rating, settlement points, QSE from the DAM disclosure."""
    cols = [
        "Delivery Date", "Hour Ending", "QSE", "Resource Name", "Resource Type",
        "HSL", "Resource Status", "Settlement Point Name",
    ]
    frames: list[pd.DataFrame] = []
    for y in years:
        for path in sorted(DAM_DIR.glob(f"*60d_DAM_Gen_Resource_Data_{y}_*.parquet")):
            df = pd.read_parquet(path, columns=cols)
            df = df[df["Resource Type"].isin(RESTYPE_TO_CLASS)]
            dt = pd.to_datetime(df["Delivery Date"])
            df = df[dt.dt.year == y]
            if not df.empty:
                frames.append(df)
    if not frames:
        raise SystemExit("no DAM Gen Resource files found for years " + repr(years))
    df = pd.concat(frames, ignore_index=True)
    df["cls"] = df["Resource Type"].map(RESTYPE_TO_CLASS)
    df["site"] = [_site(n, t) for n, t in zip(df["Resource Name"], df["Resource Type"])]
    df["out"] = df["Resource Status"].eq("OUT")

    ok = df[~df["out"] & (df["HSL"] > 0.0)]
    site_hour = ok.groupby(["cls", "site", "Delivery Date", "Hour Ending"])["HSL"].max()
    rating = site_hour.groupby(["cls", "site"]).quantile(_RATING_QUANTILE)
    rating = rating.rename("p98_rating_mw")

    def _join(s: pd.Series) -> str:
        return ";".join(sorted({str(x) for x in s if pd.notna(x)}))

    sp = ok.groupby(["cls", "site"])["Settlement Point Name"].agg(_join).rename("settlement_points")
    qse = ok.groupby(["cls", "site"])["QSE"].agg(_join).rename("qse")
    meta = pd.concat([rating, sp, qse], axis=1).reset_index()
    meta = meta[meta["p98_rating_mw"] > 0.0].copy()
    meta["p98_rating_mw"] = meta["p98_rating_mw"].round(1)
    return meta


def load_model_plants() -> pd.DataFrame:
    """Per (class, plant_code): plant name, summed nameplate MW, ERCOT zone."""
    d = pd.read_csv(BIN_ASSIGN)
    d = d[d["Plant_Group"].isin(COVERED_CLASSES)]
    pl = d.groupby(
        ["Plant_Group", "Plant_Code", "Plant_Name", "ERCOT_Zone"], as_index=False
    )["Nameplate_MW"].sum()
    return pl.rename(
        columns={
            "Plant_Group": "cls",
            "Plant_Code": "plant_code",
            "Plant_Name": "plant_name",
            "ERCOT_Zone": "zone",
            "Nameplate_MW": "plant_nameplate_mw",
        }
    )


def _forensic_seeds() -> dict[str, int]:
    """Substation-token -> plant_code from the hand-forensic non-CAMPD crosswalk.

    Those rows were adjudicated unambiguous by hand (switchable / behind-fence
    units the automated capacity+abbrev path cannot see); seed them accepted.
    Keyed by the DAM settlement-point substation token.
    """
    seeds: dict[str, int] = {}
    if not FORENSIC.exists():
        return seeds
    fdf = pd.read_csv(FORENSIC)
    for _, r in fdf.iterrows():
        code = int(r["plant_code"])
        for sp in str(r["dam_settlement_points"]).split(";"):
            stem = _mnem_stem(_site(sp.strip(), "CCGT90"))
            if stem:
                seeds[stem] = code
    return seeds


def build(years: list[int]) -> pd.DataFrame:
    """Propose the DAM-site -> EIA-plant crosswalk with evidence + accept gate."""
    sites = load_dam_sites(years)
    plants = load_model_plants()
    seeds = _forensic_seeds()

    rows: list[dict] = []
    for _, s in sites.iterrows():
        cand = plants[plants["cls"] == s["cls"]].copy()
        if cand.empty:
            continue
        cand["capacity_ratio"] = s["p98_rating_mw"] / cand["plant_nameplate_mw"]
        scores = [corroboration(s["site"], n) for n in cand["plant_name"]]
        cand["corr"] = [sc for sc, _ in scores]
        cand["method"] = [m for _, m in scores]
        # Capacity fit peaks at ratio 1.0, decays either side (train fractions
        # are penalized, so a config-collapsed half-plant does not out-rank a
        # true full-plant match).
        cand["capfit"] = (1.0 - (cand["capacity_ratio"] - 1.0).abs()).clip(0.0, 1.0)
        cand["blend"] = (0.65 * cand["corr"] + 0.35 * cand["capfit"]).round(3)
        cand = cand.sort_values("blend", ascending=False)
        top = cand.iloc[0]

        n_strong = int((cand["corr"] >= _STRONG).sum())
        cap_ok = _CAP_LO <= top["capacity_ratio"] <= _CAP_HI
        strong = top["corr"] >= _STRONG
        accepted = int(strong and cap_ok and n_strong == 1)
        method = top["method"]

        # Forensic seed override (hand-adjudicated): accept onto the seeded plant.
        stem = _mnem_stem(s["site"])
        if stem in seeds:
            seed_code = seeds[stem]
            srow = plants[(plants["cls"] == s["cls"]) & (plants["plant_code"] == seed_code)]
            if not srow.empty:
                top = srow.iloc[0]
                top = top.copy()
                top["capacity_ratio"] = s["p98_rating_mw"] / top["plant_nameplate_mw"]
                accepted = 1
                method = "forensic_seed"

        rows.append(
            {
                "site": s["site"],
                "class": s["cls"],
                "p98_rating_mw": s["p98_rating_mw"],
                "settlement_points": s["settlement_points"],
                "qse": s["qse"],
                "plant_code": int(top["plant_code"]),
                "plant_name": top["plant_name"],
                "zone": top["zone"],
                "plant_nameplate_mw": round(float(top["plant_nameplate_mw"]), 1),
                "capacity_ratio": round(float(top["capacity_ratio"]), 3),
                "match_method": method,
                "match_score": round(float(top.get("blend", np.nan)), 3)
                if "blend" in top
                else np.nan,
                "n_strong_candidates": n_strong,
                "accepted": accepted,
            }
        )

    out = pd.DataFrame(rows)
    out = out.sort_values(
        ["accepted", "class", "p98_rating_mw"], ascending=[False, True, False]
    ).reset_index(drop=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    out = build(args.years)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out.to_csv(index=False))

    n_acc = int(out["accepted"].sum())
    print(f"wrote {len(out)} site rows ({n_acc} accepted) -> {args.out}")
    for cls in COVERED_CLASSES:
        sub = out[out["class"] == cls]
        acc = sub[sub["accepted"] == 1]
        acc_gw = (acc["p98_rating_mw"].sum() / 1000.0) if not acc.empty else 0.0
        tot_gw = sub["p98_rating_mw"].sum() / 1000.0
        print(
            f"  {cls}: {len(sub)} sites ({tot_gw:.1f} GW), "
            f"{len(acc)} accepted ({acc_gw:.1f} GW, "
            f"{100.0 * acc_gw / tot_gw if tot_gw else 0:.0f}% of class rating)"
        )


if __name__ == "__main__":
    main()
