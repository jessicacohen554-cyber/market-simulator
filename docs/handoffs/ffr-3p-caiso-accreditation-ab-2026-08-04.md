# FFR-3P addendum — the paired CAISO NQC arm, MEASURED

**Session.** FFR Wave 3, CAISO accreditation lane, branch
`claude/caiso-accreditation-ledger-lim6v5` — the session that built the incumbent
mechanism (`caiso_nqc_accreditation`, commit `7a0999b8`, PR **#3450**). Rebased
onto `origin/main` **`af82322e`**.

**This is an ADDENDUM, not a second findings document.** A parallel session was
dispatched on the same FFR-3P charter and its handoff
(`docs/handoffs/ffr-3p-caiso-accreditation-2026-08-04.md`, commit `ba518c64`) is
on `main`. **That document is the FFR-3P findings document and it is not
superseded, contradicted or duplicated here.** This addendum adds the one thing
it explicitly did not do — *"to MEASURE the arm (owner box; **not run here**)"* —
and corrects two claims of my own that never reached `main`.

**Nothing is tuned, promoted, armed or re-banded.** `caiso_nqc_accreditation`
stays **GATED DEFAULT-OFF**; no `ScenarioConfig` default moved; no holdout year
was approached; the freeze and both markers are as found.

---

## 1. What is measured

The two commands the incumbent handoff's reproduction block lists as *not run*:

```bash
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --out-dir results/ffr3p/caiso-control
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --caiso-nqc-accreditation --out-dir results/ffr3p/caiso-nqc-armed
```

Both cold, run concurrently (rule 12: two invocations, years sequential within
each), 14.1–14.2 min wall each, peak RSS 5.1 GB.

| arm | posture | resolved cache key | 2026 accredited firm | reserve position | Σ backstop MW | Σ additions MW | **FC-2 row 4** |
|---|---|---|--:|--:|--:|--:|--:|
| **control** | shipped | **`e5822277b72184f6`** | 50,729 | 0.8852 | 14,043.6 | 21,448.0 | **65.48 % FAIL** |
| **armed** | `--caiso-nqc-accreditation` | `ee0e448058d115aa` | **51,802** | **0.9040** | **12,731.6** | 20,136.0 | **63.23 % FAIL** |

`caiso_nqc_accreditation` is recorded under `scenario_config` in each leg's
`run_config.json` (rule 21).

### 1.1 The default-off gate's byte-identity is now measured, not asserted

The control's resolved key **`e5822277b72184f6` is the same key FFR-3H §1.1 and
FFR-3A-2 §2 recorded** — cold-solved at a different HEAD, in a different
container, with the new field present and unarmed. Together with the unmoved
pinned default `603c2498bf71d21d`, that is the empirical proof that adding the
field changed nothing at its default. Every published cell of the control
reproduces FFR-3H arm A exactly: backstop 14,043.6 MW, additions 21,448.0 MW,
share 65.48 %, RM path 1.80 / −3.12 / −0.31 / 12.35 / 15.28 %.

### 1.2 Both pre-registered predictions land

* **+1,072.6 MW** of 2026 accredited firm capacity was pre-registered in this
  session's mechanism commit before either arm ran. Measured: **+1,073**.
* **Reserve position 0.8852 → 0.9039** was predicted independently in the
  incumbent handoff §3.4. Measured: **0.9040**.

### 1.3 Zero invariant flips — the rule-14 contingency did not fire

I1/I2/I4/I5/I6/I8/I9/I10/I11/I13/I14 **PASS in both**. I3, I7, I12 **FAIL in
both, on the same years**. Retirements (2,615.3 MW), renewable builds
(5,404.4 MW), storage builds (0.0 MW) and CO2 are **identical to the digit**;
load-weighted price moves +$0.002/MWh in 2030 and is otherwise bit-identical.

I7's shortfall shrinks without clearing: 2026 −6,577 → **−5,504**, 2027 −9,243 →
**−8,170**, 2028 −8,001 → **−6,929**, 2029 −1,420 → **−186**. The 2029 gain
(+1,234 MW) exceeds 2026's (+1,073) because the VRE pool has grown — **the credit
responds to the model's own build even though its rate is flat.** What is
invariant is the rate, not the MW.

So nothing got worse, and the "if the accurate input makes a metric worse, keep
it and open the root cause" branch (rules 1/14) was never reached.

---

## 2. The finding that is not just a confirmation

### 2.1 The whole effect lands in 2030, because 2027–2029 are RATE-limited

| year | RM % control → armed | backstop MW control → armed |
|---|---|---|
| 2026 | 1.80 → **3.95** | 0.0 → 0.0 |
| 2027 | −3.12 → **−1.01** | 1,396.4 → 1,396.4 *(unchanged)* |
| 2028 | −0.31 → **1.74** | 2,792.8 → 2,792.8 *(unchanged)* |
| 2029 | 12.35 → **14.65** | 5,585.6 → 5,585.6 *(unchanged)* |
| 2030 | 15.28 → **15.34** | **4,268.8 → 2,956.8** |

2027–2029 do not move by a megawatt. FFR-3H §1.2 measured those years as exactly
the 2× growth ladder off the 0.6982 GW/yr EIA-860 `gas_ct` seed —
**rate-limited, not need-limited** — and a smaller gap in a ladder-capped year
buys nothing. 2030 is the single need-limited year, so the entire −1,312.0 MW
lands there.

### 2.2 This sharpens the incumbent handoff's ordering argument rather than confirming it

Its §3.4 recommends **B-1 (storage fleet vintage) first, this second**, partly on
the ground that arming the VRE credit *"would remove a sixth of the signal from
the next diagnosis."* **Measured, it does not.** It removes **2.25 pp of a
65-point share**, and it removes *nothing at all* from 2027, 2028 or 2029 — the
years where the backstop grinds and where a storage-vintage diagnosis would
actually read its signal. The B-1-first ordering is still the right call on
magnitude (storage is 90 % of the deficit, this is 16 %), but **the cost of
arming this first is much smaller than §3.4 assumed**, and the owner should weigh
the two on magnitude alone rather than on signal contamination.

Corollary: **−2.25 pp is a lower bound**, not an estimate. The same ledger
correction in a window where the growth ladder is not binding would be worth
more.

### 2.3 The honest headline

**This does not fix CAISO's backstop share.** 65.48 % → 63.23 %, still FAIL. It
is kept because it is CAISO's own published number in place of a generic
non-CAISO one (rule 14), **not** because of the 2.25 pp — and a session quoting
this arm as progress on BLK-10 would be misreading it.

---

## 3. Two corrections to my own claims — neither reached `main`

Stated explicitly because both appeared in this branch's commit messages before
the parallel session's Table 1.1 evidence arrived, and both are **wrong**. Neither
was ever merged: `main` carries only `7a0999b8` (the mechanism), whose registry
values and citations are unaffected.

1. **RETRACTED — "CAISO thermal is under-credited by +1,735.8 MW."** I argued
   from the CPUC QC methodology text (dispatchable resources at a Pmax test, no
   EFORd derate) plus per-unit spot checks where NQC equalled the EIA-860 *summer*
   rating. The incumbent handoff §2.2 settles it fleet-wide from Table 1.1:
   CAISO's published thermal credit is **29,979 / 31,433 = 0.9537** against the
   model's implied **0.9457** — the model is **0.8 % ABOVE** CAISO's own number,
   and switching to a 1.00 Pmax basis would **over-credit by ~1,978 MW**. My spot
   checks compared NQC against an already-ambient-derated summer rating and so
   could not see the ~4.6 % NDC→NQC haircut CAISO applies. **The estimate is
   correctly KEPT** and CAISO correctly stays out of
   `THERMAL_ACCREDITATION_BASIS_BY_ISO`. My figure was the size of the derate,
   not the size of an error.
2. **RETRACTED — "hydro is under-credited by ~+1,681 MW."** I inferred a
   dispatchable share from the ORNL-EHA/HILARRI `hydro-plant-modes` partition
   (86.5 % reservoir-class) and a name-keyword match on the NQC list (96.8 % of
   *matched* hydro NQC on `Dispatchable=Y`). Both are indirect, and the keyword
   match covered only ~4.1 GW of a ~6.3 GW published hydro NQC, so its 96.8 % is
   a share of the subset it happened to find. The incumbent handoff §2.1 measures
   the realized fleet-wide rate directly — **6,295 / 9,076 = 0.6936** — i.e. the
   model's 0.7041 is already **1.1 pp generous** on rate; what is short is the
   *fleet* (its B-2 pumped-storage caveat applies). **The class-split refinement
   is the wrong thing to prioritise**, exactly as §2.1 says.

The general lesson, worth carrying: **a fleet-wide published ratio beats an
inferred partition every time.** Both of my errors came from reasoning about
*which class a resource belongs to* when the ISO publishes *what the whole class
actually accredited*.

**Unaffected by these retractions**, because they rest on the CY2026 workbook
directly rather than on any partition: the solar/wind registry values (0.2096 /
0.2202, independently closure-checked against Table 1.1 to within 0.3 pp), the
derive, the tests, and §1–§2 of this addendum.

---

## 4. What this addendum does NOT claim

* **It does not re-adjudicate the base-year deficit.** That is the incumbent
  handoff's §1–§2 and §4, and it stands; §3 above defers to it on the two points
  where we disagreed and concedes both.
* **It does not recommend arming.** Owner decision D.1 (HOLD PROMOTION, FIND ROOT
  CAUSE) stands. §2.2 adjusts one input to that decision; it does not make it.
* **It does not claim the arm generalises.** −2.25 pp is measured on one
  five-year window in which three of five years are ladder-capped.
* **It does not re-score FC-2 row 4.** CAISO is FAIL before and after.
* **It does not register a run.** Both legs are labelled diagnosis probe arms,
  not keeper bundles and not program T1-F/T1-H runs, so neither the backcast
  registry (forbidden for forecast work, rule 15) nor `register_forecast_run.py`
  is touched — the FFR-3H §7 precedent. If the owner arms the mechanism, the
  resulting T1-F leg **is** a program run and belongs on the forecast dashboard.
  The committed evidence is the two `full_horizon_summary.json` +
  `run_config.json` sidecars; the ~24 MB of per-year parquet is deliberately not
  committed.
* **It does not touch another ISO.** The arm is verified inert in the other five
  (`test_rule_25_scope_caiso_only`); rule 25 holds.

---

## 5. Process note — seconding the incumbent handoff's B-9

Two sessions ran the same charter concurrently and both built the same mechanism;
mine landed first and the parallel session deleted its duplicate under rule 19.
**The waste was not symmetric and it was not only the duplicate code.** This
session also wrote a full findings document whose §3 reached the *wrong
conclusions on two of three candidates* — conclusions the parallel session had
already refuted from a document I had not found. That document is discarded
rather than merged; only this addendum and the retractions survive. Whatever
dispatches FFR lanes should check for an in-flight branch on the same charter id
before opening a second.

---

### Reproduction

```bash
uv sync                                    # ~2 min
uv run python scripts/regenerate_clean.py  # ~63 min; 49/50 datatypes succeed —
                                           # ira-credit-parameters writes its parquet
                                           # then aborts at teardown (exit -6), harmless

uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --out-dir results/ffr3p/caiso-control
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
    --golden-posture --caiso-nqc-accreditation --out-dir results/ffr3p/caiso-nqc-armed
```

Committed evidence: `results/ffr3p/{caiso-control,caiso-nqc-armed}/`
`full_horizon_summary.json` and `run_config.json`.
