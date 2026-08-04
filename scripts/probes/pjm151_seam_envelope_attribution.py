"""pjm-151 Phase 2 — measure the PJM seam-envelope attribution defect (NO LP, NO SOLVE).

Keeper-note item 12 charges an internal inconsistency between two modules that
attribute the SAME physical seam differently:

* ``data/eia930/envelopes.py::_PJM_TIE_ZONE`` maps each PJM tie line to ONE
  model border zone (``"TVA": "PJM_Dominion"``).
* ``model/interchange/spec.py::INTERFACE_NEIGHBORS["PJM"]`` gives the TVA
  interface ``border_zones = ("PJM_AEP_Ohio", "PJM_Dominion")`` — two zones.

This probe measures what that costs, because the two structures are not
independent: :func:`model.interchange.pjm.inject_pjm_seam_flow_limit` builds a
per-ZONE (month x hour-of-day) p90 deliverability envelope from
``_PJM_TIE_ZONE`` and then SUMS it over each neighbour's ``border_zones`` to get
that neighbour's import/export cap. So a zone bucket holding several
counterparties' ties feeds every neighbour whose ``border_zones`` names it.

It reports, per (neighbour, year, direction), the cap the keeper actually
applies against the cap built DIRECTLY from that neighbour's own tie lines --
the construction that needs no zone attribution and therefore no derived share.

Rule 13 [R-MEASURED]: both constructions are measured deliverability envelopes
off PJM's own settlement-grade tie-line flow file; neither is fitted to a
residual. Rule 14 [R-ACCURATE] is the charter.

Usage:
    PYTHONPATH=.:src python scripts/probes/pjm151_seam_envelope_attribution.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TIE_DIR = REPO / "data/raw/iso-specific-transmission"
OUT = REPO / "results/calibration/_pjm151_seam_envelope_attribution.json"

YEARS = (2023, 2024, 2025)
PCT = 90.0  # constants.PJM_SEAM_FLOW_PERCENTILE

# Each PJM tie line -> the NAMED counterparty interface it belongs to. This is
# an identity, not a derivation: the tie-line label in PJM's own file IS the
# neighbouring balancing authority / utility, and INTERFACE_NEIGHBORS["PJM"]
# names the same five counterparties. Ties with no named interface are listed
# under None and excluded from every neighbour cap.
TIE_NEIGHBOR: dict[str, str | None] = {
    # MISO (Illinois / Iowa / Wisconsin / Dakotas / Indiana / Michigan)
    "AMIL": "MISO",
    "ALTE": "MISO",
    "ALTW": "MISO",
    "CWLP": "MISO",
    "MEC": "MISO",
    "WEC": "MISO",
    "MDU": "MISO",
    "LAGN": "MISO",
    "CIN": "MISO",
    "IPL": "MISO",
    "NIPS": "MISO",
    "SIGE": "MISO",
    "MECS": "MISO",
    # NYISO, incl. the three merchant HVDC/VFT cables
    "NYIS": "NYISO",
    "NEPT": "NYISO",
    "HUDS": "NYISO",
    "LIND": "NYISO",
    # Carolinas (Duke Progress East/West + Duke Carolinas)
    "CPLE": "Carolinas",
    "CPLW": "Carolinas",
    "DUK": "Carolinas",
    # single-counterparty seams
    "TVA": "TVA",
    "LGEE": "LGEE",
}

# The two live structures, copied verbatim so the probe measures the SHIPPED
# state rather than an import that could drift under it.
PJM_TIE_ZONE = {
    "NYIS": "PJM_EMAAC",
    "NEPT": "PJM_EMAAC",
    "HUDS": "PJM_EMAAC",
    "LIND": "PJM_EMAAC",
    "AMIL": "PJM_ComEd",
    "ALTE": "PJM_ComEd",
    "ALTW": "PJM_ComEd",
    "CWLP": "PJM_ComEd",
    "MEC": "PJM_ComEd",
    "WEC": "PJM_ComEd",
    "MDU": "PJM_ComEd",
    "LAGN": "PJM_ComEd",
    "CIN": "PJM_AEP_Ohio",
    "IPL": "PJM_AEP_Ohio",
    "NIPS": "PJM_AEP_Ohio",
    "SIGE": "PJM_AEP_Ohio",
    "LGEE": "PJM_AEP_Ohio",
    "OVEC": "PJM_AEP_Ohio",
    "MECS": "PJM_ATSI",
    "CPLE": "PJM_Dominion",
    "CPLW": "PJM_Dominion",
    "DUK": "PJM_Dominion",
    "TVA": "PJM_Dominion",
}
PJM_TIE_ZONE_DEFAULT = "PJM_ComEd"

BORDER_ZONES = {
    "MISO": ("PJM_ComEd", "PJM_AEP_Ohio", "PJM_ATSI"),
    "NYISO": ("PJM_EMAAC",),
    "Carolinas": ("PJM_Dominion",),
    "TVA": ("PJM_AEP_Ohio", "PJM_Dominion"),
    "LGEE": ("PJM_West_APS", "PJM_AEP_Ohio"),
}
INTERFACE_LIMIT_MW = {
    "MISO": 7300.0,
    "NYISO": 3900.0,
    "Carolinas": 2400.0,
    "TVA": 1600.0,
    "LGEE": 1100.0,
}


def load_ties(year: int) -> pd.DataFrame:
    """Return the year's tie-line flows on the model's non-leap 8760 clock."""
    path = TIE_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
    df = pd.read_csv(
        path, usecols=["datetime_beginning_ept", "tie_line", "actual_flow"]
    )
    ts = pd.to_datetime(df["datetime_beginning_ept"], format="mixed", errors="coerce")
    keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep].copy(), ts[keep]
    df["month"] = ts.dt.month.to_numpy()
    df["hod"] = ts.dt.hour.to_numpy()
    return df


def envelope_by_key(df: pd.DataFrame, key: pd.Series) -> dict[str, np.ndarray]:
    """(month x hod) p90 import/export envelope per group, export-positive input.

    ``actual_flow`` in PJM's file is import-positive at the tie; the model's
    ``pjm_zonal_interchange`` negates it to export-positive, and the envelope
    then splits the two directions. Reproduced exactly here.

    ORDER MATTERS AND IS NOT FREE: the group's ties are NETTED within the hour
    **before** the directional clip, exactly as ``pjm_zonal_interchange``'s
    ``np.add.at`` over signed flows does. Clipping per tie and then summing
    would report a group as importing 2.2 GW in hours when it was a net
    exporter — it adds up the import-side ties and throws away the simultaneous
    export-side ones. (It is the mistake this probe made on its first run: the
    MISO seam's import cap read 2,225 MW that way against a true netted 0.1 MW.)
    """
    work = df.assign(_k=key.to_numpy())
    work = work[work["_k"].notna()]
    work = work.assign(_exp_signed=-work["actual_flow"].to_numpy(dtype=float))
    hourly = (
        work.groupby(["_k", "month", "hod", "datetime_beginning_ept"], sort=False)[
            "_exp_signed"
        ]
        .sum()
        .reset_index()
    )
    signed = hourly["_exp_signed"].to_numpy(dtype=float)
    hourly = hourly.assign(
        _imp=np.clip(-signed, 0.0, None),  # net import into PJM
        _exp=np.clip(signed, 0.0, None),  # net export out of PJM
    )
    out: dict[str, np.ndarray] = {}
    for k, sub in hourly.groupby("_k", sort=True):
        tab = np.zeros((2, 12, 24))
        for (m, h), cell in sub.groupby(["month", "hod"], sort=False):
            tab[0, m - 1, h] = np.percentile(cell["_imp"].to_numpy(), PCT)
            tab[1, m - 1, h] = np.percentile(cell["_exp"].to_numpy(), PCT)
        out[str(k)] = tab
    return out


def main() -> None:
    """Measure and report the attribution gap for all five PJM seams."""
    result: dict[str, object] = {
        "_what": "pjm-151 Phase 2: PJM seam deliverability-cap attribution, "
        "keeper construction (per-zone bucket summed over border_zones) vs "
        "the direct per-neighbour construction. No LP, no solve.",
        "percentile": PCT,
        "years": {},
    }
    for year in YEARS:
        df = load_ties(year)
        zone_key = df["tie_line"].map(
            lambda t: PJM_TIE_ZONE.get(str(t), PJM_TIE_ZONE_DEFAULT)
        )
        nb_key = df["tie_line"].map(lambda t: TIE_NEIGHBOR.get(str(t)))
        zone_env = envelope_by_key(df, zone_key)
        nb_env = envelope_by_key(df, nb_key)

        rows = {}
        for nb, bzs in BORDER_ZONES.items():
            keeper = np.zeros((2, 12, 24))
            for z in bzs:
                if z in zone_env:
                    keeper += zone_env[z]
            direct = nb_env.get(nb, np.zeros((2, 12, 24)))
            lim = INTERFACE_LIMIT_MW[nb]
            rows[nb] = {
                "border_zones": list(bzs),
                "zones_with_ties": [z for z in bzs if z in zone_env],
                "interface_limit_mw": lim,
                "import": {
                    "keeper_mean_mw": round(float(keeper[0].mean()), 1),
                    "direct_mean_mw": round(float(direct[0].mean()), 1),
                    "ratio": round(
                        float(keeper[0].mean() / max(direct[0].mean(), 1e-9)), 3
                    ),
                    "keeper_binds_frac": round(float((keeper[0] < lim).mean()), 3),
                    "direct_binds_frac": round(float((direct[0] < lim).mean()), 3),
                },
                "export": {
                    "keeper_mean_mw": round(float(keeper[1].mean()), 1),
                    "direct_mean_mw": round(float(direct[1].mean()), 1),
                    "ratio": round(
                        float(keeper[1].mean() / max(direct[1].mean(), 1e-9)), 3
                    ),
                    "keeper_binds_frac": round(float((keeper[1] < lim).mean()), 3),
                    "direct_binds_frac": round(float((direct[1] < lim).mean()), 3),
                },
            }
        result["years"][str(year)] = {
            "zone_bucket_mean_mw": {
                z: {
                    "import": round(float(t[0].mean()), 1),
                    "export": round(float(t[1].mean()), 1),
                }
                for z, t in sorted(zone_env.items())
            },
            "neighbors": rows,
        }

    OUT.write_text(json.dumps(result, indent=2))
    print(f"wrote {OUT}")
    for year, block in result["years"].items():  # type: ignore[union-attr]
        print(f"\n=== {year} ===")
        print(
            f"{'neighbor':<11}{'dir':<8}{'keeper MW':>11}{'direct MW':>11}"
            f"{'ratio':>8}{'lim MW':>9}{'keeper binds':>14}{'direct binds':>14}"
        )
        for nb, r in block["neighbors"].items():
            for d in ("import", "export"):
                print(
                    f"{nb:<11}{d:<8}{r[d]['keeper_mean_mw']:>11.1f}"
                    f"{r[d]['direct_mean_mw']:>11.1f}{r[d]['ratio']:>8.2f}"
                    f"{r['interface_limit_mw']:>9.0f}"
                    f"{r[d]['keeper_binds_frac']:>14.3f}"
                    f"{r[d]['direct_binds_frac']:>14.3f}"
                )


if __name__ == "__main__":
    main()
