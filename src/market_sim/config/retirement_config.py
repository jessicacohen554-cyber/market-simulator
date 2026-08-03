"""FFR-3F exit-throughput registry (gated constants).

Per-domain config module (the ``entry_config.py`` / ``reserve_config.py``
pattern), and the deliberate mirror of ``entry_config.py``: these are the
externally identified parameters of the exit side of the same physical
queue the entry gates bound on the build side
(``ScenarioConfig.exit_rate_limits``). Every value carries its citation here
and a row in ``docs/parameter-citations.md`` (rule 5); none is ever
residual-tuned (rule 23 ``[R-FROZEN-DERIVE]``).

**Why this module exists.** Owner decision D-8 (2026-08-03,
``docs/handoffs/ffr-owner-sitting-2026-08-02.md`` Addendum F.1) ruled that
queue **latency** and queue **throughput** are TWO mechanisms for rule 19
``[R-ONE-MECH]`` purposes. The R-NEW retirement pipeline models the latency
(``retirement_execution_lag_*`` — how long after the decision a unit leaves)
and, since the FF-1A deletion of ``staged_oversupply_thinning``, nothing
modelled the throughput (how many MW may leave in one year). FFR-3C §1.2
measured the consequence directly: with only a latency term, **exit-wave
width is invariant at exactly one year no matter how many units fail**, while
the entry side is held to 2x its own measured record — the asymmetry FFR-3C
§1.4 attributes the depth of the reserve-margin trough to.
"""

# Hard bound on the MW of thermal capacity that may DEACTIVATE in one year,
# as a multiple of the ISO's measured maximum single-year thermal
# deactivation (data.build_exit_throughput.max_annual_exit_gw, read from the
# EIA-860 retired sheet at the run's vintage).
#
# The value is the entry side's own discipline, transferred unchanged rather
# than chosen: ``entry_config.ENTRY_GROWTH_LIMIT_MULTIPLE`` is 2.0 (the ReEDS
# growth-constraint hard bound, "not allowed to exceed 200% of the prior
# maximum"), and owner decision D-2 armed it on the build side. FFR-3C §1.4's
# finding is precisely the ASYMMETRY that resulted — "exit throughput
# uncapped; replacement throughput capped at 2x the historical record" — so
# the structurally faithful repair (rule 1 ``[R-STRUCT]``) is to hold both
# sides of one queue to ONE envelope, not to pick a second number for the
# exit side. Adopting the entry multiple verbatim keeps this zero-DOF: there
# is no exit-side multiplier to fit, and none was fitted (rules 11/23 — this
# constant may not move because a residual moved).
EXIT_THROUGHPUT_LIMIT_MULTIPLE: float = 2.0

# Trailing window (years) for the measured maximum-single-year-deactivation
# seed, ending at the run's EIA-860 vintage. Eleven years reproduces the
# identification owner decision D-8 cites verbatim (FFR-3C §1.4, measured
# 2015-2025: MISO 7.57 GW, PJM 5.24, ERCOT 4.42, CAISO 1.48, NEISO 0.45,
# NYISO 0.31), so the shipped cap is the one the decision was taken against.
#
# Declared windowing choice, never residual-tuned — and for the ISOs this
# term is tested on it carries NO degrees of freedom at all, which was
# measured rather than assumed (FFR-3F §2.2): MISO / PJM / ERCOT return the
# identical maximum (7.46 / 5.24 / 4.42 GW) under the 11-year window, the
# entry side's 10-year window, and the UNWINDOWED full EIA-860 retired record
# back to 1978, at both the 2023 and 2025 vintages. Only CAISO / NEISO /
# NYISO — none of them a test ISO here — are window-sensitive, because their
# largest deactivations predate 2015.
EXIT_THROUGHPUT_WINDOW_YEARS: int = 11
