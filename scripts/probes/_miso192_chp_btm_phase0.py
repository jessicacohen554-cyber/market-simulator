"""miso-192 phase-0 (ZERO-SOLVE): is ``chp_btm_measured`` IDENTIFIABLE for MISO?

Charter: owner ruling in session miso-192 (2026-08-31), after the miso-192
census established that MISO's lever queue was empty only of *curated* names
while 32 backcast-touching matrix cells sat ``U``/``O``.  ``chp_btm_measured``
was selected as the next charter: a MEASURED-INPUT accuracy item (rule 14
[R-ACCURATE] / rule 13 [R-MEASURED]) that is keeper-armed at NYISO and
right-signed for C3a-2025 (more CHP behind the meter => more grid load the
modelled fleet must serve).

WHAT THE MECHANISM IS (nyiso-147, the construction this session must either
reproduce from MISO's OWN data or refuse).  Two INDEPENDENT published meters:

    grid_share = <ISO settlement-metered net energy, per station, per year>
                 / <EIA-923 Page-1 net generation, per plant-year>
    btm_pct    = 100 * clip(1 - grid_share, 0, 1)

NYISO's numerator is the Gold Book Table III-2a "Net Energy GWh".  Rule 25
[R-ISO-SCOPE] and rule 28(d): NYISO's VALUES transfer nothing.  Only the
CONSTRUCTION may transfer, and only if MISO publishes its own numerator.

THE ADJUDICATION RULE, FROZEN HERE BEFORE ANY QUANTITY IS COMPUTED
------------------------------------------------------------------
This is a DATA-EXISTENCE question, so the rule is existential, not numeric.

  CANDIDATE  iff  a per-plant (or per-station, PTID/ORISPL-mappable) MISO-side
             annual grid-delivered / settlement-metered ENERGY series exists,
             published by MISO or a MISO-designated body, INDEPENDENT of
             EIA-923, and covering a material share of MISO's CHP fleet.
             "Material" is fixed ex ante at >= 50% of MISO CHP nameplate in
             the CC_CHP + ST_CHP + CT_CHP classes, matching the coverage line
             miso-141 SS11.2 used to refuse a 52%-coverage repair as
             insufficient.

  REFUSE     otherwise.  Two named sub-cases, both zero-solve:
             (a) NO SECOND METER — MISO publishes no per-plant delivered-energy
                 series at all.  The two-meter identity cannot be formed.
                 Verdict G (data/governance-refused), NOT R: the mechanism is
                 sound, MISO's published record cannot identify it.
             (b) AGGREGATE ONLY — a MISO-side wedge exists but only in
                 aggregate (BA-level EIA-930, an IMM total).  Deriving
                 per-plant shares from it requires INVENTING an apportionment.
                 That is refused on the miso-176 K-2 precedent (no published
                 seam-grain entitlement aggregate may be apportioned) and
                 rule 24 [R-REGISTRY].  Verdict G.

  In EITHER refuse case the sector default stays, and this session states
  plainly that MISO's incumbent ``CHP_BTM_PCT_BY_SECTOR["merchant"] = 35.0``
  is self-declared residual-identified ("no independent source yet") -- i.e.
  the refusal LEAVES A KNOWN RULE-13 WEAKNESS IN PLACE and says so, rather
  than papering it with an invented number.

NO LP IS SOLVED BY THIS PROBE.  It reads committed artifacts and the on-disk
data roots only.  Rule 22 [R-HOLDOUT]: no year outside 2023-2025 is read.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_miso192_chp_btm_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

RAW = REPO / "data" / "raw"
OUT = REPO / "results" / "calibration" / "_miso192_chp_btm_phase0.json"

# Probe hygiene (miso-140b SS6): assert a shared loader resolves, so the
# sys.path insertion above cannot rot silently even though this probe does
# not consume per-zone demand.
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia930.zonal_shares import load_zonal_shares  # noqa: E402

_ISO_CFG = get_iso_config("MISO")
_ZONES = [z.name for z in _ISO_CFG.zones]
assert (
    load_zonal_shares("MISO", 2024, _ZONES) is not None
), "load_zonal_shares('MISO', 2024, <zones>) is None"
