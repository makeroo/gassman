'''
Created on 11/giu/2014

@author: makeroo
'''

import sys
import logging
from functools import partial
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import tornado.ioloop

import loglib
from threadpool import ThreadPool

log_email = logging.getLogger('gassman.email')

class Mailer (object):
    def __init__ (self, smtpServer, smtpPort, numThreads, queueTimeout, ioloop = tornado.ioloop.IOLoop.instance()):
        self.threadpool = ThreadPool(
            poolname='Mailer',
            thread_global_data=self,
            thread_quit_hook=self.quit_smtp,
            num_threads=numThreads,
            queue_timeout=queueTimeout)
        self.smtpServer = smtpServer
        self.smtpPort = smtpPort
        self.ioloop = ioloop

    def create_smtp (self):
        """This method is executed in a worker thread.

        Initializes the per-thread state. In this case we create one
        smtp per-thread.
        """
        smtp = smtplib.SMTP(self.smtpServer, self.smtpPort)
        return smtp

    def quit_smtp (self, global_data, local_data):
        smtp = local_data.smtp
        if smtp:
            try:
                smtp.quit()
            except:
                etype, evalue, tb = sys.exc_info()
                log_email.error('can\'t quit smtp: cause=%s/%s', etype, evalue)
                log_email.debug('full stacktrace:\n%s', loglib.TracebackFormatter(tb))

    def send (self, sender, receivers, subject, body, callback=None):
        self.threadpool.add_task(
            partial(self._send, sender, receivers, subject, body),
            callback)

    def _send (self, sender, receivers, subject, body, global_data=None, local_data=None):
        try:
            for i in range(2):
                log_email.debug('sending: try=%d, to=%s, subj=%s', i, receivers, subject)
                try:
                    smtp = local_data.smtp if hasattr(local_data, 'smtp') else None
                    if smtp is None:
                        smtp = global_data.create_smtp()
                        local_data.smtp = smtp
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    part1 = MIMEText(body, "plain", "utf-8")
                    msg.attach(part1)

                    smtp.sendmail(sender,
                                  receivers,
                                  msg.as_string().encode('ascii')
                                  )
                    log_email.debug('mail sent succesfully')
                    return True
                except smtplib.SMTPServerDisconnected as e:
                    if i:
                        raise e
                    #global_data.quit_smtp()
                    local_data.smtp = None
        except:
            etype, evalue, tb = sys.exc_info()
            log_email.error('can\'t send mail: subject=%s, cause=%s/%s', subject, etype, evalue)
            log_email.debug('email body: %s', body)
            log_email.debug('full stacktrace:\n%s', loglib.TracebackFormatter(tb))
            return False