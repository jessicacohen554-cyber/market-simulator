### 2026-07-12 — CAISO — caiso-79 STEP-0 (Greater Bay LCT bind test): the NP15 → GREATER_BAY split REFUTED ex-ante — the measured import cap cannot bind; lane redirected to a measured local-commitment driver (design filed, NO solve)

The CT_PEAKER local-commitment granularity lane's STEP-0 gate (plan §3),
decided by measurement before any build
(`scripts/probes/_caiso79_step0_greaterbay_bind.py`, no LP):

- **Data completion (committed):** Greater Bay `peak_load` 11,136/11,081/
  11,992 MW (Final LCT Table 3.3-29/3.3-27 Load+Losses+Pumps) + NP26 zonal
  rows (Table 3.2-1) into `capacity-deliverability/caiso/caiso.csv`;
  Greater Bay membership (77 plants, 6,969 MW) into
  `lcr_area_membership_CAISO.csv` via `derive_lcr_membership.py` — county
  rule for the five core Bay counties + LCT §3.3.5.1 substation-rule
  overrides (**Moss Landing bus is IN the area**; Lambie SW Sta in — the
  Solano LM6000 trio). Existing LA Basin/SDGE rows byte-unchanged; Greater
  Bay is deliberately NOT registered as a `LocalCapacityAreaSpec`, so every
  solve-path consumer is untouched.
- **The gate:** `import_cap = peak_load − LCR` = 3,824/3,752/4,551 MW
  (34–38 % of pocket peak — between LA_BASIN's never-binding 61 % and
  SDGE's binding 30 %). Ex-ante bind test on measured hourly data (PGE-TAC /
  EIA-930 load share, CAMPD in-pocket supply, LCT At-Peak non-CEMS credits):
  with non-CT thermal at 93 % CAPACITY the residual needing CT is positive
  in **≤ 0.1 % of hours** in every year (2024 max +20 MW; without any
  battery credit 0.4 %, ≤ 1 GW) — while the real GB CTs are ON in
  **22–43 % of evening hours** (p90 402/309/87 MW) and even reality's own
  non-CT dispatch leaves a positive residual in only 1–11 % of them. The
  measured cap cannot move 3–4 TWh/yr of CT, cannot form the 2024/25 local
  C3c tail — and reality's CT commitment is demonstrably NOT
  energy-cap-driven: it is contingency positioning / local-RA commitment
  (RMR, exceptional dispatch), the caiso-71 §3 conclusion with the
  import-cap alternative now measured and eliminated. The caiso-78 model
  already serves the pocket with comparable local thermal (evening p50
  3,149/3,203/2,917 MW vs measured 3,325/2,866/2,318) — the miss is the
  MIX (model CC vs real CT starts), not the import share.
- **Fork taken (pre-registered):** do NOT build the split — an import wall
  tuned tight enough to force CT would be structurally unreal (rule 1).
  **No caiso-79 solve was run.** The lane redirects to a measured
  local-commitment driver on the pocket's named CT units — min-gen window
  HE15–23, driver = pocket net-load ramp via a CAMPD-fitted response curve
  (rule-13 construction, regenerates forward), D4_WINDOWS entry in the same
  PR, LOYO-scored, `ra_mustoffer_bridge` non-stacking — design filed for
  owner review BEFORE implementation:
  `docs/handoffs/caiso-local-commitment-driver-design-2026-07.md`.
  Sequencing: the honest-bench C3a/CC re-tune (plan §4) lands first; the
  driver sizes against whatever CT deficit survives it. Full evidence:
  `results/calibration/FINDING-caiso79-step0-greaterbay-bind-2026-07-12.md`.
