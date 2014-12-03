# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# lib:  genemail.sender
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

'''
The low-level mail sending agent. Used by the manager to delegate the
actual sending of the composed email. Note that the primary reason to
use a delegated object for this (rather than just using
smtplib.SMTP()) is so that an email can be serialized into another
form, such as for entry into a database or for unit testing and
comparison.
'''

from __future__ import absolute_import

__all__ = ('Sender', 'StoredSender', 'SmtpSender', 'DebugSender')

import smtplib
import email.parser

from templatealchemy.util import adict

#------------------------------------------------------------------------------
class Sender(object):
  '''
  Abstract interface for an object capable of sending a genemail email
  out, usually to an SMTP MTA.
  '''

  #----------------------------------------------------------------------------
  def send(self, mailfrom, recipients, message):
    '''
    Sends the specified `message` (in SMTP format) to the specified
    `recipients` coming from the email address `mailfrom`. Parameters:

    :Parameters:

    mailfrom : str
      equivalent to the the SMTP ``MAIL FROM`` command.

    recipients : list(str)
      equivalent to the SMTP ``RCPT TO`` command.

    message : str
      the actuall message to be transferred, equivalent to the payload of
      the SMTP ``DATA`` command.
    '''
    raise NotImplementedError()

#------------------------------------------------------------------------------
class SmtpSender(Sender):
  '''
  An implementation of the :class:`genemail.sender.Sender` interface that
  connects to a local or remote SMTP server and submits the message for
  transfer or delivery.

  :Parameters:

  host : str, optional, default: 'localhost'
    the SMTP server to connect to.

  port : int, optional, default: 25
    the SMTP server port to connect to.

  ssl : bool, optional, default: false
    indicates whether or not to connect using SSL.

  starttls : bool, optional, default: false
    indicates that a STARTTLS command should be sent after connecting.

  username : str, optional
    set the SMTP username to authenticate as.

  password : str, optional
    set the password for the `username`.
  '''

  #----------------------------------------------------------------------------
  def __init__(self,
               host='localhost', port=25, ssl=False, starttls=False,
               username=None, password=None, *args, **kwargs):
    super(SmtpSender, self).__init__(*args, **kwargs)
    self.smtpHost = host or 'localhost'
    self.smtpPort = port or 25
    self.username = username
    self.password = password
    self.starttls = starttls
    self.ssl      = ssl

  #----------------------------------------------------------------------------
  def send(self, mailfrom, recipients, message):
    smtp = smtplib.SMTP_SSL() if self.ssl else smtplib.SMTP()
    smtp.connect(self.smtpHost, self.smtpPort)
    if self.starttls:
      smtp.starttls()
    if self.username is not None:
      smtp.login(self.username, self.password)
    smtp.sendmail(mailfrom, recipients, message)
    smtp.quit()

#------------------------------------------------------------------------------
class StoredSender(Sender):
  '''
  An implementation of the :class:`genemail.sender.Sender` interface
  that simply stores all messages in local memory in the
  :attr:`emails` attribute. Most useful when unit testing email
  generation.
  '''

  #----------------------------------------------------------------------------
  def __init__(self, *args, **kwargs):
    super(StoredSender, self).__init__(*args, **kwargs)
    self.emails = []

  #----------------------------------------------------------------------------
  def send(self, mailfrom, recipients, message):
    self.emails.append(
      adict(mailfrom=mailfrom, recipients=recipients, message=message))

#------------------------------------------------------------------------------
class DebugSender(StoredSender):
  '''
  An extension to the :class:`StoredSender` class that parses each
  email into it's MIME components, which simplifies unittesting. Each
  element in the `emails` attribute has the following attributes:

  * `mailfrom`:   SMTP-level `MAIL FROM` value (string)
  * `recipients`: SMTP-level `RCPT TO` value (list)
  * `message`:    raw SMTP `DATA` value (string)
  * `mime`:       the parsed :class:`email.message.Message` object
  * `from`:       email "From" header - not used by SMTP
  * `to`:         email "To" header - not used by SMTP
  * `date`:       email "Date" header
  * `message-id`: email "Message-ID" header
  * `subject`:    email "Subject" header
  * `plain`:      text/plain version of the email (or None)
  * `html`:       text/html version of the email (or None)
  * `calendar`:   text/calendar attachment of the email (or None)
  '''

  #----------------------------------------------------------------------------
  def send(self, mailfrom, recipients, message):
    eml = adict(mailfrom=mailfrom, recipients=recipients, message=message)
    mime = email.parser.Parser().parsestr(message)
    eml['mime']        = mime
    eml['from']        = mime.get('from')
    eml['to']          = mime.get('to')
    eml['date']        = mime.get('date')
    eml['message-id']  = mime.get('message-id')
    eml['subject']     = mime.get('subject')
    for part in mime.walk():
      ct = part.get_content_type()
      if not ct.startswith('text/'):
        continue
      ct = ct.split('/')[1]
      if eml.get(ct) is None:
        eml[ct] = part.get_payload()
      elif isinstance(eml[ct], list):
        eml[ct].append(part.get_payload())
      else:
        eml[ct] = [eml[ct], part.get_payload()]
    self.emails.append(eml)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
