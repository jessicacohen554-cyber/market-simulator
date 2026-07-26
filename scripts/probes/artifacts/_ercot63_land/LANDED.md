# ERCOT-63 landing record

- Session patch (code + docs + probes + tests + attestation): sha256
  8ab23ec3063cf60cbaa3b4b4415e3d68d97535fe8ac685b3fadf85feccf14b87,
  applied + solved + registered by `.github/workflows/ercot63-bridge-solve-register.yml`
  (run 29205996200), merged to main via PR #2152.
- Docs-sync patch (CLAUDE.md / model-methodology-spec.md / CHANGELOG.md): sha256
  e0297fc838f89676e172413142afd74b664ebeab27370a3c1638241e2485c5b8,
  applied by `.github/workflows/ercot63-docs-sync.yml` (run 29208412639),
  merged via PR #2157.
- Registered runs: `2026-07-12-ercot63-gas-bridge` (CALIBRATED-WITH-CAVEATS,
  one ledgered caveat — C3c-2024 inherited byte-identical; C5c-2024
  storage-shape FAIL flips to PASS) + `2026-07-12-ercot63-gas-bridge-ablation`
  (zero-forcing twin, linked).
- KEEPER PROMOTION (owner approval 2026-07-13, interactive sign-off): patch
  sha256 65b0784a4fd2885efd856064c93737b685383a05114ca0d968a903612e5f2b62,
  executed by `.github/workflows/ercot63-keeper-promotion.yml` — keepers.json
  ERCOT -> `2026-07-12-ercot63-gas-bridge` (supersedes ercot59-storage-deploy),
  attestation owner-stamped + DOF free_parameters ledger seeded (E8),
  keeper-auditor-repaired sidecar text, calibration-log promotion entry,
  ercot59 pair deregistered (standing keeper-and-later prune; bundle dirs
  retained), status.js rebuilt; `audit_keepers.py --iso ERCOT` PASS on the
  runner.
- Frontier status: NOT declared — ERCOT-64 lever chartered (floor-scoped LSL
  markdown, diagnosis §7); C3c scarcity-tail remains the separate ledgered
  open root-cause item.
