# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# lib:  genemail
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import
import pkg_resources

from .manager import *
from .email import *
from .modifier import *
from .sender import *

class meta():
  @property
  def package(self):
    return pkg_resources.require('genemail')[0]
  @property
  def version(self):
    return self.package.version
meta = meta()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
