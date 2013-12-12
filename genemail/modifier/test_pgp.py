# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/11/07
# copy: (C) Copyright 2013 Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import os, sys, unittest, re
import templatealchemy as ta

from .. import testing
from ..manager import Manager
from ..sender import StoredSender
from ..test import template, stoptime, unstoptime, extrafeature
from .pgp import PgpModifier

moddir = os.path.dirname(os.path.dirname(__file__))

#------------------------------------------------------------------------------
class TestPgpModifier(unittest.TestCase, testing.EmailTestMixin):

  maxDiff = None

  encEmail = '''\
MIME-Version: 1.0
Content-Type: multipart/encrypted; protocol=application/pgp-encrypted; boundary="==BNDRY=="
Content-Transfer-Encoding: 7bit
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: receiver@example.com, the-nsa@example.com
Message-ID: <1234567890@genemail.example.com>
From: sender@example.com
Subject: Hello, Joe Schmoe!

--==BNDRY==
MIME-Version: 1.0
Content-Type: application/pgp-encrypted

Version: 1

--==BNDRY==
Content-Type: application/octet-stream
MIME-Version: 1.0

-----BEGIN PGP MESSAGE-----
Version: GnuPG v1.4.11 (GNU/Linux)

hIwDPf0Efz9KxdABBACt1HKG6E+ONo1CvvH9fAbgyeEBI0yW7IqSIXewU7Il3odJ
fmgX5eQUP/HE/Jf+XsLaLZ0IZq/Jcn5hD1JzNdDStc9Kk9ry3Dwq3WTwLy4Gq6Ji
QEqYKxvUEx/VFqHfo68XiFJTDl9HrIXMeIoV0oQrirF1xkXFo88LuoPGUmAixNLA
UQHrgiKqP142RWT1KUXJzgIFhM95em25wkcdhLuAsJJG/a4fwT9gzL0hhCMnmwce
yHdCpen7umdclaHvoZKNczrhPNLRt/X3IJlyztqTsJS4iavRO+usQRP/KNjtxlZE
m9j7uLcGH8lUXgnd4hChFWojV0BLpR6tRIaGLPWeopx331BBTz9CzeIjgJGJnYvy
8aBqjQoNiq1aEYM9DQX/QjsCqjlooPvBHJNKVbeTUszPQIh+wFqj0sUcXLsMwq4F
bUFQLIiSDzveKLsDJVt+2iAvaSNs/WAjtunmCd4qXKb4F0RXKPit+0Gks3XLDB6L
vJdCbGtFxl8NNYfL4g4FiCTMt7GgumGw7kz4C6V7CTaoDQ==
=ip5F
-----END PGP MESSAGE-----

--==BNDRY==--
'''

  #----------------------------------------------------------------------------
  def setUp(self):
    stoptime(1234567890.0) # == 2009-02-13T23:31:30Z 

  #----------------------------------------------------------------------------
  def tearDown(self):
    unstoptime()

  #----------------------------------------------------------------------------
  @extrafeature('pgp')
  def test_defaults(self):
    tpl = 'Hello, {{name}}!'
    pgpmod = PgpModifier(
      gpg_options=dict(
        gnupghome=os.path.join(moddir, 'test_data', 'gpg-sender')
        )
      )
    manager = Manager(provider = template(tpl, renderer='mustache'),
                      modifier = pgpmod,
                      sender   = StoredSender(),
                      )
    eml = manager.newEmail()
    eml['name'] = 'Joe Schmoe'
    eml.setHeader('to', 'receiver@example.com, the-nsa@example.com')
    eml.setHeader('from', 'sender@example.com')
    # override the UNpredictable generated info...
    eml.setHeader('message-id', '<1234567890@genemail.example.com>')
    eml.includeComponents = ['text']
    eml.send()
    self.assertEqual(1, len(manager.sender.emails))
    out = manager.sender.emails[0]
    chk = self.encEmail
    self.registerMimeComparator('application/octet-stream', self.assertEncryptedEmailEqual_defaults)
    self.assertEmailEqual(out['message'], chk)
    self.assertEqual(out['recipients'], ['receiver@example.com', 'the-nsa@example.com'])

    # TODO: validate that the email is:
    #   - signed
    #   - encrypted to both receiver and sender
    #   - not encrypted for anyone else

  #----------------------------------------------------------------------------
  def assertEncryptedEmailEqual_defaults(self, a, b, msg=None):
    import gnupg
    gpg = gnupg.GPG(gnupghome=os.path.join(moddir, 'test_data', 'gpg-receiver'))
    adec = gpg.decrypt(a)
    if not adec.ok:
      self.fail('could not decrypt message: ' + a)
    bdec = gpg.decrypt(b)
    if not bdec.ok:
      self.fail('could not decrypt message: ' + b)
    self.assertEmailEqual(str(adec), str(bdec), msg=msg)

  #----------------------------------------------------------------------------
  @extrafeature('pgp')
  def test_prune_recipients(self):
    tpl = 'Hello, {{name}}!'
    pgpmod = PgpModifier(
      prune_keys=True,
      prune_recipients=True,
      gpg_options=dict(
        gnupghome=os.path.join(moddir, 'test_data', 'gpg-sender')
        )
      )
    manager = Manager(provider = template(tpl, renderer='mustache'),
                      modifier = pgpmod,
                      sender   = StoredSender(),
                      )
    eml = manager.newEmail()
    eml['name'] = 'Joe Schmoe'
    eml.setHeader('to', 'receiver@example.com, the-nsa@example.com')
    eml.setHeader('from', 'sender@example.com')
    # override the UNpredictable generated info...
    eml.setHeader('message-id', '<1234567890@genemail.example.com>')
    eml.includeComponents = ['text']
    eml.send()
    self.assertEqual(1, len(manager.sender.emails))
    out = manager.sender.emails[0]
    msg = out['message']
    chk = self.encEmail.replace(', the-nsa@example.com', '')
    self.registerMimeComparator('application/octet-stream', self.assertEncryptedEmailEqual_prune)
    self.assertEmailEqual(out['message'], chk)
    self.assertEqual(out['recipients'], ['receiver@example.com'])

  #----------------------------------------------------------------------------
  def assertEncryptedEmailEqual_prune(self, a, b, msg=None):
    import gnupg
    gpg = gnupg.GPG(gnupghome=os.path.join(moddir, 'test_data', 'gpg-receiver'))
    adec = gpg.decrypt(a)
    if not adec.ok:
      self.fail('could not decrypt message: ' + a)
    chk = '''\
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: receiver@example.com
Message-ID: <1234567890@genemail.example.com>
From: sender@example.com
Subject: Hello, Joe Schmoe!

Hello, Joe Schmoe!
'''
    self.assertEmailEqual(str(adec), chk, msg=msg)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
