"""Multi-class plant attribution for the per-plant CAMPD benchmark.

Single home for the machinery that assigns a *multi-class* plant's measured
series to its model classes — the fix for the bench collapse defect
(`docs/FINDING-nyiso88-peaker-heat-rate-2026-07-27.md` §5): the benchmark
builder keyed its per-plant dicts by ``plant_code`` while iterating
``(plant_code, klass)`` groups, so a plant spanning two model classes had its
WHOLE measured CAMPD/EIA-923 series attributed to whichever class came last
alphabetically, and the model dispatch of every non-winning class was silently
dropped from the payload.

The fix keys every per-plant artifact by ``(plant_code, klass)`` — serialized
as ``"<code>:<KLASS>"`` for multi-class plants, with single-class plants
keeping their bare ``"<code>"`` keys byte-unchanged — and splits the plant's
measured series across its classes on the basis ladder below.

Split-basis ladder (most-measured first, rule 14 [R-ACCURATE]):

``unit_hourly``
    CAMPD unit-level hourly gross load (``data/raw/campd-unit-level``), units
    mapped to the plant's scored classes by their measured ``unitType``
    technology family (combined cycle / combustion turbine / boiler) and
    ``primaryFuelInfo`` coal-vs-gas branch. The plant-level net series is
    split hour by hour in proportion to each class's unit gross — a fully
    measured, hour-resolved attribution that preserves each class's real
    diurnal shape (what D-1 scores). Used whenever every scored class of the
    plant maps unambiguously to at least one CAMPD unit and every unit to
    exactly one class.

``e923_monthly``
    EIA-923 per-``(plant, prime-mover)`` monthly net generation (already
    per-class via the canonical ``classify_plant``), applied as flat-within-
    month shares. Still a measured record; loses diurnal resolution. Used
    when the unit-level mapping is ambiguous (e.g. two scored classes in the
    same technology family) or the unit extract is missing for the year.

``capacity``
    Flat proration by the model fleet's per-class capacity. An estimate, the
    documented last resort (never the default), used only when neither
    measured record resolves the plant. Model *outcomes* (dispatch shares)
    are never a basis — splitting the actual by the model's own answer would
    make the benchmark endogenous (rule 13 [R-MEASURED]).

Hours where the plant net series is positive but the chosen basis carries no
signal (e.g. a unit-level metering gap) fall back to the plant's annual class
shares on that basis for those hours only.

Consumers: ``scripts/render_calibration_html.build_payload`` (live renders),
``scripts/probes/bench_multiclass_collapse.py`` (the characterization probe),
and the one-shot committed-artifact migration. Keeping the ladder here means
the probe that predicted the correction and the code that applies it cannot
diverge.
"""

from __future__ import annotations

import collections
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent

_T = 8760

#: Serialized key separator for a (plant_code, klass) slice. A bare
#: ``"<code>"`` key is a single-class plant (unchanged wire format); a
#: ``"<code>:<KLASS>"`` key is one class slice of a multi-class plant.
KEY_SEP = ":"


def slice_key(code: int | str, klass: str | None = None) -> str:
    """Serialize a plant/class key: bare code, or ``code:KLASS`` for a slice."""
    return f"{code}{KEY_SEP}{klass}" if klass else str(code)


def parse_key(key: str) -> tuple[int, str | None]:
    """Inverse of :func:`slice_key`: ``(plant_code, klass-or-None)``."""
    if KEY_SEP in key:
        code, klass = key.split(KEY_SEP, 1)
        return int(code), klass
    return int(key), None


def plant_code_of_key(key: str) -> int:
    """Plant code of a bench/payload plant key (bare or slice form)."""
    return parse_key(key)[0]


# --------------------------------------------------------------------------- #
# Technology-family mapping (CAMPD unitType <-> model class)
# --------------------------------------------------------------------------- #
# Families carry the coal/gas branch for boilers because CAMPD's boiler
# unitTypes span both fuels while the model's ST classes split coal from gas.
_FAM_CC = "CC"
_FAM_CT = "CT"
_FAM_ST_GAS = "ST_GAS"
_FAM_ST_COAL = "ST_COAL"


def class_family(klass: str) -> str | None:
    """Technology family of a model fossil class (None = not splittable)."""
    if klass.startswith("CC_"):
        return _FAM_CC
    if klass.startswith("CT_"):
        return _FAM_CT
    if klass.startswith("ST_"):
        return _FAM_ST_GAS
    if klass.startswith("COAL"):
        return _FAM_ST_COAL
    return None


def unit_family(unit_type: str, fuel: str) -> str | None:
    """Family of a CAMPD unit from its measured unitType + primaryFuelInfo.

    Mid-year conversions carry both segments (``"Combustion turbine (Started
    Jul 01, 2024), Combined cycle (Ended Jul 01, 2024)"``); the segment
    without an ``(Ended ...)`` qualifier is the unit's current technology and
    wins. Boilers branch on the measured fuel: any coal fuel -> the coal
    family, else gas/other steam.
    """
    s = str(unit_type)
    active = [seg for seg in s.split(", ") if "(Ended" not in seg] or [s]
    a = active[0]
    if "Combined cycle" in a or "combined cycle" in a:
        return _FAM_CC
    if "Combustion turbine" in a:
        return _FAM_CT
    # Everything else in the CAMPD vocabulary is a boiler variant
    # (tangentially-fired, wall-fired, cyclone, stoker, fluidized bed, ...).
    if "coal" in str(fuel).lower():
        return _FAM_ST_COAL
    return _FAM_ST_GAS


# --------------------------------------------------------------------------- #
# Model fleet class composition (per keeper bundle, no LP)
# --------------------------------------------------------------------------- #
def scored_class_composition(
    bundle: Path,
    iso: str,
    year: int,
    cache_dir: Path | None = None,
) -> dict[int, dict[str, float]]:
    """``{plant_code: {scored_class: pmax MW}}`` for a bundle-year's fleet.

    Reconstructs the bundle's own fleet via
    ``bundle_fleet.reconstruct_bundle_fleet`` (``run_year(fleet_only=True)``
    with EVERY recorded flag, fidelity-guarded — no LP), then applies the same
    ``OTHER_FOSSIL`` scoring relabel the benchmark applies
    (``apply_other_fossil_scoring`` semantics), so the composition matches the
    classes the scored dispatch frame actually carries.
    """
    cache = None
    if cache_dir is not None:
        cache = cache_dir / f"comp_{bundle.name}_{iso}_{year}.json"
        if cache.exists():
            raw = json.loads(cache.read_text())
            return _refine_coal({int(c): dict(v) for c, v in raw.items()})

    from market_sim.data.fleet import mixed_fossil_plants
    from market_sim.config.plant_taxonomy import fossil_classes
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(bundle, year, verbose=False)
    fa = state["fleet_arrays"]
    groups = (
        fa.plant_group
        if fa.plant_group is not None
        else np.array([""] * len(fa.unit_ids), dtype=object)
    )
    fossil = set(fossil_classes())
    gas_thermal = {c for c in fossil if not c.startswith("COAL")}
    mixed = mixed_fossil_plants(year)
    comp: dict[int, dict[str, float]] = collections.defaultdict(
        lambda: collections.defaultdict(float)
    )
    for code, grp, pmax in zip(fa.plant_code, groups, fa.pmax):
        code = int(code)
        grp = str(grp)
        if code <= 0 or grp not in fossil:
            continue
        # The benchmark's scoring relabel: a genuinely-mixed gas-thermal
        # plant's gas-thermal units all score as OTHER_FOSSIL, on both sides.
        if code in mixed and grp in gas_thermal:
            grp = "OTHER_FOSSIL"
        comp[code][grp] += float(pmax)
    out = {c: dict(v) for c, v in comp.items()}
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(out, sort_keys=True))
    return _refine_coal(out)


def _refine_coal(comp: dict[int, dict[str, float]]) -> dict[int, dict[str, float]]:
    """Split a bare ``COAL`` group into its supply class, per plant.

    The dispatch frame — and therefore the bench class vocabulary — refines
    ``COAL`` via ``run_calibration_full._coal_supply_class`` (ERCOT
    lignite/PRB; EIA-923-derived bituminous/sub-bituminous/waste elsewhere;
    plain ``COAL`` only for unclassified plants). Mirror it so slice keys
    match the dispatch classes exactly. Idempotent (only exact ``"COAL"``
    entries move).
    """
    from scripts import run_calibration_full as rcf

    out: dict[int, dict[str, float]] = {}
    for code, by in comp.items():
        if "COAL" not in by:
            out[code] = by
            continue
        refined = dict(by)
        mw = refined.pop("COAL")
        # A composition cached before COAL-SUB (2026-09-25) can still carry
        # the bare COAL group; an unresolvable plant keeps that legacy key (the
        # historical residual bucket) rather than an empty one.
        k = str(rcf._coal_supply_class(int(code)) or "COAL")
        refined[k] = refined.get(k, 0.0) + mw
        out[code] = refined
    return out


def multi_class_plants(comp: dict[int, dict[str, float]]) -> dict[int, list[str]]:
    """Plants with two or more scored fossil classes, classes name-sorted."""
    return {c: sorted(v) for c, v in comp.items() if len(v) > 1}


# --------------------------------------------------------------------------- #
# Measured split bases
# --------------------------------------------------------------------------- #
def _campd_states_for_iso(iso: str) -> tuple[str, ...]:
    from market_sim.data import campd

    return campd.states_for_iso(iso)


def unit_class_hourly(
    iso: str,
    year: int,
    plant_classes: dict[int, list[str]],
    raw_dir: Path | None = None,
) -> tuple[dict[int, dict[str, np.ndarray]], dict[int, str]]:
    """CAMPD unit-level hourly gross load summed per (plant, scored class).

    One pass over the ISO's state files for ``year``; only ``plant_classes``
    plants are read. Returns ``(by_class, unresolved)`` where ``by_class``
    maps ``plant -> {klass: (8760,) gross MW}`` for plants whose units all
    resolved to exactly one scored class, and ``unresolved`` maps the rest to
    a reason string (they fall down the basis ladder).
    """
    from market_sim.data import campd as campd_mod

    raw_dir = raw_dir or (REPO / "data/raw/campd-unit-level")
    wanted = set(plant_classes)
    frames: list[pd.DataFrame] = []
    for state in _campd_states_for_iso(iso):
        path = raw_dir / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path,
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "grossLoad",
                "unitType",
                "primaryFuelInfo",
            ],
        )
        # Same split-facility re-key the facility-level path applies
        # (campd._normalize_campd / CAMPD_UNIT_PLANT_REMAP, CA only) so a
        # remapped unit's history lands on the plant the bench carries.
        fac = pd.to_numeric(df["facilityId"], errors="coerce").fillna(-1).astype(int)
        uid = df["unitId"].astype(str)
        df["facilityId"] = [
            campd_mod.CAMPD_UNIT_PLANT_REMAP.get((f, u), f) for f, u in zip(fac, uid)
        ]
        df = df[df["facilityId"].isin(wanted)]
        if not df.empty:
            frames.append(df)
    by_class: dict[int, dict[str, np.ndarray]] = {}
    unresolved: dict[int, str] = {}
    if not frames:
        return by_class, {c: "no unit-level extract" for c in wanted}
    df = pd.concat(frames, ignore_index=True)
    # Hour-of-year on the model's fixed 8760 clock — the SAME mapping the
    # facility-level bench series uses (campd._hour_index_8760: month/day
    # based, Feb 29 -> -1 and dropped).
    dt = pd.to_datetime(df["date"])
    hidx = campd_mod._hour_index_8760(
        dt.dt.month.to_numpy(), dt.dt.day.to_numpy(), df["hour"].to_numpy()
    )
    df = df.assign(_h=hidx)
    df = df[(df["_h"] >= 0) & (df["_h"] < _T)]

    for code, g in df.groupby("facilityId"):
        classes = plant_classes[int(code)]
        fam_to_class: dict[str, str] = {}
        ambiguous = None
        for k in classes:
            fam = class_family(k)
            if fam is None:
                ambiguous = f"class {k} has no technology family"
                break
            if fam in fam_to_class:
                ambiguous = f"classes {fam_to_class[fam]} and {k} share family {fam}"
                break
            fam_to_class[fam] = k
        if ambiguous:
            unresolved[int(code)] = ambiguous
            continue
        per_class: dict[str, np.ndarray] = {k: np.zeros(_T) for k in classes}
        unit_meta = g.groupby("unitId")[["unitType", "primaryFuelInfo"]].first()
        unit_cls: dict[str, str] = {}
        for uid, row in unit_meta.iterrows():
            fam = unit_family(row["unitType"], row["primaryFuelInfo"])
            k = fam_to_class.get(fam)
            if k is None:
                ambiguous = f"unit {uid} family {fam} matches no scored class {classes}"
                break
            unit_cls[str(uid)] = k
        if ambiguous:
            unresolved[int(code)] = ambiguous
            continue
        got = set()
        for uid, gu in g.groupby("unitId"):
            k = unit_cls[str(uid)]
            hh = gu["_h"].to_numpy(int)
            per_class[k][hh] += np.nan_to_num(gu["grossLoad"].to_numpy(float))
            got.add(k)
        missing = [k for k in classes if k not in got]
        if missing:
            unresolved[int(code)] = f"no CAMPD unit maps to class(es) {missing}"
            continue
        by_class[int(code)] = per_class
    for code in wanted - set(by_class) - set(unresolved):
        unresolved[code] = "plant absent from unit-level extract"
    return by_class, unresolved


def hourly_shares(
    class_hourly: dict[str, np.ndarray],
    classes: list[str],
) -> np.ndarray:
    """``(n_classes, 8760)`` hourly shares from per-class gross series.

    Hours with zero total gross take the annual class shares (the plant-level
    net can be positive there only across a metering gap; a flat fallback for
    those hours preserves the annual split exactly).
    """
    stack = np.vstack([class_hourly[k] for k in classes])
    tot = stack.sum(axis=0)
    ann = stack.sum(axis=1)
    ann_share = (
        ann / ann.sum() if ann.sum() > 0 else np.full(len(classes), 1.0 / len(classes))
    )
    shares = np.where(tot > 0, stack / np.where(tot > 0, tot, 1.0), ann_share[:, None])
    return shares


def monthly_shares_to_hourly(
    monthly: dict[str, np.ndarray],
    classes: list[str],
) -> np.ndarray:
    """``(n_classes, 8760)`` flat-within-month shares from monthly MWh.

    Accepts 12-vector monthlies or 13-vector ``[annual, m01..m12]`` rows (the
    last 12 entries are the months either way).
    """
    from scripts import run_calibration_full as rcf

    edges = np.cumsum([0] + list(rcf._DAYS_IN_MONTH)) * 24
    stack = np.vstack(
        [np.clip(np.asarray(monthly[k], dtype=float)[-12:], 0.0, None) for k in classes]
    )
    ann = stack.sum(axis=1)
    ann_share = (
        ann / ann.sum() if ann.sum() > 0 else np.full(len(classes), 1.0 / len(classes))
    )
    out = np.zeros((len(classes), _T))
    for m in range(12):
        tot = stack[:, m].sum()
        col = stack[:, m] / tot if tot > 0 else ann_share
        out[:, edges[m] : edges[m + 1]] = col[:, None]
    return out


def capacity_shares(
    comp: dict[str, float],
    classes: list[str],
) -> np.ndarray:
    """``(n_classes, 8760)`` flat capacity-prorated shares (last resort)."""
    caps = np.array([max(float(comp.get(k, 0.0)), 0.0) for k in classes])
    tot = caps.sum()
    share = caps / tot if tot > 0 else np.full(len(classes), 1.0 / len(classes))
    return np.repeat(share[:, None], _T, axis=1)


#: EIA-860 prime-mover -> technology family (combined-cycle parts CA/CT/CS,
#: simple-cycle GT/IC, steam ST branching coal-vs-gas on the energy source).
_EIA860_PM_FAMILY: dict[str, str] = {
    "CA": _FAM_CC,
    "CT": _FAM_CC,
    "CS": _FAM_CC,
    "GT": _FAM_CT,
    "IC": _FAM_CT,
}
_COAL_SOURCES: frozenset[str] = frozenset(
    {"BIT", "SUB", "LIG", "WC", "RC", "ANT", "SGC", "SC"}
)


def plant_class_nameplates(
    plant_ids: set[int],
) -> dict[int, dict[str, float]]:
    """``{plant: {family: nameplate MW}}`` from the EIA-860 fleet parquet.

    The structural (non-outcome) capacity basis for nameplate proration and
    per-slice ``npl``: per-generator prime mover maps to a technology family,
    steam units branching coal-vs-gas on their energy source.
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.fleet import EIA_860_PARQUET_NAME

    path = EIA_860_DIR / EIA_860_PARQUET_NAME
    if not path.exists():
        return {}
    df = pd.read_parquet(
        path,
        columns=["plant_id", "prime_mover", "energy_source", "nameplate_capacity_mw"],
    )
    df = df[df["plant_id"].astype(int).isin(plant_ids)]
    out: dict[int, dict[str, float]] = collections.defaultdict(
        lambda: collections.defaultdict(float)
    )
    for pid, pm, src, cap in zip(
        df["plant_id"],
        df["prime_mover"],
        df["energy_source"],
        df["nameplate_capacity_mw"],
    ):
        pm = str(pm).upper()
        fam = _EIA860_PM_FAMILY.get(pm)
        if fam is None:
            fam = _FAM_ST_COAL if str(src).upper() in _COAL_SOURCES else _FAM_ST_GAS
        out[int(pid)][fam] += float(cap or 0.0)
    return {p: dict(v) for p, v in out.items()}


def class_nameplate_split(
    fam_npl: dict[str, float],
    classes: list[str],
) -> dict[str, float]:
    """Map a plant's per-family EIA-860 nameplate onto its model classes.

    Each model class takes its own family's nameplate; a family with no
    matching class folds into the largest class; a class with no family
    nameplate gets 0 (callers fall back to equal shares when all are 0).
    """
    caps: dict[str, float] = {k: 0.0 for k in classes}
    fam_to_class: dict[str, str] = {}
    for k in classes:
        fam = class_family(k)
        if fam and fam not in fam_to_class:
            fam_to_class[fam] = k
    for fam, mw in fam_npl.items():
        k = fam_to_class.get(fam)
        if k is None:
            k = max(caps, key=caps.get)
        caps[k] += float(mw)
    return caps


def nameplate_shares(
    caps: dict[str, float],
    classes: list[str],
    cap_plant: float,
) -> dict[str, float]:
    """Per-slice ``npl`` scaled to the plant nameplate, sum-preserving.

    Shares follow ``caps`` (equal when all zero); every slice but the largest
    is rounded and the largest absorbs the remainder, so the slice ``npl``
    values sum exactly to ``round(cap_plant)`` — the committed plant value.
    """
    tot = sum(max(v, 0.0) for v in caps.values())
    if tot > 0:
        share = {k: max(caps.get(k, 0.0), 0.0) / tot for k in classes}
    else:
        share = {k: 1.0 / len(classes) for k in classes}
    biggest = max(classes, key=lambda k: share[k])
    out: dict[str, float] = {}
    acc = 0.0
    for k in classes:
        if k == biggest:
            continue
        out[k] = float(round(cap_plant * share[k]))
        acc += out[k]
    out[biggest] = float(round(cap_plant)) - acc
    return out


def e923_class_monthly(
    iso: str,
    year: int,
) -> dict[int, dict[str, np.ndarray]]:
    """EIA-923 monthly net MWh per (plant, scored class) for the ISO-year.

    The same ``_eia923_frame`` + ``apply_other_fossil_scoring`` chain the
    benchmark's actual side uses, so a slice's EIA-923 annual/monthly is the
    measured per-prime-mover record — never a proration.
    """
    from market_sim.data.eia923 import load_monthly_generation
    from market_sim.data.fleet import apply_other_fossil_scoring
    from scripts import run_calibration_full as rcf

    e923 = rcf._eia923_frame(year, load_monthly_generation(), iso)
    e923 = apply_other_fossil_scoring(e923, year, plant_col="plant_id")
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    out: dict[int, dict[str, np.ndarray]] = collections.defaultdict(dict)
    for (pid, klass), g in e923.groupby(["plant_id", "klass"], observed=True):
        arr = g[mcols].sum().to_numpy(float)
        prev = out[int(pid)].get(str(klass))
        out[int(pid)][str(klass)] = arr if prev is None else prev + arr
    return dict(out)


def map_e923_to_model_classes(
    e923_by_class: dict[str, np.ndarray],
    classes: list[str],
    comp: dict[str, float],
    empty_len: int = 12,
) -> dict[str, np.ndarray]:
    """Assign a plant's EIA-923 per-class monthly rows to its model classes.

    Exact class-name match first; an unmatched EIA-923 class falls to the
    model class sharing its technology family, else to the plant's largest
    class (logged by the caller via the returned dict's coverage). Length-
    agnostic: works for 12-vector monthlies or 13-vector [annual, m01..m12].

    ``empty_len`` is the vector length to return when the plant has **no**
    EIA-923 rows at all, where there is no input array to take the length
    from. It must match the caller's convention: a caller that reads
    ``[1:]`` as twelve months needs ``empty_len=13``, or a multi-class plant
    absent from EIA-923 yields an 11-month array and the reader runs off the
    end. Defaults to 12 so existing 12-vector callers are unchanged.
    """
    n = len(next(iter(e923_by_class.values()))) if e923_by_class else int(empty_len)
    out: dict[str, np.ndarray] = {k: np.zeros(n) for k in classes}
    fam_to_class: dict[str, list[str]] = collections.defaultdict(list)
    for k in classes:
        fam = class_family(k)
        if fam:
            fam_to_class[fam].append(k)
    largest = max(classes, key=lambda k: comp.get(k, 0.0))
    for ek, arr in e923_by_class.items():
        if ek in out:
            out[ek] += arr
            continue
        fam = class_family(ek)
        cands = fam_to_class.get(fam or "", [])
        target = cands[0] if len(cands) == 1 else largest
        out[target] += arr
    return out


def split_measured_series(
    net_mw: np.ndarray,
    classes: list[str],
    comp: dict[str, float],
    unit_hourly: dict[str, np.ndarray] | None,
    e923_monthly: dict[str, np.ndarray] | None,
) -> tuple[dict[str, np.ndarray], str]:
    """Split a plant's measured hourly net series across its classes.

    Walks the basis ladder (module docstring): unit-level hourly shares,
    EIA-923 monthly shares, capacity proration. Returns
    ``({klass: (8760,) MW}, basis)`` with the slice sum equal to the input
    series in every hour by construction.
    """
    if unit_hourly is not None and all(k in unit_hourly for k in classes):
        shares = hourly_shares(unit_hourly, classes)
        basis = "unit_hourly"
    elif e923_monthly is not None and any(
        np.asarray(v).sum() > 0 for v in e923_monthly.values()
    ):
        shares = monthly_shares_to_hourly(e923_monthly, classes)
        basis = "e923_monthly"
    else:
        shares = capacity_shares(comp, classes)
        basis = "capacity"
    series = {k: shares[i] * net_mw for i, k in enumerate(classes)}
    return series, basis
