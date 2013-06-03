#!/usr/bin/python

import ConfigParser
try:
	import email.utils as email_utils
except ImportError:
	import email.Utils as email_utils
import os
import smtplib
import time

import settings

def _get_setting(key):
    parser = ConfigParser.ConfigParser()
    settings_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'settings.ini')
    parser.read(settings_path)
    return parser.get('email', key)

def send_email(to, subject, body, cc=[], bcc=[], replyto=None):
    from_ = _get_setting('from')
    replyto = replyto or from_
    email_text = """Date: %(date)s
From: %(from)s
MIME-Version: 1.0
To: %(to)s
Reply-To: %(replyto)s
CC: %(cc)s
Subject: %(subject)s
Content-Type: text/plain; charset=ISO-8859-1
Content-Transfer-Encoding: 7bit

""" % \
        {
            'from': from_,
            'subject': subject,
            'to': ','.join(to),
            'replyto': replyto,
            'cc': ','.join(cc),
            'date': email_utils.formatdate(time.time(), localtime=True)
        }
    email_text += body
    email_text = email_text.replace('\n', '\r\n') + '\r\n\r\n'

    retry_count = 0
    while True:
        try:
            session = smtplib.SMTP(_get_setting('host'))
            session.login(_get_setting('username'), _get_setting('password'))
            smtpresult = session.sendmail(from_, to + cc + bcc, email_text)
        except:
            if retry_count >= 3: # Retry up to 3 times
                raise
            else:
                retry_count += 1
        else:
            break

