#!/usr/bin/env python3
"""Fetch CAISO OASIS intertie scheduling-point LMPs and build the measured-hub
import-price input for the model's ``caiso_import_hub_prices`` mechanism.

The priced-import node prices each tranche at the WECC neighbor hub it proxies
(DIAGNOSIS-caiso-import-ladder-2026-06-19, lever A). That hub price is the OASIS
DAM LMP at the **intertie scheduling points** — Malin / Captain Jack / NOB for the
PNW (Mid-C) blocks, Palo Verde / Mead for the desert-SW blocks. This fetches them
(same PRC_LMP DAM query the hub fetch already uses, different nodes) and writes
them on the model's dense 8760-hour local (Pacific) calendar:

  data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet
    columns: year, hour (0..8759), hub in {MALIN, PALOVRDE}, price ($/MWh, the
             delivered nodal LMP = energy + congestion + loss; see below)

PRICE IS THE FULL DELIVERED NODAL LMP, NOT JUST ENERGY (changed 2026-06-23,
claude/caiso-per-hub-intertie-lmp). OASIS PRC_LMP returns the LMP as five rows
per hour-node (LMP_TYPE in {LMP, MCE, MCC, MCL, MGHG}); we keep the SUM of the
energy (MCE), congestion (MCC) and marginal-loss (MCL) components — the full
nodal LMP MINUS the GHG component (MGHG). Why:
  * The earlier MCE-only fetch made MALIN and PALOVRDE BYTE-IDENTICAL: MCE is the
    single system marginal energy price, identical at every WECC node by
    construction, so the model saw a diurnal *level* but no PNW(Mid-C) vs
    desert-SW(Palo Verde) *basis*. MCC and MCL are exactly the components that
    differ by node, so summing them in makes MALIN != PALOVRDE (the gap behind
    DIAGNOSIS-caiso-body-overprice-2026-06-21).
  * We DROP MGHG because the import injector re-adds the CARB border-carbon adder
    per tranche (clean hydro/solar pays none); folding MGHG in here would
    double-count it. At these external intertie scheduling points MGHG is ~0
    anyway, but excluding it keeps the carbon treatment unambiguous.
The measured MCL now carries the real marginal loss at the scheduling point, so
the modeled multiplicative line-loss markup in CAISO_IMPORT_DELIVERY_BASIS is
dropped in the injector to avoid double-counting (only the OATT wheel, a separate
external BAA charge not in CAISO's nodal LMP, is still added) — see
transmission.inject_caiso_import_hub_prices (rules #11/#12: prefer the measured
loss, ground the change, don't residual-fit).

oasis.caiso.com is reachable from the remote Claude env (verified 2026-06-22);
it can also run on a GitHub runner — see .github/workflows/fetch-caiso-intertie-lmp.yml.
The intertie APNode names below are CAISO's published scheduling points but vary by
registry vintage — run ``--probe`` first (one 1-day call per node) to confirm which
resolve before the full pull, exactly like fetch_caiso_oasis's "validate on first run".

Usage:
    python scripts/data/fetch_caiso_intertie_lmp.py --probe --years 2024
    python scripts/data/fetch_caiso_intertie_lmp.py --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the proven OASIS request machinery (URL build, zip retry, CSV extract).
# Running this as ``python scripts/data/fetch_caiso_intertie_lmp.py`` puts ``scripts/``
# on sys.path[0], not the repo root, so the sibling import below fails. Put the
# repo root first so ``scripts`` resolves as a namespace package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.data.fetch_caiso_oasis import _extract_csv, _fetch, _url

REPO = Path(__file__).resolve().parent.parent.parent
OUT_PARQUET = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "wecc_intertie_lmp_hourly_CAISO.parquet"
)

PRC_LMP_DAM = {"queryname": "PRC_LMP", "market_run_id": "DAM", "version": "12"}

# model hub -> OASIS intertie APNodes (averaged within a hub), confirmed by the
# mode=probe run on 2024-06-01: MALIN_5_N101, CAPTJACK_5_N003 and
# PALOVRDE_ASR-APND resolve in the current registry vintage; NOB_2_N101 and
# MEAD_2_N501 return no data and are dropped (each hub still resolves via its
# remaining node). MALIN = COI/PDCI Pacific-NW; PALOVRDE = Path-46 desert-SW.
INTERTIE_NODES: dict[str, list[str]] = {
    "MALIN": ["MALIN_5_N101", "CAPTJACK_5_N003"],
    "PALOVRDE": ["PALOVRDE_ASR-APND"],
}

# OASIS PRC_LMP component types whose SUM is the delivered nodal LMP we keep:
# energy + congestion + marginal-loss. We deliberately omit MGHG (the GHG
# component) because the import injector re-adds CARB border carbon per tranche.
# MCE is system-wide identical at every node; MCC/MCL are what differ by node and
# give MALIN (PNW) vs PALOVRDE (desert-SW) their basis separation.
_DELIVERED_LMP_COMPONENTS = ("MCE", "MCC", "MCL")

CAISO_TZ = "America/Los_Angeles"
# Cumulative first-hour-of-year for each month on the fixed NON-leap calendar
# (mirrors scripts/data/derive_actual_lmp._MONTH_START_HOUR). Feb 29 is dropped.
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()
_HOURS_PER_YEAR = 8760
# OASIS PRC_LMP DAM retention boundary (re-probed 2026-06-23): the window is
# rolling — it advanced from ~2023-03-10 to 2023-03-12 in a day. Data before the
# boundary returns ERR 1000 (aged out) and is unrecoverable; it only ages out
# further over time, so 2023 Jan 1–Mar 11 can no longer be completed from OASIS.
# 2024/2025 start at Jan 1 as usual; only 2023 is clamped. The adaptive crawl in
# _fetch_node_year self-heals if the boundary advances past this date again.
_OASIS_RETENTION_START = dt.date(2023, 3, 12)


def _hour_index(ts: pd.Series) -> np.ndarray:
    """Local timestamps -> fixed non-leap hour-of-year (Feb 29 -> -1)."""
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in ts.dt.month])
    idx = base + (ts.dt.day.to_numpy() - 1) * 24 + ts.dt.hour.to_numpy()
    return np.where((ts.dt.month == 2) & (ts.dt.day == 29), -1, idx)


def _fetch_node_year(
    node: str, year: int, window: int, sleep_s: float, deadline: float | None
) -> pd.DataFrame | None:
    """Fetch one node's DAM LMP for a year with adaptive window sizing.

    OASIS hangs (a 60s read timeout, or an ``ERR_CODE`` for aged-out ranges) on
    PRC_LMP windows past its per-report limit — a fixed 25-day window timed out
    on *every* call and fetched nothing. Mirror the proven crawl in
    ``fetch_caiso_oasis.fetch_dataset``: on a failed/empty pull, halve the
    window and retry the same start; on success, keep the working size (never
    grow back above it, so we don't oscillate into the hang zone). At a 1-day
    window that still fails, skip the day (usually aged out of OASIS retention).
    """
    frames: list[pd.DataFrame] = []
    end = min(dt.date(year + 1, 1, 1), dt.date.today())
    # OASIS PRC_LMP retention aged out everything before ~2023-03-10 (ERR 1000);
    # start there for 2023 instead of crawling ~10 weeks of dead Jan-Feb days
    # one-at-a-time (the old start at Jan 1 looked hung for many minutes).
    cur = max(dt.date(year, 1, 1), _OASIS_RETENTION_START)
    size = window
    while cur < end:
        if deadline is not None and time.monotonic() > deadline:
            print("  deadline reached — stopping", flush=True)
            break
        win_end = min(cur + dt.timedelta(days=size), end)
        url = _url(PRC_LMP_DAM, cur, win_end, node)
        payload = _fetch(url, sleep_s=sleep_s)
        time.sleep(sleep_s)
        result = _extract_csv(payload) if payload is not None else None
        if result is not None:
            frames.append(pd.read_csv(io.BytesIO(result[1])))
            # Log every success — the loop is otherwise silent and looks hung.
            print(f"    {node} {cur:%Y-%m-%d}..{win_end:%Y-%m-%d}: ok", flush=True)
            cur = win_end
        elif size > 1:
            size = max(1, size // 2)
            print(
                f"    {node} {cur:%Y-%m-%d}: no data at this window — "
                f"halving to {size}d",
                flush=True,
            )
        else:
            print(
                f"    {node}: single-day window {cur:%Y-%m-%d} failed — skipping",
                file=sys.stderr,
                flush=True,
            )
            cur = win_end
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def _to_hourly_nodal_lmp(df: pd.DataFrame, year: int) -> np.ndarray | None:
    """Raw OASIS PRC_LMP rows -> (8760,) delivered nodal LMP on the local calendar.

    OASIS returns PRC_LMP in LONG form: one row per (interval, LMP_TYPE) with the
    value in the ``MW`` column and the timestamp in ``INTERVALSTARTTIME_GMT``. We
    pivot the component types to columns and SUM the energy (MCE) + congestion
    (MCC) + loss (MCL) components — the full nodal LMP minus the GHG component
    (MGHG), which the import injector re-adds as per-tranche CARB border carbon
    (see the module docstring). MCC/MCL are what make MALIN and PALOVRDE diverge.
    """
    cols = {c.lower(): c for c in df.columns}
    ts_col = cols.get("intervalstarttime_gmt") or cols.get("interval_start_gmt")
    type_col = cols.get("lmp_type")
    val_col = cols.get("mw")
    if ts_col is None or type_col is None or val_col is None:
        return None
    sub = df[df[type_col].astype(str).isin(_DELIVERED_LMP_COMPONENTS)]
    if sub.empty:
        return None
    # Pivot to one column per component, indexed by the physical (UTC) interval;
    # aggfunc="first" collapses any accidental duplicate component rows without
    # inflating the sum. DST fall-back keeps two distinct UTC intervals here —
    # they map to the same Pacific hour and are averaged below.
    wide = sub.pivot_table(
        index=ts_col, columns=type_col, values=val_col, aggfunc="first"
    )
    if "MCE" not in wide.columns:
        return None  # energy component missing — unusable
    present = [c for c in _DELIVERED_LMP_COMPONENTS if c in wide.columns]
    nodal = wide[present].sum(axis=1, skipna=True)  # MCE + MCC + MCL = delivered
    ts = pd.Series(pd.to_datetime(nodal.index, utc=True)).dt.tz_convert(CAISO_TZ)
    hi = _hour_index(ts)
    vals = pd.to_numeric(nodal, errors="coerce").to_numpy()
    keep = (hi >= 0) & (hi < _HOURS_PER_YEAR) & np.isfinite(vals)
    out = np.full(_HOURS_PER_YEAR, np.nan)
    # Average duplicate (DST fall-back) hours; spring-forward stays NaN.
    s = pd.Series(vals[keep]).groupby(hi[keep]).mean()
    out[s.index.to_numpy()] = s.to_numpy()
    return out if np.any(np.isfinite(out)) else None


def probe(years: list[int], sleep_s: float) -> int:
    """One 1-day call per node to confirm which APNode names resolve."""
    year = years[0]
    ok_any = False
    for hub, nodes in INTERTIE_NODES.items():
        for node in nodes:
            url = _url(PRC_LMP_DAM, dt.date(year, 6, 1), dt.date(year, 6, 2), node)
            payload = _fetch(url, sleep_s=sleep_s)
            time.sleep(sleep_s)
            result = _extract_csv(payload) if payload is not None else None
            if result is None:
                print(f"  {hub:9s} {node}: NO DATA — check the node name")
                continue
            n = len(pd.read_csv(io.BytesIO(result[1])))
            print(f"  {hub:9s} {node}: OK — {n} rows for {year}-06-01")
            ok_any = True
    print(
        "probe complete."
        if ok_any
        else "probe: NO node returned data — fix INTERTIE_NODES."
    )
    return 0 if ok_any else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--window",
        type=int,
        default=12,
        help="initial window size in days (adaptively halved; 25 "
        "reliably hangs OASIS, so start below it)",
    )
    ap.add_argument("--sleep", type=float, default=5.0)
    ap.add_argument(
        "--probe",
        action="store_true",
        help="validate the intertie node names with one cheap call each",
    )
    ap.add_argument("--deadline-minutes", type=float, default=None)
    args = ap.parse_args()

    if args.probe:
        sys.exit(probe(args.years, args.sleep))

    deadline = (
        time.monotonic() + args.deadline_minutes * 60.0
        if args.deadline_minutes
        else None
    )

    existing = pd.read_parquet(OUT_PARQUET) if OUT_PARQUET.exists() else None
    records = []
    for year in args.years:
        for hub, nodes in INTERTIE_NODES.items():
            series = []
            for node in nodes:
                print(f"=== {year} {hub} {node} ===", flush=True)
                raw = _fetch_node_year(node, year, args.window, args.sleep, deadline)
                if raw is None:
                    print(f"  {node}: no data — skipped", file=sys.stderr)
                    continue
                hourly = _to_hourly_nodal_lmp(raw, year)
                if hourly is not None:
                    series.append(hourly)
            if not series:
                print(
                    f"  {hub} {year}: no node resolved — hub left to the static ladder",
                    file=sys.stderr,
                )
                continue
            price = np.nanmean(np.vstack(series), axis=0)
            # Write the DENSE 8760-hour calendar: emit every hour, NaN included.
            # measured_import_hub_prices expects a dense per-(year,hub) series and
            # interpolates the lone DST spring-forward gap (limit=2); a SPARSE
            # parquet (skipping NaN hours) would land at 8759 rows for a clean
            # year and the loader's length check would reject it, silently
            # dropping the whole year back to the static ladder. A genuine
            # multi-week hole (2023 Jan-Feb, aged out of OASIS) stays NaN here and
            # is left to the ladder by the loader's all-finite gate (intended).
            for h in range(_HOURS_PER_YEAR):
                val = float(price[h])
                records.append(
                    {
                        "year": year,
                        "hour": h,
                        "hub": hub,
                        "price": round(val, 4) if np.isfinite(val) else np.nan,
                    }
                )

    if not records:
        print("no intertie data fetched — nothing written.", file=sys.stderr)
        sys.exit(1)
    out = pd.DataFrame.from_records(records)
    if existing is not None:
        # Replace only the (year, hub) pairs we just fetched; keep the rest.
        fetched = set(zip(out["year"], out["hub"]))
        keep = existing[
            ~existing.apply(lambda r: (r["year"], r["hub"]) in fetched, axis=1)
        ]
        out = pd.concat([keep, out], ignore_index=True)
    out = out.sort_values(["year", "hub", "hour"]).reset_index(drop=True)
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PARQUET, index=False)
    print(
        f"wrote {OUT_PARQUET.relative_to(REPO)} ({len(out)} rows, "
        f"hubs {sorted(out['hub'].unique())})"
    )


if __name__ == "__main__":
    main()
