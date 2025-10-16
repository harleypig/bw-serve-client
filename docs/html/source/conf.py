"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('../../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'bw-serve-client'
copyright = '2025, Alan Young'
author = 'Alan Young'
release = '0.1.1'

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

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
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
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
  'members': True,
  'member-order': 'bysource',
  'special-members': '__init__',
  'undoc-members': True,
  'exclude-members': '__weakref__'
}

# Type hints settings
typehints_fully_qualified = False
typehints_document_rtype = True
typehints_use_rtype = True

# Intersphinx mapping
intersphinx_mapping = {
  'python': ('https://docs.python.org/3/', None),
  'requests': ('https://requests.readthedocs.io/en/latest/', None),
}
