# PRE-REGISTRATION — pjm-135 `pjm_external_net_position_cut` (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document
does not contain cannot be quoted as a pass. Format follows
`PREREG-pjm134-apsouth-joint-cut-2026-07-27.md`, **mirrored, not copied**.

Chartered by `FINDING-pjm135-star-node-import-2026-07-28.md` (this session's
M1/M2/M3/M4 measurements, all no-LP, all on already-committed data), which was
handed the question by `FINDING-pjm134` §7: the `PJM_external → PJM_Dominion`
star-node link carries **+2,266 MW / +19.9 TWh/yr** in the keeper-lineage arm A,
larger than Dominion's entire 12.1 TWh fossil deficit.

**Promotion is NOT pre-granted** and is not requested by this session. It remains
a separate owner act, and (rule 22 `[R-HOLDOUT]`) a structural mechanism change
is scored leave-one-year-out within 2023–2025 before any promotion.

---

## §0 — what the measurements found, and how it reshaped the charter

The session charter proposed a **border-attribution correction** (M1: "an
attribution that hands Dominion a ~2.3 GW continuous import band it does not
physically have is the answer"). **The measurements refute that specific
reading and redirect the delta.** Machine output:
`results/probes/pjm135_star_node_import.json`,
`results/probes/pjm135_star_node_net_position.json`.

| test | result | verdict |
|---|---|---|
| **M1** border attribution | `_PJM_TIE_ZONE` maps **all 22** ties in the file (no fallback); Dominion's four (TVA/CPLE/DUK/CPLW) are genuinely Carolinas/TVA-facing, and Dominion **measurably net-imports 1,329/1,395/1,288 MW = 11.6/12.2/11.3 TWh**, importing in 86–93 % of hours. The band is not fabricated — it is **over-sized**: 2,268/2,485/2,471 MW = 19.9/21.8/21.7 TWh, **1.71/1.78/1.92×** the measured net | **partly — the map is sound, the BAND is not** |
| **M2** shape | the band is a (month × hod) p95 climatology — 281–286 distinct values over 8,760 h, CV 0.19–0.35 against a measured 0.56–0.80, sitting **above** the measured flow in **93.4 %** of hours by construction. R² vs the measured hourly import is **negative every year** (−1.04/−1.19/−0.43); even the best possible month×hod table (the bucket *mean*) reaches only 0.41/0.37/0.59 | **YES — a capability envelope ridden as an energy schedule** |
| **M3** degeneracy guard | `PJM_external` clears at the **identical dual to every PJM zone in 100.00 % of hours**, all three years, **max \|Δ\| = 0.0000 $/MWh** (EMAAC alone separates, in 4.0/2.3/2.9 %) | **YES — and it is binding on the charter** |
| **M4** net position (not degenerate) | the `import` class in the committed sidecars **is** the LP's net interchange: **−28.89/−21.86/−25.80 TWh** against a measured **−39.98/−32.83/−32.93 TWh**. The star node supplies PJM with **+11.09/+10.97/+7.13 TWh/yr** the real seam did not. Hourly R² **negative** (−0.015/−0.220/−0.042), corr +0.57/+0.42/+0.40 | **YES — the real, measurable defect** |

**M3 is why this delta is not the one the charter guessed.** A per-border
re-attribution is provably re-routable: with every zone at one dual, moving
Dominion's band simply moves the import to ATSI or ComEd and rails it back at
zero cost — the AP-South failure mode (`FINDING-pjm134` §7) one level up. The
**+19.9 TWh "external → Dominion"** figure is itself a degenerate vertex
artifact and **is not treated as a target anywhere in this prereg.**

What is **not** degenerate is the **aggregate**: `Σ_z Flow(PJM_external → z)` is
the LP's own net interchange, it is measured wrong by 7–11 TWh/yr, and only an
aggregate constraint can bind it.

## §1 — the delta (ONE switch, one mechanism, ZERO new free parameters)

**Arm B** = the keeper recipe replayed at this session's HEAD **plus the single
flag**:

```
scripts/replay_keeper.py results/calibration/pjm121_ccbelt \
    --out-dir results/calibration/pjm135_netpos_B \
    --set pjm_external_net_position_cut=true \
    --note "pjm-135 measured star-node NET-position joint cut (single delta)"
```

- **Arm A** `results/calibration/pjm135_control_A` — keeper recipe, no delta,
  same HEAD, same container, same regenerated `clean` tree (regenerated before
  either solve). NOT a keeper candidate; registered as the run explorer's
  control arm per rule 15.
- Both arms `--year 2023 2024 2025` in ONE invocation (rule 16), years
  **sequential** within each run, arms **sequential** to each other (rule 12 +
  the pjm-133 §9 memory fact: a PJM per-plant year-solve peaks at 14.8–15.2 GB).
- Nothing else is bundled with this delta.

**Base-recipe note, stated up front.** The designated PJM keeper is
`2026-07-27-pjm-133-nameplate`, which carries one further flag
(`hydro_budget_nameplate_aware`). This A/B is run on the **pjm-121 recipe**, as
pjm-132 and pjm-134 were, so arm A is byte-comparable to that control lineage.
The delta is orthogonal to the hydro flag (an external-seam transfer constraint
vs a hydro budget allocation); re-basing onto the pjm-133 recipe is a
promotion-time step, not a validity condition for this comparison.

**What the flag does**
(`model/interchange/pjm.py::build_pjm_external_net_position_cut_groups`,
`data/eia930/envelopes.py::pjm_net_interchange_envelope`): ONE one-sided
aggregate interface-group row per hour caps the summed injection across all five
star links

```
Σ_z Flow(PJM_external -> z)  <=  P_p95( measured net import | month(t), hod(t) )
```

at the measured net-position envelope. It is the **exact construction** of the
already-shipped `pjm_east_interface_cut` and `pjm_apsouth_interface_cut` — the
shared `_build_joint_interface_cut` core, `bidirectional=False`, signs all +1 —
carried from the internal flowgates to the external seam.

- **DRIVER (rule 14 `[R-ACCURATE]`)**: the star node is bounded **only** by
  *marginal* per-border, per-direction percentiles. `build_pjm_external_flow_groups`
  caps each link's signed flow at that border's own p95;
  `inject_pjm_seam_flow_limit` sizes each neighbor's bands from the same rows.
  Five marginal 95th percentiles are summed as though they were a joint one, and
  **nothing anywhere bounds the total**. Measured (M1b): the sum-of-marginals
  import ceiling is **4,235/5,140/5,358 MW** against a joint p95 of the
  simultaneous total of **3,309/3,855/3,996 MW** — a **925/1,285/1,362 MW**
  (1.28/1.33/1.34×) gap that exists purely as an artifact of the arithmetic.
  The per-neighbor bands compound it: `INTERFACE_NEIGHBORS` border zones
  overlap, so the same envelope rows are counted twice (Dominion, via Carolinas
  + TVA) and three times (AEP_Ohio, via MISO + TVA + LGEE), lifting the seam-band
  ceiling to 6,506/7,649/8,015 MW.
- **DOF added: zero** (rule 24 `[R-DOF]`). Same tie-line file
  (`PJM_<year>_import_export_act_sch_interchange.csv`), same existing constant
  `PJM_EXTERNAL_FLOW_PERCENTILE = 95.0`, same (month × hour-of-day) bucketing.
  No scale, no haircut, no blend, no new percentile.
- **Rule 13 `[R-MEASURED]`**: no outcome is pinned. A net-position capability
  envelope regenerates for a forward year from the same feed and responds to
  changed conditions; forecast years have no measured tie file, the envelope is
  `None`, and the node is left uncapped (the two-track construction
  `pjm_measured_interface_limits` already uses).
- **Rule 19 `[R-ONE-MECH]`**: this **REPLACES** the sum-of-marginals ceiling on
  the *aggregate* question rather than stacking. The joint cap dominates (a sum
  under the limit implies each term is), so the per-border groups keep the
  **locational** bound while this row owns the **total**. No new floor is added
  to any class. *Stated honestly for the record:* the star node already carries
  three mechanisms (per-link envelope, per-neighbor bands, measured price
  ladder). None of them constrains the net position, which is the phenomenon
  this row owns — but a reader who counts mechanisms rather than phenomena will
  see a fourth, and that reading is on the table for the owner.
- **Rule 25 `[R-ISO-SCOPE]`**: gated on `config.iso == "PJM"` and on the priced
  star node; every other ISO and all forecasts are byte-identical.
- **Rule 1 `[R-STRUCT]`**: chartered because a market model with no statement
  about its own net interchange position is structurally incomplete, **not**
  because it is predicted to close the Dominion residual. §4 pre-registers, with
  numbers, that it **cannot** close it.

## §2 — the baseline this is measured against (arm A, pre-declared)

| quantity, arm A expectation | 2023 | 2024 | 2025 |
|---|---|---|---|
| net interchange (`import` class) | −28.89 TWh | −21.86 | −25.80 |
| measured net interchange | −39.98 TWh | −32.83 | −32.93 |
| hours net position exceeds the measured p95 envelope | 23.48 % | 21.22 % | 18.56 % |
| hours net position exceeds the bucket **maximum** ever observed | 9.34 % | 11.72 % | 10.71 % |
| `PJM_external` dual tied to `PJM_Dominion` | 100.00 % | 100.00 % | 100.00 % |
| slack / dump | 0 / 0 MWh | 0 / 0 | 0 / 0 |
| Dominion fossil Δ (model − EIA-923) | −20.0 TWh | −19.8 | −12.1 |
| Dominion CT_PEAKER (model / actual TWh) | 0.68 / 7.38 | 1.25 / 8.68 | 2.46 / 9.64 |
| Dominion CC_REGULAR (model / actual TWh) | 31.76 / 41.70 | 41.10 / 49.27 | 48.33 / 49.23 |

**Arm-A identity check (pre-declared, K5 below):** arm A must reproduce
`pjm134_control_A` — and therefore `pjm132_control_A` / `pjm129_meritguard_a1` —
to **0.000000 MW on every class, every hour, all three years**. Arm A is NOT
compared to the committed `pjm121_ccbelt` bundle (FINDING-pjm133 §2: that bundle
sits on the pre-guard outage envelope).

**Envelope expectation, pre-declared so it cannot be mistaken for the delta:**
both arms are expected to score **NOT-YET** with **C1 / C3a / C3c FAIL** and
D1/D2 FAIL. That is the pre-existing pjm-129/132/134 control-lineage
determination, not this delta's doing.

## §3 — PRIMARY (structural, sign-based, not a fit target)

The PRIMARY is that **the constraint the model was missing is enforced, and
enforced in the measured direction**. It is deliberately NOT a volume or price
target: rule 1 forbids judging a structurally-correct mechanism by the residual.

**P1 — enforcement.** In every year, arm B's net interchange satisfies the
measured envelope in **100.00 %** of hours — i.e. the share of hours whose net
position exceeds the measured (month × hod) p95 falls from arm A's
**23.48 / 21.22 / 18.56 %** to **0.00 %**. This is the mechanism's own contract;
anything above 0.00 % is an implementation failure, not a result.

**P2 — measured direction.** In every year, arm B's annual net interchange moves
**toward** the measured value and never past it: arm A −28.89/−21.86/−25.80 TWh,
measured −39.98/−32.83/−32.93 TWh, so arm B must land in
`(measured, arm A]` — more exporting than arm A, not more exporting than
measured. Grounding, not fitting: the cap is a *ceiling* on net import, so it
can only ever reduce imports; landing beyond the measured value would mean the
envelope is mis-signed.

**P3 — no export forcing beyond the measurement.** The hourly cap equals
`pjm_net_interchange_envelope` verbatim in every hour (no clamp, no floor), the
group is one-sided (`bidirectional=False`, `lower_cap=None`) so **net export is
never bounded**, and every per-link TTC is unchanged. Verified from the limit
array and the group construction; pinned by
`tests/iso/pjm/test_pjm_external_net_position_cut.py`.

**Reported, NOT gated (rule 1):** Dominion CT_PEAKER / CC_REGULAR volume gaps,
the zonal displacement table, the ISO-wide fossil balance, and every rubric
criterion. These are the *interesting* numbers and they are published whatever
they say — they are not the delta's pass condition.

## §4 — the expected magnitude, pre-computed, and INERT pre-registered

**This delta is pre-registered as unable to close the Dominion defect.** From
arm A's own committed net-position series against the envelope, the energy the
cap removes — holding all other flows fixed — is:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| hours the cap binds | 23.48 % | 21.22 % | 18.56 % |
| energy clipped | **1.54 TWh** | **1.80 TWh** | **1.73 TWh** |
| net position, arm A → first-order arm B | −28.89 → −30.43 | −21.86 → −23.66 | −25.80 → −27.53 |
| share of the net-position error closed | ~14 % | ~16 % | ~24 % |

**1.5–1.8 TWh against a Dominion fossil deficit of 12.1–20.0 TWh**, and M3
guarantees the displaced energy is replaced wherever the copper-plate finds it
cheapest — which the pjm-134 lineage says is western coal, not Dominion CT. A
result in which **Dominion CT_PEAKER / CC_REGULAR barely move is the expected
outcome and is published as a PASS of the PRIMARY**, exactly as pjm-134's INERT
verdict was. If P1 holds and the Dominion classes do not move, the determination
is **ENFORCED-BUT-INERT-ON-THE-DEFECT**, and that is a finding about the
copper-plate, not a failure of the mechanism.

**No-feedback ceiling (binding on this session and any follow-up):** there is
nothing in this mechanism to re-parameterise, and nothing may be added. In
particular **no multiplier, percentile sweep, haircut, blend, scale factor or
scarcity exemption may be applied to the net-position envelope**, in this
session or a successor, whatever the result. `PJM_EXTERNAL_FLOW_PERCENTILE`
stays at its existing 95.0; it is **not** a knob this delta may turn. A cap that
binds too much or too little is a discovered fact about the envelope's
construction, not a setting. Extending the joint construction to a *different*
aggregate is a new charter with its own prereg.

## §5 — pre-registered kills (structural failure modes, not residual movement)

| id | test | threshold | fires ⇒ |
|---|---|---|---|
| **K1** | **C3a guard** — the standard house no-feedback ceiling | C3a degrades by more than **+0.75 pp** in any year | report the degradation prominently; delta is not promotable without root-cause |
| **K2** | **load shedding** — the identified principal risk (see below) | arm B `slack` > 0 or `dump` > 0 MWh in any year (arm A: exactly 0 / 0) | **KILL.** A measured net-position envelope must never make the ISO infeasible; this means the (month × hod) conditioning is wrong for scarcity hours |
| **K3** | **export forcing / mis-signed cap** | the group gains a reverse bound, any per-link TTC changes, or arm B's annual net export exceeds the **measured** value in any year | **KILL.** Violates P2/P3 and the mechanism's contract |
| **K4** | **determination regression** | arm B's rubric determination class is worse than arm A's | report; not an automatic kill (rule 1), but blocks promotion pending root-cause |
| **K5** | **arm-A identity** | arm A differs from `pjm134_control_A` by more than 0.000000 MW on any class-hour | **KILL the comparison** — the A/B is not single-delta and must be re-solved |

**K2 is the identified principal risk and is stated in advance, with numbers.**
The envelope is conditioned on (month, hour-of-day) but **not** on system
stress, so in a genuinely tight hour it can sit below what PJM actually imported
that hour. Measured on arm A: the cap binds in **93.2 / 92.1 / 96.6 %** of the
top-1 % load hours, clipping **1,428 / 1,487 / 2,334 MW** on average there. If
PJM's internal fleet covers that with zero slack and zero dump, the envelope's
conditioning is adequate and the mechanism is validated. If it sheds load, the
mechanism is **wrong for this topology** and K2 fires — and per §4's ceiling the
remedy is **not** a relaxed percentile or a scarcity exemption; it is a kill and
a published finding.

**K1's asymmetry is deliberate.** C3a is a *guard*, not a target: it exists so a
structural change cannot buy its structure by wrecking the price tail. It is
reported in both directions and is never optimised toward.

## §6 — instruments, committed with this prereg

- `scripts/probes/_pjm135_star_node_import.py` — M1/M2/M3, no LP. Machine
  output `results/probes/pjm135_star_node_import.json`.
- `scripts/probes/_pjm135_star_node_net_position.py` — M1b/M4, no LP. Machine
  output `results/probes/pjm135_star_node_net_position.json`.
- `scripts/probes/_pjm135_netpos_ab.py` — the A/B scorer (committed before the
  arms solve; reads both bundles' `hourly/` sidecars, no replay). Machine
  output `results/probes/pjm135_netpos_ab.json`.
- `tests/iso/pjm/test_pjm_external_net_position_cut.py` — pins the group span,
  the one-sidedness, the negative-cap passthrough and the off-state cache key.
- `legitimacy_diagnostics.json` generated for **BOTH** arms before scoring.

## §7 — what this prereg does NOT authorise

- Any change to `_PJM_TIE_ZONE` or the per-border attribution (M1: the map is
  complete and geographically sound; the defect is the band's size, not its
  address). The one internal inconsistency found — `_PJM_TIE_ZONE` puts the
  whole TVA tie on Dominion while `INTERFACE_NEIGHBORS` splits TVA across
  AEP_Ohio and Dominion — is **reported, not fixed here**; it is a separate
  charter.
- Any per-border re-attribution delta of any kind (M3: provably re-routable).
- Any change to `PJM_EXTERNAL_FLOW_PERCENTILE`, `pjm_seam_flow_percentile`, or
  any other percentile in the seam family.
- Any re-opening of the AP-South cut or its parameterisation
  (`FINDING-pjm134` §8, binding).
- Any bundling with the hydro nameplate flag or anything else.
- Any solve, scoring or registration outside 2023–2025 (rule 22 `[R-HOLDOUT]`).
- Any change to the PJM keeper designation, which is an owner-only act.
