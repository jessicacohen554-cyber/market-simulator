"""miso-221 phase 0 — CAN AN AUTHORIZED BAND-MULTIPLIER RESHAPE REACH THE C3c TAIL?

Zero-solve. Rebuilds the designated keeper's OWN fleet and offer basis
(``2026-09-05-miso-220-nonsteam-lift``, bundle ``miso220_nonsteamlift_B``) through
the same chain ``runner.py`` runs — fleet -> bins -> arrays -> resolved delivered
fuel -> ``assemble_mc`` -> coal tranches -> gas offer margin -> anchored spread —
via ``_miso134_ct_night_order_screen.build_year``, then RE-PRICES the object's
hours against candidate ``offer_curve_by_group`` tables at the model's own
dispatched quantity.

**THE GOVERNANCE SCOPE THIS PROBE IS BUILT INSIDE, stated before any number.**
Rule 1 ``[R-STRUCT]``'s 2026-09-05 carve-out condition (a) admits the
``offer_curve_by_group`` band multipliers ``committed`` / ``econ_low`` /
``econ_high`` / ``peak`` and **explicitly excludes the structural shares
``econ_low_share`` and ``pct_peaking``**. The miso-221 charter named the shape
knob as "``peak`` and ``pct_peaking``"; only the first half is on the authorized
channel. Every candidate below therefore moves **band multipliers only** — the
tranche capacity split is never touched — and ``phys_*`` is never touched either.

**THE DECISIVE ARITHMETIC (A-0), and why it is the right one.** In an object hour
the model clears at the offer of the last in-merit tranche (miso-219 measured the
energy dual as the ONLY live price-formation channel there: reserve/ORDC inert,
zonal dispersion $0.06). Re-pricing therefore reduces to a merit-order question:
hold the model's own dispatched quantity ``Q`` fixed at the baseline's in-merit
capacity, re-sort the candidate stack, and read the offer of the ``Q``-th MW.
With the baseline table this reproduces the committed price BY CONSTRUCTION, so
the construction is self-checking; the residual against the committed P1 dual is
reported at full magnitude rather than assumed away. It is a FIRST-ORDER estimate
(dispatch is not re-optimized), and it is deliberately conservative in the arm's
favour: it lets the whole re-priced stack be re-sorted without letting any cheaper
resource elsewhere in the system displace it.

**A-1 THE REACH TEST.** The tail needs marginal offers in the $200-$1,800 range.
The probe reports, per candidate and per hour, the counterfactual price and the
capacity ladder between the committed price and the measured actual — i.e. how
much supply a reshape must move THROUGH, not merely how much it lifts.

**A-2 THE ``CT_PEAKER``-2023 EXPOSURE (F-2).** The keeper's ``CT_PEAKER``-2023 C1
cell sits at -7.985 TWh against a +/-8.00 band: 0.015 TWh of headroom. The probe
computes the pre-solve exposure of every candidate two ways, from the keeper's
OWN committed sidecars: (i) the annual energy each ``CT_PEAKER`` band produces
(``class_band_hourly_<year>.parquet``), which BOUNDS what a band-scoped change can
remove; and (ii) the energy sitting in tranche-hours where the candidate offer
crosses above the keeper's committed zonal price, which is the first-order
displacement estimate.

**A-3 THE MERIT MAP AT THE MARGIN**, including the blocks this channel CANNOT
reach: ``oil``, ``biomass`` and ``ST_CHP`` carry no ``offer_curve_by_group`` entry
(declared at miso-220 PREREG section 3, not discovered here).

Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only. No LP is solved; nothing is minted.

Usage::

    python3 scripts/probes/_miso221_peak_shape_phase0.py
"""

from __future__ import annotations

import dataclasses
import gc
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
_m134.BUNDLE = KEEPER

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402

FAMILY = os.environ.get("MISO221_FAMILY", "shape")
OUT = (
    REPO
    / f"results/calibration/_miso221_peak_shape{'' if FAMILY == 'shape' else '_' + FAMILY}.json"
)
ZONAL_ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
SCORING_HUB = "INDIANA.HUB"
SCORING_ZONE = "MISO-Indiana"
YEARS = tuple(
    int(v) for v in os.environ.get("MISO221_YEARS", "2023,2024,2025").split(",")
)
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
TOP_N = 15
TAIL_USD = 200.0  # the C3c object: measured RT hours above $200/MWh
MONTH_LENS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
EPS = 1e-9

# The four band multipliers rule 1's carve-out (a) admits. Nothing else is a
# candidate axis anywhere in this module.
AUTHORIZED_BANDS: tuple[str, ...] = ("committed", "econ_low", "econ_high", "peak")
FORBIDDEN_KEYS: tuple[str, ...] = ("econ_low_share", "pct_peaking")


def _r(x: float, n: int = 3) -> float | None:
    """Round for the JSON record; ``None`` for a non-finite value."""
    if x is None or not np.isfinite(x):
        return None
    return round(float(x), n)


def _band(unit_id: str) -> str:
    """Collapse a tranche unit_id's suffix to its offer band.

    The econ ramp is emitted as ``econlo``/``econhi`` (flat two-step form) or
    ``econc00``..``econc05`` (the ``offer_curve_smoothing_n`` ramp); both are one
    economic band for merit-ladder reporting. ``?`` marks a row carrying no
    tranche token (renewables, hydro, nuclear, imports, storage proxies).
    """
    m = re.search(r"_p(\d+)_([a-z0-9]+)$", str(unit_id))
    if not m:
        return "?"
    b = m.group(2)
    return "econ" if b.startswith("econ") else b


def _month_of_hour() -> np.ndarray:
    """Calendar month (1-12) per hour on the model's fixed non-leap 8760 clock."""
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)])[
        :HOURS
    ]


def _stamp(h: int) -> str:
    """``'MM-DD HEkk'`` on the model's own 8760 clock (February is always 28 days)."""
    doy, hod = divmod(int(h), 24)
    m, d = 0, doy
    for i, n in enumerate(MONTH_LENS):
        if d < n:
            m = i + 1
            break
        d -= n
    return f"{m:02d}-{d + 1:02d} HE{hod + 1:02d}"


def actual_lmp(year: int) -> np.ndarray:
    """(8760,) measured RT LMP at the C3a scoring hub, on the model's clock."""
    df = pd.read_parquet(ZONAL_ACTUAL)
    sub = df[(df["year"] == year) & (df["hub"] == SCORING_HUB)]
    out = np.full(HOURS, np.nan)
    out[sub["hour"].to_numpy(int)] = sub["rt"].to_numpy(float)
    return out


def object_hours(year: int) -> list[int]:
    """The year's top-15 measured-price Jun-Jul hours (the object's own hours)."""
    act = actual_lmp(year)
    mon = _month_of_hour()
    jj = np.where(((mon == 6) | (mon == 7)) & np.isfinite(act))[0]
    return sorted(int(h) for h in jj[np.argsort(act[jj])[::-1]][:TOP_N])


def keeper_zone_price(year: int) -> np.ndarray:
    """(8760,) committed P1 clearing price at the C3a scoring zone."""
    sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    p = sysf.pivot_table(index="hour", columns="zone", values="price", aggfunc="first")
    return p[SCORING_ZONE].to_numpy(float)


def keeper_band_energy(year: int, klass: str) -> dict:
    """Annual P1 energy (TWh) per offer band for one reporting class.

    Read from the keeper's committed ``class_band_hourly`` sidecar, so this is
    the keeper's own dispatch — not a reconstruction. It BOUNDS what any
    band-scoped multiplier change can remove from the class.
    """
    f = KEEPER / f"hourly/class_band_hourly_{year}.parquet"
    d = pd.read_parquet(f)
    d = d[(d["pass"] == "P1") & (d["klass"] == klass)]
    if d.empty:
        return {}
    d = d.assign(
        band=d["band"].astype(str).map(lambda b: "econ" if b.startswith("econ") else b)
    )
    g = d.groupby("band", observed=True)["mw"].sum() / 1e6  # MWh -> TWh (1 h steps)
    return {str(k): _r(float(v), 4) for k, v in g.sort_values(ascending=False).items()}


# --------------------------------------------------------------------------
# The keeper's own resolved table, read from its committed run_config. miso-220
# wrote the FULL explicit table into the keeper, so no recovery arithmetic is
# needed here (the S-1 identity miso-220 had to prove is now trivially held) —
# but it is asserted rather than assumed.
# --------------------------------------------------------------------------
def keeper_table() -> dict[str, dict[str, float]]:
    """The keeper's own ``offer_curve_by_group``, verbatim from ``run_config.json``."""
    raw = json.loads((KEEPER / "run_config.json").read_text())
    tab = raw["scenario_config"]["offer_curve_by_group"]
    assert tab and "CT_PEAKER" in tab, "keeper carries no explicit CT_PEAKER offer row"
    return {k: dict(v) for k, v in tab.items()}


def candidates() -> dict[str, dict]:
    """Candidate reshapes, all on the authorized band-multiplier channel only.

    Two families, both keeping every structural share and every ``phys_*`` key
    byte-identical to the keeper:

    * ``peakN`` — the ``peak`` multiplier on ``CT_PEAKER`` alone (keeper 4.4).
      A pure top-of-stack lever: it moves the class's 7 % peaking tranche and
      NOTHING else, so its ``CT_PEAKER`` energy exposure is bounded by that
      tranche's own dispatch (A-2).
    * ``spreadD`` — a MEAN-PRESERVING econ spread on ``CT_PEAKER``:
      ``econ_low = 1.10 - d``, ``econ_high = 1.10 + d``. The keeper has
      ``econ_low == econ_high == 1.10``, which fails ``pk_m > lo_m`` in
      ``assembly.py`` and so BYPASSES the armed ``offer_curve_smoothing_n = 6``
      ramp: the class that holds the margin in 24 of 45 object hours is the one
      fossil class whose economic block is FLAT by construction. Arming the ramp
      with a symmetric spread is mean-preserving in heat-rate-multiplier space
      (the ramp's 6 equal slices have midpoints averaging exactly 0.5, so the
      capacity-weighted multiplier is ``(lo + pk)/2 = 1.10``), so it is a pure
      SHAPE move with no level component.

    The four candidates are a COARSE REACH CENSUS, not a sweep. They answer a
    feasibility question — is the tail reachable AT ALL on this channel — and
    they are deliberately placed at and beyond the edge of the admissible range
    (``spread0.88`` drives ``econ_low`` to 0.22, a 78 % discount to the class's
    own base heat rate; ``peak20`` is 4.5x the keeper's) so that a NEGATIVE
    result is decisive rather than a matter of not having pushed hard enough.
    No LP is solved for any of them, none is promoted here, and none is scored
    against a criterion — rule 1 condition (c) forbids selecting a multiplier by
    which one makes a gate pass, and nothing below is gated on a residual.
    """
    base = keeper_table()
    out: dict[str, dict] = {"baseline": base}
    if FAMILY == "level":
        # THE TRADE-OFF FRONTIER. The shape census (FAMILY="shape") measured
        # that `CT_PEAKER|econ` IS the dominant block above the clearing price
        # (49.9 / 46.6 / 27.6 % of it) — so the channel reaches the right
        # capacity — yet neither a `peak` lift nor a mean-preserving econ spread
        # moves the price, because the first touches only 4.6-12.6 % of the
        # block and the second leaves its cap-weighted level unchanged. What is
        # left is a pure LEVEL lift on that block, which is the ONLY form with
        # first-order reach. This family measures its price reach against its
        # `CT_PEAKER` energy cost at the same value, so the two constraints are
        # read off ONE curve. It is not a search for a value that passes a gate
        # (rule 1 condition (c)); no candidate here is proposed for a solve, and
        # the frontier is reported whichever way it comes out.
        for L in (1.5, 2.5, 5.0):
            t = {k: dict(v) for k, v in base.items()}
            for b in ("committed", "econ_low", "econ_high", "peak"):
                t["CT_PEAKER"][b] = round(base["CT_PEAKER"][b] * L, 6)
            out[f"level{L:g}"] = t
        return _assert_scope(out, base)
    for pk in (20.0,):
        t = {k: dict(v) for k, v in base.items()}
        t["CT_PEAKER"]["peak"] = pk
        out[f"peak{pk:g}"] = t
    for d in (0.44, 0.88):
        t = {k: dict(v) for k, v in base.items()}
        t["CT_PEAKER"]["econ_low"] = round(1.10 - d, 6)
        t["CT_PEAKER"]["econ_high"] = round(1.10 + d, 6)
        out[f"spread{d:g}"] = t
    # one combined arm: the widest mean-preserving spread with a lifted top
    t = {k: dict(v) for k, v in base.items()}
    t["CT_PEAKER"]["econ_low"] = round(1.10 - 0.44, 6)
    t["CT_PEAKER"]["econ_high"] = round(1.10 + 0.44, 6)
    t["CT_PEAKER"]["peak"] = 12.0
    out["spread0.44+peak12"] = t
    return _assert_scope(out, base)


def _assert_scope(out: dict[str, dict], base: dict[str, dict]) -> dict[str, dict]:
    """Assert every candidate moves ONLY the four authorized band multipliers."""
    for name, tab in out.items():
        for k, row in tab.items():
            for key, val in base[k].items():
                if key in AUTHORIZED_BANDS:
                    continue
                assert row[key] == val, (
                    f"{name}/{k}/{key} moved off the authorized channel"
                )
            for key in FORBIDDEN_KEYS:
                if key in base[k]:
                    assert row[key] == base[k][key], (
                        f"{name}/{k}/{key} is a structural share"
                    )
    return out


def _stack(cfg_table, year):
    """Build the fleet with ``cfg_table`` and return (mc, klass, band, zone, pmax, avail)."""
    cfg = dataclasses.replace(keeper_config(), offer_curve_by_group=cfg_table)
    _, fleet, arrays, _, mc, _ = build_year(cfg, year)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    band = np.array([_band(g.unit_id) for g in fleet])
    zone = np.array([str(g.zone) for g in fleet])
    pmax = np.asarray(arrays.pmax, float)
    avail = np.asarray(arrays.availability, float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    return mc, klass, band, zone, pmax, avail


def _reprice(mc_h: np.ndarray, cap_h: np.ndarray, q: float) -> tuple[float, int]:
    """Offer of the ``q``-th MW in a merit-ordered stack, and its row index.

    The counterfactual clearing price at a FIXED dispatched quantity: sort the
    available tranches by offer, walk the cumulative capacity to ``q``, return
    the offer there. With the baseline stack and ``q`` = the baseline's in-merit
    capacity this returns the committed price by construction.
    """
    order = np.argsort(mc_h, kind="stable")
    cum = np.cumsum(cap_h[order])
    j = int(np.searchsorted(cum, q - 1e-6))
    j = min(j, order.size - 1)
    return float(mc_h[order[j]]), int(order[j])


def analyse_year(year: int, cands: dict[str, dict]) -> dict:
    """Re-price the object's hours under every candidate; measure reach and exposure."""
    hrs = object_hours(year)
    act = actual_lmp(year)
    zprice = keeper_zone_price(year)

    # --- baseline stack: fixes Q per hour and the self-check residual
    mc0, klass, band, zone, pmax, avail = _stack(cands["baseline"], year)
    ct0, pm0, av0 = (klass == "CT_PEAKER"), pmax, avail
    base_rows, q_of, ladder_of = [], {}, {}
    for h in hrs:
        cap_h = pmax * avail[:, h]
        live = cap_h > 1.0
        mc_h = np.where(live, mc0[:, h], np.inf)
        p = float(zprice[h])
        inm = live & (mc0[:, h] <= p + EPS)
        q = float(cap_h[inm].sum())
        q_of[h] = q
        pr, mi = _reprice(mc_h, np.where(live, cap_h, 0.0), q)
        a = float(act[h])
        base_rows.append(
            {
                "hour": int(h),
                "stamp": _stamp(h),
                "hod": int(h % 24),
                "committed_price_usd": _r(p, 2),
                "actual_rt_usd": _r(a, 2),
                "gap_usd": _r(a - p, 2),
                "dispatched_q_mw": _r(q, 0),
                "reprice_selfcheck_usd": _r(pr, 2),
                "reprice_selfcheck_residual_usd": _r(pr - p, 4),
                "marginal_klass": str(klass[mi]),
                "marginal_band": str(band[mi]),
                "marginal_zone": str(zone[mi]),
                # the block a reshape must move THROUGH, not merely lift
                "cap_between_price_and_200_mw": _r(
                    float(
                        cap_h[
                            live & (mc0[:, h] > p + EPS) & (mc0[:, h] <= TAIL_USD)
                        ].sum()
                    ),
                    0,
                ),
                "cap_between_200_and_actual_mw": _r(
                    float(
                        cap_h[live & (mc0[:, h] > TAIL_USD) & (mc0[:, h] <= a)].sum()
                    ),
                    0,
                ),
                "cap_above_actual_mw": _r(
                    float(cap_h[live & (mc0[:, h] > a)].sum()), 0
                ),
                "cap_above_price_mw": _r(
                    float(cap_h[live & (mc0[:, h] > p + EPS)].sum()), 0
                ),
            }
        )
        # per-hour class|band ladder of what sits above the clearing price
        lad = {}
        for k in sorted(set(klass[live])):
            for b in sorted(set(band[live & (klass == k)])):
                s2 = live & (klass == k) & (band == b)
                if not s2.any():
                    continue
                above = s2 & (mc0[:, h] > p + EPS)
                lad[f"{k}|{b}"] = {
                    "cap_mw": _r(float(cap_h[s2].sum()), 0),
                    "cap_w_mc_usd": _r(
                        float(
                            (mc0[s2, h] * cap_h[s2]).sum() / max(cap_h[s2].sum(), EPS)
                        ),
                        2,
                    ),
                    "min_mc_usd": _r(float(mc0[s2, h].min()), 2),
                    "max_mc_usd": _r(float(mc0[s2, h].max()), 2),
                    "cap_above_price_mw": _r(float(cap_h[above].sum()), 0),
                }
        ladder_of[str(h)] = lad

    # --- A-2 exposure baseline: the keeper's own CT_PEAKER band energy
    ct_band_twh = keeper_band_energy(year, "CT_PEAKER")

    # --- every candidate, re-priced at the same Q
    cand_out = {}
    for name, tab in cands.items():
        if name == "baseline":
            continue
        mcC, klC, bdC, _, pmC, avC = _stack(tab, year)
        rows, n_tail = [], 0
        for i, h in enumerate(hrs):
            cap_h = pmC * avC[:, h]
            live = cap_h > 1.0
            mc_h = np.where(live, mcC[:, h], np.inf)
            pr, mi = _reprice(mc_h, np.where(live, cap_h, 0.0), q_of[h])
            n_tail += int(pr > TAIL_USD)
            rows.append(
                {
                    "hour": int(h),
                    "stamp": _stamp(h),
                    "baseline_price_usd": base_rows[i]["committed_price_usd"],
                    "candidate_price_usd": _r(pr, 2),
                    "actual_rt_usd": base_rows[i]["actual_rt_usd"],
                    "delta_usd": _r(pr - float(base_rows[i]["committed_price_usd"]), 2),
                    "marginal_klass": str(klC[mi]),
                    "marginal_band": str(bdC[mi]),
                }
            )
        # A-2: first-order CT_PEAKER displacement over the WHOLE year — tranche-hours
        # whose candidate offer crosses above the keeper's committed price while the
        # baseline offer sat below it. Energy is bounded by pmax*avail at those hours.
        ct = klC == "CT_PEAKER"
        crossed_twh, ct_hours = 0.0, 0
        if ct.any():
            # The spread candidates ARM the offer_curve_smoothing_n ramp, so the
            # CT_PEAKER econ block goes from 2 flat steps to 6 sliced ones and the
            # tranche COUNT changes. A per-row mask is therefore not comparable
            # across arms; the class-level in-merit CAPACITY per hour is. The
            # exposure is the annual energy difference between the CT capacity the
            # keeper's committed dual admits under the baseline stack and under the
            # candidate's — a first-order displacement estimate at fixed price.
            ok = np.isfinite(zprice)
            inm0 = (mc0[ct0, :] <= zprice[None, :] + EPS) & ok[None, :]
            inmC = (mcC[ct, :] <= zprice[None, :] + EPS) & ok[None, :]
            mw0 = ((pm0[ct0, None] * av0[ct0, :]) * inm0).sum(axis=0)
            mwC = ((pmC[ct, None] * avC[ct, :]) * inmC).sum(axis=0)
            crossed_twh = float((mw0 - mwC).sum() / 1e6)
            ct_hours = int(np.count_nonzero(np.abs(mw0 - mwC) > 1.0))
        cw_by_band = {}
        for b in sorted(set(bdC[ct])):
            s = ct & (bdC == b)
            cw_by_band[str(b)] = {
                "cap_mw": _r(float(pmC[s].sum()), 0),
                "cap_w_mc_usd": _r(
                    float(
                        (mcC[s].mean(axis=1) * pmC[s]).sum()
                        / max(float(pmC[s].sum()), EPS)
                    ),
                    2,
                ),
            }
        cand_out[name] = {
            "CT_PEAKER_row": {k: v for k, v in tab["CT_PEAKER"].items()},
            "object_hours": rows,
            "n_object_hours_above_200": n_tail,
            "mean_price_delta_usd": _r(
                float(np.mean([r["delta_usd"] for r in rows])), 2
            ),
            "max_candidate_price_usd": _r(
                float(np.max([r["candidate_price_usd"] for r in rows])), 2
            ),
            "A2_ct_peaker_exposure": {
                "displaced_twh_first_order": _r(crossed_twh, 4),
                "hours_with_any_crossing": ct_hours,
                "note": "annual CT_PEAKER capacity-hours admitted below the keeper's own "
                "committed dual, baseline MINUS candidate; positive = the reshape "
                "removes class energy. First-order (price held at the keeper's).",
            },
            "CT_PEAKER_band_offers": cw_by_band,
        }
        del mcC, klC, bdC, pmC, avC
        gc.collect()

    out = {
        "year": year,
        "n_tranches": int(klass.size),
        "object_hours": hrs,
        "baseline": {
            "rows": base_rows,
            "max_reprice_selfcheck_residual_usd": _r(
                float(
                    np.max(
                        [abs(r["reprice_selfcheck_residual_usd"]) for r in base_rows]
                    )
                ),
                4,
            ),
            "CT_PEAKER_band_energy_twh_committed": ct_band_twh,
            "ladders": ladder_of,
        },
        "candidates": cand_out,
    }
    del mc0, klass, band, zone, pmax, avail
    gc.collect()
    return out


def nontranche_decomposition(year: int) -> dict:
    """What the NON-TRANCHE block above the clearing price actually is, by fuel.

    The ladder reports every row carrying no ``_p<code>_<band>`` token as one
    ``|?`` bucket, which is the whole non-thermal-tranche fleet — wind, nuclear,
    solar, imports, hydro, biomass, oil. That bucket is 12.9 / 16.6 / 35.7 % of
    the capacity sitting ABOVE the keeper's clearing price at the object's hours
    and is unreachable by ``offer_curve_by_group``, so what it is MADE OF decides
    whether "unreachable" is a footnote or the finding. This resolves it by
    ``fuel_type`` over the same 15 hours.

    Returns ``{fuel: {"mw": mean MW above price, "cap_w_offer_usd": ...}}``.
    """
    mc, klass, band, _zone, pmax, avail = _stack(keeper_table(), year)
    cfg = dataclasses.replace(keeper_config(), offer_curve_by_group=keeper_table())
    _, fleet, _arrays, _, _, _ = build_year(cfg, year)
    fuel = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])
    zp, hrs = keeper_zone_price(year), object_hours(year)
    nont = band == "?"
    mw: dict[str, float] = {}
    wsum: dict[str, float] = {}
    for h in hrs:
        cap = pmax * avail[:, h]
        above = (cap > 1.0) & nont & (mc[:, h] > zp[h] + EPS)
        for f in sorted(set(fuel[above])):
            sel = above & (fuel == f)
            mw[f] = mw.get(f, 0.0) + float(cap[sel].sum())
            wsum[f] = wsum.get(f, 0.0) + float((mc[sel, h] * cap[sel]).sum())
    n = len(hrs)
    return {
        f: {"mw": _r(v / n, 0), "cap_w_offer_usd": _r(wsum[f] / max(v, EPS), 2)}
        for f, v in sorted(mw.items(), key=lambda kv: -kv[1])
    }


def _keeper_reference() -> dict:
    """The keeper's own C3c baseline and CT_PEAKER C1 cells, from committed artifacts.

    Read once into the merged record so the finding's headline numbers and the
    probe's arithmetic cite ONE artifact. ``model_hours_above_200`` is counted
    from the keeper's committed P1 duals at the C3a scoring zone; the C1 cells
    are the keeper's own scored ``calibration_verdict --json`` values.
    """
    hrs, mx = {}, {}
    for y in (2023, 2024, 2025):
        p = keeper_zone_price(y)
        hrs[str(y)] = int(np.count_nonzero(p > TAIL_USD))
        mx[str(y)] = _r(float(np.nanmax(p)), 2)
    return {
        "model_hours_above_200": hrs,
        "model_max_price_usd": mx,
        "actual_hours_above_200": {
            str(y): int(np.count_nonzero(actual_lmp(y) > TAIL_USD))
            for y in (2023, 2024, 2025)
        },
        "source": "keeper hourly/system_<year>.parquet P1 at the C3a scoring zone",
    }


def merge(paths: "list[Path]", out: Path) -> None:
    """Merge per-family phase-0 records into the one canonical artifact.

    The probe is run once per (family, year) so the six builds can go in
    parallel — a single sequential process is ~50 min, three parallel
    single-year processes are ~12. The families land in ``by_year`` (shape) and
    ``by_year_level`` (level). Recipe recorded in the finding.
    """
    rec: dict = {"by_year": {}, "by_year_level": {}}
    for f in paths:
        d = json.loads(Path(f).read_text())
        key = (
            "by_year"
            if d.get("candidate_family", "shape") == "shape"
            else "by_year_level"
        )
        for y, v in d["by_year"].items():
            rec[key][y] = v
        rec.setdefault("authorized_channel", d.get("authorized_channel"))
    rec["keeper_reference"] = _keeper_reference()
    Path(out).write_text(json.dumps(rec, indent=2))


def main() -> int:
    """Run every requested year and write the phase-0 record."""
    cands = candidates()
    rec = {
        "probe": "miso-221 phase 0 - can an authorized band-multiplier reshape reach the C3c tail?",
        "keeper": "2026-09-05-miso-220-nonsteam-lift",
        "bundle": str(KEEPER.relative_to(REPO)),
        "solved": False,
        "authorized_channel": {
            "rule": "CLAUDE.md rule 1 [R-STRUCT] carve-out 2026-09-05, condition (a)",
            "bands_admitted": list(AUTHORIZED_BANDS),
            "excluded": list(FORBIDDEN_KEYS) + ["phys_*"],
            "charter_correction": (
                "the miso-221 charter named the shape knob as 'peak and pct_peaking'; "
                "pct_peaking is a STRUCTURAL SHARE and is excluded by condition (a), so "
                "every candidate here moves band multipliers only"
            ),
        },
        "candidate_family": FAMILY,
        "tail_threshold_usd": TAIL_USD,
        "by_year": {},
    }
    for y in YEARS:
        rec["by_year"][str(y)] = analyse_year(y, cands)
        print(f"  {y} done", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
