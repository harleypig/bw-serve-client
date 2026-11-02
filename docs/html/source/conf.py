"""Configuration file for the Sphinx documentation builder."""

# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.realpath('../../..'))

import bw_serve_client  # noqa: E402 - importable only once the path above is set.

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'bw-serve-client'
copyright = '2025, Alan Young'
author = 'Alan Young'
release = bw_serve_client.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
  'sphinx.ext.autodoc',
  'sphinx.ext.viewcode',
  'sphinx.ext.napoleon',
  'sphinx.ext.intersphinx',
  'sphinx.ext.githubpages',
  'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'en'

# Objects are documented in the module that defines them, so their
# headings would otherwise read bw_serve_client._generated.models.Name;
# every public name is imported from bw_serve_client itself.
add_module_names = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
  'prev_next_buttons_location': 'bottom',
  'style_external_links': False,
  'vcs_pageview_mode': 'blob',
  'style_nav_header_background': '#2980B9',
  'collapse_navigation': True,
  'sticky_navigation': True,
  'navigation_depth': 4,
  'includehidden': True,
  'titles_only': False
}

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings. Constructor arguments are in each class docstring, so
# __init__ is not documented on its own. No default for 'members': Sphinx
# 7 lets a non-string default replace a directive's own :members: list, so
# each directive names its members.
autodoc_default_options = {'member-order': 'bysource', 'undoc-members': True, 'exclude-members': '__weakref__'}

# Type hints settings
typehints_fully_qualified = False
typehints_document_rtype = True
typehints_use_rtype = True

# Intersphinx mapping
intersphinx_mapping = {
  'python': ('https://docs.python.org/3/', None),
}

# -- Every public name is documented -----------------------------------------


def _check_public_names(app: object, env: object) -> None:  # noqa: U100 - the event passes app; only env is read.
  """Warn for each name in ``bw_serve_client.__all__`` the build left out.

  Each name is looked up in the module that defines it, which is where
  autodoc documents it. Under ``-W`` a missing name fails the build.

  Args:
    app: The Sphinx application.
    env: The build environment.
  """
  # Sphinx is in the docs group, which pre-commit's pyright env lacks.
  from sphinx.util import logging as sphinx_logging  # type: ignore[import-not-found]

  documented = env.get_domain('py').objects  # type: ignore[attr-defined]
  logger = sphinx_logging.getLogger(__name__)

  for name in bw_serve_client.__all__:
    obj = getattr(bw_serve_client, name)
    target = f"{obj.__module__}.{obj.__qualname__}"

    if target not in documented:
      logger.warning(f"bw_serve_client.{name} ({target}) is not in the API reference")


def _drop_generated_module_docstring(
  app: object,  # noqa: U100 - the event's signature.
  what: str,
  name: str,
  obj: object,  # noqa: U100
  options: object,  # noqa: U100
  lines: list[str],
) -> None:
  """Drop the generated models module's docstring, a note to maintainers.

  Args:
    app: The Sphinx application.
    what: The kind of object.
    name: Its fully qualified name.
    obj: The object.
    options: The directive's options.
    lines: The docstring's lines, edited in place.
  """
  if what == 'module' and name == 'bw_serve_client._generated.models':
    lines.clear()


def setup(app: object) -> None:
  """Register the public-name check and the docstring filter.

  Args:
    app: The Sphinx application.
  """
  app.connect('env-check-consistency', _check_public_names)  # type: ignore[attr-defined]
  app.connect('autodoc-process-docstring', _drop_generated_module_docstring)  # type: ignore[attr-defined]
