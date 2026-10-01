# FINDING — `--reuse-solved` cannot regenerate NWPP's `_shared` inputs for the nwpp-44 legs

**Lane:** NWPP-44 reuse shard (v2) · **Date:** 2026-09-20 · **Pinned HEAD:** `f34520793ca64ad34f73d050f27b7e18156f1772`
**Outcome:** STOPPED at STEP 3. **Zero LP ran.** No bundle pushed (there is nothing registrable to push).

## 1. What was asked, and what actually happened

The lane was to regenerate a REGISTRABLE span bundle at zero LP: compose the three
already-solved nwpp-44 legs, then run `--reuse-solved` so
`render_calibration_html.build_payload`'s benchmark/input frames
(`results/calibration/_shared/NWPP/`) get written without a solve.

Steps 1 and 2 succeeded. **Step 3 refused reuse for every year and began a fresh solve**,
which was killed at 143 s — inside 2023's data loaders, **before HiGHS was ever entered**.

```
WARNING: --reuse-solved: no year reused: effective ScenarioConfig for year 2023 differs
from the prior bundle's persisted scenario_config:
['commitment_floor_window_netload', 'gas_basis_differential_measured_by_year',
 'gas_flow_date_year_start_package', 'vre_reference_rate_year_own']
INFO: --reuse-solved results/calibration/nwpp44_takeorpay_span: reusing years none,
solving fresh [2023, 2024, 2025]
```

`results/calibration/_shared/NWPP/` was **never created**; the out-dir holds only an empty
`dispatch/`. The lane's objective was not achieved and cannot be achieved as specified.

## 2. The compose fix DID take — that was not the blocker

`f3452079` (the pinned HEAD, the one-hunk fix this shard was sent in to exploit) works:

```
years [2023, 2024, 2025]
gas_prices {'2023': 2.54, '2024': 2.19, '2025': 3.52}
```

Compose exited 0, with `857 shared fields agree, surface fingerprint shared` across the three
legs. The previous shard's blocker is genuinely fixed. **The refusal is a different, deeper one.**

## 3. Two INDEPENDENT gates refuse. Fixing either alone changes nothing

The legs were solved at `ee276d87`. The pinned HEAD is **121 commits** later.

**Gate A — effective `ScenarioConfig` (`plan_reuse_solved`, the one that fired).** The four
named fields are **absent entirely** from every leg's persisted `run_config.json`, and are
`bool = False` at HEAD. They landed in `src/market_sim/config/scenarios.py` (+227 lines)
between `ee276d87` and HEAD, from other lanes. The comparator requires full-field equality,
so "absent" ≠ "False" and it refuses — even though all four are default-off and inert.

**Gate B — git drift (would fire next; never reached because A short-circuits first).**

```
git diff --stat ee276d87 HEAD -- src/ scripts/ data/
  → 55 files changed, 14691 insertions(+), 46 deletions(-)
```

including `scenarios.py`, `data/renewables.py`, `data/fuel/hubs.py`, `data/fleet/arrays.py`,
`runner.py`, `run_calibration.py`. The gate has **no exemption list** —
`_git("diff","--name-only",prior_sha,"HEAD","--","src","scripts","data")` refuses on *any*
changed path, probes included.

Gates that PASS and are not the problem: iso, hours, `highspy` (1.15.1 both sides), and the
solve kwargs (the refusal fires after the kwargs check).

## 4. The catch-22 this creates — the part worth the parent's attention

The compose fix lives at `scripts/probes/_nwpp42_compose_span.py`, i.e. **under `scripts/`**.
So at *any* commit carrying the fix, Gate B refuses these legs — even if Gate A were zero.
**Reuse of the nwpp-44 legs is unreachable from HEAD or from any descendant of it.**

## 5. The one path that appears open (PARENT'S CALL — this shard did not act on it)

Pin the reuse shard at **`ee276d87` exactly** — the legs' own solve commit — and compose with
the *old* script, then patch the composite's `meta.json` `gas_prices` **as a data edit**:

- `cur_sha == prior_sha`, so the whole `if prior_sha != cur_sha` drift block is **skipped** —
  Gate B never evaluates.
- Gate A's probe is rebuilt by `ee276d87`'s own code, where the four fields do not exist, so
  the dump should match the legs' persisted config. *(Inferred from the refusal naming exactly
  those four and nothing else; not directly verified, since verifying means leaving the pinned SHA.)*
- `meta.json` lives under `results/`, which **no** gate covers — so the gas-price correction
  needs no code change and cannot trip the clean-tree or drift checks.

This requires **zero edits under `src/` or `scripts/`**, which is why it is worth trying before
paying for a re-solve.

## 6. Latent defect this exposes beyond nwpp-44

The pre-fix compose bug is in **every span composed before `f3452079`** — the nwpp-42 keeper's
own `meta.json` carries `gas_prices: {"2023": 2.54}` against `years: [2023, 2024, 2025]`. Per
the fix's own comment, `plan_reuse_solved` refuses years "not in prior_gas", so **those keepers
are not reusable either until recomposed.** Recomposing them is likewise blocked by §4 for any
leg set whose solve commit predates the fix.

## 7. Cost of the alternative, stated before anyone pays it (rule 31 `[R-RETAIN]`)

A fresh NWPP span is **~90 min/year** (2024's P1 alone ran 11,600 s in the arm leg) — call it
**4–5 h of LP** for 2023–2025. This shard did not spend any of it. The three leg bundles remain
intact and verified on their own branches; nothing was deleted.

## 8. Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e))

Nothing new to retrieve — **no new solve output exists.** The three verified legs are on
`main`-unmerged shard branches at `9ac338cefa041800d9ccfe6f208e205ffe1115fd` (2023),
`6f3aa99cfe160db46822d3d54105007a3552ee86` (2024),
`063fe56cc2a6fd7cf9d8492f11a4268d97bcde45` (2025). Per rule 33(f) those SHAs are **provenance,
not a durability claim** — the branches are cut when a parent PR merges, so any leg not landed
on `main` must be costed as a re-solve (§7).
