"""spp-52 phase 0 (ZERO LP): the footprint of the authorized fossil-band x0.93 cut.

Registered in ``results/calibration/PRECOMMIT-spp-52-fossil-offer-7pct-2026-09-09.md``
§E, which fixes the estimator and what it is used for BEFORE it runs: F(y)
NAMES the rule-29 [R-SCREEN] screen year, and it contains no price actual, no
residual and no criterion. The screen year is ``argmax_y F(y)`` and nothing
else — naming it on the biggest residual is the fitted-mechanism selection
rule 1 ``[R-STRUCT]`` exists to forbid.

Construction (the caiso-251/252/254 two-rebuild pattern, ~90 s per arm): two
on-recipe ``fleet_only`` rebuilds of the SPP keeper differing ONLY in
``offer_curve_overrides`` — absent (control) vs the x0.93 band file (arm) —
differenced on the model's own assembled offer array ``mc_base``. Nothing is
reimplemented: the pricing arithmetic is whatever ``bins_to_fleet`` does, so
the footprint is the model's, not this file's reading of it.

    F(y) = sum over FOSSIL tranches of  energy[u] * mean_t |dmc[u, t]|   ($)

where ``energy[u]`` is the tranche's OWN committed P1 energy, recovered from
``hourly/class_band_hourly_<y>.parquet`` by (class, band) and split within a
(class, band) cell by tranche capacity. The keeper's per-plant parquets were
pruned under rule 15 keeper-only retention, so the class-band sidecar is the
finest committed dispatch grain available; the capacity split inside a cell is
therefore an approximation and is declared as one.

Usage: python3 scripts/probes/spp52_fossil93_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLE = REPO / "results/calibration/spp51c_oversupply"
OVERRIDE = REPO / "results/calibration/_spp52_fossil93_offer_curve.json"
OUT = REPO / "results/calibration/_spp52_fossil93_phase0.json"
YEARS = (2023, 2024, 2025)
#: Fleet classes the offer-curve router reads AND the SPP keeper's resolved
#: curve carries an entry for. ST_CHP is router-readable but has NO keeper
#: entry, so it is not cut (adding one injects a band set the keeper never
#: had); it is reported as an untouched fossil class instead.
CUT_CLASSES = (
    "CC_CHP",
    "CC_REGULAR",
    "COAL",
    "COAL_BIT",
    "COAL_LIGNITE",
    "COAL_PRB",
    "COAL_WC",
    "CT_CHP",
    "CT_PEAKER",
    "ST_GAS",
)
FOSSIL_CLASSES = CUT_CLASSES + ("ST_CHP",)
#: Sidecar band labels, longest-first so ``econlo`` never matches ``econ``.
#: The fleet tranche SUFFIX is already spelled the sidecar's way
#: (``assembly.py`` builds ``unit_id = f"{bin_id}_{suffix}"``), so the map is a
#: longest-prefix normalisation of slice/ladder variants (``committed2``,
#: ``peak3``) onto their base band.
_BANDS = ("mustrun", "committed", "econlo", "econhi", "econ", "peak", "sync")


def _band_label(unit_id: str) -> str:
    """Map a tranche unit id onto its ``class_band_hourly`` band label."""
    tail = str(unit_id).rsplit("_", 1)[-1].lower()
    for label in sorted(_BANDS, key=len, reverse=True):
        if tail.startswith(label):
            return label
    return tail


def _sidecar_class(group: str, plant_code: int) -> str:
    """Resolve a fleet ``plant_group`` onto the sidecar's ``klass`` label.

    The fleet carries every coal plant under the generic ``COAL`` group while
    the committed sidecar splits coal by SUPPLY class (``COAL_PRB`` /
    ``COAL_LIGNITE`` / ...), exactly as ``_offer_curve_for_group`` routes it.
    Without this the whole coal fleet — the majority of SPP fossil energy —
    would be attributed zero energy and silently drop out of F(y).
    """
    if group != "COAL":
        return group
    from market_sim.data.coal import coal_supply_class
    from market_sim.data.fleet import _COAL_SUPPLY_TO_CURVE

    return _COAL_SUPPLY_TO_CURVE.get(coal_supply_class(int(plant_code)), "COAL")


def rebuild(year: int, arm: bool) -> dict:
    """One on-recipe ``fleet_only`` rebuild -> mc_base / pmax / ids / groups."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    kwargs.update(derived_run_year_inputs(BUNDLE, year))
    if arm:
        kwargs["offer_curve_overrides"] = json.loads(OVERRIDE.read_text())
    from scripts.lib.bundle_fleet import clear_fleet_caches

    clear_fleet_caches()
    st = run_year(
        year,
        meta["iso"],
        int(meta.get("hours", 8760)),
        float(meta["gas_prices"][str(year)]),
        {},
        fleet_only=True,
        **kwargs,
    )
    fa = st["fleet_arrays"]
    groups = fa.plant_group
    if groups is None:
        groups = np.array([""] * len(fa.unit_ids), dtype=object)
    return {
        "mc": np.asarray(st["mc_base"], dtype=float),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "ids": np.asarray(fa.unit_ids, dtype=object),
        "groups": np.asarray(groups, dtype=object),
        "codes": np.asarray(
            fa.plant_code
            if fa.plant_code is not None
            else np.zeros(len(fa.unit_ids), dtype=int)
        ),
    }


def main() -> int:
    """Compute F(y) for every scored year and write the JSON record."""
    rec: dict = {"factor": 0.93, "years": {}, "cut_classes": list(CUT_CLASSES)}
    for year in YEARS:
        ctl, arm = rebuild(year, arm=False), rebuild(year, arm=True)
        if not np.array_equal(ctl["ids"], arm["ids"]):
            raise SystemExit(f"{year}: unit alignment differs between arms")
        dmc = arm["mc"] - ctl["mc"]
        if dmc.ndim == 1:  # scalar-per-unit objective
            mean_abs = np.abs(dmc)
        else:
            mean_abs = np.abs(dmc).mean(axis=1)

        band = pd.read_parquet(BUNDLE / f"hourly/class_band_hourly_{year}.parquet")
        band = band[band["pass"] == "P1"]
        cell_mwh = band.groupby(["klass", "band"], observed=True)["mw"].sum()

        klasses = [
            _sidecar_class(str(g), int(c))
            for g, c in zip(ctl["groups"], ctl["codes"], strict=True)
        ]
        rows = pd.DataFrame(
            {
                "klass": klasses,
                "band": [_band_label(u) for u in ctl["ids"]],
                "pmax": ctl["pmax"],
                "dmc": mean_abs,
            }
        )
        rows = rows[rows["klass"].isin(FOSSIL_CLASSES)].copy()
        cap = rows.groupby(["klass", "band"], observed=True)["pmax"].transform("sum")
        key = list(zip(rows["klass"], rows["band"], strict=True))
        rows["cell_mwh"] = [float(cell_mwh.get(k, 0.0)) for k in key]
        rows["mwh"] = np.where(cap > 0, rows["cell_mwh"] * rows["pmax"] / cap, 0.0)
        rows["dollars"] = rows["mwh"] * rows["dmc"]

        moved = rows[rows["dmc"] > 1e-12]
        twh = float(rows["mwh"].sum() / 1e6)
        # COVERAGE GUARD. The reconstructed fossil energy must reconcile with
        # the sidecar's own fossil total; a (klass, band) key the fleet spells
        # differently from the sidecar would otherwise drop a whole class out
        # of F(y) silently (it dropped ALL of coal on the first cut).
        sidecar_twh = float(band[band["klass"].isin(FOSSIL_CLASSES)]["mw"].sum() / 1e6)
        coverage = twh / sidecar_twh if sidecar_twh else 0.0
        if not 0.999 <= coverage <= 1.001:
            raise SystemExit(
                f"{year}: fossil energy coverage {coverage:.4f} "
                f"({twh:.3f} of {sidecar_twh:.3f} TWh) — a (klass, band) cell "
                "is unmatched; fix the mapping rather than reporting F(y)."
            )
        dollars = float(rows["dollars"].sum())
        rec["years"][str(year)] = {
            "fossil_twh": round(twh, 4),
            "sidecar_fossil_twh": round(sidecar_twh, 4),
            "coverage": round(coverage, 6),
            "offer_repricing_dollars": round(dollars, 1),
            "offer_repricing_musd": round(dollars / 1e6, 2),
            "mean_dmc_on_fossil_mwh": round(dollars / (twh * 1e6), 4) if twh else 0.0,
            "tranches_moved": int(len(moved)),
            "tranches_fossil": int(len(rows)),
            "classes_moved": sorted(moved["klass"].unique().tolist()),
            "by_class_musd": {
                k: round(float(v) / 1e6, 3)
                for k, v in rows.groupby("klass", observed=True)["dollars"]
                .sum()
                .items()
            },
            "max_abs_dmc_nonfossil": round(
                float(
                    np.max(mean_abs[~np.isin(np.array(klasses), list(FOSSIL_CLASSES))])
                ),
                9,
            ),
        }
        print(f"{year}: {json.dumps(rec['years'][str(year)])}")

    best = max(rec["years"], key=lambda y: rec["years"][y]["offer_repricing_dollars"])
    rec["screen_year_argmax_F"] = int(best)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(f"\nscreen year (argmax F) = {best}\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
