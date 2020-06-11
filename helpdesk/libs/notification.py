# coding: utf-8

import logging
import smtplib
from email.message import EmailMessage

import requests
from starlette.templating import Jinja2Templates

from helpdesk.config import (
    NOTIFICATION_TITLE_PREFIX,
    WEBHOOK_URL,
    ADMIN_EMAIL_ADDRS,
    FROM_EMAIL_ADDR,
    SMTP_SERVER,
    SMTP_SERVER_PORT,
    SMTP_SSL,
    SMTP_CREDENTIALS,
    get_user_email,
)

logger = logging.getLogger(__name__)

_templates = Jinja2Templates(directory='templates/notification')

NAME2RGB = {
    'green': '#008000',
    'orange': '#FFA500',
    'yellow': '#FFFF00',
    'red': '#FF0000',
    'pink': '#FFC0CB',
    'cyan': '#00FFFF',
    'grey': '#CDCDCD',
}


class Notification:
    method = None

    def __init__(self, phase, ticket):
        self.phase = phase
        self.ticket = ticket

    async def send(self):
        raise NotImplementedError

    def render(self):
        import xml.etree.ElementTree as ET

        message = _templates.get_template(f'{self.method}/{self.phase.value}.j2').render(dict(ticket=self.ticket))
        logger.debug('render_notification: message: %s', message)
        tree = ET.fromstring(message.strip())
        title = ''.join(piece.text for piece in tree.findall('title'))
        content = ''.join(piece.text for piece in tree.findall('content'))
        return title, content


class MailNotification(Notification):
    method = 'mail'

    async def get_mail_addrs(self):
        email_addrs = [ADMIN_EMAIL_ADDRS] + [get_user_email(cc) for cc in self.ticket.ccs]
        email_addrs += [get_user_email(approver) for approver in await self.ticket.get_rule_actions('approver')]
        if self.phase.value in ('approval', 'mark'):
            email_addrs += [get_user_email(self.ticket.submitter)]
        email_addrs = ','.join(addr for addr in email_addrs if addr)

    async def send(self):
        addrs = await self.get_mail_addrs()
        title, content = self.render()

        server_info = (SMTP_SERVER, SMTP_SERVER_PORT)
        smtp = smtplib.SMTP_SSL(*server_info) if SMTP_SSL else smtplib.SMTP(*server_info)
        if SMTP_CREDENTIALS:
            user, password = SMTP_CREDENTIALS.split(':')
            smtp.login(user, password)

        msg = EmailMessage()
        msg.set_content(content.strip())
        msg['Subject'] = NOTIFICATION_TITLE_PREFIX + title
        msg['From'] = FROM_EMAIL_ADDR
        msg['To'] = addrs

        try:
            smtp.send_message(msg)
        finally:
            smtp.quit()


class WebhookNotification(Notification):
    method = 'webhook'

    def get_color(self):
        if self.phase.value == 'request':
            if self.ticket.is_approved:
                color = 'cyan'
            else:
                color = 'yellow'
        else:
            color = self.ticket.color
        return NAME2RGB[color]

    async def send(self):
        if not WEBHOOK_URL:
            return
        title, content = self.render()
        # if truncate:
        #     bodies = body.split('\n')
        #     if len(bodies) > 10:
        #         bodies = bodies[:3] + ["..."] + bodies[-3:]
        #     tmp = []
        #     for line in bodies:
        #         if len(line) > 160:
        #             line = "%s ..." % line[:160]
        #         tmp.append(line)
        #     bodies = tmp
        #     body = '\n'.join(bodies)
        link = self.ticket.web_url
        msg = {
            'from': 'helpdesk',
            'title': title,
            'link': link,
            'color': self.get_color(),
            'text': f'{title}\n{link}\n{content}',
            'markdown': content,
        }
        r = requests.post(WEBHOOK_URL, json=msg, timeout=3)
        r.raise_for_status()
