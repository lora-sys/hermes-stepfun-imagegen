"""Tests for hermes-stepfun-imagegen's setup helper + entry-point wiring.

Same goals as hermes-minimax-media's ``tests/test_setup.py`` — defense in
depth so the entry-point names stay declared and the setup helper stays
idempotent. See that file's docstring for the historical context (README
previously told pip users to write the bundled-layout key, which silently
didn't match the entry-point key).
"""
from __future__ import annotations

import importlib
import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"

# Make the package importable without installing.
sys.path.insert(0, str(SRC_DIR))

setup = importlib.import_module("hermes_stepfun_imagegen.setup")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_hermes_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point setup at a temporary HERMES_HOME so tests don't touch real config."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    return tmp_path


REQUIRED_ENTRY_POINTS = {"stepfun-imggen", "image-gen-chain"}


# ---------------------------------------------------------------------------
# Entry-point declaration
# ---------------------------------------------------------------------------


class TestEntryPoints:
    def test_both_entry_points_present(self) -> None:
        eps = importlib.metadata.entry_points()
        group = (
            eps.select(group="hermes_agent.plugins")
            if hasattr(eps, "select")
            else eps.get("hermes_agent.plugins", [])
        )
        names = {ep.name for ep in group}
        missing = REQUIRED_ENTRY_POINTS - names
        assert not missing, (
            f"pyproject.toml is missing entry points: {missing}. "
            f"Found: {sorted(names)}"
        )

    def test_stepfun_imggen_targets_root_module(self) -> None:
        eps = importlib.metadata.entry_points()
        group = (
            eps.select(group="hermes_agent.plugins")
            if hasattr(eps, "select")
            else eps.get("hermes_agent.plugins", [])
        )
        ep = next((e for e in group if e.name == "stepfun-imggen"), None)
        assert ep is not None
        assert ep.value == "hermes_stepfun_imagegen", (
            f"stepfun-imggen should target the root module, got {ep.value!r}"
        )

    def test_image_gen_chain_targets_chain_subpackage(self) -> None:
        eps = importlib.metadata.entry_points()
        group = (
            eps.select(group="hermes_agent.plugins")
            if hasattr(eps, "select")
            else eps.get("hermes_agent.plugins", [])
        )
        ep = next((e for e in group if e.name == "image-gen-chain"), None)
        assert ep is not None
        assert "chain" in ep.value, (
            f"image-gen-chain should target the chain subpackage, got {ep.value!r}"
        )


# ---------------------------------------------------------------------------
# apply_setup / apply_uninstall
# ---------------------------------------------------------------------------


class TestApplySetup:
    def test_default_provider_stepfun(self, tmp_hermes_home: Path) -> None:
        cfg: dict[str, Any] = {}
        diff = setup.apply_setup(cfg, provider="stepfun")
        assert set(diff["added_to_enabled"]) == REQUIRED_ENTRY_POINTS
        assert cfg["image_gen"]["provider"] == "stepfun"
        assert cfg["image_gen"]["stepfun"]["model"] == "step-image-edit-2"

    def test_provider_chain(self, tmp_hermes_home: Path) -> None:
        cfg: dict[str, Any] = {}
        diff = setup.apply_setup(cfg, provider="image-gen-chain")
        assert diff["wrote_provider_blocks"] == ["image_gen"]
        assert cfg["image_gen"]["provider"] == "image-gen-chain"
        # We don't write the stepfun sub-block in chain mode.
        assert "stepfun" not in cfg["image_gen"]

    def test_idempotent(self, tmp_hermes_home: Path) -> None:
        cfg: dict[str, Any] = {}
        setup.apply_setup(cfg, provider="stepfun")
        diff2 = setup.apply_setup(cfg, provider="stepfun")
        assert diff2["added_to_enabled"] == []
        assert diff2["wrote_provider_blocks"] == []

    def test_does_not_overwrite_existing_provider(self, tmp_hermes_home: Path) -> None:
        """If user already set image_gen.provider = openai, don't clobber."""
        cfg = {
            "image_gen": {"provider": "openai", "openai": {"model": "gpt-image-2"}},
        }
        setup.apply_setup(cfg, provider="stepfun")
        # Untouched.
        assert cfg["image_gen"]["provider"] == "openai"

    def test_force_provider_overrides(self, tmp_hermes_home: Path) -> None:
        cfg = {"image_gen": {"provider": "openai"}}
        setup.apply_setup(cfg, provider="stepfun", force_provider=True)
        assert cfg["image_gen"]["provider"] == "stepfun"

    def test_preserves_other_enabled_plugins(self, tmp_hermes_home: Path) -> None:
        cfg = {"plugins": {"enabled": ["other-plugin", "another"]}}
        setup.apply_setup(cfg)
        enabled = cfg["plugins"]["enabled"]
        assert "other-plugin" in enabled
        assert "another" in enabled
        assert REQUIRED_ENTRY_POINTS.issubset(set(enabled))


class TestApplyUninstall:
    def test_removes_both_entry_points(self, tmp_hermes_home: Path) -> None:
        cfg: dict[str, Any] = {}
        setup.apply_setup(cfg)
        diff = setup.apply_uninstall(cfg)
        assert set(diff["removed_from_enabled"]) == REQUIRED_ENTRY_POINTS
        assert cfg["plugins"]["enabled"] == []
        # Provider blocks gone.
        assert "image_gen" not in cfg

    def test_uninstall_preserves_non_stepfun_provider(self, tmp_hermes_home: Path) -> None:
        cfg = {"image_gen": {"provider": "openai", "openai": {"model": "gpt-image-2"}}}
        diff = setup.apply_uninstall(cfg)
        # No-op because user has a non-stepfun provider.
        assert diff["cleared_provider_blocks"] == []
        assert cfg["image_gen"]["provider"] == "openai"


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------



class TestCLI:
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        # Drive the helper directly via `python -c` instead of `python -m`.
        # `python -m hermes_stepfun_imagegen.setup` first imports the package,
        # which executes `hermes_stepfun_imagegen/__init__.py`. That file
        # `from agent.image_gen_provider import ...` at module level and
        # crashes when imported outside a running hermes-agent process
        # (CI runners don't have the agent installed). `setup.py` itself
        # has no agent import so importing it directly stays faithful to
        # what the `hermes-stepfun-setup` console_script entry point does
        # on a user machine.
        cmd = (
            "import sys; sys.path.insert(0, " + repr(str(SRC_DIR)) + "); "
            "from hermes_stepfun_imagegen.setup import main; "
            "sys.exit(main(" + repr(list(args)) + "))"
        )
        return subprocess.run(
            [sys.executable, "-c", cmd],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
        )

    def test_check_nonzero_when_unconfigured(self, tmp_hermes_home: Path) -> None:
        result = self._run("--check")
        assert result.returncode == 1
        assert "NOT CONFIGURED" in result.stdout

    def test_check_zero_after_setup(self, tmp_hermes_home: Path) -> None:
        self._run()
        result = self._run("--check")
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_dry_run_does_not_modify_file(self, tmp_hermes_home: Path) -> None:
        config = tmp_hermes_home / "config.yaml"
        result = self._run("--print")
        assert "[dry-run]" in result.stdout
        assert not config.exists()

    def test_uninstall_round_trip(self, tmp_hermes_home: Path) -> None:
        self._run()
        self._run("--uninstall")
        config = tmp_hermes_home / "config.yaml"
        after = config.read_text()
        assert "stepfun-imggen" not in after
        assert "image-gen-chain" not in after
        assert "image_gen" not in after


# ---------------------------------------------------------------------------
# Plugin register() callbacks
# ---------------------------------------------------------------------------


class _StubContext:
    def __init__(self) -> None:
        self.image_providers: list[Any] = []
        self.tools: list[Any] = []
        self.hooks: list[Any] = []

    def register_image_gen_provider(self, provider: Any) -> None:
        self.image_providers.append(provider)

    def register_tool(self, *args: Any, **kwargs: Any) -> None:
        self.tools.append((args, kwargs))  # type: ignore[arg-type]

    def register_hook(self, *args: Any, **kwargs: Any) -> None:
        self.hooks.append((args, kwargs))  # type: ignore[arg-type]


class TestPluginRegisterCallbacks:
    def test_stepfun_root_registers_image_provider(self) -> None:
        import hermes_stepfun_imagegen
        ctx = _StubContext()
        hermes_stepfun_imagegen.register(ctx)
        assert len(ctx.image_providers) == 1
        assert ctx.image_providers[0].name == "stepfun"

    def test_chain_subpackage_registers_image_provider(self) -> None:
        import hermes_stepfun_imagegen.chain
        ctx = _StubContext()
        hermes_stepfun_imagegen.chain.register(ctx)
        assert len(ctx.image_providers) == 1
        assert ctx.image_providers[0].name == "image-gen-chain"