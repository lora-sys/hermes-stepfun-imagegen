"""Image generation fallback chain plugin.

Provider name: ``image-gen-chain``
Fallback order:
  1. stepfun
  2. minimax
  3. pollinations

Usage:
  Set ``image_gen.provider: image-gen-chain`` in config.yaml.
  The chain tries each backend in order and returns the first success.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    normalize_reference_images,
    resolve_aspect_ratio,
    success_response,
)

logger = logging.getLogger(__name__)

_FALLBACK_ORDER = ["stepfun", "minimax", "pollinations"]


def _get_provider(name: str) -> Optional[ImageGenProvider]:
    try:
        from agent.image_gen_registry import get_provider
        return get_provider(name)
    except Exception as exc:
        logger.debug("Chain fallback: could not resolve provider '%s': %s", name, exc)
        return None


def _resolve_chain_model(kwargs: Dict[str, Any], fallback: Optional[str]) -> Optional[str]:
    candidate = kwargs.get("model")
    if isinstance(candidate, str) and candidate.strip():
        return candidate.strip()
    return fallback


class ImageGenChainProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "image-gen-chain"

    @property
    def display_name(self) -> str:
        return "Image Gen Chain (StepFun → MiniMax → Pollinations)"

    def is_available(self) -> bool:
        # Chain is available if at least one backend is registered.
        for name in _FALLBACK_ORDER:
            provider = _get_provider(name)
            if provider is not None:
                return True
        return False

    def list_models(self) -> List[Dict[str, Any]]:
        # Return the stepfun catalog as the primary model list, since the
        # chain accepts whatever model id the configured backend understands.
        provider = _get_provider("stepfun")
        if provider is not None:
            try:
                return provider.list_models()
            except Exception:
                pass
        return [
            {
                "id": "step-image-edit-2",
                "display": "Step Image Edit 2 (via chain)",
                "speed": "~1-2s",
                "strengths": "Primary chain target",
                "price": "varies",
            }
        ]

    def default_model(self) -> Optional[str]:
        provider = _get_provider("stepfun")
        if provider is not None:
            try:
                return provider.default_model()
            except Exception:
                pass
        return "step-image-edit-2"

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Image Gen Chain",
            "badge": "chain",
            "tag": "StepFun → MiniMax → Pollinations fallback chain",
            "env_vars": [
                {
                    "key": "STEPFUN_API_KEY",
                    "prompt": "StepFun API key (optional, first priority)",
                    "url": "https://platform.stepfun.com",
                },
                {
                    "key": "MINIMAX_CN_API_KEY",
                    "prompt": "MiniMax CN API key (optional, second priority)",
                    "url": "https://api.minimaxi.com/user-center/basic-information/interface-key",
                },
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        # Union of capabilities across the chain.
        modalities = {"text"}
        max_refs = 0
        for name in _FALLBACK_ORDER:
            provider = _get_provider(name)
            if provider is None:
                continue
            try:
                caps = provider.capabilities() or {}
            except Exception:
                continue
            if "modalities" in caps:
                modalities = modalities | set(caps["modalities"])
            max_refs = max(max_refs, int(caps.get("max_reference_images") or 0))
        return {"modalities": sorted(modalities), "max_reference_images": max_refs}

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        aspect = resolve_aspect_ratio(aspect_ratio)
        prompt = (prompt or "").strip()

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_input",
                provider=self.name,
                aspect_ratio=aspect,
            )

        norm_refs = normalize_reference_images(reference_image_urls) or []
        sources: List[str] = []
        if isinstance(image_url, str) and image_url.strip():
            sources.append(image_url.strip())
        sources.extend(ref for ref in norm_refs if ref and ref not in sources)

        last_error: Optional[Dict[str, Any]] = None
        tried: List[str] = []

        for provider_name in _FALLBACK_ORDER:
            provider = _get_provider(provider_name)
            if provider is None:
                logger.debug("Chain skip '%s': provider not registered", provider_name)
                continue

            try:
                available = bool(provider.is_available())
            except Exception as exc:
                logger.debug("Chain skip '%s': is_available() raised %s", provider_name, exc)
                continue

            if not available:
                logger.debug("Chain skip '%s': not available", provider_name)
                continue

            call_kwargs: Dict[str, Any] = {
                "prompt": prompt,
                "aspect_ratio": aspect,
            }
            model = _resolve_chain_model(kwargs, provider.default_model())
            if model:
                call_kwargs["model"] = model
            if sources:
                call_kwargs["image_url"] = sources[0]
            if norm_refs:
                call_kwargs["reference_image_urls"] = norm_refs

            tried.append(provider_name)
            try:
                result = provider.generate(**call_kwargs)
            except Exception as exc:
                logger.warning("Chain backend '%s' raised: %s", provider_name, exc)
                last_error = error_response(
                    error=f"{provider_name} backend raised: {exc}",
                    error_type="provider_exception",
                    provider=provider_name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
                continue

            if isinstance(result, dict) and result.get("success"):
                logger.info("Image chain succeeded via '%s'", provider_name)
                result["provider"] = self.name
                result.setdefault("extra", {})
                result["extra"]["chain"] = {
                    "tried": tried,
                    "succeeded": provider_name,
                }
                return result

            last_error = result if isinstance(result, dict) else {
                "success": False,
                "error": str(result),
                "error_type": "provider_contract",
                "provider": provider_name,
            }
            logger.warning(
                "Chain backend '%s' failed: %s",
                provider_name,
                last_error.get("error"),
            )

        message = (
            "All image generation backends in the chain failed: "
            + ", ".join(tried)
            + f". Last error: {last_error.get('error') if isinstance(last_error, dict) else last_error}"
        )
        return error_response(
            error=message,
            error_type="chain_exhausted",
            provider=self.name,
            prompt=prompt,
            aspect_ratio=aspect,
        )


def register(ctx) -> None:
    ctx.register_image_gen_provider(ImageGenChainProvider())
