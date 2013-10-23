========
genemail
========

.. WARNING::

  2013/10/23: although functional, genemail is still in beta, and the
  API may change. That said, it works quite well.

`genemail` makes creating and sending templated email easier. The
following features are built-in:

* **Automatic html-to-text conversion** so that all generated emails
  have both a plain-text and an HTML version. Note that if the auto-
  conversion is not sufficient, each version can have it's own
  template.

* **Automatic inlining of CSS** for maximum backward compatibility
  with old and/or problematic email clients.

* **Automatic attachment management** allows a common email template
  to specify default attachments; additional attachments can be added
  to individual emails.

* **Support for DKIM email header generation** so that emails that
  are indeed not spam are less likely to be identified as such.

* **Preview data** allows templates to define sample data so that
  email previews can be generated with predefined data and/or dynamic
  data.

* **Unit of test for generated emails** is made easier thanks to a
  sender mechanism that allows outbound emails to be trapped for
  analysis instead of being delivered and a unittest mixin class that
  provides the `assertEmailEqual` method that validates that the
  significant email headers, structure and content are the same.


TL;DR
=====

Install:

.. code-block:: bash

  $ pip install genemail

Given the following package file structure:

::

  -- mypackage/
     `-- templates/
         `-- email/
             |-- logo.png
             |-- invite.html
             |-- invite.spec         # if missing: defaults are used
             |     Example content:
             |       attachments:
             |         - name:  logo.png
             |           value: !include-raw logo.png
             |           cid:   true
             `-- invite.text         # if missing: auto-generated from .html

Use genemail as follows:

.. code-block:: python

  import genemail, templatealchemy as ta

  # configure a genemail manager that uses the local SMTP server
  # and uses mako templates from a python package named 'mypackage'
  manager = genemail.Manager(
    sender   = genemail.SmtpSender(host='localhost', port='25'),
    provider = ta.Manager(
      source   = 'pkg:mypackage:templates/email',
      renderer = 'mako'),
    modifier = genemail.DkimModifier(
      selector = 'selector._domainkey.example.com',
      key      = '/path/to/private-rsa.key',
      )
    )

  # get an email template object
  eml = manager.newEmail('invite')

  # set some parameters that will be used by mako to render the
  # template
  eml['givenname'] = 'Joe'
  eml['surname']   = 'Schmoe'

  # add an ICS calendar invite
  eml.addAttachment(
    name        = 'invite.ics',
    value       = create_invite(...),
    contentType = 'text/calendar; name=invite.ics; method=PUBLISH')

  # and send the email
  eml.send()

  # the resulting email will:
  #   - have two alternative formats (text/plain and text/html)
  #   - have one top-level attachment (text/calendar)
  #   - have one text/html related attachment (logo.png)
  #   - be DKIM-signed

Overview
========

TODO: add docs


Unit Testing
============

The following example test code illustrates the recommended approach
to do unit testing with genemail (note the use of the `pxml` library
to compare HTML output):

.. code-block:: python

  import unittest, pxml, genemail, genemail.testing

  class AppTest(genemail.testing.EmailTestMixin, pxml.TestMixin, unittest.TestCase):

    def setUp(self):
      super(AppTest, self).setUp()
      self.sender = genemail.DebugSender()
      # the following is very subjective to how your app is built & used,
      # but the idea is to provide a different `sender` to genemail...
      self.app = App()
      self.app.genemail.sender = self.sender

    def test_email(self):

      # do something to cause an email to be sent
      self.app.send_an_email()

      # verify the sent email (which will have been trapped by self.sender)
      self.assertEqual(len(self.sender.emails), 1)
      self.assertEmailEqual(self.sender.emails[0], '''\
  Content-Type: multipart/alternative; boundary="==BOUNDARY-MAIN=="
  MIME-Version: 1.0
  Date: Fri, 13 Feb 2009 23:31:30 -0000
  To: test@example.com
  Message-ID: <1234567890@@genemail.example.com>
  From: noreply@example.com
  Subject: Test Subject

  --==BOUNDARY-MAIN==
  MIME-Version: 1.0
  Content-Type: text/plain; charset="us-ascii"
  Content-Transfer-Encoding: 7bit

  Email text version.

  --==BOUNDARY-MAIN==
  Content-Type: multipart/related; boundary="==BOUNDARY-HTMLREL=="
  MIME-Version: 1.0

  --==BOUNDARY-HTMLREL==
  MIME-Version: 1.0
  Content-Type: text/html; charset="us-ascii"
  Content-Transfer-Encoding: 7bit

  <html><body>Email html version.</body></html>

  --==BOUNDARY-HTMLREL==
  Content-Type: image/png
  MIME-Version: 1.0
  Content-Transfer-Encoding: 7bit
  Content-Disposition: attachment
  Content-ID: <logo.png>

  PNG.BINARY.DATA...
  --==BOUNDARY-HTMLREL==--
  --==BOUNDARY-MAIN==--
  ''')

