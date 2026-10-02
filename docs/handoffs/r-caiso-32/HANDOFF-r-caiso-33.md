SESSION R-CAISO-33 — CAISO: JOINT GAS RE-BASIS (link 15). SCOPING + PRECOMMIT first; no solve in the scoping session.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-32 (its session id is in your launch prompt) with mcp__claude-code-remote__archive_session,
  only once its PR (branch `claude/caiso-dmm-battery-soc-tnw2ww`) reads MERGED on the GitHub MCP. If it is not
  merged, do not archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main (`git cherry` shows "-"):
  `claude/r-caiso-31`, `claude/caiso-dmm-battery-soc-tnw2ww` (once merged). `claude/r-caiso-27/-29/-30` were
  already gone from the remote on 2026-10-02.
- Work on a fresh branch off origin/main.

STATE (2026-10-02):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
- R-CAISO-32 (zero LP; docs/records/caiso/r-caiso-32/FINDING-r-caiso-32-dmm-soc-outage-scoping-2026-10-02.md):
  the DMM SOC-outage series (2023 Fig 2.23, 2024 Fig 2.26; none for 2022/2025) is digitized from the PDF vectors
  (committed JSON). Admissible as a physical derate (rule 13) on the existing `storage_energy_cap` /
  `storage_soc_min` channels; reach ≤ $0.06/MWh annual mean on the keeper (pool reaches its ceiling 9–47 d/yr).
  CNOG already carries battery MW outages (14–21 % of fleet MW) that no solve consumes; the crosswalk has no
  battery rows and `caiso_storage_shape_anchor` absorbs fleet unavailability behaviourally (rule-19 conflict if
  stacked). Owner ruling (FINDING §7): CLOSE REPORT-ONLY; a battery-outage census is queued as link 17.

TASK — link 15 (owner-selected, R-CAISO-29 FINDING §1–§3): JOINT GAS RE-BASIS — SCOPING + PRECOMMIT.
- Re-identify `CAISO_CITYGATE_TRANSPORT_ADDER` against the base it rides on (the NGI CA composite, flow-dated;
  EIA N3045CA3 − composite ≈ 1.15–1.28 $/MMBtu 2023–25; the comparator is the GHG fuel region, never non-GHG)
  AND re-derive the measured offer-surface denominator (`derive_caiso_offer_surface.py`, caiso-242/244) on the
  same delivered basis, so the multipliers still round-trip to the measured bids. Moving the adder alone
  double-shifts every gas offer by ~$5–8/MWh. Rule 14 is the basis, never the residual (rule 1).
- C4 2025 gas NRMSE has zero margin (caiso-257): state the risk explicitly.
- Freeze the identification in a PRECOMMIT before any solve. A later full-span solve follows rules 32–36
  (one shard per year, shard prompts from an immutable SHA). End with a decision card.

QUEUED AFTER YOU (owner-selected). Carry into your end-of-session handoff:
- Link 16, R-CAISO-34: RUN EXPLORER STORAGE PANEL — display only (R-CAISO-31 FINDING §4). Render the
  `storage-soc-bounds` envelope (submitters' mean min/max share of ceiling by Pacific hour of day, plus the
  coverage share) next to the keeper's storage SOC on the Run Explorer storage panel. Read the committed
  extract data/raw/caiso-rtm-eoh-soc/ or the probe JSON (scripts/probes/_rcaiso31_eoh_soc_diagnostic.py); label
  it as a self-selected subset and never as a target. Optional: the R-CAISO-32 digitized SOC-outage shares
  (docs/records/caiso/r-caiso-32/dmm_soc_outage_digitized.json) may sit on the same panel as a quarterly
  reference band, labelled DMM, digitized (not selected by the owner, not refused). No solve, no ScenarioConfig
  field.
- Link 17, R-CAISO-35: BATTERY-OUTAGE CENSUS — zero LP (R-CAISO-32 FINDING §4, §7). Extend the CNOG resource
  crosswalk (data/raw/reference/caiso-resource-eia-crosswalk.csv, scripts/data/build_caiso_resource_crosswalk.py)
  to battery resources, then measure whether the `caiso_storage_shape_anchor` p95 envelope
  (data/raw/reference/caiso-storage-shape-envelope.csv) already carries the measured battery MW outages
  (14–21 % of fleet MW, scripts/probes/_rcaiso32_soc_derate_reach.py Part B): the rule-19 test. No consumer is
  proposed until that test is adjudicated. End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-32, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6,
the R-CAISO-26 PRECOMMIT §6, the R-CAISO-27 FINDING §4, the R-CAISO-28 FINDING §3, the R-CAISO-29 FINDING §3,
the R-CAISO-30 FINDING §5, the R-CAISO-31 FINDING §4 and the R-CAISO-32 FINDING §7.

NOTES:
- Fresh container: `pip install -e . pytest tzdata`, then `python3 scripts/hydrate_data.py --profile caiso`
  (a full clone reports "re-run with --force"; data is already present then).
- `git fetch origin main` can stall >2 min in a fresh container; run it in the background.
- Run `ruff format` as a separate command before any push. 4 unrelated tests in tests/unit/config fail on main.
- Shards can fail at start on the weekly limit. Relaunch once, then card the owner.
- Never `git grep` in a partial clone. Shards read long prompts from an immutable SHA (`git show <sha>:<path>`).
- `pkill -f <pattern>` matches your own shell's command line and kills it; use the PID.
- Never name a scratch script after a stdlib module.
- matplotlib and pdfplumber are not installed by default (`pip install matplotlib pdfplumber`).

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is scoping + PRECOMMIT, so expect none). PR + rebase-merge. Archive
  every shard and report leftover shard branches.
- Then launch R-CAISO-34 (link 16) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
