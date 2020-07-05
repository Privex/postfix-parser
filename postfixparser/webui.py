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
from dataclasses import dataclass, field
from typing import List, Union, Mapping, Tuple

import rethinkdb.query
import logging

from rethinkdb.net import DefaultConnection

from postfixparser import settings, api
from postfixparser.exceptions import APIException
from postfixparser.core import get_rethink
from quart import Quart, session, redirect, render_template, request, flash, jsonify
from privex.helpers import random_str, empty, filter_form, DictDataClass, DictObject

log = logging.getLogger(__name__)

app = Quart(__name__)
app.secret_key = settings.secret_key

Table = rethinkdb.query.ast.Table
RqlQuery = rethinkdb.query.ast.RqlQuery
QueryOrTable = Union[Table, RqlQuery]


@app.route('/', methods=['GET'])
async def index():
    if 'admin' in session:
        return redirect('/emails/')

    return await render_template('login.html')


@app.route('/login', methods=['POST'])
async def login():
    frm = await request.form

    if frm.get('password') == settings.admin_pass:
        session['admin'] = random_str()
        return redirect('/emails/')

    await flash('Invalid password.', 'error')
    return redirect('/')


@app.route('/emails', methods=['GET'])
@app.route('/emails/', methods=['GET'])
async def emails_ui():
    if 'admin' not in session:
        await flash("You must log in to access this.", 'error')
        return redirect('/')

    return await render_template('emails.html', VUE_DEBUG=settings.vue_debug, settings=settings)


@app.route('/logout', methods=['GET'])
async def logout():
    if 'admin' not in session:
        await flash("You must log in to access this.", 'error')
        return redirect('/')

    del session['admin']
    await flash("You have been successfully logged out", "success")
    return redirect('/')


@dataclass
class PageResult(DictDataClass):
    result: Union[list, dict, str, int, float] = field(default_factory=list)
    error: bool = False
    error_code: str = None
    count: int = 0
    remaining: int = 0
    page: int = 1
    total_pages: int = 1
    message: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    
    raw_data: Union[dict, DictObject] = field(default_factory=DictObject, repr=False)
    # ^ The raw, unmodified data that was passed as kwargs, as a dictionary
    
    def to_json_dict(self) -> dict:
        d = dict(self)
        
        if not d['error']:
            if 'error_code' in d and empty(d['error_code'], True, True):
                del d['error_code']
            if 'messages' in d and empty(d['messages'], True, True):
                del d['messages']
            if 'message' in d and empty(d['message'], True, True):
                del d['message']
        
        return d
    
    def to_json(self, indent=4, **kwargs) -> str:
        return json.dumps(self.to_json_dict(), indent=indent, **kwargs)


@app.route('/api/emails', methods=['GET'])
async def api_emails():
    """

    All GET params are used for filtering. Use ``x.y`` to access sub-dict key's (only works for 1 layer deep),
    and append ``__lt`` / ``__gt`` to the end of a key for ``<=`` and ``>=`` respectively.


    Example queries:

        Get emails where ``mail['status']['code'] == 'bounced'``

        /api/emails?status.code=bounced


        Get emails older than or equal to ``2019-09-17 00:00:00`` but newer than 2019-09-10 00:00:00

        /api/emails?timestamp__lt=2019-09-17 00:00:00&timestamp__gt=2019-09-10 00:00:00


        Find a specific email by ID

        /api/emails?id=E553EBD87B


    :return:
    """
    if 'admin' not in session:
        await flash("You must log in to access this.", 'error')
        return redirect('/')

    r, conn, r_q = await get_rethink()
    r_q: rethinkdb.query

    frm = dict(request.args)
    order_by = str(frm.pop('order', 'last_attempt')).lower()
    order_dir = str(frm.pop('order_dir', 'desc')).lower()

    _sm = r.table('sent_mail')

    # Handle appending .filter() to `_sm` for each filter key in `frm`
    _sm = await _process_filters(query=_sm, frm=frm)

    _sm, res = await _paginate_query(_sm, frm, rt_conn=conn, rt_query=r_q, order_by=order_by, order_dir=order_dir)
    _sm = await _sm.run(conn)

    sm = []
    if type(_sm) is list:
        sm = list(_sm)
    else:
        async for s in _sm:
            sm.append(dict(s))
    
    res.result = sm

    return jsonify(res.to_json_dict())


async def _paginate_query(query: QueryOrTable, frm: Mapping, rt_conn: DefaultConnection, rt_query: rethinkdb.query,
                          order_by=None, order_dir='desc') -> Tuple[QueryOrTable, PageResult]:
    _lo = filter_form(frm, 'limit', 'offset', 'page', cast=int)
    limit, offset, page = _lo.get('limit', settings.default_limit), _lo.get('offset', 0), _lo.get('page')
    if not empty(page, True, True):
        offset = limit * (page - 1)
    offset = 0 if offset < 0 else offset
    res = PageResult(error=False, count=0, remaining=0, page=1 if not page else page, total_pages=1)
    
    # Get the total number of rows which match the requested filters
    count = await query.count().run(rt_conn)
    
    # rt_query: RqlTopLevelQuery
    r_order = order_by if order_dir == 'asc' else rt_query.desc(order_by)
    limit = settings.default_limit if limit <= 0 else (settings.max_limit if limit > settings.max_limit else limit)
    offset = (count - limit if (count - limit) > 0 else 0) if offset >= count else offset
    
    # if count < offset:
    #     offset = count - limit if count - limit > 0 else count - 1
    page, total_pages = int(offset / limit) + 1, int(count / limit) - 1
    total_pages = 1 if total_pages < 1 else total_pages
    page = 1 if page < 1 else page
    res.count, res.remaining, res.page, res.total_pages = count, count - offset, page, total_pages
    # if order_by in dict(settings.rethink_tables)['sent_mail']:
    #     _sm = _sm.order_by(index=r_order)
    # else:
    query = query.skip(offset).limit(limit).order_by(r_order)
    return query, res


async def _process_filters(query: QueryOrTable, frm: Mapping, skip_keys: List[str] = None) -> QueryOrTable:
    if empty(frm, itr=True):
        return query
    
    skip_keys = ['limit', 'offset', 'page'] if not skip_keys else skip_keys
    
    for fkey, fval in frm.items():
        if fkey in skip_keys:
            continue

        query = await _filter_form_key(fkey=fkey, fval=fval, query=query)
    return query


async def _filter_form_key(fkey: str, fval: str, query: QueryOrTable) -> QueryOrTable:
    if '.' in fkey:
        k1, k2 = fkey.split('.')
        return query.filter(lambda m: m[k1][k2] == fval)
    if '__lt' in fkey:
        fkey = fkey.replace('__lt', '')
        return query.filter(lambda m: m[fkey] <= fval)
    if '__gt' in fkey:
        fkey = fkey.replace('__gt', '')
        return query.filter(lambda m: m[fkey] >= fval)
    # If the form key value starts or ends with an asterisk, then we use .match() with regex filtering
    # to find items which start/end with the actual value (rval = without asterisks)
    if fval.startswith('*') or fval.endswith('*'):
        rval = fval.replace('*', '')  # fval but without asterisks
        if fval.startswith('*') and fval.endswith('*'):  # matches: *something*
            query = query.filter(lambda m: m[fkey].match(rval))
        elif fval.startswith('*'):  # matches: *something
            query = query.filter(lambda m: m[fkey].match(f"{rval}$"))
        elif fval.endswith('*'):  # matches: something*
            query = query.filter(lambda m: m[fkey].match(f"^{rval}"))
        return query

    return query.filter(lambda m: m[fkey] == fval)


@app.errorhandler(404)
async def handle_404(exc=None):
    return await api.handle_error('NOT_FOUND', exc=exc)


@app.errorhandler(APIException)
async def api_exception_handler(exc: APIException, *args, **kwargs):
    return await api.handle_error(err_code=exc.error_code, err_msg=exc.message, code=exc.status, exc=exc, template=exc.template)


@app.errorhandler(Exception)
async def app_error_handler(exc=None, *args, **kwargs):
    log.warning("app_error_handler exception type / msg: %s / %s", type(exc), str(exc))
    log.warning("app_error_handler *args: %s", args)
    log.warning("app_error_handler **kwargs: %s", kwargs)
    return await api.handle_error('UNKNOWN_ERROR', exc=exc)
