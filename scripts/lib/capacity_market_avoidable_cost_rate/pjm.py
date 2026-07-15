"""PJM capacity-market-avoidable-cost-rate spec (the only ISO registered).

PJM's Tariff/Manual 18 deactivation and capacity must-offer-exception process
lets a unit justify its case against PJM's own published DEFAULT (generic)
gross Avoidable Cost Rate by technology class
(``source_type=pjm_manual18_default``); Monitoring Analytics (the Independent
Market Monitor) separately publishes its own avoidable-cost benchmark tables
in the State of the Market report (``source_type=monitoring_analytics_som``).
Both land in the same unified CSV, distinguished by ``source_type``.

Uses the default unified-CSV parser; no metric aliasing needed (this
datatype's column is already named ``cost_component``, not a legacy native
name).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(IsoSpec(iso="PJM"))
