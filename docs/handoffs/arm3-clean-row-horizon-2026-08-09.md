# ARM3-MEASURE — the longer-horizon MISO measurement of the MN/MI clean-tier rows

**Owner decision D-28 option A, step 3 (sitting Addendum AF.3): evidence for the Arm-3
(`miso_clean_tier_rows`) arming card.** MEASUREMENT ONLY. **No arming decision, no keeper
contact, no backcast-registry touch.** The arming card is the MANAGER's to put and the
OWNER's to sign; this document is its evidence table.

**Head at lane start:** `origin/main` `e9f99e6`. Branch
`claude/arm3-clean-row-horizon-ifcfsb`, cut at that head with zero divergence.

Authority: `docs/handoffs/d28-45u-composition-memo-2026-08-08.md` §2.1 (the fleet the rows
pay); `docs/handoffs/f2-45u-composition-2026-08-09.md` (the landed §45U seam);
`docs/handoffs/ffr-7b2-rps-krow-clean-rows-2026-08-06.md` §3.2 (the established 2026–2030
quiet window); `config/capacity_market.py` `MISO_CLEAN_TIER_REGIONS` + `STATE_RPS_ACP["MISO"]`.

---

## 0. PRE-REGISTRATION (written and committed BEFORE any solve)

This section was committed in its own commit, before either leg was launched. Nothing below
it was edited afterwards except where a line is explicitly marked as a post-solve result.

### 0.1 The window, and why 2031–2035 is the right one

The 2026–2030 window is ALREADY ESTABLISHED as quiet (FFR-7B-2 §3.2: both clean rows slack,
dual 0 in every year, whole trajectory identical to the Arm-2 leg to the digit). It is cited
here, not re-solved. The open question is the RAMP YEARS.

Reproduced from `policy.clean_tiers._clean_tier_target` against the shipped
`MISO_CLEAN_TIER_REGIONS` (no solve; this reproduces the FFR-6B §6.2 adjudication table
exactly — MN .616/.693/.770 and MI 0/.456/.570 at 2030/35/40):

| year | MN statutory | MN obligation (× .77 West share) | MI statutory | MI obligation (× .57 East share) |
|---|---|---|---|---|
| 2030 | 0.8000 | 0.6160 | 0.0000 | **0.0000** |
| 2031 | 0.8200 | 0.6314 | 0.0000 | **0.0000** |
| 2032 | 0.8400 | 0.6468 | 0.0000 | **0.0000** |
| 2033 | 0.8600 | 0.6622 | 0.0000 | **0.0000** |
| 2034 | 0.8800 | 0.6776 | 0.0000 | **0.0000** |
| 2035 | 0.9000 | 0.6930 | 0.8000 | **0.4560** |

**Why this window and not another.** MI's tier has its first statutory knot at 2035 (2023
PA 235) and the zero-before-first-knot convention imposes NOTHING before it. MI's obligation
is therefore *exactly* zero in 2031–2034 and steps discontinuously to .456 of MISO-East load
in 2035. **2031–2035 is the earliest ≤5-solve-year window that contains MI's onset year at
all** — it captures the step exactly at the window's last year, while spanning MN's +6.2 pp
ramp (.6314 → .6930). A window starting later would spend the locked ≤5-year budget on years
past the onset rather than on the onset itself.

### 0.2 Seeding — a STATED LIMITATION, not a silent one

**The 2031 leg starts from a COLD fleet, and no available protocol avoids that.** Verified
against the code, not assumed:

* `runner.py::run_scenario_iso` builds the fleet once at `start_year` and evolves it only
  inside its own year loop (`for year in range(start_year, end_year + 1)`, :1453). The
  persistent `fleet` object lives entirely within one invocation.
* There is **no cross-invocation fleet-state handoff**. The evolution ledger
  (`results/evolution_ledger.py`) is a write-then-read *record*; nothing seeds a run from it.
  Announced retirements and confirmed exits ARE seeded through `start_year - 1`
  (`_seed_through`, :1358/:1387), and the EIA-860 planned-additions pipeline is applied, so
  the **exogenous** fleet is correctly aged to 2030. What a cold 2031 start omits is the five
  years of **endogenous** economic entry/retirement.
* The only way 2031 could inherit 2026–2030 evolution is a single invocation spanning
  2026–2035 = **10 solve-years**, which `config/schedulable.py::assert_schedulable` refuses
  (`end - start + 1 > 5`) without `--full-solve-authorized`. **No such owner authorization
  exists for this lane**, and this charter does not carry one.

**Consequence for the prompt's suggested fallback.** Running 2026–2030 armed as "invocation 1"
would NOT seed invocation 2 — invocation 2 rebuilds the fleet cold at 2031 regardless, because
the cache short-circuits the per-year LP solve, never the fleet build. That leg would cost
~62 min and seed nothing. **It is therefore deliberately not run**, and the reason is recorded
here rather than left as an unexplained omission.

**How the limitation is handled:** both legs are seeded IDENTICALLY (same cold 2031 fleet,
same posture, one flag apart), so the **arm-vs-control DELTA (R4) is exact and carries no
seeding caveat at all**. The **LEVEL** reads (R1 onset/ceiling, R3 supply-vs-target) carry the
caveat, and its DIRECTION is pre-stated: FFR-7B-2 §3.1 measured 2026–2030 endogenous growth of
VRE 39.0 → 49.0 GW. Omitting that clean build **understates qualifying supply**, which biases
the rows toward binding **MORE** and **EARLIER**. So a slack row in this measurement is a
*strong* result (slack despite a conservative supply seed); a binding row is a *weak* one
(it may be the seed, not the statute). Pre-stated so it cannot be chosen after the fact.

### 0.3 The two legs

Identical postures, ONE delta. `--golden-posture` matches FFR-7B-2 and resolves MISO
curve-ON, which is the shipped posture (`shipped_capacity_clearing_by_iso()` →
`{PJM, MISO, CAISO, NEISO}: True`; owner C.4(a) B1 made golden and shipped one answer).

| leg | command delta | `miso_rps_compliance_regions` | `miso_clean_tier_rows` |
|---|---|---|---|
| CONTROL | *(none)* | **True** — via MISO's `ISOConfig.default_scenario_overrides` (owner D-26) | False |
| ARM | `--miso-clean-tier-rows` | **True** — same route | **True** |

**Arm 2 is already the MISO forecast default**, so the control IS "the standing MISO forecast
posture" without any flag. Verified mechanically: `runner.py:1015-1023` applies an ISO override
only where the caller left the field at its `ScenarioConfig` default, and `reference_config`
passes `miso_rps_compliance_regions=False`, which *equals* the default — so the override fires
and the field resolves True in BOTH legs. The cache key is computed after the overrides are
applied (:1026), so both keys record the armed Arm-2 grain. `entry_vre_capacity_revenue=True`
rides the same override in both legs.

Run **serially**: 15 GB box, FFR-7B-2 measured peak RSS ≈ 9.6 GB/leg, so two concurrent legs
would OOM (rule 12's memory cap). ARMED leg runs FIRST — per the charter, if time runs short
it is the one that must land.

### 0.4 PRE-REGISTERED READS (R1–R5) and pre-stated expectations

No read is a target. Each expectation below is stated so that a miss is visible as a miss.

* **R1 — the MN and MI row duals by year: onset (first nonzero), level, and whether the $30
  ACP ceiling binds.**
  *Expectation:* **MI dual is EXACTLY 0 in 2031–2034 by construction** (zero obligation ⇒
  RHS 0 ⇒ any non-negative qualifying generation satisfies the row). This is an arithmetic
  certainty, not a prediction — if it is violated, the mechanism is defective and that is the
  finding. **At 2035 MI is expected to BIND, most likely pinned at the $30 ACP ceiling**:
  FFR-6B §2.2 measured MISO-East short 21.7 pp by 2035 against an East-ONLY eligibility mask
  (`("MISO-East",)`), and MI's *renewable* row already pins at $30 in every year of 2026–2030.
  **MN is expected to stay SLACK (dual 0) through 2035** — its +6.2 pp ramp is covered under
  the 5-zone Midwest-footprint eligibility mask for the same reason FFR-7B-2 §3.2 found it
  covered at 2030.
* **R2 — the composed nuclear revenue at the LANDED F-2 seam for the §2.1 fleet.**
  Which reactors earn which row, with the cross-state mask flagged. *Expectation:* **if MI's
  dual sits at the $30 ceiling, the arming question is COMPOSITION-INDEPENDENT** — D-28 §2.3
  and F-2 §0(3) both measure all defensible compositions coinciding **to the cent** at
  D = $30. The F-2 seam only goes live at an **interior** dual.
* **R3 — qualifying supply vs target by region-year**: WHY the row binds when it does (new
  clean build, retirement of qualifying supply, load growth).
* **R4 — arm-vs-control deltas** in the retirement/entry ledgers and system cost: what arming
  CHANGES. *Expectation:* per E-1's charter the rows' only output is a PRICE, so energy,
  builds and retirements should be identical or near-identical; FFR-7B-2 §3.1 found the Arm-2
  pair identical to the digit in a window where entry was backstop-bound rather than
  margin-decided.
* **R5 — E-1 discipline check:** the rows acquire **no build limb** (FFR-7B-2 §1 step 9 /
  FFR-6B §5.3). Checked structurally in the code AND behaviourally in the R4 ledgers.

### 0.5 Scope guards carried

* `miso_clean_tier_rows` stays **DEFAULT-OFF** in the shipped config; the armed run IS the
  measurement. **No `ScenarioConfig` field added.** No RPS/ACP config value changed.
* The composition seam is **LANDED — consumed, not modified.**
* Everything registers to the **FORECAST namespace** (`register_forecast_run.py`); the
  backcast registry is never touched (rule 15's forecast clause).
* Matrix duty (rule 28(b)): the `miso_clean_tier_rows` cell citation gains this measurement in
  THIS session. **No cell verdict is moved** — the measurement informs an arming decision that
  is not mine to take, so the cell stays `O` for MISO.
* Rule 22: every solve is forecast-mode 2026+, explicitly permitted by the 2026+ clause; no
  measured actual is read or scored.

---

*(Sections 1–6 — the R1–R5 results, the onset/ceiling table and the card-ready summary block —
follow the solves.)*
