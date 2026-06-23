#!/usr/bin/env python3
"""Fetch CAISO OASIS intertie scheduling-point LMPs and build the measured-hub
import-price input for the model's ``caiso_import_hub_prices`` mechanism.

The priced-import node prices each tranche at the WECC neighbor hub it proxies
(DIAGNOSIS-caiso-import-ladder-2026-06-19, lever A). That hub price is the OASIS
DAM LMP at the **intertie scheduling points** — Malin / Captain Jack / NOB for the
PNW (Mid-C) blocks, Palo Verde / Mead for the desert-SW blocks. This fetches them
(same PRC_LMP DAM query the hub fetch already uses, different nodes), takes the
energy component (MCE — the per-tranche CARB border carbon is re-added by the
injector), maps the nodes to the two model hubs, and writes them on the model's
dense 8760-hour local (Pacific) calendar:

  data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet
    columns: year, hour (0..8759), hub in {MALIN, PALOVRDE}, price ($/MWh, the
             MCE energy component of the intertie LMP)

oasis.caiso.com is reachable from the remote Claude env (verified 2026-06-22);
it can also run on a GitHub runner — see .github/workflows/fetch-caiso-intertie-lmp.yml.
The intertie APNode names below are CAISO's published scheduling points but vary by
registry vintage — run ``--probe`` first (one 1-day call per node) to confirm which
resolve before the full pull, exactly like fetch_caiso_oasis's "validate on first run".

Usage:
    python scripts/fetch_caiso_intertie_lmp.py --probe --years 2024
    python scripts/fetch_caiso_intertie_lmp.py --years 2023 2024 2025
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
# Running this as ``python scripts/fetch_caiso_intertie_lmp.py`` puts ``scripts/``
# on sys.path[0], not the repo root, so the sibling import below fails. Put the
# repo root first so ``scripts`` resolves as a namespace package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.fetch_caiso_oasis import _extract_csv, _fetch, _url

REPO = Path(__file__).resolve().parent.parent
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

CAISO_TZ = "America/Los_Angeles"
# Cumulative first-hour-of-year for each month on the fixed NON-leap calendar
# (mirrors scripts/derive_actual_lmp._MONTH_START_HOUR). Feb 29 is dropped.
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


def _to_hourly_energy(df: pd.DataFrame, year: int) -> np.ndarray | None:
    """Raw OASIS rows -> (8760,) MCE energy component on the local calendar.

    OASIS PRC_LMP DAM CSV is long-format: one row per ``LMP_TYPE``
    (LMP / MCC / MCE / MCL / MGHG) with the $/MWh value in the (misnamed) ``MW``
    column and the interval start in ``INTERVALSTARTTIME_GMT``. We keep the MCE
    energy component (verified: LMP = MCE + MCC + MCL + MGHG); the per-tranche
    CARB border carbon is re-added by the injector.
    """
    needed = {"LMP_TYPE", "MW", "INTERVALSTARTTIME_GMT"}
    if not needed.issubset(df.columns):
        return None
    rows = df[df["LMP_TYPE"] == "MCE"]
    if rows.empty:
        return None
    ts = pd.to_datetime(rows["INTERVALSTARTTIME_GMT"], utc=True).dt.tz_convert(CAISO_TZ)
    hi = _hour_index(ts)
    mce = pd.to_numeric(rows["MW"], errors="coerce").to_numpy()
    keep = (hi >= 0) & (hi < _HOURS_PER_YEAR) & np.isfinite(mce)
    out = np.full(_HOURS_PER_YEAR, np.nan)
    # Average duplicate (DST fall-back) hours; spring-forward stays NaN.
    s = pd.Series(mce[keep]).groupby(hi[keep]).mean()
    out[s.index.to_numpy()] = s.to_numpy()
    return out


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
                hourly = _to_hourly_energy(raw, year)
                if hourly is not None:
                    series.append(hourly)
            if not series:
                print(
                    f"  {hub} {year}: no node resolved — hub left to the static ladder",
                    file=sys.stderr,
                )
                continue
            price = np.nanmean(np.vstack(series), axis=0)
            # Write the full 8760-hour grid, NaN hours included. The consumer
            # (eia_loader._caiso_import_hub_prices) requires a complete 8760-row
            # series per (year, hub): it interpolates the lone interior DST
            # spring-forward NaN but rejects any series shorter than 8760. If we
            # drop NaN hours, a complete year loses its DST row (8759 rows) and
            # the whole year falls back onto the static ladder.
            for h in range(_HOURS_PER_YEAR):
                v = float(price[h])
                records.append(
                    {
                        "year": year,
                        "hour": h,
                        "hub": hub,
                        "price": round(v, 4) if np.isfinite(v) else np.nan,
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
