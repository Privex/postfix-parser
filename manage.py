#!/usr/bin/env python3
"""

Copyright::
    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Postfix Log Parser / Web UI                |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+

"""
import argparse
import asyncio
import textwrap

from privex.helpers import ErrHelpParser

help_text = textwrap.dedent('''\

    Commands:

        runserver         - Run the Quart dev server (DO NOT USE IN PRODUCTION. USE Hypercorn)
        parse             - Parse the mail log and import it into the DB

''')

parser = ErrHelpParser(
    description='Privex Postfix Parser',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=help_text
)


subparser = parser.add_subparsers()


def runserver(opt):
    from postfixparser.webui import app

    app.run(
        host=opt.host,
        port=opt.port,
        debug=app.config.get('DEBUG', False)
    )


def runparse(opt):
    from postfixparser.main import main
    asyncio.run(main())


p_run = subparser.add_parser('runserver', description='Run Quart dev server (DO NOT USE IN PRODUCTION. USE Hypercorn)')
p_run.add_argument('--port', help='Port to listen on', default=5222, type=int)
p_run.add_argument('--host', help='IP/Hostname to listen on', default='127.0.0.1')
p_run.set_defaults(func=runserver)

p_parse = subparser.add_parser('parse', description='Parse the mail log and import it into the DB')
p_parse.set_defaults(func=runparse)

args = parser.parse_args()

if 'func' in args:
    args.func(args)
else:
    parser.print_help()

