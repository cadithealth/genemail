========
genemail
========

`genemail` makes creating and sending templated email easier. The
following features are built-in:

* **Automatic html-to-text conversion** so that all generated emails
  have both a plain-text and an HTML version. Note that if the auto-
  conversion is not sufficient, each version can have it's own
  template.

* **Automatic inlining of CSS** for maximum backward compatibility
  with old or problematic email clients.

* **Automatic attachment management** allows a common email template
  to specify default attachments; additional attachments can be added
  to individual emails.

* **Preview data** allows templates to define sample data so that
  email previews can be generated with predefined data and/or dynamic
  data.

* **Unit of test for generated emails** is made easier thanks to a
  sender mechanism that allows outbound emails to be trapped for
  analysis instead of being delivered.

TL;DR
=====

Install:

.. code-block:: bash

  $ pip install genemail

Use:

.. code-block:: python

  import genemail, templatealchemy as TA

  # configure a genemail manager that uses the local SMTP server
  # and uses mako templates from a python package named 'mypackage'
  manager = genemail.Template(
    sender   = genemail.SmtpSender(host='localhost', port='25'),
    provider = TA.Manager(
      source   = 'pkg:mypackage:templates/email',
      renderer = 'mako'),
    )

  # get an email template object
  eml = manager.getEmail('registered')

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

Overview
========

TODO: add docs
