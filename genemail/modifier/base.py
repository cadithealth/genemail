# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/31
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class Modifier(object):

  #----------------------------------------------------------------------------
  def modify(self, mailfrom, recipients, data):
    '''
    Modifies the prepared email for sending.

    :Parameters:

    mailfrom : str
      the SMTP-level `MAILFROM` command argument.

    recipients : { list, tuple }
      an iterable of the SMTP-level `RCPTTO` command arguments.

    data : { str, email.MIMEMessage }
      represents the SMTP-level `DATA` command argument, and can
      either be a subclass of `email.MIMEMessage` or the raw SMTP data
      (as generated by a call to `email.MIMEMessage.as_string()`).

    :Returns:

    tuple
      A three-element tuple with the adjusted `mailfrom`, `recipients`
      and `data` values.
    '''
    raise NotImplementedError()

#------------------------------------------------------------------------------
class ChainingModifier(Modifier):

  #----------------------------------------------------------------------------
  def __init__(self, modifiers=[]):
    self.modifiers = modifiers

  #----------------------------------------------------------------------------
  def addModifier(self, modifier):
    self.modifiers.append(modifier)
    return self

  #----------------------------------------------------------------------------
  def modify(self, mailfrom, recipients, data):
    for mod in self.modifiers:
      mailfrom, recipients, data = mod.modify(mailfrom, recipients, data)
    return (mailfrom, recipients, data)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
