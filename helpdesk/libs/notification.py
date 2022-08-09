# coding: utf-8

import logging
import smtplib
from email.message import EmailMessage
from typing import Tuple

import requests
from pytz import timezone
from starlette.templating import Jinja2Templates

from helpdesk.config import (
    NOTIFICATION_TITLE_PREFIX,
    WEBHOOK_URL,
    WEBHOOK_EVENT_URL,
    ADMIN_EMAIL_ADDRS,
    FROM_EMAIL_ADDR,
    SMTP_SERVER,
    SMTP_SERVER_PORT,
    SMTP_SSL,
    SMTP_CREDENTIALS,
    get_user_email,
    TIME_ZONE,
    TIME_FORMAT
)
from helpdesk.libs.sentry import report
from helpdesk.models.db.ticket import TicketPhase
from helpdesk.views.api.schemas import NodeType, NotifyMessage

logger = logging.getLogger(__name__)


def timeLocalize(value):
    tz = timezone(TIME_ZONE)
    utc = timezone('Etc/UTC')
    dt = value
    dt_with_timezone = utc.localize(dt)
    return dt_with_timezone.astimezone(tz).strftime(TIME_FORMAT)


_templates = Jinja2Templates(directory='templates/notification')
_templates.env.filters['timeLocalize'] = timeLocalize


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
        email_addrs = [ADMIN_EMAIL_ADDRS] + [get_user_email(cc) for cc in self.ticket.ccs] + self.ticket.annotation.get("approvers").split(',')
        email_addrs += [get_user_email(approver) for approver in await self.ticket.get_rule_actions('approver')]
        if self.phase.value in ('approval', 'mark'):
            email_addrs += [get_user_email(self.ticket.submitter)]
        email_addrs = ','.join(addr for addr in email_addrs if addr)
        return email_addrs

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
        if self.phase.value != 'request':
            return self.ticket.color
        if self.ticket.is_approved:
            return '#17a2b8'
        return '#ffc107'

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


class WebhookEventNotification(Notification):
    method = 'webhook'

    def render(self):
        nodes = self.ticket.annotation.get("nodes")
        next_node, notify_type= "", ""
        approvers = self.ticket.annotation.get("approvers")
        for index, node in enumerate(nodes):
            if self.ticket.annotation.get("current_node") == node.get("name"):
                next_node = nodes[index+1].get("name")  if (index != len(nodes)-1) else ""
                notify_type = node.get("node_type")

        if self.phase.value in (TicketPhase.APPROVAL.value, TicketPhase.MARK.value) or (self.phase.value == 'request' and self.ticket.status == "closed"):
            notify_type = NodeType.CC
        if notify_type == NodeType.CC:
            if self.phase.value == TicketPhase.MARK.value or approvers == "":
                notify_people = self.ticket.submitter
            else:
                notify_people = approvers + "," + self.ticket.submitter
            approvers = ""

        return NotifyMessage(
            phase=self.phase.value,
            title=self.ticket.title,
            ticket_url=self.ticket.web_url,
            status=self.ticket.status,
            is_approved=self.ticket.is_approved or False,
            submitter=self.ticket.submitter,
            params=self.ticket.params,
            request_time=self.ticket.created_at,
            reason=self.ticket.reason or "",
            approval_flow=self.ticket.annotation.get("policy"),
            current_node=self.ticket.annotation.get("current_node"),
            approvers=approvers,
            next_node=next_node,
            approval_log=self.ticket.annotation.get("approval_log"),
            notify_type=notify_type,
            notify_people=notify_people,
            comfirmed_by=self.ticket.confirmed_by or ""
        )

    async def send(self):
        if not WEBHOOK_EVENT_URL:
            return
        message = self.render()
        print(message)
        r = requests.post(WEBHOOK_EVENT_URL, message.json())
        if r.status_code == 200:
            return
        else:
            report()