# FINDING — capx D-18: the FR-24 invariant declaration ledger (records lane)

**Lane:** capx D-18 · **Model:** Opus · **Branch:** `claude/capx-d18-invariant-ledger-v6x8c2`
**Routed from:** `docs/handoffs/FINDING-capx-d4i3-ercot-slack-2026-08-31.md` §5.3 (R-6) — "a records
duty needing one owner, not a measurement question"
**Date:** 2026-08-31 · **Zero solves.** Every number below is read from a committed artifact or
printed by the checker at this HEAD.

**SCOPE.** This lane makes a standing-red CI job green by declaring what is already committed, and
corrects one misattributing line. **It adjudicates nothing and fixes no defect.** No threshold, no
scorer, no verdict file, no board block, no keeper / shard / marker, nothing in the backcast
namespace, and no `ScenarioConfig` field was touched (rule 28 not triggered). `cleared` and
`curated_subsets` are unchanged. Two files changed: this finding, and
`frontend/data/hindcast/invariant-failures.json`.

---

## 0. Headline

1. **The census re-derived here matches the charter and D4-I3 §5.3 exactly** — 13 undeclared runs
   carrying 15 undeclared FAIL idents, no discrepancy to reconcile (§1).
2. **All 13 are declared, and the job is GREEN** at the exact CI invocation (§2, §4).
3. **14 of the 15 idents point at a real, named record.** ONE — CAISO's 2021 I7 — is declared as
   **honestly untracked at root-cause grain**: the committed record *characterises* it (a property
   of the vintage-2020 seed fleet, reproduced across two FH-5 arms) but no lane owns why that seed
   fleet is 6,087 MW short. Writing "FR-3" on it would have been a fabricated attribution (§3b).
4. **`dominant_open_causes.I3` was misattributing two non-ERCOT rows and is corrected** — the open
   question is now named, and deliberately not answered (§5).

---

## 1. The census, re-derived — no difference from the charter

The charter's list was measured by D4-I3 and independently re-derived by the director. I re-derived
it a third time by running the checker at this HEAD (this container had no `numpy`/`pydantic`/
`scipy`/`highspy`; installed, then ran). **All three agree on exactly these 13 runs / 15 idents:**

| run id | undeclared idents | committed detail (verbatim from the sidecar) |
|---|---|---|
| `caiso-2021-2025-realized` | I7, I9 | 2021 accredited firm 44,070 < req 50,157 MW · simultaneous chg+dis 0.96 % (2021) / 3.24 % (2023) / 2.06 % (2024) / 0.88 % (2025) of throughput |
| `ercot-2021-2025-realized-t1h-d11r-control` | I3 | 2023 slack 0.01 % of load |
| `ercot-2021-2025-realized-t1h-d11r-exhaustion` | I3 | 2023 slack 0.06 % of load |
| `ercot-2021-2025-realized-t1h-d12c-armed` | I3 | 2023 slack 0.07 %; 2024 slack 0.02 % of load |
| `ercot-2021-2025-realized-t1h-d12c-control` | I3 | 2023 slack 0.01 % of load |
| `ercot-2021-2025-realized-t1h-refresh` | I3 | 2023 slack 0.02 % of load |
| `miso-2026-2030-s123-verify` | I3 | 2029 slack 0.02 %; 2030 slack 0.03 % of load |
| `neiso-2021-2025-realized-k99` | I6 | 2024: 23.1 % of thermal retired in one year |
| `neiso-2021-2025-realized-mystic-rescore` | I6 | 2024: 23.1 % of thermal retired in one year |
| `neiso-2026-2050-t3-golden-bau` | I3 | dump 2.17 % (2043) → 8.50 % (2050) of renewable potential |
| `pjm-2021-2025-realized-exante-control` | I7 | 2025 accredited firm 138,785 < req 139,850 MW |
| `pjm-2021-2025-realized-verified-exits` | I7 | 2025 accredited firm 138,286 < req 139,850 MW |
| `pjm-2026-2030-s6-ledger` | I7, I12 | 2028/2029/2030 firm 147,003/148,169/150,291 < req 150,263/153,001/155,946 MW · rm −11.7 / −12.6 / −13.0 % vs band [−9.7 %, 5.3 %] |

**One thing the census makes visible that the charter's ident list alone does not:** `I3` is a
**two-legged** invariant. `check_i3_unserved_dump` (`scripts/check_forecast_invariants.py:299-318`)
appends a problem for *either* slack/demand > threshold *or* dump/renewable-potential > threshold.
Five ERCOT rows and MISO trip the **slack** leg; `neiso-2026-2050-t3-golden-bau` trips the **dump**
leg and carries no slack breach at all. That is load-bearing for §5.

**No declaration was stale** — the checker's stale-entry branch (`:1019-1032`) fired on nothing,
before or after.

---

## 2. What was written

Thirteen entries appended to `declared_failures`, plus one `d18_note` carrying the per-row
attribution, plus the `dominant_open_causes.I3` rewrite (§5). Per `how_to_update`, each declaration
names the finding or lane it belongs to; per the file's own `purpose`, **none of this is
absolution** — every row remains an open root-cause finding (the file's own `purpose`, citing
rules 1/11; rule 1 `[R-STRUCT]` is the live one).

---

## 3. The 13 declarations and what each cites

### 3a. Rows pointing at a real record (12 runs, 14 idents)

**(a) Five ERCOT T1-H `I3` rows — FR-6, measured.**
`t1h-refresh` (W2-P5, `docs/hindcast-reports/ercot-2021-2025-realized-t1h-refresh-2026-08-22.md`);
`t1h-d11r-control` + `t1h-d11r-exhaustion` (lane capx D11-R,
`docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md`);
`t1h-d12c-control` + `t1h-d12c-armed` (lane capx D12-C,
`docs/handoffs/FINDING-capx-d12c-confirm-pair-2026-08-30.md`).
Cause is the standing FR-6 energy-only scarcity slack — the adequacy backstop is disabled for ERCOT
by market design (`resolve_reserve_margin_build_enabled` returns `False`;
`model/capacity_evolution/adequacy.py:396-426`, whose docstring now names FR-6 and D4-I3
explicitly), so a one-pass under-build has no corrective and lands as LP slack at VOLL. D4-I3 §2
measures 2023 slack **monotone in the year's added GW** (zero at ≥48.0 GW, 0.01 % at 39.9 GW,
0.07 % at 27.8 GW) — an under-build signature, not a curve artifact — and §4 **pre-declared** the
d12c arm's ~7× worsening as the correct consequence of two levers that remove build volume by
design. The declaration carries D4-I3 §5.1's hazard forward: `refresh` (2026-08-22 vintage) and the
four 2026-08-30 records share cache key `28cef3500ec1fd9e` yet disagree on three scored quantities,
so **these magnitudes are comparable only within a solve vintage.**

**(b) PJM `exante-control` + `verified-exits` `I7`.** Declared to the W2-P5 A/B report,
`docs/hindcast-reports/pjm-2021-2025-realized-verified-exits-2026-08-22.md`, § "Invariant
side-effect of the coal knock-on": the pair FAILs in **both** arms, so neither is introduced by the
verification mechanism. The control's 138,785 MW is the same RC-1B nuclear-phantom chain already
recorded for `k162` in the ledger's `post_clear_note` (identical number). The treated arm's extra
~499 MW traces to the **+5.290 GW of 2024 coal** the screen retires once the phantom stops masking
it. That report names **PJM's coal economic screen** as the open defect and deliberately does not
chase it.

**(c) NEISO `k99` + `mystic-rescore` `I6`.** One event declared twice — the rescore reproduces the
k99 solve against corrected Mystic-inclusive actuals. Root cause in
`docs/hindcast-reports/neiso-2021-2025-realized-k99-2026-08-19.md`: an **over-fire of the economic
retirement screen concentrated in `gas_cc`** (+3562 %, 86 % of the 5.92 GW false-retire) while
`gas_ct` and `oil` are −100 % — the screen retires the *wrong fuel*, and I6 is that same event in
the time domain. That report states explicitly that **FR-4's headline framing does not explain it**
(this run executes `retirement_rule="pipeline"` and the over-fire reproduces there, matching the
FH-1 signature); the open lane is the retirement screen itself.
*Incidental:* the k99 report already asserted "**I6 FAILs and is declared**" — that claim was
**false until this commit** and is now true. No report text was edited.

**(d) MISO `s123-verify` `I3`.** Five-step measured mechanism in
`docs/handoffs/FINDING-capx-s123-miso-adequacy-2026-08-30.md` §5, with the per-year table (2029:
145,993 MWh, 31 h, peak 14,568 MW; 2030: 231,272 MWh, 58 h, peak 17,329 MW). The S-123 package
closed MISO's I7 and the FC-1 failure **moved** to I3 rather than clearing — that finding states it
as its own result and routes a named follow-up. **Not FR-6.**

**(e) NEISO `t3-golden-bau` `I3`.** The **dump** leg,
`docs/handoffs/FINDING-capx-t3-neiso-golden-2026-08-30.md` §6.3(2), reported at full magnitude as
the model's own consequence of **zero storage entry in all 25 years** against a 9× VRE buildout.
**Not FR-6.**

**(f) PJM `s6-ledger` `I7` + `I12`.** Per-year ledger in
`docs/handoffs/FINDING-capx-s6-pjm-ledger-2026-08-30.md` §5; §5.3 records that I12 **newly FAILS**
(three consecutive band excursions — the chain length at which I12 stops being a WARN) and takes
FC-2 with it.

**(g) CAISO `I9`.** The program's storage ε-tiebreak degeneracy item,
`docs/forecast-development-plan-2026-07.md` §1.2-8 ("storage ε-tiebreak degeneracy at high
penetration (I9, CAISO →5.8 % of throughput)"), routed to lane **FF-3C item 2**. Stated honestly:
that is a **conditional lane** whose trigger includes "I9/I10 FAILs persisting at T1" and it has
**never been run** — so the mechanism is *named* and the diagnosis is *not yet done*. Corroborated
independently by `docs/handoffs/fh-5-phase-b-2026-08-11.md` §8.6, which records CAISO
storage-integrity FAILs at the same grain across both FH-5 arms.

### 3b. The one row declared as honestly untracked — CAISO 2021 `I7`

`caiso-2021-2025-realized` I7 is the **2021 seed year only**: accredited firm 44,070 < requirement
50,157 MW. The run's own W2-P5 report
(`docs/hindcast-reports/caiso-2021-2025-realized-2026-08-22.md`) discusses storage entry, the
backstop ratchet and the Diablo Canyon false-retire — **and never mentions this row**. The only
committed record that does is `docs/handoffs/fh-5-phase-b-2026-08-11.md` §8.6, which reproduces the
*identical* pair across two FH-5 arms and reasons that this is "expected rather than suspicious:
accredited firm capacity is a property of the 2021 seed fleet, and the arms differ only in gas path,
weather posture and demand vintage, none of which changes the vintage-2020 starting fleet" —
"reported and left standing".

**That is a characterisation, not a root cause.** It explains why the number is *invariant across
arms*; it does not explain why the seed fleet is **6,087 MW short of its requirement**. The obvious
attribution — `dominant_open_causes.I7`'s FR-3 hydro term — would have been **wrong to write
unqualified**: FR-3 is recorded CLOSED by FFR-1C, which moved CAISO's T0-2026 I7 from −11,201 to
−6,577 MW and filed the *residual* as an open item, and those are 2026 forecast arms, not this
2021-2025 hindcast row. So the declaration says exactly that: the family residual is FR-3-adjacent,
**no lane owns why this seed fleet is short**, and the row is registered by W2-P5 with its cause
untracked. Per the charter, an honest "registered by lane X, cause untracked" is the correct entry.

---

## 4. TASK 3 — the checker, GREEN

Run at this HEAD, at the **exact** invocation `.github/workflows/ci.yml` uses (the job passes
`--sidecar-dir` with no value and relies on its default):

```
$ python3 scripts/check_forecast_invariants.py --sidecar-dir
forecast-invariant artifact audit: 28 sidecar(s) with an invariants block, 392 record(s), 19 FAIL(s) declared
forecast-invariant artifact audit OK
$ echo $?
0
```

Identical output with the explicit path form the charter quotes:

```
$ python3 scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast
forecast-invariant artifact audit: 28 sidecar(s) with an invariants block, 392 record(s), 19 FAIL(s) declared
forecast-invariant artifact audit OK
```

**Before this commit** the same command emitted 13 problem lines and exited non-zero. **No change
outside this charter was needed** — the job goes green on declarations alone.

19 = the 4 pre-existing declared idents + the 15 declared here. `declared_failures` now holds 17
entries.

---

## 5. TASK 2 — the corrected `dominant_open_causes.I3`

**Before:**

> `"I3": "FR-6 ERCOT energy-only scarcity slack, structural and unowned in code."`

That line reads I3 as an ERCOT-only phenomenon with a single cause. **Two committed non-ERCOT runs
now carry an I3 FAIL and FR-6 cannot explain either**: MISO and NEISO are capacity-market ISOs where
`resolve_reserve_margin_build_enabled` returns `True` (`adequacy.py:396-417`: `None` resolves ON when
`MARKET_DESIGN[iso].capacity_market`, OFF only for energy-only ERCOT and unknown ISOs), so the
adequacy backstop that ERCOT lacks **is armed** in both. And the NEISO row is not even the same leg
of the invariant — it is dump, not slack.

**After** (the line as written; the full text is in the file):

> `"I3": "unserved/dump — NOT one cause, and NOT ERCOT-only (corrected 2026-08-31, lane capx D-18).
> IN ERCOT the slack leg is FR-6: the adequacy backstop is disabled for energy-only ERCOT by market
> design … OUTSIDE ERCOT FR-6 CANNOT BE THE CAUSE: MISO and NEISO are capacity-market ISOs where the
> same resolver returns True and the backstop IS armed, so their I3 rows are a different mechanism —
> miso-2026-2030-s123-verify is a slack breach (2029/2030) whose measured chain is
> FINDING-capx-s123-miso-adequacy-2026-08-30.md §5, and neiso-2026-2050-t3-golden-bau trips the OTHER
> leg of the invariant entirely, out-year renewable DUMP … What actually drives each is OPEN and
> belongs to that ISO's own lane (rule 25 [R-ISO-SCOPE]); this line names the question and
> deliberately does not answer it."`

**Nothing is adjudicated.** The line names *what each row is* (which leg, which magnitude, which
committed finding measures it) and says the cause is open and each ISO's own lane's work under rule
25 `[R-ISO-SCOPE]`. It does not propose a mechanism for either.

---

## 6. Boundaries honoured, and one observation routed on

- **Owned only the 13 pre-existing rows.** Lane D4-M is dispatched in the same batch and declares
  its own new ERCOT T1-H row in its own registration commit; no other lane's line was re-declared
  or re-worded. `capentry_note`, `c1joint_note`, `wave1_note`, `ffr2b_note`, `post_clear_note`,
  `cleared` and `curated_subsets` are **byte-unchanged**.
- **No gate and no scorer behaviour changed.** No invariant threshold anywhere; no sidecar deleted;
  `scripts/check_forecast_invariants.py` untouched.
- **Zero solves.** Rule 28 not triggered — no mechanism proposed or tested, no `ScenarioConfig`
  field added, no matrix cell written (the ERCOT/CAISO/PJM/MISO/NEISO shards were not opened).
- **Rule 22 `[R-HOLDOUT]`:** no holdout year touched — this lane reads committed sidecars only.
- **No new GitHub Actions workflow.** The existing job is made to pass.

**One observation for the director, scoped and not acted on.** `.github/workflows/ci.yml`'s header
comment (line 27) still describes this job's standing red as "*three PJM runs with undeclared I7*"
— a snapshot from the pre-clear-out sidecar set that no longer describes what was red (13 runs
across five ISOs) and, as of this commit, describes nothing at all. It is a historical measurement
note inside a CI file; editing it is not required to make the job green and is outside this lane's
"correct one misattributing line" charter, so it is **left standing and routed** rather than
quietly rewritten.

---

## 7. Report to the director

- **Census:** re-derived independently; **matches the charter exactly** — 13 runs, 15 idents, no
  reconciliation needed.
- **Checker: GREEN** (§4), exit 0, at the exact CI invocation. Nothing outside charter was needed.
- **Declarations pointing at a real record: 14 of 15 idents** (12 of 13 runs) — FR-6 for the five
  ERCOT rows (measured by D4-I3 §§2/4/5.1), the PJM coal economic screen for the two W2-P5 PJM I7
  rows, the NEISO `gas_cc` retirement-screen over-fire for both I6 rows, and the per-lane findings
  for MISO S-123, NEISO T3-golden and PJM S-6.
- **Honestly untracked: 1 ident** — CAISO 2021 `I7`. Characterised in FH-5 Phase B §8.6 as a
  seed-fleet property, but **no lane owns why the vintage-2020 CAISO seed fleet is 6,087 MW short**.
  Declared as untracked rather than attributed to FR-3, which is recorded closed with its residual
  filed separately and on different (2026 forecast) arms.
- **A borderline call worth the director's eye:** CAISO `I9` is counted in the 14 because the
  program *names* its mechanism (ε-tiebreak degeneracy, plan §1.2-8) and *routes* it to FF-3C — but
  **FF-3C is conditional and has never run**, so nobody has diagnosed it. If the director prefers to
  count "routed but never worked" as untracked, the split reads **13 tracked / 2 untracked**.
