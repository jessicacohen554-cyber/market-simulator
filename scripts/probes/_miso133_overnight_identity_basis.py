"""miso-133 probe — the overnight supply identity's two un-adjudicated rows.

Executes ``results/calibration/PREREG-miso133-overnight-supply-identity-basis-2026-08-05.md``
exactly as pre-registered (pushed at ``a2be76c6``, before any adjudicating
statistic). **NO LP IS SOLVED.** Every number is read from committed artifacts
plus a no-LP fleet assembly at HEAD under the keeper's own ``run_config.json``:

* ``frontend/data/backcast/runs/2026-08-05-miso-132b-cc-committed.js`` — the
  KEEPER's registered per-plant payload (model dispatch ``m``, annual ``m_ann``).
* ``frontend/data/backcast/bench/MISO/<year>.json.gz`` — the committed bench,
  per-plant CAMPD ``campd`` with the model's own class assignment (``group``),
  plus the ``btm`` / ``e_ann`` fields the CHP grid-delivered basis needs.
* ``results/calibration/miso132_ccmin_B/hourly/class_hourly_<year>.parquet`` —
  the keeper's P1 class aggregate, the FULL model class and therefore the only
  correct coverage denominator.
* the MISO dispatch fleet assembled at HEAD under the keeper config — the
  model-side plant -> class map and per-plant capacity.

What is new relative to miso-127 (``_miso127_overnight_gas_composition.py``):
that probe iterated the **bench** key set, so a model plant with no bench entry
was invisible to it by construction, and its 37-39 % ``ST_GAS`` coverage gap
could not be decomposed. This probe iterates the **model** side, which is what
makes the four-way M / X / N / U split (PREREG §1b) possible at all.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only (MISO holds no ``complete`` marker).
Rule 15: no run is produced, so there is nothing to register.
Rule 19 / KILL-1: nothing here sizes any parameter; no mechanism is armed.

Usage::

    uv run python scripts/probes/_miso133_overnight_identity_basis.py
"""

from __future__ import annotations

import base64
import dataclasses
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from lib.backcast_artifacts import decode_run_js  # noqa: E402
from lib.bench_multiclass import parse_key  # noqa: E402

#: The designated MISO keeper this screen is taken on (rule 15 bundle + its
#: registered dashboard payload). Nothing below moves it.
KEEPER_RUN = "2026-08-05-miso-132b-cc-committed"
KEEPER_BUNDLE = REPO / "results/calibration/miso132_ccmin_B"
PAYLOAD = REPO / f"frontend/data/backcast/runs/{KEEPER_RUN}.js"
OUT = REPO / "results/calibration/_miso133_overnight_identity_basis.json"

YEARS = (2023, 2024, 2025)  # rule 22: the ONLY years read anywhere below
_T = 8760

MONTH_LEN = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}
MO = np.concatenate([np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)])
HOD = np.arange(_T) % 24
#: miso-130's own July-night window, reused unchanged so the restated identity
#: is comparable to the row it replaces.
JULY_NIGHT = (MO == 7) & (HOD < 6)

#: PREREG §2 primary class; the other gas classes are reported, never gated.
PRIMARY_CLASS = "ST_GAS"
GAS_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP")
CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")

#: PREREG §1b construction gate: a class whose payload-side bucket sum misses
#: its own LP class total by more than this carries NO verdict.
RHO_GATE = 0.05
#: PREREG §2 S-1 verdict bar on the unmatched-energy split.
SPLIT_BAR = 0.50
#: PREREG §2 S-1b: the CAMPD Part 75 unit reporting threshold, MW.
CEMS_THRESHOLD_MW = 25.0
#: PREREG §2 S-2 corrected-CHP-coverage acceptance band.
CHP_BAND = (0.90, 1.10)


# --------------------------------------------------------------------------- #
# artifact decode
# --------------------------------------------------------------------------- #
def decode_series(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Decode a bench/payload hourly series to an 8760 MW array.

    The inverse of ``render_calibration_html._b64``: base64 -> ``uint8``
    capacity-factor percent, rescaled so the series sums to the entry's declared
    annual TWh. Identical to ``_miso127_overnight_gas_composition._decode`` so
    the two probes' MW are on the same basis.
    """
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    if raw.shape[0] < _T:
        raw = np.concatenate([raw, np.zeros(_T - raw.shape[0])])
    raw = raw[:_T]
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def load_bench(year: int) -> dict:
    """Return the committed MISO bench plant entries for ``year``."""
    path = REPO / f"frontend/data/backcast/bench/MISO/{year}.json.gz"
    with gzip.open(path, "rt") as fh:
        return json.load(fh)["bench"]["plants"]


def load_payload() -> dict:
    """Return the keeper's registered per-year dashboard payload."""
    return decode_run_js(PAYLOAD.read_text())["years"]


def class_hourly(year: int) -> dict[str, np.ndarray]:
    """Return ``{klass: (8760,) MW}`` from the keeper's own P1 class sidecar.

    This is the FULL model class — every LP unit in it, including units with no
    bench counterpart — and is therefore the correct coverage denominator
    (PREREG §1b, adopting miso-127's P2 rule).
    """
    df = pd.read_parquet(KEEPER_BUNDLE / f"hourly/class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    out: dict[str, np.ndarray] = {}
    for klass, g in df.groupby("klass", observed=True):
        s = g.sort_values("hour")["mw"].to_numpy(dtype=float)
        if s.shape[0] < _T:
            s = np.concatenate([s, np.zeros(_T - s.shape[0])])
        out[str(klass)] = s[:_T]
    return out


# --------------------------------------------------------------------------- #
# model side: the no-LP fleet assembly (PREREG §1a)
# --------------------------------------------------------------------------- #
def keeper_config():
    """Rebuild the keeper's own ScenarioConfig from its committed run_config."""
    from market_sim.config.scenarios import ScenarioConfig

    raw = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(
        **{k: v for k, v in raw["scenario_config"].items() if k in names}
    )


def assemble_fleet(year: int) -> list:
    """Assemble MISO's dispatch fleet at HEAD under the keeper config. NO LP."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import (
        build_base_fleet,
        build_dispatch_fleet,
        fleet_to_bins,
        load_fleet_from_csv,
    )

    cfg = keeper_config()
    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]
    raw = load_fleet_from_csv(
        "MISO",
        iso_config,
        year=year,
        measured_ct_heat_rates=cfg.measured_ct_heat_rates,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        cc_steam_part_capacity=cfg.cc_steam_part_capacity,
    )
    bins = fleet_to_bins(raw, "MISO", cfg)
    base = build_base_fleet(
        bins,
        "MISO",
        iso_config,
        zone_names,
        cfg,
        [],
        [],
        year,
        None,
        vintage_year=year,
        legacy_n_bins=0,
    )
    fleet, _, _, _ = build_dispatch_fleet(base, bins, [], "MISO", year, zone_names, cfg)
    return fleet


def unit_klass(gen) -> str:
    """Return a generator's dispatch class, reproducing the sidecar's own rule.

    ``run_calibration_full._dispatch_frame`` classes a non-ERCOT unit by its
    ``plant_group`` and then splits a bare ``COAL`` into its supply rank via
    ``_coal_supply_class``. This mirrors that exactly so the assembled map and
    ``class_hourly`` speak the same class vocabulary.
    """
    from run_calibration_full import _coal_supply_class, _model_class_for_unit

    k = str(getattr(gen, "plant_group", "") or "")
    if not k:
        k = _model_class_for_unit(
            str(gen.unit_id), str(gen.fuel_type), getattr(gen, "efficiency_bin", None)
        )
    if k == "COAL":
        k = _coal_supply_class(int(gen.plant_code or 0))
    return k


def model_plant_map(year: int) -> tuple[dict[int, dict[str, float]], dict]:
    """Return ``({plant_code: {klass: assembled pmax MW}}, diagnostics)``.

    The model-side class map PREREG §1a declares. ``diagnostics`` carries the
    unit/plant counts so the construction is auditable from the record alone.
    """
    fleet = assemble_fleet(year)
    cap: dict[int, dict[str, float]] = defaultdict(dict)
    n_nocode = 0
    for g in fleet:
        code = int(getattr(g, "plant_code", 0) or 0)
        if code <= 0:
            n_nocode += 1
            continue
        k = unit_klass(g)
        cap[code][k] = cap[code].get(k, 0.0) + float(g.pmax_mw)
    diag = {
        "n_units": len(fleet),
        "n_units_without_plant_code": n_nocode,
        "n_plants": len(cap),
        "n_plants_multiclass": sum(1 for v in cap.values() if len(v) > 1),
    }
    return dict(cap), diag


# --------------------------------------------------------------------------- #
# S-1: the four-way decomposition (PREREG §1b / §2)
# --------------------------------------------------------------------------- #
def decompose(
    year: int, bench: dict, payload: dict, pmap: dict[int, dict[str, float]]
) -> dict:
    """Partition each model class's own payload energy into M / X / N / U.

    Iterates the MODEL side (the payload key set), resolving each key's model
    class from the slice key when it carries one and from the assembled fleet
    otherwise. A bare key the assembly resolves to zero or to more than one
    class is UNRESOLVED and is never silently assigned.
    """
    ppl = payload[str(year)]["plants"]
    buckets: dict[str, dict[str, float]] = defaultdict(
        lambda: {"M": 0.0, "X": 0.0, "N": 0.0, "U": 0.0}
    )
    counts: dict[str, Counter] = defaultdict(Counter)
    x_hist: dict[str, Counter] = defaultdict(Counter)
    u_keys: dict[str, list] = defaultdict(list)
    unresolved: list[dict] = []

    for key, pay in ppl.items():
        code, key_klass = parse_key(key)
        m_ann = float(pay.get("m_ann") or 0.0)
        if key_klass:
            klass = key_klass
        else:
            classes = pmap.get(code, {})
            if len(classes) != 1:
                unresolved.append(
                    {
                        "key": key,
                        "code": code,
                        "n_classes": len(classes),
                        "m_ann": round(m_ann, 4),
                    }
                )
                continue
            klass = next(iter(classes))

        entry = bench.get(key)
        if entry is None:
            bucket = "U"
            u_keys[klass].append((key, code, m_ann))
        elif str(entry.get("group") or "") != klass:
            bucket = "X"
            x_hist[klass][str(entry.get("group") or "<none>")] += m_ann
        elif not entry.get("campd") or entry.get("nodata"):
            bucket = "N"
        else:
            bucket = "M"
        buckets[klass][bucket] += m_ann
        counts[klass][bucket] += 1

    return {
        "buckets": {
            k: {b: round(v, 4) for b, v in d.items()} for k, d in buckets.items()
        },
        "counts": {k: dict(c) for k, c in counts.items()},
        "x_receiving_group_twh": {
            k: {g: round(v, 4) for g, v in c.items()} for k, c in x_hist.items()
        },
        "_u_keys": u_keys,
        "unresolved": unresolved,
    }


def coverage_table(dec: dict, ch: dict[str, np.ndarray]) -> dict:
    """Return per-class coverage, the unmatched split, and the PREREG rho gate."""
    out = {}
    for klass, b in dec["buckets"].items():
        lp_twh = float(ch.get(klass, np.zeros(_T)).sum()) / 1e6
        tot = b["M"] + b["X"] + b["N"] + b["U"]
        gap = b["X"] + b["N"] + b["U"]
        rho = (tot / lp_twh - 1.0) if lp_twh > 0 else float("nan")
        out[klass] = {
            "lp_class_twh": round(lp_twh, 4),
            "payload_sum_twh": round(tot, 4),
            "rho": round(rho, 4) if np.isfinite(rho) else None,
            "gated": bool(np.isfinite(rho) and abs(rho) <= RHO_GATE),
            "coverage_M": round(b["M"] / lp_twh, 4) if lp_twh > 0 else None,
            "gap_twh": round(gap, 4),
            "split_X": round(b["X"] / gap, 4) if gap > 0 else None,
            "split_N": round(b["N"] / gap, 4) if gap > 0 else None,
            "split_U": round(b["U"] / gap, 4) if gap > 0 else None,
        }
    return out


def unbenched_capacity(
    dec: dict, pmap: dict[int, dict[str, float]], klass: str
) -> dict:
    """PREREG S-1b: is 'sub-CEMS threshold' a real explanation for bucket U?

    Returns the assembled model capacity of ``klass``'s unbenched plants, split
    at the 25 MW CAMPD Part 75 reporting threshold. The threshold applies to
    UNITS; the assembled tranche capacity is per (plant, class), so the plant
    total is the conservative reading — it can only make sub-threshold look
    LESS likely, never more, and the bar is declared in that direction.
    """
    rows = []
    for key, code, m_ann in dec["_u_keys"].get(klass, []):
        mw = float(pmap.get(code, {}).get(klass, 0.0))
        rows.append(
            {
                "key": key,
                "code": code,
                "pmax_mw": round(mw, 1),
                "m_ann_twh": round(m_ann, 4),
            }
        )
    rows.sort(key=lambda r: -r["m_ann_twh"])
    tot = sum(r["pmax_mw"] for r in rows)
    small = sum(r["pmax_mw"] for r in rows if r["pmax_mw"] < CEMS_THRESHOLD_MW)
    unit = unit_grain_threshold_share([r["code"] for r in rows])
    return {
        "n_plants": len(rows),
        "capacity_mw": round(tot, 1),
        "capacity_below_25mw_mw": round(small, 1),
        # the PRE-REGISTERED statistic (plant grain, declared conservative)
        "share_below_25mw": round(small / tot, 4) if tot > 0 else None,
        # the DISCLOSED refinement: Part 75 is written at UNIT grain
        "unit_grain": unit,
        "largest": rows[:12],
    }


def unit_grain_threshold_share(codes: list[int]) -> dict:
    """Share of these plants' EIA-860 capacity on generators below 25 MW.

    The pre-registered S-1b statistic is taken at PLANT grain, which the PREREG
    declares is the conservative direction. 40 CFR Part 75 is written at UNIT
    grain, so this is the same test at the grain the rule actually uses — it is
    reported alongside the pre-registered number, never in place of it. A bank
    of sub-25 MW reciprocating engines is exactly the case the two grains
    disagree on.
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.fleet import EIA_860_PARQUET_NAME

    path = EIA_860_DIR / EIA_860_PARQUET_NAME
    if not path.exists() or not codes:
        return {}
    df = pd.read_parquet(
        path, columns=["plant_id", "plant_name", "nameplate_capacity_mw"]
    )
    df = df[df["plant_id"].astype(int).isin(set(codes))]
    if df.empty:
        return {}
    mw = df["nameplate_capacity_mw"].astype(float)
    small = float(mw[mw < CEMS_THRESHOLD_MW].sum())
    tot = float(mw.sum())
    return {
        "n_generators": int(len(df)),
        "capacity_mw": round(tot, 1),
        "capacity_below_25mw_mw": round(small, 1),
        "share_below_25mw": round(small / tot, 4) if tot > 0 else None,
        "n_plants_covered": int(df["plant_id"].nunique()),
    }


# --------------------------------------------------------------------------- #
# S-2 / S-3: the CHP basis and the restated identity
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# the DISCLOSED REPAIR basis (see the FINDING §3): the payload/bench class
# space is the model side AFTER two documented reporting transforms that
# ``class_hourly`` does not carry. Measuring coverage across that seam is what
# produced miso-127's ST_GAS number.
# --------------------------------------------------------------------------- #
def payload_class_census(
    year: int, bench: dict, payload: dict, pmap: dict[int, dict[str, float]]
) -> dict:
    """Return the payload's OWN per-class energy totals, and what is unresolved.

    Class authority is the bench ``group`` for a benched key — that IS the class
    the payload was built under — and the assembled fleet map only for keys the
    bench does not carry. A key the fleet resolves to several classes, or to
    none, is bucketed under an explicit ``MULTI:``/``NOFLEET`` label rather than
    being forced into a class.
    """
    ppl = payload[str(year)]["plants"]
    totals: dict[str, float] = defaultdict(float)
    unbenched: dict[str, float] = defaultdict(float)
    for key, pay in ppl.items():
        code, _ = parse_key(key)
        m_ann = float(pay.get("m_ann") or 0.0)
        entry = bench.get(key)
        if entry is not None:
            klass = str(entry.get("group") or "?")
        else:
            fl = pmap.get(code, {})
            if len(fl) == 1:
                klass = next(iter(fl))
            elif fl:
                klass = "MULTI:" + ",".join(sorted(fl))
            else:
                klass = "NOFLEET"
            unbenched[klass] += m_ann
        totals[klass] += m_ann
    return {
        "class_twh": {k: round(v, 4) for k, v in totals.items()},
        "unbenched_twh": {k: round(v, 4) for k, v in unbenched.items()},
    }


def mixed_plant_roster(
    year: int, bench: dict, payload: dict, pmap: dict[int, dict[str, float]]
) -> list[dict]:
    """Return the ``OTHER_FOSSIL`` mixed-plant roster inside the MISO fleet.

    ``fleet.eia860.apply_other_fossil_scoring`` re-buckets a genuinely-mixed
    gas-thermal plant (no single gas-thermal class holds 60 % of its EIA-923 net
    generation, and its two largest classes are both gas-thermal) into
    ``OTHER_FOSSIL`` on BOTH the model and the actual side of the reporting
    chain. ``class_hourly`` is written upstream of that transform, so a class's
    raw LP total and its payload/bench total are not the same quantity.
    """
    from market_sim.data.fleet.eia860 import mixed_fossil_plants

    ppl = payload[str(year)]["plants"]
    out = []
    for code in sorted(mixed_fossil_plants(year)):
        if code not in pmap:
            continue
        entry = bench.get(str(code)) or {}
        pay = ppl.get(str(code)) or {}
        out.append(
            {
                "code": int(code),
                "name": entry.get("name"),
                "model_classes_mw": {k: round(v, 1) for k, v in pmap[code].items()},
                "model_twh": round(float(pay.get("m_ann") or 0.0), 4),
                "bench_group": entry.get("group"),
                "bench_measured_twh": round(float(entry.get("c_ann") or 0.0), 4),
                "in_bench": bool(entry),
            }
        )
    return sorted(out, key=lambda r: -r["model_twh"])


def matched_stacks(
    year: int, bench: dict, payload: dict, pmap: dict[int, dict[str, float]]
) -> dict:
    """Return per-class matched model / measured stacks on BOTH bases.

    Four series per class, all over the same matched machines:

    * ``model`` — the payload's model MW **as registered** (whole-plant for CHP:
      ``render_calibration_html`` adds the behind-the-meter host block back flat
      so the per-plant panel compares a full plant to a full CAMPD plant);
    * ``model_grid`` — that series with the add-back removed, `m - btm/T`, which
      is the LP's own grid-delivered basis (``btm`` is 0 for non-CHP classes, so
      only CHP moves);
    * ``meas`` — the bench CAMPD series, whole plant;
    * ``meas_grid`` — the bench CAMPD series scaled by
      ``grid_frac = 1 - btm/e_ann``, the PREREG §1c grid-delivered basis.

    The comparable pairs are (``model``, ``meas``) and (``model_grid``,
    ``meas_grid``). Crossing them is exactly the §7b basis error.
    """
    ppl = payload[str(year)]["plants"]
    model: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(_T))
    model_grid: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(_T))
    meas: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(_T))
    meas_grid: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(_T))
    gridfrac: dict[str, list] = defaultdict(list)

    for key, entry in bench.items():
        klass = str(entry.get("group") or "")
        pay = ppl.get(key)
        if not klass or pay is None or not entry.get("campd") or entry.get("nodata"):
            continue
        npl = float(entry.get("npl") or 0.0)
        m = decode_series(pay["m"], pay.get("m_ann"), npl)
        c = decode_series(entry["campd"], entry.get("c_ann"), npl)
        e_ann = float(entry.get("e_ann") or 0.0)
        btm = float(entry.get("btm") or 0.0)
        gf = 1.0 - (btm / e_ann) if e_ann > 0 else 1.0
        gf = min(max(gf, 0.0), 1.0)
        model[klass] += m
        # the add-back is a FLAT MW block (btm TWh spread over 8760 h), so its
        # removal is exact, not an estimate.
        model_grid[klass] += np.maximum(m - max(btm, 0.0) * 1e6 / _T, 0.0)
        meas[klass] += c
        meas_grid[klass] += c * gf
        if klass in CHP_CLASSES:
            gridfrac[klass].append(gf)

    return {
        "model": dict(model),
        "model_grid": dict(model_grid),
        "meas": dict(meas),
        "meas_grid": dict(meas_grid),
        "gridfrac": {k: v for k, v in gridfrac.items()},
    }


def chp_basis(stacks: dict) -> dict:
    """PREREG S-2: CHP coverage on the crossed basis and on both clean pairs.

    ``coverage_crossed`` reproduces the §7b number (whole-plant measured over
    grid-delivered model) so the reader can see the artifact; the two clean
    pairs are ``coverage_whole`` and ``coverage_grid``, and S-2 is scored on
    the grid-delivered one.
    """
    out = {}
    for klass in CHP_CLASSES:
        m = stacks["model"].get(klass)
        if m is None or m.sum() <= 0:
            continue
        mg = stacks["model_grid"][klass]
        c = stacks["meas"][klass]
        cg = stacks["meas_grid"][klass]
        gfs = stacks["gridfrac"].get(klass, [])
        out[klass] = {
            "model_whole_twh": round(float(m.sum()) / 1e6, 4),
            "model_grid_twh": round(float(mg.sum()) / 1e6, 4),
            "meas_whole_twh": round(float(c.sum()) / 1e6, 4),
            "meas_grid_twh": round(float(cg.sum()) / 1e6, 4),
            "coverage_whole": round(float(c.sum() / m.sum()), 4),
            "coverage_grid": round(float(cg.sum() / mg.sum()), 4)
            if mg.sum() > 0
            else None,
            "coverage_crossed": round(float(c.sum() / mg.sum()), 4)
            if mg.sum() > 0
            else None,
            "grid_frac_min": round(min(gfs), 4) if gfs else None,
            "grid_frac_mean": round(float(np.mean(gfs)), 4) if gfs else None,
            "n_plants": len(gfs),
        }
    return out


def restated_identity(stacks: dict) -> dict:
    """PREREG S-3: July-night model - measured MW by class, both clean pairs."""
    out = {}
    for klass, m in stacks["model"].items():
        mg = stacks["model_grid"][klass]
        cg = stacks["meas_grid"][klass]
        c = stacks["meas"][klass]
        out[klass] = {
            "model_whole_mw": round(float(m[JULY_NIGHT].mean()), 1),
            "model_grid_mw": round(float(mg[JULY_NIGHT].mean()), 1),
            "meas_whole_mw": round(float(c[JULY_NIGHT].mean()), 1),
            "meas_grid_mw": round(float(cg[JULY_NIGHT].mean()), 1),
            # the identity's leg: grid-delivered on BOTH sides
            "delta_grid_mw": round(float((mg - cg)[JULY_NIGHT].mean()), 1),
            "delta_whole_mw": round(float((m - c)[JULY_NIGHT].mean()), 1),
        }
    return out


def slack(
    year: int, ch: dict[str, np.ndarray], pmap: dict[int, dict[str, float]]
) -> dict:
    """PREREG S-4: July-night headroom per gas class, on the keeper's dispatch.

    The miso-132(a) lesson, applied before anything is proposed: a lever that
    adds overnight non-coal supply has to work through this headroom. The
    coherence check is explicit — a class whose keeper night dispatch exceeds
    the probe's assembled capacity is marked CONTAMINATED and not relied on.
    """
    cap: dict[str, float] = defaultdict(float)
    for classes in pmap.values():
        for k, mw in classes.items():
            cap[k] += mw
    out = {}
    for klass in GAS_CLASSES:
        s = ch.get(klass)
        if s is None:
            continue
        night = float(s[JULY_NIGHT].mean())
        peak = float(s[JULY_NIGHT].max())
        c = cap.get(klass, 0.0)
        out[klass] = {
            "assembled_cap_mw": round(c, 1),
            "july_night_mean_mw": round(night, 1),
            "july_night_max_mw": round(peak, 1),
            "headroom_mean_mw": round(c - night, 1),
            "headroom_share": round(1.0 - night / c, 4) if c > 0 else None,
            "contaminated": bool(peak > c),
        }
    return out


# --------------------------------------------------------------------------- #
# verdicts
# --------------------------------------------------------------------------- #
def verdicts(per_year: dict) -> dict:
    """Score the PREREG §2 bars: S-1 (>=2 of 3 years), S-1b and S-2."""

    def hits(fn) -> list:
        return [y for y in YEARS if fn(per_year[str(y)])]

    def split(y, which):
        row = y["coverage"].get(PRIMARY_CLASS, {})
        v = row.get(f"split_{which}")
        return v if v is not None else 0.0

    def gated(y):
        return bool(y["coverage"].get(PRIMARY_CLASS, {}).get("gated"))

    hx = hits(lambda y: gated(y) and split(y, "X") >= SPLIT_BAR)
    hu = hits(lambda y: gated(y) and split(y, "U") >= SPLIT_BAR)
    hn = hits(lambda y: gated(y) and split(y, "N") >= SPLIT_BAR)
    if len(hx) >= 2:
        s1 = "H-X BOOKKEEPING ARTIFACT"
    elif len(hu) >= 2:
        s1 = "H-U NO BENCH COUNTERPART"
    elif len(hn) >= 2:
        s1 = "H-N BENCH-SIDE DATA HOLE"
    else:
        s1 = "MIXED — no single verdict"

    shares = [
        per_year[str(y)]["unbenched_ST_GAS"].get("share_below_25mw") for y in YEARS
    ]
    shares = [s for s in shares if s is not None]
    s1b = None
    if s1.startswith("H-U"):
        n_small = sum(1 for s in shares if s >= SPLIT_BAR)
        s1b = (
            "SUB-CEMS SUPPORTED"
            if n_small >= 2
            else "SUB-CEMS FAILS — roster/crosswalk defect"
        )

    # CT_PEAKER passes the rho gate in all three years, so its S-1/S-1b verdict
    # is read on the pre-registered basis exactly as written.
    ct_u = [
        y
        for y in YEARS
        if per_year[str(y)]["coverage"].get("CT_PEAKER", {}).get("gated")
        and (per_year[str(y)]["coverage"]["CT_PEAKER"].get("split_U") or 0.0)
        >= SPLIT_BAR
    ]
    ct_small = [
        per_year[str(y)]["unbenched_CT_PEAKER"].get("share_below_25mw") for y in YEARS
    ]
    ct_small = [s for s in ct_small if s is not None]
    ct_verdict = "H-U NO BENCH COUNTERPART" if len(ct_u) >= 2 else "MIXED"
    ct_s1b = None
    ct_s1b_unit = None
    if len(ct_u) >= 2:
        ct_s1b = (
            "SUB-CEMS SUPPORTED"
            if sum(1 for s in ct_small if s >= SPLIT_BAR) >= 2
            else "SUB-CEMS FAILS — roster/crosswalk defect"
        )
        us = [
            per_year[str(y)]["unbenched_CT_PEAKER"]["unit_grain"].get(
                "share_below_25mw"
            )
            for y in YEARS
        ]
        us = [s for s in us if s is not None]
        ct_s1b_unit = (
            "SUB-CEMS SUPPORTED at unit grain"
            if sum(1 for s in us if s >= SPLIT_BAR) >= 2
            else "SUB-CEMS FAILS at unit grain"
        )

    s2 = {}
    for klass in CHP_CLASSES:
        ok = [
            y
            for y in YEARS
            if (
                per_year[str(y)]["chp_basis"].get(klass, {}).get("coverage_grid")
                is not None
                and CHP_BAND[0]
                <= per_year[str(y)]["chp_basis"][klass]["coverage_grid"]
                <= CHP_BAND[1]
            )
        ]
        s2[klass] = {
            "years_in_band": ok,
            "verdict": "RESOLVED" if len(ok) >= 2 else "PARTIALLY RESOLVED",
        }

    # The disclosed repair (FINDING §3): coverage on the payload's OWN class
    # total, i.e. model and bench on the SAME side of the OTHER_FOSSIL
    # reporting transform.
    repair = {}
    for klass in (PRIMARY_CLASS, "CT_PEAKER", "CC_REGULAR", "COAL_PRB"):
        vals = []
        for y in YEARS:
            row = per_year[str(y)]
            m = row["buckets_twh"].get(klass, {}).get("M", 0.0)
            tot = row["payload_class_census"]["class_twh"].get(klass, 0.0)
            vals.append(round(m / tot, 4) if tot > 0 else None)
        repair[klass] = {
            "coverage_raw_denominator": [
                per_year[str(y)]["coverage"].get(klass, {}).get("coverage_M")
                for y in YEARS
            ],
            "coverage_transform_consistent": vals,
        }

    return {
        "S1_ST_GAS": {
            "verdict": s1,
            "years_X": hx,
            "years_U": hu,
            "years_N": hn,
            "note": (
                "KILL-5: ST_GAS fails the rho gate in all three "
                "years, so the pre-registered basis carries NO "
                "verdict — see the repair below and FINDING §3."
            ),
        },
        "S1_CT_PEAKER": {"verdict": ct_verdict, "years_U": ct_u},
        "S1b_sub_cems_ST_GAS": s1b,
        "S1b_sub_cems_CT_PEAKER": ct_s1b,
        "S1b_sub_cems_CT_PEAKER_unit_grain": ct_s1b_unit,
        "S2_chp_basis": s2,
        "REPAIR_transform_consistent_coverage": repair,
    }


def main() -> int:
    """Run the pre-registered screen and write the JSON record."""
    payload = load_payload()
    per_year: dict = {}
    for year in YEARS:
        bench = load_bench(year)
        pmap, fleet_diag = model_plant_map(year)
        ch = class_hourly(year)
        dec = decompose(year, bench, payload, pmap)
        cov = coverage_table(dec, ch)
        stacks = matched_stacks(year, bench, payload, pmap)
        per_year[str(year)] = {
            "fleet": fleet_diag,
            "coverage": cov,
            "buckets_twh": dec["buckets"],
            "bucket_counts": dec["counts"],
            "x_receiving_group_twh": dec["x_receiving_group_twh"],
            "unresolved_keys": dec["unresolved"],
            "unbenched_ST_GAS": unbenched_capacity(dec, pmap, PRIMARY_CLASS),
            "unbenched_CT_PEAKER": unbenched_capacity(dec, pmap, "CT_PEAKER"),
            "payload_class_census": payload_class_census(year, bench, payload, pmap),
            "mixed_plant_roster": mixed_plant_roster(year, bench, payload, pmap),
            "chp_basis": chp_basis(stacks),
            "restated_identity_july_night": restated_identity(stacks),
            "slack_july_night": slack(year, ch, pmap),
        }
        print(f"  {year}: done", flush=True)

    record = {
        "probe": "miso-133 overnight supply identity — basis and coverage",
        "prereg": (
            "results/calibration/"
            "PREREG-miso133-overnight-supply-identity-basis-2026-08-05.md"
        ),
        "keeper_run": KEEPER_RUN,
        "keeper_bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
        "note": (
            "NO LP SOLVED. Nothing here sizes any parameter (KILL-1); no "
            "mechanism is armed, no run is registered, the keeper does not "
            "move. Rule 22: 2023-2025 only."
        ),
        "bars": {
            "rho_gate": RHO_GATE,
            "split_bar": SPLIT_BAR,
            "cems_threshold_mw": CEMS_THRESHOLD_MW,
            "chp_band": list(CHP_BAND),
        },
        "years": per_year,
        "verdicts": verdicts(per_year),
    }
    OUT.write_text(json.dumps(record, indent=1))
    print(f"wrote {OUT}")
    print(json.dumps(record["verdicts"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
