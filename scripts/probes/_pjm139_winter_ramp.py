"""pjm-139 (no LP): the WINTER MORNING RAMP — and why ``gas_daily_shape`` cannot
reach it, on two independent grounds.

`FINDING-pjm138` §2.2 measured the largest single cell in the whole Dominion
CT-hour measurement as the **winter morning ramp**: CT-energy-weighted DJF 2025
runs **+$46.05/MWh** and h06–h07 are the worst hours of the day
(+$13.60 / +$14.56 load-weighted in 2025), while **overnight h01–h04 the model is
$1.6–7.3/MWh too DEAR**. Its §7 lead 3 named `gas_daily_shape` — the measured
Henry Hub daily within-month shape — as the candidate for the winter cell, on
`DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.4's reasoning that "a CT/CC stack
priced on the monthly mean *cannot* print $250 on Jan 21".

**Both halves of that charter are refuted by the committed record, and this probe
measures the refutation rather than asserting it.**

* **W0 — the mechanism is ALREADY ARMED in the keeper.** `run_config.json`
  records `scenario_config.gas_daily_shape = True` (carried on the
  `prb_overrides` channel as `coal_prb_sigmoid_overrides.gas_daily_shape`), so
  the keeper's merit order *already* sees the measured intra-month commodity
  swing. The winter cell above was measured WITH it on. Matrix cell PJM =
  **K**, not `U`; the mechanism was probed at **pjm-107** (2026-07-14, leg A of
  the pjm-107/108/109 measured-tail cycle), passed every gate, and became the
  `2026-07-14-pjm-107-gas-daily` keeper.
* **W1 — and it could not reach an hour-of-day defect even if it were off**,
  because its resolution is wrong by construction. `gas_daily_shape_factors`
  builds one factor per CALENDAR DAY and repeats it across that day's 24 hours
  (`hubs.py`: ``np.repeat(day_factor, 24)``). A daily factor moves all 24 hours
  of a day by the SAME multiple, so it cannot create, close or even perturb any
  intra-day differential — and the winter morning ramp is precisely an intra-day
  differential (h06–h07 against h01–h04 inside the same winter days). Worse, the
  overnight hours it would lift in lockstep are the hours the model is already
  too DEAR in, so the mechanism's sign is wrong on half the cell. Verified
  numerically here, not argued.

Having disposed of the chartered lever, the probe measures what the cell
actually is, with the same instruments and the same identity `FINDING-pjm138`
used, so the numbers are directly comparable:

* **W2 — the handoff's own M1, run as asked.** The system-energy gap conditional
  on the day's measured HH deviation from its own monthly mean. If the commodity
  swing drove the winter cell, the gap would concentrate on high-factor days.
* **W3 — the winter-morning-ramp cell, decomposed.** The pjm-138 §1 identity
  (`total = system-energy + basis`) plus the §3 reserve credit, re-pointed at
  DJF × hour-of-day windows instead of the all-CT-hours aggregate, so the cell's
  own **reachable residual** is sized the same way the headline defect was.
* **W4 — the overnight leg** (`FINDING-pjm138` §7 lead 2, never measured): what
  sets the model's h01–h04 price against what set PJM's, including the model
  price's own pinning signature and the class dispatch that produces it.
* **W5 — the ramp itself.** The measured and modelled DJF hour-of-day price
  profiles side by side, and the h04 → h07 morning **ramp rate** each side
  produces. This separates a level miss from a shape miss, which is the
  distinction the whole charter turns on.
* **W6 — WHO sets the model's price in each cell** (`--with-fleet`). The pjm-138
  §4.1 marginal-ownership census re-pointed at the overnight and morning-ramp
  windows: in an LP the units offering *at* the dual are the price setters, so
  the census needs the offers and the duals and no solve. This is the second
  half of lead 2 — not just that the model is too dear overnight, but which
  class's rung it is too dear *on*. Requires the curated `data/clean/` inputs
  (the fleet is rebuilt through `replay_keeper`'s own meta→kwarg mapping with
  `run_year` forced to `fleet_only=True`, so no LP is constructed); the rest of
  the probe runs without them.

Committed inputs only, no LP: the keeper `hourly/` sidecars, PJM's committed
`PJM-AS` day-ahead reserve results, `data/raw/gas-prices/henry_hub_daily.csv`,
the CAMPD unit-level record, the committed benchmark payload, and the
`data/raw/pjm-zonal-lmp/` DA component intake. The measured-side loaders are
imported from `_pjm138_mec_gap_shape.py` verbatim so the hour key is the
UTC-derived EST one (`FINDING-pjm138` §5) and no statistic here inherits
pjm-137's EPT offset. Nothing is written outside `results/probes/`.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm139_winter_ramp.py
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm139_winter_ramp.py \
        --bundle results/calibration/pjm137_ctheatrate_B
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.fuel.hubs import gas_daily_shape_factors  # noqa: E402

YEARS = (2023, 2024, 2025)
HOURS = 8760
DOM = "PJM_Dominion"

#: The hour-of-day windows the pjm-138 measurement singled out. `ramp` is the
#: morning ramp (its worst intra-day cell), `overnight` the hours the model runs
#: too dear, `evepeak` the evening peak it also misses, kept as a contrast so the
#: winter cell is never read in isolation.
WINDOWS = {
    "overnight_h01_h04": (1, 2, 3, 4),
    "ramp_h06_h07": (6, 7),
    "ramp_h05_h09": (5, 6, 7, 8, 9),
    "midday_h11_h14": (11, 12, 13, 14),
    "evepeak_h16_h18": (16, 17, 18),
}

#: Model classes whose overnight dispatch is the candidate explanation for the
#: h01–h04 over-pricing (queue item 8, `st_gas_mustrun_p25_level`). Reported with
#: the whole thermal set rather than pre-selected, so the readout cannot beg the
#: question.
THERMAL_CLASSES = (
    "COAL_BIT",
    "COAL_PRB",
    "COAL_WC",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "oil",
    "OTHER",
)

OUT_PATH = Path("results/probes/pjm139_winter_ramp.json")


def _load_p138():
    """Import the pjm-138 probe so its EST-keyed measured loaders are reused
    verbatim — the UTC-derived hour key of `FINDING-pjm138` §5, never pjm-137's
    EPT one."""
    path = REPO / "scripts" / "probes" / "_pjm138_mec_gap_shape.py"
    spec = importlib.util.spec_from_file_location("_p138", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# W1 — the mechanism's own resolution
# --------------------------------------------------------------------------
def measure_shape_resolution() -> dict:
    """Does `gas_daily_shape` have the resolution the winter cell needs? No.

    The factors are built per calendar day and repeated across 24 hours, so
    their within-day dispersion is identically zero and their hour-of-day mean
    profile is exactly flat. A mechanism with zero intra-day variation cannot
    change an intra-day differential — which is what the winter morning ramp is.
    Measured rather than asserted: the within-day standard deviation is reported
    as a number, and the hour-of-day profile as 24 values.
    """
    out: dict[str, dict] = {}
    for year in YEARS:
        f = gas_daily_shape_factors(year, HOURS)
        day = f.reshape(365, 24)
        hod = np.arange(HOURS) % 24
        month = _hour_month(year)
        djf = np.isin(month, (12, 1, 2))
        # Day-level view for the cold-snap statistics.
        day_factor = day[:, 0]
        day_month = month.reshape(365, 24)[:, 0]
        djf_days = np.isin(day_month, (12, 1, 2))
        jan_days = day_month == 1
        out[str(year)] = {
            # --- the resolution kill -------------------------------------
            "max_within_day_std": float(day.std(axis=1).max()),
            "hour_of_day_mean_profile": [float(f[hod == h].mean()) for h in range(24)],
            "hour_of_day_profile_range": float(
                max(f[hod == h].mean() for h in range(24))
                - min(f[hod == h].mean() for h in range(24))
            ),
            "corr_factor_vs_hour_of_day": float(np.corrcoef(f, hod)[0, 1]),
            # --- the swing it DOES carry (so the kill is not "it's inert") -
            "factor_range": [float(f.min()), float(f.max())],
            "djf_factor": {
                "min": float(f[djf].min()),
                "p50": float(np.median(f[djf])),
                "max": float(f[djf].max()),
            },
            "jan_peak_day_factor": float(day_factor[jan_days].max()),
            "djf_days_above_1p5x": int(np.sum(day_factor[djf_days] > 1.5)),
            "djf_days_above_2x": int(np.sum(day_factor[djf_days] > 2.0)),
            "djf_days": int(djf_days.sum()),
        }
    return out


def _hour_month(year: int) -> np.ndarray:
    """Calendar month for each of the 8760 non-leap hour-of-year slots."""
    idx = pd.date_range(f"{year}-01-01", periods=HOURS + 48, freq="h")
    idx = idx[~((idx.month == 2) & (idx.day == 29))][:HOURS]
    return idx.month.to_numpy()


# --------------------------------------------------------------------------
# the per-year measurement
# --------------------------------------------------------------------------
def measure(bundle: Path) -> dict:
    p138 = _load_p138()
    p137 = p138._load_p137()
    per_year: dict[str, dict] = {}

    for year in YEARS:
        comp = p138._measured_components_est(year, p137)
        mdl = p138._model_year(bundle, year)
        ct, ct_meta = p137._dominion_ct_hourly(year)
        res = p138._measured_reserve_est(year)

        mec = comp["mec"][DOM].to_numpy(float)  # RTO-uniform system energy price
        lmp = comp["lmp"][DOM].to_numpy(float)
        syn = res["syn_mcp"]
        syn_mad = res["mad_syn_mcp"]

        month = _hour_month(year)
        hod = np.arange(HOURS) % 24
        djf = np.isin(month, (12, 1, 2))
        factor = gas_daily_shape_factors(year, HOURS)

        # pjm-138 §1's identity, hour by hour.
        sys_gap = mec - mdl["lw"]
        basis_gap = (lmp - mec) - (mdl["dom"] - mdl["lw"])
        total_gap = lmp - mdl["dom"]

        ok = np.isfinite(mec) & np.isfinite(lmp) & np.isfinite(mdl["dom"])
        okr = ok & np.isfinite(syn)
        wload = np.where(ok, mdl["load"], 0.0)
        wct = np.where(ok, ct, 0.0)

        def _cell(mask: np.ndarray, w: np.ndarray) -> dict:
            """The pjm-138 decomposition + reserve credit over one hour mask."""
            m = mask & okr
            ww = w[m]
            if ww.sum() <= 0:
                return {}

            def _q(x: np.ndarray) -> float:
                return float((x[m] * ww).sum() / ww.sum())

            return {
                "hours": int(m.sum()),
                "measured_dom_lmp": _q(lmp),
                "model_dom_dual": _q(mdl["dom"]),
                "total_gap": _q(total_gap),
                "system_energy_gap": _q(sys_gap),
                "basis_gap": _q(basis_gap),
                "measured_mec": _q(mec),
                "model_system_lw": _q(mdl["lw"]),
                "measured_syn_mcp": _q(syn),
                "measured_syn_mcp_mad": _q(syn_mad),
                "model_reserve_dual": _q(mdl["reserve"]),
                # The most generous attribution the closed reserve lane can
                # receive (pjm-138 §3.1) — a LOWER bound on the reachable part.
                "residual_after_reserve_credit": _q(sys_gap - syn + mdl["reserve"]),
                "residual_after_reserve_credit_mad": _q(
                    sys_gap - syn_mad + mdl["reserve"]
                ),
                "mean_gas_day_factor": float(factor[m].mean()),
            }

        # ---- W2 the gap conditional on the day's measured gas deviation ----
        # The handoff's M1, run as specified. Deciles are over the DAY factor so
        # each bucket is a set of whole days, which is the mechanism's own grain.
        fdec = p138._deciles(factor + np.arange(HOURS) * 1e-12)
        w2 = {
            "all_hours_by_gas_factor_decile": p138._bucket_stats(
                sys_gap, wload, fdec, range(1, 11)
            ),
            "djf_by_gas_factor_decile": p138._bucket_stats(
                np.where(djf, sys_gap, np.nan), wload, fdec, range(1, 11)
            ),
            "corr_gas_factor_vs_system_gap": float(
                np.corrcoef(factor[ok], sys_gap[ok])[0, 1]
            ),
            "corr_gas_factor_vs_system_gap_djf": float(
                np.corrcoef(factor[ok & djf], sys_gap[ok & djf])[0, 1]
            ),
            "mean_factor_by_window": {
                lab: float(factor[np.isin(hod, hrs) & djf].mean())
                for lab, hrs in WINDOWS.items()
            },
        }

        # ---- W3 the winter cell, decomposed -------------------------------
        w3 = {
            "djf_all_hours": {
                "load_weighted": _cell(djf, wload),
                "ct_weighted": _cell(djf, wct),
            },
            "jja_all_hours": {
                "load_weighted": _cell(np.isin(month, (6, 7, 8)), wload),
                "ct_weighted": _cell(np.isin(month, (6, 7, 8)), wct),
            },
        }
        for lab, hrs in WINDOWS.items():
            hm = np.isin(hod, hrs)
            w3[f"djf_{lab}"] = {
                "load_weighted": _cell(djf & hm, wload),
                "ct_weighted": _cell(djf & hm, wct),
            }
            w3[f"annual_{lab}"] = {"load_weighted": _cell(hm, wload)}

        # ---- W4 the overnight leg -----------------------------------------
        w4 = _overnight(bundle, year, mdl, mec, lmp, syn, hod, month, ok)

        # ---- W5 the ramp both sides ---------------------------------------
        def _prof(x: np.ndarray, mask: np.ndarray) -> list[float]:
            return [float(np.nanmean(x[mask & (hod == h)])) for h in range(24)]

        djf_mec = _prof(mec, djf & ok)
        djf_mdl = _prof(mdl["lw"], djf & ok)
        djf_syn = _prof(syn, djf & okr)
        w5 = {
            "djf_hour_of_day": {
                "measured_mec": djf_mec,
                "model_system_price": djf_mdl,
                "gap": [a - b for a, b in zip(djf_mec, djf_mdl)],
                "measured_syn_mcp": djf_syn,
            },
            # The single cleanest statistic in the probe: the morning ramp each
            # side actually produces, h04 (the trough) -> h07 (the peak of the
            # ramp). A level miss leaves the ramp rates equal; a shape miss does
            # not.
            "djf_morning_ramp_h04_to_h07": {
                "measured_mec": float(djf_mec[7] - djf_mec[4]),
                "model_system_price": float(djf_mdl[7] - djf_mdl[4]),
                "measured_incl_reserve": float(
                    (djf_mec[7] + djf_syn[7]) - (djf_mec[4] + djf_syn[4])
                ),
            },
            "djf_trough_to_peak": {
                "measured_mec": float(max(djf_mec) - min(djf_mec)),
                "model_system_price": float(max(djf_mdl) - min(djf_mdl)),
            },
        }

        per_year[str(year)] = {
            "fleet": ct_meta,
            "W2_gap_vs_gas_deviation": w2,
            "W3_winter_cell_decomposed": w3,
            "W4_overnight": w4,
            "W5_ramp": w5,
        }

    return per_year


def _overnight(
    bundle: Path,
    year: int,
    mdl: dict,
    mec: np.ndarray,
    lmp: np.ndarray,
    syn: np.ndarray,
    hod: np.ndarray,
    month: np.ndarray,
    ok: np.ndarray,
) -> dict:
    """What sets the model's h01–h04 price, against what set PJM's.

    `FINDING-pjm138` §7 lead 2: the model runs $1.6–7.3/MWh too DEAR overnight
    and the reserve credit does not touch it, and nothing in the lineage has
    measured why. Two candidate causes are distinguishable without a solve:

    * a **level** miss — the model's cheapest overnight marginal offer is simply
      dearer than PJM's marginal unit; or
    * a **pinning** artifact — the model's overnight price sits on a small number
      of discrete offer rungs (a floored class's marginal cost), so it cannot
      track PJM's overnight distribution at all.

    The pinning signature is measurable directly: count the distinct rounded
    price levels the model prints overnight and the share of hours the modal one
    holds, against the same statistics for PJM's own MEC. A class held at a floor
    also shows as near-zero dispersion in its own overnight dispatch, so the
    class hourly sidecar identifies which mechanism is doing it.
    """
    night = np.isin(hod, (1, 2, 3, 4)) & ok
    djf_night = night & np.isin(month, (12, 1, 2))

    cls = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    piv = (
        cls.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .reindex(range(HOURS))
        .fillna(0.0)
    )

    def _pin(x: np.ndarray, mask: np.ndarray) -> dict:
        v = np.round(x[mask], 2)
        vals, cnt = np.unique(v, return_counts=True)
        return {
            "distinct_levels": int(len(vals)),
            "modal_level": float(vals[int(np.argmax(cnt))]),
            "modal_share_pct": float(cnt.max() / cnt.sum() * 100),
            "p05": float(np.percentile(x[mask], 5)),
            "p50": float(np.percentile(x[mask], 50)),
            "p95": float(np.percentile(x[mask], 95)),
        }

    out = {
        "hours": int(night.sum()),
        "mean_measured_mec": float(mec[night].mean()),
        "mean_model_system_price": float(mdl["lw"][night].mean()),
        "mean_system_gap": float((mec - mdl["lw"])[night].mean()),
        "mean_measured_syn_mcp": float(np.nanmean(syn[night])),
        "djf_mean_system_gap": float((mec - mdl["lw"])[djf_night].mean()),
        "pinning_model": _pin(mdl["lw"], night),
        "pinning_measured_mec": _pin(mec, night),
        # Share of overnight hours in which PJM's own system energy price is
        # BELOW the model's — i.e. the model has no offer cheap enough to
        # reproduce PJM's overnight clearing point.
        "pct_hours_measured_mec_below_model": float(
            np.mean(mec[night] < mdl["lw"][night]) * 100
        ),
        "class_overnight": {},
    }
    for k in THERMAL_CLASSES:
        if k not in piv.columns:
            continue
        v = piv[k].to_numpy(float)
        mu = float(v[night].mean())
        out["class_overnight"][k] = {
            "mean_gw": mu / 1e3,
            "share_of_thermal_pct": 0.0,  # filled below
            # A class pinned at a floor barely moves across the window; a class
            # dispatching economically tracks the price. cv is the discriminator.
            "cv_overnight": float(v[night].std() / mu) if mu > 0 else 0.0,
            "ratio_night_to_peak": (
                float(mu / v[np.isin(hod, (16, 17, 18))].mean())
                if v[np.isin(hod, (16, 17, 18))].mean() > 0
                else 0.0
            ),
        }
    tot = sum(c["mean_gw"] for c in out["class_overnight"].values())
    for c in out["class_overnight"].values():
        c["share_of_thermal_pct"] = float(c["mean_gw"] / tot * 100) if tot else 0.0
    return out


def measure_ownership(bundle: Path) -> dict:
    """W6 — the marginal-class census in the overnight and morning-ramp windows.

    Reuses `_pjm138_marginal_ownership`'s fleet reconstruction verbatim (the
    `meta.json` → `replay_keeper.build_kwargs` → `solve_and_persist` path with
    `run_year` forced to `fleet_only=True`), so the offers censused are the
    offers the keeper solved on. Marginal membership is the same test pjm-138
    §4.1 used: a unit is in the marginal set when its own hourly offer equals
    its own zone's dual to within `EPS`.

    Reported per window as the count share of the marginal set (pjm-122's
    construction) so the numbers line up row-for-row with `FINDING-pjm138` §4.1.
    """
    path = REPO / "scripts" / "probes" / "_pjm138_marginal_ownership.py"
    spec = importlib.util.spec_from_file_location("_p138own", path)
    own = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(own)

    out: dict[str, dict] = {}
    for year in YEARS:
        state = own._keeper_fleet(bundle, year)
        fa = state["fleet_arrays"]
        mc = np.asarray(state["mc_base"], dtype=float)
        if mc.ndim == 1:
            mc = np.repeat(mc[:, None], HOURS, axis=1)
        avail = np.asarray(fa.pmax, dtype=float)[:, None] * np.asarray(
            fa.availability, dtype=float
        )
        grp = np.array(
            [
                str(g) if g else "?"
                for g in (
                    np.asarray(fa.plant_group, dtype=object)
                    if getattr(fa, "plant_group", None) is not None
                    else np.array(["?"] * mc.shape[0], dtype=object)
                )
            ],
            dtype=object,
        )

        price, lw, netload = own._model_prices(bundle, year)
        zones = list(price.columns)
        from market_sim.config.iso_configs import get_iso_config

        all_zone_names = list(get_iso_config("PJM").zone_names)
        zi = np.asarray(fa.zone_idx, dtype=int)
        zone_name = np.array(
            [
                all_zone_names[i] if i < len(all_zone_names) else own.EXTERNAL_ZONE
                for i in zi
            ],
            dtype=object,
        )
        internal = np.isin(zone_name, zones)
        dual = np.zeros_like(mc)
        for z in zones:
            m = zone_name == z
            if m.any():
                dual[m, :] = price[z].to_numpy(float)[None, :]

        hod = np.arange(HOURS) % 24
        month = _hour_month(year)
        djf = np.isin(month, (12, 1, 2))
        cells = {
            "overnight_h01_h04": np.isin(hod, (1, 2, 3, 4)),
            "djf_overnight_h01_h04": np.isin(hod, (1, 2, 3, 4)) & djf,
            "djf_ramp_h06_h07": np.isin(hod, (6, 7)) & djf,
            "djf_evepeak_h16_h18": np.isin(hod, (16, 17, 18)) & djf,
        }
        per_cell: dict[str, dict] = {}
        for lab, sel in cells.items():
            sub_mc, sub_av, sub_du = mc[:, sel], avail[:, sel], dual[:, sel]
            live = internal[:, None] & (sub_av > 1.0)
            at = live & (np.abs(sub_mc - sub_du) <= own.EPS)
            n_at = at.sum(axis=0)
            good = n_at > 0
            share: dict[str, float] = {}
            for k in sorted(set(grp[internal])):
                km = grp == k
                # Each hour contributes 1.0 split equally across the units at
                # its dual, then hours are averaged — pjm-122's count share.
                share[k] = float(
                    np.mean(at[km][:, good].sum(axis=0) / n_at[good]) * 100
                )
            per_cell[lab] = {
                "hours": int(sel.sum()),
                "hours_with_a_marginal_unit": int(good.sum()),
                "mean_dual": float(lw[sel].mean()),
                "count_share_pct": {
                    k: v
                    for k, v in sorted(share.items(), key=lambda kv: -kv[1])
                    if v > 0.05
                },
            }
        out[str(year)] = per_cell
    return out


#: Model class -> the CC/CT/ST family bucket
#: `scripts/data/derive_campd_ramp_envelopes.py::_bucket` builds envelopes on
#: (`_UNIT_TYPE_BUCKET` for CC/CT, `_DEFAULT_BUCKET` = ST for every boiler), so
#: the model side is aggregated on the SAME families the envelope table keys on.
CLASS_BUCKET = {
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "CT_PEAKER": "CT",
    "CT_CHP": "CT",
    "COAL_BIT": "ST",
    "COAL_PRB": "ST",
    "COAL_WC": "ST",
    "ST_GAS": "ST",
    "ST_CHP": "ST",
}


def _bench_bucket_hourly(year: int) -> dict[str, np.ndarray]:
    """Measured hourly MW per CC/CT/ST family from the COMMITTED bench payload.

    `frontend/data/backcast/bench/PJM/<year>.json.gz` carries, per model-fleet
    plant, the CAMPD actual as `round(100 x mw / nameplate)` uint8 bytes plus the
    plant's nameplate — the same record the C1/C7 gates score against, and the
    one `FINDING-pjm137` §5 requires a zonal class actual be taken from (it
    carries `split: "unit_hourly"` at mixed sites). Decoded here on the
    nameplate basis rather than rescaled to `c_ann`, because a uniform per-plant
    scalar cannot change the FRACTIONAL ramp statistic this pre-check turns on.

    Byte quantization is 1 % of each plant's nameplate. It is immaterial to a
    fleet aggregate — independent across the 214 plants, so the aggregate error
    is ~1/sqrt(n) of one plant's step — but it is why this pre-check is stated at
    the family aggregate and never per plant.
    """
    import base64
    import gzip

    path = REPO / "frontend/data/backcast/bench/PJM" / f"{year}.json.gz"
    with gzip.open(path) as fh:
        bench = json.load(fh)["bench"]["plants"]

    out = {b: np.zeros(HOURS) for b in ("CC", "CT", "ST")}
    for rec in bench.values():
        if not isinstance(rec, dict):
            continue
        bucket = CLASS_BUCKET.get(str(rec.get("group")))
        if bucket is None or not rec.get("campd"):
            continue
        raw = np.frombuffer(base64.b64decode(rec["campd"]), dtype=np.uint8).astype(
            float
        )
        mw = raw[:HOURS] / 100.0 * float(rec.get("npl") or 0.0)
        out[bucket][: len(mw)] += mw
    return out


def measure_ramp_headroom(bundle: Path) -> dict:
    """W7 — the no-LP pre-check for the successor lever (`ramp_envelopes`, PJM `U`).

    `pjm137_ctheatrate_B` runs `ramp_limits = False`: the LP carries NO
    intertemporal coupling on the thermal fleet, so every hour is an independent
    economic dispatch and the model's morning "ramp" is a free slide up the merit
    order. W5 measures the consequence — the model reproduces only 18–26 % of
    PJM's own winter morning price ramp and its DJF profile is far too flat.
    `ramp_envelopes` (CAMPD-measured max observed 1-h move per plant-family, zero
    fitted DOF, matrix PJM = `U`, armed in no keeper in any ISO) is the
    structurally-correct mechanism for that, so the pjm-123 discipline applies:
    pre-check it without a solve before chartering it.

    **The test is deliberately ONE-SIDED, and reported as such.** If the model's
    own family aggregate moves MORE per hour, as a fraction of its own fleet
    peak, than the real fleet ever demonstrably did, then some per-plant envelope
    row MUST bind — the aggregate is the sum of the parts, so aggregate excess
    proves binding. The converse does NOT hold: an aggregate move inside the
    aggregate envelope can still contain individual plants exceeding theirs, so
    this measurement can prove the mechanism FIRES but can never prove it INERT.
    Stated as a bound, exactly as `FINDING-pjm138` §3.1 states its reserve
    credit.

    Fractions of each side's own peak are used rather than MW because the bench
    series is CAMPD **gross** while the model's `P` columns are **net** (the
    ~2–7 % rebasis the loader applies, ercot-132 leg A), and because CEMS
    coverage and the model fleet are not the same unit set.
    """
    out: dict[str, dict] = {}
    for year in YEARS:
        meas = _bench_bucket_hourly(year)
        cls = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
        cls = cls[cls["pass"] == "P1"]
        piv = (
            cls.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
            .reindex(range(HOURS))
            .fillna(0.0)
        )
        month = _hour_month(year)
        djf = np.isin(month, (12, 1, 2))

        per_bucket: dict[str, dict] = {}
        for bucket in ("CC", "CT", "ST"):
            cols = [c for c, b in CLASS_BUCKET.items() if b == bucket and c in piv]
            mdl = piv[cols].sum(axis=1).to_numpy(float)
            act = meas[bucket]

            def _stats(x: np.ndarray) -> dict:
                peak = float(x.max())
                d = np.diff(x)
                up = d[d > 0]
                if peak <= 0 or not len(up):
                    return {}
                # The DJF morning rise the defect lives in: h04 -> h07 on each
                # winter day, as a fraction of the fleet's own peak.
                rise = []
                for d0 in range(365):
                    if not djf[d0 * 24]:
                        continue
                    rise.append(x[d0 * 24 + 7] - x[d0 * 24 + 4])
                return {
                    "fleet_peak_mw": peak,
                    "max_1h_up_mw": float(up.max()),
                    "max_1h_up_pct_of_peak": float(up.max() / peak * 100),
                    "p99_1h_up_pct_of_peak": float(np.percentile(up, 99) / peak * 100),
                    "djf_mean_h04_to_h07_rise_pct_of_peak": float(
                        np.mean(rise) / peak * 100
                    ),
                    "djf_max_h04_to_h07_rise_pct_of_peak": float(
                        np.max(rise) / peak * 100
                    ),
                }

            ms, as_ = _stats(mdl), _stats(act)
            if not ms or not as_:
                continue
            per_bucket[bucket] = {
                "model": ms,
                "actual": as_,
                # > 1.0 means the model out-ramps the real fleet on that
                # statistic, i.e. an envelope built from the actual WOULD bind.
                "ratio_model_over_actual": {
                    k: float(ms[k] / as_[k])
                    for k in ms
                    if k != "fleet_peak_mw" and as_.get(k, 0) > 0
                },
            }
        out[str(year)] = per_bucket
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle",
        type=Path,
        default=Path("results/calibration/pjm137_ctheatrate_B"),
        help="calibration bundle whose hourly/ sidecars supply the model duals",
    )
    ap.add_argument(
        "--with-fleet",
        action="store_true",
        help="also run W6, the marginal-ownership census (needs data/clean/)",
    )
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args(argv)

    print("pjm-139 W1 — gas_daily_shape resolution …", flush=True)
    payload = {
        "bundle": str(args.bundle),
        "years": list(YEARS),
        "W1_shape_resolution": measure_shape_resolution(),
    }
    print("pjm-139 W2/W3/W4/W5 — the winter cell …", flush=True)
    payload["per_year"] = measure(args.bundle)
    print("pjm-139 W7 — ramp-headroom pre-check …", flush=True)
    payload["W7_ramp_headroom"] = measure_ramp_headroom(args.bundle)
    if args.with_fleet:
        print("pjm-139 W6 — marginal ownership by window …", flush=True)
        payload["W6_ownership"] = measure_ownership(args.bundle)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
