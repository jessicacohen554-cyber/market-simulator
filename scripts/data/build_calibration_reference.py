"""Build the multi-year calibration reference dataset.

Calibration backcasts the dispatch model against historical years for which
EIA actuals exist (2021-2024). Each year needs year-specific renewable
capacity from EIA-860 (not the forward-projection ``RENEWABLE_INSTALLED_MW``
constants), the measured Henry Hub gas price, and a generation/emissions
benchmark to compare against.

This script extracts that reference data once and writes it under
``data/raw/_validation-source/`` so :mod:`scripts.run_calibration` (and any other
consumer) can read pre-computed values rather than re-deriving them:

* ``calibration_reference.json`` — the full reference: per ISO and year, the
  EIA-860 renewable capacity (December year-end totals, zone shares, monthly
  ramp factors, per-zone monthly capacity), the measured Henry Hub price, and
  the EIA-930 demand totals; plus the per-ISO eGRID 2023 generation/emissions
  benchmark shared across consumers.
* ``{ISO}_{year}_renewable_capacity.csv`` — one tidy CSV per ISO-year with
  the per-zone, per-month EIA-860 operable wind and solar capacity (MW).

Every number here is a MEASURED OUTCOME used only as the SCORE (rule 13
``[R-MEASURED]``): nothing in this file is an input to a solve. The EIA-930
``NG:`` fuel series arrive already screened for unit-slip hours — the repair
lives at the loader seam (``eia930.actuals._screen_fuel_spike_columns``, lane
SPP-41), where every consumer inherits it, so this builder applies no screen
of its own (rule 19 ``[R-ONE-MECH]``; the builder-local ``_screen_fuel_spikes``
SPP-31 landed here was deleted, rule 26 ``[R-DELETE]``).

Run: ``python scripts/data/build_calibration_reference.py``
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
# Repo root FIRST: ``eia930.frames._read_clean_seam`` imports ``scripts.lib.
# clean_io`` lazily, and on a DIRECT run (``python scripts/data/build_calibration
# _reference.py``) sys.path[0] is this script's own directory, so that import
# fails, the seam resolves to ``None``, and every ``load_demand_meta`` call below
# silently falls back to the CORRUPTED legacy ``eia_demand_profiles`` summary —
# the demand block would then carry PJM 2021's 2.1e9 MW spike and SPP 2023's
# 3,621,097 MW unit slip as ``peak_mw``, and PJM 2019 (which the legacy summary
# has no row for at all) would hard-fail. The committed reference was built with
# the seam live, so this line reproduces it rather than changing it; the MISO
# builder carries the same insert for the same reason. Added 2026-09-07, lane
# SPP-31.
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import CALIBRATION_DIR, FLEET_DIR  # noqa: E402
from market_sim.data.eia923 import (  # noqa: E402
    EIA923_MONTHLY_GENERATION_PATH,
)
from market_sim.data.eia930 import (  # noqa: E402
    _EIA930_BENCHMARK_COLUMNS,
    _ISO_TO_HOURLY_BA,
    _eia_hourly_frame,
    _eia_hourly_frame_filled,
)
from market_sim.data.eia930.actuals import (  # noqa: E402
    _STORAGE_BENCHMARK_SERIES,
    _STORAGE_MIN_COVERAGE_FRAC,
    _ZERO_CODED_GAP_SERIES,
)
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand_meta,
    load_eia_hourly_benchmark,
)
from market_sim.data.fleet.models import (  # noqa: E402
    ISO_NERC_REGION_ADMISSION,
    ba_codes,
    footprint_plant_mask,
)
from market_sim.data.renewables import (  # noqa: E402
    _RENEWABLE_FUELS,
    _eia860_monthly_capacity,
)

# An incomplete current-year EIA-923 release (e.g. the 2025 early monthly
# survey, ~70% of plants reporting) silently under-counts every fuel — most
# severely the classes with no CEMS backfill: the variable renewables, and
# (SPP-47) conventional hydro, whose 2025 release is worse under-counted than
# either. When a benchmarked fuel's EIA-923 BA total falls below this fraction
# of the EIA-930 grid-side telemetry for that same fuel, it is sourced from
# EIA-930 instead (the authority the volume gate already uses for these
# classes, see results.calibration.actuals_source). Which fuels are tested is
# _incomplete_renewable_fuels' candidate set: wind and solar everywhere, plus
# the ISO's own _EIA923_EXTRA_FUELS_BY_ISO entries.
_EIA923_RENEWABLE_COMPLETENESS_FRACTION: float = 0.80

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build_calibration_reference")

# Calibration years are the historical years with EIA-930 hourly profiles.
# 2021-2024 each have their own EIA-860 fleet snapshot; 2025 reuses the
# latest available EIA-860 vintage (2024), which carries no 2025 builds, so
# its renewable capacity equals the 2024 year-end totals held flat. ERCOT was
# the first ISO calibrated; PJM the second; CAISO the third; NYISO and NEISO
# are the Stage-E additions. The per-ISO-year derivation is fully generic on
# the ISO's zone topology (zone_names) and balancing-authority code, so adding
# an ISO is a CALIBRATION_ISOS + BA-code-map change only.
CALIBRATION_YEARS: tuple[int, ...] = (2021, 2022, 2023, 2024, 2025)
CALIBRATION_ISOS: tuple[str, ...] = (
    "ERCOT",
    "PJM",
    "CAISO",
    "NYISO",
    "NEISO",
    "MISO",
    "SPP",
    # NWPP is the eighth registered region and the FIRST POOL one: seventeen
    # EIA-930 balancing authorities under one key, not a single BA (registered
    # 2026-09-14 by lane NWPP-20; owner ruling N1). Every ISO-keyed lookup in
    # this builder that used to resolve a SCALAR BA code now resolves
    # ``fleet.models.ba_codes(iso)`` -- a tuple -- and filters by membership,
    # which is byte-identical for the seven 1:1 regions and is the only
    # construction that can see a whole pool (NWPP-10 §3: a scalar inverse of
    # the many-to-one BA map silently returns 1/17 of the footprint).
    "NWPP",
    # SOCO is the NINTH registered region (2026-09-14, lane SOCO-20; this block
    # landed 2026-09-16 by lane SOCO-31) -- the Southern Company BALANCING
    # AUTHORITY, not an ISO and not a pool: one EIA-930 BA code, ``SOCO``, so
    # every lookup here resolves exactly as it did for the seven 1:1 regions
    # and ``_is_pool_region("SOCO")`` is False. What is unlike every prior
    # region is the PRICE side, and it is absent by RULING -- see
    # CALIBRATION_YEARS_BY_ISO["SOCO"] below.
    "SOCO",
)

# Per-ISO calibration-year overrides. CAISO's backcast targets 2023-2025
# (doc 06: 2023 = wet hydro + Diablo at full output; 2024/2025 = the
# big-battery era) — the years with CAMPD unit-level CA extracts and EIA-923
# by-fuel benchmarks. NYISO targets 2023 (cleanest year, full CEMS) and 2025;
# 2024 is added once the NY_2024 CEMS extract lands (doc 07 §2 U1) — the
# reference data for 2024 already exists, but the backcast year is gated on
# its unit-level outages. NEISO targets 2023-2025 (it has the most complete
# CEMS coverage of the new ISOs). ISOs not listed use the full
# CALIBRATION_YEARS span.
CALIBRATION_YEARS_BY_ISO: dict[str, tuple[int, ...]] = {
    # PJM gained 2019 on 2026-08-06 (session pjm-160), the first pre-2021 year
    # any ISO carries. What unblocked it is the F3 closure in
    # scripts/data/curate_demand_profile.py::curate_pre_window: the pre-2021
    # gap was never the hourly demand DRIVER (load_demand('PJM', 2019) has
    # worked since PJM gained its per-BA extract adapter — the extract covers
    # 2018-2026), only load_demand_meta, which fell through to the legacy
    # eia_demand_meta.parquet summary and raised. The curator now writes a
    # pre-window `demand-profile` clean partition from the SAME per-BA series
    # load_demand serves, so _demand_totals resolves for 2019.
    # This is DATA READINESS ONLY (rule 22): 2019 is LOCKED-TEST tier, PJM
    # holds no `final` marker, and the holdout spend freeze is ACTIVE — so no
    # 2019 solve, score or registration is authorized by this entry. Its whole
    # purpose is that when a `final` grant is eventually issued, the inputs are
    # already prepared and frozen, with nothing left to assemble mid-spend
    # (rule 22's "already configured precisely like the frontier keeper").
    # 2020 is deliberately NOT added: PJM's 2020 per-BA demand series carries
    # two residual metering-artifact hours (192,229 and 176,085 MW against a
    # 145 GW third-highest and an 85 GW median) that the loader's 2.5x-median
    # spike screen leaves in place, so its peak_mw would be wrong by ~47 GW.
    # That is a root-cause fix in eia930.demand._screen_demand_spikes, not
    # something to bury in a reference block (rule 14 [R-ACCURATE]); see
    # FINDING-pjm160-f3-demand-profile-closure-2026-08-06.md.
    "PJM": (2019, 2021, 2022, 2023, 2024, 2025),
    # CAISO gained 2021-2022 on 2026-07-31 under the owner-authorized rule-22
    # Option-2 DATA intake (calibration-complete.json intake_log; CAISO holds
    # NO marker, so no solve/score/registration of either year — reference and
    # bench readiness only, never calibration years). 2018-2020 are NOT added:
    # eia_demand_profiles.parquet has no CAISO rows before 2021, so
    # _demand_totals hard-fails — the same F3/F4-class cross-ISO blocker
    # already recorded for NEISO below
    # (docs/holdout-data-equivalency-register-2026-07.md sec. CAISO).
    "CAISO": (2021, 2022, 2023, 2024, 2025),
    # NYISO gained 2022 on 2026-07-12 under the owner-authorized rule-22 DATA
    # intake (calibration-complete.json intake_log; NO marker, NO solve — the
    # one-shot stays quarantined): 2022 is reference/bench data readiness
    # only, never a calibration year.
    # 2024 added 2026-07-31, closing the in-sample gap the register had carried
    # since 2026-07-12: the "gated on NY_2024 unit-level outages" rationale in
    # the comment above was stale on both counts — campd-unit-level/NY_2024
    # (and NJ_2024) are on disk, and the 2026-07-24 all-ISO re-derivation gives
    # campd-unit-outages-NYISO.csv uniform-detector windows for 2018-2026. 2024
    # is an ordinary IN-SAMPLE training year (rule 22 train tier), so this is a
    # parity repair, not a holdout action: NYISO was the only multi-year ISO
    # missing a reference block for a year it is actually calibrated on.
    # 2018-2021 remain absent — build_reference()._demand_totals hard-requires
    # eia_demand_profiles.parquet rows, and that artifact starts at 2021 for
    # every ISO (the cross-ISO F3 blocker); extending it is not a NYISO task.
    "NYISO": (2022, 2023, 2024, 2025),
    # NEISO gained 2022 on 2026-07-07: the calibration-complete marker
    # (frontend/data/backcast/calibration-complete.json) authorizes the ONE-SHOT
    # 2022 holdout validation (CLAUDE.md rule 22) — 2022 is a validation year
    # for the frozen keeper, never a calibration year. 2021 added 2026-07-13
    # under the same marker's rule-22 Option-2 DATA-INTAKE channel (owner
    # authorization, calibration-complete.json intake_log) — a pre-window
    # holdout year, never a calibration year either.
    # 2019 and 2020 added 2026-08-07 (session neiso-89), on the SAME F3 closure
    # that unblocked PJM 2019 above: the blocker was never the hourly demand
    # DRIVER (load_demand('NEISO', 2019) has resolved 8,760 h off the per-BA
    # `ISNE hourly` extract all along — neiso-88 §2.3 corrects neiso-87 §3.1 on
    # this) but load_demand_meta, which fell through to the legacy
    # eia_demand_meta.parquet summary and raised. curate_demand_profile's
    # pre-window partition closes it at the curation seam for all six ISOs.
    # Unlike PJM, NEISO's 2020 per-BA series is CLEAN — 0 hours flagged by the
    # physical-bounds screen, max/median 1.93 against the 5.0 ceiling and the
    # 2.1 empirical bound — so the metering-artifact exclusion that keeps PJM
    # 2020 out does not apply here (measured this session; PJM 2020 peaks at
    # 192,229 MW, NEISO 2020 at 24,697 MW against a 12,790 MW median).
    # This is DATA READINESS ONLY (rule 22 as rewritten 2026-08-06: "what is
    # held out is the SCORE, never the DATA"). 2019 is LOCKED-TEST tier and
    # NEISO holds no `final` marker; 2020 is validation tier and the holdout
    # spend freeze is ACTIVE — so this entry authorizes no solve, no scoring
    # and no registration of either year. Its whole purpose is rule 22's
    # "already configured precisely like the frontier keeper, with nothing left
    # to prepare": the inputs are applied consistently across ALL years now, so
    # that if a grant is ever issued nothing is assembled mid-spend.
    "NEISO": (2019, 2020, 2021, 2022, 2023, 2024, 2025),
    # MISO is the Stage-F addition: the EIA-923/930 by-fuel and demand
    # extracts all cover 2023-2025 (the 2025 EIA-923 release is the partial
    # monthly survey, handled by the incomplete-vintage guard). 2021-2022
    # added 2026-07-31 under the owner-authorized rule-22 Option-2 DATA-INTAKE
    # channel (calibration-complete.json intake_log; MISO holds NO marker, so
    # the solve/score/register quarantine stands) — holdout reference/bench
    # readiness only, never calibration years. 2018-2020 and 2026 are NOT
    # added: eia_demand_profiles.parquet carries MISO rows for 2021-2025 only,
    # so _demand_totals hard-fails ("No EIA-930 data for ISO 'MISO' in year
    # 2018") — the same F3-class cross-ISO blocker recorded for NEISO above,
    # fix = extend eia_demand_profiles{,_meta}.parquet first.
    # 2020 ADDED 2026-09-10 (session miso-251, owner instruction "ensure all
    # data needed is populated in the repo to run holdout years 2020-2022").
    # The F3 blocker this comment named above is CLOSED for MISO by the same
    # curate_demand_profile.py::curate_pre_window seam PJM 2019 used: MISO now
    # carries a `demand-profile` clean partition for 2020 built from the SAME
    # per-BA EIA-930 hourly extract load_demand serves (622.5 TWh, peak
    # 112,940 MW, 0 hours repaired — identical to the array the LP dispatches),
    # so _demand_totals('MISO', 2020) resolves and no longer reaches the legacy
    # eia_demand_profiles.parquet summary. DATA READINESS ONLY: 2020 still has
    # NO MISO hub-LMP bench (docs.misoenergy.org has aged 2018-2022 off; the
    # Data Exchange fallback needs MISO_PRICING_API_KEY, absent here — re-probed
    # 404 on 2026-09-10), so C3a/C3b/C3c are unscorable on it and no 2020 rung
    # can read CALIBRATED until that key lands. See
    # docs/PRECOMMIT-miso251-holdout-ladder-2026-09-10.md section 2.3.
    "MISO": (2020, 2021, 2022, 2023, 2024, 2025),
    # SPP is the Stage-G addition (registered 2026-09-06 by lane SPP-20; this
    # block landed 2026-09-07 by lane SPP-31). TRAINING TIER ONLY: 2023-2025,
    # the three years rule 22 [R-HOLDOUT] lets any ISO be built and scored on.
    # 2021-2022 are DELIBERATELY ABSENT even though every input for them now
    # resolves (eia_demand_profiles.parquet carries SPP 2021-2025 and the clean
    # demand-profile partitions cover 2019-2025): they are validation tier, SPP
    # holds NO marker in calibration-complete.json, and the ISOs that do carry
    # pre-2023 blocks got them through the owner-authorized rule-22 Option-2
    # DATA-INTAKE channel recorded in that file's intake_log. SPP has no such
    # authorization, so adding them here is not this lane's to do. Data
    # readiness is unaffected either way (rule 22, 2026-08-06: "what is held out
    # is the SCORE, never the DATA") — the inputs are prepared and consistent
    # across every year already, and only the reference block waits on a grant.
    "SPP": (2023, 2024, 2025),
    # NWPP (registered 2026-09-14 lane NWPP-20; this block landed 2026-09-14 by
    # lane NWPP-31). 2023-2025 is the whole span the DATA supports, not a tier
    # choice: the pool frame needs all seventeen members' ``<BA> hourly``
    # extracts and those were derived by NWPP-11 from the committed EIA-930
    # BALANCE archive for 2023-2025 only, so
    # ``_eia_hourly_frame_filled("NWPP", y)`` is None for 2021, 2022 and 2026
    # (measured this lane) and both ``_demand_totals`` and the EIA-930
    # comparator below would hard-fail. Extending the span is an NWPP-11-class
    # derive of more BALANCE years, not a reference-block edit.
    #
    # THE PRICE SIDE IS ABSENT BY RULING, NOT BY OVERSIGHT: card N2 chartered
    # NWPP-13 to build a WEIM-derived hourly price series behind a STOP gate
    # pre-registered before any value was read, and that gate READ NO (the WEIM
    # on-peak price sits 22.6 / 23.6 / 37.5 % below the independent Mid-C Peak
    # traded index against a ±10 % bar). So NWPP has NO ``actual_lmp.json``
    # block, no ``actual_lmp_hourly_NWPP.parquet``, no ``TAIL_THRESHOLD``
    # entry and no amplitude row (plan gate G6), and the scorer reads
    # PRICE-UNSCORED off exactly that absence (rubric v3.8, lane NWPP-22).
    # Substituting a neighbouring hub -- SP15, NP15 or Palo Verde, each one
    # column away in the same ICE workbook -- is the load proxy rule 13
    # ``[R-MEASURED]`` forbids and stays refused (plan gate G17).
    #
    # 2019, 2021, 2022 ADDED (lane R-NWPP, 2026-09-24): the seventeen member
    # extracts were re-derived from the committed BALANCE archive over
    # 2019-2025 (``build_nwpp_ba_hourly_from_balance.py --all-nwpp --year
    # 2019..2025``, zero reconciliation residual, 2023-2025 rows
    # byte-identical), which is exactly the NWPP-11-class derive named above.
    # 2020 is deliberately ABSENT: PSEI's ``Demand (Adjusted)`` is missing for
    # 8,659 of 8,784 hours of 2020 in EIA's own BALANCE files, and the pool
    # frame's member fill would interpolate 101 points into a fabricated
    # series (rule 13). It returns when a measured PSEI 2020 load lands.
    "NWPP": (2019, 2021, 2022, 2023, 2024, 2025),
    # SOCO (registered 2026-09-14 lane SOCO-20; this block landed 2026-09-16 by
    # lane SOCO-31 for 2023-2025, the span the EIA-930 extract then carried).
    # Widened to 2019-2025 by lane I-SOCO (2026-09-24, owner instruction: every
    # ISO's backcast covers 2019-2025): ``SOCO hourly.parquet`` now carries
    # 2019-2022 folded in from the committed BALANCE archive by
    # ``extend_eia930_hourly_from_balance.py`` (the legacy-era rows of which
    # reproduce the committed 2023-01..2024-06 rows exactly), and the committed
    # EIA-923 net-generation parquet already carried SOCO back to 2018. Every
    # 2023-2025 block and CSV regenerates byte-identically.
    #
    # THE PRICE SIDE IS ABSENT BY RULING, NOT BY OVERSIGHT, AND IT IS NOT A GAP
    # FOR A LATER LANE TO CLOSE WITH A SUBSTITUTE. Southern Company publishes
    # no LMP, no day-ahead clearing price and no hourly index, and SEEM -- the
    # Southeast Energy Exchange Market that covers this footprint -- publishes
    # matched VOLUMES and, deliberately, no price (plan §2.6). Card S2 chartered
    # SOCO-13 to build a footprint-hourly volume-weighted index from FERC EQR
    # transaction data behind a STOP gate pre-registered before any datum was
    # read, and that gate READ NO: three of its five criteria failed -- hourly
    # coverage 3.66 / 2.69 / 2.64 % against a >= 5 % bar in every year, the
    # index +54.2 / +72.1 % above its independent public anchor in 2024/2025
    # against a +/-15 % bar, and the 2025 shape test -- and NO BAR WAS MOVED
    # AFTER THE SERIES WAS SEEN (FINDING-soco-13-2026-09-13.md). So SOCO has NO
    # ``actual_lmp.json`` block, no ``actual_lmp_hourly_SOCO.parquet``, no
    # ``TAIL_THRESHOLD`` entry and no amplitude row (plan gate G6), and the
    # scorer reads PRICE-UNSCORED off exactly that ABSENCE, which is therefore
    # load-bearing (rubric v3.8, lane SOCO-22). Substituting a neighbouring
    # market's hub -- MISO-South, a PJM or TVA proxy, an EIA state average
    # dressed as a price -- is the load proxy rule 13 ``[R-MEASURED]`` forbids
    # and stays refused (plan gate G17; the desk has refused it twice).
    "SOCO": (2019, 2020, 2021, 2022, 2023, 2024, 2025),
}

# Measured Henry Hub natural-gas spot price, annual average ($/MMBtu).
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
# URL: https://www.eia.gov/dnav/ng/hist/rngwhhdA.htm
HENRY_HUB_ACTUAL: dict[int, float] = {
    2018: 3.15,
    2019: 2.57,
    2020: 2.03,
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}

# eGRID benchmark workbook (EPA Emissions & Generation Resource Integrated
# Database, 2023 data release). The plant-level sheet PLNT23 carries a
# one-row banner above the header, hence skiprows=1.
EGRID_PATH: Path = FLEET_DIR / "egrid2023_data_rev2.xlsx"
EGRID_SHEET: str = "PLNT23"
EGRID_SKIPROWS: int = 1
EGRID_YEAR: int = 2023

# Heat-rate threshold (Btu/kWh) splitting eGRID gas plants into combined
# cycle (efficient, below the cut) and combustion turbine (above, or with
# no reported heat rate). 8500 sits between modern CC (~6500-7500) and
# frame CT (~10000+) heat rates.
GAS_CC_HEAT_RATE_CUTOFF: float = 8500.0

# eGRID PLFUELCT plant fuel category -> model fuel label. GAS is resolved
# separately into gas_cc / gas_ct by plant heat rate.
EGRID_FUEL_MAP: dict[str, str] = {
    "COAL": "coal",
    "NUCLEAR": "nuclear",
    "WIND": "wind",
    "SOLAR": "solar",
    "HYDRO": "hydro",
    "BIOMASS": "biomass",
    "OIL": "oil",
    "OTHF": "other",
    "OFSL": "other",
}

# eGRID reports annual CO2 mass in US short tons; the dispatch model and its
# CO2_RATES are in metric tonnes. 1 short ton = 0.90718474 metric tonnes.
SHORT_TON_TO_METRIC_TONNE: float = 0.90718474

_MWH_PER_TWH: float = 1.0e6
_MONTHS: tuple[int, ...] = tuple(range(1, 13))

# Output goes to the single validation-source root the loaders read from
# (data/raw/_validation-source). The pre-W1 ``inputs/calibration`` path was
# collapsed into data/raw/ — see config/paths.py CALIBRATION_DIR.
OUTPUT_DIR: Path = CALIBRATION_DIR


def _eia860_renewables(iso: str, year: int) -> dict:
    """Return the EIA-860 renewable-capacity reference for one ISO-year.

    For each renewable fuel the EIA-860 operable plants are placed in model
    zones and accumulated month by month from their commercial-operation
    dates (see :func:`_eia860_monthly_capacity`). The result captures the
    December year-end total, the year-end zone shares, the ISO-wide monthly
    ramp factors, and the full per-zone monthly capacity grid.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calibration year.

    Returns:
        ``{fuel: {december_total_mw, zone_shares, monthly_ramp,
        monthly_capacity_mw}}`` for each renewable fuel with EIA-860 data.
    """
    zone_names = get_iso_config(iso).zone_names
    out: dict[str, dict] = {}
    for fuel in _RENEWABLE_FUELS:
        monthly = _eia860_monthly_capacity(iso, fuel, zone_names, year)
        if monthly is None:
            logger.warning("no EIA-860 %s data for %s %d", fuel, iso, year)
            continue
        december = monthly[:, -1]
        december_total = float(december.sum())
        iso_monthly = monthly.sum(axis=0)
        out[fuel] = {
            "december_total_mw": round(december_total, 2),
            "zone_shares": {
                zone_names[z]: round(float(december[z] / december_total), 6)
                for z in range(len(zone_names))
            },
            "monthly_ramp": [
                round(float(iso_monthly[m] / iso_monthly[-1]), 6) for m in range(12)
            ],
            "monthly_capacity_mw": {
                zone_names[z]: [round(float(monthly[z, m]), 2) for m in range(12)]
                for z in range(len(zone_names))
            },
        }
    return out


def _is_pool_region(iso: str) -> bool:
    """True when ``iso`` is a POOL of several EIA-930 balancing authorities.

    Data-driven on :data:`~market_sim.data.fleet.models.ISO_TO_BA_CODES` --
    never an ``iso == "NWPP"`` ladder -- so a second pool region registers here
    with no edit. The seven 1:1 regions and SOCO return ``False``, which is why
    every branch this predicate guards is unreachable for them (rule 25
    ``[R-ISO-SCOPE]``) and their committed rows cannot move.
    """
    return len(ba_codes(iso)) > 1


def _pool_demand_meta(iso: str, year: int) -> dict:
    """Return ``load_demand_meta``-shaped totals for a POOL region's footprint.

    A pool has no row in the legacy per-ISO ``eia_demand_profiles``/
    ``eia_demand_meta`` summary and no ``demand-profile`` clean partition (both
    are keyed on the seven 1:1 ISOs the legacy extract carries), so
    :func:`load_demand_meta` raises for it. The footprint series it would have
    summarised is the POOL FRAME's ``Demand`` column -- **the identical array
    the LP dispatches**, since ``eia930.demand._load_nwpp_hourly_demand`` reads
    that same column off that same frame -- so this reads it directly rather
    than reconstructing a second one (rule 19 ``[R-ONE-MECH]``; rule 14
    ``[R-ACCURATE]``: the measured array beats any summary of it).

    The demand CONVENTION is fixed on the pool frame itself and is not
    re-decided here (NWPP-10 §1.3, ``frames._pool_hourly_frame``): members'
    **``Demand (MW) (Adjusted)``** series, each through the exact-zero DROPOUT
    screen before the sum (17 literal-0.0 NEVP hours of 2025), with the SPIKE
    screen deliberately NOT applied because its 2.5x-median bar flags 54 REAL
    CHPD hours of 12-16 January 2024 that hold a zone's annual peak. Nothing is
    padded, interpolated or rescaled beyond those repairs (rule 13
    ``[R-MEASURED]``). Reproduces the coincident peaks 49,290 / 52,564 /
    50,953 MW for 2023 / 2024 / 2025.

    Raises:
        ValueError: when the pool frame cannot be assembled for the year (a
            missing member extract), so a partial pool is never summarised.
    """
    frame = _eia_hourly_frame_filled(_ISO_TO_HOURLY_BA[iso], year)
    if frame is None:
        raise ValueError(f"No EIA-930 pool frame for region {iso!r} in year {year}")
    mw = frame["Demand"].to_numpy(dtype=float)
    if np.isnan(mw).any():
        raise ValueError(f"{iso} {year}: pool demand carries NaN hours")
    return {
        "total_annual_mwh": float(mw.sum()),
        "peak_mw": float(mw.max()),
        "min_mw": float(mw.min()),
        "avg_mw": float(mw.mean()),
    }


def _demand_totals(iso: str, year: int) -> dict:
    """Return the EIA-930 annual demand totals for one ISO-year."""
    meta = (
        _pool_demand_meta(iso, year)
        if _is_pool_region(iso)
        else load_demand_meta(iso, year)
    )
    return {
        "total_twh": round(float(meta["total_annual_mwh"]) / _MWH_PER_TWH, 4),
        "total_mwh": float(meta["total_annual_mwh"]),
        "peak_mw": float(meta["peak_mw"]),
        "min_mw": float(meta["min_mw"]),
        "avg_mw": round(float(meta["avg_mw"]), 2),
    }


def _classify_gas(heat_rate: float) -> str:
    """Return ``gas_cc`` or ``gas_ct`` for an eGRID gas plant by heat rate.

    A plant with no reported heat rate cannot be confirmed as an efficient
    combined-cycle unit, so it is conservatively counted as a combustion
    turbine.
    """
    if heat_rate != heat_rate:  # NaN — no reported heat rate
        return "gas_ct"
    return "gas_cc" if heat_rate < GAS_CC_HEAT_RATE_CUTOFF else "gas_ct"


def _egrid_benchmark(iso: str) -> dict:
    """Return the eGRID 2023 generation/emissions benchmark for one ISO.

    Reads the plant-level PLNT23 sheet, filters to the ISO's balancing
    authority, and aggregates annual net generation (TWh) and CO2 emissions
    (metric Mt) by model fuel. Gas plants are split into combined cycle and
    combustion turbine by plant heat rate (:data:`GAS_CC_HEAT_RATE_CUTOFF`).

    Args:
        iso: ISO identifier; mapped to its eGRID balancing-authority code.

    Returns:
        A benchmark dict with ``generation_twh`` and ``co2_mt`` mappings.
    """
    # eGRID's BACODE uses the same EIA-930 codes the fleet registry does
    # (ERCO, PJM, ..., SWPP for SPP, the bare "MISO" for MISO -- all verified
    # against the workbook), so the footprint is
    # :func:`~market_sim.data.fleet.models.footprint_plant_mask`: membership in
    # ``ba_codes(iso)`` AND, where the region declares one, the NERC-region
    # admission key. For the seven 1:1 regions that is exactly the former
    # ``BACODE == code`` selection -- one code, no NERC entry -- so their rows
    # are byte-identical (verified: plan gate G9). For the NWPP POOL it is the
    # only correct selection: seventeen codes, and the NERC key excludes the
    # one PLNT23 row that files under an NWPP BA from the EASTERN
    # interconnection (57914 Sidney MT Plant, NERC MRO, 135 MWh / 60.954 short
    # tons -- 880 of 881 rows admitted). The predicate is the REGISTRY one
    # (rule 24 ``[R-REGISTRY]``), never a per-plant exclusion list.
    df = pd.read_excel(EGRID_PATH, sheet_name=EGRID_SHEET, skiprows=EGRID_SKIPROWS)
    codes = ba_codes(iso)
    plants = df[footprint_plant_mask(iso, df["BACODE"], df.get("NERC"))].copy()

    fuel_cat = plants["PLFUELCT"].astype(str).str.strip().str.upper()
    gen_mwh = pd.to_numeric(plants["PLNGENAN"], errors="coerce").fillna(0.0)
    co2_ton = pd.to_numeric(plants["PLCO2AN"], errors="coerce").fillna(0.0)
    heat_rate = pd.to_numeric(plants["PLHTRT"], errors="coerce")

    generation_twh: dict[str, float] = {}
    co2_mt: dict[str, float] = {}
    for cat, gen, co2, hr in zip(fuel_cat, gen_mwh, co2_ton, heat_rate):
        if cat == "GAS":
            fuel = _classify_gas(hr)
        else:
            fuel = EGRID_FUEL_MAP.get(cat, "other")
        generation_twh[fuel] = generation_twh.get(fuel, 0.0) + float(gen) / _MWH_PER_TWH
        co2_mt[fuel] = (
            co2_mt.get(fuel, 0.0)
            + float(co2) * SHORT_TON_TO_METRIC_TONNE / _MWH_PER_TWH
        )

    return {
        "iso": iso,
        "benchmark_year": EGRID_YEAR,
        # Byte-identical to the former "filtered BACODE=%s" % ba_code for every
        # 1:1 region (one code joins to itself, and none declares a NERC key).
        "source": "EPA eGRID 2023 (PLNT23), filtered BACODE=%s%s"
        % (
            ",".join(codes),
            (
                " & NERC=%s" % ISO_NERC_REGION_ADMISSION[iso]
                if iso in ISO_NERC_REGION_ADMISSION
                else ""
            ),
        ),
        "co2_unit": "metric Mt (eGRID short tons converted)",
        "generation_twh": {k: round(v, 4) for k, v in sorted(generation_twh.items())},
        "co2_mt": {k: round(v, 4) for k, v in sorted(co2_mt.items())},
    }


def _write_year_csv(iso: str, year: int, renewables: dict) -> Path:
    """Write the per-zone, per-month renewable capacity CSV for one ISO-year.

    Args:
        iso: ISO identifier.
        year: Calibration year.
        renewables: The ISO-year renewable block from :func:`_eia860_renewables`.

    Returns:
        The path of the written CSV.
    """
    rows: list[dict] = []
    for fuel, block in renewables.items():
        for zone, monthly in block["monthly_capacity_mw"].items():
            for month, capacity in zip(_MONTHS, monthly):
                rows.append(
                    {
                        "iso": iso,
                        "year": year,
                        "fuel": fuel,
                        "zone": zone,
                        "month": month,
                        "capacity_mw": capacity,
                    }
                )
    path = OUTPUT_DIR / f"{iso}_{year}_renewable_capacity.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


# A whole EIA-923 vintage is treated as a partial release (every fuel, incl.
# the gas split, under-counted) when the balancing authority's total EIA-923
# net generation falls below this fraction of the EIA-930 grid net generation
# for the year. The 2025 early monthly survey runs ~74%; complete years ~100%.
_EIA923_VINTAGE_COMPLETENESS_FRACTION: float = 0.90

# EIA-923 reported fuel-type codes that count as coal.
_EIA923_COAL_FUELS: frozenset[str] = frozenset({"BIT", "SUB", "LIG", "WC", "RC"})
# EIA-923 reported fuel-type codes that count as oil (distillate, residual,
# kerosene, jet, waste oil, petroleum coke) — the dual-fuel winter switch fuel
# in NYISO/NEISO. Any prime mover counts; the fuel code alone classifies oil.
_EIA923_OIL_FUELS: frozenset[str] = frozenset({"DFO", "RFO", "JF", "KER", "WO", "PC"})
# The ISO -> EIA balancing-authority mapping is the fleet registry's
# :func:`~market_sim.data.fleet.models.ba_codes`, not a local scalar dict. The
# local ``_ISO_BA_CODE`` table this replaced carried exactly the seven pairs
# ``ba_codes`` returns for those regions (ERCO / CISO / PJM / NYIS / ISNE /
# MISO / SWPP), so every committed block is byte-identical; what it could not
# express is a POOL region, whose EIA-923 rows are spread over seventeen codes
# (NWPP-10 §3 -- a scalar inverse of the many-to-one map keeps whichever code
# was inserted last and silently reads 1/17 of the footprint).

# Extra EIA-923 by-fuel benchmarks emitted only for the ISOs where they are
# first-order. NYISO and NEISO additionally benchmark conventional hydro
# (NYISO's Niagara/St-Lawrence carry ~25-30 TWh/yr) and the winter dual-fuel
# oil burn. The already-calibrated ERCOT/PJM/CAISO blocks are not listed, so
# their generation_twh stays byte-identical (hydro/oil are negligible or not
# benchmarked there). Pumped storage (WAT/PS) is storage, not energy, and is
# excluded from the hydro total.
# MISO carries material upper-Midwest conventional hydro (~9 TWh/yr, on par
# with NEISO's benchmarked hydro) and a non-trivial dual-fuel oil burn
# (~2-3 TWh/yr, larger than the NYISO/NEISO oil totals already benchmarked),
# so both are first-order energy classes for its by-fuel benchmark.
# SPP carries material conventional hydro on the Missouri/Arkansas river
# projects (EIA-923 WAT/HY: 8.4002 TWh in 2023, 8.7018 in 2024 — on par with
# MISO's benchmarked ~9 TWh and above NEISO's), so hydro is first-order for its
# by-fuel benchmark. OIL IS DELIBERATELY OMITTED: SPP's EIA-923 oil burn is
# 0.2590 / 0.3237 / 0.2230 TWh over 2023-2025 (~0.09 % of a ~280 TWh system) —
# an order of magnitude below the smallest oil total already benchmarked, and
# EIA-930 agrees (0.2159 / 0.1007 / 0.0219 TWh). It is a fleet of 2.4 GW of
# petroleum-liquids nameplate that essentially never runs, not a winter
# dual-fuel switch, so it is not a first-order energy class here.
# NWPP's conventional hydro is the LARGEST benchmarked hydro in the repo and
# the single biggest energy class in its own footprint: EIA-923 WAT/HY reads
# 106.9281 / 107.9002 TWh for 2023 / 2024 (EIA-930 ``NG: WAT``: 104.233 /
# 105.040 / 110.272), i.e. ~36 % of a ~298 TWh system, an order of magnitude
# above the MISO/SPP/NEISO hydro already benchmarked. OIL IS DELIBERATELY
# OMITTED, on the SPP precedent and its own measurement: EIA-923 oil is
# 0.5579 / 0.4846 / 0.5248 TWh over 2023-2025 and EIA-930 agrees (0.4907 /
# 0.3808 / 0.4588) -- 0.16-0.19 % of footprint energy, below the 2 %
# materiality floor this repo gates classes on, and a fleet of remote diesel
# peakers rather than the winter dual-fuel switch that makes oil first-order
# in NYISO/NEISO. Reported here so the omission is a measured decision.
# GEOTHERMAL (4.4919 TWh eGRID 2023, 1.5 % of energy) likewise stays inside
# the "other" aggregate both eGRID (PLFUELCT GEOTHERMAL -> the map's default)
# and EIA-930 (``NG: OTH``) already put it in; breaking it out would need a new
# mask class in :func:`_eia923_generation_raw` and is not this lane's to add.
# SOCO's conventional hydro clears the 2 % materiality floor in every year of
# its span and is therefore first-order here too: EIA-930 ``NG: WAT`` reads
# 8.4465 / 7.0798 / 6.0123 TWh against a 239.6251 / 249.5057 / 251.8847 TWh
# footprint -- 3.52 / 2.84 / 2.39 %. Declaring it also puts it in the per-fuel
# incompleteness candidate set, which is what the 2025 vintage needs: EIA-923
# reports 0.3275 TWh of SOCO hydro that year (ratio 0.054) against a 6.6852 and
# 6.3014 TWh in the two complete years, by far the worst-reported of SOCO's
# benchmarked classes, and the guard swaps it to EIA-930 rather than scoring a
# model class against a 95 %-missing actual. OIL IS DELIBERATELY OMITTED, on the
# SPP/NWPP precedent and on its own measurement: EIA-923 oil is 0.2666 / 0.2573 /
# 0.1042 TWh and EIA-930 agrees it is smaller still (0.0009 / 0.0017 / 0.0250),
# i.e. 0.11 / 0.10 / 0.04 % of footprint energy -- an order of magnitude below
# the materiality floor, and a starting/backup fleet rather than the winter
# dual-fuel switch that makes oil first-order in NYISO/NEISO. PUMPED STORAGE is
# not a candidate and cannot become one here: ``WAT``/``PS`` is storage, the
# hydro mask below excludes it by prime mover, and SOCO's 1,306.6 MW of it is
# UNOBSERVABLE in EIA-930 for 2023 and most of 2024 (lane SOCO-31 R-i -- the
# ``NG: PS``/``BAT`` taxonomy cut-over of 2024-07-15; stated on the first
# keeper's determination basis, never filled in).
_EIA923_EXTRA_FUELS_BY_ISO: dict[str, tuple[str, ...]] = {
    "NYISO": ("hydro", "oil"),
    "NEISO": ("hydro", "oil"),
    "MISO": ("hydro", "oil"),
    "SPP": ("hydro",),
    "NWPP": ("hydro",),
    "SOCO": ("hydro",),
}


def _eia923_generation(iso: str, year: int) -> dict[str, float]:
    """EIA-923 net generation by model fuel (TWh), with the incomplete-vintage
    guard applied (an under-counted benchmarked fuel deferred to EIA-930 when
    the 923 release is a partial current-year survey). See
    :func:`_eia923_generation_raw` for the raw extraction and
    :func:`_guard_incomplete_eia923` for the guard.
    """
    return _guard_incomplete_eia923(iso, year, _eia923_generation_raw(iso, year))


@lru_cache(maxsize=1)
def _eia923_generation_table() -> pd.DataFrame:
    """Return the committed EIA-923 Page-1 net-generation table.

    The raw ``f923_{year}*.zip`` releases are large source downloads that are
    not carried in a fresh checkout. :mod:`scripts.data.process_f923_fuel_costs`
    distils them once into ``eia923_monthly_generation.parquet`` under
    ``data/raw/_processed-legacy`` — keeping the original Page-1 row grain (one
    row per plant / prime mover / fuel code), the EIA-930 ``ba_code`` and the
    annual net generation — so a balancing-authority by-fuel total summed from
    this parquet is byte-identical to the same total summed from the raw zip.
    That parquet is the resolved source here.
    """
    return pd.read_parquet(EIA923_MONTHLY_GENERATION_PATH)


@lru_cache(maxsize=None)
def _eia923_ba_frame(iso: str, year: int) -> pd.DataFrame | None:
    """Return the EIA-923 Page-1 rows for an ISO's balancing authority.

    Filters the committed EIA-923 net-generation parquet
    (:func:`_eia923_generation_table`) to the ISO's balancing authority and
    year, returning a frame with ``net_gen`` (MWh), ``pm`` (prime mover) and
    ``fc`` (fuel code). ``None`` when the parquet has no rows for the year
    (2021/2022, which predate the committed vintage) or the ISO has no
    balancing-authority mapping. Cached so the by-fuel split and the
    completeness check share a single read.
    """
    codes = ba_codes(iso)
    if not codes:
        return None
    table = _eia923_generation_table()
    # Membership, not equality: identical to ``== ba`` for a one-code region
    # and the only form that sees a whole pool. EIA-923 carries no NERC column,
    # so the eGRID admission key above has no analogue here; the residual
    # contamination is MEASURED rather than filtered -- plant 68906 (Pine
    # Forest Solar I, Hopkins County TX, NERC TRE) files under DOPD and
    # contributes 0.0295 TWh of solar to NWPP 2025 -- 0.150 % of that year's
    # solar class and 0.013 % of its footprint EIA-923 energy. It DOES reach
    # the committed 2025 block: the per-fuel incompleteness guard swaps wind
    # (923/930 = 0.5746) and hydro (0.6796) out to EIA-930 that year but not
    # solar (0.9796, above the 0.80 bar), so the number is stated here rather
    # than assumed away. Measured 2023/2024 contamination: zero (68906 files
    # no EIA-923 row before 2025). The
    # alternative -- intersecting with the curated EIA-860 operable-generator
    # plant set -- was measured and REJECTED: it would drop 0.927 TWh of real
    # 2023 generation from plants that have since retired off the snapshot to
    # remove 0.0295 TWh of misfiled solar, i.e. a worse benchmark (rule 14
    # ``[R-ACCURATE]``), and a per-plant exclusion is forbidden outright
    # (rule 24 ``[R-REGISTRY]``).
    df = table[
        (table["year"] == year) & (table["ba_code"].astype(str).str.strip().isin(codes))
    ]
    if df.empty:
        return None
    return pd.DataFrame(
        {
            "net_gen": pd.to_numeric(df["netgen_annual_mwh"], errors="coerce")
            .fillna(0.0)
            .to_numpy(),
            "pm": df["prime_mover"].astype(str).str.strip().to_numpy(),
            "fc": df["fuel_type"].astype(str).str.strip().to_numpy(),
        }
    )


def _eia923_generation_raw(iso: str, year: int) -> dict[str, float]:
    """Return EIA-923 net generation by model fuel (TWh) for an ISO-year.

    Classifies each balancing-authority row (:func:`_eia923_ba_frame`) by
    reported fuel code and prime mover. Gas is split into combined cycle (prime
    movers CA/CT/CC/CS), combustion turbine (GT) and gas steam (ST). For ISOs in
    :data:`_EIA923_EXTRA_FUELS_BY_ISO` (NYISO/NEISO/MISO/SPP) conventional hydro
    (WAT/HY) and oil (:data:`_EIA923_OIL_FUELS`) are emitted too. Unlike the
    eGRID plant snapshot, these totals sum to the balancing authority's actual
    net generation, so they are a self-consistent calibration benchmark.

    Returns an empty dict when no EIA-923 zip exists for the year (2021 and
    2022 have none) or the ISO has no balancing-authority mapping.
    """
    df = _eia923_ba_frame(iso, year)
    if df is None:
        return {}
    net_gen, pm, fc = df["net_gen"], df["pm"], df["fc"]
    is_gas = fc == "NG"
    masks = {
        "coal": fc.isin(_EIA923_COAL_FUELS),
        "gas_cc": is_gas & pm.isin(["CA", "CT", "CC", "CS"]),
        "gas_ct": is_gas & pm.isin(["GT"]),
        "gas_st": is_gas & pm.isin(["ST"]),
        "nuclear": fc == "NUC",
        "wind": fc == "WND",
        "solar": fc == "SUN",
    }
    for fuel in _EIA923_EXTRA_FUELS_BY_ISO.get(iso, ()):
        if fuel == "hydro":
            # Conventional hydro only; pumped storage (WAT/PS) is storage.
            masks["hydro"] = (fc == "WAT") & (pm == "HY")
        elif fuel == "oil":
            masks["oil"] = fc.isin(_EIA923_OIL_FUELS)
    return {
        fuel: round(float(net_gen[mask].sum()) / _MWH_PER_TWH, 4)
        for fuel, mask in masks.items()
    }


def _pool_hourly_benchmark(iso: str, year: int) -> dict[str, np.ndarray]:
    """Return a POOL region's EIA-930 hourly benchmark series, by fuel.

    :func:`load_eia_hourly_benchmark` resolves its frame through
    ``actuals._eia_hourly_path(ba_code)`` -- a single ``<BA> hourly.parquet``
    -- so it returns ``None`` for a pool code that names no file. This assembles
    the same dict for a pool WITHOUT re-deciding anything: the per-fuel series
    are the loader's OWN per-BA construction (spike screen -> zero-coded-gap
    mask -> interpolate/bfill/ffill -> pad, with the storage-coverage drop)
    applied to each of the seventeen members and then summed, and ``net_gen`` /
    ``interchange`` are read off the registered pool frame.

    **Why the fuels are summed per member rather than read off the pool frame's
    own ``NG:`` columns, measured rather than asserted.** ``frames.
    _pool_hourly_frame`` sums the members' ``NG:`` columns unscreened, and this
    footprint's members carry real EIA-930 unit slips in them: AVA 2025
    ``NG: WAT`` posts 810,113 MW in one hour against a 138 MW-class p99.9,
    NWMT 2025 ``NG: WAT`` 99,225 MW in four, NEVP 2025 ``NG: NG`` 66,310 MW in
    five, NWMT 2025 ``NG: COL`` 28,111 MW in one (twelve flagged member-hours
    across 2023-2025 in all). Read off the pool frame, 2025 hydro comes back
    111.4407 TWh; screened per member as every 1:1 region already is, it is
    110.2719 -- a 1.17 TWh artifact. The screen is defined on ONE BA's series
    (two order statistics of its own 8,760 hours), so applying it per member is
    the loader's own mechanism at the level it is defined, not a new screen
    (rules 19 ``[R-ONE-MECH]`` / 23 ``[R-FROZEN-DERIVE]``).

    **This function no longer applies the screen itself** (lane NWPP-37,
    2026-09-16): ``_eia_hourly_frame`` now screens at the frame-construction
    seam, so the member frames arrive repaired with the SAME per-member
    statistics this function's own call used, and the totals here are
    byte-identical to what they were. The explicit second application was
    removed because it is not idempotent -- re-running the screen on an
    already-screened series recomputes the p99.9 anchor with the flagged hours
    gone, which LOWERS it and can flag more; measured, a second pass takes
    three further hours (PGE 2023 ``NG: OTH`` 81 MW, NEVP 2025 ``NG: NG``
    20,354 MW, SOCO 2024 ``NG: OIL`` 155 MW). One application, at the
    constructor, is the rule-19 form.

    The seam note this docstring used to route to the desk -- that a pool's
    delivered wind/solar bound would read the UNSCREENED pool columns through
    ``renewables._eia_hourly_cf_profile`` -- is CLOSED by that lane: the pool
    frame is screened on its way out of ``_eia_hourly_frame`` too. What that
    pooled screen cannot see is a member slip the footprint sum dilutes below
    its bar, which is why this function still sums per member rather than
    reading the pool's own ``NG:`` columns; on 2025 hydro the pooled screen
    recovers 110.3171 TWh of the per-member 110.2719, so 96 % of the artifact.

    ``net_gen`` and ``interchange`` come from the pool frame's own columns
    because those two quantities are DEFINED at the pool, not summed from
    members: NWPP-20 fixed ``Net generation`` as the sum of the members'
    **Adjusted** series and ``Total interchange`` as ``NG_adj - D_adj`` (the
    footprint's external position by energy balance), precisely because BPAT's
    own ``Total interchange`` carried a ~4,000 MW over-report on internal legs
    until 2025-06 and Sigma-TI reads +32.7 TWh where the balance position is
    -3.1 TWh. Re-summing them here would reintroduce the defect the pool frame
    exists to avoid.

    Returns ``{}`` when the pool frame cannot be assembled for the year.
    """
    pool = _eia_hourly_frame(_ISO_TO_HOURLY_BA[iso], year)
    if pool is None:
        return {}
    totals: dict[str, np.ndarray] = {}
    for member in ba_codes(iso):
        frame = _eia_hourly_frame(member, year)
        if frame is None:
            logger.warning("%s %d: pool member %s has no frame", iso, year, member)
            return {}
        for name, column in _EIA930_BENCHMARK_COLUMNS:
            if column not in frame.columns:
                continue
            raw = frame[column]
            if name in _STORAGE_BENCHMARK_SERIES:
                if 1.0 - float(raw.isna().mean()) < _STORAGE_MIN_COVERAGE_FRAC:
                    continue
            if column in _ZERO_CODED_GAP_SERIES.get(member, frozenset()):
                raw = raw.mask(raw == 0.0)
            series = raw.interpolate().bfill().ffill()
            if series.isna().any():
                continue
            arr = series.to_numpy(dtype=float)
            totals[name] = totals.get(name, 0.0) + arr
    for name, column in (
        ("net_gen", "Net generation"),
        ("interchange", "Total interchange"),
    ):
        if column not in pool.columns:
            continue
        series = pool[column].interpolate().bfill().ffill()
        if series.isna().any():
            continue
        totals[name] = series.to_numpy(dtype=float)
    return totals


def _eia930_annual_by_fuel(iso: str, year: int) -> dict[str, float]:
    """Return EIA-930 grid-side net generation by fuel (TWh) for an ISO-year.

    Reads the per-BA hourly extract through the calibration bench loader and
    sums each series. The ``NG:`` fuel series arrive with EIA-930 unit-slip
    hours already repaired at the loader seam
    (``eia930.actuals._screen_fuel_spike_columns``, SPP-41) — this function
    applies no screen of its own, so the loader is the ONLY place the repair
    happens (rule 19 ``[R-ONE-MECH]``). Empty when the ISO has no EIA-930
    extract for the year. Grid-side telemetry, so the variable-renewable totals
    are not subject to the EIA-923 survey's under-count / BA mis-assignment.
    """
    bench = (
        _pool_hourly_benchmark(iso, year)
        if _is_pool_region(iso)
        else load_eia_hourly_benchmark(iso, year)
    )
    if not bench:
        return {}
    return {
        fuel: round(float(np.nansum(np.asarray(arr, dtype=float))) / _MWH_PER_TWH, 4)
        for fuel, arr in bench.items()
    }


def _incomplete_renewable_fuels(
    iso: str, year: int, raw: dict[str, float]
) -> list[str]:
    """Return the benchmarked fuels EIA-923 under-counts for an ISO-year.

    A fuel is under-counted when its raw EIA-923 BA total is below
    :data:`_EIA923_RENEWABLE_COMPLETENESS_FRACTION` of the EIA-930 grid-side
    telemetry for that fuel. Evaluated PER FUEL (not on the combined renewable
    total) so a partial wind release is caught even when solar reports fully.
    Empty for complete vintages (the two sources then agree to within a few
    percent), so the guard is a no-op there. Also empty when there is no EIA-923
    vintage at all (``raw`` empty, e.g. 2021/2022): a missing benchmark is left
    missing, not fabricated from EIA-930.

    The candidate set is wind and solar PLUS the ISO's own
    :data:`_EIA923_EXTRA_FUELS_BY_ISO` entries (lane SPP-47, owner ruling P16
    2026-09-07, on FINDING-spp-43 §6 / FINDING-spp-57 R-15). Those extras are
    exactly the fuels this builder already declares first-order and benchmarked
    for that ISO, so a fuel the same file's own logic would reject for wind is
    no longer scored on a preliminary EIA-923 vintage: SPP 2025 hydro read
    0.0233 TWh against EIA-930's 8.8299 (ratio 0.0026), by far the worst of its
    three benchmarked classes, and was the only one left unswapped. This is a
    CONSTRUCTION REPAIR of the loop's candidate set, not a re-derivation against
    a residual (rule 23 ``[R-FROZEN-DERIVE]``): the 0.80 threshold, the EIA-930
    authority, and the per-fuel evaluation are all unchanged, and it introduces
    no new parameter (rules 5 ``[R-NO-MAGIC]`` / 21 ``[R-DOF]``). The ``ref <=
    0.0`` guard below restricts it to fuels EIA-930 actually reports, which is
    why MISO oil — carried in the extras but absent from EIA-930's MISO series —
    is never swapped. An ISO with no extras evaluates exactly the former pair,
    so ERCOT/PJM/CAISO are unreachable by construction (rule 25
    ``[R-ISO-SCOPE]``).
    """
    if not raw:
        return []
    e930 = _eia930_annual_by_fuel(iso, year)
    out: list[str] = []
    for fuel in ("wind", "solar") + _EIA923_EXTRA_FUELS_BY_ISO.get(iso, ()):
        ref = e930.get(fuel, 0.0)
        if ref <= 0.0:
            continue
        if raw.get(fuel, 0.0) < _EIA923_RENEWABLE_COMPLETENESS_FRACTION * ref:
            out.append(fuel)
    return out


def _guard_incomplete_eia923(
    iso: str, year: int, gen: dict[str, float]
) -> dict[str, float]:
    """Source a benchmarked fuel from EIA-930 when EIA-923 under-counts it.

    The incomplete current-year EIA-923 release under-counts the classes with no
    CEMS backfill — the variable renewables, and the ISO's own extra benchmarked
    fuels. Any candidate fuel below the completeness fraction
    (:func:`_incomplete_renewable_fuels`, whose docstring carries the candidate
    set and the SPP-47 repair) is replaced with the EIA-930 grid total —
    byte-identical for complete vintages, where the two agree. Other classes are
    left on EIA-923 (thermal is backfilled from CAMPD downstream); callers flag
    the year via :func:`_eia923_is_incomplete`.
    """
    e930 = _eia930_annual_by_fuel(iso, year)
    patched = dict(gen)
    for fuel in _incomplete_renewable_fuels(iso, year, gen):
        logger.info(
            "%s %s: EIA-923 %s %.2f TWh is incomplete; using EIA-930 %.2f TWh",
            iso,
            year,
            fuel,
            patched.get(fuel, 0.0),
            e930[fuel],
        )
        patched[fuel] = e930[fuel]
    return patched


def _eia923_is_incomplete(iso: str, year: int) -> bool:
    """True when the WHOLE ISO-year EIA-923 vintage is a partial release.

    Distinct from the per-fuel renewable guard (which also fires on a
    single-fuel BA mis-assignment, e.g. CAISO wind, in an otherwise complete
    year): this stamps the reference year block only when the balancing
    authority's *total* EIA-923 net generation is far below the EIA-930 grid
    total (the 2025 early survey, ~74%), so downstream scorecards know the
    remaining EIA-923 by-fuel totals — notably the gas split, which has no
    clean EIA-930 equivalent — are incomplete and should defer to EIA-930.
    Complete vintages return False, so the flag never appears in their block.
    """
    df = _eia923_ba_frame(iso, year)
    if df is None:
        return False
    e930 = _eia930_annual_by_fuel(iso, year)
    e930_total = e930.get("net_gen", 0.0)
    if e930_total <= 0.0:
        return False
    e923_total = float(df["net_gen"].sum()) / _MWH_PER_TWH
    return e923_total < _EIA923_VINTAGE_COMPLETENESS_FRACTION * e930_total


def build_reference(isos_filter: tuple[str, ...] | None = None) -> Path:
    """Build the calibration reference JSON and per-year CSVs.

    Args:
        isos_filter: Optional subset of :data:`CALIBRATION_ISOS` to rebuild.
            ``None`` (the default) rebuilds every ISO, exactly as before.

    MERGE, NEVER REPLACE (added 2026-09-07, lane SPP-31 — plan §7 gate **G9**,
    "shared regenerated files alter other ISOs' rows"). The committed reference
    is loaded first and only the ISOs actually built this run are updated, so an
    ISO left out keeps its committed block byte-for-byte. This is the same
    discipline ``derive_actual_lmp.main`` and ``build_miso_lmp_reference.main``
    already apply to ``actual_lmp.json``, and it matters for the same reason: a
    whole-file rebuild silently folds in every upstream input that has landed
    since the file was last written. Concretely, on 2026-09-07 a no-op rebuild of
    the committed 2026-08-07 reference moved CAISO's ENTIRE renewables block —
    ``zone_shares`` and ``monthly_capacity_mw`` reallocated across
    NP15 / ZP26 / SP15_rest — because merge ``5a910016`` (2026-09-05) landed the
    EIA-860 ``vintage_2024`` parquets and CAISO's measured plant-hub /
    FSNO-subzone membership crosswalks a month after the reference was built.
    That is a real and probably wanted CAISO re-derivation, but it is a CAISO
    input change and it belongs to the CAISO lane, not to whichever lane happens
    to add an ISO next.

    Returns:
        The path of the written ``calibration_reference.json``.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_isos = tuple(
        iso for iso in CALIBRATION_ISOS if isos_filter is None or iso in isos_filter
    )
    unknown = sorted(set(isos_filter or ()) - set(CALIBRATION_ISOS))
    if unknown:
        raise SystemExit(f"not calibration ISOs: {unknown}")

    isos: dict[str, dict] = {}
    for iso in build_isos:
        years: dict[str, dict] = {}
        for year in CALIBRATION_YEARS_BY_ISO.get(iso, CALIBRATION_YEARS):
            renewables = _eia860_renewables(iso, year)
            block = {
                "henry_hub_actual": HENRY_HUB_ACTUAL[year],
                "demand": _demand_totals(iso, year),
                "renewables": renewables,
                "generation_twh": _eia923_generation(iso, year),
            }
            if _eia923_is_incomplete(iso, year):
                # Partial current-year EIA-923 release: the under-counted
                # benchmarked fuels are already swapped to EIA-930 above (wind,
                # solar, and the ISO's extras); flag so scorecards know the
                # remaining EIA-923 by-fuel totals (notably the gas split) are
                # incomplete and should defer to EIA-930 grid totals.
                block["eia923_incomplete"] = True
            years[str(year)] = block
            csv_path = _write_year_csv(iso, year, renewables)
            logger.info("wrote %s", csv_path.relative_to(REPO))
        isos[iso] = years

    out_path = OUTPUT_DIR / "calibration_reference.json"
    payload: dict = json.loads(out_path.read_text()) if out_path.exists() else {}
    payload["generated"] = dt.date.today().isoformat()
    payload["description"] = (
        "Multi-year calibration reference: EIA-860 renewable capacity, "
        "measured Henry Hub prices, EIA-930 demand totals, EIA-923 "
        "by-fuel net generation (the per-year generation_twh benchmark, "
        "2023-2025), and the eGRID 2023 generation/emissions benchmark."
    )
    payload["calibration_years"] = list(CALIBRATION_YEARS)
    payload["henry_hub_actual"] = {str(y): p for y, p in HENRY_HUB_ACTUAL.items()}
    payload.setdefault("egrid_benchmark", {}).update(
        {iso: _egrid_benchmark(iso) for iso in build_isos}
    )
    payload.setdefault("isos", {}).update(isos)

    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    logger.info(
        "wrote %s (built: %s)", out_path.relative_to(REPO), ", ".join(build_isos)
    )
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--isos",
        nargs="+",
        default=None,
        help="Subset of CALIBRATION_ISOS to rebuild; default all. Only the "
        "built ISOs are updated -- every other ISO keeps its committed block "
        "and per-year CSVs byte-for-byte (plan gate G9).",
    )
    args = ap.parse_args()
    build_reference(tuple(args.isos) if args.isos else None)


if __name__ == "__main__":
    main()
