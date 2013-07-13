# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# lib:  genemail.manager
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

__all__ = ('Manager',)

from templatealchemy.util import adict, callingPkgName
from . import sender as sendermod
from . import email

#------------------------------------------------------------------------------
class Manager(object):

  #----------------------------------------------------------------------------
  def __init__(self, provider=None, sender=None):
    '''
    A ``genemail.manager.Manager`` object is the main clearinghouse
    for generating templatized emails. The main objective is that it
    provides access to :class:`genemail.email.Email` objects.

    :Parameters:

    provider : TemplateAlchemy.Template, optional
      the template provider; if not specified, defaults to loading a
      `pkg` provider in the calling package's namespace.

    sender : :class:`genemail.sender.Sender`, optional
      the email sending agent; if not specified, defaults to a
      SmtpSender with default parameters.
    '''
    self.provider = provider
    if not self.provider:
      self.provider = TA.Template(
        source='pkg:%s:' % (callingPkgName(ignore='genemail'),))
    self.sender   = sender or sendermod.SmtpSender()
    self.default  = email.Email(self, None)

  #----------------------------------------------------------------------------
  def newEmail(self, name=None):
    return email.Email(self, name, default=self.default)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
