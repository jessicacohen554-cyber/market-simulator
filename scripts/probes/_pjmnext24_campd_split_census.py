"""PJM-NEXT-24 card 3 (zero LP): CAMPD facility-ID vs EIA-923 plant-ID splits across PJM.

NEXT-23 found Tait split across CAMPD facilities 2847 (GT1-3) and 55248 (CT4-7) while
EIA-923 reports all seven GTs under 2847. ``CAMPD_UNIT_PLANT_REMAP`` (``data/campd.py``)
re-keys such units for CAISO/SPP but carries no PJM entry. This census, per year 2019-2025,
over CAMPD unit-level facilities in PJM's states (``campd.states_for_iso("PJM")``):

- ``orphans``: CAMPD facilities with fossil gross load >= 10 GWh that carry no EIA-923
  fossil net generation under their own ID, matched to the EIA-860 plant in the same state
  whose name shares the first name token (candidate host plant), with whether that host is
  in the C1 bench for the year;
- ``partial``: bench plants whose CAMPD gross under their own ID is < 0.70 x their EIA-923
  fossil net (the Tait signature: CEMS covers only some of the plant's units).

The C1 annual totals are EIA-923 and so are unaffected; what a split moves is the bench's
hourly CAMPD shape (only the units under the plant's own ID shape the whole plant) and the
units feeding measured heat rates. Sized as TWh of gross load sitting under orphan IDs.

Writes ``results/phase0/pjm/_pjmnext24_campd_split_census.json``.
Run: ``python3 scripts/probes/_pjmnext24_campd_split_census.py``
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.data import campd  # noqa: E402

CAMPD_DIR = REPO / "data/raw/campd-unit-level"
E923 = REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
E860 = REPO / "data/raw/eia-860/eia860_plant.parquet"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
OUT = REPO / "results/phase0/pjm/_pjmnext24_campd_split_census.json"
YEARS = range(2019, 2026)
FOSSIL = {
    "NG",
    "BIT",
    "SUB",
    "LIG",
    "RC",
    "WC",
    "DFO",
    "RFO",
    "KER",
    "JF",
    "PC",
    "OG",
    "BFG",
}
MIN_GWH = 10.0
PARTIAL = 0.70
STOP = {"the", "power", "plant", "station", "generating", "energy", "center", "llc"}


def token(name: str) -> str:
    """First significant lower-case name token."""
    for w in re.findall(r"[a-z0-9]+", str(name).lower()):
        if w not in STOP and len(w) > 2:
            return w
    return ""


def campd_year(y: int) -> pd.DataFrame:
    """Per CAMPD facility: state, name, units, fossil gross GWh."""
    frames = []
    for st in campd.states_for_iso("PJM"):
        f = CAMPD_DIR / f"{st}_{y}.parquet"
        if f.exists():
            d = pd.read_parquet(
                f,
                columns=[
                    "stateCode",
                    "facilityName",
                    "facilityId",
                    "unitId",
                    "grossLoad",
                ],
            )
            frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["facilityId"] = pd.to_numeric(d.facilityId, errors="coerce").astype("Int64")
    g = d.groupby("facilityId").agg(
        state=("stateCode", "first"),
        name=("facilityName", "first"),
        units=("unitId", lambda s: sorted(set(map(str, s)))),
        gwh=("grossLoad", lambda s: s.fillna(0).sum() / 1e3),
    )
    return g


def bench_codes(y: int) -> set[int]:
    """Plant codes carried by the C1 bench for year ``y``."""
    bp = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    out = set()
    for key, b in bp.items():
        raw = str(b.get("pcode") or key).split(":")[0]
        if raw.isdigit():
            out.add(int(raw))
    return out


def main() -> None:
    """Every year."""
    e923 = pd.read_csv(E923)
    e923 = e923[e923.fuel_type.isin(FOSSIL)]
    e860 = pd.read_parquet(E860, columns=["Plant Code", "Plant Name", "State"])
    e860["tok"] = e860["Plant Name"].map(token)
    out: dict = {
        "what": "PJM-NEXT-24 card 3: CAMPD vs EIA-923 plant-ID splits. ZERO LP."
    }
    for y in YEARS:
        c = campd_year(y)
        net = e923[e923.year == y].groupby("plant_id").net_generation_mwh.sum() / 1e3
        bench = bench_codes(y)
        orph = []
        for fid, r in c[c.gwh >= MIN_GWH].iterrows():
            if net.get(int(fid), 0.0) > 1.0:
                continue
            tok = token(r["name"])
            hosts = e860[
                (e860.State == r.state)
                & (e860.tok == tok)
                & (e860["Plant Code"] != fid)
            ]["Plant Code"].tolist()
            hosts = [int(h) for h in hosts if net.get(int(h), 0.0) > 1.0]
            orph.append(
                {
                    "facility": int(fid),
                    "name": r["name"],
                    "state": r.state,
                    "units": r.units,
                    "gross_gwh": round(float(r.gwh), 1),
                    "host_candidates": hosts,
                    "host_in_bench": [h for h in hosts if h in bench],
                }
            )
        part = []
        for code in sorted(bench):
            n = float(net.get(code, 0.0))
            g = float(c.gwh.get(code, 0.0)) if code in c.index else 0.0
            if n >= 50.0 and g < PARTIAL * n:
                part.append(
                    {
                        "plant": code,
                        "e923_net_gwh": round(n, 1),
                        "campd_gross_gwh": round(g, 1),
                        "ratio": round(g / n, 3),
                    }
                )
        hosted = [o for o in orph if o["host_in_bench"]]
        out[str(y)] = {
            "campd_facilities": int(len(c)),
            "orphans": orph,
            "orphans_n": len(orph),
            "orphans_gwh": round(sum(o["gross_gwh"] for o in orph), 1),
            "orphans_hosted_in_bench_n": len(hosted),
            "orphans_hosted_in_bench_gwh": round(
                sum(o["gross_gwh"] for o in hosted), 1
            ),
            "partial": part,
        }
        print(
            y,
            "orphans",
            len(orph),
            out[str(y)]["orphans_gwh"],
            "GWh | hosted in bench",
            len(hosted),
            out[str(y)]["orphans_hosted_in_bench_gwh"],
            "| partial",
            len(part),
            flush=True,
        )
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
