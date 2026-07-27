# ASK — pjm-134: the Dominion CT/CC zonal inversion (FILED, NOT BUILT)

**Raised by the owner** during the pjm-133 session (2026-07-27): *"we need to fix
Dominion severe CC regular and CT peaker underrun every year."* Measured and
attributed here so the diagnosis is not lost; **nothing was built, nothing was
bundled into pjm-133** (that session is a single-delta hydro A/B, and
FINDING-caiso130 §7 forbids bundling anything with it).

All numbers below are read from **committed run payloads** — the dashboard's own
grid-delivered `volErr.zoneMon` (`m` = grid-LP model TWh, `a` = EIA-923 net gen ×
grid fraction). No LP was solved for this ask.

---

## §1 — the defect, measured

**PJM_Dominion, model vs actual (TWh), `2026-07-25-pjm-121-cc-belt` keeper:**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | 29.33 / 41.70 = **−29.7 %** | 38.46 / 49.27 = **−22.0 %** | 45.67 / 49.23 = −7.2 % |
| CT_PEAKER | 0.70 / 7.38 = **−90.5 %** | 1.28 / 8.68 = **−85.2 %** | 2.62 / 9.64 = **−72.9 %** |

Dominion carries **71–72 %** of the ISO-wide CC_REGULAR under-side in 2023/24 and
**50–57 %** of the CT_PEAKER under-side in all three years. The CT_PEAKER row is
the more serious of the two: a class running at a tenth to a quarter of its
measured output for three consecutive years is a structural fault, not a
calibration residual.

## §2 — it is an ALLOCATION INVERSION, not a level error

ISO-wide nets are small; the gross zonal offsets are an order of magnitude
larger. CT_PEAKER 2025: net **−1.34 TWh** = **+10.97 over** against **−12.31
under**. CC_REGULAR 2023: net −8.36 = +8.82 over against −17.18 under.

Capacity factor by zone, CT_PEAKER 2025, against EIA-860 `GT` nameplate mapped
through the model's own `build_zone_lookup`:

| zone | GT MW | units | model CF | actual CF |
|---|---|---|---|---|
| PJM_ComEd | 7 728 | 107 | 10.0 % | 4.5 % |
| PJM_AEP_Ohio | 7 501 | 98 | **19.5 %** | 10.1 % |
| **PJM_Dominion** | **5 654** | **74** | **5.3 %** | **19.5 %** |

**Dominion and AEP_Ohio are almost exactly swapped.** The model dispatches
roughly the right ISO-wide peaker energy and puts it in the wrong zones.

**This rules out the cheap explanations.** The capacity is present (5.7 GW, third
largest in PJM) and correctly zoned — and it is present *in the model*, because
the `volErr` aggregation only emits a (zone, class) cell for plant codes carried
in the model's own dispatch. So this is neither a missing-fleet bug nor a
zone-assignment bug. It is an economics or transmission question.

## §3 — why the measured-offer-surface family cannot reach it

The pjm-103 / 104 / 121 / 132 lane re-conditions **offer prices ISO-wide**. This
defect is about **which zone clears**, not at what price the ISO clears — so the
family is structurally incapable of touching it. That is now measured, not
argued:

| PJM_Dominion 2025 | CC_REGULAR | CT_PEAKER |
|---|---|---|
| `2026-07-27-pjm-132-control` | 45.21 (gap −4.03) | 2.46 (gap −7.18) |
| `2026-07-27-pjm-132-withinseason` | **45.21 (gap −4.03)** | **2.46 (gap −7.18)** |

Identical to the cent — the within-season delta moves Dominion by **0.00 TWh**.
Consistent with FINDING-pjm132's own ISO-wide verdict (INERT at the price level,
Lane 2 ends).

**Correcting a plausible reading:** the 2025 CC_REGULAR improvement
(−29.7 % → −7.2 %) is a **year effect, not a code fix**. It is already present in
the pjm-121 keeper, which predates pjm-132 entirely; the pjm-132 control
reproduces it at −8.2 %; and the only thing separating keeper from control there
is the merit guard, worth −0.46 TWh in the *worse* direction. No committed run
has ever moved Dominion.

## §4 — the two candidate causes, and the no-LP tests that separate them

**C1 — zonal gas basis.** The keeper runs `pjm_zonal_gas_basis`. If Dominion's
delivered gas is priced above AEP_Ohio's and ComEd's in the model, its CTs sit
behind theirs in merit order in every hour, which is exactly the observed
inversion. *Test (no LP):* read the committed per-zone basis series and rank
Dominion against AEP_Ohio/ComEd by month; compare that ranking to the measured
delivered-gas ranking (F923 / the zonal hub series). A model ranking that
inverts the measured one is the answer on its own.

**C2 — west→east transfer capability.** If the Dominion-facing interfaces are
too permissive, western coal and CC serve Dominion load and displace its local
CT/CC. Circumstantial support: PJM interchange is independently badly modelled —
model vs bench 27.83/39.98 (2023), 21.52/32.64 (2024), 25.12/17.97 (2025), with
`r` falling to **−0.14** and NRMSE **1.47** in 2025, i.e. anti-correlated with
the measured series. The relevant mechanisms (`pjm_east_interface_cut`,
`pjm_congestion`, `pjm_seam_flow_limit`, `pjm_measured_interface_limits`) are all
already live, so this is a limit-value question, not a missing-mechanism one.
*Test (no LP):* binding-share and flow-direction histogram on the Dominion-facing
links from the keeper's committed hourlies, against the measured
transfer-constraint-binding partition.

Run **both** tests before proposing any delta. If C1 fires, the fix is a data
correction (rule 14) and carries zero DOF. If C2 fires, it is a limits
reconciliation and must respect the rule-14 misalignment clause — a published
interface that our reduced network collapses into one link is exactly the
documented exception.

## §5 — scope discipline

- **Not bundled with pjm-133.** The hydro nameplate delta moves energy *into*
  a zero-MC class, which displaces thermal and would deepen this under-run; and
  the within-season gate is measured-inert here. Bundling either with this would
  buy a confounded run and no repair.
- **No mechanism is proposed in this document.** §4 is two measurements. A delta
  is chartered only after one of them fires, with its own prereg (the
  caiso-124/126/130 protocol) and its own PRIMARY.
- **Model assignment:** Opus or Fable — the lane writes `src/market_sim/` and/or
  `scripts/`, so rule 27 `[R-PUSH]` excludes Sonnet.

Next number: pjm-134.
