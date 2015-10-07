# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# lib:  genemail.util
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

import re, codecs
from StringIO import StringIO
import xml.etree.ElementTree as ET
from xml.dom import minidom
import cssutils, cssselect, xpath

#------------------------------------------------------------------------------
htmlns = 'http://www.w3.org/1999/xhtml'

#------------------------------------------------------------------------------
# email regex from:
#   http://www.regular-expressions.info/email.html
# and extended to:
#   - support "...@localhost"
#   - support TLDs up to 63 characters
#   - support internationalized domains using punycode
#       TODO: people should be able to enter their non-punycode version...
emailRegex_cre = re.compile(
  '\\b[a-z0-9._%+-]+@(?:(?:[a-z0-9-]+\\.)+(?:xn--)?[a-z]{2,63}|localhost)\\b',
  re.IGNORECASE)
def extractEmails(s):
  if not s:
    return None
  return emailRegex_cre.findall(s)

#------------------------------------------------------------------------------
def getHtmlStyleView(document, css, media='all', name=None,
                     styleCallback=lambda element: None):
  """
  :param document:
    a DOM element (must be minidom-compatible)
  :param css:
    a CSS StyleSheet string
  :param media:
    [optional] TODO: view for which media it should be
  :param name:
    [optional] TODO: names of sheets only
  :param styleCallback:
    [optional] should return css.CSSStyleDeclaration of inline styles,
    for html a style declaration for ``element@style``. Gets one
    parameter ``element`` which is the relevant DOMElement

  returns style view
    a dict of {DOMElement: css.CSSStyleDeclaration} for html

  shamelessly scrubbed from:
    http://cssutils.googlecode.com/svn/trunk/examples/style.py (``getView()``)
    ==> with an adjustment to get around a deprecationwarning in
        cssutils/css/cssstyledeclaration.py:598
    ==> and an adjustment to use "xhtml" translator for the cssselector
    ==> and an adjustment to not use lxml
  """

  sheet = cssutils.parseString(css)
  css2xpath = cssselect.GenericTranslator()
  view = {}
  specificities = {} # needed temporarily
  # TODO: filter rules simpler?, add @media
  rules = (rule for rule in sheet if rule.type == rule.STYLE_RULE)
  for rule in rules:
    for selector in rule.selectorList:
      xpe = css2xpath.css_to_xpath(selector.selectorText)
      for element in xpath.find(xpe, document):
        if element not in view:
          # add initial empty style declatation
          view[element] = cssutils.css.CSSStyleDeclaration()
          specificities[element] = {}
          # and add inline @style if present
          inlinestyle = styleCallback(element)
          if inlinestyle:
            for p in inlinestyle:
              # set inline style specificity
              view[element].setProperty(p)
              specificities[element][p.name] = (1,0,0,0)
        for p in rule.style:
          # update style declaration
          if p not in view[element]:
            # setProperty needs a new Property object and
            # MUST NOT reuse the existing Property
            # which would be the same for all elements!
            # see Issue #23
            view[element].setProperty(p.name, p.value, p.priority)
            specificities[element][p.name] = selector.specificity
          else:
            sameprio = (p.priority ==
                  view[element].getPropertyPriority(p.name))
            if not sameprio and bool(p.priority) or (
               sameprio and selector.specificity >=
                    specificities[element][p.name]):
              # later, more specific or higher prio
              # NOTE: added explicit removeProperty to get around these warnings:
              #   cssutils-0.9.8a1-py2.6.egg/cssutils/css/cssstyledeclaration.py:598: DeprecationWarning: Call to deprecated method '_getCSSValue'. Use ``property.propertyValue`` instead.
              #   cssutils-0.9.8a1-py2.6.egg/cssutils/css/cssstyledeclaration.py:598: DeprecationWarning: Call to deprecated method '_setCSSValue'. Use ``property.propertyValue`` instead.
              view[element].removeProperty(p.name)
              view[element].setProperty(p.name, p.value, p.priority)
  return view

#------------------------------------------------------------------------------
# TODO: move this to use ET elements to remove the XML roundtrip...
# TODO: this currently strips out the <!DOCTYPE> line if it appears, eg:
#       <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
def inlineHtmlStyling_minidom(doc, css):
  def scb(element):
    if element.hasAttribute('style'):
      cssText = element.getAttribute('style')
      return cssutils.css.CSSStyleDeclaration(cssText=cssText)
    return None
  view = getHtmlStyleView(doc, css, styleCallback=scb)
  for element, style in view.items():
    v = style.getCssText(separator=u'')
    element.setAttribute('style', v)
  return doc
def inlineHtmlStyling(etdoc, css):
  html = serializeHtml(etdoc)
  doc  = minidom.parseString(html)
  ret  = inlineHtmlStyling_minidom(doc, css)
  return parseXml(ret.toxml('UTF-8'))

#------------------------------------------------------------------------------
def parseXml(data):
  src = StringIO(data)
  parser = ET.XMLParser()
  parser.parser.UseForeignDTD(True)
  # todo: allow some mechanism for the caller to provide additional entities
  parser.entity['nbsp']  = unichr(160)
  parser.entity['mdash'] = unichr(8212)
  parser.entity['copy']  = unichr(169)
  parser.entity['reg']   = unichr(174)
  etree = ET.ElementTree()
  tree = etree.parse(src, parser=parser)
  return tree

#------------------------------------------------------------------------------
def serializeHtml(xdoc):
  '''
  Serializes ElementTree `xdoc` to HTML.
  NOTE: `xdoc` is mutated to qualify any non-qualified attributes
  and elements with the HTML namespace.
  '''
  # note: qualifying all attributes and elements so that this error is
  # avoided:
  #   ValueError: cannot use non-qualified names with default_namespace option
  # IMHO, it should not be throwing this...
  # http://bugs.python.org/issue17088
  for node in xdoc.iter():
    if not node.tag.startswith('{'):
      node.tag = '{%s}%s' % (htmlns, node.tag)
    for attr in list(node.keys()):
      if not attr.startswith('{'):
        node.set('{%s}%s' % (htmlns, attr), node.get(attr))
        del node.attrib[attr]
  dst = StringIO()
  etree = ET.ElementTree(xdoc)
  etree.write(dst, default_namespace=htmlns)
  # todo: it would be nice if the HTML output were 'pretty-printed'...
  return dst.getvalue()

#------------------------------------------------------------------------------
# shamelessly scrubbed from:
#   http://www.w3schools.com/tags/ref_symbols.asp
# with additions for &copy; and &reg;
r2a_map = dict((

  (u'\u00a9', '(C)'),                  # © &#169; &copy; copyright symbol
  (u'\u00ae', '(R)'),                  # ® &#174; &reg; registered trademark

  # math symbols supported by HTML
  (u'\u2200', '<for-all>'),            # ∀ &#8704; &forall; for all
  (u'\u2202', '<part>'),               # ∂ &#8706; &part; part
  (u'\u2203', '<exists>'),             # ∃ &#8707; &exist; exists
  (u'\u2205', '<empty>'),              # ∅ &#8709; &empty; empty
  (u'\u2207', '<nabla>'),              # ∇ &#8711; &nabla; nabla
  (u'\u2208', '<isin>'),               # ∈ &#8712; &isin; isin
  (u'\u2209', '<notin>'),              # ∉ &#8713; &notin; notin
  (u'\u220b', '<ni>'),                 # ∋ &#8715; &ni; ni
  (u'\u220f', '<prod>'),               # ∏ &#8719; &prod; prod
  (u'\u2211', '<sum>'),                # ∑ &#8721; &sum; sum
  (u'\u2212', '<minus>'),              # − &#8722; &minus; minus
  (u'\u2217', '<lowast>'),             # ∗ &#8727; &lowast; lowast
  (u'\u221a', '<square-root>'),        # √ &#8730; &radic; square root
  (u'\u221d', '<proportional-to>'),    # ∝ &#8733; &prop; proportional to
  (u'\u221e', '<infinity>'),           # ∞ &#8734; &infin; infinity
  (u'\u2220', '<angle>'),              # ∠ &#8736; &ang; angle
  (u'\u2227', '<and>'),                # ∧ &#8743; &and; and
  (u'\u2228', '<or>'),                 # ∨ &#8744; &or; or
  (u'\u2229', '<cap>'),                # ∩ &#8745; &cap; cap
  (u'\u222a', '<cup>'),                # ∪ &#8746; &cup; cup
  (u'\u222b', '<integral>'),           # ∫ &#8747; &int; integral
  (u'\u2234', '<therefore>'),          # ∴ &#8756; &there4; therefore
  (u'\u223c', '<similar-to>'),         # ∼ &#8764; &sim; similar to
  (u'\u2245', '<congruent-to>'),       # ≅ &#8773; &cong; congruent to
  (u'\u2248', '<almost-equal>'),       # ≈ &#8776; &asymp; almost equal
  (u'\u2260', '<not-equal>'),          # ≠ &#8800; &ne; not equal
  (u'\u2261', '<equivalent>'),         # ≡ &#8801; &equiv; equivalent
  (u'\u2264', '<less-or-equal>'),      # ≤ &#8804; &le; less or equal
  (u'\u2265', '<greater-or-equal>'),   # ≥ &#8805; &ge; greater or equal
  (u'\u2282', '<subset-of>'),          # ⊂ &#8834; &sub; subset of
  (u'\u2283', '<superset-of>'),        # ⊃ &#8835; &sup; superset of
  (u'\u2284', '<not-subset-of>'),      # ⊄ &#8836; &nsub; not subset of
  (u'\u2286', '<subset-or-equal>'),    # ⊆ &#8838; &sube; subset or equal
  (u'\u2287', '<superset-or-equal>'),  # ⊇ &#8839; &supe; superset or equal
  (u'\u2295', '<circled-plus>'),       # ⊕ &#8853; &oplus; circled plus
  (u'\u2297', '<circled-times>'),      # ⊗ &#8855; &otimes; circled times
  (u'\u22a5', '<perpendicular>'),      # ⊥ &#8869; &perp; perpendicular
  (u'\u22c5', '<dot-operator>'),       # ⋅ &#8901; &sdot; dot operator

  # greek letters supported by HTML
  (u'\u0391', '<Alpha>'),              # Α &#913; &Alpha; Alpha
  (u'\u0392', '<Beta>'),               # Β &#914; &Beta; Beta
  (u'\u0393', '<Gamma>'),              # Γ &#915; &Gamma; Gamma
  (u'\u0394', '<Delta>'),              # Δ &#916; &Delta; Delta
  (u'\u0395', '<Epsilon>'),            # Ε &#917; &Epsilon; Epsilon
  (u'\u0396', '<Zeta>'),               # Ζ &#918; &Zeta; Zeta
  (u'\u0397', '<Eta>'),                # Η &#919; &Eta; Eta
  (u'\u0398', '<Theta>'),              # Θ &#920; &Theta; Theta
  (u'\u0399', '<Iota>'),               # Ι &#921; &Iota; Iota
  (u'\u039a', '<Kappa>'),              # Κ &#922; &Kappa; Kappa
  (u'\u039b', '<Lambda>'),             # Λ &#923; &Lambda; Lambda
  (u'\u039c', '<Mu>'),                 # Μ &#924; &Mu; Mu
  (u'\u039d', '<Nu>'),                 # Ν &#925; &Nu; Nu
  (u'\u039e', '<Xi>'),                 # Ξ &#926; &Xi; Xi
  (u'\u039f', '<Omicron>'),            # Ο &#927; &Omicron; Omicron
  (u'\u03a0', '<Pi>'),                 # Π &#928; &Pi; Pi
  (u'\u03a1', '<Rho>'),                # Ρ &#929; &Rho; Rho
  (u'\u03a3', '<Sigma>'),              # Σ &#931; &Sigma; Sigma
  (u'\u03a4', '<Tau>'),                # Τ &#932; &Tau; Tau
  (u'\u03a5', '<Upsilon>'),            # Υ &#933; &Upsilon; Upsilon
  (u'\u03a6', '<Phi>'),                # Φ &#934; &Phi; Phi
  (u'\u03a7', '<Chi>'),                # Χ &#935; &Chi; Chi
  (u'\u03a8', '<Psi>'),                # Ψ &#936; &Psi; Psi
  (u'\u03a9', '<Omega>'),              # Ω &#937; &Omega; Omega
  (u'\u03b1', '<alpha>'),              # α &#945; &alpha; alpha
  (u'\u03b2', '<beta>'),               # β &#946; &beta; beta
  (u'\u03b3', '<gamma>'),              # γ &#947; &gamma; gamma
  (u'\u03b4', '<delta>'),              # δ &#948; &delta; delta
  (u'\u03b5', '<epsilon>'),            # ε &#949; &epsilon; epsilon
  (u'\u03b6', '<zeta>'),               # ζ &#950; &zeta; zeta
  (u'\u03b7', '<eta>'),                # η &#951; &eta; eta
  (u'\u03b8', '<theta>'),              # θ &#952; &theta; theta
  (u'\u03b9', '<iota>'),               # ι &#953; &iota; iota
  (u'\u03ba', '<kappa>'),              # κ &#954; &kappa; kappa
  (u'\u03bb', '<lambda>'),             # λ &#955; &lambda; lambda
  (u'\u03bc', '<mu>'),                 # μ &#956; &mu; mu
  (u'\u03bd', '<nu>'),                 # ν &#957; &nu; nu
  (u'\u03be', '<xi>'),                 # ξ &#958; &xi; xi
  (u'\u03bf', '<omicron>'),            # ο &#959; &omicron; omicron
  (u'\u03c0', '<pi>'),                 # π &#960; &pi; pi
  (u'\u03c1', '<rho>'),                # ρ &#961; &rho; rho
  (u'\u03c2', '<sigmaf>'),             # ς &#962; &sigmaf; sigmaf
  (u'\u03c3', '<sigma>'),              # σ &#963; &sigma; sigma
  (u'\u03c4', '<tau>'),                # τ &#964; &tau; tau
  (u'\u03c5', '<upsilon>'),            # υ &#965; &upsilon; upsilon
  (u'\u03c6', '<phi>'),                # φ &#966; &phi; phi
  (u'\u03c7', '<chi>'),                # χ &#967; &chi; chi
  (u'\u03c8', '<psi>'),                # ψ &#968; &psi; psi
  (u'\u03c9', '<omega>'),              # ω &#969; &omega; omega
  (u'\u03d1', '<theta-symbol>'),       # ϑ &#977; &thetasym; theta symbol
  (u'\u03d2', '<upsilon-symbol>'),     # ϒ &#978; &upsih; upsilon symbol
  (u'\u03d6', '<pi-symbol>'),          # ϖ &#982; &piv; pi symbol

  # other symbols supported by HTML
  (u'\u0152', 'OE'),                   # Œ &#338; &OElig; capital ligature OE
  (u'\u0153', 'oe'),                   # œ &#339; &oelig; small ligature oe
  # TODO: should these be decorated?...
  (u'\u0160', 'S'),                    # Š &#352; &Scaron; capital S with caron
  (u'\u0161', 's'),                    # š &#353; &scaron; small S with caron
  (u'\u0178', 'Y'),                    # Ÿ &#376; &Yuml; capital Y with diaeres
  (u'\u0192', '?'),                    # ƒ &#402; &fnof; f with hook

  (u'\u02c6', '^'),                    # ˆ &#710; &circ; modifier letter circumflex accent
  (u'\u02dc', '~'),                    # ˜ &#732; &tilde; small tilde
  (u'\u2002', ' '),                    #   &#8194; &ensp; en space
  (u'\u2003', ' '),                    #   &#8195; &emsp; em space
  (u'\u2009', ' '),                    #   &#8201; &thinsp; thin space
  (u'\u200c', '?'),                    # ‌ &#8204; &zwnj; zero width non-joiner
  (u'\u200d', '?'),                    # ‍ &#8205; &zwj; zero width joiner
  (u'\u200e', '?'),                    # ‎ &#8206; &lrm; left-to-right mark
  (u'\u200f', '?'),                    # ‏ &#8207; &rlm; right-to-left mark
  (u'\u2013', '-'),                    # – &#8211; &ndash; en dash
  (u'\u2014', '-'),                    # — &#8212; &mdash; em dash
  (u'\u2018', '\''),                   # ‘ &#8216; &lsquo; left single quotation mark
  (u'\u2019', '\''),                   # ’ &#8217; &rsquo; right single quotation mark
  (u'\u201a', '\''),                   # ‚ &#8218; &sbquo; single low-9 quotation mark
  (u'\u201c', '"'),                    # “ &#8220; &ldquo; left double quotation mark
  (u'\u201d', '"'),                    # ” &#8221; &rdquo; right double quotation mark
  (u'\u201e', '"'),                    # „ &#8222; &bdquo; double low-9 quotation mark
  (u'\u2020', '?'),                    # † &#8224; &dagger; dagger
  (u'\u2021', '?'),                    # ‡ &#8225; &Dagger; double dagger
  (u'\u2022', '*'),                    # • &#8226; &bull; bullet
  (u'\u2026', '...'),                  # … &#8230; &hellip; horizontal ellipsis
  (u'\u2030', '0/00'),                 # ‰ &#8240; &permil; per mille
  (u'\u2032', '\''),                   # ′ &#8242; &prime; minutes
  (u'\u2033', '"'),                    # ″ &#8243; &Prime; seconds
  (u'\u2039', '<'),                    # ‹ &#8249; &lsaquo; single left angle quotation
  (u'\u203a', '>'),                    # › &#8250; &rsaquo; single right angle quotation
  (u'\u203e', '-'),                    # ‾ &#8254; &oline; overline
  (u'\u20ac', '<euro>'),               # € &#8364; &euro; euro
  (u'\u2122', '<TM>'),                 # ™ &#8482; &trade; trademark
  (u'\u2190', '<-'),                   # ← &#8592; &larr; left arrow
  (u'\u2191', '?'),                    # ↑ &#8593; &uarr; up arrow
  (u'\u2192', '->'),                   # → &#8594; &rarr; right arrow
  (u'\u2193', '?'),                    # ↓ &#8595; &darr; down arrow

  # additional right arrows scrubbed from:
  #   http://right-arrow.net/
  (u'\u21d2', '=>'),                   # ⇒ &#8658; &rArr;
  (u'\u21ac', '->'),                   # ↬ &#8620;
  (u'\u21c9', '=>'),                   # ⇉ &#8649;
  (u'\u21e8', '=>'),                   # ⇨ &#8680;
  (u'\u21e5', '->|'),                  # ⇥ &#8677;
  (u'\u21e2', '->'),                   # ⇢ &#8674;
  (u'\u21aa', '->'),                   # ↪ &#8618;
  (u'\u21a6', '|->'),                  # ↦ &#8614;
  (u'\u21f6', '=>'),                   # ⇶ &#8694;
  (u'\u21a3', '>->'),                  # ↣ &#8611;
  (u'\u21f0', '|=>'),                  # ⇰ &#8688;
  (u'\u219d', '~>'),                   # ↝ &#8605;
  (u'\u21a0', '->>'),                  # ↠ &#8608;
  (u'\u21fe', '->'),                   # ⇾ &#8702;

  # others...
  (u'\u21e6', '<='),                   # ⇦ &#8678;

  ))

def reduce2ascii(text):
  ret = []
  for c in text:
    if ord(c) < 128:
      ret.append(c)
      continue
    # todo: handle ascii chars in the 128 -> 255 range...
    ret.append(r2a_map.get(c, '?'))
  return ''.join(ret)
  #return text.replace(u'\u21d2', '=>')

#------------------------------------------------------------------------------
_removeCidsRe = re.compile('\\!\\[([^\\]]*)\\]\\(cid:[^)]*\\)')
def removeCids(text):
  return _removeCidsRe.sub('[\\1]', text)

#------------------------------------------------------------------------------
# todo: move this?
smtp_header_element_upper = ['cc', 'id', 'spf', 'mime']
def smtpHeaderFormat(h):
  return '-'.join([e.upper() if e in smtp_header_element_upper else e.title()
                   for e in [e.lower() for e in h.split('-')]])

#------------------------------------------------------------------------------
# todo: installing a global unicode decode/encode translation error handler...
#       this is not ideal... see Email.getSubject() for details...
#------------------------------------------------------------------------------
def genemail_unicode2ascii(err):
  if err.reason != 'ordinal not in range(128)':
    raise err
  # todo: shouldn't this just use `r2a_map`?...
  if err.object[err.start] == unichr(160):
    # &nbsp;
    return (u' ', err.start + 1)
  if err.object[err.start] == unichr(8212):
    # &mdash;
    return (u'--', err.start + 1)
  return (u'?', err.start + 1)
#------------------------------------------------------------------------------
try:
  codecs.lookup_error('genemail_unicode2ascii')
except LookupError:
  codecs.register_error('genemail_unicode2ascii', genemail_unicode2ascii)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
