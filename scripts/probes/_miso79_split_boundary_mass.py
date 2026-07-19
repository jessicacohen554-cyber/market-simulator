"""miso-79 probe — could ANY finer zone split capture MISO's internal congestion mass?

Derive-only (NO LP). Tests reopening condition RO-3 of the frozen miso-78 M4
congestion charter (``docs/handoffs/miso-78-m4-congestion-charter-2026-07.md``
§6): a zone refinement reopens the congestion component only with "probe
evidence that the refined boundary actually carries the congestion mass".
This is that probe, run BEFORE any zonal-refinement charter is drafted.

Method, per DA train year (2023-2025, rule 22; mirrors via the sanctioned
``scripts/data/fetch_miso_bc_hist.py``): parse each binding constraint's
``(type/FromCA/ToCA)`` branch suffix at LOCAL BALANCING AUTHORITY granularity
(one level below the miso-76 zone-boundary probe ``_miso76_bc_boundary_rank``,
whose CA→zone crosswalk is reused verbatim), then decompose every model-zone
internal class's Σ|shadow price| mass into:

- **intra-LBA** — FromCA == ToCA (or ToCA ``*``, same convention as the
  miso-76 probe): mass NO LBA-granularity split can ever convert into a
  between-zone boundary, whatever the partition;
- **cross-LBA** — FromCA != ToCA within the zone: the CEILING any split of
  that zone along LBA lines could capture;

and, per zone, enumerate ALL LBA bipartitions to find the one maximizing
captured cross-partition mass (upper bound over implementable splits — real
splits face the D1/D2 load-disaggregation blockers on top).

Shadow prices are the ANSWER class (rule 13) — used here only to LOCATE and
RANK measured congestion for a scope decision, never as a model input.

Finding (2026-07-19 run): RO-3 is EMPIRICALLY DEAD at any zonal granularity.
Intra-LBA mass is 88-99.7% of every internal class every year; the best
possible single-zone LBA bipartition captures at most 1.87% of total DA
congestion mass (Plains 2023, non-persistent — 0.14% by 2025; best
persistent candidate West {NSP,OTP} peaks at 1.35%), and splitting ALL six
zones at their optimal boundaries simultaneously converts only ~1.9-3.8% of
total mass into between-zone boundaries. The ToCA ``*`` convention is not a
caveat: 19,319 of 19,429 starred rows in 2024 are XF (transformers —
single-substation equipment that physically cannot straddle an LBA
boundary; remainder: 97 ZBR + 13 PS). Recorded in the miso-78 charter §6
RO-3 addendum and the calibration-log miso-79 entry.

Run: ``.venv/bin/python scripts/probes/_miso79_split_boundary_mass.py``
"""

from __future__ import annotations

import gzip
import io
import re
from itertools import combinations

import pandas as pd

from market_sim.config.paths import RAW_DIR

MIRROR_DIR = RAW_DIR / "transfer-constraint-binding" / "MISO"
YEARS = (2023, 2024, 2025)  # train window ONLY (rule 22)

# CA -> model zone crosswalk, reused verbatim from the miso-76 probe
# (scripts/probes/_miso76_bc_boundary_rank.py; source: docs/multi-iso/
# miso-zonal-refinement-scope.md sub-BA groups). Unlisted CAs (SPP/PJM/TVA/
# MHEB sides of seam constraints) classify EXT.
CA2Z = {
    "NSP": "West",
    "OTP": "West",
    "MDU": "West",
    "GRE": "West",
    "MP": "West",
    "SMP": "West",
    "DPC": "West",
    "ALTW": "Plains",
    "MEC": "Plains",
    "MPW": "Plains",
    "AMMO": "Plains",
    "AMIL": "Illinois",
    "CWLP": "Illinois",
    "SIPC": "Illinois",
    "IPL": "Indiana",
    "NIPS": "Indiana",
    "CIN": "Indiana",
    "SIGE": "Indiana",
    "HE": "Indiana",
    "DEI": "Indiana",
    "BREC": "Indiana",
    "OVEC": "Indiana",
    "CONS": "East",
    "METC": "East",
    "DECO": "East",
    "ITCT": "East",
    "WEC": "East",
    "ALTE": "East",
    "WPS": "East",
    "MGE": "East",
    "UPPC": "East",
    "MIUP": "East",
    "EES": "South",
    "EAI": "South",
    "CLEC": "South",
    "LAFA": "South",
    "LEPA": "South",
    "SME": "South",
    "LAGN": "South",
}
_CA_PAT = re.compile(r"\(\w+/([^/]+)/([^)]+)\)")


def _load_year(year: int) -> pd.DataFrame:
    """Return (from_ca, to_ca, |SP|) rows for one DA bc_HIST mirror."""
    path = MIRROR_DIR / f"{year}_da_bc_HIST.csv.gz"
    if not path.is_file():
        raise SystemExit(
            f"{path} missing — run scripts/data/fetch_miso_bc_hist.py --markets da"
        )
    with gzip.open(path, "rb") as fh:
        df = pd.read_csv(io.BytesIO(fh.read()), skiprows=2, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    bcol = next(c for c in df.columns if c.startswith("Branch"))
    spcol = next(c for c in df.columns if "Shadow" in c)
    sp = pd.to_numeric(
        df[spcol].astype(str).str.replace(r"[\$\(\),]", "", regex=True),
        errors="coerce",
    ).abs()
    pairs = df[bcol].astype(str).str.extract(_CA_PAT)
    out = pd.DataFrame(
        {"a": pairs[0].str.strip(), "b": pairs[1].str.strip(), "sp": sp}
    ).dropna()
    # ToCA "*" / blank -> same-CA convention (matches the miso-76 probe).
    out.loc[out.b.isin(("*", "")), "b"] = out.a
    return out


def _best_bipartitions(cross: pd.DataFrame, members: list[str], top: int = 3):
    """Enumerate LBA bipartitions; return the ``top`` by captured cross mass."""
    mass = cross.groupby(["a", "b"]).sp.sum()
    results = []
    for k in range(1, len(members) // 2 + 1):
        for side in combinations(members, k):
            s = frozenset(side)
            captured = sum(m for (a, b), m in mass.items() if (a in s) != (b in s))
            results.append((captured, sorted(s)))
    results.sort(key=lambda r: -r[0])
    return results[:top]


def main() -> None:
    for year in YEARS:
        rows = _load_year(year)
        rows["za"] = rows.a.map(CA2Z).fillna("EXT")
        rows["zb"] = rows.b.map(CA2Z).fillna("EXT")
        total = rows.sp.sum()
        print(f"===== DA {year} — total Σ|SP| {total / 1e3:,.0f} k$-h =====")
        for zone in ("West", "Plains", "Indiana", "East", "Illinois", "South"):
            zc = rows[(rows.za == zone) & (rows.zb == zone)]
            if zc.empty:
                continue
            zmass = zc.sp.sum()
            cross = zc[zc.a != zc.b]
            xmass = cross.sp.sum()
            print(
                f"\n{zone}-internal: {zmass / 1e3:,.0f} k$-h "
                f"({100 * zmass / total:.1f}% of total) | "
                f"intra-LBA {100 * (zmass - xmass) / zmass:.1f}% | "
                f"cross-LBA CEILING {100 * xmass / zmass:.1f}% "
                f"(= {100 * xmass / total:.2f}% of total)"
            )
            if xmass == 0:
                continue
            top_pairs = (
                cross.assign(pair=cross.a + "-" + cross.b)
                .groupby("pair")
                .sp.sum()
                .sort_values(ascending=False)
                .head(4)
            )
            print(
                "  top cross-LBA pairs: "
                + ", ".join(
                    f"{p} {m / 1e3:,.0f}k ({100 * m / zmass:.1f}%)"
                    for p, m in top_pairs.items()
                )
            )
            members = sorted(set(zc.a) | set(zc.b))
            for captured, side in _best_bipartitions(cross, members):
                print(
                    f"  bipartition {{{','.join(side)}}} vs rest: captures "
                    f"{100 * captured / zmass:.1f}% of class, "
                    f"{100 * captured / total:.2f}% of total"
                )
        print()


if __name__ == "__main__":
    main()
