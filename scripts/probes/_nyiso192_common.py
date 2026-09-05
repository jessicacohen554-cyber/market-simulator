"""Shared instruments for the nyiso-192 phase-0 probes (NO LP anywhere).

Three read-only instruments the nyiso-192 probes share, so each probe measures
the same bytes:

* :func:`keeper_payload` / :func:`bench_plants` — the committed dashboard
  payload (``runs/<id>.js``) and bench part, decoded through the frozen codec
  in :mod:`scripts.lib.backcast_artifacts`; :func:`dec_u8` is the dashboard's
  own ``dec`` (uint8 percent-of-nameplate, ``backcast-runs.js``).
* :func:`reconstructed` — the keeper's fleet and P0 ``mc_base`` rebuilt with
  :func:`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` (fleet_only, no
  LP), cached under ``.cache/nyiso192/`` so the three probes rebuild once.
* :func:`actual_zone_price` — the MIS real-time zonal LBMP, hourly, on the
  repo's canonical fixed non-leap 8760 clock, from the committed month zips
  plus the same MIS fetch-to-cache the nyiso-149 derive uses
  (``scripts.data.derive_nyiso_chp_duty_curve.month_zip``).

Rule 13 [R-MEASURED]: every measured series here DIAGNOSES; nothing is fed back
as an input. Rule 22 [R-HOLDOUT]: 2023-2025 only.
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KEEPER_ID = "2026-09-05-nyiso-189-steam-identity"
KEEPER_BUNDLE = REPO / "results/calibration/nyiso189_steam_identity"
YEARS = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]: training years only
T = 8760  # the canonical fixed non-leap clock (rule 8 [R-8760])
CACHE = REPO / ".cache" / "nyiso192"

#: The sector default the payload add-back fell back to (market_sim.data.chp
#: CHP_BTM_PCT_BY_SECTOR["merchant"], read live so a change breaks this loudly).
CHP_GROUPS = ("CC_CHP", "CT_CHP", "ST_CHP")

NAME_TO_LETTER = {
    "WEST": "A",
    "GENESE": "B",
    "CENTRL": "C",
    "NORTH": "D",
    "MHK VL": "E",
    "CAPITL": "F",
    "HUD VL": "G",
    "MILLWD": "H",
    "DUNWOD": "I",
    "N.Y.C.": "J",
    "LONGIL": "K",
}
MODEL_ZONES = {
    "Upstate_West": list("ABCDE"),
    "Capital_Hudson": ["F", "G"],
    "Lower_Hudson": ["H", "I"],
    "NYC": ["J"],
    "Long_Island": ["K"],
}


def dec_u8(b64: str) -> np.ndarray:
    """The dashboard's ``dec``: base64 uint8 percent-of-nameplate series."""
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def keeper_payload(run_id: str = KEEPER_ID) -> dict:
    """Decode a committed ``runs/<id>.js`` payload."""
    return decode_run_js(
        (REPO / f"frontend/data/backcast/runs/{run_id}.js").read_text()
    )


def bench_plants(year: int) -> dict:
    """The committed NYISO bench part's ``plants`` block for *year*."""
    return json.load(
        gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{year}.json.gz")
    )["bench"]["plants"]


def plant_series(payload: dict, bench: dict, key: str, year: int) -> tuple:
    """(payload model MW, bench CAMPD gross MW) for one plant key, 8760 each."""
    npl = float(bench[key]["npl"])
    m = dec_u8(payload["years"][str(year)]["plants"][key]["m"]) * npl / 100.0
    c = dec_u8(bench[key]["campd"]) * npl / 100.0
    return m[:T], c[:T]


def sector_addback_mw(bench_row: dict) -> float:
    """The flat MW the defective payload added to a CHP plant.

    ``render_calibration_html`` (pre-fix) added ``e_ann x chp_btm_pct(sector)``
    spread over 8760 h; ``chp_btm_pct`` is read live so the number is never typed.
    """
    from market_sim.data.chp import chp_btm_pct

    if bench_row["group"] not in CHP_GROUPS:
        return 0.0
    code = int(str(bench_row.get("code") or "0") or 0)
    pct = chp_btm_pct(code, bench_row["group"], iso="NYISO") / 100.0
    return float(bench_row["e_ann"]) * 1e6 * pct / T


def model_zone_price(year: int) -> pd.DataFrame:
    """Keeper P1 zonal price, hour x zone, from the committed hourly sidecar."""
    s = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"system_{year}.parquet")
    return s.pivot(index="hour", columns="zone", values="price").iloc[:T]


def _canonical_index() -> pd.MultiIndex:
    ts = pd.date_range("2023-01-01", periods=T, freq="h")
    return pd.MultiIndex.from_arrays(
        [ts.month, ts.day, ts.hour], names=["mo", "dy", "hr"]
    )


def actual_zone_price(year: int) -> pd.DataFrame:
    """MIS RT zonal LBMP on the canonical 8760 clock: model zones + letters A-K.

    Committed month zips first, else the nyiso-149 derive's MIS fetch-to-cache.
    Leap-day rows are dropped and DST gaps forward-filled, the clock convention
    of every NYISO probe since nyiso-123.
    """
    from derive_nyiso_chp_duty_curve import month_zip

    frames = []
    for month in range(1, 13):
        with zipfile.ZipFile(month_zip(year, month)) as zf:
            for name in zf.namelist():
                if name.endswith(".csv"):
                    frames.append(pd.read_csv(zf.open(name)))
    df = pd.concat(frames, ignore_index=True)
    df.columns = ["ts", "name", "ptid", "lbmp", "loss", "cong"]
    df["letter"] = df["name"].astype(str).str.strip().map(NAME_TO_LETTER)
    df = df.dropna(subset=["letter"])
    ts = pd.to_datetime(df["ts"], format="%m/%d/%Y %H:%M:%S")
    df["mo"], df["dy"], df["hr"] = ts.dt.month, ts.dt.day, ts.dt.hour
    hourly = df.groupby(["letter", "mo", "dy", "hr"])["lbmp"].mean().unstack(0)
    out = pd.DataFrame(index=hourly.index)
    for zone, letters in MODEL_ZONES.items():
        out[zone] = hourly[[c for c in letters if c in hourly.columns]].mean(axis=1)
    for letter in "ABCDEFGHIJK":
        out[f"zone_{letter}"] = hourly[letter]
    out = out.reindex(_canonical_index()).ffill().bfill()
    return out.reset_index(drop=True)


def reconstructed(year: int, bundle: Path = KEEPER_BUNDLE) -> dict:
    """The bundle's reconstructed fleet for *year* (no LP), cached to ``.cache``.

    Returns ``{static: DataFrame(one row per LP unit), mc: (n, 8760), fuel: (n,
    8760), avail: (n, 8760), min_gen: (n, 8760), zones: [..]}``.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    tag = bundle.name
    npz = CACHE / f"recon_{tag}_{year}.npz"
    pq = CACHE / f"recon_{tag}_{year}.parquet"
    if not (npz.exists() and pq.exists()):
        from scripts.lib.bundle_fleet import (
            clear_fleet_caches,
            reconstruct_bundle_fleet,
        )

        clear_fleet_caches()
        state, _meta = reconstruct_bundle_fleet(bundle, year, verbose=True)
        fa = state["fleet_arrays"]
        from market_sim.config.iso_configs import get_iso_config

        # zone_idx order = the ISO config's zone order, then the priced import
        # node (a pivot's alphabetical column order is NOT the index order).
        zones = list(get_iso_config("NYISO").zone_names)
        n_idx = int(np.asarray(fa.zone_idx).max()) + 1
        zones += ["NYISO_external"] * max(0, n_idx - len(zones))
        static = pd.DataFrame(
            {
                "unit_id": list(fa.unit_ids),
                "plant_code": np.asarray(fa.plant_code).astype(int),
                "plant_group": np.asarray(fa.plant_group).astype(str),
                "zone": [zones[i] for i in np.asarray(fa.zone_idx)],
                "pmax": np.asarray(fa.pmax, float),
                "heat_rate": np.asarray(fa.heat_rate, float),
                "vom": np.asarray(fa.vom, float),
                "emission_rate": np.asarray(fa.emission_rate, float),
            }
        )
        static.to_parquet(pq)
        mg = fa.min_gen if fa.min_gen is not None else np.zeros_like(state["mc_base"])
        np.savez_compressed(
            npz,
            mc=state["mc_base"][:, :T],
            fuel=state["fuel_prices"][:, :T],
            avail=np.asarray(fa.availability, float)[:, :T],
            min_gen=np.asarray(mg, float)[:, :T],
        )
    z = np.load(npz)
    return {
        "static": pd.read_parquet(pq),
        "mc": z["mc"],
        "fuel": z["fuel"],
        "avail": z["avail"],
        "min_gen": z["min_gen"],
    }


def write_json(name: str, rec: dict) -> Path:
    """Write a probe record under ``results/calibration/`` and return its path."""
    out = REPO / "results" / "calibration" / name
    out.write_text(json.dumps(rec, indent=2, default=float))
    print(f"wrote {out.relative_to(REPO)}")
    return out
