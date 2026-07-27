"""caiso-129 / S1 derive-first gates D1-D4 for the DISCHARGE-side DA allocation.

The owner-granted S1 ask (docs/handoffs/caiso-127-storage-arbitrage-ask-2026-
07-27.md §4-§5): arm the two-sided rule-19 ``[R-ONE-MECH]`` reconciliation of
M1 (``caiso_charge_allocation_schedule``) by extending its per-day
Fourier-Motzkin allocation floor from the ``Chg`` columns to the ``Dis``
columns. The grant is conditional on these gates, run IN ORDER, with **no LP
solved**:

* **D1** — derive ``alloc_share_dis[hod]`` / ``da_frac_dis`` from the
  committed CAISO Daily Energy Storage Report LESR ``EN`` rows (the same
  source and clock convention as the charge side: ``scripts/data/
  derive_caiso_charge_allocation.py``, ``_caiso102_charge_channels``).
  Reported here from the raw statistic, before the ``SUPPORT_MIN_SHARE``
  support rule, so the gate sees the measurement and not the artifact.
* **D2** — STABILITY (the caiso-106/107 gate): pairwise cross-year Pearson
  ``r >= 0.99`` on ``alloc_share_dis`` and per-hod ``CV <= 0.20`` across the
  2x fleet growth. A shape that is not fleet-invariant is a year-specific
  outcome, not a conduct statistic — **kill**.
* **D3** — BINDING PRE-CHECK, and it is a **HARD KILL BEFORE SOLVE** (the
  caiso-74 lesson: that session spent a full A/B on a mechanism the
  arithmetic had already refuted). Against the keeper's OWN committed hourly
  discharge surface (``results/calibration/caiso126_rorsplit_B/hourly/
  storage_<year>.parquet``, ``tech == "li_ion"``, pass P1 — never a replay,
  this is a storage question), compute the floor the derived shape would
  impose and confirm it BINDS: the implied evening floor must exceed the
  keeper's own evening discharge on a material share of days, and the
  residual overnight allowance must sit BELOW the keeper's measured overnight
  over-discharge. Ex-ante slack ⇒ the family is dead, no LP is solved.
* **D4** — confirm the mechanism cannot pin the LEVEL: the day total stays
  the LP's own and ``1 - da_frac_dis`` of it stays free.

No LP is built or solved anywhere in this probe; every number is a statistic
of a committed raw source or of the committed keeper bundle.

Usage:
  python scripts/probes/_caiso129_s1_gates.py [--cache <parquet>]
``--cache`` points at a pre-parsed concat of the storage-report
``market_output`` sheets (the ``derive_caiso_charge_allocation.py --cache``
convention); without it the xlsx are parsed (~5 min).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from derive_caiso_charge_allocation import (  # noqa: E402
    SUPPORT_MIN_SHARE,
    hourly_pivot,
    load_market_output,
)

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results" / "calibration" / "caiso126_rorsplit_B"
# The caiso-125/127 window convention (hod, model clock).
OVERNIGHT = list(range(0, 7))  # hod 0-6
EVENING = list(range(17, 22))  # hod 17-21
# D2 gates (the ask §5, the caiso-106/107 discipline).
D2_MIN_R = 0.99
D2_MAX_CV = 0.20
# D3: a floor counts as binding in an hour when it exceeds the keeper's own
# discharge by more than this (MWh in the hour) — pure numerical noise guard.
BIND_TOL_MWH = 1.0
# D3: the keeper's measured battery-only overnight over-discharge, FINDING-
# caiso127 §3 (model li_ion vs measured EIA-930 NG:OTH), MW.
KEEPER_OVERNIGHT_EXCESS_MW = {2023: 151.0, 2024: 99.0, 2025: 98.0}


def keeper_dis_grid(year: int) -> np.ndarray:
    """(365, 24) keeper P1 li_ion discharge MW from the committed sidecar.

    Read from the keeper's own ``hourly/storage_<year>.parquet`` (the
    per-tech sidecar added at caiso-127 and verified byte-faithful against
    the committed bundle) — never a replay: this is a storage question and
    the sidecar is the keeper's own output.
    """
    path = KEEPER / "hourly" / f"storage_{year}.parquet"
    d = pd.read_parquet(path)
    d = d[(d["tech"] == "li_ion") & (d["pass"] == "P1")].sort_values("hour")
    v = d["discharge_mw"].to_numpy(dtype=float)
    if v.size != 8760:
        raise ValueError(f"{path}: expected 8760 li_ion P1 hours, got {v.size}")
    return v.reshape(365, 24)


def side_stats(
    ifm: np.ndarray, rtd: np.ndarray, hod: np.ndarray
) -> tuple[np.ndarray, float]:
    """``(alloc_share[24], da_frac)`` for one side of the LESR ``EN`` rows.

    The EXACT statistic ``scripts/data/derive_caiso_charge_allocation.py``
    computes for the charge side, lifted here so the discharge side is
    measured by an identical code path (and so the live rule-23 derive is not
    modified for a candidate that these gates may kill). ``ifm``/``rtd`` are
    the year's per-slot non-negative MW of the side being measured (charge =
    ``clip(-EN, 0)``, discharge = ``clip(+EN, 0)``) and ``hod`` their
    hour-of-day:

    * ``alloc_share[h]`` = (annual IFM volume in hod ``h``) / (annual IFM
      volume), after the :data:`SUPPORT_MIN_SHARE` support rule and
      renormalization, so ``Σ_hod = 1``;
    * ``da_frac`` = ``Σ min(ifm, rtd) / Σ rtd`` — the DA-scheduled share of
      realized volume (the bounded free RT-margin slice is ``1 - da_frac``).
    """
    ann_ifm = float(ifm.sum())
    if ann_ifm <= 0.0 or rtd.sum() <= 0.0:
        raise ValueError("zero annual volume on this side")
    da_frac = float(np.minimum(ifm, rtd).sum() / rtd.sum())
    share = np.array([ifm[hod == h].sum() / ann_ifm for h in range(24)])
    assert abs(share.sum() - 1.0) < 1e-9
    share[share < SUPPORT_MIN_SHARE] = 0.0
    return share / share.sum(), da_frac


def _report_stability(label: str, shapes: dict[int, np.ndarray]) -> tuple[float, float]:
    """Print and return ``(min pairwise r, max gated per-hod CV)`` for a shape."""
    ys = list(shapes)
    rs = []
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            rs.append(float(np.corrcoef(shapes[ys[i]], shapes[ys[j]])[0, 1]))
    arr = np.stack([shapes[y] for y in ys])
    with np.errstate(divide="ignore", invalid="ignore"):
        cv = np.where(arr.mean(0) > 1e-4, arr.std(0) / arr.mean(0), np.nan)
    # Gate only hods carrying material measured allocation — a CV on a ~0
    # entry is measurement dust (the SUPPORT_MIN_SHARE rationale). Written
    # relative to the profile's own total so the same threshold applies to
    # the share basis (total 1) and the fleet-normalized rate basis alike.
    gated = arr.mean(0) >= SUPPORT_MIN_SHARE * arr.mean(0).sum()
    cv_max = float(np.nanmax(cv[gated])) if gated.any() else float("nan")
    print(
        f"  {label:28s}: min r {min(rs):.4f} "
        f"({'/'.join(f'{r:.4f}' for r in rs)}) | max gated CV {cv_max:.3f} "
        f"over {int(gated.sum())} hods"
    )
    return min(rs), cv_max


def main() -> int:
    cache = None
    args = sys.argv[1:]
    if "--cache" in args:
        cache = Path(args[args.index("--cache") + 1])

    p = hourly_pivot(load_market_output(cache))
    p["TRADE_DATE"] = pd.to_datetime(p["TRADE_DATE"])

    # ---------------- D1 -------------------------------------------------
    print("=" * 78)
    print("D1 — measured discharge-side DA allocation (LESR EN, IFM/RTD)")
    print("=" * 78)
    raw_share: dict[int, np.ndarray] = {}
    sup_share: dict[int, np.ndarray] = {}
    da_fracs: dict[int, float] = {}
    for year in YEARS:
        py = p[p.TRADE_DATE.dt.year == year]
        en_ifm = np.nan_to_num(py["IFM_EN"].to_numpy(dtype=float))
        en_rtd = np.nan_to_num(py["RTD_EN"].to_numpy(dtype=float))
        hod = py["hod"].to_numpy(dtype=int)
        dis_ifm = np.clip(en_ifm, 0.0, None)
        dis_rtd = np.clip(en_rtd, 0.0, None)
        # Raw (pre-support-rule) hod share — what D2 is gated on.
        ann = dis_ifm.sum()
        rs = np.array([dis_ifm[hod == h].sum() / ann for h in range(24)])
        raw_share[year] = rs
        share_dis, da_frac_dis = side_stats(dis_ifm, dis_rtd, hod)
        sup_share[year] = share_dis
        da_fracs[year] = da_frac_dis
        print(
            f"\n{year}: da_frac_dis {da_frac_dis:.4f} | annual IFM dis "
            f"{ann / 1e6:.3f} TWh, RTD dis {dis_rtd.sum() / 1e6:.3f} TWh"
        )
        print(
            "  raw share : "
            + " ".join(f"{v:.3f}" for v in rs)
            + f"  (Σ {rs.sum():.3f})"
        )
        print(
            "  support   : "
            + " ".join(f"{v:.3f}" for v in share_dis)
            + f"  (active {int((share_dis > 0).sum())} hods, "
            f"min-share rule {SUPPORT_MIN_SHARE})"
        )
        print(
            f"  windows   : overnight(0-6) {rs[OVERNIGHT].sum():.3f} | "
            f"belly(10-14) {rs[10:15].sum():.3f} | "
            f"evening(17-21) {rs[EVENING].sum():.3f}"
        )

    # ---------------- D2 CONTROL -----------------------------------------
    # The charge side, measured by the IDENTICAL code path, is the control
    # that decides whether a discharge-side stability failure is a real
    # property of the measurement or an artifact of this probe's basis. Two
    # bases are reported for both sides because the two documented numbers
    # live on different ones: FINDING-caiso103 §1A's "r >= 0.994" is the
    # FLEET-NORMALIZED mean rate profile (_caiso103_alloc_stats statistic
    # (A)); the ask §5 names ``alloc_share_dis`` (the hod share of the annual
    # IFM volume). A gate that fires on one basis and not the other would be
    # a basis artifact; one that fires on both is the measurement.
    print("\n" + "=" * 78)
    print("D2 CONTROL — the CHARGE side through the identical code path")
    print("=" * 78)
    chg_raw: dict[int, np.ndarray] = {}
    for year in YEARS:
        py = p[p.TRADE_DATE.dt.year == year]
        en_ifm = np.nan_to_num(py["IFM_EN"].to_numpy(dtype=float))
        hod = py["hod"].to_numpy(dtype=int)
        c = np.clip(-en_ifm, 0.0, None)
        chg_raw[year] = np.array([c[hod == h].sum() / c.sum() for h in range(24)])
    _report_stability("charge alloc_share", chg_raw)
    _report_stability("discharge alloc_share_dis", raw_share)
    # The fleet-normalized rate basis — the basis FINDING-caiso103 §1A's
    # r >= 0.994 was actually measured on (_caiso103_alloc_stats statistic A:
    # mean across days of the hod's IFM MW / that month's EIA-860 battery
    # fleet MW, PS excluded — the caiso-99 envelope denominator).
    sys.path.insert(0, str(REPO / "scripts" / "probes"))
    from _caiso103_alloc_stats import monthly_fleet  # noqa: E402

    chg_rate: dict[int, np.ndarray] = {}
    dis_rate: dict[int, np.ndarray] = {}
    for year in YEARS:
        py = p[p.TRADE_DATE.dt.year == year].copy()
        days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        days = days[(days.month != 2) | (days.day != 29)]
        idx = pd.MultiIndex.from_product([days, range(24)], names=["TRADE_DATE", "hod"])
        pf = py.set_index(["TRADE_DATE", "hod"]).reindex(idx).fillna(0.0).reset_index()
        en = pf["IFM_EN"].to_numpy(dtype=float).reshape(len(days), 24)
        mw, _mwh = monthly_fleet(year)
        fleet_d = mw[np.array([d.month - 1 for d in days])][:, None]
        chg_rate[year] = (np.clip(-en, 0.0, None) / fleet_d).mean(axis=0)
        dis_rate[year] = (np.clip(en, 0.0, None) / fleet_d).mean(axis=0)
    _report_stability("charge fleet-norm rate", chg_rate)
    _report_stability("discharge fleet-norm rate", dis_rate)

    # ---------------- D2 -------------------------------------------------
    print("\n" + "=" * 78)
    print(
        f"D2 — stability (gates: pairwise r >= {D2_MIN_R}, per-hod CV <= {D2_MAX_CV})"
    )
    print("=" * 78)
    ys = list(YEARS)
    rs_all = []
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            r = float(np.corrcoef(raw_share[ys[i]], raw_share[ys[j]])[0, 1])
            rs_all.append(r)
            print(f"  r({ys[i]},{ys[j]}) = {r:.4f}")
    arr = np.stack([raw_share[y] for y in ys])
    with np.errstate(divide="ignore", invalid="ignore"):
        cv = np.where(arr.mean(0) > 1e-4, arr.std(0) / arr.mean(0), np.nan)
    print(
        "  per-hod CV : " + " ".join(f"{v:.2f}" if np.isfinite(v) else "--" for v in cv)
    )
    # Only hods that carry material measured allocation are gated — a CV on a
    # ~0 share is measurement dust, not instability (the same rationale as the
    # SUPPORT_MIN_SHARE rule).
    gated = arr.mean(0) >= SUPPORT_MIN_SHARE
    cv_max = float(np.nanmax(cv[gated])) if gated.any() else float("nan")
    r_min = min(rs_all)
    d2_pass = (r_min >= D2_MIN_R) and (cv_max <= D2_MAX_CV)
    print(
        f"  gated hods (mean share >= {SUPPORT_MIN_SHARE}): "
        f"{int(gated.sum())} | max CV {cv_max:.3f} | min r {r_min:.4f}"
    )
    print(f"  D2: {'PASS' if d2_pass else 'FAIL — KILL'}")
    if not d2_pass:
        print("\nD2 failed: the discharge shape is not a fleet-invariant conduct")
        print("statistic. Per the ask §5 this KILLS the family — no build, no solve.")

    # ---------------- D3 -------------------------------------------------
    print("\n" + "=" * 78)
    if d2_pass:
        print("D3 — BINDING PRE-CHECK against the keeper's own hourly discharge")
        print("     (HARD KILL BEFORE SOLVE — the caiso-74 lesson)")
    else:
        print("D3 — reported for INFORMATION ONLY: D2 has already killed the family.")
        print("     Nothing below authorizes a build or a solve; it exists so the")
        print("     owner can see whether a repaired-shape variant would even bind.")
    print("=" * 78)
    d3_rows = []
    for year in YEARS:
        dis = keeper_dis_grid(year)  # (365,24) MW == MWh in the hour
        share = sup_share[year]
        da = da_fracs[year]
        day_tot = dis.sum(axis=1)  # (365,) the LP's OWN day total
        floor = share[None, :] * da * day_tot[:, None]  # (365,24)
        short = np.clip(floor - dis, 0.0, None)
        binds = short > BIND_TOL_MWH
        days_binding = float((binds.any(axis=1)).mean())
        ev_binds = float(binds[:, EVENING].any(axis=1).mean())
        # Residual overnight allowance, holding the LP's own day total: the
        # most the fleet could still place overnight once every non-overnight
        # floor is honoured.
        non_on = [h for h in range(24) if h not in OVERNIGHT]
        allow = np.clip(day_tot - floor[:, non_on].sum(axis=1), 0.0, None)
        allow_mw = float(allow.mean() / len(OVERNIGHT))
        keeper_on_mw = float(dis[:, OVERNIGHT].mean())
        excess = KEEPER_OVERNIGHT_EXCESS_MW[year]
        binds_ev_or_all = days_binding
        print(
            f"\n{year}: day-total mean {day_tot.mean() / 1e3:.1f} GWh | "
            f"floor shortfall {short.sum() / 1e6:.3f} TWh "
            f"({short.sum() / dis.sum() * 100:.1f} % of annual discharge)"
        )
        print(
            f"  days with any binding hour {days_binding:.3f} | "
            f"days with a binding EVENING hour {ev_binds:.3f} | "
            f"binding hours {float(binds.mean()):.3f} of all"
        )
        print(
            "  per-hod binding share: "
            + " ".join(f"{v:.2f}" for v in binds.mean(axis=0))
        )
        print(
            f"  keeper overnight(0-6) discharge {keeper_on_mw:.0f} MW/h | "
            f"residual overnight ALLOWANCE {allow_mw:.0f} MW/h "
            f"(headroom {allow_mw - keeper_on_mw:+.0f})"
        )
        print(
            f"  measured overnight over-discharge to remove: {excess:.0f} MW "
            f"(FINDING-caiso127 §3, battery-only basis)"
        )
        # DIRECTION — the structural half of D3. The construction is a FLOOR,
        # so it can only ever ADD discharge to an hour. The measured shape
        # puts a non-trivial share in the overnight, so the overnight limb of
        # the floor FORCES overnight discharge — the opposite of the defect's
        # sign. Quantified against the MW the defect needs removed.
        on_forced = float(short[:, OVERNIGHT].sum() / (365 * len(OVERNIGHT)))
        print(
            f"  DIRECTION: the overnight limb FORCES +{on_forced:.0f} MW/h of "
            f"extra overnight discharge (floor shortfall in hod 0-6), against a "
            f"defect that needs {excess:.0f} MW REMOVED"
        )
        # What the construction would need to bind on the overnight at all:
        # allowance = D x (1 - da x share_non_overnight) must fall to the
        # keeper's own overnight total.
        s_non_on = float(share[[h for h in range(24) if h not in OVERNIGHT]].sum())
        keeper_on_frac = keeper_on_mw * len(OVERNIGHT) / day_tot.mean()
        need_da = (1.0 - keeper_on_frac) / s_non_on
        print(
            f"  to make the overnight allowance merely EQUAL the keeper's own "
            f"overnight discharge, da_frac_dis would have to be {need_da:.3f} "
            f"(measured {da:.3f})"
        )
        # SCALE-INVARIANCE — why this is not a property of the keeper's own
        # day totals. Both sides are FRACTIONS of the day total D[d]:
        # allowance = D x (1 - da x s_non_on) and the keeper's overnight is
        # its own fraction of D, so the ratio holds for ANY D the LP would
        # re-optimize to. The refutation does not depend on the keeper's
        # volume.
        print(
            f"  scale-invariant: allowance = {1 - da * s_non_on:.3f} x D[d] vs "
            f"keeper overnight {keeper_on_frac:.3f} x D[d] "
            f"({(1 - da * s_non_on) / keeper_on_frac:.2f}x free, for ANY D)"
        )
        d3_rows.append(
            {
                "year": year,
                "days_binding": binds_ev_or_all,
                "ev_binds": ev_binds,
                "shortfall_frac": float(short.sum() / dis.sum()),
                "allow_mw": allow_mw,
                "keeper_on_mw": keeper_on_mw,
                "excess": excess,
            }
        )

    # The ask's own two-part D3 criterion.
    ev_ok = all(r["ev_binds"] >= 0.10 for r in d3_rows)
    allow_ok = all(
        r["allow_mw"] < r["keeper_on_mw"] - 0.5 * r["excess"] for r in d3_rows
    )
    d3_pass = ev_ok and allow_ok
    print("\n" + "-" * 78)
    print(
        f"  (a) evening floor binds on a material share of days (>= 0.10 in "
        f"every year): {'YES' if ev_ok else 'NO'}"
    )
    print(
        "  (b) residual overnight allowance sits below the keeper's own "
        f"overnight discharge by at least half the excess: "
        f"{'YES' if allow_ok else 'NO'}"
    )
    print(f"  D3: {'PASS' if d3_pass else 'FAIL — HARD KILL, NO LP IS SOLVED'}")
    if not d3_pass:
        print(
            "\nD3 failed: the derived discharge floor is ex-ante SLACK against the\n"
            "keeper's own dispatch, so arming it cannot move the overnight position.\n"
            "Per the owner grant this kills the S1 family with no LP solved."
        )
    if not d2_pass:
        return 1
    if not d3_pass:
        return 2

    # ---------------- D4 -------------------------------------------------
    print("\n" + "=" * 78)
    print("D4 — the mechanism cannot pin the LEVEL")
    print("=" * 78)
    for year in YEARS:
        da = da_fracs[year]
        print(
            f"  {year}: Σ_hod alloc_share_dis = {sup_share[year].sum():.6f}, so the "
            f"day-total floor is da_frac_dis x D[d] = {da:.4f} x D[d] — the day "
            f"total D[d] stays the LP's own and {1 - da:.4f} of it stays free at "
            "the RT margin; D[d] = 0 remains feasible (nothing is forced)."
        )
    print("\nALL GATES PASS — S1 is admissible to build and A/B.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
