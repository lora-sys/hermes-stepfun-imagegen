"""Tests for hermes_stepfun_imagegen plugin."""

import os
import sys

# Ensure plugin is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hermes_stepfun_imagegen import StepFunImageGenProvider


def test_provider_name():
    provider = StepFunImageGenProvider()
    assert provider.name == "stepfun"


def test_provider_display_name():
    provider = StepFunImageGenProvider()
    assert provider.display_name == "StepFun"


def test_default_model():
    provider = StepFunImageGenProvider()
    assert provider.default_model() == "step-image-edit-2"


def test_list_models():
    provider = StepFunImageGenProvider()
    models = provider.list_models()
    assert len(models) == 3
    ids = [m["id"] for m in models]
    assert "step-image-edit-2" in ids
    assert "step-2x-large" in ids
    assert "step-1x-medium" in ids


def test_capabilities():
    provider = StepFunImageGenProvider()
    caps = provider.capabilities()
    assert "text" in caps["modalities"]
    assert "image" in caps["modalities"]


def test_is_available_without_key(monkeypatch):
    monkeypatch.delenv("STEPFUN_API_KEY", raising=False)
    provider = StepFunImageGenProvider()
    assert provider.is_available() is False


def test_is_available_with_key(monkeypatch):
    monkeypatch.setenv("STEPFUN_API_KEY", "test-key")
    provider = StepFunImageGenProvider()
    assert provider.is_available() is True


def test_generate_requires_api_key(monkeypatch):
    monkeypatch.delenv("STEPFUN_API_KEY", raising=False)
    provider = StepFunImageGenProvider()
    result = provider.generate(prompt="test", aspect_ratio="square")
    assert result["success"] is False
    assert result["error_type"] == "auth_required"


def test_generate_requires_prompt(monkeypatch):
    monkeypatch.setenv("STEPFUN_API_KEY", "test-key")
    provider = StepFunImageGenProvider()
    result = provider.generate(prompt="", aspect_ratio="square")
    assert result["success"] is False
    assert result["error_type"] == "invalid_argument"
