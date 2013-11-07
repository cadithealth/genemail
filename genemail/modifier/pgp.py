# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/11/07
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

# TODO: look into:
#   - http://www.ietf.org/rfc/rfc4880.txt
#   - https://www.enigmail.net/documentation/features.php
#   - http://sites.inka.de/tesla/gpgrelay.html

# TODO: add a setting for a key server, and if the recipient is not
#       known, look them up in there... *AWESOME* :)

from __future__ import absolute_import

import logging, asset, email

from .base import Modifier

try:
  import gnupg
  __all__ = ('PgpModifier',)
except ImportError:
  gnupg = None
  __all__ = []

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
class PgpModifier(Modifier):

  #----------------------------------------------------------------------------
  def __init__(self, prune_keys=True, prune_recipients=False,
               sign=None, add_key='sign-key', gpg_options=None):
    import gnupg
    self.kprune  = prune_keys
    self.rprune  = prune_recipients
    self.sign    = sign
    self.addkeys = add_key
    if self.addkeys is not None:
      if asset.isstr(self.addkeys):
        self.addkeys = [self.addkeys]
      self.addkeys = list(set(self.addkeys))
      if 'sign-key' in self.addkeys:
        self.addkeys.remove('sign-key')
        if self.sign is not None:
          self.addkeys.append(self.sign)
    self.gpg = gnupg.GPG(**(gpg_options or dict()))

  #----------------------------------------------------------------------------
  def modify(self, mailfrom, recipients, data, *other):

    rcptlist = list(set(recipients))

    if self.kprune:
      keys = self.gpg.list_keys()
      for rcpt in rcptlist[:]:
        for key in keys:
          if rcpt in ','.join(key.get('uids', [])):
            break
        else:
          rcptlist.remove(rcpt)
          log.warning('recipient %s removed (not found in keys)', rcpt)

    if self.rprune:
      recipients = rcptlist[:]
      if asset.isstr(data):
        data = email.message_from_string(data)
      if 'to' in data:
        del data['to']
        data.add_header('to', ', '.join(recipients))

    if not asset.isstr(data):
      hdritems = data.items()
      data = data.as_string()
      if not data.endswith('\n'):
        data += '\n'
    else:
      hdritems = email.message_from_string(data).items()

    if self.addkeys:
      rcptlist = list(set(rcptlist + self.addkeys))

    data = self.gpg.encrypt(data, rcptlist, sign=self.sign, always_trust=True)
    if not data.ok:
      raise ValueError('Encryption failed: ' + data.status)

    edata = email.MIMEMultipart.MIMEMultipart(
      'encrypted', protocol='application/pgp-encrypted')

    params = email.MIMENonMultipart.MIMENonMultipart('application', 'pgp-encrypted')
    params.set_payload('Version: 1\n')
    edata.attach(params)

    payload = email.MIMENonMultipart.MIMENonMultipart('application', 'octet-stream')
    payload.set_payload(str(data))
    edata.attach(payload)

    for key, value in hdritems:
      if key.lower() in ('content-type', 'mime-version'):
        continue
      edata.add_header(key, value)

    return (mailfrom, recipients, edata) + other

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
