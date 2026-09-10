# GOVERNANCE NOTE — the touchpoint `--declared-degradation` channel is NEW SURFACE and the owner should rule on it

**Session miso-251, 2026-09-10.** Flagged here rather than left in a commit message, because it
changes what a C6 governance PASS can be written for. **Nothing about it is hidden and nothing
about it is urgent** — the ladder it unblocks is already run and reported — but it is the kind of
change that should be ratified or refused deliberately.

---

## 1. What it does

`scripts/gen_touchpoint_attestation.py` writes a touchpoint's `calibration_attestation.json`, and
its whole purpose is that a touchpoint's C6 PASS is **computed, not typed**: it compares every
shared `meta.json` key against the keeper and refuses to write the file if anything differs outside
a provenance set. Before today it admitted **zero** recipe deltas.

It now accepts `--declared-degradation FIELD` (repeatable) with a mandatory `--degradation-reason`.

## 2. Why it had to exist for MISO to have a holdout ladder at all

MISO published **no ASM reserve record before 2023**. `docs.misoenergy.org` keeps a rolling ~3.5-year
window; every pre-2023 probe of `asm_exante_damcp` / `asm_rtmcp_final` / `asm_rt_co` returns **404**
(re-verified 2026-09-10; the 2026-07-31 intake's authoritative 5,481-request sweep of 2018–2022
found **0 days published**; the documented Data Exchange fallback needs `MISO_PRICING_API_KEY`,
which is in neither the environment nor the repo).

The keeper arms `miso_measured_reserve_requirements`, whose loader **hard-errors** on a missing
year rather than falling back — by design, so the flag can never "solve on the static estimates it
claims to replace" — and `miso_reserve_online_gated` is its hard dependent, which the code refuses
to run without it. So the keeper's recipe **cannot be executed on any MISO year before 2023**, and
before this change any year that was executed (by disarming them) **could not be attested**.

Without the channel, MISO's holdout ladder is closed **by construction rather than by evidence**.
That is not MISO-specific: **any ISO whose measured overlay post-dates its holdout years hits the
same wall.**

## 3. The guards — enforced, not promised

| guard | what it stops |
|---|---|
| **Default-only.** A declared key is admitted ONLY when the touchpoint's value equals that field's `ScenarioConfig` default. | It can **DISARM** an overlay and **never arm one**, never re-cut a multiplier, never introduce a scalar. A declared key at any other value stays a hard error. |
| **Fails closed.** If `ScenarioConfig` defaults cannot be imported, every declared key stays a conflict. | An unverifiable declaration is worth nothing, so it buys nothing. |
| **Container all-or-nothing.** The generic `prb_overrides` dict is admitted only if EVERY field that moved inside it verifies. | One undeclared or non-default field smuggled into the container refuses the whole container. |
| **Mandatory reason.** `--declared-degradation` without `--degradation-reason` is a hard error. | A delta with no stated cause is exactly the silent drift the generator exists to refuse. |
| **Full disclosure.** The delta, each field's default, and the reason are written verbatim into `governance.attested_by` and into a `touchpoint.declared_degradations` block. | A reader of the attestation cannot miss it. |
| **Everything else still binds.** Recipe identity is still computed exactly over every other shared key; solve-surface drift is still checked. | The machine check is narrowed by exactly the declared set and by nothing else. |

Six tests pin these (`tests/scoring/test_touchpoint_declared_degradation.py`), including the two
that matter most: a declared key at a non-default value is still refused, and the channel fails
closed without defaults.

**Why "default" is the right line.** Disarming a rule-13 measured overlay drops the run onto the
construction a **FORECAST** year uses — which is what rule 13 `[R-MEASURED]`'s own admissibility
test asks for. The degradation makes the holdout year *more* like a forward run, not less.

## 4. The second change in the same file, which is a plain bug fix

The generator also demanded all four governance assertions be **true** on the keeper. A keeper using
rule 1 `[R-STRUCT]`'s authorized `offer_curve_by_group` channel carries
`levers_trace_to_measured_input` and `no_fit_to_price_residuals` as **false**, scoped by an
`authorized_price_tuning` declaration — and its own C6 **passes** on that basis in
`calibration_verdict.score_governance`. MISO's keeper is exactly that shape. The generator simply
predated the 2026-09-05 amendment. It now mirrors the scorer: those two assertions are scoped when
a declaration is present, `no_pinning_to_actuals` and `outage_filter_exogenous_net_load` are never
scoped, and a keeper with the two false and NO declaration is still refused. The touchpoint now
carries the keeper's **own** assertion values rather than a blanket `True`, which is strictly more
truthful than what it wrote before.

## 5. What the owner is being asked

Nothing is pending on this — the 2022/2021/2020 rungs are run and reported either way. The question
is whether the channel **stays**:

* **(a) Ratify it** as standing tooling, on the guards in §3.
* **(b) Narrow it** — e.g. require the declared field to be named in an allow-list in the repo
  rather than passed on the command line, so the set of degradable overlays is itself reviewed.
* **(c) Refuse it** — in which case `gen_touchpoint_attestation.py` reverts, MISO's pre-2023 rungs
  become **unattestable** (C6 UNATTESTED → NOT-YET on governance alone, regardless of the model),
  and MISO has no holdout ladder until `MISO_PRICING_API_KEY` and a pre-2023 ASM record both exist —
  which, for the ASM record, they never will.

My recommendation is **(a) with (b) to follow if the channel is ever used a second time**: the
default-only guard is the load-bearing one and it is airtight as written, but an allow-list would
make the *set* of degradable overlays reviewable rather than per-invocation, and that is worth
having before a second ISO uses it.
