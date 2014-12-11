# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/10
# copy: (C) Copyright 2013 Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, unittest, re, time, pkg_resources
import templatealchemy as ta

from .manager import Manager
from .sender import Sender, StoredSender
from . import util

#------------------------------------------------------------------------------

def eqstrip(val):
  val = val.replace('\r\n', '\n').replace('\r', '\n')
  val = re.sub('[ \t]+', ' ', val)
  return val.strip()

def wsstrip(val):
  return re.sub('\s+', '', val)

def template(s, renderer='mako'):
  return ta.Template(source='string:' + s, renderer=renderer)

#------------------------------------------------------------------------------

def stoptime(at=None):
  if at is None:
    at = time.time()
  at = float(at)
  if not hasattr(time, '__original_time__'):
    time.__original_time__ = time.time
  time.time = lambda: at
  return at

def unstoptime():
  if hasattr(time, '__original_time__'):
    time.time = time.__original_time__

#------------------------------------------------------------------------------

# todo: i should create a class-level decorator version of this too...
def extrafeature(name):
  dist = pkg_resources.get_distribution('genemail')
  for pkg in dist.requires(extras=[name]):
    if not pkg_resources.working_set.find(pkg):
      return unittest.skip('"{}" feature requires package "{}"'.format(name, pkg))
  return lambda func: func

#------------------------------------------------------------------------------
class TestEmail(unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def setUp(self):
    stoptime(1234567890.0) # == 2009-02-13T23:31:30Z 

  #----------------------------------------------------------------------------
  def tearDown(self):
    unstoptime()

  #----------------------------------------------------------------------------
  def assertXmlEqual(self, val, chk):
    if val == chk:
      return self.assertEqual(val, chk)
    if wsstrip(val) == wsstrip(chk):
      return self.assertEqual(wsstrip(val), wsstrip(chk))
    # TODO: make this XML-normalize the values first...
    self.assertMultiLineEqual(eqstrip(val),eqstrip(chk))

  #----------------------------------------------------------------------------
  def assertMimeXmlEqual(self, val, chk):
    if val == chk:
      return self.assertEqual(val, chk)
    if wsstrip(val) == wsstrip(chk):
      return self.assertEqual(wsstrip(val), wsstrip(chk))
    # TODO: make this XML-normalize the XML/HTML values first...
    self.assertMultiLineEqual(eqstrip(val), eqstrip(chk))

  #----------------------------------------------------------------------------
  def test_inlineHtmlStyling(self):
    html = '<html><body><div>foo</div></body></html>'
    css  = 'body{color:red}body > div{font-size:10px}'
    chk  = '''\
<html xmlns="http://www.w3.org/1999/xhtml">
  <body style="color: red">
    <div style="font-size: 10px">foo</div>
  </body>
</html>
'''
    xdoc = util.parseXml(html)
    xdoc = util.inlineHtmlStyling(xdoc, css)
    out  = util.serializeHtml(xdoc)
    self.assertXmlEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_deprecationwarning_workaround(self):
    html = '<html><body><p class="f">first</p><p>second</p></body></html>'
    css  = 'p{background:#666;}p.f{background:#042d5a;}'
    import warnings
    warnings.filterwarnings(
      "error",
      message='Call to deprecated method \'_[sg]etCSSValue\'. Use ``property.propertyValue`` instead.',
      category=DeprecationWarning,
      module='cssutils.css.cssstyledeclaration',
      lineno=598,
    )
    xdoc = util.parseXml(html)
    xdoc = util.inlineHtmlStyling(xdoc, css)
    out  = util.serializeHtml(xdoc)
    self.assertXmlEqual(out, '''\
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <p class="f" style="background: #042d5a">first</p>
    <p style="background: #666">second</p>
  </body>
</html>
''')

  #----------------------------------------------------------------------------
  def test_reduce2ascii_is_needed(self):
    from .util import reduce2ascii as r2a
    self.assertRaises(UnicodeEncodeError,
                      u'this \u21d2 that'.encode,
                      'ascii')
    r2a(u'this \u21d2 that').encode('ascii')

  #----------------------------------------------------------------------------
  def test_reduce2ascii(self):
    from .util import reduce2ascii as r2a
    self.assertEqual(r2a(u'this \u21d2 that'), 'this => that')
    self.assertEqual(r2a(u'this \u2190 that'), 'this <- that')
    self.assertEqual(r2a(u'this \u21e6 that'), 'this <= that')
    self.assertEqual(
      r2a(u'\u2192\u21d2\u21ac\u21c9\u21e8\u21e5\u21e2\u21aa\u21a6\u21f6\u21a3\u21f0\u219d\u21a0\u21fe'),
      '->=>->=>=>->|->->|->=>>->|=>~>->>->')

  #----------------------------------------------------------------------------
  def test_callingPkgName(self):
    from templatealchemy.util import callingPkgName
    self.assertEqual(callingPkgName(), 'genemail')
    self.assertEqual(callingPkgName(ignore='genemail'), 'unittest')

  #----------------------------------------------------------------------------
  def test_subject_element(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title><email:subject share="content">${message.title()}</email:subject></title>
 </head>
 <body>
  <p>${message}.</p>
 </body>
</html>
'''
    chk = 'This Is A Test'
    eml = Manager(sender=StoredSender(), provider=template(tpl)).newEmail()
    eml['message'] = 'This is a test'
    self.assertEqual(eml.getSubject(), chk)
    # TODO: ensure share="content" works... (it doesn't currently...)

  #----------------------------------------------------------------------------
  def test_subject_entities(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title email:subject="content">${message.title()}&nbsp;&mdash;&nbsp;And More!...</title>
 </head>
 <body>
  <h1>Foo &amp; Bar</h1>
  <p>${message}&nbsp;&mdash;&nbsp;and more!...</p>
 </body>
</html>
'''
    schk = 'This & That -- And More!...'
    hchk = '''\
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>This &amp; That&#160;&#8212;&#160;And More!...</title>
  </head>
  <body>
  <h1>Foo &amp; Bar</h1>
  <p>This &amp; that&#160;&#8212;&#160;and more!...</p>
 </body>
</html>
'''
    eml = Manager(sender=StoredSender(), provider=template(tpl)).newEmail()
    eml['message'] = 'This & that'
    self.assertEqual(eml.getSubject(), schk)
    self.assertXmlEqual(eml.getHtml(), hchk)

  #----------------------------------------------------------------------------
  def test_subject_attribute(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title email:subject="content">${message.title()}</title>
 </head>
 <body>
  <p>${message}.</p>
 </body>
</html>
'''
    chk = 'This Is A Test'
    eml = Manager(sender=StoredSender(), provider=template(tpl)).newEmail()
    eml['message'] = 'This is a test'
    self.assertEqual(eml.getSubject(), chk)

  #----------------------------------------------------------------------------
  def test_subject_maxlength(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title><email:subject share="content">${message.title()}</email:subject></title>
 </head>
 <body>
  <p>${message}.</p>
 </body>
</html>
'''
    chk = 'This Is A Test [...]'
    man = Manager(sender=StoredSender(), provider=template(tpl))
    man.default.maxSubjectLength = 20
    eml = man.newEmail()
    eml['message'] = 'This is a test of capping the subject length'
    self.assertEqual(eml.getSubject(), chk)
    chk2 = 'This [...]'
    eml2 = man.newEmail()
    eml2.maxSubjectLength = 10
    eml2['message'] = 'This is a test of capping the subject length'
    self.assertEqual(eml2.getSubject(), chk2)

  #----------------------------------------------------------------------------
  def test_subject_snip(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title><email:subject share="content">${message.title()}</email:subject></title>
 </head>
 <body>
  <p>${message}.</p>
 </body>
</html>
'''
    chk = 'This Is [...snip...]'
    man = Manager(sender=StoredSender(), provider=template(tpl))
    man.default.maxSubjectLength = 20
    man.default.snipIndicator = '[...snip...]'
    eml = man.newEmail()
    eml['message'] = 'This is a test of changing the snip indicator'
    self.assertEqual(eml.getSubject(), chk)

  #----------------------------------------------------------------------------
  def test_simpleEmail_textOnly(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <email:header name="To">test@example.com</email:header>
  <email:header name="From" value="noreply@example.com">this-is-bogus</email:header>
  <email:env name="unused">feedback value</email:env>
  <title email:subject="content">${message.title()}</title>
 </head>
 <body>
  <p>${message}.</p>
  <p>Also sent to: <span email:header="CC">foo@example.com</span>.</p>
 </body>
</html>
'''
    tchk = '''\
This is a test.

Also sent to: foo@example.com.
'''
    etchk = '''\
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
From: noreply@example.com
CC: foo@example.com
To: test@example.com
Date: Fri, 13 Feb 2009 23:31:30 -0000
Message-ID: <1234567890@genemail.example.com>
Subject: This Is A Test\n\n''' + tchk
    hchk = '''\
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>This Is A Test</title>
  </head>
  <body>
  <p>This is a test.</p>
  <p>Also sent to: <span>foo@example.com</span>.</p>
 </body>
</html>
'''
    eml = Manager(sender=StoredSender(), provider=template(tpl)).newEmail()
    # override the UN-predictable generated info...
    eml.setHeader('Message-ID', '<1234567890@genemail.example.com>')
    eml.includeComponents = ['text']
    eml['message'] = 'This is a test'
    eml.send()
    self.assertEqual(len(eml.manager.sender.emails), 1)
    out = eml.manager.sender.emails[0]
    self.assertMultiLineEqual(eml.getText(), tchk)
    self.assertXmlEqual(eml.getHtml(), hchk)
    self.assertMultiLineEqual(out['message'], etchk)
    self.assertEqual(
      sorted(out['recipients']),
      sorted(['test@example.com', 'foo@example.com']))

  #----------------------------------------------------------------------------
  def test_cidCleanup(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <email:header name="To">test@example.com</email:header>
  <email:header name="From" value="noreply@example.com">this-is-bogus</email:header>
  <title email:subject="content">${message.title()}</title>
  <email:attachment name="smiley.png" encoding="base64" cid="true">
   dGhpcyBpcyBhIGJvZ3VzIGltYWdlCg==
  </email:attachment>
 </head>
 <body>
  <p>${message}.</p>
  <p>Also sent to: <span email:header="CC">foo@example.com</span>.</p>
  <p><img alt="smiley" src="cid:smiley.png"/></p>
 </body>
</html>
'''
    chk = '''\
This is a test.

Also sent to: foo@example.com.

[smiley]
'''
    eml = Manager(sender=StoredSender(), provider=template(tpl)).newEmail()
    eml['message'] = 'This is a test'
    self.assertMultiLineEqual(eml.getText(), chk)

  #----------------------------------------------------------------------------
  def test_inlineStyling(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <email:header name="To">test@example.com</email:header>
  <email:header name="From" value="noreply@example.com">this-is-bogus</email:header>
  <title email:subject="content">${message.title()}</title>
<style type="text/css">
p > span { font-weight: bold; }
  </style>
 </head>
 <body>
  <p>${message}.</p>
  <p>Also sent to: <span email:header="CC">foo@example.com</span>.</p>
 </body>
</html>
'''
    tchk = '''\
This is a test.

Also sent to: foo@example.com.
'''
    etchk = '''\
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
From: noreply@example.com
CC: foo@example.com
To: test@example.com
Date: Fri, 13 Feb 2009 23:31:30 -0000
Message-ID: <1234567890@genemail.example.com>
Subject: This Is A Test\n\n''' + tchk
    hchk = '''\
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>This Is A Test</title>
  </head>
  <body>
  <p>This is a test.</p>
  <p>Also sent to: <span style="font-weight: bold">foo@example.com</span>.</p>
 </body>
</html>
'''
    eml = Manager(sender=StoredSender(), provider=template(tpl)).newEmail()
    # override the UN-predictable generated info...
    eml.setHeader('Message-ID', '<1234567890@genemail.example.com>')
    eml.includeComponents = ['text']
    eml['message'] = 'This is a test'
    eml.send()
    #self.assertMultiLineEqual(eml.manager.sender.emails[0]['message'], etchk)
    #self.assertMultiLineEqual(eml.getText(), tchk)
    self.assertXmlEqual(eml.getHtml(), hchk)

  #----------------------------------------------------------------------------
  def test_email_rawSmtp(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <email:header name="To">test@example.com</email:header>
  <email:header name="From" value="noreply@example.com"/>
  <email:attachment name="smiley.png" encoding="base64" cid="true">
   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA
   IGNIUk0AAHolAACAgwAA+f8AAIDpAAB1MAAA6mAAADqYAAAXb5JfxUYAAAK0SURBVHjabJNfaJNX
   GMZ/X/IlaWub1NqWzLY6dYyiKAWxF0MdyC4KgjeObWy72G28EESam93sOlUZA82Nt2OMiWWwQmFg
   BXfVIQ6JqdY0sRi1TZfG/OmX7/vOOXm9KIRU+8KB9+F9zvPAe85jiQidtfrnxJCIJIAphEkBEFkU
   mEdIH774eKOTb3UKFO6emA6E+1LR0c/pHjxGV+wQAG61wNZGhurqAtqvJz/96snMBwK5O8dvxcbO
   Jvo//oJQpBdaLiJqm2SFINCFcuuU83+zWVhIH/3u6aW2wPLvx1KxsTPTw+MXQFdA/Y/oGrScbZtA
   D5YdhdAg2Ht5nZmlnL8/c+KH50kr++v4SDASKx757DKWWgPvFYv35kE0p05PAPDvP/+BZTN5bgoi
   I4gdJ7twDd+pjAa0NolYfALLySO1DNIosJJdZmUpD34T/CYrS3lWsstIo4DUMljNPAMjJ9HKJGyt
   zPk9PV20qllQFRDTXqr47o4XEq8BfhPxXfp6h1DKnLe1Nkcjpoy4b3ZcBhDl7o6VSyQEWptDtlKm
   qRtvwsHWVpv4zdXbAJjczV0xQEtvoJQJ2lqZQrNentgTbrWHeunGDuf3MYDjltDK5AJa6bnN8ltE
   +YjyWXz0st2/fzpnpVIFrcxcQCmTfrnewPguaI8DBw7y4GGRtfUqnuPgOQ5r61UePCwyFAuB9jC+
   y4vXVbQ2aUtE+Oun/tTIgD09vr8Lb+9ZNktFni0/p16vAdDXF+XIaIyP4kPYzQKZ1S1W192ZL1PN
   ZPsrz/7Ye2tsIJQ4vL+f7micQPQTLLt3e/u6QauWw6kUyb2q8qLkpb++7l36IEx/JLunw0FSB/fZ
   DEeD9PcEAKhsGUo1Q2FD4fqt5Lc/q5ld0wjw25VwXCCByJTAJNt5XhRhHkh//4te6+S/GwD2npI7
   ZK15EgAAAABJRU5ErkJggg==
  </email:attachment>
  <title email:subject="content">${message.title()}</title>
 </head>
 <body>
  <p>${message}.</p>
  <p><img alt="smiley" src="cid:smiley.png"/></p>
 </body>
</html>
'''
    schk = 'This And That'
    hchk = '''\
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>This And That</title>
  </head>
  <body>
  <p>This and that.</p>
  <p><img alt="smiley" src="cid:smiley.png"/></p>
 </body>
</html>
'''

    regex = re.compile('.*<email:attachment[^>]*>([^<]*)</email:attachment>.*', re.DOTALL)

    chk = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: test@example.com
Message-ID: <1234567890@genemail.example.com>
From: noreply@example.com
Subject: This And That

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

This and that.

[smiley]


--==genemail.test-alt-2==
Content-Type: multipart/related; boundary="==genemail.test-rel-3=="
MIME-Version: 1.0

--==genemail.test-rel-3==
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>This And That</title>
  </head>
  <body>
  <p>This and that.</p>
  <p><img alt="smiley" src="cid:smiley.png"/></p>
 </body>
</html>

--==genemail.test-rel-3==
Content-Type: image/png; name="smiley.png"
MIME-Version: 1.0
Content-Transfer-Encoding: base64
Content-Disposition: attachment
Content-ID: <smiley.png>

''' + regex.sub('\\1', tpl).replace('   ','').strip() + '''
--==genemail.test-rel-3==--
--==genemail.test-alt-2==--
'''

    eml = Manager(sender=StoredSender(), provider=template(tpl)).newEmail()
    # override the UNpredictable generated info...
    eml.setHeader('Message-ID', '<1234567890@genemail.example.com>')
    eml.boundary = 'genemail.test'
    eml['message'] = 'This and that'
    eml.send()
    self.assertEqual(eml.getSubject(), schk)
    self.assertXmlEqual(eml.getHtml(), hchk)
    self.assertMimeXmlEqual(eml.manager.sender.emails[0]['message'], chk)

  #----------------------------------------------------------------------------
  def test_default_recycling(self):
    tpl1 = '<p xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0">T1 to <span email:header="CC">foo1@example.com</span>.</p>'
    man  = Manager(sender=StoredSender(), provider=template(tpl1))
    eml1 = man.newEmail()
    eml1.setHeader('To', 'test@example.com')
    eml1.setHeader('From', 'noreply@example.com')
    eml1.setHeader('Bcc', 'bcc@example.com')
    eml1.setHeader('Message-ID', '<1234567890@genemail.example.com>')
    eml1.includeComponents = ['text']
    eml1.send()
    self.assertEqual(len(eml1.manager.sender.emails), 1)
    out1 = eml1.manager.sender.emails[-1]
    self.assertEqual(
      sorted(out1['recipients']),
      sorted(['test@example.com', 'foo1@example.com', 'bcc@example.com']))
    eml2 = man.newEmail()
    eml2.setHeader('To', 'test@example.com')
    eml2.setHeader('From', 'noreply@example.com')
    eml2.setHeader('Message-ID', '<2234567890@genemail.example.com>')
    eml2.includeComponents = ['text']
    eml2.send()
    self.assertEqual(len(eml2.manager.sender.emails), 2)
    out2 = eml2.manager.sender.emails[-1]
    self.assertEqual(
      sorted(out2['recipients']),
      sorted(['test@example.com', 'foo1@example.com']))

  #----------------------------------------------------------------------------
  def test_bccHeader(self):
    tpl = '''\
<html
 lang="en"
 xml:lang="en"
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title email:subject="content">${message.title()}</title>
  <email:header name="to">rcpt@example.com</email:header>
  <email:header name="from">mailfrom@example.com</email:header>
 </head>
 <body><p>${message}.</p></body>
</html>
'''
    sender  = StoredSender()
    manager = Manager(sender=sender, provider=template(tpl))
    eml = manager.newEmail()
    eml['message'] = 'test'
    eml.setHeader('BcC', 'bcc@example.com')
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.boundary = 'genemail.test'
    eml.send()
    self.assertEqual(len(sender.emails), 1)
    out = sender.emails[0]
    self.assertEqual(sorted(out.keys()), sorted(['mailfrom', 'recipients', 'message']))
    self.assertEqual(out['mailfrom'], 'mailfrom@example.com')
    self.assertEqual(
      sorted(out['recipients']),
      sorted(['rcpt@example.com', 'bcc@example.com']))

    # ensure that the 'bcc' headers is stripped out of the output
    chk = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0
From: mailfrom@example.com
To: rcpt@example.com
Date: Fri, 13 Feb 2009 23:31:30 -0000
Message-ID: <1234567890@@genemail.example.com>
Subject: Test

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

test.


--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
  <head>
    <title>Test</title>
  </head>
  <body>
    <p>test.</p>
  </body>
</html>

--==genemail.test-alt-2==--
'''
    self.assertMimeXmlEqual(out['message'], chk)

  #----------------------------------------------------------------------------
  def test_noMinimalMime(self):
    tpl = '''\
<html
 lang="en"
 xml:lang="en"
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title email:subject="content">${message.title()}</title>
  <email:header name="to">rcpt@example.com</email:header>
  <email:header name="from">mailfrom@example.com</email:header>
 </head>
 <body><p>${message}.</p></body>
</html>
'''
    manager = Manager(sender=StoredSender(), provider=template(tpl))
    manager.default.minimalMime = False
    eml = manager.newEmail()
    eml['message'] = 'test'
    eml.setHeader('BcC', 'bcc@example.com')
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.boundary = 'genemail.test'
    eml.send()
    self.assertEqual(1, len(manager.sender.emails))
    out = manager.sender.emails[0]
    self.assertEqual(sorted(out.keys()), sorted(['mailfrom', 'recipients', 'message']))
    self.assertEqual(out['mailfrom'], 'mailfrom@example.com')
    self.assertEqual(sorted(out['recipients']), sorted(['rcpt@example.com', 'bcc@example.com']))
    chk = '''\
Content-Type: multipart/mixed; boundary="==genemail.test-mix-1=="
MIME-Version: 1.0
From: mailfrom@example.com
To: rcpt@example.com
Date: Fri, 13 Feb 2009 23:31:30 -0000
Message-ID: <1234567890@@genemail.example.com>
Subject: Test

--==genemail.test-mix-1==
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

test.


--==genemail.test-alt-2==
Content-Type: multipart/related; boundary="==genemail.test-rel-3=="
MIME-Version: 1.0

--==genemail.test-rel-3==
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
  <head>
    <title>Test</title>
  </head>
  <body>
    <p>test.</p>
  </body>
</html>

--==genemail.test-rel-3==--
--==genemail.test-alt-2==--
--==genemail.test-mix-1==--
'''
    self.assertMimeXmlEqual(out['message'], chk)

  #----------------------------------------------------------------------------
  def test_managerBccHeader(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title email:subject="content">${message.title()}</title>
  <email:header name="to">rcpt@example.com</email:header>
  <email:header name="from">mailfrom@example.com</email:header>
 </head>
 <body><p>${message}.</p></body>
</html>
'''
    sender  = StoredSender()
    class MyManager(Manager):
      def updateHeaders(self, emailobj, headers):
        #super(MyManager, self).updateHeaders(emailobj, headers)
        headers['bcc'] = 'bcc@example.com'
    manager = MyManager(sender=sender, provider=template(tpl))
    eml = manager.newEmail()
    eml['message'] = 'test'
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.includeComponents = ['text']
    eml.send()
    self.assertEqual(len(sender.emails), 1)
    out = sender.emails[0]
    self.assertEqual(
      sorted(out['recipients']),
      sorted(['rcpt@example.com', 'bcc@example.com']))

  # TODO: test non-CID attachments...
  # TODO: test CID-cleansing...

  #----------------------------------------------------------------------------
  def test_env_extraction(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <email:header name="To">test@example.com</email:header>
  <email:header name="From" value="noreply@example.com">this-is-bogus</email:header>
  % comment:
-*- spec -*-
settings:
  env-name: feedback env-value
-*- /spec -*-
  % endcomment
  <email:env name="env-name">feedback env-value</email:env>
  <title email:subject="content">${message.title()}</title>
 </head>
 <body>
  <p>${message}.</p>
  <p>Also sent to: <span email:header="CC">foo@example.com</span>.</p>
 </body>
</html>
'''
    eml = Manager(sender=StoredSender(), provider=template(tpl)).newEmail()
    self.assertEqual(eml.getSetting('env-name'), 'feedback env-value')
    self.assertEqual(eml.getSettings(), dict([['env-name', 'feedback env-value']]))

  #----------------------------------------------------------------------------
  def test_standaloneHtml(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <email:header name="To">test@example.com</email:header>
  <email:header name="From">noreply@example.com</email:header>
  <title email:subject="content">${message.title()}</title>
  <email:attachment name="slogan.txt" encoding="base64" cid="true">
    QUxMIFlPVVIgQkFTRSBBUkUgQkVMT05HIFRPIFVT
  </email:attachment>
 </head>
 <body>
  <p>${message} <img src="cid:slogan.txt"/>.</p>
 </body>
</html>
'''
    chk = '''\
'''
    manager = Manager(sender=StoredSender(), provider=template(tpl))
    eml = manager.newEmail()
    eml['message'] = 'Foo the bar'
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.boundary = 'genemail.test'
    eml.send()
    self.assertEqual(len(manager.sender.emails), 1)
    out = manager.sender.emails[0]
    chk = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: test@example.com
Message-ID: <1234567890@@genemail.example.com>
From: noreply@example.com
Subject: Foo The Bar

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Foo the bar [].

--==genemail.test-alt-2==
Content-Type: multipart/related; boundary="==genemail.test-rel-3=="
MIME-Version: 1.0

--==genemail.test-rel-3==
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Foo The Bar</title>
  </head>
  <body>
    <p>Foo the bar <img src="cid:slogan.txt" />.</p>
  </body>
</html>
--==genemail.test-rel-3==
Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment
Content-ID: <slogan.txt>

ALL YOUR BASE ARE BELONG TO US
--==genemail.test-rel-3==--
--==genemail.test-alt-2==--
'''
    self.assertMimeXmlEqual(out['message'], chk)
    chk = '''\
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Foo The Bar</title>
  </head>
  <body>
    <p>Foo the bar <img src="data:text/plain;base64,QUxMIFlPVVIgQkFTRSBBUkUgQkVMT05HIFRPIFVT" />.</p>
  </body>
</html>
'''
    self.assertXmlEqual(eml.getHtml(standalone=True), chk)

  #----------------------------------------------------------------------------
  def test_spec_override(self):
    manager = Manager(
      sender   = StoredSender(),
      provider = ta.Manager(
        source   = 'pkg:genemail:test_data/templates/email',
        renderer = 'mako'),
      # modifier = genemail.DkimModifier(
      #   selector = 'selector._domainkey.example.com',
      #   key      = '/path/to/private-rsa.key',
      # )
    )
    eml = manager.newEmail('invite')
    eml['name'] = 'Joe Schmoe'
    eml['email'] = 'test@example.com'
    eml.addAttachment(
      name        = 'invite.ics',
      value       = '''\
BEGIN:VCALENDAR
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test Invite
END:VEVENT
END:VCALENDAR
''',
      contentType = 'text/calendar; name=invite.ics; method=PUBLISH')
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.boundary = 'genemail.test'
    eml.send()
    self.assertEqual(len(manager.sender.emails), 1)
    out = manager.sender.emails[0]
    chk = '''\
Content-Type: multipart/mixed; boundary="==genemail.test-mix-1=="
MIME-Version: 1.0
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: "Joe Schmoe" <test@example.com>
Message-ID: <1234567890@@genemail.example.com>
From: "Hello World" <noreply@example.com>
Subject: Hello!

--==genemail.test-mix-1==
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Hello Joe Schmoe, please find your invite attached.

--==genemail.test-alt-2==
Content-Type: multipart/related; boundary="==genemail.test-rel-3=="
MIME-Version: 1.0

--==genemail.test-rel-3==
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Hello!</title>
  </head>
  <body>
    <img src="cid:logo.png" />
    <h1>Hello Joe Schmoe!</h1>
    <p>Please find your invite attached. <img src="cid:smiley.png" /></p>
    <img src="cid:sig.png" />
  </body>
  </html>
--==genemail.test-rel-3==
Content-Type: image/png; name="smiley.png"
MIME-Version: 1.0
Content-Transfer-Encoding: base64
Content-Disposition: attachment
Content-ID: <smiley.png>

iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJCAQAAABKmM6bAAAAOElEQVQI12WOQQ4AQAQDpxv//3L3
YJvI6oGgA2E+FVizIZ9OciIUxBf3YemB2TPALhqtns+r2n9d0gAQF+Ohrm4AAAAASUVORK5CYII=
--==genemail.test-rel-3==
Content-Type: image/png; name="logo.png"
MIME-Version: 1.0
Content-Transfer-Encoding: base64
Content-Disposition: attachment
Content-ID: <logo.png>

iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJAQMAAADaX5RTAAAABlBMVEX///8AAABVwtN+AAAAAXRS
TlMAQObYZgAAAAFiS0dEAIgFHUgAAAAgSURBVAjXY6hnYPjPwLCEgUEFjFIYGNIaGJ43MBxmAABI
GwXfd8ROSAAAAABJRU5ErkJggg==
--==genemail.test-rel-3==
Content-Type: image/png; name="sig.png"
MIME-Version: 1.0
Content-Transfer-Encoding: base64
Content-Disposition: attachment
Content-ID: <sig.png>

iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJAQMAAADaX5RTAAAABlBMVEUAAAAAAAClZ7nPAAAAAXRS
TlMAQObYZgAAAB5JREFUCNdj+MDAIMDAIMTAwMjA8L8BRAqBRT4wAAAyoQOmAXy5oQAAAABJRU5E
rkJggg==
--==genemail.test-rel-3==--
--==genemail.test-alt-2==--
--==genemail.test-mix-1==
MIME-Version: 1.0
Content-Type: text/calendar; name="invite.ics"; method="PUBLISH";
 charset="us-ascii"
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="invite.ics"

BEGIN:VCALENDAR
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test Invite
END:VEVENT
END:VCALENDAR

--==genemail.test-mix-1==--
'''
    self.assertMimeXmlEqual(out['message'], chk)

  #----------------------------------------------------------------------------
  def test_email_headersAreCaseInsensitive(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title email:subject="content">${message.title()}</title>
  <email:header name="to">rcpt@example.com</email:header>
  <email:header name="frOM">mailfrom@example.com</email:header>
 </head>
 <body><p>${message}.</p></body>
</html>
'''
    sender  = StoredSender()
    manager = Manager(sender=sender, provider=template(tpl))
    eml = manager.newEmail()
    eml['message'] = 'test'
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.includeComponents = ['text']
    eml.send()
    self.assertEqual(len(sender.emails), 1)
    out = sender.emails[0]
    self.assertEqual(out.recipients, ['rcpt@example.com'])
    self.assertEqual(out.mailfrom, 'mailfrom@example.com')

  #----------------------------------------------------------------------------
  def test_manager_defaultHeaders(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title email:subject="content">${message.title()}</title>
  <email:header name="to">rcpt@example.com</email:header>
 </head>
 <body><p>${message}.</p></body>
</html>
'''
    sender  = StoredSender()
    manager = Manager(
      sender   = sender,
      provider = template(tpl),
      default  = {'headers': {'from': 'mailfrom@example.com'}},
    )
    eml = manager.newEmail()
    eml['message'] = 'test'
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.includeComponents = ['text']
    eml.send()
    self.assertEqual(len(sender.emails), 1)
    out = sender.emails[0]
    self.assertEqual(out.recipients, ['rcpt@example.com'])
    self.assertEqual(out.mailfrom, 'mailfrom@example.com')

  #----------------------------------------------------------------------------
  def test_manager_defaultHeadersCaseInsensitive(self):
    tpl = '''\
<html
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:email="http://pythonhosted.org/genemail/xmlns/1.0"
 >
 <head>
  <title email:subject="content">${message.title()}</title>
  <email:header name="to">rcpt@example.com</email:header>
 </head>
 <body><p>${message}.</p></body>
</html>
'''
    sender  = StoredSender()
    manager = Manager(
      sender   = sender,
      provider = template(tpl),
      default  = {'headers': {'frOM': 'mailfrom@example.com'}},
    )
    eml = manager.newEmail()
    eml['message'] = 'test'
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.includeComponents = ['text']
    self.assertEqual(eml.getHeader('from'), 'mailfrom@example.com')

  #----------------------------------------------------------------------------
  def test_multipass_nocache(self):
    tpl = '<html><body>The count is: ${getCount()}</body></html>'
    manager = Manager(sender=StoredSender(), provider=template(tpl))
    eml = manager.newEmail()
    class Counter():
      def __init__(self): self.count = 0
      def inc(self):
        self.count += 1
        return self.count
    counter = Counter()
    eml['getCount'] = counter.inc
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.boundary = 'genemail.test'
    eml.send(mailfrom='mailfrom@example.com', recipients='rcpt@example.com')
    self.assertEqual(len(manager.sender.emails), 1)
    # TODO: reduce this by caching by "template/genemail_format" ...!!!...
    self.assertEqual(counter.count, 9)
    out = manager.sender.emails[0]

    chk = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0
Date: Fri, 13 Feb 2009 23:31:30 -0000
Message-ID: <1234567890@@genemail.example.com>
Subject: The count is: 3

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

The count is: 5

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html xmlns="http://www.w3.org/1999/xhtml"><body>The count is: 7</body></html>
--==genemail.test-alt-2==--
'''

    self.assertMimeXmlEqual(out['message'], chk)

  #----------------------------------------------------------------------------
  def test_multipass_cache(self):
    tpl = '<html><body>The count is: ${cache.get("c", lambda:getCount())}</body></html>'
    manager = Manager(sender=StoredSender(), provider=template(tpl))
    eml = manager.newEmail()
    class Counter():
      def __init__(self): self.count = 0
      def inc(self):
        self.count += 1
        return self.count
    counter = Counter()
    eml['getCount'] = counter.inc
    # override the UNpredictable generated info...
    eml.setHeader('date', 'Fri, 13 Feb 2009 23:31:30 -0000')
    eml.setHeader('message-id', '<1234567890@@genemail.example.com>')
    eml.boundary = 'genemail.test'
    eml.send(mailfrom='mailfrom@example.com', recipients='rcpt@example.com')
    self.assertEqual(len(manager.sender.emails), 1)
    self.assertEqual(counter.count, 1)
    out = manager.sender.emails[0]

    chk = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0
Date: Fri, 13 Feb 2009 23:31:30 -0000
Message-ID: <1234567890@@genemail.example.com>
Subject: The count is: 1

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

The count is: 1

--==genemail.test-alt-2==
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html xmlns="http://www.w3.org/1999/xhtml"><body>The count is: 1</body></html>
--==genemail.test-alt-2==--
'''
    self.assertMimeXmlEqual(out['message'], chk)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
