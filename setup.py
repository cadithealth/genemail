#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/03
# copy: (C) Copyright 2013 Cadit Inc., see LICENSE.txt
#------------------------------------------------------------------------------

import os, sys, re
from setuptools import setup, find_packages

# require python 2.7+
assert(sys.version_info[0] > 2
       or sys.version_info[0] == 2
       and sys.version_info[1] >= 7)

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

test_requires = [
  'nose                 >= 1.2.1',
  'coverage             >= 3.5.3',
  ]

requires = [
  'TemplateAlchemy      >= 0.1.14',
  'cssutils             >= 0.9.10b1',
  'cssselect            >= 0.7.1',
  'py-dom-xpath         >= 0.1',
  'html2text            >= 3.200.3',
  'dkimpy               >= 0.5.4',
  'dnspython            >= 1.11.0',
  ]

entrypoints = {
  'console_scripts': [
    'genemail           = genemail.cli:main',
    ],
  }

setup(
  name                  = 'genemail',
  version               = '0.1.3',
  description           = 'A templated email generation library',
  long_description      = README,
  classifiers           = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Programming Language :: Python',
    'Operating System :: OS Independent',
    'Topic :: Software Development',
    'Natural Language :: English',
    'License :: OSI Approved :: MIT License',
    'License :: Public Domain',
    ],
  author                = 'Philip J Grabner, Cadit Health Inc',
  author_email          = 'oss@cadit.com',
  url                   = 'http://github.com/cadithealth/genemail',
  keywords              = 'template email generation html text smtp',
  packages              = find_packages(),
  namespace_packages    = ['genemail'],
  include_package_data  = True,
  zip_safe              = True,
  install_requires      = requires,
  tests_require         = test_requires,
  test_suite            = 'genemail',
  entry_points          = entrypoints,
  license               = 'MIT (http://opensource.org/licenses/MIT)',
  )

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
