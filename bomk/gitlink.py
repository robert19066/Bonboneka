"""
bomk/gitlink.py – Manage template git configuration and auto-commit behavior.
"""

import subprocess
import json
from pathlib import Path
from .lib import Logger
from .config import TEMPLATE_REPO


GITLINK_CONFIG = ".bomk_gitlink.json"


def _run_git(args: list[str], cwd: str, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return result."""
    if capture:
        return subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
    else:
        return subprocess.run(
            ["git"] + args,
            cwd=cwd,
        )


def set_origin(template_path: Path, url: str, log: Logger | None = None) -> None:
    """Set or update the git origin for a template."""
    if not (template_path / ".git").exists():
        raise ValueError(f"Template is not a git repository: {template_path}")

    log and log.step(f"Setting origin to: {url}")

    # Check if origin exists
    r = _run_git(["remote", "get-url", "origin"], str(template_path))

    if r.returncode == 0 and r.stdout.strip():
        # Origin exists, update it
        _run_git(["remote", "set-url", "origin", url], str(template_path))
        log and log.success(f"Origin updated")
    else:
        # Origin doesn't exist, add it
        _run_git(["remote", "add", "origin", url], str(template_path))
        log and log.success(f"Origin added")


def set_behaviour(template_path: Path, behaviour: str, log: Logger | None = None) -> None:
    """Set the auto-commit behaviour (commit-per-build or manual-commit)."""
    if behaviour not in ("commit-per-build", "manual-commit"):
        raise ValueError(f"Invalid behaviour: {behaviour}. Must be 'commit-per-build' or 'manual-commit'")

    config_path = template_path / GITLINK_CONFIG
    config = {}

    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            config = {}

    config["behaviour"] = behaviour
    config_path.write_text(json.dumps(config, indent=2))

    log and log.success(f"Behaviour set to: {behaviour}")


def get_behaviour(template_path: Path) -> str:
    """Get the current auto-commit behaviour."""
    config_path = template_path / GITLINK_CONFIG
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            return config.get("behaviour", "manual-commit")
        except json.JSONDecodeError:
            return "manual-commit"
    return "manual-commit"


def commit_template(template_path: Path, log: Logger | None = None) -> None:
    """Commit all changes in the template to git."""
    if not (template_path / ".git").exists():
        raise ValueError(f"Template is not a git repository: {template_path}")

    log and log.step("Committing template changes")

    # Stage all changes
    _run_git(["add", "-A"], str(template_path))

    # Check if there are changes to commit
    r = _run_git(["diff", "--cached", "--quiet"], str(template_path))

    if r.returncode == 0:
        log and log.info("No changes to commit")
        return

    # Commit
    _run_git(
        ["commit", "-m", "Auto-commit by Bonboneka"],
        str(template_path),
    )

    log and log.success("Changes committed")


def disengage_template(template_path: Path, log: Logger | None = None) -> None:
    """Reset template to default origin and remove gitlink configuration."""
    if not (template_path / ".git").exists():
        raise ValueError(f"Template is not a git repository: {template_path}")

    log and log.step("Disengaging template")

    # Reset origin to default
    _run_git(["remote", "set-url", "origin", TEMPLATE_REPO], str(template_path))
    log and log.success(f"Origin reset to: {TEMPLATE_REPO}")

    # Remove config file
    config_path = template_path / GITLINK_CONFIG
    if config_path.exists():
        config_path.unlink()
        log and log.success(f"Configuration removed")
    else:
        log and log.info("No configuration to remove")

    log and log.success("Template disengaged successfully")


def push_template(template_path: Path, log: Logger | None = None) -> None:
    """Push all commits to the remote repository."""
    if not (template_path / ".git").exists():
        raise ValueError(f"Template is not a git repository: {template_path}")

    log and log.step("Pushing changes to remote")

    # Push to origin
    r = _run_git(["push", "origin", "HEAD"], str(template_path))

    if r.returncode != 0:
        raise ValueError(f"Git push failed:\n{r.stderr.strip()}")

    log and log.success("Changes pushed to remote")
