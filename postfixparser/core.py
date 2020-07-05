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
import json
import logging
import rethinkdb.ast
import rethinkdb.query

from typing import Tuple, List, Union

from privex.helpers import empty
from quart import request
from quart.exceptions import BadRequest
from rethinkdb import RethinkDB
from rethinkdb.ast import DB
from rethinkdb.net import DefaultConnection

from postfixparser import settings
from privex.loghelper import LogHelper

from postfixparser.settings import AppError, DEFAULT_ERR, ERRORS

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


async def extract_json(rq: request) -> Union[list, dict]:
    """
    Extract JSON formatted POST data from a Quart request.

    **Example** (Dictionary JSON POST data)::

        >>> async def my_view():
        ...     data = extract_json(request)
        ...     if not isinstance(data, dict):
        ...         return jsonify(error=True, message=f"JSON POST data must be a dictionary (map/object)!"), 400
        ...     first_name = data.get('first_name')
        ...     last_name = data.get('last_name')

    **Example** (List JSON POST data)::

        >>> async def other_view():
        ...     data = extract_json(request)
        ...     if not isinstance(data, list):
        ...         return jsonify(error=True, message=f"JSON POST data must be a list (array)!"), 400
        ...     for name in data:

    """
    try:
        data = await rq.get_json(force=True)
        return data
    except (json.decoder.JSONDecodeError, BadRequest) as e:
        log.debug('get_json failed, falling back to extracting from form keys')
        data = list(rq.form.keys())
        if len(data) >= 1:
            return json.loads(data[0])
        raise e


def get_accepts(headers) -> List[str]:
    lower_headers = {k.lower(): v for k, v in headers.items()}
    accepts = lower_headers.get('accept', 'application/json').split(',')
    return [a.split(';')[0] for a in accepts]


async def filter_methods(data: list):
    methods = {}
    for d in data:
        m = d['method']
        if m not in methods:
            methods[m] = []
        methods[m].append(d)
    return methods


def _get_error(code: str, fallback: str = 'UNKNOWN_ERROR') -> AppError:
    """
    Attempt to retrieve an :class:`.AppError` by it's error code, with fallback to the error code ``fallback``.

    If something goes wrong trying to fallback to ``fallback``, then :attr:`.DEFAULT_ERR` will be returned instead.

        >>> err = _get_error('NOT_FOUND')
        >>> print(err.code, err.message)
        NOT_FOUND The requested resource or URL was not found. You may wish to check the URL for typos.

        >>> err = _get_error('NON_EXISTENT_ERR')
        >>> print(err.code, err.message)
        UNKNOWN_ERROR An unknown error has occurred. Please contact the administrator of this site.

    :param str code:      The error code to attempt to retrieve, e.g. ``NOT_FOUND``.
    :param str fallback:  The error code to attempt to fallback to, if ``code`` wasn't found.
    :return AppError err: An instance of an error in :class:`.AppError` form.
    """
    e = ERRORS.get(code, ERRORS.get(fallback))
    if empty(e, True, True): return DEFAULT_ERR
    return e


def add_app_error(code: str, msg: str, status: int = 500) -> AppError:
    """
    Add a new error code for easy API error raising.

        >>> add_app_error("INV_TOKEN", "Invalid API token specified in Authorization header.", 403)


    :param str code:     A short, unique capitalized error code, e.g. ``INV_USERNAME`` - this code should be static, i.e. never change,
                         since it should be used by API clients for handling certain errors.
    :param str msg:      A human readable error message, e.g. "Username must be at least 5 characters"
    :param int status:   An integer HTTP status code that should be returned when this error is raised.
    :return AppError err:  The :class:`.AppError` instance which was added/updated in :attr:`.ERRORS`
    """
    ERRORS[code] = AppError(code, msg, status)
    return ERRORS[code]

