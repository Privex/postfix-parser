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
import rethinkdb.query
import logging
from postfixparser import settings
from postfixparser.core import get_rethink
from quart import Quart, session, redirect, render_template, request, flash, jsonify
from privex.helpers import random_str, empty

log = logging.getLogger(__name__)


app = Quart(__name__)

app.secret_key = settings.secret_key


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

    return await render_template('emails.html', VUE_DEBUG=settings.vue_debug)


@app.route('/logout', methods=['GET'])
async def logout():
    if 'admin' not in session:
        await flash("You must log in to access this.", 'error')
        return redirect('/')

    del session['admin']
    await flash("You have been successfully logged out", "success")
    return redirect('/')


# def api_filter(mail):
#     frm = dict(request.args)
#     log.info('mail is: %s', mail)
#     for fkey, fval in frm.items():
#         if '.' in fkey:
#             k1, k2 = fkey.split('.')
#             log.info('mail[%s][%s] != %s', k1, k2, fval)
#             if mail[k1][k2] != fval:
#                 return False
#             continue
#         log.info('mail[%s] != %s', fkey, fval)
#         if mail[fkey] != fval:
#             return False
#     return True


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
    order_by, order_dir = 'timestamp', 'asc'

    _sm = r.table('sent_mail')

    if not empty(frm, itr=True):
        if 'order' in frm:
            order_by = str(frm['order']).lower()
            del frm['order']
        if 'order_dir' in frm:
            order_dir = str(frm['order_dir']).lower()
            del frm['order_dir']

        for fkey, fval in frm.items():
            if '.' in fkey:
                k1, k2 = fkey.split('.')
                _sm = _sm.filter(lambda m: m[k1][k2] == fval)
            elif '__lt' in fkey:
                fkey = fkey.replace('__lt', '')
                _sm = _sm.filter(lambda m: m[fkey] <= fval)
            elif '__gt' in fkey:
                fkey = fkey.replace('__gt', '')
                _sm = _sm.filter(lambda m: m[fkey] >= fval)
            else:
                _sm = _sm.filter(lambda m: m[fkey] == fval)

    r_order = order_by if order_dir == 'asc' else r_q.desc(order_by)
    # if order_by in dict(settings.rethink_tables)['sent_mail']:
    #     _sm = _sm.order_by(index=r_order)
    # else:
    _sm = _sm.order_by(r_order)
    _sm = await _sm.run(conn)

    sm = []
    if type(_sm) is list:
        sm = list(_sm)
    else:
        async for s in _sm:
            sm.append(dict(s))

    return jsonify(sm)

