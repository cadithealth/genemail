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

* **Support for PGP email encryption** so that emails can contain
  sensitive information that should not be visible to the public.

* **Preview data** allows templates to define sample data so that
  email previews can be generated with predefined data and/or dynamic
  data.

* **Unit of test for generated emails** is made easier thanks to a
  sender mechanism that allows outbound emails to be trapped for
  analysis instead of being delivered and a unittest mixin class that
  provides the `assertEmailEqual` method that validates that the
  significant email headers, structure and content are the same.


Project
=======

* Homepage: https://github.com/cadithealth/genemail
* Bugs: https://github.com/cadithealth/genemail/issues


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


DKIM Signed Email
=================

TODO: add docs


Per-Email Value Caching
=======================

When genemail renders a typical email with HTML, plain-text, subjects,
and headers all being supplied by the same template, it by default
evaluates the template many times with different ``genemail_format``
values and different output renderings. This can be a problem, for
example, if the template calls out to dynamically generate content
that should only be evaluated once per email such as a pixel tracker.

To solve this, genemail inserts a default parameter named ``cache``
which is an "auto-caching dict". The difference between a standard
`dict` class and the `cache` parameter is that the `.get` method will
populate itself with the default value if the specified key does not
exist. Furthermore, if the default value is a callable, it will first
call it (with no arguments) before caching it.

The following example makes use of a `makeUniqueUrl()` function that
can be used to track clicks in the email on a per-email basis. If it
did not use the `cache` object, `makeUniqueUrl()` would be called
multiple times per email.

.. code-block:: mako

  <p>
   Please click on the link below:
   <a href="${cache.get('myCacheKey', lambda: makeUniqueUrl())}">click me!</a>
  </p>

Note that this cache is a *per-email-instance* cache.


Encrypted Email
===============

The genemail ``pgp`` optional feature allows you to generate encrypted
outbound email. It does this using the ``python-gnupg`` package, which
in turn uses the ``gpg`` external command-line program. Genemail can
both encrypt and sign the emails, or only encrypt. Steps to generate
encrypted email:

1. First, create a GPG-home directory with all of the necessary
keys. For example:

.. code-block:: bash

  # create the directory
  $ mkdir -p /path/to/gpghome
  $ chmod 700 /path/to/gpghome

  # for signing, a private key is needed. generate one:
  $ gpg --homedir /path/to/gpghome --gen-key

  # for encryption, the public key of every recipient of encrypted
  # emails is needed. do this for every recipient:
  $ gpg --homedir /path/to/gpghome --import /path/to/recipient/public.key

2. Then, configure genemail to use the
``genemail.modifier.PgpModifier`` modifier. For example:

.. code-block:: python

  import genemail

  # configure a genemail manager using the modifier
  manager = genemail.Manager(
    # ...
    modifier = genemail.modifier.PgpModifier(
      sign        = 'noreply@example.com',
      gpg_options = dict(gnupghome = '/path/to/gpghome'),
      ),
    # ...
    )

PgpModifier takes the following parameters:

* ``sign``: str, optional, default: null

  If specified, it is taken to be the ID or email address of the GPG
  key to use to sign outbound emails. In this case, either the
  passphrase must be empty, or you must be using a gpg-agent. The
  default is null, which disables signing.

* ``add_key``: list(str), optional, default: 'sign-key'

  The `add_key` parameter specifies IDs or email addresses that should
  be added to the encryption list, but not to the recipient list.
  This is useful if a global 'backdoor' key is needed. It can also be
  set to ``'sign-key'`` (the default) which indicates that the signing
  key should be added (thus the sender can decrypt the sent
  messages). Set this to null to disable any addition. It can also be
  a list of values.

* ``prune_keys``: bool, optional, default: true

  If truthy (the default), then the list of email addresses for whom
  the email is encrypted for is reduced to the set of recipients that
  have an exactly matching key. If too many addresses are pruned (this
  can happen if the gpg binary is smarter at matching an email address
  to a key), then this may need to be set to false -- but beware, if
  any address cannot be resolved to a key by gpg, then the entire
  encryption process fails, and the email is not sent.

* ``prune_recipients``: bool, optional, default: false

  If truthy, then encrypted emails will only be sent to the list of
  addresses that were the result of a `prune_keys` pruning. If they
  are not pruned, the recipients will receive emails that they cannot
  read. This is by default false so that it is more obvious that some
  action needs to be taken (i.e. give the GPG-home directory the
  appropriate list of keys).

* ``gpg_options``: dict, optional

  This parameter is a collection of parameters passed to gnupg. The
  only required parameter is `gnupghome`, which is the path to the
  GPG-home directory. All currently available parameters:

  * ``gnupghome``: str, optional, default: null
  * ``gpgbinary``: str, optional, default: 'gpg'
  * ``use_agent``: bool, optional, default: false
  * ``verbose``: bool, optional, default: false
  * ``keyring``: str, optional, default: null
  * ``secret_keyring``: str, optional, default: null
  * ``options``: list(str), optional, default: null


Unit Testing
============

The following example test code illustrates the recommended approach
to do unit testing with genemail (note the use of the `pxml` library
to compare HTML output):

.. code-block:: python

  import unittest, pxml, genemail, genemail.testing

  class AppTest(genemail.testing.EmailTestMixin, pxml.XmlTestMixin, unittest.TestCase):

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

