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
import logging
import rethinkdb.ast
import rethinkdb.query

from typing import Tuple
from rethinkdb import RethinkDB
from rethinkdb.ast import DB
from rethinkdb.net import DefaultConnection

from postfixparser import settings
from privex.loghelper import LogHelper

_lh = LogHelper('postfixparser')
_lh.add_console_handler(level=logging.INFO)

log = logging.getLogger(__name__)

__STORE = {}


async def get_rethink() -> Tuple[DB, DefaultConnection, RethinkDB]:
    """

    Usage:

        >>> from postfixparser.core import get_rethink
        >>>
        >>> r, conn, rDB = await get_rethink()
        >>> r.table('blocks').insert(dict(block_num=1234)).run(conn)


    :return DB rethink: (Tuple Param 1) - Main RethinkDB database query object :class:`rethinkdb.RethinkDB`
    :return DefaultConnection conn: (Tuple Param 2) - Rethink Connection Object :class:`rethinkdb.net.DefaultConnection`
    """
    if 'rethink' in __STORE:
        return __STORE['rethink']

    # Setup RethinkDB connection
    # log.debug('Initialising RethinkDB connector')
    r: rethinkdb.query = RethinkDB()
    r.set_loop_type('asyncio')
    conn = await r.connect(settings.rethink_host, settings.rethink_port)

    dbs = await r.db_list().run(conn)
    if settings.rethink_db not in dbs:
        log.debug('Database %s did not exist. Creating.', settings.rethink_db)
        await r.db_create(settings.rethink_db).run(conn)

    # Create required tables inside of database
    db = r.db(settings.rethink_db)   # type: DB
    rtables = await db.table_list().run(conn)
    for t, indexes in settings.rethink_tables:
        if t not in rtables:
            log.debug('Table %s did not exist. Creating.', t)
            await db.table_create(t).run(conn)
        idxs = await db.table(t).index_list().run(conn)
        for index in indexes:
            if index not in idxs:
                log.debug('Index %s on table %s did not exist. Creating.', index, t)
                await db.table(t).index_create(index).run(conn)

    __STORE['rethink'] = db, conn, r
    return __STORE['rethink']


