"""caiso-218 — bound-hour exceedance curves on the committed caiso-217 recon.

NO LP, NO SOLVE — the licensed input-assembly reconstruction only (the same
caiso-105/131 ``run_year(fleet_only=True)`` channel the committed caiso-216/217
probes use, via the caiso-217 wrapper's cache namespace so the crosswalk-ACTIVE
recon is reused byte-identically).

Context (FINDING-caiso218-path-limit-survey-2026-08-24.md): the Phase-0 survey
found NO published cut-grain operating-limit series for the internal Path 15 /
Path 26 corridors 2023-2025 — CAISO discontinued the Path 15/26 TTC/ATC posting
2018-11-01 and no longer enforces the internal path branch groups; the real
market binds the corridor's CONSTITUENT ELEMENTS as individual flowgates whose
limits are published only as DMM annual-average scalars (element grain, not our
single-link cut grain, and not convertible without the restricted FNM shift
factors). These curves are therefore BOUNDING DIAGNOSTICS, never a proposed
input: for a grid of hypothetical single-link caps X they count the recon hours
whose cut surplus exceeds X — quantifying the CEILING of what any measured
tighter cut limit could have delivered, for the owner's adjudication of the
caiso-216 SF.3a successor lanes. Choosing an X from these curves (or from
reality's split-hour counts) as a model input would be an outcome pin —
rule 13 [R-MEASURED] — and is exactly what the caiso-218 fence forbids.

Controls: the rebuilt cut series must reproduce the committed caiso-217
S1'/cut26-L2 stats EXACTLY (hours-over-path, belly mean, max) before any curve
is written — proving the series measured here IS the committed caiso-217 recon.

Writes ``results/calibration/_caiso218_limit_whatif.json`` (deterministic:
sorted keys, rounded floats, no timestamps).

Usage:
    CAISO217_CACHE=<scratch>/caiso217_recon \
        PYTHONPATH=.:src python3 scripts/probes/_caiso218_limit_whatif.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _caiso217_realized_membership as c217  # noqa: E402  (committed wrapper)

c216 = c217.c216  # the committed caiso-216 instrument, caiso-217 cache namespace

OUT_JSON = REPO / "results/calibration/_caiso218_limit_whatif.json"
COMMITTED = REPO / "results/calibration/_caiso217_realized_membership.json"

#: Cap grids (MW). Dense 250-MW steps bracketing each cut's armed rating, plus
#: the DMM-2023-published element-grain average binding limits as labeled marks
#: (2023 Annual Report on Market Issues and Performance, ch. 6: Moss
#: Landing-Las Aguilas 340 MW, Tesla-Los Banos #1 1,600 MW, Midway-Vincent #2
#: 2,100 MW, Gates-Midway #1 2,500 MW, Panoche-Gates #2 200 MW,
#: 6410_CP1_NG 1,600 MW). Element limits are NOT cut limits — the marks are
#: reference points on the curve, not candidate inputs.
GRID15 = sorted(set(range(0, 6001, 250)) | {340, 1600, 2100, 2500, 3265, 5400})
GRID26 = sorted(set(range(0, 4001, 250)) | {200, 1600, 2100, 3000})
DMM_MARKS = {
    "200": "Panoche-Gates #2 230kV (DMM 2023 avg binding limit)",
    "340": "Moss Landing-Las Aguilas 230kV (DMM 2023 avg binding limit)",
    "1600": "Tesla-Los Banos #1 500kV / 6410_CP1_NG (DMM 2023)",
    "2100": "Midway-Vincent #2 500kV (DMM 2023 avg binding limit)",
    "2500": "Gates-Midway #1 500kV (DMM 2023 avg binding limit)",
    "3000": "Path 26 S->N WECC catalog rating (armed)",
    "3265": "Path 15 N->S WECC catalog rating",
    "5400": "Path 15 S->N WECC catalog rating (armed)",
}


def cut_l2_series(year: int) -> dict[str, np.ndarray]:
    """Rebuild the caiso-217 realized cut-15/cut-26 L2 surplus series.

    Mirrors ``_caiso216_belly_surplus.main`` (B2 block) exactly, on the
    caiso-217 crosswalk-ACTIVE recon cache.
    """
    rc = c216.recon(year)
    sc = c216.sidecars(year)
    zmap = c216.match_zone_rows(rc["demand"], sc["demand"])
    missing = [z for z in c216.CA_ZONES if z not in zmap]
    if missing:
        raise SystemExit(f"{year}: zone row match failed for {missing}")
    for z, j in zmap.items():
        err = float(np.nanmax(np.abs(rc["demand"][j] - sc["demand"][z].to_numpy())))
        if err > 0.5:
            raise SystemExit(f"{year}: demand row mismatch {z} ({err:.2f} MW)")

    dem_z = np.stack([sc["demand"][z].to_numpy() for z in c216.CA_ZONES])
    zshare = dem_z.sum(axis=1) / dem_z.sum()
    inj_iso = np.zeros(c216.HOURS)
    for kl in ("biomass", "OTHER"):
        if kl in sc["klass"].columns:
            inj_iso = inj_iso + sc["klass"][kl].to_numpy()

    out: dict[str, np.ndarray] = {}
    for cut, zones in c216.CUT_ZONES.items():
        zi = [zmap[z] for z in zones]
        zsel = [c216.CA_ZONES.index(z) for z in zones]
        dem = rc["demand"][zi].sum(axis=0)
        ren = rc["solar_pot"][zi].sum(axis=0) + rc["wind_pot"][zi].sum(axis=0)
        nuc = rc["nuclear_mw"][zi].sum(axis=0)
        inj = inj_iso * float(zshare[zsel].sum())
        out[cut] = ren + nuc + inj - dem
    return out


def main() -> None:
    from market_sim.data.zone_assignment import load_caiso_hub_membership

    membership = load_caiso_hub_membership()
    if not membership:
        raise SystemExit(
            "caiso-plant-hub-membership.csv is absent — these curves measure "
            "the committed caiso-217 (post-crosswalk) recon only"
        )
    print(f"hub-membership crosswalk ACTIVE: {len(membership)} plants")

    committed = json.loads(COMMITTED.read_text())
    hod = c216.hod_of_hour()
    belly = (hod >= c216.BELLY[0]) & (hod <= c216.BELLY[1])

    out: dict = {
        "grids_mw": {"cut15": GRID15, "cut26": GRID26},
        "dmm_marks": DMM_MARKS,
        "years": {},
    }
    for year in c216.YEARS:
        series = cut_l2_series(year)
        cyr = committed["years"][str(year)]["B2_surplus"]
        yr: dict = {"controls": {}, "curves": {}, "reality_hours_committed": {}}
        for cut, grid in (("cut15", GRID15), ("cut26", GRID26)):
            s = series[cut]
            ref = cyr[cut]["L2_plus_injected"]
            got = {
                "hours_over_path": int((s > c216.SN_CAP[cut]).sum()),
                "belly_mean_mw": float(np.round(s[belly].mean(), 2)),
                "max_mw": float(np.round(np.max(s), 2)),
                "hours_pos": int((s > 0).sum()),
            }
            ctrl = {k: [got[k], ref[k], got[k] == ref[k]] for k in got}
            yr["controls"][cut] = ctrl
            if not all(v[2] for v in ctrl.values()):
                raise SystemExit(
                    f"{year} {cut}: rebuilt series does not reproduce the "
                    f"committed caiso-217 stats — {ctrl}"
                )
            yr["curves"][cut] = {
                str(x): {
                    "hours_all": int((s > x).sum()),
                    "hours_belly": int((s[belly] > x).sum()),
                }
                for x in grid
            }
            yr["reality_hours_committed"][cut] = cyr[cut]["reality_hours"]
        out["years"][str(year)] = yr
        print(
            f"{year}: controls exact for both cuts; "
            f"cut15 h>5400={yr['curves']['cut15']['5400']['hours_all']} "
            f"(committed {cyr['cut15']['L2_plus_injected']['hours_over_path']})"
        )

    # Cross-year identifiability reading: for each candidate X, the recon's
    # year-vector of bound hours vs reality's committed split-hour vector.
    # Reported as data — the structural conclusion lives in the FINDING.
    ident = {}
    for x in GRID15:
        ident[str(x)] = [
            out["years"][str(y)]["curves"]["cut15"][str(x)]["hours_all"]
            for y in c216.YEARS
        ]
    out["cut15_hours_by_cap_2023_2024_2025"] = ident
    out["reality_split_gt15_committed"] = [
        committed["years"][str(y)]["B2_surplus"]["cut15"]["reality_hours"][
            "split_gt15"
        ]
        for y in c216.YEARS
    ]

    OUT_JSON.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
