"""Caching of intermediate and final simulation results.

A cached run lives in ``results/{iso}/{cache_key}/`` where ``cache_key`` is
the deterministic hash of the :class:`~market_sim.config.scenarios.ScenarioConfig`
that produced it. Each weather year's final dispatch is one
``year_{year}.parquet`` file, and the full config is written once as
``config.yaml`` alongside it.

When the two-pass commitment screen runs, the year also keeps a separate
``year_{year}_p1.parquet`` holding the Pass 1 (pre-commitment) dispatch, so
both the P1 and the final P2 datasets are available. ``year_{year}.parquet``
always holds the final result — P2 when commitment is enabled, P1 when it is
off — so every existing reader is unaffected by the extra P1 file.

Cache-key staleness (cache-epoch policy)
----------------------------------------
The cache directory is keyed on ``ScenarioConfig.cache_key()``, which hashes
``asdict(config)`` — so a change that alters a solve's *output* but is **not** a
``ScenarioConfig`` field (a bug fix in the LP builder, a new mechanism gated by
an env var, a change to a measured input basis) does NOT move the key, and a
pre-change ``results/{iso}/{key}/`` bundle would be silently re-used. The
project's cache-epoch policy (refactor-consolidation plan §7 H, compat clause 2)
governs this: a behavior-changing PR must either express the change as a
``ScenarioConfig`` field (so the key moves) or bump the documented cache epoch
and purge/segregate the affected caches. A pure byte-identical refactor needs
neither. This module never auto-invalidates on epoch; that is the operator's
responsibility per that policy.

**The epoch is a dated ledger entry, not a code token.** There is deliberately
no ``CACHE_EPOCH`` constant: a constant that entered ``ScenarioConfig`` would
move the key of *every* config including the backcast keepers (a solve-affecting
change under rule 24 and a rule-28 matrix row for a non-mechanism), and one that
did not enter the key would be inert. The epoch is therefore materialized on two
surfaces, both human-read:

* **Key advances** — when a change legitimately re-keys the DEFAULT config —
  are recorded at ``PINNED_DEFAULT_CACHE_KEY`` in
  ``tests/regression/test_persisted_identity.py``, with a dated cause block
  above the literal. A key movement caused by an unregistered new field is NOT
  an advance: the remedy is ``_CACHE_KEY_OPTIONAL_FIELDS`` registration
  (``scripts/check_cache_key_registration.py``), never re-pinning.
* **Same-key invalidations** — a behavior change that leaves every key
  unmoved — are recorded in the ledger below, because nothing else can see
  them. Each entry names its date, its cause, exactly what is invalidated, and
  what is NOT.

Cache-epoch ledger (same-key invalidations)
-------------------------------------------
**Epoch 2026-08-04c — FFR-4D CAISO base-fleet re-vintage. NO KEY MOVES; CAISO
BUNDLES IN BOTH MODES ARE INVALIDATED.** Three CAISO-scoped changes
(``docs/handoffs/ffr-4d-caiso-fleet-vintage-2026-08-04.md``), all of which move
CAISO output under **unchanged cache keys**:

* **``STORAGE_BASE_FLEET_MW["CAISO"]`` re-vintaged** — ``low/mid/high``
  ``6,000 / 8,000 / 12,000`` → ``11,590 / 15,450 / 19,260`` MW, re-derived by
  the registry's OWN documented EIA-860 construction (the one that already
  reproduces PJM/MISO/NYISO/NEISO exactly) on the committed EIA-860 2025 Early
  Release. A **constants-level** change with no ``ScenarioConfig`` field, so no
  key moves. **Behavioral in CAISO forecast mode** (the base-year storage fleet
  nearly doubles).
* **``RENEWABLE_INSTALLED_MW["CAISO"]`` re-vintaged** — wind ``7,000 → 6,330``
  and solar ``22,000 → 24,920`` MW, from the same EIA-860 release. Also
  constants-level, also no key move. **Behavioral in CAISO FORECAST mode only**:
  ``data.renewables`` reads this registry only when ``mode != "backcast"``; a
  backcast already takes that year's EIA-860 month-end capacity.
* **``storage_measured_base_fleet`` added, default ``True``** — a CAISO backcast
  now resolves its storage base fleet as of its solve year from EIA-860
  (``model.storage.load_eia860_storage``) instead of the flat forecast scalar.
  Registered in ``_CACHE_KEY_OPTIONAL_FIELDS``, so the key does NOT move — this
  is the default-flip hazard the entry below describes, entered DELIBERATELY and
  recorded here because the ledger is the only surface that can see it.
  **Behavioral in CAISO backcast mode**: the fleet goes from a flat 8,000 MW to
  the measured 7,492 / 11,131 / 15,448 MW at year-end 2023 / 2024 / 2025.

**The same-key collision is MEASURED, not asserted.** FFR-4D solved both arms of
the CAISO 2026-2030 forecast at one head — control (pre-FFR-4D constants) and
treated — and **both resolve to the SAME key** ``35b0a89be0c07483`` while
producing materially different output: cumulative ``reserve_backstop`` additions
14,043.6 MW vs 8,186.3 MW, FC-2 row 4 65.48 % vs 52.51 %, and invariant ``I3``
FAIL vs PASS. The arms stayed clean only because each had its own ``--out-dir``;
sharing one would have made the second run silently re-use the first's bundle.
This is the first entry in this ledger whose collision is demonstrated by a
solved A/B rather than inferred from the registration mechanics.

*Invalidated:* **every cached CAISO bundle, in BOTH modes** — forecast bundles
(all three changes) and backcast bundles (the third). **The designated CAISO
keeper ``2026-08-04-caiso-172-measured-path15`` — and every CAISO keeper before
it — was solved on the flat 8,000 MW scalar, so its committed metrics are
PRE-EPOCH**; it needs a re-solve
and a re-gate in the CAISO lane before its numbers are quoted again. That is
stated as an open, owed item in the FFR-4D handoff §7, not as a completed one.

*NOT invalidated:* **every other ISO, in both modes.** All three changes are
CAISO-scoped by construction — two are CAISO rows of per-ISO registries, and the
third resolves through ``STORAGE_MEASURED_BASE_FLEET_ISOS``, which contains
CAISO alone. ERCOT/PJM/MISO/NYISO/NEISO keepers are untouched (rule 25
[R-ISO-SCOPE]); ERCOT's own hand-entered storage row is routed, not changed.

**Epoch 2026-08-04b — FFR-3U bridge-seam fix + the D-11 two-key quarantine. NO
KEY MOVES; TWO KEYS ARE PERMANENTLY REFUSED.** The seam fix
(``docs/handoffs/ffr-3u-bridge-seam-2026-08-04.md``) scopes the runner's
un-bridging clause to genuine T1-X crossover forward years, so a T1-FF window
whose boundary sits at its own base year again BRIDGES 2022 (and 2026) instead
of solving them. It is a guard change, not a mechanism: **no ``ScenarioConfig``
field was added, removed or re-defaulted, and all seven measured keys — the
default plus the six per-ISO 2023 backcast keys — are byte-identical before and
after** (default ``603c2498bf71d21d``; ERCOT ``df386bca96a1d288``, CAISO
``a9afddae291525c1``, PJM ``9834b2018b598423``, MISO ``2a1252c3acae89e9``,
NYISO ``fd15030b3ee60f11``, NEISO ``5b1633171fead559``).

*Invalidated:* **exactly two bundles**, ``b99600bceb8cb6b8`` and
``5c352508039513da`` — FFR-3Q's two ERCOT base-2021 T1-FF arms, which solved
2022 (a validation-tier holdout) under an active freeze. Because the fix moves
no key, the same config still hashes to them, so the refusal is mechanical
rather than documentary: see :data:`CONTAMINATED_CACHE_KEYS` and
:func:`assert_cache_key_uncontaminated`, enforced at ``get_cache_path``.
Owner decision D-11 condition 2.

*NOT invalidated:* everything else. No backcast bundle, no keeper, no T1-H,
T1-X or base-2023 T1-FF leg is touched — every one of those postures realizes
the identical solve-year set before and after (measured across seven postures in
``tests/scoring/test_full_forward_hindcast.py::TestBridgeSeam``). The only
behavioural change is that a posture which was *illegal to run at all* now
bridges instead of solving.

**Epoch 2026-08-04 — D-10 warm-start OFF for forecast bundles. THIS ONE IS A KEY
ADVANCE, NOT A SAME-KEY INVALIDATION — recorded here anyway because it is the
entry a reader looking for "why did every forecast key move on 2026-08-04" will
come to.** Owner decision D-10 (sitting ``ffr-owner-sitting-2026-08-02.md``
Addendum K.3, implemented by FFR-3T,
``docs/handoffs/ffr-3t-warmstart-off-2026-08-04.md``): every shipped forecast
runner now passes ``forecast_xyear_warmstart=False`` explicitly, so a resumed
forecast solves its first post-kill year the same way its control does — cold —
and the kill-resume drill (FF-3E part c) is structurally passable.

*Cause:* the flag is a ``_CACHE_KEY_OPTIONAL_FIELDS`` member, so an EXPLICIT
non-default ``False`` enters the hash. **Measured, all six ISOs x four shipped
forecast configs (T1-F / T1-H / T1-X / golden-posture battery): 24 of 24 keys
MOVED** — e.g. ERCOT T1-F ``e8ce5b85cc254830 -> 02d559f6a00f24b7``, NEISO T1-H
``cee8181a253afd6a -> 688dd67264951c7e``. Because the keys move, **no purge is
required for correctness**: a cold post-D-10 run cannot be served a warm
pre-D-10 bundle — they are addressed differently. Pre-D-10 warm forecast
bundles simply become unreachable by the shipped runners; delete them to
reclaim disk, using the tracked-file warning below, or leave them.

*Why this is NOT expressed as a default flip, which is the form the signed
decision's coordination note anticipated.* Both halves of a default flip were
measured at implementation and both exceed the decision:

* **forecast keys would NOT have moved.** ``cache_key`` drops a registered
  field at the LIVE default, so a post-flip ``False`` default hashes exactly as
  the pre-flip ``True`` default did — all 24 keys byte-IDENTICAL across the
  simulated flip, i.e. a cold run silently re-using a warm bundle. That is the
  FFR-3A blocker-4 same-key invalidation this ledger's 2026-08-03 entry
  describes, recurring exactly as that entry predicted it would.
* **backcast keeper keys WOULD have moved.** Every keeper's ``run_config.json``
  carries an explicit ``true``, which becomes non-default after a flip: all six
  moved (ERCOT ``f95a5d2aab761873 -> 86cdfc027116b309``, PJM
  ``c20ec90ee9626b07 -> c562ac25bb545281``, and so on).

*NOT invalidated:* **every backcast bundle and every keeper.** The six keeper
cache keys are byte-identical before and after (ERCOT ``f95a5d2aab761873``,
PJM ``c20ec90ee9626b07``, CAISO ``df6220a243add2ad``, NYISO
``c3b175a9fcf4af8d``, NEISO ``6ff540e9a9ee3b2f``, MISO ``dfe9d5c68e15c54c``),
the pinned default key is unmoved at ``603c2498bf71d21d``, and the backcast
solve PATH is untouched: ``run_calibration_full.py`` passes no explicit
``xyear_warmstart``, so the calibration lane still resolves cross-year warm
start from ``MARKET_SIM_WARMSTART_XYEAR`` (default ON) exactly as before.

**Epoch 2026-08-03b — FFR-SC NYISO demand-anchor re-derive (NYISO forecast only).**
``constants.DEMAND_GROWTH_RATES["NYISO"]`` is re-derived from the 2026 Gold Book
(``docs/handoffs/ffr-sc-transmission-ab-2026-08-03.md`` §7): mid near
``0.018 → 0.0122``, long ``0.012 → 0.0127``, low ``0.008/0.006 → -0.0024/0.0028``,
high ``0.030/0.020 → 0.0263/0.0196``. A **constants-level** change with no
``ScenarioConfig`` field, so **no key moves** — measured: ``ScenarioConfig()``
hashes to ``973a0acdef818e91`` both with and without it (the move from the
ledger entry below's ``603c2498bf71d21d`` is upstream field additions, not this).

*Invalidated:* cached **NYISO forecast-mode** bundles (including ``hindcast=True``
and T1-X crossover legs) solved before this commit — their demand trajectory is
the superseded 2025-Gold-Book one. *NOT invalidated:* every other ISO (only the
NYISO row moved), and **every backcast bundle in every ISO** — the backcast path
takes measured load and never reads this table, so no keeper is touched. The
concurrent ATB pin move (v3.0.0 → v4.0.0) invalidates nothing at all: every
derived constant is byte-identical under both versions.

**Epoch 2026-08-03 — FFR Wave-2 constants + the D-1/D-2 owner default flips.**
Taken at FFR-3A step 0 (`docs/handoffs/ffr-t1-regate-2026-08-02.md`), clearing
the epoch debt the owner sitting recorded as outstanding
(`ffr-owner-sitting-2026-08-02.md` Addendum B.6, "FFR-3A must clear this debt
before its consolidated battery — it is now a concrete item, not a
hypothetical"). Three causes, all of which move forecast output under
**unchanged cache keys**:

* **FFR-2C net-CONE re-anchor** (`ffr-2c-net-cone-currency-2026-08-02.md`,
  commits `5dcba9c` PJM / `aaa6a25` NYISO) — a **constants-level** change that
  landed AFTER the single 2026-08-02 bump. Two forward net-CONE vintages are
  re-anchored from their published instruments: **PJM 2027/28 → 2028/29
  (88.520 → 118.877 $/kW-yr, +34.3 %)** and **NYISO 2025-26 → 2026-27
  (+14.1 %)**. No ``ScenarioConfig`` field changed, so no key moved.
  **Behavioral** in every forecast year the new vintage governs (PJM: solve
  year 2028+), through all three capacity screens, which price on the one
  ``capacity_price_per_firm_mw_yr`` seam. PJM additionally gains a published
  price floor that removes the curve's zero-cross from 2028.
* **Owner decision D-1** (this session) — ``retirement_rule`` default
  ``"legacy"`` → ``"pipeline"``. **Behavioral in every forecast year** (a
  different retirement decision rule).
* **Owner decision D-2** (this session) — ``entry_rate_limits`` and
  ``entry_commissioning_lag`` defaults ``False`` → ``True``. **Behavioral in
  every forecast year** (rate-limited entry, +2-year COD lag). The same commit
  fixed a latent ``TypeError`` in the growth-ladder seed that the arming made
  reachable (``runner.py``), so no pre-flip cache of an armed run can exist.

**Why D-1/D-2 are same-key invalidations and NOT key advances — correcting a
premise in the signed packet.** The sitting's D-1 section states the field is
"cache-key-registered at non-default, so the flip moves forecast cache keys by
construction — no silent reuse". **That is not how the registration behaves.**
``cache_key()`` drops a ``_CACHE_KEY_OPTIONAL_FIELDS`` member when it equals
``getattr(ScenarioConfig(), name)`` — the **LIVE** default, recomputed on every
call, not a frozen sentinel. Flipping such a field's default therefore drops the
NEW value from the hash and the key does **not** move: measured this session,
``cache_key(ScenarioConfig())`` is ``603c2498bf71d21d`` both before and after
all three flips. A pre-flip legacy-rule bundle and a post-flip pipeline-rule
config are the same key. The inverse also holds and is useful: an EXPLICIT
``retirement_rule="legacy"`` is now non-default and hashes distinctly
(``0e49083ebacb2612``), so control arms in the FFR-3A battery are safely
separable. **Structural note for any future default flip of an optional-
registered field: it will silently recur, and the ledger is the only thing that
can see it.**

*Invalidated:* every cached bundle produced in **forecast mode**
(``mode="forecast"``, including ``hindcast=True`` and T1-X crossover legs) at a
commit before this epoch — in particular every FC-3 citation in
``ff-t1-gate-2026-07.md`` §4.1, which FFR-2E already flagged as pre-epoch legs.
Purge exactly as the 2026-08-02 entry below directs.

.. warning::

   **Purge only what git does not track.** The ``find ... -delete`` loop below
   is safe for the directories it names, but ``results/`` also holds COMMITTED
   evidence bundles from earlier lanes (e.g. ``results/ff2b-after/``,
   ``results/ffr1c/`` — registered ``evolution_<year>.json`` and
   ``full_horizon_summary.json`` artifacts cited by their handoffs). Extending
   the loop to those directories deletes tracked files: FFR-3A did exactly that
   and had to ``git checkout -- results/`` to restore 410 of them. Check
   ``git status --short`` after any purge, and restore anything showing ``D``.
   The actual invalidated artifacts are the gitignored per-ISO cache roots and
   ``year_*.parquet`` files, which is all the loop below needs to reach.

*NOT invalidated:* **backcast** caches and every keeper bundle. The two
re-anchored vintages are forecast-only forward capacity parameters; ``retirement
_rule`` and both entry gates drive forecast-mode capacity evolution, which does
not run in a backcast. The six current keepers' cache keys are unmoved (the
default key is byte-stable at ``603c2498bf71d21d``, and no keeper sets any of
the three fields).

**Epoch 2026-08-02 — FFR Wave-1 forecast fixes (FR-1, FR-2, FR-7, FR-8).**
Taken once at the Wave-1 close (`docs/forecast-readiness-prompt-pack-2026-07.md`
§W1-X; `docs/handoffs/ffr-w1x-wave1-close-2026-08-02.md`). Four merged fixes
change forecast output under **unchanged cache keys** — none added, removed or
re-defaulted a ``ScenarioConfig`` field, so no key moved and a pre-Wave-1 bundle
would be silently re-used:

* **FR-1** (`ffr-1a-confirmed-exit-accounting-2026-07-31.md`) — confirmed-exit
  tranche derates are now written to the evolution ledger. Dispatch-inert
  (byte-identity attested), but every cached ``evolution_<year>.json`` from a
  forecast run predating it is missing its ``confirmed_derates`` rows and its
  ``confirmed``/``announced`` reason split.
* **FR-2** (same doc, arm 2) — partial-year confirmed exits now complete in
  year+1 instead of holding a fraction of their MW forever. **Behavioral:**
  fleet MW, dispatch and prices move from the exit year+1 onward.
* **FR-7** (`ffr-1b-solve-year-availability-2026-08-01.md`) — the age-based
  availability escalation keys on the SOLVE year, not ``weather_year``.
  **Behavioral in every forecast year**: the fleet ages, and model-built
  entrants no longer carry a negative age.
* **FR-8** (same doc) — the measured 2025 Martin Lake derate is gated to
  backcast, so it can no longer leak into a ``weather_year=2025``-pinned
  crossover leg. **Behavioral** for every T1-X leg, realized and forward.

*Invalidated:* every cached bundle produced in **forecast mode**
(``mode="forecast"``, including ``hindcast=True`` capacity-hindcast and T1-X
crossover legs) at a commit before the Wave-1 merges — any solve year, not only
2026+, because FR-8 reaches a crossover's realized 2023–2025 legs too. Purge or
move aside the per-ISO cache roots and the contents of every forecast
``--out-dir`` cache (the roots hold tracked ``.gitignore`` keep-files — clear
their contents, not the directories)::

    rm -rf results/{ERCOT,CAISO,PJM,MISO,NYISO,NEISO}
    for d in full-horizon ff-t1f-baseline ffr1a d9-ab probe-* verify-*; do
        [ -d "results/$d" ] && find "results/$d" -mindepth 1 ! -name .gitignore -delete
    done

Run it before any forecast solve on a checkout that predates 2026-08-02; a
container cloned fresh after that date has nothing to purge (verified empty at
the close: zero ``year_*.parquet`` anywhere under ``results/``).

*NOT invalidated:* **backcast** caches and every keeper bundle. FR-7/FR-8 are
mode-gated and FR-1/FR-2 run only under forecast-mode capacity evolution; the
six current keepers' input surfaces and cache keys were attested unchanged
across all three ``scenarios.py``-touching Wave-1 merges (§W1-X close doc §1).
"""

from contextlib import contextmanager
from pathlib import Path

import numpy as np

from market_sim.config import paths
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.dispatch import DispatchResult
from market_sim.results.outputs import FleetContext, read_fleet_context

# Root directory under which all cached results are stored. Sourced from the
# central path registry (:data:`market_sim.config.paths.RESULTS_ROOT`,
# ``DATA_ROOT/results``) rather than a cwd-relative ``Path("results")`` so the
# results tree does not silently fork when the process runs outside the repo
# root. Kept as a mutable module attribute: tests (and a handful of scripts)
# redirect it to a temporary directory — prefer the :func:`cache_root`
# contextmanager over hand-rolling a save/set/restore dance.
CACHE_ROOT = paths.RESULTS_ROOT

_CONFIG_FILENAME = "config.yaml"


@contextmanager
def cache_root(root: "Path | str"):
    """Temporarily redirect :data:`CACHE_ROOT` to ``root``, restoring on exit.

    Absorbs the save/set/restore dance repeated across the result-export and
    reference-solve scripts (``export_results``, ``run_full_horizon``,
    ``ff_readiness_battery``, ...): ``prior = cache.CACHE_ROOT; cache.CACHE_ROOT
    = tmp; try: ...; finally: cache.CACHE_ROOT = prior``. The restore runs even
    if the body raises, so a redirected cache never leaks into a later solve in
    the same process (which would read/write the wrong tree).

    Args:
        root: The directory to point the cache at for the duration of the block.

    Yields:
        The resolved :class:`~pathlib.Path` the cache now points at.
    """
    global CACHE_ROOT
    prior = CACHE_ROOT
    CACHE_ROOT = Path(root)
    try:
        yield CACHE_ROOT
    finally:
        CACHE_ROOT = prior


# Cache keys whose on-disk bundles are CONTAMINATED and may never be served
# (owner decision D-11 condition 2, ``docs/handoffs/ffr-owner-sitting-2026-08-02.md``
# Addendum L.2; discharged by FFR-3U, ``docs/handoffs/ffr-3u-bridge-seam-2026-08-04.md``).
#
# Why a denylist and not an epoch bump: the epoch ledger above is human-read and
# never auto-invalidates, and the FFR-3U seam fix deliberately moves NO cache key
# (it is a guard fix, not a mechanism — every key is byte-identical before and
# after). So the very config that solved 2022 still hashes to these keys: without
# a mechanical refusal, a later run would silently CACHE-HIT the contaminated
# 2022 solve and inherit the rule-22 breach with no banner at all.
#
# The refusal is scoped to what protects the tier: a bundle DIRECTORY existing at
# one of these keys is a hard error, naming the key and telling the operator to
# delete it. An absent directory is fine — a re-probe on a clean tree re-solves
# normally, and under the fixed seam bridges 2022. This closes the reuse channel
# without blocking the legitimate re-probe (a later lane).
CONTAMINATED_CACHE_KEYS: dict[str, str] = {
    "b99600bceb8cb6b8": (
        "FFR-3Q arm A (ERCOT T1-FF base 2021, retirement_rule=pipeline) — SOLVED "
        "2022, a validation-tier holdout year, under an active holdout freeze"
    ),
    "5c352508039513da": (
        "FFR-3Q arm B (ERCOT T1-FF base 2021, retirement_rule=legacy) — SOLVED "
        "2022, a validation-tier holdout year, under an active holdout freeze"
    ),
}


def assert_cache_key_uncontaminated(iso: str, cache_key: str) -> None:
    """Refuse a cache key whose bundle is quarantined under rule 22.

    Called from :func:`get_cache_path`, the single seam every cache read and
    write routes through, so no reader can bypass it. A no-op unless the key is
    in :data:`CONTAMINATED_CACHE_KEYS` **and** a directory for it exists.

    Raises:
        RuntimeError: A bundle directory exists at a contaminated key.
    """
    reason = CONTAMINATED_CACHE_KEYS.get(cache_key)
    if reason is None:
        return
    bundle = CACHE_ROOT / iso / cache_key
    if not bundle.exists():
        return
    raise RuntimeError(
        f"cache key {cache_key} is QUARANTINED and its bundle must not be read "
        f"or extended: {reason}. Owner decision D-11 condition 2 requires this "
        f"key to be uncacheable. Delete {bundle} and re-solve; the FFR-3U seam "
        "fix makes the same window bridge 2022 rather than solve it."
    )


def get_cache_path(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> Path:
    """Return the Parquet path for one cached scenario-year.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag. ``None`` is the final-result file
            ``year_{year}.parquet``; ``"p1"`` is the Pass 1 dataset
            ``year_{year}_p1.parquet`` kept when the commitment screen runs.

    Returns:
        Path ``results/{iso}/{cache_key}/year_{year}[_{pass_label}].parquet``.
    """
    assert_cache_key_uncontaminated(iso, cache_key)
    suffix = "" if pass_label is None else f"_{pass_label}"
    return CACHE_ROOT / iso / cache_key / f"year_{year}{suffix}.parquet"


def get_config_path(iso: str, cache_key: str, year: int) -> Path:
    """Return the ``config.yaml`` path sitting beside a cached scenario."""
    return get_cache_path(iso, cache_key, year).parent / _CONFIG_FILENAME


def is_cached(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> bool:
    """Return whether a cached result exists for this scenario-year.

    ``pass_label`` selects which solve pass to check; ``None`` is the
    final-result file (see :func:`get_cache_path`).
    """
    return get_cache_path(iso, cache_key, year, pass_label).exists()


def save_result(
    result: DispatchResult,
    config: ScenarioConfig,
    iso: str,
    year: int,
    context: FleetContext | None = None,
    pass_label: str | None = None,
    demand: "np.ndarray | None" = None,
) -> Path:
    """Persist a dispatch result and its config to the cache.

    Writes the result as Parquet and, if not already present, the full
    config as ``config.yaml`` in the same directory.

    Args:
        result: The solved dispatch result to cache.
        config: The scenario config that produced ``result``; its
            ``cache_key`` selects the cache directory.
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Weather/simulation year.
        context: Optional fleet context stored in the Parquet metadata so
            the result can be aggregated without re-deriving the fleet.
        pass_label: Solve-pass tag (see :func:`get_cache_path`). ``None``
            writes the final-result file; ``"p1"`` writes the Pass 1
            dataset.
        demand: Optional ``(n_zones, T)`` served demand, stored so the
            forecast-invariant checker can verify the energy balance.

    Returns:
        The Parquet path written.
    """
    cache_key = config.cache_key()
    path = get_cache_path(iso, cache_key, year, pass_label)
    path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(path, context=context, demand=demand)
    config.to_yaml_full(path.parent / _CONFIG_FILENAME)
    return path


def load_result(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> DispatchResult:
    """Load a cached dispatch result.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag (see :func:`get_cache_path`). ``None``
            loads the final-result file; ``"p1"`` loads the Pass 1 dataset.

    Returns:
        The cached :class:`DispatchResult`.

    Raises:
        FileNotFoundError: When no cached result exists for this scenario-year.
    """
    path = get_cache_path(iso, cache_key, year, pass_label)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached result for iso={iso} cache_key={cache_key} "
            f"year={year} pass={pass_label} (expected {path})"
        )
    return DispatchResult.from_parquet(path)


def load_fleet_context(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> FleetContext:
    """Load the fleet context stored alongside a cached dispatch result.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag (see :func:`get_cache_path`).

    Returns:
        The cached :class:`~market_sim.results.outputs.FleetContext`.

    Raises:
        FileNotFoundError: When no cached result exists for this scenario-year.
        ValueError: When the cached result carries no fleet context.
    """
    path = get_cache_path(iso, cache_key, year, pass_label)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached result for iso={iso} cache_key={cache_key} "
            f"year={year} (expected {path})"
        )
    return read_fleet_context(path)
