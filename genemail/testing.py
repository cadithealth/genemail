# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/21
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

# todo: this could be smarter... for example, it could:
#       - detect when references resolve to the same content, but
#         by different Content-IDs
#       - detect when multipart sections could collapse to the same
#         semantic structure

from __future__ import absolute_import
import unittest, email

from .util import smtpHeaderFormat

#------------------------------------------------------------------------------
def canonicalHeaders(message, ignore=None):
  '''
  Returns a canonical string representation of the `message` headers,
  with the following changes made:

  * The MIME boundary specified in the "Content-Type" header, if
    specified, removed.

  * Any headers listed in `ignore` are removed.

  :Parameters:

  ignore : list(str), optional, default: ['Content-Transfer-Encoding']
    List of headers that should not be included in the canonical
    form.
  '''
  if ignore is None:
    ignore = ['Content-Transfer-Encoding']
  ignore = [key.lower() for key in ignore]
  hdrs = {key.lower(): '; '.join(sorted(message.get_all(key)))
          for key in message.keys()
          if key.lower() not in ignore}
  hdrs['content-type'] = '; '.join(['='.join(filter(None, pair))
                                    for pair in message.get_params()
                                    if pair[0].lower() != 'boundary'])
  return '\n'.join([
    smtpHeaderFormat(key) + ': ' + hdrs[key]
    for key in sorted(hdrs.keys())]) + '\n'

#------------------------------------------------------------------------------
def canonicalStructure(message):
  ret = message.get_content_type() + '\n'
  if not message.is_multipart():
    return ret
  msgs = message.get_payload()
  for idx, msg in enumerate(msgs):
    last = idx + 1 >= len(msgs)
    indent = '\n|-- ' if not last else '\n    '
    ret += '|-- ' if not last else '`-- '
    ret += indent.join(canonicalStructure(msg)[:-1].split('\n')) + '\n'
  return ret

#------------------------------------------------------------------------------
def makemsg(msg, submsg):
  if msg is None:
    return submsg
  return msg + ' (' + submsg + ')'

#------------------------------------------------------------------------------
class EmailTestMixin(object):

  mime_cmp_factories = {
    'text/html'      : lambda self, ct: self.try_assertXmlEqual,
    'text/xml'       : lambda self, ct: self.try_assertXmlEqual,
    'text/*'         : lambda self, ct: self.assertMultiLineEqual,
    '*/*'            : lambda self, ct: self.assertEqual,
    }

  #----------------------------------------------------------------------------
  def registerMimeComparator(self, mimetype, comparator):
    def factory(self, ct):
      return comparator
    self.mime_cmp_factories = dict(EmailTestMixin.mime_cmp_factories)
    self.mime_cmp_factories[mimetype] = factory

  #----------------------------------------------------------------------------
  def _parseEmail(self, eml):
    return email.message_from_string(eml)

  #----------------------------------------------------------------------------
  def assertEmailHeadersEqual(self, eml1, eml2, msg=None):
    eml1 = self._parseEmail(eml1)
    eml2 = self._parseEmail(eml2)
    self._assertEmailHeadersEqual(eml1, eml2, msg=msg)

  #----------------------------------------------------------------------------
  def assertNotEmailHeadersEqual(self, eml1, eml2, msg=None):
    try:
      self.assertEmailHeadersEqual(eml1, eml2, msg=msg)
      self.fail(msg or 'email headers %r == %r' % (eml1, eml2))
    except AssertionError: pass

  #----------------------------------------------------------------------------
  def assertEmailStructureEqual(self, eml1, eml2, msg=None):
    eml1 = self._parseEmail(eml1)
    eml2 = self._parseEmail(eml2)
    self._assertEmailStructureEqual(eml1, eml2, msg=msg)

  #----------------------------------------------------------------------------
  def assertNotEmailStructureEqual(self, eml1, eml2, msg=None):
    try:
      self.assertEmailStructureEqual(eml1, eml2, msg=msg)
      self.fail(msg or 'email structure %r == %r' % (eml1, eml2))
    except AssertionError: pass

  #----------------------------------------------------------------------------
  def assertEmailContentEqual(self, eml1, eml2, msg=None, mime_cmp_factories=None):
    eml1 = self._parseEmail(eml1)
    eml2 = self._parseEmail(eml2)
    self._assertEmailContentEqual(eml1, eml2, msg=msg, mcf=mime_cmp_factories)

  #----------------------------------------------------------------------------
  def assertNotEmailContentEqual(self, eml1, eml2, msg=None):
    try:
      self.assertEmailContentEqual(eml1, eml2, msg=msg)
      self.fail(msg or 'email content %r == %r' % (eml1, eml2))
    except AssertionError: pass

  #----------------------------------------------------------------------------
  def assertEmailEqual(self, eml1, eml2, msg=None, mime_cmp_factories=None):
    eml1 = self._parseEmail(eml1)
    eml2 = self._parseEmail(eml2)
    self._assertEmailHeadersEqual(eml1, eml2, msg=msg)
    self._assertEmailStructureEqual(eml1, eml2, msg=msg)
    self._assertEmailContentEqual(eml1, eml2, msg=msg, mcf=mime_cmp_factories)

  #----------------------------------------------------------------------------
  def assertNotEmailEqual(self, eml1, eml2, msg=None, mime_cmp_factories=None):
    try:
      self.assertEmailEqual(eml1, eml2, msg=msg, mime_cmp_factories=mime_cmp_factories)
      self.fail(msg or 'email %r == %r' % (eml1, eml2))
    except AssertionError: pass

  #----------------------------------------------------------------------------
  def _assertEmailHeadersEqual(self, msg1, msg2, msg=None):
    hdr1 = 'EMAIL HEADERS:\n' + canonicalHeaders(msg1)
    hdr2 = 'EMAIL HEADERS:\n' + canonicalHeaders(msg2)
    self.assertMultiLineEqual(hdr1, hdr2, msg=msg)

  #----------------------------------------------------------------------------
  def _assertEmailStructureEqual(self, msg1, msg2, msg=None):
    str1 = 'EMAIL STRUCTURE:\n' + canonicalStructure(msg1)
    str2 = 'EMAIL STRUCTURE:\n' + canonicalStructure(msg2)
    self.assertMultiLineEqual(str1, str2, msg=msg)

  #----------------------------------------------------------------------------
  def _assertEmailContentEqual(self, msg1, msg2, msg=None, mcf=None, context=None):
    if context is None:
      context = 'component root'
    self.assertEqual(
      msg1.is_multipart(), msg2.is_multipart(),
      msg=makemsg(msg, context + ' is not multipart similar'))
    self.assertEqual(
      msg1.get_content_type(), msg2.get_content_type(),
      msg=makemsg(msg, context + ' has content-type mismatch'))
    if context == 'component root':
      context = 'component ' + msg1.get_content_type()
    if not msg1.is_multipart():
      return self._assertEmailPayloadEqual(
        msg1, msg2, msg=msg, mcf=mcf, context=context)
    msgs1 = msg1.get_payload()
    msgs2 = msg2.get_payload()
    self.assertEqual(
      len(msgs1), len(msgs2),
      msg=makemsg(msg, context + ' has sub-message count mismatch'))
    for idx, submsg in enumerate(msgs1):
      sctxt = context + '[' + str(idx) + '] > ' + submsg.get_content_type()
      self._assertEmailContentEqual(
        submsg, msgs2[idx], msg=msg, mcf=mcf, context=sctxt)

  #----------------------------------------------------------------------------
  def _assertEmailPayloadEqual(self, msg1, msg2, msg=None, mcf=None, context='message'):
    # paranoia...
    self.assertFalse(msg1.is_multipart() or msg2.is_multipart())
    self.assertEqual(msg1.get_content_type(), msg2.get_content_type())
    # /paranoia...
    dat1 = msg1.get_payload(decode=True)
    dat2 = msg2.get_payload(decode=True)
    def getcmp(msg, mcf):
      ret = mcf.get(msg.get_content_type())
      if ret is None:
        ret = mcf.get(msg.get_content_maintype() + '/*')
      if ret is None:
        ret = mcf.get('*/*')
      return ret
    pcmp = None
    if mcf is not None:
      pcmp = getcmp(msg1, mcf)
    if pcmp is None:
      pcmp = getcmp(msg1, self.mime_cmp_factories)
    self.assertIsNotNone(
      pcmp, 'no comparator for mime-type "%s"' % (msg1.get_content_type(),))
    pcmp = pcmp(self, msg1.get_content_type())
    try:
      pcmp(dat1, dat2)
    except AssertionError as err:
      raise AssertionError(
        makemsg(msg, context + ' has different payload') + '; ' + err.message)

  #----------------------------------------------------------------------------
  def try_assertXmlEqual(self, dat1, dat2, msg=None):
    if hasattr(self, 'assertXmlEqual'):
      return self.assertXmlEqual(dat1, dat2)
    return self.assertMultiLineEqual(dat1, dat2)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
