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

import templatealchemy as TA
from templatealchemy.util import adict, callingPkgName
from . import sender as sendermod
from . import email

#------------------------------------------------------------------------------
class Manager(object):

  #----------------------------------------------------------------------------
  def __init__(self, provider=None, modifier=None, sender=None):
    '''
    A ``genemail.manager.Manager`` object is the main clearinghouse
    for generating templatized emails. The main objective is that it
    provides access to :class:`genemail.email.Email` objects.

    :Parameters:

    provider : TemplateAlchemy.Template, optional
      the template provider; if not specified, defaults to loading a
      `pkg` provider in the calling package's namespace.

    modifier : :class:`genemail.modifier.Modifier`, optional
      an email modifier, generally used for post-generation email
      adjustment, such as always adding a blind-copy recipient
      (equivalent to adding a BCC header) or adding cryptographic
      signature headers or content with DKIM or GPG.

    sender : :class:`genemail.sender.Sender`, optional
      the email sending agent; if not specified, defaults to a
      SmtpSender with default parameters.
    '''
    self.provider = provider
    if not self.provider:
      self.provider = TA.Template(
        source='pkg:%s:' % (callingPkgName(ignore='genemail'),))
    self.modifier = modifier or None
    self.sender   = sender or sendermod.SmtpSender()
    self.default  = email.Email(self, None)

  #----------------------------------------------------------------------------
  def newEmail(self, name=None, provider=None):
    return email.Email(self, name, provider=provider, default=self.default)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
