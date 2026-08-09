"""Shared harness for miso-147 — high-price-hour dispatch composition (Phase 0).

Everything every miso-147 probe shares: the four strata masks built once from
the ACTUAL RT series (PREREG §2(a)), the single C3a weight (§2(b)), the Pair-A
bucket map and Pair-B family map (§4.1/§4.2), the CAMPD unit-grain loader
(§2(c) — DIRECT ``campd-unit-level`` reads; never ``load_campd_hourly``, whose
facility-level preference silently collapses IL/TX to facility grain), the
gross→net parasitic conversion (the pipeline's own factor artifact), and a
fleet-side pack cache so ``fleet_state`` is rebuilt once per year, not once per
probe.

PREREG (pushed before any adjudicating statistic, PR #3785):
``results/calibration/PREREG-miso147-highprice-dispatch-composition-2026-08-09.md``

Probe hygiene (miso-140b §6): the repo root is inserted on ``sys.path`` below
and every probe entry point calls :func:`hygiene`.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _i, _p in enumerate((REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes")):
    sys.path.insert(_i, str(_p))

from _miso143_stack import (  # noqa: E402
    COAL_COLS,
    GAS_COLS,
    HOURS,
    KEEPER,
    THERMAL_COLS,
    YEARS,
    clear_many,
    fleet_state,
    hygiene,
    klass_of,
    markup_ceiling,
    month_of_hour,
    sidecar_classes,
    sidecar_price,
    windows,
)
from _miso137_c3a_gap_decomposition import actual_hourly  # noqa: E402

# --------------------------------------------------------------------------- #
# PREREG §2(a) — strata constants
# --------------------------------------------------------------------------- #
TAIL_USD = 200.0  #: "ordinary" boundary, INCLUSIVE (miso-146 G-F2 convention)
NEAR_LO_USD = 100.0  #: S2 lower bound, exclusive
S1_Q = 0.90  #: S1 = top decile of the year's <=$200 population

# PREREG §4.3 — the materiality floor, a neutral scale rule fixed pre-measurement
FLOOR_MW = 300.0
FLOOR_FRAC = 0.05


def floor_for(actual_mw: float) -> float:
    """PREREG §4.3: ``max(300 MW, 5% of the actual-side mean MW)``."""
    return max(FLOOR_MW, FLOOR_FRAC * float(actual_mw))


# --------------------------------------------------------------------------- #
# PREREG §4.1 — Pair A bucket map (asserted against the sidecar at load)
# --------------------------------------------------------------------------- #
MODEL_BUCKETS: dict[str, tuple[str, ...]] = {
    "coal": COAL_COLS,
    "gas_merchant": ("CC_REGULAR", "CT_PEAKER", "ST_GAS"),
    "gas_chp": ("CC_CHP", "CT_CHP", "ST_CHP"),
    "nuclear": ("nuclear",),
    "wind": ("wind",),
    "solar": ("solar",),
    "hydro": ("hydro",),
    "other_oil_bio": ("OTHER", "biomass", "oil"),
    "net_import": ("import",),
}

#: EIA-930 series per bucket, on MISO's OWN reporting fold (verified at run
#: time): the MISO BA carries NO ``NG: OIL`` (oil folds into ``other``) and NO
#: ``NG: PS`` (pumped storage folds into hydro/``NG: WAT``); batteries appear
#: only from 2025. Gas buckets all compare against "gas" (the CHP split is
#: model-side only — 930 cannot see it, PREREG §4.1 BTM caveat); net_import
#: compares to −interchange.
E930_KEY: dict[str, str] = {
    "coal": "coal",
    "gas_merchant": "gas",
    "gas_chp": "gas",
    "gas_total": "gas",
    "nuclear": "nuclear",
    "wind": "wind",
    "solar": "solar",
    "hydro_ps": "hydro",
    "other_oil_bio": "other",
    "net_import": "-interchange",
    "battery": "battery (2025 only)",
}

# PREREG §4.2 — Pair B family map (CAMPD families from bench_multiclass)
FAMILY_TO_KLASSES: dict[str, tuple[str, ...]] = {
    "CC": ("CC_REGULAR", "CC_CHP"),
    "CT": ("CT_PEAKER", "CT_CHP"),
    "ST_GAS": ("ST_GAS", "ST_CHP"),
    "ST_COAL": COAL_COLS,
}
FAMILY_930_FUEL = {"CC": "gas", "CT": "gas", "ST_GAS": "gas", "ST_COAL": "coal"}

#: The keeper sidecar's verified klass vocabulary (availability check, PREREG
#: §10.2). An unmapped klass reading silently as zero is the miso-141/143 trap;
#: sidecar_pivot() asserts exact equality.
EXPECTED_KLASSES = frozenset(
    {
        "CC_CHP", "CC_REGULAR", "COAL_BIT", "COAL_LIGNITE", "COAL_PRB",
        "CT_CHP", "CT_PEAKER", "OTHER", "ST_CHP", "ST_GAS",
        "biomass", "hydro", "import", "nuclear", "oil", "solar", "wind",
    }
)


# --------------------------------------------------------------------------- #
# Strata (PREREG §2(a)) — built once, from the ACTUAL RT series only
# --------------------------------------------------------------------------- #
def strata(year: int) -> dict:
    """Masks + metadata for S0/MAYCTRL, S1, S2, S3 of one year.

    Never pooled; S1/S2 may overlap and the overlap is reported wherever both
    appear (PREREG §2(a)).
    """
    rt, _da = actual_hourly(year)
    valid = np.isfinite(rt)
    s3 = valid & (rt > TAIL_USD)
    s2 = valid & (rt > NEAR_LO_USD) & (rt <= TAIL_USD)
    pop = rt[valid & (rt <= TAIL_USD)]
    thr = float(np.quantile(pop, S1_Q))
    s1 = valid & (rt <= TAIL_USD) & (rt >= thr)
    may = valid & (month_of_hour(np.arange(HOURS)) == 5)
    may_name = "S0" if year == 2025 else "MAYCTRL"
    masks = {"S1": s1, "S2": s2, "S3": s3, may_name: may}
    return {
        "year": year,
        "rt": rt,
        "valid": valid,
        "masks": masks,
        "S1_thr_usd": round(thr, 4),
        "counts": {k: int(v.sum()) for k, v in masks.items()},
        "overlap_S1_S2": int((s1 & s2).sum()),
        "n_valid": int(valid.sum()),
    }


def wmean(x: np.ndarray, w: np.ndarray, mask: np.ndarray) -> float:
    """C3a-weighted mean of ``x`` over ``mask`` hours (NaN-guarded)."""
    m = mask & np.isfinite(x) & np.isfinite(w)
    ws = float(w[m].sum())
    return float((x[m] * w[m]).sum() / ws) if ws > 0 else float("nan")


def c3a_weight(year: int) -> np.ndarray:
    """The single weight (PREREG §2(b)): keeper sidecar per-hour total demand."""
    return sidecar_price(year)[1]


def model_price(year: int) -> np.ndarray:
    """Keeper P1 load-weighted hourly price (the C3a model series)."""
    return sidecar_price(year)[0]


# --------------------------------------------------------------------------- #
# Model-side loaders
# --------------------------------------------------------------------------- #
def sidecar_pivot(year: int) -> pd.DataFrame:
    """P1 class dispatch (8760 x klass), asserting the full 17-klass vocabulary."""
    piv = sidecar_classes(year)
    got = set(map(str, piv.columns))
    assert got == set(EXPECTED_KLASSES), (
        f"sidecar klass vocabulary drifted for {year}: "
        f"missing {sorted(EXPECTED_KLASSES - got)}, extra {sorted(got - EXPECTED_KLASSES)}"
    )
    return piv


def storage_net(year: int, techs: tuple[str, ...] | None = None) -> np.ndarray:
    """P1 storage net output (discharge - charge), (8760,) MW.

    ``techs`` restricts to sidecar tech values (e.g. ``("pumped_storage",)``) —
    needed because EIA-930 MISO folds PS into hydro (NG: WAT) and carries
    batteries separately (2025 only), so the Pair-A fold must mirror that.
    """
    df = pd.read_parquet(KEEPER / "hourly" / f"storage_{year}.parquet")
    df = df[df["pass"] == "P1"]
    if techs is not None:
        df = df[df["tech"].isin(techs)]
    g = df.groupby("hour").agg(d=("discharge_mw", "sum"), c=("charge_mw", "sum"))
    g = g.reindex(range(HOURS)).fillna(0.0)
    return (g["d"] - g["c"]).to_numpy(float)


def bucket_series(piv: pd.DataFrame, klasses: tuple[str, ...]) -> np.ndarray:
    """Sum the pivot's klass columns for one bucket, (8760,) MW."""
    return piv[list(klasses)].sum(axis=1).to_numpy(float)


# --------------------------------------------------------------------------- #
# Actual-side loaders
# --------------------------------------------------------------------------- #
def e930(year: int) -> dict[str, np.ndarray]:
    """EIA-930 MISO BA hourly benchmark dict ((8760,) MW arrays)."""
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    d = load_eia_hourly_benchmark("MISO", year)
    assert d is not None, f"EIA-930 MISO benchmark unavailable for {year}"
    return d


def e930_demand(year: int) -> np.ndarray:
    """EIA-930 MISO BA metered demand, (8760,) MW (Pair-A control row)."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    df = _eia_hourly_frame_filled("MISO", year)
    assert df is not None and "Demand" in df.columns
    v = pd.to_numeric(df["Demand"], errors="coerce").interpolate().bfill().ffill()
    v = v.to_numpy(float)
    assert v.shape[0] == HOURS, f"930 Demand length {v.shape[0]} != {HOURS}"
    return v


def campd_units(year: int) -> tuple[pd.DataFrame, dict]:
    """MISO CAMPD unit-hour frame (GROSS) + universe metadata.

    Columns: ``plant_id`` (int), ``unit`` (str), ``hoy`` (0..8759), ``gross``
    (MW), ``family`` (CC/CT/ST_GAS/ST_COAL). Direct per-state unit-level reads
    with the split-facility remap and the str->int ``facilityId`` cast
    (PREREG §2(c)); restricted through the repo's canonical crosswalk
    ``build_zone_lookup("MISO")``.
    """
    from market_sim.data import campd as campd_mod
    from market_sim.data.zone_assignment import build_zone_lookup
    from scripts.lib.bench_multiclass import unit_family

    zones = build_zone_lookup("MISO")
    frames: list[pd.DataFrame] = []
    unresolved: dict[str, float] = {}
    for st in campd_mod.states_for_iso("MISO"):
        path = REPO / "data" / "raw" / "campd-unit-level" / f"{st}_{year}.parquet"
        df = pd.read_parquet(
            path,
            columns=["facilityId", "unitId", "date", "hour", "grossLoad",
                     "unitType", "primaryFuelInfo"],
        )
        fac = pd.to_numeric(df["facilityId"], errors="coerce").fillna(-1).astype(int)
        uid = df["unitId"].astype(str)
        df["plant_id"] = [
            campd_mod.CAMPD_UNIT_PLANT_REMAP.get((f, u), f) for f, u in zip(fac, uid)
        ]
        df = df[df["plant_id"].isin(zones)]
        if df.empty:
            continue
        dt = pd.to_datetime(df["date"])
        hoy = campd_mod._hour_index_8760(
            dt.dt.month.to_numpy(), dt.dt.day.to_numpy(), df["hour"].to_numpy()
        )
        df = df.assign(hoy=hoy)
        df = df[df["hoy"] >= 0]  # drop Feb 29
        fam_key = df["unitType"].astype(str) + "|" + df["primaryFuelInfo"].astype(str)
        fam_map = {
            k: unit_family(*k.split("|", 1)) for k in fam_key.unique()
        }
        df = df.assign(family=fam_key.map(fam_map))
        bad = df["family"].isna()
        if bad.any():
            unresolved[st] = unresolved.get(st, 0.0) + float(
                df.loc[bad, "grossLoad"].fillna(0).sum()
            )
            df = df[~bad]
        frames.append(
            pd.DataFrame(
                {
                    "plant_id": df["plant_id"].to_numpy(int),
                    "unit": (df["plant_id"].astype(str) + ":" + df["unitId"].astype(str)),
                    "hoy": df["hoy"].to_numpy(int),
                    "gross": df["grossLoad"].fillna(0.0).to_numpy(float),
                    "family": df["family"].astype(str),
                }
            )
        )
        del df
    out = pd.concat(frames, ignore_index=True)
    meta = {
        "year": year,
        "n_units": int(out["unit"].nunique()),
        "n_plants": int(out["plant_id"].nunique()),
        "unresolved_gross_mwh_by_state": {k: round(v, 1) for k, v in unresolved.items()},
        "universe": "CAMPD fossil-only, GROSS, MISO via build_zone_lookup",
    }
    return out, meta


def parasitic_map() -> dict[int, float]:
    """The pipeline's own {plant_id: net/gross} factor artifact."""
    import run_calibration_full as rcf

    return rcf._parasitic_factor_map()


def campd_family_hourly(
    units: pd.DataFrame, basis: str, factors: dict[int, float] | None = None
) -> dict[str, np.ndarray]:
    """Per-family (8760,) MW series from the unit frame, GROSS or NET.

    NET applies the pipeline's per-plant parasitic factor (default 1.0 when a
    plant has no measured factor — the pipeline's own fallback). One basis per
    comparison, stated by the caller at the point of use (TRAP 4).
    """
    assert basis in ("gross", "net")
    g = units
    if basis == "net":
        assert factors is not None
        f = g["plant_id"].map(lambda p: factors.get(int(p), 1.0)).to_numpy(float)
        val = g["gross"].to_numpy(float) * f
    else:
        val = g["gross"].to_numpy(float)
    out: dict[str, np.ndarray] = {}
    for fam in FAMILY_TO_KLASSES:
        m = (g["family"] == fam).to_numpy()
        arr = np.zeros(HOURS)
        np.add.at(arr, g.loc[m, "hoy"].to_numpy(int), val[m])
        out[fam] = arr
    return out


def family_parasitic_factor(units: pd.DataFrame, factors: dict[int, float]) -> dict[str, float]:
    """Gross-weighted mean net/gross factor per family (for NET-basis legs)."""
    out: dict[str, float] = {}
    for fam in FAMILY_TO_KLASSES:
        g = units[units["family"] == fam]
        tot = float(g["gross"].sum())
        if tot <= 0:
            out[fam] = 1.0
            continue
        f = g["plant_id"].map(lambda p: factors.get(int(p), 1.0)).to_numpy(float)
        out[fam] = float((g["gross"].to_numpy(float) * f).sum() / tot)
    return out


# --------------------------------------------------------------------------- #
# Fleet pack (model unit-grain WITHOUT a solve) — cached per year
# --------------------------------------------------------------------------- #
def _cache_dir() -> Path:
    d = Path(os.environ.get("MISO147_CACHE", "")) or Path(tempfile.gettempdir()) / "_miso147_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fleet_pack(year: int) -> dict:
    """{klass, pmax, availability, mc_base, markup} for one year, disk-cached.

    Derived from ``fleet_state`` (``run_year(fleet_only=True)`` — no LP). The
    cache only avoids rebuilding inputs across the session's probes; it lives
    in a temp dir and is never committed.
    """
    p = _cache_dir() / f"fleet_{year}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in z.files}
    st = fleet_state(year)
    gens, fa = st["fleet"], st["fleet_arrays"]
    pack = {
        "klass": klass_of(gens).astype(str),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "availability": np.asarray(fa.availability, dtype=np.float32),
        "mc_base": np.asarray(st["mc_base"], dtype=np.float32),
        "markup": np.asarray(markup_ceiling(gens, fa, st["config"]), dtype=float),
    }
    np.savez_compressed(p, **pack)
    return pack


def fam_of_klass() -> dict[str, str]:
    """klass -> Pair-B family (fossil klasses only).

    The FLEET-side klass vocabulary (klass_of / plant_group) carries generic
    ``COAL`` where the sidecar splits COAL_BIT/COAL_LIGNITE/COAL_PRB — both
    map to the ST_COAL family (verified in the G-F3 universe registration).
    """
    out: dict[str, str] = {"COAL": "ST_COAL"}
    for fam, kl in FAMILY_TO_KLASSES.items():
        for k in kl:
            out[k] = fam
    return out


# --------------------------------------------------------------------------- #
# Outage CSV (system-grain bound; aggregate only, never class-attributed)
# --------------------------------------------------------------------------- #
def outage_daily(year: int) -> pd.DataFrame:
    """MISO daily outage MW by cause (Derated/Forced/Planned/Unplanned)."""
    p = REPO / "data" / "raw" / "miso-generation-outages" / f"miso_outages_estimated_{year}.csv"
    df = pd.read_csv(p, parse_dates=["interval_date"])
    keep = ["interval_date"] + [c for c in df.columns if c.startswith("MISO_")]
    return df[keep]


def day_of_hoy(hoy: np.ndarray) -> np.ndarray:
    """Non-leap day-of-year (0-based) for hour-of-year indices."""
    return np.asarray(hoy, dtype=int) // 24
