"""FF-2A entry-stack sizing/lag registry (gated constants).

Per-domain config module (the ``reserve_config.py`` / ``interchange_config.py``
pattern): the externally identified parameters of the FF-2A entry-stack gates
(``ScenarioConfig.entry_rate_limits`` / ``entry_commissioning_lag``). Every
value carries its citation here and a row in ``docs/parameter-citations.md``
(rule 5); none is ever residual-tuned (rule 23).
"""

# Growth-ladder hard bound on annual entry builds: a technology's annual build
# may not exceed this multiple of its PRIOR MAXIMUM annual build in the ISO
# (seeded from the measured EIA-860 record at the run's vintage —
# data.build_throughput.max_annual_build_gw_by_tech — and rising endogenously
# as the model builds, since the prior max includes model-year builds). This is
# the ReEDS growth-constraint hard bound adopted verbatim: "growth rates are
# not allowed to exceed 200% of the prior maximum" annual installation rate
# (NREL, Regional Energy Deployment System (ReEDS) Model Documentation 2025,
# growth-constraints section; the documentation's intermediate capital-cost
# penalty bands at 130-175%/175-200% are NOT adopted — a screening model has
# no capex-penalty channel, and a fitted penalty would be a rule-13/14
# violation; adopting only the published hard bound keeps the constraint
# zero-DOF). Applied per tech to the economic new-entry screen and, for
# gas_ct, shared with the reserve-margin backstop (one physical queue —
# rule 19: the backstop and economic entry draw one throughput budget).
ENTRY_GROWTH_LIMIT_MULTIPLE: float = 2.0

# Trailing window (years) for the measured prior-max annual-build seed. The
# seed is the max annual COD MW by tech/ISO over the window ending at the
# run's EIA-860 vintage. Ten years bounds the seed to the modern (post-FERC
# LGIP cluster-reform era) interconnection-throughput regime — LBNL "Queued
# Up" 2024 measures the regime shift directly (median IR→COD doubled from
# <2 yr for 2000-2007 builds to >4 yr for 2018-2023 builds), so a 2001-03
# gas-boom COD rate is not evidence of today's deliverable throughput
# (e.g. PJM added 7.5 GW of gas CT in 2001 alone vs a 2011-2020 max of
# 0.55 GW/yr). Windowing choice, declared here, never residual-tuned.
ENTRY_THROUGHPUT_WINDOW_YEARS: int = 10

# Clearance→COD lag (years) for economic new entry, by technology (gated:
# ScenarioConfig.entry_commissioning_lag). The screen's economic clearance is
# the developer's commitment decision (≈ executed interconnection agreement +
# FID); the lag to commercial operation is the measured LBNL "Queued Up" 2024
# median IA→COD duration: "~25 months for projects built from 2016-2023"
# (LBNL Queued Up 2024 edition, duration analysis, 861-project sample) →
# 2 years, applied uniformly. LBNL notes standalone batteries complete this
# phase fastest and wind slowest, but publishes no per-tech medians for the
# IA→COD leg, so the uniform median is the honest zero-DOF value; a per-tech
# refinement from the on-disk EIA-860 proposed-pipeline vintages is recorded
# as future work (ff-entry-stack-completion-2026-07.md). Techs absent from
# the mapping default to ENTRY_COD_LAG_DEFAULT_YEARS.
ENTRY_COD_LAG_YEARS: dict[str, int] = {
    "wind": 2,
    "solar": 2,
    "gas_cc": 2,
    "gas_ct": 2,
}
ENTRY_COD_LAG_DEFAULT_YEARS: int = 2
