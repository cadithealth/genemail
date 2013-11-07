# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/31
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

from .base import Modifier

try:
  import dkim
  __all__ = ('DkimModifier',)
except ImportError:
  dkim = None
  __all__ = []

#------------------------------------------------------------------------------
class DkimModifier(Modifier):

  #----------------------------------------------------------------------------
  def __init__(self, privateKey, domain, selector,
               identity=None, canonicalize=None, headers=None,
               algorithm=None, length=None):
    '''
    Create a genemail.Modifier that adds DKIM signature headers to emails.

    :Parameters:

    privateKey : str
      a PKCS#1 private key in base64-encoded text form

    domain : str
      the DKIM domain value for the signature

    selector : str
      the DKIM selector value for the signature

    identity : str, optional
      the DKIM identity value for the signature (defaults to the
      default dkimpy package value)

    canonicalize : list(str, str), optional
      the canonicalization algorithms to use (defaults to the default
      dkimpy package value)

    headers : list(str), optional
      a list of strings indicating which headers are to be signed
      (defaults to the default dkimpy package value)

    algorithm : str, optional
      a list of strings indicating which headers are to be signed
      (defaults to the default dkimpy package value)

    length : bool, optional
      true if the l= tag should be included to indicate body length
      (defaults to the default dkimpy package value)
    '''
    import dkim
    self.key      = privateKey
    self.domain   = domain
    self.selector = selector
    self.logger   = None
    self.dkimargs = dict()
    if identity is not None:
      self.dkimargs['identity'] = identity
    if canonicalize is not None:
      self.dkimargs['canonicalize'] = canonicalize
    if headers is not None:
      self.dkimargs['include_headers'] = headers
    if algorithm is not None:
      self.dkimargs['signature_algorithm'] = algorithm
    if length is not None:
      self.dkimargs['length'] = length

  #----------------------------------------------------------------------------
  def modify(self, mailfrom, recipients, data):
    import dkim
    if not isinstance(data, basestring):
      data = data.as_string()
    dkimhdr = dkim.sign(data, self.selector, self.domain, self.key,
                        logger=self.logger, **self.dkimargs)
    return (mailfrom, recipients, dkimhdr + data)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
