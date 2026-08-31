"""CAISO gas-ofo-events spec — the SoCalGas OFO/EFO declaration ledgers.

CAISO's gas-fired fleet in SP15 burns gas delivered on the Southern California
Gas Company (SoCalGas) system, whose Operational Flow Orders are the physical
deliverability events behind the ISO's winter gas-scarcity days. SoCalGas
publishes both event histories on its ENVOY portal with no authentication, each
as a single table with one column per year (see
:func:`scripts.lib.gas_ofo_events.parse_envoy_year_column_table`).

The LOW ledger is the one that matters for winter deliverability: it reaches
back to 2015 and its stages escalate 1 -> 2 -> 3 -> 3.1/3.2/3.3 -> 4 -> 5 as
the tolerance band tightens from -5 percent. The HIGH ledger reaches back to
1997 but carried no stage before mid-2018, so its early rows land with a null
``stage`` by construction.

``DATA NEEDED``: Pacific Gas & Electric publishes its own OFO record for the
NP15 half of the CAISO footprint on a different portal with a different layout.
It is NOT yet retrieved. Adding it is one more :class:`OfoSource` here plus a
reader in :data:`scripts.lib.gas_ofo_events.READERS` — no shared-code change.
See ``data/raw/gas-ofo-events/README.md``.
"""

from __future__ import annotations

from . import IsoSpec, OfoSource, register

#: SoCalGas ENVOY public endpoints (no authentication) the snapshots come from.
ENVOY_LOW_OFO_URL = (
    "https://www.socalgas-envoy.com/Public/ViewExternalLowOFO.getLowOFOEvent"
)
ENVOY_HIGH_OFO_URL = "https://www.socalgas-envoy.com/Public/ViewExternalOFO.getOFOEvent"

SPEC = register(
    IsoSpec(
        iso="CAISO",
        sources=(
            OfoSource(
                utility="SOCALGAS",
                side="low",
                filename="socalgas_low_ofo_events.html",
                url=ENVOY_LOW_OFO_URL,
            ),
            OfoSource(
                utility="SOCALGAS",
                side="high",
                filename="socalgas_high_ofo_events.html",
                url=ENVOY_HIGH_OFO_URL,
            ),
        ),
    )
)
