# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# lib:  genemail.email
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

import re
import copy
import base64
import mimetypes
import xml.etree.ElementTree as ET
import html2text
from templatealchemy.util import adict
import email.Encoders, email.Message, email.MIMEMultipart, email.MIMEText
import email.MIMEImage, email.Utils
import uuid

from . import util
from .idict import idict

#------------------------------------------------------------------------------
__all__ = ('Email',)
xmlns = 'http://pythonhosted.org/genemail/xmlns/1.0'
htmlns = util.htmlns
class MissingHeader(Exception): pass

#------------------------------------------------------------------------------
class AutoCachingDict(dict):
  def get(self, key, default=None):
    if key in self:
      return self[key]
    if callable(default):
      default = default()
    self[key] = default
    return default

#------------------------------------------------------------------------------
class Email(object):

  DEFAULTS = dict(
    structure = {

      #  default mail structure:
      #
      #     multipart/mixed [IFF there are attachments without "Content-ID"]
      #     |-- multipart/alternative
      #     |   |-- text/plain
      #     |   `-- multipart/related; type="text/html"
      #     |       |-- text/html
      #     |       `-- image/png... [attachments with "Content-ID"]
      #     `-- application/octet-stream... [attachments without "Content-ID"]
      #
      #               Content-Type: image/png
      #               Content-Transfer-Encoding: base64
      #               Content-Location: file:///.../...
      #               Content-ID: <ImageName>

      'mime:mixed; optimize=True': [
        {'mime:alternative': [
          'email:text',
          {'mime:related; type="text/html"': [
            'email:html',
            {'mime:attachments': 'email:attachments; cid=True'},
          ]},
        ]},
        {'mime:attachments': 'email:attachments; cid=False'},
      ]

    },
    params               = {},
    attachments          = [],
    headers              = idict(),
    includeComponents    = [],
    maxSubjectLength     = 512,
    snipIndicator        = '[...]',
    textEncoding         = None,
    htmlEncoding         = None,
    transferEncoding     = None,
    encoding             = None,
    boundary             = None,
    minimalMime          = True,
  )

  #----------------------------------------------------------------------------
  def __init__(self, manager, name, provider=None, default=None):
    self.manager  = manager
    self.name     = name
    self.provider = provider or self.manager.provider
    self.template = self.provider.getTemplate(self.name)
    self._headers = idict()
    if default is None:
      default = adict(self.DEFAULTS)
    for attr in self.DEFAULTS.keys():
      setattr(self, attr, copy.deepcopy(getattr(default, attr, None)))
    self.params['cache'] = AutoCachingDict()
    # self.attachmentTable    = None
    # for key, val in self.provider.getMap('headers', {}).items():
    #   self.headers[key] = val

  #----------------------------------------------------------------------------
  def __setitem__(self, key, val): self.params[key] = val
  def __getitem__(self, key): return self.params[key]
  def __delitem__(self, key): del self.params[key]

  #----------------------------------------------------------------------------
  def setHeader(self, key, val):
    'Set the email header `key` to `val`, overriding all other header sources.'
    self.headers[key] = val

  #----------------------------------------------------------------------------
  def getHeader(self, key):
    '''
    Get the current value of the header `key`. Note that this will only return
    the value as set with a prior :meth:`setHeader` call - it will *not*
    extract headers set by the template(s).
    '''
    return self.headers[key]

  #----------------------------------------------------------------------------
  def hasHeader(self, key):
    '''
    Returns whether or not the header `key` has been set with a prior call
    to :meth:`setHeader` - it will *not* extract headers set by the template(s).
    '''
    return self.headers.has_key(key)

  #----------------------------------------------------------------------------
  def delHeader(self, key):
    '''
    If the header `key` had been set with a prior call to
    :meth:`setHeader`, this will unset the header. Note that it will
    *not* delete any headers set by the template(s).
    '''
    del self.headers[key]

  #----------------------------------------------------------------------------
  # note: for some reason @property...(setter|deleter) don't work with
  # with setattr(...) in python 2.7.3. ugh. need to use old-style.
  def getHeaders(self):
    return self._headers
  def setHeaders(self, val):
    self._headers = idict(val)
  def delHeaders(self):
    self._headers = idict()
  headers = property(getHeaders, setHeaders, delHeaders)

  #----------------------------------------------------------------------------
  def getSettings(self):
    '''
    Returns a dictionary of settings set by the template (this is so
    that templates can communicate non-output parameters back to the
    calling application).
    '''
    if self.template.meta.settings:
      return self.template.meta.settings
    return adict()

  #----------------------------------------------------------------------------
  def getSetting(self, key, default=None):
    '''
    Returns the template-set setting name `key`. If not set, `default`
    is returned. See :meth:`getSettings` for details.
    '''
    return self.getSettings().get(key, default)

  #----------------------------------------------------------------------------
  def addAttachment(self, name, value, cid=False, contentType=None):
    '''
    Add an attachment to the email. The `name` is the default filename that
    will be offered when the recipient tries to "Save..." the attachment. The
    `value` is the actual content of the attachment. If `cid` is True, then
    the attachment will be stored as an embedded object, and will therefore
    not be directly saveable by the recipient and it can be accessed from
    within the HTML, for example, with the `name` set to ``'logo.png'``, the
    following will result in a valid image reference in the HTML::

      <img alt="The Logo" src="cid:logo.png"/>

    (note the ``cid:`` prefix that must be added in the HTML.)
    '''
    self.attachments.append(
      adict(name=name, value=value, cid=cid, contentType=contentType))

  #----------------------------------------------------------------------------
  def getTemplateXml(self, fallbackToNone=True):
    params = dict(self.params)
    params.update({'genemail_format': 'xml'})
    for fmt in ('xml', 'xhtml', 'html'):
      if fmt in self.template.meta.formats:
        return util.parseXml(self.template.render(fmt, params))
    if fallbackToNone:
      try:
        return util.parseXml(self.template.render(None, params))
      except ET.ParseError:
        return None
    return None

  #----------------------------------------------------------------------------
  def getTemplateHeaders(self):
    ret = idict()
    # todo: this requires that headers be defined as separate elements, eg:
    #         <email:header name="..." value="...">...</email:header>
    #       rather than being able to tag an existing node, such as:
    #         <p>This email was sent to <span email:header="To">...</span>.</p>
    xdoc = self.getTemplateXml()
    if xdoc is None:
      return ret
    etag = '{%s}header' % (xmlns,)
    for node in xdoc.iter():
      if node.tag == etag:
        ret[node.get('name')] = node.get('value') or node.text
        continue
      if node.get(etag) is not None:
        ret[node.get(etag)] = node.text
    return ret

  #----------------------------------------------------------------------------
  def getTemplateAttachments(self):
    atts = {}
    for att in self.template.meta.attachments or []:
      atts[att.name] = att
    xdoc = self.getTemplateXml()
    if xdoc is None:
      return atts.values()
    for node in xdoc.iter('{%s}attachment' % (xmlns,)):
      att = adict(
        name        = node.get('name'),
        contentType = node.get('content-type', None),
        value       = node.get('value', None) or node.text,
        cid         = node.get('cid', 'false').lower() == 'true',
      )
      if node.get('encoding', None) == 'base64':
        att.value = base64.b64decode(att.value)
      atts[att.name] = att
    return atts.values()

  #----------------------------------------------------------------------------
  def getTemplateStyle(self):
    ret  = []
    if 'css' in self.template.meta.formats:
      params = dict(self.params)
      params.update({'genemail_format': 'css'})
      ret.append(self.template.render('css', params))
    xdoc = self.getTemplateXml()
    if xdoc is None:
      return ' '.join(ret)
    # todo: what if the node has a "src" attribute...
    for node in xdoc.findall('{%s}head/{%s}style[@type="text/css"]' % (htmlns, htmlns)):
      ret.append(node.text)
    return ' '.join(ret)

  #----------------------------------------------------------------------------
  def getHtml(self, standalone=False, extraparams=None):
    '''
    Returns the raw HTML that would be generated if the email were
    sent with the current settings. Use :meth:`send` to actually send
    the email.
    '''

    # todo: what if 'html' is not in `includeComponents`?

    if standalone:
      ret = self.getHtml(extraparams=extraparams)
      return self.inlineCidAttachments(ret)

    params = dict(self.params)
    params.update({'genemail_format': 'html'})
    if extraparams:
      params.update(extraparams)

    # todo: try alternative formats if 'html' isn't available? eg xhtml...
    html = self.template.render('html', params)

    # todo: this double roundtrip of parse/serialize html is ridiculous

    # remove all genemail xmlns elements and attributes and non-inline css
    # note: using list() so that i can mutate the underlying object
    html = util.parseXml(html)
    def stripSpecial(el):
      for attr in list(el.keys()):
        if attr.startswith('{%s}' % (xmlns,)):
          del el.attrib[attr]
      for node in list(el.getchildren()):
        if node.tag.startswith('{%s}' % (xmlns,)):
          el.remove(node)
          continue
        stripSpecial(node)
    stripSpecial(html)
    for topnode in html.getchildren():
      if topnode.tag == '{%s}head' % (htmlns,):
        for node in list(topnode.getchildren()):
          if node.tag == '{%s}style' % (htmlns,) and node.get('type') == 'text/css':
            topnode.remove(node)

    style = (self.getTemplateStyle() or '').strip()
    if len(style) > 0:
      html = util.inlineHtmlStyling(html, style)

    return util.serializeHtml(html)

  #----------------------------------------------------------------------------
  def inlineCidAttachments(self, html):
    for att in self.getAttachments():
      if not att.cid:
        continue
      ct = att.contentType or 'application/octet-stream'
      value = 'data:' + ct + ';base64,' + base64.b64encode(att['value'])
      # todo: this is a "brute-force" approach... i should replace only
      #       attributes that have this exact value...
      html = html.replace('cid:' + att.name, value)
    return html

  #----------------------------------------------------------------------------
  def getText(self):
    '''
    Returns the plain-text version of the email that would be
    generated if it were sent with the current settings. Use
    :meth:`send` to actually send the email.
    '''
    # todo: what if 'text' is not in `includeComponents`?
    params = dict(self.params)
    params.update({'genemail_format': 'text'})
    if 'text' in self.template.meta.formats:
      return self.template.render('text', params)
    try:
      html = self.getHtml(extraparams={'genemail_format': 'text'})
    except Exception:
      return self.template.render(None, params)
    # todo: it would be interesting to be able to configure html2text to only
    #       put it footnotes for IMG tags that had non-"cid:" image references...
    text = html2text.html2text(html)
    # TODO: html2text should have taken care of this... but since it hasn't,
    #       are there any other characters that need to be escaped?...
    # todo: this seems a bit brute-force to reduce to ascii? perhaps
    #       the caller should inspect the text and change the content type?
    #       or, better yet, have this return a tuple with the content type
    return util.removeCids(util.reduce2ascii(text)).strip() + '\n'

  subject_collapse_spaces = re.compile(r'[\s]+', re.DOTALL)
  subject_remove_nonascii = re.compile(r'[^ -~]+', re.DOTALL)

  #----------------------------------------------------------------------------
  def _cleanSubject(self, subject):
    ret = self.subject_collapse_spaces.sub(' ', subject)
    ret = self.subject_remove_nonascii.sub('', ret)
    ret = util.reduce2ascii(ret.strip())
    if self.maxSubjectLength is not None and self.snipIndicator is not None:
      if len(ret) > self.maxSubjectLength:
        ret = ret[:self.maxSubjectLength - len(self.snipIndicator)] + self.snipIndicator
    return ret

  #----------------------------------------------------------------------------
  def getSubject(self):
    '''
    Returns the ``Subject`` header of the email that would be
    generated if it were sent with the current settings. Use
    :meth:`send` to actually send the email.
    '''
    if 'subject' in self.headers:
      return self.headers['subject']
    if 'subject' in self.template.meta.formats:
      params = dict(self.params)
      params.update({'genemail_format': 'subject'})
      # todo: check subject encoding?...
      return self.template.render('subject', self.params)
    # todo: what if there is no XML format?...
    # note: purposefully NOT using encoding=self.encoding so that i can
    #       then more cleanly replace HTML entity characters...
    # todo: clean up this entity-replacement strategy
    xdoc = self.getTemplateXml()
    if xdoc is None:
      return self._cleanSubject(self.getText())
    etag = '{%s}subject' % (xmlns,)
    ret = []
    for node in xdoc.iter():
      if node.tag == etag or node.get(etag) == 'content':
        ret.append(node.text)
    ret = ' '.join(ret).encode('us-ascii', 'genemail_unicode2ascii')
    ret = self._cleanSubject(ret)
    if ret:
      return ret
    return self._cleanSubject(self.getText())

  #----------------------------------------------------------------------------
  def getMessageID(self, from_):
    '''
    Returns the ``Message-ID`` header of the email that would be
    generated if it were sent with the current settings. If no
    message-id is present, one is generated based on the domain of the
    `from_` parameter.
    '''

    if 'message-id' in self.headers:
      return self.headers['message-id']
    return '<{msgid}@{domain}>'.format(
      msgid  = str(uuid.uuid4()),
      domain = 'localhost' if '@' not in from_ else from_.split('@', 1)[1],
    )

  #----------------------------------------------------------------------------
  def getAttachments(self):
    atts = {att.name: att for att in self.getTemplateAttachments()}
    for att in self.attachments:
      atts[att.name] = att
    for att in atts.values():
      if att.contentType:
        continue
      att.contentType = mimetypes.guess_type(att.name or '', False)[0] \
        or 'application/octet-stream'
    return atts.values()

  #----------------------------------------------------------------------------
  def getOutputHeaders(self):
    curheaders = idict()
    curheaders.update(self.getTemplateHeaders())
    curheaders.update(self.headers)
    defaultHeaders = {
      'Subject' : lambda: self.getSubject(),
      'Date'    : lambda: email.Utils.formatdate(),
    }
    for name, value in defaultHeaders.items():
      if name not in curheaders:
        curheaders[name] = value() if callable(value) else value
    if hasattr(self.manager, 'updateHeaders'):
      self.manager.updateHeaders(self, curheaders)
    return curheaders

  #----------------------------------------------------------------------------
  def getSmtpData(self):
    '''
    Returns the raw SMTP data that would be sent if the email were sent
    with the current settings. Use :meth:`send` to actually send the email.
    '''
    return self._getMimeMessage(self.getOutputHeaders()).as_string()

  #----------------------------------------------------------------------------
  def _getMimeMessage(self, curheaders):

    curheaders = idict(curheaders)

    # reduce headers to those that should be in outbound email
    # todo: should i instead be filtering for known allowed headers instead
    #       of removing known disallowed headers?...
    for header in ('bcc',):
      if header in curheaders:
        del curheaders[header]

    # the following text/html encoding selection is done only because
    # utf-8 results in base64 transfer encoding, which sucks because it
    # is not human-readable... hence trying others first. and the problem
    # with iso-8859-1 is that the "&copy;" and "&nbsp;" entities don't
    # show up, but it uses quoted-printable...
    # ==> UPDATE: i can't seem to reproduce this... the following translations
    #             occur: &mdash; => &#8212;, &copy; => &#169;, &nbsp; => &#160;

    # TODO: address the other self.encoding uses and see if the default
    #       should really be us-ascii instead of None...

    funcs = adict()

    def make_email_text():
      if self.includeComponents and 'text' not in self.includeComponents:
        return None
      txtenc  = self.textEncoding or self.transferEncoding or self.encoding
      if txtenc is not None:
        return email.MIMEText.MIMEText(self.getText(), 'plain', txtenc)
      # do several encoding round trips until one is found that does not
      # degrade the content
      for txtenc in [ 'ascii', 'iso-8859-1', 'utf-8' ]:
        src = self.getText()
        try: txt = email.MIMEText.MIMEText(src, 'plain', txtenc)
        except UnicodeEncodeError: continue
        if src == txt.get_payload(decode=True):
          return txt
      raise TypeError('could not encode email text component - try setting an encoding')
    funcs.make_email_text = make_email_text

    def make_email_html():
      if self.includeComponents and 'html' not in self.includeComponents:
        return None
      htmlenc = self.htmlEncoding or self.transferEncoding or self.encoding
      if htmlenc is not None:
        return email.MIMEText.MIMEText(self.getHtml(), 'html', htmlenc)
      # do several encoding round trips until one is found that does not
      # degrade the content
      for htmlenc in [ 'ascii', 'iso-8859-1', 'utf-8' ]:
        src = self.getHtml()
        try: html = email.MIMEText.MIMEText(src, 'html', htmlenc)
        except UnicodeEncodeError: continue
        if src == html.get_payload(decode=True):
          return html
      raise TypeError('could not encode email html component - try setting an encoding')
    funcs.make_email_html = make_email_html

    funcs.atts_cache = None
    def make_email_attachments(cid=False):
      if self.includeComponents and 'attachments' not in self.includeComponents:
        return None
      if funcs.atts_cache is None:
        funcs.atts_cache = self.getAttachments()
      return [att for att in funcs.atts_cache if att.cid == cid]
    funcs.make_email_attachments = make_email_attachments

    funcs.bndidx = 0
    def make_boundary(type):
      if not self.boundary:
        return None
      funcs.bndidx += 1
      return '==%s-%s-%i==' % (self.boundary, type, funcs.bndidx)
    funcs.make_boundary = make_boundary

    def comp_extend(comp, spec):
      if isinstance(spec, basestring):
        spec = [spec]
      for item in ( spec or [] ):
        item = funcs.make_component(item)
        if not item:
          continue
        if isinstance(comp, list):
          if isinstance(item, list):
            comp.extend(item)
          else:
            comp.append(item)
        else:
          if isinstance(item, list):
            for cur in item:
              comp.attach(cur)
          else:
            comp.attach(item)
      return comp
    funcs.comp_extend = comp_extend

    def checkMinimalMime(comp, optimize=None):
      if optimize is True or self.minimalMime:
        load = comp.get_payload()
        if not isinstance(load, basestring) \
            and len(load) == 1:
          return load[0]
      return comp

    def make_mime_mixed(spec, optimize=None):
      comp = email.MIMEMultipart.MIMEMultipart(
        'mixed', boundary=make_boundary('mix'))
      return checkMinimalMime(funcs.comp_extend(comp, spec))
    funcs.make_mime_mixed = make_mime_mixed

    def make_mime_alternative(spec, optimize=None):
      comp = email.MIMEMultipart.MIMEMultipart(
        'alternative', boundary=make_boundary('alt'))
      return checkMinimalMime(funcs.comp_extend(comp, spec))
    funcs.make_mime_alternative = make_mime_alternative

    def make_mime_related(spec, type=None, optimize=None):
      # TODO: do something with `type`...
      comp = email.MIMEMultipart.MIMEMultipart(
        'related', boundary=make_boundary('rel'))
      return checkMinimalMime(funcs.comp_extend(comp, spec))
    funcs.make_mime_related = make_mime_related

    def make_mime_attachments(spec):
      if self.includeComponents and 'attachments' not in self.includeComponents:
        return None
      atts = funcs.comp_extend([], spec)
      if not atts:
        return None
      ret = []
      for att in atts:
        maintype, subtype = (att.contentType or 'application/octet-stream').split('/', 1)
        if maintype == 'text':
          # note: we should handle calculating the charset
          matt = email.MIMEText.MIMEText(att.value, _subtype=subtype)
        elif maintype == 'image':
          matt = email.MIMEImage.MIMEImage(att.value, _subtype=subtype, name=att.name)
        elif maintype == 'audio':
          matt = email.MIMEAudio.MIMEAudio(att.value, _subtype=subtype)
        else:
          matt = email.MIMEBase.MIMEBase(maintype, subtype)
          matt.set_payload(att.value)
          email.Encoders.encode_base64(matt)
        if att.cid:
          matt.add_header('Content-Disposition', 'attachment')
          matt.add_header('Content-ID', '<' + att.name + '>')
        else:
          matt.add_header('Content-Disposition', 'attachment', filename=att.name)
        ret.append(matt)
      return ret
    funcs.make_mime_attachments = make_mime_attachments

    def make_component(spec):
      kls, comp, kw = spec, None, dict()
      if isinstance(spec, dict) and len(spec) == 1:
        kls = spec.keys()[0]
      if isinstance(kls, basestring) and ':' in kls:
        kls, comp = kls.split(':', 1)
        if ';' in comp:
          comp, kw = comp.split(';', 1)
          kw = [pairs.strip().split('=', 1)
                for pairs in kw.strip().split(',')]
          kw = {k: eval(v) for k, v in kw}
      if kls == 'email':
        return funcs['make_email_' + comp](**kw)
      if kls == 'mime':
        return funcs['make_mime_' + comp](spec.values()[0], **kw)
      raise SyntaxError('unsupported email structure component: %r' % (spec,))
    funcs.make_component = make_component

    if self.includeComponents == ['text']:
      msg = make_email_text()
    else:
      msg = make_component(self.structure)

    for k,v in curheaders.items():
      msg[util.smtpHeaderFormat(k)] = v

    return msg

  #----------------------------------------------------------------------------
  def send(self, mailfrom=None, recipients=None):
    '''
    Send the email. The ``To`` header can be overriden with the `recipients`
    parameter, and the ``From`` header con be overriden with the `mailfrom`
    parameter. Note that if these parameters are used, then the headers are
    NOT adjusted to reflect the new settings (this is to allow ``Bcc`` type
    behavior).

    :Parameters:

    mailfrom : str, optional

      Email address to set as the ``MAIL FROM`` address on the SMTP
      protocol level. Note that this will NOT set or override the
      active ``From`` header. If not specified, the address will be
      extracted from the ``From`` header.

      This parameter's domain will also be used to generate the
      ``Message-ID`` header, if it is not specified.

    recipients : { str, list(str) }, optional

      Email addresses to send this email to, on the SMTP protocol
      level. Note that this will NOT set or override the active ``To``
      header. If not specified, the addresses will be extracted from
      the ``To``, ``CC``, and ``BCC`` headers.
    '''
    hdrs = self.getOutputHeaders()
    if mailfrom is None:
      mailfrom = util.extractEmails(hdrs.get('from'))
      if not mailfrom:
        raise MissingHeader('email source ("from") not specified')
      mailfrom = mailfrom[0]
    if recipients is None:
      recipients = util.extractEmails(hdrs.get('to')) or []
      recipients += util.extractEmails(hdrs.get('cc')) or []
      recipients += util.extractEmails(hdrs.get('bcc')) or []
      if not recipients or len(recipients) <= 0:
        raise MissingHeader('email destination ("to") not specified')
    elif isinstance(recipients, basestring):
      recipients = [recipients]
    if 'Message-ID' not in hdrs:
      hdrs['Message-ID'] = self.getMessageID(mailfrom)
    data = self._getMimeMessage(hdrs)
    if self.manager.modifier:
      mailfrom, recipients, data = self.manager.modifier.modify(
        mailfrom, recipients, data)
    if not isinstance(data, basestring):
      data = data.as_string()
      if not data.endswith('\n'):
        data += '\n'
    self.manager.sender.send(mailfrom, recipients, data)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
