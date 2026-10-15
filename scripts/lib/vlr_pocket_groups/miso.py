"""MISO ``vlr-pocket-groups`` spec: the MTEP15 VLR study's Scenario-1C groups.

Source: PUCT Docket 46416, Exhibit CWL-5 (MTEP15 VLR study), pp.12–13 — groups
A (Amite South), B (DSG), C–E (WOTAB) and F (Western) of the op-guide VLR
units; see ``data/raw/vlr-pocket-groups/README.md``.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(IsoSpec(iso="MISO"))
