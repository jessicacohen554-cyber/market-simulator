# nyiso-58-tempderate — temp-derate full-keeper rerun (PROBE)

Byte-faithful replay of the `2026-07-07-nyiso-56-measured-zonal` keeper's
recorded solve kwargs (`replay_keeper.build_kwargs` on the keeper's own
`meta.json`) with `temp_dependent_derate=True` added — nothing else changed.
All three train years (2023-2025) in one bundle per CLAUDE.md rule 16.
Registered as a dashboard PROBE, never a keeper promotion
(`docs/handoffs/temp-derate-keeper-rerun-playbook-2026-07.md`).

## hoursGt300 (DA-expressible, NYISO/NEISO $300 threshold)

| year | keeper | this probe | ablation twin | actual (DA) |
|---|---|---|---|---|
| 2023 | 21 | 39 | 49 | 1 |
| 2024 | 0  | 2  | 2  | 0 |
| 2025 | 14 | 36 | 44 | 12 |

Scarcity tail gets WORSE in every year vs the keeper (moves further from
actual), unlike the single-year ERCOT/PJM validation probes where the
mechanism closed an undershoot. NYISO's keeper was not undershooting scarcity
hours to begin with (2023 already 21h model vs 1h actual; 2025 was close at
14h vs 12h) — the added hot-hour capacity tightening pushes both years further
into overshoot.

## Other structural deltas vs keeper

- C1 fuel-mix / C2 system volume / C4 dispatch correlation / C5a CO2:
  essentially unchanged (confirms the CC/CT reshape is capacity-neutral as
  designed; NYISO has no coal fleet for the additive COAL/ST_GAS channel to
  matter at scale).
- C3a mean LMP: mixed — 2023 regresses (31.59→37.21 vs actual 30.29, now
  overshoots), 2024/2025 improve (closes real undershoot: 2024 33.18→34.88 vs
  actual 35.95; 2025 56.21→61.71 vs actual 60.74).
- C3b price shape: 2023 regresses sharply (0.188→0.421 stat), 2024/2025
  roughly unchanged.
- C8 forced-energy share (ST_GAS at the reliability floor): improves
  slightly in all three years (30.5/44.6/38.2% → 27.8/41.2/34.4%) — the
  probe's raw FAIL label is an artifact of no governance attestation/ledger
  on an unattested probe bundle, not a magnitude regression.

## Root cause of the 2023 regression (investigated 2026-07-09)

Isolated the 2023 C3a/C3c regression. It is **downstate locational
reserve-scarcity over-firing**, NOT load-shed and NOT a transmission bottleneck:

- The spurious >$300 hours (e.g. Aug 14 & Aug 21 2023, when the real RT LBMP
  was only $45–65) clear at $2000 driven by **`reserve_price` $909–$1336**, not
  by unserved energy. Annual model load-shed is ~830 MWh (5 thin-margin
  instances); the keeper (flat derate) sheds **zero** MWh yet still posts 15
  false >$300 hours — so the tail is a reserve-co-opt price artifact in both.
- In the false-VOLL hours **no transmission link binds**; Central-East is at its
  month-specific *measured* DAM-posting limit but downstate imports and the
  Lower_Hudson→NYC interface sit below their caps. The pocket is short on
  reserve-eligible **headroom**, not energy transfer capacity.
- Mechanism: temp-derate (an accurate physical input, rule 11) trims the
  downstate CT/peaker fleet's available capacity on warm-but-not-extreme
  afternoons (30–31 °C, well below the 34 °C summer peak). That fleet supplies
  the East 10-min (1,200 MW / $775 RCPF) and SENY 30-min (1,300 MW / $500 RCPF)
  reserve families. With less peaker headroom the requirement shorts and the
  **correctly SOM-sourced** RCPF penalties fire and stack ($775+$500 ≈ the
  ~$1,300 reserve prices observed), lifting every downstate zone's LBMP.

**This is a PRE-EXISTING weakness the keeper shares** (keeper: 15 false >$300
hours in 2023 on the same non-event days; temp-derate deepens it to 39). The
reserve requirements and penalties are already primary-source (NYISO SOM)
grounded — they are not the bug and must not be tuned down (that would be a
residual-fit, rules 1/24). The genuine physical suspect is that the temp-derate
CT slope (0.0126/°C, a *frame*-GT literature value) over-derates NYC's largely
**aeroderivative** peaker fleet, which is less temperature-sensitive — but
resolving that is a mechanism-level refinement (per-turbine-technology derate,
needs EIA-860 turbine-model data + cross-ISO validation), not a promotion-time
knob. The condition-varying downstate reserve requirement (#1344 Ask-B) that
would also discipline this remains **data-blocked** per the keeper attestation.

Recommendation: **DO NOT PROMOTE.** Per rules 1 & 11 the temp-derate mechanism
stays available (it is directionally correct and improves 2024/25 C3a/C8), but
promoting nyiso-58 now would enshrine a load-bearing C3a/C3c regression whose
root cause is an unresolved (partly data-blocked) downstate reserve-adequacy
interaction. nyiso-58 becomes a legitimate keeper candidate only after the
aero-vs-frame CT-derate refinement and/or the #1344 dynamic reserve requirement
land — both of which improve the keeper baseline too. Keeper stays
`2026-07-07-nyiso-56-measured-zonal`.
