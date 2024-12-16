# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


import os
import sys

import django
from sphinx.builders.html import StandaloneHTMLBuilder

sys.path.insert(0, os.path.join(os.path.abspath('.'), '../../backend'))  # noqa : to fix the following imports

from MrMap import VERSION
from MrMap.settings import LOG_DIR

os.environ['DJANGO_SETTINGS_MODULE'] = 'MrMap.settings'


# Get an instance of a logger

# create log dir if it does not exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

django.setup()

import sphinx_rtd_theme  # noqa

# -- Project information -----------------------------------------------------

project = 'MrMap'
copyright = '2021, mrmap-community'
author = 'mrmap-community'

# The full version, including alpha/beta/rc tags
release = VERSION


user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
    'sphinx_multiversion',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".

# html_static_path = ['_static']

linkcheck_timeout = 30

linkcheck_ignore = [r'http://localhost\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)', r'https://localhost\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)', r'http://127.0.0.1\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
                    r'https://127.0.0.1\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)', r'http://YOUR-IP-ADDRESS\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)', ]

linkcheck_request_headers = {
    "*": {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; '
          'rv:24.0) Gecko/20100101 Firefox/24.0'}
}

master_doc = "index"

# to get docstrings from django code, the django project needs to setup fist

StandaloneHTMLBuilder.supported_image_types = [
    'image/svg+xml',
    'image/gif',
    'image/png',
    'image/jpeg'
]


smv_tag_whitelist = r'^v\d+\.\d+$'                # Include tags like "v2.1"
# smv_branch_whitelist = r'^develop$'              # Include develop branch
smv_branch_whitelist = r'^armin1$'   
# Use branches from all remotes
smv_remote_whitelist = None