# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-07-12

### Added
- New CLI helper `hermes-stepfun-setup` (installed via `pip install
  hermes-stepfun-imagegen[setup]` or `[test]`). One-shot configures
  `~/.hermes/config.yaml`:
    - Adds `stepfun-imggen` and `image-gen-chain` to `plugins.enabled`
    - Writes the `image_gen` provider block (`provider: stepfun`,
      `stepfun.model: step-image-edit-2`)
    - Idempotent — re-running is a no-op
  - Flags: `--check` (exit-code-only status), `--print` / `--dry-run`,
    `--uninstall` (full reverse), `--json` (machine-readable output),
    `--provider {stepfun|image-gen-chain}` (which one to set as default),
    `--force-provider` (overwrite an already-set provider)
- New `[project.optional-dependencies]` extras: `setup` (PyYAML),
  `test` (pytest + PyYAML)
- New test file `tests/test_setup.py` with 17 tests covering entry-point
  declarations, setup/uninstall idempotence, --check exit codes, and
  plugin register() callback wiring for both `stepfun-imggen` and
  `image-gen-chain`
- README: installation instructions now lead with the
  `pip install + hermes-stepfun-setup` flow. Troubleshooting section
  explains why the entry-point key (`stepfun-imggen`) differs from the
  manual-install key (`image_gen/stepfun`).

### Fixed
- README previously told pip users to write `image_gen/stepfun` (the
  bundled-layout key) into `plugins.enabled`, which silently did NOT
  enable the pip-installed entry-point plugin (different key shape).
  `hermes-stepfun-setup` writes the correct key automatically.
- Existing pip-install users who followed the old README (writing
  `image_gen/stepfun` — the bundled-layout path-derived key) will see
  `hermes plugins list` show those plugins as "not enabled".
  `hermes-stepfun-setup` rewrites the enabled list to the correct
  entry-point names (`stepfun-imggen`, `image-gen-chain`). Manual-install
  users — who placed the package under `~/.hermes/plugins/image_gen/`
  per the manual-install section — already use the path-derived keys
  and are unaffected.
- Uninstall previously wiped the `stepfun:` sub-block even when the
  user's primary provider wasn't stepfun (e.g. `image_gen.provider:
  openai` with a leftover stepfun model block). Now it only clears
  fields we wrote.

## [0.2.2] - 2026-07-11

### Fixed
- TOML syntax error in `pyproject.toml`; chain plugin lint.

## [0.2.1] - 2026-07-11

### Changed
- Bumped version for PyPI release.

## [0.2.0] - 2026-07-11

### Added
- New fallback chain provider: `image-gen-chain`
  - Tries `stepfun` first, then `minimax`, then `pollinations`
  - Returns first successful result with `extra.chain` metadata
  - Enables automatic failover without extra user code

### Changed
- Package now ships `hermes_stepfun_imagegen.chain` alongside the main StepFun backend

## [0.1.1] - 2026-07-10

### Fixed
- **Billing path bug**: `STEPFUN_BASE_URL` default changed from
  `https://api.stepfun.com/v1` to `https://api.stepfun.com/step_plan/v1`.
  Step Plan subscribers using the previous default were being billed
  against their cash balance (per-image ¥ deduction) instead of against
  their subscription credit quota. Same key, different path, different
  meter. The `/step_plan/v1` endpoint is the one used by official
  Step Plan integrations (OpenClaw, Claude Code, Hermes). Override the
  env var to fall back to the open-platform endpoint if you want cash
  billing.

## [0.1.0] - 2026-07-10

### Added
- Initial release of `hermes-stepfun-imagegen`
- Support for `step-image-edit-2` model (text-to-image + image editing)
- Support for `step-2x-large` model (high-quality image-to-image)
- Support for `step-1x-medium` model (balanced quality/speed)
- Text-to-image generation via StepFun API
- Image editing via multipart upload
- Image-to-image transformation
- Configurable model selection via `config.yaml`
- Environment variable configuration (`STEPFUN_API_KEY`, `STEPFUN_BASE_URL`)
- Automatic image caching to local filesystem
- PyPI package distribution
- GitHub repository at https://github.com/lora-sys/hermes-stepfun-imagegen

[Unreleased]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/lora-sys/hermes-stepfun-imagegen/releases/tag/v0.1.0
