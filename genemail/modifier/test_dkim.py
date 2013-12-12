# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/10
# copy: (C) Copyright 2013 Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

import sys, unittest, re
import templatealchemy as ta

from ..manager import Manager
from ..sender import StoredSender
from .. import util, modifier, testing
from ..test import template, stoptime, unstoptime, extrafeature

#------------------------------------------------------------------------------
class TestDkimModifier(unittest.TestCase, testing.EmailTestMixin):

  maxDiff = None

  #----------------------------------------------------------------------------
  def setUp(self):
    stoptime(1234567890.0) # == 2009-02-13T23:31:30Z

  #----------------------------------------------------------------------------
  def tearDown(self):
    unstoptime()

  #----------------------------------------------------------------------------
  @extrafeature('dkim')
  def test_dkim(self):
    tpl = 'Hello, {{name}}!'
    dkimmod = modifier.DkimModifier(
      privateKey = '''\
-----BEGIN RSA PRIVATE KEY-----
MIIBOgIBAAJBAM3tYc678cHyJdmBCoQyqIHv9+eCksiAvc19zNlaDMkVKtk2/yae
8LLSAyf4B4CG1c18HyAv0lS6UeGDzLqk5bMCAwEAAQJAMLp/boAi0RYPxsw2RNoH
7ddu/iVzvmZYg4vFMZmRdPNUaDgJSuPGR1CawTeXwTP+IZuMQHLVDEiVN7g4KSIp
oQIhAPYEF/OWK93cEqGW9fdHlvMwRLekuVciXkypoSESKpZvAiEA1kjMnT7AkvPz
k7gw/rYRo0O3q7EYOylrHde4rVpCZv0CIFp10uDMnUCtBWTJf5P3jPfLDdmBBm2V
w5ro3MiuR16dAiEAp5SVWKA70HEyW6MfxgMzdgA+gupjrdjtaZBMYF4HMi0CIDcs
ZZ1QMmhqF106XrQeSToj+xD2C8INmZh5HyzQJi6h
-----END RSA PRIVATE KEY-----
''',
      domain = 'example.com',
      selector = '20130731v1',
      )
    manager = Manager(provider = template(tpl, renderer='mustache'),
                      modifier = dkimmod,
                      sender   = StoredSender(),
                      )
    eml = manager.newEmail()
    eml['name'] = 'Joe Schmoe'
    eml.setHeader('to', 'rcpt@example.com')
    eml.setHeader('from', 'noreply@example.com')
    # override the UNpredictable generated info...
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.includeComponents = ['text']
    eml.send()
    self.assertEqual(1, len(manager.sender.emails))
    out = manager.sender.emails[0]

    self.assertRegexpMatches(out['message'], '''\
^DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/simple; d=example\.com; i=@example\.com; \r
 q=dns/txt; s=20130731v1; t=\d{1,11}; h=MIME-Version : Content-Type : \r
 Content-Transfer-Encoding : Date : To : Message-ID : From : Subject : \r
 Date : From : Subject; bh=J5dIdGf2WyNWDpPJz50a\+Olx8RJYoHCRY7ckDZ4gT84=; \r
 b=[0-9a-zA-Z=+/\r\n ]{85,}\r
MIME-Version: 1\.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: rcpt@example\.com
Message-ID: <1234567890@@genemail\.example\.com>
From: noreply@example\.com
Subject: Hello, Joe Schmoe!

Hello, Joe Schmoe!$''')

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
