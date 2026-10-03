"""closeout-PJM-cc22 phase 0 (zero LP): per-plant decomposition of C1 CC_REGULAR, all years.

Keeper ``2026-10-03-closeout-pjm-nuc-keeper``: payload ``plants[pid].m_ann`` / ``m_mon`` vs the
bench ``plants[pid].e_ann`` / ``e_mon`` (CAMPD shape, EIA-923 net level). Reports, per CC_REGULAR
plant, model − actual by year, and the 2022 anomaly = Δ2022 − mean Δ(other years).
Writes ``results/phase0/pjm/_closeoutpjm_cc22_plants.json``.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUN = REPO / "frontend/data/backcast/runs/2026-10-03-closeout-pjm-nuc-keeper.js"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
OUT = REPO / "results/phase0/pjm/_closeoutpjm_cc22_plants.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
KLASS = "CC_REGULAR"


def _payload() -> dict:
    """Decode the keeper's registered run payload."""
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', RUN.read_text())
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def main() -> None:
    """Build the per-plant table and write it."""
    pay = _payload()["years"]
    rows: dict[str, dict] = {}
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
        mod = pay[str(y)]["plants"]
        for pid, b in bench.items():
            if b.get("group") != KLASS:
                continue
            m = mod.get(pid, {})
            r = rows.setdefault(pid, {"name": b["name"], "zone": b["zone"], "npl": b.get("npl"), "y": {}})
            r["y"][y] = {
                "m": float(m.get("m_ann") or 0.0),
                "a": float(b.get("e_ann") or 0.0),
                "m_mon": m.get("m_mon"),
                "a_mon": b.get("e_mon"),
                "cap": m.get("cap"),
            }
    for r in rows.values():
        d = {y: v["m"] - v["a"] for y, v in r["y"].items()}
        r["d"] = d
        oth = [d[y] for y in d if y != 2022]
        r["anom22"] = d.get(2022, 0.0) - (sum(oth) / len(oth) if oth else 0.0)
    OUT.write_text(json.dumps(rows, indent=1, default=str))
    ranked = sorted(rows.items(), key=lambda kv: -abs(kv[1]["d"].get(2022, 0.0)))
    print("pid name zone npl | d2019..d2025 | anom22 | a2022 m2022")
    for pid, r in ranked[:30]:
        ds = " ".join(f"{r['d'].get(y, float('nan')):+5.2f}" for y in YEARS)
        y22 = r["y"].get(2022, {})
        print(f"{pid:>6} {r['name'][:22]:22} {r['zone'][4:]:11} {r['npl']} | {ds} | {r['anom22']:+5.2f} | "
              f"{y22.get('a', 0):5.2f} {y22.get('m', 0):5.2f}")
    for y in YEARS:
        print(y, "sum d", round(sum(r["d"].get(y, 0) for r in rows.values()), 2))


if __name__ == "__main__":
    main()
