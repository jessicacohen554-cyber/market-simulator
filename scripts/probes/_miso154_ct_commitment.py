"""miso-154 — the **CT COMMITMENT INSTRUMENT**: a reusable, no-LP
reconstruction of MISO's P1 dispatch that reproduces the **P1 startup
amortization** instead of taking prices on the base cost.

Pre-registration (pushed at ``065c83e``, blob ``771ebc33``, verified
byte-identical against the FETCHED remote ref BEFORE any adjudicating
statistic):
``results/calibration/PREREG-miso154-ct-commitment-instrument-2026-08-12.md``.

THE OBJECT (PREREG §1). miso-153's T-6b compares ``mc_base`` against the
keeper's **P1** clearing price and runs **+22.0 / +22.1 / +23.7 %** hot on
``CT_PEAKER``. But MISO's P1 clears on the **bid** cost,
``mc_bid = mc_base + markup`` (``pipeline/solve.py:254-265``), where ``markup``
is the monthly startup amortization ``startup_cost / run_length``
(``model/commitment.py::compute_monthly_markup``). Comparing a *base* cost
against a *bid*-cost clearing price admits every tranche whose startup
recovery has not been earned.

MISO arms **no** P1 bid adjustment, **no** bid-max target and **no**
commitment bridge (PREREG §1.1), so its P1 bid is EXACTLY
``mc_base + markup`` — one seam to reproduce, not several.

THE REUSABLE SURFACE (PREREG §2 — a helper, not a one-off):

    basis   = assemble_year(cfg, year)        # production chain, per-year pin
    p0      = reconstruct_p0(basis)           # the run-length source
    markup  = commitment_markup(basis, p0)    # PRODUCTION compute_monthly_markup
    mc_bid  = basis.mc_base + markup
    l1      = reconstruct_p1_pricetaking(basis, mc_bid)
    l2      = reconstruct_p1_meritorder(basis, mc_bid)
    stat    = class_energy_residual(basis, l1, "CT_PEAKER")

Each stage is independently importable and takes/returns plain arrays, so a
later session can re-use one stage without the script body.

GATING (PREREG §5): ``|resid| <= 10 %`` of ``CT_PEAKER`` energy at the
top-200 model-demand hours, on the **L1** leg (the leg directly comparable to
the published price-taking baseline). L2 is reported and NEVER gates.

RESULT — **B-PARTIAL (clears 2 of 3). NO offer-level lever follows.**
The markup correction is decisive in size and direction: the published
price-taking residual **+21.99 / +22.14 / +23.72 %** becomes
**−13.21 / −7.53 / −4.47 %**, so the base-vs-bid mis-specification accounted
for **28–35 pp** of it. 2024/2025 clear; **2023 fails at −13.21 %**.

**LIMITATION — READ BEFORE RE-USING THIS HELPER (PREREG §5 B-PARTIAL).**
*The instrument's own uncertainty is WIDER than the bar it is gated on.*

* **The P0 proxy dominates.** There is no committed P0 pass, so the markup's
  run-length source is reconstructed. Bounding it with the two extreme bases
  (T-9) gives **[−28.98, −7.28] / [−24.11, −3.21] / [−18.65, −0.25] %** —
  spans of ~22 / 21 / 18 pp against a bar only 20 pp wide.
* **The direction is against the instrument.** A true P0 clears at P0 prices,
  which are <= the P1 prices this proxy uses, and an LP dispatches less than
  price-taking. Both push the same way: fewer/shorter P0 runs -> a LARGER
  markup -> a COLDER reconstruction. **The true residual therefore sits BELOW
  the numbers above** — 2023 fails harder, and 2024/2025 move toward the
  −10 % edge.
* **The v4 band series is approximated** (T-10): production keys the
  amortization horizon on renewable POTENTIAL, the committed sidecars carry
  only DISPATCHED. The v3/v4 gap is **5.51 / 4.86 / 4.66 pp** — above the 2 pp
  disclosure threshold, so this is a LIVE limitation, not a rounding detail.
  The v3 basis would clear 3 of 3; it is **not** the keeper's basis
  (``tranche_startup_conditional_runs=True``) and must never be substituted to
  buy a pass.
* **L1 under-reproduces heavily-floored classes by construction.** Price-taking
  cannot dispatch an out-of-merit must-run floor, so ``ST_GAS`` (47 % forced,
  D-2) runs **−11.8 / −17.0 / −19.4 %**. For a floored class use **L2**, which
  dispatches floors first.
* **min-run / min-down are ABSENT for MISO CT — verified twice.** All **733**
  ``CT_PEAKER`` tranches carry ``min_run_hours == min_down_hours == 0.0``
  (distinct-value census); the only 51 fleet units with a min-run are
  ``COAL_FAMILY``. So :func:`enforce_min_run` moves CT energy by exactly
  **0.00 pp**, and the ONLY commitment physics reaching MISO's CT is the
  startup amortization this instrument reproduces.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds no marker.

Usage::

    PYTHONPATH=$PWD .venv/bin/python scripts/probes/_miso154_ct_commitment.py
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# T-1: the miso-134 module is HARD-WIRED to miso132_ccmin_B. This session's
# keeper is miso-148, so the bundle is REPOINTED before any helper runs, and
# the repoint is ASSERTED — inheriting miso-132's config would silently screen
# the wrong keeper.
BUNDLE = REPO / "results/calibration/miso148_basis_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE

from _miso134_ct_night_order_screen import (  # noqa: E402
    build_year,
    keeper_config,
    keeper_prices,
)
from market_sim.data.fleet import campd_ct_run_band_ratios  # noqa: E402
from market_sim.model.commitment import (  # noqa: E402
    compute_monthly_markup,
    find_runs,
)

# T-8: the markup MUST be the production function, never a re-implementation —
# a copy would reproduce my own expectation instead of the model's.
if compute_monthly_markup.__module__ != "market_sim.model.commitment":
    raise SystemExit(
        "T-8 FAIL: compute_monthly_markup is not the production symbol "
        f"(module={compute_monthly_markup.__module__})"
    )

OUT = REPO / "results/calibration/_miso154_ct_commitment.json"
YEARS = (2023, 2024, 2025)  # rule 22: the ONLY years touched anywhere below
ISO = "MISO"

# T-5: the six CARRY zones. MISO_external / MISO_external_South are IMPORT
# NODES — excluded from every price/demand aggregate.
CARRY_ZONES = (
    "MISO-East",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-Plains",
    "MISO-South",
    "MISO-West",
)

TOPN = 200  # PREREG §3 Stage 6: the miso-153 window, unchanged
BAR = 0.10  # PREREG §5: the gating bar on |resid|
T6_TOL = 1e-9  # T-6: the 2023 weather_year control tolerance
TARGET = "CT_PEAKER"

# The dispatchable thermal set. COAL is POOLED (miso-153 T-9): the split names
# the coal rank only, and pooling both sides is exactly equivalent for the
# energy totals while removing a fragile mapping.
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC", "COAL")
COAL_POOL = "COAL_FAMILY"

MONTH_LEN = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
             7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MO = np.concatenate([np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)])


# ---------------------------------------------------------------------------
# Stage 1 — assemble
# ---------------------------------------------------------------------------


@dataclass
class YearBasis:
    """One year's assembled fleet, offer basis and keeper reference frames.

    Everything downstream reads THIS — no stage re-derives the fleet, so a
    later session can build the basis once and drive several reconstructions
    off it.
    """

    year: int
    fleet: list
    arrays: object
    mc_base: np.ndarray          # (n_gen, T) P0 base offer
    availcap: np.ndarray         # (n_gen, T) pmax x availability — the LP bound
    labels: np.ndarray           # (n_gen,) class_hourly klass per generator
    zprice: np.ndarray           # (n_gen, T) each generator's own zonal price
    demand: np.ndarray           # (T,) ISO demand
    top: np.ndarray              # (TOPN,) the peak-window hour indices
    class_hourly: pd.DataFrame   # keeper P1 (klass x hour) MW
    run_ratio_t: np.ndarray | None
    n_hours: int


def _class_label(g) -> str:
    """Return the ``class_hourly`` klass for one assembled generator.

    Mirrors ``run_calibration_full._dispatch_frame``: non-ERCOT fleets class by
    ``plant_group``. COAL is pooled to ``COAL_FAMILY``.

    T-2: fields are read DIRECTLY. A silent 3-argument ``getattr`` default on
    the offer path IS the bug — ``FleetArrays`` is ``.pmax`` while
    ``Generator`` is ``.pmax_mw``, and a default would hide the mismatch.
    """
    group = str(g.plant_group or "")
    return COAL_POOL if group == "COAL" else group


def _band_of(unit_id: str) -> str:
    """Return the raw tranche band suffix of a per-plant unit id, or ``""``."""
    m = re.search(r"_p(\d+)_([a-z0-9_]+)$", unit_id)
    return m.group(2) if m else ""


def keeper_class_hourly(year: int) -> pd.DataFrame:
    """Return the keeper's committed P1 ``(klass x hour)`` dispatch MW frame."""
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    wide = ch.pivot_table(index="klass", columns="hour", values="mw",
                          observed=True, aggfunc="sum").fillna(0.0)
    full = pd.DataFrame(0.0, index=wide.index, columns=np.arange(8760))
    full.loc[:, wide.columns] = wide
    present = [c for c in COAL_CLASSES if c in full.index]
    if present:
        pooled = full.loc[present].sum(axis=0)
        full = full.drop(index=present)
        full.loc[COAL_POOL] = pooled
    return full


def _run_ratio_series(ch: pd.DataFrame, demand: np.ndarray) -> np.ndarray | None:
    """Reconstruct the v4 condition-keyed amortization band series.

    ``tranche_startup_conditional_runs`` keys the amortization horizon on the
    hour's within-year net-load percentile band
    (``scripts/run_calibration.py:3977-3991``). Production computes net load
    from renewable POTENTIAL (``cap x cf``); the committed sidecars carry only
    DISPATCHED wind/solar, so this uses
    ``net_load = ISO demand - wind - solar`` off the keeper's own
    ``class_hourly``. Bounded by T-10, which reports the bar under
    ``run_ratio_t = 1.0`` (the v3 basis) as well.

    Returns ``None`` when the ISO carries no committed band artifact — the v4
    flag is then a documented no-op, never a silent hand number (rule 23).
    """
    bands = campd_ct_run_band_ratios(ISO)
    if bands is None:
        return None
    edges, ratios = bands
    vre = np.zeros(demand.shape[0])
    for k in ("wind", "solar"):
        if k in ch.index:
            vre = vre + ch.loc[k].to_numpy()
    net = demand - vre
    pct = (np.argsort(np.argsort(net)) + 1.0) / float(net.shape[0])
    idx = np.searchsorted(np.asarray(edges, dtype=float), pct, side="right")
    return np.asarray(ratios, dtype=float)[idx]


def assemble_year(cfg, year: int) -> YearBasis:
    """Assemble one year's basis through the PRODUCTION chain.

    **T-6 (non-optional).** ``_apply_outage_overlays`` keys the unit-level
    CAMPD outage derate on ``config.weather_year``, NOT on the solve year
    (``data/fleet/arrays.py:1091-1092``), while the production backcast
    pipeline pins ``weather_year = year`` per solve year
    (``pipeline/backcast_config.py:1235``). ``_miso134.build_year`` takes ONE
    config, so passing the keeper's ``weather_year = 2023`` unchanged silently
    applies 2023's outage windows to 2024 and 2025. The per-year pin is the
    repair; 2023 is its own control (its ``weather_year`` already was 2023, so
    it must come out unchanged).
    """
    cfg_y = dataclasses.replace(cfg, weather_year=year)
    _raw, fleet, arrays, _fp, mc_base, _zn = build_year(cfg_y, year)

    price_df, demand = keeper_prices(year)
    carry = [z for z in CARRY_ZONES if z in price_df.columns]
    if len(carry) != 6:
        raise SystemExit(f"T-5 FAIL: expected 6 carry zones, got {carry}")

    n_gen = len(fleet)
    n_hours = int(mc_base.shape[1])

    avail = np.asarray(arrays.availability, dtype=np.float64)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], (n_gen, n_hours))
    availcap = np.asarray(arrays.pmax, dtype=np.float64)[:, None] * avail

    # Each generator's own zonal price. Import-node generators (which carry no
    # assembled capacity — miso-153 §5) get +inf so they can never be in merit.
    zones = np.array([str(g.zone) for g in fleet], dtype=object)
    zprice = np.full((n_gen, n_hours), np.inf)
    for z in carry:
        sel = zones == z
        if sel.any():
            zprice[sel] = price_df[z].to_numpy()[None, :]

    ch = keeper_class_hourly(year)
    top = np.sort(np.argsort(demand)[::-1][:TOPN])

    return YearBasis(
        year=year,
        fleet=fleet,
        arrays=arrays,
        mc_base=mc_base,
        availcap=availcap,
        labels=np.array([_class_label(g) for g in fleet], dtype=object),
        zprice=zprice,
        demand=demand,
        top=top,
        class_hourly=ch,
        run_ratio_t=_run_ratio_series(ch, demand),
        n_hours=n_hours,
    )


# ---------------------------------------------------------------------------
# Stage 2 — the P0 reconstruction (the run-length source)
# ---------------------------------------------------------------------------


def reconstruct_p0(basis: YearBasis, mode: str = "pricetaking") -> np.ndarray:
    """Return an ``(n_gen, T)`` P0 dispatch proxy for the markup's run lengths.

    There is no committed P0 pass (the keeper's ``hourly/`` sidecars carry
    ``pass == "P1"`` only), so the run-length source must be reconstructed.

    Modes — the three T-9 bases that BOUND the proxy error:

    * ``"pricetaking"``: in-merit on ``mc_base`` against the keeper's own P1
      zonal prices. **Declared bias, running AGAINST this session's
      conclusion:** P1 prices are >= P0 prices (P1 adds a non-negative markup
      to every offer), so this OVER-states P0 running -> LONGER runs -> a
      SMALLER markup -> MORE CT admitted -> the reconstruction stays
      HOT-leaning, which makes the bar HARDER to clear.
    * ``"never"``: no P0 runs at all. A month with no run amortizes over the
      measured horizon outright, so this is the MAXIMUM markup.
    * ``"always"``: every unit runs every hour. The monthly run is then the
      whole month, capped by the measured horizon — the markup FLOOR.
    """
    if mode == "pricetaking":
        return np.where(
            (basis.mc_base <= basis.zprice) & (basis.availcap > 1e-6),
            basis.availcap, 0.0,
        )
    if mode == "never":
        return np.zeros_like(basis.availcap)
    if mode == "always":
        return basis.availcap.copy()
    raise ValueError(f"unknown P0 mode: {mode}")


# ---------------------------------------------------------------------------
# Stage 3 — the markup (PRODUCTION function)
# ---------------------------------------------------------------------------


def commitment_markup(basis: YearBasis, p0: np.ndarray, cfg,
                      run_ratio_t: np.ndarray | None = None) -> np.ndarray:
    """Return the ``(n_gen, T)`` P1 startup-amortization markup.

    Delegates to the PRODUCTION ``compute_monthly_markup`` with the keeper's
    own gates, reproducing ``pipeline/solve.py:254-265`` exactly. T-8 asserts
    at import that the symbol is the production one.
    """
    return compute_monthly_markup(
        basis.fleet,
        basis.arrays,
        p0,
        basis.n_hours,
        gas_st_season_spread=cfg.gas_st_startup_spread,
        gas_st_startup_cost=cfg.gas_st_startup_cost,
        chp_startup_covered=cfg.chp_startup_covered,
        coal_warm_committed=cfg.coal_warm_committed,
        run_ratio_t=run_ratio_t,
    )


# ---------------------------------------------------------------------------
# Stage 5 — the P1 reconstructions
# ---------------------------------------------------------------------------


def reconstruct_p1_pricetaking(basis: YearBasis, mc_bid: np.ndarray) -> np.ndarray:
    """**L1** — in-merit on the BID against the keeper's own P1 zonal prices.

    This is miso-153's T-6b with its single mis-specification corrected
    (``mc_bid`` in place of ``mc_base``), so the result is DIRECTLY comparable
    to the published +22.0 / +22.1 / +23.7 %. **L1 is the gating leg.**
    """
    return np.where(
        (mc_bid <= basis.zprice) & (basis.availcap > 1e-6), basis.availcap, 0.0
    )


def enforce_min_run(basis: YearBasis, disp: np.ndarray) -> tuple[np.ndarray, dict]:
    """**T-11** — extend every run to the unit's physical ``min_run_hours``.

    MISO arms no commitment bridge and no P2 pass, so its P1 LP enforces
    neither a minimum run nor a minimum down time; the only place commitment
    physics reaches the P1 objective is the startup amortization. This variant
    exists to MEASURE that: if enforcing a minimum run makes the fit WORSE,
    that is positive evidence the LP does not carry it.

    Returns the extended dispatch and a census of the parameters applied.
    """
    out = disp.copy()
    n_ext = 0
    n_units = 0
    for g, gen in enumerate(basis.fleet):
        mrh = int(gen.min_run_hours)
        if mrh <= 1:
            continue
        n_units += 1
        on = disp[g] > 1e-6
        if not on.any():
            continue
        for start, end in find_runs(on):
            if end - start >= mrh:
                continue
            stop = min(start + mrh, basis.n_hours)
            out[g, start:stop] = basis.availcap[g, start:stop]
            n_ext += 1
    return out, {"units_with_min_run": n_units, "runs_extended": n_ext}


def reconstruct_p1_meritorder(basis: YearBasis, mc_bid: np.ndarray) -> np.ndarray:
    """**L2** — ISO-wide merit-order clearing against the keeper's own total.

    Declared refinement (PREREG §3 Stage 5), reported and **never gating**.

    Min-gen floors dispatch first (``arrays.min_gen``, falling back to
    ``pmin`` broadcast); the remainder of the keeper's OWN hourly thermal
    total is then filled in ascending ``mc_bid``. Conserving the total by
    construction isolates the offer ORDER from the offer LEVEL — it asks only
    "given the MW of thermal the LP dispatched this hour, does merit order on
    the bid put the right share on CT?", which price-taking cannot ask.
    """
    n_gen, n_hours = basis.availcap.shape
    thermal = _thermal_classes(basis)
    tsel = np.isin(basis.labels, thermal)

    mg = basis.arrays.min_gen
    if mg is None:
        floor = np.broadcast_to(
            np.asarray(basis.arrays.pmin, dtype=np.float64)[:, None],
            (n_gen, n_hours),
        )
    else:
        floor = np.asarray(mg, dtype=np.float64)
    floor = np.minimum(floor, basis.availcap) * tsel[:, None]

    target = np.zeros(n_hours)
    for k in thermal:
        if k in basis.class_hourly.index:
            target = target + basis.class_hourly.loc[k].to_numpy()

    out = floor.copy()
    rows = np.where(tsel)[0]
    headroom_all = (basis.availcap - floor)[rows]
    resid_all = target - floor.sum(axis=0)

    for t in range(n_hours):
        resid = resid_all[t]
        if resid <= 1e-6:
            continue
        head = headroom_all[:, t]
        live = head > 1e-6
        if not live.any():
            continue
        idx = rows[live]
        head = head[live]
        order = np.argsort(mc_bid[idx, t], kind="stable")
        idx, head = idx[order], head[order]
        cum = np.cumsum(head)
        n_full = int(np.searchsorted(cum, resid))
        if n_full:
            out[idx[:n_full], t] += head[:n_full]
        if n_full < idx.shape[0]:
            prior = cum[n_full - 1] if n_full else 0.0
            out[idx[n_full], t] += resid - prior
    return out


def _thermal_classes(basis: YearBasis) -> list[str]:
    """Return the assembled classes that participate in the thermal stack."""
    present = set(basis.labels.tolist())
    return [c for c in (*GAS_CLASSES, COAL_POOL) if c in present]


# ---------------------------------------------------------------------------
# Stage 6 — validation
# ---------------------------------------------------------------------------


def class_energy_residual(basis: YearBasis, disp: np.ndarray,
                          klass: str = TARGET) -> dict:
    """Return the reconstruction-vs-keeper energy residual for one class.

    ``resid = (E_recon - E_keeper) / E_keeper`` over the top-200 model-demand
    hours (the gated window) with the annual figure alongside, ungated.
    """
    sel = basis.labels == klass
    keeper = (basis.class_hourly.loc[klass].to_numpy()
              if klass in basis.class_hourly.index else np.zeros(basis.n_hours))
    rec_t = disp[sel].sum(axis=0)

    def _pair(mask_idx) -> dict:
        r = float(rec_t[mask_idx].sum())
        k = float(keeper[mask_idx].sum())
        return {"recon_mwh": r, "keeper_mwh": k,
                "resid": (r - k) / k if k else None}

    top = _pair(basis.top)
    ann = _pair(np.arange(basis.n_hours))
    top["within_bar"] = bool(top["resid"] is not None and abs(top["resid"]) <= BAR)
    return {"top200": top, "annual": ann, "bar": BAR}


def markup_census(basis: YearBasis, markup: np.ndarray,
                  klass: str = TARGET) -> dict:
    """**T-7** — the markup's own magnitude, so an inert instrument can't hide.

    A markup of ~0 at the peak means the instrument changes nothing and the
    exercise is void (PREREG §4 trigger **S-INERT**). Reported with its
    distribution, never as a single number.
    """
    sel = basis.labels == klass
    cap = np.asarray(basis.arrays.pmax, dtype=np.float64)[sel]
    mk = markup[sel][:, basis.top]
    w = cap.sum()
    capwtd = float((mk.mean(axis=1) * cap).sum() / w) if w else 0.0
    flat = mk.reshape(-1)
    return {
        "cap_weighted_mean_per_mwh": capwtd,
        "p10": float(np.percentile(flat, 10)),
        "p50": float(np.percentile(flat, 50)),
        "p90": float(np.percentile(flat, 90)),
        "max": float(flat.max()),
        "share_of_cap_with_zero_markup": float(
            (cap[(mk.max(axis=1) <= 1e-9)].sum() / w) if w else 0.0),
    }


def suffix_inventory(basis: YearBasis) -> dict:
    """**T-3** — the FULL raw band-suffix inventory, per class, un-aggregated.

    The econ block smooths into ``econc00..econc05``; collapsing one-per-band
    keeps only the DEAREST sub-tranche and yields a spurious exact 0.0. Dumped
    so that collapse cannot pass unnoticed.
    """
    df = pd.DataFrame({
        "klass": basis.labels,
        "suffix": [_band_of(str(g.unit_id)) for g in basis.fleet],
        "pmax": np.asarray(basis.arrays.pmax, dtype=np.float64),
    })
    inv = (df.groupby(["klass", "suffix"], observed=True)
             .agg(n=("pmax", "size"), cap_mw=("pmax", "sum")).reset_index())
    return {
        "n_distinct_suffixes": int(df["suffix"].nunique()),
        "distinct_suffixes": sorted(df["suffix"].unique().tolist()),
        "target_class": {
            r.suffix: {"n": int(r.n), "cap_mw": round(float(r.cap_mw), 1)}
            for r in inv[inv.klass == TARGET].itertuples(index=False)
        },
    }


def startup_basis_census(basis: YearBasis, klass: str = TARGET) -> dict:
    """The measured start-recovery inputs behind the markup, per class.

    Identification is from CAMPD unit conduct through the production fleet —
    never from MISO's masked offer book, whose class bridge was built and
    REFUTED at miso-138 (PREREG §2).
    """
    sel = np.where(basis.labels == klass)[0]
    cap = np.asarray(basis.arrays.pmax, dtype=np.float64)[sel]
    su = np.array([float(basis.fleet[i].startup_cost_per_mw) for i in sel])
    rh = np.array([float(basis.fleet[i].fast_start_run_hours) for i in sel])
    mr = np.array([float(basis.fleet[i].min_run_hours) for i in sel])
    w = cap.sum()
    has = (su > 0) & (rh > 0)
    return {
        "n_tranches": int(sel.size),
        "cap_mw": float(w),
        "cap_weighted_startup_per_mw": float((su * cap).sum() / w) if w else 0.0,
        "cap_weighted_measured_run_h": float((rh * cap).sum() / w) if w else 0.0,
        "cap_weighted_min_run_h": float((mr * cap).sum() / w) if w else 0.0,
        "cap_share_with_startup_and_measured_run": float(
            cap[has].sum() / w) if w else 0.0,
        "cap_share_with_startup_no_measured_run": float(
            cap[(su > 0) & (rh <= 0)].sum() / w) if w else 0.0,
    }


# ---------------------------------------------------------------------------
# The driver
# ---------------------------------------------------------------------------


def run_year(cfg, year: int) -> dict:
    """Build the instrument for one year and report every §5/§6 statistic."""
    basis = assemble_year(cfg, year)
    rr = basis.run_ratio_t

    p0 = reconstruct_p0(basis, "pricetaking")
    markup = commitment_markup(basis, p0, cfg, rr)
    mc_bid = basis.mc_base + markup

    # The published miso-153 baseline, recomputed here on the SAME fleet so
    # the correction is measured against a like-for-like number.
    base_l1 = reconstruct_p1_pricetaking(basis, basis.mc_base)
    l1 = reconstruct_p1_pricetaking(basis, mc_bid)
    l2 = reconstruct_p1_meritorder(basis, mc_bid)

    out = {
        "n_gen": len(basis.fleet),
        "top200_demand_gw_mean": float(basis.demand[basis.top].mean() / 1e3),
        "run_ratio_top200_mean": float(rr[basis.top].mean()) if rr is not None
        else None,
        "suffix_inventory_T3": suffix_inventory(basis),
        "startup_basis": startup_basis_census(basis),
        "markup_census_T7": markup_census(basis, markup),
        "BASELINE_pricetaking_mc_base": class_energy_residual(basis, base_l1),
        "L1_pricetaking_mc_bid": class_energy_residual(basis, l1),
        "L2_meritorder": class_energy_residual(basis, l2),
    }

    # T-9: bound the P0-proxy error with the markup's own extreme bases.
    for mode in ("never", "always"):
        mk = commitment_markup(basis, reconstruct_p0(basis, mode), cfg, rr)
        out[f"T9_p0_{mode}"] = {
            "markup": markup_census(basis, mk),
            "L1": class_energy_residual(
                basis, reconstruct_p1_pricetaking(basis, basis.mc_base + mk)),
        }

    # T-10: the v4 band reconstruction vs the v3 basis.
    mk_v3 = commitment_markup(basis, p0, cfg, None)
    out["T10_v3_flat_ratio"] = {
        "markup": markup_census(basis, mk_v3),
        "L1": class_energy_residual(
            basis, reconstruct_p1_pricetaking(basis, basis.mc_base + mk_v3)),
    }

    # T-11: does enforcing a minimum run help or hurt?
    ext, cens = enforce_min_run(basis, l1)
    out["T11_min_run_enforced"] = {
        "census": cens, "L1": class_energy_residual(basis, ext)}

    # Per-class residuals alongside the target, so a CT "fix" that wrecks
    # another class cannot pass unseen.
    out["per_class_L1"] = {
        k: class_energy_residual(basis, l1, k)["top200"]
        for k in _thermal_classes(basis)
    }
    return out


def main() -> None:
    cfg = keeper_config()
    raw = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    names = {f.name for f in dataclasses.fields(cfg)}
    dropped = sorted(set(raw) - names)
    print(f"[T-1] bundle = {BUNDLE.name}  matched={len(set(raw) & names)} "
          f"dropped={len(dropped)}")
    print(f"[T-8] compute_monthly_markup from {compute_monthly_markup.__module__}")

    result = {"bundle": BUNDLE.name, "t1_dropped": dropped,
              "prereg": "PREREG-miso154-ct-commitment-instrument-2026-08-12.md",
              "years": {}}
    for y in YEARS:
        print(f"\n===== {y} =====", flush=True)
        r = run_year(cfg, y)
        result["years"][str(y)] = r
        b = r["BASELINE_pricetaking_mc_base"]["top200"]
        one = r["L1_pricetaking_mc_bid"]["top200"]
        two = r["L2_meritorder"]["top200"]
        mk = r["markup_census_T7"]["cap_weighted_mean_per_mwh"]
        print(f"  n_gen={r['n_gen']}  CT markup ${mk:.2f}/MWh (cap-wtd, top200)")
        print(f"  BASELINE (mc_base) resid {b['resid']*100:+.1f}%")
        print(f"  L1       (mc_bid)  resid {one['resid']*100:+.1f}%  "
              f"{'PASS' if one['within_bar'] else 'FAIL'} (bar +-10%)")
        print(f"  L2       (merit)   resid {two['resid']*100:+.1f}%")

    OUT.write_text(json.dumps(result, indent=2, default=float))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
