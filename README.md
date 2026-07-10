# Hermes StepFun ImageGen

StepFun image generation backend for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

Supports StepFun's image models:

- `step-image-edit-2` — recommended, fast text-to-image + image editing (1-2s)
- `step-2x-large` — high-quality text-to-image / image-to-image
- `step-1x-medium` — balanced quality and speed

## Demo

![Demo](docs/assets/demo-optimized.gif)

## Installation

### From PyPI

```bash
pip install hermes-stepfun-imagegen
```

### From source

```bash
git clone https://github.com/lora-sys/hermes-stepfun-imagegen.git
cd hermes-stepfun-imagegen
pip install -e .
```

### Manual install

Copy the plugin directory to your Hermes plugins folder:

```bash
cp -r src/hermes_stepfun_imagegen ~/.hermes/plugins/image_gen/stepfun
```

## Quick Start

### 1. Set your StepFun API key

Add to `~/.hermes/.env`:

```bash
STEPFUN_API_KEY=your-stepfun-api-key
```

### 2. Enable the plugin

Add to `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - image_gen/stepfun

image_gen:
  provider: stepfun
  model: step-image-edit-2
```

### 3. Restart Hermes

```bash
hermes gateway restart
```

## Usage

Once configured, just ask the Hermes model to generate images:

**Text-to-image:**
```
生成一张赛博朋克风格的龙
```

**Image editing:**
```
把这张图换成水墨画风格
```

**Image-to-image:**
```
把这张照片转成梵高风格
```

## Screenshots

### Text-to-Image Examples

**Prompt:** "A cute cat astronaut floating in space, digital art"
![Cat Astronaut](docs/assets/screenshot-cat.png)

**Prompt:** "A majestic dragon perched on a cyberpunk skyscraper at sunset"
![Cyberpunk Dragon](docs/assets/screenshot-dragon.png)

**Prompt:** "Traditional Chinese ink painting of mountains and rivers"
![Ink Mountains](docs/assets/screenshot-ink.png)

## Model Comparison

| Model | Speed | Quality | Best For | Edits Supported |
|-------|-------|---------|----------|-----------------|
| `step-image-edit-2` | ~1-2s | Good | Fast iteration, text-to-image, editing | ✅ Yes |
| `step-2x-large` | ~10-20s | High | High-quality output, image-to-image | ✅ Yes |
| `step-1x-medium` | ~10-20s | Medium | Balanced speed and quality | ✅ Yes |

### vs Other Hermes Image Plugins

| Feature | stepfun | openai | fal | krea |
|---------|---------|--------|-----|------|
| Model | step-image-edit-2 | gpt-image-2 | Flux / others | Krea models |
| Auth | API Key | API Key | API Key | API Key |
| Speed | 1-2s | 15s-2min | Varies | Varies |
| Editing | ✅ | ✅ | ✅ | ✅ |
| Image-to-image | ✅ | ✅ | ✅ | ✅ |
| Local-only | ❌ | ❌ | ❌ | ❌ |
| Cost | Paid | Paid | Paid | Paid |

## Model Selection

Change the default model in `config.yaml`:

```yaml
image_gen:
  provider: stepfun
  model: step-2x-large  # or step-1x-medium
```

Available models:

| Model ID | Display Name | Speed | Best For |
|----------|--------------|-------|----------|
| `step-image-edit-2` | Step Image Edit 2 | ~1-2s | Fast iteration, text-to-image + editing |
| `step-2x-large` | Step 2X Large | ~10-20s | High quality, image-to-image |
| `step-1x-medium` | Step 1X Medium | ~10-20s | Balanced quality and speed |

## Configuration Options

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STEPFUN_API_KEY` | Yes | Your StepFun API key from https://platform.stepfun.com |
| `STEPFUN_BASE_URL` | No | Override API base URL (default: `https://api.stepfun.com/step_plan/v1` for Step Plan subscribers) |

### Config.yaml Options

```yaml
image_gen:
  provider: stepfun
  model: step-image-edit-2  # default model
```

## API Reference

- StepFun 开放平台: https://platform.stepfun.com
- API 文档: https://platform.stepfun.com/docs/zh/api-reference/images/image
- Image generation: https://platform.stepfun.com/docs/zh/api-reference/images/image
- Image editing: https://platform.stepfun.com/docs/zh/api-reference/images/edits
- Image-to-image: https://platform.stepfun.com/docs/zh/api-reference/images/image2image

## Troubleshooting

### `STEPFUN_API_KEY not set`

Make sure you've added your API key to `~/.hermes/.env`:

```bash
STEPFUN_API_KEY=your-key-here
```

Then restart Hermes.

### Plugin not loading

Check that the plugin is enabled in `config.yaml`:

```yaml
plugins:
  enabled:
    - image_gen/stepfun
```

And verify the plugin directory exists:

```bash
ls ~/.hermes/plugins/image_gen/stepfun/
```

### Image generation fails

1. Check your API key is valid at https://platform.stepfun.com
2. Verify you have API credits available
3. Check the Hermes logs for error details:

```bash
tail -f ~/.hermes/logs/errors.log
```

### `405 Method Not Allowed` or connection errors

Make sure you're using the correct base URL. The plugin defaults to `https://api.stepfun.com/step_plan/v1` (Step Plan path — billable against your subscription credit, not your cash balance). If you need the legacy platform endpoint (billed per image, paid in cash), override:

```bash
export STEPFUN_BASE_URL=https://api.stepfun.com/v1
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

```bash
# Clone the repo
git clone https://github.com/lora-sys/hermes-stepfun-imagegen.git
cd hermes-stepfun-imagegen

# Install in editable mode
pip install -e .

# Run tests
python -m pytest tests/

# Build package
python -m build
```

## License

MIT

## Author

lora-sys

## Links

- GitHub: https://github.com/lora-sys/hermes-stepfun-imagegen
- PyPI: https://pypi.org/project/hermes-stepfun-imagegen/
- Issues: https://github.com/lora-sys/hermes-stepfun-imagegen/issues
- Hermes Agent: https://github.com/NousResearch/hermes-agent
