# FINDING — nyiso-104b: NYISO frontier + CALIBRATED-WITH-CAVEATS, and the holdout marker splits in two

**Session:** nyiso-104 · **Date:** 2026-07-31 · **ISO:** NYISO (+ cross-ISO governance)
**Keeper:** `2026-07-30-nyiso-100-silretire` — **UNCHANGED**. No solve ran.
**Owner decisions, verbatim:** *"I am comfortable with taking c3c as a caveat and calling NYISO
calibrated with caveats if we've exhausted options to address scarcity tail"* and *"I think there
should be 2 markers - calibrated with caveats and complete for 2022 touchpoint testing but NOT
training and then calibration FINAL for holdouts"* and *"So NEISO is just complete for 2022 touch
point testing not training. NYISO would also be marked as this now if we've frontiered. Neither is
final."*

---

## 0. Headline

Two things, both scorer/governance-side, neither touching a dispatch path:

1. **NYISO is CALIBRATED-WITH-CAVEATS.** C3c was the *sole* FAIL — every other criterion already
   passed. It is now one ledgered caveat (of a budget of 3), on a **verified-exhausted** lever
   queue. The keeper is unchanged and no LP ran.
2. **The rule-22 holdout marker splits into two independent tiers.** `complete` authorizes the
   iterable validation ladder; a new `final` block authorizes the touch-once locked test. Both
   NEISO and NYISO hold `complete`; **`final` is empty**.

The second change is the load-bearing one. Before it, a single `complete` entry authorized *every*
out-of-training year — so the least reversible spend in the whole policy (the touch-once 2019 /
H1-2026 locked test) was reachable on the same declaration as the cheapest one. Rule 22 admitted
this in its own text: *"the CI gate is tier-agnostic — it enforces the marker, not the
validation/locked distinction, which is a discipline clause."* Declaring NYISO complete under the
old single-marker scheme would have silently armed its locked test.

---

## 1. The condition was tested, not assumed

The owner's authorization was conditional on having *exhausted options*. That was verified against
the record rather than inherited from the charter.

| candidate | disposition | session |
|---|---|---|
| J/K commitment + reserve tiers | closed in full (SRMC roof ~$258 mainland) | nyiso-83/84 |
| DA virtual depth / DA demand formation | REFUSED ex-ante on identification — NYISO publishes no submitted-curve equivalent; P-59 `zonalBidLoad` has no price axis, so `net(λ)` needs an assumed price distribution = a fitted scalar (rule 21) | nyiso-94 |
| TSA transfer derate | REFUSED ex-ante, not identifiable | nyiso-95 |
| `unit_outage_short_windows` | INERT ex-ante — detector is coal-only, NYISO has no coal | nyiso-93 |
| CT start-frequency lane | closed | nyiso-96 |
| `tranche_startup_amortization` | tested (R on rule 1, then owner-promoted for its C1 pass) | nyiso-96 |
| **SCUC load-pocket security commitment + BPCG** (last surviving candidate) | closed **ex-ante on CONTENT, not merely access**: the as-enforced AORR is MyNYISO-walled *and* the public 2008-vintage Appendix B carries no derivable NYC parameter | nyiso-97 |
| import hourly shape | REFUSED — an attributed C3c *symptom*; the seam is exonerated | nyiso-99 |
| G-J locality limit | REFUSED ex-ante — Capital_Hudson straddles the locality; two of four boundary legs are not LP quantities | nyiso-101 |

The one nominally-open item, **`nyiso_iroquois_winter_spread` (item 4)**, is the only thing that
looked like a live lever. It is not: its construction conserves the annual spread, so it is
explicitly blocked on a *joint summer scarcity lever* — and summer is precisely what is exhausted.
nyiso-92 dated the actual RT tail as **summer** (2025 Jun 23–25 alone = 18 of 42 hours; the
Jan-2024 storm produced **zero** >$300 hours), which caps the winter-fuel lane at ~4–5 h/yr.

**Condition satisfied.** The re-open condition is a `Capital_Hudson → Zone-F/Zone-G` **topology
split**, which needs its own owner charter (the ERCOT West/Panhandle class, CLOSED) — a different
project, not a lever.

## 1.1 What the caveat does and does not claim

It does **not** claim the benchmark is wrong. The measured RT tail is real and the model
under-produces it: **model 3 / 0 / 7 h vs actual 10 / 12 / 42 h** above $300 (0.30× / 0.00× /
0.17×). The ledger entries follow MISO's own `price_tail` precedent and say so honestly —
`MODEL MISS (structural — representation-frontier caveat, every admissible mechanism tried on
record per rule 1)` — rather than borrowing a measured-input excuse the situation does not support.

Rule 1 `[R-STRUCT]` is *why* this is a ledger entry and not a mechanism: every remaining way to
lift the tail is fitted to the tail residual, and a tail reached through a mechanism that isn't
real is worse than a missing tail.

---

## 2. The marker split

`scripts/lib/holdout_policy.py` (the existing single-home module) gains the tier map; all three
rule-22 gates read it.

| tier | years | marker block | spend semantics |
|---|---|---|---|
| train | 2023–2025 | *(none)* | the only tuned window |
| validation | 2018, 2020, 2021, 2022 | **`complete`** | **iterable** — model-selection evidence, never a certified out-of-sample number |
| locked test | 2019, 2026 (H1) | **`final`** | **touch-once, ever** |

**Fails closed.** `tier_for_year` maps any year in none of the three sets (2027, 2015, …) to
`locked_test`, the strictest tier — an unanticipated year can never be spent on the weaker marker.
An absent `final` block authorizes nobody.

Current state:

| ISO | `complete` | `final` |
|---|---|---|
| NEISO | ✓ (validation only) | ✗ — **never scored, not granted** (corrected 2026-08-06, D-23 — see below) |
| NYISO | ✓ (validation only, re-declared) | ✗ — never scored, not granted |
| all others | ✗ | ✗ |

> **CORRECTION 2026-08-06 (owner decision D-23).** The NEISO row above previously read
> "✗ — locked test **already SPENT** 2026-07-07 on the frozen neiso-53 config", and the
> paragraph below cited NEISO as the worked example of the "spent" case. **That was false.**
> No NEISO 2019 or H1-2026 year has ever been solved, scored or registered; the id cited as
> the frozen config is a TRAIN-tier 2023–2025 run. NEISO belongs in the same category as
> NYISO — never scored, not granted. Citation chain:
> `results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1 →
> `docs/third-party-peer-review-2026-07.md` §6.3 item 1 → D-23 / sitting Addendum X.6.
> **This corrects the record only; it grants nothing.** NEISO stays absent from `final`.

**Absence from `final` is deliberately not self-explaining.** It covers both "never authorized"
and "authorized once, spent, never re-grantable" — though **no ISO is currently in the spent
state**, so today every blank means "never authorized". The per-ISO `locked_test` note
in the marker file is what distinguishes them, and both files now say so explicitly, so a future
session cannot read the blank as an invitation.

### 2.1 NYISO's marker is a RE-declaration

NYISO held a marker from 2026-07-13 that was **withdrawn 2026-07-19** by the phantom-outage
re-audit: the then-keeper (nyiso-62) was solved against a stale-detector outage extract and its
offer curves were compensating for under-counted outages (rule 14 / the ERCOT-79 condition), so on
the corrected detector it flipped to NOT-YET on C1/C3a/C3b. The withdrawal record's own prescribed
path was *"re-calibrate NYISO offer curves against the corrected outages across the full 2023-2025
span, then re-declare."* That lane is complete — the keeper re-declared here descends entirely from
the post-correction re-calibration (nyiso-96 → 98 → 99 → 100, all after 2026-07-19). The withdrawn
record is annotated `superseded` rather than deleted.

---

## 3. Nothing is spendable today, and that is not this change

The **holdout spend freeze** (`frontend/data/backcast/holdout-freeze.json`, declared 2026-07-25,
**held** 2026-07-26) is **ACTIVE**. It outranks every marker and is checked first: while it stands,
no out-of-training year may be solved for any ISO — validation tier included. Its cause is a
separate, still-open availability-envelope defect (the CAMPD economic-layup over-count that
survives the merit-order guard).

So NYISO's 2022 touchpoint becomes spendable only when the **owner lifts the freeze**. No session
lifts it by inference from a passing metric. This is verified, not assumed — the gate was exercised
against the real repo and the freeze fires ahead of the marker.

---

## 4. Verification

Determination, on the committed bundle, scorer-side only:

```
CALIBRATION DETERMINATION: CALIBRATED-WITH-CAVEATS
[~] CAVEAT  SUPP  C3c price tail / scarcity (RT hourly) [ledgered]
determination basis:
  - 1 ledgered measured-input caveat(s): C3c price tail / scarcity (RT hourly)
```

1 ledgered caveat against `MAX_LEDGERED_CAVEATS = 3`; 0 protective caveats; 0 FAILs.

Gate behaviour, exercised on a temp repo (marker logic) and the real repo (freeze):

| case | result |
|---|---|
| `[2023,2024,2025]` any ISO | allowed |
| `[2022]` NYISO / NEISO (`complete`) | allowed |
| **`[2019]` NYISO, `[2026]` NEISO** | **BLOCKED — not in `final`** (was allowed pre-split) |
| `[2022]` ERCOT (unmarked) | blocked |
| `[2022, 2019]` NYISO | blocked on the locked leg |
| `[2027]` NYISO | blocked — unenumerated year falls to locked |
| `final` only, `[2022]` | blocked — the blocks are independent, not nested |
| any year, freeze active | blocked ahead of the marker |

- `legitimacy_diagnostics --keepers` D-6: **PASS**, NEISO's two 2022 bundles correctly tiered
  `validation`/`complete`.
- `audit_keepers --check`: **PASS**, 0 failures, 0 warnings.
- `tests/scoring/test_holdout_year_gate.py` + `test_audit_keepers.py` +
  `test_legitimacy_diagnostics.py`: **96 passed** (8 new tier tests; 3 existing tests updated to
  assert the new tier-specific message rather than the superseded one).

---

## 5. Files

- `scripts/lib/holdout_policy.py` — tier map, `tier_for_year`, `split_breach_by_tier`, `authorized`
- `scripts/run_calibration_full.py::enforce_holdout_year_gate` — tier-aware, freeze still first
- `scripts/legitimacy_diagnostics.py::run_d6_quarantine` — per-tier rows and failures
- `scripts/audit_keepers.py::holdout_quarantine_failures` — per-tier failures
- `frontend/data/backcast/calibration-complete.json` — `final` block, NYISO entry, NEISO re-scoped
- `scripts/gen_nyiso100_attestation.py` — the C3c `exceptions` ledger (**generator is the source of
  truth**; editing only the emitted JSON is reverted by the next run)
- `frontend/data/backcast/keepers/NYISO.json` — `frontier` block; `status/NYISO.js` rebuilt
- `CLAUDE.md` rule 22 — the "tier-agnostic" clause superseded
