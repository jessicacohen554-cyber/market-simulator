# MEMO — the G-20b within-window tight-hour treatment question (owner decision requested)

> pjm-153, 2026-08-04. Written to discharge
> `results/calibration/FINDING-guard-falseneg-audit-2026-07-27.md` **§7.2**, which
> named this memo as the *only* route by which PJM keeper root cause (6b)'s live
> remnant — and matrix §5.3 queue **item 5** — can be unblocked: *"a within-window
> tight-hour treatment memo, owner sign-off, its own charter, LOYO within
> 2023–2025."*
>
> **This memo decides nothing and arms nothing.** No guard parameter is read
> except as a citation (rule 23 `[R-FROZEN-DERIVE]`), no LP was solved, no
> artifact regenerated. It asks one question, sets out the evidence **on both
> sides**, and pre-registers what a follow-on charter would have to carry so that
> a yes is actionable and a no is final.

---

## §1 — the question, in one paragraph

The merit-order guard reclassifies a detected CAMPD outage window as **economic
layup** rather than a mechanical outage when the unit's own measured short-run
marginal cost sat above the revealed marginal cost of the capacity that was
actually running, for at least `MERIT_OOM_FRAC = 0.90` of the window's hours. A
window so vetoed **leaves the availability envelope entirely** — the unit is
returned to the model as AVAILABLE for the whole span, and the LP declines it on
its own economics. By construction, up to **10 % of a vetoed window's hours were
NOT out of merit**, and those are precisely the tight, high-price hours.

> **Should a vetoed window's in-merit tail stay erased with the window, or should
> the availability envelope keep the unit out through those hours?**

That is the entire question. It is a **grain** question — the evidence is
hour-grain, the treatment is window-grain — not a parameter question.

---

## §2 — the mechanism, cited

`scripts/lib/outage_detect.py`:

```
SRMC_u(t) = HR_u × delivered_fuel_price(u, t)
RCC(t)    = capacity-weighted MERIT_RCC_PCTL quantile of SRMC over the units
            MEASURED RUNNING at t (CEMS CF ≥ REAL_RUN_CF)
layup    ⟺ #{t ∈ window : SRMC_u(t) > RCC(t)} / #window ≥ MERIT_OOM_FRAC
```

* `MERIT_RCC_PCTL = 0.90`, `MERIT_OOM_FRAC = 0.90` — identified **jointly** across
  the ISOs carrying a published outage instrument, against that published series
  alone; structural percentiles over per-ISO self-referential distributions, so no
  scalar fitted on one ISO's residual crosses a boundary (rules 23/24/25).
* The guard is **fail-safe**: an unidentified unit or unpriceable span returns
  `False` and the window is **kept**. It can only ever REMOVE windows it has
  positive measured evidence against.
* Applied at derive time via `scripts/data/derive_campd_unit_outages.py
  --merit-order-guard`; vetoed windows are written to the labelled companion
  `data/raw/campd-unit-outages-layup-<ISO>.csv` (3,247 rows for PJM), which **no
  loader reads by default**. The model consumes the base
  `campd-unit-outages-PJM.csv` (10,671 rows).
* Every input is a measured physical/market quantity — CAMPD operation and heat
  input, plus delivered fuel prices. **No LMP, no cleared price, no cleared
  quantity, no MWh/price residual anywhere in the construction** (rules 11/13/26).

---

## §3 — what is at stake, measured

**Exposure (guard audit §1, D1).** PJM drops **13.3 / 8.9 / 12.5 %** of baseline
outage GW-days across 2023/2024/2025 — and PJM's drops are **the most
season-uniform of the six ISOs** (DJF/MAM/JJA/SON = 28/27/20/25), which is what
foreshadowed its D3 result. Top dropped classes: ST_GAS, COAL/CC_REGULAR.

**Price stake (pjm-138 §4.2), and it is material.** Removing the guard's own
2.8–5.0 GW from the tightest net-load decile's offer stack moves the clearing
price on the mean by:

| removed | 2023 | 2024 | 2025 |
|---|---|---|---|
| 3 GW | +$3.97 | +$8.02 | +$14.95 |
| 5 GW | +$7.45 | +$12.46 | +$23.36 |

i.e. **28–59 % of that decile's system-energy gap, as a LOWER bound.**

**But the audit's own verdict is UNCHANGED, and that is the point.** No PJM cell
was confirmed. The D2 population test — do the dropped windows look like the
mechanical population? — is **clean 3/3 for PJM**, and the D3 exceedance signal is
**mostly a window-LENGTH composition effect**, established by the post-hoc
placement null in §4 of that audit. So §3 is a change of *stakes*, not of
*evidence*. **Nothing may be armed on the price alone** (the audit's own §7.3, and
rules 1/13).

---

## §4 — the evidence cuts both ways, and the memo must say so

**For keeping the in-merit tail out of the envelope (i.e. shortening the veto):**

1. The veto is window-grain but the phenomenon is hour-grain. A unit can be
   economically laid up for 90 % of a span and genuinely unavailable — or simply
   not restartable within the hour — for the remaining 10 %.
2. Those 10 % are **not random**: out-of-merit is defined against the running
   fleet's revealed cost, so the in-merit hours are exactly the tight hours. The
   guard therefore returns capacity to the envelope with maximum leverage on the
   price, which is the pjm-138 §4.2 number.
3. Rule 14 `[R-ACCURATE]` cuts this way: the measured record says the unit was
   in merit and did not run.

**Against (i.e. the charter's existing "not shortened" decision was right):**

1. **The charter §3a D2 decision was explicit and reasoned.** Windows are *not*
   shortened, on the stated rationale that there is **no evidence of a
   genuinely-down core** — the out-of-merit share is close to binary at window
   grain (NEISO p25 = 0.00, p75 = 1.00), so a 90 %-out-of-merit window is
   overwhelmingly a fully-out-of-merit window with measurement noise, not a
   90/10 mixture.
2. **The unit measurably did NOT run through those hours.** That is the datum. The
   guard's claim is about *why* — economics, not mechanics — and being in merit
   for a handful of hours does not establish that the unit was mechanically able
   to serve them.
3. **neiso-68 is the direct counter-example**: seam-population units were in merit
   on essentially every seam day and **stayed down anyway**. Being in merit
   demonstrably does not imply availability.
4. **`MERIT_OOM_FRAC` is not load-bearing**, so "just lower the threshold" is not
   the lever it looks like: 0.70 → 1.00 moves the NEISO veto count only 560 → 412.
   Anyone proposing to shorten windows must not reach for the fraction.

**And a hard bar on both:** rule 19 `[R-ONE-MECH]` forbids **stacking** a new
within-window treatment on the guard's lane. Any charter must **replace** the
guard's window-grain rule with an hour-grain one — never add a second mechanism
that also decides availability inside a vetoed span.

---

## §5 — what a follow-on charter must carry (pre-registered here, so a "yes" is actionable)

If the owner signs off, the charter is bound by all of the following, committed
**before** any measurement that decides it:

* **Form.** An hour-grain **replacement** of the window-grain veto, not an
  addition (rule 19). The natural statement: a vetoed window returns to the
  envelope **only for its out-of-merit hours**; its in-merit hours stay booked as
  unavailable. No new tunable, no new percentile, no threshold sweep.
* **Zero fitted parameters** (rules 5/13/21/24). If the construction needs a
  number that is not already identified in `outage_detect.py` against a published
  outage instrument, the charter fails at the screen.
* **`MERIT_OOM_FRAC` and `MERIT_RCC_PCTL` do not move** (rule 23). A re-derivation
  needs a cited source-data change, and none exists. A charter that moves either
  is out of order regardless of its result.
* **Scored on AMPLITUDE, never the annual mean** (pjm-141; PJM's level passes by
  cancellation: +$6.82/+$5.78/+$3.40 overnight, −$7.62/−$11.37/−$22.19 at peak).
  The pre-registered target is the **tightest-decile** clearing price, with the
  annual-level effect declared ex ante.
* **A C3c report is mandatory.** PJM's C3c passes with model tail hours
  **3 / 10 / 32 h**; a mechanism that adds unavailability in tight hours is the
  most likely thing in the queue to move it. It must be reported whichever way it
  goes.
* **LOYO within 2023–2025** (rule 22). Leave-one-year-out before any promotion;
  in-sample gain with held-out degradation is overfitting. **No holdout year is
  touched in any mode** — PJM holds `complete`, is absent from `final`, and the
  holdout spend freeze is ACTIVE and outranks both.
* **Kill rules, pre-registered:**
  * **K1** — if the reclassified hours are **< 1 %** of the vetoed span's hours at
    PJM in any year, the mechanism cannot reach the pjm-138 §4.2 stake and is
    dead at the pre-check, no LP.
  * **K2** — if the tightest-decile clearing-price move is **< $1.00/MWh** on the
    mean in any year, it is inert on its own charter (the pjm-142 K-A bar shape).
  * **K3** — if any C1-gated class moves **> 1.5 TWh**, the arm has reached
    outside its lane (the pjm-147 E1d bar).
  * **K4** — if the determination moves from CALIBRATED for a reason the charter
    did not license ex ante, the arm is refused, whatever it did to the tail (the
    pjm-146 lesson: an unlicensed C1 magnitude is a stop, not a caveat).
* **A cross-ISO scope statement.** The guard is shared code. The charter states up
  front whether it changes only PJM's extract or all six, and — per rule 25 — no
  other ISO's cell is written by a PJM session.

---

## §6 — the decision requested

**Charter the hour-grain replacement, yes or no.**

* **No** is a complete and defensible answer: the audit confirmed no cell,
  PJM's D2 is clean 3/3, D3 is mostly length composition, and the charter's
  original "not shortened" decision has a stated rationale that the binary
  window-grain distribution supports. On a **no**, matrix §5.3 item 5 and keeper
  root cause (6b)'s remnant both close as **owner-refused**, and the pjm-138 §4.2
  price becomes a disclosed representation cost rather than an open lead.
* **Yes** authorizes a charter bound by §5 — and **only** §5. It does not
  authorize moving a guard parameter, shortening windows by a swept threshold, or
  arming anything on the price.

**What this memo explicitly does NOT recommend.** It does not recommend a
direction. The dispatch that produced it, the audit that requested it, and rules
1/13 all say the same thing: **do not arm anything on the price alone**, and the
non-price evidence is genuinely divided.

---

## §7 — rule compliance

* **Rules 1/13/21/23/24** — no parameter read except as a citation; nothing tuned;
  nothing sized by a residual; no deriver touched.
* **Rule 19 `[R-ONE-MECH]`** — the replacement-not-stacking bar is stated as
  binding in §4 and §5.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; freeze respected; LOYO required of
  any successor.
* **Rule 15 `[R-DASHBOARD]`** — no solve ⇒ nothing to register.
* **Rule 25 `[R-ISO-SCOPE]`** — PJM's lane only; the cross-ISO exposure figures in
  §3 are the audit's own published table, quoted, not re-derived, and no other
  ISO's cell is written.

**Sources.** `results/calibration/FINDING-guard-falseneg-audit-2026-07-27.md`
§§1–4, §7.2; `results/calibration/FINDING-pjm138-system-energy-is-reserve-opportunity-cost-2026-07-29.md`
§4.2 and §6; `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §3a;
`scripts/lib/outage_detect.py:396–452`, `:634–644`;
`scripts/data/derive_campd_unit_outages.py:870–890`, `:1395–1449`;
`frontend/data/backcast/keepers/PJM.json` root cause (6b).
