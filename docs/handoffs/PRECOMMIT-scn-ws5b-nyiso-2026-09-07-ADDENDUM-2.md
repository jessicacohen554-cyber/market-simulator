# ADDENDUM 2 to PRECOMMIT-scn-ws5b-nyiso-2026-09-07 — the REF leg landed, the identity gate PASSES exactly, and four predictions are already scorable

**Written with `REF` returned, `CAP-STATE-TIGHT` still solving and `CES-P60` just launched.**
This is an interim record, not the FINDING: it exists because the container is ephemeral and
because the numbers below are what §7's predictions are scored against — recording them now,
before the remaining legs land, is what stops any of it being written to fit a later result.
**No prediction in the parent PRECOMMIT §7 is edited here.** Each is quoted as written and scored.

---

## 1. `REF` — solved, and every pre-declared property holds

| property | pre-declared (PRECOMMIT §4/§6) | **measured** | |
|---|---|---|---|
| cache_key | `f1a2ef17634b0467` | **`f1a2ef17634b0467`** | **MATCH** |
| horizon | 2026–2050 | 2026–2050, `n_solved_years` **25**, `error: null` | ✓ |
| wall | ≈2.0–2.5 h (4.87 min/solve-year × 25) | **6,970.1 s = 116.2 min**, **4.647 min/solve-year** | ✓ |
| peak RSS | ≈3.5–4.1 GB | **3,953.4 MB** | ✓ |

**P-8 (cost) — the super-linear uplift is refuted a second time.** NYISO's 25-year per-year cost
(**4.647** min/solve-year) is **4.5 % BELOW** its own 5-year Stage-A rate (4.87), even though the
per-year cost *rises* within the 5-year window (219 → 331 s). That independently reproduces the
program's only prior 25-year measurement (GOLDEN-3 NEISO, years 21–25 at 0.68× years 1–5) and
refutes FF-3E's ~1.76× projection on a second ISO. The PRECOMMIT's flat-median bracket was the
right instrument; the projection was not.

Run id `nyiso-2026-2050-scn-campaign-stageb-2026-09-07-ref` (ADDENDUM 1 §2), committed at
`docs/handoffs/scn-ws5b-nyiso/REF/`, solved by shard S-1's sibling S-2 (commit `5e2d851e`,
**two files, both inside its own directory** — scope verified by `git show --stat`).

---

## 2. THE 2026–2030 IDENTITY GATE — **PASS, EXACTLY**

The gate pre-registered in PRECOMMIT §8, run as written: every scalar in the summary's own
trajectory row, plus every member of `capacity_by_fuel_mw` / `generation_by_fuel_mwh` /
`builds_by_source`, over 2026–2030, Stage-B `REF` against the committed Stage-A `REF`.

```
Stage-B f1a2ef17634b0467  vs  Stage-A f10cc93084b4c0db
232 scalars compared | worst |rel| = 0.000e+00
VERDICT: PASS   (pre-registered: PASS <=1e-9, WARN <=1e-6, FAIL beyond)
```

**Not "within tolerance" — identical, to every printed digit, on all 232.** The tolerance band
was never used.

**This is the strongest single confirmation the lane has produced, and it validates three separate
things at once:**
1. **G-DRIFT's all-INERT classification was right**, including the one judgement call — the
   measured SPP-41 `_screen_fuel_spike_columns` seam (§2.4). Had that hunk reached a NYISO
   forecast input, this gate would have moved.
2. **The shard's `data/clean/` rebuild reproduced the inputs bit-for-bit.** The S-2 container had
   to regenerate the derived tree from `data/raw/` before solving; the gate proves the
   regeneration is deterministic. *(It also reports two datatypes failing to rebuild on separate
   paths — `lmp` and `emissions-unit-annual` — which the solve does not consume; ROUTED to
   SCN-DESK as an observation, not repaired here.)*
3. **The horizon extension is inert in the overlapping years.** `end_year` is the only difference
   between the two base YAMLs, and nothing in the solve path reads it as a per-year input.

**P-1 scored: PASS on `REF`.** The remaining four legs are gated identically as they land.

---

## 3. `REF` at full horizon is a materially different case from `REF` in the T1-F window

| year | `co2_mt` | S12 budget Mt | cap vs REF | `lw_price` | `vre_mw` | `gas_cc_ccs` MW | `rps_dual` |
|---|---|---|---|---|---|---|---|
| 2026 | 23.692 | 23.160 | **tightening** | 50.19 | 3,900.0 | 0.0 | 40.00 |
| 2027 | 24.591 | 22.420 | **tightening** | 49.18 | 3,900.0 | 0.0 | 40.00 |
| 2028 | 17.163 | 21.680 | loosening | 50.92 | 3,900.0 | 2,984.4 | 40.00 |
| 2030 | 10.903 | 20.200 | loosening | 54.95 | 6,743.4 | 6,255.9 | 40.00 |
| **2033** | **9.126** *(minimum)* | 17.980 | loosening | 60.49 | 10,743.4 | 7,255.9 | 40.00 |
| 2035 | 9.222 | 16.500 | loosening | 60.46 | 13,743.4 | 7,255.9 | 40.00 |
| 2040 | 11.032 | 12.800 | loosening | 69.41 | 19,743.4 | 7,255.9 | 40.00 |
| 2041 | 11.573 | 11.980 | loosening | 70.86 | 22,743.4 | 7,255.9 | 40.00 |
| **2042** | **12.258** | **11.160** | **TIGHTENING** | 73.13 | 22,743.4 | 7,255.9 | 40.00 |
| 2045 | 14.338 | 8.700 | tightening | 81.14 | 28,743.4 | 7,255.9 | 40.00 |
| 2050 | 18.352 | 4.600 | tightening | 109.19 | 34,743.4 | 10,255.9 | 40.00 |

**P-4(a) — the CAP-STATE-TIGHT crossing year. PRE-REGISTERED 2044, band [2041, 2050]. MEASURED
2042. Band PASS; central estimate MISSED by two years, and the MECHANISM I gave was wrong.**
Reported at full magnitude rather than smoothed: I predicted the crossing would come from the
budget glide falling toward a flat-or-still-declining `REF`. It does not. **`REF` emissions bottom
out at 9.126 Mt in 2033 and then rise monotonically to 18.352 Mt by 2050 — they double.** The
crossing is driven from *both* sides at once, and the rising limb is the larger half. What rises
is load: the demand and datacenter paths outrun the clean build, while `gas_cc_ccs` sits flat at
7,255.9 MW for fourteen years (2032–2046) before adding 3.0 GW at the very end. **This is a
finding about `REF`, not about the cap** — and it is the single most consequential thing the
horizon extension has surfaced so far, because every Stage-A delta was measured against a
five-year window in which `REF` was *falling*.

**P-9 (`rps_dual`) — CONFIRMED on `REF`, and the conditional limb did not fire.** `rps_dual` reads
**40.0000 in all 25 years**, at `STATE_RPS_ACP["NYISO"]`, exactly as it did in all five years of
all ten Stage-A legs — *even at 34,743.4 MW of VRE, nearly 9× the 2026 fleet.* The RPS row never
becomes interior in `REF`. Whether the `CES-T80` / `ALL-CLEAN` target row reaching 1.00 at 2050
moves it is still open and is scored when those legs land.

**A Stage-A finding is RETIRED by the horizon — the honest way round.** PRECOMMIT §1.4 (quoting
Stage-A §1.4) recorded: *"REF curtails **exactly 0.0 MWh** of wind and solar in every year, so G8
is recorded **N/A** with its reason."* At full horizon **`REF` curtails up to 10.55 % of renewable
potential** (I3 detail: 2.62 % at 2043 rising to 10.55 % at 2049). **G8's object does not fail to
exist — it needed a horizon long enough for VRE to saturate.** The Stage-A N/A was correct *for
its window* and is superseded, not contradicted.

### 3.1 `REF`'s own invariants — one FAIL, three WARN

- **I3 FAIL (unserved/dump).** Two limbs, both new at this horizon. **Dump** (renewable
  curtailment) 2.62 % → **10.55 %** of potential across 2043–2049. **Slack** (unserved load) from
  2047: 52 h / 30.0 GWh / peak 1,595 MW at 2047, growing to 113 h / 104.7 GWh / peak 2,596 MW at
  2050 — 0.01 % → 0.05 % of load. **The REFERENCE case sheds load in its last four years.** This
  is declared in `invariant-failures.json` in the registration commit, per the Y-24 ratchet.
- **I12 WARN** — reserve margin 23.6 % at 2035 against a requirement-implied band [8.2 %, 23.2 %].
  One year, 0.4 pts over.
- **I13 WARN (cobweb)** — `wind(21)`, `solar(18)`, `gas_cc(7)`. Visible in the table above as
  **3,000 MW renewable-build pulses on alternating years from 2033** — the entry screen oscillating
  against an annual cap. Reported; it is a one-pass-evolution property (rule 10 `[R-ONE-PASS]`),
  not a defect introduced by this campaign.
- **I14 WARN** — `lw_price` $96.3 / $101.7 / $109.2 at 2048–2050 outside [0.5×, 3.0×] of CC MC
  $31.0. Not declared (WARN, not FAIL), consistent with Stage A's treatment.

---

## 4. SCN-FIX3's dual recording seam is live, and it behaves as its contract says

Every Stage-B trajectory row carries **both** new keys. On `REF` they read
`clean_region_duals: null` and `co2_cap_price: null` in all 25 years — which is **correct and is
the contract, not a gap**: `REF` has no clean-tier row and no mass cap, and `_policy_duals`
returns `None` (never `0.0` or `[]`) when the family carried no rows. The keys being *present* is
what proves the seam fired.

**Consequence, restated before the legs that need it land:** `CAP-STATE-TIGHT`'s `co2_cap_price`
and `CES-T80` / `ALL-CLEAN`'s `clean_region_duals` will be readable from the committed summary at
the coordinator. **This lane's Stage-A §9 item 4 is therefore discharged in practice, not just on
paper**, and the G4/G7 dual limbs are scored **as the gates state them** rather than by Stage A's
identity substitute. Stage-A legs carry neither key, so any Stage-A ↔ Stage-B dual comparison is a
comparison against an **absent** record and is reported as such.

---

## 5. Shard record, corrected

| shard | leg | session | state |
|---|---|---|---|
| S-1 | `CAP-STATE-TIGHT` | `session_01NGJCYY3dnspeh8qvmadnzj` | **solving**, background; its own note revises the cost projection **upward** from ≈5.4 h |
| S-2 | `REF` | `session_01DfnnL7pj4rt9YhRbb1UgDV` | **DONE** — 116.2 min, key matched, archived |
| **S-3** | `CES-P60` | `session_016BrbcZfg4zjQbdFo2kVX1G` | **launched** |
| S-4 | `CES-T80` | — | queued (S14 caps the SCN track at 2 concurrent) |
| S-5 | `ALL-CLEAN` | — | queued |

**Two corrections to ADDENDUM 1 §3, made because it is a record.** (a) The launch times there
(2026-09-08T05:41/05:42Z) were copied from `create_session`'s `created_at`, which reads ~10 h
before the container clock; the real launches were **≈23:30Z on 2026-09-08**. (b) ADDENDUM 1 said
each shard pushes its branch; **S-2 additionally opened a PR and merged itself to `main`**, which
was not asked for. No harm resulted — the merge carried **two files, both inside its own case
directory** — and the artifacts are on `main`, which is where the coordinator wanted them anyway.
The S-3 prompt adds an explicit **"do not open a pull request and do not merge to main"**; the
coordinator integrates.

**Operational note for any successor coordinating S16 shards:** `SendMessage` and `ListAgents`
do **not** reach these cloud sessions — they see only agents on the local machine. The mechanism
that works is `create_trigger` with `persistent_session_id` set, then `fire_trigger`. A shard that
goes IDLE has stopped and will not resume on its own; a shard that is IDLE *with a background
solve running* is behaving correctly and must **not** be poked.

---

*Written before `CAP-STATE-TIGHT`, `CES-P60`, `CES-T80` or `ALL-CLEAN` returned. Parent:
`docs/handoffs/PRECOMMIT-scn-ws5b-nyiso-2026-09-07.md` and its ADDENDUM 1.*
