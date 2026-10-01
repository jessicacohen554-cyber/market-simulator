# PRE-REGISTRATION — pjm-136 `pjm_zonal_loss_surface` (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document
does not contain cannot be quoted as a pass. Format follows
`PREREG-pjm135-star-node-net-position-cut-2026-07-28.md`, **mirrored, not
copied**.

Chartered by `FINDING-pjm136-zonal-dual-structure-2026-07-28.md` (this session's
M1a/M1b/M2/M3 measurements, all no-LP), which was handed the question by
`FINDING-pjm135` §7: the Dominion CT/CC zonal inversion stays open, the
per-border star-node lever is closed by measurement, and *"a successor needs a
mechanism that changes the dual structure — real internal congestion — not
another flow cap."*

**Promotion is NOT pre-granted** and is not requested by this session. It remains
a separate owner act, and (rule 22 `[R-HOLDOUT]`) a structural mechanism change
is scored leave-one-year-out within 2023–2025 before any promotion.

---

## §0 — what the measurements found, and how it reshaped the charter

The charter asked which internal link would have to bind. **The answer is none —
and that refutes the whole flow-limit family rather than pointing inside it.**

| test | result | verdict |
|---|---|---|
| **M1a** what binds in the model | the keeper separates on `AEP_Ohio→Dominion`, `West_APS→Dominion` and `SWMAAC→Dominion` in **0.0 % of all 26,280 hours**; all eight zones sit at one dual in **96.4/97.6/97.0 %**, mean max zonal spread **$0.29/$0.63/$0.97** | **the Dominion boundaries carry NO congestion at all** |
| **M1b** what PJM does | PJM's own DA prices separate on **every** one of those links in **100.0 %** of hours, mean max zonal spread **$16.83/$18.06/$29.64** | **the gap is total** |
| **M2** the losses question | the loss component carries **20/24/23 %** of the mean DOM−AEP-DAYTON gap, exceeds $1 **on its own** in **24/33/54 %** of hours, and needs **no binding constraint**; per-zone deviations are **sign-stable 12/12 months** (Dominion +, SWMAAC +, ComEd −) | **YES — the delta** |
| **M3** topology adequacy | intra-zone hub spread inside ComEd/AEP_Ohio is **$0.25–$1.70** against an inter-zone DOM-vs-AEP **$3.02/$3.88/$6.57** | **the 8-zone reduction can carry it** |

**Why this delta and not another flow cap.** Tightening a constraint that is
slack in 100 % of hours cannot manufacture a persistent every-hour gradient; it
can only begin to bind somewhere. The loss component separates duals **without
any constraint binding**, which is the only mechanism class that can reach a
copper-plate.

## §1 — the delta, exactly

`ScenarioConfig.pjm_zonal_loss_surface` — **new, default off, ZERO fitted
scalars**, PJM-gated, byte-identical off. Each bidirectional PJM-**internal**
link splits into a one-way pair (`transmission.apply_pjm_zonal_loss_links`,
11 → 22 links) and each direction's receiving-end energy-balance coefficient
becomes `1 − eps(month)` (`dispatch.build_constraints(link_loss)`), with

```
eps_(x→y),m = max(0, (dev_y,m − dev_x,m) / (1 + dev_y,m))
```

`dev` is the frozen derive `scripts/data/derive_pjm_loss_surface.py` over PJM's
**own** published per-zone MLC record: `dev_z,m = Σ MLC_z / Σ MEC`, DA basis, all
21 transmission zones load-weighted onto the eight model zones through the
canonical `eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS` crosswalk. **Every model
zone is real; none is interpolated.** MEC identity checked uniform across zones
per UTC interval to **0.000000 $/MWh**. The only non-measured device is the
0.001 $/MWh loss-pair flow tiebreak (storage-ε class, rule 9 `[R-EPSILON]`).

**Scope boundaries, fixed here:**
- Rule 19 `[R-ONE-MECH]` — this owns the **loss** component only. Congestion
  stays with `pjm_measured_interface_limits` and the joint EAST / AP-South /
  net-position cuts, all unchanged.
- The **external star node is NOT lossy**. `PJM_external` is a fictitious pricing
  node with no published deviation; inventing one would be a fitted scalar
  (rule 5). Its five links are neither split nor charged. This is a real
  asymmetry and it is kill K3's subject, not a hidden assumption.
- Rule 25 `[R-ISO-SCOPE]` — PJM's surface, PJM's cell. `miso_zonal_loss_surface`
  is a REJECTED PROBE in MISO and that verdict is **not** transferred here in
  either direction.

## §2 — PRIMARY (P1): reproduce the measured loss component

**P1 — the deliverable, and the only thing this lane claims.** For each of the
11 internal links and each of 2023/2024/2025, the arm-B minus arm-A change in
the mean hourly dual difference must reproduce the **measured DA loss component**
`mean(MLC_a − MLC_b)` within **[0.5×, 1.5×]**.

Pre-computed from arm A's own committed duals and the derived surface
(`E[Δ] = mean(−λ_a·eps_fwd/(1−eps_fwd) + λ_b·eps_rev/(1−eps_rev))`), **before any
solve**, the expected ratios are **0.82–1.05× on all 33 link-years**. The three
chartered Dominion boundaries:

| link (a→b), $/MWh | 2023 expected / measured loss | 2024 | 2025 |
|---|---|---|---|
| AEP_Ohio→Dominion | **−0.553 / −0.541** | **−0.976 / −1.056** | **−1.625 / −1.896** |
| West_APS→Dominion | −0.713 / −0.719 | −0.606 / −0.656 | −0.869 / −1.045 |
| SWMAAC→Dominion | +0.249 / +0.245 | +0.430 / +0.486 | +0.575 / +0.704 |

**P2 — the copper-plate must break.** The share of hours in which all eight PJM
zones sit at one dual must fall materially below arm A's **96.4 / 97.6 / 97.0 %**
in every year. A delta that leaves the copper-plate intact has not fired.

**P3 — construction fidelity.** The realised `link_loss` matrix must equal the
derive's `eps` verbatim (no scale, no clip beyond the documented `max(0, ·)`
reverse clamp), and the off-state must be byte-identical (covered by
`tests/iso/pjm/test_pjm_zonal_loss_surface.py::TestOffStateByteIdentity`).

## §3 — pre-registered kills (structural failure modes, not residual movement)

**K1 — no fabricated separation** (the miso-76 R2 analogue). The arm-B model
separation must not exceed the **measured DA total** `mean(LMP_a − LMP_b)` in
magnitude on any of the three Dominion-facing links, and must carry the same
sign there. Pre-computed ratios vs total: **0.13 / 0.18 / 0.11** on
AEP_Ohio→Dominion — comfortable.

**K1-declared exceptions — named NOW, with numbers, so they can never be
constructed after the fact.** A loss-only mechanism over-states the *total*
separation wherever congestion offsets loss rather than reinforcing it. On the
committed measurements that is:

| link | year | expected model Δ | measured **total** Δ | measured **loss** Δ |
|---|---|---|---|---|
| **AEP_Ohio→ATSI** | 2024 | −0.282 | **+0.083** | −0.313 |
| **AEP_Ohio→ATSI** | 2025 | −0.563 | **−0.146** | −0.656 |
| AEP_Ohio→West_APS | 2023 | +0.163 | −0.392 | +0.178 |
| Central_PA→EMAAC | 2023/24/25 | −0.194 / −0.471 / −0.754 | +3.917 / +1.567 / +1.751 | −0.185 / −0.521 / −0.897 |
| SWMAAC→Dominion | 2025 | +0.575 | −3.009 | +0.704 |

`AEP_Ohio↔ATSI` is **PJM's exact analogue of the MISO East−Indiana pair-year that
tripped miso-76's R2**: its measured total is near zero *because* congestion
(+0.396/+0.510) and loss (−0.313/−0.656) cancel, so a loss-only mechanism
over-states it. **These specific link-years are pre-declared as a
representation bound — missing congestion, not fabricated loss** (the loss
component itself is reproduced at 0.86–0.95×) — and are reported, not killed.
**Any over-total link-year beyond this table is a K1 FAIL.**

**K2 — no load shedding.** Losses consume MWh: PJM must generate roughly
1–2 TWh/yr more to serve the same load. Slack and dump must be **exactly zero**
in both arms, all three years. This is the named principal risk: if PJM's fleet
cannot cover the loss make-up in the tightest hours, the mechanism has bought
separation with unserved energy and is retired.

**K3 — the seam must not absorb the delta.** Internally-wheeled energy now pays a
loss while seam-sourced energy does not, so external imports become *relatively*
cheaper. Arm B's net interchange must not move **further from the measured value
than arm A's by more than 1.0 TWh** in any year (arm A: −28.98/−21.91/−25.92 TWh
against a measured −39.98/−32.83/−32.93; the pjm-135 net-position cut and the
per-border p95 envelopes bound the channel, and Dominion's own external band is
already ridden in 76–93 % of hours, so the headroom is small — but it is not
zero and this gate is where it is checked).

**K4 — the C1 margin is thin and is watched explicitly.** The keeper passes C1 by
**1.4 % of band** (2023 CC_REGULAR −7.89 TWh against ±8.00). Any delta costing
CC_REGULAR more than **0.11 TWh** flips C1 back to FAIL. Pre-registered
disposition (rule 1 `[R-STRUCT]`): **a C1 flip does NOT retire the mechanism** —
a structurally-correct measured mechanism stays in even when the fit worsens, and
the response is to find the real root cause, never to revert. It **does** block
any promotion recommendation from this session, and it is reported in the
headline rather than buried.

**K5 — arm-A identity.** Arm A must reproduce the committed
`pjm135_netpos_keeper_C` class hourlies to **0.000000000 MW** on all classes,
every hour, all three years. A non-identical control invalidates the A/B.

**K6 — solve cost is recorded, not gated.** The split doubles the internal link
columns (11 → 22, +96,360 columns). pjm-134's per-link interface rows cost ~2.5×;
pjm-135's single aggregate row cost nothing. Whatever this costs is reported.

## §4 — the expected magnitude, pre-computed, and INERT pre-registered

**This delta is pre-registered as unable to close the CT leg of the Dominion
inversion.** Its entire reach on the `AEP_Ohio→Dominion` boundary is a dual lift
of **$0.55 / $0.98 / $1.63 /MWh** at arm A's own mean prices ($30.24/$29.30/
$39.52). Dominion `CT_PEAKER` is short **−6.7 / −7.4 / −7.2 TWh** and sits far up
the offer stack; a ~$1.6/MWh lift does not bring peakers in by 7 TWh. Dominion
`CC_REGULAR` (−1.6 % in 2025) is the plausible mover, and its whole remaining gap
is under 1 TWh.

**A result in which Dominion CT_PEAKER barely moves is the expected outcome and
is published as a PASS of the PRIMARY**, exactly as pjm-134's and pjm-135's INERT
verdicts were. If P1/P2 hold and the Dominion classes do not move, the
determination is **ENFORCED-BUT-INERT-ON-THE-CT-LEG**, and that is a finding
about where the remaining 76–80 % of the measured separation lives (congestion),
not a failure of the mechanism.

**No-feedback ceiling (binding on this session and any successor):** there is
nothing in this mechanism to re-parameterise, and nothing may be added. **No
multiplier, percentile, haircut, blend, scale factor, floor, cap or scarcity
exemption may be applied to the delivery-factor surface**, in this session or a
successor, whatever the result. The surface is a measured physical quantity; it
re-derives **only** when its source data updates (rule 23
`[R-FROZEN-DERIVE]`), never because a residual moved. A separation that comes
out too large or too small is a discovered fact about the measured network
property, not a setting. Extending the construction to a *different* component
(congestion) is a new charter with its own prereg.

## §5 — arms, protocol, and what is reported either way

| | arm A (control) | arm B (delta) |
|---|---|---|
| bundle | `results/calibration/pjm136_control_A` | `results/calibration/pjm136_lossurf_B` |
| recipe | `pjm135_netpos_keeper_C` verbatim (`replay_keeper.py`) | + `--set pjm_zonal_loss_surface=true` |
| years | 2023 + 2024 + 2025, one invocation (rule 16) | same |
| order | sequential, years sequential within each (rule 12) | |

`legitimacy_diagnostics.json` is generated for **both** arms before scoring.
Both arms are registered on the backcast dashboard (rule 15) and the
`zonal_loss_surface` matrix cell is updated in this session (rule 28 duty b),
**including if the verdict is REJECTED or INERT**. C3c is expected to FAIL in
both arms and D1/D2 to FAIL in both — pre-existing and long-standing, not this
delta.
