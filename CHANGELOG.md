# Changelog

## [0.2.0] - 2026-07-11

### Added
- New fallback chain provider: `image-gen-chain`
  - Tries `stepfun` first, then `minimax`, then `pollinations`
  - Returns first successful result with `extra.chain` metadata
  - Enables automatic failover without extra user code

### Changed
- Package now ships `hermes_stepfun_imagegen.chain` alongside the main StepFun backend

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI workflow with automated testing and PyPI publishing
- Unit tests with pytest
- CONTRIBUTING.md with development guidelines
- Demo GIF showcasing plugin capabilities
- Plugin comparison table in README
- Troubleshooting section in README

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

### Documentation
- Comprehensive README with installation, configuration, and usage examples
- API reference links to StepFun documentation
- Model comparison tables
- Troubleshooting guide

[Unreleased]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/lora-sys/hermes-stepfun-imagegen/releases/tag/v0.1.0
