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
import asyncio
import logging
import re
import rethinkdb.query
from enum import Enum
from typing import Dict
from postfixparser import settings
from postfixparser.core import get_rethink
from postfixparser.objects import PostfixLog, PostfixMessage
from postfixparser.parser import parse_line

log = logging.getLogger(__name__)


_match = r'([A-Za-z]+ [0-9]+ [0-9]+\:[0-9]+:[0-9]+).*'
"""(0) Regex to match the Date/Time at the start of each log line"""

_match += r'([A-F0-9]{10})\: ?(.*)'
"""Regex to match the (1) Queue ID and the (2) Log Message"""

match = re.compile(_match)


class ObjectExists(BaseException):
    pass


class OnConflict(Enum):
    QUIET = "quiet"
    EXCEPT = "except"
    UPDATE = "update"


async def save_obj(table, data, primary=None, onconflict: OnConflict = OnConflict.EXCEPT):
    r, conn, _ = await get_rethink()
    _data = dict(data)
    if primary is not None:
        if 'id' not in _data: _data['id'] = _data[primary]
        g = await r.table(table).get(data[primary]).run(conn)

        if g is not None:
            if onconflict == OnConflict.QUIET:
                return None
            if onconflict == OnConflict.EXCEPT:
                raise ObjectExists(f"Table '{table}' entry with '{primary} = {data[primary]}' already exists!")
            if onconflict == OnConflict.UPDATE:
                return await r.table(table).get(data[primary]).update(_data).run(conn)
            raise AttributeError("'saveobj' onconflict must be either 'quiet', 'except', or 'update'")
    return await r.table(table).insert(_data).run(conn)


async def import_log(logfile: str) -> Dict[str, PostfixMessage]:
    log.info('Opening log file %s', logfile)
    messages = {}
    with open(logfile, 'r') as f:
        while True:
            line = f.readline()
            if not line: break

            m = match.match(line)
            if not m: continue

            dtime, qid, msg = m.groups()
            if qid not in messages:
                messages[qid] = PostfixMessage(timestamp=dtime, queue_id=qid)

            messages[qid].merge(await parse_line(msg))
            messages[qid].lines.append(PostfixLog(timestamp=dtime, queue_id=qid, message=msg))

    log.info('Finished parsing log file %s', logfile)
    return messages


async def main():
    r, conn, r_q = await get_rethink()
    r_q: rethinkdb.query

    log.info('Importing log file')
    msgs = await import_log(settings.mail_log)
    log.info('Converting log data into list')
    msg_list = [{"id": qid, **msg.clean_dict(convert_time=r_q.expr)} for qid, msg in msgs.items()]
    log.info('Total of %d message entries', len(msg_list))
    log.info('Generating async batch save list')
    save_list = []
    for m in msg_list:
        mfrom, mto = m.get('mail_from'), m.get('mail_to')
        mfrom_dom, mto_dom = mfrom.split('@')[1], mto.split('@')[1]
        if mfrom_dom in settings.ignore_domains or mto_dom in settings.ignore_domains:
            continue
        save_list.append(save_obj('sent_mail', m, primary="id", onconflict=OnConflict.UPDATE))
    log.info('Firing off asyncio.gather(save_list)...')
    await asyncio.gather(*save_list)
    log.info('Finished!')

