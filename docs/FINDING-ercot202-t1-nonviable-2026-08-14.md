# FINDING — ercot-202: card T option (T-1) is NON-VIABLE as chartered — `gas_hh_monthly_shape` is ALREADY ARMED on the ERCOT keeper

**Session ercot-202, 2026-08-14, branch `claude/ercot-202-gas-hh-shape-ab-3ldc3z`,
assembled at `origin/main` `d5a0b94`.** Dispatched to execute
`docs/DECISION-CARD-ercot196-shape-2024-2025-2026-08-13.md` card T option **(T-1)**
— arm the measured Henry Hub monthly shape as an input-correctness A/B against the
run192 keeper recipe — **with (T-3b)**, the published-adder overlay-completeness
audit, as its read-only companion.

**NO LP WAS SOLVED. NO YEAR WAS SCORED. NO RUN WAS REGISTERED. THE KEEPER IS
UNTOUCHED.** The A/B was not run because the pre-solve viability check disqualified
it: **the mechanism (T-1) proposes to arm is already armed in the keeper**, so the
chartered control and arm resolve to the same effective configuration and the A/B
has zero delta by construction. Per the dispatching prompt's standing instruction —
*"IF T-1 TURNS OUT NON-VIABLE, do not substitute a lever. Report to the owner and
stop"* — no lever was substituted and `energy_online_capability_cap` was **not**
armed, considered, or prepared.

Everything below is reproducible from committed artifacts by
`scripts/probes/ercot202_t1_viability.py` (output:
`results/calibration/ercot202_t1_viability.json`). Rule 13 `[R-MEASURED]`: every
measured series is read for audit/attribution only — none enters a model input.
Rule 22: only {2023, 2024, 2025} were read; no marker was granted or spent.

---

## 1. THE FINDING, STATED FIRST

Card T §4(T-1)(b) charters the A/B on the premise that the field is *"built and
default-off … currently unarmed"*, and card T §2(c) states the consequence it
draws from that premise:

> "The keeper prices ERCOT gas as one annual scalar (2024: 2.19, 2025: 3.52
> $/MMBtu) × the generic `GAS_MONTHLY_SEASONALITY` × the armed measured daily
> factors (`gas_daily_shape`, mean-preserving per month) — so the **measured
> month-to-month commodity shape never enters**."

**That premise is false.** The run192 keeper arms `gas_hh_monthly_shape`, and has
since the ercot-29 probe ladder. Three independent committed records agree:

| record | field | value |
|---|---|---|
| `results/calibration/ercot192_arm_B/meta.json` (solve-kwarg snapshot) | `gas_hh_monthly_shape` | **`true`** |
| same bundle `run_config.json` → `scenario_config` (**the RESOLVED config the LP ran**, rule 24 `[R-REGISTRY]`) | `gas_hh_monthly_shape` | **`True`** |
| `docs/codebase-site/data/mechanism-matrix.js:1886` (xiso-3 census, 2026-08-04) | `gas_hh_monthly_shape` | *"**ARMED ON THE ERCOT KEEPER**"* |

The keeper's resolved gas block in full: `gas_hh_monthly_shape=True`,
`gas_seasonality=True`, `gas_daily_shape=True`, `gas_monthly_actuals=False`,
`gas_price_override=2.54` (2023), `mode='backcast'`.

**The distinction the card missed is class-default vs keeper-value.** `scenarios.py`
ships the field `False` (*"Off by default (byte-identical)"* — its own docstring),
which is what "built, default-off" correctly describes. The ERCOT **keeper** passes
it `True` as a `solve_and_persist` kwarg. "Default-off" and "unarmed on the keeper"
are different statements; the record conflated them.

### 1.1 The zero-delta proof, through the seam the A/B would use

The chartered A/B is CONTROL = the run192 recipe replayed verbatim, ARM = the same
plus `--set gas_hh_monthly_shape=true`. Reconstructing both through
`scripts/replay_keeper.build_kwargs` — the exact seam the solves would use, with
`--set`'s dual-channel routing mirrored:

```
CONTROL  effective gas_hh_monthly_shape = True
ARM      effective gas_hh_monthly_shape = True
EFFECTIVE VALUES EQUAL?                   True
kwargs keys differing: ['prb_overrides']
  prb_overrides delta: gas_hh_monthly_shape: None -> True
```

The only difference the arm introduces is writing `gas_hh_monthly_shape: True` into
the `prb_overrides` channel — setting a value that is **already `True`** through the
explicit kwarg. It is a no-op on the solve. Running the chartered A/B would spend
two full-span ERCOT solves to produce two bundles identical in every dispatch,
price and gate, differing only in a recorded config key.

### 1.2 The mechanism itself is sound — it is the charter that is void

Arming is not in question; only whether arming is *new*. Measured against the
production code path (`data/fuel/trajectories.py::gas_seasonal_shape`), with the
committed series `data/raw/gas-prices/henry_hub_monthly.csv` present, the mechanism
is real, effective and clean on every count card T claims for it:

* **Complete measured coverage** — 12/12 months present for 2023, 2024 and 2025, so
  the `if not np.isnan(monthly).any()` fallback never fires.
* **Armed ≠ unarmed** in all three years (the measured shape genuinely replaces the
  generic one).
* **Exactly level-preserving** — the hour-weighted mean of the armed factors is
  `1.000000000000` (2024, 2025) and `0.9999999999999998` (2023, float rounding).
  This is what makes it carry **zero fitted scalars** (rules 20 `[R-DOF]` / 23
  `[R-FROZEN-DERIVE]`): the level stays the trusted annual pin, only the
  month-to-month shape is measured.

**A caution for any future session repeating this check**: with `data/raw/gas-prices/`
absent (e.g. an un-hydrated sparse checkout), `gas_seasonal_shape` silently returns
the **generic** shape for both armed and unarmed configs — the documented
missing-data fallback. An armed-vs-unarmed comparison run without the data present
looks byte-identical and would wrongly read as "the flag is inert". Hydrate first.

### 1.3 Card T §2(c)'s wedge, reproduced exactly — and what it actually measures

The probe reproduces card T §2(c) to the cent as `level × (measured − generic)`:

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **2024** ($/MMBtu) | **+0.65** | **−0.69** | **−0.75** | **−0.42** | +0.14 | +0.49 | −0.01 | −0.10 | +0.30 | +0.11 | −0.19 | +0.41 |
| **2025** ($/MMBtu) | +0.07 | **+0.31** | **+0.52** | +0.18 | −0.05 | −0.25 | −0.15 | **−0.44** | −0.20 | −0.15 | +0.09 | +0.10 |

(Card T reports Jan-2024 +0.65, Feb −0.69, Mar −0.74, Apr −0.42, Jun +0.50,
Dec +0.42; 2025 Feb +0.31, Mar +0.52, Aug −0.44. The arithmetic matches; the
Mar/Jun/Dec-2024 hundredths are rounding.)

**But the sign labels invert the model's actual state.** Card T reads Jan-2024
"+0.65 model-cheap" and Feb/Mar/Apr "model-dear", which is only true if the model
sits on the *generic* column. It sits on the *measured* column. The wedge is
therefore not a live model-vs-reality defect — it is the distance between the
keeper's actual state and a counterfactual the keeper is not in, i.e. **a measure of
what arming already bought, reported as if it were still owed.** The same wedge
appears in the field's own `scenarios.py` docstring (*"the generic shape holds
Feb/Mar-2024 ~$0.7/MMBtu too dear … and Jan-2024 $0.66 too cheap"*) — describing the
defect the field exists to fix, which card T §2(c) cites and reads as current.

Consequently card T §3's ledger line *"~$2–3/MWh in Feb from fuel shape (T-1)"* is
**not reachable reach** — it is already in the keeper's 2025 numbers.

---

## 2. HOW THE CLAIM PROPAGATED (so the correction lands at the source)

The record contains **both** the correct and the stale statement; the stale one was
carried forward verbatim in each session's "open owner rulings carried" block
without being re-checked against the keeper config.

**Origin (stale).** `docs/PRECOMMIT-ercot145-gas-daily-shape-2026-07-31.md` §1b:
*"Its admissible descendant is `gas_hh_monthly_shape` … built for exactly this
reason, **currently unarmed**, and **carrying no matrix row**"*, restated as §6 open
ruling 1.

**Carried verbatim** into `DIAGNOSIS-ercot146` §, `DIAGNOSIS-ercot147`,
`PRECOMMIT-ercot148` §5, `PRECOMMIT-ercot149` §5, and
`docs/calibration-log/ercot.md` lines 3520 / 3574 / 3817 / 3954 — then inherited by
`DECISION-CARD-ercot196` §2(c) / §4(T-1)(b) / §5 and its log entry (line 8038).

**Corrected in-record on 2026-08-04, but never back-propagated.** The xiso-3/xiso-4
cross-ISO census read the arming correctly and acted on it:

* `results/calibration/PREREG-xiso3-shared-stem-backlog-2026-08-04.md` #37 homes the
  field on `gas_daily_shape` — *"(`KKKKKK`, **ERCOT armed**)"*.
* `results/calibration/FINDING-xiso4-cross-iso-shared-stem-2026-08-04.md` adjudicates
  the same choice: *"`gas_daily_shape` is `KKKKKK` and **matches ERCOT's arming**,
  where `gas_monthly_actuals` reads `G`."*
* `mechanism-matrix.js:1886` records it as **"ARMED ON THE ERCOT KEEPER"**.

`mechanism-matrix.js` therefore contradicts itself: **line 1886** (correct, xiso-3)
against **line 779** and **line 1879** (stale, ercot-145b lineage). This session
corrects only those two stale notes; no cell verdict is touched.

### 2.1 The rule-28(c) "row gap" is ALSO stale — do not open a new row

Card T §4(T-1)(b) instructs the executing session to *"close that row gap when it
arms the A/B"*. **There is no gap.** The xiso-3 census registered the field
*literally* inside the `gas_daily_shape` row's `def` (the deliberate home-row
convention that census established), which is what rule 28(c) requires. Verified by
running the CI guard itself:

```
$ python scripts/check_mechanism_matrix.py
mechanism-matrix: integrity OK (docs/codebase-site/data/mechanism-matrix.js + 6 ISO shards)
mechanism-matrix: anchors checked (188 field + 48 row + 145 path; ...) — 0 unresolvable beyond the ratchet
mechanism-matrix: keeper stamps match every keepers/<ISO>.json
mechanism-matrix: §5.x prose headers match every keepers/<ISO>.json
  → exit 0
```

Minting a separate `gas_hh_monthly_shape` row would **break** the census convention
and duplicate a registered field. No row was added, and **no ISO shard cell was
edited** — this session tested no mechanism (rule 28(b) attaches to a mechanism
test; a viability check that cancels the test is not one).

---

## 3. (T-3b) THE PUBLISHED-ADDER OVERLAY-COMPLETENESS AUDIT — READ-ONLY, DELIVERED

Card T's companion asks: *does the committed RTORPA/RTORDPA overlay capture the full
published adder content of 2024/2025 RTSPP?* Card T §4(T-3b) budgeted *"one data ask
(month-grain published adder series, **not currently on disk**)"*.

**The data is on disk** — in the very artifact the overlay already reads. ERCOT MIS
report **NP6-905-CD** ("Historical Real-Time Price Adders by SCED Interval"), curated
by `scripts/data/fetch_ercot_ordc_reserves.py` into
`data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`, carries **all three**
published RT price adders as columns: `rtorpa`, `rtoffpa`, `rtordpa`. No data ask is
needed.

**ANSWER: the committed overlay is NOT complete. It is short by exactly one
published component — RTOFFPA, the Real-Time Off-Line Reserve Price Adder.**

`results/scarcity.py::ercot_rtordpa_overlay_series` reads
`columns=["hour", "rtordpa"]` only. Measured across `src/`, the columns any code
path actually consumes are **`['rtordpa']`**. `rtoffpa` appears in `src/` **only in
prose comments** (`retirements.py:1754`, `scenarios.py:2869`, `prior.py:70`,
`runner.py:3500`) — never as a data read. `rtorpa`'s absence is deliberate and
correct: the co-opt LP produces it endogenously via the reserve-balance dual, so
overlaying it would double-count (rule 19 `[R-ONE-MECH]`). **RTOFFPA has no
endogenous counterpart and no overlay — it is represented nowhere.**

Annual content, with the overlay's own RTC+B regime gate applied (2025 hours ≥ 8112
zeroed):

| year | `rtordpa` (APPLIED) | `rtoffpa` (**NOT applied**) | `rtorpa` (endogenous) | total published | RTOFFPA as % of applied |
|---|---|---|---|---|---|
| 2023 | 0.7496 | **0.5843** | 0.9453 | 2.2792 | **+77.9 %** |
| 2024 | 0.2293 | **0.1522** | 0.2029 | 0.5844 | **+66.3 %** |
| 2025 | 0.3709 | **0.0326** | 0.0606 | 0.4641 | +8.8 % |

($/MWh, simple hourly mean. The applied column reproduces card T §2(d)'s
demand-weighted +0.25 / +0.42 for 2024/2025 — demand-weighting lifts it slightly, as
expected where adders correlate with load.)

**The unapplied slice lands squarely in card T's named 2024 residual months** —
monthly mean $/MWh, `rtoffpa` against the applied `rtordpa`:

| 2024 month (card §1 squared-share) | `rtordpa` applied | `rtoffpa` unapplied | uplift |
|---|---|---|---|
| **Nov** (.271, largest) | 0.2284 | 0.2302 | **+101 %** |
| **Apr** (.189) | 0.6186 | 0.5076 | **+82 %** |
| **Aug** (.168) | 0.1766 | 0.4265 | **+242 %** |
| **May** (.153) | 0.1238 | 0.4108 | **+332 %** |

In 2025 it is near-inert except Jun (0.2876 vs 0.2389, +120 %) and Oct (0.0814 vs
0.2263, +36 %); **Feb-2025 — card T §2(d)'s largest basis month — carries
`rtoffpa` ≈ 0.0001, so the completeness gap does NOT touch it.**

**Three honest limits on this result, stated so it is not over-read:**

1. **Whether RTOFFPA belongs in the RTSPP scoring basis is NOT settled by this
   audit.** The repo's own intake header flags `rtorpa` as *"the ORDC on-line adder
   ERCOT folds into RTSPP"* and is **silent** on `rtoffpa`'s settlement role. Closing
   that needs the Nodal Protocols §6.6.3.2 / §6.5.7.5 citation. **This is the one
   real data/documentation ask T-3b produces** — and it is a protocol citation, not a
   series.
2. **The magnitudes are basis-consistency scale, not residual scale.** $0.15–0.58
   $/MWh annual against monthly residuals of $5–7 $/MWh. This is a correctness
   question, never a C3b lever.
3. **Its direction is not uniformly favourable**, which is exactly why it must not be
   chased. Adding adder content to the model price helps the months the model
   under-reads (Aug/Nov-2024) and **worsens** the months it over-reads
   (Apr/May-2024, the outage-season remainder). Under rule 1 `[R-STRUCT]` that is
   irrelevant to whether it is right — but it does mean nobody should expect a fit
   gain, and it must never be adopted *because* of one.

**Nothing was armed.** Adding RTOFFPA to the model price would be a new mechanism
needing its own charter, a rule-19 `[R-ONE-MECH]` reconciliation against the
endogenous reserve dual and the existing `ercot_rtordpa_overlay` (cell `K`), and the
protocol citation in limit 1. **No step was taken.**

---

## 4. WHAT THE OWNER IS ASKED TO DECIDE (nothing is decided here)

1. **(T-1) is void as written.** Card T's recommendation cannot be executed: its
   object is already in the keeper. The owner may wish to record T-1 as
   **withdrawn-on-premise** rather than tested — no mechanism was refuted, and the
   ERCOT `gas_hh_monthly_shape` posture is unchanged and correct.
2. **The shape queue is now one option shorter than card T states.** T-1 buys
   nothing further; T-4 stays refused (Q-B / R-A); T-2 stays owner-gated (D2 freeze).
   Of the card's board that leaves **T-0** and the **T-3a/T-3b basis pair** as the
   only live items. The card's §3 reach ledger should be read down accordingly —
   the "~$2–3/MWh in Feb-2025 from fuel shape" line is already spent.
3. **T-3b returns a positive result needing a ruling**: the committed overlay is
   incomplete by RTOFFPA (materially in 2023/2024, not in 2025). Whether that is a
   defect depends on the protocol question in §3 limit 1. Two separable owner calls:
   (a) commission the protocol citation; (b) if RTOFFPA is in RTSPP, decide whether
   the fix belongs on the **model** side (a new overlay leg — a mechanism, needing a
   charter) or the **scoring** side (T-3a's settlement-basis question, rubric-only).
4. **A record-hygiene question.** The stale "unarmed / no matrix row" claim survived
   ~6 documents over two weeks because "open rulings carried" blocks were copied
   forward without re-verification, while the correction (xiso-3) landed in a
   different lane and was never back-propagated. This session corrects the two
   self-contradicting `mechanism-matrix.js` notes; the owner may want the stale
   PRECOMMIT/DIAGNOSIS/log lines annotated rather than silently left standing (they
   are historical filings, so this session did **not** rewrite them).

---

## 5. GOVERNANCE — WHAT THIS SESSION DID NOT TOUCH

**No solve, no score, no registration.** No LP was built; no year was solved; no
run was produced, so rule 15 `[R-DASHBOARD]` has nothing to register and rule 16
`[R-ALLYEARS]` nothing to span. No precommit was pushed — there is no A/B to
pre-register. No DOF ledger entry — no new field exists (`gas_hh_monthly_shape` has
been in `ScenarioConfig` and in the keeper's ledger basis throughout; `n_residual`
is untouched at 6).

**Rule 22 `[R-HOLDOUT]`:** ERCOT holds no `complete` and no `final` marker. Only
{2023, 2024, 2025} artifacts were read; nothing was solved or scored in any year;
no `--holdout-authorized` anywhere; no marker granted or spent.

**Standing rulings honoured, none re-litigated:** Q-B (no ERCOT C3a-2023 spend, final)
— 2023 appears here only as a training-span year of the keeper's own config and the
adder audit, never as a determination target. R-A (NOT-YET stands; no C3b-2023 round).
ercot-195's L-SCAR L-1 non-identifiability — not re-tested, and none of its three
owner-decision routes taken. D2 composition freeze — untouched. T-2/T-3a/T-4 —
untouched. `diurnal_price_amplitude` stays `U`.

**Rule 28 `[R-MECH-MATRIX]`:** the matrix and the ERCOT shard were read before any
step. No cell verdict edited in any shard (no mechanism was tested). No row added
(§2.1: the field is already registered; CI green). The only matrix edit is the
factual correction of two stale base-file **notes** that contradict line 1886 of the
same file.

**Rule 25 `[R-ISO-SCOPE]`:** nothing crossed an ISO boundary; no other ISO's shard,
keeper, bench or registry was touched.

**P2 stays archived** — no P2 flag, no `--enable-legacy-p2`. **No new GitHub Actions
workflow** — this is a private repo and every runner-minute is billed; all work ran
in-session.

**The named structural successor `energy_online_capability_cap` was NOT armed,
prepared, or evaluated** — it is uncharted, is a structural LP change, and needs
owner authorization plus its own precommit and rule-19 reconciliation.

**Session consumed the ercot-202 shorthand. Next shorthand: ercot-198.**

**Artifacts produced:** this finding; `scripts/probes/ercot202_t1_viability.py`;
`results/calibration/ercot202_t1_viability.json`; the `docs/calibration-log/ercot.md`
entry; the two-note `mechanism-matrix.js` correction. Nothing else.
