# ASSESSMENT nyiso-144 — frontier re-declaration and the `complete`-tier posture

Session nyiso-144. Keeper at HEAD `2026-08-18-nyiso-143-n11tsl-arm`
(determination **CALIBRATED**, rubric v3.4, C3c the lone ledgered caveat).

---

## 0. THE ANSWER

* **`complete` is HELD and needs nothing from this session** — unless the
  nyiso-144 A/B promotes, in which case its entry is re-keyed with a
  determination re-verification (rule 22 D-5(b); §3).
* **Frontier: still NOT-YET.** But the queue has changed character. nyiso-143
  left four open items, three of which were open *research* questions. After
  this session **none of them is**: item 1 is dissolved and replaced by a named
  data object, item 2 is measured and now blocked on an owner ruling, item 3 is
  built and A/B'd, item 4 is untouched by design. **Frontier is blocked on
  decisions and one data purchase, not on investigation.**
* **NO `final` grant is proposed**, and none should be. nyiso-142's NOT-READY
  verdict and nyiso-143's re-verification both stand unchanged; the holdout
  spend freeze is `active: true` and outranks both marker blocks regardless.

---

## 1. THE FOUR OPEN ITEMS, RE-ASSESSED

### Item 1 — "the downstate scarcity mechanism": **DISSOLVED, and replaced**

nyiso-143 named this the critical path: 100 % of the *model's* C3c tail hours
are Long_Island, the Zone-K bound produces all of them, and removing the bound
removes the tail — so build a downstate scarcity channel.

**This session measured the real tail before building, and the object is not
downstate.** In NYISO's actual C3c tail hours the NYCA-wide reserve price
averages **$306.74 / $31.74 / $393.31** and clears $50 in **100 % / 15 % / 95 %**
of them; Long Island's *locational* adder averages $116.00 / $5.36 / $152.12.
The tail is a **control-area reserve-shortage pricing event** that Long Island
participates in. A Zone-K-scoped mechanism could not have reproduced it, and
building one would have been building the wrong object.

The instrument that *would* price it already exists in the model and never
fires: `nyca_10min_spin`, published 655 MW at a **$775** RCPF, binds in **zero
hours of all three years**, because the class is idle-allowed. So do both Long
Island families. Full record and the three-way convergence with nyiso-110 and
nyiso-124: `FINDING-nyiso144-downstate-scarcity-and-rho-2026-08-18.md` §1.

**Item 1 is replaced by a single named object: a defensible 10-minute
deliverable-ramp capability for NYISO hydro** (§1.4 of the finding). It decides
whether `nyiso_spin_reserve_online` can bind, because `rho*` for inertness is
0.3426 / 0.3635 / 0.4619 — below nyiso-110's own stated 0.5 floor — and hydro
supplies almost all the eligible output while carrying no `RAMP10_FRAC_*` entry
at all. **This is now the critical path.** It is a data-intake question, not a
modelling one, and it is not a single-ISO-lane decision to fund.

### Item 2 — `online_rho`: **MEASURED; now blocked on an owner ruling**

Delivered: `scripts/data/derive_campd_online_reserve_rho.py` +
`src/market_sim/data/online_reserve_rho.py`, replacing an identification that
was dead code on a binned fleet. Measured `incity_obligation` **0.3014**
(min-load 1.2462) at 95.5 % CAMPD coverage; `nyc_spin` **0.2011** (min-load
1.1247) at 80.5 %.

**Settled:** the downstate gated family is LIVE — `rho*` ≈ 3.0 sits far above
the entire admissible band, so rho decides how hard the row binds, never
whether. nyiso-143's open question is answered.

**Not settled, and why both cells stay `U`:** both measured values fall **below
the code's own `RHO_CLIP` floor of 0.5**, a band inherited from the legacy path
with **no primary citation anywhere in the repo**. `rho_used` therefore returns
the floor, not the measurement — the same rule 21 `[R-DOF]` defect moved one
level out. The band was left unchanged rather than widened to fit the
measurement. **Owner rule-22 D-5(b) call.**

### Item 3 — the bridge membership channel: **BUILT, and A/B'd**

`nyiso_gas_bridge_plant_exclusions` (default off), the bridge's half of a
correction that previously existed only on the reliability floor, so nyiso-140
had fixed one *mechanism* rather than the plant (rule 19). Identification is the
nyiso-140 lay-up criterion verbatim, derived **blind to the mechanism's own D-4
verdicts** — which is what makes its selection of 7 of the bridge's 8 D-4
failures evidence rather than circularity. Pre-registration:
`PREREG-nyiso144-bridge-layup-membership-2026-08-18.md`; result:
`RESULT-nyiso144-bridge-layup-membership-2026-08-18.md`.

**A correction to the handoff's premise is recorded there**: the keeper's own
committed `legitimacy_diagnostics.json` does not carry the Port Jefferson
figures the handoff quotes (2024: 0.0616 TWh / 1,716 h / median 45.222 MW /
44.7 % at zero / verdict **pass** — not 0.1495 TWh / 4,623 h / 0.000 MW /
71.2 %). Roseton's row matches exactly; 2517's and 7314's do not.

### Item 4 — `nyiso_iroquois_winter_spread`: **UNTOUCHED, by design**

Both halves remain exactly where nyiso-143 filed them. The arming decision is an
owner D-5(b) call (it improves a measured input while degrading C3a-2025); the
taxonomy defect needs a base-row + all-six-shards edit, which is a governance
round, not a single-ISO lane. `DECISION-CARD-nyiso143-iroquois-taxonomy-gap-2026-08-18.md`.

---

## 2. FRONTIER — the determination

**NOT-YET**, unchanged in verdict and changed in kind.

The frontier question is whether NYISO's remaining queue is exhausted of
*model-side* work. It is not, but what remains is now enumerable and none of it
is open investigation:

| # | object | kind | who decides |
|---|---|---|---|
| 1 | NYISO hydro 10-minute deliverable ramp | **data intake** | owner (funding/scope) |
| 2 | `RHO_CLIP` band | **governance** | owner (D-5(b)) |
| 3 | plant 7314's bridge over-run | model-side, **offer/economics** | a NYISO lane |
| 4 | `nyiso_iroquois_winter_spread` arming + taxonomy | **governance** ×2 | owner |

Only item 3 is a lane-sized modelling task, and it is a small one. **A frontier
re-declaration is therefore reachable in one more session once items 1, 2 and 4
are ruled on** — which is a materially different position from nyiso-143's,
where item 1 was an unscoped "identify and build a mechanism".

**What this session does NOT claim:** that the C3c miss is now explained away.
It is not. §1 explains *where the tail comes from* and *why the model's own
instrument for it never fires*; it does not close the gap, and C3c remains the
keeper's lone ledgered caveat, reported at full magnitude.

---

## 3. `complete` — the posture, stated explicitly

**HELD, and correctly keyed at HEAD.** `frontend/data/backcast/calibration-complete.json`
carries NYISO under `complete` with `keeper: "2026-08-18-nyiso-143-n11tsl-arm"`
and `determination: CALIBRATED` (rubric v3.4, 0 FAILs, C3c the lone ledgered
caveat), re-verified without a solve at the nyiso-143 promotion.

**What `complete` authorizes and what it does not.** It authorizes the
validation touchpoints (2022, and the ladder back to 2020) — and **the holdout
spend freeze, which is `active: true`, suspends that authorization**. So no
out-of-training year may be solved, scored or registered in this session or any
other while the freeze stands, and none was: every year read anywhere in this
session is 2023, 2024 or 2025.

**The one duty this session may incur.** If the nyiso-144 A/B promotes, rule 22
D-5(b) requires the `complete` entry to be re-keyed to the new run **and its
determination re-verified against it** (`scripts/calibration_verdict.py
--run-id`, committed artifacts only, never a solve) before the promotion commit
lands; a re-verified determination that is *worse* stops the promotion and
escalates. `keeper_at_declaration` is preserved either way. If the A/B does not
promote, the entry is untouched.

---

## 4. `final` — NOT PROPOSED, and the record is unchanged

nyiso-142 job 2 found NYISO NOT READY on both locked-test years; nyiso-143
re-verified that at HEAD and corrected one leg (the "no EIA-930 rows for 2026"
half is FALSIFIED — 4,343 NYIS rows are on disk). **The conclusion is unchanged
and this session adds nothing to it:**

* **2019** — Indian Point 2/3 absent from every `eia860_generator*` vintage; 1
  actual RT hour above $300, the least discriminating year in the record, so it
  cannot discriminate on C3c; and `data/raw/lmp-data/NYISO/` holds no 2019 file
  at all, so it could not be zonally scored even if solved.
* **H1-2026** — unsolvable on the frozen keeper config because
  `nyiso_dynamic_reserve_requirements`' loader **raises** rather than falling
  back, against on-disk CSVs covering 2022–2025 only and a published LRR
  schedule gap (v2021 ends 2026-02-14, v2026 starts 2026-07-10). Closing it
  needs an adjudicated mid-year splice — a methodology decision about the frozen
  config's inputs taken *after* the config was selected, which a touch-once test
  cannot absorb.
* NYISO's locked test is **NEVER GRANTED**, not spent (rule 22's D-23
  correction). Nothing here changes that, and nothing should be read as
  proposing it.

---

## 5. GOVERNANCE RECORD

* **Holdout freeze ACTIVE and untouched.** Every year solved, scored or read in
  this session is 2023–2025 (rules 16 / 22).
* **Rule 15**: every completed run registered on the dashboard in this session,
  keeper or probe.
* **Rule 28(b)**: every mechanism this session touched has its NYISO shard cell
  re-stamped — `nyiso_synchronised_reserve`, `nyiso_incity_commitment_obligation`
  (both stay `U`, sharper blocker), `nyiso_spin_reserve_online` (`I` confirmed),
  and the bridge row's membership leg.
* **Rule 28(c)**: the one new `ScenarioConfig` field
  (`nyiso_gas_bridge_plant_exclusions`) is registered in the matrix under the
  bridge row's documented sub-scalar escape hatch, alongside its siblings.
* **Rules 25 / 28(d)**: no other ISO's shard, keeper shard or lane file touched.
  Every measured value here is NYISO's own and transfers nowhere.
* **DO-NOT-REDO**: the Zone-K A/B (nyiso-143) is closed — do not re-solve it,
  and do not reach the tail back by re-tightening the transfer bound. The
  nyiso-110 spin-online solve is confirmed, not to be re-run.
