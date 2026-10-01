# FINDING — ercot-203: RTOFFPA is NOT a component of the Real-Time Settlement Point Price. The committed adder overlay is COMPLETE for the scoring basis; the object is CLOSED.

**Session ercot-203 (filed `203b` — see the shorthand note in §6), 2026-08-15, branch
`claude/ercot-203-rtoffpa-completeness-v8e324`, assembled at `origin/main` `315a245` and
rebased onto `633d12f`.** Dispatched to resolve the protocol gate the
ercot-202 (T-3b) audit named as its one open ask
(`docs/FINDING-ercot202-t1-nonviable-2026-08-14.md` §3 limit 1, §4 item 3(a)), and — only
on a YES — to charter an RTOFFPA overlay leg.

**THE GATE RETURNED NO. NO MECHANISM WAS CHARTERED, NO `ScenarioConfig` FIELD WAS ADDED,
NO LP WAS SOLVED, NO YEAR WAS SCORED, NO RUN WAS REGISTERED, THE KEEPER WAS NOT TOUCHED.**
*(The ERCOT keeper did change during this session's lifetime — to
`2026-08-14-ercot202-arm-plantphysics` — but by a concurrent lane, not by this session,
which read and wrote no keeper, registry or bench file. Nothing in this finding depends on
which run is designated: it is a protocol reading, and no run was solved or scored.)*
Per the dispatching prompt's Phase-0 instruction — *"If RTOFFPA is NOT in RTSPP -> the
audit's answer is 'the overlay is complete for the scoring basis'. CLOSE the object, stamp
the record, and STOP. That is a full, successful outcome — do not go looking for a lever to
replace it."* — the object is closed and no substitute lever was sought, prepared or
evaluated.

---

## 1. THE DETERMINATION, STATED FIRST

**RTOFFPA does not enter the Real-Time Settlement Point Price. It prices Off-Line reserve
*capacity* through a separate settlement stream — the Ancillary Service imbalance payment
of Nodal Protocol §6.7.5 — and never energy.**

Therefore the ercot-202 magnitude table ($0.5843 / $0.1522 / $0.0326 per MWh of unapplied
`rtoffpa` in 2023/2024/2025) measures content that is **absent from both sides of the
comparison**: it is not in the model price, and it is not in the ERCOT actuals the model is
scored against either. Adding it would not have completed the overlay — it would have
**broken** it, by inserting into the model price a component the benchmark price does not
contain.

The correct reading of the ercot-202 audit is therefore inverted from the one its own
framing invited: **the overlay reads exactly the published adder columns that belong in the
scored basis, and RTOFFPA is not one of them.**

**This determination is not new to the record — it re-derives, from primary sources, a
conclusion the repo already held.** `docs/FINDING-ercot198-t3b-adder-overlay-audit-2026-08-14.md`
§1 — the *other* T-3b execution, committed one day before ercot-202 — states it outright:
*"there is no third settled adder; **RTOFFPA** (published in the same report) is not part of
energy settlement and is excluded (measured anyway: 0.178 $/MWh dw 2024, 0.010 2025)."*
ercot-202 reached the opposite framing without citing it. §4.1 below reconciles the two and
records which one stands.

### 1.1 The basis, component by component

| published adder | in RTSPP? | how the model represents it | status |
|---|---|---|---|
| RTORPA (On-Line Reserve) | **YES** (§6.6.1.1) | **endogenous by design** — reserve-balance dual under `energy_reserve_coopt`; overlaying it would double-count (rule 19 `[R-ONE-MECH]`) | in basis; **the design is right, but ercot-198 measured the endogenous analogue at ≈ 0 — see §4.1. NOT this session's object** |
| RTORDPA (On-Line Reliability Deployment) | **YES** (§6.6.1.1) | **overlay** — `ercot_rtordpa_overlay_series`, verified equal to the published series (ercot-198, max abs diff 0.0) | in basis, carried, correct |
| RTOFFPA (Off-Line Reserve) | **NO** (§6.7.5 only) | **not represented — correctly** | **CLOSED: out of basis** |

Read precisely: what this session closes is that the overlay is **not missing a published
adder column**. That is exactly the question T-3b asked and the only one a protocol citation
can settle. It is *not* a claim that the model reproduces the full published adder content
of RTSPP — §4.1 records the open item that does bear on that, and it is RTORPA's, not
RTOFFPA's.

---

## 2. THE PROTOCOL CITATION (verbatim, with section numbers)

Source documents, downloaded from the ERCOT Protocol Library
(`https://www.ercot.com/mktrules/nprotocols/library/<year>`) and read directly — the
by-section Nodal Protocols, Section 6 (*Adjustment Period and Real-Time Operations*):

| effective | archive | Section 6 document |
|---|---|---|
| 2023-07-01 | `July 1, 2023 Nodal Protocols.zip` | `06-070123_Nodal.docx` |
| 2024-12-01 | `December 1, 2024 Nodal Protocols.zip` | `06-120124_Nodal.docx` |
| 2025-08-01 | `August-1-2025-Nodal-Protocols.zip` | `06-080125_Nodal.docx` |
| 2025-12-05 (RTC+B go-live) | `December-5-2025-Nodal-Protocols.zip` | `06-120525_Nodal.docx` |

The quotes below are from `06-120124_Nodal.docx`; **§2.5 verifies they are identical in the
2023 and pre-RTC-2025 versions**, so the determination covers the whole 2023–2025 training
span rather than one snapshot.

### 2.1 §6.5.7.3(12) — the adder-to-price mapping (THE decisive sentence)

> "(12) For each SCED process, ERCOT shall calculate a Real-Time On-Line Reserve Price
> Adder and a Real-Time Off-Line Reserve Price Adder based on the On-Line and Off-Line
> available reserves in the ERCOT System and the Operating Reserve Demand Curve (ORDC). …
> In addition, for each SCED process, ERCOT shall calculate a Real-Time On-Line Reliability
> Deployment Price Adder. **The sum of the Real-Time Reliability Deployment Price Adder and
> the Real-Time On-Line Reserve Price Adder shall be averaged over the 15-minute Settlement
> Interval and added to the Real-Time LMPs to determine the Real-Time Settlement Point
> Prices.** … An Ancillary Service imbalance Settlement shall be performed pursuant to
> Section 6.7.5, Real-Time Ancillary Service Imbalance Payment or Charge, to make Resources
> indifferent to the utilization of their capacity for energy or Ancillary Service
> reserves."

The paragraph computes **all three** adders in one breath and then routes **exactly two**
of them into RTSPP. The Off-Line adder is computed and sent to §6.7.5, not to the price.

### 2.2 §6.6.1(1) — the same statement at the head of the settlement-price section

> "(1) Real-Time energy Settlements use Real-Time Settlement Point Prices that are
> calculated for Resource Nodes, Load Zones, and Hubs. … an administrative price floor of
> -$251/MWh will be applied to Real-Time Settlement Point Prices **after adding the sum of
> the Real-Time On-Line Reliability Deployment Price Adders and the Real-Time On-Line
> Reserve Price Adder**."

### 2.3 §6.6.1.1(1) / §6.6.1.2(1) — the formulas

Resource Node:

> "(1) The Real-Time Settlement Point Price for a Resource Node Settlement Point is the
> time-weighted average of the sum of the Real-Time LMPs, Real-Time On-Line Reliability
> Deployment Price Adders, and the Real-Time On-Line Reserve Price Adders. …
>
> `RTSPP = Max (-$251, ((RNWF y * (RTLMP y + RTORPA y + RTORDPA y))))`"

Load Zone — **the ERCOT scoring basis' own settlement point class**:

> "`RTSPP = Max (-$251, ((TLMP y * LZLMP y) / TLMP y) + RTRSVPOR + RTRDP)`
> Where: `RTRSVPOR = (RNWF y * RTORPA y)` … `RTRDP = (RNWF y * RTORDPA y)`"

The energy-weighted Load Zone variant (§6.6.1.2(2), `RTSPPEW`) carries the same two terms.
Hubs (§6.6.1.3) resolve through §3.5.2 Hub Definitions onto the same bus LMPs plus the same
two adders. **`RTOFFPA` appears in none of these formulas.**

### 2.4 §6.7.5 — RTOFFPA's ONE and ONLY use in all of Section 6

> "(1) Based on the Real-Time On-Line Reliability Deployment Price Adders, Real-Time On-Line
> Reserve Price Adders and a Real-Time Off-Line Reserve Price Adders, ERCOT shall calculate
> Ancillary Service imbalance Settlement, **which will make Resources indifferent to the
> utilization of their capacity for energy or Ancillary Service reserves**, as set forth in
> this Section.
>
> (7) … `RTASIAMT q = (-1) * [(RTASOLIMB q * RTRSVPOR) + (RTASOFFIMB q * RTRSVPOFF)]` …
> Where: … **`RTRSVPOFF = (RNWF y * RTOFFPA y)`** … `RTASOFFIMB q = RTOFFCAP q - (RTASOFF q
> + RTNCLRNSRESP q)`"

`RTOFFPA` multiplies `RTASOFFIMB` — an **Off-Line reserve *capacity* imbalance in MWh**,
built (§6.7.5(7)) from `RTOFFCAP = RTCST30HSL + RTOFFNSHSL + RTNCLRNSCAP`, i.e. the
telemetered HSLs of resources with an **`OFF` status that can cold-start in 30 minutes**,
resources with an **`OFFNS`** (Off-Line Non-Spin) status, and non-controllable Load Resource
Non-Spin capacity. These are, by definition, resources **producing no energy** in the
interval. RTOFFPA prices the option they hold, not electricity they deliver.

**Textual completeness check.** `RTOFFPA` occurs **exactly twice in the whole of Section 6**
(the formula line and its variable-definition row), both inside §6.7.5 — verified by string
count on each of the 2023, 2024 and 2025 documents (§2.5). There is no third occurrence
anywhere in the section that defines settlement prices.

### 2.5 The determination holds across the entire 2023–2025 training span

String-level verification on each downloaded Section 6:

| Section 6 | Resource-Node RTSPP formula | Load-Zone RTSPP formula | `RTOFFPA` count | §6.5.7.3(12) sentence |
|---|---|---|---|---|
| `06-070123` (2023) | `Max(-$251, RNWF*(RTLMP + RTORPA + RTORDPA))` | `… + RTRSVPOR + RTRDP` | 2 (both §6.7.5) | present |
| `06-120124` (2024) | identical | identical | 2 (both §6.7.5) | present |
| `06-080125` (2025 pre-RTC) | identical | identical | 2 (both §6.7.5) | present |
| `06-120525` (RTC+B) | `Max(-$251, RNWF*(RTLMP + RTRDPA))` | `… + RTRDP` | **0** | replaced |

**The RTC+B row independently validates the overlay's own regime gate.** On 2025-12-05
RTC+B retired the adder regime: `RTOFFPA` vanishes from Section 6 **entirely** and RTSPP
reduces to LMP + the Reliability Deployment Price Adder for Energy. `scarcity.py` cuts the
overlay at `RTCB_GOLIVE_HOUR = 338 * 24 = 8112`, which on the model's non-leap 8760 clock is
**2025-12-05 00:00** — the exact effective date of the `06-120525` revision. The gate lands
on the protocol boundary to the hour.

---

## 3. THE INDEPENDENT EMPIRICAL CHECK (measured data, no LP)

The protocol citation is the load-bearing evidence. It was corroborated against the measured
series alone by `scripts/probes/ercot203_rtoffpa_basis.py`
(→ `results/calibration/ercot203_rtoffpa_basis.json`), which decomposes the **measured**
settlement price we score against — `HB_HUBAVG` from
`data/raw/lmp-data/RTMLZHBSPP_<year>.zip`, ERCOT's *Real-Time Market Load Zone and Hub
Settlement Point Prices*, i.e. RTSPP itself — onto the published adders and the SCED
`system_lambda` from the same NP6-905-CD parquet the overlay reads.

**All-hours basis identity, mean absolute residual ($/MWh) — the robust leg:**

| candidate decomposition of measured RTSPP | 2023 | 2024 | 2025 (pre-RTC+B) |
|---|---|---|---|
| `system_lambda` only | 4.953 | 2.862 | 2.853 |
| **`+ RTORPA + RTORDPA`** (the protocol reading) | **3.971** | **2.744** | **2.763** |
| `+ RTORPA + RTORDPA + RTOFFPA` (the alternative) | 4.277 | 2.820 | 2.797 |

Adding the two protocol adders **improves** the identity in all three years; adding RTOFFPA
on top **degrades** it in all three. Three independent years, same ordering, matching the
citation.

**Three honest limits on the empirical leg, so it is not over-read:**

1. **It is corroboration, not proof.** The residual is not zero even under the protocol
   reading (MAE $2.7–4.0/MWh) because `HB_HUBAVG` carries congestion that `system_lambda`
   does not, and because 15-minute prices are averaged to the hourly clock. What the test
   reads is the **ordering**, not the level.
2. **Only MAE discriminates; the signed mean does not.** All adders are non-negative, so
   adding any of them mechanically drives the signed residual more negative. The signed
   column is reported in the JSON for completeness and carries no evidential weight.
3. **The scarcity-hour subsets are directionally consistent but noise-dominated**, and the
   least-squares attribution is **uninformative** — it was designed as an indicative leg and
   did not survive its own diagnostic. `RTOFFPA` is never live while `RTORPA` is dark
   (0 such hours in 2023, 2024 and 2025), and the two are collinear at
   r = 0.948 / 0.993 / 0.996, so the fitted loadings (e.g. 2024: −2.78 on RTORPA, +4.64 on
   RTOFFPA) are collinearity artifacts and are **not** cited as evidence either way. On the
   `rtoffpa > 0` subsets, including RTOFFPA raises MAE in every subset of every year
   (2024: 12.82 → 14.45; 2025: 8.91 → 10.18) — consistent, but inside scatter of the same
   magnitude.

**One structural by-product worth keeping** (it also forecloses the Phase-1 rule-19
reconciliation had the gate gone the other way): across all three years there is **not one
hour** in which `rtoffpa > 0` while `rtorpa = 0`. An RTOFFPA overlay leg could therefore
never have fired in an hour where the endogenous reserve dual was not already active — it
would have stacked a second measured reserve adder on top of the mechanism that already
prices those hours, which is a rule 19 `[R-ONE-MECH]` double-count on its face.

---

## 4. WHAT THIS CLOSES, AND WHAT IT DOES NOT

**CLOSED.** The (T-3b) overlay-completeness object. The committed overlay carries every
published adder that enters the scoring basis; RTOFFPA is out of basis by protocol. The
ercot-202 finding's §3 limit 1 ("whether RTOFFPA belongs in the RTSPP scoring basis is NOT
settled by this audit") and §4 item 3(a) ("commission the protocol citation") are both
discharged by §2 above. **§4 item 3(b) is moot** — it was conditional on a YES ("*if*
RTOFFPA is in RTSPP, decide whether the fix belongs on the model side or the scoring
side"); with a NO there is no fix to place on either side, and in particular **T-3a is not
handed any new work by this session**.

### 4.1 THE RECORD CORRECTION — two T-3b executions disagreed; this settles which stands

T-3b was executed **twice**, by two lanes, on consecutive days, with **opposite** conclusions
about RTOFFPA:

| | ercot-198 (2026-08-14, `[FABLE]`, `claude/ercot-scar-t3b-adder-audit`) | ercot-202 (2026-08-14) |
|---|---|---|
| RTOFFPA | **excluded** — "not part of energy settlement"; measured anyway (0.178 dw 2024, 0.010 2025) | **the gap** — "the committed overlay is NOT complete… short by exactly one published component" |
| authority cited | 2024 SOM p. 43 (secondary) | none — flagged as its own open ask (§3 limit 1) |
| named live gap | **published RTORPA**, +0.237 $/MWh dw 2024 | RTOFFPA |

**ercot-198 stands; ercot-202's RTOFFPA framing does not.** §2's primary-source citation
confirms ercot-198's exclusion and upgrades its evidence from the SOM's summary ("the current
ERCOT market design features two distinct price adders") to the Protocol text that defines
the settlement price. ercot-202's §3 was honest about not having settled the question — it
labelled the ask as limit 1 and armed nothing — so what is corrected is a framing, not an
action: no artifact was built on it, and its measured magnitudes are arithmetically fine
(its simple-mean 0.1522 vs ercot-198's demand-weighted 0.178 for 2024 is the expected
weighting difference). The two lanes appear not to have seen each other's work; the
shorthand ledger for 198–203 is interleaved across branches, which is the likelier proximate
cause than either measurement being wrong.

**The live item on this object is ercot-198's, and this session did not touch it.** ercot-198
measured that the then-keeper's (`2026-08-12-run192-arm-coal-peak`) endogenous stand-in for
RTORPA — the ORDC total-family reserve dual, sidecar `ordc_adder` — is **≈ zero** (2 non-zero hours in 2024, max $0.15/h; 1 hour in
2025), so the published RTORPA content sits in bench `rt_lw_mon` and in **neither** the
scored `pMon` **nor** the overlay. Unlike RTOFFPA that is an **in-basis** quantity: §2 puts
RTORPA squarely inside RTSPP. But it is a **mechanism** question (why is the co-optimized
reserve dual dormant?), not an overlay-completeness one, and rule 19 `[R-ONE-MECH]` bars the
obvious shortcut of overlaying the published series on top of the mechanism that is supposed
to produce it. **It is out of this session's Phase-0 scope, was not investigated, and is left
exactly where ercot-198 filed it.** Nothing here charters it.

**DO-NOT-REDO (rule 28 discipline).** "Add the measured RTOFFPA to the ERCOT model price" is
now an adjudicated dead end with a primary-source citation. It must not be re-proposed as a
lever, in any lane, without new evidence at the level of a protocol revision. The one
condition that would reopen it does not exist and cannot arise retroactively: a protocol
amendment putting RTOFFPA into RTSPP, which would in any case apply forward from its
effective date, not to 2023–2025.

**NOT CLOSED / NOT TOUCHED.** Nothing else. This session did not test, arm, prepare or
evaluate any mechanism; it did not look for a substitute lever after the NO; and it neither
investigated nor chartered ercot-198's dormant-`ordc_adder` item (§4.1). ERCOT's board is
unchanged: **T-0** and **T-3a** remain the live card-T items, T-1 stays void on premise
(ercot-202), T-2 owner-gated (D2 freeze), T-4 refused (Q-B / R-A).

**FOR THE OWNER (nothing decided here).** Two items follow from §4.1, both recorded rather
than acted on: (a) ercot-202's §4 item 3 asked for a ruling on a gap that does not exist —
it can be closed as answered, and its "positive result" line read down; (b) ercot-198's
RTORPA finding is the one that survives on this object and has had no ruling — whether the
dormant reserve dual is worth a diagnostic lane is an owner call, and it is a mechanism
question (rule 19 bars overlaying the published series as a shortcut), not a T-3a scoring one.

---

## 5. RECORD STAMPS MADE BY THIS SESSION

1. **This finding** — the closure record with the verbatim citation.
2. **`scripts/probes/ercot203_rtoffpa_basis.py`** + `results/calibration/ercot203_rtoffpa_basis.json`
   — the read-only empirical corroboration.
3. **`scripts/data/fetch_ercot_ordc_reserves.py`** — the intake docstring's **silence on
   `rtoffpa` was the gate itself** (ercot-202 §3 limit 1). It is now filled: each of the
   three adder columns states its settlement role with its protocol section, so the next
   reader of the parquet cannot re-derive the same open question from the same silence.
4. **`src/market_sim/results/scarcity.py::ercot_rtordpa_overlay_series`** — docstring records
   that the overlay is **complete for the RTSPP basis**, with the citation and the
   RTOFFPA-is-out-of-basis adjudication.
5. **`docs/codebase-site/data/mechanism-matrix.js`** (`ercot_rtordpa_overlay` row note) and
   **`docs/codebase-site/data/mechanism-matrix/ERCOT.js`** (that cell's `ev` citation) —
   the completeness adjudication. **The cell verdict is UNCHANGED at `K`**: no mechanism was
   tested (rule 28(b) attaches to a mechanism test; a protocol gate that cancels the charter
   is not one), and **no row was minted** — no `ScenarioConfig` field was added, so rule
   28(c) is not engaged.
6. **`docs/calibration-log/ercot.md`** — the ercot-203 entry.

---

## 6. GOVERNANCE — WHAT THIS SESSION DID NOT TOUCH

**No solve, no score, no registration.** No LP was built; no year was solved; no run was
produced — so rule 15 `[R-DASHBOARD]` has nothing to register and rule 16 `[R-ALLYEARS]`
nothing to span. No precommit was pushed: the Phase-0 gate returned NO, so there is no A/B
to pre-register, and pushing a precommit for a solve that will never run would be a false
record. No DOF ledger entry — **no new field exists**; `n_residual` is untouched at 6.

**Rule 22 `[R-HOLDOUT]`:** ERCOT holds no `complete` and no `final` marker. Only
{2023, 2024, 2025} were read; nothing was solved or scored in any year; no
`--holdout-authorized` anywhere; no marker granted or spent. The probe hard-fails on any
year outside the training span by construction.

**Rule 13 `[R-MEASURED]`:** every measured series here is read for audit and attribution
only. None entered a model input, and the session's conclusion is that one of them
(`rtoffpa`) must **not** become one.

**Rule 1 `[R-STRUCT]`:** the determination is made entirely on market structure — what the
Protocols say the settlement price is — and not on any residual. No fit was consulted, and
none would have been admissible: had the gate returned YES, ercot-202 §3 limit 3 already
established the direction is not uniformly favourable.

**Standing rulings honoured, none re-litigated:** Q-B (no ERCOT C3a-2023 spend, final) —
2023 appears here only as a training-span year of the protocol verification and the basis
probe, never as a determination target. R-A (NOT-YET stands; no C3b-2023 round).
`energy_online_capability_cap` — ERCOT `R` (ERCOT-155/159), **not** armed, prepared or
considered as a substitute after the NO. ercot-195's L-SCAR L-1 non-identifiability not
re-tested. D2 composition freeze, T-0/T-2/T-3a/T-4 and `diurnal_price_amplitude` (`U`)
untouched. `gas_hh_monthly_shape` posture unchanged (ercot-202: armed and correct).

**Rule 25 `[R-ISO-SCOPE]`:** nothing crossed an ISO boundary. No other ISO's shard, keeper,
bench or registry was touched. The finding is ERCOT-specific by construction — it is a
reading of the ERCOT Nodal Protocols.

**Rule 27 `[R-PUSH]`:** no core file was bulk-rewritten. The two source edits are local
docstring edits pushed as exact on-disk bytes, blob-verified after push.

**P2 stays archived** — no P2 flag, no `--enable-legacy-p2`. **No new GitHub Actions
workflow** — private repo, billed minutes; all work ran in-session.

**Session consumed the ercot-203 shorthand, filed as `203b`. Next shorthand: ercot-205.**
*(Housekeeping: the ERCOT shorthand ledger is tangled across 198–205 — parallel branches
claim shorthands mid-session. `docs/calibration-log/ercot.md` carries ercot-202 → ercot-198
→ ercot-201 → ercot-202 in file order; ercot-198's entry declares "next: ercot-199";
ercot-202's finding §5 declares "next: ercot-198", already consumed, while its log entry
declares ercot-203; and **two lanes then took ercot-203 concurrently** — the rule-18
grain-repair successor, which landed first and promoted the keeper, and this one. This
session's log entry is therefore filed as `203b`, and since that lane declared ercot-204,
the next free shorthand after both is **ercot-205**. §4.1's duplicated T-3b execution is
the visible cost of the same tangle, one object-space earlier.)*

**Artifacts produced:** this finding; `scripts/probes/ercot203_rtoffpa_basis.py`;
`results/calibration/ercot203_rtoffpa_basis.json`; the two docstring stamps; the matrix
base-row note + ERCOT shard `ev`; the `docs/calibration-log/ercot.md` entry. Nothing else.
