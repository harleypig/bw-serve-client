"""Tests for the package's public surface, ``bw_serve_client.__all__`` (#31)."""

from __future__ import annotations

import pytest

import bw_serve_client
from bw_serve_client._generated import models
from bw_serve_client._generated import routes

HAND_WRITTEN = [
  "ApiClient",
  "ErrorHandler",
  "DefaultErrorHandler",
  "BitwardenError",
  "ValidationError",
  "UserError",
  "ExternalServiceError",
  "InternalError",
  "Folders",
  "Folder",
]

# Importable from their modules, but deliberately not part of the surface.
INTERNAL = ["Resource", "category_for_status", "Route", "Parameter", "ROUTES", "_generated", "_models", "logging"]


# -----------------------------------------------------------------------------
class TestAll:
  """``__all__`` is the hand-written classes plus the generated models, and nothing else."""

  def test_every_name_resolves(self: TestAll) -> None:
    """Every exported name is bound on the package, so ``import *`` cannot fail."""
    missing = [name for name in bw_serve_client.__all__ if not hasattr(bw_serve_client, name)]

    assert missing == []

  def test_hand_written_names_are_exported(self: TestAll) -> None:
    """The client, the handler protocol and default, the errors and the resource classes are public."""
    assert set(HAND_WRITTEN) <= set(bw_serve_client.__all__)

  def test_nothing_else(self: TestAll) -> None:
    """The surface is exactly the hand-written names and the models, so an addition is a decision."""
    assert sorted(bw_serve_client.__all__) == sorted([*HAND_WRITTEN, *models.__all__])

  @pytest.mark.parametrize("name", INTERNAL)
  def test_internal_names_are_not_exported(self: TestAll, name: str) -> None:
    """Internals and the generated route list stay out of ``__all__``."""
    assert name not in bw_serve_client.__all__

  def test_no_route_list_name_leaks(self: TestAll) -> None:
    """No name the route-list module exports reaches the package surface, whatever it adds later."""
    assert set(routes.__all__).isdisjoint(bw_serve_client.__all__)
