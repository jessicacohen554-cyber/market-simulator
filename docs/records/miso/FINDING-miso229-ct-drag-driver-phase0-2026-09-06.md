# FINDING miso-229 phase 0 — MISO's CT reliability DRIVER **EXISTS and is year-stable** (evening Spearman **+0.706 / +0.636 / +0.743**), so the admissible successor to the quarantined actuals pin is live. **But ERCOT's WINDOW does not transfer**: MISO's midday block is as strongly driven as its evening. **ZERO LP MINUTES. Nothing armed, nothing fitted, nothing promoted.**

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** (CALIBRATED). Continues miso-228 under
the owner's decision of 2026-09-06 (option (c): fix CT_PEAKER, then promote the seam pair).
Instrument: `scripts/probes/_miso229_ct_drag_driver_phase0.py` → `_miso229_ct_drag_driver.json`.
Rule 22: 2023–2025. DOF ledger unchanged at **41/2**.

---

## 1. The lever miso-228 named is REFUSED, definitively

`ct_mustrun_per_plant` is **inadmissible and already adjudicated so**. Its own field docstring:

> *"a per-plant monthly reliability must-run floor **equal to their observed EIA-923 net
> generation** … Because the floor IS observed generation …"*

That is rule 13 `[R-MEASURED]`'s **named** forbidden case — pinning a unit to its observed
generation — and the codebase already treats it as such: `scenarios.py` calls it *"the
`ct_mustrun_per_plant` **quarantine** … pinned ANNUAL commitment from an outcome filing"*,
`backcast_config.py` calls it *"the measured-actuals `ct_mustrun_per_plant` **crutch**"*, and it
is **formally D-9 QUARANTINED** in `scripts/legitimacy_diagnostics.py` (machine-asserted
`False`; the miso-226 run's own diagnostics already check it). **It is not merely disallowed —
it is enforced off, and arming it would have "fixed" C1 by forcing the observed energy, i.e. for
the worst possible reason.**

## 2. The admissible successor, named by the code itself

`ct_netload_drag` / `apply_ct_netload_drag_floor` — *"the **forward-native replacement** for the
`ct_mustrun_per_plant` actuals pin"*: a min-gen floor `clip(slope*netGW + intercept, 0, cap)`
gated to a ramp window, whose **trigger** (net load) and **magnitude** (a physical min-gen) both
regenerate for a forward year and respond to changed conditions — admissible in backcast *and*
forecast by construction. It is the **ERCOT and PJM keeper** mechanism
(`netload_drag_floors` cells `K`/`K`; CAISO and NYISO `R`). **MISO's cell is `U`** — untested,
so no rule-28 DO-NOT-REDO bar.

## 3. Rule 17 `[R-FLOOR-WINDOW]`'s gate: does MISO have the DRIVER? **YES.**

Ported `derive_pjm_ct_netload_drag.py` to MISO byte-for-byte in method, changing only the ISO and
its clock (**CST = UTC − 6**, not PJM's EST). Pure-play CT_PEAKER plants (≥90 % of plant model
capacity is CT_PEAKER): **127 plants / 19,537 MW = 88 % of class nameplate**; measured CT
**15.037 / 13.791 / 14.804 TWh**.

| block | 2023 mean CF (ρ) | 2024 mean CF (ρ) | 2025 mean CF (ρ) |
|---|---|---|---|
| overnight 22–06 | 0.0360 (+0.361) | 0.0321 (+0.429) | 0.0340 (+0.560) |
| morning 06–11 | 0.0824 (+0.574) | 0.0706 (+0.591) | 0.0668 (+0.721) |
| **midday 11–15** | **0.1343 (+0.743)** | **0.1146 (+0.691)** | **0.1126 (+0.734)** |
| **evening 15–22** | **0.1245 (+0.706)** | **0.1237 (+0.636)** | **0.1457 (+0.743)** |

**The driver is PRESENT and year-stable**: evening ρ **+0.706 / +0.636 / +0.743**, matching
ERCOT's ~0.7, and the overnight CF is near-zero (0.032–0.036) exactly as the mechanism's own
driver evidence requires — a floor binding overnight would be the rule-17 bug by definition.

## 4. WHAT DOES NOT TRANSFER, found before anything was armed

**ERCOT's 15–22 window is ERCOT's story, not MISO's.** MISO's **midday** block is as strongly
driven as its evening (ρ 0.743 / 0.691 / 0.734 vs 0.706 / 0.636 / 0.743) and carries a
comparable CF (0.113–0.134 vs 0.124–0.146). ERCOT's and CAISO's window is justified by *solar
collapse* producing a sharp evening ramp; MISO carries far less solar, and its CT commitment is
a **broad high-net-load daytime** phenomenon rather than an evening-ramp one.

Rule 25 `[R-ISO-SCOPE]` therefore bites twice, and both are stated here **before** a derive is
written: MISO may not carry ERCOT's fitted coefficients (`ct_drag_slope_per_gw` 0.00703,
`_intercept` −0.1427, `_cap` 0.47), **and it may not carry ERCOT's window either**. MISO's window
must be chosen from MISO's own block evidence — on this table, roughly **11–22** — and declared
with its driver in the PRECOMMIT, per rule 17 clause (b).

## 5. WHAT THIS LICENSES — nothing yet, deliberately

No curve is fitted, no coefficient committed, no field flipped, no derive frozen, no arm run,
the keeper untouched. This probe answers one question — *is a MISO derive worth writing?* — and
the answer is **yes**. The next session writes the frozen MISO derive (rule 23), declares the
window and coefficients ex ante, mints the matrix row (`ct_netload_drag` has **no base row in
any ISO** — rule 28c owes one plus six cells), and screens on 2023 before any full span.

**Reported against the lever**: it is a **min-gen floor**, and C8 already reports CT_PEAKER at
**27.6 / 18.6 / 15.6 %** forced — *grounded*, but already the fleet's largest forced share. Rule
19 `[R-ONE-MECH]` requires the successor to **reconcile or replace**, never stack, and rule 18's
forced-energy budget (peakers > 15 %) is the live constraint the screen must clear. Adding
floor energy to the class with the highest forced share is the honest risk of this lever, and it
is named now rather than discovered at the gate.
