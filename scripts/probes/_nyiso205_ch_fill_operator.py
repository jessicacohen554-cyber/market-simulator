"""nyiso-205 phase 0 — is ``cheapest_first`` the right distribution operator for the
Capital_Hudson ``ST_GAS`` ``tmax 31.1`` reliability-floor limb?

ZERO LP. This is nyiso-203 §5's test, taken verbatim on a limb it has never been taken on.

THE OBJECT. The live Capital_Hudson ``ST_GAS`` hot step carries an EMPTY ``distribution``
column in ``data/raw/reference/reliability_floor_coeffs_NYISO.csv``, so it falls through to
``ReliabilityFloorSpec.distribution``'s dataclass default ``cheapest_first``. Every OTHER
enabled NYISO limb names ``pro_rata`` explicitly — including the ``CH_ST_ev`` ramp family on
this very (zone, class). The question is whether the operator this limb actually runs is the
one Capital_Hudson steam's own metered conduct supports.

WHY THE OPERATOR AND NOT THE MEMBERSHIP. nyiso-204 refused the membership arm (2480 + 8006) and
nyiso-204b refused its narrowed form (2480 alone); DO-NOT-REDO covers both. 204b §3 named the
instrument the evidence actually points at: 2480's D-4 conviction is that its meter reads zero
in 100 % of the hours THE CHEAPEST-FIRST FILL REACHES IT — a fact about which hours a zonal
target selects at the BOTTOM of the stack, not about who belongs in the class.

WHAT THE TWO OPERATORS DO (``model/interchange/core.py``). Both size the same hourly quantity,
``frac × Σ available capacity`` over the selected rows, so the delivered AGGREGATE MW is
identical and they differ ONLY in which units carry it:

* ``cheapest_first`` (``_distribute_group_floor``) sorts rows by heat rate and fills each to its
  available cap until the target is exhausted — a CONCENTRATION assertion.
* ``pro_rata`` floors every row at ``frac ×`` its own available capacity, so a plant's share of
  the floor equals its AVAILABLE-CAPACITY share exactly — a PROPORTIONALITY assertion.

That is why the operator is a cleaner object than the membership edit nyiso-204 refused: the
membership edit shrank the target's own base by ~60 % (a level change by the back door, rules
21 / 23), while an operator swap moves no MW in aggregate.

THE TEST. In the limb's own binding window — reconstructed from the engine's own code path
(``iso_zone_tmax`` → ``tmax > 31.1 °C`` → ``_bridge_flagged_runs(min_event_hours=48)``, which
reproduces 504 / 432 / 600 h for 2023 / 2024 / 2025) — measure per plant:

1. **gen share**   = plant Σ metered CAMPD ``grossLoad`` ÷ class Σ
2. **avail share** = plant Σ (``pmax × availability``) ÷ class Σ — which IS ``pro_rata``'s own
   allocation share, exactly
3. **g/a ratio**   = (1) ÷ (2)  ← nyiso-203 §5's statistic
4. **``cheapest_first``'s allocation share**, computed by running the SHIPPED
   ``_distribute_group_floor`` kernel on the reconstructed arrays — not by arithmetic here
5. **manufactured energy** ``Σ max(0, floor − metered)`` per plant under EACH operator — the
   do-no-harm statistic, nyiso-203 §6's

Robustness, pre-registered in ``results/calibration/PREREG-nyiso205-ch-fill-operator.md`` §4 so
it cannot be chosen after the fact: every share is reported over THREE hour sets — the bridged
binding window (the limb's own), the unbridged ``tmax > 31.1`` flagged hours, and the binding
window narrowed to the h14-21 evening peak. A conclusion that survives only one cut is reported
as not surviving. *(The PREREG's third cut, "all hours of flagged calendar days", is degenerate —
the day gate is already day-constant — and was replaced by the h14-21 cut BEFORE any number was
read; see ``_limb_masks`` and the PREREG addendum §A.)*

Diagnostic only. Arms nothing, edits nothing, registers nothing; the registry is read, never
patched, and no CSV is touched.

Reproduce: ``uv run python scripts/probes/_nyiso205_ch_fill_operator.py``.
Writes ``results/calibration/_nyiso205_ch_fill_operator.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.bundle_fleet import (  # noqa: E402
    ensure_probe_path,
    reconstruct_bundle_fleet,
)

ensure_probe_path()

BUNDLE = ROOT / "results" / "calibration" / "nyiso202_startup_aware"
KEEPER_ID = "2026-09-06-nyiso-202-startup-aware"
ISO = "NYISO"
ZONE = "Capital_Hudson"
KLASS = "ST_GAS"
THRESHOLD_C = 31.1  # the limb's own day gate
MIN_EVENT_HOURS = 48  # _STEAM_MIN_EVENT_HOURS, applied to ST_GAS by the loader
FLOOR_PCT = 0.0973  # commit_frac 0.8105 × min_stable_pct 0.12 (frozen, rule 23)
YEARS = (2023, 2024, 2025)
NAMES = {
    2625: "Bowline Generating Station",
    8006: "Roseton Generating LLC",
    2480: "Danskammer Generating Station",
}
OUT = ROOT / "results" / "calibration" / "_nyiso205_ch_fill_operator.json"


def _limb_masks(year: int, hours: int) -> dict[str, np.ndarray]:
    """Return the limb's three hour sets, built on the engine's own code path.

    ``binding`` is the mask the engine actually applies (the bridged run mask);
    ``flagged`` is the raw day gate before bridging; ``binding_h14_21`` is the
    binding window narrowed to the evening peak hours the class's own
    (disarmed) ``CH_ST_ev`` ramp family targets. The last two exist only as the
    pre-registered robustness cuts — the verdict is read off ``binding``.

    The PREREG's third cut was "all hours of flagged calendar days". It is
    DEGENERATE: ``iso_zone_tmax`` returns a DAILY tmax broadcast hourly, so the
    raw day gate is already constant within a calendar day and that cut is
    identical to ``flagged`` by construction. It is replaced here by the
    h14-21 peak-window cut, which is not degenerate and asks the sharper
    question — does the proportionality hold when the system is actually tight,
    or only across the overnight hours a 48 h bridge sweeps in? **The
    substitution was made before any number was read** (PREREG addendum §A).
    """
    from market_sim.data.eia_loader import iso_zone_tmax
    from market_sim.model.interchange.core import _bridge_flagged_runs

    wx = iso_zone_tmax(ISO, year, hours, zone=ZONE)
    if wx is None:
        raise SystemExit(f"no weather for {ZONE} {year}")
    tmax, _ = wx
    flagged = np.asarray(tmax) > THRESHOLD_C
    binding = _bridge_flagged_runs(flagged, MIN_EVENT_HOURS)
    hod = np.arange(hours) % 24
    peak = binding & (hod >= 14) & (hod <= 21)
    return {"binding": binding, "flagged": flagged, "binding_h14_21": peak}


def _cheapest_first_take(
    pmax: np.ndarray,
    availability: np.ndarray,
    pmin: np.ndarray,
    heat_rate: np.ndarray,
    frac: np.ndarray,
) -> np.ndarray:
    """Run the SHIPPED cheapest-first kernel on the limb's rows and return its floor.

    The kernel touches only ``pmax``/``availability``/``pmin``/``heat_rate``/``min_gen``
    (and allocates ``min_gen_mechanism``), each indexed by ``rows`` — so calling it on a
    row-sliced shim with ``rows = arange(n)`` is exact, not a re-implementation. ``min_gen``
    starts at ``pmin`` exactly as ``_apply_frac`` initialises it; the returned array is the
    composed floor, so ``floor − pmin`` is the forced increment.
    """
    from market_sim.model.interchange.core import _distribute_group_floor

    n, hours = availability.shape
    shim = SimpleNamespace(
        pmax=pmax,
        availability=availability,
        pmin=pmin,
        heat_rate=heat_rate,
        min_gen=np.broadcast_to(pmin[:, None], (n, hours)).copy(),
        min_gen_mechanism=None,
    )
    _distribute_group_floor(shim, np.arange(n), frac, hours)
    return shim.min_gen


def _pro_rata_take(
    pmax: np.ndarray, availability: np.ndarray, pmin: np.ndarray, frac: np.ndarray
) -> np.ndarray:
    """Return the ``pro_rata`` branch's composed floor for the limb's rows.

    Mirrors ``_apply_frac``'s else-branch verbatim: each row floored at ``frac ×`` its own
    available capacity, composed with ``pmin`` through ``maximum``.
    """
    n, hours = availability.shape
    floor = np.broadcast_to(pmin[:, None], (n, hours)).copy()
    np.maximum(floor, frac * (pmax[:, None] * availability), out=floor)
    return floor


def _metered(year: int, hours: int, codes: list[int]) -> dict[int, np.ndarray]:
    """Return per-plant hourly metered ``grossLoad`` on the run horizon's hour index."""
    import pandas as pd

    from market_sim.config.paths import RAW_DIR

    c = pd.read_parquet(RAW_DIR / "campd-unit-level" / f"NY_{year}.parquet")
    c = c[c["facilityId"].astype(int).isin(codes)].copy()
    c["code"] = c["facilityId"].astype(int)
    c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
    g = c.groupby(["code", "ts"])["grossLoad"].sum().reset_index()
    origin = pd.Timestamp(year=year, month=1, day=1)
    g["h"] = ((g["ts"] - origin) / pd.Timedelta(hours=1)).astype(int)
    g = g[(g["h"] >= 0) & (g["h"] < hours)]
    out: dict[int, np.ndarray] = {}
    for code in codes:
        p = g[g["code"] == code]
        series = np.zeros(hours, dtype=float)
        series[p["h"].to_numpy()] = p["grossLoad"].to_numpy(dtype=float)
        out[code] = series
    return out


def main() -> int:
    """Measure the limb's operator question on 2023-2025 and write the JSON record."""
    from market_sim.config.iso_configs import get_iso_config

    rec: dict = {
        "session": "nyiso-205",
        "status": "ZERO LP — one fleet_only reconstruction per year, no solve, nothing patched",
        "keeper": KEEPER_ID,
        "question": (
            "nyiso-203 §5's operator test, taken on the Capital_Hudson ST_GAS tmax 31.1 limb: "
            "do the class's plants share the hot-day commitment in proportion to available "
            "capacity (pro_rata), or is it concentrated on the cheapest plant (cheapest_first)?"
        ),
        "limb": {
            "zone": ZONE,
            "plant_class": KLASS,
            "driver": "tmax",
            "threshold_c": THRESHOLD_C,
            "floor_pct": FLOOR_PCT,
            "min_event_hours": MIN_EVENT_HOURS,
            "distribution_live": "cheapest_first (CSV column EMPTY -> dataclass default)",
        },
        "years": {},
    }

    for year in YEARS:
        state, meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
        fa = state["fleet_arrays"]
        zone_names = [z.name for z in get_iso_config(meta["iso"]).zones]
        z_idx = zone_names.index(ZONE)
        sel = (
            (np.asarray(fa.plant_group) == KLASS)
            & (fa.zone_idx == z_idx)
            & (fa.pmax > 0.0)
        )
        rows = np.flatnonzero(sel)
        hours = int(fa.availability.shape[1])
        pmax = fa.pmax[rows]
        pmin = fa.pmin[rows]
        hr = fa.heat_rate[rows]
        availability = fa.availability[rows, :]
        codes = np.asarray(fa.plant_code)[rows].astype(int)

        masks = _limb_masks(year, hours)
        frac = np.where(masks["binding"], FLOOR_PCT, 0.0)

        avail = pmax[:, None] * availability
        cf_floor = _cheapest_first_take(pmax, availability, pmin, hr, frac)
        pr_floor = _pro_rata_take(pmax, availability, pmin, frac)
        cf_forced = np.maximum(cf_floor - pmin[:, None], 0.0)
        pr_forced = np.maximum(pr_floor - pmin[:, None], 0.0)

        gen = _metered(year, hours, sorted(set(int(c) for c in codes)))

        yr: dict = {
            "n_rows": int(rows.size),
            "hours_binding": int(masks["binding"].sum()),
            "hours_flagged_unbridged": int(masks["flagged"].sum()),
            "hours_binding_h14_21": int(masks["binding_h14_21"].sum()),
            "zonal_target_mean_mw_on_binding": float(
                (FLOOR_PCT * avail.sum(axis=0))[masks["binding"]].mean()
            ),
            "class_nameplate_mw": float(
                sum(pmax[codes == c].sum() for c in sorted(set(codes)))
            ),
            "aggregate_identity": {},
            "cuts": {},
            "plants": {},
        }

        # The operators must deliver the SAME aggregate. Verified, not assumed.
        for name, arr in (("cheapest_first", cf_forced), ("pro_rata", pr_forced)):
            yr["aggregate_identity"][name + "_forced_twh"] = float(arr.sum() / 1e6)
        yr["aggregate_identity"]["target_twh"] = float(
            (FLOOR_PCT * avail.sum(axis=0))[masks["binding"]].sum() / 1e6
        )

        for cut, mask in masks.items():
            m = mask
            tot_gen = sum(gen[c][m].sum() for c in sorted(set(codes)))
            tot_avail = avail[:, m].sum()
            cut_rec: dict = {}
            for c in sorted(set(codes)):
                r = codes == c
                g_share = float(gen[c][m].sum() / tot_gen) if tot_gen else 0.0
                a_share = float(avail[r][:, m].sum() / tot_avail) if tot_avail else 0.0
                cut_rec[str(c)] = {
                    "gen_share": g_share,
                    "avail_share": a_share,
                    "g_over_a": float(g_share / a_share) if a_share else None,
                }
            yr["cuts"][cut] = cut_rec

        m = masks["binding"]
        tot_cf = cf_forced[:, m].sum()
        tot_pr = pr_forced[:, m].sum()
        for c in sorted(set(codes)):
            r = codes == c
            metered = gen[c]
            cf_p = cf_floor[r][:, m].sum(axis=0)
            pr_p = pr_floor[r][:, m].sum(axis=0)
            yr["plants"][str(c)] = {
                "name": NAMES.get(int(c), str(c)),
                "nameplate_mw": float(pmax[r].sum()),
                "n_rows": int(r.sum()),
                "heat_rate_min": float(hr[r].min()),
                "heat_rate_max": float(hr[r].max()),
                # allocation shares of the limb's forced energy, binding hours
                "cheapest_first_share": float(cf_forced[r][:, m].sum() / tot_cf)
                if tot_cf
                else 0.0,
                "pro_rata_share": float(pr_forced[r][:, m].sum() / tot_pr)
                if tot_pr
                else 0.0,
                "cheapest_first_forced_twh": float(cf_forced[r][:, m].sum() / 1e6),
                "pro_rata_forced_twh": float(pr_forced[r][:, m].sum() / 1e6),
                # manufactured energy: floor above what the meter actually did
                "manufactured_twh_cheapest_first": float(
                    np.maximum(cf_p - metered[m], 0.0).sum() / 1e6
                ),
                "manufactured_twh_pro_rata": float(
                    np.maximum(pr_p - metered[m], 0.0).sum() / 1e6
                ),
                "binding_h_cheapest_first": int((cf_forced[r][:, m] > 1e-9).any(0).sum()),
                "binding_h_pro_rata": int((pr_forced[r][:, m] > 1e-9).any(0).sum()),
                "metered_mean_mw_on_binding": float(metered[m].mean()),
                "metered_p_online_on_binding": float((metered[m] > 0).mean()),
            }
        rec["years"][str(year)] = yr

        print(f"=== {year}  limb binds {yr['hours_binding']} h "
              f"(unbridged {yr['hours_flagged_unbridged']} h); "
              f"zonal target {yr['zonal_target_mean_mw_on_binding']:.1f} MW mean")
        print(f"    {'plant':>6} {'name':<30}{'gen sh':>9}{'avail sh':>10}{'g/a':>8}"
              f"{'CF sh':>9}{'PR sh':>8}{'HR':>14}")
        for c in sorted(set(codes)):
            v = yr["plants"][str(c)]
            k = yr["cuts"]["binding"][str(c)]
            print(
                f"    {c:>6} {v['name'][:29]:<30}{k['gen_share']:>9.3f}"
                f"{k['avail_share']:>10.3f}{(k['g_over_a'] or 0.0):>8.2f}"
                f"{v['cheapest_first_share']:>9.3f}{v['pro_rata_share']:>8.3f}"
                f"{v['heat_rate_min']:>7.2f}-{v['heat_rate_max']:.2f}"
            )
        ai = yr["aggregate_identity"]
        print(f"    aggregate forced: CF {ai['cheapest_first_forced_twh']:.5f} TWh vs "
              f"PR {ai['pro_rata_forced_twh']:.5f} TWh (target {ai['target_twh']:.5f})\n")

    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
