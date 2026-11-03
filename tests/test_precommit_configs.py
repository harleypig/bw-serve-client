"""The check and fix pre-commit configs run the same hooks (#95).

A file that passes one config must pass the other, so the two may differ only
where a hook needs a different flag to check rather than fix. Every such
difference is listed in ``ALLOWED``; anything else is drift.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

# The test env installs only the main and test groups, which carry no PyYAML.
# The precommit-configs-match hook in both configs runs this file with pinned
# dependencies, so CI's lint job is where it runs.
yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent
CHECK = ROOT / ".pre-commit-config.yaml"
FIX = ROOT / ".pre-commit-config-fix.yaml"

#: Keys every hook may word differently: it describes the mode, not the hook.
ALWAYS_ALLOWED = frozenset({"description"})

#: Per hook id, the keys that differ because one config checks and the other
#: fixes. ``additional_dependencies`` is never listed: both modes need the
#: same environment.
ALLOWED: dict[str, frozenset[str]] = {
  # Upstream rewrites files; the check config greps for the same findings.
  "trailing-whitespace": frozenset({"repo", "rev", "name", "language", "entry", "types"}),
  "end-of-file-fixer": frozenset({"repo", "rev", "name", "language", "entry", "args", "types"}),
  # ``poetry check --lock`` against ``poetry lock``.
  "poetry-lock": frozenset({"name", "entry"}),
  "isort": frozenset({"args"}),
  "yapf": frozenset({"args"}),
  "pydocstringformatter": frozenset({"args", "entry"}),
  "markdownlint": frozenset({"args"}),
}


def load_hooks(path: Path) -> list[dict[str, Any]]:
  """Flatten a config's hooks in run order, each carrying its repo and rev.

  Args:
    path: The pre-commit config to read.

  Returns:
    One dict per hook: the hook's own keys plus ``repo`` and, where the repo
    has one, ``rev``.
  """
  config = yaml.safe_load(path.read_text(encoding="utf-8"))
  hooks = []

  for repo in config["repos"]:
    pinned = {key: repo[key] for key in ("repo", "rev") if key in repo}
    hooks.extend({**pinned, **hook} for hook in repo["hooks"])

  return hooks


def differing_keys(check: dict[str, Any], fix: dict[str, Any]) -> set[str]:
  """Name the keys whose values differ between two hooks, absence included.

  Args:
    check: The hook as the check config declares it.
    fix: The same hook as the fix config declares it.

  Returns:
    Every key present in either hook whose values are not equal.
  """
  return {key for key in check.keys() | fix.keys() if check.get(key) != fix.get(key)}


CHECK_HOOKS = load_hooks(CHECK)
FIX_HOOKS = load_hooks(FIX)
FIX_BY_ID = {hook["id"]: hook for hook in FIX_HOOKS}


# -----------------------------------------------------------------------------
class TestConfigsMatch:
  """The two configs run the same hooks, in the same order, in the same environments."""

  def test_same_top_level_settings(self: TestConfigsMatch) -> None:
    """Settings outside ``repos`` (exclude, default versions) are the same in both."""
    check = yaml.safe_load(CHECK.read_text(encoding="utf-8"))
    fix = yaml.safe_load(FIX.read_text(encoding="utf-8"))

    del check["repos"], fix["repos"]

    assert check == fix

  def test_same_hook_ids_in_order(self: TestConfigsMatch) -> None:
    """Each config runs the same hook ids in the same order."""
    assert [hook["id"] for hook in CHECK_HOOKS] == [hook["id"] for hook in FIX_HOOKS]

  @pytest.mark.parametrize("check_hook", CHECK_HOOKS, ids=lambda hook: hook["id"])
  def test_same_additional_dependencies(self: TestConfigsMatch, check_hook: dict[str, Any]) -> None:
    """A hook installs the same extra packages whichever config runs it."""
    fix_hook = FIX_BY_ID.get(check_hook["id"], {})

    assert check_hook.get("additional_dependencies") == fix_hook.get("additional_dependencies")

  @pytest.mark.parametrize("check_hook", CHECK_HOOKS, ids=lambda hook: hook["id"])
  def test_differences_are_allowed(self: TestConfigsMatch, check_hook: dict[str, Any]) -> None:
    """A hook differs between the configs only in keys ``ALLOWED`` names for it."""
    allowed = ALWAYS_ALLOWED | ALLOWED.get(check_hook["id"], frozenset())
    fix_hook = FIX_BY_ID.get(check_hook["id"], {})

    assert differing_keys(check_hook, fix_hook) - allowed == set()


# -----------------------------------------------------------------------------
class TestAllowlist:
  """``ALLOWED`` names only real hooks and real differences, so it cannot hide drift by going stale."""

  @pytest.mark.parametrize("hook_id", sorted(ALLOWED))
  def test_entry_names_a_hook(self: TestAllowlist, hook_id: str) -> None:
    """Every allowlisted id is a hook both configs run."""
    check_ids = {hook["id"] for hook in CHECK_HOOKS}

    assert hook_id in check_ids & FIX_BY_ID.keys()

  @pytest.mark.parametrize("hook_id", sorted(ALLOWED))
  def test_entry_keys_still_differ(self: TestAllowlist, hook_id: str) -> None:
    """Every allowlisted key does differ, so a resolved difference leaves the list."""
    check_hook = next(hook for hook in CHECK_HOOKS if hook["id"] == hook_id)

    assert ALLOWED[hook_id] - differing_keys(check_hook, FIX_BY_ID[hook_id]) == set()

  def test_detects_an_unlisted_difference(self: TestAllowlist) -> None:
    """A changed dependency on an otherwise identical hook is reported, so the check is not vacuous."""
    check = {"id": "demo", "additional_dependencies": ["a"]}
    fix = {"id": "demo", "additional_dependencies": ["a", "b"]}

    assert differing_keys(check, fix) == {"additional_dependencies"}
