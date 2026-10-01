# FINDING — capx D75-R: the PJM VRE ELCC delivery-year vintage axis, BUILT and MEASURED

**Lane:** capx D75-R, executing `FINDING-capx-d75-2026-09-06.md` §8 — itself executing
`FINDING-capx-d66-2026-09-06.md` §8 card B — under the director's rulings **R1 / R2 / R3** of
2026-09-06. Branch `claude/capx-d75r-pjm-vre-elcc-kxto0z`. **DATA PROFILE: pjm.** MODEL: Opus.
Ex-ante record: `PRECOMMIT-capx-d75r-pjm-vre-elcc-vintage-2026-09-06.md` (pushed before the first
solve; Addendum A records the rebase and re-declares the keys). Instruments:
`docs/handoffs/d75r/{vre-elcc-vintage-phase0,screen-gates,full-gates}.json`.

**GATED DEFAULT-OFF. NOTHING ARMED. NOT A KEEPER, and none is proposed** — arming is an owner card
on the measurement below (§8).

---

## 0. The answer in one paragraph

Card B's repair is **built, measured, and it works exactly as its own arithmetic said it would.**
Accrediting PJM's wind and solar at each delivery year's OWN published ELCC class ratings moves
accredited VRE **DOWN in all three in-scope delivery years** — solved **−754.631 / −332.854 /
−148.314 MW** for DY 2023/24 / 2024/25 / 2025/26 against phase 0's predicted **−754.633 / −332.854
/ −148.315** — i.e. the mechanism lands on its pre-solve prediction to **~0.001 MW in every year**.
Every one of the **26 scored bands is byte-identical** between arms: nothing flips, in either
direction. **FC-3 improves materially and inside its still-failing bands**: modelled retirements
**18.058 → 17.294 GW** against 15.062 actual (error **0.199 → 0.148**, a quarter of the error
removed), false-retire **8.065 → 7.596 GW**, window release precision **0.421 → 0.439**, and the
2023 all-channel precision **0.689 → 0.965**. The position residual is **two-sided**, as a real
basis repair should be, and Σ|gap| falls on both of D66 §1.2's frames (**B 2.587 → 2.074 pt**,
**A 1.579 → 1.067**). Two pre-declared expectations **missed** and are reported at full magnitude
rather than smoothed (§4.3, §5): DY 2025/26's residual **narrows** where the PRECOMMIT predicted it
would widen, and the 2024/25 and 2025/26 census move **UP** despite less VRE credit — both through
the fleet-propagation channel the PRECOMMIT named but could not sign. Two procedural errors of my
own are recorded in §7 rather than glossed.

---

## 1. What was built (and the one thing that needed a second key)

| piece | where |
|---|---|
| registry | `RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"]`, keyed by delivery-year label |
| gate | `ScenarioConfig.pjm_vre_accreditation_vintage`, **default-OFF** |
| predicate | `retirements.vre_accreditation_vintage_armed` |
| resolver | `resolve_renewable_vintage_credit`, **rung 0** of `resolve_renewable_capacity_credit` |
| harness | `run_capacity_hindcast.py --pjm-vre-accreditation-vintage` |

**The predicate requires THREE conditions**: the new field, **`pjm_accreditation_design_vintage`
(D48's own gate)**, and a registry entry for the ISO. So this is a **sub-gate inside the D48
family**, never a mechanism beside it: the VRE half can never be vintaged while the thermal half is
not (rule 19 `[R-ONE-MECH]` — a mixed accreditation basis is the exact failure D45 §2.2 measured
and D48 exists to remove).

**Why a second key was unavoidable**, since the charter asks it be said: D48's key is **ARMED for
PJM by owner ruling**, through `iso_configs.py::_pjm_config`'s `default_scenario_overrides`
(2026-09-05, on the D57 A/B). Keying this axis off it alone would have armed an untested mechanism
**by default** in every PJM forecast run the moment it landed, and moved the shipped `pjm-t1h`
recipe key. The composition above meets rule 19's substance without that.

**Zero scalar fields; zero free parameters beyond the ONE reconciliation ruling R1 authorised.**
Every rating is a published PJM class rating reconciled **byte-for-byte** to
`data/raw/capacity-market/elcc/pjm/pjm.csv`; the model's single `solar` class is blended from PJM's
two published classes at PJM's **own** Table-5 installed-MW mix, written as the arithmetic
`1189/(1189+8713)` = 12.01 % fixed and re-derived from the same committed rows by test — a declared
**cross-vintage reconciliation** under rule 14 `[R-ACCURATE]`'s misalignment exception, since PJM
publishes no pre-reform fixed/tracking pairing in any of seven primary documents (D75 §2). A split
sized to the position residual, or backed out of PJM's cleared solar UCAP, is **forbidden by name**
(rule 13) and neither exists in the code.

**The conclusion is mix-INSENSITIVE**, which is why one declared mix decides the card: DY 2024/25's
break-even blend is 0.5527, **above** PJM's own tracking rating of 0.50, so the implied fixed share
is **negative (−0.310)** — outside the admissible range entirely. No mix can flip the sign.

**Scope (rule 25 `[R-ISO-SCOPE]`)**: PJM-only by construction, locked by test across MISO / NYISO /
NEISO / CAISO / ERCOT. No ISO inherits PJM's verdict.

## 2. STEP 1 — the intake (merged as `c6d1441e`)

`FINDING-capx-d75` §6 item 1. Three tranches added verbatim from primary PJM postings, each with
source doc + page + **sha256** per row, all four documents fetched in-session and hash-matched to
the identities D75 recorded; the Dec-2021 2024/25 tranche **relabelled** PRELIMINARY/SUPERSEDED
rather than replaced (it is a real published artifact — final for that BRA *as then scheduled*).

| DY | ratings W / fixed / tracking | source |
|---|---|---|
| 2023/24 | 15 / 38 / 54 % | `elcc-class-ratings-for-2023-2024-bra.pdf` p.1, posted 2021-12-16 (`c50890fb…`) |
| 2024/25 **FINAL** | 21 / 33 / 50 % | Dec-2023 study Table 2, report p.4 / PDF p.7 (`192ea596…`); restated standalone (`f3fb54db…`) |
| 2025/26 3IA | 38 / 10 / 14 % | `2025-26-3ia-elcc-class-ratings.pdf` p.1, posted 2025-03-12 (`1d9d7e00…`) |

The Dec-2023 report states in terms that *"only the 2024/2025 values are final"*. **Before this
intake the repository's only 2024/25 rating set was the superseded one**, which is why it had to
precede the build.

## 3. PHASE 0 (zero LP) — PASS on the ruled per-year SIGN gate (R3)

The instrument calls the **shipped code path** under control and armed configs differing in one
field, on the D57 arm-A committed pools. **No `fleet_only` rebuild was needed and the reason is
measured, not assumed**: every arm-A ledger's `fleet_by_fuel_after` carries **no wind or solar key
in any year**, so PJM's persistent fleet holds no VRE units and accredited VRE = pool × credit
exactly.

| DY | credit W / S: incumbent → vintaged | Δ accredited VRE | gate |
|---|---|---:|---|
| 2022/23 | 0.41 / 0.1064 → *unchanged* | **0.000** | out of scope (pre-ELCC), **inert** |
| **2023/24** | → **0.15 / 0.520788** | **−754.633** | **DOWN ✓** |
| **2024/25** | → **0.21 / 0.479587** | **−332.854** | **DOWN ✓** |
| **2025/26** | → **0.38 / 0.135197** | **−148.315** | **DOWN ✓** |

The built code reproduces D75's independent hand arithmetic to **0.046 MW** (the rounding of its
published one-decimal figures) — two lanes, two constructions, one number.

**It is NOT a uniform derate**, and that matters for reading everything below: the two classes move
in **opposite** directions (2023/24 wind **−2,640.0 MW**, solar **+1,885.4 MW**), because PJM's
pre-reform class-average solar ratings sit far **above** the post-reform marginal ones the incumbent
curve carries. A mechanism that moved both classes the same way would be a derate wearing a
vintage's clothes.

## 4. STEP 4 — the SCREEN (rule 29), DY 2023/24: **PASS on all four legs**

Screen year named in the PRECOMMIT **before the screen ran**, as the year the mechanism's own
measured footprint is largest — never the largest residual. Arm `c45c007bed278d2e` against a
**same-HEAD** control `6eff06b0ec80f182`, both at `5375be8b`.

### 4.1 The four pre-declared legs

1. **IDENTITY ✓** — the solve's arm credits are **0.15 / 0.520788**, the registry's published values
   to the digit; accredited-VRE delta **−754.631 solved** vs **−754.633 predicted**. Control sits on
   the incumbent 0.41 / 0.1064.
2. **CONFINEMENT ✓** — requirement (163,166.2 MW), thermal accreditation by fuel, and storage firm
   MW **byte-identical**. The D48 thermal half is armed in both arms and does not move.
3. **NO NON-TARGET LOAD-BEARING FLIP ✓** — floor retentions, entry decisions, thermal / renewable /
   storage additions and the RPS dual identical in all three years. **D57 §3.5's identity holds in
   both arms** (0 cleared units in either decision set: the screen's failing set IS the auction's
   uncleared set).
4. **INERTNESS ✓** — 2021 and 2022 byte-identical, confirming ruling R2's scope limit on a real
   solve rather than by construction alone.

### 4.2 The substantive screen result — a channel the fixed-pool arithmetic could not show

Uncleared units **39 → 21**; retirement cohort **2,624.467 → 1,860.613 MW**; and the clearing
**price (86.517664 $/MW-day) and cleared MW (170,432.642) are IDENTICAL**. Less price-taking VRE in
`Q_0` means **more thermal must clear at the same curve intersection** — capacity revenue up,
retirements harder. That is the pre-declared rule-14 sign, arriving through the supply stack rather
than through the price.

### 4.3 Position — direction as pre-declared, magnitudes not

1.06233 → 1.05770; the residual **narrows** on both frames (B −1.061 → −0.598 pt, A −0.712 →
−0.250). The **direction** is the pre-declared one for the single in-scope year where the model sits
*above* the published position. The **magnitudes** differ from PRECOMMIT §7's fixed-pool table
(which had −3.642 → −3.174) because the base drifted between the PRECOMMIT and the solve — D67-ARM
changed the requirement operand. The per-year position delta is **−0.46 pt against −0.47
predicted**.

## 5. STEP 5 — the FULL WINDOW (2021–2025), and the two misses

Control `a9c66d8ea25acb9d` / arm `b518f5fe7d02f961`, one bundle each, differenced.

### 5.1 IDENTITY holds in every in-scope year, to ~0.001 MW

| DY | Δ accredited VRE, **solved** | phase 0 | |
|---|---:|---:|---|
| 2023/24 | −754.631 | −754.633 | ✓ |
| 2024/25 | −332.854 | −332.854 | ✓ |
| 2025/26 | −148.314 | −148.315 | ✓ |

### 5.2 Every scored band is IDENTICAL; FC-3 improves inside its failing bands

**All 26 bands byte-identical between arms — nothing flips, in either direction.** The metrics that
move, all in the right direction:

| metric | control | arm |
|---|---:|---:|
| `retirements.total_gw.model` (actual 15.062) | 18.058 | **17.294** |
| `retirements.total_gw.err_frac` | 0.199 | **0.148** |
| `false_retire.false_gw` | 8.065 | **7.596** |
| `plant_release_precision.window.all` | 0.421 | **0.439** |
| `plant_release_precision` 2023, all channels | 0.689 | **0.965** |
| `plant_release_precision.window.economic` | 0.122 | **0.129** |
| CO2 (all three years) | — | ±0.01 %, unmoved |

`unit_recall_gt300` is unchanged at 0.65 (13/20 matched) — the mechanism removes *false* exits, it
does not find missing *true* ones, which is the honest reading of a supply-side accreditation
repair.

### 5.3 Position at full magnitude, both of D66 §1.2's frames

| DY | model | gap B | gap A | |
|---|---|---:|---:|---|
| 2023/24 | 1.06233 → 1.05770 | −1.061 → **−0.598** | −0.712 → **−0.250** | **narrows** |
| 2024/25 | 1.05731 → 1.05970 | −0.336 → **−0.575** | −0.180 → **−0.419** | **widens** |
| 2025/26 | 0.99802 → 1.00091 | +1.190 → **+0.901** | +0.687 → **+0.398** | **narrows** |
| | **Σ\|gap\|** | 2.587 → **2.074** | 1.579 → **1.067** | |

### 5.4 **PRECOMMIT STOP 4 FIRED — two misses, reported at full magnitude**

**(a) DY 2025/26's residual NARROWS where the PRECOMMIT predicted it would widen.**
**(b) The 2024/25 and 2025/26 census move UP (173,512 → 173,905 and 144,164 → 144,581 MW) despite
less VRE credit in both years.**

Both have the same cause, and it is **not** a defect in the mechanism: the arm retired **763.9 MW
less in 2023**, so more thermal is standing from 2024 on, and that propagation **outweighs** the
direct −332.9 / −148.3 MW VRE reduction. The direct effect is exactly as pre-declared (§5.1,
identity holds to 0.001 MW); what the fixed-pool arithmetic could not represent is the fleet its own
decisions leave behind. This is the channel PRECOMMIT §6 named ("the screen's census is the solve's
own") and D62's STOP 5 recorded before it — **stated as a fired STOP, not absorbed**, and **nothing
was re-tuned in response** (rule 1 `[R-STRUCT]`).

### 5.5 The 2024/25–2025/26 confinement leg reads FAIL — diagnosed, and it is NOT a leak

`thermal_accredited_identical` is False in 2024 and 2025. The diagnosis is decisive: **requirement
(164,107.6 / 144,450.0 MW), storage firm MW and the VRE pools are identical in EVERY year**, and
thermal was **byte-identical in 2023**, the screen year where both arms enter with the same fleet.
The 2024–25 difference is therefore the **downstream fleet divergence** of the arm's own 2023
decisions, not the mechanism reaching outside its declared footprint. Confinement is a **screen-year
leg** by construction — it can only mean what it is meant to mean where the entering fleet is
shared — and this lane's analyzer applies it to every year, so its later-year verdict is reported
here with that reading rather than as a failure. The 2025 clearing price also falls
**358.267 → 328.007 $/MW-day** through the same channel.

## 6. What this lane ROUTES rather than absorbs

1. **`evolution_2022.json` still carries no adequacy block** (`wind_cap_mw` / `solar_cap_mw` /
   `renewable_credit_applied` / `storage_firm_mw` absent) while 2021 and 2023–2025 carry it —
   D75 §6 item 3. **Reproduced on a FRESH solve at current HEAD**, so it is not a stale-bundle
   artifact; it forced a pool reconstruction in both this lane's phase 0 and its full-window
   analyzer. Unexplained; a lane that owns the ledger should take it.
2. **The EIA-860 `Fixed Tilt?` / `Single-Axis Tracking?` derivation** — ruling R1 made it a separate
   data-intake card; it is the only route that regenerates forward from the model's own build
   (rule 13's test) and would retire the cross-vintage reconciliation §1 declares.
3. **The 2025/26 BRA-vs-3IA vintage question** (D75 §5): this lane wires the delivery year's FINAL
   (3IA) ratings and says so; the 2025/26 BRA cleared on the ratings current in July 2024 and that
   report's tables are images that do not extract.
4. **PJM's 2025/26 3IA thermal ratings differ from the wired 2026/27 set** (gas CC 78 vs 74, CT 63
   vs 60, steam 74 vs 73, diesel 92 vs 91; nuclear and coal equal). The intake now carries them.
   That is a **THERMAL** vintage gap on D48's own half, not this card's — routed, untouched.

## 7. Two procedural errors of my own, recorded rather than glossed

1. **The full control's HEAD guard tripped (exit 90).** I committed the screen gate table *while
   that solve was running*, so `git rev-parse HEAD` moved under it. Audited immediately: the entire
   diff between the two shas is **one file, `docs/handoffs/d75r/screen-gates.json`** — zero
   solve-path files (`src/market_sim`, `scripts/run_*`, `scripts/lib`, `data/raw` all empty). The
   bundle is therefore valid and is used. The guard did its job; I made the sha move. No commit was
   made during any subsequent solve.
2. **My own gate analyzer had a pool-vintage bug**, found on this lane's full-window run and fixed
   before any number here was quoted: it computed the reported accredited-VRE delta on **end-of-year**
   pools where the screen accredits the **prior** year's, which inverted the reported sign in 2024
   (+277.9 instead of −332.9) in a year with VRE additions. `gate_identity.holds` was always
   computed on the **credits**, so no verdict was ever affected — only the reported MW. Fixed to
   read `evolution_{Y-1}`'s pools, with the same roll-forward phase 0 uses for the 2022 gap.

## 8. Recommendation

**The mechanism is correct, it is measured, and I recommend ARMING it for PJM — as an owner
decision, which this lane does not take.** The case, in the order the rules weigh it:

1. **Rule 14 `[R-ACCURATE]` is the reason, and it is dispositive on its own.** These are the ISO's
   OWN published accreditation values for the delivery year each auction actually cleared on. The
   incumbent curve applies PJM's **2026/27 marginal-ELCC** ratings to 2023, 2024 and 2025 — three
   years that cleared under a different published construct — purely because the curve clamps.
   Preferring the published vintage is what the rule requires **whatever it does to the fit**, and
   this lane would make the same recommendation had the residual moved the other way.
2. **Nothing regresses.** All 26 scored bands are byte-identical; no criterion flips in either
   direction; CO2 is unmoved.
3. **Structural integrity improves, and so do the numbers** — which is the easy case, not the hard
   one the owner's standard contemplates. FC-3's total-retirement error falls **0.199 → 0.148**,
   false exits fall 469 MW, release precision rises, and Σ|gap| falls on both frames.
4. **The DOF cost is zero** beyond the one reconciliation ruling R1 authorised and this document
   declares at the seam.

**What arming does NOT close, stated at the gate:** the model still over-retires (17.294 vs 15.062
GW actual) and `unit_recall_gt300` is unchanged at 0.65 — this repair removes false exits, it does
not find missing true ones. The 2024/25 and 2025/26 census remain **below** the published cleared
position and this mechanism moves them the wrong way there through fleet propagation (§5.4); that
residual is D66 card B's remaining half and is **not** closed here.

**If arming is granted**, the honest posture is the D57 precedent: arm it in
`iso_configs.py::_pjm_config`'s `default_scenario_overrides` alongside the three gates already
there, leaving the shared `ScenarioConfig` default OFF so every other ISO and every backcast keeper
stays byte-identical and `--no-pjm-vre-accreditation-vintage` still reaches the control. **This lane
has not done that**, and no default was moved.
