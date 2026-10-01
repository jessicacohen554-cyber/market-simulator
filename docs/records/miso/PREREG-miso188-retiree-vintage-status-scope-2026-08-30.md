# PREREG miso-188 — RETIREE-CHANNEL VINTAGE-STATUS SCOPE: the dark within-window retiree phantom, dropped on EIA-860's own contemporaneous status

**Session miso-188 (2026-08-30).** Registered **BEFORE any adjudicating
quantity is computed** (the phase-0 characterization quantities restated
below were computed first and are disclosed in §0; no A/B leg exists and no
gate quantity has been computed). Target: the **C1 fuelmix CC_REGULAR 2024
band exceedance (+8.037 vs ±8.00 TWh)** on the keeper
`2026-08-26-miso-187-nucavail` (bundle `miso187_nuc_B`), determination
NOT-YET on {C3a-2025 −12.3185 %, C1 CC_REGULAR-2024}, C3c the single
ledgered caveat. **Charter:** the miso-188 handoff prompt, ask B — *"a
measured-input or identification repair in the miso-172/186/187 pattern
(zero fitted scalars) is the lane's proven currency; any lever = its own
PREREG, pushed + blob-verified BEFORE the solve, with a same-recipe
zero-delta control and pre-registered kill gates."* This supersedes, for
this object only, PREREG-miso187 §6's "owner charter needed" report-only
posture on the C1 band exceedance — the handoff IS that charter.

**Mechanism-in-kind boundary (named now so rule 28 is decidable):** a NEW
gated `ScenarioConfig` field, **`retiree_vintage_status_scope`** (default
off, byte-inert while off), scoping the within-window retiree injection
channel (`data/fleet/eia860.py::load_retired_within_window`) by the
**year-matched EIA-860 vintage status oracle** — the SAME instrument class
as the two status-basis mechanisms already armed in this keeper's recipe:
`carry_operating_mothballs` (the Cottonwood OA re-carry — vintage OP status
ADDS capacity the snapshot's OP filter wrongly drops) and
`unit_outage_fleet_status_scope` (miso-186 — snapshot non-OP status drops
event rows the fleet does not model). This is the symmetric third leg:
**vintage non-OP status drops retiree-channel units the paper retirement
date wrongly carries.** Rule 28(c) duties fire: one new matrix row + a cell
line in every ISO shard, in the same push as the field. Rule 19
`[R-ONE-MECH]`: fleet-membership-by-contemporaneous-status is ONE mechanism
family; this extends its coverage to the retiree channel rather than
stacking a new phenomenon owner.

## 0. What has been looked at, and what has not (the pre-registration boundary)

Phase-0 (this session, zero-solve, committed keeper artifacts + measured
in-repo sources only) computed, before this document:

* **Ask A validation:** `calibration_verdict.py --run-id
  2026-08-26-miso-187-nucavail` reproduces the registered determination
  exactly (NOT-YET on {C3a-2025 −12.3 %, C1 CC_REGULAR-2024 +8.04}).
* **The C1 characterization** (keeper `class_hourly` sidecars vs
  `bench/MISO/*.json.gz`): CC_REGULAR error (model − classFull) **+1.71
  (2023) / +8.997 raw, +8.037 scored (2024) / −1.50 (2025, unscoreable
  vintage)**; the 2024 excess concentrates **Feb–Jun (+4.6 TWh vs CAMPD)
  and Oct–Nov (+1.0)** with Jul–Sep near-exact; the gas FAMILY total error
  is ≈0.0 (2023) / +5.6 (2024) / −0.1 (2025).
* **Availability audit** (the keeper's own fleet/availability construction
  rebuilt through the `run_calibration.py` path — retirees + mothballs
  injected, `weather_year` pinned per year): the CC availability input
  tracks the real fleet closely (actual/available = 92–93 % in Jul–Aug
  2024); the Union Power (55380) Feb-2024 whole-plant outage applies at the
  LP grain exactly (monthly availability factor 0.062); model CC dispatch
  runs at 87–94 % of available energy in 2024 (availability-saturated) vs
  74–90 % in 2023. The 2024 excess is therefore membership/availability
  -sensitive in a way 2023's is not.
* **The phantom identification** (the adjudicating evidence, restated in
  §1): per-plant CAMPD records for every MISO retiree-channel unit ≥40 MW,
  the EIA-860 vintage_2021–2024 status of each, and the in-merit
  availability energy of each under the keeper's own mc/price construction.
* **Environment facts:** 15 GB RAM / 4 cores / 8 GB swapfile enabled
  (miso-169 recipe); full clone, `data/raw` complete.

**No A/B leg has been solved; no gate quantity of §4 has been computed.**

## 1. The identification (measured, zero fitted scalars)

The within-window retiree channel (`load_retired_within_window`, backcast
mirror of planned additions) injects whole-plant exits absent from the
single recent operable snapshot and lets the COD ramp dispatch each
**through its formal EIA-860 retirement month**. But several MISO
retiree-channel plants were **deactivated years before their paper
retirement date**, and EIA's own contemporaneous record says so — the
year-matched vintage snapshots (`data/raw/eia-860/vintage_<year>/`, the
identical oracle `carry_operating_mothballs` already reads) mark them
non-OP, and their CAMPD record is an unbroken string of exact zeros:

| plant | units | MW | formal ret | latest vintage ≤2023/≤2024 status | CAMPD GWh 2022/2023/2024 |
|---|---|---|---|---|---|
| **862 Grand Tower** (CC_REGULAR, MISO-Illinois) | 1–4 | 511 | 2024-04 | **OS / OS** | **0.0 / 0.0 / 0.0** |
| 202 Carl Bailey (ST_GAS, MISO-South) | 1 | 122 | 2024-10 | OS / OS | 0.0 / 0.0 / 0.0 |
| 2050 Baxter Wilson (ST_GAS, MISO-South) | 1 | 494 | 2023-03 | SB / — | 0.0 / 0.0 / — |
| 10075 Taconite Harbor (MISO-West) | 1–2 | 155 | 2023-03 | SB / — | 0.0 / 0.0 / — |
| 52006 LaO GEN1 (MISO-South) | GEN1 | 57 | 2024-04 | OS / OS | not CEMS-covered |
| — control case: 6155 Rush Island (COAL_PRB) | 1–2 | 1,178 | 2024-10 | **OP / OP** | 892 / **892 / 612 (ran)** |
| — accepted miss: 1047 Lansing (COAL, MISO-Plains) | 4 | 241 | 2023-06 | OP / — | 0.0 / 0.0 / — |

The model dispatches these phantoms. Measured under the keeper's own
construction (availability × in-merit vs the keeper's committed P1 prices):

* **Grand Tower 2024: 1.304 TWh available Jan–Apr, 1.229 TWh in-merit** —
  a 511 MW CC at 2024 gas prices, dark in reality for three straight
  years, carried by the channel into exactly the CC-excess window.
* Grand Tower 2023: 3.548 TWh in-merit (full year).
* Baxter Wilson 2023: 0.195 TWh in-merit (Jan–Mar); Taconite Harbor 2023:
  0.210; Carl Bailey: 0.298 (2023) / 0.135 (2024).
* **2025: provably zero effect** — every affected unit's formal exit
  precedes 2025, so the COD ramp already zeroes all of them in 2025. This
  lever makes **no claim on C3a-2025** (ask C's object stays where
  miso-187 left it: the adjudicated mc-idled/flat-stack model-class
  residual, owner D-4 posture court).

**The oracle (fixed now):** for backcast solve year Y, a retiree-channel
unit `(plant_id, generator_id)` is **dropped** iff its status in the
**latest committed vintage V ≤ Y whose operable sheet lists it** is
non-`OP` (OA/OS/SB); a unit listed nowhere fails **OPEN** (kept) — the
same fail-open discipline as `unit_outage_fleet_status_scope`. Rush Island
(OP, ran) is kept by the oracle; Lansing (OP-but-dark) is kept too — the
**accepted miss**, disclosed here and NOT patched: patching it would need
same-year CEMS darkness as a *membership* input, which this prereg
deliberately refuses (the layup precedent treats economic darkness as
must-run-mask evidence, never as membership/availability; rule 13's
outcome-pinning line).

**Admissibility (rules 13/14):** the EIA-860 vintage status sheet is a
published, contemporaneous, forward-regenerable fleet-status record — the
identical admissibility basis on which `carry_operating_mothballs`
(charter §4, the rule-13 hinge: "EIA's own contemporaneous status") and
`unit_outage_fleet_status_scope` (miso-186) were adjudicated and armed in
this very keeper. Zero fitted scalars; the identification is
year-independent (no parameter identified against any year's outcome), so
the standing LOYO note is satisfied structurally (rules 20/22). Rule 14:
the measured status record is preferred over the formal retirement date
the channel currently trusts.

**A-priori scored-face expectation, declared now:** removing ~1.23 TWh of
in-merit phantom CC availability from the saturated Jan–Apr 2024 window
predicts **C1 CC_REGULAR-2024 falls by between 0.3 and 1.23 TWh** (the
spread is other-CC/coal substitution, honestly unknown ex ante), i.e.
+8.04 → +6.8..+7.7 — a predicted PASS, not a guaranteed one. C3a-2024
(−4.64 %) should move toward zero (supply removal raises prices);
**C3a-2023 (+2.40 %) may rise** (the same sign logic on 3.5 TWh of 2023
phantom — the adverse face, reported at full magnitude); ST_GAS-2023
(+4.04 TWh) should fall slightly (Baxter/Taconite/Bailey); COAL_PRB is
near-untouched (Lansing kept; Rush Island kept). Movements are reported
whatever they are, never traded.

## 2. The work (mechanism first, then the A/B — both legs at ONE HEAD)

1. **The field** — `ScenarioConfig.retiree_vintage_status_scope: bool =
   False`, registered with the nyiso-119/caiso-186 discipline **in the same
   commit**: `_CACHE_KEY_OPTIONAL_FIELDS` entry, default-ledger `"False"`
   entry, measured-record entry ("EIA-860 vintage generator status"), and
   the dataclass docstring comment. No new CLI flag (the `replay_keeper
   --set` channel carries it, exactly as miso-186/187's fields).
2. **The scope** — `load_retired_within_window(..., year=...,
   vintage_status_scope=False)`: when on and `year` is given, drop injected
   units per the §1 oracle; INFO-log the dropped units + MW per year.
   Threaded from `scripts/run_calibration.py` (the driver both legs run
   through) and `runner.py`'s backcast branch, gated on the field.
3. **Unit test** — the oracle's keep/drop/fail-open behavior.
4. **Matrix duties (rule 28c)** — new row in
   `docs/codebase-site/data/mechanism-matrix.js` + a cell line in EVERY ISO
   shard (`U` for MISO pending the A/B; `·`/`U` for sisters per their
   channels); `scripts/check_mechanism_matrix.py` green before push.
5. **The A/B (§4)** — control + arm `replay_keeper` replays of
   `miso187_nuc_B`, both AFTER the mechanism push, at one HEAD.

## 3. Anti-sweep (binding)

The oracle form is frozen by this document: latest committed vintage ≤
solve year, per `(plant_id, generator_id)`, non-OP = {anything ≠ "OP"},
fail-open on unlisted. **No CEMS quantity enters membership**; no unit is
added to or removed from the oracle's verdict because of what a leg later
shows; the Lansing miss stands. No deriver is re-tuned; no threshold
exists to sweep. The witnesses, gates and thresholds below are frozen; no
alternative statistic may be quoted after seeing a result. A result
against interest is reported at full magnitude. A missing/deficient input
STOPs with the deficiency disclosed.

## 4. The A/B (PREREG-miso184 §6 gates verbatim where they apply, re-keyed to this lever's structure)

Control and arm are `replay_keeper` replays of `miso187_nuc_B` at one HEAD,
run SEQUENTIALLY (rule 12; miso-169 memory recipe: 8 GB swapfile,
`MARKET_SIM_HIGHS_THREADS=4`), each the FULL span 2023 2024 2025 in ONE
invocation (rule 16):

```
python3 scripts/replay_keeper.py results/calibration/miso187_nuc_B \
  --out-dir results/calibration/miso188_rvs_A \
  --note "miso-188 CONTROL: byte-faithful keeper replay at HEAD (retiree_vintage_status_scope default off)"
python3 scripts/replay_keeper.py results/calibration/miso187_nuc_B \
  --out-dir results/calibration/miso188_rvs_B \
  --set retiree_vintage_status_scope=true \
  --note "miso-188 ARM: retiree-channel vintage-status scope (single delta; PREREG-miso188)"
```

Registration ids `2026-08-30-miso-188-control` /
`2026-08-30-miso-188-rvsscope` (a bundle-timestamp date shift is a naming
deviation, disclosed, per the miso-187 precedent) — **BOTH registered
whatever the outcome** (rule 15, full span, rule 16).

* **S-0 CONTROL INERTNESS (ABANDON).** Every scored sidecar of the control
  (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years)
  value-identical to the committed keeper's (`miso187_nuc_B`). Anything
  else ⇒ HEAD drift — STOP, report, no arm conclusion (the miso-177 R-0
  discipline).
* **S-1 EXACTNESS (KILL).** The arm's `run_config.json` records exactly the
  single delta `retiree_vintage_status_scope=true` (control false/absent);
  every other input byte-identical between legs. The flag demonstrably
  acted, witnessed from the legs' own `dispatch/<year>_P1.parquet` (frozen
  now): **(a)** Grand Tower (862) total dispatch is **> 0 in the control**
  in 2023 and in 2024 and **exactly 0 in the arm** in both; **(b)** Carl
  Bailey (202), Baxter Wilson (2050) and Taconite Harbor (10075) each have
  arm dispatch exactly 0 in every year; **(c)** Rush Island (6155) has
  **nonzero dispatch in BOTH legs in 2023 and 2024** — the oracle's
  keep-side witness (its magnitudes are reported, never gated); **(d)**
  Lansing (1047) dispatch is nonzero in BOTH legs in 2023 (the accepted
  miss, unchanged by construction).
* **S-2 STRUCTURE (the charter's structural gate).** The arm's 2024
  CC_REGULAR class energy (P1 `class_hourly`) falls below the control's by
  **≥ 0.10 TWh** — the floor of the §1 predicted range, an order of
  magnitude under the phantom's 1.23 TWh in-merit availability.
* **THE CHARTER KILL.** An arm whose scored C1 CC_REGULAR-2024 improves
  while the S-1 witnesses show the flag did not act as specified (any S-1
  clause failing) is an unidentified level lever wearing a repair's name →
  REJECTED regardless of every other number (rule 1's enforcement).
* **S-4 CONDUCT (KILL).** Zero NEW D-4 conduct failures on the arm's
  regenerated `legitimacy_diagnostics.json` vs the control's; C8 PASS all
  years.
* **S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill).** The
  complete verdict scorer on both legs; C3a all years, C1/C2/C3b/C3c/C4,
  every movement reported at full magnitude. Any **gated criterion
  PASS→FAIL flip in any year**, or a C3a movement out of the commercial
  band in 2023/2024, fires the **owner-escalation path** — never an
  auto-reject and never an auto-keeper.

**Promotion rule (fixed now).** The arm is promoted keeper **iff S-0 is
clean, S-1 and S-4 are clean, S-2 passes, the charter kill is silent, and
S-5 records ZERO gated-criterion PASS→FAIL flips** — the C1 CC_REGULAR-2024
flip to PASS is predicted but NOT required for promotion (rules 1/14: the
membership correction is structurally right whatever the residual does; the
standing owner posture directive, twice in writing at miso-184/186 and
exercised at miso-186/187, covers a scored-face regression short of a
criterion flip). S-1 clean but S-2 failing (the mechanism acted, the class
total did not move) ⇒ MIXED: registered, cell `I`, keeper unchanged, owner
escalation with both faces. Any S-5 criterion flip ⇒ registered, keeper
unchanged, owner escalation (the miso-187 §4 structural-split precedent —
never self-adjudicated). S-1 or S-4 firing ⇒ NOT promoted, cell `R`.
Registration + matrix stamp + calibration-log entry in-session regardless
of outcome; a promotion re-stamps `keepers/MISO.json`, rebuilds
`status/MISO.js`, and fires the calibration-keeper-auditor. MISO holds no
`complete`/`final` marker, so no rule-22 D-5(b) re-key is owed. DOF ledger
on promotion: one new entry, identification MEASURED (EIA-860 vintage
status), `n_scalars` 0, `n_residual` unchanged at 2.

## 5. Instrument

`scripts/probes/_miso188_ab_gates.py` →
`results/calibration/_miso188_ab_gates.json` — the miso-187 scorer
re-keyed (KEEPER `miso187_nuc_B` / CONTROL `miso188_rvs_A` / ARM
`miso188_rvs_B`; the S-1 witnesses and S-2 threshold above), committed
**after this PREREG and before it is run** (the miso-184 order). If
promoted, the attestation generator is re-keyed from miso-187's with the
new MEASURED ledger entry; the control stays unattested.

## 6. DO-NOT-REDO and governance

**DO-NOT-REDO (miso-185 §9 + miso-186/187 carried in full):** the offer
family at BOTH grains (miso-179 `R` / miso-180 `I`); `miso_south_firm_
export_block` `G`; `miso_south_export_ladder_rt_tail` `R`;
`miso_seam_coincident_envelope` `R`; `measured_interface_limits` `R`;
`m2m_seam_entitlement_cap` `G`; `import_shape_lever` `G`;
`internal_congestion_split` `G`; `zonal_loss_surface` `R`;
`measured_offer_surface` `R`; `gas_hub_basis_overlay` `R`;
`ramp_envelopes` `I`; `dam_availability_rebasis` `R`; the ordc/reserve and
dispersion families; reserve-requirement raises. The 2025 scarce N→S RDT
residual (S-2 7/47) is the adjudicated mc-idled/flat-stack MODEL-CLASS
object — NOT re-opened here (this lever provably has zero 2025 effect).
`unit_outage_fleet_status_scope` and `nuclear_unit_availability` are the
keeper (`K`) — not re-tested; both ride unchanged in both legs.
`mustrun_online_frac_per_year` `R` — untouched (this lever changes no
floor and no online_frac). `carry_operating_mothballs` — armed in the
keeper, untouched; its OA-only ADD-side scope is not modified (this lever
is the DROP side of the retiree channel, a different injection path).

**Governance.** Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; freeze ACTIVE;
MISO holds NO marker (fail-closed); no new data fetch of any kind (all
sources committed). Rule 12: years sequential within each leg; legs
sequential. Rules 13/14/19/23/24: per §1; the field is registered, recorded
in `run_config.json`, no off-registry channel. Rule 28: §5.4 queue stamp +
calibration-log entry + MISO shard cell (new row) adjudicated in-session,
negative outcomes included; `check_mechanism_matrix.py` before every matrix
push. Rule 27 `[R-PUSH]`: exact on-disk bytes; every pushed blob ≥300 lines
verified; on HTTP 408/500 set `git config http.version HTTP/1.1` and retry
before concluding anything. No new `.github/workflows`. THE OWNER MERGES;
no PR unless asked.
