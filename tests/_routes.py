"""Discovery of resource classes and their route-declaring methods.

Shared by the route coverage and docstring tests, which must see the same
set of methods.
"""

from __future__ import annotations

import importlib
import pkgutil

import bw_serve_client
from bw_serve_client.resource import Resource
from bw_serve_client.resource import routed_methods
from bw_serve_client.resource import RouteKey

#: One route-declaring method: its class, its name, its routes.
RoutedMethod = tuple[type[Resource], str, tuple[RouteKey, ...]]


# -----------------------------------------------------------------------------
def resource_classes() -> list[type[Resource]]:
  """Find every resource class in the package.

  Every submodule is imported first, so a class is found whether or not
  ``__init__`` exports it yet. Only classes defined in the package count,
  so a test's own stand-in class never does.

  Returns:
    The classes, sorted by qualified name.
  """
  for module in pkgutil.walk_packages(bw_serve_client.__path__, f"{bw_serve_client.__name__}."):
    importlib.import_module(module.name)

  found: dict[str, type[Resource]] = {}
  pending: list[type[Resource]] = [Resource]

  while pending:
    cls = pending.pop()
    pending.extend(cls.__subclasses__())

    if cls is not Resource and cls.__module__.startswith(f"{bw_serve_client.__name__}."):
      found[f"{cls.__module__}.{cls.__qualname__}"] = cls

  return [found[name] for name in sorted(found)]


# -----------------------------------------------------------------------------
def resource_methods() -> list[RoutedMethod]:
  """List every route-declaring method of every resource class.

  Returns:
    One ``(class, method name, declared routes)`` entry per method.
  """
  return [(cls, name, keys) for cls in resource_classes() for name, keys in routed_methods(cls).items()]
