# DIAGNOSIS — ERCOT-132 leg A: the ramp-envelope mechanism had TWO defects — it was UNREACHABLE (its `ScenarioConfig` declaration was never written) and its MW were on the wrong basis. Both repaired; no keeper touched, no solve chartered.

**Date** 2026-07-28 · **ISO** cross-ISO (the fix is ISO-agnostic; CAISO is the
only ISO with a live loader-path artifact) · **Lane** ercot132-ramp ·
**Keeper** `2026-07-28-ercot129-conditional-coal-min` — **untouched** ·
**Chartered by** `DIAGNOSIS-ercot127` §1, whose closing paragraph routed the
basis defect ·
**Method** code trace + committed artifacts + unit tests. **No LP was built. No
year was solved. No run was registered. No keeper file was touched.**

**This lane repairs the MECHANISM's correctness. It does NOT reopen the claim
that ramp bounds fix the coal dispatch band** — ERCOT-127 §1 measured that
inert and it stays closed.

---

## 0. Both defects verified this session, not assumed

| claim | verification |
|---|---|
| `ramp_limits` is not a `ScenarioConfig` field | `hasattr(ScenarioConfig(), "ramp_limits")` → **False** |
| arming it crashes | `ScenarioConfig().with_overrides(ramp_limits=True)` → **`TypeError: unexpected keyword argument 'ramp_limits'`**, i.e. `run_calibration_full.py:4046` raises the moment `--ramp-limits` is passed |
| consumers silently see False | `pipeline/year.py:190`, `runner.py:1594`, `run_calibration.py:4146` all read `getattr(config, "ramp_limits", False)` |
| it is armed in ZERO runs | no committed `run_config.json` (104 on disk) or registry sidecar (78) contains a `ramp_limits` key at all |
| the derive measures GROSS | `derive_campd_ramp_envelopes.py` docstring: "max observed 1-h increase in summed **gross** load" |
| the loader used it as NET | `build_ramp_groups` docstring: measured plant row "(MW, **used directly**)" |
| default cache key | `603c2498bf71d21d` before **and** after this session |

## 1. Defect 1 — the declaration was never written

Everything around the field exists: the design doc specifies it
(`docs/ramp-locational-design-2026-07.md` §245, verbatim
`ScenarioConfig.ramp_limits: bool = False`), it has a `TIER_TAGS` entry
(`scenarios.py:9323`, tier 3), a CLI flag
(`run_calibration_full.py:2996/4045-4046/9485/10555`), LP row builders
(`model/lp/rows.py:570-620`, `1308-1325`), a loader
(`data/fleet/campd_bins.py`), a frozen derive, a committed CAISO artifact, and a
row in `docs/parameter-citations.md:1172`. **The one line that declares it is
absent.**

**It was never there** — `git log -S "ramp_limits: bool" -- src/market_sim/config/scenarios.py`
returns **no commits**. This is not a truncation; the line was simply never
written, and everything downstream assumed it had been.

The evidence is visible in the file: the field's **comment block survives**
(`scenarios.py:1764-1778`, "envelopes in the dispatch LP
(model/dispatch._build_ramp_rows) …") but begins **mid-sentence**, orphaned onto
the *next* field, `local_capacity_constraints` — its sibling from the same
design doc, which **is** declared. `parameter-citations.md` even records the
intended trailing comment, "GATED, default-OFF plant-group hourly ramp".

**Resolution: DECLARE, not remove.** Removing the flag would delete a fully
built, zero-fitted-DOF measured-physical mechanism on account of a one-line
clerical omission, while its co-designed sibling stays live. The mechanism has
never been fairly tested anywhere except CAISO, and it cannot be, until it can
be turned on.

* `ramp_limits: bool = False`, restored at its documented position.
* Registered in `_CACHE_KEY_OPTIONAL_FIELDS`, so the **default key stays
  `603c2498bf71d21d`** (test-pinned, verified) while an armed run gets a
  distinct key (`56869e8b9896fd78`).
* The three `getattr(config, "ramp_limits", False)` call sites become
  `config.ramp_limits`. **This is part of the fix, not tidying**: the defensive
  fallback is precisely what converted a missing field into a silent
  no-op — the mechanism reported itself off instead of failing loudly. A future
  omission now raises.

**Consequence to carry forward:** no run has ever had `ramp_limits` armed, so
any prior claim of an "armed" ERCOT ramp arm should be re-read as an
unarmed run. The CAISO A/B (§3) predates none of this — it is unaffected,
because it went through `run_calibration.py`'s own path with the same
`getattr` … see §3.

## 2. Defect 2 — gross MW fed into net columns

The derive measures CAMPD `grossLoad` deltas; the LP's `P` columns are **net**.
The loader passed the published MW straight through, so every ISO's ramp rows
were loose by the station-service fraction.

**The conversion belongs on the LOADER side, and is applied there only**
(putting it in both would double-count). Three reasons, recorded in the code:

1. The artifact is a **measurement record** of what CAMPD reports, which is
   gross. A derive that silently wrote net would misrepresent its own source,
   and rule 23 `[R-FROZEN-DERIVE]` re-derives only on a **source** change — a
   representation fix is not one. **The committed CAISO artifact is therefore
   byte-identical** (md5 `33c4e6b9…` before and after; `git status` clean).
2. The basis change happens exactly where measured plant MW meet the model's net
   columns — the `build_ramp_groups` seam.
3. **Only the `basis == "plant"` rows carry MW.** The `class_fraction` fallback
   rows are **already basis-neutral by construction**: the derive forms them as
   `median(gross_delta / gross_pmax_obs)` — a gross-over-gross ratio — and the
   loader applies them as `frac × net pmax`, which yields a net delta with no
   conversion at all. A derive-side fix would have had to convert one row family
   and not the other, i.e. write a **mixed-basis file**. A regression test pins
   this asymmetry.

**The factor is per-plant and measured** (rule 14 `[R-ACCURATE]`): the pooled
EIA-923-net / CAMPD-gross ratio from `parasitic_load_factors.parquet`
(`campd.compute_parasitic_factors`). Where a plant has no reconciliation, the
**cited class default** keyed by the group's *capacity-dominant model
`plant_group`* (`campd.DEFAULT_PARASITIC_LOAD_PCT`, EPRI/EIA station-service
typicals) — the identical measured-else-class-default resolution the parasitic
derive itself applies, so the two paths cannot disagree. The `plant_group` grain
is deliberately finer than the artifact's CC/CT/ST bucket, which collapses COAL
(7.0 %) and ST_GAS (5.0 %) into one family.

**It is NOT ERCOT's coal 0.8972/0.9051/0.9069 factor**, which is a single-class
*annual-energy* ratio and has no business rebasing a per-plant cross-class ramp
envelope.

### 2.1 The ~10 % figure was itself the wrong instrument — the real number is ~2.5 %

ERCOT-127 §1 estimated the rows were "~10 % looser". That estimate came from the
coal energy ratio. Measured properly, per plant and per class, on CAISO — **the
only ISO with a loader-path artifact** (89 rows, 30 of them `basis == "plant"`):

| bucket | rows | ramp_up gross MW | factor | ramp_up net MW |
|---|---|---|---|---|
| CC | 23 | 7,369 | 0.975 | 7,185 |
| CT | 5 | 601 | 0.990 | 595 |
| ST | 2 | 476 | 0.950 | 452 |
| **total** | **30** | **8,446** | | **8,232** (**−2.53 %**) |

(down-envelope −2.51 %). None of CAISO's 30 ramp plants carry a measured
parasitic factor — the committed artifact is ERCOT-scoped (463 plants, **zero**
overlap with CAISO's plant codes) — so all three take the cited class default.
The defect was real; its magnitude was **overstated ~4×** for the one ISO where
it is live, because CAISO's ramp fleet is CC-dominated and CC station service is
2.5 %, not coal's 7 %.

**Open, routed not fixed:** extending `parasitic_load_factors.parquet` beyond
ERCOT would replace those class defaults with measured per-plant factors. That
is a data-intake lane, not this one.

## 3. Scope held

* **No solve is chartered and none was run.** `ramp_limits` is armed in zero
  keepers (§0), so this is latent-correctness with no live blast radius. An
  arming A/B would be a **separate bundle and a separate decision**; it is not
  folded in here.
* **The ERCOT artifact is NOT promoted.** It stays at the probe path
  (`data/raw/_validation-source/ercot127_campd_ramp_envelopes_ERCOT.csv`) so
  `ramp_limits` cannot arm on ERCOT by accident. Promoting it to
  `data/raw/_processed-legacy/campd_ramp_envelopes_ERCOT.csv` is the owner's
  call and its own lane.
* **Rule 23 cleared explicitly.** The derive was **not** re-run and its output is
  byte-identical. The change is a units/basis **correctness** fix on the
  consumer side. **No residual was consulted, and no number moved because a
  residual moved.**
* **Rule 26 duty (c)** discharged: `ramp_envelopes` row added to the mechanism
  matrix in this PR — ERCOT `R` (ERCOT-127 §1, measured inert on the coal band),
  CAISO `I`, the rest `U`. `scripts/check_mechanism_matrix.py` passes.

### 3.1 One correction to the charter's expected cell values

The charter specified "`R` for ERCOT, `U` elsewhere". **CAISO is not untested**:
`results/calibration/_archive/FINDING-ramp-lcr-caiso-2026-07.md` records a full
A/B (`ramp_limits` + `local_capacity_constraints` on, drags off), re-verified
post-P2-archival on 2026-07-07 (`caiso-ct-drag-d8-closure-2026-07.md` §7) —
near-inert on evening CT (+2 MW), still failing criterion (i), with the
suppressor identified as the P1-native RA physical bridge rather than ramp.
Recording CAISO as `U` would have invited a re-test the DO-NOT-REDO discipline
exists to prevent, so its cell is **`I`** with that citation.

## 4. Tests (the deliverable's proof)

`tests/unit/data/test_ramp_envelope_basis.py`, 8 tests, all passing:

* **Reachability** — the field is declared, defaults off, **arms** (the thing
  that was broken), the default cache key is byte-stable at
  `603c2498bf71d21d`, and an armed key is distinct.
* **Basis** — a measured plant row rebases by its measured factor; a plant with
  no factor falls back to the cited class default; the rebasis **tightens,
  never loosens**; and `class_fraction` rows are **not** rebased (the
  double-count guard).

Regression: `tests/regression/test_persisted_identity.py` 11/11,
`tests/unit/data/test_ramp_limits.py` 10/10, `tests/unit/config/test_flag_registry.py`
12/12, `tests/unit/data/` 1,105 passed / 14 skipped.
`scripts/run_calibration_full.py --help` parses.
