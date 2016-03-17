"""
Created on 11/giu/2014

@author: makeroo
"""

import sys
import logging
import time
from functools import partial
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import tornado.ioloop

import loglib
from threadpool import ThreadPool


log_email = logging.getLogger('gassman.email')


class Mailer (object):
    MAX_TRIES = 3
    DELAY_AFTER_FAILURES = 2

    def __init__(self, smtp_server, smtp_port, num_threads, queue_timeout, default_sender, ioloop=tornado.ioloop.IOLoop.current()):
        self.threadpool = ThreadPool(
            poolname='Mailer',
            thread_global_data=self,
            thread_quit_hook=self._quit_smtp,
            num_threads=num_threads,
            queue_timeout=queue_timeout)
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.default_sender = default_sender
        self.ioloop = ioloop

    def _create_smtp(self):
        """This method is executed in a worker thread.

        Initializes the per-thread state. In this case we create one
        smtp per-thread.
        """
        smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
        return smtp

    @staticmethod
    def _quit_smtp(global_data, local_data):
        smtp = local_data.smtp
        if smtp is not None:
            smtp.quit()

    def send(self, receivers, subject, body, sender=None, reply_to=None, callback=None):
        self.threadpool.add_task(
            partial(self._send, sender or self.default_sender, receivers, subject, body, reply_to),
            callback
        )

    def _send(self, sender, receivers, subject, body, reply_to=None, global_data=None, local_data=None):
        try:
            for i in range(self.MAX_TRIES, 0, -1):
                log_email.debug('sending: try=%d, to=%s, subj=%s', self.MAX_TRIES - i + 1, receivers, subject)
                try:
                    smtp = local_data.smtp if hasattr(local_data, 'smtp') else None
                    if smtp is None:
                        smtp = global_data._create_smtp()
                        local_data.smtp = smtp
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    if reply_to is not None:
                        msg['reply-to'] = reply_to
                    part1 = MIMEText(body, "plain", "utf-8")
                    msg.attach(part1)

                    smtp.sendmail(sender,
                                  receivers,
                                  msg.as_string().encode('ascii')
                                  )
                    log_email.debug('mail sent succesfully')
                    return True
                except smtplib.SMTPException as e:
                    if i == 1:
                        raise e
                    # global_data.quit_smtp()
                    local_data.smtp = None
                    time.sleep(self.DELAY_AFTER_FAILURES)
        except:
            etype, evalue, tb = sys.exc_info()
            log_email.error('can\'t send mail: subject=%s, cause=%s/%s', subject, etype, evalue)
            log_email.debug('email body: %s', body)
            log_email.debug('full stacktrace:\n%s', loglib.TracebackFormatter(tb))
            return False
