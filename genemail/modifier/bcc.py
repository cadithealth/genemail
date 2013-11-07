# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/31
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from .base import Modifier

#------------------------------------------------------------------------------
class BccModifier(Modifier):

  #----------------------------------------------------------------------------
  def __init__(self, bcc):
    self.bcc = bcc

  #----------------------------------------------------------------------------
  def modify(self, mailfrom, recipients, data):
    if self.bcc in recipients:
      return (mailfrom, recipients, data)
    return (mailfrom, tuple(recipients) + (self.bcc,), data)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
