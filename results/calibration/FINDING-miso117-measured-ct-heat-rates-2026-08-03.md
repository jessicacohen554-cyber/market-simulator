# FINDING miso-117 — `measured_ct_heat_rates` is LIVE and KEEPER-grade at MISO, and the prereg's own headline prediction is REFUTED: a class-average-cheaper re-price makes the class run **less**

Session miso-117, 2026-08-03, branch `claude/miso-117-measured-ct-heat-rates-nc5xme`,
off `origin/main` at `f6d9a4b`. Two full solves (arm A control, arm B
treatment), each `--year 2023 2024 2025` in ONE invocation, years sequential
inside it, chains run one at a time. Pre-registration
`results/calibration/PREREG-miso117-ct-heat-rates-2026-08-03.md` was written,
committed **and pushed** before either arm solved.

**KEEPER: `2026-08-03-miso-117b-ct-heat`** (bundle
`results/calibration/miso117_ctheatrate_B`), promoted under the owner's explicit
in-session instruction — *"If so plz promote. If structural integrity improves
but gates regress that may still be a keeper"* — which is an override of the
prereg's own promotion blocker (§7), recorded as such at §6 below and **not** a
re-reading of the prereg.

> ⚠️ **RULE 15 IS NOT SATISFIED AND THE REGISTRATION IS INCOMPLETE.** The
> dashboard run payloads (1.4 MB each) and the `hourly/` sidecars
> (0.63–0.79 MB each) could not be pushed: `git push` began refusing **every**
> pack with HTTP 413 mid-session — including a ~200-byte empty commit and a
> 60 KB thin pack, after ~11 MB of registration had been attempted — and
> `mcp__github__push_files` cannot carry a file over ~457 KB. See §8. **A
> successor must land those bytes before this keeper is quotable from the
> dashboard.**

---

## 0. Verdict

**The lever is `K` for MISO** — chartered on rule 14 `[R-ACCURATE]`, live at the
LP seam, and adopted with every criterion verdict unchanged. It is **not** a C7
`COAL_PRB` instrument and was never offered as one.

| | arm A control | arm B treatment |
|---|---|---|
| run id | `2026-08-03-miso-117a-control` | `2026-08-03-miso-117b-ct-heat` |
| determination | NOT-YET | NOT-YET |
| C1 fuel-mix | PASS (16/16, free 12/12) | PASS (16/16, free 12/12) |
| C2 / C3b / C4 / C6 / C8 | PASS | PASS |
| C3a mean LMP | CAVEAT [ledgered] −14.2 % (2025) | CAVEAT [ledgered] −14.1 % (2025) |
| C3c price tail | CAVEAT [ledgered] 1/6/0 h | CAVEAT [ledgered] 1/6/0 h (**bit-identical**) |
| C7 diurnal shape | FAIL `COAL_PRB` ×3 | FAIL `COAL_PRB` ×3 |

**No criterion verdict changes in either direction.** Ledgered-caveat budget
unchanged at 2/3 `{C3a, C3c}`.

## 1. What it replaces, and why it is admissible regardless of the residual

miso-115 §4 measured MISO's `CT_PEAKER` trough heat rate at **11.13 / 11.25 /
11.26 MMBtu/MWh gross** against the model's **12.37 net** — **+9.9…+11.1 % too
dear**, worth **$3.15 / $2.45 / $3.91 per MWh** at the keeper's own gas prices,
with a trough-selection control of +0.2…+0.5 % and a class-average control of
+0.6 %, and gross-vs-net making the true gap larger. miso-116 re-audited it and
it **survives intact** (unlike miso-115's two CHP results, which miso-116
withdrew). `ST_GAS` is already right, so the defect is CT-specific.

Arm B replaces eGRID's plant-average **annual** rate with MISO's own measured
per-plant CAMPD **loaded** rate on **86 plants / 19,120.7 MW = 85.8 % of
`CT_PEAKER` class capacity**, all 86 artifact rows `flag == "ok"` — **zero
excluded by the physical band**. The artifact was **not re-derived** (rule 23
`[R-FROZEN-DERIVE]`); it is the committed
`data/raw/_processed-legacy/campd_ct_heat_rates_MISO.csv` landed under PR #3217.

Rule 25 `[R-ISO-SCOPE]`: MISO's own artifact from MISO's own CAMPD data. The
NYISO / PJM / CAISO / NEISO `K` verdicts transfer nothing and no parameter is
imported from them.

## 2. Phase 0 — the wiring hazard, checked before a solve was spent

Under `use_campd_bins` **ERCOT** reads the curated sheet and this same flag is
byte-identically **inert** (ERCOT-146). Verified empirically for MISO
(`scripts/probes/_miso117_flag_fidelity.py`, the neiso-70 template), with **both
probe arms built from the keeper's own `run_config.json`** — the miso-116 §7
discipline, since the keeper arms `measured_chp_heat_rates` and a default-config
probe reads a different model than the keeper solved:

* 509 tranches moved of 2,740; **19,120.7 of 22,281.8 `CT_PEAKER` MW**.
* `classes touched == ['CT_PEAKER']` — no scope leak.
* Plant grain **12.3720 → 12.0351 MMBtu/MWh (−2.72 %)**, reproducing miso-115
  §4's published model value **12.37 exactly** — the check that the probe is
  keeper-matched.
* All three fleet vintages identical (the artifact is one pooled 2023–2025
  measurement).

## 3. The refuted prediction, and the statistic that explains it

**Prereg §5 prediction 1 said `CT_PEAKER` energy would RISE +0.2…+1.5 TWh in all
three years.** It **falls**:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `CT_PEAKER` A → B (TWh) | 15.468 → **14.235** | 19.838 → **18.828** | 19.088 → **17.862** |
| Δ | **−1.234** | **−1.010** | **−1.226** |
| actual | 17.038 | 19.225 | 19.291 |

**The explanation is in the artifact itself, and Phase 0 quoted the wrong
statistic.** The re-price is **capacity-weighted cheaper (−0.393 MMBtu/MWh)**
but **generation-weighted essentially neutral and slightly DEARER (+0.003)**:
56 plants / 13,801.1 MW got cheaper and 30 / 5,319.6 MW got dearer, and *the
cheap ones barely run*. **A class-average heat rate is the wrong statistic for a
dispatch prediction.** The Phase 0 write-up led with −2.72 % as though it
predicted direction; it does not, and that error is recorded here rather than
smoothed over.

Two more predictions fail, both reported:

* **Prediction 2** said C1 improves 2023 / worsens 2024. Both signs are wrong:
  2023 was 1.57 TWh **under** and worsens; 2024 was **+0.61 TWh over** and
  improves to −0.40 under.
* **Prediction 4** said λ moves **down**. It moves **up** (+0.065 / +0.059 /
  +0.020 $/MWh) — consistent with the generation-weighted read, ~0.2 %, and
  **not** offered as a C3a improvement.

Total generation is conserved (−0.014 / −0.002 / −0.001 TWh): the CT energy goes
to `CC_REGULAR`, imports, `COAL_PRB`, `CC_CHP` and `ST_GAS`. This is
reallocation, not a volume artifact.

## 4. Prediction 5 CONFIRMED — and it reproduces miso-107's independent number

miso-107 measured, on miso-106's arm, that arming this flag raised the h14-21
`reliability_floor × CT_PEAKER` limb's forced energy **1.188 → 1.743 TWh
(+47 %)**. Measured here independently:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| floored TWh A → B | 1.1819 → **1.7361** (+46.9 %) | 1.1968 → 1.6880 (+41.0 %) | 1.1814 → 1.6533 (+39.9 %) |
| D-2 share A → B | 0.1157 → **0.1407** | 0.0821 → 0.0999 | 0.0867 → 0.1043 |

**C8 PASSES outright** — every year stays under the 0.15 peaker cap, so the
rule-20 conditional-pass route was **not needed**. D-4 off-window binding is
**0.000 on every limb in both arms**. The limb was **not touched**, and per the
miso-106 keeper note it must not be.

**Basis note, so no successor reads two incomparable numbers as a
contradiction:** D-2's `class_total_twh` denominator is summed over the
**aligned plant subset** the floor reconstruction covers, not the whole class,
so it moves 10.2164 → 12.3420 TWh for `CT_PEAKER` while the **solved** class
dispatch moves 15.4683 → 14.2348 TWh the other way. Both are correct on their
own basis. On the solved-dispatch denominator the shares would be **0.122 /
0.090 / 0.093**, i.e. the gate as scored is the **conservative** reading.

## 5. What improves, and the cost — both reported, neither the justification

**Improves.** C7 `CT_PEAKER` off-peak CV ratio **0.981 / 0.836 / 0.799 → 1.219 /
0.917 / 1.042** — the repriced class's own diurnal amplitude moves toward the
actual in all three years, and 2025 clears the 0.50 bound by a much wider
margin. `profile_r` 0.972/0.971/0.985 → 0.973/0.971/0.986. C3a-2025 −14.2 →
−14.1 %. C3c bit-identical.

**The cost.** C7 `COAL_PRB` off-peak CV ratio **0.466 → 0.462, 0.475 → 0.474,
0.314 → 0.309** against a 0.50 bound — **the keeper's one failing criterion gets
marginally worse.** It FAILs in both arms in every year. Per rules 1
`[R-STRUCT]` / 14 `[R-ACCURATE]` the measured input is **not** reverted for it: a
worse residual on an accurate input is a discovered bug, never a reason to
restore an estimate.

## 6. Disposition — and the override, stated plainly

The prereg §7 made *"the keeper's own failing criterion, C7 `COAL_PRB`, getting
worse"* an explicit **promotion blocker**. That blocker **fired**. The promotion
is the **owner's explicit in-session override** of it (the ercot-150 disposition
pattern), on the stated ground that structural integrity improves even where a
gate regresses. The session's own recommendation, on the identification alone,
was YES; the prereg's bar was self-imposed and the owner is its authority.

Construction gates: **K1, K3, K4, K5 PASS.** **K2 passes on the prereg's
SCORECARD basis** — arm A reproduces the keeper's determination and all nine
criterion statuses. On the **strict-byte** basis arm A differs from the
committed miso-109b sidecars by up to **3,728.5 MW** on a class-hour; that
same-HEAD drift is **reported, not a kill** (both arms share it — which is
exactly why a same-HEAD control was solved), and its cause is **filed, not
guessed at**.

**Inter-arm HEAD disclosure:** arm A solved at `6c5848f`, arm B at `d3267fc`.
The only commit between them changes `replay_keeper.main()`'s post-solve
`meta.json` **date** rewrite — it runs after `solve_and_persist` returns and
touches nothing in `src/market_sim/` or the solve path. The arms are same-HEAD
for solve purposes.

## 7. Tool defect found and fixed en route

`replay_keeper._restore_display_date` exists so a byte-faithful **in-place**
replay keeps the keeper's dashboard id. Its predicate never tested `--out-dir`,
so a **zero-delta control** — which takes no `--set` and therefore satisfied
every other condition — inherited the keeper's date: solved 2026-08-03, stamped
**2026-07-31**, three days before its own treatment arm. One A/B, two dates.
Fixed by skipping the restore when `--out-dir` resolves elsewhere than the
replayed bundle; verified on all four cases (in-place and `--out-dir == bundle`
still restore, so id stability is preserved). **This behaviour applies to every
control arm produced this way**, so other ISOs' committed control bundles may
carry inherited dates — not touched from this lane (rule 25), but flagged.

Also fixed: `scripts/run_calibration_full.py --help` crashed on a pre-existing
argparse bug (three help strings carried a bare `%` argparse read as a format
spec). Escaped to `%%`; `--help` now renders 2,883 lines.

## 8. THE BLOCKER — transport, and what it means for rule 15

`git push` in this session refuses packs with **HTTP 413**, and the behaviour
changed **mid-session**:

* Early on, 413 fired **only when the push would CREATE the remote ref**. It is
  not a pack-size limit — a 58 KB thin pack and a ~200-byte empty-commit pack
  failed identically. Creating the branch with `mcp__github__create_branch`
  first and then pushing to the existing ref **worked**, and five commits landed
  that way (prereg, probes, scorer, the `--help` fix, the `replay_keeper` fix),
  each blob-verified per rule 27.
* After an ~11 MB registration push was attempted, **every** subsequent push
  fails with 413 — including a fresh empty commit and a 60 KB thin pack, after
  `git gc --prune=now`, with `http.postBuffer` forced low, and with an explicit
  refspec. Retries with exponential backoff do not recover it.

`mcp__github__push_files` caps at ~457 KB per payload, so it **cannot** carry
the 1.4 MB run payloads or the 0.63–0.79 MB `hourly/` parquets. **Consequence:
the two runs are registered locally but their payloads are not on the remote, so
they will not appear in the Run Explorer** (the sidecar-without-payload trap
documented in `docs/handoffs/dashboard-payload-push-gap-2026-07.md`). Rule 15 is
therefore **not** satisfied by this session, and the keeper promotion is not
quotable from the dashboard until a successor lands those bytes.

Everything needed to reproduce is committed: the prereg, both probes, the
scorer, and the exact `replay_keeper` commands (prereg §3).

## 9. What must NOT be done with this

* **Do NOT relax the h14-21 `CT_PEAKER` reliability-floor limb** to buy back C1
  volume (rules 1 / 14; barred by the miso-106 keeper note), and do **not**
  re-derive `min_stable_pct` against a residual (rule 23; rule 25).
* **Do NOT re-open** the `CC_CHP` volume or heat-rate questions (miso-116, both
  WITHDRAWN), the trough-quantity question for
  `CT_PEAKER`/`ST_GAS`/`CC_REGULAR` (miso-115, refused), or quote the
  `CT_CHP`/`ST_CHP` ratios (VOID on coverage).
* **Do NOT** arm `miso_cc_coal_rebalance`, re-license `miso_firm_import_floor`
  or `miso_pjm_lmp_import_pricing`, charter the seam hod mis-shape, or re-open
  the top-decile convexity deficit (miso-89, ledgered).
* The regulated-PRB self-commitment family stays **SPENT** (miso-111 `R`,
  miso-112 `R`, miso-113 `I`).
* **C7 `COAL_PRB` is NOT closed by this lever and no successor should expect it
  to be.** It still needs the overnight dispatch *distribution* WIDENED
  (miso-113), which is the data-blocked miso-78/79 congestion + sub-hourly-RT
  lane.

## 10. Rule duties

* **Rule 15** — **NOT SATISFIED**, §8. Both runs registered locally; payloads and
  hourly sidecars blocked by transport.
* **Rule 16** — both arms carry `[2023, 2024, 2025]` in one bundle each.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; MISO holds no
  `calibration-complete` marker, and no holdout year was solved, scored or read.
* **Rule 19 / 23 / 26** — one mechanism, no derive re-run, arming recorded in
  `run_config.json` in both channels.
* **Rule 21 `[R-DOF]`** — arm B's ledger gains one `measured-physical` row and
  zero residual rows (26 entries, still 2 residual).
* **Rule 28 duty (b)** — the `measured_ct_heat_rates` MISO cell must be stamped
  `U → K` with this finding as its citation. **BLOCKED by §8**
  (`mechanism-matrix.js` is 539 KB, over the `push_files` cap, and `git push` is
  down) — it is the successor's first action.
* **Contamination declared** — the session read miso-115, miso-116, the MISO log
  and the matrix before writing the prereg, so it was **not** blind to the
  expected direction. What was fixed in advance is the decision rule, the gates
  and the predictions — three of which the result **refuted**.
* Next number: **miso-118.**
