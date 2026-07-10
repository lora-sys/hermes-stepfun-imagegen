# Hermes StepFun ImageGen

StepFun image generation backend for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

Supports StepFun's image models:

- `step-image-edit-2` — recommended, fast text-to-image + image editing (1-2s)
- `step-2x-large` — high-quality text-to-image / image-to-image
- `step-1x-medium` — balanced quality and speed

## Installation

### From PyPI (once published)

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

## Configuration

### 1. Set your StepFun API key

Add to `~/.hermes/.env`:

```bash
STEPFUN_API_KEY=your-stepfun-api-key
```

Or export it in your shell:

```bash
export STEPFUN_API_KEY=your-stepfun-api-key
```

### 2. Enable the plugin

Add to `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - image_gen/stepfun

image_gen:
  provider: stepfun
  model: step-image-edit-2  # optional, defaults to step-image-edit-2
```

### 3. Restart Hermes

```bash
hermes gateway restart
```

Or restart the Hermes desktop app.

## Usage

Once configured, the Hermes model can call `image_generate` directly:

**Text-to-image:**
```
生成一张赛博朋克风格的龙
```

**Image editing:**
```
把这张图换成水墨画风格
```
(with an image URL or file)

**Image-to-image:**
```
把这张照片转成梵高风格
```

## Model Selection

Change the default model in `config.yaml`:

```yaml
image_gen:
  provider: stepfun
  model: step-2x-large  # or step-1x-medium
```

Available models:

| Model | Speed | Best for |
|-------|-------|----------|
| `step-image-edit-2` | ~1-2s | Fast iteration, text-to-image + editing |
| `step-2x-large` | ~10-20s | High quality, image-to-image |
| `step-1x-medium` | ~10-20s | Balanced quality and speed |

## Examples

### Text-to-Image

```python
from hermes_tools import image_generate

result = image_generate(
    prompt="A majestic dragon perched on a cyberpunk skyscraper at sunset",
    aspect_ratio="square",
    model="step-image-edit-2",
    steps=8,
    seed=42
)
```

### Image Editing

```python
result = image_generate(
    prompt="Convert to watercolor painting style",
    image_url="https://example.com/photo.jpg",
    model="step-image-edit-2",
    steps=8
)
```

### Image-to-Image

```python
result = image_generate(
    prompt="Transform into Van Gogh's Starry Night style",
    image_url="https://example.com/photo.jpg",
    model="step-2x-large",
    source_weight=0.7
)
```

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

Make sure you're using the correct base URL. The plugin defaults to `https://api.stepfun.com/v1`. If you need to override:

```bash
export STEPFUN_BASE_URL=https://api.stepfun.com/v1
```

## API Reference

- StepFun 开放平台: https://platform.stepfun.com
- API 文档: https://platform.stepfun.com/docs/zh/api-reference/images/image
- Image generation: https://platform.stepfun.com/docs/zh/api-reference/images/image
- Image editing: https://platform.stepfun.com/docs/zh/api-reference/images/edits
- Image-to-image: https://platform.stepfun.com/docs/zh/api-reference/images/image2image

## Development

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

# Upload to PyPI
twine upload dist/*
```

## License

MIT

## Author

lora-sys

## Links

- GitHub: https://github.com/lora-sys/hermes-stepfun-imagegen
- Issues: https://github.com/lora-sys/hermes-stepfun-imagegen/issues
- Hermes Agent: https://github.com/NousResearch/hermes-agent
