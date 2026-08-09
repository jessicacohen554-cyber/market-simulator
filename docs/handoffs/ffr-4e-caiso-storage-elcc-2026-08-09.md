# FFR-4E — CAISO's published storage accreditation, reconciled; and FC-2 row 4 re-read

**Lane.** FFR-4D's routed top successor (§7 D-1 + D-4), chartered against the
ACCREDITATION-RATE cause. Branch `claude/ffr-4e-caiso-storage-elcc-1gznik`, based on
`origin/main` **`2ce94eb`** (rebased fresh at session start; re-verified below).

**The capacity-price ANCHOR route is REFUSED, as chartered.** No CAISO capacity-price
anchor, net-CONE, CPM soft-offer cap or entry-screen price term is read, changed, or
quoted anywhere in this work, and **no row-4 improvement via that route is claimed**.
§8 states this formally.

---

## PRE-REGISTRATION (written and committed BEFORE the treated arm was solved)

Committed in `ffr-4e: pre-register` so the decision rules below cannot be read as
post-hoc. Results sections are appended after.

### P-1. The construction, chosen before measurement

CAISO's published battery accreditation enters as a **whole-class ratio on a NAMEPLATE
basis**, NOT as a by-duration table:

```
STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"] = 13,365 / 15,448.4 = 0.865138
```

gated behind a new **default-OFF** `ScenarioConfig.caiso_storage_nqc_accreditation`.
Rationale pre-registered in §3; the three reasons, stated before the row-4 read:

1. **CAISO publishes no storage duration table.** The CY2026 NQC report's `2026 Tech
   Factors` tab has **no battery row** — batteries are *dispatchable* and are accredited
   at demonstrated capability, not by a technology factor. Minting a CAISO
   `STORAGE_ELCC_BY_DURATION_BY_ISO` entry would be inventing an object CAISO does not
   publish.
2. **The published ratio is NQC/NDC; the model's multiplicand is nameplate.** Dropping
   0.9458 onto `power_cap_mw` is the substitution FFR-4D §6.1 warned against, and it is
   quantified in §3.3.
3. The registry gains a whole-class path that is **one mechanism, not a stack** (rule 19):
   where a whole-class ratio exists it **replaces** `_elcc_for_duration`, never multiplies
   it.

### P-2. Keeper guard — the gate is default-OFF, and that is the pre-registered posture

The CAISO **backcast** keeper `2026-08-09-caiso-184-c1-lpbasis` **does** consume the
storage accreditation entries (§4 enumerates the four consumers; `run_config.json` shows
`capacity_deliverability_limits: true`, `storage_capacity_value: true`,
`renewable_elcc_curves: true`). Byte-inertness is therefore **not** available by
inspection, and the keeper's evolution ledger is not committed (bundles are slim), so it
cannot be re-read without a re-solve. The charter's second branch is taken: **gate the
intake default-off**, which makes byte-inertness hold *by construction* rather than by
measurement. Pre-registered check **G-INERT**: with the gate absent, the CAISO
accreditation chain is numerically identical to HEAD, and the pinned default cache key is
unmoved.

### P-3. FC-2 row 4 arms

Both arms at this head, cold, `scripts/run_full_horizon.py --iso CAISO --start-year 2026
--end-year 2030` (5 years, sequential — rule 12), separate `--out-dir`s:

| arm | config |
|---|---|
| **control** | HEAD default (gate off) |
| **treated** | `caiso_storage_nqc_accreditation` ON, nothing else changed |

**The control is a NEW control, not FFR-4D's.** FFR-4D's D-8 control (14,043.6 / 21,448.0
/ 65.48 %) was measured *before* its own fleet fix; that fix is merged at this head, so
the expected control here is FFR-4D's **treated** arm (≈ 8,186.3 MW / 52.51 %). Predicted
before solving; §5 reports what actually came back.

### P-4. Decision rule, pre-registered

Row 4 scores `cumulative reserve_backstop thermal additions ÷ total additions`
(`scripts/forecast_verdict.py`): **PASS ≤ 10 %, CAVEAT 10–30 %, FAIL > 30 %**.

* If the treated arm clears to PASS or CAVEAT — report it as the accreditation cause
  closing, with the fleet fix (FFR-4D) as the other half.
* **If row 4 still FAILs with the fleet AND the accreditation right — THAT IS THE
  FINDING** (rule 11). It is written as such; **no further lever is pulled in this
  session**, and in particular the capacity-price anchor is not touched. The residual then
  points at the anchor object, which is **NOT this lane's** — it may be chartered later,
  by someone else, on its own rule-14 merits.

### P-5. D-4 (dilution) decision rule

Intake a published CAISO/CPUC **portfolio** dilution source if one exists at citation
quality; otherwise **HOLD the hard 1.0** and document the assumption in the registry
comment. Pre-registered: the committed E3/Astrapé incremental study is examined for this
purpose, and it qualifies only if it is a *portfolio/fleet-average* object on a
*compatible penetration axis*. §6 records the adjudication.

---

## 1. State verified at this head

| item | verified |
|---|---|
| `origin/main` | **`2ce94eb`** |
| CAISO keeper | **`2026-08-09-caiso-184-c1-lpbasis`** — re-read from `frontend/data/backcast/keepers/CAISO.json` at this head, as the packet instructed |
| `complete` markers | CAISO **absent** (withdrawn by the owner 2026-08-06 at caiso-178) |
| `final` markers | EMPTY — CAISO's locked test never granted, never spent |
| years touched | **2023–2025 in-sample (none solved) and 2026–2030 forecast ONLY.** No out-of-training year was solved, scored, read or approached. |

Prerequisites ran in the briefed order: `uv sync` first, then
`scripts/regenerate_clean.py`.
