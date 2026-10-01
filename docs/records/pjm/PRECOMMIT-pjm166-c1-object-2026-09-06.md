# PRECOMMIT — pjm-166: the PJM held-out C1 object, and the same-HEAD control

**Session:** pjm-166 · **Date:** 2026-09-06 · **HEAD:** `ca1bcc70` ·
**Branch:** `claude/pjm-gas-coal-c1-0lm1m8`
**Keeper under study:** `2026-08-15-pjm-162-inputclock` (bundle `pjm_debugb_inputclock_A`) —
**UNCHANGED by this session.**
**Touchpoints read:** `2026-09-05-pjm-2022-2021-touchpoints` (bundle `pjm_tp2022_2021_k162`).

Written **before** any LP is launched, per rule 29 `[R-SCREEN]` clause (b): the G-DRIFT
audit is recorded here so it cannot be written to fit a result.

---

## 1. What this session is, and is not

The dispatch asked for the gas-over / coal-under C1 object on PJM's two held-out rungs to be
taken back to 2023–2025 as an **object** (rule 22 step 3), starting **zero-LP** (rule 29
clause 0).

**No mechanism is armed, swept, or tuned in this session.** Nothing is fitted to a
touchpoint year — rule 22's loop forbids identifying any parameter against 2021/2022, and the
zero-LP work below is measurement only. **No `ScenarioConfig` field changes**, so rule 28(c)
does not fire.

**There is therefore no screen year to name under rule 29(a).** That clause governs a **new
config**; the single LP this session runs is a **control** — the incumbent keeper's own
recipe replayed on its own training years — which is neither a screen nor an arm. Clause (a)
is inapplicable rather than waived.

## 2. G-DRIFT — attempted first, and it is STRUCTURALLY UNDISCHARGEABLE

Rule 30(b) makes G-CTRL **form 4** (difference against the keeper's committed bundle) the
default and requires a code-level drift audit rather than a control solve. The audit was
attempted first, as the rule directs:

```
git diff 457ae04 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib \
    data/raw/_validation-source data/raw/reference
→ fatal: bad revision '457ae04'
```

`457ae04` is the `git_sha` recorded in `pjm_debugb_inputclock_A/meta.json`
(timestamp `2026-08-15T08:42:21`). It **does not exist in the repository at HEAD**, and this
is not a shallow-clone artifact: the clone was deepened to **11,640 commits** and the object
still does not resolve. The cause is named in CLAUDE.md — the **2026-08-16 history rewrite**
(`.github/workflows/cleanup-large-blobs.yml` run 31955205445) force-pushed a rewritten
history, so *"every pre-2026-08-16 commit-sha citation outside
`docs/governance/citation-commit-map.txt` is now a dead (or, for short prefixes, possibly
WRONG) reference."* The keeper solved on **2026-08-15**, one day before the rewrite, and
`457ae04` is **not** in the 114-line commit map.

**Verdict: G-DRIFT cannot be discharged for this keeper at any cost** — there is no diff to
classify, not merely a large one. This is *stronger* than the NEISO precedent
(`ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05` §4 i), where the diff existed but
spanned 120 files / +119,273 lines and was ruled unclassifiable. An unclassifiable diff is
treated as **LIVE**, and a LIVE hunk is exactly what earns a control solve under rule 29(b).

**The control solve is therefore EARNED, and is the only available route to the question.**
It is also the open limit the touchpoint assessment named (§4 i, §5 item 2): PJM's HEAD drift
has never been measured, and NEISO's INERT verdict does **not** transfer (rule 25
`[R-ISO-SCOPE]` — PJM arms `pjm_measured_interface_limits`, `pjm_da_virtual_bids` and
`measured_ramp_capability`, none of which NEISO touches).

## 3. The control — pre-registered before it runs

```
python scripts/run_calibration_full.py --replay-bundle \
  results/calibration/pjm_debugb_inputclock_A --year 2023 2024 2025 \
  --out-dir results/calibration/pjm_headctrl_k162
```

Training years only. **No `--holdout-authorized`, no held-out year, no locked-test year.**
Differenced against the keeper's committed `hourly/` sidecars
(`class_hourly_*`, `system_*`).

**Pre-registered read, fixed now:**

| series | INERT if | LIVE if |
|---|---|---|
| system mean zonal **price** | \|Δ\| < 0.05 % | ≥ 0.05 % |
| **demand**, **slack**, **dump** | bit-identical | any difference |
| **total generation** | \|Δ\| < 0.01 % | ≥ 0.01 % |
| worst **per-class annual energy** | \|Δ\| < 0.5 % | ≥ 0.5 % |

These are the NEISO measurement's own thresholds, set at roughly an order of magnitude above
what degenerate-LP tie-breaking produced there (−0.008 % on price; bit-identical demand /
slack / dump; 0.17 % worst class). They are declared here so the verdict is not chosen after
seeing the numbers.

**What the control can and cannot do.** It can only establish whether the in-sample-vs-holdout
comparison in the touchpoint assessment is like-for-like. It **cannot** promote anything, it
is not a screen, it produces no keeper, and it changes no determination. If drift is measured
LIVE, the touchpoints' §4(i) open limit hardens into a stated confound and the held-out
numbers are re-read against the control column rather than against the keeper's committed one.

## 4. Phase-0 (zero-LP) work, declared complete before the LP starts

Every number in the accompanying FINDING is computed from **committed artifacts only** — the
bench sidecars, the keeper's and the touchpoint's committed `hourly/` files, the EIA-923
delivered-price parquet and the EIA-930 hourly extract. No LP was solved to produce any of
it, and none of it depends on the control's outcome.

## 5. Governance

- PJM holds `complete`; the holdout freeze is scoped to `locked_test` alone. **No held-out
  year is solved in this session** — the control is 2023–2025 — so no marker is spent and the
  rule-22 registration gate is not engaged.
- `final` is **not** granted to PJM. 2019 and H1-2026 are untouched.
- Keeper **UNCHANGED**. No promotion, no re-key, no `calibration-complete.json` edit.
- Matrix (rule 28 b): no mechanism is tested, so no cell verdict moves. The
  `da_virtual_bids` cell stays **`K`** — see FINDING §3, which **re-measures** an
  already-adjudicated and owner-escalated item rather than re-opening it.
