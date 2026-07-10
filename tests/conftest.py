"""Test configuration and shared fixtures for hermes-stepfun-imagegen."""

import sys
import types
import pathlib

# ---------------------------------------------------------------------------
# Stub the `agent.image_gen_provider` module so tests can run without
# installing the full Hermes Agent core package.
# ---------------------------------------------------------------------------

agent_pkg = types.ModuleType("agent")
agent_pkg.__path__ = [str(pathlib.Path(__file__).parent.parent / "agent")]
sys.modules.setdefault("agent", agent_pkg)

# Minimal stub of the symbols used by the plugin.
image_gen_provider = types.ModuleType("agent.image_gen_provider")


def _default_aspect_ratio():
    return "landscape"


def resolve_aspect_ratio(value=None):
    if not isinstance(value, str):
        return _default_aspect_ratio()
    v = value.strip().lower()
    if v in ("landscape", "square", "portrait"):
        return v
    return _default_aspect_ratio()


def normalize_reference_images(value):
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value if item]


def error_response(error, error_type="unknown", **kwargs):
    result = dict(kwargs)
    result.setdefault("success", False)
    result.setdefault("error", error)
    result.setdefault("error_type", error_type)
    return result


def success_response(image="", **kwargs):
    result = dict(kwargs)
    result.setdefault("success", True)
    result.setdefault("image", image)
    return result


def save_b64_image(b64, prefix="image"):
    import base64
    import tempfile

    data = base64.b64decode(b64) if isinstance(b64, str) else b64
    tmp = tempfile.NamedTemporaryFile(prefix=f"{prefix}_", suffix=".png", delete=False)
    tmp.write(data)
    tmp.close()
    return pathlib.Path(tmp.name)


def save_url_image(url, prefix="image"):
    import urllib.request
    import tempfile

    req = urllib.request.Request(url, headers={"User-Agent": "HermesTest/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    tmp = tempfile.NamedTemporaryFile(prefix=f"{prefix}_", suffix=".png", delete=False)
    tmp.write(data)
    tmp.close()
    return pathlib.Path(tmp.name)


class ImageGenProvider:
    pass


image_gen_provider.DEFAULT_ASPECT_RATIO = "landscape"
image_gen_provider.ImageGenProvider = ImageGenProvider
image_gen_provider.error_response = error_response
image_gen_provider.normalize_reference_images = normalize_reference_images
image_gen_provider.resolve_aspect_ratio = resolve_aspect_ratio
image_gen_provider.save_b64_image = save_b64_image
image_gen_provider.save_url_image = save_url_image
image_gen_provider.success_response = success_response

agent_pkg.image_gen_provider = image_gen_provider
sys.modules.setdefault("agent.image_gen_provider", image_gen_provider)
