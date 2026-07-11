# Hermes StepFun ImageGen

[![PyPI](https://img.shields.io/pypi/v/hermes-stepfun-imagegen)](https://pypi.org/project/hermes-stepfun-imagegen/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)


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

## Fallback Chain

This package also ships a built-in fallback chain provider: `image-gen-chain`.

Priority:

1. `stepfun` — use this plugin first
2. `minimax` — fall back if StepFun is unavailable
3. `pollinations` — free anonymous fallback when the paid backends are not configured or fail

### Why use the chain?

- You keep StepFun as the default quality tier.
- You still get outputs when StepFun is down, quota is exhausted, or the API key is missing.
- The free Pollinations backend removes the single point of failure without requiring another paid account.

### Setup

```yaml
plugins:
  enabled:
    - stepfun-imggen
    - image-gen-chain

image_gen:
  provider: image-gen-chain
  model: step-image-edit-2
```

No extra env vars are required for the free Pollinations tier. Keep `STEPFUN_API_KEY` set for the first hop.

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

## Fallback Chain Usage

The bundled `image-gen-chain` provider tries backends in order and returns the first successful result.

Supported fallback order:

1. `stepfun`
2. `minimax`
3. `pollinations`

### Example config

```yaml
plugins:
  enabled:
    - stepfun-imggen
    - image-gen-chain

image_gen:
  provider: image-gen-chain
  model: step-image-edit-2
```

### Behavior notes

- The chain only falls back on provider errors, auth issues, or missing credentials.
- Successful generations include `extra.chain.tried` and `extra.chain.succeeded` in the tool result.
- Pollinations is used as the last resort because it is free but slower and lower fidelity than StepFun or MiniMax.

## Model Comparison

| Model | Speed | Quality | Best For | Edits Supported |
|-------|-------|---------|----------|-----------------|
| `step-image-edit-2` | ~1-2s | Good | Fast iteration, text-to-image, editing | ✅ Yes |
| `step-2x-large` | ~10-20s | High | High-quality output, image-to-image | ✅ Yes |
| `step-1x-medium` | ~10-20s | Medium | Balanced speed and quality | ✅ Yes |

### vs Other Hermes Image Plugins

| Feature | stepfun | openai | fal | krea | chain |
|---------|---------|--------|-----|------|-------|
| Model | step-image-edit-2 | gpt-image-2 | Flux / others | Krea models | stepfun -> minimax -> pollinations |
| Auth | API Key | API Key | API Key | API Key | mixed; last hop is free |
| Speed | 1-2s | 15s-2min | Varies | Varies | varies by hop |
| Editing | ✅ | ✅ | ✅ | ✅ | ✅ when available |
| Image-to-image | ✅ | ✅ | ✅ | ✅ | ✅ when available |
| Local-only | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cost | Paid | Paid | Paid | Paid | paid + free fallback |

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

### My usage is billing my cash balance, not my Step Plan credit

**Symptom:** you see image-edit calls on the [StepFun "账户余额" page](https://platform.stepfun.com/user-center/billing) (deducted ¥ per call) and the "Step Plan Credit 用量" page does not increment the way you expect.

**Cause:** the plugin is calling the **open-platform endpoint** `https://api.stepfun.com/v1/...`, which bills every call against your cash balance. Step Plan subscribers must use `https://api.stepfun.com/step_plan/v1/...` to draw from the subscription credit quota. Same key, different path, different meter.

**Fix (one line):** the default `STEPFUN_BASE_URL` was changed in v0.1.1 to point at `/step_plan/v1/`. Upgrade:

```bash
pip install --upgrade hermes-stepfun-imagegen
```

Or, if you've pinned the plugin path under `~/.hermes/plugins/image_gen/stepfun/`, pull the latest `__init__.py` (search for `STEPFUN_BASE_URL`) and make sure the default is `https://api.stepfun.com/step_plan/v1`. Then restart Hermes:

```bash
hermes gateway restart
```

To confirm the fix is live, run a smoke test and inspect the effective base URL:

```bash
python -c "import importlib.util; m=importlib.import_module('hermes_stepfun_imagegen'); print(m.STEPFUN_BASE_URL)"
# expected: https://api.stepfun.com/step_plan/v1
```

**Note on already-billed calls:** StepFun does not refund calls that were billed against your cash balance before you switched endpoints. Going forward, calls go to credit.

**If you actually want cash billing** (e.g. you've used up your Step Plan quota and want to keep going with the per-image rate), explicitly override the base URL:

```bash
# in ~/.hermes/.env
STEPFUN_BASE_URL=https://api.stepfun.com/v1
```

See the official [Step Plan image integration docs](https://platform.stepfun.com/docs/zh/step-plan/integrations/image-api) for details on the two endpoints.

### Diagnostic prompt for your agent

If you ask an AI agent to debug this for you, paste the block below into a fresh chat. It walks the agent through the exact checks that matter:

```text
You are debugging a Hermes Agent + StepFun image plugin billing issue. The user
is on a Step Plan subscription, but image generation/editing calls are being
billed against their cash balance (per-image ¥ deduction) instead of against
their Step Plan credit quota.

StepFun has TWO independent endpoints that bill DIFFERENTLY for the SAME API
key:

  - https://api.stepfun.com/v1/...            (open platform -> cash balance)
  - https://api.stepfun.com/step_plan/v1/...  (Step Plan     -> credit quota)

The plugin in ~/.hermes/plugins/image_gen/stepfun/__init__.py defaults to
STEPFUN_BASE_URL. The default was historically the cash endpoint, which
bills subscribers' cash balance. Step Plan subscribers need the /step_plan/v1
path.

Walk through these checks in order. Do not skip any. After each check, report
PASS/FAIL with the exact value you saw. When you find the problem, state the
fix in one sentence.

1. CONFIRM the plugin is the latest version. Read the file
   ~/.hermes/plugins/image_gen/stepfun/__init__.py and find the line that
   sets STEPFUN_BASE_URL. Report the literal value.

2. If the default is NOT https://api.stepfun.com/step_plan/v1, the plugin is
   on the legacy cash endpoint. That is the bug.

3. Check for env override: `grep -E '^STEPFUN_BASE_URL=' ~/.hermes/.env`
   Report whether the user has set it. If they have, that value wins over
   the default — verify it points at /step_plan/v1.

4. Check for the install path being a vendored copy under
   ~/.hermes/plugins/ (not the pip-installed version). If both exist,
   ~/.hermes/plugins/ wins because Hermes loads it first. Report which
   one is on disk.

5. Confirm the version that is actually loaded into the running gateway:
   from outside the gateway, run:
     python -c "import sys; sys.path.insert(0, '/home/lora/.hermes/hermes-agent');
                from importlib.machinery import SourceFileLoader;
                m = SourceFileLoader('p', '/home/lora/.hermes/plugins/image_gen/stepfun/__init__.py').load_module();
                print(m.STEPFUN_BASE_URL)"
   The output is what the gateway will use on the next call.

6. Suggest the smallest fix:
   - If STEPFUN_BASE_URL default is wrong: edit the file, change the default
     to https://api.stepfun.com/step_plan/v1, then `hermes gateway restart`.
   - If env override is wrong: edit ~/.hermes/.env, fix STEPFUN_BASE_URL,
     then `hermes gateway restart`.
   - If vendored copy is stale: replace it with the latest from the
     hermes-stepfun-imagegen repo, then `hermes gateway restart`.

7. After applying the fix, do an end-to-end smoke test:
     STEPFUN_API_KEY=... python -c "import importlib.util;
       m=importlib.import_module('hermes_stepfun_imagegen');
       p=m.StepFunImageGenProvider();
       r=p.generate('a tiny red circle on white', aspect_ratio='square');
       print(r['success'], r['provider'], r['model'])"
   Confirm success=True, provider=stepfun.

8. Tell the user: "Going forward, calls will bill against Step Plan credit.
   Previous calls that billed your cash balance are not refundable by
   StepFun. If you want to dispute them, contact StepFun support with your
   account ID and the date range."

Output format: a numbered list of checks with PASS/FAIL and the literal
value seen. Then ONE recommended fix command. No verbose explanation. The
user is technical.
```

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
    - stepfun-imggen
```

And verify the pip package is installed:

```bash
python -c "import hermes_stepfun_imagegen; print(hermes_stepfun_imagegen.__file__)"
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
