"""miso-246 phase 0 — the MISO BACKCAST LEVER-QUEUE CENSUS. Zero LP.

Pre-registration:
``results/calibration/PREREG-miso246-the-backcast-lever-queue-census-2026-09-08.md``
(pushed with this probe, before either ran). Every bar below is a LITERAL here,
quoted from that PREREG, so each leg adjudicates even if a predecessor artifact
is missing.

What it measures, in PREREG section order:

* **G-PARSE / G-MODE / G-ISO** — the mechanical enumeration source E1: every ISO
  shard's cells mapped onto the base row set's ``mode`` (B / BF / F), so a
  backcast-lane-reachable ``O``/``U`` count exists for all six ISOs on ONE
  parser (PREREG section 3a's primary bar reads the five ``complete``-holding
  ISOs' median, a comparator this session had NOT measured when the bar was
  fixed).
* **G-BASIS** — the two Indiana-hub series are distinct (the lane's standing
  basis-discipline trap: the decile column is RT, every seam ladder is DA).
* **G-BUS / G-RECON** — the p_bus series is the keeper's committed P1
  ``MISO_external`` price, and the four-seam reconstruction is miso-241's
  REPAIRED instrument, with Manitoba's incumbent and repaired export legs proven
  identical arrays (so miso-236's published Manitoba numbers were not measured
  on a superseded instrument).
* **M-a1 / M-a2** — the bus-price compression object, and the RUNG TEST that
  adjudicates it: what share of hours p_bus sits within $0.01 of an enumerable
  candidate price at that bus.
* **M-b1 / M-b2** — Manitoba determinism, and the ceiling-set / merit-set
  decomposition that says which object carries the deficit.
* **M-c1** — the CC_REGULAR shape deficit, reproduced on the CURRENT keeper.

Usage: ``python3 scripts/probes/_miso246_lever_queue_census_phase0.py``
"""

from __future__ import annotations

import base64
import gzip
import importlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

CAL = REPO / "results/calibration"
KEEPER = CAL / "miso245_ladderfix_K"
RUN_ID = "2026-09-08-miso-245-ladderfix"
OUT = CAL / "_miso246_lever_queue_census_phase0.json"
MATRIX_BASE = REPO / "docs/codebase-site/data/mechanism-matrix.js"
SHARD_DIR = REPO / "docs/codebase-site/data/mechanism-matrix"
BENCH = REPO / "frontend/data/backcast/bench/MISO"
PAYLOAD = REPO / f"frontend/data/backcast/runs/{RUN_ID}.js"
ACTUAL_MISO_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet"

YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"
EXT_BUS = "MISO_external"
EXT_BUS_SOUTH = "MISO_external_South"
FOUR_SEAM = ("PJM", "SPP", "South", "Manitoba")
BUS_OF_SEAM = {
    "PJM": EXT_BUS,
    "SPP": EXT_BUS,
    "South": EXT_BUS_SOUTH,
    "Manitoba": EXT_BUS,
}
MIDWEST_ZONES = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
)
ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP")
COMPLETE_ISOS = ("ERCOT", "NEISO", "PJM", "CAISO", "NYISO")
GROUP_CC = "CC_REGULAR"

# ---- PREREG bars, fixed ex ante (literals, never read from an artifact) ----
BAR_SHARD_CELLS_MISO = 312  # G-PARSE
BAR_UNMAPPED = 0  # G-PARSE / G-ISO
BAR_BASIS_CORR = 0.60  # G-BASIS: da vs rt must be DISTINCT
BAR_RUNG_TOL_USD = 0.01  # M-a2 tolerance (NEVER widened)
BAR_RUNG_SHARE = 0.90  # M-a2 decision rule
TMPL_CELLS = 12 * 24
TMPL_MIN_SAMPLES = 8  # M-b2: drop a subset cell below this, and report the count
_MONTH_LEN = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# PREREG section 4 reference values, restated HERE so the reproduction legs bind
# even if a predecessor artifact is absent. NONE of these is a bar: every one is
# REPORTED, and two keeper promotions have intervened since each was published.
REF_SIGMA_PBUS = (6.09, 16.51, 15.22)  # miso-242 section 6, miso-233 keeper
REF_SIGMA_DA = (12.81, 19.89, 26.12)  # miso-242 section 6
REF_TMPL_MANITOBA_MEAS = (0.7380, 0.7205, 0.6594)  # miso-236 section 3
REF_TMPL_MANITOBA_MODEL = (0.6036, 0.5207, 0.2869)  # miso-236 section 3
REF_CEILING_SHARE_MANITOBA = (0.4279, 0.4152, 0.2492)  # miso-241 section 3

FAILED: list[str] = []


def fail(leg: str, msg: str) -> None:
    FAILED.append(f"{leg}: {msg}")


# ----------------------------------------------------------------- E1 parsing
def parse_base_rows(text: str) -> dict[str, dict]:
    """Base matrix rows keyed by mechanism id, carrying ``mode`` / ``cat`` / ``name``.

    The file is JS, so the rows are split on their own ``{ id: "..."`` openers and
    each block is read with anchored field regexes; nothing is ``eval``-ed.
    """
    starts = [m.start() for m in re.finditer(r'\{\s*id:\s*"[a-z0-9_]+"', text)]
    starts.append(len(text))
    rows: dict[str, dict] = {}
    for i in range(len(starts) - 1):
        blk = text[starts[i] : starts[i + 1]]
        rid = re.search(r'id:\s*"([a-z0-9_]+)"', blk).group(1)
        mode = re.search(r'\bmode:\s*"([A-Z]+)"', blk)
        cat = re.search(r'\bcat:\s*"([a-z0-9_]+)"', blk)
        name = re.search(r'\bname:\s*"([^"]*)"', blk)
        rows[rid] = {
            "mode": mode.group(1) if mode else None,
            "cat": cat.group(1) if cat else None,
            "name": name.group(1) if name else None,
        }
    return rows


def parse_shard(text: str) -> dict[str, dict]:
    """One ISO shard's cells keyed by mechanism id, with the verdict and ev length."""
    out: dict[str, dict] = {}
    for m in re.finditer(
        r'^\s{4}([a-z0-9_]+):\s*\{\s*cell:\s*"([KRIGOU.])"(.*)$', text, re.M
    ):
        ev = re.search(r'\bev:\s*"', m.group(3))
        out[m.group(1)] = {"cell": m.group(2), "has_ev": bool(ev)}
    return out


# --------------------------------------------------------------- M-b template
def template_r2(y: np.ndarray, cell: np.ndarray) -> tuple[float, float, int]:
    """(raw, dof-adjusted, cells used) between-cell variance share — miso-236's estimator.

    Reproduced verbatim from ``_miso236_neighbour_state_residual_phase0`` so the
    reproduction leg compares like with like; cells carrying fewer than
    ``TMPL_MIN_SAMPLES`` samples are dropped (M-b2's declared rule) and the count
    of dropped cells is returned.
    """
    df = pd.DataFrame({"c": cell, "y": y})
    counts = df.groupby("c")["y"].transform("size").to_numpy()
    keep = counts >= TMPL_MIN_SAMPLES
    y2, c2 = y[keep], cell[keep]
    used = int(len(np.unique(c2)))
    d2 = pd.DataFrame({"c": c2, "y": y2})
    fitted = d2.groupby("c")["y"].transform("mean").to_numpy()
    ss_tot = float(((y2 - y2.mean()) ** 2).sum())
    raw = float(1.0 - ((y2 - fitted) ** 2).sum() / ss_tot) if ss_tot > 0 else 0.0
    n = len(y2)
    adj = 1.0 - (1.0 - raw) * (n - 1) / (n - used) if n > used else float("nan")
    return round(raw, 4), round(adj, 4), used


def cc_series(b64: str, cap: float) -> np.ndarray:
    """miso-234's decoder: uint8 percent-of-nameplate bytes scaled to MW."""
    x = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)[:HOURS]
    out = np.zeros(HOURS)
    out[: x.size] = x * (cap / 100.0)
    return out


def main() -> int:  # noqa: PLR0912, PLR0915 - one linear probe, PREREG section order
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import (
        measured_miso_spp_hub_prices,
        measured_seam_import_envelope,
    )
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_MANITOBA_SEAM_SPEC,
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )

    m41 = importlib.import_module("_miso241_spp_quantity_side_charter_phase0")
    m38 = importlib.import_module("_miso238_pjm_seam_channel_attribution_phase0")
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    build_recons = m41.build_recons
    classify_leg = m41.classify_leg
    ols_resid = m38.ols_resid

    rep: dict = {
        "probe": "miso-246 phase 0 — the MISO backcast lever-queue census",
        "prereg": "results/calibration/PREREG-miso246-the-backcast-lever-queue-census-2026-09-08.md",
        "keeper": RUN_ID,
        "zero_lp": True,
        "read_only": True,
        "grants_no_marker": True,
        "price_basis": {
            "p_bus": f"keeper committed P1 price at {EXT_BUS} (system_<year>.parquet)",
            "seam_regressor": "measured Indiana-hub DA (actual_lmp_hourly_MISO.parquet `da`, float32)",
            "decile_price": "measured Indiana-hub RT (_miso224 actual_zone_price)",
            "spp_anchor": "measured SPP NORTH hub DA",
        },
        "bars": {
            "shard_cells_miso": BAR_SHARD_CELLS_MISO,
            "unmapped": BAR_UNMAPPED,
            "basis_corr_max": BAR_BASIS_CORR,
            "rung_tol_usd": BAR_RUNG_TOL_USD,
            "rung_share": BAR_RUNG_SHARE,
            "tmpl_min_samples": TMPL_MIN_SAMPLES,
        },
        "gates": {},
        "reported": {},
    }

    # ================================================== G-PARSE / G-MODE / G-ISO
    base = parse_base_rows(MATRIX_BASE.read_text())
    n_no_mode = sum(1 for r in base.values() if r["mode"] is None)
    iso_census: dict[str, dict] = {}
    for iso in ISOS:
        p = SHARD_DIR / f"{iso}.js"
        if not p.exists():
            iso_census[iso] = {"present": False}
            continue
        cells = parse_shard(p.read_text())
        unmapped = sorted(k for k in cells if k not in base)
        ou = {k: v for k, v in cells.items() if v["cell"] in ("O", "U")}
        bc = {k: v for k, v in ou.items() if base.get(k, {}).get("mode") in ("B", "BF")}
        fc_only = {k: v for k, v in ou.items() if base.get(k, {}).get("mode") == "F"}
        non_na_bc = [
            k
            for k, v in cells.items()
            if v["cell"] != "." and base.get(k, {}).get("mode") in ("B", "BF")
        ]
        iso_census[iso] = {
            "present": True,
            "n_cells": len(cells),
            "n_unmapped": len(unmapped),
            "unmapped": unmapped[:10],
            "by_code": {
                c: sum(1 for v in cells.values() if v["cell"] == c) for c in "KUIRGO."
            },
            "n_ou": len(ou),
            "N_bc": len(bc),
            "n_ou_forecast_only": len(fc_only),
            "n_non_na_backcast": len(non_na_bc),
            "share_bc": (round(len(bc) / len(non_na_bc), 4) if non_na_bc else None),
        }
    miso_c = iso_census["MISO"]
    if miso_c.get("n_cells") != BAR_SHARD_CELLS_MISO:
        fail("G-PARSE", f"MISO cells {miso_c.get('n_cells')} != {BAR_SHARD_CELLS_MISO}")
    if any(
        v.get("present") and v["n_unmapped"] > BAR_UNMAPPED for v in iso_census.values()
    ):
        fail("G-ISO", "at least one shard has cells with no base row")
    rep["gates"]["G_PARSE_G_ISO"] = {
        "iso_census": iso_census,
        "base_rows": len(base),
        "base_rows_without_mode": n_no_mode,
        "PASS": not any(g.startswith(("G-PARSE", "G-ISO")) for g in FAILED),
    }
    rep["gates"]["G_MODE"] = {
        "mode_counts_all_rows": {
            m: sum(1 for r in base.values() if r["mode"] == m)
            for m in ("B", "BF", "F", None)
        },
        "silently_defaulted": 0,
        "note": (
            "rows carrying no `mode` in the committed file are counted, never "
            "defaulted: a cell whose base row has no mode is EXCLUDED from N_bc "
            "and appears in n_ou but not in N_bc or n_ou_forecast_only"
        ),
        "PASS": True,
    }

    # -------- PREREG section 3a: the primary cross-ISO bar
    peers = [iso_census[i]["N_bc"] for i in COMPLETE_ISOS if iso_census[i]["present"]]
    med = float(np.median(peers)) if peers else float("nan")
    rep["gates"]["S3A_CROSS_ISO"] = {
        "N_bc_by_iso": {i: iso_census[i].get("N_bc") for i in ISOS},
        "complete_holders": list(COMPLETE_ISOS),
        "median_N_bc_over_complete_holders": med,
        "miso_N_bc": miso_c.get("N_bc"),
        "bar": "MISO N_bc <= median(N_bc) over the five complete-holding ISOs",
        "PASS": bool(miso_c.get("N_bc", 1e9) <= med),
        "secondary_share_reported_not_gated": {
            i: iso_census[i].get("share_bc") for i in ISOS
        },
    }

    # ------------------------------------------------------------- G-BASIS
    lmp = pd.read_parquet(ACTUAL_MISO_LMP)
    basis = {}
    for y in YEARS:
        s = lmp[lmp["year"] == y]
        da = s["da"].to_numpy(float)
        rt = s["rt"].to_numpy(float)
        ok = np.isfinite(da) & np.isfinite(rt)
        basis[str(y)] = round(float(np.corrcoef(da[ok], rt[ok])[0, 1]), 4)
    if any(v >= BAR_BASIS_CORR for v in basis.values()):
        fail("G-BASIS", f"da/rt corr not distinct: {basis}")
    rep["gates"]["G_BASIS"] = {
        "corr_da_rt": basis,
        "bar_max": BAR_BASIS_CORR,
        "PASS": all(v < BAR_BASIS_CORR for v in basis.values()),
    }

    # ------------------------------- shared per-year operands (G-BUS, G-RECON)
    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()
    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}
    specs["Manitoba"] = MISO_MANITOBA_SEAM_SPEC
    ladders = (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )
    ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
    month = np.repeat(np.arange(12), [24 * d for d in _MONTH_LEN])
    hod_all = np.tile(np.arange(24), 365)

    gbus: dict[str, dict] = {}
    grecon: dict[str, dict] = {}
    ma1: dict[str, dict] = {}
    ma2: dict[str, dict] = {}
    mb: dict[str, dict] = {}
    mc: dict[str, dict] = {}

    pay = json.loads(
        gzip.decompress(
            base64.b64decode(
                re.search(r'runGz\["[^"]+"\]="([^"]+)"', PAYLOAD.read_text()).group(1)
            )
        ).decode()
    )
    pay_years = pay.get("years") or pay

    for yi, year in enumerate(YEARS):
        gy = g_all.loc[year]

        def dense(col: str) -> np.ndarray:
            return (
                gy[col]
                .reindex(range(HOURS))
                .interpolate(limit=3)
                .ffill()
                .bfill()
                .to_numpy(float)
            )

        border = dense("pjm_border")
        da = dense("da")
        spp_hub = np.asarray(measured_miso_spp_hub_prices("MISO", year, HOURS), float)
        anchors = {"PJM": border, "SPP": spp_hub}

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        zones_present = sorted(sysf["zone"].unique())
        bus_price = {
            b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
            for b in zones_present
        }
        pb = bus_price[EXT_BUS]
        gbus[str(year)] = {
            "zones": zones_present,
            "n_rows_ext": int(len(pb)),
            "south_bus_present": EXT_BUS_SOUTH in bus_price,
            "south_bus_distinct": bool(
                EXT_BUS_SOUTH in bus_price
                and not np.array_equal(pb, bus_price[EXT_BUS_SOUTH])
            ),
        }
        if len(pb) != HOURS or EXT_BUS_SOUTH not in bus_price:
            fail(
                "G-BUS",
                f"{year}: ext rows {len(pb)}, south bus present {EXT_BUS_SOUTH in bus_price}",
            )

        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )
        R, widths = {}, {}
        for seam in FOUR_SEAM:
            widths[seam] = float(specs[seam].interface_limit_mw) / SEAM_FLOW_TRANCHES
            R[seam] = build_recons(
                seam,
                year,
                bus_price[BUS_OF_SEAM[seam]],
                anchors,
                env_i,
                env_e,
                widths[seam],
                ks,
                ladders,
            )
        man_same = bool(
            np.array_equal(
                R["Manitoba"]["exp_incumbent"], R["Manitoba"]["exp_repaired"]
            )
        )
        grecon[str(year)] = {
            "manitoba_incumbent_equals_repaired": man_same,
            "harness_note": "build_recons imported from _miso241 (the REPAIRED instrument)",
        }
        if not man_same:
            fail(
                "G-RECON",
                f"{year}: Manitoba export legs differ; miso-236 numbers are superseded",
            )

        # -------------------------------------------------------------- M-a1
        okp = np.isfinite(pb) & np.isfinite(da)
        ma1[str(year)] = {
            "sigma_p_bus": round(float(pb[okp].std()), 2),
            "sigma_da": round(float(da[okp].std()), 2),
            "ratio": round(float(pb[okp].std() / da[okp].std()), 4),
            "mean_p_bus": round(float(pb[okp].mean()), 2),
            "mean_da": round(float(da[okp].mean()), 2),
            "corr_p_bus_da": round(float(np.corrcoef(pb[okp], da[okp])[0, 1]), 4),
            "ref_miso242_sigma_p_bus": REF_SIGMA_PBUS[yi],
            "ref_miso242_sigma_da": REF_SIGMA_DA[yi],
        }

        # -------------------------------------------------------------- M-a2
        cands: dict[str, np.ndarray] = {}
        for seam in ("PJM", "SPP", "Manitoba"):  # seams hosted on MISO_external
            if seam == "PJM":
                d_i = np.asarray(ladders[1][year]["PJM"]["import"], float)
                d_e = np.asarray(ladders[1][year]["PJM"]["export"], float)
                a = anchors["PJM"]
                cands[f"{seam}_import"] = a[None, :] + d_i[:, None]
                cands[f"{seam}_export"] = a[None, :] + d_e[:, None]
            elif seam == "SPP":
                d_i = np.asarray(ladders[2][year]["SPP"]["import"], float)
                d_e = np.asarray(ladders[2][year]["SPP"]["export"], float)
                a = anchors["SPP"]
                cands[f"{seam}_import"] = a[None, :] + d_i[:, None]
                cands[f"{seam}_export"] = a[None, :] + d_e[:, None]
            else:
                d_i = np.asarray(ladders[0][year][seam]["import"], float)
                d_e = np.asarray(ladders[0][year][seam]["export"], float)
                cands[f"{seam}_import"] = np.broadcast_to(
                    d_i[:, None], (d_i.size, HOURS)
                )
                cands[f"{seam}_export"] = np.broadcast_to(
                    d_e[:, None], (d_e.size, HOURS)
                )
        for z in MIDWEST_ZONES:
            if z in bus_price:
                cands[f"zone_{z}"] = bus_price[z][None, :]

        dist_by_src = {k: np.abs(v - pb[None, :]).min(axis=0) for k, v in cands.items()}
        allmin = np.min(np.vstack(list(dist_by_src.values())), axis=0)
        hit = allmin <= BAR_RUNG_TOL_USD
        ladder_srcs = [k for k in dist_by_src if not k.startswith("zone_")]
        zone_srcs = [k for k in dist_by_src if k.startswith("zone_")]
        hit_ladder = (
            np.min(np.vstack([dist_by_src[k] for k in ladder_srcs]), axis=0)
            <= BAR_RUNG_TOL_USD
        )
        hit_zone = (
            np.min(np.vstack([dist_by_src[k] for k in zone_srcs]), axis=0)
            <= BAR_RUNG_TOL_USD
            if zone_srcs
            else np.zeros(HOURS, bool)
        )
        ma2[str(year)] = {
            "R_rung": round(float(hit.mean()), 4),
            "R_rung_ladder_only": round(float(hit_ladder.mean()), 4),
            "R_rung_zone_only": round(float(hit_zone.mean()), 4),
            "R_rung_ladder_exclusive": round(float((hit_ladder & ~hit_zone).mean()), 4),
            "R_rung_zone_exclusive": round(float((hit_zone & ~hit_ladder).mean()), 4),
            "n_candidate_rows": int(sum(v.shape[0] for v in cands.values())),
            "min_distance_quantiles_usd": {
                q: round(float(np.quantile(allmin, p)), 4)
                for q, p in (("p50", 0.5), ("p90", 0.9), ("p99", 0.99), ("max", 1.0))
            },
            "unmatched_hours": int((~hit).sum()),
            "unmatched_p_bus_mean": (
                round(float(pb[~hit].mean()), 2) if (~hit).any() else None
            ),
            "unmatched_p_bus_max": (
                round(float(pb[~hit].max()), 2) if (~hit).any() else None
            ),
        }

        # -------------------------------------------------------- M-b1 / M-b2
        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        cell = (month * 24 + hod_all)[ok]
        meas_net_man = dense("Manitoba")[ok]
        model_net_man = (R["Manitoba"]["imp"] - R["Manitoba"]["exp_repaired"])[ok]
        reg = da[ok]
        r_meas = ols_resid(meas_net_man, reg)
        r_model = ols_resid(model_net_man, reg)
        t_meas = template_r2(r_meas, cell)
        t_model = template_r2(r_model, cell)

        # miso-241 section 3's OWN definition, reproduced exactly: a hour is
        # CEILING-ACTIVE iff EITHER leg's ceiling binds, computed on the ok subset.
        w_man = widths["Manitoba"]
        leg_i = classify_leg(
            R["Manitoba"]["n_i"][ok], R["Manitoba"]["env_i_eff"][ok], w_man
        )
        leg_e = classify_leg(
            R["Manitoba"]["n_e_repaired"][ok], R["Manitoba"]["env_e_eff"][ok], w_man
        )
        ceil_mask = leg_i["ceiling"] | leg_e["ceiling"]
        ceiling_share = float(ceil_mask.mean())
        sub = {}
        for nm, msk in (("ceiling", ceil_mask), ("merit", ~ceil_mask)):
            if msk.sum() < TMPL_CELLS:
                sub[nm] = {"n_hours": int(msk.sum()), "insufficient": True}
                continue
            tm = template_r2(r_meas[msk], cell[msk])
            tp = template_r2(r_model[msk], cell[msk])
            sub[nm] = {
                "n_hours": int(msk.sum()),
                "tmpl_measured_adj": tm[1],
                "tmpl_model_adj": tp[1],
                "cells_used_measured": tm[2],
                "cells_used_model": tp[2],
                "Gamma": round(tm[1] - tp[1], 4),
            }
        mb[str(year)] = {
            "tmpl_measured_raw": t_meas[0],
            "tmpl_measured_adj": t_meas[1],
            "tmpl_model_raw": t_model[0],
            "tmpl_model_adj": t_model[1],
            "ref_miso236_measured_adj": REF_TMPL_MANITOBA_MEAS[yi],
            "ref_miso236_model_adj": REF_TMPL_MANITOBA_MODEL[yi],
            "ceiling_active_share": round(ceiling_share, 4),
            "ref_miso241_ceiling_share": REF_CEILING_SHARE_MANITOBA[yi],
            "subsets": sub,
        }

        # -------------------------------------------------------------- M-c1
        yb = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]
        yp = pay_years.get(str(year)) or pay_years.get(year)
        a_cc = np.zeros(HOURS)
        m_cc = np.zeros(HOURS)
        n_pl = 0
        for code, bp in yb["plants"].items():
            if bp.get("group") != GROUP_CC or bp.get("nodata"):
                continue
            cap = float(bp.get("npl") or 0.0)
            cb = bp.get("campd")
            pp = yp["plants"].get(str(code))
            if cap <= 0 or not cb or not pp or not pp.get("m"):
                continue
            a_cc += cc_series(cb, cap)
            m_cc += cc_series(pp["m"], cap)
            n_pl += 1
        deficit = a_cc - m_cc
        shape_def = a_cc - m_cc * (a_cc.sum() / m_cc.sum())
        p = act
        okc = np.isfinite(p)
        order = np.argsort(p[okc], kind="stable")
        idx = np.arange(HOURS)[okc]
        dec = []
        for i, part in enumerate(np.array_split(order, 10)):
            h = idx[part]
            dec.append(
                {
                    "decile": i + 1,
                    "mean_price_rt": round(float(p[h].mean()), 2),
                    "mean_deficit_mw": round(float(deficit[h].mean()), 1),
                    "shape_deficit_mw": round(float(shape_def[h].mean()), 1),
                    "deficit_pct_of_measured": round(
                        float(100 * deficit[h].mean() / a_cc[h].mean()), 2
                    ),
                }
            )
        hod = np.arange(HOURS) % 24
        hod_shape = [round(float(shape_def[hod == h].mean()), 1) for h in range(24)]
        mc[str(year)] = {
            "plants_matched": n_pl,
            "measured_twh": round(float(a_cc.sum() / 1e6), 3),
            "model_twh": round(float(m_cc.sum() / 1e6), 3),
            "by_price_decile_rt": dec,
            "shape_deficit_span_mw": round(
                float(
                    max(d["shape_deficit_mw"] for d in dec)
                    - min(d["shape_deficit_mw"] for d in dec)
                ),
                1,
            ),
            "shape_deficit_d1_d10_mw": [
                dec[0]["shape_deficit_mw"],
                dec[-1]["shape_deficit_mw"],
            ],
            "shape_deficit_by_hod": hod_shape,
            "argmin_hod": int(np.argmin(hod_shape)),
            "argmax_hod": int(np.argmax(hod_shape)),
        }

    rep["gates"]["G_BUS"] = {
        "years": gbus,
        "PASS": not any(g.startswith("G-BUS") for g in FAILED),
    }
    rep["gates"]["G_RECON"] = {
        "years": grecon,
        "PASS": not any(g.startswith("G-RECON") for g in FAILED),
    }

    # ---- M-a2 decision rule
    rung_all = all(ma2[str(y)]["R_rung"] >= BAR_RUNG_SHARE for y in YEARS)
    rep["gates"]["M_A2_RUNG"] = {
        "years": ma2,
        "bar": f"R_rung >= {BAR_RUNG_SHARE} in ALL THREE years",
        "RUNG_DETERMINED": bool(rung_all),
    }
    # ---- M-b2 decision rule
    votes = {"merit": 0, "ceiling": 0, "tie_or_insufficient": 0}
    for y in YEARS:
        s = mb[str(y)]["subsets"]
        gm = s.get("merit", {}).get("Gamma")
        gc = s.get("ceiling", {}).get("Gamma")
        if gm is None or gc is None:
            votes["tie_or_insufficient"] += 1
        elif gm > gc:
            votes["merit"] += 1
        elif gc > gm:
            votes["ceiling"] += 1
        else:
            votes["tie_or_insufficient"] += 1
    verdict_b = (
        "MERIT (same object as item (a))"
        if votes["merit"] >= 2
        else "CEILING (the envelope)"
        if votes["ceiling"] >= 2
        else "UNRESOLVED — the decomposition did not separate"
    )
    rep["gates"]["M_B2_DECOMP"] = {"years": mb, "votes": votes, "VERDICT": verdict_b}

    rep["reported"]["M_A1_sigma"] = ma1
    rep["reported"]["M_C1_cc_shape"] = mc
    rep["FAILED_LEGS"] = FAILED
    rep["ALL_GATED_LEGS_PASS"] = not FAILED

    OUT.write_text(json.dumps(rep, indent=1) + "\n")

    # ------------------------------------------------------------------ print
    print(f"FAILED_LEGS: {FAILED}")
    print("\n=== E1 / section 3a — backcast-lane-reachable O/U cells (N_bc) ===")
    for iso in ISOS:
        c = iso_census[iso]
        if not c.get("present"):
            print(f"  {iso:6s} (no shard)")
            continue
        mark = (
            "  <- MISO"
            if iso == "MISO"
            else (" (complete)" if iso in COMPLETE_ISOS else "")
        )
        print(
            f"  {iso:6s} cells {c['n_cells']:>4} | O/U {c['n_ou']:>3}"
            f" | N_bc {c['N_bc']:>3} | fc-only {c['n_ou_forecast_only']:>3}"
            f" | share {c['share_bc']}{mark}"
        )
    print(f"  median N_bc over complete holders = {med}")
    print(
        f"  MISO N_bc = {miso_c['N_bc']}  -> section 3a PRIMARY BAR "
        f"{'CLEARS' if miso_c['N_bc'] <= med else 'MISSES'}"
    )

    print("\n=== M-a1 (reported) — sigma(p_bus) vs sigma(Indiana-hub DA) ===")
    for y in YEARS:
        a = ma1[str(y)]
        print(
            f"  {y}  sigma p_bus {a['sigma_p_bus']:>7.2f} (miso-242 {a['ref_miso242_sigma_p_bus']})"
            f"  sigma DA {a['sigma_da']:>7.2f} (miso-242 {a['ref_miso242_sigma_da']})"
            f"  ratio {a['ratio']:.4f}  corr {a['corr_p_bus_da']}"
        )

    print("\n=== M-a2 (GATED) — the rung test ===")
    for y in YEARS:
        a = ma2[str(y)]
        print(
            f"  {y}  R_rung {a['R_rung']:.4f}  (ladder {a['R_rung_ladder_only']:.4f},"
            f" zone {a['R_rung_zone_only']:.4f}, ladder-excl {a['R_rung_ladder_exclusive']:.4f},"
            f" zone-excl {a['R_rung_zone_exclusive']:.4f})"
            f"  unmatched {a['unmatched_hours']}  min-dist p50/p90/max"
            f" {a['min_distance_quantiles_usd']['p50']}/{a['min_distance_quantiles_usd']['p90']}"
            f"/{a['min_distance_quantiles_usd']['max']}"
        )
    print(f"  RUNG-DETERMINED (all three >= {BAR_RUNG_SHARE}): {rung_all}")

    print("\n=== M-b1 / M-b2 — Manitoba determinism ===")
    for y in YEARS:
        b = mb[str(y)]
        print(
            f"  {y}  tmpl meas {b['tmpl_measured_adj']:.4f} (miso-236 {b['ref_miso236_measured_adj']})"
            f"  model {b['tmpl_model_adj']:.4f} (miso-236 {b['ref_miso236_model_adj']})"
            f"  ceiling share {b['ceiling_active_share']:.4f} (miso-241 {b['ref_miso241_ceiling_share']})"
        )
        for nm in ("ceiling", "merit"):
            s = b["subsets"].get(nm, {})
            if s.get("insufficient"):
                print(f"      {nm:8s} n={s['n_hours']} INSUFFICIENT")
            else:
                print(
                    f"      {nm:8s} n={s['n_hours']:>5} meas {s['tmpl_measured_adj']:.4f}"
                    f" model {s['tmpl_model_adj']:.4f}  Gamma {s['Gamma']:+.4f}"
                    f"  cells {s['cells_used_measured']}/{s['cells_used_model']}"
                )
    print(f"  votes {votes} -> VERDICT {verdict_b}")

    print("\n=== M-c1 (reported) — CC_REGULAR shape deficit, price deciles on RT ===")
    for y in YEARS:
        c = mc[str(y)]
        print(
            f"  {y}  plants {c['plants_matched']}  meas {c['measured_twh']} TWh"
            f"  model {c['model_twh']} TWh  shape d1->d10"
            f" {c['shape_deficit_d1_d10_mw']}  span {c['shape_deficit_span_mw']}"
            f"  hod argmin {c['argmin_hod']} argmax {c['argmax_hod']}"
        )
        print(
            "       decile pct-of-measured: "
            + " ".join(
                f"{d['deficit_pct_of_measured']:.1f}" for d in c["by_price_decile_rt"]
            )
        )
    print(f"\nwrote {OUT}")
    return 0 if not FAILED else 1


if __name__ == "__main__":
    raise SystemExit(main())
