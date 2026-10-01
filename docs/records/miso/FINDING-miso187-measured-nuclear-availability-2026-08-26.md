# FINDING miso-187 — the MEASURED-NUCLEAR AVAILABILITY ARM lands a **STRUCTURAL SPLIT** (S-3 outflow PASS at +0.298 GW — the ex-ante prediction almost exactly — with S-2 direction unchanged at 7/47), the scored face is **NET-NEUTRAL** (C3a-2025 unchanged to 4 dp, zero criterion flips), and the arm is **PROMOTED KEEPER** under the owner's in-session directive resolving the pre-registered escalation

**Session miso-187 (2026-08-25/26).** Executes
`PREREG-miso187-measured-nuclear-availability-2026-08-25.md` (committed and
pushed at `db0f1d9` **BEFORE any adjudicating quantity was computed**; the
frozen scorer at `0fd6997` before it ran). The queue head per miso-186 §3/§6
— the second candidate that cleared every PREREG-miso186 §4 admissibility
clause, unarmed there only by the single-delta selection rule. **LP SPENT
under the standing charter:** control + arm `replay_keeper` replays of
`miso186_dir_B` at HEAD, full span, both registered
(`2026-08-25-miso-187-control` / `2026-08-26-miso-187-nucavail`).
**KEEPER CHANGES: `2026-08-25-miso-186-statusscope` →
`2026-08-26-miso-187-nucavail`** (owner in-session directive, §4).
Determination of the new keeper: **NOT-YET on {C3a-2025, C1 fuelmix
CC_REGULAR 2024}**, C6 attested, C8 PASS all years, C3c the single ledgered
caveat — the same basis as the outgoing keeper, with C1 2024 a hair
*smaller*. **Matrix cell adjudicated: `nuclear_unit_availability` U → `K`**
in MISO's shard (an existing `ScenarioConfig` field — no new row, duty 26(c)
not triggered).

Instruments: `scripts/probes/_miso187_ab_gates.py` →
`results/calibration/_miso187_ab_gates.json` (S-0…S-5 + the charter kill);
`scripts/gen_miso187_attestation.py` (the keeper attestation; ledger 35
entries / `n_residual` 2 unchanged).

## 0. The verdict

The pre-registered structural gates **SPLIT**: **S-3 PASS** — the model's
2025 scarce-mean South boundary-complex net inflow moved +0.682 →
**+0.385 GW**, +0.298 GW toward the measured −2.441, matching the committed
+0.299 GW static reach almost exactly — while **S-2 FAIL** — the N→S RDT
binding count did not move (7/47 → 7/47, composition 7/0/40 untouched). The
PREREG §4 promotion rule maps a split to owner escalation with keeper
unchanged by default; the owner resolved it in-session, in writing and in
advance (*"Is this a recommended keeper candidate? If so plz promote. If
structural integrity improves but gates regress that may still be a
keeper."*), delegating the recommendation. The recommendation was **YES**
(§4), and the arm was promoted with both faces disclosed at full magnitude.

## 1. The data work (charter steps 1–3)

* **Disclosed correction to the charter's framing.** The charter (and
  miso-186 §3) said MISO had "no `NUCLEAR_MONTHLY_CF_BY_YEAR` entry" and
  attributed the 0.897 smear to "the static seasonal pattern × (1−EFORD)".
  **Both sub-claims are false at HEAD**: the anchor exists
  (`constants.py`, with its own EIA-923 derivation citation) and is the
  active smear — on the frozen 2025 scarce set (months 21×Jun/13×Jul/5×Aug/
  8×Sep) the anchor means **0.8972**, the committed 0.897 exactly, where the
  static alternative would mean 0.912. The structural claim (uniform across
  all 13 reactors, no per-reactor layer) was correct and is what the arm
  repairs. Charter step 1 therefore became a **verification**:
  `derive_nuclear_monthly_cf.py --isos MISO --check` — the committed table
  matches the EIA-923 derivation exactly.
* **The crosswalk.** `NRC_TO_EIA["MISO"]`: 13 reactors exactly matching the
  model fleet — Clinton (204,1), Fermi 2 (1729,2), Monticello (1922,1),
  Prairie Island 1/2 (1925,1/2), Point Beach 1/2 (4046,1/2), Waterford 3
  (4270,3), Grand Gulf 1 (6072,1), Callaway (6153,1), River Bend Station 1
  (6462,1), Arkansas Nuclear 1/2 (8055,1/2). Palisades reports to NRC but
  carries no EIA-860 OP fleet unit (the Crane comment discipline);
  Duane Arnold carries neither.
* **The extract.** `derive_nuclear_availability.py --iso MISO` →
  `data/raw/nuclear-availability-MISO.csv`: 6,760 rows, 13 reactors,
  `--check` reproduces byte-for-byte. **Every Jun–Sep month 2023–2025
  reconciles to the anchor within tolerance** (2025 Jun/Jul/Aug/Oct to
  +0.0000 %); **14 winter/shoulder months** (2023: Jan–Apr, Oct–Dec; 2024:
  Feb–Apr, Oct–Dec; 2025: Jan–Mar, May, Nov) hit the thermal-vs-net wedge
  and are DROPPED — the smear stands there per the deriver's documented
  fallback, so the overlay's reach is concentrated exactly in the
  scarce-relevant window. Frozen scalars inherited verbatim (rule 23).

## 2. The A/B (PREREG §4 = PREREG-miso184 §6 verbatim re-keyed; record `_miso187_ab_gates.json`)

| gate | result |
|---|---|
| S-0 control inertness | **PASS** — max\|diff\| = 0.0 on every scored sidecar of every year vs the committed keeper |
| S-1 exactness | **PASS** — single delta in `run_config`; Callaway 2025 scarce dispatch **1067.7 → 615.2 MW**, South 5-reactor aggregate **4718.5 → 5114.5 MW** — both exactly as the NRC record predicted |
| **S-2 direction** | **FAIL** — 2025 scarce N→S binding **7/47 → 7/47** (S→N 0/47, unconstrained 40/47; composition untouched). 2023: 3 → 3; 2024: 1 → 1 |
| **S-3 outflow** | **PASS** — `N_S^m` +0.682 → **+0.385 GW** (move **+0.298** ≥ 0.1 toward the measured −2.441; matching the +0.299 committed static reach; balance verified < 1 MW) |
| charter kill | **SILENT** — C3a-2025 does not improve (unchanged), and S-3 passes |
| S-4 conduct | **PASS** — zero D-4 fails, zero new; C8 PASS all years (2025 ST_GAS grounded-above-budget note carries over) |
| S-5 full magnitude | C3a: 2023 +1.2177 → **+2.4049 %** (sole regression, in-band), 2024 −4.6749 → −4.6440 %, 2025 **−12.3185 → −12.3185 %(unchanged to 4 dp)**; **ZERO criterion flips** (C1 CC_REGULAR 2024 stays FAIL and improves +8.089 → +8.037 TWh vs ±8.00); no band exits — the escalation condition itself never fired |

Nuclear annual energy is anchor-preserved as designed: control
87.152/90.199/90.591 TWh (2023/2024/2025) vs arm 86.994/90.022/90.446 —
≤0.18 TWh/yr, pure redistribution across reactors and days.

## 3. Reading the split

The two structural gates measure different depths of the same object. S-3
is the *flow*: 0.3 GW of real South supply restored in scarce hours flows
straight out of the region, shrinking the wrong-way wheel by the predicted
amount. S-2 is the *price-spread regime*: a binding hour flips only when the
South's economic surplus at the Midwest price changes sign, and the miso-186
decomposition already measured that gap at ~3.6 GW of mc-idled South
capacity (the EXHAUSTED offer family / adjudicated flat-stack model-class
residual) — 0.3 GW of nuclear cannot close it, and did not. The S-2 non-move
at unchanged composition is therefore the expected honest remainder, not
evidence against the layer. C3a-2025's exact non-move is the same physics at
the level grain: +0.299 GW of cheap South supply and −0.075 GW of Midwest
supply nearly cancel in the ISO-mean price.

## 4. The promotion (owner in-session directive)

The PREREG froze: a split ⇒ registered, keeper UNCHANGED, owner escalation.
The owner's message this session — *"Is this a recommended keeper candidate?
If so plz promote. If structural integrity improves but gates regress that
may still be a keeper."* — is that escalation's answer, delegating the
recommendation. The recommendation was **YES**, on rules 1/14:

* The control keeps a uniform fleet-month smear where an **admissible
  measured per-reactor record exists** — the candidate's five admissibility
  clauses were adjudicated at miso-186 §3, and MISO was the ONLY
  multi-reactor ISO whose keeper lacked the overlay all four sister ISOs
  carry (pjm-nuc-1b owner-ordered, nyiso-98, caiso-148, neiso-71). Keeping
  the smear on the S-2 result would be preferring an estimate over measured
  data because of a residual — rule 14's named failure mode.
* The structural evidence moved the right way at the predicted magnitude
  (S-3 +0.298 vs +0.299 predicted; S-1 witnesses exact), with zero fitted
  parameters (ledger 35 entries, `n_residual` unchanged at 2; LOYO
  trivially clean — the identification is a published physical measurement,
  year-independent).
* The scored cost is essentially nil: C3a-2025 unchanged, 2024 and C1
  CC_REGULAR 2024 hair better, the single in-band 2023 shift (+1.19 pp)
  disclosed; zero flips; S-4 clean.

Promotion mechanics executed: arm attestation generated
(`gen_miso187_attestation.py` — C6 attested; determination basis NOT-YET on
{C3a-2025, C1 CC_REGULAR 2024}, C3c ledgered), `keepers/MISO.json` re-keyed
(prior note archived as `superseded_promotion_note_miso186`),
`status/MISO.js` rebuilt, matrix §5.4 header + queue stamp + MISO shard
re-stamped (cell U → K; `check_mechanism_matrix.py` clean),
calibration-log entry appended, calibration-keeper-auditor fired. MISO
holds no `complete`/`final` marker, so no rule-22 D-5(b) re-key is owed.

## 5. What the direction object is after the repair

N→S binding 7/47 (unchanged) and +0.385 GW scarce-mean INTO the South vs
the measured 32/47 S→N record and −2.441 GW out. The named availability
road is now exhausted: both miso-186 §3 candidates are armed and in the
keeper. The remaining formation is the ~3.3 GW mc-idled block — the
adjudicated flat-stack/tail model-class residual (offer family EXHAUSTED at
both grains, miso-179/180) — folding back into the standing owner D-4
posture question with the ~1.3 GW scarce-export concession (miso-184 GAP),
now another 0.3 GW smaller in the outflow dimension. The miso-183
falsifiable prediction stands for any future candidate.

## 6. Reported against interest

* **The PREREG/charter factual correction** (§1): the anchor exists and is
  the active smear; the miso-186 §3 "no entry" sub-claim was false. The
  structural charter survives it unchanged, but the record is corrected.
* **S-2 failed at its declared line** — the arm did not move the RDT
  binding count at all; the gates are reported as the split they are, and
  the promotion rests on the owner directive + rules 1/14, not on any claim
  the direction gate passed.
* **The arm leg was killed once mid-solve** on a misread log line: the
  assembly-stage arrays build logs "0 reactor(s)" because its
  binned-cache generators list carries non-matching ids; the LP's own
  dispatch-fleet build (between the import-node and unit-outage-derate
  steps) applied **13/13 reactors in every year**. The partial out-dir was
  deleted unread and the leg relaunched clean; S-0 control identity proves
  the assembly-stage build is output-inert. The cache-id mismatch in that
  non-dispatch build is noted as a cosmetic wart, not repaired here.
* **The arm's run id is dated 2026-08-26**, not the PREREG's declared
  2026-08-25 — the relaunched solve crossed midnight UTC and the id date
  derives from the bundle timestamp. Naming deviation, disclosed.
* **A container restart killed the first control-leg wait** mid-session;
  the control bundle was verified complete on disk (its log ends at the
  replay's final post-step) before any further step.
* **The legs ran at tree `0fd6997`** (pre-merge) while scoring ran at the
  merged `5520a7d`: the diff between the two touches ZERO solve-path files
  (rubric v3.5 scorer + docs only, enumerated in-session), both legs were
  scored with the same scorer, and S-0 confirms output identity with the
  committed keeper.
* **The NYISO matrix shard arrived syntax-broken from main** (a raw `"`
  inside a `verbatim:` comment string, nyiso-155 promotion); it got a
  mechanical single-quote swap — content unchanged — so the matrix guard
  could run. Cross-lane edit, disclosed; no NYISO verdict or stamp touched.
* **Registration prunes** under top-15 retention removed
  `2026-08-19-miso-170-membership` and `2026-08-19-miso-170-sitegrain`
  (tool-decided; committed with the registrations).
* **14 wedge-dropped months** keep the smear (§1) — the overlay is NOT a
  full-year replacement; its coverage is exactly the reconciliation-clean
  months, scarce season included.

## 7. Standing OWNER items, restated not decided

(1) the C8 provenance-materiality floor (unrepaired); (2) the
committed-vs-regenerated diagnostics exposure; (3) `RHO_CLIP` cross-ISO
band item; (4) **D-4 posture — the direction object is now 0.3 GW smaller
in the outflow dimension with NO named availability arm remaining**: the
~1.3 GW scarce-export model-class concession stands behind the ~3.3 GW
mc-idled block; (5) the C1 fuelmix CC_REGULAR 2024 band exceedance (now
+8.04 vs ±8.00 — repairing it is offer-family/flat-stack territory,
adjudicated exhausted); (6) the MISO-Illinois $8.22/MMBtu scarce
delivered-gas observation (Midwest lane).

## 8. Governance

Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; MISO holds neither marker;
freeze untouched; no new fetch; no re-key owed. Rule 15/16: BOTH legs
registered, full span, one invocation each. Rule 12: years sequential; legs
sequential; miso-169 memory recipe (8 GB swapfile,
`MARKET_SIM_HIGHS_THREADS=4`). Rules 5/13/14/23/24: the field is the
existing registered `nuclear_unit_availability`; measured-identified, zero
fitted scalars; anchor verified never re-tuned; frozen deriver scalars
inherited. Rule 26: §5.4 header + queue stamp + MISO shard cell/keeper/
gates re-stamp + calibration-log entry in-session;
`check_mechanism_matrix.py` clean. Rule 27 `[R-PUSH]`: exact on-disk bytes;
every pushed blob ≥300 lines verified. No new `.github/workflows`.
**DO-NOT-REDO honoured throughout** (miso-185 §9 + miso-186 carried in
full): nothing re-opened; the offer family untouched at both grains;
`unit_outage_fleet_status_scope` not re-tested (it is the predecessor
mechanism, carried in the keeper recipe).

## 9. Reproduction

```
cd <repo root>
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
  --python 3.12 python scripts/data/derive_nuclear_monthly_cf.py --isos MISO --years 2023 2024 2025 --check
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
  --python 3.12 python scripts/data/derive_nuclear_availability.py --iso MISO --check
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml,highspy \
  --python 3.12 python scripts/probes/_miso187_ab_gates.py
```

Reads the committed `miso186_dir_B` sidecars, the miso187_nuc_A/B bundles,
`data/raw/nrc-reactor-status/{2023,2024,2025}PowerStatus.txt`,
`data/raw/nuclear-availability-MISO.csv`,
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`. PREREG:
`db0f1d9`; crosswalk+extract: `197a8ba`; scorer: `0fd6997`; scoring HEAD:
`5520a7d` (PR #4287's merge).
