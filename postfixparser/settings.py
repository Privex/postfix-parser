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
import pytz
from os import getenv as env
from dotenv import load_dotenv
from privex.helpers import env_bool, env_csv

load_dotenv()

vue_debug = env_bool('VUE_DEBUG', False)
"""
If True, the development version of Vue (with devtools support and logging) will be used instead of the 
production minified version.
"""

rethink_host = env('RETHINK_HOST', 'localhost')
rethink_port = int(env('RETHINK_PORT', 28015))
rethink_db = env('RETHINK_DB', 'maildata')

rethink_tables = [
    ('sent_mail', ['mail_to', 'timestamp', 'first_attempt', 'last_attempt']),
]

mail_log = env('MAIL_LOG', '/var/log/mail.log')


admin_pass = env('ADMIN_PASS', 'SetThis!InYourEnv')
secret_key = env('SECRET_KEY', 'SetThis!InYourEnv')

log_timezone = pytz.timezone(env('LOG_TIMEZONE', 'UTC'))
"""
If your mail.log isn't in UTC, set the LOG_TIMEZONE env var to a pytz compatible timezone
"""

ignore_domains = env_csv('IGNORE_DOMAINS', ['localhost', '127.0.0.1'])
