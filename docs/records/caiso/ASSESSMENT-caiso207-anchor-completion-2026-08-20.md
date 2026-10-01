# ASSESSMENT — caiso-207: BOTH branches non-executable. Branch B (`caiso_ra_mpb_capacity_anchor`) was **COMPLETED IN FULL at FFR-4F on 2026-08-09** — re-verified at HEAD this session, mechanism live, seam reproduced to the dollar — and its absence from the forecast dashboard is the **deliberate `cccc911` retention sweep**, not a registration gap. Branch A stays rested. Keeper unchanged at `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET); the owner packet is now **TWO** items (2026-08-20)

**No solve. No probe. No LP was spent, no bundle produced, no dashboard
registration due.** Everything below is measured from already-committed
artifacts. **No mechanism was tested, so rule 28b does not attach and no cell
verdict moves** (the caiso-206 precedent, applied identically).

---

## §0 — THE HEADLINE, and it is a correction to this session's own charter

**The caiso-207 handoff nominated Branch B as "THE EXECUTABLE WORK". It is not
executable, because it is already done.** Every element of the deliverable the
handoff specifies was executed at **FFR-4F (2026-08-09)**, eleven days before
this session, and is verified intact at HEAD below:

| handoff deliverable | where it was executed | verified at HEAD this session |
|---|---|---|
| "pre-register the gate table BEFORE any solve" | FFR-4F §4 (P-1…P-3, committed in `ffr-4f: pre-register the paired FC-2 read`, which precedes both solves) | doc committed, pre-registration section intact |
| "A/B vs a zero-delta control" | FFR-4F §5, both arms cold, CAISO 2026–2030, 5 years sequential | both arms' slim artifacts committed under `results/ffr4f/`; control key `3d3e836a176ac9cd`, treated `da19509d457988e5` |
| "register on the FORECAST dashboard … NEVER the backcast registry" | FFR-4F §5.5, `register_forecast_run.py`, ids `caiso-2026-2030-ffr4f-caiso-{control,treated}` | **registered, then deliberately swept** — see §2 |
| "stamp the CAISO matrix shard cell (rule 28b)" | FFR-4F §7 duty (b) | cell present, `cell: "O", fc: "O"`, carrying the full adjudication note |

**The handoff's premise is a misreading of the `O` verdict.** It reads
"cell O, fc O" as *untested / open work*. The cell's own note defines O for this
mechanism in the opposite terms, verbatim:

> "**FORECAST STAYS O — deliberately NOT R.** Read this precisely: R would mean
> 'rejected as armed for its chartered purpose', and this lane's chartered
> purpose was the RULE 14 ANCHOR CORRECTION, which SUCCEEDED and is merged … O
> records exactly the true state: built, published-source-grounded,
> solve-adjudicated, merged, default-OFF, in no keeper, with **ARMING AN OWNER
> DECISION** (rules 5/24/28, routed F-3)."

So `O` here means *adjudicated and merged, arming owner-pending* — not
*untested*. Re-running the A/B would spend hours of solve to reproduce a result
already committed to the megawatt, which is precisely what the rule 28(a)
DO-NOT-REDO discipline exists to prevent.

**Consequence: this session executes the same default branch as caiso-206 —
verify, record, route. Nothing is solved and nothing is armed.**

---

## §1 — Branch B verified at HEAD (no solve; the mechanism is live and unchanged)

| # | check | instrument | result |
|---|---|---|---|
| 1 | `ScenarioConfig` field exists | `scenarios.py:3487` | `caiso_ra_mpb_capacity_anchor: bool = False` — **GATED default-OFF** |
| 2 | resolver | `config/capacity_market.py:1164` | `resolve_caiso_ra_mpb_anchor`; `CAISO_RA_MPB_ANCHOR_PER_KW_YR = 138.36` (`:1161`) |
| 3 | CLI flag | `scripts/run_full_horizon.py:883` | `--caiso-ra-mpb-capacity-anchor` present and wired (`:349`, `:966`) |
| 4 | unit pins | `pytest tests/unit/config/test_caiso_ra_mpb_anchor.py` | **11 passed** |
| 5 | **seam value, gate-off** | `capacity_revenue_per_mw_yr('CAISO','gas_ct',…)` | **82,795.2 $/MW-yr** — reproduces FFR-4F §3.2 **to the dollar** |
| 6 | **seam value, armed** | same, `caiso_ra_mpb_capacity_anchor=True` | **130,058.4 $/MW-yr** — reproduces §3.2 to the dollar |
| 7 | rule 25 isolation | all five other ISOs, both configs | **byte-identical**: ERCOT 0.0, PJM 46,458.6, MISO 75,012.0, NYISO 103,400.0, NEISO 108,940.0 |
| 8 | cache-key pin | `scripts/check_cache_key_registration.py` | **ok** — 736 fields, 189 registered, all resolve; **189 declared defaults all match HEAD** (so the anchor's `False` default is unmoved) |
| 9 | intake committed | `data/raw/capacity-market/demand-curve/caiso/` | `caiso.csv` carries the two `ra_mpb` rows (2025 Final 11.21, **2026 Forecast 11.53**) + the CPUC source PDF |
| 10 | both arms auditable | `results/ffr4f/{caiso-control,caiso-treated}` | `full_horizon_summary.json` + `run_config.json` + five per-year evolution ledgers each, **tracked in git** |

**Nothing about the mechanism has drifted since FFR-4F.** The two seam values
are the sharpest evidence: they reproduce the lane's own measurement exactly,
which identifies this as the same object at the same seam.

---

## §2 — The one genuinely NEW fact: the FFR-4F pair is off the forecast dashboard, **deliberately**

This is the part no prior CAISO record carries, and it is why a reader following
FFR-4F §5.5 to the dashboard would find nothing.

**Measured this session:** `register_forecast_run.py --reindex` — which is *also*
the Pages-deploy assembly step, i.e. the single writer of the **live** forecast
dashboard — writes **2 runs**, and neither is CAISO:

```
skip invariant-failures.json: no run_id
[reindex] wrote 2 runs to frontend/data/forecast/registry + .../runs
```

**Why.** The forecast namespace (`registry/`, `runs/`, `manifest.js`,
`program-status.js`) is entirely **gitignored** and fully derived from one
committed input: the canonical per-run sidecars `frontend/data/hindcast/<id>.json`.
Commit **`cccc911` (2026-08-19, "Clear forecast dashboard of all pre-keeper-refresh
runs")** deleted **all 187** of them — including
`caiso-2026-2030-ffr4f-caiso-control.json` and `-treated.json` — on the stated
ground that *"none was built on a current keeper config (newest registration
2026-08-13; every current keeper postdates it)"*, naming
`2026-08-17-caiso-200-h1-memberpanel` among them. The sweep verified its own
effect: *"--reindex writes 0 runs"*. The only two sidecars on the dashboard today
(`neiso-2021-2025-realized-k99`, `pjm-2021-2025-realized-k162`) were registered
**after** the sweep.

**This is the forecast-side analogue of the standing 2026-08-15 site-retention
directive** — the same policy caiso-206 §D item 3 anticipated for the backcast
lane. It is retention policy operating as designed, **not** a registration gap
and **not** an FFR-4F defect: that lane registered correctly, and a later
owner-directed sweep removed the record.

**Therefore the sidecars are NOT re-committed by this session.** Re-committing
them would undo an owner-directed retention sweep executed one day ago — plainly
not a session's call, and directly contrary to the directive that removed them.

**What this changes for a future reader:** the anchor's evidence now lives
**only** in (a) the committed slim artifacts `results/ffr4f/{caiso-control,caiso-treated}/`,
(b) `docs/handoffs/ffr-4f-caiso-anchor-merits-2026-08-09.md`, and (c) the
mechanism-matrix note. The `.gitignore` entry for `/results/ffr4f/*/*/*/*.parquet`
anticipated exactly this, committing the slim artifacts *"so the paired table is
auditable without a re-solve"* — that provision is now load-bearing rather than
belt-and-braces.

---

## §3 — Standing state re-verified (Branch A unchanged; committed bytes only)

Item-for-item against caiso-206 §A, all reproduced:

| # | check | instrument | result |
|---|---|---|---|
| 1 | keeper identity | `keepers/CAISO.json` | `2026-08-17-caiso-200-h1-memberpanel` — **unchanged** |
| 2 | determination | `calibration_verdict.py --run-id <keeper>` (never a solve) | **NOT-YET**, reproduced exactly |
| 3 | keeper text truthfulness | `audit_keepers.py --iso CAISO` | **PASS, 0 failures / 0 warnings** |
| 4 | status sync | `build_status.py --iso CAISO --check` | *"status parts in sync (1 keepers: CAISO)"* |
| 5 | caiso-205 registration | registry sidecars + run payloads | both present **and tracked**, years `[2023, 2024, 2025]` each |
| 6 | DOF ledger | `calibration_attestation.json` ×3 | keeper **10/7**, control **10/7**, arm **11/7** — 11th on the ARM only |
| 7 | holdout posture | `calibration-complete.json`, `holdout-freeze.json` | `complete` = {NEISO, NYISO, PJM}; `final` carries **no ISO entry at all** (only its `_note`, *"DELIBERATELY EMPTY as of 2026-07-31"*) — **CAISO in neither**; freeze **ACTIVE** |
| 8 | mechanism matrix | CAISO shard | `ercot_storage_adaptive_expectation` **I** with the caiso-205 stamp; anchor **O/O**. **No verdict moves** |

**Scorecard, re-verified in full:** C1 fuel-mix PASS (**12/12, free 8/8**) · C2
system volume PASS · **C3a mean LMP FAIL — the SOLE load-bearing failure** (2023
PASS; 2024 **+12.8 %**, 2025 **+15.7 %** vs actual RT LMP) · C3b PASS · **C3c the
SINGLE ledgered caveat** (2023 0 h vs 47 h; 2024 1 h vs 35 h; 2025 PASS) · C4
PASS · C6 governance PASS · C8 forced-energy PASS. Determination basis:
*undocumented out-of-tolerance (FAIL) criteria: price_mean*.

**Branch A is untouched, as the charter requires:** no solve, no probe, no
re-litigation of the C3a basis (CLOSED — judged vs actual RT LMP only, caiso-203
ruling 1), no re-run of the caiso-204 identification or the caiso-205 A/B.

---

## §4 — The owner packet, now **TWO** live items

caiso-206 §C carried one. This session's charter surfaces a second, which is
genuinely live and has never been put to the owner as a decision in the CAISO
lane's own records.

### (1) Fund a tail-formation object — CARRIED FORWARD UNCHANGED

Only a funded tail-formation object can move the C3a/C3c compression (two faces
of one behaviour, caiso-202 §B). Bounds stated against interest:

| object | status | measured reach |
|---|---|---|
| **(a) PS water-state hourly intake** | declined **3×** | **62.1 % / 10.4 %** of the required 2024 / 2025 C3a move **at its most favourable bound** |
| **(b) import spot-capacity derivation** | not funded | direct λ share **< 5 %** of the positive gap |

**Neither closes C3a on its own arithmetic** against the broad **~$2–3/h**
sub-$60 level-down the miss requires. Reaching the number through any §F-killed
lever would be a rule-13 act. **If no funding order issues, rest is correct.**

### (2) **F-3 — the arming posture of `caiso_ra_mpb_capacity_anchor`** — NEWLY SURFACED HERE

The mechanism is built, measured, merged, default-OFF and keeper-inert **by
construction**. Arming it is explicitly an **owner decision** (FFR-4F F-3, rules
5/24/28), and FFR-4F's pre-registered **D-4** barred its own lane from pulling
any further lever after the read. The measured facts, both directions:

| lane | what arming costs | what arming buys |
|---|---|---|
| **forecast** | 2027 reserve margin **7.74 % → 5.88 %** (−1.9 pp), 2028 **10.29 % → 8.47 %**; I7 accredited-firm shortfall **deepens** (2027 54,969 → 54,019 MW); FC-1 and FC-2 row1 both **worse** | FC-2 row 4 **52.5 % → 46.1 %** |
| **backcast** | would **move the designated keeper** — the seam is reached via the retirement screen and plant-financials — and so needs a full re-solve + re-gate | nothing measured; no backcast adjudicates it |

**The honest reading, and it argues against arming for the row-4 reason:**
FFR-4F's pre-registered **trap test fired**. Total thermal built is **identical
to the megawatt** in both arms (10,186.3 MW), as are total additions
(15,590.7 MW), renewables (5,404.4), storage (0.0) and retirements (2,615.3).
**The only change is the label on 1,000 MW** — backstop −1,000, economic +1,000,
delivered two years later. Row 4 improves *solely* because capacity moved into a
channel the numerator does not count. Per FFR-4F D-2 that is **channel
substitution, not a gain**, and arming to capture it would be the rule 1
`[R-STRUCT]` trap the owner declined this anchor as a route to in the first place
(D-15).

**Routed, not decided.** A session cannot arm it. The recommendation this
assessment offers, for the owner's convenience only: **keep default-OFF** absent
a reason unrelated to row 4 — the mechanism's rule-14 correctness is already
banked by its merge, and nothing in the forecast lane's own measurement makes
arming an improvement.

---

## §5 — DO-NOT-REDO, extended

Everything in caiso-206 §B carries forward verbatim (the caiso-202/203/204/205
lists; new evidence means one thing only — a keeper whose own scored path
spikes). **Added by this session:**

1. **Do not re-run the FFR-4F A/B.** The committed slim artifacts +
   `docs/handoffs/ffr-4f-caiso-anchor-merits-2026-08-09.md` **are** the
   full-magnitude record, and the mechanism is verified unchanged at HEAD (§1).
2. **Do not read the anchor's `O` cell as untested.** It means *adjudicated,
   merged, arming owner-pending*. The cell note says so explicitly.
3. **Do not re-commit the swept `frontend/data/hindcast/` sidecars.** Their
   removal is the deliberate `cccc911` retention sweep (§2), not a gap.
4. **Do not re-derive the anchor value.** 138.36 $/kW-yr is fixed from two
   published CPUC figures committed *before* either arm solved, and FFR-4F §5.4
   records that it was not revisited afterwards.

---

## §6 — Filed items

Carried from caiso-206 §D, each **re-verified still open** this session, and each
fixable only at the next promotion:

1. **Stale DOF-ledger text** — the `offer_curve_by_group` row still reads
   `"identification": "residual"` on the keeper bundle, overstating the residual
   content for CAISO's CC_REGULAR / CT_PEAKER bands (measured from OASIS
   `PUB_DAM_GRP` since 2026-08-02, caiso-202 §H). **Verified still stale.**
2. **Diagnostics vintage drift** — the keeper-vintage `legitimacy_diagnostics.json`
   differs from fresh bundles on one D-4 row (chp_steam plant 10034).
3. **Site retention** — the caiso-205 pair postdates the keeper and comes off at
   the next promotion in the ordinary way. Not an anomaly.
4. **Session mechanics** — regenerate `data/clean` before any solve; **ONE** CAISO
   3-year invocation at a time (~13.3 GiB cgroup cap).

**New, and routed OFF this lane (rule 25 `[R-ISO-SCOPE]`):**

5. **Program-wide stale registration citations.** `cccc911` swept **187**
   sidecars across every ISO, so *every* lane's records that cite a registered
   forecast-run id now point at a run no longer on the dashboard — CAISO's
   FFR-4F pair among them, but PJM's, ERCOT's, MISO's, NYISO's and NEISO's
   equally. The shared base row in `mechanism-matrix.js` still reads *"registered
   caiso-2026-2030-ffr4f-caiso-{control,treated}"*. **Not repaired here:** it is a
   cross-ISO condition in a shared file, and fixing only CAISO's citation would
   make the file inconsistent while fixing all of them is off-lane. Routed for a
   cross-lane or governance session.

---

## §7 — Governance

* **Rule 1 `[R-STRUCT]`.** Nothing tuned to a residual. §4(2) explicitly declines
  to recommend arming for the row-4 improvement, because that improvement is
  channel substitution.
* **Rule 12 `[R-PARALLEL]` / mechanics.** No solve run, so neither the year-loop
  nor the memory-cap constraint was engaged.
* **Rule 15 `[R-DASHBOARD]`.** **No run was produced, so no registration is due.**
  The caiso-134/140/150/202/206 disposition applies unchanged. §2 records why the
  FFR-4F pair is nonetheless absent from the forecast dashboard.
* **Rule 22 `[R-HOLDOUT]`.** No year solved, scored or registered. CAISO absent
  from both `complete` and `final`; freeze **ACTIVE**; no out-of-training year
  approached.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. Verified by measurement that arming the
  anchor leaves all five other ISOs byte-identical at the seam (§1 item 7). The
  program-wide sweep consequence is *reported*, not repaired (§6 item 5).
* **Rule 27 `[R-PUSH]`.** Opus. No source file was modified at all this session —
  the deliverable is records only.
* **Rule 28 `[R-MECH-MATRIX]`.** **No mechanism was tested, so duty (b) does not
  attach and no cell verdict moves** — the caiso-206 precedent applied
  identically. The §5.2 prose block records the session.

---

## §8 — Record changes

- This file; `docs/calibration-log/caiso.md` caiso-207 entry; matrix §5.2
  caiso-207 block.
- **Keeper, markers, holdout freeze, every matrix cell verdict, and every source
  file: UNCHANGED.** No run registered (none produced). No CAISO shard cell
  edited.

Next number: caiso-208.
