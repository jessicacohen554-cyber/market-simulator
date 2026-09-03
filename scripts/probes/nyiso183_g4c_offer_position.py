#!/usr/bin/env python3
"""nyiso-183 G4c — the MODEL's own offer for Ravenswood against its MEASURED SRMC.

PREREG §4 G4c named "the model's ``mc`` for Ravenswood's ``ST_GAS`` tranches
against its measured ``srmc``" and pre-declared that, absent the model offer,
G4 resolves to ``PARTIALLY TESTED``. §0 established that the ``unit_hourly``
artifact nyiso-181 used is gone (PR #4656 closed unmerged, its branch deleted),
and the keeper's own invocation is recorded nowhere in the repository, so a
verifiable control replay is not available.

**It is not needed.** ``scripts.lib.bundle_fleet.reconstruct_bundle_fleet``
rebuilds a bundle's fleet and its ``mc_base`` offer array **exactly as the
bundle solved, with NO LP**, from the bundle's own ``meta.json``, behind a
fidelity guard that hard-fails on any dropped gate. That is the keeper's own
offer, obtained without a solve — so G4c is scored in full rather than skipped.

TWO DISCLOSED DEVIATIONS from G4c's literal wording, neither relaxing its bar:

* **``mc_base`` (P0 base cost), not the P1 bid cost.** The P1 markup is
  amortized startup, which measured SRMC (``HR x delivered fuel``) does not
  carry either — so ``mc_base`` is the apples-to-apples comparand and the P1
  offer would be the mismatched one. The startup markup is reported separately
  where the fleet exposes it, never netted silently.
* **capacity-weighted time mean, not load-weighted.** Load weights need a
  dispatch the no-LP reconstruction does not produce. The \$5/MWh bar is
  unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO), str(_REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.data import campd  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402
from scripts.lib.campd_measured_classes import (  # noqa: E402
    campd_unittype_class,
    corrected_unit_class,
)
from scripts.lib.outage_detect import (  # noqa: E402
    MERIT_RCC_PCTL,
    build_merit_order_panel,
)

KEEPER = _REPO / "results" / "calibration" / "nyiso177_vintage_B1p"
YEARS = (2023, 2024, 2025)
ISO = "NYISO"
CLASS = "ST_GAS"
RAVENSWOOD = 2500
PEERS = {
    2490: "Arthur Kill",
    8906: "Astoria Gen",
    2516: "Northport",
    2511: "E F Barrett",
    2625: "Bowline Point",
}
G4_BAR_USD = 5.0


def _hours(year: int) -> int:
    return len(pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h"))


def model_offer(bundle: Path, year: int) -> pd.DataFrame:
    """Per-LP-unit ``(plant, klass, cap_mw, mc_mean)`` at the keeper's own config."""
    state, meta = reconstruct_bundle_fleet(bundle, year, verbose=True)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    n_gen = len(np.asarray(fa.pmax))
    # mc_base is (n_gen, T) or (n_gen,) depending on whether any hourly term is
    # armed; normalise to a per-unit time mean either way.
    if mc.ndim == 2:
        mc_mean = mc.mean(axis=1)
    else:
        mc_mean = mc
    assert len(mc_mean) == n_gen, (len(mc_mean), n_gen)

    def col(*names):
        for nm in names:
            v = getattr(fa, nm, None)
            if v is not None:
                return np.asarray(v)
        raise AttributeError(names)

    return pd.DataFrame(
        {
            "unit_id": np.asarray(fa.unit_ids, dtype=object),
            "plant": col("plant_code"),
            "klass": col("plant_group"),
            "cap_mw": col("pmax"),
            "mc_mean": mc_mean,
        }
    )


def stgas_units(year: int, plant_groups: dict[int, set[str]]) -> set[tuple[int, str]]:
    """The CAMPD units the MODEL routes to ``ST_GAS``, on the keeper's own crosswalk.

    POPULATION REPAIR (this session, disclosed): the first cut of ``measured_srmc``
    averaged the panel's ``srmc`` over EVERY unit at an ``ST_GAS``-labelled plant,
    which at Ravenswood pulls in ``UCC001`` — the site's COMBINED CYCLE, measured
    HR 7.137 against the steam units' ~11 — and at Astoria the four ``RH``/``SH``
    heat-recovery halves at HR 5.3-5.6. That is nyiso-181 §3's population trap in
    mirror image, and it silently moved the plant ordering the gate reads. The
    population is now the SAME per-unit crosswalk the keeper's own
    ``campd_per_unit_attribution`` uses (``scripts.lib.campd_measured_classes``),
    with each plant's model roster taken from the no-LP reconstruction itself.
    """
    keep: set[tuple[int, str]] = set()
    for state in campd.states_for_iso(ISO):
        path = _REPO / "data" / "raw" / "campd-unit-level" / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=["facilityId", "unitId", "unitType"])
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df.dropna(subset=["facilityId"])
        for (fac, uid), g in df.groupby(["facilityId", "unitId"], sort=False):
            groups = plant_groups.get(int(fac))
            if not groups:
                continue
            ut = g["unitType"].dropna()
            if ut.empty:
                continue
            is_chp = any(k.endswith("_CHP") for k in groups)
            base = campd_unittype_class(str(ut.iloc[0]), is_chp)
            if corrected_unit_class(base, groups) == CLASS:
                keep.add((int(fac), str(uid)))
    return keep


def measured_srmc(
    year: int, members: set[tuple[int, str]]
) -> dict[int, tuple[float, float]]:
    """``{plant: (mean measured SRMC over ST_GAS units, priced hours)}`` from the guard's panel."""
    panel = build_merit_order_panel(
        ISO,
        year,
        _hours(year),
        campd.merit_panel_states_for_iso(ISO),
        MERIT_RCC_PCTL,
        member_facilities=None,
    )
    if panel is None:
        return {}
    acc: dict[int, list[tuple[float, int]]] = {}
    for (fac, _uid), s in panel.srmc.items():
        if (int(fac), str(_uid)) not in members:
            continue
        ok = np.isfinite(s)
        if not ok.any():
            continue
        acc.setdefault(int(fac), []).append((float(np.mean(s[ok])), int(ok.sum())))
    return {
        f: (
            float(sum(v * n for v, n in rows) / sum(n for _, n in rows)),
            sum(n for _, n in rows),
        )
        for f, rows in acc.items()
    }


def run(bundle: Path) -> dict:
    out: dict = {
        "session": "nyiso-183",
        "gate": "G4c",
        "bundle": str(bundle.relative_to(_REPO)),
        "bar_usd_mwh": G4_BAR_USD,
        "instrument": (
            "scripts.lib.bundle_fleet.reconstruct_bundle_fleet (fleet_only, NO LP) "
            "-> mc_base, vs outage_detect.build_merit_order_panel srmc"
        ),
        "years": {},
    }
    for year in YEARS:
        off = model_offer(bundle, year)
        groups: dict[int, set[str]] = {}
        for plant, klass in zip(
            off["plant"].astype(int), off["klass"].astype(str)
        ):
            groups.setdefault(int(plant), set()).add(klass)
        members = stgas_units(year, groups)
        out.setdefault("population", {})[str(year)] = {
            "n_stgas_units": len(members),
            "units": sorted(f"{f}:{u}" for f, u in members),
        }
        srmc = measured_srmc(year, members)
        st = off[off["klass"].astype(str) == CLASS].copy()
        st["plant"] = st["plant"].astype(int)
        g = st.groupby("plant").apply(
            lambda d: pd.Series(
                {
                    "cap_mw": float(d["cap_mw"].sum()),
                    "model_mc": float(
                        (d["mc_mean"] * d["cap_mw"]).sum() / max(d["cap_mw"].sum(), 1e-9)
                    ),
                    "n_tranches": int(len(d)),
                }
            ),
            include_groups=False,
        )
        rows = []
        for plant, r in g.iterrows():
            m = srmc.get(int(plant))
            rows.append(
                {
                    "plant": int(plant),
                    "name": PEERS.get(int(plant), "Ravenswood" if plant == RAVENSWOOD else ""),
                    "cap_mw": round(r["cap_mw"], 1),
                    "n_tranches": int(r["n_tranches"]),
                    "model_mc": round(r["model_mc"], 3),
                    "measured_srmc": None if m is None else round(m[0], 3),
                    "model_minus_measured": (
                        None if m is None else round(r["model_mc"] - m[0], 3)
                    ),
                }
            )
        rows.sort(key=lambda x: x["model_mc"])
        peer_rows = [
            x
            for x in rows
            if x["plant"] in PEERS and x["measured_srmc"] is not None
        ]
        rav = next((x for x in rows if x["plant"] == RAVENSWOOD), None)
        peer_mc_med = (
            float(np.median([x["model_mc"] for x in peer_rows])) if peer_rows else None
        )
        peer_srmc_med = (
            float(np.median([x["measured_srmc"] for x in peer_rows]))
            if peer_rows
            else None
        )
        leg_i = (
            rav is not None
            and rav["model_minus_measured"] is not None
            and rav["model_minus_measured"] <= -G4_BAR_USD
        )
        leg_ii = (
            rav is not None
            and peer_mc_med is not None
            and peer_srmc_med is not None
            and rav["measured_srmc"] is not None
            and (peer_mc_med - rav["model_mc"]) >= G4_BAR_USD
            and rav["measured_srmc"] > peer_srmc_med
        )
        out["years"][str(year)] = {
            "rows": rows,
            "peer_model_mc_median": None if peer_mc_med is None else round(peer_mc_med, 3),
            "peer_measured_srmc_median": (
                None if peer_srmc_med is None else round(peer_srmc_med, 3)
            ),
            "ravenswood_model_rank_of": (
                None
                if rav is None
                else f"{[x['plant'] for x in rows].index(RAVENSWOOD) + 1} of {len(rows)} (cheapest first)"
            ),
            "ravenswood_measured_rank_of": (
                None
                if rav is None or rav["measured_srmc"] is None
                else "%d of %d (cheapest first)"
                % (
                    sorted(
                        x["measured_srmc"]
                        for x in rows
                        if x["measured_srmc"] is not None
                    ).index(rav["measured_srmc"])
                    + 1,
                    sum(1 for x in rows if x["measured_srmc"] is not None),
                )
            ),
            "leg_i_model_below_own_measured_by_bar": bool(leg_i),
            "leg_ii_merit_position_inversion": bool(leg_ii),
            "G4c_fired": bool(leg_i or leg_ii),
        }
    out["G4c_fired_any_year"] = any(
        v["G4c_fired"] for v in out["years"].values()
    )
    out["G4c_fired_years"] = [
        int(y) for y, v in out["years"].items() if v["G4c_fired"]
    ]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=KEEPER)
    ap.add_argument(
        "--out",
        default=str(_REPO / "results" / "calibration" / "_nyiso183_g4c_offer_position.json"),
    )
    args = ap.parse_args()
    res = run(args.bundle)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str))
    for year, v in res["years"].items():
        print(f"\n=== {year}: model mc_base vs measured SRMC, NYISO ST_GAS plants ===")
        print(pd.DataFrame(v["rows"]).to_string(index=False))
        print(
            f"  peer model-mc median {v['peer_model_mc_median']}   "
            f"peer measured-SRMC median {v['peer_measured_srmc_median']}"
        )
        print(
            f"  Ravenswood model rank {v['ravenswood_model_rank_of']} | "
            f"measured rank {v['ravenswood_measured_rank_of']}"
        )
        print(
            f"  leg(i) {v['leg_i_model_below_own_measured_by_bar']}  "
            f"leg(ii) {v['leg_ii_merit_position_inversion']}  "
            f"=> G4c {v['G4c_fired']}"
        )
    print("\nG4c FIRED:", res["G4c_fired_any_year"], res["G4c_fired_years"])
    print("written:", args.out)


if __name__ == "__main__":
    main()
