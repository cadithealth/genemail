#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/03
# copy: (C) Copyright 2013 Cadit Inc., see LICENSE.txt
#------------------------------------------------------------------------------

import os, sys, re, setuptools
from setuptools import setup, find_packages

# require python 2.7+
if sys.hexversion < 0x02070000:
  raise RuntimeError('This package requires python 2.7 or better')

heredir = os.path.abspath(os.path.dirname(__file__))
def read(*parts, **kw):
  try:    return open(os.path.join(heredir, *parts)).read()
  except: return kw.get('default', '')

test_dependencies = [
  'nose                 >= 1.3.0',
  'coverage             >= 3.5.3',
  'pxml                 >= 0.2.9',
]

dependencies = [
  'TemplateAlchemy      >= 0.1.21',
  'cssutils             >= 0.9.10b1',
  'cssselect            >= 0.7.1',
  'py-dom-xpath         >= 0.1',
  'html2text            >= 3.200.3',
  'globre               >= 0.1.3',
  'asset                >= 0.6.3',
]

extras_dependencies = {
  'pgp'                 : 'python-gnupg >= 0.3.5',
  'dkim'                : 'dkimpy       >= 0.5.4',
}

entrypoints = {
  'console_scripts': [
    'genemail           = genemail.cli:main',
  ],
}

classifiers = [
  'Development Status :: 4 - Beta',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Operating System :: OS Independent',
  'Topic :: Software Development',
  'Natural Language :: English',
  'License :: OSI Approved :: MIT License',
  'License :: Public Domain',
]

setup(
  name                  = 'genemail',
  version               = read('VERSION.txt', default='0.0.1').strip(),
  description           = 'A templated email generation library',
  long_description      = read('README.rst'),
  classifiers           = classifiers,
  author                = 'Philip J Grabner, Cadit Health Inc',
  author_email          = 'oss@cadit.com',
  url                   = 'http://github.com/cadithealth/genemail',
  keywords              = 'template email generation html text smtp',
  packages              = find_packages(),
  include_package_data  = True,
  zip_safe              = True,
  install_requires      = dependencies,
  extras_require        = extras_dependencies,
  tests_require         = test_dependencies,
  test_suite            = 'genemail',
  entry_points          = entrypoints,
  license               = 'MIT (http://opensource.org/licenses/MIT)',
)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
