# PREREG — miso-155: **close the instrument gap by READING the model's own P0**, then gate the CT instrument at the charter's ±10 %

**Session** miso-155 · **ISO** MISO · **Date** 2026-08-13 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED at
pre-registration** · **Model** `claude-opus-5` (rule 27 `[R-PUSH]`: this scope
writes `src/market_sim/` and `scripts/run_*.py`, so Opus/Fable only).

**This document is pushed and blob-verified against the FETCHED remote ref
BEFORE any adjudicating statistic is computed** (rule 27 `[R-PUSH]`).

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 ONLY. MISO holds **NEITHER**
`complete` NOR `final`. No holdout year is read, solved, scored or registered
anywhere in this session. Any run produced covers all three train years in ONE
bundle (rule 16 `[R-ALLYEARS]`).

---

## 0. THE FIRST DECISION, TAKEN: **BRANCH (A)** — close the gap, do not widen the bar

The miso-154 handoff put one decision first. I take **(A)**: fix the
instrument by persisting the model's own P0, and gate at the charter's
**unchanged ±10 %**. I do **not** take (B) (charter the offer level now at a
widened ±15 %). Four reasons, the third being dispositive:

1. **Rule 14 `[R-ACCURATE]` is directly on point.** The P0 run pattern is not
   an unobservable — it is a quantity **the model itself computes** at the
   P0→P1 seam (`pipeline/solve.py:249-265`) and then discards. Reconstructing
   it from P1 prices is an *estimate* standing in for an available exact input.
   Rule 14's whole subject is preferring the accurate input; widening a
   tolerance so an estimate can clear it is the move the rule exists to stop.
2. **Rule 1 `[R-STRUCT]`: structure first.** (B) reaches an instrument "pass"
   by moving the bar, then charters an offer-curve level on top of it. That is
   the wrong order and the wrong instrument.
3. **(B)'s arithmetic does not actually hold, and this is dispositive.** The
   claim behind (B) is that an 18–22 pp span fits inside a 30 pp-wide ±15 %
   bar. But the span is **not centred**: 2023's own T-9 interval is
   **[−28.98 %, −7.28 %]**, which is **not contained** in [−15 %, +15 %].
   A ±15 % bar would therefore certify 2023 on a point estimate its own
   declared uncertainty does not support — and miso-154 §4.2 established that
   **both** known biases point colder, i.e. toward the end of that interval
   that fails. (B) buys a pass the instrument cannot pay for.
4. **(A) is strictly better than the handoff advertises, and it is cheap.**
   Persisting the P0 pattern collapses **T-9** (18–22 pp) to zero. Persisting
   the `(T,)` `startup_run_ratio_t` alongside it *also* collapses **T-10**
   (the v4 band approximation, 4.66–5.51 pp) to zero — the handoff's option (A)
   only claimed T-9. **Both live limitations die on one artifact**, and that
   artifact is two small parquet files.

**What (A) does NOT do.** It does not touch the committed bundle spec: the
persistence is **opt-in, default OFF, and additive-only** (§2.3). It adds **no
`ScenarioConfig` field** and **no solve-affecting tunable** (§2.4), so rules 24
`[R-REGISTRY]` / 28(c) `[R-MECH-MATRIX]` are not engaged by the build. **No
CT offer-LEVEL lever is proposed in this document** — that remains reachable
only through a SECOND PREREG and only under branch C-CLEAR (§6).

**Escalated to the owner, not self-authorized** (miso-154 §10 named this an
owner decision): making the P0 sidecar **default-on**, i.e. part of every
keeper bundle's committed contents, WOULD be a bundle-spec change. **I am not
doing that.** This session ships it default-off and reports the measured file
sizes so the owner can decide the spec question on evidence.

---

## 1. What is already established and is NOT re-derived

Carried from `FINDING-miso154-ct-commitment-instrument-2026-08-12.md`; none of
it is re-measured:

* The +22–24 % CT price-taking residual was **the instrument, not the fleet**:
  miso-153's T-6b compared `mc_base` against a **bid**-cost clearing price.
  Correcting to `mc_bid` moves it 28–35 pp → **−13.21 / −7.53 / −4.47 %**.
* **min-run / min-down are ABSENT for MISO CT** — all 733 `CT_PEAKER` tranches
  carry `min_run_hours == min_down_hours == 0.0`; the only 51 min-run units are
  `COAL_FAMILY`. **No CT min-run/min-down lever is proposed here.** The startup
  amortization is the only commitment physics reaching MISO's CT.
* MISO arms **no** P1 bid adjustment, **no** bid-max target and **no**
  commitment bridge, so its P1 bid is EXACTLY `mc_base + markup`.
* **L1 cannot dispatch an out-of-merit floor.** miso-154 measured this on
  `ST_GAS` (47 % forced → −11.8 / −17.0 / −19.4 %). This is a *structural*
  property of price-taking, and §4.2 below is where it re-enters as a
  pre-registered, measurement-gated leg rather than a rescue.
* The across-unit dispersion object (miso-153 §12–§13), the D-4 window flag
  (miso-153 §11), the within-unit offer-shape family (miso-151), the base-band
  inversion (miso-152) and C7 `COAL_PRB` (owner order) are all **CLOSED /
  DEPRIORITIZED**. None is re-opened.

### 1.1 What I inspected BEFORE writing this document (disclosure)

All instrument/plumbing, none of it a statistic about the CT residual:

* `pipeline/solve.py:249-265`, `model/commitment.py:210-331`
  (`compute_monthly_markup`, incl. the `_amortized` v3/v4 horizon rule),
  `scripts/run_calibration.py::run_year` (the `startup_run_ratio_t`
  construction at `:4023-4039`; `p2_state` at `:5187`; the return at `:5247`),
  `scripts/run_calibration_full.py::solve_and_persist` (`:3000`) and its
  sidecar writers (`:478`, `:5182`).
* `scripts/capture_keeper_goldens.py` — the **existing, tested** path that
  reconstructs a keeper's exact `solve_and_persist` kwargs from its
  `meta.json` and asserts a key-by-key fidelity oracle. §3 reuses this
  mechanism rather than hand-assembling a 267-flag CLI.
* The keeper's committed `metrics.json` / `run_config.json` / `meta.json`, and
  `scripts/calibration_verdict.py --run-id 2026-08-09-miso-148-basis-aware`
  (committed artifacts only, **no solve**), which reproduces the published
  determination: **NOT-YET**, fail set **{C3a, C3b}**, C3a-2025 **−15.6 %**,
  C3b-2025 **NRMSE 0.212**, C3c ledgered 1/1, C6 PASS, C8 PASS with
  **CT_PEAKER-2023 grounded above budget at 16.8 % forced (2.0415 of
  12.1818 TWh)**. That last number is an *input to* the §4.2 admissibility
  test and was read before the test was written — declared here for that
  reason.
* `_MISO_OFFER_CURVE` (`pipeline/backcast_config.py:750-820`): CT_PEAKER
  `committed 1.025`, `econ_low 1.0`, `econ_high 1.0`, `peak 4.00`.
* **`data/raw/som-competitive-conduct/som_competitive_conduct.csv`** — the
  Potomac Economics MISO IMM transcription. Read while enumerating what
  already sets the CT econ band (rule 19 `[R-ONE-MECH]`). It is **evidence
  about a lever this document does not propose**, so it is disclosed in §8
  rather than used here.

**Not inspected:** any exact-P0 markup, any re-measured residual, any control
solve output. The §5 priors are reasoned from the mechanism, not read off an
answer.

---

## 2. The build — fixed here before it is written

### 2.1 The artifact

Two per-year sidecars, written **only** when the new opt-in flag is set:

* **`hourly/p0_commitment_<year>.parquet`** — one row per generator:
  `(year, gen_index, unit_id, on_bits)`, where `on_bits` is
  `np.packbits(p0_dispatch[g] > 0.05 × pmax[g])` as bytes.
  **This is the exact and COMPLETE input `compute_monthly_markup` draws from
  P0**: the function touches the P0 dispatch only through
  `find_runs(dispatch[g, h0:h1] > threshold)` with
  `threshold = 0.05 × pmax[g]` (`commitment.py:275`, `:318`). Nothing else in
  the markup depends on the P0 *level*.
* **`hourly/startup_run_ratio_<year>.parquet`** — `(year, hour, run_ratio)`,
  the `(T,)` `startup_run_ratio_t` actually passed to the markup. Absent when
  the run is on the v3 basis (`run_ratio_t is None`).

### 2.2 How the instrument consumes it (T-8 preserved)

The probe rebuilds a **surrogate dispatch** `pmax[:, None] × unpackbits(...)`
and passes it to the **production** `compute_monthly_markup`. Because the
function compares `surrogate[g,t] > 0.05 × pmax[g]`, the surrogate reproduces
the recorded boolean exactly for every `pmax > 0` row, so the returned markup
is **bit-identical to the one the solve itself used**. The markup is therefore
**READ, never re-implemented** — T-8 (`__module__` assertion) is retained
unchanged.

### 2.3 Byte-neutrality at default (T-14)

The flag defaults **False**. At default: no new files, no changed files, no
changed dispatch, no changed `run_config.json`/`meta.json` content beyond the
new recorded key itself. **The committed bundle spec is unchanged.**

### 2.4 Registry posture (rules 24 / 28(c))

The flag is **write-only** — it cannot change a solve. It is therefore a
`solve_and_persist` / CLI parameter, **not** a `ScenarioConfig` field, on the
exact precedent of `persist_p2_state` (`--persist-p2-state`). No matrix
mechanism row is created (rule 28(c) is not engaged); the MISO shard is still
stamped with this session's queue outcome under rule 28(b).
**Zero 3-argument `getattr(` is added on the offer path** (T-2).

---

## 3. The control solve — a keeper REPRODUCTION, not a new config

One invocation, **years 2023 2024 2025 sequential** (rule 12 `[R-PARALLEL]`),
run **in this session** (CLAUDE.md: never offload a solve to CI).

Kwargs are reconstructed from the keeper's own `meta.json` by the existing
`capture_keeper_goldens.build_solve_kwargs` mechanism, plus **exactly one**
added argument: the §2 persistence flag. Determinism pinned as that script
pins it (`MARKET_SIM_HIGHS_THREADS=1`).

Bundle `miso155_p0_A`, run id `2026-08-13-miso-155-control-p0`.
**Rule 15 `[R-DASHBOARD]`: it is registered, committed and pushed in this
session** whatever it shows — it is a completed backcast run.

**The instrument is scored against THIS control's own `class_hourly`, not the
keeper's.** That pairing is mandatory: the persisted P0 belongs to this solve,
so it must be validated against this solve's P1. The keeper comparison is a
separate validity gate (V2).

---

## 4. The instrument — three legs, fixed here before measurement

Per year, at the **top-200 model-demand hours** (the miso-153 window,
unchanged), statistic
`resid ≡ (E_recon − E_control) / E_control` for `CT_PEAKER`.
Annual figures reported alongside, ungated.

### 4.1 L1X — price-taking on the EXACT bid. **THE GATING LEG.**

`mc_bid = mc_base + markup_exact`, `recon[g,t] = pmax·avail` where
`mc_bid ≤ price[zone(g),t]`. Identical in construction to miso-154's L1 with
the P0 proxy and the reconstructed v4 series both replaced by reads. It is the
leg directly comparable to the published +22.0 / +22.1 / +23.7 % baseline and
to miso-154's −13.21 / −7.53 / −4.47 %.

### 4.2 L1F — floors first, then price-taking. **CONDITIONALLY GATING, and its admissibility is MEASURED, not chosen.**

L1's known structural defect is that price-taking **cannot dispatch an
out-of-merit min-gen floor** (miso-154, on `ST_GAS`). L1F repairs exactly that
one thing: every row is dispatched at `arrays.min_gen` first, and price-taking
on `mc_bid` fills only the headroom above the floor. It does **not** import
L2's energy-conservation property.

**This is pre-registered as a leg, not kept in reserve as a rescue, and the
escape hatch is closed by a measurement fixed here:**

> **L1F is admissible ONLY IF** the measured out-of-merit floored `CT_PEAKER`
> energy at the top-200 hours — floored MW whose own `mc_bid` exceeds the
> zonal price in that hour — is **≥ 5 %** of control `CT_PEAKER` top-200
> energy, in **at least 2 of 3** years. Below that threshold L1F ≈ L1X by
> construction and **cannot** be quoted, whatever it reads.

The threshold is set from the mechanism, not the answer: below ~5 % the
floored block cannot account for a bar-sized residual, so a "pass" there would
be arithmetic coincidence. The relevant context — CT_PEAKER-2023 is 16.8 %
forced annually (§1.1) — is an *annual* share on a *different* denominator and
does **not** pre-determine the top-200 test.

### 4.3 L2 — merit-order clearing. **REPORTED, NEVER GATES.**

Carried unchanged from miso-154 PREREG §5, including its fence: L2 conserves
the control's own hourly thermal total by construction, so a good L2 number is
partly an artifact of its own clearing and **must not buy a pass**.

---

## 5. Priors — two-sided, numeric, committed before measurement

**PRIOR P-1 (direction, the load-bearing one).** The exact-P0 markup is
**LARGER** than the proxy's, so **L1X lands COLDER than miso-154's L1 in all
three years**. Reasoning, from the mechanism: the proxy cleared price-taking
on `mc_base` at P1 prices, which hands every in-merit tranche its full
availability and produces long continuous blocks; the real P0 is an LP serving
load at P0 prices, which dispatches less and cycles more. `_amortized` takes
`min(avg_run, ceiling)`, so shorter P0 runs can only shorten the horizon and
raise the markup.

**PRIOR P-2 (magnitude, two-sided and explicitly against this session).** L1X
lands in **[−28.98 %, −13.21 %] for 2023**, **[−24.11 %, −7.53 %] for 2024**,
**[−18.65 %, −4.47 %] for 2025** — i.e. between miso-154's proxy point and its
T-9 `never` bound, which is the markup ceiling. Centred at roughly the
**lower-middle** of each: **−20 % / −15 % / −11 %**.

**I therefore pre-register the expectation that L1X FAILS the ±10 % bar in
2023 with near-certainty (its entire admissible interval is beyond −10 %), and
that it plausibly fails in all three years.** This is stated before measuring
because it is the honest reading of miso-154 §4.2, and because a session that
only pre-registers outcomes flattering to its own branch has pre-registered
nothing. **Choosing (A) is not a prediction that (A) passes** — it is the
claim that (A) measures the right thing. If L1X fails at ±10 % with an exact
markup, that is a REAL result about the model, not an instrument artifact, and
it is worth more than a widened bar that reads PASS.

**PRIOR P-3 (L1F).** If P-1/P-2 hold and the §4.2 admissibility threshold is
met, L1F lands **hotter than L1X by 3–15 pp** in each year, because the floored
block it adds is energy the control dispatches and L1X structurally omits.
Two-sided: L1F could also land **below** L1X in a year where the floor
displaces headroom L1X was already counting.

---

## 6. The gating bar and the branches — fixed, with their reasons

**BAR: `|resid| ≤ 10 %` for `CT_PEAKER` at the top-200 demand hours.**
**UNCHANGED from the charter. It is not widened anywhere in this document.**
Evaluated per year; the branch is decided on the count of years that clear.

| branch | condition | consequence |
|---|---|---|
| **C-CLEAR** | **L1X** clears **3 of 3** | Instrument **VALIDATED at ±10 %** on an exact markup. CT volumes are measurable. **THEN and only then** a SECOND PREREG may charter **ONE** CT offer-LEVEL lever, inheriting the §7 against-interest bound and stating its expected 2023 effect **before** any solve. |
| **C-FLOOR** | L1X fails, **AND** §4.2's admissibility threshold is met, **AND** **L1F** clears **3 of 3** | The residual is attributed to out-of-merit floored CT energy price-taking cannot represent. Instrument validated **on L1F only**, and the finding must say so in those words. A SECOND PREREG becomes reachable on the same terms as C-CLEAR. |
| **C-PARTIAL** | Either leg clears **2 of 3** and neither clears 3 of 3 | Reported at full magnitude. **NO lever, NO second PREREG.** The failing year is the finding. |
| **C-FAIL** | Both legs clear **≤ 1 of 3** | **NO lever.** With the markup now EXACT, a residual this size is a structural statement about the model's CT dispatch-vs-offer relationship, and *that* becomes the finding. |

**Magnitudes are reported in every branch, always.** No branch permits quoting
L2 as the gating leg, and none permits substituting the v3 flat-ratio basis —
miso-154 §4.3 established v3 clears 3 of 3 and is **not** the keeper's basis
(`tranche_startup_conditional_runs=True`); substituting it to buy a pass is
the fitted move rule 1 `[R-STRUCT]` forbids. **The exact `run_ratio_t` read
from the control retires that question entirely.**

### 6.1 Pre-committed surprise triggers

| trigger | fires when | what I do |
|---|---|---|
| **S-CEILING** | L1X is **colder than the T-9 `never` bound** in any year | Arithmetically impossible with a correct read — `never` is the markup ceiling. The pack/unpack or the surrogate is wrong. **Stop, debug, disclose before any conclusion.** |
| **S-WARMER** | L1X is **hotter than miso-154's proxy L1** in all three years | **P-1 is refuted** and miso-154 §4.2's declared bias was backwards. Report as a refutation of the inherited finding, at full magnitude. |
| **S-INERT** | exact vs proxy cap-weighted CT markup differ by **< 1 %** | The exactness bought nothing: the T-9 span was an artifact of its extreme bounds, not of the proxy. The build still ships (rule 14), but the finding says the limitation was over-stated. |
| **S-NOREPRO** | the control fails validity gate **V2** (§7) | The control is not a keeper reproduction. Everything downstream is labelled against the control, never against the keeper. |

---

## 7. Validity gates — reproduce a published number BEFORE any adjudicating statistic

The miso-154 void-run precedent is binding: its baseline leg caught a
truncated checkout. Two gates, both run first.

* **V1 — the instrument's own baseline.** The probe's
  `BASELINE_pricetaking_mc_base` leg must reproduce miso-153's published T-6b
  at **+21.99 / +22.14 / +23.72 %** to **±0.01 pp**, on **n_gen 2929 / 2923 /
  2923**. (miso-154 achieved ±0.001 pp.)
* **V2 — the control is a keeper reproduction.** The control's scored
  determination must read **NOT-YET** with fail set **{C3a, C3b}**, C3a-2025
  within **±1.0 pp** of **−15.6 %**, C3b-2025 within **±0.02** of **0.212**.
  A miss fires **S-NOREPRO** and is disclosed, not absorbed.

**Environment integrity, already executed and recorded here:**
`git status --short | grep -c '^ D'` = **0**, 11,004 tracked files;
`curate_capacity_deliverability.py` → **776 MISO rows** (the expected count).
The container had **no `.venv`**; one was built from `requirements.txt`.

**AGAINST-INTEREST BOUND (binding, inherited from miso-154 PREREG §7).**
2023 passes C3a at ≈ −0.5 %. A lever that lifts 2023's mean by more than
**+3 %** is a **REGRESSION** even if 2025 improves. **This session applies no
lever**; the bound is restated so a SECOND PREREG inherits it.

**Contingency, pre-registered.** If the control solve cannot complete all
three years in this session, **no adjudicating statistic is quoted**: the
session reports the build as shipped-but-unmeasured, registers nothing, and
the branch is left undecided. A partial-year solve is **never** registered
(rule 16 `[R-ALLYEARS]`).

---

## 8. Rule 19 `[R-ONE-MECH]` — what already sets the MISO CT econ band

Enumerated now, before any successor proposes to add to it, per the rule's
"enumerate first" duty. **Nothing in this list is changed by this session.**

1. **The band multipliers.** `_MISO_OFFER_CURVE["CT_PEAKER"]`:
   `econ_low 1.0`, `econ_high 1.0` — measurement-AFFIRMED neutral, on MISO's
   own CAMPD marginal HR being flat-to-falling with load (0.687 / 0.691),
   corroborated by NEISO as a third fleet.
2. **The startup amortization** (`tranche_startup_amortization` +
   `_measured_runs` + `_conditional_runs`): cap-weighted **$4.15–4.74/MWh** at
   the top-200 hours. Registered by `_MISO_OFFER_CURVE`'s own comment as the
   representation of MISO's ELMP fast-start pricing.
3. **`gas_offer_margin`** (armed on this keeper): reprices `max(0, mult − phys)`
   from fuel-scaled to a fixed $/MWh margin at the ISO anchor, with
   `phys_econ_low 0.687 / phys_econ_high 0.691`.
4. **The `peak 4.00` band** on `pct_peaking 7.0` of CT capacity.

**A measured MISO datum that any future CT offer-LEVEL charter must confront,
recorded here because I read it (§1.1) and it cuts against the lever this lane
is heading toward.** The Potomac Economics MISO IMM measures the **system
price-cost mark-up** at **+3.0 % (2023)** and **−2.5 % (2024)**, with the
economic-withholding output gap "effectively de minimis" (**0.1 % / 0.06 %**
of load; 2025 IMM quarterlies 22 / 59 / 71 MW·h⁻¹). *(Source:
`data/raw/som-competitive-conduct/som_competitive_conduct.csv`, rows 12–13 /
24–25, transcribed with per-row `source_doc`+`source_page` provenance from
`2023-MISO-SOM_Report_Body-Final.pdf` p.112 and
`2024-MISO-SOM_Report_Body_Final.pdf` p.120.)* MISO's real market clears
essentially **at cost**, and the model's CT already offers at its own base
heat rate plus a startup markup. **This is not adjudicated here and no verdict
is minted on it** — it is filed so a successor cannot charter an offer-LEVEL
lift without answering it. It is evidence, not a decision.

---

## 9. Traps, each with its counter-measurement

T-1…T-11 are inherited from miso-153/miso-154 and re-run unchanged; T-12…T-17
are new to this build.

| # | Trap | Counter-measurement |
|---|---|---|
| **T-1** | `_miso134` is HARD-WIRED to `miso132_ccmin_B` | Repoint and **assert**; report matched/dropped key counts |
| **T-2** | 3-arg `getattr` on the offer path silently encodes a wrong field name | **Zero** 3-argument `getattr(` added; `grep` count reported; `ruff` clean |
| **T-3** | Collapsing the `econc00..econc05` smoothing yields a spurious exact 0.0 | Full raw suffix inventory before aggregation. **Disbelieve clean zeros** — every exact 0.0 gets a second derivation or is reported unverified |
| **T-4** | `SimpleNamespace` fixtures encode the same wrong name as the code | Production types only; assert no `SimpleNamespace` |
| **T-5** | `MISO_external*` are IMPORT NODES | Assert carry-zone count **== 6**; import nodes excluded from every aggregate |
| **T-6** | `build_year` keys the CAMPD derate on `config.weather_year`, not the solve year | `dataclasses.replace(cfg, weather_year=y)` per year, **plus** its own 2023-unchanged control (tolerance 1e-9, magnitude reported) |
| **T-7** | An inert instrument "clears" nothing and looks like a fix | Report cap-weighted CT markup $/MWh at top-200 **and** its distribution, for BOTH the exact and the proxy markup |
| **T-8** | A re-implemented markup reproduces my expectation, not the model's | **Assert** `compute_monthly_markup.__module__ == "market_sim.model.commitment"`; the surrogate-dispatch route (§2.2) keeps the production function |
| **T-9** | *(retired by construction)* the P0 proxy is not P0 | **The P0 is now READ.** Still report the three T-9 bases on the control so the collapsed span is *measured*, not asserted |
| **T-10** | *(retired by construction)* `run_ratio_t` needs potential, sidecars carry dispatched | **The series is now READ.** Report the exact-vs-reconstructed v4 gap so T-10's 4.66–5.51 pp is measured as closed |
| **T-11** | The charter names min-run/min-down; MISO's CT carries none | Re-assert the distinct-value census (733/733 at 0.0) on the control's own fleet |
| **T-12** | A bit-packing round-trip that silently truncates the last partial byte | Assert `unpackbits(packbits(on))[:, :T] == on` **exactly**, elementwise, per year; and assert the surrogate reproduces the recorded boolean elementwise |
| **T-13** | The surrogate could differ from the true P0 for `pmax == 0` rows | Count and report such rows; assert their markup contribution to CT top-200 energy is exactly 0 |
| **T-14** | The persistence flag silently perturbs the solve | Flag-off vs flag-on **dispatch byte-identity** on a small golden (1 gen / 1 zone / 24 h and one real ISO-year slice), plus a file-list diff proving additive-only |
| **T-15** | The control is not the keeper (drifted HEAD) | V2 (§7), plus the `capture_keeper_goldens` fidelity oracle key-by-key against the keeper's `meta.json`/`run_config.json`; every mismatch reported |
| **T-16** | Scoring the instrument against the KEEPER's `class_hourly` while using the CONTROL's P0 mixes two solves | The instrument is scored against the **control's own** `class_hourly`; the keeper pairing is reported separately and labelled |
| **T-17** | The exact-vs-proxy comparison confounded by keeper-vs-control drift | Run **both** the proxy leg and the exact leg **on the same control bundle**, so the exact-vs-proxy delta is internally controlled |

---

## 10. Rules engaged

* **Rule 1 `[R-STRUCT]`** — the instrument is judged on whether it reproduces
  the model's own mechanism, never on whether it flatters a residual. The bar
  is not widened; the basis is not substituted.
* **Rule 14 `[R-ACCURATE]`** — §0.1: read the exact input, do not tolerate an
  estimate because it is convenient.
* **Rule 13 `[R-MEASURED]`** — nothing is pinned to a measured outcome. The
  instrument is validated against the model's own output, which is not an
  actual.
* **Rule 19 `[R-ONE-MECH]`** — §8 enumerates what already sets the CT econ
  band. No floor, bridge or adder is added.
* **Rule 21 `[R-DOF]`** — the build introduces **zero** free parameters. The
  only new numeric in this document is the §4.2 admissibility threshold, which
  gates a *report*, not a solve.
* **Rule 24 `[R-REGISTRY]` / 28(c)** — no `ScenarioConfig` field; a write-only
  CLI/`solve_and_persist` parameter on the `persist_p2_state` precedent.
* **Rule 25 `[R-ISO-SCOPE]`** — nothing crosses an ISO boundary; the sidecar
  is ISO-agnostic plumbing carrying no ISO's parameters.
* **Rules 15 / 16 / 12 / 22** — register the control in this session, all
  three train years in one bundle, years sequential, no holdout year touched.
* **Rule 27 `[R-PUSH]`** — Opus; local edits pushed as exact on-disk bytes;
  every push touching a ≥300-line file blob-verified immediately.
* **Rule 28(b) `[R-MECH-MATRIX]`** — the MISO shard is stamped with this
  session's outcome, including a rejection.

---

## 11. §10 disclosure standard

Any statistic computed in this session that is **not** in §4–§9 is labelled
**NOT PRE-REGISTERED** where it is reported, with its counter-measurement and
its **full magnitude** — in the favourable and the unfavourable branch alike.
Scope extensions are disclosed, never silently folded in.
