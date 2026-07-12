"""One-shot setup helper for hermes-stepfun-imagegen.

After ``pip install hermes-stepfun-imagegen[setup]``, this script adds the
two StepFun plugin entry points (``stepfun-imggen`` and ``image-gen-chain``)
to ``~/.hermes/config.yaml``'s ``plugins.enabled`` list and writes a default
``image_gen`` provider block. Idempotent.

Usage::

    hermes-stepfun-setup                  # enable + write defaults
    hermes-stepfun-setup --check          # exit 0 if configured, 1 otherwise
    hermes-stepfun-setup --uninstall      # remove entries + provider block
    hermes-stepfun-setup --print          # dry run
    hermes-stepfun-setup --json           # machine-readable status
    hermes-stepfun-setup --provider stepfun   # use stepfun as default provider
    hermes-stepfun-setup --provider image-gen-chain   # use the chain

Why this exists
---------------
Hermes' plugin loader (``hermes_cli/plugins.py:_scan_entry_points``) creates
plugin manifests from entry points with ``key=ep.name`` (e.g.
``"stepfun-imggen"``). Writing ``plugins.enabled: [image_gen/stepfun]``
(the bundled-layout path-derived key) does NOT match an entry-point-installed
plugin. ``hermes-stepfun-setup`` writes the correct key so users don't have
to remember the spelling.

If/when upstream Hermes' entry-point loader learns to read the yaml kind,
this script becomes a one-shot migration aid rather than a permanent
install step.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Entry point names (must match pyproject.toml)
ENTRY_POINTS = ("stepfun-imggen", "image-gen-chain")

# Default model per provider.
DEFAULT_MODELS = {
    "stepfun": "step-image-edit-2",
}


def _config_path() -> Path:
    home = os.environ.get("HERMES_HOME", "").strip()
    if home:
        return Path(home).expanduser() / "config.yaml"
    return Path.home() / ".hermes" / "config.yaml"


def _yaml_module():
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        sys.exit(
            "PyYAML is required for hermes-stepfun-setup.\n"
            "Install with:  pip install 'hermes-stepfun-imagegen[setup]'  "
            "or  pip install pyyaml\n"
            f"({exc})"
        )
    return yaml


def load_config(path: Path) -> dict[str, Any]:
    yaml = _yaml_module()
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        sys.exit(f"Could not parse {path}: {exc}")


def save_config(path: Path, cfg: dict[str, Any]) -> None:
    yaml = _yaml_module()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")


def current_status(cfg: dict[str, Any]) -> dict[str, Any]:
    plugins_raw = cfg.get("plugins")
    plugins: dict[str, Any] = plugins_raw if isinstance(plugins_raw, dict) else {}
    enabled_raw = plugins.get("enabled")
    enabled: set[str] = set(enabled_raw) if isinstance(enabled_raw, list) else set()

    image_block_raw = cfg.get("image_gen")
    image_block: dict[str, Any] = image_block_raw if isinstance(image_block_raw, dict) else {}
    provider = image_block.get("provider")
    stepfun_block_raw = image_block.get("stepfun")
    stepfun_block: dict[str, Any] = stepfun_block_raw if isinstance(stepfun_block_raw, dict) else {}

    return {
        "config_path": str(_config_path()),
        "plugins_enabled": sorted(enabled),
        "missing_entry_points": sorted(set(ENTRY_POINTS) - enabled),
        "image_gen_provider": provider,
        "image_gen_model": image_block.get("model"),
        "stepfun_model": stepfun_block.get("model"),
        "fully_configured": all(ep in enabled for ep in ENTRY_POINTS),
    }


def apply_setup(
    cfg: dict[str, Any], *, provider: str = "stepfun", force_provider: bool = False,
) -> dict[str, Any]:
    """Mutate ``cfg`` to enable + configure everything. Returns a diff.

    ``provider`` picks which one to set as ``image_gen.provider``:
      - "stepfun"         → uses the StepFun backend (default)
      - "image-gen-chain" → uses the fallback chain StepFun -> MiniMax -> Pollinations

    ``force_provider`` (default False) overwrites an already-set
    ``image_gen.provider``. By default we leave it alone — only write when
    it's not yet set, so this script is idempotent and won't surprise a
    user who already picked a different provider.
    """
    diff: dict[str, Any] = {"added_to_enabled": [], "wrote_provider_blocks": []}

    plugins = cfg.setdefault("plugins", {})
    if not isinstance(plugins, dict):
        plugins = {}
        cfg["plugins"] = plugins
    enabled_list = plugins.setdefault("enabled", [])
    if not isinstance(enabled_list, list):
        enabled_list = []
        plugins["enabled"] = enabled_list
    enabled_set = set(enabled_list)
    for ep in ENTRY_POINTS:
        if ep not in enabled_set:
            enabled_list.append(ep)
            enabled_set.add(ep)
            diff["added_to_enabled"].append(ep)

    # image_gen block — write provider only if absent.
    image_gen = cfg.get("image_gen") or {}
    if not isinstance(image_gen, dict):
        image_gen = {}
    changed = False
    existing_provider = image_gen.get("provider")
    if existing_provider is None or force_provider:
        if image_gen.get("provider") != provider:
            image_gen["provider"] = provider
            changed = True
    # Default model for stepfun (other providers can stay untouched).
    if provider == "stepfun":
        cur_stepfun = image_gen.get("stepfun") or {}
        if not isinstance(cur_stepfun, dict):
            cur_stepfun = {}
        want_model = DEFAULT_MODELS["stepfun"]
        if cur_stepfun.get("model") != want_model:
            cur_stepfun["model"] = want_model
            changed = True
        image_gen["stepfun"] = cur_stepfun
    if changed:
        diff["wrote_provider_blocks"].append("image_gen")
    cfg["image_gen"] = image_gen

    return diff


def apply_uninstall(cfg: dict[str, Any]) -> dict[str, Any]:
    diff: dict[str, list[str]] = {
        "removed_from_enabled": [],
        "cleared_provider_blocks": [],
    }
    plugins_raw = cfg.get("plugins")
    plugins: dict[str, Any] = plugins_raw if isinstance(plugins_raw, dict) else {}
    enabled_raw = plugins.get("enabled")
    enabled: list[Any] = enabled_raw if isinstance(enabled_raw, list) else []
    ep_set = set(ENTRY_POINTS)
    diff["removed_from_enabled"] = [e for e in enabled if e in ep_set]
    plugins["enabled"] = [e for e in enabled if e not in ep_set]
    cfg["plugins"] = plugins

    image_gen = cfg.get("image_gen")
    if isinstance(image_gen, dict):
        # Only touch fields we ourselves wrote — leave any non-stepfun
        # provider untouched (user may have set stepfun model for a
        # different primary provider, e.g. openai + stepfun fallback).
        if image_gen.get("provider") == "stepfun":
            image_gen.pop("provider", None)
            image_gen.pop("stepfun", None)
            cfg["image_gen"] = image_gen
            diff["cleared_provider_blocks"].append("image_gen")

    # Tidy: drop empty top-level blocks.
    ig = cfg.get("image_gen")
    if isinstance(ig, dict) and not ig:
        cfg.pop("image_gen", None)

    return diff


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="hermes-stepfun-setup",
        description="Configure ~/.hermes/config.yaml to load the StepFun plugins.",
    )
    ap.add_argument("--check", action="store_true",
                    help="exit 0 if fully configured, 1 otherwise (no writes)")
    ap.add_argument("--uninstall", action="store_true",
                    help="reverse the setup (remove entries + clear provider block)")
    ap.add_argument("--print", dest="dry_run", action="store_true",
                    help="dry run: show what would change, don't write")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON to stdout")
    ap.add_argument("--provider", default="stepfun",
                    choices=("stepfun", "image-gen-chain"),
                    help="which provider to set as image_gen.provider (default: stepfun)")
    ap.add_argument("--force-provider", action="store_true",
                    help="overwrite image_gen.provider even if already set")
    args = ap.parse_args(argv)

    path = _config_path()
    cfg = load_config(path)

    if args.check:
        status = current_status(cfg)
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            if status["fully_configured"]:
                print(f"OK  {path}")
                print(f"    enabled: {', '.join(status['plugins_enabled']) or '(none)'}")
                return 0
            print(f"NOT CONFIGURED  {path}")
            if status["missing_entry_points"]:
                print(f"    missing: {', '.join(status['missing_entry_points'])}")
            return 1

    if args.uninstall:
        diff = apply_uninstall(cfg)
        if not args.dry_run:
            save_config(path, cfg)
        if args.json:
            print(json.dumps({"action": "uninstall", "path": str(path),
                              "diff": diff, "dry_run": args.dry_run}, indent=2))
        else:
            print(f"{'[dry-run] ' if args.dry_run else ''}Updated {path}")
            if diff["removed_from_enabled"]:
                print(f"  removed from plugins.enabled: "
                      f"{', '.join(diff['removed_from_enabled'])}")
            if diff["cleared_provider_blocks"]:
                print(f"  cleared provider blocks: "
                      f"{', '.join(diff['cleared_provider_blocks'])}")
        return 0

    diff = apply_setup(cfg, provider=args.provider, force_provider=args.force_provider)
    if not args.dry_run:
        save_config(path, cfg)
    if args.json:
        print(json.dumps({"action": "setup", "path": str(path),
                          "diff": diff, "dry_run": args.dry_run,
                          "provider": args.provider,
                          "status": current_status(cfg)}, indent=2))
    else:
        print(f"{'[dry-run] ' if args.dry_run else ''}Configured {path}")
        if diff["added_to_enabled"]:
            print(f"  added to plugins.enabled: "
                  f"{', '.join(diff['added_to_enabled'])}")
        if diff["wrote_provider_blocks"]:
            print(f"  wrote provider blocks: "
                  f"{', '.join(diff['wrote_provider_blocks'])}")
        print(f"  image_gen.provider: {args.provider}")
        if not diff["added_to_enabled"] and not diff["wrote_provider_blocks"]:
            print("  no changes — already configured")
    return 0


if __name__ == "__main__":
    sys.exit(main())