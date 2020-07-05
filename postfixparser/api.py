import json
import traceback
from typing import Union, Dict, Any

from privex.helpers import empty_if, DictObject, filter_form
from quart import jsonify, request, render_template
from werkzeug.datastructures import Headers

from . import settings
from .core import get_accepts
from .settings import AppError, ERRORS

import logging

log = logging.getLogger(__name__)


def error_dict(error_code: str, msg: str, extra: dict = None):
    extra = {} if not extra else dict(extra)
    return dict(error=True, error_code=error_code, message=msg, result=None, **extra)


def error(error_code: str, msg: str, code: int = 400, extra: dict = None):
    """
    Generate a Flask/Quart JSON error response

        >>> from app import api
        >>> def my_view():
        ...     return api.error('NOT_FOUND', 'No object found with that ID', code=404)

    :param str error_code:    A short string error code for referencing the error
    :param str msg:           A human readable error message
    :param int code:          The HTTP status code to return (default: 400 - Bad Request)
    :param dict extra:        Optionally specify a dictionary of extra key/value's to merge with the outputted JSON dict
    """
    res = error_dict(error_code, msg, extra=extra)
    if code is None: return jsonify(res)
    return jsonify(res), code


def result_dict(res: Union[dict, list, str, int], count: int = None, total: int = None, extra: dict = None):
    extra = {} if not extra else dict(extra)
    
    _res = dict(error=False)
    if count is None and isinstance(res, (list, set, tuple)):
        _res['count'] = len(res)
    elif count is not None:
        _res['count'] = int(count)
    
    if total is not None: _res['total'] = int(total)
    return {**_res, 'result': res, **extra}


def result(res: Union[dict, list, str, int], code: int = 200, count: int = None, total: int = None, extra: dict = None):
    """
    Generate a Flask/Quart JSON response

        >>> from postfixparser import api
        >>> def my_view():
        ...     results = filter_objects('blocks', producer='exampleproducer')
        ...     return api.result(results)


    :param dict|list|str|int res:     The result object to include in the response
    :param int code:                  The HTTP status code to return (default: 200 - Success)

    :param count:                     The number of results. If not specified and object is a list/set/tuple, then count will be set
                                      to the object length.

    :param total:                     The total number of available results (for paginating)
    :param dict extra:                Optionally specify a dictionary of extra key/value's to merge with the outputted JSON dict
    """
    _res = result_dict(res, count=count, total=total, extra=extra)
    return jsonify(_res), code


async def wants_json() -> bool:
    """
    Returns ``True`` if the client appears to want JSON, or ``False`` if they don't appear to desire
    JSON (e.g. a web browser).

        >>> # noinspection PyUnresolvedReferences
        >>> async def my_view():
        ...     if await wants_json():
        ...         return jsonify(hello='world')
        ...     return await render_template('hello.html', world='example')


    """
    rv = await request.values
    if rv.get('format', '').lower() == 'json':
        return True
    
    h: Headers = request.headers
    h: dict = dict(h)
    accepts = get_accepts(h)
    _json_types = ['application/json', 'text/json', 'json']
    if len(accepts) == 0:
        return True
    if accepts[0].lower() in _json_types:
        return True
    
    for a in accepts:
        if a in ['text/html', 'application/xhtml+xml']:
            return False
        if a in _json_types:
            return True
    return True


async def handle_error(err_code='UNKNOWN_ERROR', err_msg=None, code: int = None, exc: Exception = None, **kwargs):
    tpl = empty_if(kwargs.get('template'), 'api_error.html')
    
    res, extra = DictObject(error_code=err_code), {}
    if exc is not None:
        res.exc_name, res.exc_msg, res.traceback = str(type(exc)), str(exc), traceback.format_exc()
        log.warning("_handle_error exception type / msg: %s / %s", res.exc_name, res.exc_msg)
        log.warning("_handle_error traceback: %s", res.traceback)
    err: AppError = ERRORS.get(err_code, ERRORS['UNKNOWN_ERROR'])
    res.error_msg = err.message if err_msg is None else err_msg
    res.status_code = err.status if code is None else code
    
    if settings.DEBUG and exc is not None:
        extra: Dict[str, Any] = dict(exception=filter_form(res, 'traceback', 'exc_name', 'exc_msg'))
        if 'traceback' in extra['exception']: extra['exception']['traceback'] = res.traceback.split("\n")
    
    if await wants_json():
        return error(res.error_code, msg=res.error_msg, code=res.status_code, extra=extra)
    
    tpl = await render_template(
        tpl, **res, data=json.dumps(error_dict(res.error_code, msg=res.error_msg, extra=extra), indent=4)
    )
    return tpl, res.status_code
