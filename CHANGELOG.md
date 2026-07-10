# Changelog

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

[Unreleased]: https://github.com/lora-sys/hermes-stepfun-imagegen/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/lora-sys/hermes-stepfun-imagegen/releases/tag/v0.1.0
