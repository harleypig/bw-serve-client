"""Load one of the repository's tools by path, for the test that covers it.

The tools under ``upstream/``, ``codegen/`` and the repository root are
scripts, not packages, so nothing makes them importable. Putting their
directory on ``sys.path`` would make them importable everywhere, for the
rest of the session, under a generic name like ``detect`` or ``generate``,
and a shadowed or cached module could then couple tests that have nothing
to do with each other (#103 - test modules changing sys.path).
``test_sys_path.py`` is the check that nothing does.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------------
def load_tool(relpath: str, name: str) -> ModuleType:
  """Load the tool at ``relpath`` as a module called ``name``.

  ``name`` stays registered in ``sys.modules``, because dataclasses look
  the defining module up there, so it must be one no other module uses.

  A tool that imports a sibling by its bare name (``detect`` imports
  ``spec_fixes``) gets its own directory on ``sys.path`` while it runs and
  keeps the sibling it imported. Both are undone afterwards: ``sys.path``
  is restored and the sibling is dropped from ``sys.modules``, so neither
  is importable by anything else.

  Args:
    relpath: The tool's path, relative to the repository root.
    name: The module name to load it under.

  Returns:
    The loaded module.

  Raises:
    ValueError: ``name`` is already a loaded module.
  """
  if name in sys.modules:
    raise ValueError(f"{name} is already a loaded module")

  path = ROOT / relpath
  spec = importlib.util.spec_from_file_location(name, path)
  assert spec is not None
  assert spec.loader is not None
  module = importlib.util.module_from_spec(spec)

  saved_path = list(sys.path)
  saved_modules = set(sys.modules)
  sys.modules[name] = module
  sys.path.insert(0, str(path.parent))

  try:
    spec.loader.exec_module(module)

  except BaseException:
    del sys.modules[name]
    raise

  finally:
    sys.path[:] = saved_path

    for added in set(sys.modules) - saved_modules - {name}:
      file = getattr(sys.modules[added], "__file__", None)

      if file is not None and Path(file).resolve().parent == path.parent:
        del sys.modules[added]

  return module
