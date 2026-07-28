"""caiso-133 — WHICH import-direction limit binds on the CAISO corridors?

``FINDING-caiso132`` killed ask A1 and, in doing so, stated an honest limit
(§2): the zonal spread ``lambda_terminus - lambda_corridor`` says *some*
import-direction limit binds, but the duals alone cannot say **which** of the
three candidates it is —

1. the **corridor deliverability group** (the measured EIA-930 per-(month x
   hour-of-day) p95 net-import envelope, one one-sided interface row per leg),
2. the **link's own TTC** (the flow column's bound: COI/Path-66 4,800 MW into
   NP15, Path-46/WOR 10,623 MW into SP15_rest),
3. the **``WECC_import_simultaneous`` interface** over both legs (7,500 MW
   baked, superseded by the published branch-group MIC seam limit when
   ``capacity_deliverability_limits`` is on — the keeper's setting).

Until that is separated no lever can be selected for **C3a-2025** and any
candidate is a guess. This instrument separates it two independent ways:

* **§A — REACHABILITY (no LP, committed data only).** A constraint can carry a
  positive dual only if it is *attainable*. Each leg's flow is bounded above by
  its own corridor envelope, so if that envelope never reaches the link's TTC,
  and the two legs' envelopes never sum to the seam cap, then limits 2 and 3
  are strictly slack in **every** hour by construction and limit 1 is the only
  one that can ever bind. This is exact and needs nothing but the envelope
  builder the LP itself calls.

* **§B — MEASURED ATTRIBUTION (from the solved network sidecar).** The LP's own
  flow-column stationarity closes the decomposition exactly. The flow column
  carries zero objective cost and appears in the two energy-balance rows plus
  every interface group it belongs to, so

      lambda_to - lambda_from = -z_link - sum_g s(g,link) * y_g

  with ``z_link`` the column's reduced cost, ``y_g`` each group's row dual and
  ``s`` its signed membership. Every right-hand term is >= 0 in the import
  direction and is the rent charged by exactly ONE limit. Reading them from
  ``hourly/network_<year>.parquet`` attributes the congestion rent per leg, per
  hour, with no ambiguity left.

* **§C — the rule-14 question.** Having named the binding limit, ask whether it
  is the *inaccurate* input: compare the model's corridor import in the defect
  hours against the MEASURED corridor import in the same hours. A cap the model
  presses against while already carrying MORE import than reality is not too
  tight, and relaxing it is rule-1 ``[R-STRUCT]`` / rule-14 ``[R-ACCURATE]``
  refused (the caiso-121 +2,606 MW surplus-belly over-import).

Defect-hour conventions, the dual method, the CA-lambda construction and the
reconciliation to ``FINDING-caiso131`` §7 are **imported verbatim** from
``_caiso132_corridor_export_gates`` so nothing here re-measures what that
instrument already carries (its §10 DO-NOT-REDO) and every row composes with
caiso-120/121/131/132 on the same basis.

**No LP is built and no solver is called.** Nothing is armed: this is a
measurement that SELECTS a family; arming one is a separate owner ask with its
own D-gates and prereg (rule 1 ``[R-STRUCT]``).

Usage::

    PYTHONPATH=.:src:scripts/probes .venv/bin/python \\
        scripts/probes/_caiso133_binding_limit_separation.py \\
        results/calibration/caiso133_sidecar_A [--years 2023 2024 2025]

The bundle argument only needs ``hourly/system_<y>.parquet`` +
``hourly/class_hourly_<y>.parquet`` for §A/§C; §B additionally needs
``hourly/network_<y>.parquet`` and is skipped (with a loud note) when the
bundle predates that sidecar.

Finding: ``results/calibration/FINDING-caiso133-binding-limit-separation-2026-07-28.md``
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from _caiso132_corridor_export_gates import (  # noqa: E402
    CA_ZONES,
    CORRIDOR_TERMINUS,
    EQ_TOL,
    T,
    class_hourly,
    defect_mask,
    envelopes,
    spread_frame,
    zonal_demand,
    zonal_prices,
)

ISO = "CAISO"
# The corridor legs' own physical link ratings, read from the LP's topology
# rather than restated, so a re-rating cannot silently invalidate §A.
LINK_TO = {z: t for z, t in CORRIDOR_TERMINUS.items()}


# ---------------------------------------------------------------------------
# topology / limit levels (no LP)
# ---------------------------------------------------------------------------
def corridor_link_ttc() -> dict[str, float]:
    """Per-leg link TTC (MW) from the LP's own split topology."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.interchange.caiso import split_caiso_import_node_per_hub

    cfg = split_caiso_import_node_per_hub(get_iso_config(ISO))
    out: dict[str, float] = {}
    for leg, term in CORRIDOR_TERMINUS.items():
        for ln in cfg.links:
            if (ln.from_zone, ln.to_zone) == (leg, term):
                out[leg] = float(ln.ttc_mw)
    return out


def seam_cap_mw(year: int) -> float | None:
    """The ``WECC_import_simultaneous`` cap the LP saw for ``year`` (MW).

    With ``capacity_deliverability_limits`` on — the caiso-51 keeper setting,
    still on in the current keeper — the baked 7,500 MW scalar is replaced by
    the published branch-group Maximum Import Capability summed to the WECC
    boundary (``transmission.apply_deliverability_seam_limit``). Returns the
    baked scalar when the published limit is unavailable.
    """
    from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data import capacity_deliverability as capdel

    try:
        dy = capdel.resolve_delivery_year(ISO, year)
        season = capdel.resolve_season(ISO)
        by_zone, _ = aggregate_by_zone(
            ISO,
            capdel.import_limit_by_area(ISO, dy, season),
            capdel.area_types_by_area(ISO, dy, season, "import_limit"),
        )
        published = by_zone.get("WECC_import")
        if published:
            return float(published)
    except Exception as exc:  # pragma: no cover - data-availability guard
        print(f"      (published MIC unavailable for {year}: {exc})")
    for lim in get_iso_config(ISO).interface_limits:
        if lim.name == "WECC_import_simultaneous":
            return float(lim.cap_mw)
    return None


# ---------------------------------------------------------------------------
# §A — reachability: which limits CAN bind at all?
# ---------------------------------------------------------------------------
def section_a(years: tuple[int, ...]) -> dict:
    """A: is each candidate limit ATTAINABLE, hour by hour?"""
    print("\n" + "=" * 96)
    print("A — REACHABILITY (no LP): can each candidate limit bind AT ALL?")
    print("=" * 96)
    print(
        "  A limit carries a positive dual only if some feasible point makes it\n"
        "  tight. Each leg's flow is bounded above by its OWN corridor group cap,\n"
        "  so:  env_leg(t) < TTC_leg           => the link bound is unreachable;\n"
        "       env_PNW(t) + env_DSW(t) < MIC  => the seam row is unreachable.\n"
        "  Both are exact upper-bound arguments — no solve, no flow series."
    )
    ttc = corridor_link_ttc()
    print(
        f"\n  link TTC (LP topology): {', '.join(f'{k} {v:,.0f} MW' for k, v in ttc.items())}"
    )

    rows: dict[int, dict] = {}
    for year in years:
        both = envelopes(year)
        env = both["import"]
        exp = both.get("export") or {}
        mic = seam_cap_mw(year)
        tot = np.zeros(T)
        print(
            f"\n  --- {year}   seam cap (MIC) {mic:,.0f} MW ---"
            if mic
            else f"\n  --- {year} ---"
        )
        print(
            f"      {'leg':<10} {'env mean':>9} {'env max':>9} {'TTC':>9} "
            f"{'env/TTC max':>12} {'h env>=TTC':>11}"
        )
        year_row = {}
        for leg in CORRIDOR_TERMINUS:
            e = np.asarray(env[leg], dtype=float)
            tot += e
            n_hit = int((e >= ttc[leg] - 1e-9).sum())
            print(
                f"      {leg:<10} {e.mean():>9.1f} {e.max():>9.1f} {ttc[leg]:>9.1f} "
                f"{e.max() / ttc[leg]:>12.3f} {n_hit:>11d}"
            )
            year_row[leg] = {
                "env_max": float(e.max()),
                "ttc": float(ttc[leg]),
                "hours_env_ge_ttc": n_hit,
            }
        n_seam = int((tot >= float(mic) - 1e-9).sum()) if mic else -1
        print(
            f"      {'SUM legs':<10} {tot.mean():>9.1f} {tot.max():>9.1f} "
            f"{(mic or float('nan')):>9.1f} {tot.max() / mic if mic else float('nan'):>12.3f} "
            f"{n_seam:>11d}"
        )
        year_row["_seam"] = {
            "mic": float(mic) if mic else None,
            "sum_env_max": float(tot.max()),
            "hours_sum_ge_mic": n_seam,
        }
        # The same argument in the EXPORT (negative) direction: the corridor
        # group's own lower bound is -export_env, so if that never reaches the
        # link's -TTC (or the two legs' -MIC), the link bound and the seam row
        # are unreachable DOWNWARD too — i.e. the corridor group is the only
        # transmission constraint that can bind on either leg in either
        # direction. Reported so the claim is not import-only.
        if exp:
            tot_x = np.zeros(T)
            print(
                f"      {'-- export':<10} {'env mean':>9} {'env max':>9} {'TTC':>9} "
                f"{'env/TTC max':>12} {'h env>=TTC':>11}"
            )
            for leg in CORRIDOR_TERMINUS:
                x = np.asarray(exp.get(leg, np.zeros(T)), dtype=float)
                tot_x += x
                n_hit_x = int((x >= ttc[leg] - 1e-9).sum())
                print(
                    f"      {leg:<10} {x.mean():>9.1f} {x.max():>9.1f} {ttc[leg]:>9.1f} "
                    f"{x.max() / ttc[leg]:>12.3f} {n_hit_x:>11d}"
                )
                year_row[leg]["hours_exp_env_ge_ttc"] = n_hit_x
            n_seam_x = int((tot_x >= float(mic) - 1e-9).sum()) if mic else -1
            print(
                f"      {'SUM legs':<10} {tot_x.mean():>9.1f} {tot_x.max():>9.1f} "
                f"{(mic or float('nan')):>9.1f} "
                f"{tot_x.max() / mic if mic else float('nan'):>12.3f} {n_seam_x:>11d}"
            )
            year_row["_seam"]["hours_sum_exp_ge_mic"] = n_seam_x
        rows[year] = year_row

    unreachable_ttc = all(
        rows[y][leg]["hours_env_ge_ttc"] == 0
        and rows[y][leg].get("hours_exp_env_ge_ttc", 0) == 0
        for y in years
        for leg in CORRIDOR_TERMINUS
    )
    unreachable_seam = all(
        rows[y]["_seam"]["hours_sum_ge_mic"] == 0
        and rows[y]["_seam"].get("hours_sum_exp_ge_mic", 0) == 0
        for y in years
    )
    print(
        "\n  >>> link TTC reachable in ANY hour, EITHER direction: "
        f"{'NO — structurally unreachable' if unreachable_ttc else 'YES'}\n"
        "  >>> seam (WECC_import_simultaneous) reachable in ANY hour, EITHER "
        f"direction: {'NO — structurally unreachable' if unreachable_seam else 'YES'}"
    )
    if unreachable_ttc and unreachable_seam:
        print(
            "  >>> Therefore EVERY bind on either corridor leg — import OR export —\n"
            "      is the CORRIDOR DELIVERABILITY GROUP, the measured p95 net-flow\n"
            "      envelope. The FINDING-caiso132 §2 three-way ambiguity is CLOSED."
        )
    return {
        "rows": rows,
        "ttc_unreachable": bool(unreachable_ttc),
        "seam_unreachable": bool(unreachable_seam),
    }


# ---------------------------------------------------------------------------
# §B — measured attribution from the network sidecar
# ---------------------------------------------------------------------------
_SIGNED = re.compile(r"([+-])([^+-]+)")


def _group_members(label: str) -> list[tuple[float, str]]:
    """Parse a ``grp:+A>B-C>D`` sidecar label into signed link names.

    A trailing ``#n`` is the writer's disambiguator for two groups that share a
    signed membership; it carries no membership information and is stripped.
    """
    body = label[len("grp:") :].split("#", 1)[0]
    return [(1.0 if s == "+" else -1.0, name) for s, name in _SIGNED.findall(body)]


def network_frame(bundle: Path, year: int) -> "pd.DataFrame | None":
    """P1 network sidecar for ``year``, or ``None`` when the bundle predates it."""
    path = bundle / "hourly" / f"network_{year}.parquet"
    if not path.exists():
        return None
    d = pd.read_parquet(path)
    return d[d["pass"] == "P1"]


def section_b(bundle: Path, years: tuple[int, ...]) -> dict:
    """B: attribute the defect-hour congestion rent to ONE limit, per leg, per hour."""
    print("\n" + "=" * 96)
    print("B — MEASURED ATTRIBUTION from the solved duals (network sidecar)")
    print("=" * 96)
    print(
        "  Identity (exact, the LP's own stationarity on the zero-cost flow column):\n"
        "    lambda_to - lambda_from = -z_link - sum_g s(g,link) * y_g\n"
        "  z_link = the link column's reduced cost (its OWN TTC bound),\n"
        "  y_g    = each interface group's row dual (corridor group / seam row).\n"
        "  Every term is >= 0 in the import direction and is ONE limit's rent."
    )
    out: dict[int, dict] = {}
    for year in years:
        net = network_frame(bundle, year)
        if net is None:
            print(
                f"\n  --- {year}: no network_{year}.parquet in this bundle — SKIPPED ---"
            )
            continue
        if not (bundle / "hourly" / f"system_{year}.parquet").exists():
            # The per-year system slices are written once at the END of a
            # multi-year run, so a bundle can legitimately be mid-flight.
            print(f"\n  --- {year}: no system_{year}.parquet yet — SKIPPED ---")
            continue
        links = net[net["kind"] == "link"]
        groups = net[net["kind"] == "group"]
        mask = defect_mask(bundle, year)
        idx = np.flatnonzero(mask)
        p = zonal_prices(bundle, year)
        dem = zonal_demand(bundle, year)
        ca = [z for z in CA_ZONES if z in p.columns]
        w = dem[ca].sum(axis=1).to_numpy()
        sp = spread_frame(bundle, year)

        print(f"\n  --- {year}: Sep-Dec surplus belly, n = {idx.size} h ---")
        print(
            f"      {'leg':<10} {'rent':>8} | {'corridor grp':>13} {'link TTC':>9} "
            f"{'seam row':>9} {'residual':>9}"
        )
        year_out = {}
        for leg, term in CORRIDOR_TERMINUS.items():
            link_name = f"{leg}>{term}"
            lk = links[links["name"] == link_name]
            if lk.empty:
                print(f"      {leg:<10} (link {link_name} absent from the sidecar)")
                continue
            z = lk.sort_values("hour")["dual"].to_numpy()
            # Every group this link belongs to, split into the single-member
            # corridor group and the multi-member seam row by its own label.
            corridor = np.zeros(T)
            seam = np.zeros(T)
            for label in groups["name"].unique():
                members = _group_members(str(label))
                names = [n for _s, n in members]
                if link_name not in names:
                    continue
                sgn = next(s for s, n in members if n == link_name)
                y = (
                    groups[groups["name"] == label]
                    .sort_values("hour")["dual"]
                    .to_numpy()
                )
                bucket = corridor if len(members) == 1 else seam
                bucket += sgn * y
            # Rent per limit, >= 0 in the import direction (the negated duals).
            rent_link = -z
            rent_corr = -corridor
            rent_seam = -seam
            spread = sp[leg].to_numpy()
            resid = spread - (rent_link + rent_corr + rent_seam)
            # Demand-weighted over the defect hours, the C3a currency.
            aw = lambda a: float(np.average(a[idx], weights=w[idx]))  # noqa: E731
            rent = aw(np.maximum(spread, 0.0))
            print(
                f"      {leg:<10} {rent:>8.2f} | {aw(rent_corr):>13.2f} "
                f"{aw(rent_link):>9.2f} {aw(rent_seam):>9.2f} {aw(np.abs(resid)):>9.2e}"
            )
            year_out[leg] = {
                "rent": rent,
                "corridor_group": aw(rent_corr),
                "link_ttc": aw(rent_link),
                "seam_row": aw(rent_seam),
                "max_abs_residual": float(np.abs(resid[idx]).max())
                if idx.size
                else 0.0,
                # Share of import-bound HOURS whose rent is carried by each limit.
                "hours_corridor": float(
                    (rent_corr[idx] > EQ_TOL).mean() if idx.size else np.nan
                ),
                "hours_link": float(
                    (rent_link[idx] > EQ_TOL).mean() if idx.size else np.nan
                ),
                "hours_seam": float(
                    (rent_seam[idx] > EQ_TOL).mean() if idx.size else np.nan
                ),
            }
        out[year] = year_out

        # Whole-year attribution too, so the answer is not a window artefact.
        print(f"      {'-' * 70}")
        print(
            f"      {'ALL 8760 h':<10} {'rent':>8} | {'corridor grp':>13} "
            f"{'link TTC':>9} {'seam row':>9}"
        )
        for leg, term in CORRIDOR_TERMINUS.items():
            link_name = f"{leg}>{term}"
            lk = links[links["name"] == link_name]
            if lk.empty:
                continue
            z = lk.sort_values("hour")["dual"].to_numpy()
            corridor = np.zeros(T)
            seam = np.zeros(T)
            for label in groups["name"].unique():
                members = _group_members(str(label))
                names = [n for _s, n in members]
                if link_name not in names:
                    continue
                sgn = next(s for s, n in members if n == link_name)
                y = (
                    groups[groups["name"] == label]
                    .sort_values("hour")["dual"]
                    .to_numpy()
                )
                (corridor if len(members) == 1 else seam)[:] += sgn * y
            ann = lambda a: float(np.average(a, weights=w))  # noqa: E731
            print(
                f"      {leg:<10} {ann(np.maximum(sp[leg].to_numpy(), 0.0)):>8.2f} | "
                f"{ann(-corridor):>13.2f} {ann(-z):>9.2f} {ann(-seam):>9.2f}"
            )
    return out


# ---------------------------------------------------------------------------
# §C — is the binding limit the INACCURATE input? (rule 14)
# ---------------------------------------------------------------------------
def measured_corridor_import(year: int) -> "np.ndarray | None":
    """Measured NET corridor import (MW, both legs) mapped onto the model clock.

    Reads the same bytes, applies the same lag correction, and keys the same
    ``(month x hour-of-day)`` buckets as ``measured_corridor_flow_envelope``,
    so §C compares the model against the very series the binding cap was
    derived from — never a re-derivation that could drift, and never a
    positional index that a leap year or a data gap would silently shift.
    Returns the ``(T,)`` bucket-mean series (NaN where a bucket is empty).
    """
    from market_sim.config.interchange_config import CAISO_CORRIDOR_DIBA
    from market_sim.config.paths import RAW_DIR
    from market_sim.data.eia930.envelopes import _caiso_interchange_model_clock
    from market_sim.data.fleet import _hour_to_month_index

    path = RAW_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    local = _caiso_interchange_model_clock(pd.DatetimeIndex(frame["local_time"]))
    frame = frame[local.year == year]
    local = local[local.year == year]
    if frame.empty:
        return None
    work = pd.DataFrame(
        {
            "corridor": frame["diba"].astype(str).map(CAISO_CORRIDOR_DIBA).to_numpy(),
            "month": local.month.to_numpy(),
            "hod": local.hour.to_numpy(),
            "ts": local.to_numpy(),
            "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["corridor", "mw"])
    if work.empty:
        return None
    # EIA-930 sign: mw > 0 means CISO EXPORTS, so net import = -sum(mw) over
    # BOTH corridors' DIBAs at each timestamp; then the (month, hod) mean.
    per_ts = -work.groupby(["ts", "month", "hod"], observed=True)["mw"].sum()
    per_ts = per_ts.reset_index(name="net_import")
    tab = np.full((12, 24), np.nan)
    for (m, h), g in per_ts.groupby(["month", "hod"], observed=True):
        tab[int(m) - 1, int(h)] = float(g["net_import"].mean())
    rm = _hour_to_month_index(T)  # 0-based month per model hour
    rh = np.arange(T) % 24
    return tab[rm, rh]


def section_c(bundle: Path, years: tuple[int, ...]) -> dict:
    """C: the rule-14 question — is the binding envelope too TIGHT, or too loose?"""
    print("\n" + "=" * 96)
    print("C — rule 14 [R-ACCURATE]: is the binding limit the INACCURATE input?")
    print("=" * 96)
    print(
        "  The binding limit is a MEASURED envelope (EIA-930 per-(month x hod) p95\n"
        "  net import). Relaxing it is refused on its face unless the model is\n"
        "  short of import against reality in the very hours it binds. Compare the\n"
        "  model's corridor import to the MEASURED corridor import, same hours."
    )
    out = {}
    for year in years:
        if not (bundle / "hourly" / f"class_hourly_{year}.parquet").exists():
            continue
        mask = defect_mask(bundle, year)
        idx = np.flatnonzero(mask)
        if idx.size == 0:
            continue
        env = envelopes(year)["import"]
        cap = np.sum([np.asarray(env[z], dtype=float) for z in env], axis=0)
        ch = class_hourly(bundle, year)
        model_imp = ch["import"].to_numpy() if "import" in ch.columns else np.zeros(T)
        meas = measured_corridor_import(year)
        util = float(
            np.nanmean(model_imp[idx] / np.where(cap[idx] > 0, cap[idx], np.nan))
        )
        print(f"\n  --- {year}: Sep-Dec surplus belly, n = {idx.size} h ---")
        print(
            f"      corridor import ceiling (sum of legs)   {cap[idx].mean():9.0f} MW"
        )
        print(
            f"      model import                            {model_imp[idx].mean():9.0f} MW   (utilisation {util:.3f})"
        )
        if meas is not None and np.isfinite(meas[idx]).any():
            m = float(np.nanmean(meas[idx]))
            print(f"      MEASURED corridor import (EIA-930)      {m:9.0f} MW")
            print(
                f"      model - measured                        {model_imp[idx].mean() - m:+9.0f} MW"
                "   <- positive => the model already OVER-imports"
            )
            out[year] = {
                "cap": float(cap[idx].mean()),
                "model": float(model_imp[idx].mean()),
                "measured": m,
                "utilisation": util,
            }
        else:
            print("      MEASURED corridor import: unavailable")
            out[year] = {
                "cap": float(cap[idx].mean()),
                "model": float(model_imp[idx].mean()),
                "measured": None,
                "utilisation": util,
            }
    return out


# ---------------------------------------------------------------------------
# §D — the unit sidecar's first dividend: ask A2's D1 becomes computable
# ---------------------------------------------------------------------------
def section_d(bundle: Path, years: tuple[int, ...]) -> dict:
    """D: the plant-level ONLINE reserve measure ask A2's D1 was BLOCKED on.

    ``docs/handoffs/caiso-131-c3c-c3a-ask-2026-07-27.md`` §4 records D1 as
    blocked by a data gap: the plant-level ONLINE (synchronized) headroom PJM
    already uses needs per-unit hourly dispatch AND the availability-derated
    capacity bound, and no slim bundle carried either. The ``unit_hourly``
    sidecar carries both, so D1 is now a read.

    D1 as filed: *"Compute plant-level online (synchronized) headroom on the
    keeper and show it is < 5 GW in the model's own tightest decile. If it is
    not, A2 is inert and is killed before any solve."*

    **Two things this section reports honestly, and does not adjudicate.**

    1. The ask's §4 premise — *"CAISO's overlay still evaluates
       ``reserve_headroom`` on total fleet headroom"* — does not match the code
       as it stands: ``results.scarcity.caiso_scarcity_overlay`` calls
       ``reserve_headroom`` (which already splits online/offline through
       ``_online_plant_mask``) and passes ``reserves_online_mw=r_online`` into
       ``ordc_adder``, where it drives the half-hour LOLP term. What is large is
       ``reserves_total = r_online + r_offline + import_headroom``, the
       full-hour term's argument. Recorded as a fact about the code; what A2
       should therefore re-specify is A2's question.
    2. The number below is the **online THERMAL** headroom — the component the
       unit sidecar uniquely unblocks. The overlay's own ``r_online`` also
       carries storage headroom and curtailed-renewable headroom, neither of
       which this sidecar holds (storage lives in ``storage_<y>.parquet``;
       renewable potential is not persisted at all). So this is a *lower bound*
       on ``r_online``, and it is the right object for D1's kill test, which
       asks whether the online measure is materially smaller than the 12-13 GW
       total-headroom surface ``FINDING-caiso131`` §4 measured.

    **This is D1 and only D1.** A2's D2 (the §2 E1/E2 spillover pre-check) and
    D3 (no fitted parameter) are NOT run here, and arming A2 remains a separate
    owner ask with its own prereg (rule 1 ``[R-STRUCT]``).
    """
    from market_sim.results.scarcity import QUICK_START_FUEL_TYPES, RESERVE_FUEL_TYPES

    print("\n" + "=" * 96)
    print("D — ask A2's D1: plant-level ONLINE reserve (unblocked by the unit sidecar)")
    print("=" * 96)
    print(
        "  Gate as filed (ask §4 D1): the ONLINE measure must be < 5 GW in the model's\n"
        "  own tightest decile, else A2 is INERT and is killed before any solve.\n"
        "  Online is decided at the PLANT level (every tranche of a plant whose summed\n"
        "  dispatch exceeds 1 MW), exactly as results.scarcity._online_plant_mask does.\n"
        "  Rows are the THERMAL component (RESERVE_FUEL_TYPES) — the part this sidecar\n"
        "  unblocks; the overlay's own r_online adds storage + curtailed-renewable\n"
        "  headroom, which no committed sidecar carries. Lower bound, stated as one."
    )
    out: dict[int, dict] = {}
    for year in years:
        path = bundle / "hourly" / f"unit_hourly_{year}.parquet"
        if not path.exists():
            print(
                f"\n  --- {year}: no unit_hourly_{year}.parquet in this bundle — SKIPPED ---"
            )
            continue
        d = pd.read_parquet(path)
        d = d[d["pass"] == "P1"]
        plant_mw = d.groupby(["plant_code", "hour"], observed=True)["mw"].sum()
        d = d.join(plant_mw.rename("plant_mw"), on=["plant_code", "hour"])
        therm = d[d["fuel"].isin(sorted(RESERVE_FUEL_TYPES))]
        head = therm["cap_mw"] - therm["mw"]
        by_hour = lambda sel: (  # noqa: E731
            head[sel]
            .groupby(therm.loc[sel, "hour"])
            .sum()
            .reindex(range(T), fill_value=0.0)
            .to_numpy()
        )
        total = by_hour(therm["hour"].notna())
        online = by_hour(therm["plant_mw"] > 1.0)
        offline_quick = by_hour(
            (therm["plant_mw"] <= 1.0)
            & therm["fuel"].isin(sorted(QUICK_START_FUEL_TYPES))
        )
        print(
            f"\n  --- {year}: {d['unit_id'].nunique()} LP units, {len(d):,} unit-hours ---"
        )
        print(f"      {'measure':<34} {'min':>9} {'p10':>9} {'median':>9}")
        for label, arr in (
            ("TOTAL thermal headroom", total),
            ("PLANT-LEVEL ONLINE thermal (A2 D1)", online),
            ("offline quick-start thermal", offline_quick),
        ):
            print(
                f"      {label:<34} {arr.min():>9.0f} {np.percentile(arr, 10):>9.0f} "
                f"{np.median(arr):>9.0f}"
            )
        p10 = float(np.percentile(online, 10))
        print(
            f"      >>> D1: tightest-decile ONLINE thermal = {p10:,.0f} MW vs the "
            f"5,000 MW gate -> "
            f"{'PASS — the online measure IS materially smaller' if p10 < 5000 else 'FAIL — D1 kills A2 before any solve'}"
            f"   (CAISO MCL {1400:,} MW, sigma {2500:,} MW)"
        )
        out[year] = {
            "total_min": float(total.min()),
            "online_min": float(online.min()),
            "online_p10": p10,
            "online_median": float(np.median(online)),
            "d1_pass": bool(p10 < 5000),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(int(y) for y in args.years)

    print(
        "caiso-133 — separating the binding IMPORT-direction limit. NO LP, NOTHING ARMED."
    )
    print(f"bundle: {args.bundle}   years: {years}")

    a = section_a(years)
    b = section_b(args.bundle, years)
    c = section_c(args.bundle, years)
    d = section_d(args.bundle, years)

    print("\n" + "=" * 96)
    print("SUMMARY")
    print("=" * 96)
    print(
        "  A (reachability, no LP): link TTC "
        f"{'UNREACHABLE' if a['ttc_unreachable'] else 'reachable'}; seam row "
        f"{'UNREACHABLE' if a['seam_unreachable'] else 'reachable'}."
    )
    if b:
        worst = max(
            (
                r["max_abs_residual"]
                for yr in b.values()
                for r in yr.values()
                if isinstance(r, dict)
            ),
            default=float("nan"),
        )
        print(f"  B (measured duals): identity closes to {worst:.2e} $/MWh worst-case.")
    else:
        print("  B: SKIPPED — the bundle carries no network sidecar.")
    if c:
        over = [
            f"{y}: {v['model'] - v['measured']:+.0f} MW"
            for y, v in c.items()
            if v["measured"]
        ]
        if over:
            print(
                f"  C (rule 14): model - measured import in the defect hours — "
                f"{'; '.join(over)}."
            )
    if d:
        print(
            "  D (ask A2 D1): tightest-decile ONLINE reserve — "
            + "; ".join(f"{y}: {v['online_p10']:,.0f} MW" for y, v in d.items())
            + f" -> {'PASS' if all(v['d1_pass'] for v in d.values()) else 'FAIL'}."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
