"""R-CAISO-7 Object 1 (ZERO LP): where the 2019-21 CC_REGULAR excess comes from.

Reads the R-CAISO-6 fold legs' full bundles straight from their shard commits
(``git archive <sha>``, rule 33(d) provenance SHAs) into a temp dir, and the
measured EIA-930 corridor net import
(``derive_caiso_import_tranches.corridor_net_import``). Reports, per year:

* model vs EIA-930 net import, per corridor (PNW / DSW) and window;
* per import tranche: capability, energy, offer price, and the first-order
  energy the tranche would add if priced at the MEASURED intertie hub in the
  hours the hub prints (2021 only: 5,976 of 8,760 h) -- no price feedback, an
  upper bound;
* the SP15_rest>SDGE link under the per-year LCT import caps: binding hours,
  SDGE price, unserved energy.

Writes ``results/calibration/_rcaiso7/object1_census.json``.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso7_dsw_import_census.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]
from market_sim.config.interchange_config import (  # noqa: E402
    CAISO_IMPORT_DELIVERY_BASIS,
    CARB_UNSPECIFIED_IMPORT_EF,
    IMPORT_TRANCHE_EF,
)
from market_sim.data.eia_loader import measured_intertie_hub_price_raw  # noqa: E402
from scripts.data.derive_caiso_import_tranches import corridor_net_import  # noqa: E402

LEGS = {  # R-CAISO-6 RESULT, "Leg provenance"
    2019: "11d774b8f12996441fa8d00c9a1a1db59c540fc5",
    2020: "daee04299af666298d007cb540642bb93069e41d",
    2021: "e419162ab6c039a8ac72709fd055724d7b832f08",
}
HUB = {"WECC_DSW": "PALOVRDE", "WECC_PNW": "MALIN"}
OUT = Path("results/calibration/_rcaiso7/object1_census.json")


def _extract(tmp: Path, year: int) -> Path:
    """Unpack one leg bundle from its shard commit; return the bundle dir."""
    path = f"results/calibration/rcaiso6_O2_{year}"
    arc = subprocess.run(
        ["git", "archive", LEGS[year], path], check=True, capture_output=True
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(tmp)], input=arc, check=True)
    return tmp / path


def _carbon_from_scarcity(u: pd.DataFrame) -> float:
    """Recover the run's allowance price from the $180 scarcity rung's mc."""
    mc = float(u.loc[u.unit_id == "WECC_DSW_WECC_scarcity", "mc"].iloc[0])
    return (mc - 180.0) / CARB_UNSPECIFIED_IMPORT_EF


def census_year(b: Path, year: int, meas: pd.DataFrame) -> dict:
    """Return the Object 1 census for one fold year."""
    u = pd.read_parquet(
        b / f"hourly/unit_hourly_{year}.parquet",
        filters=[("zone", "in", ["WECC_PNW", "WECC_DSW"])],
    )
    lam = pd.read_parquet(b / f"hourly/system_{year}.parquet")
    lamp = lam.pivot(index="hour", columns="zone", values="price")
    border = CARB_UNSPECIFIED_IMPORT_EF * _carbon_from_scarcity(u)
    hod = np.arange(8760) % 24
    win = {
        "h0_6": hod <= 6,
        "h8_16": (hod >= 8) & (hod <= 16),
        "h17_22": (hod >= 17) & (hod <= 22),
    }
    out: dict = {"corridors": {}, "tranches": {}}
    for z in ("WECC_PNW", "WECC_DSW"):
        m = (
            u[u.zone == z]
            .groupby("hour")
            .mw.sum()
            .reindex(range(8760))
            .fillna(0)
            .to_numpy()
        )
        a = meas.loc[year][z].reindex(range(8760)).to_numpy()
        d = m - a
        out["corridors"][z] = {
            "model_twh": round(m.sum() / 1e6, 2),
            "eia930_twh": round(np.nansum(a) / 1e6, 2),
            **{
                f"excess_mw_{k}": round(float(np.nanmean(d[v]))) for k, v in win.items()
            },
        }
    add_total = 0.0
    for uid, g in u.groupby("unit_id"):
        z = g.zone.iloc[0]
        name = uid[len(z) + 1 :]
        g = g.sort_values("hour")
        cap, mw, mc = (g[c].to_numpy() for c in ("cap_mw", "mw", "mc"))
        rec = {
            "cap_mean_mw": round(float(cap.mean())),
            "twh": round(mw.sum() / 1e6, 2),
            "offer_mean": round(float(mc.mean()), 1),
        }
        hub = measured_intertie_hub_price_raw("CAISO", year, 8760, HUB[z])
        if (
            hub is not None
            and not name.startswith("export")
            and name
            not in (
                "PNW_hydro_base",
                "DSW_solar_PV",
                "WECC_scarcity",  # firm / placeholder
            )
        ):
            _loss, wheel = CAISO_IMPORT_DELIVERY_BASIS.get(name, (0.0, 0.0))
            ef = IMPORT_TRANCHE_EF["CAISO"].get(name, CARB_UNSPECIFIED_IMPORT_EF)
            mc_meas = hub + wheel + border * ef / CARB_UNSPECIFIED_IMPORT_EF
            fin = np.isfinite(hub)
            clear = fin & (mc_meas < lamp[z].to_numpy()[:8760])
            add = float(np.where(clear, cap - mw, 0.0).clip(0).sum() / 1e6)
            rec["measured_hours"] = int(fin.sum())
            rec["first_order_add_twh"] = round(add, 2)
            add_total += add
        out["tranches"][uid] = rec
    out["first_order_add_twh_total"] = round(add_total, 2)
    net = pd.read_parquet(b / f"hourly/network_{year}.parquet")
    link = net[net.name == "SP15_rest>SDGE"]
    sd = lam[lam.zone == "SDGE"]
    out["sd_pocket"] = {
        "link_limit_mw": float(link.limit_up.iloc[0]),
        "binding_hours": int((link.dual.abs() > 1e-6).sum()),
        "sdge_price_mean": round(float(sd.price.mean()), 1),
        "sp15_price_mean": round(float(lam[lam.zone == "SP15_rest"].price.mean()), 1),
        "sdge_hours_gt_500": int((sd.price > 500).sum()),
        "sdge_unserved_mwh": round(float(sd.slack.sum())),
    }
    return out


def main() -> None:
    """Run the census over the three fold years and write the JSON."""
    meas = corridor_net_import(years=tuple(LEGS))
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        for y in LEGS:
            res[str(y)] = census_year(_extract(Path(tmp), y), y, meas)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(
        json.dumps(
            {
                y: {k: v for k, v in r.items() if k != "tranches"}
                for y, r in res.items()
            },
            indent=1,
            default=float,
        )
    )


if __name__ == "__main__":
    main()
