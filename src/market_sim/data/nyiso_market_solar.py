"""NYISO front-of-meter (market-generator) solar capacity by model zone.

Loader for the frozen artifact
``data/raw/reference/nyiso-market-solar-capacity.csv``, built by
``scripts/data/derive_nyiso_market_solar.py`` from NYISO's Gold Book
*Table III-2a — NYISO Market Generators* (vintages 2023 / 2024 / 2025).

**The defect this input corrects (rule 14 ``[R-ACCURATE]``).** The model
distributes NYISO solar capacity from the EIA-860 utility-scale operable
schedule, which lists every NY solar plant ≥ 1 MW — including ~2 GW of
**distribution-connected NY-Sun community solar that is not a NYISO market
generator**. That output is already **netted out of the EIA-930 ``NYIS``
demand series** the model uses as load: EIA-930 ``NYIS`` ``NG: SUN`` is
identically zero in every hour of 2023-2025 (nyiso-106 measured 8,760/8,760
zero hours — *"structurally absent (NY grid solar is overwhelmingly
distribution-connected / net-metered)"*). Carrying it a second time as a
grid-supply decision variable is a **double count** of the same MWh: once as a
reduction in demand, once as supply.

This is the rule-14 *documented-misalignment* path, not a free choice: the
EIA-860 population is defined on a **different boundary** than the model's
representation (grid-supply resources against an EIA-930 net-load demand
series), so it is reconciled to the subset that is actually a NYISO grid
resource rather than replaced by a guess.

**Identification carries no freedom.** A NY solar plant is a NYISO grid-supply
resource *iff NYISO registers it in Table III-2a*. Three published columns
(load zone A-K, nameplate MW, in-service date) and the same A-K → five-zone
crosswalk the rest of the codebase uses
(:data:`market_sim.data.nyiso_demand_response._ZONE_TO_MODEL`). The monthly
ramp is the construction :func:`market_sim.data.renewables._eia860_monthly_capacity`
already applies to EIA-860 — a plant contributes from its in-service month
onward — so this is a **basis swap on one input**, not a new mechanism.

**Rule 13 ``[R-MEASURED]``.** An INPUT (which plants are NYISO market
generators, and how big they are), never an outcome. It regenerates for a
forward year from the same registry, and it responds to changed conditions.
It is emphatically *not* the measured solar generation series and it does not
cap dispatch at delivered output (contrast the CAISO
``caiso_solar_cap_at_delivered`` diagnostic, which pins to an outcome and is
rule-13 inadmissible in a keeper): the LP still dispatches and curtails solar
endogenously against this capacity.

**DECLARED LIMITATION, stated here because it bounds what the mechanism may
claim.** This swaps the capacity *basis* only; the hourly CF profile keeps its
existing ISO-wide normalization (``RENEWABLE_AVG_CF["NYISO"]["solar"]``, a
whole-NY-fleet blend the model realizes at ≈ 0.133). NYISO's registered market
fleet is more modern and more single-axis-tracking than that blend (the Gold
Book's own Net Energy column gives it ≈ 0.20 CF), so the two need not agree.
**Measured against the registry's own published output** (0.23 / 0.50 /
1.08 TWh in 2023 / 2024 / 2025), the armed mechanism delivers 0.21 / 0.52 /
0.75 TWh: within 8 % and 4 % in 2023 and 2024, but **0.33 TWh short in 2025**,
where the large tracking plants (Morris Ridge, High River, East Point) came to
dominate the registry. The residual 2025 error is therefore in the
**tightening** direction, and a 2025 price improvement must be read against
that bound rather than banked whole. Re-identifying the fleet CF is a separate
object with its own identification work (rule 19 ``[R-ONE-MECH]``) and is
deliberately **not** bundled here.

**Rule 25 ``[R-ISO-SCOPE]``.** NYISO-only, from NYISO's own posting; the
artifact records its ISO and :func:`load_market_solar_monthly` hard-errors on
a mismatch rather than falling back to another ISO's numbers.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

import numpy as np

from market_sim.config.paths import RAW_DIR

ARTIFACT: Path = RAW_DIR / "reference" / "nyiso-market-solar-capacity.csv"

MONTHS_PER_YEAR: int = 12


@lru_cache(maxsize=1)
def _read_artifact(path: str) -> dict[tuple[int, int, str], float]:
    """Return ``{(year, month, model_zone): capacity_mw}`` from the artifact.

    Args:
        path: Absolute path to the curated CSV (a string so the cache key is
            hashable).

    Returns:
        Mapping from ``(year, month, model zone)`` to registered nameplate MW.

    Raises:
        ValueError: if any row carries an ISO other than ``NYISO`` (rule 25 —
            never silently consume another ISO's artifact).
    """
    out: dict[tuple[int, int, str], float] = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(line for line in fh if not line.startswith("#")):
            iso = (row["iso"] or "").strip().upper()
            if iso != "NYISO":
                raise ValueError(
                    f"{path}: row carries iso={iso!r}; this artifact is NYISO-only "
                    "(rule 25 [R-ISO-SCOPE])"
                )
            key = (int(row["year"]), int(row["month"]), row["model_zone"].strip())
            out[key] = float(row["capacity_mw"])
    if not out:
        raise ValueError(f"{path}: no rows")
    return out


def load_market_solar_monthly(
    iso: str,
    year: int,
    zone_names: list[str] | tuple[str, ...],
    path: Path | None = None,
) -> np.ndarray | None:
    """Return NYISO registered market-generator solar capacity by zone-month.

    Args:
        iso: ISO identifier; anything other than ``"NYISO"`` returns ``None``
            (rule 25 — the mechanism never crosses an ISO boundary).
        year: Solve year.
        zone_names: Ordered model zone names, matching ``iso_config.zones``.
        path: Optional artifact override (tests).

    Returns:
        An ``(n_zones, 12)`` array of registered nameplate MW by month, ordered
        to ``zone_names``; ``None`` when the ISO is not NYISO or the artifact
        does not cover ``year`` (a missing year leaves the EIA-860 basis
        untouched rather than substituting a silent hand number).

    Raises:
        FileNotFoundError: if the artifact is absent while the mechanism is
            armed — an armed mechanism must never degrade to the basis it was
            armed to replace without saying so.
    """
    if iso.upper() != "NYISO":
        return None
    src = Path(path) if path is not None else ARTIFACT
    if not src.exists():
        raise FileNotFoundError(
            f"nyiso_solar_market_generator_basis is armed but {src} is missing; "
            "regenerate with scripts/data/derive_nyiso_market_solar.py"
        )
    table = _read_artifact(str(src))
    if not any(k[0] == year for k in table):
        return None
    monthly = np.zeros((len(zone_names), MONTHS_PER_YEAR), dtype=float)
    for z_idx, zone in enumerate(zone_names):
        for month in range(1, MONTHS_PER_YEAR + 1):
            monthly[z_idx, month - 1] = table.get((year, month, zone), 0.0)
    return monthly
