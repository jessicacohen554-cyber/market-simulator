# FINDING capx-D16 — the armed-interface mc=0 seam guard: fail closed on a no-shape solve year

**Session.** capx-d16-seam-guard (capacity-expansion / Forecast Finalization track), chartered
at director refresh #19 to execute the director's mechanism decision on S-123 routed item 5
(`docs/handoffs/FINDING-capx-s123-miso-adequacy-2026-08-30.md` §5/§7.5: the armed-interface
mc=0 seam degradation). Branch `claude/capx-d16-seam-guard-i9rnne`, fresh off `origin/main` at
`3960244`. 2026-08-30. **Zero-solve:** yes — no LP built or solved; every verification is an
injector-level call or a test. No out-of-training year solved/scored/registered; freeze posture
untouched. **Rule 28:** no mechanism proposed, tested or armed; no `ScenarioConfig` field; no
matrix row or cell (the director's ruling verbatim: *a guard that refuses is not a mechanism*);
`scripts/check_mechanism_matrix.py` green at delivery.

---

## 0. Headline

**The free-seam hole is closed, fail-closed.** `inject_reference_price_mc`
(`src/market_sim/model/interchange/import_nodes.py`) now raises a hard `ValueError` — naming
the ISO, the year, every unpriced seam with its BA/proxy, the band-row count, the free
import/export MW at stake, and the S-123 §5 citation — whenever the fleet carries
reference-price band rows that neither the flow-responsive per-band path nor the flat
aggregate could price (i.e. an armed reference interface whose solve year resolves NO seam
load shape: every year ≥ 2026 at HEAD). Before this change the function returned `False` and
the rows kept the mc = 0 placeholder from `build_reference_price_node` with LIVE bounds — up
to ~14.3 GW of free import capacity (and free export sinks) for MISO's three registered seams,
silently, in any future "arm the reference interface in forecast" experiment. The deliberate
alternative NOT built, per the director's decision: a flat gas × HR fallback price — that
would synthesize a price input needing its own identification and matrix row (rules 5
`[R-NO-MAGIC]`, 21 `[R-FROZEN-DERIVE]`-adjacent identification duty, 24 `[R-REGISTRY]`, 28
`[R-MECH-MATRIX]`); if a future lane wants it, that is its own charter.

Every reachable default/keeper path is untouched, proven at the byte level (§3): the guard
fires **only** where the LP would previously have been built on free seams.

## 1. The raise site

**Inside `inject_reference_price_mc`, at the end of its row loop** — not at the armed call
sites. The injector is the one function that knows, row by row, which seam bands were matched
by unit-id mark yet left on the placeholder; both armed callers go through it (the generic
registry step `apply_reference_price_seam_injections`, gated
`config.reference_price_interface` ∧ `iso ∈ INTERFACE_NEIGHBORS` ∧ `iso ≠ CAISO`, and CAISO's
`apply_caiso_seam_injections` under `caiso_reference_price_seam`), so one site covers both
plus any future caller. Mechanics:

* The loop's former silent fall-through (`priced is None` **and** `aggregate is None` →
  `continue`, leaving mc = 0) now records the row under its seam name
  (`unpriced_rows`); after the loop, a non-empty record raises. Rows built via
  `extra_neighbors` (the Manitoba seam) are matched by the same unit-id convention and are
  covered; a name absent from `INTERFACE_NEIGHBORS[iso]` is reported as such.
* **The documented benign `False` is preserved**: a fleet with NO reference-price rows (a
  non-reference run) still returns `False` quietly and touches nothing —
  `test_inject_noop_without_node` passes unchanged, and the new
  `test_no_node_fleet_still_returns_false_quietly` pins it in a no-shape year.
* The condition "any matched row left unpriced" is equivalent at HEAD to "nothing priced":
  whenever ANY neighbor resolves a shape, `InterfacePrices.aggregate()` is non-None and
  catches every row as the flat fallback. Tracking per-row is the tighter invariant and stays
  correct if the aggregate semantics ever change.
* No new tunable, no config read, no constant: the guard consumes only what the function
  already computes. Docstrings updated (`Raises:` on the injector; a fail-closed note on the
  registry step), citation comment at the raise site.

The refusal pattern follows `scripts/lib/holdout_policy.py`'s precedent (fail closed to the
strictest interpretation; the loud error is the feature) and the registry's existing
`ValueError` convention (`apply_interchange_injections`' net-load check).

## 2. Unreachability re-verification — the three S-123 lanes, re-measured at HEAD

S-123 §5 adjudicated the defect unreachable today on three lanes. Re-verified this session,
each against the current tree, plus a fourth measurement widening lane 1 to every preparable
backcast year:

1. **Backcast keeper years 2023–2025 (ladder-armed).** The measured seam ladders displace the
   band prices at overlay step 4 (`_inject_seam_ladder` via
   `inject_{miso,pjm}_seam_ladder_prices`, called only from
   `scripts/run_calibration.py::_backcast_measured_interchange_prices`), which runs AFTER the
   injector (registry step 1). The guard sits upstream — but never fires there, because step 1
   itself prices every row in those years (see 4 below). **Byte-identity proof:** sha256 of
   the full post-injection + post-ladder `mc` matrix, un-edited tree vs edited tree, for
   MISO × {2023, 2024, 2025} and PJM × {2023, 2024, 2025}: all six hashes identical
   (e.g. MISO 2023 `000e01c2…`, PJM 2025 `32712d73…`).
2. **Default forecast configs.** `ScenarioConfig.reference_price_interface` defaults `False`;
   the MISO default-arm lives ONLY in `resolve_reference_price_interface`
   (`config/constants.py`), whose only callers are the two backcast CLIs
   (`run_calibration_full.py:11957`, `run_calibration.py:6486`) — the forecast path
   (`runner.py` → `build_interchange_spec`, `spec.py:1898` `use_ref`) reads the config field
   directly. Seam nodes are never built; the registry step short-circuits at its gate. Pinned
   by the new `test_default_off_forecast_step_is_a_noop` (default config + seam rows present +
   no-shape year ⇒ mc byte-untouched, no raise).
3. **An armed-interface forecast solve year ≥ 2026 — the defect lane, now the refusal lane.**
   Measured per-BA extract coverage (`data/raw/eia-930-hourly/`, the `_neighbor_load` source):
   MISO/PJM/CISO end at H1-2026 (4,343–4,344 rows), NYIS 3,912, SWPP 3,359, SOCO ends 2025 —
   no BA serves a full calendar year ≥ 2026, and `_eia_hourly_frame_filled` is year-based
   (needs ≥ 8,688 rows), so no 2026+ request resolves at any horizon length. Where
   `inject_reference_price_mc` previously returned `False` over live mc=0 rows, it now raises:
   verified directly for MISO 2035 (48 rows / 3 seams / 14,300 MW free import named) and
   CAISO 2035 (32 rows / 2 corridors).

**The widened lane-1 measurement (why no ladder-exemption machinery is needed):** every seam
BA extract fully covers 2018–2025 (SOCO 2023–2025, but SOCO is only ever a proxy — PJM's
MISO/NYIS and MISO's PJM/SWPP primaries cover 2018–2025), so at least one neighbor resolves —
and the aggregate therefore prices every band row — in **every** backcast year any armed ISO
can reach or prepare: training 2023–2025, the validation years 2020–2022 (PJM holds
`complete`; guard verified silent, `applied=True`, zero unpriced rows, for PJM/MISO/CAISO ×
2019–2022), and the prepared PJM ladder years 2019/2021/2022. The refusal is confined to
years ≥ 2026 and pre-extract years ≤ 2017 (locked-test tier, unsolvable by the rule-22 gates
anyway). One honest consequence worth naming: a someday-authorized **H1-2026 crossover
backcast leg** (locked-test tier, currently frozen) arms MISO's interface via the CLI default
and would previously have solved silently on free seams — it now refuses loudly until a
load-shape source serving 2026 is intaken (or the seam is priced by a measured overlay
covering it). That is the defect class closed, not a new restriction: the message names
exactly what is missing.

## 3. Tests

* **New: `TestReferencePriceFailClosed`** (`tests/unit/data/test_neighbor_price.py`, the
  injector's existing test home), five tests, hermetic where they must always run (loader
  monkeypatched empty via the file's `_FakeFrames` idiom — no data files needed, immune to
  future extract intakes):
  * `test_armed_no_shape_year_raises` — trivial case first (24 h clock, one ordinary unit +
    the seam node): armed MISO + no shape ⇒ `ValueError` naming `MISO 2035`, all three seams,
    `S-123`, and the summed 14,300 MW free-import capability.
  * `test_extra_neighbor_rows_are_guarded_too` — Manitoba (`extra_neighbors`) bands covered.
  * `test_no_node_fleet_still_returns_false_quietly` — the benign `False` contract kept.
  * `test_resolved_year_never_raises_and_prices_every_row` — integration (real extracts,
    skip-if-absent): MISO 2023 prices all 48 bands, ordinary row untouched.
  * `test_default_off_forecast_step_is_a_noop` — lane 2 pinned at the registry step.
* **Seam-adjacent suite green:** 214 passed across `test_transmission.py`,
  `test_transmission_facade.py`, `test_interchange_parity.py`, the PJM/MISO seam-ladder and
  flow-limit files, `test_miso_manitoba_seam.py`, `test_reference_price_firm_export.py`;
  `test_neighbor_price.py` 32/32.
* **Fast lane** (`pytest -n auto -m "not slow and not integration and not fulldata"`): 7,284
  passed, 76 failed — **all 76 reproduce IDENTICALLY on the un-edited tree** (stash → rerun →
  failure-set diff empty). They are other-lane/environment drift, e.g.
  `test_constants_facade.py`'s `STORAGE_TECH_AVAILABLE_YEAR` facade re-export gap, CAISO
  clean-tranche and curation files sensitive to this checkout's hydration; none touch the
  seam path.
* Lint/format: `ruff check` + `ruff format --check` clean on both touched files.

## 4. Governance

* **Rule 22:** zero solves; the only 2026+ activity is a unit-level injector call that now
  refuses; no backcast surface beyond the untouched-path verification; freeze/tier state
  unread and unchanged.
* **Rules 5/21/24/28:** no fallback synthesized, no tunable added, no registry channel, no
  matrix edit; `check_mechanism_matrix.py` green (194 field + 49 row + 151 path anchors).
* **Rule 27:** Fable session; local Edit + `git push` of exact on-disk bytes; post-push blob
  verification recorded for the ≥300-line files (`import_nodes.py`,
  `test_neighbor_price.py`).
* **Routed onward (unchanged from S-123 §7):** the TVA extract intake + South-seam re-point
  (item 4) remains the accurate fix for the seam the guard now protects; the guard makes its
  precondition ("arms the interface in a year the ladder does not cover") loudly visible
  instead of silently degraded.
