# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/22
# copy: (C) Copyright 2013 Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, unittest
try:
  import pxml
except ImportError:
  pxml = None

from .testing import EmailTestMixin

#------------------------------------------------------------------------------
class TestEmailMixin(EmailTestMixin, unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def setUp(self):
    super(TestEmailMixin, self).setUp()
    self.noxml = False

  #----------------------------------------------------------------------------
  def test_mixin_headers_same(self):
    eml1 = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: test@example.com
Message-ID: <1234567890@@genemail.example.com>
From: noreply@example.com
Subject: Foo The Bar

--==genemail.test-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

CONTENT
--==genemail.test-alt-2==
'''
    eml2 = '''\
date: Fri, 13 Feb 2009 23:31:30 -0000
subject: Foo The Bar
from: noreply@example.com
mime-version: 1.0
to: test@example.com
content-type: multipart/alternative; boundary="==genemail.test-BOUNDARY-alt-2=="
message-id: <1234567890@@genemail.example.com>

--==genemail.test-BOUNDARY-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

CONTENT
--==genemail.test-BOUNDARY-alt-2==
'''
    self.assertEmailEqual(eml1, eml2)

  #----------------------------------------------------------------------------
  def test_mixin_headers_diff(self):
    eml1 = '''\
Content-Type: text/plain
MIME-Version: 1.0
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: test@example.com
Message-ID: <1234567890@@genemail.example.com>
From: noreply@example.com
Subject: Foo The Bar

CONTENT
'''
    eml2 = '''\
Date: Fri, 13 Feb 2009 23:31:30 -0000
Subject: Foo The Bar
X-Generator: an extra header (note that mime-version is missing)
From: noreply@example.com
To: test@example.com
Message-ID: <1234567890@@genemail.example.com>
Content-Type: text/plain; charset=us-ascii

CONTENT
'''
    with self.assertRaises(AssertionError) as cm:
      self.assertEmailEqual(eml1, eml2)
    msg = '\n'.join(cm.exception.message.split('\n')[1:])
    self.assertMultiLineEqual(msg, '''\
  EMAIL HEADERS:
- Content-Type: text/plain
+ Content-Type: text/plain; charset=us-ascii
  Date: Fri, 13 Feb 2009 23:31:30 -0000
  From: noreply@example.com
  Message-ID: <1234567890@@genemail.example.com>
- MIME-Version: 1.0
  Subject: Foo The Bar
  To: test@example.com
+ X-Generator: an extra header (note that mime-version is missing)
''')

  #----------------------------------------------------------------------------
  def test_mixin_structure_same(self):
    eml1 = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0

--==genemail.test-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

--==genemail.test-alt-2==
Content-Type: multipart/related; boundary="==genemail.test-rel-3=="
MIME-Version: 1.0

--==genemail.test-rel-3==
Content-Type: text/plain
MIME-Version: 1.0

--==genemail.test-rel-3==
Content-Type: image/png
MIME-Version: 1.0

--==genemail.test-rel-3==--
--==genemail.test-alt-2==--
'''
    eml2 = '''\
Content-Type: multipart/alternative; boundary="==BOUNDARY-f8967b6d-alt-2=="
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-alt-2==
Content-Type: multipart/related; boundary="==BOUNDARY-f8967b6d-rel-3=="
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-rel-3==
Content-Type: text/plain
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-rel-3==
Content-Type: image/png
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-rel-3==--
--==BOUNDARY-f8967b6d-alt-2==--
'''
    self.assertEmailEqual(eml1, eml2)

  #----------------------------------------------------------------------------
  def test_mixin_structure_diff(self):
    eml1 = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0

--==genemail.test-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

--==genemail.test-alt-2==
Content-Type: multipart/related; boundary="==genemail.test-rel-3=="
MIME-Version: 1.0

--==genemail.test-rel-3==
Content-Type: text/plain
MIME-Version: 1.0

--==genemail.test-rel-3==
Content-Type: image/png
MIME-Version: 1.0

--==genemail.test-rel-3==--
--==genemail.test-alt-2==--
'''
    eml2 = '''\
Content-Type: multipart/alternative; boundary="==BOUNDARY-f8967b6d-alt-2=="
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-alt-2==
Content-Type: multipart/related; boundary="==BOUNDARY-f8967b6d-rel-3=="
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-rel-3==
Content-Type: text/plain
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-rel-3==
Content-Type: image/png
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-rel-3==
Content-Type: text/svg
MIME-Version: 1.0

--==BOUNDARY-f8967b6d-rel-3==--
--==BOUNDARY-f8967b6d-alt-2==--
'''
    with self.assertRaises(AssertionError) as cm:
      self.assertEmailEqual(eml1, eml2)
    msg = '\n'.join(cm.exception.message.split('\n')[1:])
    self.assertMultiLineEqual(msg, '''\
  EMAIL STRUCTURE:
  multipart/alternative
  |-- text/plain
  `-- multipart/related
      |-- text/plain
-     `-- image/png
?     ^
+     |-- image/png
?     ^
+     `-- text/svg
''')

  #----------------------------------------------------------------------------
  def test_mixin_content_textplain_same(self):
    eml1 = '''\
Content-Type: text/plain
MIME-Version: 1.0

this is some content.
'''
    eml2 = '''\
Content-Type: text/plain
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

this is some=
 content.
'''
    self.assertEmailEqual(eml1, eml2)

  #----------------------------------------------------------------------------
  def test_mixin_content_textplain_diff(self):
    eml1 = '''\
Content-Type: text/plain
MIME-Version: 1.0

this is some content.
'''
    eml2 = '''\
Content-Type: text/plain
MIME-Version: 1.0

this is some=
 content.
'''
    with self.assertRaises(AssertionError) as cm:
      self.assertEmailEqual(eml1, eml2)
    msg = '\n'.join(cm.exception.message.split('\n')[1:])
    self.assertMultiLineEqual(msg, '''\
- this is some content.
+ this is some=
+  content.
''')

  #----------------------------------------------------------------------------
  def test_mixin_content_multiparttextplain_same(self):
    eml1 = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0

--==genemail.test-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

this is some content.
--==genemail.test-alt-2==--
'''
    eml2 = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0

--==genemail.test-alt-2==
Content-Type: text/plain
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

this is some con=
tent.
--==genemail.test-alt-2==--
'''
    self.assertEmailEqual(eml1, eml2)

  #----------------------------------------------------------------------------
  def test_mixin_content_multiparttextplain_diff(self):
    eml1 = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0

--==genemail.test-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

this is some content.
--==genemail.test-alt-2==--
'''
    eml2 = '''\
Content-Type: multipart/alternative; boundary="==genemail.test-alt-2=="
MIME-Version: 1.0

--==genemail.test-alt-2==
Content-Type: text/plain
MIME-Version: 1.0

this is some con=
tent.
--==genemail.test-alt-2==--
'''
    with self.assertRaises(AssertionError) as cm:
      self.assertEmailEqual(eml1, eml2)
    msg = '\n'.join(cm.exception.message.split('\n')[1:])
    self.assertMultiLineEqual(msg, '''\
- this is some content.
+ this is some con=
tent.
?                 ++
''')

  #----------------------------------------------------------------------------
  def assertXmlEqual(self, x1, x2, msg=None):
    if self.noxml or pxml is None:
      return self.assertMultiLineEqual(x1, x2, msg=msg)
    class PxmlXmlTest(pxml.XmlTestMixin, unittest.TestCase):
      def runTest(self): pass
    PxmlXmlTest().assertXmlEqual(x1, x2, msg=msg)

  #----------------------------------------------------------------------------
  def test_mixin_content_texthtml_same(self):
    eml1 = '''\
Content-Type: text/html
MIME-Version: 1.0

<html><body id="Foo" class="bar">hello</body></html>
'''
    eml2 = '''\
Content-Type: text/html
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<html  ><body class='bar' id='Foo' >hello=
</body  ></html>
'''
    # note: these are not actually semantically different, but
    #       this is a test of behaviour if 'assertXmlEqual'
    #       is NOT available.
    self.noxml = True
    with self.assertRaises(AssertionError) as cm:
      self.assertEmailEqual(eml1, eml2)
    msg = '\n'.join(cm.exception.message.split('\n')[1:])
    self.assertMultiLineEqual(msg, '''\
- <html><body id="Foo" class="bar">hello</body></html>
?             ---------      ^   ^
+ <html  ><body class='bar' id='Foo' >hello</body  ></html>
?      ++             ^   ^^^^^^^^^^^            ++
''')
    if pxml is None:
      sys.stderr.write('*** PXML LIBRARY NOT PRESENT - SKIPPING XML DIFF *** ')
      return
    self.noxml = False
    self.assertEmailEqual(eml1, eml2)

  #----------------------------------------------------------------------------
  def test_mixin_content_texthtml_diff(self):
    eml1 = '''\
Content-Type: text/html
MIME-Version: 1.0

<html><body id="Foo" class="bar">hello</body></html>
'''
    eml2 = '''\
Content-Type: text/html
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<html ><body class = 'bar' >hel=
lo</body></html>
'''
    # note: these are both syntactically AND semantically
    # different... they should be different with and without
    # xml processing - but the errors should be different.
    self.noxml = True
    with self.assertRaises(AssertionError) as cm:
      self.assertEmailEqual(eml1, eml2)
    msg = '\n'.join(cm.exception.message.split('\n')[1:])
    self.assertMultiLineEqual(msg, '''\
- <html><body id="Foo" class="bar">hello</body></html>
?             ---------      ^   ^
+ <html ><body class = 'bar' >hello</body></html>
?      +            + ^^   ^^
''')
    if pxml is None:
      sys.stderr.write('*** PXML LIBRARY NOT PRESENT - SKIPPING XML DIFF *** ')
      return
    self.noxml = False
    with self.assertRaises(AssertionError) as cm:
      self.assertEmailEqual(eml1, eml2)
    msg = '\n'.join(cm.exception.message.split('\n')[1:])
    self.assertMultiLineEqual(msg, '''\
  <?xml version="1.0" encoding="UTF-8"?>
  <html>
-   <body class="bar" id="Foo">hello</body>
?                   ---------
+   <body class="bar">hello</body>
  </html>
''')

  #----------------------------------------------------------------------------
  def test_mixin_allinone(self):

    if pxml is None:
      sys.stderr.write('*** PXML LIBRARY NOT PRESENT - SKIPPING XML DIFF *** ')
      return

    eml1 = '''\
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
  <body id="bar" class="foo">
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

    eml2 = '''\
Content-Type: multipart/alternative; boundary="==ARANDOMBOUNDARY-HEHE-alt-2=="
MIME-Version: 1.0
Date: Fri, 13 Feb 2009 23:31:30 -0000
To: test@example.com
Message-ID: <1234567890@@genemail.example.com>
From: noreply@example.com
Subject: Foo The Bar

--==ARANDOMBOUNDARY-HEHE-alt-2==
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Foo the bar [].

--==ARANDOMBOUNDARY-HEHE-alt-2==
Content-Type: multipart/related; boundary="==ARANDOMBOUNDARY-HEHE-rel-3=="
MIME-Version: 1.0

--==ARANDOMBOUNDARY-HEHE-rel-3==
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Foo The Bar</title>
  </head>
  <body class="foo" id="bar">
    <p>Foo the bar <img src="cid:slogan.txt" />.</p>
  </body>
</html>
--==ARANDOMBOUNDARY-HEHE-rel-3==
Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment
Content-ID: <slogan.txt>

ALL YOUR BASE ARE BELONG TO US
--==ARANDOMBOUNDARY-HEHE-rel-3==--
--==ARANDOMBOUNDARY-HEHE-alt-2==--
'''
    self.assertEmailEqual(eml1, eml2)


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
