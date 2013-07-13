# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# lib:  genemail.cli
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/07/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, argparse, yaml, os.path
from . import manager, sender

#------------------------------------------------------------------------------
def main(args=None, output=None):

  cli = argparse.ArgumentParser(
    description='Command-line interface to the `genemail` email generation'
    ' library.'
    )

  cli.add_argument(
    '-v', '--verbose',
    action='count',
    help='enable verbose output (multiple invocations increase verbosity)')

  cli.add_argument(
    '-n', '--name', metavar='NAME',
    default=None, action='store',
    help='set the template name; if omitted, the root template will be used')

  cli.add_argument(
    '-p', '--param', metavar='NAME=VALUE',
    default=[], action='append',
    help='set a template variable where `VALUE` is taken as a literal'
    ' string (overrides any values set in `--params`)')

  cli.add_argument(
    '-y', '--params', metavar='YAML',
    default=[], action='append',
    help='specifies a YAML-encoded dictionary as template variables;'
    ' if the value starts with the letter "@", the rest is the file name to'
    ' read as a YAML structure. If the value is exactly a dash ("-"), then'
    ' the YAML structure is read from STDIN. In all cases, the YAML'
    ' structure must be a dictionary')

  cli.add_argument(
    '-r', '--renderer', metavar='SPEC',
    default='mako',
    help='sets the TemplateAlchemy rendering driver (default: %(default)r)')

  cli.add_argument(
    '-H', '--smtp-host', metavar='HOST',
    default='localhost',
    help='set the SMTP server hostname (default: %(default)r)')

  cli.add_argument(
    '-P', '--smtp-port', metavar='PORT',
    default=25, type=int,
    help='set the SMTP server port number (default: %(default)r)')

  cli.add_argument(
    '--smtp-ssl',
    default=False, action='store_true',
    help='enable SSL communication with the SMTP server')

  cli.add_argument(
    '--smtp-starttls',
    default=False, action='store_true',
    help='enable STARTTLS with the SMTP server')

  cli.add_argument(
    '--smtp-username', metavar='USERNAME',
    help='set the SMTP username to authenticate as')

  cli.add_argument(
    '--smtp-password', metavar='PASSWORD',
    help='set the SMTP password to authenticate with (if `--smtp-username`'
    ' is specified, but not `--smtp-password` or the password is exactly'
    ' "-", the password will be prompted for securely)')

  # TODO: add output control, --html --text --smtp, etc.

  cli.add_argument(
    'source', metavar='SOURCE',
    nargs='?',
    help='sets the TemplateAlchemy source driver; if exactly a dash ("-") or'
    ' omitted, then the template is read from STDIN')

  options = cli.parse_args(args)

  # params = dict()

  # for yparam in options.params:
  #   if yparam == '-':
  #     yparam = sys.stdin.read()
  #   elif yparam.startswith('@'):
  #     with open(yparam[1:], 'rb') as fp:
  #       yparam = fp.read()
  #   try:
  #     yparam = yaml.load(yparam)
  #   except Exception:
  #     cli.error('could not parse YAML expression: %r'
  #               % (yparam,))
  #   if not isinstance(yparam, dict):
  #     cli.error('"--params" expressions must resolve to dictionaries')
  #   params.update(yparam)

  # for kparam in options.param:
  #   if '=' not in kparam:
  #     cli.error('"--param" expressions must be in the KEY=VALUE format')
  #   key, value = kparam.split('=', 1)
  #   params[key] = value

  # options.params = params
  # output = output or sys.stdout

  # if options.source is None or options.source == '-':
  #   options.source = stream.StreamSource(sys.stdin)
  # elif ':' not in options.source and os.path.isfile(options.source):
  #   options.source = stream.StreamSource(open(options.source, 'rb'))

  # template = engine.Template(
  #   source=options.source,
  #   renderer=options.renderer,
  #   )

  # if options.name is not None:
  #   template = template.getTemplate(options.name)

  # output.write(template.render(options.format, options.params))

  emlman = manager.Manager()

  return 0

#------------------------------------------------------------------------------
if __name__ == '__main__':
  sys.exit(main())

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
