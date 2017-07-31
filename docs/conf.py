#!/usr/bin/env python3
# -*- coding: utf-8 -*-

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.todo',
              'sphinx.ext.viewcode',
              'sphinx.ext.githubpages',
              'sphinx.ext.napoleon',
              'sphinx.ext.intersphinx']

templates_path = ['_templates']

source_suffix = '.rst'
master_doc = 'index'

project = 'bare68k'
copyright = '2017, Christian Vogelgsang'
author = 'Christian Vogelgsang'

# will be set by setup.py
version = '0.0'
release = '0.0.0'

language = None
exclude_patterns = []
pygments_style = 'sphinx'

todo_include_todos = True

intersphinx_mapping = {'python': ('https://docs.python.org/3.6', None)}

# html
html_theme = 'sphinx_rtd_theme'
#html_theme = 'alabaster'
# html_sidebars = {
#    '**': [
#        'about.html',
#        'navigation.html',
#        'relations.html',  # needs 'show_related': True theme option to display
#        'searchbox.html',
#        'donate.html',
#    ]
#}

# html help
htmlhelp_basename = 'bare68kdoc'

# latex options
latex_elements = {
}
latex_documents = [
    (master_doc, 'bare68k.tex', 'bare68k Documentation',
     'Christian Vogelgsang', 'manual'),
]

# man page
man_pages = [
    (master_doc, 'bare68k', 'bare68k Documentation',
     [author], 1)
]

# texinfo
texinfo_documents = [
    (master_doc, 'bare68k', 'bare68k Documentation',
     author, 'bare68k', 'One line description of project.',
     'Miscellaneous'),
]
