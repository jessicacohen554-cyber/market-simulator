# SPP Addition Desk — ledger (2026-09)

Canonical live state of the SPP addition program. Plan: `docs/multi-iso/spp-addition-plan-2026-09.md`.
Desk prompt: `docs/handoffs/spp-desk-handoff-2026-09-06.md`. **This ledger wins where the plan or the
handoff diverge on live state.** One `§0` entry per sitting, newest at top; amendments are appended to
the sitting's entry (`am.1`, `am.2`), never rewritten. Errors are recorded against interest in the entry
that finds them (§6).

---

## 0. Sittings (newest first)

### 0h. r#7 — sitting #7: FIRST SPP KEEPER LANDED (NOT-YET, owner direction); SPP-35 landed; SPP-41 unlaunched → v2; W4b repairs + SPP-57 issued (2026-09-07, main HEAD `8a4bfd29`)

- Pin `8a4bfd29` (109 commits since r#6). Branch fast-forwarded.
- **GRADED BY CONTENT.** **SPP-40 LANDED** (`claude/spp-40-first-solve-pvanrx`, PRs #5425 / #5434 /
  #5446 / #5447; `PRECOMMIT-spp-40` pushed at `45d02b0e` before the solve; `FINDING-spp-40-2026-09-07.md`).
  The rule-29(a) 2024 screen was **KILLED as pre-registered** on the direction leg — link live at bound
  1,776 h (20.3 %) but 877 N→S / 899 S→N, a 22-hour tie against a 1.7:1 N→S-dominant market; legs B/C/D
  passed. The owner then ruled in-session (**P14**, §2) and the full span was solved (369 s, 5.25 GB)
  and registered as the **FIRST SPP KEEPER `2026-09-07-spp-1-baseline`**, determination **NOT-YET** at
  full magnitude (C1 FAIL, C3a/C3b/C3c FAIL; C2/C4/C6/C8 PASS). DoD rows 1–5 MET. The tie was
  2024-specific (2023 1,702/275, 2025 1,245/373). Reported not tuned: |S−N| ~$1 vs $12–17; 7–9
  negative hours vs ~1,000; 0.0 % re-curtailment; CT over / CC+ST under; 2025 unserved 2,007 MWh.
  Registration surfaces verified at the pin: `keepers/SPP.json`, `index.json` (7), `status/SPP.js`,
  `bench/SPP/{2023,2024,2025}`, registry + 743 KB payload, `spp40_baseline_B/` + `hourly/`, shard
  stamped (`measured_interface_limits` U → O), log spp-1/spp-2, §5.7 header re-stamped. The lane also
  found and neutralised a **rule-25 breach** (SPP had inherited ERCOT-fitted COAL bands) BEFORE solving.
  **SPP-35 LANDED** (`claude/spp-35-seven-iso-prose-ypsq70`, PR #5440): S-1/S-2/O-4/O-6 closed; six
  leftovers routed (→ SPP-37). **SPP-41 NOT LAUNCHED** — no branch, no FINDING; the seam is untouched
  (`_screen_fuel_spikes` still only in the builder). Re-issued as **v2** (same stem) widened to the
  wind-INPUT path SPP-40 §4 found (the same h3907 slip reaches the delivered wind profile, +27 GWh).
- **GATES at the pin:** parity 0; gate-(a) 0; bench-freshness 0 (29 parts); goldens 0 (three
  pre-existing STALE notes, NEISO/ERCOT, not ours); matrix 0 (one anchor-digit warning, not ours);
  refactor-guards 0 (after `pip install numpy …` — the container had lost its deps; not a repo state);
  `audit_keepers --check` **EXIT 1 — S1 stale `status/ERCOT.js`, `status/PJM.js`** (MISO's cleared;
  PJM's new) — §3 R-s.
- **NO CARDS SERVED. Desk acts within P1 / P7 / P14 as ruled:** (1) SPP-40's R-1 (re-issue with a
  re-cut direction leg) is MOOT — the full span is the keeper and the 29(b) control. (2) The three
  score/input defects SPP-40 named are ZERO-DOF data repairs, so they are chartered as **W4b**:
  **SPP-36** coal supply class (`derive_coal_supply.py --iso SPP`, CLI verified by the desk against
  `--help`), **SPP-37** SPP-35's six leftovers, **SPP-42** the 2025 hydro vintage repair
  (`--hydro-backfill-year 2024`, the CAISO/PJM/MISO/NEISO precedent; matrix row
  `hydro_vintage_input_repair`) folded with ONE full-span re-baseline after SPP-36 + SPP-41, under a
  promotion rule declared in its PRECOMMIT (any ambiguity STOPs → card). (3) **SPP-57** issued in
  full — design now, solve after SPP-42 — with the STOP gate carrying **ex-ante dominance
  thresholds** (E-6). Promotion of any W5 candidate is a card (P15), never the lane's act.
- **Collision check (§4):** the MISO lane promoted `2026-09-07-miso-233-spp-hourly` (MISO's priced SPP
  seam, rule 25 — MISO's own); `git diff 7347933c..8a4bfd29` on `iso_configs.py` / `interchange/` /
  `spp_seam_*` is EMPTY, so no SPP object moved. Its bundle `miso233_sppseam_K` is MISO's.
- ISSUED: SPP-41 v2, SPP-36, SPP-37 (parallel, now); SPP-42 (after 36 + 41); SPP-57 (design now).
  Next sitting: grade all five; serve P15 if SPP-42 STOPs or SPP-57 reports a candidate; then SPP-51
  (Fable) and SPP-58 in ranked order.

### 0g. r#6 — sitting #6: W3 ALL LANDED; SPP-40 owner-launched; C4-2023 blocker relayed; SPP-41 + SPP-35 issued (2026-09-07, main HEAD `7347933c`)

- Pin `7347933c` (branch fast-forwarded from `9bdd0709`; the two newer merges are MISO/PJM lanes, no SPP
  touch). **Owner note: "spp 40 has launched."** No `claude/spp-40*` head is visible on origin at the
  pin, so per the standing line SPP-40 reads **RUNNING (owner-launched), branch unconfirmed**.
- **GRADED BY CONTENT — six lanes LANDED 2026-09-07:** SPP-30 (#5378), SPP-31 (#5389), SPP-32 (#5396 +
  #5399), SPP-33 (#5377), SPP-34 (#5388), SPP-53 (#5374/#5383/#5393). SPP-40's four preconditions
  verified at the pin: `_spp_config` link `ttc_mw = 3400.0` (not the 48,700 placeholder); outages
  `campd-unit-outages-SPP.csv` + siblings; `actual_lmp.json` / `calibration_reference.json` SPP
  blocks; clean zonal shares + wind shape + `meanzero.py` basis rows.
- **GATES at the pin:** parity 0 (16 runs / 49 dirs), gate-(a) 0, bench-freshness 0 (26 parts),
  goldens 0, refactor-guards 0, matrix 0 (7 shards). `audit_keepers --check` **EXIT 1 — S1: stale
  `status/ERCOT.js` and `status/MISO.js`**, neither this desk's (§3 R-k). `keepers/index.json` still
  six; no SPP bundle exists yet, as expected.
- **BLOCKER FOUND FOR SPP-40, relayed as an addendum, not a re-charter.** FINDING-spp-31 §3.3/§5a:
  the P9 `NG:` spike screen closed only inside `calibration_reference.json`; the C4 scoring path
  (`run_calibration_full._eia930_frame_generic` → `e930.parquet` → `bench/`) calls the loader
  unscreened, so SPP 2023's C4 would score wind against +3.5857 TWh (one hour, h3907). → **SPP-41
  chartered (Fable)**: move the screen into `load_eia_hourly_benchmark`, zero-LP two-series proof
  first (SPP 2023 wind, NYISO 2024 `other`), cache-key + bench-freshness consequence audit. SPP-40
  told to report C4-2023 as UNSCORED pending SPP-41; the desk re-renders bench/SPP/2023 afterwards
  (no re-solve — the LP never reads the benchmark).
- **SPP-35 chartered (Opus)**: SPP-34's S-1 (five stale "six ISOs" sentences in CLAUDE.md / spec /
  codebase README / user manual) + S-2 (ISO badge contrast, five of seven fail WCAG AA; the passing
  `.badge--iso-*` pattern already exists) + SPP-20's O-4 / O-6 doc items.
- **W5 reshaped from W3 evidence (no card needed — desk acts within P1/P13 as ruled):** SPP-51 is
  re-labelled **Fable** — SPP-33's R1 (anchor map) and R2 (`HH + gas_basis` heat-rate correction:
  10.09 / 10.23 / 16.78 vs the registered values) and the ERCOT 820-vs-±835 MW clip question are
  adjudications riding the same PR; **SPP-58** added (asymmetric pair 3,400 / 4,206 MW with a second
  ψ identification, after SPP-57); **SPP-59** reserved (SPP-32's R-3/R-4/R-5 consolidations — MISO
  files, held for the MISO lane's consent). SPP-33's R3 (`_HR_GAS_ELASTIC` global key) stays with
  the desk as a W5 card (§3 R-n) — it is forward-only and inert for the keeper.
- **CHARTER DEFECTS FOUND BY THE LANES, corrected here (§6 E-5):** `derive_cc_committed_pct.py` in
  the SPP-30 sequence (ERCOT-only legacy, would have overwritten ERCOT's file); `hubs.py` named as
  the SPP-32 basis home (it is `basis/meanzero.py`); the SPP-30 charter's "zero full-year fallbacks"
  gate was unachievable as written (every ISO carries `eia923_netzero` units) — the lane reported 9,
  itemised, inside the cross-ISO band, and the desk accepts that as the gate's intent.
- ISSUED: SPP-40 ADDENDUM (into the running session), SPP-41, SPP-35. Next sitting: grade all three;
  when SPP-40 lands verify `keepers/SPP.json`, `index.json`, `status/SPP.js`, `bench/SPP`, the shard
  stamp; after SPP-41 re-render + re-score C4-2023; then W5 in ranked order (SPP-57 → SPP-51 → SPP-58 …).

### 0f. r#5 — sitting #5: SPP IS REGISTERED; SPP-14/15/20 landed; P1 ranking applied; P13 ruled; W3 + SPP-53 issued (2026-09-07, main HEAD `96a6c4b3`, 01:35 UTC)

- Pin `96a6c4b3` (137 commits since r#4). Branch fast-forwarded. **Needs-registration line (E-4
  standing): SPP-20 has merged — nothing is gated on registration any more.**
- **GRADED BY CONTENT.** SPP-20 **LANDED** (PR #5329, `claude/spp-20-topology-market-design-1iew99`,
  `FINDING-spp-20-2026-09-06.md`): `SUPPORTED_ISOS` = 7; SPP-North 0.5125 / SPP-South 0.4875; voll 2000;
  PRM 0.16; TAIL 200; `SURFACE_ISOS` = 7; overrides `{}`; six keepers unmoved (0 moved surface rows,
  persisted identity 23/23, MISO keeper `fleet_only` hash-identical); 15 six-tuple tests extended, 3
  documented exclusions. **The N↔S link is a 48,700 MW PLACEHOLDER that cannot bind** (no public
  rating; SPP-20 §5 R-6) → card P13. Eight routed items (§3 R-i…R-p). SPP-14 **LANDED** (PRs #5335,
  #5341; two parallel sessions → an add/add collision on the FINDING, salvaged onto main by the owner's
  lane as `df5e8c3d` / `3cfb73bc`; both reports kept): `portal.spp.org` answered anonymously on
  2026-09-06 (the SPP-12/13 block did not reproduce; UA-independent); rows 5–9 ALL SERVED from SPP's own
  files; per-hub parquet promoted under the cross-check gate (sha256-identical system rebuild); hourly
  \|N−S\| mean/p90: **2024 widest on both legs, both markets** (RT mean 17.23 vs 12.13 / 15.18; p90 41.4
  vs 28.5 / 36.2) → **P7 stands on the hourly measure**; the four-group table served (below); RTBM
  effective limits exist only from 2026-01-28 (§5.4). SPP-15 **LANDED** (PR #5333): 12 back-year CEMS
  parquets, 4 sub-BA files, interchange widened 2019–2025 with the 2023–25 slice byte-identical, gas
  back years; blocked table EMPTY.
- **P1 RANKING APPLIED (desk act under the ruled test, no card).** `oklahoma_internal` 0.603 / 0.681 /
  0.648 of hours at $188 / $229 / $331 mean \|shadow\| ≥ `n_s_corridor` 0.555 / 0.516 / 0.631 at $140 /
  $194 / $227 ≫ `sps_tie` 0.258 / 0.342 / 0.282 at $52 / $70 / $59 (2023 / 2024 / 2025). The SPS tie
  never reaches the N↔S share → **SPP-57 outranks SPP-54**; SPP-54 stays queued behind it.
- **CARD P13 RULED** (§2): SPP-53 pulled from W5 into W3 as SPP-40's fourth precondition — a Fable
  derive lane reconciling the 2026→ corridor-flowgate effective limits into one link TTC under rule
  14's misalignment clause, construction declared in a PRECOMMIT before any limit is read.
- **ISSUED: SPP-30, SPP-31, SPP-32, SPP-33, SPP-34, SPP-53** (six parallel lanes; the W3 charters carry
  "RULINGS APPLIED (r#5)" blocks assigning SPP-20's and SPP-14's routed items: R-2 → SPP-32, R-3/R-4/R-5/
  R-8 → SPP-34, R-7 → SPP-33, the `_validation-source/README.md` row → SPP-31, R-6 → SPP-53).
- Gates at the pin: audit_keepers 0 · parity 0 (15 runs / 48 dirs — the owner's MISO lane pruned) ·
  bench 0 (25 parts) · goldens 0 · refactor-guards 0 (the SPP allowlist entry is gone) · matrix validate
  0 · **`check_gate_a_provenance` EXIT 1, now MISO** (`gate.a_keeper_marker` cites superseded
  `miso-230-ctdrag-seam`) — capx Q34 duty, §3 R-e updated. `keepers/index.json` still six — correct
  until SPP-40 registers.
- Standing note from the SPP-14 collision: **one charter = one session.** A charter pasted into two
  sessions produces two FINDINGs at one path and a salvage merge; the desk asks the owner before
  re-issuing anything that might already be running (§0 rule 3 already says so — restated because it
  cost a salvage).

### 0e. r#4 — sitting #4: SPP-13 and SPP-21 landed, SPP-20 running, P12 ruled, SPP-14 chartered (2026-09-06, main HEAD `5a20cec1`, 23:01 UTC)

- Pin `5a20cec1` (61 commits since r#3; the r#3 desk commit merged as PR #5291). Branch fast-forwarded.
- **GRADED BY CONTENT.** SPP-13 **LANDED** (PR #5314, `claude/spp-13-portal-ftp-ttc-h2vk-h9c6q8`,
  `FINDING-spp-13-2026-09-06.md`): the public-data route is **anonymous FTP** (`pubftp.spp.org`, user
  `anonymous`, password = email — no token, no login) and is blocked ONLY by the session egress (port
  21 not relayed; controls `ftp.gnu.org` / `ftp.debian.org` fail identically). Every product's FTP
  folder + file grammar recorded; real product schemas verified from the v35 sample zip (BC 14 columns
  incl. `Real Time Effective Limit`; hourly load by control zone = the EIA-930 sub-BA tokens); gen-mix
  2024-02-15 → 2025-12-16 and monthly peak load LANDED. Row 11 (N↔S rating): **swept, NOT PUBLIC** —
  it lives in the ITP Constraint Assessment NDA/CEII workbook (`SPPSPSTIES`, `SPSNMTIES` tabs), so
  SPP-20's Tier-3 estimate is the ruled path and the RTBM `Real Time Effective Limit` (row 8) is the
  measured substitute for SPP-53. Per-hub spread and four-group tables: NOT OBTAINABLE; P7 stands.
  SPP-21 **LANDED** (PR #5304, `claude/spp-21-matrix-shard-ti2gy3`, `FINDING-spp-21-2026-09-06.md`):
  seventh shard, 305 cells (162 `U` / 47 fc-only `U` / 96 `.`), guard exit 0, 33/33 matrix tests,
  7 columns render; no verdict minted anywhere; the lane also touched the two matrix test files
  (out of its charter region, recorded by the lane as owner-authorized) — noted, not adjudicated.
  SPP-20: no branch/commit → asked; owner: "Running on another branch" → RUNNING; its six target
  files have had ZERO writes since the r#3 pin (a quiet window).
- **CARD P12 RULED** (§2): "Try to find the data somewhere else" → **SPP-14 chartered** (Opus;
  gridstatus.io hosted API, the `gridstatus` package's endpoints, EnergyOnline, spp.org CDN hosts,
  Kaggle/Zenodo mirrors, MMU monthly tables; a rule-14 cross-check gate against the committed
  system-hub parquet before any landed series is used). W3/W4 never wait on it.
- Gates at the pin: ALL 0 — audit_keepers, parity (17 runs / 50 dirs), gate-(a) (re-keyed since r#3),
  bench, goldens, refactor-guards, matrix validate.
- ISSUED: SPP-14. Nothing else newly issuable — W3 waits on SPP-20.

**r#4 am.1** (owner: *"Is that really all that can run"*). Checked rather than asserted: every W3
derive — `derive_campd_unit_outages`, `derive_thermal_tranches`, `derive_actual_lmp`,
`build_calibration_reference`, `curate_zonal_shares`, `build_miso_wind_shape` — calls
`get_iso_config("SPP")`, so W3 is gated by registration itself (SPP-20), not by this desk; SPP-34's
`iso-topologies.json` likewise. Two things need NO registration and were not yet issued:
**SPP-15** (back-year intake 2019–2022 of the SPP-11 products — rule 22 data prep, no marker; the
owner's dispatch is the `--holdout-intake SPP` authorization) and an **SPP-14 addendum** (the three
measured files in SPP's v35 zip: `SL_to_Pnode_to_Zone_with_Area.csv`, `Hub_Definitions.csv`,
`TieFlows_Sep2025.csv`, HTTPS-reachable). Considered and NOT chartered: a NASA-POWER pre-pull for
the wind shape — the builder keeps no raw cache, so it would mean editing the MISO builder for a
network pull that is minutes long; and SPP-34's prose half — it would advertise seven ISOs before
the registration exists. Both issued; recorded against interest that r#4 called W3's gate "SPP-20"
without having measured which scripts impose it (§6 E-4).

### 0d. r#3 — sitting #3: SPP-12 landed, G12 met, P10/P11 ruled, SPP-13 chartered, SPP-20 issued (2026-09-06, main HEAD `992760ec`, 22:20 UTC)

- Pin `992760ec` (54 commits since r#2; the r#2 desk commit merged as PR #5273). Branch fast-forwarded.
- **GRADED BY CONTENT.** SPP-12 **LANDED** (PR #5285, `claude/spp-12-fetch-portal-x9cn-6atxy2`,
  `FINDING-spp-12-2026-09-06.md`). Served: planning PDFs (PRM, VRLs, offer cap, ITP report), the ASOM
  hub-spread series (2024 confirmed the widest year on BOTH published measures → P7 stands), wind
  curtailment as MW, the LTLF (`2025 ITP`, vintage 2025, four peak rows) — **G12 MET**, and the NRC
  addendum (Wolf Creek 2045; **Cooper 2034-01-18, SLR under review — inside the horizon**). Blocked:
  portal rows 5–9 — **not an API move but an `X-SPP-UI-Token` requirement** (discriminating probe: a
  real fsName returns `200 []`, an invented one 404); row 11 (N↔S TTC) **not found** in the ITP
  report. **The SPP-54/57 ranking has no measured input** — the binding-constraint archive is behind
  the token. SPP-12 fixed the four-group spec in `spp-binding-constraints/README.md` before any data
  (rule 1). SPP-21: no branch/commit → asked; owner: "Running on another branch" → RUNNING.
- **TWO CORRECTIONS TO THE PLAN from SPP-12** (recorded §6 E-3): PRM is 16 % East summer (v5.0A),
  the plan's 15 % was PY2023–25; SPP's posted energy offer cap is $1,000 (Order 831 hard ceiling
  $2,000). Both now carried in the SPP-20 charter.
- **CARDS P10, P11 RULED** (§2): voll $2,000 (cost-verified ceiling, both numbers cited); SPP-13
  chartered (FTP public-data route + ITP Manual sweep for the N↔S capability), W2 proceeds in parallel,
  SPP-20 registers the N↔S TTC Tier-3 with the misalignment documented if SPP-13 has not landed.
- **ISSUED: SPP-20** (the pin flip — P1–P11 ruled, G12 met; charter carries r#2 + r#3 "RULINGS
  APPLIED" blocks and the live-writer collision list) and **SPP-13** (new, plan §8).
- Gates at the pin: audit_keepers 0 · parity 0 (16 runs / 49 dirs) · bench 0 · goldens 0 ·
  refactor-guards 0 · matrix validate 0 · **`check_gate_a_provenance` EXIT 1 again, now CAISO**
  (`gate.a_keeper_marker` cites superseded `2026-09-06-caiso-257-b1-ctonly`) — capx Q34 duty,
  ROUTED (§3 R-e updated).
- Matrix files: base last written 21:34 UTC, shards 22:14 UTC (SCN-WS5A-RESOLVE) — continuous; SPP-21
  (running) rebases before its single commit per charter.

### 0c. r#2 — sitting #2: W1 graded, cards P1–P9 ruled, SPP-21 issued (2026-09-06, main HEAD `a6e4b6db`, 21:50 UTC)

- Owner said "Refresh". Pin: `origin/main` `a6e4b6db` (111 commits since r#1's pin, incl. the
  charter's own merge; the D79 solve-surface fingerprint; four keeper promotions — NEISO neiso-105,
  MISO, CAISO, NYISO; the SCN desk's r#16). Branch fast-forwarded to it.
- **GRADED BY CONTENT.** SPP-10 **LANDED** (PR #5254, `claude/spp-10-miso-audit-wowrmp`): the
  814-line audit + doc 00/01 corrections; census 103.3 GW / 828 plants reconciles to SPP's MMU at
  +0.5 % / −2.8 %; registry-values table §5 (22 rows) is what SPP-20 executes. SPP-11 **LANDED**
  (PRs #5239 / #5243 / #5247, `claude/spp-11-fetch-epa-eia-xs70mz`): all four items GOT, blocked
  table EMPTY, 16 CEMS parquets schema-verified, 17 sub-BAs = 0.9995–0.9999 of BA demand, 11 DIBAs.
  SPP-12: no commit, no branch → **asked, not graded LOST**; owner: "It is running on another
  branch" → RUNNING, branch to be recorded when it lands.
- **CARDS P1–P9 SERVED AND RULED** (§2, verbatim). P9 is NEW — raised by the audit §3.4 (three
  defective EIA-930 SWPP hours). The plan §3 ruling column is filled; charters SPP-20 / SPP-31 /
  SPP-40 carry "RULINGS APPLIED" blocks; W5 gains SPP-57 (Oklahoma pocket) ranked against SPP-54.
- **ISSUED: SPP-21** (matrix shard) — the r#1 hold is lifted: the base file's last write was
  21:34 UTC (miso PJM seam ladder), shards 21:37 (nyiso-207); writers are continuous, so the
  charter's "rebase immediately before your single commit" is the protocol, not a hold.
  **ISSUED: SPP-12 ADDENDUM** (paste into the running session): NRC licence intake (routed back by
  SPP-11), the Oklahoma-internal flowgate group, explicit P7 confirmation.
- **STILL BLOCKED: SPP-20** on G12 alone (LTLF edition/vintage — SPP-12's row 13). P1–P9 no longer
  block it. **New atomicity item** recorded in plan §2.3: `config/solve_surface.py::SURFACE_ISOS`
  (D79) must gain SPP in the same commit as `_ISO_BUILDERS`, with `--diff` showing zero moved rows
  for the six ISOs.
- Gates at the pin: `audit_keepers --check` 0 · parity 0 (15 runs / 48 dirs) · bench-freshness 0 ·
  golden-manifest 0 · refactor-guards 0 · matrix (validate mode) 0 with the two pre-existing anchor
  warnings · **`check_gate_a_provenance` EXIT 1** — NEISO's `gate.a_keeper_marker` cites the
  superseded keeper `neiso-99-joint-p1`; the current keeper is `2026-09-06-neiso-105-fossil-offer`.
  That is the capx director's standing Q34 re-key duty, not this desk's → ROUTED (§3 R-e).
- Errors against interest recorded in §6 (two).

### 0b. r#1 — first sitting, W1 issued (2026-09-06, main HEAD `b22b91c3`; charter commit `45055ba0` on `claude/spp-iso-model-plan-pf6ygd`)

- Owner instruction, verbatim: *"Commit the plan and then you turn into the desk and issue wave 1."*
  The charter commit was pushed and blob-verified (plan 808 lines, handoff 177 lines — local and
  origin sha256 MATCH; `git diff HEAD origin/<branch>` empty).
- Gates run at the pin, all exit 0: `audit_keepers --check`, `check_registry_payload_parity`
  (15 runs / 48 bundle dirs), `check_gate_a_provenance` (6 rows), `check_bench_freshness` (24 parts,
  0 stale), `check_golden_manifest`, `ci_refactor_guards`, `check_mechanism_matrix --base origin/main`
  (two PRE-EXISTING anchor warnings on `entry_lookahead_reprice` / `startup_co2_reporting`, not this
  desk's — routed, not repaired).
- **ISSUED: SPP-10, SPP-11, SPP-12** (plan §8 W1, verbatim; stems in §5). Three parallel Opus lanes,
  DATA PROFILE shared, disjoint files. Dispatch is unconfirmed until a branch exists.
- **HELD: SPP-21** (the early-issue option). The matrix base file
  `docs/codebase-site/data/mechanism-matrix.js` was last written by capx D78-R2 at 18:36 UTC, 30 min
  before this pin, and the shards by nyiso-204b at 18:26 — active writers. SPP-21 is issued at
  sitting #2 beside SPP-20 after a fresh collision check (§4 hold recorded).
- Cards: none served (P1–P8 are due at sitting #2 with W1's evidence — ruling O-1).
- Nothing else moved. No src/, scripts/, configs/, tests/ or frontend/ file touched by this desk.

### 0a. r#0 — charter (2026-09-06, main HEAD `b22b91c3`)

- Program chartered by the owner in session `claude/spp-iso-model-plan-pf6ygd`. Three owner answers
  taken at charter and recorded as O-1…O-3 (§2).
- Verified state recorded in the plan §2: SPP is NOT registered (six-ISO pin in five places); SWPP
  EIA-930 hourly + hub LMP actuals 2023–2025 already on disk; CEMS missing for OK NE NM WY; portal.spp.org
  file-browser API moved (listings `[]`, downloads 404 on this date); `spp` token collides with ERCOT's
  `DAMLZHBSPP_*` zips; `docs/multi-iso/00` §0/§3 falsely claim SPP registered.
- Wave graph W1–W6 and charters W1–W4 committed to the plan §8; W5 reserved; W6 routed (P8).
- Gates at charter: not run by this session (docs-only charter; nothing under `src/` touched) —
  recorded UNREAD. The r#1 sitting runs them.
- Nothing dispatched. Dispatch is unconfirmed until a branch exists.

---

## 1. Lane scoreboard

Status vocabulary: CHARTERED · ISSUED · RUNNING · LANDED · KILLED · HELD · ROUTED.

| Lane | Wave | Model | Profile | Status | Branch realised | PR | FINDING |
|---|---|---|---|---|---|---|---|
| SPP-10 audit + doc 00 fix | W1 | Opus | shared | **LANDED 2026-09-06** | `claude/spp-10-miso-audit-wowrmp` (session-assigned; stem was `claude/spp-10-audit-k7wq`) | — | `FINDING-spp-10-2026-09-06.md` → `docs/multi-iso/spp-data-audit.md` |
| SPP-11 EPA CAMPD + EIA fetch | W1 | Opus | shared | **LANDED 2026-09-06** — all four §6 items 1–4 GOT, blocked table EMPTY | `claude/spp-11-fetch-epa-eia-xs70mz` (stem issued `…-m3rd`; branch set by the session's own directive) | — | `docs/handoffs/FINDING-spp-11-2026-09-06.md` |
| SPP-12 portal.spp.org + spp.org fetch | W1 | Opus | shared | **LANDED 2026-09-06** — rows 10–14 + NRC served; rows 5–9 token-blocked; row 11 not found; addendum (A)(B-spec)(C) honoured | `claude/spp-12-fetch-portal-x9cn-6atxy2` | #5285 | `docs/handoffs/FINDING-spp-12-2026-09-06.md` |
| SPP-13 portal FTP route + N↔S TTC (P11) | W2 | Opus | shared | **LANDED 2026-09-06** — FTP route documented (anonymous; egress-blocked on port 21); row 11 NOT PUBLIC (NDA/CEII); gen-mix + monthly peak landed | `claude/spp-13-portal-ftp-ttc-h2vk-h9c6q8` | #5314 | `docs/handoffs/FINDING-spp-13-2026-09-06.md` |
| SPP-14 alt HTTPS sources for rows 5–9 (P12) | W2 | Opus | shared | **LANDED 2026-09-06** — rows 5–9 ALL served from SPP's own portal (open anonymously that day); per-hub parquet promoted (gate PASS); four-group table served; addendum (A)(B)(C) landed | `claude/spp-14-alt-sources-w6dp` + `-i49r3m` (two parallel sessions; salvaged `df5e8c3d`, `3cfb73bc`) | #5335, #5341 | `FINDING-spp-14-2026-09-06.md` + `-session-b.md` |
| SPP-15 back-year intake 2019–2022 (rule-22 data prep) | W2∥ | Opus | shared | **LANDED 2026-09-06** — all four items GOT, blocked table EMPTY; producers unmodified; interchange widened with the 2023-2025 slice proven byte-identical (268,177 rows, sha256 `243889469b96…`, before and after); nothing solved/scored/registered and no marker claimed. Four source defects reported and routed, not filled — incl. **`N3045OK3` publishes nothing 2015-2021** (OK gas exists for only 3 of the 7 years 2019-2025) and two impossible `AECI` prints that sign-flip SWPP's 2020 system net | `claude/spp-15-backyears-intake-0cah85` (stem issued `…-q3nf`; branch set by the session's own directive) | — | `docs/handoffs/FINDING-spp-15-2026-09-06.md` |
| SPP-20 register (pin flip) | W2 | Fable | shared→spp | **LANDED 2026-09-06** — SPP registered; six keepers unmoved; N↔S link a 48,700 MW placeholder (→ P13 / SPP-53); 8 routed items assigned r#5 | `claude/spp-20-topology-market-design-1iew99` | #5329 | `docs/handoffs/FINDING-spp-20-2026-09-06.md` |
| SPP-21 matrix shard + §5.7 | W2 | Opus | code | **LANDED 2026-09-06** — seventh shard live (305 cells: 162 `U` / 47 fc-only `U` / 96 `.`), `check_mechanism_matrix.py` exit 0 on 7 shards, 33/33 matrix tests pass, page renders 7 columns. **TWO out-of-region edits, both owner-authorized in session:** (1) 4 six-ISO assertions in `tests/unit/config/test_mechanism_matrix_{shard_migration,keeper_stamp}.py` (the charter budgeted one); (2) a one-line repair to `mechanism-matrix-assemble.js` for a PRE-EXISTING anchor mismatch that had left the rendered page blank since the 2026-08-11 sharding | `claude/spp-21-matrix-shard-ti2gy3` (stem issued `…-r4tq`; branch set by the session's own directive) | — | `docs/handoffs/FINDING-spp-21-2026-09-06.md` |
| SPP-30 outages + tranches | W3 | Opus | spp | **LANDED 2026-09-07** — G4 PASS (OK 1060 / NE 358 windows); 9 itemised full-year fallbacks; `derive_cc_committed_pct` dropped (E-5) | `claude/spp-30-outages-tranches-l2mdug` (stem `claude/spp-30-outages-tranches-b8kt`) | #5378 | `docs/handoffs/FINDING-spp-30-2026-09-07.md` |
| SPP-31 benchmarks | W3 | Opus | spp | **LANDED 2026-09-07** — SPP blocks in every shared JSON, others byte-identical; P9 closed in the builder; **§5a C4-path gap → SPP-41** | `claude/spp-31-benchmarks-calibration-klpemi` (stem `claude/spp-31-benchmarks-n2vw`) | #5389 | `docs/handoffs/FINDING-spp-31-2026-09-07.md` |
| SPP-32 zonal + wind shape + gas hub | W3 | Opus | spp | **LANDED 2026-09-07** — all gates PASS; six keepers unmoved; basis 2022–24 in `meanzero.py`; R-3/4/5 → SPP-59 | `claude/spp-32-zonal-wind-gas-tmuwui` (stem `claude/spp-32-zonal-wind-gas-r7ql`) | #5396, #5399 | `docs/handoffs/FINDING-spp-32-2026-09-07.md` |
| SPP-33 seam derive | W3 | Opus | spp | **LANDED 2026-09-07** — `hr_by_year` for SPP-51; R1/R2 → SPP-51 (Fable), R3 → desk | `claude/spp-33-seam-derive-ezmktp` (stem `claude/spp-33-seam-derive-c4hm`) | #5377 | `docs/handoffs/FINDING-spp-33-2026-09-07.md` |
| SPP-34 site + docs | W3 | Opus | code | **LANDED 2026-09-07** — S-1/S-2 → SPP-35; S-3 evidence job open; S-4 → audit | `claude/spp-34-site-docs-hjykvj` (stem `claude/spp-34-site-docs-t9xe`) | #5388 | `docs/handoffs/FINDING-spp-34-2026-09-07.md` |
| SPP-40 first solve → first keeper | W4 | Fable | spp | **LANDED 2026-09-07 — FIRST SPP KEEPER `2026-09-07-spp-1-baseline`, NOT-YET (P14 owner direction over the pre-registered 2024 screen kill); the 29(b) control for every later SPP lane; R-1…R-8 assigned r#7** | `claude/spp-40-first-solve-pvanrx` | #5425, #5434, #5446, #5447 | `docs/handoffs/FINDING-spp-40-2026-09-07.md` (+ PRECOMMIT) |
| SPP-41 EIA-930 spike screen → loader seam (SPP-31 §5a + SPP-40 §4 wind input) | W4b | Fable | code | **ISSUED r#6 — NOT LAUNCHED; RE-ISSUED v2 r#7** | — (stem `claude/spp-41-fuel-spike-seam-k2mr`) | — | — |
| SPP-35 seven-ISO prose + badge contrast (S-1/S-2, O-4/O-6) | W4∥ | Opus | code | **LANDED 2026-09-07** — all four closed; six leftovers R-1…R-6 → SPP-37 (R-3 routed) | `claude/spp-35-seven-iso-prose-ypsq70` (stem `…-v8jd`) | #5440 | `docs/handoffs/FINDING-spp-35-2026-09-07.md` |
| SPP-36 coal supply class (SPP-40 R-7) | W4b | Opus | spp | **ISSUED r#7** | — (stem `claude/spp-36-coal-supply-class-t3kp`) | — | — |
| SPP-37 SPP-35's six leftovers | W4b | Opus | code | **ISSUED r#7** | — (stem `claude/spp-37-leftovers-q7hn`) | — | — |
| SPP-42 hydro-2025 repair + re-baseline → keeper-2 candidate (SPP-40 R-8) | W4b | Opus | spp | **ISSUED r#7** · preconditions SPP-36 + SPP-41 | — (stem `claude/spp-42-hydro-rebaseline-w8nd`) | — | — |
| SPP-57 Oklahoma pocket (P1 first lever) | W5 | Fable | spp | **ISSUED r#7** · design now, solve after SPP-42; promotion = card P15 | — (stem `claude/spp-57-oklahoma-pocket-m4rt`) | — | — |
| SPP-53 N↔S TTC derive (P13 — W5 → W3) | W3 | Fable | spp | **LANDED 2026-09-07** — `ttc_mw` 48,700 → **3,400 MW** (FCITC, ex-ante construction); S→N set 4,206 → SPP-58 | `claude/spp-53-ttc-link-limit-67e3yf` (stem `claude/spp-53-ns-ttc-f6dz`) | #5374, #5383, #5393 | `docs/handoffs/FINDING-spp-53-2026-09-07.md` |
| SPP-51 (→ Fable r#6), 52, 54, 55, 56, 58 (new r#6), 59 (reserved r#6) levers | W5 | per plan §8 | spp | RESERVED · blocked on SPP-40 · **P1 ranking APPLIED r#5: SPP-57 (Oklahoma pocket) before SPP-54 (SPS pocket)** | — | — | — |
| SPP-60 forecast entry | W6 | Fable | spp | ROUTED to capx director (P8) | — | — | — |

---

## 2. Owner rulings (verbatim, numbered)

| # | Date | Question | Ruling (verbatim) | Where it binds |
|---|---|---|---|---|
| O-1 | 2026-09-06 | SPP topology for the first backcast: how many zones? | "Let the Phase-0 data audit decide" | plan §3 card P1 (served at sitting #2 with W1 evidence); no default topology in any charter |
| O-2 | 2026-09-06 | Where should the SPP desk sit relative to the existing directors? | "Standalone SPP desk (Recommended)" | this desk; rulings namespace P; collision register §4 |
| O-3 | 2026-09-06 | Data you cannot fetch from a session — how should the plan handle it? | "The plan should include sessions that fetch the data" | plan §6 (every row is a fetch lane first: SPP-11, SPP-12); manual upload only on a documented block |
| P1 | 2026-09-06 r#2 | topology for the W2 registration | "2 zones now; two ranked levers (Recommended)" | SPP-20 registers SPP-North/SPP-South; SPP-54 (SPS pocket) and SPP-57 (Oklahoma pocket) both pre-declared, ranked by SPP-12's per-flowgate binding share + shadow price vs the N↔S corridor |
| P2 | 2026-09-06 r#2 | SPP's MISO seam given MISO prices SPP from its side | "Served schedule first, priced seam default-off (Recommended)" | `_SCALAR_INTERCHANGE_ISOS` += SPP; `NeighborInterface("MISO")` + `("AECI")` default-off; SPP-51 validates |
| P3 | 2026-09-06 r#2 | ERCOT DC ties | ACCEPTED: "ERCOT DC ties as a default-off neighbour, 820 MW" | SPP-20 |
| P4 | 2026-09-06 r#2 | reserves | ACCEPTED: "defer reserve co-optimisation (M2 last)" | SPP-56 last; cells `U` |
| P5 | 2026-09-06 r#2 | scarcity seed | ACCEPTED: "no scarcity/ORDC seed at registration" | `voll=2000`; SPP-55 later; `test_iso_config` checkpoint untouched |
| P6 | 2026-09-06 r#2 | `TAIL_THRESHOLD["SPP"]` | "$200 (Recommended)" | three files, SPP-20; SPP-31 regenerates |
| P7 | 2026-09-06 r#2 | first-solve screen | "Control = none; screen 2024, structural STOP gate only (Recommended)" | SPP-40 PRECOMMIT; SPP-12's hourly per-hub number overrides 2024 if it disagrees |
| P8 | 2026-09-06 r#2 | W6 forecast entry | "Route to the capx director after a keeper exists (Recommended)" | SPP-60 never chartered by this desk |
| P10 | 2026-09-06 r#3 | `voll` after SPP-12's correction (posted cap $1,000; Order 831 hard ceiling $2,000) | "$2,000 — the cost-verified ceiling (Recommended)" | SPP-20 registers 2000.0 with both numbers cited; SPP-55 revisits against the VRLs |
| P11 | 2026-09-06 r#3 | unblocking portal rows 5–9 + the N↔S TTC | "Charter SPP-13 probe lane; W2 proceeds in parallel (Recommended)" | SPP-13 chartered (FTP route, ITP Manual sweep); SPP-20 registers the N↔S TTC Tier-3 with misalignment documented if SPP-13 has not landed; SPP-54/57 ranking waits for the flowgate archive |
| P12 | 2026-09-06 r#4 | rows 5–9 after SPP-13 (anonymous FTP, egress-blocked; row 11 NDA-only) | "Try to find the data somewhere else" | SPP-14 chartered (HTTPS third-party / mirror sweep with a rule-14 cross-check gate); W3/W4 proceed regardless; row 11 stays Tier-3 in SPP-20 |
| P1 (applied) | 2026-09-07 r#5 | the SPP-54 vs SPP-57 ranking under P1's own test | — (desk act; SPP-14 §5.2 measured `oklahoma_internal` ≥ `n_s_corridor` ≫ `sps_tie` in all three years on both legs) | SPP-57 first; SPP-54 does not clear "SPS-tie share ≥ N↔S share" and stays queued |
| P13 | 2026-09-07 r#5 | the N↔S TTC for the first keeper (SPP-20's 48,700 MW placeholder cannot bind) | "Pull SPP-53 into W3 as SPP-40's precondition (Recommended)" | SPP-53 issued (Fable derive, PRECOMMIT-first construction, rule 14 misalignment documented); SPP-40's preconditions now SPP-30/31/32/53 — **EXECUTED 2026-09-07 (SPP-53): 3,400 MW** |
| P14 | 2026-09-07 (given IN the SPP-40 session, recorded r#7) | the 2024 screen killed on a 22-h direction tie — is the baseline a keeper candidate? | "Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper." | the full span was solved and `2026-09-07-spp-1-baseline` promoted as the FIRST SPP KEEPER at NOT-YET; STANDING for W5: a candidate that improves structure may be promoted even if gates regress — but promotion is served as a card (P15…), never a lane's act |
| P9 | 2026-09-06 r#2 | EIA-930 SWPP defective hours (audit §3.4) | "Benchmark-side fix in SPP-31; demand-side routed (Recommended)" | SPP-31 screens `NG:` columns in the benchmark builder; low-side demand screen → audit track (§3 R-f); SPP-40 PRECOMMIT names the hours |

---

## 3. Routed / open, not this desk's to fix

| # | Item | Owner | Why it is here |
|---|---|---|---|
| R-a | W6 forecast-program entry for SPP (T1-F, `program-status.json`, `GOLDEN_ISOS`) | capx director (after card P8) | this desk never writes `frontend/data/forecast/` |
| R-b | `complete` marker for SPP holdout years | owner (rule 22) | manifest row 15 deferred; no out-of-training solve chartered |
| R-c | MISO's own SPP seam constants | MISO calibration lane | rule 25; SPP-20 adds SPP's blocks only |
| R-d | rule-28(c) CI enforcement gap | audit track | inherited consequence: read checker output, not exit code |
| R-e | `check_gate_a_provenance` EXIT 1 at r#2 (NEISO), r#3 (CAISO), r#5 (**MISO**: cites superseded `miso-230-ctdrag-seam`) `gate.a_keeper_marker` cites superseded `2026-09-06-caiso-257-b1-ctonly` | capx director (standing Q34 re-key duty) | seen at this desk's pin; not this desk's file |
| R-h | Row 11 — the N↔S transfer capability / SPS tie ratings exist only in SPP's ITP Constraint Assessment NDA/CEII workbook (`SPPSPSTIES`, `SPSNMTIES`), FINDING-spp-13 §4 | owner (an NDA read is an owner act, never a lane's) | SPP-20 registers Tier-3 with the misalignment documented; SPP-53 uses the RTBM `Real Time Effective Limit` as the measured substitute once row 8 lands |
| R-i | **D79 declared-hash ledger has no new-ISO-row limb** (FINDING-spp-20 §5 R-1): `check_cache_key_registration.py` check 6 treats a by-ISO entry as one string, so appending SPP's row is an "edit" breach and `--declare` refuses already-declared names → SPP's 17 new surface rows are UNDECLARED (they stay out of SPP's own cache key) | capx director (D79 owner) — wanted before SPP-40 registers, so SPP's first bundle's key sees its rows | the six ISOs are unaffected; SPP's key is incomplete until the limb exists |
| R-j | The 2026-01-28→ 14-column daily RTBM BC files are a forward-looking measured limit series (FINDING-spp-14 §5.4) | SPP-53 (now chartered) | its reduced corridor sidecar is SPP-53's deliverable |
| R-g | Cooper Nuclear (801 MW, NE) licence expires **2034-01-18** with its SLR under review; Wolf Creek 2045 with intent only — an SPP forecast assuming both firm through 2050 assumes an outcome the instrument record does not yet support (FINDING-spp-12 §7) | forecast lane / capx director, at W6 | recorded so SPP-60's charter carries it; no backcast consequence |
| R-f | low-side EIA-930 demand dropout screen (`_screen_demand_dropouts` catches only exactly-0.0; SWPP 2025-06-21 05:00 = 1,505 MW and 2024-07-19 00:00 escape) — repo-wide, cache-key risk | audit track (ruling P9) | SPP-40's PRECOMMIT names the hours as known artifacts; no SPP lane adds a screen parameter |

| R-k | `audit_keepers --check` S1: `status/ERCOT.js` and `status/MISO.js` stale against their keeper shards at pin `7347933c` | the ERCOT / MISO promoting lanes (rule 22 D-5(b) re-key duty) or capx | seen at this desk's pin; not this desk's files |
| R-l | CAISO `calibration_reference.json` renewables block predates the 2026-09-05 EIA-860 `vintage_2024` intake (FINDING-spp-31 §4a); three CAISO test files red on `main` (FINDING-spp-32 §8) | CAISO calibration lane | pre-existing, proven at HEAD without SPP code |
| R-m | 63 non-SPP registry rows regenerated by SPP-34's R-3, 35 still `needs-citation` (FINDING-spp-34 S-4) | audit track (rule 5 citations) | not an SPP object |
| R-n | `_HR_GAS_ELASTIC` global name key blocks SPP↔MISO forward elasticity (FINDING-spp-33 R3; PJM owns `"MISO"`) | SPP-DESK — a W5 card, forward-only, inert for the backcast keeper | a keying change in `neighbor_price.py` is mechanism-shaped; not SPP-51's one lever |
| R-o | SPP-30's `derive_cc_committed_pct.py` has no `argparse` and silently ignores `--iso` (would overwrite ERCOT's file) | ERCOT lane / audit — a guard (refuse `--iso ≠ ERCOT`) or deletion (rule 26, superseded by `derive_thermal_tranches`) | not run for SPP; recorded so nobody else does |
| R-p | SPP-35 R-3: `generate_parameter_registry.py` cannot express an `iso_configs` value (the O-6 code half) | registry owner / audit track | not an SPP object |
| R-q | SPP-40 R-6: gas split CT 1.78× / CC 0.85× / ST 0.78× with coal −4…−11 TWh — a commitment-physics question (rule 18) | SPP-DESK — W5 queue entry after SPP-57/51/58; never a band | mechanism-shaped; needs its own lever lane |
| R-r | FINDING-spp-53 §6 O-1/O-2 (asymmetric pair 3,400 / 4,206; identification width 2,645–11,121 MW) — SPP-40 §7.2 shows S→N live at the symmetric rating | SPP-58 (chartered r#6) | queued after SPP-57 |
| R-s | `audit_keepers --check` S1: `status/ERCOT.js`, `status/PJM.js` stale at pin `8a4bfd29` | ERCOT / PJM promoting lanes | not this desk's files |
| R-t | Three pre-existing STALE goldens (NEISO perfb-campd ×2 vs live `neiso-106`; ERCOT perfb-campd-ercot-after, provenance pruned) | NEISO / ERCOT lanes | reported by `check_golden_manifest` at the pin, exit 0 |

---

## 4. Collision register (verify at every sitting against the capx and SCN ledgers' top entries)

| Surface | Live writers at charter | SPP lane | Protocol |
|---|---|---|---|
| `config/capacity_market.py` adequacy / entry / storage dicts | capx D75-R landed 17:11 UTC; D76 / D78 / D81 LIVE (capx r#52) | SPP-20 | append SPP as the LAST entry of each dict, rebase last; HOLD if a capx lane holds the same dict mid-PR |
| `config/constants.py` `DEMAND_GROWTH_RATES(+_VINTAGES)`, `DATACENTER_ADDITIONS_MW`, `ELECTRIFICATION_LAYERS`, `VOLUNTARY_BASELINE_ISO_WEIGHT` | SCN desk (load re-derivation, voluntary dict); capx D67 lane (PJM rate) | SPP-20 | append-last; SPP-20 declares the constant families it adds |
| `model/interchange/spec.py` | miso-231 seam ladder landed 21:34 UTC; miso-232 LIVE | SPP-20 (new `"SPP"` blocks only), SPP-51 | region-disjoint; append after the MISO blocks; rebase last |
| `data/renewables.py`, `data/fuel/hubs.py` | any live per-ISO calibration lane | SPP-32 | named regions; G-DRIFT classification of every hunk in the FINDING |
| `frontend/data/backcast/tail/actual_tail.json`, `amplitude/actual_amplitude.json`, `completeness/` | holdout-intake lanes | SPP-31 | regenerate as the LAST commit after rebase; non-SPP diff = ∅ |
| `docs/codebase-site/data/mechanism-matrix.js` + shards | every lane, several times a day | SPP-21 (7th shard), SPP-40 (stamp), every W3+ lane (cell lines) | one commit; last after rebase; 7 shards from SPP-21 on |
| `scripts/ci_refactor_guards.py` allowlist | audit Y-lanes | SPP-20 | delete-only edit; cite Y-21 |
| `frontend/data/backcast/keepers/index.json`, `status/*.js` | keeper promotions | SPP-40 | per-ISO shards are conflict-free; `index.json` is one line, rebase last |
| `frontend/data/forecast/program-status.json`, `ff-verdicts.json`, goldens, `GOLDEN_ISOS` | capx director's sole writer | none until W6 | ROUTE, never charter |
| `results/cache.py`, `ScenarioConfig` fields | capx D77/D79 (cache fingerprint) | none | never touched by any SPP lane through W4 (plan §7 G8) |
| Per-plant solve slots | capx / SCN campaigns, per-ISO calibration lanes | SPP-40, SPP-5x | advisory: confirm no other per-plant solve before the SPP leg (rule 12, ≤ 2 concurrent) |
| r#7 | MISO lane keeper `2026-09-07-miso-233-spp-hourly` (bundle `miso233_sppseam_K`) — MISO's priced SPP seam, rule 25 | VERIFIED no SPP object moved (`iso_configs.py`, `interchange/`, `spp_seam_*` diff empty 7347933c..8a4bfd29); SPP-51 will read MISO's seam constants but never edit them |

Holds recorded: **r#1 — SPP-21 held** (LIFTED r#2 — writers on the matrix files are continuous, so the charter's rebase-immediately-before-commit line is the protocol); `mechanism-matrix.js` last written by capx D78-R2 (`8e68a471`, 18:36 UTC) and the shards by nyiso-204b (`330e3cac`, 18:26 UTC) within the hour before the pin. Re-check at sitting #2.

---

## 5. Issuance record

| Sitting | Lane | Stem issued | Branch realised | Charter location | Note |
|---|---|---|---|---|---|
| r#1 | SPP-10 | `claude/spp-10-audit-k7wq` | — | plan §8 W1 · SPP-10 | issued verbatim |
| r#1 | SPP-11 | `claude/spp-11-fetch-epa-eia-m3rd` | — | plan §8 W1 · SPP-11 | issued verbatim |
| r#1 | SPP-12 | `claude/spp-12-fetch-portal-x9cn` | unknown — owner confirms RUNNING r#2 | plan §8 W1 · SPP-12 | issued verbatim |
| r#2 | SPP-12 addendum | (into the running session) | — | plan §8 W1 · SPP-12 ADDENDUM | NRC intake + Oklahoma flowgate group + P7 confirm |
| r#2 | SPP-21 | `claude/spp-21-matrix-shard-r4tq` | unknown — owner confirms RUNNING r#3 | plan §8 W2 · SPP-21 | issued verbatim |
| r#3 | SPP-13 | `claude/spp-13-portal-ftp-ttc-h2vk` | — | plan §8 W2 · SPP-13 | new charter under P11 |
| r#3 | SPP-20 | `claude/spp-20-register-p8nz` | unknown — owner confirms RUNNING r#4 | plan §8 W2 · SPP-20 (+ r#2/r#3 RULINGS APPLIED) | issued verbatim |
| r#3 | SPP-13 | `claude/spp-13-portal-ftp-ttc-h2vk` | `claude/spp-13-portal-ftp-ttc-h2vk-h9c6q8` | plan §8 W2 · SPP-13 | LANDED #5314 |
| r#4 | SPP-14 | `claude/spp-14-alt-sources-w6dp` | — | plan §8 W2 · SPP-14 | new charter under P12 |
| r#4 am.1 | SPP-14 addendum | (into the SPP-14 session) | — | plan §8 · SPP-14 ADDENDUM | three v35-zip measured files |
| r#4 am.1 | SPP-15 | `claude/spp-15-backyears-q3nf` | `claude/spp-15-backyears-intake-0cah85` | plan §8 · SPP-15 | LANDED #5333 |
| r#5 | SPP-30 | `claude/spp-30-outages-tranches-b8kt` | — | plan §8 W3 · SPP-30 (+ r#5 block) | issued |
| r#5 | SPP-31 | `claude/spp-31-benchmarks-n2vw` | — | plan §8 W3 · SPP-31 (+ r#2/r#5 blocks) | issued |
| r#5 | SPP-32 | `claude/spp-32-zonal-wind-gas-r7ql` | — | plan §8 W3 · SPP-32 (+ r#5 block) | issued |
| r#5 | SPP-33 | `claude/spp-33-seam-derive-c4hm` | — | plan §8 W3 · SPP-33 (+ r#5 block) | issued |
| r#5 | SPP-34 | `claude/spp-34-site-docs-t9xe` | — | plan §8 W3 · SPP-34 (+ r#5 block) | issued |
| r#5 | SPP-53 | `claude/spp-53-ns-ttc-f6dz` | — | plan §8 · SPP-53 (new, P13) | issued |
| r#6 | SPP-40 addendum | (into the running SPP-40 session, owner-launched) | — | plan §8 · SPP-40 ADDENDUM | six facts; C4-2023 unquotable until SPP-41 |
| r#6 | SPP-41 | `claude/spp-41-fuel-spike-seam-k2mr` | — | plan §8 · SPP-41 (new) | issued |
| r#6 | SPP-35 | `claude/spp-35-seven-iso-prose-v8jd` | — | plan §8 · SPP-35 (new) | issued |
| r#7 | SPP-41 v2 | `claude/spp-41-fuel-spike-seam-k2mr` | — | plan §8 W4b · SPP-41 v2 | v1 never launched; re-issued whole |
| r#7 | SPP-36 | `claude/spp-36-coal-supply-class-t3kp` | — | plan §8 W4b · SPP-36 | issued |
| r#7 | SPP-37 | `claude/spp-37-leftovers-q7hn` | — | plan §8 W4b · SPP-37 | issued |
| r#7 | SPP-42 | `claude/spp-42-hydro-rebaseline-w8nd` | — | plan §8 W4b · SPP-42 | issued; launch after SPP-36 + SPP-41 land |
| r#7 | SPP-57 | `claude/spp-57-oklahoma-pocket-m4rt` | — | plan §8 W5 · SPP-57 | issued; design now, solve after SPP-42 |

---

## 6. Errors against interest

| # | Sitting | Error | Consequence | Correction |
|---|---|---|---|---|
| E-1 | r#0 charter (found r#2) | The plan listed **WY** among SPP's missing CEMS states. No EIA-860 plant with BA `SWPP` is in Wyoming (audit §2.4); the plan also omitted **CO** from the footprint. | SPP-11 fetched four inert `WY_*` parquets on the charter's word (harmless: the loader filters to the ISO's fleet). | Plan §2.1 corrected r#2; `ISO_STATES["SPP"]` in the SPP-20 charter now follows audit row 21 (WY out, CO in). |
| E-4 | r#4 (found r#4 am.1) | The r#4 entry stated "W3 waits on SPP-20" and "nothing else newly issuable" without measuring which scripts impose the gate or listing what needs no registration. The owner asked. | Two issuable lanes (SPP-15, the SPP-14 addendum) were a sitting late. | Measured (`get_iso_config` in every W3 derive) and recorded; from r#5 every sitting's §0 entry carries a "what needs no registration / what does" line until SPP-20 merges. |
| E-3 | r#0/r#2 (found r#3) | The plan carried **PRM 15 %** (manifest row 12) and card P5 cited "$2,000 — FERC 831 offer cap" as if it were SPP's posted cap. SPP-12's transcriptions: the live East BAA Base PRM is **16 %** (v5.0A; 15 % was PY2023–25), and SPP's posted Safety-Net Energy Offer Cap is **$1,000** ($2,000 is the Order 831 hard ceiling). The r#2 addendum also cited audit §6.1 to a lane that read it before SPP-10 had merged. | P5's value survives on a different justification (card P10); the PRM row now carries the live vintage with the history cited. | Plan §3 and the SPP-20 charter corrected r#3; the desk cites only landed files in addenda from now on. |
| E-2 | r#2 | The desk ran `git merge --ff-only origin/main` on its branch while the harness was in plan mode (read-only). | None — a fast-forward with no local commits; nothing lost or rewritten. | Recorded because the mode was explicit; the desk does not repeat state changes under plan mode. |
| E-5 | r#5 charters (found r#6) | Three charter defects the W3 lanes had to catch: (i) SPP-30's sequence named `derive_cc_committed_pct.py --iso SPP` — the script has no `argparse`, is ERCOT-only and would have overwritten ERCOT's committed file; (ii) SPP-32 named `data/fuel/hubs.py` as the basis home — the SPP rows belong in `basis/meanzero.py`; (iii) SPP-30's gate read "ZERO full-year fallbacks" — unachievable, every ISO carries `eia923_netzero` units (MISO 135, PJM 95 …). | None landed wrong: SPP-30 refused the script on a scratch proof and reported 9 itemised fallbacks; SPP-32 wired the right file. The desk had asserted the sequence and the gate from docstrings it had not run. | Plan §5/§8 corrected this sitting; standing note: a charter's RUN line is verified against `--help` output, not a docstring, before issuance. |
| E-6 | r#5/r#6 charters (found r#7) | The SPP-40 STOP gate was chartered as "link binds in the measured direction" with no dominance threshold, so the lane operationalised it as a strict inequality and a 22-hour (0.25 %) tie killed a screen whose every sign-based reading agreed with the market; the owner had to direct the full span (P14). | One extra owner intervention; no wrong number landed — the screen record stands unedited and the keeper is the honest baseline. | Standing rule from r#7: every direction/sign leg in an SPP STOP gate states an ex-ante dominance threshold (e.g. ≥ 55 % of at-bound hours) and a minimum liveness (≥ 5 % of hours); written into SPP-57's charter. |
