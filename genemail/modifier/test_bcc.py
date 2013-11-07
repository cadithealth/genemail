# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/10
# copy: (C) Copyright 2013 Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, unittest, re
import templatealchemy as ta

from ..manager import Manager
from ..sender import Sender, StoredSender
from .. import util, modifier
from ..test import template

#------------------------------------------------------------------------------
class TestBccModifier(unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def test_bcc(self):
    tpl = 'Hello, {{name}}!'
    manager = Manager(provider = template(tpl, renderer='mustache'),
                      modifier = modifier.BccModifier('bcc@example.com'),
                      sender   = StoredSender(),
                      )
    eml = manager.newEmail()
    eml['name'] = 'Joe Schmoe'
    eml.setHeader('to', 'rcpt@example.com')
    eml.setHeader('from', 'noreply@example.com')
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.includeComponents = ['text']
    eml.send()
    self.assertEqual(1, len(manager.sender.emails))
    out = manager.sender.emails[0]
    self.assertEqual(sorted(out['recipients']), sorted(['rcpt@example.com', 'bcc@example.com']))
    self.assertEqual(out['mailfrom'], 'noreply@example.com')
    self.assertMultiLineEqual(out['message'], '''\
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: rcpt@example.com
Message-ID: <1234567890@@genemail.example.com>
From: noreply@example.com
Subject: Hello, Joe Schmoe!

Hello, Joe Schmoe!
''')

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
