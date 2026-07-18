# Handoff — proper CC capacity reconcile + the next PJM diagnostic Fable session (2026-07-14)

**Context.** pjm-110 (the CC summer-capacity guard + CT-only bench flag) is now
the PJM keeper (owner-adopted 2026-07-14, superseding pjm-107). The guard is a
minimal, correct hygiene fix — but it exposed a stack of CC-capacity mechanisms
that don't yet compose cleanly, and it left the July-gas diagnosis's substantive
PJM residuals untouched. This handoff charters the two follow-ons the pjm-110
attestation and calibration-log reference. **Part A is an Opus engineering
charter; Part B is a Fable/diagnostic design session** (no solve until the
design is agreed, mirroring the pjm-107 spec-then-execute split).

Grounding: `docs/DIAGNOSIS-pjm-july-cc-overrun-2026-07.md` (§3b, §6, §7);
`docs/calibration-log.md` 2026-07-14 PJM-110 entry; the guard
(`fleet._reconcile_cc_pmax_to_nameplate` + `fleet.cc_summer_capacity`), the
demonstrated-peak reconcile (`fleet._reconcile_cc_capacity` /
`scripts/data/derive_cc_capacity_reconcile.py`), and the Leg-B CT-only flag
(`render_calibration_html._flag_ct_only_reporters`).

---

## Part A — Proper CC capacity reconcile (Opus engineering charter)

### A.1 The problem: three CC-capacity mechanisms that don't compose

A PJM CC plant's LP capacity is now set by three overlapping mechanisms, applied
in this order inside the flag-on keeper path (`fleet_to_bins`):

1. **The guard** (`_reconcile_cc_pmax_to_nameplate`, Leg A): clips the
   fleet-loaded pmax sum to the **EIA-860 nameplate sum** when it exceeds it
   (double-file corruption). Fallback schema bound.
2. **`cc_nameplate_summer_derate`** rescales net-summer → nameplate via the
   `cc_summer_derate_ratio` (clamped at 1.0).
3. **`cc_capacity_reconcile`** (`--mode cap`/`raise`): caps to / raises to the
   **demonstrated CAMPD p999 peak** — the *measured* capability, which can sit
   above nameplate (cold-weather over-rating) or below it.

The three disagree about which bound wins, and the current order lets the
weakest-justified one clip a stronger one:

- **New Covert (55297)** — the guard clips it to nameplate **1176 MW**, but its
  measured CAMPD demonstrated peak is **1192.4 MW** (a real cold over-rating the
  reconcile table already records). The guard runs *before* the reconcile's
  `min()`, so 1176 wins and **16 MW of demonstrated, measured capability is
  discarded** — a rule-13 inversion (estimate beating measurement).
- **56807 (−69 MW) and 55710 (−7 MW)** — carried phantom net-summer above
  nameplate under the keeper and are **not** in the reconcile table (the derive
  screen's 1.1× cap-margin didn't trip, and 55710 is CT-only so its CAMPD peak
  is understated). The guard correctly removes their phantom, but only to
  nameplate — it never checked whether their *measured* peak is the better bound.

### A.2 The target: one measured-capability stack, ordered by trust

Collapse the three into a single per-plant CC capacity resolved from the most
trustworthy available measurement, **measured > schema > net-summer**:

| plant CEMS state | LP capacity = | rationale |
|---|---|---|
| complete CAMPD record | **demonstrated CAMPD p999 peak** (raise OR cap) | rule 13: measured capability, above or below nameplate |
| CT-only / incomplete CEMS (Leg-B flag) | **EIA-860 nameplate sum** (guard) | CAMPD peak is understated — untrustworthy; nameplate is the schema bound |
| double-file corruption, no clean CAMPD | **nameplate sum** (guard) | schema bound; corruption cleaned |
| clean, CAMPD absent | net-summer (unchanged default) | no better bound |

Concretely: **the demonstrated-peak reconcile is the authority where CAMPD is
complete; the nameplate guard is the fallback where it is not.** The guard must
never clip a plant below a demonstrated peak it has a *complete* CEMS record
for.

### A.3 Work items

1. **Order/precedence fix.** Make the guard clip to `max(nameplate_sum,
   demonstrated_peak)` for plants with a complete CEMS record (i.e., let the
   reconcile's raise/cap value win where it is measured-trustworthy), and to
   `nameplate_sum` otherwise. Cleanest implementation: run the guard **after**
   the reconcile in `fleet_to_bins`, or have the guard consult the same
   demonstrated-peak table. Add a unit test pinning Covert to 1192.4 under the
   keeper (not 1176).
2. **Re-derive the reconcile table to full CC coverage** (`--mode cap` AND
   `--mode raise` in one PJM table). Currently 17 cap-only rows. It should carry
   *every* CC_REGULAR plant whose demonstrated peak differs from its model
   capacity in either direction — including 56807/55710-type plants — so the
   guard is a pure fallback, not the primary bound. Re-derive is a source-data
   action (rule 23), not a residual fit; commit cites the CAMPD vintage.
3. **Exclude CT-only plants from the CAMPD cap** (the Leg-A ↔ Leg-B interaction).
   55710 (Allegheny 3-4-5) is BOTH guarded AND CT-only: its CAMPD p999 is only
   the CT block, so a demonstrated-peak cap would *under*-rate it. Feed the
   Leg-B `_flag_ct_only_reporters` detection (923-net > 1.1× CAMPD-gross) into
   the derive screen's exclusion list so CT-only plants fall back to nameplate,
   never to their understated CAMPD peak.
4. **Deprecate the redundant path if it collapses.** If the unified stack makes
   `cc_nameplate_summer_derate`'s clamped-at-1.0 ratio dead for corrupt plants,
   remove it rather than leave a re-armable knob (rule 26).
5. **Re-gate.** This touches the keeper fleet, so re-solve pjm-110's recipe and
   confirm within-noise (the Covert +16 MW is the only expected dispatch delta;
   the 56807/55710 nameplate values are unchanged unless their demonstrated peak
   is higher). Register as the next PJM run; owner promotes.

### A.4 Cross-ISO consistency — this is ONE model (do this first, it reframes A.3)

The audit that motivated this charter turned up that the CC-capacity stack is
ISO-agnostic in *mechanism* (no `if iso ==` branch in the guard,
`cc_nameplate_summer_derate`, or `_reconcile_cc_capacity`; the reconcile path
resolves per-ISO as `cc_capacity_reconcile_{iso}.csv`; the derive is
ISO-parameterized) — but the *switches and data* have drifted into three
inconsistencies that the unification must fix so it lands as one model, not a
PJM patch:

| ISO | `cc_nameplate_summer_derate` | `cc_capacity_reconcile` | reconcile table | guard |
|---|---|---|---|---|
| ERCOT | off (CAMPD bins) | off | ✓ | always-on |
| CAISO | on | off | **none** | always-on |
| PJM | on | on | ✓ | always-on |
| MISO | off | on | ✓ | always-on |
| NYISO | on | off | **none** | always-on |
| NEISO | on | off | **none** | always-on |

1. **Kill the cross-ISO default-path footgun (rules 24/25).** The ScenarioConfig
   default `cc_capacity_reconcile_path` is hardcoded to **ERCOT's** table
   (`scenarios.py:4179`). Every flag-OFF ISO (CAISO/ERCOT/NEISO/NYISO) carries
   `…_ERCOT.csv` in its config; flip the flag on for CAISO without overriding the
   path and it silently reads ERCOT's demonstrated peaks — a tuned curve crossing
   an ISO boundary. Make the default neutral: resolve `cc_capacity_reconcile_{iso}
   .csv` by the run's ISO (mirror the CLI at `run_calibration_full.py:8879`), or
   `None` → the reconcile no-ops when no ISO table exists. Delete the ERCOT
   literal (rule 25: a deprecated default that still parses is re-armable).
2. **Even out reconcile coverage — derive all six, or document the exemption.**
   Tables exist only for ERCOT/MISO/PJM; CAISO/NYISO/NEISO have none, so the
   *measured* demonstrated-peak bound is unavailable there and the guard
   (nameplate) is their only measured CC bound. Run `derive_cc_capacity_reconcile
   .py --iso {CAISO,NYISO,NEISO}` (full cap+raise coverage, CT-only excluded per
   item A.3.3) so every ISO's CC capacity is on the same measured stack — or, if
   an ISO genuinely shouldn't reconcile (e.g. ERCOT's CAMPD-bin basis already
   bounds it), state that exemption in the derive doc rather than leaving it
   silent.
3. **Decide the guard's gating and apply it uniformly.** The guard is
   unconditional (always-on) while the other two are `ScenarioConfig` flags —
   defensible (it is a schema-integrity fix, net_summer ≤ nameplate, not a
   market feature) but asymmetric. Either (a) gate it `cc_summer_capacity_guard`
   **default-on** for A/B reversibility and symmetry (the `confirmed_exits_enabled`
   pattern), or (b) keep it ungated and document in the fleet loader that it is a
   data validator, not a tunable feature. Make it a deliberate choice, not an
   accident of which session wrote it.

**Guardrails.** No `ScenarioConfig` flag invented for tuning (an on/off gate for
the guard is fine — it is a validator switch, not a knob); the demonstrated peak
is a measured CAMPD input (rule 13-admissible, re-derives only on CAMPD vintage
change — rule 23); no value tuned to a residual; every table stays inside its
own ISO (rule 24). Grade: Opus (cross-ISO derive + PJM re-solve). Other ISOs'
keepers are static bundles — extending their reconcile tables changes only a
forward re-solve, which is the owner's call; do not re-solve them in this charter.

---

## Part B — Next PJM diagnostic Fable session (the open §7 residuals)

pjm-110 leaves PJM at **NOT-YET on C3c** (the LP-vs-MIP scarcity boundary,
confirmed in the pjm-107/108/109 cycle) with the load-bearing criteria all
green. The July-gas diagnosis (§7) named four open leads; the two with real
volume/structure behind them are the Fable session's charter. **Diagnostic
first — no config flip, no solve, until the mechanism is identified and the
gate is pre-committed (rule 1).**

### B.1 Lead 1 — July-2025 coal conduct (the surviving C3c-summer volume lead)

The diagnosis's headline survivor: 2025 July **coal** is **+1.9 TWh** over 923
(COAL_BIT +1.63: West_APS +0.85, AEP_Ohio +0.66, SWMAAC +0.36), i.e. ~2.5 GW of
average phantom mid-merit supply *in the scarcity month* — annual 2025 coal
**+7.7** / gas **−6.8** vs 923. This cushion, not a gas phantom, is the
volume-side suspect for the missing summer half of the C3c tail (model 17 h vs
actual 51 h). **Questions to run (no-LP, measured):** is the 2025 coal-gas split
break a delivered-coal **price vintage** effect (F923 2025 coal price too low
vs gas), or coal **supply/stockpile conduct** the take-or-pay + PRB sigmoid
doesn't carry in 2025 conditions? Decompose the 2025 coal over-run by plant and
month against the F923 delivered-coal series and the CAMPD coal dispatch; check
whether the over-run concentrates on the sub-floor committed multipliers
(DOF-ledger issue #1302). Complement, not alternative, to the owner-closed
reserve opportunity-cost boundary.

### B.2 Lead 2 — CC zonal misallocation / Dominion under-run

The model persistently holds the **Dominion CC belt 5–13 CF-points below
reality** in July (Greensville/Brunswick/Warren run 0.90+ CF actual, model
~0.86) while over-running the AEP-Ohio/Central-PA/ComEd cyclers — 2024-EMAAC
(+1.05 TWh) the largest single cell — with interchange **r = −0.16** vs the
tie-line record *despite the measured seam ladder already on*. Trace whether the
binding constraint is **seam pricing**, the **zonal congestion surface**, or
**Dominion-zone fuel cost**, on the volErr zone-month cells. This is a
merit/congestion allocation signature D-1 hides by class-netting (fleet
profile_r 0.95–0.98 passes), so it needs the **per-plant** view.

### B.3 Supporting instrument — per-plant diurnal cycling metric (D-1p)

The over-runners are flat overnight where reality two-shifts (30–50 % of the
over-run accrues in h0–6); the under-runners are the opposite. Class D-1 nets
this out. Build a **per-plant overnight-turndown shape metric (D-1p)** so the
residual is visible and gateable before any commitment-posture work — it is the
instrument both leads need, and the eventual shape lever (if a PJM offer-floor
corpus supports it) is the ERCOT gas-commitment-bridge pattern.

### B.4 Owner boundary note — C1 930-vs-923 anchoring (deferred, owner)

Document the PJM 930-vs-923 gas/coal divergence (diagnosis §4: the two federal
series *invert the sign* of the 2025 mix error) alongside the interchange
three-way meter note, and decide whether C1's gas/coal rows stay 930-anchored or
move to the 923 basis volErr already uses. Until then, cross-basis deltas
(model-vs-930) must not seed volume charters without a 923 cross-check — the
July-gas diagnosis is the case study. Owner-level scoring decision, not a
dispatch charter.

### B.5 Session shape

Fable design pass → identify the mechanism + pre-commit the gate (rule 1, never
the residual) → hand to an Opus/Sonnet solve session only if a measured,
forecast-native lever is found. If C3c stays short after Leads 1–2, the honest
state is **FAIL-as-disclosed-boundary** (LP-vs-MIP online posture) — do not
reach for an adder/haircut/tuned multiplier (rules 1/11/13/26), and do not
re-open the owner-closed reserve-supply lane.
