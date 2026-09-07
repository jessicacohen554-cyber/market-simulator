"""nyiso-211 POST-HOC phase 0 — size the ``unit_outage_per_unit_clip`` footprint
at NYISO's combined-cycle bins, on the keeper's own extract basis.

Zero-LP, and **arms nothing**. The over-derate test
(``scripts/probes/nyiso211_overderate_test.py``) found months in which the
meter recorded more CC energy than the LP was physically able to produce, on
the basis every keeper has carried since nyiso-196
(``unit_outage_extract_basis_share``). ``unit_outage_per_unit_clip``
(miso-202, GATED default-off, zero free parameters) enforces the invariant that
ONE UNIT CANNOT BE MORE THAN 100 % OUT OF SERVICE before units are summed into
a bin, and by construction can only ever remove LESS. Rule 28(d): the flag is
adjudicated in MISO and enters NYISO as an UNTESTED cell — this probe measures
its NYISO footprint and nothing more.

The three bases compared, all through the same loader call the keeper's LP makes
(``market_sim.data.outages.unit_outage_derate_factors``):

* ``pre196``  — the pre-nyiso-196 basis (extract_basis_share OFF).
* ``keeper``  — the current keeper basis (extract_basis_share ON).
* ``clipped`` — the keeper basis plus ``per_unit_clip``.

Availability is reconstructed as ``base x factor``, where ``base`` is recovered
from the committed rebuild cache (``avail_keeper_basis / factor_keeper_basis``),
so the comparison runs on the LP's own availability rather than on the factor
alone.

**POST-HOC.** Not among the predictions declared in
``results/calibration/PREREG-nyiso211-cricket-valley-lineage-attribution.md``;
decides no pre-registered verdict; proposes no arm and moves no default.

Run::

    uv run python scripts/probes/nyiso211_clip_phase0.py
"""

from __future__ import annotations

import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(p))

from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402

YEARS = (2023, 2024, 2025)
KLASS = "CC_REGULAR"
T = 8760
MONTH_STARTS = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
CACHE = ROOT / ".cache/nyiso196"
BENCH = ROOT / "frontend/data/backcast/bench/NYISO"
TARGET = 57185

BASES = {
    "pre196": dict(extract_basis_share=False, per_unit_clip=False),
    "keeper": dict(extract_basis_share=True, per_unit_clip=False),
    "clipped": dict(extract_basis_share=True, per_unit_clip=True),
}


def factors(year: int, **kw) -> dict[tuple[int, str], np.ndarray]:
    return unit_outage_derate_factors(
        year, iso="NYISO", per_unit_crosswalk=True, merit_order_guard=True, **kw
    )


def measured(year: int) -> dict[int, list[float]]:
    bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["plants"]
    return {
        int(str(code).split(":", 1)[0]): [
            float(v) for v in (bp.get("c_mon") or [0.0] * 12)
        ]
        for code, bp in bench.items()
        if bp.get("group") == KLASS
    }


def main() -> None:
    out: dict[str, dict] = {}
    for year in YEARS:
        st = pickle.load(open(CACHE / f"rebuild_{year}_arm.pkl", "rb"))
        units, avail = st["units"], st["avail"]
        fac = {name: factors(year, **kw) for name, kw in BASES.items()}
        meas = measured(year)

        rows = {}
        for plant, grp in units[units.group == KLASS].groupby("plant"):
            plant = int(plant)
            key = (plant, KLASS)
            f_keeper = fac["keeper"].get(key)
            if f_keeper is None:
                continue
            idx, pmax = grp.i.to_numpy(), grp.pmax.to_numpy()[:, None]
            # avail (LP) = base x factor(keeper basis); recover base where the
            # factor is non-zero, and hold it flat elsewhere (a zeroed factor
            # carries no information about the base it multiplied).
            f_k = np.asarray(f_keeper[:T], dtype=float)
            lp = np.asarray(avail[idx][:, :T], dtype=float)
            with np.errstate(divide="ignore", invalid="ignore"):
                base = np.where(f_k > 1e-9, lp / f_k, np.nan)
            filler = np.nanmedian(base) if np.isfinite(base).any() else 1.0
            base = np.where(np.isfinite(base), base, filler)

            entry = {"pmax_mw": round(float(grp.pmax.sum()), 1)}
            cm = meas.get(plant)
            for name in BASES:
                f = fac[name].get(key)
                if f is None:
                    entry[name] = None
                    continue
                a = np.clip(base * np.asarray(f[:T], dtype=float), 0.0, 1.0)
                energy_h = (a * pmax).sum(axis=0)
                months = [
                    float(energy_h[MONTH_STARTS[m] : MONTH_STARTS[m + 1]].sum()) / 1e3
                    for m in range(12)
                ]
                rec = {
                    "mean_avail": round(
                        float((a * pmax).sum() / (pmax.sum() * T)), 4
                    ),
                    "available_gwh": round(sum(months), 2),
                }
                if cm:
                    over = [
                        i + 1
                        for i in range(12)
                        if months[i] > 0 and cm[i] / months[i] > 1.0
                    ]
                    rec["months_meter_exceeds_ceiling"] = over
                    rec["measured_over_available"] = (
                        round(sum(cm) / sum(months), 4) if sum(months) > 0 else None
                    )
                entry[name] = rec
            rows[str(plant)] = entry
        out[str(year)] = rows

    summary = {
        str(y): {
            "target": out[str(y)].get(str(TARGET)),
            "class_months_over_ceiling": {
                b: sum(
                    len((r.get(b) or {}).get("months_meter_exceeds_ceiling") or [])
                    for r in out[str(y)].values()
                )
                for b in BASES
            },
            "class_plants_over_ceiling": {
                b: sum(
                    1
                    for r in out[str(y)].values()
                    if (r.get(b) or {}).get("months_meter_exceeds_ceiling")
                )
                for b in BASES
            },
            "plants_clip_moves": sorted(
                p
                for p, r in out[str(y)].items()
                if r.get("keeper")
                and r.get("clipped")
                and abs(r["keeper"]["mean_avail"] - r["clipped"]["mean_avail"]) > 1e-4
            ),
        }
        for y in YEARS
    }

    doc = {
        "session": "nyiso-211",
        "status": "POST-HOC phase 0 — arms nothing, moves no default, decides no declared verdict",
        "flag": "unit_outage_per_unit_clip (miso-202; NYISO cell UNTESTED, rule 28(d))",
        "bases": {k: str(v) for k, v in BASES.items()},
        "summary": summary,
        "plants": out,
    }
    dest = ROOT / "results/calibration/_nyiso211_clip_phase0.json"
    dest.write_text(json.dumps(doc, indent=1))
    print(json.dumps(summary, indent=1))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
