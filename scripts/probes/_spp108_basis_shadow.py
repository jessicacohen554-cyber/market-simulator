"""SPP-108 step 0a probe: shadow-score C1 on the EIA-930-aligned basis with the SPP-88 gas-coverage correction (zero LP).

Close-out plan §3.4 step 0a. Reads only the SPP-107 keeper's committed payload and on-disk inputs, never solves,
never changes the scorer. Reuses the SPP-87 gross-coal construction (``_spp87_benchmark_reconcile``) verbatim and
adds the SPP-88 gas-coverage term:

* ``committed`` — the scorer's bench as committed;
* ``gross_coal`` — SPP-87: coal classes at per-plant CEMS gross (net where CAMPD is null), reconcile scale undone;
* ``aligned_prorata`` — gross coal + the scorer's gas-family bench scaled to EIA-930 SWPP gas
  (the part of EIA-923 gas outside SPP metering, SPP-88), spread pro rata over the gas classes;
* ``aligned_cc_only`` / ``aligned_chp_first`` — the same coverage term put entirely on CC_REGULAR (the bound
  most favourable to CC) or first on the CHP classes (SPP-88's named candidates; least favourable to CC).

Every basis is scored with the scorer's own ``score_fuelmix`` / ``score_sysvol``. Writes
``results/phase0/spp/_spp108_basis_shadow.json`` (gitignored) and prints the C1 table.

Run: ``uv run python scripts/probes/_spp108_basis_shadow.py`` (~3 min, CEMS reads dominate).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts/probes"))
import _spp87_benchmark_reconcile as s87  # noqa: E402
import calibration_verdict as cv  # noqa: E402

RUN_ID = "2026-10-02-spp-107-mmu-repair"
BUNDLE = REPO / "results/calibration/spp107EXR_span"
OUT = REPO / "results/phase0/spp/_spp108_basis_shadow.json"
CHP = ("CC_CHP", "CT_CHP", "ST_CHP")
ROWS = ("COAL_PRB", "COAL_LIGNITE", "CC_REGULAR", "CT_PEAKER", "ST_GAS")


def frame_path() -> Path:
    """The keeper's EIA-923 benchmark frame, as named in its meta.json."""
    meta = json.loads((BUNDLE / "meta.json").read_text())
    return (BUNDLE / meta["shared_inputs"]["eia923"]).resolve()


def plant_gross(frame: pd.DataFrame) -> pd.DataFrame:
    """Per plant-year CEMS gross and EIA-923 net TWh for the scorer's coal plants (SPP-87 §1)."""
    e923 = pd.read_csv(REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv")
    coal923 = e923[e923.fuel_type.isin(s87.COAL_FUELS)]
    rows = []
    for y in s87.YEARS:
        ids = set(frame[(frame.year == y) & frame.klass.isin(s87.COAL)].plant_id.astype(int))
        g = s87.cems_coal(y, ids).groupby("facilityId").mwh.sum() / 1e6
        n = coal923[(coal923.year == y) & coal923.plant_id.isin(ids)].groupby("plant_id").net_generation_mwh.sum() / 1e6
        pp = pd.DataFrame({"gross": g, "net923": n}).fillna(0.0)
        pp.index.name = "plant_id"
        rows.append(pp.reset_index().assign(year=y))
    return pd.concat(rows)


def with_gas_coverage(b: dict, mode: str) -> tuple[dict, float]:
    """Return a copy of ``b`` whose gas family is moved onto EIA-930 SWPP gas, and the TWh removed."""
    b = copy.deepcopy(b)
    cf = b["classFull"]
    gas = [c for c in s87.GAS if c in cf]
    tot = sum(cf[c] for c in gas)
    delta = tot - float(b["e930"]["gas"])  # > 0: EIA-923 gas outside SPP metering (SPP-88)
    if mode == "prorata":
        for c in gas:
            cf[c] -= delta * cf[c] / tot
    elif mode == "cc_only":
        cf["CC_REGULAR"] -= delta
    elif mode == "chp_first":
        chp = sum(cf.get(c, 0.0) for c in CHP)
        take = min(delta, chp)
        for c in CHP:
            if c in cf and chp > 0:
                cf[c] -= take * cf[c] / chp
        rest = [c for c in gas if c not in CHP]
        rtot = sum(cf[c] for c in rest)
        for c in rest:
            cf[c] -= (delta - take) * cf[c] / rtot
    return b, delta


def main() -> None:
    """Build the shadow benches, score them and write the JSON record."""
    art = cv.load_artifacts(RUN_ID)
    pay, bench = art["payload"]["years"], art["bench"]
    frame = pd.read_parquet(frame_path())
    plant = plant_gross(frame)
    gross = {y: s87.shadow_bench(y, bench[y], frame, plant, True)[0] for y in bench}
    bases = {"committed": bench, "gross_coal": gross}
    cover = {}
    for mode in ("prorata", "cc_only", "chp_first"):
        bases[f"aligned_{mode}"] = {}
        for y in bench:
            bases[f"aligned_{mode}"][y], cover[y] = with_gas_coverage(gross[y], mode)

    scored = {}
    for name, ball in bases.items():
        for y in bench:
            out = cv.score_fuelmix(y, pay[str(y)], ball[y], iso="SPP") + cv.score_sysvol(
                y, pay[str(y)], ball[y], iso="SPP", bench_all=ball
            )
            for r in out:
                scored.setdefault((r["criterion"], r.get("key"), y), {})[name] = r
    rec = {"run_id": RUN_ID, "gas_coverage_twh": {y: round(v, 3) for y, v in cover.items()}, "rows": []}
    for (crit, key, y), d in sorted(scored.items(), key=lambda kv: (kv[0][2], str(kv[0][1]))):
        row = {"year": y, "criterion": crit, "key": key, "model": d["committed"].get("model")}
        for name, r in d.items():
            act = r.get("actual")
            row[name] = {
                "actual": act,
                "miss": round(r["model"] - act, 3) if isinstance(act, (int, float)) and r.get("model") is not None else None,
                "share_pp": r.get("share_pp"),
                "status": r["status"],
            }
        rec["rows"].append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1, default=str))

    print("gas coverage (bench gas − EIA-930 gas, TWh):", rec["gas_coverage_twh"])
    names = list(bases)
    print("year key        " + " | ".join(f"{n:>22}" for n in names))
    for r in rec["rows"]:
        if r["criterion"] == "fuelmix" and r["key"] in ROWS:
            cells = [f"{r[n]['miss']:+7.2f} {r[n]['share_pp'] or 0:+5.1f}pp {r[n]['status']:>5}" for n in names]
            print(f"{r['year']} {r['key']:<11} " + " | ".join(f"{c:>22}" for c in cells))
    moved = [
        (r["year"], r["criterion"], r["key"], {n: r[n]["status"] for n in names})
        for r in rec["rows"]
        if len({r[n]["status"] for n in names}) > 1
    ]
    print("status moves:", json.dumps(moved, indent=1))


if __name__ == "__main__":
    main()
