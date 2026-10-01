# FINDING — ercot-175: the offered-vs-deliverable wedge at SCED grain is MEASURED, fully licensed, and it is the RIGHT SIZE (0.93 × M at the median) but the WRONG SHAPE for any single admissible mechanism — **FILED-REDIRECTED** on the pre-registered rule (w_ramp/M p50 0.26 < 0.60); NO LP, no build, keeper UNCHANGED

**Session ercot-175, 2026-08-06.** Charter: the ercot-173 §1 re-pointing —
the SCED-grain wedge between the market's sub-$200 offered stack and what it
delivered at the 2023 missed tail hours — now that the full delivery-2023
NP3-965 corpus is on disk. Decision rules, licensing bars, the rule-13 line,
kill-gate assignment and predictions were pre-registered and pushed **before
any measurement**
(`docs/PRECOMMIT-ercot175-sced-deliverable-wedge-2026-08-06.md`); the kill
gates were PRECOMMIT-ercot172 §5 inherited verbatim and were **never
reached** (no arm was licensed). Keeper **UNCHANGED** at
`2026-08-05-run168b-year-curves`. **No run was solved, so none is
registered** (rules 15/16 — stated explicitly so the absence is not read as a
skipped registration). Record:
`results/calibration/ercot175_sced_wedge_phase0.json`; probe
`scripts/probes/ercot175_sced_wedge_phase0.py`.

---

## 0. Verdict

| | |
|---|---|
| **Licences** | L1 corpus **1.0000**; L2 HASL/HDL/Base Point all **1.0000**; L3 chain violations 0.46 % / 0.05 % (bars 0.90/0.90/0.05) — **fully licensed, all faces** |
| **Construction bridges** | M(h) reproduces the committed record (mean 3.3003 vs 3.3007 GW, p50 2.2131 vs 2.2165 — inside the 1 % stop bar); the committed V_r reproduces to **0.01 GW** on its own unclipped-10-step basis (56.52 vs 56.51 GW mean) |
| **Decision statistics** | w_ramp/M p50 **0.2621** (bar 0.60); s_ramp p50 **0.2928** (bar 0.60) |
| **Branch fired** | **2 — FILED-REDIRECTED**, exactly as pre-registered |
| **LP / mechanism** | **NONE** — no arm licensed, no owner adjudication sought, nothing built |
| **ercot-151 corpus blocker** | **DISSOLVED as a side effect** — the delivery-2023 corpus that lane was DATA-BLOCKED on now exists on disk (§5 owner item 7) |

## 1. The measurement (H123, the verdict-bearing set; H61 descriptive in the record)

Per 5-min interval, per ONLINE scope-S resource, the monotone min-chain
`O → min(O,HASL) → min(O,HASL,HDL) → min(O,HASL,HDL,BP)`, interval-mean per
hour, GW:

| step / term | mean | p50 | reading |
|---|---|---|---|
| **O** — sub-$200 offered (35-step, HSL-clipped) | 53.90 | 57.53 | the physical cheap stack |
| **W_AS** = O − min(O,HASL) | 1.00 | 1.05 | AS holdback intersecting the cheap stack |
| **W_RAMP** = after-HASL − after-HDL | 0.64 | 0.56 | ramp-unreachable this interval |
| **W_RESID** = after-HDL − delivered | 0.31 | 0.29 | 5-min congestion / dispatch economics |
| **D** — delivered sub-$200 (Base Point) | 51.95 | 55.28 | |
| **total wedge O − D** | **1.95** | **1.96** | vs the model's margin **M**: mean 3.30 / p50 2.21 |
| **wedge/M per-hour p50** | | **0.927** | the aggregate is almost exactly the margin |
| startable (OFFQS/OFFNS) sub-$200 offered | 0.93 | 0.77 | Base Point 0.03 — effectively undelivered |
| model AS holdback H_model (withheld families) | 3.96 | 3.79 | **already larger than W_AS**; W_AS − H_model p50 = **−2.87** |
| AS awards on online-S thermal | 3.20 | 3.22 | most holdback sits ABOVE the sub-$200 curve MW |

Per class (mean GW over H123): the wedge is spread thin — COAL W_AS 0.26 /
W_RAMP 0.30, CC 0.26 / 0.22, ST_GAS 0.45 / 0.10, CT 0.03 / 0.01. No class
carries a concentrated defect; the largest single cell (ST_GAS W_AS 0.45) is
under a quarter of M's p50 on its own.

**A construction discovery bridging to the committed record**: the committed
V_r (56.5 GW mean) reproduces exactly on its own basis, and decomposes as
53.9 GW physical (35-step, HSL-clipped) + **~3.0 GW of sub-$200 curve-MW
above HSL** (offered on paper, not capability at the interval) − 1.45 GW
recovered in steps 11–35 that the 10-step read missed + ~1.0 GW startable.
The ercot-173 headline "V_r > V_m" was carried by non-physical above-HSL
curve MW: on the physical basis the market's cheap stack (53.9 + 0.9) is
slightly BELOW the model's V_m 55.2 GW — which sharpens, not weakens, the
ercot-173 refutation of the excess-depth premise (the model still does not
carry material excess cheap depth; ~0.4–1.3 GW at most, far below M).

## 2. The structural reading (rule 1) — what the wedge is and is not

* **Reality delivered its cheap stack.** D 51.95 GW mean vs the model's own
  dispatched sub-$200 ≈ V_m − M ≈ 51.9 GW mean — the *dispatched quantities
  agree almost exactly*. The 2023 missed-tail defect is a **marginal-price
  phenomenon, not a quantity phenomenon**: at the same ~52 GW of delivered
  cheap energy, reality's next deliverable MW priced $462 (p50) while the
  model's next MW prices <$200.
* **The wedge family is the right SIZE**: per hour, undelivered-cheap
  (W_AS + W_RAMP + W_RESID) covers **0.93 of M at the median** — "5-min
  deliverability" in aggregate is almost exactly the structure whose absence
  leaves the model its sub-$200 margin.
* **But it is the wrong SHAPE for any admissible single mechanism**: it
  splits AS 0.47 / ramp 0.26 / residual 0.13 (shares of M, p50). The
  pre-registered majority-plus-margin bar (0.60, twice) exists precisely so a
  minority term is not built and the rest tuned; no term comes close.
* **The AS term names no missing structure.** The model already withholds
  H_model 3.79 GW p50 — 2.87 GW MORE than reality's thermal sub-$200 AS
  wedge. ERCOT-102's refutation of the AS-holdout premise ("in place and
  slack") is corroborated here at unit-scoped SCED grain with a different
  instrument. The reserve family stays CLOSED; nothing to build, exactly as
  the precommit's §5 hard fence anticipated.
* **The ramp term is real but minority and mis-distributed for the object**:
  0.56 GW p50, concentrated NOT in the August evenings that dominate H123
  but in deep winter-morning misses (h704/h706 = Jan-30 08:00/10:00, W_RAMP
  2.8/2.2 GW — hours where M is 15–16 GW and no deliverability term could
  close the miss anyway). Arming `ramp_limits` on this evidence would be a
  minority mechanism for this object; the ERCOT cell stays `R` with the new
  evidence recorded.
* **The startable-RT fact corroborates the ercot-151 conduct
  identification**: OFF-startable resources carry only **~0.9 GW** of
  sub-$200 SCED offers at these hours (Base Point 0.03 GW), while the model
  hands the whole OFF-startable increment its cheap DAM-basis curves. The
  real market's cheap OFF depth does not exist *in RT conduct terms* — the
  marginal formation at the missed hours lives on the RT re-offer/start
  ladder the model's DAM-basis stack cannot see (the ercot-151 chartered
  lane), not in deliverability structure. This is measured corroboration,
  not a re-opening of the aggregate-depth premise (REFUTED, stands).

**The redirect, stated plainly**: after this measurement, the 2023 missed
>$200 formation is bounded away from (a) excess model depth (ercot-173,
sharpened in §1), (b) reserve-side/AS structure (ERCOT-102/107/108,
corroborated again), (c) any single deliverability term at SCED grain (this
session), and (d) the frozen ceiling lane (ercot-174 §3b). What remains
consistent with every committed measurement is the **marginal re-offer /
start-economics conduct at ~52 GW delivered** — the ercot-151
offline-increment re-pricing lane, whose sole blocker (the delivery-2023
corpus) has since dissolved. That lane already carries its own charter,
identification design and owner asks; it needs no new premise from this
session, only its standing owner authorization (§5 item 7).

## 3. Predictions adjudicated (all pre-registered, §9 of the precommit)

* **P-W** (total wedge p50 ≥ 2 GW): read **1.96 GW** — a 2 % near-miss of
  the stated figure; the substantive clause (a ~0 wedge would contradict the
  ercot-173 refutation) did not fire. Reported at full magnitude.
* **P-AS** (W_AS 2–6 GW; net unmodeled AS wedge small): the GROSS awards on
  online thermal read 3.2 GW (inside the band's logic) but W_AS against the
  sub-$200 block is only **1.05 GW** — the magnitude read MISSED because most
  holdback sits above the cheap curve MW; the directional clause is
  CONFIRMED and stronger than predicted (net wedge **negative**, −2.87 GW).
* **P-RAMP** (no magnitude claimed; evening concentration expected): the
  expectation was WRONG — the large ramp-wedge hours are winter mornings,
  not August evenings. Reported as such.
* **P-START** (GW-scale startable cheap offers expected from the ercot-151
  DAM analogue): **MISSED by an order of magnitude** (0.93 GW vs ~13.5
  GW DAM-instrument) — itself the informative fact of §2: cheap DAM curves
  of OFF units do not persist into RT SCED conduct at these hours.
* **P-L**: confirmed (all licences at 1.0000; HDL fully populated).

## 4. Kill gates

Not reached — no arm was licensed, no solve occurred. G-DOF is trivially
satisfied (zero scalars of any kind were created); every other inherited gate
requires a solved pair and is recorded **NOT REACHED**, per the ercot-174
precedent.

## 5. Owner items — filed, NOT decided (precommit §6, extended by this measurement)

1. The **ERCOT-148/149 ↔ double-count collision** (ercot-174 §3b) — ceiling
   lane FROZEN, untouched here.
2. The **finer-grain-wins variant**, named not built (ercot-174 §3b).
3. **ercot-172 fault 3** (multi-week plateau as hourly ceiling) — the sole
   remaining structural route to the 2024 object.
4. The **run168b keeper non-reproduction at HEAD** — re-key vs re-solve.
5. The **W_AS reconciliation** is RESOLVED by measurement rather than filed
   as an open question: the model over-withholds relative to reality's
   thermal sub-$200 wedge; no AS-side action exists.
6. **`ramp_limits` loader-path promotion**: NOT licensed by this Phase 0 on
   its own pre-registered bar (w_ramp/M 0.26). The ERCOT cell stays `R`; the
   winter-morning concentration is recorded as the only evidence pointing
   anywhere for a future ramp object.
7. **NEW — the ercot-151 lane is no longer data-blocked**: its §4 owner ask
   (1) (the delivery-2023 NP3-965 corpus) is satisfied by the corpus this
   session measured on; ask (2) (authorize the design round — the CC-tier
   widening + 2023 pool block + full-span A/B) is the standing owner gate
   and is THE recommended next ERCOT session, on this session's evidence.

## 6. Governance

Rule 15/16: no solve, no registration — stated in §0. Rule 22: 2023 only (a
training year); no out-of-training year read, solved or scored; no clean
partitions regenerated (no solve). Rule 13: HASL/HDL/Base Point were read
ONLY as measurement evidence; no model input was written (the precommit §5
line held — nothing was built at all). Rule 23: no derive touched. Rule 24:
no `ScenarioConfig` field added. Rule 25: ERCOT-scoped. Rule 27: every push
touching a ≥300-line file blob-verified (the probe, 422 lines, verified
sha256-identical post-push). Rule 28: matrix §5.1 gains **item 18**; the
`ramp_envelopes` ERCOT note is re-stamped with this outcome in the same
session; `check_mechanism_matrix.py` exit 0 and `node --check` on the matrix
JS before push.

**DO-NOT-REDO honoured in full** — the event-cap ceiling lane was not
entered; the depth premise was not re-litigated (it was sharpened by a
construction discovery, §1); the reserve family was not re-opened (its
closure was corroborated); no storage offer surface; no aggregate or
per-hour telemetered cap; no coal offer lane; West/Panhandle stayed closed;
ercot-172's C3 not attempted; the CC-headroom crosswalk stays
FILED-UNLICENSED.

**Not a keeper candidate.** Nothing was solved; the deliverable is the
licensed measurement, the branch adjudication, and the redirect to the
ercot-151 lane with its blocker dissolved.

**Next shorthand: ercot-176.**
