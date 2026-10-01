# RESULT — SPP-49 (2026-09-19): the benchmark-membership defect, repaired and gated

**Base:** `8cb4d9c9` (the SPP-48 PROMOTION branch, checked and found **not** an ancestor of
`origin/main` at `995f7b7e`, so it is this lane's base as the handoff directed).
**Lane branch:** `claude/spp-benchmark-membership-defect-4yqm2f`, commit `3f64471e`, **pushed**.
**Method and full phase-0 measurement:** `PRECOMMIT-spp-49-benchmark-membership-2026-09-19.md`.
**Keeper:** `2026-09-16-spp-42-commitment-feasibility` — **UNTOUCHED.** Rung
`2026-09-19-spp-48-midvintage-exit` — **UNTOUCHED.**
**No LP was run** (rule 32(a)). Nothing armed, nothing registered, no keeper moved.

---

## 0. Headline

1. **The defect is one line, now pinned.** `zone_assignment._EIA860_PLANT_PATH` is a module-level
   constant bound **at import** to the canonical `EIA_860_DIR`, never to `active_eia860_dir()`.
   The benchmark's EIA-860 supplement therefore *cannot* follow `eia860_vintage_tracks_solve_year`
   — no config can redirect it.
2. **It reaches every region, and it is two defects, not one.** PJM is the largest by an order of
   magnitude — **857 plants, 8.8 TWh absent from its 2025 ACTUAL, a live keeper year** — because
   **PJM is not in `_EIA860_SUPPLEMENT_ISOS` at all.**
3. **The repair is built, gated default-off, and byte-identical off** — proven, not asserted: the
   flag-off rebuild reproduces SPP-48's HEAD hash `eia923-78357736757d` exactly.
4. **The obvious variant was refused on measurement.** A year-matched REPLACE deletes real metered
   generation in **7 of 9** regions (SOCO 2024 −7,275.9 GWh). Rules 13/14.
5. **SPP needs ZERO LP.** The arm moves no LP input, so its scored result is the committed dispatch
   against a rebuilt benchmark. **A promotion here costs no re-solves at all.**
6. **And it makes C1 WORSE** — which is the point, not a problem. See §2.

---

## 1. What was built

`ScenarioConfig.benchmark_membership_vintage_union` (default **off**). For benchmark year `y` the
ISO plant set becomes `build_zone_lookup(iso)` **UNION** the plants BA-coded to the ISO in the
EIA-860 vintage covering `y`, holding last to canonical. Driven by the run's **year**, not by any
config vintage, so the benchmark stays a pure function of `(iso, year)` and the reference data.

Threaded through the one `_iso_plant_ids` seam that bench, injection, class-shares and the
completeness probe all read, so the two sides cannot split basis (rule 19). Recovered by
`rebuild_benchmark` from `meta.json` then `run_config.json`, mirroring `mustrun_chp_btm_holdout`.

**Additive by construction** — it never removes a plant, so it can only add real metered
generation, and each plant contributes exactly what EIA-923 reports for that year. **No double
count** with the fleet-keyed CAMPD backfill: its firing test skips a plant EIA-923 already reports
at or above 50,000 MWh, and Oklaunion clears it (2,601,923 MWh in 2019; 1,103,627 in 2020).

---

## 2. What it does to the scores — reported at full magnitude

Measured via `--rebuild-benchmark` on the rung bundle's **own** settings (handoff trap (c)), with
the model side taken from the committed `hourly/class_hourly_<year>.parquet`. **The model is
unchanged**, so every movement below is the *actual* moving.

| yr | class | model | actual OFF | actual ON | miss OFF | miss ON | |
|---|---|---|---|---|---|---|---|
| 2019 | **COAL_PRB** | 70.4818 | 76.8210 | 79.4168 | **−6.3392** | **−8.9351** | **WORSE** |
| 2019 | CT_PEAKER | 14.1337 | 12.4706 | 12.4958 | +1.6632 | +1.6379 | better |
| 2019 | wind | 85.2609 | 71.9845 | 72.0257 | +13.2764 | +13.2351 | better |
| 2019 | oil | 0.0002 | 0.2038 | 0.2098 | −0.2036 | −0.2096 | WORSE |
| 2020 | **COAL_PRB** | 57.0452 | 65.8489 | 66.9496 | **−8.8037** | **−9.9044** | **WORSE** |
| 2020 | CT_PEAKER | 16.0230 | 9.6551 | 9.6614 | +6.3680 | +6.3616 | better |
| 2020 | wind | 90.7698 | 79.2136 | 79.2309 | +11.5563 | +11.5389 | better |
| 2020 | oil | 0.0000 | 0.2018 | 0.2048 | −0.2018 | −0.2048 | WORSE |

2021 and 2022 are unchanged at class grain (their added rows carry ~0 MWh).

**The load-bearing `COAL_PRB` row degrades in both live years.** Against the *committed* frame
(67.0581, what the registered run is actually scored on) 2020 reads −10.0129 → **−9.9044**, a
marginal improvement — but that is entirely the CAMPD→EIA-923 basis shift of §3, not a dispatch
gain. On a like-for-like HEAD basis, both years get worse.

**This is the expected outcome and it is not a reason to revert.** Rule 1 `[R-STRUCT]`: a real
market behaviour stays in even when it makes the fit worse, and the root cause gets fixed instead.
Rule 14 `[R-ACCURATE]`: *"If swapping a hand estimate for real data makes the backcast worse, that
is a signal that something else in the model is miscalibrated."*

**What the worse number says, diagnostically:** the model is **8.9 TWh short of SPP's 2019 PRB
coal** once the real metered generation is in the actual. That is the same object SPP-47 filed as
**"Object A" — the coal↔CC elasticity**, the largest single C1 residual (r = +0.885 vs gas price),
for which the handoff records that no structural successor has been found and that it is
explicitly **not** closeable through the rule-1 authorized offer-curve channel. This lane makes
that residual *bigger and more honest*; it does not close it.

**Determination is unchanged** either way: `NOT-YET`, failing set `{C1, C3a, C3b, C4}`.

---

## 3. The one number that goes down, named rather than buried

The committed 2020 frame carries plant 127 at **1,209,201 MWh**; the repaired frame carries
**1,100,658** (`COAL_PRB`) + 2,969 (`oil`). This is a **basis normalisation, not a deletion**: the
committed figure was **CAMPD CEMS net** booked by the fleet-keyed backfill, the repaired one is the
plant's **own EIA-923 survey value**. Both are real measurements; preferring the survey where it
reports adequately, and reserving CAMPD for genuine under-reporting, **is** the benchmark's
documented convention — which this plant follows for the first time, because it is finally a
member. Stated so the owner can weigh it; not averaged away.

---

## 4. Blast radius, and why the gate is default-off

Measured at **row** grain (a zero-MWh row still changes the frame's bytes):

| ISO | inert years | live years |
|---|---|---|
| **SPP** | **2023, 2024, 2025** | 2019 (11 rows / 2,668,406 MWh) · 2020 (8 / 1,127,316) · 2021 (2 / 0) · 2022 (3 / 275) |
| CAISO | 2023–2025 | 2022 (12 / 148,026) |
| ERCOT | 2023–2025 | 2021 (3 / 1,538) · 2022 (1 / 0) |
| MISO | 2024, 2025 | 2020 (77 / 6,756,889) · 2021 (37 / 3,243,948) · 2022 (20 / 3,030,903) · 2023 (1 / 0) |
| NEISO | 2024, 2025 | 2020 (38 / 358,009) · 2021 (34 / 326,799) · 2022 (20 / 142,990) · 2023 (1 / 0) |
| NYISO | 2024, 2025 | 2022 (6 / 134,213) · 2023 (1 / 0) |
| NWPP | 2023–2025 | none |
| SOCO | 2025 | 2023 (7 / 0) · 2024 (2 / 403) |
| **PJM** | **none** | **every year**, incl. 2024 (138 / 2,452,964) and **2025 (47 / 8,804,034)** |

The handoff's item 4 asked whether more than SPP moves. **It does — so the gate is default-off**
(rule 25 `[R-ISO-SCOPE]`; `zone_assignment.py` and `run_calibration_full.py` are shared seams).

**SPP's keeper years are INERT**, so arming SPP cannot move keeper 12. A test pins exactly that
and fails loudly if it ever stops being true.

### 4.1 PJM is a separate, larger object — reported, not repaired

PJM's membership is **eGRID-2023 only**, with no EIA-860 supplement of any kind. 1,727 plants in
the lookup against 2,584 in the EIA-860 PJM-BA union. **8,991 GWh is absent from the 2025 ACTUAL of
`2026-09-11-pjm-d4-4-gasoutage`'s own scored span.** The right repair there may simply be adding
PJM to `_EIA860_SUPPLEMENT_ISOS` — a different object with a different blast radius, and PJM's lane
to decide. Recorded so it is not rediscovered.

---

## 5. A second defect found on the way, filed not fixed

`rebuild_benchmark` builds `group_by_code` from `iso_config` **defaults**, so **it does not
reproduce the solve path's own benchmark for a config that changes the fleet.** That is why the
committed frame carries plant 127 (the solving fleet had it) while both legs of SPP-48 §A.1's
two-leg rebuild did not. SPP-48's "the benchmark is invariant to the fleet repair" is therefore
true **of `rebuild_benchmark`**, and true only because the rebuild ignores the bundle's own fleet
config — on the solve path the benchmark is *not* invariant. Different seam; fixing it here would
widen the change beyond what the census covers.

Also visible: 2021/2022 `ST_GAS` differ from the committed frame by +0.2591/+0.2527 TWh with
**zero** flag effect — pre-existing HEAD-vs-committed drift this lane neither caused nor touches.

---

## 6. Tests and governance

* **New:** `tests/unit/data/test_benchmark_membership_vintage_union.py`, 9 tests, all pass —
  byte-identity off, the defect reproduced, the additive property, "cannot invent generation",
  no-double-count (both directions), the vintage resolver against the real parquets, and the
  **SPP keeper-year inertness tripwire**.
  One of these caught a real subtlety: the backfill skip depends on `_coal_supply_class` agreeing
  with `_classify_f923`, which holds for a real ORIS code and not for a synthetic one — so the
  fixture uses plant 127 and pins the real mechanism.
* **Widened, not weakened:** three existing one-arg `_iso_plant_ids` test patches now absorb the
  new arguments. The 42 tests in the adjacent membership files pass.
* **Suite status, with inherited failures separated by measurement rather than assumption.** Every
  failure below was re-run at the parent commit `8cb4d9c9` and **reproduces identically**:
  `tests/unit` 10 failures (data-profile tokens, CAISO ST_GAS registry artifact, NEISO Mystic
  retiree — which SPP-48 §5.1 already records — gas-offer zonal anchor ×2, emissions vendored
  parity, export ×4); `tests/curation + tests/scoring` 24 baseline failures (keeper/bundle
  resolution and golden-manifest provenance, i.e. bundles absent from this sparse checkout).
  One further test, `test_consume_phase3d::test_zone_lookup_matches_raw`, failed once in a full
  run and **passes in isolation and on re-run**; it is order/state-dependent on `data/clean/`, and
  this diff touches neither `zone_assignment.py` nor `clean_io`. `tests/unit/model` is fully green
  (1,488 passed).
* **Gates:** `check_cache_key_registration.py` **passes** (855 fields, 310 registered, all
  resolve, all declared defaults match HEAD). `check_mechanism_matrix.py --base 8cb4d9c9`
  **passes** — integrity, anchors, keeper stamps, and all four ratchets. `ruff` clean.
* **Rule 27 `[R-PUSH]`:** both ≥300-line files pushed as exact on-disk bytes and **blob-verified
  after push** — `run_calibration_full.py` `4191a263c7c2` (14,963 lines) and `scenarios.py`
  `651239befd0c` (21,550 lines), local and remote hashes identical.
* **Rule 28:** matrix row plus a cell in **all nine** ISO shards, same commit; each cell carries
  that ISO's own measured numbers and every one is `O` (built, measured, arming undecided) — no
  verdict transfers (rule 28(d)).
* **Rules 21/24:** zero free parameters — a union over EIA's own published per-vintage BA codes.
* **Rule 31 `[R-RETAIN]`:** nothing deleted. I unstaged (and kept on disk) four SPP-48 bundle
  parquets that a `git checkout <sha> --` had incidentally staged; they are not this lane's to add
  to `main`.

---

## 7. Retrievability and shards

**No shards were launched, and none was needed** — §8 establishes the arm costs zero LP for SPP,
so there is nothing a shard could have produced that the parent could not compute without one
(rule 32(a): the parent never solves; rule 34: never launch a shard whose result cannot back a
promotion). Nothing is stranded on ephemeral disk: the whole deliverable is commit `3f64471e` on
`claude/spp-benchmark-membership-defect-4yqm2f`, plus the reproducible probe
`scripts/probes/_spp49_membership_census.py` (three legs: `census`, `shapes`, `inert`).

---

## 8. Why a promotion here would cost ZERO re-solves

The flag reaches one LP input — the injected biomass/OTHER must-run — and **it moves neither**,
measured for all four rung years:

* **No union-added plant classifies as an injected class.** Added classes are `COAL_PRB`,
  `CT_PEAKER`, `oil`, `wind` only; `biomass`/`OTHER` adds: **none**, in every year.
* **`_vintage_completeness` never crosses the 0.90 carry threshold**: 2019 0.9890 → 0.9988,
  2020 0.9876 → 0.9919, 2021 unchanged 0.9833, 2022 0.9838 → 0.9838.

So the LP inputs are byte-identical and the arm's scored result **is** the committed dispatch
against a rebuilt benchmark. A promotion is a rebuild-and-rescore, not a solve.

---

## 9. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]` — asked, not pre-empted)

Nothing has been armed or registered, and I am not treating any of this as decided.

1. **Arm `benchmark_membership_vintage_union` for SPP and re-register the 2019–2022 rung against
   the corrected benchmark?** Cost: **zero LP** (§8). Effect: SPP's 2019/2020 `COAL_PRB` C1 misses
   grow to −8.9351 / −9.9044 TWh, determination unchanged at NOT-YET, keeper 12 provably untouched.
   *This session's reading, which is a recommendation and not a decision:* worth doing on rule-14
   grounds — the actual becomes correct and the residual becomes honest — **provided** it is
   understood that this makes a failing criterion look worse, which rules 1/14 say is the right
   trade.
2. **A default flip (arming it in `_spp_config`) is a separate owner ruling** and is not proposed
   here.
3. **Charter the PJM object (§4.1)?** It is the larger and more general defect — 8.8 TWh missing
   from a live keeper year — and it is probably a one-line membership fix (`_EIA860_SUPPLEMENT_ISOS`)
   rather than this flag.
4. **Charter the `rebuild_benchmark` fleet-config defect (§5)?** It silently makes a rebuild
   disagree with the solve that produced the bundle, which affects every ISO that rebuilds a
   fleet-changing config.
