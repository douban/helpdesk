# coding: utf-8

import logging
import smtplib
from email.message import EmailMessage

import requests
from helpdesk.config import (
    WEBHOOK_URL,
    FROM_EMAIL_ADDR,
    SMTP_SERVER,
    SMTP_SERVER_PORT,
    SMTP_SSL,
    SMTP_CREDENTIALS,
)

logger = logging.getLogger(__name__)


def send_mail(to, subject, body):
    server_info = (SMTP_SERVER, SMTP_SERVER_PORT)
    smtp = smtplib.SMTP_SSL(*server_info) if SMTP_SSL else smtplib.SMTP(*server_info)
    if SMTP_CREDENTIALS:
        user, password = SMTP_CREDENTIALS.split(':')
        smtp.login(user, password)

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL_ADDR
    msg['To'] = to

    try:
        smtp.send_message(msg)
    except Exception as e:
        logger.warning('send email failed(%s): %s', to, e)
    finally:
        smtp.quit()


def send_webhook(target, subject, body, truncate=True):
    if not WEBHOOK_URL:
        return
    body = body.replace("\n\n", "\n")
    if truncate:
        bodies = body.split('\n')
        if len(bodies) > 10:
            bodies = bodies[:3] + ["..."] + bodies[-3:]
        tmp = []
        for line in bodies:
            if len(line) > 160:
                line = "%s ..." % line[:160]
            tmp.append(line)
        bodies = tmp
        body = '\n'.join(bodies)
    msg = {
        'from': 'helpdesk',
        'to': target,
        'title': subject,
        'text': subject + '\n' + body,
        'markdown': body,
    }
    r = requests.post(WEBHOOK_URL, json=msg, timeout=3)
    if r.status_code != 200:
        logger.warning('send channels failed(%s): %s', target, r.text)
