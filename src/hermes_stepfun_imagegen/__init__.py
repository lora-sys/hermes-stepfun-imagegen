"""StepFun image generation backend.

Exposes StepFun's image models as an ImageGenProvider implementation:

- step-image-edit-2  (recommended): text-to-image + image editing, 1-2s
- step-2x-large: high-quality text-to-image / image-to-image
- step-1x-medium: mid-quality text-to-image / image-to-image

API reference: https://platform.stepfun.com/docs/zh/api-reference/images/image
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    normalize_reference_images,
    resolve_aspect_ratio,
    save_b64_image,
    save_url_image,
    success_response,
)

logger = logging.getLogger(__name__)

STEPFUN_BASE_URL = os.environ.get("STEPFUN_BASE_URL", "https://api.stepfun.com/v1")

# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

_MODELS: Dict[str, Dict[str, Any]] = {
    "step-image-edit-2": {
        "display": "Step Image Edit 2",
        "speed": "~1-2s",
        "strengths": "Fast text-to-image + editing, recommended",
        "price": "varies",
    },
    "step-2x-large": {
        "display": "Step 2X Large",
        "speed": "~10-20s",
        "strengths": "High quality, supports image-to-image",
        "price": "varies",
    },
    "step-1x-medium": {
        "display": "Step 1X Medium",
        "speed": "~10-20s",
        "strengths": "Balanced quality and speed",
        "price": "varies",
    },
}

DEFAULT_MODEL = "step-image-edit-2"

# StepFun size format is "height x width" for step-image-edit-2
# e.g. 1024x1024, 768x1360, 896x1184, 1360x768, 1184x896
_ASPECT_TO_SIZE = {
    "landscape": "768x1360",
    "square": "1024x1024",
    "portrait": "1360x768",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_config() -> Dict[str, Any]:
    """Read image_gen section from config.yaml."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen config: %s", exc)
        return {}


def _resolve_model() -> str:
    """Pick the active model id."""
    cfg = _load_config()
    stepfun_cfg = cfg.get("stepfun") if isinstance(cfg.get("stepfun"), dict) else {}
    candidate = stepfun_cfg.get("model") if isinstance(stepfun_cfg, dict) else None
    if isinstance(candidate, str) and candidate in _MODELS:
        return candidate
    top = cfg.get("model")
    if isinstance(top, str) and top in _MODELS:
        return top
    return DEFAULT_MODEL


def _load_image_bytes(ref: str) -> Tuple[bytes, str]:
    """Load image bytes from a URL, data URI, or local path."""
    ref = ref.strip()
    lower = ref.lower()
    if lower.startswith(("http://", "https://")):
        import urllib.request

        req = urllib.request.Request(ref, headers={"User-Agent": "Hermes/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        name = ref.split("?", 1)[0].rsplit("/", 1)[-1] or "image.png"
        return data, name
    if lower.startswith("data:"):
        header, _, b64 = ref.partition(",")
        ext = "png"
        if "image/" in header:
            ext = header.split("image/", 1)[1].split(";", 1)[0] or "png"
        return base64.b64decode(b64), f"image.{ext}"
    # Local file path
    from agent.file_safety import raise_if_read_blocked

    raise_if_read_blocked(ref)
    with open(ref, "rb") as fh:
        data = fh.read()
    name = os.path.basename(ref) or "image.png"
    return data, name


def _call_stepfun(
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Tuple[str, bytes, str]]] = None,
) -> Dict[str, Any]:
    """Make a request to the StepFun API and return parsed JSON."""
    import urllib.request
    import urllib.error

    url = f"{STEPFUN_BASE_URL}{path}"
    api_key = os.environ.get("STEPFUN_API_KEY")
    if not api_key:
        return error_response(
            error="STEPFUN_API_KEY not set.",
            error_type="auth_required",
            provider="stepfun",
        )

    headers = {"Authorization": f"Bearer {api_key}"}

    if files is not None:
        # multipart/form-data
        boundary = "----HermesStepFunBoundary"
        body_parts: List[bytes] = []

        for key, (filename, data, content_type) in files.items():
            body_parts.append(
                f"--{boundary}\r\n".encode()
            )
            body_parts.append(
                f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
            )
            body_parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
            body_parts.append(data)
            body_parts.append(b"\r\n")

        if payload:
            for k, v in payload.items():
                if v is None:
                    continue
                body_parts.append(
                    f"--{boundary}\r\n".encode()
                )
                body_parts.append(
                    f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
                )
                body_parts.append(str(v).encode())
                body_parts.append(b"\r\n")

        body_parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(body_parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        body = json.dumps(payload or {}).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        logger.debug("StepFun API error %s: %s", exc.code, detail)
        return error_response(
            error=f"StepFun API error {exc.code}: {detail[:300]}",
            error_type="api_error",
            provider="stepfun",
        )
    except Exception as exc:
        logger.debug("StepFun request failed", exc_info=True)
        return error_response(
            error=f"StepFun request failed: {exc}",
            error_type="api_error",
            provider="stepfun",
        )


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class StepFunImageGenProvider(ImageGenProvider):
    """StepFun image generation backend."""

    @property
    def name(self) -> str:
        return "stepfun"

    @property
    def display_name(self) -> str:
        return "StepFun"

    def is_available(self) -> bool:
        if not os.environ.get("STEPFUN_API_KEY"):
            return False
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": model_id,
                "display": meta["display"],
                "speed": meta["speed"],
                "strengths": meta["strengths"],
                "price": meta.get("price", "varies"),
            }
            for model_id, meta in _MODELS.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "StepFun",
            "badge": "paid",
            "tag": "step-image-edit-2 / step-2x-large / step-1x-medium",
            "env_vars": [
                {
                    "key": "STEPFUN_API_KEY",
                    "prompt": "StepFun API key",
                    "url": "https://platform.stepfun.com",
                },
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        # step-image-edit-2 supports editing; step-2x/1x support image2image
        return {"modalities": ["text", "image"], "max_reference_images": 1}

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="stepfun",
                aspect_ratio=aspect,
            )

        api_key = os.environ.get("STEPFUN_API_KEY")
        if not api_key:
            return error_response(
                error="STEPFUN_API_KEY not set. Configure it in Hermes settings.",
                error_type="auth_required",
                provider="stepfun",
                aspect_ratio=aspect,
            )

        model_id = _resolve_model()
        model_meta = _MODELS.get(model_id, _MODELS[DEFAULT_MODEL])

        # Collect source images
        sources: List[str] = []
        if isinstance(image_url, str) and image_url.strip():
            sources.append(image_url.strip())
        for ref in (normalize_reference_images(reference_image_urls) or []):
            sources.append(ref)
        sources = sources[: self.capabilities().get("max_reference_images", 1)]
        is_edit = bool(sources)
        modality = "image" if is_edit else "text"

        try:
            if is_edit and model_id == "step-image-edit-2":
                result = self._edit_image(prompt, aspect, sources[0], model_id)
            elif is_edit and model_id in ("step-2x-large", "step-1x-medium"):
                result = self._image_to_image(prompt, aspect, sources[0], model_id, kwargs)
            else:
                result = self._text_to_image(prompt, aspect, model_id, kwargs)
        except Exception as exc:
            logger.debug("StepFun generation failed", exc_info=True)
            return error_response(
                error=f"StepFun generation failed: {exc}",
                error_type="api_error",
                provider="stepfun",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        if not result.get("success"):
            return result

        return success_response(
            image=result.get("image", ""),
            model=model_id,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="stepfun",
            modality=modality,
            extra=result.get("extra", {}),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _text_to_image(
        self,
        prompt: str,
        aspect: str,
        model_id: str,
        kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        # step-image-edit-2 uses "height x width"
        size = _ASPECT_TO_SIZE.get(aspect, _ASPECT_TO_SIZE["square"])
        if model_id != "step-image-edit-2":
            # step-2x-large / step-1x-medium: width x height (OpenAI-style)
            width, height = {
                "landscape": (1280, 800),
                "square": (1024, 1024),
                "portrait": (800, 1280),
            }.get(aspect, (1024, 1024))
            size = f"{width}x{height}"

        payload: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt[:512],
            "size": size,
            "n": 1,
            "response_format": "b64_json",
        }

        if model_id == "step-image-edit-2":
            payload["steps"] = int(kwargs.get("steps", 8))
            payload["cfg_scale"] = float(kwargs.get("cfg_scale", 1.0))
            seed = kwargs.get("seed")
            if seed is not None:
                payload["seed"] = int(seed)
        else:
            payload["steps"] = int(kwargs.get("steps", 50))
            payload["cfg_scale"] = float(kwargs.get("cfg_scale", 6.0))
            seed = kwargs.get("seed")
            if seed is not None:
                payload["seed"] = int(seed)

        resp = _call_stepfun("/images/generations", payload=payload)
        if not resp.get("data"):
            return error_response(
                error="StepFun returned no image data",
                error_type="empty_response",
                provider="stepfun",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        item = resp["data"][0]
        b64 = item.get("b64_json")
        url = item.get("url")
        seed_value = item.get("seed")

        if b64:
            try:
                saved_path = save_b64_image(b64, prefix=f"stepfun_{model_id}")
                image_ref = str(saved_path)
            except Exception as exc:
                return error_response(
                    error=f"Could not save image: {exc}",
                    error_type="io_error",
                    provider="stepfun",
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
        elif url:
            try:
                saved_path = save_url_image(url, prefix=f"stepfun_{model_id}")
                image_ref = str(saved_path)
            except Exception as exc:
                logger.warning("Could not cache StepFun image URL: %s", exc)
                image_ref = url
        else:
            return error_response(
                error="StepFun response contained neither b64_json nor URL",
                error_type="empty_response",
                provider="stepfun",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {"size": size}
        if seed_value is not None:
            extra["seed"] = seed_value

        return {"success": True, "image": image_ref, "extra": extra}

    def _edit_image(
        self,
        prompt: str,
        aspect: str,
        source_url: str,
        model_id: str,
    ) -> Dict[str, Any]:
        # step-image-edit-2 edits: multipart upload
        try:
            data, fname = _load_image_bytes(source_url)
        except Exception as exc:
            return error_response(
                error=f"Could not load source image for editing: {exc}",
                error_type="io_error",
                provider="stepfun",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        content_type = "image/png"
        if fname.lower().endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        elif fname.lower().endswith(".webp"):
            content_type = "image/webp"

        files = {
            "image": (fname, data, content_type),
        }

        payload: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt[:512],
            "response_format": "b64_json",
            "steps": 8,
            "cfg_scale": 1.0,
            "seed": 1,
            "text_mode": "false",
        }

        resp = _call_stepfun("/images/edits", payload=payload, files=files)
        if not resp.get("data"):
            return error_response(
                error="StepFun edit returned no image data",
                error_type="empty_response",
                provider="stepfun",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        item = resp["data"][0]
        b64 = item.get("b64_json")
        url = item.get("url")
        seed_value = item.get("seed")

        if b64:
            try:
                saved_path = save_b64_image(b64, prefix=f"stepfun_edit_{model_id}")
                image_ref = str(saved_path)
            except Exception as exc:
                return error_response(
                    error=f"Could not save edited image: {exc}",
                    error_type="io_error",
                    provider="stepfun",
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
        elif url:
            try:
                saved_path = save_url_image(url, prefix=f"stepfun_edit_{model_id}")
                image_ref = str(saved_path)
            except Exception as exc:
                logger.warning("Could not cache StepFun edit URL: %s", exc)
                image_ref = url
        else:
            return error_response(
                error="StepFun edit response contained neither b64_json nor URL",
                error_type="empty_response",
                provider="stepfun",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {}
        if seed_value is not None:
            extra["seed"] = seed_value

        return {"success": True, "image": image_ref, "extra": extra}

    def _image_to_image(
        self,
        prompt: str,
        aspect: str,
        source_url: str,
        model_id: str,
        kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        size = f"1024x1024"
        payload: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt[:1024],
            "source_url": source_url,
            "source_weight": float(kwargs.get("source_weight", 0.5)),
            "size": size,
            "n": 1,
            "response_format": "b64_json",
        }
        if "steps" in kwargs:
            payload["steps"] = int(kwargs["steps"])
        if "cfg_scale" in kwargs:
            payload["cfg_scale"] = float(kwargs["cfg_scale"])
        if "seed" in kwargs and kwargs["seed"]:
            payload["seed"] = int(kwargs["seed"])

        resp = _call_stepfun("/images/image2image", payload=payload)
        if not resp.get("data"):
            return error_response(
                error="StepFun image2image returned no image data",
                error_type="empty_response",
                provider="stepfun",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        item = resp["data"][0]
        b64 = item.get("b64_json")
        url = item.get("url")
        seed_value = item.get("seed")

        if b64:
            try:
                saved_path = save_b64_image(b64, prefix=f"stepfun_i2i_{model_id}")
                image_ref = str(saved_path)
            except Exception as exc:
                return error_response(
                    error=f"Could not save image2image result: {exc}",
                    error_type="io_error",
                    provider="stepfun",
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
        elif url:
            try:
                saved_path = save_url_image(url, prefix=f"stepfun_i2i_{model_id}")
                image_ref = str(saved_path)
            except Exception as exc:
                logger.warning("Could not cache StepFun i2i URL: %s", exc)
                image_ref = url
        else:
            return error_response(
                error="StepFun image2image response missing b64_json and URL",
                error_type="empty_response",
                provider="stepfun",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {"size": size}
        if seed_value is not None:
            extra["seed"] = seed_value

        return {"success": True, "image": image_ref, "extra": extra}


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Register the StepFun image generation provider."""
    ctx.register_image_gen_provider(StepFunImageGenProvider())
