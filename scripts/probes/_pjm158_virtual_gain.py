"""pjm-158 Phase 0.2/0.3 — the PJM DA virtual layer's clearing gain and its
rung-compression exactness.

pjm-157 §1.1 established that ``ScenarioConfig.pjm_da_virtual_bids`` clears
**+8.13 / +7.50 / −2.23 TWh** away from its own rule-13 admissibility anchor in
the three TUNED years, and proposed a causal channel: the layer converts an
hourly price error into a quantity error, because ``net(λ)`` is monotone in the
dual.  This probe measures that channel directly on the measured corpus.

Three questions, all answered on the IN-SAMPLE 2023-2025 curves only (the raw
corpus is fetched by ``scripts/data/fetch_pjm_da_virtuals.py``, whose default
year span is exactly 2023-2025 — no out-of-training data is read, and nothing
here solves or scores anything, so the active holdout freeze is untouched):

* **§1 the anchor** — clear each hour's raw submitted net curve at the ACTUAL
  DA price and confirm the annual net is ≈ 0 (the pjm-105 reference the
  mechanism's admissibility argument rests on).
* **§2 the gain** — ``dNet/dλ``: how many MWh of cleared virtual a $1/MWh dual
  error buys, by season and hour-of-day.  Then the ONE-STEP PREDICTION: clear
  the same measured curve at ``actual DA + the model's own measured hourly
  price error`` and check whether that alone reproduces the observed
  +8.13/+7.50/−2.23 deviation.  If it does, the deviation is a price-error
  transmission, not a curve-rendering defect.
* **§3 the compression** — is the ``N_RUNGS``-per-side equal-MW ladder
  representation-exact, as ``virtual_bids`` claims ("resolution only, never
  tunable values")?  Compares the rendered ladder's ``net(λ)`` against the raw
  curve's at the prices the model actually visits, and measures any systematic
  displacement of the crossing price ``λ0``.

Run:  .venv/bin/python scripts/probes/_pjm158_virtual_gain.py
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.data.virtual_bids import N_RUNGS, _hourly_net_rungs  # noqa: E402

TWH = 1e6
YEARS = (2023, 2024, 2025)
BUNDLE = "results/calibration/pjm152_collapse_A"
RUN_PAYLOAD = "frontend/data/backcast/runs/2026-08-04-pjm-152-collapse.js"
RAW = Path("data/raw/pjm-da-virtuals")

#: PJM published hub set used as the RTO Day-Ahead reference price.  The feed
#: is RTO-aggregated, so its clearing reference must be RTO-wide too.
HUB_ALL = "ALL_HUBS_MEAN"


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------
def load_curve(year: int) -> pd.DataFrame:
    """Raw submitted INC/DEC price points for one year, on the model clock.

    Mirrors ``virtual_bids._load_bids_frame`` (same EPT parse, same DST
    fall-back averaging, same EIA-930 local-clock join) so the probe and the
    LP read identical curves.
    """
    from market_sim.data.virtual_bids import _load_bids_frame

    bids = _load_bids_frame("PJM", year, 8760)
    if bids is None:
        raise FileNotFoundError(f"no hrl_da_incs_decs parquets for {year} in {RAW}")
    return bids


def actual_da_price(year: int) -> np.ndarray:
    """Hourly RTO Day-Ahead reference price ($/MWh) on the model's 8760 clock.

    Simple mean of PJM's twelve published hubs' ``total_lmp_da`` — the feed
    the virtual curves are submitted into is RTO-aggregated, so the reference
    must be RTO-wide rather than a single hub.
    """
    path = Path("data/raw/lmp-data") / f"PJM_{year}_rt_da_monthly_lmps.csv"
    f = pd.read_csv(path)
    f["ept"] = pd.to_datetime(f["datetime_beginning_ept"], format="mixed")
    f = f[f["ept"].dt.year == year]
    s = f.groupby("ept")["total_lmp_da"].mean().sort_index()
    return _on_model_clock(s, year)


def _on_model_clock(s: pd.Series, year: int) -> np.ndarray:
    """Reindex an EPT-stamped hourly series onto the model's 8760 row order."""
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    df = _eia_hourly_frame_filled("PJM", year)
    local = pd.DatetimeIndex(df["Local time"])[:8760]
    return s.reindex(local).ffill().bfill().to_numpy(dtype=float)


def model_zonal(year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Model P1 zonal duals, zonal load shares and the load-weighted system dual.

    The LP splits each rung across zones by ``zone_share = load / Σ load`` and
    each zonal piece clears against THAT zone's own dual, so reproducing the
    LP's clearing needs the zonal duals, not just the system average.  The
    ``PJM_external`` star node carries no physical load and is excluded, exactly
    as ``build_pjm_da_virtual_units`` sees it (the virtual units are built over
    the physical zonal demand matrix).

    Returns ``(price (n_zone, T), share (n_zone, T), system dual (T,))``.
    """
    sy = pd.read_parquet(f"{BUNDLE}/hourly/system_{year}.parquet")
    sy = sy[(sy["pass"] == "P1") & (sy["zone"] != "PJM_external")]
    price = sy.pivot_table(index="zone", columns="hour", values="price").sort_index()
    dem = sy.pivot_table(index="zone", columns="hour", values="demand").sort_index()
    p = price.to_numpy(dtype=float)
    d = dem.to_numpy(dtype=float)
    share = d / np.maximum(d.sum(axis=0, keepdims=True), 1.0)
    return p, share, (p * share).sum(axis=0)


def model_cleared(year: int) -> tuple[float, float]:
    """Model's cleared (VIRTUAL_INC, VIRTUAL_DEC) energy in TWh, P1."""
    ch = pd.read_parquet(f"{BUNDLE}/hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    g = ch.groupby("klass")["mw"].sum() / TWH
    return float(g.get("VIRTUAL_INC", 0.0)), float(g.get("VIRTUAL_DEC", 0.0))


# ---------------------------------------------------------------------------
# the raw net curve, evaluated
# ---------------------------------------------------------------------------
def build_hour_arrays(bids: pd.DataFrame) -> list[tuple[np.ndarray, np.ndarray]]:
    """Per-hour (ascending price, cumulative-net-drop) arrays of the raw curve.

    ``net(λ) = Σ_{DEC ≥ λ} dec − Σ_{INC ≤ λ} inc`` starts at ``Σ dec`` and
    falls by ``dec_p + inc_p`` as λ crosses each price point p upward, so it
    is fully described by (sorted prices, total_dec, cumulative block sums).
    Returns one entry per model hour, index-aligned to 0..8759.
    """
    out: list[tuple[np.ndarray, np.ndarray] | None] = [None] * 8760
    sub = bids[(bids["inc"] > 0.0) | (bids["dec"] > 0.0)]
    for t, g in sub.groupby("t", sort=False):
        p = g["price"].to_numpy(dtype=float)
        block = (g["dec"] + g["inc"]).to_numpy(dtype=float)
        total_dec = float(g["dec"].sum())
        o = np.argsort(p)
        p, block = p[o], block[o]
        # net just BELOW price p[i] is total_dec - Σ_{j<i} block[j]
        out[int(t)] = (p, total_dec - (np.cumsum(block) - block))
    return out


def eval_net(hours: list, lam: np.ndarray) -> np.ndarray:
    """``net(λ_t)`` in MW for each hour (+ = net virtual DEMAND).

    At a dual strictly between two submitted price points the net is the level
    of the step to the left; ``searchsorted(..., "right")`` picks it, and a
    dual exactly at a price point takes the post-crossing level (that price's
    demand has stopped buying and its supply has started selling).
    """
    out = np.zeros(8760)
    for t, rec in enumerate(hours):
        if rec is None:
            continue
        p, lvl = rec
        i = int(np.searchsorted(p, lam[t], side="right"))
        out[t] = lvl[0] if i == 0 else (lvl[i - 1] - (lvl[i - 1] - _below(lvl, i)))
    return out


def _below(lvl: np.ndarray, i: int) -> float:
    """Net level strictly ABOVE the i-th price point (post-crossing)."""
    return lvl[i] if i < lvl.size else 0.0


def eval_net_fast(hours: list, lam: np.ndarray) -> np.ndarray:
    """Vectorized ``net(λ_t)`` in MW (+ = net virtual DEMAND)."""
    out = np.zeros(8760)
    for t, rec in enumerate(hours):
        if rec is None:
            continue
        p, lvl_below = rec
        i = int(np.searchsorted(p, lam[t], side="right"))
        # lvl_below[i] is the net level just BELOW p[i]; after crossing p[i-1]
        # the level is lvl_below[i] (or 0 past the top of the curve).
        out[t] = lvl_below[i] if i < lvl_below.size else 0.0
    return out


def gain(hours: list, lam: np.ndarray, delta: float) -> np.ndarray:
    """Central-difference ``dNet/dλ`` at λ_t, MW per $/MWh (≤ 0 by monotonicity)."""
    up = eval_net_fast(hours, lam + delta)
    dn = eval_net_fast(hours, lam - delta)
    return (up - dn) / (2.0 * delta)


# ---------------------------------------------------------------------------
# §3 — the rendered ladder
# ---------------------------------------------------------------------------
def ladder_net(ladder: tuple, lam: np.ndarray) -> np.ndarray:
    """``net(λ_t)`` of the RENDERED rung ladder, MW (+ = net virtual DEMAND).

    Applies the LP's own clearing logic to ``_hourly_net_rungs`` output: a DEC
    rung priced at ``b`` withdraws (adds DA demand) whenever the dual is below
    ``b``; an INC rung offered at ``o`` produces whenever the dual is above
    ``o``.
    """
    dec_mw, dec_p, inc_mw, inc_p = ladder
    lam_r = lam[None, :]
    return (dec_mw * (dec_p > lam_r)).sum(axis=0) - (inc_mw * (inc_p < lam_r)).sum(
        axis=0
    )


def zonal_sum(fn, price_z: np.ndarray, share_z: np.ndarray) -> np.ndarray:
    """Σ_z share_z(t) · net(λ_z(t)) — the LP's own zone-by-zone clearing."""
    out = np.zeros(price_z.shape[1])
    for zi in range(price_z.shape[0]):
        out += share_z[zi] * fn(price_z[zi])
    return out


def crossing_price(hours: list) -> np.ndarray:
    """Raw curve's crossing price λ0 per hour (the price where net hits 0)."""
    out = np.full(8760, np.nan)
    for t, rec in enumerate(hours):
        if rec is None:
            continue
        p, lvl_below = rec
        j = np.nonzero(lvl_below <= 0.0)[0]
        out[t] = p[j[0] - 1] if j.size and j[0] > 0 else (p[-1] if not j.size else p[0])
    return out


def ladder_crossing(bids: pd.DataFrame, n_rungs: int) -> tuple[np.ndarray, np.ndarray]:
    """Rendered ladder's crossing bracket: (top DEC rung price, bottom INC price)."""
    dec_mw, dec_p, inc_mw, inc_p = _hourly_net_rungs(bids, 8760, n_rungs)
    top_dec = np.where(dec_mw.max(axis=0) > 0, dec_p.max(axis=0), np.nan)
    bot_inc = np.where(inc_mw.max(axis=0) > 0, inc_p.min(axis=0), np.nan)
    return top_dec, bot_inc


# ---------------------------------------------------------------------------
def lmp_delta_hr(year: int) -> np.ndarray | None:
    """The run payload's committed model−actual hourly $/MWh series."""
    import re

    src = Path(RUN_PAYLOAD).read_text(encoding="utf-8")
    blob = re.search(r'runGz\["[^"]+"\]="([^"]+)"', src).group(1)
    payload = json.loads(gzip.decompress(base64.b64decode(blob)))
    y = payload["years"].get(str(year), {})
    if "lmpDeltaHr" not in y:
        return None
    raw = np.frombuffer(base64.b64decode(y["lmpDeltaHr"]), dtype="<i2").astype(float)
    return np.resize(raw, 8760)


def season(year: int) -> np.ndarray:
    """Season label per model hour."""
    m = pd.date_range(f"{year}-01-01", periods=8760, freq="h").month.to_numpy()
    lab = np.full(8760, "shoulder", dtype=object)
    lab[np.isin(m, [12, 1, 2])] = "winter"
    lab[np.isin(m, [6, 7, 8])] = "summer"
    return lab


def main() -> None:
    pd.set_option("display.width", 180)
    print("=" * 80)
    print("pjm-158 Phase 0.2/0.3 — DA virtual layer: anchor, gain, compression")
    print("=" * 80)

    summary = []
    for year in YEARS:
        print(f"\n{'#' * 70}\n#  {year}\n{'#' * 70}")
        bids = load_curve(year)
        hours = build_hour_arrays(bids)
        lam_a = actual_da_price(year)
        price_z, share_z, lam_m = model_zonal(year)
        vinc, vdec = model_cleared(year)
        ladder = _hourly_net_rungs(bids, 8760, N_RUNGS)

        # --- §1 the anchor -------------------------------------------------
        net_a = eval_net_fast(hours, lam_a)
        net_m_curve = eval_net_fast(hours, lam_m)
        ref_twh = net_a.sum() / TWH
        model_net_demand = -(vinc + vdec)  # + = phantom demand
        print("\n--- §1 anchor: raw net curve cleared at ACTUAL DA price ---")
        print(f"  reference annual net  = {ref_twh:+.3f} TWh  (+ = net virtual DEMAND)")
        print(f"                         {-ref_twh:+.3f} TWh  (+ = net virtual SUPPLY,")
        print("                                        the pjm-105 docstring sign)")
        print(f"  model cleared: INC {vinc:+.3f}  DEC {vdec:+.3f} TWh")
        print(f"  model net demand      = {model_net_demand:+.3f} TWh")
        print(f"  DEVIATION from anchor = {model_net_demand - ref_twh:+.3f} TWh")
        print(f"  gross turnover (model)= {vinc - vdec:.3f} TWh")

        # --- §2 the gain ---------------------------------------------------
        print("\n--- §2 gain dNet/dλ at the actual DA price (MW per $/MWh) ---")
        gains = {d: gain(hours, lam_a, d) for d in (1.0, 5.0, 10.0)}
        for d, g in gains.items():
            print(
                f"  ±${d:>4.0f}: mean {g.mean():9.1f}   median {np.median(g):9.1f}   "
                f"p10 {np.percentile(g, 10):9.1f}   p90 {np.percentile(g, 90):9.1f}   "
                f"annual |Σ| {np.abs(g).sum() / 1e3:8.1f} GWh per $/MWh"
            )
        g1 = gains[1.0]
        sea = season(year)
        hod = np.arange(8760) % 24
        print("\n  by season (±$1 gain, MW per $/MWh):")
        for s in ("winter", "shoulder", "summer"):
            k = sea == s
            print(f"    {s:9s} n={k.sum():5d}  mean {g1[k].mean():9.1f}")
        print("\n  by hour-of-day (±$1 gain, MW per $/MWh):")
        hod_mean = pd.Series(g1).groupby(hod).mean()
        print("   " + "  ".join(f"h{h:02d}:{hod_mean[h]:7.0f}" for h in range(0, 24, 3)))

        # --- §2b/§3 the attribution chain ---------------------------------
        # anchor -> system dual -> zonal duals -> rendered ladder -> the LP.
        # Each step adds exactly one effect, so the deviation is attributed
        # without any free parameter.
        raw_fn = lambda lz: eval_net_fast(hours, lz)  # noqa: E731
        lad_fn = lambda lz: ladder_net(ladder, lz)  # noqa: E731
        step_sys = net_m_curve.sum() / TWH
        step_zon = zonal_sum(raw_fn, price_z, share_z).sum() / TWH
        step_lad = zonal_sum(lad_fn, price_z, share_z).sum() / TWH
        print("\n--- §2b/§3 attribution chain (TWh, + = net virtual DEMAND) ---")
        rows = [
            ("1 anchor: raw curve @ ACTUAL DA price", ref_twh, None),
            ("2   + model price level (system dual)", step_sys, step_sys - ref_twh),
            ("3   + zonal dual dispersion", step_zon, step_zon - step_sys),
            ("4   + N_RUNGS ladder compression", step_lad, step_lad - step_zon),
            ("5 OBSERVED (the LP's own clearing)", model_net_demand,
             model_net_demand - step_lad),
        ]
        for lab, val, delta in rows:
            d = "" if delta is None else f"   step {delta:+7.3f}"
            print(f"  {lab:42s} {val:+8.3f}{d}")
        print(f"  {'TOTAL deviation from anchor':42s} "
              f"{model_net_demand - ref_twh:+8.3f}")

        # --- §3b compression, measured on its own --------------------------
        print("\n--- §3b compression exactness (N_RUNGS = %d/side) ---" % N_RUNGS)
        lad_m = ladder_net(ladder, lam_m)
        lad_a = ladder_net(ladder, lam_a)
        for tag, raw_v, lad_v in (
            ("at the model's own system dual", net_m_curve, lad_m),
            ("at the actual DA price        ", net_a, lad_a),
        ):
            d = lad_v - raw_v
            print(
                f"  {tag}: ladder−raw  mean {d.mean():8.2f} MW   "
                f"MAE {np.abs(d).mean():8.2f} MW   annual {d.sum() / TWH:+.3f} TWh"
            )
        lam0 = crossing_price(hours)
        top_dec, bot_inc = ladder_crossing(bids, N_RUNGS)
        ok = np.isfinite(lam0) & np.isfinite(top_dec) & np.isfinite(bot_inc)
        mid = 0.5 * (top_dec + bot_inc)
        print(
            f"  crossing λ0: raw mean {np.nanmean(lam0[ok]):7.2f}   "
            f"ladder bracket mean [{np.nanmean(top_dec[ok]):7.2f}, "
            f"{np.nanmean(bot_inc[ok]):7.2f}]   midpoint {np.nanmean(mid[ok]):7.2f}   "
            f"displacement {np.nanmean(mid[ok] - lam0[ok]):+7.2f} $/MWh"
        )
        print("  resolution sensitivity (zonal clearing, TWh):")
        for n in (4, 8, 16, 32, 64):
            lad_n = _hourly_net_rungs(bids, 8760, n)
            v = zonal_sum(lambda lz: ladder_net(lad_n, lz), price_z, share_z).sum() / TWH
            print(f"    N_RUNGS={n:3d}: {v:+.3f}   (raw-curve zonal = {step_zon:+.3f})")

        summary.append(
            {
                "year": year,
                "anchor": ref_twh,
                "sys_dual": step_sys,
                "zonal": step_zon,
                "ladder": step_lad,
                "observed": model_net_demand,
                "deviation": model_net_demand - ref_twh,
                "from_price": step_sys - ref_twh,
                "from_zonal": step_zon - step_sys,
                "from_compression": step_lad - step_zon,
                "unexplained": model_net_demand - step_lad,
                "gain_mean_MW_per_$": g1.mean(),
                "lam0_disp_$": float(np.nanmean(mid[ok] - lam0[ok])),
                "price_mae_vs_DA": float(np.abs(lam_m - lam_a).mean()),
            }
        )

    print("\n" + "=" * 80)
    print("SUMMARY (+ = net virtual DEMAND / phantom load)")
    print("=" * 80)
    print(pd.DataFrame(summary).set_index("year").round(3).to_string())
    Path("results/calibration/_pjm158_virtual_gain.json").write_text(
        json.dumps(summary, indent=2, default=float)
    )


if __name__ == "__main__":
    main()
