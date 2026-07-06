# FOM + scarcity joint protocol — Stage-3 addendum: backstop-OFF grid variant (2026-07-06)

*Stage-3 addendum to `fom-scarcity-joint-protocol-2026-07-05-stage2.md`. Executes
the Stage-2 report §3 / plan §5.4 **unblocking path (b)**: re-run the ERCOT FOM
grid with the adequacy backstop **disabled**, to test whether the FOM axis
becomes observable once the backstop isn't flooding CT and collapsing scarcity.
Forecast probes only — nothing registers on the backcast dashboard, nothing
touches 2022 / H1-2026 (rule 22). The ATB flip stays **frozen** pending the
plan's §5.4 gates; this is a diagnostic, not a flip.*

**Headline: backstop-off does NOT unblock the FOM axis — the defaults stay
frozen.** With the harness-enabled adequacy backstop removed
(`reserve_margin_build_enabled=False`, a harness variant via the new
`run_fom_scarcity_grid.py --backstop-off` flag — **not** a model-default change),
the capacity trajectory is again **byte-identical across the FOM axis** in all
six ERCOT cells: **zero economic retirements anywhere**, CO₂ identical to the
tenth of a Mt, prices identical. Flipping CT 8→21 / CC 12→30 / coal 40→45 still
moves zero MW and zero tonnes. Grid JSON:
`fom-scarcity-grid-2026-07-06-stage3-backstop-off.json` (ERCOT leg only,
`--skip-pjm`; 6 cells, 2026-2031, mid growth, legacy equal-width fleet).

## What changed vs Stage 2, and what didn't

| Quantity (atb × ordc cell) | Stage 2 (backstop ON) | Stage 3 (backstop OFF) |
|---|---|---|
| economic thermal retired | 0 GW | 0 GW |
| backstop forced-build, first 3 yr | 15,214 MW | **0 MW** (backstop off) |
| floor-retained MW, 2027 → 2031 | 12,678 → 59,493 | 12,678 → 36,325 |
| CO₂ 2026-2031 cumulative | 1105.6 Mt | 1110.5 Mt |
| avg price 2026 → 2031 | (collapsed by CT flood) | 22.9 → 40.9 $/MWh |
| FOM axis moves anything? | no | **no** |

**The masking mechanism shifted; the masking did not lift.** In Stage 2 two
mechanisms hid FOM: the accredited floor un-retired every eligible unit, *and*
the backstop flooded 15 GW of CT that collapsed scarcity. Remove the backstop and
the **accredited floor alone is sufficient** to keep the FOM axis inert — it
un-retires every screen-eligible unit (34–47 GW flagged by 2029), so no economic
retirement ever reaches the point where a going-forward FOM bar would decide it.
FOM is a *cost bar on a retirement that never happens*.

## The deeper finding: the floor is upstream of the price signal, so no scarcity emerges

The point of path (b) was that, absent the backstop, mid-growth adequacy shortage
would express as **scarcity price** the screens could see — lifting revenue and
making the *relative* FOM bar matter. It does not, because the floor sits
**upstream of the price signal**: by retaining every eligible unit, it keeps the
fleet physically whole, so dispatch is never short and prices stay low
(**mean $22.9 → $40.9/MWh across 2026-2031, no scarcity spike**). The ERCOT
mid-growth system is **accredited-short but dispatch-long** — the UCAP/ELCC
adequacy ledger says the requirement is unmet, but the physical fleet the floor
preserves clears energy with ample headroom, so the ORDC overlay has nothing to
price (the `ordc` and `coopt` cells are within rounding of the `off` cell). The
scarcity-free signal Stage 2 attributed to the backstop flood is really produced
by the floor one layer up; removing the backstop cannot reveal a scarcity that
the floor prevents from forming. (This is the forecast-side twin of the ERCOT
capacity-hindcast s3 finding — a perfect-foresight LP on a fleet the floor keeps
whole is structurally long.)

## Acceptance gates (plan §5.4)

| Gate | Observed (atb × ordc, backstop off) | Pass? |
|---|---|---|
| 2026-2028 thermal retirement pace 0.5-2 GW/yr | 0 GW (floor retains all eligible) | ✗ |
| Backstop ≈ 0 in years 1-3 | 0 MW (trivially — backstop off) | ✓ (vacuous) |
| Overall | — | **✗** |

The backstop gate now passes vacuously (there is no backstop), but the retirement
pace gate fails identically to Stage 2: 0 GW/yr, because the floor — not the
backstop — is what retains the fleet.

## Decision & disposition of the unblocking paths

**DO NOT flip.** The ATB values (21/30/45) remain the frozen, externally-identified
targets (Stage-2 DOF ledger unchanged). Path (b) is now **closed as a negative
result**: disabling the backstop does not make FOM observable — it hands the
masking from the backstop to the accredited floor, which was always the dominant
blocker (plan Stage-1 note, prerequisite A). The three Stage-2 unblocking paths
resolve as:

- **(a) Foresight lookahead** (plan §2.3 / §2.4, `run_foresight_ab.py`) — the
  live open path; A/B re-run recorded separately in the plan doc §2.4. Whether the
  lookahead arm closes the adequacy gap economically (so the floor stops binding)
  is exactly what it measures.
- **(b) Backstop-off grid** — **this addendum: NO.** The floor masks FOM without
  the backstop's help.
- **(c) Non-short demand paths** — untested here; the natural next probe is a
  demand path (or an accreditation basis) under which ERCOT is not perpetually
  accredited-short, so the floor stops un-retiring the whole eligible set. Not run
  this session.

**Root-cause pointer (rules 1/11/14).** The real blocker is the
**accredited-short-but-dispatch-long** gap: the floor's UCAP/ELCC adequacy ledger
declares a shortage the energy dispatch does not have, so the floor over-retains
and both the FOM axis and the scarcity price signal are suppressed. Fixing that is
a floor/accreditation-calibration question (does the ERCOT PRM × accredited-basis
requirement match the physical adequacy the dispatch shows?), **not** an FOM or a
revenue-stack tuning — and it lives in `capacity.py`, which is quiet this wave
(recorded as a recommendation, per the no-model-code-changes scope guard).

*Grid JSON: `docs/handoffs/fom-scarcity-grid-2026-07-06-stage3-backstop-off.json`.
Produced 2026-07-06, W2-P3 Stage 3. Harness variant only; no model default or
`capacity.py` change.*
</content>
