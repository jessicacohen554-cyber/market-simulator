# AUDIT — MISO + CAISO committed/must-run offer bands vs SRMC floor (G-21 generalization, #1302)

**Scope:** design + audit only. No solves, no numeric offer value changed, no
keeper touched. This generalizes the PJM Manual-15 SRMC re-grounding
(`pjm-83-srmc-reground` → `pjm-90-cchp-srmc`, `docs/FINDING-pjm-burndown-2026-07.md`
§2, `docs/calibration-log.md`) to MISO and CAISO's committed/must-run offer
bands, per gap-register G-21 / issue #1302. NYISO and NEISO are out of scope
per owner directive. Each ISO's actual re-grounding + re-solve is its own lane
and its own keeper decision — this document only locates the defect pattern
and proposes the numeric target.

## 1. The physical floor rule (mirrors `FINDING-pjm-burndown-2026-07.md` §2)

Every thermal tranche is priced `base_hr × mult × delivered_fuel_price + VOM`,
with `base_hr` the plant's (or class's) own CAMPD-measured average heat rate
(`Plant_Avg_HR_MMBtu_MWh`) and **VOM held constant across bands**
(`data/offer_curves.py`, `docs/offer-curve-methodology.md`). Because VOM does
not move, the only lever a sub-1.0 multiplier has is discounting the fuel term
below the plant's own average-heat-rate fuel cost.

**Physical floor for a non-CHP, non-take-or-pay gas class: committed/econ
bands ≥ 1.0× base_hr** ("Manual-15 composite-cost recovery; the LP has no
no-load variable" — PJM's own citation, `FINDING-pjm-burndown-2026-07.md` §2).
CAISO's tariff-native analog is the **Default Energy Bid (DEB)**: a cost-based
reference level = heat rate × gas price + VOM + a competitive adder (CAISO
Tariff §39.7; cited in-code at `backcast_config.py:440-445` — "the
market-power mitigation Default Energy Bid for a gas unit is cost-based ...
suppliers offer close to short-run marginal cost"). MISO's analog is its
cost-based-offer floor (Tariff Module C / Attachment L: fuel cost × heat rate
+ O&M) sanity-checked in-code against the **MISO IMM (Potomac Economics)
State of the Market Report** (`backcast_config.py:630-633`). A multiplier
below 1.0 on a non-CHP, non-take-or-pay gas tranche has no basis under any of
the three regimes.

**Two classes are legitimate exceptions, both already recognized in the PJM
table and reproduced here:**

- **CHP classes (CC_CHP/CT_CHP)** may legitimately sit below 1.0 **only** when
  the sub-1.0 discount represents the steam host's credit and the plant's
  BTM/must-run steam floor is handled separately — the pjm-90 finding is that
  this reasoning does NOT extend to the grid-delivered economic tranche once
  the BTM share is already netted out (the steam credit is the host's, already
  removed; the grid MWh must bid at power-only cost). So a CHP class sitting
  below 1.0 needs its OWN steam-credit justification, not a blanket pass.
- **Combined-cycle (CC_REGULAR) econ bands may legitimately sit slightly below
  1.0** when backed by the ISO's own measured CAMPD marginal-heat-rate shape:
  unlike a steam boiler (monotonically worse part-load heat rate, so 1.0×
  average is a true floor), a CC's flat efficient operating plateau can run at
  an incremental heat rate *below* its own class-average heat rate (the
  average includes less-efficient min-load/startup hours). Both MISO and
  CAISO have this citation in-code (CAMPD-derived, ISO-local, not an ERCOT
  copy) — see §2/§3.

The failure pattern to find (the "pjm-83 defect"): a **non-CHP class, or a CHP
class's already-BTM-netted grid tranche**, sitting below 1.0× with **no
ISO-specific measured citation** — typically because the value is an
inherited ERCOT-fit ("generic `else`-branch") byte-copy, which rule 25
forbids crossing an ISO boundary.

## 2. MISO audit

Live curve = `_MISO_OFFER_CURVE` (`src/market_sim/pipeline/backcast_config.py:634-697`),
merged onto the rule-24 neutralized (1.0) generic base, confirmed as the
**exact curve in the current keeper** `2026-07-08-miso-47-steamgas-ct`
(`meta.json`: `offer_curve_overrides={}`, `offer_curve_deltas={}`). This
registry was already de-leaked from the ERCOT `else` branch (rule-24 cross-ISO
scrub) for CT_PEAKER/CC_CHP/CT_CHP/ST_GAS.

| Class | Band | Mult | base_hr (cap-wtd, MMBtu/MWh) | Verdict | Citation / provenance |
|---|---|---|---|---|---|
| CC_REGULAR | committed | 1.20 | 7.436 | OK (above floor) | MISO CAMPD part-load premium (min-load ~30–40% above full-load SRMC); ISO-local |
| CC_REGULAR | econ_low | 0.95 | 7.436 | **SURVIVES on physics** (< 1.0 but grounded) | MISO's own CAMPD flat-body marginal HR ≈0.93–0.95× avg — same exception class as PJM CC_REGULAR / CAISO CC_REGULAR (§1); ISO-local, not ERCOT |
| CC_REGULAR | econ_high | 1.08 | 7.436 | OK | MISO CAMPD near-flat full-load shape |
| CT_PEAKER | committed/econ_low/econ_high | 1.0/1.0/1.0 | 12.372 | OK (neutral, not sub-floor) | De-leaked to neutral; **open TODO** (code: "MISO carries no independent CT part-load heat-rate spread yet") — not a defect for this audit, just unrefined |
| CC_CHP | committed/econ_low/econ_high | 1.0/1.0/1.0 | 6.762 | OK | De-leaked to neutral |
| CT_CHP | committed/econ_low/econ_high | 1.0/1.0/1.0 | 6.616 | OK | De-leaked to neutral |
| ST_GAS | committed/econ_low/econ_high | 1.0/1.0/1.0 | 11.270 | OK | De-leaked to neutral |
| **ST_GAS_INTERMEDIATE** | **committed** | **0.85** | **9.917*** | **FAILS — pjm-83 pattern** | Generic default (`backcast_config.py:1539-1546`), **not ISO-scoped, not neutralized** (the class is absent from `_GENERIC_NEUTRAL_GAS_CLASSES`) and **no physical citation for the sub-1.0 committed value** — the class's own doc comment only justifies the *shape* (near-baseload, low peaking share), not pricing below the floor |

`*` cap-weighted `Plant_Avg_HR_MMBtu_MWh` across the five named MISO
ST_GAS_INTERMEDIATE plants (Harding Street 10.824, Ames 14.230, Nine Mile
Point 8.538, Lewis Creek 10.394, Sabine 10.417 — `bin_assignments_MISO.csv`),
weighted by nameplate MW.

**Finding — MISO's headline defect is ST_GAS_INTERMEDIATE, not
`_MISO_OFFER_CURVE`.** `_MISO_OFFER_CURVE` itself is clean at HEAD: its one
sub-1.0 band (CC_REGULAR econ_low 0.95) is the recognized CC-physics
exception, ISO-locally grounded, not an ERCOT byte-copy. But the
**ST_GAS_INTERMEDIATE `committed` band is 0.85× — live in the current MISO
keeper** (`meta.json: st_gas_intermediate=True`, covering Harding Street,
Ames, Nine Mile Point, Lewis Creek, Sabine). This is a bare, ISO-unscoped
generic default, sitting below its own sibling class's design rule:
`CT_INTERMEDIATE.committed = 1.00`, justified in-code as "an always-running
unit amortizes its one start over thousands of hours, so its committed energy
is priced at its own delivered marginal cost (base_HR × ~1.0–1.2)"
(`backcast_config.py:1505-1509`) — `ST_GAS_INTERMEDIATE` explicitly "Mirrors
CT_INTERMEDIATE" in its own comment but its committed multiplier (0.85) does
not follow that rule. At the cap-weighted base_hr above, the gap is
`(1.00−0.85) × 9.917 ≈ 1.49 MMBtu/MWh`, ≈ **$3.3–5.2/MWh underpriced** on the
committed block at MISO's cited 2023–2025 delivered-gas range ($2.19–$3.52/MMBtu,
`config/scenarios.py:4414-4441` coal-sigmoid comments). This is a live,
uncited, active-in-keeper sub-SRMC band — the closest MISO analog to the
original pjm-83 defect.

**Adjacent, already-tracked, NOT part of this deliverable:** the coal PRB/BIT
sigmoid passthrough family (`floor`/`gas_mid`/`gas_slope`,
`config/scenarios.py:4366-4449`) is a *different* mechanism (fuel-price
discount, not an HR-multiplier band) and is already flagged in the gap
register as an ERCOT byte-copy (`gas_mid=2.85`/`gas_slope=2.5` identical
across every ERCOT and MISO entry; MISO PRB `floor=0.78` is also
byte-identical to ERCOT PRB's `floor=0.78`) — tracked under issue #1347, not
re-litigated here.

## 3. CAISO audit

Live curve = `_CAISO_OFFER_CURVE` (`backcast_config.py:471-548`), confirmed as
the **exact curve in the current keeper** `2026-07-07-caiso65-seam-envelope-clock`
(`meta.json`: `offer_curve_overrides={}`, `offer_curve_deltas={}`,
`st_gas_intermediate=False`, `cc_intermediate_split=False`). Unlike MISO/NEISO/
NYISO, **CAISO was explicitly excluded from the 2026-07 rule-24 de-leak scrub**
for CC_CHP/CT_CHP/ST_GAS — the code comment states these three classes are
"PINNED to the values CAISO previously inherited from the generic
ERCOT-lineage `else` branch. They are NOT CAISO-grounded ... preserved
verbatim ONLY so the neutral generic fallback does not silently change the
caiso-51 keeper ... Re-grounding these on CAISO's own DMM/CAMPD data is a
separate, out-of-scope CAISO item" (`backcast_config.py:511-519`). This audit
is exactly that flagged follow-up.

| Class | Band | Mult | base_hr (cap-wtd, MMBtu/MWh) | Verdict | Citation / provenance |
|---|---|---|---|---|---|
| CC_REGULAR | committed | 1.00 | 7.442 | OK | CAISO DMM/CAMPD-grounded (2026-07-04 lever A) |
| CC_REGULAR | econ_low | 0.95 | 7.442 | **SURVIVES on physics** | CAISO's own CAMPD CC flat-body marginal HR ≈0.95× avg = "true incremental SRMC" (in-code citation, `backcast_config.py:492-494`); same CC-physics exception as MISO/PJM — ISO-local, not ERCOT |
| CC_REGULAR | econ_high | 1.21 | 7.442 | OK | CAMPD CC marginal-HR reach |
| CT_PEAKER | committed/econ_low/econ_high | 1.35/1.10/1.50 | 10.862 | OK | NYISO-grounded start hurdle + CAISO DEB cost+adder shape (in-code citation) |
| CC_CHP | committed | 1.00 | 6.902 | OK | CAISO-grounded (2026-07-04 lever A, same min-load-block fix as CC_REGULAR) |
| **CC_CHP** | **econ_low** | **0.96** | **6.902** | **FAILS — pjm-83 pattern** | **Explicitly flagged in-code as NOT CAISO-grounded** — inherited ERCOT `else`-branch byte-copy, "out-of-scope CAISO item" |
| CC_CHP | econ_high | 1.12 | 6.902 | OK-level, ungrounded provenance | ERCOT byte-copy but ≥1.0 — not urgent |
| CT_CHP | committed/econ_low/econ_high/peak | 1.10/1.20/1.20/1.40 | 11.009 | OK-level, ungrounded provenance | ERCOT byte-copy but all ≥1.0 — not urgent |
| **ST_GAS** | **committed** | **0.81** | **11.847** | **FAILS — pjm-83 pattern (direct analog)** | **Explicitly flagged in-code as NOT CAISO-grounded** — this is literally the same numeric value (`0.81`) the base config assigns to *every* non-ERCOT ISO's un-neutralized ST_GAS committed band before the rule-24 scrub (`backcast_config.py:1523`) |
| ST_GAS | econ_low/econ_high/peak | 1.05/1.40/4.20 | 11.847 | OK-level, ungrounded provenance | ERCOT byte-copy but ≥1.0 — not urgent |

**Finding — CAISO carries two live, self-flagged, sub-SRMC bands:** `ST_GAS
committed = 0.81` (gap `(1.00−0.81) × 11.847 ≈ 2.25 MMBtu/MWh`, ≈
**$7.9–11.3/MWh underpriced** at a representative $3.5–5.0/MMBtu CAISO
delivered-gas range, `gas_basis_differential.CAISO = 1.2` over Henry Hub) and
`CC_CHP econ_low = 0.96` (gap ≈0.28 MMBtu/MWh, ≈$1–1.4/MWh, smaller but still
below floor). Both are the **exact pattern PJM's pjm-79/pjm-90 cycle fixed**:
an ERCOT-fit multiplier surviving on a non-ERCOT ISO with no local citation,
and (for CC_CHP) sitting below the SRMC floor on the grid-delivered economic
tranche after the BTM steam credit is already netted out elsewhere. CT_CHP's
bands are also ungrounded ERCOT byte-copies but are not sub-floor, so they are
lower priority.

## 4. Per-ISO re-grounding recipe (NOT applied — design only)

Mirrors the pjm-79/pjm-90 recipe exactly: raise only the sub-floor
multiplier(s) to 1.00 (or the nearest already-grounded sibling value), leave
every already-≥1.0 band untouched, change nothing else in the run recipe.

### CAISO — 2 bands, both in `_CAISO_OFFER_CURVE`

```
"ST_GAS": {
    "committed": 1.00,   # was 0.81 — no non-CHP tranche below power-only SRMC
    # econ_low 1.05 / econ_high 1.40 / peak 4.20 unchanged (already ≥ floor)
},
"CC_CHP": {
    "econ_low": 1.00,    # was 0.96 — steam credit is the host's (BTM-netted
                          # elsewhere via chp_steam_following); grid MWh bids
                          # at true power-only cost, mirroring pjm-90's CC_CHP fix
    # committed 1.00 / econ_high 1.12 unchanged (already ≥ floor)
},
```
Citation for both: CAISO Tariff §39.7 Default Energy Bid (cost-based floor);
CC_CHP additionally mirrors the pjm-90 CC_CHP finding (steam credit belongs to
the BTM-netted host, not the grid tranche). CT_CHP's ungrounded-but-≥1.0 bands
are flagged but **not** in this recipe — no floor violation, so re-grounding
them is a DMM/CAMPD-data-collection exercise (own CAISO cap-weighted HR study,
like the one already done for CC_REGULAR/CT_PEAKER), not a same-day multiplier
flip.

### MISO — 1 band, generic `ST_GAS_INTERMEDIATE` (not `_MISO_OFFER_CURVE`)

```
"ST_GAS_INTERMEDIATE": {
    "committed": 1.00,   # was 0.85 — matches CT_INTERMEDIATE's own committed
                          # = 1.00 design rule ("priced at its own delivered
                          # marginal cost, base_HR x ~1.0-1.2"), which this
                          # class explicitly claims to mirror but didn't apply
    # econ_low 1.00 / econ_high 1.15 / peak 2.20 unchanged (already ≥ floor)
},
```
Citation: MISO cost-based-offer floor (fuel × heat rate + O&M), sanity-checked
against the MISO IMM (Potomac Economics) SOM report — the same floor concept
`_MISO_OFFER_CURVE`'s own docstring already invokes for the sibling
`_MISO_OFFER_CURVE` classes. Because this is a **generic, class-name-keyed**
default (not inside an ISO ternary), raising it to 1.00 would also affect any
future ISO that turns on `st_gas_intermediate` — currently only MISO does, so
in practice this is a MISO-scoped fix, but the recipe should land the fix in a
way that keeps the value class-scoped rather than adding a MISO-only branch
for a class MISO alone uses (avoids a second stale generic default the way
ST_GAS's own `else` arm required a later rule-24 scrub).

`_MISO_OFFER_CURVE`'s CC_REGULAR econ_low (0.95) is **not** in this recipe —
it is the recognized, ISO-locally-cited CC-physics exception (§1), not a
defect.

## 5. Honesty gate

This document is an audit + design artifact only. No `offer_curve_by_group` /
`COAL_SIGMOID_DEFAULTS` value has been changed, no config file has been
edited, and no run has been solved. Each recipe above still needs: (a) an
owner go-ahead to spend a re-solve, (b) the full 2023–2025 bundle (rule 16),
(c) leave-one-year-out re-scoring before promotion (rule 16/holdout policy),
and (d) its own keeper decision (rule 1 — a structurally-correct fix is not
auto-promoted just because it clears this audit; PJM's own ST_GAS fix
*worsened* its C2 volume fit and was promoted anyway on structure, and MISO/
CAISO's fixes should expect the same rule-14 disposition: a worse number here
is a discovered bug elsewhere to root-cause, not a reason to revert).
