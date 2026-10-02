"""R-CAISO-33 G-RT: does the re-based offer surface round-trip to the keeper's measured bids? ZERO LP.

Pre-registered in ``PRECOMMIT-r-caiso-33-joint-gas-rebasis-2026-10-02.md`` §4.1:
for every consumed class and band, per year, the re-derived multiplier evaluated
on the DELIVERED series must reproduce the keeper multiplier evaluated on the
bare composite within ±$0.75/MWh at the class base heat rate::

    |m_new,y x HR x (g_y + a + c_y)  -  m_keeper,y x HR x (g_y + c_y)| <= 0.75

with ``g_y`` the keeper's own flow-dated composite annual mean, ``a`` the
transport adder and ``c_y = 0.057 x P_CO2,y``. The keeper artifact is read from
``main`` at the keeper's pin (``git show``), the re-based one from the working
tree. Pooled bands are compared the same way at the 2023-25 mean gas.

Usage::

    python3 scripts/probes/_rcaiso33_roundtrip_gate.py [--keeper-sha SHA]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    CAISO_CITYGATE_TRANSPORT_ADDER,
    STATE_CARBON_PRICE_BY_ISO,
)

ARTIFACT = "data/raw/_validation-source/caiso_offer_curve_measured.json"
OUT = REPO / "docs/records/caiso/r-caiso-33/roundtrip_gate.json"
TOL = 0.75
CO2 = 0.057
BANDS = ("econ_low", "econ_high", "peak")


def main() -> int:
    """Compare keeper vs re-based multipliers in $/MWh; write the gate table; exit 1 on FAIL."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--keeper-sha", default="cd5897987106193b34b84c5f4bb4a7c9bb1e4760")
    args = ap.parse_args()
    old = json.loads(
        subprocess.check_output(
            ["git", "show", f"{args.keeper_sha}:{ARTIFACT}"], cwd=REPO
        )
    )
    new = json.loads((REPO / ARTIFACT).read_text())
    basis = json.loads(
        (REPO / "docs/records/caiso/r-caiso-33/transport_basis.json").read_text()
    )
    g = {int(k): v for k, v in basis["keeper_composite_annual_mean"].items()}
    a = CAISO_CITYGATE_TRANSPORT_ADDER
    rows = []
    ok = True
    for cls in (c for c in new if not c.startswith("_")):
        hr = new[cls]["base_hr"]
        assert abs(hr - old[cls]["base_hr"]) < 1e-9, (cls, hr, old[cls]["base_hr"])
        po = old["_provenance"]["per_year_band_mults"][cls]
        pn = new["_provenance"]["per_year_band_mults"][cls]
        for band in BANDS:
            for y in (2023, 2024, 2025):
                c = CO2 * STATE_CARBON_PRICE_BY_ISO["CAISO"][y]
                k = po[band][str(y)] * hr * (g[y] + c)
                r = pn[band][str(y)] * hr * (g[y] + a + c)
                d = r - k
                rows.append(
                    {
                        "class": cls,
                        "band": band,
                        "year": y,
                        "keeper_usd_mwh": round(k, 2),
                        "rebased_usd_mwh": round(r, 2),
                        "delta": round(d, 2),
                        "pass": abs(d) <= TOL,
                    }
                )
                ok &= abs(d) <= TOL
            gm = sum(g[y] for y in (2023, 2024, 2025)) / 3
            cm = (
                CO2
                * sum(STATE_CARBON_PRICE_BY_ISO["CAISO"][y] for y in (2023, 2024, 2025))
                / 3
            )
            k = old[cls]["bands"][band] * hr * (gm + cm)
            r = new[cls]["bands"][band] * hr * (gm + a + cm)
            rows.append(
                {
                    "class": cls,
                    "band": band,
                    "year": "pooled",
                    "keeper_usd_mwh": round(k, 2),
                    "rebased_usd_mwh": round(r, 2),
                    "delta": round(r - k, 2),
                    "pass": abs(r - k) <= TOL,
                    "keeper_mult": old[cls]["bands"][band],
                    "rebased_mult": new[cls]["bands"][band],
                }
            )
            ok &= abs(r - k) <= TOL
    doc = {
        "gate": "G-RT",
        "tolerance_usd_mwh": TOL,
        "adder": a,
        "keeper_sha": args.keeper_sha,
        "pass": bool(ok),
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    for r in rows:
        print(
            f"{r['class']:11s} {r['band']:9s} {str(r['year']):6s} keeper {r['keeper_usd_mwh']:7.2f}  rebased {r['rebased_usd_mwh']:7.2f}  d {r['delta']:+5.2f}  {'ok' if r['pass'] else 'FAIL'}"
        )
    print("G-RT", "PASS" if ok else "FAIL", "->", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
